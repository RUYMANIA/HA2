import asyncio
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

class SQLiteTests(unittest.TestCase):
    def test_wal_snapshot_and_sql_denial(self):
        from hermes_bridge.sqlite_reader import protected_snapshot
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
            path = Path(tmp)/'db'
            writer = sqlite3.connect(path)
            self.addCleanup(writer.close)
            writer.execute('PRAGMA journal_mode=WAL')
            writer.execute('CREATE TABLE t(v)'); writer.execute('INSERT INTO t VALUES(1)'); writer.commit()
            with protected_snapshot(path, allow_auxiliary=True) as reader:
                self.assertEqual(reader.execute('SELECT count(*) FROM t').fetchone()[0],1)
                writer.execute('INSERT INTO t VALUES(2)'); writer.commit()
                self.assertEqual(reader.execute('SELECT count(*) FROM t').fetchone()[0],1)
                for sql in ['INSERT INTO t VALUES(3)','UPDATE t SET v=4','DELETE FROM t','CREATE TABLE evil(x)',"ATTACH ':memory:' AS evil",'PRAGMA query_only=OFF','PRAGMA journal_mode=DELETE']:
                    with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError): reader.execute(sql)
            with protected_snapshot(path, allow_auxiliary=True) as reader:
                self.assertEqual(reader.execute('SELECT count(*) FROM t').fetchone()[0],2)
            writer.close()
            # Fixture-only checkpoint by its writer; never used on live source.
            with sqlite3.connect(path) as owner:
                owner.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            owner.close()
            for suffix in ('-wal', '-shm'):
                Path(str(path)+suffix).unlink(missing_ok=True)
            self.assertFalse(Path(str(path)+'-wal').exists())
            with self.assertRaises(OSError):
                with protected_snapshot(path): pass
            with protected_snapshot(path, allow_auxiliary=True) as reader:
                self.assertEqual(reader.execute('SELECT count(*) FROM t').fetchone()[0],2)

class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_ws_auth_ids_reconnect_and_redaction(self):
        from aiohttp import web
        from hermes_bridge.runtime import HAClient, PublicError
        auth = []; commands = []; connections = []
        async def handler(request):
            self.assertNotIn('token', str(request.rel_url))
            ws = web.WebSocketResponse(); await ws.prepare(request)
            connections.append(ws)
            await ws.send_json({'type':'auth_required'})
            frame = await ws.receive_json(); auth.append(frame)
            await ws.send_json({'type':'auth_ok'})
            async for message in ws:
                frame = json.loads(message.data); commands.append(frame)
                if frame.get('bad'):
                    await ws.send_json({'id':frame['id'], 'type':'result', 'success':False, 'error':{'message':'TOKEN-PRIVATE'}})
                else:
                    await ws.send_json({'id':frame['id'], 'type':'result','success':True,'result':{'version':'0.2.0','hermes_cron':{'jobs':[]}}})
            return ws
        app=web.Application(); app.router.add_get('/api/websocket',handler)
        runner=web.AppRunner(app); await runner.setup()
        site=web.TCPSite(runner,'127.0.0.1',0); await site.start()
        port=site._server.sockets[0].getsockname()[1]
        client=HAClient(f'http://127.0.0.1:{port}','TOKEN-PRIVATE',timeout=1)
        try:
            await asyncio.gather(*[client.call('ha2_notifications/get') for _ in range(3)])
            self.assertEqual([x['id'] for x in commands],[1,2,3,4]) # guarded get + three serialized RPCs
            with self.assertRaises(PublicError) as err:
                await client.call('ha2_notifications/get',bad=True)
            self.assertNotIn('PRIVATE',str(err.exception))
            with self.assertRaises(PublicError): await client.call('call_service')
            await connections[-1].close()
            await client.call('ha2_notifications/get')
            self.assertEqual(len(auth),2)
            self.assertEqual(auth[0],{'type':'auth','access_token':'TOKEN-PRIVATE'})
        finally:
            await client.close(); await runner.cleanup()
        self.assertTrue(client.closed)

    async def test_auth_version_timeout_and_cancel_fail_closed(self):
        from aiohttp import web
        from hermes_bridge.runtime import HAClient, PublicError
        mode=['auth']; seen=[]
        async def handler(request):
            ws=web.WebSocketResponse(); await ws.prepare(request)
            await ws.send_json({'type':'auth_required'}); await ws.receive_json()
            if mode[0]=='auth':
                await ws.send_json({'type':'auth_invalid','message':'TOKEN-PRIVATE'}); return ws
            await ws.send_json({'type':'auth_ok'})
            async for msg in ws:
                frame=json.loads(msg.data); seen.append(frame['type'])
                if mode[0]=='version':
                    await ws.send_json({'id':frame['id'],'type':'result','success':True,'result':{'version':'0.1.3','hermes_cron':{}}})
                elif mode[0]=='wrongid':
                    await ws.send_json({'id':True,'type':'result','success':True,'result':{}})
                else: await asyncio.sleep(.2)
            return ws
        app=web.Application(); app.router.add_get('/api/websocket',handler)
        runner=web.AppRunner(app); await runner.setup(); site=web.TCPSite(runner,'127.0.0.1',0); await site.start()
        url=f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}'
        try:
            for case in ['auth','version','wrongid','timeout','cancel']:
                mode[0]=case; client=HAClient(url,'TOKEN-PRIVATE',timeout=.05)
                try:
                    if case=='cancel':
                        task=asyncio.create_task(client.call('ha2_notifications/cron_sync',jobs=[])); await asyncio.sleep(.01); task.cancel()
                        with self.assertRaises(asyncio.CancelledError): await task
                    else:
                        with self.assertRaises(PublicError) as error: await client.call('ha2_notifications/cron_sync',jobs=[])
                        self.assertNotIn('PRIVATE',str(error.exception))
                    self.assertFalse(client.verified)
                finally: await client.close()
            self.assertNotIn('ha2_notifications/cron_sync',seen)
        finally: await runner.cleanup()

    async def test_factory_real_bridge_fake_ws_integration_and_single_owner(self):
        from aiohttp import web
        from hermes_bridge.runtime import make_factory, PublicError
        frames=[]
        async def handler(request):
            ws=web.WebSocketResponse(); await ws.prepare(request)
            await ws.send_json({'type':'auth_required'}); await ws.receive_json(); await ws.send_json({'type':'auth_ok'})
            async for msg in ws:
                frame=json.loads(msg.data); frames.append(frame)
                jobs=frame.get('jobs',[])
                dto={'version':'0.2.0','hermes_cron':{'jobs':[dict(j,source_instance=frame.get('source_instance'),profile='default',policy={'enabled':False,'content':'brief'}) for j in jobs]}}
                await ws.send_json({'id':frame['id'],'type':'result','success':True,'result':dto})
            return ws
        app=web.Application(); app.router.add_get('/api/websocket',handler)
        runner=web.AppRunner(app); await runner.setup(); site=web.TCPSite(runner,'127.0.0.1',0); await site.start()
        url=f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}'
        try:
            with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
                home=Path(tmp); (home/'cron').mkdir(); (home/'cron/jobs.json').write_text('{"jobs":[{"id":"j","name":"Job"}]}')
                with sqlite3.connect(home/'cron/executions.db') as db: db.execute('CREATE TABLE executions(id,job_id,status,source,finished_at,delivery_outcome)')
                observer=await make_factory(home,lambda:(url,'TOKEN-PRIVATE'))()
                task=asyncio.create_task(observer.run())
                for _ in range(50):
                    if any(f['type'].endswith('cron_sync') for f in frames): break
                    await asyncio.sleep(.01)
                self.assertTrue((await observer.status())['ha_verified'])
                self.assertEqual(frames[-1]['jobs'][0]['job_id'],'j')
                self.assertEqual(observer.bridge.policies['j']['enabled'],False)
                self.assertFalse((home/'state.db').exists())
                with self.assertRaises(PublicError): await observer.run()
                await observer.stop(); await asyncio.gather(task,return_exceptions=True)
                self.assertTrue(observer.client.closed)
        finally: await runner.cleanup()

    async def test_runtime_status_degrades_when_tick_reader_fails(self):
        from hermes_bridge.runtime import RuntimeObserver
        class Reader:
            def read(self): return []
        class Bridge:
            catalog_reader=Reader(); ledger_reader=Reader(); last_report={}
            async def tick(self):
                self.last_report={'ledger':'unavailable','catalog':'cached'}
        class Client:
            verified=False
            async def close(self): pass
        observer=RuntimeObserver(Bridge(),Client())
        task=asyncio.create_task(observer.run()); await asyncio.sleep(.02)
        self.assertEqual((await observer.status())['source_health'],'unavailable')
        await observer.stop(); await asyncio.gather(task,return_exceptions=True)

    async def test_factory_preflight_checkpoint_and_cleanup(self):
        from hermes_bridge.runtime import make_factory, HAClient
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
            home=Path(tmp); (home/'cron').mkdir()
            (home/'cron/jobs.json').write_text('{"jobs":[]}')
            calls=[]
            async def creds(): calls.append('credentials'); return ('http://127.0.0.1:1','secret')
            factory=make_factory(home=home,credential_provider=creds)
            self.assertEqual(calls,[])
            with self.assertRaises(Exception): await factory()
            self.assertEqual(calls,[]) # No connection/credential lookup before complete source preflight.
            with sqlite3.connect(home/'cron/executions.db') as db:
                db.execute('CREATE TABLE executions(id,job_id,status,source,finished_at,delivery_outcome)')
            observer=await factory()
            self.assertEqual(calls,['credentials'])
            self.assertEqual((home/'ha2-notifications/checkpoint.json').stat().st_mode & 0o777,0o600)
            source=observer.bridge.source_instance
            self.assertEqual((await observer.status())['source_health'],'ok')
            task=asyncio.create_task(observer.run()); await asyncio.sleep(.05)
            await observer.stop()
            await asyncio.gather(task,return_exceptions=True)
            self.assertTrue(observer.client.closed)
            other=await factory(); self.assertEqual(other.bridge.source_instance,source); await other.stop()
            self.assertNotIn('secret',json.dumps(await observer.status()))
            (home/'ha2-notifications/source.json').chmod(0o644)
            with self.assertRaises(Exception): await factory()

    async def test_bridge_readers_and_checkpoint_do_not_starve_loop(self):
        import time
        from hermes_bridge.bridge import Bridge, MemoryCheckpointStore
        class Client:
            async def call(self,*a,**k): return {'hermes_cron':{'jobs':[]}}
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
            b=Bridge(tmp,'source',Client(),checkpoint_store=MemoryCheckpointStore())
            class Slow:
                def read(self): time.sleep(.12); return []
            b.catalog_reader=Slow(); b.ledger_reader=Slow()
            ticks=[]
            async def pulse():
                for _ in range(8): ticks.append(asyncio.get_running_loop().time()); await asyncio.sleep(.02)
            heartbeat=asyncio.create_task(pulse()); await asyncio.sleep(0)
            await b.tick(); await heartbeat
            self.assertLess(max(y-x for x,y in zip(ticks,ticks[1:])),.08)

if __name__ == '__main__': unittest.main()

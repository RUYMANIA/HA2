"""Cron protocol remains compatible with the audited HA2 0.3 extension."""
import asyncio
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

class BackendCompatibility(unittest.IsolatedAsyncioTestCase):
    async def test_only_audited_02_and_03_backends_sync_after_guard(self):
        from aiohttp import web
        from hermes_bridge.runtime import HAClient,PublicError
        version=['0.3.0'];seen=[]
        async def handler(request):
            ws=web.WebSocketResponse();await ws.prepare(request)
            await ws.send_json({'type':'auth_required'});await ws.receive_json();await ws.send_json({'type':'auth_ok'})
            async for message in ws:
                data=json.loads(message.data);seen.append(data['type'])
                await ws.send_json({'id':data['id'],'type':'result','success':True,'result':{'version':version[0],'hermes_cron':{'jobs':[]}}})
            return ws
        app=web.Application();app.router.add_get('/api/websocket',handler)
        runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
        try:
            for current in ('0.3.0','0.2.0','0.1.3','0.4.0'):
                version[0]=current;seen.clear();client=HAClient(f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}','FIXTURE_ONLY',timeout=2)
                try:
                    if current in ('0.2.0','0.3.0'):
                        await client.call('ha2_notifications/cron_sync',source_instance='fixture',profile='default',jobs=[])
                        self.assertEqual(seen,['ha2_notifications/get','ha2_notifications/cron_sync'])
                    else:
                        with self.assertRaises(PublicError):await client.call('ha2_notifications/cron_sync',jobs=[])
                        self.assertEqual(seen,['ha2_notifications/get'])
                finally:await client.close()
        finally:await runner.cleanup()

if __name__=='__main__':unittest.main()

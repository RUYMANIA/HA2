"""Cron production boundaries, private in-memory Store; no running HA API."""
import asyncio, copy, unittest
from datetime import datetime, timezone, timedelta
from uuid import uuid5, NAMESPACE_URL
from custom_components.ha2_notifications.engine import Engine, Error
from test_engine import MemoryStore, rule

JOB=dict(job_id='job-original',name='Tarea',schedule='cada día',enabled=True,no_agent=False,delivery='telegram',excerpt_available=True)
class CronTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store=MemoryStore();self.now=datetime(2026,10,24,10,tzinfo=timezone.utc)
        self.e=Engine(self.store,'UTC',lambda:self.now,lambda:set());await self.e.load()
    async def sync(self,jobs=None):
        await self.e.cron_sync(source_instance='host',profile='default',jobs=[JOB] if jobs is None else jobs)
    def snap(self):return self.e.cron_snapshot()
    async def policy(self,**kw):
        args=dict(job_key=self.snap()['jobs'][0]['job_key'],expected_revision=self.snap()['revision'],enabled=True,content='brief',mode='cue',title='');args.update(kw)
        return await self.e.cron_policy(**args)
    def envelope(self,**kw):
        r=dict(execution_id='run1',finished_at=self.now.isoformat(),status='completed',delivery_outcome='unknown');r.update(kw);return r
    async def result(self,**kw):
        return await self.e.cron_result(source_instance='host',profile='default',job_id='job-original',result=self.envelope(**kw))
    async def test_brief_has_complete_content_footer_without_guessing_channel(self):
        await self.sync([dict(JOB,delivery='local')]);await self.policy();self.now+=timedelta(seconds=1)
        for status,delivery,label in [('completed','unknown','completada'),('failed','failed','fallida'),('unknown','not_configured','con estado desconocido')]:
            await self.result(execution_id='footer-'+status,status=status,delivery_outcome=delivery)
            body=self.e.data['queue'][-1]['rule']['body']
            self.assertIn('Tarea '+label+'. Entrega original:',body)
            self.assertIn('Contenido completo en Hermes Agent.',body)
            for invented in ('Telegram','telegram','Discord','email'):
                self.assertNotIn(invented,body)
        await self.policy(content='excerpt');self.now+=timedelta(seconds=1)
        await self.result(execution_id='footer-excerpt',preview='Primera\nSegunda\nTercera\nCuarta')
        body=self.e.data['queue'][-1]['rule']['body']
        self.assertEqual(body,'Primera\nSegunda\nTercera\n\nExtracto del resultado de Hermes Agent.')
        await self.result(execution_id='footer-fallback')
        self.assertIn('Contenido completo en Hermes Agent.',self.e.data['queue'][-1]['rule']['body'])

    async def test_concurrent_result_ingestion_and_sync_store_failure(self):
        await self.sync();await self.policy();self.now+=timedelta(seconds=1)
        results=await asyncio.gather(self.result(),self.result())
        self.assertEqual(sorted(r['outcome'] for r in results),['duplicate','queued'])
        self.assertEqual(len(self.e.data['queue']),1)
        before=copy.deepcopy(self.e.data);self.store.fail=True
        with self.assertRaisesRegex(Error,'unavailable'):await self.sync([])
        self.assertEqual(self.e.data,before)
        self.assertTrue(self.snap()['jobs'][0]['present'])

    async def test_unnamed_jobs_have_safe_ephemeral_alias(self):
        await self.sync([dict(JOB,name='')]);await self.policy();self.now+=timedelta(seconds=1)
        await self.result();q=self.e.data['queue'][0]
        self.assertEqual(q['rule']['name'],'Tarea de Hermes');self.assertEqual(q['rule']['title'],'Tarea de Hermes')
        self.assertEqual(self.snap()['jobs'][0]['name'],'')

    async def test_inflight_policy_off_cancels_claim_without_affecting_ha(self):
        await self.sync();await self.policy();self.now+=timedelta(seconds=1);await self.result()
        rid=await self.e.command('save',rule=rule(),expected_revision=0);await self.e.enqueue(rid)
        entered=asyncio.Event();release=asyncio.Event();outer=self
        class Sender:
            async def readiness(self):return 'ready'
            async def deliver(self,item,claim,valid):
                entered.set();await release.wait();outer.assertFalse(valid());await claim(2)
        task=asyncio.create_task(self.e.step(Sender()));await entered.wait()
        await self.policy(enabled=False);release.set();await task
        self.assertEqual([q['rule_id'] for q in self.e.data['queue']],[rid])

    async def test_finished_ttl_retry_and_submitted_recovery(self):
        await self.sync();await self.policy();self.now+=timedelta(minutes=10)
        finished=self.now-timedelta(minutes=5)
        await self.result(finished_at=finished.isoformat())
        self.assertEqual(self.e.data['queue'][0]['expires'],finished.timestamp()+1800)
        self.now+=timedelta(minutes=1)
        await self.result(finished_at=finished.isoformat())
        self.assertEqual(self.e.data['queue'][0]['expires'],finished.timestamp()+1800)
        class Sender:
            async def readiness(self):return 'ready'
            async def deliver(self,item,claim,valid):
                await claim(2);raise asyncio.CancelledError
        with self.assertRaises(asyncio.CancelledError):await self.e.step(Sender())
        await self.e.load();self.assertEqual(self.e.data['queue'],[])
        self.assertEqual(self.e.data['logs'][-1]['status'],'uncertain')
        self.assertEqual((await self.result(finished_at=finished.isoformat()))['outcome'],'duplicate')

    async def test_identity_isolation_bad_sync_and_exact_dto_limits(self):
        await self.sync();await self.policy()
        await self.sync([dict(JOB,job_id='new-id')]);jobs=self.snap()['jobs']
        self.assertTrue(jobs[0]['policy']['enabled']);self.assertFalse(jobs[1]['policy']['enabled'])
        self.assertEqual(set(jobs[0]),{'job_key','source_instance','profile','job_id','name','schedule','enabled','no_agent','delivery','excerpt_available','present','policy'})
        self.assertEqual(set(self.snap()['sources'][0]),{'source_instance','profile','online','last_seen'})
        before=copy.deepcopy(self.e.data)
        invalid=[dict(JOB,job_id='bad/id'),dict(JOB,job_id='a'*129),dict(JOB,name='a'*161),dict(JOB,schedule='a'*161),dict(JOB,no_agent=0),dict(JOB,name='bad\u202e'),dict(JOB,extra='private')]
        for j in invalid:
            with self.assertRaisesRegex(Error,'invalid_rule'):await self.sync([JOB,j])
        for source,profile in [('bad host','default'),('host','a'*65),('host','bad\\profile')]:
            with self.assertRaisesRegex(Error,'invalid_rule'):await self.e.cron_sync(source_instance=source,profile=profile,jobs=[JOB])
        self.assertEqual(before,self.e.data)

    async def test_result_atomic_queue_dedupe_ttl_cancel_and_origins(self):
        await self.sync();await self.policy();self.now+=timedelta(seconds=1)
        before=copy.deepcopy(self.e.data);self.store.fail=True
        with self.assertRaisesRegex(Error,'unavailable'):await self.result()
        self.assertEqual(before,self.e.data);self.store.fail=False
        r=await self.result();rid=uuid5(NAMESPACE_URL,'host/default/job-original/run1').hex
        self.assertEqual(r,dict(accepted=True,outcome='queued',request_id=rid))
        q=self.e.data['queue'][0];self.assertEqual(q['expires'],self.now.timestamp()+1800)
        self.assertEqual(q['rule']['kind'],'result');self.assertEqual(q['rule']['trigger'],'manual');self.assertEqual(self.e.data['rules'],[])
        self.assertEqual(q['origin']['execution_id'],'run1');self.assertEqual(self.e.data['logs'][-1]['origin'],q['origin'])
        self.assertNotIn('body',self.e.data['logs'][-1])
        await self.e.load();self.assertEqual((await self.result())['outcome'],'duplicate')
        self.assertEqual(len(self.e.data['queue']),1)
        await self.policy(enabled=False);self.assertEqual(self.e.data['queue'],[])
        await self.policy();self.now+=timedelta(seconds=1);await self.result(execution_id='run2')
        await self.sync([]);self.assertEqual(self.e.data['queue'],[])

    async def test_result_nonqueued_ack_cutoff_future_and_queue_full_retry(self):
        await self.sync()
        self.assertEqual((await self.result())['outcome'],'disabled')
        await self.policy();self.now+=timedelta(seconds=10)
        for eid,fields,expected in [
            ('old',dict(finished_at=(self.now-timedelta(minutes=1)).isoformat()),'disabled'),
            ('expired',dict(finished_at=(self.now-timedelta(minutes=31)).isoformat()),'expired'),
            ('silent',dict(silent=True),'silent')]:
            r=await self.result(execution_id=eid,**fields);self.assertTrue(r['accepted']);self.assertEqual(r['outcome'],expected)
        with self.assertRaisesRegex(Error,'invalid_rule'):await self.result(finished_at=(self.now+timedelta(minutes=6)).isoformat())
        with self.assertRaisesRegex(Error,'invalid_rule'):await self.result(delivery_outcome='private-error')
        with self.assertRaisesRegex(Error,'invalid_rule'):await self.result(execution_id='bad/id')
        await self.e.command('pause',paused=True,expected_revision=0)
        self.assertEqual((await self.result(execution_id='paused'))['outcome'],'paused')
        await self.e.command('pause',paused=False,expected_revision=1)
        for _ in range(32):await self.e.enqueue(manual=rule())
        before=copy.deepcopy(self.e.data)
        with self.assertRaisesRegex(Error,'queue_full'):await self.result(execution_id='retry')
        self.assertEqual(before,self.e.data)
        self.e.data['queue'].clear();r=await self.result(execution_id='retry',status='unknown')
        self.assertEqual(r['outcome'],'queued');self.assertIn('desconocido',self.e.data['queue'][0]['rule']['body'])
        await self.sync([])
        self.assertEqual((await self.result(execution_id='missing'))['outcome'],'missing_job')

    async def test_failed_preview_and_bare_secrets_are_never_copied(self):
        await self.sync();await self.policy(content='excerpt');self.now+=timedelta(seconds=1)
        await self.result(status='failed',preview='upstream stacktrace private details')
        self.assertNotIn('stacktrace',self.e.data['queue'][-1]['rule']['body'])
        await self.result(execution_id='secrets',preview='hola\nsk-abcdefghijklmnopqrstuvwxyz012345\nghp_abcdefgh12345678\ntercero')
        self.assertNotIn('sk-',self.e.data['queue'][-1]['rule']['body']);self.assertNotIn('ghp_',self.e.data['queue'][-1]['rule']['body'])

    async def test_excerpt_sanitization_utf8_and_brief_fallback(self):
        await self.sync();await self.policy(content='excerpt',mode='voice',title='😀'*32)
        self.now+=timedelta(seconds=1)
        await self.result(preview='Voz: hola\u0000\nhttps://private.test/a\ntoken=secret\n'+('😀'*500))
        q=self.e.data['queue'][0];body=q['rule']['body']
        self.assertNotIn('secret',body);self.assertNotIn('https://',body);self.assertNotIn('\u0000',body)
        self.assertLessEqual(len(body.encode('utf-8')),4096);self.assertIn('Extracto',body)
        self.assertLessEqual(len(q['rule']['title'].encode('utf-8')),128)
        await self.result(execution_id='no-preview',preview='')
        self.assertIn('completada',self.e.data['queue'][-1]['rule']['body'])

    async def test_policy_concurrency_and_commit_failure(self):
        await self.sync();before=copy.deepcopy(self.e.data)
        self.store.fail=True
        with self.assertRaisesRegex(Error,'unavailable'):await self.policy()
        self.assertEqual(before,self.e.data);self.store.fail=False
        revision=self.snap()['revision']
        results=await asyncio.gather(self.policy(title='Uno'),self.policy(title='Dos',expected_revision=revision),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,Error) for r in results),1)
        self.assertEqual(self.e.data['revision'],0)
        before=copy.deepcopy(self.e.data)
        for change in (dict(title='a'*33),dict(mode='mute'),dict(enabled=1),dict(content='raw')):
            with self.assertRaisesRegex(Error,'invalid_rule'):await self.policy(**change)
        self.assertEqual(before,self.e.data)

    async def test_sync_defaults_revision_validation_and_old_store_reload(self):
        rid=await self.e.command('save',rule=rule(),expected_revision=0)
        old=copy.deepcopy(self.e.data);await self.sync()
        s=self.snap();j=s['jobs'][0]
        self.assertEqual(j['policy'],dict(enabled=False,content='brief',mode='cue',title=''))
        self.assertEqual(j['job_key'],uuid5(NAMESPACE_URL,'host/default/job-original').hex)
        self.assertEqual(self.e.data['rules'],old['rules']);self.assertEqual(self.e.data['revision'],1)
        rev=s['revision'];await self.sync();self.assertEqual(self.snap()['revision'],rev)
        before=copy.deepcopy(self.e.data)
        with self.assertRaisesRegex(Error,'invalid_rule'):await self.sync([dict(JOB,delivery='https://secret')])
        self.assertEqual(self.e.data,before)
        with self.assertRaisesRegex(Error,'invalid_rule'):await self.sync([JOB,JOB])
        await self.sync([]);self.assertFalse(self.snap()['jobs'][0]['present'])
        await self.sync();self.assertFalse(self.snap()['jobs'][0]['policy']['enabled'])
        self.store.data=old;await self.e.load();self.assertEqual(self.e.data['rules'][0]['id'],rid)
        self.assertEqual(self.snap()['jobs'],[])
        await self.sync();self.now+=timedelta(seconds=91)
        self.assertFalse(self.snap()['sources'][0]['online'])

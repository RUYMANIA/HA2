"""Real Engine Store boundary; private transport fixtures, no network."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
from types import SimpleNamespace
from custom_components.ha2_notifications.engine import Engine, Error
from custom_components.ha2_notifications import proactive as p

class Store:
    def __init__(self):self.data=None;self.fail=False
    async def async_load(self):return deepcopy(self.data)
    async def async_save(self,data):
        if self.fail:raise OSError('<script>secret</script>')
        self.data=deepcopy(data)

class Transport:
    def __init__(self):self.ready=True;self.calls=[];self.started=asyncio.Event();self.release=asyncio.Event();self.completed=True
    async def capabilities(self):return dict.fromkeys(p.CAPABILITY_KEYS,True)
    async def readiness(self):return {'ready':self.ready,'reason':None if self.ready else '<script>private</script>'}
    async def generate(self,rid,intent,config,valid):
        assert valid();self.calls.append(('generate',rid));self.started.set();await self.release.wait()
        return SimpleNamespace(request_id=rid,body='<script>private opener</script>')
    async def present(self,prepared,config,valid):
        assert valid();self.calls.append(('present',prepared.request_id));return dict(accepted=True,completed=self.completed,reason='<script>private</script>')
    async def cancel(self,rid):self.calls.append(('cancel',rid))
    async def close(self):self.calls.append(('close',))

class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store=Store();self.now=datetime(2026,10,24,12,0,0,123456,tzinfo=timezone.utc)
        self.e=Engine(self.store,'Atlantic/Canary',lambda:self.now,lambda:set())
        await self.e.load();self.t=Transport()
        self.assertTrue(hasattr(p,'Coordinator'),'Missing HA supervised coordinator')
        self.c=p.Coordinator(self.e,self.t,lambda coro,name:asyncio.create_task(coro,name=name))
        await self.c.initialize()
    async def asyncTearDown(self):
        if hasattr(self,'c'):await self.c.close()
    async def enable(self):await self.c.configure(0,dict(p.DEFAULT_CONFIG,enabled=True))
    async def due(self):self.now=datetime.fromisoformat(self.e.data['proactive']['next_due_at']);await self.c.tick()
    async def test_defaults_off_separate_revision_and_strict_errors(self):
        self.assertFalse(self.c.snapshot()['config']['enabled']);self.assertIsNone(self.c.task)
        await self.enable();self.assertEqual(self.e.data['revision'],0);self.assertEqual(self.c.snapshot()['revision'],1)
        self.assertGreater(datetime.fromisoformat(self.c.snapshot()['runtime']['next_due_at']),self.now)
        for rev,config,reason in ((0,p.DEFAULT_CONFIG,'conflict'),(True,p.DEFAULT_CONFIG,'conflict'),(1,{},'invalid_config')):
            with self.assertRaisesRegex(Error,reason):await self.c.configure(rev,config)
    async def test_claim_durable_before_model_nonblocking_single_and_metadata_only(self):
        await self.enable();await self.due();await asyncio.wait_for(self.t.started.wait(),1)
        claim=self.store.data['proactive']['claim'];self.assertEqual(claim['request_id'],self.t.calls[0][1])
        await self.c.tick();self.assertEqual(len(self.t.calls),1)
        self.t.release.set();await self.c.task
        self.assertEqual(self.c.snapshot()['runtime']['status'],'completed')
        self.assertEqual(self.c.snapshot()['revision'],1)
        self.assertNotIn('<script>',str(self.store.data));self.assertNotIn('request_id',str(self.c.snapshot()))
    async def test_reconfigure_epoch_cancel_own_only(self):
        await self.enable();await self.due();await self.t.started.wait();old=self.c.task;old_id=self.t.calls[0][1]
        await self.c.configure(1,p.DEFAULT_CONFIG)
        self.assertTrue(old.done());self.assertIn(('cancel',old_id),self.t.calls)
        self.assertIsNone(self.e.data['proactive']['claim']);self.assertFalse(self.c.valid())
    async def test_pause_busy_queue_and_unknown_skip_no_replay(self):
        await self.enable();self.e.data['paused']=True;await self.due()
        self.assertEqual(self.t.calls,[]);self.assertGreater(datetime.fromisoformat(self.e.data['proactive']['next_due_at']),self.now)
        self.e.data['paused']=False;self.t.ready=False;await self.due()
        self.assertEqual(self.t.calls,[]);self.assertNotIn('<script>',str(self.c.snapshot()))
    async def test_restart_future_preserved_past_and_claim_resampled(self):
        await self.enable();future=self.e.data['proactive']['next_due_at'];await self.c.initialize()
        self.assertEqual(self.e.data['proactive']['next_due_at'],future)
        self.now=datetime.fromisoformat(future)+timedelta(seconds=1);await self.c.initialize()
        self.assertGreater(datetime.fromisoformat(self.e.data['proactive']['next_due_at']),self.now)
        self.e.data['proactive']['claim']={'request_id':'a'*32,'epoch':1};await self.c.initialize()
        self.assertIsNone(self.e.data['proactive']['claim']);self.assertEqual(self.t.calls,[])
    async def test_storage_failure_no_generation_no_raw_error(self):
        await self.enable();self.store.fail=True
        with self.assertRaisesRegex(Error,'unavailable'):await self.due()
        self.assertEqual(self.t.calls,[])
    async def test_preempt_active_when_readiness_or_global_pause_changes(self):
        await self.enable();await self.due();await self.t.started.wait();task=self.c.task
        self.t.ready=False;await self.c.tick();self.assertTrue(task.done())
        self.assertEqual([x[0] for x in self.t.calls],['generate','cancel'])
    async def test_closed_adapter_no_invented_capabilities(self):
        closed=p.ClosedTransport();self.assertEqual(await closed.capabilities(),dict.fromkeys(p.CAPABILITY_KEYS,False))
        self.assertFalse((await closed.readiness())['ready'])

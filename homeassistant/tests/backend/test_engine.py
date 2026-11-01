import asyncio, copy, importlib.util, pathlib, unittest
from datetime import datetime, timezone, timedelta
ROOT = pathlib.Path(__file__).resolve().parents[2]
FILE=ROOT/'custom_components/ha2_notifications/engine.py'
if FILE.exists():
    spec=importlib.util.spec_from_file_location('engine',FILE)
    engine=importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
else: engine=None

class MemoryStore:
    def __init__(self): self.data=None; self.fail=False
    async def async_load(self): return copy.deepcopy(self.data)
    async def async_save(self,data):
        if self.fail: raise OSError('private upstream error')
        self.data=copy.deepcopy(data)

def rule(**kw):
    return dict(name='Prueba',title='Aviso',body='Contenido',trigger='manual',**kw)

class EngineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.assertIsNotNone(engine,'Production engine must exist')
        self.store=MemoryStore(); self.now=datetime(2026,10,22,10,tzinfo=timezone.utc)
        self.e=engine.Engine(self.store,'Atlantic/Canary',lambda:self.now,lambda:{'sensor.test'})
        await self.e.load()
    async def test_once_recovery_and_nonexistent_weekly_time(self):
        self.now=datetime(2026,3,29,2,tzinfo=timezone.utc)
        await self.e.command('save',rule=dict(rule(enabled=True),trigger='weekly',time='01:30',days=[6],expiry_minutes=1440),expected_revision=0)
        await self.e.schedule()
        self.assertEqual(self.e.data['queue'],[],'Spring missing local hour is skipped, not shifted')
        self.now=datetime(2026,10,22,10,tzinfo=timezone.utc)
        await self.e.command('save',rule=dict(rule(enabled=True),trigger='once',date='2026-10-22',time='10:50'),expected_revision=1)
        await self.e.schedule();await self.e.load();await self.e.schedule()
        self.assertEqual(len(self.e.data['queue']),1)
        self.assertEqual(self.e.data['queue'][0]['expires'],datetime(2026,10,22,10,20,tzinfo=timezone.utc).timestamp())

    async def test_busy_drop_offline_wait_and_expiry(self):
        rid=await self.e.command('save',rule=rule(busy='drop'),expected_revision=0)
        await self.e.enqueue(rid)
        class Offline:
            async def readiness(self):return 'unavailable'
            async def deliver(self,*args):raise AssertionError('Offline must never deliver')
        sender=Offline()
        await self.e.step(sender)
        self.assertEqual(self.e.data['logs'][-1]['status'],'failed')
        rule2=rule();rule2['id']=rid
        await self.e.command('save',rule=rule2,expected_revision=1)
        await self.e.enqueue(rid);await self.e.step(sender)
        self.assertEqual(self.e.data['logs'][-1]['status'],'waiting')
        self.now+=timedelta(minutes=31);await self.e.step(sender)
        self.assertEqual(self.e.data['queue'],[])
        self.assertEqual(self.e.data['logs'][-1]['status'],'expired')

    async def test_concurrent_edit_conflicts_and_claim_cancellation(self):
        calls=await asyncio.gather(self.e.command('save',rule=rule(),expected_revision=0),self.e.command('save',rule=rule(),expected_revision=0),return_exceptions=True)
        self.assertEqual(sum(isinstance(c,engine.Error) for c in calls),1)
        rid=self.e.data['rules'][0]['id'];await self.e.enqueue(rid)
        entered=asyncio.Event();release=asyncio.Event();outer=self
        class Sender:
            async def readiness(self):return 'ready'
            async def deliver(self,item,claim,valid):
                entered.set();await release.wait()
                outer.assertFalse(valid())
                await claim(2)
        task=asyncio.create_task(self.e.step(Sender()))
        await entered.wait()
        await self.e.command('pause',paused=True,expected_revision=1)
        release.set();await task
        self.assertEqual(self.e.data['queue'],[])
        self.assertEqual(self.e.data['logs'][-1]['status'],'cancelled')

    async def test_unload_style_cancellation_preserves_claim_for_uncertain_reload(self):
        rid=await self.e.command('save',rule=rule(),expected_revision=0)
        await self.e.enqueue(rid)
        claimed=asyncio.Event()
        class Sender:
            async def readiness(self):return 'ready'
            async def deliver(self,item,claim,valid):
                await claim(2);claimed.set();await asyncio.Event().wait()
        task=asyncio.create_task(self.e.step(Sender()))
        await claimed.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(self.store.data['queue'][0]['phase'],'submitted')
        await self.e.load()
        self.assertEqual(self.e.data['queue'],[])
        self.assertEqual(self.e.data['logs'][-1]['status'],'uncertain')

    async def test_unclaimed_busy_race_keeps_durable_queue(self):
        rid=await self.e.command('save',rule=rule(),expected_revision=0)
        await self.e.enqueue(rid)
        class Sender:
            async def readiness(self):return 'ready'
            async def deliver(self,*args):return 'waiting','busy'
        await self.e.step(Sender())
        self.assertEqual(len(self.e.data['queue']),1)
        self.assertEqual(self.e.data['queue'][0]['phase'],'queued')
        self.assertEqual(self.e.data['logs'][-1]['status'],'waiting')

    async def test_request_id_cannot_duplicate_scheduled_occurrence(self):
        rid=await self.e.command('save',rule=dict(rule(enabled=True),trigger='weekly',time='10:50',days=[3]),expected_revision=0)
        await self.e.schedule()
        request_id=self.e.data['queue'][0]['request_id']
        await self.e.enqueue(rid,request_id=request_id)
        self.assertEqual(len(self.e.data['queue']),1,'All producer paths share request id dedup')

    async def test_submitted_claim_after_commit_failure_never_replays(self):
        rid=await self.e.command('save',rule=rule(),expected_revision=0)
        await self.e.enqueue(rid)
        outer=self
        class Sender:
            calls=0
            async def readiness(self):return 'ready'
            async def deliver(self,item,claim,valid):
                self.calls+=1;await claim(2)
                outer.store.fail=True
                return 'delivered',''
        sender=Sender()
        with self.assertRaises(engine.Error):await self.e.step(sender)
        self.store.fail=False
        try: await self.e.step(sender)
        except engine.Error: pass
        self.assertEqual(sender.calls,1,'Never replay a submitted claim after result persistence fails')
        self.assertEqual(self.e.data['logs'][-1]['status'],'uncertain')

    async def test_worker_claim_before_effect_crash_recovery_and_expiry(self):
        self.assertTrue(hasattr(self.e,'step'),'Production delivery worker required')
        rid=await self.e.command('save',rule=rule(),expected_revision=0)
        req=await self.e.enqueue(rid)
        outer=self
        class Sender:
            available=True; idle=False; calls=0
            async def readiness(self): return 'ready' if self.idle else 'busy'
            async def deliver(self,item,claim,valid):
                self.calls+=1
                await claim(9)
                outer.assertEqual(outer.store.data['queue'][0]['phase'],'submitted')
                outer.assertTrue(valid())
                return 'delivered',''
        sender=Sender()
        await self.e.step(sender)
        self.assertEqual(sender.calls,0)
        self.assertEqual(self.e.data['logs'][-1]['status'],'waiting')
        self.now+=timedelta(seconds=6);sender.idle=True
        await self.e.step(sender)
        self.assertEqual(sender.calls,1)
        self.assertEqual(self.e.data['queue'],[])
        self.assertEqual(self.e.data['logs'][-1]['status'],'delivered')
        await self.e.enqueue(rid)
        self.store.data['queue'][0].update(phase='submitted',baseline_generation=9)
        await self.e.load()
        self.assertEqual(self.e.data['logs'][-1]['status'],'uncertain')
        self.assertEqual(self.e.data['queue'],[])
        await self.e.enqueue(rid)
        self.now+=timedelta(minutes=31)
        await self.e.step(sender)
        self.assertEqual(self.e.data['logs'][-1]['status'],'expired')
        self.assertEqual(sender.calls,1)
        self.assertEqual(self.e.data['revision'],1)

    async def test_schedule_recovery_dst_dedup_and_state_cooldown(self):
        self.assertTrue(hasattr(self.e,'schedule'),'Production scheduler required')
        rid=await self.e.command('save',rule=dict(rule(enabled=True),trigger='weekly',time='10:50',days=[3]),expected_revision=0)
        await self.e.schedule()
        self.assertEqual(len(self.e.data['queue']),1)
        await self.e.load(); await self.e.schedule()
        self.assertEqual(len(self.e.data['queue']),1)
        self.now+=timedelta(days=7,hours=2)
        await self.e.schedule()
        self.assertEqual(len(self.e.data['queue']),1,'No stale catchup')
        await self.e.command('save',rule=dict(rule(enabled=True),trigger='weekly',time='01:30',days=[6]),expected_revision=1)
        self.now=datetime(2026,10,25,0,35,tzinfo=timezone.utc)
        await self.e.schedule(); count=len(self.e.data['queue'])
        self.now+=timedelta(hours=1); await self.e.schedule()
        self.assertEqual(len(self.e.data['queue']),count,'Repeated local hour dedup')
        state=await self.e.command('save',rule=dict(rule(enabled=True),trigger='state',entity_id='sensor.test',to_state='on'),expected_revision=2)
        for old in (None,'unknown','unavailable','on'):
            await self.e.state_changed('sensor.test',old,'on')
        self.assertFalse(any(q['rule_id']==state for q in self.e.data['queue']))
        await self.e.state_changed('sensor.test','off','on')
        await self.e.state_changed('sensor.test','off','on')
        self.assertEqual(sum(q['rule_id']==state for q in self.e.data['queue']),1)
        self.now+=timedelta(seconds=61)
        await self.e.state_changed('sensor.test','off','on')
        self.assertEqual(sum(q['rule_id']==state for q in self.e.data['queue']),2)
        self.assertEqual(self.e.data['revision'],3)

    async def test_durable_outbox_idempotence_and_pending_cancellation(self):
        self.assertTrue(hasattr(self.e,'enqueue'),'Durable enqueue is required')
        rid=await self.e.command('save',rule=rule(),expected_revision=0)
        req='a'*32
        self.assertEqual(await self.e.enqueue(rid,request_id=req),req)
        self.assertEqual(await self.e.enqueue(rid,request_id=req),req)
        self.assertEqual(len(self.store.data['queue']),1)
        self.assertEqual(self.e.data['revision'],1)
        await self.e.command('pause',paused=True,expected_revision=1)
        self.assertEqual(self.e.data['queue'],[])
        self.assertEqual(self.e.data['logs'][-1]['status'],'cancelled')
        with self.assertRaisesRegex(engine.Error,'paused'): await self.e.enqueue(rid)
        await self.e.command('pause',paused=False,expected_revision=2)
        for _ in range(32): await self.e.enqueue(rid)
        with self.assertRaisesRegex(engine.Error,'queue_full'): await self.e.enqueue(rid)
        await self.e.command('toggle',id=rid,enabled=False,expected_revision=3)
        self.assertEqual(self.e.data['queue'],[])
        self.assertLessEqual(len(self.e.data['logs']),200)
        self.assertNotIn('Contenido',str(self.e.data['logs']))

    async def test_canonical_validation_and_crud(self):
        rid=await self.e.command('save',rule=rule(),expected_revision=0)
        item=self.e.data['rules'][0]
        self.assertEqual(item.get('expiry_minutes'),30)
        self.assertEqual(item['days'],[0,1,2,3,4])
        for bad in ({'id':None},{'id':0},{'title':' '},{'body':'é'*3000},{'enabled':1},{'time':'24:00'},
                    {'days':[True]},{'trigger':'state','entity_id':'sensor.missing','to_state':'on'},
                    {'trigger':'once','date':'2026-03-29','time':'01:30'},
                    {'trigger':'once','date':'2026-10-25','time':'01:30'}, {'extra':'x'}):
            payload=rule();payload.update(bad)
            with self.subTest(bad=bad), self.assertRaisesRegex(engine.Error,'invalid_rule'):
                await self.e.command('save',rule=payload,expected_revision=1)
        await self.e.command('toggle',id=rid,enabled=True,expected_revision=1)
        self.assertTrue(self.e.data['rules'][0]['enabled'])
        updated=rule();updated.update(id=rid,name='Editado')
        await self.e.command('save',rule=updated,expected_revision=2)
        self.assertEqual(len(self.e.data['rules']),1)
        await self.e.command('delete',id=rid,expected_revision=3)
        self.assertEqual(self.e.data['rules'],[])
        with self.assertRaisesRegex(engine.Error,'not_found'):
            await self.e.command('delete',id=rid,expected_revision=4)

    async def test_empty_save_conflict_and_atomic_failure(self):
        self.assertEqual((self.e.data['revision'],self.e.data['paused'],self.e.data['rules']),(0,False,[]))
        saved=await self.e.command('save',rule=rule(),expected_revision=0)
        self.assertEqual(len(saved),32)
        self.assertFalse(self.e.data['rules'][0]['enabled'])
        with self.assertRaisesRegex(engine.Error,'conflict'):
            await self.e.command('pause',paused=True,expected_revision=0)
        self.store.fail=True
        with self.assertRaisesRegex(engine.Error,'unavailable'):
            await self.e.command('pause',paused=True,expected_revision=1)
        self.assertFalse(self.e.data['paused'])
        self.assertEqual(self.e.data['revision'],1)
        self.store.fail=False
        other=engine.Engine(self.store,'Atlantic/Canary',lambda:self.now,lambda:{'sensor.test'})
        await other.load()
        self.assertEqual(other.data,self.e.data)

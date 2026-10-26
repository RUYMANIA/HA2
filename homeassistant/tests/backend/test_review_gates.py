"""Regressions from independent review; real engine, injected IO and clock."""
import copy
import importlib.util
from pathlib import Path
import unittest
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('review_engine', ROOT / 'custom_components/ha2_notifications/engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

class MemoryStore:
    def __init__(self): self.data = None
    async def async_load(self): return copy.deepcopy(self.data)
    async def async_save(self, data): self.data = copy.deepcopy(data)

class ReviewGates(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now = datetime(2026, 10, 22, 10, tzinfo=timezone.utc)
        self.store = MemoryStore()
        self.engine = engine.Engine(self.store, 'Atlantic/Canary', lambda: self.now, lambda: {'sensor.test'})
        await self.engine.load()

    async def save(self, **kwargs):
        rule = dict(name='Prueba', title='Aviso', body='Contenido', trigger='manual')
        rule.update(kwargs)
        return await self.engine.command('save', rule=rule, expected_revision=self.engine.data['revision'])

    async def test_drop_when_target_becomes_busy_after_readiness(self):
        rid = await self.save(busy='drop')
        await self.engine.enqueue(rid)
        class BusyRace:
            async def readiness(self): return 'ready'
            async def deliver(self, *args): return 'waiting', 'busy'
        await self.engine.step(BusyRace())
        self.assertEqual(self.engine.data['queue'], [], 'drop must also apply to the second busy check')
        self.assertEqual(self.store.data['queue'], [])
        self.assertEqual(self.engine.data['logs'][-1]['status'], 'failed')
        self.assertEqual(self.engine.data['logs'][-1]['reason'], 'busy')

    async def test_full_queue_records_scheduled_backpressure_once_and_recovers(self):
        filler = await self.save()
        for _ in range(32): await self.engine.enqueue(filler)
        rid = await self.save(enabled=True, trigger='once', date='2026-10-22', time='11:00')
        await self.engine.schedule()
        blocked = [l for l in self.engine.data['logs'] if l['rule_id'] == rid]
        self.assertEqual([(l['status'], l['reason']) for l in blocked], [('waiting', 'queue_full')])
        await self.engine.load()
        await self.engine.schedule()
        self.assertEqual(len([l for l in self.engine.data['logs'] if l['rule_id'] == rid]), 1)
        class Success:
            async def readiness(self): return 'ready'
            async def deliver(self, item, claim, valid):
                await claim(1)
                return 'delivered', ''
        await self.engine.step(Success())
        await self.engine.schedule()
        self.assertEqual(len(self.engine.data['queue']), 32)
        self.assertEqual(sum(q['rule_id'] == rid for q in self.engine.data['queue']), 1)
        self.assertEqual(self.engine.data['logs'][-1]['status'], 'queued')

    async def test_full_queue_records_event_failure_without_consuming_cooldown(self):
        filler = await self.save()
        for _ in range(32): await self.engine.enqueue(filler)
        rid = await self.save(enabled=True, trigger='state', entity_id='sensor.test', to_state='on')
        await self.engine.state_changed('sensor.test', 'off', 'on')
        failed = [l for l in self.store.data['logs'] if l['rule_id'] == rid]
        self.assertEqual([(l['status'], l['reason']) for l in failed], [('failed', 'queue_full')])
        self.assertNotIn(rid, self.store.data['cooldowns'], 'A rejected event is not a successful enqueue')
        class Success:
            async def readiness(self): return 'ready'
            async def deliver(self, item, claim, valid):
                await claim(1)
                return 'delivered', ''
        await self.engine.step(Success())
        await self.engine.state_changed('sensor.test', 'off', 'on')
        self.assertEqual(sum(q['rule_id'] == rid for q in self.engine.data['queue']), 1)
        self.assertEqual(self.store.data['cooldowns'][rid], self.now.timestamp())

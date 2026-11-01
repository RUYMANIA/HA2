"""Activity contract on the actual Engine; no HA API or device effects."""
import copy
import unittest
from datetime import datetime, timezone, timedelta
from custom_components.ha2_notifications.engine import Engine
from test_engine import MemoryStore, rule


class ActivityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store = MemoryStore()
        self.now = datetime(2026, 10, 27, 10, 15, 32, tzinfo=timezone.utc)
        self.e = Engine(self.store, 'Atlantic/Canary', lambda: self.now, lambda: set())
        await self.e.load()

    async def test_manual_action_source_is_internal_and_timestamp_keeps_real_offset(self):
        from custom_components.ha2_notifications.engine import Error
        self.now = datetime.fromisoformat('2026-07-01T10:15:32+01:00')
        rid = await self.e.enqueue(manual=dict(kind='result', title='Result', body='Private'))
        event = self.e.data['logs'][-1]
        self.assertEqual((event['id'], event['source'], event['kind'], event['trigger']),
                         (rid, 'home_assistant', 'result', 'manual'))
        self.assertEqual(event['at'], '2026-07-01T10:15:32+01:00')
        self.assertEqual(datetime.fromisoformat(event['at']).utcoffset(), timedelta(hours=1))
        with self.assertRaisesRegex(Error, 'invalid_rule'):
            await self.e.enqueue(manual=dict(kind='result', title='Result', body='Private', source='proactive'))
        self.assertEqual(self.e.data['revision'], 0)

    async def test_unknown_kind_from_legacy_queue_is_null_not_inferred_from_current_rule(self):
        rid = await self.e.command('save', expected_revision=0, rule=rule(kind='weather'))
        request_id = await self.e.enqueue(rid)
        data = copy.deepcopy(self.e.data)
        data['queue'][0]['rule'].pop('kind')
        data['queue'][0]['rule']['name'] = 'Original queue name'
        data['rules'][0].update(kind='reminder', name='New current name')
        await self.e.commit(data)
        await self.e.load()
        class Sender:
            async def readiness(self):
                return 'ready'
            async def deliver(self, item, claim, valid):
                await claim(1)
                return 'delivered', ''
        await self.e.step(Sender())
        event = self.e.data['logs'][-1]
        self.assertIsNone(event['kind'])
        self.assertEqual(event['name'], 'Original queue name')
        self.assertEqual(event['id'], request_id)
        self.assertEqual(event['source'], 'home_assistant')

    async def test_retention_200_preserves_legacy_bytes_and_revision(self):
        legacy = dict(id='old', at='2026-10-01T09:00:00+01:00', rule_id='old-rule',
                      name='Original', status='delivered', reason='')
        self.store.data = dict(self.e.data, revision=55, logs=[copy.deepcopy(legacy)])
        await self.e.load()
        self.assertEqual(self.e.data['logs'], [legacy])
        self.assertNotIn('source', self.e.data['logs'][0])
        rid = await self.e.enqueue(manual=dict(title='Result', body='private', kind='result'))
        item = self.e.data['queue'][0]
        data = copy.deepcopy(self.e.data)
        for _ in range(198):
            self.e.log(data, item, 'waiting', 'busy')
        await self.e.commit(data)
        self.assertEqual(len(self.e.data['logs']), 200)
        self.assertEqual(self.e.data['logs'][0], legacy)
        data = copy.deepcopy(self.e.data)
        self.e.log(data, item, 'delivered')
        await self.e.commit(data)
        await self.e.load()
        self.assertEqual(len(self.e.data['logs']), 200)
        self.assertEqual(self.e.data['logs'][-1]['id'], rid)
        self.assertEqual(self.e.data['logs'][-1]['status'], 'delivered')
        self.assertNotIn(legacy, self.e.data['logs'])
        self.assertEqual(self.e.data['revision'], 55)

    async def test_scheduled_ha_captures_metadata_and_event_time_without_payload(self):
        rid = await self.e.command('save', expected_revision=0, rule=dict(
            rule(enabled=True, kind='reminder'), name='Fichar salida',
            trigger='weekly', days=[1], time='10:15', body='SECRET https://private.invalid'))
        await self.e.schedule()
        queued = copy.deepcopy(self.e.data['logs'][-1])
        self.assertEqual((queued.get('source'), queued.get('kind'), queued.get('trigger')),
                         ('home_assistant', 'reminder', 'weekly'))
        self.assertEqual(queued['name'], 'Fichar salida')
        self.assertEqual(datetime.fromisoformat(queued['at']), self.now)
        self.now += timedelta(seconds=7)
        edited = dict(self.e.data['rules'][0], name='Renamed', kind='weather')
        await self.e.command('save', expected_revision=1, rule=edited)
        cancelled = self.e.data['logs'][-1]
        self.assertEqual((cancelled['name'], cancelled['kind']), ('Fichar salida', 'reminder'))
        self.assertEqual(cancelled['id'], queued['id'])
        self.assertEqual(cancelled['status'], 'cancelled')
        self.assertEqual(datetime.fromisoformat(cancelled['at']), self.now)
        self.assertNotIn('SECRET', str(self.e.data['logs']))
        self.assertNotIn('https://', str(self.e.data['logs']))
        self.assertEqual(self.e.data['revision'], 2)
        self.assertEqual(self.store.data['logs'], self.e.data['logs'])

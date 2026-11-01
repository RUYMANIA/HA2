"""Activity traces exercise the real Coordinator and Engine, private effects only."""
import asyncio
from copy import deepcopy
from datetime import datetime
import unittest
import test_coordinator as fixtures


class ActivityLogTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = fixtures.CoordinatorTests.asyncSetUp
    asyncTearDown = fixtures.CoordinatorTests.asyncTearDown
    enable = fixtures.CoordinatorTests.enable
    due = fixtures.CoordinatorTests.due
    async def test_event_timestamps_are_stage_times_not_due_or_completion_time(self):
        from datetime import timedelta
        await self.enable()
        original_generate = self.t.generate
        async def generate(*args):
            prepared = await original_generate(*args)
            self.now += timedelta(seconds=2)
            return prepared
        async def present(*args):
            self.now += timedelta(seconds=3)
            return dict(accepted=True, completed=True)
        self.t.generate = generate
        self.t.present = present
        self.t.release.set()
        await self.due()
        start = self.now
        await self.c.task
        logs = self.e.data['logs']
        self.assertEqual([datetime.fromisoformat(x['at']) for x in logs],
                         [start, start, start + timedelta(seconds=2),
                          start + timedelta(seconds=5), start + timedelta(seconds=5)])

    async def test_failed_presentation_log_commit_blocks_presentation_effect(self):
        await self.enable()
        original_save = self.store.async_save
        async def save(data):
            if data['logs'] and data['logs'][-1]['status'] == 'presenting':
                raise OSError('SECRET storage detail')
            await original_save(data)
        self.store.async_save = save
        self.t.release.set()
        await self.due()
        owner = deepcopy(self.c.owner)
        await self.c.task
        self.assertEqual([x['status'] for x in self.e.data['logs']], ['claimed', 'generating', 'failed'])
        self.assertEqual(self.e.data['logs'][-1]['reason'], 'unavailable')
        self.assertNotIn(('present', owner['request_id']), self.t.calls)
        self.assertIsNone(self.e.data['proactive']['last_completed_at'])
        self.assertNotIn('SECRET', str(self.e.data))

    async def test_failed_reconfiguration_commit_does_not_cancel_or_publish_false_event(self):
        await self.enable()
        await self.due()
        await asyncio.wait_for(self.t.started.wait(), 1)
        before = deepcopy(self.e.data)
        self.store.fail = True
        with self.assertRaisesRegex(fixtures.Error, 'unavailable'):
            await self.c.configure(1, fixtures.p.DEFAULT_CONFIG)
        self.store.fail = False
        self.assertEqual(self.e.data, before)
        self.assertEqual(self.store.data, before)
        self.assertTrue(self.c.valid())
        self.t.release.set()
        await self.c.task
        self.assertEqual(self.e.data['logs'][-1]['status'], 'completed')
        self.assertNotIn('cancelled', [x['status'] for x in self.e.data['logs']])

    async def test_mismatched_generated_request_id_never_presents_or_cancels_foreign_request(self):
        from types import SimpleNamespace
        await self.enable()
        async def generate(*args):
            return SimpleNamespace(request_id='b' * 32, body='SECRET opener')
        self.t.generate = generate
        await self.due()
        owner = deepcopy(self.c.owner)
        await self.c.task
        self.assertEqual([x['status'] for x in self.e.data['logs']], ['claimed', 'generating', 'skipped'])
        self.assertTrue(all(x['id'] == owner['request_id'] for x in self.e.data['logs']))
        self.assertEqual(self.t.calls, [('cancel', owner['request_id'])])
        self.assertNotIn('SECRET', str(self.e.data))

    async def test_active_current_shape_preserves_rules_revision55_and_proactive_config_revision4(self):
        # Isolated fixture matching the protected shape, never read/write a live Store.
        from custom_components.ha2_notifications.engine import normalize
        from datetime import timedelta
        state = fixtures.p.empty_state()
        state.update(revision=4, epoch=9,
                     config=dict(fixtures.p.DEFAULT_CONFIG, enabled=True, all_day=False,
                                 start='08:00', end='15:00', interval_minutes=240, mode='voice'),
                     next_due_at=(self.now + timedelta(minutes=5)).isoformat(), status='scheduled')
        legacy = dict(id='legacy', at='2026-10-20T09:00:00+01:00', rule_id='old',
                      name='Original', status='delivered', reason='')
        rules = [normalize(dict(name='Rule '+str(n), title='Title', body='Private body',
                                trigger='manual', enabled=True), self.e.tz, set()) for n in range(3)]
        data = deepcopy(self.e.data)
        data.update(revision=55, rules=rules, logs=[legacy], proactive=state)
        await self.e.commit(data)
        await self.c.initialize()
        before = deepcopy(self.e.data)
        await self.c.tick()
        self.assertEqual(self.e.data, before, 'Polling must not invent historical proactive events')
        self.t.release.set()
        await self.due()
        await self.c.task
        self.assertEqual(self.e.data['revision'], 55)
        self.assertEqual(self.e.data['rules'], rules)
        self.assertEqual(self.e.data['proactive']['revision'], 4)
        self.assertEqual(self.e.data['proactive']['epoch'], 9)
        self.assertEqual(self.e.data['proactive']['config'], state['config'])
        self.assertEqual(self.e.data['logs'][0], legacy)
        self.assertNotIn('source', self.e.data['logs'][0])
        self.assertEqual(len(self.e.data['logs']), 6)
        self.assertNotIn('Private body', str(self.e.data['logs']))

    async def test_common_retention_counts_ha_and_proactive_events_together(self):
        legacy = dict(id='legacy', at='2026-10-20T09:00:00+01:00', rule_id='old',
                      name='Original', status='delivered', reason='')
        data = deepcopy(self.e.data)
        data['logs'] = [dict(legacy, id='legacy-'+str(n)) for n in range(198)]
        await self.e.commit(data)
        await self.e.enqueue(manual=dict(kind='reminder', title='Title', body='Private'))
        class Sender:
            async def readiness(self):
                return 'ready'
            async def deliver(self, item, claim, valid):
                await claim(1)
                return 'delivered', ''
        await self.e.step(Sender())
        self.assertEqual(len(self.e.data['logs']), 200)
        await self.enable()
        self.t.release.set()
        await self.due()
        await self.c.task
        self.assertEqual(len(self.e.data['logs']), 200)
        self.assertEqual([x['source'] for x in self.e.data['logs'][-7:]],
                         ['home_assistant'] * 2 + ['proactive'] * 5)
        self.assertEqual(self.e.data['logs'][0]['id'], 'legacy-5')
        self.assertEqual(self.store.data['logs'], self.e.data['logs'])
        await self.e.load()
        self.assertEqual(self.store.data['logs'], self.e.data['logs'])

    async def test_results_do_not_equate_generated_accepted_or_false_delivery_to_completed(self):
        await self.enable()
        for result in (None, {}, {'accepted': True, 'completed': False},
                       {'accepted': False, 'completed': True},
                       {'accepted': False, 'completed': False},
                       {'accepted': True, 'completed': True}):
            with self.subTest(result=result):
                async def present(*args):
                    return result
                self.t.present = present
                self.t.release.set()
                await self.due()
                rid = self.c.owner['request_id']
                await self.c.task
                logs = [x for x in self.e.data['logs'] if x['id'] == rid]
                completed = isinstance(result, dict) and result.get('accepted') is True and result.get('completed') is True
                accepted = isinstance(result, dict) and result.get('accepted') is True
                self.assertEqual([x['status'] for x in logs],
                                 ['claimed', 'generating', 'presenting'] +
                                 (['accepted'] if accepted else []) +
                                 (['completed'] if completed else ['skipped']))
                self.assertEqual(logs[-1]['reason'], None if completed else 'not_completed')
                self.assertEqual(self.e.data['proactive']['status'], 'completed' if completed else 'skipped')
                before = deepcopy(self.e.data['logs'])
                await self.c.tick()
                await self.c.update({'request_id': rid, 'epoch': self.e.data['proactive']['epoch']},
                                    'completed', completed=True)
                self.assertEqual(self.e.data['logs'], before)

    async def test_generation_and_presentation_exceptions_log_only_allowlisted_failure(self):
        await self.enable()
        for stage in ('generate', 'present'):
            with self.subTest(stage=stage):
                original = getattr(self.t, stage)
                async def fail(*args):
                    raise RuntimeError('SECRET https://private.invalid/opener')
                setattr(self.t, stage, fail)
                self.t.release.set()
                await self.due()
                owner = deepcopy(self.c.owner)
                await self.c.task
                logs = [x for x in self.e.data['logs'] if x['id'] == owner['request_id']]
                self.assertEqual(logs[-1]['status'], 'failed')
                self.assertEqual(logs[-1]['reason'], 'unavailable')
                self.assertIsNone(self.e.data['proactive']['claim'])
                self.assertIsNone(self.e.data['proactive']['last_completed_at'])
                self.assertNotIn('SECRET', str(self.e.data))
                self.assertNotIn('https://', str(self.e.data))
                before = deepcopy(self.e.data['logs'])
                await self.c.tick()
                await self.c.update(owner, 'failed', 'unavailable')
                self.assertEqual(self.e.data['logs'], before)
                setattr(self.t, stage, original)

    async def test_guard_cancellation_uses_request_id_once_and_stale_owner_cannot_complete(self):
        await self.enable()
        await self.due()
        await asyncio.wait_for(self.t.started.wait(), 1)
        owner = deepcopy(self.c.owner)
        self.t.ready = False
        await self.c.tick()
        last = self.e.data['logs'][-1]
        self.assertEqual((last['id'], last['status'], last['reason']),
                         (owner['request_id'], 'cancelled', 'guard_blocked'))
        before = deepcopy(self.e.data['logs'])
        await self.c.tick()
        await self.c.cancel_active()
        await self.c.update(owner, 'completed', completed=True)
        self.assertEqual(self.e.data['logs'], before)
        self.assertIsNone(self.e.data['proactive']['last_completed_at'])
        self.assertEqual(self.t.calls.count(('cancel', owner['request_id'])), 1)

    async def test_reconfigure_logs_old_owner_cancellation_atomically_once(self):
        await self.enable()
        await self.due()
        await asyncio.wait_for(self.t.started.wait(), 1)
        owner = deepcopy(self.c.owner)
        original_save = self.store.async_save
        saves = []
        async def save(data):
            saves.append(deepcopy(data))
            await original_save(data)
        self.store.async_save = save
        await self.c.configure(1, dict(fixtures.p.DEFAULT_CONFIG, enabled=True, interval_minutes=120))
        self.assertEqual(saves[0]['logs'][-1]['status'], 'cancelled')
        self.assertEqual(saves[0]['logs'][-1]['id'], owner['request_id'])
        logs = deepcopy(self.e.data['logs'])
        self.assertEqual([x['status'] for x in logs], ['claimed', 'generating', 'cancelled'])
        self.assertEqual(logs[-1]['reason'], 'configuration_changed')
        self.assertEqual(self.e.data['proactive']['epoch'], owner['epoch'] + 1)
        self.assertEqual(self.e.data['proactive']['revision'], 2)
        await self.c.update(owner, 'completed', completed=True)
        await self.c.cancel_active()
        await self.c.tick()
        self.assertEqual(self.e.data['logs'], logs)
        self.assertIsNone(self.e.data['proactive']['last_completed_at'])
        self.assertEqual(self.t.calls.count(('cancel', owner['request_id'])), 1)

    async def test_guard_skip_once_per_due_not_every_tick_or_delivery(self):
        await self.enable()
        self.t.ready = False
        revision = self.e.data['proactive']['revision']
        epoch = self.e.data['proactive']['epoch']
        await self.due()
        self.assertEqual(len(self.e.data['logs']), 1)
        skipped = deepcopy(self.e.data['logs'][0])
        self.assertEqual((skipped['source'], skipped['kind'], skipped['status'], skipped['reason']),
                         ('proactive', 'proactive', 'skipped', 'guard_blocked'))
        self.assertIsNone(skipped['id'], 'No request ID exists before a claim')
        for _ in range(4):
            await self.c.tick()
        self.assertEqual(self.e.data['logs'], [skipped])
        await self.due()
        self.assertEqual(len(self.e.data['logs']), 2)
        self.assertEqual(self.t.calls, [])
        self.assertIsNone(self.e.data['proactive']['last_completed_at'])
        self.assertEqual(self.e.data['proactive']['revision'], revision)
        self.assertEqual(self.e.data['proactive']['epoch'], epoch)

    async def test_encounter_logs_claim_generation_presentation_completion_in_same_store(self):
        await self.enable()
        revision = (self.e.data['revision'], self.e.data['proactive']['revision'])
        original_generate = self.t.generate
        original_present = self.t.present
        async def generate(*args):
            self.assertEqual([x['status'] for x in self.store.data['logs']], ['claimed', 'generating'])
            return await original_generate(*args)
        async def present(*args):
            self.assertEqual(self.store.data['logs'][-1]['status'], 'presenting')
            return await original_present(*args)
        self.t.generate = generate
        self.t.present = present
        await self.due()
        self.assertEqual([x['status'] for x in self.store.data['logs']], ['claimed', 'generating'])
        await asyncio.wait_for(self.t.started.wait(), 1)
        rid = self.c.owner['request_id']
        before = deepcopy(self.e.data['logs'])
        for _ in range(3):
            await self.c.tick()
        self.assertEqual(self.e.data['logs'], before)
        self.t.release.set()
        await self.c.task
        logs = self.e.data['logs']
        self.assertEqual([x['status'] for x in logs],
                         ['claimed', 'generating', 'presenting', 'accepted', 'completed'])
        for event in logs:
            self.assertEqual(event['id'], rid)
            self.assertEqual((event['source'], event['kind'], event['name']),
                             ('proactive', 'proactive', 'Invitación proactiva'))
            self.assertEqual(datetime.fromisoformat(event['at']), self.now)
            self.assertIsNone(event['rule_id'])
        self.assertEqual(self.store.data['logs'], logs)
        self.assertEqual((self.e.data['revision'], self.e.data['proactive']['revision']), revision)
        self.assertNotIn('private', str(logs))
        self.assertNotIn('body', str(logs))
        self.assertNotIn('opener', str(logs))
        self.assertNotIn('https://', str(logs))
        await self.c.tick()
        self.assertEqual(self.e.data['logs'], logs)

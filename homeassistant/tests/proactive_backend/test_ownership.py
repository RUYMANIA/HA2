"""Additional pure regression probes: request-bound validity and runtime privacy."""
import asyncio
from datetime import datetime, timezone
import unittest
import test_coordinator as fixtures

class OwnershipTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = fixtures.CoordinatorTests.asyncSetUp
    asyncTearDown = fixtures.CoordinatorTests.asyncTearDown
    enable = fixtures.CoordinatorTests.enable
    due = fixtures.CoordinatorTests.due
    async def test_old_valid_callback_cannot_validate_new_owner(self):
        await self.enable();await self.due();await self.t.started.wait()
        old=dict(self.c.owner)
        old_valid=lambda:self.c.valid(old)
        self.assertTrue(old_valid())
        await self.c.configure(1,dict(self.c.snapshot()['config'],mode='voice'))
        self.t.started.clear();await self.due();await self.t.started.wait()
        self.assertFalse(old_valid())
        self.assertTrue(self.c.valid(self.c.owner))
    async def test_close_is_idempotent_and_request_id_is_durable_metadata(self):
        await self.enable();await self.due();await self.t.started.wait()
        rid=self.c.owner['request_id'];self.t.release.set();await self.c.task
        self.assertEqual(self.store.data['proactive'].get('last_request_id'),rid)
        await self.c.close();await self.c.close()
        self.assertEqual(self.t.calls.count(('close',)),1)

    async def test_unload_storage_failure_still_closes_owned_transport(self):
        await self.enable();await self.due();await self.t.started.wait()
        self.store.fail=True
        await self.c.close()
        self.assertIn(('close',),self.t.calls)
        self.assertIsNone(self.c.task);self.assertFalse(self.c.valid())

    async def test_ordinary_queue_preempts_without_consuming_or_reordering_it(self):
        await self.enable();await self.due();await self.t.started.wait();task=self.c.task
        self.e.data['queue']=[{'request_id':'f'*32,'phase':'queued'}]
        await self.c.tick()
        self.assertTrue(task.done())
        self.assertEqual(self.e.data['queue'],[{'request_id':'f'*32,'phase':'queued'}])
        self.assertEqual([call[0] for call in self.t.calls],['generate','cancel'])

    async def test_accepted_without_completed_never_marks_completed(self):
        await self.enable();self.t.completed=False;self.t.release.set()
        await self.due();await self.c.task
        self.assertIsNone(self.c.snapshot()['runtime']['last_completed_at'])
        self.assertEqual(self.c.snapshot()['runtime']['reason'],'not_completed')
    async def test_disabled_legacy_state_does_not_drift_queue_rules_or_cron(self):
        self.e.data['revision']=49
        self.e.data['rules']=[dict(id=str(i),enabled=False) for i in range(4)]
        self.e.data['hermes_cron']={'revision':7,'jobs':[{'key':i} for i in range(12)],'receipts':{}}
        before={key:str(self.e.data[key]) for key in ('revision','rules','hermes_cron','queue')}
        await self.c.initialize();await self.enable();await self.due();await self.t.started.wait()
        self.t.release.set();await self.c.task
        self.assertEqual({key:str(self.e.data[key]) for key in before},before)

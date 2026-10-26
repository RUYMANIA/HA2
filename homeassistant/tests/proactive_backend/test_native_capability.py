"""Native listening is not an extension of the retired 30s requirement."""
import unittest
import test_coordinator as f

class NativeCapabilityTests(unittest.IsolatedAsyncioTestCase):
 asyncSetUp=f.CoordinatorTests.asyncSetUp
 asyncTearDown=f.CoordinatorTests.asyncTearDown
 async def test_native_listen_replaces_30s_and_missing_native_fails_closed(self):
  async def caps():return dict(full_agent=True,session_binding=True,transcript_only=True,native_listen=True)
  self.t.capabilities=caps
  await self.c.refresh();self.assertTrue(self.c.ready)
  self.assertNotIn('listen_timeout_30s',self.c.snapshot()['capabilities'])
  async def old():return dict(full_agent=True,session_binding=True,transcript_only=True,listen_timeout_30s=True)
  self.t.capabilities=old;await self.c.refresh();self.assertFalse(self.c.ready)

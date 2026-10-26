import unittest
from aiohttp import ClientSession
from custom_components.hermes_agent.api import HermesAgentClient

class CapabilityClientTests(unittest.IsolatedAsyncioTestCase):
 async def test_bootstrap_capability_requires_explicit_boolean_and_full_native_api(self):
  async with ClientSession() as session:
   client=HermesAgentClient(session,'http://fixture.invalid','fixture-token')
   data={'capabilities':{'conversation':{'available':True,'native_session_bootstrap':True,'full_agent':True}}}
   async def request(*a,**kw):return data
   client._request_json=request
   self.assertEqual(await client.async_proactive_capabilities(),{'native_session_bootstrap':True,'full_agent':True})
   data['capabilities']['conversation']['native_session_bootstrap']='true'
   self.assertFalse((await client.async_proactive_capabilities())['native_session_bootstrap'])

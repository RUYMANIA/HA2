"""Parent cross-contract regression. Production policy engine; only IO/clock injected."""
import asyncio,copy,importlib.util,unittest
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('ha2_policy_engine',ROOT/'custom_components/ha2_notifications/engine.py')
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
class MemoryStore:
 async def async_load(self):return None
 async def async_save(self,data):self.value=copy.deepcopy(data)
class BusySender:
 async def readiness(self):return 'busy'
 async def deliver(self,*args):raise AssertionError('Busy target must never receive a card')
class DropPolicy(unittest.IsolatedAsyncioTestCase):
 async def test_canonical_drop_is_accepted_and_drops_busy_delivery(self):
  store=MemoryStore();engine=policy.Engine(store,'Atlantic/Canary',lambda:datetime.now(timezone.utc),lambda:set())
  await engine.load()
  raw={'name':'Compatibilidad','title':'Prueba','body':'Mensaje de prueba','trigger':'manual','busy':'drop'}
  saved=await engine.command('save',rule=raw,expected_revision=0)
  self.assertEqual(engine.data['rules'][0]['busy'],'drop')
  await engine.enqueue(saved)
  await engine.step(BusySender())
  self.assertEqual(engine.data['queue'],[])
  self.assertEqual(engine.data['logs'][-1]['status'],'failed')
  self.assertEqual(engine.data['logs'][-1]['reason'],'busy')
if __name__=='__main__':unittest.main(verbosity=2)

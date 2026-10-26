"""Internal prompts and handoff JSON must never become Ball STT subtitles."""
from pathlib import Path
from types import SimpleNamespace
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'native_provider'))
from ui_timing_runtime import TimingRuntime

class TimingBoundaryTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.calls=[];self.metadata=[]
  async def infer(*args,**kw):self.calls.append((args,kw));return 'fixture answer'
  async def sender(text,duration):self.metadata.append((text,duration));return {'sent':True}
  self.runtime=TimingRuntime(SimpleNamespace(infer=infer),sender=sender,diagnostic=None)
 async def test_bootstrap_generation_and_native_handoff_do_not_publish_internal_text(self):
  text='INTERNAL FIXTURE: generation or quoted handoff, not spoken STT'
  result=await self.runtime.infer([{'role':'user','content':text}],conversation_id='fixture',bootstrap_session=True)
  self.assertEqual(result,'fixture answer');self.assertEqual(self.metadata,[]);self.assertTrue(self.calls[0][1]['bootstrap_session'])
 async def test_regular_manual_stt_metadata_is_unchanged(self):
  await self.runtime.infer([{'role':'user','content':'Pregunta normal'}],conversation_id='fixture')
  self.assertEqual(self.metadata,[('Pregunta normal',None)])

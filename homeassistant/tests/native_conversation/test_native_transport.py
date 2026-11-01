"""Coordinator -> real native transport. Model and hardware boundaries are fixtures."""
import asyncio
from datetime import datetime,timezone
from types import SimpleNamespace
import unittest
from homeassistant.core import HomeAssistant
from custom_components.ha2_notifications.engine import Engine
from custom_components.ha2_notifications.proactive import Coordinator,DEFAULT_CONFIG
from custom_components.ha2_notifications.native_transport import NativeProactiveTransport
import test_native_starter as n

class Store:
 async def async_save(self,data):self.data=data
 async def async_load(self):return None
class Gate:
 def __init__(self):self.installed=False;self.invalid=False
 def probe(self):return True
 def install(self):self.installed=True;return True
 def arm(self,sid,valid):self.sid=sid;self.valid=valid
 def invalidate(self):self.invalid=True
class TransportIntegration(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  await n.NativeStarterTests.asyncSetUp(self);self.model_calls=[];self.gate=Gate();self.now=datetime(2026,10,25,12,tzinfo=timezone.utc)
  async def caps():return {'native_session_bootstrap':True,'full_agent':True}
  async def infer(**kw):self.model_calls.append(kw);return SimpleNamespace(text='¿Te apetece charlar?')
  self.client=SimpleNamespace(async_proactive_capabilities=caps,async_inference=infer)
  self.ctx=SimpleNamespace(satellite=self.sat,client=self.client,pipeline=SimpleNamespace(language='es'),gate=self.gate,starter=self.starter)
  self.sender.clock=lambda:self.now
  self.sender.target=lambda:{'available':True,'night_active':self.night,'menu_open':False,'card_active':False,'player_idle':not self.busy}
  self.transport=NativeProactiveTransport(self.hass,self.sender,resolver=lambda:self.ctx,cue_media_id='http://fixture.invalid/cue.wav')
  self.engine=Engine(Store(),'Atlantic/Canary',lambda:self.now,lambda:set());await self.engine.load()
  self.coordinator=Coordinator(self.engine,self.transport,lambda coro,name:asyncio.create_task(coro,name=name));await self.coordinator.initialize()
 async def asyncTearDown(self):await self.coordinator.close()
 async def test_due_claim_generates_then_native_announce_and_listen(self):
  await self.coordinator.configure(0,dict(DEFAULT_CONFIG,enabled=True,mode='voice'))
  self.now=datetime.fromisoformat(self.engine.data['proactive']['next_due_at']);await self.coordinator.tick();await self.coordinator.task
  self.assertEqual(self.coordinator.snapshot()['runtime']['status'],'completed')
  self.assertEqual(len(self.model_calls),1);self.assertTrue(self.model_calls[0]['bootstrap_session']);self.assertTrue(self.sent[0]['start_conversation'])
  self.assertEqual(self.engine.data['rules'],[]);self.assertEqual(self.engine.data['queue'],[])
 async def test_night_skips_without_generation_or_audio(self):
  self.night=True;await self.coordinator.configure(0,dict(DEFAULT_CONFIG,enabled=True,mode='voice'));self.now=datetime.fromisoformat(self.engine.data['proactive']['next_due_at']);await self.coordinator.tick()
  self.assertEqual(self.model_calls,[]);self.assertEqual(self.sent,[])
 async def test_cue_uses_native_media_without_synthesizing_voice(self):
  prepared=await self.transport.generate('a'*32,'saludo',dict(DEFAULT_CONFIG),lambda:True)
  result=await self.transport.present(prepared,dict(DEFAULT_CONFIG),lambda:True)
  self.assertTrue(result['completed']);self.assertEqual(len(self.sent),1)
 async def test_missing_companion_feature_is_fail_closed(self):
  async def caps():return {}
  self.client.async_proactive_capabilities=caps
  self.transport._caps_at=0  # Expire the 5s cache populated by initialize().
  caps=await self.transport.capabilities();self.assertFalse(caps['full_agent']);self.assertFalse((await self.transport.readiness())['ready'])

 async def test_default_runtime_is_wired_to_native_transport(self):
  from custom_components.ha2_notifications import Runtime
  runtime=Runtime(self.hass,SimpleNamespace(data={'target_prefix':'fixture','weather_entity':'weather.fixture'}))
  try:self.assertIsInstance(runtime.proactive.transport,NativeProactiveTransport)
  finally:await runtime.proactive.transport.close()

 async def test_short_opener_rejects_over_120_characters_before_audio(self):
  async def infer(**kw):
   self.model_calls.append(kw)
   return SimpleNamespace(text='a'*120+'.')
  self.client.async_inference=infer
  with self.assertRaisesRegex(RuntimeError,'invalid_opener'):
   await self.transport.generate('a'*32,'saludo',dict(DEFAULT_CONFIG),lambda:True)
  self.assertEqual(len(self.model_calls),1)
  self.assertEqual(self.sent,[])
  self.assertIsNone(self.transport.owner)
  self.assertIsNone(self.transport.prepared)

 async def test_short_opener_contract_rejects_multiple_sentences_words_bytes_and_markup(self):
  samples=['Hola. ¿Charlamos?','¿Qué tal? ¿Charlamos?','Hola\n¿Charlamos?',
           'Hola… ¿Charlamos?','Hola。 ¿Charlamos?','¿Charlamos?!',
           ' '.join(['a']*21)+'.','界'*80+'.','**¿Charlamos?**',
           '¿Charlamos?\x00','¿Charlamos?\u2028','Hola\ud800.',
           '¿Charlamos? 😊','Una invitación sin terminar']
  for text in samples:
   with self.subTest(text=ascii(text)):
    async def infer(**kw):
     self.model_calls.append(kw)
     return SimpleNamespace(text=text)
    self.client.async_inference=infer
    before=len(self.model_calls)
    try:
     with self.assertRaisesRegex(RuntimeError,'invalid_opener'):
      await self.transport.generate('a'*32,'saludo',dict(DEFAULT_CONFIG),lambda:True)
     self.assertIsNone(self.transport.owner)
     self.assertIsNone(self.transport.prepared)
     self.assertEqual(self.sent,[])
     self.assertEqual(len(self.model_calls),before+1)
    finally:await self.transport.cancel('a'*32)

 async def test_short_opener_exact_boundaries_and_original_context_are_preserved(self):
  samples=['¿Te apetece charlar sobre ciencia ficción?',"Would you like to chat about today's plans?",
           'á'*119+'.',' '.join(['a']*20)+'.','界'*79+'á'+'.','a\u0301'*59+'.']
  for text in samples:
   with self.subTest(text=ascii(text)):
    async def infer(**kw):return SimpleNamespace(text=text)
    self.client.async_inference=infer
    try:
     prepared=await self.transport.generate('a'*32,'saludo',dict(DEFAULT_CONFIG),lambda:True)
     self.assertEqual(prepared['body'],text)
    finally:await self.transport.cancel('a'*32)

 async def test_short_opener_rejects_bullet_list(self):
  async def infer(**kw):return SimpleNamespace(text='- Hola.')
  self.client.async_inference=infer
  with self.assertRaisesRegex(RuntimeError,'invalid_opener'):
   await self.transport.generate('a'*32,'saludo',dict(DEFAULT_CONFIG),lambda:True)
  self.assertEqual(self.sent,[])

 async def test_short_opener_failure_is_logged_without_text_audio_or_retry(self):
  async def infer(**kw):
   self.model_calls.append(kw)
   return SimpleNamespace(text='Hola. ¿Charlamos?')
  self.client.async_inference=infer
  await self.coordinator.configure(0,dict(DEFAULT_CONFIG,enabled=True,mode='voice'))
  self.now=datetime.fromisoformat(self.engine.data['proactive']['next_due_at'])
  await self.coordinator.tick();await self.coordinator.task
  await self.coordinator.tick()
  self.assertEqual(self.coordinator.snapshot()['runtime']['status'],'failed')
  self.assertEqual(len(self.model_calls),1);self.assertEqual(self.sent,[])
  self.assertNotIn('Hola.',str(self.engine.data))
  self.assertEqual(self.engine.data['queue'],[])

 async def test_short_opener_policy_does_not_restrict_manual_conversation_starter(self):
  result=await self.starter.start('a'*159+'.',lambda:True)
  self.assertTrue(result['completed']);self.assertEqual(len(self.sent),1)

 async def test_short_opener_prompt_declares_the_actual_limits(self):
  prepared=await self.transport.generate('a'*32,'saludo',dict(DEFAULT_CONFIG),lambda:True)
  prompt=self.model_calls[-1]['messages'][0]['content']
  self.assertIn('una única frase',prompt)
  self.assertIn('120 caracteres',prompt)
  self.assertIn('20 palabras',prompt)
  self.assertIn('240 bytes UTF-8',prompt)
  self.assertIn('Sin listas',prompt)
  self.assertEqual(prepared['body'],'¿Te apetece charlar?')

 async def test_short_opener_is_rechecked_before_speech_in_both_modes(self):
  for mode in ('cue','voice'):
   with self.subTest(mode=mode):
    prepared=await self.transport.generate('a'*32,'saludo',dict(DEFAULT_CONFIG),lambda:True)
    prepared['body']='Hola. ¿Charlamos?'
    result=await self.transport.present(prepared,dict(DEFAULT_CONFIG,mode=mode),lambda:True)
    self.assertEqual(result,dict(accepted=False,completed=False,reason='invalid_opener'))
    self.assertEqual(self.sent,[])
    self.assertIsNone(self.transport.owner)
    self.assertIsNone(self.transport.prepared)

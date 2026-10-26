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

"""Native announcement -> listening, using real HA/ESPHome classes."""
import asyncio
from types import SimpleNamespace
import unittest
from homeassistant.core import HomeAssistant
from homeassistant.components.assist_satellite.entity import AssistSatelliteEntity,AssistSatelliteState,AssistSatelliteAnnouncement
from homeassistant.components.esphome.assist_satellite import EsphomeAssistSatellite
from custom_components.ha2_notifications.native_conversation import NativeConversationStarter

class NativeEntity(AssistSatelliteEntity):
 async def async_get_configuration(self):return None
 async def async_set_configuration(self,config):return None
 def on_pipeline_event(self,event):pass
 async_start_conversation=EsphomeAssistSatellite.async_start_conversation
 _do_announce=EsphomeAssistSatellite._do_announce
 def async_write_ha_state(self):pass  # Entity-publication boundary only; use real _set_state.
class NativeStarterTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.hass=HomeAssistant('/config/.ha2-development-tests/native-flow');self.allowed=True;self.night=False;self.busy=False;self.sent=[];self.finished=False
  self.sat=NativeEntity();self.sat.hass=self.hass;self.sat.entity_id='assist_satellite.fixture';self.sat._conversation_id=None;self.sat._extra_system_prompt=None;self.sat._is_announcing=False;self.sat._pipeline_task=None;self.sat._tts_streaming_task=None;self.sat._entry_data=SimpleNamespace(media_player_formats={});self.sat._set_state(AssistSatelliteState.IDLE)
  async def resolve(body,media_id,preannounce_media_id=None):
   if self.prepare_hook:self.prepare_hook()
   return AssistSatelliteAnnouncement(message=body,media_id='http://fixture.invalid/tts.wav',original_media_id='fixture',tts_token=None,media_id_source='tts')
  self.prepare_hook=None;self.sat._resolve_announcement_media_id=resolve
  async def send(media_id,timeout,message,**kw):
   self.sent.append({'message':message,**kw});self.assertFalse(self.finished)
   # API/audio boundary fixture: listening only follows audible-completion ACK.
   self.finished=True;self.sat._set_state(AssistSatelliteState.LISTENING)
  self.sat.cli=SimpleNamespace(send_voice_assistant_announcement_await_response=send)
  async def ready():return 'busy' if self.busy else 'ready'
  self.sender=SimpleNamespace(readiness=ready,night=lambda:self.night)
  self.starter=NativeConversationStarter(self.hass,self.sender,self.sat)
 async def test_native_flag_and_opener_context_before_listening(self):
  result=await self.starter.start('¿Te apetece charlar?',lambda:self.allowed)
  self.assertTrue(result['completed']);self.assertEqual(self.sent,[{'message':'¿Te apetece charlar?','start_conversation':True,'preannounce_media_id':''}]);self.assertTrue(self.finished)
  self.assertEqual(self.sat._extra_system_prompt,'¿Te apetece charlar?');self.assertTrue(self.sat._conversation_id)
 async def test_night_or_busy_never_sends(self):
  self.night=True;r=await self.starter.start('Hola',lambda:self.allowed);self.assertFalse(r['accepted']);self.assertEqual(self.sent,[])
  self.night=False;self.busy=True;r=await self.starter.start('Hola',lambda:self.allowed);self.assertFalse(r['accepted']);self.assertEqual(self.sent,[])
 async def test_foreign_pipeline_is_never_cancelled(self):
  t=asyncio.create_task(asyncio.sleep(60));self.sat._pipeline_task=t
  try:r=await self.starter.start('Hola',lambda:self.allowed);self.assertFalse(r['accepted']);self.assertFalse(t.cancelled());self.assertEqual(self.sent,[])
  finally:t.cancel();await asyncio.gather(t,return_exceptions=True)
 async def test_readiness_rechecked_after_preparing_audio(self):
  self.prepare_hook=lambda:setattr(self,'busy',True)
  r=await self.starter.start('Hola',lambda:self.allowed);self.assertFalse(r['accepted']);self.assertEqual(self.sent,[])
 async def test_acceptance_without_listening_is_not_completion(self):
  async def send(*a,**kw):self.sent.append(kw)
  self.sat.cli.send_voice_assistant_announcement_await_response=send
  self.starter.listen_ack_timeout=.01
  r=await self.starter.start('Hola',lambda:self.allowed);self.assertTrue(r['accepted']);self.assertFalse(r['completed'])
 async def test_foreign_response_state_not_reset_in_cleanup(self):
  foreign=asyncio.create_task(asyncio.sleep(60))
  async def send(*a,**kw):self.sat._tts_streaming_task=foreign
  self.sat.cli.send_voice_assistant_announcement_await_response=send;self.starter.listen_ack_timeout=.01
  try:
   await self.starter.start('Hola',lambda:self.allowed)
   self.assertEqual(self.sat.state,AssistSatelliteState.RESPONDING);self.assertFalse(foreign.cancelled())
  finally:foreign.cancel();await asyncio.gather(foreign,return_exceptions=True)

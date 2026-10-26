"""Exercise the REGISTERED aioesphomeapi ingress, not a replacement attribute."""
import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from aioesphomeapi import APIClient
from aioesphomeapi.api_pb2 import VoiceAssistantRequest,VoiceAssistantResponse,VoiceAssistantAnnounceFinished
from homeassistant.helpers.entity import Entity
from custom_components.ha2_notifications.native_ingress import NativeIngressGate
from custom_components.ha2_notifications import native_conversation as native_version

class Connection:
 def __init__(self):self.callbacks={};self.sent=[]
 def send_message(self,message):self.sent.append(message)
 def add_message_callback(self,callback,types):
  for t in types:self.callbacks.setdefault(t,[]).append(callback)
  def remove():
   for t in types:self.callbacks[t].remove(callback)
  return remove
 def emit(self,message):
  for callback in list(self.callbacks.get(type(message),[])):callback(message)
class Client:
 subscribe_voice_assistant=APIClient.subscribe_voice_assistant
 def __init__(self):self._connection=Connection();self.tasks=[]
 def _get_connection(self):return self._connection
 def _create_background_task(self,coro):self.tasks.append(asyncio.create_task(coro))
class Satellite:
 async_on_remove=Entity.async_on_remove
 def __init__(self):
  self.cli=Client();self._on_remove=[];self._pipeline_task=None;self._tts_streaming_task=None;self._conversation_id='own';self.calls=0;self.finished=0
 async def handle_pipeline_start(self,*args):self.calls+=1;return 0
 async def handle_pipeline_stop(self,*args):pass
 async def handle_audio(self,*args):pass
 async def handle_announcement_finished(self,*args):self.finished+=1
class IngressTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.sat=Satellite();self.allowed=True;self.safe=True
  old=self.sat.cli.subscribe_voice_assistant(handle_start=self.sat.handle_pipeline_start,handle_stop=self.sat.handle_pipeline_stop,handle_audio=self.sat.handle_audio,handle_announcement_finished=self.sat.handle_announcement_finished)
  self.sat.async_on_remove(old)
  self.gate=NativeIngressGate(self.sat,lambda:self.safe,api_audio=True)
 async def asyncTearDown(self):
  for callback in list(self.sat._on_remove):callback()
  await asyncio.sleep(0)
 async def emit(self):
  self.sat.cli._connection.emit(VoiceAssistantRequest(start=True));await asyncio.sleep(0);await asyncio.sleep(0)
 async def test_installed_callback_allows_native_and_manual_but_never_duplicates(self):
  self.assertTrue(self.gate.install());self.assertEqual(len(self.sat.cli._connection.callbacks[VoiceAssistantRequest]),1)
  self.assertTrue(self.gate.install());self.gate.arm('own',lambda:self.allowed);await self.emit();self.assertEqual(self.sat.calls,1)
  await self.emit();self.assertEqual(self.sat.calls,2)
 async def test_foreign_tts_is_not_cancelled_or_dispatched(self):
  self.gate.install();self.gate.arm('own',lambda:self.allowed);task=asyncio.create_task(asyncio.sleep(60));self.sat._tts_streaming_task=task
  try:
   await self.emit();self.assertEqual(self.sat.calls,0);self.assertFalse(task.cancelled())
   self.assertTrue(any(isinstance(m,VoiceAssistantResponse) and m.error for m in self.sat.cli._connection.sent))
  finally:task.cancel();await asyncio.gather(task,return_exceptions=True)
 async def test_invalidated_announcement_cannot_reopen_listening(self):
  self.gate.install();self.gate.arm('own',lambda:self.allowed);self.gate.invalidate();await self.emit();self.assertEqual(self.sat.calls,0)
  await self.emit();self.assertEqual(self.sat.calls,1)
 async def test_night_or_menu_at_ingress_rejects_without_stopping_audio(self):
  self.gate.install();self.gate.arm('own',lambda:self.allowed);self.safe=False;await self.emit();self.assertEqual(self.sat.calls,0)
 async def test_explicit_device_stop_releases_pending_then_manual_works(self):
  self.gate.install();self.gate.arm('own',lambda:self.allowed);self.gate.invalidate()
  self.sat.cli._connection.emit(VoiceAssistantRequest(start=False));await asyncio.sleep(0);await asyncio.sleep(0)
  await self.emit();self.assertEqual(self.sat.calls,1)
 async def test_late_announcement_ack_does_not_finish_foreign_tts(self):
  self.gate.install();self.gate.arm('own',lambda:self.allowed);task=asyncio.create_task(asyncio.sleep(60));self.sat._tts_streaming_task=task
  try:
   self.sat.cli._connection.emit(VoiceAssistantAnnounceFinished(success=True));await asyncio.sleep(0);await asyncio.sleep(0)
   self.assertEqual(self.sat.finished,0);self.assertFalse(task.cancelled())
  finally:task.cancel();await asyncio.gather(task,return_exceptions=True)
 async def test_unknown_subscription_is_fail_closed_and_does_not_mutate(self):
  self.sat._on_remove=[];before=list(self.sat.cli._connection.sent);self.assertFalse(self.gate.install());self.assertEqual(self.sat.cli._connection.sent,before)
  # Clean up fixture subscription whose public entity-removal receipt was hidden.
  for callbacks in self.sat.cli._connection.callbacks.values():callbacks.clear()
 async def test_unknown_ha_version_never_changes_subscription(self):
  before=list(self.sat.cli._connection.sent)
  with patch.object(native_version,'HA_VERSION','unknown',create=True):self.assertFalse(self.gate.install())
  self.assertEqual(self.sat.cli._connection.sent,before)
 async def test_failed_announcement_never_allows_a_late_automatic_start(self):
  self.gate.install();self.gate.arm('own',lambda:self.allowed)
  self.sat.cli._connection.emit(VoiceAssistantAnnounceFinished(success=False));await asyncio.sleep(0);await asyncio.sleep(0)
  await self.emit();self.assertEqual(self.sat.calls,0)

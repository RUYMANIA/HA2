"""Per-device native ingress guard, installed through the public subscription.

No core edits, global monkeypatches or edits to captured closure cells. Resolve
and replace this entity's existing subscription at idle; retain its cleanup.
"""
from __future__ import annotations
import hashlib
import inspect
from aioesphomeapi import APIClient
from .native_conversation import NativeConversationStarter

SUBSCRIPTION_HASH='3eb68c90fe2a4103e8361d360c83a66e8798db3d86436fe26c1673bd8c4ec922'

class NativeIngressGate:
    def __init__(self,satellite,safe,*,api_audio):
        self.satellite,self.safe,self.api_audio=satellite,safe,api_audio
        self.installed=False;self.pending=None
        self.connection=None;self.started_conversation=None;self.started_task=None
        self.original_start=satellite.handle_pipeline_start

    def _kwargs(self,handler):
        sat=self.satellite
        values=dict(handle_start=handler,handle_stop=self.handle_stop if handler==self.handle_start else sat.handle_pipeline_stop,
                    handle_announcement_finished=self.handle_announcement_finished if handler==self.handle_start else sat.handle_announcement_finished)
        if self.api_audio:values['handle_audio']=sat.handle_audio
        return values

    def install(self):
        if self.installed:return self.connection is self.satellite.cli._connection
        if not NativeConversationStarter.compatible() or not self.safe():return False
        if hashlib.sha256(inspect.getsource(APIClient.subscribe_voice_assistant).encode()).hexdigest()!=SUBSCRIPTION_HASH:return False
        sat=self.satellite
        for name in ('_pipeline_task','_tts_streaming_task'):
            task=getattr(sat,name,None)
            if task is not None and not task.done():return False
        callbacks=getattr(sat,'_on_remove',None)
        if not isinstance(callbacks,list):return False
        matches=[]
        for callback in callbacks:
            if getattr(callback,'__qualname__','')!='APIClient.subscribe_voice_assistant.<locals>.unsub':continue
            cells=dict(zip(callback.__code__.co_freevars,callback.__closure__ or ()))
            if 'self' in cells and cells['self'].cell_contents is sat.cli:matches.append(callback)
        if len(matches)!=1:return False
        old=matches[0]
        # No await between idle admission, unsubscribe and resubscribe.
        old()
        try:new=sat.cli.subscribe_voice_assistant(**self._kwargs(self.handle_start))
        except Exception:
            callbacks.remove(old)
            try:sat.async_on_remove(sat.cli.subscribe_voice_assistant(**self._kwargs(self.original_start)))
            except Exception:pass
            return False
        callbacks.remove(old);sat.async_on_remove(new);self.installed=True
        self.connection=sat.cli._connection
        return True

    def probe(self):
        if not NativeConversationStarter.compatible():return False
        if hashlib.sha256(inspect.getsource(APIClient.subscribe_voice_assistant).encode()).hexdigest()!=SUBSCRIPTION_HASH:return False
        if self.installed:return self.connection is self.satellite.cli._connection
        matches=[]
        for callback in getattr(self.satellite,'_on_remove',None) or ():
            if getattr(callback,'__qualname__','')!='APIClient.subscribe_voice_assistant.<locals>.unsub':continue
            cells=dict(zip(callback.__code__.co_freevars,callback.__closure__ or ()))
            if 'self' in cells and cells['self'].cell_contents is self.satellite.cli:matches.append(callback)
        return len(matches)==1

    async def handle_announcement_finished(self,finished):
        foreign=False
        if self.pending is not None:
            for name in ('_pipeline_task','_tts_streaming_task'):
                task=getattr(self.satellite,name,None)
                if task is not None and not task.done():foreign=True
        if not foreign:await self.satellite.handle_announcement_finished(finished)
        if self.pending is not None and self.satellite._conversation_id==self.pending['conversation_id']:
            self.satellite._is_announcing=False
            if getattr(finished,'success',None) is False:self.pending['invalid']=True

    async def handle_stop(self,abort):
        # An explicit device STOP clears native continue_conversation as well.
        # Do not reject the user's next manual start because of an old tombstone.
        if abort:self.pending=None
        await self.satellite.handle_pipeline_stop(abort)

    def arm(self,conversation_id,valid):
        if not self.installed or self.pending is not None:raise RuntimeError('native_ingress_unavailable')
        self.pending=dict(conversation_id=conversation_id,valid=valid,invalid=False)
        self.started_conversation=None;self.started_task=None

    def invalidate(self):
        # Keep a tombstone until the queued start is rejected. Merely restoring a
        # callback would let a late automatic request escape cancellation.
        if self.pending is not None:self.pending['invalid']=True

    async def handle_start(self,conversation_id,flags,audio_settings,wake_word_phrase):
        pending=self.pending
        if pending is None:
            return await self.original_start(conversation_id,flags,audio_settings,wake_word_phrase)
        self.pending=None
        try:
            allowed=(not pending['invalid'] and pending['valid']()
                     and self.satellite._conversation_id==pending['conversation_id'] and self.safe())
            for name in ('_pipeline_task','_tts_streaming_task'):
                task=getattr(self.satellite,name,None)
                if task is not None and not task.done():allowed=False
        except Exception:allowed=False
        if not allowed:
            # APIClient's registered dispatcher sends VoiceAssistantResponse(error=True).
            # In particular, never enter native handle_pipeline_start: it cancels TTS.
            return None
        result=await self.original_start(conversation_id,flags,audio_settings,wake_word_phrase)
        self.started_conversation=pending['conversation_id']
        self.started_task=getattr(self.satellite,'_pipeline_task',None)
        return result

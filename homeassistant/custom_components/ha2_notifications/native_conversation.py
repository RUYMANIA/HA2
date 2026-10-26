"""Native announcement -> native listening. No VAD override or core patches.

Only the HA/ESPHome audio boundary is used. The high-level HA wrapper is not
called because it cancels a running pipeline before checking availability.
This class does NOT claim end-to-end physical acceptance or a race guard.
"""
from __future__ import annotations
import asyncio
import inspect
import hashlib
import time
from homeassistant.components import conversation
from homeassistant.helpers import chat_session
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.components.assist_satellite.entity import AssistSatelliteState
from homeassistant.components.esphome.assist_satellite import EsphomeAssistSatellite

# Compatibility fingerprint only; no production readiness is inferred from a hash.
EXPECTED_START_HASH='44dc85329f3b6957f6d4711c59531e5045455fb1b04403b5ed6d912e8338c559'

class NativeConversationStarter:
    def __init__(self,hass,sender,satellite,*,sleep=asyncio.sleep,monotonic=time.monotonic,gate=None):
        self.hass,self.sender,self.satellite=hass,sender,satellite
        self.sleep,self.monotonic=sleep,monotonic
        self.listen_ack_timeout=5.0  # ACK watchdog, NOT microphone listening duration.
        self.active=False
        self.gate=gate;self.conversation_id=None

    @staticmethod
    def compatible():
        return HA_VERSION=='2026.7.2' and hashlib.sha256(inspect.getsource(EsphomeAssistSatellite.handle_pipeline_start).encode()).hexdigest()==EXPECTED_START_HASH

    def _has_foreign_task(self):
        for name in ('_pipeline_task','_tts_streaming_task'):
            task=getattr(self.satellite,name,None)
            if task is not None and not task.done():return True
        return False

    async def _ready(self,valid):
        return (valid() and not self.sender.night() and not self._has_foreign_task()
                and not self.satellite._is_announcing and await self.sender.readiness()=='ready')

    async def start(self,body,valid,*,media_id=None):
        if not isinstance(body,str) or not body.strip() or len(body)>400 or len(body.encode())>480:
            return dict(accepted=False,completed=False,reason='invalid_body')
        if self.active:return dict(accepted=False,completed=False,reason='busy')
        self.active=True
        self.conversation_id=None
        sat=self.satellite;sid=None;accepted=False;audio_ack=False;completed=False
        previous_id=sat._conversation_id;previous_extra=sat._extra_system_prompt
        try:
            if not await self._ready(valid):return dict(accepted=False,completed=False,reason='guard_blocked')
            announcement=await sat._resolve_announcement_media_id(body,media_id,preannounce_media_id=None)
            # Final admission is after any awaited media resolution. There is no
            # _cancel_running_pipeline, media STOP, or replay in this path.
            if not await self._ready(valid):return dict(accepted=False,completed=False,reason='guard_blocked')
            with chat_session.async_get_chat_session(self.hass) as session:
                with conversation.async_get_chat_log(self.hass,session) as log:
                    log.async_add_assistant_content_without_tools(conversation.AssistantContent(agent_id=sat.entity_id,content=body))
                sid=session.conversation_id
            sat._conversation_id=sid;sat._extra_system_prompt=body
            self.conversation_id=sid
            if self.gate is not None:self.gate.arm(sid,valid)
            sat._is_announcing=True;sat._set_state(AssistSatelliteState.RESPONDING)
            accepted=True
            await sat.async_start_conversation(announcement)
            audio_ack=True
            deadline=self.monotonic()+self.listen_ack_timeout
            while self.monotonic()<deadline:
                if not valid() or self.sender.night() or sat._conversation_id!=sid:
                    return dict(accepted=True,completed=False,reason='ownership_or_policy_changed')
                if sat.state==AssistSatelliteState.LISTENING:
                    completed=True
                    return dict(accepted=True,completed=True,reason=None)
                await self.sleep(.02)
            return dict(accepted=True,completed=False,reason='listen_unconfirmed')
        except asyncio.CancelledError:
            if self.gate is not None:self.gate.invalidate()
            raise
        except Exception:
            return dict(accepted=accepted,completed=False,reason='native_start_failed')
        finally:
            self.active=False
            if self.gate is not None and accepted and not completed:self.gate.invalidate()
            if sid is not None and sat._conversation_id==sid and (audio_ack or not accepted):
                sat._is_announcing=False
                # Do not mark a listening pipeline idle or overwrite another turn.
                if sat.state==AssistSatelliteState.RESPONDING and not self._has_foreign_task():
                    sat._set_state(AssistSatelliteState.IDLE)
                if not accepted:
                    sat._conversation_id=previous_id;sat._extra_system_prompt=previous_extra

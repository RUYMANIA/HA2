"""Existing HA coordinator -> full Hermes -> native announcement/listening.

No card transport, extra scheduler, fixed microphone timeout or model override.
All external effects stay behind real companion and native-ingress capabilities.
"""
from __future__ import annotations
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import time
from homeassistant.components import conversation
from homeassistant.components.assist_pipeline import pipeline
from homeassistant.components.esphome import assist_satellite as esp_satellite
from homeassistant.helpers.network import get_url
from .native_conversation import NativeConversationStarter
from .native_ingress import NativeIngressGate
from .proactive import CAPABILITY_KEYS,INTENT_IDS

class NativeProactiveTransport:
    def __init__(self,hass,sender,*,resolver=None,cue_media_id=None):
        self.hass,self.sender=hass,sender;self.resolver=resolver
        self.closed=False;self.owner=None;self.context=None;self.prepared=None
        self._cached_caps=None;self._caps_at=0.;self._cached_client=None
        self.cue_media_id=cue_media_id
        if self.cue_media_id is None and (Path(__file__).parent/'static'/'proactive-three-notes.wav').is_file():
            try:self.cue_media_id=get_url(hass,allow_external=False,allow_cloud=False).rstrip('/')+'/ha2-notifications-static/proactive-three-notes.wav'
            except Exception:pass

    def _safe_ingress(self):
        try:
            t=self.sender.target()
            return (not self.closed and t.get('available') is True and t.get('night_active') is False
                    and t.get('menu_open') is False and t.get('card_active') is False and t.get('player_idle') is True)
        except Exception:return False

    def _resolve(self):
        if self.resolver is not None:return self.resolver()
        component=self.hass.data.get('assist_satellite')
        sat=component.get_entity(f'assist_satellite.{self.sender.prefix}_assist_satellite') if component else None
        if sat is None:raise RuntimeError('native_target_unavailable')
        selected=pipeline.async_get_pipeline(self.hass,sat._resolve_pipeline())
        agent=conversation.async_get_agent(self.hass,selected.conversation_engine)
        client=getattr(agent,'_client',None)
        if client is None or not hasattr(client,'async_proactive_capabilities'):raise RuntimeError('native_agent_unavailable')
        info=sat._entry_data.device_info
        flags=info.voice_assistant_feature_flags_compat(sat._entry_data.api_version)
        api_audio=bool(flags & esp_satellite.VoiceAssistantFeature.API_AUDIO)
        if flags & esp_satellite.VoiceAssistantFeature.SPEAKER and not api_audio:
            raise RuntimeError('unverified_udp_start_boundary')
        gate=getattr(sat,'_ha2_native_ingress_gate',None)
        if gate is None:
            gate=NativeIngressGate(sat,self._safe_ingress,api_audio=api_audio)
            sat._ha2_native_ingress_gate=gate
        else:gate.safe=self._safe_ingress
        if self.context is not None and self.context.satellite is sat and self.context.client is client:
            return self.context
        return SimpleNamespace(satellite=sat,client=client,pipeline=selected,gate=gate,
                               starter=NativeConversationStarter(self.hass,self.sender,sat,gate=gate))

    async def capabilities(self):
        caps=dict.fromkeys(CAPABILITY_KEYS,False)
        if self.closed:return caps
        try:
            ctx=self._resolve()
            if self._cached_caps is None or self._cached_client is not ctx.client or time.monotonic()-self._caps_at>5:
                self._cached_caps=await ctx.client.async_proactive_capabilities()
                self._cached_client=ctx.client;self._caps_at=time.monotonic()
            full=self._cached_caps.get('full_agent') is True
            bound=self._cached_caps.get('native_session_bootstrap') is True
            caps.update(full_agent=full,session_binding=bound,
                        native_listen=ctx.gate.probe(),transcript_only=self.cue_media_id is not None)
        except Exception:pass
        return caps

    async def readiness(self):
        try:
            caps=await self.capabilities()
            if not all(caps[k] for k in ('full_agent','session_binding','native_listen')):
                return dict(ready=False,reason='unavailable')
            ctx=self._resolve()
            if self.context is not None and self.context.starter.active and self.context.starter.conversation_id is not None:
                target=self.sender.target();sat=ctx.satellite
                same=(ctx.satellite is self.context.satellite and sat._conversation_id==self.context.starter.conversation_id)
                safe=(target.get('available') is True and target.get('night_active') is False
                      and target.get('menu_open') is False and target.get('card_active') is False)
                return dict(ready=bool(same and safe),reason=None if same and safe else 'busy')
            ready=self._safe_ingress() and await self.sender.readiness()=='ready'
            return dict(ready=bool(ready),reason=None if ready else 'busy')
        except Exception:return dict(ready=False,reason='unavailable')

    async def generate(self,request_id,intent_id,config,valid):
        if self.closed or self.owner is not None or intent_id not in INTENT_IDS or not valid():raise RuntimeError('unavailable')
        if not (await self.readiness())['ready']:raise RuntimeError('unavailable')
        ctx=self._resolve()
        if not ctx.gate.install():raise RuntimeError('native_ingress_unavailable')
        self.owner=request_id;self.context=ctx
        local=self.sender.clock().astimezone(ZoneInfo(self.hass.config.time_zone)).strftime('%H:%M')
        prompt=(f'Genera sólo una invitación breve y natural a charlar, máximo180caracteres. '
                f'Intención:{intent_id};hora local:{local};idioma:{ctx.pipeline.language}. '
                'Terminal compartido: no identifiques a nadie, no uses nombres ni datos privados, '
                'no atribuyas aburrimiento o necesidad emocional, no presiones ni culpabilices. '
                'No uses herramientas ni envíes mensajes: devuelve únicamente la invitación.')
        try:
            result=await ctx.client.async_inference(messages=[dict(role='user',content=prompt)],
                conversation_id=request_id,language=ctx.pipeline.language,bootstrap_session=True)
            body=getattr(result,'text',None)
            if not valid() or not isinstance(body,str) or not body.strip() or len(body)>400 or len(body.encode())>480:
                raise RuntimeError('invalid_opener')
            self.prepared=dict(request_id=request_id,body=body,context=ctx)
            return self.prepared
        except BaseException:
            self.owner=None;self.prepared=None
            raise

    async def present(self,prepared,config,valid):
        if prepared is not self.prepared or prepared['request_id']!=self.owner or not valid():
            return dict(accepted=False,completed=False,reason='ownership_changed')
        ctx=self._resolve()
        if ctx.satellite is not prepared['context'].satellite or ctx.client is not prepared['context'].client:
            return dict(accepted=False,completed=False,reason='target_changed')
        if config['mode']=='cue' and self.cue_media_id is None:
            return dict(accepted=False,completed=False,reason='cue_unavailable')
        try:
            return await ctx.starter.start(prepared['body'],valid,
                media_id=self.cue_media_id if config['mode']=='cue' else None)
        finally:self.owner=None;self.prepared=None

    async def cancel(self,request_id):
        if request_id!=self.owner:return
        if self.context is not None:self.context.gate.invalidate()
        self.owner=None;self.prepared=None
        # Never media STOP or cancellation of a foreign/native conversation task.

    async def close(self):
        self.closed=True
        if self.owner is not None:await self.cancel(self.owner)

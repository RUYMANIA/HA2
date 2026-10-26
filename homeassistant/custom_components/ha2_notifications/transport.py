"""HA-native card transport; no shell, sockets, selectors, volume or STOP."""
from __future__ import annotations
import asyncio
import json
import time
import math
import re
import ipaddress
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from homeassistant.components import tts
from homeassistant.components.assist_pipeline import pipeline
from homeassistant.helpers.network import get_url
from .engine import Error, identifier

class Sender:
    def __init__(self,hass,prefix,weather_entity,clock,monotonic=time.monotonic,sleep=asyncio.sleep):
        self.hass,self.prefix,self.weather_entity,self.clock=hass,prefix,weather_entity,clock
        self.monotonic,self.sleep=monotonic,sleep

    def state(self,domain,suffix=''):
        entity=f'{domain}.{self.prefix}{suffix}'
        value=self.hass.states.get(entity)
        if value is None or value.state in ('unknown','unavailable'): raise Error('unavailable')
        return value

    def json_state(self,suffix):
        try:
            value=json.loads(self.state('sensor',suffix).state)
            if not isinstance(value,dict): raise ValueError
            return value
        except (ValueError,TypeError): raise Error('unavailable') from None

    def status(self):
        value=self.json_state('_card_status')
        try:
            if value.get('request_id'): identifier(value['request_id'])
            elif value.get('request_id')!='': raise ValueError
            if type(value.get('generation')) is not int or value['generation']<0: raise ValueError
            if type(value.get('visible')) is not bool: raise ValueError
            if value.get('state') not in ('idle','pending','shown','playing','audio_done','dismissed','expired','interrupted','rejected'): raise ValueError
            if value.get('audio') not in ('none','waiting','playing','done','cancelled','failed','suppressed'): raise ValueError
            return value
        except (ValueError,Error): raise Error('unavailable') from None

    def night(self):
        value=self.json_state('_ui_night').get('night_active')
        if type(value) is not bool and not (type(value) is int and value in (0,1)): raise Error('unavailable')
        return bool(value)

    def target(self):
        target={'name':'XiaoZhi Ball v2','available':False,'night_active':None,
                'card_active':None,'menu_open':None,'player_idle':None}
        try:
            target['night_active']=self.night()
            active=self.state('binary_sensor','_card_active').state
            if active not in ('on','off'): raise Error('unavailable')
            target['card_active']=active=='on'
            page=self.json_state('_ui_status').get('page')
            if not isinstance(page,str) or not page: raise Error('unavailable')
            target['menu_open']=page!='closed'
            target['player_idle']=self.state('media_player').state=='idle'
            self.state('assist_satellite','_assist_satellite')
            self.status()
            target['available']=True
        except Error: pass
        return target

    async def readiness(self):
        target=self.target()
        if not target['available']: return 'unavailable'
        status=self.status()
        if (target['card_active'] or target['menu_open'] or not target['player_idle']
            or self.state('assist_satellite','_assist_satellite').state!='idle'
            or status['visible'] or status['state'] in ('pending','shown','playing')
            or status['audio'] in ('playing','waiting')): return 'busy'
        return 'ready'

    async def prepare(self,body):
        try:
            choice=self.state('select','_assistant').state
            if choice=='preferred': resolved=pipeline.async_get_pipeline(self.hass,None)
            else:
                matches=[p for p in pipeline.async_get_pipelines(self.hass) if p.name==choice]
                if len(matches)!=1: raise Error('config_error')
                resolved=matches[0]
            if not resolved.tts_engine or not resolved.tts_language: raise Error('config_error')
            options={'preferred_format':'wav','preferred_sample_rate':48000,
                     'preferred_sample_channels':1,'preferred_sample_bytes':2}
            if resolved.tts_voice is not None: options['voice']=resolved.tts_voice
            base=get_url(self.hass,allow_external=False,allow_cloud=False)
            parsed=urlsplit(base)
            if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment or parsed.hostname in ('localhost','host.docker.internal'): raise Error('config_error')
            try:
                address=ipaddress.ip_address(parsed.hostname)
                if address.is_loopback or address.is_unspecified or address.is_link_local: raise Error('config_error')
            except ValueError: pass
            manager=self.hass.data[tts.DATA_TTS_MANAGER]
            stream=manager.async_create_result_stream(resolved.tts_engine,use_file_cache=False,language=resolved.tts_language,options=options)
            stream.async_set_message(body)
            if not re.fullmatch(r'/api/tts_proxy/[A-Za-z0-9_.-]+',stream.url) or '..' in stream.url: raise Error('config_error')
            url=base.rstrip('/')+stream.url
            if len(url)>384: raise Error('config_error')
            return url
        except Error: raise
        except Exception: raise Error('config_error') from None

    def weather_text(self):
        state=self.hass.states.get(self.weather_entity)
        if state is None or state.state in ('unknown','unavailable'): raise Error('unavailable')
        conditions={'clear-night':'Despejado','cloudy':'Nublado','exceptional':'Tiempo adverso','fog':'Niebla','hail':'Granizo','lightning':'Tormenta','lightning-rainy':'Tormenta y lluvia','partlycloudy':'Intervalos nubosos','pouring':'Lluvia intensa','rainy':'Lluvia','snowy':'Nieve','snowy-rainy':'Aguanieve','sunny':'Soleado','windy':'Viento','windy-variant':'Viento y nubes'}
        lines=[conditions.get(state.state,'Estado: '+state.state)]
        attrs=state.attributes
        for key,label,unit_key in (('temperature','Temperatura','temperature_unit'),('humidity','Humedad','%'),('wind_speed','Viento','wind_speed_unit')):
            value=attrs.get(key);unit='%' if unit_key=='%' else attrs.get(unit_key)
            if type(value) in (int,float) and math.isfinite(value) and unit:
                lines.append(f'{label}: '+format(value,'g').replace('.',',')+' '+str(unit))
        lines.append('Datos HA '+state.last_updated.astimezone(ZoneInfo(self.hass.config.time_zone)).strftime('%d/%m %H:%M'))
        body='\n'.join(lines)
        if len(body)>4000 or len(body.encode())>4096: raise Error('config_error')
        return body

    async def call(self,action,data):
        await asyncio.wait_for(self.hass.services.async_call('esphome',self.prefix+'_'+action,data,blocking=True),5)

    async def deliver(self,item,claim,valid):
        request_id=item['request_id'];rule=item['rule'];submitted=False
        try:
            if not valid(): return 'cancelled','configuration_changed'
            readiness=await self.readiness()
            if readiness!='ready': return 'waiting',readiness
            baseline=self.status()['generation']
            night=self.night()
            body=rule['body']
            if rule['kind']=='weather': body=self.weather_text()
            url=None
            if rule['mode']=='voice' and not night:
                url=await asyncio.wait_for(self.prepare(body),10)
            if not valid(): return 'cancelled','configuration_changed'
            readiness=await self.readiness()
            if readiness!='ready': return 'waiting',readiness
            night=night or self.night()
            baseline=self.status()['generation']
            await claim(baseline)
            if not valid(): return 'cancelled','configuration_changed'
            submitted=True
            await self.call('card_show',{'request_id':request_id,'title':rule['title'],'body':body,
                            'kind':rule['kind'],'ttl_ms':30000,'audio_expected':rule['mode']=='voice' and not night})
            deadline=self.monotonic()+3
            generation=None
            while self.monotonic()<deadline:
                if not valid(): return 'cancelled','configuration_changed'
                status=self.status()
                if status['request_id']==request_id:
                    if status['generation']<=baseline: return 'uncertain','stale_ack'
                    if status['state']=='shown' and status['visible']:
                        generation=status['generation'];break
                    if status['state'] in ('rejected','dismissed','expired','interrupted'): return 'failed','card_rejected'
                elif status['generation']>baseline: return 'uncertain','producer_conflict'
                await self.sleep(.1)
            if generation is None: return 'uncertain','show_unconfirmed'
            if status.get('truncated'): return 'delivered','truncated'
            if night or self.night() or status['audio']=='suppressed': return 'night_silent','night_mode'
            if rule['mode']!='voice': return 'delivered',''
            status=self.status()
            if (status['request_id']!=request_id or status['generation']!=generation or not status['visible']): return 'uncertain','ownership_changed'
            if (self.state('media_player').state!='idle' or self.state('assist_satellite','_assist_satellite').state!='idle' or self.json_state('_ui_status').get('page')!='closed'): return 'delivered','audio_busy'
            if not valid(): return 'delivered','audio_cancelled'
            await self.call('card_play',{'request_id':request_id,'url':url})
            deadline=self.monotonic()+120
            while self.monotonic()<deadline:
                if not valid(): return 'delivered','audio_cancelled'
                status=self.status()
                if status['request_id']!=request_id or status['generation']!=generation: return 'uncertain','ownership_changed'
                if status['audio']=='suppressed' and status.get('reason')=='night_mode': return 'night_silent','night_mode'
                if status['state']=='audio_done' and status['audio']=='done': return 'audio_done',''
                if status['state'] in ('rejected','expired','interrupted','dismissed') or status['audio'] in ('failed','cancelled'): return 'delivered','audio_unconfirmed'
                await self.sleep(.1)
            return 'delivered','audio_unconfirmed'
        except asyncio.CancelledError: raise
        except Error as exc:
            reason=str(exc)
            return ('uncertain' if submitted else 'failed'), reason if reason in ('unavailable','config_error') else 'preparation_failed'
        except Exception:
            return ('uncertain' if submitted else 'failed'),'transport_error'

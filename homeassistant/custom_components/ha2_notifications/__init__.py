"""HA² Notifications — admin-only native integration, staging 0.3.0."""
from __future__ import annotations
import asyncio
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import re
import voluptuous as vol
from homeassistant.components import websocket_api, panel_custom, frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ConfigEntryNotReady
from homeassistant.helpers.storage import Store
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.components.vacuum import VacuumActivity
from .engine import Engine, Error
from .transport import Sender
from .proactive import Coordinator, ClosedTransport
from .native_transport import NativeProactiveTransport

DOMAIN='ha2_notifications'
VERSION='0.3.0'
ENTITY_DOMAINS={'sensor','binary_sensor','input_boolean','input_select','switch','timer',
                'vacuum','light','cover','lock','climate','fan','media_player','select',
                'number','input_number'}


def strict_int(value):
    if type(value) is not int or value<0: raise vol.Invalid('Expected a nonnegative integer')
    return value


def strict_bool(value):
    if type(value) is not bool: raise vol.Invalid('Expected a boolean')
    return value


def validate_target(hass,data):
    prefix=data.get('target_prefix','xiaozhi_ball_v2')
    weather=data.get('weather_entity','weather.forecast_casa')
    if not isinstance(prefix,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}',prefix) or not isinstance(weather,str) or not re.fullmatch(r'weather\.[a-z0-9_]+',weather): raise Error('config_error')
    entities=[f'{domain}.{prefix}{suffix}' for domain,suffix in (
        ('sensor','_card_status'),('sensor','_ui_status'),('sensor','_ui_night'),
        ('binary_sensor','_card_active'),('media_player',''),
        ('assist_satellite','_assist_satellite'),('select','_assistant'))]+[weather]
    if any(hass.states.get(entity) is None for entity in entities): raise Error('config_error')
    if any(not hass.services.has_service('esphome',prefix+'_'+name) for name in ('card_show','card_play','card_cancel')): raise Error('config_error')
    return {'target_prefix':prefix,'weather_entity':weather}


class Runtime:
    def __init__(self,hass,entry,proactive_transport=None):
        self.hass,self.entry=hass,entry
        self.stopped=False;self.tasks=set();self.worker=None;self.unsubscribe=None
        self.sender=Sender(hass,entry.data['target_prefix'],entry.data['weather_entity'],lambda:datetime.now(timezone.utc))
        self.engine=Engine(Store(hass,1,DOMAIN,private=True,atomic_writes=True),hass.config.time_zone,
                           lambda:datetime.now(timezone.utc),lambda:{v['entity_id'] for v in self.entity_options()})
        self.proactive=Coordinator(self.engine,proactive_transport if proactive_transport is not None else NativeProactiveTransport(hass,self.sender),hass.async_create_background_task)

    def entity_options(self):
        result=[]
        for state in self.hass.states.async_all():
            if state.domain not in ENTITY_DOMAINS: continue
            declared=state.attributes.get('options')
            if state.domain=='climate' and not isinstance(declared,list):
                declared=state.attributes.get('hvac_modes')
            if isinstance(declared,list):
                values=declared;source='declared'
            elif state.domain in ('binary_sensor','input_boolean','switch','light','fan'):
                values=['off','on'];source='domain'
            elif state.domain=='vacuum':
                values=[activity.value for activity in VacuumActivity];source='domain'
            else:
                values=[];source='current'
            valid=lambda value: isinstance(value,str) and bool(value.strip()) and len(value)<=255 and value not in ('unknown','unavailable')
            options=list(dict.fromkeys(value for value in values if valid(value)))[:63]
            if valid(state.state) and state.state not in options: options.append(state.state)
            result.append({'entity_id':state.entity_id,'name':state.name,'state':state.state,
                           'state_options':options,'state_options_source':source})
        return sorted(result,key=lambda item:item['entity_id'])

    def snapshot(self):
        data=self.engine.data
        return {'version':VERSION,'revision':data['revision'],'paused':data['paused'],
                'rules':deepcopy(data['rules']),'logs':deepcopy(data['logs']),
                'queue_count':len(data['queue']),'timezone':self.hass.config.time_zone,
                'weather_entity':self.entry.data['weather_entity'],'target':self.sender.target(),
                'entity_options':self.entity_options(),'hermes_cron':self.engine.cron_snapshot(),
                'proactive':self.proactive.snapshot(),
                'capabilities':{'voice':True,'triggers':['weekly','once','state','manual']}}

    async def run(self):
        while not self.stopped:
            try:
                await self.engine.schedule()
            except asyncio.CancelledError: raise
            except Exception: pass
            try:
                await self.proactive.tick()
            except asyncio.CancelledError: raise
            except Exception: pass
            try:
                await self.engine.step(self.sender)
            except asyncio.CancelledError: raise
            except Exception:
                # Storage/transient IO failure: no effects without committed claim.
                # Public logs never receive upstream exceptions or content.
                pass
            await asyncio.sleep(1)

    @callback
    def on_state(self,event):
        if self.stopped: return
        entity=event.data['entity_id']
        if not any(r['enabled'] and r['trigger']=='state' and r['entity_id']==entity for r in self.engine.data['rules']): return
        old,new=event.data.get('old_state'),event.data.get('new_state')
        async def process():
            try: await self.engine.state_changed(entity,old.state if old else None,new.state if new else None)
            except Error: pass
        task=self.hass.async_create_background_task(process(),'HA² state transition')
        self.tasks.add(task);task.add_done_callback(self.tasks.discard)

    async def close(self):
        self.stopped=True
        if self.unsubscribe: self.unsubscribe();self.unsubscribe=None
        pending=list(self.tasks)+([self.worker] if self.worker else [])
        for task in pending: task.cancel()
        if pending: await asyncio.gather(*pending,return_exceptions=True)
        self.tasks.clear()
        await self.proactive.close()


def runtime(hass):
    value=hass.data.get(DOMAIN,{}).get('runtime')
    if value is None or value.stopped: raise Error('unavailable')
    return value


def register_ws(hass):
    fields={
        'proactive_config':{vol.Required('expected_revision'):strict_int,vol.Required('config'):dict},
        'get':{},'save':{vol.Required('rule'):dict,vol.Required('expected_revision'):strict_int},
        'delete':{vol.Required('rule_id'):str,vol.Required('expected_revision'):strict_int},
        'toggle':{vol.Required('rule_id'):str,vol.Required('enabled'):strict_bool,vol.Required('expected_revision'):strict_int},
        'pause':{vol.Required('paused'):strict_bool,vol.Required('expected_revision'):strict_int},
        'test':{vol.Required('rule_id'):str},
        'cron_sync':{vol.Required('source_instance'):str,vol.Required('profile'):str,
                     vol.Required('jobs'):[vol.Schema({vol.Required('job_id'):str,vol.Required('name'):str,vol.Required('schedule'):str,vol.Required('enabled'):strict_bool,vol.Required('no_agent'):strict_bool,vol.Required('delivery'):vol.In(('local','telegram','discord','slack','email','other')),vol.Required('excerpt_available'):strict_bool})]},
        'cron_policy':{vol.Required('job_key'):str,vol.Required('expected_revision'):strict_int,vol.Required('enabled'):strict_bool,vol.Required('content'):vol.In(('brief','excerpt')),vol.Required('mode'):vol.In(('cue','voice')),vol.Required('title'):str},
        'cron_result':{vol.Required('source_instance'):str,vol.Required('profile'):str,vol.Required('job_id'):str,
                       vol.Required('result'):vol.Schema({vol.Required('execution_id'):str,vol.Required('finished_at'):str,vol.Required('status'):vol.In(('completed','failed','unknown')),vol.Required('delivery_outcome'):vol.In(('queued','delivered','suppressed','failed','not_configured','unknown')),vol.Optional('preview'):str,vol.Optional('silent'):strict_bool})}}
    for action,extra in fields.items():
        schema={'type':DOMAIN+'/'+action,**extra}
        def create_handler(action,schema):
            @websocket_api.websocket_command(vol.All(vol.Schema(schema)))
            @websocket_api.require_admin
            @websocket_api.async_response
            async def handler(hass,connection,msg):
                try:
                    current=runtime(hass)
                    args={k:v for k,v in msg.items() if k not in ('id','type')}
                    if action in ('delete','toggle','test'): args['id']=args.pop('rule_id')
                    if action=='cron_result':
                        result=await current.engine.cron_result(**args)
                        connection.send_result(msg['id'],result)
                        return
                    if action in ('cron_sync','cron_policy'):
                        await getattr(current.engine,action)(**args)
                        result={}
                    elif action=='proactive_config':
                        await current.proactive.configure(**args)
                        result={}
                    elif action=='get': result={}
                    elif action=='test': result={'queued_request_id':await current.engine.enqueue(args['id'])}
                    else:
                        saved=await current.engine.command(action,**args)
                        result={'saved_id':saved} if action=='save' else {}
                    connection.send_result(msg['id'],dict(current.snapshot(),**result))
                except Error as exc: connection.send_error(msg['id'],str(exc),'HA²: '+str(exc))
                except Exception: connection.send_error(msg['id'],'unavailable','HA² unavailable')
            return handler
        websocket_api.async_register_command(hass,create_handler(action,schema))


SEND_SCHEMA=vol.Schema({vol.Optional('rule_id'):str,vol.Optional('title'):str,
                        vol.Optional('body'):str,vol.Optional('kind'):str,
                        vol.Optional('mode'):str,vol.Optional('request_id'):str})

async def send(hass,call):
    try:
        current=runtime(hass);args=dict(call.data)
        request_id=args.pop('request_id',None);rule_id=args.pop('rule_id',None)
        if rule_id is not None and args: raise Error('invalid_rule')
        result=await current.engine.enqueue(rule_id,request_id=request_id,manual=args if rule_id is None else None)
        return {'enqueued':True,'request_id':result}
    except Error as exc: raise HomeAssistantError('HA²: '+str(exc)) from None


async def async_setup(hass,config):
    state=hass.data.setdefault(DOMAIN,{'runtime':None})
    if not state.get('ws_registered'):
        register_ws(hass);state['ws_registered']=True
    return True

async def async_setup_entry(hass,entry):
    await async_setup(hass,{})
    state=hass.data[DOMAIN]
    if state['runtime'] is not None: return False
    try: validate_target(hass,entry.data)
    except Error: raise ConfigEntryNotReady('HA² target services/entities not ready') from None
    current=Runtime(hass,entry)
    await current.engine.load()
    await current.proactive.initialize()
    if not state.get('static_registered'):
        await hass.http.async_register_static_paths([StaticPathConfig('/ha2-notifications-static',str(Path(__file__).parent/'static'),False)])
        state['static_registered']=True
    await panel_custom.async_register_panel(hass,frontend_url_path='ha2-notifications',webcomponent_name='ha2-notifications-panel',
        sidebar_title='HA² - RUYMANIA',sidebar_icon='mdi:robot-excited',module_url=f'/ha2-notifications-static/panel.js?v={VERSION}',require_admin=True,embed_iframe=False,trust_external=False)
    state['runtime']=current
    async def handle_send(call): return await send(hass,call)
    async_register_admin_service(hass,DOMAIN,'send',handle_send,SEND_SCHEMA,supports_response=SupportsResponse.OPTIONAL)
    current.unsubscribe=hass.bus.async_listen('state_changed',current.on_state)
    current.worker=hass.async_create_background_task(current.run(),'HA² notifications worker')
    return True

async def async_unload_entry(hass,entry):
    state=hass.data[DOMAIN];current=state.get('runtime')
    if current:
        state['runtime']=None
        await current.close()
        hass.services.async_remove(DOMAIN,'send')
        frontend.async_remove_panel(hass,'ha2-notifications')
    return True

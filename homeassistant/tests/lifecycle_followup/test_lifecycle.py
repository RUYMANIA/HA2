"""Isolated HA imports: no async_start, network or live config registration."""
import asyncio
import json
import pathlib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import voluptuous as vol
from homeassistant.core import HomeAssistant, Event
from homeassistant.auth.models import User
from homeassistant import config_entries
from homeassistant.components import frontend
from homeassistant.exceptions import Unauthorized, ConfigEntryNotReady
import custom_components.ha2_notifications as integration
from custom_components.ha2_notifications.config_flow import NotificationsConfigFlow

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = {'target_prefix':'xiaozhi_ball_v2','weather_entity':'weather.forecast_casa'}
RULE = {'name':'Isolated','title':'Test','body':'Not sent','trigger':'manual','enabled':False,'busy':'drop'}

class Connection:
    def __init__(self, admin=True):
        self.user = User(name='Isolated identity',perm_lookup=None,is_active=True,is_owner=admin) if admin is not None else None
        self.results=[]; self.errors=[]
    def send_result(self, msg_id, result): self.results.append((msg_id,result))
    def send_error(self, msg_id, code, message): self.errors.append((msg_id,code,message))

class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = ROOT/'isolated-config'/self._testMethodName
        self.config.mkdir(parents=True, mode=0o700)
        self.hass = HomeAssistant(str(self.config))
        self.hass.config.time_zone = 'Atlantic/Canary'
        self.static = AsyncMock()
        self.hass.http = SimpleNamespace(async_register_static_paths=self.static)
        self.hass.config_entries = config_entries.ConfigEntries(self.hass,{})
        self.entry = SimpleNamespace(data=DATA)
        self.effects=[]
        async def forbidden(call):
            self.effects.append(call)
            raise AssertionError('No device/service effect allowed')
        for name in ('card_show','card_play','card_cancel'):
            self.hass.services.async_register('esphome','xiaozhi_ball_v2_'+name,forbidden)
        for domain,suffix in (('sensor','_card_status'),('sensor','_ui_status'),('sensor','_ui_night'),('binary_sensor','_card_active'),('media_player',''),('assist_satellite','_assist_satellite'),('select','_assistant')):
            self.hass.states.async_set(domain+'.xiaozhi_ball_v2'+suffix,'idle')
        self.hass.states.async_set('weather.forecast_casa','sunny')
        await integration.async_setup(self.hass,{})

    async def asyncTearDown(self):
        await integration.async_unload_entry(self.hass,self.entry)
        await self.hass.async_block_till_done()
        self.assertEqual(self.effects,[])

    async def ws(self, action, **args):
        handler,schema = self.hass.data['websocket_api']['ha2_notifications/'+action]
        msg=schema({'id':173,'type':'ha2_notifications/'+action,**args})
        connection=Connection()
        handler(self.hass,connection,msg)
        # async_response schedules background tasks; wait for this specific result.
        for _ in range(100):
            if connection.results or connection.errors: break
            await asyncio.sleep(.001)
        self.assertTrue(connection.results or connection.errors,'WS handler did not finish')
        return connection

    async def test_registered_ws_all_nonadmin_and_anonymous_rejected(self):
        expected={'get','save','delete','toggle','pause','test','cron_sync','cron_policy','cron_result','proactive_config'}
        handlers={key.split('/')[1]:value for key,value in self.hass.data['websocket_api'].items() if key.startswith('ha2_notifications/')}
        self.assertEqual(set(handlers),expected)
        arguments={'proactive_config':{'expected_revision':0,'config':{'enabled':False,'all_day':True,'start':'09:00','end':'21:00','interval_minutes':60,'mode':'cue'}},'get':{},'save':{'rule':RULE,'expected_revision':0},'delete':{'rule_id':'a'*32,'expected_revision':0},'toggle':{'rule_id':'a'*32,'enabled':True,'expected_revision':0},'pause':{'paused':True,'expected_revision':0},'test':{'rule_id':'a'*32},
                  'cron_sync':{'source_instance':'host','profile':'default','jobs':[{'job_id':'job-original','name':'Tarea','schedule':'cada día','enabled':True,'no_agent':False,'delivery':'telegram','excerpt_available':True}]},
                  'cron_policy':{'job_key':'a'*32,'expected_revision':0,'enabled':True,'content':'brief','mode':'cue','title':''},
                  'cron_result':{'source_instance':'host','profile':'default','job_id':'job-original','result':{'execution_id':'x','finished_at':'2026-10-24T10:00:00Z','status':'completed','delivery_outcome':'unknown'}}}
        for action,(handler,schema) in handlers.items():
            message=schema({'id':173,'type':'ha2_notifications/'+action,**arguments[action]})
            for identity in (False,None):
                with self.subTest(action=action,identity=identity):
                    connection=Connection(identity)
                    with self.assertRaises(Unauthorized): handler(self.hass,connection,message)
                    self.assertEqual(connection.results,[]); self.assertEqual(connection.errors,[])
        self.assertIsNone(self.hass.data[integration.DOMAIN]['runtime'])

    async def test_real_ws_schemas_rule_id_and_reserved_transport_id(self):
        await integration.async_setup_entry(self.hass,self.entry)
        saved=await self.ws('save',rule=RULE,expected_revision=0)
        rid=saved.results[0][1]['saved_id']
        for action,extra in (('toggle',{'enabled':True,'expected_revision':1}),('delete',{'expected_revision':2}),('test',{})):
            _,schema=self.hass.data['websocket_api']['ha2_notifications/'+action]
            self.assertEqual(schema({'id':173,'type':'ha2_notifications/'+action,'rule_id':rid,**extra})['rule_id'],rid)
            with self.assertRaises(vol.Invalid): schema({'id':rid,'type':'ha2_notifications/'+action,**extra})
        toggled=await self.ws('toggle',rule_id=rid,enabled=True,expected_revision=1)
        self.assertEqual(toggled.results[0][0],173)
        self.assertTrue(toggled.results[0][1]['rules'][0]['enabled'])
        # Pause worker while testing explicit enqueue; never send anything.
        current=integration.runtime(self.hass)
        current.worker.cancel(); await asyncio.gather(current.worker,return_exceptions=True)
        queued=await self.ws('test',rule_id=rid)
        self.assertEqual(len(queued.results[0][1]['queued_request_id']),32)
        self.assertEqual(current.engine.data['queue'][0]['rule_id'],rid)
        deleted=await self.ws('delete',rule_id=rid,expected_revision=2)
        self.assertEqual(deleted.results[0][1]['rules'],[])
        self.assertEqual(deleted.results[0][1]['queue_count'],0)

    async def test_setup_unload_reload_real_panel_store_and_listener_cancellation(self):
        listeners_before=self.hass.bus.async_listeners().get('state_changed',0)
        handlers=dict(self.hass.data['websocket_api'])
        old=[]
        for cycle in range(2):
            self.assertTrue(await integration.async_setup_entry(self.hass,self.entry))
            current=integration.runtime(self.hass)
            self.assertFalse(current.stopped)
            self.assertFalse(current.worker.done())
            panel=self.hass.data[frontend.DATA_PANELS]['ha2-notifications']
            self.assertTrue(panel.require_admin)
            self.assertFalse(panel.config['_panel_custom']['embed_iframe'])
            self.assertFalse(panel.config['_panel_custom']['trust_external'])
            self.assertEqual(self.hass.bus.async_listeners()['state_changed'],listeners_before+1)
            self.assertTrue(self.hass.services.has_service(integration.DOMAIN,'send'))
            if cycle==0:
                rid=await current.engine.command('save',rule=RULE,expected_revision=0)
            else:
                self.assertEqual(current.engine.data['rules'][0]['id'],rid)
                self.assertEqual(current.engine.data['revision'],1)
            # Force an in-flight state transition through the real listener callback.
            current.engine.data['rules']=[dict(current.engine.data['rules'][0],enabled=True,trigger='state',entity_id='sensor.isolated')]
            pending=AsyncMock(side_effect=lambda *args: None)
            started=asyncio.Event()
            async def blocked(*args):
                started.set(); await asyncio.Event().wait()
            with patch.object(current.engine,'state_changed',side_effect=blocked):
                current.on_state(Event('state_changed',{'entity_id':'sensor.isolated','old_state':SimpleNamespace(state='off'),'new_state':SimpleNamespace(state='on')}))
                await asyncio.wait_for(started.wait(),1)
                tasks=list(current.tasks); self.assertEqual(len(tasks),1)
                self.assertTrue(await integration.async_unload_entry(self.hass,self.entry))
                self.assertTrue(all(t.cancelled() for t in tasks))
            self.assertTrue(current.worker.done()); self.assertTrue(current.stopped)
            self.assertIsNone(current.unsubscribe); self.assertFalse(current.tasks)
            self.assertIsNone(self.hass.data[integration.DOMAIN]['runtime'])
            self.assertNotIn('ha2-notifications',self.hass.data[frontend.DATA_PANELS])
            self.assertFalse(self.hass.services.has_service(integration.DOMAIN,'send'))
            self.assertEqual(self.hass.bus.async_listeners().get('state_changed',0),listeners_before)
            self.assertEqual((await self.ws('get')).errors[0][1],'unavailable')
            await integration.async_setup(self.hass,{})
            self.assertEqual(self.hass.data['websocket_api'],handlers)
            old.append(current)
        self.assertIsNot(old[0],old[1])
        self.assertEqual(self.static.await_count,1)
        store=self.config/'.storage/ha2_notifications'
        self.assertEqual(store.stat().st_mode & 0o777,0o600)

    async def test_missing_target_setup_is_clean(self):
        self.hass.states.async_remove('weather.forecast_casa')
        with self.assertRaises(ConfigEntryNotReady): await integration.async_setup_entry(self.hass,self.entry)
        self.assertIsNone(self.hass.data[integration.DOMAIN]['runtime'])
        self.assertFalse(self.hass.services.has_service(integration.DOMAIN,'send'))
        self.assertNotIn('ha2-notifications',self.hass.data.get(frontend.DATA_PANELS,{}))
        self.assertEqual(self.static.await_count,0)

    async def test_real_config_flow_forms_validation_creation_and_single_instance(self):
        self.assertIs(config_entries.HANDLERS[integration.DOMAIN],NotificationsConfigFlow)
        manifest=json.loads((pathlib.Path(integration.__file__).parent/'manifest.json').read_text())
        self.assertTrue(manifest['config_flow']); self.assertTrue(manifest['single_config_entry'])
        self.assertEqual(manifest['requirements'],[])
        flow=NotificationsConfigFlow(); flow.hass=self.hass
        flow.handler=integration.DOMAIN; flow.flow_id='isolated'; flow.context={'source':'user'}
        self.assertEqual((await flow.async_step_user())['type'],'form')
        for invalid in ({'target_prefix':'../unsafe','weather_entity':'weather.forecast_casa'}, {'target_prefix':'xiaozhi_ball_v2','weather_entity':'sensor.invalid'}):
            self.assertEqual((await flow.async_step_user(invalid))['errors'],{'base':'config_error'})
        self.hass.states.async_remove('weather.forecast_casa')
        self.assertEqual((await flow.async_step_user(DATA))['errors'],{'base':'config_error'})
        self.hass.states.async_set('weather.forecast_casa','sunny')
        self.hass.services.async_remove('esphome','xiaozhi_ball_v2_card_play')
        self.assertEqual((await flow.async_step_user(DATA))['errors'],{'base':'config_error'})
        self.hass.services.async_register('esphome','xiaozhi_ball_v2_card_play',lambda call: None)
        result=await flow.async_step_user(DATA)
        self.assertEqual(result['type'],'create_entry'); self.assertEqual(result['data'],DATA)
        # Insert only into THIS unstarted, isolated manager; never setup a flow entry.
        entry=config_entries.ConfigEntry(domain=integration.DOMAIN,data=DATA,title='Isolated',source='user',version=1,minor_version=1,options={},unique_id=None,discovery_keys={},subentries_data=[])
        self.hass.config_entries._entries[entry.entry_id]=entry
        self.assertEqual((await flow.async_step_user())['reason'],'single_instance_allowed')
        self.assertEqual((await flow.async_step_user(DATA))['reason'],'single_instance_allowed')
        self.assertIsNone(self.hass.data[integration.DOMAIN]['runtime'])

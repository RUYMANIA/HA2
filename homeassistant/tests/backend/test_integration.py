import asyncio, importlib, json, pathlib, unittest
from types import SimpleNamespace
from unittest.mock import patch
import voluptuous as vol
from homeassistant.core import HomeAssistant, Context
from homeassistant.exceptions import Unauthorized,HomeAssistantError
from test_engine import MemoryStore,rule
import test_ha
import custom_components.ha2_notifications as integration

class Connection:
    def __init__(self,admin=True): self.user=SimpleNamespace(is_admin=admin);self.results=[];self.errors=[]
    def send_result(self,i,value):self.results.append(value)
    def send_error(self,i,code,message):self.errors.append(code)

class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=test_ha.TransportTests.asyncSetUp
    put=test_ha.TransportTests.put
    sync=test_ha.TransportTests.sync
    sleep=test_ha.TransportTests.sleep
    claim=test_ha.TransportTests.claim
    async def test_real_store_private_atomic_roundtrip(self):
        from homeassistant.helpers.storage import Store
        from custom_components.ha2_notifications.engine import Engine
        from datetime import datetime,timezone
        import stat
        config=pathlib.Path(self.hass.config.config_dir)
        config.mkdir(parents=True,exist_ok=True,mode=0o700)
        store=Store(self.hass,1,'ha2_notifications_test',private=True,atomic_writes=True)
        engine=Engine(store,'Atlantic/Canary',lambda:datetime.now(timezone.utc),lambda:set())
        await engine.load()
        saved=await engine.command('save',rule=rule(),expected_revision=0)
        from test_cron import JOB
        await engine.cron_sync(source_instance='host',profile='default',jobs=[JOB])
        state=engine.cron_snapshot()
        await engine.cron_policy(job_key=state['jobs'][0]['job_key'],expected_revision=state['revision'],enabled=True,content='brief',mode='cue',title='')
        ack=await engine.cron_result(source_instance='host',profile='default',job_id=JOB['job_id'],result=dict(execution_id='stored-run',finished_at=datetime.now(timezone.utc).isoformat(),status='completed',delivery_outcome='unknown'))
        self.assertTrue(ack['accepted'])
        file=config/'.storage/ha2_notifications_test'
        self.assertEqual(stat.S_IMODE(file.stat().st_mode),0o600)
        payload=json.loads(file.read_text())
        self.assertEqual(payload['data']['rules'][0]['id'],saved)
        fresh=Store(self.hass,1,'ha2_notifications_test',private=True,atomic_writes=True)
        restored=Engine(fresh,'Atlantic/Canary',lambda:datetime.now(timezone.utc),lambda:set())
        await restored.load();self.assertEqual(restored.data,engine.data)

    async def test_configflow_discovery_and_existing_target_validation(self):
        spec=importlib.util.find_spec('custom_components.ha2_notifications.config_flow')
        self.assertIsNotNone(spec,'Config flow required')
        from custom_components.ha2_notifications.config_flow import NotificationsConfigFlow
        from homeassistant import config_entries
        self.assertIs(config_entries.HANDLERS.get('ha2_notifications'),NotificationsConfigFlow)
        path=pathlib.Path(integration.__file__).parent
        manifest=json.loads((path/'manifest.json').read_text())
        self.assertEqual(manifest['version'],'0.3.0');self.assertEqual(manifest['requirements'],[])
        self.assertIn('panel_custom',manifest['dependencies'])
        self.assertTrue(manifest['config_flow'])
        flow=NotificationsConfigFlow();flow.hass=self.hass;flow.handler='ha2_notifications';flow.flow_id='test'
        with patch.object(NotificationsConfigFlow,'_async_current_entries',return_value=[]):
            form=await flow.async_step_user()
            self.assertEqual(form['type'],'form')
            result=await flow.async_step_user({'target_prefix':'xiaozhi_ball_v2','weather_entity':'weather.forecast_casa'})
            self.assertEqual(result['errors'],{'base':'config_error'})
            self.put('weather.forecast_casa','sunny');self.put('select.xiaozhi_ball_v2_assistant','Hermes prueba')
            result=await flow.async_step_user({'target_prefix':'xiaozhi_ball_v2','weather_entity':'weather.forecast_casa'})
            self.assertEqual(result['type'],'create_entry')
            self.assertEqual(result['data']['target_prefix'],'xiaozhi_ball_v2')
        with patch.object(NotificationsConfigFlow,'_async_current_entries',return_value=[object()]):
            result=await flow.async_step_user()
            self.assertEqual(result['reason'],'single_instance_allowed')

    async def test_entry_ws_permissions_native_store_panel_and_clean_reload(self):
        self.assertTrue(hasattr(integration,'async_setup_entry'),'Loadable HA integration required')
        self.put('weather.forecast_casa','sunny')
        self.put('select.xiaozhi_ball_v2_assistant','Hermes prueba')
        self.hass.config.time_zone='Atlantic/Canary'
        self.hass.http=SimpleNamespace(async_register_static_paths=self.static)
        self.static_calls=[];self.panel_calls=[];store=MemoryStore()
        entry=SimpleNamespace(data={'target_prefix':'xiaozhi_ball_v2','weather_entity':'weather.forecast_casa'})
        async def panel(*args,**kw):self.panel_calls.append(kw)
        with patch.object(integration,'Store',return_value=store) as store_ctor, patch.object(integration.panel_custom,'async_register_panel',side_effect=panel),patch.object(integration.frontend,'async_remove_panel') as removed:
            self.assertTrue(await integration.async_setup(self.hass,{}))
            handlers=dict(self.hass.data['websocket_api'])
            for command,(handler,schema) in handlers.items():
                if not command.startswith('ha2_notifications/'): continue
                with self.assertRaises(vol.Invalid): schema({'id':1,'type':command,'unexpected':True})
                if command.endswith(('/save','/delete','/toggle','/pause')):
                    args={'save':{'rule':rule()},'delete':{'rule_id':'a'*32},'toggle':{'rule_id':'a'*32,'enabled':True},'pause':{'paused':False}}[command.rsplit('/',1)[1]]
                    msg={'id':1,'type':command,'expected_revision':True,**args}
                    with self.assertRaises(vol.Invalid): schema(msg)
            self.assertTrue(await integration.async_setup_entry(self.hass,entry))
            self.assertTrue(self.panel_calls[0]['require_admin'])
            self.assertIs(self.panel_calls[0].get('embed_iframe'),False)
            self.assertIs(self.panel_calls[0].get('trust_external'),False)
            self.assertEqual(self.panel_calls[0]['module_url'],'/ha2-notifications-static/panel.js?v=0.3.0')
            self.assertEqual(self.panel_calls[0]['sidebar_title'],'HA² - RUYMANIA')
            self.assertEqual(self.panel_calls[0]['sidebar_icon'],'mdi:robot-excited')
            self.assertTrue(store_ctor.call_args.kwargs['private']);self.assertTrue(store_ctor.call_args.kwargs['atomic_writes'])
            async def ws(action,**args):
                handler,schema=self.hass.data['websocket_api']['ha2_notifications/'+action]
                msg={'id':1,'type':'ha2_notifications/'+action,**args}
                self.assertTrue(schema)
                schema(msg)
                rejected=Connection(False)
                with self.assertRaises(Unauthorized): handler(self.hass,rejected,msg)
                connection=Connection();handler(self.hass,connection,msg)
                await self.hass.async_block_till_done()
                return connection
            connection=await ws('get')
            snapshot=connection.results[-1]
            self.assertEqual(snapshot['rules'],[]);self.assertFalse(snapshot['paused'])
            self.assertEqual(snapshot['revision'],0)
            self.assertEqual(snapshot['hermes_cron'],dict(revision=0,sources=[],jobs=[]))
            from test_cron import JOB
            synced=await ws('cron_sync',source_instance='host',profile='default',jobs=[JOB])
            cs=synced.results[-1]['hermes_cron'];job_key=cs['jobs'][0]['job_key']
            changed=await ws('cron_policy',job_key=job_key,expected_revision=cs['revision'],enabled=True,content='brief',mode='cue',title='')
            self.assertEqual(changed.results[-1]['revision'],0)
            result=await ws('cron_result',source_instance='host',profile='default',job_id=JOB['job_id'],result=dict(execution_id='ws-run',finished_at=integration.datetime.now(integration.timezone.utc).isoformat(),status='completed',delivery_outcome='unknown'))
            self.assertEqual(set(result.results[-1]),{'accepted','outcome','request_id'})
            self.assertEqual(result.results[-1]['outcome'],'queued')
            await ws('cron_policy',job_key=job_key,expected_revision=changed.results[-1]['hermes_cron']['revision'],enabled=False,content='brief',mode='cue',title='')
            for action,payload in [('cron_sync',dict(source_instance='host',profile='default',jobs=[dict(JOB,extra=True)])),('cron_result',dict(source_instance='host',profile='default',job_id=JOB['job_id'],result=dict(execution_id='x',finished_at='2026-10-24T10:00:00Z',status='completed',delivery_outcome='unknown',extra=True))),('cron_policy',dict(job_key=job_key,expected_revision=True,enabled=True,content='brief',mode='cue',title=''))]:
                handler,schema=self.hass.data['websocket_api']['ha2_notifications/'+action]
                with self.assertRaises(vol.Invalid):schema(dict(id=1,type='ha2_notifications/'+action,**payload))
            self.assertEqual(snapshot['timezone'],'Atlantic/Canary')
            connection=await ws('save',rule=rule(),expected_revision=0)
            rid=connection.results[-1]['saved_id']
            await ws('toggle',rule_id=rid,enabled=True,expected_revision=1)
            conflict=await ws('pause',paused=True,expected_revision=0)
            self.assertEqual(conflict.errors,['conflict'])
            await ws('pause',paused=True,expected_revision=2)
            blocked=await ws('test',rule_id=rid)
            self.assertEqual(blocked.errors,['paused'])
            await ws('pause',paused=False,expected_revision=3)
            queued=await ws('test',rule_id=rid)
            self.assertEqual(len(queued.results[-1]['queued_request_id']),32)
            await ws('delete',rule_id=rid,expected_revision=4)
            runtime=self.hass.data['ha2_notifications']['runtime']
            async def get_user(uid):return SimpleNamespace(is_admin=uid=='admin')
            self.hass.auth=SimpleNamespace(async_get_user=get_user)
            with self.assertRaises(Unauthorized):
                await self.hass.services.async_call('ha2_notifications','send',{'title':'Aviso','body':'Texto'},blocking=True,context=Context(user_id='guest'),return_response=True)
            response=await self.hass.services.async_call('ha2_notifications','send',{'title':'Aviso','body':'Texto','request_id':'b'*32},blocking=True,context=Context(user_id='admin'),return_response=True)
            self.assertEqual(response,{'enqueued':True,'request_id':'b'*32})
            response2=await self.hass.services.async_call('ha2_notifications','send',{'title':'Aviso','body':'Texto','request_id':'b'*32},blocking=True,return_response=True)
            self.assertEqual(response2,response)
            with self.assertRaises(HomeAssistantError):
                await self.hass.services.async_call('ha2_notifications','send',{'title':'Solo título'},blocking=True)
            self.put('sensor.test','off')
            state_id=await runtime.engine.command('save',rule=dict(rule(enabled=True),trigger='state',entity_id='sensor.test',to_state='on'),expected_revision=5)
            self.put('sensor.test','on')
            await asyncio.sleep(0)
            if runtime.tasks: await asyncio.gather(*runtime.tasks)
            self.assertEqual(sum(q['rule_id']==state_id for q in runtime.engine.data['queue']),1)
            self.assertTrue(await integration.async_unload_entry(self.hass,entry))
            self.assertTrue(runtime.worker.done());self.assertFalse(runtime.tasks)
            removed.assert_called_once()
            unloaded=await ws('get');self.assertEqual(unloaded.errors,['unavailable'])
            await integration.async_setup(self.hass,{})
            self.assertEqual(self.hass.data['websocket_api'],handlers)
            await integration.async_setup_entry(self.hass,entry)
            self.assertEqual(len(self.static_calls),1)
            self.assertEqual(self.hass.data['ha2_notifications']['runtime'].engine.data['revision'],6)
            await integration.async_unload_entry(self.hass,entry)
    async def static(self,paths):self.static_calls.append(paths)

import asyncio
import pathlib
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.auth.models import User
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers.storage import Store
import custom_components.ha2_notifications as ha
from custom_components.ha2_notifications import proactive as p

class Connection:
    def __init__(self,admin=True):self.user=User(name='fixture',perm_lookup=None,is_active=True,is_owner=admin);self.results=[];self.errors=[]
    def send_result(self,id,value):self.results.append((id,value))
    def send_error(self,id,code,message):self.errors.append((id,code,message))

class WSTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        root=pathlib.Path(__file__).resolve().parents[2]/'isolated-config'/self._testMethodName
        root.mkdir(parents=True,exist_ok=True)
        self.hass=HomeAssistant(str(root));self.hass.config.time_zone='Atlantic/Canary'
        self.r=ha.Runtime(self.hass,SimpleNamespace(data={'target_prefix':'xiaozhi_ball_v2','weather_entity':'weather.forecast_casa'}))
        await self.r.engine.load()
        self.assertTrue(hasattr(self.r,'proactive'),'Runtime coordinator missing')
        await self.r.proactive.initialize()
        await ha.async_setup(self.hass,{})
        self.hass.data[ha.DOMAIN]['runtime']=self.r
    async def asyncTearDown(self):
        if hasattr(self,'r'):await self.r.close()
        await self.hass.async_block_till_done()
    async def ws(self,config,rev=0):
        handler,schema=self.hass.data['websocket_api']['ha2_notifications/proactive_config']
        conn=Connection();handler(self.hass,conn,schema({'id':173,'type':'ha2_notifications/proactive_config','config':config,'expected_revision':rev}))
        for _ in range(100):
            if conn.results or conn.errors:return conn
            await asyncio.sleep(.001)
        self.fail('WS did not finish')
    async def test_schema_admin_reserved_id_and_exact_fields(self):
        handler,schema=self.hass.data['websocket_api']['ha2_notifications/proactive_config']
        msg={'id':173,'type':'ha2_notifications/proactive_config','config':p.DEFAULT_CONFIG,'expected_revision':0}
        with self.assertRaises(Unauthorized):handler(self.hass,Connection(False),schema(msg))
        for extra in ({'other':'x'},{'request_id':'a'*32}):
            with self.assertRaises(vol.Invalid):schema(dict(msg,**extra))
        with self.assertRaises(vol.Invalid):schema(dict(msg,id='a'*32))
        self.assertEqual(len([k for k in self.hass.data['websocket_api'] if k.startswith('ha2_notifications/')]),10)
    async def test_full_snapshot_strict_error_and_store_roundtrip_no_rule_drift(self):
        for index in range(4):
            await self.r.engine.command('save',expected_revision=index,rule={'name':f'Fixture {index}','title':'Prueba','body':'No enviar','trigger':'manual','enabled':False})
        self.r.engine.data['revision']=49
        jobs=[dict(job_id=f'fixture-job-{index}',name=f'Tarea {index}',schedule='cada día',enabled=True,no_agent=False,delivery='telegram',excerpt_available=True) for index in range(12)]
        await self.r.engine.cron_sync(source_instance='fixture-host',profile='default',jobs=jobs)
        before=self.r.engine.cron_snapshot()
        self.assertEqual(len(before['jobs']),12)
        self.assertFalse(any(job['policy']['enabled'] for job in before['jobs']))
        reply=await self.ws(dict(p.DEFAULT_CONFIG,enabled=True))
        value=reply.results[0][1];self.assertEqual(reply.results[0][0],173)
        self.assertEqual(value['revision'],49);self.assertEqual(len(value['rules']),4);self.assertEqual(value['hermes_cron'],before)
        self.assertEqual(value['proactive']['revision'],1);self.assertEqual(value['version'],'0.3.0')
        self.assertFalse(any(value['proactive']['capabilities'].values()))
        self.assertEqual((await self.ws({},1)).errors[0][1],'invalid_config')
        self.assertEqual((await self.ws(p.DEFAULT_CONFIG,0)).errors[0][1],'conflict')
        await self.r.proactive.close()
        loaded=await self.r.engine.store.async_load();self.assertEqual(loaded['proactive']['revision'],1)
        self.assertNotIn('<script>',str(loaded))
    async def test_worker_notifications_continue_while_model_is_blocked(self):
        from test_coordinator import Transport
        from unittest.mock import AsyncMock
        from datetime import timedelta
        t=Transport()
        await self.r.proactive.close()
        self.r.proactive=p.Coordinator(self.r.engine,t,self.hass.async_create_background_task)
        await self.r.proactive.initialize()
        await self.r.proactive.configure(0,dict(p.DEFAULT_CONFIG,enabled=True))
        self.r.engine.data['proactive']['next_due_at']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
        await self.r.proactive.tick();await asyncio.wait_for(t.started.wait(),1)
        ordinary=asyncio.Event()
        self.r.engine.schedule=AsyncMock()
        async def step(sender):ordinary.set()
        self.r.engine.step=step
        self.r.worker=self.hass.async_create_background_task(self.r.run(),'fixture notification worker')
        await asyncio.wait_for(ordinary.wait(),1)
        self.assertFalse(self.r.proactive.task.done())
        await self.r.close()
        self.assertTrue(self.r.worker.done());self.assertIsNone(self.r.proactive.task)

    async def test_public_unavailable_no_trace(self):
        self.r.stopped=True
        reply=await self.ws(p.DEFAULT_CONFIG)
        self.assertEqual(reply.errors,[(173,'unavailable','HA²: unavailable')])

"""Expanded WS security gate: nine commands, strict guest boundaries."""
import pathlib, unittest
from types import SimpleNamespace
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import Unauthorized
import custom_components.ha2_notifications as integration
from test_cron import JOB
from test_engine import rule
from test_integration import Connection

class CronWSGate(unittest.IsolatedAsyncioTestCase):
    async def test_all_nine_commands_reject_guest_and_anonymous(self):
        hass=HomeAssistant(str(pathlib.Path(__file__).parent/'security-config'))
        await integration.async_setup(hass,{})
        args={'proactive_config':dict(expected_revision=0,config={'enabled':False,'all_day':True,'start':'09:00','end':'21:00','interval_minutes':60,'mode':'cue'}),'get':{},'save':dict(rule=rule(),expected_revision=0),'delete':dict(rule_id='a'*32,expected_revision=0),'toggle':dict(rule_id='a'*32,enabled=True,expected_revision=0),'pause':dict(paused=True,expected_revision=0),'test':dict(rule_id='a'*32),
              'cron_sync':dict(source_instance='host',profile='default',jobs=[JOB]),
              'cron_policy':dict(job_key='a'*32,expected_revision=0,enabled=True,content='brief',mode='cue',title=''),
              'cron_result':dict(source_instance='host',profile='default',job_id=JOB['job_id'],result=dict(execution_id='x',finished_at='2026-10-24T10:00:00Z',status='completed',delivery_outcome='unknown'))}
        handlers={k.split('/')[1]:v for k,v in hass.data['websocket_api'].items() if k.startswith(integration.DOMAIN+'/')}
        self.assertEqual(set(handlers),set(args))
        for action,(handler,schema) in handlers.items():
            message=schema(dict(id=173,type=integration.DOMAIN+'/'+action,**args[action]))
            for user in (SimpleNamespace(is_admin=False),None):
                with self.subTest(action=action,user=user):
                    connection=Connection();connection.user=user
                    with self.assertRaises(Unauthorized):handler(hass,connection,message)
                    self.assertEqual(connection.results,[]);self.assertEqual(connection.errors,[])
        self.assertIsNone(hass.data[integration.DOMAIN]['runtime'])

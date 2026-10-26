"""Installed HA imports, no HA start/network; only service/clock IO faked."""
import asyncio, importlib.util, pathlib, unittest, json
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from homeassistant.core import HomeAssistant, Context, State
ROOT=pathlib.Path(__file__).resolve().parents[2]
SPEC=importlib.util.find_spec('custom_components.ha2_notifications.transport')
if SPEC:
    from custom_components.ha2_notifications import transport
else: transport=None

class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.assertIsNotNone(transport,'Native HA transport required')
        self.hass=HomeAssistant(str(ROOT/'test-config'))
        self.now=datetime(2026,10,22,10,tzinfo=timezone.utc)
        self.mono=0.;self.calls=[];self.claimed=False;self.night=False;self.auto_ack=True
        self.status=dict(request_id='',generation=2,state='idle',visible=False,audio='none',reason='',truncated=False)
        self.put('media_player.xiaozhi_ball_v2','idle')
        self.put('assist_satellite.xiaozhi_ball_v2_assist_satellite','idle')
        self.put('binary_sensor.xiaozhi_ball_v2_card_active','off')
        self.put('sensor.xiaozhi_ball_v2_ui_status',json.dumps({'page':'closed'}))
        self.put('sensor.xiaozhi_ball_v2_ui_night',json.dumps({'night_active':False}))
        self.sync()
        async def call(domain,service,data,blocking=False,**kwargs):
            self.assertEqual(domain,'esphome');self.assertTrue(blocking)
            self.calls.append((service,dict(data)))
            self.assertTrue(self.claimed,'Effect must follow durable claim')
            if self.auto_ack:
                if service.endswith('card_show'):
                    self.status.update(request_id=data['request_id'],generation=3,state='shown',visible=True,audio='suppressed' if self.night else 'none',reason='night_mode' if self.night else '')
                    self.put('binary_sensor.xiaozhi_ball_v2_card_active','on')
                if service.endswith('card_play'):self.status.update(state='audio_done',audio='done')
                self.sync()
        async def handler(service_call):
            await call('esphome',service_call.service,service_call.data,blocking=True)
        for action in ('card_show','card_play','card_cancel'):
            self.hass.services.async_register('esphome','xiaozhi_ball_v2_'+action,handler)
        self.sender=transport.Sender(self.hass,'xiaozhi_ball_v2','weather.forecast_casa',lambda:self.now,lambda:self.mono,self.sleep)
        self.job={'request_id':'a'*32,'expires':self.now.timestamp()+1800,'rule':{'title':'Aviso','body':'Contenido','kind':'notice','mode':'cue'}}
    def put(self,e,s,attrs=None):self.hass.states.async_set(e,s,attrs)
    def sync(self):self.put('sensor.xiaozhi_ball_v2_card_status',json.dumps(self.status))
    async def sleep(self,secs):self.mono+=secs
    async def claim(self,generation):self.assertEqual(generation,2);self.claimed=True
    async def test_voice_resolves_selected_pipeline_and_real_stream_contract(self):
        self.assertTrue(hasattr(self.sender,'prepare'),'Native TTS stream preparation required')
        self.put('select.xiaozhi_ball_v2_assistant','Hermes prueba')
        pipeline=SimpleNamespace(name='Hermes prueba',tts_engine='tts.hermes',tts_language='es-ES',tts_voice=None)
        captured={}
        class Stream:
            url='/api/tts_proxy/private-token.wav'
            def async_set_message(self,body):captured['body']=body
        class Manager:
            def async_create_result_stream(self,engine,**kwargs):
                captured.update(engine=engine,**kwargs);return Stream()
        from homeassistant.components import tts
        self.hass.data[tts.DATA_TTS_MANAGER]=Manager()
        with patch.object(transport.pipeline,'async_get_pipelines',return_value=[pipeline]), patch.object(transport,'get_url',return_value='http://192.0.2.10:8123'):
            url=await self.sender.prepare('Texto')
            self.assertTrue(url.endswith('.wav'))
            self.assertEqual(captured['engine'],'tts.hermes')
            self.assertFalse(captured['use_file_cache'])
            self.assertNotIn('voice',captured['options'])
            self.assertEqual(captured['options']['preferred_sample_rate'],48000)
            self.assertEqual(captured['body'],'Texto')
            self.job['rule']['mode']='voice'
            self.assertEqual(await self.sender.deliver(self.job,self.claim,lambda:True),('audio_done',''))
        self.assertEqual([c[0] for c in self.calls],['xiaozhi_ball_v2_card_show','xiaozhi_ball_v2_card_play'])
        self.put('select.xiaozhi_ball_v2_assistant','missing')
        with patch.object(transport.pipeline,'async_get_pipelines',return_value=[pipeline]):
            with self.assertRaisesRegex(transport.Error,'config_error'): await self.sender.prepare('Texto')

    async def test_night_never_prepares_or_replays_voice(self):
        self.job['rule']['mode']='voice';self.night=True
        self.put('sensor.xiaozhi_ball_v2_ui_night',json.dumps({'night_active':True}))
        async def forbidden(body):self.fail('Night must not allocate or synthesize TTS')
        self.sender.prepare=forbidden
        self.assertEqual(await self.sender.deliver(self.job,self.claim,lambda:True),('night_silent','night_mode'))
        self.assertEqual(len(self.calls),1)

    async def test_weather_uses_real_units_and_update_time(self):
        self.assertTrue(hasattr(self.sender,'weather_text'),'Weather production formatter required')
        self.put('weather.forecast_casa','sunny',{'temperature':23,'temperature_unit':'°C','wind_speed':9,'wind_speed_unit':'km/h'})
        body=self.sender.weather_text()
        self.assertIn('Soleado',body);self.assertIn('23 °C',body);self.assertIn('9 km/h',body);self.assertIn('Datos HA',body)

    async def test_busy_change_during_prepare_remains_retryable_without_claim(self):
        self.job['rule']['mode']='voice'
        async def prepare(body):
            self.put('media_player.xiaozhi_ball_v2','playing')
            return 'http://192.0.2.10:8123/api/tts_proxy/private.wav'
        self.sender.prepare=prepare
        self.assertEqual(await self.sender.deliver(self.job,self.claim,lambda:True),('waiting','busy'))
        self.assertFalse(self.claimed);self.assertEqual(self.calls,[])

    async def test_night_change_during_prepare_never_plays(self):
        self.job['rule']['mode']='voice'
        async def prepare(body):
            self.put('sensor.xiaozhi_ball_v2_ui_night',json.dumps({'night_active':True}))
            return 'http://192.0.2.10:8123/api/tts_proxy/private.wav'
        self.sender.prepare=prepare
        self.assertEqual(await self.sender.deliver(self.job,self.claim,lambda:True),('night_silent','night_mode'))
        self.assertEqual(len(self.calls),1)
        self.assertFalse(self.calls[0][1]['audio_expected'])

    async def test_foreign_generation_after_show_never_plays_or_cancels(self):
        self.job['rule']['mode']='voice'
        async def prepare(body):return 'http://192.0.2.10:8123/api/tts_proxy/private.wav'
        self.sender.prepare=prepare
        self.auto_ack=False
        original=self.sender.call
        # Pre-show baseline remains generation2, then another producer wins ACK.
        self.status.update(request_id='',generation=2,state='idle',visible=False);self.sync()
        async def foreign(action,data):
            await original(action,data)
            self.status.update(request_id='c'*32,generation=4,state='shown',visible=True);self.sync()
        self.sender.call=foreign
        result=await self.sender.deliver(self.job,self.claim,lambda:True)
        self.assertEqual(result,('uncertain','producer_conflict'))
        self.assertEqual([c[0] for c in self.calls],['xiaozhi_ball_v2_card_show'])

    async def test_stale_matching_ack_not_delivery(self):
        self.auto_ack=False
        original=self.sender.call
        async def stale(action,data):
            await original(action,data)
            self.status.update(request_id=data['request_id'],state='shown',visible=True);self.sync()
        self.sender.call=stale
        self.assertEqual(await self.sender.deliver(self.job,self.claim,lambda:True),('uncertain','stale_ack'))

    async def test_firmware_truncation_is_reported_not_silently_successful(self):
        self.status['truncated']=True;self.sync()
        self.assertEqual(await self.sender.deliver(self.job,self.claim,lambda:True),('delivered','truncated'))

    async def test_cue_requires_fresh_matching_visible_ack_and_ttl(self):
        self.assertEqual(await self.sender.readiness(),'ready')
        self.assertEqual(await self.sender.deliver(self.job,self.claim,lambda:True),('delivered',''))
        self.assertEqual(self.calls[0][1]['ttl_ms'],30000)
        self.assertFalse(self.calls[0][1]['audio_expected'])
        self.assertEqual(len(self.calls),1)
    async def test_offline_and_busy_fail_closed(self):
        self.put('sensor.xiaozhi_ball_v2_ui_status','unknown')
        self.assertEqual(await self.sender.readiness(),'unavailable')
        self.put('sensor.xiaozhi_ball_v2_ui_status',json.dumps({'page':'menu'}))
        self.assertEqual(await self.sender.readiness(),'busy')
    async def test_lost_ack_is_uncertain_never_retried_or_cancel_other(self):
        self.auto_ack=False
        result=await self.sender.deliver(self.job,self.claim,lambda:True)
        self.assertEqual(result[0],'uncertain')
        self.assertEqual(len(self.calls),1)
    async def test_cancelled_guard_prevents_any_effect(self):
        self.assertEqual((await self.sender.deliver(self.job,self.claim,lambda:False))[0],'cancelled')
        self.assertEqual(self.calls,[])

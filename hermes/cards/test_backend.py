"""Host-only backend contract tests. No network/hardware calls."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location('backend', ROOT / 'backend.py')
if spec and spec.loader and (ROOT / 'backend.py').exists():
    import sys
    b = importlib.util.module_from_spec(spec)
    sys.modules['backend'] = b
    spec.loader.exec_module(b)
else:
    b = None


class ValidationTests(unittest.TestCase):
    def test_body_utf8_bytes_match_display_limit_without_silent_truncation(self):
        self.assertEqual(len(b.CardRequest('notice','Texto','ñ'*2048).text.encode('utf-8')),4096)
        self.assertEqual(len(b.CardRequest('notice','Texto','x'*4000).text),4000)
        with self.assertRaises(b.CardError):
            b.CardRequest('notice','Texto','ñ'*2049)

    def test_utf8_request_and_strict_bounds(self):
        self.assertIsNotNone(b, 'backend implementation is missing')
        request = b.CardRequest('notice', '¡Hola 🌦️!', 'Mañana café', 30)
        self.assertEqual(request.ttl_ms, 30000)
        self.assertRegex(request.request_id, r'^[a-f0-9]{32}$')
        for seconds in (1, 121, True, 2.5):
            with self.subTest(seconds=seconds), self.assertRaises(b.CardError):
                b.CardRequest('notice', 'Title', 'Body', seconds)
        for title in ('', ' ', 'bad\x00title', 'x' * 121, '\ud800'):
            with self.subTest(title=repr(title)), self.assertRaises(b.CardError):
                b.CardRequest('notice', title, 'Body', 30)
        with self.assertRaises(b.CardError):
            b.CardRequest('unknown', 'T', 'B', 30)
        with self.assertRaises(b.CardError):
            b.CardRequest('result', 'T', '', 30)


class PipelineTests(unittest.TestCase):
    def test_selected_pipeline_voice_and_common_audio_options(self):
        listing = {'preferred_pipeline': 'p1', 'pipelines': [
            {'id': 'p1', 'name': 'Other', 'tts_engine': 'tts.other', 'language': 'en', 'tts_voice': 'Other'},
            {'id': 'p2', 'name': 'Nabu', 'tts_engine': 'tts.cloud', 'language': 'es',
             'tts_language': 'es-ES', 'tts_voice': 'Current voice'}]}
        pipeline = b.resolve_pipeline('Nabu', listing)
        body = b.tts_payload(pipeline, 'Café')
        self.assertEqual(body['engine_id'], 'tts.cloud')
        self.assertEqual(body['language'], 'es-ES')
        self.assertIs(body['cache'], True)
        self.assertEqual(body['options'], {'voice': 'Current voice', 'preferred_format': 'wav',
            'preferred_sample_rate': 48000, 'preferred_sample_channels': 1, 'preferred_sample_bytes': 2})
        for choice in ('preferred', 'unavailable', 'unknown', None):
            self.assertEqual(b.resolve_pipeline(choice, listing)['id'], 'p1')
        with self.assertRaises(b.CardError):
            b.resolve_pipeline('Missing', listing)
        listing['pipelines'].append(dict(listing['pipelines'][1], id='p3'))
        with self.assertRaises(b.CardError):
            b.resolve_pipeline('Nabu', listing)


class DataTests(unittest.TestCase):
    def test_audio_path_matches_firmware_rejecting_query_or_oversize(self):
        origin = {'internal_url':'http://192.0.2.10:8123'}
        for path in ('/api/tts_proxy/a?nonce=Q', '/api/tts_proxy/a?', '/api/tts_proxy/'+'a'*400):
            with self.subTest(path=path), self.assertRaises(b.CardError):
                b.audio_url({'path':path}, origin)

    def test_rejected_empty_identity_is_readable_to_allow_recovery(self):
        status = {'request_id':'','state':'rejected','visible':False,'audio':'none',
                  'reason':'invalid_request','generation':0,'truncated':False}
        self.assertEqual(b.parse_status(status)['state'], 'rejected')

    def test_only_validated_lan_origin_and_unchanged_token_path(self):
        data = {'url': 'http://127.0.0.1:8123/api/tts_proxy/a_nonce-Q.wav',
                'path': '/api/tts_proxy/a_nonce-Q.wav'}
        self.assertEqual(b.audio_url(data, {'internal_url': 'http://192.0.2.10:8123'}),
                         'http://192.0.2.10:8123/api/tts_proxy/a_nonce-Q.wav')
        for host in ('127.0.0.1', 'localhost', '8.8.8.8', 'example.com', '198.51.100.20'):
            with self.subTest(host=host), self.assertRaises(b.CardError):
                b.audio_url(data, {'internal_url': 'http://' + host + ':8123'})
        for path in ('//evil/a', '/api/tts_proxy/../config', '/bad', '/api/tts_proxy/a#secret'):
            with self.subTest(path=path), self.assertRaises(b.CardError):
                b.audio_url(dict(data, path=path), {'internal_url': 'http://192.0.2.10:8123'})

    def test_weather_only_present_data_units_timestamp(self):
        state = {'state': 'cloudy', 'last_updated': '2026-10-18T17:00:00+00:00',
                 'attributes': {'temperature': 21.3, 'temperature_unit': '°C', 'humidity': 70,
                                'wind_speed': 5, 'wind_speed_unit': 'km/h'}}
        text = b.weather_text(state)
        self.assertIn('21,3 °C', text)
        self.assertIn('70 %', text)
        self.assertIn('5 km/h', text)
        self.assertIn('Datos HA 18/10 17:00', text)
        self.assertNotIn('precip', text)
        state['attributes'].pop('temperature_unit')
        self.assertNotIn('21,3', b.weather_text(state))
        for bad in ({}, dict(state, state='unavailable'), dict(state, last_updated='bad')):
            with self.assertRaises(b.CardError):
                b.weather_text(bad)


class CompactWeatherTests(unittest.TestCase):
    def test_weather_compact_spanish_real_units_and_local_timestamp(self):
        sample = {'state': 'rainy', 'last_updated': '2026-10-18T17:00:00+00:00',
                  'attributes': {'temperature': 22.3, 'temperature_unit': '°C',
                                 'humidity': 88, 'wind_speed': 24.8, 'wind_speed_unit': 'km/h'}}
        text = b.weather_text(sample)
        self.assertLessEqual(len(text.splitlines()), 5)
        self.assertIn('Lluvia', text)
        self.assertIn('22,3 °C', text)
        self.assertIn('88 %', text)
        self.assertIn('24,8 km/h', text)
        self.assertIn('Datos HA 18/10 17:00', text)
        self.assertNotIn('2026-10-18T', text)
        self.assertNotIn('rainy', text)


class FakeClock:
    def __init__(self):
        self.now = 0.
    def __call__(self):
        return self.now
    async def sleep(self, seconds):
        self.now += seconds


class FakeDevice:
    def __init__(self):
        self.calls = []
        self.current = dict(request_id='', state='idle', visible=False, audio='none',
                            reason='', generation=0, truncated=False)
        self.busy = False
        self.verified = False
        self.fail_identity = False
        self.conflict = False
        self.play_outcome = 'done'
    async def verify(self):
        if self.fail_identity:
            raise b.CardError('identity_mismatch')
        self.verified = True
    async def idle(self):
        return not self.busy
    async def status(self):
        return dict(self.current)
    async def call(self, action, data):
        assert self.verified
        self.calls.append((action, dict(data)))
        if action == 'card_show':
            self.current.update(request_id=data['request_id'], state='shown', visible=True,
                                audio='waiting' if data['audio_expected'] else 'none', generation=1)
        elif action == 'card_play':
            if self.conflict:
                self.current.update(request_id='f' * 32, generation=2)
            elif self.play_outcome == 'done':
                self.current.update(state='audio_done', audio='done')
            elif self.play_outcome == 'interrupted':
                self.current.update(state='interrupted', audio='cancelled', visible=False)
            else:
                self.current.update(state='playing', audio='playing')
        elif action == 'card_cancel' and self.current['request_id'] == data['request_id']:
            self.current.update(state='dismissed', audio='cancelled', visible=False)


class FakeTTS:
    async def prepare(self, request):
        return 'http://192.0.2.10:8123/api/tts_proxy/test'


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_spoken_card_survives_completion_until_local_ttl(self):
        device, clock = FakeDevice(), FakeClock()
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('notice', 'Aviso', 'Mensaje de prueba', speak=True))
        self.assertTrue(result['ok'])
        self.assertTrue(result['played'])
        self.assertTrue(device.current['visible'])
        self.assertEqual(device.current['state'], 'audio_done')
        self.assertEqual([action for action, _ in device.calls], ['card_show', 'card_play'])

    async def test_plain_ack_left_to_local_expiry(self):
        device, clock = FakeDevice(), FakeClock()
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('reminder', 'T', 'Ahora'))
        self.assertTrue(result['ok'])
        self.assertTrue(result['displayed'])
        self.assertFalse(result['played'])
        self.assertEqual([c[0] for c in device.calls], ['card_show'])
        self.assertTrue(device.current['visible'])

    async def test_speech_completion_not_send_is_success(self):
        device, clock = FakeDevice(), FakeClock()
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('result', 'T', 'Aportado', speak=True))
        self.assertTrue(result['ok'])
        self.assertTrue(result['played'])
        self.assertEqual([c[0] for c in device.calls], ['card_show', 'card_play'])
        self.assertNotIn('url', str(result))

    async def test_identity_busy_and_producer_conflict_never_clear_other(self):
        for case in ('identity', 'busy', 'conflict', 'interrupted', 'timeout'):
            device, clock = FakeDevice(), FakeClock()
            device.fail_identity = case == 'identity'
            device.busy = case == 'busy'
            device.conflict = case == 'conflict'
            if case in ('interrupted', 'timeout'):
                device.play_outcome = case
            result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
                b.CardRequest('notice', 'T', 'B', 2, True), idle_wait=1)
            self.assertFalse(result['ok'], case)
            self.assertFalse(result['played'], case)
            if case in ('identity', 'busy'):
                self.assertEqual(device.calls, [])
            if case == 'conflict':
                self.assertEqual(device.current['request_id'], 'f' * 32)
                self.assertNotIn('card_cancel', [c[0] for c in device.calls])

    async def test_busy_ttl_and_slow_synthesis_expire_without_device_write(self):
        device, clock = FakeDevice(), FakeClock()
        device.busy = True
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B',2), idle_wait=30)
        self.assertEqual(result['reason'], 'expired')
        self.assertEqual(device.calls, [])
        device.busy = False
        class SlowTTS:
            async def prepare(self, request):
                clock.now += 3
                return 'http://192.0.2.10:8123/api/tts_proxy/private'
        result = await b.Coordinator(device, SlowTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B',2,True))
        self.assertEqual(result['reason'], 'expired')
        self.assertEqual(device.calls, [])

    async def test_error_has_terminal_status_not_old_shown_snapshot(self):
        device, clock = FakeDevice(), FakeClock()
        device.play_outcome = 'interrupted'
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B',30,True))
        self.assertEqual(result['state'],'interrupted')
        self.assertFalse(result['visible'])

    async def test_generation_conflict_late_callback_does_not_cleanup_replacement(self):
        device, clock = FakeDevice(), FakeClock()
        original = device.call
        async def call(action,data):
            await original(action,data)
            if action == 'card_play':
                device.current['generation'] += 1
        device.call = call
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B',30,True))
        self.assertEqual(result['reason'],'generation_conflict')
        self.assertNotIn('card_cancel',[c[0] for c in device.calls])

    async def test_tts_failure_no_silent_fallback_or_show(self):
        device, clock = FakeDevice(), FakeClock()
        class FailedTTS:
            async def prepare(self, request):
                raise b.CardError('tts_error')
        result = await b.Coordinator(device, FailedTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B',30,True))
        self.assertEqual(result['reason'],'tts_error')
        self.assertEqual(device.calls,[])

    async def test_pending_other_producer_not_overwritten(self):
        device, clock = FakeDevice(), FakeClock()
        device.current.update(request_id='b'*32,state='pending',visible=False,card_active=True)
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B'))
        self.assertEqual(result['reason'],'card_busy')
        self.assertEqual(device.calls,[])

    async def test_zero_wait_allows_one_idle_check(self):
        device, clock = FakeDevice(), FakeClock()
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B'),idle_wait=0)
        self.assertTrue(result['ok'])

    async def test_polling_deadline_bounds_slow_adapter(self):
        import asyncio,time
        device = FakeDevice()
        coordinator = b.Coordinator(device)
        async def slow():
            await asyncio.sleep(.1)
            return True
        with self.assertRaises(b.CardError):
            await coordinator._wait(slow,time.monotonic()+.01,'busy')

    async def test_nonblocking_cleanup_is_never_awaited(self):
        device, clock = FakeDevice(), FakeClock()
        device.play_outcome = 'done'
        def sleep(_):
            raise AssertionError('cleanup must be fire-and-forget')
        result = await b.Coordinator(device, FakeTTS(), clock, sleep).show(
            b.CardRequest('notice','T','B',30,True))
        self.assertTrue(result['played'])
        self.assertEqual([c[0] for c in device.calls],['card_show','card_play'])

    async def test_playback_timeout_is_honest(self):
        device, clock = FakeDevice(), FakeClock()
        device.play_outcome = 'playing'
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).show(
            b.CardRequest('notice','T','B',30,True), playback_timeout=.1)
        self.assertEqual(result['reason'],'playback_timeout')

    async def test_cancel_pending_hidden_card(self):
        device, clock = FakeDevice(), FakeClock()
        device.current.update(request_id='a'*32,state='pending',card_active=True)
        result = await b.Coordinator(device, FakeTTS(), clock, clock.sleep).cancel('a'*32)
        self.assertTrue(result['ok'])
        self.assertEqual([c[0] for c in device.calls],['card_cancel'])

    async def test_cancel_is_compare_id_and_verified_readback(self):
        device, clock = FakeDevice(), FakeClock()
        device.current.update(request_id='a' * 32, visible=True, state='shown')
        coordinator = b.Coordinator(device, FakeTTS(), clock, clock.sleep)
        bad = await coordinator.cancel('b' * 32)
        self.assertFalse(bad['ok'])
        self.assertEqual(device.calls, [])
        good = await coordinator.cancel('a' * 32)
        self.assertTrue(good['ok'])
        self.assertFalse(device.current['visible'])


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_discovery_identity_schemas_and_domain_collisions(self):
        from types import SimpleNamespace as NS
        def obj(name, **fields):
            return type(name, (), {})( ) if not fields else type(name, (), fields)()
        schema = {
            'card_show': {'request_id':'STRING','title':'STRING','body':'STRING','kind':'STRING','ttl_ms':'INT','audio_expected':'BOOL'},
            'card_play': {'request_id':'STRING','url':'STRING'}, 'card_cancel': {'request_id':'STRING'}}
        services = [NS(name=n,key=i,args=[NS(name=k,type=NS(name=t)) for k,t in args.items()])
                    for i,(n,args) in enumerate(schema.items())]
        entities = [obj('LightInfo', key=7, object_id='lamp'),
                    obj('MediaPlayerInfo', key=7, object_id='player'),
                    obj('TextSensorInfo', key=8, object_id='card_status'),
                    obj('BinarySensorInfo', key=9, object_id='card_active')]
        class Client:
            def __init__(self):
                self.mac = '00:00:00:00:00:00'
                self.calls = []
            async def device_info(self):
                return NS(mac_address=self.mac)
            async def list_entities_services(self):
                return entities, services
            def subscribe_states(self, callback):
                self.callback = callback
                callback(obj('TextSensorState', key=8, state='{"request_id":"","state":"idle","visible":false,"audio":"none","reason":"","generation":0,"truncated":false}', missing_state=False))
                callback(obj('BinarySensorState', key=9, state=False, missing_state=False))
            async def execute_service(self, service, data):
                self.calls.append((service.name, data))
        client = Client()
        device = b.NativeDevice(client, None)
        await device.verify()
        client.callback(obj('LightState', key=7, state=True))
        client.callback(obj('MediaPlayerState', key=7, state='IDLE'))
        self.assertEqual(device.states[('LightState',7)].state, True)
        self.assertEqual(device.states[('MediaPlayerState',7)].state, 'IDLE')
        self.assertFalse((await device.status())['visible'])
        await device.call('card_cancel', {'request_id':'a'*32})
        self.assertEqual(client.calls[0][0], 'card_cancel')
        client.mac = '02:00:00:00:00:01'
        with self.assertRaises(b.CardError):
            await b.NativeDevice(client,None).verify()
        client.mac = '00:00:00:00:00:00'
        services[0].args[0].type.name = 'INT'
        with self.assertRaises(b.CardError):
            await b.NativeDevice(client,None).verify()

    async def test_tts_adapter_selected_voice_no_playback_or_fallback(self):
        class HA:
            def __init__(self):
                self.posts = []
            async def rest(self, path, data=None):
                if path.startswith('/api/states/'):
                    return {'state':'Chosen'}
                if path == '/api/config':
                    return {'internal_url':'http://192.0.2.10:8123'}
                self.posts.append((path,data))
                return {'path':'/api/tts_proxy/cache_nonce_keep.wav', 'url':'http://127.0.0.1:8123/api/tts_proxy/cache_nonce_keep.wav'}
            async def ws(self, command):
                self.command = command
                return {'preferred_pipeline':'other', 'pipelines':[
                    {'id':'other','name':'Other','tts_engine':None},
                    {'id':'selected','name':'Chosen','tts_engine':'tts.current','tts_language':'es-ES','tts_voice':None}]}
        ha = HA()
        url = await b.HATTS(ha).prepare(b.CardRequest('notice','Título','Texto humano',speak=True))
        self.assertEqual(ha.command, 'assist_pipeline/pipeline/list')
        self.assertEqual(len(ha.posts), 1)
        self.assertEqual(ha.posts[0][0], '/api/tts_get_url')
        self.assertEqual(ha.posts[0][1]['engine_id'], 'tts.current')
        self.assertEqual(ha.posts[0][1]['message'], 'Texto humano')
        self.assertNotIn('voice', ha.posts[0][1]['options'])
        self.assertTrue(url.endswith('/cache_nonce_keep.wav'))

    async def test_status_validation_rejects_malformed(self):
        for value in ({}, {'request_id':'bad'}, 'bad'):
            with self.assertRaises(b.CardError):
                b.parse_status(value)


class LockTests(unittest.TestCase):
    def test_lock_bounded_and_reusable(self):
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = pathlib.Path(tmp)/'lock'
            with b.LocalLock(path, timeout=0):
                with self.assertRaises(b.CardError):
                    with b.LocalLock(path, timeout=0):
                        self.fail('second owner')
            with b.LocalLock(path, timeout=0):
                pass


class CLITests(unittest.TestCase):
    def test_parser_invalid_before_runtime_and_json_exit_codes(self):
        import io
        from contextlib import redirect_stdout
        for args in (['show','--kind','notice','--title','T','--text','B','--seconds','1'],
                     ['cancel','--request-id','bad'], ['show','--title','T','--text','']):
            out = io.StringIO()
            with redirect_stdout(out):
                code = b.main(args, runtime_factory=lambda _: self.fail('invalid input reached runtime'))
            self.assertEqual(code, 2)
            import json
            self.assertFalse(json.loads(out.getvalue())['ok'])
        self.assertEqual(b.exit_code({'ok':False,'reason':'interrupted'}), 4)
        self.assertEqual(b.exit_code({'ok':False,'reason':'expired'}), 5)
        self.assertEqual(b.exit_code({'ok':False,'reason':'rejected'}), 6)

    def test_full_cli_show_injected_no_network(self):
        import io,json
        from contextlib import asynccontextmanager, redirect_stdout
        device = FakeDevice()
        @asynccontextmanager
        async def runtime(args):
            yield device, None
        out = io.StringIO()
        with redirect_stdout(out):
            code = b.main(['show','--kind','result','--title','¡Hola!','--text','Resultado aportado'], runtime_factory=runtime)
        self.assertEqual(code, 0)
        result = json.loads(out.getvalue())
        self.assertTrue(result['displayed'])
        self.assertFalse(result['played'])
        self.assertEqual(device.calls[0][1]['body'], 'Resultado aportado')


class HTTPTests(unittest.IsolatedAsyncioTestCase):
    async def test_ha_adapter_routes_guard_and_real_json_encoding(self):
        import json
        calls = []
        def opener(request, timeout):
            calls.append(request)
            class Response:
                def __enter__(self): return self
                def __exit__(self,*args): pass
                def read(self,n): return b'{"path":"/api/tts_proxy/private"}'
            return Response()
        ha = b.HAClient('http://127.0.0.1:8123','private-token', opener=opener)
        await ha.rest('/api/tts_get_url', {'engine_id':'tts.current','message':'Café'})
        self.assertEqual(json.loads(calls[0].data)['message'], 'Café')
        self.assertEqual(calls[0].get_method(),'POST')
        self.assertEqual(calls[0].get_header('Authorization'),'Bearer private-token')
        with self.assertRaises(b.CardError):
            await ha.rest('/api/services/assist_satellite/announce',{})
        with self.assertRaises(b.CardError):
            await ha.ws('assist_pipeline/run')
        self.assertEqual(len(calls),1)


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_connection_identity_client_label_login_and_async_stop(self):
        import inspect,sys
        from types import SimpleNamespace as NS
        from unittest.mock import patch
        class Client:
            def __init__(self,*args,**kwargs):
                self.kwargs = kwargs
                self.closed = False
            async def connect(self, **kwargs):
                self.connect_kwargs = kwargs
            async def disconnect(self):
                self.closed = True
        client = Client()
        def factory(*args, **kwargs):
            client.kwargs = kwargs
            return client
        fake_aio = NS(APIClient=factory)
        fake_yaml = NS(safe_load=lambda _: {'api_encryption_key':'test-secret'})
        with patch.dict(sys.modules, {'aioesphomeapi':fake_aio, 'yaml':fake_yaml}), \
             patch.object(b,'SECRETS',NS(read_text=lambda:'test')), \
             patch.object(b.HAClient,'from_local',return_value=NS()):
            async with b.create_runtime(NS(host='example.local')) as (device,ha):
                self.assertEqual(client.kwargs['client_info'],'HermesCards')
                self.assertFalse(client.kwargs['provide_time'])
                self.assertEqual(client.kwargs['expected_mac'],'000000000000')
                self.assertIs(client.connect_kwargs.get('login'), True)
                self.assertTrue(inspect.iscoroutinefunction(client.connect_kwargs['on_stop']))
                await client.connect_kwargs['on_stop'](False)
                self.assertFalse(device.connected)
        self.assertTrue(client.closed)


class SignalTests(unittest.IsolatedAsyncioTestCase):
    async def test_sigterm_cancels_current_operation_and_restores_handlers(self):
        import asyncio,signal
        from unittest.mock import patch
        loop = asyncio.get_running_loop()
        callbacks, removed = {}, []
        async def command(*_):
            callbacks[signal.SIGTERM]()
            await asyncio.sleep(0)
        with patch.object(loop,'add_signal_handler',side_effect=lambda sig,cb:callbacks.update({sig:cb})), \
             patch.object(loop,'remove_signal_handler',side_effect=lambda sig:removed.append(sig)), \
             patch.object(b,'run_command',side_effect=command):
            with self.assertRaises(asyncio.CancelledError):
                await b.run_with_signals(None,None,None)
        self.assertIn(signal.SIGTERM,removed)
        self.assertIn(signal.SIGINT,removed)


if __name__ == '__main__':
    unittest.main()

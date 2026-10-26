"""Host-only timing tests; generated fixtures are not hardware recordings."""
import asyncio
import importlib.util
import io
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parent
SCRATCH = Path('/path/to/user/.hermes/cache/scratch')
sys.path.insert(0, str(ROOT))

def pcm(frames=4800, channels=1, rate=48000):
    out = io.BytesIO()
    with wave.open(out, 'wb') as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(b'\x00\x00' * frames * channels)
    return out.getvalue()

class PCMTests(unittest.TestCase):
    def test_real_pcm_frames_not_stream_sentinel(self):
        spec = importlib.util.find_spec('ui_timing_runtime')
        self.assertIsNotNone(spec, 'decoded duration implementation is missing')
        import ui_timing_runtime as timing
        self.assertEqual(timing.pcm_duration_ms(pcm()), 100)
        self.assertEqual(timing.pcm_duration_ms(pcm(channels=2)), 100)
        streaming = bytearray(pcm())
        struct.pack_into('<I', streaming, 4, 0xffffffff)
        struct.pack_into('<I', streaming, 40, 0xffffffff)
        self.assertEqual(timing.pcm_duration_ms(streaming), 100)
        with self.assertRaises(ValueError):
            timing.pcm_duration_ms(pcm()[:-1])

    def test_format_alignment_bounds_and_extra_chunks(self):
        import ui_timing_runtime as timing
        for index, value, encoding in ((22,0,'H'), (24,0,'I'), (28,1,'I'), (32,1,'H'), (34,7,'H')):
            bad = bytearray(pcm())
            struct.pack_into('<'+encoding, bad, index, value)
            with self.assertRaises(ValueError): timing.pcm_duration_ms(bad)
        with self.assertRaises(ValueError): timing.pcm_duration_ms(pcm(frames=1))
        with self.assertRaises(ValueError): timing.pcm_duration_ms(pcm(frames=48000*601))
        extra = bytearray(pcm()[:12] + b'JUNK\x04\x00\x00\x00test' + pcm()[12:])
        struct.pack_into('<I', extra, 4, len(extra)-8)
        self.assertEqual(timing.pcm_duration_ms(extra), 100)

class WrapperTests(unittest.IsolatedAsyncioTestCase):
    async def test_original_arguments_and_body_unchanged_before_return(self):
        import ui_timing_runtime as timing
        self.assertTrue(hasattr(timing, 'TimingRuntime'), 'runtime wrapper missing')
        class Original:
            def capabilities(self): return {'tts': True}
            async def infer(self, *args, **kwargs): return args, kwargs
            async def close(self): self.closed = True
            async def synthesize(self, *args, **kwargs):
                self.called = args, kwargs
                return body, 'audio/wav'
        body = pcm()
        original = Original()
        sent = []
        async def sender(message, duration_ms):
            sent.append((message, duration_ms))
            return {'sent': True, 'supported': True}
        with tempfile.TemporaryDirectory(dir=SCRATCH) as root:
            wrapper = timing.TimingRuntime(original, sender=sender, diagnostic=Path(root)/'stats.json')
            kwargs = dict(language='es', provider=None, voice=None, speed=None, instructions=None)
            result = await wrapper.synthesize('Prueba exacta. ', **kwargs)
            self.assertIs(result[0], body)
            self.assertEqual(result[1], 'audio/wav')
            self.assertEqual(original.called, (('Prueba exacta. ',), kwargs))
            self.assertEqual(sent, [('Prueba exacta. ', 100)])
            self.assertEqual(wrapper.capabilities(), {'tts': True})
            self.assertEqual(await wrapper.infer('input', language='es'), (('input',), {'language':'es'}))
            await wrapper.close()
            self.assertTrue(original.closed)

    async def test_fail_open_unknown_audio_timeout_diagnostic_and_stt(self):
        import ui_timing_runtime as timing
        class Original:
            async def synthesize(self, *args, **kwargs): return self.body, 'original/type'
            async def infer(self, *args, **kwargs):
                self.infer_call = args, kwargs
                return 'original answer'
        original = Original()
        original.body = b'unknown'
        sent = []
        async def sender(*args):
            sent.append(args)
            await asyncio.sleep(10)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as root:
            diag = Path(root)/'stats.json'
            wrapper = timing.TimingRuntime(original, sender=sender, diagnostic=diag)
            self.assertEqual(await wrapper.synthesize('secret'), (b'unknown', 'original/type'))
            self.assertTrue(diag.exists(), 'private numeric diagnostics missing')
            original.body = pcm()
            wrapper.tts_budget = .04
            await asyncio.wait_for(wrapper.synthesize('secret'), .3)
            wrapper.stt_budget = .04
            messages = [{'role':'system','content':'not sent'}, {'role':'user','content':'Exacta. '},
                        {'role':'assistant','content':'not sent'}]
            self.assertEqual(await asyncio.wait_for(wrapper.infer(messages, language='es'), .3), 'original answer')
            self.assertIs(original.infer_call[0][0], messages)
            self.assertEqual(original.infer_call[1], {'language':'es'})
            self.assertEqual(sent[-1], ('Exacta. ', None))
            data = __import__('json').loads(diag.read_text())
            self.assertTrue(all(type(v) in (int, bool) for v in data.values()))
            self.assertNotIn('secret', diag.read_text())
            self.assertEqual(diag.stat().st_mode & 0o777, 0o600)

    async def test_stt_ignores_nonusers_and_preserves_original_error(self):
        import ui_timing_runtime as timing
        calls=[]
        class Original:
            async def infer(self, *args, **kwargs): return args, kwargs
            async def synthesize(self, *args, **kwargs): raise RuntimeError('original failure')
        async def sender(*args): calls.append(args); raise OSError('fixture transport failure')
        wrapper=timing.TimingRuntime(Original(), sender=sender, diagnostic=None)
        messages=[{'role':'system','content':'system'}, {'role':'assistant','content':'assistant'},
                  {'role':'tool','content':'tool'}]
        self.assertEqual((await wrapper.infer(messages))[0], (messages,))
        self.assertEqual(calls, [])
        messages += [{'role':'user','content':'first'}, {'role':'user','content':'last'}]
        await wrapper.infer(messages)
        self.assertEqual(calls, [('last',None)])
        with self.assertRaisesRegex(RuntimeError, 'original failure'):
            await wrapper.synthesize('test')

    async def test_http_body_and_mime_unchanged_on_metadata_failure(self):
        try:
            import aiohttp
        except ImportError:
            self.skipTest('HTTP regression requires existing provider dependencies')
        sys.path.insert(0, str(ROOT/'provider'))
        from hermes_ha_provider import app
        from types import SimpleNamespace as NS
        import ui_timing_runtime as timing
        body=pcm()
        class Original:
            def tts_capabilities(self): return {'providers':[], 'default_provider':None}
            async def synthesize(self,*args,**kwargs): return body, 'audio/wav'
        async def sender(*args): raise OSError('fixture failure')
        async def read(limit): return b'{"text":"Test"}'
        request=NS(content_length=15, content_type='application/json', content=NS(read=read),
                   app={app.SETTINGS_KEY:NS(json_limit=1000,tts_text_limit=1000),
                        app.RUNTIME_KEY:timing.TimingRuntime(Original(),sender=sender,diagnostic=None)})
        response=await app.tts(request)
        self.assertIs(response.body,body)
        self.assertEqual(response.content_type,'audio/wav')

    async def test_diagnostic_cleanup_error_cannot_break_audio(self):
        import ui_timing_runtime as timing
        from unittest.mock import patch
        class Original:
            async def synthesize(self,*args,**kwargs): return b'unknown', 'audio/mpeg'
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            wrapper=timing.TimingRuntime(Original(),diagnostic=Path(directory)/'numeric.json')
            with patch.object(Path, 'unlink', side_effect=OSError('fixture cleanup error')):
                self.assertEqual(await wrapper.synthesize('Prueba'), (b'unknown','audio/mpeg'))

class ProcessTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_timeout_cancel_reaps_child_and_private_decode_cleanup(self):
        import ui_timing_runtime as timing
        self.assertTrue(hasattr(timing, 'run_process'), 'bounded process runner missing')
        import time
        with tempfile.TemporaryDirectory(dir=SCRATCH) as root:
            pidfile = Path(root)/'pid'
            code = "import os,time,pathlib; pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(20)" % str(pidfile)
            task = asyncio.create_task(timing.run_process([sys.executable, '-c', code], timeout=.15))
            with self.assertRaises(asyncio.TimeoutError): await task
            pid = int(pidfile.read_text())
            with self.assertRaises(ProcessLookupError): os.kill(pid, 0)
            task = asyncio.create_task(timing.run_process([sys.executable, '-c', code], timeout=20))
            await asyncio.sleep(.08)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError): await task
            with self.assertRaises(ProcessLookupError): os.kill(int(pidfile.read_text()), 0)
            before = set(SCRATCH.glob('ball-ui-audio-*'))
            with self.assertRaises(ValueError):
                await timing.measure_duration(b'ID3 invalid fixture', 'audio/mpeg')
            self.assertEqual(before, set(SCRATCH.glob('ball-ui-audio-*')))

    async def test_fragmented_stdout_is_complete_and_oversize_rejected(self):
        import ui_timing_runtime as timing
        code = "import sys,time;sys.stdout.write('a');sys.stdout.flush();time.sleep(.03);sys.stdout.write('b')"
        self.assertEqual(await timing.run_process([sys.executable, '-c', code]), b'ab')
        with self.assertRaises(ValueError):
            await timing.run_process([sys.executable, '-c', "print('x'*2000)"])

    async def test_generated_mp3_fixture_decodes_to_real_frames(self):
        import ui_timing_runtime as timing
        if not Path('/usr/bin/afconvert').exists():
            self.skipTest('afconvert not installed; no install attempted')
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            source, mp3, decoded = (Path(directory)/n for n in ('fixture.wav','fixture.mp3','decoded.wav'))
            source.write_bytes(pcm(frames=48000))
            try:
                await timing.run_process(['/usr/bin/afconvert','-f','MPG3','-d','.mp3',str(source),str(mp3)])
            except ValueError:
                self.skipTest('Apple MP3 encoder unavailable (decoder tested separately with real provider)')
            await timing.run_process(['/usr/bin/afconvert','-f','WAVE','-d','LEI16',str(mp3),str(decoded)])
            expected = timing.pcm_duration_ms(decoded.read_bytes())
            measured, quality = await timing.measure_duration(mp3.read_bytes(), 'audio/mpeg')
            self.assertEqual(measured, expected)
            self.assertEqual(quality, 2)

    async def test_stale_private_audio_ttl_and_modes(self):
        import ui_timing_runtime as timing
        from unittest.mock import patch
        stale = Path(tempfile.mkdtemp(prefix='ball-ui-audio-', dir=SCRATCH))
        (stale/'source.mp3').write_bytes(b'expired fixture')
        old = __import__('time').time()-700
        os.utime(stale, (old, old))
        runner = timing.run_process
        seen=[]
        async def observe(argv, **kwargs):
            source = Path(argv[-2])
            seen.append(True)
            self.assertEqual(source.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(source.stat().st_mode & 0o777, 0o600)
            self.assertEqual(Path(argv[-1]).stat().st_mode & 0o777, 0o600)
            return await runner(argv, **kwargs)
        try:
            with patch.object(timing, 'run_process', observe):
                with self.assertRaises(ValueError):
                    await timing.measure_duration(b'ID3 invalid fixture', 'audio/mpeg')
            self.assertTrue(seen)
            self.assertFalse(stale.exists(), 'stale private audio must expire')
        finally:
            __import__('shutil').rmtree(stale, ignore_errors=True)

class HelperTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_schema_readonly_probe_and_stt_tts_dispatch(self):
        helperpath = Path('/path/to/user/.hermes/projects/xiaozhi-ui-v3/ui_tts_timing_send.py')
        self.assertTrue(helperpath.exists(), 'ephemeral native helper missing')
        spec = importlib.util.spec_from_file_location('timing_helper', helperpath)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        from types import SimpleNamespace as NS
        def service(name, schema):
            return NS(name=name, key=1, args=[NS(name=k, type=NS(name=v)) for k,v in schema.items()])
        class Client:
            services=[]
            calls=[]
            async def device_info(self): return NS(mac_address='00:00:00:00:00:00')
            async def list_entities_services(self): return [], self.services
            async def execute_service(self, svc, values): self.calls.append((svc.name, values))
        client = Client()
        payload = helper.validate({'message':'Exacta. ', 'duration_ms':100})
        self.assertTrue((await helper.dispatch(client, payload))['unsupported'])
        self.assertEqual(client.calls, [])
        client.services=[service('ui_tts_timing', {'message':'STRING','duration_ms':'INT'})]
        self.assertTrue((await helper.dispatch(client, payload, probe=True))['supported'])
        self.assertEqual(client.calls, [])
        self.assertTrue((await helper.dispatch(client, payload))['sent'])
        self.assertEqual(client.calls[-1], ('ui_tts_timing', {'message':'Exacta. ', 'duration_ms':100}))
        client.services=[service('ui_stt_text', {'message':'STRING'})]
        self.assertTrue((await helper.dispatch(client, helper.validate({'kind':'stt','message':'Completa'})))['sent'])
        self.assertEqual(client.calls[-1], ('ui_stt_text', {'message':'Completa'}))
        client.services=[service('ui_tts_timing', {'message':'STRING','duration_ms':'FLOAT'})]
        self.assertTrue((await helper.dispatch(client,payload))['schema_mismatch'])
        for data in ({'message':'a'*4097,'duration_ms':100}, {'message':'x','duration_ms':True},
                     {'message':'x','duration_ms':600001}, {'kind':'stt','message':'x','duration_ms':10},
                     {'kind':'other','message':'x'}, {'message':'\ud800','duration_ms':1}):
            with self.assertRaises(ValueError): helper.validate(data)

class EntrypointTests(unittest.TestCase):
    def test_factory_only_wraps_ball_loopback_without_endpoint_changes(self):
        import ui_timing_runtime as timing
        self.assertTrue(hasattr(timing, 'wrap_app_factory'), 'entrypoint companion binding missing')
        from types import SimpleNamespace as NS
        runtime = object()
        calls = []
        def factory(settings, original):
            calls.append((settings, original))
            return 'same app'
        companion = timing.wrap_app_factory(factory)
        settings = NS(host='127.0.0.1', port=18765, hermes_api_session_key='xiaozhi-assist-test')
        self.assertEqual(companion(settings, runtime), 'same app')
        self.assertIsInstance(calls[-1][1], timing.TimingRuntime)
        settings = NS(host='127.0.0.1', port=18766, hermes_api_session_key='xiaozhi-assist-test')
        companion(settings, runtime)
        self.assertIs(calls[-1][1], runtime)

if __name__ == '__main__':
    unittest.main()

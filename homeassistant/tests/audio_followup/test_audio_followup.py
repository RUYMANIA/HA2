"""Offline transport follow-up: real HA registry and Sender, IO/clock fixtures only."""
import asyncio
import importlib.util
import json
import pathlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('baseline_ha_tests', ROOT / 'tests/backend/test_ha.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
transport = baseline.transport


class AudioFollowup(unittest.IsolatedAsyncioTestCase):
    # Reuse fixture setup/helpers, not its test methods (safe for discovery too).
    put = baseline.TransportTests.put
    sync = baseline.TransportTests.sync
    sleep = baseline.TransportTests.sleep
    claim = baseline.TransportTests.claim

    async def asyncSetUp(self):
        await baseline.TransportTests.asyncSetUp(self)
        self.job['rule']['mode'] = 'voice'
        self.valid = True
        self.prepared = 0
        self.prepare_hook = lambda: None
        self.show_hook = lambda: None
        self.play_hook = lambda: None
        self.play_wait = None
        self.show_ack = True
        self.play_done = True
        self.put('select.xiaozhi_ball_v2_assistant', 'Fixture pipeline')
        resolved = SimpleNamespace(name='Fixture pipeline', tts_engine='tts.fixture', tts_language='es-ES', tts_voice=None)
        owner = self
        class Stream:
            url = '/api/tts_proxy/fixture.wav'
            def async_set_message(self, body):
                owner.assertEqual(body, owner.job['rule']['body'])
                owner.prepared += 1
                owner.prepare_hook()
        class Manager:
            def async_create_result_stream(self, engine, **kwargs):
                owner.assertEqual(engine, 'tts.fixture')
                owner.assertFalse(kwargs['use_file_cache'])
                return Stream()
        self.hass.data[transport.tts.DATA_TTS_MANAGER] = Manager()
        self.enterContext(patch.object(transport.pipeline, 'async_get_pipelines', return_value=[resolved]))
        self.enterContext(patch.object(transport, 'get_url', return_value='http://192.0.2.20:8123'))
        async def handler(service_call):
            self.assertTrue(self.claimed)
            action = service_call.service
            data = dict(service_call.data)
            self.calls.append((action, data))
            if action.endswith('card_show'):
                if self.show_ack:
                    self.status.update(request_id=data['request_id'], generation=3, state='shown', visible=True, audio='none')
                    self.sync()
                self.show_hook()
            elif action.endswith('card_play'):
                if self.play_done:
                    self.status.update(state='audio_done', audio='done')
                    self.sync()
                self.play_hook()
                if self.play_wait is not None:
                    self.play_wait[0].set()
                    await self.play_wait[1].wait()
            else:
                self.fail('No cancel/STOP or other service allowed')
        for action in ('card_show', 'card_play', 'card_cancel'):
            self.hass.services.async_register('esphome', 'xiaozhi_ball_v2_' + action, handler)

    async def deliver(self):
        return await self.sender.deliver(self.job, self.claim, lambda: self.valid)

    def actions(self):
        return [name.removeprefix('xiaozhi_ball_v2_') for name, _ in self.calls]

    def foreign(self):
        self.status.update(request_id='b'*32, generation=4)
        self.sync()

    async def test_followup_audio_done(self):
        self.assertEqual(await self.deliver(), ('audio_done', ''))
        self.assertEqual(self.prepared, 1)
        self.assertEqual(self.actions(), ['card_show', 'card_play'])

    async def test_followup_audio_busy(self):
        self.show_hook = lambda: self.put('media_player.xiaozhi_ball_v2', 'playing')
        self.assertEqual(await self.deliver(), ('delivered', 'audio_busy'))
        self.assertEqual(self.actions(), ['card_show'])

    async def test_followup_night_suppressed_on_play(self):
        def suppressed():
            self.status.update(state='shown', audio='suppressed', reason='night_mode')
            self.sync()
        self.play_hook = suppressed
        self.assertEqual(await self.deliver(), ('night_silent', 'night_mode'))
        self.assertEqual(self.actions(), ['card_show', 'card_play'])

    async def test_followup_ownership_changed_after_play(self):
        self.play_hook = self.foreign
        self.assertEqual(await self.deliver(), ('uncertain', 'ownership_changed'))
        self.assertEqual(self.actions(), ['card_show', 'card_play'])

    async def test_followup_ownership_changed_before_play(self):
        # Real state-store read boundary: shown ACK is read once, then replaced.
        original = type(self.hass.states).get
        reads = 0
        def get(store, entity_id):
            nonlocal reads
            if entity_id == 'sensor.xiaozhi_ball_v2_card_status' and self.calls:
                reads += 1
                if reads == 2:
                    self.foreign()
            return original(store, entity_id)
        with patch.object(type(self.hass.states), 'get', get):
            self.assertEqual(await self.deliver(), ('uncertain', 'ownership_changed'))
        self.assertEqual(self.actions(), ['card_show'])

    async def test_followup_audio_unconfirmed_terminal(self):
        def fail():
            self.status.update(audio='failed')
            self.sync()
        self.play_hook = fail
        self.assertEqual(await self.deliver(), ('delivered', 'audio_unconfirmed'))
        self.assertEqual(self.actions(), ['card_show', 'card_play'])

    async def test_followup_audio_unconfirmed_clock_deadline(self):
        self.play_done = False
        self.assertEqual(await self.deliver(), ('delivered', 'audio_unconfirmed'))
        self.assertGreaterEqual(self.mono, 120)
        self.assertLess(self.mono, 120.2)
        self.assertEqual(self.actions(), ['card_show', 'card_play'])

    async def test_followup_guard_after_real_prepare(self):
        self.prepare_hook = lambda: setattr(self, 'valid', False)
        self.assertEqual(await self.deliver(), ('cancelled', 'configuration_changed'))
        self.assertEqual(self.prepared, 1)
        self.assertFalse(self.claimed)
        self.assertEqual(self.calls, [])

    async def test_followup_busy_after_real_prepare(self):
        self.prepare_hook = lambda: self.put('media_player.xiaozhi_ball_v2', 'playing')
        self.assertEqual(await self.deliver(), ('waiting', 'busy'))
        self.assertEqual(self.prepared, 1)
        self.assertFalse(self.claimed)
        self.assertEqual(self.calls, [])

    async def test_followup_night_after_real_prepare(self):
        self.prepare_hook = lambda: self.put('sensor.xiaozhi_ball_v2_ui_night', json.dumps({'night_active': True}))
        self.assertEqual(await self.deliver(), ('night_silent', 'night_mode'))
        self.assertEqual(self.prepared, 1)
        self.assertFalse(self.calls[0][1]['audio_expected'])
        self.assertEqual(self.actions(), ['card_show'])

    async def test_followup_guard_after_claim(self):
        async def claim(generation):
            await self.claim(generation)
            self.valid = False
        self.assertEqual(await self.sender.deliver(self.job, claim, lambda: self.valid), ('cancelled', 'configuration_changed'))
        self.assertTrue(self.claimed)
        self.assertEqual(self.calls, [])

    async def test_followup_audio_guard_after_play(self):
        self.play_hook = lambda: setattr(self, 'valid', False)
        self.assertEqual(await self.deliver(), ('delivered', 'audio_cancelled'))
        self.assertEqual(self.actions(), ['card_show', 'card_play'])

    async def test_followup_real_task_cancellation(self):
        started, release = asyncio.Event(), asyncio.Event()
        self.play_wait = (started, release)
        task = asyncio.create_task(self.deliver())
        await asyncio.wait_for(started.wait(), 2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(task.cancelled())
        self.assertEqual(self.actions(), ['card_show', 'card_play'])

    async def test_followup_prepare_io_cancellation_signal(self):
        # Stream allocation is synchronous: inject its cancellation exception,
        # rather than self-cancelling a task without a suspension point.
        def cancelled():
            raise asyncio.CancelledError()
        self.prepare_hook = cancelled
        with self.assertRaises(asyncio.CancelledError):
            await self.deliver()
        self.assertEqual(self.prepared, 1)
        self.assertFalse(self.claimed)
        self.assertEqual(self.calls, [])

    async def test_followup_show_ack_clock_deadline(self):
        self.show_ack = False
        self.assertEqual(await self.deliver(), ('uncertain', 'show_unconfirmed'))
        self.assertGreaterEqual(self.mono, 3)
        self.assertLess(self.mono, 3.2)
        self.assertEqual(self.actions(), ['card_show'])


if __name__ == '__main__':
    # Run only added cases: inherited baseline cases have different IO assumptions.
    names = sorted(n for n in dir(AudioFollowup) if n.startswith('test_followup_'))
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(AudioFollowup(n) for n in names))
    raise SystemExit(not result.wasSuccessful())

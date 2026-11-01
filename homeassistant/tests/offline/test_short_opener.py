"""Pure probes of exact installed validator and transport AST, not HA compatibility.

Compile unchanged stdlib imports, constants, validator and transport class from
native_transport.py. HA imports and _resolve's default branch are not exercised;
resolver/gate/client/starter are inert fixtures. No claim about native HA/audio.
"""
import ast
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load_transport():
    path = ROOT / 'custom_components/ha2_notifications/native_transport.py'
    tree = ast.parse(path.read_text(), filename=str(path))
    allowed_imports = {'__future__', 'pathlib', 'types', 'zoneinfo', 'time', 're', 'unicodedata'}
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Import) and all(n.name in allowed_imports for n in node.names):
            nodes.append(node)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module in allowed_imports:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id.startswith('MAX_OPENER_') for t in node.targets):
            nodes.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in {'valid_short_opener', 'NativeProactiveTransport'}:
            nodes.append(node)
    from custom_components.ha2_notifications.proactive import CAPABILITY_KEYS, INTENT_IDS
    namespace = dict(__file__=str(path), CAPABILITY_KEYS=CAPABILITY_KEYS, INTENT_IDS=INTENT_IDS)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return SimpleNamespace(**namespace)


class ShortOpenerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.module = load_transport()
        self.calls, self.presentations = [], []
        self.text = '¿Te apetece charlar?'
        self.invalidations = 0
        async def inference(**kw):
            self.calls.append(kw)
            return SimpleNamespace(text=self.text)
        async def start(body, valid, **kw):
            self.assertTrue(valid())
            self.presentations.append((body, kw))
            return dict(accepted=True, completed=True)
        def invalidate():
            self.invalidations += 1
        self.context = SimpleNamespace(
            client=SimpleNamespace(async_inference=inference),
            gate=SimpleNamespace(install=lambda: True, invalidate=invalidate, probe=lambda: True),
            pipeline=SimpleNamespace(language='es'), satellite=object(),
            starter=SimpleNamespace(start=start, active=False),
        )
        hass = SimpleNamespace(config=SimpleNamespace(time_zone='UTC'))
        sender = SimpleNamespace(clock=lambda: datetime(2026, 10, 29, 12, tzinfo=timezone.utc))
        self.transport = self.module.NativeProactiveTransport(
            hass, sender, resolver=lambda: self.context, cue_media_id='fixture://cue')
        async def readiness():
            return dict(ready=True)
        self.transport.readiness = readiness
        self.rid = 'a' * 32

    async def generate(self):
        return await self.transport.generate(self.rid, 'saludo', {}, lambda: True)

    async def test_exact_character_word_byte_boundaries(self):
        self.assertEqual((self.module.MAX_OPENER_CHARACTERS, self.module.MAX_OPENER_WORDS,
                          self.module.MAX_OPENER_UTF8_BYTES), (120, 20, 240))
        for text in ['á' * 119 + '.', ' '.join(['a'] * 20) + '.', '界' * 79 + 'á' + '.', 'a\u0301' * 59 + '.']:
            with self.subTest(text=ascii(text)):
                self.assertTrue(self.module.valid_short_opener(text))
        for text in ['a' * 120 + '.', ' '.join(['a'] * 21) + '.', '界' * 80 + '.']:
            with self.subTest(text=ascii(text)):
                self.assertFalse(self.module.valid_short_opener(text))

    async def test_invalid_format_and_unicode_rejected(self):
        for text in [None, '', ' Hola.', 'Hola. ', 'Hola. ¿Charlamos?', 'Hola\n¿Charlamos?',
                     'Hola… ¿Charlamos?', 'Hola。 ¿Charlamos?', '¿Charlamos?!', '**¿Charlamos?**',
                     '¿Charlamos?\x00', '¿Charlamos?\u2028', 'Hola\ud800.', '¿Charlamos? 😊',
                     'Una invitación sin terminar', '- Hola.', 'https://fixture.invalid.']:
            with self.subTest(text=ascii(text)):
                self.assertFalse(self.module.valid_short_opener(text))

    async def test_invalid_generation_has_no_truncation_retry_or_presentation(self):
        self.text = 'a' * 120 + '.'
        with self.assertRaisesRegex(RuntimeError, 'invalid_opener'):
            await self.generate()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.presentations, [])
        self.assertIsNone(self.transport.owner)
        self.assertIsNone(self.transport.prepared)

    async def test_exact_valid_text_and_context_reach_both_presentation_modes(self):
        for mode in ('cue', 'voice'):
            self.text = '¿Te apetece charlar sobre ciencia ficción?'
            prepared = await self.generate()
            self.assertEqual(prepared['body'], self.text)
            self.assertIs(prepared['context'], self.context)
            self.assertEqual(self.calls[-1]['conversation_id'], self.rid)
            self.assertTrue(self.calls[-1]['bootstrap_session'])
            result = await self.transport.present(prepared, dict(mode=mode), lambda: True)
            self.assertTrue(result['completed'])
            self.assertEqual(self.presentations[-1], (self.text, dict(media_id='fixture://cue' if mode == 'cue' else None)))

    async def test_validator_runs_again_before_presentation(self):
        for mode in ('cue', 'voice'):
            prepared = await self.generate()
            prepared['body'] = 'Hola. ¿Charlamos?'
            result = await self.transport.present(prepared, dict(mode=mode), lambda: True)
            self.assertEqual(result, dict(accepted=False, completed=False, reason='invalid_opener'))
            self.assertEqual(self.presentations, [])
            self.assertIsNone(self.transport.owner)
        self.assertEqual(self.invalidations, 2)

    async def test_prompt_declares_actual_limits(self):
        await self.generate()
        prompt = self.calls[-1]['messages'][0]['content']
        for text in ['una única frase', '120 caracteres', '20 palabras', '240 bytes UTF-8', 'Sin listas']:
            self.assertIn(text, prompt)

    async def test_ownership_guard_blocks_foreign_prepared_and_preserves_owner(self):
        prepared = await self.generate()
        foreign = dict(prepared, request_id='b' * 32)
        result = await self.transport.present(foreign, dict(mode='voice'), lambda: True)
        self.assertEqual(result['reason'], 'ownership_changed')
        await self.transport.cancel('b' * 32)
        self.assertEqual(self.transport.owner, self.rid)
        self.assertEqual(self.presentations, [])
        await self.transport.close()
        self.assertIsNone(self.transport.owner)

    async def test_invalidated_generation_never_prepares(self):
        valid = True
        async def inference(**kw):
            nonlocal valid
            valid = False
            return SimpleNamespace(text=self.text)
        self.context.client.async_inference = inference
        with self.assertRaisesRegex(RuntimeError, 'invalid_opener'):
            await self.transport.generate(self.rid, 'saludo', {}, lambda: valid)
        self.assertIsNone(self.transport.owner)
        self.assertEqual(self.presentations, [])

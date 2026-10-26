import unittest
import sys
sys.path.insert(0, '/config')
from custom_components.hermes_agent.tts import HermesTTSEntity

class InheritedVoiceTests(unittest.TestCase):
    def test_default_requests_do_not_reuse_audio_from_previous_voice(self):
        entity = HermesTTSEntity.__new__(HermesTTSEntity)
        entity._attr_default_options = None
        first = dict(entity.default_options or {})
        second = dict(entity.default_options or {})
        self.assertNotEqual(first, second, 'Identical cache key would reuse old voice audio')
        self.assertNotIn('voice', first)
        self.assertNotIn('provider', first)
        self.assertNotIn('speed', first)

if __name__ == '__main__':
    unittest.main()

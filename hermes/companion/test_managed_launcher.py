import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

class LauncherTests(unittest.TestCase):
    def test_enters_managed_runtime_without_pinning_tts(self):
        import managed_launcher
        original = ['python', '-I', '-c', "import runpy,sys; import hermes_bootstrap; runpy.run_module('hermes_cli.main',run_name='__main__')"]
        result = managed_launcher.script_command(original, Path('/private/provider.py'), ['--probe'])
        self.assertEqual(result[:3], original[:3])
        self.assertIn('import hermes_bootstrap;', result[-1])
        self.assertIn("runpy.run_path('/private/provider.py'", result[-1])
        self.assertIn('--probe', result[-1])
        self.assertNotIn('tts.provider', result[-1])
        self.assertIn("runpy.run_module('hermes_cli.main'", original[-1])

if __name__ == '__main__':
    unittest.main()

"""Offline snapshot checks. Never invoke provider/card entrypoints or live services."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hermes-source', type=Path, help='Optional Hermes core checkout for plugin API tests')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    card_lock = root/'cards/.backend.lock'
    if card_lock.exists():
        parser.error('Snapshot must be offline with no existing cards/.backend.lock')
    compiled = 0
    for path in sorted(root.rglob('*.py')):
        compile(path.read_bytes(), str(path), 'exec')
        compiled += 1
    results = []
    # A fresh home prevents core imports from reading the operator profile/.env.
    with tempfile.TemporaryDirectory(prefix='.snapshot-tests-', dir=root) as sandbox:
        env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT', 'LANG', 'LC_ALL') if key in os.environ}
        env.update(HOME=sandbox, HERMES_HOME=sandbox, TMPDIR=sandbox,
                   PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        suites = [
            ('launcher', 'companion', ['-I', '-B', '-m', 'unittest', 'discover', '-s', '.', '-p', 'test_managed_launcher.py', '-v']),
            ('cards', 'cards', ['-I', '-B', '-m', 'unittest', 'discover', '-s', '.', '-p', 'test_backend.py', '-v']),
            ('bridge', 'plugin', ['-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests/bridge', '-p', 'test_*.py', '-v']),
            ('runtime', 'plugin', ['-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests/runtime', '-p', 'test_*.py', '-v']),
        ]
        # Only pure PCM/explicitly injected sender wrappers; no helper/device calls.
        timing_code = '''import sys,unittest,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import test_ui_timing as tests
import ui_timing_runtime as timing
tests.SCRATCH=Path(os.environ['TMPDIR'])
timing.SCRATCH=tests.SCRATCH
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (tests.PCMTests,tests.WrapperTests,tests.EntrypointTests))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
'''
        suites.append(('timing_pure_subset', 'companion', ['-I', '-B', '-c', timing_code]))
        if args.hermes_source:
            env['PYTHONPATH'] = str(args.hermes_source.resolve())
            suites.append(('plugin_all', 'plugin', ['-B', '-m', 'pytest', '-p', 'pytest_asyncio.plugin', '-p', 'no:cacheprovider', '--import-mode=importlib', '-q', '-rs', 'tests']))
        for name, cwd, command in suites:
            proc = subprocess.run([sys.executable, *command], cwd=root/cwd, env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
            if name == 'cards':
                card_lock.unlink(missing_ok=True)  # fixture-created lock only
            output = proc.stdout.replace(str(Path.home()), '/path/to/user').replace(sandbox, '<temporary-test-home>')
            results.append(dict(suite=name, cwd=cwd, command=['python', *command], exit_code=proc.returncode, output=output))
            print(f'{name}: exit={proc.returncode}\n{output}')
    report = dict(python=sys.version, compiled_in_memory=compiled,
                  core_api_tests_requested=bool(args.hermes_source), results=results)
    (root/'test-results.json').write_text(json.dumps(report, indent=2)+'\n')
    return int(any(item['exit_code'] for item in results))


if __name__ == '__main__':
    raise SystemExit(main())

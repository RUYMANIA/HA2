"""Explicit stdlib-only suite. Never import HA setup or contact services.

An empty package namespace resolves the *real* pure modules by their normal
names without executing custom_components/ha2_notifications/__init__.py.
This is not an HA compatibility shim, and does not test HA classes or guards.
"""
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True


def forbid_external_effects(event, args):
    if event in {'socket.connect', 'socket.bind', 'subprocess.Popen', 'os.system'}:
        raise RuntimeError('External effect forbidden in the offline suite: ' + event)


def main():
    sys.addaudithook(forbid_external_effects)
    for name, path in (
        ('custom_components', ROOT / 'custom_components'),
        ('custom_components.ha2_notifications', ROOT / 'custom_components/ha2_notifications'),
    ):
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    groups = {
        'backend': ['test_engine', 'test_review_gates', 'test_cron', 'test_activity'],
        'proactive_backend': ['test_scheduler', 'test_coordinator', 'test_native_capability',
                              'test_ownership', 'test_activity_log'],
        'contract': ['test_compat'],
        'offline': ['test_short_opener'],
    }
    for directory in groups:
        sys.path.insert(0, str(ROOT / 'tests' / directory))
    suite = unittest.TestSuite()
    for names in groups.values():
        for name in names:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
    # Assert unique IDs: helper imports must not inflate the reported case count.
    def cases(item):
        if isinstance(item, unittest.TestSuite):
            for child in item:
                yield from cases(child)
        else:
            yield item
    ids = [case.id() for case in cases(suite)]
    if len(ids) != len(set(ids)):
        raise RuntimeError('Duplicate test IDs in explicit suite')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())

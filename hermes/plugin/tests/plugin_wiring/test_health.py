"""Health must reach the administrator without leaking upstream fields."""
import asyncio
import json
from pathlib import Path
import runpy
import tempfile
import unittest

FIXTURE=runpy.run_path(str(Path(__file__).with_name('test_plugin.py')))

class HealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_bounded_runtime_health_is_exposed_and_private_fields_dropped(self):
        class Observer(FIXTURE['Observer']):
            async def status(self):
                return dict(source_health='ok',ha_verified=True,catalog_count=12,ledger='ok',catalog='cached',token='PRIVATE_UPSTREAM',body='PRIVATE_BODY')
        with tempfile.TemporaryDirectory(prefix='ha2-health-') as directory:
            ctx=FIXTURE['Context'](); observer=Observer()
            FIXTURE['load']().register_bridge(ctx,lambda:observer,state_path=Path(directory)/'private/enabled.json')
            handler=ctx.commands['ha2-notifications']
            try:
                await handler('start')
                text=await handler('status'); actual=json.loads(text)
                self.assertEqual(actual.get('source_health'),'ok')
                self.assertIs(actual.get('ha_verified'),True)
                self.assertEqual(actual.get('catalog_count'),12)
                self.assertEqual(actual.get('ledger'),'ok')
                self.assertEqual(actual.get('catalog'),'cached')
                self.assertNotIn('PRIVATE',text)
            finally:
                await handler('stop')

if __name__=='__main__':unittest.main()

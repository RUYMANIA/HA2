"""Servicio de conversación aislado; sin cambiar STT/TTS existentes."""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
for line in (ROOT / 'provider.env').read_text().splitlines():
    key, sep, value = line.partition('=')
    if sep:
        os.environ[key] = value
values = {}
for line in Path('/path/to/user/.hermes/.env').read_text().splitlines():
    key, sep, value = line.partition('=')
    if sep:
        values[key.strip()] = value.strip().strip('"').strip("'")
os.environ['HERMES_HA_HOST'] = '127.0.0.1'
os.environ['HERMES_HA_PORT'] = '18765'
os.environ['HERMES_API_URL'] = 'http://192.0.2.10:8642'
os.environ['HERMES_API_TOKEN'] = values['API_SERVER_KEY']
os.environ['HERMES_API_SESSION_KEY'] = 'xiaozhi-assist-test'
os.environ['HERMES_HA_TEMP_DIR'] = '/path/to/user/.hermes/cache/scratch'
sys.path.insert(0, str(ROOT / 'provider'))
sys.path.insert(0, str(ROOT))
from hermes_ha_provider import cli
from ui_timing_runtime import wrap_app_factory
cli.create_app = wrap_app_factory(cli.create_app)
cli.main()

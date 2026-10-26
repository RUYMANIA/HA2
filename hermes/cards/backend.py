"""On-demand Xiaozhi cards coordinator; no daemon or HA configuration changes."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
import uuid


class CardError(Exception):
    """A safe, public machine-readable reason (never upstream exception text)."""
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def validate_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{32}', value):
        raise CardError('invalid_request_id')
    return value


def validate_text(value: str, limit: int, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise CardError('invalid_' + name)
    try:
        value.encode('utf-8', errors='strict')
    except UnicodeError:
        raise CardError('invalid_' + name) from None
    if any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise CardError('invalid_' + name)
    return value


def resolve_pipeline(choice, listing: dict) -> dict:
    pipelines = listing.get('pipelines', [])
    if choice in (None, 'preferred', 'unknown', 'unavailable'):
        matches = [p for p in pipelines if p.get('id') == listing.get('preferred_pipeline')]
    else:
        # HA's installed AssistPipelineSelect uses the pipeline NAME, not its id.
        matches = [p for p in pipelines if p.get('name') == choice]
    if len(matches) != 1:
        raise CardError('pipeline_unresolved')
    return dict(matches[0])


def tts_payload(pipeline: dict, text: str) -> dict:
    if not pipeline.get('tts_engine'):
        raise CardError('tts_unavailable')
    options = {'preferred_format': 'wav', 'preferred_sample_rate': 48000,
               'preferred_sample_channels': 1, 'preferred_sample_bytes': 2}
    if pipeline.get('tts_voice'):
        options['voice'] = pipeline['tts_voice']
    # HA merges entity default_options itself; do not overwrite or invent them.
    return {'engine_id': pipeline['tts_engine'], 'message': text, 'cache': True,
            'language': pipeline.get('tts_language') or pipeline.get('language'),
            'options': options}


def audio_url(result: dict, config: dict) -> str:
    from urllib.parse import urlsplit
    # Pin the actual LAN HA origin. Never pass a proxy localhost/remote URL to Ball.
    origin = config.get('internal_url', '')
    try:
        parsed = urlsplit(origin)
        if (parsed.scheme != 'http' or parsed.hostname != '192.0.2.10'
                or parsed.port != 8123 or parsed.username or parsed.password
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
            raise ValueError
        path = result['path']
        part = urlsplit(path)
        if (part.scheme or part.netloc or part.fragment
                or not re.fullmatch(r'/api/tts_proxy/[A-Za-z0-9_.-]+', path)
                or len('http://192.0.2.10:8123' + path) > 384
                or '..' in part.path or any(ord(c) < 33 for c in path)):
            raise ValueError
        return 'http://192.0.2.10:8123' + path
    except (KeyError, ValueError, TypeError):
        raise CardError('unsafe_audio_url') from None


def weather_text(state: dict) -> str:
    from datetime import datetime
    condition = state.get('state')
    if not condition or condition in ('unknown', 'unavailable'):
        raise CardError('weather_unavailable')
    stamp = state.get('last_updated', '')
    try:
        dt = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise CardError('weather_timestamp_unavailable') from None
    from zoneinfo import ZoneInfo
    # Compact 5-line layout for the actual round screen, not a raw ISO/API dump.
    conditions = {'clear-night':'Despejado', 'cloudy':'Nublado', 'exceptional':'Tiempo adverso',
        'fog':'Niebla', 'hail':'Granizo', 'lightning':'Tormenta',
        'lightning-rainy':'Tormenta y lluvia', 'partlycloudy':'Intervalos nubosos',
        'pouring':'Lluvia intensa', 'rainy':'Lluvia', 'snowy':'Nieve',
        'snowy-rainy':'Aguanieve', 'sunny':'Soleado', 'windy':'Viento',
        'windy-variant':'Viento y nubes'}
    fields = [conditions.get(str(condition), 'Estado: ' + str(condition))]
    attrs = state.get('attributes') or {}
    for key, label, unit_key in (
        ('temperature', 'Temperatura', 'temperature_unit'),
        ('humidity', 'Humedad', '%'), ('wind_speed', 'Viento', 'wind_speed_unit')):
        value = attrs.get(key)
        unit = '%' if unit_key == '%' else attrs.get(unit_key)
        if value is not None and unit and type(value) in (int, float):
            import math
            if math.isfinite(value):
                number = format(value, 'g').replace('.', ',')
                fields.append(f'{label}: {number} {unit}')
    # This is HA's state-update time, not a claim about a live weather observation.
    local = dt.astimezone(ZoneInfo('Etc/UTC'))
    fields.append('Datos HA ' + local.strftime('%d/%m %H:%M'))
    return '\n'.join(fields)


@dataclass(frozen=True)
class CardRequest:
    kind: str
    title: str
    text: str
    seconds: int = 30
    speak: bool = False
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self):
        if self.kind not in ('reminder', 'weather', 'result', 'notice'):
            raise CardError('invalid_kind')
        validate_text(self.title, 120, 'title')
        validate_text(self.text, 4000, 'text')
        if len(self.text.encode('utf-8')) > 4096:
            raise CardError('invalid_text')
        validate_id(self.request_id)
        if type(self.seconds) is not int or not 2 <= self.seconds <= 120:
            raise CardError('invalid_ttl')
        if type(self.speak) is not bool:
            raise CardError('invalid_speak')

    @property
    def ttl_ms(self) -> int:
        return self.seconds * 1000


import asyncio
import time

TERMINAL_FAILURES = {'dismissed', 'expired', 'interrupted', 'rejected'}


def outcome(request_id='', *, ok=False, displayed=False, played=False, reason='', status=None):
    result = {'ok': ok, 'request_id': request_id, 'displayed': displayed,
              'played': played, 'reason': reason, 'text_delivered': displayed}
    if status:
        # Explicit allow-list; no URLs, title/text, upstream errors or credentials.
        for key in ('state', 'visible', 'audio', 'generation', 'truncated'):
            if key in status:
                result[key] = status[key]
    return result


class Coordinator:
    """Injected adapters keep all device effects outside the coordination policy."""
    def __init__(self, device, tts=None, clock=time.monotonic, sleep=asyncio.sleep):
        self.device, self.tts, self.clock, self.sleep = device, tts, clock, sleep

    async def _wait(self, predicate, deadline, reason):
        while self.clock() < deadline:
            try:
                value = await asyncio.wait_for(predicate(), timeout=max(.001, deadline-self.clock()))
            except asyncio.TimeoutError:
                raise CardError(reason) from None
            if self.clock() >= deadline:
                raise CardError(reason)
            if value:
                return value
            await self.sleep(min(.1, max(0, deadline - self.clock())))
        raise CardError(reason)

    async def _owned(self, request_id, generation=None):
        status = await self.device.status()
        if status['request_id'] != request_id:
            raise CardError('producer_conflict')
        if generation is not None and status['generation'] != generation:
            raise CardError('generation_conflict')
        if status['state'] in TERMINAL_FAILURES:
            raise CardError(status['state'])
        if status['audio'] in ('failed', 'cancelled'):
            raise CardError('audio_' + status['audio'])
        return status

    async def _cleanup(self, request_id, generation):
        # Check before writing and compare-id again in firmware (atomic ownership).
        current = await self.device.status()
        if (current['request_id'] == request_id and current['generation'] == generation
                and (current.get('card_active', False) or current['visible']
                     or current['state'] in ('pending','shown','playing')
                     or current['audio'] in ('playing', 'waiting'))):
            await self.device.call('card_cancel', {'request_id': request_id})
            async def cancelled():
                current = await self.device.status()
                if current['request_id'] != request_id:
                    raise CardError('producer_conflict')
                return current if (current['state'] in ('dismissed','expired','interrupted')
                    and not current['visible'] and current['audio'] not in ('playing','waiting')) else None
            await self._wait(cancelled, self.clock() + 2, 'cleanup_unconfirmed')

    async def show(self, request: CardRequest, idle_wait=30, playback_timeout=120):
        displayed = played = False
        generation = None
        touched = False
        leave_visible = False
        status = None
        reason = ''
        suppressed = False
        deadline = self.clock() + request.seconds  # End-to-end freshness, includes synthesis/busy wait.
        try:
            if not 0 <= idle_wait <= 60 or not 0 < playback_timeout <= 120:
                raise CardError('invalid_timeout')
            await self.device.verify()  # MAC, exact actions + argument types, typed sensors.
            url = None
            night_reader = getattr(self.device, 'night_active', None)
            suppressed = bool(await night_reader()) if request.speak and night_reader else False
            if request.speak and not suppressed:
                if self.tts is None:
                    raise CardError('tts_unavailable')
                url = await asyncio.wait_for(self.tts.prepare(request), timeout=max(.01, deadline-self.clock()))
            if self.clock() >= deadline:
                raise CardError('expired')
            if not await self.device.idle():
                await self._wait(self.device.idle, min(deadline, self.clock() + idle_wait), 'busy')
            baseline = await self.device.status()
            if (baseline.get('card_active', False) or baseline['visible']
                    or baseline['state'] in ('pending','shown','playing')
                    or baseline['audio'] in ('playing', 'waiting')):
                raise CardError('card_busy')
            if self.clock() >= deadline:
                raise CardError('expired')
            touched = True
            await self.device.call('card_show', {
                'request_id': request.request_id, 'title': request.title, 'body': request.text,
                'kind': request.kind, 'ttl_ms': max(1, int((deadline-self.clock())*1000)),
                'audio_expected': request.speak})
            async def shown():
                current = await self.device.status()
                if current['request_id'] == request.request_id:
                    if current['state'] in TERMINAL_FAILURES:
                        raise CardError(current['state'])
                    if current['generation'] <= baseline['generation']:
                        raise CardError('stale_ack')
                    return current if current['visible'] and current['state'] == 'shown' else None
                if current['generation'] > baseline['generation']:
                    raise CardError('producer_conflict')
                return None
            status = await self._wait(shown, min(deadline, self.clock()+3), 'show_unconfirmed')
            generation = status['generation']
            displayed = True
            suppressed = suppressed or status.get('audio') == 'suppressed'
            if not request.speak or suppressed:
                leave_visible = True  # Device owns TTL; no daemon needed.
            else:
                if not await self.device.idle():
                    raise CardError('busy')
                await self._owned(request.request_id, generation)
                if self.clock() >= deadline:
                    raise CardError('expired')
                await self.device.call('card_play', {'request_id': request.request_id, 'url': url})
                async def completed():
                    current = await self._owned(request.request_id, generation)
                    return current if (current['state'] == 'audio_done' and current['audio'] == 'done') or current['audio'] == 'suppressed' else None
                status = await self._wait(completed, min(deadline, self.clock()+playback_timeout), 'playback_timeout')
                suppressed = status['audio'] == 'suppressed'
                played = not suppressed
                leave_visible = True  # Reading time remains owned by the local TTL after speech.
        except CardError as exc:
            reason = 'expired' if exc.reason == 'busy' and self.clock() >= deadline else exc.reason
        except asyncio.TimeoutError:
            reason = 'expired' if self.clock() >= deadline else 'timeout'
        except asyncio.CancelledError:
            reason = 'interrupted'
        except Exception:
            reason = 'transport_error'
        finally:
            if touched and not leave_visible:
                try:
                    latest = await self.device.status()
                    if (latest['request_id'] == request.request_id and
                            (generation is None or latest['generation'] == generation)):
                        status = latest
                    # A lost ack may still have shown OUR card. Never cancel another producer.
                    if generation is None:
                        current = await self.device.status()
                        if current['request_id'] == request.request_id:
                            generation = current['generation']
                    if generation is not None:
                        await self._cleanup(request.request_id, generation)
                except Exception:
                    reason = reason or 'cleanup_unconfirmed'
        if suppressed and not reason:
            status = dict(status or {}, audio='suppressed')
        return outcome(request.request_id, ok=not reason, displayed=displayed, played=played,
                       reason=reason or ('night_mode' if suppressed else ''), status=status)

    async def cancel(self, request_id):
        try:
            validate_id(request_id)
            await self.device.verify()
            current = await self.device.status()
            if current['request_id'] != request_id:
                raise CardError('request_id_mismatch')
            await self._cleanup(request_id, current['generation'])
            current = await self.device.status()
            if current['request_id'] != request_id or current['visible']:
                raise CardError('cancel_unconfirmed')
            return outcome(request_id, ok=True, status=current)
        except CardError as exc:
            return outcome(request_id, reason=exc.reason)
        except Exception:
            return outcome(request_id, reason='transport_error')


import json
from pathlib import Path

EXPECTED_MAC = '00:00:00:00:00:00'
ACTION_SCHEMA = {
    'card_show': {'request_id': 'STRING', 'title': 'STRING', 'body': 'STRING',
                  'kind': 'STRING', 'ttl_ms': 'INT', 'audio_expected': 'BOOL'},
    'card_play': {'request_id': 'STRING', 'url': 'STRING'},
    'card_cancel': {'request_id': 'STRING'},
}


def parse_status(raw):
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(value, dict):
            raise ValueError
        keys = ('request_id', 'state', 'visible', 'audio', 'reason', 'generation', 'truncated')
        if not all(k in value for k in keys):
            raise ValueError
        if value['request_id']:
            validate_id(value['request_id'])
        elif value['request_id'] != '' or value['state'] not in ('idle','rejected'):
            raise ValueError
        if value['state'] not in {'idle','pending','shown','playing','audio_done', *TERMINAL_FAILURES}:
            raise ValueError
        if value['audio'] not in ('none','waiting','playing','done','cancelled','failed','suppressed'):
            raise ValueError
        if any(type(value[k]) is not bool for k in ('visible','truncated')):
            raise ValueError
        if type(value['generation']) is not int or value['generation'] < 0:
            raise ValueError
        if not isinstance(value['reason'], str):
            raise ValueError
        return {k: value[k] for k in keys}
    except (ValueError, KeyError, TypeError, CardError):
        raise CardError('invalid_card_status') from None


class NativeDevice:
    """Native API state subscription only; NEVER subscribes voice-assistant audio."""
    def __init__(self, client, ha):
        self.client, self.ha = client, ha
        self.states = {}
        self.services = {}
        self.entities = []
        self.verified = False
        self.connected = True

    def on_state(self, state):
        # Numeric entity keys can collide across domains. A LightState is not a player!
        self.states[(type(state).__name__, state.key)] = state

    async def verify(self):
        if self.verified:
            return
        info = await self.client.device_info()
        if info.mac_address.upper() != EXPECTED_MAC:
            raise CardError('identity_mismatch')
        self.entities, services = await self.client.list_entities_services()
        for name, schema in ACTION_SCHEMA.items():
            matches = [s for s in services if s.name == name]
            if len(matches) != 1:
                raise CardError('missing_card_actions')
            service = matches[0]
            actual = {a.name: getattr(a.type, 'name', None) for a in service.args}
            if actual != schema or len(service.args) != len(schema):
                raise CardError('action_schema_mismatch')
            self.services[name] = service
        def sensor(kind, suffix):
            matches = [e for e in self.entities if type(e).__name__ == kind and
                       (e.object_id == suffix or e.object_id.endswith('_' + suffix))]
            if len(matches) != 1:
                raise CardError('missing_card_sensors')
            return matches[0].key
        self.status_key = sensor('TextSensorInfo', 'card_status')
        self.active_key = sensor('BinarySensorInfo', 'card_active')
        self.client.subscribe_states(self.on_state)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if ('TextSensorState', self.status_key) in self.states and ('BinarySensorState', self.active_key) in self.states:
                break
            await asyncio.sleep(.05)
        else:
            raise CardError('initial_state_timeout')
        self.verified = True
        try:
            await self.status()
        except Exception:
            self.verified = False
            raise

    async def status(self):
        if not self.connected or not self.verified:
            raise CardError('device_unavailable')
        state = self.states.get(('TextSensorState', self.status_key))
        active = self.states.get(('BinarySensorState', self.active_key))
        if state is None or active is None or getattr(state,'missing_state',False) or getattr(active,'missing_state',False):
            raise CardError('card_state_unavailable')
        value = parse_status(state.state)
        if type(active.state) is not bool:
            raise CardError('invalid_card_status')
        value['card_active'] = active.state
        return value

    async def night_active(self):
        # Optional cost-saving gate; firmware remains authoritative at admission/play.
        matches = [e for e in self.entities if type(e).__name__ == 'TextSensorInfo' and
                   (e.object_id == 'ui_night' or e.object_id.endswith('_ui_night'))]
        if len(matches) != 1:
            return False
        state = self.states.get(('TextSensorState', matches[0].key))
        try:
            return json.loads(state.state).get('night_active') in (True, 1)
        except (AttributeError, TypeError, ValueError):
            return False

    async def idle(self):
        # HA's existing connection is the real mic owner. Read its satellite/player states,
        # never call announce/stop, pipeline/run, or subscribe_voice_assistant here.
        if not self.connected or not self.verified or self.ha is None:
            raise CardError('device_unavailable')
        satellite, player = await asyncio.gather(
            self.ha.rest('/api/states/assist_satellite.example_satellite_assist_satellite'),
            self.ha.rest('/api/states/media_player.example_satellite'))
        return satellite.get('state') == 'idle' and player.get('state') in ('idle','off')

    async def call(self, action, data):
        if not self.verified or not self.connected or action not in self.services:
            raise CardError('device_not_verified')
        schema = ACTION_SCHEMA[action]
        if set(data) != set(schema):
            raise CardError('action_data_mismatch')
        for key, kind in schema.items():
            required = {'STRING':str,'INT':int,'BOOL':bool}[kind]
            if type(data[key]) is not required:
                raise CardError('action_data_mismatch')
        validate_id(data['request_id'])
        # Send is NOT delivery. Coordinator awaits matching state acknowledgement.
        await self.client.execute_service(self.services[action], data)


class HATTS:
    def __init__(self, ha):
        self.ha = ha

    async def prepare(self, request):
        selection, listing, config = await asyncio.gather(
            self.ha.rest('/api/states/select.example_satellite_assistant'),
            self.ha.ws('assist_pipeline/pipeline/list'), self.ha.rest('/api/config'))
        pipeline = resolve_pipeline(selection.get('state'), listing)
        # URL allocation is lazy; no pipeline run or satellite action and no proxy GET.
        result = await self.ha.rest('/api/tts_get_url', tts_payload(pipeline, request.text))
        return audio_url(result, config)


class LocalLock:
    """Bounded advisory file lock; keep inode in place to avoid unlink races."""
    def __init__(self, path, timeout=2):
        self.path, self.timeout, self.fd = Path(path), timeout, None

    def __enter__(self):
        import fcntl
        import os
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return self
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise CardError('lock_busy')
                    time.sleep(min(.05, max(0, deadline-time.monotonic())))
        except Exception as exc:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
            if isinstance(exc, CardError):
                raise
            raise CardError('lock_failed') from None

    def __exit__(self, *args):
        import fcntl
        import os
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
            self.fd = None


ROOT = Path(__file__).resolve().parent
HA_ENV = Path('/path/to/user/.hermes/.env')
SECRETS = Path('/path/to/user/.hermes/projects/xiaozhi-ball-esphome/secrets.yaml')
WS_PYTHON = '/path/to/user/.hermes/tools/xiaozhi-backup/venv/bin/python'

# Isolated read-only WS bridge: credentials pass through private stdin, not argv/env/logs.
# Importing assist-local/ha_api.py in the ESPHome venv would require websockets there.
WS_BRIDGE = r'''
import json, sys
from websockets.sync.client import connect
try:
    data = json.load(sys.stdin)
    if data['command'] != 'assist_pipeline/pipeline/list':
        raise ValueError()
    base = data['base']
    url = ('wss' + base[5:] if base.startswith('https:') else 'ws' + base[4:]) + '/api/websocket'
    with connect(url, open_timeout=5, close_timeout=1) as sock:
        if json.loads(sock.recv(timeout=5))['type'] != 'auth_required':
            raise ValueError()
        sock.send(json.dumps({'type':'auth','access_token':data['token']}))
        if json.loads(sock.recv(timeout=5))['type'] != 'auth_ok':
            raise ValueError()
        sock.send(json.dumps({'id':1,'type':data['command']}))
        while True:
            response = json.loads(sock.recv(timeout=10))
            if response.get('id') == 1 and response.get('type') == 'result':
                if not response.get('success'):
                    raise ValueError()
                print(json.dumps(response['result']))
                break
except Exception:
    sys.exit(1)
'''


class HAClient:
    def __init__(self, base, token, opener=None, ws_python=WS_PYTHON):
        from urllib.parse import urlsplit
        from urllib.request import build_opener, HTTPRedirectHandler
        parsed = urlsplit(base)
        if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1','localhost','192.0.2.10')
                or parsed.port != 8123 or parsed.username or parsed.password
                or parsed.path not in ('','/') or parsed.query or parsed.fragment):
            raise CardError('unsafe_ha_origin')
        self.base, self.token, self.ws_python = base.rstrip('/'), token, ws_python
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        self.opener = opener or build_opener(NoRedirect()).open

    @classmethod
    def from_local(cls):
        try:
            values = {}
            for line in HA_ENV.read_text().splitlines():
                key, sep, value = line.partition('=')
                if sep and key.strip() in ('HASS_URL','HASS_TOKEN'):
                    values[key.strip()] = value.strip().strip('\"').strip("'")
            return cls(values['HASS_URL'], values['HASS_TOKEN'])
        except CardError:
            raise
        except Exception:
            raise CardError('ha_credentials_unavailable') from None

    async def rest(self, path, data=None):
        from urllib.request import Request
        allowed = {'/api/config', '/api/states/select.example_satellite_assistant',
                   '/api/states/weather.example', '/api/states/media_player.example_satellite',
                   '/api/states/assist_satellite.example_satellite_assist_satellite'}
        if not ((data is None and path in allowed) or (data is not None and path == '/api/tts_get_url')):
            raise CardError('ha_route_not_allowed')
        def request_json():
            request = Request(self.base + path,
                data=None if data is None else json.dumps(data, ensure_ascii=False).encode('utf-8'),
                headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'},
                method='GET' if data is None else 'POST')
            try:
                with self.opener(request, timeout=10) as response:
                    payload = response.read(1048577)
                    if len(payload) > 1048576:
                        raise ValueError()
                    value = json.loads(payload)
                    if not isinstance(value, dict) or 'error' in value:
                        raise ValueError()
                    return value
            except Exception:
                raise CardError('tts_error' if data is not None else 'ha_read_failed') from None
        return await asyncio.to_thread(request_json)

    async def ws(self, command):
        if command != 'assist_pipeline/pipeline/list':
            raise CardError('ha_route_not_allowed')
        process = None
        try:
            process = await asyncio.create_subprocess_exec(self.ws_python, '-I', '-c', WS_BRIDGE,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL)
            payload = json.dumps({'base':self.base,'token':self.token,'command':command}).encode()
            stdout, _ = await asyncio.wait_for(process.communicate(payload), timeout=15)
            if process.returncode != 0 or len(stdout) > 1048576:
                raise ValueError()
            result = json.loads(stdout)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except asyncio.CancelledError:
            raise
        except Exception:
            raise CardError('ha_ws_failed') from None
        finally:
            if process is not None and process.returncode is None:
                process.kill()
                await process.wait()


from contextlib import asynccontextmanager


@asynccontextmanager
async def create_runtime(args):
    try:
        import aioesphomeapi
        import yaml
        secrets = yaml.safe_load(SECRETS.read_text())
        psk = secrets['api_encryption_key']
        ha = HAClient.from_local()
        client = aioesphomeapi.APIClient(args.host, 6053, noise_psk=psk,
            expected_mac=EXPECTED_MAC.replace(':','').lower(), client_info='HermesCards', provide_time=False)
    except CardError:
        raise
    except Exception:
        raise CardError('runtime_dependencies_unavailable') from None
    device = NativeDevice(client, ha)
    async def disconnected(expected):
        device.connected = False
    try:
        await asyncio.wait_for(client.connect(on_stop=disconnected, login=True, log_errors=False), timeout=10)
        yield device, ha
    finally:
        device.connected = False
        try:
            await asyncio.wait_for(client.disconnect(), timeout=3)
        except Exception:
            pass


def parser():
    import argparse
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise CardError('invalid_arguments')
    result = Parser(description='Tarjetas bajo demanda; sin daemon ni cambios en Home Assistant.')
    result.add_argument('--host', default='xiaozhi-ball-v2.local')
    result.add_argument('--lock-timeout', type=float, default=2)
    commands = result.add_subparsers(dest='command', required=True, parser_class=Parser)
    show = commands.add_parser('show')
    show.add_argument('--kind', choices=('reminder','weather','result','notice'), default='notice')
    show.add_argument('--title', required=True)
    show.add_argument('--text', required=True)
    weather = commands.add_parser('weather')
    weather.add_argument('--title', default='El tiempo')
    for item in (show, weather):
        item.add_argument('--seconds', type=int, default=30)
        item.add_argument('--speak', action='store_true')
        item.add_argument('--idle-wait', type=float, default=30)
        item.add_argument('--playback-timeout', type=float, default=120)
    cancel = commands.add_parser('cancel')
    cancel.add_argument('--request-id', required=True)
    commands.add_parser('status')
    return result


def validate_args(args):
    import math
    if not math.isfinite(args.lock_timeout) or not 0 <= args.lock_timeout <= 10:
        raise CardError('invalid_lock_timeout')
    if not re.fullmatch(r'[A-Za-z0-9.-]{1,253}', args.host):
        raise CardError('invalid_host')
    if args.command == 'cancel':
        validate_id(args.request_id)
    if args.command in ('show','weather'):
        if not 0 <= args.idle_wait <= 60 or not 0 < args.playback_timeout <= 120:
            raise CardError('invalid_timeout')
        # Weather text comes ONLY from HA, but validate all user input before connection.
        return CardRequest(args.kind if args.command == 'show' else 'weather', args.title,
                           args.text if args.command == 'show' else 'pending', args.seconds, args.speak)
    return None


async def run_command(args, request, runtime_factory):
    async with runtime_factory(args) as (device, ha):
        coordinator = Coordinator(device, HATTS(ha) if ha else None)
        if args.command == 'cancel':
            return await coordinator.cancel(args.request_id)
        if args.command == 'status':
            await device.verify()
            status = await device.status()
            return outcome(status['request_id'], ok=True, status=status)
        if args.command == 'weather':
            from dataclasses import replace
            text = weather_text(await ha.rest('/api/states/weather.example'))
            request = replace(request, text=text)
        return await coordinator.show(request, idle_wait=args.idle_wait,
                                      playback_timeout=args.playback_timeout)


async def run_with_signals(args, request, runtime_factory):
    import signal
    loop, task = asyncio.get_running_loop(), asyncio.current_task()
    installed = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        previous = signal.getsignal(sig)
        try:
            loop.add_signal_handler(sig, task.cancel)
            installed[sig] = previous
        except (NotImplementedError, RuntimeError, ValueError):
            pass  # Main-thread Unix CLI supports it; injected non-main callers may not.
    try:
        return await run_command(args, request, runtime_factory)
    finally:
        for sig, previous in installed.items():
            loop.remove_signal_handler(sig)
            signal.signal(sig, previous)


def exit_code(result):
    if result['ok']:
        return 0
    reason = result['reason']
    if reason.startswith('invalid_') or reason in ('unsafe_audio_url','unsafe_ha_origin'):
        return 2
    if reason in ('busy','card_busy','lock_busy','lock_failed'):
        return 3
    if reason in ('interrupted','producer_conflict','generation_conflict','request_id_mismatch','dismissed'):
        return 4
    if reason in ('expired','playback_timeout'):
        return 5
    if reason == 'rejected':
        return 6
    return 1


def main(argv=None, runtime_factory=None):
    import logging
    # This entrypoint emits one allow-listed JSON object, never raw native/HTTP exceptions.
    logging.disable(logging.CRITICAL)
    request = None
    try:
        args = parser().parse_args(argv)
        request = validate_args(args)
        with LocalLock(ROOT / '.backend.lock', args.lock_timeout):
            result = asyncio.run(run_with_signals(args, request, runtime_factory or create_runtime))
    except CardError as exc:
        result = outcome(request.request_id if request else '', reason=exc.reason)
    except (KeyboardInterrupt, asyncio.CancelledError):
        result = outcome(request.request_id if request else '', reason='interrupted')
    except Exception:
        result = outcome(request.request_id if request else '', reason='transport_error')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code(result)


if __name__ == '__main__':
    raise SystemExit(main())

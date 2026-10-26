"""Gateway-owned HA² runtime. No registration, tasks, credentials or sockets at import."""
from __future__ import annotations
import asyncio
import importlib.util
import inspect
import os
from pathlib import Path
import stat
import uuid
from urllib.parse import urlsplit, urlunsplit

from .bridge import Bridge, CatalogReader, LedgerReader, PreviewReader, JSONCheckpointStore


class PublicError(RuntimeError):
    """Only fixed public error codes cross this boundary."""


class HAClient:
    ALLOWED = frozenset({'ha2_notifications/get', 'ha2_notifications/cron_sync', 'ha2_notifications/cron_result'})

    def __init__(self, url, token, *, timeout=15):
        parts = urlsplit(url)
        if parts.scheme not in ('http', 'https') or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
            raise PublicError('invalid_ha_url')
        self._url = urlunsplit(('wss' if parts.scheme == 'https' else 'ws', parts.netloc, parts.path.rstrip('/')+'/api/websocket', '', ''))
        self._token = token
        self.timeout = timeout
        self._session = None
        self._ws = None
        self._lock = asyncio.Lock()
        self._id = 0
        self.closed = False
        self.verified = False

    async def _disconnect(self):
        self.verified = False
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    async def _connect(self):
        import aiohttp
        if self.closed: raise PublicError('client_closed')
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        self._ws = await self._session.ws_connect(self._url, heartbeat=20, autoping=True, max_msg_size=2_000_000)
        if (await self._ws.receive_json()).get('type') != 'auth_required':
            raise PublicError('ha_auth_failed')
        await self._ws.send_json({'type':'auth', 'access_token':self._token})
        if (await self._ws.receive_json()).get('type') != 'auth_ok':
            raise PublicError('ha_auth_failed')
        # Version guard applies after every reconnect, before any sync/result.
        snapshot = await self._rpc('ha2_notifications/get', {})
        if not isinstance(snapshot, dict) or snapshot.get('version') not in ('0.2.0', '0.3.0') or not isinstance(snapshot.get('hermes_cron'), dict):
            raise PublicError('ha_version_mismatch')
        self.verified = True

    async def _rpc(self, kind, payload):
        self._id += 1
        ident = self._id
        await self._ws.send_json({'id':ident, 'type':kind, **payload})
        frame = await self._ws.receive_json()
        if not isinstance(frame, dict) or type(frame.get('id')) is not int or frame['id'] != ident or frame.get('type') != 'result':
            raise PublicError('ha_protocol_error')
        if frame.get('success') is not True:
            raise PublicError('ha_command_failed')
        result = frame.get('result')
        if not isinstance(result, dict): raise PublicError('ha_protocol_error')
        return result

    async def call(self, kind, **payload):
        if kind not in self.ALLOWED or 'id' in payload or 'type' in payload:
            raise PublicError('ha_command_forbidden')
        async with self._lock:
            try:
                async with asyncio.timeout(self.timeout):
                    if self._ws is None or self._ws.closed:
                        await self._disconnect()
                        await self._connect()
                    return await self._rpc(kind, payload)
            except asyncio.CancelledError:
                await self._disconnect()
                raise
            except PublicError:
                await self._disconnect()
                raise
            except Exception:
                await self._disconnect()
                raise PublicError('ha_unavailable') from None

    async def close(self):
        self.closed = True
        await self._disconnect()
        if self._session is not None:
            await self._session.close()
            self._session = None
        self._token = None


def _private_directory(path):
    if not path.exists(): path.mkdir(mode=0o700)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise PublicError('unsafe_runtime_directory')


def _prepare(home, client):
    # No network/credentials before BOTH readers validate. Preview never opened.
    catalog = CatalogReader(home)
    ledger = LedgerReader(home, allow_auxiliary=True)
    jobs = catalog.read()
    ledger.read()
    directory = home/'ha2-notifications'
    _private_directory(directory)
    identity_store = JSONCheckpointStore(directory/'source.json')
    identity = identity_store.load()
    if identity is None:
        identity = {'version':1, 'source_instance':uuid.uuid4().hex}
        identity_store.save(identity)
    if not isinstance(identity, dict) or set(identity) != {'version','source_instance'} or identity['version'] != 1:
        raise PublicError('invalid_source_identity')
    source = identity['source_instance']
    if not isinstance(source, str) or len(source) != 32 or any(c not in '0123456789abcdef' for c in source):
        raise PublicError('invalid_source_identity')
    bridge = Bridge(home, source, client, checkpoint_store=JSONCheckpointStore(directory/'checkpoint.json'))
    bridge.catalog_reader = catalog
    bridge.ledger_reader = ledger
    bridge.preview_reader = PreviewReader(home, allow_auxiliary=True)
    return bridge, len(jobs)


def _credentials(home):
    url, token = os.environ.get('HASS_URL'), os.environ.get('HASS_TOKEN')
    if not url or not token:
        # Reuse current private helper; never persist a second credential copy.
        helper = home/'projects/assist-local/ha_api.py'
        info = helper.stat()
        if info.st_uid != os.getuid() or info.st_mode & 0o022 or helper.is_symlink():
            raise PublicError('unsafe_credential_helper')
        spec = importlib.util.spec_from_file_location('_ha2_private_credentials', helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fallback_url, fallback_token = module.credentials()
        url, token = url or fallback_url, token or fallback_token
    if not isinstance(url, str) or not isinstance(token, str) or not token:
        raise PublicError('ha_credentials_unavailable')
    return url, token


class RuntimeObserver:
    def __init__(self, bridge, client, count=0):
        self.bridge = bridge
        self.client = client
        self._task = None
        self._stopped = False
        self._source_health = 'ok'
        self._count = count

    async def run(self):
        if self._task is not None or self._stopped:
            raise PublicError('observer_already_owned')
        self._task = asyncio.current_task()
        try:
            delay = 1
            while not self._stopped:
                try:
                    # Prevent false online sync if a previously valid ledger disappears.
                    jobs, _ = await asyncio.gather(asyncio.to_thread(self.bridge.catalog_reader.read), asyncio.to_thread(self.bridge.ledger_reader.read))
                    self._source_health = 'ok'; self._count = len(jobs)
                    await self.bridge.tick()
                    report = self.bridge.last_report
                    if report.get('ledger') == 'unavailable' or report.get('catalog') == 'unavailable':
                        self._source_health = 'unavailable'
                    delay = min(delay*2,30) if any(value == 'unavailable' for value in report.values()) else 1
                except asyncio.CancelledError: raise
                except Exception:
                    self._source_health = 'unavailable'
                    delay = min(delay*2,30)
                await asyncio.sleep(delay)
        finally:
            self._stopped = True
            await self.client.close()

    async def status(self):
        report = self.bridge.last_report
        return {'version':'0.2.0', 'profile':'default', 'running':self._task is not None and not self._task.done() and not self._stopped,
                'source_health':self._source_health, 'ha_verified':self.client.verified,
                'catalog_count':self._count, 'ledger':report.get('ledger','unknown'),
                'catalog':report.get('catalog','unknown')}

    async def stop(self):
        self._stopped = True
        task = self._task
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await self.client.close()


def make_factory(home=None, credential_provider=None):
    """Capture approved default home now; async factory opens resources only at start."""
    if home is None:
        from hermes_cli.config import get_hermes_home
        home = get_hermes_home()
    home = Path(home).expanduser().resolve(strict=True)
    # No other profile may be selected, including symlink aliases resolving there.
    if 'profiles' in home.parts:
        raise PublicError('profile_not_approved')

    async def factory():
        client = None
        try:
            bridge, count = await asyncio.to_thread(_prepare, home, None)
            if credential_provider is None:
                credentials = await asyncio.to_thread(_credentials, home)
            elif inspect.iscoroutinefunction(credential_provider):
                credentials = await credential_provider()
            else:
                credentials = await asyncio.to_thread(credential_provider)
                if inspect.isawaitable(credentials): credentials = await credentials
            url, token = credentials
            client = HAClient(url, token)
            bridge.client = client
            return RuntimeObserver(bridge, client, count)
        except asyncio.CancelledError:
            if client is not None: await client.close()
            raise
        except Exception:
            if client is not None: await client.close()
            raise PublicError('runtime_preflight_failed') from None
    return factory

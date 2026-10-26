"""Gateway-loop wiring only; no imports or execution of the observer at registration."""
from __future__ import annotations

import asyncio
import inspect
import json
import os
from pathlib import Path
import tempfile

COMMAND = 'ha2-notifications'
OWNER_ID = '1000000'
VERSION = '0.2.0'


def _authorized(source, platform=None):
    # None is reserved for trusted in-process startup, never a public wire parameter.
    if source is None:
        return platform in (None, '', 'local')
    from gateway.config import Platform
    from gateway.session import SessionSource
    if not isinstance(source, SessionSource) or source.is_bot:
        return False
    if source.profile not in (None, '', 'default'):
        return False
    if platform not in (None, '', source.platform.value):
        return False
    if source.platform == Platform.LOCAL:
        # execute_command already requires authorize_local_source; remote login subjects are
        # auth:v1:[...] and cannot equal the private Unix peer principal.
        return source.user_id == f'uid:{os.getuid()}'
    return source.platform == Platform.TELEGRAM and source.user_id == OWNER_ID


class BridgeController:
    def __init__(self, ctx, factory, state_path):
        self.ctx = ctx
        self.factory = factory
        self.path = Path(state_path)
        self.task = None
        self.observer = None
        self.loop = None
        self.lock = None
        self.closed = False
        self.failure = False
        self.enabled = self._read_enabled()

    def _read_enabled(self):
        try:
            if self.path.is_symlink():
                return False
            data = json.loads(self.path.read_text(encoding='utf-8'))
            return data == {'version': 1, 'enabled': True}
        except (OSError, ValueError):
            return False

    def _persist(self, enabled):
        parent = self.path.parent
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if parent.is_symlink() or self.path.is_symlink():
            raise ValueError('unsafe_state_path')
        os.chmod(parent, 0o700)
        fd, name = tempfile.mkstemp(prefix='.enabled-', dir=parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump({'version': 1, 'enabled': enabled}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        self.enabled = enabled

    async def _serve(self, observer):
        try:
            await observer.run()
        except asyncio.CancelledError:
            raise
        except Exception:
            self.failure = True
        finally:
            try:
                await observer.stop()
            except Exception:
                self.failure = True

    def unload(self):
        # Plugin unload happens in a loader worker, not necessarily the gateway loop.
        self.closed = True
        if self.loop is not None and not self.loop.is_closed() and self.task is not None:
            self.loop.call_soon_threadsafe(self.task.cancel)
        # Preserve enabled: force reload/restart is not an explicit user stop.

    async def command(self, raw_args, *, source=None, platform=None, session_id='', session_key=''):
        if getattr(self.ctx, 'profile_name', None) != 'default' or not _authorized(source, platform):
            return json.dumps({'error': 'permission_denied'})
        action = raw_args.strip()
        if action not in ('start', 'status', 'stop', 'resume'):
            return json.dumps({'error': 'invalid_action'})
        if self.closed:
            return json.dumps({'error': 'unloaded'})
        loop = asyncio.get_running_loop()
        if self.loop is None:
            self.loop = loop
            self.lock = asyncio.Lock()
        if self.loop is not loop:
            return json.dumps({'error': 'wrong_runtime_loop'})
        async with self.lock:
            try:
                if action == 'stop':
                    self._persist(False)
                    if self.task is not None and not self.task.done():
                        self.task.cancel()
                        try:
                            await self.task
                        except asyncio.CancelledError:
                            pass
                elif action in ('start', 'resume'):
                    if action == 'start':
                        self._persist(True)
                    if self.enabled and (self.task is None or self.task.done()):
                        observer = self.factory()
                        if inspect.isawaitable(observer):
                            observer = await observer
                        if not all(inspect.iscoroutinefunction(getattr(observer, key, None))
                                   for key in ('run', 'status', 'stop')):
                            raise TypeError('invalid_observer')
                        self.observer = observer
                        self.failure = False
                        coro = self._serve(observer)
                        try:
                            self.task = self.ctx.spawn_task(coro, name='ha2-notifications:observer')
                        except Exception:
                            coro.close()
                            await observer.stop()
                            raise
                        # Enter _serve before another command/unload can cancel the task.
                        await asyncio.sleep(0)
                if action == 'status' and self.observer is not None:
                    # Exercise the real status API, but never echo arbitrary upstream data.
                    health = await self.observer.status()
                    # Explicitly validate bounded diagnostics; never forward arbitrary fields.
                    self.public_health = {}
                    if isinstance(health, dict):
                        if health.get('source_health') in ('ok', 'unavailable'):
                            self.public_health['source_health'] = health['source_health']
                        if type(health.get('ha_verified')) is bool:
                            self.public_health['ha_verified'] = health['ha_verified']
                        if type(health.get('catalog_count')) is int and 0 <= health['catalog_count'] <= 512:
                            self.public_health['catalog_count'] = health['catalog_count']
                        for key in ('ledger', 'catalog'):
                            if health.get(key) in ('ok', 'unknown', 'cached', 'unavailable'):
                                self.public_health[key] = health[key]
            except Exception:
                self.failure = True
                return json.dumps({'error': 'bridge_unavailable', **self.snapshot()})
            return json.dumps(self.snapshot())

    def snapshot(self):
        return {'version': VERSION, 'profile': 'default', 'enabled': self.enabled,
                'running': self.task is not None and not self.task.done(),
                'failed': self.failure, **getattr(self, 'public_health', {})}


class AsyncCallAdapter:
    """Adapt the parent's call(type, **payload) without putting credentials in commands.

    A synchronous client must support use from a worker thread; it must not own an aiohttp
    session bound to the gateway loop. Native async clients are awaited in their owning loop.
    """
    def __init__(self, client):
        self._client = client

    async def call(self, kind, **payload):
        method = self._client.call
        if inspect.iscoroutinefunction(method):
            return await method(kind, **payload)
        result = await asyncio.to_thread(method, kind, **payload)
        return await result if inspect.isawaitable(result) else result


async def startup_hook(event_type, context, *, resolve=None):
    """Legacy hook helper: resolve the CURRENT registered handler, which closes over its ctx.

    Wire only to gateway:startup in a private profile's HOOK.yaml/handler.py. No ctx is
    supplied by the legacy hook event; never construct a second context or factory here.
    """
    if event_type != 'gateway:startup':
        return None
    if resolve is None:
        from hermes_cli.plugins import get_plugin_command_handler
        resolve = get_plugin_command_handler
    handler = resolve(COMMAND)
    if handler is None:
        return {'error': 'bridge_not_registered'}
    # This is a trusted internal call, not a user-supplied RPC source value.
    return await handler('resume', source=None)


def register_bridge(ctx, factory, *, state_path=None):
    """factory() -> observer or awaitable[observer]; observer.run/status/stop are async.

    Registration is synchronous and loop-free. Only the registered async handler starts tasks.
    state_path must name a file inside a dedicated private plugin state directory.
    """
    if state_path is None:
        from hermes_cli.config import get_hermes_home
        state_path = get_hermes_home() / 'ha2-notifications' / 'enabled.json'
    controller = BridgeController(ctx, factory, state_path)
    ctx.register_command(COMMAND, controller.command, description='HA² observer administration',
                         args_hint='start|status|stop', argument_mode='text')
    ctx.on_unload(controller.unload)
    return controller

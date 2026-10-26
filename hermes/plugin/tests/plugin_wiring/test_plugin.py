import asyncio
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, '/path/to/user/.hermes/hermes-agent')

def load():
    path = ROOT / 'hermes_bridge/plugin.py'
    assert path.exists(), 'plugin wrapper has not been implemented'
    spec = importlib.util.spec_from_file_location('wiring_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class Context:
    profile_name = 'default'
    def __init__(self): self.commands = {}; self.tasks = []; self.cleanup = []
    def register_command(self, name, handler, **kwargs): self.commands[name] = handler
    def on_unload(self, callback): self.cleanup.append(callback)
    def spawn_task(self, coro, *, name):
        task = asyncio.get_running_loop().create_task(coro, name=name)
        self.tasks.append(task)
        return task

class Observer:
    def __init__(self): self.runs = 0; self.stops = 0
    async def run(self):
        self.runs += 1
        await asyncio.Event().wait()
    async def stop(self): self.stops += 1
    async def status(self): return {'DO_NOT_LEAK': 'private upstream body'}

def test_registration_without_loop_and_real_async_lifecycle(tmp_path):
    mod = load(); ctx = Context(); observer = Observer()
    controller = mod.register_bridge(ctx, lambda: observer, state_path=tmp_path/'private/enabled.json')
    assert not ctx.tasks
    assert asyncio.iscoroutinefunction(ctx.commands['ha2-notifications'])
    async def scenario():
        handler = ctx.commands['ha2-notifications']
        result = json.loads(await handler('start', source=None))
        await asyncio.sleep(0)
        assert result['running'] and observer.runs == 1
        await handler('start', source=None)
        assert len(ctx.tasks) == 1
        assert 'DO_NOT_LEAK' not in await handler('status', source=None)
        result = json.loads(await handler('stop', source=None))
        assert not result['running'] and not result['enabled']
        assert observer.stops == 1
    asyncio.run(scenario())
    assert controller is not None
    assert os.stat(tmp_path/'private/enabled.json').st_mode & 0o777 == 0o600
    assert os.stat(tmp_path/'private').st_mode & 0o777 == 0o700

def test_startup_uses_current_registered_context_and_private_enabled_resume(tmp_path):
    mod = load(); ctx = Context(); first = Observer(); path = tmp_path/'private/enabled.json'
    mod.register_bridge(ctx, lambda: first, state_path=path)
    async def scenario():
        await ctx.commands['ha2-notifications']('start')
        # Loader worker cleanup safely returns cancellation to the task's owning loop.
        await asyncio.to_thread(ctx.cleanup[0])
        await asyncio.sleep(0)
        await asyncio.gather(*ctx.tasks, return_exceptions=True)
        assert first.stops == 1 and json.loads(path.read_text())['enabled']
        second_ctx = Context(); second = Observer()
        async def factory(): return second
        mod.register_bridge(second_ctx, factory, state_path=path)
        # Resolver called on every hook invocation, never an old context closure.
        lookup = lambda name: second_ctx.commands.get(name)
        await mod.startup_hook('session:start', {}, resolve=lookup)
        assert not second_ctx.tasks
        await mod.startup_hook('gateway:startup', {'platforms':['homeassistant']}, resolve=lookup)
        assert second.runs == 1
        await second_ctx.commands['ha2-notifications']('stop')
        third_ctx = Context()
        mod.register_bridge(third_ctx, lambda: Observer(), state_path=path)
        await mod.startup_hook('gateway:startup', {}, resolve=lambda name: third_ctx.commands.get(name))
        assert not third_ctx.tasks
    asyncio.run(scenario())


def test_real_primary_invocation_owner_and_unix_subject_not_display_name(tmp_path):
    mod = load()
    from hermes_cli.plugin_command_dispatch import invoke_plugin_command
    from gateway.config import Platform
    from gateway.session import SessionSource
    ctx = Context(); mod.register_bridge(ctx, lambda: Observer(), state_path=tmp_path/'p/state.json')
    handler = ctx.commands['ha2-notifications']
    async def scenario():
        for source, platform in [
            (SessionSource(Platform.TELEGRAM, '1', user_id='2', user_name='1000000'), 'telegram'),
            (SessionSource(Platform.DISCORD, '1', user_id='1000000'), 'discord'),
            (SessionSource(Platform.LOCAL, '1', user_id='auth:v1:["local","","uid:501"]'), 'local'),
            (SessionSource(Platform.TELEGRAM, '1', user_id='1000000'), 'discord'),
            (SimpleNamespace(platform=Platform.TELEGRAM, user_id='1000000'), 'telegram'),
        ]:
            result = await invoke_plugin_command(handler, 'start', source=source, platform=platform)
            assert json.loads(result)['error'] == 'permission_denied'
        assert not ctx.tasks
        source = SessionSource(Platform.LOCAL, '1', user_id=f'uid:{os.getuid()}')
        result = await invoke_plugin_command(handler, 'start', source=source, platform='local')
        assert json.loads(result)['running']
        await handler('stop', source=source, platform='local')
        source = SessionSource(Platform.TELEGRAM, '1', user_id='1000000')
        assert json.loads(await handler('start', source=source, platform='telegram'))['running']
        await handler('stop')
    asyncio.run(scenario())


def test_transport_adapts_sync_off_loop_and_async_without_credentials_in_repr():
    mod = load()
    import threading
    loop_thread = threading.get_ident()
    class Sync:
        def call(self, kind, **payload):
            assert threading.get_ident() != loop_thread
            return {'kind':kind, **payload}
    class Async:
        async def call(self, kind, **payload):
            assert threading.get_ident() == loop_thread
            return {'kind':kind, **payload}
    async def scenario():
        for client in (Sync(), Async()):
            wrapped = mod.AsyncCallAdapter(client)
            assert await wrapped.call('ha2_notifications/get') == {'kind':'ha2_notifications/get'}
    asyncio.run(scenario())


def test_failures_are_sanitized_and_profile_is_fail_closed(tmp_path):
    mod = load(); ctx = Context()
    def failing_factory(): raise RuntimeError('SECRET HASS_TOKEN SHOULD NEVER LEAK')
    mod.register_bridge(ctx, failing_factory, state_path=tmp_path/'p/state.json')
    async def scenario():
        reply = await ctx.commands['ha2-notifications']('start')
        assert 'SECRET' not in reply and json.loads(reply)['error'] == 'bridge_unavailable'
        ctx.profile_name = 'other'
        assert json.loads(await ctx.commands['ha2-notifications']('status'))['error'] == 'permission_denied'
        ctx.profile_name = 'default'
        assert json.loads(await ctx.commands['ha2-notifications']('start garbage'))['error'] == 'invalid_action'
    asyncio.run(scenario())


def test_legacy_hook_loader_and_registry_await_real_handler(tmp_path):
    from gateway.hooks import _load_hook_dir, HookRegistry
    mod = load(); ctx = Context()
    mod.register_bridge(ctx, lambda: Observer(), state_path=tmp_path/'state/enabled.json')
    hookdir = tmp_path/'hook'; hookdir.mkdir()
    (hookdir/'HOOK.yaml').write_text('name: ha2-wiring-test\nevents: ["gateway:startup"]\n')
    (hookdir/'handler.py').write_text(
        'async def handle(event_type, context):\n'
        '    return await helper(event_type, context, resolve=resolve)\n')
    name, events, handle, description = _load_hook_dir(hookdir)
    handle.__globals__['helper'] = mod.startup_hook
    handle.__globals__['resolve'] = lambda name: ctx.commands.get(name)
    registry = HookRegistry()
    registry._handlers[events[0]] = [handle]
    async def scenario():
        await ctx.commands['ha2-notifications']('start')
        await ctx.commands['ha2-notifications']('stop')
        assert json.loads((await registry.emit_collect('gateway:startup', {}))[0])['running'] is False
    asyncio.run(scenario())

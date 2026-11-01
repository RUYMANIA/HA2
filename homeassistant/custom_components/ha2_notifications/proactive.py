"""Proactive policy and injected transport contract (PROACTIVE-CONTRACT v1)."""
from __future__ import annotations
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import random
import re
from uuid import uuid4

DEFAULT_CONFIG = dict(enabled=False, all_day=True, start='09:00', end='21:00', interval_minutes=60, mode='cue')
CAPABILITY_KEYS = ('full_agent', 'session_binding', 'transcript_only', 'native_listen')
INTENT_IDS = ('saludo', 'curiosidad', 'conversacion_ligera', 'pausa_creativa', 'cotidiano')


def validate_config(raw):
    if not isinstance(raw, dict) or set(raw) != set(DEFAULT_CONFIG):
        raise ValueError('invalid_config')
    if type(raw['enabled']) is not bool or type(raw['all_day']) is not bool:
        raise ValueError('invalid_config')
    for field in ('start', 'end'):
        if not isinstance(raw[field], str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', raw[field], flags=re.ASCII):
            raise ValueError('invalid_config')
    interval = raw['interval_minutes']
    if type(interval) is not int or not 30 <= interval <= 1440 or interval % 30 or raw['mode'] not in ('cue', 'voice'):
        raise ValueError('invalid_config')
    if not raw['all_day'] and raw['start'] == raw['end']:
        raise ValueError('invalid_config')
    return deepcopy(raw)


def in_window(config, now, tz):
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        return False
    if config['all_day']:
        return True
    clock = now.astimezone(tz).strftime('%H:%M')
    start, end = config['start'], config['end']
    return start <= clock < end if start < end else clock >= start or clock < end


def sample_due(config, now, rng):
    interval = config['interval_minutes'] * 60
    return now + timedelta(seconds=rng.uniform(.75 * interval, min(1.25 * interval, 86400)))


def choose_intent(recent, rng):
    return rng.choice([item for item in INTENT_IDS if item not in recent] or list(INTENT_IDS))


class ClosedTransport:
    """Unimplemented section-4 adapter. Never claims installed capabilities.

    Real adapters implement capabilities/readiness/generate/present/cancel/close.
    generate and present must call synchronous valid() at every effect boundary;
    readiness must fail closed on night unknown, menu, human/audio/card activity.
    Prepared is opaque except request_id. Only cancel(request_id) may stop work.
    """
    async def capabilities(self):
        return dict.fromkeys(CAPABILITY_KEYS, False)

    async def readiness(self):
        return dict(ready=False, reason='unavailable')

    async def generate(self, request_id, intent_id, config, valid):
        raise RuntimeError('unavailable')

    async def present(self, prepared, config, valid):
        return dict(accepted=False, completed=False, reason='unavailable')

    async def cancel(self, request_id):
        pass

    async def close(self):
        pass


def empty_state():
    return dict(revision=0, config=deepcopy(DEFAULT_CONFIG), epoch=0,
                next_due_at=None, claim=None, last_request_id=None, recent_intents=[],
                status='disabled', reason=None, last_attempt_at=None,
                last_completed_at=None)


class Coordinator:
    """Single supervised encounter; shares Engine's durable lock and Store.

    create_task is HA's async_create_background_task, injected for isolation.
    tick never awaits model generation/presentation. No second scheduler/daemon.
    """
    def __init__(self, engine, transport, create_task, rng=None):
        self.engine, self.transport, self.create_task = engine, transport, create_task
        self.rng = rng if rng is not None else random.SystemRandom()
        self.task = None
        self.closed = False
        self.ready = False
        self.caps = dict.fromkeys(CAPABILITY_KEYS, False)
        self.owner = None

    def snapshot(self):
        state = self.engine.data.get('proactive', empty_state())
        return dict(revision=state['revision'], config=deepcopy(state['config']),
                    runtime={key: state.get(key) for key in ('status', 'reason', 'next_due_at', 'last_attempt_at', 'last_completed_at')},
                    capabilities=deepcopy(self.caps))

    async def initialize(self):
        async with self.engine.lock:
            data = deepcopy(self.engine.data)
            state = data.setdefault('proactive', empty_state())
            try:
                validate_config(state['config'])
            except (ValueError, TypeError):
                # Malformed persisted proactive config must never enable effects.
                state = data['proactive'] = empty_state()
            due = state.get('next_due_at')
            now = self.engine.clock()
            try:
                missed = due is None or datetime.fromisoformat(due) <= now
            except (ValueError, TypeError):
                missed = True
            if state['claim'] or missed:
                state['epoch'] += 1
                state['claim'] = None
                state['next_due_at'] = sample_due(state['config'], now, self.rng).isoformat() if state['config']['enabled'] else None
                state['status'] = 'scheduled' if state['config']['enabled'] else 'disabled'
                state['reason'] = None
            if data != self.engine.data:
                await self.engine.commit(data)
        await self.refresh()

    async def configure(self, expected_revision, config):
        from .engine import Error
        async with self.engine.lock:
            current = self.engine.data.get('proactive', empty_state())
            if type(expected_revision) is not int or expected_revision != current['revision']:
                raise Error('conflict')
            try:
                config = validate_config(config)
            except (ValueError, TypeError):
                raise Error('invalid_config') from None
            if config == current['config']:
                return
            data = deepcopy(self.engine.data)
            state = data.setdefault('proactive', empty_state())
            if current['claim']:
                self.activity(data, current['claim']['request_id'], 'cancelled', 'configuration_changed')
            state.update(config=config, revision=current['revision'] + 1,
                         epoch=current['epoch'] + 1, claim=None,
                         next_due_at=sample_due(config, self.engine.clock(), self.rng).isoformat() if config['enabled'] else None,
                         status='scheduled' if config['enabled'] else 'disabled', reason=None)
            await self.engine.commit(data)
        await self.cancel_active()

    def policy_valid(self):
        state = self.engine.data.get('proactive', empty_state())
        return (not self.closed and state['config']['enabled'] and not self.engine.data['paused']
                and not self.engine.data['queue'] and in_window(state['config'], self.engine.clock(), self.engine.tz))

    def valid(self, owner=None):
        owner = self.owner if owner is None else owner
        state = self.engine.data.get('proactive', empty_state())
        return bool(owner and owner == self.owner and self.ready and self.policy_valid()
                    and state['epoch'] == owner['epoch'] and state['claim'] == owner)

    async def refresh(self):
        self.ready = False
        try:
            caps = await self.transport.capabilities()
            self.caps = {key: caps.get(key) is True for key in CAPABILITY_KEYS} if isinstance(caps, dict) else dict.fromkeys(CAPABILITY_KEYS, False)
            readiness = await self.transport.readiness()
            config = self.engine.data.get('proactive', empty_state())['config']
            supported = all(self.caps[key] for key in ('full_agent', 'session_binding', 'native_listen')) and (config['mode'] != 'cue' or self.caps['transcript_only'])
            self.ready = bool(supported and isinstance(readiness, dict) and readiness.get('ready') is True)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.caps = dict.fromkeys(CAPABILITY_KEYS, False)

    async def tick(self):
        if self.closed:
            return
        state = self.engine.data.get('proactive', empty_state())
        if not state['config']['enabled']:
            await self.cancel_active()
            return
        await self.refresh()
        if self.task is not None and not self.task.done():
            if not self.valid():
                await self.cancel_active()
            return
        self.task = None
        async with self.engine.lock:
            state = self.engine.data.get('proactive', empty_state())
            due = state['next_due_at']
            now = self.engine.clock()
            if not due or datetime.fromisoformat(due) > now:
                return
            data = deepcopy(self.engine.data)
            state = data['proactive']
            state['next_due_at'] = sample_due(state['config'], now, self.rng).isoformat()
            if not (self.ready and self.policy_valid()):
                state.update(status='skipped', reason='guard_blocked')
                self.activity(data, None, 'skipped', 'guard_blocked')
                await self.engine.commit(data)
                return
            intent = choose_intent(state['recent_intents'], self.rng)
            owner = dict(request_id=uuid4().hex, epoch=state['epoch'])
            state.update(claim=owner, last_request_id=owner['request_id'], last_attempt_at=now.isoformat(), status='generating', reason=None)
            state['recent_intents'] = (state['recent_intents'] + [intent])[-3:]
            self.activity(data, owner['request_id'], 'claimed')
            self.activity(data, owner['request_id'], 'generating')
            await self.engine.commit(data)  # Must complete before task/model side effect.
            self.owner = owner
            self.task = self.create_task(self.encounter(deepcopy(owner), intent, deepcopy(state['config'])), 'HA² proactive encounter')

    def activity(self, data, request_id, status, reason=None):
        # Construct metadata only, never accept prepared content or transport reasons.
        self.engine.log(data, dict(request_id=request_id, rule_id=None, source='proactive',
                                  rule=dict(name='Invitación proactiva', kind='proactive')),
                        status, reason)

    async def update(self, owner, status, reason=None, completed=False, *, terminal=True, accepted=False):
        async with self.engine.lock:
            state = self.engine.data.get('proactive', empty_state())
            if state['claim'] != owner or state['epoch'] != owner['epoch']:
                return False
            data = deepcopy(self.engine.data)
            if terminal:
                data['proactive'].update(status=status, reason=reason, claim=None)
            if accepted:
                self.activity(data, owner['request_id'], 'accepted')
            self.activity(data, owner['request_id'], status, reason)
            if completed:
                data['proactive']['last_completed_at'] = self.engine.clock().isoformat()
            await self.engine.commit(data)
            return True

    async def encounter(self, owner, intent, config):
        valid = lambda: self.valid(owner)
        try:
            await self.refresh()
            if not self.valid():
                await self.update(owner, 'skipped', 'guard_blocked')
                return
            prepared = await self.transport.generate(owner['request_id'], intent, config, valid)
            request_id = prepared.get('request_id') if isinstance(prepared, dict) else getattr(prepared, 'request_id', None)
            await self.refresh()
            if request_id != owner['request_id'] or not self.valid():
                await self.update(owner, 'skipped', 'guard_blocked')
                return
            if not await self.update(owner, 'presenting', terminal=False):
                return
            result = await self.transport.present(prepared, config, valid)
            completed = isinstance(result, dict) and result.get('accepted') is True and result.get('completed') is True and self.valid()
            accepted = isinstance(result, dict) and result.get('accepted') is True
            await self.update(owner, 'completed' if completed else 'skipped', None if completed else 'not_completed', completed, accepted=accepted)
        except asyncio.CancelledError:
            raise
        except Exception:
            try:
                await self.update(owner, 'failed', 'unavailable')
            except Exception:
                pass  # Durable ambiguous claim recovers without replay.
        finally:
            try:
                await self.transport.cancel(owner['request_id'])
            except Exception:
                pass
            if self.owner == owner:
                self.owner = None

    async def cancel_active(self):
        task, owner = self.task, self.owner
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        try:
            if owner:
                await self.update(owner, 'cancelled', 'guard_blocked')
        finally:
            self.task = None
            self.owner = None

    async def close(self):
        if self.closed:
            return
        self.closed = True
        self.ready = False
        try:
            await self.cancel_active()
        except Exception:
            pass  # Keep an ambiguous durable claim; boot recovery never replays.
        finally:
            try:
                await self.transport.close()
            except Exception:
                pass

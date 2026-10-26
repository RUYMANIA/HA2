#!/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python -I
"""One-shot encrypted UI metadata; no playback, microphone or HA dependency."""
from __future__ import annotations
import asyncio
import json
import logging
import os
from pathlib import Path
import stat
import sys

SECRETS = Path('/path/to/user/.hermes/projects/xiaozhi-ball-esphome/secrets.yaml')
MAC = '00:00:00:00:00:00'
HOST = '192.0.2.10'


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError('invalid_input')
    kind = payload.get('kind', 'tts')
    allowed = {'kind', 'message', 'duration_ms'} if kind == 'tts' else {'kind', 'message'}
    if kind not in ('tts', 'stt') or set(payload) - allowed:
        raise ValueError('invalid_input')
    message = payload.get('message')
    if (not isinstance(message, str) or not message.strip() or '\x00' in message
            or len(message.encode('utf-8', errors='strict')) > 4096):
        raise ValueError('invalid_input')
    result = {'kind': kind, 'message': message}
    if kind == 'tts':
        duration = payload.get('duration_ms')
        if type(duration) is not int or not 1 <= duration <= 600000:
            raise ValueError('invalid_duration')
        result['duration_ms'] = duration
    return result


def outcome(**kwargs):
    result = dict(ok=False, supported=False, unsupported=False, schema_mismatch=False,
                  identity_mismatch=False, sent=False, matched=False, match_known=False,
                  invalid=False, timeout=False, failed=False)
    result.update(kwargs)
    return result


async def dispatch(client, payload, *, probe=False):
    info = await client.device_info()
    if info.mac_address.upper() != MAC:
        return outcome(identity_mismatch=True)
    _, services = await client.list_entities_services()  # fresh descriptor, no cached key
    name = 'ui_stt_text' if payload['kind'] == 'stt' else 'ui_tts_timing'
    matches = [s for s in services if s.name == name]
    if not matches:
        return outcome(unsupported=True)
    schema = {'message': 'STRING'}
    if payload['kind'] == 'tts':
        schema['duration_ms'] = 'INT'
    if (len(matches) != 1 or len(matches[0].args) != len(schema)
            or {a.name: getattr(a.type, 'name', None) for a in matches[0].args} != schema):
        return outcome(schema_mismatch=True)
    if probe:
        return outcome(ok=True, supported=True)
    # The installed aioesphomeapi execute_service is async; awaiting is the send.
    await client.execute_service(matches[0], {k: payload[k] for k in schema})
    # Native action has no acknowledgement of UI ownership/match. Never claim it.
    return outcome(ok=True, supported=True, sent=True)


def private_psk():
    import yaml
    fd = os.open(SECRETS, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        details = os.fstat(stream.fileno())
        if (not stat.S_ISREG(details.st_mode) or details.st_uid != os.getuid()
                or stat.S_IMODE(details.st_mode) != 0o600):
            raise ValueError('unsafe_secret_file')
        psk = yaml.safe_load(stream)['api_encryption_key']
    if not isinstance(psk, str) or not psk:
        raise ValueError('invalid_secret')
    return psk


async def run(payload, *, probe=False):
    import aioesphomeapi
    client = aioesphomeapi.APIClient(HOST, 6053, noise_psk=private_psk(),
        expected_mac=MAC.replace(':', '').lower(), client_info='Hermes UITiming', provide_time=False)
    try:
        await client.connect(login=True, log_errors=False)
        return await dispatch(client, payload, probe=probe)
    finally:
        try:
            await asyncio.wait_for(client.disconnect(), .15)
        except Exception:
            pass


def main():
    logging.disable(logging.CRITICAL)
    try:
        if sys.argv[1:] not in ([], ['--probe']):
            raise ValueError('invalid_input')
        # Escaped Unicode can require six source bytes per code unit.
        raw = sys.stdin.buffer.read(32769)
        if len(raw) > 32768:
            raise ValueError('invalid_input')
        payload = validate(json.loads(raw))
        budget = .9 if payload['kind'] == 'stt' else 2.1
        result = asyncio.run(asyncio.wait_for(run(payload, probe='--probe' in sys.argv), budget))
    except asyncio.TimeoutError:
        result = outcome(timeout=True)
    except (ValueError, UnicodeError, KeyError, TypeError):
        result = outcome(invalid=True)
    except Exception:
        result = outcome(failed=True)
    print(json.dumps(result, separators=(',', ':')))
    return 0  # result is numeric/boolean, never a raw exception


if __name__ == '__main__':
    raise SystemExit(main())

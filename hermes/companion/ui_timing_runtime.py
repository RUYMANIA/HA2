"""Optional, fail-open UI timing companion for the isolated Ball provider."""
from __future__ import annotations
import asyncio
import json
import os
from pathlib import Path
import struct
import tempfile
import time

MAX_AUDIO = 128 * 1024 * 1024


def pcm_duration_ms(audio: bytes) -> int:
    """Count actual integer PCM frames, including streaming data-to-EOF headers."""
    if not 12 <= len(audio) <= MAX_AUDIO or audio[:4] != b'RIFF' or audio[8:12] != b'WAVE':
        raise ValueError('invalid_pcm')
    riff_size = struct.unpack_from('<I', audio, 4)[0]
    if riff_size not in (0, 0xffffffff, len(audio) - 8):
        raise ValueError('truncated_riff')
    offset, fmt, data_size = 12, None, None
    while offset < len(audio):
        if offset + 8 > len(audio):
            raise ValueError('truncated_chunk')
        tag, size = struct.unpack_from('<4sI', audio, offset)
        offset += 8
        if tag == b'data' and size in (0, 0xffffffff):
            size = len(audio) - offset
        if offset + size > len(audio):
            raise ValueError('truncated_chunk')
        if tag == b'fmt ':
            if fmt is not None or size < 16:
                raise ValueError('invalid_format')
            fmt = struct.unpack_from('<HHIIHH', audio, offset)
        elif tag == b'data':
            if data_size is not None:
                raise ValueError('ambiguous_data')
            data_size = size
        offset += size + (size & 1)
    if offset != len(audio) or fmt is None or data_size is None:
        raise ValueError('invalid_chunks')
    kind, channels, rate, byte_rate, align, bits = fmt
    if (kind != 1 or not 1 <= channels <= 8 or not 8000 <= rate <= 192000
            or bits not in (8, 16, 24, 32) or align != channels * (bits // 8)
            or byte_rate != rate * align or not data_size or data_size % align):
        raise ValueError('invalid_pcm_format')
    frames = data_size // align
    if frames * 1000 < rate or frames > rate * 600:
        raise ValueError('invalid_duration')
    return (frames * 1000 + rate // 2) // rate


SCRATCH = Path('/path/to/user/.hermes/cache/scratch')
UI_ROOT = Path('/path/to/user/.hermes/projects/xiaozhi-ui-v3')
PYTHON = '/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python'
DIAGNOSTIC = SCRATCH / 'ball-ui-timing-private' / 'timing.json'


def valid_message(message):
    return (isinstance(message, str) and bool(message.strip()) and '\x00' not in message
            and len(message.encode('utf-8', errors='strict')) <= 4096)


class TimingRuntime:
    """Delegation preserves provider selection and all original call arguments."""
    tts_budget = 2.65  # plus kill/reap reserve, under 3s total
    stt_budget = 1.15  # plus kill/reap reserve, under 1.5s total

    def __init__(self, original, *, sender=None, diagnostic=DIAGNOSTIC):
        self._original = original
        self._sender = sender or send_metadata
        self._diagnostic = diagnostic
        self._stats = dict(tts_count=0, measured_count=0, sent_count=0,
                           failure_count=0, total_ms=0, duration_ms=0, quality=0,
                           matched_count=0, match_known=False, stt_count=0,
                           stt_sent_count=0, stt_total_ms=0, unsupported_count=0)

    def __getattr__(self, name):
        return getattr(self._original, name)

    def _record(self):
        if self._diagnostic is None:
            return
        temporary = None
        try:
            target = Path(self._diagnostic)
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if target.parent.stat().st_mode & 0o077:
                return
            fd, temporary = tempfile.mkstemp(prefix='.timing-', dir=target.parent)
            with os.fdopen(fd, 'w') as stream:
                json.dump(self._stats, stream)
            os.replace(temporary, target)
        except Exception:
            pass
        finally:
            if temporary:
                try:
                    Path(temporary).unlink(missing_ok=True)
                except OSError:
                    pass

    async def _tts_metadata(self, text, audio, mime):
        if not valid_message(text):
            raise ValueError('invalid_message')
        duration, quality = await measure_duration(audio, mime)
        self._stats.update(duration_ms=duration, quality=quality)
        self._stats['measured_count'] += 1
        sent = await self._sender(text, duration)
        for flag in ('failed','invalid','timeout','schema_mismatch','identity_mismatch'):
            self._stats['helper_'+flag] = bool(sent.get(flag))
        self._stats['failure_count'] += any(self._stats['helper_'+flag] for flag in ('failed','invalid','timeout','schema_mismatch','identity_mismatch'))
        self._stats['sent_count'] += bool(sent.get('sent'))
        self._stats['unsupported_count'] += bool(sent.get('unsupported'))

    async def synthesize(self, *args, **kwargs):
        result = await self._original.synthesize(*args, **kwargs)
        started = time.monotonic()
        self._stats['tts_count'] += 1
        self._stats.update(duration_ms=0, quality=0)
        try:
            text = args[0] if args else kwargs['text']
            await asyncio.wait_for(self._tts_metadata(text, *result), self.tts_budget)
        except Exception:
            self._stats['failure_count'] += 1
        finally:
            self._stats['total_ms'] = round((time.monotonic() - started) * 1000)
            self._record()
        return result

    async def infer(self, *args, **kwargs):
        # Proactive generation and first-turn handoff carry internal context, not
        # microphone transcription. Never send these prompts to the Ball UI.
        if kwargs.get('bootstrap_session') is True:
            return await self._original.infer(*args, **kwargs)
        started = time.monotonic()
        try:
            messages = args[0] if args else kwargs.get('messages')
            if isinstance(messages, list):
                last = next((m for m in reversed(messages)
                             if isinstance(m, dict) and m.get('role') == 'user'), None)
                if last is not None and valid_message(last.get('content')):
                    self._stats['stt_count'] += 1
                    sent = await asyncio.wait_for(self._sender(last['content'], None), self.stt_budget)
                    self._stats['stt_sent_count'] += bool(sent.get('sent'))
        except Exception:
            self._stats['failure_count'] += 1
        finally:
            self._stats['stt_total_ms'] = round((time.monotonic() - started) * 1000)
            self._record()
        return await self._original.infer(*args, **kwargs)


async def run_process(argv, *, data=None, timeout=2.5):
    """No shell, inherited secrets, stderr logs, or surviving process group."""
    import signal
    env = {'HOME': '/path/to/user', 'TMPDIR': str(SCRATCH),
           'PATH': '/usr/bin:/bin', 'LANG': 'en_US.UTF-8'}
    spawn = asyncio.create_task(asyncio.create_subprocess_exec(
        *argv, stdin=asyncio.subprocess.PIPE if data is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        env=env, start_new_session=True))
    process = None
    try:
        process = await asyncio.shield(spawn)
        async def exchange():
            if data is not None:
                process.stdin.write(data)
                await process.stdin.drain()
                process.stdin.close()
            output = bytearray()
            while True:
                chunk = await process.stdout.read(1025 - len(output))
                if not chunk:
                    break
                output.extend(chunk)
                if len(output) > 1024:
                    raise ValueError('oversized_result')
            await process.wait()
            if process.returncode:
                raise ValueError('process_failed')
            return bytes(output)
        return await asyncio.wait_for(exchange(), timeout)
    finally:
        if process is None:
            process = await spawn
        if process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await process.wait()


def cleanup_expired_audio():
    """Crash leftovers: own private directories only, ten-minute lazy TTL."""
    import shutil
    import stat
    now = time.time()
    for path in SCRATCH.glob('ball-ui-audio-*'):
        try:
            details = path.lstat()
            if (stat.S_ISDIR(details.st_mode) and details.st_uid == os.getuid()
                    and details.st_mode & 0o777 == 0o700 and now - details.st_mtime > 600):
                shutil.rmtree(path)
        except OSError:
            pass


async def measure_duration(audio, mime):
    cleanup_expired_audio()
    if audio[:4] == b'RIFF':
        return pcm_duration_ms(audio), 1
    if (mime not in ('audio/mpeg', 'audio/mp3') or not 4 <= len(audio) <= MAX_AUDIO
            or not (audio[:3] == b'ID3' or (audio[0] == 255 and audio[1] & 224 == 224))
            or not Path('/usr/bin/afconvert').is_file()):
        raise ValueError('unsupported_audio')
    with tempfile.TemporaryDirectory(prefix='ball-ui-audio-', dir=SCRATCH) as directory:
        root = Path(directory)
        os.chmod(root, 0o700)
        source, output = root/'source.mp3', root/'decoded.wav'
        for path in (source, output):
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                if path == source:
                    stream.write(audio)
        await run_process(['/usr/bin/afconvert', '-f', 'WAVE', '-d', 'LEI16',
                           str(source), str(output)], timeout=2.4)
        if output.stat().st_size > MAX_AUDIO:
            raise ValueError('oversized_pcm')
        return pcm_duration_ms(output.read_bytes()), 2


def wrap_app_factory(factory):
    """Install only in run_provider, never the shared provider package/CLI."""
    def create_app(settings, runtime):
        if (settings.host == '127.0.0.1' and settings.port == 18765
                and settings.hermes_api_session_key == 'xiaozhi-assist-test'):
            runtime = TimingRuntime(runtime)
        return factory(settings, runtime)
    return create_app


async def send_metadata(message, duration_ms):
    if not valid_message(message):
        raise ValueError('invalid_message')
    payload = {'kind': 'stt' if duration_ms is None else 'tts', 'message': message}
    if duration_ms is not None:
        payload['duration_ms'] = duration_ms
    raw = await run_process([PYTHON, '-I', str(UI_ROOT/'ui_tts_timing_send.py')],
                            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                            timeout=2.4 if duration_ms is not None else 1.05)
    decoded = json.loads(raw)
    if not isinstance(decoded, dict) or any(type(v) not in (int, bool) for v in decoded.values()):
        raise ValueError('invalid_helper_result')
    return decoded



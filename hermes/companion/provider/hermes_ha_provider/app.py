"""aiohttp application and versioned provider API."""

from __future__ import annotations

import asyncio
import hmac
import json
import math
import os
import shutil
import tempfile
from collections.abc import Awaitable, Callable, Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from aiohttp import web

from .config import Settings
from .runtime import CapabilityUnavailable, HermesRuntime, RuntimeFailure
from .version import __version__

Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


class Runtime(Protocol):
    def capabilities(self) -> dict[str, bool]: ...

    def tts_capabilities(self) -> dict[str, Any]: ...

    async def infer(
        self,
        messages: list[dict[str, str]],
        *,
        conversation_id: str | None = None,
        language: str | None = None,
        bootstrap_session: bool = False,
    ) -> str: ...

    async def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        provider: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        instructions: str | None = None,
    ) -> tuple[bytes, str]: ...

    async def transcribe(self, path: Path) -> tuple[str, str | None]: ...


class ApiError(Exception):
    """An expected, stable API error."""

    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


SETTINGS_KEY = web.AppKey("settings", Settings)
RUNTIME_KEY = web.AppKey("runtime", Runtime)
SEMAPHORE_KEY = web.AppKey("semaphore", asyncio.Semaphore)
TOKEN_DIGEST_KEY = web.AppKey("token_digest", bytes)


def _error_response(code: str, message: str, status: int) -> web.Response:
    return web.json_response({"error": {"code": code, "message": message}}, status=status)


@web.middleware
async def error_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    try:
        response = await handler(request)
    except ApiError as exc:
        response = _error_response(exc.code, exc.message, exc.status)
    except web.HTTPRequestEntityTooLarge:
        response = _error_response("invalid_request", "request body is too large", 413)
    except (json.JSONDecodeError, UnicodeDecodeError):
        response = _error_response("invalid_request", "request body is not valid JSON", 400)
    except CapabilityUnavailable:
        response = _error_response("capability_unavailable", "capability is unavailable", 503)
    except RuntimeFailure:
        response = _error_response("provider_error", "Hermes provider request failed", 502)
    except TimeoutError:
        response = _error_response("timeout", "request timed out", 504)
    except Exception:
        response = _error_response("internal_error", "internal server error", 500)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@web.middleware
async def auth_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    if request.path == "/health":
        return await handler(request)
    header = request.headers.get("Authorization", "")
    scheme, separator, candidate = header.partition(" ")
    supplied = candidate if separator and scheme.lower() == "bearer" else ""
    supplied_digest = sha256(supplied.encode()).digest()
    if not hmac.compare_digest(supplied_digest, request.app[TOKEN_DIGEST_KEY]):
        raise ApiError("unauthorized", "valid bearer authentication is required", 401)
    return await handler(request)


@web.middleware
async def resource_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    if request.path == "/health":
        return await handler(request)
    settings = request.app[SETTINGS_KEY]
    semaphore = request.app[SEMAPHORE_KEY]
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=settings.busy_timeout)
    except TimeoutError as exc:
        raise ApiError("busy", "service is busy", 503) from exc
    try:
        async with asyncio.timeout(settings.request_timeout):
            return await handler(request)
    finally:
        semaphore.release()


def _content_length_guard(request: web.Request, limit: int) -> None:
    length = request.content_length
    if length is not None and length > limit:
        raise ApiError("invalid_request", "request body is too large", 413)


async def _read_json(request: web.Request, limit: int) -> Mapping[str, Any]:
    _content_length_guard(request, limit)
    if request.content_type != "application/json":
        raise ApiError("invalid_request", "Content-Type must be application/json", 415)
    data = await request.content.read(limit + 1)
    if len(data) > limit:
        raise ApiError("invalid_request", "request body is too large", 413)
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ApiError("invalid_request", "request body is not valid JSON", 400) from exc
    if not isinstance(payload, Mapping):
        raise ApiError("invalid_request", "JSON body must be an object", 400)
    return payload


def _only_keys(payload: Mapping[str, Any], allowed: set[str]) -> None:
    if set(payload) - allowed:
        raise ApiError("invalid_request", "request contains unsupported fields", 400)


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def capabilities(request: web.Request) -> web.Response:
    settings = request.app[SETTINGS_KEY]
    runtime = request.app[RUNTIME_KEY]
    available = runtime.capabilities()
    tts_capabilities = runtime.tts_capabilities()
    available["tts"] = bool(tts_capabilities["providers"])
    labels = {
        name: "Hermes configured provider" if enabled else None
        for name, enabled in available.items()
    }
    return web.json_response(
        {
            "api_version": 1,
            "companion_version": __version__,
            "capabilities": {
                "conversation": {
                    "available": available.get("inference", False),
                    "languages": ["*"],
                    "full_agent": bool(settings.hermes_api_url),
                    "native_session_bootstrap": bool(settings.hermes_api_url and callable(getattr(runtime, "_bootstrap_native_session", None))),
                },
                "tts": {
                    "available": available.get("tts", False),
                    # Local Assist deployment: wildcard maps to English in HA.
                    # This is a locale declaration, not a provider/voice override.
                    "languages": ["es-ES", "es"],
                    "formats": ["mp3"],
                    "options": ["provider", "voice", "speed", "instructions"],
                    "default_provider": tts_capabilities["default_provider"],
                    "providers": tts_capabilities["providers"],
                },
                "stt": {
                    "available": available.get("stt", False),
                    "languages": ["*"],
                    "formats": ["wav", "ogg"],
                    "codecs": ["pcm", "opus"],
                    "bit_rates": [16],
                    "sample_rates": [8000, 16000, 24000, 48000],
                    "channels": [1, 2],
                    "max_audio_bytes": settings.stt_upload_limit,
                },
            },
            # Compatibility aliases for early clients.
            "platforms": available,
            "providers": labels,
            "formats": {"tts": ["mp3"], "stt": ["wav", "ogg"]},
            "limits": {
                "json_bytes": settings.json_limit,
                "inference_text_bytes": settings.inference_text_limit,
                "tts_text_bytes": settings.tts_text_limit,
                "stt_upload_bytes": settings.stt_upload_limit,
                "max_audio_bytes": settings.stt_upload_limit,
            },
        }
    )


async def inference(request: web.Request) -> web.Response:
    settings = request.app[SETTINGS_KEY]
    payload = await _read_json(request, settings.json_limit)
    _only_keys(payload, {"messages", "conversation_id", "language", "system_prompt", "bootstrap_session"})
    bootstrap = payload.get("bootstrap_session", False)
    if type(bootstrap) is not bool:
        raise ApiError("invalid_request", "bootstrap_session must be a boolean", 400)
    raw_messages = payload.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages or len(raw_messages) > 100:
        raise ApiError("invalid_request", "messages must be a non-empty list of at most 100", 400)
    messages: list[dict[str, str]] = []
    text_bytes = 0
    system_prompt = payload.get("system_prompt")
    if system_prompt is not None:
        if not isinstance(system_prompt, str) or not system_prompt.strip():
            raise ApiError("invalid_request", "system_prompt must be a non-empty string", 400)
        text_bytes += len(system_prompt.encode())
        messages.append({"role": "system", "content": system_prompt.strip()})
    for raw in raw_messages:
        if not isinstance(raw, Mapping) or set(raw) != {"role", "content"}:
            raise ApiError("invalid_request", "each message requires role and content", 400)
        role, content = raw.get("role"), raw.get("content")
        if role not in {"system", "user", "assistant"} or not isinstance(content, str):
            raise ApiError("invalid_request", "message role or content is invalid", 400)
        text_bytes += len(content.encode())
        messages.append({"role": role, "content": content})
    if text_bytes > settings.inference_text_limit:
        raise ApiError("invalid_request", "inference text is too large", 413)
    metadata: dict[str, str] = {}
    for key in ("conversation_id", "language"):
        value = payload.get(key)
        if value is not None:
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > 256
                or any(char in value for char in "\r\n")
            ):
                raise ApiError("invalid_request", f"{key} must be a short non-empty string", 400)
            metadata[key] = value
    response: dict[str, str] = {
        "text": await request.app[RUNTIME_KEY].infer(
            messages,
            conversation_id=metadata.get("conversation_id"),
            language=metadata.get("language"),
            **({"bootstrap_session": True} if bootstrap else {}),
        )
    }
    response.update(metadata)
    return web.json_response(response)


async def tts(request: web.Request) -> web.Response:
    settings = request.app[SETTINGS_KEY]
    payload = await _read_json(request, settings.json_limit)
    _only_keys(payload, {"text", "language", "provider", "voice", "speed", "instructions"})
    text = payload.get("text")
    language = payload.get("language")
    if language is not None and (
        not isinstance(language, str) or not language.strip() or len(language) > 64
    ):
        raise ApiError("invalid_request", "language must be a short non-empty string", 400)
    if not isinstance(text, str) or not text.strip():
        raise ApiError("invalid_request", "text must be a non-empty string", 400)
    if len(text.encode()) > settings.tts_text_limit:
        raise ApiError("invalid_request", "TTS text is too large", 413)
    runtime = request.app[RUNTIME_KEY]
    tts_capabilities = runtime.tts_capabilities()
    advertised = {
        item["id"]: item
        for item in tts_capabilities["providers"]
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    provider = payload.get("provider")
    if provider is not None:
        if not isinstance(provider, str) or not provider.strip() or len(provider) > 64:
            raise ApiError("invalid_request", "provider must be a short non-empty string", 400)
        provider = provider.strip().lower()
        if provider not in advertised:
            raise ApiError("invalid_request", "provider is not advertised", 400)
    voice = payload.get("voice")
    if voice is not None:
        if not isinstance(voice, str) or not voice.strip() or len(voice) > 256:
            raise ApiError("invalid_request", "voice must be a short non-empty string", 400)
        voice = voice.strip()
        selected = provider or tts_capabilities["default_provider"]
        provider_info = advertised.get(selected)
        advertised_voices = (
            {
                item["id"]
                for item in provider_info.get("voices", [])
                if isinstance(item, Mapping) and isinstance(item.get("id"), str)
            }
            if isinstance(provider_info, Mapping)
            else set()
        )
        if provider_info is None or voice not in advertised_voices:
            raise ApiError("invalid_request", "voice is not advertised for provider", 400)
    speed = payload.get("speed")
    if speed is not None:
        if isinstance(speed, bool) or not isinstance(speed, (int, float)):
            raise ApiError("invalid_request", "speed must be a number from 0.25 to 4", 400)
        speed = float(speed)
        if not math.isfinite(speed) or not 0.25 <= speed <= 4.0:
            raise ApiError("invalid_request", "speed must be a number from 0.25 to 4", 400)
    instructions = payload.get("instructions")
    if instructions is not None:
        if (
            not isinstance(instructions, str)
            or not instructions.strip()
            or "\x00" in instructions
            or len(instructions.encode()) > 4096
        ):
            raise ApiError(
                "invalid_request",
                "instructions must be a non-empty string of at most 4096 bytes",
                400,
            )
        instructions = instructions.strip()
    audio, content_type = await runtime.synthesize(
        text,
        language=language,
        provider=provider,
        voice=voice,
        speed=speed,
        instructions=instructions,
    )
    return web.Response(body=audio, content_type=content_type)


_CONTENT_SUFFIXES = {
    "audio/aac": ".aac",
    "audio/flac": ".flac",
    "audio/m4a": ".m4a",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
    "audio/x-wav": ".wav",
    "application/octet-stream": ".audio",
}


async def stt(request: web.Request) -> web.Response:
    settings = request.app[SETTINGS_KEY]
    if request.content_type not in _CONTENT_SUFFIXES:
        raise ApiError("invalid_request", "unsupported audio Content-Type", 415)
    _content_length_guard(request, settings.stt_upload_limit)
    directory = str(settings.temp_dir) if settings.temp_dir else None
    temp_root = Path(tempfile.mkdtemp(prefix="hermes-ha-stt-", dir=directory))
    os.chmod(temp_root, 0o700)
    path = temp_root / f"audio{_CONTENT_SUFFIXES[request.content_type]}"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    size = 0
    try:
        with os.fdopen(descriptor, "wb") as stream:
            async for chunk in request.content.iter_chunked(64 * 1024):
                size += len(chunk)
                if size > settings.stt_upload_limit:
                    raise ApiError("invalid_request", "audio upload is too large", 413)
                stream.write(chunk)
        if size == 0:
            raise ApiError("invalid_request", "audio upload is empty", 400)
        transcript, language = await request.app[RUNTIME_KEY].transcribe(path)
        response: dict[str, str] = {"text": transcript}
        if language:
            response["language"] = language
        return web.json_response(response)
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
        await asyncio.to_thread(shutil.rmtree, temp_root, True)


async def _close_runtime(app: web.Application) -> None:
    close = getattr(app[RUNTIME_KEY], "close", None)
    if callable(close):
        result = close()
        if asyncio.iscoroutine(result):
            await result


def create_app(settings: Settings, runtime: Runtime | None = None) -> web.Application:
    """Create a configured companion application without starting a server."""
    app = web.Application(
        middlewares=[error_middleware, auth_middleware, resource_middleware],
        client_max_size=max(settings.stt_upload_limit, settings.json_limit) + 1,
    )
    app[SETTINGS_KEY] = settings
    app[RUNTIME_KEY] = runtime or HermesRuntime(settings)
    app[SEMAPHORE_KEY] = asyncio.Semaphore(settings.concurrency)
    app[TOKEN_DIGEST_KEY] = sha256(settings.token.encode()).digest()
    app.router.add_get("/health", health, allow_head=False)
    app.router.add_get("/v1/capabilities", capabilities, allow_head=False)
    app.router.add_post("/v1/inference", inference)
    app.router.add_post("/v1/tts", tts)
    app.router.add_post("/v1/stt", stt)
    app.on_cleanup.append(_close_runtime)
    return app

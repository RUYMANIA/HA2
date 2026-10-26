"""Async API v1 client for the Hermes provider companion."""

from __future__ import annotations

import json
import math
from collections.abc import AsyncIterable, AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout
from yarl import URL

from .const import (
    API_VERSION_MAJOR,
    DEFAULT_MAX_STT_BYTES,
    MAX_ERROR_BODY,
    MAX_JSON_RESPONSE,
    MAX_TTS_INSTRUCTIONS_LENGTH,
    MAX_TTS_SPEED,
    MIN_TTS_SPEED,
)
from .models import (
    AudioFormat,
    ConversationCapability,
    HealthResult,
    HermesCapabilities,
    InferenceMessage,
    InferenceResult,
    STTCapability,
    STTResult,
    TTSCapability,
    TTSProvider,
    TTSVoice,
    optional_string,
)


class HermesApiError(Exception):
    """Base class for safe, stable API client failures."""


class InvalidUrlError(HermesApiError, ValueError):
    """The companion URL is unsafe or malformed."""


class CannotConnectError(HermesApiError):
    """The companion could not be reached."""


class AuthenticationError(HermesApiError):
    """The bearer token was rejected."""


class UnsupportedApiError(HermesApiError):
    """The companion does not implement the supported API major version."""


class CapabilityUnavailableError(HermesApiError):
    """The requested capability is unavailable."""


class InvalidResponseError(HermesApiError):
    """The companion returned an invalid or unexpectedly large response."""


class RequestError(HermesApiError):
    """The request is invalid before it reaches the companion."""


class RemoteError(HermesApiError):
    """A redacted stable error returned by the companion."""

    def __init__(self, code: str, status: int, message: str = "") -> None:
        self.code = code
        self.status = status
        self.message = message
        super().__init__(f"Hermes companion returned {code} (HTTP {status})")


def normalize_url(value: str) -> str:
    """Normalize and validate a companion base URL.

    Credentials, query strings, and fragments are rejected so bearer credentials
    can never be sent to an URL whose effective destination is ambiguous.
    """
    try:
        url = URL(value.strip())
    except (TypeError, ValueError) as err:
        raise InvalidUrlError("Enter a valid HTTP or HTTPS URL") from err

    if url.scheme not in {"http", "https"} or not url.host:
        raise InvalidUrlError("Enter an HTTP or HTTPS URL with a host")
    if url.user is not None or url.password is not None:
        raise InvalidUrlError("Embedded URL credentials are not allowed")
    if url.fragment:
        raise InvalidUrlError("URL fragments are not allowed")
    if url.query_string:
        raise InvalidUrlError("URL query strings are not allowed")

    path = url.path.rstrip("/")
    normalized = url.with_path(path).with_query(None).with_fragment(None)
    return str(normalized)


class _BoundedStream(AsyncIterable[bytes]):
    """Enforce an upload limit while preserving streaming."""

    def __init__(self, source: AsyncIterable[bytes], limit: int) -> None:
        self._source = source
        self._limit = limit

    async def __aiter__(self) -> AsyncIterator[bytes]:
        total = 0
        async for chunk in self._source:
            if not isinstance(chunk, bytes):
                raise RequestError("Audio stream chunks must be bytes")
            total += len(chunk)
            if total > self._limit:
                raise RequestError("Audio exceeds the advertised upload limit")
            yield chunk


class HermesAgentClient:
    """Typed client using Home Assistant's shared aiohttp session."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        token: str,
        *,
        request_timeout: float = 10.0,
        inference_timeout: float = 60.0,
        tts_timeout: float = 60.0,
        stt_timeout: float = 120.0,
    ) -> None:
        if not token.strip():
            raise AuthenticationError("A bearer token is required")
        self._session = session
        self.base_url = normalize_url(base_url)
        self._base = URL(self.base_url)
        self._headers = {"Authorization": f"Bearer {token}"}
        self.request_timeout = request_timeout
        self.inference_timeout = inference_timeout
        self.tts_timeout = tts_timeout
        self.stt_timeout = stt_timeout
        self._capabilities: HermesCapabilities | None = None

    @property
    def capabilities_cache(self) -> HermesCapabilities | None:
        """Return the last parsed capability response, if any."""
        return self._capabilities

    async def async_health(self) -> HealthResult:
        """Check companion liveness."""
        data = await self._request_json("GET", "/health", request_timeout=self.request_timeout)
        status = data.get("status")
        if not isinstance(status, str) or not status:
            raise InvalidResponseError("Health response has no status")
        return HealthResult(
            status=status,
            api_version=optional_string(data.get("api_version")),
            companion_version=optional_string(data.get("companion_version")),
        )

    async def async_capabilities(self) -> HermesCapabilities:
        """Fetch and validate API v1 capabilities."""
        data = await self._request_json(
            "GET", "/v1/capabilities", request_timeout=self.request_timeout
        )
        capabilities = _parse_capabilities(data)
        self._capabilities = capabilities
        return capabilities

    async def async_proactive_capabilities(self) -> dict[str, bool]:
        data = await self._request_json("GET", "/v1/capabilities", request_timeout=self.request_timeout)
        caps = data.get("capabilities", {}).get("conversation", {})
        return {"native_session_bootstrap": caps.get("native_session_bootstrap") is True,
                "full_agent": caps.get("full_agent") is True}

    async def async_inference(
        self,
        messages: Sequence[InferenceMessage | Mapping[str, str]],
        *,
        conversation_id: str | None = None,
        language: str | None = None,
        system_prompt: str | None = None,
        bootstrap_session: bool = False,
    ) -> InferenceResult:
        """Run provider inference."""
        serialized: list[dict[str, str]] = []
        for message in messages:
            if isinstance(message, InferenceMessage):
                role, content = message.role, message.content
            else:
                role, content = message.get("role"), message.get("content")
            if not isinstance(role, str) or not isinstance(content, str):
                raise RequestError("Inference messages require string role and content")
            serialized.append({"role": role, "content": content})
        if not serialized:
            raise RequestError("At least one inference message is required")

        payload: dict[str, Any] = {"messages": serialized}
        if type(bootstrap_session) is not bool:
            raise RequestError("bootstrap_session must be a boolean")
        if bootstrap_session:
            payload["bootstrap_session"] = True
        _set_optional(payload, "conversation_id", conversation_id)
        _set_optional(payload, "language", language)
        _set_optional(payload, "system_prompt", system_prompt)
        data = await self._request_json(
            "POST", "/v1/inference", json_data=payload, request_timeout=self.inference_timeout
        )
        text = data.get("text")
        if not isinstance(text, str):
            raise InvalidResponseError("Inference response has no text")
        return InferenceResult(
            text=text,
            conversation_id=optional_string(data.get("conversation_id")),
            model=optional_string(data.get("model")),
            provider=optional_string(data.get("provider")),
        )

    async def async_tts(
        self,
        text: str,
        *,
        language: str | None = None,
        provider: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        instructions: str | None = None,
    ) -> tuple[str, bytes]:
        """Synthesize speech and return bytes, never a server path."""
        if not text:
            raise RequestError("TTS text must not be empty")
        payload: dict[str, Any] = {"text": text}
        _set_optional(payload, "language", language)
        capability = self._capabilities.tts if self._capabilities is not None else None
        _validate_tts_controls(capability, provider, voice, speed, instructions)
        _set_optional(payload, "provider", provider)
        _set_optional(payload, "voice", voice)
        if speed is not None:
            payload["speed"] = speed
        _set_optional(payload, "instructions", instructions)

        async with self._request(
            "POST", "/v1/tts", json_data=payload, request_timeout=self.tts_timeout
        ) as response:
            await self._raise_for_error(response)
            audio = await _read_bounded(response, _tts_response_limit(self._capabilities))
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            content_type = content_type.split(";", 1)[0].strip().lower()
            extension = response.headers.get("X-Audio-Extension") or _extension_for(
                content_type
            )
            return extension, audio

    async def async_stt(
        self,
        audio: bytes | AsyncIterable[bytes],
        *,
        content_type: str,
        language: str | None = None,
        sample_rate: int | None = None,
        channels: int | None = None,
    ) -> STTResult:
        """Stream bounded audio to the transcription endpoint."""
        limit = _stt_upload_limit(self._capabilities)
        if isinstance(audio, bytes):
            if len(audio) > limit:
                raise RequestError("Audio exceeds the advertised upload limit")
            body: bytes | AsyncIterable[bytes] = audio
        else:
            body = _BoundedStream(audio, limit)

        headers = {"Content-Type": content_type}
        if language:
            headers["X-Language"] = language
        if sample_rate is not None:
            headers["X-Sample-Rate"] = str(sample_rate)
        if channels is not None:
            headers["X-Channels"] = str(channels)
        data = await self._request_json(
            "POST",
            "/v1/stt",
            data=body,
            headers=headers,
            request_timeout=self.stt_timeout,
        )
        text = data.get("text") or data.get("transcript")
        if not isinstance(text, str):
            raise InvalidResponseError("STT response has no transcript")
        return STTResult(text=text, language=optional_string(data.get("language")))

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        path: str,
        *,
        request_timeout: float,
        json_data: Mapping[str, Any] | None = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> AsyncIterator[ClientResponse]:
        request_headers = dict(self._headers)
        if headers:
            request_headers.update(headers)
        url = self._base.with_path(f"{self._base.path.rstrip('/')}{path}")
        try:
            async with self._session.request(
                method,
                url,
                headers=request_headers,
                json=json_data,
                data=data,
                timeout=ClientTimeout(total=request_timeout),
                allow_redirects=False,
            ) as response:
                # Refusing all redirects is stricter than merely refusing cross-host
                # redirects and guarantees Authorization never reaches another origin.
                yield response
        except (TimeoutError, ClientError) as err:
            raise CannotConnectError("Unable to reach the Hermes companion") from err

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        request_timeout: float,
        json_data: Mapping[str, Any] | None = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        async with self._request(
            method,
            path,
            request_timeout=request_timeout,
            json_data=json_data,
            data=data,
            headers=headers,
        ) as response:
            await self._raise_for_error(response)
            raw = await _read_bounded(response, MAX_JSON_RESPONSE)
        try:
            parsed = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            raise InvalidResponseError("Companion returned invalid JSON") from err
        if not isinstance(parsed, dict):
            raise InvalidResponseError("Companion returned a non-object JSON response")
        return parsed

    async def _raise_for_error(self, response: ClientResponse) -> None:
        if response.status < 300:
            return
        raw = await _read_bounded(response, MAX_ERROR_BODY, truncate=True)
        code = "http_error"
        message = ""
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                error = payload.get("error", payload)
                if isinstance(error, dict):
                    code = optional_string(error.get("code")) or code
                    message = optional_string(error.get("message")) or ""
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        if response.status in {401, 403} or code == "unauthorized":
            raise AuthenticationError("The Hermes companion rejected the token")
        if 300 <= response.status < 400:
            raise RemoteError("redirect_refused", response.status)
        if code == "capability_unavailable":
            raise CapabilityUnavailableError(message or "Capability unavailable")
        raise RemoteError(code, response.status, message)


def _set_optional(payload: dict[str, Any], key: str, value: Any) -> None:
    if value is not None and value != "":
        payload[key] = value


async def _read_bounded(
    response: ClientResponse, limit: int, *, truncate: bool = False
) -> bytes:
    length = response.content_length
    if length is not None and length > limit and not truncate:
        raise InvalidResponseError("Companion response exceeds the safe size limit")
    raw = bytearray()
    while chunk := await response.content.read(min(65536, limit + 1 - len(raw))):
        raw.extend(chunk)
        if len(raw) > limit:
            if truncate:
                return bytes(raw[:limit])
            raise InvalidResponseError("Companion response exceeds the safe size limit")
    return bytes(raw)


def _parse_capabilities(data: Mapping[str, Any]) -> HermesCapabilities:
    version_value = data.get("api_version")
    version = str(version_value) if isinstance(version_value, (str, int)) else ""
    normalized_version = version.removeprefix("v").removeprefix("V")
    try:
        major = int(normalized_version.split(".", 1)[0])
    except ValueError:
        major = -1
    if major != API_VERSION_MAJOR:
        raise UnsupportedApiError(f"Unsupported companion API version: {version or 'missing'}")

    raw_caps = data.get("capabilities", data.get("platforms", {}))
    if not isinstance(raw_caps, Mapping):
        raise InvalidResponseError("Capabilities response has no platform map")

    providers = _string_mapping(data.get("providers"))
    limits = _integer_mapping(data.get("limits"))
    conversation_info = _mapping(raw_caps.get("conversation"))
    tts_info = _mapping(raw_caps.get("tts"))
    stt_info = _mapping(raw_caps.get("stt"))

    return HermesCapabilities(
        api_version=version,
        companion_version=optional_string(data.get("companion_version")),
        conversation=ConversationCapability(
            available=_capability_enabled(raw_caps, "conversation", "inference"),
            languages=_strings(conversation_info.get("languages")),
        ),
        tts=TTSCapability(
            available=_capability_enabled(raw_caps, "tts"),
            languages=_strings(tts_info.get("languages", data.get("tts_languages"))),
            voices=_strings(tts_info.get("voices", data.get("tts_voices"))),
            formats=_formats(tts_info.get("formats", data.get("tts_formats"))),
            options=_strings(tts_info.get("options")),
            default_language=optional_string(tts_info.get("default_language")),
            default_options=_scalar_mapping(tts_info.get("default_options")),
            default_provider=optional_string(tts_info.get("default_provider")),
            providers=_tts_providers(tts_info.get("providers")),
        ),
        stt=STTCapability(
            available=_capability_enabled(raw_caps, "stt"),
            languages=_strings(stt_info.get("languages", data.get("stt_languages"))),
            formats=_format_names(stt_info.get("formats", data.get("stt_formats"))),
            codecs=_strings(stt_info.get("codecs")),
            bit_rates=_integers(stt_info.get("bit_rates")),
            sample_rates=_integers(stt_info.get("sample_rates")),
            channels=_integers(stt_info.get("channels")),
            max_audio_bytes=_positive_int(
                stt_info.get(
                    "max_audio_bytes",
                    limits.get("stt_max_bytes", limits.get("max_stt_bytes")),
                )
            ),
        ),
        provider_labels=providers,
        limits=limits,
    )


def _capability_enabled(caps: Mapping[str, Any], *names: str) -> bool:
    for name in names:
        value = caps.get(name)
        if isinstance(value, bool):
            return value
        if isinstance(value, Mapping):
            enabled = value.get("available", value.get("enabled", True))
            if isinstance(enabled, bool):
                return enabled
    return False


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, str) and item
    }


def _integer_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, int) and not isinstance(item, bool)
    }


def _scalar_mapping(value: Any) -> dict[str, str | int | float | bool | None]:
    if not isinstance(value, Mapping):
        return {}
    return {
        key: item
        for key, item in value.items()
        if isinstance(key, str)
        and isinstance(item, (str, int, float, bool, type(None)))
    }


def _tts_providers(value: Any) -> tuple[TTSProvider, ...]:
    """Parse only the public, diagnostics-safe TTS provider contract."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    providers: list[TTSProvider] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        provider_id = optional_string(item.get("id"))
        label = optional_string(item.get("label"))
        if provider_id is None or label is None:
            continue
        voices: list[TTSVoice] = []
        raw_voices = item.get("voices")
        if isinstance(raw_voices, Sequence) and not isinstance(raw_voices, (str, bytes)):
            for voice in raw_voices:
                if not isinstance(voice, Mapping):
                    continue
                voice_id = optional_string(voice.get("id"))
                name = optional_string(voice.get("name"))
                if voice_id is not None and name is not None:
                    voices.append(TTSVoice(id=voice_id, name=name))
        providers.append(
            TTSProvider(
                id=provider_id,
                label=label,
                default_voice=optional_string(item.get("default_voice")),
                voices=tuple(voices),
                supports_speed=item.get("supports_speed") is True,
                supports_instructions=item.get("supports_instructions") is True,
            )
        )
    return tuple(providers)


def _validate_tts_controls(
    capability: TTSCapability | None,
    provider: str | None,
    voice: str | None,
    speed: float | None,
    instructions: str | None,
) -> None:
    """Validate dynamic controls against the fetched companion contract."""
    values = (provider, voice, speed, instructions)
    if capability is None:
        if any(value is not None for value in values):
            raise RequestError("TTS controls require advertised companion capabilities")
        return
    supported = set(capability.options)
    controls = {
        "provider": provider,
        "voice": voice,
        "speed": speed,
        "instructions": instructions,
    }
    if any(value is not None and name not in supported for name, value in controls.items()):
        raise RequestError("Requested TTS controls are not advertised by the companion")
    if provider is not None and provider not in capability.provider_ids:
        raise RequestError("Requested TTS provider is not advertised by the companion")
    selected = capability.provider(provider)
    if voice is not None and (selected is None or voice not in selected.voice_ids):
        raise RequestError("Requested TTS voice does not belong to the selected provider")
    if speed is not None:
        if isinstance(speed, bool) or not isinstance(speed, (int, float)):
            raise RequestError("TTS speed must be numeric")
        if not math.isfinite(speed) or not MIN_TTS_SPEED <= speed <= MAX_TTS_SPEED:
            raise RequestError("TTS speed is outside the supported range")
        if selected is not None and not selected.supports_speed:
            raise RequestError("Selected TTS provider does not support speed")
    if instructions is not None:
        if not isinstance(instructions, str) or len(instructions) > MAX_TTS_INSTRUCTIONS_LENGTH:
            raise RequestError("TTS instructions are invalid or too long")
        if selected is not None and not selected.supports_instructions:
            raise RequestError("Selected TTS provider does not support instructions")


def _integers(value: Any) -> tuple[int, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        item for item in value if isinstance(item, int) and not isinstance(item, bool)
    )


def _positive_int(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _format_names(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            name = item.split("/", 1)[-1].split(";", 1)[0]
        elif isinstance(item, Mapping):
            raw = item.get("format") or item.get("extension")
            name = raw if isinstance(raw, str) else ""
        else:
            name = ""
        if name and name not in result:
            result.append(name)
    return tuple(result)


def _formats(value: Any) -> tuple[AudioFormat, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    formats: list[AudioFormat] = []
    for item in value:
        if isinstance(item, str):
            if "/" in item:
                content_type = item
                extension = _extension_for(item)
            else:
                extension = item.lower().lstrip(".")
                content_type = _content_type_for_extension(extension)
            formats.append(AudioFormat(content_type=content_type, extension=extension))
            continue
        if not isinstance(item, Mapping):
            continue
        content_type = item.get("content_type") or item.get("mime_type")
        if not isinstance(content_type, str) or not content_type:
            continue
        extension = item.get("extension")
        formats.append(
            AudioFormat(
                content_type=content_type,
                extension=(
                    extension
                    if isinstance(extension, str) and extension
                    else _extension_for(content_type)
                ),
                codec=optional_string(item.get("codec")),
                sample_rate=_optional_int(item.get("sample_rate")),
                channels=_optional_int(item.get("channels")),
                bit_rate=_optional_int(item.get("bit_rate")),
            )
        )
    return tuple(formats)


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _content_type_for_extension(extension: str) -> str:
    return {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "webm": "audio/webm",
        "aac": "audio/aac",
        "m4a": "audio/mp4",
    }.get(extension.lower().lstrip("."), "application/octet-stream")


def _extension_for(content_type: str) -> str:
    return {
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/ogg": "ogg",
        "audio/flac": "flac",
        "audio/webm": "webm",
    }.get(content_type.split(";", 1)[0].lower(), "bin")


def _stt_upload_limit(capabilities: HermesCapabilities | None) -> int:
    if capabilities is None:
        return DEFAULT_MAX_STT_BYTES
    if capabilities.stt.max_audio_bytes is not None:
        return capabilities.stt.max_audio_bytes
    for key in ("stt_upload_bytes", "max_audio_bytes", "stt_max_bytes", "max_stt_bytes"):
        if value := capabilities.limits.get(key):
            return value
    return DEFAULT_MAX_STT_BYTES


def _tts_response_limit(capabilities: HermesCapabilities | None) -> int:
    default = 32 * 1024 * 1024
    if capabilities is None:
        return default
    return capabilities.limits.get(
        "tts_max_response_bytes",
        capabilities.limits.get("max_tts_bytes", default),
    )

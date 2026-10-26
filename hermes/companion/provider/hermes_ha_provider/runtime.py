"""Lazy, defensive adapters around installed Hermes runtime seams."""

from __future__ import annotations

import asyncio
import copy
import importlib
import inspect
import json
import logging
import mimetypes
import os
import re
import sys
import tempfile
import threading
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, cast

from aiohttp import ClientError, ClientSession, ClientTimeout

from .config import Settings

_LOGGER = logging.getLogger(__name__)

_SAFE_AUDIO_TYPES = {
    "audio/aac",
    "audio/flac",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-wav",
}

_BUILTIN_VOICE_KEYS = {
    "edge": "voice",
    "elevenlabs": "voice_id",
    "openai": "voice",
    "minimax": "voice_id",
    "xai": "voice_id",
    "mistral": "voice_id",
    "gemini": "voice",
    "kittentts": "voice",
    "piper": "voice",
    "deepinfra": "voice",
}
_BUILTIN_SPEED_PROVIDERS = frozenset(
    {"edge", "elevenlabs", "openai", "minimax", "xai", "kittentts", "piper", "deepinfra"}
)
_BUILTIN_INSTRUCTION_PROVIDERS = frozenset({"openai"})
_SAFE_PROVIDER_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_MISSING = object()


class RuntimeFailure(RuntimeError):
    """A redacted provider failure safe to map at the HTTP boundary."""


class CapabilityUnavailable(RuntimeFailure):
    """The requested Hermes seam is not installed or configured."""


class Importer(Protocol):
    def __call__(self, name: str) -> ModuleType: ...


def _extract_content(response: Any) -> str:
    if isinstance(response, Mapping):
        choices = response.get("choices")
    else:
        choices = getattr(response, "choices", None)
    if not isinstance(choices, Sequence) or isinstance(choices, (str, bytes)) or not choices:
        raise RuntimeFailure("Hermes returned an invalid inference response")
    choice = choices[0]
    message = (
        choice.get("message")
        if isinstance(choice, Mapping)
        else getattr(choice, "message", None)
    )
    content = (
        message.get("content")
        if isinstance(message, Mapping)
        else getattr(message, "content", None)
    )
    if isinstance(content, str) and content:
        return content
    if isinstance(content, Sequence) and not isinstance(content, (str, bytes)):
        parts: list[str] = []
        for part in content:
            text = part.get("text") if isinstance(part, Mapping) else getattr(part, "text", None)
            if isinstance(text, str):
                parts.append(text)
        if parts:
            return "".join(parts)
    raise RuntimeFailure("Hermes returned an empty inference response")


def _json_mapping(value: str) -> Mapping[str, Any] | None:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


async def _invoke(function: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    """Invoke a possibly blocking or async Hermes function without blocking aiohttp."""
    result = await asyncio.to_thread(function, *args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class HermesRuntime:
    """Lazy compatibility boundary around an installed Hermes checkout/package."""

    _SEAMS = {
        "inference": ("agent.auxiliary_client", "call_llm"),
        "tts": ("tools.tts_tool", "text_to_speech_tool"),
        "stt": ("tools.transcription_tools", "transcribe_audio"),
    }

    def __init__(self, settings: Settings, importer: Importer = importlib.import_module) -> None:
        self._settings = settings
        self._importer = importer
        self._functions: dict[str, Callable[..., Any] | None] = {}
        self._modules: dict[str, ModuleType] = {}
        self._api_session: ClientSession | None = None
        self._tts_config_lock = threading.RLock()
        self._configure_runtime()

    def _configure_runtime(self) -> None:
        if self._settings.hermes_source is not None:
            source = self._settings.hermes_source.resolve()
            if not source.is_dir():
                raise RuntimeFailure("configured Hermes source directory is unavailable")
            source_string = str(source)
            if source_string not in sys.path:
                sys.path.insert(0, source_string)
        if self._settings.hermes_home is not None:
            os.environ["HERMES_HOME"] = str(self._settings.hermes_home.resolve())
            try:
                constants = self._importer("hermes_constants")
                setter = getattr(constants, "set_hermes_home_override", None)
                if callable(setter):
                    setter(self._settings.hermes_home.resolve())
            except ImportError:
                # Hermes may be installed as a package/version without this helper.
                pass
        if self._settings.hermes_profile:
            os.environ["HERMES_PROFILE"] = self._settings.hermes_profile

    def _load(self, capability: str) -> Callable[..., Any]:
        if capability in self._functions:
            function = self._functions[capability]
            if function is None:
                raise CapabilityUnavailable(f"{capability} is unavailable")
            return function
        module_name, attribute = self._SEAMS[capability]
        try:
            module = self._importer(module_name)
            candidate = getattr(module, attribute)
            if not callable(candidate):
                raise TypeError
        except (ImportError, AttributeError, TypeError):
            self._functions[capability] = None
            raise CapabilityUnavailable(f"{capability} is unavailable") from None
        function = cast(Callable[..., Any], candidate)
        self._functions[capability] = function
        self._modules[capability] = module
        return function

    def capabilities(self) -> dict[str, bool]:
        """Probe import availability without exposing module paths or configuration."""
        availability: dict[str, bool] = {}
        for capability in self._SEAMS:
            if capability == "inference" and self._settings.hermes_api_url:
                availability[capability] = True
                continue
            try:
                self._load(capability)
            except CapabilityUnavailable:
                availability[capability] = False
            else:
                availability[capability] = True
        return availability

    def tts_capabilities(self) -> dict[str, Any]:
        """Discover safe, selectable Hermes TTS providers and voices."""
        try:
            self._load("tts")
        except CapabilityUnavailable:
            return {"default_provider": None, "providers": []}
        module = self._modules["tts"]
        config = self._load_tts_config(module)
        builtins = self._builtin_names(module)
        labels = self._builtin_labels()
        configured_default = self._provider_id(config.get("provider"))
        default_provider = configured_default or self._provider_id(
            getattr(module, "DEFAULT_PROVIDER", "edge")
        )

        providers: dict[str, dict[str, Any]] = {}
        candidates = {
            provider
            for raw_name, section in config.items()
            if isinstance(section, Mapping)
            and (provider := self._provider_id(raw_name)) is not None
            and provider in builtins
        }
        if default_provider in builtins:
            candidates.add(default_provider)
        for provider in sorted(candidates):
            if not self._builtin_available(module, config, provider):
                continue
            section = config.get(provider)
            provider_config = section if isinstance(section, Mapping) else {}
            voice_key = _BUILTIN_VOICE_KEYS.get(provider)
            voice = self._public_value(provider_config.get(voice_key)) if voice_key else None
            providers[provider] = self._provider_capability(
                provider,
                labels.get(provider, provider.replace("_", " ").title()),
                voice,
                self._configured_voices(provider_config, voice),
                provider in _BUILTIN_SPEED_PROVIDERS,
                provider in _BUILTIN_INSTRUCTION_PROVIDERS,
            )

        named = config.get("providers")
        if isinstance(named, Mapping):
            for raw_name, raw_section in named.items():
                provider = self._provider_id(raw_name)
                if provider is None or provider in builtins or not isinstance(raw_section, Mapping):
                    continue
                provider_type = str(raw_section.get("type") or "command").strip().lower()
                command = raw_section.get("command")
                if (
                    provider_type != "command"
                    or not isinstance(command, str)
                    or not command.strip()
                ):
                    continue
                voice = self._public_value(raw_section.get("voice"))
                providers[provider] = self._provider_capability(
                    provider,
                    self._public_value(raw_section.get("name"))
                    or provider.replace("_", " ").title(),
                    voice,
                    self._configured_voices(raw_section, voice),
                    True,
                    False,
                )

        for plugin in self._plugin_providers():
            provider = self._provider_id(getattr(plugin, "name", None))
            if provider is None or provider in builtins or provider in providers:
                continue
            try:
                if not bool(plugin.is_available()):
                    continue
            except Exception:
                _LOGGER.debug(
                    "Hermes plugin TTS provider availability check failed",
                    exc_info=True,
                )
                continue
            voices = self._plugin_voices(plugin)
            default_voice = self._public_value(self._call_optional(plugin, "default_voice"))
            configured = config.get(provider)
            if isinstance(configured, Mapping):
                default_voice = self._public_value(configured.get("voice")) or default_voice
            if default_voice and all(item["id"] != default_voice for item in voices):
                voices.insert(0, self._voice(default_voice, default_voice))
            synthesize = getattr(plugin, "synthesize", None)
            providers[provider] = self._provider_capability(
                provider,
                self._public_value(getattr(plugin, "display_name", None)) or provider.title(),
                default_voice,
                voices,
                self._accepts_keyword(synthesize, "speed"),
                self._accepts_keyword(synthesize, "instructions"),
            )

        ordered = [providers[name] for name in sorted(providers)]
        return {
            "default_provider": default_provider if default_provider in providers else None,
            "providers": ordered,
        }

    def _load_tts_config(self, module: ModuleType) -> dict[str, Any]:
        loader = getattr(module, "_load_tts_config", None)
        if not callable(loader):
            return {}
        try:
            value = loader()
        except Exception:
            return {}
        return copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}

    def _builtin_names(self, module: ModuleType) -> set[str]:
        raw = getattr(module, "BUILTIN_TTS_PROVIDERS", ())
        names = {provider for item in raw if (provider := self._provider_id(item)) is not None}
        return names or set(_BUILTIN_VOICE_KEYS) | {"neutts"}

    def _builtin_labels(self) -> dict[str, str]:
        try:
            module = self._importer("hermes_cli.tools_config")
            category = getattr(module, "TOOL_CATEGORIES", {}).get("tts", {})
            rows = category.get("providers", []) if isinstance(category, Mapping) else []
        except (ImportError, AttributeError, TypeError):
            return {}
        labels: dict[str, str] = {}
        for row in rows if isinstance(rows, Sequence) else []:
            if not isinstance(row, Mapping):
                continue
            provider = self._provider_id(row.get("tts_provider") or row.get("id"))
            label = self._public_value(row.get("name"))
            if provider and label and not row.get("requires_nous_auth"):
                labels[provider] = label
        return labels

    def _builtin_available(self, module: ModuleType, config: dict[str, Any], provider: str) -> bool:
        check = getattr(module, "check_tts_requirements", None)
        if not callable(check):
            return provider == self._provider_id(config.get("provider"))
        probe = copy.deepcopy(config)
        probe["provider"] = provider
        try:
            return bool(self._with_tts_config(module, probe, check))
        except Exception:
            return False

    def _plugin_providers(self) -> list[Any]:
        try:
            plugins = self._importer("hermes_cli.plugins")
            discover = getattr(plugins, "_ensure_plugins_discovered", None)
            if callable(discover):
                discover()
            registry = self._importer("agent.tts_registry")
            listed = registry.list_providers()
        except (ImportError, AttributeError, TypeError):
            return []
        return list(listed) if isinstance(listed, Sequence) else []

    def _plugin_voices(self, plugin: Any) -> list[dict[str, str]]:
        try:
            raw_voices = plugin.list_voices()
        except Exception:
            return []
        voices: dict[str, dict[str, str]] = {}
        for raw in raw_voices if isinstance(raw_voices, Sequence) else []:
            if not isinstance(raw, Mapping):
                continue
            voice_id = self._public_value(raw.get("id"))
            name = self._public_value(raw.get("display") or raw.get("name")) or voice_id
            if voice_id and name:
                voices[voice_id] = self._voice(voice_id, name)
        return [voices[key] for key in sorted(voices)]

    def _configured_voices(
        self, provider_config: Mapping[str, Any], default_voice: str | None
    ) -> list[dict[str, str]]:
        """Return a sanitized provider-owned voice inventory with its default first."""
        voices: dict[str, dict[str, str]] = {}
        raw_voices = provider_config.get("voices")
        if isinstance(raw_voices, str):
            try:
                raw_voices = json.loads(raw_voices)
            except json.JSONDecodeError:
                raw_voices = None
        if isinstance(raw_voices, Sequence) and not isinstance(raw_voices, (str, bytes)):
            for raw in raw_voices:
                if isinstance(raw, str):
                    voice_id = self._public_value(raw)
                    name = voice_id
                elif isinstance(raw, Mapping):
                    voice_id = self._public_value(raw.get("id"))
                    name = self._public_value(raw.get("name") or raw.get("display"))
                    name = name or voice_id
                else:
                    continue
                if voice_id and name:
                    voices[voice_id] = self._voice(voice_id, name)
        if default_voice:
            default = voices.pop(default_voice, self._voice(default_voice, default_voice))
            return [default, *voices.values()]
        return list(voices.values())

    @staticmethod
    def _call_optional(instance: Any, name: str) -> Any:
        value = getattr(instance, name, None)
        try:
            return value() if callable(value) else value
        except Exception:
            return None

    @staticmethod
    def _accepts_keyword(function: Any, keyword: str) -> bool:
        if not callable(function):
            return False
        try:
            parameters = inspect.signature(function).parameters.values()
        except (TypeError, ValueError):
            return False
        return any(
            item.name == keyword or item.kind is inspect.Parameter.VAR_KEYWORD
            for item in parameters
        )

    @staticmethod
    def _provider_id(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        return normalized if _SAFE_PROVIDER_ID.fullmatch(normalized) else None

    @staticmethod
    def _public_value(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        if (
            not normalized
            or len(normalized) > 256
            or any(character in normalized for character in "\x00\r\n")
            or normalized.startswith(("/", "~", "\\"))
        ):
            return None
        return normalized

    @staticmethod
    def _voice(voice_id: str, name: str) -> dict[str, str]:
        return {"id": voice_id, "name": name}

    @staticmethod
    def _provider_capability(
        provider: str,
        label: str,
        default_voice: str | None,
        voices: list[dict[str, str]],
        supports_speed: bool,
        supports_instructions: bool,
    ) -> dict[str, Any]:
        return {
            "id": provider,
            "label": label,
            "default_voice": default_voice,
            "voices": voices,
            "supports_speed": supports_speed,
            "supports_instructions": supports_instructions,
        }

    def _with_tts_config(
        self,
        module: ModuleType,
        config: dict[str, Any],
        function: Callable[..., Any],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        with self._tts_config_lock:
            original = getattr(module, "_load_tts_config", _MISSING)
            if original is _MISSING:
                raise RuntimeFailure("Hermes TTS configuration override is unavailable")
            module.__dict__["_load_tts_config"] = lambda: copy.deepcopy(config)
            try:
                return function(*args, **kwargs)
            finally:
                module.__dict__["_load_tts_config"] = original

    async def infer(
        self,
        messages: list[dict[str, str]],
        *,
        conversation_id: str | None = None,
        language: str | None = None,
        bootstrap_session: bool = False,
    ) -> str:
        if type(bootstrap_session) is not bool:
            raise RuntimeFailure("Invalid session bootstrap request")
        if bootstrap_session:
            if not isinstance(conversation_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", conversation_id):
                raise RuntimeFailure("Invalid session bootstrap id")
            await self._bootstrap_native_session(conversation_id)
        if self._settings.hermes_api_url:
            text = await self._infer_via_api(messages, conversation_id, language)
            if bootstrap_session:
                history = await self._native_session_json("GET", f"/api/sessions/{conversation_id}/messages")
                rows = history.get("data")
                if not isinstance(rows, list) or history.get("session_id") != conversation_id:
                    raise RuntimeFailure("Invalid native session history")
                last = next((row for row in reversed(rows) if isinstance(row, dict) and row.get("role") == "assistant"), None)
                if last is None or not isinstance(last.get("content"), str) or last["content"].strip() != text.strip():
                    raise RuntimeFailure("Native session persistence not verified")
            return text
        function = self._load("inference")
        try:
            response = await _invoke(
                function,
                task=None,
                messages=messages,
                timeout=self._settings.request_timeout,
            )
            return _extract_content(response)
        except RuntimeFailure:
            raise
        except Exception as exc:
            raise RuntimeFailure("Hermes inference failed") from exc

    async def _native_session_json(self, method: str, path: str, payload=None, expected=200) -> dict:
        if not self._settings.hermes_api_url:
            raise RuntimeFailure("Native session API unavailable")
        if self._api_session is None or self._api_session.closed:
            self._api_session = ClientSession(timeout=ClientTimeout(total=self._settings.request_timeout))
        try:
            async with self._api_session.request(method, self._settings.hermes_api_url + path,
                headers={"Authorization": f"Bearer {self._settings.hermes_api_token}"},
                json=payload, allow_redirects=False) as response:
                if response.status != expected:
                    raise RuntimeFailure("Native session operation refused")
                raw = await response.content.read(self._settings.json_limit + 1)
            if len(raw) > self._settings.json_limit:
                raise RuntimeFailure("Native session response too large")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise RuntimeFailure("Invalid native session response")
            return data
        except (ClientError, TimeoutError, ValueError) as exc:
            raise RuntimeFailure("Native session operation failed") from exc

    async def _bootstrap_native_session(self, session_id: str) -> None:
        # Never adopt a pre-existing row after a 409, and never retry an ambiguous create.
        await self._native_session_json("POST", "/api/sessions", {"id": session_id, "source": "api_server"}, expected=201)
        data = await self._native_session_json("GET", f"/api/sessions/{session_id}")
        if not isinstance(data.get("session"), dict) or data["session"].get("id") != session_id:
            raise RuntimeFailure("Native session readback mismatch")

    async def _infer_via_api(
        self,
        messages: list[dict[str, str]],
        conversation_id: str | None,
        language: str | None,
    ) -> str:
        if self._api_session is None or self._api_session.closed:
            self._api_session = ClientSession(
                timeout=ClientTimeout(total=self._settings.request_timeout)
            )
        headers = {
            "Authorization": f"Bearer {self._settings.hermes_api_token}",
            "X-Hermes-Session-Key": self._settings.hermes_api_session_key,
        }
        if conversation_id:
            headers["X-Hermes-Session-Id"] = conversation_id
        if language:
            headers["Accept-Language"] = language
        url = f"{self._settings.hermes_api_url}/v1/chat/completions"
        try:
            async with self._api_session.post(
                url,
                headers=headers,
                json={"model": "hermes-agent", "messages": messages, "stream": False},
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    raise RuntimeFailure("Hermes agent API request failed")
                raw = await response.content.read(self._settings.json_limit + 1)
        except RuntimeFailure:
            raise
        except (ClientError, TimeoutError) as exc:
            raise RuntimeFailure("Hermes agent API request failed") from exc
        if len(raw) > self._settings.json_limit:
            raise RuntimeFailure("Hermes agent API response exceeded the configured limit")
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeFailure("Hermes agent API returned invalid JSON") from exc
        return _extract_content(payload)

    async def close(self) -> None:
        """Close the native Hermes API connection pool."""
        if self._api_session is not None and not self._api_session.closed:
            await self._api_session.close()

    async def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        provider: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        instructions: str | None = None,
    ) -> tuple[bytes, str]:
        function = self._load("tts")
        module = self._modules["tts"]
        config = self._load_tts_config(module)
        selected = provider or self._provider_id(config.get("provider"))
        if voice is not None:
            if selected is None:
                selected = self._provider_id(getattr(module, "DEFAULT_PROVIDER", "edge"))
            if selected is None:
                raise RuntimeFailure("Hermes TTS voice override is unavailable")
            config = copy.deepcopy(config)
            if selected in self._builtin_names(module):
                voice_key = _BUILTIN_VOICE_KEYS.get(selected)
                if voice_key is None:
                    raise RuntimeFailure("Hermes TTS voice override is unavailable")
                section = config.get(selected)
                provider_config = dict(section) if isinstance(section, Mapping) else {}
                provider_config[voice_key] = voice
                config[selected] = provider_config
            else:
                named = config.get("providers")
                if isinstance(named, Mapping) and isinstance(named.get(selected), Mapping):
                    named_config = copy.deepcopy(dict(named))
                    provider_config = dict(cast(Mapping[str, Any], named_config[selected]))
                    provider_config["voice"] = voice
                    named_config[selected] = provider_config
                    config["providers"] = named_config
                configured = config.get(selected)
                plugin_config = dict(configured) if isinstance(configured, Mapping) else {}
                plugin_config["voice"] = voice
                config[selected] = plugin_config
                config["voice"] = voice
        kwargs = {
            "provider": provider,
            "speed": speed,
            "instructions": instructions,
        }
        supported_kwargs = {
            key: value
            for key, value in kwargs.items()
            if value is not None and self._accepts_keyword(function, key)
        }
        _ = language  # Hermes' public TTS tool currently has no language override.
        directory = str(self._settings.temp_dir) if self._settings.temp_dir else None
        try:
            with tempfile.TemporaryDirectory(prefix="hermes-ha-tts-", dir=directory) as temp_name:
                temp_root = Path(temp_name)
                os.chmod(temp_root, 0o700)
                path = temp_root / "audio.mp3"
                if callable(getattr(module, "_load_tts_config", None)):
                    result = await asyncio.to_thread(
                        self._with_tts_config,
                        module,
                        config,
                        function,
                        text,
                        output_path=str(path),
                        **supported_kwargs,
                    )
                elif voice is None:
                    result = await _invoke(
                        function,
                        text,
                        output_path=str(path),
                        **supported_kwargs,
                    )
                else:
                    raise RuntimeFailure("Hermes TTS voice override is unavailable")
                audio_path = self._tts_result_path(result, fallback=path, root=temp_root)
                data = await asyncio.to_thread(self._read_bounded, audio_path)
                content_type = mimetypes.guess_type(audio_path.name)[0] or "audio/mpeg"
                if content_type not in _SAFE_AUDIO_TYPES:
                    content_type = "application/octet-stream"
                return data, content_type
        except (CapabilityUnavailable, RuntimeFailure):
            raise
        except Exception as exc:
            raise RuntimeFailure("Hermes text-to-speech failed") from exc

    def _tts_result_path(self, result: Any, fallback: Path, root: Path) -> Path:
        if isinstance(result, str):
            mapping = _json_mapping(result)
            if mapping is not None:
                if mapping.get("success") is False:
                    raise RuntimeFailure("Hermes text-to-speech failed")
                raw_paths = mapping.get("file_paths")
                if isinstance(raw_paths, list):
                    if not all(
                        isinstance(item, str) and Path(item).resolve().is_relative_to(root)
                        for item in raw_paths
                    ):
                        raise RuntimeFailure("Hermes returned an unexpected audio location")
                    if len(raw_paths) != 1:
                        raise RuntimeFailure("Hermes returned multiple audio files")
                raw_path = (
                    raw_paths[0]
                    if isinstance(raw_paths, list) and raw_paths
                    else mapping.get("file_path") or mapping.get("path")
                )
                if isinstance(raw_path, str):
                    candidate = Path(raw_path).resolve()
                    if not candidate.is_relative_to(root):
                        raise RuntimeFailure("Hermes returned an unexpected audio location")
                    return candidate
            elif result.startswith("MEDIA:"):
                candidate = Path(result.removeprefix("MEDIA:").strip()).resolve()
                if not candidate.is_relative_to(root):
                    raise RuntimeFailure("Hermes returned an unexpected audio location")
                return candidate
        if fallback.is_file() and fallback.stat().st_size:
            return fallback
        raise RuntimeFailure("Hermes returned no audio")

    def _read_bounded(self, path: Path) -> bytes:
        with path.open("rb") as stream:
            data = stream.read(self._settings.tts_audio_limit + 1)
        if len(data) > self._settings.tts_audio_limit:
            raise RuntimeFailure("Hermes audio exceeded the configured limit")
        if not data:
            raise RuntimeFailure("Hermes returned empty audio")
        return data

    async def transcribe(self, path: Path) -> tuple[str, str | None]:
        function = self._load("stt")
        try:
            result = await _invoke(function, str(path))
        except CapabilityUnavailable:
            raise
        except Exception as exc:
            raise RuntimeFailure("Hermes transcription failed") from exc
        if isinstance(result, str):
            mapping = _json_mapping(result)
            if mapping is None:
                if result.strip():
                    return result, None
                raise RuntimeFailure("Hermes returned an empty transcript")
            result = mapping
        if not isinstance(result, Mapping) or result.get("success") is False:
            raise RuntimeFailure("Hermes transcription failed")
        transcript = result.get("transcript") or result.get("text")
        if not isinstance(transcript, str) or not transcript.strip():
            raise RuntimeFailure("Hermes returned an empty transcript")
        language = result.get("language")
        return transcript, language if isinstance(language, str) else None

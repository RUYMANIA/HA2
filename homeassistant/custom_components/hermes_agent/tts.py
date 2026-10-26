"""Text-to-speech platform for Hermes Agent."""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Mapping
from typing import Any, override

from homeassistant.components import tts
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import HermesApiError
from .const import (
    CONF_DEFAULT_PROVIDER,
    CONF_DEFAULT_VOICE,
    MAX_TTS_INSTRUCTIONS_LENGTH,
    MAX_TTS_SPEED,
    MIN_TTS_SPEED,
)
from .models import TTSCapability

_LOGGER = logging.getLogger(__name__)
_DEFAULT_LANGUAGE = "en"
_CONTENT_TYPE_EXTENSIONS = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
    "audio/aac": "aac",
}


def _get_value(source: object, *names: str) -> Any:
    """Read the first present mapping key or object attribute."""
    for name in names:
        if isinstance(source, Mapping) and name in source:
            return source[name]
        if hasattr(source, name):
            return getattr(source, name)
    return None


def _platform_capability(capabilities: object, platform: str) -> object:
    """Return a platform capability from supported response layouts."""
    platforms = _get_value(capabilities, "platforms", "capabilities")
    if platforms is not None:
        nested = _get_value(platforms, platform)
        if nested is not None:
            return nested
    value = _get_value(capabilities, platform)
    return capabilities if value is None else value


def _capability_enabled(capabilities: object, platform: str) -> bool:
    """Treat only an explicitly false capability as disabled."""
    capability = _platform_capability(capabilities, platform)
    if capability is False:
        return False
    enabled = _get_value(capability, "enabled", "available", "supported")
    return enabled is not False


def _string_list(value: object) -> list[str]:
    """Return a deduplicated list of non-empty strings."""
    if not isinstance(value, (list, tuple)):
        return []
    return list(dict.fromkeys(item for item in value if isinstance(item, str) and item))


def _tts_value(capabilities: object, capability: object, *names: str) -> Any:
    """Read nested or flat, TTS-prefixed capability metadata."""
    if not isinstance(capability, bool):
        value = _get_value(capability, *names)
        if value is not None:
            return value
    return _get_value(capabilities, *(f"tts_{name}" for name in names))


def _extension(value: str) -> str | None:
    """Normalize either a MIME type or extension for Home Assistant."""
    normalized = value.strip().lower().split(";", 1)[0]
    if normalized in _CONTENT_TYPE_EXTENSIONS:
        return _CONTENT_TYPE_EXTENSIONS[normalized]
    normalized = normalized.removeprefix(".")
    return normalized if re.fullmatch(r"[a-z0-9]{1,8}", normalized) else None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Hermes TTS entity when advertised."""
    data = config_entry.runtime_data
    if not _capability_enabled(data.capabilities, "tts"):
        return
    async_add_entities([HermesTTSEntity(config_entry)])


class HermesTTSEntity(tts.TextToSpeechEntity):
    """Native Home Assistant TTS entity backed by Hermes."""

    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the TTS entity."""
        self._entry = entry
        self._client = entry.runtime_data.client
        self._attr_name = entry.title
        capabilities = entry.runtime_data.capabilities
        capability = _platform_capability(capabilities, "tts")

        languages = _string_list(
            _tts_value(capabilities, capability, "languages", "supported_languages")
        )
        if "*" in languages:
            languages = [language for language in languages if language != "*"] or [
                _DEFAULT_LANGUAGE
            ]
        default_language = _tts_value(
            capabilities, capability, "default_language", "language"
        )
        if not isinstance(default_language, str) or not default_language:
            default_language = languages[0] if languages else _DEFAULT_LANGUAGE
        if not languages:
            languages = [default_language]
        elif default_language not in languages:
            languages.insert(0, default_language)

        option_names = _string_list(
            _tts_value(capabilities, capability, "options", "supported_options")
        )
        self._attr_supported_languages = languages
        self._attr_default_language = default_language
        self._attr_supported_options = option_names or None
        integration_defaults: dict[str, str] = {}
        if "provider" in option_names:
            provider = entry.options.get(CONF_DEFAULT_PROVIDER)
            if isinstance(provider, str) and provider:
                integration_defaults["provider"] = provider
        if "voice" in option_names:
            voice = entry.options.get(CONF_DEFAULT_VOICE)
            if isinstance(voice, str) and voice:
                integration_defaults["voice"] = voice
        self._attr_default_options = integration_defaults or None
        self._supported_option_names = frozenset(option_names)
        self._tts_capability = capability if isinstance(capability, TTSCapability) else None
        self._integration_defaults = integration_defaults
        self._attr_unique_id = f"{entry.entry_id}-tts"

    @property
    @override
    def default_options(self) -> Mapping[str, Any]:
        """Do not reuse an utterance synthesized under an earlier Hermes voice.

        The nonce is only a HA cache-key salt; it is not sent to the provider.
        Hermes resolves provider, voice, speaker and pauses for every synthesis.
        """
        return {**(self._attr_default_options or {}), "_hermes_request": uuid.uuid4().hex}

    @override
    async def async_get_tts_audio(
        self,
        message: str,
        language: str,
        options: dict[str, Any] | None = None,
    ) -> tts.TtsAudioType:
        """Generate speech with conservative, advertised provider options."""
        merged_options: dict[str, Any] = dict(self._integration_defaults)
        if options and self._supported_option_names:
            merged_options.update(
                {
                    key: value
                    for key, value in options.items()
                    if key in self._supported_option_names
                    and isinstance(value, (str, int, float, bool, type(None)))
                }
            )

        try:
            provider = _optional_string(merged_options.get("provider"), "provider")
            voice = _optional_string(merged_options.get("voice"), "voice")
            speed = _optional_speed(merged_options.get("speed"))
            instructions = _optional_string(
                merged_options.get("instructions"), "instructions"
            )
            _validate_controls(self._tts_capability, provider, voice, speed, instructions)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

        try:
            audio_type, data = await self._client.async_tts(
                text=message,
                language=language or None,
                provider=provider,
                voice=voice,
                speed=speed,
                instructions=instructions,
            )
        except (HermesApiError, TypeError, ValueError) as err:
            _LOGGER.error("Hermes TTS request failed (%s)", type(err).__name__)
            raise HomeAssistantError("Hermes Agent could not generate speech") from err

        extension = _extension(audio_type) if isinstance(audio_type, str) else None
        if extension is None or not isinstance(data, bytes) or not data:
            raise HomeAssistantError("Hermes Agent returned invalid speech audio")
        return extension, data


def _optional_string(value: object, name: str) -> str | None:
    """Validate a string control and normalize an empty value to no override."""
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"TTS {name} must be a string")
    return value


def _optional_speed(value: object) -> float | None:
    """Validate and normalize the automation speed control."""
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not MIN_TTS_SPEED <= value <= MAX_TTS_SPEED
    ):
        raise ValueError("TTS speed must be between 0.25 and 4.0")
    return float(value)


def _validate_controls(
    capability: TTSCapability | None,
    provider: str | None,
    voice: str | None,
    speed: float | None,
    instructions: str | None,
) -> None:
    """Reject invalid automation controls before calling the companion."""
    selected = capability.provider(provider) if capability is not None else None
    if capability is not None:
        if provider is not None and provider not in capability.provider_ids:
            raise ValueError("The selected Hermes TTS provider is not advertised")
        if voice is not None and (selected is None or voice not in selected.voice_ids):
            raise ValueError("The selected voice does not belong to the selected provider")
        if speed is not None and selected is not None and not selected.supports_speed:
            raise ValueError("The selected provider does not support TTS speed")
        if instructions is not None and selected is not None and not selected.supports_instructions:
            raise ValueError("The selected provider does not support TTS instructions")
    if instructions is not None and len(instructions) > MAX_TTS_INSTRUCTIONS_LENGTH:
        raise ValueError("TTS instructions are too long")

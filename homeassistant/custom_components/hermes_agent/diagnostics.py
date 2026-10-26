"""Diagnostics for Hermes Agent."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import HermesAgentConfigEntry
from .const import CONF_TOKEN

_REDACT_KEYS = {
    CONF_TOKEN,
    "authorization",
    "api_key",
    "access_token",
    "refresh_token",
    "password",
    "secret",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HermesAgentConfigEntry
) -> dict[str, Any]:
    """Return safe config and capability diagnostics."""
    runtime = entry.runtime_data
    capabilities = runtime.capabilities
    return {
        "entry": async_redact_data(
            {
                "title": entry.title,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            _REDACT_KEYS,
        ),
        "capabilities": {
            "api_version": capabilities.api_version,
            "companion_version": capabilities.companion_version,
            "available_platforms": capabilities.available_platforms,
            "provider_labels": async_redact_data(
                dict(capabilities.provider_labels), _REDACT_KEYS
            ),
            "tts_languages": capabilities.tts_languages,
            "tts_voices": capabilities.tts_voices,
            "tts_default_provider": capabilities.tts.default_provider,
            "tts_providers": [
                {
                    "id": provider.id,
                    "label": provider.label,
                    "default_voice": provider.default_voice,
                    "voices": [
                        {"id": voice.id, "name": voice.name}
                        for voice in provider.voices
                    ],
                    "supports_speed": provider.supports_speed,
                    "supports_instructions": provider.supports_instructions,
                }
                for provider in capabilities.tts.providers
            ],
            "tts_formats": [
                {
                    "content_type": item.content_type,
                    "extension": item.extension,
                    "codec": item.codec,
                    "sample_rate": item.sample_rate,
                    "channels": item.channels,
                }
                for item in capabilities.tts_formats
            ],
            "stt_languages": capabilities.stt_languages,
            "stt_formats": list(capabilities.stt.formats),
            "stt_codecs": list(capabilities.stt.codecs),
            "stt_sample_rates": list(capabilities.stt.sample_rates),
            "stt_channels": list(capabilities.stt.channels),
            "limits": dict(capabilities.limits),
        },
        "loaded_platforms": runtime.platforms,
    }

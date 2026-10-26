"""Speech-to-text platform for Hermes Agent."""

from __future__ import annotations

import logging
import wave
from collections.abc import AsyncIterable, Callable, Mapping
from io import BytesIO
from typing import Any, TypeVar, override

from homeassistant.components import stt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

_LOGGER = logging.getLogger(__name__)
_DEFAULT_MAX_AUDIO_BYTES = 25 * 1024 * 1024
_HARD_MAX_AUDIO_BYTES = 25 * 1024 * 1024
_WAV_HEADER_BYTES = 44
_EnumT = TypeVar("_EnumT")


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


def _enum_list(
    value: object, enum_type: Callable[[Any], _EnumT], fallback: _EnumT
) -> list[_EnumT]:
    """Convert advertised enum values while ignoring unknown future values."""
    if not isinstance(value, (list, tuple)):
        return [fallback]
    result: list[_EnumT] = []
    for item in value:
        try:
            converted = enum_type(item)
        except (TypeError, ValueError):
            continue
        if converted not in result:
            result.append(converted)
    return result or [fallback]


def _stt_value(capabilities: object, capability: object, *names: str) -> Any:
    """Read nested or flat, STT-prefixed capability metadata."""
    if not isinstance(capability, bool):
        value = _get_value(capability, *names)
        if value is not None:
            return value
    return _get_value(capabilities, *(f"stt_{name}" for name in names))


def _languages(capabilities: object, capability: object) -> list[str]:
    """Return advertised STT languages with a conservative fallback."""
    value = _stt_value(capabilities, capability, "languages", "supported_languages")
    if isinstance(value, (list, tuple)):
        result = list(
            dict.fromkeys(
                item
                for item in value
                if isinstance(item, str) and item and item != "*"
            )
        )
        if result:
            return result
    return ["en"]


def _content_type(metadata: stt.SpeechMetadata) -> str:
    """Map Home Assistant speech metadata to the companion content type."""
    audio_format = str(metadata.format)
    codec = str(metadata.codec)
    bit_rate = int(metadata.bit_rate.value)
    sample_rate = int(metadata.sample_rate.value)
    channels = int(metadata.channel.value)
    return (
        f"audio/{audio_format}; codecs=audio/{codec}; samplerate={sample_rate}; "
        f"bitspersample={bit_rate}; channels={channels}"
    )


def _as_provider_audio(metadata: stt.SpeechMetadata, audio: bytes) -> bytes:
    """Wrap headerless PCM frames in a WAV container when HA labels them WAV."""
    if (
        metadata.format != stt.AudioFormats.WAV
        or metadata.codec != stt.AudioCodecs.PCM
        or audio.startswith(b"RIFF")
    ):
        return audio
    output = BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(int(metadata.channel.value))
        wav_file.setsampwidth(int(metadata.bit_rate.value) // 8)
        wav_file.setframerate(int(metadata.sample_rate.value))
        wav_file.writeframes(audio)
    return output.getvalue()


def _transcript(response: object) -> str | None:
    """Extract transcript text from minor companion response variants."""
    if isinstance(response, str):
        return response.strip() or None
    candidate = _get_value(response, "text", "transcript")
    if isinstance(candidate, str):
        return candidate.strip() or None
    if candidate is not None and candidate is not response:
        return _transcript(candidate)
    return None


def _response_succeeded(response: object) -> bool:
    """Interpret explicit failure markers while allowing text-only responses."""
    success = _get_value(response, "success")
    if success is False:
        return False
    state = _get_value(response, "result", "status", "state")
    return not (
        isinstance(state, str) and state.lower() in {"error", "failed", "failure"}
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Hermes STT entity when advertised."""
    data = config_entry.runtime_data
    if not _capability_enabled(data.capabilities, "stt"):
        return
    async_add_entities([HermesSTTEntity(config_entry)])


class HermesSTTEntity(stt.SpeechToTextEntity):
    """Native Home Assistant STT entity backed by Hermes."""

    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the STT entity."""
        self._client = entry.runtime_data.client
        self._attr_name = entry.title
        capabilities = entry.runtime_data.capabilities
        capability = _platform_capability(capabilities, "stt")
        self._supported_languages = _languages(capabilities, capability)
        self._supported_formats = _enum_list(
            _stt_value(capabilities, capability, "formats", "supported_formats"),
            stt.AudioFormats,
            stt.AudioFormats.WAV,
        )
        self._supported_codecs = _enum_list(
            _stt_value(capabilities, capability, "codecs", "supported_codecs"),
            stt.AudioCodecs,
            stt.AudioCodecs.PCM,
        )
        self._supported_bit_rates = _enum_list(
            _stt_value(capabilities, capability, "bit_rates", "supported_bit_rates"),
            stt.AudioBitRates,
            stt.AudioBitRates.BITRATE_16,
        )
        self._supported_sample_rates = _enum_list(
            _stt_value(
                capabilities, capability, "sample_rates", "supported_sample_rates"
            ),
            stt.AudioSampleRates,
            stt.AudioSampleRates.SAMPLERATE_16000,
        )
        self._supported_channels = _enum_list(
            _stt_value(capabilities, capability, "channels", "supported_channels"),
            stt.AudioChannels,
            stt.AudioChannels.CHANNEL_MONO,
        )
        max_bytes = _stt_value(
            capabilities,
            capability,
            "max_audio_bytes",
            "max_upload_bytes",
            "max_stt_bytes",
        )
        self._max_audio_bytes = (
            min(max_bytes, _HARD_MAX_AUDIO_BYTES)
            if isinstance(max_bytes, int)
            and not isinstance(max_bytes, bool)
            and max_bytes > 0
            else _DEFAULT_MAX_AUDIO_BYTES
        )
        self._attr_unique_id = f"{entry.entry_id}-stt"

    @property
    @override
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return self._supported_languages

    @property
    @override
    def supported_formats(self) -> list[stt.AudioFormats]:
        """Return supported container formats."""
        return self._supported_formats

    @property
    @override
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        """Return supported codecs."""
        return self._supported_codecs

    @property
    @override
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        """Return supported bit depths."""
        return self._supported_bit_rates

    @property
    @override
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        """Return supported sample rates."""
        return self._supported_sample_rates

    @property
    @override
    def supported_channels(self) -> list[stt.AudioChannels]:
        """Return supported channel counts."""
        return self._supported_channels

    @override
    async def async_process_audio_stream(
        self,
        metadata: stt.SpeechMetadata,
        stream: AsyncIterable[bytes],
    ) -> stt.SpeechResult:
        """Buffer bounded audio, add a WAV header when needed, and transcribe."""
        audio = bytearray()
        raw_limit = max(0, self._max_audio_bytes - _WAV_HEADER_BYTES)
        try:
            async for chunk in stream:
                if not isinstance(chunk, bytes):
                    raise TypeError("audio stream yielded non-bytes")
                if len(audio) + len(chunk) > raw_limit:
                    _LOGGER.warning(
                        "Hermes STT audio exceeded the configured upload limit"
                    )
                    return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
                audio.extend(chunk)
            if not audio:
                return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

            provider_audio = _as_provider_audio(metadata, bytes(audio))
            result = await self._client.async_stt(
                audio=provider_audio,
                content_type=_content_type(metadata),
                language=metadata.language or None,
                sample_rate=int(metadata.sample_rate.value),
                channels=int(metadata.channel.value),
            )
            text = _transcript(result)
            if text is None or not _response_succeeded(result):
                return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
        except Exception as err:  # noqa: BLE001 - HA STT must return ERROR
            _LOGGER.error("Hermes STT request failed (%s)", type(err).__name__)
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

        return stt.SpeechResult(text, stt.SpeechResultState.SUCCESS)

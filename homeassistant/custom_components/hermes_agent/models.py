"""Typed data models shared by Hermes Agent platforms."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .api import HermesAgentClient


@dataclass(frozen=True, slots=True)
class AudioFormat:
    """A media format advertised by the companion."""

    content_type: str
    extension: str
    codec: str | None = None
    sample_rate: int | None = None
    channels: int | None = None
    bit_rate: int | None = None


@dataclass(frozen=True, slots=True)
class ConversationCapability:
    """Conversation capability consumed by the entity platform."""

    available: bool
    languages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TTSVoice:
    """A safe voice identifier and display name."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class TTSProvider:
    """Safe TTS provider metadata advertised by the companion."""

    id: str
    label: str
    default_voice: str | None = None
    voices: tuple[TTSVoice, ...] = ()
    supports_speed: bool = False
    supports_instructions: bool = False

    @property
    def voice_ids(self) -> tuple[str, ...]:
        """Return this provider's advertised voice identifiers."""
        return tuple(voice.id for voice in self.voices)


@dataclass(frozen=True, slots=True)
class TTSCapability:
    """Text-to-speech capability consumed by the entity platform."""

    available: bool
    languages: tuple[str, ...] = ()
    voices: tuple[str, ...] = ()
    formats: tuple[AudioFormat, ...] = ()
    options: tuple[str, ...] = ()
    default_language: str | None = None
    default_options: Mapping[str, str | int | float | bool | None] = field(
        default_factory=dict
    )
    default_provider: str | None = None
    providers: tuple[TTSProvider, ...] = ()

    def provider(self, provider_id: str | None) -> TTSProvider | None:
        """Resolve an explicit provider or the advertised Hermes default."""
        effective_id = provider_id or self.default_provider
        return next((item for item in self.providers if item.id == effective_id), None)

    @property
    def provider_ids(self) -> tuple[str, ...]:
        """Return advertised provider identifiers."""
        return tuple(provider.id for provider in self.providers)

    @property
    def advertised_voice_ids(self) -> tuple[str, ...]:
        """Return unique voice identifiers in stable provider order."""
        return tuple(dict.fromkeys(voice.id for item in self.providers for voice in item.voices))


@dataclass(frozen=True, slots=True)
class STTCapability:
    """Speech-to-text capability consumed by the entity platform."""

    available: bool
    languages: tuple[str, ...] = ()
    formats: tuple[str, ...] = ()
    codecs: tuple[str, ...] = ()
    bit_rates: tuple[int, ...] = ()
    sample_rates: tuple[int, ...] = ()
    channels: tuple[int, ...] = ()
    max_audio_bytes: int | None = None


@dataclass(frozen=True, slots=True)
class HermesCapabilities:
    """Validated, forward-compatible API v1 capability contract."""

    api_version: str
    companion_version: str | None
    conversation: ConversationCapability
    tts: TTSCapability
    stt: STTCapability
    provider_labels: Mapping[str, str] = field(default_factory=dict)
    limits: Mapping[str, int] = field(default_factory=dict)

    @property
    def tts_languages(self) -> tuple[str, ...]:
        """Return advertised TTS languages."""
        return self.tts.languages

    @property
    def tts_voices(self) -> tuple[str, ...]:
        """Return advertised TTS voices."""
        return self.tts.advertised_voice_ids or self.tts.voices

    @property
    def tts_formats(self) -> tuple[AudioFormat, ...]:
        """Return advertised TTS response formats."""
        return self.tts.formats

    @property
    def stt_languages(self) -> tuple[str, ...]:
        """Return advertised STT languages."""
        return self.stt.languages

    @property
    def available_platforms(self) -> tuple[str, ...]:
        """Return supported Home Assistant platform names in stable order."""
        return tuple(
            name
            for name, available in (
                ("conversation", self.conversation.available),
                ("tts", self.tts.available),
                ("stt", self.stt.available),
            )
            if available
        )


@dataclass(frozen=True, slots=True)
class HealthResult:
    """Safe liveness information."""

    status: str
    api_version: str | None = None
    companion_version: str | None = None


@dataclass(frozen=True, slots=True)
class InferenceMessage:
    """A bounded inference message."""

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Inference response returned to the conversation platform."""

    text: str
    conversation_id: str | None = None
    model: str | None = None
    provider: str | None = None


@dataclass(frozen=True, slots=True)
class TTSResult:
    """Generated speech and its media metadata."""

    audio: bytes
    content_type: str
    extension: str


@dataclass(frozen=True, slots=True)
class STTResult:
    """Transcription response."""

    text: str
    language: str | None = None


@dataclass(slots=True)
class HermesAgentRuntimeData:
    """Runtime data exposed to platform setup functions."""

    client: HermesAgentClient
    capabilities: HermesCapabilities
    platforms: tuple[str, ...]


def optional_string(value: Any) -> str | None:
    """Return a non-empty string, otherwise None."""
    return value if isinstance(value, str) and value else None

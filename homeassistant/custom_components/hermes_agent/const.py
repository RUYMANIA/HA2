"""Constants for the Hermes Agent integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "hermes_agent"
NAME: Final = "Hermes Agent"

CONF_URL: Final = "url"
CONF_TOKEN: Final = "token"  # noqa: S105 - config key, not a credential
CONF_VERIFY_TLS: Final = "verify_tls"
CONF_REQUEST_TIMEOUT: Final = "request_timeout"
CONF_INFERENCE_TIMEOUT: Final = "inference_timeout"
CONF_TTS_TIMEOUT: Final = "tts_timeout"
CONF_STT_TIMEOUT: Final = "stt_timeout"
CONF_SYSTEM_PROMPT: Final = "system_prompt"
CONF_DEFAULT_VOICE: Final = "default_voice"
CONF_DEFAULT_PROVIDER: Final = "default_provider"
CONF_ENABLE_CONVERSATION: Final = "enable_conversation"
CONF_ENABLE_TTS: Final = "enable_tts"
CONF_ENABLE_STT: Final = "enable_stt"

DEFAULT_VERIFY_TLS: Final = True
DEFAULT_REQUEST_TIMEOUT: Final = 10.0
DEFAULT_INFERENCE_TIMEOUT: Final = 60.0
DEFAULT_TTS_TIMEOUT: Final = 60.0
DEFAULT_STT_TIMEOUT: Final = 120.0
DEFAULT_SYSTEM_PROMPT: Final = ""
DEFAULT_VOICE: Final = ""
DEFAULT_PROVIDER: Final = ""
MIN_TTS_SPEED: Final = 0.25
MAX_TTS_SPEED: Final = 4.0
MAX_TTS_INSTRUCTIONS_LENGTH: Final = 2000
MIN_TIMEOUT: Final = 1.0
MAX_TIMEOUT: Final = 300.0

API_VERSION_MAJOR: Final = 1
MAX_ERROR_BODY: Final = 8 * 1024
MAX_JSON_RESPONSE: Final = 512 * 1024
DEFAULT_MAX_STT_BYTES: Final = 25 * 1024 * 1024

PLATFORM_CONVERSATION: Final = "conversation"
PLATFORM_TTS: Final = "tts"
PLATFORM_STT: Final = "stt"
SUPPORTED_PLATFORMS: Final = (
    PLATFORM_CONVERSATION,
    PLATFORM_TTS,
    PLATFORM_STT,
)

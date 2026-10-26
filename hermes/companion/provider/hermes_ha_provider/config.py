"""Configuration and bind-safety validation."""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

_PLACEHOLDER_TOKENS = {
    "change-me",
    "changeme",
    "hermes-token",
    "replace-me",
    "token",
    "your-token-here",
}


class ConfigurationError(ValueError):
    """Raised for unsafe or invalid service configuration."""


def _is_loopback(host: str) -> bool:
    normalized = host.strip().strip("[]").lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _is_strong_token(token: str) -> bool:
    lowered = token.strip().lower()
    return len(token.encode()) >= 32 and lowered not in _PLACEHOLDER_TOKENS and len(set(token)) >= 8


def _int_env(environ: dict[str, str], name: str, default: int) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be positive")
    return value


def _validated_api_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ConfigurationError(
            "HERMES_API_URL must be an HTTP(S) base URL without credentials, query, or fragment"
        )
    return value.strip().rstrip("/")


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated companion settings."""

    token: str
    host: str = "127.0.0.1"
    port: int = 8765
    hermes_source: Path | None = None
    hermes_home: Path | None = None
    hermes_profile: str | None = None
    hermes_api_url: str | None = None
    hermes_api_token: str | None = None
    hermes_api_session_key: str = "home-assistant"
    temp_dir: Path | None = None
    json_limit: int = 256 * 1024
    inference_text_limit: int = 32 * 1024
    tts_text_limit: int = 32 * 1024
    stt_upload_limit: int = 25 * 1024 * 1024
    tts_audio_limit: int = 25 * 1024 * 1024
    concurrency: int = 4
    request_timeout: float = 120.0
    busy_timeout: float = 0.05

    def __post_init__(self) -> None:
        if not self.token:
            raise ConfigurationError("HERMES_HA_TOKEN is required")
        if not _is_loopback(self.host) and not _is_strong_token(self.token):
            raise ConfigurationError(
                "non-loopback binds require a strong token of at least 32 bytes"
            )
        if not 1 <= self.port <= 65535:
            raise ConfigurationError("port must be between 1 and 65535")
        positive = (
            self.json_limit,
            self.inference_text_limit,
            self.tts_text_limit,
            self.stt_upload_limit,
            self.tts_audio_limit,
            self.concurrency,
        )
        if any(value <= 0 for value in positive):
            raise ConfigurationError("limits and concurrency must be positive")
        if self.json_limit > 256 * 1024:
            raise ConfigurationError("JSON limit cannot exceed 256 KiB")
        if self.inference_text_limit > 32 * 1024 or self.tts_text_limit > 32 * 1024:
            raise ConfigurationError("text limits cannot exceed 32 KiB")
        if self.request_timeout <= 0 or self.busy_timeout <= 0:
            raise ConfigurationError("timeouts must be positive")
        if bool(self.hermes_api_url) != bool(self.hermes_api_token):
            raise ConfigurationError(
                "HERMES_API_URL and HERMES_API_TOKEN must be configured together"
            )
        if self.hermes_api_url is not None:
            object.__setattr__(self, "hermes_api_url", _validated_api_url(self.hermes_api_url))
            if len((self.hermes_api_token or "").encode()) < 16:
                raise ConfigurationError("HERMES_API_TOKEN must be at least 16 bytes")
        if (
            not self.hermes_api_session_key
            or len(self.hermes_api_session_key) > 128
            or any(char in self.hermes_api_session_key for char in "\r\n")
        ):
            raise ConfigurationError("HERMES_API_SESSION_KEY is invalid")

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        """Load settings from environment variables."""
        env = dict(os.environ if environ is None else environ)
        source = env.get("HERMES_SOURCE")
        home = env.get("HERMES_HOME")
        temp_dir = env.get("HERMES_HA_TEMP_DIR")
        try:
            timeout = float(env.get("HERMES_HA_REQUEST_TIMEOUT", "120"))
            busy_timeout = float(env.get("HERMES_HA_BUSY_TIMEOUT", "0.05"))
        except ValueError as exc:
            raise ConfigurationError("timeouts must be numeric") from exc
        return cls(
            token=env.get("HERMES_HA_TOKEN", ""),
            host=env.get("HERMES_HA_HOST", "127.0.0.1"),
            port=_int_env(env, "HERMES_HA_PORT", 8765),
            hermes_source=Path(source).expanduser() if source else None,
            hermes_home=Path(home).expanduser() if home else None,
            hermes_profile=env.get("HERMES_PROFILE"),
            hermes_api_url=env.get("HERMES_API_URL") or None,
            hermes_api_token=env.get("HERMES_API_TOKEN") or None,
            hermes_api_session_key=env.get(
                "HERMES_API_SESSION_KEY", "home-assistant"
            ),
            temp_dir=Path(temp_dir).expanduser() if temp_dir else None,
            json_limit=_int_env(env, "HERMES_HA_JSON_LIMIT", 256 * 1024),
            inference_text_limit=_int_env(env, "HERMES_HA_INFERENCE_TEXT_LIMIT", 32 * 1024),
            tts_text_limit=_int_env(env, "HERMES_HA_TTS_TEXT_LIMIT", 32 * 1024),
            stt_upload_limit=_int_env(env, "HERMES_HA_STT_UPLOAD_LIMIT", 25 * 1024 * 1024),
            tts_audio_limit=_int_env(env, "HERMES_HA_TTS_AUDIO_LIMIT", 25 * 1024 * 1024),
            concurrency=_int_env(env, "HERMES_HA_CONCURRENCY", 4),
            request_timeout=timeout,
            busy_timeout=busy_timeout,
        )

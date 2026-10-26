"""Hermes Agent Home Assistant integration lifecycle."""

from __future__ import annotations

from typing import Any, TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AuthenticationError, HermesAgentClient, HermesApiError
from .const import (
    CONF_ENABLE_CONVERSATION,
    CONF_ENABLE_STT,
    CONF_ENABLE_TTS,
    CONF_INFERENCE_TIMEOUT,
    CONF_REQUEST_TIMEOUT,
    CONF_STT_TIMEOUT,
    CONF_TOKEN,
    CONF_TTS_TIMEOUT,
    CONF_URL,
    CONF_VERIFY_TLS,
    DEFAULT_INFERENCE_TIMEOUT,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_STT_TIMEOUT,
    DEFAULT_TTS_TIMEOUT,
    DEFAULT_VERIFY_TLS,
)
from .models import HermesAgentRuntimeData

HermesAgentConfigEntry: TypeAlias = ConfigEntry[HermesAgentRuntimeData]

_PLATFORM_ENUM = {
    "conversation": Platform.CONVERSATION,
    "tts": Platform.TTS,
    "stt": Platform.STT,
}
_OPTION_KEYS = {
    "conversation": CONF_ENABLE_CONVERSATION,
    "tts": CONF_ENABLE_TTS,
    "stt": CONF_ENABLE_STT,
}


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration namespace."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: HermesAgentConfigEntry
) -> bool:
    """Set up and forward only capabilities enabled by the companion."""
    client = _client_for_entry(hass, entry)
    try:
        capabilities = await client.async_capabilities()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed("Hermes companion rejected the token") from err
    except HermesApiError as err:
        raise ConfigEntryNotReady("Unable to query Hermes capabilities") from err

    platforms = tuple(
        platform
        for platform in capabilities.available_platforms
        if entry.options.get(_OPTION_KEYS[platform], True)
    )
    entry.runtime_data = HermesAgentRuntimeData(
        client=client,
        capabilities=capabilities,
        platforms=platforms,
    )
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(
        entry, [_PLATFORM_ENUM[platform] for platform in platforms]
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: HermesAgentConfigEntry
) -> bool:
    """Unload exactly the platforms that were forwarded."""
    runtime = entry.runtime_data
    platforms = [_PLATFORM_ENUM[platform] for platform in runtime.platforms]
    if not platforms:
        return True
    return await hass.config_entries.async_unload_platforms(entry, platforms)


async def _async_update_listener(
    hass: HomeAssistant, entry: HermesAgentConfigEntry
) -> None:
    """Reload an entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _client_for_entry(
    hass: HomeAssistant, entry: HermesAgentConfigEntry
) -> HermesAgentClient:
    """Build a client from config-entry data and non-secret options."""
    options = entry.options
    verify_tls = bool(
        options.get(
            CONF_VERIFY_TLS,
            entry.data.get(CONF_VERIFY_TLS, DEFAULT_VERIFY_TLS),
        )
    )
    session = async_get_clientsession(hass, verify_ssl=verify_tls)
    return HermesAgentClient(
        session,
        entry.data[CONF_URL],
        entry.data[CONF_TOKEN],
        request_timeout=float(
            options.get(CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT)
        ),
        inference_timeout=float(
            options.get(CONF_INFERENCE_TIMEOUT, DEFAULT_INFERENCE_TIMEOUT)
        ),
        tts_timeout=float(options.get(CONF_TTS_TIMEOUT, DEFAULT_TTS_TIMEOUT)),
        stt_timeout=float(options.get(CONF_STT_TIMEOUT, DEFAULT_STT_TIMEOUT)),
    )

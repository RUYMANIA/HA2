"""Config flow for Hermes Agent."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AuthenticationError,
    CannotConnectError,
    HermesAgentClient,
    HermesApiError,
    InvalidUrlError,
    UnsupportedApiError,
    normalize_url,
)
from .const import (
    CONF_DEFAULT_PROVIDER,
    CONF_DEFAULT_VOICE,
    CONF_ENABLE_CONVERSATION,
    CONF_ENABLE_STT,
    CONF_ENABLE_TTS,
    CONF_INFERENCE_TIMEOUT,
    CONF_REQUEST_TIMEOUT,
    CONF_STT_TIMEOUT,
    CONF_SYSTEM_PROMPT,
    CONF_TOKEN,
    CONF_TTS_TIMEOUT,
    CONF_URL,
    CONF_VERIFY_TLS,
    DEFAULT_INFERENCE_TIMEOUT,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_STT_TIMEOUT,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TTS_TIMEOUT,
    DEFAULT_VERIFY_TLS,
    DOMAIN,
    MAX_TIMEOUT,
    MIN_TIMEOUT,
    NAME,
)
from .models import HermesAgentRuntimeData, HermesCapabilities


def _user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    values = defaults or {}
    url_field = (
        vol.Required(CONF_URL, default=values[CONF_URL])
        if values.get(CONF_URL)
        else vol.Required(CONF_URL)
    )
    return vol.Schema(
        {
            url_field: str,
            vol.Required(CONF_TOKEN, default=values.get(CONF_TOKEN, "")): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
            vol.Optional(CONF_NAME, default=values.get(CONF_NAME, NAME)): str,
            vol.Optional(
                CONF_VERIFY_TLS,
                default=values.get(CONF_VERIFY_TLS, DEFAULT_VERIFY_TLS),
            ): bool,
        }
    )


TIMEOUT_VALIDATOR = vol.All(
    vol.Coerce(float), vol.Range(min=MIN_TIMEOUT, max=MAX_TIMEOUT)
)


class HermesAgentConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle setup and token replacement."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a Hermes provider companion."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                url = normalize_url(user_input[CONF_URL])
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                capabilities = await self._probe(
                    url,
                    user_input[CONF_TOKEN],
                    bool(user_input.get(CONF_VERIFY_TLS, DEFAULT_VERIFY_TLS)),
                )
            except InvalidUrlError:
                errors["base"] = "invalid_url"
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except UnsupportedApiError:
                errors["base"] = "unsupported_api"
            except HermesApiError:
                errors["base"] = "unknown"
            except Exception:  # noqa: BLE001 - config flows must render safe errors
                errors["base"] = "unknown"
            else:
                if not capabilities.available_platforms:
                    errors["base"] = "no_capabilities"
                else:
                    title = user_input.get(CONF_NAME, NAME).strip() or NAME
                    return self.async_create_entry(
                        title=title,
                        data={
                            CONF_URL: url,
                            CONF_TOKEN: user_input[CONF_TOKEN],
                            CONF_NAME: title,
                            CONF_VERIFY_TLS: bool(
                                user_input.get(CONF_VERIFY_TLS, DEFAULT_VERIFY_TLS)
                            ),
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Begin bearer-token replacement."""
        self._reauth_entry_data = entry_data
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and save a replacement token."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            token = user_input[CONF_TOKEN]
            try:
                capabilities = await self._probe(
                    entry.data[CONF_URL],
                    token,
                    bool(
                        entry.options.get(
                            CONF_VERIFY_TLS,
                            entry.data.get(CONF_VERIFY_TLS, DEFAULT_VERIFY_TLS),
                        )
                    ),
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except UnsupportedApiError:
                errors["base"] = "unsupported_api"
            except HermesApiError:
                errors["base"] = "unknown"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                if not capabilities.available_platforms:
                    errors["base"] = "no_capabilities"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={CONF_TOKEN: token},
                    )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def _probe(
        self, url: str, token: str, verify_tls: bool
    ) -> HermesCapabilities:
        session = async_get_clientsession(self.hass, verify_ssl=verify_tls)
        client = HermesAgentClient(session, url, token)
        await client.async_health()
        return await client.async_capabilities()

    @staticmethod
    def async_get_options_flow(config_entry: Any) -> OptionsFlow:
        """Return the options flow handler."""
        return HermesAgentOptionsFlow()


class HermesAgentOptionsFlow(OptionsFlow):
    """Manage non-secret runtime options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit timeouts, prompt, voice, TLS, and enabled platforms."""
        entry = self.config_entry
        runtime = getattr(entry, "runtime_data", None)
        capabilities = (
            runtime.capabilities
            if isinstance(runtime, HermesAgentRuntimeData)
            else None
        )
        current = entry.options
        data = entry.data
        errors: dict[str, str] = {}
        if user_input is not None and capabilities is not None:
            provider = user_input.get(CONF_DEFAULT_PROVIDER, "")
            voice = user_input.get(CONF_DEFAULT_VOICE, "")
            selected = capabilities.tts.provider(provider or None)
            if provider and provider not in capabilities.tts.provider_ids:
                errors["base"] = "invalid_tts_provider_voice"
            elif voice and (selected is None or voice not in selected.voice_ids):
                errors["base"] = "invalid_tts_provider_voice"
        if user_input is not None and not errors:
            return self.async_create_entry(title="", data=user_input)

        values = user_input if user_input is not None else current
        schema: dict[Any, Any] = {
            vol.Optional(
                CONF_VERIFY_TLS,
                default=values.get(
                    CONF_VERIFY_TLS,
                    data.get(CONF_VERIFY_TLS, DEFAULT_VERIFY_TLS),
                ),
            ): bool,
            vol.Optional(
                CONF_REQUEST_TIMEOUT,
                default=values.get(CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT),
            ): TIMEOUT_VALIDATOR,
            vol.Optional(
                CONF_INFERENCE_TIMEOUT,
                default=values.get(CONF_INFERENCE_TIMEOUT, DEFAULT_INFERENCE_TIMEOUT),
            ): TIMEOUT_VALIDATOR,
            vol.Optional(
                CONF_TTS_TIMEOUT,
                default=values.get(CONF_TTS_TIMEOUT, DEFAULT_TTS_TIMEOUT),
            ): TIMEOUT_VALIDATOR,
            vol.Optional(
                CONF_STT_TIMEOUT,
                default=values.get(CONF_STT_TIMEOUT, DEFAULT_STT_TIMEOUT),
            ): TIMEOUT_VALIDATOR,
            vol.Optional(
                CONF_SYSTEM_PROMPT,
                default=values.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT),
            ): str,
        }
        if (
            capabilities is not None
            and "provider" in capabilities.tts.options
            and capabilities.tts.providers
        ):
            provider_options = [{"value": "", "label": "Hermes default"}]
            provider_options.extend(
                {"value": item.id, "label": item.label}
                for item in capabilities.tts.providers
            )
            schema[
                vol.Optional(
                    CONF_DEFAULT_PROVIDER,
                    default=values.get(CONF_DEFAULT_PROVIDER, ""),
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=provider_options)
            )
        voice_ids = (
            capabilities.tts.advertised_voice_ids if capabilities is not None else ()
        )
        if capabilities is not None and "voice" in capabilities.tts.options and voice_ids:
            voice_options = [{"value": "", "label": "Hermes default"}]
            voice_options.extend({"value": item, "label": item} for item in voice_ids)
            schema[
                vol.Optional(
                    CONF_DEFAULT_VOICE,
                    default=values.get(CONF_DEFAULT_VOICE, ""),
                )
            ] = selector.SelectSelector(selector.SelectSelectorConfig(options=voice_options))
        availability = {
            CONF_ENABLE_CONVERSATION: capabilities is None
            or capabilities.conversation.available,
            CONF_ENABLE_TTS: capabilities is None or capabilities.tts.available,
            CONF_ENABLE_STT: capabilities is None or capabilities.stt.available,
        }
        for key, available in availability.items():
            if available:
                schema[vol.Optional(key, default=values.get(key, True))] = bool

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema), errors=errors
        )

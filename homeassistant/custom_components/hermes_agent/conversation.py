"""Conversation platform for Hermes Agent."""

from __future__ import annotations

import logging
import json
from collections.abc import Mapping
from typing import Any, Literal, override

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import HermesApiError

_LOGGER = logging.getLogger(__name__)


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
        for name in (platform, "inference"):
            nested = _get_value(platforms, name)
            if nested is not None:
                return nested
    for name in (platform, "inference"):
        value = _get_value(capabilities, name)
        if value is not None:
            return value
    return capabilities


def _capability_enabled(capabilities: object, platform: str) -> bool:
    """Treat only an explicitly false capability as disabled."""
    platforms = _get_value(capabilities, "platforms", "capabilities")
    for source in (platforms, capabilities):
        if source is None:
            continue
        for name in (platform, "inference"):
            direct = _get_value(source, name)
            if direct is False:
                return False
    capability = _platform_capability(capabilities, platform)
    if capability is False:
        return False
    enabled = _get_value(capability, "enabled", "available", "supported")
    return enabled is not False


def _response_text(response: object) -> str | None:
    """Extract generated text from minor companion response variants."""
    if isinstance(response, str):
        return response.strip() or None

    candidate = _get_value(response, "text", "content", "output_text", "response")
    if isinstance(candidate, str):
        return candidate.strip() or None
    if candidate is not None and candidate is not response:
        return _response_text(candidate)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Hermes conversation entity."""
    data = config_entry.runtime_data
    if not _capability_enabled(data.capabilities, "conversation"):
        return
    async_add_entities([HermesConversationEntity(config_entry)])


class HermesConversationEntity(conversation.ConversationEntity):
    """Native Home Assistant conversation entity backed by Hermes."""

    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the conversation entity."""
        self._entry = entry
        self._client = entry.runtime_data.client
        self._attr_name = entry.title
        self._attr_unique_id = f"{entry.entry_id}-conversation"

    @property
    @override
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        capabilities = self._entry.runtime_data.capabilities
        capability = _platform_capability(capabilities, "conversation")
        languages = (
            _get_value(capability, "languages", "supported_languages")
            if not isinstance(capability, bool)
            else None
        )
        if languages is None:
            languages = _get_value(
                capabilities,
                "conversation_languages",
                "inference_languages",
            )
        if isinstance(languages, (list, tuple)):
            result = [item for item in languages if isinstance(item, str) and item]
            if result:
                return result
        return MATCH_ALL

    @override
    async def async_added_to_hass(self) -> None:
        """Register this entity as the config entry's conversation agent."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self._entry, self)

    @override
    async def async_will_remove_from_hass(self) -> None:
        """Unregister the conversation agent."""
        conversation.async_unset_agent(self.hass, self._entry)
        await super().async_will_remove_from_hass()

    @override
    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process one turn with bounded Home Assistant conversation history."""
        messages: list[dict[str, str]] = []
        prompt = self._entry.options.get("system_prompt") or self._entry.options.get(
            "prompt"
        )
        if isinstance(prompt, str) and prompt.strip():
            messages.append({"role": "system", "content": prompt.strip()})

        # Home Assistant has already appended the current user turn. Keep a bounded
        # history so Assist remains conversational without creating a hidden
        # server-side session store in the companion.
        for item in chat_log.content[-20:]:
            content = getattr(item, "content", None)
            role = getattr(item, "role", None)
            if (
                role in {"system", "user", "assistant"}
                and isinstance(content, str)
                and content.strip()
            ):
                messages.append({"role": role, "content": content})

        response = intent.IntentResponse(language=user_input.language)
        try:
            # Native start_conversation seeds an assistant turn from this satellite.
            # The companion's canonical API ignores body history for an explicit id:
            # carry that ONE opener as quoted context in the new user turn, never system.
            prior = [item for item in chat_log.content[:-1] if getattr(item, "role", None) in {"user", "assistant"}]
            native_first = (bool(user_input.satellite_id) and len(prior) == 1
                and getattr(prior[0], "role", None) == "assistant"
                and getattr(prior[0], "agent_id", None) == user_input.satellite_id
                and getattr(prior[0], "content", None) == user_input.extra_system_prompt
                and isinstance(user_input.extra_system_prompt, str)
                and 0 < len(user_input.extra_system_prompt) <= 400)
            if native_first:
                messages[-1] = {"role": "user", "content":
                    "Contexto del terminal compartido. Responde a la persona sin atribuirle identidad. "
                    + json.dumps({"invitacion_emitida": user_input.extra_system_prompt,
                                  "respuesta_de_la_persona": user_input.text}, ensure_ascii=False)}
            result = await self._client.async_inference(
                messages=messages,
                conversation_id=user_input.conversation_id,
                language=user_input.language,
                **({"bootstrap_session": True} if native_first else {}),
            )
            text = _response_text(result)
            if text is None:
                raise ValueError("empty inference response")
        except (HermesApiError, TypeError, ValueError) as err:
            _LOGGER.error("Hermes conversation request failed (%s)", type(err).__name__)
            response.async_set_error(
                intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
                "Hermes Agent could not process the request.",
            )
            return conversation.ConversationResult(
                response=response,
                conversation_id=user_input.conversation_id,
            )

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(agent_id=user_input.agent_id, content=text)
        )
        return conversation.async_get_result_from_chat_log(user_input, chat_log)

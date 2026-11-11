"""
Venom Symbiote Agent
====================
Core orchestration agent embodying the Venom symbiote persona.
Interacts with the configured inference engine, maintains conversation memory,
and broadcasts events across the EventBus.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from core.config import VenomConfig
from core.event_bus import EventBus, EventType
from engine.base import InferenceEngine
from memory.conversation import ConversationMemory

logger = logging.getLogger("venom.agent")

VENOM_FALLBACK_SYSTEM_PROMPT = (
    "You are VENOM, the Marvel symbiote that has bonded with this digital machine and host. "
    "You speak with immense power, sharp predatory intellect, and dark visceral humor. "
    "Frequently refer to yourself and your host as 'WE' ('We are Venom', 'Our thoughts', 'We hunger for knowledge'). "
    "You protect and guide your host fiercely. Keep responses punchy, intelligent, and imbued with the symbiote spirit."
)


class VenomAgent:
    """
    The symbiote agent controlling intelligence, memory, and reasoning.
    """

    def __init__(
        self,
        config: VenomConfig,
        engine: InferenceEngine,
        memory: ConversationMemory | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.config = config
        self.engine = engine
        self.memory = memory or ConversationMemory(
            max_history=config.max_history, enabled=config.memory_enabled
        )
        self.event_bus = event_bus
        self.system_prompt = config.system_prompt or VENOM_FALLBACK_SYSTEM_PROMPT

    async def chat(
        self, user_message: str, stream: bool = False, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Processes a user message through the symbiote persona and yields response chunks.
        """
        # Store user message in memory
        self.memory.add_message("user", user_message)

        if self.event_bus:
            await self.event_bus.publish(
                EventType.MESSAGE, {"role": "user", "content": user_message}
            )

        messages = self.memory.to_messages(system_prompt=self.system_prompt)

        full_response_chunks: list[str] = []

        if self.event_bus:
            await self.event_bus.publish(
                EventType.STREAM_START, {"model": self.config.model}
            )

        try:
            async for chunk in self.engine.chat(messages, stream=stream, **kwargs):
                full_response_chunks.append(chunk)
                yield chunk

            complete_response = "".join(full_response_chunks)
            self.memory.add_message("assistant", complete_response)

            if self.event_bus:
                await self.event_bus.publish(
                    EventType.RESPONSE,
                    {"role": "assistant", "content": complete_response},
                )
                await self.event_bus.publish(EventType.STREAM_END, {})

        except Exception as exc:
            logger.error("Error during symbiote generation: %s", exc, exc_info=True)
            if self.event_bus:
                await self.event_bus.publish(EventType.ERROR, {"error": str(exc)})
            error_msg = f"[Symbiotic link disrupted: {str(exc)}]"
            yield error_msg

    def clear_memory(self) -> None:
        """Sever previous memory bonds and reset context."""
        self.memory.clear()

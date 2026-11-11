"""
Conversation Memory Module
==========================
Manages in-memory dialogue history with FIFO truncation and LLM format conversion.
"""

from __future__ import annotations

import datetime
from typing import Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Represents a single turn in the conversation."""
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Text content of the message")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


class ConversationMemory:
    """
    In-memory conversation history buffer.
    """

    def __init__(self, max_history: int = 50, enabled: bool = True) -> None:
        self.max_history = max_history
        self.enabled = enabled
        self._history: list[ChatMessage] = []

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a new message to the memory."""
        msg = ChatMessage(role=role, content=content)
        if not self.enabled:
            return msg

        self._history.append(msg)
        # Evict oldest if exceeding capacity
        if len(self._history) > self.max_history:
            self._history.pop(0)
        return msg

    def get_history(self, limit: int | None = None) -> list[ChatMessage]:
        """Return historical messages, optionally limited to the most recent."""
        if limit is not None and limit > 0:
            return self._history[-limit:]
        return list(self._history)

    def to_messages(self, system_prompt: str | None = None) -> list[dict[str, str]]:
        """
        Export conversation as a list of dicts suitable for LLM APIs:
        [{"role": "system", "content": "..."}, {"role": "user", ...}]
        """
        result: list[dict[str, str]] = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})

        for msg in self._history:
            result.append({"role": msg.role, "content": msg.content})

        return result

    def clear(self) -> None:
        """Clear all conversation history."""
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)

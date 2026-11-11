"""
Venom Event Bus
===============
Thread-safe, async-capable pub/sub event bus for internal Venom component
communication.  Handlers are ordinary coroutines; the bus dispatches events
concurrently via ``asyncio.gather``.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List

logger = logging.getLogger("venom.event_bus")


class EventType(str, Enum):
    """Canonical event types used throughout the Venom system."""

    MESSAGE = "MESSAGE"
    RESPONSE = "RESPONSE"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    ERROR = "ERROR"
    STREAM_START = "STREAM_START"
    STREAM_END = "STREAM_END"
    SYSTEM = "SYSTEM"


# A handler is any async callable that accepts a single data argument.
Handler = Callable[[Any], Coroutine[Any, Any, None]]


class EventBus:
    """
    Async publish/subscribe event bus.

    Example usage::

        bus = EventBus()

        async def on_message(data):
            print("Received:", data)

        bus.subscribe(EventType.MESSAGE, on_message)
        await bus.publish(EventType.MESSAGE, {"text": "Hello"})
        bus.unsubscribe(EventType.MESSAGE, on_message)
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    # ── Subscription management ───────────────────────────────────────────────

    def subscribe(self, event_type: EventType | str, handler: Handler) -> None:
        """Register *handler* to be called whenever *event_type* is published."""
        key = str(event_type)
        if handler not in self._handlers[key]:
            self._handlers[key].append(handler)
            logger.debug("Subscribed %s to event '%s'", handler.__name__, key)

    def unsubscribe(self, event_type: EventType | str, handler: Handler) -> None:
        """Remove *handler* from the subscriber list for *event_type*."""
        key = str(event_type)
        try:
            self._handlers[key].remove(handler)
            logger.debug("Unsubscribed %s from event '%s'", handler.__name__, key)
        except ValueError:
            logger.warning(
                "Handler %s was not subscribed to event '%s'", handler.__name__, key
            )

    # ── Publishing ────────────────────────────────────────────────────────────

    async def publish(self, event_type: EventType | str, data: Any = None) -> None:
        """
        Dispatch *data* to all handlers subscribed to *event_type*.

        All handlers are awaited concurrently.  Exceptions raised by individual
        handlers are caught and logged so that they don't prevent other handlers
        from running.
        """
        key = str(event_type)
        handlers = list(self._handlers.get(key, []))
        if not handlers:
            return

        logger.debug("Publishing event '%s' to %d handler(s)", key, len(handlers))

        async def _safe_call(h: Handler) -> None:
            try:
                await h(data)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Handler %s raised an error for event '%s': %s",
                    h.__name__,
                    key,
                    exc,
                )

        await asyncio.gather(*(_safe_call(h) for h in handlers))

    # ── Utility ───────────────────────────────────────────────────────────────

    def clear(self, event_type: EventType | str | None = None) -> None:
        """Remove all subscriptions, optionally scoped to a single *event_type*."""
        if event_type is None:
            self._handlers.clear()
        else:
            self._handlers.pop(str(event_type), None)

    def handler_count(self, event_type: EventType | str) -> int:
        """Return the number of handlers registered for *event_type*."""
        return len(self._handlers.get(str(event_type), []))


# Module-level singleton — import and use directly in other modules.
event_bus: EventBus = EventBus()

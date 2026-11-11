"""
Inference Engine — Abstract Base Class
=======================================
Defines the common contract that every Venom inference engine must satisfy.
Concrete engines (Ollama, OpenAI, …) subclass ``InferenceEngine`` and implement
the three abstract methods below.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator


class InferenceEngine(ABC):
    """
    Abstract base class for Venom inference engines.

    Every engine **must** implement:

    * :meth:`chat` — send a list of messages and receive a response (streaming
      or not).
    * :meth:`health_check` — verify that the upstream service is reachable.
    * :meth:`get_models` — enumerate models available on this backend.
    """

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Send *messages* to the inference backend and yield the response.

        Parameters
        ----------
        messages:
            Conversation history as a list of ``{"role": ..., "content": ...}``
            dicts.
        stream:
            When ``True`` the generator yields successive text chunks as they
            arrive from the model; when ``False`` it yields exactly one chunk
            containing the complete response.
        **kwargs:
            Engine-specific overrides such as ``temperature``, ``max_tokens``,
            etc.

        Yields
        ------
        str
            Incremental (streaming) or complete (non-streaming) response text.
        """
        # ``yield`` makes this a generator — required by the type system even
        # though it is abstract and will never be called directly.
        yield  # type: ignore[misc]

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Return ``True`` if the backend is reachable and ready, ``False``
        otherwise.
        """

    @abstractmethod
    async def get_models(self) -> list[str]:
        """
        Return a list of model identifier strings available on this backend.
        The list may be empty when the backend is unavailable.
        """

    # ── Shared helpers ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

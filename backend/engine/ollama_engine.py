"""
Ollama Inference Engine
========================
Wraps the Ollama REST API (http://localhost:11434 by default) to provide chat
completions with optional token-level streaming via Server-Sent Events / NDJSON.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from core.config import VenomConfig
from engine.base import InferenceEngine

logger = logging.getLogger("venom.engine.ollama")


class OllamaEngine(InferenceEngine):
    """
    Inference engine backed by a local Ollama server.

    Uses ``httpx.AsyncClient`` directly against the Ollama REST API so we have
    fine-grained control over timeouts and streaming without depending on the
    ``ollama`` Python SDK's higher-level abstractions.
    """

    def __init__(self, config: VenomConfig) -> None:
        self.config = config
        self.base_url = config.ollama_url.rstrip("/")
        self.model = config.model
        self._client: httpx.AsyncClient | None = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_client(self) -> httpx.AsyncClient:
        """Return (or lazily create) the shared async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=5.0),
            )
        return self._client

    async def _close(self) -> None:
        """Cleanly close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── InferenceEngine interface ──────────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Call ``POST /api/chat`` and yield response text chunks.

        When *stream* is ``False`` the entire JSON response is awaited before a
        single chunk is yielded.  When *stream* is ``True`` each NDJSON line
        emitted by Ollama is decoded and its ``message.content`` field is
        yielded incrementally.

        Parameters
        ----------
        messages:
            Full conversation history (system + user + assistant turns).
        stream:
            Enable token-level streaming.
        **kwargs:
            Forwarded verbatim into the Ollama request body (e.g.
            ``temperature``, ``top_p``, ``num_predict``).
        """
        client = self._get_client()
        payload: dict[str, Any] = {
            "model": kwargs.pop("model", self.model),
            "messages": messages,
            "stream": stream,
            **kwargs,
        }

        try:
            if stream:
                async with client.stream("POST", "/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        err_text = err_bytes.decode(errors="ignore")
                        logger.error("Ollama API error %d: %s", response.status_code, err_text)
                        if "not found" in err_text.lower() or response.status_code == 404:
                            yield f"[Ollama Error: Model '{payload['model']}' not found. Run 'ollama pull {payload['model']}' in your terminal, or switch to Gemini in .env]"
                        else:
                            yield f"[Ollama Error {response.status_code}: {err_text[:200]}]"
                        return

                    async for raw_line in response.aiter_lines():
                        if not raw_line.strip():
                            continue
                        try:
                            data = json.loads(raw_line)
                        except json.JSONDecodeError:
                            logger.warning("Unparseable SSE line: %s", raw_line[:120])
                            continue

                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content

                        if data.get("done", False):
                            break
            else:
                response = await client.post("/api/chat", json=payload)
                if response.status_code != 200:
                    yield f"[Ollama Error {response.status_code}: {response.text[:200]}]"
                    return
                data = response.json()
                yield data.get("message", {}).get("content", "")

        except httpx.RequestError as exc:
            error_msg = f"Ollama connection error: {exc}. Is Ollama running on {self.base_url}?"
            logger.error(error_msg)
            yield f"[Ollama Offline: {error_msg}]"

    async def health_check(self) -> bool:
        """
        Verify the Ollama server is reachable by hitting ``GET /api/tags``.

        Returns
        -------
        bool
            ``True`` when the server responds with HTTP 200, ``False``
            otherwise.
        """
        try:
            client = self._get_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama health check failed: %s", exc)
            return False

    async def get_models(self) -> list[str]:
        """
        Return an asynchronous snapshot of available Ollama models.
        """
        try:
            client = self._get_client()
            resp = await client.get("/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                names = [m["name"] for m in models]
                return names if names else [self.model]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch Ollama model list: %s", exc)
        return [self.model]

    def __repr__(self) -> str:
        return f"<OllamaEngine url={self.base_url!r} model={self.model!r}>"

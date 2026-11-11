"""
OpenAI Inference Engine
=======================
Connects to OpenAI Chat Completions API with token-level streaming.
Uses HTTPX directly (no external 'openai' SDK dependency required).
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from core.config import VenomConfig
from engine.base import InferenceEngine

logger = logging.getLogger("venom.engine.openai")

OPENAI_API_BASE = "https://api.openai.com/v1"


class OpenAIEngine(InferenceEngine):
    """
    Inference engine backed by the OpenAI Chat Completions API.
    """

    def __init__(self, config: VenomConfig) -> None:
        self.config = config
        self.model = config.model
        self.api_key = config.openai_api_key

        if not self.api_key:
            logger.warning("VENOM_OPENAI_API_KEY is not set.")

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "[Error: VENOM_OPENAI_API_KEY is not configured in .env]"
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": kwargs.get("temperature", 0.7),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                if stream:
                    async with client.stream(
                        "POST",
                        f"{OPENAI_API_BASE}/chat/completions",
                        headers=headers,
                        json=payload,
                    ) as resp:
                        if resp.status_code != 200:
                            err_body = await resp.aread()
                            yield f"[OpenAI Error {resp.status_code}: {err_body.decode(errors='ignore')[:200]}]"
                            return

                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if line.startswith("data: "):
                                raw = line[6:].strip()
                                if raw == "[DONE]":
                                    break
                                try:
                                    chunk_data = json.loads(raw)
                                    delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                                except Exception:
                                    pass
                else:
                    resp = await client.post(
                        f"{OPENAI_API_BASE}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        yield text
                    else:
                        yield f"[OpenAI Error {resp.status_code}: {resp.text[:200]}]"

            except Exception as exc:
                logger.error("OpenAI request error: %s", exc)
                yield f"[OpenAI Connection Error: {str(exc)}]"

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{OPENAI_API_BASE}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def get_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]

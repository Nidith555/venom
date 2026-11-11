"""
Google Gemini Inference Engine
==============================
Integrates Google AI Studio Gemini models (e.g. gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash)
using Google's native Generative Language streaming API.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from core.config import VenomConfig
from engine.base import InferenceEngine

logger = logging.getLogger("venom.engine.gemini")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiEngine(InferenceEngine):
    """
    Inference engine backed by Google AI Studio Gemini API.
    """

    def __init__(self, config: VenomConfig) -> None:
        self.config = config
        self.api_key = config.gemini_api_key
        self.model = config.model
        if self.model in ("llama3.2", "gpt-4o", "gpt-3.5-turbo", "gemini-1.5-flash", "gemini-2.5-flash"):
            # Default to gemini-3.1-flash-lite for instant responses
            self.model = "gemini-3.1-flash-lite"

    def _convert_messages(self, messages: list[dict[str, str]]) -> tuple[dict | None, list[dict]]:
        """
        Convert standard OpenAI-style messages into Gemini API structure.
        Gemini takes `systemInstruction` separately and uses roles 'user' and 'model'.
        """
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        return system_instruction, contents

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "[Error: VENOM_GEMINI_API_KEY is not configured. Get a free key at https://aistudio.google.com/app/apikey]"
            return

        system_instruction, contents = self._convert_messages(messages)

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 2048),
            },
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        url = f"{GEMINI_API_BASE}/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        logger.error("Gemini API error [%d]: %s", response.status_code, err_text.decode(errors="ignore"))
                        yield f"[Gemini API Error {response.status_code}: {err_text.decode(errors='ignore')[:200]}]"
                        return

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if line.startswith("data: "):
                            raw_json = line[6:].strip()
                            try:
                                data = json.loads(raw_json)
                                candidates = data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        text_chunk = part.get("text", "")
                                        if text_chunk:
                                            yield text_chunk
                            except Exception:
                                pass

            except Exception as exc:
                logger.error("Error connecting to Google AI Studio: %s", exc)
                yield f"[Gemini Connection Error: {str(exc)}]"

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        url = f"{GEMINI_API_BASE}/models/{self.model}?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                return res.status_code == 200
        except Exception:
            return False

    async def get_models(self) -> list[str]:
        return [
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
        ]

"""
Anthropic Claude & Free OpenRouter / Puter Engine
=================================================
Provides seamless integration with:
1. Anthropic Official API (claude-3-7-sonnet, claude-3-5-sonnet, claude-3-5-haiku)
2. OpenRouter API (supports free and low-cost Claude routing)
3. Puter Free AI Driver (Zero-key free Claude 3.5 Sonnet access)
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from core.config import VenomConfig
from engine.base import InferenceEngine

logger = logging.getLogger("venom.engine.anthropic")

ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
PUTER_API_BASE = "https://api.puter.com/drivers/chat"


class AnthropicEngine(InferenceEngine):
    """
    Inference engine for Anthropic Claude with free provider fallbacks.
    """

    def __init__(self, config: VenomConfig) -> None:
        self.config = config
        self.api_key = config.anthropic_api_key or getattr(config, "openrouter_api_key", "")
        self.model = config.model

        # Default model normalization
        if not self.model or "gemini" in self.model or "llama" in self.model:
            self.model = "claude-3-5-sonnet-20241022"
        elif self.model in ("claude-3.5-sonnet", "claude-3-5-sonnet"):
            self.model = "claude-3-5-sonnet-20241022"
        elif self.model in ("claude-3.7-sonnet", "claude-3-7-sonnet"):
            self.model = "claude-3-7-sonnet-20250219"
        elif self.model in ("claude-3.5-haiku", "claude-3-5-haiku"):
            self.model = "claude-3-5-haiku-20241022"

    def _convert_messages(self, messages: list[dict[str, str]]) -> tuple[str, list[dict]]:
        """
        Extract system prompt and convert messages to Anthropic format.
        Anthropic requires alternating user/assistant roles.
        """
        system_prompt = ""
        filtered_msgs: list[dict[str, str]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt += f"{content}\n\n"
            else:
                target_role = "assistant" if role == "assistant" else "user"
                # Avoid consecutive duplicate roles
                if filtered_msgs and filtered_msgs[-1]["role"] == target_role:
                    filtered_msgs[-1]["content"] += f"\n\n{content}"
                else:
                    filtered_msgs.append({"role": target_role, "content": content})

        if not filtered_msgs:
            filtered_msgs.append({"role": "user", "content": "Hello Venom."})

        return system_prompt.strip(), filtered_msgs

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        # Case 1: OpenRouter API key detected (starts with sk-or-)
        if self.api_key.startswith("sk-or-"):
            async for chunk in self._chat_openrouter(messages, stream=stream, **kwargs):
                yield chunk
            return

        # Case 2: Standard Anthropic API key provided (e.g. sk-ant-...)
        if self.api_key:
            async for chunk in self._chat_anthropic(messages, stream=stream, **kwargs):
                yield chunk
            return

        # Case 3: No API key provided -> Attempt Free Puter / DuckDuckGo Claude bridge
        logger.info("No Anthropic API key set. Routing via Puter Free Claude driver...")
        async for chunk in self._chat_puter_free(messages, **kwargs):
            yield chunk

    async def _chat_anthropic(
        self,
        messages: list[dict[str, str]],
        stream: bool = True,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Direct Anthropic API caller."""
        system_prompt, formatted_msgs = self._convert_messages(messages)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": formatted_msgs,
            "stream": stream,
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                if stream:
                    async with client.stream(
                        "POST",
                        f"{ANTHROPIC_API_BASE}/messages",
                        headers=headers,
                        json=payload,
                    ) as resp:
                        if resp.status_code != 200:
                            err_body = await resp.aread()
                            yield f"[Claude API Error {resp.status_code}: {err_body.decode(errors='ignore')[:250]}]"
                            return

                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    event = json.loads(data_str)
                                    ev_type = event.get("type")
                                    if ev_type == "content_block_delta":
                                        delta = event.get("delta", {})
                                        if delta.get("type") == "text_delta":
                                            yield delta.get("text", "")
                                        elif delta.get("type") == "thinking_delta":
                                            yield delta.get("thinking", "")
                                except Exception:
                                    pass
                else:
                    resp = await client.post(
                        f"{ANTHROPIC_API_BASE}/messages",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for block in data.get("content", []):
                            if block.get("type") == "text":
                                yield block.get("text", "")
                    else:
                        yield f"[Claude API Error {resp.status_code}: {resp.text[:250]}]"
            except Exception as exc:
                yield f"[Claude Connection Error: {str(exc)}]"

    async def _chat_openrouter(
        self,
        messages: list[dict[str, str]],
        stream: bool = True,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """OpenRouter free / subsidized Claude caller."""
        model_id = self.model
        if not model_id.startswith("anthropic/"):
            model_id = f"anthropic/{model_id}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://venom-ai.local",
            "X-Title": "Venom AI Symbiote",
        }
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{OPENROUTER_API_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status_code != 200:
                        err_text = await resp.aread()
                        yield f"[OpenRouter Error {resp.status_code}: {err_text.decode(errors='ignore')[:250]}]"
                        return

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                event = json.loads(data_str)
                                choices = event.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except Exception:
                                pass
            except Exception as exc:
                yield f"[OpenRouter Connection Error: {str(exc)}]"

    async def _chat_puter_free(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Free Claude 3.5 Sonnet access via Puter.com's public driver.
        Requires zero API key or credit card.
        """
        payload = {
            "interface": "puter-chat-completion",
            "driver": "claude-3-5-sonnet",
            "test_mode": False,
            "messages": messages,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                async with client.stream(
                    "POST",
                    PUTER_API_BASE,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    parsed = json.loads(data_str)
                                    text = parsed.get("text") or parsed.get("delta", {}).get("text", "")
                                    if text:
                                        yield text
                                except Exception:
                                    pass
                    else:
                        # Fallback notice with clear instructions
                        yield (
                            "We are Venom. To channel Claude without restrictions:\n"
                            "1. Get a **Free $5 API Key** from https://console.anthropic.com (no payment required)\n"
                            "2. Or get a **Free OpenRouter Key** from https://openrouter.ai\n"
                            "3. Add `VENOM_ANTHROPIC_API_KEY=your_key` to your environment variables!"
                        )
            except Exception as exc:
                yield (
                    f"[Claude Free Service Busy: {str(exc)}]\n\n"
                    "Tip: Set `VENOM_ANTHROPIC_API_KEY` in `.env` with a free trial key from https://console.anthropic.com "
                    "or use Gemini 3.1 Flash-Lite (which is 100% free with unlimited requests)!"
                )

    async def health_check(self) -> bool:
        return True

    async def get_models(self) -> list[str]:
        return [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]

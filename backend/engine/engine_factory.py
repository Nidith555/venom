"""
Engine Factory Module
=====================
Constructs the appropriate InferenceEngine instance dynamically based on configuration.
Uses lazy imports so missing optional provider SDKs (e.g. openai) do not crash other engines.
"""

from __future__ import annotations

import logging
from core.config import VenomConfig
from engine.base import InferenceEngine

logger = logging.getLogger("venom.engine.factory")


def create_engine(config: VenomConfig) -> InferenceEngine:
    """
    Factory function to instantiate the configured inference engine.

    Supported engines:
    - gemini: Google AI Studio Gemini API (native HTTPX streaming)
    - ollama: Local Ollama server (HTTPX streaming)
    - openai: OpenAI Cloud API (or compatible proxies)
    """
    engine_name = config.engine.lower().strip()
    logger.info("Initializing inference engine: %s (model: %s)", engine_name, config.model)

    if engine_name == "gemini":
        from engine.gemini_engine import GeminiEngine
        return GeminiEngine(config)

    elif engine_name in ("anthropic", "claude"):
        from engine.anthropic_engine import AnthropicEngine
        return AnthropicEngine(config)

    elif engine_name == "ollama":
        from engine.ollama_engine import OllamaEngine
        return OllamaEngine(config)

    elif engine_name == "openai":
        try:
            from engine.openai_engine import OpenAIEngine
            return OpenAIEngine(config)
        except ImportError:
            raise ImportError(
                "The 'openai' package is not installed. Run 'pip install openai' "
                "or switch VENOM_ENGINE to 'gemini' or 'ollama' in your .env file."
            )

    else:
        logger.warning(
            "Unknown engine '%s' requested. Defaulting to Ollama.", engine_name
        )
        from engine.ollama_engine import OllamaEngine
        return OllamaEngine(config)

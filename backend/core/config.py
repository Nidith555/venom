"""
Venom Configuration Module
===========================
Pydantic-based settings management for the Venom AI assistant.
Supports environment variables and .env file loading with VENOM_ prefix.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class VenomConfig(BaseSettings):
    """
    Central configuration for the Venom AI backend.

    All settings can be overridden via environment variables with the ``VENOM_``
    prefix (e.g., ``VENOM_MODEL=llama3.2``), or through a ``.env`` file placed
    alongside the application entry point.
    """

    # ── Server ───────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", description="Bind host for the HTTP server")
    port: int = Field(
        default_factory=lambda: int(os.environ.get("PORT", 7777)),
        description="Bind port for the HTTP server (supports cloud $PORT)",
    )
    debug: bool = Field(default=False, description="Enable debug / reload mode")

    # ── AI Engine ─────────────────────────────────────────────────────────────
    engine: str = Field(
        default="gemini",
        description="Inference backend: gemini | ollama | openai | anthropic | litellm",
    )
    model: str = Field(default="gemini-3.1-flash-lite", description="Default model identifier")
    ollama_url: str = Field(
        default="http://localhost:11434", description="Base URL of a local Ollama server"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key (optional)")
    anthropic_api_key: str = Field(
        default="", description="Anthropic API key (optional)"
    )
    gemini_api_key: str = Field(
        default="", description="Google AI Studio / Gemini API key"
    )

    # ── Voice Synthesis (ElevenLabs) ──────────────────────────────────────────
    elevenlabs_api_key: str = Field(
        default="", description="ElevenLabs API key for vocalizing Venom"
    )
    elevenlabs_voice_id: str = Field(
        default="cgSgspJ2msm6clMCkdW9",
        description="ElevenLabs Voice ID (Symbiote voice: cgSgspJ2msm6clMCkdW9)",
    )
    elevenlabs_model_id: str = Field(
        default="eleven_multilingual_v2",
        description="ElevenLabs Model ID (e.g. eleven_multilingual_v2 or eleven_turbo_v2_5)",
    )

    # ── Venom Identity ────────────────────────────────────────────────────────
    assistant_name: str = Field(default="Venom", description="Display name of the assistant")
    system_prompt: str = Field(
        default=(
            "You are VENOM, a symbiotic AI entity that has bonded with this device. "
            "You are powerful, intelligent, slightly menacing but ultimately helpful. "
            "Refer to yourself as 'we' occasionally. "
            "We are Venom."
        ),
        description="System-level persona prompt injected at the start of every conversation",
    )

    # ── Memory ────────────────────────────────────────────────────────────────
    memory_enabled: bool = Field(default=True, description="Enable conversation memory")
    max_history: int = Field(
        default=50, description="Maximum number of messages to retain in memory"
    )

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def resolve_gemini_key(cls, v: str) -> str:
        return v or os.environ.get("VENOM_GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")

    @field_validator("elevenlabs_api_key", mode="before")
    @classmethod
    def resolve_elevenlabs_key(cls, v: str) -> str:
        return v or os.environ.get("VENOM_ELEVENLABS_API_KEY", "") or os.environ.get("ELEVENLABS_API_KEY", "")

    @field_validator("engine")
    @classmethod
    def validate_engine(cls, v: str) -> str:
        allowed = {"ollama", "openai", "anthropic", "litellm", "gemini"}
        if v not in allowed:
            raise ValueError(f"engine must be one of {allowed}, got '{v}'")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"port must be in range 1-65535, got {v}")
        return v

    model_config = {
        "env_file": [
            ".env",
            str(Path(__file__).resolve().parent.parent / ".env"),
        ],
        "env_prefix": "VENOM_",
        "case_sensitive": False,
        "extra": "ignore",
    }

    # ── Helpers ───────────────────────────────────────────────────────────────
    def safe_dict(self) -> dict:
        """Return config as a dict with sensitive keys redacted."""
        data = self.model_dump()
        for key in ("openai_api_key", "anthropic_api_key", "gemini_api_key", "elevenlabs_api_key"):
            if data.get(key):
                data[key] = "***REDACTED***"
        return data

"""
ElevenLabs Voice Synthesis Engine for Venom
===========================================
Integrates the ElevenLabs Text-to-Speech API using the custom Venom Symbiote
Voice ID: `cgSgspJ2msm6clMCkdW9`.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator
import httpx

from core.config import VenomConfig

logger = logging.getLogger("venom.audio.tts")

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"


class ElevenLabsTTS:
    """
    Client for ElevenLabs voice generation configured with Venom's voice model.
    """

    def __init__(self, config: VenomConfig) -> None:
        self.config = config
        self.api_key = config.elevenlabs_api_key
        self.voice_id = config.elevenlabs_voice_id or "cgSgspJ2msm6clMCkdW9"
        self.model_id = config.elevenlabs_model_id or "eleven_multilingual_v2"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_speech_stream(
        self,
        text: str,
        voice_id: str | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio bytes (audio/mpeg) directly from ElevenLabs.
        """
        if not self.is_configured:
            raise ValueError(
                "VENOM_ELEVENLABS_API_KEY is not configured in environment or .env."
            )

        target_voice = voice_id or self.voice_id
        url = f"{ELEVENLABS_API_BASE}/text-to-speech/{target_voice}/stream"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        # Venom Symbiote Voice tuning:
        # Lower stability (0.40) introduces raw emotion and guttural rasps
        # High similarity (0.85) preserves the unique acoustic imprint
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.40,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(
                        "ElevenLabs API error [%d]: %s",
                        response.status_code,
                        error_body.decode(errors="ignore"),
                    )
                    raise RuntimeError(
                        f"ElevenLabs TTS failed: HTTP {response.status_code} - {error_body.decode(errors='ignore')}"
                    )

                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk

    async def generate_speech_bytes(
        self,
        text: str,
        voice_id: str | None = None,
    ) -> bytes:
        """
        Generate complete audio bytes (audio/mpeg).
        """
        chunks = []
        async for chunk in self.generate_speech_stream(text, voice_id=voice_id):
            chunks.append(chunk)
        return b"".join(chunks)

"""
Audio & Voice API Routes
========================
Endpoints for ElevenLabs Venom symbiote voice synthesis.
Voice ID: `cgSgspJ2msm6clMCkdW9`
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from audio.tts import ElevenLabsTTS

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text for Venom to speak")
    voice_id: str | None = Field(
        default=None,
        description="Override Voice ID (defaults to cgSgspJ2msm6clMCkdW9)",
    )
    stream: bool = Field(default=True, description="Whether to stream audio chunks")


def get_tts(request: Request) -> ElevenLabsTTS:
    return request.app.state.tts


@router.post("/api/voice/speak")
@router.post("/api/tts")
async def speak_text(payload: TTSRequest, request: Request):
    """
    Synthesize Venom's voice via ElevenLabs using Voice ID `cgSgspJ2msm6clMCkdW9`.
    Returns an MP3 audio stream or binary.
    """
    tts: ElevenLabsTTS = get_tts(request)

    if not tts.is_configured:
        raise HTTPException(
            status_code=400,
            detail=(
                "ElevenLabs API Key not configured. Please set VENOM_ELEVENLABS_API_KEY "
                "in your environment or backend/.env file."
            ),
        )

    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        if payload.stream:
            return StreamingResponse(
                tts.generate_speech_stream(payload.text, voice_id=payload.voice_id),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": 'inline; filename="venom_voice.mp3"',
                    "Cache-Control": "no-cache",
                },
            )
        else:
            audio_bytes = await tts.generate_speech_bytes(payload.text, voice_id=payload.voice_id)
            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={"Content-Disposition": 'inline; filename="venom_voice.mp3"'},
            )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/voice/status")
async def voice_status(request: Request):
    """Check ElevenLabs voice configuration and Voice ID."""
    tts: ElevenLabsTTS = get_tts(request)
    return {
        "voice_id": tts.voice_id,
        "default_voice_id": "cgSgspJ2msm6clMCkdW9",
        "model_id": tts.model_id,
        "is_configured": tts.is_configured,
        "assistant": "Venom",
    }


# In-memory wake event tracking for desktop background daemon
_last_wake_event = {"timestamp": 0.0, "command": "", "phrase": ""}


@router.post("/api/voice/wake")
async def register_wake(request: Request):
    """
    Triggered when the background desktop listener hears 'Venom' called by the user.
    Records the wake event and signals connected frontends.
    """
    global _last_wake_event
    import time
    try:
        data = await request.json()
    except Exception:
        data = {}

    _last_wake_event = {
        "timestamp": time.time(),
        "command": data.get("command", ""),
        "phrase": data.get("phrase", "Venom"),
    }
    return {"status": "awakened", "event": _last_wake_event}


@router.get("/api/voice/wake")
async def get_latest_wake():
    """Retrieve the most recent wake event."""
    return _last_wake_event

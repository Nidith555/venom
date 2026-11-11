"""
System API Routes
=================
Endpoints for system vitals, model enumeration, and configuration diagnostics.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from agent.venom_agent import VenomAgent

router = APIRouter()


@router.get("/api/health")
async def health_check(request: Request):
    """Vitals check for Venom symbiote server and underlying engine."""
    agent: VenomAgent = request.app.state.agent
    engine_healthy = await agent.engine.health_check()
    return {
        "status": "alive" if engine_healthy else "degraded",
        "symbiote": "VENOM",
        "engine": agent.config.engine,
        "engine_reachable": engine_healthy,
        "model": agent.config.model,
        "memory_items": len(agent.memory),
        "voice_id": agent.config.elevenlabs_voice_id,
        "voice_configured": bool(agent.config.elevenlabs_api_key),
    }


@router.get("/api/models")
async def list_models(request: Request):
    """Retrieve all available models reported by the current inference engine."""
    agent: VenomAgent = request.app.state.agent
    try:
        res = agent.engine.get_models()
        if hasattr(res, "__await__"):
            models = await res
        else:
            models = res
    except Exception as exc:
        models = [agent.config.model]
    return {
        "current_model": agent.config.model,
        "engine": agent.config.engine,
        "available_models": models,
    }


@router.get("/api/config")
async def get_config(request: Request):
    """Safe view of current configuration parameters without revealing secrets."""
    agent: VenomAgent = request.app.state.agent
    cfg = agent.config
    return {
        "assistant_name": cfg.assistant_name,
        "engine": cfg.engine,
        "model": cfg.model,
        "ollama_url": cfg.ollama_url,
        "has_openai_key": bool(cfg.openai_api_key),
        "has_anthropic_key": bool(cfg.anthropic_api_key),
        "has_gemini_key": bool(cfg.gemini_api_key),
        "memory_enabled": cfg.memory_enabled,
        "max_history": cfg.max_history,
        "elevenlabs_voice_id": cfg.elevenlabs_voice_id,
        "has_elevenlabs_key": bool(cfg.elevenlabs_api_key),
        "debug": cfg.debug,
    }

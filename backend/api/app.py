"""
Venom FastAPI Application
=========================
Initializes the FastAPI application, lifespans, CORS middleware, and mounts routers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import VenomConfig
from core.event_bus import EventBus
from engine.engine_factory import create_engine
from memory.conversation import ConversationMemory
from agent.venom_agent import VenomAgent
from audio.tts import ElevenLabsTTS
from api.routes.chat import router as chat_router
from api.routes.system import router as system_router
from api.routes.audio import router as audio_router
from api.routes.files import router as files_router

logger = logging.getLogger("venom.app")


def create_app(config: VenomConfig | None = None) -> FastAPI:
    """Application factory for Venom."""
    cfg = config or VenomConfig()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Initializing Venom Symbiotic Kernel...")
        event_bus = EventBus()
        engine = create_engine(cfg)
        memory = ConversationMemory(
            max_history=cfg.max_history, enabled=cfg.memory_enabled
        )
        agent = VenomAgent(
            config=cfg, engine=engine, memory=memory, event_bus=event_bus
        )
        tts = ElevenLabsTTS(config=cfg)

        app.state.config = cfg
        app.state.event_bus = event_bus
        app.state.engine = engine
        app.state.memory = memory
        app.state.agent = agent
        app.state.tts = tts

        logger.info(
            "Symbiote online. Bonded to engine=%s with model=%s | Voice ID: %s",
            cfg.engine,
            cfg.model,
            cfg.elevenlabs_voice_id,
        )
        yield

        # Shutdown
        logger.info("Severing symbiote bonds...")
        if hasattr(engine, "_close"):
            await engine._close()

    app = FastAPI(
        title="Venom Symbiotic AI",
        description="Marvel-inspired local-first AI assistant backend based on OpenJarvis principles.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Allow cross-origin requests for web frontends
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router)
    app.include_router(system_router)
    app.include_router(audio_router)
    app.include_router(files_router)

    # Mount built frontend static assets if available
    dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if dist_dir.exists():
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api/") or full_path.startswith("ws/"):
                raise HTTPException(status_code=404, detail="Not found")
            file_path = dist_dir / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(dist_dir / "index.html"))

    return app

"""
Chat API Routes
===============
Endpoints for chat completions, OpenAI compatibility, history, and WebSocket streaming.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent.venom_agent import VenomAgent

router = APIRouter()


class SimpleChatRequest(BaseModel):
    message: str = Field(..., description="User prompt to the symbiote")
    stream: bool = Field(default=True, description="Whether to stream the response chunks")
    model: str | None = Field(default=None, description="Model override")
    files: list[dict[str, Any]] | None = Field(default=None, description="Attached files metadata & content")


class SimpleChatResponse(BaseModel):
    response: str
    role: str = "assistant"
    model: str


class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[OpenAIMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None


def get_agent(request: Request) -> VenomAgent:
    return request.app.state.agent


@router.post("/api/chat")
async def chat_endpoint(payload: SimpleChatRequest, request: Request):
    """
    Standard chat endpoint supporting both text response and SSE streaming.
    """
    agent: VenomAgent = get_agent(request)

    if payload.stream:
        async def event_generator() -> AsyncGenerator[str, None]:
            async for chunk in agent.chat(payload.message, stream=True, files=payload.files, model=payload.model):
                # Send server-sent event
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        chunks = []
        async for chunk in agent.chat(payload.message, stream=False, files=payload.files, model=payload.model):
            chunks.append(chunk)
        full_text = "".join(chunks)
        return SimpleChatResponse(
            response=full_text,
            role="assistant",
            model=agent.config.model,
        )


@router.get("/api/chat/history")
async def get_history(request: Request):
    """Retrieve full or recent conversation history."""
    agent: VenomAgent = get_agent(request)
    return {"history": agent.memory.get_history()}


@router.delete("/api/chat/history")
async def clear_history(request: Request):
    """Wipe current conversation history."""
    agent: VenomAgent = get_agent(request)
    agent.clear_memory()
    return {"status": "cleared", "message": "Symbiote memory slate wiped clean."}


@router.post("/v1/chat/completions")
async def openai_completions(payload: OpenAIChatCompletionRequest, request: Request):
    """
    OpenAI-compatible /v1/chat/completions endpoint.
    Allows standard OpenAI libraries and tools to connect directly to Venom.
    """
    agent: VenomAgent = get_agent(request)
    model = payload.model or agent.config.model
    created_ts = int(time.time())
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    # Extract latest user message
    last_user_msg = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), ""
    )

    if payload.stream:
        async def sse_stream():
            async for chunk in agent.chat(last_user_msg, stream=True):
                data = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(data)}\n\n"

            # Terminal chunk
            done_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(done_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(sse_stream(), media_type="text/event-stream")

    else:
        chunks = []
        async for chunk in agent.chat(last_user_msg, stream=False):
            chunks.append(chunk)
        full_text = "".join(chunks)

        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": full_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(last_user_msg.split()),
                "completion_tokens": len(full_text.split()),
                "total_tokens": len(last_user_msg.split()) + len(full_text.split()),
            },
        }


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Real-time streaming WebSocket endpoint.
    Client sends JSON: {"message": "..."}
    Server streams: {"type": "chunk", "content": "..."}
    Terminal event: {"type": "done"}
    """
    await websocket.accept()
    agent: VenomAgent = websocket.app.state.agent

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                prompt = payload.get("message", "")
            except Exception:
                prompt = data

            if not prompt.strip():
                continue

            await websocket.send_json({"type": "start", "model": agent.config.model})

            async for chunk in agent.chat(prompt, stream=True):
                await websocket.send_json({"type": "chunk", "content": chunk})

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "error": str(exc)})
        except Exception:
            pass

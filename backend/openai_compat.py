from __future__ import annotations

import json
import time
from typing import Any

from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from agents.lobechat_adapter import lobe_model_list, respond_to_lobechat


class OpenAIMessage(BaseModel):
    role: str
    content: str | list[dict[str, Any]] = ""


class OpenAIChatRequest(BaseModel):
    model: str = "interview-agent-local"
    messages: list[OpenAIMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    tools: list[dict[str, Any]] | None = None


def models_response() -> dict[str, Any]:
    return {"object": "list", "data": lobe_model_list()}


def chat_completions_response(payload: OpenAIChatRequest):
    messages = [{"role": item.role, "content": _message_content(item.content)} for item in payload.messages]
    text = respond_to_lobechat(messages, payload.model)

    if payload.stream:
        return StreamingResponse(_stream_chunks(text, payload.model), media_type="text/event-stream")

    return JSONResponse(
        {
            "id": f"chatcmpl-interview-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": payload.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(_message_content(item.content).split()) for item in payload.messages),
                "completion_tokens": len(text.split()),
                "total_tokens": sum(len(_message_content(item.content).split()) for item in payload.messages) + len(text.split()),
            },
        }
    )


def _stream_chunks(text: str, model: str):
    for token in _chunk_text(text):
        yield "data: " + json.dumps(
            {
                "id": f"chatcmpl-interview-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}],
            }
        ) + "\n\n"
    yield "data: " + json.dumps(
        {
            "id": f"chatcmpl-interview-{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
    ) + "\n\n"
    yield "data: [DONE]\n\n"


def _chunk_text(text: str, size: int = 24):
    words = text.split(" ")
    for index in range(0, len(words), size):
        yield " ".join(words[index : index + size]) + " "


def _message_content(content: str | list[dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for item in content:
        if item.get("type") == "text":
            parts.append(item.get("text", ""))
    return "\n".join(parts)

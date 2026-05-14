from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol


class ProviderError(RuntimeError):
    pass


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatRequest:
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float = 0.4
    max_tokens: int = 900
    json_mode: bool = False
    tools: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class ChatResponse:
    text: str
    provider: str
    model: str
    usage: Usage = field(default_factory=Usage)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderHealth:
    ok: bool
    provider: str
    model: str
    local: bool
    message: str


class AIProvider(Protocol):
    name: str
    local: bool

    def chat(self, request: ChatRequest) -> ChatResponse:
        ...

    def stream(self, request: ChatRequest) -> Iterable[str]:
        ...

    def embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        ...

    def tool_calls(self, request: ChatRequest) -> ChatResponse:
        ...

    def health_check(self, model: str | None = None) -> ProviderHealth:
        ...

    def model_list(self) -> list[str]:
        ...


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) + len(text) // 16)


def usage_from_text(
    input_text: str,
    output_text: str,
    cost_per_1k_input: float = 0.0,
    cost_per_1k_output: float = 0.0,
) -> Usage:
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=round(
            (input_tokens / 1000 * cost_per_1k_input) + (output_tokens / 1000 * cost_per_1k_output),
            6,
        ),
    )


def messages_to_text(messages: list[ChatMessage]) -> str:
    return "\n".join(f"{message.role}: {message.content}" for message in messages)

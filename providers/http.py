from __future__ import annotations

import json
import os
from typing import Any, Iterable

import requests

from providers.base import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ProviderError,
    ProviderHealth,
    messages_to_text,
    usage_from_text,
)


class BaseHTTPProvider:
    name = "base"
    local = False

    def __init__(self, config: dict[str, Any], defaults: dict[str, Any]):
        self.config = config
        self.defaults = defaults
        self.base_url = config.get("base_url", "").rstrip("/")
        self.default_model = config.get("default_model") or defaults.get("model")
        self.timeout = int(defaults.get("timeout_seconds", 60))
        self.temperature = float(defaults.get("temperature", 0.4))
        self.max_tokens = int(defaults.get("max_tokens", 900))
        self.cost_per_1k_input = float(config.get("cost_per_1k_input", 0) or 0)
        self.cost_per_1k_output = float(config.get("cost_per_1k_output", 0) or 0)

    def headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def chat(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError

    def stream(self, request: ChatRequest) -> Iterable[str]:
        yield self.chat(request).text

    def embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        raise ProviderError(f"{self.name} embeddings are not implemented yet.")

    def tool_calls(self, request: ChatRequest) -> ChatResponse:
        return self.chat(request)

    def health_check(self, model: str | None = None) -> ProviderHealth:
        try:
            models = self.model_list()
            selected = model or self.default_model
            if models and selected and selected not in models and self.local:
                return ProviderHealth(False, self.name, selected, self.local, f"Model '{selected}' was not found.")
            return ProviderHealth(True, self.name, selected or "", self.local, f"{self.name} is reachable.")
        except Exception as exc:
            return ProviderHealth(False, self.name, model or self.default_model or "", self.local, str(exc))

    def model_list(self) -> list[str]:
        return []

    def _usage(self, request: ChatRequest, text: str):
        return usage_from_text(messages_to_text(request.messages), text, self.cost_per_1k_input, self.cost_per_1k_output)


class OllamaProvider(BaseHTTPProvider):
    name = "ollama"
    local = True

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self.default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": [message.__dict__ for message in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.json_mode:
            payload["format"] = "json"
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        response.raise_for_status()
        raw = response.json()
        text = raw.get("message", {}).get("content", "").strip()
        return ChatResponse(text=text, provider=self.name, model=model, usage=self._usage(request, text), raw=raw)

    def stream(self, request: ChatRequest) -> Iterable[str]:
        model = request.model or self.default_model
        payload = {
            "model": model,
            "messages": [message.__dict__ for message in request.messages],
            "stream": True,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
        }
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line.decode("utf-8"))
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    def model_list(self) -> list[str]:
        response = requests.get(f"{self.base_url}/api/tags", timeout=5)
        response.raise_for_status()
        return [item.get("name", "") for item in response.json().get("models", [])]


class OpenAICompatibleProvider(BaseHTTPProvider):
    name = "openai_compatible"
    local = False

    def headers(self) -> dict[str, str]:
        headers = super().headers()
        api_key_env = self.config.get("api_key_env")
        api_key = os.getenv(api_key_env, "") if api_key_env else ""
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self.default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": [message.__dict__ for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False,
        }
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if request.tools:
            payload["tools"] = request.tools
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=self.headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        raw = response.json()
        message = raw["choices"][0]["message"]
        text = (message.get("content") or "").strip()
        return ChatResponse(
            text=text,
            provider=self.name,
            model=model,
            usage=self._usage(request, text),
            tool_calls=message.get("tool_calls", []) or [],
            raw=raw,
        )

    def model_list(self) -> list[str]:
        response = requests.get(f"{self.base_url}/models", headers=self.headers(), timeout=5)
        response.raise_for_status()
        return [item.get("id", "") for item in response.json().get("data", [])]


class LMStudioProvider(OpenAICompatibleProvider):
    name = "lmstudio"
    local = True


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
    local = False


class XAIProvider(OpenAICompatibleProvider):
    name = "xai"
    local = False


class AnthropicProvider(BaseHTTPProvider):
    name = "anthropic"
    local = False

    def headers(self) -> dict[str, str]:
        api_key = os.getenv(self.config.get("api_key_env", ""), "")
        if not api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not set.")
        return {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

    def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self.default_model
        system = "\n".join(message.content for message in request.messages if message.role == "system")
        messages = [message.__dict__ for message in request.messages if message.role != "system"]
        payload = {
            "model": model,
            "system": system,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        response = requests.post(f"{self.base_url}/messages", json=payload, headers=self.headers(), timeout=self.timeout)
        response.raise_for_status()
        raw = response.json()
        text = "".join(block.get("text", "") for block in raw.get("content", []) if block.get("type") == "text").strip()
        return ChatResponse(text=text, provider=self.name, model=model, usage=self._usage(request, text), raw=raw)


class GeminiProvider(BaseHTTPProvider):
    name = "gemini"
    local = False

    def chat(self, request: ChatRequest) -> ChatResponse:
        api_key = os.getenv(self.config.get("api_key_env", ""), "")
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is not set.")
        model = request.model or self.default_model
        system = "\n".join(message.content for message in request.messages if message.role == "system")
        contents = [
            {"role": "user" if message.role != "assistant" else "model", "parts": [{"text": message.content}]}
            for message in request.messages
            if message.role != "system"
        ]
        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "responseMimeType": "application/json" if request.json_mode else "text/plain",
            },
        }
        url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        raw = response.json()
        candidates = raw.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        text = "".join(part.get("text", "") for part in parts).strip()
        return ChatResponse(text=text, provider=self.name, model=model, usage=self._usage(request, text), raw=raw)

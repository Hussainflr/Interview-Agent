from __future__ import annotations

from typing import Any

from providers.base import AIProvider
from providers.http import (
    AnthropicProvider,
    GeminiProvider,
    LMStudioProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
    XAIProvider,
)


PROVIDER_CLASSES = {
    "ollama": OllamaProvider,
    "lmstudio": LMStudioProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "xai": XAIProvider,
}


def build_provider(name: str, settings: dict[str, Any]) -> AIProvider:
    providers = settings.get("providers", {})
    if name not in PROVIDER_CLASSES:
        raise KeyError(f"Unknown provider '{name}'")
    return PROVIDER_CLASSES[name](providers.get(name, {}), settings.get("llm", {}))


def available_providers(settings: dict[str, Any], *, include_disabled: bool = True) -> list[dict[str, Any]]:
    result = []
    for name, config in settings.get("providers", {}).items():
        if name not in PROVIDER_CLASSES:
            continue
        enabled = bool(config.get("enabled", False))
        if not include_disabled and not enabled:
            continue
        result.append(
            {
                "id": name,
                "name": _label(name),
                "enabled": enabled,
                "local": bool(config.get("local", False)),
                "default_model": config.get("default_model", ""),
                "base_url": config.get("base_url", ""),
                "api_key_env": config.get("api_key_env", ""),
            }
        )
    return result


def _label(name: str) -> str:
    return {
        "ollama": "Ollama",
        "lmstudio": "LM Studio",
        "openai_compatible": "OpenAI-compatible",
        "openai": "OpenAI",
        "anthropic": "Claude",
        "gemini": "Gemini",
        "xai": "Grok / xAI",
    }.get(name, name)

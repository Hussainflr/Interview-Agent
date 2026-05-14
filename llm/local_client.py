from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from providers.base import ProviderError
from providers.router import ModelRouter


class LocalModelError(RuntimeError):
    pass


@dataclass
class ModelHealth:
    ok: bool
    provider: str
    model: str
    message: str
    local: bool = True


class LocalLLMClient:
    """Compatibility wrapper around the new provider router."""

    def __init__(self, settings: dict[str, Any]):
        self.router = ModelRouter(settings)

    def health(self) -> ModelHealth:
        health = self.router.health()
        return ModelHealth(
            ok=health.ok,
            provider=health.provider,
            model=health.model,
            message=health.message,
            local=health.local,
        )

    def generate(self, system: str, user: str, *, json_mode: bool = False) -> str:
        try:
            return self.router.generate(system, user, json_mode=json_mode)
        except ProviderError as exc:
            raise LocalModelError(str(exc)) from exc

    def generate_json(self, system: str, user: str, fallback: dict[str, Any]) -> dict[str, Any]:
        return self.router.generate_json(system, user, fallback)

from __future__ import annotations

import json
import logging
import time
from typing import Any

from providers.base import ChatMessage, ChatRequest, ChatResponse, ProviderError, ProviderHealth
from providers.registry import available_providers, build_provider

logger = logging.getLogger(__name__)


class ModelRouter:
    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.llm = settings.get("llm", {})
        self.routing = settings.get("routing", {})
        self.providers = settings.get("providers", {})
        self.session_cost_usd = 0.0

    def provider_catalog(self) -> list[dict[str, Any]]:
        return available_providers(self.settings)

    def health(self, provider_name: str | None = None, model: str | None = None) -> ProviderHealth:
        selected = provider_name or self.llm.get("provider", "ollama")
        provider = build_provider(selected, self.settings)
        return provider.health_check(model or self._model_for(selected))

    def health_all(self) -> list[dict[str, Any]]:
        statuses = []
        for item in available_providers(self.settings):
            if not item["enabled"]:
                statuses.append(
                    {
                        "ok": False,
                        "provider": item["id"],
                        "model": item["default_model"],
                        "local": item["local"],
                        "message": "Provider disabled or missing API key.",
                    }
                )
                continue
            health = self.health(item["id"], item["default_model"])
            statuses.append(health.__dict__)
        return statuses

    def model_list(self, provider_name: str | None = None) -> list[str]:
        selected = provider_name or self.llm.get("provider", "ollama")
        return build_provider(selected, self.settings).model_list()

    def chat(
        self,
        system: str,
        user: str,
        *,
        task: str = "interviewer",
        provider: str | None = None,
        model: str | None = None,
        json_mode: bool = False,
        sensitive: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResponse:
        messages = [ChatMessage("system", system), ChatMessage("user", user)]
        last_error: Exception | None = None

        for provider_name in self._route(task, provider, sensitive=sensitive):
            try:
                if not self._provider_allowed(provider_name, sensitive=sensitive):
                    continue
                adapter = build_provider(provider_name, self.settings)
                request = ChatRequest(
                    messages=messages,
                    model=model or self._model_for(provider_name, task),
                    temperature=float(self.llm.get("temperature", 0.4)),
                    max_tokens=int(self.llm.get("max_tokens", 900)),
                    json_mode=json_mode,
                    tools=tools or [],
                    metadata={"task": task, "sensitive": sensitive},
                )
                response = adapter.chat(request)
                self.session_cost_usd += response.usage.estimated_cost_usd
                if self._over_budget():
                    logger.warning("Model routing budget exceeded: %s", self.session_cost_usd)
                return response
            except Exception as exc:
                last_error = exc
                logger.warning("Provider %s failed for task %s: %s", provider_name, task, exc)
                time.sleep(0.2)

        raise ProviderError(str(last_error) if last_error else "No allowed provider could handle the request.")

    def stream(
        self,
        system: str,
        user: str,
        *,
        task: str = "interviewer",
        provider: str | None = None,
        model: str | None = None,
        sensitive: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ):
        messages = [ChatMessage("system", system), ChatMessage("user", user)]
        last_error: Exception | None = None

        for provider_name in self._route(task, provider, sensitive=sensitive):
            try:
                if not self._provider_allowed(provider_name, sensitive=sensitive):
                    continue
                adapter = build_provider(provider_name, self.settings)
                request = ChatRequest(
                    messages=messages,
                    model=model or self._model_for(provider_name, task),
                    temperature=float(self.llm.get("temperature", 0.4)),
                    max_tokens=int(self.llm.get("max_tokens", 900)),
                    json_mode=False,
                    tools=tools or [],
                    metadata={"task": task, "sensitive": sensitive},
                )
                yield from adapter.stream(request)
                return
            except Exception as exc:
                last_error = exc
                logger.warning("Streaming provider %s failed for task %s: %s", provider_name, task, exc)
                time.sleep(0.2)

        raise ProviderError(str(last_error) if last_error else "No allowed provider could stream the request.")

    def generate(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool = False,
        task: str = "interviewer",
        sensitive: bool = False,
    ) -> str:
        return self.chat(system, user, json_mode=json_mode, task=task, sensitive=sensitive).text

    def generate_json(
        self,
        system: str,
        user: str,
        fallback: dict[str, Any],
        *,
        task: str = "evaluator",
        sensitive: bool = False,
    ) -> dict[str, Any]:
        try:
            text = self.generate(system, user, json_mode=True, task=task, sensitive=sensitive)
            return _extract_json(text)
        except Exception as exc:
            logger.warning("Using fallback JSON after model/router error: %s", exc)
            return fallback

    def _route(self, task: str, provider: str | None, *, sensitive: bool) -> list[str]:
        if provider:
            return [provider] + [name for name in self.llm.get("fallback_chain", []) if name != provider]

        task_provider = self.routing.get(f"{task}_provider", "auto")
        if task_provider and task_provider != "auto":
            return [task_provider]

        if task == "classifier":
            return [self.routing.get("classifier_provider", "ollama")]

        primary = self.llm.get("provider", "ollama")
        chain = [primary] + [name for name in self.llm.get("fallback_chain", []) if name != primary]

        if sensitive or self.routing.get("privacy_mode") == "local_only":
            return [name for name in chain if self.providers.get(name, {}).get("local")]

        if self.routing.get("privacy_mode") == "hybrid":
            local = [name for name in chain if self.providers.get(name, {}).get("local")]
            cloud = [name for name in self.providers if not self.providers.get(name, {}).get("local")]
            return local + cloud

        return chain

    def _provider_allowed(self, provider_name: str, *, sensitive: bool) -> bool:
        config = self.providers.get(provider_name, {})
        if not config.get("enabled", False):
            return False
        if sensitive and not config.get("local", False) and not self.routing.get("allow_cloud_for_sensitive_context", False):
            return False
        if self.routing.get("privacy_mode") == "local_only" and not config.get("local", False):
            return False
        return True

    def _model_for(self, provider_name: str, task: str = "interviewer") -> str:
        config = self.providers.get(provider_name, {})
        if task == "classifier":
            return config.get("classifier_model") or config.get("default_model") or self.llm.get("model", "")
        if provider_name == self.llm.get("provider") and self.llm.get("model"):
            return self.llm["model"]
        return config.get("default_model") or self.llm.get("model", "")

    def _over_budget(self) -> bool:
        budget = float(self.routing.get("max_cloud_cost_usd_per_session", 0.0) or 0.0)
        return budget > 0 and self.session_cost_usd > budget


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)

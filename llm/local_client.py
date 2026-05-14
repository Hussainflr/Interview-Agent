from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)


class LocalModelError(RuntimeError):
    pass


@dataclass
class ModelHealth:
    ok: bool
    provider: str
    model: str
    message: str


class LocalLLMClient:
    def __init__(self, settings: dict[str, Any]):
        llm = settings["llm"]
        self.provider = llm.get("provider", "ollama").lower()
        self.model = llm.get("model", "qwen3:4b")
        self.temperature = float(llm.get("temperature", 0.4))
        self.max_tokens = int(llm.get("max_tokens", 900))
        self.timeout = int(llm.get("timeout_seconds", 60))
        self.retries = int(llm.get("retries", 1))
        self.ollama_base_url = llm.get("base_url", "http://localhost:11434").rstrip("/")
        self.lmstudio_base_url = llm.get("lmstudio_base_url", "http://localhost:1234/v1").rstrip("/")

    def health(self) -> ModelHealth:
        try:
            if self.provider == "ollama":
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                response.raise_for_status()
                models = [item.get("name") for item in response.json().get("models", [])]
                if self.model not in models:
                    return ModelHealth(
                        False,
                        self.provider,
                        self.model,
                        f"Ollama is running, but model '{self.model}' is not installed. Run: ollama pull {self.model}",
                    )
                return ModelHealth(True, self.provider, self.model, "Ollama is ready.")

            response = requests.get(f"{self.lmstudio_base_url}/models", timeout=5)
            response.raise_for_status()
            return ModelHealth(True, self.provider, self.model, "LM Studio local server is ready.")
        except requests.RequestException as exc:
            target = self.ollama_base_url if self.provider == "ollama" else self.lmstudio_base_url
            return ModelHealth(
                False,
                self.provider,
                self.model,
                f"Cannot reach {self.provider} at {target}. Start the local model server and try again.",
            )
        except Exception as exc:
            return ModelHealth(False, self.provider, self.model, str(exc))

    def generate(self, system: str, user: str, *, json_mode: bool = False) -> str:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                if self.provider == "ollama":
                    return self._generate_ollama(system, user, json_mode=json_mode)
                if self.provider == "lmstudio":
                    return self._generate_lmstudio(system, user, json_mode=json_mode)
                raise LocalModelError(f"Unsupported local provider '{self.provider}'. Use ollama or lmstudio.")
            except (requests.RequestException, LocalModelError) as exc:
                last_error = exc
                logger.warning("Local LLM call failed on attempt %s: %s", attempt + 1, exc)
                if attempt < self.retries:
                    time.sleep(0.5 * (attempt + 1))

        raise LocalModelError(str(last_error) if last_error else "Local model call failed.")

    def generate_json(self, system: str, user: str, fallback: dict[str, Any]) -> dict[str, Any]:
        try:
            text = self.generate(system, user, json_mode=True)
            return _extract_json(text)
        except Exception as exc:
            logger.warning("Using fallback JSON after model error: %s", exc)
            return fallback

    def _generate_ollama(self, system: str, user: str, *, json_mode: bool) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"
        response = requests.post(f"{self.ollama_base_url}/api/chat", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "").strip()

    def _generate_lmstudio(self, system: str, user: str, *, json_mode: bool) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        response = requests.post(
            f"{self.lmstudio_base_url}/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


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


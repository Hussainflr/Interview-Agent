from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
SETTINGS_PATH = ROOT_DIR / "configs" / "settings.yaml"


def _env(name: str, default: Any) -> Any:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    if isinstance(default, bool):
        return value.lower() in {"1", "true", "yes", "on"}
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    if isinstance(default, float):
        try:
            return float(value)
        except ValueError:
            return default
    return value


@lru_cache(maxsize=1)
def get_settings() -> dict[str, Any]:
    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    llm = settings.setdefault("llm", {})
    app = settings.setdefault("app", {})

    llm["provider"] = _env("LOCAL_LLM_PROVIDER", llm.get("provider", "ollama"))
    llm["model"] = _env("LOCAL_LLM_MODEL", llm.get("model", "qwen3:4b"))
    llm["base_url"] = _env("OLLAMA_BASE_URL", llm.get("base_url", "http://localhost:11434"))
    llm["lmstudio_base_url"] = _env(
        "LMSTUDIO_BASE_URL", llm.get("lmstudio_base_url", "http://localhost:1234/v1")
    )
    llm["temperature"] = _env("LOCAL_LLM_TEMPERATURE", llm.get("temperature", 0.4))
    llm["max_tokens"] = _env("LOCAL_LLM_MAX_TOKENS", llm.get("max_tokens", 900))
    llm["timeout_seconds"] = _env("LOCAL_LLM_TIMEOUT_SECONDS", llm.get("timeout_seconds", 60))
    llm["retries"] = _env("LOCAL_LLM_RETRIES", llm.get("retries", 1))

    app["session_dir"] = str(ROOT_DIR / app.get("session_dir", "outputs/sessions"))
    app["report_dir"] = str(ROOT_DIR / app.get("report_dir", "outputs/reports"))
    app["enable_tts"] = _env("ENABLE_TTS", app.get("enable_tts", False))

    return settings


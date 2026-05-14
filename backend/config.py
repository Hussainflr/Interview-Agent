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
    providers = settings.setdefault("providers", {})
    routing = settings.setdefault("routing", {})

    llm["provider"] = _env("LOCAL_LLM_PROVIDER", llm.get("provider", "ollama"))
    llm["model"] = _env("LOCAL_LLM_MODEL", llm.get("model", "qwen3:4b"))
    llm["temperature"] = _env("LOCAL_LLM_TEMPERATURE", llm.get("temperature", 0.4))
    llm["max_tokens"] = _env("LOCAL_LLM_MAX_TOKENS", llm.get("max_tokens", 900))
    llm["timeout_seconds"] = _env("LOCAL_LLM_TIMEOUT_SECONDS", llm.get("timeout_seconds", 60))
    llm["retries"] = _env("LOCAL_LLM_RETRIES", llm.get("retries", 1))
    routing["privacy_mode"] = _env("PRIVACY_MODE", routing.get("privacy_mode", "local_only"))

    if "ollama" in providers:
        providers["ollama"]["base_url"] = _env(
            "OLLAMA_BASE_URL", providers["ollama"].get("base_url", "http://localhost:11434")
        )
        providers["ollama"]["default_model"] = _env(
            "OLLAMA_MODEL", providers["ollama"].get("default_model", llm["model"])
        )
    if "lmstudio" in providers:
        providers["lmstudio"]["base_url"] = _env(
            "LMSTUDIO_BASE_URL", providers["lmstudio"].get("base_url", "http://localhost:1234/v1")
        )
        providers["lmstudio"]["default_model"] = _env(
            "LMSTUDIO_MODEL", providers["lmstudio"].get("default_model", "local-model")
        )

    provider_env_map = {
        "openai": ("OPENAI_BASE_URL", "OPENAI_MODEL"),
        "anthropic": ("ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL"),
        "gemini": ("GEMINI_BASE_URL", "GEMINI_MODEL"),
        "xai": ("XAI_BASE_URL", "XAI_MODEL"),
        "openai_compatible": ("OPENAI_COMPATIBLE_BASE_URL", "OPENAI_COMPATIBLE_MODEL"),
    }
    for name, (base_env, model_env) in provider_env_map.items():
        if name not in providers:
            continue
        providers[name]["base_url"] = _env(base_env, providers[name].get("base_url", ""))
        providers[name]["default_model"] = _env(model_env, providers[name].get("default_model", ""))
        api_key_env = providers[name].get("api_key_env")
        if api_key_env and os.getenv(api_key_env):
            providers[name]["enabled"] = _env(f"{name.upper()}_ENABLED", True)
        else:
            providers[name]["enabled"] = _env(f"{name.upper()}_ENABLED", providers[name].get("enabled", False))

    app["session_dir"] = str(ROOT_DIR / app.get("session_dir", "outputs/sessions"))
    app["report_dir"] = str(ROOT_DIR / app.get("report_dir", "outputs/reports"))
    app["enable_tts"] = _env("ENABLE_TTS", app.get("enable_tts", False))

    mcp = settings.setdefault("mcp", {})
    if mcp.get("registry_path"):
        mcp["registry_path"] = str(ROOT_DIR / mcp["registry_path"])
    if mcp.get("audit_log"):
        mcp["audit_log"] = str(ROOT_DIR / mcp["audit_log"])

    return settings

from providers.router import ModelRouter


def test_provider_catalog_contains_local_defaults():
    settings = {
        "llm": {"provider": "ollama", "model": "qwen3:4b", "fallback_chain": ["ollama", "lmstudio"]},
        "routing": {"privacy_mode": "local_only"},
        "providers": {
            "ollama": {"enabled": True, "local": True, "default_model": "qwen3:4b"},
            "lmstudio": {"enabled": True, "local": True, "default_model": "local-model"},
            "openai": {"enabled": True, "local": False, "default_model": "gpt-4.1-mini"},
        },
    }
    catalog = ModelRouter(settings).provider_catalog()
    ids = {item["id"] for item in catalog}
    assert {"ollama", "lmstudio", "openai"}.issubset(ids)


def test_local_only_route_filters_cloud():
    settings = {
        "llm": {"provider": "openai", "model": "gpt-4.1-mini", "fallback_chain": ["ollama", "openai"]},
        "routing": {"privacy_mode": "local_only"},
        "providers": {
            "ollama": {"enabled": True, "local": True, "default_model": "qwen3:4b"},
            "openai": {"enabled": True, "local": False, "default_model": "gpt-4.1-mini"},
        },
    }
    router = ModelRouter(settings)
    assert router._route("interviewer", None, sensitive=False) == ["ollama"]

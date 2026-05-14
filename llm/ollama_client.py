from __future__ import annotations

from backend.config import get_settings
from llm.local_client import LocalLLMClient


def generate_streaming_response(prompt: str) -> str:
    """Backward-compatible helper for older imports.

    The app now uses LocalLLMClient directly and supports both Ollama and
    LM Studio. This wrapper remains so older code does not crash.
    """

    client = LocalLLMClient(get_settings())
    return client.generate(
        "You are a helpful local interview preparation assistant.",
        prompt,
        json_mode=False,
    )


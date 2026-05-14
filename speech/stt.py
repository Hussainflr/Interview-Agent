from __future__ import annotations

from functools import lru_cache

from backend.config import get_settings


@lru_cache(maxsize=1)
def _model():
    from faster_whisper import WhisperModel

    config = get_settings()
    return WhisperModel(
        config["stt"]["model"],
        device=config["stt"].get("device", "cpu"),
        compute_type="int8",
    )


def transcribe(audio_path: str) -> str:
    segments, _ = _model().transcribe(audio_path)
    return " ".join(segment.text.strip() for segment in segments).strip()


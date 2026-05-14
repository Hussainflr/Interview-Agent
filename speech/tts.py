from __future__ import annotations

import os
import tempfile
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")


@lru_cache(maxsize=1)
def _engine():
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 180)
    engine.setProperty("volume", 0.9)
    return engine


def speak_to_file(text: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=OUTPUT_DIR) as f:
        temp_path = f.name
    engine = _engine()
    engine.save_to_file(text, temp_path)
    engine.runAndWait()
    return temp_path


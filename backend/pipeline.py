from __future__ import annotations

import tempfile

import soundfile as sf

from agents.interview_agent import InterviewAgent
from backend.config import get_settings
from speech.stt import transcribe
from speech.tts import speak_to_file


def process_audio_array(audio_array, session_id: str | None = None):
    """Transcribe local audio and route it through the interview agent."""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio_array, 16000)
        wav_path = f.name

    text = transcribe(wav_path)
    if not text.strip():
        return b"", "No speech detected. You can also type your answer.", text, session_id

    agent = InterviewAgent(get_settings())
    if not session_id:
        session = agent.start_session({})
        session_id = session["id"]

    result = agent.handle_message(session_id, text)
    response_text = result.get("reply", "")
    if result.get("next_question"):
        response_text = f"{response_text}\n\nNext question: {result['next_question']}"

    audio_bytes = b""
    if get_settings()["app"].get("enable_tts"):
        output_audio_path = speak_to_file(response_text)
        with open(output_audio_path, "rb") as f:
            audio_bytes = f.read()

    return audio_bytes, response_text, text, session_id


import tempfile
import soundfile as sf

from speech.stt import transcribe
from speech.tts import speak_to_file
from agents.crew import build_crew

crew = build_crew()  # create once


def process_audio_array(audio_array):
    """
    audio_array: numpy float32 array
    """

    # Save as WAV (for whisper)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio_array, 16000)
        wav_path = f.name

    # STT
    text = transcribe(wav_path)

    print("🧑 User:", text)

    if not text.strip():
        return b"", "No speech detected", text

    # CrewAI
    result = crew.kickoff(inputs={"answer": text})
    response_text = str(result)

    print("🤖 AI:", response_text)

    # TTS
    output_audio_path = speak_to_file(response_text)

    with open(output_audio_path, "rb") as f:
        audio_bytes = f.read()

    return audio_bytes, response_text, text
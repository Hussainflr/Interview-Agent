import pyttsx3
import os
import tempfile

# -------------------------
# Paths
# -------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# -------------------------
# TTS Engine
# -------------------------
engine = pyttsx3.init()
engine.setProperty('rate', 180)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)

# -------------------------
# Main TTS function
# -------------------------
def speak_to_file(text: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Create temporary WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=OUTPUT_DIR) as f:
        temp_path = f.name

    # Save speech to file
    engine.save_to_file(text, temp_path)
    engine.runAndWait()

    return temp_path
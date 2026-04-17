import os
import subprocess
import uuid
import urllib.request

# -------------------------
# Paths
# -------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_DIR = os.path.join(BASE_DIR, "models", "piper")
MODEL_PATH = os.path.join(MODEL_DIR, "en_US-lessac-medium.onnx")

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"


# -------------------------
# Ensure model exists
# -------------------------
def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not os.path.exists(MODEL_PATH):
        print("⬇️ Downloading Piper model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("✅ Model downloaded")


# -------------------------
# Main TTS function
# -------------------------
def speak_to_file(text: str):
    ensure_model()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename = os.path.join(OUTPUT_DIR, f"output_{uuid.uuid4()}.wav")

    process = subprocess.Popen(
        [
            "piper",
            "--model",
            MODEL_PATH,
            "--output_file",
            filename,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    process.communicate(text[:500])  # limit length for stability

    # -------------------------
    # Validate output
    # -------------------------
    if not os.path.exists(filename):
        raise RuntimeError("❌ TTS failed: output file not created")

    return filename
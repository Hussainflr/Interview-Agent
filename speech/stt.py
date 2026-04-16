from faster_whisper import WhisperModel
import yaml

with open("config/settings.yaml") as f:
    config = yaml.safe_load(f)

MODEL_SIZE = config["stt"]["model"]

# M1 optimization
model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8"   # ⚡ faster on M1
)

def transcribe(audio_path):
    segments, _ = model.transcribe(audio_path)

    text = ""
    for segment in segments:
        text += segment.text + " "

    return text.strip()
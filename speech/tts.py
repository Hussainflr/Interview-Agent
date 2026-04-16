import subprocess
import yaml

with open("config/settings.yaml") as f:
    config = yaml.safe_load(f)

MODEL_PATH = config["tts"]["model_path"]

def speak(text):
    command = f'echo "{text}" | piper --model {MODEL_PATH} --output_file output.wav'
    subprocess.run(command, shell=True)

    # Play audio (Mac)
    subprocess.run("afplay output.wav", shell=True)
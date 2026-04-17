import subprocess
import threading

current_process = None

def speak(text):
    global current_process

    # Stop previous speech if interrupt triggered
    if current_process:
        current_process.kill()

    command = f'echo "{text}" | piper --model models/piper/en_US-lessac-medium.onnx --output_file output.wav'
    subprocess.run(command, shell=True)

    current_process = subprocess.Popen("afplay output.wav", shell=True)



# -----------------------
# Session State Init (TOP OF FILE)
# -----------------------
import streamlit as st
import queue

def init_session_state():
    defaults = {
        "running": False,
        "audio_queue": queue.Queue(),
        "history": [],
        "interrupt": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()
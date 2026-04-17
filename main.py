import streamlit as st
import av
import queue
import threading
import time

from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
from llm.ollama_client import generate_streaming_response
from speech.stt import transcribe
from speech.tts import speak
from agents.crew import build_crew
import numpy as np
import soundfile as sf
from utils.vad import is_speech

st.title("🎤 Real-Time Interview Agent")
st.markdown(
    f"### Status: {'🟢 Listening' if st.session_state.running else '🔴 Stopped'}"
)
# -----------------------
# Session State
# -----------------------
if "running" not in st.session_state:
    st.session_state.running = False

if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = queue.Queue()

if "history" not in st.session_state:
    st.session_state.history = []

if "interrupt" not in st.session_state:
    st.session_state.interrupt = False

# -----------------------
# Audio Processor
# -----------------------
class AudioProcessor(AudioProcessorBase):
    def recv(self, frame: av.AudioFrame):
        audio = frame.to_ndarray().flatten()

        # 🚨 If user speaks → trigger interrupt
        st.session_state.interrupt = True

        st.session_state.audio_queue.put(audio)
        return frame

# -----------------------
# Start / Stop Buttons
# -----------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ Start Interview"):
        st.session_state.running = True

with col2:
    if st.button("⛔ Stop Interview"):
        st.session_state.running = False

# -----------------------
# WebRTC Stream
# -----------------------
webrtc_ctx = webrtc_streamer(
    key="interview",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

# -----------------------
# Background Worker
# -----------------------

def process_audio():
    crew = build_crew()

    buffer = []
    silence_counter = 0
    SILENCE_THRESHOLD = 10  # adjust sensitivity

    while st.session_state.running:

        if not st.session_state.audio_queue.empty():
            chunk = st.session_state.audio_queue.get()

            if is_speech(chunk):
                buffer.append(chunk)
                silence_counter = 0
            else:
                silence_counter += 1

            # If silence detected → process sentence
            if silence_counter > SILENCE_THRESHOLD and buffer:

                audio_np = np.concatenate(buffer)
                sf.write("temp.wav", audio_np, 16000)

                buffer = []
                silence_counter = 0

                # STT
                text = transcribe("temp.wav")

                if text.strip():
                    st.session_state.history.append(("You", text))

                    # INTERRUPT CHECK
                    # Reset interrupt BEFORE AI starts speaking
                    st.session_state.interrupt = False

                    response = generate_streaming_response(text)
                    # st.session_state.interrupt = True
                    
                    # LLM RESPONSE (streaming style)
                    # response = generate_streaming_response(text)

                    st.session_state.history.append(("AI", response))

                    speak(response)

        time.sleep(0.1)

# -----------------------
# Run Thread
# -----------------------
if st.session_state.running:
    threading.Thread(target=process_audio, daemon=True).start()

# -----------------------
# UI Chat Display
# -----------------------
st.subheader("Conversation")

for role, msg in st.session_state.history:
    if role == "You":
        st.markdown(f"🧑 **You:** {msg}")
    else:
        st.markdown(f"🤖 **AI:** {msg}")
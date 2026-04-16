import streamlit as st
from speech.stt import transcribe
from speech.tts import speak
from agents.crew import build_crew

st.title("🎤 AI Interview Agent")

if "history" not in st.session_state:
    st.session_state.history = []

audio_file = st.file_uploader("Upload your answer")

if audio_file:
    with open("temp.wav", "wb") as f:
        f.write(audio_file.read())

    text = transcribe("temp.wav")

    st.write("🧑 You:", text)

    crew = build_crew()
    response = crew.kickoff(inputs={"answer": text})

    st.write("🤖 AI:", response)

    speak(response)
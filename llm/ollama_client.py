import requests
import yaml
import streamlit as st

with open("configs/settings.yaml") as f:
    config = yaml.safe_load(f)

MODEL = config["llm"]["model"]

def generate_streaming_response(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )

    full_text = ""

    for line in response.iter_lines():
        if line:
            chunk = eval(line.decode("utf-8"))
            token = chunk.get("response", "")
            full_text += token

            # Interrupt if user starts speaking
            if st.session_state.get("interrupt"):
                break

    return full_text
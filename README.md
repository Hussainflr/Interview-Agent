# 🎤 Real-Time AI Interview Agent (Local, Voice-Based)

🚀 A ChatGPT-like voice assistant for technical interviews — running 100% locally with multi-agent intelligence.

* 🧠 Multi-agent orchestration (CrewAI)
* 🎙️ Speech-to-Text (faster-whisper)
* 🔊 Text-to-Speech (Piper)
* 🤖 Local LLM (Ollama - Mistral / Llama3)
* 🌐 Streamlit UI with live microphone interaction

---

## 🚀 Features

* 🎤 **Real-time voice interaction**
* 🧠 **Multi-agent interview flow** (Interviewer + Evaluator)
* 🔄 **Streaming-like responses**
* ⛔ **Interrupt support** (user can cut AI mid-response)
* 🤫 **Silence detection (VAD)** using Silero
* 🔒 **Fully local (no API required)**

---

## 🧠 System Architecture

```
Mic Input
   ↓
VAD (Silero)
   ↓
STT (faster-whisper)
   ↓
CrewAI Agents
   ↓
LLM (Ollama)
   ↓
TTS (Piper)
   ↓
Audio Output + UI
```

---

## 📁 Project Structure

```
interview-agent/
│
├── app/
│   └── main.py              # Streamlit UI
│
├── agents/
│   ├── crew.py
│   ├── interviewer.py
│   └── evaluator.py
│
├── llm/
│   └── ollama_client.py
│
├── speech/
│   ├── stt.py              # faster-whisper
│   └── tts.py              # Piper
│
├── utils/
│   └── vad.py              # Silero VAD
│
├── config/
│   └── settings.yaml
│
├── models/
│   └── piper/              # local TTS models (ignored in git)
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup (Conda - Recommended for M1)

### 1. Create environment

```bash
conda create -n interview-agent python=3.10 -y
conda activate interview-agent
```

---

### 2. Install core dependencies

```bash
conda install -c conda-forge pip setuptools wheel -y
conda install -c conda-forge ffmpeg libsndfile -y
```

---

### 3. Install Python packages

```bash
python -m pip install \
numpy\
streamlit \
crewai \
faster-whisper \
av \
soundfile \
pydub \
requests \
pyyaml \
silero-vad
```

---

### 4. Install Piper (TTS)

```bash
brew install piper
```

Download voice model:

```bash
mkdir -p models/piper
cd models/piper

curl -L -o en_US-lessac-medium.onnx \
https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

---

### 5. Setup Ollama

Install and pull model:

```bash
ollama pull mistral
# OR
ollama pull llama3:8b
```

---

## ▶️ Run Application

```bash
streamlit run app/main.py
```

---

## 🎮 Usage

1. Click **▶️ Start Interview**
2. Speak naturally into your microphone
3. AI listens, processes, and responds
4. AI asks follow-up questions
5. Click **⛔ Stop Interview** to end

---

## 🧠 Agents

* **Interviewer Agent**

  * Asks structured technical/behavioral questions

* **Evaluator Agent**

  * Evaluates responses and provides feedback

---

## ⚡ Tech Stack

| Component | Tool                      |
| --------- | ------------------------- |
| UI        | Streamlit                 |
| LLM       | Ollama (Mistral / Llama3) |
| STT       | faster-whisper            |
| TTS       | Piper                     |
| VAD       | Silero VAD                |
| Agents    | CrewAI                    |

---

## 🔥 Key Highlights

* 💯 Fully local AI pipeline (privacy-friendly)
* ⚡ Optimized for Apple Silicon (M1/M2)
* 🧩 Modular architecture (easy to swap components)
* 🎯 Real-time conversational UX

---

## ⚠️ Notes

* Ensure microphone permissions are enabled
* Use `mistral` for speed, `llama3:8b` for quality
* Avoid large models (>8B) on M1 for real-time performance

---

## 🚀 Future Improvements

* 📊 Interview scoring dashboard
* 🧠 Memory-aware conversation
* 🔁 Streaming TTS (speak while generating)
* 🎭 Multi-role interviewers (HR + Tech + System Design)

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or PRs.

---

## 📜 License

MIT License

---

## ⭐ Acknowledgements

* CrewAI for agent orchestration
* Ollama for local LLM serving
* Silero for VAD
* Open-source speech community

---

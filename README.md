# 🎤 Real-Time AI Interview Agent (Local, Voice-Based)


# 🎤 Real-Time AI Interview Agent (Local, Voice-Based)

🚀 A ChatGPT-like voice assistant for technical interviews — running 100% locally with multi-agent intelligence built with:

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

## ⚡ Quick Start (Recommended)

```bash
git clone <your-repo-url>
cd interview-agent

chmod +x setup.sh
./setup.sh
```

👉 Then run:

```bash
streamlit run app/main.py
```

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
├── setup.sh                # 🔥 one-command setup
├── requirements.txt
└── README.md
```

---

## ⚙️ Manual Setup (Optional)

If you prefer step-by-step:

### 1. Create environment

```bash
conda create -n interview-agent python=3.10 -y
conda activate interview-agent
```

---

### 2. Install dependencies

```bash
conda install -c conda-forge pip setuptools wheel ffmpeg libsndfile -y
```

```bash
python -m pip install \
numpy==1.26.4 \
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

### 3. Install Piper (TTS)

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

### 4. Setup Ollama

```bash
ollama pull mistral
# OR
ollama pull llama3:8b
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

## ⭐ If you found this useful, consider starring the repo!

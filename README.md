# 🎤 Real-Time AI Interview Agent (FastAPI + React + Local LLM)

> 🚀 A fully local, real-time **voice-based interview assistant** with streaming audio, multi-agent reasoning, and no cloud APIs.

---

## 🔥 Demo Overview

```text
🎤 Speak → AI listens → transcribes → evaluates → responds → speaks back
```

* Real-time microphone streaming (PCM)
* WebSocket-based communication
* AI-driven interview flow
* Fully offline (Ollama + local models)

---

## 🧠 Architecture

```text
React (Mic - PCM stream)
   ↓ WebSocket
FastAPI Backend
   ↓
STT (faster-whisper)
   ↓
CrewAI Agents (LiteLLM)
   ↓
Ollama (Mistral / Llama3)
   ↓
TTS (pyttsx3)
   ↓
Audio response → Browser
```

---

## ⚡ Tech Stack

| Layer    | Technology                    |
| -------- | ----------------------------- |
| Frontend | Next.js (React)               |
| Backend  | FastAPI + WebSockets          |
| Agents   | CrewAI                        |
| LLM      | Ollama (local) via CrewAI     |
| STT      | faster-whisper                |
| TTS      | pyttsx3 (macOS native)      |
| Audio    | Web Audio API (PCM streaming) |

---

## 📁 Project Structure

```bash
interview-agent/
├── backend/
│   ├── main.py
│   ├── websocket.py
│   ├── pipeline.py
│   └── __init__.py
│
├── frontend/              # Next.js app
│   ├── app/
│   └── package.json
│
├── agents/
│   ├── crew.py
│   ├── interviewer.py
│   └── evaluator.py
│
├── speech/
│   ├── stt.py
│   └── tts.py
│
├── models/
│   └── piper/
│
├── outputs/
└── README.md
```

---

## 🚀 Setup Instructions

### 🧩 1. Prerequisites

Install:

* Node.js (for frontend)
* Ollama
* Python packages (automatically installed by setup.sh)

---

### 🤖 2. Setup Ollama

```bash
ollama pull mistral
ollama run mistral
```

---

### 🐍 3. Backend Setup (Python)

```bash
conda create -n interview-agent python=3.10 -y
conda activate interview-agent
```

Install dependencies:

```bash
pip install fastapi uvicorn crewai litellm \
faster-whisper soundfile numpy
```

Set environment variables:

```bash
export OPENAI_API_KEY=dummy
export OLLAMA_BASE_URL=http://localhost:11434
```

Run backend:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### ⚛️ 4. Frontend Setup (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

---

## 🎮 Usage

1. Click **Start**
2. Allow microphone access
3. Speak naturally
4. AI:

   * transcribes your speech
   * evaluates your answer
   * asks follow-up questions
   * responds with voice

---

## 🔊 Audio Pipeline

* 🎤 Input: PCM streaming (Web Audio API)
* 🧠 STT: faster-whisper
* 🤖 LLM: Ollama (local)
* 🔊 Output: Piper TTS

---

## ⚠️ Important Notes

* No WebM / ffmpeg required (pure PCM streaming)
* Ensure microphone permissions are enabled
* Keep Ollama running during usage
* First run may take time (model loading)

---

## 🔥 Key Features

* ✅ Real-time audio streaming (WebSocket)
* ✅ Fully local AI (privacy-first)
* ✅ Multi-agent reasoning (CrewAI)
* ✅ No OpenAI or external APIs
* ✅ Modular & scalable architecture

---

## 🚀 Future Improvements

* 🔴 Streaming LLM responses (token-by-token)
* ⛔ Interrupt AI speech
* 🎯 Voice Activity Detection (VAD)
* 📊 Interview scoring dashboard
* 💬 Chat-style UI (like ChatGPT)

---

## 🧠 Key Learnings

* Real-time audio ≠ file uploads
* WebSockets are essential for streaming apps
* PCM streaming avoids ffmpeg complexity
* AI pipeline latency is the main UX challenge

---

## 📜 License

MIT License

---

## ⭐ If you found this useful, consider starring the repo!

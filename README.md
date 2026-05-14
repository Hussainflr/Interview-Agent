# Local Interview Agent

A local-first mock interview coach for role-specific practice, answer scoring, feedback, follow-up questions, progress tracking, and report export. It runs with local models through Ollama or LM Studio and does not require OpenAI, Claude, or any paid cloud API by default.

## What It Does

- Starts mock interviews by role, difficulty, and interview type.
- Supports Software Engineer, ML Engineer, Data Scientist, Project Manager, UN/INGO role, Product Manager, and DevOps Engineer modes.
- Scores answers with a clear rubric: relevance, clarity, depth, structure, and role fit.
- Gives strengths, weaknesses, an improved sample answer, and a follow-up question.
- Routes greetings, unclear text, unrelated input, abusive input, and unsafe input before using the interview pipeline.
- Stores session history locally in `outputs/sessions`.
- Exports interview reports as Markdown or PDF in `outputs/reports`.
- Accepts pasted CV/resume text and job descriptions. Text file upload is supported as a convenience.
- Provides text input as the primary flow, with optional microphone input.

## Architecture

```text
frontend/app/page.js
  UI, provider/model controls, dashboard, text answers, optional mic

backend/main.py
  FastAPI routes, uploads, report export, model health checks

agents/interview_agent.py
  intent routing, guardrails, orchestration, scoring, follow-up generation

llm/local_client.py
  Ollama and LM Studio clients, retries, timeouts, JSON output handling

prompts/
  reusable question and evaluation prompt templates

backend/storage.py
  local JSON session history

speech/
  lazy-loaded faster-whisper STT and optional pyttsx3 TTS
```

## Local Setup

### 1. Install prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- One local model server:
  - Ollama: <https://ollama.com>
  - LM Studio: <https://lmstudio.ai>

### 2. Install the app

```bash
./setup.sh
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
```

### 3. Configure local models

Copy `.env.example` to `.env` if `setup.sh` did not already do it.

```bash
cp .env.example .env
```

Useful settings:

```bash
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_MODEL=qwen3:4b
OLLAMA_BASE_URL=http://localhost:11434
LMSTUDIO_BASE_URL=http://localhost:1234/v1
ENABLE_TTS=false
```

### 4. Run with Ollama

```bash
ollama pull qwen3:4b
ollama serve
```

In another terminal:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

In another terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

### 5. Run with LM Studio

1. Open LM Studio.
2. Download a chat/instruct model.
3. Start the local server from the Developer tab.
4. Use provider `LM Studio` in the app.
5. Set the model name shown by LM Studio, or keep the loaded model selected in LM Studio.

Default LM Studio URL:

```text
http://localhost:1234/v1
```

## Recommended Local Models

- Fast starter: `qwen3:4b`
- Stronger general interview coaching: `llama3.1:8b`, `qwen2.5:7b`, `mistral:7b`
- Better reasoning if your machine can handle it: `qwen2.5:14b`, `llama3.1:70b`

For low-memory machines, start with 4B to 8B quantized models.

## Usage

1. Start the backend and frontend.
2. Select provider and model.
3. Click `Check model`.
4. Choose role, difficulty, and interview type.
5. Paste CV highlights or a job description if available.
6. Click `Start new interview`.
7. Type an answer and click `Send answer`.
8. Review score, rubric, feedback, and the next question.
9. Export Markdown or PDF report when done.

## Troubleshooting

- `Cannot reach ollama`: run `ollama serve` or open the Ollama app.
- `model is not installed`: run `ollama pull <model>`.
- LM Studio health fails: confirm the local server is running on `http://localhost:1234/v1`.
- Slow responses: use a smaller model, lower `LOCAL_LLM_MAX_TOKENS`, or close other heavy apps.
- Microphone fails: continue with text input. Voice is optional.
- PDF export fails: install `reportlab` with `pip install reportlab`.

## Tests

```bash
source .venv/bin/activate
pytest
```

## Future Improvements

- True token streaming in the UI.
- Better PDF/DOCX resume parsing.
- Charts for long-term progress across sessions.
- Separate small local model for classification when available.
- Browser-side speech recognition fallback where supported.

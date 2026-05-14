# Local Interview Agent

A local-first mock interview coach for role-specific practice, answer scoring, feedback, follow-up questions, progress tracking, and report export. It runs offline with Ollama or LM Studio by default, and can optionally route to OpenAI, Claude, Gemini, Grok/xAI, or OpenAI-compatible endpoints when API keys and privacy policy allow it.

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
- Supports a provider abstraction layer and MCP-ready tool registry.

## Architecture

```text
frontend/
  Vendored LobeChat source UI integrated with the Interview Agent backend

backend/main.py
  FastAPI routes, uploads, report export, model health checks

agents/interview_agent.py
  intent routing, guardrails, orchestration, scoring, follow-up generation

providers/
  Provider interface, Ollama, LM Studio, OpenAI-compatible, OpenAI, Claude, Gemini, xAI, routing

mcp/
  MCP server registry, stdio client scaffold, tool whitelist, context filtering, audit logging

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
- Node.js 20 or newer
- pnpm, or Corepack enabled
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
pnpm --dir frontend install
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
./run.sh
```

Open `http://localhost:3010`.

For Docker production-style mode:

```bash
docker compose up --build
```

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

## Hybrid Providers

Cloud providers are optional and disabled unless configured through environment variables. See:

- `docs/PROVIDERS.md`
- `docs/ARCHITECTURE.md`

Supported provider IDs:

- `ollama`
- `lmstudio`
- `openai_compatible`
- `openai`
- `anthropic`
- `gemini`
- `xai`

Privacy modes:

- `local_only`: only local models.
- `hybrid`: local first, cloud fallback when allowed.
- `cloud_allowed`: configured cloud provider can be used.

## MCP

MCP support is secure-by-default. Servers are disabled until configured, tools must be whitelisted, tool descriptions are hidden from the model unless explicitly enabled, and calls are audited.

See `docs/MCP_SETUP.md`.

## Primary LobeChat UI

The project now uses LobeChat as the primary frontend by exposing the Interview Agent backend as an OpenAI-compatible provider.

```bash
./run.sh
```

Open:

```text
http://localhost:3010
```

See `docs/LOBECHAT_INTEGRATION.md`.

Example registry:

```bash
configs/mcp_servers.yaml
```

Example local server:

```bash
tools/example_mcp_server.py
```

## Usage

1. Start the platform with `./run.sh`.
2. Open LobeChat at `http://localhost:3010`.
3. Select `Interview Coach` as the model.
4. Start a technical, behavioral, HR, leadership, system design, ML/AI, or UN/INGO mock interview in chat.
5. Paste CV highlights or a job description when you want personalized coaching.
6. Answer naturally and review the score, rubric, stronger answer, and follow-up question.

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

## Docker

```bash
docker compose up --build
```

When using Ollama from Docker, point `OLLAMA_BASE_URL` to your host, for example `http://host.docker.internal:11434`.

## Future Improvements

- True token streaming in the UI.
- Better PDF/DOCX resume parsing.
- Charts for long-term progress across sessions.
- Separate small local model for classification when available.
- Browser-side speech recognition fallback where supported.

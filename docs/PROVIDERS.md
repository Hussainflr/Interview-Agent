# Provider Setup

The app starts in fully local mode.

## Ollama

```bash
ollama pull qwen3:4b
ollama serve
```

`.env`:

```bash
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_MODEL=qwen3:4b
PRIVACY_MODE=local_only
```

## LM Studio

Start the LM Studio local server, then use:

```bash
LOCAL_LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=local-model
```

## OpenAI-Compatible Local APIs

Use this for vLLM, LocalAI, llama.cpp server, or other compatible endpoints.

```bash
LOCAL_LLM_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_BASE_URL=http://localhost:8001/v1
OPENAI_COMPATIBLE_MODEL=local-model
PRIVACY_MODE=local_only
```

## Optional Cloud Providers

Cloud providers stay disabled until API keys are present and privacy mode allows them.

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
XAI_API_KEY=...
PRIVACY_MODE=hybrid
```

Recommended pattern:

- Use `local_only` for CVs, job descriptions, and private interview history.
- Use `hybrid` only when you are comfortable sending non-sensitive prompts to cloud providers.
- Use `cloud_allowed` for explicit cloud testing.

# Interview Agent Frontend Integration

This directory is a vendored LobeChat frontend source tree. The previous custom Next.js frontend has been removed.

The Interview Agent backend is integrated through LobeChat's OpenAI-compatible provider settings:

```bash
ENABLED_OPENAI=1
OPENAI_API_KEY=interview-local-key
OPENAI_PROXY_URL=http://127.0.0.1:8000/v1
OPENAI_MODEL_LIST=-all,+interview-agent-local=Interview Coach,+interview-agent-hybrid=Interview Coach Hybrid
ENABLED_OLLAMA=1
OLLAMA_PROXY_URL=http://127.0.0.1:11434
```

Run from the repository root:

```bash
./run.sh
```

The source dev server runs on:

```text
http://localhost:3010
```

Docker production mode runs on:

```bash
docker compose up --build
```

```text
http://localhost:3210
```

Keep interview-specific backend logic in the Python backend. Frontend changes here should be limited to LobeChat product customization, assistant presets, branding, plugin panels, or settings improvements.

# Architecture Overview

## Design Goals

- Local-first by default: Ollama and LM Studio work without cloud keys.
- Hybrid capable: OpenAI, Claude, Gemini, Grok/xAI, and OpenAI-compatible endpoints are optional providers.
- Provider-neutral agents: interview logic calls `ModelRouter`, not vendor SDKs.
- MCP-ready with least privilege: MCP servers are registered, disabled by default, whitelisted per tool, and audited.

## Main Modules

```text
frontend/
  Provider/model controls, privacy mode, MCP status, interview UI

backend/
  FastAPI API, session endpoints, provider endpoints, MCP endpoints

agents/
  InterviewAgent orchestration, intent routing, scoring, feedback

providers/
  Unified AIProvider interface, HTTP adapters, model router

mcp/
  MCP registry, stdio client, permission policy, audit logging

tools/
  Example local MCP server

prompts/
  Reusable prompt templates
```

## Provider Interface

Every provider adapter follows:

- `chat()`
- `stream()`
- `embeddings()`
- `tool_calls()`
- `health_check()`
- `model_list()`

Current adapters:

- `ollama`
- `lmstudio`
- `openai_compatible`
- `openai`
- `anthropic`
- `gemini`
- `xai`

The cloud adapters use direct HTTP calls instead of mandatory SDK packages. This keeps setup simple and preserves offline installs.

## Routing Policy

`routing.privacy_mode` controls provider selection:

- `local_only`: only local providers can be used.
- `hybrid`: local providers are tried first; cloud is fallback when allowed.
- `cloud_allowed`: configured provider/fallback chain can include cloud.

Sensitive context, such as pasted CVs or job descriptions, is kept local unless `allow_cloud_for_sensitive_context` is explicitly enabled.

## MCP Security Model

The MCP layer is secure by default:

- Servers are disabled until explicitly enabled in `configs/mcp_servers.yaml`.
- Tools must be listed in `allowed_tools`.
- Only configured transports are allowed.
- Tool descriptions are not exposed to models unless explicitly enabled.
- Tool calls and failures are written to `outputs/audit/mcp_audit.jsonl`.
- Tool arguments and responses pass through simple context filtering.

This project currently includes a minimal stdio MCP client to avoid adding mandatory runtime dependencies. A production deployment can replace `mcp/client.py` with the official MCP SDK while keeping `MCPManager` as the application boundary.

## Framework Decision

- LangChain/LangGraph: useful for large workflow graphs, but currently heavier than needed.
- LiteLLM/OpenRouter: useful as optional future provider gateways, but they would add external dependency and routing policy complexity.
- AutoGen/CrewAI: good for multi-agent demos, but unnecessary for this focused interview flow.
- MCP SDKs: recommended for production-grade MCP clients/servers; kept optional here to preserve local-first simplicity.

The current architecture uses small internal interfaces first. That makes framework adoption easy later without forcing it today.

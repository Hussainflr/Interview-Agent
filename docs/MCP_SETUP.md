# MCP Setup Guide

MCP support is available but locked down by default.

## Enable The Example Server

Edit `configs/mcp_servers.yaml`:

```yaml
servers:
  - id: local_tools
    name: Local Safe Tools
    enabled: true
    transport: stdio
    command: python
    args:
      - tools/example_mcp_server.py
    allowed_tools:
      - echo
      - session_summary
    allow_file_access: false
```

Restart the backend, then visit the app settings panel or call:

```bash
curl http://127.0.0.1:8000/api/mcp/servers
curl http://127.0.0.1:8000/api/mcp/tools
```

## Security Rules

- Do not enable random MCP servers from the internet.
- Keep `default_policy: deny`.
- Whitelist only tools you understand.
- Avoid file or shell tools unless they are sandboxed and scoped to a safe directory.
- Keep `expose_tool_descriptions_to_model: false` unless you need autonomous tool selection.
- Review `outputs/audit/mcp_audit.jsonl`.

## Why So Strict?

MCP tool descriptions, tool responses, and server transports can become prompt-injection or exfiltration channels. This project treats MCP servers as untrusted until configured otherwise.

#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


TOOLS = [
    {
        "name": "echo",
        "description": "Return the provided text. Use only for local testing.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "session_summary",
        "description": "Create a short session summary from provided text.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]


def respond(request_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error:
        payload["error"] = {"code": -32000, "message": error}
    else:
        payload["result"] = result or {}
    print(json.dumps(payload), flush=True)


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        request = json.loads(line)
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            respond(request_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "example-local-tools", "version": "0.1.0"}})
        elif method == "tools/list":
            respond(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            if name == "echo":
                respond(request_id, {"content": [{"type": "text", "text": args.get("text", "")}]})
            elif name == "session_summary":
                text = args.get("text", "")
                summary = text[:500] + ("..." if len(text) > 500 else "")
                respond(request_id, {"content": [{"type": "text", "text": summary}]})
            else:
                respond(request_id, error=f"Unknown tool: {name}")
        else:
            respond(request_id, {})


if __name__ == "__main__":
    main()

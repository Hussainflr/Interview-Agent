from __future__ import annotations

import json
import subprocess
import threading
from dataclasses import dataclass
from typing import Any

from mcp.security import MCPSecurityPolicy


@dataclass
class MCPTool:
    server_id: str
    name: str
    description: str
    input_schema: dict[str, Any]


class StdioMCPClient:
    """Minimal JSON-RPC stdio MCP client.

    This intentionally implements only discovery and tool calls needed by this
    project. Production deployments can replace it with the official MCP SDK
    without changing the manager/provider-facing shape.
    """

    def __init__(self, server: dict[str, Any], policy: MCPSecurityPolicy):
        self.server = server
        self.policy = policy
        self.process: subprocess.Popen[str] | None = None
        self._next_id = 1
        self._lock = threading.Lock()

    def start(self) -> None:
        self.policy.assert_server_allowed(self.server)
        if self.process:
            return
        self.process = subprocess.Popen(
            [self.server["command"], *self.server.get("args", [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.server.get("cwd") or None,
        )
        self._request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "interview-agent", "version": "0.3.0"}})

    def list_tools(self) -> list[MCPTool]:
        self.start()
        response = self._request("tools/list", {})
        tools = []
        for item in response.get("tools", []):
            name = item.get("name", "")
            try:
                self.policy.assert_tool_allowed(self.server, name)
            except Exception:
                continue
            tools.append(
                MCPTool(
                    server_id=self.server["id"],
                    name=name,
                    description=self.policy.filter_context(item.get("description", "")),
                    input_schema=item.get("inputSchema", {}),
                )
            )
        return tools

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.start()
        self.policy.assert_tool_allowed(self.server, tool_name)
        safe_args = json.loads(self.policy.filter_context(json.dumps(arguments)))
        self.policy.audit("tool_call_requested", {"server": self.server["id"], "tool": tool_name})
        response = self._request("tools/call", {"name": tool_name, "arguments": safe_args})
        content = response.get("content", [])
        filtered = self.policy.filter_context(json.dumps(content))
        self.policy.audit("tool_call_completed", {"server": self.server["id"], "tool": tool_name})
        return {"content": json.loads(filtered) if filtered else []}

    def stop(self) -> None:
        if self.process:
            self.process.terminate()
            self.process = None

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MCP process is not running.")
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
            self.process.stdin.flush()
            while True:
                line = self.process.stdout.readline()
                if not line:
                    raise RuntimeError("MCP server closed stdout.")
                response = json.loads(line)
                if response.get("id") == request_id:
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    return response.get("result", {})

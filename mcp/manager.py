from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mcp.client import MCPTool, StdioMCPClient
from mcp.security import MCPSecurityPolicy


class MCPManager:
    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.mcp = settings.get("mcp", {})
        self.policy = MCPSecurityPolicy(settings)
        self.servers = self._load_servers()
        self.clients: dict[str, StdioMCPClient] = {}

    def list_servers(self) -> list[dict[str, Any]]:
        return [
            {
                "id": server.get("id"),
                "name": server.get("name", server.get("id")),
                "enabled": bool(server.get("enabled", False)),
                "transport": server.get("transport", "stdio"),
                "allowed_tools": server.get("allowed_tools", []),
                "allow_file_access": bool(server.get("allow_file_access", False)),
            }
            for server in self.servers
        ]

    def discover_tools(self) -> list[dict[str, Any]]:
        tools: list[MCPTool] = []
        for server in self.servers:
            if not server.get("enabled", False):
                continue
            if server.get("transport") != "stdio":
                continue
            client = self._client(server)
            try:
                tools.extend(client.list_tools())
            except Exception as exc:
                self.policy.audit("tool_discovery_failed", {"server": server.get("id"), "error": str(exc)})
        return [tool.__dict__ for tool in tools]

    def call_tool(self, server_id: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        server = self._server(server_id)
        client = self._client(server)
        return client.call_tool(tool_name, arguments)

    def tool_specs_for_model(self) -> list[dict[str, Any]]:
        if not self.mcp.get("enabled", True):
            return []
        if not self.mcp.get("expose_tool_descriptions_to_model", False):
            return []
        specs = []
        for tool in self.discover_tools():
            specs.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"{tool['server_id']}__{tool['name']}",
                        "description": tool["description"],
                        "parameters": tool["input_schema"] or {"type": "object", "properties": {}},
                    },
                }
            )
        return specs

    def _load_servers(self) -> list[dict[str, Any]]:
        servers = list(self.mcp.get("servers", []) or [])
        registry_path = self.mcp.get("registry_path")
        if registry_path and Path(registry_path).exists():
            with Path(registry_path).open("r", encoding="utf-8") as f:
                registry = yaml.safe_load(f) or {}
            servers.extend(registry.get("servers", []) or [])
        return servers

    def _server(self, server_id: str) -> dict[str, Any]:
        for server in self.servers:
            if server.get("id") == server_id:
                return server
        raise KeyError(f"MCP server '{server_id}' is not registered.")

    def _client(self, server: dict[str, Any]) -> StdioMCPClient:
        server_id = server["id"]
        if server_id not in self.clients:
            self.clients[server_id] = StdioMCPClient(server, self.policy)
        return self.clients[server_id]

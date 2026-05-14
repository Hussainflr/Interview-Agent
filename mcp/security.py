from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ToolPermissionError(PermissionError):
    pass


class MCPSecurityPolicy:
    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.mcp = settings.get("mcp", {})
        self.security = settings.get("security", {})
        self.audit_path = Path(self.mcp.get("audit_log", "outputs/audit/mcp_audit.jsonl"))
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.blocked_patterns = [
            re.compile(pattern, re.I) for pattern in self.security.get("blocked_secret_patterns", [])
        ]

    def assert_server_allowed(self, server: dict[str, Any]) -> None:
        if not server.get("enabled", False):
            raise ToolPermissionError(f"MCP server '{server.get('id')}' is disabled.")
        if server.get("transport") not in set(self.mcp.get("allowed_transports", ["stdio"])):
            raise ToolPermissionError(f"Transport '{server.get('transport')}' is not allowed.")

    def assert_tool_allowed(self, server: dict[str, Any], tool_name: str) -> None:
        allowed_tools = set(server.get("allowed_tools", []))
        if self.mcp.get("default_policy", "deny") == "deny" and tool_name not in allowed_tools:
            raise ToolPermissionError(f"Tool '{tool_name}' is not whitelisted for server '{server.get('id')}'.")

    def filter_context(self, text: str) -> str:
        filtered = text or ""
        for pattern in self.blocked_patterns:
            filtered = pattern.sub("[REDACTED]", filtered)
        return filtered[: int(self.mcp.get("max_tool_response_chars", 4000))]

    def audit(self, event: str, payload: dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

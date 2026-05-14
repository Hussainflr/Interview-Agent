import pytest

from mcp.security import MCPSecurityPolicy, ToolPermissionError


def test_mcp_policy_denies_unlisted_tool(tmp_path):
    policy = MCPSecurityPolicy(
        {
            "mcp": {"audit_log": str(tmp_path / "audit.jsonl"), "default_policy": "deny", "allowed_transports": ["stdio"]},
            "security": {"blocked_secret_patterns": []},
        }
    )
    server = {"id": "safe", "enabled": True, "transport": "stdio", "allowed_tools": ["echo"]}
    with pytest.raises(ToolPermissionError):
        policy.assert_tool_allowed(server, "read_secrets")


def test_mcp_policy_filters_secret_words(tmp_path):
    policy = MCPSecurityPolicy(
        {
            "mcp": {"audit_log": str(tmp_path / "audit.jsonl"), "max_tool_response_chars": 200},
            "security": {"blocked_secret_patterns": ["API_KEY"]},
        }
    )
    assert "API_KEY" not in policy.filter_context("API_KEY should not pass")

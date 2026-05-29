"""Headless Claude tool_config defaults for delegate/dispatch entrypoints.

Without a minimal ``--mcp-config``, the Claude CLI loads every MCP server
from the user's global config and injects all tool schemas into the prompt,
which can fail instantly with "Prompt is too long" before the task brief runs.
"""
from __future__ import annotations

from pathlib import Path

CLAUDE_DELEGATE_MCP_CONFIG = (
    Path(__file__).resolve().parent / "configs" / "claude-delegate-mcp.json"
)

# Built-in Claude Code tools only — no ``mcp__*`` entries.
CLAUDE_DELEGATE_ALLOWED_TOOLS = (
    "Read,Write,Edit,Bash,Grep,Glob,TodoWrite,WebFetch,WebSearch"
)

_DELEGATE_ENTRYPOINTS = frozenset({"delegate", "dispatch"})


def merge_delegate_claude_tool_config(
    agent_name: str,
    entrypoint: str,
    tool_config: dict | None,
) -> dict | None:
    """Return ``tool_config`` with minimal MCP restrictions for headless Claude.

    Skips merge when the caller already set ``mcp_config_path`` or
    ``allowed_tools`` (e.g. pipeline translation paths via ``dispatch.py``).
    """
    if agent_name != "claude" or entrypoint not in _DELEGATE_ENTRYPOINTS:
        return tool_config
    if not CLAUDE_DELEGATE_MCP_CONFIG.is_file():
        return tool_config
    tc = dict(tool_config or {})
    if tc.get("mcp_config_path") or tc.get("allowed_tools"):
        return tc
    tc["mcp_config_path"] = str(CLAUDE_DELEGATE_MCP_CONFIG)
    tc["allowed_tools"] = CLAUDE_DELEGATE_ALLOWED_TOOLS
    return tc

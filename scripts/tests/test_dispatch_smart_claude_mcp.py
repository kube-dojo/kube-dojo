"""Regression: headless Claude delegate/dispatch must not load user MCP schemas."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime import delegate_config as delegate_config_mod
from agent_runtime.delegate_config import (
    CLAUDE_DELEGATE_ALLOWED_TOOLS,
    CLAUDE_DELEGATE_MCP_CONFIG,
    merge_delegate_claude_tool_config,
)
from agent_runtime import runner
from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.result import ParseResult


def test_delegate_mcp_fixture_is_empty_servers() -> None:
    assert CLAUDE_DELEGATE_MCP_CONFIG.is_file()
    payload = json.loads(CLAUDE_DELEGATE_MCP_CONFIG.read_text(encoding="utf-8"))
    assert payload == {"mcpServers": {}}


def test_merge_skips_non_claude_and_bridge() -> None:
    assert merge_delegate_claude_tool_config("codex", "delegate", None) is None
    assert merge_delegate_claude_tool_config(
        "claude",
        "bridge",
        {"is_new_session": True},
    ) == {"is_new_session": True}


def test_merge_respects_caller_override() -> None:
    custom = {
        "mcp_config_path": "/tmp/custom.mcp.json",
        "allowed_tools": "mcp__rag__verify_word,Read",
    }
    assert merge_delegate_claude_tool_config("claude", "delegate", custom) == custom


@pytest.mark.parametrize("entrypoint", ["delegate", "dispatch"])
def test_merge_applies_minimal_mcp_for_claude_delegate(entrypoint: str) -> None:
    merged = merge_delegate_claude_tool_config("claude", entrypoint, None)
    assert merged is not None
    assert merged["mcp_config_path"] == str(CLAUDE_DELEGATE_MCP_CONFIG)
    assert merged["allowed_tools"] == CLAUDE_DELEGATE_ALLOWED_TOOLS
    assert "mcp__" not in merged["allowed_tools"]


def test_merge_skips_when_fixture_missing() -> None:
    """If the minimal MCP fixture is absent, the merge is a no-op (graceful)."""
    fake_missing = SimpleNamespace(is_file=lambda: False)
    with patch.object(delegate_config_mod, "CLAUDE_DELEGATE_MCP_CONFIG", fake_missing):
        assert merge_delegate_claude_tool_config("claude", "delegate", None) is None
        passthrough = {"is_new_session": True}
        assert (
            merge_delegate_claude_tool_config("claude", "delegate", passthrough)
            is passthrough
        )


def test_claude_adapter_emits_mcp_flags_for_delegate_tool_config() -> None:
    tc = merge_delegate_claude_tool_config("claude", "delegate", None)
    plan = ClaudeAdapter().build_invocation(
        prompt="brief",
        mode="danger",
        cwd=Path.cwd(),
        model="claude-sonnet-4-6",
        task_id="t1",
        session_id=None,
        tool_config=tc,
    )
    assert "--mcp-config" in plan.cmd
    idx = plan.cmd.index("--mcp-config")
    assert plan.cmd[idx + 1] == str(CLAUDE_DELEGATE_MCP_CONFIG)
    tools_idx = plan.cmd.index("--allowedTools")
    allowed = plan.cmd[tools_idx + 1]
    assert allowed == CLAUDE_DELEGATE_ALLOWED_TOOLS
    assert "mcp__" not in allowed


def test_invoke_passes_delegate_mcp_tool_config_to_claude_adapter() -> None:
    captured: dict[str, object] = {}

    def build_invocation(**kw):
        captured["tool_config"] = kw["tool_config"]
        return InvocationPlan(cmd=["claude", "-p"], cwd=kw["cwd"])

    adapter = type(
        "StubClaude",
        (),
        {
            "default_model": "claude-sonnet-4-6",
            "supported_modes": frozenset({"read-only", "workspace-write", "danger"}),
            "build_invocation": staticmethod(build_invocation),
            "liveness_signal_paths": staticmethod(lambda _plan: ()),
            "parse_response": staticmethod(
                lambda **_kw: ParseResult(ok=True, response="ok"),
            ),
        },
    )()
    proc = SimpleNamespace(
        returncode=0,
        stdin=None,
        poll=lambda: 0,
        kill=lambda: None,
        wait=lambda timeout=None: 0,
    )
    state = SimpleNamespace(stdout_lines=["ok"], stderr_lines=[])

    with (
        patch.object(runner, "_load_adapter", return_value=adapter),
        patch.object(runner, "has_headroom", return_value=(True, "")),
        patch.object(runner, "build_agent_env", return_value={}),
        patch.object(runner.subprocess, "Popen", return_value=proc),
        patch.object(runner, "start_watchdog", return_value=(state, [])),
        patch.object(runner, "stop_watchdog"),
        patch.object(runner, "write_record"),
    ):
        runner.invoke(
            "claude",
            "search task",
            mode="read-only",
            cwd=Path("/tmp"),
            entrypoint="delegate",
            skip_headroom_check=True,
        )

    tc = captured["tool_config"]
    assert isinstance(tc, dict)
    assert tc["mcp_config_path"] == str(CLAUDE_DELEGATE_MCP_CONFIG)
    assert "mcp__" not in tc["allowed_tools"]

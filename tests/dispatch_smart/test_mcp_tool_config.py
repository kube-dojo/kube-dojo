from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from agent_runtime.adapters.deepseek import (  # noqa: E402
    DeepSeekAdapter,
    translate_mcp_prefix_for_hermes,
)
from agent_runtime.tool_config import build_mcp_tool_config  # noqa: E402


@pytest.mark.parametrize("agent", ["deepseek", "grok", "qwen"])
def test_build_mcp_tool_config_hermes_lane(agent: str) -> None:
    tool_config, diagnostics = build_mcp_tool_config(agent, mcp_servers=["sources"])

    assert tool_config == {"hermes_mcp_servers": ["sources"]}
    assert diagnostics["resolution_status"] == "ok"
    assert diagnostics["requested_servers"] == ["sources"]
    assert diagnostics["resolved_servers"] == ["sources"]
    assert diagnostics["config_path"].endswith(".hermes/config.yaml")


def test_translate_mcp_prefix_for_hermes() -> None:
    prompt = (
        "Use mcp__sources__search_text and mcp__sources__verify_word "
        "before writing."
    )
    rewritten = translate_mcp_prefix_for_hermes(prompt)

    assert rewritten == (
        "Use mcp_sources_search_text and mcp_sources_verify_word "
        "before writing."
    )
    assert "mcp__sources__" not in rewritten


def test_deepseek_adapter_rewrites_sources_prefix_when_requested() -> None:
    adapter = DeepSeekAdapter()
    plan = adapter.build_invocation(
        prompt="Call mcp__sources__search_text for corpus lookup.",
        mode="workspace-write",
        cwd=Path.cwd(),
        model="deepseek-v4-pro",
        task_id="test-task",
        session_id=None,
        tool_config={"hermes_mcp_servers": ["sources"]},
    )

    oneshot_arg = next(arg for arg in plan.cmd if arg.startswith("--oneshot="))
    assert "mcp_sources_search_text" in oneshot_arg
    assert "mcp__sources__" not in oneshot_arg


def test_deepseek_adapter_leaves_prompt_unmodified_without_sources_mcp() -> None:
    adapter = DeepSeekAdapter()
    prompt = "Call mcp__sources__search_text for corpus lookup."
    plan = adapter.build_invocation(
        prompt=prompt,
        mode="workspace-write",
        cwd=Path.cwd(),
        model="deepseek-v4-pro",
        task_id="test-task",
        session_id=None,
        tool_config=None,
    )

    oneshot_arg = next(arg for arg in plan.cmd if arg.startswith("--oneshot="))
    assert oneshot_arg == f"--oneshot={prompt}"

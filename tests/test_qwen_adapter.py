"""Unit tests for the ``QwenAdapter`` Hermes integration (openrouter provider)."""
from __future__ import annotations

from pathlib import Path

from agent_runtime.adapters.qwen import QwenAdapter


def test_build_invocation_read_only(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.qwen.shutil.which", lambda _: "hermes")
    adapter = QwenAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    cmd = plan.cmd
    assert cmd == [
        "hermes",
        "-m",
        "qwen/qwen3.6-plus",
        "--provider",
        "openrouter",
        "-t",
        "web",
        "--oneshot=p",
    ]
    assert "--yolo" not in cmd
    assert "-z" not in cmd


def test_build_invocation_workspace_write(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.qwen.shutil.which", lambda _: "hermes")
    adapter = QwenAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="workspace-write",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    cmd = plan.cmd
    assert "--yolo" in cmd
    toolsets = cmd[cmd.index("-t") + 1]
    assert toolsets == "web,file,terminal,code_execution,todo"


def test_build_invocation_danger(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.qwen.shutil.which", lambda _: "hermes")
    adapter = QwenAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="danger",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    toolsets = plan.cmd[plan.cmd.index("-t") + 1]
    assert "memory" in toolsets
    assert "skills" in toolsets


def test_model_override(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.qwen.shutil.which", lambda _: "hermes")
    adapter = QwenAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model="qwen/qwen3.6-flash",
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[plan.cmd.index("-m") + 1] == "qwen/qwen3.6-flash"


def test_parse_response_strips_hermes_banner() -> None:
    adapter = QwenAdapter()
    result = adapter.parse_response(
        stdout="💡 Python project detected. Run with hermes -z.\n\nAnswer",
        stderr="",
        returncode=0,
        output_file=None,
        plan=None,
        call_start_time=None,
    )

    assert result.ok is True
    assert result.response == "Answer"


def test_parse_response_detects_rate_limit() -> None:
    adapter = QwenAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="rate limit exceeded",
        returncode=1,
        output_file=None,
        plan=None,
        call_start_time=None,
    )

    assert result.rate_limited is True
    assert result.ok is False


def test_qwen_hermes_argv_puts_oneshot_last(monkeypatch) -> None:
    """Hermes --oneshot=<prompt> must follow --provider and -m (equals-form)."""
    monkeypatch.setattr("agent_runtime.adapters.qwen.shutil.which", lambda _: "hermes")
    adapter = QwenAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    cmd = plan.cmd
    assert cmd[-1] == "--oneshot=hello"
    assert "-z" not in cmd
    assert cmd[0] == "hermes"
    assert cmd[cmd.index("-m") + 1] == "qwen/qwen3.6-plus"
    assert cmd[cmd.index("--provider") + 1] == "openrouter"


def test_qwen_hermes_argv_handles_flag_like_prompt(monkeypatch) -> None:
    """Flag-like prompts bind via --oneshot= so argparse never treats them as flags."""
    monkeypatch.setattr("agent_runtime.adapters.qwen.shutil.which", lambda _: "hermes")
    adapter = QwenAdapter()
    plan = adapter.build_invocation(
        prompt="--provider",
        mode="read-only",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    cmd = plan.cmd
    assert "--oneshot=--provider" in cmd
    assert "-z" not in cmd

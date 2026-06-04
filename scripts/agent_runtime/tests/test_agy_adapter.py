"""Unit tests for the ``AgyAdapter`` Antigravity CLI integration."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_runtime.adapters.agy import AgyAdapter


def _build(mode: str) -> list[str]:
    adapter = AgyAdapter()
    plan = adapter.build_invocation(
        prompt="p",
        mode=mode,
        cwd=Path("/tmp"),
        model="gemini-3.5-flash-high",
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    return plan.cmd


def test_build_invocation_always_includes_dangerously_skip(monkeypatch) -> None:
    """--dangerously-skip-permissions is unconditional across all modes.

    Agy has no finer-grained permission model than this single flag, and
    leaving it off causes interactive permission prompts that hang a
    headless dispatch. dispatch_smart.py also forces mode=danger as a
    second line of defense, but the adapter must hold the invariant on
    its own so direct runner.invoke callers get the right behavior.
    """
    monkeypatch.setattr("agent_runtime.adapters.agy.shutil.which", lambda _: "agy")

    for mode in ("read-only", "workspace-write", "danger"):
        cmd = _build(mode)
        assert cmd == [
            "agy",
            "-p",
            "p",
            "--dangerously-skip-permissions",
            "--model",
            "Gemini 3.5 Flash (High)",
        ], (
            f"mode={mode} must produce the same cmd because agy has no "
            f"mode-specific permission flag"
        )


def test_build_invocation_maps_model_slug(monkeypatch) -> None:
    """A runtime model slug is mapped to agy's `--model` display string."""
    monkeypatch.setattr("agent_runtime.adapters.agy.shutil.which", lambda _: "agy")
    adapter = AgyAdapter()

    plan = adapter.build_invocation(
        prompt="p",
        mode="workspace-write",
        cwd=Path("/tmp"),
        model="gemini-3.1-pro-high",
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    assert "--model" in plan.cmd
    assert plan.cmd[plan.cmd.index("--model") + 1] == "Gemini 3.1 Pro (High)"


def test_build_invocation_accepts_display_string(monkeypatch) -> None:
    """Passing the canonical display string maps to itself (idempotent)."""
    monkeypatch.setattr("agent_runtime.adapters.agy.shutil.which", lambda _: "agy")
    adapter = AgyAdapter()

    plan = adapter.build_invocation(
        prompt="p",
        mode="workspace-write",
        cwd=Path("/tmp"),
        model="Gemini 3.1 Pro (High)",
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[plan.cmd.index("--model") + 1] == "Gemini 3.1 Pro (High)"


def test_build_invocation_unknown_model_falls_back_to_default(monkeypatch) -> None:
    """A stale/unknown slug (e.g. legacy 'tui-controlled') degrades to the
    adapter default rather than passing an invalid --model value."""
    monkeypatch.setattr("agent_runtime.adapters.agy.shutil.which", lambda _: "agy")
    adapter = AgyAdapter()

    plan = adapter.build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model="tui-controlled",
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[plan.cmd.index("--model") + 1] == "Gemini 3.5 Flash (High)"


def test_build_invocation_with_session_id(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.agy.shutil.which", lambda _: "agy")
    adapter = AgyAdapter()
    session_id = "123e4567-e89b-12d3-a456-426614174000"

    plan = adapter.build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model="gemini-3.5-flash-high",
        task_id=None,
        session_id=session_id,
        tool_config=None,
    )

    assert f"--conversation={session_id}" in plan.cmd


def test_build_invocation_uses_home_fallback(monkeypatch) -> None:
    monkeypatch.setattr("agent_runtime.adapters.agy.shutil.which", lambda _: None)
    adapter = AgyAdapter()

    plan = adapter.build_invocation(
        prompt="p",
        mode="read-only",
        cwd=Path("/tmp"),
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[0].endswith("/.local/bin/agy")
    assert plan.stdin_payload == ""


def test_parse_response_happy_path() -> None:
    adapter = AgyAdapter()
    result = adapter.parse_response(
        stdout="Answer\n",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "Answer"
    assert result.rate_limited is False
    assert result.session_id is None
    assert result.tokens is None
    # stderr_excerpt is documented as a diagnostic signal — None when no
    # diagnostic output. Don't pollute it with informational notes.
    assert result.stderr_excerpt is None


def test_parse_response_empty_stdout_happy_returncode_fails() -> None:
    """Successful exit + no stdout is not a successful call."""
    adapter = AgyAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is False
    assert result.response == ""
    assert result.rate_limited is False
    assert result.stderr_excerpt is None


def test_parse_response_detects_rate_limit() -> None:
    adapter = AgyAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="RESOURCE_EXHAUSTED: quota exceeded",
        returncode=1,
        output_file=None,
    )

    assert result.rate_limited is True
    assert result.ok is False
    assert result.response == ""

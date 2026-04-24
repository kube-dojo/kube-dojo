from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import citation_backfill  # noqa: E402


def test_dispatch_gemini_uses_sys_executable_and_absolute_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: dispatch_gemini must launch dispatch.py with sys.executable
    and an absolute path. The previous implementation probed
    `Path("scripts/dispatch.py")` and `Path(".venv/bin/python")` relative to
    cwd — which silently succeeded in the primary repo but failed in git
    worktrees (no `.venv`) with `PermissionError: scripts/dispatch.py`
    because subprocess.run tried to exec the .py file directly without an
    interpreter."""
    captured: dict[str, object] = {}

    class _Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd: list[str], **kwargs: object) -> _Completed:
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return _Completed()

    monkeypatch.setattr(subprocess, "run", _fake_run)

    ok, _ = citation_backfill.dispatch_gemini("hello")

    assert ok is True
    cmd = captured["cmd"]
    assert isinstance(cmd, list) and cmd
    assert cmd[0] == sys.executable, f"expected sys.executable, got {cmd[0]!r}"
    dispatch_arg = Path(cmd[1])
    assert dispatch_arg.is_absolute(), f"dispatch.py path must be absolute, got {cmd[1]!r}"
    assert dispatch_arg.name == "dispatch.py"
    assert "gemini" in cmd


def test_dispatch_gemini_default_timeout_unchanged_for_research_inject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_research / run_inject still use the original 900s budget.

    citation_backfill.dispatch_gemini is shared between whole-module
    work (research/inject — legitimately long prompts) and the short
    per-finding URL-candidate path. The former must NOT get the short
    timeout: a content-generation call can legitimately run 5-10 min,
    and a 120s cap there would turn every real generation into a false
    timeout. The per-finding cap lives at the call site instead.
    """
    captured: dict[str, object] = {}

    class _Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd: list[str], **kwargs: object) -> _Completed:
        captured["cmd"] = cmd
        captured["timeout"] = kwargs.get("timeout")
        return _Completed()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    citation_backfill.dispatch_gemini("hello")  # no explicit timeout

    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    ti = cmd.index("--timeout")
    inner = int(cmd[ti + 1])
    outer = captured["timeout"]
    assert inner == outer
    assert inner == citation_backfill.GEMINI_DEFAULT_TIMEOUT
    assert inner >= 600, (
        f"default Gemini timeout is {inner}s — whole-module research/"
        "inject needs the longer budget; per-finding caps belong at the "
        "call site"
    )


def test_dispatch_gemini_honors_explicit_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per-finding callers must be able to pass a short timeout.

    Both the inner `--timeout` arg to dispatch.py and the outer
    subprocess.run(timeout=...) must reflect the caller's value — a
    drift would let the outer watchdog fire while the inner argument
    lied about its own budget.
    """
    captured: dict[str, object] = {}

    class _Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd: list[str], **kwargs: object) -> _Completed:
        captured["cmd"] = cmd
        captured["timeout"] = kwargs.get("timeout")
        return _Completed()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    citation_backfill.dispatch_gemini("hello", timeout=120)

    cmd = captured["cmd"]
    ti = cmd.index("--timeout")
    assert int(cmd[ti + 1]) == 120
    assert captured["timeout"] == 120


def test_dispatch_gemini_timeout_error_message_reflects_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the outer watchdog fires, the error string must name the
    actual configured budget — operators use this to distinguish a
    per-finding timeout (120s) from a whole-module one (900s) in logs.
    """
    def _raise_timeout(cmd: list[str], **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout") or 0)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)
    ok, msg = citation_backfill.dispatch_gemini("hello", timeout=120)
    assert ok is False
    assert "120" in msg, f"error should name the budget; got {msg!r}"

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import citation_backfill  # noqa: E402


def test_dispatch_gemini_launches_dispatch_with_venv_python_and_absolute_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: dispatch_gemini must launch dispatch.py with the
    primary-checkout venv's Python (AGENTS.md §3 forbids sys.executable
    — it misses venv-only deps) and an absolute path to dispatch.py.

    An earlier revision used `sys.executable`; PR #374 review (Codex)
    caught the rule violation. The interpreter path is derived from
    REPO_ROOT (i.e. from __file__), so it stays correct when the
    script is invoked from a git worktree — the worktree shares the
    primary checkout's .venv via this absolute path.
    """
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
    interpreter = Path(cmd[0])
    assert interpreter.is_absolute(), f"interpreter must be absolute, got {cmd[0]!r}"
    assert interpreter.name == "python", f"expected .venv/bin/python, got {cmd[0]!r}"
    assert ".venv" in interpreter.parts, (
        f"must use .venv python (AGENTS.md §3 bans sys.executable), got {cmd[0]!r}"
    )
    assert cmd[0] != sys.executable or sys.executable.endswith("/.venv/bin/python"), (
        "dispatch_gemini must not use sys.executable (AGENTS.md §3)"
    )
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


# ---- Claude dispatcher --------------------------------------------------


def test_dispatch_claude_raises_on_peak_hours_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Claude peak-hours refusal must NOT be flattened into a generic
    False — that would let resolve_module mark the in-flight finding
    as unresolvable. It must raise DispatcherUnavailable so the caller
    leaves the finding in needs_citation and aborts the run for retry.

    Regression guard against the #374 review finding (Codex).
    """
    class _P:
        returncode = 2
        stdout = ""
        stderr = (
            "⏸ Claude peak hours in effect (14:00-20:00 local Mon-Fri, "
            "currently 15:xx). Refusing to dispatch to avoid 2x pricing."
        )

    def fake_run(cmd: list[str], **kwargs: object) -> _P:
        return _P()

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(citation_backfill.DispatcherUnavailable, match="peak hours"):
        citation_backfill.dispatch_claude("hi", timeout=180)


def test_dispatch_claude_raises_on_budget_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per-process call-budget exhaustion is also retryable — next
    fresh process gets a new budget. Must raise DispatcherUnavailable,
    not return False."""
    class _P:
        returncode = 2
        stdout = ""
        stderr = "Claude call budget exhausted after 50 calls; restart to reset."

    monkeypatch.setattr(subprocess, "run", lambda c, **kw: _P())
    with pytest.raises(citation_backfill.DispatcherUnavailable, match="budget"):
        citation_backfill.dispatch_claude("hi", timeout=180)


def test_dispatch_claude_returns_false_on_ordinary_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-unavailability failures (e.g. malformed prompt, CLI crash)
    still return (False, message) as before — those ARE the "the LLM
    got nowhere" class and should fall through to unresolvable."""
    class _P:
        returncode = 1
        stdout = ""
        stderr = "TypeError: something broke"

    monkeypatch.setattr(subprocess, "run", lambda c, **kw: _P())
    ok, msg = citation_backfill.dispatch_claude("hi", timeout=180)
    assert ok is False
    assert "TypeError" in msg

"""Tests for ``scripts.quality.dispatchers``."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality import dispatchers  # noqa: E402


def test_writer_for_index_returns_codex_writes_claude_reviews_for_every_index() -> None:
    """Even/odd alternation was retired 2026-04-25 after empirical evidence
    that claude-as-writer lands ~440-line modules vs codex's 1500–2000+.

    Regression guard: every index — even, odd, large, zero — must return
    ``("codex", "claude")``. Cross-family review is still satisfied
    (different model families).
    """
    for idx in (0, 1, 2, 50, 100, 741, 742, 1000):
        assert dispatchers.writer_for_index(idx) == ("codex", "claude"), idx


def test_tiebreaker_is_gemini() -> None:
    assert dispatchers.tiebreaker_agent() == "gemini"


def test_dispatch_rejects_unknown_agent() -> None:
    with pytest.raises(ValueError, match="unknown agent"):
        dispatchers.dispatch("grok", "prompt", timeout=10)  # type: ignore[arg-type]


def test_looks_unavailable_detects_peak_hours() -> None:
    assert dispatchers._looks_unavailable("Error: Claude peak hours in effect until 20:00")


def test_looks_unavailable_detects_budget() -> None:
    assert dispatchers._looks_unavailable("ClaudeUnavailableError: call budget exhausted")


def test_looks_unavailable_detects_rate_limit() -> None:
    assert dispatchers._looks_unavailable("gemini: RATE_LIMIT — slow down")


def test_looks_unavailable_false_for_real_errors() -> None:
    assert not dispatchers._looks_unavailable("SyntaxError: unexpected token")
    assert not dispatchers._looks_unavailable("")


def test_dispatcher_unavailable_is_runtime_error() -> None:
    # Sanity — callers rely on catching RuntimeError for retry logic.
    assert issubclass(dispatchers.DispatcherUnavailable, RuntimeError)


def test_dispatch_result_fields_populated(monkeypatch) -> None:
    """Dispatch surfaces stdout/stderr/returncode/duration from subprocess."""
    import subprocess

    class FakeProc:
        stdout = "verdict output"
        stderr = ""
        returncode = 0

    def fake_run(*args, **kwargs):
        return FakeProc()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = dispatchers.dispatch("gemini", "prompt", timeout=10)
    assert result.ok is True
    assert result.stdout == "verdict output"
    assert result.returncode == 0
    assert result.agent == "gemini"
    assert result.duration_sec >= 0


def test_dispatch_raises_unavailable_on_marker(monkeypatch) -> None:
    import subprocess

    class FakeProc:
        stdout = ""
        stderr = "Claude peak hours in effect"
        returncode = 1

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())
    with pytest.raises(dispatchers.DispatcherUnavailable):
        dispatchers.dispatch("claude", "prompt", timeout=10)


def test_dispatch_returns_failure_not_unavailable_for_real_errors(monkeypatch) -> None:
    """Non-zero exit without an unavailability marker must surface as
    ``ok=False``, not raise — caller decides retry vs FAILED."""
    import subprocess

    class FakeProc:
        stdout = ""
        stderr = "SyntaxError in prompt"
        returncode = 1

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())
    result = dispatchers.dispatch("codex", "prompt", timeout=10)
    assert result.ok is False
    assert "SyntaxError" in result.stderr


def test_dispatch_timeout_returns_failure(monkeypatch) -> None:
    import subprocess

    def raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="fake", timeout=10)

    monkeypatch.setattr(subprocess, "run", raise_timeout)
    result = dispatchers.dispatch("gemini", "prompt", timeout=10)
    assert result.ok is False
    assert "timeout" in result.stderr.lower()


def test_dispatch_passes_no_tools_for_claude_when_tools_disabled(monkeypatch) -> None:
    """Claude writer/reviewer dispatches must propagate ``--no-tools`` so
    the CLI returns text-only output. Without it, Claude in print mode
    is agentic and modifies files in cwd.

    Regression guard for the k8s-capa-module-1.2-argo-events smoke
    autopsy (Apr 24): writer FAILED with ``no frontmatter delimiter
    found`` because Claude had used Edit/Write to rewrite the worktree
    file and returned only a summary on stdout.
    """
    import subprocess
    captured: dict = {}

    class FakeProc:
        stdout = "ok"
        stderr = ""
        returncode = 0

    def capture_run(cmd, *args, **kwargs):
        captured["cmd"] = list(cmd)
        return FakeProc()

    monkeypatch.setattr(subprocess, "run", capture_run)
    dispatchers.dispatch("claude", "prompt", timeout=10, tools_disabled=True)
    assert "--no-tools" in captured["cmd"]


def test_dispatch_omits_no_tools_when_not_requested(monkeypatch) -> None:
    """Default (citation_verify, translation, etc.) must NOT pass
    ``--no-tools`` — Claude's full tool set is needed there."""
    import subprocess
    captured: dict = {}

    class FakeProc:
        stdout = "ok"
        stderr = ""
        returncode = 0

    monkeypatch.setattr(
        subprocess, "run",
        lambda cmd, *a, **k: (captured.setdefault("cmd", list(cmd)), FakeProc())[1],
    )
    dispatchers.dispatch("claude", "prompt", timeout=10)
    assert "--no-tools" not in captured["cmd"]


def test_dispatch_no_tools_only_for_claude(monkeypatch) -> None:
    """Codex/Gemini have no built-in agentic tools surface in
    ``scripts.dispatch`` (Codex relies on ``--sandbox read-only``),
    so the flag is a no-op for them. Passing it should still not crash
    or pollute the command line.
    """
    import subprocess
    captured: dict = {}

    class FakeProc:
        stdout = "ok"
        stderr = ""
        returncode = 0

    monkeypatch.setattr(
        subprocess, "run",
        lambda cmd, *a, **k: (captured.setdefault("cmd", list(cmd)), FakeProc())[1],
    )
    dispatchers.dispatch("codex", "prompt", timeout=10, tools_disabled=True)
    assert "--no-tools" not in captured["cmd"]
    captured.clear()
    dispatchers.dispatch("gemini", "prompt", timeout=10, tools_disabled=True)
    assert "--no-tools" not in captured["cmd"]

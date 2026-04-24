"""Tests for ``scripts.quality.dispatchers``."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality import dispatchers  # noqa: E402


def test_writer_for_index_even_is_codex_writes() -> None:
    writer, reviewer = dispatchers.writer_for_index(0)
    assert writer == "codex"
    assert reviewer == "claude"


def test_writer_for_index_odd_is_claude_writes() -> None:
    writer, reviewer = dispatchers.writer_for_index(1)
    assert writer == "claude"
    assert reviewer == "codex"


def test_writer_for_index_stable_for_large_even() -> None:
    # Permanent module_index: regression guard on the i%2 rotation.
    assert dispatchers.writer_for_index(742) == ("codex", "claude")
    assert dispatchers.writer_for_index(741) == ("claude", "codex")


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

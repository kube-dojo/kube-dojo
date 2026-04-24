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


def test_dispatch_gemini_uses_short_per_finding_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One slow Gemini call must not block the whole pilot for 15 minutes.

    Guards against a silent regression to 900s — that value is correct
    for the write-path pipeline (whole-module generation) but wrong for
    the short, structured URL-candidate prompt. Both the outer
    subprocess.run timeout AND the inner `--timeout` argument passed to
    dispatch.py must be the short value, and the two must match (a
    mismatch would let the outer watchdog fire first while the inner
    timeout argument lied).
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

    citation_backfill.dispatch_gemini("hello")

    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    # Inner: dispatch.py --timeout <N>
    ti = cmd.index("--timeout")
    inner_timeout = int(cmd[ti + 1])
    # Outer: subprocess.run(..., timeout=<N>)
    outer_timeout = captured["timeout"]
    assert inner_timeout == outer_timeout, (
        "inner --timeout and outer subprocess timeout must match"
    )
    assert inner_timeout <= 180, (
        f"per-finding Gemini timeout is {inner_timeout}s — too long; "
        "one stuck call blocks the whole pilot"
    )
    assert inner_timeout == citation_backfill.GEMINI_PER_FINDING_TIMEOUT

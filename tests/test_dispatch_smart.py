from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "dispatch_smart.py"


def _run_dispatch_smart(args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT)] + args
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_dispatch_smart_danger_requires_worktree() -> None:
    """Dispatching danger mode without --worktree should hard-fail."""
    result = _run_dispatch_smart(["edit", "--mode", "danger", "x"])

    assert result.returncode != 0
    merged_output = (result.stdout + result.stderr).lower()
    assert "danger" in merged_output
    assert "worktree" in merged_output


def test_dispatch_smart_danger_allows_dry_run_with_worktree() -> None:
    """Dry-run should not touch missing worktrees and should still resolve mode checks."""
    result = _run_dispatch_smart(
        ["edit", "--mode", "danger", "--worktree", ".worktrees/foo", "--dry-run", "x"]
    )

    assert result.returncode == 0
    assert "mode=danger" in result.stdout
    assert "[dry-run] task_id=" in result.stdout

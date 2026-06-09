"""Unit tests for the ``AgyAdapter`` (Antigravity CLI) integration.

Regression coverage for #1827: agy sandboxes file ops to
``~/.gemini/antigravity-cli/scratch/`` and ignores the process cwd, so the
dispatch worktree/repo MUST be added to agy's workspace via ``--add-dir <cwd>``
or agy can neither read the file under review nor write authored output into
the repo (the root cause of the s115 "no file written" and s117 "reviewed a
file it never read" fabrication verdicts).
"""
from __future__ import annotations

from pathlib import Path

from agent_runtime.adapters.agy import AgyAdapter


def _plan(monkeypatch, mode: str, cwd: Path):
    monkeypatch.setattr(
        "agent_runtime.adapters.agy.shutil.which", lambda _: "agy"
    )
    adapter = AgyAdapter()
    return adapter.build_invocation(
        prompt="p",
        mode=mode,
        cwd=cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )


def test_add_dir_includes_worktree_workspace_write(monkeypatch) -> None:
    cwd = Path("/repo/.worktrees/x")
    plan = _plan(monkeypatch, "workspace-write", cwd)
    assert "--add-dir" in plan.cmd
    # --add-dir must be immediately followed by the cwd so agy can read+write there
    assert plan.cmd[plan.cmd.index("--add-dir") + 1] == str(cwd)


def test_add_dir_includes_worktree_read_only(monkeypatch) -> None:
    # reviews (read-only) also need the file under review in agy's workspace
    cwd = Path("/repo/.worktrees/y")
    plan = _plan(monkeypatch, "read-only", cwd)
    assert plan.cmd[plan.cmd.index("--add-dir") + 1] == str(cwd)


def test_skip_permissions_present(monkeypatch) -> None:
    plan = _plan(monkeypatch, "danger", Path("/tmp"))
    assert "--dangerously-skip-permissions" in plan.cmd

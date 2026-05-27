from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "dispatch_smart.py"
SCRIPTS_DIR = SCRIPT.parent


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


def test_dispatch_smart_agy_danger_no_worktree_passes_guards() -> None:
    """agy review-class dispatches don't write to disk under danger mode,
    so neither worktree guard should fire. We don't dry-run (which would
    bypass both guards trivially) — instead we assert the worktree-required
    error strings do NOT appear. The dispatch will fail later (no agy
    binary in CI, or agent_runtime import) but BOTH worktree-guards must
    be passed before that downstream failure."""
    result = _run_dispatch_smart(
        ["review", "--agent", "agy", "--mode", "danger", "x"]
    )
    merged_output = (result.stdout or "") + (result.stderr or "")
    # Neither worktree guard should fire for agy.
    assert "--mode danger requires --worktree" not in merged_output, (
        f"agy hit the line-397 guard. stderr={result.stderr!r}"
    )
    assert "requires --worktree to avoid trampling" not in merged_output, (
        f"agy hit the line-411 guard. stderr={result.stderr!r}"
    )


def test_hermes_router_argv_puts_oneshot_last() -> None:
    """Hermes --oneshot=<prompt> must follow --provider and -m (equals-form)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from dispatch_smart import _router_command

    cmd = _router_command("hermes", "qwen-3.6-flash", "hello")
    assert cmd[-1] == "--oneshot=hello"
    assert "-z" not in cmd
    assert cmd[1:5] == ["--provider", "openrouter", "-m", "qwen/qwen3.6-flash"]


def test_hermes_router_argv_handles_flag_like_prompt() -> None:
    """Flag-like prompts bind via --oneshot= so argparse never treats them as flags."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from dispatch_smart import _router_command

    argv = _router_command("hermes", "qwen-3.6-flash", "--provider")
    assert "--oneshot=--provider" in argv
    assert "-z" not in argv


def test_codex_draft_default_is_gpt_5_5() -> None:
    sys.path.insert(0, str(SCRIPTS_DIR))
    from dispatch_smart import TASK_CLASSES

    assert TASK_CLASSES["draft"].models["codex"] == "gpt-5.5"


def test_codex_edit_default_unchanged() -> None:
    sys.path.insert(0, str(SCRIPTS_DIR))
    from dispatch_smart import TASK_CLASSES

    assert TASK_CLASSES["edit"].models["codex"] == "gpt-5.3-codex-spark"


def test_dispatch_smart_codex_forces_danger_mode() -> None:
    """Codex always resolves to danger mode."""
    # Codex auto-forces mode=danger, so non-read-only-like dispatches still
    # require a worktree.
    result = _run_dispatch_smart(["edit", "--agent", "codex", "x"])
    merged_output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode != 0
    assert "danger" in merged_output
    assert "worktree" in merged_output


def test_dispatch_smart_codex_review_no_worktree_required() -> None:
    """Codex review/search remain runtime-necessary in danger mode but do not need a worktree.

    Regression test for #1586: dispatch_smart.py previously forced --worktree for any
    codex dispatch because mode=danger required it; that broke Decision Card C codex-as-reviewer
    pairings. The fix carves out the worktree REQUIREMENT for codex review/search while keeping
    codex in danger mode (codex adapter needs network+FS for tool-calls).
    """
    result = _run_dispatch_smart(["review", "--agent", "codex", "--dry-run", "x"])
    assert result.returncode == 0
    assert "mode=danger" in result.stdout
    assert "worktree=(none — danger)" in result.stdout
    merged_output = (result.stdout or "") + (result.stderr or "")
    assert "requires --worktree" not in merged_output

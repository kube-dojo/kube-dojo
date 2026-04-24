"""Tests for ``scripts.quality.worktree``.

Covers the Codex must-fixes this module closes:

* **#2** — primary checkout stays on ``main`` (worktree isolation)
* **#3** — rebase before ff-only merge survives advancing ``main``
* **#6** — ``try/finally`` cleanup on success AND exception
* **#9** — ``primary_checkout_root`` resolves the venv whether called
  from the primary checkout or from inside a worktree

Pure-path helpers get unit tests (no filesystem). Git-ops helpers get
integration tests with a real git repo in a tmpdir so the fix for #3
is provably exercised, not just mocked.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality import worktree  # noqa: E402


# ---------- pure path helpers ------------------------------------------


def test_primary_checkout_root_primary_returns_unchanged() -> None:
    primary = Path("/home/user/kubedojo")
    assert worktree.primary_checkout_root(primary) == primary


def test_primary_checkout_root_strips_worktree_layout() -> None:
    """From ``<primary>/.worktrees/<name>/`` returns ``<primary>`` — if
    this breaks, the venv path resolves to a non-existent location
    whenever the script is invoked from inside a worktree."""
    wt = Path("/home/user/kubedojo/.worktrees/quality-module-1.2")
    assert worktree.primary_checkout_root(wt) == Path("/home/user/kubedojo")


def test_primary_checkout_root_on_dot_worktrees_literal_still_handled() -> None:
    # Edge: a directory literally named .worktrees with children — the
    # heuristic is name-based, not git-metadata-based. Documents that.
    nested = Path("/tmp/.worktrees/foo")
    assert worktree.primary_checkout_root(nested) == Path("/tmp")


def test_worktree_dir_layout() -> None:
    primary = Path("/repo")
    assert worktree.worktree_dir(primary, "k8s-cka-module-1.1") == Path(
        "/repo/.worktrees/quality-k8s-cka-module-1.1"
    )


def test_branch_name_format() -> None:
    assert worktree.branch_name("k8s-cka-module-1.1") == "quality/k8s-cka-module-1.1"


# ---------- real-git integration ---------------------------------------


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a real git repo with a ``main`` branch, one seed commit, and
    a neutral ``user.*`` config. Returns the repo root.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)
    # Mirror the real repo's .gitignore entry so ``has_uncommitted`` doesn't
    # flag the ``.worktrees/`` directory we'll create as untracked noise.
    (repo / ".gitignore").write_text(".worktrees/\n")
    (repo / "README.md").write_text("seed\n")
    subprocess.run(["git", "add", ".gitignore", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=repo, check=True, capture_output=True)
    return repo


def _commit(repo: Path, filename: str, content: str, message: str) -> str:
    (repo / filename).write_text(content)
    subprocess.run(["git", "add", filename], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    return sha


def _head_sha(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_create_and_remove_worktree(git_repo: Path) -> None:
    slug = "fake-mod"
    wt = worktree.create_worktree(git_repo, slug)
    assert wt.exists()
    assert (wt / "README.md").exists()  # worktree has the main tree
    # Branch exists.
    branch = worktree.branch_name(slug)
    rc = subprocess.run(
        ["git", "rev-parse", "--verify", branch], cwd=git_repo, capture_output=True
    ).returncode
    assert rc == 0

    worktree.remove_worktree(git_repo, slug)
    assert not wt.exists()
    rc = subprocess.run(
        ["git", "rev-parse", "--verify", branch], cwd=git_repo, capture_output=True
    ).returncode
    assert rc != 0  # branch deleted


def test_create_reconciles_orphaned_worktree_dir(git_repo: Path) -> None:
    """SIGKILL scenario: the directory exists on disk but git's worktree
    metadata doesn't know about it. Re-creating must prune + succeed
    rather than erroring with "already exists"."""
    slug = "orphan-test"
    wt_path = worktree.worktree_dir(git_repo, slug)
    wt_path.parent.mkdir(parents=True, exist_ok=True)
    wt_path.mkdir()
    (wt_path / "stale.txt").write_text("leftover")

    wt = worktree.create_worktree(git_repo, slug)
    assert wt == wt_path
    assert wt.exists()
    assert (wt / "README.md").exists()


def test_session_cleans_up_worktree_on_success(git_repo: Path) -> None:
    slug = "session-ok"
    with worktree.worktree_session(git_repo, slug) as wt:
        assert wt.exists()
    assert not wt.exists()


def test_session_cleans_up_worktree_on_exception(git_repo: Path) -> None:
    """Codex must-fix #6 — every branch-mutation path has try/finally."""
    slug = "session-raise"

    class _BoomError(RuntimeError):
        pass

    with pytest.raises(_BoomError):
        with worktree.worktree_session(git_repo, slug) as wt:
            assert wt.exists()
            raise _BoomError("simulated stage failure")

    # Worktree dir cleaned up even though we raised.
    assert not worktree.worktree_dir(git_repo, slug).exists()
    # Branch preserved for post-mortem (intentional).
    branch = worktree.branch_name(slug)
    rc = subprocess.run(
        ["git", "rev-parse", "--verify", branch], cwd=git_repo, capture_output=True
    ).returncode
    assert rc == 0


def test_rebase_and_ff_merge_survives_main_advancing(git_repo: Path) -> None:
    """Codex must-fix #3 — v1 cut branches from the old ``main`` tip and
    used ``--ff-only``. The SECOND module's merge would fail because
    its branch was cut from the old main. This test forces that
    scenario and asserts the rebase-then-ff flow survives it.
    """
    # Module A: create, commit inside the worktree.
    wt_a = worktree.create_worktree(git_repo, "module-a")
    (wt_a / "a.md").write_text("content a\n")
    subprocess.run(["git", "add", "a.md"], cwd=wt_a, check=True)
    subprocess.run(["git", "commit", "-m", "module-a rewrite"], cwd=wt_a, check=True, capture_output=True)

    # Module B: branch cut from the OLD main (module A not merged yet).
    wt_b = worktree.create_worktree(git_repo, "module-b")
    (wt_b / "b.md").write_text("content b\n")
    subprocess.run(["git", "add", "b.md"], cwd=wt_b, check=True)
    subprocess.run(["git", "commit", "-m", "module-b rewrite"], cwd=wt_b, check=True, capture_output=True)

    # Merge A into main. Now main is ahead of B's branch point.
    worktree.rebase_onto_main(git_repo, "module-a")
    sha_a = worktree.merge_ff_only(git_repo, "module-a")
    worktree.remove_worktree(git_repo, "module-a")

    # Without rebase, ff-only of B should fail because main has diverged.
    # The rebase-onto-main call fixes that before we try to merge.
    worktree.rebase_onto_main(git_repo, "module-b")
    sha_b = worktree.merge_ff_only(git_repo, "module-b")
    worktree.remove_worktree(git_repo, "module-b")

    # Both commits present on main, a.md and b.md both visible.
    assert (git_repo / "a.md").read_text() == "content a\n"
    assert (git_repo / "b.md").read_text() == "content b\n"
    assert sha_a != sha_b
    assert _head_sha(git_repo) == sha_b
    # Primary still on ``main`` — Codex must-fix #2.
    assert worktree.current_branch(git_repo) == "main"


def test_rebase_raises_on_conflict(git_repo: Path) -> None:
    """When the branch's changes conflict with main, rebase aborts
    cleanly and raises — caller decides retry vs FAILED."""
    # Both the worktree branch and main edit the same file; rebase will conflict.
    wt = worktree.create_worktree(git_repo, "conflict-test")
    (wt / "shared.md").write_text("branch version\n")
    subprocess.run(["git", "add", "shared.md"], cwd=wt, check=True)
    subprocess.run(["git", "commit", "-m", "branch edit"], cwd=wt, check=True, capture_output=True)

    # Conflicting change on main.
    _commit(git_repo, "shared.md", "main version\n", "main edit")

    with pytest.raises(worktree.WorktreeError, match="rebase"):
        worktree.rebase_onto_main(git_repo, "conflict-test")

    # After the raised abort, the worktree should not be stuck in a
    # rebase-in-progress state — git rebase --abort was called in the
    # failure path.
    status = subprocess.run(
        ["git", "status"], cwd=wt, capture_output=True, text=True, check=True
    ).stdout
    assert "rebase in progress" not in status.lower()

    worktree.remove_worktree(git_repo, "conflict-test")


def test_primary_stays_on_main_across_worktree_lifecycle(git_repo: Path) -> None:
    """Codex must-fix #2 — the primary checkout must never have its HEAD
    mutated by the pipeline. Assert across a full session+rebase+merge."""
    assert worktree.current_branch(git_repo) == "main"
    with worktree.worktree_session(git_repo, "no-mutate") as wt:
        (wt / "x.md").write_text("x\n")
        subprocess.run(["git", "add", "x.md"], cwd=wt, check=True)
        subprocess.run(["git", "commit", "-m", "x"], cwd=wt, check=True, capture_output=True)
        # During the session, the primary checkout is untouched.
        assert worktree.current_branch(git_repo) == "main"
        assert not worktree.has_uncommitted(git_repo)
        worktree.rebase_onto_main(git_repo, "no-mutate")
        worktree.merge_ff_only(git_repo, "no-mutate")
    assert worktree.current_branch(git_repo) == "main"

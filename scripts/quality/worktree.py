"""Git worktree lifecycle for per-module isolation.

Every module the pipeline rewrites runs in its own worktree at
``.worktrees/quality-<slug>/`` on branch ``quality/<slug>``. The primary
checkout never changes branches, never has mutations, stays clean on
``main``. This closes four Codex must-fixes in one mechanism:

* #2 — primary checkout stays on ``main``
* #3 — every branch is freshly rebased onto current ``main`` before
  merge, so fast-forward works after the first merge advances ``main``
* #6 — ``try/finally`` wraps every lifecycle step; SIGKILL leaves an
  orphaned worktree but ``WorktreeSession`` on next run reconciles it
* #9 — :func:`primary_checkout_root` resolves the venv path correctly
  whether the script is invoked from the primary checkout or from
  inside a worktree

Design choice: we use ``git worktree add`` rather than clones because
worktrees share the object database, which keeps disk cheap at 742×
module scale. Trade-off: two worktrees on the same branch is a git
error — we work around it by making each branch name module-unique.
"""

from __future__ import annotations

import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class WorktreeError(RuntimeError):
    """A git worktree or branch operation failed."""


def primary_checkout_root(repo_root: Path) -> Path:
    """Resolve the primary checkout root, even when invoked from a worktree.

    AGENTS.md §1 mandates ``.worktrees/<name>/`` inside the primary
    checkout. When a script in ``scripts/quality/`` runs from a worktree,
    ``Path(__file__).resolve().parents[2]`` returns
    ``<primary>/.worktrees/<name>`` — the ``.venv`` isn't there (worktrees
    share the primary venv), so a naive ``_VENV_PYTHON`` would point at
    a non-existent interpreter.

    Pure path-math, no filesystem access — unit-testable without touching
    disk. Ported verbatim from :mod:`citation_backfill` where PR #374
    introduced it after the bug bit the ``--agent claude`` pilot.
    """
    if repo_root.parent.name == ".worktrees":
        return repo_root.parent.parent
    return repo_root


def _run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Thin ``subprocess.run`` wrapper with sane defaults for git calls."""
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


def worktree_dir(primary: Path, slug: str) -> Path:
    """Canonical worktree path for a given slug."""
    return primary / ".worktrees" / f"quality-{slug}"


def branch_name(slug: str) -> str:
    return f"quality/{slug}"


def _branch_exists(primary: Path, branch: str) -> bool:
    rc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", branch],
        cwd=primary,
        capture_output=True,
    ).returncode
    return rc == 0


def _worktree_registered(primary: Path, path: Path) -> bool:
    """Check if ``path`` is already in ``git worktree list``.

    Handles the SIGKILL-recovery case where the filesystem has a
    ``.worktrees/quality-<slug>/`` directory but the git metadata is
    stale (or vice versa).
    """
    result = _run_git(["worktree", "list", "--porcelain"], primary, check=False)
    if result.returncode != 0:
        return False
    target = str(path.resolve())
    for line in result.stdout.splitlines():
        if line.startswith("worktree ") and line[len("worktree "):] == target:
            return True
    return False


def create_worktree(primary: Path, slug: str, base_ref: str = "main") -> Path:
    """Create a fresh worktree on a new branch off ``base_ref``.

    If a stale worktree from a prior SIGKILL'd run exists, it is pruned
    first. If the branch already exists (commits in flight from the
    prior run), the worktree is re-attached to that branch at its tip —
    do NOT reset it, the resume logic in :mod:`stages` decides whether
    to build on it or to abandon it.
    """
    wt = worktree_dir(primary, slug)
    branch = branch_name(slug)

    # SIGKILL reconciliation: if the directory is on disk but git doesn't
    # know about it (orphaned), we have to remove the directory ourselves
    # — ``git worktree prune`` only prunes git metadata that points at
    # missing directories, not the reverse. ``git worktree remove`` also
    # refuses because git doesn't consider it a worktree. ``rmtree`` is
    # the only mechanism that actually clears the leftover directory.
    if wt.exists() and not _worktree_registered(primary, wt):
        shutil.rmtree(wt, ignore_errors=True)
        _run_git(["worktree", "prune"], primary, check=False)

    if _worktree_registered(primary, wt):
        return wt

    wt.parent.mkdir(parents=True, exist_ok=True)

    if _branch_exists(primary, branch):
        # Resume: attach the worktree to the existing branch. The caller
        # inspects the branch's tip to decide whether to trust the
        # in-flight commits or to discard them.
        result = _run_git(["worktree", "add", str(wt), branch], primary, check=False)
    else:
        result = _run_git(
            ["worktree", "add", "-b", branch, str(wt), base_ref],
            primary,
            check=False,
        )

    if result.returncode != 0:
        raise WorktreeError(
            f"git worktree add failed for {slug}: {result.stderr.strip() or result.stdout.strip()}"
        )
    return wt


def remove_worktree(primary: Path, slug: str, *, delete_branch: bool = True) -> None:
    """Tear down worktree + branch. Safe to call on partial state.

    Used in the ``finally`` path of :func:`worktree_session` and after
    successful merges. ``delete_branch=False`` preserves the branch for
    post-mortem inspection when a run fails.
    """
    wt = worktree_dir(primary, slug)
    branch = branch_name(slug)
    if _worktree_registered(primary, wt) or wt.exists():
        _run_git(["worktree", "remove", "--force", str(wt)], primary, check=False)
    _run_git(["worktree", "prune"], primary, check=False)
    if delete_branch and _branch_exists(primary, branch):
        _run_git(["branch", "-D", branch], primary, check=False)


@contextmanager
def worktree_session(primary: Path, slug: str, base_ref: str = "main") -> Iterator[Path]:
    """Context manager for the create → use → destroy lifecycle.

    Yields the worktree path. Cleans up on every exit path (success,
    exception, SIGKILL will skip the ``finally`` but the next run's
    :func:`create_worktree` reconciles the orphan).

    Intentionally does NOT swallow the worktree's branch on exception —
    leaves it for post-mortem. The wrapping pipeline command is
    responsible for branch cleanup on explicit failure.
    """
    wt = create_worktree(primary, slug, base_ref=base_ref)
    try:
        yield wt
    finally:
        # Branch kept on exception paths for diagnosis; successful exits
        # call ``remove_worktree(delete_branch=True)`` explicitly after
        # merge. Here we only drop the worktree directory.
        try:
            _run_git(["worktree", "remove", "--force", str(wt)], primary, check=False)
            _run_git(["worktree", "prune"], primary, check=False)
        except Exception:  # pragma: no cover — best-effort cleanup
            pass


def rebase_onto_main(primary: Path, slug: str, *, remote_main: str = "main") -> None:
    """Rebase ``quality/<slug>`` onto the tip of ``main`` inside its worktree.

    Must run before ``merge --ff-only`` on ``main``. Without this, the
    second merge of the session would fail because the branch was cut
    from the old ``main`` tip (Codex must-fix #3).

    Uses the worktree as cwd so the rebase doesn't mutate the primary's
    HEAD even if something goes sideways.
    """
    wt = worktree_dir(primary, slug)
    if not wt.exists():
        raise WorktreeError(f"worktree missing for {slug} at {wt}")
    result = _run_git(["rebase", remote_main], wt, check=False)
    if result.returncode != 0:
        # Abort cleanly — leave the branch as-is so the caller can
        # decide whether to retry, mark FAILED, or manual-intervene.
        _run_git(["rebase", "--abort"], wt, check=False)
        raise WorktreeError(
            f"rebase onto {remote_main} failed for {slug}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


def merge_ff_only(primary: Path, slug: str) -> str:
    """Fast-forward-merge ``quality/<slug>`` into ``main`` on the primary.

    Returns the merge-commit SHA (which equals the branch tip in the
    ff-only case). Caller must have already called :func:`rebase_onto_main`.

    Raises :class:`WorktreeError` if ff-only merge is not possible —
    usually means a race: another worker advanced ``main`` between
    rebase and merge. Caller retries (rebase-and-merge loop).
    """
    branch = branch_name(slug)
    result = _run_git(["merge", "--ff-only", branch], primary, check=False)
    if result.returncode != 0:
        raise WorktreeError(
            f"ff-only merge failed for {slug} (main likely advanced): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    sha = _run_git(["rev-parse", "HEAD"], primary).stdout.strip()
    return sha


def current_branch(cwd: Path) -> str:
    return _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd).stdout.strip()


def has_uncommitted(cwd: Path) -> bool:
    result = _run_git(["status", "--porcelain"], cwd)
    return bool(result.stdout.strip())

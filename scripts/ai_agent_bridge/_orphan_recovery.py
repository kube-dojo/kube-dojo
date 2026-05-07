"""Auto-commit stranded Codex work after a workspace-write inbox run."""

from __future__ import annotations

import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ._config import REPO_ROOT

_ALLOWED_ROOTS = ("scripts/", "tests/", "docs/", "plans/")
_PATH_HINT_RE = re.compile(r"(?:[A-Za-z0-9_.-]+/)+(?:[A-Za-z0-9_.-]+)?")


@dataclass(frozen=True)
class RecoveryCandidate:
    delivery_id: str
    thread_id: str
    latest_message_body: str
    thread_bodies: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryResult:
    commit_sha: str | None
    reason: str | None
    changed_files: tuple[str, ...] = ()


def _run(
    repo_root: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _git_head_changed_files(repo_root: Path) -> tuple[str, ...]:
    tracked = _run(repo_root, "diff", "--name-only", "HEAD", "--").stdout.splitlines()
    untracked = _run(
        repo_root, "ls-files", "--others", "--exclude-standard"
    ).stdout.splitlines()
    changed = sorted({path.strip() for path in (*tracked, *untracked) if path.strip()})
    return tuple(changed)


def _extract_path_hints(text: str) -> set[str]:
    hints: set[str] = set()
    for match in _PATH_HINT_RE.finditer(text):
        raw = match.group(0).strip("`()[]{}<>,.:;\"'")
        if "/" not in raw:
            continue
        if raw.endswith("/"):
            hints.add(raw)
            continue
        hints.add(raw)
        parent = raw.rsplit("/", 1)[0]
        if parent:
            hints.add(f"{parent}/")
    return hints


def _matches_thread(path: str, hints: set[str]) -> bool:
    return any(path == hint.rstrip("/") or path.startswith(hint) for hint in hints)


def _short_description(body: str) -> str:
    for line in body.splitlines():
        cleaned = line.strip().lstrip("#*- ").strip()
        if cleaned:
            return cleaned[:72]
    return "workspace-write delivery"


def _build_commit_message(candidate: RecoveryCandidate) -> str:
    short = _short_description(candidate.latest_message_body)
    return (
        f"[TIMEOUT RECOVERY] {short}\n\n"
        f"Recovery of stranded Codex work from delivery {candidate.delivery_id}\n"
        f"in thread {candidate.thread_id}. Original run exceeded hard_timeout=900s\n"
        "but the edits looked complete.\n\n"
        "Co-Authored-By: Codex (timeout recovery)\n"
    )


def _run_ruff(repo_root: Path, py_files: tuple[str, ...]) -> bool:
    if not py_files:
        return True
    ruff_bin = repo_root / ".venv" / "bin" / "ruff"
    if not ruff_bin.exists():
        ruff_bin = REPO_ROOT / ".venv" / "bin" / "ruff"
    result = subprocess.run(
        [str(ruff_bin), "check", *py_files],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _check_lease(
    db_conn: sqlite3.Connection, delivery_id: str
) -> RecoveryResult | None:
    """Return a refused RecoveryResult if the broker lease is still active.

    Callers MUST pass the live DB connection — this check is the only guard
    against racing a broker that is still writing to the workspace.  The rule:
      - delivery row missing → refuse (unknown state, don't guess)
      - lease_until NULL     → safe (broker never claimed a lease)
      - lease_until expired  → safe (broker's window has closed)
      - lease_until in future → refuse (broker may still be writing)
    """
    cursor = db_conn.execute(
        "SELECT lease_until FROM deliveries WHERE delivery_id = ?",
        (delivery_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return RecoveryResult(commit_sha=None, reason="delivery-not-found")
    lease_until_raw: str | None = row[0]
    if lease_until_raw is not None:
        try:
            lease_dt = datetime.fromisoformat(lease_until_raw)
        except ValueError:
            pass
        else:
            if lease_dt > datetime.now(UTC):
                return RecoveryResult(commit_sha=None, reason="broker-lease-active")
    return None


def recover_orphan_commit(
    candidate: RecoveryCandidate,
    *,
    db_conn: sqlite3.Connection,
    repo_root: Path = REPO_ROOT,
) -> RecoveryResult:
    refused = _check_lease(db_conn, candidate.delivery_id)
    if refused is not None:
        return refused

    changed_files = _git_head_changed_files(repo_root)
    if not changed_files:
        return RecoveryResult(commit_sha=None, reason="clean-tree")

    if any(not path.startswith(_ALLOWED_ROOTS) for path in changed_files):
        return RecoveryResult(
            commit_sha=None,
            reason="outside-allowed-scope",
            changed_files=changed_files,
        )

    hints = {
        hint
        for body in candidate.thread_bodies
        for hint in _extract_path_hints(body)
    }
    if not hints or any(not _matches_thread(path, hints) for path in changed_files):
        return RecoveryResult(
            commit_sha=None,
            reason="thread-mismatch",
            changed_files=changed_files,
        )

    py_files = tuple(path for path in changed_files if path.endswith(".py"))
    if not _run_ruff(repo_root, py_files):
        return RecoveryResult(
            commit_sha=None,
            reason="ruff-failed",
            changed_files=changed_files,
        )

    subprocess.run(
        ["git", "-C", str(repo_root), "add", "--", *changed_files],
        check=True,
        capture_output=True,
        text=True,
    )
    commit = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "commit",
            "-m",
            _build_commit_message(candidate),
            "--only",
            "--",
            *changed_files,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0:
        subprocess.run(
            ["git", "-C", str(repo_root), "restore", "--staged", "--", *changed_files],
            check=False,
            capture_output=True,
            text=True,
        )
        return RecoveryResult(
            commit_sha=None,
            reason="pre-commit-failed",
            changed_files=changed_files,
        )

    sha = _run(repo_root, "rev-parse", "HEAD").stdout.strip()
    return RecoveryResult(commit_sha=sha, reason=None, changed_files=changed_files)

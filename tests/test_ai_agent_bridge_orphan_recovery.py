from __future__ import annotations

import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _orphan_recovery

_DELIVERY_ID = "delivery-123"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".venv" / "bin").mkdir(parents=True)
    ruff = repo / ".venv" / "bin" / "ruff"
    ruff.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    ruff.chmod(0o755)
    (repo / "scripts").mkdir()
    (repo / "tests").mkdir()
    (repo / "docs").mkdir()
    (repo / "plans").mkdir()
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md", ".venv/bin/ruff")
    _git(repo, "commit", "-m", "init")
    return repo


def _candidate(*bodies: str) -> _orphan_recovery.RecoveryCandidate:
    return _orphan_recovery.RecoveryCandidate(
        delivery_id=_DELIVERY_ID,
        thread_id="thread-456",
        latest_message_body=bodies[-1],
        thread_bodies=tuple(bodies),
    )


def _make_db(lease_until: str | None, *, delivery_id: str = _DELIVERY_ID) -> sqlite3.Connection:
    """Return an in-memory DB with a single delivery row."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE deliveries (
            delivery_id TEXT PRIMARY KEY,
            message_id  TEXT NOT NULL,
            lease_until TEXT
        )
    """)
    conn.execute(
        "INSERT INTO deliveries (delivery_id, message_id, lease_until) VALUES (?, ?, ?)",
        (delivery_id, "msg-000", lease_until),
    )
    conn.commit()
    return conn


def _expired_lease() -> str:
    return (datetime.now(UTC) - timedelta(hours=1)).isoformat()


def _active_lease() -> str:
    return (datetime.now(UTC) + timedelta(hours=1)).isoformat()


def test_recover_orphan_commit_commits_allowed_matching_file(tmp_path: Path):
    repo = _init_repo(tmp_path)
    target = repo / "scripts" / "ai_agent_bridge"
    target.mkdir()
    changed = target / "_inbox.py"
    changed.write_text("print('ok')\n", encoding="utf-8")

    result = _orphan_recovery.recover_orphan_commit(
        _candidate("Hook into scripts/ai_agent_bridge/_inbox.py"),
        db_conn=_make_db(lease_until=None),
        repo_root=repo,
    )

    assert result.commit_sha
    assert result.changed_files == ("scripts/ai_agent_bridge/_inbox.py",)
    assert _git(repo, "status", "--short").stdout == ""
    message = _git(repo, "log", "-1", "--pretty=%B").stdout
    assert "[TIMEOUT RECOVERY] Hook into scripts/ai_agent_bridge/_inbox.py" in message
    assert "Recovery of stranded Codex work from delivery delivery-123" in message


def test_recover_orphan_commit_commits_with_expired_lease(tmp_path: Path):
    """Expired lease_until is safe — broker's window has closed."""
    repo = _init_repo(tmp_path)
    target = repo / "scripts" / "ai_agent_bridge"
    target.mkdir()
    (target / "_inbox.py").write_text("print('ok')\n", encoding="utf-8")

    result = _orphan_recovery.recover_orphan_commit(
        _candidate("Hook into scripts/ai_agent_bridge/_inbox.py"),
        db_conn=_make_db(lease_until=_expired_lease()),
        repo_root=repo,
    )

    assert result.commit_sha is not None
    assert result.reason is None


def test_recover_orphan_commit_refuses_active_lease(tmp_path: Path):
    """Active lease means broker may still be writing — must not race it."""
    repo = _init_repo(tmp_path)
    (repo / "scripts" / "work.py").write_text("x = 1\n", encoding="utf-8")

    result = _orphan_recovery.recover_orphan_commit(
        _candidate("scripts/work.py"),
        db_conn=_make_db(lease_until=_active_lease()),
        repo_root=repo,
    )

    assert result.commit_sha is None
    assert result.reason == "broker-lease-active"


def test_recover_orphan_commit_refuses_missing_delivery(tmp_path: Path):
    """Delivery row not in DB means unknown state — refuse rather than guess."""
    repo = _init_repo(tmp_path)
    (repo / "scripts" / "work.py").write_text("x = 1\n", encoding="utf-8")

    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE deliveries (
            delivery_id TEXT PRIMARY KEY,
            message_id  TEXT NOT NULL,
            lease_until TEXT
        )
    """)
    conn.commit()

    result = _orphan_recovery.recover_orphan_commit(
        _candidate("scripts/work.py"),
        db_conn=conn,
        repo_root=repo,
    )

    assert result.commit_sha is None
    assert result.reason == "delivery-not-found"

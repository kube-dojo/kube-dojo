from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _orphan_recovery



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
        delivery_id="delivery-123",
        thread_id="thread-456",
        latest_message_body=bodies[-1],
        thread_bodies=tuple(bodies),
    )


def test_recover_orphan_commit_commits_allowed_matching_file(tmp_path: Path):
    repo = _init_repo(tmp_path)
    target = repo / "scripts" / "ai_agent_bridge"
    target.mkdir()
    changed = target / "_inbox.py"
    changed.write_text("print('ok')\n", encoding="utf-8")

    result = _orphan_recovery.recover_orphan_commit(
        _candidate("Hook into scripts/ai_agent_bridge/_inbox.py"),
        repo_root=repo,
    )

    assert result.commit_sha
    assert result.changed_files == ("scripts/ai_agent_bridge/_inbox.py",)
    assert _git(repo, "status", "--short").stdout == ""
    message = _git(repo, "log", "-1", "--pretty=%B").stdout
    assert "[TIMEOUT RECOVERY] Hook into scripts/ai_agent_bridge/_inbox.py" in message
    assert "Recovery of stranded Codex work from delivery delivery-123" in message

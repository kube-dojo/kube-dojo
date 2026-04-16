from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "issue_watch.py"
    spec = importlib.util.spec_from_file_location("issue_watch", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


issue_watch = _load_module()


def test_poll_issue_initializes_state_and_log(tmp_path: Path) -> None:
    payload = {
        "number": 248,
        "title": "Review batch",
        "url": "https://example.test/issues/248",
        "state": "OPEN",
        "updatedAt": "2026-04-16T08:00:00Z",
        "comments": [
            {
                "url": "https://example.test/issues/248#issuecomment-1",
                "createdAt": "2026-04-16T08:00:00Z",
                "author": {"login": "user1"},
                "body": "First feedback",
            }
        ],
    }

    with patch.object(issue_watch, "fetch_issue", return_value=payload):
        result = issue_watch.poll_issue(248, repo_root=tmp_path)

    assert result["new_comments"] == 1
    assert Path(result["state_path"]).exists()
    assert Path(result["log_path"]).exists()
    assert "First feedback" in Path(result["log_path"]).read_text(encoding="utf-8")


def test_poll_issue_only_logs_new_comments(tmp_path: Path) -> None:
    initial = {
        "number": 248,
        "title": "Review batch",
        "url": "https://example.test/issues/248",
        "state": "OPEN",
        "updatedAt": "2026-04-16T08:00:00Z",
        "comments": [
            {
                "url": "https://example.test/issues/248#issuecomment-1",
                "createdAt": "2026-04-16T08:00:00Z",
                "author": {"login": "user1"},
                "body": "First feedback",
            }
        ],
    }
    current = {
        **initial,
        "updatedAt": "2026-04-16T08:30:00Z",
        "comments": [
            initial["comments"][0],
            {
                "url": "https://example.test/issues/248#issuecomment-2",
                "createdAt": "2026-04-16T08:30:00Z",
                "author": {"login": "user2"},
                "body": "Second feedback",
            },
        ],
    }
    state_path = tmp_path / ".pipeline" / "issue-watch" / "248.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(initial, indent=2), encoding="utf-8")

    with patch.object(issue_watch, "fetch_issue", return_value=current):
        result = issue_watch.poll_issue(248, repo_root=tmp_path)

    assert result["new_comments"] == 1
    log_text = (tmp_path / ".pipeline" / "issue-watch" / "248.log").read_text(encoding="utf-8")
    assert "Second feedback" in log_text
    assert "First feedback" not in log_text

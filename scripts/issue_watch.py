#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / ".pipeline" / "issue-watch"


def fetch_issue(issue_number: int, *, repo_root: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--json",
            "number,title,url,state,updatedAt,comments",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise ValueError("unexpected GitHub issue payload")
    return payload


def _state_path(issue_number: int, *, repo_root: Path) -> Path:
    return repo_root / ".pipeline" / "issue-watch" / f"{issue_number}.json"


def _log_path(issue_number: int, *, repo_root: Path) -> Path:
    return repo_root / ".pipeline" / "issue-watch" / f"{issue_number}.log"


def _read_previous(issue_number: int, *, repo_root: Path) -> dict[str, Any] | None:
    path = _state_path(issue_number, repo_root=repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _comment_key(comment: dict[str, Any]) -> str:
    url = str(comment.get("url", "")).strip()
    created = str(comment.get("createdAt", "")).strip()
    author = comment.get("author") or {}
    login = str(author.get("login", "")).strip() if isinstance(author, dict) else ""
    return "|".join((url, created, login))


def _extract_new_comments(previous: dict[str, Any] | None, current: dict[str, Any]) -> list[dict[str, Any]]:
    previous_comments = previous.get("comments", []) if isinstance(previous, dict) else []
    seen = {_comment_key(item) for item in previous_comments if isinstance(item, dict)}
    current_comments = current.get("comments", [])
    fresh: list[dict[str, Any]] = []
    if not isinstance(current_comments, list):
        return fresh
    for item in current_comments:
        if not isinstance(item, dict):
            continue
        key = _comment_key(item)
        if key not in seen:
            fresh.append(item)
    return fresh


def _append_log(issue_number: int, comments: list[dict[str, Any]], *, repo_root: Path) -> None:
    if not comments:
        return
    path = _log_path(issue_number, repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for comment in comments:
            author = comment.get("author") or {}
            login = str(author.get("login", "unknown")).strip() if isinstance(author, dict) else "unknown"
            created = str(comment.get("createdAt", "")).strip()
            url = str(comment.get("url", "")).strip()
            body = str(comment.get("body", "")).strip()
            handle.write(f"## {created} — {login}\n")
            handle.write(f"{url}\n\n")
            handle.write(body)
            handle.write("\n\n---\n")


def poll_issue(issue_number: int, *, repo_root: Path) -> dict[str, Any]:
    previous = _read_previous(issue_number, repo_root=repo_root)
    current = fetch_issue(issue_number, repo_root=repo_root)
    new_comments = _extract_new_comments(previous, current)

    state_path = _state_path(issue_number, repo_root=repo_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
    _append_log(issue_number, new_comments, repo_root=repo_root)

    return {
        "issue_number": issue_number,
        "title": current.get("title", ""),
        "url": current.get("url", ""),
        "updated_at": current.get("updatedAt", ""),
        "total_comments": len(current.get("comments", [])) if isinstance(current.get("comments"), list) else 0,
        "new_comments": len(new_comments),
        "new_comment_urls": [str(item.get("url", "")).strip() for item in new_comments],
        "state_path": str(state_path),
        "log_path": str(_log_path(issue_number, repo_root=repo_root)),
    }


def loop_issue(issue_number: int, *, repo_root: Path, interval_seconds: int) -> None:
    while True:
        result = poll_issue(issue_number, repo_root=repo_root)
        print(json.dumps(result, sort_keys=True), flush=True)
        time.sleep(interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Watch GitHub issue comments into local state files")
    parser.add_argument("command", choices=("run", "loop"))
    parser.add_argument("issue_number", type=int)
    parser.add_argument("--interval-seconds", type=int, default=1800)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    if args.command == "run":
        print(json.dumps(poll_issue(args.issue_number, repo_root=repo_root), indent=2, sort_keys=True))
        return 0

    loop_issue(args.issue_number, repo_root=repo_root, interval_seconds=args.interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

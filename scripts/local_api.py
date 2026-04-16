#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline_v2.cli import _build_status_report as build_v2_status_report
from status import (
    _build_lab_summary,
    _extract_frontmatter,
    _git_head_for_file,
    build_repo_status,
)
from translation_v2 import build_status as build_translation_status
from translation_v2 import detect_module_state
from ztt_status import build_status as build_ztt_status


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8767
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
GENERATED_PREFIXES = (
    ".astro/",
    ".dispatch-logs/",
    ".review-results/",
    "dist/",
    "logs/",
    "site/",
)
PIPELINE_PREFIXES = (
    ".bridge/",
    ".pipeline/",
    ".pids/",
)


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _load_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _classify_path(path: str) -> str:
    if path.startswith(GENERATED_PREFIXES):
        return "generated"
    if path.startswith(PIPELINE_PREFIXES):
        return "pipeline"
    if path.startswith("src/") or path.startswith("scripts/") or path.startswith("tests/") or path.startswith("docs/"):
        return "source"
    return "other"


def build_worktree_status(repo_root: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--branch"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "repo_root": str(repo_root),
            "ok": False,
            "error": result.stderr.strip() or "git status failed",
        }

    lines = result.stdout.splitlines()
    branch = ""
    ahead = 0
    behind = 0
    if lines and lines[0].startswith("## "):
        branch_line = lines[0][3:]
        branch = branch_line
        if "..." in branch_line:
            branch = branch_line.split("...", 1)[0]
        if "[ahead " in branch_line:
            ahead = int(branch_line.split("[ahead ", 1)[1].split("]", 1)[0].split(",")[0])
        if "[behind " in branch_line:
            behind = int(branch_line.split("[behind ", 1)[1].split("]", 1)[0].split(",")[0])

    entries: list[dict[str, Any]] = []
    counts = {
        "total": 0,
        "staged": 0,
        "unstaged": 0,
        "untracked": 0,
        "conflicted": 0,
    }
    categories = {"source": 0, "generated": 0, "pipeline": 0, "other": 0}

    for line in lines[1:]:
        if not line.strip():
            continue
        if line.startswith("?? "):
            path = line[3:]
            staged = False
            unstaged = False
            untracked = True
            conflicted = False
            index_status = "?"
            worktree_status = "?"
        else:
            index_status = line[0]
            worktree_status = line[1]
            path = line[3:]
            staged = index_status not in {" ", "?"}
            unstaged = worktree_status not in {" ", "?"}
            untracked = False
            conflicted = index_status == "U" or worktree_status == "U"
        category = _classify_path(path)
        counts["total"] += 1
        counts["staged"] += int(staged)
        counts["unstaged"] += int(unstaged)
        counts["untracked"] += int(untracked)
        counts["conflicted"] += int(conflicted)
        categories[category] += 1
        entries.append(
            {
                "path": path,
                "index_status": index_status,
                "worktree_status": worktree_status,
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "conflicted": conflicted,
                "category": category,
            }
        )

    return {
        "repo_root": str(repo_root),
        "ok": True,
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "dirty": counts["total"] > 0,
        "counts": counts,
        "categories": categories,
        "entries": entries,
    }


def _db_latest_for_module(db_path: Path, module_key: str) -> dict[str, Any] | None:
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        job = conn.execute(
            """
            SELECT *
            FROM jobs
            WHERE module_key = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (module_key,),
        ).fetchone()
        event = conn.execute(
            """
            SELECT *
            FROM events
            WHERE module_key = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (module_key,),
        ).fetchone()
    finally:
        conn.close()

    return {
        "db_path": str(db_path),
        "latest_job": dict(job) if job is not None else None,
        "latest_event": (
            {**dict(event), "payload_json": _load_json(str(event["payload_json"]))}
            if event is not None
            else None
        ),
    }


def build_module_state(repo_root: Path, module_key: str) -> dict[str, Any]:
    normalized = module_key[:-3] if module_key.endswith(".md") else module_key
    en_path = repo_root / "src" / "content" / "docs" / f"{normalized}.md"
    uk_path = repo_root / "src" / "content" / "docs" / "uk" / f"{normalized}.md"
    frontmatter = _extract_frontmatter(en_path) if en_path.exists() else {}
    lab = frontmatter.get("lab")
    lab_id = None
    if isinstance(lab, str) and lab.strip():
        lab_id = lab.strip()
    elif isinstance(lab, dict):
        for key in ("id", "name", "slug"):
            value = lab.get(key)
            if isinstance(value, str) and value.strip():
                lab_id = value.strip()
                break

    fact_ledger = repo_root / ".pipeline" / "fact-ledgers" / f"{normalized.replace('/', '__')}.json"
    lab_summary = _build_lab_summary(repo_root)
    lab_state = next((item for item in lab_summary["items"] if item["lab_id"] == lab_id), None) if lab_id else None

    return {
        "module_key": normalized,
        "track": normalized.split("/", 1)[0] if "/" in normalized else normalized,
        "english_path": str(en_path),
        "english_exists": en_path.exists(),
        "english_commit": _git_head_for_file(repo_root, en_path) if en_path.exists() else "",
        "ukrainian_path": str(uk_path),
        "ukrainian_exists": uk_path.exists(),
        "ukrainian_state": detect_module_state(repo_root, normalized) if en_path.exists() else None,
        "frontmatter": frontmatter,
        "fact_ledger": {
            "path": str(fact_ledger),
            "exists": fact_ledger.exists(),
        },
        "lab": {
            "lab_id": lab_id,
            "state": lab_state,
        },
    }


def build_module_orchestration_latest(repo_root: Path, module_key: str) -> dict[str, Any]:
    normalized = module_key[:-3] if module_key.endswith(".md") else module_key
    return {
        "module_key": normalized,
        "v2": _db_latest_for_module(repo_root / ".pipeline" / "v2.db", normalized),
        "translation_v2": _db_latest_for_module(repo_root / ".pipeline" / "translation_v2.db", normalized),
    }


def route_request(repo_root: Path, raw_path: str) -> tuple[int, dict[str, Any]]:
    parsed = urlsplit(raw_path)
    path = parsed.path.rstrip("/") or "/"
    query = parse_qs(parsed.query)

    if path == "/healthz":
        return 200, {"ok": True}
    if path == "/api/status/summary":
        return 200, build_repo_status(repo_root)
    if path == "/api/pipeline/v2/status":
        db_path = repo_root / ".pipeline" / "v2.db"
        if not db_path.exists():
            return 404, {"error": "missing_db", "db_path": str(db_path)}
        return 200, build_v2_status_report(db_path)
    if path == "/api/translation/v2/status":
        section = query.get("section", [None])[0]
        return 200, build_translation_status(
            repo_root,
            db_path=repo_root / ".pipeline" / "translation_v2.db",
            section=section,
        )
    if path == "/api/labs/status":
        return 200, _build_lab_summary(repo_root)
    if path == "/api/ztt/status":
        return 200, build_ztt_status(repo_root)
    if path == "/api/git/worktree":
        return 200, build_worktree_status(repo_root)
    if path.startswith("/api/module/") and path.endswith("/state"):
        module_key = unquote(path[len("/api/module/") : -len("/state")]).strip("/")
        if not module_key:
            return 400, {"error": "missing_module_key"}
        return 200, build_module_state(repo_root, module_key)
    if path.startswith("/api/module/") and path.endswith("/orchestration/latest"):
        module_key = unquote(path[len("/api/module/") : -len("/orchestration/latest")]).strip("/")
        if not module_key:
            return 400, {"error": "missing_module_key"}
        return 200, build_module_orchestration_latest(repo_root, module_key)
    return 404, {"error": "not_found", "path": path}


def make_handler(repo_root: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            status_code, payload = route_request(repo_root, self.path)
            body = json.dumps(payload, indent=2, sort_keys=True, default=_json_default).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve(repo_root: Path, host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(repo_root))
    print(json.dumps({"repo_root": str(repo_root), "host": host, "port": port}, sort_keys=True))
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic local API for KubeDojo state")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    serve(args.repo_root.resolve(), args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

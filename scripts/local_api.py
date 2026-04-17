#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline_v2.cli import _build_status_report as build_v2_status_report
from status import (
    _build_lab_summary,
    _build_missing_modules_summary,
    _enrich_translation_v2_with_per_track,
    _enrich_v2_with_per_track,
    _extract_frontmatter,
    _git_head_for_file,
    build_repo_status,
)
from translation_v2 import build_status as build_translation_status
from translation_v2 import detect_module_state
from ztt_status import build_status as build_ztt_status


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8768
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
DEFAULT_FEEDBACK_ISSUE = 248
RUNTIME_SERVICES = (
    {"name": "dev", "pid_file": ".pids/dev.pid", "port": 4333, "label": "Astro Dev Server"},
    {"name": "api", "pid_file": ".pids/api.pid", "port": 8768, "label": "Deterministic Local API"},
    {"name": "feedback", "pid_file": ".pids/feedback.pid", "port": None, "label": "GitHub Issue Watcher"},
    {"name": "pipeline", "pid_file": ".pids/pipeline.pid", "port": None, "label": "Pipeline Supervisor"},
    {"name": "v2-write-worker", "pid_file": ".pids/v2-write-worker.pid", "port": None, "label": "V2 Write Worker"},
    {"name": "v2-review-worker", "pid_file": ".pids/v2-review-worker.pid", "port": None, "label": "V2 Review Worker"},
    {"name": "v2-patch-worker", "pid_file": ".pids/v2-patch-worker.pid", "port": None, "label": "V2 Patch Worker"},
)
RUNTIME_SERVICE_ORDER = tuple(svc["name"] for svc in RUNTIME_SERVICES)


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


def build_issue_watch_state(repo_root: Path, issue_number: int) -> dict[str, Any] | None:
    path = repo_root / ".pipeline" / "issue-watch" / f"{issue_number}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "issue_number": issue_number,
            "error": "invalid_state_json",
            "path": str(path),
        }
    if not isinstance(payload, dict):
        return {
            "issue_number": issue_number,
            "error": "invalid_state_shape",
            "path": str(path),
        }
    comments = payload.get("comments", [])
    last_comment = comments[-1] if isinstance(comments, list) and comments else None
    return {
        "issue_number": issue_number,
        "path": str(path),
        "title": payload.get("title", ""),
        "url": payload.get("url", ""),
        "state": payload.get("state", ""),
        "updated_at": payload.get("updatedAt", ""),
        "comments_count": len(comments) if isinstance(comments, list) else 0,
        "last_comment": last_comment,
    }


def _inspect_pid_file(pid_path: Path) -> dict[str, Any]:
    """Read a pid file and probe the process. Returns pid, status, uptime, stale flag."""
    pid: int | None = None
    status = "stopped"
    uptime_seconds: float | None = None
    stale_pid_file = False
    pid_file_mtime: float | None = None

    if not pid_path.exists():
        return {
            "pid": None,
            "status": "stopped",
            "uptime_seconds": None,
            "stale_pid_file": False,
            "pid_file_mtime": None,
        }

    try:
        stat_result = pid_path.stat()
        pid_file_mtime = stat_result.st_mtime
    except OSError:
        pid_file_mtime = None

    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pid = None

    if pid is not None:
        try:
            os.kill(pid, 0)  # Signal 0 probes existence without delivering a signal.
            status = "running"
            if pid_file_mtime is not None:
                uptime_seconds = max(0.0, time.time() - pid_file_mtime)
        except OSError:
            status = "stale"
            stale_pid_file = True
    else:
        status = "stale"
        stale_pid_file = True

    return {
        "pid": pid,
        "status": status,
        "uptime_seconds": uptime_seconds,
        "stale_pid_file": stale_pid_file,
        "pid_file_mtime": pid_file_mtime,
    }


def _humanize_service_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def build_runtime_services_status(repo_root: Path) -> dict[str, Any]:
    services: list[dict[str, Any]] = []
    running = 0
    stopped = 0
    stale = 0

    seen_names: set[str] = set()
    for svc in RUNTIME_SERVICES:
        pid_path = repo_root / svc["pid_file"]
        probe = _inspect_pid_file(pid_path)
        seen_names.add(svc["name"])
        if probe["status"] == "running":
            running += 1
        elif probe["status"] == "stale":
            stale += 1
        else:
            stopped += 1
        services.append(
            {
                "name": svc["name"],
                "label": svc["label"],
                "status": probe["status"],
                "pid": probe["pid"],
                "port": svc["port"],
                "pid_file": str(pid_path),
                "uptime_seconds": probe["uptime_seconds"],
                "stale_pid_file": probe["stale_pid_file"],
                "known": True,
            }
        )

    # Auto-discover pid files not covered by the curated list so operators can
    # see workers spawned by scripts that haven't been registered yet.
    pids_dir = repo_root / ".pids"
    if pids_dir.is_dir():
        for pid_path in sorted(pids_dir.glob("*.pid")):
            name = pid_path.stem
            if name in seen_names:
                continue
            probe = _inspect_pid_file(pid_path)
            if probe["status"] == "running":
                running += 1
            elif probe["status"] == "stale":
                stale += 1
            else:
                stopped += 1
            services.append(
                {
                    "name": name,
                    "label": _humanize_service_name(name),
                    "status": probe["status"],
                    "pid": probe["pid"],
                    "port": None,
                    "pid_file": str(pid_path),
                    "uptime_seconds": probe["uptime_seconds"],
                    "stale_pid_file": probe["stale_pid_file"],
                    "known": False,
                }
            )

    return {
        "running": running,
        "stopped": stopped,
        "stale": stale,
        "total": running + stopped + stale,
        "services": services,
    }


def render_dashboard_html(*, issue_number: int = DEFAULT_FEEDBACK_ISSUE) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KubeDojo Local Monitor</title>
  <style>
    :root {{
      --bg: #0a0f1a;
      --surface-0: #111827;
      --surface-1: #1a2332;
      --surface-2: #1f2b3d;
      --text: #e5e7eb;
      --text-secondary: #9ca3af;
      --text-dim: #6b7280;
      --accent: #38bdf8;
      --accent-muted: rgba(56,189,248,0.12);
      --teal: #2dd4bf;
      --teal-muted: rgba(45,212,191,0.12);
      --green: #4ade80;
      --green-muted: rgba(74,222,128,0.12);
      --amber: #fbbf24;
      --amber-muted: rgba(251,191,36,0.10);
      --red: #f87171;
      --red-muted: rgba(248,113,113,0.10);
      --border: rgba(255,255,255,0.06);
      --border-subtle: rgba(255,255,255,0.03);
      --radius: 12px;
      --radius-sm: 8px;
      --radius-xs: 6px;
    }}
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      -webkit-font-smoothing: antialiased;
      line-height: 1.5;
    }}
    .mono {{ font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace; }}

    .header {{
      background: linear-gradient(180deg, rgba(17,24,39,0.95) 0%, rgba(10,15,26,0.98) 100%);
      border-bottom: 1px solid var(--border);
      padding: 20px 0;
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(12px);
    }}
    .header-inner {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .header-left {{ display: flex; align-items: center; gap: 14px; }}
    .logo {{
      width: 32px; height: 32px; border-radius: 8px;
      background: linear-gradient(135deg, var(--accent), var(--teal));
      display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 14px; color: #0a0f1a; flex-shrink: 0;
    }}
    .header-title {{ font-size: 16px; font-weight: 600; letter-spacing: -0.01em; }}
    .header-sub {{ font-size: 12px; color: var(--text-dim); }}
    .header-right {{ display: flex; align-items: center; gap: 12px; }}
    .status-pill {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 5px 12px; border-radius: 20px;
      font-size: 12px; font-weight: 500;
      background: var(--green-muted); color: var(--green);
    }}
    .status-pill .dot {{
      width: 6px; height: 6px; border-radius: 50%;
      background: currentColor; animation: pulse 2s ease-in-out infinite;
    }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
    .refresh-btn {{
      background: var(--surface-1); color: var(--text);
      border: 1px solid var(--border); padding: 6px 14px;
      border-radius: var(--radius-sm); font-size: 13px;
      font-weight: 500; cursor: pointer; transition: all 0.15s;
      display: flex; align-items: center; gap: 6px;
    }}
    .refresh-btn:hover {{ background: var(--surface-2); border-color: rgba(255,255,255,0.12); }}
    .refresh-btn.loading {{ opacity: 0.6; pointer-events: none; }}
    .refresh-btn svg {{ transition: transform 0.3s; }}
    .refresh-btn.loading svg {{ animation: spin 0.8s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .last-updated {{ font-size: 11px; color: var(--text-dim); }}

    .main {{ max-width: 1440px; margin: 0 auto; padding: 24px; }}

    .metrics {{
      display: grid; grid-template-columns: repeat(6, 1fr);
      gap: 12px; margin-bottom: 24px;
    }}
    .metric {{
      background: var(--surface-0); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 16px;
      position: relative; overflow: hidden;
    }}
    .metric::before {{
      content: ''; position: absolute; top: 0; left: 0; right: 0;
      height: 2px; background: var(--border);
    }}
    .metric.good::before {{ background: var(--green); }}
    .metric.warn::before {{ background: var(--amber); }}
    .metric.bad::before {{ background: var(--red); }}
    .metric.accent::before {{ background: var(--accent); }}
    .metric-label {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--text-dim); margin-bottom: 8px;
    }}
    .metric-value {{ font-size: 26px; font-weight: 700; letter-spacing: -0.02em; line-height: 1; }}
    .metric-sub {{ font-size: 11px; color: var(--text-dim); margin-top: 6px; }}

    .progress-track {{
      height: 4px; background: rgba(255,255,255,0.06);
      border-radius: 2px; margin-top: 10px; overflow: hidden;
    }}
    .progress-fill {{ height: 100%; border-radius: 2px; transition: width 0.6s ease; }}
    .progress-fill.green {{ background: var(--green); }}
    .progress-fill.amber {{ background: var(--amber); }}
    .progress-fill.accent {{ background: var(--accent); }}

    .sections {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .section-full {{ grid-column: 1 / -1; }}

    .panel {{
      background: var(--surface-0); border: 1px solid var(--border);
      border-radius: var(--radius); overflow: hidden;
    }}
    .panel-header {{
      padding: 14px 18px; border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between;
    }}
    .panel-title {{
      font-size: 13px; font-weight: 600;
      display: flex; align-items: center; gap: 8px;
    }}
    .panel-icon {{
      width: 18px; height: 18px; border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      font-size: 11px; flex-shrink: 0;
    }}
    .panel-badge {{
      font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600;
    }}
    .panel-body {{ padding: 16px 18px; }}
    .panel-body-flush {{ padding: 0; }}

    .svc-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; }}
    .svc-item {{
      padding: 14px 18px; border-right: 1px solid var(--border);
      display: flex; align-items: center; gap: 12px;
    }}
    .svc-item:last-child {{ border-right: 0; }}
    .svc-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
    .svc-dot.running {{ background: var(--green); box-shadow: 0 0 8px rgba(74,222,128,0.4); }}
    .svc-dot.stopped {{ background: var(--text-dim); }}
    .svc-dot.stale {{ background: var(--red); box-shadow: 0 0 8px rgba(248,113,113,0.45); }}
    .svc-info {{ min-width: 0; flex: 1; }}
    .svc-name {{ font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px; }}
    .svc-detail {{ font-size: 11px; color: var(--text-dim); }}
    .svc-chip {{
      display: inline-block; padding: 1px 6px; border-radius: 4px;
      font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
    }}
    .svc-chip.stale {{ background: var(--red-muted); color: var(--red); }}
    .svc-chip.discovered {{ background: var(--accent-muted); color: var(--accent); }}

    .queue-cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
    .queue-col {{ border-right: 1px solid var(--border); }}
    .queue-col:last-child {{ border-right: 0; }}
    .queue-col-header {{
      padding: 10px 14px; border-bottom: 1px solid var(--border-subtle);
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim);
      display: flex; align-items: center; justify-content: space-between;
    }}
    .queue-count {{
      font-size: 10px; padding: 1px 6px; border-radius: 8px;
      background: rgba(255,255,255,0.06); color: var(--text-secondary);
    }}
    .queue-list {{ margin: 0; padding: 0; list-style: none; max-height: 180px; overflow-y: auto; }}
    .queue-list::-webkit-scrollbar {{ width: 4px; }}
    .queue-list::-webkit-scrollbar-track {{ background: transparent; }}
    .queue-list::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.08); border-radius: 2px; }}
    .queue-item {{
      padding: 6px 14px; font-size: 12px; border-bottom: 1px solid var(--border-subtle);
      color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .queue-item:last-child {{ border-bottom: 0; }}
    .queue-empty {{ padding: 20px 14px; text-align: center; font-size: 12px; color: var(--text-dim); }}

    .wt-summary {{
      display: flex; gap: 16px; padding: 12px 18px;
      border-bottom: 1px solid var(--border); flex-wrap: wrap;
    }}
    .wt-stat {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); }}
    .wt-stat-val {{ font-weight: 600; color: var(--text); }}
    .wt-table {{ width: 100%; border-collapse: collapse; }}
    .wt-table th {{
      text-align: left; padding: 8px 14px; font-size: 11px;
      font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
      color: var(--text-dim); border-bottom: 1px solid var(--border);
      background: rgba(0,0,0,0.15);
    }}
    .wt-table td {{ padding: 5px 14px; font-size: 12px; border-bottom: 1px solid var(--border-subtle); }}
    .wt-table tr:last-child td {{ border-bottom: 0; }}
    .wt-path {{ color: var(--text-secondary); }}
    .wt-badge {{
      display: inline-block; padding: 1px 6px; border-radius: 4px;
      font-size: 10px; font-weight: 600; text-transform: uppercase;
    }}
    .wt-badge.M {{ background: var(--amber-muted); color: var(--amber); }}
    .wt-badge.A {{ background: var(--green-muted); color: var(--green); }}
    .wt-badge.D {{ background: var(--red-muted); color: var(--red); }}
    .wt-badge.U {{ background: var(--red-muted); color: var(--red); }}
    .wt-badge.Q {{ background: var(--accent-muted); color: var(--accent); }}
    .wt-cat {{
      font-size: 10px; padding: 1px 6px; border-radius: 4px;
      background: rgba(255,255,255,0.04); color: var(--text-dim);
    }}
    .wt-scroll {{ max-height: 260px; overflow-y: auto; }}
    .wt-scroll::-webkit-scrollbar {{ width: 4px; }}
    .wt-scroll::-webkit-scrollbar-track {{ background: transparent; }}
    .wt-scroll::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.08); border-radius: 2px; }}

    .tracks-table {{ width: 100%; border-collapse: collapse; }}
    .tracks-table th {{
      text-align: left; padding: 10px 18px; font-size: 11px;
      font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
      color: var(--text-dim); border-bottom: 1px solid var(--border);
      background: rgba(0,0,0,0.15);
    }}
    .tracks-table th.num {{ text-align: right; }}
    .tracks-table td {{
      padding: 10px 18px; font-size: 13px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .tracks-table tr:last-child td {{ border-bottom: 0; }}
    .tracks-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
    .tracks-table td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .tracks-table td.name {{ font-weight: 600; }}
    .tracks-table .dim {{ color: var(--text-dim); }}
    .tracks-table .warn {{ color: var(--amber); font-weight: 600; }}
    .tracks-table .bad {{ color: var(--red); font-weight: 600; }}
    .tracks-table .good {{ color: var(--green); }}
    .tracks-table .zero {{ color: var(--text-dim); }}

    .queue-summary {{
      padding: 14px 18px; border-bottom: 1px solid var(--border);
      display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
      gap: 0; text-align: center;
    }}
    .queue-stat {{ border-right: 1px solid var(--border-subtle); padding: 2px 8px; }}
    .queue-stat:last-child {{ border-right: 0; }}
    .queue-stat-val {{ font-size: 20px; font-weight: 700; letter-spacing: -0.01em; line-height: 1; }}
    .queue-stat-label {{
      font-size: 10px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-top: 6px;
    }}
    .queue-per-track {{ padding: 0; }}
    .qpt-row {{
      display: grid; grid-template-columns: 1fr auto;
      padding: 8px 18px; border-bottom: 1px solid var(--border-subtle);
      font-size: 12px; align-items: center; gap: 12px;
    }}
    .qpt-row:last-child {{ border-bottom: 0; }}
    .qpt-name {{ color: var(--text-secondary); }}
    .qpt-status {{ font-size: 11px; color: var(--text-dim); text-align: right; }}
    .qpt-status .pill {{
      display: inline-block; padding: 1px 7px; border-radius: 10px;
      font-size: 10px; font-weight: 600; margin-left: 4px;
    }}
    .qpt-status .pill.w {{ background: var(--accent-muted); color: var(--accent); }}
    .qpt-status .pill.r {{ background: var(--amber-muted); color: var(--amber); }}
    .qpt-status .pill.p {{ background: var(--teal-muted); color: var(--teal); }}
    .qpt-status .pill.d {{ background: var(--red-muted); color: var(--red); }}
    .qpt-status.idle {{ color: var(--green); }}
    .qpt-top {{
      padding: 12px 18px; border-top: 1px solid var(--border);
      background: rgba(0,0,0,0.12);
    }}
    .qpt-top-title {{
      font-size: 10px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-bottom: 8px;
    }}
    .qpt-top-list {{ margin: 0; padding: 0; list-style: none; }}
    .qpt-top-list li {{
      padding: 3px 0; font-size: 12px; color: var(--text-secondary);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .qpt-top-kind {{
      display: inline-block; width: 14px; font-weight: 700;
      font-size: 10px; text-transform: uppercase;
    }}
    .qpt-top-kind.w {{ color: var(--accent); }}
    .qpt-top-kind.r {{ color: var(--amber); }}
    .qpt-top-kind.p {{ color: var(--teal); }}
    .qpt-top-kind.d {{ color: var(--red); }}

    .ztt-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
    .ztt-section {{ padding: 14px 18px; border-right: 1px solid var(--border); }}
    .ztt-section:last-child {{ border-right: 0; }}
    .ztt-section-title {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-bottom: 10px;
    }}
    .ztt-row {{ display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; }}
    .ztt-check {{
      width: 16px; height: 16px; border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      font-size: 10px; flex-shrink: 0;
    }}
    .ztt-check.pass {{ background: var(--green-muted); color: var(--green); }}
    .ztt-check.fail {{ background: var(--red-muted); color: var(--red); }}
    .ztt-label {{ color: var(--text-secondary); }}
    .ztt-val {{ margin-left: auto; font-weight: 600; font-size: 11px; }}

    .missing-group {{ margin-bottom: 12px; }}
    .missing-group:last-child {{ margin-bottom: 0; }}
    .missing-group-title {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-bottom: 8px;
      display: flex; align-items: center; gap: 8px;
    }}
    .missing-list {{ margin: 0; padding: 0; list-style: none; }}
    .missing-item {{
      padding: 5px 10px; font-size: 12px; color: var(--text-secondary);
      border-radius: var(--radius-xs); margin-bottom: 2px;
    }}
    .missing-item:hover {{ background: rgba(255,255,255,0.03); }}

    .fb-header {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px; }}
    .fb-icon {{
      width: 32px; height: 32px; border-radius: 50%;
      background: var(--accent-muted); color: var(--accent);
      display: flex; align-items: center; justify-content: center;
      font-size: 14px; flex-shrink: 0;
    }}
    .fb-title {{ font-size: 14px; font-weight: 600; }}
    .fb-meta {{
      font-size: 12px; color: var(--text-dim);
      display: flex; gap: 12px; margin-top: 2px; flex-wrap: wrap;
    }}
    .fb-meta span {{ display: flex; align-items: center; gap: 4px; }}
    .fb-comment {{
      background: var(--surface-1); border: 1px solid var(--border);
      border-radius: var(--radius-sm); padding: 12px; margin-top: 12px;
    }}
    .fb-comment-header {{ font-size: 11px; color: var(--text-dim); margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }}
    .fb-comment-body {{
      font-size: 12px; color: var(--text-secondary); line-height: 1.5;
      max-height: 120px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;
    }}

    .clr-green {{ color: var(--green); }}
    .clr-amber {{ color: var(--amber); }}
    .clr-red {{ color: var(--red); }}
    .clr-accent {{ color: var(--accent); }}
    .empty-state {{ padding: 24px; text-align: center; color: var(--text-dim); font-size: 13px; }}
    .skeleton {{
      background: linear-gradient(90deg, var(--surface-1) 25%, var(--surface-2) 50%, var(--surface-1) 75%);
      background-size: 200% 100%; animation: shimmer 1.5s infinite;
      border-radius: var(--radius-xs); height: 16px;
    }}
    @keyframes shimmer {{ 0% {{ background-position: -200% 0; }} 100% {{ background-position: 200% 0; }} }}

    @media (max-width: 1200px) {{ .metrics {{ grid-template-columns: repeat(3, 1fr); }} }}
    @media (max-width: 960px) {{
      .sections {{ grid-template-columns: 1fr; }}
      .metrics {{ grid-template-columns: repeat(2, 1fr); }}
      .svc-grid {{ grid-template-columns: 1fr; }}
      .svc-item {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .svc-item:last-child {{ border-bottom: 0; }}
      .queue-cols, .ztt-grid {{ grid-template-columns: 1fr; }}
      .queue-col {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .queue-col:last-child {{ border-bottom: 0; }}
      .ztt-section {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .ztt-section:last-child {{ border-bottom: 0; }}
    }}
    @media (max-width: 640px) {{
      .metrics {{ grid-template-columns: 1fr; }}
      .main {{ padding: 16px; }}
      .header-inner {{ padding: 0 16px; flex-wrap: wrap; }}
    }}
  </style>
</head>
<body>
  <header class="header">
    <div class="header-inner">
      <div class="header-left">
        <div class="logo">K</div>
        <div>
          <div class="header-title">KubeDojo Local Monitor</div>
          <div class="header-sub">Read-only operations console &middot; port 8768</div>
        </div>
      </div>
      <div class="header-right">
        <span class="status-pill" id="conn-status"><span class="dot"></span> Connected</span>
        <span class="last-updated" id="last-updated"></span>
        <button class="refresh-btn" id="refresh">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
      </div>
    </div>
  </header>

  <div class="main">
    <div class="metrics" id="metrics">
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:60%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:80%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:70%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:50%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:65%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:75%"></div></div>
    </div>

    <div class="sections">
      <div class="section-full">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-icon" style="background:var(--accent-muted);color:var(--accent);">#</span>
              Site by Track
            </div>
            <span class="panel-badge" id="tracks-badge" style="background:var(--accent-muted);color:var(--accent);"></span>
          </div>
          <div class="panel-body-flush">
            <table class="tracks-table">
              <thead>
                <tr>
                  <th>Track</th>
                  <th class="num">Modules</th>
                  <th class="num">V2 write</th>
                  <th class="num">V2 review</th>
                  <th class="num">V2 patch</th>
                  <th class="num">V2 dead</th>
                  <th class="num">T2 pend</th>
                </tr>
              </thead>
              <tbody id="tracks-body"></tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="section-full">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-icon" style="background:var(--green-muted);color:var(--green);">S</span>
              Runtime Services
            </div>
            <span class="panel-badge" id="svc-badge" style="background:var(--green-muted);color:var(--green);"></span>
          </div>
          <div class="panel-body-flush">
            <div class="svc-grid" id="services"></div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--accent-muted);color:var(--accent);">P</span>
            V2 Pipeline
          </div>
          <span class="panel-badge" id="v2-badge"></span>
        </div>
        <div class="panel-body-flush" id="v2-body"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--teal-muted);color:var(--teal);">T</span>
            Translation V2
          </div>
          <span class="panel-badge" id="trans-badge"></span>
        </div>
        <div class="panel-body-flush" id="trans-body"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--amber-muted);color:var(--amber);">G</span>
            Git Worktree
          </div>
          <span class="panel-badge" id="wt-badge"></span>
        </div>
        <div class="panel-body-flush" id="worktree"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--amber-muted);color:var(--amber);">M</span>
            Missing Modules
          </div>
          <span class="panel-badge" id="missing-badge"></span>
        </div>
        <div class="panel-body" id="missing"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--accent-muted);color:var(--accent);">F</span>
            Feedback Issue #{issue_number}
          </div>
        </div>
        <div class="panel-body" id="feedback"></div>
      </div>
    </div>
  </div>

  <script>
    const ISSUE = {issue_number};
    const $ = (sel) => document.querySelector(sel);

    async function fetchJson(url) {{
      const r = await fetch(url);
      if (!r.ok) return {{ error: `HTTP ${{r.status}}`, url }};
      return r.json();
    }}

    function esc(s) {{
      const d = document.createElement('div');
      d.textContent = String(s ?? '');
      return d.innerHTML;
    }}

    function progressBar(pct, color) {{
      const p = Math.max(0, Math.min(100, pct || 0));
      return `<div class="progress-track"><div class="progress-fill ${{color}}" style="width:${{p}}%"></div></div>`;
    }}

    function renderMetrics(summary, worktree, feedback, t2FullQueue) {{
      const v2 = summary.v2_pipeline || {{}};
      const t2 = t2FullQueue || summary.translation_v2_pipeline?.queue || {{}};
      const missing = summary.missing_modules || {{}};
      const svc = summary.runtime_services || {{}};
      const v2rate = v2.convergence_rate ?? 0;
      const t2rate = t2.convergence_rate ?? 0;
      const activeMissing = missing.active_exact?.missing ?? 0;

      const cards = [
        {{
          label: 'English Modules',
          value: summary.english_modules ?? 0,
          cls: 'accent',
          sub: `${{summary.tracks?.length ?? 0}} tracks`,
        }},
        {{
          label: 'V2 Convergence',
          value: `${{v2rate.toFixed(1)}}%`,
          cls: v2rate >= 90 ? 'good' : v2rate >= 50 ? 'warn' : 'bad',
          sub: `${{v2.total_modules ?? 0}} modules tracked`,
          bar: {{ pct: v2rate, color: v2rate >= 90 ? 'green' : 'amber' }},
        }},
        {{
          label: 'Translation V2',
          value: `${{t2rate.toFixed(1)}}%`,
          cls: t2rate >= 90 ? 'good' : t2rate >= 50 ? 'warn' : 'bad',
          sub: `${{t2.total_modules ?? 0}} modules tracked`,
          bar: {{ pct: t2rate, color: t2rate >= 90 ? 'green' : 'amber' }},
        }},
        {{
          label: 'Active Missing',
          value: activeMissing,
          cls: activeMissing === 0 ? 'good' : 'warn',
          sub: `${{missing.deferred?.missing_min ?? 0}}&ndash;${{missing.deferred?.missing_max ?? 0}} deferred`,
        }},
        (() => {{
          const run = svc.running ?? 0;
          const stop = svc.stopped ?? 0;
          const st = svc.stale ?? 0;
          const total = svc.total ?? (run + stop + st);
          const bits = [];
          if (stop) bits.push(`${{stop}} stopped`);
          if (st) bits.push(`${{st}} stale`);
          return {{
            label: 'Services',
            value: `${{run}}/${{total}}`,
            cls: st ? 'bad' : (stop ? 'warn' : 'good'),
            sub: bits.length ? bits.join(' · ') : 'All running',
          }};
        }})(),
        {{
          label: 'Worktree',
          value: worktree.dirty ? `${{worktree.counts?.total ?? 0}} files` : 'Clean',
          cls: worktree.dirty ? 'warn' : 'good',
          sub: worktree.branch ? `${{esc(worktree.branch)}}${{worktree.ahead ? ` +${{worktree.ahead}}` : ''}}` : '',
        }},
      ];

      $('#metrics').innerHTML = cards.map(c => `
        <div class="metric ${{c.cls}}">
          <div class="metric-label">${{c.label}}</div>
          <div class="metric-value">${{c.value}}</div>
          ${{c.sub ? `<div class="metric-sub">${{c.sub}}</div>` : ''}}
          ${{c.bar ? progressBar(c.bar.pct, c.bar.color) : ''}}
        </div>
      `).join('');
    }}

    function formatUptime(seconds) {{
      if (seconds == null || !isFinite(seconds) || seconds < 0) return '';
      const s = Math.floor(seconds);
      if (s < 60) return `${{s}}s`;
      const m = Math.floor(s / 60);
      if (m < 60) return `${{m}}m`;
      const h = Math.floor(m / 60);
      if (h < 48) return `${{h}}h ${{m % 60}}m`;
      const d = Math.floor(h / 24);
      return `${{d}}d ${{h % 24}}h`;
    }}

    function renderServices(data) {{
      if (!data.services || data.services.length === 0) {{
        $('#services').innerHTML = '<div class="empty-state">No services configured</div>';
        return;
      }}
      const total = data.total ?? (data.running + data.stopped + (data.stale || 0));
      const badge = $('#svc-badge');
      const badgeBits = [`${{data.running}} / ${{total}} running`];
      if (data.stale) badgeBits.push(`${{data.stale}} stale`);
      badge.textContent = badgeBits.join(' · ');
      if (data.stale) {{
        badge.style.background = 'var(--red-muted)';
        badge.style.color = 'var(--red)';
      }} else if (data.stopped === 0) {{
        badge.style.background = 'var(--green-muted)';
        badge.style.color = 'var(--green)';
      }} else {{
        badge.style.background = 'var(--amber-muted)';
        badge.style.color = 'var(--amber)';
      }}

      $('#services').innerHTML = data.services.map(s => {{
        const chips = [];
        if (s.status === 'stale') chips.push('<span class="svc-chip stale">Stale PID</span>');
        if (s.known === false) chips.push('<span class="svc-chip discovered">Discovered</span>');
        let detail;
        if (s.status === 'running') {{
          const up = formatUptime(s.uptime_seconds);
          detail = `PID ${{s.pid}}${{up ? ` &middot; up ${{up}}` : ''}}`;
        }} else if (s.status === 'stale') {{
          detail = s.pid != null ? `PID ${{s.pid}} not responding` : 'Unreadable PID file';
        }} else {{
          detail = 'Stopped';
        }}
        if (s.port) detail += ` &middot; :${{s.port}}`;
        return `
        <div class="svc-item">
          <span class="svc-dot ${{s.status}}"></span>
          <div class="svc-info">
            <div class="svc-name">${{esc(s.label)}}${{chips.join('')}}</div>
            <div class="svc-detail mono">${{detail}}</div>
          </div>
        </div>`;
      }}).join('');
    }}

    const TRACK_LABEL = {{
      'prerequisites': 'Prerequisites',
      'linux': 'Linux',
      'k8s': 'Kubernetes',
      'cloud': 'Cloud',
      'platform': 'Platform Engineering',
      'on-premises': 'On-Premises',
      'ai-ml-engineering': 'AI/ML Engineering',
      'other': 'Other',
    }};

    function shortenKey(key) {{
      return String(key || '').replace(/^src\\/content\\/docs\\//, '').replace(/\\.md$/, '');
    }}

    function renderSiteTracks(summary, v2, t2Queue) {{
      const tracks = summary.tracks || [];
      const v2ByTrack = new Map(((v2 || {{}}).per_track || []).map(t => [t.slug, t.counts]));
      const t2ByTrack = new Map(((t2Queue || {{}}).per_track || []).map(t => [t.slug, t.counts]));

      const total = tracks.reduce((sum, t) => sum + (t.module_count || 0), 0);
      const active = tracks.filter(t => t.module_count > 0).length;
      $('#tracks-badge').textContent = `${{total}} modules · ${{active}} tracks`;

      const cls = (n) => n > 0 ? '' : 'zero';
      const rowFor = (t) => {{
        const v = v2ByTrack.get(t.slug) || {{}};
        const tr2 = t2ByTrack.get(t.slug) || {{}};
        const t2Pend = (tr2.pending_write || 0) + (tr2.pending_review || 0);
        const deadCls = (v.dead_letter || 0) > 0 ? 'bad' : 'zero';
        const reviewCls = (v.pending_review || 0) > 0 ? 'warn' : 'zero';
        return `<tr>
          <td class="name">${{esc(t.label)}}</td>
          <td class="num">${{t.module_count}}</td>
          <td class="num ${{cls(v.pending_write || 0)}}">${{v.pending_write || 0}}</td>
          <td class="num ${{reviewCls}}">${{v.pending_review || 0}}</td>
          <td class="num ${{cls(v.pending_patch || 0)}}">${{v.pending_patch || 0}}</td>
          <td class="num ${{deadCls}}">${{v.dead_letter || 0}}</td>
          <td class="num ${{cls(t2Pend)}}">${{t2Pend}}</td>
        </tr>`;
      }};

      $('#tracks-body').innerHTML = tracks.map(rowFor).join('');
    }}

    function renderPipelinePanel(bodyId, badgeId, data, label) {{
      const el = $(bodyId);
      const badge = $(badgeId);
      if (!data || data.error) {{
        badge.textContent = 'Unknown';
        badge.style.background = 'var(--amber-muted)';
        badge.style.color = 'var(--amber)';
        el.innerHTML = `<div class="empty-state">${{data?.error ? esc(data.error) : 'No data'}}</div>`;
        return;
      }}
      const counts = data.counts || {{}};
      const totalPending = (counts.pending_write || 0) + (counts.pending_review || 0) + (counts.pending_patch || 0);
      const dead = counts.dead_letter || 0;
      if (totalPending === 0 && dead === 0) {{
        badge.textContent = 'Idle';
        badge.style.background = 'var(--green-muted)';
        badge.style.color = 'var(--green)';
      }} else {{
        const parts = [];
        if (totalPending) parts.push(`${{totalPending}} pending`);
        if (dead) parts.push(`${{dead}} dead`);
        badge.textContent = parts.join(' · ');
        badge.style.background = dead ? 'var(--red-muted)' : 'var(--amber-muted)';
        badge.style.color = dead ? 'var(--red)' : 'var(--amber)';
      }}

      const done = counts.done ?? 0;
      const tracked = done + totalPending + dead + (counts.in_progress ?? 0);
      const conv = tracked > 0 ? (done / tracked * 100) : (data.convergence_rate ?? 0);
      let html = `
        <div class="queue-summary">
          <div class="queue-stat"><div class="queue-stat-val">${{done}}</div><div class="queue-stat-label">Done</div></div>
          <div class="queue-stat"><div class="queue-stat-val">${{totalPending}}</div><div class="queue-stat-label">Pending</div></div>
          <div class="queue-stat"><div class="queue-stat-val">${{dead}}</div><div class="queue-stat-label">Dead</div></div>
          <div class="queue-stat"><div class="queue-stat-val">${{conv.toFixed(1)}}%</div><div class="queue-stat-label">Converged</div></div>
        </div>`;

      const perTrack = data.per_track || [];
      const active = perTrack.filter(t => {{
        const c = t.counts || {{}};
        return (c.pending_write || 0) + (c.pending_review || 0) + (c.pending_patch || 0) + (c.dead_letter || 0) > 0;
      }});
      html += '<div class="queue-per-track">';
      if (active.length === 0) {{
        html += `<div class="empty-state">All tracks idle</div>`;
      }} else {{
        for (const t of active) {{
          const c = t.counts || {{}};
          const bits = [];
          if (c.pending_write) bits.push(`<span class="pill w">${{c.pending_write}}W</span>`);
          if (c.pending_review) bits.push(`<span class="pill r">${{c.pending_review}}R</span>`);
          if (c.pending_patch) bits.push(`<span class="pill p">${{c.pending_patch}}P</span>`);
          if (c.dead_letter) bits.push(`<span class="pill d">${{c.dead_letter}}D</span>`);
          html += `<div class="qpt-row">
            <span class="qpt-name">${{esc(TRACK_LABEL[t.slug] || t.slug)}}</span>
            <span class="qpt-status">${{bits.join(' ')}}</span>
          </div>`;
        }}
      }}
      html += '</div>';

      const topItems = [];
      for (const t of perTrack) {{
        if (!t.modules) continue;
        for (const kind of ['dead_letter', 'pending_review', 'pending_write', 'pending_patch']) {{
          for (const m of (t.modules[kind] || [])) {{
            topItems.push({{kind, path: m}});
          }}
        }}
      }}
      const kindLabel = {{dead_letter: 'D', pending_review: 'R', pending_write: 'W', pending_patch: 'P'}};
      if (topItems.length > 0) {{
        const shown = topItems.slice(0, 6);
        html += `<div class="qpt-top">
          <div class="qpt-top-title">Top items (${{shown.length}} of ${{topItems.length}})</div>
          <ul class="qpt-top-list mono">
            ${{shown.map(i => `<li><span class="qpt-top-kind ${{kindLabel[i.kind].toLowerCase()}}">${{kindLabel[i.kind]}}</span> ${{esc(shortenKey(i.path))}}</li>`).join('')}}
          </ul>
        </div>`;
      }}

      el.innerHTML = html;
    }}

    function renderWorktree(data) {{
      const el = $('#worktree');
      if (data.error) {{
        el.innerHTML = `<div class="empty-state clr-red">${{esc(data.error)}}</div>`;
        return;
      }}

      const badge = $('#wt-badge');
      if (!data.dirty) {{
        badge.textContent = 'Clean';
        badge.style.background = 'var(--green-muted)';
        badge.style.color = 'var(--green)';
        el.innerHTML = `
          <div class="wt-summary">
            <div class="wt-stat">Branch: <span class="wt-stat-val">${{esc(data.branch)}}</span></div>
          </div>
          <div class="empty-state">Working tree is clean</div>`;
        return;
      }}

      badge.textContent = `${{data.counts.total}} changes`;
      badge.style.background = 'var(--amber-muted)';
      badge.style.color = 'var(--amber)';

      const c = data.counts;
      let summary = `
        <div class="wt-summary">
          <div class="wt-stat">Branch: <span class="wt-stat-val">${{esc(data.branch)}}</span></div>
          ${{data.ahead ? `<div class="wt-stat">Ahead: <span class="wt-stat-val clr-green">+${{data.ahead}}</span></div>` : ''}}
          ${{data.behind ? `<div class="wt-stat">Behind: <span class="wt-stat-val clr-red">-${{data.behind}}</span></div>` : ''}}
          ${{c.staged ? `<div class="wt-stat">Staged: <span class="wt-stat-val clr-green">${{c.staged}}</span></div>` : ''}}
          ${{c.unstaged ? `<div class="wt-stat">Unstaged: <span class="wt-stat-val clr-amber">${{c.unstaged}}</span></div>` : ''}}
          ${{c.untracked ? `<div class="wt-stat">Untracked: <span class="wt-stat-val clr-accent">${{c.untracked}}</span></div>` : ''}}
        </div>`;

      const statusLabel = (entry) => {{
        if (entry.untracked) return ['?', 'Q'];
        if (entry.conflicted) return ['U', 'U'];
        const s = entry.index_status !== ' ' && entry.index_status !== '?' ? entry.index_status : entry.worktree_status;
        return [s, s];
      }};

      const entries = (data.entries || []).slice(0, 80);
      let rows = entries.map(e => {{
        const [label, cls] = statusLabel(e);
        return `<tr>
          <td><span class="wt-badge ${{cls}}">${{label}}</span></td>
          <td class="wt-path mono">${{esc(e.path)}}</td>
          <td><span class="wt-cat">${{e.category}}</span></td>
        </tr>`;
      }}).join('');

      el.innerHTML = `${{summary}}
        <div class="wt-scroll">
          <table class="wt-table">
            <thead><tr><th>Status</th><th>Path</th><th>Category</th></tr></thead>
            <tbody>${{rows}}</tbody>
          </table>
        </div>
        ${{data.entries.length > 80 ? `<div class="empty-state">Showing 80 of ${{data.entries.length}} entries</div>` : ''}}`;
    }}

    function renderZtt(data) {{
      const el = $('#ztt');
      const badge = $('#ztt-badge');

      if (data.error) {{
        el.innerHTML = `<div class="empty-state clr-red">${{esc(data.error)}}</div>`;
        return;
      }}

      const ready = data.ready || {{}};
      const allReady = ready.english_production_bar && ready.ukrainian_sync_clean;
      badge.textContent = allReady ? 'Ready' : 'Needs Work';
      badge.style.background = allReady ? 'var(--green-muted)' : 'var(--amber-muted)';
      badge.style.color = allReady ? 'var(--green)' : 'var(--amber)';

      const chk = (val) => val
        ? '<span class="ztt-check pass">&#10003;</span>'
        : '<span class="ztt-check fail">&#10007;</span>';

      const theory = data.theory || {{}};
      const labs = data.labs || {{}};
      const uk = data.ukrainian || {{}};

      el.innerHTML = `
        <div class="ztt-grid">
          <div class="ztt-section">
            <div class="ztt-section-title">Readiness</div>
            <div class="ztt-row">${{chk(ready.english_production_bar)}}<span class="ztt-label">English Production</span></div>
            <div class="ztt-row">${{chk(ready.ukrainian_sync_clean)}}<span class="ztt-label">Ukrainian Sync</span></div>
            <div class="ztt-section-title" style="margin-top:14px">Theory</div>
            <div class="ztt-row">${{chk(theory.all_have_frontmatter)}}<span class="ztt-label">Frontmatter</span><span class="ztt-val">${{theory.module_count ?? 0}} modules</span></div>
            <div class="ztt-row">${{chk(theory.all_have_labs)}}<span class="ztt-label">Labs Linked</span></div>
            <div class="ztt-row">${{chk(theory.meets_line_threshold)}}<span class="ztt-label">Line Threshold</span></div>
          </div>
          <div class="ztt-section">
            <div class="ztt-section-title">Labs</div>
            <div class="ztt-row">${{chk(labs.all_exist)}}<span class="ztt-label">All Exist</span><span class="ztt-val">${{labs.total ?? 0}} labs</span></div>
            <div class="ztt-row">${{chk(labs.all_executable)}}<span class="ztt-label">Executable</span></div>
            <div class="ztt-row">${{chk(labs.all_have_solutions)}}<span class="ztt-label">Solutions</span></div>
            <div class="ztt-section-title" style="margin-top:14px">Ukrainian</div>
            <div class="ztt-row">${{chk(uk.all_synced)}}<span class="ztt-label">All Synced</span><span class="ztt-val">${{uk.synced ?? 0}}/${{uk.total ?? 0}}</span></div>
            <div class="ztt-row">${{chk(uk.no_stale)}}<span class="ztt-label">No Stale</span></div>
          </div>
        </div>`;
    }}

    function renderMissing(data) {{
      const el = $('#missing');
      const badge = $('#missing-badge');

      if (data.error) {{
        el.innerHTML = `<div class="empty-state clr-red">${{esc(data.error)}}</div>`;
        return;
      }}

      const active = data.active_exact || {{}};
      const deferred = data.deferred || {{}};
      const activeList = active.modules ?? [];
      const deferredList = deferred.modules ?? [];
      const total = activeList.length + deferredList.length;

      badge.textContent = total === 0 ? 'Complete' : `${{total}} missing`;
      badge.style.background = total === 0 ? 'var(--green-muted)' : 'var(--amber-muted)';
      badge.style.color = total === 0 ? 'var(--green)' : 'var(--amber)';

      if (total === 0) {{
        el.innerHTML = '<div class="empty-state">All modules present</div>';
        return;
      }}

      let html = '';
      if (activeList.length) {{
        html += `<div class="missing-group">
          <div class="missing-group-title"><span class="wt-badge M">Active</span> ${{activeList.length}} missing</div>
          <ul class="missing-list">${{activeList.map(m => `<li class="missing-item mono">${{esc(m)}}</li>`).join('')}}</ul>
        </div>`;
      }}
      if (deferredList.length) {{
        html += `<div class="missing-group">
          <div class="missing-group-title"><span class="wt-badge Q">Deferred</span> ${{deferredList.length}} estimated</div>
          <ul class="missing-list">${{deferredList.slice(0, 20).map(m => `<li class="missing-item mono">${{esc(m)}}</li>`).join('')}}</ul>
          ${{deferredList.length > 20 ? `<div class="empty-state">+${{deferredList.length - 20}} more</div>` : ''}}
        </div>`;
      }}
      el.innerHTML = html;
    }}

    function renderFeedback(data) {{
      const el = $('#feedback');
      if (data.error) {{
        el.innerHTML = `<div class="empty-state">${{data.error === 'missing_issue_watch_state' ? 'Issue watcher not running or no data yet' : esc(data.error)}}</div>`;
        return;
      }}

      let html = `
        <div class="fb-header">
          <div class="fb-icon">#</div>
          <div>
            <div class="fb-title">${{esc(data.title || `Issue #${{data.issue_number}}`)}}</div>
            <div class="fb-meta">
              <span><span class="wt-badge ${{data.state === 'open' ? 'A' : 'D'}}">${{data.state || 'unknown'}}</span></span>
              <span>${{data.comments_count ?? 0}} comments</span>
              ${{data.updated_at ? `<span>Updated ${{esc(data.updated_at)}}</span>` : ''}}
            </div>
          </div>
        </div>`;

      if (data.last_comment) {{
        const c = data.last_comment;
        const body = typeof c === 'object' ? (c.body || JSON.stringify(c, null, 2)) : String(c);
        const author = typeof c === 'object' ? (c.author || c.user || '') : '';
        html += `
          <div class="fb-comment">
            <div class="fb-comment-header">
              ${{author ? `<strong>${{esc(author)}}</strong> &middot; ` : ''}}Latest comment
            </div>
            <div class="fb-comment-body mono">${{esc(body.substring(0, 800))}}</div>
          </div>`;
      }}
      el.innerHTML = html;
    }}

    let refreshing = false;
    async function refresh() {{
      if (refreshing) return;
      refreshing = true;
      const btn = $('#refresh');
      btn.classList.add('loading');

      try {{
        const [summary, missing, services, worktree, feedback, v2Status, transStatus] = await Promise.all([
          fetchJson('/api/status/summary'),
          fetchJson('/api/missing-modules/status'),
          fetchJson('/api/runtime/services'),
          fetchJson('/api/git/worktree'),
          fetchJson(`/api/issue-watch/${{ISSUE}}`),
          fetchJson('/api/pipeline/v2/status'),
          fetchJson('/api/translation/v2/status'),
        ]);

        summary.missing_modules = missing;
        summary.runtime_services = services;

        const t2Queue = transStatus.queue || transStatus;
        renderMetrics(summary, worktree, feedback, t2Queue);
        renderServices(services);
        renderSiteTracks(summary, v2Status, t2Queue);
        renderPipelinePanel('#v2-body', '#v2-badge', v2Status, 'V2 Pipeline');
        renderPipelinePanel('#trans-body', '#trans-badge', t2Queue, 'Translation V2');
        renderWorktree(worktree);
        renderMissing(missing);
        renderFeedback(feedback);

        const now = new Date();
        $('#last-updated').textContent = `Updated ${{now.toLocaleTimeString()}}`;
        const pill = $('#conn-status');
        pill.innerHTML = '<span class="dot"></span> Connected';
        pill.style.background = 'var(--green-muted)';
        pill.style.color = 'var(--green)';
      }} catch (err) {{
        const pill = $('#conn-status');
        pill.innerHTML = '<span class="dot"></span> Error';
        pill.style.background = 'var(--red-muted)';
        pill.style.color = 'var(--red)';
        console.error('Dashboard refresh failed:', err);
      }} finally {{
        refreshing = false;
        btn.classList.remove('loading');
      }}
    }}

    $('#refresh').addEventListener('click', refresh);
    refresh();
    setInterval(refresh, 60000);
  </script>
</body>
</html>"""


def route_request(repo_root: Path, raw_path: str) -> tuple[int, Any, str]:
    parsed = urlsplit(raw_path)
    path = parsed.path.rstrip("/") or "/"
    query = parse_qs(parsed.query)

    if path in {"/", "/dashboard"}:
        return 200, render_dashboard_html(), "text/html; charset=utf-8"
    if path == "/healthz":
        return 200, {"ok": True}, "application/json; charset=utf-8"
    if path == "/api/status/summary":
        # Dashboard hot path: skip the git-per-file translation + ZTT passes
        # (~2min total). Full versions served by /api/translation/v2/status
        # and /api/ztt/status.
        return 200, build_repo_status(repo_root, fast=True), "application/json; charset=utf-8"
    if path == "/api/missing-modules/status":
        return 200, _build_missing_modules_summary(repo_root), "application/json; charset=utf-8"
    if path == "/api/runtime/services":
        return 200, build_runtime_services_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/pipeline/v2/status":
        db_path = repo_root / ".pipeline" / "v2.db"
        if not db_path.exists():
            return 404, {"error": "missing_db", "db_path": str(db_path)}, "application/json; charset=utf-8"
        return 200, _enrich_v2_with_per_track(build_v2_status_report(db_path)), "application/json; charset=utf-8"
    if path == "/api/translation/v2/status":
        section = query.get("section", [None])[0]
        # Dashboard hot path skips the git-per-file freshness walk; callers
        # that need it can pass ?freshness=1.
        want_freshness = query.get("freshness", ["0"])[0] not in ("0", "false", "")
        db_path = repo_root / ".pipeline" / "translation_v2.db"
        if want_freshness:
            t2 = build_translation_status(repo_root, db_path=db_path, section=section)
        else:
            from translation_v2 import _build_translation_queue_status
            t2 = {
                "repo_root": str(repo_root),
                "db_path": str(db_path),
                "section": section,
                "freshness": None,
                "queue": _build_translation_queue_status(db_path) if db_path.exists() else None,
            }
        return 200, _enrich_translation_v2_with_per_track(t2), "application/json; charset=utf-8"
    if path == "/api/labs/status":
        return 200, _build_lab_summary(repo_root), "application/json; charset=utf-8"
    if path == "/api/ztt/status":
        return 200, build_ztt_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/git/worktree":
        return 200, build_worktree_status(repo_root), "application/json; charset=utf-8"
    if path.startswith("/api/issue-watch/"):
        try:
            issue_number = int(path.split("/")[-1])
        except ValueError:
            return 400, {"error": "invalid_issue_number"}, "application/json; charset=utf-8"
        payload = build_issue_watch_state(repo_root, issue_number)
        if payload is None:
            return 404, {"error": "missing_issue_watch_state", "issue_number": issue_number}, "application/json; charset=utf-8"
        return 200, payload, "application/json; charset=utf-8"
    if path.startswith("/api/module/") and path.endswith("/state"):
        module_key = unquote(path[len("/api/module/") : -len("/state")]).strip("/")
        if not module_key:
            return 400, {"error": "missing_module_key"}, "application/json; charset=utf-8"
        return 200, build_module_state(repo_root, module_key), "application/json; charset=utf-8"
    if path.startswith("/api/module/") and path.endswith("/orchestration/latest"):
        module_key = unquote(path[len("/api/module/") : -len("/orchestration/latest")]).strip("/")
        if not module_key:
            return 400, {"error": "missing_module_key"}, "application/json; charset=utf-8"
        return 200, build_module_orchestration_latest(repo_root, module_key), "application/json; charset=utf-8"
    return 404, {"error": "not_found", "path": path}, "application/json; charset=utf-8"


def make_handler(repo_root: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            status_code, payload, content_type = route_request(repo_root, self.path)
            if content_type.startswith("text/html"):
                body = str(payload).encode("utf-8")
            else:
                body = json.dumps(payload, indent=2, sort_keys=True, default=_json_default).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
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

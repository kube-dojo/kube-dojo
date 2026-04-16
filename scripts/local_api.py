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
    _build_missing_modules_summary,
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
DEFAULT_FEEDBACK_ISSUE = 248


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


def render_dashboard_html(*, issue_number: int = DEFAULT_FEEDBACK_ISSUE) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KubeDojo Local Monitor</title>
  <style>
    :root {{
      --bg: #0b1320;
      --panel: #121c2b;
      --panel-2: #18253a;
      --text: #e8eef8;
      --muted: #9db0c9;
      --accent: #4db6ac;
      --warn: #ffb74d;
      --bad: #ef5350;
      --good: #66bb6a;
      --border: #25354f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      background: radial-gradient(circle at top, #15243d 0%, var(--bg) 45%);
      color: var(--text);
    }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
    h1, h2 {{ margin: 0 0 12px; }}
    p {{ color: var(--muted); line-height: 1.5; }}
    .toolbar {{ display: flex; gap: 12px; align-items: center; margin-bottom: 24px; }}
    button {{
      background: var(--accent);
      color: #081019;
      border: 0;
      padding: 10px 14px;
      border-radius: 10px;
      font-weight: 700;
      cursor: pointer;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}
    .card, .panel {{
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.25);
    }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .value {{ font-size: 28px; font-weight: 800; margin-top: 6px; }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .bad {{ color: var(--bad); }}
    .two-col {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 16px;
    }}
    .stack {{ display: grid; gap: 16px; }}
    pre {{
      background: rgba(8, 16, 25, 0.55);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      overflow: auto;
      font-size: 12px;
      line-height: 1.45;
    }}
    .meta {{ color: var(--muted); font-size: 12px; }}
    a {{ color: #8ed1c9; }}
    @media (max-width: 960px) {{
      .two-col {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="toolbar">
      <div>
        <h1>KubeDojo Local Monitor</h1>
        <p>Read-only dashboard over the deterministic local API. Refreshes repo status, worktree, missing-module queue, ZTT, and feedback issue #{issue_number}.</p>
      </div>
      <button id="refresh">Refresh</button>
    </div>
    <div class="grid" id="cards"></div>
    <div class="two-col">
      <div class="stack">
        <section class="panel">
          <h2>Queue Summary</h2>
          <pre id="summary">Loading...</pre>
        </section>
        <section class="panel">
          <h2>Missing Modules</h2>
          <pre id="missing">Loading...</pre>
        </section>
        <section class="panel">
          <h2>Worktree</h2>
          <pre id="worktree">Loading...</pre>
        </section>
      </div>
      <div class="stack">
        <section class="panel">
          <h2>Zero to Terminal</h2>
          <pre id="ztt">Loading...</pre>
        </section>
        <section class="panel">
          <h2>Feedback Issue #{issue_number}</h2>
          <pre id="feedback">Loading...</pre>
        </section>
      </div>
    </div>
  </div>
  <script>
    const issueNumber = {issue_number};
    async function fetchJson(url) {{
      const response = await fetch(url);
      if (!response.ok) {{
        return {{ error: `HTTP ${{response.status}}`, url }};
      }}
      return response.json();
    }}
    function statusClass(flag) {{
      return flag ? 'good' : 'warn';
    }}
    function renderCards(summary, worktree, feedback) {{
      const v2 = summary.v2_pipeline || {{ counts: {{}}, convergence_rate: 0, total_modules: 0 }};
      const t2 = summary.translation_v2_pipeline?.queue || {{ counts: {{}}, convergence_rate: 0, total_modules: 0 }};
      const missing = summary.missing_modules || {{ active_exact: {{}}, deferred: {{}} }};
      const ztt = summary.zero_to_terminal || {{ ready: {{}}, theory: {{}}, labs: {{}}, ukrainian: {{}} }};
      const cards = [
        ['English Modules', summary.english_modules ?? 0, ''],
        ['V2 Convergence', `${{(v2.convergence_rate ?? 0).toFixed(1)}}%`, ''],
        ['Translation V2', `${{(t2.convergence_rate ?? 0).toFixed(1)}}%`, ''],
        ['Active Missing', missing.active_exact?.missing ?? 0, (missing.active_exact?.missing ?? 0) === 0 ? 'good' : 'warn'],
        ['Deferred Missing', `${{missing.deferred?.missing_min ?? 0}}-${{missing.deferred?.missing_max ?? 0}}`, ''],
        ['Worktree Dirty', worktree.dirty ? 'YES' : 'NO', worktree.dirty ? 'warn' : 'good'],
        ['ZTT English', ztt.ready?.english_production_bar ? 'READY' : 'NOT READY', ztt.ready?.english_production_bar ? 'good' : 'warn'],
        ['ZTT Ukrainian', ztt.ready?.ukrainian_sync_clean ? 'CLEAN' : 'DRIFT', ztt.ready?.ukrainian_sync_clean ? 'good' : 'warn'],
        ['Feedback Comments', feedback.comments_count ?? 0, ''],
        ['Feedback Updated', feedback.updated_at || 'n/a', ''],
      ];
      const root = document.getElementById('cards');
      root.innerHTML = cards.map(([label, value, cls]) => `
        <div class="card">
          <div class="label">${{label}}</div>
          <div class="value ${{cls}}">${{value}}</div>
        </div>
      `).join('');
    }}
    function pretty(obj) {{
      return JSON.stringify(obj, null, 2);
    }}
    async function refresh() {{
      const [summary, missing, worktree, ztt, feedback] = await Promise.all([
        fetchJson('/api/status/summary'),
        fetchJson('/api/missing-modules/status'),
        fetchJson('/api/git/worktree'),
        fetchJson('/api/ztt/status'),
        fetchJson(`/api/issue-watch/${{issueNumber}}`),
      ]);
      summary.missing_modules = missing;
      renderCards(summary, worktree, feedback);
      document.getElementById('summary').textContent = pretty({{
        v2_pipeline: summary.v2_pipeline,
        translation_v2_pipeline: summary.translation_v2_pipeline,
        translations: summary.translations,
        labs: summary.labs,
      }});
      document.getElementById('missing').textContent = pretty(summary.missing_modules);
      document.getElementById('worktree').textContent = pretty(worktree);
      document.getElementById('ztt').textContent = pretty(ztt);
      document.getElementById('feedback').textContent = pretty(feedback);
    }}
    document.getElementById('refresh').addEventListener('click', refresh);
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
        return 200, build_repo_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/missing-modules/status":
        return 200, _build_missing_modules_summary(repo_root), "application/json; charset=utf-8"
    if path == "/api/pipeline/v2/status":
        db_path = repo_root / ".pipeline" / "v2.db"
        if not db_path.exists():
            return 404, {"error": "missing_db", "db_path": str(db_path)}, "application/json; charset=utf-8"
        return 200, build_v2_status_report(db_path), "application/json; charset=utf-8"
    if path == "/api/translation/v2/status":
        section = query.get("section", [None])[0]
        return (
            200,
            build_translation_status(
                repo_root,
                db_path=repo_root / ".pipeline" / "translation_v2.db",
                section=section,
            ),
            "application/json; charset=utf-8",
        )
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

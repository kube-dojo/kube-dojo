from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_module()


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _init_repo(repo_root: Path) -> None:
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "test@example.com")
    _git(repo_root, "config", "user.name", "Test User")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _module_frontmatter(*, lab_id: str | None = None) -> str:
    lines = ["---", 'title: "Example"']
    if lab_id:
        lines.extend(
            [
                "lab:",
                f'  id: "{lab_id}"',
                f'  url: "https://killercoda.com/kubedojo/scenario/{lab_id}"',
                '  duration: "20 min"',
                '  difficulty: "beginner"',
                '  environment: "ubuntu"',
            ]
        )
    lines.extend(["---", "", "body"])
    return "\n".join(lines)


def _init_v2_db(path: Path, *, module_key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE jobs (
              id INTEGER PRIMARY KEY,
              module_key TEXT NOT NULL,
              phase TEXT NOT NULL,
              model TEXT,
              queue_state TEXT NOT NULL,
              leased_by TEXT,
              lease_id TEXT,
              leased_at INTEGER,
              lease_expires_at INTEGER,
              enqueued_at INTEGER,
              requested_calls INTEGER,
              estimated_usd REAL,
              idempotency_key TEXT
            );
            CREATE TABLE events (
              id INTEGER PRIMARY KEY,
              module_key TEXT NOT NULL,
              type TEXT NOT NULL,
              payload_json TEXT DEFAULT '{}',
              at INTEGER
            );
            """
        )
        conn.execute(
            """
            INSERT INTO jobs
            (module_key, phase, model, queue_state, requested_calls, estimated_usd, idempotency_key)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (module_key, "review", "codex", "completed", 1, 0.01, f"{module_key}-job"),
        )
        conn.execute(
            "INSERT INTO events (module_key, type, payload_json, at) VALUES (?, ?, ?, ?)",
            (module_key, "review_completed", '{"verdict":"APPROVE"}', 1),
        )
        conn.commit()
    finally:
        conn.close()


def _init_translation_v2_db(path: Path, *, module_key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE jobs (
              id INTEGER PRIMARY KEY,
              module_key TEXT NOT NULL,
              phase TEXT NOT NULL,
              model TEXT,
              queue_state TEXT NOT NULL
            );
            CREATE TABLE events (
              id INTEGER PRIMARY KEY,
              module_key TEXT NOT NULL,
              type TEXT NOT NULL,
              payload_json TEXT DEFAULT '{}'
            );
            """
        )
        conn.execute(
            "INSERT INTO jobs (module_key, phase, model, queue_state) VALUES (?, ?, ?, ?)",
            (module_key, "write", "gemini", "completed"),
        )
        conn.execute(
            "INSERT INTO events (module_key, type, payload_json) VALUES (?, ?, ?)",
            (module_key, "translation_verified", '{"status":"synced"}'),
        )
        conn.commit()
    finally:
        conn.close()


def _setup_repo(repo_root: Path) -> tuple[str, Path]:
    _init_repo(repo_root)
    en_path = repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.1-alpha.md"
    _write(en_path, _module_frontmatter(lab_id="prereq-0.1-alpha"))
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "add english")
    en_commit = _git(repo_root, "log", "-1", "--format=%H", "--", str(en_path))
    _write(
        repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal/module-0.1-alpha.md",
        "\n".join(
            [
                "---",
                f'en_commit: "{en_commit}"',
                f'en_file: "{en_path.relative_to(repo_root).as_posix()}"',
                "---",
                "",
                "body",
            ]
        ),
    )
    _write(repo_root / ".pipeline/fact-ledgers/prerequisites__zero-to-terminal__module-0.1-alpha.json", "{}")
    _write(
        repo_root / ".pipeline/lab-state.yaml",
        yaml.dump(
            {
                "labs": {
                    "prereq-0.1-alpha": {
                        "phase": "done",
                        "severity": "clean",
                        "module": "prerequisites/zero-to-terminal/module-0.1-alpha",
                    }
                }
            },
            sort_keys=False,
        ),
    )
    module_key = "prerequisites/zero-to-terminal/module-0.1-alpha"
    _init_v2_db(repo_root / ".pipeline/v2.db", module_key=module_key)
    _init_translation_v2_db(repo_root / ".pipeline/translation_v2.db", module_key=module_key)

    # Add pending modules for list verification
    conn_v2 = sqlite3.connect(repo_root / ".pipeline/v2.db")
    conn_v2.execute(
        "INSERT INTO jobs (module_key, phase, queue_state) VALUES (?, ?, ?)",
        ("pending/v2/review", "review", "pending"),
    )
    conn_v2.execute(
        "INSERT INTO jobs (module_key, phase, queue_state) VALUES (?, ?, ?)",
        ("pending/v2/write", "write", "pending"),
    )
    conn_v2.commit()
    conn_v2.close()

    conn_trans = sqlite3.connect(repo_root / ".pipeline/translation_v2.db")
    conn_trans.execute(
        "INSERT INTO jobs (module_key, phase, queue_state) VALUES (?, ?, ?)",
        ("pending/trans/review", "review", "pending"),
    )
    conn_trans.execute(
        "INSERT INTO jobs (module_key, phase, queue_state) VALUES (?, ?, ?)",
        ("pending/trans/write", "write", "pending"),
    )
    conn_trans.commit()
    conn_trans.close()

    return module_key, en_path


def test_build_worktree_status_classifies_source_and_generated_changes(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    _write(repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.1-alpha.md", _module_frontmatter())
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "initial")

    _write(repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.1-alpha.md", "changed\n")
    _write(repo_root / "dist/index.html", "generated\n")

    status = local_api.build_worktree_status(repo_root)

    assert status["ok"] is True
    assert status["dirty"] is True
    assert status["categories"]["source"] == 1
    assert status["categories"]["generated"] == 1


def test_route_request_serves_summary_and_module_endpoints(tmp_path: Path) -> None:
    repo_root = tmp_path
    module_key, _ = _setup_repo(repo_root)

    status_code, summary, content_type = local_api.route_request(repo_root, "/api/status/summary")
    assert status_code == 200
    assert content_type.startswith("application/json")
    # Dashboard hot path skips ZTT and translation freshness for perf.
    assert summary["zero_to_terminal"] is None
    assert summary["translations"] is None
    assert summary["translation_v2_pipeline"] is None
    assert "missing_modules" in summary
    # New per-track rollup is present and covers the known tracks.
    assert isinstance(summary.get("tracks"), list)
    track_slugs = {t["slug"] for t in summary["tracks"]}
    assert {"prerequisites", "k8s"} <= track_slugs
    # V2 pipeline is enriched with per-track groupings.
    assert isinstance(summary["v2_pipeline"].get("per_track"), list)

    status_code, missing_modules, _ = local_api.route_request(repo_root, "/api/missing-modules/status")
    assert status_code == 200
    assert missing_modules["active_exact"]["missing"] > 0
    assert missing_modules["deferred"]["missing_min"] == 3

    status_code, services, _ = local_api.route_request(repo_root, "/api/runtime/services")
    assert status_code == 200
    assert services["stopped"] >= 1
    # New shape: total/running/stopped/stale always present; per-service fields include uptime + stale flag.
    assert services["total"] == services["running"] + services["stopped"] + services["stale"]
    api_entry = next(s for s in services["services"] if s["name"] == "api")
    assert api_entry["status"] == "stopped"
    assert api_entry["uptime_seconds"] is None
    assert api_entry["stale_pid_file"] is False
    assert api_entry["known"] is True

    status_code, module_state, _ = local_api.route_request(
        repo_root, f"/api/module/{module_key}/state"
    )
    assert status_code == 200
    assert module_state["english_exists"] is True
    assert module_state["ukrainian_state"]["status"] == "synced"
    assert module_state["lab"]["state"]["severity"] == "clean"

    status_code, latest, _ = local_api.route_request(
        repo_root, f"/api/module/{module_key}/orchestration/latest"
    )
    assert status_code == 200
    assert latest["v2"]["latest_job"]["phase"] == "review"
    assert latest["translation_v2"]["latest_event"]["type"] == "translation_verified"


def test_runtime_services_detects_stale_pid_and_discovers_unknown_workers(tmp_path: Path) -> None:
    repo_root = tmp_path
    pids_dir = repo_root / ".pids"
    pids_dir.mkdir()

    # Stale known service: pid file points at a PID that's definitely not alive.
    (pids_dir / "api.pid").write_text("999999\n", encoding="utf-8")
    # Running known service: use our own PID so the existence probe succeeds.
    import os as _os
    (pids_dir / "dev.pid").write_text(f"{_os.getpid()}\n", encoding="utf-8")
    # Discovered (not in RUNTIME_SERVICES) stale worker.
    (pids_dir / "adhoc-worker.pid").write_text("999998\n", encoding="utf-8")

    payload = local_api.build_runtime_services_status(repo_root)

    by_name = {s["name"]: s for s in payload["services"]}
    assert by_name["api"]["status"] == "stale"
    assert by_name["api"]["stale_pid_file"] is True
    assert by_name["dev"]["status"] == "running"
    assert by_name["dev"]["uptime_seconds"] is not None
    assert by_name["dev"]["uptime_seconds"] >= 0
    assert "adhoc-worker" in by_name
    assert by_name["adhoc-worker"]["known"] is False
    assert by_name["adhoc-worker"]["status"] == "stale"

    assert payload["stale"] >= 2
    assert payload["running"] >= 1
    assert payload["total"] == payload["running"] + payload["stopped"] + payload["stale"]


def test_route_request_supports_translation_section_and_missing_db(tmp_path: Path) -> None:
    repo_root = tmp_path
    _setup_repo(repo_root)

    # Fast path (default): freshness is skipped.
    status_code, translation, _ = local_api.route_request(
        repo_root,
        "/api/translation/v2/status?section=prerequisites/zero-to-terminal",
    )
    assert status_code == 200
    assert translation["freshness"] is None
    assert "pending/trans/review" in translation["queue"]["pending_review"]
    assert "pending/trans/write" in translation["queue"]["pending_write"]
    assert isinstance(translation["queue"].get("per_track"), list)

    # Opt in to the full freshness walk.
    status_code, translation_full, _ = local_api.route_request(
        repo_root,
        "/api/translation/v2/status?section=prerequisites/zero-to-terminal&freshness=1",
    )
    assert status_code == 200
    assert translation_full["freshness"]["section"] == "prerequisites/zero-to-terminal"

    status_code, v2, _ = local_api.route_request(repo_root, "/api/pipeline/v2/status")
    assert status_code == 200
    assert "pending/v2/review" in v2["pending_review"]
    assert "pending/v2/write" in v2["pending_write"]

    (repo_root / ".pipeline" / "v2.db").unlink()
    status_code, payload, _ = local_api.route_request(repo_root, "/api/pipeline/v2/status")
    assert status_code == 404
    assert payload["error"] == "missing_db"


def test_route_request_serves_dashboard_and_issue_watch(tmp_path: Path) -> None:
    repo_root = tmp_path
    _setup_repo(repo_root)
    watch_path = repo_root / ".pipeline" / "issue-watch" / "248.json"
    watch_path.parent.mkdir(parents=True, exist_ok=True)
    watch_path.write_text(
        json.dumps(
            {
                "number": 248,
                "title": "Review batch",
                "url": "https://example.test/issues/248",
                "state": "OPEN",
                "updatedAt": "2026-04-16T09:00:00Z",
                "comments": [
                    {
                        "url": "https://example.test/issues/248#issuecomment-1",
                        "createdAt": "2026-04-16T09:00:00Z",
                        "author": {"login": "user1"},
                        "body": "feedback",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    status_code, html, content_type = local_api.route_request(repo_root, "/")
    assert status_code == 200
    assert content_type.startswith("text/html")
    assert "KubeDojo Local Monitor" in html

    status_code, payload, content_type = local_api.route_request(repo_root, "/api/issue-watch/248")
    assert status_code == 200
    assert content_type.startswith("application/json")
    assert payload["comments_count"] == 1


def test_cli_starts_server_and_reports_host_port(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    process = subprocess.Popen(
        [
            sys.executable,
            "scripts/local_api.py",
            "--host",
            "127.0.0.1",
            "--port",
            "8876",
            "--repo-root",
            str(repo_root),
        ],
        cwd="/Users/krisztiankoos/projects/kubedojo",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        line = process.stdout.readline().strip()
        data = json.loads(line)
        assert data["host"] == "127.0.0.1"
        assert data["port"] == 8876
    finally:
        process.terminate()
        process.wait(timeout=5)

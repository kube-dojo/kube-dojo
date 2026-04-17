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
              priority INTEGER,
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
              lease_id TEXT,
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


def test_module_endpoints_reject_path_traversal(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)

    hostile_keys = [
        "../../../../etc/passwd",
        "../../.agents/skills/platform-expert/SKILL",
        "..%2F..%2Fetc%2Fpasswd",  # URL-encoded traversal
        "foo/../bar",
        ".hidden/module",
        "foo//bar",  # empty middle segment
        "UPPERCASE/module",  # uppercase not allowed in slugs
        "foo/bar$baz",  # disallowed char
    ]

    for hostile in hostile_keys:
        status_state, payload_state, _ = local_api.route_request(
            repo_root, f"/api/module/{hostile}/state"
        )
        assert status_state == 400, (hostile, payload_state)
        assert payload_state["error"] in {"invalid_module_key", "missing_module_key"}

        status_orch, payload_orch, _ = local_api.route_request(
            repo_root, f"/api/module/{hostile}/orchestration/latest"
        )
        assert status_orch == 400, (hostile, payload_orch)
        assert payload_orch["error"] in {"invalid_module_key", "missing_module_key"}


def test_module_endpoints_accept_legitimate_keys(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    # Legit slugs should pass validation and reach the handler even if the
    # file doesn't exist (the handler reports english_exists: False).
    status_code, payload, _ = local_api.route_request(
        repo_root, "/api/module/prerequisites/zero-to-terminal/module-0.1-alpha/state"
    )
    assert status_code == 200
    assert payload["english_exists"] is False


def test_route_request_returns_json_error_on_sqlite_schema_drift(tmp_path: Path) -> None:
    """If a v2 DB exists but has a broken schema, the handler must return a
    JSON error envelope via do_GET, not raise into the HTTP server."""
    repo_root = tmp_path
    _init_repo(repo_root)
    v2_db = repo_root / ".pipeline" / "v2.db"
    v2_db.parent.mkdir(parents=True, exist_ok=True)
    # Create a DB with a jobs table missing the queue_state column the reader needs.
    conn = sqlite3.connect(v2_db)
    try:
        conn.execute("CREATE TABLE jobs (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()

    # route_request will raise sqlite3.OperationalError on this broken schema.
    # The handler must wrap that into a 500 JSON envelope.
    import http.client
    from threading import Thread

    handler_cls = local_api.make_handler(repo_root)
    server = local_api.ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn_http = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn_http.request("GET", "/api/pipeline/v2/status")
        resp = conn_http.getresponse()
        body = resp.read().decode("utf-8")
        assert resp.status == 500
        payload = json.loads(body)
        assert payload["error"] in {"sqlite_error", "internal_error"}
        assert "path" in payload
    finally:
        server.shutdown()
        server.server_close()


def test_pid_reuse_detection_marks_old_process_as_stale(
    tmp_path: Path, monkeypatch
) -> None:
    """If the live process started long before the pid file was written, the
    pid file is treated as stale (PID was reused by an unrelated process)."""
    import os as _os

    pid_path = tmp_path / "reused.pid"
    pid_path.write_text(f"{_os.getpid()}\n", encoding="utf-8")
    # Stub process age to simulate a long-running process that predates the
    # pid file by much more than the reuse slack.
    monkeypatch.setattr(
        local_api,
        "_process_age_seconds",
        lambda pid: local_api._PID_REUSE_SLACK_SECONDS + 3600.0,
    )
    probe = local_api._inspect_pid_file(pid_path)
    assert probe["status"] == "stale"
    assert probe["stale_pid_file"] is True


def test_pid_fresh_process_reports_running(tmp_path: Path, monkeypatch) -> None:
    import os as _os

    pid_path = tmp_path / "fresh.pid"
    pid_path.write_text(f"{_os.getpid()}\n", encoding="utf-8")
    # Process age within the slack window -> should report running.
    monkeypatch.setattr(local_api, "_process_age_seconds", lambda pid: 5.0)
    probe = local_api._inspect_pid_file(pid_path)
    assert probe["status"] == "running"
    assert probe["stale_pid_file"] is False
    assert probe["uptime_seconds"] == 5.0


def test_pid_reuse_helper_handles_missing_process() -> None:
    # Very high PID that's almost certainly not a live process.
    assert local_api._process_age_seconds(999_999) is None


def test_api_schema_advertises_new_endpoints() -> None:
    schema = local_api.build_api_schema()
    assert schema["version"] == 1
    paths = {e["path"] for e in schema["endpoints"]}
    # Must advertise new endpoints so agents can discover them without
    # reading this file.
    assert "/api/briefing/session" in paths
    assert "/api/schema" in paths
    assert "/api/git/worktrees" in paths
    assert "/api/git/worktree" in paths  # singular still there
    assert "conventions" in schema
    assert "errors" in schema["conventions"]


def test_weak_etag_stable_for_identical_bytes() -> None:
    a = local_api._weak_etag(b"hello world")
    b = local_api._weak_etag(b"hello world")
    c = local_api._weak_etag(b"hello worlds")
    assert a == b
    assert a != c
    assert a.startswith('W/"sha256:')


def test_match_etag_handles_list_weak_and_star() -> None:
    etag = 'W/"sha256:abc123"'
    assert local_api._match_etag(etag, etag) is True
    assert local_api._match_etag("*", etag) is True
    assert local_api._match_etag('W/"sha256:nope"', etag) is False
    # Strong/weak equivalence for comparison.
    assert local_api._match_etag('"sha256:abc123"', etag) is True
    # Comma-separated list.
    assert local_api._match_etag(f'"other", {etag}, "other2"', etag) is True
    assert local_api._match_etag("", etag) is False


def test_normalized_cache_key_is_order_invariant() -> None:
    k1 = local_api._normalized_cache_key("/x", {"a": ["1"], "b": ["2"]})
    k2 = local_api._normalized_cache_key("/x", {"b": ["2"], "a": ["1"]})
    assert k1 == k2
    assert local_api._normalized_cache_key("/x", {}) == "/x"


def test_sqlite_version_key_changes_on_write(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    # Absent DB has an absent sentinel.
    absent = local_api._sqlite_version_key(db_path)
    assert absent[0] == "absent"
    # Create + insert = new version key.
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.commit()
    conn.close()
    v1 = local_api._sqlite_version_key(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    v2 = local_api._sqlite_version_key(db_path)
    assert v1 != v2
    assert v1[0] != "absent"


def test_cached_response_reuses_entry_until_version_bump(tmp_path: Path) -> None:
    # Use a unique key so test isolation holds across tests.
    key = f"/test/cache/{id(tmp_path)}"
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return 200, {"hits": calls["n"]}, "application/json; charset=utf-8"

    version_state = {"v": 1}

    def version():
        return ("v", version_state["v"])

    code_a, body_a, _ct, etag_a = local_api.cached_response(
        key, ttl_seconds=60, version_fn=version, builder=builder
    )
    assert code_a == 200
    assert calls["n"] == 1

    # Second call within TTL + same version -> cached.
    code_b, body_b, _ct, etag_b = local_api.cached_response(
        key, ttl_seconds=60, version_fn=version, builder=builder
    )
    assert calls["n"] == 1
    assert body_b is body_a or body_b == body_a
    assert etag_b == etag_a

    # Version bump -> rebuild.
    version_state["v"] = 2
    code_c, body_c, _ct, etag_c = local_api.cached_response(
        key, ttl_seconds=60, version_fn=version, builder=builder
    )
    assert calls["n"] == 2
    assert etag_c != etag_a


def test_cached_response_does_not_cache_errors(tmp_path: Path) -> None:
    key = f"/test/errors/{id(tmp_path)}"
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return 500, {"error": "boom"}, "application/json; charset=utf-8"

    code, _body, _ct, _etag = local_api.cached_response(
        key, ttl_seconds=60, version_fn=lambda: ("v",), builder=builder
    )
    assert code == 500
    # Second call should also go through the builder (no poisoning).
    local_api.cached_response(key, ttl_seconds=60, version_fn=lambda: ("v",), builder=builder)
    assert calls["n"] == 2


def test_build_worktrees_list_returns_primary(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    _write(repo_root / "README.md", "hi\n")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "initial")
    result = local_api.build_worktrees_list(repo_root)
    assert result["ok"] is True
    assert result["count"] >= 1
    paths = [w["path"] for w in result["worktrees"]]
    assert str(repo_root) in paths


def test_session_briefing_serves_compact_snapshot(tmp_path: Path) -> None:
    _setup_repo(tmp_path)
    # Write a STATUS.md that the briefing will parse.
    _write(
        tmp_path / "STATUS.md",
        "# status\n\n## TODO\n\n- [ ] finish alpha\n- [ ] finish beta\n\n"
        "## Blockers\n\n- slow CI\n",
    )
    briefing = local_api.build_session_briefing(tmp_path)
    assert set(briefing).issuperset(
        {"snapshot", "workspace", "services", "pipelines", "focus", "blockers", "next_reads"}
    )
    assert briefing["focus"][:2] == ["finish alpha", "finish beta"]
    assert briefing["blockers"] == ["slow CI"]

    # Compact drops next_reads, links, and the worktrees list.
    compact = local_api._compact_briefing(briefing)
    assert "next_reads" not in compact
    assert "links" not in compact
    assert "worktrees" not in compact["workspace"]
    assert compact["workspace"]["worktrees_total"] == briefing["workspace"]["worktrees_total"]


def test_serve_request_sets_etag_and_matches_on_replay(tmp_path: Path) -> None:
    _setup_repo(tmp_path)
    _write(
        tmp_path / "STATUS.md",
        "# status\n\n## TODO\n\n- [ ] task one\n",
    )
    code1, body1, _ct1, etag1 = local_api.serve_request(tmp_path, "/api/schema")
    assert code1 == 200
    assert etag1.startswith('W/"sha256:')
    # Replay should return the same bytes + same etag (cache hit).
    code2, body2, _ct2, etag2 = local_api.serve_request(tmp_path, "/api/schema")
    assert code2 == 200
    assert etag2 == etag1
    assert body1 == body2
    # And If-None-Match match semantics should accept it.
    assert local_api._match_etag(etag1, etag2)


def test_background_snapshot_exposes_freshness_metadata() -> None:
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"value": calls["n"]}

    snap = local_api.BackgroundSnapshot(
        key="test-snap-1",
        interval_seconds=60.0,
        builder=builder,
    )
    # Before any refresh runs.
    data, meta = snap.get()
    assert data is None
    assert meta["freshness_state"] == "refreshing"

    snap.refresh_blocking()
    data, meta = snap.get()
    assert data == {"value": 1}
    assert meta["freshness_state"] == "fresh"
    assert meta["refresh_error"] is None
    assert meta["refresh_duration_ms"] is not None
    assert meta["refresh_in_flight"] is False


def test_sqlite_version_key_detects_wal_only_write(tmp_path: Path) -> None:
    """Regression: PR #259 round 1 used PRAGMA data_version which is a
    per-connection counter and therefore unreliable across fresh
    connections. Version key must change on a WAL-mode write."""
    db_path = tmp_path / "wal.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.commit()
    conn.close()
    local_api._close_all_sqlite_version_connections()
    v1 = local_api._sqlite_version_key(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()
    v2 = local_api._sqlite_version_key(db_path)

    assert v1 != v2, "WAL-mode write must change the version key"


def test_sqlite_version_key_detects_same_size_write(tmp_path: Path) -> None:
    """Codex round-2 blocker: (mtime, size) missed same-size writes.
    The fix uses PRAGMA data_version on a persistent connection, which
    increments on every commit regardless of file-level changes.

    Write, then UPDATE a row in place so the file size is unchanged.
    Without a reliable detector, the version key would collide.
    """
    db_path = tmp_path / "same_size.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    local_api._close_all_sqlite_version_connections()
    size_before = db_path.stat().st_size
    v1 = local_api._sqlite_version_key(db_path)

    # In-place update: row count and stored int width are both unchanged.
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE t SET x = 2")
    conn.commit()
    conn.close()
    size_after = db_path.stat().st_size
    v2 = local_api._sqlite_version_key(db_path)

    # The whole point of this test is the "same size" case; prove it.
    assert size_before == size_after, (
        f"test presumption broken: size changed {size_before}->{size_after}"
    )
    assert v1 != v2, "in-place UPDATE must change the version key"


def test_sqlite_version_key_detects_db_replacement(tmp_path: Path) -> None:
    """Non-blocking polish from Codex round-3: if the DB file is
    REPLACED (different inode) rather than modified in place, the
    cached persistent connection would otherwise keep reporting the
    old counter until TTL rebuilt the cache. The inode check drops
    the stale handle so the first call after replacement gives a
    fresh, correct key.
    """
    db_path = tmp_path / "rotated.db"
    other = tmp_path / "other.db"

    # DB A — one row, version V_a.
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    local_api._close_all_sqlite_version_connections()
    v_a = local_api._sqlite_version_key(db_path)

    # DB B — different physical file, then rename over db_path.
    conn = sqlite3.connect(other)
    conn.execute("CREATE TABLE t (x INTEGER, y TEXT)")
    conn.execute("INSERT INTO t VALUES (42, 'b')")
    conn.execute("INSERT INTO t VALUES (43, 'bb')")
    conn.commit()
    conn.close()
    # Rename replaces the inode at db_path without going through
    # sqlite's own rewrite path.
    other.replace(db_path)

    v_b = local_api._sqlite_version_key(db_path)
    assert v_a != v_b, "DB replacement must change the version key"


def test_sqlite_version_key_stable_without_writes(tmp_path: Path) -> None:
    """Repeated calls with no intervening write must return the same key."""
    db_path = tmp_path / "stable.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    local_api._close_all_sqlite_version_connections()
    v1 = local_api._sqlite_version_key(db_path)
    v2 = local_api._sqlite_version_key(db_path)
    v3 = local_api._sqlite_version_key(db_path)
    assert v1 == v2 == v3


def test_cache_keyed_by_repo_root(tmp_path: Path) -> None:
    """Regression: PR #259 round 1 used process-global caches that
    ignored repo_root. Two repos hitting the same URL path would share
    a cache entry.
    """
    repo_a = tmp_path / "repo_a"
    repo_b = tmp_path / "repo_b"
    repo_a.mkdir()
    repo_b.mkdir()
    key_a = local_api._normalized_cache_key("/api/schema", {}, repo_root=repo_a)
    key_b = local_api._normalized_cache_key("/api/schema", {}, repo_root=repo_b)
    assert key_a != key_b
    # With no repo_root the key falls back to path only (backward-compat).
    assert local_api._normalized_cache_key("/api/schema", {}) == "/api/schema"


def test_status_md_cache_isolates_per_path(tmp_path: Path) -> None:
    """Regression: STATUS.md cache was process-global, one entry.
    Different repos' STATUS.md files must resolve independently.
    """
    status_a = tmp_path / "a" / "STATUS.md"
    status_b = tmp_path / "b" / "STATUS.md"
    status_a.parent.mkdir()
    status_b.parent.mkdir()
    status_a.write_text(
        "# a\n\n## TODO\n\n- [ ] task from A\n", encoding="utf-8"
    )
    status_b.write_text(
        "# b\n\n## TODO\n\n- [ ] task from B\n", encoding="utf-8"
    )
    data_a = local_api._parse_status_md(status_a)
    data_b = local_api._parse_status_md(status_b)
    assert data_a["focus"] == ["task from A"]
    assert data_b["focus"] == ["task from B"]


def test_background_snapshot_serializes_concurrent_builds() -> None:
    """Regression: the "single in-flight" guarantee required a build
    lock. refresh_blocking() called from one thread while the daemon
    thread also tries to refresh must not produce overlapping builders.

    Deterministic — no sleeps. An instrumented build lock signals when
    the second caller reaches lock contention, so the test proves that
    B actually attempted entry before A released (not just that B
    happened not to finish first).
    """
    import threading

    class _InstrumentedLock:
        """Substitute for ``BackgroundSnapshot._build_lock`` that records
        a ``waiter_entered`` event the second time ``acquire`` is called
        while the lock is held, so the test can synchronize on ``B is
        now waiting`` without sleeping."""

        def __init__(self) -> None:
            self._inner = threading.Lock()
            self.waiter_entered = threading.Event()
            self._acquire_attempts = 0
            self._counter_lock = threading.Lock()

        def acquire(self, timeout: float = -1.0) -> bool:
            with self._counter_lock:
                self._acquire_attempts += 1
                attempt = self._acquire_attempts
            if attempt >= 2 and self._inner.locked():
                # Signal BEFORE the blocking acquire so the driver can
                # release A after confirming B has reached contention.
                self.waiter_entered.set()
            if timeout < 0:
                self._inner.acquire()
                return True
            return self._inner.acquire(timeout=timeout)

        def release(self) -> None:
            self._inner.release()

    running_now = {"n": 0}
    max_concurrent = {"n": 0}
    release_builder = threading.Event()
    in_builder = threading.Event()
    counter_lock = threading.Lock()

    def slow_builder():
        with counter_lock:
            running_now["n"] += 1
            max_concurrent["n"] = max(max_concurrent["n"], running_now["n"])
        in_builder.set()
        # Park inside the builder until the test explicitly releases.
        release_builder.wait(timeout=5.0)
        with counter_lock:
            running_now["n"] -= 1
        return {"ok": True}

    snap = local_api.BackgroundSnapshot(
        key="concurrency-test",
        interval_seconds=60.0,
        builder=slow_builder,
    )
    instrumented = _InstrumentedLock()
    snap._build_lock = instrumented  # type: ignore[assignment]

    # Thread A enters the builder and parks there.
    t_a = threading.Thread(target=snap.refresh_blocking)
    t_a.start()
    assert in_builder.wait(timeout=3.0), "builder A never entered"

    # Thread B also attempts to acquire the build lock. It must block.
    t_b = threading.Thread(target=snap.refresh_blocking)
    t_b.start()
    assert instrumented.waiter_entered.wait(timeout=3.0), (
        "B did not reach lock contention before A released — test invalid"
    )

    # Release A; B proceeds into the builder sequentially.
    release_builder.set()
    t_a.join(timeout=3.0)
    t_b.join(timeout=3.0)
    assert not t_a.is_alive() and not t_b.is_alive()
    assert max_concurrent["n"] == 1, "two builders ran concurrently"


def test_refresh_blocking_honors_timeout() -> None:
    """refresh_blocking(timeout=...) must return False if the build
    lock cannot be acquired before the timeout elapses."""
    import threading

    release = threading.Event()
    in_builder = threading.Event()

    def slow_builder():
        in_builder.set()
        release.wait(timeout=3.0)
        return {"ok": True}

    snap = local_api.BackgroundSnapshot(
        key="timeout-test",
        interval_seconds=60.0,
        builder=slow_builder,
    )
    # Thread A holds the build lock.
    t_a = threading.Thread(target=snap.refresh_blocking)
    t_a.start()
    assert in_builder.wait(timeout=3.0)

    # Caller B asks with a small timeout. Lock is held; return False fast.
    ok = snap.refresh_blocking(timeout=0.05)
    assert ok is False, "timeout path must return False"

    release.set()
    t_a.join(timeout=3.0)
    # Once A releases, a follow-up call succeeds.
    assert snap.refresh_blocking(timeout=3.0) is True


def test_background_snapshot_reports_degraded_on_builder_error() -> None:
    def builder():
        raise RuntimeError("boom")

    snap = local_api.BackgroundSnapshot(
        key="test-snap-2",
        interval_seconds=60.0,
        builder=builder,
    )
    snap.refresh_blocking()
    data, meta = snap.get()
    assert data is None
    assert meta["freshness_state"] == "degraded"
    assert "RuntimeError: boom" in (meta["refresh_error"] or "")


def test_pipeline_leases_lists_active_only(tmp_path: Path) -> None:
    """Codex round-1 bug: we were using ms; the control-plane stores
    Unix epoch SECONDS. Everything below is in seconds."""
    module_key, _ = _setup_repo(tmp_path)
    now_s = 1_700_000_000  # Realistic seconds-since-epoch value.

    conn = sqlite3.connect(tmp_path / ".pipeline/v2.db")
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, "
        "leased_at, lease_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (module_key, "write", "leased", "codex", "lease-a", now_s - 1, now_s + 60),
    )
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, "
        "leased_at, lease_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("other/module-stale", "write", "leased", "claude", "lease-b",
         now_s - 10_000, now_s - 1),
    )
    conn.commit()
    conn.close()

    result = local_api.build_pipeline_leases(tmp_path, now_seconds=now_s)
    assert result["exists"] is True
    assert result["count"] == 1
    assert result["active"][0]["lease_id"] == "lease-a"
    assert result["active"][0]["seconds_to_expiry"] == 60


def test_pipeline_leases_returns_empty_when_db_missing(tmp_path: Path) -> None:
    result = local_api.build_pipeline_leases(tmp_path)
    assert result["exists"] is False
    assert result["count"] == 0
    assert result["active"] == []


def test_module_lease_reports_held_vs_free(tmp_path: Path) -> None:
    module_key, _ = _setup_repo(tmp_path)
    now_s = 1_700_000_000
    r = local_api.build_module_lease(tmp_path, module_key, now_seconds=now_s)
    assert r["held"] is False

    conn = sqlite3.connect(tmp_path / ".pipeline/v2.db")
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, "
        "leased_at, lease_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (module_key, "review", "leased", "gemini", "lease-x", now_s - 1, now_s + 120),
    )
    conn.commit()
    conn.close()
    r = local_api.build_module_lease(tmp_path, module_key, now_seconds=now_s)
    assert r["held"] is True
    assert r["lease"]["leased_by"] == "gemini"
    assert r["lease"]["seconds_to_expiry"] == 120


def test_pipeline_events_filters_and_limits(tmp_path: Path) -> None:
    module_key, _ = _setup_repo(tmp_path)
    conn = sqlite3.connect(tmp_path / ".pipeline/v2.db")
    for i in range(5):
        conn.execute(
            "INSERT INTO events (module_key, type, payload_json, at) VALUES (?, ?, ?, ?)",
            (module_key, f"type_{i}", f'{{"i":{i}}}', 1000 + i),
        )
    conn.execute(
        "INSERT INTO events (module_key, type, payload_json, at) VALUES (?, ?, ?, ?)",
        ("other/module", "x", "{}", 9999),
    )
    conn.commit()
    conn.close()

    scoped = local_api.build_pipeline_events(tmp_path, module_key=module_key, since_seconds=None, limit=3)
    assert scoped["count"] == 3
    assert all(e["module_key"] == module_key for e in scoped["events"])
    ids = [e["id"] for e in scoped["events"]]
    assert ids == sorted(ids, reverse=True)
    assert isinstance(scoped["events"][0]["payload_json"], dict)

    windowed = local_api.build_pipeline_events(tmp_path, module_key=module_key, since_seconds=1002, limit=10)
    ats = [e["at"] for e in windowed["events"]]
    assert all(a >= 1002 for a in ats)


def test_pipeline_stuck_catches_expired_and_silent_jobs_in_seconds(tmp_path: Path) -> None:
    """Bug-fix regression: Codex caught the ms-vs-seconds mismatch.
    Threshold is now honored in seconds against seconds-valued
    timestamps from the real control-plane."""
    module_key, _ = _setup_repo(tmp_path)
    now_s = 10_000
    conn = sqlite3.connect(tmp_path / ".pipeline/v2.db")
    # Expired lease -> stuck_leased
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, "
        "leased_at, lease_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("stuck/one", "write", "leased", "codex", "lex-1",
         now_s - 1_000, now_s - 10),
    )
    # In-flight with no recent event for current attempt -> stuck_in_state
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, leased_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("stuck/silent", "review", "running", "claude", "lex-silent", now_s - 10_000),
    )
    conn.execute(
        "INSERT INTO events (module_key, type, lease_id, payload_json, at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("stuck/silent", "attempt_started", "lex-silent", "{}", now_s - 10_000),
    )
    # Fresh in-flight -> not stuck (has recent event for its lease)
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, leased_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("fresh/one", "review", "running", "claude", "lex-fresh", now_s),
    )
    conn.execute(
        "INSERT INTO events (module_key, type, lease_id, payload_json, at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("fresh/one", "attempt_started", "lex-fresh", "{}", now_s - 10),
    )
    conn.commit()
    conn.close()

    r = local_api.build_pipeline_stuck(tmp_path, threshold_seconds=60, now_seconds=now_s)
    stuck_leased_keys = {j["module_key"] for j in r["stuck_leased"]}
    stuck_in_state_keys = {j["module_key"] for j in r["stuck_in_state"]}
    assert "stuck/one" in stuck_leased_keys
    assert "stuck/silent" in stuck_in_state_keys
    assert "fresh/one" not in stuck_in_state_keys


def test_pipeline_stuck_correlates_events_by_lease_id(tmp_path: Path) -> None:
    """Codex round-4 bug: correlating events by module_key alone let
    a fresh event from an EARLIER lease mask a hung current lease."""
    _setup_repo(tmp_path)
    now_s = 10_000
    conn = sqlite3.connect(tmp_path / ".pipeline/v2.db")
    # Current (hung) lease: running, no event for THIS lease_id.
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, leased_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("rolled/over", "write", "running", "claude", "current-lease", now_s - 10_000),
    )
    # Old event from a PREVIOUS lease for the same module — should NOT
    # make the current attempt look healthy.
    conn.execute(
        "INSERT INTO events (module_key, type, lease_id, payload_json, at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("rolled/over", "attempt_started", "previous-lease", "{}", now_s - 1),
    )
    conn.commit()
    conn.close()
    r = local_api.build_pipeline_stuck(tmp_path, threshold_seconds=60, now_seconds=now_s)
    assert any(j["module_key"] == "rolled/over" for j in r["stuck_in_state"])


def test_reviews_index_and_single(tmp_path: Path) -> None:
    reviews_dir = tmp_path / ".pipeline" / "reviews"
    reviews_dir.mkdir(parents=True)
    (reviews_dir / "cka__module-2.8-scheduler.md").write_text(
        "# Review\n\n## 2026-01-01 — WRITE\n\n**Writer**: gemini\n",
        encoding="utf-8",
    )
    (reviews_dir / "ztt__module-0.1.md").write_text("short", encoding="utf-8")

    index = local_api.build_reviews_index(tmp_path)
    assert index["exists"] is True
    assert index["count"] == 2
    keys = {r["module_key"] for r in index["reviews"]}
    assert "cka/module-2.8-scheduler" in keys
    assert "ztt/module-0.1" in keys

    single = local_api.build_module_reviews(tmp_path, "cka/module-2.8-scheduler")
    assert single is not None
    assert "**Writer**: gemini" in single["body"]
    assert single["truncated"] is False

    # Truncation path. ``size`` is the actual on-disk size (per Codex
    # round-4 polish: truncated responses must not lie about file
    # size); ``max_bytes`` carries the cap applied.
    big_content = "x" * 50_000
    (reviews_dir / "big__one.md").write_text(big_content, encoding="utf-8")
    trunc = local_api.build_module_reviews(tmp_path, "big/one", max_bytes=1000)
    assert trunc is not None
    assert trunc["truncated"] is True
    assert trunc["size"] == 50_000
    assert trunc["max_bytes"] == 1000
    assert trunc["body_size"] == 1000


def test_resolve_bridge_db_path_precedence(tmp_path: Path, monkeypatch) -> None:
    """Codex round-1 bug: we hardcoded .bridge/messages.db but the
    Python bridge default is .mcp/servers/message-broker/messages.db.
    Resolution must honor $AB_DB_PATH first, then fall through."""
    repo = tmp_path
    monkeypatch.delenv("AB_DB_PATH", raising=False)
    p = local_api._resolve_bridge_db_path(repo)
    assert p == repo / ".bridge" / "messages.db"

    mcp_path = repo / ".mcp" / "servers" / "message-broker" / "messages.db"
    mcp_path.parent.mkdir(parents=True)
    mcp_path.write_bytes(b"")
    assert local_api._resolve_bridge_db_path(repo) == mcp_path

    bridge_path = repo / ".bridge" / "messages.db"
    bridge_path.parent.mkdir(parents=True)
    bridge_path.write_bytes(b"")
    assert local_api._resolve_bridge_db_path(repo) == bridge_path

    override = tmp_path / "custom.db"
    override.write_bytes(b"")
    monkeypatch.setenv("AB_DB_PATH", str(override))
    assert local_api._resolve_bridge_db_path(repo) == override


def test_resolve_bridge_db_path_honors_nonexistent_override(
    tmp_path: Path, monkeypatch
) -> None:
    """Codex round-2 bug: $AB_DB_PATH must win even when the override
    file doesn't yet exist. Previously we only used it when present,
    silently reading the wrong DB on a fresh override."""
    repo = tmp_path
    bridge_path = repo / ".bridge" / "messages.db"
    bridge_path.parent.mkdir(parents=True)
    bridge_path.write_bytes(b"")
    not_yet_created = tmp_path / "future.db"
    monkeypatch.setenv("AB_DB_PATH", str(not_yet_created))
    resolved = local_api._resolve_bridge_db_path(repo)
    assert resolved == not_yet_created
    assert not resolved.exists()


def test_bridge_messages_filters_and_previews(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("AB_DB_PATH", raising=False)
    db_path = tmp_path / ".bridge" / "messages.db"
    db_path.parent.mkdir(parents=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE messages (
          id INTEGER PRIMARY KEY,
          task_id TEXT, from_llm TEXT, to_llm TEXT, message_type TEXT,
          content TEXT, data TEXT, timestamp TEXT, acknowledged INTEGER,
          status TEXT
        )
        """
    )
    long_content = "y" * 800
    for i, ts in enumerate(["2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", "2026-03-01T00:00:00Z"]):
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, timestamp, "
            "acknowledged, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"t{i}", "claude", "codex", "review", long_content, ts, 0, "sent"),
        )
    conn.commit()
    conn.close()

    all_ = local_api.build_bridge_messages(tmp_path, since=None, limit=10)
    assert all_["count"] == 3
    # Long content trimmed to preview.
    first = all_["messages"][0]
    assert "content" not in first  # replaced by preview
    assert first["content_full_length"] == 800
    assert first["content_preview"].endswith("(truncated)")

    since = local_api.build_bridge_messages(tmp_path, since="2026-02-01T00:00:00Z", limit=10)
    assert since["count"] == 2


def test_quality_scores_parses_audit_markdown(tmp_path: Path) -> None:
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """# Audit\n\n## All Scored Modules\n\n### Critical & High Priority\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| Alpha Beta | CKA | 55 | **1.3** | Critical | stub |\n"""
        """| Gamma Module | CKAD | 500 | **3.7** | Good | ok |\n"""
        """| Delta | KCNA | 74 | **1.7** | Critical | stub |\n""",
        encoding="utf-8",
    )
    # Reset the cache so this test doesn't see a stale parse from
    # another test's tmp_path.
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()

    r = local_api.build_quality_scores(tmp_path)
    assert r["exists"] is True
    assert r["count"] == 3
    assert r["critical_count"] == 2
    scores = {m["module"]: m for m in r["modules"]}
    assert scores["Alpha Beta"]["severity"] == "critical"
    assert scores["Gamma Module"]["severity"] == "good"


def _diag_codes(diagnostics: list[dict[str, object]]) -> set[str]:
    """Helper: extract the stable ``code`` field from a diagnostics list."""
    return {str(entry.get("code")) for entry in diagnostics if isinstance(entry, dict)}


def test_module_state_diagnostics_are_structured_dicts(tmp_path: Path) -> None:
    """Schema-tweak #263: diagnostics changed from ``list[str]`` to
    ``list[dict]`` with ``{severity, code, summary, source, next_action?}``.
    Agents switch on ``severity`` / ``code`` and drill in via
    ``next_action``, which the old string tags could not carry."""
    module_key, _ = _setup_repo(tmp_path)
    state = local_api.build_module_state(tmp_path, module_key)
    diagnostics = state.get("diagnostics")
    assert isinstance(diagnostics, list)
    for entry in diagnostics:
        assert isinstance(entry, dict)
        # Required fields.
        assert entry.get("severity") in {"info", "warn", "critical"}
        assert isinstance(entry.get("code"), str) and entry["code"]
        assert isinstance(entry.get("summary"), str) and entry["summary"]
        assert isinstance(entry.get("source"), str) and entry["source"]
        # next_action is optional but when present must be a string.
        if "next_action" in entry:
            assert isinstance(entry["next_action"], str)


def test_module_state_flags_missing_lab_and_ledger(tmp_path: Path) -> None:
    # Minimal repo: no lab, no fact ledger, no UK.
    repo = tmp_path
    _init_repo(repo)
    _write(
        repo / "src/content/docs/k8s/cka/module-X-stub.md",
        "---\ntitle: stub\n---\nbody\n",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    state = local_api.build_module_state(repo, "k8s/cka/module-X-stub")
    codes = _diag_codes(state["diagnostics"])
    assert "no_lab" in codes
    assert "no_fact_ledger" in codes
    assert "uk_translation_missing" in codes


def test_rubric_diagnostics_matches_by_track_and_number(tmp_path: Path) -> None:
    """Codex round-4 bug: rubric matching compared raw slugs like
    'module-2.8-scheduler-lifecycle-theory' to audit labels like
    'CKA 2.8: Scheduler Lifecycle Theory' and never matched."""
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """## All Scored Modules\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| CKA 2.8: Scheduler Lifecycle Theory | CKA | 55 | **1.3** | Critical | stub |\n""",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()

    # Build minimal EN file for the module under its real-world path.
    en = (
        tmp_path
        / "src/content/docs/k8s/cka/part2-workloads-scheduling/module-2.8-scheduler-lifecycle-theory.md"
    )
    _init_repo(tmp_path)
    _write(en, "---\ntitle: Scheduler\n---\nbody\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    state = local_api.build_module_state(
        tmp_path, "k8s/cka/part2-workloads-scheduling/module-2.8-scheduler-lifecycle-theory"
    )
    assert "rubric_critical" in _diag_codes(state["diagnostics"])


def test_rubric_diagnostics_matches_non_numbered_entry(tmp_path: Path) -> None:
    """Codex round-2 bug: audit entries like 'Platform: Systems Thinking'
    (no module number) were never matched. Now resolved via name-token
    overlap when ≥2 tokens are shared AND the track alias matches."""
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """## All Scored Modules\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| Platform: Systems Thinking | Platform Foundations | 820 | **4.6** | Excellent | gold |\n"""
        """| Prerequisites: GitOps | Modern DevOps | 543 | **2.9** | Medium | overloaded |\n""",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()

    _init_repo(tmp_path)
    en = tmp_path / "src/content/docs/platform/foundations/module-1-systems-thinking.md"
    _write(en, "---\ntitle: Systems Thinking\n---\nbody\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    # Severity is "excellent" so no rubric_* tag is expected. But the
    # match must have happened; verify by directly probing the helper.
    quality = local_api.build_quality_scores(tmp_path)
    sev = local_api._rubric_severity_for_module(
        "platform/foundations/module-1-systems-thinking",
        quality["modules"],
    )
    assert sev == "excellent"

    # Prerequisites: GitOps → "needs_work" (3.5 > 2.9 >= 2.5). Not
    # critical/poor, so no tag in diagnostics either; probe the helper.
    sev2 = local_api._rubric_severity_for_module(
        "prerequisites/modern-devops/module-5-gitops",
        quality["modules"],
    )
    assert sev2 == "needs_work"


def test_rubric_diagnostics_matches_via_label_prefix(tmp_path: Path) -> None:
    """Codex round-3 bug: the Track column is often a SUBtrack
    ('Workloads', 'AWS', 'Foundations'). The top-level track is in
    the Module label prefix ('CKA:', 'Platform:', 'Prerequisites:').
    The matcher must consult both."""
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """## All Scored Modules\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| CKA: Autoscaling | Workloads | 450 | **2.2** | Poor | dry |\n""",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()
    quality = local_api.build_quality_scores(tmp_path)
    sev = local_api._rubric_severity_for_module(
        "k8s/cka/part2-workloads-scheduling/module-6-autoscaling",
        quality["modules"],
    )
    # Track col is "Workloads" (no CKA alias) but the label prefix
    # carries "CKA:" — the matcher must see it.
    assert sev == "poor"


def test_rubric_diagnostics_cka_does_not_match_ckad(tmp_path: Path) -> None:
    """Codex round-3 bug: raw substring ``'cka' in 'CKAD'`` is True,
    letting a CKAD audit row attach to a CKA module path. Matcher
    must use word boundaries."""
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """## All Scored Modules\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| CKAD 3.5: API Deprecations | CKAD | 433 | **2.4** | Poor | reference |\n""",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()
    quality = local_api.build_quality_scores(tmp_path)
    sev = local_api._rubric_severity_for_module(
        "k8s/cka/part3-services-networking/module-3.5-gateway-api",
        quality["modules"],
    )
    assert sev is None  # CKA module must NOT pick up the CKAD row.

    # And the CKAD path DOES match.
    sev_ckad = local_api._rubric_severity_for_module(
        "k8s/ckad/module-3.5-api-deprecations",
        quality["modules"],
    )
    assert sev_ckad == "poor"


def test_rubric_diagnostics_track_only_overlap_is_not_a_match(tmp_path: Path) -> None:
    """Codex round-3 bug: overlap of ``{platform, sre}`` — both track
    tokens — must NOT match. Matcher requires ≥ 1 NON-track token in
    the overlap."""
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """## All Scored Modules\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| Platform: Site Reliability Engineering (SRE) | Platform | 400 | **2.2** | Poor | generic |\n""",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()
    quality = local_api.build_quality_scores(tmp_path)
    # A platform module whose name just says "sre basics" shouldn't
    # inherit the severity from a generic "Platform: ... SRE" row.
    sev = local_api._rubric_severity_for_module(
        "platform/foundations/module-1-sre-basics",
        quality["modules"],
    )
    assert sev is None


def test_rubric_diagnostics_unrecognized_track_never_matches(tmp_path: Path) -> None:
    """Codex round-2 bug: when the path's track wasn't in the alias
    table, matching silently became permissive and could attach a
    random rubric row. Now unknown tracks always return None."""
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """## All Scored Modules\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| CKA 2.8: Scheduler Lifecycle Theory | CKA | 55 | **1.3** | Critical | stub |\n""",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()
    quality = local_api.build_quality_scores(tmp_path)
    # Path track "exotic" is not in _TRACK_ALIASES. Must not match
    # ANY row, regardless of number overlap.
    sev = local_api._rubric_severity_for_module(
        "exotic/module-2.8-scheduler",
        quality["modules"],
    )
    assert sev is None


def test_rubric_diagnostics_no_false_match_for_different_track(tmp_path: Path) -> None:
    """A module path like k8s/kcna/module-2.8-... must not pick up a
    'CKA 2.8:' rubric entry (track disambiguation)."""
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir()
    audit.write_text(
        """## All Scored Modules\n\n"""
        """| Module | Track | Lines | Score | Action | Issue |\n"""
        """|---|---|---|---|---|---|\n"""
        """| CKA 2.8: Scheduler Lifecycle Theory | CKA | 55 | **1.3** | Critical | stub |\n""",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()

    en = tmp_path / "src/content/docs/k8s/kcna/module-2.8-something-unrelated.md"
    _init_repo(tmp_path)
    _write(en, "---\ntitle: KCNA\n---\nbody\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    state = local_api.build_module_state(tmp_path, "k8s/kcna/module-2.8-something-unrelated")
    assert "rubric_critical" not in _diag_codes(state["diagnostics"])


def test_query_sqlite_rows_propagates_schema_drift(tmp_path: Path) -> None:
    """Bug-fix regression: 'no such column' must NOT silently return
    empty — that was how the priority-column bug stayed hidden."""
    db_path = tmp_path / "schema.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE jobs (id INTEGER, module_key TEXT)")
    conn.commit()
    conn.close()
    import pytest as _pytest
    with _pytest.raises(sqlite3.OperationalError) as exc_info:
        local_api._query_sqlite_rows(db_path, "SELECT ghost_column FROM jobs")
    assert "no such column" in str(exc_info.value)


def test_query_sqlite_rows_tolerates_missing_table(tmp_path: Path) -> None:
    db_path = tmp_path / "missing_table.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE other (id INTEGER)")
    conn.commit()
    conn.close()
    result = local_api._query_sqlite_rows(db_path, "SELECT * FROM does_not_exist")
    assert result == []


def test_module_state_includes_orchestration_and_lease_inline(tmp_path: Path) -> None:
    """Schema-tweak #263: ``build_module_state`` folds in orchestration
    + lease so "why is X blocked" is one call, not three.

    The individual endpoints stay for callers that only want a slice,
    but the one-call path is the happy path for agent drill-down."""
    module_key, _ = _setup_repo(tmp_path)
    state = local_api.build_module_state(tmp_path, module_key)
    assert "orchestration" in state
    assert "lease" in state
    # Orchestration has the two sub-keys mirroring the dedicated endpoint.
    orch = state["orchestration"]
    assert "v2" in orch
    assert "translation_v2" in orch
    # Lease returns ``{held: bool, ...}``.
    assert "held" in state["lease"]


def test_module_state_orchestration_surfaces_pipeline_rejection(tmp_path: Path) -> None:
    """A pipeline-rejected module must get a ``pipeline_rejected``
    diagnostic so agents see the reason without fetching the events
    endpoint separately."""
    module_key, _ = _setup_repo(tmp_path)
    conn = sqlite3.connect(tmp_path / ".pipeline/v2.db")
    # Overwrite the fixture's first job with rejected state.
    conn.execute(
        "UPDATE jobs SET queue_state = ? WHERE module_key = ?",
        ("rejected", module_key),
    )
    # Add a second, newer rejected job so ORDER BY id DESC picks it.
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, model) "
        "VALUES (?, ?, ?, ?)",
        (module_key, "review", "rejected", "gemini"),
    )
    conn.commit()
    conn.close()
    state = local_api.build_module_state(tmp_path, module_key)
    codes = _diag_codes(state["diagnostics"])
    assert "pipeline_rejected" in codes


def test_briefing_has_actions_and_top_modules(tmp_path: Path) -> None:
    """Schema-tweak #263: briefing gains ``actions.active/blocked/next``
    and ``top_modules`` so Codex and Claude both see what to touch next."""
    _setup_repo(tmp_path)
    _write(
        tmp_path / "STATUS.md",
        "# status\n\n## TODO\n\n- [ ] task one\n",
    )
    import time as _time
    now_s = int(_time.time())
    conn = sqlite3.connect(tmp_path / ".pipeline/v2.db")
    conn.execute(
        "INSERT INTO jobs (module_key, phase, queue_state, leased_by, lease_id, "
        "leased_at, lease_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("active/module", "write", "leased", "codex", "l-live", now_s - 10, now_s + 300),
    )
    conn.commit()
    conn.close()
    briefing = local_api.build_session_briefing(tmp_path)
    assert "actions" in briefing
    # Codex round-2 request: ``active`` instead of ``now`` — that bucket
    # is read-only ("currently owned"), not "what I should touch".
    assert set(briefing["actions"].keys()) == {"active", "blocked", "next"}
    assert any("codex" in entry for entry in briefing["actions"]["active"])
    assert "top_modules" in briefing
    reasons = {m.get("reason") for m in briefing["top_modules"]}
    assert "active_lease" in reasons


def test_briefing_top_modules_covers_critical_quality(tmp_path: Path) -> None:
    """Codex round-2 gap: top_modules was missing critical_quality
    and ready_queue categories. Rubric-critical rows must surface as
    drillable entries, not just stringified actions.next lines."""
    _setup_repo(tmp_path)
    _write(tmp_path / "STATUS.md", "# s\n\n## TODO\n\n- [ ] x\n")
    audit = tmp_path / "docs" / "quality-audit-results.md"
    audit.parent.mkdir(exist_ok=True)
    audit.write_text(
        "## All Scored Modules\n\n"
        "| Module | Track | Lines | Score | Action | Issue |\n"
        "|---|---|---|---|---|---|\n"
        "| CKA 2.8: Bad Stub | CKA | 55 | **1.3** | Critical | stub |\n",
        encoding="utf-8",
    )
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()
    briefing = local_api.build_session_briefing(tmp_path)
    reasons = {m.get("reason") for m in briefing["top_modules"]}
    assert "critical_quality" in reasons
    # Critical rubric entries must point at the scores endpoint.
    cq = [m for m in briefing["top_modules"] if m.get("reason") == "critical_quality"]
    assert cq and cq[0]["endpoint"] == "/api/quality/scores"


def test_compact_briefing_keeps_actions_and_top_modules(tmp_path: Path) -> None:
    """Compact mode strips navigation aids but MUST keep the
    actionable fields — that's the whole point."""
    _setup_repo(tmp_path)
    _write(tmp_path / "STATUS.md", "# status\n\n## TODO\n\n- [ ] x\n")
    briefing = local_api.build_session_briefing(tmp_path)
    compact = local_api._compact_briefing(briefing)
    assert "actions" in compact
    assert "top_modules" in compact
    assert "next_reads" not in compact
    assert "links" not in compact


def test_worktrees_list_includes_dirty_counts(tmp_path: Path) -> None:
    """Schema-tweak #263: each worktree entry now carries a ``counts``
    dict so operators see which worktree is lively without shelling
    into each one."""
    repo = tmp_path
    _init_repo(repo)
    _write(repo / "README.md", "hi\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    _write(repo / "README.md", "hi\n\nmore\n")

    result = local_api.build_worktrees_list(repo)
    assert result["ok"] is True
    assert result["count"] >= 1
    first = result["worktrees"][0]
    assert "counts" in first
    counts = first["counts"]
    assert counts is not None
    assert counts["total"] >= 1
    assert counts["unstaged"] >= 1
    assert first["dirty"] is True


def test_worktree_counts_total_counts_paths_not_statuses(tmp_path: Path) -> None:
    """Codex round-2 bug: counts.total used staged+unstaged+untracked,
    which double-counts a file that is both staged AND unstaged. That
    made sibling-worktree counts incomparable with the primary
    worktree's. Fix: total is the number of unique paths reported by
    ``git status --porcelain=v1``."""
    repo = tmp_path
    _init_repo(repo)
    _write(repo / "README.md", "v1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")

    # Stage a change, then edit the same file again so git reports
    # both a staged and an unstaged modification for one path.
    _write(repo / "README.md", "v2\n")
    _git(repo, "add", "README.md")
    _write(repo / "README.md", "v3\n")

    counts = local_api._worktree_dirty_counts(repo)
    assert counts is not None
    assert counts["total"] == 1  # one path, not two
    assert counts["staged"] >= 1
    assert counts["unstaged"] >= 1


def test_worktree_counts_dirty_is_none_when_unreadable(tmp_path: Path) -> None:
    """Codex round-2 bug: a failed ``git status`` was folded into
    dirty=False, which is a false negative. Unreadable worktrees must
    surface as dirty=None so "unknown" and "clean" are distinguishable."""
    # Path that exists but isn't a git repo.
    non_repo = tmp_path / "not-a-repo"
    non_repo.mkdir()
    counts = local_api._worktree_dirty_counts(non_repo)
    assert counts is None


def test_schema_lists_phase_c_endpoints() -> None:
    schema = local_api.build_api_schema()
    paths = {e["path"] for e in schema["endpoints"]}
    for expected in (
        "/api/pipeline/leases",
        "/api/pipeline/v2/events",
        "/api/pipeline/v2/stuck",
        "/api/reviews",
        "/api/bridge/messages",
        "/api/quality/scores",
        "/api/module/{key}/lease",
    ):
        assert expected in paths, f"/api/schema missing {expected}"


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

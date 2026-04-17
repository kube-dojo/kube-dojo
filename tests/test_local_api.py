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
    connections. Version key must change on a WAL-mode write, measured
    across fresh lookups.
    """
    db_path = tmp_path / "wal.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.commit()
    conn.close()
    v1 = local_api._sqlite_version_key(db_path)

    # Open a separate connection, insert (this write lands in the WAL),
    # and close. The main .db file may not be touched if checkpoint has
    # not run yet.
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    # Force a small, quick write that is likely to stay in the WAL.
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()
    v2 = local_api._sqlite_version_key(db_path)

    assert v1 != v2, "WAL-mode write must change the version key"


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
    """
    import threading

    started = []
    running_now = {"n": 0}
    max_concurrent = {"n": 0}
    lock = threading.Lock()
    release = threading.Event()

    def slow_builder():
        with lock:
            running_now["n"] += 1
            max_concurrent["n"] = max(max_concurrent["n"], running_now["n"])
            started.append(True)
        # Block long enough for a second caller to race in.
        release.wait(timeout=1.0)
        with lock:
            running_now["n"] -= 1
        return {"iteration": len(started)}

    snap = local_api.BackgroundSnapshot(
        key="concurrency-test",
        interval_seconds=60.0,
        builder=slow_builder,
    )

    # Thread A: refresh_blocking holds the build lock.
    t_a = threading.Thread(target=snap.refresh_blocking, args=(5.0,))
    t_a.start()
    # Wait until A is inside the builder.
    for _ in range(50):
        with lock:
            if running_now["n"] >= 1:
                break
        import time as _t
        _t.sleep(0.01)
    # Thread B: concurrent refresh_blocking must BLOCK on the lock.
    t_b = threading.Thread(target=snap.refresh_blocking, args=(5.0,))
    t_b.start()
    # Give B a moment to attempt entry.
    import time as _t
    _t.sleep(0.05)
    # Release A, which lets B enter.
    release.set()
    t_a.join(timeout=3.0)
    t_b.join(timeout=3.0)
    assert not t_a.is_alive() and not t_b.is_alive()
    assert max_concurrent["n"] == 1, "two builders ran concurrently"


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

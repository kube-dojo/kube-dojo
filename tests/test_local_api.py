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

    status_code, summary = local_api.route_request(repo_root, "/api/status/summary")
    assert status_code == 200
    assert summary["zero_to_terminal"]["ready"]["english_production_bar"] is True

    status_code, module_state = local_api.route_request(
        repo_root, f"/api/module/{module_key}/state"
    )
    assert status_code == 200
    assert module_state["english_exists"] is True
    assert module_state["ukrainian_state"]["status"] == "synced"
    assert module_state["lab"]["state"]["severity"] == "clean"

    status_code, latest = local_api.route_request(
        repo_root, f"/api/module/{module_key}/orchestration/latest"
    )
    assert status_code == 200
    assert latest["v2"]["latest_job"]["phase"] == "review"
    assert latest["translation_v2"]["latest_event"]["type"] == "translation_verified"


def test_route_request_supports_translation_section_and_missing_db(tmp_path: Path) -> None:
    repo_root = tmp_path
    _setup_repo(repo_root)

    status_code, translation = local_api.route_request(
        repo_root,
        "/api/translation/v2/status?section=prerequisites/zero-to-terminal",
    )
    assert status_code == 200
    assert translation["freshness"]["section"] == "prerequisites/zero-to-terminal"

    (repo_root / ".pipeline" / "v2.db").unlink()
    status_code, payload = local_api.route_request(repo_root, "/api/pipeline/v2/status")
    assert status_code == 404
    assert payload["error"] == "missing_db"


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

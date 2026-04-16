from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "status.py"
    spec = importlib.util.spec_from_file_location("repo_status", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


repo_status = _load_module()
build_repo_status = repo_status.build_repo_status


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def _init_v2_db(path: Path) -> None:
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
            ("prerequisites/zero-to-terminal/module-0.1-alpha", "review", "codex", "completed"),
        )
        conn.execute(
            "INSERT INTO events (module_key, type, payload_json) VALUES (?, ?, ?)",
            ("prerequisites/zero-to-terminal/module-0.1-alpha", "done", "{}"),
        )
        conn.commit()
    finally:
        conn.close()


def _init_translation_v2_db(path: Path) -> None:
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
            ("prerequisites/zero-to-terminal/module-0.1-alpha", "write", "gemini", "completed"),
        )
        conn.execute(
            "INSERT INTO events (module_key, type, payload_json) VALUES (?, ?, ?)",
            ("prerequisites/zero-to-terminal/module-0.1-alpha", "translation_completed", "{}"),
        )
        conn.commit()
    finally:
        conn.close()


def test_build_repo_status_combines_v2_translations_labs_and_ztt(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)

    en_dir = repo_root / "src/content/docs/prerequisites/zero-to-terminal"
    uk_dir = repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal"
    fact_dir = repo_root / ".pipeline/fact-ledgers"

    en_path = en_dir / "module-0.1-alpha.md"
    _write(en_path, _module_frontmatter(lab_id="prereq-0.1-alpha"))
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "add english")
    en_commit = _git(repo_root, "log", "-1", "--format=%H", "--", str(en_path))

    _write(
        uk_dir / en_path.name,
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
    _write(fact_dir / "prerequisites__zero-to-terminal__module-0.1-alpha.json", "{}")
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
    _init_v2_db(repo_root / ".pipeline/v2.db")
    _init_translation_v2_db(repo_root / ".pipeline/translation_v2.db")

    status = build_repo_status(repo_root)

    assert status["english_modules"] == 1
    assert status["translations"]["synced"] == 1
    assert status["translations"]["sync_clean"] is True
    assert status["labs"]["done_clean"] == 1
    assert status["v2_pipeline"]["total_modules"] == 1
    assert status["translation_v2_pipeline"]["queue"]["total_modules"] == 1
    assert status["missing_modules"]["active_exact"]["missing"] > 0
    assert status["missing_modules"]["deferred"]["missing_min"] >= 0
    assert status["zero_to_terminal"]["ready"]["english_production_bar"] is True
    assert status["ownership"]["translation"] == "translation v2 queue + uk_sync worker"


def test_cli_json_output(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    _write(
        repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.1-alpha.md",
        _module_frontmatter(),
    )
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "add english")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/status.py",
            "--json",
            "--repo-root",
            str(repo_root),
        ],
        cwd="/Users/krisztiankoos/projects/kubedojo",
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    assert data["english_modules"] == 1
    assert data["translations"]["missing"] == 1
    assert "missing_modules" in data

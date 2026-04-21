from __future__ import annotations

import importlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "translation_v2.py"
    spec = importlib.util.spec_from_file_location("translation_v2", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


translation_v2 = _load_module()
status_script = importlib.import_module("status")


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


def _en_module(title: str = "English Title") -> str:
    return "\n".join(["---", f'title: "{title}"', "---", "", "## Body", "", "English body."])


def _uk_module(*, en_commit: str, en_file: str, title: str = "Український заголовок") -> str:
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            f'en_commit: "{en_commit}"',
            f'en_file: "{en_file}"',
            "---",
            "",
            "## Тіло",
            "",
            "Український текст.",
        ]
    )


def _module_with_metadata(*, title: str, body: str, metadata: dict[str, Any] | None = None) -> str:
    lines = ["---", f'title: "{title}"']
    for key, value in (metadata or {}).items():
        if isinstance(value, list):
            rendered = "[" + ", ".join(json.dumps(item, ensure_ascii=False) for item in value) + "]"
            lines.append(f"{key}: {rendered}")
        else:
            lines.append(f'{key}: {json.dumps(value, ensure_ascii=False)}')
    lines.extend(["---", "", "## Body", "", body])
    return "\n".join(lines)


def _init_translation_status_db(db_path: Path, *entries: tuple[str, str]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE jobs (id INTEGER PRIMARY KEY, module_key TEXT NOT NULL, phase TEXT NOT NULL, model TEXT, queue_state TEXT NOT NULL);
            CREATE TABLE events (id INTEGER PRIMARY KEY, module_key TEXT NOT NULL, type TEXT NOT NULL, payload_json TEXT DEFAULT '{}');
            """
        )
        for module_key, event_type in entries:
            conn.execute(
                "INSERT INTO jobs (module_key, phase, model, queue_state) VALUES (?, ?, ?, ?)",
                (module_key, "review", translation_v2.VERIFY_MODEL, "completed"),
            )
            conn.execute(
                "INSERT INTO events (module_key, type, payload_json) VALUES (?, ?, ?)",
                (module_key, event_type, "{}"),
            )
        conn.commit()
    finally:
        conn.close()


def _init_translation_status_db_with_jobs(
    db_path: Path,
    *,
    jobs: list[tuple[str, str, str]],
    events: list[tuple[str, str]],
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE jobs (id INTEGER PRIMARY KEY, module_key TEXT NOT NULL, phase TEXT NOT NULL, model TEXT, queue_state TEXT NOT NULL);
            CREATE TABLE events (id INTEGER PRIMARY KEY, module_key TEXT NOT NULL, type TEXT NOT NULL, payload_json TEXT DEFAULT '{}');
            """
        )
        for module_key, phase, queue_state in jobs:
            conn.execute(
                "INSERT INTO jobs (module_key, phase, model, queue_state) VALUES (?, ?, ?, ?)",
                (module_key, phase, translation_v2.TRANSLATE_MODEL, queue_state),
            )
        for module_key, event_type in events:
            conn.execute(
                "INSERT INTO events (module_key, type, payload_json) VALUES (?, ?, ?)",
                (module_key, event_type, "{}"),
            )
        conn.commit()
    finally:
        conn.close()


def _verify_with_metadata(
    repo_root: Path, module_key: str, *, uk_overrides: dict[str, Any] | None = None
) -> tuple[bool, dict[str, Any]]:
    metadata = {"complexity": "MEDIUM", "time_to_complete": "45 min", "prerequisites": ["module-0.1-alpha"]}
    en_path = repo_root / "src/content/docs" / f"{module_key}.md"
    _write(en_path, _module_with_metadata(title="English Title", body="English body.", metadata=metadata))
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english")
    uk_metadata = {
        **metadata,
        "en_commit": _git(repo_root, "log", "-1", "--format=%H", "--", str(en_path)),
        "en_file": en_path.relative_to(repo_root).as_posix(),
        **(uk_overrides or {}),
    }
    _write(
        repo_root / "src/content/docs/uk" / f"{module_key}.md",
        _module_with_metadata(title="Український заголовок", body="Український текст.", metadata=uk_metadata),
    )
    return translation_v2._verify_translation(repo_root, module_key)


def test_detect_module_state_marks_commit_drift_stale(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    en_path = repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.1-alpha.md"
    _write(en_path, _en_module())
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english")
    old_commit = _git(repo_root, "log", "-1", "--format=%H", "--", str(en_path))

    uk_path = repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal/module-0.1-alpha.md"
    _write(
        uk_path,
        _uk_module(
            en_commit=old_commit,
            en_file=en_path.relative_to(repo_root).as_posix(),
        ),
    )
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "ukrainian")

    _write(en_path, _en_module(title="English Title v2"))
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english update")

    state = translation_v2.detect_module_state(
        repo_root, "prerequisites/zero-to-terminal/module-0.1-alpha"
    )
    assert state["status"] == "stale"
    assert "stale_commit" in state["issues"]


def test_enqueue_translation_targets_respects_limit_and_skips_synced(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    base = repo_root / "src/content/docs/prerequisites/zero-to-terminal"
    mod1 = base / "module-0.1-alpha.md"
    mod2 = base / "module-0.2-beta.md"
    _write(mod1, _en_module())
    _write(mod2, _en_module())
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english")
    commit1 = _git(repo_root, "log", "-1", "--format=%H", "--", str(mod1))
    commit2 = _git(repo_root, "log", "-1", "--format=%H", "--", str(mod2))

    _write(
        repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal/module-0.1-alpha.md",
        _uk_module(
            en_commit=commit1,
            en_file=mod1.relative_to(repo_root).as_posix(),
        ),
    )
    _write(
        repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal/module-0.2-beta.md",
        _uk_module(
            en_commit=commit2,
            en_file=mod2.relative_to(repo_root).as_posix(),
        ),
    )
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "ukrainian")

    _write(mod2, _en_module(title="Beta v2"))
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "beta update")

    db_path = repo_root / ".pipeline/translation_v2.db"
    cp = translation_v2.ControlPlane(repo_root=repo_root, db_path=db_path)
    enqueued = translation_v2.enqueue_translation_targets(
        cp,
        section="prerequisites/zero-to-terminal",
        limit=1,
    )

    assert enqueued == ["prerequisites/zero-to-terminal/module-0.2-beta"]
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT module_key, phase, queue_state FROM jobs").fetchall()
    finally:
        conn.close()
    assert rows == [("prerequisites/zero-to-terminal/module-0.2-beta", "write", "pending")]


def test_translation_worker_completes_missing_module(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    en_path = repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.3-gamma.md"
    _write(en_path, _en_module())
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english")

    db_path = repo_root / ".pipeline/translation_v2.db"
    cp = translation_v2.ControlPlane(repo_root=repo_root, db_path=db_path)
    cp.enqueue(
        "prerequisites/zero-to-terminal/module-0.3-gamma",
        phase="write",
        model=translation_v2.TRANSLATE_MODEL,
    )

    def fake_translate(en_file: Path) -> bool:
        module_key = translation_v2._module_key_for_en_path(repo_root, en_file)
        uk_path = translation_v2._uk_path_for_module_key(repo_root, module_key)
        _write(
            uk_path,
            _uk_module(
                en_commit=translation_v2._git_head_for_file(repo_root, en_file),
                en_file=en_file.relative_to(repo_root).as_posix(),
            ),
        )
        return True

    worker = translation_v2.TranslationWorker(
        cp,
        translate_new_fn=fake_translate,
        fix_fn=lambda *_args, **_kwargs: True,
    )
    outcome = worker.run_once()

    assert outcome.status == "queued_for_verify"
    state = translation_v2.detect_module_state(
        repo_root, "prerequisites/zero-to-terminal/module-0.3-gamma"
    )
    assert state["status"] == "synced"

    verify = translation_v2.VerifyWorker(cp)
    verify_outcome = verify.run_once()
    assert verify_outcome.status == "completed"

    report = translation_v2.build_status(repo_root, db_path=db_path, section="prerequisites/zero-to-terminal")
    assert report["queue"]["counts"]["done"] == 1


def test_verify_worker_requeues_write_on_quality_failure(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    en_path = repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.4-delta.md"
    _write(en_path, _en_module())
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english")
    en_commit = _git(repo_root, "log", "-1", "--format=%H", "--", str(en_path))

    uk_path = repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal/module-0.4-delta.md"
    _write(
        uk_path,
        "\n".join(
            [
                "---",
                'title: "Поганий переклад"',
                f'en_commit: "{en_commit}"',
                f'en_file: "{en_path.relative_to(repo_root).as_posix()}"',
                "---",
                "",
                "самий",
            ]
        ),
    )

    db_path = repo_root / ".pipeline/translation_v2.db"
    cp = translation_v2.ControlPlane(repo_root=repo_root, db_path=db_path)
    cp.enqueue(
        "prerequisites/zero-to-terminal/module-0.4-delta",
        phase="review",
        model=translation_v2.VERIFY_MODEL,
    )
    cp.emit_event(
        "translation_write_started",
        module_key="prerequisites/zero-to-terminal/module-0.4-delta",
        payload={"phase": "write"},
    )

    verify = translation_v2.VerifyWorker(cp)
    outcome = verify.run_once()

    assert outcome.status == "retry_scheduled"
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT phase, queue_state FROM jobs WHERE module_key = ? ORDER BY id ASC",
            ("prerequisites/zero-to-terminal/module-0.4-delta",),
        ).fetchall()
    finally:
        conn.close()
    assert rows == [("review", "completed"), ("write", "pending")]


def test_build_status_treats_recovered_module_as_done(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    en_path = repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.5-epsilon.md"
    _write(en_path, _en_module())
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english")
    en_commit = _git(repo_root, "log", "-1", "--format=%H", "--", str(en_path))
    _write(
        repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal/module-0.5-epsilon.md",
        _uk_module(
            en_commit=en_commit,
            en_file=en_path.relative_to(repo_root).as_posix(),
        ),
    )

    db_path = repo_root / ".pipeline/translation_v2.db"
    cp = translation_v2.ControlPlane(repo_root=repo_root, db_path=db_path)
    cp.enqueue(
        "prerequisites/zero-to-terminal/module-0.5-epsilon",
        phase="review",
        model=translation_v2.VERIFY_MODEL,
    )
    verify = translation_v2.VerifyWorker(cp)
    verify.run_once()

    report = translation_v2.build_status(repo_root, db_path=db_path, section="prerequisites/zero-to-terminal")
    assert report["queue"]["counts"]["done"] == 1
    assert report["queue"]["counts"]["dead_letter"] == 0


def test_translation_v2_status_reports_per_track_done_and_dead_letter(tmp_path: Path) -> None:
    db_path = tmp_path / ".pipeline/translation_v2.db"
    _init_translation_status_db(
        db_path,
        ("prerequisites/zero-to-terminal/module-0.1-alpha", "translation_verified"),
        ("linux/shell/module-1.1-alpha", "module_dead_lettered"),
    )
    report = status_script._enrich_translation_v2_with_per_track({"queue": translation_v2._build_translation_queue_status(db_path)})
    by_track = {item["slug"]: item for item in report["queue"]["per_track"]}
    assert by_track["prerequisites"]["modules"]["done"] == ["prerequisites/zero-to-terminal/module-0.1-alpha"]
    assert by_track["linux"]["modules"]["dead_letter"] == ["linux/shell/module-1.1-alpha"]


def test_translation_v2_status_exposes_in_progress_modules_per_track(tmp_path: Path) -> None:
    db_path = tmp_path / ".pipeline/translation_v2.db"
    _init_translation_status_db_with_jobs(
        db_path,
        jobs=[
            ("prerequisites/zero-to-terminal/module-0.1-alpha", "write", "leased"),
            ("linux/shell/module-1.1-alpha", "review", "pending"),
        ],
        events=[
            ("prerequisites/zero-to-terminal/module-0.1-alpha", "translation_write_started"),
            ("linux/shell/module-1.1-alpha", "translation_written"),
        ],
    )

    queue = translation_v2._build_translation_queue_status(db_path)
    assert queue["counts"]["in_progress"] == 1
    assert queue["in_progress"] == ["prerequisites/zero-to-terminal/module-0.1-alpha"]

    report = status_script._enrich_translation_v2_with_per_track({"queue": queue})
    by_track = {item["slug"]: item for item in report["queue"]["per_track"]}
    assert by_track["prerequisites"]["modules"]["in_progress"] == [
        "prerequisites/zero-to-terminal/module-0.1-alpha"
    ]


def test_translation_v2_freshness_rollup_is_per_track_not_global(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    prereq_en = repo_root / "src/content/docs/prerequisites/zero-to-terminal/module-0.1-alpha.md"
    linux_en = repo_root / "src/content/docs/linux/shell/module-1.1-alpha.md"
    _write(prereq_en, _en_module())
    _write(linux_en, _en_module(title="Linux Alpha"))
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "english")
    prereq_commit = _git(repo_root, "log", "-1", "--format=%H", "--", str(prereq_en))
    linux_old_commit = _git(repo_root, "log", "-1", "--format=%H", "--", str(linux_en))

    _write(
        repo_root / "src/content/docs/uk/prerequisites/zero-to-terminal/module-0.1-alpha.md",
        _uk_module(en_commit=prereq_commit, en_file=prereq_en.relative_to(repo_root).as_posix()),
    )
    _write(
        repo_root / "src/content/docs/uk/linux/shell/module-1.1-alpha.md",
        _uk_module(en_commit=linux_old_commit, en_file=linux_en.relative_to(repo_root).as_posix()),
    )
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "ukrainian")

    _write(linux_en, _en_module(title="Linux Alpha v2"))
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "linux update")

    db_path = repo_root / ".pipeline/translation_v2.db"
    _init_translation_status_db(
        db_path,
        ("prerequisites/zero-to-terminal/module-0.1-alpha", "translation_verified"),
        ("linux/shell/module-1.1-alpha", "module_dead_lettered"),
    )

    report = translation_v2.build_status(repo_root, db_path=db_path)
    enriched = status_script._enrich_translation_v2_with_per_track(report)
    by_track = {item["slug"]: item for item in enriched["queue"]["per_track"]}

    assert by_track["prerequisites"]["freshness"] == {
        "up_to_date_count": 1,
        "stale_count": 0,
        "missing_count": 0,
        "dead_letter_count": 0,
    }
    assert by_track["linux"]["freshness"] == {
        "up_to_date_count": 0,
        "stale_count": 1,
        "missing_count": 0,
        "dead_letter_count": 1,
    }


def test_verify_translation_fails_on_lab_metadata_drift(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    verified, details = _verify_with_metadata(
        repo_root,
        "prerequisites/zero-to-terminal/module-0.6-zeta",
        uk_overrides={"complexity": "QUICK"},
    )

    assert verified is False
    assert "lab_metadata_mismatch:complexity" in details["issues"]
    assert details["lab_metadata_mismatches"] == ["complexity"]


def test_verify_translation_passes_on_lab_metadata_parity(tmp_path: Path) -> None:
    repo_root = tmp_path
    _init_repo(repo_root)
    verified, details = _verify_with_metadata(
        repo_root,
        "prerequisites/zero-to-terminal/module-0.7-eta",
    )

    assert verified is True
    assert "lab_metadata_mismatches" not in details

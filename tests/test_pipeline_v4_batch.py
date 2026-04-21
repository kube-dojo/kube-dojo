from __future__ import annotations

import sqlite3
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import pipeline_v4  # noqa: E402
import pipeline_v4_batch  # noqa: E402


def _patch_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    db_path = tmp_path / ".pipeline" / "v2.db"
    monkeypatch.setattr(pipeline_v4_batch, "DB_PATH", db_path)
    return db_path


def _expire_lease(db_path: Path, module_key: str) -> None:
    """Manually roll the lease expiry back so acquire sees it as stale."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE v4_batch_leases SET expires_at = 0 WHERE module_key = ?",
            (module_key,),
        )
        conn.commit()
    finally:
        conn.close()


def _lease_row(db_path: Path, module_key: str) -> sqlite3.Row | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            "SELECT * FROM v4_batch_leases WHERE module_key = ?",
            (module_key,),
        ).fetchone()
    finally:
        conn.close()


def test_acquire_lease_first_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_db(monkeypatch, tmp_path)
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-1", 60) is True
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-2", 60) is False


def test_acquire_after_expiry_succeeds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = _patch_db(monkeypatch, tmp_path)
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-1", 60) is True
    _expire_lease(db_path, "ai/foo/module-1")
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-2", 60) is True
    row = _lease_row(db_path, "ai/foo/module-1")
    assert row is not None
    assert row["worker_id"] == "w-2"


def test_complete_then_reacquire(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = _patch_db(monkeypatch, tmp_path)
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-1", 60) is True
    pipeline_v4_batch.complete_lease("ai/foo/module-1", "w-1", "clean")
    row = _lease_row(db_path, "ai/foo/module-1")
    assert row is not None and row["outcome"] == "clean"
    # Completed leases should not block a new acquire.
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-2", 60) is True
    row = _lease_row(db_path, "ai/foo/module-1")
    assert row is not None
    assert row["worker_id"] == "w-2"
    assert row["outcome"] is None


def test_release_lets_other_acquire(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-1", 60) is True
    pipeline_v4_batch.release_lease("ai/foo/module-1", "w-1")
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-2", 60) is True


def test_release_on_wrong_worker_is_noop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-1", 60) is True
    pipeline_v4_batch.release_lease("ai/foo/module-1", "intruder")
    assert pipeline_v4_batch.acquire_lease("ai/foo/module-1", "w-2", 60) is False


def _quality_payload(modules: list[dict[str, object]]) -> dict[str, object]:
    return {"modules": modules}


def test_select_candidates_filters_by_track_and_score(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    payload = _quality_payload(
        [
            {"path": "ai/foo/module-1.md", "score": 2.1, "primary_issue": "thin"},
            {"path": "ai/foo/module-2.md", "score": 3.8, "primary_issue": "no_quiz"},
            {"path": "ai/foo/module-3.md", "score": 4.5, "primary_issue": ""},
            {"path": "k8s/cka/module-1.md", "score": 1.5, "primary_issue": "thin"},
            {"path": "ai/bar/module-1.md", "score": 3.0, "primary_issue": "no_exercise"},
        ]
    )
    cands = pipeline_v4_batch.select_candidates(
        track="/ai",
        quality_fetch=lambda root: payload,
    )
    assert [c.module_key for c in cands] == [
        "ai/foo/module-1",
        "ai/bar/module-1",
        "ai/foo/module-2",
    ]


def test_select_candidates_applies_limit_and_min_score(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    payload = _quality_payload(
        [
            {"path": "ai/a.md", "score": 1.0, "primary_issue": "thin"},
            {"path": "ai/b.md", "score": 2.0, "primary_issue": "thin"},
            {"path": "ai/c.md", "score": 3.0, "primary_issue": "thin"},
            {"path": "ai/d.md", "score": 3.5, "primary_issue": "thin"},
        ]
    )
    cands = pipeline_v4_batch.select_candidates(
        limit=2,
        min_score=2.0,
        quality_fetch=lambda root: payload,
    )
    assert [c.module_key for c in cands] == ["ai/b", "ai/c"]


def _canned_result(
    module_key: str,
    *,
    outcome: str = "clean",
    score_before: float = 2.0,
    score_after: float = 4.2,
    retry_count: int = 0,
    delay: float = 0.0,
) -> "pipeline_v4.PipelineV4Result":
    if delay:
        time.sleep(delay)
    return pipeline_v4.PipelineV4Result(
        module_key=module_key,
        started_at="2026-04-21T00:00:00+00:00",
        finished_at="2026-04-21T00:00:01+00:00",
        stage_reached="DONE",
        outcome=outcome,
        reason="",
        score_before=score_before,
        score_after=score_after,
        gaps_before=["thin"],
        gaps_after=[],
        retry_count=retry_count,
        citation_v3_exit=0,
        events=[],
    )


def test_run_batch_happy_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    payload = _quality_payload(
        [
            {"path": "ai/a.md", "score": 2.0, "primary_issue": "thin"},
            {"path": "ai/b.md", "score": 2.5, "primary_issue": "thin"},
        ]
    )
    runs: list[tuple[str, bool, bool]] = []

    def _runner(module_key: str, **kwargs):
        runs.append((module_key, kwargs["dry_run"], kwargs["skip_citation"]))
        return _canned_result(module_key, score_after=4.2)

    emitted: list[dict[str, object]] = []
    summary = pipeline_v4_batch.run_batch(
        track="/ai",
        workers=2,
        dry_run=True,
        skip_citation=True,
        quality_fetch=lambda root: payload,
        runner=_runner,
        emit=emitted.append,
    )

    errors = [e for e in emitted if isinstance(e, dict) and e.get("outcome") == "error"]
    assert not errors, f"unexpected errors in batch: {errors}"
    assert summary["processed"] == 2
    assert summary["by_outcome"] == {"clean": 2}
    # (4.2-2.0) + (4.2-2.5) = 2.2 + 1.7 = 3.9
    assert round(summary["score_delta_total"], 1) == 3.9
    assert {r[0] for r in runs} == {"ai/a", "ai/b"}
    assert all(r[1] is True and r[2] is True for r in runs)
    # Results stream before summary.
    assert emitted[-1] == {"summary": summary}


def test_workers_clamped_to_max(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--workers 8 must clamp to MAX_WORKERS and emit a stderr warning.
    Above the cap the expected behavior is Gemini 429s, so enforce
    rather than letting the caller shoot themselves in the foot."""
    _patch_db(monkeypatch, tmp_path)
    observed: list[int] = []
    live = 0
    max_live = 0
    import threading as _threading
    lock = _threading.Lock()

    def _runner(module_key: str, **kwargs):
        nonlocal live, max_live
        with lock:
            live += 1
            max_live = max(max_live, live)
            observed.append(live)
        try:
            time.sleep(0.05)
            return _canned_result(module_key)
        finally:
            with lock:
                live -= 1

    payload = _quality_payload(
        [{"path": f"ai/m-{i}.md", "score": 2.0, "primary_issue": "thin"} for i in range(6)]
    )
    pipeline_v4_batch.run_batch(
        workers=8,
        quality_fetch=lambda root: payload,
        runner=_runner,
        emit=lambda _p: None,
    )
    err = capsys.readouterr().err
    assert "clamping" in err, f"expected clamp warning on stderr, got: {err}"
    assert max_live <= pipeline_v4_batch.MAX_WORKERS, (
        f"workers clamp broken: max_live={max_live} but MAX_WORKERS="
        f"{pipeline_v4_batch.MAX_WORKERS}"
    )


def test_run_batch_runs_in_parallel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    payload = _quality_payload(
        [
            {"path": f"ai/m-{i}.md", "score": 2.0, "primary_issue": "thin"}
            for i in range(4)
        ]
    )
    live = 0
    max_live = 0
    lock = threading.Lock()

    def _runner(module_key: str, **kwargs):
        nonlocal live, max_live
        with lock:
            live += 1
            max_live = max(max_live, live)
        try:
            time.sleep(0.05)
            return _canned_result(module_key)
        finally:
            with lock:
                live -= 1

    summary = pipeline_v4_batch.run_batch(
        workers=4,
        quality_fetch=lambda root: payload,
        runner=_runner,
        emit=lambda _p: None,
    )
    assert summary["processed"] == 4
    assert max_live >= 2, f"expected parallel execution but max_live was {max_live}"


def test_run_batch_records_error_and_releases_lease(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = _patch_db(monkeypatch, tmp_path)
    payload = _quality_payload(
        [{"path": "ai/broken.md", "score": 2.0, "primary_issue": "thin"}]
    )

    def _runner(module_key: str, **kwargs):
        raise RuntimeError("boom")

    summary = pipeline_v4_batch.run_batch(
        workers=1,
        quality_fetch=lambda root: payload,
        runner=_runner,
        emit=lambda _p: None,
    )
    assert summary["by_outcome"] == {"error": 1}
    # Lease should have been released on error so a retry can pick it up.
    assert pipeline_v4_batch.acquire_lease("ai/broken", "retry-worker", 60) is True
    # Previously released lease row was replaced by the retry acquire.
    row = _lease_row(db_path, "ai/broken")
    assert row is not None
    assert row["worker_id"] == "retry-worker"


def test_run_batch_skips_locked_module(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    # Simulate another batch holding the lease.
    assert pipeline_v4_batch.acquire_lease("ai/locked", "other-worker", 3600) is True

    payload = _quality_payload(
        [{"path": "ai/locked.md", "score": 2.0, "primary_issue": "thin"}]
    )
    called: list[str] = []

    def _runner(module_key: str, **kwargs):
        called.append(module_key)
        return _canned_result(module_key)

    summary = pipeline_v4_batch.run_batch(
        workers=1,
        quality_fetch=lambda root: payload,
        runner=_runner,
        emit=lambda _p: None,
    )
    assert called == [], "runner should not be invoked when lease is held elsewhere"
    assert summary["by_outcome"] == {"skipped_locked": 1}


def test_run_batch_no_candidates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)
    summary = pipeline_v4_batch.run_batch(
        quality_fetch=lambda root: _quality_payload([]),
        emit=lambda _p: None,
    )
    assert summary["processed"] == 0
    assert summary["reason"] == "no_candidates"


def test_cli_exit_code_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_db(monkeypatch, tmp_path)

    def _fake_run_batch(**kwargs):
        return {"processed": 1, "by_outcome": {"clean": 1}}

    monkeypatch.setattr(pipeline_v4_batch, "run_batch", _fake_run_batch)
    assert pipeline_v4_batch.main(["--limit", "1"]) == 0


def test_cli_exit_code_failure_on_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_db(monkeypatch, tmp_path)

    def _fake_run_batch(**kwargs):
        return {"processed": 1, "by_outcome": {"error": 1}}

    monkeypatch.setattr(pipeline_v4_batch, "run_batch", _fake_run_batch)
    assert pipeline_v4_batch.main(["--limit", "1"]) == 1

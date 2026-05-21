from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from scripts.calibration import report, run_cell, schema, score_cell
from scripts.calibration.run_cell import DispatchResult

RUN_DATE = "2026-05-21"
CODE_REVIEW_RESPONSE = (
    ".github/workflows/security.yml:10 security -- zizmor lacks "
    "--strict-collection. .github/workflows/security.yml:11 correctness -- "
    "scan scope misses .github/actions reusable actions. "
    ".github/dependabot.yml:6 correctness -- missing cooldown default-days. "
    ".github/workflows/security.yml:8 security -- pip install zizmor is unpinned."
)


def _run_cell_args(db_path: Path, output_root: Path, *extra: str) -> list[str]:
    return [
        "--lane",
        "code-review",
        "--canonical-string",
        "gpt-5.3-codex-spark",
        "--fixture-id",
        "pr-1333-security-yaml",
        "--run-date",
        RUN_DATE,
        "--db-path",
        str(db_path),
        "--output-root",
        str(output_root),
        "--timeout-s",
        "1",
        *extra,
    ]


def _install_fake_run_cell(monkeypatch) -> None:
    original = run_cell.run_cell

    def fake_dispatch(model, prompt, cwd, timeout_s):
        return DispatchResult(
            response=CODE_REVIEW_RESPONSE,
            task_id=f"fake-{model.canonical_string}",
            latency_s=0.01,
        )

    def fake_run_cell(**kwargs):
        return original(**kwargs, dispatch_fn=fake_dispatch)

    monkeypatch.setattr(run_cell, "run_cell", fake_run_cell)


def _latest_scored_at(db_path: Path) -> str:
    with schema.connect(db_path) as conn:
        row = conn.execute("SELECT MAX(scored_at) AS scored_at FROM scores").fetchone()
    assert row is not None
    return str(row["scored_at"])


def _score_count(db_path: Path) -> int:
    with schema.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM scores").fetchone()
    assert row is not None
    return int(row["count"])


def _only_cell_id(db_path: Path) -> str:
    with schema.connect(db_path) as conn:
        rows = conn.execute("SELECT cell_id FROM cells").fetchall()
    assert len(rows) == 1
    return str(rows[0]["cell_id"])


def test_run_cell_auto_renders_report_newer_than_scores(
    tmp_path,
    monkeypatch,
    capsys,
):
    db_path = tmp_path / "ledger.db"
    output_root = tmp_path / "calibration" / "v1"
    monkeypatch.setattr(schema, "utc_now_iso", lambda: f"{RUN_DATE}T00:00:00+00:00")
    _install_fake_run_cell(monkeypatch)

    assert run_cell.main(_run_cell_args(db_path, output_root)) == 0

    report_index = output_root / "reports" / RUN_DATE / "index.html"
    scored_at = datetime.fromisoformat(_latest_scored_at(db_path)).timestamp()
    captured = capsys.readouterr()
    assert "rendered calibration reports" in captured.err
    assert report_index.is_file()
    assert report_index.stat().st_mtime > scored_at


def test_run_cell_no_render_suppresses_report(tmp_path, monkeypatch):
    db_path = tmp_path / "ledger.db"
    output_root = tmp_path / "calibration" / "v1"
    _install_fake_run_cell(monkeypatch)

    assert run_cell.main(_run_cell_args(db_path, output_root, "--no-render")) == 0

    assert not (output_root / "reports" / RUN_DATE / "index.html").exists()


def test_run_cell_skips_render_on_dispatch_failure(monkeypatch, tmp_path):
    db_path = tmp_path / "ledger.db"
    output_root = tmp_path / "calibration" / "v1"

    def fail_run_cell(**kwargs):
        raise RuntimeError("dispatch failed")

    monkeypatch.setattr(run_cell, "run_cell", fail_run_cell)

    with pytest.raises(RuntimeError, match="dispatch failed"):
        run_cell.main(_run_cell_args(db_path, output_root))

    assert not (output_root / "reports" / RUN_DATE / "index.html").exists()


def test_run_cell_score_then_separate_score_cell_does_not_double_insert(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "ledger.db"
    output_root = tmp_path / "calibration" / "v1"
    _install_fake_run_cell(monkeypatch)

    assert run_cell.main(_run_cell_args(db_path, output_root, "--no-render")) == 0
    before = _score_count(db_path)

    score_cell.score_cell(cell_id=_only_cell_id(db_path), db_path=db_path)

    assert _score_count(db_path) == before


def test_render_reports_idempotent_without_new_scores(tmp_path, monkeypatch):
    db_path = tmp_path / "ledger.db"
    output_root = tmp_path / "calibration" / "v1"
    _install_fake_run_cell(monkeypatch)

    assert run_cell.main(_run_cell_args(db_path, output_root)) == 0

    report_dir = output_root / "reports" / RUN_DATE
    report_index = report_dir / "index.html"
    first_html = report_index.read_text(encoding="utf-8")
    report.render_reports(db_path=db_path, out_dir=report_dir, run_date=RUN_DATE)

    assert report_index.read_text(encoding="utf-8") == first_html

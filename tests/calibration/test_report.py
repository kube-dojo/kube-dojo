from __future__ import annotations

from scripts.calibration import report, schema
from scripts.calibration.models import model_by_canonical


def _insert_cell(db_path, lane, fixture_id, canonical, score):
    model = model_by_canonical(canonical)
    row = schema.build_cell_row(
        lane=lane,
        fixture_id=fixture_id,
        model=model,
        run_date="2026-05-21",
    )
    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id=f"task-{canonical}-{lane}",
            response_path=f"calibration/v1/2026-05-21/responses/{cell_id}.md",
            cost_usd=0.02,
        )
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="gate",
            gate_pass=score == 1.0,
            score_value=score,
        )
    return cell_id


def test_report_renders_matrix_per_lane_and_per_model(tmp_path):
    db_path = tmp_path / "ledger.db"
    schema.init_db(db_path)
    cell_id = _insert_cell(
        db_path,
        "code-writing",
        "parse-dependabot-cooldown",
        "gpt-5.5",
        1.0,
    )
    _insert_cell(db_path, "code-writing", "parse-dependabot-cooldown", "claude-opus-4-7", 0.0)
    _insert_cell(db_path, "fact-check", "k8s-1-35-claims", "gpt-5.5", 1.0)
    _insert_cell(db_path, "fact-check", "k8s-1-35-claims", "claude-opus-4-7", 1.0)
    with schema.connect(db_path) as conn:
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="llm_judge_score",
            gate_pass=False,
            score_value=None,
            scorer="llm-judge:dummy",
            gate_failure_reason="scorer_unparseable_output",
        )

    out_dir = tmp_path / "reports"
    written = report.render_reports(db_path=db_path, out_dir=out_dir)

    matrix = (out_dir / "matrix.html").read_text(encoding="utf-8")
    per_lane = (out_dir / "per-lane" / "code-writing.html").read_text(
        encoding="utf-8",
    )
    per_model = (out_dir / "per-model" / "gpt-5.5.html").read_text(
        encoding="utf-8",
    )
    index = (out_dir / "index.html").read_text(encoding="utf-8")

    assert out_dir / "matrix.html" in written
    assert cell_id in matrix
    assert "code-writing" in matrix
    assert "judge n/a" in matrix
    assert "gpt-5.5" in per_lane
    assert ">n/a</td>" in per_lane
    assert "confidence vs actual" in per_model.lower()
    assert "total_cost=$0.0800" in index

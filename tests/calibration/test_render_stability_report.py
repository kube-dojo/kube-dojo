from __future__ import annotations

from scripts.calibration import schema
from scripts.calibration.models import model_by_canonical
from scripts.calibration.v1 import render_stability_report


def test_stability_report_filters_to_llm_judge_scores_by_default(tmp_path):
    db_path = tmp_path / "ledger.db"
    schema.init_db(db_path)
    model = model_by_canonical("claude-opus-4-7")
    row = schema.build_cell_row(
        lane="orchestrating",
        fixture_id="multi-task-routing-brief",
        model=model,
        run_date="2026-05-21",
    )
    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="deterministic_gate",
            gate_pass=False,
            score_value=0.0,
        )
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="llm_judge_score",
            gate_pass=True,
            score_value=8.0,
            scorer="llm-judge:a",
            gate_failure_reason="gate_passed",
        )
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="llm_judge_score",
            gate_pass=False,
            score_value=4.0,
            scorer="llm-judge:b",
            gate_failure_reason="gate_failed_legitimately",
        )

    llm_only = render_stability_report.load_cell_stats(db_path)
    with_deterministic = render_stability_report.load_cell_stats(
        db_path,
        include_deterministic_gates=True,
    )

    assert len(llm_only) == 1
    assert llm_only[0].n_scores == 2
    assert llm_only[0].score_min == 0.4
    assert len(with_deterministic) == 1
    assert with_deterministic[0].n_scores == 3
    assert with_deterministic[0].score_min == 0.0

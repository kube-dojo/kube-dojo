from __future__ import annotations

from scripts.calibration import pareto, schema
from scripts.calibration.models import model_by_canonical


def test_compute_pareto_with_single_cell(tmp_path):
    db_path = tmp_path / "ledger.db"
    schema.init_db(db_path)

    model = model_by_canonical("gpt-5.5")
    row = schema.build_cell_row(
        lane="code-writing",
        fixture_id="parse-dependabot-cooldown",
        model=model,
        run_date="2026-05-21",
    )

    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id="task-1",
            response_path="calibration/v1/2026-05-21/responses/cell.md",
            latency_s=1.0,
        )
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="pytest_exit",
            gate_pass=True,
            score_value=1.0,
        )

    rows = pareto.compute_pareto(db_path)
    assert len(rows) == 1
    assert rows[0].canonical_string == "gpt-5.5"
    assert rows[0].cells == 1

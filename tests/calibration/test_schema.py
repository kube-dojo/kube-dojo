from __future__ import annotations

from scripts.calibration import schema
from scripts.calibration.models import model_by_canonical


def test_schema_initializes_cells_dispatches_scores(tmp_path):
    db_path = tmp_path / "ledger.db"
    schema.init_db(db_path)
    model = model_by_canonical("gpt-5.3-codex-spark")
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
            latency_s=1.2,
        )
        schema.insert_score(
            conn,
            cell_id=cell_id,
            gate_name="pytest_exit",
            gate_pass=True,
            score_value=1.0,
        )
        stored = schema.fetch_cell(conn, cell_id)
        indexes = schema.list_indexes(conn)
        score_columns = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(scores)").fetchall()
        }

    assert cell_id == (
        "code-writing-parse-dependabot-cooldown-"
        "gpt-5.3-codex-spark@xhigh-2026-05-21"
    )
    assert stored["ledger_version"] == "v1"
    assert stored["canonical_string"] == "gpt-5.3-codex-spark"
    assert {
        "idx_cells_lane",
        "idx_cells_canonical",
        "idx_cells_family",
        "idx_cells_run_date",
        "idx_scores_cell",
    }.issubset(indexes)
    assert "gate_failure_reason" in score_columns


def test_schema_gate_failure_reason_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "ledger.db"
    with schema.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE scores (
              cell_id TEXT NOT NULL,
              gate_name TEXT NOT NULL,
              gate_pass INTEGER NOT NULL CHECK (gate_pass IN (0, 1)),
              score_value REAL,
              scorer TEXT NOT NULL,
              replicate_seq INTEGER NOT NULL DEFAULT 0,
              stderr_excerpt TEXT,
              scored_at TEXT NOT NULL,
              PRIMARY KEY (cell_id, gate_name, scorer)
            )
            """
        )

    schema.init_db(db_path)
    schema.init_db(db_path)

    with schema.connect(db_path) as conn:
        score_columns = [
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(scores)").fetchall()
        ]
    assert score_columns.count("gate_failure_reason") == 1

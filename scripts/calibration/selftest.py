"""End-to-end smoke test for the calibration harness."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import report, schema, score_cell
from .run_cell import DEFAULT_OUTPUT_ROOT, run_cell


def run_selftest(
    *,
    run_date: str | None = None,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    db_path: Path | None = None,
) -> str:
    run_date = run_date or schema.today_iso()
    db_path = db_path or output_root / run_date / "results.db"
    cell_id = run_cell(
        lane="code-writing",
        canonical_string="gpt-5.3-codex-spark",
        fixture_id="parse-dependabot-cooldown",
        run_date=run_date,
        db_path=db_path,
        output_root=output_root,
    )
    score_cell.score_cell(cell_id=cell_id, db_path=db_path)
    reports = report.render_reports(
        db_path=db_path,
        out_dir=output_root / run_date / "reports",
    )

    with schema.connect(db_path) as conn:
        cell_count = conn.execute(
            "SELECT COUNT(*) AS count FROM cells WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()["count"]
        dispatch_count = conn.execute(
            "SELECT COUNT(*) AS count FROM dispatches WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()["count"]
        score_count = conn.execute(
            "SELECT COUNT(*) AS count FROM scores WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()["count"]
        response_row = conn.execute(
            "SELECT response_path FROM dispatches WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()

    response_path = Path(response_row["response_path"])
    if not response_path.is_absolute():
        response_path = Path(__file__).resolve().parents[2] / response_path
    matrix_path = output_root / run_date / "reports" / "matrix.html"

    assert cell_count == 1
    assert dispatch_count == 1
    assert score_count >= 1
    assert response_path.exists()
    assert matrix_path in reports
    assert cell_id in matrix_path.read_text(encoding="utf-8")
    return cell_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the calibration self-test")
    parser.add_argument("--run-date")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--db-path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(
        run_selftest(
            run_date=args.run_date,
            output_root=args.output_root,
            db_path=args.db_path,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


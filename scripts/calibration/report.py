"""Render HTML calibration reports from the SQLite ledger."""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import schema
from .constants import DETERMINISTIC_SCORERS
from .models import ANCHORS, LANES
from .run_cell import DEFAULT_DB_PATH, DEFAULT_OUTPUT_ROOT

TEMPLATE_DIR = Path(__file__).resolve().parent / "reports" / "templates"


@dataclass(frozen=True)
class CellSummary:
    cell_id: str
    lane: str
    canonical_string: str
    run_date: str
    family: str
    effort_requested: str
    effort_confidence: str
    deterministic_score: float
    llm_score: float | None
    response_path: str | None


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _safe_filename(value: str) -> str:
    return value.replace("/", "_").replace("@", "_")


def load_summaries(db_path: Path) -> list[CellSummary]:
    return load_summaries_for_run(db_path)


def load_summaries_for_run(
    db_path: Path,
    *,
    run_date: str | None = None,
) -> list[CellSummary]:
    schema.init_db(db_path)
    with schema.connect(db_path) as conn:
        cells_sql = "SELECT * FROM cells"
        params: tuple[str, ...] = ()
        if run_date is not None:
            cells_sql += " WHERE run_date = ?"
            params = (run_date,)
        cells_sql += " ORDER BY run_date, lane, canonical_string"
        cells = conn.execute(
            cells_sql,
            params,
        ).fetchall()
        scores = conn.execute(
            "SELECT * FROM scores ORDER BY cell_id, gate_name, scorer"
        ).fetchall()
        dispatches = conn.execute(
            """
            SELECT cell_id, response_path
            FROM dispatches
            WHERE dispatch_id IN (
              SELECT MAX(dispatch_id) FROM dispatches GROUP BY cell_id
            )
            """
        ).fetchall()

    score_rows: dict[str, list[Any]] = defaultdict(list)
    for score in scores:
        score_rows[str(score["cell_id"])].append(score)
    response_paths = {
        str(dispatch["cell_id"]): str(dispatch["response_path"])
        for dispatch in dispatches
    }

    summaries: list[CellSummary] = []
    for cell in cells:
        cell_scores = score_rows[str(cell["cell_id"])]
        deterministic = [
            int(row["gate_pass"])
            for row in cell_scores
            if str(row["scorer"]) in DETERMINISTIC_SCORERS
            and str(row["gate_name"]) != "human_spot_check"
        ]
        llm = [
            float(row["score_value"])
            for row in cell_scores
            if str(row["scorer"]).startswith("llm-judge:")
            and row["score_value"] is not None
        ]
        deterministic_score = (
            sum(deterministic) / len(deterministic) if deterministic else 0.0
        )
        llm_score = sum(llm) / len(llm) if llm else None
        summaries.append(
            CellSummary(
                cell_id=str(cell["cell_id"]),
                lane=str(cell["lane"]),
                canonical_string=str(cell["canonical_string"]),
                run_date=str(cell["run_date"]),
                family=str(cell["family"]),
                effort_requested=str(cell["effort_requested"]),
                effort_confidence=str(cell["effort_confidence"]),
                deterministic_score=deterministic_score,
                llm_score=llm_score,
                response_path=response_paths.get(str(cell["cell_id"])),
            )
        )
    return summaries


def _latest_run_date(db_path: Path) -> str | None:
    schema.init_db(db_path)
    with schema.connect(db_path) as conn:
        row = conn.execute("SELECT MAX(run_date) AS run_date FROM cells").fetchone()
    if row is None or row["run_date"] is None:
        return None
    return str(row["run_date"])


def report_dir_for_run(
    run_date: str,
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> Path:
    return output_root / "reports" / run_date


def _matrix_context(summaries: list[CellSummary]) -> dict[str, Any]:
    models = [model.canonical_string for model in ANCHORS]
    lanes = [lane for lane in LANES if any(cell.lane == lane for cell in summaries)]
    by_key = {(cell.lane, cell.canonical_string): cell for cell in summaries}
    rows = [
        {
            "lane": lane,
            "cells": [by_key.get((lane, model)) for model in models],
        }
        for lane in lanes
    ]
    return {
        "lanes": lanes,
        "models": models,
        "rows": rows,
        "total_cells": len(summaries),
    }


def render_reports(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    out_dir: Path | None = None,
    run_date: str | None = None,
) -> list[Path]:
    run_date = run_date or _latest_run_date(db_path)
    summaries = load_summaries_for_run(db_path, run_date=run_date)
    run_date = run_date or "latest"
    out_dir = out_dir or report_dir_for_run(run_date)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "per-lane").mkdir(exist_ok=True)
    (out_dir / "per-model").mkdir(exist_ok=True)

    env = _env()
    written: list[Path] = []

    matrix_html = env.get_template("matrix.html.j2").render(
        **_matrix_context(summaries),
        run_date=run_date,
    )
    matrix_path = out_dir / "matrix.html"
    matrix_path.write_text(matrix_html, encoding="utf-8")
    written.append(matrix_path)

    per_lane_template = env.get_template("per_lane.html.j2")
    lanes = sorted({cell.lane for cell in summaries})
    for lane in lanes:
        lane_cells = sorted(
            [cell for cell in summaries if cell.lane == lane],
            key=lambda cell: (cell.deterministic_score, cell.llm_score or 0.0),
            reverse=True,
        )
        path = out_dir / "per-lane" / f"{lane}.html"
        path.write_text(
            per_lane_template.render(
                lane=lane,
                cells=lane_cells,
                run_date=run_date,
            ),
            encoding="utf-8",
        )
        written.append(path)

    per_model_template = env.get_template("per_model.html.j2")
    models = sorted({cell.canonical_string for cell in summaries})
    for canonical_string in models:
        model_cells = sorted(
            [cell for cell in summaries if cell.canonical_string == canonical_string],
            key=lambda cell: LANES.index(cell.lane),
        )
        path = out_dir / "per-model" / f"{_safe_filename(canonical_string)}.html"
        path.write_text(
            per_model_template.render(
                canonical_string=canonical_string,
                cells=model_cells,
                run_date=run_date,
            ),
            encoding="utf-8",
        )
        written.append(path)

    total_cost = _total_cost(db_path)
    index_path = out_dir / "index.html"
    index_path.write_text(
        _render_index(
            run_date=run_date,
            total_cells=len(summaries),
            total_cost=total_cost,
            families=sorted({cell.family for cell in summaries}),
            lanes=lanes,
            models=models,
        ),
        encoding="utf-8",
    )
    written.append(index_path)
    return written


def _total_cost(db_path: Path) -> float:
    with schema.connect(db_path) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0.0) AS total_cost FROM dispatches"
        ).fetchone()
    return float(row["total_cost"])


def _render_index(
    *,
    run_date: str,
    total_cells: int,
    total_cost: float,
    families: list[str],
    lanes: list[str],
    models: list[str],
) -> str:
    family_list = ", ".join(families) if families else "none"
    lane_links = "\n".join(
        f'<li><a href="per-lane/{lane}.html">{lane}</a></li>' for lane in lanes
    )
    model_links = "\n".join(
        f'<li><a href="per-model/{_safe_filename(model)}.html">{model}</a></li>'
        for model in models
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Calibration reports — {run_date}</title>
<link rel="stylesheet" href="../design-system.css">
</head>
<body>
<h1>Calibration reports — {run_date}</h1>
<p class="meta">cells={total_cells} · total_cost=${total_cost:.4f} · families={family_list}</p>
<p><a href="matrix.html">Matrix heatmap</a></p>
<h2>Per Lane</h2>
<ul>{lane_links}</ul>
<h2>Per Model</h2>
<ul>{model_links}</ul>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render calibration reports")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--run-date")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for path in render_reports(
        db_path=args.db_path,
        out_dir=args.out_dir,
        run_date=args.run_date,
    ):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

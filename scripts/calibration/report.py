"""Render HTML calibration reports from the SQLite ledger."""
from __future__ import annotations

import argparse
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import constants
from . import schema
from .models import ANCHORS, LANES
from .run_cell import DEFAULT_DB_PATH, DEFAULT_OUTPUT_ROOT

TEMPLATE_DIR = Path(__file__).resolve().parent / "reports" / "templates"


@dataclass(frozen=True)
class CellSummary:
    cell_id: str
    lane: str
    fixture_id: str
    canonical_string: str
    run_date: str
    family: str
    effort_requested: str
    effort_confidence: str
    deterministic_score: float
    llm_score: float | None
    composite: float
    letter: str
    color: str
    gate_pct: float
    judge_title: str
    judge_dissent: bool
    response_path: str | None


@dataclass(frozen=True)
class LaneGrade:
    lane: str
    composite: float
    letter: str
    color: str


@dataclass(frozen=True)
class LaneModelSummary:
    canonical_string: str
    composite: float
    letter: str
    color: str
    judge_dissent: bool


def _score_row_value(row: Any, key: str) -> Any:
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return getattr(row, key)


def _deterministic_rows(score_rows: list[Any]) -> list[Any]:
    return [
        row
        for row in score_rows
        if _score_row_value(row, "scorer") == "deterministic"
        and _score_row_value(row, "gate_name") != "human_spot_check"
    ]


def _judge_rows(score_rows: list[Any]) -> list[Any]:
    return [
        row
        for row in score_rows
        if str(_score_row_value(row, "scorer")).startswith("llm-judge:")
    ]


def _gate_component(score_rows: list[Any]) -> float:
    det_rows = _deterministic_rows(score_rows)
    if not det_rows:
        return 0.0

    has_ratios = any(
        _score_row_value(row, "score_value") is not None
        and 0.0 <= float(_score_row_value(row, "score_value")) <= 1.0
        for row in det_rows
    )
    if has_ratios:
        values = [
            float(_score_row_value(row, "score_value"))
            if _score_row_value(row, "score_value") is not None
            else (1.0 if _score_row_value(row, "gate_pass") else 0.0)
            for row in det_rows
        ]
    else:
        values = [1.0 if _score_row_value(row, "gate_pass") else 0.0 for row in det_rows]
    return (sum(values) / len(values)) * 10.0


def _parsed_judge_scores(score_rows: list[Any]) -> list[float]:
    return [
        float(_score_row_value(row, "score_value"))
        for row in _judge_rows(score_rows)
        if _score_row_value(row, "score_value") is not None
    ]


def _judge_title(score_rows: list[Any]) -> str:
    values: list[str] = []
    for row in _judge_rows(score_rows):
        score_value = _score_row_value(row, "score_value")
        values.append("n/a" if score_value is None else f"{float(score_value):.1f}")
    return ", ".join(values) if values else "n/a"


def letter_grade_for_score(score: float) -> tuple[str, str]:
    for letter, lower, upper, color in constants.LETTER_GRADE_BANDS:
        if lower <= score < upper:
            return letter, color
    return constants.LETTER_GRADE_BANDS[-1][0], constants.LETTER_GRADE_BANDS[-1][3]


def judge_dissent(score_rows: list[Any], lane: str) -> bool:
    if lane not in constants.PROSE_LANES:
        return False
    judge_scores = _parsed_judge_scores(score_rows)
    if len(judge_scores) < 2:
        return False
    return max(judge_scores) - min(judge_scores) > constants.JUDGE_DISSENT_THRESHOLD


def composite_score(score_rows: list[Any], lane: str) -> tuple[float, str, str]:
    gate_component = _gate_component(score_rows)
    parsed_judge_scores = _parsed_judge_scores(score_rows)

    if lane in constants.MECHANICAL_LANES:
        composite = gate_component
    elif lane in constants.PROSE_LANES:
        if parsed_judge_scores:
            judge_component = sum(parsed_judge_scores) / len(parsed_judge_scores)
            composite = (
                constants.COMPOSITE_GATE_WEIGHT * gate_component
                + constants.COMPOSITE_JUDGE_WEIGHT * judge_component
            )
        else:
            composite = constants.COMPOSITE_GATE_WEIGHT * gate_component
    else:
        composite = gate_component

    composite = max(0.0, min(10.0, composite))
    letter, color = letter_grade_for_score(composite)
    return composite, letter, color


def _grade_summary(cells: list[CellSummary]) -> dict[str, Any] | None:
    if not cells:
        return None
    score = sum(cell.composite for cell in cells) / len(cells)
    letter, color = letter_grade_for_score(score)
    return {"composite": score, "letter": letter, "color": color}


def _lane_grades(cells: list[CellSummary]) -> list[LaneGrade]:
    grouped: dict[str, list[CellSummary]] = defaultdict(list)
    for cell in cells:
        grouped[cell.lane].append(cell)

    grades: list[LaneGrade] = []
    for lane in LANES:
        summary = _grade_summary(grouped.get(lane, []))
        if summary is None:
            continue
        grades.append(
            LaneGrade(
                lane=lane,
                composite=float(summary["composite"]),
                letter=str(summary["letter"]),
                color=str(summary["color"]),
            )
        )
    return grades


def _lane_model_summaries(cells: list[CellSummary]) -> list[LaneModelSummary]:
    grouped: dict[str, list[CellSummary]] = defaultdict(list)
    for cell in cells:
        grouped[cell.canonical_string].append(cell)

    summaries: list[LaneModelSummary] = []
    for model in sorted(grouped):
        summary = _grade_summary(grouped[model])
        if summary is None:
            continue
        summaries.append(
            LaneModelSummary(
                canonical_string=model,
                composite=float(summary["composite"]),
                letter=str(summary["letter"]),
                color=str(summary["color"]),
                judge_dissent=any(cell.judge_dissent for cell in grouped[model]),
            )
        )
    return summaries


def _letter_grade_legend() -> list[dict[str, str]]:
    legend = []
    for letter, lower, upper, color in constants.LETTER_GRADE_BANDS:
        if letter == "A":
            band = f"{lower:.1f}+"
        elif letter == "F":
            band = f"<{upper:.1f}"
        else:
            band = f"{lower:.1f}-{upper:.1f}"
        legend.append({"letter": letter, "band": band, "color": color})
    return legend


def _radar_context(cells: list[CellSummary]) -> dict[str, Any]:
    size = 480.0
    center = size / 2.0
    outer_radius = 130.0
    label_radius = 188.0
    cells_by_lane: dict[str, list[CellSummary]] = defaultdict(list)
    for cell in cells:
        cells_by_lane[cell.lane].append(cell)
    axis_count = len(LANES)

    def point_for(index: int, radius: float) -> tuple[float, float]:
        angle = -math.pi / 2 + (2 * math.pi * index / axis_count)
        return center + radius * math.cos(angle), center + radius * math.sin(angle)

    rings = []
    for value in (2, 4, 6, 8, 10):
        radius = outer_radius * value / 10.0
        rings.append(
            {
                "value": value,
                "points": " ".join(
                    f"{x:.1f},{y:.1f}"
                    for x, y in (point_for(index, radius) for index in range(axis_count))
                ),
            }
        )

    axes = []
    polygon_points = []
    for index, lane in enumerate(LANES):
        summary = _grade_summary(cells_by_lane.get(lane, []))
        composite = float(summary["composite"]) if summary else 0.0
        letter = str(summary["letter"]) if summary else letter_grade_for_score(0.0)[0]
        color = str(summary["color"]) if summary else letter_grade_for_score(0.0)[1]
        axis_x, axis_y = point_for(index, outer_radius)
        score_x, score_y = point_for(index, outer_radius * composite / 10.0)
        label_x, label_y = point_for(index, label_radius)
        cos_value = math.cos(-math.pi / 2 + (2 * math.pi * index / axis_count))
        if cos_value < -0.35:
            anchor = "end"
            chip_x = label_x - 22.0
        elif cos_value > 0.35:
            anchor = "start"
            chip_x = label_x + 4.0
        else:
            anchor = "middle"
            chip_x = label_x + 16.0
        chip_x = max(8.0, min(size - 28.0, chip_x))
        chip_y = label_y + 3.0
        axes.append(
            {
                "lane": lane,
                "axis_x": axis_x,
                "axis_y": axis_y,
                "label_x": max(18.0, min(size - 18.0, label_x)),
                "label_y": max(18.0, min(size - 18.0, label_y)),
                "anchor": anchor,
                "chip_x": chip_x,
                "chip_y": chip_y,
                "chip_text_x": chip_x + 10.0,
                "chip_text_y": chip_y + 10.0,
                "composite": composite,
                "letter": letter,
                "color": color,
                "missing": summary is None,
            }
        )
        polygon_points.append(f"{score_x:.1f},{score_y:.1f}")

    return {
        "axes": axes,
        "rings": rings,
        "polygon_points": " ".join(polygon_points),
        "center": center,
        "outer_radius": outer_radius,
        "size": size,
    }


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
        llm = [
            float(row["score_value"])
            for row in cell_scores
            if str(row["scorer"]).startswith("llm-judge:")
            and row["score_value"] is not None
        ]
        gate_component = _gate_component(cell_scores)
        deterministic_score = gate_component / 10.0
        llm_score = sum(llm) / len(llm) if llm else None
        composite, letter, color = composite_score(cell_scores, str(cell["lane"]))
        summaries.append(
            CellSummary(
                cell_id=str(cell["cell_id"]),
                lane=str(cell["lane"]),
                fixture_id=str(cell["fixture_id"]),
                canonical_string=str(cell["canonical_string"]),
                run_date=str(cell["run_date"]),
                family=str(cell["family"]),
                effort_requested=str(cell["effort_requested"]),
                effort_confidence=str(cell["effort_confidence"]),
                deterministic_score=deterministic_score,
                llm_score=llm_score,
                composite=composite,
                letter=letter,
                color=color,
                gate_pct=gate_component * 10.0,
                judge_title=_judge_title(cell_scores),
                judge_dissent=judge_dissent(cell_scores, str(cell["lane"])),
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
    rows = []
    for lane in lanes:
        cells = [by_key.get((lane, model)) for model in models]
        rows.append(
            {
                "lane": lane,
                "cells": cells,
                "summary": _grade_summary(
                    [cell for cell in summaries if cell.lane == lane]
                ),
            }
        )
    model_summaries = [
        _grade_summary([cell for cell in summaries if cell.canonical_string == model])
        for model in models
    ]
    return {
        "lanes": lanes,
        "models": models,
        "rows": rows,
        "model_summaries": model_summaries,
        "overall_summary": _grade_summary(summaries),
        "grade_legend": _letter_grade_legend(),
        "total_cells": len(summaries),
    }


def render_reports(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    out_dir: Path | None = None,
    run_date: str | None = None,
) -> list[Path]:
    if run_date is None:
        run_date = _latest_run_date(db_path) or "latest"
    summaries = load_summaries_for_run(db_path, run_date=run_date)
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
        lane_models = sorted(
            _lane_model_summaries([cell for cell in summaries if cell.lane == lane]),
            key=lambda cell: cell.composite,
            reverse=True,
        )
        path = out_dir / "per-lane" / f"{lane}.html"
        path.write_text(
            per_lane_template.render(
                lane=lane,
                cells=lane_models,
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
        lane_grades = _lane_grades(model_cells)
        strengths = sorted(
            [grade for grade in lane_grades if grade.letter == "A"],
            key=lambda grade: grade.composite,
            reverse=True,
        )
        weaknesses = sorted(
            [grade for grade in lane_grades if grade.letter == "F"],
            key=lambda grade: grade.composite,
        )
        path = out_dir / "per-model" / f"{_safe_filename(canonical_string)}.html"
        path.write_text(
            per_model_template.render(
                canonical_string=canonical_string,
                cells=model_cells,
                radar=_radar_context(model_cells),
                strengths=strengths,
                weaknesses=weaknesses,
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

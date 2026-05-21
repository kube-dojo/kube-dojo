"""Select high-variance calibration cells for stability replicates."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_DB_PATH = REPO_ROOT / "calibration" / "v1" / "ledger.db"
DEFAULT_OUT_PATH = REPO_ROOT / "calibration" / "v1" / "reports" / "stability-candidates.json"
DIAGNOSTIC_GATES = frozenset({"human_spot_check", "llm_judge_error"})


@dataclass(frozen=True)
class ScoreSample:
    gate_name: str
    raw_value: float
    unit_value: float


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _unit_score(gate_name: str, score_value: float) -> float:
    """Map mixed ledger scores onto a pass/fail-like 0..1 scale."""
    if gate_name == "llm_judge_score":
        return max(0.0, min(1.0, score_value / 10.0))
    return max(0.0, min(1.0, score_value))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def load_cell_scores(
    *,
    db_path: Path,
    excluded_lanes: set[str],
) -> dict[str, dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
              c.cell_id,
              c.domain,
              c.lane,
              c.fixture_id,
              c.fixture_version,
              c.family,
              c.provider_cli,
              c.model_id,
              c.version,
              c.canonical_string,
              c.effort_requested,
              c.run_date,
              s.gate_name,
              s.score_value
            FROM cells AS c
            JOIN scores AS s ON s.cell_id = c.cell_id
            WHERE s.score_value IS NOT NULL
            ORDER BY c.canonical_string, c.lane, s.gate_name, s.scorer
            """
        ).fetchall()

    grouped: dict[str, dict[str, Any]] = {}
    samples_by_cell: dict[str, list[ScoreSample]] = defaultdict(list)
    for row in rows:
        lane = str(row["lane"])
        gate_name = str(row["gate_name"])
        if lane in excluded_lanes or gate_name in DIAGNOSTIC_GATES:
            continue
        cell_id = str(row["cell_id"])
        grouped.setdefault(
            cell_id,
            {
                "cell_id": cell_id,
                "domain": str(row["domain"]),
                "lane": lane,
                "fixture_id": str(row["fixture_id"]),
                "fixture_version": str(row["fixture_version"]),
                "family": str(row["family"]),
                "provider_cli": str(row["provider_cli"]),
                "model_id": str(row["model_id"]),
                "version": str(row["version"]),
                "canonical_string": str(row["canonical_string"]),
                "effort_requested": str(row["effort_requested"]),
                "run_date": str(row["run_date"]),
            },
        )
        raw_value = float(row["score_value"])
        samples_by_cell[cell_id].append(
            ScoreSample(
                gate_name=gate_name,
                raw_value=raw_value,
                unit_value=_unit_score(gate_name, raw_value),
            )
        )

    candidates: dict[str, dict[str, Any]] = {}
    for cell_id, cell in grouped.items():
        samples = samples_by_cell[cell_id]
        if not samples:
            continue
        unit_values = [sample.unit_value for sample in samples]
        raw_values = [sample.raw_value for sample in samples]
        mean_score = _mean(unit_values)
        scorer_disagreement = max(unit_values) - min(unit_values)
        boundary_distance = abs(0.5 - mean_score)
        candidates[cell_id] = {
            **cell,
            "n_scores": len(samples),
            "score_min": round(min(unit_values), 4),
            "score_max": round(max(unit_values), 4),
            "mean_score": round(mean_score, 4),
            "scorer_disagreement": round(scorer_disagreement, 4),
            "boundary_distance": round(boundary_distance, 4),
            "raw_score_min": round(min(raw_values), 4),
            "raw_score_max": round(max(raw_values), 4),
            "rank_score": round(scorer_disagreement - boundary_distance, 4),
        }
    return candidates


def rank_candidates(
    candidates: dict[str, dict[str, Any]],
    *,
    top_per_model: int,
    cap_total: int,
) -> list[dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates.values():
        by_model[str(candidate["canonical_string"])].append(candidate)

    selected: list[dict[str, Any]] = []
    for model in sorted(by_model):
        model_candidates = sorted(
            by_model[model],
            key=lambda item: (
                -float(item["scorer_disagreement"]),
                float(item["boundary_distance"]),
                -int(item["n_scores"]),
                str(item["lane"]),
                str(item["cell_id"]),
            ),
        )[:top_per_model]
        for model_rank, candidate in enumerate(model_candidates, start=1):
            selected.append({**candidate, "model_rank": model_rank})

    ranked = sorted(
        selected,
        key=lambda item: (
            -float(item["scorer_disagreement"]),
            float(item["boundary_distance"]),
            -int(item["n_scores"]),
            str(item["canonical_string"]),
            str(item["lane"]),
        ),
    )[:cap_total]
    return [
        {
            **candidate,
            "rank": rank,
        }
        for rank, candidate in enumerate(ranked, start=1)
    ]


def build_payload(
    *,
    db_path: Path,
    top_per_model: int,
    cap_total: int,
    excluded_lanes: set[str],
) -> dict[str, Any]:
    candidates = rank_candidates(
        load_cell_scores(db_path=db_path, excluded_lanes=excluded_lanes),
        top_per_model=top_per_model,
        cap_total=cap_total,
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "db_path": str(db_path.relative_to(REPO_ROOT) if db_path.is_relative_to(REPO_ROOT) else db_path),
        "top_per_model": top_per_model,
        "cap_total": cap_total,
        "excluded_lanes": sorted(excluded_lanes),
        "metric_note": (
            "Metrics use score_value normalized to 0..1: llm_judge_score is divided "
            "by 10, deterministic gates are already 0/1, and diagnostic/error gates "
            "are excluded."
        ),
        "candidates": candidates,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank calibration cells for stability replicate runs."
    )
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_PATH)
    parser.add_argument("--top-per-model", type=int, default=5)
    parser.add_argument("--cap-total", type=int, default=70)
    parser.add_argument(
        "--exclude-lane",
        action="append",
        default=["mcp-use"],
        help="Lane to exclude from replicate selection. Repeatable.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.top_per_model < 1:
        print("error: --top-per-model must be >= 1", file=sys.stderr)
        return 2
    if args.cap_total < 1:
        print("error: --cap-total must be >= 1", file=sys.stderr)
        return 2
    if not args.db_path.exists():
        print(f"error: ledger not found: {args.db_path}", file=sys.stderr)
        return 2

    payload = build_payload(
        db_path=args.db_path,
        top_per_model=args.top_per_model,
        cap_total=args.cap_total,
        excluded_lanes=set(args.exclude_lane),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2)
    args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

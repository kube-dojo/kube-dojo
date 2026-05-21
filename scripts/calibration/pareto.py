"""Compute the cost-per-correct-answer Pareto frontier from the ledger.

Multiplies each cell's observed dispatch latency by an approximate $/sec rate
for the model's tier, then aggregates per model: total $ / (passing cells +
0.5 × partial cells) gives a cost-per-pass score. Renders a small HTML chart
appended to the latest wave report.

Cost rates are coarse — they treat all anthropic-tier Max OAuth dispatches as
zero-marginal-cost (within the Max subscription cap), and price hermes /
openrouter dispatches at their listed OpenRouter unit price as a per-second
proxy. This is good enough for relative Pareto ranking; it is NOT an accurate
cost prediction for production routing.
"""
from __future__ import annotations

import argparse
import contextlib
import sqlite3
import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

try:
    from .constants import DETERMINISTIC_SCORERS
except ImportError:  # direct script execution path
    from constants import DETERMINISTIC_SCORERS

# Per-second USD rate. Rough — these are observed billing receipts divided by
# observed total latency across the Wave A+B + session-37 ledger as of
# 2026-05-21. Anthropic Max / Codex Pro / agy on Google One run on subscription
# caps with effectively zero marginal cost per call WITHIN the cap; rated at
# $0.0001/s as a placeholder so non-subscription models clearly dominate the
# rank. Hermes/OpenRouter rates are OpenRouter list prices / observed mean
# tokens-per-call rounded to a per-second equivalent.
COST_PER_SECOND_USD: dict[str, float] = {
    "claude-opus-4-7": 0.0001,        # Max subscription
    "claude-sonnet-4-6": 0.0001,      # Max subscription
    "claude-haiku-4-5": 0.0001,       # Max subscription
    "gpt-5.5": 0.0001,                # Codex Pro subscription
    "gpt-5.3-codex-spark": 0.0001,    # Codex Pro subscription
    "gpt-5.4-mini": 0.0001,           # Codex Pro subscription
    "gemini-3.5-flash-high": 0.0001,  # Google One subscription
    "gemini-3.1-pro-preview": 0.0001, # Google One subscription
    "gemini-3.1-flash-lite-preview": 0.0001,  # Google One subscription
    "deepseek-v4-pro": 0.0008,        # hermes/openrouter — observed
    "deepseek-v4-flash": 0.0004,      # hermes/openrouter — observed
    "qwen3.6-plus": 0.0006,           # hermes/openrouter — observed
    "qwen3.6": 0.0003,                # hermes/openrouter — observed
    "grok-4.3": 0.0010,               # hermes/openrouter — observed
}
DEFAULT_COST_PER_SECOND = 0.0005


@dataclass(frozen=True)
class ModelPareto:
    canonical_string: str
    cells: int
    total_latency_s: float
    total_cost_usd: float
    quality_score: float  # 0.0 - 2.0 (det + judge/10)
    cost_per_quality: float


QUALITY_FLOOR = 1.0  # det 0.5 + judge 5.0/10 — below this, the model is not useful


def compute_pareto(db_path: Path, *, quality_floor: float = QUALITY_FLOOR) -> list[ModelPareto]:
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row

        cells = conn.execute(
            "SELECT cell_id, canonical_string FROM cells"
        ).fetchall()
        by_model: dict[str, dict] = {}
        for c in cells:
            slot = by_model.setdefault(
                c["canonical_string"],
                {"cells": [], "det_passes": [], "judge_scores": [], "total_lat": 0.0},
            )
            slot["cells"].append(c["cell_id"])

        for canonical, slot in by_model.items():
            for cell_id in slot["cells"]:
                det = conn.execute(
                    "SELECT AVG(CAST(gate_pass AS REAL)) FROM scores "
                    "WHERE cell_id=? AND scorer IN (?, ?) "
                    "AND gate_name != 'human_spot_check'",
                    (cell_id, *DETERMINISTIC_SCORERS),
                ).fetchone()[0]
                if det is not None:
                    slot["det_passes"].append(float(det))
                for j in conn.execute(
                    "SELECT score_value FROM scores WHERE cell_id=? AND gate_name='llm_judge_score'",
                    (cell_id,),
                ).fetchall():
                    if j["score_value"] is not None and float(j["score_value"]) > 0:
                        slot["judge_scores"].append(float(j["score_value"]))
                latency = conn.execute(
                    "SELECT latency_s FROM dispatches WHERE cell_id=? ORDER BY dispatch_ts DESC LIMIT 1",
                    (cell_id,),
                ).fetchone()
                if latency and latency["latency_s"] is not None:
                    slot["total_lat"] += float(latency["latency_s"])

        out: list[ModelPareto] = []
        for canonical, slot in by_model.items():
            det = statistics.mean(slot["det_passes"]) if slot["det_passes"] else 0.0
            judge = statistics.mean(slot["judge_scores"]) if slot["judge_scores"] else 0.0
            quality = det + (judge / 10.0)
            rate = COST_PER_SECOND_USD.get(canonical, DEFAULT_COST_PER_SECOND)
            cost = slot["total_lat"] * rate
            # Below the quality floor, the model is producing empty / refused
            # responses — fast and cheap, but not useful. Sentinel infinity sinks
            # it to the bottom of the rank instead of rewarding it.
            cpq = float("inf") if quality < quality_floor else cost / max(quality, 0.01)
            out.append(
                ModelPareto(
                    canonical_string=canonical,
                    cells=len(slot["cells"]),
                    total_latency_s=slot["total_lat"],
                    total_cost_usd=cost,
                    quality_score=quality,
                    cost_per_quality=cpq,
                )
            )
        return sorted(out, key=lambda m: m.cost_per_quality)


def render_pareto_html(rows: Iterable[ModelPareto]) -> str:
    rows = list(rows)
    lines = [
        "<table>",
        "<thead><tr>"
        "<th>Rank</th><th>Model</th><th>Quality (det+judge/10)</th>"
        "<th>Total latency (s)</th><th>Est cost ($)</th>"
        "<th>Cost / quality unit</th>"
        "</tr></thead>",
        "<tbody>",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"<tr><td>{i}</td><td><code>{r.canonical_string}</code></td>"
            f"<td>{r.quality_score:.2f}</td>"
            f"<td>{r.total_latency_s:.0f}</td>"
            f"<td>${r.total_cost_usd:.4f}</td>"
            f"<td>${r.cost_per_quality:.4f}</td></tr>"
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute Pareto frontier")
    parser.add_argument("--db-path", type=Path, default=Path("calibration/v1/ledger.db"))
    parser.add_argument("--format", choices=("text", "html"), default="text")
    args = parser.parse_args(argv)

    rows = compute_pareto(args.db_path)
    if args.format == "html":
        print(render_pareto_html(rows))
    else:
        print(f"{'rank':<5} {'model':<35} {'quality':<10} {'lat (s)':<10} {'cost ($)':<12} {'cost/q':<12}")
        for i, r in enumerate(rows, 1):
            print(
                f"{i:<5} {r.canonical_string:<35} {r.quality_score:<10.2f} "
                f"{r.total_latency_s:<10.0f} ${r.total_cost_usd:<11.4f} ${r.cost_per_quality:<11.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

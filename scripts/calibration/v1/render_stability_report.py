"""Render the v1 calibration stability variance report."""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from html import escape
from pathlib import Path
from statistics import median, pstdev
from typing import Any
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_DATE = "2026-05-21"
DEFAULT_DB_PATH = REPO_ROOT / "calibration" / "v1" / "ledger.db"
DEFAULT_CANDIDATES_PATH = (
    REPO_ROOT / "calibration" / "v1" / "reports" / "stability-candidates.json"
)
DEFAULT_OUT_PATH = (
    REPO_ROOT
    / "calibration"
    / "v1"
    / "reports"
    / REPORT_DATE
    / "stability.html"
)


@dataclass(frozen=True)
class CellStats:
    cell_id: str
    lane: str
    fixture_id: str
    canonical_string: str
    effort_requested: str
    n_scores: int
    mean: float
    stddev: float
    score_min: float
    score_max: float
    replicate_seqs: tuple[int, ...]

    @property
    def scorer_disagreement(self) -> float:
        return self.score_max - self.score_min

    @property
    def model_label(self) -> str:
        return f"{self.canonical_string}@{self.effort_requested}"


@dataclass(frozen=True)
class CoverageRow:
    cell_id: str
    lane: str
    model: str
    rank: int
    replicates_done: int
    current_mean: float | None
    current_stddev: float | None


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_scores(value: str | None) -> list[float]:
    if value is None:
        return []
    return [float(part) for part in value.split(",") if part]


def _parse_replicate_seqs(value: str | None) -> tuple[int, ...]:
    if value is None:
        return ()
    return tuple(sorted({int(part) for part in value.split(",") if part}))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (percentile / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _fmt(value: float | None) -> str:
    if value is None:
        return "&mdash;"
    return f"{value:.3f}"


def _h(value: object) -> str:
    return escape(str(value), quote=True)


def _href(value: str) -> str:
    return escape(quote(value), quote=True)


def _per_lane_link(lane: str) -> str:
    return f'<a href="per-lane/{_href(lane)}.html">{_h(lane)}</a>'


def _per_model_link(model: str, label: str | None = None) -> str:
    text = label if label is not None else model
    return f'<a href="per-model/{_href(model)}.html"><code>{_h(text)}</code></a>'


def load_cell_stats(db_path: Path) -> list[CellStats]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
              s.cell_id,
              c.lane,
              c.fixture_id,
              c.canonical_string,
              c.effort_requested,
              COUNT(s.score_value) AS n_scores,
              AVG(s.score_value) AS mean_score,
              GROUP_CONCAT(s.score_value) AS score_values,
              GROUP_CONCAT(DISTINCT s.replicate_seq) AS replicate_seqs
            FROM scores AS s
            JOIN cells AS c ON c.cell_id = s.cell_id
            WHERE s.score_value IS NOT NULL
            GROUP BY s.cell_id
            ORDER BY c.lane, c.canonical_string, c.fixture_id
            """
        ).fetchall()

    stats: list[CellStats] = []
    for row in rows:
        values = _parse_scores(row["score_values"])
        if not values:
            continue
        stats.append(
            CellStats(
                cell_id=str(row["cell_id"]),
                lane=str(row["lane"]),
                fixture_id=str(row["fixture_id"]),
                canonical_string=str(row["canonical_string"]),
                effort_requested=str(row["effort_requested"]),
                n_scores=int(row["n_scores"]),
                mean=float(row["mean_score"]),
                stddev=pstdev(values),
                score_min=min(values),
                score_max=max(values),
                replicate_seqs=_parse_replicate_seqs(row["replicate_seqs"]),
            )
        )
    return stats


def load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_candidates = payload["candidates"] if isinstance(payload, dict) else payload
    if not isinstance(raw_candidates, list):
        msg = f"candidate payload must contain a list: {path}"
        raise ValueError(msg)
    return raw_candidates


def build_coverage(
    candidates: list[dict[str, Any]],
    stats_by_cell: dict[str, CellStats],
) -> list[CoverageRow]:
    rows: list[CoverageRow] = []
    for fallback_rank, candidate in enumerate(candidates, start=1):
        cell_id = str(candidate["cell_id"])
        stats = stats_by_cell.get(cell_id)
        canonical_string = str(candidate.get("canonical_string", "unknown"))
        effort_requested = str(candidate.get("effort_requested", "unknown"))
        model = f"{canonical_string}@{effort_requested}"
        replicate_count = len(stats.replicate_seqs) if stats is not None else 0
        rows.append(
            CoverageRow(
                cell_id=cell_id,
                lane=str(candidate.get("lane", stats.lane if stats is not None else "unknown")),
                model=model,
                rank=int(candidate.get("rank", fallback_rank)),
                replicates_done=min(replicate_count, 3),
                current_mean=stats.mean if stats is not None else None,
                current_stddev=stats.stddev if stats is not None else None,
            )
        )
    return sorted(rows, key=lambda row: (row.replicates_done, row.rank, row.cell_id))


def _render_top_disagreement(rows: list[CellStats]) -> str:
    table_rows = []
    for row in rows:
        table_rows.append(
            "    <tr>"
            f"<td>{_per_lane_link(row.lane)}</td>"
            f"<td>{_per_model_link(row.canonical_string, row.model_label)}</td>"
            f"<td><code>{_h(row.fixture_id)}</code></td>"
            f"<td class=\"num\">{row.n_scores}</td>"
            f"<td class=\"num\">{_fmt(row.mean)}</td>"
            f"<td class=\"num\">{_fmt(row.stddev)}</td>"
            f"<td class=\"num\">[{_fmt(row.score_min)}..{_fmt(row.score_max)}]</td>"
            f"<td class=\"num\">{_fmt(row.scorer_disagreement)}</td>"
            "</tr>"
        )
    return "\n".join(table_rows)


def _render_coverage(rows: list[CoverageRow]) -> str:
    table_rows = []
    for row in rows:
        status_class = "top" if row.replicates_done >= 3 else "bot"
        table_rows.append(
            "    <tr>"
            f"<td class=\"cell\"><code>{_h(row.cell_id)}</code></td>"
            f"<td>{_per_lane_link(row.lane)}</td>"
            f"<td><code>{_h(row.model)}</code></td>"
            f"<td class=\"num {status_class}\">{row.replicates_done}</td>"
            f"<td class=\"num\">{_fmt(row.current_mean)}</td>"
            f"<td class=\"num\">{_fmt(row.current_stddev)}</td>"
            "</tr>"
        )
    return "\n".join(table_rows)


def _render_link_list(values: list[str], prefix: str, *, code: bool = False) -> str:
    links = []
    for value in values:
        href = f"{prefix}/{_href(value)}.html"
        label = f"<code>{_h(value)}</code>" if code else _h(value)
        links.append(f'<a href="{href}">{label}</a>')
    return ", ".join(links)


def render_report(
    *,
    cell_stats: list[CellStats],
    candidates: list[dict[str, Any]],
    out_path: Path,
) -> str:
    stats_by_cell = {row.cell_id: row for row in cell_stats}
    coverage_rows = build_coverage(candidates, stats_by_cell)
    stddevs = [row.stddev for row in cell_stats]
    headline_mean = _mean(stddevs) if stddevs else 0.0
    headline_median = median(stddevs) if stddevs else 0.0
    headline_p95 = _percentile(stddevs, 95.0)
    top_disagreement = sorted(
        cell_stats,
        key=lambda row: (
            -row.scorer_disagreement,
            -row.stddev,
            row.lane,
            row.canonical_string,
            row.fixture_id,
        ),
    )[:20]
    replicate_seqs = sorted(
        {seq for row in cell_stats for seq in row.replicate_seqs}
    )
    lanes = sorted({row.lane for row in cell_stats})
    models = sorted({row.canonical_string for row in cell_stats})
    report_rel = (
        str(out_path.relative_to(REPO_ROOT))
        if out_path.is_relative_to(REPO_ROOT)
        else str(out_path)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Stability variance report - {REPORT_DATE}</title>
<style>
  body {{ max-width: 1200px; margin: 0 auto; padding: 1.5rem 1.25rem 4rem; font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1a1a1a; }}
  h1 {{ margin-bottom: 0.25rem; }}
  p.meta {{ color: #555; font-size: 0.9rem; margin-top: 0.2rem; }}
  h2 {{ margin-top: 2rem; border-bottom: 2px solid #eee; padding-bottom: 0.25rem; }}
  .tldr {{ background:#fff8e1; padding:0.85rem 1rem; border-left:4px solid #ffb300; margin:0.75rem 0 1.25rem; border-radius:0.3rem; }}
  .finding {{ background:#e8f5e9; padding:0.6rem 0.9rem; border-left:4px solid #2e7d32; margin:0.5rem 0; border-radius:0.3rem; }}
  table {{ width:100%; border-collapse: collapse; margin: 0.75rem 0 1.25rem; font-size: 0.92rem; }}
  th, td {{ border:1px solid #ddd; padding:0.35rem 0.55rem; vertical-align: top; }}
  th {{ background:#f3f5f7; text-align:left; font-weight: 600; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  td.cell code {{ word-break: break-all; }}
  td.top {{ background: #e6f4ea; font-weight: 600; }}
  td.mid {{ background: #fff8e1; }}
  td.bot {{ background: #fde7e7; font-weight: 600; }}
  code {{ background:#f3f5f7; padding:0.05rem 0.3rem; border-radius:0.2rem; font-size:0.9em; }}
  a {{ color:#0645ad; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>

<h1>Stability variance report</h1>
<p class="meta">{REPORT_DATE} &middot; {len(cell_stats)} scored cells &middot; {len(candidates)} stability candidates &middot; replicate_seq={", ".join(str(seq) for seq in replicate_seqs) or "none"} &middot; output=<code>{_h(report_rel)}</code></p>

<h2>1. Headline variance floor</h2>
<div class="tldr">
  <strong>Variance floor.</strong> Across all scored cells in <code>calibration/v1/ledger.db</code>, per-cell raw <code>score_value</code> standard deviation averages <strong>{_fmt(headline_mean)}</strong>, with median <strong>{_fmt(headline_median)}</strong> and p95 <strong>{_fmt(headline_p95)}</strong>.
</div>
<table>
  <thead><tr><th>Metric</th><th>Value</th></tr></thead>
  <tbody>
    <tr><td>Mean cell stddev</td><td class="num">{_fmt(headline_mean)}</td></tr>
    <tr><td>Median cell stddev</td><td class="num">{_fmt(headline_median)}</td></tr>
    <tr><td>p95 cell stddev</td><td class="num">{_fmt(headline_p95)}</td></tr>
  </tbody>
</table>

<h2>2. Top 20 most-disagreeing cells</h2>
<table>
  <thead><tr>
    <th>Lane</th><th>Model</th><th>Fixture</th><th>n_scores</th><th>Mean</th><th>Stddev</th><th>[min..max]</th><th>Disagreement</th>
  </tr></thead>
  <tbody>
{_render_top_disagreement(top_disagreement)}
  </tbody>
</table>

<h2>3. Replicate coverage table</h2>
<p class="meta"><code>replicates_done</code> counts distinct scored <code>replicate_seq</code> values, including baseline <code>0</code>; this report caps the display at the target of 3 samples per candidate.</p>
<table>
  <thead><tr>
    <th>Candidate cell_id</th><th>Lane</th><th>Model</th><th>replicates_done</th><th>current_mean</th><th>current_stddev</th>
  </tr></thead>
  <tbody>
{_render_coverage(coverage_rows)}
  </tbody>
</table>

<h2>4. Methodology</h2>
<p>Scorer-disagreement is the raw <code>max(score_value) - min(score_value)</code> span across all score rows for a cell, so it highlights cells where gates or judges disagree inside the current ledger. Replicate-variance is the standard deviation after repeated dispatches of the lane-boundary candidates selected near the pass/fail midpoint, and the coverage table shows which of those 42 cells have enough scored samples to trust that estimate. The headline variance floor aggregates every scored cell, not just candidates, and serves as the current noise estimate for the model fleet; mixed deterministic and LLM-judge scales should be read as variance flags rather than absolute grades.</p>

<h2>5. Links</h2>
<ul>
  <li><a href="index.html">Report index</a></li>
  <li><a href="matrix.html">Matrix heatmap</a></li>
  <li>Per-lane reports: {_render_link_list(lanes, "per-lane")}</li>
  <li>Per-model reports: {_render_link_list(models, "per-model", code=True)}</li>
</ul>

</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render the calibration v1 stability variance HTML report."
    )
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_PATH)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.db_path.exists():
        print(f"error: ledger not found: {args.db_path}")
        return 2
    if not args.candidates.exists():
        print(f"error: candidates JSON not found: {args.candidates}")
        return 2

    cell_stats = load_cell_stats(args.db_path)
    candidates = load_candidates(args.candidates)
    rendered = render_report(
        cell_stats=cell_stats,
        candidates=candidates,
        out_path=args.out,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")

    stddevs = [row.stddev for row in cell_stats]
    top_three = sorted(
        cell_stats,
        key=lambda row: (
            -row.scorer_disagreement,
            -row.stddev,
            row.lane,
            row.canonical_string,
            row.fixture_id,
        ),
    )[:3]
    print(f"wrote {args.out}")
    print(f"mean stddev: {_fmt(_mean(stddevs) if stddevs else 0.0)}")
    print(f"median stddev: {_fmt(median(stddevs) if stddevs else 0.0)}")
    print(f"p95 stddev: {_fmt(_percentile(stddevs, 95.0))}")
    print("top 3 disagreement cells:")
    for index, row in enumerate(top_three, start=1):
        print(
            f"{index}. {row.cell_id} "
            f"disagreement={_fmt(row.scorer_disagreement)} "
            f"mean={_fmt(row.mean)} stddev={_fmt(row.stddev)} "
            f"range=[{_fmt(row.score_min)}..{_fmt(row.score_max)}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run stability replicates for selected calibration cells."""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.calibration import run_wave, schema  # noqa: E402
from scripts.calibration.models import model_by_canonical  # noqa: E402
from scripts.calibration.run_cell import DEFAULT_DB_PATH, DEFAULT_OUTPUT_ROOT  # noqa: E402

DEFAULT_CANDIDATES_PATH = (
    REPO_ROOT / "calibration" / "v1" / "reports" / "stability-candidates.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT / "calibration" / "v1" / "reports" / "stability-replicates.json"
)


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_candidates(path: Path, max_cells: int) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_candidates = payload["candidates"] if isinstance(payload, dict) else payload
    candidates: list[dict[str, Any]] = []
    for candidate in raw_candidates:
        candidates.append(candidate)
        if len(candidates) >= max_cells:
            break
    return candidates


def _latest_dispatch_status(db_path: Path, cell_id: str) -> dict[str, Any]:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT dispatch_id, task_id, returncode, response_path
            FROM dispatches
            WHERE cell_id = ?
            ORDER BY dispatch_id DESC
            LIMIT 1
            """,
            (cell_id,),
        ).fetchone()
    if row is None:
        return {
            "dispatch_id": None,
            "task_id": None,
            "returncode": None,
            "response_path": None,
        }
    return {
        "dispatch_id": row["dispatch_id"],
        "task_id": row["task_id"],
        "returncode": row["returncode"],
        "response_path": row["response_path"],
    }


def _score_count(db_path: Path, cell_id: str, replicate_seq: int) -> int:
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM scores
            WHERE cell_id = ? AND replicate_seq = ?
            """,
            (cell_id, replicate_seq),
        ).fetchone()
    return int(row["count"])


def _spec_for_candidate(candidate: dict[str, Any], replicate_seq: int) -> run_wave.CellSpec:
    return run_wave.CellSpec(
        lane=str(candidate["lane"]),
        fixture_id=str(candidate["fixture_id"]),
        model=model_by_canonical(str(candidate["canonical_string"])),
        replicate_seq=replicate_seq,
    )


def _result_by_cell(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(result["cell_id"]): result for result in results if result.get("cell_id")}


def _run_candidates_once(
    *,
    candidates: list[dict[str, Any]],
    replicate_seq: int,
    db_path: Path,
    output_root: Path,
    timeout_s: int,
) -> dict[str, dict[str, Any]]:
    by_run_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_run_date[str(candidate["run_date"])].append(candidate)

    statuses: dict[str, dict[str, Any]] = {}
    for run_date, run_candidates in sorted(by_run_date.items()):
        cells = [
            _spec_for_candidate(candidate, replicate_seq)
            for candidate in run_candidates
        ]
        results = run_wave.run_wave(
            cells=cells,
            run_date=run_date,
            db_path=db_path,
            output_root=output_root,
            timeout_s=timeout_s,
            score=True,
        )
        results_by_cell = _result_by_cell(results)
        for candidate in run_candidates:
            cell_id = str(candidate["cell_id"])
            result = results_by_cell.get(cell_id)
            if result is None:
                statuses[cell_id] = {
                    "ok": False,
                    "reason": "missing run_wave result",
                    "replicate_seq": replicate_seq,
                }
                continue
            if not result.get("ok"):
                statuses[cell_id] = {
                    "ok": False,
                    "reason": str(result.get("error", "dispatch failed")),
                    "replicate_seq": replicate_seq,
                    "elapsed_s": result.get("elapsed_s"),
                }
                continue

            dispatch = _latest_dispatch_status(db_path, cell_id)
            returncode = dispatch["returncode"]
            score_count = _score_count(db_path, cell_id, replicate_seq)
            if returncode not in (None, 0):
                statuses[cell_id] = {
                    "ok": False,
                    "reason": f"dispatch returncode {returncode}",
                    "replicate_seq": replicate_seq,
                    "dispatch": dispatch,
                    "elapsed_s": result.get("elapsed_s"),
                }
                continue
            if not result.get("scored") or score_count == 0:
                statuses[cell_id] = {
                    "ok": False,
                    "reason": str(result.get("score_error", "scoring failed")),
                    "replicate_seq": replicate_seq,
                    "dispatch": dispatch,
                    "elapsed_s": result.get("elapsed_s"),
                    "score_count": score_count,
                }
                continue
            statuses[cell_id] = {
                "ok": True,
                "replicate_seq": replicate_seq,
                "dispatch": dispatch,
                "elapsed_s": result.get("elapsed_s"),
                "score_count": score_count,
            }
    return statuses


def run_replicates(
    *,
    candidates: list[dict[str, Any]],
    db_path: Path,
    output_root: Path,
    max_cells: int,
    replicates: int,
    timeout_s: int,
) -> dict[str, Any]:
    selected = candidates[:max_cells]
    skipped: dict[str, str] = {}
    completed: list[dict[str, Any]] = []

    for replicate_seq in range(1, replicates + 1):
        active = [
            candidate
            for candidate in selected
            if str(candidate["cell_id"]) not in skipped
        ]
        if not active:
            break

        logging.info(
            "replicate %s/%s: dispatching %s active cell(s)",
            replicate_seq,
            replicates,
            len(active),
        )
        first_attempt = _run_candidates_once(
            candidates=active,
            replicate_seq=replicate_seq,
            db_path=db_path,
            output_root=output_root,
            timeout_s=timeout_s,
        )

        retry = [
            candidate
            for candidate in active
            if not first_attempt.get(str(candidate["cell_id"]), {}).get("ok")
        ]
        retry_statuses: dict[str, dict[str, Any]] = {}
        if retry:
            logging.warning(
                "replicate %s: retrying %s failed cell(s) once",
                replicate_seq,
                len(retry),
            )
            retry_statuses = _run_candidates_once(
                candidates=retry,
                replicate_seq=replicate_seq,
                db_path=db_path,
                output_root=output_root,
                timeout_s=timeout_s,
            )

        for candidate in active:
            cell_id = str(candidate["cell_id"])
            status = retry_statuses.get(cell_id) or first_attempt.get(cell_id)
            if status and status.get("ok"):
                completed.append(
                    {
                        "cell_id": cell_id,
                        "lane": candidate["lane"],
                        "canonical_string": candidate["canonical_string"],
                        **status,
                    }
                )
                continue
            reason = str(status.get("reason", "unknown failure") if status else "no status")
            skipped[cell_id] = reason
            logging.warning(
                "skipping cell after replicate %s failure: %s (%s)",
                replicate_seq,
                cell_id,
                reason,
            )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "db_path": str(db_path.relative_to(REPO_ROOT) if db_path.is_relative_to(REPO_ROOT) else db_path),
        "max_cells": max_cells,
        "replicates": replicates,
        "selected_cells": len(selected),
        "completed_replicates": len(completed),
        "skipped_cells": [
            {"cell_id": cell_id, "reason": reason}
            for cell_id, reason in sorted(skipped.items())
        ],
        "completed": completed,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run calibration stability replicates from candidate JSON."
    )
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--max-cells", type=int, default=70)
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--timeout-s", type=int, default=1800)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    if args.max_cells < 1:
        print("error: --max-cells must be >= 1", file=sys.stderr)
        return 2
    if args.replicates < 1:
        print("error: --replicates must be >= 1", file=sys.stderr)
        return 2
    if not args.candidates.exists():
        print(f"error: candidates JSON not found: {args.candidates}", file=sys.stderr)
        return 2

    schema.init_db(args.db_path)
    candidates = load_candidates(args.candidates, args.max_cells)
    summary = run_replicates(
        candidates=candidates,
        db_path=args.db_path,
        output_root=args.output_root,
        max_cells=args.max_cells,
        replicates=args.replicates,
        timeout_s=args.timeout_s,
    )
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(summary, indent=2)
    args.summary_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if not summary["skipped_cells"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

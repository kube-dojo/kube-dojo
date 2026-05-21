"""Fire a calibration wave with at most one cell in flight per family.

Dispatch any (lane × model × fixture) cell tuple via one worker thread per
family; within a family, cells run sequentially (codex models share one
queue). Cells are scored as they complete; the ledger is the canonical
record. ``--smoke`` runs a single cell so the harness wiring can be validated
cheaply before the full sweep fires.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import string
import sys
import time
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from . import schema, score_cell
from .models import ANCHORS, LANES, CalibrationModel, Wave
from .run_cell import DEFAULT_DB_PATH, DEFAULT_OUTPUT_ROOT, REPO_ROOT, run_cell

# Lane -> fixture id for Wave C / D. Wave A and B happened to share the same
# fixtures per lane; we keep that contract here, swapping in the harder code-
# review / debugging fixtures designed in session 37 plus the two new lanes.
LANE_FIXTURES: dict[str, str] = {
    "code-writing": "parse-dependabot-cooldown",
    "code-review": "k8s-controller-leader-election",
    "content-writing-long": "kubedojo-rbac-module",
    "content-review": "flawed-module-rubric-review",
    "fact-check": "k8s-1-35-claims",
    "architecting": "kubedojo-review-override-rfc",
    "orchestrating": "multi-task-routing-brief",
    "debugging": "pod-pending-topology-mismatch",
    "refactoring": "check-site-health-refactor",
    "summarization": "session-34-handoff",
    "mcp-use": "define-the-word-in-uk",
    "harness-following": "inline-write-falco-module",
}


def _assert_lane_fixture_consistency() -> None:
    """Fail at module-load if LANES and LANE_FIXTURES diverge.

    Companion of ``score_cell._assert_lane_set_consistency``; together they
    catch the "added a lane but forgot one of the three lookups" regression
    before any cell dispatches.
    """
    lanes_in_models: set[str] = {str(lane) for lane in LANES}
    lanes_in_fixtures: set[str] = set(LANE_FIXTURES)
    if lanes_in_models != lanes_in_fixtures:
        missing_in_fixtures = lanes_in_models - lanes_in_fixtures
        missing_in_models = lanes_in_fixtures - lanes_in_models
        raise RuntimeError(
            "calibration lane drift: "
            f"LANES \\ LANE_FIXTURES = {sorted(missing_in_fixtures)}; "
            f"LANE_FIXTURES \\ LANES = {sorted(missing_in_models)}"
        )


_assert_lane_fixture_consistency()


@dataclass(frozen=True)
class CellSpec:
    lane: str
    fixture_id: str
    model: CalibrationModel
    replicate_seq: int = 0


def select_models(
    *,
    waves: Iterable[Wave],
    canonical_filter: Iterable[str] | None,
) -> list[CalibrationModel]:
    waves_set = set(waves)
    if canonical_filter:
        filter_set = set(canonical_filter)
        return [model for model in ANCHORS if model.canonical_string in filter_set]
    return [model for model in ANCHORS if model.wave in waves_set]


def build_cells(
    *,
    models: Iterable[CalibrationModel],
    lanes: Iterable[str],
) -> list[CellSpec]:
    cells = []
    for model in models:
        for lane in lanes:
            fixture = LANE_FIXTURES.get(lane)
            if not fixture:
                raise KeyError(f"no fixture mapping for lane {lane!r}")
            cells.append(CellSpec(lane=lane, fixture_id=fixture, model=model))
    return cells


def _dispatch_one(
    spec: CellSpec,
    *,
    run_date: str,
    db_path: Path,
    output_root: Path,
    timeout_s: int,
    score: bool,
) -> dict:
    started = time.monotonic()
    cell_id = schema.make_cell_id(
        lane=spec.lane,
        fixture_id=spec.fixture_id,
        canonical_string=spec.model.canonical_string,
        effort_requested=spec.model.effort_requested,
        run_date=run_date,
    )
    try:
        cell_id = run_cell(
            lane=spec.lane,
            canonical_string=spec.model.canonical_string,
            fixture_id=spec.fixture_id,
            run_date=run_date,
            db_path=db_path,
            output_root=output_root,
            timeout_s=timeout_s,
            replicate_seq=spec.replicate_seq,
        )
        elapsed = time.monotonic() - started
        scored = False
        if score:
            try:
                score_cell.score_cell(
                    cell_id=cell_id,
                    db_path=db_path,
                    replicate_seq=spec.replicate_seq,
                )
                scored = True
            except Exception as exc:  # noqa: BLE001 — scoring failure ≠ dispatch failure
                return {
                    "ok": True,
                    "cell_id": cell_id,
                    "lane": spec.lane,
                    "model": spec.model.canonical_string,
                    "family": spec.model.family,
                    "replicate_seq": spec.replicate_seq,
                    "elapsed_s": elapsed,
                    "scored": False,
                    "score_error": repr(exc),
                }
        return {
            "ok": True,
            "cell_id": cell_id,
            "lane": spec.lane,
            "model": spec.model.canonical_string,
            "family": spec.model.family,
            "replicate_seq": spec.replicate_seq,
            "elapsed_s": elapsed,
            "scored": scored,
        }
    except Exception as exc:  # noqa: BLE001 — record + continue
        return {
            "ok": False,
            "cell_id": None,
            "lane": spec.lane,
            "model": spec.model.canonical_string,
            "family": spec.model.family,
            "replicate_seq": spec.replicate_seq,
            "elapsed_s": time.monotonic() - started,
            "error": repr(exc),
        }


def preflight_probe(
    *,
    cells: list[CellSpec],
    probe_timeout_s: int = 90,
) -> list[dict]:
    """Probe one model per distinct adapter (provider_cli + agent_name).

    Burning ~$5 of API credit on a 60-min sweep before noticing that one
    adapter is broken is the failure mode this guards against. For each
    distinct adapter we dispatch a tiny prompt with a tight timeout and
    record the outcome. Caller decides whether to abort.
    """
    from .run_cell import build_dispatch_plan, dispatch_prompt

    seen: dict[tuple[str, str | None], CalibrationModel] = {}
    for cell in cells:
        plan = build_dispatch_plan(cell.model)
        key = (cell.model.provider_cli, plan.agent_name)
        seen.setdefault(key, cell.model)

    print(
        f"preflight: probing {len(seen)} distinct adapter(s) "
        f"({probe_timeout_s}s timeout each)",
        flush=True,
    )

    results: list[dict] = []
    for (provider_cli, agent_name), model in seen.items():
        response_text = ""
        started = time.monotonic()
        try:
            result = dispatch_prompt(
                model,
                "Reply with the single word OK.",
                REPO_ROOT,
                probe_timeout_s,
            )
            response_text = (result.response or "").strip()
            lower_response = response_text.lower()
            if lower_response.rstrip(string.punctuation + string.whitespace) != "ok":
                raise RuntimeError(
                    "preflight probe expected an 'OK' response; got "
                    f"{response_text!r} from {model.canonical_string}"
                )
            results.append(
                {
                    "ok": True,
                    "provider_cli": provider_cli,
                    "agent_name": agent_name,
                    "model": model.canonical_string,
                    "elapsed_s": time.monotonic() - started,
                    "response_preview": response_text[:80],
                }
            )
            print(
                f"  [{provider_cli}/{agent_name or '-'}] "
                f"{model.canonical_string} ok {results[-1]['elapsed_s']:.1f}s",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001 — record + return
            results.append(
                {
                    "ok": False,
                    "provider_cli": provider_cli,
                    "agent_name": agent_name,
                    "model": model.canonical_string,
                    "elapsed_s": time.monotonic() - started,
                    "error": repr(exc),
                    "response_preview": response_text[:80],
                }
            )
            print(
                f"  [{provider_cli}/{agent_name or '-'}] "
                f"{model.canonical_string} FAIL: {exc!r}",
                flush=True,
            )
    return results


def run_wave(
    *,
    cells: list[CellSpec],
    run_date: str,
    db_path: Path,
    output_root: Path,
    timeout_s: int,
    max_parallel_per_family: int = 1,
    score: bool = True,
) -> list[dict]:
    """Dispatch cells with at most ``max_parallel_per_family`` in flight per family.

    The implementation uses one worker per family. Within a family, dispatches
    run sequentially; across families, they run in parallel.
    """
    schema.init_db(db_path)
    by_family: dict[str, list[CellSpec]] = defaultdict(list)
    for cell in cells:
        by_family[cell.model.family].append(cell)

    def _run_family(family_cells: list[CellSpec]) -> list[dict]:
        results: list[dict] = []
        for spec in family_cells:
            r = _dispatch_one(
                spec,
                run_date=run_date,
                db_path=db_path,
                output_root=output_root,
                timeout_s=timeout_s,
                score=score,
            )
            results.append(r)
            status = "ok" if r["ok"] else "FAIL"
            scored_marker = "[scored]" if r.get("scored") else ""
            print(
                f"  [{r['family']}] {spec.model.canonical_string} × {spec.lane} "
                f"{status} {r['elapsed_s']:.1f}s {scored_marker}",
                flush=True,
            )
        return results

    print(
        f"firing {len(cells)} cells across {len(by_family)} family lane(s) "
        f"(max parallel: {max_parallel_per_family} per family)",
        flush=True,
    )
    all_results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_parallel_per_family * len(by_family),
    ) as pool:
        futures = {
            pool.submit(_run_family, family_cells): family
            for family, family_cells in by_family.items()
        }
        for future in concurrent.futures.as_completed(futures):
            family = futures[future]
            try:
                family_results = future.result()
                all_results.extend(family_results)
                print(
                    f"family {family} done: "
                    f"{sum(1 for r in family_results if r['ok'])}/{len(family_results)} ok",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"family {family} crashed: {exc!r}", flush=True)
    return all_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a calibration wave")
    parser.add_argument(
        "--wave",
        choices=("A", "B", "C", "D"),
        action="append",
        help="Wave letter (repeatable). Ignored when --models is given.",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        help="Explicit canonical_string filter (overrides --wave).",
    )
    parser.add_argument(
        "--lanes",
        nargs="*",
        default=list(LANES),
        help=f"Lanes to dispatch (default: all {len(LANES)} lanes).",
    )
    parser.add_argument("--run-date", help="ISO date for the cell rows.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--timeout-s", type=int, default=1800)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Only dispatch the first cell in the resolved spec list.",
    )
    parser.add_argument(
        "--no-score",
        action="store_true",
        help="Skip in-line scoring; dispatch only.",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help=(
            "Skip the pre-flight adapter probe. Default is to probe each "
            "distinct (provider_cli, agent_name) pair with a 90s ceiling "
            "and abort if any fails. Use only when intentionally re-running "
            "a partial wave."
        ),
    )
    parser.add_argument(
        "--summary-jsonl",
        type=Path,
        help="Append a JSON object summary to this path after dispatch.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_date = args.run_date or schema.today_iso()

    if not args.wave and not args.models:
        print("error: pass --wave or --models", file=sys.stderr)
        return 2

    models = select_models(
        waves=args.wave or (),
        canonical_filter=args.models,
    )
    if not models:
        print("error: no models matched the filter", file=sys.stderr)
        return 2

    cells = build_cells(models=models, lanes=args.lanes)
    if args.smoke:
        cells = cells[:1]
    if not cells:
        print("error: no cells to run", file=sys.stderr)
        return 2

    if not args.skip_preflight and not args.smoke:
        probe_results = preflight_probe(cells=cells)
        failed = [r for r in probe_results if not r["ok"]]
        if failed:
            print(
                f"\npreflight: {len(failed)}/{len(probe_results)} adapter(s) "
                f"failed — aborting before any cell is dispatched. "
                f"Pass --skip-preflight to override.",
                file=sys.stderr,
            )
            for fail in failed:
                print(
                    f"  - {fail['provider_cli']}/{fail['agent_name'] or '-'} "
                    f"({fail['model']}): {fail.get('error', '?')}",
                    file=sys.stderr,
                )
            return 3
        print(
            f"preflight: {len(probe_results)}/{len(probe_results)} adapter(s) "
            "ok; opening full sweep.\n",
            flush=True,
        )

    results = run_wave(
        cells=cells,
        run_date=run_date,
        db_path=args.db_path,
        output_root=args.output_root,
        timeout_s=args.timeout_s,
        score=not args.no_score,
    )

    ok = sum(1 for r in results if r["ok"])
    print(f"\nwave summary: {ok}/{len(results)} ok", flush=True)
    if args.summary_jsonl:
        args.summary_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_jsonl.open("a", encoding="utf-8") as fp:
            fp.write(
                json.dumps(
                    {
                        "run_date": run_date,
                        "models": [m.canonical_string for m in models],
                        "lanes": list(args.lanes),
                        "cells_total": len(results),
                        "cells_ok": ok,
                        "results": results,
                    },
                    sort_keys=True,
                )
                + "\n",
            )
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

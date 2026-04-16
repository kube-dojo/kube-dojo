from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from migrate_v1_to_v2 import migrate_v1_to_v2
from v2_ab_test import run_ab_test
from .control_plane import (
    DEFAULT_BUDGETS_PATH,
    DEFAULT_DB_PATH,
    ControlPlane,
)
from .patch_worker import PatchWorker
from .preflight import run_preflight
from .review_worker import PATCH_MODEL, REVIEW_MODEL, ReviewWorker
from .write_worker import WRITE_MODEL, WriteWorker
from .watchdog import sweep_once, watch_forever


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Week 1 v2 pipeline control plane")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to .pipeline/v2.db")
    parser.add_argument(
        "--budgets",
        type=Path,
        default=DEFAULT_BUDGETS_PATH,
        help="Path to .pipeline/budgets.yaml",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    enqueue = subparsers.add_parser("enqueue", help="Enqueue a pending job")
    enqueue.add_argument("module_key")
    enqueue.add_argument("--phase", required=True)
    enqueue.add_argument("--model", required=True)
    enqueue.add_argument("--priority", type=int, default=100)
    enqueue.add_argument("--requested-calls", type=int, default=1)
    enqueue.add_argument("--estimated-usd", type=float, default=0.0)

    lease_next = subparsers.add_parser("lease-next", help="Lease the next pending job")
    lease_next.add_argument("worker_id")
    lease_next.add_argument("--model")
    lease_next.add_argument("--requested-calls", type=int)
    lease_next.add_argument("--estimated-usd", type=float)
    lease_next.add_argument("--lease-seconds", type=int, default=900)
    lease_next.add_argument("--json", action="store_true")

    complete = subparsers.add_parser("complete", help="Record usage and complete a lease")
    complete.add_argument("lease_id")
    complete.add_argument("--actual-calls", type=int, default=1)
    complete.add_argument("--actual-usd", type=float, default=0.0)
    complete.add_argument("--tokens-in", type=int, default=0)
    complete.add_argument("--tokens-out", type=int, default=0)

    status = subparsers.add_parser("status", help="Show pipeline status summary")
    status.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show", help="Inspect control-plane state")
    show_subparsers = show.add_subparsers(dest="show_command", required=True)
    show_budget = show_subparsers.add_parser("budget", help="Show current usage vs caps")
    show_budget.add_argument("--json", action="store_true")
    show_needs_human = show_subparsers.add_parser(
        "needs-human",
        help="Show modules dead-lettered for human intervention",
    )
    show_needs_human.add_argument("--json", action="store_true")
    show_flapping = show_subparsers.add_parser(
        "flapping",
        help="Show modules with more than three attempts",
    )
    show_flapping.add_argument("--json", action="store_true")

    recover_dead_letters = subparsers.add_parser(
        "recover-dead-letters",
        help="Requeue unresolved dead-letter modules after manual triage",
    )
    recover_dead_letters.add_argument("modules", nargs="*")
    recover_dead_letters.add_argument(
        "--phase",
        choices=("review", "write", "patch"),
        default="review",
        help="Phase to enqueue for recovered modules",
    )
    recover_dead_letters.add_argument("--priority", type=int, default=100)
    recover_dead_letters.add_argument("--dry-run", action="store_true")
    recover_dead_letters.add_argument("--json", action="store_true")

    budget = subparsers.add_parser("budget", help="Alias for show budget; also supports edits")
    budget.add_argument("--json", action="store_true")
    budget_subparsers = budget.add_subparsers(dest="budget_command")
    budget_set = budget_subparsers.add_parser("set", help="Set a model budget field")
    budget_set.add_argument("model")
    budget_set.add_argument("field")
    budget_set.add_argument("value")

    watchdog = subparsers.add_parser("watchdog", help="Manual watchdog controls")
    watchdog_subparsers = watchdog.add_subparsers(dest="watchdog_command", required=True)
    watchdog_subparsers.add_parser("sweep", help="Release expired leases once")
    watchdog_loop = watchdog_subparsers.add_parser("loop", help="Run the optional watchdog loop")
    watchdog_loop.add_argument("--interval-seconds", type=int, default=30)

    review_worker = subparsers.add_parser("review-worker", help="Run the Week 2 review worker")
    review_worker_subparsers = review_worker.add_subparsers(
        dest="review_worker_command",
        required=True,
    )
    review_worker_run = review_worker_subparsers.add_parser("run", help="Review one queued job")
    review_worker_run.add_argument("--worker-id", default="review-worker")
    review_worker_run.add_argument("--json", action="store_true")
    review_worker_loop = review_worker_subparsers.add_parser("loop", help="Run the review worker loop")
    review_worker_loop.add_argument("--worker-id", default="review-worker")
    review_worker_loop.add_argument("--sleep-seconds", type=float, default=5.0)

    patch_worker = subparsers.add_parser("patch-worker", help="Run the Week 3 patch worker")
    patch_worker_subparsers = patch_worker.add_subparsers(
        dest="patch_worker_command",
        required=True,
    )
    patch_worker_run = patch_worker_subparsers.add_parser("run", help="Patch one queued job")
    patch_worker_run.add_argument("--worker-id", default="patch-worker")
    patch_worker_run.add_argument("--json", action="store_true")
    patch_worker_loop = patch_worker_subparsers.add_parser("loop", help="Run the patch worker loop")
    patch_worker_loop.add_argument("--worker-id", default="patch-worker")
    patch_worker_loop.add_argument("--sleep-seconds", type=float, default=5.0)

    write_worker = subparsers.add_parser("write-worker", help="Run the Week 4 write worker")
    write_worker_subparsers = write_worker.add_subparsers(
        dest="write_worker_command",
        required=True,
    )
    write_worker_run = write_worker_subparsers.add_parser("run", help="Write one queued job")
    write_worker_run.add_argument("--worker-id", default="write-worker")
    write_worker_run.add_argument("--json", action="store_true")
    write_worker_loop = write_worker_subparsers.add_parser("loop", help="Run the write worker loop")
    write_worker_loop.add_argument("--worker-id", default="write-worker")
    write_worker_loop.add_argument("--sleep-seconds", type=float, default=5.0)

    migrate = subparsers.add_parser("migrate-v1", help="Migrate v1 state.yaml into v2.db")
    migrate.add_argument(
        "--state",
        type=Path,
        default=Path(".pipeline/state.yaml"),
        help="Path to v1 .pipeline/state.yaml",
    )
    migrate.add_argument("--dry-run", action="store_true")
    migrate.add_argument("--json", action="store_true")

    ab_test = subparsers.add_parser("ab-test", help="Compare v1 and v2 on a sample of review modules")
    ab_test.add_argument("--count", type=int, default=50)
    ab_test.add_argument("--modules")
    ab_test.add_argument("--state", type=Path, default=Path(".pipeline/state.yaml"))
    ab_test.add_argument("--seed", type=int, default=239)
    ab_test.add_argument("--max-iterations", type=int, default=24)
    ab_test.add_argument("--json", action="store_true")

    preflight = subparsers.add_parser("preflight", help="Run deterministic pre-flight checks")
    preflight.add_argument("module_path", type=Path)
    preflight.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    control_plane = ControlPlane(db_path=args.db, budgets_path=args.budgets)

    if args.command == "enqueue":
        job = control_plane.enqueue(
            args.module_key,
            phase=args.phase,
            model=args.model,
            priority=args.priority,
            requested_calls=args.requested_calls,
            estimated_usd=args.estimated_usd,
        )
        print(
            f"enqueued job {job.job_id} {job.module_key} "
            f"({job.phase}/{job.model}) idempotency_key={job.idempotency_key}"
        )
        return 0

    if args.command == "lease-next":
        lease = control_plane.lease_next_job(
            args.worker_id,
            model=args.model,
            requested_calls=args.requested_calls,
            estimated_usd=args.estimated_usd,
            lease_seconds=args.lease_seconds,
        )
        if args.json:
            print(json.dumps(lease.__dict__ if lease else None, indent=2, sort_keys=True))
        elif lease is None:
            print("no lease granted")
        else:
            print(
                f"leased job {lease.job_id} to {lease.worker_id} "
                f"(lease_id={lease.lease_id}, model={lease.model})"
            )
        return 0

    if args.command == "complete":
        inserted = control_plane.record_usage(
            args.lease_id,
            actual_calls=args.actual_calls,
            actual_usd=args.actual_usd,
            tokens_in=args.tokens_in,
            tokens_out=args.tokens_out,
        )
        print("usage recorded" if inserted else "usage already recorded")
        return 0

    if args.command == "status":
        return _show_status(args.db, json_output=args.json)

    if args.command == "recover-dead-letters":
        return _recover_dead_letters(
            control_plane,
            modules=args.modules,
            phase=args.phase,
            priority=args.priority,
            dry_run=args.dry_run,
            json_output=args.json,
        )

    if args.command == "show":
        if args.show_command == "budget":
            return _show_budget(control_plane, json_output=args.json)
        if args.show_command == "needs-human":
            return _show_needs_human(control_plane, json_output=args.json)
        if args.show_command == "flapping":
            return _show_flapping(control_plane, json_output=args.json)
        parser.error(f"Unhandled show command: {args.show_command}")

    if args.command == "budget":
        if args.budget_command == "set":
            control_plane.set_budget(args.model, args.field, _coerce_value(args.value))
            print(f"updated {args.model}.{args.field} -> {args.value}")
            return 0
        return _show_budget(control_plane, json_output=args.json)

    if args.command == "watchdog":
        if args.watchdog_command == "sweep":
            released = sweep_once(control_plane)
            print(f"released {released} expired lease(s)")
            return 0
        watch_forever(control_plane, interval_seconds=args.interval_seconds)
        return 0

    if args.command == "review-worker":
        worker = ReviewWorker(control_plane, worker_id=args.worker_id)
        if args.review_worker_command == "run":
            outcome = worker.run_once()
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": outcome.status,
                            "module_key": outcome.module_key,
                            "lease_id": outcome.lease_id,
                            "details": outcome.details,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            elif outcome.status == "idle":
                print("no review job available")
            else:
                print(f"{outcome.status}: {outcome.module_key}")
            return 0
        worker.loop_forever(sleep_seconds=args.sleep_seconds)
        return 0

    if args.command == "patch-worker":
        worker = PatchWorker(control_plane, worker_id=args.worker_id)
        if args.patch_worker_command == "run":
            outcome = worker.run_once()
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": outcome.status,
                            "module_key": outcome.module_key,
                            "lease_id": outcome.lease_id,
                            "details": outcome.details,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            elif outcome.status == "idle":
                print("no patch job available")
            else:
                print(f"{outcome.status}: {outcome.module_key}")
            return 0
        worker.loop_forever(sleep_seconds=args.sleep_seconds)
        return 0

    if args.command == "write-worker":
        worker = WriteWorker(control_plane, worker_id=args.worker_id)
        if args.write_worker_command == "run":
            outcome = worker.run_once()
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": outcome.status,
                            "module_key": outcome.module_key,
                            "lease_id": outcome.lease_id,
                            "details": outcome.details,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            elif outcome.status == "idle":
                print("no write job available")
            else:
                print(f"{outcome.status}: {outcome.module_key}")
            return 0
        worker.loop_forever(sleep_seconds=args.sleep_seconds)
        return 0

    if args.command == "migrate-v1":
        summary = migrate_v1_to_v2(
            control_plane,
            state_path=args.state,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        else:
            print(summary.render_text())
        return 0

    if args.command == "ab-test":
        report = run_ab_test(
            count=args.count,
            modules_filter=args.modules,
            state_path=args.state,
            budgets_path=args.budgets,
            seed=args.seed,
            max_iterations=args.max_iterations,
        )
        if args.json:
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        else:
            print(report.render_text())
        return 0

    if args.command == "preflight":
        result = run_preflight(args.module_path)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        else:
            print(f"Preflight {'PASS' if result.passed else 'FAIL'}: {args.module_path}")
            for finding in result.findings:
                icon = "PASS" if finding.passed else finding.severity
                print(f"[{icon}] {finding.id}: {finding.evidence}")
        return 0 if result.passed else 1

    parser.error(f"Unhandled command: {args.command}")
    return 1


def _show_status(db_path: Path, *, json_output: bool) -> int:
    report = _build_status_report(db_path)
    if json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    phase_rows = [(phase, report["counts"][phase]) for phase in report["phase_order"]]
    metric_rows = [
        ("total_modules", report["total_modules"]),
        ("convergence_rate", f"{report['convergence_rate']:.1f}%"),
        ("flapping_count", report["flapping_count"]),
        ("needs_human_count", report["needs_human_count"]),
    ]

    print(f"Pipeline status ({report['db_path']})")
    _print_table(("Phase", "Count"), phase_rows)
    print()
    _print_table(("Metric", "Value"), metric_rows)
    return 0


def _build_status_report(db_path: Path) -> dict[str, Any]:
    phase_order = [
        "pending_review",
        "pending_write",
        "pending_patch",
        "done",
        "dead_letter",
        "in_progress",
    ]
    counts = {phase: 0 for phase in phase_order}
    modules: set[str] = set()
    job_state_by_module: dict[str, dict[str, Any]] = {}
    event_types_by_module: dict[str, set[str]] = {}
    attempt_counts: dict[str, int] = {}
    dead_letter_rows: list[dict[str, Any]] = []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        job_rows = conn.execute(
            """
            SELECT module_key, phase, queue_state
            FROM jobs
            WHERE module_key IS NOT NULL
            ORDER BY id ASC
            """
        ).fetchall()
        event_rows = conn.execute(
            """
            SELECT id, module_key, type, payload_json, at
            FROM events
            WHERE module_key IS NOT NULL
            ORDER BY id ASC
            """
        ).fetchall()
    finally:
        conn.close()

    for row in job_rows:
        module_key = str(row["module_key"])
        phase = str(row["phase"])
        queue_state = str(row["queue_state"])
        modules.add(module_key)
        state = job_state_by_module.setdefault(
            module_key,
            {
                "pending_phases": set(),
                "has_leased": False,
                "has_failed": False,
                "has_completed": False,
            },
        )
        if queue_state == "pending":
            state["pending_phases"].add(phase)
        elif queue_state == "leased":
            state["has_leased"] = True
        elif queue_state == "failed":
            state["has_failed"] = True
        elif queue_state == "completed":
            state["has_completed"] = True

    for row in event_rows:
        module_key = str(row["module_key"])
        event_type = str(row["type"])
        modules.add(module_key)
        event_types_by_module.setdefault(module_key, set()).add(event_type)
        if event_type == "attempt_started":
            attempt_counts[module_key] = attempt_counts.get(module_key, 0) + 1
        if event_type in {"needs_human_intervention", "module_dead_lettered", "dead_letter_recovered"}:
            dead_letter_rows.append(
                {
                    "module_key": module_key,
                    "id": int(row["id"]),
                    "type": event_type,
                    "payload_json": str(row["payload_json"] or "{}"),
                    "at": int(row["at"]),
                }
            )

    unresolved_dead_letters = {
        row["module_key"]
        for row in _current_dead_letter_rows(dead_letter_rows)
    }

    for module_key in modules:
        job_state = job_state_by_module.get(module_key)
        event_types = event_types_by_module.get(module_key, set())
        counts[_module_status(job_state, event_types, dead_lettered=module_key in unresolved_dead_letters)] += 1

    total_modules = len(modules)
    done_count = counts["done"]
    convergence_rate = (done_count / total_modules * 100.0) if total_modules else 0.0
    flapping_count = sum(1 for attempts in attempt_counts.values() if attempts > 3)

    return {
        "db_path": str(db_path),
        "phase_order": phase_order,
        "counts": counts,
        "total_modules": total_modules,
        "convergence_rate": convergence_rate,
        "flapping_count": flapping_count,
        "needs_human_count": len(unresolved_dead_letters),
    }


def _module_status(
    job_state: dict[str, Any] | None,
    event_types: set[str],
    *,
    dead_lettered: bool,
) -> str:
    pending_phases = set(job_state["pending_phases"]) if job_state else set()
    has_leased = bool(job_state and job_state["has_leased"])
    has_completed = bool(job_state and job_state["has_completed"])

    if dead_lettered:
        return "dead_letter"
    if has_leased:
        return "in_progress"
    if "patch" in pending_phases:
        return "pending_patch"
    if pending_phases.intersection({"review", "check_pre"}):
        return "pending_review"
    if "write" in pending_phases:
        return "pending_write"
    if pending_phases:
        return "pending_review"
    if "done" in event_types or has_completed:
        return "done"
    return "pending_write"


def _print_table(headers: tuple[str, str], rows: list[tuple[str, Any]]) -> None:
    left_width = max(len(headers[0]), *(len(str(left)) for left, _ in rows))
    right_width = max(len(headers[1]), *(len(str(right)) for _, right in rows))
    print(f"{headers[0]:<{left_width}} | {headers[1]:>{right_width}}")
    print(f"{'-' * left_width}-+-{'-' * right_width}")
    for left, right in rows:
        print(f"{str(left):<{left_width}} | {str(right):>{right_width}}")


def _show_budget(control_plane: ControlPlane, *, json_output: bool) -> int:
    report = control_plane.budget_report()
    if json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"Budget report ({report['db_path']})")
    for row in report["rows"]:
        usd_cap = row["weekly_budget_usd_cap"]
        usd_cap_text = "n/a" if usd_cap is None else f"{usd_cap:.2f}"
        print(
            f"{row['model']}: active {row['active_leases']}/{row['max_concurrent']} | "
            f"hourly calls {row['hourly_calls_committed']}/{row['hourly_calls_cap']} | "
            f"weekly calls {row['weekly_calls_committed']}/{row['weekly_calls_cap']} | "
            f"weekly usd {row['weekly_budget_usd_committed']:.2f}/{usd_cap_text}"
        )
    if not report["rows"]:
        print("(no configured or observed models)")
    return 0


def _show_needs_human(control_plane: ControlPlane, *, json_output: bool) -> int:
    rows = _current_dead_letter_rows(
        [
            {
                "module_key": str(event["module_key"]),
                "id": int(event["id"]),
                "type": str(event["type"]),
                "payload_json": str(event["payload_json"] or "{}"),
                "at": int(event["at"]),
            }
            for event in (
                control_plane.iter_events("needs_human_intervention")
                + control_plane.iter_events("module_dead_lettered")
                + control_plane.iter_events("dead_letter_recovered")
            )
        ]
    )
    if json_output:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    if not rows:
        print("(no modules need human intervention)")
        return 0
    print("Needs human intervention")
    for row in rows:
        print(
            f"{row['module_key']}: {row['reason']} "
            f"(rewrite_attempts={row['rewrite_attempts']}, at={row['at']})"
        )
    return 0


def _recover_dead_letters(
    control_plane: ControlPlane,
    *,
    modules: list[str],
    phase: str,
    priority: int,
    dry_run: bool,
    json_output: bool,
) -> int:
    targets = _current_dead_letter_rows(
        [
            {
                "module_key": str(event["module_key"]),
                "id": int(event["id"]),
                "type": str(event["type"]),
                "payload_json": str(event["payload_json"] or "{}"),
                "at": int(event["at"]),
            }
            for event in (
                control_plane.iter_events("needs_human_intervention")
                + control_plane.iter_events("module_dead_lettered")
                + control_plane.iter_events("dead_letter_recovered")
            )
        ]
    )
    requested = set(modules)
    if requested:
        targets = [row for row in targets if row["module_key"] in requested]
    model = _model_for_phase(phase)
    results = []
    for row in targets:
        result = {
            "module_key": row["module_key"],
            "previous_reason": row["reason"],
            "requeue_phase": phase,
            "requeue_model": model,
            "dry_run": dry_run,
        }
        if not dry_run:
            control_plane.emit_event(
                "dead_letter_recovered",
                module_key=row["module_key"],
                payload={
                    "previous_reason": row["reason"],
                    "rewrite_attempts": row.get("rewrite_attempts"),
                    "requeue_phase": phase,
                    "requeue_model": model,
                },
            )
            job = control_plane.enqueue(
                row["module_key"],
                phase=phase,
                model=model,
                priority=priority,
            )
            result["job_id"] = job.job_id
        results.append(result)

    if json_output:
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0
    if not results:
        print("(no dead-letter modules selected)")
        return 0
    for row in results:
        suffix = " [dry-run]" if row["dry_run"] else ""
        print(
            f"recovered {row['module_key']} -> {row['requeue_phase']}/{row['requeue_model']}{suffix}"
        )
    return 0


def _show_flapping(control_plane: ControlPlane, *, json_output: bool) -> int:
    counts: dict[str, int] = {}
    for event in control_plane.iter_events("attempt_started"):
        module_key = str(event["module_key"])
        counts[module_key] = counts.get(module_key, 0) + 1
    rows = [
        {"module_key": module_key, "attempts": attempts}
        for module_key, attempts in sorted(counts.items())
        if attempts > 3
    ]
    if json_output:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    if not rows:
        print("(no flapping modules)")
        return 0
    print("Flapping modules")
    for row in rows:
        print(f"{row['module_key']}: {row['attempts']} attempts")
    return 0


def _current_dead_letter_rows(event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_dead_by_module: dict[str, dict[str, Any]] = {}
    latest_recovery_order: dict[str, tuple[int, int]] = {}
    for event in sorted(event_rows, key=lambda row: (int(row["at"]), int(row.get("id", 0)))):
        module_key = str(event["module_key"])
        event_type = str(event["type"])
        at = int(event["at"])
        event_id = int(event.get("id", 0))
        if event_type == "dead_letter_recovered":
            latest_recovery_order[module_key] = (at, event_id)
            continue
        if event_type not in {"needs_human_intervention", "module_dead_lettered"}:
            continue
        payload = json.loads(str(event["payload_json"] or "{}"))
        latest_dead_by_module[module_key] = {
            "module_key": module_key,
            "id": event_id,
            "reason": payload.get("reason"),
            "rewrite_attempts": payload.get("rewrite_attempts"),
            "at": at,
        }
    unresolved = [
        row
        for module_key, row in latest_dead_by_module.items()
        if latest_recovery_order.get(module_key, (-1, -1))
        < (int(row["at"]), int(row.get("id", 0)))
    ]
    return sorted(unresolved, key=lambda row: (row["module_key"], int(row["at"])))


def _model_for_phase(phase: str) -> str:
    if phase == "review":
        return REVIEW_MODEL
    if phase == "patch":
        return PATCH_MODEL
    return WRITE_MODEL


def _coerce_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


if __name__ == "__main__":
    raise SystemExit(main())

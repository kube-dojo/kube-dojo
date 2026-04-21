#!/usr/bin/env python3
"""Citation-pipeline autopilot: loop `run_section.py --auto-pick --only-uncited`.

Designed for "human triggered, walks away" operation. You give it an
end condition (max sections, wall-clock deadline, or both) and it
keeps processing the densest uncited section until the condition is
met or the queue is drained.

Each iteration is an independent run_section invocation — failures in
one section don't poison the loop, and the human can Ctrl-C between
sections without leaving bad state.

Usage:
    .venv/bin/python scripts/autopilot.py --max-sections 3
    .venv/bin/python scripts/autopilot.py --until-time 08:00
    .venv/bin/python scripts/autopilot.py --max-sections 5 --until-time 14:30
    .venv/bin/python scripts/autopilot.py --dry-run           # list the queue, don't run
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")
RUN_SECTION = str(SCRIPT_DIR / "run_section.py")
LOG_DIR = REPO_ROOT / ".pipeline" / "v3" / "autopilot"


def _parse_hhmm(value: str) -> dt.datetime:
    """HH:MM → next occurrence of that wall-clock time (today or tomorrow)."""
    hh, mm = value.split(":", 1)
    now = dt.datetime.now()
    target = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    return target


def _queue_preview(min_uncited: int) -> list[tuple[str, int, int]]:
    sys.path.insert(0, str(SCRIPT_DIR))
    from run_section import _candidate_sections  # type: ignore  # noqa: E402
    return _candidate_sections(min_uncited=min_uncited)


def _log_iteration(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{dt.date.today().isoformat()}.jsonl"
    import json
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _run_one_section(min_uncited: int) -> tuple[int, str]:
    """Invoke run_section with --auto-pick --only-uncited. Return
    (exit_code, section_picked_or_empty)."""
    cmd = [
        PYTHON,
        RUN_SECTION,
        "--auto-pick",
        "--only-uncited",
        f"--min-uncited={min_uncited}",
    ]
    print(f"→ running: {' '.join(cmd)}", flush=True)
    # Stream output live so the operator can tail progress. Capture
    # the tail for the autopilot log.
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Loop run_section.py --auto-pick until a stop condition is met.",
    )
    parser.add_argument(
        "--max-sections",
        type=int,
        default=None,
        help="Stop after this many sections have been processed.",
    )
    parser.add_argument(
        "--until-time",
        type=str,
        default=None,
        help="Stop when this wall-clock time (HH:MM, 24h) is reached.",
    )
    parser.add_argument(
        "--min-uncited",
        type=int,
        default=3,
        help="Sections with fewer uncited modules than this are ignored (default: 3).",
    )
    parser.add_argument(
        "--sleep-between",
        type=int,
        default=30,
        help="Seconds to pause between sections (default: 30). Gives Codex a break and lets the operator Ctrl-C cleanly.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the queue preview and exit without invoking the pipeline.",
    )
    args = parser.parse_args(argv)

    if args.max_sections is None and args.until_time is None and not args.dry_run:
        parser.error("specify at least one of --max-sections, --until-time, or --dry-run")

    deadline: dt.datetime | None = _parse_hhmm(args.until_time) if args.until_time else None

    print("== autopilot ==", flush=True)
    if args.max_sections is not None:
        print(f"  stop after {args.max_sections} section(s)", flush=True)
    if deadline is not None:
        print(f"  stop at {deadline.isoformat(sep=' ', timespec='minutes')}", flush=True)
    print(f"  min-uncited threshold: {args.min_uncited}", flush=True)

    queue = _queue_preview(args.min_uncited)
    print(f"→ queue head ({len(queue)} sections above threshold):", flush=True)
    for sec, uncited, total in queue[:10]:
        print(f"    {uncited:3d}/{total:<3d}  {sec}", flush=True)
    if args.dry_run:
        return 0

    processed = 0
    failures = 0
    while True:
        if args.max_sections is not None and processed >= args.max_sections:
            print(f"→ stop: processed {processed} sections", flush=True)
            break
        if deadline is not None and dt.datetime.now() >= deadline:
            print(f"→ stop: deadline {deadline.isoformat()} reached", flush=True)
            break

        iteration_start = time.time()
        rc, _ = _run_one_section(args.min_uncited)
        elapsed = round(time.time() - iteration_start, 1)
        _log_iteration({
            "iteration": processed + 1,
            "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
            "elapsed_s": elapsed,
            "exit_code": rc,
        })
        processed += 1
        if rc != 0:
            failures += 1
            print(f"✗ iteration {processed} exit={rc} ({elapsed}s) — continuing", flush=True)
        else:
            print(f"✓ iteration {processed} ok ({elapsed}s)", flush=True)

        # Recheck whether anything's left; pipeline auto-pick prints
        # "queue may be drained" with rc=0 when empty.
        remaining = _queue_preview(args.min_uncited)
        if not remaining:
            print("→ queue drained; stopping", flush=True)
            break

        if args.max_sections is not None and processed >= args.max_sections:
            continue  # break next loop iteration
        if deadline is not None and dt.datetime.now() >= deadline:
            continue

        if args.sleep_between > 0:
            print(f"  sleeping {args.sleep_between}s before next section", flush=True)
            time.sleep(args.sleep_between)

    print(f"== autopilot done: processed={processed} failures={failures} ==", flush=True)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Batch-run pipeline_v3 with per-module commits.

For each module key in --from-file, runs run_pipeline(), and if the
module file changed and status is 'clean' or 'residuals_queued' (both
are acceptable landings per session 7 policy), commits the change.

Writes progress to .pipeline/v3/batches/<label>.log (jsonl).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_v3 import run_pipeline, DOCS_ROOT, REPO_ROOT  # type: ignore  # noqa: E402

COMMITTABLE = {"clean", "residuals_queued"}


def file_changed(module_path: Path) -> bool:
    r = subprocess.run(
        ["git", "status", "--porcelain", "--", str(module_path)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return bool(r.stdout.strip())


def commit_module(module_key: str, module_path: Path, status: str) -> dict:
    rel = module_path.relative_to(REPO_ROOT).as_posix()
    add = subprocess.run(["git", "add", rel], cwd=REPO_ROOT,
                         capture_output=True, text=True, check=False)
    if add.returncode != 0:
        return {"committed": False, "error": f"git add failed: {add.stderr}"}
    msg = f"content(citations): apply v3 pipeline to {module_key}\n\nstatus={status}"
    cm = subprocess.run(["git", "commit", "-m", msg], cwd=REPO_ROOT,
                        capture_output=True, text=True, check=False)
    if cm.returncode != 0:
        return {"committed": False, "error": f"git commit failed: {cm.stderr}"}
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return {"committed": True, "sha": sha.stdout.strip()}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--from-file", required=True,
                   help="File with one module key per line (# comments ok)")
    p.add_argument("--label", required=True,
                   help="Short label for the log file (e.g. session-8-t1)")
    p.add_argument("--skip-research", action="store_true",
                   help="Skip Stage 1 (use when seed JSON already exists)")
    p.add_argument("--start", type=int, default=0,
                   help="Skip the first N keys (for resuming)")
    args = p.parse_args(argv)

    batch_path = Path(args.from_file)
    keys = [line.strip() for line in batch_path.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")]
    if args.start:
        keys = keys[args.start:]
    if not keys:
        print("no keys", file=sys.stderr)
        return 2

    log_path = Path(".pipeline/v3/batches") / f"{args.label}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    totals = {"n": len(keys), "done": 0, "clean": 0, "residuals": 0,
              "failed": 0, "committed": 0, "skipped_no_change": 0}

    with log_path.open("a", encoding="utf-8") as log_f:
        for i, key in enumerate(keys, 1):
            t0 = time.time()
            try:
                rec = run_pipeline(key, skip_research=args.skip_research)
                status = rec.get("status", "unknown")
            except Exception as exc:  # noqa: BLE001
                entry = {"i": i, "key": key, "status": "exception",
                         "err": f"{type(exc).__name__}:{exc}",
                         "elapsed_s": round(time.time() - t0, 1)}
                log_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                log_f.flush()
                totals["failed"] += 1
                print(json.dumps(entry, ensure_ascii=False), flush=True)
                continue

            module_path = DOCS_ROOT / f"{key}.md"
            commit_info: dict = {"committed": False, "reason": "unchecked"}
            if status in COMMITTABLE and module_path.exists() and file_changed(module_path):
                commit_info = commit_module(key, module_path, status)
            elif status in COMMITTABLE:
                commit_info = {"committed": False, "reason": "no_file_change"}
                totals["skipped_no_change"] += 1
            else:
                commit_info = {"committed": False, "reason": f"status={status}"}

            if commit_info.get("committed"):
                totals["committed"] += 1

            totals["done"] += 1
            if status == "clean":
                totals["clean"] += 1
            elif status == "residuals_queued":
                totals["residuals"] += 1
            else:
                totals["failed"] += 1

            entry = {"i": i, "key": key, "status": status,
                     "elapsed_s": round(time.time() - t0, 1),
                     "commit": commit_info,
                     "progress": f"{totals['done']}/{totals['n']}"}
            log_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            log_f.flush()
            print(json.dumps(entry, ensure_ascii=False), flush=True)

        final = {"summary": totals, "label": args.label}
        log_f.write(json.dumps(final, ensure_ascii=False) + "\n")

    print("---", flush=True)
    print(json.dumps(final, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

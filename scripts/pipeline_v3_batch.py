#!/usr/bin/env python3
"""Batch wrapper for pipeline_v3.

Runs `run_pipeline(module_key)` over a list of module keys, sequentially
(the bridge serializes Codex/Gemini dispatches anyway). Per-module run
records land in `.pipeline/v3/runs/`; this script writes a single
`batch_summary` line to stdout per module and a final aggregate.

Module keys can be passed as args or read from a file (one per line):

    python scripts/pipeline_v3_batch.py mod1 mod2 mod3
    python scripts/pipeline_v3_batch.py --from-file ztt-batch.txt
    python scripts/pipeline_v3_batch.py --from-file - < ztt-batch.txt

Each module-run inherits the v3 flags it doesn't override:
    --skip-research, --no-auto-apply, --gate-agent, --coherence-agent
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_v3 import run_pipeline  # type: ignore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Batch driver for pipeline_v3")
    p.add_argument("module_keys", nargs="*")
    p.add_argument("--from-file",
                   help="read module keys from FILE (one per line; '-' = stdin)")
    p.add_argument("--skip-research", action="store_true")
    p.add_argument("--no-auto-apply", action="store_true")
    p.add_argument("--gate-agent", default="codex", choices=["codex", "gemini"])
    p.add_argument("--coherence-agent", default="gemini", choices=["codex", "gemini"])
    p.add_argument("--stop-on-failure", action="store_true",
                   help="abort the batch on the first non-clean module")
    args = p.parse_args(argv)

    keys = list(args.module_keys)
    if args.from_file:
        text = sys.stdin.read() if args.from_file == "-" \
            else Path(args.from_file).read_text(encoding="utf-8")
        keys.extend(line.strip() for line in text.splitlines()
                    if line.strip() and not line.strip().startswith("#"))
    if not keys:
        p.error("no module keys provided (give args or --from-file)")

    aggregate = {"clean": 0, "residuals_queued": 0, "failed": 0, "modules": []}

    for i, key in enumerate(keys, 1):
        t0 = time.time()
        try:
            record = run_pipeline(
                key,
                skip_research=args.skip_research,
                auto_apply=not args.no_auto_apply,
                gate_agent_text=args.gate_agent,
                gate_agent_coherence=args.coherence_agent,
            )
        except Exception as exc:  # noqa: BLE001
            line = {"i": i, "module_key": key, "status": "exception",
                    "error": f"{type(exc).__name__}:{exc}",
                    "elapsed_s": round(time.time() - t0, 1)}
            print(json.dumps(line, ensure_ascii=False))
            aggregate["failed"] += 1
            aggregate["modules"].append(line)
            if args.stop_on_failure:
                break
            continue

        status = record.get("status", "unknown")
        line = {
            "i": i, "module_key": key, "status": status,
            "elapsed_s": round(time.time() - t0, 1),
            "overstatement_applied": len(
                record["auto_apply"]["overstatement"]["applied"]),
            "off_topic_deleted": len(
                record["auto_apply"]["off_topic_delete"]["applied"]),
            "queued_total": sum(
                len(v) for v in (record.get("queued_findings") or {}).values()),
            "human_review_path": record.get("_human_review_path"),
        }
        print(json.dumps(line, ensure_ascii=False))
        if status == "clean":
            aggregate["clean"] += 1
        elif status == "residuals_queued":
            aggregate["residuals_queued"] += 1
        else:
            aggregate["failed"] += 1
        aggregate["modules"].append(line)
        if args.stop_on_failure and status != "clean":
            break

    print("---")
    print(json.dumps({"summary": {k: v for k, v in aggregate.items() if k != "modules"},
                      "total": len(aggregate["modules"])},
                     indent=2, ensure_ascii=False))
    return 0 if aggregate["failed"] == 0 and aggregate["residuals_queued"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

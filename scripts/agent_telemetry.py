#!/usr/bin/env python3
"""Agent performance telemetry — outcome annotation + per-agent report (#1860).

`logs/smart_dispatch.jsonl` already auto-captures every dispatch (agent, model,
task_class, mode, elapsed, ok, response_chars) but carries NO quality signal.
This module adds the missing layer: the orchestrator's ground-check VERDICT per
dispatch, stored in `logs/agent_outcomes.jsonl` (gitignored, like the dispatch
log), joined back to the dispatch log on `task_id` for a per-agent rollup.

Usage::

    # after ground-checking a dispatch's output, record the outcome:
    python -m scripts.agent_telemetry annotate mlops-1.9-rev \\
        --activity review --role reviewer --outcome fabrication \\
        --module ai-ml-engineering/mlops/1.9-model-serving \\
        --note "claimed 'frameworks absent' — grep disproved (present 5-16x); discarded"

    # for a direct-CLI agent not in smart_dispatch.jsonl (e.g. grok), pass --agent:
    python -m scripts.agent_telemetry annotate grok-k8s-probe \\
        --agent grok --model grok-build --activity research --outcome clean

    # per-agent performance rollup:
    python -m scripts.agent_telemetry report
    python -m scripts.agent_telemetry report --agent deepseek
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

PRIMARY_REPO = Path(__file__).resolve().parent.parent
DISPATCH_LOG = PRIMARY_REPO / "logs" / "smart_dispatch.jsonl"
OUTCOME_LOG = PRIMARY_REPO / "logs" / "agent_outcomes.jsonl"

# Outcome vocabulary (the orchestrator's ground-check verdict on a dispatch):
#   clean       — output correct; review verdict held / findings real; no fabrication
#   partial     — mostly good but needed a fix-pass / had minor real issues
#   fabrication — invented content / review / tool-use provenance (the trust-killer)
#   overturned  — review verdict was wrong and was discarded / re-run
#   rejected_fp — raised >=1 false-positive finding that ground-check rejected
OUTCOMES = ("clean", "partial", "fabrication", "overturned", "rejected_fp")
ACTIVITIES = ("author", "review", "fix", "research", "mechanical")
# outcomes that count against trust when computing a "miss rate"
_MISS = {"fabrication", "overturned"}


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # tolerate a partially-written tail line
    return rows


def _dispatch_index() -> dict[str, dict]:
    """task_id -> most-recent dispatch record from smart_dispatch.jsonl."""
    idx: dict[str, dict] = {}
    for row in _load_jsonl(DISPATCH_LOG):
        tid = row.get("task_id")
        if tid:
            idx[tid] = row  # later rows win (most recent)
    return idx


def annotate(args: argparse.Namespace) -> int:
    disp = _dispatch_index().get(args.task_id, {})
    agent = args.agent or disp.get("agent")
    model = args.model or disp.get("model")
    if not agent:
        print(
            f"error: task_id '{args.task_id}' not found in {DISPATCH_LOG.name}; "
            "pass --agent (and --model) for a direct-CLI dispatch."
        )
        return 2
    record = {
        "ts": int(time.time()),
        "task_id": args.task_id,
        "agent": agent,
        "model": model,
        "task_class": disp.get("task_class"),
        "activity": args.activity,
        "role": args.role,
        "outcome": args.outcome,
        "module": args.module,
        "note": args.note,
        "session": args.session,
    }
    OUTCOME_LOG.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOME_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    print(f"recorded: {agent} ({model}) {args.activity}/{args.outcome} [{args.task_id}]")
    return 0


def _agent_stats(dispatches: list[dict], outcomes: list[dict]) -> dict[str, dict]:
    stats: dict[str, dict] = defaultdict(
        lambda: {
            "dispatches": 0,
            "empty_or_failed": 0,
            "elapsed_total": 0.0,
            "elapsed_n": 0,
            "by_class": defaultdict(int),
            "annotated": 0,
            "outcomes": defaultdict(int),
        }
    )
    for d in dispatches:
        a = d.get("agent")
        if not a:
            continue
        s = stats[a]
        s["dispatches"] += 1
        s["by_class"][d.get("task_class") or "?"] += 1
        if d.get("ok") is False or (d.get("response_chars") or 0) == 0:
            s["empty_or_failed"] += 1
        el = d.get("elapsed_s")
        if isinstance(el, (int, float)):
            s["elapsed_total"] += el
            s["elapsed_n"] += 1
    for o in outcomes:
        a = o.get("agent")
        if not a:
            continue
        s = stats[a]
        s["annotated"] += 1
        s["outcomes"][o.get("outcome") or "?"] += 1
    return stats


def _pct(n: int, d: int) -> str:
    return f"{(100.0 * n / d):.0f}%" if d else "—"


def report(args: argparse.Namespace) -> int:
    dispatches = _load_jsonl(DISPATCH_LOG)
    outcomes = _load_jsonl(OUTCOME_LOG)
    if args.since:
        dispatches = [d for d in dispatches if (d.get("ts") or 0) >= args.since]
        outcomes = [o for o in outcomes if (o.get("ts") or 0) >= args.since]
    stats = _agent_stats(dispatches, outcomes)
    agents = sorted(stats, key=lambda a: -stats[a]["dispatches"])
    if args.agent:
        agents = [a for a in agents if a == args.agent]

    print(f"Agent performance — {len(dispatches)} dispatches, {len(outcomes)} annotated outcomes")
    print("=" * 78)
    hdr = f"{'agent':<12}{'disp':>5}{'fail%':>7}{'avg_s':>7}{'annot':>6}{'miss%':>7}  outcomes"
    print(hdr)
    print("-" * 78)
    for a in agents:
        s = stats[a]
        avg = s["elapsed_total"] / s["elapsed_n"] if s["elapsed_n"] else 0.0
        miss = sum(s["outcomes"][k] for k in _MISS)
        oc = " ".join(f"{k}={v}" for k, v in sorted(s["outcomes"].items()))
        print(
            f"{a:<12}{s['dispatches']:>5}{_pct(s['empty_or_failed'], s['dispatches']):>7}"
            f"{avg:>7.0f}{s['annotated']:>6}{_pct(miss, s['annotated']):>7}  {oc}"
        )
    print("-" * 78)
    print("fail% = empty/errored dispatches · miss% = (fabrication+overturned)/annotated · "
          "annotate more to grow the signal")
    if args.agent and agents:
        s = stats[agents[0]]
        print(f"\n{agents[0]} by task_class: " +
              ", ".join(f"{k}={v}" for k, v in sorted(s["by_class"].items())))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Agent performance telemetry (#1860).")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("annotate", help="record a ground-check outcome for a dispatch")
    a.add_argument("task_id")
    a.add_argument("--activity", required=True, choices=ACTIVITIES)
    a.add_argument("--outcome", required=True, choices=OUTCOMES)
    a.add_argument("--role", choices=("author", "reviewer", "fixer"))
    a.add_argument("--module")
    a.add_argument("--agent", help="override (for direct-CLI agents not in the dispatch log)")
    a.add_argument("--model")
    a.add_argument("--note")
    a.add_argument("--session")
    a.set_defaults(func=annotate)

    r = sub.add_parser("report", help="per-agent performance rollup")
    r.add_argument("--agent")
    r.add_argument("--since", type=int, help="unix ts lower bound")
    r.set_defaults(func=report)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

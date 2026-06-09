#!/usr/bin/env python3
"""Agent performance telemetry — outcome annotation + per-agent report (#1860).

`logs/smart_dispatch.jsonl` already auto-captures every dispatch (agent, model,
task_class, mode, elapsed, ok, response_chars) but carries NO quality signal.
This module adds the missing layer: the orchestrator's ground-check VERDICT per
dispatch, stored in `logs/agent_outcomes.jsonl` (gitignored, like the dispatch
log), joined back to the dispatch log on `task_id`.

**Harness ⟂ model** (the durable-content decomposition): a dispatch lane pairs a
HARNESS (the runtime — hermes, cursor, codex, antigravity…) with a MODEL (the
brain — deepseek-v4-pro, gpt-5.5, gemini-3.1-pro…). The `--agent` slug is the
LANE; some lanes are bare harnesses, others are model-named lanes that run *on* a
harness (e.g. `deepseek` and `qwen` both run on `hermes`). Telemetry rolls up by
lane, by harness, and by model so you can tell a flaky harness from a weak model.

Usage::

    python -m scripts.agent_telemetry annotate mlops-1.9-rev \\
        --activity review --role reviewer --outcome fabrication \\
        --module ai-ml-engineering/mlops/1.9-model-serving --note "..."
    python -m scripts.agent_telemetry report            # by lane (default)
    python -m scripts.agent_telemetry report --by harness   # or: lane | model | all
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

OUTCOMES = ("clean", "partial", "fabrication", "overturned", "rejected_fp")
ACTIVITIES = ("author", "review", "fix", "research", "mechanical")
_MISS = {"fabrication", "overturned"}  # outcomes that count against trust

# Lane -> harness (the runtime a lane dispatches through), derived from the
# adapters: deepseek/qwen wrap `hermes`; cursor/opencode/codex/agy/gemini/claude
# are their own CLIs. A lane absent here == its own harness.
HARNESS_BY_LANE = {
    "deepseek": "hermes",       # hermes --provider deepseek
    "qwen": "hermes",           # hermes --provider openrouter (qwen)
    "hermes": "hermes",
    "opencode": "opencode",
    "cursor": "cursor",
    "codex": "codex",
    "claude": "claude-code",
    "agy": "antigravity",
    "gemini": "gemini-cli",
    "grok": "grok-cli",
}


def harness_of(lane: str | None) -> str:
    return HARNESS_BY_LANE.get(lane or "", lane or "?")


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


def _dispatch_index(dispatch_log: Path = DISPATCH_LOG) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for row in _load_jsonl(dispatch_log):
        tid = row.get("task_id")
        if tid:
            idx[tid] = row  # most recent wins
    return idx


def _group(dispatches: list[dict], outcomes: list[dict], keyfn) -> dict[str, dict]:
    """Group dispatch + outcome rows under keyfn(row). keyfn accepts either a
    dispatch row or an outcome row (both carry `agent` and `model`)."""
    g: dict[str, dict] = defaultdict(
        lambda: {
            "dispatches": 0,
            "empty_or_failed": 0,
            "elapsed_total": 0.0,
            "elapsed_n": 0,
            "by_class": defaultdict(int),
            "models": set(),
            "annotated": 0,
            "outcomes": defaultdict(int),
        }
    )
    for d in dispatches:
        k = keyfn(d)
        if not k:
            continue
        s = g[k]
        s["dispatches"] += 1
        s["by_class"][d.get("task_class") or "?"] += 1
        if d.get("model"):
            s["models"].add(d["model"])
        if d.get("ok") is False or (d.get("response_chars") or 0) == 0:
            s["empty_or_failed"] += 1
        el = d.get("elapsed_s")
        if isinstance(el, (int, float)):
            s["elapsed_total"] += el
            s["elapsed_n"] += 1
    for o in outcomes:
        k = keyfn(o)
        if not k:
            continue
        s = g[k]
        s["annotated"] += 1
        s["outcomes"][o.get("outcome") or "?"] += 1
    return g


def _agent_stats(dispatches: list[dict], outcomes: list[dict]) -> dict[str, dict]:
    """Per-lane stats (grouped by the dispatch `agent` slug). Stable for tests."""
    return _group(dispatches, outcomes, lambda r: r.get("agent"))


def _rows_from_group(group: dict[str, dict], key_name: str) -> list[dict]:
    rows = []
    for k in sorted(group, key=lambda x: -group[x]["dispatches"]):
        s = group[k]
        miss = sum(s["outcomes"].get(m, 0) for m in _MISS)
        row = {
            key_name: k,
            "models": sorted(s["models"]),
            "dispatches": s["dispatches"],
            "empty_or_failed": s["empty_or_failed"],
            "fail_pct": round(100 * s["empty_or_failed"] / s["dispatches"], 1) if s["dispatches"] else None,
            "avg_elapsed_s": round(s["elapsed_total"] / s["elapsed_n"], 1) if s["elapsed_n"] else None,
            "annotated": s["annotated"],
            "miss": miss,
            "miss_pct": round(100 * miss / s["annotated"], 1) if s["annotated"] else None,
            "outcomes": dict(sorted(s["outcomes"].items())),
            "by_class": dict(sorted(s["by_class"].items())),
        }
        # Only the lane view carries a separate harness field; for the by_harness
        # view the group key already IS the harness (avoid a key collision).
        if key_name == "lane":
            row["harness"] = harness_of(k)
        rows.append(row)
    return rows


def build_agent_telemetry(repo_root: Path | None = None, *, since: int | None = None) -> dict:
    """JSON-serializable rollup used by both the CLI report and the API."""
    dl = (repo_root / "logs" / "smart_dispatch.jsonl") if repo_root else DISPATCH_LOG
    ol = (repo_root / "logs" / "agent_outcomes.jsonl") if repo_root else OUTCOME_LOG
    dispatches = _load_jsonl(dl)
    outcomes = _load_jsonl(ol)
    if since:
        dispatches = [d for d in dispatches if (d.get("ts") or 0) >= since]
        outcomes = [o for o in outcomes if (o.get("ts") or 0) >= since]
    return {
        "generated_at": int(time.time()),
        "dispatch_total": len(dispatches),
        "annotated_total": len(outcomes),
        "lanes": _rows_from_group(_group(dispatches, outcomes, lambda r: r.get("agent")), "lane"),
        "by_harness": _rows_from_group(_group(dispatches, outcomes, lambda r: harness_of(r.get("agent"))), "harness"),
        "by_model": _rows_from_group(_group(dispatches, outcomes, lambda r: r.get("model")), "model"),
    }


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
        "harness": harness_of(agent),
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
    print(f"recorded: {agent}/{harness_of(agent)} ({model}) {args.activity}/{args.outcome} [{args.task_id}]")
    return 0


def _print_table(title: str, key_name: str, rows: list[dict]) -> None:
    print(f"\n{title}")
    print("-" * 86)
    extra = "harness" if key_name == "lane" else "models"
    print(f"{key_name:<11}{extra:<14}{'disp':>5}{'fail%':>7}{'avg_s':>7}{'annot':>6}{'miss%':>7}  outcomes")
    for r in rows:
        side = (r["harness"] or "?") if key_name == "lane" else ",".join(r["models"])[:13]
        oc = " ".join(f"{k}={v}" for k, v in r["outcomes"].items())
        fail = f"{r['fail_pct']}%" if r["fail_pct"] is not None else "—"
        miss = f"{r['miss_pct']}%" if r["miss_pct"] is not None else "—"
        avg = round(r["avg_elapsed_s"]) if r["avg_elapsed_s"] is not None else 0
        print(
            f"{str(r[key_name]):<11}{side:<14}{r['dispatches']:>5}{fail:>7}{avg:>7}"
            f"{r['annotated']:>6}{miss:>7}  {oc}"
        )


def report(args: argparse.Namespace) -> int:
    data = build_agent_telemetry(since=args.since)
    print(f"Agent performance — {data['dispatch_total']} dispatches, "
          f"{data['annotated_total']} annotated outcomes")
    print("=" * 86)
    by = args.by
    if by in ("lane", "all"):
        _print_table("BY LANE (what you dispatch to)", "lane", data["lanes"])
    if by in ("harness", "all"):
        _print_table("BY HARNESS (the runtime)", "harness", data["by_harness"])
    if by in ("model", "all"):
        _print_table("BY MODEL (the brain)", "model", data["by_model"])
    print("-" * 86)
    print("fail% = empty/errored dispatches · miss% = (fabrication+overturned)/annotated")
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

    r = sub.add_parser("report", help="performance rollup")
    r.add_argument("--by", choices=("lane", "harness", "model", "all"), default="lane")
    r.add_argument("--since", type=int, help="unix ts lower bound")
    r.set_defaults(func=report)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

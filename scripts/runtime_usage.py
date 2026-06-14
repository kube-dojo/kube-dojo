"""Runtime dispatch usage telemetry from ``logs/smart_dispatch.jsonl`` (#1973 P3).

Read-only rollups over smart_dispatch records: calls, ok/failed counts, elapsed
latency — no token/cost fields (those are not captured in the dispatch log).
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from telemetry_store import _percentile_ms

_dispatch_log_override: Path | None = None


def dispatch_log_path(repo_root: Path) -> Path:
    if _dispatch_log_override is not None:
        return _dispatch_log_override
    return repo_root / "logs" / "smart_dispatch.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _dispatch_ts(record: dict[str, Any]) -> int | None:
    ts = record.get("ts")
    if isinstance(ts, (int, float)):
        return int(ts)
    if isinstance(ts, str) and ts.strip():
        text = ts.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return int(parsed.timestamp())
        except ValueError:
            return None
    return None


def _is_failed(record: dict[str, Any]) -> bool:
    return record.get("ok") is False or (record.get("response_chars") or 0) == 0


def _elapsed_values(records: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for record in records:
        elapsed = record.get("elapsed_s")
        if isinstance(elapsed, (int, float)):
            values.append(float(elapsed))
    return values


def _agent_bucket(records: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for record in records if _is_failed(record))
    calls = len(records)
    ok = calls - failed
    elapsed = _elapsed_values(records)
    models = sorted({str(record["model"]) for record in records if record.get("model")})
    by_class: dict[str, int] = defaultdict(int)
    for record in records:
        by_class[str(record.get("task_class") or "?")] += 1
    mean_elapsed = round(sum(elapsed) / len(elapsed), 3) if elapsed else None
    p95_elapsed = round(_percentile_ms([int(round(v * 1000)) for v in elapsed], 0.95) / 1000, 3) if elapsed else None
    return {
        "calls": calls,
        "ok": ok,
        "failed": failed,
        "rate_failed": round(failed / calls, 4) if calls else 0.0,
        "mean_elapsed_s": mean_elapsed,
        "p95_elapsed_s": p95_elapsed,
        "models": models,
        "by_class": dict(sorted(by_class.items())),
    }


def _totals_from_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    bucket = _agent_bucket(records)
    return {
        "calls": bucket["calls"],
        "ok": bucket["ok"],
        "failed": bucket["failed"],
        "rate_failed": bucket["rate_failed"],
        "mean_elapsed_s": bucket["mean_elapsed_s"],
    }


def load_dispatch_records(
    repo_root: Path,
    *,
    days: int | None = None,
    agent: str | None = None,
    task_class: str | None = None,
) -> list[dict[str, Any]]:
    records = _load_jsonl(dispatch_log_path(repo_root))
    window_days = min(max(1, int(days)), 30) if days is not None else None
    cutoff = int(time.time()) - window_days * 86400 if window_days is not None else None

    filtered: list[dict[str, Any]] = []
    for record in records:
        ts = _dispatch_ts(record)
        if cutoff is not None and (ts is None or ts < cutoff):
            continue
        if agent and record.get("agent") != agent:
            continue
        if task_class and record.get("task_class") != task_class:
            continue
        filtered.append(record)
    return filtered


def build_runtime_usage_payload(
    repo_root: Path,
    *,
    days: int = 7,
    agent: str | None = None,
    task_class: str | None = None,
) -> dict[str, Any]:
    window_days = min(max(1, int(days)), 30)
    records = load_dispatch_records(
        repo_root,
        days=window_days,
        agent=agent,
        task_class=task_class,
    )

    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        agent_name = str(record.get("agent") or "?")
        by_agent[agent_name].append(record)

    agents: list[dict[str, Any]] = []
    for agent_name in sorted(by_agent, key=lambda name: -len(by_agent[name])):
        bucket = _agent_bucket(by_agent[agent_name])
        agents.append({"agent": agent_name, **bucket})

    return {
        "generated_at": int(time.time()),
        "days": window_days,
        "agent_filter": agent,
        "task_class_filter": task_class,
        "totals": _totals_from_records(records),
        "agents": agents,
    }


def build_runtime_recent_payload(
    repo_root: Path,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    record_limit = min(max(1, int(limit)), 500)
    records = _load_jsonl(dispatch_log_path(repo_root))
    summaries: list[dict[str, Any]] = []
    for record in records:
        ts = _dispatch_ts(record)
        summaries.append(
            {
                "ts": ts if ts is not None else record.get("ts"),
                "agent": record.get("agent"),
                "model": record.get("model"),
                "task_class": record.get("task_class"),
                "ok": record.get("ok"),
                "elapsed_s": record.get("elapsed_s"),
                "task_id": record.get("task_id"),
            }
        )
    summaries.sort(key=lambda item: item.get("ts") or 0, reverse=True)
    return {
        "generated_at": int(time.time()),
        "records": summaries[:record_limit],
    }

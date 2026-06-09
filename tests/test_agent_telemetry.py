"""Unit tests for agent_telemetry report aggregation (#1860)."""
from __future__ import annotations

from agent_telemetry import _agent_stats


def test_agent_stats_joins_dispatches_and_outcomes() -> None:
    dispatches = [
        {"task_id": "d1", "agent": "deepseek", "task_class": "review", "ok": True,
         "response_chars": 5000, "elapsed_s": 200.0},
        {"task_id": "d2", "agent": "deepseek", "task_class": "review", "ok": True,
         "response_chars": 6000, "elapsed_s": 100.0},
        {"task_id": "d3", "agent": "deepseek", "task_class": "draft", "ok": False,
         "response_chars": 0, "elapsed_s": 10.0},
        {"task_id": "c1", "agent": "codex", "task_class": "review", "ok": True,
         "response_chars": 3000, "elapsed_s": 300.0},
    ]
    outcomes = [
        {"task_id": "d1", "agent": "deepseek", "outcome": "fabrication"},
        {"task_id": "d2", "agent": "deepseek", "outcome": "clean"},
        {"task_id": "c1", "agent": "codex", "outcome": "clean"},
    ]
    stats = _agent_stats(dispatches, outcomes)

    ds = stats["deepseek"]
    assert ds["dispatches"] == 3
    assert ds["empty_or_failed"] == 1          # d3 (ok False + 0 chars)
    assert ds["annotated"] == 2
    assert ds["outcomes"]["fabrication"] == 1
    assert ds["outcomes"]["clean"] == 1
    assert ds["by_class"]["review"] == 2
    assert ds["by_class"]["draft"] == 1
    # avg elapsed over the 3 dispatches = (200+100+10)/3
    assert round(ds["elapsed_total"] / ds["elapsed_n"], 1) == 103.3

    cx = stats["codex"]
    assert cx["dispatches"] == 1
    assert cx["empty_or_failed"] == 0
    assert cx["outcomes"]["clean"] == 1


def test_agent_stats_handles_empty() -> None:
    assert _agent_stats([], []) == {}

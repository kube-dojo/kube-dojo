from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline_v2.control_plane import ControlPlane
from pipeline_v2.review_worker import (
    CHECK_PRE_MODEL,
    DEEP_CHECK_IDS,
    REVIEW_FALLBACK_MODEL,
    REVIEW_MODEL,
    ReviewWorker,
)


GOOD_MODULE = """---
title: Review Worker Test
slug: /review-worker-test
sidebar:
  order: 1
---

# Review Worker Test

This module explains why review workers should run deterministic checks first.

## Learning Outcomes

- Explain the pre-flight gate.
- Understand review model routing.

## Content

Avoid deprecated APIs and keep the prose emoji free.
"""


def _write_budgets(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "models": {
                    REVIEW_MODEL: {
                        "max_concurrent": 2,
                        "weekly_calls": 200,
                        "hourly_calls": 50,
                        "weekly_budget_usd": 40.0,
                        "cooldown_after_rate_limit": 300,
                    }
                },
                "defaults": {
                    "max_concurrent": 1,
                    "weekly_calls": 25,
                    "hourly_calls": 10,
                    "weekly_budget_usd": 5.0,
                    "cooldown_after_rate_limit": 300,
                    "weekly_window": "rolling_7d",
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _make_control_plane(tmp_path: Path) -> ControlPlane:
    budgets_path = tmp_path / ".pipeline" / "budgets.yaml"
    db_path = tmp_path / ".pipeline" / "v2.db"
    _write_budgets(budgets_path)
    return ControlPlane(repo_root=tmp_path, db_path=db_path, budgets_path=budgets_path)


def _write_module(tmp_path: Path, name: str = "module-1.1-review-worker.md") -> Path:
    module_path = tmp_path / "docs" / name
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(GOOD_MODULE, encoding="utf-8")
    return module_path


def _completed_process(cmd: list[str], *, returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)


def _preflight_side_effect(*args, **kwargs):
    cmd = args[0]
    if cmd[:2] == ["npx", "markdownlint-cli2"]:
        return _completed_process(cmd)
    if cmd[:1] == ["yamllint"]:
        return _completed_process(cmd)
    raise AssertionError(f"Unexpected subprocess call: {cmd}")


def _simple_response(check_id: str, *, passed: bool = True) -> str:
    return json.dumps(
        {
            "verdict": "APPROVE" if passed else "REJECT",
            "checks": [
                {
                    "id": check_id,
                    "passed": passed,
                    "evidence": f"{check_id} {'ok' if passed else 'failed'}",
                    "fix_hint": "" if passed else f"Fix {check_id}",
                    "line_range": [1, 1],
                }
            ],
            "feedback": f"{check_id} {'passed' if passed else 'failed'}",
        }
    )


def _deep_response(
    *,
    cov: bool = True,
    depth: bool = True,
    why: bool = True,
    fact_check: bool = True,
    fact_evidence: str | None = None,
) -> str:
    checks = [
        {
            "id": "COV",
            "passed": cov,
            "evidence": "coverage ok" if cov else "coverage gap",
            "fix_hint": "" if cov else "Cover every learning outcome",
            "line_range": [2, 4],
        },
        {
            "id": "DEPTH",
            "passed": depth,
            "evidence": "depth ok" if depth else "missing operational nuance",
            "fix_hint": "" if depth else "Add practitioner-grade nuance",
            "line_range": [5, 8],
        },
        {
            "id": "WHY",
            "passed": why,
            "evidence": "why ok" if why else "missing rationale",
            "fix_hint": "" if why else "Explain the rationale for design choices",
            "line_range": [9, 10],
        },
        {
            "id": "FACT_CHECK",
            "passed": fact_check,
            "evidence": fact_evidence or ("facts verified" if fact_check else "could not verify current facts"),
            "fix_hint": "" if fact_check else "Verify claims against current live sources",
            "line_range": [11, 12],
        },
    ]
    return json.dumps(
        {
            "verdict": "APPROVE" if all(item["passed"] for item in checks) else "REJECT",
            "checks": checks,
            "feedback": "deep checks passed" if all(item["passed"] for item in checks) else "deep checks failed",
        }
    )


def _fetch_rows(db_path: Path, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def test_preflight_markdownlint_failure_skips_llm_and_enqueues_patch(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    control_plane.enqueue(str(module_path.relative_to(tmp_path)), phase="review", model=REVIEW_MODEL)
    dispatch = Mock()
    worker = ReviewWorker(control_plane, dispatch_fn=dispatch)

    def failing_subprocess(*args, **kwargs):
        cmd = args[0]
        if cmd[:2] == ["npx", "markdownlint-cli2"]:
            return _completed_process(
                cmd,
                returncode=1,
                stdout=f"{module_path}:12 MD032/blanks-around-lists Lists should be surrounded by blank lines",
            )
        return _completed_process(cmd)

    with patch("pipeline_v2.preflight.subprocess.run", side_effect=failing_subprocess), patch(
        "pipeline_v2.preflight._resolve_link_statuses",
        return_value={},
    ):
        outcome = worker.run_once()

    assert outcome.status == "preflight_failed"
    dispatch.assert_not_called()
    failed_event = control_plane.iter_events("check_failed")[-1]
    payload = json.loads(failed_event["payload_json"])
    assert payload["source"] == "preflight"
    assert payload["checks"][0]["id"] == "MARKDOWNLINT"
    queued_patch = _fetch_rows(
        control_plane.db_path,
        "SELECT phase, queue_state FROM jobs WHERE phase = 'patch'",
    )
    assert len(queued_patch) == 1
    assert queued_patch[0]["queue_state"] == "pending"


def test_preflight_pass_dispatches_llm_review(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    control_plane.enqueue(str(module_path.relative_to(tmp_path)), phase="review", model=REVIEW_MODEL)
    dispatch = Mock(
        side_effect=[
            (True, _simple_response("PRES")),
            (True, _simple_response("NO_EMOJI")),
            (True, _simple_response("K8S_API")),
            (True, _deep_response()),
        ]
    )
    worker = ReviewWorker(control_plane, dispatch_fn=dispatch)

    with patch("pipeline_v2.preflight.subprocess.run", side_effect=_preflight_side_effect), patch(
        "pipeline_v2.preflight._resolve_link_statuses",
        return_value={},
    ):
        outcome = worker.run_once()

    assert outcome.status == "approved"
    assert dispatch.call_count == 4


def test_malformed_json_retries_once_then_attempt_failed(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    control_plane.enqueue(str(module_path.relative_to(tmp_path)), phase="review", model=REVIEW_MODEL)
    dispatch = Mock(side_effect=[(True, "not json"), (True, "still not json")])
    worker = ReviewWorker(control_plane, dispatch_fn=dispatch)

    with patch("pipeline_v2.preflight.subprocess.run", side_effect=_preflight_side_effect), patch(
        "pipeline_v2.preflight._resolve_link_statuses",
        return_value={},
    ):
        outcome = worker.run_once()

    assert outcome.status == "attempt_failed"
    assert dispatch.call_count == 2
    failed_event = control_plane.iter_events("attempt_failed")[-1]
    payload = json.loads(failed_event["payload_json"])
    assert payload["reason"] == "malformed_json"
    assert control_plane.fetch_value("SELECT COUNT(*) FROM jobs WHERE phase = 'patch'") == 0


def test_review_usage_limit_falls_back_to_gpt_5_4(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    control_plane.enqueue(str(module_path.relative_to(tmp_path)), phase="review", model=REVIEW_MODEL)
    dispatch = Mock(
        side_effect=[
            (True, "ERROR: You've hit your usage limit for GPT-5.3-Codex-Spark."),
            (True, _simple_response("PRES")),
            (True, _simple_response("NO_EMOJI")),
            (True, _simple_response("K8S_API")),
            (True, _deep_response()),
        ]
    )
    worker = ReviewWorker(control_plane, dispatch_fn=dispatch)

    with patch("pipeline_v2.preflight.subprocess.run", side_effect=_preflight_side_effect), patch(
        "pipeline_v2.preflight._resolve_link_statuses",
        return_value={},
    ):
        outcome = worker.run_once()

    assert outcome.status == "approved"
    models = [call.kwargs["model"] for call in dispatch.call_args_list]
    assert models == [
        REVIEW_MODEL,
        REVIEW_FALLBACK_MODEL,
        REVIEW_FALLBACK_MODEL,
        REVIEW_FALLBACK_MODEL,
        REVIEW_FALLBACK_MODEL,
    ]


def test_review_worker_enforces_review_outcomes(tmp_path):
    cases = [
        ("approved", [_simple_response("PRES"), _simple_response("NO_EMOJI"), _simple_response("K8S_API"), _deep_response()], "check_pre", "APPROVE", None),
        ("rejected", [_simple_response("PRES", passed=False), _simple_response("NO_EMOJI"), _simple_response("K8S_API"), _deep_response()], "patch", "REJECT", "PRES"),
        ("rejected", [_simple_response("PRES"), _simple_response("NO_EMOJI"), _simple_response("K8S_API"), _deep_response(fact_evidence="unverified: could not confirm Kubernetes 1.99 claim")], "patch", "REJECT", "FACT_CHECK"),
    ]
    for i, (status, responses, phase, verdict, failed_check) in enumerate(cases):
        case_root = tmp_path / f"case-{i}"
        control_plane = _make_control_plane(case_root)
        module_path = _write_module(case_root)
        control_plane.enqueue(str(module_path.relative_to(case_root)), phase="review", model=REVIEW_MODEL)
        worker = ReviewWorker(control_plane, dispatch_fn=Mock(side_effect=[(True, r) for r in responses]))
        with patch("pipeline_v2.preflight.subprocess.run", side_effect=_preflight_side_effect), patch(
            "pipeline_v2.preflight._resolve_link_statuses",
            return_value={},
        ):
            outcome = worker.run_once()
        assert outcome.status == status
        payload = json.loads(control_plane.iter_events("check_passed" if phase == "check_pre" else "check_failed")[-1]["payload_json"])
        assert payload["verdict"] == verdict
        if failed_check:
            assert payload["failed_checks"][0]["id"] == failed_check
        if failed_check == "FACT_CHECK":
            assert json.loads(control_plane.iter_events("fact_check_unverified")[-1]["payload_json"])["unverified_claims"][0]["id"] == "FACT_CHECK"
        queued = _fetch_rows(control_plane.db_path, "SELECT phase, model, queue_state FROM jobs WHERE phase = ?", (phase,))
        assert len(queued) == 1
        assert queued[0]["queue_state"] == "pending"
        if phase == "check_pre":
            assert queued[0]["model"] == CHECK_PRE_MODEL


def test_three_simple_dispatches_then_one_deep(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    control_plane.enqueue(str(module_path.relative_to(tmp_path)), phase="review", model=REVIEW_MODEL)
    dispatch = Mock(
        side_effect=[
            (True, _simple_response("PRES")),
            (True, _simple_response("NO_EMOJI")),
            (True, _simple_response("K8S_API")),
            (True, _deep_response()),
        ]
    )
    worker = ReviewWorker(control_plane, dispatch_fn=dispatch)

    with patch("pipeline_v2.preflight.subprocess.run", side_effect=_preflight_side_effect), patch(
        "pipeline_v2.preflight._resolve_link_statuses",
        return_value={},
    ):
        worker.run_once()

    models = [call.kwargs["model"] for call in dispatch.call_args_list]
    assert models == [REVIEW_MODEL] * 4
    prompts = [call.args[0] for call in dispatch.call_args_list]
    for check_id, prompt in zip(("PRES", "NO_EMOJI", "K8S_API"), prompts[:3]):
        assert f"check_id={check_id}" in prompt or check_id in prompt
    assert "COV" in prompts[3] and "FACT_CHECK" in prompts[3]


def test_fact_check_is_deep_check():
    assert "FACT_CHECK" in DEEP_CHECK_IDS


def test_review_worker_completes_lease_and_records_usage(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    control_plane.enqueue(str(module_path.relative_to(tmp_path)), phase="review", model=REVIEW_MODEL)
    dispatch = Mock(
        side_effect=[
            (True, _simple_response("PRES")),
            (True, _simple_response("NO_EMOJI")),
            (True, _simple_response("K8S_API")),
            (True, _deep_response()),
        ]
    )
    worker = ReviewWorker(control_plane, dispatch_fn=dispatch)

    with patch("pipeline_v2.preflight.subprocess.run", side_effect=_preflight_side_effect), patch(
        "pipeline_v2.preflight._resolve_link_statuses",
        return_value={},
    ):
        outcome = worker.run_once()

    assert outcome.status == "approved"
    assert control_plane.fetch_value("SELECT COUNT(*) FROM reservations") == 0
    assert control_plane.fetch_value("SELECT COUNT(*) FROM active_leases") == 0
    assert control_plane.fetch_value("SELECT COUNT(*) FROM usage") == 1
    assert control_plane.fetch_value(
        "SELECT actual_calls FROM usage ORDER BY id DESC LIMIT 1",
    ) == 4
    assert control_plane.fetch_value(
        "SELECT queue_state FROM jobs WHERE phase = 'review' ORDER BY id ASC LIMIT 1",
    ) == "completed"

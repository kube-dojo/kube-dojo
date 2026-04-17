from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import Mock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline_v2.control_plane import ControlPlane
from pipeline_v2.patch_worker import PatchWorker
from pipeline_v2.review_worker import PATCH_MODEL, REVIEW_MODEL
from pipeline_v2.write_worker import WRITE_MODEL


MODULE_TEXT = """---
title: Patch Worker Test
slug: /patch-worker-test
sidebar:
  order: 1
---

# Patch Worker Test

## Learning Outcomes

- Explain targeted patching.
- Recognize rewrite escalation.

## Content

Paragraph A explains the initial concept.
Paragraph B needs more depth.
Paragraph C explains the operational tradeoff.
Paragraph D closes the lesson.
"""


def _write_budgets(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "models": {
                    PATCH_MODEL: {
                        "max_concurrent": 2,
                        "weekly_calls": 200,
                        "hourly_calls": 50,
                        "weekly_budget_usd": 40.0,
                        "cooldown_after_rate_limit": 300,
                    },
                    REVIEW_MODEL: {
                        "max_concurrent": 2,
                        "weekly_calls": 200,
                        "hourly_calls": 50,
                        "weekly_budget_usd": 40.0,
                        "cooldown_after_rate_limit": 300,
                    },
                    WRITE_MODEL: {
                        "max_concurrent": 2,
                        "weekly_calls": 200,
                        "hourly_calls": 50,
                        "weekly_budget_usd": 40.0,
                        "cooldown_after_rate_limit": 300,
                    },
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


def _write_module(tmp_path: Path, name: str = "module-1.1-patch-worker.md") -> Path:
    module_path = tmp_path / "docs" / name
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(MODULE_TEXT, encoding="utf-8")
    return module_path


def _fetch_rows(db_path: Path, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def _patch_response(edits: list[dict], *, feedback: str = "applied") -> str:
    return json.dumps({"edits": edits, "feedback": feedback})


def _seed_patch_job(
    control_plane: ControlPlane,
    module_key: str,
    *,
    failed_checks: list[dict],
    feedback: str = "Targeted edits required.",
) -> None:
    control_plane.emit_event(
        "check_failed",
        module_key=module_key,
        payload={
            "verdict": "REJECT",
            "failed_checks": failed_checks,
            "feedback": feedback,
        },
    )
    control_plane.enqueue(module_key, phase="patch", model=PATCH_MODEL)


def _failed_check(check_id: str, line_range: list[int]) -> dict:
    return {
        "id": check_id,
        "passed": False,
        "evidence": f"{check_id} failed",
        "fix_hint": f"Fix {check_id}",
        "line_range": line_range,
    }


def _seed_patch_attempts(control_plane: ControlPlane, module_key: str, count: int) -> None:
    for _ in range(count):
        control_plane.emit_event(
            "attempt_started",
            module_key=module_key,
            payload={"phase": "patch", "worker_id": "seed"},
        )


def _seed_rewrite_attempts(control_plane: ControlPlane, module_key: str, count: int) -> None:
    for index in range(count):
        control_plane.emit_event(
            "rewrite_escalated",
            module_key=module_key,
            payload={"phase": "patch", "reasons": [f"seed-{index}"]},
        )


def test_patch_applies_all_edits_and_reenqueues_review(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("DEPTH", [14, 14])],
    )
    dispatch = Mock(
        return_value=(
            True,
            _patch_response(
                [
                    {
                        "type": "replace",
                        "find": "Paragraph B needs more depth.",
                        "new": "Paragraph B now adds operational depth and a concrete failure mode.",
                        "reason": "Address DEPTH failure",
                    }
                ]
            ),
        )
    )
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "patched"
    assert "operational depth" in module_path.read_text(encoding="utf-8")
    queued_review = _fetch_rows(
        control_plane.db_path,
        "SELECT phase, model, queue_state FROM jobs WHERE phase = 'review' AND queue_state = 'pending'",
    )
    assert len(queued_review) == 1
    assert queued_review[0]["model"] == REVIEW_MODEL


def test_patch_uses_sliced_content_not_full_module(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = tmp_path / "docs" / "module-1.2-large-patch-worker.md"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Large Patch Worker Test", ""]
    target_line_text = "Paragraph 45 target anchor."
    top_outside = "Paragraph 01 outside slice sentinel."
    bottom_outside = "Paragraph 90 outside slice sentinel."
    for index in range(1, 91):
        if index == 1:
            lines.append(top_outside)
        elif index == 45:
            lines.append(target_line_text)
        elif index == 90:
            lines.append(bottom_outside)
        else:
            lines.append(f"Paragraph {index:02d}.")
    module_text = "\n".join(lines) + "\n"
    module_path.write_text(module_text, encoding="utf-8")
    module_key = str(module_path.relative_to(tmp_path))
    target_line = module_text.splitlines().index(target_line_text) + 1
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("DEPTH", [target_line, target_line])],
    )
    dispatch = Mock(
        return_value=(
            True,
            _patch_response(
                [
                    {
                        "type": "replace",
                        "find": target_line_text,
                        "new": "Paragraph 45 target anchor with added operational depth.",
                        "reason": "Address DEPTH failure",
                    }
                ]
            ),
        )
    )
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "patched"
    prompt = dispatch.call_args.args[0]
    assert target_line_text in prompt
    assert top_outside not in prompt
    assert bottom_outside not in prompt


def test_patch_partial_apply_escalates_without_writing_file(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    original = module_path.read_text(encoding="utf-8")
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("WHY", [15, 15])],
    )
    dispatch = Mock(
        return_value=(
            True,
            _patch_response(
                [
                    {
                        "type": "replace",
                        "find": "Paragraph C explains the operational tradeoff.",
                        "new": "Paragraph C explains the operational tradeoff and why the choice matters.",
                        "reason": "Address WHY failure",
                    },
                    {
                        "type": "replace",
                        "find": "Paragraph Z missing anchor.",
                        "new": "This anchor does not exist.",
                        "reason": "Bad anchor",
                    },
                ]
            ),
        )
    )
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "rewrite_escalated"
    assert module_path.read_text(encoding="utf-8") == original
    assert len(control_plane.iter_events("rewrite_escalated")) == 1
    assert control_plane.count_events_for_module(module_key, "patch_apply_failed") == 0


def test_patch_zero_percent_apply_emits_patch_apply_failed_and_escalates(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("PRES", [13, 13])],
    )
    dispatch = Mock(
        return_value=(
            True,
            _patch_response(
                [
                    {
                        "type": "replace",
                        "find": "Missing anchor entirely.",
                        "new": "Cannot apply this.",
                        "reason": "Broken anchor",
                    }
                ]
            ),
        )
    )
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "rewrite_escalated"
    assert len(control_plane.iter_events("patch_apply_failed")) == 1
    assert len(control_plane.iter_events("rewrite_escalated")) == 1


def test_more_than_three_dispersed_ranges_escalates_before_dispatch(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[
            _failed_check("COV", [10, 10]),
            _failed_check("DEPTH", [14, 14]),
            _failed_check("WHY", [15, 15]),
            _failed_check("PRES", [16, 16]),
        ],
    )
    dispatch = Mock()
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "rewrite_escalated"
    dispatch.assert_not_called()
    payload = json.loads(control_plane.iter_events("rewrite_escalated")[-1]["payload_json"])
    assert "dispersed_ranges>3" in payload["reasons"]


def test_escalation_enqueues_write_job(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[
            _failed_check("COV", [10, 10]),
            _failed_check("DEPTH", [14, 14]),
            _failed_check("WHY", [15, 15]),
            _failed_check("PRES", [16, 16]),
        ],
    )
    worker = PatchWorker(control_plane, dispatch_fn=Mock())

    outcome = worker.run_once()

    assert outcome.status == "rewrite_escalated"
    queued_write = _fetch_rows(
        control_plane.db_path,
        "SELECT phase, model, queue_state FROM jobs WHERE phase = 'write' ORDER BY id DESC",
    )
    assert len(queued_write) == 1
    assert queued_write[0]["model"] == WRITE_MODEL
    assert queued_write[0]["queue_state"] == "pending"


def test_more_than_two_patch_attempts_escalates_before_dispatch(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("DEPTH", [14, 14])],
    )
    _seed_patch_attempts(control_plane, module_key, 2)
    dispatch = Mock()
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "rewrite_escalated"
    dispatch.assert_not_called()
    payload = json.loads(control_plane.iter_events("rewrite_escalated")[-1]["payload_json"])
    assert "patch_attempts>2" in payload["reasons"]


def test_patch_attempts_counter_resets_after_rewrite(tmp_path):
    """Regression: lifetime patch_attempts counter caused immediate escalation
    on the first patch attempt of any post-rewrite cycle, breaking convergence."""
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    # Round 1 already exhausted: 3 patch attempts followed by a rewrite escalation.
    _seed_patch_attempts(control_plane, module_key, 3)
    _seed_rewrite_attempts(control_plane, module_key, 1)
    # Fresh write completed; round 2 starts now.
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("DEPTH", [14, 14])],
    )
    dispatch = Mock(
        return_value=(
            True,
            _patch_response(
                [
                    {
                        "type": "replace",
                        "find": "Paragraph B needs more depth.",
                        "new": "Paragraph B now adds operational depth.",
                        "reason": "DEPTH",
                    }
                ]
            ),
        )
    )
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "patched", (
        f"Expected first patch attempt of round 2 to dispatch, got {outcome.status}"
    )
    dispatch.assert_called_once()


def test_patch_degraded_counter_resets_after_rewrite(tmp_path):
    """Regression: lifetime patch_degraded counter caused immediate escalation
    on the first patch attempt of any post-rewrite cycle."""
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    control_plane.emit_event(
        "patch_degraded",
        module_key=module_key,
        payload={"reason": "round 1 patch introduced regression"},
    )
    _seed_rewrite_attempts(control_plane, module_key, 1)
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("DEPTH", [14, 14])],
    )
    dispatch = Mock(
        return_value=(
            True,
            _patch_response(
                [
                    {
                        "type": "replace",
                        "find": "Paragraph B needs more depth.",
                        "new": "Paragraph B now adds operational depth.",
                        "reason": "DEPTH",
                    }
                ]
            ),
        )
    )
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "patched"
    dispatch.assert_called_once()


def test_patch_degraded_event_escalates_before_dispatch(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("WHY", [15, 15])],
    )
    control_plane.emit_event(
        "patch_degraded",
        module_key=module_key,
        payload={"reason": "introduced new issue"},
    )
    dispatch = Mock()
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "rewrite_escalated"
    dispatch.assert_not_called()
    payload = json.loads(control_plane.iter_events("rewrite_escalated")[-1]["payload_json"])
    assert "patch_degraded" in payload["reasons"]


def test_more_than_three_rewrite_attempts_dead_letters_module(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[
            _failed_check("COV", [10, 10]),
            _failed_check("DEPTH", [14, 14]),
            _failed_check("WHY", [15, 15]),
            _failed_check("PRES", [16, 16]),
        ],
    )
    _seed_rewrite_attempts(control_plane, module_key, 3)
    dispatch = Mock()
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "needs_human_intervention"
    dispatch.assert_not_called()
    assert len(control_plane.iter_events("needs_human_intervention")) == 1
    assert len(control_plane.iter_events("module_dead_lettered")) == 1
    assert control_plane.fetch_value(
        "SELECT queue_state FROM jobs WHERE phase = 'patch' ORDER BY id DESC LIMIT 1"
    ) == "failed"


def test_malformed_response_releases_lease_for_retry(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("DEPTH", [14, 14])],
    )
    dispatch = Mock(side_effect=[(True, "not json"), (True, "still not json")])
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "retry_scheduled"
    assert control_plane.fetch_value(
        "SELECT queue_state FROM jobs WHERE phase = 'patch' ORDER BY id DESC LIMIT 1"
    ) == "pending"
    assert control_plane.fetch_value("SELECT COUNT(*) FROM active_leases") == 0
    assert control_plane.fetch_value("SELECT COUNT(*) FROM reservations") == 0
    assert control_plane.fetch_value("SELECT COUNT(*) FROM usage") == 0
    payload = json.loads(control_plane.iter_events("job_released")[-1]["payload_json"])
    assert payload["reason"] == "malformed_patch_response"


def test_requires_reorganization_feedback_escalates_before_dispatch(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("COV", [10, 12])],
        feedback="This module requires reorganization before targeted edits will converge.",
    )
    dispatch = Mock()
    worker = PatchWorker(control_plane, dispatch_fn=dispatch)

    outcome = worker.run_once()

    assert outcome.status == "rewrite_escalated"
    dispatch.assert_not_called()
    payload = json.loads(control_plane.iter_events("rewrite_escalated")[-1]["payload_json"])
    assert "feedback_requires_reorganization" in payload["reasons"]


def test_repeated_exceptions_dead_letter(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    module_path = _write_module(tmp_path)
    module_key = str(module_path.relative_to(tmp_path))
    _seed_patch_job(
        control_plane,
        module_key,
        failed_checks=[_failed_check("DEPTH", [14, 14])],
    )
    for _ in range(2):
        control_plane.emit_event(
            "attempt_failed",
            module_key=module_key,
            payload={"phase": "patch", "reason": "worker_error", "error": "seeded"},
        )
    worker = PatchWorker(control_plane, dispatch_fn=Mock(side_effect=RuntimeError("boom")))

    outcome = worker.run_once()

    assert outcome.status == "needs_human_intervention"
    assert control_plane.fetch_value(
        "SELECT queue_state FROM jobs WHERE phase = 'patch' ORDER BY id DESC LIMIT 1"
    ) == "failed"
    payload = json.loads(control_plane.iter_events("needs_human_intervention")[-1]["payload_json"])
    assert payload["reason"] == "patch_worker_repeated_exception"
    assert len(control_plane.iter_events("module_dead_lettered")) == 1

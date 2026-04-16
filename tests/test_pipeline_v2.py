from __future__ import annotations

import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline_v2.cli import main as pipeline_main
from pipeline_v2.cli import _build_status_report
from pipeline_v2.control_plane import ControlPlane
from pipeline_v2.watchdog import sweep_once


def _write_budgets(
    path: Path,
    *,
    max_concurrent: int = 2,
    kill_switch_policy: str = "CLAUDE_ONLY_PAUSE",
    models: dict[str, dict[str, object]] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    configured_models = {
        "claude-sonnet-4-6": {
            "cooldown_after_rate_limit": 600,
            "hourly_calls": 50,
            "max_concurrent": max_concurrent,
            "weekly_budget_usd": 40.0,
            "weekly_calls": 200,
        }
    }
    if models:
        configured_models.update(models)
    path.write_text(
        yaml.safe_dump(
            {
                "kill_switch_policy": kill_switch_policy,
                "models": configured_models,
                "defaults": {
                    "max_concurrent": 1,
                    "hourly_calls": 10,
                    "weekly_calls": 25,
                    "weekly_budget_usd": 5.0,
                    "cooldown_after_rate_limit": 300,
                    "weekly_window": "rolling_7d",
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _make_control_plane(
    tmp_path: Path,
    *,
    max_concurrent: int = 2,
    kill_switch_policy: str = "CLAUDE_ONLY_PAUSE",
    models: dict[str, dict[str, object]] | None = None,
) -> ControlPlane:
    budgets_path = tmp_path / ".pipeline" / "budgets.yaml"
    db_path = tmp_path / ".pipeline" / "v2.db"
    _write_budgets(
        budgets_path,
        max_concurrent=max_concurrent,
        kill_switch_policy=kill_switch_policy,
        models=models,
    )
    return ControlPlane(repo_root=tmp_path, db_path=db_path, budgets_path=budgets_path)


def _fetch_one(db_path: Path, sql: str, params: tuple = ()) -> sqlite3.Row:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(sql, params).fetchone()
        assert row is not None
        return row
    finally:
        conn.close()


def test_enqueue_defaults_to_one_requested_call(tmp_path):
    control_plane = _make_control_plane(tmp_path)

    # This test uses the real default at the API boundary rather than an
    # explicit argument to cover the Week 1 default reservation behavior.
    job = control_plane.enqueue(
        "docs/module-a.md",
        phase="review",
        model="claude-sonnet-4-6",
    )

    assert job.requested_calls == 1


def test_token_buffer_20_percent_applied(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    control_plane.enqueue(
        "docs/module-a.md",
        phase="review",
        model="claude-sonnet-4-6",
        estimated_usd=0.2,
    )

    lease = control_plane.lease_next_job(
        "worker-1",
        requested_calls=3,
        estimated_usd=1.75,
    )

    assert lease is not None
    assert lease.requested_calls == 3
    assert lease.estimated_usd == 1.75
    reservation = _fetch_one(
        control_plane.db_path,
        "SELECT reserved_calls, reserved_usd FROM reservations WHERE lease_id = ?",
        (lease.lease_id,),
    )
    assert reservation["reserved_calls"] == 3
    assert reservation["reserved_usd"] == 2.1


def test_idempotency_key_stable_across_releases_and_usage_is_deduped(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    job = control_plane.enqueue(
        "docs/module-b.md",
        phase="patch",
        model="claude-sonnet-4-6",
    )
    first_lease = control_plane.lease_next_job("worker-1")
    assert first_lease is not None
    assert control_plane.release_lease(first_lease.lease_id, reason="manual-retry") is True

    second_lease = control_plane.lease_next_job("worker-2")
    assert second_lease is not None
    assert first_lease.idempotency_key == second_lease.idempotency_key == job.idempotency_key

    assert control_plane.record_usage(second_lease.lease_id, actual_usd=0.44) is True
    assert control_plane.record_usage(second_lease.lease_id, actual_usd=0.44) is False
    assert control_plane.fetch_value("SELECT COUNT(*) FROM usage") == 1


def test_max_concurrent_only_allows_one_live_lease(tmp_path):
    control_plane = _make_control_plane(tmp_path, max_concurrent=1)
    control_plane.enqueue("docs/module-1.md", phase="review", model="claude-sonnet-4-6")
    control_plane.enqueue("docs/module-2.md", phase="review", model="claude-sonnet-4-6")

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda idx: control_plane.lease_next_job(f"worker-{idx}"), [1, 2]))

    granted = [lease for lease in results if lease is not None]
    assert len(granted) == 1
    blocked_events = control_plane.iter_events("dispatch_blocked_budget")
    assert blocked_events


def test_watchdog_sweep_once_releases_expired_leases(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    control_plane.enqueue("docs/module-c.md", phase="review", model="claude-sonnet-4-6")
    lease = control_plane.lease_next_job("worker-1", lease_seconds=120)
    assert lease is not None

    conn = sqlite3.connect(control_plane.db_path)
    try:
        conn.execute(
            "UPDATE active_leases SET expires_at = CAST(strftime('%s','now') AS INTEGER) - 5"
        )
        conn.execute(
            "UPDATE jobs SET lease_expires_at = CAST(strftime('%s','now') AS INTEGER) - 5"
        )
        conn.commit()
    finally:
        conn.close()

    assert sweep_once(control_plane) == 1
    assert control_plane.fetch_value("SELECT COUNT(*) FROM reservations") == 0
    assert control_plane.fetch_value(
        "SELECT queue_state FROM jobs WHERE id = ?",
        (lease.job_id,),
    ) == "pending"
    release_event = control_plane.iter_events("job_released")[-1]
    assert json.loads(release_event["payload_json"])["reason"] == "lease_expired"


def test_malformed_budget_file_falls_back_to_last_good_config_and_records_event(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    control_plane.enqueue("docs/module-d.md", phase="review", model="claude-sonnet-4-6")
    lease = control_plane.lease_next_job("worker-1")
    assert lease is not None
    assert control_plane.release_lease(lease.lease_id, reason="manual-retry") is True
    control_plane.budgets_path.write_text("models: [", encoding="utf-8")
    assert control_plane.lease_next_job("worker-2") is not None

    event = control_plane.iter_events("config_reload_failed")[-1]
    assert "while parsing" in json.loads(event["payload_json"])["error"]


def test_cooldown_after_rate_limit_blocks_lease(tmp_path):
    control_plane = _make_control_plane(tmp_path)
    control_plane.enqueue("docs/module-rate-limit.md", phase="review", model="claude-sonnet-4-6")

    conn = sqlite3.connect(control_plane.db_path)
    try:
        conn.execute(
            """
            INSERT INTO events (type, module_key, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "attempt_rate_limited",
                "docs/module-rate-limit.md",
                json.dumps({"model": "claude-sonnet-4-6"}, sort_keys=True),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    assert control_plane.lease_next_job("worker-1") is None
    assert control_plane.fetch_value("SELECT queue_state FROM jobs WHERE id = 1") == "pending"
    event = control_plane.iter_events("model_cooldown_active")[-1]
    payload = json.loads(event["payload_json"])
    assert payload["model"] == "claude-sonnet-4-6"
    assert payload["cooldown_seconds"] == 600


def test_pause_all_kill_switch_blocks_all_models(tmp_path):
    control_plane = _make_control_plane(
        tmp_path,
        kill_switch_policy="PAUSE_ALL",
        models={
            "claude-sonnet-4-6": {
                "cooldown_after_rate_limit": 600,
                "hourly_calls": 50,
                "max_concurrent": 2,
                "weekly_budget_usd": 40.0,
                "weekly_calls": 1,
            },
            "gemini-3-flash-preview": {
                "cooldown_after_rate_limit": 300,
                "hourly_calls": 800,
                "max_concurrent": 5,
                "weekly_calls": 100,
            },
        },
    )
    control_plane.enqueue("docs/module-pause-all-1.md", phase="patch", model="claude-sonnet-4-6")
    initial = control_plane.lease_next_job("worker-1", model="claude-sonnet-4-6")
    assert initial is not None
    assert control_plane.record_usage(initial.lease_id, actual_calls=1, actual_usd=0.5) is True

    control_plane.enqueue("docs/module-pause-all-2.md", phase="review", model="gemini-3-flash-preview")
    control_plane.enqueue("docs/module-pause-all-3.md", phase="patch", model="claude-sonnet-4-6")

    assert control_plane.lease_next_job("worker-2", model="gemini-3-flash-preview") is None
    assert control_plane.lease_next_job("worker-3", model="claude-sonnet-4-6") is None
    blocked_events = control_plane.iter_events("dispatch_blocked_budget")
    pause_payloads = [json.loads(event["payload_json"]) for event in blocked_events]
    assert any(
        payload["reason"] == "pipeline_paused" and payload["policy"] == "PAUSE_ALL"
        for payload in pause_payloads
    )


def test_claude_only_pause_blocks_claude_only(tmp_path):
    control_plane = _make_control_plane(
        tmp_path,
        kill_switch_policy="CLAUDE_ONLY_PAUSE",
        models={
            "claude-sonnet-4-6": {
                "cooldown_after_rate_limit": 600,
                "hourly_calls": 50,
                "max_concurrent": 2,
                "weekly_budget_usd": 40.0,
                "weekly_calls": 1,
            },
            "gemini-3-flash-preview": {
                "cooldown_after_rate_limit": 300,
                "hourly_calls": 800,
                "max_concurrent": 5,
                "weekly_calls": 100,
            },
        },
    )
    control_plane.enqueue("docs/module-claude-cap.md", phase="patch", model="claude-sonnet-4-6")
    initial = control_plane.lease_next_job("worker-1", model="claude-sonnet-4-6")
    assert initial is not None
    assert control_plane.record_usage(initial.lease_id, actual_calls=1, actual_usd=0.5) is True

    control_plane.enqueue("docs/module-gemini-open.md", phase="review", model="gemini-3-flash-preview")
    control_plane.enqueue("docs/module-claude-blocked.md", phase="patch", model="claude-sonnet-4-6")

    gemini_lease = control_plane.lease_next_job("worker-2", model="gemini-3-flash-preview")
    assert gemini_lease is not None
    assert gemini_lease.model == "gemini-3-flash-preview"
    assert control_plane.lease_next_job("worker-3", model="claude-sonnet-4-6") is None
    blocked_events = control_plane.iter_events("dispatch_blocked_budget")
    pause_payloads = [json.loads(event["payload_json"]) for event in blocked_events]
    assert any(
        payload["reason"] == "pipeline_paused"
        and payload["policy"] == "CLAUDE_ONLY_PAUSE"
        and payload["model"] == "claude-sonnet-4-6"
        for payload in pause_payloads
    )


def test_budget_and_show_budget_are_cli_aliases(tmp_path, capsys):
    control_plane = _make_control_plane(tmp_path)
    control_plane.enqueue("docs/module-e.md", phase="review", model="claude-sonnet-4-6")
    with patch("pipeline_v2.cli.watch_forever") as watch_forever:
        budget_rc = pipeline_main(
            ["--db", str(control_plane.db_path), "--budgets", str(control_plane.budgets_path), "budget", "--json"]
        )
        budget_out = capsys.readouterr().out
        show_rc = pipeline_main(
            ["--db", str(control_plane.db_path), "--budgets", str(control_plane.budgets_path), "show", "budget", "--json"]
        )
        show_out = capsys.readouterr().out

    assert budget_rc == 0
    assert show_rc == 0
    assert json.loads(budget_out) == json.loads(show_out)
    watch_forever.assert_not_called()


def test_recover_dead_letters_requeues_review_and_clears_module_level_dead_letter(tmp_path, capsys):
    control_plane = _make_control_plane(tmp_path)
    module_key = "docs/module-dead-letter.md"
    job = control_plane.enqueue(module_key, phase="review", model="claude-sonnet-4-6")
    lease = control_plane.lease_next_job("worker-1")
    assert lease is not None
    assert lease.job_id == job.job_id
    assert control_plane.fail_lease_terminal(
        lease.lease_id,
        reason="rewrite_attempt_limit",
        event_payload={"phase": "patch", "rewrite_attempts": 4},
    )

    before = _build_status_report(control_plane.db_path)
    assert before["counts"]["dead_letter"] == 1
    assert before["needs_human_count"] == 1

    recover_rc = pipeline_main(
        [
            "--db",
            str(control_plane.db_path),
            "--budgets",
            str(control_plane.budgets_path),
            "recover-dead-letters",
            "--json",
        ]
    )
    recovered = json.loads(capsys.readouterr().out)

    assert recover_rc == 0
    assert recovered == [
        {
            "dry_run": False,
            "job_id": 2,
            "module_key": module_key,
            "previous_reason": "rewrite_attempt_limit",
            "requeue_model": "gpt-5.3-codex-spark",
            "requeue_phase": "review",
        }
    ]

    after = _build_status_report(control_plane.db_path)
    assert after["counts"]["dead_letter"] == 0
    assert after["counts"]["pending_review"] == 1
    assert after["needs_human_count"] == 0

    show_rc = pipeline_main(
        [
            "--db",
            str(control_plane.db_path),
            "--budgets",
            str(control_plane.budgets_path),
            "show",
            "needs-human",
            "--json",
        ]
    )
    assert show_rc == 0
    assert json.loads(capsys.readouterr().out) == []

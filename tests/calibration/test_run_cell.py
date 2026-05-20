from __future__ import annotations

import json
import shutil

import pytest

from scripts.calibration import run_cell, schema
from scripts.calibration.models import model_by_canonical
from scripts.calibration.run_cell import DispatchResult


def test_build_dispatch_plan_for_codex_effort_config():
    model = model_by_canonical("gpt-5.3-codex-spark")
    plan = run_cell.build_dispatch_plan(model)
    assert plan.kind == "subprocess"
    assert "--model" in plan.argv
    assert "gpt-5.3-codex-spark" in plan.argv
    assert "model_reasoning_effort=xhigh" in plan.argv


def test_build_dispatch_plan_routes_grok_4_3_via_prompt_prefix_hint():
    model = model_by_canonical("grok-4.3")
    plan = run_cell.build_dispatch_plan(model)
    assert plan.kind == "runtime"
    assert plan.agent_name in {"grok", "qwen"}
    assert plan.model == model.canonical_string
    assert plan.prompt_prefix == f"[Reasoning effort hint: {model.effort_requested}]\n\n"
    assert isinstance(plan.argv, tuple)


def test_haiku_4_5_omits_effort_flag():
    """Regression guard: claude-haiku-4-5 has effort_mechanism='none'; --effort must NOT appear in argv."""
    plan = run_cell.build_dispatch_plan(model_by_canonical("claude-haiku-4-5"))
    assert "--effort" not in plan.argv


def test_run_cell_persists_cell_dispatch_response_and_jsonl_with_relative_output_root(tmp_path):
    db_path = tmp_path / "ledger.db"
    output_root = run_cell.DEFAULT_OUTPUT_ROOT / f"tmp-test-{tmp_path.name}"

    try:

        def fake_dispatch(model, prompt, cwd, timeout_s):
            assert model.canonical_string == "gpt-5.3-codex-spark"
            assert "parse_dependabot_cooldown" in prompt
            assert cwd == run_cell.REPO_ROOT
            assert timeout_s == 30
            return DispatchResult(
                response="def parse_dependabot_cooldown(yaml_text):\n    return None\n",
                task_id="fake-task",
                latency_s=0.01,
            )

        cell_id = run_cell.run_cell(
            lane="code-writing",
            canonical_string="gpt-5.3-codex-spark",
            fixture_id="parse-dependabot-cooldown",
            run_date="2026-05-21",
            db_path=db_path,
            output_root=output_root,
            timeout_s=30,
            dispatch_fn=fake_dispatch,
        )

        response_path = output_root / "2026-05-21" / "responses" / f"{cell_id}.md"
        jsonl_path = output_root / "2026-05-21" / "results.jsonl"
        assert response_path.exists()
        row = json.loads(jsonl_path.read_text(encoding="utf-8").strip())
        assert row["cell_id"] == cell_id
        assert row["response_path"] == str(response_path.relative_to(run_cell.REPO_ROOT))
        with schema.connect(db_path) as conn:
            assert schema.fetch_cell(conn, cell_id)["family"] == "openai"
            dispatch = conn.execute(
                "SELECT * FROM dispatches WHERE cell_id = ?",
                (cell_id,),
            ).fetchone()
        assert dispatch["task_id"] == "fake-task"
        assert dispatch["response_path"] == str(response_path.relative_to(run_cell.REPO_ROOT))
    finally:
        shutil.rmtree(output_root, ignore_errors=True)


def test_run_cell_persists_cell_dispatch_response_and_jsonl_with_absolute_output_root(tmp_path):
    db_path = tmp_path / "ledger.db"
    output_root = tmp_path / "calibration" / "v1"

    def fake_dispatch(model, prompt, cwd, timeout_s):
        assert model.canonical_string == "gpt-5.3-codex-spark"
        assert "parse_dependabot_cooldown" in prompt
        assert cwd == run_cell.REPO_ROOT
        assert timeout_s == 30
        return DispatchResult(
            response="def parse_dependabot_cooldown(yaml_text):\n    return None\n",
            task_id="fake-task",
            latency_s=0.01,
        )

    cell_id = run_cell.run_cell(
        lane="code-writing",
        canonical_string="gpt-5.3-codex-spark",
        fixture_id="parse-dependabot-cooldown",
        run_date="2026-05-21",
        db_path=db_path,
        output_root=output_root,
        timeout_s=30,
        dispatch_fn=fake_dispatch,
    )

    response_path = output_root / "2026-05-21" / "responses" / f"{cell_id}.md"
    jsonl_path = output_root / "2026-05-21" / "results.jsonl"
    assert response_path.exists()
    row = json.loads(jsonl_path.read_text(encoding="utf-8").strip())
    assert row["cell_id"] == cell_id
    with schema.connect(db_path) as conn:
        assert schema.fetch_cell(conn, cell_id)["family"] == "openai"
        dispatch = conn.execute(
            "SELECT * FROM dispatches WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()
    assert dispatch["task_id"] == "fake-task"
    assert dispatch["response_path"] == str(response_path)


def test_missing_fixture_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_cell.run_cell(
            lane="code-writing",
            canonical_string="gpt-5.3-codex-spark",
            fixture_id="missing-fixture",
            db_path=tmp_path / "ledger.db",
            output_root=tmp_path / "calibration",
            dispatch_fn=lambda model, prompt, cwd, timeout_s: DispatchResult(
                response="",
                task_id="unused",
                latency_s=0.0,
            ),
        )

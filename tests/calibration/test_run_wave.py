from __future__ import annotations

import pytest

from scripts.calibration import run_cell as run_cell_module
from scripts.calibration import run_wave
from scripts.calibration.models import model_by_canonical
from scripts.calibration.run_cell import DispatchResult


def _build_cell() -> run_wave.CellSpec:
    return run_wave.CellSpec(
        lane="code-writing",
        fixture_id="parse-dependabot-cooldown",
        model=model_by_canonical("gpt-5.5"),
    )


@pytest.mark.parametrize("response", ["OK", "OK.", "OK!", "oK"])
def test_preflight_probe_accepts_ok(response, monkeypatch):
    def fake_dispatch_prompt(model, prompt, cwd, timeout_s):
        assert cwd == run_cell_module.REPO_ROOT
        return DispatchResult(response=response, task_id="probe", latency_s=0.01)

    monkeypatch.setattr(run_cell_module, "dispatch_prompt", fake_dispatch_prompt)

    results = run_wave.preflight_probe(cells=[_build_cell()])

    assert len(results) == 1
    assert results[0]["ok"] is True
    assert results[0]["response_preview"] == response


def test_preflight_probe_fails_on_empty_response(monkeypatch):
    def fake_dispatch_prompt(model, prompt, cwd, timeout_s):
        return DispatchResult(response="", task_id="probe", latency_s=0.01)

    monkeypatch.setattr(run_cell_module, "dispatch_prompt", fake_dispatch_prompt)

    results = run_wave.preflight_probe(cells=[_build_cell()])

    assert len(results) == 1
    assert results[0]["ok"] is False
    assert results[0]["response_preview"] == ""
    assert "expected an 'OK' response" in results[0]["error"]


def test_preflight_probe_fails_on_refusal(monkeypatch):
    response = "I cannot help with that."

    def fake_dispatch_prompt(model, prompt, cwd, timeout_s):
        return DispatchResult(response=response, task_id="probe", latency_s=0.01)

    monkeypatch.setattr(run_cell_module, "dispatch_prompt", fake_dispatch_prompt)

    results = run_wave.preflight_probe(cells=[_build_cell()])

    assert len(results) == 1
    assert results[0]["ok"] is False
    assert results[0]["response_preview"] == response
    assert "expected an 'OK' response" in results[0]["error"]


def test_preflight_probe_fails_on_prefixed_ok_refusal(monkeypatch):
    response = "OK, I cannot help with that."

    def fake_dispatch_prompt(model, prompt, cwd, timeout_s):
        return DispatchResult(response=response, task_id="probe", latency_s=0.01)

    monkeypatch.setattr(run_cell_module, "dispatch_prompt", fake_dispatch_prompt)

    results = run_wave.preflight_probe(cells=[_build_cell()])

    assert len(results) == 1
    assert results[0]["ok"] is False
    assert results[0]["response_preview"] == response
    assert "expected an 'OK' response" in results[0]["error"]


# ---------------------------------------------------------------------------
# Multi-fixture LANE_FIXTURES tests (#1441 phase 3 refactor)
# ---------------------------------------------------------------------------


def test_lane_fixtures_values_are_lists():
    """Every lane maps to a list of fixture ids, not a single string."""
    from scripts.calibration import run_wave

    for lane, fixtures in run_wave.LANE_FIXTURES.items():
        assert isinstance(fixtures, list), f"{lane}: expected list, got {type(fixtures)}"
        assert len(fixtures) >= 1, f"{lane}: empty fixture list"
        for fid in fixtures:
            assert isinstance(fid, str) and fid, f"{lane}: bad fixture id {fid!r}"


def test_lane_fixtures_files_exist_on_disk():
    """Every (lane, fixture_id) in LANE_FIXTURES has a YAML file on disk."""
    from pathlib import Path
    from scripts.calibration import run_wave

    root = Path(run_wave.__file__).parent / "ground-truth" / "v1"
    for lane, fixtures in run_wave.LANE_FIXTURES.items():
        for fid in fixtures:
            yaml_path = root / lane / f"{fid}.yaml"
            legacy_path = root / lane / f"{fid}.legacy.yaml"
            assert yaml_path.exists() or legacy_path.exists(), (
                f"{lane}/{fid}: missing fixture YAML"
            )


def test_lane_fixtures_files_have_matching_prompts():
    """Every (lane, fixture_id) in LANE_FIXTURES has a prompt MD file on disk."""
    from pathlib import Path
    from scripts.calibration import run_wave

    root = Path(run_wave.__file__).parent / "prompts" / "v1"
    for lane, fixtures in run_wave.LANE_FIXTURES.items():
        for fid in fixtures:
            prompt_path = root / lane / f"{fid}.md"
            assert prompt_path.exists(), f"{lane}/{fid}: missing prompt MD"


def test_build_cells_expands_multi_fixture_lane():
    """build_cells produces N cells when a lane has N fixtures (× 1 model)."""
    from scripts.calibration import models, run_wave

    test_model = next(iter(models.ANCHORS))
    cells = run_wave.build_cells(models=[test_model], lanes=["architecting"])
    arch_fixtures = run_wave.LANE_FIXTURES["architecting"]
    assert len(cells) == len(arch_fixtures), (
        f"expected {len(arch_fixtures)} cells, got {len(cells)}"
    )
    fixture_ids = {cell.fixture_id for cell in cells}
    assert fixture_ids == set(arch_fixtures), (
        f"fixture coverage mismatch: {fixture_ids} vs {arch_fixtures}"
    )


def test_build_cells_single_fixture_lane_still_one_cell():
    """Lanes with 1 fixture still produce 1 cell per (model, lane) pair."""
    from scripts.calibration import models, run_wave

    test_model = next(iter(models.ANCHORS))
    cells = run_wave.build_cells(models=[test_model], lanes=["code-writing"])
    assert len(cells) == 1
    assert cells[0].fixture_id == "parse-dependabot-cooldown"


def test_build_cells_multi_lane_total_count():
    """Total cells = sum of fixtures across the selected lanes (× 1 model)."""
    from scripts.calibration import models, run_wave

    test_model = next(iter(models.ANCHORS))
    lanes = ["architecting", "code-writing", "debugging"]
    expected = sum(len(run_wave.LANE_FIXTURES[lane]) for lane in lanes)
    cells = run_wave.build_cells(models=[test_model], lanes=lanes)
    assert len(cells) == expected

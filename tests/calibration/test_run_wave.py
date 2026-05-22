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


# ---------------------------------------------------------------------------
# --fixture CLI enforcement (#1450) — 1-fixture-per-model-per-wave rule
# ---------------------------------------------------------------------------


def test_main_rejects_multi_fixture_lane_without_fixture_arg(capsys):
    """Running --lanes architecting (3 fixtures) without --fixture must exit 2."""
    from scripts.calibration import run_wave

    rc = run_wave.main(
        [
            "--wave", "A",
            "--lanes", "architecting",
            "--skip-preflight",
            "--no-render",
            "--no-score",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2, f"expected exit 2, got {rc}"
    assert "1-fixture-per-model-per-wave" in captured.err
    assert "architecting" in captured.err


def test_main_accepts_single_fixture_lane_without_fixture_arg(monkeypatch):
    """--lanes code-writing (1 fixture) without --fixture remains backward-compatible.

    Stub _dispatch_one to avoid an actual model dispatch — we're only proving
    the validation gate doesn't reject this shape.
    """
    from scripts.calibration import run_wave

    calls: list[run_wave.CellSpec] = []

    def fake_dispatch(spec, **_kwargs):
        calls.append(spec)
        return {
            "ok": True,
            "cell_id": "fake",
            "lane": spec.lane,
            "model": spec.model.canonical_string,
            "family": spec.model.family,
            "replicate_seq": 0,
            "elapsed_s": 0.0,
            "scored": False,
        }

    monkeypatch.setattr(run_wave, "_dispatch_one", fake_dispatch)
    monkeypatch.setattr(run_wave, "preflight_probe", lambda cells: [{"ok": True} for _ in cells])
    rc = run_wave.main(
        [
            "--wave", "A",
            "--lanes", "code-writing",
            "--no-render",
            "--no-score",
            "--smoke",
        ]
    )
    assert rc == 0, f"expected exit 0, got {rc}"
    assert len(calls) >= 1
    assert all(c.fixture_id == "parse-dependabot-cooldown" for c in calls)


def test_main_accepts_multi_fixture_lane_with_fixture_arg(monkeypatch):
    """--lanes architecting --fixture <id> dispatches only that fixture."""
    from scripts.calibration import run_wave

    calls: list[run_wave.CellSpec] = []

    def fake_dispatch(spec, **_kwargs):
        calls.append(spec)
        return {
            "ok": True,
            "cell_id": "fake",
            "lane": spec.lane,
            "model": spec.model.canonical_string,
            "family": spec.model.family,
            "replicate_seq": 0,
            "elapsed_s": 0.0,
            "scored": False,
        }

    monkeypatch.setattr(run_wave, "_dispatch_one", fake_dispatch)
    monkeypatch.setattr(run_wave, "preflight_probe", lambda cells: [{"ok": True} for _ in cells])
    rc = run_wave.main(
        [
            "--wave", "A",
            "--lanes", "architecting",
            "--fixture", "cascade-reviewer-tiebreak-policy",
            "--no-render",
            "--no-score",
            "--smoke",
        ]
    )
    assert rc == 0, f"expected exit 0, got {rc}"
    assert all(c.fixture_id == "cascade-reviewer-tiebreak-policy" for c in calls)


def test_main_rejects_unknown_fixture_id(capsys):
    """--fixture id that isn't in LANE_FIXTURES[lane] must exit 2 with a clear error."""
    from scripts.calibration import run_wave

    rc = run_wave.main(
        [
            "--wave", "A",
            "--lanes", "architecting",
            "--fixture", "does-not-exist",
            "--no-render",
            "--no-score",
            "--smoke",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "does-not-exist" in captured.err
    assert "Valid:" in captured.err


def test_build_cells_filter_param_filters_fixtures():
    """build_cells with fixture_filter restricts to a single fixture per lane."""
    from scripts.calibration import models, run_wave

    test_model = next(iter(models.ANCHORS))
    cells = run_wave.build_cells(
        models=[test_model],
        lanes=["architecting"],
        fixture_filter="kubedojo-review-override-rfc",
    )
    assert len(cells) == 1
    assert cells[0].fixture_id == "kubedojo-review-override-rfc"


# ---------------------------------------------------------------------------
# --judge1 / --judge2 override (Claude-throttle window mitigation, #1441)
# ---------------------------------------------------------------------------


def test_main_passes_judge_args_through_to_score_cell(monkeypatch):
    """`--judge1 X --judge2 Y` flows from main → _dispatch_one → score_cell."""
    from scripts.calibration import run_wave, score_cell as sc_mod
    captured: dict[str, str] = {}

    def fake_score(*, cell_id, db_path, replicate_seq, judge1, judge2):
        captured["judge1"] = judge1
        captured["judge2"] = judge2
        return {"gate1": True}

    monkeypatch.setattr(sc_mod, "score_cell", fake_score)
    monkeypatch.setattr(run_wave, "preflight_probe", lambda cells: [{"ok": True} for _ in cells])
    # Stub the actual model dispatch so we don't burn API calls.
    monkeypatch.setattr(run_wave, "run_cell", lambda **_kw: "fake-cell-id")

    rc = run_wave.main([
        "--wave", "A",
        "--lanes", "code-writing",
        "--judge1", "gemini-3.5-flash-high",
        "--judge2", "codex-gpt-5.5",
        "--no-render",
        "--smoke",
    ])
    assert rc == 0, f"expected exit 0, got {rc}"
    assert captured.get("judge1") == "gemini-3.5-flash-high"
    assert captured.get("judge2") == "codex-gpt-5.5"


def test_main_default_judges_are_sonnet_plus_gemini_flash():
    """Default judges match the score_cell production defaults."""
    from scripts.calibration import run_wave
    parser = run_wave.build_parser()
    ns = parser.parse_args(["--wave", "A", "--lanes", "code-writing"])
    assert ns.judge1 == "claude-sonnet-4-6"
    assert ns.judge2 == "gemini-3.5-flash-high"

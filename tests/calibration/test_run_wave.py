from __future__ import annotations

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


def test_preflight_probe_accepts_ok(monkeypatch):
    def fake_dispatch_prompt(model, prompt, cwd, timeout_s):
        assert cwd == run_cell_module.REPO_ROOT
        return DispatchResult(response="OK", task_id="probe", latency_s=0.01)

    monkeypatch.setattr(run_cell_module, "dispatch_prompt", fake_dispatch_prompt)

    results = run_wave.preflight_probe(cells=[_build_cell()])

    assert len(results) == 1
    assert results[0]["ok"] is True
    assert results[0]["response_preview"] == "OK"


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

"""Tests for scripts/score_module.py (issue #2419).

Pins the canonical 8-dimension rubric contract (D1-D8 incl. Practitioner
Depth): 33/40 pass sum, per-dimension floor of 4, rejection of stale 7-score
and invalid 9-score input, out-of-range scores, CLI stdin/JSON. Literals
(33/40, band edges) are asserted directly, not recomputed from the module's
constants — tests pin the contract, not the implementation.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "score_module.py"
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def _load():
    spec = importlib.util.spec_from_file_location("score_module", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sm = _load()

ALL_FOUR = [4, 4, 4, 4, 4, 4, 4, 4]  # sum 32 — below the 33 pass line
BARE_PASS = [4, 4, 4, 4, 4, 4, 4, 5]  # sum 33 — lowest passing sum


def run_cli(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(VENV_PYTHON), str(SCRIPT), *args],
                          input=stdin, capture_output=True, text=True, check=False)


class TestPassContract:
    def test_sum_32_with_clean_floor_fails(self):
        result = sm.score(ALL_FOUR)
        assert result["sum"] == 32
        assert result["floor_pass"] is True and result["sum_pass"] is False
        assert result["passes"] is False

    def test_sum_33_passes(self):
        result = sm.score(BARE_PASS)
        assert result["sum"] == 33 and result["max"] == 40
        assert result["passes"] is True and result["rating"] == "Pass"

    def test_high_sum_with_d8_below_floor_fails(self):
        # Sum 38 clears the bar; D8 = 3 must sink it via the floor.
        result = sm.score([5, 5, 5, 5, 5, 5, 5, 3])
        assert result["sum_pass"] is True and result["floor_pass"] is False
        assert result["passes"] is False
        assert ("Practitioner Depth", 3) in result["weak_dimensions"]

    def test_floor_fail_on_any_single_dimension(self):
        for i in range(8):
            values = [5] * 8
            values[i] = 3
            assert sm.score(values)["passes"] is False, f"D{i+1} below floor must fail"

    def test_result_keys_stable(self):
        result = sm.score(BARE_PASS)
        assert set(result) == {"scores", "sum", "max", "min_score", "floor_pass",
                               "sum_pass", "passes", "rating", "weak_dimensions"}
        assert list(result["scores"].values()) == BARE_PASS
        assert len(result["scores"]) == 8


class TestRatingBands:
    @pytest.mark.parametrize(
        "total,expected",
        [(40, "Pass"), (33, "Pass"), (32, "Needs polish"), (25, "Needs polish"),
         (24, "Needs work"), (17, "Needs work"), (16, "Rewrite"), (8, "Rewrite")],
    )
    def test_band_edges(self, total, expected):
        values = [1] * 8
        remaining = total - 8
        for i in range(8):
            add = min(4, remaining)
            values[i] += add
            remaining -= add
        assert remaining == 0 and sum(values) == total
        assert expected in sm.score(values)["rating"]  # fails wrap as FAIL(<band> ...)


class TestInputValidation:
    def test_wrong_score_counts_rejected(self):
        with pytest.raises(ValueError, match="Expected 8 scores, got 7"):
            sm.score([4, 5, 4, 4, 5, 4, 4])  # stale 7-dim input
        with pytest.raises(ValueError, match="Expected 8 scores, got 9"):
            sm.score([4, 5, 4, 4, 5, 4, 4, 4, 4])

    @pytest.mark.parametrize("bad", [0, 6, -1, 99])
    def test_out_of_range_rejected(self, bad):
        values = [4] * 8
        values[3] = bad
        with pytest.raises(ValueError, match="out of range 1-5"):
            sm.score(values)


class TestCLI:
    def test_argv_boundaries(self):
        proc = run_cli(*[str(v) for v in BARE_PASS])
        assert proc.returncode == 0 and "RESULT: PASS (33/40)" in proc.stdout
        proc = run_cli(*[str(v) for v in ALL_FOUR])
        assert proc.returncode == 1 and "RESULT: FAIL" in proc.stdout
        assert "Need 1 more points to reach 33" in proc.stdout

    def test_stdin_json_pass_and_fail(self):
        proc = run_cli("-", "--json", stdin="4 4 4 4 4 4 4 5\n")
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)
        assert payload["passes"] is True and payload["sum"] == 33 and payload["max"] == 40
        assert "Practitioner Depth" in payload["scores"]

        proc = run_cli("-", "--json", stdin="5 5 5 5 5 5 5 3\n")
        assert proc.returncode == 1
        payload = json.loads(proc.stdout)
        assert payload["passes"] is False and payload["floor_pass"] is False
        assert payload["weak_dimensions"] == [["Practitioner Depth", 3]]

    def test_cli_rejects_stale_seven_scores(self):
        proc = run_cli("4", "5", "4", "4", "5", "4", "4")
        assert proc.returncode == 1
        assert "Expected 8 scores, got 7" in proc.stderr

from __future__ import annotations

import pytest

from scripts.calibration.selftest import run_selftest

pytestmark = [
    pytest.mark.requires_dispatch,
    pytest.mark.skip(reason="requires a real Codex dispatch"),
]


def test_selftest_runs_one_real_codex_cell(tmp_path):
    cell_id = run_selftest(
        run_date="2026-05-21",
        output_root=tmp_path / "calibration" / "v1",
        db_path=tmp_path / "results.db",
    )
    assert "gpt-5.3-codex-spark@xhigh" in cell_id


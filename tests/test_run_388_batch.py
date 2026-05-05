"""Unit tests for #388 batch remote-branch skip behavior."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.quality import run_388_batch


def _build_plan() -> dict:
    return {
        "tracks": [
            {
                "track": "platform",
                "modules": [
                    {"path": "platform/module-1.9-foo"},
                    {"path": "platform/module-1.9-bar"},
                ],
            }
        ]
    }


def test_select_modules_skips_matching_remote_pilot_branches() -> None:
    selected, reasons = run_388_batch.select_modules(
        "platform",
        _build_plan(),
        {},
        set(),
        {"module-1.9-foo": "codex/388-pilot-module-1.9-foo"},
    )
    assert selected == ["src/content/docs/platform/module-1.9-bar"]
    assert any("[skip] module-1.9-foo: active remote branch codex/388-pilot-module-1.9-foo" in r for r in reasons)


def test_select_modules_keeps_module_without_matching_remote_branch() -> None:
    selected, reasons = run_388_batch.select_modules("platform", _build_plan(), {}, set(), {})
    assert len(selected) == 2
    assert not reasons


def test_main_no_skip_active_branches_overrides_bucket_skip(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(run_388_batch, "fetch_upgrade_plan", _build_plan)
    monkeypatch.setattr(run_388_batch, "fetch_quality_board", lambda: {})
    monkeypatch.setattr(run_388_batch, "fetch_active_leases", lambda: set())
    monkeypatch.setattr(
        run_388_batch,
        "fetch_active_pilot_branches",
        lambda: {"module-1.9-foo": "codex/388-pilot-module-1.9-foo"},
    )

    rc = run_388_batch.main(["--track", "platform", "--dry", "--no-skip-active-branches"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "[skip] module-1.9-foo: active remote branch" not in out
    assert "platform/module-1.9-foo" in out


def test_main_skips_module_with_active_pilot_branch_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(run_388_batch, "fetch_upgrade_plan", _build_plan)
    monkeypatch.setattr(run_388_batch, "fetch_quality_board", lambda: {})
    monkeypatch.setattr(run_388_batch, "fetch_active_leases", lambda: set())
    monkeypatch.setattr(
        run_388_batch,
        "fetch_active_pilot_branches",
        lambda: {"module-1.9-foo": "codex/388-pilot-module-1.9-foo"},
    )

    rc = run_388_batch.main(["--track", "platform", "--dry"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "[skip] module-1.9-foo: active remote branch codex/388-pilot-module-1.9-foo" in out
    assert "platform/module-1.9-bar" in out


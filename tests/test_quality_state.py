"""Tests for ``scripts.quality.state``.

Covers the Codex must-fixes this module closes:

* **#5** — durable in-progress states (WRITE/REVIEW_IN_PROGRESS stamp attempt_id)
* **#10** — compare-and-swap transitions + fcntl.flock lease contention
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality import state  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_state_dir(tmp_path, monkeypatch):
    """Redirect STATE_DIR to a tmp path so tests don't touch real state files."""
    monkeypatch.setattr(state, "STATE_DIR", tmp_path / "state")
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)


def _make_state(slug: str = "test-module", stage: str = "UNAUDITED") -> dict:
    """Build a minimal in-memory state for tests."""
    s = {
        "slug": slug,
        "module_path": f"src/content/docs/{slug.replace('-', '/')}.md",
        "module_index": 0,
        "stage": stage,
        "history": [{"at": state.now_iso(), "stage": stage, "note": "test-seed"}],
    }
    return s


def test_load_missing_returns_none() -> None:
    assert state.load_state("does-not-exist") is None


def test_save_and_load_roundtrips() -> None:
    s = _make_state("roundtrip")
    state.save_state(s)
    loaded = state.load_state("roundtrip")
    assert loaded is not None
    assert loaded["slug"] == "roundtrip"
    assert loaded["stage"] == "UNAUDITED"


def test_new_state_assigns_module_index() -> None:
    module_path = state.CONTENT_ROOT.parent.parent.parent / "src/content/docs/k8s/cka/fake.md"
    s = state.new_state(module_path, module_index=42)
    assert s["module_index"] == 42
    assert s["stage"] == "UNAUDITED"
    assert s["attempt_id"] is None
    assert s["retry_count"] == 0


def test_transition_advances_on_matching_disk_stage() -> None:
    s = _make_state("t1", stage="UNAUDITED")
    state.save_state(s)
    result = state.transition(s, "UNAUDITED", "AUDITED", note="audit done")
    assert result["stage"] == "AUDITED"
    disk = state.load_state("t1")
    assert disk is not None and disk["stage"] == "AUDITED"
    # History breadcrumb written with the short ``note`` but no meta bloat.
    last_history = disk["history"][-1]
    assert last_history["stage"] == "AUDITED"
    assert last_history["note"] == "audit done"


def test_transition_rejected_when_disk_advanced_underneath() -> None:
    """CAS: if another worker advanced the state while we were working,
    our transition must refuse rather than clobber."""
    s = _make_state("t2", stage="UNAUDITED")
    state.save_state(s)
    # Simulate another worker advancing the state on disk.
    disk_copy = state.load_state("t2")
    assert disk_copy is not None
    state.transition(disk_copy, "UNAUDITED", "AUDITED")
    # Our in-memory state still says UNAUDITED; try to transition from UNAUDITED.
    with pytest.raises(state.TransitionRejected):
        state.transition(s, "UNAUDITED", "AUDITED")


def test_transition_rejects_unknown_target_stage() -> None:
    s = _make_state("t3")
    state.save_state(s)
    with pytest.raises(state.StateError):
        state.transition(s, "UNAUDITED", "NOT_A_REAL_STAGE")


def test_start_in_progress_stamps_attempt_id() -> None:
    """Durable in-progress state with a fresh attempt_id — Codex must-fix #5."""
    s = _make_state("t4", stage="WRITE_PENDING")
    state.save_state(s)
    attempt_id = state.start_in_progress(s, "WRITE_PENDING", "WRITE_IN_PROGRESS")
    assert len(attempt_id) == 12
    assert s["stage"] == "WRITE_IN_PROGRESS"
    assert s["attempt_id"] == attempt_id
    disk = state.load_state("t4")
    assert disk is not None and disk["attempt_id"] == attempt_id


def test_start_in_progress_rejects_non_in_progress_target() -> None:
    s = _make_state("t5", stage="WRITE_PENDING")
    state.save_state(s)
    with pytest.raises(state.StateError):
        state.start_in_progress(s, "WRITE_PENDING", "WRITE_DONE")


def test_record_failure_sets_stage_and_reason() -> None:
    s = _make_state("t6", stage="WRITE_IN_PROGRESS")
    state.save_state(s)
    state.record_failure(s, "subprocess timeout")
    assert s["stage"] == "FAILED"
    assert s["failure_reason"] == "subprocess timeout"
    disk = state.load_state("t6")
    assert disk is not None and disk["stage"] == "FAILED"
    assert disk["history"][-1]["reason"] == "subprocess timeout"


def test_lease_blocks_concurrent_holder() -> None:
    """Second lease acquirer must wait until the first releases.

    Regression guard for Codex must-fix #10 — without the lease, two
    workers can run the same stage concurrently.
    """
    slug = "lease-test"
    state.save_state(_make_state(slug))
    hold_duration = 0.2
    second_acquired_at: list[float] = []
    first_released_at: list[float] = []

    def first_holder() -> None:
        with state.state_lease(slug, timeout=2.0):
            time.sleep(hold_duration)
            first_released_at.append(time.monotonic())

    def second_holder() -> None:
        # Small delay so the first holder definitely acquires first.
        time.sleep(0.02)
        with state.state_lease(slug, timeout=2.0):
            second_acquired_at.append(time.monotonic())

    t1 = threading.Thread(target=first_holder)
    t2 = threading.Thread(target=second_holder)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert first_released_at and second_acquired_at
    assert second_acquired_at[0] >= first_released_at[0] - 0.01  # -0.01 for clock jitter


def test_lease_times_out_when_contended_too_long() -> None:
    slug = "lease-timeout"
    state.save_state(_make_state(slug))
    release_evt = threading.Event()

    def hog() -> None:
        with state.state_lease(slug, timeout=2.0):
            release_evt.wait(timeout=2.0)

    t = threading.Thread(target=hog)
    t.start()
    time.sleep(0.05)  # let hog acquire
    try:
        with pytest.raises(TimeoutError):
            with state.state_lease(slug, timeout=0.1):
                pass
    finally:
        release_evt.set()
        t.join()


def test_leased_state_rejects_wrong_slug() -> None:
    slug = "owner-test"
    state.save_state(_make_state(slug))
    other = _make_state("different-slug")
    with state.state_lease(slug, timeout=2.0) as lease:
        with pytest.raises(state.StateError):
            lease.save(other)


def test_iter_state_slugs_returns_sorted() -> None:
    for slug in ["zebra", "alpha", "mike"]:
        state.save_state(_make_state(slug))
    assert state.iter_state_slugs() == ["alpha", "mike", "zebra"]

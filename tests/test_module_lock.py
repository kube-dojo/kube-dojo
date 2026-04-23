from __future__ import annotations

import sqlite3
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline_common import module_lock  # noqa: E402


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point module_lock at a tmp DB per test + clear the schema cache so
    each test re-runs CREATE TABLE IF NOT EXISTS against its own file.
    """
    p = tmp_path / ".pipeline" / "v2.db"
    monkeypatch.setattr(module_lock, "DEFAULT_DB_PATH", p)
    monkeypatch.setattr(module_lock, "_INITIALIZED_DBS", set())
    return p


def _row(db_path: Path, module_key: str) -> sqlite3.Row | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(
            "SELECT * FROM module_write_locks WHERE module_key = ?",
            (module_key,),
        ).fetchone()
    finally:
        conn.close()


def _expire(db_path: Path, module_key: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE module_write_locks SET expires_at = 0 WHERE module_key = ?",
            (module_key,),
        )
        conn.commit()
    finally:
        conn.close()


def test_acquire_on_empty_db_succeeds(db_path: Path) -> None:
    conflict = module_lock.acquire_module_lock("mod-a", holder="worker-1")
    assert conflict is None
    row = _row(db_path, "mod-a")
    assert row is not None
    assert row["holder"] == "worker-1"
    assert row["completed_at"] is None


def test_double_acquire_same_key_returns_conflict(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    conflict = module_lock.acquire_module_lock("mod-a", holder="w2")
    assert conflict is not None
    assert conflict.holder == "w1"
    assert conflict.expires_at > conflict.acquired_at


def test_different_keys_do_not_conflict(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    assert module_lock.acquire_module_lock("mod-b", holder="w2") is None
    # Both rows present.
    assert _row(db_path, "mod-a") is not None
    assert _row(db_path, "mod-b") is not None


def test_expired_lock_gets_stolen(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    _expire(db_path, "mod-a")
    # Another holder takes over cleanly.
    assert module_lock.acquire_module_lock("mod-a", holder="w2") is None
    row = _row(db_path, "mod-a")
    assert row is not None
    assert row["holder"] == "w2"


def test_completed_lock_gets_stolen(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    assert module_lock.complete_module_lock(
        "mod-a", holder="w1", outcome="done"
    )
    # Another holder can now take it.
    assert module_lock.acquire_module_lock("mod-a", holder="w2") is None
    row = _row(db_path, "mod-a")
    assert row is not None
    assert row["holder"] == "w2"
    # And the completed row is gone — the new acquire evicted it.
    assert row["completed_at"] is None
    assert row["outcome"] is None


def test_complete_guards_by_holder(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    assert not module_lock.complete_module_lock(
        "mod-a", holder="imposter", outcome="evil"
    )
    # Original holder can still complete.
    assert module_lock.complete_module_lock(
        "mod-a", holder="w1", outcome="done"
    )


def test_release_guards_by_holder(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    assert not module_lock.release_module_lock("mod-a", holder="imposter")
    # Row still there.
    assert _row(db_path, "mod-a") is not None
    assert module_lock.release_module_lock("mod-a", holder="w1")
    assert _row(db_path, "mod-a") is None


def test_release_does_not_touch_completed_row(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    assert module_lock.complete_module_lock(
        "mod-a", holder="w1", outcome="done"
    )
    # Completed rows ignore release — the row survives, owner audit trail
    # stays intact until next acquire evicts it.
    assert not module_lock.release_module_lock("mod-a", holder="w1")
    row = _row(db_path, "mod-a")
    assert row is not None
    assert row["outcome"] == "done"


def test_sweep_clears_expired_and_completed(db_path: Path) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    assert module_lock.acquire_module_lock("mod-b", holder="w2") is None
    assert module_lock.acquire_module_lock("mod-c", holder="w3") is None
    _expire(db_path, "mod-a")
    module_lock.complete_module_lock("mod-b", holder="w2", outcome="ok")
    # mod-c is live and should survive.
    cleared = module_lock.sweep_expired_locks()
    assert cleared == 2
    assert _row(db_path, "mod-a") is None
    assert _row(db_path, "mod-b") is None
    assert _row(db_path, "mod-c") is not None


def test_context_manager_success_records_completion(db_path: Path) -> None:
    with module_lock.module_lock(
        "mod-a", holder="w1", outcome_on_success="clean"
    ):
        # Re-entry by another holder is blocked inside the body.
        conflict = module_lock.acquire_module_lock("mod-a", holder="w2")
        assert conflict is not None
        assert conflict.holder == "w1"
    row = _row(db_path, "mod-a")
    assert row is not None
    assert row["completed_at"] is not None
    assert row["outcome"] == "clean"


def test_context_manager_exception_releases_by_default(db_path: Path) -> None:
    with pytest.raises(RuntimeError, match="boom"):
        with module_lock.module_lock("mod-a", holder="w1"):
            raise RuntimeError("boom")
    # Released — row is gone, next acquire unblocked.
    assert _row(db_path, "mod-a") is None
    assert module_lock.acquire_module_lock("mod-a", holder="w2") is None


def test_context_manager_exception_with_outcome_records_it(
    db_path: Path,
) -> None:
    with pytest.raises(RuntimeError):
        with module_lock.module_lock(
            "mod-a",
            holder="w1",
            outcome_on_error="crashed",
        ):
            raise RuntimeError("boom")
    row = _row(db_path, "mod-a")
    assert row is not None
    assert row["outcome"] == "crashed"
    assert row["completed_at"] is not None


def test_context_manager_conflict_raises_lock_acquire_error(
    db_path: Path,
) -> None:
    assert module_lock.acquire_module_lock("mod-a", holder="w1") is None
    with pytest.raises(module_lock.LockAcquireError) as excinfo:
        with module_lock.module_lock("mod-a", holder="w2"):
            pytest.fail("should not enter body")
    assert excinfo.value.module_key == "mod-a"
    assert excinfo.value.conflict.holder == "w1"


def test_default_holder_is_pid_at_hostname() -> None:
    h = module_lock.default_holder()
    assert "@" in h
    pid_part, host_part = h.split("@", 1)
    assert pid_part.isdigit()
    assert host_part  # non-empty


def test_empty_module_key_rejected(db_path: Path) -> None:
    with pytest.raises(ValueError, match="module_key"):
        module_lock.acquire_module_lock("", holder="w1")
    with pytest.raises(ValueError):
        module_lock.complete_module_lock("", holder="w1", outcome="x")
    with pytest.raises(ValueError):
        module_lock.release_module_lock("", holder="w1")


def test_nonpositive_lease_rejected(db_path: Path) -> None:
    with pytest.raises(ValueError, match="lease_seconds"):
        module_lock.acquire_module_lock(
            "mod-a", holder="w1", lease_seconds=0
        )
    with pytest.raises(ValueError):
        module_lock.acquire_module_lock(
            "mod-a", holder="w1", lease_seconds=-5
        )


def test_concurrent_threads_single_winner(db_path: Path) -> None:
    """Stress: N threads race to acquire the same key. Exactly one wins.

    This is the real contract the caller cares about: the pilot bug
    (two resolvers on the same module clobbering each other) cannot
    recur if and only if at most one acquirer succeeds per snapshot.
    """
    # Prime the schema cache from the main thread so the threads are not
    # all doing CREATE TABLE in parallel — the _ensure_schema lock handles
    # that too, but priming keeps the race purely on the INSERT.
    assert module_lock.acquire_module_lock("primer", holder="prime") is None
    module_lock.release_module_lock("primer", holder="prime")

    winners: list[bool] = []
    barrier = threading.Barrier(10)

    def attempt() -> None:
        barrier.wait()
        # Each thread gets a unique holder so the winner's identity is
        # visible but all 10 are contending for the SAME key.
        holder = f"t-{threading.get_ident()}"
        conflict = module_lock.acquire_module_lock(
            "hot-key", holder=holder
        )
        winners.append(conflict is None)

    threads = [threading.Thread(target=attempt) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)
    assert all(not t.is_alive() for t in threads), "thread hung"
    assert sum(1 for w in winners if w) == 1, winners


def test_lease_seconds_affects_expires_at(db_path: Path) -> None:
    before = int(time.time())
    module_lock.acquire_module_lock(
        "mod-a", holder="w1", lease_seconds=60
    )
    after = int(time.time())
    row = _row(db_path, "mod-a")
    assert row is not None
    assert before + 60 <= row["expires_at"] <= after + 60

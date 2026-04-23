"""Per-module write lock backed by `.pipeline/v2.db`.

Purpose
-------
Prevent two processes from concurrently rewriting the same module's
files. Citation-residuals resolve + pipeline_v4 batch + future workers
all mutate `src/content/docs/<module_key>.md` plus per-module queue
state under `.pipeline/v3/human-review/<module_key>.json`. A last-write-
wins race on either file silently loses work.

The lock is advisory — it only protects writers that choose to acquire
it. It is not a substitute for fcntl or OS-level file locking; it's a
coordination primitive between cooperating tools.

Contract
--------
Schema (created lazily on first use):

    CREATE TABLE module_write_locks (
        module_key TEXT PRIMARY KEY,
        holder TEXT NOT NULL,
        acquired_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        completed_at INTEGER,
        outcome TEXT
    )

One row per `module_key`. A live (non-expired, non-completed) row blocks
others. Expired or completed rows are evicted inside the same
transaction as a new acquire, so repeat runs do not accumulate dead
rows.

State transitions:
- acquire → row inserted with `expires_at = now + ttl`.
- complete → `completed_at` set, `outcome` recorded. Row becomes
  inert and will be deleted the next time anyone tries to acquire.
- release → row deleted. Use when a writer crashes or aborts without a
  meaningful outcome.
- sweep_expired → removes dead rows whose `expires_at` has passed. Not
  required for correctness (acquire evicts as it goes) but useful for
  observability / housekeeping.

Stolen leases. An expired lock is considered abandoned; the next
acquirer evicts and takes it. TTL should therefore be *generously*
longer than the real work, not a tight deadline. 1800 s (30 min) is
the default to cover large citation_residuals runs including LLM +
network stalls without forcing risky steals on a slow-but-alive run.

Why a new table instead of `v4_batch_leases`. `pipeline_v4_batch.py`
defines `v4_batch_leases` locally; that table name is v4-specific.
The citation_residuals resolver is a v3 consumer and should not pick
up a v4-named table. A future refactor can migrate v4 batch onto this
primitive; for now they coexist.
"""

from __future__ import annotations

import os
import socket
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / ".pipeline" / "v2.db"
DEFAULT_LEASE_SECONDS = 1800

LOCK_SCHEMA = """
CREATE TABLE IF NOT EXISTS module_write_locks (
    module_key TEXT PRIMARY KEY,
    holder TEXT NOT NULL,
    acquired_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    completed_at INTEGER,
    outcome TEXT
);
CREATE INDEX IF NOT EXISTS idx_module_write_locks_expires
    ON module_write_locks(expires_at);
"""

_INIT_LOCK = threading.Lock()
_INITIALIZED_DBS: set[str] = set()


@dataclass(frozen=True)
class LockConflict:
    """Details about an existing live lock that blocked an acquire."""

    holder: str
    acquired_at: int
    expires_at: int


class LockAcquireError(RuntimeError):
    """Raised when acquire_module_lock cannot take the lock.

    The exception carries the live holder's record so the caller can log
    a precise reason (who holds it, until when) without re-querying.
    """

    def __init__(self, module_key: str, conflict: LockConflict):
        self.module_key = module_key
        self.conflict = conflict
        super().__init__(
            f"module {module_key!r} is already locked by "
            f"{conflict.holder!r} until epoch {conflict.expires_at}"
        )


def default_holder() -> str:
    """Stable identifier for the current process: pid@hostname."""
    return f"{os.getpid()}@{socket.gethostname()}"


def _ensure_schema(db_path: Path) -> None:
    """Idempotent CREATE IF NOT EXISTS, serialized per path."""
    key = str(db_path)
    if key in _INITIALIZED_DBS:
        return
    with _INIT_LOCK:
        if key in _INITIALIZED_DBS:
            return
        db_path.parent.mkdir(parents=True, exist_ok=True)
        setup = sqlite3.connect(db_path, timeout=30)
        try:
            setup.execute("PRAGMA journal_mode=WAL")
            setup.executescript(LOCK_SCHEMA)
            setup.commit()
        finally:
            setup.close()
        _INITIALIZED_DBS.add(key)


def _connect(db_path: Path) -> sqlite3.Connection:
    _ensure_schema(db_path)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _current_live_holder(
    conn: sqlite3.Connection, module_key: str
) -> LockConflict | None:
    """Return the current live holder's record, or None if the slot is
    free or holds only an expired/completed row.

    Callers run this inside a BEGIN IMMEDIATE block after evicting dead
    rows, so a non-None result is authoritative for the transaction's
    snapshot.
    """
    row = conn.execute(
        """
        SELECT holder, acquired_at, expires_at
        FROM module_write_locks
        WHERE module_key = ?
        """,
        (module_key,),
    ).fetchone()
    if row is None:
        return None
    return LockConflict(
        holder=row["holder"],
        acquired_at=int(row["acquired_at"]),
        expires_at=int(row["expires_at"]),
    )


def acquire_module_lock(
    module_key: str,
    *,
    holder: str | None = None,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    db_path: Path | None = None,
) -> LockConflict | None:
    """Try to take a lock on module_key. Returns None on success, or a
    LockConflict describing the live holder if the slot is taken.

    Raises ValueError on obviously wrong inputs (empty key, non-positive
    TTL). Does not raise on contention — the caller decides whether to
    skip, retry, or escalate.
    """
    if not module_key:
        raise ValueError("module_key must be non-empty")
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive")
    holder = holder or default_holder()
    db_path = db_path or DEFAULT_DB_PATH
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        # Evict expired-or-completed rows for this key so a stuck or
        # crashed predecessor does not block forever.
        conn.execute(
            """
            DELETE FROM module_write_locks
            WHERE module_key = ?
              AND (completed_at IS NOT NULL
                   OR expires_at <= CAST(strftime('%s','now') AS INTEGER))
            """,
            (module_key,),
        )
        try:
            conn.execute(
                """
                INSERT INTO module_write_locks
                    (module_key, holder, acquired_at, expires_at)
                VALUES (
                    ?, ?,
                    CAST(strftime('%s','now') AS INTEGER),
                    CAST(strftime('%s','now') AS INTEGER) + ?
                )
                """,
                (module_key, holder, lease_seconds),
            )
            conn.commit()
            return None
        except sqlite3.IntegrityError:
            # PRIMARY KEY collision means a live row survived the
            # eviction step (another holder has a non-expired,
            # non-completed lock).
            conflict = _current_live_holder(conn, module_key)
            conn.rollback()
            if conflict is None:
                # Extremely unlikely race: the blocker was evicted by
                # another connection between our DELETE and INSERT.
                # Re-raise as transient so the caller can retry.
                raise
            return conflict
    finally:
        conn.close()


def complete_module_lock(
    module_key: str,
    *,
    holder: str | None = None,
    outcome: str,
    db_path: Path | None = None,
) -> bool:
    """Mark the lock completed with an outcome. Returns True if the row
    was updated (caller held the lock), False otherwise (someone else
    held it or it had already been released/expired).

    A completed row is inert — it does not block future acquires — but
    is kept around briefly so operators can see recent outcomes via a
    direct query. It is evicted on the next acquire for this key.
    """
    if not module_key:
        raise ValueError("module_key must be non-empty")
    holder = holder or default_holder()
    db_path = db_path or DEFAULT_DB_PATH
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            """
            UPDATE module_write_locks
            SET completed_at = CAST(strftime('%s','now') AS INTEGER),
                outcome = ?
            WHERE module_key = ?
              AND holder = ?
              AND completed_at IS NULL
            """,
            (outcome, module_key, holder),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def release_module_lock(
    module_key: str,
    *,
    holder: str | None = None,
    db_path: Path | None = None,
) -> bool:
    """Drop a live lock without recording an outcome. Use for aborted
    runs (user cancelled, crash recovery) where `complete` would be a
    lie. Returns True if a row was deleted.

    Guarded by holder so a stale process cannot release someone else's
    lock.
    """
    if not module_key:
        raise ValueError("module_key must be non-empty")
    holder = holder or default_holder()
    db_path = db_path or DEFAULT_DB_PATH
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            """
            DELETE FROM module_write_locks
            WHERE module_key = ?
              AND holder = ?
              AND completed_at IS NULL
            """,
            (module_key, holder),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def sweep_expired_locks(db_path: Path | None = None) -> int:
    """Delete every expired-or-completed lock row. Returns the count.

    Purely hygienic — `acquire_module_lock` evicts the specific key it
    wants. Call this from a watchdog if you want rows not to linger.
    """
    db_path = db_path or DEFAULT_DB_PATH
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            """
            DELETE FROM module_write_locks
            WHERE completed_at IS NOT NULL
               OR expires_at <= CAST(strftime('%s','now') AS INTEGER)
            """
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


@contextmanager
def module_lock(
    module_key: str,
    *,
    holder: str | None = None,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    db_path: Path | None = None,
    outcome_on_success: str = "ok",
    outcome_on_error: str | None = None,
) -> Iterator[None]:
    """Context manager: acquire on enter, complete on clean exit,
    release on exception.

    Raises LockAcquireError if the lock is held. Callers that want to
    skip-on-contention should call `acquire_module_lock` directly and
    branch on its return value — the context manager is for the common
    "take it or bail" path.

    On clean exit: records `outcome_on_success` via complete.
    On exception: releases the lock so a follow-up run can retry. If
    `outcome_on_error` is set, records that outcome instead of
    releasing (useful when you want an audit trail of the failure).
    """
    holder = holder or default_holder()
    conflict = acquire_module_lock(
        module_key,
        holder=holder,
        lease_seconds=lease_seconds,
        db_path=db_path,
    )
    if conflict is not None:
        raise LockAcquireError(module_key, conflict)
    try:
        yield
    except Exception:
        if outcome_on_error is not None:
            complete_module_lock(
                module_key,
                holder=holder,
                outcome=outcome_on_error,
                db_path=db_path,
            )
        else:
            release_module_lock(
                module_key, holder=holder, db_path=db_path
            )
        raise
    else:
        complete_module_lock(
            module_key,
            holder=holder,
            outcome=outcome_on_success,
            db_path=db_path,
        )

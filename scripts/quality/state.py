"""Atomic per-module state I/O with ``fcntl.flock`` leases and CAS transitions.

The pipeline stores one JSON per module at
``.pipeline/quality-pipeline/<slug>.json``. Every transition is:

1. **Leased** — the caller holds an exclusive ``fcntl.flock`` on the state
   file for the full duration of the stage's work (dispatch, git ops,
   citation fetch, etc.). This prevents two concurrent workers from
   double-processing the same module (Codex must-fix #10).
2. **Compare-and-swap** — the ``transition`` call asserts the on-disk
   stage matches the caller's expectation before writing the new stage.
   A stale in-memory ``state`` dict that's diverged from disk will
   refuse to transition.
3. **Atomic** — every write is ``write-temp then os.replace``. A SIGKILL
   mid-write leaves either the old file or the new file, never a
   truncated one.

Durable in-progress states (``WRITE_IN_PROGRESS``, ``REVIEW_IN_PROGRESS``)
exist so that a SIGKILL between "started a subprocess" and "subprocess
finished" lands in a state that :mod:`stages` can resume idempotently
(Codex must-fix #5). The resume logic lives in :mod:`stages`; this
module only guarantees the state file itself is sound.
"""

from __future__ import annotations

import fcntl
import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .worktree import primary_checkout_root

REPO_ROOT = primary_checkout_root(Path(__file__).resolve().parents[2])
STATE_DIR = REPO_ROOT / ".pipeline" / "quality-pipeline"
CONTENT_ROOT = REPO_ROOT / "src" / "content" / "docs"

# Full state machine. Ordered by the expected forward path; terminal states
# (``COMMITTED``, ``SKIPPED``, ``FAILED``) and branches (``REVIEW_CHANGES``)
# live at the end. See the design doc for the transition graph.
STAGES = (
    "UNAUDITED",
    "AUDITED",
    "ROUTED",
    "WRITE_PENDING",
    "WRITE_IN_PROGRESS",
    "WRITE_DONE",
    "CITATION_VERIFY",
    "REVIEW_PENDING",
    "REVIEW_IN_PROGRESS",
    "REVIEW_APPROVED",
    "REVIEW_CHANGES",
    "CITATION_CLEANUP_ONLY",
    "COMMITTED",
    "SKIPPED",
    "FAILED",
)

TERMINAL_STAGES = frozenset({"COMMITTED", "SKIPPED", "FAILED"})
IN_PROGRESS_STAGES = frozenset({"WRITE_IN_PROGRESS", "REVIEW_IN_PROGRESS"})


class StateError(Exception):
    """State file I/O or transition failure."""


class TransitionRejected(StateError):
    """CAS failed — on-disk stage differs from the expected ``from_stage``.

    Raised when ``transition()`` detects another worker advanced the state
    between ``load`` and ``save``. Callers treat this as "someone else took
    this module" and move on.
    """


def slug_for(module_path: Path) -> str:
    """Derive the canonical slug from a content-doc path.

    ``src/content/docs/k8s/capa/module-1.2-argo-events.md`` →
    ``k8s-capa-module-1.2-argo-events``. Stable across re-runs and
    filesystem moves as long as the file stays under ``CONTENT_ROOT``.
    """
    rel = module_path.resolve().relative_to(CONTENT_ROOT)
    return str(rel).replace("/", "-").removesuffix(".md")


def state_path_for(slug: str) -> Path:
    return STATE_DIR / f"{slug}.json"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def new_state(module_path: Path, module_index: int) -> dict[str, Any]:
    """Construct an initial state dict.

    ``module_index`` is the permanent, alphabetical-by-path index assigned
    at bootstrap. It's used for writer round-robin (``i % 2`` → Codex vs
    Claude) and stays stable across re-bootstraps so a SIGKILL mid-retry
    doesn't flip the writer assignment.
    """
    slug = slug_for(module_path)
    return {
        "slug": slug,
        "module_path": module_path.resolve().relative_to(REPO_ROOT).as_posix(),
        "module_index": module_index,
        "stage": "UNAUDITED",
        "audit": None,
        "route": None,
        "writer": None,
        "reviewer": None,
        "write": None,
        "review": None,
        "citations": None,
        "commit": None,
        "retry_count": 0,
        "attempt_id": None,
        "history": [{"at": now_iso(), "stage": "UNAUDITED", "note": "created"}],
        "failure_reason": None,
    }


def load_state(slug: str) -> dict[str, Any] | None:
    """Read a state file. Returns ``None`` if it doesn't exist.

    Does not acquire a lease — callers reading for display only (``status``
    subcommand, briefing endpoint) can use this freely. Workers that
    intend to mutate must use :func:`state_lease` instead.
    """
    p = state_path_for(slug)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    """Atomic write. Must only be called while holding the lease.

    Exposed for :func:`state_lease` internals and for bootstrap
    (which creates state files serially before any worker starts).
    """
    _atomic_write_json(state_path_for(state["slug"]), state)


@contextmanager
def state_lease(slug: str, timeout: float = 5.0) -> Iterator["LeasedState"]:
    """Acquire an exclusive lease on a module's state file.

    Implementation uses a sidecar lock file (``<slug>.json.lock``) so the
    state JSON itself can be read without blocking. The lock is released
    automatically when the ``with`` block exits (success OR exception) OR
    when the process dies — ``fcntl.flock`` is tied to the file descriptor
    and the kernel cleans up on process exit.

    Raises :class:`TimeoutError` if another worker holds the lease longer
    than ``timeout`` seconds. Default 5s is intentionally short — the
    lease is meant to be held for the full stage (minutes), so contention
    should be rare and a fast failure tells the caller to skip this slug.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = STATE_DIR / f"{slug}.json.lock"
    # Open with O_CREAT so the lock file materializes on first touch.
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"state lease contended for {slug} (>{timeout}s)")
                time.sleep(0.05)
        yield LeasedState(slug)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


class LeasedState:
    """Handle returned by :func:`state_lease` — read/write under the lease.

    The handle does not cache; each ``load`` re-reads the file so callers
    see the latest bytes even if they call ``load`` multiple times during
    the lease (e.g. resume logic that peeks at ``write.commit_sha`` before
    deciding the new stage).
    """

    def __init__(self, slug: str) -> None:
        self._slug = slug

    def load(self) -> dict[str, Any] | None:
        return load_state(self._slug)

    def save(self, state: dict[str, Any]) -> None:
        if state.get("slug") != self._slug:
            raise StateError(f"lease is for {self._slug!r} but state has slug {state.get('slug')!r}")
        save_state(state)


def transition(
    state: dict[str, Any],
    from_stage: str,
    to_stage: str,
    **meta: Any,
) -> dict[str, Any]:
    """CAS transition: verify on-disk stage matches ``from_stage``, then advance.

    ``state`` is mutated in place AND saved. Returns the updated dict for
    call-site convenience. Callers MUST hold the lease for ``state['slug']``
    across load → mutate → transition, or another worker may have
    advanced the state between the caller's load and this write.

    Raises :class:`TransitionRejected` if the on-disk stage doesn't match.
    Raises :class:`StateError` if the target stage isn't in :data:`STAGES`.
    """
    if to_stage not in STAGES:
        raise StateError(f"unknown target stage: {to_stage!r}")
    disk = load_state(state["slug"])
    if disk is None:
        raise StateError(f"state file missing for {state['slug']!r}")
    if disk["stage"] != from_stage:
        raise TransitionRejected(
            f"{state['slug']}: expected stage {from_stage!r} on disk, found {disk['stage']!r}"
        )
    state["stage"] = to_stage
    for k, v in meta.items():
        state[k] = v
    entry: dict[str, Any] = {"at": now_iso(), "stage": to_stage}
    # Filter meta-shaped entries out of the history blob — they can be huge
    # (whole Codex outputs); the history is only a breadcrumb trail.
    if "note" in meta:
        entry["note"] = meta["note"]
    state.setdefault("history", []).append(entry)
    save_state(state)
    return state


def start_in_progress(state: dict[str, Any], from_stage: str, to_stage: str) -> str:
    """Transition into an in-progress stage and stamp a fresh ``attempt_id``.

    Must be called while holding the lease. Returns the new ``attempt_id``
    so callers can thread it into subprocess logs / commit messages for
    post-mortem correlation.
    """
    if to_stage not in IN_PROGRESS_STAGES:
        raise StateError(f"{to_stage!r} is not an in-progress stage")
    attempt_id = uuid.uuid4().hex[:12]
    transition(state, from_stage, to_stage, attempt_id=attempt_id)
    return attempt_id


def record_failure(state: dict[str, Any], reason: str) -> None:
    """Force-transition to ``FAILED`` with a reason. Caller must hold the lease."""
    state["stage"] = "FAILED"
    state["failure_reason"] = reason
    state.setdefault("history", []).append(
        {"at": now_iso(), "stage": "FAILED", "reason": reason}
    )
    save_state(state)


def iter_state_slugs() -> list[str]:
    """List every slug with a state file, sorted. Bootstrap uses this to resume."""
    if not STATE_DIR.exists():
        return []
    return sorted(p.stem for p in STATE_DIR.glob("*.json"))

"""Queue with writer stickiness for site-wide quality rewrite (v5).

Sits on top of :mod:`state` — adds a ``queue`` sub-document to each module's
state file. Stickiness rule:

* When the assigned writer hits a transient error (rate limit, auth, 5xx),
  the queue marks the module ``blocked`` with exponential backoff and
  retries the **same** writer later. **Never** falls back to the other
  writer family on transient errors — cross-writer fallback would defeat
  the site-wide style consistency goal.
* Only after ``MAX_PRIMARY_ATTEMPTS`` (5) failed attempts does the queue
  escalate to the tertiary writer (Claude). Tertiary is intentionally
  expensive and rare — it should only fire when the primary writer is
  genuinely incapable on this module, not when the API was flaky.

The queue does NOT subsume the v2 quality stage machine. v2 stages
(``UNAUDITED`` → … → ``COMMITTED``) still drive the rewrite step by step;
the queue layer chooses *which writer* to dispatch and *when* to retry.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .state import (
    CONTENT_ROOT,
    load_state,
    now_iso,
    save_state,
    state_lease,
)

# --- Routing rule -----------------------------------------------------------
#
# Frontmatter ``complexity`` tag wins. Otherwise track-based fallback. If
# neither resolves, default to tertiary so a human picks instead of silently
# routing to whichever the order ended up.

PRIMARY_BEGINNER = "gemini-3.1-pro-preview"
PRIMARY_ADVANCED = "gpt-5.5"
TERTIARY = "claude-opus-4-7"

BEGINNER_TRACKS = (
    "ai/foundations",
    "ai/open-models-local-inference",
)
ADVANCED_TRACKS = (
    "platform/disciplines/data-ai",
    "on-premises/ai-ml-infrastructure",
    "platform/toolkits/data-ai-platforms",
    "ai-ml-engineering",
    "platform/disciplines",
    "platform/toolkits",
    "k8s",
    "linux",
)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_COMPLEXITY_RE = re.compile(r"complexity\s*[:=]\s*[`'\"]?\[?(\w+)\]?", re.IGNORECASE)
_REVISION_LINE_RE = re.compile(r"^revision_pending\s*:.*\n", re.MULTILINE)


def _read_complexity(module_path: Path) -> str | None:
    """Return frontmatter complexity tag (lowercased) or None.

    Looks at structured frontmatter first, then a freeform ``Complexity:``
    blockquote/heading line in the first 30 lines (the convention varies
    across older vs newer modules).
    """
    text = module_path.read_text(encoding="utf-8")
    fm = _FRONTMATTER_RE.match(text)
    if fm:
        m = _COMPLEXITY_RE.search(fm.group(1))
        if m:
            return m.group(1).lower()
    head = "\n".join(text.splitlines()[:30])
    m = _COMPLEXITY_RE.search(head)
    if m:
        return m.group(1).lower()
    return None


def route_writer(module_path: Path) -> str:
    """Return the assigned writer for a module per the routing rule.

    Frontmatter complexity tag wins (``[QUICK]`` / ``[COMPLEX]`` etc.). If
    absent, falls back to track-based heuristics. If neither classifies the
    module, returns the tertiary writer so a human review will catch it.
    """
    complexity = _read_complexity(module_path)
    if complexity in {"quick", "beginner", "easy", "intro"}:
        return PRIMARY_BEGINNER
    if complexity in {"complex", "advanced", "deep"}:
        return PRIMARY_ADVANCED

    rel = module_path.resolve().relative_to(CONTENT_ROOT).as_posix()
    section = "/".join(rel.split("/")[:2])
    for t in BEGINNER_TRACKS:
        if section.startswith(t):
            return PRIMARY_BEGINNER
    for t in ADVANCED_TRACKS:
        if section.startswith(t):
            return PRIMARY_ADVANCED
    return TERTIARY


# --- Backoff schedule -------------------------------------------------------
#
# Exponential, intentionally slow. The user is OK waiting hours for a flaky
# writer to recover — that's better than burning the cross-writer fallback.

BACKOFF_SECONDS = (
    5 * 60,        # 1st transient failure → 5 min
    30 * 60,       # 2nd → 30 min
    2 * 3600,      # 3rd → 2 hr
    8 * 3600,      # 4th → 8 hr
    24 * 3600,     # 5th → 24 hr (then escalate on next failure)
)
MAX_PRIMARY_ATTEMPTS = len(BACKOFF_SECONDS)


# --- Queue sub-document schema ----------------------------------------------


def new_queue_doc(assigned_writer: str) -> dict[str, Any]:
    return {
        "assigned_writer": assigned_writer,
        "writer_attempts": 0,
        "total_attempts": 0,
        "escalation_level": 0,           # 0=primary, 1=tertiary
        "blocked_until": None,           # ISO timestamp or None
        "last_block_reason": None,
        "revision_pending": True,        # banner to learners
        "queued_at": now_iso(),
        "completed_at": None,
    }


# --- High-level operations (each holds a state.lease internally) ------------


@dataclass(frozen=True)
class ClaimResult:
    """Returned by :func:`claim`. Tells the caller what writer to use, or why not."""
    writer: str | None
    blocked_until: str | None
    reason: str | None  # human-readable when writer is None


def ensure_queued(slug: str, module_path: Path) -> dict[str, Any]:
    """Idempotently attach a queue doc to a module's state AND set the banner.

    Routes the writer per :func:`route_writer` if no queue doc exists yet,
    or returns the existing one (writer assignment is sticky across calls).
    Also sets ``revision_pending: true`` in the module's frontmatter so the
    Starlight banner renders for learners during the queue lifetime.
    """
    with state_lease(slug):
        state = load_state(slug)
        if state is None:
            raise FileNotFoundError(f"state for {slug!r} missing — run pipeline bootstrap first")
        if "queue" not in state:
            state["queue"] = new_queue_doc(route_writer(module_path))
            save_state(state)
        # Frontmatter mutation lives outside the JSON state but is tied to it.
        # Idempotent — no-op if already set.
        set_revision_pending_frontmatter(module_path)
        return state["queue"]


def claim(slug: str, *, now: float | None = None) -> ClaimResult:
    """Try to claim this module for processing.

    Returns the writer to use, or None with a reason if the queue says
    we should wait. Does NOT change state — call :func:`record_attempt_start`
    once the dispatch actually launches.
    """
    state = load_state(slug)
    if state is None or "queue" not in state:
        return ClaimResult(writer=None, blocked_until=None, reason="not queued")
    q = state["queue"]
    if q.get("completed_at"):
        return ClaimResult(writer=None, blocked_until=None, reason="already completed")
    blocked = q.get("blocked_until")
    if blocked:
        cur = now if now is not None else time.time()
        if _iso_to_epoch(blocked) > cur:
            return ClaimResult(writer=None, blocked_until=blocked, reason=f"blocked until {blocked}")
    return ClaimResult(writer=q["assigned_writer"], blocked_until=None, reason=None)


def record_attempt_start(slug: str) -> None:
    """Increment attempt counters. Call right before launching the writer dispatch."""
    with state_lease(slug):
        state = load_state(slug)
        if state is None or "queue" not in state:
            raise FileNotFoundError(f"queue for {slug!r} missing")
        q = state["queue"]
        q["writer_attempts"] = int(q.get("writer_attempts", 0)) + 1
        q["total_attempts"] = int(q.get("total_attempts", 0)) + 1
        q["blocked_until"] = None  # we're attempting now
        save_state(state)


def record_block(slug: str, reason: str) -> str:
    """Mark the module blocked (transient writer error) with backoff.

    Backoff index uses the writer's per-writer attempts; if we've used up
    the schedule, escalate to tertiary instead. Returns the new blocked_until
    timestamp (or "ESCALATED" if we tipped over).
    """
    with state_lease(slug):
        state = load_state(slug)
        if state is None or "queue" not in state:
            raise FileNotFoundError(f"queue for {slug!r} missing")
        q = state["queue"]
        attempts = int(q.get("writer_attempts", 0))
        if attempts >= MAX_PRIMARY_ATTEMPTS and q.get("escalation_level", 0) == 0:
            # Tip over to tertiary
            q["escalation_level"] = 1
            q["assigned_writer"] = TERTIARY
            q["writer_attempts"] = 0
            q["blocked_until"] = None
            q["last_block_reason"] = f"escalated after {attempts} primary attempts: {reason}"
            save_state(state)
            return "ESCALATED"
        # Otherwise apply backoff with the assigned writer
        idx = min(attempts - 1, len(BACKOFF_SECONDS) - 1)
        delay = BACKOFF_SECONDS[max(idx, 0)]
        until_epoch = time.time() + delay
        until_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(until_epoch))
        q["blocked_until"] = until_iso
        q["last_block_reason"] = reason
        save_state(state)
        return until_iso


def record_completion(slug: str, module_path: Path | None = None) -> None:
    """Mark the queue entry done AND remove the banner from frontmatter.

    Pass ``module_path`` so the frontmatter can be cleared. If omitted, the
    state is updated but the banner stays — caller is responsible for the
    banner cleanup later (e.g. a separate batch script).
    """
    with state_lease(slug):
        state = load_state(slug)
        if state is None or "queue" not in state:
            raise FileNotFoundError(f"queue for {slug!r} missing")
        q = state["queue"]
        q["completed_at"] = now_iso()
        q["revision_pending"] = False
        q["blocked_until"] = None
        save_state(state)
    if module_path is not None:
        clear_revision_pending_frontmatter(module_path)


# --- Helpers ----------------------------------------------------------------


def _iso_to_epoch(iso: str) -> float:
    return time.mktime(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))


def set_revision_pending_frontmatter(module_path: Path) -> bool:
    """Add ``revision_pending: true`` to a module's frontmatter (idempotent).

    Inserted just after the opening ``---`` so the banner state is the first
    thing a reviewer sees in git diffs. Returns True if the file changed.
    """
    text = module_path.read_text(encoding="utf-8")
    fm = _FRONTMATTER_RE.match(text)
    if not fm:
        # No frontmatter — refuse silently rather than guess where to inject.
        return False
    if _REVISION_LINE_RE.search(fm.group(0)):
        return False  # already set
    new_fm = fm.group(0).replace("---\n", "---\nrevision_pending: true\n", 1)
    new_text = new_fm + text[fm.end():]
    module_path.write_text(new_text, encoding="utf-8")
    return True


def clear_revision_pending_frontmatter(module_path: Path) -> bool:
    """Remove the ``revision_pending`` line from a module's frontmatter."""
    text = module_path.read_text(encoding="utf-8")
    fm = _FRONTMATTER_RE.match(text)
    if not fm:
        return False
    new_fm = _REVISION_LINE_RE.sub("", fm.group(0), count=1)
    if new_fm == fm.group(0):
        return False  # nothing to remove
    new_text = new_fm + text[fm.end():]
    module_path.write_text(new_text, encoding="utf-8")
    return True


def queue_summary() -> dict[str, Any]:
    """Aggregate counts for ``status`` display. No lease — read-only snapshot."""
    from .state import iter_state_slugs

    by_writer: dict[str, dict[str, int]] = {}
    by_status: dict[str, int] = {"queued": 0, "blocked": 0, "completed": 0, "escalated": 0}
    total = 0
    for slug in iter_state_slugs():
        state = load_state(slug)
        if state is None or "queue" not in state:
            continue
        q = state["queue"]
        total += 1
        w = q.get("assigned_writer", "unknown")
        d = by_writer.setdefault(w, {"queued": 0, "blocked": 0, "completed": 0})
        if q.get("completed_at"):
            d["completed"] += 1
            by_status["completed"] += 1
        elif q.get("blocked_until"):
            d["blocked"] += 1
            by_status["blocked"] += 1
        else:
            d["queued"] += 1
            by_status["queued"] += 1
        if q.get("escalation_level", 0) > 0:
            by_status["escalated"] += 1
    return {"total": total, "by_writer": by_writer, "by_status": by_status}


__all__ = [
    "PRIMARY_BEGINNER",
    "PRIMARY_ADVANCED",
    "TERTIARY",
    "MAX_PRIMARY_ATTEMPTS",
    "BACKOFF_SECONDS",
    "ClaimResult",
    "route_writer",
    "ensure_queued",
    "claim",
    "record_attempt_start",
    "record_block",
    "record_completion",
    "queue_summary",
    "set_revision_pending_frontmatter",
    "clear_revision_pending_frontmatter",
]

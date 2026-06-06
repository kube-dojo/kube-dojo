"""Shared usage logger for the agent runtime.

Every invocation through ``runner.invoke()`` writes exactly one JSONL record
here. The file layout reuses ``batch_state/api_usage/`` so the existing
``/api/batch/usage`` endpoint at ``scripts/api/main.py:152`` surfaces
per-agent + per-entrypoint cost data with zero new plumbing.

File layout::

    batch_state/api_usage/usage_<agent>-<entrypoint>_YYYY-MM-DD.jsonl

Examples::

    batch_state/api_usage/usage_codex-bridge_2026-04-10.jsonl
    batch_state/api_usage/usage_gemini-dispatch_2026-04-10.jsonl
    batch_state/api_usage/usage_claude-delegate_2026-04-10.jsonl

Atomicity: we use ``os.open(O_APPEND | O_CREAT | O_WRONLY)`` + single
``os.write()`` per line, bypassing Python's buffered I/O entirely. POSIX
guarantees ``write(2)`` with ``O_APPEND`` is atomic across concurrent writers
for payloads smaller than ``PIPE_BUF`` (typically 4KB). Our JSONL records
are always < 2KB so we're well inside the guarantee. No filelock dependency.

Headroom check: ``has_headroom(agent, model)`` scans the last 15 minutes
of records scoped by ``(agent, model)`` and returns False if any record
has ``outcome == "rate_limited"`` within that window. The runner calls
this pre-invocation and raises ``RateLimitedError`` if headroom is False
— saves the quota slot that would otherwise be burned on a known-rate-
limited call. The window was reduced from 5h to 15min on 2026-04-10
after a transient 429 false-locked the quota for 5 hours on real
builds; see ``_RATE_LIMIT_WINDOW_S`` for the full story.

Record schema note:
    session_mode: one of ``"new"``, ``"resume"``, ``"none"``, describing how
    resume inputs/outputs were handled for this call:

    - ``new``: session_id was None on input and output session_id is non-None
    - ``resume``: non-None input and non-None output session_id
    - ``none``: any other combination (including dropped input sessions)

Issue: #1184. Supersedes standalone #1183.
"""
from __future__ import annotations

import contextlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Rate-limit window in seconds. History:
#   2026-04-09: 5 hours (way too long; one false 429 nuked 5 hours of build)
#   2026-04-10: 15 minutes (still blocked actively-responding Gemini for
#               14+ minutes after a stale transient-429 record)
#   2026-04-11: 5 minutes — see _MIN_EVENTS_TO_BLOCK below for the
#               complementary "isolated event = ignore" rule.
#
# Philosophy:
#   - True quota exhaustion IS rare for us (Google AI Pro subscription,
#     not API key rate limits). When it does happen, the next call after
#     5 minutes either confirms the lock or clears it.
#   - Transient server-capacity issues are common and clear in seconds.
#     The CLI retries them internally. We must not block on them.
#   - An ISOLATED rate-limit event in the window is treated as transient
#     noise and DOES NOT block. Two or more events in the window means
#     the quota is actually exhausted, and we block.
_RATE_LIMIT_WINDOW_S = 5 * 60

# Minimum number of rate-limit events in the window required to actually
# block. A single isolated event is almost always a transient that the
# CLI's internal retry already handled — blocking on it just penalizes
# the next attempt for an issue that's already cleared.
_MIN_EVENTS_TO_BLOCK = 2

# Even if multiple events accumulated in the window, the issue has
# probably cleared by the time the most recent event is older than this
# many seconds. Real quota lockouts produce a continuous stream of 429s,
# not a brief flurry followed by silence. If the latest event is
# stale-by-this-much, we trust the model is responding again.
_RECENCY_BLOCK_THRESHOLD_S = 90

# Manual override: set LU_BYPASS_RATE_LIMIT=1 to disable the headroom
# check entirely. Useful when you've verified the model is responding
# but a stale record is still tripping the check.
_BYPASS_ENV = "LU_BYPASS_RATE_LIMIT"

# In-process cache of rate-limit state, keyed by (agent, model). When a
# call returns outcome="rate_limited", we stamp the timestamp here so
# subsequent calls in the same process short-circuit immediately without
# re-reading the JSONL file.
_RATE_LIMIT_CACHE: dict[tuple[str, str], float] = {}


def _usage_dir() -> Path:
    """Return the batch_state/api_usage/ directory, creating it if missing."""
    # Resolve relative to repo root so this works from any cwd.
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "batch_state" / "api_usage"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _usage_file(agent: str, entrypoint: str, day: datetime | None = None) -> Path:
    """Return the daily JSONL path for (agent, entrypoint)."""
    if day is None:
        day = datetime.now(UTC)
    date_str = day.strftime("%Y-%m-%d")
    return _usage_dir() / f"usage_{agent}-{entrypoint}_{date_str}.jsonl"


def write_record(record: dict[str, Any]) -> None:
    """Append one JSONL record atomically.

    Required fields in ``record``:
        ts, agent, entrypoint, model, outcome

    The function does NOT validate the schema — adapters and runner are
    responsible for building correct records. We only handle the write.

    Atomicity: ``os.open`` + ``os.write`` in one call, bypassing Python's
    buffered I/O. Safe under concurrent writers within POSIX PIPE_BUF.

    If the write fails for any reason (permission denied, disk full, etc.),
    we log a warning to stderr and continue — usage logging is observability,
    not correctness; losing a record is preferable to crashing the caller.
    """
    try:
        path = _usage_file(record["agent"], record["entrypoint"])
        line = (json.dumps(record, ensure_ascii=False, default=str) + "\n").encode("utf-8")
        fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.write(fd, line)
        finally:
            os.close(fd)

        # Update in-process rate-limit cache if this was a rate-limit event.
        # (Gemini review finding #3: use the record's own ts, not wall-clock
        # at write time. Writing a delayed record would otherwise poison the
        # cache by starting the 5h block window from "now" instead of the
        # actual event time. Also honor the newest event when multiple writers
        # race on the same (agent, model) key.)
        if record.get("outcome") == "rate_limited":
            key = (record["agent"], record["model"])
            ts_str = record.get("ts")
            event_ts: float = time.time()  # safe fallback
            if ts_str:
                with contextlib.suppress(ValueError, AttributeError):
                    event_ts = datetime.fromisoformat(
                        str(ts_str).replace("Z", "+00:00")
                    ).timestamp()
            existing = _RATE_LIMIT_CACHE.get(key)
            if existing is None or event_ts > existing:
                _RATE_LIMIT_CACHE[key] = event_ts
    except Exception as exc:  # pragma: no cover — degraded mode only
        # Best-effort: print to stderr but don't fail the caller. The agent
        # call itself already succeeded or failed at this point; we're only
        # trying to persist a telemetry row.
        import sys
        print(
            f"[usage] WARNING: failed to write record: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )


def has_headroom(agent: str, model: str) -> tuple[bool, str]:
    """Check whether (agent, model) has quota headroom for a new call.

    Returns:
        (True, "")  — no recent rate-limit in the 15-minute window, proceed.
        (False, reason) — a rate-limit occurred within 15 minutes; caller
            should raise RateLimitedError immediately without burning a
            quota slot.

    Implementation:
        1. Check in-process cache first (fast path, zero I/O).
        2. Fall through to reading today's JSONL files scoped by
           (agent, model), looking for any rate_limited record within
           the last 15 minutes.

    Window history: originally 5 hours, reduced to 15 minutes on
    2026-04-10, then to 5 minutes + min-events-to-block=2 on 2026-04-11
    after a single 25-second-old transient false-locked an actively-
    responding model. See ``_RATE_LIMIT_WINDOW_S``.
    """
    now = time.time()

    # Manual override: emergency unblock when a stale record is wedging
    # an actively-responding model. Set LU_BYPASS_RATE_LIMIT=1 to skip.
    if os.environ.get(_BYPASS_ENV):
        return True, ""

    # Slow path: scan JSONL files for this (agent, *) and filter by model
    # inside. To survive system clock jumps where old rate-limit records
    # might be in files with dates that don't match the currently shifted
    # clock, we glob all files for the agent and rely on the file mtime
    # plus the absolute `ts` inside the record.
    cutoff = now - _RATE_LIMIT_WINDOW_S
    usage_dir = _usage_dir()
    rate_limit_events: list[float] = []

    for file_path in usage_dir.glob(f"usage_{agent}-*.jsonl"):
        try:
            # Skip files whose modification time is entirely before the cutoff
            if file_path.stat().st_mtime < cutoff:
                continue

            with open(file_path, encoding="utf-8") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except json.JSONDecodeError:
                        continue  # truncated or corrupted line; skip
                    if rec.get("model") != model:
                        continue
                    if rec.get("outcome") != "rate_limited":
                        continue
                    ts_str = rec.get("ts")
                    if not ts_str:
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
                    except (ValueError, AttributeError):
                        continue
                    if ts >= cutoff:
                        rate_limit_events.append(ts)
        except OSError:
            continue  # file disappeared mid-scan or permission denied; skip

    # Cross-check the in-process cache as well — its event may not be on
    # disk yet (writer race) and we'd otherwise undercount.
    cache_key = (agent, model)
    cached_ts = _RATE_LIMIT_CACHE.get(cache_key)
    if cached_ts is not None:
        if cached_ts >= cutoff and cached_ts not in rate_limit_events:
            rate_limit_events.append(cached_ts)
        elif cached_ts < cutoff:
            _RATE_LIMIT_CACHE.pop(cache_key, None)  # expired

    # Block ONLY when:
    #   1. We have enough events to be confident the quota is actually
    #      exhausted (≥ _MIN_EVENTS_TO_BLOCK), AND
    #   2. The most recent event is recent enough that the issue is
    #      likely still active (< _RECENCY_BLOCK_THRESHOLD_S seconds).
    # A single isolated event, OR a stale flurry that ended N+ seconds
    # ago, is treated as cleared and we proceed.
    if len(rate_limit_events) >= _MIN_EVENTS_TO_BLOCK:
        most_recent = max(rate_limit_events)
        age_s = int(now - most_recent)
        if age_s < _RECENCY_BLOCK_THRESHOLD_S:
            return False, (
                f"rate_limited {age_s}s ago "
                f"({len(rate_limit_events)} events in last {_RATE_LIMIT_WINDOW_S // 60}min)"
            )

    return True, ""


def _reset_rate_limit_cache_for_tests() -> None:
    """Clear the in-process rate-limit cache. Tests only."""
    _RATE_LIMIT_CACHE.clear()

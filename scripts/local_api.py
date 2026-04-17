#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Heavy imports (pipeline_v2, status, translation_v2, ztt_status) are deferred
# into the handlers that actually need them. Measured: moving these out of the
# module top saves ~150 ms from server startup and keeps /healthz and
# /api/runtime/services paths dependency-free. See issue #258.


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8768
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
GENERATED_PREFIXES = (
    ".astro/",
    ".dispatch-logs/",
    ".review-results/",
    "dist/",
    "logs/",
    "site/",
)
PIPELINE_PREFIXES = (
    ".bridge/",
    ".pipeline/",
    ".pids/",
)
DEFAULT_FEEDBACK_ISSUE = 248
RUNTIME_SERVICES = (
    {"name": "dev", "pid_file": ".pids/dev.pid", "port": 4333, "label": "Astro Dev Server"},
    {"name": "api", "pid_file": ".pids/api.pid", "port": 8768, "label": "Deterministic Local API"},
    {"name": "feedback", "pid_file": ".pids/feedback.pid", "port": None, "label": "GitHub Issue Watcher"},
    {"name": "pipeline", "pid_file": ".pids/pipeline.pid", "port": None, "label": "Pipeline Supervisor"},
    {"name": "v2-write-worker", "pid_file": ".pids/v2-write-worker.pid", "port": None, "label": "V2 Write Worker"},
    {"name": "v2-review-worker", "pid_file": ".pids/v2-review-worker.pid", "port": None, "label": "V2 Review Worker"},
    {"name": "v2-patch-worker", "pid_file": ".pids/v2-patch-worker.pid", "port": None, "label": "V2 Patch Worker"},
)
RUNTIME_SERVICE_ORDER = tuple(svc["name"] for svc in RUNTIME_SERVICES)

# Module keys are hierarchical slugs under src/content/docs, e.g.
# "prerequisites/zero-to-terminal/module-0.1-alpha". Segments only allow
# lowercase ascii, digits, dots, dashes, and underscores. NO "..", no "/"
# at the edges, no absolute paths. The per-segment check rejects traversal
# attempts like "..", ".", or leading-dot hidden names.
_MODULE_KEY_SEGMENT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def _validate_module_key(repo_root: Path, raw: str) -> str | None:
    """Normalize and validate a module-key slug.

    Returns the normalized key (".md" suffix stripped) if safe, else None.
    Rejects path-traversal patterns and anything that would resolve outside
    src/content/docs.
    """
    if not raw:
        return None
    normalized = raw[:-3] if raw.endswith(".md") else raw
    if not normalized or normalized.startswith("/") or normalized.endswith("/"):
        return None
    segments = normalized.split("/")
    for segment in segments:
        if segment in ("", ".", "..") or not _MODULE_KEY_SEGMENT_RE.match(segment):
            return None
    docs_root = (repo_root / "src" / "content" / "docs").resolve()
    try:
        candidate = (docs_root / f"{normalized}.md").resolve()
        candidate.relative_to(docs_root)
    except (OSError, ValueError):
        return None
    return normalized


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _load_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


# ============================================================
# Response cache + ETag + background snapshot
# ============================================================
#
# Design notes (per reviewer feedback on issue #258):
#   - Cache stores response BYTES, not payload dicts. ETag = weak hash of
#     bytes. Reusing cached bytes makes ETag stable and 304 cheap.
#   - Cache key = normalized (repo_root, path, sorted-query). Avoids
#     cross-repo contamination when two repos share one process.
#   - Invalidation combines TTL + per-endpoint dependency versions. For
#     sqlite deps the version is ``PRAGMA data_version`` on a persistent
#     per-path read-only connection (the documented/reliable usage — see
#     _sqlite_version_key). The connection is also probed for inode/device
#     changes so a replaced DB file is detected.
#   - Background snapshots use fixed-*delay* (not fixed-interval): sleep
#     runs AFTER the refresh completes, so an overrun does not cause
#     overlapping runs. A per-instance build lock enforces single-in-
#     flight across refresh_blocking() and the daemon thread.


_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, "_CacheEntry"] = {}


class _CacheEntry:
    __slots__ = (
        "body_bytes",
        "content_type",
        "etag",
        "expires_at",
        "version_key",
        "built_at",
    )

    def __init__(
        self,
        body_bytes: bytes,
        content_type: str,
        etag: str,
        expires_at: float,
        version_key: tuple,
        built_at: float,
    ) -> None:
        self.body_bytes = body_bytes
        self.content_type = content_type
        self.etag = etag
        self.expires_at = expires_at
        self.version_key = version_key
        self.built_at = built_at


def _weak_etag(body_bytes: bytes) -> str:
    return 'W/"sha256:' + hashlib.sha256(body_bytes).hexdigest()[:16] + '"'


def _path_mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


# Persistent read-only sqlite connections keyed by absolute db path.
# ``PRAGMA data_version`` returns a monotonic counter on a specific
# connection that increments whenever ANOTHER connection commits a
# write. So a single persistent connection, queried repeatedly, is a
# reliable change signal — unlike round-1's fresh-connection misuse.
# The dict lock serializes access; sqlite itself is single-writer,
# and we only keep one persistent reader per db for bookkeeping.
#
# We also cache ``(st_dev, st_ino)`` alongside each connection. If the
# DB file is REPLACED (rename/copy rather than in-place modify) the
# inode changes and we must drop the cached connection — otherwise it
# stays attached to the old inode and keeps reporting the old version.
_SQLITE_VERSION_CONNECTIONS: dict[str, tuple[sqlite3.Connection, tuple]] = {}
_SQLITE_VERSION_LOCK = threading.Lock()


def _close_all_sqlite_version_connections() -> None:
    """Test helper: drop cached read-only connections (e.g. between
    tests that recreate DB files at the same path)."""
    with _SQLITE_VERSION_LOCK:
        for conn, _ident in _SQLITE_VERSION_CONNECTIONS.values():
            try:
                conn.close()
            except sqlite3.Error:
                pass
        _SQLITE_VERSION_CONNECTIONS.clear()


def _file_identity(path: Path) -> tuple:
    """Return ``(st_dev, st_ino)`` or ``None`` fallback. Used to detect
    whether a file at the same path is the *same* file or a replacement."""
    try:
        s = path.stat()
    except OSError:
        return (0, 0)
    return (s.st_dev, s.st_ino)


def _sqlite_version_key(db_path: Path) -> tuple:
    """Fingerprint a sqlite DB using ``PRAGMA data_version`` on a
    persistent read-only connection.

    Contract: two calls return the same key iff no other connection
    has committed between them *and* the file at ``db_path`` is the
    same inode. If the file has been replaced (different inode), the
    cached connection is dropped and reopened. This catches every
    form of write (WAL append, WAL reuse after checkpoint, in-place
    DELETE/MEMORY writes, rapid same-size writes inside one mtime
    granule) plus DB replacement — none of which ``(mtime, size)``
    alone can distinguish.
    """
    if not db_path.exists():
        return ("absent",)

    key = str(db_path.resolve())
    identity = _file_identity(db_path)
    with _SQLITE_VERSION_LOCK:
        cached = _SQLITE_VERSION_CONNECTIONS.get(key)
        if cached is not None:
            conn, cached_identity = cached
            if cached_identity != identity:
                # File was replaced (different inode). Close the stale
                # handle and open a new one below.
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
                _SQLITE_VERSION_CONNECTIONS.pop(key, None)
                cached = None
        if cached is None:
            try:
                conn = sqlite3.connect(
                    f"file:{db_path}?mode=ro",
                    uri=True,
                    timeout=1.0,
                    check_same_thread=False,
                )
            except sqlite3.Error:
                return ("open_failed", _path_mtime(db_path))
            _SQLITE_VERSION_CONNECTIONS[key] = (conn, identity)
        else:
            conn, _ = cached

        try:
            row = conn.execute("PRAGMA data_version").fetchone()
            data_version = int(row[0]) if row is not None else 0
        except sqlite3.Error:
            # Connection poisoned — drop so the next call opens fresh.
            _SQLITE_VERSION_CONNECTIONS.pop(key, None)
            try:
                conn.close()
            except sqlite3.Error:
                pass
            return ("error", _path_mtime(db_path))

    return ("v", identity, data_version)


def _normalized_cache_key(
    path: str,
    query: dict[str, list[str]],
    repo_root: Path | None = None,
) -> str:
    """Normalize (repo_root, path, sorted-query) for stable cache/ETag keys.

    ``repo_root`` is included so two different repos sharing one Python
    process (e.g. the test suite) don't cross-contaminate each other's
    cache. The default of ``None`` keeps backward-compat for callers that
    only key by path + query.
    """
    prefix = f"{Path(repo_root).resolve()}::" if repo_root is not None else ""
    if not query:
        return prefix + path
    parts = []
    for k in sorted(query):
        for v in query[k]:
            parts.append(f"{k}={v}")
    return prefix + path + "?" + "&".join(parts)


def _serialize_payload(payload: Any, content_type: str) -> bytes:
    if content_type.startswith("application/json"):
        return json.dumps(payload, indent=2, sort_keys=True, default=_json_default).encode("utf-8")
    if content_type.startswith("text/html"):
        return str(payload).encode("utf-8")
    return str(payload).encode("utf-8")


def cached_response(
    cache_key: str,
    ttl_seconds: float,
    version_fn: Callable[[], tuple],
    builder: Callable[[], tuple[int, Any, str]],
) -> tuple[int, bytes, str, str]:
    """Serve a response through the cache. Returns (status, body_bytes, content_type, etag).

    Cache is skipped on non-2xx responses.
    """
    now = time.time()
    version_key = version_fn()
    with _CACHE_LOCK:
        entry = _CACHE.get(cache_key)
        if (
            entry is not None
            and entry.expires_at > now
            and entry.version_key == version_key
        ):
            return 200, entry.body_bytes, entry.content_type, entry.etag

    status_code, payload, content_type = builder()
    body_bytes = _serialize_payload(payload, content_type)
    etag = _weak_etag(body_bytes)

    if 200 <= status_code < 300:
        with _CACHE_LOCK:
            _CACHE[cache_key] = _CacheEntry(
                body_bytes=body_bytes,
                content_type=content_type,
                etag=etag,
                expires_at=now + ttl_seconds,
                version_key=version_key,
                built_at=now,
            )
    return status_code, body_bytes, content_type, etag


def _cache_stats() -> dict[str, Any]:
    with _CACHE_LOCK:
        return {
            "entries": len(_CACHE),
            "keys": sorted(_CACHE.keys()),
        }


# --- Background snapshot ---


class BackgroundSnapshot:
    """Fixed-delay background refresher for an expensive builder.

    Guarantees:
        - Never more than one refresh in flight.
        - Atomic snapshot swap: callers see either the old or new snapshot,
          never a partial one.
        - Exposes freshness metadata so callers can detect staleness.
    """

    def __init__(
        self,
        key: str,
        interval_seconds: float,
        builder: Callable[[], Any],
        stale_threshold_seconds: float | None = None,
    ) -> None:
        self.key = key
        self.interval_seconds = interval_seconds
        self.builder = builder
        # Default stale threshold: 5x refresh interval, min 60s.
        self.stale_threshold_seconds = (
            stale_threshold_seconds
            if stale_threshold_seconds is not None
            else max(60.0, interval_seconds * 5)
        )
        # ``_lock`` protects metadata reads; ``_build_lock`` enforces
        # single-in-flight so ``refresh_blocking()`` and the background
        # thread cannot overlap each other's build.
        self._lock = threading.Lock()
        self._build_lock = threading.Lock()
        self._snapshot: Any = None
        self._started_at: float | None = None
        self._completed_at: float | None = None
        self._duration_ms: float | None = None
        self._last_error: str | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run,
            name=f"snapshot-{self.key}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._refresh_once()
            # Fixed-delay: sleep AFTER completion so overruns never overlap.
            self._stop.wait(self.interval_seconds)

    def _refresh_once_locked(self) -> None:
        """Core refresh, assuming ``_build_lock`` is already held."""
        started = time.time()
        with self._lock:
            self._started_at = started
        try:
            snapshot = self.builder()
            err: str | None = None
        except Exception as exc:  # noqa: BLE001
            snapshot = None
            err = f"{type(exc).__name__}: {exc}"
        completed = time.time()
        with self._lock:
            if snapshot is not None:
                self._snapshot = snapshot
            self._completed_at = completed
            self._duration_ms = (completed - started) * 1000.0
            self._last_error = err

    def _refresh_once(self) -> None:
        """Serialize all builders through ``_build_lock``. The real
        enforcement of the "single in-flight" guarantee."""
        with self._build_lock:
            self._refresh_once_locked()

    def refresh_blocking(self, timeout: float | None = None) -> bool:
        """Trigger one refresh in the calling thread. Returns True if
        the refresh ran, False if ``timeout`` elapsed while waiting
        for the build lock. ``timeout=None`` waits forever."""
        lock_timeout = -1.0 if timeout is None else float(timeout)
        acquired = self._build_lock.acquire(timeout=lock_timeout)
        if not acquired:
            return False
        try:
            self._refresh_once_locked()
        finally:
            self._build_lock.release()
        return True

    def get(self) -> tuple[Any, dict[str, Any]]:
        now = time.time()
        with self._lock:
            snapshot = self._snapshot
            started = self._started_at
            completed = self._completed_at
            duration = self._duration_ms
            error = self._last_error
        stale_seconds = (now - completed) if completed is not None else None
        in_flight = (
            started is not None and (completed is None or started > completed)
        )
        if snapshot is None and completed is None:
            # Never completed a refresh — the caller will have to build sync.
            state = "refreshing"
        elif snapshot is None and error is not None:
            state = "degraded"
        elif stale_seconds is not None and stale_seconds > self.stale_threshold_seconds:
            state = "stale"
        else:
            state = "fresh"
        meta = {
            "refresh_started_at": started,
            "refresh_completed_at": completed,
            "refresh_duration_ms": duration,
            "refresh_error": error,
            "stale_seconds": stale_seconds,
            "stale_threshold_seconds": self.stale_threshold_seconds,
            "freshness_state": state,
            "refresh_in_flight": in_flight,
        }
        return snapshot, meta


# Registry of background snapshots. Started lazily on first access so that
# unit tests and `--help` invocations don't spawn threads.
_SNAPSHOTS: dict[str, BackgroundSnapshot] = {}
_SNAPSHOTS_LOCK = threading.Lock()


def _register_snapshot(
    key: str,
    interval_seconds: float,
    builder: Callable[[], Any],
    stale_threshold_seconds: float | None = None,
) -> BackgroundSnapshot:
    with _SNAPSHOTS_LOCK:
        existing = _SNAPSHOTS.get(key)
        if existing is not None:
            return existing
        snap = BackgroundSnapshot(key, interval_seconds, builder, stale_threshold_seconds)
        _SNAPSHOTS[key] = snap
    return snap


def _classify_path(path: str) -> str:
    if path.startswith(GENERATED_PREFIXES):
        return "generated"
    if path.startswith(PIPELINE_PREFIXES):
        return "pipeline"
    if path.startswith("src/") or path.startswith("scripts/") or path.startswith("tests/") or path.startswith("docs/"):
        return "source"
    return "other"


def build_worktree_status(repo_root: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--branch"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "repo_root": str(repo_root),
            "ok": False,
            "error": result.stderr.strip() or "git status failed",
        }

    lines = result.stdout.splitlines()
    branch = ""
    ahead = 0
    behind = 0
    if lines and lines[0].startswith("## "):
        branch_line = lines[0][3:]
        branch = branch_line
        if "..." in branch_line:
            branch = branch_line.split("...", 1)[0]
        if "[ahead " in branch_line:
            ahead = int(branch_line.split("[ahead ", 1)[1].split("]", 1)[0].split(",")[0])
        if "[behind " in branch_line:
            behind = int(branch_line.split("[behind ", 1)[1].split("]", 1)[0].split(",")[0])

    entries: list[dict[str, Any]] = []
    counts = {
        "total": 0,
        "staged": 0,
        "unstaged": 0,
        "untracked": 0,
        "conflicted": 0,
    }
    categories = {"source": 0, "generated": 0, "pipeline": 0, "other": 0}

    for line in lines[1:]:
        if not line.strip():
            continue
        if line.startswith("?? "):
            path = line[3:]
            staged = False
            unstaged = False
            untracked = True
            conflicted = False
            index_status = "?"
            worktree_status = "?"
        else:
            index_status = line[0]
            worktree_status = line[1]
            path = line[3:]
            staged = index_status not in {" ", "?"}
            unstaged = worktree_status not in {" ", "?"}
            untracked = False
            conflicted = index_status == "U" or worktree_status == "U"
        category = _classify_path(path)
        counts["total"] += 1
        counts["staged"] += int(staged)
        counts["unstaged"] += int(unstaged)
        counts["untracked"] += int(untracked)
        counts["conflicted"] += int(conflicted)
        categories[category] += 1
        entries.append(
            {
                "path": path,
                "index_status": index_status,
                "worktree_status": worktree_status,
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "conflicted": conflicted,
                "category": category,
            }
        )

    return {
        "repo_root": str(repo_root),
        "ok": True,
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "dirty": counts["total"] > 0,
        "counts": counts,
        "categories": categories,
        "entries": entries,
    }


def build_worktrees_list(repo_root: Path) -> dict[str, Any]:
    """List every worktree attached to the primary repo.

    Parses ``git worktree list --porcelain``. Returns a compact payload
    suitable for agent cold-start: agents need to know about sibling
    worktrees (e.g. ``codex-wt-*``) to avoid colliding on the same branch.
    """
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "ok": False,
            "error": result.stderr.strip() or "git worktree list failed",
            "worktrees": [],
        }

    worktrees: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in result.stdout.splitlines():
        if not line:
            if current is not None:
                worktrees.append(current)
                current = None
            continue
        if line.startswith("worktree "):
            if current is not None:
                worktrees.append(current)
            current = {
                "path": line[len("worktree ") :],
                "branch": None,
                "head": None,
                "detached": False,
                "locked": False,
                "prunable": False,
            }
        elif current is None:
            continue
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD ") :]
        elif line.startswith("branch "):
            # Format: ``branch refs/heads/<name>``.
            ref = line[len("branch ") :]
            if ref.startswith("refs/heads/"):
                current["branch"] = ref[len("refs/heads/") :]
            else:
                current["branch"] = ref
        elif line == "detached":
            current["detached"] = True
        elif line.startswith("locked"):
            current["locked"] = True
        elif line.startswith("prunable"):
            current["prunable"] = True
    if current is not None:
        worktrees.append(current)

    # Enrich each entry with a dirty-counts summary. This is the
    # signal operators actually want ("which worktree is lively?")
    # and without it agents had to shell into every worktree.
    #
    # ``dirty`` is tri-state: True/False when counts were obtained,
    # ``None`` when we couldn't read the worktree (missing path,
    # permission error, prunable ref). "unknown" and "clean" are
    # materially different; a False here would be a false negative.
    for wt in worktrees:
        wt_path = Path(wt["path"])
        counts = _worktree_dirty_counts(wt_path) if wt_path.exists() else None
        wt["counts"] = counts
        if counts is None:
            wt["dirty"] = None
        else:
            wt["dirty"] = bool(counts.get("total", 0))

    primary_path = str(repo_root)
    return {
        "ok": True,
        "primary": primary_path,
        "count": len(worktrees),
        "worktrees": worktrees,
    }


def _worktree_dirty_counts(worktree_path: Path) -> dict[str, Any] | None:
    """Run ``git status --porcelain=v1`` inside ``worktree_path`` and
    return a summary of counts. Returns ``None`` on failure so callers
    can distinguish "unknown" from "clean".

    ``total`` counts each PATH once (matching the primary-worktree
    ``build_worktree_status`` semantics), so a file that is both
    staged and unstaged adds 1, not 2. ``staged`` / ``unstaged`` /
    ``untracked`` remain per-status counts for operators who want
    breakdowns — those may overlap.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    staged = unstaged = untracked = conflicted = 0
    total_paths = 0
    for line in result.stdout.splitlines():
        if not line:
            continue
        total_paths += 1
        if line.startswith("?? "):
            untracked += 1
            continue
        idx = line[0] if line else " "
        wt = line[1] if len(line) > 1 else " "
        if idx == "U" or wt == "U":
            conflicted += 1
        if idx not in (" ", "?"):
            staged += 1
        if wt not in (" ", "?"):
            unstaged += 1
    return {
        # ``total`` is unique-path count (matches primary-worktree
        # ``build_worktree_status``). staged/unstaged/untracked are
        # per-status counts and may overlap — a file with both a
        # staged and an unstaged change is in both sub-counts but
        # contributes 1 to total.
        "total": total_paths,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "conflicted": conflicted,
    }


def _db_latest_for_module(db_path: Path, module_key: str) -> dict[str, Any] | None:
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        job = conn.execute(
            """
            SELECT *
            FROM jobs
            WHERE module_key = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (module_key,),
        ).fetchone()
        event = conn.execute(
            """
            SELECT *
            FROM events
            WHERE module_key = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (module_key,),
        ).fetchone()
    finally:
        conn.close()

    return {
        "db_path": str(db_path),
        "latest_job": dict(job) if job is not None else None,
        "latest_event": (
            {**dict(event), "payload_json": _load_json(str(event["payload_json"]))}
            if event is not None
            else None
        ),
    }


def build_module_state(repo_root: Path, module_key: str) -> dict[str, Any]:
    from status import _build_lab_summary, _extract_frontmatter, _git_head_for_file
    from translation_v2 import detect_module_state

    normalized = module_key[:-3] if module_key.endswith(".md") else module_key
    en_path = repo_root / "src" / "content" / "docs" / f"{normalized}.md"
    uk_path = repo_root / "src" / "content" / "docs" / "uk" / f"{normalized}.md"
    frontmatter = _extract_frontmatter(en_path) if en_path.exists() else {}
    lab = frontmatter.get("lab")
    lab_id = None
    if isinstance(lab, str) and lab.strip():
        lab_id = lab.strip()
    elif isinstance(lab, dict):
        for key in ("id", "name", "slug"):
            value = lab.get(key)
            if isinstance(value, str) and value.strip():
                lab_id = value.strip()
                break

    fact_ledger = repo_root / ".pipeline" / "fact-ledgers" / f"{normalized.replace('/', '__')}.json"
    lab_summary = _build_lab_summary(repo_root)
    lab_state = next((item for item in lab_summary["items"] if item["lab_id"] == lab_id), None) if lab_id else None

    state = {
        "module_key": normalized,
        "track": normalized.split("/", 1)[0] if "/" in normalized else normalized,
        "english_path": str(en_path),
        "english_exists": en_path.exists(),
        "english_commit": _git_head_for_file(repo_root, en_path) if en_path.exists() else "",
        "ukrainian_path": str(uk_path),
        "ukrainian_exists": uk_path.exists(),
        "ukrainian_state": detect_module_state(repo_root, normalized) if en_path.exists() else None,
        "frontmatter": frontmatter,
        "fact_ledger": {
            "path": str(fact_ledger),
            "exists": fact_ledger.exists(),
        },
        "lab": {
            "lab_id": lab_id,
            "state": lab_state,
        },
    }

    # Fold orchestration + lease inline so "why is X blocked" is one
    # call (the /api/module/{key}/orchestration/latest and /lease
    # endpoints remain for back-compat and for callers who only want
    # that slice).
    state["orchestration"] = build_module_orchestration_latest(repo_root, normalized)
    state["lease"] = build_module_lease(repo_root, normalized)

    state["diagnostics"] = build_module_diagnostics(repo_root, normalized, state)

    # Add orchestration-derived diagnostics. We do this AFTER the
    # base diagnostics so pipeline signals append rather than
    # duplicate what ``build_module_diagnostics`` already produced.
    latest_job = (state["orchestration"].get("v2") or {}).get("latest_job") or {}
    queue_state = latest_job.get("queue_state")
    if queue_state == "rejected":
        state["diagnostics"].append(_diag(
            severity="critical",
            code="pipeline_rejected",
            summary="Pipeline v2 rejected the last run",
            source="pipeline_v2.jobs",
            next_action=f"GET /api/pipeline/v2/events?module={normalized}",
        ))
    elif queue_state == "dead_letter":
        state["diagnostics"].append(_diag(
            severity="critical",
            code="pipeline_dead_letter",
            summary="Module is in pipeline dead-letter",
            source="pipeline_v2.jobs",
            next_action=f"GET /api/pipeline/v2/events?module={normalized}",
        ))
    if state["lease"].get("held"):
        lease_info = state["lease"].get("lease") or {}
        leased_by = lease_info.get("leased_by", "unknown")
        secs = lease_info.get("seconds_to_expiry")
        state["diagnostics"].append(_diag(
            severity="info",
            code="lease_held",
            summary=f"Leased by {leased_by} ({secs}s to expiry)" if secs else f"Leased by {leased_by}",
            source="pipeline_v2.jobs",
            next_action="wait for lease to release before claiming work",
        ))

    return state


def build_module_orchestration_latest(repo_root: Path, module_key: str) -> dict[str, Any]:
    normalized = module_key[:-3] if module_key.endswith(".md") else module_key
    return {
        "module_key": normalized,
        "v2": _db_latest_for_module(repo_root / ".pipeline" / "v2.db", normalized),
        "translation_v2": _db_latest_for_module(repo_root / ".pipeline" / "translation_v2.db", normalized),
    }


# ============================================================
# Phase C: leases, diagnostics, quality, pipeline events/stuck,
# reviews, bridge messages
# ============================================================


def _query_sqlite_rows(
    db_path: Path,
    sql: str,
    params: tuple = (),
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Run a read-only query and return rows as dicts. Empty list if
    the DB is missing or the referenced table doesn't exist; every
    other sqlite error propagates so the handler can surface it as a
    500 (silently swallowing hides schema-drift bugs)."""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=1.0)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchmany(limit)]
    except sqlite3.OperationalError as exc:
        # "no such table" is an expected "feature not yet provisioned"
        # state (e.g. bridge DB absent before first message). Anything
        # else — "no such column", type mismatch, etc. — is a bug the
        # caller needs to see.
        if "no such table" in str(exc):
            return []
        raise
    finally:
        conn.close()


# Timestamps in .pipeline/v2.db are Unix epoch SECONDS (SQLite's
# strftime('%s','now') — see scripts/pipeline_v2/control_plane.py). All
# comparisons here must use the same unit.


def build_pipeline_leases(repo_root: Path, *, now_seconds: int | None = None) -> dict[str, Any]:
    """Active pipeline leases (from ``jobs`` table).

    A lease is active when ``leased_by`` is set and ``lease_expires_at``
    is in the future. Payload ordered by expiry so the most-at-risk
    leases are first.
    """
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return {"db_path": str(db_path), "active": [], "count": 0, "exists": False}

    now_seconds = now_seconds if now_seconds is not None else int(time.time())
    rows = _query_sqlite_rows(
        db_path,
        """
        SELECT module_key, phase, queue_state, model, priority,
               leased_by, lease_id, leased_at, lease_expires_at
        FROM jobs
        WHERE leased_by IS NOT NULL
          AND lease_expires_at IS NOT NULL
          AND lease_expires_at > ?
        ORDER BY lease_expires_at ASC
        """,
        (now_seconds,),
    )
    for row in rows:
        exp = row.get("lease_expires_at")
        if isinstance(exp, (int, float)):
            row["seconds_to_expiry"] = max(0, int(exp) - now_seconds)
    return {
        "db_path": str(db_path),
        "exists": True,
        "count": len(rows),
        "active": rows,
        "queried_at_seconds": now_seconds,
    }


def build_module_lease(
    repo_root: Path, module_key: str, *, now_seconds: int | None = None
) -> dict[str, Any]:
    """Lease state for one module. Returns ``{held: False}`` when no
    active lease exists (vs 404 semantics, which would be ambiguous
    between 'no lease' and 'no pipeline DB')."""
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return {
            "module_key": module_key,
            "held": False,
            "reason": "missing_db",
            "db_path": str(db_path),
        }
    now_seconds = now_seconds if now_seconds is not None else int(time.time())
    rows = _query_sqlite_rows(
        db_path,
        """
        SELECT module_key, phase, queue_state, model, priority,
               leased_by, lease_id, leased_at, lease_expires_at
        FROM jobs
        WHERE module_key = ?
          AND leased_by IS NOT NULL
          AND lease_expires_at IS NOT NULL
          AND lease_expires_at > ?
        ORDER BY lease_expires_at DESC
        LIMIT 1
        """,
        (module_key, now_seconds),
    )
    if not rows:
        return {"module_key": module_key, "held": False}
    row = rows[0]
    exp = row.get("lease_expires_at")
    if isinstance(exp, (int, float)):
        row["seconds_to_expiry"] = max(0, int(exp) - now_seconds)
    return {"module_key": module_key, "held": True, "lease": row}


# ---- pipeline events / stuck ----


def build_pipeline_events(
    repo_root: Path,
    module_key: str | None,
    since_seconds: int | None,
    limit: int = 200,
) -> dict[str, Any]:
    """Timeline view of ``.pipeline/v2.db`` events.

    Filter by ``module_key`` (optional) and ``since_seconds`` (optional,
    inclusive Unix-epoch seconds to match the control-plane's time
    unit). Newest-first, capped by ``limit`` (default 200, max 2000).
    """
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return {"db_path": str(db_path), "exists": False, "count": 0, "events": []}
    capped = max(1, min(int(limit), 2000))
    clauses: list[str] = []
    params: list[Any] = []
    if module_key:
        clauses.append("module_key = ?")
        params.append(module_key)
    if since_seconds is not None:
        clauses.append("at >= ?")
        params.append(int(since_seconds))
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = _query_sqlite_rows(
        db_path,
        f"""
        SELECT id, type, module_key, lease_id, payload_json, at
        FROM events
        {where}
        ORDER BY id DESC
        LIMIT {capped}
        """,
        tuple(params),
    )
    for row in rows:
        payload = row.get("payload_json")
        if isinstance(payload, str):
            row["payload_json"] = _load_json(payload)
    return {
        "db_path": str(db_path),
        "exists": True,
        "module_key": module_key,
        "since_seconds": since_seconds,
        "limit": capped,
        "count": len(rows),
        "events": rows,
    }


# Phases considered "in-flight" when computing stuck modules. A job
# that's been sitting in one of these states longer than the threshold
# is a candidate for human attention.
_STUCK_IN_FLIGHT_STATES = ("leased", "running", "in_progress")
_DEFAULT_STUCK_THRESHOLD_SECONDS = 3600  # 1 hour


def build_pipeline_stuck(
    repo_root: Path,
    *,
    threshold_seconds: int = _DEFAULT_STUCK_THRESHOLD_SECONDS,
    now_seconds: int | None = None,
) -> dict[str, Any]:
    """Dead-letter view — jobs stuck at a phase longer than ``threshold_seconds``.

    Two signals are surfaced:

    - ``stuck_leased``: jobs whose lease has expired OR whose
      ``leased_at`` is older than the threshold.
    - ``stuck_in_state``: jobs in an in-flight ``queue_state`` with no
      recent event *for the current attempt*. Events are correlated
      to the job's current ``lease_id`` — a recent event from an
      earlier lease for the same module must not mask a hung current
      lease.
    """
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return {"db_path": str(db_path), "exists": False, "stuck_leased": [], "stuck_in_state": []}

    now_seconds = now_seconds if now_seconds is not None else int(time.time())
    cutoff = now_seconds - threshold_seconds

    stuck_leased = _query_sqlite_rows(
        db_path,
        """
        SELECT module_key, phase, queue_state, leased_by, lease_id,
               leased_at, lease_expires_at
        FROM jobs
        WHERE leased_by IS NOT NULL
          AND (
              (lease_expires_at IS NOT NULL AND lease_expires_at < ?)
              OR (leased_at IS NOT NULL AND leased_at < ?)
          )
        ORDER BY leased_at ASC
        LIMIT 500
        """,
        (now_seconds, cutoff),
    )

    # Correlate events by lease_id (and fall back to module_key for
    # jobs without a lease_id) so a fresh event from a previous
    # attempt can't mask a hung current attempt.
    stuck_in_state = _query_sqlite_rows(
        db_path,
        f"""
        SELECT j.module_key, j.phase, j.queue_state, j.leased_by,
               j.lease_id, j.leased_at,
               (
                   SELECT MAX(at) FROM events e
                   WHERE (j.lease_id IS NOT NULL AND e.lease_id = j.lease_id)
                      OR (j.lease_id IS NULL AND e.module_key = j.module_key)
               ) AS last_event_at
        FROM jobs j
        WHERE j.queue_state IN ({','.join('?' for _ in _STUCK_IN_FLIGHT_STATES)})
        ORDER BY j.leased_at ASC
        LIMIT 500
        """,
        tuple(_STUCK_IN_FLIGHT_STATES),
    )
    # Keep only those whose last event for the current attempt is
    # older than the threshold (NULL/0 counts as stuck — a running
    # job that has emitted zero events is stuck by definition).
    stuck_in_state = [
        row for row in stuck_in_state
        if (row.get("last_event_at") or 0) < cutoff
    ]

    return {
        "db_path": str(db_path),
        "exists": True,
        "threshold_seconds": threshold_seconds,
        "queried_at_seconds": now_seconds,
        "stuck_leased_count": len(stuck_leased),
        "stuck_leased": stuck_leased,
        "stuck_in_state_count": len(stuck_in_state),
        "stuck_in_state": stuck_in_state,
    }


# ---- reviews audit log ----


_REVIEW_AUDIT_DIR = Path(".pipeline") / "reviews"


def _review_filename_to_module_key(filename: str) -> str:
    """Filenames use ``__`` as path separators. Strip trailing
    ``.md`` / ``.lock``."""
    name = filename
    for suffix in (".md", ".lock"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.replace("__", "/")


def _module_key_to_review_filename(module_key: str) -> str:
    return module_key.replace("/", "__") + ".md"


def build_reviews_index(repo_root: Path) -> dict[str, Any]:
    """List every review artifact with its module key and last-modified
    timestamp. Callers fetch the body via ``/api/reviews?module=...``."""
    reviews_dir = repo_root / _REVIEW_AUDIT_DIR
    if not reviews_dir.is_dir():
        return {"reviews_dir": str(reviews_dir), "exists": False, "count": 0, "reviews": []}
    reviews: list[dict[str, Any]] = []
    for path in sorted(reviews_dir.glob("*.md")):
        try:
            mtime = path.stat().st_mtime
            size = path.stat().st_size
        except OSError:
            mtime, size = 0.0, 0
        reviews.append({
            "module_key": _review_filename_to_module_key(path.name),
            "filename": path.name,
            "size": size,
            "mtime": mtime,
        })
    return {
        "reviews_dir": str(reviews_dir),
        "exists": True,
        "count": len(reviews),
        "reviews": reviews,
    }


def build_module_reviews(
    repo_root: Path,
    module_key: str,
    *,
    max_bytes: int = 200_000,
) -> dict[str, Any] | None:
    """Return the full review log for a module, capped at ``max_bytes``.

    The log is a markdown file produced by the pipeline with one
    section per review pass (writer, plan, duration, reviewer,
    severity, etc.). We return it as a single ``body`` string so
    agents can parse what they need without the API pretending to
    understand every variation of the format.
    """
    reviews_dir = repo_root / _REVIEW_AUDIT_DIR
    path = reviews_dir / _module_key_to_review_filename(module_key)
    if not path.is_file():
        return None
    try:
        stat = path.stat()
        on_disk_size = stat.st_size
        mtime = stat.st_mtime
    except OSError:
        on_disk_size, mtime = 0, 0.0
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    truncated = False
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
        truncated = True
    try:
        body = raw.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        body = raw.decode("latin-1", errors="replace")
    return {
        "module_key": module_key,
        "path": str(path),
        "size": on_disk_size,
        "body_size": len(body.encode("utf-8")),
        "truncated": truncated,
        "max_bytes": max_bytes if truncated else None,
        "mtime": mtime,
        "body": body,
    }


# ---- bridge messages ----


def _resolve_bridge_db_path(repo_root: Path) -> Path:
    """Locate ``messages.db`` the same way the bridge CLI does.

    Precedence:
      1. ``$AB_DB_PATH`` — unconditional. An explicit override must
         win even if the file doesn't yet exist; the caller surfaces
         ``exists=False`` when that happens. (Codex round-2 caught that
         previously we only honored AB_DB_PATH when the file already
         existed — quietly reading the wrong DB on a fresh override.)
      2. ``.bridge/messages.db`` — set by the ``scripts/ab`` wrapper
         and by the repo setup guide; the repo convention.
      3. ``.mcp/servers/message-broker/messages.db`` — the upstream
         Python default when no wrapper is used.
    Within 2 and 3, the first existing file wins; if neither exists,
    the convention path (2) is returned.
    """
    explicit = os.environ.get("AB_DB_PATH")
    if explicit:
        return Path(explicit)
    candidates = [
        repo_root / ".bridge" / "messages.db",
        repo_root / ".mcp" / "servers" / "message-broker" / "messages.db",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def build_bridge_messages(
    repo_root: Path,
    since: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Recent agent-bridge messages from the bridge DB.

    Filter ``since`` is an ISO-8601 timestamp (string comparison is
    safe — the bridge stores ISO-8601 UTC). ``limit`` caps at 500 rows
    so a single call can't overwhelm a polling agent.
    """
    db_path = _resolve_bridge_db_path(repo_root)
    if not db_path.exists():
        return {"db_path": str(db_path), "exists": False, "count": 0, "messages": []}
    capped = max(1, min(int(limit), 500))
    if since:
        rows = _query_sqlite_rows(
            db_path,
            f"""
            SELECT id, task_id, from_llm, to_llm, message_type,
                   content, timestamp, acknowledged, status
            FROM messages
            WHERE timestamp >= ?
            ORDER BY id DESC
            LIMIT {capped}
            """,
            (since,),
            limit=capped,
        )
    else:
        rows = _query_sqlite_rows(
            db_path,
            f"""
            SELECT id, task_id, from_llm, to_llm, message_type,
                   content, timestamp, acknowledged, status
            FROM messages
            ORDER BY id DESC
            LIMIT {capped}
            """,
            limit=capped,
        )
    # Truncate message content to a readable preview so a burst of
    # long messages doesn't blow up the response. Full content stays
    # accessible via the bridge CLI.
    for row in rows:
        content = row.get("content")
        if isinstance(content, str) and len(content) > 400:
            row["content_preview"] = content[:400] + "… (truncated)"
            row["content_full_length"] = len(content)
            row.pop("content", None)
    return {
        "db_path": str(db_path),
        "exists": True,
        "since": since,
        "limit": capped,
        "count": len(rows),
        "messages": rows,
    }


# ---- quality scores ----


_QUALITY_AUDIT_CACHE: dict[str, dict[str, Any]] = {}
_QUALITY_AUDIT_CACHE_LOCK = threading.Lock()


# Matches rows like:
#   | CKA 2.8: Scheduler Lifecycle Theory | CKA | 55 | **1.3** | Critical | ... |
# Score is the first bold-number occurrence.
_QUALITY_ROW_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*\*?\*?([0-9]+(?:\.[0-9]+)?)\*?\*?\s*\|"
)


def build_quality_scores(repo_root: Path) -> dict[str, Any]:
    """Parse ``docs/quality-audit-results.md`` and expose per-module
    rubric scores.

    The file is markdown with multiple tables; we walk it row-by-row
    extracting ``(module, track, lines, score)``. Cached by mtime.
    """
    audit_path = repo_root / "docs" / "quality-audit-results.md"
    if not audit_path.exists():
        return {"audit_path": str(audit_path), "exists": False, "modules": [], "count": 0}

    try:
        mtime = audit_path.stat().st_mtime
    except OSError:
        mtime = 0.0
    key = str(audit_path.resolve())
    with _QUALITY_AUDIT_CACHE_LOCK:
        entry = _QUALITY_AUDIT_CACHE.get(key)
        if entry is not None and entry["mtime"] == mtime:
            return entry["data"]

    try:
        text = audit_path.read_text(encoding="utf-8")
    except OSError:
        return {"audit_path": str(audit_path), "exists": False, "modules": [], "count": 0}

    modules: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        # Skip table header / separator rows.
        if "---" in line or line.startswith("| Module") or line.startswith("| Rating"):
            continue
        match = _QUALITY_ROW_RE.match(line)
        if not match:
            continue
        module = match.group(1).strip()
        track = match.group(2).strip()
        lines_str = match.group(3).strip()
        score = float(match.group(4))
        try:
            lines_count = int(lines_str) if lines_str.isdigit() else None
        except ValueError:
            lines_count = None
        # Skip the score-distribution table (first col is "Excellent"/"Good"/etc).
        if module in {"Excellent", "Good", "Needs Work", "Poor", "Critical"}:
            continue
        severity = "critical" if score < 2.0 else (
            "poor" if score < 2.5 else (
                "needs_work" if score < 3.5 else (
                    "good" if score < 4.5 else "excellent"
                )
            )
        )
        modules.append({
            "module": module,
            "track": track,
            "lines": lines_count,
            "score": score,
            "severity": severity,
        })

    scores = [m["score"] for m in modules]
    avg = round(sum(scores) / len(scores), 2) if scores else None
    critical = [m for m in modules if m["severity"] == "critical"]
    poor = [m for m in modules if m["severity"] == "poor"]
    data = {
        "audit_path": str(audit_path),
        "exists": True,
        "mtime": mtime,
        "count": len(modules),
        "average": avg,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "critical": critical,
        "critical_count": len(critical),
        "poor_count": len(poor),
        "modules": modules,
    }
    with _QUALITY_AUDIT_CACHE_LOCK:
        _QUALITY_AUDIT_CACHE[key] = {"mtime": mtime, "data": data}
    return data


# ---- module diagnostics ----


def _diag(
    severity: str,
    code: str,
    summary: str,
    source: str,
    next_action: str | None = None,
) -> dict[str, Any]:
    """Build a structured diagnostic entry.

    Shape per Codex round-5 review: ``severity`` (info|warn|critical),
    ``code`` (stable string agents can switch on), ``summary`` (human-
    readable one-liner), ``source`` (which subsystem flagged it), and
    ``next_action`` (suggested drill-down command or endpoint). The
    dict shape is richer than a plain string tag and lets agents both
    triage and act without a second lookup.
    """
    entry: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "summary": summary,
        "source": source,
    }
    if next_action is not None:
        entry["next_action"] = next_action
    return entry


def build_module_diagnostics(
    repo_root: Path,
    module_key: str,
    base_state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Actionable diagnostics for a module.

    Each entry is a dict ``{severity, code, summary, source, next_action?}``
    so agents can triage by severity, switch on the stable ``code``, and
    follow ``next_action`` without guessing where to look next.
    """
    diagnostics: list[dict[str, Any]] = []

    if not base_state.get("english_exists"):
        diagnostics.append(_diag(
            severity="critical",
            code="english_missing",
            summary="Module path has no EN source file",
            source="filesystem",
            next_action="git log -- src/content/docs/<module>",
        ))
        return diagnostics

    frontmatter = base_state.get("frontmatter") or {}
    if not isinstance(frontmatter, dict) or not frontmatter:
        diagnostics.append(_diag(
            severity="warn",
            code="frontmatter_missing",
            summary="EN file parses with empty/invalid frontmatter",
            source="frontmatter",
            next_action="read the first ~10 lines of english_path",
        ))
    elif not frontmatter.get("title"):
        diagnostics.append(_diag(
            severity="warn",
            code="frontmatter_no_title",
            summary="Frontmatter is missing a `title:` key",
            source="frontmatter",
            next_action="read the first ~10 lines of english_path",
        ))

    lab = base_state.get("lab") or {}
    if not lab.get("lab_id"):
        diagnostics.append(_diag(
            severity="info",
            code="no_lab",
            summary="Module has no killercoda/lab attached",
            source="frontmatter.lab",
            next_action="GET /api/labs/status",
        ))

    fact = base_state.get("fact_ledger") or {}
    if not fact.get("exists"):
        diagnostics.append(_diag(
            severity="info",
            code="no_fact_ledger",
            summary="Module has no .pipeline/fact-ledgers/ entry yet",
            source="pipeline_v2",
            next_action="pipeline enqueue — scripts/pipeline_v2 CLI",
        ))

    if not base_state.get("ukrainian_exists"):
        diagnostics.append(_diag(
            severity="info",
            code="uk_translation_missing",
            summary="No Ukrainian translation present",
            source="filesystem",
            next_action="GET /api/translation/v2/status",
        ))
    else:
        uk_state = base_state.get("ukrainian_state") or {}
        if isinstance(uk_state, dict):
            status = uk_state.get("status") or uk_state.get("state")
            happy = {"ok", "current", "fresh", "synced"}
            if status and status not in happy:
                diagnostics.append(_diag(
                    severity="warn",
                    code=f"uk_state_{status}",
                    summary=f"Ukrainian translation state: {status}",
                    source="translation_v2",
                    next_action=f"GET /api/translation/v2/status (filter for {status})",
                ))

    # Rubric severity from docs/quality-audit-results.md.
    try:
        quality = build_quality_scores(repo_root)
    except Exception:  # noqa: BLE001
        quality = {"modules": []}
    sev = _rubric_severity_for_module(module_key, quality.get("modules", []))
    if sev in ("critical", "poor"):
        diagnostics.append(_diag(
            severity="critical" if sev == "critical" else "warn",
            code=f"rubric_{sev}",
            summary=f"Rubric score marks this module as {sev}",
            source="docs/quality-audit-results.md",
            next_action="GET /api/quality/scores",
        ))

    # Orchestration-driven diagnostics (pipeline stuck / dead-letter)
    # are attached by ``build_module_state`` after orchestration data
    # is fetched, so we don't duplicate the sqlite round-trip here.
    return diagnostics


_MODULE_NUMBER_RE = re.compile(r"module-([0-9]+(?:\.[0-9]+)*)")
# Used to strip ``module-X.Y-`` prefix from a slug to get a readable
# name token set.
_MODULE_NUMBER_PREFIX_RE = re.compile(r"^module-[0-9]+(?:\.[0-9]+)*-")
_PART_PREFIX_RE = re.compile(r"^part[0-9]+-?")

# Track slugs → strings likely to appear (case-insensitive) in the
# audit doc's track column. Kept narrow so we don't false-match
# (e.g. "cka" matching "kcna" substrings).
_TRACK_ALIASES: dict[str, tuple[str, ...]] = {
    "cka": ("cka",),
    "ckad": ("ckad",),
    "cks": ("cks",),
    "kcna": ("kcna",),
    "kcsa": ("kcsa",),
    "prerequisites": (
        "prerequisites", "k8s basics", "cloud native 101", "modern devops",
        "zero to terminal", "philosophy", "design",
    ),
    "linux": ("linux",),
    "cloud": ("cloud",),
    "platform": ("platform", "toolkit", "sre", "gitops", "devsecops", "mlops", "aiops"),
    "on-prem": ("on-prem", "on-premises"),
    "on-premises": ("on-prem", "on-premises"),
    "ai-ml-engineering": (
        "ai/ml", "ai-ml", "ai/ml engineering", "mlops", "genai",
        "advanced genai", "multimodal", "deep learning", "classical ml",
    ),
}

# Tokens that are too generic to contribute to the name-overlap match
# (e.g. "module", "part", "intro"). ``basics`` was removed in round-3:
# it can be the only distinguishing token in short unnumbered labels.
_NAME_TOKEN_STOPLIST = frozenset({
    "module", "part", "the", "a", "an", "and", "of", "to", "for", "with",
    "intro", "introduction", "overview",
})


# Labels typically look like ``<Track>[ <number>][:-] <Name>``.
# Capture the leading track prefix so we can match even when the
# audit ``Track`` column is a subtrack like "Workloads" or "AWS".
_LABEL_TRACK_PREFIX_RE = re.compile(
    r"^\s*(?P<track>[A-Za-z][A-Za-z/\- ]*?)\s*(?:[0-9]+(?:\.[0-9]+)*)?\s*[:\-]"
)


def _audit_row_track_tokens(row: dict[str, Any]) -> set[str]:
    """Return every track-like string attached to an audit row.

    Combines the ``Track`` column (typically a subtrack like
    ``Workloads`` or ``AWS``) with the ``Track:`` prefix of the
    ``Module`` label (``CKA 2.8: ...``, ``Platform: ...``).
    """
    out: set[str] = set()
    track_col = str(row.get("track", "")).strip().lower()
    if track_col:
        out.add(track_col)
    module_label = str(row.get("module", ""))
    m = _LABEL_TRACK_PREFIX_RE.match(module_label)
    if m:
        out.add(m.group("track").strip().lower())
    return out


def _alias_matches(alias: str, candidates: set[str]) -> bool:
    """Whole-word check so ``cka`` doesn't match ``ckad``."""
    pattern = re.compile(r"\b" + re.escape(alias) + r"\b")
    return any(pattern.search(c) for c in candidates)


_CERT_TRACKS = frozenset({"cka", "ckad", "cks", "kcna", "kcsa"})


def _track_word_set(track_slug: str | None, aliases: tuple[str, ...]) -> set[str]:
    """Tokens that should NOT count as a non-track overlap signal.

    Used to make the name-overlap match meaningful: an overlap of
    ``{platform, sre}`` between a module path and a "Platform: SRE…"
    label is vacuous when both are track tokens for this module.
    """
    out: set[str] = set()
    if track_slug:
        out |= _normalize_name_tokens(track_slug)
    for alias in aliases:
        out |= _normalize_name_tokens(alias)
    # Cert paths share a ``k8s/`` parent segment that's structural,
    # not semantic. Without this the label "CKA: k8s.io Navigation"
    # matches any k8s/cka/* module via the vacuous ``{cka, k8s}``
    # overlap.
    if track_slug in _CERT_TRACKS:
        out.add("k8s")
    return out


def _normalize_name_tokens(text: str) -> set[str]:
    """Split a string into a lowercase-alphanumeric token set suitable
    for overlap comparison. Drops pure numbers and stop-words."""
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    return {
        tok
        for tok in tokens
        if tok
        and not tok.isdigit()
        and tok not in _NAME_TOKEN_STOPLIST
    }


def _rubric_severity_for_module(
    module_key: str, audit_modules: list[dict[str, Any]]
) -> str | None:
    """Best-effort match from a module path to an audit-doc entry.

    Matching has three stages, each requiring a STRICT track match
    when the module path has a recognized track — we never fall back
    to "any track matches" (that was a round-2 false-positive source).

    1. Numbered match. Extract ``(track, number)`` from the path.
       Require the audit ``track`` column to match a track alias
       AND the audit ``module`` label to contain the number with
       word boundaries (so "2.8" doesn't match "12.8"). Accepts
       labels like "CKA 2.8: ...", "... 2.8 - ...", "... 2.8) ...".

    2. Name-overlap match. For audit rows that have no module
       number (e.g. ``Platform: Systems Thinking``), compute the
       overlap between the module path's name tokens and the
       label's tokens. Require ≥ 2 shared tokens plus a track-
       alias match. This covers the non-numbered rubric entries
       that round-2 flagged.

    3. Return None. Unknown track → no match, to avoid the
       "any row wins" false positive.
    """
    segments = module_key.split("/")
    last_raw = segments[-1]
    last = last_raw.lower()
    num_match = _MODULE_NUMBER_RE.search(last)
    number = num_match.group(1) if num_match else None

    # Detect the track from the path.
    track_slug = None
    for seg in segments:
        key = seg.lower()
        if key in _TRACK_ALIASES:
            track_slug = key
            break
    aliases = _TRACK_ALIASES.get(track_slug, ()) if track_slug else ()

    if not aliases:
        # Unknown track → no match (round-2 caught "any row wins"
        # false positives).
        return None

    # Track tokens for THIS module. Used both to filter audit rows
    # (whole-word match to avoid cka/ckad collision) and to compute
    # "non-track overlap" in stage 2.
    track_word_set = _track_word_set(track_slug, aliases)

    def _row_track_matches(row: dict[str, Any]) -> bool:
        candidates = _audit_row_track_tokens(row)
        return any(_alias_matches(alias, candidates) for alias in aliases)

    # ----- stage 1: numbered match -----
    if number:
        number_re = re.compile(
            r"(?:^|[\s(])" + re.escape(number) + r"(?=[\s:\-\)—.,])"
        )
        for entry in audit_modules:
            label = str(entry.get("module", ""))
            if not number_re.search(label):
                continue
            if _row_track_matches(entry):
                return entry.get("severity")

    # ----- stage 2: name-overlap match -----
    name_slug = _MODULE_NUMBER_PREFIX_RE.sub("", last)
    path_tokens = _normalize_name_tokens(name_slug)
    for seg in segments[:-1]:
        if _PART_PREFIX_RE.match(seg):
            continue
        path_tokens |= _normalize_name_tokens(seg)
    if not path_tokens:
        return None

    best: tuple[int, str | None] = (0, None)
    for entry in audit_modules:
        if not _row_track_matches(entry):
            continue
        label_tokens = _normalize_name_tokens(str(entry.get("module", "")))
        overlap = path_tokens & label_tokens
        # Require ≥ 2 overlap AND at least one NON-track-alias token
        # in the overlap; otherwise ``{platform, sre}`` alone would
        # attach any "Platform: ... SRE ..." row to every platform
        # module containing "sre".
        if len(overlap) < 2:
            continue
        non_track = overlap - track_word_set
        if not non_track:
            continue
        score = len(overlap) + len(non_track)
        if score > best[0]:
            best = (score, entry.get("severity"))
    return best[1]


def build_issue_watch_state(repo_root: Path, issue_number: int) -> dict[str, Any] | None:
    path = repo_root / ".pipeline" / "issue-watch" / f"{issue_number}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "issue_number": issue_number,
            "error": "invalid_state_json",
            "path": str(path),
        }
    if not isinstance(payload, dict):
        return {
            "issue_number": issue_number,
            "error": "invalid_state_shape",
            "path": str(path),
        }
    comments = payload.get("comments", [])
    last_comment = comments[-1] if isinstance(comments, list) and comments else None
    return {
        "issue_number": issue_number,
        "path": str(path),
        "title": payload.get("title", ""),
        "url": payload.get("url", ""),
        "state": payload.get("state", ""),
        "updated_at": payload.get("updatedAt", ""),
        "comments_count": len(comments) if isinstance(comments, list) else 0,
        "last_comment": last_comment,
    }


def _process_age_seconds(pid: int) -> float | None:
    """Return the process's elapsed running time in seconds, or None if unknown.

    Uses POSIX `ps -o etime=` (portable across Linux and macOS). Parsing
    handles the `[[DD-]HH:]MM:SS` format `ps` emits.
    """
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "etime="],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    etime = result.stdout.strip()
    if not etime:
        return None
    try:
        days = 0
        if "-" in etime:
            days_str, etime = etime.split("-", 1)
            days = int(days_str)
        parts = etime.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = (int(p) for p in parts)
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = (int(p) for p in parts)
        else:
            return None
    except ValueError:
        return None
    return float(days * 86400 + hours * 3600 + minutes * 60 + seconds)


# If a process's age exceeds the pid-file age by more than this many seconds,
# treat the PID as reused (the real owner exited and a new process inherited
# the PID). 60s absorbs normal pid-file write jitter.
_PID_REUSE_SLACK_SECONDS = 60.0


def _inspect_pid_file(pid_path: Path) -> dict[str, Any]:
    """Read a pid file and probe the process. Returns pid, status, uptime, stale flag.

    Detects PID reuse: if the live process started meaningfully before the
    pid file was written, the pid file is treated as stale rather than
    claiming a healthy service.
    """
    pid: int | None = None
    status = "stopped"
    uptime_seconds: float | None = None
    stale_pid_file = False
    pid_file_mtime: float | None = None

    if not pid_path.exists():
        return {
            "pid": None,
            "status": "stopped",
            "uptime_seconds": None,
            "stale_pid_file": False,
            "pid_file_mtime": None,
        }

    try:
        stat_result = pid_path.stat()
        pid_file_mtime = stat_result.st_mtime
    except OSError:
        pid_file_mtime = None

    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pid = None

    if pid is not None:
        try:
            os.kill(pid, 0)  # Signal 0 probes existence without delivering a signal.
        except OSError:
            status = "stale"
            stale_pid_file = True
        else:
            proc_age = _process_age_seconds(pid)
            if proc_age is not None and pid_file_mtime is not None:
                pid_file_age = max(0.0, time.time() - pid_file_mtime)
                if proc_age > pid_file_age + _PID_REUSE_SLACK_SECONDS:
                    # Process existed long before the pid file was written -> reused PID.
                    status = "stale"
                    stale_pid_file = True
                else:
                    status = "running"
                    uptime_seconds = proc_age
            else:
                status = "running"
                if pid_file_mtime is not None:
                    uptime_seconds = max(0.0, time.time() - pid_file_mtime)
    else:
        status = "stale"
        stale_pid_file = True

    return {
        "pid": pid,
        "status": status,
        "uptime_seconds": uptime_seconds,
        "stale_pid_file": stale_pid_file,
        "pid_file_mtime": pid_file_mtime,
    }


def _humanize_service_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def build_runtime_services_status(repo_root: Path) -> dict[str, Any]:
    services: list[dict[str, Any]] = []
    running = 0
    stopped = 0
    stale = 0

    seen_names: set[str] = set()
    for svc in RUNTIME_SERVICES:
        pid_path = repo_root / svc["pid_file"]
        probe = _inspect_pid_file(pid_path)
        seen_names.add(svc["name"])
        if probe["status"] == "running":
            running += 1
        elif probe["status"] == "stale":
            stale += 1
        else:
            stopped += 1
        services.append(
            {
                "name": svc["name"],
                "label": svc["label"],
                "status": probe["status"],
                "pid": probe["pid"],
                "port": svc["port"],
                "pid_file": str(pid_path),
                "uptime_seconds": probe["uptime_seconds"],
                "stale_pid_file": probe["stale_pid_file"],
                "known": True,
            }
        )

    # Auto-discover pid files not covered by the curated list so operators can
    # see workers spawned by scripts that haven't been registered yet.
    pids_dir = repo_root / ".pids"
    if pids_dir.is_dir():
        for pid_path in sorted(pids_dir.glob("*.pid")):
            name = pid_path.stem
            if name in seen_names:
                continue
            probe = _inspect_pid_file(pid_path)
            if probe["status"] == "running":
                running += 1
            elif probe["status"] == "stale":
                stale += 1
            else:
                stopped += 1
            services.append(
                {
                    "name": name,
                    "label": _humanize_service_name(name),
                    "status": probe["status"],
                    "pid": probe["pid"],
                    "port": None,
                    "pid_file": str(pid_path),
                    "uptime_seconds": probe["uptime_seconds"],
                    "stale_pid_file": probe["stale_pid_file"],
                    "known": False,
                }
            )

    return {
        "running": running,
        "stopped": stopped,
        "stale": stale,
        "total": running + stopped + stale,
        "services": services,
    }


def render_dashboard_html(*, issue_number: int = DEFAULT_FEEDBACK_ISSUE) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KubeDojo Local Monitor</title>
  <style>
    :root {{
      --bg: #0a0f1a;
      --surface-0: #111827;
      --surface-1: #1a2332;
      --surface-2: #1f2b3d;
      --text: #e5e7eb;
      --text-secondary: #9ca3af;
      --text-dim: #6b7280;
      --accent: #38bdf8;
      --accent-muted: rgba(56,189,248,0.12);
      --teal: #2dd4bf;
      --teal-muted: rgba(45,212,191,0.12);
      --green: #4ade80;
      --green-muted: rgba(74,222,128,0.12);
      --amber: #fbbf24;
      --amber-muted: rgba(251,191,36,0.10);
      --red: #f87171;
      --red-muted: rgba(248,113,113,0.10);
      --border: rgba(255,255,255,0.06);
      --border-subtle: rgba(255,255,255,0.03);
      --radius: 12px;
      --radius-sm: 8px;
      --radius-xs: 6px;
    }}
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      -webkit-font-smoothing: antialiased;
      line-height: 1.5;
    }}
    .mono {{ font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace; }}

    .header {{
      background: linear-gradient(180deg, rgba(17,24,39,0.95) 0%, rgba(10,15,26,0.98) 100%);
      border-bottom: 1px solid var(--border);
      padding: 20px 0;
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(12px);
    }}
    .header-inner {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .header-left {{ display: flex; align-items: center; gap: 14px; }}
    .logo {{
      width: 32px; height: 32px; border-radius: 8px;
      background: linear-gradient(135deg, var(--accent), var(--teal));
      display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 14px; color: #0a0f1a; flex-shrink: 0;
    }}
    .header-title {{ font-size: 16px; font-weight: 600; letter-spacing: -0.01em; }}
    .header-sub {{ font-size: 12px; color: var(--text-dim); }}
    .header-right {{ display: flex; align-items: center; gap: 12px; }}
    .status-pill {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 5px 12px; border-radius: 20px;
      font-size: 12px; font-weight: 500;
      background: var(--green-muted); color: var(--green);
    }}
    .status-pill .dot {{
      width: 6px; height: 6px; border-radius: 50%;
      background: currentColor; animation: pulse 2s ease-in-out infinite;
    }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
    .refresh-btn {{
      background: var(--surface-1); color: var(--text);
      border: 1px solid var(--border); padding: 6px 14px;
      border-radius: var(--radius-sm); font-size: 13px;
      font-weight: 500; cursor: pointer; transition: all 0.15s;
      display: flex; align-items: center; gap: 6px;
    }}
    .refresh-btn:hover {{ background: var(--surface-2); border-color: rgba(255,255,255,0.12); }}
    .refresh-btn.loading {{ opacity: 0.6; pointer-events: none; }}
    .refresh-btn svg {{ transition: transform 0.3s; }}
    .refresh-btn.loading svg {{ animation: spin 0.8s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .last-updated {{ font-size: 11px; color: var(--text-dim); }}

    .main {{ max-width: 1440px; margin: 0 auto; padding: 24px; }}

    .metrics {{
      display: grid; grid-template-columns: repeat(6, 1fr);
      gap: 12px; margin-bottom: 24px;
    }}
    .metric {{
      background: var(--surface-0); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 16px;
      position: relative; overflow: hidden;
    }}
    .metric::before {{
      content: ''; position: absolute; top: 0; left: 0; right: 0;
      height: 2px; background: var(--border);
    }}
    .metric.good::before {{ background: var(--green); }}
    .metric.warn::before {{ background: var(--amber); }}
    .metric.bad::before {{ background: var(--red); }}
    .metric.accent::before {{ background: var(--accent); }}
    .metric-label {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--text-dim); margin-bottom: 8px;
    }}
    .metric-value {{ font-size: 26px; font-weight: 700; letter-spacing: -0.02em; line-height: 1; }}
    .metric-sub {{ font-size: 11px; color: var(--text-dim); margin-top: 6px; }}

    .progress-track {{
      height: 4px; background: rgba(255,255,255,0.06);
      border-radius: 2px; margin-top: 10px; overflow: hidden;
    }}
    .progress-fill {{ height: 100%; border-radius: 2px; transition: width 0.6s ease; }}
    .progress-fill.green {{ background: var(--green); }}
    .progress-fill.amber {{ background: var(--amber); }}
    .progress-fill.accent {{ background: var(--accent); }}

    .sections {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .section-full {{ grid-column: 1 / -1; }}

    .panel {{
      background: var(--surface-0); border: 1px solid var(--border);
      border-radius: var(--radius); overflow: hidden;
    }}
    .panel-header {{
      padding: 14px 18px; border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between;
    }}
    .panel-title {{
      font-size: 13px; font-weight: 600;
      display: flex; align-items: center; gap: 8px;
    }}
    .panel-icon {{
      width: 18px; height: 18px; border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      font-size: 11px; flex-shrink: 0;
    }}
    .panel-badge {{
      font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600;
    }}
    .panel-body {{ padding: 16px 18px; }}
    .panel-body-flush {{ padding: 0; }}

    .svc-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; }}
    .svc-item {{
      padding: 14px 18px; border-right: 1px solid var(--border);
      display: flex; align-items: center; gap: 12px;
    }}
    .svc-item:last-child {{ border-right: 0; }}
    .svc-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
    .svc-dot.running {{ background: var(--green); box-shadow: 0 0 8px rgba(74,222,128,0.4); }}
    .svc-dot.stopped {{ background: var(--text-dim); }}
    .svc-dot.stale {{ background: var(--red); box-shadow: 0 0 8px rgba(248,113,113,0.45); }}
    .svc-info {{ min-width: 0; flex: 1; }}
    .svc-name {{ font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px; }}
    .svc-detail {{ font-size: 11px; color: var(--text-dim); }}
    .svc-chip {{
      display: inline-block; padding: 1px 6px; border-radius: 4px;
      font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
    }}
    .svc-chip.stale {{ background: var(--red-muted); color: var(--red); }}
    .svc-chip.discovered {{ background: var(--accent-muted); color: var(--accent); }}

    .queue-cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
    .queue-col {{ border-right: 1px solid var(--border); }}
    .queue-col:last-child {{ border-right: 0; }}
    .queue-col-header {{
      padding: 10px 14px; border-bottom: 1px solid var(--border-subtle);
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim);
      display: flex; align-items: center; justify-content: space-between;
    }}
    .queue-count {{
      font-size: 10px; padding: 1px 6px; border-radius: 8px;
      background: rgba(255,255,255,0.06); color: var(--text-secondary);
    }}
    .queue-list {{ margin: 0; padding: 0; list-style: none; max-height: 180px; overflow-y: auto; }}
    .queue-list::-webkit-scrollbar {{ width: 4px; }}
    .queue-list::-webkit-scrollbar-track {{ background: transparent; }}
    .queue-list::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.08); border-radius: 2px; }}
    .queue-item {{
      padding: 6px 14px; font-size: 12px; border-bottom: 1px solid var(--border-subtle);
      color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .queue-item:last-child {{ border-bottom: 0; }}
    .queue-empty {{ padding: 20px 14px; text-align: center; font-size: 12px; color: var(--text-dim); }}

    .wt-summary {{
      display: flex; gap: 16px; padding: 12px 18px;
      border-bottom: 1px solid var(--border); flex-wrap: wrap;
    }}
    .wt-stat {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-secondary); }}
    .wt-stat-val {{ font-weight: 600; color: var(--text); }}
    .wt-table {{ width: 100%; border-collapse: collapse; }}
    .wt-table th {{
      text-align: left; padding: 8px 14px; font-size: 11px;
      font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
      color: var(--text-dim); border-bottom: 1px solid var(--border);
      background: rgba(0,0,0,0.15);
    }}
    .wt-table td {{ padding: 5px 14px; font-size: 12px; border-bottom: 1px solid var(--border-subtle); }}
    .wt-table tr:last-child td {{ border-bottom: 0; }}
    .wt-path {{ color: var(--text-secondary); }}
    .wt-badge {{
      display: inline-block; padding: 1px 6px; border-radius: 4px;
      font-size: 10px; font-weight: 600; text-transform: uppercase;
    }}
    .wt-badge.M {{ background: var(--amber-muted); color: var(--amber); }}
    .wt-badge.A {{ background: var(--green-muted); color: var(--green); }}
    .wt-badge.D {{ background: var(--red-muted); color: var(--red); }}
    .wt-badge.U {{ background: var(--red-muted); color: var(--red); }}
    .wt-badge.Q {{ background: var(--accent-muted); color: var(--accent); }}
    .wt-cat {{
      font-size: 10px; padding: 1px 6px; border-radius: 4px;
      background: rgba(255,255,255,0.04); color: var(--text-dim);
    }}
    .wt-scroll {{ max-height: 260px; overflow-y: auto; }}
    .wt-scroll::-webkit-scrollbar {{ width: 4px; }}
    .wt-scroll::-webkit-scrollbar-track {{ background: transparent; }}
    .wt-scroll::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.08); border-radius: 2px; }}

    .tracks-table {{ width: 100%; border-collapse: collapse; }}
    .tracks-table th {{
      text-align: left; padding: 10px 18px; font-size: 11px;
      font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
      color: var(--text-dim); border-bottom: 1px solid var(--border);
      background: rgba(0,0,0,0.15);
    }}
    .tracks-table th.num {{ text-align: right; }}
    .tracks-table td {{
      padding: 10px 18px; font-size: 13px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .tracks-table tr:last-child td {{ border-bottom: 0; }}
    .tracks-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
    .tracks-table td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .tracks-table td.name {{ font-weight: 600; }}
    .tracks-table .dim {{ color: var(--text-dim); }}
    .tracks-table .warn {{ color: var(--amber); font-weight: 600; }}
    .tracks-table .bad {{ color: var(--red); font-weight: 600; }}
    .tracks-table .good {{ color: var(--green); }}
    .tracks-table .zero {{ color: var(--text-dim); }}

    .queue-summary {{
      padding: 14px 18px; border-bottom: 1px solid var(--border);
      display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
      gap: 0; text-align: center;
    }}
    .queue-stat {{ border-right: 1px solid var(--border-subtle); padding: 2px 8px; }}
    .queue-stat:last-child {{ border-right: 0; }}
    .queue-stat-val {{ font-size: 20px; font-weight: 700; letter-spacing: -0.01em; line-height: 1; }}
    .queue-stat-label {{
      font-size: 10px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-top: 6px;
    }}
    .queue-per-track {{ padding: 0; }}
    .qpt-row {{
      display: grid; grid-template-columns: 1fr auto;
      padding: 8px 18px; border-bottom: 1px solid var(--border-subtle);
      font-size: 12px; align-items: center; gap: 12px;
    }}
    .qpt-row:last-child {{ border-bottom: 0; }}
    .qpt-name {{ color: var(--text-secondary); }}
    .qpt-status {{ font-size: 11px; color: var(--text-dim); text-align: right; }}
    .qpt-status .pill {{
      display: inline-block; padding: 1px 7px; border-radius: 10px;
      font-size: 10px; font-weight: 600; margin-left: 4px;
    }}
    .qpt-status .pill.w {{ background: var(--accent-muted); color: var(--accent); }}
    .qpt-status .pill.r {{ background: var(--amber-muted); color: var(--amber); }}
    .qpt-status .pill.p {{ background: var(--teal-muted); color: var(--teal); }}
    .qpt-status .pill.d {{ background: var(--red-muted); color: var(--red); }}
    .qpt-status.idle {{ color: var(--green); }}
    .qpt-top {{
      padding: 12px 18px; border-top: 1px solid var(--border);
      background: rgba(0,0,0,0.12);
    }}
    .qpt-top-title {{
      font-size: 10px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-bottom: 8px;
    }}
    .qpt-top-list {{ margin: 0; padding: 0; list-style: none; }}
    .qpt-top-list li {{
      padding: 3px 0; font-size: 12px; color: var(--text-secondary);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .qpt-top-kind {{
      display: inline-block; width: 14px; font-weight: 700;
      font-size: 10px; text-transform: uppercase;
    }}
    .qpt-top-kind.w {{ color: var(--accent); }}
    .qpt-top-kind.r {{ color: var(--amber); }}
    .qpt-top-kind.p {{ color: var(--teal); }}
    .qpt-top-kind.d {{ color: var(--red); }}

    .ztt-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
    .ztt-section {{ padding: 14px 18px; border-right: 1px solid var(--border); }}
    .ztt-section:last-child {{ border-right: 0; }}
    .ztt-section-title {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-bottom: 10px;
    }}
    .ztt-row {{ display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; }}
    .ztt-check {{
      width: 16px; height: 16px; border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      font-size: 10px; flex-shrink: 0;
    }}
    .ztt-check.pass {{ background: var(--green-muted); color: var(--green); }}
    .ztt-check.fail {{ background: var(--red-muted); color: var(--red); }}
    .ztt-label {{ color: var(--text-secondary); }}
    .ztt-val {{ margin-left: auto; font-weight: 600; font-size: 11px; }}

    .missing-group {{ margin-bottom: 12px; }}
    .missing-group:last-child {{ margin-bottom: 0; }}
    .missing-group-title {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.04em; color: var(--text-dim); margin-bottom: 8px;
      display: flex; align-items: center; gap: 8px;
    }}
    .missing-list {{ margin: 0; padding: 0; list-style: none; }}
    .missing-item {{
      padding: 5px 10px; font-size: 12px; color: var(--text-secondary);
      border-radius: var(--radius-xs); margin-bottom: 2px;
    }}
    .missing-item:hover {{ background: rgba(255,255,255,0.03); }}

    .fb-header {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px; }}
    .fb-icon {{
      width: 32px; height: 32px; border-radius: 50%;
      background: var(--accent-muted); color: var(--accent);
      display: flex; align-items: center; justify-content: center;
      font-size: 14px; flex-shrink: 0;
    }}
    .fb-title {{ font-size: 14px; font-weight: 600; }}
    .fb-meta {{
      font-size: 12px; color: var(--text-dim);
      display: flex; gap: 12px; margin-top: 2px; flex-wrap: wrap;
    }}
    .fb-meta span {{ display: flex; align-items: center; gap: 4px; }}
    .fb-comment {{
      background: var(--surface-1); border: 1px solid var(--border);
      border-radius: var(--radius-sm); padding: 12px; margin-top: 12px;
    }}
    .fb-comment-header {{ font-size: 11px; color: var(--text-dim); margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }}
    .fb-comment-body {{
      font-size: 12px; color: var(--text-secondary); line-height: 1.5;
      max-height: 120px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;
    }}

    .clr-green {{ color: var(--green); }}
    .clr-amber {{ color: var(--amber); }}
    .clr-red {{ color: var(--red); }}
    .clr-accent {{ color: var(--accent); }}
    .empty-state {{ padding: 24px; text-align: center; color: var(--text-dim); font-size: 13px; }}
    .skeleton {{
      background: linear-gradient(90deg, var(--surface-1) 25%, var(--surface-2) 50%, var(--surface-1) 75%);
      background-size: 200% 100%; animation: shimmer 1.5s infinite;
      border-radius: var(--radius-xs); height: 16px;
    }}
    @keyframes shimmer {{ 0% {{ background-position: -200% 0; }} 100% {{ background-position: 200% 0; }} }}

    @media (max-width: 1200px) {{ .metrics {{ grid-template-columns: repeat(3, 1fr); }} }}
    @media (max-width: 960px) {{
      .sections {{ grid-template-columns: 1fr; }}
      .metrics {{ grid-template-columns: repeat(2, 1fr); }}
      .svc-grid {{ grid-template-columns: 1fr; }}
      .svc-item {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .svc-item:last-child {{ border-bottom: 0; }}
      .queue-cols, .ztt-grid {{ grid-template-columns: 1fr; }}
      .queue-col {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .queue-col:last-child {{ border-bottom: 0; }}
      .ztt-section {{ border-right: 0; border-bottom: 1px solid var(--border); }}
      .ztt-section:last-child {{ border-bottom: 0; }}
    }}
    @media (max-width: 640px) {{
      .metrics {{ grid-template-columns: 1fr; }}
      .main {{ padding: 16px; }}
      .header-inner {{ padding: 0 16px; flex-wrap: wrap; }}
    }}
  </style>
</head>
<body>
  <header class="header">
    <div class="header-inner">
      <div class="header-left">
        <div class="logo">K</div>
        <div>
          <div class="header-title">KubeDojo Local Monitor</div>
          <div class="header-sub">Read-only operations console &middot; port 8768</div>
        </div>
      </div>
      <div class="header-right">
        <span class="status-pill" id="conn-status"><span class="dot"></span> Connected</span>
        <span class="last-updated" id="last-updated"></span>
        <button class="refresh-btn" id="refresh">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
      </div>
    </div>
  </header>

  <div class="main">
    <div class="metrics" id="metrics">
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:60%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:80%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:70%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:50%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:65%"></div></div>
      <div class="metric"><div class="metric-label">Loading</div><div class="skeleton" style="width:75%"></div></div>
    </div>

    <div class="sections">
      <div class="section-full">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-icon" style="background:var(--accent-muted);color:var(--accent);">#</span>
              Site by Track
            </div>
            <span class="panel-badge" id="tracks-badge" style="background:var(--accent-muted);color:var(--accent);"></span>
          </div>
          <div class="panel-body-flush">
            <table class="tracks-table">
              <thead>
                <tr>
                  <th>Track</th>
                  <th class="num">Modules</th>
                  <th class="num">V2 write</th>
                  <th class="num">V2 review</th>
                  <th class="num">V2 patch</th>
                  <th class="num">V2 dead</th>
                  <th class="num">T2 pend</th>
                </tr>
              </thead>
              <tbody id="tracks-body"></tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="section-full">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-icon" style="background:var(--green-muted);color:var(--green);">S</span>
              Runtime Services
            </div>
            <span class="panel-badge" id="svc-badge" style="background:var(--green-muted);color:var(--green);"></span>
          </div>
          <div class="panel-body-flush">
            <div class="svc-grid" id="services"></div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--accent-muted);color:var(--accent);">P</span>
            V2 Pipeline
          </div>
          <span class="panel-badge" id="v2-badge"></span>
        </div>
        <div class="panel-body-flush" id="v2-body"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--teal-muted);color:var(--teal);">T</span>
            Translation V2
          </div>
          <span class="panel-badge" id="trans-badge"></span>
        </div>
        <div class="panel-body-flush" id="trans-body"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--amber-muted);color:var(--amber);">G</span>
            Git Worktree
          </div>
          <span class="panel-badge" id="wt-badge"></span>
        </div>
        <div class="panel-body-flush" id="worktree"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--amber-muted);color:var(--amber);">M</span>
            Missing Modules
          </div>
          <span class="panel-badge" id="missing-badge"></span>
        </div>
        <div class="panel-body" id="missing"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="panel-icon" style="background:var(--accent-muted);color:var(--accent);">F</span>
            Feedback Issue #{issue_number}
          </div>
        </div>
        <div class="panel-body" id="feedback"></div>
      </div>
    </div>
  </div>

  <script>
    const ISSUE = {issue_number};
    const $ = (sel) => document.querySelector(sel);

    async function fetchJson(url) {{
      const r = await fetch(url);
      if (!r.ok) return {{ error: `HTTP ${{r.status}}`, url }};
      return r.json();
    }}

    function esc(s) {{
      const d = document.createElement('div');
      d.textContent = String(s ?? '');
      return d.innerHTML;
    }}

    function progressBar(pct, color) {{
      const p = Math.max(0, Math.min(100, pct || 0));
      return `<div class="progress-track"><div class="progress-fill ${{color}}" style="width:${{p}}%"></div></div>`;
    }}

    function renderMetrics(summary, worktree, feedback, t2FullQueue) {{
      const v2 = summary.v2_pipeline || {{}};
      const t2 = t2FullQueue || summary.translation_v2_pipeline?.queue || {{}};
      const missing = summary.missing_modules || {{}};
      const svc = summary.runtime_services || {{}};
      const v2rate = v2.convergence_rate ?? 0;
      const t2rate = t2.convergence_rate ?? 0;
      const activeMissing = missing.active_exact?.missing ?? 0;

      const cards = [
        {{
          label: 'English Modules',
          value: summary.english_modules ?? 0,
          cls: 'accent',
          sub: `${{summary.tracks?.length ?? 0}} tracks`,
        }},
        {{
          label: 'V2 Convergence',
          value: `${{v2rate.toFixed(1)}}%`,
          cls: v2rate >= 90 ? 'good' : v2rate >= 50 ? 'warn' : 'bad',
          sub: `${{v2.total_modules ?? 0}} modules tracked`,
          bar: {{ pct: v2rate, color: v2rate >= 90 ? 'green' : 'amber' }},
        }},
        {{
          label: 'Translation V2',
          value: `${{t2rate.toFixed(1)}}%`,
          cls: t2rate >= 90 ? 'good' : t2rate >= 50 ? 'warn' : 'bad',
          sub: `${{t2.total_modules ?? 0}} modules tracked`,
          bar: {{ pct: t2rate, color: t2rate >= 90 ? 'green' : 'amber' }},
        }},
        {{
          label: 'Active Missing',
          value: activeMissing,
          cls: activeMissing === 0 ? 'good' : 'warn',
          sub: `${{missing.deferred?.missing_min ?? 0}}&ndash;${{missing.deferred?.missing_max ?? 0}} deferred`,
        }},
        (() => {{
          const run = svc.running ?? 0;
          const stop = svc.stopped ?? 0;
          const st = svc.stale ?? 0;
          const total = svc.total ?? (run + stop + st);
          const bits = [];
          if (stop) bits.push(`${{stop}} stopped`);
          if (st) bits.push(`${{st}} stale`);
          return {{
            label: 'Services',
            value: `${{run}}/${{total}}`,
            cls: st ? 'bad' : (stop ? 'warn' : 'good'),
            sub: bits.length ? bits.join(' · ') : 'All running',
          }};
        }})(),
        {{
          label: 'Worktree',
          value: worktree.dirty ? `${{worktree.counts?.total ?? 0}} files` : 'Clean',
          cls: worktree.dirty ? 'warn' : 'good',
          sub: worktree.branch ? `${{esc(worktree.branch)}}${{worktree.ahead ? ` +${{worktree.ahead}}` : ''}}` : '',
        }},
      ];

      $('#metrics').innerHTML = cards.map(c => `
        <div class="metric ${{c.cls}}">
          <div class="metric-label">${{c.label}}</div>
          <div class="metric-value">${{c.value}}</div>
          ${{c.sub ? `<div class="metric-sub">${{c.sub}}</div>` : ''}}
          ${{c.bar ? progressBar(c.bar.pct, c.bar.color) : ''}}
        </div>
      `).join('');
    }}

    function formatUptime(seconds) {{
      if (seconds == null || !isFinite(seconds) || seconds < 0) return '';
      const s = Math.floor(seconds);
      if (s < 60) return `${{s}}s`;
      const m = Math.floor(s / 60);
      if (m < 60) return `${{m}}m`;
      const h = Math.floor(m / 60);
      if (h < 48) return `${{h}}h ${{m % 60}}m`;
      const d = Math.floor(h / 24);
      return `${{d}}d ${{h % 24}}h`;
    }}

    function renderServices(data) {{
      if (!data.services || data.services.length === 0) {{
        $('#services').innerHTML = '<div class="empty-state">No services configured</div>';
        return;
      }}
      const total = data.total ?? (data.running + data.stopped + (data.stale || 0));
      const badge = $('#svc-badge');
      const badgeBits = [`${{data.running}} / ${{total}} running`];
      if (data.stale) badgeBits.push(`${{data.stale}} stale`);
      badge.textContent = badgeBits.join(' · ');
      if (data.stale) {{
        badge.style.background = 'var(--red-muted)';
        badge.style.color = 'var(--red)';
      }} else if (data.stopped === 0) {{
        badge.style.background = 'var(--green-muted)';
        badge.style.color = 'var(--green)';
      }} else {{
        badge.style.background = 'var(--amber-muted)';
        badge.style.color = 'var(--amber)';
      }}

      $('#services').innerHTML = data.services.map(s => {{
        const chips = [];
        if (s.status === 'stale') chips.push('<span class="svc-chip stale">Stale PID</span>');
        if (s.known === false) chips.push('<span class="svc-chip discovered">Discovered</span>');
        let detail;
        if (s.status === 'running') {{
          const up = formatUptime(s.uptime_seconds);
          detail = `PID ${{s.pid}}${{up ? ` &middot; up ${{up}}` : ''}}`;
        }} else if (s.status === 'stale') {{
          detail = s.pid != null ? `PID ${{s.pid}} not responding` : 'Unreadable PID file';
        }} else {{
          detail = 'Stopped';
        }}
        if (s.port) detail += ` &middot; :${{s.port}}`;
        return `
        <div class="svc-item">
          <span class="svc-dot ${{s.status}}"></span>
          <div class="svc-info">
            <div class="svc-name">${{esc(s.label)}}${{chips.join('')}}</div>
            <div class="svc-detail mono">${{detail}}</div>
          </div>
        </div>`;
      }}).join('');
    }}

    const TRACK_LABEL = {{
      'prerequisites': 'Prerequisites',
      'linux': 'Linux',
      'k8s': 'Kubernetes',
      'cloud': 'Cloud',
      'platform': 'Platform Engineering',
      'on-premises': 'On-Premises',
      'ai-ml-engineering': 'AI/ML Engineering',
      'other': 'Other',
    }};

    function shortenKey(key) {{
      return String(key || '').replace(/^src\\/content\\/docs\\//, '').replace(/\\.md$/, '');
    }}

    function renderSiteTracks(summary, v2, t2Queue) {{
      const tracks = summary.tracks || [];
      const v2ByTrack = new Map(((v2 || {{}}).per_track || []).map(t => [t.slug, t.counts]));
      const t2ByTrack = new Map(((t2Queue || {{}}).per_track || []).map(t => [t.slug, t.counts]));

      const total = tracks.reduce((sum, t) => sum + (t.module_count || 0), 0);
      const active = tracks.filter(t => t.module_count > 0).length;
      $('#tracks-badge').textContent = `${{total}} modules · ${{active}} tracks`;

      const cls = (n) => n > 0 ? '' : 'zero';
      const rowFor = (t) => {{
        const v = v2ByTrack.get(t.slug) || {{}};
        const tr2 = t2ByTrack.get(t.slug) || {{}};
        const t2Pend = (tr2.pending_write || 0) + (tr2.pending_review || 0);
        const deadCls = (v.dead_letter || 0) > 0 ? 'bad' : 'zero';
        const reviewCls = (v.pending_review || 0) > 0 ? 'warn' : 'zero';
        return `<tr>
          <td class="name">${{esc(t.label)}}</td>
          <td class="num">${{t.module_count}}</td>
          <td class="num ${{cls(v.pending_write || 0)}}">${{v.pending_write || 0}}</td>
          <td class="num ${{reviewCls}}">${{v.pending_review || 0}}</td>
          <td class="num ${{cls(v.pending_patch || 0)}}">${{v.pending_patch || 0}}</td>
          <td class="num ${{deadCls}}">${{v.dead_letter || 0}}</td>
          <td class="num ${{cls(t2Pend)}}">${{t2Pend}}</td>
        </tr>`;
      }};

      $('#tracks-body').innerHTML = tracks.map(rowFor).join('');
    }}

    function renderPipelinePanel(bodyId, badgeId, data, label) {{
      const el = $(bodyId);
      const badge = $(badgeId);
      if (!data || data.error) {{
        badge.textContent = 'Unknown';
        badge.style.background = 'var(--amber-muted)';
        badge.style.color = 'var(--amber)';
        el.innerHTML = `<div class="empty-state">${{data?.error ? esc(data.error) : 'No data'}}</div>`;
        return;
      }}
      const counts = data.counts || {{}};
      const totalPending = (counts.pending_write || 0) + (counts.pending_review || 0) + (counts.pending_patch || 0);
      const dead = counts.dead_letter || 0;
      if (totalPending === 0 && dead === 0) {{
        badge.textContent = 'Idle';
        badge.style.background = 'var(--green-muted)';
        badge.style.color = 'var(--green)';
      }} else {{
        const parts = [];
        if (totalPending) parts.push(`${{totalPending}} pending`);
        if (dead) parts.push(`${{dead}} dead`);
        badge.textContent = parts.join(' · ');
        badge.style.background = dead ? 'var(--red-muted)' : 'var(--amber-muted)';
        badge.style.color = dead ? 'var(--red)' : 'var(--amber)';
      }}

      const done = counts.done ?? 0;
      const tracked = done + totalPending + dead + (counts.in_progress ?? 0);
      const conv = tracked > 0 ? (done / tracked * 100) : (data.convergence_rate ?? 0);
      let html = `
        <div class="queue-summary">
          <div class="queue-stat"><div class="queue-stat-val">${{done}}</div><div class="queue-stat-label">Done</div></div>
          <div class="queue-stat"><div class="queue-stat-val">${{totalPending}}</div><div class="queue-stat-label">Pending</div></div>
          <div class="queue-stat"><div class="queue-stat-val">${{dead}}</div><div class="queue-stat-label">Dead</div></div>
          <div class="queue-stat"><div class="queue-stat-val">${{conv.toFixed(1)}}%</div><div class="queue-stat-label">Converged</div></div>
        </div>`;

      const perTrack = data.per_track || [];
      const active = perTrack.filter(t => {{
        const c = t.counts || {{}};
        return (c.pending_write || 0) + (c.pending_review || 0) + (c.pending_patch || 0) + (c.dead_letter || 0) > 0;
      }});
      html += '<div class="queue-per-track">';
      if (active.length === 0) {{
        html += `<div class="empty-state">All tracks idle</div>`;
      }} else {{
        for (const t of active) {{
          const c = t.counts || {{}};
          const bits = [];
          if (c.pending_write) bits.push(`<span class="pill w">${{c.pending_write}}W</span>`);
          if (c.pending_review) bits.push(`<span class="pill r">${{c.pending_review}}R</span>`);
          if (c.pending_patch) bits.push(`<span class="pill p">${{c.pending_patch}}P</span>`);
          if (c.dead_letter) bits.push(`<span class="pill d">${{c.dead_letter}}D</span>`);
          html += `<div class="qpt-row">
            <span class="qpt-name">${{esc(TRACK_LABEL[t.slug] || t.slug)}}</span>
            <span class="qpt-status">${{bits.join(' ')}}</span>
          </div>`;
        }}
      }}
      html += '</div>';

      const topItems = [];
      for (const t of perTrack) {{
        if (!t.modules) continue;
        for (const kind of ['dead_letter', 'pending_review', 'pending_write', 'pending_patch']) {{
          for (const m of (t.modules[kind] || [])) {{
            topItems.push({{kind, path: m}});
          }}
        }}
      }}
      const kindLabel = {{dead_letter: 'D', pending_review: 'R', pending_write: 'W', pending_patch: 'P'}};
      if (topItems.length > 0) {{
        const shown = topItems.slice(0, 6);
        html += `<div class="qpt-top">
          <div class="qpt-top-title">Top items (${{shown.length}} of ${{topItems.length}})</div>
          <ul class="qpt-top-list mono">
            ${{shown.map(i => `<li><span class="qpt-top-kind ${{kindLabel[i.kind].toLowerCase()}}">${{kindLabel[i.kind]}}</span> ${{esc(shortenKey(i.path))}}</li>`).join('')}}
          </ul>
        </div>`;
      }}

      el.innerHTML = html;
    }}

    function renderWorktree(data) {{
      const el = $('#worktree');
      if (data.error) {{
        el.innerHTML = `<div class="empty-state clr-red">${{esc(data.error)}}</div>`;
        return;
      }}

      const badge = $('#wt-badge');
      if (!data.dirty) {{
        badge.textContent = 'Clean';
        badge.style.background = 'var(--green-muted)';
        badge.style.color = 'var(--green)';
        el.innerHTML = `
          <div class="wt-summary">
            <div class="wt-stat">Branch: <span class="wt-stat-val">${{esc(data.branch)}}</span></div>
          </div>
          <div class="empty-state">Working tree is clean</div>`;
        return;
      }}

      badge.textContent = `${{data.counts.total}} changes`;
      badge.style.background = 'var(--amber-muted)';
      badge.style.color = 'var(--amber)';

      const c = data.counts;
      let summary = `
        <div class="wt-summary">
          <div class="wt-stat">Branch: <span class="wt-stat-val">${{esc(data.branch)}}</span></div>
          ${{data.ahead ? `<div class="wt-stat">Ahead: <span class="wt-stat-val clr-green">+${{data.ahead}}</span></div>` : ''}}
          ${{data.behind ? `<div class="wt-stat">Behind: <span class="wt-stat-val clr-red">-${{data.behind}}</span></div>` : ''}}
          ${{c.staged ? `<div class="wt-stat">Staged: <span class="wt-stat-val clr-green">${{c.staged}}</span></div>` : ''}}
          ${{c.unstaged ? `<div class="wt-stat">Unstaged: <span class="wt-stat-val clr-amber">${{c.unstaged}}</span></div>` : ''}}
          ${{c.untracked ? `<div class="wt-stat">Untracked: <span class="wt-stat-val clr-accent">${{c.untracked}}</span></div>` : ''}}
        </div>`;

      const statusLabel = (entry) => {{
        if (entry.untracked) return ['?', 'Q'];
        if (entry.conflicted) return ['U', 'U'];
        const s = entry.index_status !== ' ' && entry.index_status !== '?' ? entry.index_status : entry.worktree_status;
        return [s, s];
      }};

      const entries = (data.entries || []).slice(0, 80);
      let rows = entries.map(e => {{
        const [label, cls] = statusLabel(e);
        return `<tr>
          <td><span class="wt-badge ${{cls}}">${{label}}</span></td>
          <td class="wt-path mono">${{esc(e.path)}}</td>
          <td><span class="wt-cat">${{e.category}}</span></td>
        </tr>`;
      }}).join('');

      el.innerHTML = `${{summary}}
        <div class="wt-scroll">
          <table class="wt-table">
            <thead><tr><th>Status</th><th>Path</th><th>Category</th></tr></thead>
            <tbody>${{rows}}</tbody>
          </table>
        </div>
        ${{data.entries.length > 80 ? `<div class="empty-state">Showing 80 of ${{data.entries.length}} entries</div>` : ''}}`;
    }}

    function renderZtt(data) {{
      const el = $('#ztt');
      const badge = $('#ztt-badge');

      if (data.error) {{
        el.innerHTML = `<div class="empty-state clr-red">${{esc(data.error)}}</div>`;
        return;
      }}

      const ready = data.ready || {{}};
      const allReady = ready.english_production_bar && ready.ukrainian_sync_clean;
      badge.textContent = allReady ? 'Ready' : 'Needs Work';
      badge.style.background = allReady ? 'var(--green-muted)' : 'var(--amber-muted)';
      badge.style.color = allReady ? 'var(--green)' : 'var(--amber)';

      const chk = (val) => val
        ? '<span class="ztt-check pass">&#10003;</span>'
        : '<span class="ztt-check fail">&#10007;</span>';

      const theory = data.theory || {{}};
      const labs = data.labs || {{}};
      const uk = data.ukrainian || {{}};

      el.innerHTML = `
        <div class="ztt-grid">
          <div class="ztt-section">
            <div class="ztt-section-title">Readiness</div>
            <div class="ztt-row">${{chk(ready.english_production_bar)}}<span class="ztt-label">English Production</span></div>
            <div class="ztt-row">${{chk(ready.ukrainian_sync_clean)}}<span class="ztt-label">Ukrainian Sync</span></div>
            <div class="ztt-section-title" style="margin-top:14px">Theory</div>
            <div class="ztt-row">${{chk(theory.all_have_frontmatter)}}<span class="ztt-label">Frontmatter</span><span class="ztt-val">${{theory.module_count ?? 0}} modules</span></div>
            <div class="ztt-row">${{chk(theory.all_have_labs)}}<span class="ztt-label">Labs Linked</span></div>
            <div class="ztt-row">${{chk(theory.meets_line_threshold)}}<span class="ztt-label">Line Threshold</span></div>
          </div>
          <div class="ztt-section">
            <div class="ztt-section-title">Labs</div>
            <div class="ztt-row">${{chk(labs.all_exist)}}<span class="ztt-label">All Exist</span><span class="ztt-val">${{labs.total ?? 0}} labs</span></div>
            <div class="ztt-row">${{chk(labs.all_executable)}}<span class="ztt-label">Executable</span></div>
            <div class="ztt-row">${{chk(labs.all_have_solutions)}}<span class="ztt-label">Solutions</span></div>
            <div class="ztt-section-title" style="margin-top:14px">Ukrainian</div>
            <div class="ztt-row">${{chk(uk.all_synced)}}<span class="ztt-label">All Synced</span><span class="ztt-val">${{uk.synced ?? 0}}/${{uk.total ?? 0}}</span></div>
            <div class="ztt-row">${{chk(uk.no_stale)}}<span class="ztt-label">No Stale</span></div>
          </div>
        </div>`;
    }}

    function renderMissing(data) {{
      const el = $('#missing');
      const badge = $('#missing-badge');

      if (data.error) {{
        el.innerHTML = `<div class="empty-state clr-red">${{esc(data.error)}}</div>`;
        return;
      }}

      const active = data.active_exact || {{}};
      const deferred = data.deferred || {{}};
      const activeList = active.modules ?? [];
      const deferredList = deferred.modules ?? [];
      const total = activeList.length + deferredList.length;

      badge.textContent = total === 0 ? 'Complete' : `${{total}} missing`;
      badge.style.background = total === 0 ? 'var(--green-muted)' : 'var(--amber-muted)';
      badge.style.color = total === 0 ? 'var(--green)' : 'var(--amber)';

      if (total === 0) {{
        el.innerHTML = '<div class="empty-state">All modules present</div>';
        return;
      }}

      let html = '';
      if (activeList.length) {{
        html += `<div class="missing-group">
          <div class="missing-group-title"><span class="wt-badge M">Active</span> ${{activeList.length}} missing</div>
          <ul class="missing-list">${{activeList.map(m => `<li class="missing-item mono">${{esc(m)}}</li>`).join('')}}</ul>
        </div>`;
      }}
      if (deferredList.length) {{
        html += `<div class="missing-group">
          <div class="missing-group-title"><span class="wt-badge Q">Deferred</span> ${{deferredList.length}} estimated</div>
          <ul class="missing-list">${{deferredList.slice(0, 20).map(m => `<li class="missing-item mono">${{esc(m)}}</li>`).join('')}}</ul>
          ${{deferredList.length > 20 ? `<div class="empty-state">+${{deferredList.length - 20}} more</div>` : ''}}
        </div>`;
      }}
      el.innerHTML = html;
    }}

    function renderFeedback(data) {{
      const el = $('#feedback');
      if (data.error) {{
        el.innerHTML = `<div class="empty-state">${{data.error === 'missing_issue_watch_state' ? 'Issue watcher not running or no data yet' : esc(data.error)}}</div>`;
        return;
      }}

      let html = `
        <div class="fb-header">
          <div class="fb-icon">#</div>
          <div>
            <div class="fb-title">${{esc(data.title || `Issue #${{data.issue_number}}`)}}</div>
            <div class="fb-meta">
              <span><span class="wt-badge ${{data.state === 'open' ? 'A' : 'D'}}">${{data.state || 'unknown'}}</span></span>
              <span>${{data.comments_count ?? 0}} comments</span>
              ${{data.updated_at ? `<span>Updated ${{esc(data.updated_at)}}</span>` : ''}}
            </div>
          </div>
        </div>`;

      if (data.last_comment) {{
        const c = data.last_comment;
        const body = typeof c === 'object' ? (c.body || JSON.stringify(c, null, 2)) : String(c);
        const author = typeof c === 'object' ? (c.author || c.user || '') : '';
        html += `
          <div class="fb-comment">
            <div class="fb-comment-header">
              ${{author ? `<strong>${{esc(author)}}</strong> &middot; ` : ''}}Latest comment
            </div>
            <div class="fb-comment-body mono">${{esc(body.substring(0, 800))}}</div>
          </div>`;
      }}
      el.innerHTML = html;
    }}

    let refreshing = false;
    async function refresh() {{
      if (refreshing) return;
      refreshing = true;
      const btn = $('#refresh');
      btn.classList.add('loading');

      try {{
        const [summary, missing, services, worktree, feedback, v2Status, transStatus] = await Promise.all([
          fetchJson('/api/status/summary'),
          fetchJson('/api/missing-modules/status'),
          fetchJson('/api/runtime/services'),
          fetchJson('/api/git/worktree'),
          fetchJson(`/api/issue-watch/${{ISSUE}}`),
          fetchJson('/api/pipeline/v2/status'),
          fetchJson('/api/translation/v2/status'),
        ]);

        summary.missing_modules = missing;
        summary.runtime_services = services;

        const t2Queue = transStatus.queue || transStatus;
        renderMetrics(summary, worktree, feedback, t2Queue);
        renderServices(services);
        renderSiteTracks(summary, v2Status, t2Queue);
        renderPipelinePanel('#v2-body', '#v2-badge', v2Status, 'V2 Pipeline');
        renderPipelinePanel('#trans-body', '#trans-badge', t2Queue, 'Translation V2');
        renderWorktree(worktree);
        renderMissing(missing);
        renderFeedback(feedback);

        const now = new Date();
        $('#last-updated').textContent = `Updated ${{now.toLocaleTimeString()}}`;
        const pill = $('#conn-status');
        pill.innerHTML = '<span class="dot"></span> Connected';
        pill.style.background = 'var(--green-muted)';
        pill.style.color = 'var(--green)';
      }} catch (err) {{
        const pill = $('#conn-status');
        pill.innerHTML = '<span class="dot"></span> Error';
        pill.style.background = 'var(--red-muted)';
        pill.style.color = 'var(--red)';
        console.error('Dashboard refresh failed:', err);
      }} finally {{
        refreshing = false;
        btn.classList.remove('loading');
      }}
    }}

    $('#refresh').addEventListener('click', refresh);
    refresh();
    setInterval(refresh, 60000);
  </script>
</body>
</html>"""


# ============================================================
# Agent orientation: /api/briefing/session + /api/schema
# ============================================================


# Keyed by resolved path so different repos' STATUS.md files never alias.
_STATUS_MD_CACHE: dict[str, dict[str, Any]] = {}
_STATUS_MD_CACHE_LOCK = threading.Lock()


def _parse_status_md(status_path: Path) -> dict[str, Any]:
    """Extract focus + blockers + a light summary from STATUS.md.

    Caches by absolute path + mtime to keep briefing cheap and to stay
    safe when multiple repos share one Python process.
    """
    try:
        mtime = status_path.stat().st_mtime
    except OSError:
        return {"focus": [], "blockers": [], "exists": False}

    cache_key = str(status_path.resolve())
    with _STATUS_MD_CACHE_LOCK:
        entry = _STATUS_MD_CACHE.get(cache_key)
        if entry is not None and entry["mtime"] == mtime:
            return entry["data"]

    try:
        text = status_path.read_text(encoding="utf-8")
    except OSError:
        return {"focus": [], "blockers": [], "exists": False}

    focus: list[str] = []
    blockers: list[str] = []
    section = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            if heading.startswith("todo"):
                section = "todo"
            elif heading.startswith("blocker"):
                section = "blocker"
            else:
                section = None
            continue
        if section == "todo":
            # Only collect unchecked items: - [ ] ...
            if line.lstrip().startswith("- [ ]"):
                bullet = line.lstrip()[5:].strip()
                if bullet and len(focus) < 10:
                    focus.append(bullet)
        elif section == "blocker":
            if line.lstrip().startswith("- "):
                bullet = line.lstrip()[2:].strip()
                if bullet and len(blockers) < 10:
                    blockers.append(bullet)

    data = {"focus": focus, "blockers": blockers, "exists": True}
    with _STATUS_MD_CACHE_LOCK:
        _STATUS_MD_CACHE[cache_key] = {"mtime": mtime, "data": data}
    return data


def _recent_commits(repo_root: Path, limit: int = 5) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["git", "log", f"-n{limit}", "--pretty=format:%h%x09%s"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if result.returncode != 0:
        return []
    commits: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        if "\t" in line:
            sha, subject = line.split("\t", 1)
        else:
            sha, subject = line[:8], line[8:].lstrip()
        commits.append({"sha": sha, "subject": subject})
    return commits


def _pipeline_summary_safe(repo_root: Path) -> dict[str, Any] | None:
    """Return pipeline v2 summary. None if DB absent; error dict if broken."""
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return None
    try:
        from pipeline_v2.cli import _build_status_report as build_v2_status_report
        report = build_v2_status_report(db_path)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
    # Keep compact — only head counts, not per-module listings.
    summary = report.get("summary") if isinstance(report, dict) else None
    queue = report.get("queue") if isinstance(report, dict) else None
    return {
        "summary": summary,
        "queue_head": {k: v for k, v in (queue or {}).items() if k in ("in_flight", "ready", "blocked", "rejected")},
    }


def build_session_briefing(repo_root: Path) -> dict[str, Any]:
    """Compact control-plane snapshot for agent orientation.

    Target: ≤ 2K tokens. Designed to be the *first* call a fresh agent
    makes, replacing the usual ``cat STATUS.md + git log + ls`` crawl.
    See issue #258.
    """
    status_md = _parse_status_md(repo_root / "STATUS.md")
    worktree = build_worktree_status(repo_root)
    worktrees = build_worktrees_list(repo_root)
    services = build_runtime_services_status(repo_root)
    commits = _recent_commits(repo_root, limit=5)
    pipeline = _pipeline_summary_safe(repo_root)

    alerts: list[str] = []
    if services.get("stale", 0):
        alerts.append(f"{services['stale']} stale pid file(s) — process exited without cleanup")
    if isinstance(pipeline, dict) and "error" in pipeline:
        alerts.append(f"pipeline v2 status unavailable: {pipeline['error']}")

    # Phase C: surface stuck pipeline jobs and critical rubric scores so
    # agents see high-signal issues without polling additional endpoints.
    try:
        stuck = build_pipeline_stuck(repo_root)
    except Exception:  # noqa: BLE001
        stuck = None
    if isinstance(stuck, dict) and stuck.get("exists"):
        leased = stuck.get("stuck_leased_count", 0)
        in_state = stuck.get("stuck_in_state_count", 0)
        if leased:
            alerts.append(f"{leased} job(s) with expired/stale lease — worker may have crashed")
        if in_state:
            alerts.append(f"{in_state} job(s) stuck in-flight with no recent event")

    try:
        quality = build_quality_scores(repo_root)
    except Exception:  # noqa: BLE001
        quality = None
    critical_quality: list[str] = []
    if isinstance(quality, dict) and quality.get("exists"):
        if quality.get("critical_count"):
            alerts.append(
                f"{quality['critical_count']} module(s) at critical rubric score (<2.0)"
            )
        critical_quality = [
            f"{m['module']} [{m['track']}] score {m['score']}"
            for m in (quality.get("critical") or [])[:5]
        ]

    # Action-oriented triage lists. Agents ask "what should I touch"
    # not "what's the global state"; the lists below answer that in
    # the same call as the briefing.
    #
    # ``active``  — what is CURRENTLY owned / in flight. Read-only from
    #               a deciding-agent's view; you don't grab these.
    # ``blocked`` — things the pipeline can't make progress on without
    #               a human or a re-enqueue.
    # ``next``    — things ready to pick up right now.
    #
    # Every row that names a module is mirrored in ``top_modules[]``
    # with a reason + drill-down endpoint.
    actions_active: list[str] = []
    actions_blocked: list[str] = []
    actions_next: list[str] = []
    top_modules: list[dict[str, Any]] = []

    try:
        leases = build_pipeline_leases(repo_root)
    except Exception:  # noqa: BLE001
        leases = None
    if isinstance(leases, dict) and leases.get("exists"):
        for lease in (leases.get("active") or [])[:5]:
            secs = lease.get("seconds_to_expiry")
            actions_active.append(
                f"{lease.get('leased_by','?')} → {lease.get('module_key','?')} "
                f"({lease.get('phase','?')}, {secs}s left)"
            )
            top_modules.append({
                "module_key": lease.get("module_key"),
                "phase": lease.get("phase"),
                "reason": "active_lease",
                "endpoint": f"/api/module/{lease.get('module_key')}/state",
            })

    if isinstance(stuck, dict) and stuck.get("exists"):
        for job in (stuck.get("stuck_leased") or [])[:5]:
            actions_blocked.append(
                f"{job.get('module_key','?')} stale lease "
                f"(held by {job.get('leased_by','?')})"
            )
            top_modules.append({
                "module_key": job.get("module_key"),
                "phase": job.get("phase"),
                "reason": "stale_lease",
                "endpoint": f"/api/pipeline/v2/events?module={job.get('module_key')}",
            })
        for job in (stuck.get("stuck_in_state") or [])[:5]:
            actions_blocked.append(
                f"{job.get('module_key','?')} stuck in {job.get('queue_state','?')}"
            )
            top_modules.append({
                "module_key": job.get("module_key"),
                "phase": job.get("phase"),
                "reason": "stuck_in_state",
                "endpoint": f"/api/pipeline/v2/events?module={job.get('module_key')}",
            })

    if isinstance(quality, dict) and quality.get("exists"):
        for m in (quality.get("critical") or [])[:5]:
            actions_next.append(
                f"rubric-critical rewrite: {m.get('module','?')} "
                f"({m.get('track','?')}) score {m.get('score','?')}"
            )
            # Rubric rows don't carry a real ``module_key`` (the
            # audit uses human-readable labels), so we store the
            # label itself as the key and point at /api/quality/
            # scores for drill-down. Agents can cross-reference.
            top_modules.append({
                "module_key": m.get("module"),
                "phase": None,
                "reason": "critical_quality",
                "endpoint": "/api/quality/scores",
            })

    if isinstance(pipeline, dict) and pipeline.get("queue_head"):
        queue_head = pipeline["queue_head"] or {}
        ready = queue_head.get("ready") or 0
        if ready:
            actions_next.append(f"{ready} job(s) ready to pick up in pipeline v2")
            top_modules.append({
                "module_key": None,
                "phase": None,
                "reason": "ready_queue",
                "endpoint": "/api/pipeline/v2/status",
            })

    return {
        "snapshot": {
            "generated_at": time.time(),
            "generator": "local_api.build_session_briefing",
            "version": 1,
        },
        "workspace": {
            "primary_branch": worktree.get("branch") if worktree.get("ok") else None,
            "dirty": worktree.get("dirty") if worktree.get("ok") else None,
            "counts": worktree.get("counts") if worktree.get("ok") else None,
            "ahead": worktree.get("ahead") if worktree.get("ok") else None,
            "behind": worktree.get("behind") if worktree.get("ok") else None,
            "worktrees_total": worktrees.get("count", 0),
            "worktrees": [
                {
                    "path": wt.get("path"),
                    "branch": wt.get("branch"),
                    "detached": wt.get("detached", False),
                }
                for wt in (worktrees.get("worktrees") or [])
            ],
        },
        "services": {
            "running": services["running"],
            "stopped": services["stopped"],
            "stale": services["stale"],
            "total": services["total"],
        },
        "pipelines": {"v2": pipeline},
        "recent_commits": commits,
        "focus": status_md.get("focus", []),
        "blockers": status_md.get("blockers", []),
        "alerts": alerts,
        "critical_quality": critical_quality,
        "actions": {
            # ``active`` — currently owned / in flight (read-only).
            # ``blocked`` — needs human or re-enqueue.
            # ``next`` — ready to pick up.
            "active": actions_active,
            "blocked": actions_blocked,
            "next": actions_next,
        },
        "top_modules": top_modules,
        "next_reads": [
            {"rel": "schema", "endpoint": "/api/schema", "desc": "Full endpoint index"},
            {"rel": "status", "endpoint": "/api/status/summary", "desc": "Full repo status"},
            {"rel": "pipeline", "endpoint": "/api/pipeline/v2/status", "desc": "Pipeline v2 queue"},
            {"rel": "translation", "endpoint": "/api/translation/v2/status", "desc": "UK translation queue"},
            {"rel": "services", "endpoint": "/api/runtime/services", "desc": "Runtime pids / ports"},
            {"rel": "worktrees", "endpoint": "/api/git/worktrees", "desc": "All attached worktrees"},
            {"rel": "module-state", "endpoint": "/api/module/{key}/state", "desc": "Per-module EN+UK+lab+frontmatter"},
            {"rel": "module-orchestration", "endpoint": "/api/module/{key}/orchestration/latest", "desc": "Per-module latest pipeline job/event"},
        ],
        "links": {
            "status_md": "STATUS.md",
            "claude_md": "CLAUDE.md",
            "dashboard": "/",
        },
    }


def _compact_briefing(briefing: dict[str, Any]) -> dict[str, Any]:
    """Drop fields that aren't actionable for agents to shave tokens further.

    Keeps ``actions`` and ``top_modules`` — those are THE actionable
    fields — and drops navigation aids (``next_reads``, ``links``) and
    the full worktrees list (``worktrees_total`` is enough).
    """
    compact = dict(briefing)
    compact.pop("next_reads", None)
    compact.pop("links", None)
    if "workspace" in compact and isinstance(compact["workspace"], dict):
        ws = dict(compact["workspace"])
        ws.pop("worktrees", None)
        compact["workspace"] = ws
    return compact


# Registry keyed by resolved ``repo_root`` so multiple repos sharing one
# Python process (test suite, multi-repo servers) never cross-contaminate.
_SESSION_BRIEFING_SNAPSHOTS: dict[str, BackgroundSnapshot] = {}
_SESSION_BRIEFING_SNAPSHOT_LOCK = threading.Lock()


def get_or_build_session_briefing(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (briefing, freshness_meta). Uses a background snapshot so
    the briefing endpoint is always cheap."""
    key = str(repo_root.resolve())
    with _SESSION_BRIEFING_SNAPSHOT_LOCK:
        snap = _SESSION_BRIEFING_SNAPSHOTS.get(key)
        if snap is None:
            snap = _register_snapshot(
                f"briefing_session::{key}",
                interval_seconds=15.0,
                builder=lambda: build_session_briefing(repo_root),
            )
            # Prime synchronously on the first request so the first caller
            # sees real data instead of ``freshness_state=refreshing``.
            snap.refresh_blocking()
            snap.start()
            _SESSION_BRIEFING_SNAPSHOTS[key] = snap
    payload, freshness = snap.get()
    if payload is None:
        # Degraded path — build synchronously once.
        payload = build_session_briefing(repo_root)
    return payload, freshness


# ---- /api/schema ----


def build_api_schema() -> dict[str, Any]:
    """Machine-readable endpoint index. Lets agents discover the API
    without reading this 1.7K-LOC file."""
    return {
        "version": 1,
        "conventions": {
            "errors": 'JSON envelope: {"error": "<code>", ...optional context}.',
            "cache": "Weak ETag returned on cacheable responses; send If-None-Match to get 304.",
            "compact": "/api/briefing/session supports ?compact=1 to drop non-actionable fields.",
            "freshness": "Background-refreshed endpoints embed a 'freshness' dict with freshness_state and stale_seconds.",
        },
        "endpoints": [
            {"path": "/", "desc": "HTML dashboard", "content_type": "text/html"},
            {"path": "/healthz", "desc": "Liveness probe"},
            {"path": "/api/schema", "desc": "This document"},
            {
                "path": "/api/briefing/session",
                "desc": "Agent cold-start orientation snapshot. First call for fresh agents.",
                "query": ["compact=1"],
                "freshness": "background-refreshed every 15s",
            },
            {"path": "/api/status/summary", "desc": "Repo status (fast)"},
            {"path": "/api/missing-modules/status", "desc": "Modules missing from nav/sidebar"},
            {"path": "/api/runtime/services", "desc": "Runtime services (pids, uptime, ports)"},
            {"path": "/api/pipeline/v2/status", "desc": "Pipeline v2 queue + per-track"},
            {
                "path": "/api/translation/v2/status",
                "desc": "UK translation queue",
                "query": ["section=...", "freshness=1 (slow git walk)"],
            },
            {"path": "/api/labs/status", "desc": "Labs summary"},
            {"path": "/api/ztt/status", "desc": "Zero-to-Terminal pilot status"},
            {"path": "/api/git/worktree", "desc": "Dirty entries in the PRIMARY repo only"},
            {"path": "/api/git/worktrees", "desc": "All attached worktrees (plural)"},
            {"path": "/api/issue-watch/{n}", "desc": "Single watched GH issue state"},
            {"path": "/api/module/{key}/state", "desc": "Per-module EN+UK+lab+frontmatter+diagnostics"},
            {"path": "/api/module/{key}/orchestration/latest", "desc": "Per-module latest pipeline job+event"},
            {"path": "/api/module/{key}/lease", "desc": "Current pipeline lease for one module"},
            {"path": "/api/pipeline/leases", "desc": "Active pipeline leases (ordered by expiry)"},
            {
                "path": "/api/pipeline/v2/events",
                "desc": "Pipeline v2 event timeline",
                "query": [
                    "module=...",
                    "since_seconds=... (Unix epoch seconds; matches v2.db unit)",
                    "limit=... (max 2000)",
                ],
            },
            {
                "path": "/api/pipeline/v2/stuck",
                "desc": "Stuck/stalled jobs (expired leases + in-flight-with-stale-events)",
                "query": ["threshold_seconds=... (default 3600)"],
            },
            {
                "path": "/api/reviews",
                "desc": "Review audit index (omit query) or single-module log (?module=...)",
                "query": ["module=..."],
            },
            {
                "path": "/api/bridge/messages",
                "desc": ".bridge/messages.db tail",
                "query": ["since=<ISO-8601>", "limit=... (max 500)"],
            },
            {"path": "/api/quality/scores", "desc": "Rubric scores from docs/quality-audit-results.md"},
            {"path": "/api/cache/stats", "desc": "Response-cache introspection"},
        ],
    }


def route_request(repo_root: Path, raw_path: str) -> tuple[int, Any, str]:
    parsed = urlsplit(raw_path)
    path = parsed.path.rstrip("/") or "/"
    query = parse_qs(parsed.query)

    if path in {"/", "/dashboard"}:
        return 200, render_dashboard_html(), "text/html; charset=utf-8"
    if path == "/healthz":
        return 200, {"ok": True}, "application/json; charset=utf-8"
    if path == "/api/status/summary":
        # Dashboard hot path: skip the git-per-file translation + ZTT passes
        # (~2min total). Full versions served by /api/translation/v2/status
        # and /api/ztt/status.
        from status import build_repo_status
        return 200, build_repo_status(repo_root, fast=True), "application/json; charset=utf-8"
    if path == "/api/missing-modules/status":
        from status import _build_missing_modules_summary
        return 200, _build_missing_modules_summary(repo_root), "application/json; charset=utf-8"
    if path == "/api/runtime/services":
        return 200, build_runtime_services_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/pipeline/v2/status":
        db_path = repo_root / ".pipeline" / "v2.db"
        if not db_path.exists():
            return 404, {"error": "missing_db", "db_path": str(db_path)}, "application/json; charset=utf-8"
        from pipeline_v2.cli import _build_status_report as build_v2_status_report
        from status import _enrich_v2_with_per_track
        return 200, _enrich_v2_with_per_track(build_v2_status_report(db_path)), "application/json; charset=utf-8"
    if path == "/api/translation/v2/status":
        section = query.get("section", [None])[0]
        # Dashboard hot path skips the git-per-file freshness walk; callers
        # that need it can pass ?freshness=1.
        want_freshness = query.get("freshness", ["0"])[0] not in ("0", "false", "")
        db_path = repo_root / ".pipeline" / "translation_v2.db"
        from status import _enrich_translation_v2_with_per_track
        if want_freshness:
            from translation_v2 import build_status as build_translation_status
            t2 = build_translation_status(repo_root, db_path=db_path, section=section)
        else:
            from translation_v2 import _build_translation_queue_status
            t2 = {
                "repo_root": str(repo_root),
                "db_path": str(db_path),
                "section": section,
                "freshness": None,
                "queue": _build_translation_queue_status(db_path) if db_path.exists() else None,
            }
        return 200, _enrich_translation_v2_with_per_track(t2), "application/json; charset=utf-8"
    if path == "/api/labs/status":
        from status import _build_lab_summary
        return 200, _build_lab_summary(repo_root), "application/json; charset=utf-8"
    if path == "/api/ztt/status":
        from ztt_status import build_status as build_ztt_status
        return 200, build_ztt_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/git/worktree":
        return 200, build_worktree_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/git/worktrees":
        return 200, build_worktrees_list(repo_root), "application/json; charset=utf-8"
    if path == "/api/schema":
        return 200, build_api_schema(), "application/json; charset=utf-8"
    if path == "/api/briefing/session":
        compact = query.get("compact", ["0"])[0] not in ("0", "false", "")
        briefing, freshness = get_or_build_session_briefing(repo_root)
        briefing = dict(briefing)
        briefing["freshness"] = freshness
        if compact:
            briefing = _compact_briefing(briefing)
        return 200, briefing, "application/json; charset=utf-8"
    if path == "/api/cache/stats":
        return 200, _cache_stats(), "application/json; charset=utf-8"
    if path == "/api/pipeline/leases":
        return 200, build_pipeline_leases(repo_root), "application/json; charset=utf-8"
    if path == "/api/pipeline/v2/stuck":
        try:
            threshold = int(query.get("threshold_seconds", [str(_DEFAULT_STUCK_THRESHOLD_SECONDS)])[0])
        except (TypeError, ValueError):
            threshold = _DEFAULT_STUCK_THRESHOLD_SECONDS
        threshold = max(60, min(threshold, 24 * 3600))
        return 200, build_pipeline_stuck(repo_root, threshold_seconds=threshold), "application/json; charset=utf-8"
    if path == "/api/pipeline/v2/events":
        mk = query.get("module", [None])[0]
        module_key: str | None = None
        if mk:
            module_key = _validate_module_key(repo_root, mk)
            if module_key is None:
                return 400, {"error": "invalid_module_key"}, "application/json; charset=utf-8"
        try:
            since_seconds = int(query.get("since_seconds", ["0"])[0]) or None
        except (TypeError, ValueError):
            since_seconds = None
        try:
            limit = int(query.get("limit", ["200"])[0])
        except (TypeError, ValueError):
            limit = 200
        return 200, build_pipeline_events(repo_root, module_key, since_seconds, limit), "application/json; charset=utf-8"
    if path == "/api/reviews":
        mk = query.get("module", [None])[0]
        if mk:
            module_key = _validate_module_key(repo_root, mk)
            if module_key is None:
                return 400, {"error": "invalid_module_key"}, "application/json; charset=utf-8"
            payload = build_module_reviews(repo_root, module_key)
            if payload is None:
                return 404, {"error": "review_not_found", "module_key": module_key}, "application/json; charset=utf-8"
            return 200, payload, "application/json; charset=utf-8"
        return 200, build_reviews_index(repo_root), "application/json; charset=utf-8"
    if path == "/api/bridge/messages":
        since = query.get("since", [None])[0]
        try:
            limit = int(query.get("limit", ["100"])[0])
        except (TypeError, ValueError):
            limit = 100
        return 200, build_bridge_messages(repo_root, since, limit), "application/json; charset=utf-8"
    if path == "/api/quality/scores":
        return 200, build_quality_scores(repo_root), "application/json; charset=utf-8"
    if path.startswith("/api/module/") and path.endswith("/lease"):
        raw_key = unquote(path[len("/api/module/") : -len("/lease")]).strip("/")
        if not raw_key:
            return 400, {"error": "missing_module_key"}, "application/json; charset=utf-8"
        module_key = _validate_module_key(repo_root, raw_key)
        if module_key is None:
            return 400, {"error": "invalid_module_key"}, "application/json; charset=utf-8"
        return 200, build_module_lease(repo_root, module_key), "application/json; charset=utf-8"
    if path.startswith("/api/issue-watch/"):
        try:
            issue_number = int(path.split("/")[-1])
        except ValueError:
            return 400, {"error": "invalid_issue_number"}, "application/json; charset=utf-8"
        payload = build_issue_watch_state(repo_root, issue_number)
        if payload is None:
            return 404, {"error": "missing_issue_watch_state", "issue_number": issue_number}, "application/json; charset=utf-8"
        return 200, payload, "application/json; charset=utf-8"
    if path.startswith("/api/module/") and path.endswith("/state"):
        raw_key = unquote(path[len("/api/module/") : -len("/state")]).strip("/")
        if not raw_key:
            return 400, {"error": "missing_module_key"}, "application/json; charset=utf-8"
        module_key = _validate_module_key(repo_root, raw_key)
        if module_key is None:
            return 400, {"error": "invalid_module_key"}, "application/json; charset=utf-8"
        return 200, build_module_state(repo_root, module_key), "application/json; charset=utf-8"
    if path.startswith("/api/module/") and path.endswith("/orchestration/latest"):
        raw_key = unquote(path[len("/api/module/") : -len("/orchestration/latest")]).strip("/")
        if not raw_key:
            return 400, {"error": "missing_module_key"}, "application/json; charset=utf-8"
        module_key = _validate_module_key(repo_root, raw_key)
        if module_key is None:
            return 400, {"error": "invalid_module_key"}, "application/json; charset=utf-8"
        return 200, build_module_orchestration_latest(repo_root, module_key), "application/json; charset=utf-8"
    return 404, {"error": "not_found", "path": path}, "application/json; charset=utf-8"


# ============================================================
# Cache policy + request pipeline
# ============================================================
#
# TTLs are tuned for the dashboard (60s refresh) and agent polling. They are
# short enough that human interactivity never sees stale state beyond a few
# seconds, but long enough to absorb thundering-herd polls. sqlite-backed
# routes add a ``PRAGMA data_version``-based dep check so a write from the
# pipeline supervisor invalidates the cache immediately.


def _v_v2_db(repo_root: Path) -> tuple:
    return ("v2", _sqlite_version_key(repo_root / ".pipeline" / "v2.db"))


def _v_translation_db(repo_root: Path) -> tuple:
    return ("t2", _sqlite_version_key(repo_root / ".pipeline" / "translation_v2.db"))


def _v_always_fresh(_: Path) -> tuple:
    # Placeholder for TTL-only policies.
    return ("ttl",)


# Map fixed paths (query-independent beyond ``?compact=1``) to policies.
# (ttl_seconds, version_fn_or_None)
CACHE_POLICY: dict[str, tuple[float, Callable[[Path], tuple] | None]] = {
    "/healthz": (60.0, None),
    "/api/schema": (600.0, None),
    "/api/status/summary": (10.0, _v_v2_db),
    "/api/missing-modules/status": (30.0, None),
    "/api/runtime/services": (2.0, None),
    "/api/pipeline/v2/status": (5.0, _v_v2_db),
    "/api/translation/v2/status": (5.0, _v_translation_db),
    "/api/labs/status": (10.0, None),
    "/api/ztt/status": (30.0, None),
    "/api/git/worktree": (2.0, None),
    "/api/git/worktrees": (5.0, None),
    "/api/briefing/session": (5.0, None),  # background-refreshed; TTL just caps rebuild rate
}


def _match_etag(if_none_match: str, etag: str) -> bool:
    """Return True if the client's If-None-Match header matches our ETag.

    Handles comma-separated lists and leading ``W/`` weak marker.
    """
    if not if_none_match:
        return False
    candidates = [tok.strip() for tok in if_none_match.split(",") if tok.strip()]
    # Strip W/ prefix on both sides for weak-compare semantics.
    our = etag[2:] if etag.startswith("W/") else etag
    for cand in candidates:
        if cand == "*":
            return True
        normalized = cand[2:] if cand.startswith("W/") else cand
        if normalized == our:
            return True
    return False


def serve_request(
    repo_root: Path, raw_path: str
) -> tuple[int, bytes, str, str]:
    """Compute ``(status, body_bytes, content_type, etag)`` for ``raw_path``.

    Serves from cache for paths registered in ``CACHE_POLICY``. Builds on miss.
    ETag is always set from the response bytes so 304 works for every 2xx
    response, cached or not.
    """
    parsed = urlsplit(raw_path)
    path = parsed.path.rstrip("/") or "/"
    query = parse_qs(parsed.query)

    policy = CACHE_POLICY.get(path)
    if policy is not None:
        ttl, version_fn = policy
        cache_key = _normalized_cache_key(path, query, repo_root=repo_root)

        def _version() -> tuple:
            return version_fn(repo_root) if version_fn is not None else ("ttl",)

        def _build() -> tuple[int, Any, str]:
            return route_request(repo_root, raw_path)

        return cached_response(cache_key, ttl, _version, _build)

    status_code, payload, content_type = route_request(repo_root, raw_path)
    body_bytes = _serialize_payload(payload, content_type)
    etag = _weak_etag(body_bytes)
    return status_code, body_bytes, content_type, etag


def make_handler(repo_root: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                status_code, body, content_type, etag = serve_request(repo_root, self.path)
            except sqlite3.Error as exc:
                status_code = 500
                payload = {
                    "error": "sqlite_error",
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "path": self.path,
                }
                content_type = "application/json; charset=utf-8"
                body = _serialize_payload(payload, content_type)
                etag = _weak_etag(body)
            except Exception as exc:  # noqa: BLE001 - surface all read failures as JSON
                status_code = 500
                payload = {
                    "error": "internal_error",
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "path": self.path,
                }
                content_type = "application/json; charset=utf-8"
                body = _serialize_payload(payload, content_type)
                etag = _weak_etag(body)

            if 200 <= status_code < 300:
                inm = self.headers.get("If-None-Match", "")
                if _match_etag(inm, etag):
                    self.send_response(304)
                    self.send_header("ETag", etag)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return

            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            if 200 <= status_code < 300:
                self.send_header("ETag", etag)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve(repo_root: Path, host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(repo_root))
    print(json.dumps({"repo_root": str(repo_root), "host": host, "port": port}, sort_keys=True))
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic local API for KubeDojo state")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    serve(args.repo_root.resolve(), args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

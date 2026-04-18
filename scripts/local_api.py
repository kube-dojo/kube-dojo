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
import uuid
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
GH_REPO = "kube-dojo/kube-dojo.github.io"
GH_CACHE_TTL_SECONDS = 60.0
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
# Build jobs (/api/build/run + /api/build/status)
# ============================================================


_BUILD_JOBS_LOCK = threading.Lock()
_BUILD_JOBS_STATE: dict[str, dict[str, Any]] = {}
_BUILD_JOBS_FILENAME = ".cache/build_jobs.json"
_BUILD_JOBS_MAX = 10
_BUILD_TAIL_LINES = 30
_WARNING_LINE_RE = re.compile(r"\bwarning\b", re.IGNORECASE)


def _build_jobs_path(repo_root: Path) -> Path:
    return repo_root / _BUILD_JOBS_FILENAME


def _read_build_jobs(repo_root: Path) -> list[dict[str, Any]]:
    path = _build_jobs_path(repo_root)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(payload, dict):
        payload = payload.get("jobs", [])
    if not isinstance(payload, list):
        return []
    return [job for job in payload if isinstance(job, dict)]


def _write_build_jobs(repo_root: Path, jobs: list[dict[str, Any]]) -> None:
    path = _build_jobs_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(
        json.dumps(jobs[-_BUILD_JOBS_MAX :], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _reset_build_jobs_state() -> None:
    """Test helper: drop in-memory build-job state across repos."""
    with _BUILD_JOBS_LOCK:
        _BUILD_JOBS_STATE.clear()


def _trim_tail(lines: list[str]) -> list[str]:
    return lines[-_BUILD_TAIL_LINES :]


def _normalize_warning_line(line: str) -> str | None:
    normalized = " ".join(line.strip().split())
    if not normalized or not _WARNING_LINE_RE.search(normalized):
        return None
    return normalized


def _find_build_job_locked(state: dict[str, Any], job_id: str) -> dict[str, Any] | None:
    for job in reversed(state["jobs"]):
        if job.get("job_id") == job_id:
            return job
    return None


def _persist_build_state_locked(repo_root: Path, state: dict[str, Any]) -> None:
    state["jobs"] = state["jobs"][-_BUILD_JOBS_MAX :]
    _write_build_jobs(repo_root, state["jobs"])


def _load_build_state(repo_root: Path) -> dict[str, Any]:
    repo_key = str(repo_root.resolve())
    with _BUILD_JOBS_LOCK:
        state = _BUILD_JOBS_STATE.get(repo_key)
        if state is not None:
            return state
        jobs = _read_build_jobs(repo_root)[-_BUILD_JOBS_MAX :]
        repaired = False
        now = time.time()
        for job in jobs:
            if job.get("state") != "running":
                continue
            started_at = float(job.get("started_at") or now)
            tail = list(job.get("last_30_lines") or [])
            tail.append("local_api: build job marked failed after API restart")
            job["state"] = "fail"
            job["finished_at"] = now
            job["duration_s"] = round(max(0.0, now - started_at), 3)
            job["last_30_lines"] = _trim_tail(tail)
            job["new_warnings"] = sorted(set(job.get("new_warnings") or []))
            repaired = True
        state = {"jobs": jobs, "active_job_id": None}
        if repaired:
            _persist_build_state_locked(repo_root, state)
        _BUILD_JOBS_STATE[repo_key] = state
        return state


def _spawn_build_process(repo_root: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        ["npm", "run", "build"],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def _build_job_payload(job: dict[str, Any]) -> dict[str, Any]:
    started_at = float(job["started_at"])
    if job.get("state") == "running":
        duration_s = round(max(0.0, time.time() - started_at), 3)
    else:
        duration_s = job.get("duration_s")
    return {
        "job_id": job["job_id"],
        "started_at": started_at,
        "state": job["state"],
        "duration_s": duration_s,
        "last_30_lines": list(job.get("last_30_lines") or []),
        "new_warnings": list(job.get("new_warnings") or []),
        "finished_at": job.get("finished_at"),
    }


def _monitor_build_job(repo_root: Path, job_id: str, process: subprocess.Popen[str]) -> None:
    state = _load_build_state(repo_root)
    if process.stdout is not None:
        for raw_line in process.stdout:
            line = raw_line.rstrip("\r\n")
            warning = _normalize_warning_line(line)
            with _BUILD_JOBS_LOCK:
                job = _find_build_job_locked(state, job_id)
                if job is None:
                    continue
                tail = list(job.get("last_30_lines") or [])
                tail.append(line)
                job["last_30_lines"] = _trim_tail(tail)
                warning_set = set(job.get("warning_set") or [])
                if warning is not None:
                    warning_set.add(warning)
                baseline = set(job.get("baseline_warning_set") or [])
                job["warning_set"] = sorted(warning_set)
                job["new_warnings"] = sorted(warning_set - baseline)
                _persist_build_state_locked(repo_root, state)
        process.stdout.close()

    return_code = process.wait()
    finished_at = time.time()
    with _BUILD_JOBS_LOCK:
        job = _find_build_job_locked(state, job_id)
        if job is None:
            return
        baseline = set(job.get("baseline_warning_set") or [])
        warning_set = set(job.get("warning_set") or [])
        job["state"] = "pass" if return_code == 0 else "fail"
        job["finished_at"] = finished_at
        job["duration_s"] = round(max(0.0, finished_at - float(job["started_at"])), 3)
        job["new_warnings"] = sorted(warning_set - baseline)
        job.pop("baseline_warning_set", None)
        if state.get("active_job_id") == job_id:
            state["active_job_id"] = None
        _persist_build_state_locked(repo_root, state)


def start_build_job(repo_root: Path) -> tuple[int, Any, str]:
    state = _load_build_state(repo_root)
    with _BUILD_JOBS_LOCK:
        active_job_id = state.get("active_job_id")
        if active_job_id:
            active_job = _find_build_job_locked(state, active_job_id)
            if active_job is not None and active_job.get("state") == "running":
                return (
                    409,
                    {
                        "error": "build_in_progress",
                        "job_id": active_job_id,
                        "started_at": active_job.get("started_at"),
                    },
                    "application/json; charset=utf-8",
                )
            state["active_job_id"] = None

        previous_green_warnings: set[str] = set()
        for previous_job in reversed(state["jobs"]):
            if previous_job.get("state") == "pass":
                previous_green_warnings = set(previous_job.get("warning_set") or [])
                break

        started_at = time.time()
        job_id = f"build-{uuid.uuid4().hex[:12]}"
        job = {
            "job_id": job_id,
            "started_at": started_at,
            "state": "running",
            "duration_s": None,
            "finished_at": None,
            "last_30_lines": [],
            "warning_set": [],
            "baseline_warning_set": sorted(previous_green_warnings),
            "new_warnings": [],
        }
        state["jobs"].append(job)
        state["active_job_id"] = job_id
        _persist_build_state_locked(repo_root, state)

    try:
        process = _spawn_build_process(repo_root)
    except OSError as exc:
        finished_at = time.time()
        with _BUILD_JOBS_LOCK:
            failed_job = _find_build_job_locked(state, job_id)
            if failed_job is not None:
                failed_job["state"] = "fail"
                failed_job["finished_at"] = finished_at
                failed_job["duration_s"] = round(max(0.0, finished_at - started_at), 3)
                failed_job["last_30_lines"] = [f"local_api: failed to start build: {exc}"]
                failed_job.pop("baseline_warning_set", None)
                state["active_job_id"] = None
                _persist_build_state_locked(repo_root, state)
        return (
            500,
            {"error": "build_spawn_failed", "job_id": job_id, "message": str(exc)},
            "application/json; charset=utf-8",
        )

    threading.Thread(
        target=_monitor_build_job,
        args=(repo_root, job_id, process),
        daemon=True,
    ).start()
    return 202, {"job_id": job_id, "started_at": started_at}, "application/json; charset=utf-8"


def get_build_job_status(repo_root: Path, job_id: str) -> tuple[int, Any, str]:
    state = _load_build_state(repo_root)
    with _BUILD_JOBS_LOCK:
        job = _find_build_job_locked(state, job_id)
        if job is None:
            return 404, {"error": "build_job_not_found", "job_id": job_id}, "application/json; charset=utf-8"
        return 200, _build_job_payload(job), "application/json; charset=utf-8"


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
    etag_builder: Callable[[Any, bytes], str] | None = None,
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
    etag = etag_builder(payload, body_bytes) if etag_builder is not None else _weak_etag(body_bytes)

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


def _gh_json_fields(*fields: str) -> str:
    return ",".join(fields)


def _gh_repo_cmd(*args: str) -> list[str]:
    return ["gh", *args, "--repo", GH_REPO]


def _run_gh_json(*args: str, timeout: int = 10) -> tuple[int, Any]:
    try:
        result = subprocess.run(
            _gh_repo_cmd(*args),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return 503, {"error": "gh CLI not available"}
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "Could not resolve to an issue or pull request" in stderr:
            return 404, {"error": "not_found"}
        return 502, {"error": "gh command failed", "message": stderr or "gh command failed"}
    try:
        return 200, json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return 502, {"error": "invalid_gh_json", "message": str(exc)}


def _normalize_gh_item(item: dict[str, Any]) -> dict[str, Any]:
    labels = item.get("labels") or []
    assignees = item.get("assignees") or []
    comments = item.get("comments") or []
    return {
        "number": item.get("number"),
        "title": item.get("title", ""),
        "state": item.get("state", ""),
        "labels": [
            label.get("name")
            for label in labels
            if isinstance(label, dict) and label.get("name")
        ],
        "assignees": [
            assignee.get("login")
            for assignee in assignees
            if isinstance(assignee, dict) and assignee.get("login")
        ],
        "comments_count": len(comments) if isinstance(comments, list) else 0,
        "updated_at": item.get("updatedAt", ""),
        "url": item.get("url", ""),
    }


def _normalize_gh_comments(comments: Any) -> list[dict[str, Any]]:
    if not isinstance(comments, list):
        return []
    normalized: list[dict[str, Any]] = []
    for comment in comments[-5:]:
        if not isinstance(comment, dict):
            continue
        author = comment.get("author") or {}
        normalized.append(
            {
                "author": author.get("login", "") if isinstance(author, dict) else "",
                "body": comment.get("body", ""),
                "created_at": comment.get("createdAt", ""),
                "url": comment.get("url", ""),
            }
        )
    return normalized


def _build_gh_list(kind: str, state: str, limit: int) -> tuple[int, Any, str]:
    status_code, payload = _run_gh_json(
        kind,
        "list",
        "--state",
        state,
        "--limit",
        str(limit),
        "--json",
        _gh_json_fields("number", "title", "state", "labels", "assignees", "comments", "updatedAt", "url"),
    )
    if status_code != 200:
        return status_code, payload, "application/json; charset=utf-8"
    items = [
        _normalize_gh_item(item)
        for item in payload
        if isinstance(item, dict)
    ]
    return 200, {
        "repo": GH_REPO,
        "state": state,
        "limit": limit,
        "count": len(items),
        "items": items,
    }, "application/json; charset=utf-8"


def _build_gh_detail(kind: str, number: int) -> tuple[int, Any, str]:
    fields = ["number", "title", "state", "labels", "assignees", "comments", "updatedAt", "url"]
    if kind == "pr":
        fields.append("mergeable")
    status_code, payload = _run_gh_json(
        kind,
        "view",
        str(number),
        "--json",
        _gh_json_fields(*fields),
    )
    if status_code != 200:
        return status_code, payload, "application/json; charset=utf-8"
    if not isinstance(payload, dict):
        return 502, {"error": "invalid_gh_json", "message": "expected object"}, "application/json; charset=utf-8"
    item = _normalize_gh_item(payload)
    item["comments"] = _normalize_gh_comments(payload.get("comments"))
    if kind == "pr":
        item["mergeable"] = payload.get("mergeable")
    return 200, item, "application/json; charset=utf-8"


def _is_gh_path(path: str) -> bool:
    return (
        path in {"/api/gh/issues", "/api/gh/prs"}
        or path.startswith("/api/gh/issues/")
        or path.startswith("/api/gh/prs/")
    )


def _gh_payload_etag(path: str, payload: Any) -> str:
    latest = "empty"
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            updated_values = [
                item.get("updated_at", "")
                for item in items
                if isinstance(item, dict) and item.get("updated_at")
            ]
            if updated_values:
                latest = max(updated_values)
        elif payload.get("updated_at"):
            latest = str(payload["updated_at"])
    return _weak_etag(f"{path}:{latest}".encode("utf-8"))


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
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "--branch"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "repo_root": str(repo_root),
            "ok": False,
            "error": f"git status unavailable: {type(exc).__name__}",
        }
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
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "error": f"git worktree list unavailable: {type(exc).__name__}",
            "worktrees": [],
        }
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
    review = build_module_reviews(repo_root, normalized, max_bytes=50_000)
    if review and review.get("fact_check_status") == "unverified":
        state["diagnostics"].append(_diag(
            severity="warn",
            code="fact_check_unverified",
            summary="Latest review contains unverified fact claims",
            source="reviews",
            next_action=f"GET /api/reviews?module={normalized}",
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
    """Stuck/dead-letter view of pipeline v2.

    Three signals are surfaced:

    - ``stuck_leased``: jobs whose lease has expired OR whose
      ``leased_at`` is older than the threshold.
    - ``stuck_in_state``: jobs in an in-flight ``queue_state`` with no
      recent event *for the current attempt*. Events are correlated
      to the job's current ``lease_id`` — a recent event from an
      earlier lease for the same module must not mask a hung
      current lease.
    - ``dead_lettered``: modules with a ``module_dead_lettered``
      event that has not been superseded by a later
      ``dead_letter_recovered`` event. These are modules the
      pipeline explicitly gave up on and need human triage or
      ``pipeline_v2 recover-dead-letters`` before they will make
      progress.
    """
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return {
            "db_path": str(db_path),
            "exists": False,
            "stuck_leased": [],
            "stuck_in_state": [],
            "dead_lettered": [],
        }

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

    # Dead-lettered modules. We defer to ``pipeline_v2.cli.
    # _current_dead_letter_rows`` for the reducer so this endpoint
    # agrees with the pipeline's own needs_human_count. That helper
    # sorts by ``(at, id)`` and compares recovery-event order against
    # dead-letter-event order, so out-of-order ``at`` timestamps or
    # ``(id)`` vs ``(at)`` skew don't cause this endpoint to
    # disagree with the source of truth.
    dead_events = _query_sqlite_rows(
        db_path,
        """
        SELECT id, module_key, type, payload_json, at
        FROM events
        WHERE type IN (
            'module_dead_lettered',
            'needs_human_intervention',
            'dead_letter_recovered'
        )
        """,
    )
    # Only swallow the "pipeline_v2 not installed at all" case,
    # narrowed by ``exc.name`` so a transitive import failure inside
    # pipeline_v2.cli (broken install, missing dep) doesn't silently
    # degrade to ``dead_lettered = []`` and hide modules that need
    # human triage. A renamed/removed ``_current_dead_letter_rows``
    # raises ImportError (not ModuleNotFoundError) and propagates.
    _current_dead_letter_rows = None
    try:
        from pipeline_v2.cli import _current_dead_letter_rows
    except ModuleNotFoundError as exc:
        if exc.name not in {"pipeline_v2", "pipeline_v2.cli"}:
            raise
    if _current_dead_letter_rows is not None and dead_events:
        dead_lettered = _current_dead_letter_rows(dead_events)
    else:
        dead_lettered = []

    # Phase D stale-worker view: per-``leased_by`` roll-up. A worker may
    # hold several non-expired leases but have gone silent across all of
    # them — that's a zombie that the per-module ``stuck_in_state`` view
    # doesn't surface cleanly because a bursty event on a sibling lease
    # can hide it. We group by worker and take the most recent event
    # from ANY of their current leases as the heartbeat. ``idle_seconds``
    # = None means "never emitted" and ranks as strictly staler than any
    # finite idle time.
    active_lease_rows = _query_sqlite_rows(
        db_path,
        """
        SELECT j.leased_by, j.lease_id, j.module_key, j.phase,
               j.leased_at, j.lease_expires_at,
               (
                   SELECT MAX(at) FROM events e
                   WHERE e.lease_id = j.lease_id
               ) AS last_event_at
        FROM jobs j
        WHERE j.leased_by IS NOT NULL
          AND (j.lease_expires_at IS NULL OR j.lease_expires_at >= ?)
        ORDER BY j.leased_by ASC, j.lease_id ASC, j.id ASC
        """,
        (now_seconds,),
    )
    by_worker: dict[str, dict[str, Any]] = {}
    for row in active_lease_rows:
        worker = row.get("leased_by")
        if not worker:
            continue
        bucket = by_worker.setdefault(str(worker), {
            "leased_by": str(worker),
            "active_lease_count": 0,
            "module_keys": [],
            "last_event_at": None,
        })
        bucket["active_lease_count"] += 1
        mk = row.get("module_key")
        if mk and mk not in bucket["module_keys"]:
            bucket["module_keys"].append(mk)
        le = row.get("last_event_at")
        if isinstance(le, (int, float)):
            if bucket["last_event_at"] is None or le > bucket["last_event_at"]:
                bucket["last_event_at"] = int(le)

    stale_workers: list[dict[str, Any]] = []
    for bucket in by_worker.values():
        le = bucket["last_event_at"]
        if le is None:
            idle: int | None = None
        else:
            idle = max(0, now_seconds - int(le))
        # Stale if the worker has never emitted an event on any active
        # lease, OR its most recent heartbeat is older than the threshold.
        if idle is None or idle > threshold_seconds:
            bucket["idle_seconds"] = idle
            stale_workers.append(bucket)
    # Rank "never emitted" as strictly staler than any finite idle, then
    # longest-idle first, with ``leased_by`` as a deterministic tiebreaker
    # so two workers at the same idle-seconds don't rearrange across
    # calls. (Codex Phase D review: finite-idle ties were non-
    # deterministic.)
    stale_workers.sort(
        key=lambda w: (
            0 if w.get("idle_seconds") is None else 1,
            -(w.get("idle_seconds") or 0),
            str(w.get("leased_by") or ""),
        )
    )

    return {
        "db_path": str(db_path),
        "exists": True,
        "threshold_seconds": threshold_seconds,
        "queried_at_seconds": now_seconds,
        "stuck_leased_count": len(stuck_leased),
        "stuck_leased": stuck_leased,
        "stuck_in_state_count": len(stuck_in_state),
        "stuck_in_state": stuck_in_state,
        "dead_lettered_count": len(dead_lettered),
        "dead_lettered": dead_lettered,
        "stale_workers_count": len(stale_workers),
        "stale_workers": stale_workers,
    }


# ---- reviews audit log ----


_REVIEW_AUDIT_DIR = Path(".pipeline") / "reviews"
_VALID_FACT_CHECK_STATUSES = {"verified", "unverified", "failed", "none"}
_LATEST_REVIEW_RE = re.compile(r"^## .*?— `REVIEW`.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
_FAILED_FACT_CHECK_RE = re.compile(r"^- \*\*FACT_CHECK\*\*:\s*(.+)$", re.MULTILINE)
_UNVERIFIED_CLAIM_RE = re.compile(r"unverified:\s*(.+)", re.IGNORECASE)


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


def _fact_check_summary(review_body: str) -> dict[str, Any]:
    latest = next(iter(_LATEST_REVIEW_RE.findall(review_body)), "")
    failed = [m.strip() for m in _FAILED_FACT_CHECK_RE.findall(latest)]
    if failed:
        return {"fact_check_status": "failed", "unverified_evidence": []}
    unverified = [f"unverified: {m.strip()}" for m in _UNVERIFIED_CLAIM_RE.findall(latest)]
    if unverified:
        return {"fact_check_status": "unverified", "unverified_evidence": unverified[:3]}
    return {
        "fact_check_status": "verified" if "FACT_CHECK" in latest else "none",
        "unverified_evidence": [],
    }


def build_reviews_index(
    repo_root: Path,
    *,
    fact_check_status: str | None = None,
) -> dict[str, Any]:
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
            summary = _fact_check_summary(path.read_text(encoding="utf-8"))
        except OSError:
            mtime, size = 0.0, 0
            summary = {"fact_check_status": "none", "unverified_evidence": []}
        if fact_check_status and summary["fact_check_status"] != fact_check_status:
            continue
        reviews.append({
            "module_key": _review_filename_to_module_key(path.name),
            "filename": path.name,
            "size": size,
            "mtime": mtime,
            **summary,
        })
    reviews.sort(key=lambda item: item["mtime"], reverse=True)
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
    summary = _fact_check_summary(body)
    return {
        "module_key": module_key,
        "path": str(path),
        "size": on_disk_size,
        "body_size": len(body.encode("utf-8")),
        "truncated": truncated,
        "max_bytes": max_bytes if truncated else None,
        "mtime": mtime,
        **summary,
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
_CITATION_STATUS_CACHE: dict[str, dict[str, Any]] = {}
_CITATION_STATUS_CACHE_LOCK = threading.Lock()


_QUALITY_TITLE_RE = re.compile(r'^title:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
_QUALITY_TRACK_LABELS = {
    "ai": "AI",
    "ai-ml-engineering": "AI/ML Engineering",
    "cloud": "Cloud",
    "linux": "Linux",
    "on-premises": "On-Premises",
    "platform": "Platform",
    "prerequisites": "Prerequisites",
}


def _quality_severity(score: float) -> str:
    if score < 2.0:
        return "critical"
    if score < 2.5:
        return "poor"
    if score < 3.5:
        return "needs_work"
    if score < 4.5:
        return "good"
    return "excellent"


def _quality_track_label(rel: Path) -> str:
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "k8s" and parts[1] in _CERT_TRACKS:
        return parts[1].upper()
    top = _QUALITY_TRACK_LABELS.get(parts[0], parts[0].replace("-", " ").title())
    if len(parts) >= 2 and not parts[1].startswith(("module-", "part")):
        return f"{top} {parts[1].replace('-', ' ').title()}"
    return top


def _quality_title_and_label(rel: Path, text: str) -> tuple[str, str]:
    frontmatter = text[4:].split("\n---\n", 1)[0] if text.startswith("---\n") and "\n---\n" in text[4:] else ""
    match = _QUALITY_TITLE_RE.search(frontmatter)
    title = (match.group(1).strip() if match else "") or rel.stem.replace("-", " ").title()
    title = re.sub(r"^Module\s+[0-9]+(?:\.[0-9]+)*:\s*", "", title).strip()
    track = _quality_track_label(rel)
    number_match = _MODULE_NUMBER_RE.search(rel.stem)
    if track.lower() in _CERT_TRACKS and number_match:
        return title, f"{track} {number_match.group(1)}: {title}"
    return title, f"{track}: {title}"


def build_quality_scores(repo_root: Path) -> dict[str, Any]:
    """Build live heuristic quality scores from current EN module files.

    Signals stay intentionally cheap and debuggable: line count drives
    the base score, then valid frontmatter/title, quiz/knowledge-check,
    exercises/labs, and diagrams/mermaid add structure bonuses.
    """
    docs_root = repo_root / "src" / "content" / "docs"
    if not docs_root.exists():
        return {"exists": False, "source": "heuristic", "generated_at": time.time(), "modules": [], "count": 0}

    paths = sorted(
        path
        for path in docs_root.glob("**/module-*.md")
        if ".staging." not in path.name and not path.relative_to(docs_root).as_posix().startswith("uk/")
    )
    sig = hashlib.sha1()
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            continue
        sig.update(path.relative_to(docs_root).as_posix().encode("utf-8"))
        sig.update(f":{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8"))
    signature = sig.hexdigest()
    key = str(docs_root.resolve())
    with _QUALITY_AUDIT_CACHE_LOCK:
        entry = _QUALITY_AUDIT_CACHE.get(key)
        if entry is not None and entry["signature"] == signature:
            return entry["data"]

    modules: list[dict[str, Any]] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lines_count = len(text.splitlines())
        has_title = text.startswith("---\n") and bool(_QUALITY_TITLE_RE.search(text[4:].split("\n---\n", 1)[0]))
        has_quiz = bool(re.search(r"^##+\s+(quiz|knowledge check)\b", text, re.IGNORECASE | re.MULTILINE))
        has_exercise = bool(re.search(r"^##+\s+(exercise|hands-on|practice|lab)\b", text, re.IGNORECASE | re.MULTILINE))
        has_diagram = "```mermaid" in text or "<details>" in text
        base = 0.4 if lines_count < 60 else 0.9 if lines_count < 120 else 1.4 if lines_count < 220 else 1.8 if lines_count < 300 else 2.1
        score = min(5.0, round(base + (0.6 if has_title else 0.0) + (0.8 if has_quiz else 0.0) + (0.8 if has_exercise else 0.0) + (0.7 if has_diagram else 0.0), 1))
        severity = _quality_severity(score)
        action = {
            "critical": "Critical",
            "poor": "Rewrite",
            "needs_work": "Improve",
            "good": "Polish",
            "excellent": "Strong",
        }[severity]
        issues = []
        if lines_count < 220:
            issues.append("thin")
        if not has_quiz:
            issues.append("no quiz")
        if not has_exercise:
            issues.append("no exercise")
        if not has_diagram:
            issues.append("no diagram")
        _, module = _quality_title_and_label(path.relative_to(docs_root), text)
        modules.append({
            "module": module,
            "track": _quality_track_label(path.relative_to(docs_root)),
            "lines": lines_count,
            "score": score,
            "severity": severity,
            "action": action,
            "primary_issue": ", ".join(issues[:2]) if issues else "balanced",
        })

    scores = [m["score"] for m in modules]
    avg = round(sum(scores) / len(scores), 2) if scores else None
    critical = [m for m in modules if m["severity"] == "critical"]
    poor = [m for m in modules if m["severity"] == "poor"]
    data = {
        "exists": True,
        "source": "heuristic",
        "generated_at": time.time(),
        "signature": signature[:12],
        "docs_root": str(docs_root),
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
        _QUALITY_AUDIT_CACHE[key] = {"signature": signature, "data": data}
    return data


def build_quality_upgrade_plan(repo_root: Path, *, target: float = 4.0) -> dict[str, Any]:
    """Return an upgrade-planning view for modules below a rubric target.

    This turns the historical audit into an actionable queue for the
    4/5 and 5/5 upgrade epics:

    - target < 5.0  -> issue #180
    - target >= 5.0 -> issue #181

    Only scored modules can be classified precisely; the response also
    reports how many repo modules remain unscored/unknown.
    """
    try:
        quality = build_quality_scores(repo_root)
    except Exception as exc:  # noqa: BLE001
        return {
            "exists": False,
            "error": f"quality_scores_failed: {type(exc).__name__}",
            "target": target,
        }

    docs_root = repo_root / "src" / "content" / "docs"
    total_modules = 0
    if docs_root.exists():
        total_modules = sum(
            1
            for path in docs_root.glob("**/module-*.md")
            if ".staging." not in path.name and not path.relative_to(docs_root).as_posix().startswith("uk/")
        )

    modules = list(quality.get("modules") or [])
    scored_count = len(modules)
    unscored_unknown_count = max(0, total_modules - scored_count)
    needs_upgrade = [m for m in modules if float(m.get("score") or 0.0) < target]
    needs_upgrade.sort(key=lambda m: (float(m.get("score") or 0.0), str(m.get("module") or "")))

    by_track: dict[str, list[dict[str, Any]]] = {}
    severity_counts: dict[str, int] = {}
    for module in needs_upgrade:
        track = str(module.get("track") or "Unknown")
        by_track.setdefault(track, []).append(module)
        sev = str(module.get("severity") or "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    track_groups = [
        {
            "track": track,
            "count": len(items),
            "average_score": round(sum(float(i.get("score") or 0.0) for i in items) / len(items), 2),
            "modules": items,
        }
        for track, items in sorted(
            by_track.items(),
            key=lambda kv: (
                min(float(i.get("score") or 0.0) for i in kv[1]),
                kv[0].lower(),
            ),
        )
    ]

    epic_issue = 181 if target >= 5.0 else 180
    return {
        "exists": bool(quality.get("exists")),
        "source": quality.get("source"),
        "target": target,
        "epic_issue": epic_issue,
        "epic_issue_url": f"https://github.com/kube-dojo/kube-dojo.github.io/issues/{epic_issue}",
        "scored_count": scored_count,
        "total_repo_modules": total_modules,
        "unscored_unknown_count": unscored_unknown_count,
        "coverage_pct": round(100.0 * scored_count / total_modules, 1) if total_modules else 0.0,
        "needs_upgrade_count": len(needs_upgrade),
        "severity_counts": severity_counts,
        "tracks": track_groups,
        "top_worst": needs_upgrade[:10],
        "scope_note": (
            "This plan is based on live heuristic scores from current English module content."
        ),
    }


def build_citation_status(repo_root: Path) -> dict[str, Any]:
    """Return deterministic citation coverage for English module files."""
    from check_citations import check_file

    docs_root = repo_root / "src" / "content" / "docs"
    if not docs_root.exists():
        return {
            "exists": False,
            "error": f"docs_root_missing: {docs_root}",
        }

    module_paths = sorted(
        path
        for path in docs_root.glob("**/module-*.md")
        if ".staging." not in path.name and not path.relative_to(docs_root).as_posix().startswith("uk/")
    )
    latest_mtime = max((path.stat().st_mtime for path in module_paths), default=0.0)
    cache_key = str(docs_root.resolve())
    with _CITATION_STATUS_CACHE_LOCK:
        entry = _CITATION_STATUS_CACHE.get(cache_key)
        if entry and entry.get("mtime") == latest_mtime:
            return entry["data"]

    results = [check_file(path) for path in module_paths]
    failing = [item for item in results if not item.get("passes")]
    by_track: dict[str, list[dict[str, Any]]] = {}
    for item in failing:
        rel = Path(item["path"]).relative_to(docs_root).as_posix()
        track = rel.split("/", 1)[0]
        module_key = rel.removesuffix(".md")
        track_item = {
            "module": module_key,
            "issues": item.get("issues") or [],
            "sources_count": item.get("sources_count") or 0,
        }
        by_track.setdefault(track, []).append(track_item)

    track_groups = []
    for track, items in sorted(by_track.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        issue_counts: dict[str, int] = {}
        for item in items:
            for issue in item.get("issues") or []:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        track_groups.append({
            "track": track,
            "count": len(items),
            "issue_counts": issue_counts,
            "modules": items,
        })

    data = {
        "exists": True,
        "total_repo_modules": len(module_paths),
        "passes_count": len(results) - len(failing),
        "failing_count": len(failing),
        "coverage_pct": round(100.0 * (len(results) - len(failing)) / len(results), 1) if results else 0.0,
        "tracks": track_groups,
        "top_missing": failing[:20],
        "scope_note": (
            "Deterministic citation gate: modules need a Sources section, war-story sources, "
            "and traceable citation markers before they count as review-passed."
        ),
    }
    with _CITATION_STATUS_CACHE_LOCK:
        _CITATION_STATUS_CACHE[cache_key] = {"mtime": latest_mtime, "data": data}
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

    # Rubric severity from live quality scores.
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
            source=f"quality_scores:{quality.get('source', 'unknown')}",
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


def build_recent_activity(repo_root: Path) -> dict[str, Any]:
    """Recent operator-relevant activity across git, pipeline, bridge, and watched issue.

    Keeps the payload compact and deterministic so humans and agents can answer
    "what changed recently?" without stitching together git log, queue reads,
    bridge DB tails, and issue-watch files themselves.
    """
    commits = _recent_commits(repo_root, limit=10)

    try:
        pipeline = build_pipeline_events(repo_root, None, None, limit=15)
    except Exception as exc:  # noqa: BLE001
        pipeline = {"error": f"{type(exc).__name__}: {exc}", "events": []}

    pipeline_events = []
    if isinstance(pipeline, dict):
        for event in (pipeline.get("events") or [])[:10]:
            pipeline_events.append(
                {
                    "id": event.get("id"),
                    "type": event.get("type"),
                    "module_key": event.get("module_key"),
                    "at": event.get("at"),
                }
            )

    try:
        bridge = build_bridge_messages(repo_root, None, limit=10)
    except Exception as exc:  # noqa: BLE001
        bridge = {"error": f"{type(exc).__name__}: {exc}", "messages": []}

    bridge_messages = []
    if isinstance(bridge, dict):
        for msg in (bridge.get("messages") or [])[:8]:
            bridge_messages.append(
                {
                    "id": msg.get("id"),
                    "created_at": msg.get("created_at"),
                    "from_agent": msg.get("from_agent"),
                    "to_agent": msg.get("to_agent"),
                    "kind": msg.get("kind"),
                    "task_id": msg.get("task_id"),
                }
            )

    issue = build_issue_watch_state(repo_root, DEFAULT_FEEDBACK_ISSUE)
    watched_issue = None
    if issue:
        watched_issue = {
            "number": issue.get("number") or DEFAULT_FEEDBACK_ISSUE,
            "title": issue.get("title"),
            "state": issue.get("state"),
            "updated_at": issue.get("updated_at") or issue.get("updatedAt"),
            "comments_count": issue.get("comments_count") or len(issue.get("comments") or []),
            "latest_comment_preview": issue.get("latest_comment_preview"),
            "url": issue.get("url") or issue.get("html_url"),
        }

    return {
        "generated_at": time.time(),
        "recent_commits": commits,
        "pipeline_events": pipeline_events,
        "bridge_messages": bridge_messages,
        "watched_issue": watched_issue,
    }


_ACTIVITY_DEFAULT_SINCE_SECONDS = 86400  # 24h
_ACTIVITY_MAX_LIMIT = 500


def _iso_to_epoch(value: Any) -> int | None:
    """Parse an ISO-8601 timestamp to Unix-epoch seconds.

    Accepts the bridge's ``YYYY-MM-DDTHH:MM:SS[.ffffff][Z|+00:00]`` shape.
    Returns ``None`` on unparseable / absent input so the caller can drop
    the item rather than anchoring the feed at epoch-0.
    """
    if not isinstance(value, str) or not value:
        return None
    from datetime import datetime, timezone
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _recent_commits_with_time(
    repo_root: Path,
    *,
    since_seconds: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Like ``_recent_commits`` but each row carries a committer-time ``at``.

    Used by the merged activity feed so commits can be sorted against
    pipeline events and bridge messages on a single axis. ``since_seconds``
    is applied via ``git log --since=@<epoch>`` (inclusive).
    """
    capped = max(1, min(int(limit), 500))
    cmd = ["git", "log", f"-n{capped}", "--pretty=format:%h%x09%ct%x09%s"]
    if since_seconds is not None:
        cmd.insert(2, f"--since=@{int(since_seconds)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    commits: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        sha, ct, subject = parts
        try:
            at = int(ct)
        except ValueError:
            continue
        commits.append({"sha": sha, "at": at, "subject": subject})
    return commits


def build_activity_feed(
    repo_root: Path,
    *,
    since_seconds: int | None = None,
    limit: int = 50,
    now_seconds: int | None = None,
) -> dict[str, Any]:
    """Merged chronological feed: git commits + pipeline v2 events + bridge messages.

    Everything is normalized to one item shape so operators see a single
    timeline. Each source is fetched with a per-source cap of ``4 * limit``
    (min 50) before merging so a quiet source isn't crowded out at the
    merge boundary. Items with an unparseable timestamp are dropped, not
    anchored at 0 — otherwise they'd always rank last in ascending order
    or first in descending, hiding real recent activity.

    Defaults: ``since_seconds`` = now − 24 h, ``limit`` = 50 (max 500).
    """
    now_seconds = now_seconds if now_seconds is not None else int(time.time())
    if since_seconds is None:
        since_seconds = now_seconds - _ACTIVITY_DEFAULT_SINCE_SECONDS
    capped = max(1, min(int(limit), _ACTIVITY_MAX_LIMIT))
    per_source_cap = max(capped * 4, 50)

    items: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {
        "commit": 0,
        "pipeline_event": 0,
        "bridge_message": 0,
    }
    errors: dict[str, str] = {}

    try:
        commits = _recent_commits_with_time(
            repo_root, since_seconds=since_seconds, limit=per_source_cap
        )
    except Exception as exc:  # noqa: BLE001
        commits = []
        errors["commit"] = f"{type(exc).__name__}: {exc}"
    for c in commits:
        items.append({
            "source": "commit",
            "at": c.get("at"),
            "kind": "commit",
            "module_key": None,
            "summary": c.get("subject"),
            "ref": {"sha": c.get("sha")},
        })
        source_counts["commit"] += 1

    # Pipeline events: order by ``at`` DESC (NOT ``id`` DESC). Event
    # rows can be backfilled with an older ``at`` than their ``id`` —
    # ``build_pipeline_events`` uses ``id`` ordering for its own
    # purposes, but using that here would let a high-id/low-at
    # backfill consume a per-source slot and push a genuinely newer
    # event out of the merge candidates. See Codex Phase D review.
    try:
        db_path = repo_root / ".pipeline" / "v2.db"
        if db_path.exists():
            event_rows = _query_sqlite_rows(
                db_path,
                """
                SELECT id, type, module_key, lease_id, at
                FROM events
                WHERE at >= ?
                ORDER BY at DESC
                LIMIT ?
                """,
                (int(since_seconds), int(per_source_cap)),
            )
        else:
            event_rows = []
    except Exception as exc:  # noqa: BLE001
        event_rows = []
        errors["pipeline_event"] = f"{type(exc).__name__}: {exc}"
    for e in event_rows:
        items.append({
            "source": "pipeline_event",
            "at": e.get("at"),
            "kind": e.get("type"),
            "module_key": e.get("module_key"),
            "summary": None,
            "ref": {"event_id": e.get("id"), "lease_id": e.get("lease_id")},
        })
        source_counts["pipeline_event"] += 1

    # Bridge messages: fetch newest-first WITHOUT a SQL ``since`` filter,
    # then filter in Python via ``_iso_to_epoch``. The SQL filter is a
    # lexical string compare against an ISO timestamp column that may
    # contain fractional seconds or ``+00:00`` offsets — a ``...Z``
    # cutoff lexically drops ``...0.500Z`` and ``...+00:00`` rows even
    # when they represent later absolute times. See Codex Phase D review.
    try:
        bridge = build_bridge_messages(repo_root, None, limit=per_source_cap)
    except Exception as exc:  # noqa: BLE001
        bridge = {"messages": []}
        errors["bridge_message"] = f"{type(exc).__name__}: {exc}"
    for m in (bridge.get("messages") or []):
        at = _iso_to_epoch(m.get("timestamp"))
        if at is None or at < since_seconds:
            continue
        items.append({
            "source": "bridge_message",
            "at": at,
            "kind": m.get("message_type"),
            "module_key": None,
            "summary": f"{m.get('from_llm') or '?'}→{m.get('to_llm') or '?'}",
            "ref": {"message_id": m.get("id"), "task_id": m.get("task_id")},
        })
        source_counts["bridge_message"] += 1

    # Drop items with no usable timestamp (would cluster at the top/bottom
    # depending on sort direction and mislead operators).
    items = [it for it in items if isinstance(it.get("at"), (int, float))]
    items.sort(key=lambda it: int(it["at"]), reverse=True)
    items = items[:capped]

    payload: dict[str, Any] = {
        "generated_at": now_seconds,
        "since_seconds": since_seconds,
        "limit": capped,
        "count": len(items),
        "source_counts": source_counts,
        "items": items,
    }
    if errors:
        payload["errors"] = errors
    return payload


# ---- Phase D: per-section track readiness ----

# Pipeline v2's ``jobs.queue_state`` is one of ``pending | leased |
# completed | failed`` (control_plane.py:195-201). It is NOT the same
# vocabulary as the status reducer's ``pending_write | pending_review |
# pending_patch | in_progress | done | dead_letter`` (cli.py:536-560),
# which is derived from a combination of job rows + events. Bucketing
# naïvely off raw ``queue_state`` misclassifies dead-lettered modules
# as in-flight. We reuse the pipeline's own reducer so this endpoint
# stays in lock-step with ``/api/pipeline/v2/status``.
_READINESS_BUCKET_FOR_STATUS: dict[str, str] = {
    "done": "cleared",
    "dead_letter": "dead_letter",
    "in_progress": "in_flight",
    "pending_write": "in_flight",
    "pending_review": "in_flight",
    "pending_patch": "in_flight",
}


def _readiness_bucket_for_status(status: str | None) -> str:
    if not status:
        return "not_yet_enqueued"
    # Unknown statuses default to in_flight so a reducer extension
    # doesn't silently mark new work cleared.
    return _READINESS_BUCKET_FOR_STATUS.get(status, "in_flight")


def _load_v2_module_statuses(repo_root: Path) -> dict[str, str]:
    """Map ``module_key`` → reducer status from ``.pipeline/v2.db``.

    Uses the same ``_module_status`` reducer as
    ``pipeline_v2.cli._build_status_report`` so the readiness grid
    agrees with ``/api/pipeline/v2/status`` row-for-row. Dead-letter
    detection flows through ``_current_dead_letter_rows``.
    """
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return {}
    # Import here so the module-level deferral pattern is preserved.
    # Missing pipeline_v2 degrades to an empty map (same stance as
    # ``build_pipeline_stuck`` around dead-letter rows).
    try:
        from pipeline_v2.cli import (
            _current_dead_letter_rows,
            _module_status,
        )
    except ModuleNotFoundError as exc:
        if exc.name not in {"pipeline_v2", "pipeline_v2.cli"}:
            raise
        return {}

    job_rows = _query_sqlite_rows(
        db_path,
        """
        SELECT module_key, phase, queue_state
        FROM jobs
        WHERE module_key IS NOT NULL
        ORDER BY id ASC
        """,
    )
    event_rows = _query_sqlite_rows(
        db_path,
        """
        SELECT id, module_key, type, payload_json, at
        FROM events
        WHERE module_key IS NOT NULL
        ORDER BY id ASC
        """,
    )

    modules: set[str] = set()
    job_state_by_module: dict[str, dict[str, Any]] = {}
    event_types_by_module: dict[str, set[str]] = {}
    dead_letter_rows: list[dict[str, Any]] = []

    for row in job_rows:
        module_key = str(row.get("module_key") or "")
        if not module_key:
            continue
        phase = str(row.get("phase") or "")
        queue_state = str(row.get("queue_state") or "")
        modules.add(module_key)
        state = job_state_by_module.setdefault(
            module_key,
            {
                "pending_phases": set(),
                "has_leased": False,
                "has_failed": False,
                "has_completed": False,
            },
        )
        if queue_state == "pending":
            state["pending_phases"].add(phase)
        elif queue_state == "leased":
            state["has_leased"] = True
        elif queue_state == "failed":
            state["has_failed"] = True
        elif queue_state == "completed":
            state["has_completed"] = True

    for row in event_rows:
        module_key = str(row.get("module_key") or "")
        if not module_key:
            continue
        event_type = str(row.get("type") or "")
        modules.add(module_key)
        event_types_by_module.setdefault(module_key, set()).add(event_type)
        if event_type in {
            "needs_human_intervention",
            "module_dead_lettered",
            "dead_letter_recovered",
        }:
            dead_letter_rows.append({
                "module_key": module_key,
                "id": int(row.get("id") or 0),
                "type": event_type,
                "payload_json": str(row.get("payload_json") or "{}"),
                "at": int(row.get("at") or 0),
            })

    unresolved_dead_letters = {
        r["module_key"] for r in _current_dead_letter_rows(dead_letter_rows)
    }

    statuses: dict[str, str] = {}
    for module_key in modules:
        status = _module_status(
            job_state_by_module.get(module_key),
            event_types_by_module.get(module_key, set()),
            dead_lettered=module_key in unresolved_dead_letters,
        )
        statuses[module_key] = status
    return statuses


def _section_for_key(module_key: str) -> str:
    """Second path segment of a module key; ``_root`` for top-level modules.

    Examples: ``k8s/cka/module-1.1-foo`` → ``cka``; ``prerequisites/
    module-1.1-foo`` → ``_root``. Keeps top-level tracks from crashing
    the grid while still bucketing them as a real section.
    """
    parts = str(module_key).split("/")
    if len(parts) < 3:
        return "_root"
    return parts[1]


def build_tracks_readiness(repo_root: Path) -> dict[str, Any]:
    """Per-track, per-section readiness grid for the operator dashboard.

    Buckets every English module on disk into one of:
      - ``cleared`` — pipeline v2 latest state is ``done``/``completed``
      - ``in_flight`` — pending_* / leased / running / in_progress
      - ``dead_letter`` — pipeline gave up, needs human triage
      - ``not_yet_enqueued`` — file exists but has no v2 job row

    Readiness % = ``cleared / total``. Tracks come out in the canonical
    ``TRACK_ORDER``; within a track, sections are alphabetical so the
    grid layout is stable across calls.
    """
    docs_root = repo_root / "src" / "content" / "docs"
    from status import TRACK_ORDER, _iter_en_modules, _track_for_key
    pipeline_status = _load_v2_module_statuses(repo_root)

    # track_slug -> section_slug -> counts
    grid: dict[str, dict[str, dict[str, int]]] = {}

    for path in _iter_en_modules(docs_root):
        rel = path.relative_to(docs_root).as_posix()
        module_key = rel[:-3] if rel.endswith(".md") else rel
        track = _track_for_key(module_key)
        section = _section_for_key(module_key)
        bucket = _readiness_bucket_for_status(pipeline_status.get(module_key))
        t = grid.setdefault(track, {})
        s = t.setdefault(
            section,
            {
                "total": 0,
                "cleared": 0,
                "in_flight": 0,
                "dead_letter": 0,
                "not_yet_enqueued": 0,
            },
        )
        s["total"] += 1
        s[bucket] += 1

    track_labels = dict(TRACK_ORDER)
    canonical_order = [slug for slug, _ in TRACK_ORDER]
    # Preserve canonical order; append "other" and any unknown slugs at
    # the tail so a surprise top-level directory isn't swallowed.
    seen = set(canonical_order)
    extras = [t for t in grid if t not in seen]
    track_order = canonical_order + sorted(extras)

    out_tracks: list[dict[str, Any]] = []
    grand: dict[str, int] = {
        "total": 0,
        "cleared": 0,
        "in_flight": 0,
        "dead_letter": 0,
        "not_yet_enqueued": 0,
    }
    for slug in track_order:
        sections_map = grid.get(slug)
        if not sections_map:
            continue
        sections: list[dict[str, Any]] = []
        track_total = 0
        track_cleared = 0
        track_in_flight = 0
        track_dead = 0
        track_notenq = 0
        for section_slug in sorted(sections_map.keys()):
            counts = sections_map[section_slug]
            total = counts["total"]
            cleared = counts["cleared"]
            readiness_pct = round(100.0 * cleared / total, 1) if total else 0.0
            sections.append({
                "slug": section_slug,
                "total": total,
                "cleared": cleared,
                "in_flight": counts["in_flight"],
                "dead_letter": counts["dead_letter"],
                "not_yet_enqueued": counts["not_yet_enqueued"],
                "readiness_pct": readiness_pct,
            })
            track_total += total
            track_cleared += cleared
            track_in_flight += counts["in_flight"]
            track_dead += counts["dead_letter"]
            track_notenq += counts["not_yet_enqueued"]
        out_tracks.append({
            "slug": slug,
            "label": track_labels.get(slug, slug.replace("-", " ").title()),
            "total": track_total,
            "cleared": track_cleared,
            "in_flight": track_in_flight,
            "dead_letter": track_dead,
            "not_yet_enqueued": track_notenq,
            "readiness_pct": round(100.0 * track_cleared / track_total, 1) if track_total else 0.0,
            "sections": sections,
        })
        grand["total"] += track_total
        grand["cleared"] += track_cleared
        grand["in_flight"] += track_in_flight
        grand["dead_letter"] += track_dead
        grand["not_yet_enqueued"] += track_notenq

    grand["readiness_pct"] = (
        round(100.0 * grand["cleared"] / grand["total"], 1) if grand["total"] else 0.0
    )
    return {
        "generated_at": int(time.time()),
        "totals": grand,
        "tracks": out_tracks,
    }


def build_navigation_status(repo_root: Path) -> dict[str, Any]:
    """Detect route/nav surfaces that still require manual inspection.

    Signals:
    - top-level English track directories and whether they have matching UK hubs
    - candidate-stale index pages: any ``index.md`` older than content beneath it
    """
    docs_root = repo_root / "src" / "content" / "docs"
    uk_root = docs_root / "uk"

    top_level_tracks = []
    missing_uk_top_level = []
    for child in sorted(docs_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name in {"uk", "test"}:
            continue
        en_index = child / "index.md"
        uk_index = uk_root / child.name / "index.md"
        module_count = sum(
            1
            for path in child.rglob("*.md")
            if path.name != "index.md"
        )
        item = {
            "slug": child.name,
            "english_index_exists": en_index.exists(),
            "ukrainian_index_exists": uk_index.exists(),
            "module_count": module_count,
        }
        top_level_tracks.append(item)
        if en_index.exists() and not uk_index.exists():
            missing_uk_top_level.append(child.name)

    stale_indexes = []
    for index_path in sorted(docs_root.rglob("index.md")):
        if "/uk/" in index_path.as_posix():
            continue
        try:
            index_mtime = index_path.stat().st_mtime
        except OSError:
            continue
        subtree_files = [
            path
            for path in index_path.parent.rglob("*.md")
            if path != index_path and "/uk/" not in path.as_posix()
        ]
        if not subtree_files:
            continue
        newest_child = max(subtree_files, key=lambda path: path.stat().st_mtime if path.exists() else 0.0)
        try:
            newest_child_mtime = newest_child.stat().st_mtime
        except OSError:
            continue
        if newest_child_mtime <= index_mtime:
            continue
        stale_indexes.append(
            {
                "index": str(index_path.relative_to(repo_root)),
                "newest_child": str(newest_child.relative_to(repo_root)),
                "lag_seconds": int(newest_child_mtime - index_mtime),
            }
        )

    stale_indexes.sort(key=lambda item: item["lag_seconds"], reverse=True)

    return {
        "generated_at": time.time(),
        "top_level_tracks": top_level_tracks,
        "missing_uk_top_level": missing_uk_top_level,
        "candidate_stale_indexes": stale_indexes[:100],
        "candidate_stale_count": len(stale_indexes),
    }


def _parse_site_health_output(output: str) -> dict[str, Any]:
    errors_match = re.search(r"RESULTS:\s+(\d+)\s+errors,\s+(\d+)\s+warnings", output)
    stats_match = re.search(
        r"STATS:\s+(\d+)\s+files,\s+(\d+)\s+modules,\s+(\d+)\s+links checked",
        output,
    )
    errors = int(errors_match.group(1)) if errors_match else None
    warnings = int(errors_match.group(2)) if errors_match else None
    stats = None
    if stats_match:
        stats = {
            "files": int(stats_match.group(1)),
            "modules": int(stats_match.group(2)),
            "links_checked": int(stats_match.group(3)),
        }
    return {
        "errors": errors,
        "warnings": warnings,
        "ok": errors == 0 if errors is not None else None,
        "stats": stats,
    }


def build_delivery_status(repo_root: Path) -> dict[str, Any]:
    """Delivery-facing readiness surface for build + health status.

    Answers the operator question: is the published output roughly current, and
    is the content tree structurally healthy, without requiring manual command
    runs and log parsing.
    """
    docs_root = repo_root / "src" / "content" / "docs"
    dist_root = repo_root / "dist"
    docs_files = [p for p in docs_root.rglob("*.md") if p.is_file()]
    newest_source = max((_path_mtime(p) for p in docs_files), default=0.0)
    dist_files = [p for p in dist_root.rglob("*") if p.is_file()] if dist_root.exists() else []
    newest_dist = max((_path_mtime(p) for p in dist_files), default=0.0)

    build_state = {
        "dist_exists": dist_root.exists(),
        "dist_file_count": len(dist_files),
        "newest_source_mtime": newest_source,
        "newest_dist_mtime": newest_dist,
        "up_to_date": bool(dist_files) and newest_dist >= newest_source,
    }

    health_cmd = [sys.executable, "scripts/check_site_health.py"]
    try:
        result = subprocess.run(
            health_cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        health = _parse_site_health_output(result.stdout)
        health["exit_code"] = result.returncode
        health["summary_line"] = next(
            (line.strip() for line in result.stdout.splitlines() if line.startswith("RESULTS:")),
            None,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        health = {
            "ok": None,
            "errors": None,
            "warnings": None,
            "stats": None,
            "exit_code": None,
            "summary_line": None,
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "generated_at": time.time(),
        "build": build_state,
        "site_health": health,
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
    .review-list {{ list-style: none; margin: 0; padding: 0; }}
    .review-item {{ padding: 10px 0; border-bottom: 1px solid var(--border-subtle); }}
    .review-item:last-child {{ border-bottom: 0; }}
    .review-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
    .review-pill {{ padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; text-transform: uppercase; }}
    .review-pill.verified {{ background: var(--green-muted); color: var(--green); }}
    .review-pill.unverified {{ background: var(--amber-muted); color: var(--amber); }}
    .review-pill.failed {{ background: var(--red-muted); color: var(--red); }}
    .review-pill.none {{ background: rgba(255,255,255,0.06); color: var(--text-dim); }}
    .review-note {{ margin-top: 6px; font-size: 12px; color: var(--text-secondary); }}
    .review-note mark {{ background: var(--amber-muted); color: var(--amber); padding: 0 3px; border-radius: 4px; }}

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

    /* ---- Phase D: Operator panel ---- */
    .op-hero {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      padding: 14px 18px 18px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .op-hero-block {{ min-width: 0; }}
    .op-hero-title {{
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--text-dim); margin-bottom: 6px;
    }}
    .op-hero-list {{
      font-size: 13px; color: var(--text-secondary);
      list-style: none; margin: 0; padding: 0;
    }}
    .op-hero-list li {{
      padding: 4px 0;
      border-bottom: 1px dashed var(--border-subtle);
    }}
    .op-hero-list li:last-child {{ border-bottom: 0; }}
    .op-hero-list .alert {{ color: var(--amber); }}
    .op-hero-list .blocker {{ color: var(--red); }}
    .op-hero-empty {{ color: var(--text-dim); font-style: italic; font-size: 12px; }}

    .op-cols {{
      display: grid; grid-template-columns: repeat(3, 1fr);
      gap: 0;
    }}
    .op-col {{
      border-right: 1px solid var(--border-subtle);
      padding: 14px 18px;
      min-height: 140px;
    }}
    .op-col:last-child {{ border-right: 0; }}
    .op-col-title {{
      font-size: 11px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.06em; margin: 0 0 10px 0;
    }}
    .op-col-title.now {{ color: var(--accent); }}
    .op-col-title.blocked {{ color: var(--red); }}
    .op-col-title.next {{ color: var(--green); }}
    .op-col-list {{ list-style: none; margin: 0; padding: 0; font-size: 13px; }}
    .op-col-list li {{
      padding: 6px 0;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      word-break: break-word;
    }}
    .op-col-list li:last-child {{ border-bottom: 0; }}
    .op-col-list a {{
      color: var(--accent); text-decoration: none;
      font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace;
      font-size: 11px;
    }}
    .op-col-list a:hover {{ text-decoration: underline; }}

    /* Section readiness grid */
    .readiness-wrap {{ padding: 4px 0 0 0; }}
    .readiness-track {{
      border-bottom: 1px solid var(--border-subtle);
      padding: 12px 18px;
    }}
    .readiness-track:last-child {{ border-bottom: 0; }}
    .readiness-track-header {{
      display: flex; justify-content: space-between; align-items: baseline;
      margin-bottom: 8px;
    }}
    .readiness-track-name {{
      font-weight: 600; font-size: 14px;
    }}
    .readiness-track-sub {{
      font-size: 12px; color: var(--text-dim);
      font-variant-numeric: tabular-nums;
    }}
    .readiness-sections {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 8px;
    }}
    .readiness-section {{
      background: var(--surface-1);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 8px 10px;
      font-size: 12px;
    }}
    .readiness-section-head {{
      display: flex; justify-content: space-between;
      font-family: 'SF Mono', 'Fira Code', ui-monospace, monospace;
      font-size: 11px;
      margin-bottom: 6px;
    }}
    .readiness-section-slug {{ color: var(--text); font-weight: 600; }}
    .readiness-section-pct {{
      color: var(--green); font-variant-numeric: tabular-nums;
    }}
    .readiness-section-pct.mid {{ color: var(--amber); }}
    .readiness-section-pct.low {{ color: var(--text-dim); }}
    .readiness-section-bar {{
      height: 4px; border-radius: 2px; background: var(--border);
      overflow: hidden; margin-bottom: 6px;
    }}
    .readiness-section-fill {{
      height: 100%; background: var(--green); transition: width 0.3s;
    }}
    .readiness-section-fill.mid {{ background: var(--amber); }}
    .readiness-section-fill.low {{ background: var(--text-dim); }}
    .readiness-section-counts {{
      display: flex; gap: 8px;
      color: var(--text-dim);
      font-variant-numeric: tabular-nums;
      font-family: 'SF Mono', 'Fira Code', ui-monospace, monospace;
      font-size: 11px;
    }}
    .readiness-section-counts .dead {{ color: var(--red); }}
    .readiness-section-counts .inflight {{ color: var(--amber); }}
    .readiness-section-counts .cleared {{ color: var(--green); }}

    /* Activity feed */
    .activity-feed {{
      list-style: none; margin: 0; padding: 0;
      max-height: 420px; overflow-y: auto;
    }}
    .activity-feed li {{
      display: grid;
      grid-template-columns: 18px 80px 1fr;
      gap: 10px; padding: 8px 18px;
      font-size: 12px;
      border-bottom: 1px solid var(--border-subtle);
      align-items: center;
    }}
    .activity-feed li:last-child {{ border-bottom: 0; }}
    .activity-src {{
      width: 18px; height: 18px; border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: 10px;
    }}
    .activity-src.commit {{ background: var(--accent-muted); color: var(--accent); }}
    .activity-src.pipeline_event {{ background: var(--teal-muted); color: var(--teal); }}
    .activity-src.bridge_message {{ background: var(--amber-muted); color: var(--amber); }}
    .activity-time {{
      font-family: 'SF Mono', 'Fira Code', ui-monospace, monospace;
      color: var(--text-dim); font-size: 11px;
    }}
    .activity-text {{ color: var(--text-secondary); word-break: break-word; min-width: 0; }}
    .activity-text .mod {{ color: var(--accent); }}
    @media (max-width: 900px) {{
      .op-hero {{ grid-template-columns: 1fr; }}
      .op-cols {{ grid-template-columns: 1fr; }}
      .op-col {{ border-right: 0; border-bottom: 1px solid var(--border-subtle); }}
      .op-col:last-child {{ border-bottom: 0; }}
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
              <span class="panel-icon" style="background:var(--accent-muted);color:var(--accent);">O</span>
              Operator
            </div>
            <span class="panel-badge" id="op-badge" style="background:var(--accent-muted);color:var(--accent);">&nbsp;</span>
          </div>
          <div class="op-hero" id="op-hero">
            <div class="op-hero-block">
              <div class="op-hero-title">Alerts</div>
              <div class="op-hero-empty">Loading&hellip;</div>
            </div>
            <div class="op-hero-block">
              <div class="op-hero-title">Focus</div>
              <div class="op-hero-empty">Loading&hellip;</div>
            </div>
          </div>
          <div class="op-cols">
            <div class="op-col">
              <h4 class="op-col-title now">Now</h4>
              <ul class="op-col-list" id="op-now"><li class="op-hero-empty">Loading&hellip;</li></ul>
            </div>
            <div class="op-col">
              <h4 class="op-col-title blocked">Blocked</h4>
              <ul class="op-col-list" id="op-blocked"><li class="op-hero-empty">Loading&hellip;</li></ul>
            </div>
            <div class="op-col">
              <h4 class="op-col-title next">Next</h4>
              <ul class="op-col-list" id="op-next"><li class="op-hero-empty">Loading&hellip;</li></ul>
            </div>
          </div>
        </div>
      </div>

      <div class="section-full">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-icon" style="background:var(--teal-muted);color:var(--teal);">R</span>
              Section Readiness
            </div>
            <span class="panel-badge" id="readiness-badge" style="background:var(--teal-muted);color:var(--teal);">&nbsp;</span>
          </div>
          <div class="panel-body-flush readiness-wrap" id="readiness-body">
            <div class="empty-state">Loading&hellip;</div>
          </div>
        </div>
      </div>

      <div class="section-full">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <span class="panel-icon" style="background:var(--amber-muted);color:var(--amber);">A</span>
              Activity (last 24 h)
            </div>
            <span class="panel-badge" id="activity-badge" style="background:var(--amber-muted);color:var(--amber);">&nbsp;</span>
          </div>
          <div class="panel-body-flush" id="activity-body">
            <div class="empty-state">Loading&hellip;</div>
          </div>
        </div>
      </div>

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
            <span class="panel-icon" style="background:var(--amber-muted);color:var(--amber);">R</span>
            Review Audit
          </div>
          <span class="panel-badge" id="reviews-badge"></span>
        </div>
        <div class="panel-body" id="reviews"></div>
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

    function renderReviews(data) {{
      const el = $('#reviews');
      const badge = $('#reviews-badge');
      if (!data || data.error) {{
        badge.textContent = 'Unknown';
        el.innerHTML = `<div class="empty-state">${{esc(data?.error || 'No data')}}</div>`;
        return;
      }}
      const rows = (data.reviews || []).slice(0, 8);
      const unverified = rows.filter(r => r.fact_check_status === 'unverified').length;
      badge.textContent = unverified ? `${{unverified}} unverified` : `${{data.count || 0}} reviews`;
      badge.style.background = unverified ? 'var(--amber-muted)' : 'var(--green-muted)';
      badge.style.color = unverified ? 'var(--amber)' : 'var(--green)';
      el.innerHTML = rows.length ? `<ul class="review-list">${{rows.map(r => `
        <li class="review-item">
          <div class="review-head">
            <span class="mono">${{esc(shortenKey(r.module_key))}}</span>
            <span class="review-pill ${{esc(r.fact_check_status || 'none')}}">${{esc(r.fact_check_status || 'none')}}</span>
          </div>
          ${{r.unverified_evidence?.[0] ? `<div class="review-note"><mark>${{esc(r.unverified_evidence[0])}}</mark></div>` : ''}}
        </li>`).join('')}}</ul>` : '<div class="empty-state">No review audit files</div>';
    }}

    // ---- Phase D: Operator / Readiness / Activity ----

    function renderOperator(briefing) {{
      const alerts = briefing?.alerts || [];
      const focus = briefing?.focus || [];
      const blockers = briefing?.blockers || [];

      // Hero: alerts + focus (blockers appended to alerts visually).
      const alertItems = [
        ...blockers.map(s => `<li class="blocker">${{esc(s)}}</li>`),
        ...alerts.map(s => `<li class="alert">${{esc(s)}}</li>`),
      ];
      const focusItems = focus.map(s => `<li>${{esc(s)}}</li>`);
      $('#op-hero').innerHTML = `
        <div class="op-hero-block">
          <div class="op-hero-title">Alerts &amp; Blockers</div>
          ${{alertItems.length
            ? `<ul class="op-hero-list">${{alertItems.join('')}}</ul>`
            : '<div class="op-hero-empty">None</div>'}}
        </div>
        <div class="op-hero-block">
          <div class="op-hero-title">Focus</div>
          ${{focusItems.length
            ? `<ul class="op-hero-list">${{focusItems.join('')}}</ul>`
            : '<div class="op-hero-empty">None</div>'}}
        </div>`;

      // Prefer the structured ``action_rows[]`` — each row carries its
      // own bucket + endpoint + reason, so we don't have to reverse-
      // parse the display string. Fall back to the ``actions.active`` /
      // ``actions.blocked`` / ``actions.next`` string arrays for older
      // briefings that don't have the new field.
      const rowsSrc = Array.isArray(briefing?.action_rows) && briefing.action_rows.length
        ? briefing.action_rows
        : (() => {{
            const bag = [];
            for (const bucket of ['active', 'blocked', 'next']) {{
              for (const label of (briefing?.actions?.[bucket] || [])) {{
                bag.push({{bucket, label, module_key: null, phase: null, reason: null, endpoint: null}});
              }}
            }}
            return bag;
          }})();

      const renderRow = (r) => {{
        const label = esc(r.label || '');
        const link = r.endpoint
          ? ` <a href="${{esc(r.endpoint)}}" title="${{esc(r.endpoint)}}" target="_blank" rel="noopener">[drill]</a>`
          : '';
        return `<li>${{label}}${{link}}</li>`;
      }};
      const renderCol = (bucket) => {{
        const rows = rowsSrc.filter(r => r.bucket === bucket);
        return rows.length
          ? rows.map(renderRow).join('')
          : '<li class="op-hero-empty">Nothing here</li>';
      }};

      $('#op-now').innerHTML = renderCol('active');
      $('#op-blocked').innerHTML = renderCol('blocked');
      $('#op-next').innerHTML = renderCol('next');

      const counts = {{active: 0, blocked: 0, next: 0}};
      for (const r of rowsSrc) {{
        if (counts[r.bucket] !== undefined) counts[r.bucket]++;
      }}
      const total = counts.active + counts.blocked + counts.next;
      const badge = $('#op-badge');
      badge.textContent = total ? `${{total}} items` : 'Idle';
      if (counts.blocked) {{
        badge.style.background = 'var(--red-muted)';
        badge.style.color = 'var(--red)';
      }} else if (total) {{
        badge.style.background = 'var(--accent-muted)';
        badge.style.color = 'var(--accent)';
      }} else {{
        badge.style.background = 'var(--green-muted)';
        badge.style.color = 'var(--green)';
      }}
    }}

    function readinessClass(pct) {{
      if (pct >= 80) return '';
      if (pct >= 40) return 'mid';
      return 'low';
    }}

    function renderReadiness(data) {{
      const el = $('#readiness-body');
      const badge = $('#readiness-badge');
      if (!data || data.error) {{
        el.innerHTML = `<div class="empty-state">${{esc(data?.error || 'No data')}}</div>`;
        badge.textContent = 'Unknown';
        return;
      }}
      const tracks = data.tracks || [];
      const totals = data.totals || {{}};
      const pct = totals.readiness_pct ?? 0;
      badge.textContent = `${{totals.cleared ?? 0}} / ${{totals.total ?? 0}} cleared · ${{pct}}%`;
      if (tracks.length === 0) {{
        el.innerHTML = '<div class="empty-state">No modules on disk</div>';
        return;
      }}
      el.innerHTML = tracks.map(t => {{
        const sections = (t.sections || []).map(s => {{
          const scls = readinessClass(s.readiness_pct ?? 0);
          const parts = [
            `<span class="cleared">${{s.cleared ?? 0}}✓</span>`,
            (s.in_flight ? `<span class="inflight">${{s.in_flight}}↻</span>` : ''),
            (s.dead_letter ? `<span class="dead">${{s.dead_letter}}✗</span>` : ''),
            (s.not_yet_enqueued ? `<span>${{s.not_yet_enqueued}}·</span>` : ''),
          ].filter(Boolean).join(' ');
          return `<div class="readiness-section">
            <div class="readiness-section-head">
              <span class="readiness-section-slug">${{esc(s.slug)}}</span>
              <span class="readiness-section-pct ${{scls}}">${{s.readiness_pct}}%</span>
            </div>
            <div class="readiness-section-bar">
              <div class="readiness-section-fill ${{scls}}" style="width:${{s.readiness_pct}}%"></div>
            </div>
            <div class="readiness-section-counts">${{parts}} <span>/ ${{s.total}}</span></div>
          </div>`;
        }}).join('');
        return `<div class="readiness-track">
          <div class="readiness-track-header">
            <span class="readiness-track-name">${{esc(t.label)}}</span>
            <span class="readiness-track-sub">${{t.cleared ?? 0}} / ${{t.total ?? 0}} · ${{t.readiness_pct ?? 0}}%</span>
          </div>
          <div class="readiness-sections">${{sections}}</div>
        </div>`;
      }}).join('');
    }}

    function formatRelTime(epoch, nowEpoch) {{
      const dt = Math.max(0, nowEpoch - epoch);
      if (dt < 60) return `${{dt}}s`;
      if (dt < 3600) return `${{Math.floor(dt/60)}}m`;
      if (dt < 86400) return `${{Math.floor(dt/3600)}}h`;
      return `${{Math.floor(dt/86400)}}d`;
    }}

    function renderActivity(data) {{
      const el = $('#activity-body');
      const badge = $('#activity-badge');
      if (!data || data.error) {{
        el.innerHTML = `<div class="empty-state">${{esc(data?.error || 'No data')}}</div>`;
        badge.textContent = 'Unknown';
        return;
      }}
      const items = (data.items || []).slice(0, 60);
      const counts = data.source_counts || {{}};
      const parts = [];
      if (counts.commit) parts.push(`${{counts.commit}} commits`);
      if (counts.pipeline_event) parts.push(`${{counts.pipeline_event}} events`);
      if (counts.bridge_message) parts.push(`${{counts.bridge_message}} msgs`);
      badge.textContent = parts.length ? parts.join(' · ') : 'Quiet';
      if (items.length === 0) {{
        el.innerHTML = '<div class="empty-state">No recent activity</div>';
        return;
      }}
      const now = data.generated_at || Math.floor(Date.now() / 1000);
      const srcAbbrev = {{commit: 'C', pipeline_event: 'P', bridge_message: 'B'}};
      const rows = items.map(it => {{
        const srcCls = String(it.source || '');
        const abbr = srcAbbrev[srcCls] || '?';
        const t = formatRelTime(it.at, now);
        let desc;
        if (it.source === 'commit') {{
          desc = `<span class="mono">${{esc(it.ref?.sha || '')}}</span> ${{esc(it.summary || '')}}`;
        }} else if (it.source === 'pipeline_event') {{
          const modPart = it.module_key
            ? `<span class="mod mono">${{esc(shortenKey(it.module_key))}}</span> `
            : '';
          desc = `${{modPart}}${{esc(it.kind || '')}}`;
        }} else {{
          desc = `${{esc(it.summary || '')}} <span class="mono" style="color:var(--text-dim)">${{esc(it.kind || '')}}</span>`;
        }}
        return `<li>
          <span class="activity-src ${{srcCls}}">${{abbr}}</span>
          <span class="activity-time">${{t}} ago</span>
          <span class="activity-text">${{desc}}</span>
        </li>`;
      }}).join('');
      el.innerHTML = `<ul class="activity-feed">${{rows}}</ul>`;
    }}

    let refreshing = false;
    async function refresh() {{
      if (refreshing) return;
      refreshing = true;
      const btn = $('#refresh');
      btn.classList.add('loading');

      try {{
        const [summary, missing, services, worktree, feedback, reviews, v2Status, transStatus,
               briefing, readiness, activity] = await Promise.all([
          fetchJson('/api/status/summary'),
          fetchJson('/api/missing-modules/status'),
          fetchJson('/api/runtime/services'),
          fetchJson('/api/git/worktree'),
          fetchJson(`/api/issue-watch/${{ISSUE}}`),
          fetchJson('/api/reviews'),
          fetchJson('/api/pipeline/v2/status'),
          fetchJson('/api/translation/v2/status'),
          fetchJson('/api/briefing/session?compact=1'),
          fetchJson('/api/tracks/readiness'),
          fetchJson('/api/activity?limit=60'),
        ]);

        summary.missing_modules = missing;
        summary.runtime_services = services;

        const t2Queue = transStatus.queue || transStatus;
        renderOperator(briefing);
        renderReadiness(readiness);
        renderActivity(activity);
        renderMetrics(summary, worktree, feedback, t2Queue);
        renderServices(services);
        renderSiteTracks(summary, v2Status, t2Queue);
        renderPipelinePanel('#v2-body', '#v2-badge', v2Status, 'V2 Pipeline');
        renderPipelinePanel('#trans-body', '#trans-badge', t2Queue, 'Translation V2');
        renderWorktree(worktree);
        renderMissing(missing);
        renderReviews(reviews);
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
    """Return pipeline v2 summary. None if DB absent; error dict if broken.

    Shape map from ``pipeline_v2.cli._build_status_report``:
      - ``counts``: {pending_review, pending_write, pending_patch,
                     in_progress, dead_letter, done}
      - ``needs_human_count``: dead-letter count after resolution
      - ``total_modules``, ``convergence_rate``, ``flapping_count``

    ``queue_head`` collapses those into actionable buckets callers can
    promote into briefing actions:
      - ``ready`` = pending_review + pending_write + pending_patch
      - ``in_progress`` = ``counts.in_progress``
      - ``dead_letter`` = ``counts.dead_letter`` (a.k.a. needs-human)
    """
    db_path = repo_root / ".pipeline" / "v2.db"
    if not db_path.exists():
        return None
    try:
        from pipeline_v2.cli import _build_status_report as build_v2_status_report
        report = build_v2_status_report(db_path)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(report, dict):
        return {"error": "non_dict_report"}

    counts = report.get("counts") or {}
    ready = sum(
        int(counts.get(k, 0))
        for k in ("pending_review", "pending_write", "pending_patch")
    )
    queue_head = {
        "ready": ready,
        "in_progress": int(counts.get("in_progress", 0)),
        "dead_letter": int(counts.get("dead_letter", 0)),
    }
    # Briefing is a cold-start hot path; keep the payload compact.
    # Full ``counts`` / ``convergence_rate`` live on
    # /api/pipeline/v2/status; here we expose only the actionable
    # summary an agent needs before deciding what to do.
    return {
        "total_modules": report.get("total_modules"),
        "needs_human_count": report.get("needs_human_count"),
        "queue_head": queue_head,
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
        dead_letter_stuck = stuck.get("dead_lettered_count", 0)
        stale_worker_count = stuck.get("stale_workers_count", 0)
        if leased:
            alerts.append(f"{leased} job(s) with expired/stale lease — worker may have crashed")
        if in_state:
            alerts.append(f"{in_state} job(s) stuck in-flight with no recent event")
        if dead_letter_stuck:
            alerts.append(
                f"{dead_letter_stuck} module(s) dead-lettered (unresolved) — need human triage"
            )
        if stale_worker_count:
            alerts.append(
                f"{stale_worker_count} worker(s) holding leases but silent — possible zombie"
            )

    try:
        quality = build_quality_scores(repo_root)
    except Exception:  # noqa: BLE001
        quality = None
    try:
        reviews = build_reviews_index(repo_root, fact_check_status="unverified")
    except Exception:  # noqa: BLE001
        reviews = None
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
    if isinstance(reviews, dict) and reviews.get("count"):
        alerts.append(f"{reviews['count']} module(s) with unverified fact claims")

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
    # Structured row shape per ``action_rows[]``:
    #   ``{bucket, label, module_key, phase, reason, endpoint}``
    # The dashboard reads this directly. Agents that want the old flat
    # list view still get ``actions.{active,blocked,next}`` (derived
    # from ``action_rows`` below) plus ``top_modules[]``, both preserved
    # for backward compat.
    action_rows: list[dict[str, Any]] = []
    top_modules: list[dict[str, Any]] = []

    def _add_row(
        bucket: str,
        label: str,
        *,
        module_key: str | None = None,
        phase: str | None = None,
        reason: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        action_rows.append({
            "bucket": bucket,
            "label": label,
            "module_key": module_key,
            "phase": phase,
            "reason": reason,
            "endpoint": endpoint,
        })
        # ``top_modules[]`` keeps its historical shape (module_key may
        # be None for repo-level rows like ``ready_queue``).
        if reason and endpoint:
            top_modules.append({
                "module_key": module_key,
                "phase": phase,
                "reason": reason,
                "endpoint": endpoint,
            })

    try:
        leases = build_pipeline_leases(repo_root)
    except Exception:  # noqa: BLE001
        leases = None
    if isinstance(leases, dict) and leases.get("exists"):
        for lease in (leases.get("active") or [])[:5]:
            secs = lease.get("seconds_to_expiry")
            mk = lease.get("module_key")
            _add_row(
                "active",
                f"{lease.get('leased_by','?')} → {mk or '?'} "
                f"({lease.get('phase','?')}, {secs}s left)",
                module_key=mk,
                phase=lease.get("phase"),
                reason="active_lease",
                endpoint=f"/api/module/{mk}/state" if mk else None,
            )

    if isinstance(stuck, dict) and stuck.get("exists"):
        for job in (stuck.get("stuck_leased") or [])[:5]:
            mk = job.get("module_key")
            _add_row(
                "blocked",
                f"{mk or '?'} stale lease (held by {job.get('leased_by','?')})",
                module_key=mk,
                phase=job.get("phase"),
                reason="stale_lease",
                endpoint=f"/api/pipeline/v2/events?module={mk}" if mk else None,
            )
        for job in (stuck.get("stuck_in_state") or [])[:5]:
            mk = job.get("module_key")
            _add_row(
                "blocked",
                f"{mk or '?'} stuck in {job.get('queue_state','?')}",
                module_key=mk,
                phase=job.get("phase"),
                reason="stuck_in_state",
                endpoint=f"/api/pipeline/v2/events?module={mk}" if mk else None,
            )

    if isinstance(quality, dict) and quality.get("exists"):
        for m in (quality.get("critical") or [])[:5]:
            # Rubric rows don't carry a real ``module_key`` (the
            # audit uses human-readable labels), so we store the
            # label itself as the key and point at /api/quality/
            # scores for drill-down. Agents can cross-reference.
            _add_row(
                "next",
                f"rubric-critical rewrite: {m.get('module','?')} "
                f"({m.get('track','?')}) score {m.get('score','?')}",
                module_key=m.get("module"),
                reason="critical_quality",
                endpoint="/api/quality/scores",
            )
    if isinstance(reviews, dict) and reviews.get("exists"):
        for review in (reviews.get("reviews") or [])[:5]:
            mk = review.get("module_key")
            _add_row(
                "blocked",
                f"{mk or '?'} has unverified fact claim",
                module_key=mk,
                reason="fact_check_unverified",
                endpoint=f"/api/reviews?module={mk}" if mk else None,
            )

    if isinstance(pipeline, dict) and pipeline.get("queue_head"):
        queue_head = pipeline["queue_head"] or {}
        ready = int(queue_head.get("ready") or 0)
        if ready:
            _add_row(
                "next",
                f"{ready} job(s) ready to pick up in pipeline v2",
                reason="ready_queue",
                endpoint="/api/pipeline/v2/status",
            )
        dead_letter = int(queue_head.get("dead_letter") or 0)
        if dead_letter:
            _add_row(
                "blocked",
                f"{dead_letter} job(s) in dead-letter — needs human or re-enqueue",
                reason="pipeline_dead_letter",
                endpoint="/api/pipeline/v2/stuck",
            )

    actions_active = [r["label"] for r in action_rows if r["bucket"] == "active"]
    actions_blocked = [r["label"] for r in action_rows if r["bucket"] == "blocked"]
    actions_next = [r["label"] for r in action_rows if r["bucket"] == "next"]

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
        # Structured twin of ``actions.*``. Each row has {bucket,
        # label, module_key, phase, reason, endpoint}. Dashboards and
        # UI consumers read this directly — scanning ``label`` strings
        # to infer drill-down endpoints is fragile and misroutes when
        # the same module appears in multiple buckets (Codex Phase D
        # review round 3).
        "action_rows": action_rows,
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
            {"path": "/api/activity/recent", "desc": "Recent commits, pipeline events, bridge messages, watched issue (grouped by source)"},
            {
                "path": "/api/activity",
                "desc": "Merged chronological feed (commits + pipeline events + bridge messages), newest-first",
                "query": [
                    "since=<Unix-epoch seconds | ISO-8601> (default: 24 h ago)",
                    "limit=... (default 50, max 500)",
                ],
            },
            {"path": "/api/navigation/status", "desc": "Top-level route coverage and candidate-stale index pages"},
            {"path": "/api/delivery/status", "desc": "Build freshness and site-health status"},
            {
                "path": "/api/tracks/readiness",
                "desc": "Per-track, per-section production-readiness grid (cleared/in_flight/dead_letter/not_yet_enqueued)",
            },
            {"path": "/api/runtime/services", "desc": "Runtime services (pids, uptime, ports)"},
            {"path": "/api/build/run", "desc": "Spawn `npm run build` in the background", "method": "POST"},
            {"path": "/api/build/status", "desc": "Build job status + tail + warning diff", "query": ["job_id=..."]},
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
            {
                "path": "/api/gh/issues",
                "desc": "Cached GitHub issue list for agent orientation",
                "query": ["state=open|closed|all (default open)", "limit=... (default 50, max 200)"],
            },
            {
                "path": "/api/gh/issues/{n}",
                "desc": "Single GitHub issue with the last 5 comments",
            },
            {
                "path": "/api/gh/prs",
                "desc": "Cached GitHub pull request list for agent orientation",
                "query": ["state=open|closed|merged|all (default open)", "limit=... (default 50, max 200)"],
            },
            {
                "path": "/api/gh/prs/{n}",
                "desc": "Single GitHub pull request with the last 5 comments and mergeable state",
            },
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
                "desc": "Stuck/stalled jobs + dead-lettered modules + zombie-worker roll-up (stale_workers[])",
                "query": ["threshold_seconds=... (default 3600)"],
            },
            {
                "path": "/api/reviews",
                "desc": "Review audit index (omit query) or single-module log (?module=...)",
                "query": ["module=...", "fact_check_status=verified|unverified|failed|none"],
            },
            {
                "path": "/api/bridge/messages",
                "desc": ".bridge/messages.db tail",
                "query": ["since=<ISO-8601>", "limit=... (max 500)"],
            },
            {"path": "/api/quality/scores", "desc": "Live heuristic rubric scores from current English module files"},
            {
                "path": "/api/quality/upgrade-plan",
                "desc": "Upgrade queue derived from rubric scores for #180 (4/5) or #181 (5/5)",
                "query": ["target=4.0|5.0"],
            },
            {"path": "/api/citations/status", "desc": "Citation gate coverage and missing-source queue by track/module"},
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
    if path == "/api/activity/recent":
        return 200, build_recent_activity(repo_root), "application/json; charset=utf-8"
    if path == "/api/activity":
        since_raw = query.get("since", [None])[0]
        since_seconds: int | None = None
        if since_raw:
            try:
                # Accept epoch seconds...
                since_seconds = int(since_raw)
            except (TypeError, ValueError):
                # ...or an ISO-8601 timestamp.
                since_seconds = _iso_to_epoch(since_raw)
                if since_seconds is None:
                    return 400, {"error": "invalid_since"}, "application/json; charset=utf-8"
        try:
            limit = int(query.get("limit", ["50"])[0])
        except (TypeError, ValueError):
            limit = 50
        return (
            200,
            build_activity_feed(repo_root, since_seconds=since_seconds, limit=limit),
            "application/json; charset=utf-8",
        )
    if path == "/api/navigation/status":
        return 200, build_navigation_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/delivery/status":
        return 200, build_delivery_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/tracks/readiness":
        return 200, build_tracks_readiness(repo_root), "application/json; charset=utf-8"
    if path == "/api/runtime/services":
        return 200, build_runtime_services_status(repo_root), "application/json; charset=utf-8"
    if path == "/api/build/status":
        job_id = query.get("job_id", [None])[0]
        if not job_id:
            return 400, {"error": "missing_job_id"}, "application/json; charset=utf-8"
        return get_build_job_status(repo_root, job_id)
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
    if path == "/api/gh/issues":
        state = query.get("state", ["open"])[0] or "open"
        if state not in {"open", "closed", "all"}:
            state = "open"
        try:
            limit = int(query.get("limit", ["50"])[0])
        except (TypeError, ValueError):
            limit = 50
        return _build_gh_list("issue", state, max(1, min(limit, 200)))
    if path.startswith("/api/gh/issues/"):
        try:
            number = int(path.split("/")[-1])
        except ValueError:
            return 400, {"error": "invalid_issue_number"}, "application/json; charset=utf-8"
        return _build_gh_detail("issue", number)
    if path == "/api/gh/prs":
        state = query.get("state", ["open"])[0] or "open"
        if state not in {"open", "closed", "merged", "all"}:
            state = "open"
        try:
            limit = int(query.get("limit", ["50"])[0])
        except (TypeError, ValueError):
            limit = 50
        return _build_gh_list("pr", state, max(1, min(limit, 200)))
    if path.startswith("/api/gh/prs/"):
        try:
            number = int(path.split("/")[-1])
        except ValueError:
            return 400, {"error": "invalid_pr_number"}, "application/json; charset=utf-8"
        return _build_gh_detail("pr", number)
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
        fact_check_status = query.get("fact_check_status", [None])[0]
        if fact_check_status and fact_check_status not in _VALID_FACT_CHECK_STATUSES:
            return 400, {"error": "invalid_fact_check_status"}, "application/json; charset=utf-8"
        mk = query.get("module", [None])[0]
        if mk:
            module_key = _validate_module_key(repo_root, mk)
            if module_key is None:
                return 400, {"error": "invalid_module_key"}, "application/json; charset=utf-8"
            payload = build_module_reviews(repo_root, module_key)
            if payload is None:
                return 404, {"error": "review_not_found", "module_key": module_key}, "application/json; charset=utf-8"
            return 200, payload, "application/json; charset=utf-8"
        return 200, build_reviews_index(repo_root, fact_check_status=fact_check_status), "application/json; charset=utf-8"
    if path == "/api/bridge/messages":
        since = query.get("since", [None])[0]
        try:
            limit = int(query.get("limit", ["100"])[0])
        except (TypeError, ValueError):
            limit = 100
        return 200, build_bridge_messages(repo_root, since, limit), "application/json; charset=utf-8"
    if path == "/api/quality/scores":
        return 200, build_quality_scores(repo_root), "application/json; charset=utf-8"
    if path == "/api/quality/upgrade-plan":
        try:
            target = float(query.get("target", ["4.0"])[0])
        except (TypeError, ValueError):
            return 400, {"error": "invalid_target"}, "application/json; charset=utf-8"
        if target <= 0:
            return 400, {"error": "invalid_target"}, "application/json; charset=utf-8"
        return 200, build_quality_upgrade_plan(repo_root, target=target), "application/json; charset=utf-8"
    if path == "/api/citations/status":
        return 200, build_citation_status(repo_root), "application/json; charset=utf-8"
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


def route_post_request(repo_root: Path, raw_path: str) -> tuple[int, Any, str]:
    path = urlsplit(raw_path).path.rstrip("/") or "/"
    if path == "/api/build/run":
        return start_build_job(repo_root)
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
    "/api/activity/recent": (5.0, _v_v2_db),
    "/api/navigation/status": (30.0, None),
    "/api/delivery/status": (30.0, None),
    "/api/runtime/services": (2.0, None),
    "/api/pipeline/v2/status": (5.0, _v_v2_db),
    "/api/translation/v2/status": (5.0, _v_translation_db),
    "/api/labs/status": (10.0, None),
    "/api/quality/upgrade-plan": (30.0, None),
    "/api/citations/status": (30.0, None),
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

    if _is_gh_path(path):
        cache_key = _normalized_cache_key(path, query, repo_root=repo_root)

        def _build() -> tuple[int, Any, str]:
            return route_request(repo_root, raw_path)

        return cached_response(
            cache_key,
            GH_CACHE_TTL_SECONDS,
            lambda: ("gh",),
            _build,
            lambda payload, _body: _gh_payload_etag(path, payload),
        )

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

            try:
                self.send_response(status_code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                if 200 <= status_code < 300:
                    self.send_header("ETag", etag)
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                # Client disconnected mid-response. Swallowing keeps the
                # worker thread alive; the server itself is unaffected.
                return

        def do_POST(self) -> None:  # noqa: N802
            try:
                status_code, payload, content_type = route_post_request(repo_root, self.path)
            except Exception as exc:  # noqa: BLE001 - surface all write failures as JSON
                status_code = 500
                payload = {
                    "error": "internal_error",
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "path": self.path,
                }
                content_type = "application/json; charset=utf-8"

            body = _serialize_payload(payload, content_type)
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve(repo_root: Path, host: str, port: int) -> None:
    ThreadingHTTPServer.daemon_threads = True
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((host, port), make_handler(repo_root))
    print(json.dumps({"repo_root": str(repo_root), "host": host, "port": port}, sort_keys=True))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    finally:
        server.server_close()


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

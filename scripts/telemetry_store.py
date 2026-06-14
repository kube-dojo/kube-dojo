"""SQLite persistence for KubeDojo telemetry (#1973).

- Module-build token telemetry in ``.pipeline/telemetry/module_builds.db``
- Tool-timing telemetry in ``.pipeline/telemetry/tool_timings.db``
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

_db_path_override: Path | None = None
_tool_timings_db_path_override: Path | None = None

_TOOL_TIMING_WINDOWS = {
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}


def db_path(repo_root: Path) -> Path:
    if _db_path_override is not None:
        return _db_path_override
    return repo_root / ".pipeline" / "telemetry" / "module_builds.db"


def tool_timings_db_path(repo_root: Path) -> Path:
    if _tool_timings_db_path_override is not None:
        return _tool_timings_db_path_override
    return repo_root / ".pipeline" / "telemetry" / "tool_timings.db"


def _isoformat_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _now_z() -> str:
    return _isoformat_z(datetime.now(UTC))


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _required_text(value: str | None, field: str) -> str:
    cleaned = _clean_text(value)
    if cleaned is None:
        raise ValueError(f"{field} must not be blank")
    return cleaned


def _parse_recorded_at(value: str | None) -> str:
    if value is None:
        return _now_z()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return _now_z()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return _isoformat_z(datetime.fromisoformat(text))
        except ValueError as exc:
            raise ValueError("recorded_at must be a valid ISO-8601 timestamp") from exc
    raise ValueError("recorded_at must be a valid ISO-8601 timestamp")


def _computed_total_tokens(participant: dict[str, Any]) -> int | None:
    total = participant.get("total_tokens")
    if total is not None:
        return int(total)
    prompt = participant.get("prompt_tokens")
    response = participant.get("response_tokens")
    if prompt is None and response is None:
        return None
    return int(prompt or 0) + int(response or 0)


def _connect(db_file: Path) -> sqlite3.Connection:
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS module_build_runs (
            run_id             TEXT PRIMARY KEY,
            created_at         TEXT NOT NULL,
            updated_at         TEXT NOT NULL,
            track              TEXT NOT NULL,
            slug               TEXT NOT NULL,
            module_title       TEXT,
            branch             TEXT,
            commit_sha         TEXT,
            pr_number          INTEGER,
            pr_url             TEXT,
            status             TEXT NOT NULL DEFAULT 'recorded',
            swarm_used         INTEGER NOT NULL,
            swarm_label        TEXT NOT NULL DEFAULT 'none',
            swarm_note         TEXT NOT NULL,
            wall_clock_minutes REAL,
            source             TEXT NOT NULL,
            notes              TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_mbr_track_slug
            ON module_build_runs(track, slug, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_mbr_updated
            ON module_build_runs(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_mbr_swarm
            ON module_build_runs(swarm_used, updated_at DESC);

        CREATE TABLE IF NOT EXISTS module_build_participants (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id          TEXT NOT NULL,
            role            TEXT NOT NULL,
            agent           TEXT NOT NULL,
            model           TEXT,
            effort          TEXT,
            label           TEXT,
            calls           INTEGER,
            prompt_tokens   INTEGER,
            response_tokens INTEGER,
            total_tokens    INTEGER,
            token_source    TEXT NOT NULL DEFAULT 'unavailable',
            cost_usd_est    REAL,
            notes           TEXT,
            FOREIGN KEY(run_id) REFERENCES module_build_runs(run_id)
                ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_mbp_run
            ON module_build_participants(run_id, id);
        """
    )


def _participant_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "role": row["role"],
        "agent": row["agent"],
        "model": row["model"],
        "effort": row["effort"],
        "label": row["label"],
        "calls": row["calls"],
        "prompt_tokens": row["prompt_tokens"],
        "response_tokens": row["response_tokens"],
        "total_tokens": row["total_tokens"],
        "token_source": row["token_source"],
        "cost_usd_est": row["cost_usd_est"],
        "notes": row["notes"],
    }


def participant_totals(participants: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = sum(int(item["prompt_tokens"] or 0) for item in participants)
    response = sum(int(item["response_tokens"] or 0) for item in participants)
    total = sum(int(item["total_tokens"] or 0) for item in participants)
    cost = sum(float(item["cost_usd_est"] or 0.0) for item in participants)
    return {
        "participants": len(participants),
        "prompt_tokens": prompt,
        "response_tokens": response,
        "total_tokens": total,
        "cost_usd_est": round(cost, 6),
    }


def rollup(runs: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = sum(int(run["totals"]["prompt_tokens"]) for run in runs)
    response = sum(int(run["totals"]["response_tokens"]) for run in runs)
    total = sum(int(run["totals"]["total_tokens"]) for run in runs)
    participants = sum(int(run["totals"]["participants"]) for run in runs)
    cost = sum(float(run["totals"]["cost_usd_est"]) for run in runs)
    swarm_runs = sum(1 for run in runs if run["swarm_used"])
    return {
        "runs": len(runs),
        "swarm_runs": swarm_runs,
        "solo_runs": len(runs) - swarm_runs,
        "participants": participants,
        "prompt_tokens": prompt,
        "response_tokens": response,
        "total_tokens": total,
        "cost_usd_est": round(cost, 6),
    }


def _run_row_to_dict(row: sqlite3.Row, participants: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "track": row["track"],
        "slug": row["slug"],
        "module_title": row["module_title"],
        "branch": row["branch"],
        "commit_sha": row["commit_sha"],
        "pr_number": row["pr_number"],
        "pr_url": row["pr_url"],
        "status": row["status"],
        "swarm_used": bool(row["swarm_used"]),
        "swarm_label": row["swarm_label"],
        "swarm_note": row["swarm_note"],
        "wall_clock_minutes": row["wall_clock_minutes"],
        "source": row["source"],
        "notes": row["notes"],
        "participants": participants,
        "totals": participant_totals(participants),
    }


def _load_participants(conn: sqlite3.Connection, run_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not run_ids:
        return {}
    placeholders = ",".join("?" for _ in run_ids)
    rows = conn.execute(
        f"""
        SELECT run_id, role, agent, model, effort, label, calls, prompt_tokens,
               response_tokens, total_tokens, token_source, cost_usd_est, notes
        FROM module_build_participants
        WHERE run_id IN ({placeholders})
        ORDER BY run_id, id
        """,
        run_ids,
    ).fetchall()
    participants: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        participants[str(row["run_id"])].append(_participant_row_to_dict(row))
    return participants


def _normalize_participant(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": _required_text(raw.get("role"), "participant.role"),
        "agent": _required_text(raw.get("agent"), "participant.agent"),
        "model": _clean_text(raw.get("model")),
        "effort": _clean_text(raw.get("effort")),
        "label": _clean_text(raw.get("label")),
        "calls": raw.get("calls"),
        "prompt_tokens": raw.get("prompt_tokens"),
        "response_tokens": raw.get("response_tokens"),
        "total_tokens": _computed_total_tokens(raw),
        "token_source": _required_text(raw.get("token_source") or "unavailable", "participant.token_source"),
        "cost_usd_est": raw.get("cost_usd_est"),
        "notes": _clean_text(raw.get("notes")),
    }


def validate_module_build_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate ingest JSON; raises ValueError with a field-specific message."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    run_id = _required_text(payload.get("run_id") or f"mbt-{uuid4().hex}", "run_id")
    track = _required_text(payload.get("track"), "track")
    slug = _required_text(payload.get("slug"), "slug")
    status = _required_text(payload.get("status") or "recorded", "status")
    swarm_label = _clean_text(payload.get("swarm_label")) or "none"
    swarm_note = _required_text(payload.get("swarm_note"), "swarm_note")
    source = _required_text(payload.get("source"), "source")

    if "swarm_used" not in payload:
        raise ValueError("swarm_used is required")

    participants_raw = payload.get("participants") or []
    if not isinstance(participants_raw, list):
        raise ValueError("participants must be a list")

    return {
        "run_id": run_id,
        "created_at": _parse_recorded_at(payload.get("recorded_at")),
        "updated_at": _now_z(),
        "track": track,
        "slug": slug,
        "module_title": _clean_text(payload.get("module_title")),
        "branch": _clean_text(payload.get("branch")),
        "commit_sha": _clean_text(payload.get("commit_sha")),
        "pr_number": payload.get("pr_number"),
        "pr_url": _clean_text(payload.get("pr_url")),
        "status": status,
        "swarm_used": bool(payload["swarm_used"]),
        "swarm_label": swarm_label,
        "swarm_note": swarm_note,
        "wall_clock_minutes": payload.get("wall_clock_minutes"),
        "source": source,
        "notes": _clean_text(payload.get("notes")),
        "participants": [_normalize_participant(item) for item in participants_raw],
    }


def upsert_run(repo_root: Path, payload: dict[str, Any]) -> str:
    """Validate and upsert a module-build run; returns run_id."""
    validated = validate_module_build_ingest(payload)
    run_id = validated["run_id"]
    participant_rows = [
        (
            run_id,
            participant["role"],
            participant["agent"],
            participant["model"],
            participant["effort"],
            participant["label"],
            participant["calls"],
            participant["prompt_tokens"],
            participant["response_tokens"],
            participant["total_tokens"],
            participant["token_source"],
            participant["cost_usd_est"],
            participant["notes"],
        )
        for participant in validated["participants"]
    ]

    db_file = db_path(repo_root)
    with closing(_connect(db_file)) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO module_build_runs (
                run_id, created_at, updated_at, track, slug, module_title,
                branch, commit_sha, pr_number, pr_url, status, swarm_used,
                swarm_label, swarm_note, wall_clock_minutes, source, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                created_at = module_build_runs.created_at,
                updated_at = excluded.updated_at,
                track = excluded.track,
                slug = excluded.slug,
                module_title = excluded.module_title,
                branch = excluded.branch,
                commit_sha = excluded.commit_sha,
                pr_number = excluded.pr_number,
                pr_url = excluded.pr_url,
                status = excluded.status,
                swarm_used = excluded.swarm_used,
                swarm_label = excluded.swarm_label,
                swarm_note = excluded.swarm_note,
                wall_clock_minutes = excluded.wall_clock_minutes,
                source = excluded.source,
                notes = excluded.notes
            """,
            (
                run_id,
                validated["created_at"],
                validated["updated_at"],
                validated["track"],
                validated["slug"],
                validated["module_title"],
                validated["branch"],
                validated["commit_sha"],
                validated["pr_number"],
                validated["pr_url"],
                validated["status"],
                1 if validated["swarm_used"] else 0,
                validated["swarm_label"],
                validated["swarm_note"],
                validated["wall_clock_minutes"],
                validated["source"],
                validated["notes"],
            ),
        )
        conn.execute("DELETE FROM module_build_participants WHERE run_id = ?", (run_id,))
        if participant_rows:
            conn.executemany(
                """
                INSERT INTO module_build_participants (
                    run_id, role, agent, model, effort, label, calls, prompt_tokens,
                    response_tokens, total_tokens, token_source, cost_usd_est, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                participant_rows,
            )
        conn.commit()
    return run_id


def query_runs(
    repo_root: Path,
    *,
    track: str | None = None,
    slug: str | None = None,
    swarm_used: bool | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if track:
        conditions.append("track = ?")
        params.append(track.strip())
    if slug:
        conditions.append("slug = ?")
        params.append(slug.strip())
    if swarm_used is not None:
        conditions.append("swarm_used = ?")
        params.append(1 if swarm_used else 0)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(max(1, min(int(limit), 500)))

    db_file = db_path(repo_root)
    with closing(_connect(db_file)) as conn:
        _ensure_schema(conn)
        rows = conn.execute(
            f"""
            SELECT *
            FROM module_build_runs
            {where}
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        run_ids = [str(row["run_id"]) for row in rows]
        participants = _load_participants(conn, run_ids)

    return [_run_row_to_dict(row, participants.get(str(row["run_id"]), [])) for row in rows]


def build_module_build_payload(
    repo_root: Path,
    *,
    track: str | None = None,
    slug: str | None = None,
    swarm_used: bool | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    runs = query_runs(
        repo_root,
        track=track,
        slug=slug,
        swarm_used=swarm_used,
        limit=limit,
    )
    return {
        "generated_at": _now_z(),
        "records_total": len(runs),
        "totals": rollup(runs),
        "runs": runs,
    }


def build_module_build_detail_payload(
    repo_root: Path,
    *,
    track: str,
    slug: str,
    limit: int = 20,
) -> dict[str, Any]:
    payload = build_module_build_payload(
        repo_root,
        track=track.strip(),
        slug=slug.strip(),
        swarm_used=None,
        limit=limit,
    )
    return {
        "generated_at": payload["generated_at"],
        "track": track.strip(),
        "slug": slug.strip(),
        "records_total": payload["records_total"],
        "totals": payload["totals"],
        "latest": payload["runs"][0] if payload["runs"] else None,
        "runs": payload["runs"],
    }


# ---------------------------------------------------------------------------
# Tool-timing telemetry (#1973 P2)
# ---------------------------------------------------------------------------


def _ensure_tool_timings_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tool_timings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            tool_name   TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            tool_use_id TEXT,
            session_id  TEXT,
            failed      INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_tt_ts ON tool_timings(ts);
        CREATE INDEX IF NOT EXISTS idx_tt_name_ts ON tool_timings(tool_name, ts);
        """
    )


def _percentile_ms(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = (len(sorted_values) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = rank - lower
    return round(sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction)


def _tool_timing_window_start(window: str) -> tuple[str, str]:
    delta = _TOOL_TIMING_WINDOWS.get(window)
    if delta is None:
        window = "1h"
        delta = _TOOL_TIMING_WINDOWS[window]
    return window, _isoformat_z(datetime.now(UTC) - delta)


def validate_tool_timing_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    tool_name = _required_text(payload.get("tool_name"), "tool_name")
    duration_ms = payload.get("duration_ms")
    if duration_ms is None:
        raise ValueError("duration_ms is required")
    try:
        duration_val = int(duration_ms)
    except (TypeError, ValueError) as exc:
        raise ValueError("duration_ms must be a non-negative integer") from exc
    if duration_val < 0:
        raise ValueError("duration_ms must be a non-negative integer")

    return {
        "ts": _parse_recorded_at(payload.get("ts")),
        "tool_name": tool_name,
        "duration_ms": duration_val,
        "tool_use_id": _clean_text(payload.get("tool_use_id")),
        "session_id": _clean_text(payload.get("session_id")),
        "failed": 1 if payload.get("failed") else 0,
    }


def ingest_tool_timing(repo_root: Path, record: dict[str, Any]) -> None:
    validated = validate_tool_timing_ingest(record)
    db_file = tool_timings_db_path(repo_root)
    with closing(_connect(db_file)) as conn:
        _ensure_tool_timings_schema(conn)
        conn.execute(
            """
            INSERT INTO tool_timings (ts, tool_name, duration_ms, tool_use_id, session_id, failed)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                validated["ts"],
                validated["tool_name"],
                validated["duration_ms"],
                validated["tool_use_id"],
                validated["session_id"],
                validated["failed"],
            ),
        )
        conn.commit()


def tool_timing_summary(
    repo_root: Path,
    *,
    window: str = "1h",
    tool: str | None = None,
) -> list[dict[str, Any]]:
    window, window_start = _tool_timing_window_start(window)
    conditions = ["ts >= ?"]
    params: list[Any] = [window_start]
    if tool:
        conditions.append("tool_name = ?")
        params.append(tool.strip())

    where = " AND ".join(conditions)
    db_file = tool_timings_db_path(repo_root)
    with closing(_connect(db_file)) as conn:
        _ensure_tool_timings_schema(conn)
        rows = conn.execute(
            f"""
            SELECT tool_name, duration_ms, failed
            FROM tool_timings
            WHERE {where}
            ORDER BY tool_name, duration_ms
            """,
            params,
        ).fetchall()

    durations: dict[str, list[int]] = defaultdict(list)
    failures: dict[str, int] = defaultdict(int)
    for row in rows:
        tool_name = str(row["tool_name"])
        durations[tool_name].append(int(row["duration_ms"]))
        failures[tool_name] += int(row["failed"])

    results: list[dict[str, Any]] = []
    for tool_name, values in durations.items():
        count = len(values)
        results.append(
            {
                "tool_name": tool_name,
                "count": count,
                "p50_ms": _percentile_ms(values, 0.50),
                "p95_ms": _percentile_ms(values, 0.95),
                "p99_ms": _percentile_ms(values, 0.99),
                "mean_ms": round(sum(values) / count),
                "failure_count": failures[tool_name],
            }
        )

    return sorted(results, key=lambda item: (-item["count"], item["tool_name"]))


def build_tool_timing_payload(
    repo_root: Path,
    *,
    window: str = "1h",
    tool: str | None = None,
) -> dict[str, Any]:
    window, _ = _tool_timing_window_start(window)
    tools = tool_timing_summary(repo_root, window=window, tool=tool)
    return {
        "generated_at": _now_z(),
        "window": window,
        "tools": tools,
    }

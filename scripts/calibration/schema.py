"""SQLite schema and small persistence helpers for calibration v1."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from .models import CalibrationModel

DEFAULT_DOMAIN = "kubedojo"
DEFAULT_FIXTURE_VERSION = "v1"
DEFAULT_LEDGER_VERSION = "v1"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cells (
  cell_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  lane TEXT NOT NULL,
  fixture_id TEXT NOT NULL,
  fixture_version TEXT NOT NULL,
  family TEXT NOT NULL,
  provider_cli TEXT NOT NULL,
  model_id TEXT NOT NULL,
  version TEXT NOT NULL,
  canonical_string TEXT NOT NULL,
  effort_requested TEXT NOT NULL,
  effort_mechanism TEXT NOT NULL,
  effort_confidence TEXT NOT NULL,
  effort_effective TEXT,
  run_date TEXT NOT NULL,
  as_of_date TEXT NOT NULL,
  ledger_version TEXT NOT NULL DEFAULT 'v1',
  created_at TEXT NOT NULL,
  UNIQUE (
    domain,
    lane,
    fixture_id,
    fixture_version,
    family,
    provider_cli,
    model_id,
    version,
    effort_requested,
    run_date
  )
);

CREATE TABLE IF NOT EXISTS dispatches (
  dispatch_id INTEGER PRIMARY KEY AUTOINCREMENT,
  cell_id TEXT NOT NULL REFERENCES cells(cell_id) ON DELETE CASCADE,
  task_id TEXT NOT NULL,
  dispatch_ts TEXT NOT NULL,
  response_path TEXT NOT NULL,
  cwd TEXT,
  tool_uses TEXT,
  latency_s REAL,
  cost_usd REAL,
  returncode INTEGER,
  stderr_excerpt TEXT,
  UNIQUE (cell_id, task_id)
);

CREATE TABLE IF NOT EXISTS scores (
  cell_id TEXT NOT NULL REFERENCES cells(cell_id) ON DELETE CASCADE,
  gate_name TEXT NOT NULL,
  gate_pass INTEGER NOT NULL CHECK (gate_pass IN (0, 1)),
  score_value REAL,
  scorer TEXT NOT NULL,
  replicate_seq INTEGER NOT NULL DEFAULT 0,
  stderr_excerpt TEXT,
  gate_failure_reason TEXT,
  scored_at TEXT NOT NULL,
  PRIMARY KEY (cell_id, gate_name, scorer)
);

CREATE TABLE IF NOT EXISTS production_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  family TEXT NOT NULL,
  provider_cli TEXT NOT NULL,
  model_id TEXT NOT NULL,
  version TEXT NOT NULL,
  effort_requested TEXT NOT NULL,
  event_type TEXT NOT NULL,
  pr_number INTEGER,
  occurred_at TEXT NOT NULL,
  evidence_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_cells_lane ON cells (lane);
CREATE INDEX IF NOT EXISTS idx_cells_canonical ON cells (canonical_string);
CREATE INDEX IF NOT EXISTS idx_cells_family ON cells (family);
CREATE INDEX IF NOT EXISTS idx_cells_run_date ON cells (run_date);
CREATE INDEX IF NOT EXISTS idx_scores_cell ON scores (cell_id);
"""


def today_iso() -> str:
    return date.today().isoformat()


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def make_cell_id(
    *,
    lane: str,
    fixture_id: str,
    canonical_string: str,
    effort_requested: str,
    run_date: str,
) -> str:
    return f"{lane}-{fixture_id}-{canonical_string}@{effort_requested}-{run_date}"


def connect(db_path: Path | str) -> sqlite3.Connection:
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str) -> None:
    with connect(db_path) as conn:
        # WAL mode lets parallel score_cell workers commit concurrently. Without
        # it, -P > 1 scoring hits ~70% `database is locked` failures during
        # judge dispatch — see session-36 handoff. journal_mode is persistent,
        # so this is a one-shot on first init; re-applies are no-ops.
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA_SQL)
        _ensure_columns(
            conn,
            "dispatches",
            {
                "cwd": "TEXT",
                "tool_uses": "TEXT",
            },
        )
        _ensure_columns(
            conn,
            "scores",
            {
                "replicate_seq": "INTEGER NOT NULL DEFAULT 0",
                "stderr_excerpt": "TEXT",
                "gate_failure_reason": "TEXT",
            },
        )


def _ensure_columns(
    conn: sqlite3.Connection,
    table: str,
    columns: dict[str, str],
) -> None:
    existing = {
        str(row["name"])
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    for name, sql_type in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")


def _scorer_for_replicate(scorer: str, replicate_seq: int) -> str:
    if replicate_seq <= 0 or f":replicate-{replicate_seq}" in scorer:
        return scorer
    return f"{scorer}:replicate-{replicate_seq}"


def build_cell_row(
    *,
    lane: str,
    fixture_id: str,
    model: CalibrationModel,
    run_date: str,
    domain: str = DEFAULT_DOMAIN,
    fixture_version: str = DEFAULT_FIXTURE_VERSION,
    as_of_date: str | None = None,
    ledger_version: str = DEFAULT_LEDGER_VERSION,
    effort_effective: str | None = None,
) -> dict[str, Any]:
    model_row = asdict(model)
    cell_id = make_cell_id(
        lane=lane,
        fixture_id=fixture_id,
        canonical_string=model.canonical_string,
        effort_requested=model.effort_requested,
        run_date=run_date,
    )
    return {
        "cell_id": cell_id,
        "domain": domain,
        "lane": lane,
        "fixture_id": fixture_id,
        "fixture_version": fixture_version,
        "family": model_row["family"],
        "provider_cli": model_row["provider_cli"],
        "model_id": model_row["model_id"],
        "version": model_row["version"],
        "canonical_string": model_row["canonical_string"],
        "effort_requested": model_row["effort_requested"],
        "effort_mechanism": model_row["effort_mechanism"],
        "effort_confidence": model_row["effort_confidence"],
        "effort_effective": effort_effective,
        "run_date": run_date,
        "as_of_date": as_of_date or run_date,
        "ledger_version": ledger_version,
        "created_at": utc_now_iso(),
    }


def insert_cell(conn: sqlite3.Connection, row: dict[str, Any]) -> str:
    columns = (
        "cell_id",
        "domain",
        "lane",
        "fixture_id",
        "fixture_version",
        "family",
        "provider_cli",
        "model_id",
        "version",
        "canonical_string",
        "effort_requested",
        "effort_mechanism",
        "effort_confidence",
        "effort_effective",
        "run_date",
        "as_of_date",
        "ledger_version",
        "created_at",
    )
    placeholders = ", ".join(f":{column}" for column in columns)
    updates = ", ".join(
        f"{column}=excluded.{column}"
        for column in columns
        if column not in {"cell_id", "created_at"}
    )
    conn.execute(
        f"""
        INSERT INTO cells ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(cell_id) DO UPDATE SET {updates}
        """,
        row,
    )
    return str(row["cell_id"])


def insert_dispatch(
    conn: sqlite3.Connection,
    *,
    cell_id: str,
    task_id: str,
    response_path: str,
    cwd: str | None = None,
    tool_uses: object | None = None,
    latency_s: float | None = None,
    cost_usd: float | None = None,
    returncode: int | None = None,
    stderr_excerpt: str | None = None,
    dispatch_ts: str | None = None,
) -> None:
    if isinstance(tool_uses, str) or tool_uses is None:
        tool_uses_json = tool_uses
    else:
        tool_uses_json = json.dumps(tool_uses, sort_keys=True)
    conn.execute(
        """
        INSERT INTO dispatches (
          cell_id, task_id, dispatch_ts, response_path, cwd, tool_uses,
          latency_s, cost_usd, returncode, stderr_excerpt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(cell_id, task_id) DO UPDATE SET
          dispatch_ts=excluded.dispatch_ts,
          response_path=excluded.response_path,
          cwd=excluded.cwd,
          tool_uses=excluded.tool_uses,
          latency_s=excluded.latency_s,
          cost_usd=excluded.cost_usd,
          returncode=excluded.returncode,
          stderr_excerpt=excluded.stderr_excerpt
        """,
        (
            cell_id,
            task_id,
            dispatch_ts or utc_now_iso(),
            response_path,
            cwd,
            tool_uses_json,
            latency_s,
            cost_usd,
            returncode,
            stderr_excerpt,
        ),
    )


def insert_score(
    conn: sqlite3.Connection,
    *,
    cell_id: str,
    gate_name: str,
    gate_pass: bool,
    score_value: float | None = None,
    scorer: str = "deterministic",
    replicate_seq: int = 0,
    stderr_excerpt: str | None = None,
    gate_failure_reason: str | None = None,
    scored_at: str | None = None,
) -> None:
    scorer = _scorer_for_replicate(scorer, replicate_seq)
    conn.execute(
        """
        INSERT INTO scores (
          cell_id, gate_name, gate_pass, score_value, scorer, stderr_excerpt,
          gate_failure_reason, replicate_seq, scored_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(cell_id, gate_name, scorer) DO UPDATE SET
          gate_pass=excluded.gate_pass,
          score_value=excluded.score_value,
          stderr_excerpt=excluded.stderr_excerpt,
          gate_failure_reason=excluded.gate_failure_reason,
          replicate_seq=excluded.replicate_seq,
          scored_at=excluded.scored_at
        """,
        (
            cell_id,
            gate_name,
            1 if gate_pass else 0,
            score_value,
            scorer,
            stderr_excerpt,
            gate_failure_reason,
            replicate_seq,
            scored_at or utc_now_iso(),
        ),
    )


def insert_scores(
    conn: sqlite3.Connection,
    *,
    cell_id: str,
    gates: dict[str, bool],
    scorer: str = "deterministic",
    replicate_seq: int = 0,
) -> None:
    for gate_name, gate_pass in gates.items():
        insert_score(
            conn,
            cell_id=cell_id,
            gate_name=gate_name,
            gate_pass=gate_pass,
            score_value=1.0 if gate_pass else 0.0,
            scorer=scorer,
            replicate_seq=replicate_seq,
        )


def fetch_cell(conn: sqlite3.Connection, cell_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM cells WHERE cell_id = ?", (cell_id,)).fetchone()
    if row is None:
        raise KeyError(f"unknown calibration cell: {cell_id}")
    return row


def list_indexes(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index'"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def bulk_insert_scores(
    conn: sqlite3.Connection,
    *,
    cell_id: str,
    rows: Iterable[tuple[str, bool, float | None, str]],
    replicate_seq: int = 0,
) -> None:
    for gate_name, gate_pass, score_value, scorer in rows:
        insert_score(
            conn,
            cell_id=cell_id,
            gate_name=gate_name,
            gate_pass=gate_pass,
            score_value=score_value,
            scorer=scorer,
            replicate_seq=replicate_seq,
        )

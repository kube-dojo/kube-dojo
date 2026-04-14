from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / ".pipeline"
DEFAULT_DB_PATH = PIPELINE_DIR / "v2.db"
DEFAULT_BUDGETS_PATH = PIPELINE_DIR / "budgets.yaml"
DEFAULT_LEASE_SECONDS = 900
SQLITE_NOW_EPOCH = "CAST(strftime('%s','now') AS INTEGER)"
SQLITE_ONE_HOUR_AGO_EPOCH = "CAST(strftime('%s','now','-1 hour') AS INTEGER)"
DEFAULT_KILL_SWITCH_POLICY = "CLAUDE_ONLY_PAUSE"


@dataclass(frozen=True)
class BudgetRule:
    max_concurrent: int = 1
    weekly_calls: int = 100
    hourly_calls: int = 25
    weekly_budget_usd: float | None = None
    cooldown_after_rate_limit: int = 300
    weekly_window: str = "rolling_7d"


@dataclass(frozen=True)
class BudgetConfig:
    defaults: BudgetRule
    models: dict[str, BudgetRule]
    kill_switch_policy: str = DEFAULT_KILL_SWITCH_POLICY

    def for_model(self, model: str) -> BudgetRule:
        return self.models.get(model, self.defaults)


@dataclass(frozen=True)
class Job:
    job_id: int
    module_key: str
    phase: str
    model: str
    priority: int
    queue_state: str
    idempotency_key: str
    requested_calls: int
    estimated_usd: float


@dataclass(frozen=True)
class Lease:
    lease_id: str
    job_id: int
    module_key: str
    phase: str
    model: str
    worker_id: str
    requested_calls: int
    estimated_usd: float
    idempotency_key: str
    expires_at: int


@dataclass(frozen=True)
class BudgetRow:
    model: str
    max_concurrent: int
    active_leases: int
    hourly_calls_cap: int | None
    hourly_calls_committed: int
    weekly_calls_cap: int | None
    weekly_calls_committed: int
    weekly_budget_usd_cap: float | None
    weekly_budget_usd_committed: float


class BudgetStore:
    """Reloadable budgets config with last-good fallback."""

    def __init__(self, path: Path):
        self.path = path
        self._last_good: BudgetConfig | None = None
        self.last_error: str | None = None

    def load(self) -> BudgetConfig:
        try:
            raw = {}
            if self.path.exists():
                raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
            config = _parse_budget_config(raw)
        except Exception as exc:
            if self._last_good is None:
                raise
            self.last_error = str(exc)
            return self._last_good

        self._last_good = config
        self.last_error = None
        return config

    def set_value(self, model: str, field: str, value: Any) -> None:
        raw: dict[str, Any]
        if self.path.exists():
            raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        else:
            raw = {}
        models = raw.setdefault("models", {})
        model_cfg = models.setdefault(model, {})
        model_cfg[field] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(raw, sort_keys=True),
            encoding="utf-8",
        )
        self.load()


def _parse_budget_config(raw: dict[str, Any]) -> BudgetConfig:
    defaults_raw = raw.get("defaults") or {}
    defaults = _budget_rule_from_mapping(defaults_raw)
    models_raw = raw.get("models") or {}
    models = {
        str(model): _budget_rule_from_mapping(mapping or {}, defaults)
        for model, mapping in models_raw.items()
    }
    kill_switch_policy = str(
        raw.get(
            "kill_switch_policy",
            defaults_raw.get("kill_switch_policy", DEFAULT_KILL_SWITCH_POLICY),
        )
    ).upper()
    return BudgetConfig(
        defaults=defaults,
        models=models,
        kill_switch_policy=kill_switch_policy,
    )


def _budget_rule_from_mapping(
    raw: dict[str, Any],
    defaults: BudgetRule | None = None,
) -> BudgetRule:
    base = defaults or BudgetRule()
    return BudgetRule(
        max_concurrent=int(raw.get("max_concurrent", base.max_concurrent)),
        weekly_calls=int(raw.get("weekly_calls", base.weekly_calls)),
        hourly_calls=int(raw.get("hourly_calls", base.hourly_calls)),
        weekly_budget_usd=(
            float(raw["weekly_budget_usd"])
            if raw.get("weekly_budget_usd") is not None
            else base.weekly_budget_usd
        ),
        cooldown_after_rate_limit=int(
            raw.get("cooldown_after_rate_limit", base.cooldown_after_rate_limit)
        ),
        weekly_window=str(raw.get("weekly_window", base.weekly_window)),
    )


class ControlPlane:
    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        db_path: Path | None = None,
        budgets_path: Path | None = None,
    ):
        self.repo_root = repo_root or REPO_ROOT
        self.pipeline_dir = self.repo_root / ".pipeline"
        self.db_path = db_path or self.pipeline_dir / "v2.db"
        self.budgets_path = budgets_path or self.pipeline_dir / "budgets.yaml"
        self.pipeline_dir.mkdir(parents=True, exist_ok=True)
        self.budget_store = BudgetStore(self.budgets_path)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_key TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    model TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 100,
                    queue_state TEXT NOT NULL DEFAULT 'pending'
                        CHECK (queue_state IN ('pending', 'leased', 'completed', 'failed')),
                    leased_by TEXT,
                    lease_id TEXT,
                    leased_at INTEGER,
                    lease_expires_at INTEGER,
                    enqueued_at INTEGER NOT NULL DEFAULT ({SQLITE_NOW_EPOCH}),
                    requested_calls INTEGER NOT NULL DEFAULT 1 CHECK (requested_calls > 0),
                    estimated_usd REAL NOT NULL DEFAULT 0 CHECK (estimated_usd >= 0),
                    idempotency_key TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS active_leases (
                    lease_id TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    job_id INTEGER NOT NULL UNIQUE,
                    expires_at INTEGER NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    lease_id TEXT PRIMARY KEY,
                    job_id INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    reserved_calls INTEGER NOT NULL,
                    reserved_usd REAL NOT NULL,
                    reserved_at INTEGER NOT NULL DEFAULT ({SQLITE_NOW_EPOCH}),
                    idempotency_key TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lease_id TEXT NOT NULL,
                    job_id INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    actual_calls INTEGER NOT NULL,
                    actual_usd REAL NOT NULL,
                    tokens_in INTEGER NOT NULL DEFAULT 0,
                    tokens_out INTEGER NOT NULL DEFAULT 0,
                    completed_at INTEGER NOT NULL DEFAULT ({SQLITE_NOW_EPOCH}),
                    idempotency_key TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    module_key TEXT,
                    lease_id TEXT,
                    payload_json TEXT NOT NULL DEFAULT '{{}}',
                    at INTEGER NOT NULL DEFAULT ({SQLITE_NOW_EPOCH})
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_queue
                    ON jobs(queue_state, priority, enqueued_at, id);
                CREATE INDEX IF NOT EXISTS idx_active_leases_model
                    ON active_leases(model, expires_at);
                CREATE INDEX IF NOT EXISTS idx_reservations_model
                    ON reservations(model, reserved_at);
                CREATE INDEX IF NOT EXISTS idx_usage_model
                    ON usage(model, completed_at);
                CREATE INDEX IF NOT EXISTS idx_events_type
                    ON events(type, at);
                """
            )
            conn.commit()
        finally:
            conn.close()

    def enqueue(
        self,
        module_key: str,
        *,
        phase: str,
        model: str,
        priority: int = 100,
        requested_calls: int = 1,
        estimated_usd: float = 0.0,
    ) -> Job:
        idempotency_key = uuid.uuid4().hex
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                """
                INSERT INTO jobs (
                    module_key, phase, model, priority, queue_state,
                    requested_calls, estimated_usd, idempotency_key
                ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (
                    module_key,
                    phase,
                    model,
                    priority,
                    requested_calls,
                    estimated_usd,
                    idempotency_key,
                ),
            )
            job_id = int(cursor.lastrowid)
            _record_event(
                conn,
                "job_enqueued",
                module_key=module_key,
                payload={
                    "job_id": job_id,
                    "phase": phase,
                    "model": model,
                    "priority": priority,
                    "requested_calls": requested_calls,
                    "estimated_usd": estimated_usd,
                    "idempotency_key": idempotency_key,
                },
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return Job(
            job_id=job_id,
            module_key=module_key,
            phase=phase,
            model=model,
            priority=priority,
            queue_state="pending",
            idempotency_key=idempotency_key,
            requested_calls=requested_calls,
            estimated_usd=estimated_usd,
        )

    def lease_next_job(
        self,
        worker_id: str,
        *,
        model: str | None = None,
        requested_calls: int | None = None,
        estimated_usd: float | None = None,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> Lease | None:
        config = self.budget_store.load()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if self.budget_store.last_error:
                _record_event(
                    conn,
                    "config_reload_failed",
                    payload={"error": self.budget_store.last_error},
                )

            params: list[Any] = []
            model_clause = ""
            if model:
                model_clause = "AND model = ?"
                params.append(model)
            candidate = conn.execute(
                f"""
                SELECT *
                FROM jobs
                WHERE queue_state = 'pending'
                {model_clause}
                ORDER BY priority ASC, enqueued_at ASC, id ASC
                LIMIT 1
                """,
                params,
            ).fetchone()
            if candidate is None:
                conn.commit()
                return None

            job_id = int(candidate["id"])
            chosen_model = str(candidate["model"])
            rule = config.for_model(chosen_model)
            requested = requested_calls or int(candidate["requested_calls"])
            estimated_cost_usd = (
                float(estimated_usd)
                if estimated_usd is not None
                else float(candidate["estimated_usd"])
            )
            reserved_usd = estimated_cost_usd * 1.20

            paused, pause_context = self._is_pipeline_paused(conn, chosen_model, config)
            if paused:
                _record_event(
                    conn,
                    "dispatch_blocked_budget",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "job_id": job_id,
                        "model": chosen_model,
                        "reason": "pipeline_paused",
                        "policy": pause_context["policy"],
                        "exhausted_models": pause_context["exhausted_models"],
                    },
                )
                conn.commit()
                return None

            cooldown = conn.execute(
                f"""
                SELECT
                    MAX(at) AS last_rate_limited_at,
                    {SQLITE_NOW_EPOCH} AS now_at
                FROM events
                WHERE type = 'attempt_rate_limited'
                  AND payload_json LIKE ?
                """,
                (f'%"model"%{json.dumps(chosen_model)}%',),
            ).fetchone()
            last_rate_limited_at = cooldown["last_rate_limited_at"]
            if (
                last_rate_limited_at is not None
                and int(last_rate_limited_at) + rule.cooldown_after_rate_limit
                > int(cooldown["now_at"])
            ):
                _record_event(
                    conn,
                    "model_cooldown_active",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "job_id": job_id,
                        "model": chosen_model,
                        "last_rate_limited_at": int(last_rate_limited_at),
                        "cooldown_seconds": rule.cooldown_after_rate_limit,
                        "cooldown_until": int(last_rate_limited_at)
                        + rule.cooldown_after_rate_limit,
                    },
                )
                conn.commit()
                return None

            active_leases = int(
                conn.execute(
                    f"""
                    SELECT COUNT(*) AS count
                    FROM active_leases
                    WHERE model = ?
                      AND expires_at > {SQLITE_NOW_EPOCH}
                    """,
                    (chosen_model,),
                ).fetchone()["count"]
            )
            if rule.max_concurrent <= 0 or active_leases >= rule.max_concurrent:
                _record_event(
                    conn,
                    "dispatch_blocked_budget",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "job_id": job_id,
                        "model": chosen_model,
                        "reason": "max_concurrent",
                        "max_concurrent": rule.max_concurrent,
                        "active_leases": active_leases,
                    },
                )
                conn.commit()
                return None

            committed = _committed_budget(conn, chosen_model, rule.weekly_window)
            if committed["hourly_calls"] + requested > rule.hourly_calls:
                _record_event(
                    conn,
                    "dispatch_blocked_budget",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "job_id": job_id,
                        "model": chosen_model,
                        "reason": "hourly_calls",
                        "requested_calls": requested,
                        "hourly_calls_cap": rule.hourly_calls,
                        "hourly_calls_committed": committed["hourly_calls"],
                    },
                )
                conn.commit()
                return None

            if committed["weekly_calls"] + requested > rule.weekly_calls:
                _record_event(
                    conn,
                    "dispatch_blocked_budget",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "job_id": job_id,
                        "model": chosen_model,
                        "reason": "weekly_calls",
                        "requested_calls": requested,
                        "weekly_calls_cap": rule.weekly_calls,
                        "weekly_calls_committed": committed["weekly_calls"],
                        "policy": config.kill_switch_policy,
                    },
                )
                _record_event(
                    conn,
                    "kill_switch_triggered",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "model": chosen_model,
                        "reason": "weekly_calls",
                        "policy": config.kill_switch_policy,
                    },
                )
                conn.commit()
                return None

            if (
                rule.weekly_budget_usd is not None
                and committed["weekly_budget_usd"] + reserved_usd > rule.weekly_budget_usd
            ):
                _record_event(
                    conn,
                    "dispatch_blocked_budget",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "job_id": job_id,
                        "model": chosen_model,
                        "reason": "weekly_budget_usd",
                        "estimated_usd": reserved_usd,
                        "weekly_budget_usd_cap": rule.weekly_budget_usd,
                        "weekly_budget_usd_committed": committed["weekly_budget_usd"],
                        "policy": config.kill_switch_policy,
                    },
                )
                _record_event(
                    conn,
                    "kill_switch_triggered",
                    module_key=str(candidate["module_key"]),
                    payload={
                        "model": chosen_model,
                        "reason": "weekly_budget_usd",
                        "policy": config.kill_switch_policy,
                    },
                )
                conn.commit()
                return None

            lease_id = uuid.uuid4().hex
            conn.execute(
                f"""
                UPDATE jobs
                SET queue_state = 'leased',
                    leased_by = ?,
                    lease_id = ?,
                    leased_at = {SQLITE_NOW_EPOCH},
                    lease_expires_at = {SQLITE_NOW_EPOCH} + ?
                WHERE id = ?
                """,
                (worker_id, lease_id, lease_seconds, job_id),
            )
            conn.execute(
                f"""
                INSERT INTO active_leases (lease_id, model, job_id, expires_at, idempotency_key)
                VALUES (?, ?, ?, {SQLITE_NOW_EPOCH} + ?, ?)
                """,
                (
                    lease_id,
                    chosen_model,
                    job_id,
                    lease_seconds,
                    str(candidate["idempotency_key"]),
                ),
            )
            conn.execute(
                """
                INSERT INTO reservations (
                    lease_id, job_id, model, reserved_calls, reserved_usd, idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    lease_id,
                    job_id,
                    chosen_model,
                    requested,
                    reserved_usd,
                    str(candidate["idempotency_key"]),
                ),
            )
            _record_event(
                conn,
                "job_leased",
                module_key=str(candidate["module_key"]),
                lease_id=lease_id,
                payload={
                    "job_id": job_id,
                    "model": chosen_model,
                    "worker_id": worker_id,
                    "requested_calls": requested,
                    "estimated_usd": estimated_cost_usd,
                    "reserved_usd": reserved_usd,
                    "idempotency_key": str(candidate["idempotency_key"]),
                },
            )
            lease_row = conn.execute(
                "SELECT lease_expires_at FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return Lease(
            lease_id=lease_id,
            job_id=job_id,
            module_key=str(candidate["module_key"]),
            phase=str(candidate["phase"]),
            model=chosen_model,
            worker_id=worker_id,
            requested_calls=requested,
            estimated_usd=estimated_cost_usd,
            idempotency_key=str(candidate["idempotency_key"]),
            expires_at=int(lease_row["lease_expires_at"]),
        )

    def record_usage(
        self,
        lease_id: str,
        *,
        actual_calls: int = 1,
        actual_usd: float = 0.0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        outcome: str = "attempt_succeeded",
    ) -> bool:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            job = conn.execute(
                """
                SELECT id, module_key, model, idempotency_key
                FROM jobs
                WHERE lease_id = ?
                """,
                (lease_id,),
            ).fetchone()
            if job is None:
                raise ValueError(f"Unknown lease_id '{lease_id}'")

            inserted = conn.execute(
                """
                INSERT OR IGNORE INTO usage (
                    lease_id, job_id, model, actual_calls, actual_usd,
                    tokens_in, tokens_out, idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lease_id,
                    int(job["id"]),
                    str(job["model"]),
                    actual_calls,
                    actual_usd,
                    tokens_in,
                    tokens_out,
                    str(job["idempotency_key"]),
                ),
            ).rowcount == 1
            conn.execute("DELETE FROM reservations WHERE lease_id = ?", (lease_id,))
            conn.execute("DELETE FROM active_leases WHERE lease_id = ?", (lease_id,))
            conn.execute(
                """
                UPDATE jobs
                SET queue_state = 'completed',
                    leased_by = NULL,
                    leased_at = NULL,
                    lease_expires_at = NULL
                WHERE id = ?
                """,
                (int(job["id"]),),
            )
            _record_event(
                conn,
                outcome,
                module_key=str(job["module_key"]),
                lease_id=lease_id,
                payload={
                    "job_id": int(job["id"]),
                    "actual_calls": actual_calls,
                    "actual_usd": actual_usd,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "usage_deduped": not inserted,
                },
            )
            conn.commit()
            return inserted
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release_lease(self, lease_id: str, *, reason: str) -> bool:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            job = conn.execute(
                """
                SELECT id, module_key
                FROM jobs
                WHERE lease_id = ?
                  AND queue_state = 'leased'
                """,
                (lease_id,),
            ).fetchone()
            if job is None:
                conn.commit()
                return False
            conn.execute("DELETE FROM reservations WHERE lease_id = ?", (lease_id,))
            conn.execute("DELETE FROM active_leases WHERE lease_id = ?", (lease_id,))
            conn.execute(
                """
                UPDATE jobs
                SET queue_state = 'pending',
                    leased_by = NULL,
                    lease_id = NULL,
                    leased_at = NULL,
                    lease_expires_at = NULL
                WHERE id = ?
                """,
                (int(job["id"]),),
            )
            _record_event(
                conn,
                "job_released",
                module_key=str(job["module_key"]),
                lease_id=lease_id,
                payload={"job_id": int(job["id"]), "reason": reason},
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def sweep_once(self) -> int:
        conn = self._connect()
        released = 0
        try:
            conn.execute("BEGIN IMMEDIATE")
            expired = conn.execute(
                f"""
                SELECT al.lease_id, al.job_id, j.module_key, j.idempotency_key,
                       EXISTS(
                           SELECT 1 FROM usage u
                           WHERE u.idempotency_key = j.idempotency_key
                       ) AS has_usage
                FROM active_leases al
                JOIN jobs j ON j.id = al.job_id
                WHERE al.expires_at <= {SQLITE_NOW_EPOCH}
                ORDER BY al.expires_at ASC, al.lease_id ASC
                """
            ).fetchall()
            for row in expired:
                lease_id = str(row["lease_id"])
                job_id = int(row["job_id"])
                conn.execute("DELETE FROM reservations WHERE lease_id = ?", (lease_id,))
                conn.execute("DELETE FROM active_leases WHERE lease_id = ?", (lease_id,))
                if int(row["has_usage"]):
                    conn.execute(
                        """
                        UPDATE jobs
                        SET queue_state = 'completed',
                            leased_by = NULL,
                            leased_at = NULL,
                            lease_expires_at = NULL
                        WHERE id = ?
                        """,
                        (job_id,),
                    )
                    continue
                conn.execute(
                    """
                    UPDATE jobs
                    SET queue_state = 'pending',
                        leased_by = NULL,
                        lease_id = NULL,
                        leased_at = NULL,
                        lease_expires_at = NULL
                    WHERE id = ?
                    """,
                    (job_id,),
                )
                _record_event(
                    conn,
                    "job_released",
                    module_key=str(row["module_key"]),
                    lease_id=lease_id,
                    payload={"job_id": job_id, "reason": "lease_expired"},
                )
                released += 1
            conn.commit()
            return released
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def budget_report(self) -> dict[str, Any]:
        config = self.budget_store.load()
        conn = self._connect()
        try:
            models = {
                *config.models.keys(),
                *[
                    str(row["model"])
                    for row in conn.execute("SELECT DISTINCT model FROM jobs").fetchall()
                ],
            }
            rows = []
            for model in sorted(models):
                rule = config.for_model(model)
                committed = _committed_budget(conn, model, rule.weekly_window)
                active_leases = int(
                    conn.execute(
                        f"""
                        SELECT COUNT(*) AS count
                        FROM active_leases
                        WHERE model = ?
                          AND expires_at > {SQLITE_NOW_EPOCH}
                        """,
                        (model,),
                    ).fetchone()["count"]
                )
                rows.append(
                    BudgetRow(
                        model=model,
                        max_concurrent=rule.max_concurrent,
                        active_leases=active_leases,
                        hourly_calls_cap=rule.hourly_calls,
                        hourly_calls_committed=committed["hourly_calls"],
                        weekly_calls_cap=rule.weekly_calls,
                        weekly_calls_committed=committed["weekly_calls"],
                        weekly_budget_usd_cap=rule.weekly_budget_usd,
                        weekly_budget_usd_committed=committed["weekly_budget_usd"],
                    )
                )
            return {
                "db_path": str(self.db_path),
                "budgets_path": str(self.budgets_path),
                "rows": [asdict(row) for row in rows],
            }
        finally:
            conn.close()

    def set_budget(self, model: str, field: str, value: Any) -> None:
        self.budget_store.set_value(model, field, value)

    def iter_events(self, event_type: str | None = None) -> list[sqlite3.Row]:
        conn = self._connect()
        try:
            if event_type:
                return conn.execute(
                    "SELECT * FROM events WHERE type = ? ORDER BY id ASC",
                    (event_type,),
                ).fetchall()
            return conn.execute("SELECT * FROM events ORDER BY id ASC").fetchall()
        finally:
            conn.close()

    def fetch_value(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        conn = self._connect()
        try:
            row = conn.execute(sql, params).fetchone()
            if row is None:
                return None
            return row[0]
        finally:
            conn.close()

    def _is_pipeline_paused(
        self,
        conn: sqlite3.Connection,
        current_model: str,
        config: BudgetConfig | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        config = config or self.budget_store.load()
        policy = config.kill_switch_policy
        models = {
            *config.models.keys(),
            *[
                str(row["model"])
                for row in conn.execute(
                    """
                    SELECT DISTINCT model FROM (
                        SELECT model FROM jobs
                        UNION
                        SELECT model FROM reservations
                        UNION
                        SELECT model FROM usage
                    )
                    """
                ).fetchall()
            ],
        }
        exhausted_models: list[str] = []
        for model in sorted(models):
            rule = config.for_model(model)
            committed = _committed_budget(conn, model, rule.weekly_window)
            weekly_calls_exhausted = committed["weekly_calls"] >= rule.weekly_calls
            weekly_budget_exhausted = (
                rule.weekly_budget_usd is not None
                and committed["weekly_budget_usd"] >= rule.weekly_budget_usd
            )
            if weekly_calls_exhausted or weekly_budget_exhausted:
                exhausted_models.append(model)

        if not exhausted_models:
            return False, {"policy": policy, "exhausted_models": exhausted_models}
        if policy == "PAUSE_ALL":
            return True, {"policy": policy, "exhausted_models": exhausted_models}
        if policy == "CLAUDE_ONLY_PAUSE":
            return current_model.startswith("claude-"), {
                "policy": policy,
                "exhausted_models": exhausted_models,
            }
        return False, {"policy": policy, "exhausted_models": exhausted_models}


def _weekly_threshold_sql(window: str) -> str:
    if window == "calendar_utc":
        return (
            "CASE "
            "WHEN strftime('%w','now') = '1' "
            f"THEN CAST(strftime('%s','now','start of day') AS INTEGER) "
            f"ELSE CAST(strftime('%s','now','weekday 1','-7 days','start of day') AS INTEGER) "
            "END"
        )
    return "CAST(strftime('%s','now','-7 days') AS INTEGER)"


def _committed_budget(
    conn: sqlite3.Connection,
    model: str,
    weekly_window: str,
) -> dict[str, float]:
    weekly_threshold = _weekly_threshold_sql(weekly_window)
    hourly = conn.execute(
        f"""
        SELECT
            COALESCE(
                (SELECT SUM(actual_calls) FROM usage
                 WHERE model = ? AND completed_at > {SQLITE_ONE_HOUR_AGO_EPOCH}),
                0
            ) +
            COALESCE(
                (SELECT SUM(reserved_calls) FROM reservations
                 WHERE model = ? AND reserved_at > {SQLITE_ONE_HOUR_AGO_EPOCH}),
                0
            ) AS committed_calls
        """,
        (model, model),
    ).fetchone()
    weekly = conn.execute(
        f"""
        SELECT
            COALESCE(
                (SELECT SUM(actual_calls) FROM usage
                 WHERE model = ? AND completed_at > {weekly_threshold}),
                0
            ) +
            COALESCE(
                (SELECT SUM(reserved_calls) FROM reservations
                 WHERE model = ? AND reserved_at > {weekly_threshold}),
                0
            ) AS committed_calls,
            COALESCE(
                (SELECT SUM(actual_usd) FROM usage
                 WHERE model = ? AND completed_at > {weekly_threshold}),
                0
            ) +
            COALESCE(
                (SELECT SUM(reserved_usd) FROM reservations
                 WHERE model = ? AND reserved_at > {weekly_threshold}),
                0
            ) AS committed_usd
        """,
        (model, model, model, model),
    ).fetchone()
    return {
        "hourly_calls": int(hourly["committed_calls"]),
        "weekly_calls": int(weekly["committed_calls"]),
        "weekly_budget_usd": round(float(weekly["committed_usd"]), 4),
    }


def _record_event(
    conn: sqlite3.Connection,
    event_type: str,
    *,
    module_key: str | None = None,
    lease_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO events (type, module_key, lease_id, payload_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            event_type,
            module_key,
            lease_id,
            json.dumps(payload or {}, sort_keys=True),
        ),
    )

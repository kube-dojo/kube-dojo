"""Broker utilities: PID file management, lock detection, cleanup, status."""

import json
import os
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from ._config import DB_PATH, PID_DIR, REPO_ROOT


def _git_status_snapshot() -> set[str]:
    """Capture current set of modified/untracked files for post-validation."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO_ROOT)
        )
        return set(result.stdout.strip().splitlines()) if result.stdout.strip() else set()
    except Exception:
        return set()


def _validate_file_writes(pre_snapshot: set[str], allowed_path: str) -> list[str]:
    """Compare git status before/after to detect unauthorized file writes.

    Returns list of violation descriptions (empty = clean).
    """
    post_snapshot = _git_status_snapshot()
    new_changes = post_snapshot - pre_snapshot
    if not new_changes:
        return []

    # Normalize allowed path to be relative to repo root
    try:
        allowed_rel = str(Path(allowed_path).resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        allowed_rel = allowed_path

    violations = []
    for change in new_changes:
        # git status --porcelain format: "XY filename" or "XY filename -> newname"
        file_part = change[3:].strip().split(" -> ")[0].strip('"')
        if file_part != allowed_rel:
            violations.append(f"{change.strip()} (unauthorized)")
    return violations


def _write_pid_file(agent: str, task_id: str, info: dict, pid: int | None = None):
    """Write a PID file for a running agent process."""
    PID_DIR.mkdir(parents=True, exist_ok=True)
    pid_file = PID_DIR / f"{agent}-{task_id}.json"
    pid_data = {
        "pid": pid or os.getpid(),
        "agent": agent,
        "started": datetime.now(UTC).isoformat(),
        **info,
    }
    pid_file.write_text(json.dumps(pid_data, indent=2))


def _is_task_locked(agent: str, task_id: str) -> bool:
    """Check if another process is already working on this task.

    Returns True if locked (another process is alive), False if free.
    Cleans up stale PID files automatically.
    Excludes the current process's own PID (prevents self-lock).
    Also detects stale locks: if PID file is older than 30 minutes and the
    process doesn't look like a python/gemini/claude process, treat as stale.
    """
    if not task_id:
        return False

    pid_file = PID_DIR / f"{agent}-{task_id}.json"
    if not pid_file.exists():
        return False

    try:
        data = json.loads(pid_file.read_text())
        pid = data.get("pid", 0)
        if pid == os.getpid():
            return False  # It's us — not locked
        os.kill(pid, 0)  # Signal 0 = check if process exists

        # Process exists, but check if PID file is stale (>30 min old)
        return _check_stale_lock(data, pid, pid_file)
    except (ProcessLookupError, PermissionError):
        # Process is dead — clean up stale PID file
        pid_file.unlink(missing_ok=True)
        return False
    except Exception:
        pid_file.unlink(missing_ok=True)
        return False


def _check_stale_lock(data: dict, pid: int, pid_file: Path) -> bool:
    """Check if a lock held by a live process is stale (>30 min old).

    Returns True if locked (process is alive and lock is valid), False if stale (cleaned up).
    """
    started = data.get("started")
    if not started:
        return True  # Can't check age — assume locked

    try:
        start_time = datetime.fromisoformat(started)
        age_minutes = (datetime.now(UTC) - start_time).total_seconds() / 60
        if age_minutes <= 30:
            return True  # Young lock, process is alive — locked
    except (ValueError, TypeError):
        return True  # Can't parse timestamp — assume locked

    # PID exists but lock is old — verify process is actually ours
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm="],
            capture_output=True, text=True, timeout=5
        )
        proc_name = result.stdout.strip().lower()
        if any(name in proc_name for name in ("python", "gemini", "claude", "node")):
            return True  # Our process, still running
        print(f"🧹 Stale PID lock: {pid_file.name} (PID {pid} is '{proc_name}', {age_minutes:.0f}m old)")
        pid_file.unlink(missing_ok=True)
        return False
    except Exception:
        # Can't verify process name — treat old lock as stale
        print(f"🧹 Stale PID lock: {pid_file.name} ({age_minutes:.0f}m old, can't verify process)")
        pid_file.unlink(missing_ok=True)
        return False


def _remove_pid_file(agent: str, task_id: str):
    """Remove PID file when process finishes."""
    pid_file = PID_DIR / f"{agent}-{task_id}.json"
    pid_file.unlink(missing_ok=True)


def broker_cleanup(max_age_hours: int = 24, dry_run: bool = False):
    """Clean up stuck broker state: stale PIDs, ancient unacked messages, orphaned locks."""
    action = "Would clean" if dry_run else "Cleaning"
    cleaned = 0

    # 1. Clean stale PID files
    cleaned += _cleanup_stale_pids(action, max_age_hours, dry_run)

    # 2. Force-ack ancient unacknowledged messages
    cleaned += _cleanup_ancient_messages(action, max_age_hours, dry_run)

    # 3. Summary
    mode = " (DRY RUN)" if dry_run else ""
    if cleaned == 0:
        print(f"✅ Broker is clean — nothing to do{mode}")
    else:
        print(f"\n🧹 {cleaned} items cleaned{mode}")


def _cleanup_stale_pids(action: str, max_age_hours: int, dry_run: bool) -> int:
    """Clean stale PID files. Returns count of cleaned items."""
    cleaned = 0
    if not PID_DIR.exists():
        return 0

    for pid_file in PID_DIR.glob("*.json"):
        try:
            data = json.loads(pid_file.read_text())
            pid = data.get("pid", 0)
            try:
                os.kill(pid, 0)
                # Process alive — check age
                started = data.get("started", "")
                if started:
                    start_time = datetime.fromisoformat(started)
                    age_h = (datetime.now(UTC) - start_time).total_seconds() / 3600
                    if age_h > max_age_hours:
                        print(f"  {action} stale PID: {pid_file.name} (alive but {age_h:.1f}h old)")
                        if not dry_run:
                            pid_file.unlink(missing_ok=True)
                        cleaned += 1
            except (ProcessLookupError, PermissionError):
                # Process dead
                print(f"  {action} dead PID: {pid_file.name} (process gone)")
                if not dry_run:
                    pid_file.unlink(missing_ok=True)
                cleaned += 1
        except Exception:
            print(f"  {action} corrupt PID: {pid_file.name}")
            if not dry_run:
                pid_file.unlink(missing_ok=True)
            cleaned += 1
    return cleaned


def _cleanup_ancient_messages(action: str, max_age_hours: int, dry_run: bool) -> int:
    """Force-ack ancient unacknowledged messages. Returns count of cleaned items."""
    cleaned = 0
    if not DB_PATH.exists():
        return 0

    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    datetime.now(UTC).isoformat()
    rows = db.execute(
        "SELECT id, task_id, from_llm, to_llm, timestamp FROM messages WHERE acknowledged=0"
    ).fetchall()
    for row in rows:
        try:
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            age_h = (datetime.now(UTC) - ts).total_seconds() / 3600
            if age_h > max_age_hours:
                print(f"  {action} stuck msg #{row['id']}: {row['from_llm']}→{row['to_llm']} "
                      f"task={row['task_id']} ({age_h:.1f}h old)")
                if not dry_run:
                    db.execute("UPDATE messages SET acknowledged=1 WHERE id=?", (row["id"],))
                cleaned += 1
        except (ValueError, TypeError):
            pass
    if not dry_run:
        db.commit()
    db.close()
    return cleaned


def bridge_status():
    """Show status of all running bridge processes."""
    if not PID_DIR.exists():
        print("No PID directory found. No processes tracked yet.")
        return

    pid_files = list(PID_DIR.glob("*.json"))
    if not pid_files:
        print("No bridge processes tracked.")
        return

    alive, stale = _categorize_pid_files(pid_files)

    if alive:
        print(f"🟢 {len(alive)} running bridge process(es):\n")
        for name, data in alive:
            _print_process_info(name, data)
    else:
        print("No running bridge processes.")

    if stale:
        print(f"🔴 Cleaned up {len(stale)} stale PID file(s): {', '.join(n for n, _ in stale)}")


def _categorize_pid_files(pid_files: list[Path]) -> tuple[list, list]:
    """Categorize PID files into alive and stale. Cleans up stale files."""
    alive = []
    stale = []
    for pf in sorted(pid_files):
        try:
            data = json.loads(pf.read_text())
            pid = data.get("pid", 0)
            try:
                os.kill(pid, 0)
                alive.append((pf.name, data))
            except (ProcessLookupError, PermissionError):
                stale.append((pf.name, data))
                pf.unlink()
        except Exception:
            stale.append((pf.name, {}))
            pf.unlink()
    return alive, stale


def _print_process_info(name: str, data: dict):
    """Print info for a single running bridge process."""
    print(f"  {name}")
    print(f"    PID: {data.get('pid')}")
    print(f"    Agent: {data.get('agent')}")
    print(f"    Task: {data.get('task_id')}")
    print(f"    Model: {data.get('model', 'N/A')}")
    print(f"    Started: {data.get('started')}")
    # Show log file tail
    log_dir = REPO_ROOT / ".mcp/servers/message-broker/logs"
    log_file = log_dir / f"{data.get('agent')}-{data.get('task_id')}.log"
    if log_file.exists():
        lines = log_file.read_text().strip().split('\n')
        last_line = lines[-1] if lines else "(empty)"
        print(f"    Log: {log_file}")
        print(f"    Last output: {last_line[:100]}")
    print()

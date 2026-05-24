from __future__ import annotations

import os
import subprocess
from pathlib import Path


def resolve_primary_repo_root(start: Path | None = None) -> Path | None:
    """Return the primary working tree root (not a linked worktree checkout)."""
    base = (start or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--git-common-dir"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    common = result.stdout.strip()
    if not common:
        return None
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = (base / common_path).resolve()
    return common_path.parent.resolve()


def process_cwd() -> Path | None:
    try:
        return Path(os.getcwd()).resolve()
    except OSError:
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def inspect_repo_root(repo_root: Path) -> dict[str, object]:
    """Validate that the API is serving from the expected primary checkout."""
    resolved = repo_root.resolve()
    primary = resolve_primary_repo_root(resolved)
    cwd = process_cwd()
    warnings: list[str] = []
    if primary is not None and resolved != primary:
        warnings.append(
            f"repo_root {resolved} is not the primary checkout ({primary}); "
            "artifact routes may 404 if this process outlives a worktree removal."
        )
    if cwd is not None and ".worktrees" in cwd.parts:
        warnings.append(f"process cwd {cwd} is inside a git worktree; prefer primary repo root.")
    api_pid_path = resolved / ".pids" / "api.pid"
    if api_pid_path.exists():
        try:
            pid = int(api_pid_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            warnings.append("api pid file is unreadable.")
        else:
            if not _pid_alive(pid):
                warnings.append("api pid file references a dead process.")
    return {
        "repo_root": str(resolved),
        "primary_repo_root": str(primary) if primary is not None else None,
        "process_cwd": str(cwd) if cwd is not None else None,
        "warnings": warnings,
    }


def build_healthz_payload(repo_root: Path) -> dict[str, object]:
    inspection = inspect_repo_root(repo_root)
    critical = [
        warning
        for warning in inspection["warnings"]
        if warning.startswith("repo_root ") or "dead process" in warning or "unreadable" in warning
    ]
    return {
        "ok": not critical,
        "repo_root": inspection["repo_root"],
        "primary_repo_root": inspection["primary_repo_root"],
        "warnings": inspection["warnings"],
    }

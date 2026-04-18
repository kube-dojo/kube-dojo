from __future__ import annotations

import fcntl
import re
from datetime import UTC, datetime
from pathlib import Path
def _render_audit_entry(event: str, timestamp: str, fields: dict) -> str:
    checks = fields.get("checks") if isinstance(fields.get("checks"), list) else []
    passed = [str(check.get("id", "?")) for check in checks if isinstance(check, dict) and check.get("passed")]
    failed = [str(check.get("id", "?")) for check in checks if isinstance(check, dict) and not check.get("passed")]
    lines = [
        f"## {timestamp} — `{event}` — `{fields.get('verdict', '')}`",
        "",
        f"**Reviewer**: {fields.get('reviewer', 'unknown')}",
        f"**Attempt**: {fields.get('attempt', '?')}",
        f"**Severity**: {fields.get('severity', 'unknown')}",
        f"**Checks**: {len(passed)}/{len(checks)} passed" + (f" ({' '.join(passed)})" if passed else "") + (f" | **Failed**: {' '.join(failed)}" if failed else ""),
        f"**Job Id**: {fields['job_id']}",
        f"**Lease Id**: {fields['lease_id']}",
    ]
    failed_evidence = [
        f"- **{check.get('id', '?')}**: {str(check.get('evidence', '')).strip()}"
        for check in checks
        if isinstance(check, dict) and not check.get("passed") and str(check.get("evidence", "")).strip()
    ]
    if failed_evidence:
        lines.extend(["", "**Failed check evidence**:", *failed_evidence])
    feedback = str(fields.get("feedback", "")).strip()
    if feedback:
        lines.extend(["", "**Feedback**:", *[f"> {line}" if line else ">" for line in feedback.splitlines() or [feedback]]])
    return "\n".join(lines)
def append_review_audit(module_path: Path, event: str, **fields) -> Path:
    repo_root = next((parent for parent in (module_path.parent, *module_path.parents) if (parent / ".pipeline").exists()), Path.cwd())
    module_key = str(fields.pop("module_key", module_path.stem)).removesuffix(".md")
    target = repo_root / ".pipeline" / "reviews" / f"{module_key.replace('/', '__')}.md"
    timestamp = fields.pop("timestamp", None)
    if not isinstance(timestamp, str):
        current = timestamp or datetime.now(UTC)
        timestamp = (current.replace(tzinfo=UTC) if current.tzinfo is None else current.astimezone(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target.with_suffix(".lock"), "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            existing = target.read_text(encoding="utf-8") if target.exists() else ""
            if any(fields.get(key) and f"**{key.replace('_', ' ').title()}**: {fields[key]}" in existing for key in ("job_id", "lease_id")):
                return target
            body = re.split(r"\n---\n+", existing, maxsplit=1)[1].lstrip() if "\n---\n" in existing else ""
            entry = _render_audit_entry(event, timestamp, fields)
            display_path = str(module_path.resolve()) if repo_root not in module_path.resolve().parents else str(module_path.resolve().relative_to(repo_root))
            target.write_text(
                "\n".join([
                    f"# Review Audit: {module_key}",
                    "",
                    f"**Path**: `{display_path}`",
                    f"**First pass**: {(re.findall(r'^## ([0-9TZ:\\-]+) — ', existing, re.MULTILINE) or [timestamp])[-1] if existing else timestamp}",
                    f"**Last pass**: {timestamp}",
                    f"**Total passes**: {len(re.findall(r'^## ([0-9TZ:\\-]+) — ', existing, re.MULTILINE)) + 1}",
                    "**Current phase**: pending",
                    "**Current reviewer**: -",
                    "**Current severity**: -",
                    "",
                    "---",
                    "",
                    entry if not body.strip() else f"{entry}\n\n---\n\n{body.strip()}",
                    "",
                ]),
                encoding="utf-8",
            )
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
    return target

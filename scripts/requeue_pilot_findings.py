#!/usr/bin/env python3
"""One-off: undo 2026-04-24 Claude-pilot effect on the residuals queue.

The pilot (PR #374 --agent claude) resolved 73 findings and marked others
unresolvable across 57 modules. We are reverting the module edits (via
`git restore`) and want the findings to land back in `needs_citation[]`
so the forthcoming RAG-based resolver can re-try them with grounded
citations.

Strategy: for each queue file in .pipeline/v3/human-review/, find entries
in `resolved_findings[]` and `unresolvable_findings[]` whose `resolved_at`
timestamp is >= CUTOFF (pilot window), strip resolver-added fields, and
prepend them back into `queued_findings.needs_citation[]`.

Dry-run by default; pass --apply to write.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
HUMAN_REVIEW_DIR = REPO_ROOT / ".pipeline" / "v3" / "human-review"

RESOLVER_ADDED_FIELDS = {
    "resolved_at",
    "url",
    "tier",
    "short_id",
    "anchors_matched",
    "unresolvable_reason",
    "attempts",
}


def parse_iso_z(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def strip_resolver_fields(entry: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in entry.items() if k not in RESOLVER_ADDED_FIELDS}


def requeue_one(path: Path, cutoff: datetime) -> tuple[dict[str, Any], int, int, bool]:
    data = json.loads(path.read_text(encoding="utf-8"))
    queued = data.setdefault("queued_findings", {})
    nc = list(queued.get("needs_citation") or [])
    resolved = list(data.get("resolved_findings") or [])
    unresolvable = list(data.get("unresolvable_findings") or [])

    def split(entries: list[dict[str, Any]]) -> tuple[list, list]:
        pilot, kept = [], []
        for e in entries:
            ts = e.get("resolved_at")
            if ts and parse_iso_z(ts) >= cutoff:
                pilot.append(e)
            else:
                kept.append(e)
        return pilot, kept

    pilot_resolved, kept_resolved = split(resolved)
    pilot_unresolvable, kept_unresolvable = split(unresolvable)

    requeued = [strip_resolver_fields(e) for e in pilot_resolved + pilot_unresolvable]
    new_nc = requeued + nc

    data["queued_findings"]["needs_citation"] = new_nc
    data["resolved_findings"] = kept_resolved
    data["unresolvable_findings"] = kept_unresolvable
    changed = bool(pilot_resolved) or bool(pilot_unresolvable)
    return data, len(pilot_resolved), len(pilot_unresolvable), changed


def find_cutoff(files: list[Path]) -> datetime:
    """Pilot cutoff = earliest `resolved_at` across files mtime'd in last 3h."""
    from datetime import timedelta

    mtime_floor = datetime.now(timezone.utc) - timedelta(hours=3)
    earliest: datetime | None = None
    for p in files:
        if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) < mtime_floor:
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for arr in (data.get("resolved_findings") or [], data.get("unresolvable_findings") or []):
            for e in arr:
                ts = e.get("resolved_at")
                if not ts:
                    continue
                t = parse_iso_z(ts)
                if t < mtime_floor:
                    continue
                if earliest is None or t < earliest:
                    earliest = t
    if earliest is None:
        print("ERROR: could not find any pilot-window resolved_at timestamps", file=sys.stderr)
        sys.exit(2)
    return earliest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    ap.add_argument(
        "--cutoff",
        help="ISO-8601 UTC cutoff (e.g. 2026-04-24T12:00:00Z). "
        "Entries with resolved_at >= cutoff are requeued. "
        "If omitted, auto-detected from recently-touched queue files.",
    )
    args = ap.parse_args()

    files = sorted(HUMAN_REVIEW_DIR.glob("*.json"))
    if not files:
        print(f"No queue files in {HUMAN_REVIEW_DIR}", file=sys.stderr)
        return 1

    cutoff = parse_iso_z(args.cutoff) if args.cutoff else find_cutoff(files)
    print(f"# Cutoff: {cutoff.isoformat()} — entries with resolved_at >= this are requeued")
    print(f"# Scanning {len(files)} queue files in {HUMAN_REVIEW_DIR}")
    print(f"# Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()

    total_resolved = 0
    total_unresolvable = 0
    files_touched = 0

    for path in files:
        new_data, n_res, n_unres, changed = requeue_one(path, cutoff)
        if not changed:
            continue
        files_touched += 1
        total_resolved += n_res
        total_unresolvable += n_unres
        print(f"{path.name}: requeue {n_res} resolved + {n_unres} unresolvable")
        if args.apply:
            path.write_text(json.dumps(new_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print(f"# Files touched: {files_touched}")
    print(f"# Requeued:      {total_resolved} resolved + {total_unresolvable} unresolvable")
    print(f"#                = {total_resolved + total_unresolvable} findings back in needs_citation")
    if not args.apply:
        print("# Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

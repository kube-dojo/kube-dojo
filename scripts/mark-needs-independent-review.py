#!/usr/bin/env python3
"""Mark every passed module as needing an independent reviewer stamp.

Independent reviewer = codex or claude. Gemini does NOT count as independent
because it is the same family as the writer and has known self-bias.

Run this after switching the official reviewer to Codex. All modules previously
passed by Gemini (or with no recorded reviewer) get `needs_independent_review=True`.
Their `reviewer` field is preserved if set, else assumed "gemini".

The modules are NOT reset to an earlier phase — the content on disk remains
usable. Only the independent reviewer stamp is flagged as missing, so operators
can prioritize re-reviewing with Codex when quota is available.

Usage:
    python scripts/mark-needs-independent-review.py --dry-run
    python scripts/mark-needs-independent-review.py --apply

The script is idempotent: running it twice is a no-op on already-marked modules.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
STATE_FILE = REPO_ROOT / ".pipeline" / "state.yaml"

# Mirror of v1_pipeline.INDEPENDENT_REVIEWER_FAMILIES — duplicated here so this
# script has no import-time dependency on the full pipeline module.
INDEPENDENT_REVIEWER_FAMILIES = {"codex", "claude"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    group.add_argument("--apply", action="store_true", help="Persist changes to state.yaml")
    args = parser.parse_args()

    if not STATE_FILE.exists():
        print(f"State file not found: {STATE_FILE}", file=sys.stderr)
        return 1

    state = yaml.safe_load(STATE_FILE.read_text()) or {}
    modules = state.get("modules") or {}

    total = 0
    would_mark = 0
    already_independent = 0
    not_done = 0

    for ms in modules.values():
        total += 1
        phase = ms.get("phase")
        if phase != "done":
            not_done += 1
            continue
        reviewer = ms.get("reviewer") or "gemini"
        if reviewer in INDEPENDENT_REVIEWER_FAMILIES and not ms.get("needs_independent_review", False):
            already_independent += 1
            continue
        ms["reviewer"] = reviewer
        ms["needs_independent_review"] = True
        would_mark += 1

    print(f"Total modules in state: {total}")
    print(f"  phase=done: {total - not_done}")
    print(f"  phase!=done (skipped): {not_done}")
    print(f"  already independently reviewed: {already_independent}")
    print(f"  to flag needs_independent_review=True: {would_mark}")

    if args.apply and would_mark > 0:
        STATE_FILE.write_text(yaml.safe_dump(state, sort_keys=False))
        print(f"\n✓ Applied. {would_mark} modules flagged in {STATE_FILE}")
    elif args.dry_run:
        print("\n(dry-run — no changes written)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

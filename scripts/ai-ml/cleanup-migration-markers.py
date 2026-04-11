#!/usr/bin/env python3
"""Remove neural-dojo migration markers from AI/ML Engineering modules.

Phase 4b (#199) left a TODO-style blockquote line on every migrated module:
    > **Migrated from neural-dojo** — pending pipeline polish

These are migration-tool artifacts, not module content, and should not ship
to readers. Delete them and any leading blank line the removal leaves behind.

Usage:
    python scripts/ai-ml/cleanup-migration-markers.py --dry-run
    python scripts/ai-ml/cleanup-migration-markers.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACK_ROOT = REPO_ROOT / "src" / "content" / "docs" / "ai-ml-engineering"

MARKER_LINE = "> **Migrated from neural-dojo** — pending pipeline polish"
# Match the line with optional trailing whitespace; remove the whole line
# including its trailing newline so we don't leave a blank line behind when
# the marker was a standalone blockquote continuation of the preceding line.
MARKER_RE = re.compile(
    r"^> \*\*Migrated from neural-dojo\*\* — pending pipeline polish\s*\n",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Report changes, write nothing")
    mode.add_argument("--apply", action="store_true", help="Apply the cleanup")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    touched = 0
    skipped = 0

    for md in sorted(TRACK_ROOT.rglob("*.md")):
        content = md.read_text(encoding="utf-8")
        if MARKER_LINE not in content:
            skipped += 1
            continue
        new_content = MARKER_RE.sub("", content)
        if new_content == content:
            # Marker present but regex didn't match — unusual whitespace. Skip.
            print(f"  SKIP (regex miss): {md.relative_to(REPO_ROOT)}", file=sys.stderr)
            skipped += 1
            continue
        rel = md.relative_to(REPO_ROOT)
        print(f"  {'would strip' if args.dry_run else 'stripped   '}: {rel}")
        if args.apply:
            md.write_text(new_content, encoding="utf-8")
        touched += 1

    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print(f"\n[{mode}] touched={touched}, skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

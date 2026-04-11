#!/usr/bin/env python3
"""Normalize `sidebar.order` values across on-prem module files.

Re-flows every on-prem section so `sidebar.order` values are a contiguous
sequence starting at the section convention: `index.md=0`, first module=2,
next=3, next=4, ... (on-prem skips order 1 historically). Modules are
sorted by their filename's dotted module number (e.g. `3.1` before `3.10`
before `3.2` — numeric, not lexicographic).

Why this exists:
- PR #204's initial `_lib.sh` used a `major*100+minor` formula that
  diverged from the sibling convention (small sequential integers),
  leaving modules with orders like 105, 305, 901 alongside existing
  orders 2-5 in the same section. Functionally it sorted correctly, but
  was inconsistent.
- This script is idempotent: run it any number of times; it always lands
  on the same sequential values.
- Safe to run after phase2-new-modules.sh: any stubs created with the old
  formula get normalized on the next invocation.

Usage:
    python scripts/on-prem/normalize-sidebar-order.py --dry-run
    python scripts/on-prem/normalize-sidebar-order.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACK_ROOT = REPO_ROOT / "src" / "content" / "docs" / "on-premises"

MODULE_RE = re.compile(r"^module-(\d+)\.(\d+)-.+\.md$")
ORDER_LINE_RE = re.compile(r"^(\s*order:\s*)\d+(\s*)$", re.MULTILINE)
FIRST_MODULE_ORDER = 2  # index.md=0; module-X.1=2 (on-prem convention)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print planned changes, write nothing")
    mode.add_argument("--apply", action="store_true", help="Apply the normalization")
    return parser.parse_args()


def write_text_atomic(path: Path, content: str) -> None:
    """Write file via tempfile + replace (atomic on POSIX)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=path.parent
    ) as tmp:
        tmp.write(content)
        temp_name = tmp.name
    Path(temp_name).replace(path)


def read_current_order(text: str) -> int | None:
    match = ORDER_LINE_RE.search(text)
    if not match:
        return None
    # The full line looks like "  order: <n>"; extract <n> from the text.
    number_match = re.search(r"order:\s*(\d+)", match.group(0))
    return int(number_match.group(1)) if number_match else None


def set_order(text: str, new_order: int) -> str:
    return ORDER_LINE_RE.sub(rf"\g<1>{new_order}\g<2>", text, count=1)


def normalize_section(section_dir: Path, dry_run: bool) -> tuple[int, int]:
    """Normalize one section. Returns (touched, unchanged)."""
    modules: list[tuple[int, int, Path]] = []
    for md in section_dir.glob("module-*.md"):
        match = MODULE_RE.match(md.name)
        if not match:
            continue
        modules.append((int(match.group(1)), int(match.group(2)), md))
    # Sort by (major, minor) — numeric, not lexicographic
    modules.sort(key=lambda item: (item[0], item[1]))

    touched = 0
    unchanged = 0
    for index, (_major, _minor, md) in enumerate(modules):
        expected = FIRST_MODULE_ORDER + index
        text = md.read_text(encoding="utf-8")
        current = read_current_order(text)
        if current is None:
            print(f"  SKIP (no order line): {md.relative_to(REPO_ROOT)}", file=sys.stderr)
            continue
        if current == expected:
            unchanged += 1
            continue
        action = "would set" if dry_run else "set"
        print(f"  {action} {md.relative_to(REPO_ROOT)}: {current} -> {expected}")
        if not dry_run:
            write_text_atomic(md, set_order(text, expected))
        touched += 1
    return touched, unchanged


def main() -> int:
    args = parse_args()
    if not TRACK_ROOT.exists():
        print(f"Track root not found: {TRACK_ROOT}", file=sys.stderr)
        return 1

    total_touched = 0
    total_unchanged = 0
    sections = sorted(p for p in TRACK_ROOT.iterdir() if p.is_dir())
    for section in sections:
        touched, unchanged = normalize_section(section, dry_run=args.dry_run)
        total_touched += touched
        total_unchanged += unchanged

    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print(f"\n[{mode}] touched={total_touched}, unchanged={total_unchanged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Filter a list of changed Ukrainian markdown files down to those whose diff
touches real *content* — dropping metadata-only changes (e.g. a provenance
`en_commit:` frontmatter line) so the CI russicism / calque gates do not
re-scan an untouched translation and surface its PRE-EXISTING findings.

The UK quality gates (`check_uk_changed.py`, `uk_calque_v2.py`) each scan the
WHOLE file they are handed, not just the changed lines. A pure-metadata touch
(the `en_commit` provenance backfill, #2237) therefore triggers a full re-scan
that fails on russicisms/structural issues the touch did not introduce. This
filter runs ONCE in the workflow and feeds the reduced list to both gates.

"Metadata-only" is defined conservatively: a file is metadata-only iff EVERY
line its diff adds/modifies on the new side is (a) within the YAML frontmatter
block AND (b) contains no Cyrillic. Rule (b) means any edit to translated
frontmatter prose (`title:`, `description:`) — or any body edit — routes the
file back to a full scan, so the gate's intent is preserved. Only fully-ASCII
metadata additions (a git SHA, `sidebar.order`, an ASCII slug) are skipped.

Usage:
    python3 scripts/quality/filter_content_changed.py --base-ref origin/main \
        <file1.md> <file2.md> ...

Prints the content-changed subset (one path per line) to stdout. With no
`--base-ref`, every input path is printed unchanged (fail-safe: scan all).

Pure stdlib.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Any Cyrillic code point (U+0400–U+04FF). An added frontmatter line containing
# Cyrillic is treated as translated content (e.g. an edited title), NOT skipped.
CYRILLIC_RE = re.compile("[\u0400-\u04FF]")

# Unified-diff hunk header: capture the new-side start line (and optional count).
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def frontmatter_end_line(text: str) -> int:
    """1-based line number of the closing `---` of the YAML frontmatter block.

    Returns 0 when the file has no leading frontmatter (so every line is body).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return 0
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return idx + 1  # 1-based line number of the closing fence
    return 0


def added_new_side_lines(base_ref: str, path: Path) -> list[tuple[int, str]] | None:
    """Lines added/modified on the NEW side of `git diff base_ref...HEAD -- path`.

    Returns a list of (new_line_number, line_text). Returns None when the diff
    cannot be computed (git error / not a repo) so the caller can fail safe and
    scan the file in full.
    """
    try:
        proc = subprocess.run(
            ["git", "diff", "--unified=0", f"{base_ref}...HEAD", "--", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None

    added: list[tuple[int, str]] = []
    new_lineno = 0
    in_hunk = False
    for line in proc.stdout.splitlines():
        hunk = _HUNK_RE.match(line)
        if hunk:
            new_lineno = int(hunk.group(1))
            in_hunk = True
            continue
        if not in_hunk:
            # Pre-hunk header block (`diff --git`, `index`, `--- a/…`, `+++ b/…`,
            # `new file mode`, …). Skipping only here avoids mis-reading a body
            # addition whose content starts with `++`/`--` — inside a hunk it
            # appears as `+++…`/`---…` but IS content, not a header.
            continue
        if line.startswith("+"):
            added.append((new_lineno, line[1:]))
            new_lineno += 1
        # `-` (deletion) lines and everything else do not advance the new-side
        # counter; with --unified=0 there are no context lines.
    return added


def is_metadata_only(base_ref: str, path: Path) -> bool:
    """True iff the file's diff vs base_ref touches only frontmatter metadata."""
    added = added_new_side_lines(base_ref, path)
    if added is None:
        return False  # cannot determine → scan in full
    if not added:
        # Only deletions (no added lines). A body deletion can still introduce a
        # structural FAIL (e.g. making two `##` headings adjacent), so we cannot
        # prove it safe from the new side alone — fail toward a full scan.
        return False

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False  # cannot read head file → scan in full

    fm_end = frontmatter_end_line(text)
    if fm_end == 0:
        return False  # no frontmatter → any addition is body content

    for lineno, content in added:
        if lineno > fm_end:
            return False  # a body line changed
        if CYRILLIC_RE.search(content):
            return False  # translated prose added inside frontmatter
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Base git ref to diff against (e.g. origin/main). "
        "When omitted, every input path is emitted unchanged.",
    )
    parser.add_argument("paths", nargs="*", help="Changed Ukrainian markdown files")
    args = parser.parse_args(argv)

    for path_str in args.paths:
        if args.base_ref and is_metadata_only(args.base_ref, Path(path_str)):
            continue  # drop metadata-only file from the downstream scan
        print(path_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Remove a leaked source-H1 from KubeDojo modules.

A module fails the verifier's `gate_no_source_h1` when the first real content
line after the frontmatter is an `# ` H1 heading. Starlight already renders an
H1 from the `title:` frontmatter, so this duplicate H1 must be removed.

Detection mirrors `verify_module.source_h1_metrics` EXACTLY: walk the post-
frontmatter body, skipping blank / blockquote (`>`) / `---` / `<!--` lines; the
first remaining line is the violation iff it starts with `# `.

Deterministic, single-line removal. Use `--check` to list without editing.

  python scripts/quality/fix_leaked_source_h1.py <path>... [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


def find_leaked_h1_index(text: str) -> int | None:
    """Return the 0-based line index of the leaked source-H1, or None."""
    match = FRONTMATTER.match(text)
    body = text[match.end() :] if match else text
    body_offset = text[: match.end()].count("\n") if match else 0

    for i, line in enumerate(body.splitlines()):
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith(">")
            or stripped == "---"
            or stripped.startswith("<!--")
        ):
            continue
        if stripped.startswith("# "):
            return body_offset + i
        return None
    return None


def fix_text(text: str) -> tuple[str, str | None]:
    """Return (new_text, removed_line) — removed_line is None if no violation."""
    idx = find_leaked_h1_index(text)
    if idx is None:
        return text, None
    # Preserve trailing newline semantics by splitting with keepends.
    lines = text.splitlines(keepends=True)
    removed = lines[idx].rstrip("\n")
    del lines[idx]
    # Collapse a resulting double blank line at the removal point.
    if (
        idx < len(lines)
        and idx > 0
        and lines[idx].strip() == ""
        and lines[idx - 1].strip() == ""
    ):
        del lines[idx]
    return "".join(lines), removed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument(
        "--check", action="store_true", help="List violations without editing."
    )
    args = ap.parse_args(argv)

    fixed = 0
    clean = 0
    for p in args.paths:
        text = p.read_text(encoding="utf-8")
        new_text, removed = fix_text(text)
        if removed is None:
            clean += 1
            continue
        fixed += 1
        if args.check:
            print(f"[would fix] {p}: remove leaked H1 -> {removed!r}")
        else:
            p.write_text(new_text, encoding="utf-8")
            print(f"[fixed]    {p}: removed leaked H1 -> {removed!r}")
    verb = "would fix" if args.check else "fixed"
    print(f"\n{verb} {fixed} module(s); {clean} had no leaked H1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

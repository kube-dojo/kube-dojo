#!/usr/bin/env python3
"""Lint reader aids on AI history chapters.

Validates the canonical layout from `docs/research/ai-history/READER_AIDS.md`:

  Tier 1 — REQUIRED on every chapter:
    1. TL;DR        :::tip[In one paragraph] aside, ≤80 words
    2. Cast         <details><summary><strong>Cast of characters</strong></summary> with ≤6 data rows
    3. Timeline     <details><summary><strong>Timeline …</strong></summary> with mermaid timeline directive
    4. Glossary     <details><summary><strong>Plain-words glossary</strong></summary> with 5–7 terms
    5. Why-still    :::note[Why this still matters today] aside, ≤120 words

Exits non-zero if any chapter fails. Use --json for machine-readable output.

Usage:
    python scripts/check_reader_aids.py                 # all 72 chapters
    python scripts/check_reader_aids.py ch-04 ch-58     # specific chapters
    python scripts/check_reader_aids.py --json          # JSON output
    python scripts/check_reader_aids.py --quiet         # only print failures
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = REPO_ROOT / "src" / "content" / "docs" / "ai-history"

TLDR_OPEN = ":::tip[In one paragraph]"
WHY_STILL_OPEN = ":::note[Why this still matters today]"
ASIDE_CLOSE = ":::"

CAST_SUMMARY = re.compile(r"<summary>\s*(?:<strong>\s*)?Cast of characters\s*(?:</strong>\s*)?</summary>", re.IGNORECASE)
TIMELINE_SUMMARY = re.compile(r"<summary>\s*(?:<strong>\s*)?Timeline\b[^<]*(?:</strong>\s*)?</summary>", re.IGNORECASE)
GLOSSARY_SUMMARY = re.compile(r"<summary>\s*(?:<strong>\s*)?Plain-words glossary\s*(?:</strong>\s*)?</summary>", re.IGNORECASE)
DETAILS_OPEN = re.compile(r"<details>")
DETAILS_CLOSE = re.compile(r"</details>")
MERMAID_TIMELINE = re.compile(r"```mermaid\s*\ntimeline\b", re.IGNORECASE)
TABLE_DATA_ROW = re.compile(r"^\|(?!\s*[-:])\s*\S")  # | word… (not a separator | --- | row)


@dataclass
class ChapterReport:
    slug: str
    path: Path
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tldr_words: int | None = None
    why_still_words: int | None = None
    cast_rows: int | None = None
    glossary_terms: int | None = None
    timeline_events: int | None = None

    def ok(self) -> bool:
        return not self.failures


def slice_aside(lines: list[str], open_marker: str) -> tuple[int, int] | None:
    """Find an aside block delimited by `open_marker` and the next `:::` close.

    Returns (start_idx, end_idx) line indices (inclusive of open, exclusive of close),
    or None if not found / unterminated.
    """
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == open_marker)
    except StopIteration:
        return None
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == ASIDE_CLOSE:
            return start + 1, j  # body lines between markers
    return None  # unterminated


def count_words(text: str) -> int:
    # Strip markdown emphasis/links/inline code so we count actual words.
    cleaned = re.sub(r"`[^`]*`", " ", text)            # inline code
    cleaned = re.sub(r"\*\*?", "", cleaned)            # bold/italic markers
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)  # [text](url) -> text
    return len(cleaned.split())


def find_details_block(lines: list[str], summary_re: re.Pattern[str]) -> tuple[int, int] | None:
    """Find a <details>…</details> block whose <summary> matches `summary_re`.

    Returns (start_idx_of_details, end_idx_of_details_inclusive) or None.
    """
    for i, ln in enumerate(lines):
        if summary_re.search(ln):
            # walk backward to <details>
            start = None
            for k in range(i, -1, -1):
                if DETAILS_OPEN.search(lines[k]):
                    start = k
                    break
            if start is None:
                return None
            # walk forward to </details>
            for k in range(i, len(lines)):
                if DETAILS_CLOSE.search(lines[k]):
                    return start, k
            return None
    return None


def count_table_data_rows(block: list[str]) -> int:
    """Count `| … |` data rows, skipping the header row and the |---| separator."""
    rows = [ln for ln in block if TABLE_DATA_ROW.match(ln)]
    # rows[0] is the header; subtract 1 if we got at least one match.
    return max(0, len(rows) - 1)


def count_glossary_terms(block: list[str]) -> int:
    """Glossary terms are bolded entries: `- **Term** —` (bullet list) or `**Term** —` (paragraph)."""
    pattern = re.compile(r"^(?:[-*]\s+)?\*\*[^*]+\*\*")
    return sum(1 for ln in block if pattern.match(ln.strip()))


def count_timeline_events(block: list[str]) -> int:
    """Inside a mermaid timeline, lines like `2024 : event` or `Q1 2024 : event` are events."""
    in_mermaid = False
    n = 0
    for ln in block:
        s = ln.strip()
        if s.startswith("```mermaid"):
            in_mermaid = True
            continue
        if s.startswith("```") and in_mermaid:
            in_mermaid = False
            continue
        if not in_mermaid:
            continue
        # event lines look like `<label> : <text>` and aren't `title …`
        if s.startswith("title"):
            continue
        if " : " in s:
            n += 1
    return n


def lint_chapter(path: Path) -> ChapterReport:
    rep = ChapterReport(slug=path.stem, path=path)
    lines = path.read_text(encoding="utf-8").splitlines()

    # 1. TL;DR
    span = slice_aside(lines, TLDR_OPEN)
    if span is None:
        rep.failures.append("missing or unterminated TL;DR aside :::tip[In one paragraph]:::")
    else:
        body = "\n".join(lines[span[0]:span[1]]).strip()
        rep.tldr_words = count_words(body)
        if rep.tldr_words > 80:
            rep.failures.append(f"TL;DR is {rep.tldr_words} words (cap ≤80)")

    # 2. Cast of characters
    cast = find_details_block(lines, CAST_SUMMARY)
    if cast is None:
        rep.failures.append("missing Cast of characters <details> block")
    else:
        rep.cast_rows = count_table_data_rows(lines[cast[0]:cast[1]+1])
        if rep.cast_rows == 0:
            rep.failures.append("Cast of characters has no data rows")
        elif rep.cast_rows > 6:
            rep.failures.append(f"Cast of characters has {rep.cast_rows} rows (cap ≤6)")

    # 3. Timeline
    timeline = find_details_block(lines, TIMELINE_SUMMARY)
    if timeline is None:
        rep.failures.append("missing Timeline <details> block")
    else:
        block_text = "\n".join(lines[timeline[0]:timeline[1]+1])
        if not MERMAID_TIMELINE.search(block_text):
            rep.failures.append("Timeline block missing ```mermaid\\ntimeline directive")
        else:
            rep.timeline_events = count_timeline_events(lines[timeline[0]:timeline[1]+1])
            if rep.timeline_events == 0:
                rep.warnings.append("Timeline mermaid block has 0 event lines")

    # 4. Plain-words glossary
    gloss = find_details_block(lines, GLOSSARY_SUMMARY)
    if gloss is None:
        rep.failures.append("missing Plain-words glossary <details> block")
    else:
        rep.glossary_terms = count_glossary_terms(lines[gloss[0]:gloss[1]+1])
        if rep.glossary_terms < 5 or rep.glossary_terms > 7:
            rep.failures.append(f"Glossary has {rep.glossary_terms} terms (spec 5–7)")

    # 5. Why this still matters today
    span = slice_aside(lines, WHY_STILL_OPEN)
    if span is None:
        rep.failures.append("missing or unterminated :::note[Why this still matters today]::: aside")
    else:
        body = "\n".join(lines[span[0]:span[1]]).strip()
        rep.why_still_words = count_words(body)
        if rep.why_still_words > 120:
            rep.failures.append(f"Why-still is {rep.why_still_words} words (cap ≤120)")

    return rep


def render_human(reports: list[ChapterReport], quiet: bool) -> int:
    failed = [r for r in reports if not r.ok()]
    warned = [r for r in reports if r.warnings and r.ok()]
    if not quiet:
        for r in reports:
            tag = "FAIL" if not r.ok() else ("WARN" if r.warnings else "OK  ")
            details = []
            if r.tldr_words is not None: details.append(f"tldr={r.tldr_words}w")
            if r.cast_rows is not None: details.append(f"cast={r.cast_rows}")
            if r.timeline_events is not None: details.append(f"tl={r.timeline_events}")
            if r.glossary_terms is not None: details.append(f"gloss={r.glossary_terms}")
            if r.why_still_words is not None: details.append(f"why={r.why_still_words}w")
            print(f"{tag}  {r.slug}  {' '.join(details)}")
            for f in r.failures: print(f"      FAIL: {f}")
            for w in r.warnings: print(f"      WARN: {w}")
    if quiet:
        for r in failed:
            print(f"FAIL  {r.slug}")
            for f in r.failures: print(f"      {f}")
        for r in warned:
            print(f"WARN  {r.slug}")
            for w in r.warnings: print(f"      {w}")
    print()
    print(f"Summary: {len(reports)} chapters · {len(reports)-len(failed)} pass · {len(failed)} fail · {len(warned)} warn-only")
    return 1 if failed else 0


def render_json(reports: list[ChapterReport]) -> int:
    out = []
    for r in reports:
        out.append({
            "slug": r.slug,
            "path": str(r.path.relative_to(REPO_ROOT)),
            "ok": r.ok(),
            "failures": r.failures,
            "warnings": r.warnings,
            "tldr_words": r.tldr_words,
            "why_still_words": r.why_still_words,
            "cast_rows": r.cast_rows,
            "glossary_terms": r.glossary_terms,
            "timeline_events": r.timeline_events,
        })
    print(json.dumps(out, indent=2))
    return 1 if any(not r.ok() for r in reports) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("filters", nargs="*", help="Chapter slug prefixes (e.g. ch-04, ch-58). Default: all 72.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable output.")
    ap.add_argument("--quiet", action="store_true", help="Only print failures + summary.")
    args = ap.parse_args()

    paths = sorted(CHAPTERS_DIR.glob("ch-*.md"))
    if args.filters:
        paths = [p for p in paths if any(p.name.startswith(f) for f in args.filters)]
    if not paths:
        print(f"no chapter files matched under {CHAPTERS_DIR}", file=sys.stderr)
        return 2

    reports = [lint_chapter(p) for p in paths]
    if args.json:
        return render_json(reports)
    return render_human(reports, args.quiet)


if __name__ == "__main__":
    sys.exit(main())

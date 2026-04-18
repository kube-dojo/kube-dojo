#!/usr/bin/env python3
"""Deterministic citation gate for quality-upgrade passes.

Usage:
    python scripts/check_citations.py path/to/module.md
    python scripts/check_citations.py module1.md module2.md --json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SOURCES_HEADING_RE = re.compile(r"^##\s+Sources\s*$", re.MULTILINE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
FOOTNOTE_DEF_RE = re.compile(r"^\[\^[^\]]+\]:", re.MULTILINE)
WAR_STORY_RE = re.compile(r"^\s*>\s+\*\*War Story:", re.MULTILINE)
SOURCE_LINE_RE = re.compile(r"Source\s*\*{0,2}\s*:", re.IGNORECASE)


def _slice_after_sources(text: str) -> str:
    match = SOURCES_HEADING_RE.search(text)
    if not match:
        return ""
    return text[match.end() :]


def _has_citation_marker(text: str) -> bool:
    return bool(MARKDOWN_LINK_RE.search(text) or FOOTNOTE_DEF_RE.search(text))


def _war_story_has_source(text: str) -> bool:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("> **War Story:"):
            window = lines[i : i + 8]
            if not any(SOURCE_LINE_RE.search(entry) for entry in window):
                return False
    return True


def check_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    sources_block = _slice_after_sources(text)
    sources_links = MARKDOWN_LINK_RE.findall(sources_block)
    has_sources = bool(sources_block)
    has_citation = _has_citation_marker(text)
    war_story_ok = _war_story_has_source(text)

    issues: list[str] = []
    if not has_sources:
        issues.append("missing_sources_section")
    if has_sources and not sources_links:
        issues.append("sources_section_has_no_external_links")
    if not has_citation:
        issues.append("no_citation_markers_found")
    if not war_story_ok:
        issues.append("war_story_missing_source_line")

    return {
        "path": str(path),
        "passes": not issues,
        "issues": issues,
        "sources_count": len(sources_links),
        "has_sources_section": has_sources,
        "has_citation_marker": has_citation,
        "war_stories_have_sources": war_story_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = [check_file(Path(path)) for path in args.paths]
    overall_pass = all(result["passes"] for result in results)

    if args.json:
        print(json.dumps({"passes": overall_pass, "results": results}, indent=2, ensure_ascii=False))
        return 0 if overall_pass else 1

    for result in results:
        status = "PASS" if result["passes"] else "FAIL"
        print(f"{status} {result['path']}")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"  - {issue}")
        else:
            print(f"  - sources: {result['sources_count']}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

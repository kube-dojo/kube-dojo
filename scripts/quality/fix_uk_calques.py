#!/usr/bin/env python3
"""Deterministic, context-aware Ukrainian calque fixer for markdown prose.

Usage:
    .venv/bin/python scripts/quality/fix_uk_calques.py scan PATH [PATH ...]
    .venv/bin/python scripts/quality/fix_uk_calques.py fix PATH [PATH ...]
"""
from __future__ import annotations

import argparse
import importlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

ukrainian = importlib.import_module("checks.ukrainian")
_WORD_CHAR = ukrainian._WORD_CHAR

AUTO_FIX = [
    ("в цілому", "загалом"),
    ("на протязі", "протягом"),
    ("по крайній мірі", "принаймні"),
    ("в залежності від", "залежно від"),
    ("у залежності від", "залежно від"),
    ("по мірі", "у міру"),
    ("у відповідності до", "відповідно до"),
    ("в відповідності до", "відповідно до"),
    ("приймати участь", "брати участь"),
    ("прийняти участь", "взяти участь"),
]

FLAG_ONLY = [
    (
        r"у\s+відповідності\s+(?:з|із)\b",
        "→ «відповідно до» + GENITIVE — case of the following noun changes; fix by hand",
    ),
    (
        r"в\s+залежності\s+(?:з|із)\b",
        "→ «відповідно до» + GENITIVE — case of the following noun changes; fix by hand",
    ),
    (
        r"в\s+залежності(?!\s+від)",
        "ambiguous noun-vs-adverb; «перебувати в залежності» → «залежати»; bare noun «залежність» is fine",
    ),
]

RAHUVATY_FORMS = [
    "рахую",
    "рахуєш",
    "рахує",
    "рахуємо",
    "рахуєте",
    "рахують",
    "рахував",
    "рахувала",
    "рахувало",
    "рахували",
    "рахувати",
    "рахуючи",
]

_RAHUVATY_NOTE = (
    "count-sense is OK (or «підраховувати»); consider-sense → «вважати». Adjudicate by hand."
)

_FENCE_LINE = re.compile(r"^\s*(```+|~~~+)")
_INLINE_CODE = re.compile(r"`[^`\n]+`")


def _build_phrase_pattern(phrase: str) -> re.Pattern[str]:
    words = phrase.split()
    inner = r"\s+".join(re.escape(word) for word in words)
    return re.compile(rf"(?<![{_WORD_CHAR}]){inner}(?![{_WORD_CHAR}])", re.IGNORECASE)


_AUTO_FIX_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_build_phrase_pattern(phrase), replacement) for phrase, replacement in AUTO_FIX
]

_FLAG_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(source, re.IGNORECASE), note) for source, note in FLAG_ONLY
]

_RAHUVATY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(rf"(?<![{_WORD_CHAR}]){re.escape(form)}(?![{_WORD_CHAR}])", re.IGNORECASE)
    for form in RAHUVATY_FORMS
]


def _preserve_case(original: str, replacement: str) -> str:
    if not replacement:
        return replacement
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _split_inline_code(line: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    last = 0
    for match in _INLINE_CODE.finditer(line):
        if match.start() > last:
            parts.append(("prose", line[last : match.start()]))
        parts.append(("code", match.group(0)))
        last = match.end()
    if last < len(line):
        parts.append(("prose", line[last:]))
    if not parts:
        parts.append(("prose", line))
    return parts


def _apply_auto_fixes_to_prose(prose: str) -> tuple[str, int]:
    fixes = 0
    for pattern, replacement in _AUTO_FIX_PATTERNS:

        def _replacer(match: re.Match[str], *, _replacement: str = replacement) -> str:
            nonlocal fixes
            fixes += 1
            return _preserve_case(match.group(0), _replacement)

        prose = pattern.sub(_replacer, prose)
    return prose, fixes


def _detect_flags_in_prose(prose: str) -> list[tuple[str, str]]:
    flags: list[tuple[str, str]] = []
    for pattern, note in _FLAG_PATTERNS:
        for match in pattern.finditer(prose):
            flags.append((match.group(0), note))
    for pattern in _RAHUVATY_PATTERNS:
        for match in pattern.finditer(prose):
            flags.append((match.group(0), _RAHUVATY_NOTE))
    return flags


def _process_prose_line(line: str) -> tuple[str, int, list[tuple[str, str]]]:
    parts = _split_inline_code(line)
    out: list[str] = []
    total_fixes = 0
    line_flags: list[tuple[str, str]] = []

    for kind, segment in parts:
        if kind == "code":
            out.append(segment)
            continue
        fixed, fixes = _apply_auto_fixes_to_prose(segment)
        total_fixes += fixes
        line_flags.extend(_detect_flags_in_prose(fixed))
        out.append(fixed)

    return "".join(out), total_fixes, line_flags


@dataclass
class ProcessResult:
    text: str
    auto_fixes: int
    flags: list[tuple[int, str, str]]


def process_text(content: str) -> ProcessResult:
    lines = content.splitlines(keepends=True)
    if not lines and content == "":
        return ProcessResult(text="", auto_fixes=0, flags=[])

    out_lines: list[str] = []
    auto_fixes = 0
    flags: list[tuple[int, str, str]] = []

    in_frontmatter = False
    frontmatter_seen = False
    in_fence = False

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not frontmatter_seen and stripped == "---":
            frontmatter_seen = True
            in_frontmatter = True
            out_lines.append(line)
            continue
        if in_frontmatter:
            out_lines.append(line)
            if stripped == "---":
                in_frontmatter = False
            continue

        if _FENCE_LINE.match(line):
            in_fence = not in_fence
            out_lines.append(line)
            continue

        if in_fence:
            out_lines.append(line)
            continue

        processed, fixes, line_flags = _process_prose_line(line.rstrip("\n"))
        auto_fixes += fixes
        for token, note in line_flags:
            flags.append((line_no, token, note))
        if line.endswith("\n"):
            processed += "\n"
        out_lines.append(processed)

    return ProcessResult(text="".join(out_lines), auto_fixes=auto_fixes, flags=flags)


def iter_md_paths(paths: list[Path]) -> list[Path]:
    collected: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix == ".md":
                collected.append(path)
            continue
        if path.is_dir():
            collected.extend(sorted(path.rglob("*.md")))
    return collected


def _scan_paths(paths: list[Path], *, quiet: bool) -> int:
    total_auto = 0
    total_flags = 0
    files_with_auto = 0

    for path in iter_md_paths(paths):
        content = path.read_text(encoding="utf-8")
        preview = _preview_auto_fixes(content)
        result = process_text(content)

        if preview:
            files_with_auto += 1
            total_auto += len(preview)
            if not quiet:
                for line_no, token, replacement in preview:
                    print(f"{path}:{line_no}: {token} → {replacement}")

        if result.flags:
            total_flags += len(result.flags)
            if not quiet:
                for line_no, token, note in result.flags:
                    print(f"{path}:{line_no}: {token} — {note}")

    if not quiet and (total_auto or total_flags):
        print(
            f"{total_auto} auto-fixable calque(s) across {files_with_auto} file(s); "
            f"{total_flags} flag(s) need review"
        )

    return 1 if total_auto or total_flags else 0


def _preview_auto_fixes(content: str) -> list[tuple[int, str, str]]:
    """Report auto-fixable calques without mutating (scan mode detail lines)."""
    lines = content.splitlines(keepends=True)
    hits: list[tuple[int, str, str]] = []

    in_frontmatter = False
    frontmatter_seen = False
    in_fence = False

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not frontmatter_seen and stripped == "---":
            frontmatter_seen = True
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue
        if _FENCE_LINE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for kind, segment in _split_inline_code(line.rstrip("\n")):
            if kind == "code":
                continue
            for pattern, replacement in _AUTO_FIX_PATTERNS:
                for match in pattern.finditer(segment):
                    hits.append(
                        (
                            line_no,
                            match.group(0),
                            _preserve_case(match.group(0), replacement),
                        )
                    )
    return hits


def _fix_paths(paths: list[Path], *, quiet: bool) -> int:
    total_auto = 0
    total_flags = 0
    files_changed = 0

    for path in iter_md_paths(paths):
        content = path.read_text(encoding="utf-8")
        result = process_text(content)
        if result.auto_fixes:
            files_changed += 1
            total_auto += result.auto_fixes
            path.write_text(result.text, encoding="utf-8")
        total_flags += len(result.flags)
        if not quiet:
            for line_no, token, note in result.flags:
                print(f"{path}:{line_no}: {token} — {note}")

    print(f"{total_auto} auto-fixes across {files_changed} files; {total_flags} flags need review")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Report calques and flags without editing")
    scan_parser.add_argument("paths", nargs="+", type=Path)
    scan_parser.add_argument("--quiet", action="store_true")

    fix_parser = subparsers.add_parser("fix", help="Apply auto-fixes in place")
    fix_parser.add_argument("paths", nargs="+", type=Path)
    fix_parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "scan":
        return _scan_paths(args.paths, quiet=args.quiet)
    return _fix_paths(args.paths, quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())

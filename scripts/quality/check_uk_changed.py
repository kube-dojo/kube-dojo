#!/usr/bin/env python3
"""CI wrapper for Ukrainian russicism checks on changed files.

Usage:
    .venv/bin/python scripts/quality/check_uk_changed.py <file1.md> <file2.md>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from checks import ukrainian

RUSSIAN_ONLY_CHARS_RE = re.compile(r"[ыёъэ]")


def _check_file_for_russian_chars(path: Path) -> list[str]:
    failures: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for match in RUSSIAN_ONLY_CHARS_RE.finditer(line):
            char = match.group(0)
            col = match.start() + 1
            failures.append(f"{path}:{line_no}:{col}: forbidden Russian-only character '{char}'")
    return failures


def _check_file_for_russicisms(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    failures: list[str] = []
    for check in ukrainian.check_russicisms(content):
        if check.check == "RUSSICISM" and not check.passed:
            failures.append(f"{path}: {check.message}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Ukrainian markdown files to check")
    args = parser.parse_args()

    errors: list[str] = []
    for path_str in args.paths:
        path = Path(path_str)
        if not path.is_file():
            errors.append(f"{path}: file not found")
            continue

        try:
            errors.extend(_check_file_for_russian_chars(path))
            errors.extend(_check_file_for_russicisms(path))
        except OSError as exc:
            errors.append(f"{path}: failed to read file: {exc}")

    for error in errors:
        print(error)

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

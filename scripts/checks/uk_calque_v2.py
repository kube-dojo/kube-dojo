#!/usr/bin/env python3
"""Detection-only CI guard for Russian calque patterns and structural bugs
in Ukrainian markdown translations (src/content/docs/uk/**/*.md).

Runs on list of changed files from argv.
Prints findings as: path:line: [CLASS/severity] <matched snippet>
Calque classes -> WARN (advisory, exit 0)
Structural -> FAIL (exit 1 if any)

Pure stdlib only.
"""

import re
import sys
from pathlib import Path

PARTICIPLE_STEMS = [
    "існуюч", "працююч", "оточуюч", "конкуруюч", "конфліктуюч",
    "взаємодіюч", "відволікаюч", "простоююч", "лякаюч", "блимаюч",
    "відкриваюч", "закриваюч", "бракуюч", "наступаюч", "деградуюч", "домінуюч",
]
ADJ_ENDINGS = r"(ий|ого|их|ій|ім|ою|у|і|е|им|ими|ому|а)"
PARTICIPLE_PATTERN = re.compile(
    rf"\b({'|'.join(PARTICIPLE_STEMS)}){ADJ_ENDINGS}\b",
    re.IGNORECASE,
)

ZNAKHODYTSYA_PATTERN = re.compile(
    r"\b(знаходиться|знаходяться|знаходитеся|знаходитесь|знаходитися)\b",
    re.IGNORECASE,
)

THE_FOLLOWING_NOUNS = r"(?:команд|рядк|пункт|елемент|приклад|крок|вимог)"
THE_FOLLOWING_PATTERN = re.compile(
    r"наступні\s+.{0,30}?" + THE_FOLLOWING_NOUNS,
    re.IGNORECASE,
)

MOJIBAKE_RE = re.compile(
    r"[\u0400-\u04FF][^\s\u0400-\u04FFa-zA-Z0-9'’ʼ\-—–—.,;:!?()[\]{}«»\"]+[\u0400-\u04FF]"
)

FALSE_POSITIVE_SUBSTRS = ["являється", "в якості", "вірний"]


def _is_false_positive(text: str) -> bool:
    lower = text.lower()
    return any(fp in lower for fp in FALSE_POSITIVE_SUBSTRS)


def process_file(path: Path) -> list[str]:
    """Return list of finding strings for the given file. Only processes uk .md files."""
    if not path.is_file() or path.suffix != ".md":
        return []
    path_str = str(path)
    if "src/content/docs/uk" not in path_str and "/uk/" not in path_str:
        return []

    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return []

    lines = content.splitlines(keepends=False)
    findings: list[str] = []

    # Calque patterns only in prose (skip fenced code blocks; strip inline code per line)
    in_fence = False
    fence_marker: str | None = None
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = stripped[:3]
                continue
        else:
            if fence_marker and stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            continue

        # prose line: remove inline code for matching
        prose_line = re.sub(r"`[^`\n]+`", "", line)

        # 1. Active present participles (adjective forms only)
        for match in PARTICIPLE_PATTERN.finditer(prose_line):
            snip = match.group(0)
            if _is_false_positive(snip) or _is_false_positive(prose_line):
                continue
            findings.append(f"{path}:{i}: [PARTICIPLE/WARN] {snip}")

        # 2. Знаходиться family
        for match in ZNAKHODYTSYA_PATTERN.finditer(prose_line):
            snip = match.group(0)
            if _is_false_positive(snip) or _is_false_positive(prose_line):
                continue
            findings.append(f"{path}:{i}: [ZNAKHODYTSYA/WARN] {snip}")

        # 3. "the following" calque (plural + enumeration noun within ~30 chars)
        for match in THE_FOLLOWING_PATTERN.finditer(prose_line):
            snip = match.group(0)
            if _is_false_positive(snip) or _is_false_positive(prose_line):
                continue
            findings.append(f"{path}:{i}: [THE_FOLLOWING/WARN] {snip}")

    # 4a. Duplicate consecutive ## headings (structural FAIL) — always scan
    prev_h = None
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("## "):
            if prev_h == stripped:
                findings.append(f"{path}:{i}: [DUPLICATE_HEADING/FAIL] {stripped}")
            prev_h = stripped

    # 4b. Mojibake (non-Cyrillic-non-Latin run embedded in Cyrillic word) — anywhere
    for i, line in enumerate(lines, 1):
        for match in MOJIBAKE_RE.finditer(line):
            snip = match.group(0)
            if _is_false_positive(snip) or _is_false_positive(line):
                continue
            findings.append(f"{path}:{i}: [MOJIBAKE/FAIL] {snip}")

    return findings


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: .venv/bin/python scripts/checks/uk_calque_v2.py <changed-uk-md> [..]", file=sys.stderr)
        return 0

    has_fail = False
    for arg in argv:
        p = Path(arg)
        file_findings = process_file(p)
        for finding in file_findings:
            print(finding)
            if "/FAIL]" in finding:
                has_fail = True

    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())

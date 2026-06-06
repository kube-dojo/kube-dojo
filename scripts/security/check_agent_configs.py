#!/usr/bin/env python3
"""Supply-chain DETECTION tripwire — issue #1812 (Miasma-class worm defense).

Miasma-class worms can inject backdoors into AI-coding-agent config files — content
that auto-executes when the repo is opened in an AI IDE (e.g. a piped-to-shell
dropper, or instructions telling the agent to run a remote payload). This tripwire
is the DETECT control for that variant. Prevention layers: `.npmrc ignore-scripts`
(#1813), lifecycle-script + provenance + lockfile-integrity tripwires (#1813/#1817).

Whole-file regex scan of agent-config paths for high-signal auto-exec compositions
only — NOT bare keywords (legitimate configs contain `npm run build`, localhost
`curl`, and the substring "eval" inside "evaluate").

Suppression (acknowledgement marker, NOT an authorization control):
  A finding is suppressed when its line OR the line immediately above contains the
  literal token `agent-config-allow`. An attacker could add the marker — the real
  value is forcing a human to review a flagged auto-exec line; the marker only
  records that review (same framing as the lockfile tripwire's `[lockfile-only]`).

Exit 0 = clean. Exit 1 = injection signal found. Exit 2 = error (fail-closed).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_REPORT = 50
MAX_SNIPPET = 120
SUPPRESSION_MARKER = "agent-config-allow"

EXCLUDE_DIRS = frozenset({".git", "node_modules", "dist", ".worktrees", "scripts"})
RECURSE_DIRS = frozenset({".claude", ".cursor", ".continue"})
SCAN_FILENAMES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        ".cursorrules",
        ".clinerules",
        ".windsurfrules",
        "copilot-instructions.md",
        ".aider.conf.yml",
    }
)

# High-signal auto-exec compositions — auditable / extensible.
PATTERNS: dict[str, re.Pattern[str]] = {
    # Downloader piped straight into an interpreter.
    "pipe-to-shell": re.compile(
        r"(?:curl|wget|fetch|Invoke-WebRequest|iwr)\b[^\n|]*\|\s*"
        r"(?:sudo\s+)?(?:sh|bash|zsh|python3?|node|perl|ruby)\b",
        re.IGNORECASE,
    ),
    # base64 decode piped to shell.
    "base64-to-shell": re.compile(
        r"base64\s+(?:-d|--decode)\b[^\n|]*\|\s*(?:sh|bash|zsh)\b",
        re.IGNORECASE,
    ),
    # Download then execute via && chain.
    "download-and-run": re.compile(
        r"(?:curl|wget)\b[^\n]*&&[^\n]*(?:\b(?:sh|bash)\b|chmod\s+\+x)",
        re.IGNORECASE,
    ),
    # Shell eval of a command substitution.
    "eval-cmd-subst": re.compile(
        r'eval\s*[("\x60][^\n)]*\$\(|eval\s+["\x60]?\$\(',
        re.IGNORECASE,
    ),
    # JS eval of decoded/obfuscated payload.
    "eval-decoded-js": re.compile(
        r"eval\s*\(\s*(?:atob|Buffer\.from|decodeURIComponent|"
        r"String\.fromCharCode|unescape)\b",
        re.IGNORECASE,
    ),
    # Node child_process exec/spawn on the same line.
    "child-process-exec": re.compile(
        r"child_process.*\b(?:exec|execSync|spawn)\b|"
        r"\b(?:exec|execSync|spawn)\b.*child_process",
        re.IGNORECASE,
    ),
    # PowerShell Invoke-Expression.
    "powershell-iex": re.compile(
        r"(?:Invoke-Expression|\bIEX\b)\b",
        re.IGNORECASE,
    ),
    # Python remote fetch + execute.
    "python-remote-exec": re.compile(
        r"(?:os\.system|subprocess\.(?:run|call|Popen)|\bexec\()[^\n]*"
        r"\b(?:urllib|requests|urlopen|http://|https://)",
        re.IGNORECASE,
    ),
}


def is_excluded(rel: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def should_scan_file(rel: Path) -> bool:
    if is_excluded(rel):
        return False
    if not rel.parts:
        return False
    if rel.parts[0] in RECURSE_DIRS:
        return True
    if rel.parts[:2] == (".github", "copilot-instructions.md"):
        return True
    return rel.name in SCAN_FILENAMES


def iter_scan_paths() -> list[Path]:
    found: list[Path] = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(REPO_ROOT)
        except ValueError:
            continue
        if should_scan_file(rel):
            found.append(path)
    return found


def truncate_snippet(text: str) -> str:
    line = text.strip()
    if len(line) <= MAX_SNIPPET:
        return line
    return line[: MAX_SNIPPET - 3] + "..."


def is_suppressed(lines: list[str], lineno: int) -> bool:
    """Suppress if marker on this line or the line immediately above."""
    idx = lineno - 1
    if 0 <= idx < len(lines) and SUPPRESSION_MARKER in lines[idx]:
        return True
    if idx > 0 and SUPPRESSION_MARKER in lines[idx - 1]:
        return True
    return False


Finding = tuple[Path, int, str, str]


def scan_file(path: Path) -> tuple[list[Finding], str | None]:
    rel = path.relative_to(REPO_ROOT)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [], f"cannot read {rel}: {exc}"

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [], f"skipped binary/undecodable: {rel}"

    lines = text.splitlines()
    findings: list[Finding] = []
    for lineno, line in enumerate(lines, start=1):
        for tag, pattern in PATTERNS.items():
            if pattern.search(line):
                if is_suppressed(lines, lineno):
                    continue
                findings.append((rel, lineno, tag, truncate_snippet(line)))
    return findings, None


def main(argv: list[str]) -> int:
    print("Agent-config injection tripwire — scanning AI IDE config paths.")

    if not REPO_ROOT.is_dir():
        print(f"ERROR: repo root not found: {REPO_ROOT}", file=sys.stderr)
        return 2

    try:
        paths = iter_scan_paths()
    except OSError as exc:
        print(f"ERROR: cannot walk repo tree: {exc}", file=sys.stderr)
        return 2

    all_findings: list[Finding] = []
    notes: list[str] = []

    for path in paths:
        findings, note = scan_file(path)
        all_findings.extend(findings)
        if note:
            notes.append(note)

    for note in notes:
        print(f"NOTE: {note}")

    if all_findings:
        print(
            f"\n  SUPPLY-CHAIN TRIPWIRE: {len(all_findings)} agent-config "
            f"auto-exec signal(s):",
            file=sys.stderr,
        )
        shown = all_findings[:MAX_REPORT]
        for rel, lineno, tag, snippet in shown:
            print(f"    [{tag}] {rel}:{lineno} — {snippet}", file=sys.stderr)
        remaining = len(all_findings) - len(shown)
        if remaining > 0:
            print(f"    … and {remaining} more finding(s)", file=sys.stderr)
        print(
            "\n  This is how the Miasma agent-config-injection variant plants "
            "auto-exec payloads in `.claude/`, `.cursor/`, `AGENTS.md`, "
            "`CLAUDE.md`, etc.\n"
            "  Remediation: remove the payload. If it is a legitimate "
            "documentation example reviewed by a human, add the literal marker "
            f"`{SUPPRESSION_MARKER}` on that line or the line above.\n"
            "  The marker is NOT an authorization control — it only records "
            "human review.",
            file=sys.stderr,
        )
        return 1

    print(f"OK — no agent-config auto-exec signals ({len(paths)} file(s) scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

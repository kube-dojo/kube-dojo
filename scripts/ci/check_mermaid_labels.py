#!/usr/bin/env python3
"""Flag unquoted parentheses in Mermaid flowchart node labels.

Background — bug autopsy (2026-06-06, issue #1823, surfaced while investigating
"mermaid flows not rendered" on ``platform/.../module-4.2-defense-in-depth``):

Mermaid diagrams render **client-side** (``src/scripts/mermaid-renderer.ts`` →
``mermaid.render``). Neither ``npm run build`` nor the site-health link check
ever parses the diagram source, so a *syntax* error in a diagram is invisible to
every existing gate — it only shows up as a broken render in the browser (the
renderer's error state un-hides the raw ``<pre>``, so the live site displays raw
mermaid code).

The dominant authoring mistake is an **unquoted ``(`` inside a ``[...]`` or
``{...}`` flowchart node label**. The flowchart parser treats ``(`` as the start
of a round-node shape and aborts the *whole* diagram::

    WebServer[Web Server (serves static files)]   ->  Parse error ... got 'PS'

The fix is to quote the label so the parser reads it as literal text::

    WebServer["Web Server (serves static files)"]

This check closes that gap deterministically. It is intentionally scoped to the
confirmed, prevalent failure (unquoted parens in square/rhombus labels) to keep
false positives at zero — valid shapes are explicitly *not* flagged:

  * quoted labels  ``["..."]`` / ``{"..."}``  (loose mode permits any char)
  * cylinder       ``[(...)]``
  * subroutine     ``[[...]]``
  * round node     ``(...)``  and stadium ``([...])`` / circle ``((...))``
  * hexagon        ``{{...}}``
  * any non-``flowchart``/``graph`` diagram type (state/sequence/class/er/…)

Usage::

    python scripts/ci/check_mermaid_labels.py [--root src/content/docs] [--selftest]

Exit codes: 0 = clean, 1 = one or more violations (or selftest fail).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOC_SUFFIXES = {".md", ".mdx"}

# Square node ``id[label]`` whose label is NOT quoted (``["``), NOT a cylinder
# (``[(``), NOT a subroutine (``[[``), and contains a paren before its ``]``.
# The label body excludes ``"`` so a *quoted* label anywhere in the construct
# (e.g. the parallelogram ``[/"...(...)..."/]``) does not match — only a truly
# unquoted paren is a parse breaker.
SQUARE = re.compile(r"[A-Za-z0-9_)\]]\[(?![\"(\[])[^\]\"]*[()][^\]\"]*\]")

# Rhombus/decision node ``id{label}`` whose label is NOT quoted (``{"``), NOT a
# hexagon (``{{``), and contains a paren before its ``}``.
RHOMBUS = re.compile(r"[A-Za-z0-9_)\]]\{(?![\"{])[^}\"]*[()][^}\"]*\}")

FLOWCHART_PREFIXES = ("flowchart", "graph")


def violations_in_line(line: str) -> bool:
    """True when ``line`` contains an unquoted-paren square or rhombus label."""
    return bool(SQUARE.search(line) or RHOMBUS.search(line))


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return (1-based line number, stripped line) hits inside flowchart fences."""
    hits: list[tuple[int, str]] = []
    in_mermaid = False
    type_decided = False
    is_flowchart = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            # Toggle fence state; reset per-fence type tracking either way.
            in_mermaid = not in_mermaid and stripped.startswith("```mermaid")
            type_decided = False
            is_flowchart = False
            continue
        if not in_mermaid or not stripped:
            continue
        # The first non-empty content line names the diagram type. Only the
        # flowchart parser has the unquoted-paren failure mode, and the header
        # line itself never carries a node label.
        if not type_decided:
            type_decided = True
            is_flowchart = stripped.lower().startswith(FLOWCHART_PREFIXES)
            continue
        if is_flowchart and violations_in_line(raw):
            hits.append((lineno, stripped))
    return hits


def scan(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in DOC_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "```mermaid" not in text:
            continue
        for lineno, snippet in scan_text(text):
            findings.append((path, lineno, snippet))
    return findings


def selftest() -> int:
    # Each snippet is the BODY of a ```mermaid fence; ``fence`` wraps it so the
    # scanner sees a real fenced block (it only inspects ```mermaid regions).
    def fence(body: str) -> str:
        return f"```mermaid\n{body}\n```\n"

    good = [
        'flowchart TD\n    A["Web Server (static)"] --> B',  # quoted
        "flowchart TD\n    A[(Database PostgreSQL)] --> B",  # cylinder
        "flowchart TD\n    A[[Subroutine call]] --> B",  # subroutine
        "graph LR\n    A((Internet)) --> B[Firewall]",  # circle + plain
        "flowchart TD\n    B(Cluster Autoscaler detects pending)",  # round node
        'flowchart TD\n    Q{"Need access (kernel)?"} --> Y',  # quoted rhombus
        'flowchart TD\n    E[/"Idea to prod (2h)"/] --> F',  # quoted parallelogram
        'stateDiagram-v2\n    state "Normal (CPU<80%)" as N',  # state diagram
        "flowchart TD\n    A[Plain label no parens] --> B",  # no parens
    ]
    bad = [
        "flowchart TD\n    Firewall --> W[Web Server (serves static files)]",
        "graph TD\n    A[Physical Disk (/dev/sda)] --> B",
        "graph TD\n    E --> C[/boot (ext4)]",  # square label starting with '/'
        "flowchart TD\n    VPA --> M[Auto: Update Pods (recreates)]",
        "flowchart TD\n    Q3{Is duration critical (no cold starts)?}",
    ]
    fails = 0
    for src in good:
        if scan_text(fence(src)):
            print(f"selftest FAIL: false positive on:\n    {src!r}")
            fails += 1
    for src in bad:
        if not scan_text(fence(src)):
            print(f"selftest FAIL: missed violation in:\n    {src!r}")
            fails += 1
    if fails:
        print(f"selftest: {fails} failure(s)")
        return 1
    print("selftest: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="src/content/docs", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    if not args.root.exists():
        print(f"error: root not found: {args.root}", file=sys.stderr)
        return 1

    findings = scan(args.root)
    if not findings:
        print(f"mermaid label check: OK (root={args.root})")
        return 0

    print(f"mermaid label check: {len(findings)} violation(s)\n")
    print("Unquoted '(' inside a flowchart [..] or {..} label aborts the whole")
    print('diagram. Quote the label, e.g.  Node["Web Server (static)"].\n')
    for path, line, snippet in findings:
        print(f"  {path}:{line}\n    {snippet}")
    print("\nFix: wrap each flagged label in double quotes.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

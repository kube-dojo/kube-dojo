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
# unquoted paren is a parse breaker. Group 1 = the char before ``[`` (a
# left-context guard, kept verbatim); group 2 = the label body, so ``--fix``
# can rewrite the match as ``<g1>["<g2>"]``.
SQUARE = re.compile(r"([A-Za-z0-9_)\]])\[(?![\"(\[])([^\]\"]*[()][^\]\"]*)\]")

# Rhombus/decision node ``id{label}`` whose label is NOT quoted (``{"``), NOT a
# hexagon (``{{``), and contains a paren before its ``}``. Same two groups.
RHOMBUS = re.compile(r"([A-Za-z0-9_)\]])\{(?![\"{])([^}\"]*[()][^}\"]*)\}")

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


def _quote_line(line: str) -> tuple[str, int]:
    """Wrap every unquoted-paren square/rhombus label on ``line`` in quotes.

    Uses the SAME ``SQUARE``/``RHOMBUS`` patterns as the detector, so a fixed
    line is, by construction, no longer a violation. Returns (new_line, count).
    """
    count = 0

    def sq(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f'{m.group(1)}["{m.group(2)}"]'

    def rh(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f'{m.group(1)}{{"{m.group(2)}"}}'

    line = SQUARE.sub(sq, line)
    line = RHOMBUS.sub(rh, line)
    return line, count


def fix_text(text: str) -> tuple[str, int]:
    """Return (new_text, num_fixes) with unquoted-paren labels quoted.

    Mirrors ``scan_text``'s fence/type scoping exactly — only lines inside a
    ```mermaid flowchart/graph fence are rewritten; everything else (prose,
    code, non-flowchart diagrams) is passed through byte-for-byte.
    """
    out: list[str] = []
    in_mermaid = False
    type_decided = False
    is_flowchart = False
    fixes = 0
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_mermaid = not in_mermaid and stripped.startswith("```mermaid")
            type_decided = False
            is_flowchart = False
            out.append(raw)
            continue
        if not in_mermaid or not stripped:
            out.append(raw)
            continue
        if not type_decided:
            type_decided = True
            is_flowchart = stripped.lower().startswith(FLOWCHART_PREFIXES)
            out.append(raw)
            continue
        if is_flowchart:
            new, n = _quote_line(raw)
            fixes += n
            out.append(new)
        else:
            out.append(raw)
    new_text = "\n".join(out)
    if text.endswith("\n"):
        new_text += "\n"
    return new_text, fixes


def fix(root: Path) -> list[tuple[Path, int]]:
    """Quote unquoted-paren labels in-place. Returns (path, count) per file."""
    changed: list[tuple[Path, int]] = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in DOC_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "```mermaid" not in text:
            continue
        new_text, n = fix_text(text)
        if n:
            path.write_text(new_text, encoding="utf-8")
            changed.append((path, n))
    return changed


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
        # --fix must leave a clean line byte-for-byte unchanged.
        fixed, n = fix_text(fence(src))
        if n or fixed != fence(src):
            print(f"selftest FAIL: --fix altered a clean line:\n    {src!r}")
            fails += 1
    for src in bad:
        if not scan_text(fence(src)):
            print(f"selftest FAIL: missed violation in:\n    {src!r}")
            fails += 1
        # --fix must make the violation disappear (scan finds nothing after).
        fixed, n = fix_text(fence(src))
        if n < 1 or scan_text(fixed):
            print(f"selftest FAIL: --fix did not resolve:\n    {src!r}\n    -> {fixed!r}")
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
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Quote unquoted-paren labels in place instead of just reporting.",
    )
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    if not args.root.exists():
        print(f"error: root not found: {args.root}", file=sys.stderr)
        return 1

    if args.fix:
        changed = fix(args.root)
        total = sum(n for _, n in changed)
        if not changed:
            print(f"mermaid label fix: nothing to fix (root={args.root})")
            return 0
        print(f"mermaid label fix: quoted {total} label(s) in {len(changed)} file(s)\n")
        for path, n in changed:
            print(f"  {path}: {n}")
        # Re-scan so the command's exit code reflects the post-fix state.
        return 1 if scan(args.root) else 0

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

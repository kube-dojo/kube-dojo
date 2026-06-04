#!/usr/bin/env python3
"""Validate the `lab.url` frontmatter convention across the curriculum.

Background — bug autopsy (2026-06-04, surfaced by PR #1742):
Module ``cka/.../module-1.3-helm.md`` shipped with
``lab.url: https://killercoda.com/playgrounds/scenario/kubernetes`` — a
*generic* KillerCoda playground instead of the module-specific scenario.
It was invisible to every existing gate because:

  * the value is frontmatter metadata, not teaching prose (reviewers skim it);
  * the bad URL returned **HTTP 200** — a real, live page, so the link checker
    (which only flags 404s) passed it; the defect was *semantic*, not broken;
  * ``verify_module.py`` never inspected ``lab.url``;
  * 268 of 269 modules followed the ``kubedojo/scenario/`` convention by
    authoring discipline alone — nothing *enforced* it.

This check closes that gap deterministically: every ``lab.url`` must point at a
module-specific ``https://killercoda.com/kubedojo/scenario/<slug>`` page. It is
stdlib-only (no PyYAML) so it can run in the dependency-free link-check job and
on every fork PR.

Usage::

    python scripts/ci/check_lab_urls.py [--root src/content/docs] [--selftest]

Exit codes: 0 = all conforming, 1 = one or more violations (or selftest fail).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# A conforming lab URL is the module-specific KillerCoda scenario under the
# kube-dojo org. Example: https://killercoda.com/kubedojo/scenario/cka-1.3-helm
CONVENTION = re.compile(
    r"^https://killercoda\.com/kubedojo/scenario/[a-z0-9]+(?:[._-][a-z0-9]+)*/?$"
)

DOC_SUFFIXES = {".md", ".mdx"}


def extract_lab_url(text: str) -> tuple[int, str] | None:
    """Return (1-based line number, url) for the frontmatter ``lab.url`` value.

    Returns None when the file has no frontmatter or no ``lab.url`` key. Parses
    only the leading ``---`` fenced block and tracks indentation so a stray
    ``url:`` elsewhere in the body is never mistaken for the lab URL.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    # Locate the closing frontmatter fence.
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None

    in_lab = False
    lab_indent = 0
    for i in range(1, end):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        key = raw.strip()
        if not in_lab:
            if key.startswith("lab:") and indent == 0:
                in_lab = True
                lab_indent = indent
            continue
        # Inside the lab block: a key at or below the lab indent ends it.
        if indent <= lab_indent:
            in_lab = False
            if key.startswith("lab:") and indent == 0:
                in_lab = True
            continue
        m = re.match(r"url:\s*(.+?)\s*$", key)
        if m:
            url = m.group(1).strip().strip("'\"")
            return (i + 1, url)
    return None


def scan(root: Path) -> list[tuple[Path, int, str]]:
    """Return a list of (path, line, url) violations under ``root``."""
    violations: list[tuple[Path, int, str]] = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in DOC_SUFFIXES or not path.is_file():
            continue
        found = extract_lab_url(path.read_text(encoding="utf-8"))
        if found is None:
            continue
        line, url = found
        if not CONVENTION.match(url):
            violations.append((path, line, url))
    return violations


def selftest() -> int:
    good = [
        "https://killercoda.com/kubedojo/scenario/cka-1.3-helm",
        "https://killercoda.com/kubedojo/scenario/cka-1.7-kubeadm",
        "https://killercoda.com/kubedojo/scenario/ckad-2.1-pods/",
        "https://killercoda.com/kubedojo/scenario/cks-5.2-application-failures",
    ]
    bad = [
        "https://killercoda.com/playgrounds/scenario/kubernetes",  # the #1742 bug
        "http://killercoda.com/kubedojo/scenario/cka-1.3-helm",  # not https
        "https://killercoda.com/someone-else/scenario/cka-1.3-helm",
        "https://example.com/kubedojo/scenario/cka-1.3-helm",
        "https://killercoda.com/kubedojo/scenario/",  # no slug
    ]
    fails = 0
    for u in good:
        if not CONVENTION.match(u):
            print(f"selftest FAIL: expected conforming, rejected: {u}")
            fails += 1
    for u in bad:
        if CONVENTION.match(u):
            print(f"selftest FAIL: expected violation, accepted: {u}")
            fails += 1

    sample = "---\ntitle: T\nlab:\n  id: x\n  url: https://killercoda.com/playgrounds/scenario/kubernetes\n---\nbody\nurl: https://decoy.example.com\n"
    parsed = extract_lab_url(sample)
    if parsed != (5, "https://killercoda.com/playgrounds/scenario/kubernetes"):
        print(f"selftest FAIL: parser returned {parsed!r}")
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

    violations = scan(args.root)
    if not violations:
        print(f"lab.url convention check: OK (root={args.root})")
        return 0

    print(f"lab.url convention check: {len(violations)} violation(s)\n")
    print("Every `lab.url` must be a module-specific KillerCoda scenario:")
    print("  https://killercoda.com/kubedojo/scenario/<module-slug>\n")
    for path, line, url in violations:
        print(f"  {path}:{line}\n    got: {url}")
    print(
        "\nFix: point each lab at its own kube-dojo scenario "
        "(see any sibling module for the slug pattern)."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

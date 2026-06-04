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
module-specific ``https://killercoda.com/kubedojo/scenario/<slug>`` page.

Frontmatter is parsed with a real YAML loader (PyYAML, already a repo
dependency) rather than a hand-rolled scanner. The first draft used a
line-based parser; codex R1 review (PR #1790) showed it failed open on
flow-style ``lab: {url: ...}`` mappings and mis-captured inline ``# comments``.
A real parser eliminates that whole class of edge cases.

Usage::

    python scripts/ci/check_lab_urls.py [--root src/content/docs] [--selftest]

Exit codes: 0 = all conforming, 1 = one or more violations (or selftest fail).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# A conforming lab URL is the module-specific KillerCoda scenario under the
# kube-dojo org. Example: https://killercoda.com/kubedojo/scenario/cka-1.3-helm
CONVENTION = re.compile(
    r"^https://killercoda\.com/kubedojo/scenario/[a-z0-9]+(?:[._-][a-z0-9]+)*/?$"
)

DOC_SUFFIXES = {".md", ".mdx"}


def extract_lab_url(text: str) -> str | None:
    """Return the frontmatter ``lab.url`` value, or None when absent.

    Parses the leading ``---`` fenced YAML block with a real loader, so
    block-style, flow-style (``lab: {url: ...}``), quoting, and inline
    comments are all handled correctly. Returns None when there is no
    frontmatter, no ``lab`` mapping, or no ``url`` key — and also when the
    block is not parseable YAML (other gates own malformed frontmatter).
    """
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    lab = data.get("lab")
    if not isinstance(lab, dict):
        return None
    url = lab.get("url")
    if not isinstance(url, str):
        return None
    return url.strip()


def find_line(text: str, url: str) -> int:
    """Best-effort 1-based line number of ``url`` in the source (0 if absent)."""
    for i, line in enumerate(text.splitlines(), start=1):
        if url in line:
            return i
    return 0


def scan(root: Path) -> list[tuple[Path, int, str]]:
    """Return a list of (path, line, url) violations under ``root``."""
    violations: list[tuple[Path, int, str]] = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in DOC_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        url = extract_lab_url(text)
        if url is None:
            continue
        if not CONVENTION.match(url):
            violations.append((path, find_line(text, url), url))
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

    # Parser cases, including the flow-style + inline-comment edge cases codex
    # R1 flagged (PR #1790). All must extract the URL so CONVENTION can judge it.
    bad_url = "https://killercoda.com/playgrounds/scenario/kubernetes"
    good_url = "https://killercoda.com/kubedojo/scenario/cka-1.3-helm"
    parser_cases: list[tuple[str, str | None]] = [
        # block style with a decoy url: in the body
        (f"---\ntitle: T\nlab:\n  id: x\n  url: {bad_url}\n---\nbody\nurl: https://decoy.example.com\n", bad_url),
        # flow-style mapping on the lab line (previously failed OPEN -> None)
        (f"---\ntitle: T\nlab: {{id: x, url: '{bad_url}'}}\n---\n", bad_url),
        # inline YAML comment after the url (previously captured into the value)
        (f"---\ntitle: T\nlab:\n  id: x\n  url: {good_url}  # canonical scenario\n---\n", good_url),
        # double-quoted value
        (f'---\ntitle: T\nlab:\n  id: x\n  url: "{good_url}"\n---\n', good_url),
        # no lab block at all
        ("---\ntitle: T\n---\nbody\n", None),
        # no frontmatter
        ("body only\nurl: https://decoy.example.com\n", None),
    ]
    for i, (src, expected) in enumerate(parser_cases):
        got = extract_lab_url(src)
        if got != expected:
            print(f"selftest FAIL: parser case {i}: expected {expected!r}, got {got!r}")
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
        loc = f"{path}:{line}" if line else str(path)
        print(f"  {loc}\n    got: {url}")
    print(
        "\nFix: point each lab at its own kube-dojo scenario "
        "(see any sibling module for the slug pattern)."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

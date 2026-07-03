#!/usr/bin/env python3
"""Deterministic complexity-marker normalizer.

Canonical complexity marker (locked convention, see docs/quality-rubric.md and
issues #2141 #2146 #2181 #2187 #2195): the tier token is a **backticked bracketed
tier** — one of ``[QUICK]`` ``[MEDIUM]`` ``[COMPLEX]`` ``[ADVANCED]`` ``[EXPERT]`` —
i.e. written as `` `[MEDIUM]` `` inside the module's header/banner line. The single
source of truth is the BODY marker; the legacy ``complexity:`` frontmatter key is
dropped.

What this tool normalizes (deterministic, token-only, container-preserving):

  1. Bare-word tiers          -> backticked bracket, mapped to the controlled vocab:
       Quick/Medium/Complex/Advanced/Expert (any caps)  -> `[SAME]`
       Intermediate                                      -> `[MEDIUM]`
       Beginner                                          -> `[QUICK]`
       ranges map to their CEILING (spaced OR hyphenated):
       "Beginner to intermediate" / "Beginner-to-..."    -> `[MEDIUM]`
       "Intermediate to Advanced" / "Intermediate-to-Advanced" -> `[ADVANCED]`
  2. Bare bracket   `[MEDIUM]`  (no backticks)            -> `` `[MEDIUM]` ``
  3. Non-canonical `[BEGINNER]` tier                      -> `` `[QUICK]` `` (mapped)
  4. Top-level `complexity:` frontmatter key             -> removed (body is SoT)

What it deliberately does NOT do (out of scope; would restructure internally
consistent per-track layouts and is not asked for by the driving issues):

  * It does not move a marker into a blockquote. A ``## Complexity: [MEDIUM]``
    heading or a ``| Complexity | ... |`` table cell keeps its container; only the
    tier TOKEN inside it is canonicalized.
  * It does not re-LEVEL a module based on content judgement. ``[QUICK]`` stays
    ``[QUICK]`` even where the audit (e.g. #2141) flags a genuine mislabel — those
    are tracked as separate content follow-ups.

Guards against false positives on prose:
  * The "Complexity" label is matched case-sensitively (capital C); lowercase prose
    "complexity" is ignored.
  * Tier spellings are title/upper case; lowercase prose "advanced" is ignored.
  * Only a FRAMED marker (bold ``**Complexity**``, or a line led by ``>``/``#``/``|``)
    within the first BODY_SCAN_LINES body lines is rewritten, and only the FIRST such
    marker per file. A bare line-leading ``Complexity: Advanced users…`` prose
    sentence is NOT framed, so it is left untouched.

Usage:
  python scripts/normalize_complexity_markers.py            # dry-run report
  python scripts/normalize_complexity_markers.py --write    # apply in place
  python scripts/normalize_complexity_markers.py --check    # exit 1 if any drift
  python scripts/normalize_complexity_markers.py --root src/content/docs/cloud
"""
from __future__ import annotations

import argparse
import os
import re
import sys

DEFAULT_ROOT = "src/content/docs"
BODY_SCAN_LINES = 25  # marker banners always sit at the very top of the body

SANCTIONED = ("QUICK", "MEDIUM", "COMPLEX", "ADVANCED", "EXPERT")
_TIER_RANK = {"QUICK": 0, "MEDIUM": 1, "COMPLEX": 2, "ADVANCED": 3, "EXPERT": 4}

# Bare-word tier synonyms (audience words included). A range "X to Y" (spaced or
# hyphenated) maps to its CEILING = the higher-ranked of the two tiers.
_WORD_TO_TIER = {
    "quick": "QUICK",
    "beginner": "QUICK",
    "medium": "MEDIUM",
    "intermediate": "MEDIUM",
    "complex": "COMPLEX",
    "advanced": "ADVANCED",
    "expert": "EXPERT",
}
_TIER_WORD_ALT = "Beginner|Intermediate|Advanced|Complex|Medium|Quick|Expert"
# Range separator: "to" flanked by whitespace and/or hyphens (spaced OR hyphenated).
_RANGE_RE = re.compile(r"^(?P<a>[a-z]+)[\s\-]+to[\s\-]+(?P<b>[a-z]+)$", re.IGNORECASE)

_LABEL = r"(?P<label>(?:[#>\s\-\|]*)?\*{0,2}Complexity\*{0,2}\s*[:|]?\*{0,2}\s*)"
_VALUE = (
    r"(?P<value>"
    r"`\[(?:QUICK|MEDIUM|COMPLEX|ADVANCED|EXPERT|BEGINNER|INTERMEDIATE)\]`"   # backticked bracket
    r"|\[(?:QUICK|MEDIUM|COMPLEX|ADVANCED|EXPERT|BEGINNER|INTERMEDIATE)\]"     # bare bracket
    # range: two tier words joined by " to " or "-to-" (MUST precede single words)
    r"|(?i:" + _TIER_WORD_ALT + r")[\s\-]+to[\s\-]+(?i:" + _TIER_WORD_ALT + r")"
    r"|QUICK|MEDIUM|COMPLEX|ADVANCED|EXPERT"                                   # bareword upper
    r"|Intermediate|Beginner|Advanced|Complex|Medium|Quick|Expert"            # bareword title
    r")"
)
# Case-sensitive: capital "Complexity" + title/upper single-tier spellings exclude
# prose; the range group is scoped-insensitive so "Beginner to intermediate" matches.
_MARKER_RE = re.compile(_LABEL + _VALUE)
_FM_COMPLEXITY_RE = re.compile(r"^complexity\s*:", re.IGNORECASE)  # top-level key only


def canonical_tier(raw: str) -> str:
    """Map a raw tier token to one of the 5 sanctioned tiers (upper, unbracketed).

    A range ("X to Y" / "X-to-Y") maps to its ceiling (higher-ranked tier).
    """
    s = raw.strip().strip("`").strip("[]").strip()
    m = _RANGE_RE.match(s)
    if m:
        t1 = _WORD_TO_TIER.get(m.group("a").lower())
        t2 = _WORD_TO_TIER.get(m.group("b").lower())
        if t1 and t2:
            return t1 if _TIER_RANK[t1] >= _TIER_RANK[t2] else t2
    low = s.lower()
    if low in _WORD_TO_TIER:
        return _WORD_TO_TIER[low]
    up = s.upper()
    if up in SANCTIONED:
        return up
    raise ValueError(f"unmappable tier token: {raw!r}")


def _is_framed(line: str, m: re.Match) -> bool:
    """A genuine marker banner is bold-framed (**Complexity**) or on a >/#/| line.

    A bare line-leading "Complexity: Advanced users …" prose sentence is NOT framed,
    so it is left untouched (guards the docstring's no-prose-rewrite contract).
    """
    lstr = line.lstrip()
    if lstr[:1] in (">", "#", "|"):
        return True
    if "**Complexity" in m.group("label") or "Complexity**" in line[: m.end("label")]:
        return True
    return False


def normalize_marker_line(line: str):
    """Return (new_line, changed, before_token, after_token) for a marker line."""
    m = _MARKER_RE.search(line)
    if not m or not _is_framed(line, m):
        return line, False, None, None
    raw_val = m.group("value")
    tier = canonical_tier(raw_val)
    canonical = f"`[{tier}]`"
    if raw_val == canonical:
        return line, False, raw_val, canonical
    new_line = line[: m.start("value")] + canonical + line[m.end("value") :]
    return new_line, new_line != line, raw_val, canonical


def _split_frontmatter(lines):
    """Return (fm_start, fm_end) line indices of the YAML frontmatter, or (-1,-1)."""
    if not lines or lines[0].strip() != "---":
        return -1, -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return 0, i
    return -1, -1


def process_file(path: str):
    """Return dict describing the change (or None if nothing to do)."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    fm_start, fm_end = _split_frontmatter(lines)
    changed = False
    result = {"path": path, "fm_removed": None, "marker": None}

    # 1) drop top-level frontmatter complexity: key
    if fm_end > 0:
        new_fm = []
        for ln in lines[fm_start + 1 : fm_end]:
            if _FM_COMPLEXITY_RE.match(ln):
                result["fm_removed"] = ln.strip()
                changed = True
                continue
            new_fm.append(ln)
        if result["fm_removed"] is not None:
            lines = lines[: fm_start + 1] + new_fm + lines[fm_end:]
            # recompute fm_end after removal
            fm_start, fm_end = _split_frontmatter(lines)

    body_start = fm_end + 1 if fm_end > 0 else 0
    # 2) normalize the FIRST framed marker token within the top of the body
    scanned = 0
    for idx in range(body_start, len(lines)):
        if scanned >= BODY_SCAN_LINES:
            break
        scanned += 1
        new_line, ln_changed, before, after = normalize_marker_line(lines[idx])
        m = _MARKER_RE.search(lines[idx])
        if m and _is_framed(lines[idx], m):
            # found the marker banner (whether or not it needs changing) -> stop
            if ln_changed:
                lines[idx] = new_line
                result["marker"] = (before, after, lines[idx].rstrip("\n"))
                changed = True
            else:
                result["marker"] = (before, after, None)  # already canonical
            break

    if not changed:
        return None
    result["new_content"] = "".join(lines)
    return result


def iter_md_files(root: str):
    for dirpath, _dirs, filenames in os.walk(root):
        # exclude Ukrainian translation lane
        if os.sep + "uk" + os.sep in dirpath + os.sep or dirpath.rstrip(os.sep).endswith(os.sep + "uk"):
            continue
        parts = os.path.relpath(dirpath, root).split(os.sep)
        if parts and parts[0] == "uk":
            continue
        for fn in filenames:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Normalize complexity markers to canonical form.")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="content root to scan")
    ap.add_argument("--write", action="store_true", help="apply changes in place")
    ap.add_argument("--check", action="store_true", help="exit 1 if any drift found (no write)")
    args = ap.parse_args(argv)

    root = args.root
    if not os.path.isdir(root):
        # allow running from repo root or elsewhere
        alt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), root)
        if os.path.isdir(alt):
            root = alt
        else:
            print(f"ERROR: root not found: {args.root}", file=sys.stderr)
            return 2

    changes = []
    for path in sorted(iter_md_files(root)):
        try:
            res = process_file(path)
        except ValueError as e:
            print(f"SKIP {path}: {e}", file=sys.stderr)
            continue
        if res:
            changes.append(res)

    n_fm = sum(1 for c in changes if c["fm_removed"])
    n_marker = sum(1 for c in changes if c["marker"] and c["marker"][2])
    for c in changes:
        rel = os.path.relpath(c["path"], root)
        bits = []
        if c["fm_removed"]:
            bits.append(f"fm-drop({c['fm_removed']})")
        if c["marker"] and c["marker"][2]:
            bits.append(f"{c['marker'][0]} -> {c['marker'][1]}")
        print(f"{rel}: {'; '.join(bits)}")

    print(
        f"\n{len(changes)} files changed  "
        f"({n_marker} marker tokens, {n_fm} frontmatter keys dropped)",
        file=sys.stderr,
    )

    if args.write:
        for c in changes:
            with open(c["path"], "w", encoding="utf-8") as f:
                f.write(c["new_content"])
        print(f"WROTE {len(changes)} files", file=sys.stderr)
        return 0

    if args.check:
        return 1 if changes else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

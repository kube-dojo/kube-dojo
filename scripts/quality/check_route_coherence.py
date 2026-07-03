#!/usr/bin/env python3
"""Deterministic route-coherence linter (issue #2151).

Catches the cross-module / route-integrity defect class the per-module QA pipeline
is structurally blind to (a backward "Next Module" link still *resolves*, so
site-health passes it). Complements `check_site_health.py` (which checks that links
resolve) by checking the *relationships between* modules and their section route.

Checks
------
ERROR (fail CI):
  * next-broken     — a module's "Next Module" link target does not resolve to a
                      known page.
  * next-backward   — the Next link points to an EARLIER module in the same section
                      (or to itself). This is the #2143 disease (philosophy 1.4 ->
                      back to Cloud Native 101; planning 1.4 -> nothing forward).

WARNING (report, do not fail):
  * next-skip       — within a section, the Next link skips the immediate successor
                      module (points further ahead, or leaves the section while
                      earlier siblings remain) — the intra-section chain break GLM
                      missed (planning 1.4 -> 1.6 leaving 1.5 orphaned).
  * next-missing     — a non-terminal module has no Next link at all.
  * terminus-orphan — the LAST module of a section has no forward Next link
                      (dead-end terminus).
  * count-drift     — a section index's module TABLE row count != on-disk
                      module-*.md count.
  * marker-drift    — a complexity marker is not canonical (delegates to
                      normalize_complexity_markers).
  * marker-dual     — complexity declared in BOTH frontmatter and body.

A committed baseline (`scripts/quality/route_coherence_baseline.json`) records
known violations so CI fails only on NEW ones (ratchet). Regenerate with
`--update-baseline` as the curriculum lane drains the inventory.

Usage:
  python scripts/quality/check_route_coherence.py            # CI mode (ratchet, ERROR-gated)
  python scripts/quality/check_route_coherence.py --all      # print every finding
  python scripts/quality/check_route_coherence.py --json     # machine-readable
  python scripts/quality/check_route_coherence.py --update-baseline
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "src" / "content" / "docs"
BASELINE_PATH = REPO_ROOT / "scripts" / "quality" / "route_coherence_baseline.json"

ERROR_RULES = {"next-broken", "next-backward"}


@dataclass
class Finding:
    rule: str
    path: str  # docs-relative
    line: int
    detail: str
    level: str = "error"

    def key(self) -> str:
        return f"{self.rule}|{self.path}|{self.detail}"


@dataclass
class Module:
    path: Path
    rel: str  # docs-relative posix
    slug: str  # route slug, no leading/trailing slash
    section: str  # parent dir docs-relative
    number: tuple  # numeric module ordering key, or () if unparsable


# ── frontmatter / slug ────────────────────────────────────────────────────────

def _read_frontmatter(text: str):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else None


def _path_derived_slug(md: Path) -> str:
    slug = str(md.relative_to(DOCS_DIR).with_suffix("")).replace("\\", "/")
    if slug == "index":
        return ""
    if slug.endswith("/index"):
        return slug[: -len("/index")]
    return slug


def _slug_for(md: Path, fm: str) -> str:
    m = re.search(r"^slug:\s*(.+)$", fm, re.MULTILINE)
    if m:
        return m.group(1).strip().strip('"').strip("'").strip("/")
    return _path_derived_slug(md).strip("/")


_NUM_RE = re.compile(r"module-(\d+(?:\.\d+)*)")


def _module_number(name: str) -> tuple:
    m = _NUM_RE.search(name)
    if not m:
        return ()
    return tuple(int(p) for p in m.group(1).split("."))


# ── Next-Module link extraction ───────────────────────────────────────────────

# Navigation cue for the module's forward link. Deliberately EXCLUDES "Next Steps"
# (a further-reading/exercise content section, not module nav).
_NEXT_MARKER = re.compile(
    r"(?im)^\s*(?:#{1,4}\s*|\*\*)?"
    r"(?:Next Module|What'?s Next|Up Next|Next Up|Where to Next|Continue to|Continue your|▶|➡)\b"
)
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# link labels that are NOT the forward-nav link: previous, related reading, back-to
_SKIP_LABEL_RE = re.compile(r"(?i)\b(prev|previous|related|see also|back to|return to)\b")
_FWD_LABEL_RE = re.compile(r"(?i)\b(next|continue|forward|onward)\b")


def _extract_next_href(lines: list[str]) -> tuple[str | None, int]:
    """Return (href, 1-based line) for the module's Next link, or (None, -1)."""
    # search from the bottom: the nav footer is at the end
    for i in range(len(lines) - 1, -1, -1):
        if _NEXT_MARKER.search(lines[i]):
            # collect links from this line and the following few non-empty lines
            for j in range(i, min(i + 4, len(lines))):
                if j > i and _NEXT_MARKER.search(lines[j]):
                    continue
                for lm in _LINK_RE.finditer(lines[j]):
                    link_text, href = lm.group(1), lm.group(2).strip()
                    # skip anchor-only / external / mailto
                    if href.startswith(("#", "http://", "https://", "mailto:")):
                        continue
                    # Skip a "previous"/"related"/"back to" link unless a forward cue
                    # (next/continue) is present. The label may sit BEFORE the link
                    # (**Related**: [x]) or INSIDE the link text ([Previous](x)), so
                    # check both.
                    context = lines[j][: lm.start()] + " " + link_text
                    if _SKIP_LABEL_RE.search(context) and not _FWD_LABEL_RE.search(context):
                        continue
                    return href, j + 1
            return None, i + 1
    return None, -1


def _apply_relative(base_parts: list[str], href: str) -> str:
    parts = list(base_parts)
    for seg in href.strip("/").split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts).strip("/")


def _resolve_candidates(href: str, source_slug: str) -> list[str]:
    """Candidate route slugs for a link href, best-first.

    Starlight serves `a/b/module-x.md` at URL `/a/b/module-x/`, so relative links
    resolve treating the module's OWN slug as a directory (primary model). Some
    authors write file-relative links (parent dir); that is the fallback. Mirrors
    check_site_health.check_link_targets so "resolves" means the same thing here.
    """
    href = href.split("#", 1)[0].split("?", 1)[0].strip()
    if not href:
        return []
    if href.startswith("/"):
        return [href.strip("/")]
    seg = source_slug.split("/")
    # File-relative FIRST (matches check_site_health order): a `./` link targets the
    # section index (parent dir), not the module itself. `../module-x` links fail
    # file-relative (they'd need a track-level module-x) and fall through to the
    # Starlight directory model, which is correct for them.
    return [
        _apply_relative(seg[:-1], href),   # file-relative (source's parent dir)
        _apply_relative(seg, href),        # Starlight directory model (slug is a dir)
    ]


# ── load modules + route map ──────────────────────────────────────────────────

def load_modules():
    modules: dict[str, Module] = {}  # rel -> Module
    slug_to_rel: dict[str, str] = {}
    all_slugs: set[str] = set()
    for md in sorted(DOCS_DIR.rglob("*.md")):
        rel = md.relative_to(DOCS_DIR).as_posix()
        if rel.startswith("uk/") or rel.endswith(".staging.md"):
            continue
        fm = _read_frontmatter(md.read_text(errors="replace")) or ""
        slug = _slug_for(md, fm)
        all_slugs.add(slug)
        slug_to_rel[slug] = rel
        if md.name.startswith("module-"):
            modules[rel] = Module(
                path=md,
                rel=rel,
                slug=slug,
                section=md.parent.relative_to(DOCS_DIR).as_posix(),
                number=_module_number(md.name),
            )
    return modules, slug_to_rel, all_slugs


# ── checks ────────────────────────────────────────────────────────────────────

def check_next_links(modules, slug_to_rel, all_slugs, findings):
    # group modules by section for sequence reasoning
    by_section: dict[str, list[Module]] = {}
    for mod in modules.values():
        by_section.setdefault(mod.section, []).append(mod)
    for mods in by_section.values():
        mods.sort(key=lambda m: (m.number or (9999,)))

    for mod in modules.values():
        lines = mod.path.read_text(errors="replace").splitlines()
        href, ln = _extract_next_href(lines)
        siblings = by_section[mod.section]
        is_last = siblings and siblings[-1].rel == mod.rel

        if href is None:
            if is_last:
                findings.append(Finding("terminus-orphan", mod.rel, ln if ln > 0 else 1,
                                        "last module of section has no forward Next link",
                                        level="warning"))
            else:
                findings.append(Finding("next-missing", mod.rel, 1,
                                        "non-terminal module has no Next link",
                                        level="warning"))
            continue

        candidates = _resolve_candidates(href, mod.slug)
        resolved = next((c for c in candidates if c in all_slugs), None)
        if resolved is None:
            findings.append(Finding("next-broken", mod.rel, ln,
                                    f"Next link '{href}' -> {candidates} does not resolve",
                                    level="error"))
            continue

        target_rel = slug_to_rel.get(resolved)
        target_mod = modules.get(target_rel) if target_rel else None
        if target_mod is None:
            # points to an index/section page — acceptable (cross-section terminus)
            continue

        # direction check only when both are in the same section and numbered
        if target_mod.section == mod.section and mod.number and target_mod.number:
            if target_mod.number <= mod.number:
                findings.append(Finding("next-backward", mod.rel, ln,
                                        f"Next -> {target_mod.rel} is backward/self "
                                        f"({target_mod.number} <= {mod.number})",
                                        level="error"))
                continue
            # skip check: is there an immediate successor that was bypassed?
            idx = siblings.index(mod)
            if idx + 1 < len(siblings):
                expected = siblings[idx + 1]
                if expected.rel != target_mod.rel:
                    findings.append(Finding("next-skip", mod.rel, ln,
                                            f"Next -> {target_mod.number} skips immediate "
                                            f"successor {expected.number}",
                                            level="warning"))
        elif target_mod.section != mod.section and not is_last:
            # leaves the section while later siblings remain
            findings.append(Finding("next-skip", mod.rel, ln,
                                    f"Next leaves section to {target_mod.rel} but this is "
                                    f"not the last module of {mod.section}",
                                    level="warning"))


# module basename in any href (relative OR absolute): [..](/a/b/module-x/) or (../module-x/)
_MODULE_LINK_RE = re.compile(r"\]\([^)]*?(module-[\w.][\w.\-]*?)/?\)")


def check_counts(modules, findings):
    by_section: dict[str, list[str]] = {}
    for mod in modules.values():
        by_section.setdefault(mod.section, []).append(mod.path.stem)
    for section, disk_stems in by_section.items():
        index = DOCS_DIR / section / "index.md"
        if not index.exists():
            continue
        text = index.read_text(errors="replace")
        disk_set = set(disk_stems)
        # distinct module basenames the index links to that actually live in this section
        referenced = {b for b in _MODULE_LINK_RE.findall(text) if b in disk_set}
        if not referenced:
            continue  # index has no module table (e.g. a hub that only links sections)
        if referenced != disk_set:
            missing = sorted(disk_set - referenced)
            extra = sorted(referenced - disk_set)  # always empty by construction; kept for clarity
            detail = (f"index links {len(referenced)} of {len(disk_set)} section modules"
                      + (f"; not listed: {missing[:6]}" if missing else "")
                      + (f"; stale: {extra[:6]}" if extra else ""))
            findings.append(Finding("count-drift", f"{section}/index.md", 1, detail,
                                    level="warning"))


def check_markers(findings):
    """Delegate complexity-marker drift + dual-source to the normalizer if present."""
    ncm_path = REPO_ROOT / "scripts" / "normalize_complexity_markers.py"
    if not ncm_path.exists():
        return  # normalizer not landed yet (separate PR); skip gracefully
    import importlib.util
    spec = importlib.util.spec_from_file_location("_ncm", ncm_path)
    ncm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ncm)
    for md in sorted(DOCS_DIR.rglob("*.md")):
        rel = md.relative_to(DOCS_DIR).as_posix()
        if rel.startswith("uk/") or rel.endswith(".staging.md"):
            continue
        try:
            res = ncm.process_file(str(md))
        except ValueError:
            continue
        if not res:
            continue
        if res.get("fm_removed"):
            findings.append(Finding("marker-dual", rel, 1,
                                    "complexity declared in frontmatter AND body",
                                    level="warning"))
        if res.get("marker") and res["marker"][2]:
            findings.append(Finding("marker-drift", rel, 1,
                                    f"non-canonical marker {res['marker'][0]!r}",
                                    level="warning"))


# ── baseline ratchet ──────────────────────────────────────────────────────────

def load_baseline() -> set[str]:
    if not BASELINE_PATH.exists():
        return set()
    return set(json.loads(BASELINE_PATH.read_text()).get("violations", []))


def run_all():
    modules, slug_to_rel, all_slugs = load_modules()
    findings: list[Finding] = []
    check_next_links(modules, slug_to_rel, all_slugs, findings)
    check_counts(modules, findings)
    check_markers(findings)
    findings.sort(key=lambda f: (f.level != "error", f.rule, f.path))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="print every finding (incl. warnings + baselined)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--update-baseline", action="store_true", help="rewrite the baseline from current findings")
    args = ap.parse_args(argv)

    findings = run_all()

    if args.update_baseline:
        errors = sorted(f.key() for f in findings if f.rule in ERROR_RULES)
        BASELINE_PATH.write_text(json.dumps({
            "_comment": "Known route-coherence ERROR violations. CI fails only on NEW ones. "
                        "Drain this as the curriculum lane fixes links; regenerate with "
                        "check_route_coherence.py --update-baseline.",
            "violations": errors,
        }, indent=2) + "\n")
        print(f"baseline updated: {len(errors)} ERROR violations recorded", file=sys.stderr)
        return 0

    baseline = load_baseline()
    new_errors = [f for f in findings if f.rule in ERROR_RULES and f.key() not in baseline]

    if args.json:
        print(json.dumps({
            "findings": [f.__dict__ for f in findings],
            "new_errors": [f.__dict__ for f in new_errors],
        }, indent=2))
    else:
        shown = findings if args.all else [f for f in findings if f.rule in ERROR_RULES]
        for f in shown:
            tag = "NEW" if (f.rule in ERROR_RULES and f.key() not in baseline) else "   "
            print(f"[{f.level.upper():7}] {tag} {f.rule}: {f.path}:{f.line} — {f.detail}")
        n_err = sum(1 for f in findings if f.rule in ERROR_RULES)
        n_warn = sum(1 for f in findings if f.rule not in ERROR_RULES)
        print(f"\n{len(findings)} findings ({n_err} error-class, {n_warn} warning-class); "
              f"{len(new_errors)} NEW error(s) beyond baseline of {len(baseline)}.", file=sys.stderr)

    return 1 if new_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Catch valid-but-wrong arXiv citations: an arXiv link that returns HTTP 200 but
points to the WRONG paper.

The failure mode (issue #1991): an author writes the correct paper *title* in the
markdown link text but a wrong arXiv *ID*. The URL still resolves, so
``verify_module.py``'s ``sources_all_reachable`` gate, link checkers, and the Astro
Zod schema all pass it. Only an ID->title correspondence check catches it. This is
the same blind-spot class as the killercoda ``lab.url`` bug (valid URL, wrong
content) closed by ``scripts/ci/check_lab_urls.py``.

Design goals: PRECISE (≈0 false positives) so it stays load-bearing.
- Only checks markdown links whose link TEXT is *title-like* (a real claimed title),
  after stripping ``Author et al. — `` / ``Author, YYYY — `` prefixes.
- Skips prose-phrase links, bare-URL link text, ``arXiv:1234.5678`` link text,
  author-year-only citations, and short tags (e.g. ``SimCLR``, ``HNSW paper``) —
  those carry no title to validate, so they cannot be checked this way.
- Fetches the real arXiv title and FAILs only on near-zero token overlap.
- Network-resilient: fetch errors are reported as warnings, never hard failures
  (so the gate does not flake on arXiv downtime).
- Escape hatch: put ``<!-- arxiv-ok: 1234.5678 -->`` anywhere in the file to
  whitelist a specific ID (e.g. a legitimately terse title).

Usage:
  check_arxiv_citations.py <file.md> [more.md ...]   # explicit files
  check_arxiv_citations.py --changed                 # changed *.md vs origin/main
  check_arxiv_citations.py --all                     # every src/content/docs/*.md
Exit 1 on any confirmed mismatch.
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "src" / "content" / "docs"

LINK_RE = re.compile(r"\[([^\]]+)\]\((?:https?://)?arxiv\.org/abs/(\d{4}\.\d{4,5})\)")
OK_RE = re.compile(r"<!--\s*arxiv-ok:\s*(\d{4}\.\d{4,5})\s*-->")
# author/citation prefixes we strip to expose the title portion of the link text
PREFIX_RE = re.compile(
    r"^[A-Z][^—:]*?et al\.?(,?\s*\d{4})?\s*[—:-]\s*|"  # "Gama et al. — Title" / "X et al.: Title"
    r"^[A-Z][A-Za-z.'’-]+\s*(&|and)\s*[A-Z][A-Za-z.'’-]+,?\s*\d{4}\s*[—:-]\s*"  # "Kipf & Welling, 2017 — Title"
)
AUTHOR_YEAR_ONLY = re.compile(r"^[A-Z][^()]*?et al\.?,?\s*\(?\d{4}\)?\.?$|^[A-Z][A-Za-z.'’-]+\s*(&|and)\s*[A-Z][A-Za-z.'’-]+,?\s*\(?\d{4}\)?$")
BARE_URL = re.compile(r"^(arxiv\.org|https?://|arxiv:)", re.I)
# link text that is a method/acronym name, not a paper title: "... (HyDE)", "... (GAN)"
METHOD_PAREN = re.compile(r"\([A-Z][A-Za-z0-9]{1,7}\)\s*$")
# prose-sentence signals — a citation sentence, not a title (e.g. "...OpenAI published the X paper")
PROSE_VERB = re.compile(r"\b(published|introduc\w+|propos\w+|demonstrat\w+|catalog\w+|describ\w+|present\w+|showed)\b", re.I)
STOP = {"the", "a", "an", "of", "for", "and", "with", "to", "in", "on", "your",
        "using", "via", "from", "paper", "original", "et", "al", "approach", "study"}


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _norm_tokens(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return {w for w in s.split() if len(w) > 3 and w not in STOP}


def _title_like(text: str) -> str | None:
    """Return the claimed-title portion if the link text is a checkable formal title.

    Returns None (skip) for prose phrases, bare URLs, short tags, and author/citation
    text — none of which carry a paper title we can validate against arXiv. Keeping
    this strict is what holds the false-positive rate at ~0.
    """
    t = PREFIX_RE.sub("", text).strip().strip("*").strip()
    if BARE_URL.match(t) or AUTHOR_YEAR_ONLY.match(text.strip()):
        return None
    # After stripping a leading author prefix, any remaining author-citation signal
    # (" & ", "et al", a trailing "(YYYY)") means this is a citation label, not a title.
    if " & " in t or re.search(r"\bet al\b", t, re.I) or re.search(r"\(\s*\d{4}\s*\)\s*$", t):
        return None
    # method/acronym names and prose sentences are not paper titles → cannot validate
    if METHOD_PAREN.search(t) or PROSE_VERB.search(t):
        return None
    words = [w for w in re.split(r"\s+", t) if w]
    if len(words) < 4:  # short tags / single-concept labels carry no checkable title
        return None
    # A real paper title cited in prose is Title Case; lowercase prose phrases are not.
    sig = [w for w in words if len(re.sub(r"[^A-Za-z]", "", w)) > 3]
    if not sig:
        return None
    capped = sum(1 for w in sig if w[:1].isupper())
    if capped / len(sig) < 0.5:
        return None
    return t


def fetch_title(arxiv_id: str, cache: dict) -> str | None:
    if arxiv_id in cache:
        return cache[arxiv_id]
    title = None
    try:
        req = urllib.request.Request(
            f"https://arxiv.org/abs/{arxiv_id}", headers={"User-Agent": "Mozilla/5.0"})
        body = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        m = re.search(r"<title>\s*\[[0-9.]+\]\s*(.*?)</title>", body, re.S)
        if m:
            title = html.unescape(re.sub(r"\s+", " ", m.group(1)).strip())
    except Exception as exc:  # network/transport — warn, do not hard-fail
        cache[arxiv_id] = ("ERR", str(exc))
        return cache[arxiv_id]
    cache[arxiv_id] = title
    return title


def check_file(path: Path, cache: dict) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    whitelisted = set(OK_RE.findall(text))
    violations, warnings = [], []
    seen = set()
    for claimed, arxiv_id in LINK_RE.findall(text):
        title = _title_like(claimed)
        if title is None or arxiv_id in whitelisted:
            continue
        key = (arxiv_id, title)
        if key in seen:
            continue
        seen.add(key)
        real = fetch_title(arxiv_id, cache)
        if isinstance(real, tuple):  # ERR
            warnings.append(f"{_rel(path)}: could not verify {arxiv_id} ({real[1]})")
            continue
        if real is None:
            warnings.append(f"{_rel(path)}: no title parsed for {arxiv_id}")
            continue
        ct, rt = _norm_tokens(title), _norm_tokens(real)
        if not ct:
            continue
        overlap = len(ct & rt) / len(ct)
        if overlap < 0.30:
            violations.append(
                f"{_rel(path)}: arXiv {arxiv_id} claimed=\"{title[:60]}\" "
                f"but real title=\"{real[:60]}\" (overlap {overlap:.0%}) "
                f"— wrong ID? add `<!-- arxiv-ok: {arxiv_id} -->` if intentional.")
    return violations, warnings


def changed_md() -> list[Path]:
    try:
        subprocess.run(["git", "-C", str(REPO_ROOT), "fetch", "-q", "origin", "main"],
                       check=False, timeout=60)
        base = subprocess.run(["git", "-C", str(REPO_ROOT), "merge-base", "HEAD", "origin/main"],
                              capture_output=True, text=True).stdout.strip() or "origin/main"
        out = subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--name-only", base, "--"],
                             capture_output=True, text=True).stdout
    except Exception:
        out = ""
    return [REPO_ROOT / p for p in out.split() if p.endswith(".md") and (REPO_ROOT / p).exists()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--changed", action="store_true", help="check changed *.md vs origin/main")
    ap.add_argument("--all", action="store_true", help="check all docs *.md")
    args = ap.parse_args()

    if args.all:
        files = sorted(DOCS.rglob("*.md"))
    elif args.changed:
        files = changed_md()
    else:
        files = [Path(f) for f in args.files]
    files = [f.resolve() for f in files if f.exists() and f.suffix == ".md"]
    if not files:
        print("check_arxiv_citations: no markdown files to check.")
        return 0

    cache: dict = {}
    all_v, all_w = [], []
    for f in files:
        v, w = check_file(f, cache)
        all_v += v
        all_w += w
    for w in all_w:
        print(f"WARN  {w}")
    for v in all_v:
        print(f"FAIL  {v}")
    print(f"\ncheck_arxiv_citations: {len(files)} file(s), "
          f"{len(all_v)} mismatch(es), {len(all_w)} unverifiable.")
    return 1 if all_v else 0


if __name__ == "__main__":
    sys.exit(main())

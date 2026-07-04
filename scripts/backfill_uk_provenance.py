#!/usr/bin/env python3
"""Backfill `en_commit` provenance into UK translations that lack it.

Some UK files were translated in older sweeps that never recorded which EN
commit they were translated from, so `detect_uk_divergence.py` cannot compute
their drift (they land in `missing_en_commit` and their staleness is invisible).

For each such file we record, as its baseline, the EN counterpart's commit that
was HEAD at the time of the UK file's own last commit — i.e. the EN state the
translation was made against, as closely as git can reconstruct it. Re-running
the divergence detector afterwards then yields the TRUE stale set.

Usage:
    python scripts/backfill_uk_provenance.py --dry-run     # preview counts
    python scripts/backfill_uk_provenance.py               # write frontmatter
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UK_ROOT = REPO_ROOT / "src/content/docs/uk"
DIVERGENCE = REPO_ROOT / ".pipeline/translation_divergence.json"


def _sh(*args: str) -> str:
    return subprocess.run(
        list(args), cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout.strip()


def _en_path_for(uk_path: Path) -> Path:
    rel = uk_path.relative_to(UK_ROOT)
    return REPO_ROOT / "src/content/docs" / rel


def _en_exists_at_head(en_path: Path) -> bool:
    rel = en_path.relative_to(REPO_ROOT)
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{rel}"],
            cwd=REPO_ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


def _baseline_en_commit(uk_path: Path, en_path: Path) -> str | None:
    rel_uk = str(uk_path.relative_to(REPO_ROOT))
    rel_en = str(en_path.relative_to(REPO_ROOT))
    uk_date = _sh("git", "log", "-1", "--format=%cI", "--", rel_uk)
    if not uk_date:
        return None
    commit = _sh("git", "log", "-1", "--format=%H", f"--before={uk_date}", "--", rel_en)
    if not commit:
        # EN created after the UK's last edit (rare) — use the EN's earliest commit.
        commit = _sh("git", "log", "--format=%H", "--", rel_en).splitlines()[-1:] or [""]
        commit = commit[0]
    return commit or None


def _inject_en_commit(text: str, sha: str) -> str | None:
    """Insert `en_commit: <sha>` into the YAML frontmatter. Returns None if the
    file has no frontmatter or already has en_commit."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = m.group(1)
    if re.search(r"^en_commit:", fm, re.M):
        return None  # already present
    new_fm = fm + f"\nen_commit: {sha}"
    return text[: m.start(1)] + new_fm + text[m.end(1) :]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = json.loads(DIVERGENCE.read_text())
    missing = data.get("missing_en_commit", [])
    backfilled, orphans, skipped = [], [], []

    for entry in missing:
        uk_path = REPO_ROOT / entry["uk_path"]
        en_path = _en_path_for(uk_path)
        if not _en_exists_at_head(en_path):
            orphans.append(entry["module_key"])
            continue
        sha = _baseline_en_commit(uk_path, en_path)
        if not sha:
            skipped.append(entry["module_key"])
            continue
        text = uk_path.read_text()
        new_text = _inject_en_commit(text, sha)
        if new_text is None:
            skipped.append(entry["module_key"])
            continue
        if not args.dry_run:
            uk_path.write_text(new_text)
        backfilled.append((entry["module_key"], sha[:8]))

    print(f"missing_en_commit  : {len(missing)}")
    print(f"backfilled         : {len(backfilled)}{' (DRY-RUN, not written)' if args.dry_run else ''}")
    print(f"orphans (EN gone)  : {len(orphans)}")
    print(f"skipped (no fm/date): {len(skipped)}")
    if orphans:
        print("  orphan UK (EN deleted/moved — separate problem):")
        for k in orphans[:15]:
            print(f"    - {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

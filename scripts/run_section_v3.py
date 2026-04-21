#!/usr/bin/env python3
"""One-shot v3 citation-pipeline section runner.

v3 = citation-backfill pipeline (per-claim research + verify + inject
+ audit, driven by scripts/pipeline_v3.py). v4 (thin-module body
expansion) gets its own `run_section_v4.py` when implemented.

Runs the full end-to-end flow for a curriculum section:

    1. Preflight — git tree clean, Codex auth reachable.
    2. pipeline_v3_section.run_section_pipeline — discovery + per-module
       research/verify/inject/audit/auto-apply. Writes pool, seeds,
       module edits.
    3. Cleanup — delete any .staging.md seed files that leaked in.
    4. Per-module commits — one commit for the pool, one per module
       whose status is in COMMITTABLE. Inject-failed modules get
       their seed changes reverted (the pipeline's new seed isn't
       trustworthy when inject refused the edits).
    5. `npm run build` — hard stop if the build is not clean.
    6. `git push origin main`.

Usage:
    .venv/bin/python scripts/run_section_v3.py <section-path>
    .venv/bin/python scripts/run_section_v3.py --auto-pick --only-uncited
    .venv/bin/python scripts/run_section_v3.py <section-path> --no-push
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

from citation_backfill import REPO_ROOT, flat_section_name  # type: ignore  # noqa: E402
from pipeline_v3_section import run_section_pipeline  # type: ignore  # noqa: E402
from section_source_discovery import (  # type: ignore  # noqa: E402
    list_section_modules,
    normalize_section_key,
)

COMMITTABLE = {"clean", "residuals_queued"}
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"
QUALITY_SCORES_URL = "http://127.0.0.1:8768/api/quality/scores"
_QUALITY_TITLE_RE = re.compile(r'^title:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
_MODULE_NUMBER_RE = re.compile(r"module-([0-9]+(?:\.[0-9]+)*)")
_CERT_TRACKS = frozenset({"cka", "ckad", "cks", "kcna", "kcsa"})
_QUALITY_TRACK_LABELS = {
    "ai": "AI",
    "ai-ml-engineering": "AI/ML Engineering",
    "cloud": "Cloud",
    "linux": "Linux",
    "on-premises": "On-Premises",
    "platform": "Platform",
    "prerequisites": "Prerequisites",
}
_QUALITY_ISSUE_CACHE: dict[str, str] | None = None
_QUALITY_ISSUE_CACHE_LOADED = False


def _run(cmd: list[str], *, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def _git_clean() -> tuple[bool, str]:
    out = _run(["git", "status", "--porcelain"], check=False)
    dirty = [line for line in out.stdout.splitlines() if line and not line.startswith("??")]
    return (not dirty, out.stdout)


def _codex_auth_live(timeout_s: int = 25) -> bool:
    try:
        result = subprocess.run(
            ["codex", "exec", "--full-auto", "--skip-git-repo-check"],
            input='return the JSON {"ok":true}',
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return result.returncode == 0 and '{"ok":true}' in result.stdout


def _module_has_sources(module_key: str) -> bool:
    module_path = DOCS_ROOT / f"{module_key}.md"
    if not module_path.exists():
        return False
    body = module_path.read_text(encoding="utf-8", errors="replace")
    # Match `## Sources` at line start, allowing trailing whitespace or
    # heading-level variants the normaliser might emit.
    for line in body.splitlines():
        stripped = line.strip()
        if stripped == "## Sources" or stripped.startswith("## Sources "):
            return True
    return False


def _section_module_keys(section_key: str) -> list[str]:
    return [
        path.relative_to(DOCS_ROOT).with_suffix("").as_posix()
        for path in list_section_modules(section_key)
    ]


def _uncited_modules(section_key: str) -> list[str]:
    return [key for key in _section_module_keys(section_key) if not _module_has_sources(key)]


def _quality_track_label(rel: Path) -> str:
    parts = rel.parts
    if not parts:
        return ""
    first = parts[0]
    if len(parts) >= 2 and first == "k8s" and parts[1] in _CERT_TRACKS:
        return parts[1].upper()
    top = _QUALITY_TRACK_LABELS.get(first, first.replace("-", " ").title())
    if len(parts) >= 2 and not parts[1].startswith(("module-", "part")):
        return f"{top} {parts[1].replace('-', ' ').title()}"
    return top


def _module_quality_label(module_key: str) -> str:
    rel = Path(f"{module_key}.md")
    module_path = DOCS_ROOT / rel
    title = rel.stem.replace("-", " ").title()
    if module_path.exists():
        text = module_path.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---\n") and "\n---\n" in text[4:]:
            frontmatter = text[4:].split("\n---\n", 1)[0]
            match = _QUALITY_TITLE_RE.search(frontmatter)
            if match:
                title = match.group(1).strip() or title
    title = re.sub(r"^Module\s+[0-9]+(?:\.[0-9]+)*:\s*", "", title).strip()
    track = _quality_track_label(rel)
    number_match = _MODULE_NUMBER_RE.search(rel.stem)
    if track.lower() in _CERT_TRACKS and number_match:
        return f"{track} {number_match.group(1)}: {title}"
    return f"{track}: {title}"


def _iter_quality_score_entries(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    entries: list[dict] = []
    seen: set[str] = set()
    modules = payload.get("modules")
    if isinstance(modules, list):
        for entry in modules:
            if not isinstance(entry, dict):
                continue
            module = entry.get("module")
            if isinstance(module, str) and module not in seen:
                seen.add(module)
                entries.append(entry)
    for key, value in payload.items():
        if key == "modules" or not isinstance(value, list):
            continue
        for entry in value:
            if not isinstance(entry, dict):
                continue
            module = entry.get("module")
            if isinstance(module, str) and module not in seen:
                seen.add(module)
                entries.append(entry)
    return entries


def _load_quality_issue_map(timeout_s: float = 5.0) -> dict[str, str] | None:
    global _QUALITY_ISSUE_CACHE, _QUALITY_ISSUE_CACHE_LOADED
    if _QUALITY_ISSUE_CACHE_LOADED:
        return _QUALITY_ISSUE_CACHE
    try:
        with urlopen(QUALITY_SCORES_URL, timeout=timeout_s) as response:
            payload = json.load(response)
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(
            f"warning: content-stable gate failed open; could not load {QUALITY_SCORES_URL}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        _QUALITY_ISSUE_CACHE = None
        _QUALITY_ISSUE_CACHE_LOADED = True
        return None
    issues: dict[str, str] = {}
    for entry in _iter_quality_score_entries(payload):
        module = entry.get("module")
        issue = entry.get("primary_issue")
        if isinstance(module, str):
            issues[module] = issue if isinstance(issue, str) else ""
    _QUALITY_ISSUE_CACHE = issues
    _QUALITY_ISSUE_CACHE_LOADED = True
    return issues


def _content_stable_modules(
    module_keys: list[str],
    *,
    log_skips: bool,
) -> list[str]:
    issues_by_label = _load_quality_issue_map()
    if issues_by_label is None:
        return module_keys

    kept: list[str] = []
    for module_key in module_keys:
        label = _module_quality_label(module_key)
        if label not in issues_by_label:
            print(
                f"warning: {module_key} missing from /api/quality/scores; content-stable gate failing open",
                file=sys.stderr,
                flush=True,
            )
            kept.append(module_key)
            continue
        issue = issues_by_label[label]
        if issue == "no citations":
            kept.append(module_key)
            continue
        if log_skips:
            shown_issue = issue or "<empty>"
            print(f"skip: {module_key} primary_issue={shown_issue} — parks for v4", flush=True)
    return kept


def _candidate_sections(min_uncited: int = 3, *, content_stable_only: bool = False) -> list[tuple[str, int, int]]:
    """Scan every section directory under DOCS_ROOT; return (section_key,
    eligible_uncited_count, total_count) for those with >= min_uncited
    modules still missing `## Sources`. When content_stable_only is set,
    only modules whose quality-score primary_issue is exactly
    "no citations" count toward the threshold. Sorted highest-uncited
    first so the densest backlog comes first.
    """
    candidates: list[tuple[str, int, int]] = []
    seen: set[str] = set()
    for path in DOCS_ROOT.rglob("module-*.md"):
        if path.name.endswith(".staging.md"):
            continue
        section_dir = path.parent
        section_key = section_dir.relative_to(DOCS_ROOT).as_posix()
        # Skip Ukrainian translations — citations land on the English
        # source modules; UK translations sync separately via uk_sync.
        if section_key.startswith("uk/"):
            continue
        if section_key in seen:
            continue
        seen.add(section_key)
        modules = _section_module_keys(section_key)
        uncited_keys = [m for m in modules if not _module_has_sources(m)]
        if content_stable_only:
            uncited_keys = _content_stable_modules(uncited_keys, log_skips=False)
        uncited = len(uncited_keys)
        if uncited >= min_uncited:
            candidates.append((section_key, uncited, len(modules)))
    candidates.sort(key=lambda t: (-t[1], t[0]))
    return candidates


def auto_pick_section(min_uncited: int = 3, *, content_stable_only: bool = False) -> str | None:
    """Pick the section most in need of citation work.

    Ranking is simple uncited-count desc, path asc. The scorer's
    display names (e.g. "Platform Toolkits: Harbor - Enterprise
    Container Registry") don't map cleanly to directory paths, so
    the API-score weighting tried earlier produced false matches
    on substring overlaps. Plain uncited count is the honest signal
    and already accounts for critical modules — a section with 12
    uncited modules will also have many critical ones by definition.
    """
    candidates = _candidate_sections(
        min_uncited=min_uncited,
        content_stable_only=content_stable_only,
    )
    if not candidates:
        return None
    section_key, uncited, total = candidates[0]
    count_label = "content-stable uncited" if content_stable_only else "uncited"
    print(
        f"→ auto-pick: {section_key} ({uncited}/{total} modules {count_label})",
        flush=True,
    )
    return section_key


def _preflight(allow_dirty: bool) -> bool:
    print("→ preflight: git clean?", flush=True)
    clean, detail = _git_clean()
    if not clean and not allow_dirty:
        print(f"✗ uncommitted tracked changes; commit or stash first:\n{detail}", file=sys.stderr)
        return False
    print("  ok" if clean else "  dirty but --allow-dirty set", flush=True)

    print("→ preflight: codex auth live?", flush=True)
    if not _codex_auth_live():
        print("✗ codex exec smoke test failed. run `codex login` then retry.", file=sys.stderr)
        return False
    print("  ok", flush=True)
    return True


def _revert_seed(module_key: str) -> None:
    seed_rel = f"docs/citation-seeds/{flat_section_name(module_key)}.json"
    seed_path = REPO_ROOT / seed_rel
    if not seed_path.exists():
        return
    # If the seed is tracked and modified, revert. If it's brand-new
    # (untracked), delete — it's stale from a pipeline run whose inject
    # step refused to apply the edits.
    r = _run(["git", "ls-files", "--error-unmatch", seed_rel], check=False)
    if r.returncode == 0:
        _run(["git", "checkout", "--", seed_rel])
        print(f"  reverted tracked seed: {seed_rel}", flush=True)
    else:
        seed_path.unlink()
        print(f"  deleted untracked seed: {seed_rel}", flush=True)


def _remove_staging_seeds(section_key: str) -> None:
    """Delete any seed JSONs whose module-key ends with `.staging`.

    The section pipeline now filters `.staging.md` at enumeration time
    (scripts/section_source_discovery.list_section_modules), but a
    seed could still land here if a prior pipeline run wrote one and
    the module-filter change hadn't landed yet.
    """
    seed_dir = REPO_ROOT / "docs" / "citation-seeds"
    prefix = flat_section_name(section_key)
    removed = []
    for seed in seed_dir.glob(f"{prefix}-*.staging.json"):
        seed.unlink()
        removed.append(seed.name)
    if removed:
        print(f"  removed {len(removed)} staging seed(s): {', '.join(removed)}", flush=True)


def _commit_pool(section_key: str) -> None:
    pool_rel = f"docs/citation-pools/{flat_section_name(section_key)}.json"
    if not (REPO_ROOT / pool_rel).exists():
        print(f"  no pool file to commit at {pool_rel}", flush=True)
        return
    _run(["git", "add", pool_rel])
    # If nothing staged (pool unchanged), skip.
    staged = _run(["git", "diff", "--cached", "--name-only"], check=False).stdout.strip()
    if pool_rel not in staged:
        print(f"  pool unchanged, no commit: {pool_rel}", flush=True)
        return
    msg = (
        f"content(citation-pool): {section_key.split('/')[-1]} section pool\n\n"
        "Discovered by scripts/section_source_discovery.py via "
        "scripts/run_section.py.\n\n"
        "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    )
    _run(["git", "commit", "-m", msg])
    print(f"  committed pool: {pool_rel}", flush=True)


def _commit_module(module_key: str) -> bool:
    module_rel = f"src/content/docs/{module_key}.md"
    seed_rel = f"docs/citation-seeds/{flat_section_name(module_key)}.json"
    if not (REPO_ROOT / module_rel).exists():
        print(f"  skip {module_key} — module file missing", flush=True)
        return False
    # Stage what exists; missing seeds are tolerated (pipeline may have
    # skipped research and reused a tracked seed).
    _run(["git", "add", module_rel])
    if (REPO_ROOT / seed_rel).exists():
        _run(["git", "add", seed_rel])
    staged = _run(["git", "diff", "--cached", "--name-only"], check=False).stdout.strip().splitlines()
    if module_rel not in staged:
        print(f"  {module_key} — no module diff, nothing to commit", flush=True)
        return False
    msg = (
        f"content(citations): apply v3 section pipeline to {module_key}\n\n"
        "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
    )
    _run(["git", "commit", "-m", msg])
    print(f"  committed: {module_key}", flush=True)
    return True


def _build() -> bool:
    print("→ npm run build", flush=True)
    t0 = time.time()
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    dt = round(time.time() - t0, 1)
    if result.returncode != 0:
        print(f"✗ build failed in {dt}s", file=sys.stderr)
        print(result.stdout[-3000:], file=sys.stderr)
        print(result.stderr[-2000:], file=sys.stderr)
        return False
    # grab the pages count if present, as a sanity line
    last_lines = "\n".join(result.stdout.splitlines()[-3:])
    print(f"  build ok in {dt}s\n  {last_lines}", flush=True)
    return True


def _push() -> bool:
    print("→ git push origin main", flush=True)
    result = _run(["git", "push", "origin", "main"], check=False)
    if result.returncode != 0:
        print(f"✗ push failed:\n{result.stderr}", file=sys.stderr)
        return False
    print(f"  {result.stderr.strip().splitlines()[-1]}", flush=True)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="End-to-end section pipeline: preflight → run → commit → build → push",
    )
    parser.add_argument(
        "section_path",
        nargs="?",
        help="Section path under src/content/docs/. Omit if using --auto-pick.",
    )
    parser.add_argument(
        "--auto-pick",
        action="store_true",
        help="Auto-select the densest critical section still needing citations.",
    )
    parser.add_argument(
        "--only-uncited",
        action="store_true",
        help="Restrict the per-module stage to modules that lack `## Sources`. Pool is still rebuilt from the whole section.",
    )
    parser.add_argument(
        "--min-uncited",
        type=int,
        default=3,
        help="With --auto-pick, ignore sections with fewer uncited modules than this (default: 3).",
    )
    parser.add_argument(
        "--content-stable-only",
        action="store_true",
        help="Skip modules unless /api/quality/scores reports primary_issue == 'no citations'.",
    )
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--max-batch-chars", type=int, default=28_000)
    parser.add_argument("--no-build", action="store_true", help="Skip npm run build")
    parser.add_argument("--no-push", action="store_true", help="Skip git push")
    parser.add_argument("--no-commit", action="store_true", help="Run pipeline only, do not commit")
    parser.add_argument("--allow-dirty", action="store_true", help="Proceed even if tracked files are dirty")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args(argv)

    if args.auto_pick:
        if args.section_path:
            print("→ --auto-pick ignored because an explicit section_path was given", flush=True)
            section_key = normalize_section_key(args.section_path)
        else:
            picked = auto_pick_section(
                min_uncited=args.min_uncited,
                content_stable_only=args.content_stable_only,
            )
            if not picked:
                count_label = "content-stable uncited" if args.content_stable_only else "uncited"
                print(
                    f"→ auto-pick found no section with >= {args.min_uncited} {count_label} modules; queue may be drained",
                    flush=True,
                )
                return 0
            section_key = picked
    else:
        if not args.section_path:
            parser.error("section_path is required unless --auto-pick is set")
        section_key = normalize_section_key(args.section_path)

    print(f"== run_section: {section_key} ==", flush=True)

    if not args.skip_preflight and not _preflight(args.allow_dirty):
        return 2

    modules_override: list[str] | None = None
    if args.only_uncited:
        uncited = _uncited_modules(section_key)
        all_keys = _section_module_keys(section_key)
        print(
            f"→ --only-uncited: {len(uncited)}/{len(all_keys)} modules lack ## Sources",
            flush=True,
        )
        if not uncited:
            print("→ nothing to do; section is fully cited", flush=True)
            return 0
        modules_override = uncited

    if args.content_stable_only:
        candidate_keys = modules_override or _section_module_keys(section_key)
        kept = _content_stable_modules(candidate_keys, log_skips=True)
        if modules_override is not None:
            print(
                f"→ --content-stable-only: {len(kept)}/{len(candidate_keys)} selected modules are stable enough for v3",
                flush=True,
            )
        else:
            print(
                f"→ --content-stable-only: {len(kept)}/{len(candidate_keys)} section modules are stable enough for v3",
                flush=True,
            )
        if not kept:
            print("→ nothing to do; selected modules park for v4", flush=True)
            return 0
        modules_override = kept

    result = run_section_pipeline(
        section_key,
        batch_size=args.batch_size,
        max_batch_chars=args.max_batch_chars,
        modules_override=modules_override,
    )
    print(json.dumps(
        {k: v for k, v in result.items() if k != "results"},
        indent=2,
        ensure_ascii=False,
    ), flush=True)
    if not result.get("ok"):
        print("✗ pipeline returned not-ok", file=sys.stderr)
        return 3

    if args.no_commit:
        print("→ --no-commit set, leaving working tree dirty for review", flush=True)
        return 0

    print("→ cleaning staging seeds (defensive)", flush=True)
    _remove_staging_seeds(section_key)

    print("→ committing pool", flush=True)
    _commit_pool(section_key)

    print("→ committing per-module", flush=True)
    committed = 0
    failed = 0
    for entry in result.get("results", []):
        module_key = entry["module_key"]
        status = entry.get("status")
        if status in COMMITTABLE:
            if _commit_module(module_key):
                committed += 1
        else:
            print(f"  skip {module_key} — status={status}; reverting seed", flush=True)
            _revert_seed(module_key)
            failed += 1

    print(f"→ committed={committed} skipped={failed}", flush=True)

    if committed == 0:
        print("→ no commits to push; done", flush=True)
        return 0

    if not args.no_build and not _build():
        print("✗ build failed — commits stay local, fix then `git push` manually", file=sys.stderr)
        return 4

    if not args.no_push and not _push():
        return 5

    print(f"✓ section done: {committed} committed, {failed} skipped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

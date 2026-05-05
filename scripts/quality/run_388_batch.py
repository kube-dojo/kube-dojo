#!/usr/bin/env python3
"""End-to-end #388 batch runner — single entry point for solo operation.

Chains the existing building blocks against the local API:
  1. Bucket build  → query /api/quality/upgrade-plan + /api/quality/board
                     filter by track or top-level alias, skip already-shipped
                     and modules currently leased by other workers
  2. Dispatch      → dispatch_388_pilot.main() (codex writer + gemini review + auto-merge)
  3. Cleanup       → cleanup_388_pilot.main() (re-verify, clear flags, remove worktrees)
  4. Summary       → per-event counts + held PRs needing manual triage

Held-PR triage stays MANUAL (per C3, deliberated in ab discuss day3-388 2026-05-02):
trivial nits inline-fix + merge; structural failures re-dispatch codex on the existing
branch with the gemini review as the brief.

Tracks come in two flavours:

  Fine-grained (matches /api/quality/upgrade-plan `track` field):
      KCNA  KCSA  CKA  CKAD  CKS  "Platform Toolkits"  "Linux Foundations" ...

  Top-level aliases (expand to all modules under a filesystem prefix):
      certifications        → k8s/      (all cert tracks)
      platform-engineering  → platform/
      fundamentals          → prerequisites/  +  linux/
      cloud                 → cloud/
      on-premises           → on-premises/
      ai                    → ai/
      ai-ml-engineering     → ai-ml-engineering/

Common usage:

  # Auto-build bucket from API for the KCSA cert track
  .venv/bin/python scripts/quality/run_388_batch.py --track KCSA

  # Top-level alias — all critical modules under platform/
  .venv/bin/python scripts/quality/run_388_batch.py --track platform-engineering

  # Use a curated list (skip auto-build)
  .venv/bin/python scripts/quality/run_388_batch.py \\
    --input scripts/quality/day3-bucket1-kcna.txt

  # Preview the plan without dispatching
  .venv/bin/python scripts/quality/run_388_batch.py --track CKAD --dry

  # See available tracks (joined with critical-mod counts)
  .venv/bin/python scripts/quality/run_388_batch.py --list-tracks
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
QUALITY_DIR = REPO / "scripts/quality"
LOG_DIR = REPO / "logs"
API_BASE = "http://127.0.0.1:8768"
CRITICAL_THRESHOLD = 2.0  # rubric score below this = critical (mirrors API definition)

sys.path.insert(0, str(REPO / "scripts"))


# Top-level aliases → list of filesystem prefixes the alias covers.
# These mirror the site-level navigation tabs in CLAUDE.md.
TOP_LEVEL_ALIASES: dict[str, list[str]] = {
    "certifications":       ["k8s/"],
    "platform-engineering": ["platform/"],
    "fundamentals":         ["prerequisites/", "linux/"],
    "cloud":                ["cloud/"],
    "on-premises":          ["on-premises/"],
    "ai":                   ["ai/"],
    "ai-ml-engineering":    ["ai-ml-engineering/"],
}


def api_get(path: str) -> dict:
    url = f"{API_BASE}{path}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def fetch_upgrade_plan() -> dict:
    """GET /api/quality/upgrade-plan?target=5.0 — pre-bucketed by track."""
    return api_get("/api/quality/upgrade-plan?target=5.0")


def fetch_quality_board() -> dict[str, dict]:
    """GET /api/quality/board — keyed by path for cheap lookups."""
    d = api_get("/api/quality/board")
    return {m["path"]: m for m in d.get("modules", [])}


def fetch_active_leases() -> set[str]:
    """GET /api/pipeline/leases — return the set of paths currently leased."""
    d = api_get("/api/pipeline/leases")
    paths: set[str] = set()
    for lease in d.get("active", []):
        # lease shape exposes module_key/slug/path depending on revision; cover all common keys
        for key in ("path", "module_path", "module_key"):
            if key in lease:
                paths.add(lease[key])
    return paths


def fetch_active_pilot_branches() -> dict[str, str]:
    """Read active remote `codex/388-pilot-*` and `claude/388-pilot-*` branches once."""
    cmd = [
        "git",
        "-C",
        str(REPO),
        "ls-remote",
        "--heads",
        "origin",
        "codex/388-pilot-*",
        "claude/388-pilot-*",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return {}
    active: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        ref = parts[1]
        if not ref.startswith("refs/heads/"):
            continue
        branch = ref.removeprefix("refs/heads/")
        if branch.startswith("codex/388-pilot-"):
            slug = branch.removeprefix("codex/388-pilot-")
            if slug and slug not in active:
                active[slug] = branch
        elif branch.startswith("claude/388-pilot-"):
            slug = branch.removeprefix("claude/388-pilot-")
            if slug and slug not in active:
                active[slug] = branch
    return active


def list_tracks(plan: dict) -> None:
    print(f"Total critical (<{CRITICAL_THRESHOLD}) modules: {plan.get('needs_upgrade_count', '?')}")
    print()
    print("Fine-grained tracks (use --track <name>):")
    print(f"  {'TRACK':40s}  {'TOP-LEVEL':16s}  COUNT  AVG")
    rows = []
    for t in plan.get("tracks", []):
        name = t.get("track") or t.get("name") or "?"
        n = t.get("count", 0)
        if not n:
            continue
        avg = t.get("average_score", 0)
        sample = t.get("modules", [{}])[0].get("path", "")
        toplevel = sample.split("/", 1)[0] if sample else "?"
        rows.append((toplevel, name, n, avg))
    # sort: top-level group, then by count desc within group
    rows.sort(key=lambda r: (r[0], -r[2]))
    for toplevel, name, n, avg in rows:
        print(f"  {name:40s}  {toplevel:16s}  {n:>5}  {avg:.2f}")
    print()
    print("Top-level aliases (use --track <alias>):")
    for alias, prefixes in TOP_LEVEL_ALIASES.items():
        print(f"  {alias:24s} → {' + '.join(prefixes)}")


def select_modules(
    track_arg: str,
    plan: dict,
    board: dict,
    leases: set[str],
    active_pilot_branches: dict[str, str] | None = None,
) -> tuple[list[str], list[str]]:
    """Resolve --track to a filtered list of repo-relative paths.

    Returns (selected_paths, skip_reasons) — selected_paths are
    'src/content/docs/<api-path>' format ready for the dispatcher.
    """
    plan_tracks = plan.get("tracks", [])

    # First try exact (case-insensitive) fine-grained match
    matched_track = None
    for t in plan_tracks:
        if (t.get("track") or "").lower() == track_arg.lower():
            matched_track = t
            break

    if matched_track:
        candidates = list(matched_track.get("modules", []))
        scope = f"track={matched_track['track']}"
    elif track_arg.lower() in TOP_LEVEL_ALIASES:
        prefixes = TOP_LEVEL_ALIASES[track_arg.lower()]
        candidates = []
        for t in plan_tracks:
            for m in t.get("modules", []):
                if any(m["path"].startswith(p) for p in prefixes):
                    candidates.append(m)
        scope = f"alias={track_arg.lower()} ({' + '.join(prefixes)})"
    else:
        valid_aliases = sorted(TOP_LEVEL_ALIASES)
        raise SystemExit(
            f"❌ unknown --track '{track_arg}'. "
            f"Run --list-tracks to see all options. "
            f"Aliases: {', '.join(valid_aliases)}."
        )

    # Filter: skip modules that the board says are already done OR currently leased
    selected: list[str] = []
    reasons: list[str] = []
    pilot_map = active_pilot_branches or {}
    for m in candidates:
        api_path = m["path"]
        repo_path = f"src/content/docs/{api_path}"
        slug = Path(api_path).name
        if slug in pilot_map:
            reason = f"[skip] {slug}: active remote branch {pilot_map[slug]}"
            reasons.append(reason)
            print(reason)
            continue
        b = board.get(api_path, {})
        if b.get("status") == "done" or b.get("revision_pending") is False and (b.get("score", 0) or 0) >= 4.0:
            reasons.append(f"  skip [done]      {api_path}")
            continue
        if api_path in leases or repo_path in leases:
            reasons.append(f"  skip [leased]    {api_path}")
            continue
        selected.append(repo_path)

    print(f"[batch] {scope}: {len(candidates)} critical → {len(selected)} after filters ({len(reasons)} skipped)")
    if reasons and len(reasons) <= 8:
        for r in reasons:
            print(r)
    return selected, reasons


def write_bucket_file(paths: list[str], out_path: Path, scope_desc: str) -> None:
    today = dt.date.today().isoformat()
    header = (
        f"# Auto-built #388 bucket — {scope_desc}\n"
        f"# {len(paths)} module(s) at <{CRITICAL_THRESHOLD} critical-rubric.\n"
        f"# Source: {API_BASE}/api/quality/upgrade-plan + /api/quality/board + /api/pipeline/leases @ {today}\n"
        f"# Generated by scripts/quality/run_388_batch.py\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + "\n".join(paths) + "\n")


def read_log_events(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]


def gh_pr_url(pr_num: int) -> str:
    return f"https://github.com/kube-dojo/kube-dojo.github.io/pull/{pr_num}"


def print_summary(log_path: Path) -> dict:
    """Read the dispatcher's JSONL log and print a per-event summary table."""
    events = read_log_events(log_path)
    counts: dict[str, int] = {
        "module_start": 0,
        "merged": 0,
        "merge_held_nits": 0,
        "merge_held": 0,
        "module_skip": 0,
        "codex_error": 0,
        "gemini_error": 0,
        "worktree_error": 0,
    }
    held_nits: list[tuple[int, str]] = []
    held_full: list[tuple[int, str, str]] = []  # (pr, module, verdict)
    skipped: list[tuple[str, str]] = []
    for e in events:
        kind = e.get("event")
        if kind in counts:
            counts[kind] += 1
        if kind == "merge_held_nits":
            held_nits.append((e["pr"], e["module"]))
        elif kind == "merge_held":
            held_full.append((e["pr"], e["module"], e.get("verdict", "?")))
        elif kind == "module_skip":
            skipped.append((e["module"], e.get("reason", "?")))

    print()
    print("=" * 70)
    print("BATCH SUMMARY")
    print("=" * 70)
    print(f"Log: {log_path}")
    for k, v in counts.items():
        if v:
            print(f"  {k:20s} {v}")
    if held_nits:
        print(f"\n--- {len(held_nits)} PR(s) held with APPROVE_WITH_NITS — manual triage needed ---")
        print("    Per C3: trivial nits (URL fix, alias removal, typo) → fix inline + merge.")
        print("    Read gemini's review on each PR before deciding.")
        for pr, mod in held_nits:
            print(f"  PR #{pr}  {gh_pr_url(pr)}")
            print(f"    module: {mod}")
    if held_full:
        print(f"\n--- {len(held_full)} PR(s) held with NEEDS CHANGES / UNCLEAR — manual decision ---")
        print("    Per C3: structural failures → re-dispatch codex on the existing branch.")
        for pr, mod, verdict in held_full:
            print(f"  PR #{pr} [{verdict}]  {gh_pr_url(pr)}")
            print(f"    module: {mod}")
    if skipped:
        print(f"\n--- {len(skipped)} module(s) skipped (codex_failed / no_pr_in_response) ---")
        for mod, reason in skipped:
            print(f"  {reason}  {mod}")
    print()
    return {"counts": counts, "held_nits": held_nits, "held_full": held_full, "skipped": skipped}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="End-to-end #388 batch: bucket build → dispatch → cleanup → summary.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Tracks come from /api/quality/upgrade-plan (fine-grained) or aliases\n"
            "(top-level). Run --list-tracks to discover them.\n\n"
            "Held PRs require MANUAL triage. The summary at the end lists each held\n"
            "PR with its gemini review URL — read the review and apply C3 routing:\n"
            "  - APPROVE_WITH_NITS (trivial: URL fix, alias removal, typo)\n"
            "      → fix inline on the branch, gh pr merge --squash --delete-branch <num>\n"
            "  - NEEDS CHANGES / UNCLEAR (structural)\n"
            "      → close PR or re-dispatch codex on the existing branch with the gemini\n"
            "        review as the brief.\n"
        ),
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--track", help="Fine-grained track name (KCNA, CKAD, …) or top-level alias.")
    src.add_argument("--input", "-i", type=Path, help="Use an existing curated module-list file.")
    src.add_argument("--list-tracks", action="store_true", help="List all tracks + aliases and exit.")
    p.add_argument(
        "--bucket-out", type=Path, default=None,
        help="When --track is used, write the bucket here (default: scripts/quality/day3-bucket-<track>-<date>.txt).",
    )
    p.add_argument(
        "--log", type=Path, default=None,
        help="JSONL log path (default: logs/388_batch_<bucket-stem>_<date>.jsonl).",
    )
    p.add_argument("--dry", action="store_true", help="Print the plan; do not dispatch or clean up.")
    p.add_argument("--no-cleanup", action="store_true", help="Skip the post-dispatch cleanup step.")
    p.add_argument("--max", "-n", type=int, default=0, help="Stop after N modules (passed through to dispatcher).")
    p.add_argument(
        "--no-skip-active-branches",
        action="store_true",
        help="Do not skip modules with active codex/claude 388-pilot remote branches.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.list_tracks:
        list_tracks(fetch_upgrade_plan())
        return 0

    if not args.track and not args.input:
        print("❌ provide --track <name|alias>, --input <file>, or --list-tracks", file=sys.stderr)
        return 1

    today = dt.date.today().isoformat()

    # ── 1. Resolve / build the bucket file ─────────────────────────────
    queue: list[str] = []
    if args.track:
        plan = fetch_upgrade_plan()
        board = fetch_quality_board()
        leases = fetch_active_leases()
        active_branches = {} if args.no_skip_active_branches else fetch_active_pilot_branches()
        if leases:
            print(f"[batch] {len(leases)} active pipeline lease(s) — those modules will be skipped")
        queue, _ = select_modules(args.track, plan, board, leases, active_branches)
        if not queue:
            print("❌ no modules to dispatch (all filtered out).", file=sys.stderr)
            return 1
        slug = args.track.lower().replace(" ", "-").replace("/", "-")
        bucket_path = args.bucket_out or QUALITY_DIR / f"day3-bucket-{slug}-{today}.txt"
        scope = f"track={args.track}"
        if not args.dry:
            write_bucket_file(queue, bucket_path, scope)
            print(f"[batch] wrote {bucket_path.relative_to(REPO)}")
        else:
            print(f"[batch] (dry: would write {len(queue)} module(s) to {bucket_path.relative_to(REPO)})")
            for p in queue[:5]:
                print(f"        - {p}")
            if len(queue) > 5:
                print(f"        ... ({len(queue) - 5} more)")
    else:
        bucket_path = args.input.resolve()
        if not bucket_path.exists():
            print(f"❌ input file not found: {bucket_path}", file=sys.stderr)
            return 1
        print(f"[batch] using existing bucket → {bucket_path.relative_to(REPO)}")
        queue = [
            line.strip()
            for line in bucket_path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]

    # ── 2. Compute log path ────────────────────────────────────────────
    log_path = args.log or LOG_DIR / f"388_batch_{bucket_path.stem}_{today}.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # ── 3. Plan summary ────────────────────────────────────────────────
    if args.max and args.max > 0:
        queue = queue[: args.max]
    est_min = len(queue) * 12  # ~12 min/module avg from Day 2 pilot
    print()
    print("[batch] PLAN")
    print(f"  modules:        {len(queue)}")
    print(f"  log:            {log_path.relative_to(REPO)}")
    print(f"  expected wall:  ~{est_min // 60}h {est_min % 60}m at 12 min/module (Day 2 baseline)")
    print(f"  cleanup:        {'skip' if args.no_cleanup else 'run after pilot_done'}")
    if queue:
        print(f"  first 3:        {', '.join(Path(p).name for p in queue[:3])}")
        print(f"  last 3:         {', '.join(Path(p).name for p in queue[-3:])}")

    if args.dry:
        print("\n[batch] --dry: stopping before dispatch.")
        return 0

    # ── 4. Dispatch ────────────────────────────────────────────────────
    print("\n[batch] dispatching ...")
    from quality import dispatch_388_pilot  # type: ignore  # noqa: E402

    dispatcher_argv = ["--input", str(bucket_path), "--log", str(log_path)]
    if args.max and args.max > 0:
        dispatcher_argv += ["--max", str(args.max)]
    rc = dispatch_388_pilot.main(dispatcher_argv)
    if rc != 0:
        print(f"\n[batch] ❌ dispatcher returned {rc}; skipping cleanup.")
        print_summary(log_path)
        return rc

    # ── 5. Cleanup ─────────────────────────────────────────────────────
    if not args.no_cleanup:
        print("\n[batch] running cleanup ...")
        from quality import cleanup_388_pilot  # type: ignore  # noqa: E402

        cleanup_388_pilot.main(["--input", str(bucket_path)])

    # ── 6. Summary ─────────────────────────────────────────────────────
    print_summary(log_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

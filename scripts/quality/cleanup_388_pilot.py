#!/usr/bin/env python3
"""Post-pilot cleanup for #388 Day 2.

Run after `dispatch_388_pilot.py` reports `pilot_done`:

  1. Re-fetch + ff-merge origin/main so all merged PRs are local.
  2. For each module in pilot-2026-05-02.txt: re-verify on main; record tier + body_words + revision_pending flag.
  3. If frontmatter still has `revision_pending: true` on a merged module, set it to `false`. Stage in one cleanup commit.
  4. Remove stale pilot worktrees + local branches.
  5. Remove the /private/tmp/kubedojo-build-388-pilot worktree codex created during run.
  6. Print a final per-module table + summary.

Usage:
  .venv/bin/python scripts/quality/cleanup_388_pilot.py        # do everything
  .venv/bin/python scripts/quality/cleanup_388_pilot.py --dry  # report only, no writes
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/krisztiankoos/projects/kubedojo")
PILOT_FILE = REPO / "scripts/quality/pilot-2026-05-02.txt"
TMP_BUILD_WT = Path("/private/tmp/kubedojo-build-388-pilot")


def run(cmd: list[str], cwd: Path = REPO, check: bool = False) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        print(f"FAIL: {' '.join(cmd)}\n{p.stdout}\n{p.stderr}", file=sys.stderr)
        sys.exit(1)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def fetch_main():
    run(["git", "fetch", "origin", "main"], check=True)
    run(["git", "pull", "--ff-only", "origin", "main"])


def verify_module(path: str) -> dict:
    cmd = [str(REPO / ".venv/bin/python"), "scripts/quality/verify_module.py",
           "--glob", path, "--skip-source-check", "--out", "/tmp/cleanup-verify.jsonl", "--quiet"]
    run(cmd)
    try:
        with open("/tmp/cleanup-verify.jsonl") as f:
            lines = f.readlines()
        return json.loads(lines[-1]) if lines else {}
    except Exception:
        return {}


def fix_revision_pending(path: Path, dry: bool) -> bool:
    """Return True if file needed and got the fix."""
    text = path.read_text()
    if not re.search(r"^revision_pending:\s*true\b", text, re.MULTILINE):
        return False
    if dry:
        return True
    new = re.sub(r"^revision_pending:\s*true\b", "revision_pending: false", text, count=1, flags=re.MULTILINE)
    path.write_text(new)
    return True


def remove_pilot_worktrees(dry: bool):
    _, out = run(["git", "worktree", "list", "--porcelain"])
    wts = []
    cur = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if cur: wts.append(cur)
            cur = {"path": line.split(" ", 1)[1]}
        elif line.startswith("branch "):
            cur["branch"] = line.split(" ", 1)[1]
        elif line == "" and cur:
            wts.append(cur); cur = {}
    if cur: wts.append(cur)

    pilot_wts = [w for w in wts if "388-pilot" in w.get("path", "")]
    print(f"\n[cleanup] {len(pilot_wts)} pilot worktree(s) to remove")
    for w in pilot_wts:
        print(f"  - {w['path']}  ({w.get('branch','?')})")
        if dry: continue
        run(["git", "worktree", "remove", "--force", w["path"]])
        if "branch" in w:
            br = w["branch"].replace("refs/heads/", "")
            run(["git", "branch", "-D", br])


def remove_tmp_build_wt(dry: bool):
    if not TMP_BUILD_WT.exists():
        return
    print(f"\n[cleanup] removing {TMP_BUILD_WT}")
    if dry: return
    run(["git", "worktree", "remove", "--force", str(TMP_BUILD_WT)])


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry", action="store_true", help="Report only, do not write")
    p.add_argument("--no-fetch", action="store_true", help="Skip git fetch + pull")
    args = p.parse_args(argv)

    if not args.no_fetch:
        print("[cleanup] fetching origin/main...")
        fetch_main()

    pilot = [l.strip() for l in PILOT_FILE.read_text().splitlines() if l.strip()]
    print(f"\n[cleanup] {len(pilot)} pilot modules to verify\n")

    needed_fix = []
    rows = []
    for path in pilot:
        full = REPO / path
        if not full.exists():
            rows.append((path, "MISSING", "-", "-", "-"))
            continue
        rec = verify_module(path)
        tier = rec.get("tier", "?")
        body = rec.get("metrics", {}).get("body_words", "?")
        rp = rec.get("frontmatter", {}).get("revision_pending", "?")
        passed = "yes" if rec.get("passed") else "no"
        rows.append((path, tier, body, rp, passed))
        # Only clear the flag when the module actually passes the verifier on main
        # (i.e., the rewrite has merged). Don't touch held / not-yet-merged modules.
        if rp is True and rec.get("passed") is True:
            if fix_revision_pending(full, args.dry):
                needed_fix.append(path)

    print("\n=== PILOT POST-MERGE STATUS ===")
    print(f"{'tier':6s} {'body':>6s} {'rp':>6s} {'pass':>5s}  module")
    for path, tier, body, rp, passed in rows:
        print(f"{str(tier):6s} {str(body):>6s} {str(rp):>6s} {passed:>5s}  {path}")

    if needed_fix:
        print(f"\n[cleanup] frontmatter rewritten on {len(needed_fix)} module(s):")
        for path in needed_fix: print(f"  - {path}")
        if not args.dry:
            run(["git", "add"] + needed_fix)
            msg = f"chore(388): clear revision_pending flag on {len(needed_fix)} pilot module(s)"
            code, _ = run(["git", "commit", "-m", msg])
            print(f"[cleanup] commit: rc={code}")
            if code == 0:
                run(["git", "push", "origin", "main"])

    remove_pilot_worktrees(args.dry)
    remove_tmp_build_wt(args.dry)
    print("\n[cleanup] done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

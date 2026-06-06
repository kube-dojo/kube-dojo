#!/usr/bin/env python3
"""Supply-chain DETECTION tripwire — issue #1812 (Miasma-class worm defense).

`.npmrc` sets `ignore-scripts=true` (PREVENTION). `check_install_scripts.py` catches
non-registry sources, local links, and alias masquerade. THIS tripwire's distinct job is
to surface any lockfile dependency mutation (`version` / `resolved` / `integrity`) that
is NOT accompanied by a `package.json` change — the "silent lockfile swap" where an
attacker edits `package-lock.json` without touching `package.json` and `npm ci` installs
the malicious artifact without complaint.

Decision:
  - dependency tuples unchanged          → PASS (exit 0)
  - lockfile tuples changed AND package.json also changed → PASS (normal dep bump)
  - lockfile tuples changed AND package.json UNCHANGED    → FAIL (exit 1)

Override (acknowledgement marker, NOT an authorization control):
  A failure is suppressed when the HEAD commit message contains the literal token
  `[lockfile-only]` OR env `LOCKFILE_OVERRIDE=1` is set. An attacker could add the
  marker to their own PR — the real value is forcing the lockfile diff to be NOTICED
  and reviewed; the marker only records that a human acknowledged it.

Range selection (git-diff based, deterministic, no network):
  - `--base <ref>` / `--head <ref>`; defaults: head=`HEAD`, base from env
    `LOCKFILE_BASE` else `HEAD~1`.
  - `--three-dot` uses `<base>...<head>` (merge-base diff — use for pull requests).
  - Default (no `--three-dot`) uses `<base>..<head>` (two-dot — fine for push / local).

Edge cases:
  - No base commit (initial/shallow clone with one commit) → note + PASS (exit 0).
  - Missing `package-lock.json` at base (newly added) → all entries are "new".
  - `git`/JSON errors → non-zero exit with a clear message (fail closed).

Exit 0 = clean or acknowledged. Exit 1 = silent lockfile swap signal.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCKFILE = "package-lock.json"
MANIFEST = "package.json"
TUPLE_FIELDS = ("version", "resolved", "integrity")
MAX_REPORT = 50
OVERRIDE_TOKEN = "[lockfile-only]"


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def ref_exists(ref: str) -> bool:
    return run_git(["rev-parse", "--verify", ref], check=False).returncode == 0


def commit_message(ref: str) -> str:
    result = run_git(["log", "-1", "--format=%B", ref], check=False)
    if result.returncode != 0:
        return ""
    return result.stdout


def diff_range(base: str, head: str, three_dot: bool) -> str:
    sep = "..." if three_dot else ".."
    return f"{base}{sep}{head}"


def manifest_changed_in_range(range_spec: str) -> bool:
    return run_git(["diff", "--quiet", range_spec, "--", MANIFEST], check=False).returncode != 0


def lockfile_changed_in_range(range_spec: str) -> bool:
    return run_git(["diff", "--quiet", range_spec, "--", LOCKFILE], check=False).returncode != 0


def load_packages_at(ref: str) -> dict[str, dict[str, str | None]] | None:
    """Return packages map keyed by lockfile path, or None if lockfile absent at ref."""
    result = run_git(["show", f"{ref}:{LOCKFILE}"], check=False)
    if result.returncode != 0:
        stderr = (result.stderr or "").lower()
        if "does not exist" in stderr or "exists on disk, but not in" in stderr:
            return None
        print(f"ERROR: cannot read {LOCKFILE} at {ref}: {result.stderr.strip()}", file=sys.stderr)
        raise RuntimeError(f"git show failed for {ref}:{LOCKFILE}")

    return packages_from_json_text(result.stdout, f"{ref}:{LOCKFILE}")


def packages_from_json_text(text: str, source: str) -> dict[str, dict[str, str | None]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {source}: {exc}", file=sys.stderr)
        raise RuntimeError("invalid lockfile JSON") from exc

    packages = data.get("packages")
    if not isinstance(packages, dict):
        return {}

    out: dict[str, dict[str, str | None]] = {}
    for path, meta in packages.items():
        if not path or not isinstance(meta, dict):
            continue
        out[path] = {field: meta.get(field) for field in TUPLE_FIELDS}
    return out


def load_packages_worktree(ref: str) -> dict[str, dict[str, str | None]]:
    """Load lockfile from the worktree when ref is HEAD, else via git show."""
    if ref in ("HEAD", "head"):
        lock_path = REPO_ROOT / LOCKFILE
        if not lock_path.is_file():
            print(f"ERROR: lockfile not found: {lock_path}", file=sys.stderr)
            raise RuntimeError("missing worktree lockfile")
        try:
            text = lock_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot read {lock_path}: {exc}", file=sys.stderr)
            raise RuntimeError("missing worktree lockfile") from exc
        return packages_from_json_text(text, str(lock_path))

    pkgs = load_packages_at(ref)
    return pkgs if pkgs is not None else {}


def dependency_tuple_changes(
    before: dict[str, dict[str, str | None]] | None,
    after: dict[str, dict[str, str | None]],
) -> list[str]:
    before = before or {}
    changed: list[str] = []
    all_paths = sorted(set(before) | set(after))
    for path in all_paths:
        if before.get(path) != after.get(path):
            changed.append(path)
    return changed


def override_active(head: str) -> bool:
    if os.environ.get("LOCKFILE_OVERRIDE") == "1":
        return True
    return OVERRIDE_TOKEN in commit_message(head)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect silent package-lock.json dependency swaps (issue #1812)."
    )
    parser.add_argument(
        "--base",
        default=os.environ.get("LOCKFILE_BASE"),
        help="Base ref (default: env LOCKFILE_BASE, else HEAD~1)",
    )
    parser.add_argument("--head", default="HEAD", help="Head ref (default: HEAD)")
    parser.add_argument(
        "--three-dot",
        action="store_true",
        help="Use three-dot diff range (merge-base; for pull requests)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv[1:])
    head = args.head
    base = args.base or "HEAD~1"
    three_dot = args.three_dot

    print(f"Lockfile-integrity tripwire — comparing {LOCKFILE} dependency tuples.")

    if not ref_exists(head):
        print(f"ERROR: head ref not found: {head}", file=sys.stderr)
        return 2

    if base == "HEAD~1" and not ref_exists("HEAD~1"):
        print(
            "NOTE: no parent commit (initial or shallow clone) — skipping lockfile diff."
        )
        print("OK — nothing to compare.")
        return 0

    if not ref_exists(base):
        print(f"ERROR: base ref not found: {base}", file=sys.stderr)
        return 2

    range_spec = diff_range(base, head, three_dot)
    print(f"Range: {range_spec}")

    try:
        before_pkgs = load_packages_at(base)
        after_pkgs = load_packages_worktree(head)
    except RuntimeError:
        return 2

    changed_paths = dependency_tuple_changes(before_pkgs, after_pkgs)

    if not changed_paths:
        print("OK — no dependency tuple changes in lockfile.")
        return 0

    # Structured tuple compare is authoritative even if git diff merge-base differs.
    pkg_json_changed = manifest_changed_in_range(range_spec)
    lockfile_in_diff = lockfile_changed_in_range(range_spec)

    if pkg_json_changed:
        print(
            f"NOTE: {len(changed_paths)} dependency tuple(s) changed and "
            f"{MANIFEST} also changed in {range_spec} — expected for dep bumps."
        )
        print("OK — lockfile change accompanied by manifest change.")
        return 0

    if override_active(head):
        print(
            f"NOTE: override active ({OVERRIDE_TOKEN} in commit message or "
            "LOCKFILE_OVERRIDE=1) — acknowledging lockfile-only change."
        )
        print(
            f"  {len(changed_paths)} dependency tuple(s) changed without "
            f"{MANIFEST} change (reviewed/acknowledged)."
        )
        return 0

    print(
        f"\n  SUPPLY-CHAIN TRIPWIRE: silent lockfile swap — "
        f"{len(changed_paths)} dependency tuple(s) changed without a "
        f"{MANIFEST} change in {range_spec}:",
        file=sys.stderr,
    )
    if not lockfile_in_diff:
        print(
            f"  (structured compare detected tuple drift; git diff may use a "
            f"different merge-base than {range_spec})",
            file=sys.stderr,
        )

    shown = changed_paths[:MAX_REPORT]
    for path in shown:
        before = (before_pkgs or {}).get(path, {})
        after = after_pkgs.get(path, {})
        print(f"    [lockfile-swap] {path}", file=sys.stderr)
        for field in TUPLE_FIELDS:
            if before.get(field) != after.get(field):
                print(
                    f"      {field}: {before.get(field)!r} → {after.get(field)!r}",
                    file=sys.stderr,
                )

    remaining = len(changed_paths) - len(shown)
    if remaining > 0:
        print(f"    … and {remaining} more path(s)", file=sys.stderr)

    print(
        "\n  This is how a Miasma-class attacker swaps a resolved tarball without "
        "touching package.json. Review the lockfile diff.\n"
        "  If legitimate (e.g. npm audit fix), either commit the change together "
        f"with {MANIFEST} or add the acknowledgement marker [lockfile-only] to the "
        "commit message (or set LOCKFILE_OVERRIDE=1 locally).\n"
        "  The marker is NOT an authorization control — it only records human review.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

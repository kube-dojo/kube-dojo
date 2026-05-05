#!/usr/bin/env python3
"""Set-based gate for incident-duplication regressions.

The checker enforces a monotonicity rule:

* New violations may be introduced by base->branch diff **only if**
  they are not in the base set.
* Passing means ``after`` violations are a subset of ``before`` and count
  has not increased.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

Triple = tuple[str, str, str]


REPO_ROOT = Path(__file__).resolve().parents[2]


def _python_executable(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return os.environ.get("KUBEDOJO_INCIDENT_GATE_PYTHON", "python3")


def _run_git(cmd: list[str], repo_root: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *cmd],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(stderr)
    return result


def _run_check(repo_root: Path) -> list[dict]:
    script = repo_root / "scripts" / "check_incident_reuse.py"
    result = subprocess.run(
        [_python_executable(repo_root), str(script), "--json"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )

    if result.returncode not in (0, 1):
        err = result.stderr.strip() or result.stdout.strip() or "checker command failed"
        raise RuntimeError(err)

    payload = json.loads(result.stdout)
    violations = payload.get("violations")
    if not isinstance(violations, list):
        raise RuntimeError("checker JSON missing violations list")
    return violations


def _to_triples(violations: list[dict]) -> set[Triple]:
    triples: set[Triple] = set()
    for violation in violations:
        if not isinstance(violation, dict):
            continue
        kind = violation.get("kind")
        incident = violation.get("incident")
        file = violation.get("file")
        if all(isinstance(value, str) for value in (kind, incident, file)):
            triples.add((str(kind), str(incident), str(file)))
    return triples


def _run_in_base_worktree(repo_root: Path, base_ref: str) -> tuple[set[Triple], list[dict]]:
    with tempfile.TemporaryDirectory(prefix="incident-dedup-base-") as worktree:
        worktree_path = Path(worktree)
        _run_git(["worktree", "add", "--detach", str(worktree_path), base_ref], repo_root)
        try:
            before_violations = _run_check(worktree_path)
            return _to_triples(before_violations), before_violations
        finally:
            # Remove the linked worktree registration even if inspection fails.
            _run_git(["worktree", "remove", "--force", str(worktree_path)], repo_root)


def _sorted_triples(triples: set[Triple]) -> list[list[str]]:
    return [list(item) for item in sorted(triples)]


def run_delta_gate(repo_root: Path, base_ref: str) -> tuple[bool, dict]:
    before_set, before_violations = _run_in_base_worktree(repo_root, base_ref)
    after_violations = _run_check(repo_root)
    after_set = _to_triples(after_violations)

    added = after_set - before_set
    removed = before_set - after_set
    count_regressed = len(after_set) > len(before_set)

    ok = len(added) == 0 and not count_regressed
    return ok, {
        "mode": "delta",
        "base_ref": base_ref,
        "status": "pass" if ok else "fail",
        "added": _sorted_triples(added),
        "removed": _sorted_triples(removed),
        "before": _sorted_triples(before_set),
        "after": _sorted_triples(after_set),
        "before_count": len(before_set),
        "after_count": len(after_set),
        "added_count": len(added),
        "removed_count": len(removed),
        "count_regressed": count_regressed,
        "before_violations": before_violations,
        "after_violations": after_violations,
    }


def run_absolute_gate(repo_root: Path) -> tuple[bool, dict]:
    after_violations = _run_check(repo_root)
    after_set = _to_triples(after_violations)
    ok = len(after_set) == 0
    return ok, {
        "mode": "absolute",
        "status": "pass" if ok else "fail",
        "after": _sorted_triples(after_set),
        "after_count": len(after_set),
        "violations": after_violations,
    }


def _print_human_report(result: dict, ok: bool, mode: str) -> None:
    if mode == "delta":
        print(f"incident_dedup_gate: {'PASS' if ok else 'FAIL'} (delta)")
        print(
            f"before violations: {result['before_count']} | after violations: {result['after_count']} "
            f"| added: {result['added_count']} | removed: {result['removed_count']}"
        )
        if result["count_regressed"]:
            print(
                f"COUNT REGRESSION: after={result['after_count']} > before={result['before_count']}"
            )
        if result["added"]:
            print("NEW triples introduced:")
            for kind, incident, file in result["added"]:
                print(f"  - kind={kind} | incident={incident} | file={file}")
        if ok:
            print("No new incident triples introduced.")
        return

    print(f"incident_dedup_gate: {'PASS' if ok else 'FAIL'} (absolute)")
    if not ok:
        print(f"Remaining violations: {result['after_count']}")
        for kind, incident, file in result["after"]:
            print(f"  - kind={kind} | incident={incident} | file={file}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gate incident reuse regressions by set difference",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base git ref for delta comparison (default: origin/main)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--mode",
        default="delta",
        choices=("delta", "absolute"),
        help="Gate mode (delta compares base->current, absolute fails if any violations exist)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = REPO_ROOT

    if args.mode == "delta":
        ok, payload = run_delta_gate(repo_root, args.base)
    else:
        ok, payload = run_absolute_gate(repo_root)

    if args.json:
        json.dump(
            payload,
            sys.stdout,
            indent=2,
            sort_keys=True,
        )
        sys.stdout.write("\n")
    else:
        _print_human_report(payload, ok, args.mode)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

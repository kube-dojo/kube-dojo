#!/usr/bin/env python3
"""Passive verifier for review findings against branch or worktree files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def _norm(text: str) -> str:
    text = "\n".join(line.strip() for line in text.replace("`", "").splitlines()).strip()
    return re.sub(r"\s+", " ", text)


def parse_findings(review: str) -> list[dict[str, object]]:
    starts = [m.start() for m in re.finditer(r"^FINDING:", review, re.M)] + [len(review)]
    findings = []
    for start, end in zip(starts, starts[1:]):
        block = review[start:end].strip()
        loc = re.search(r"^FILE:LINE:\s*(.+?):(\d+)\s*$", block, re.M)
        code = re.search(r"^CURRENT CODE(?: .*)?:\s*$", block, re.M)
        if not (loc and code):
            continue
        body = []
        for line in block[code.end():].splitlines():
            if re.match(r"^[A-Z][A-Z ]+:", line):
                break
            body.append(line.lstrip())
        findings.append({"path": loc.group(1), "line": int(loc.group(2)), "code": "\n".join(body).strip()})
    return findings


def verify_review(review: str, reader) -> list[dict[str, object]]:
    results = []
    for finding in parse_findings(review):
        text = reader(finding["path"])
        quote = _norm(str(finding["code"]))
        lines = text.splitlines()
        span = max(1, str(finding["code"]).count("\n") + 1)
        start = max(0, int(finding["line"]) - 1)
        window = _norm("\n".join(lines[start:start + span]))
        status = "quote_missing" if quote not in _norm(text) else "verified" if quote in window else "line_mismatch"
        results.append({**finding, "status": status})
    return results


def _read_target(path: str, branch: str | None) -> str:
    if branch:
        return subprocess.run(
            ["git", "show", f"{branch}:{path}"], check=True, text=True, capture_output=True
        ).stdout
    return Path(path).read_text("utf-8")


_SUMMARY_PREFIX = "Review verifier for PR"


def _read_review(args: argparse.Namespace) -> str:
    if not args.from_pr:
        return sys.stdin.read()
    # Skip the verifier's own summary comments so repeat --from-pr --post-comment
    # runs don't parse their own output as if it were the reviewer's.
    jq = (
        f'[.comments[] | select(.body | startswith("{_SUMMARY_PREFIX}") | not)]'
        ' | last | .body // ""'
    )
    return subprocess.run(
        ["gh", "pr", "view", str(args.pr), "--json", "comments", "--jq", jq],
        check=True, text=True, capture_output=True,
    ).stdout


def _summary(pr: int, results: list[dict[str, object]]) -> str:
    counts = {name: sum(r["status"] == name for r in results) for name in ("verified", "line_mismatch", "quote_missing")}
    lines = [f"Review verifier for PR #{pr}: {counts['verified']} verified, {counts['line_mismatch']} line_mismatch, {counts['quote_missing']} quote_missing."]
    lines.extend(f"- `{r['status']}` {r['path']}:{r['line']}" for r in results)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--branch")
    parser.add_argument("--from-pr", action="store_true")
    parser.add_argument("--post-comment", action="store_true")
    args = parser.parse_args()
    results = verify_review(_read_review(args), lambda path: _read_target(path, args.branch))
    body = _summary(args.pr, results)
    print(body)
    if args.post_comment:
        subprocess.run(["gh", "pr", "comment", str(args.pr), "-F", "-"], input=body, check=True, text=True)
    return 1 if any(r["status"] == "quote_missing" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

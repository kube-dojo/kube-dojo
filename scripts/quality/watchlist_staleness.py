#!/usr/bin/env python3
"""watchlist_staleness.py — currency dashboard for dated 'as of YYYY[-MM]' claims (#1959 D2).

The durable-content rule (.claude/rules/durable-vendor-content.md) quarantines
volatile facts into dated snapshots ("Landscape snapshot — as of YYYY-MM").
Those dated markers ARE the software watchlist: each one is a promise that
someone verified a fast-moving fact (a price, a version, a project's maturity)
at a point in time. This script greps them, computes their age, and flags the
stale ones so the continuous-improvement stream knows what to re-verify.

Refresh cadence
---------------
Re-check the named fast-movers on the ~3x/yr Kubernetes release rhythm plus
ad-hoc when a major release lands. Key projects to watch (extend as the
curriculum grows): Kubernetes, Argo CD/Rollouts, Karpenter, OpenCost/Kubecost,
Cilium, Istio, vLLM/KServe, Prometheus, OpenTelemetry, Crossplane, Backstage,
Velero, Kyverno, Terraform/OpenTofu, KEDA, containerd, cert-manager, Gateway
API, Flux. A refresh = edit the dated snapshot cell (not the surrounding
teaching) + add a "currency refresh" entry to src/content/docs/changelog.md.

Usage
-----
  scripts/quality/watchlist_staleness.py                  # table; stale = age >= --stale-months
  scripts/quality/watchlist_staleness.py --stale-months 6
  scripts/quality/watchlist_staleness.py --json           # machine output (for a dashboard/API)
  scripts/quality/watchlist_staleness.py --now 2026-06     # pin the reference month (reproducible)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# "as of 2026-06", "as of 2026", "(as of 2025)" — the 'as of' phrasing targets
# current-state volatility claims, not bare citation years ("He et al., 2015").
MARKER = re.compile(r"as of\s+(20\d{2})(?:-(\d{2}))?", re.IGNORECASE)
SNAPSHOT_HINT = re.compile(r"landscape snapshot", re.IGNORECASE)


def months_between(y0: int, m0: int, y1: int, m1: int) -> int:
    return (y1 - y0) * 12 + (m1 - m0)


def collect(root: Path, repo: Path, ny: int, nm: int) -> list[dict]:
    rows: list[dict] = []
    for p in sorted(root.rglob("*.md")):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines, 1):
            for m in MARKER.finditer(line):
                yr = int(m.group(1))
                mo = int(m.group(2)) if m.group(2) else None
                # Year-only markers assume mid-year (June) so age is neither
                # over- nor under-stated by up to a full year.
                eff_mo = mo if mo else 6
                rows.append(
                    {
                        "file": str(p.relative_to(repo)),
                        "line": i,
                        "date": f"{yr}-{mo:02d}" if mo else str(yr),
                        "age_months": months_between(yr, eff_mo, ny, nm),
                        "granularity": "month" if mo else "year",
                        "snapshot_callout": bool(SNAPSHOT_HINT.search(line)),
                        "snippet": line.strip()[:120],
                    }
                )
    rows.sort(key=lambda r: (-r["age_months"], r["file"], r["line"]))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--root",
        default="src/content/docs",
        help="content root (default: src/content/docs)",
    )
    ap.add_argument(
        "--stale-months",
        type=int,
        default=4,
        help="age in months at/above which a marker is stale (default 4 ~ K8s release cycle)",
    )
    ap.add_argument("--now", help="reference month YYYY-MM (default: today)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if args.now:
        try:
            ny, nm = (int(x) for x in args.now.split("-"))
        except ValueError:
            print(f"error: --now must be YYYY-MM, got {args.now!r}", file=sys.stderr)
            return 2
    else:
        today = date.today()
        ny, nm = today.year, today.month

    repo = Path(__file__).resolve().parents[2]
    root = repo / args.root
    if not root.is_dir():
        print(f"error: content root not found: {root}", file=sys.stderr)
        return 2

    rows = collect(root, repo, ny, nm)
    stale = [r for r in rows if r["age_months"] >= args.stale_months]
    n_files = len({r["file"] for r in rows})

    if args.json:
        print(
            json.dumps(
                {
                    "reference_month": f"{ny}-{nm:02d}",
                    "stale_months_threshold": args.stale_months,
                    "total_markers": len(rows),
                    "files_with_markers": n_files,
                    "stale_count": len(stale),
                    "markers": rows,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    print(
        f"Software-watchlist staleness — reference {ny}-{nm:02d}, stale threshold ≥{args.stale_months} months"
    )
    print(f"{len(rows)} 'as of' markers across {n_files} files; {len(stale)} stale\n")
    if stale:
        print(
            "STALE — re-verify against upstream, then refresh the dated snapshot (oldest first):"
        )
        for r in stale:
            tag = "📸" if r["snapshot_callout"] else "  "
            print(
                f"  {tag} {r['age_months']:>3}mo  {r['date']:<7}  {r['file']}:{r['line']}"
            )
            print(f"          {r['snippet']}")
    else:
        print("No stale markers. 🎉")
    print("\n(📸 = inside a 'Landscape snapshot' callout · --json for machine output)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""CI guardrail — enforce the "each incident in at most ONE module" rule.

This script is the durable counterpart to ``scripts/audit_incident_reuse.py``:
the audit one *measures* repetition, this one *prevents* it. Wire it into CI
alongside ``scripts/check_site_health.py`` and ``scripts/check_reader_aids.py``.

Rule (per user direction, 2026-05-04):

* Every named real-world incident appears in at most ONE module across the
  entire EN curriculum.
* That ONE module is its CANONICAL — see ``docs/audits/2026-05-04-incident-canonicals.md``.
* Any OTHER module that mentions the same incident must mark the mention
  with an ``<!-- incident-xref: <slug> -->`` HTML comment within 200
  characters of the mention. The xref pattern is for short cross-references
  ("see module-X.Y for the original incident") — not for re-telling the
  story.

The script imports ``INCIDENTS`` from ``audit_incident_reuse.py`` so the
keyword catalog is the single source of truth. Editing one updates the
other.

Exit codes:
  0  no violations
  1  violations found
  2  unrelated error (missing file, etc.)

Usage:
  python3 scripts/check_incident_reuse.py [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCOPE = REPO / "src" / "content" / "docs"
EXCLUDE_DIRS = ("/uk/", "/ai-history/", "/ai-ml-engineering/history/")

# Import the regex catalog so this stays in sync with the audit script.
sys.path.insert(0, str(REPO / "scripts"))
from audit_incident_reuse import INCIDENTS, in_scope  # noqa: E402

# Slugs match docs/audits/2026-05-04-incident-canonicals.md.
# Slug → (canonical relpath under repo root, incident label)
CANONICALS: dict[str, tuple[str, str]] = {
    "knight-capital-2012": (
        "src/content/docs/prerequisites/modern-devops/module-1.1-infrastructure-as-code.md",
        "Knight Capital 2012",
    ),
    "tesla-2018-cryptojacking": (
        "src/content/docs/k8s/cks/part1-cluster-setup/module-1.5-gui-security.md",
        "Tesla 2018 cryptojacking",
    ),
    "capital-one-2019": (
        "src/content/docs/k8s/cks/part1-cluster-setup/module-1.4-node-metadata.md",
        "Capital One 2019 breach",
    ),
    "gitlab-2017-db1": (
        "src/content/docs/prerequisites/zero-to-terminal/module-0.2-what-is-a-terminal.md",
        "GitLab 2017 db1 incident",
    ),
    "equifax-2017": (
        "src/content/docs/prerequisites/cloud-native-101/module-1.2-docker-fundamentals.md",
        "Equifax 2017 breach",
    ),
    "facebook-2021-bgp": (
        "src/content/docs/cloud/aws-essentials/module-1.5-route53.md",
        "Facebook 2021 BGP outage",
    ),
    "solarwinds-2020": (
        "src/content/docs/prerequisites/modern-devops/module-1.3-cicd-pipelines.md",
        "SolarWinds 2020",
    ),
    "codecov-2021": (
        "src/content/docs/prerequisites/modern-devops/module-1.6-devsecops.md",
        "Codecov 2021 bash uploader",
    ),
    "log4shell": (
        "src/content/docs/platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security.md",
        "Log4Shell / CVE-2021-44228",
    ),
    "target-2013": (
        "src/content/docs/platform/foundations/security-principles/module-4.2-defense-in-depth.md",
        "Target 2013 breach",
    ),
    "uber-2022-hardcoded-creds": (
        "src/content/docs/k8s/cks/part4-microservice-vulnerabilities/module-4.3-secrets-management.md",
        "Uber 2022 hardcoded credentials",
    ),
    "aws-s3-useast1-2017": (
        "src/content/docs/platform/foundations/reliability-engineering/module-2.2-failure-modes-and-effects.md",
        "AWS S3 us-east-1 2017",
    ),
    "cloudflare-2020-bgp": (
        "src/content/docs/platform/foundations/advanced-networking/module-1.4-bgp-routing.md",
        "Cloudflare 2020 BGP / config",
    ),
    "netflix-chaos-monkey": (
        "src/content/docs/platform/disciplines/reliability-security/chaos-engineering/module-1.1-chaos-principles.md",
        "Netflix Chaos Monkey",
    ),
    "amazon-two-pizza": (
        "src/content/docs/platform/disciplines/core-platform/leadership/module-1.1-platform-team-building.md",
        "Amazon two-pizza teams",
    ),
    # Catalog incidents claimed by the prereqs sweep (#878 PR sequence). Once a sweep PR claims a
    # catalog incident, it becomes the canonical for that incident — same one-module rule applies.
    "github-2018-split-brain": (
        "src/content/docs/prerequisites/git-deep-dive/module-2-advanced-merging.md",
        "GitHub October 2018 split-brain",
    ),
    "atlassian-2022-deletion": (
        "src/content/docs/prerequisites/git-deep-dive/module-4-undo-recovery.md",
        "Atlassian April 2022 data deletion",
    ),
    "cloudflare-2022-bgp": (
        "src/content/docs/prerequisites/modern-devops/module-1.2-gitops.md",
        "Cloudflare BGP June 2022 policy reorder",
    ),
    "cloudflare-2019-regex": (
        "src/content/docs/prerequisites/modern-devops/module-1.3-cicd-pipelines.md",
        "Cloudflare 2019 regex outage",
    ),
    "github-2021-mysql": (
        "src/content/docs/prerequisites/modern-devops/module-1.4-observability.md",
        "GitHub August 2021 MySQL degradation",
    ),
    # Catalog incidents claimed by the KCSA + KCNA sweep (#878 PR sequence).
    "siloscape-2021": (
        "src/content/docs/k8s/kcsa/part2-cluster-component-security/module-2.2-node-security.md",
        "Siloscape 2021 Windows container escape",
    ),
    "xz-utils-2024": (
        "src/content/docs/k8s/kcsa/part4-threat-model/module-4.4-supply-chain.md",
        "XZ Utils backdoor CVE-2024-3094",
    ),
}

# Always-forbidden incidents — these have NO canonical and may not appear
# anywhere in the curriculum. Fictional/templated stories per user 2026-05-04.
FORBIDDEN = (
    "Fictional / fabricated incident names",
    "Templated 'fintech + Black Friday + $X.X million' trope",
)

# Reverse map: incident label → slug
LABEL_TO_SLUG = {label: slug for slug, (_, label) in CANONICALS.items()}

XREF_RE = re.compile(r"<!--\s*incident-xref:\s*([a-z0-9\-]+)\s*-->", re.IGNORECASE)


def relpath(p: Path) -> str:
    return str(p.relative_to(REPO))


def has_xref_near(text: str, match_start: int, match_end: int, slug: str, window: int = 200) -> bool:
    """True if an <!-- incident-xref: SLUG --> marker exists within `window` chars."""
    near_start = max(0, match_start - window)
    near_end = min(len(text), match_end + window)
    for m in XREF_RE.finditer(text[near_start:near_end]):
        if m.group(1).lower() == slug.lower():
            return True
    return False


def scan_for_violations() -> tuple[list[dict], int]:
    files = sorted(p for p in SCOPE.rglob("*.md") if in_scope(p))
    violations: list[dict] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = relpath(path)
        for incident_label, patterns in INCIDENTS.items():
            for pat in patterns:
                m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
                if not m:
                    continue

                # Forbidden incident — never allowed anywhere.
                if incident_label in FORBIDDEN:
                    violations.append({
                        "file": rel,
                        "incident": incident_label,
                        "kind": "forbidden",
                        "snippet": _snippet(text, m),
                        "remediation": "Replace with a concept-led 'Why This Module Matters' section per docs/audits/2026-05-04-incident-canonicals.md (option (c)). No fabricated incidents.",
                    })
                    break

                slug = LABEL_TO_SLUG.get(incident_label)
                if slug is None:
                    # Tracked but no canonical assigned (low-volume incident).
                    # We still complain if it appears in 2+ files — but that
                    # check is handled below in the second pass.
                    break

                canonical_rel = CANONICALS[slug][0]
                if rel == canonical_rel:
                    break  # canonical may mention freely

                if has_xref_near(text, m.start(), m.end(), slug):
                    break  # marked cross-reference is allowed

                violations.append({
                    "file": rel,
                    "incident": incident_label,
                    "kind": "duplicate",
                    "canonical": canonical_rel,
                    "snippet": _snippet(text, m),
                    "remediation": (
                        f"Either (a) replace this paragraph with a different real incident "
                        f"from docs/audits/2026-05-04-incident-replacement-catalog.md, "
                        f"(b) shorten to a one-sentence cross-reference and add "
                        f"<!-- incident-xref: {slug} --> within 200 chars, "
                        f"or (c) drop the dramatic opener and write a concept-led WTMM."
                    ),
                })
                break  # one violation per (file, incident) is enough

    # Second pass: incidents WITHOUT a canonical that appear in 2+ files.
    files_per_incident: dict[str, list[str]] = {}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for incident_label, patterns in INCIDENTS.items():
            if incident_label in FORBIDDEN or incident_label in LABEL_TO_SLUG:
                continue
            for pat in patterns:
                if re.search(pat, text, flags=re.IGNORECASE | re.DOTALL):
                    files_per_incident.setdefault(incident_label, []).append(relpath(path))
                    break

    second_pass = 0
    for incident_label, paths in files_per_incident.items():
        if len(paths) > 1:
            second_pass += 1
            for p in paths:
                violations.append({
                    "file": p,
                    "incident": incident_label,
                    "kind": "untracked-duplicate",
                    "all_files": paths,
                    "remediation": (
                        f"This incident appears in {len(paths)} files but has no canonical "
                        f"assignment. Add it to docs/audits/2026-05-04-incident-canonicals.md "
                        f"and rewrite duplicates per the rule."
                    ),
                })

    return violations, len(files)


def _snippet(text: str, m: re.Match) -> str:
    s = max(0, m.start() - 30)
    e = min(len(text), m.end() + 30)
    out = re.sub(r"\s+", " ", text[s:e]).strip()
    if len(out) > 140:
        out = out[:137] + "..."
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    try:
        violations, total = scan_for_violations()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        json.dump(
            {"total_files": total, "violations": violations},
            sys.stdout,
            indent=2,
            default=str,
        )
        sys.stdout.write("\n")
    else:
        print(f"scanned {total} module files")
        if not violations:
            print("OK — no incident-reuse violations.")
            return 0
        by_incident: dict[str, list[dict]] = {}
        for v in violations:
            by_incident.setdefault(v["incident"], []).append(v)
        print(f"\nFOUND {len(violations)} violations across {len(by_incident)} incidents:\n")
        for incident, vs in sorted(by_incident.items(), key=lambda kv: -len(kv[1])):
            print(f"  {len(vs):3d}  {incident}  [{vs[0]['kind']}]")
            for v in vs[:5]:
                print(f"        - {v['file']}")
            if len(vs) > 5:
                print(f"        ... and {len(vs) - 5} more")
        print()
        print("Remediation:")
        print("  (a) Replace with a different real incident from")
        print("      docs/audits/2026-05-04-incident-replacement-catalog.md")
        print("  (b) Shorten to a cross-reference + add <!-- incident-xref: SLUG --> marker")
        print("  (c) Drop the dramatic opener; write a concept-led WTMM section")
        print()
        print("See docs/audits/2026-05-04-incident-canonicals.md for the full ruleset.")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())

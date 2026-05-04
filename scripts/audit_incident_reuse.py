#!/usr/bin/env python3
"""Deterministic curriculum-wide audit of repeated incident/anecdote use.

Scans every module .md file in scope and counts files (not occurrences) that
mention each tracked incident. Outputs a markdown table sorted by file count,
plus per-incident file lists with a short framing snippet.

Scope:
  src/content/docs/**/*.md
  EXCLUDING: uk/, ai-history/, ai-ml-engineering/history/, index.md files

Usage:
  python3 scripts/audit_incident_reuse.py [--out PATH]

The keyword catalog below is the single source of truth for what counts as
"the same incident." Each incident is matched if ANY of its key phrases
appear (case-insensitive). Phrases are tuned to avoid false positives —
e.g. "Tesla" alone is too broad (matches Nikola Tesla in physics modules),
so we require "Tesla" + a 2018-cryptojacking signal.
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCOPE = REPO / "src" / "content" / "docs"
EXCLUDE_DIRS = ("/uk/", "/ai-history/", "/ai-ml-engineering/history/")

# Each incident: a label + a list of regex patterns. A file "contains" the
# incident if ANY of its patterns matches. Patterns are case-insensitive.
# Use phrase-pairs (entity + signal) to avoid name collisions.
INCIDENTS: dict[str, list[str]] = {
    "Knight Capital 2012": [
        r"Knight Capital",
        r"\$4[46]0\s*million.{0,40}45\s*minutes",
    ],
    "Tesla 2018 cryptojacking": [
        # Require Tesla within 800 chars of an unambiguous incident signal.
        # `nvidia-tesla-t4` (GPU model) is filtered: it doesn't co-occur with these signals.
        # Variants of cryptojacking phrasing: cryptojacking, cryptomining, crypto-mining,
        # cryptocurrency mining, mining cryptocurrency, mine cryptocurrency, Monero, xmrig.
        r"Tesla[^a-zA-Z0-9].{0,800}(crypto[\s\-]?(jack|min|miner)|(mining|mine)\s+(cryptocurrency|crypto)|(cryptocurrency|crypto)\s+(mining|miner)|monero|xmrig|redlock|exposed (\w+\s+){0,3}(dashboard|console|admin|infrastructure)|2018.{0,80}(breach|compromise|incident|attack))",
        r"(crypto[\s\-]?(jack|min|miner)|(mining|mine)\s+(cryptocurrency|crypto)|(cryptocurrency|crypto)\s+(mining|miner)|monero|xmrig|redlock).{0,800}Tesla[^a-zA-Z0-9]",
    ],
    "Uber 2022 hardcoded credentials": [
        # Critical: \bUber\b — without word boundary "Uber" matches inside "kUBERnetes".
        r"\bUber\b.{0,400}(hardcoded|hard-coded|admin password|network share|PowerShell|Thycotic|MFA fatigue|2022.{0,40}breach|Lapsus)",
        r"(hardcoded|hard-coded).{0,400}\bUber\b",
    ],
    "Capital One 2019 breach": [
        r"Capital One.{0,200}(2019|WAF|SSRF|metadata|106 million|100 million)",
    ],
    "SolarWinds 2020": [
        r"SolarWinds",
        r"Orion.{0,40}(supply chain|build|update|compromise)",
    ],
    "Codecov 2021 bash uploader": [
        r"Codecov",
    ],
    "Log4Shell / CVE-2021-44228": [
        r"Log4Shell",
        r"CVE-2021-44228",
        r"log4j.{0,40}(vuln|RCE|2021)",
    ],
    "Equifax 2017 breach": [
        r"Equifax",
        r"143\s*million.{0,40}(records|people|consumers)",
        r"147\s*million.{0,40}(records|people|consumers)",
    ],
    "Heartbleed CVE-2014-0160": [
        r"Heartbleed",
        r"CVE-2014-0160",
    ],
    "Maersk NotPetya 2017": [
        r"NotPetya",
        r"Maersk.{0,200}(ransomware|wiper|2017|NotPetya)",
    ],
    "WannaCry 2017": [
        r"WannaCry",
    ],
    "GitLab 2017 db1 incident": [
        # Widened: catches "2017 GitLab database outage", "Postmortem of database outage of January 31",
        # "fatigued admin... replication lag", and other variant phrasings.
        r"GitLab.{0,400}(2017|db1|rm[\s\-]rf|6[\s\-]hour|backup|replication lag|January 31|postmortem of database outage|database outage|production data loss|streamed live)",
        r"(rm[\s\-]rf|backup failed|replication lag|fatigued.{0,40}admin).{0,400}GitLab",
    ],
    "Cloudflare 2019 regex outage": [
        r"Cloudflare.{0,200}(regex|2019|July|backtrack|catastrophic)",
        r"(regex|catastrophic backtrack).{0,200}Cloudflare",
    ],
    "Cloudflare 2020 BGP / config": [
        r"Cloudflare.{0,200}(BGP|2020|configuration push)",
    ],
    "Facebook 2021 BGP outage": [
        # Require Facebook + outage-specific phrasing (not just "Facebook" + "BGP" — too many false positives in MetalLB/Cilium context).
        r"(Facebook|Meta).{0,400}(October 2021|2021.{0,40}outage|disappeared from the internet|disconnected.{0,40}data center|six[\s\-]hour outage|locked out)",
        r"(October 2021|disappeared from the internet|six[\s\-]hour outage).{0,400}(Facebook|Meta)",
    ],
    "AWS S3 us-east-1 2017": [
        r"AWS.{0,80}S3.{0,80}us-east-1",
        r"S3.{0,80}us-east-1.{0,80}(2017|outage)",
    ],
    "CrowdStrike 2024 Falcon outage": [
        r"CrowdStrike.{0,200}(Falcon|2024|July 19|kernel|BSOD|sensor)",
    ],
    "Slack outage": [
        # Tightened: must explicitly reference Slack THE PRODUCT going down, not "notified the team via Slack".
        r"Slack.{0,80}(was down|was unavailable|outage in (January|February) 202[12]|January 4, 2021)",
        r"(was down|was unavailable).{0,80}Slack",
    ],
    "Robinhood / GameStop": [
        r"Robinhood.{0,80}(GameStop|outage|2021|halt)",
    ],
    "TeamTNT cryptojacking": [
        r"TeamTNT",
    ],
    "Kinsing cryptojacking": [
        r"Kinsing",
    ],
    "Sony PSN 2011": [
        r"Sony.{0,80}(PSN|PlayStation Network|2011)",
    ],
    "Code Spaces 2014": [
        r"Code Spaces",
    ],
    "Target 2013 breach": [
        r"Target.{0,80}(2013|breach|HVAC|40 million)",
    ],
    "ChaosDB 2021": [
        r"ChaosDB",
        r"CosmosDB.{0,80}(Jupyter|metadata|2021|Wiz)",
    ],
    "Argo CD path-traversal CVE-2022-24348": [
        r"CVE-2022-24348",
        r"Argo CD.{0,80}(path traversal|2022|CVE)",
    ],
    "3CX 2023 supply chain": [
        r"3CX",
    ],
    "MOVEit 2023": [
        r"MOVEit",
    ],
    "Spring4Shell CVE-2022-22965": [
        r"Spring4Shell",
        r"CVE-2022-22965",
    ],
    "Microsoft 38TB SAS-token leak 2023": [
        r"38\s*TB.{0,80}(SAS|leak)",
        r"Microsoft AI.{0,80}(SAS|2023|leak)",
    ],
    "Toyota 2022 / 2023 GitHub leak": [
        r"Toyota.{0,200}(GitHub|2022|2023|leaked|exposed)",
    ],
    "Mercedes-Benz 2024 GitHub token": [
        r"Mercedes.{0,80}(GitHub|token|2024)",
    ],
    "Netflix Chaos Monkey": [
        r"Chaos Monkey",
    ],
    "Spotify squad model": [
        r"Spotify.{0,80}(squad|tribe|chapter|guild)",
    ],
    "Amazon two-pizza teams": [
        r"two[\s\-]pizza",
    ],
    "Knight Capital generic 'deploy to N of M' trope": [
        r"\b(7|seven) of (8|eight)\s*servers",
    ],
    "Holiday / Black Friday outage trope": [
        r"Black Friday.{0,80}(outage|down|incident|disaster|peak)",
        r"holiday.{0,40}(launch|sale).{0,200}(outage|down|broke|crashed)",
    ],
    "Ericsson 2018 certificate expiration": [
        r"Ericsson.{0,200}(certificate|expired|expir|2018)",
        r"(O2|SoftBank).{0,200}(certificate|expir).{0,200}(2018|December)",
    ],
    "Fictional / fabricated incident names": [
        # User: "you cannot fool a human" — these are made-up company names with manufactured stats.
        # Enumerate known fabricated names from the explore-agent sample. Add more as discovered.
        r"GlobalTradeX",
        r"GlobalPay\b",
        r"GlobalBank\b",
        r"AcmeCorp",
        r"AcmeCo\b",
        r"FintechCo\b",
        r"PayCorp\b",
        r"ShopWell\b",
        r"FastShop\b",
    ],
    "Templated 'fintech + Black Friday + $X.X million' trope": [
        # Structural reuse of made-up incident: payment/fintech company + holiday + dollar-figure loss.
        # Two-step match: needs all of [payment|fintech|e-commerce|checkout] + [Black Friday|Cyber Monday|holiday] + [$N.N million|$N million].
        r"(payment|fintech|e-?commerce|checkout|retailer).{0,400}(Black Friday|Cyber Monday|holiday).{0,400}\$[\d.]+\s*million",
        r"(Black Friday|Cyber Monday).{0,400}(payment|fintech|e-?commerce|checkout|retailer).{0,400}\$[\d.]+\s*million",
    ],
}


def in_scope(p: Path) -> bool:
    s = str(p)
    if any(d in s for d in EXCLUDE_DIRS):
        return False
    if p.name == "index.md":
        return False
    return True


def scan() -> tuple[dict[str, list[tuple[Path, str]]], list[Path]]:
    files = sorted(p for p in SCOPE.rglob("*.md") if in_scope(p))
    hits: dict[str, list[tuple[Path, str]]] = defaultdict(list)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for incident, patterns in INCIDENTS.items():
            for pat in patterns:
                m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
                if m:
                    start = max(0, m.start() - 30)
                    end = min(len(text), m.end() + 30)
                    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
                    if len(snippet) > 140:
                        snippet = snippet[:137] + "..."
                    hits[incident].append((path, snippet))
                    break
    return hits, files


def relpath(p: Path) -> str:
    return str(p.relative_to(REPO))


def render_markdown(hits: dict[str, list[tuple[Path, str]]], total: int) -> str:
    incidents_sorted = sorted(
        hits.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )
    lines = []
    lines.append("# Curriculum-wide incident-reuse audit")
    lines.append("")
    lines.append(f"Generated by `scripts/audit_incident_reuse.py` over {total} module files in scope.")
    lines.append("")
    lines.append("Scope: `src/content/docs/**/*.md`, excluding `uk/`, `ai-history/`, `ai-ml-engineering/history/`, and `index.md` files.")
    lines.append("")
    lines.append("## Summary table")
    lines.append("")
    lines.append("| Incident | Files |")
    lines.append("|---|---|")
    for incident, occurrences in incidents_sorted:
        if not occurrences:
            continue
        lines.append(f"| {incident} | {len(occurrences)} |")
    lines.append("")
    lines.append("Hard rule (per user, 2026-05-04): each named incident may appear in at most ONE module. Anything above 1 in the table needs de-duplication.")
    lines.append("")
    lines.append("## Per-incident file lists")
    lines.append("")
    for incident, occurrences in incidents_sorted:
        if not occurrences:
            continue
        lines.append(f"### {incident}")
        lines.append("")
        lines.append(f"**Files: {len(occurrences)}**")
        lines.append("")
        for path, snippet in occurrences:
            lines.append(f"- `{relpath(path)}` — _{snippet}_")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "docs" / "audits" / "2026-05-04-incident-reuse.md")
    args = ap.parse_args()

    hits, files = scan()
    md = render_markdown(hits, total=len(files))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    print(f"wrote {args.out} ({len(files)} files scanned, {sum(1 for v in hits.values() if v)} incidents matched)")
    print()
    print("Top 10 by file count:")
    for incident, occurrences in sorted(hits.items(), key=lambda kv: -len(kv[1]))[:10]:
        if occurrences:
            print(f"  {len(occurrences):3d}  {incident}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

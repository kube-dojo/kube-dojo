# Incident canonicals — locked 2026-05-04

> **Hard rule (per user, 2026-05-04):** every named real-world incident appears in at most ONE module across the entire EN curriculum. The canonical module is the only one allowed to *tell the story*; every other module that needs to invoke the lesson either (a) uses a different real, verifiable incident, (b) cross-references the canonical with a single sentence + relative link, or (c) drops the dramatic-opener and uses a concept-led "Why This Module Matters" section instead.
>
> Fabricated companies (GlobalTradeX, AcmeCorp, etc.) and templated "fintech + Black Friday + $X.X million" stories are NEVER acceptable. The user's standard: *"no bullshit, humans are very receptive for that — you cannot fool a human."*

## Lock table

**#878 closed 2026-05-06.** All 33 incident-reuse violations have been resolved. The gate (`scripts/quality/incident_dedup_gate.py`) now runs in `absolute` mode by default and is required on every PR via `.github/workflows/incident-dedup.yml`. New canonical assignments are allowed; new incident additions must be claimed in this doc as part of the introducing PR.

| # | Incident | Canonical module | Lesson it owns |
|---|---|---|---|
| 1 | Knight Capital 2012 | `prerequisites/modern-devops/module-1.1-infrastructure-as-code.md` | Fleet drift / partial deployment / "7 of 8 servers" |
| 2 | Tesla 2018 cryptojacking | `k8s/cks/part1-cluster-setup/module-1.5-gui-security.md` | Exposed Kubernetes dashboard without authentication |
| 3 | Capital One 2019 breach | `k8s/cks/part1-cluster-setup/module-1.4-node-metadata.md` | IMDSv1 SSRF → cloud IAM credential extraction |
| 4 | GitLab.com 2017 db1 incident | `prerequisites/zero-to-terminal/module-0.2-what-is-a-terminal.md` | Terminal-context confusion → wrong env command |
| 5 | Equifax 2017 breach | `prerequisites/cloud-native-101/module-1.2-docker-fundamentals.md` | Unpatched dependency / Apache Struts |
| 6 | Facebook 2021 BGP outage | `cloud/aws-essentials/module-1.5-route53.md` | DNS / routing global blast-radius |
| 7 | SolarWinds 2020 supply chain | `prerequisites/modern-devops/module-1.3-cicd-pipelines.md` | Build-environment compromise / artifact provenance |
| 8 | Codecov 2021 bash uploader | `prerequisites/modern-devops/module-1.6-devsecops.md` | CI tool supply-chain compromise |
| 9 | Log4Shell / CVE-2021-44228 | `platform/disciplines/reliability-security/devsecops/module-4.4-supply-chain-security.md` | Transitive-dependency vulnerability management |
| 10 | Target 2013 breach | `platform/foundations/security-principles/module-4.2-defense-in-depth.md` | HVAC vendor → segmentation / defense-in-depth |
| 11 | Uber 2022 hardcoded credentials | `k8s/cks/part4-microservice-vulnerabilities/module-4.3-secrets-management.md` | Hardcoded admin credentials in deployment scripts |
| 12 | AWS S3 us-east-1 2017 outage | `platform/foundations/reliability-engineering/module-2.2-failure-modes-and-effects.md` | Typo in production command / blast-radius |
| 13 | Cloudflare 2020 BGP / config | `platform/foundations/advanced-networking/module-1.4-bgp-routing.md` | BGP misconfiguration / global routing blast-radius |
| 14 | Netflix Chaos Monkey (concept) | `platform/disciplines/reliability-security/chaos-engineering/module-1.1-chaos-principles.md` | Deliberate failure injection / resilience testing |
| 15 | Amazon two-pizza teams (concept) | `platform/disciplines/core-platform/leadership/module-1.1-platform-team-building.md` | Org/team sizing for autonomy |

All paths verified to exist on `main` 2026-05-04.

## Disposition rule for non-canonical occurrences

When a module currently uses one of the above incidents but is NOT the canonical, choose ONE of:

**(a) Replace with a different real, verifiable incident** — pick from the catalog at `docs/audits/2026-05-04-incident-replacement-catalog.md`. The replacement must topically fit the module's lesson AND be primary-source verifiable (publication URL + year + verbatim citation, per the citation_v3 rules in `docs/research/citation-rules.md`). No Wikipedia. No LLM-confabulated arxiv IDs.

**(b) Cross-reference the canonical** — one sentence + relative link, no story re-telling. Example pattern:
> *Engineers who want the deployment-control case study should see [the Knight Capital walkthrough in module 1.1](../modern-devops/module-1.1-infrastructure-as-code/).*

**(c) Drop the dramatic opener entirely** — write a concept-led "Why This Module Matters" section. Lead with the principle, the operational stakes, and what the learner will be able to do after the module. No fabricated company anecdotes. No invented dollar figures. No "imagine you're at a fintech company" filler.

## Special handling: fabricated / templated stories

The audit flagged 3 modules using the templated "fintech + Black Friday + $X.X million" trope and 2 using fictional company names (GlobalTradeX et al.). These do NOT get a canonical and do NOT get a 1:1 replacement. Per user direction 2026-05-04, they are rewritten as **concept-led WTMM** (option (c) above). Reason: a fabricated incident in the curriculum is dishonest framing — readers smell it immediately, and once trust breaks, the rest of the module's authority breaks with it.

## What this doc is NOT

This is the canonical-assignment lock. The actual story rewrites + replacement-incident research live in:
- `docs/audits/2026-05-04-incident-replacement-catalog.md` — verified real incidents the sweep agents may use as replacements
- `docs/audits/2026-05-04-incident-reuse.md` — the per-incident file list (refresh: `python3 scripts/audit_incident_reuse.py`)
- `scripts/check_incident_reuse.py` — CI guardrail enforcing the "max 1 per incident" rule

This doc is read-only ground-truth for sweep agents. If you need to change a canonical assignment, update this file with a dated rationale; don't silently re-pick.

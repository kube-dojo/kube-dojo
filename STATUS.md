# Session Status

> **Read this first every session. Update before ending.**

## Current State

**568 modules** across 6 tracks. **115 Ukrainian translations** (~40% of certs + prereqs).

**Website:** https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build)

**Site tabs:** Home | Fundamentals | Linux | Cloud | Certifications | Platform | On-Premises

## Curriculum Summary

| Track | Modules | Status |
|-------|---------|--------|
| Fundamentals | 33 | Complete |
| Linux Deep Dive | 37 | Complete |
| Cloud | 84 | Complete |
| Certifications (CKA/CKAD/CKS/KCNA/KCSA/Extending + 12 learning paths) | 175 | Complete |
| Platform Engineering | 209 | Complete |
| On-Premises Kubernetes | 30 | Complete (needs Gemini review) |
| **Total** | **568** | **Complete** |

### Certifications Breakdown
| Cert | Modules |
|------|---------|
| CKA | 47 |
| CKAD | 30 |
| CKS | 30 |
| KCNA | 28 |
| KCSA | 26 |
| Extending K8s | 8 |

### Cloud Breakdown
| Section | Modules |
|---------|---------|
| Hyperscaler Rosetta Stone | 1 |
| AWS Essentials | 12 |
| GCP Essentials | 12 |
| Azure Essentials | 12 |
| Architecture Patterns | 4 |
| EKS Deep Dive | 5 |
| GKE Deep Dive | 5 |
| AKS Deep Dive | 4 |
| Advanced Operations | 10 |
| Managed Services | 10 |
| Enterprise & Hybrid | 10 |

### On-Premises Breakdown
| Section | Modules |
|---------|---------|
| Planning & Economics | 4 |
| Bare Metal Provisioning | 4 |
| Networking | 4 |
| Storage | 3 |
| Multi-Cluster | 3 |
| Security | 4 |
| Operations | 5 |
| Resilience | 3 |

### Platform Engineering Breakdown
| Section | Modules |
|---------|---------|
| Foundations | 32 |
| Disciplines (SRE, Platform Eng, GitOps, DevSecOps, MLOps, AIOps + Release Eng, Chaos Eng, FinOps, Data Eng, Networking, AI/GPU Infra, Leadership) | 71 |
| Toolkits (17 categories) | 96 |
| Supply Chain Defense Guide | 1 |
| CNPE Learning Path | 1 |

### Ukrainian Translations
| Track | Translated | Total |
|-------|-----------|-------|
| Prerequisites | 35 | 33 |
| CKA | 47 | 47 |
| CKAD | 30 | 30 |
| CKS | 0 | 30 |
| KCNA | 0 | 28 |
| KCSA | 0 | 26 |
| **Total** | **115** | **558** |

## Quality Standard

**Rubric-based quality system** (docs/quality-rubric.md): 7 dimensions scored 1-5. Pass = avg >= 3.5, no dimension at 1.

**Audit results** (docs/quality-audit-results.md, 2026-04-03): 31 modules scored.
- Overall avg: 3.3/5 (GOOD)
- Gold standard: Systems Thinking (4.6), On-Prem Case (4.4)
- 5 critical stubs fixed (expanded from 49-74 lines to 266-918 lines)
- 3 high-priority modules improved (API Deprecations, etcd-operator, Deployments)
- Remaining: 8 medium, 11 low priority modules need improvements

**Systemic issues found & being addressed**:
1. No modules had formal learning outcomes → added to all rewritten modules + codified in writer prompt
2. Active learning back-loaded to end in 87% of modules → inline prompts added to rewrites
3. Quiz questions tested recall not understanding → scenario-based quizzes in all rewrites

## Open GitHub Issues

| # | Issue | Status |
|---|-------|--------|
| #14 | Curriculum Monitoring & Official Sources | Open |
| #143 | Ukrainian Translation — Full Coverage | Open (~40%) |
| #157 | Supabase Auth + Progress Migration | Open |
| #156 | CKA Parts 3-5 Labs | Open |
| #165 | Epic: Pedagogical Quality Review | Open (Phases 1-3,5 done; Phase 4 in progress) |
| #177 | Improve Lowest-Quality Modules | Open (8 critical/high done, ~19 remaining) |
| #179 | Improve Lowest-Quality Labs | Open (blocked on Phase 3 lab audit) |

## Recently Closed (Session 3)
| # | Issue | Status |
|---|-------|--------|
| #174 | Phase 1: Research Educational Frameworks | Closed — docs/pedagogical-framework.md |
| #175 | Phase 2: Create Quality Rubric | Closed — docs/quality-rubric.md |
| #176 | Phase 3: Audit Modules Against Rubric | Closed — 31 modules scored |
| #178 | Phase 5: Codify Quality Standards | Closed — writer prompt, rules, skill updated |
| #170-173 | Gemini's buzzword issues | Closed — replaced by concrete sub-tickets |

## TODO

- [x] Prerequisites: all 33 modules improved (outcomes, inline prompts, quiz upgrades, emoji fixes) — EN + UK complete
- [x] Linux: all 37 modules improved (outcomes added) — EN + UK complete
- [x] CKA: all 41 modules improved (outcomes + inline prompts on Part 0 and troubleshooting) — EN complete, UK syncing
- [ ] CKAD: 24 modules — outcomes being added (agent running)
- [ ] CKS/KCNA/KCSA: 84 modules — outcomes being added (agent running)
- [ ] Remaining: Cloud (84), Platform (209), On-Prem (30) — #180
- [ ] Lab quality audit and improvements — #179
- [ ] Gemini adversary review remaining on-prem + discipline modules
- [ ] Ukrainian translations: CKS (30), KCNA (28), KCSA (26)
- [ ] Visual aid beautification pass (alignment, ASCII formatting)

## Blockers
None

## Key Decisions
- Migrated from MkDocs Material to Starlight (Astro) — faster builds, proper i18n, modern stack
- `scripts/dispatch.py` replaces `ai_agent_bridge/` — direct CLI dispatch, no SQLite broker
- GH Actions pinned to commit SHA, requirements locked with hashes, Dependabot enabled
- Pinned zod@3.25.76 (zod v4 breaks Starlight schema validation)
- `defaultLocale: 'root'` for Starlight i18n — English at root URLs, Ukrainian at `/uk/`
- On-prem modules written by parallel agents (~500 lines each), need Gemini adversary review

---
**Maintenance Rule**: Claude updates this file at session end or after completing modules.

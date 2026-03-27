# Session Status

> **Read this first every session. Update before ending.**

## Current State

**568 modules** across 6 tracks. **115 Ukrainian translations** (~40% of certs + prereqs).

**Website:** https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build)

**Site tabs:** Home | What's New | Fundamentals | Cloud | Certifications | Platform Engineering

## Curriculum Summary

| Track | Modules | Status |
|-------|---------|--------|
| Prerequisites | 33 | Complete |
| Linux (Everyday Use + Deep Dive) | 37 | Complete |
| Cloud | 85 | Complete |
| Certifications (CKA/CKAD/CKS/KCNA/KCSA/Extending) | 169 | Complete |
| Platform Engineering | 204 | Complete |
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
10/10 quality = 4 "Did You Know?" facts, war stories with financial impact, 8 quiz questions, hands-on exercises.

All completed modules meet this standard. 329 modules adversary-reviewed by Gemini (4 phases, 95%+ scored 9.5-10/10).

**~95 modules reviewed in Session 2** (47 fixes applied). **~30 on-prem + ~30 discipline modules still need review.**

## Open GitHub Issues

| # | Issue | Status |
|---|-------|--------|
| #14 | Curriculum Monitoring & Official Sources | Open |
| #105 | Ukrainian Translation (Phase 1) | Open (~40%) |
| #135 | On-Premises Track | Closed — 30 modules, 16,241 lines |

## Recently Closed (Session 2)
| # | Issue | Status |
|---|-------|--------|
| #129 | Review .claude/skills/ | Closed — 12→4 skills |
| #130 | Migrate to Starlight | Closed — 1,298 pages, ~30s build |
| #131 | Give Gemini proper tools | Closed — dispatch.py |
| #135 | On-Premises K8s Track | Closed — 30 modules |

## TODO

- [ ] Gemini adversary review ~10 remaining on-prem modules (20/30 done, 16 fixed)
- [ ] Gemini adversary review ~32 discipline modules
- [ ] Theme overhaul: visual verification in browser (#136, #137, #138, #139)
- [ ] Theme overhaul Phase 3: MDX components (#140)
- [ ] Theme overhaul Phase 4: breadcrumbs + prev/next (#141)
- [ ] Ukrainian translations: CKS (30), KCNA (28), KCSA (26)
- [ ] Ukrainian sidebar labels (`src/content/i18n/uk.json`)

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

# Session Status

> **Read this first every session. Update before ending.**

## Current State

**541 English modules** across 5 tracks. **115 Ukrainian translations** (~40% of certs + prereqs).

**Website:** https://kube-dojo.github.io/ (MkDocs Material, pinned mkdocs<2.0.0, 0 warnings)

**Site tabs:** Home | What's New | Fundamentals | Cloud | Certifications | Platform Engineering

## Curriculum Summary

| Track | Modules | Status |
|-------|---------|--------|
| Prerequisites | 33 | Complete |
| Linux (Everyday Use + Deep Dive) | 37 | Complete |
| Cloud | 85 | Complete |
| Certifications (CKA/CKAD/CKS/KCNA/KCSA/Extending) | 169 | Complete |
| Platform Engineering | 217 | Complete |
| **Total** | **541** | **Complete** |

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

### Platform Engineering Breakdown
| Section | Modules |
|---------|---------|
| Foundations | 32 |
| Disciplines (SRE, Platform Eng, GitOps, DevSecOps, MLOps, AIOps + Release Eng, Chaos Eng, FinOps, Data Eng, Networking, AI/GPU Infra, Leadership) | 71 |
| Toolkits (17 categories) | 96 |
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
| **Total** | **115** | **541** |

## Quality Standard
10/10 quality = 4 "Did You Know?" facts, war stories with financial impact, 8 quiz questions, hands-on exercises.

All completed modules meet this standard. 329 modules adversary-reviewed by Gemini (4 phases, 95%+ scored 9.5-10/10).

**~100+ newer modules still need Gemini adversary review** (Cloud track, Extending K8s, new disciplines).

## Open GitHub Issues

| # | Issue | Status |
|---|-------|--------|
| #14 | Curriculum Monitoring & Official Sources | Open |
| #105 | Ukrainian Translation (Phase 1) | Open (~40%) |
| #129 | Review and enrich .claude/skills/ | Open |
| #130 | Migrate from MkDocs to Starlight (Astro) | Open |
| #131 | Give Gemini proper tools | Done (dispatch.py replaces bridge) |

## TODO

- [ ] Close #131 — dispatch.py migration complete
- [ ] Run Gemini adversary review on ~100+ unreviewed modules
- [ ] #130 — Starlight migration (MkDocs is dead)
- [ ] #129 — Review/consolidate .claude/skills/
- [ ] Ukrainian translations: CKS (30), KCNA (28), KCSA (26) + all new content
- [ ] Push 36 unpushed commits to remote

## Blockers
None

## Key Decisions
- Gemini drafts (350-400 lines) need Claude expansion to 700-900+ lines
- Cloud track organized by provider, not by topic
- MkDocs 2.0 blocked — pinned to <2.0.0, future migration to Starlight/Astro (#130)
- `scripts/dispatch.py` replaces `ai_agent_bridge/` — direct CLI dispatch, no SQLite broker

---
**Maintenance Rule**: Claude updates this file at session end or after completing modules.

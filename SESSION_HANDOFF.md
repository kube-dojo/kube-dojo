# Session Handoff — 2026-03-26 (Session 2)

## What Was Done This Session

### Infrastructure Overhaul
- **Replaced ai_agent_bridge with dispatch.py** — 1,800+ lines → 230 lines. Direct CLI calls to Gemini/Claude, JSON logging to `.dispatch-logs/`. Gemini-reviewed, 3 deadlock bugs fixed.
- **Consolidated 12 skills → 4** — k8s-cert-expert, platform-expert, curriculum-writer, module-quality-reviewer. Closed #129.
- **Supply chain hardening** — Pinned all GH Actions to commit SHA, generated requirements.lock with hashes, enabled Dependabot. Closed #131.

### Starlight Migration (MkDocs → Astro) — #130 CLOSED
- Wrote `scripts/migrate-to-starlight.py` (converts 648 English + 115 Ukrainian files)
- Scaffolded Astro/Starlight project (astro.config.mjs, content.config.ts, custom CSS)
- Fixed critical bugs found via Chrome browser investigation:
  - 5,323 broken `.md` links → stripped extensions, slug-based routing
  - Dots stripped from slugs (module-1.1 → module-11) → explicit `slug:` frontmatter
  - Sidebar showing parent label on all children → only set on index pages
  - 2 corrupted Ukrainian files (watchdog output) → cleaned + added H1 titles
  - Pinned zod@3.25.76 (zod v4 breaks Starlight schema validation)
- Removed old MkDocs files (docs/, mkdocs.yml, requirements.txt, .venv)
- Rewrote health check for Starlight (frontmatter, link format, module count)
- Updated deploy workflow (Node.js 22 + npm ci + astro build)
- Build: 1,350+ pages in ~30-40s
- Created 17 missing index.md files for cert parts and Linux sections

### Gemini Adversary Reviews — ~95 modules reviewed, 47 fixes
| Track | Reviewed | Fixes |
|-------|----------|-------|
| AWS Essentials (12) | 12/12 | 14 fixes (SLR trust policy, Fargate startup time, S3 BucketKey, etc.) |
| GCP Essentials (12) | 10/12 | 5 fixes (IAM get-iam-policy, Compute Engine logging, Cloud Run flag, etc.) |
| Azure Essentials (12) | 9/12 | 9 fixes (Entra ID mgmt group, Blob cost math, Functions --os-type, etc.) |
| Architecture Patterns (4) | 4/4 | 3 fixes (version math, Istio warmupDurationSecs, aws:SourceVpc) |
| EKS/GKE/AKS Deep Dives (14) | 14/14 | 4 fixes (AKS CLI command, GKE API version, storage provisioner, Karpenter) |
| Advanced Ops + Managed Services (20) | 16/20 | 2 fixes (AWS route quota, GitLab date) |
| Extending K8s (8) | 8/8 | 2 fixes (CRD schema version, scheduler extenders) |
| New Disciplines (36) | 6/36 | 1 fix (Facebook outage date) |

### Content Written
- **Trivy/LiteLLM supply chain attack** (March 2026) — War story in 3 modules + "Did You Know" in Trivy module
- **Supply Chain Defense Guide** — Standalone practical guide (CI/CD hardening, dependency management, container security, K8s runtime defense, incident response). Added to nav + DevSecOps track.
- **On-Premises Kubernetes Track** — 30 NEW modules, 16,241 lines (#135 CLOSED)
  - Section 1: Planning & Economics (4 modules) — server sizing, NUMA, cluster topology, TCO
  - Section 2: Bare Metal Provisioning (4 modules) — datacenter fundamentals, PXE, Talos/Flatcar, Sidero/Metal3
  - Section 3: Networking (4 modules) — spine-leaf, BGP, MetalLB/kube-vip, DNS/certs
  - Section 4: Storage (3 modules) — architecture decisions, Ceph/Rook, local storage
  - Section 5: Multi-Cluster (3 modules) — private cloud platforms, shared CPs, CAPI
  - Section 6: Security (4 modules) — air-gapped, HSM/TPM, AD/LDAP/OIDC, compliance
  - Section 7: Operations (5 modules) — upgrades, firmware, auto-remediation, observability, capacity
  - Section 8: Resilience (3 modules) — multi-site DR, hybrid connectivity, cloud repatriation

### Fixes & Cleanup
- Updated stale index pages (prerequisites, cloud, certifications, toolkits)
- Fixed all build warnings (broken links, missing nav entries)
- Updated start-docs.sh for Astro, start-claude.sh for new STATUS.md format
- Updated translation rules and content checklist for Starlight
- Fixed PSU diagram (active/active not active/standby)
- Corrected latency stats (Amazon 100ms, not 1ms)
- Fixed NUMA/etcd claim (affects in-memory DBs, not etcd)
- Fixed TCO model (cloud pricing was 3x inflated)

## Current State

**558 modules** across 6 tracks:
- Prerequisites: 33
- Linux: 37
- Cloud: 85
- Certifications: 169
- Platform Engineering: 204
- **On-Premises: 30 (NEW)**

**Site**: Starlight/Astro, 1,350+ pages, ~30-40s build, deployed via GitHub Pages

## Open Issues
- #14 — Curriculum Monitoring (ongoing)
- #105 — Ukrainian Translation (~40% done)

## TODO Next Session
- **Gemini review the 30 on-prem modules** — written by agents, need adversary review
- **Gemini review remaining ~30 discipline modules** that timed out
- **Ukrainian sidebar labels** (`src/content/i18n/uk.json`)
- **Ukrainian translations** for CKS (30), KCNA (28), KCSA (26)
- **Update STATUS.md** with 558 module count and on-prem track
- **Clean up worktree branches** (`git branch -D worktree-agent-*`)

## Key Decisions
- Parallel agent strategy works: 4 agents wrote 16 modules in ~15 minutes (vs ~4 hours sequential)
- Starlight `defaultLocale: 'root'` keeps English at root URLs
- zod@3.25.76 pinned (zod v4 breaks Starlight)
- On-prem modules written at ~500 lines each (matches existing quality standard)
- Gemini reviews of agent-written content is critical — agents write good structure but may have technical inaccuracies

## Unpushed Commits
None — all pushed.

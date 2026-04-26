---
title: "What's New"
template: splash
sidebar:
  order: 2
  label: "What's New"
---

## April 26, 2026 — Site-wide Quality Rewrite + Route Design + AI History Book Planning

### Site-wide Module Quality Rewrite Underway
- A 384-module rewrite batch (issue #388) is grinding through the curriculum, lifting modules to a stricter pedagogical bar
- ~130 modules already shipped at the new bar with cross-family review or deferred-review approval
- Auto-approved modules carry a `qa_pending` banner until a real cross-family reviewer signs off; rewritten modules briefly carry a `revision_pending` banner that clears on completion
- Full lifecycle is tracked operator-side via the local API briefing — public lifecycle visibility is on the roadmap (#391)

### Section Health Surfaced on Index Pages
Section index pages now surface in-flight rework counts via a new `SectionHealthSummary` component (#390). Learners can see at a glance which sections are actively improving and which are stable. Hub pages roll up child counts.

### Curriculum Route Design Tightened
Hub pages were rewritten as **route guides** instead of catalogs (#246):
- The Platform Engineering hub now opens with three persona routes (SRE, DevEx Builder, Platform Architect) instead of an alphabetical section dump
- Platform Foundations and Platform Disciplines mirror the same persona-keyed shape with enriched per-section "best for" / "pair with" guidance
- The Kubernetes Certifications hub now leads with three personas (Operator, Developer, Security Specialist) instead of an alphabetical KCNA → KCSA → CKAD → CKA → CKS default that suggested the wrong starting point for most learners
- The Platform hub gained a "Common Entry Mistakes" callout that the earlier rewrite had dropped
- New bridge pages help learners cross between tracks: K8s → On-Prem, K8s → Platform Engineering, AI/ML → AI Platform Engineering, AI/ML → Private AI Infrastructure (also part of #246)

### AI History Book — 68-Chapter Expansion & First Drafts
The AI History Book epic (#394) has been expanded into a definitive 68-chapter roadmap, intertwining infrastructural milestones with critical mathematical breakthroughs (from Boole and Markov to Backpropagation and PageRank). The rigorous KubeDojo sourcing standard (claim-level matrices, primary/secondary confirmation) has been applied to Parts 1, 2, and 6. The first five chapters—covering George Boole, Alan Turing, Claude Shannon, Andrey Markov, and McCulloch & Pitts—have been drafted as the "Golden Standard" for the book's narrative tone.

### Internal Reliability Improvements
- Atomic-drain pattern documented for the quality pipeline — the deferred-review queue and the rewrite batch race when run concurrently, so they now alternate
- A reproducible silent-crash bug in the deferred-review drain script was identified and filed (#396)
- Cross-family review caught real quality bugs in route-design changes that build-clean alone missed (security-cert ordering inversion, redundant section bloat, relative-link drift) — reinforced the "do not skip cross-family review even on small content changes" rule

---

## April 16, 2026 — ZTT, AI/ML, Cert Prep, and Curriculum Routing

### Zero to Terminal Hardened
- `Zero to Terminal` theory converged to the stricter review bar
- early labs were audited and tightened instead of left as implicit backlog
- Ukrainian sync for ZTT was brought under the new translation-v2 control flow

### AI/ML Learner Path Expanded
The AI/ML track now has a clear local-first path instead of jumping straight into large-scale infrastructure.

New learner-facing modules include:
- Home AI Workstation Fundamentals
- Reproducible Python, CUDA, and ROCm Environments
- Notebooks, Scripts, and Project Layouts
- Home-Scale RAG Systems
- Notebooks to Production for ML/LLMs
- Small-Team Private AI Platform
- Single-GPU Local Fine-Tuning
- Multi-GPU Home-Lab Fine-Tuning
- Local Inference Stack for Learners
- Home AI Operations and Cost Model

### Certification Prep Gaps Closed
Dedicated exam-prep modules were added for:
- `LFCS`
- `CNPE`
- `CNPA`
- `CGOA`

This work also removed a lot of quiet `partial coverage elsewhere` debt from the learner experience.

### Route Guidance Improved
Major hub pages were refreshed so learners can move between tracks more intentionally:
- homepage
- Kubernetes certifications
- Cloud
- Platform Engineering
- On-Premises
- AI/ML Engineering

### Internal Delivery Infrastructure Improved
- v2 review / patch routing was hardened and aligned to the actual contract
- translation-v2 now handles Ukrainian sync with queue-style control
- the local monitor/API shows more deterministic queue state instead of only summary counts

---

## April 17, 2026 — New Top-Level AI Track

### AI Is Now a First-Class Learner Track

A new top-level `AI` track now exists for learners who need AI literacy and practical AI working habits before advanced AI/ML engineering.

Initial sections:
- `AI Foundations`
- `AI-Native Work`

This track is intentionally separate from `AI/ML Engineering`:
- `AI` is the accessible front door
- `AI/ML Engineering` remains the advanced builder path

### Why This Matters

The repo already had strong AI/ML engineering depth, but it was missing a true beginner-friendly AI literacy path.

The new track fills that gap with modules for:
- what AI is
- what LLMs are
- prompting basics
- verification
- privacy, safety, and trust
- using AI for learning, writing, research, and coding
- AI-native work habits, assistants, agents, and workflow design

---

## March 28, 2026 — Theme Overhaul + New Tracks

### Custom Design System
Complete visual redesign with K8s-themed design:
- **Custom homepage** with hero, terminal decoration, track cards, stats, learning path
- **Custom topbar** with K logo, 7 nav pills (Home, Fundamentals, Linux, Cloud, Certifications, Platform, On-Premises)
- **Smart sidebar** — shows current track's subsections, collapsible navigation, monospace module numbers
- **Breadcrumbs** on every module page
- **Meta chips** — colored complexity (Quick/Medium/Advanced) and time badges
- **Content enhancement** — War Story cards, Did You Know cards, quiz styling (all automatic, no .md changes needed)
- **Progress tracking** — Mark Complete button, sidebar checkmarks, [progress dashboard](/changelog/) with export/import
- **Dark/light mode** with proper support across all pages

### Networking Discipline — 5 NEW modules
CNI Architecture & Selection, Network Policy Design, Service Mesh Strategy, Ingress & Gateway API, Multi-Cluster Networking.

### Platform Leadership Discipline — 5 NEW modules
Building Platform Teams, Developer Experience Strategy, Platform as Product, Adoption & Migration, Scaling Platform Organizations.

### Supply Chain Defense Guide — 4 new sections
Transitive dependency auditing, registry quarantine defense, AI/LLM gateway security, credential rotation verification.

### Sidebar Labels Fixed
32 index.md files updated — no more raw directory names (e.g. `part0-environment` → "Part 0: Environment Setup").

### Linux Deep Dive — Top-Level Track
Linux moved from a Fundamentals subsection to its own top-level track (37 modules).

### All Certification Learning Paths in Sidebar
PCA, ICA, CCA, CGOA, CBA, OTCA, KCA, CAPA, CNPE, CNPA, LFCS, FinOps — all 12 learning paths now accessible from the sidebar.

---

## March 26, 2026 — Starlight Migration + On-Premises Track

### Starlight Migration (from MkDocs)
- Migrated 648 English + 115 Ukrainian files to Astro/Starlight
- Fixed 5,323 broken links, dot-stripping in slugs, sidebar labels
- Build: ~1,400 pages in ~30s (down from 2+ minutes on MkDocs)
- Deployed via GitHub Pages with Node.js 22

### On-Premises Kubernetes — 30 NEW modules
Complete bare-metal K8s track:
- Planning & Economics (4) — server sizing, NUMA, cluster topology, TCO
- Bare Metal Provisioning (4) — PXE, Talos/Flatcar, Sidero/Metal3
- Networking (4) — spine-leaf, BGP, MetalLB/kube-vip, DNS/certs
- Storage (3) — Ceph/Rook, local storage
- Multi-Cluster (3) — private cloud, shared control planes, CAPI
- Security (4) — air-gapped, HSM/TPM, AD/LDAP/OIDC, compliance
- Operations (5) — upgrades, firmware, auto-remediation, observability
- Resilience (3) — multi-site DR, hybrid connectivity, cloud repatriation

### Infrastructure
- `scripts/dispatch.py` replaces ai_agent_bridge (1,800+ → 230 lines)
- Skills consolidated (12 → 4)
- GitHub Actions pinned to commit SHA, Dependabot enabled

---

## March 2026 — Ecosystem Update + 21 Certifications

The original March update — 60+ new modules, quality review, expanded certification coverage.

### Highlights
- **Zero to Terminal** — 10 modules for absolute beginners
- **Ukrainian Translation** — 115 pages translated
- **KCNA Update** — AI/ML, WebAssembly, Green Computing modules
- **21 Certification Tracks** — every CNCF certification covered
- **Kubernetes 1.35** — all content aligned
- **Platform Engineering Toolkit** — 15 new modules (FinOps, Kyverno, Chaos Engineering, Operators, CAPI, vCluster, Rook/Ceph, GPU Scheduling, etc.)

---

## December 2025 — Initial Release

KubeDojo launched with 311 modules covering CKA, CKAD, CKS, KCNA, KCSA, Platform Engineering, Linux, and IaC.

---

### By the Numbers (Current)

| Metric | Count |
|--------|-------|
| Total modules | 700+ |
| Tracks | 7 (Fundamentals, Linux, Cloud, Certifications, Platform, On-Premises, AI/ML) |
| Certification paths | 18+ |
| Ukrainian translations | 300+ pages |
| Build time | ~30s for ~1,700 pages |

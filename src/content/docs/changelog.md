---
title: "What's New"
template: splash
sidebar:
  order: 2
  label: "What's New"
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

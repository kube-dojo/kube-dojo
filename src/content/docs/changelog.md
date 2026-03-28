---
title: "What's New"
sidebar:
  order: 2
  label: "What's New"
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
- **Progress tracking** — Mark Complete button, sidebar checkmarks, [progress dashboard](/progress/) with export/import
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
| Total modules | 568 |
| Tracks | 6 (Fundamentals, Linux, Cloud, Certifications, Platform, On-Premises) |
| Certifications covered | 21 |
| Ukrainian translations | 115 pages |
| Build time | ~25s for 1,437 pages |

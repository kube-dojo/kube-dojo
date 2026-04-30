---
title: "What's New"
template: splash
sidebar:
  order: 2
  label: "What's New"
---

## May 1, 2026 — Machine Learning Track Restructured (Phase 0)

The AI/ML Engineering track's `classical-ml/` section has been restructured and renamed to [Machine Learning](/ai-ml-engineering/machine-learning/), and a new peer section [Reinforcement Learning](/ai-ml-engineering/reinforcement-learning/) has been scaffolded. Old URLs redirect to their new homes; nothing existing 404s.

This is Phase 0 of the ML curriculum expansion tracked in [issue #677](https://github.com/kube-dojo/kube-dojo.github.io/issues/677). Phase 1 onward will fill the new section with Tier-1 modules on regression, evaluation, feature engineering, trees, k-NN/SVM, clustering, anomaly detection, dimensionality reduction, and hyperparameter optimization, plus a Tier-1 reinforcement-learning practitioner foundation.

Phase 0 ships:

- The Tier-1 spine (twelve slots in `machine-learning/`, two slots in `reinforcement-learning/`) with the existing XGBoost and Time Series Forecasting modules renumbered to 1.6 and 1.12 to make room.
- A from-scratch rewrite of [Module 1.1 — Scikit-learn API & Pipelines](/ai-ml-engineering/machine-learning/module-1.1-scikit-learn-api-and-pipelines/), refocused away from the broad algorithm survey and onto the workflow contract that makes every later module honest: estimator API, leakage-safe `Pipeline` and `ColumnTransformer`, cross-validation splitter discipline, custom transformers via `BaseEstimator`, and the hyperparameter-search interface.
- Two new quality gates under `scripts/quality/`: a citation HTTP verifier (every URL in a module's Sources section must resolve to a 200 on the same host) and a python-block syntax checker. Every Phase 1+ module passes both before merge.

## April 29, 2026 — AI History Book: Part 1 Released

The first nine chapters of the [AI History book](/ai-history/) are ready to read. Part 1 covers AI's mathematical foundations, 1840s–1950s: Boole, Turing, Shannon, Markov, McCulloch–Pitts, the cybernetics movement, Walter's electronic tortoises, von Neumann's stored program, and magnetic-core memory.

Every chapter opens with a one-paragraph summary, a cast of characters, a timeline, and a glossary; closes with a "Why this still matters today" note; and exposes its named scenes in the right-side navigation. Math-heavy chapters get a foldout sidebar with the equations laid out.

[Start with Chapter 1 →](/ai-history/ch-01-the-laws-of-thought/)

---

## April 26, 2026 — Quality Rewrite + Route Design

### Module quality rewrite underway
Roughly 130 modules have been rewritten to a stricter pedagogical bar, with more in progress. Each module is reviewed against the published quality rubric before going live.

### Hub pages rewritten as route guides
- **Platform Engineering** opens with three persona routes: SRE, DevEx Builder, Platform Architect.
- **Kubernetes Certifications** opens with three personas: Operator, Developer, Security Specialist — replacing the alphabetical default that pointed most learners at the wrong starting point.
- **Bridge pages** added for moving between tracks: K8s ↔ On-Premises, K8s ↔ Platform Engineering, AI/ML ↔ AI Platform Engineering.
- **Section health** is now visible on each section's index — see which sections are actively improving and which are stable.

### AI History Book scoped
The AI History book is scoped at 72 chapters covering the math, hardware, funding, and people behind each era of AI. First drafts are landing chapter by chapter.

---

## April 17, 2026 — New AI Track

A new top-level **AI** track for AI literacy and practical working habits — a beginner-friendly entry point separate from the existing **AI/ML Engineering** advanced builder path.

Initial sections: AI Foundations, AI-Native Work. Modules cover what AI is, what LLMs are, prompting, verification, privacy, and using AI for learning, writing, research, and coding.

---

## April 16, 2026 — ZTT, AI/ML Path, Certification Prep

### Zero to Terminal hardened
Theory and early labs tightened. Ukrainian translation kept in sync.

### AI/ML local-first path
Ten new modules so a learner with one home GPU can build a working RAG system or fine-tune a model without renting a cluster:

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

### Certification prep gaps closed
New exam-prep modules for LFCS, CNPE, CNPA, and CGOA.

### Hub pages refreshed
Homepage, Kubernetes certifications, Cloud, Platform Engineering, On-Premises, and AI/ML Engineering hubs rewritten for clearer cross-track navigation.

---

## March 28, 2026 — Theme Overhaul + New Modules

### New design
Custom homepage, K-themed topbar, smart sidebar that follows your current track, breadcrumbs on every module, complexity/time chips, dark/light mode. Mark-Complete button with an exportable progress dashboard.

### Linux Deep Dive promoted to its own track
37 modules, moved out from under Fundamentals into a top-level Linux track.

### Networking discipline — 5 new modules
CNI Architecture & Selection, Network Policy Design, Service Mesh Strategy, Ingress & Gateway API, Multi-Cluster Networking.

### Platform Leadership discipline — 5 new modules
Building Platform Teams, Developer Experience Strategy, Platform as Product, Adoption & Migration, Scaling Platform Organizations.

### Supply Chain Defense Guide — 4 new sections
Transitive dependency auditing, registry quarantine, AI/LLM gateway security, credential rotation verification.

### All 12 certification learning paths in the sidebar
PCA, ICA, CCA, CGOA, CBA, OTCA, KCA, CAPA, CNPE, CNPA, LFCS, FinOps.

---

## March 26, 2026 — Site Migration + On-Premises Kubernetes

### Faster, cleaner site
Site migrated to Starlight (Astro). Build is now seconds for the whole site instead of minutes; broken links cleaned up across the move.

### On-Premises Kubernetes — 30 new modules
Complete bare-metal K8s track:

- **Planning & Economics** (4) — server sizing, NUMA, cluster topology, TCO
- **Bare Metal Provisioning** (4) — PXE, Talos/Flatcar, Sidero/Metal3
- **Networking** (4) — spine-leaf, BGP, MetalLB/kube-vip, DNS/certs
- **Storage** (3) — Ceph/Rook, local storage
- **Multi-Cluster** (3) — private cloud, shared control planes, CAPI
- **Security** (4) — air-gapped, HSM/TPM, AD/LDAP/OIDC, compliance
- **Operations** (5) — upgrades, firmware, auto-remediation, observability
- **Resilience** (3) — multi-site DR, hybrid connectivity, cloud repatriation

---

## March 2026 — Ecosystem Update

- **Zero to Terminal** — 10 modules for absolute beginners
- **Ukrainian translation** — 115 pages (Prerequisites, CKA, CKAD)
- **KCNA update** — AI/ML, WebAssembly, Green Computing modules
- **21 certification tracks** — every CNCF certification covered
- **Kubernetes 1.35** — all content aligned
- **Platform Engineering Toolkit** — 15 new modules (FinOps, Kyverno, Chaos Engineering, Operators, CAPI, vCluster, Rook/Ceph, GPU Scheduling)

---

## December 2025 — Initial Release

KubeDojo launched with 311 modules covering CKA, CKAD, CKS, KCNA, KCSA, Platform Engineering, Linux, and IaC.

---

### By the Numbers

| Metric | Count |
|--------|-------|
| Total modules | 700+ |
| Tracks | 7 (Fundamentals, Linux, Cloud, Certifications, Platform, On-Premises, AI/ML) |
| Certification paths | 18+ |
| Ukrainian translations | 300+ pages |

---
title: "Kubernetes Certifications"
sidebar:
  order: 1
  label: "Certifications"
---
**The Kubestronaut Path** — All 5 certifications required for [Kubestronaut](https://www.cncf.io/training/kubestronaut/) status, CNCF's recognition for passing KCNA, KCSA, CKAD, CKA, and CKS.

---

## Overview

```
                        KUBESTRONAUT PATH
    ════════════════════════════════════════════════════════

    ENTRY LEVEL (multiple choice, 90 min)
    ┌──────────────────────────────────────────────────────┐
    │  KCNA   Kubernetes & Cloud Native Associate          │
    │         └── Conceptual understanding of K8s & CNCF   │
    │                                                      │
    │  KCSA   Kubernetes & Cloud Native Security Associate │
    │         └── Security concepts and threat modeling    │
    └──────────────────────────────────────────────────────┘
                             │
                             ▼
    PRACTITIONER LEVEL (hands-on lab, 2 hours)
    ┌──────────────────────────────────────────────────────┐
    │  CKAD   Certified Kubernetes Application Developer   │
    │         └── Build and deploy applications            │
    │                                                      │
    │  CKA    Certified Kubernetes Administrator           │
    │         └── Install, configure, manage clusters      │
    │                                                      │
    │  CKS    Certified Kubernetes Security Specialist     │
    │         └── Secure clusters end-to-end (requires CKA)│
    └──────────────────────────────────────────────────────┘

    ════════════════════════════════════════════════════════
```

---

## Certifications

| Cert | Name | Type | Modules | Curriculum |
|------|------|------|---------|------------|
| [KCNA](kcna/) | Kubernetes & Cloud Native Associate | Multiple choice | 28 | [Details](kcna/) |
| [KCSA](kcsa/) | Kubernetes & Cloud Native Security Associate | Multiple choice | 26 | [Details](kcsa/) |
| [CKAD](ckad/) | Certified Kubernetes Application Developer | Hands-on lab | 30 | [Details](ckad/) |
| [CKA](cka/) | Certified Kubernetes Administrator | Hands-on lab | 47 | [Details](cka/) |
| [CKS](cks/) | Certified Kubernetes Security Specialist | Hands-on lab | 30 | [Details](cks/) |
| | **Total** | | **161** | |

---

## Suggested Order

One hard rule applies regardless of the path below: **CKS requires prior CKA completion.** It is not just "security-flavored Kubernetes." It assumes you already know how to administer clusters under time pressure.

**Option 1: Breadth First** (understand the landscape)
```
KCNA → KCSA → CKAD → CKA → CKS
```

**Option 2: Depth First** (production admin focus)
```
CKA → CKAD → CKS → KCNA → KCSA
```

**Option 3: Developer Path**
```
KCNA → CKAD → (stop here or continue to CKA)
```

**Option 4: Security Path**
```
CKA → CKS → KCSA
```

## Which Certification Should You Start With?

Use this quick rule instead of staring at the full table:

| If your goal is... | Start here | Why |
|---|---|---|
| understand Kubernetes and the CNCF landscape | [KCNA](kcna/) | lowest-pressure conceptual entry point |
| become employable as a cluster administrator | [CKA](cka/) | the strongest admin-first hands-on route |
| ship applications on Kubernetes | [CKAD](ckad/) | best developer-first route |
| go deeper into cluster security | [CKA](cka/) then [CKS](cks/) | `CKS` assumes admin fluency and requires `CKA` |
| understand security concepts before hardening clusters | [KCSA](kcsa/) | good conceptual security companion, not a replacement for `CKS` |
| move toward platform engineering | [KCNA](kcna/) or [CKA](cka/) first, then [CNPA](cnpa/) and later [CNPE](cnpe/) | platform certs are specialization tracks after core Kubernetes literacy, not substitutes for it |

If you are unsure, the safest defaults are:
- `KCNA` for conceptual learners
- `CKA` for operations-minded learners
- `CKAD` for application developers

## Start Here If

- you want external certification goals and exam-shaped structure
- you already finished [Prerequisites](../prerequisites/) or equivalent hands-on fundamentals
- you want the shortest route into employable Kubernetes administration or application delivery skills

## Do Not Start Here First If

- you are still uncomfortable with the terminal, SSH, files, and packages
- you have never deployed basic workloads to a cluster
- you are looking for theory-first platform engineering rather than certification prep

If that is your situation, start with [Prerequisites](../prerequisites/) first.

## Safest Route Into This Track

```text
Prerequisites
   |
KCNA or CKA
   |
CKAD / CKS / specialist certs
```

Use `KCNA` if you want a conceptual entry point. Use `CKA` if you already want hands-on cluster administration pressure from day one.

If your long-term goal is `CNPA` or `CNPE`, treat them as **post-foundation** credentials. `CNPA` can follow `KCNA` for conceptual platform learners, but `CNPE` makes the most sense after you already have at least one real hands-on Kubernetes route such as `CKA` or `CKAD`.

## Common Certification Routes

- `Beginner -> operator`: `Prerequisites -> KCNA -> CKA -> CKS`
- `Beginner -> developer`: `Prerequisites -> KCNA -> CKAD`
- `Linux / ops -> admin`: `Linux -> CKA -> CKS`
- `Kubernetes -> platform`: `KCNA or CKA -> CNPA -> CNPE`
- `GitOps / platform specialist`: `KCNA or CKA -> CGOA / CNPA / CNPE`

Specialist certifications are not a better first move than learning the core Kubernetes path. They make the most sense after you already understand how clusters, workloads, and operations fit together.

## Tool & Specialist Certifications

Beyond Kubestronaut, CNCF offers tool-specific certifications. KubeDojo maps existing modules as learning paths for each:

| Cert | Name | Learning Path |
|------|------|---------------|
| [PCA](pca/) | Prometheus Certified Associate | Prometheus, PromQL, alerting |
| [ICA](ica/) | Istio Certified Associate | Service mesh, traffic management |
| [CCA](cca/) | Cilium Certified Associate | eBPF networking, policies |
| [CGOA](cgoa/) | Certified GitOps Associate | ArgoCD, Flux, GitOps principles |
| [CBA](cba/) | Certified Backstage Associate | IDPs, developer portals |
| [OTCA](otca/) | OpenTelemetry Certified Associate | Observability, tracing |
| [KCA](kca/) | Kyverno Certified Associate | Policy as code |
| [CAPA](capa/) | Certified Argo Project Associate | Argo Workflows, Rollouts |
| [CNPE](cnpe/) | Cloud Native Platform Engineer | Cross-track learning path |
| [CNPA](cnpa/) | Cloud Native Platform Associate | Platform fundamentals |
| [FinOps](finops/) | FinOps Practitioner | Cloud cost optimization |

These are best treated as specialization tracks, not replacements for a first Kubernetes foundation. For most learners:
- `KCNA`, `CKA`, or `CKAD` should come first
- specialist certs and platform certs make more sense once you know whether your work is admin, developer, security, GitOps, or platform focused

## Extending Kubernetes

| Section | Modules | Description |
|---------|---------|-------------|
| [Extending K8s](extending/) | 8 | Controllers, operators, webhooks, API aggregation, CRDs |

---

## Exam Tips

All exams share these characteristics:
- **PSI Bridge proctoring** — Strict environment, webcam required
- **kubernetes.io allowed** — Official docs are your friend
- **Time pressure** — Speed matters as much as knowledge

Typical pacing:
- `KCNA` / `KCSA`: 4-8 weeks if you are already in the curriculum about `5-8 h/week`
- `CKAD` / `CKA`: 2-4 months at about `8-10 h/week`
- `CKS` after `CKA`: usually another `4-8 weeks`
- full Kubestronaut path: commonly `3-6 months` for already-technical learners at roughly `10 h/week`

For hands-on exams (CKAD, CKA, CKS):
- Practice with `kubectl` until it's muscle memory
- Master vim/nano for YAML editing
- Use `kubectl explain` and `--dry-run=client -o yaml`
- [killer.sh](https://killer.sh) included with exam purchase — use it

## After This Track

- go to [Cloud](../cloud/) if you want provider-specific production Kubernetes
- go to [Platform Engineering](../platform/) if you want systems thinking, SRE, GitOps, and platform design beyond the exams
- go to [On-Premises](../on-premises/) if your goal is private infrastructure and you already have Linux depth

## Choose Your Next Track After Core Kubernetes

| If Kubernetes leads you toward... | Next track | Why |
|---|---|---|
| managed production clusters on AWS, GCP, or Azure | [Cloud](../cloud/) | provider-specific networking, identity, and managed-control-plane patterns live there |
| SRE, GitOps, delivery automation, and internal platforms | [Platform Engineering](../platform/) | that is the systems-and-organization layer above the exams |
| private clusters, bare metal, and datacenter operations | [On-Premises](../on-premises/) | those assumptions diverge sharply from managed-cloud Kubernetes |
| ML workloads, serving, and AI infrastructure | [AI/ML Engineering](../ai-ml-engineering/) | the Kubernetes track is a prerequisite there, not the full workflow |

## Common Failure Modes After This Track

- assuming certification completion automatically means platform-engineering readiness
- jumping into on-prem operations without enough Linux depth
- treating specialist certifications as a substitute for choosing a real next operating context

---

## Curriculum Sources

We track official CNCF curricula:
- [CNCF Curriculum Repository](https://github.com/cncf/curriculum)
- [CKA Program Changes](https://training.linuxfoundation.org/certified-kubernetes-administrator-cka-program-changes/)
- [CKS Program Changes](https://training.linuxfoundation.org/cks-program-changes/)

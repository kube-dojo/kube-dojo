---
title: "Kubernetes Certifications"
sidebar:
  order: 1
  label: "Certifications"
---
**The Kubestronaut Path** — All 5 certifications required for [Kubestronaut](https://www.cncf.io/training/kubestronaut/) status.

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

For hands-on exams (CKAD, CKA, CKS):
- Practice with `kubectl` until it's muscle memory
- Master vim/nano for YAML editing
- Use `kubectl explain` and `--dry-run=client -o yaml`
- [killer.sh](https://killer.sh) included with exam purchase — use it

---

## Curriculum Sources

We track official CNCF curricula:
- [CNCF Curriculum Repository](https://github.com/cncf/curriculum)
- [CKA Program Changes](https://training.linuxfoundation.org/certified-kubernetes-administrator-cka-program-changes/)
- [CKS Program Changes](https://training.linuxfoundation.org/cks-program-changes/)

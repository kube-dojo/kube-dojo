---
title: "CGOA - Certified GitOps Associate"
sidebar:
  order: 1
  label: "CGOA"
---
> **Multiple-choice exam** | 90 minutes | Passing score: 75% | $250 USD

## Overview

The CGOA (Certified GitOps Associate) validates your understanding of GitOps principles, patterns, and related practices. It's a **theory exam** — multiple-choice questions, no terminal access. Think of it as "KCNA for GitOps."

**KubeDojo covers ~90%+ of CGOA topics** through our existing Platform Engineering track. This page maps CGOA domains to existing modules so you can prepare efficiently.

> **Good news**: If you've already worked through our GitOps discipline and toolkits, you've covered the hardest parts. This exam tests understanding of concepts, not hands-on skills — but our hands-on modules give you the deep understanding that makes theory questions easy.

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| GitOps Terminology | 20% | Excellent (GitOps discipline modules) |
| GitOps Principles | 30% | Excellent (GitOps discipline + IaC modules) |
| Related Practices | 16% | Excellent (IaC, DevOps, CI/CD, DevSecOps modules) |
| GitOps Patterns | 20% | Excellent (promotion, drift, progressive delivery modules) |
| Tooling | 14% | Excellent (ArgoCD, Flux, Helm, Kustomize toolkit modules) |

---

## Domain 1: GitOps Terminology (20%)

### Competencies
- Continuous delivery and deployment concepts
- Declarative vs imperative approaches
- Desired state and state stores
- Drift detection and correction
- Reconciliation loops

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | What is GitOps? OpenGitOps 4 principles, key terminology | Direct |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Drift detection and reconciliation loops | Direct |
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Declarative vs imperative, desired state concepts | Direct |
| [IaC 6.5](../../platform/disciplines/delivery-automation/iac/module-6.5-drift-remediation/) | Drift remediation strategies | Direct |
| [Modern DevOps: GitOps](../../prerequisites/modern-devops/module-1.2-gitops/) | GitOps overview for beginners | Supporting |

---

## Domain 2: GitOps Principles (30%)

### Competencies
- **Declarative**: Desired state is expressed declaratively
- **Versioned and Immutable**: Desired state is stored in a versioned, immutable source of truth
- **Pulled Automatically**: Agents pull desired state automatically
- **Continuously Reconciled**: Agents continuously observe and reconcile actual state

> This is the highest-weighted domain. Know the [OpenGitOps v1.0 principles](https://opengitops.dev/) cold.

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [GitOps 3.1](../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/) | OpenGitOps 4 principles in depth | Direct |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Git as the versioned, immutable source of truth; repo strategies | Direct |
| [GitOps 3.4](../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/) | Continuous reconciliation and drift detection | Direct |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | Pull-based delivery across clusters | Direct |
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | Declarative configuration, state management | Direct |
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | Pull-based reconciliation in practice (Application CRD, sync policies) | Direct |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | Pull-based reconciliation with 5 controllers | Direct |

---

## Domain 3: Related Practices (16%)

### Competencies
- Configuration as Code (CaC)
- Infrastructure as Code (IaC)
- DevOps culture and practices
- CI/CD pipelines and their relationship to GitOps

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [IaC 6.1](../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) | IaC fundamentals, declarative infrastructure | Direct |
| [IaC 6.4](../../platform/disciplines/delivery-automation/iac/module-6.4-iac-at-scale/) | IaC at scale, configuration management | Direct |
| [IaC 6.2](../../platform/disciplines/delivery-automation/iac/module-6.2-iac-testing/) | Testing infrastructure code | Supporting |
| [IaC 6.3](../../platform/disciplines/delivery-automation/iac/module-6.3-iac-security/) | Security in IaC | Supporting |
| [Modern DevOps: IaC](../../prerequisites/modern-devops/module-1.1-infrastructure-as-code/) | IaC overview for beginners | Supporting |
| [Modern DevOps: CI/CD](../../prerequisites/modern-devops/module-1.3-cicd-pipelines/) | CI/CD pipeline fundamentals | Direct |
| [Modern DevOps: DevSecOps](../../prerequisites/modern-devops/module-1.6-devsecops/) | DevOps/DevSecOps culture | Supporting |
| [DevSecOps 4.3](../../platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd/) | CI/CD pipeline design and security integration | Supporting |
| [Cloud Native Ecosystem](../../prerequisites/cloud-native-101/module-1.4-cloud-native-ecosystem/) | CNCF landscape, cloud native practices | Supporting |
| [Dagger](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.1-dagger/) | Modern CI/CD pipeline design | Supporting |
| [Tekton](../../platform/toolkits/cicd-delivery/ci-cd-pipelines/module-3.2-tekton/) | K8s-native CI/CD | Supporting |

---

## Domain 4: GitOps Patterns (20%)

### Competencies
- Deployment and release patterns (blue-green, canary, rolling)
- Progressive delivery strategies
- Pull-based vs event-driven reconciliation
- Environment promotion strategies
- Repository patterns (monorepo, polyrepo)

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Monorepo vs polyrepo, app-of-apps pattern | Direct |
| [GitOps 3.3](../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/) | Environment promotion patterns (dev/staging/prod) | Direct |
| [GitOps 3.5](../../platform/disciplines/delivery-automation/gitops/module-3.5-secrets/) | Secrets management patterns in GitOps workflows | Direct |
| [GitOps 3.6](../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/) | Multi-cluster deployment patterns | Direct |
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Progressive delivery: canary, blue-green, analysis runs | Direct |
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | ApplicationSet, sync waves, hooks, pull-based model | Direct |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | Event-driven reconciliation, notification controller | Direct |
| [Helm & Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Manifest customization patterns for promotion | Direct |

---

## Domain 5: Tooling (14%)

### Competencies
- Manifest formats (YAML, JSON, Helm charts, Kustomize overlays)
- State store management (Git repositories)
- Reconciliation engines (ArgoCD, Flux)

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [ArgoCD](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) | Application CRD, sync policies, RBAC, ApplicationSet | Direct |
| [Flux](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/) | GitRepository, HelmRelease, Kustomization, 5 controllers | Direct |
| [Helm & Kustomize](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/) | Helm charts, Kustomize overlays, manifest packaging | Direct |
| [GitOps 3.2](../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/) | Git as state store, repo layout patterns | Direct |
| [Argo Rollouts](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/) | Progressive delivery tooling | Direct |

---

## Study Strategy

```
CGOA PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1: GitOps Foundations (covers Domains 1 + 2 = 50% of exam!)
├── GitOps 3.1 — What is GitOps, OpenGitOps principles
├── IaC 6.1 — Declarative vs imperative, desired state
├── GitOps 3.4 — Drift detection & reconciliation
└── IaC 6.5 — Drift remediation strategies

Week 2: GitOps Patterns (Domain 4 = 20%)
├── GitOps 3.2 — Repository strategies (monorepo vs polyrepo)
├── GitOps 3.3 — Environment promotion patterns
├── GitOps 3.5 — Secrets management in GitOps
└── GitOps 3.6 — Multi-cluster GitOps

Week 3: Tooling Deep Dive (Domain 5 = 14%)
├── ArgoCD toolkit module (pull-based reconciliation)
├── Flux toolkit module (event-driven reconciliation)
├── Helm & Kustomize (manifest formats)
└── Argo Rollouts (progressive delivery)

Week 4: Related Practices + Review (Domain 3 = 16%)
├── Modern DevOps: CI/CD pipelines
├── IaC 6.2-6.4 (testing, security, scale)
├── DevSecOps 4.3 (security in CI/CD)
└── Review all domains, focus on terminology
```

> **Pro tip**: Domains 1 and 2 together are worth **50% of the exam** and are both covered by the same set of modules. Nail the OpenGitOps principles and terminology first — it's the highest ROI study time.

---

## Exam Tips

- **This is a theory exam** — no terminal, no kubectl. You need to *understand* concepts, not execute them. But our hands-on modules build deeper understanding than reading alone.
- **Know the 4 OpenGitOps principles by heart** — Declarative, Versioned & Immutable, Pulled Automatically, Continuously Reconciled. Expect multiple questions testing nuances of each.
- **Pull vs push is a key distinction** — understand why pull-based (agent in cluster polling Git) is the GitOps way, and how event-driven (webhook triggers) differs.
- **ArgoCD vs Flux** — know the architectural differences (single controller vs 5 specialized controllers), not just that both "do GitOps."
- **Progressive delivery is not the same as CI/CD** — canary/blue-green/rolling are *release* strategies, separate from the *build/test* pipeline.
- **Declarative != YAML** — declarative is about expressing *what* not *how*. The exam may test this distinction.
- **90 minutes is generous** — for ~60 multiple-choice questions, you have ~1.5 min per question. Flag and skip anything you're unsure about.
- **75% pass rate** — you can miss roughly 1 in 4 questions. Don't panic over a few unknowns.

---

## Gap Analysis

KubeDojo's existing Platform Engineering track covers the vast majority of CGOA topics. Here's what's left:

| Topic | Status | Notes |
|-------|--------|-------|
| OpenGitOps specification details | Fully covered | GitOps 3.1 covers all 4 principles from the official spec |
| Configuration as Code (CaC) vs IaC distinction | Minor gap | IaC modules cover IaC deeply; CaC as a distinct concept (e.g., application config vs infrastructure) is not explicitly called out but is implicitly covered |
| GitOps history and origin | Minor gap | GitOps 3.1 likely covers Weaveworks/Alexis Richardson origin, but exam may ask specific historical details |
| Comparison of push vs pull CD models | Covered | GitOps 3.1 + ArgoCD/Flux modules contrast the models |
| YAML/JSON/Jsonnet manifest formats | Covered | Helm & Kustomize module covers YAML and Helm; Jsonnet is briefly covered in the Helm/Kustomize module |

**No new modules are needed.** The 6 GitOps discipline modules, 4 GitOps toolkit modules, 6 IaC modules, and supporting prerequisites/CI-CD modules provide comprehensive CGOA preparation.

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Associate Level:
├── KCNA (Cloud Native Associate) — K8s fundamentals
├── KCSA (Security Associate) — Security fundamentals
└── CGOA (GitOps Associate) ← YOU ARE HERE

Professional Level:
├── CKA (K8s Administrator) — Cluster operations
├── CKAD (K8s Developer) — Application deployment
├── CKS (K8s Security Specialist) — Security hardening
└── CNPE (Platform Engineer) — Full platform skills

Specialist (Coming):
└── CKNE (K8s Network Engineer) — Advanced networking
```

The CGOA pairs naturally with the KCNA — together they cover Kubernetes fundamentals and GitOps delivery. If you're pursuing the full Kubestronaut path, CGOA knowledge directly supports the CKA (deployments, rollouts) and CNPE (GitOps is 25% of that exam).

---
name: k8s-cert-expert
description: Kubernetes certification expertise (CKA, CKAD, CKS, KCNA, KCSA). Use for exam content, curriculum accuracy, study strategy. Triggers on "CKA", "CKAD", "CKS", "KCNA", "KCSA", "exam", "certification".
---

# Kubernetes Certification Expert

Consolidated knowledge for all five CNCF Kubernetes certifications. Use when writing, reviewing, or verifying exam-aligned content.

## Exam Overview

| Cert | Format | Duration | Questions | Pass | Focus |
|------|--------|----------|-----------|------|-------|
| CKA | Hands-on | 2h | 16 tasks | 66% | Cluster admin, troubleshooting |
| CKAD | Hands-on | 2h | 15 tasks | 66% | App dev, deployment, observability |
| CKS | Hands-on | 2h | 15 tasks | 67% | Security hardening, runtime |
| KCNA | Multiple choice | 90m | ~60 | 75% | Cloud native fundamentals |
| KCSA | Multiple choice | 90m | ~60 | 75% | Security fundamentals |

## Domain Weights

### CKA 2025
| Domain | Weight |
|--------|--------|
| Troubleshooting | 30% |
| Cluster Architecture, Installation & Configuration | 25% |
| Services & Networking | 20% |
| Workloads & Scheduling | 15% |
| Storage | 10% |

**2025 Changes**: Added Helm, Kustomize, Gateway API, CRDs/Operators, Pod Security Admission. Deprioritized etcd backup, cluster upgrades.

### CKAD 2025
| Domain | Weight |
|--------|--------|
| Application Design and Build | 20% |
| Application Deployment | 20% |
| Application Observability and Maintenance | 15% |
| Application Environment, Configuration and Security | 25% |
| Services & Networking | 20% |

### CKS 2025
| Domain | Weight |
|--------|--------|
| Cluster Setup | 10% |
| Cluster Hardening | 15% |
| System Hardening | 15% |
| Minimize Microservice Vulnerabilities | 20% |
| Supply Chain Security | 20% |
| Monitoring, Logging and Runtime Security | 20% |

**Key tools**: Falco, Trivy, AppArmor, seccomp, OPA/Gatekeeper, Kyverno, NetworkPolicies, Cilium.

### KCNA
| Domain | Weight |
|--------|--------|
| Kubernetes Fundamentals | 44% |
| Container Orchestration | 28% |
| Cloud Native Architecture | 12% |
| Application Delivery | 16% |

### KCSA
| Domain | Weight |
|--------|--------|
| Overview of Cloud Native Security | 14% |
| Kubernetes Cluster Component Security | 22% |
| Kubernetes Security Fundamentals | 22% |
| Kubernetes Threat Model | 16% |
| Platform Security | 16% |
| Compliance and Security Frameworks | 10% |

## Exam Strategy: Three-Pass Method

1. **Pass 1 — Quick Wins** (1-3 min): Create pods, deployments, services. Simple kubectl commands.
2. **Pass 2 — Medium Tasks** (4-6 min): RBAC, NetworkPolicies, PVC, Helm, security contexts.
3. **Pass 3 — Complex Tasks** (remaining time): Troubleshooting, multi-step, cluster-level.

## Critical Exam Tips (Hands-on)

- Always `kubectl config use-context` first
- Use imperative commands: `kubectl run`, `kubectl create`, `kubectl expose`
- Generate YAML: `--dry-run=client -o yaml`
- Use `kubectl explain` instead of searching docs
- Partial credit exists — attempt everything
- Good enough > perfect

## KubeDojo Module Counts

| Cert | Modules | Path |
|------|---------|------|
| CKA | 47 | docs/k8s/cka/ |
| CKAD | 30 | docs/k8s/ckad/ |
| CKS | 30 | docs/k8s/cks/ |
| KCNA | 28 | docs/k8s/kcna/ |
| KCSA | 26 | docs/k8s/kcsa/ |
| Extending K8s | 8 | docs/k8s/extending/ |

## Official Resources

- [CNCF Curriculum](https://github.com/cncf/curriculum)
- [kubernetes.io/docs](https://kubernetes.io/docs/)
- [helm.sh/docs](https://helm.sh/docs/)
- killer.sh for realistic exam simulation

---
title: "Platform Engineering Track"
sidebar:
  order: 1
  label: "Platform Engineering"
---
> **Beyond Certifications** - Deep practitioner knowledge for SRE, Platform Engineering, DevSecOps, and MLOps.

---

## Why This Track Exists

Kubernetes certifications teach you *how* to use Kubernetes. This track teaches you *how to run production systems* on Kubernetes - the disciplines, principles, and tools that separate operators from practitioners.

This is for people who:
- Have Kubernetes fundamentals (or certifications)
- Want to understand theory, not just tools
- Need to make technology decisions at work
- Want to implement best practices, not just pass exams

---

## Structure

```
platform/
├── foundations/        # Theory that doesn't change
│   ├── systems-thinking/
│   ├── reliability-engineering/
│   ├── observability-theory/
│   ├── security-principles/
│   └── distributed-systems/
│
├── disciplines/        # Applied practices
│   ├── sre/
│   ├── platform-engineering/
│   ├── gitops/
│   ├── iac/
│   ├── devsecops/
│   ├── mlops/
│   └── aiops/
│
└── toolkits/           # Current tools (will evolve)
    ├── observability/      # Prometheus, OTel, Grafana
    ├── gitops-deployments/ # ArgoCD, Flux, Helm
    ├── ci-cd-pipelines/    # Dagger, Tekton, Argo Workflows
    ├── iac-tools/          # Terraform, OpenTofu, Pulumi
    ├── security-tools/     # Vault, OPA, Falco
    ├── networking/         # Cilium, Service Mesh
    ├── scaling-reliability/ # Karpenter, KEDA, Velero
    ├── platforms/          # Backstage, Crossplane
    ├── developer-experience/ # K9s, Telepresence
    ├── ml-platforms/       # Kubeflow, MLflow
    └── aiops-tools/        # Anomaly detection, AIOps
```

---

## Reading Order

### Start with Foundations

Theory that applies everywhere. Read these first - they don't change.

| Track | Why Start Here |
|-------|---------------|
| [Systems Thinking](foundations/systems-thinking/) | Mental models for complex systems |
| [Reliability Engineering](foundations/reliability-engineering/) | Failure theory, redundancy, risk |
| [Distributed Systems](foundations/distributed-systems/) | CAP, consensus, consistency |
| [Observability Theory](foundations/observability-theory/) | What to measure and why |
| [Security Principles](foundations/security-principles/) | Zero trust, threat modeling |

### Then Pick a Discipline

Applied practices - how to do the work.

| Discipline | Best For |
|------------|----------|
| [SRE](disciplines/core-platform/sre/) | Operations, reliability, on-call |
| [Platform Engineering](disciplines/core-platform/platform-engineering/) | Developer experience, self-service |
| [GitOps](disciplines/delivery-automation/gitops/) | Deployment, reconciliation |
| [Infrastructure as Code](disciplines/delivery-automation/iac/) | IaC patterns, testing, drift management |
| [DevSecOps](disciplines/reliability-security/devsecops/) | Security integration, compliance |
| [MLOps](disciplines/data-ai/mlops/) | ML lifecycle, model serving |
| [AIOps](disciplines/data-ai/aiops/) | AI-driven operations, automation |

### Reference Toolkits as Needed

Tools change. Use these as reference when implementing.

| Toolkit | When to Use |
|---------|-------------|
| [Observability](toolkits/observability-intelligence/observability/) | Setting up monitoring/tracing |
| [GitOps & Deployments](toolkits/cicd-delivery/gitops-deployments/) | Implementing ArgoCD/Flux |
| [CI/CD Pipelines](toolkits/cicd-delivery/ci-cd-pipelines/) | Dagger, Tekton, Argo Workflows |
| [IaC Tools](toolkits/infrastructure-networking/iac-tools/) | Terraform, OpenTofu, Pulumi, Ansible |
| [Security Tools](toolkits/security-quality/security-tools/) | Policy, secrets, runtime security |
| [Networking](toolkits/infrastructure-networking/networking/) | Cilium, Service Mesh |
| [Scaling & Reliability](toolkits/developer-experience/scaling-reliability/) | Karpenter, KEDA, Velero |
| [Platforms](toolkits/infrastructure-networking/platforms/) | Building internal platforms |
| [Developer Experience](toolkits/developer-experience/devex-tools/) | K9s, Telepresence |
| [ML Platforms](toolkits/data-ai-platforms/ml-platforms/) | ML infrastructure |
| [AIOps Tools](toolkits/observability-intelligence/aiops-tools/) | Anomaly detection, AIOps |

---

## Module Format

Every module includes:

- **Why This Matters** - Real-world motivation
- **Theory** - Principles and mental models
- **Current Landscape** - Tools that implement this
- **Hands-On** - Practical implementation
- **Best Practices** - What good looks like
- **Common Mistakes** - Anti-patterns to avoid
- **Further Reading** - Books, talks, papers

---

## Status

✅ **This track is complete** - 102 modules across foundations, disciplines, and toolkits.

| Section | Modules | Status |
|---------|---------|--------|
| Foundations | 19 | ✅ Complete |
| Disciplines | 43 | ✅ Complete |
| Toolkits | 40 | ✅ Complete |

---

## Prerequisites

Before starting this track, you should have:
- Kubernetes basics (or completed [Prerequisites](../prerequisites/))
- Some production experience (helpful but not required)
- Curiosity about "why" not just "how"

---

*"Tools change. Principles don't."*

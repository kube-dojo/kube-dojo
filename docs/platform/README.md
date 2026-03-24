# Platform Engineering Track

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
| [Systems Thinking](foundations/systems-thinking/README.md) | Mental models for complex systems |
| [Reliability Engineering](foundations/reliability-engineering/README.md) | Failure theory, redundancy, risk |
| [Distributed Systems](foundations/distributed-systems/README.md) | CAP, consensus, consistency |
| [Observability Theory](foundations/observability-theory/README.md) | What to measure and why |
| [Security Principles](foundations/security-principles/README.md) | Zero trust, threat modeling |

### Then Pick a Discipline

Applied practices - how to do the work.

| Discipline | Best For |
|------------|----------|
| [SRE](disciplines/sre/README.md) | Operations, reliability, on-call |
| [Platform Engineering](disciplines/platform-engineering/README.md) | Developer experience, self-service |
| [GitOps](disciplines/gitops/README.md) | Deployment, reconciliation |
| [Infrastructure as Code](disciplines/iac/README.md) | IaC patterns, testing, drift management |
| [DevSecOps](disciplines/devsecops/README.md) | Security integration, compliance |
| [MLOps](disciplines/mlops/README.md) | ML lifecycle, model serving |
| [AIOps](disciplines/aiops/README.md) | AI-driven operations, automation |

### Reference Toolkits as Needed

Tools change. Use these as reference when implementing.

| Toolkit | When to Use |
|---------|-------------|
| [Observability](toolkits/observability/README.md) | Setting up monitoring/tracing |
| [GitOps & Deployments](toolkits/gitops-deployments/README.md) | Implementing ArgoCD/Flux |
| [CI/CD Pipelines](toolkits/ci-cd-pipelines/README.md) | Dagger, Tekton, Argo Workflows |
| [IaC Tools](toolkits/iac-tools/README.md) | Terraform, OpenTofu, Pulumi, Ansible |
| [Security Tools](toolkits/security-tools/README.md) | Policy, secrets, runtime security |
| [Networking](toolkits/networking/README.md) | Cilium, Service Mesh |
| [Scaling & Reliability](toolkits/scaling-reliability/README.md) | Karpenter, KEDA, Velero |
| [Platforms](toolkits/platforms/README.md) | Building internal platforms |
| [Developer Experience](toolkits/developer-experience/README.md) | K9s, Telepresence |
| [ML Platforms](toolkits/ml-platforms/README.md) | ML infrastructure |
| [AIOps Tools](toolkits/aiops-tools/README.md) | Anomaly detection, AIOps |

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
- Kubernetes basics (or completed [Prerequisites](../prerequisites/README.md))
- Some production experience (helpful but not required)
- Curiosity about "why" not just "how"

---

*"Tools change. Principles don't."*

---
title: "Cloud Native Tools"
sidebar:
  order: 1
---
**Tools change. This is your reference guide to the current cloud native ecosystem.**

These are implementation guides for specific tools — how to install, configure, operate, and troubleshoot them. For the principles and practices behind these tools, see **[Platform Engineering](../)**.

---

## Structure

```
toolkits/
├── cicd-delivery/                      # CI/CD & Delivery (14 modules)
│   ├── ci-cd-pipelines/               # Dagger, Tekton, Argo Workflows
│   ├── gitops-deployments/            # ArgoCD, Argo Rollouts, Flux, Helm
│   ├── source-control/               # GitLab, Gitea/Forgejo, GitHub Advanced
│   └── container-registries/          # Harbor, Zot, Dragonfly
│
├── observability-intelligence/         # Observability (16 modules)
│   ├── observability/                 # Prometheus, OTel, Grafana, Loki, Pixie, Hubble, Coroot
│   └── aiops-tools/                   # Anomaly detection, event correlation
│
├── infrastructure-networking/          # Infrastructure (42 modules)
│   ├── iac-tools/                     # Terraform, OpenTofu, Pulumi, Ansible, Wing, SST, System Initiative, Nitric
│   ├── k8s-distributions/            # k3s, k0s, MicroK8s, Talos, OpenShift, Managed K8s
│   ├── networking/                    # Cilium, Service Mesh
│   ├── platforms/                     # Backstage, Crossplane, cert-manager
│   └── storage/                       # Rook/Ceph, MinIO, Longhorn
│
├── security-quality/                   # Security & Quality (13 modules)
│   ├── security-tools/               # Vault, OPA/Gatekeeper, Falco, Tetragon, KubeArmor
│   └── code-quality/                  # SonarQube, Semgrep, CodeQL, Snyk, Trivy
│
├── developer-experience/               # Developer Experience (11 modules)
│   ├── devex-tools/                   # K9s, Telepresence, Local K8s, DevPod, Gitpod/Codespaces
│   └── scaling-reliability/           # Karpenter, KEDA, Velero
│
└── data-ai-platforms/                  # Data & AI Platforms (16 modules)
    ├── ml-platforms/                   # Kubeflow, MLflow, Feature Stores, vLLM, Ray Serve, LangChain
    └── cloud-native-databases/        # CockroachDB, CloudNativePG, Neon/PlanetScale, Vitess
```

---

## Toolkit Groups

### CI/CD & Delivery (14 modules)

| Toolkit | Modules | Key Tools |
|---------|---------|-----------|
| [CI/CD Pipelines](cicd-delivery/ci-cd-pipelines/) | 3 | Dagger, Tekton, Argo Workflows |
| [GitOps & Deployments](cicd-delivery/gitops-deployments/) | 5 | ArgoCD, Argo Rollouts, Flux, Helm |
| [Source Control](cicd-delivery/source-control/) | 3 | GitLab, Gitea/Forgejo, GitHub Advanced |
| [Container Registries](cicd-delivery/container-registries/) | 3 | Harbor, Zot, Dragonfly |

### Observability (16 modules)

| Toolkit | Modules | Key Tools |
|---------|---------|-----------|
| [Observability Stack](observability-intelligence/observability/) | 12 | Prometheus, OpenTelemetry, Grafana, Loki, Pixie, Hubble, Coroot |
| [AIOps Tools](observability-intelligence/aiops-tools/) | 4 | Anomaly detection, event correlation, root cause analysis |

### Infrastructure (42 modules)

| Toolkit | Modules | Key Tools |
|---------|---------|-----------|
| [IaC Tools](infrastructure-networking/iac-tools/) | 17 | Terraform, OpenTofu, Pulumi, Ansible, Wing, SST, System Initiative, Nitric |
| [K8s Distributions](infrastructure-networking/k8s-distributions/) | 8 | k3s, k0s, MicroK8s, Talos, OpenShift, Managed K8s |
| [Networking](infrastructure-networking/networking/) | 8 | Cilium, Service Mesh |
| [Platforms](infrastructure-networking/platforms/) | 6 | Backstage, Crossplane, cert-manager |
| [Storage](infrastructure-networking/storage/) | 3 | Rook/Ceph, MinIO, Longhorn |
| **Subtotal** | **42** | |

### Security & Quality (13 modules)

| Toolkit | Modules | Key Tools |
|---------|---------|-----------|
| [Security Tools](security-quality/security-tools/) | 8 | Vault, OPA/Gatekeeper, Falco, Tetragon, KubeArmor |
| [Code Quality](security-quality/code-quality/) | 5 | SonarQube, Semgrep, CodeQL, Snyk, Trivy |

### Developer Experience (11 modules)

| Toolkit | Modules | Key Tools |
|---------|---------|-----------|
| [DevEx Tools](developer-experience/devex-tools/) | 5 | K9s, Telepresence, Local K8s, DevPod, Gitpod/Codespaces |
| [Scaling & Reliability](developer-experience/scaling-reliability/) | 6 | Karpenter, KEDA, Velero |

### Data & AI Platforms (16 modules)

| Toolkit | Modules | Key Tools |
|---------|---------|-----------|
| [ML Platforms](data-ai-platforms/ml-platforms/) | 11 | Kubeflow, MLflow, Feature Stores, vLLM, Ray Serve, LangChain |
| [Cloud-Native Databases](data-ai-platforms/cloud-native-databases/) | 5 | CockroachDB, CloudNativePG, Neon/PlanetScale, Vitess |

---

## Summary

| Group | Toolkits | Modules |
|-------|----------|---------|
| CI/CD & Delivery | 4 | 14 |
| Observability | 2 | 16 |
| Infrastructure | 5 | 42 |
| Security & Quality | 2 | 13 |
| Developer Experience | 2 | 11 |
| Data & AI Platforms | 2 | 16 |
| **Total** | **17** | **112** |

---

## How to Use Toolkits

1. **Read Foundations first** — understand the theory behind the tool
2. **Read the Discipline** — understand the practices the tool implements
3. **Pick tools based on need** — not everything applies to your stack
4. **Hands-on practice** — every toolkit includes exercises
5. **Stay current** — tools evolve, check release notes

## Tool Selection Philosophy

We include tools that are:

- **CNCF Graduated/Incubating** — community validation
- **Production-proven** — battle-tested at scale
- **Actively maintained** — regular releases, active community
- **Interoperable** — works with the broader ecosystem

---

## Quick Start

Pick a toolkit based on your current focus:

- **Starting observability?** Begin with [Prometheus](observability-intelligence/observability/module-1.1-prometheus/)
- **Implementing GitOps?** Start with [ArgoCD](cicd-delivery/gitops-deployments/module-2.1-argocd/)
- **Managing infrastructure?** Check out [Terraform](infrastructure-networking/iac-tools/module-7.1-terraform/)
- **Building a platform?** Check out [Backstage](infrastructure-networking/platforms/module-7.1-backstage/)
- **Securing clusters?** Start with [Falco](security-quality/security-tools/module-4.3-falco/)
- **ML workloads?** Begin with [Kubeflow](data-ai-platforms/ml-platforms/module-9.1-kubeflow/)

---

## Prerequisites

Before diving into toolkits:

- Complete relevant [Foundations](../foundations/) modules
- Understand the [Discipline](../disciplines/) the tool supports
- Have a Kubernetes cluster (kind/minikube for learning)

---

*"Principles tell you why. Tools tell you how."*

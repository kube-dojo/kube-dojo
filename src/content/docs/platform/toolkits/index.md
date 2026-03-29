---
title: "Toolkits"
sidebar:
  order: 1
---
> **Current tools for platform engineering** - Practical guides to the most important cloud-native tools

## About Toolkits

Toolkits are hands-on guides to specific tools. Unlike Foundations (timeless theory) and Disciplines (practices), toolkits evolve with the ecosystem. We focus on CNCF-graduated and widely-adopted tools.

## Structure

| Toolkit | Focus | Modules |
|---------|-------|---------|
| [Observability](observability-intelligence/observability/) | Prometheus, OpenTelemetry, Grafana, Loki, Pixie, Hubble, Coroot | 8 |
| [GitOps & Deployments](cicd-delivery/gitops-deployments/) | ArgoCD, Argo Rollouts, Flux, Helm | 4 |
| [CI/CD Pipelines](cicd-delivery/ci-cd-pipelines/) | Dagger, Tekton, Argo Workflows | 3 |
| [IaC Tools](infrastructure-networking/iac-tools/) | Terraform, OpenTofu, Pulumi, Ansible, Wing, SST, System Initiative, Nitric | 10 |
| [Security Tools](security-quality/security-tools/) | Vault, OPA/Gatekeeper, Falco, Tetragon, KubeArmor | 6 |
| [Networking](infrastructure-networking/networking/) | Cilium, Service Mesh | 2 |
| [Scaling & Reliability](developer-experience/scaling-reliability/) | Karpenter, KEDA, Velero | 3 |
| [Platforms](infrastructure-networking/platforms/) | Backstage, Crossplane, cert-manager | 3 |
| [Developer Experience](developer-experience/) | K9s, Telepresence, Local K8s, DevPod, Gitpod/Codespaces | 5 |
| [ML Platforms](data-ai-platforms/ml-platforms/) | Kubeflow, MLflow, Feature Stores, vLLM, Ray Serve, LangChain | 6 |
| [AIOps Tools](observability-intelligence/aiops-tools/) | Anomaly detection, Event correlation | 4 |
| [Source Control](cicd-delivery/source-control/) | GitLab, Gitea/Forgejo, GitHub Advanced | 3 |
| [Code Quality](security-quality/code-quality/) | SonarQube, Semgrep, CodeQL, Snyk, Trivy | 5 |
| [Container Registries](cicd-delivery/container-registries/) | Harbor, Zot, Dragonfly | 3 |
| [K8s Distributions](infrastructure-networking/k8s-distributions/) | k3s, k0s, MicroK8s, Talos, OpenShift, Managed K8s | 6 |
| [Cloud-Native Databases](data-ai-platforms/cloud-native-databases/) | CockroachDB, CloudNativePG, Neon/PlanetScale, Vitess | 4 |
| [Storage](infrastructure-networking/storage/) | Rook/Ceph, MinIO, Longhorn | 3 |
| **Total** | | **78** |

## How to Use Toolkits

1. **Read Foundations first** - Understand the theory
2. **Read Disciplines** - Understand the practices
3. **Pick tools based on need** - Not everything applies
4. **Hands-on practice** - Toolkits include exercises
5. **Stay current** - Tools evolve, check release notes

## Tool Selection Philosophy

We include tools that are:

- **CNCF Graduated/Incubating** - Community validation
- **Production-proven** - Battle-tested at scale
- **Actively maintained** - Regular releases, active community
- **Interoperable** - Works with the ecosystem

## Prerequisites

Before diving into toolkits:

- Complete relevant [Foundations](../foundations/) modules
- Understand the [Discipline](../disciplines/) the tool supports
- Have a Kubernetes cluster (kind/minikube for learning)

## Start Learning

Pick a toolkit based on your current focus:

- **Starting observability?** Begin with [Prometheus](observability-intelligence/observability/module-1.1-prometheus/)
- **Implementing GitOps?** Start with [ArgoCD](cicd-delivery/gitops-deployments/module-2.1-argocd/)
- **Managing infrastructure?** Check out [Terraform](infrastructure-networking/iac-tools/module-7.1-terraform/)
- **Building a platform?** Check out [Backstage](infrastructure-networking/platforms/module-7.1-backstage/)

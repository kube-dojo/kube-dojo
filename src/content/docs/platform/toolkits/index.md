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
| [Observability](observability/) | Prometheus, OpenTelemetry, Grafana, Loki, Pixie, Hubble, Coroot | 8 |
| [GitOps & Deployments](gitops-deployments/) | ArgoCD, Argo Rollouts, Flux, Helm | 4 |
| [CI/CD Pipelines](ci-cd-pipelines/) | Dagger, Tekton, Argo Workflows | 3 |
| [IaC Tools](iac-tools/) | Terraform, OpenTofu, Pulumi, Ansible, Wing, SST, System Initiative, Nitric | 10 |
| [Security Tools](security-tools/) | Vault, OPA/Gatekeeper, Falco, Tetragon, KubeArmor | 6 |
| [Networking](networking/) | Cilium, Service Mesh | 2 |
| [Scaling & Reliability](scaling-reliability/) | Karpenter, KEDA, Velero | 3 |
| [Platforms](platforms/) | Backstage, Crossplane, cert-manager | 3 |
| [Developer Experience](developer-experience/) | K9s, Telepresence, Local K8s, DevPod, Gitpod/Codespaces | 5 |
| [ML Platforms](ml-platforms/) | Kubeflow, MLflow, Feature Stores, vLLM, Ray Serve, LangChain | 6 |
| [AIOps Tools](aiops-tools/) | Anomaly detection, Event correlation | 4 |
| [Source Control](source-control/) | GitLab, Gitea/Forgejo, GitHub Advanced | 3 |
| [Code Quality](code-quality/) | SonarQube, Semgrep, CodeQL, Snyk, Trivy | 5 |
| [Container Registries](container-registries/) | Harbor, Zot, Dragonfly | 3 |
| [K8s Distributions](k8s-distributions/) | k3s, k0s, MicroK8s, Talos, OpenShift, Managed K8s | 6 |
| [Cloud-Native Databases](cloud-native-databases/) | CockroachDB, CloudNativePG, Neon/PlanetScale, Vitess | 4 |
| [Storage](storage/) | Rook/Ceph, MinIO, Longhorn | 3 |
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

- **Starting observability?** Begin with [Prometheus](observability/module-1.1-prometheus/)
- **Implementing GitOps?** Start with [ArgoCD](gitops-deployments/module-2.1-argocd/)
- **Managing infrastructure?** Check out [Terraform](iac-tools/module-7.1-terraform/)
- **Building a platform?** Check out [Backstage](platforms/module-7.1-backstage/)

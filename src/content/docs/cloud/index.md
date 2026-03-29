---
title: "Cloud"
sidebar:
  order: 1
---
**Master the hyperscalers that run your Kubernetes clusters.**

Kubernetes doesn't exist in a vacuum. It runs on AWS, GCP, or Azure — and you need to know the cloud platform underneath. This track takes you from cloud fundamentals to production-grade managed Kubernetes.

---

## Learning Path

```
Rosetta Stone (cross-provider concepts)
        │
        ├─── AWS ──────────────────────────┐
        │    Essentials (12) → EKS (5)     │
        │                                  │
        ├─── Google Cloud ─────────────────┤
        │    Essentials (12) → GKE (5)     │
        │                                  │
        └─── Azure ────────────────────────┤
             Essentials (12) → AKS (4)     │
                                           │
                    ┌──────────────────────-┘
                    ▼
        Architecture & Enterprise
        ├── Architecture Patterns (4)
        ├── Advanced Operations (10)
        ├── Managed Services (10)
        └── Enterprise & Hybrid (10)
```

**Pick your provider** — you don't need all three. Learn the essentials for the cloud you use, then go deep on its managed Kubernetes offering.

---

## Sections

### AWS (17 modules)

| Section | Modules | Description |
|---------|---------|-------------|
| [AWS Essentials](aws-essentials/) | 12 | IAM, VPC, EC2, S3, Route53, ECR, ECS, Lambda, Secrets, CloudWatch, CI/CD, CloudFormation |
| [EKS Deep Dive](eks-deep-dive/) | 5 | EKS architecture, networking, identity, autoscaling, production |

### Google Cloud (17 modules)

| Section | Modules | Description |
|---------|---------|-------------|
| [GCP Essentials](gcp-essentials/) | 12 | IAM, VPC, Compute, Cloud Storage, DNS, Artifact Registry, Cloud Run, Functions, Secret Manager, Monitoring, Cloud Build, Deployment Manager |
| [GKE Deep Dive](gke-deep-dive/) | 5 | GKE architecture, networking, Workload Identity, Autopilot, Fleet |

### Azure (16 modules)

| Section | Modules | Description |
|---------|---------|-------------|
| [Azure Essentials](azure-essentials/) | 12 | Entra ID, VNet, VMs, Blob Storage, Azure DNS, ACR, ACI, Functions, Key Vault, Monitor, DevOps, Bicep |
| [AKS Deep Dive](aks-deep-dive/) | 4 | AKS architecture, networking, identity, production |

### Architecture & Enterprise (34 modules)

| Section | Modules | Description |
|---------|---------|-------------|
| [Hyperscaler Rosetta Stone](hyperscaler-rosetta-stone/) | 1 | Cross-provider concept mapping |
| [Architecture Patterns](architecture-patterns/) | 4 | Managed vs self-managed, multi-cluster, cloud IAM, VPC topologies |
| [Advanced Operations](advanced-operations/) | 10 | Multi-account, transit hubs, cross-cluster networking, DR, active-active |
| [Managed Services](managed-services/) | 10 | Databases, caching, messaging, ML services, analytics |
| [Enterprise & Hybrid](enterprise-hybrid/) | 10 | Landing zones, hybrid connectivity, compliance, migration, fleet management |

**84 modules total.** Not everything goes into Kubernetes — the essentials tracks cover standalone containers, serverless, and when K8s is overkill.

---

## Prerequisites

- [Fundamentals](../prerequisites/) — Cloud Native 101, Docker, basic K8s
- [Linux](../linux/) — recommended for networking and security modules
- [Certifications](../k8s/) — recommended (CKA/CKAD give hands-on K8s experience before cloud-specific deep dives)

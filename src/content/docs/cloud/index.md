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

## Safest Default Route

```text
Hyperscaler Rosetta Stone
   |
Pick one provider
   |
Provider Essentials
   |
Managed Kubernetes (EKS / GKE / AKS)
   |
Architecture & Enterprise
```

Do not try to learn all three providers at once unless you have a specific architecture reason. Most learners should go deep on one provider first.

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

## Good Next Steps After Cloud

- go to [Platform Engineering](../platform/) if you want SRE, GitOps, delivery automation, and platform design on top of cloud infrastructure
- go to [On-Premises](../on-premises/) if you want to compare managed-cloud assumptions with private-infrastructure realities

## Choose Your Exit Ramp

| After Cloud, if you want to... | Go to... | Why |
|---|---|---|
| run internal platforms, improve delivery, and standardize operations | [Platform Engineering](../platform/) | cloud skill alone does not teach platform discipline |
| evaluate private infrastructure, repatriation, or hybrid tradeoffs | [On-Premises](../on-premises/) | managed services hide many concerns that become explicit on private infrastructure |
| support ML workloads and AI systems on cloud Kubernetes | [AI/ML Engineering](../ai-ml-engineering/) | the AI/ML track gives the application and model layer this track does not |

## Common Failure Modes In Cloud

- trying to learn all three providers before you can operate one of them well
- jumping into enterprise/hybrid sections before a provider essentials path is solid
- confusing provider familiarity with platform-engineering depth

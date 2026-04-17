---
title: "Cloud"
sidebar:
  order: 1
---
**Master the hyperscaler that actually runs your Kubernetes clusters.**

Kubernetes doesn't exist in a vacuum. It runs on AWS, GCP, or Azure — and you need to know the cloud platform underneath. This track takes you from cloud fundamentals to managed Kubernetes operations and then into the architecture and operating-model decisions that show up in real production environments.

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

**Pick one provider deeply first** — you do not need all three. Learn the essentials for the cloud you actually use, then go deep on its managed Kubernetes offering before you spend time comparing clouds.

## Start Here If

- you already understand basic Kubernetes workloads and want the provider context around them
- your next questions are about VPCs, IAM, managed control planes, or production cloud networking
- you need one real cloud path rather than vague multi-cloud familiarity

## Do Not Start Here First If

- you still need terminal, Git, container, or YAML confidence
- you have never operated a basic cluster locally or in a learning environment
- you are trying to learn "all cloud" before you can reason clearly about one provider

If that is your situation, start with [Prerequisites](../prerequisites/) first and then come back here with stronger Kubernetes basics.

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

Do not try to learn all three providers at once unless you have a specific architecture reason. Most learners should go deep on one provider first and treat the others as later translation work, not simultaneous study.

## Which Cloud Route Fits You?

| If your goal is... | Start with... | Then move to... |
|---|---|---|
| become productive on the cloud your team already uses | the matching provider essentials section | that provider's managed Kubernetes path |
| compare providers without drowning in details | [Hyperscaler Rosetta Stone](hyperscaler-rosetta-stone/) | one provider essentials path only |
| support managed Kubernetes on AWS in a production team | [AWS Essentials](aws-essentials/) | [EKS Deep Dive](eks-deep-dive/) |
| support managed Kubernetes on Google Cloud in a production team | [GCP Essentials](gcp-essentials/) | [GKE Deep Dive](gke-deep-dive/) |
| support managed Kubernetes on Azure in a production team | [Azure Essentials](azure-essentials/) | [AKS Deep Dive](aks-deep-dive/) |
| reason about enterprise tradeoffs, hybrid design, and operating models | one provider path first | Architecture Patterns -> Advanced Operations -> Enterprise & Hybrid |

The mistake to avoid is trying to use Architecture & Enterprise as your entry point. Those sections assume you already understand at least one provider's primitives.

Equivalent depth means this:
- any one of `AWS Essentials -> EKS`, `GCP Essentials -> GKE`, or `Azure Essentials -> AKS` is enough to make you productive on that provider
- none of those paths makes you "multi-cloud ready" by itself
- the cross-provider insight comes later, once one provider already feels operationally normal to you

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

- [Fundamentals](../prerequisites/) — Cloud Native 101, Docker, basic K8s (`~6-8 hours` if you only need the cloud-facing subset)
- [Linux](../linux/) — recommended for networking and security modules
- [Certifications](../k8s/) — recommended (CKA/CKAD give hands-on K8s experience before cloud-specific deep dives)

## Common Failure Modes In Cloud

- trying to learn all three providers before you can operate one of them well
- jumping into enterprise and hybrid sections before a provider essentials path is solid
- confusing provider familiarity with platform-engineering depth
- treating managed-cloud convenience as proof that you understand the underlying operational tradeoffs

## Good Next Steps After Cloud

- go to [Platform Engineering](../platform/) if you want SRE, GitOps, delivery automation, and platform design on top of cloud infrastructure
- go to [On-Premises](../on-premises/) if you want to compare managed-cloud assumptions with private-infrastructure realities
- go to [AI/ML Engineering](../ai-ml-engineering/) if your cloud path is mainly about serving, training, or operating ML workloads on managed platforms

If you are responsible for production at scale, treat `Advanced Operations` as part of the real cloud path rather than an optional appendix. Provider essentials and managed-Kubernetes basics get you running; the operations and enterprise sections are where multi-account design, networking boundaries, resilience, and governance start to look like production.

## Choose Your Exit Ramp

| After Cloud, if you want to... | Go to... | Why |
|---|---|---|
| run internal platforms, improve delivery, and standardize operations | [Platform Engineering](../platform/) | cloud skill alone does not teach platform discipline |
| evaluate private infrastructure, repatriation, or hybrid tradeoffs | [On-Premises](../on-premises/) | managed services hide many concerns that become explicit on private infrastructure |
| support ML workloads and AI systems on cloud Kubernetes | [AI/ML Engineering](../ai-ml-engineering/) | the AI/ML track gives the application and model layer this track does not |

---
title: "Kubernetes Distributions Toolkit"
sidebar:
  order: 0
  label: "K8s Distributions"
---
> **Toolkit Track** | 7 Modules | ~6.5 hours total

## Overview

The Kubernetes Distributions Toolkit covers lightweight Kubernetes alternatives for edge, IoT, development, and resource-constrained environments. When vanilla Kubernetes is too heavy—requiring too much RAM, too many nodes, or too complex to manage—these distributions deliver Kubernetes-compatible APIs with dramatically lower overhead.

This toolkit applies concepts from [Systems Thinking](../../../foundations/systems-thinking/) and [Platform Engineering](../../../disciplines/core-platform/platform-engineering/).

## Prerequisites

Before starting this toolkit:
- Kubernetes fundamentals (kubectl, deployments, services)
- Container runtime basics (containerd, Docker)
- Basic Linux system administration
- Understanding of when you'd use Kubernetes vs simpler alternatives

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 14.1 | [k3s](module-14.1-k3s/) | `[MEDIUM]` | 45-50 min |
| 14.2 | [k0s](module-14.2-k0s/) | `[MEDIUM]` | 40-45 min |
| 14.3 | [MicroK8s](module-14.3-microk8s/) | `[MEDIUM]` | 40-45 min |
| 14.4 | [Talos](module-14.4-talos/) | `[COMPLEX]` | 50-55 min |
| 14.5 | [OpenShift](module-14.5-openshift/) | `[COMPLEX]` | 50-55 min |
| 14.6 | [Managed Kubernetes](module-14.6-managed-kubernetes/) | `[COMPLEX]` | 55-60 min |
| 14.7 | [RKE2](module-14.7-rke2/) | `[COMPLEX]` | 50-55 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy k3s** — The most popular lightweight Kubernetes for edge
2. **Run k0s** — Zero-friction Kubernetes for any environment
3. **Use MicroK8s** — Canonical's snap-based Kubernetes
4. **Understand Talos** — Immutable OS built specifically for Kubernetes
5. **Navigate OpenShift** — Enterprise Kubernetes with batteries included
6. **Compare managed services** — EKS vs GKE vs AKS decision making
7. **Deploy RKE2** — Enterprise-hardened, FIPS-compliant Kubernetes for high-security environments
8. **Choose the right distribution** — Match specific infrastructure and compliance requirements to distribution strengths

## Distribution Selection Guide

```
WHICH KUBERNETES DISTRIBUTION?
─────────────────────────────────────────────────────────────────────────────

"I need Kubernetes on edge devices with limited resources"
└──▶ k3s
     • 512MB RAM minimum (production: 1GB)
     • Single binary, ~60MB
     • Built-in: Traefik, Local Storage, SQLite
     • CNCF Sandbox project
     • Most popular edge K8s

"I need enterprise security, FIPS compliance, and CIS hardening"
└──▶ RKE2
     • Hardened by default, passes CIS Benchmark
     • FIPS 140-2 validated cryptography (via go-fips)
     • Single binary, optimized for air-gap registries
     • Default Rancher provisioner
     • Ideal for defense, gov, and regulated industries

"I want zero dependencies, single binary, works anywhere"
└──▶ k0s
     • ~180MB single binary
     • No host dependencies (even for HA)
     • Built-in: kube-router, containerd
     • Cluster API support
     • Enterprise support (Mirantis)

"I'm using Ubuntu/Canonical ecosystem"
└──▶ MicroK8s
     • Snap-based installation
     • Add-ons via microk8s enable
     • Tight Ubuntu integration
     • Built-in: dns, storage, dashboard
     • Popular for development

"I need vanilla Kubernetes behavior"
└──▶ kubeadm / Cluster API
     • Full upstream K8s
     • Most compatible
     • More resources required
     • Production proven at scale

COMPARISON MATRIX:
─────────────────────────────────────────────────────────────────────────────
                    k3s         k0s         MicroK8s    RKE2        kubeadm
─────────────────────────────────────────────────────────────────────────────
Min RAM            512MB       512MB       512MB       4GB         2GB
Binary size        ~60MB       ~180MB      Via snap    ~200MB+     ~300MB
Architecture       ARM/AMD64   ARM/AMD64   ARM/AMD64   AMD64/ARM64 ARM/AMD64
HA built-in        ✓ (embed)   ✓           ✓           ✓ (embed)   Manual
Datastore          SQLite/etc  SQLite/etc  Dqlite      etcd        etcd
Install method     curl|bash   curl|bash   snap        curl|bash   apt/yum
CNCF project       Sandbox     No          No          No          Yes
Air-gap support    ✓           ✓           ✓           ✓ (native)  ✓
Windows nodes      ✓           ✓           Limited     ✓           ✓
Cert rotation      Auto        Auto        Auto        Auto        Manual
FIPS 140-2         No          No          No          ✓           Manual
CIS Hardened       Manual      Manual      Manual      ✓ (Default) Manual
```

## The Lightweight Kubernetes Landscape

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  KUBERNETES DISTRIBUTION LANDSCAPE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  UPSTREAM KUBERNETES                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  kubeadm         │  Cluster API      │  kOps                        │   │
│  │  (official)      │  (declarative)    │  (AWS-focused)               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LIGHTWEIGHT DISTRIBUTIONS                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  k3s                  k0s                  MicroK8s                │   │
│  │  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐         │   │
│  │  │ Rancher/SUSE│     │  Mirantis   │      │  Canonical  │         │   │
│  │  │ Edge focus  │     │ Zero deps   │      │ Snap-based  │         │   │
│  │  │ CNCF Sandbox│     │             │      │ Ubuntu      │         │   │
│  │  └─────────────┘     └─────────────┘      └─────────────┘         │   │
│  │                                                                     │   │
│  │  Kind                 minikube              k3d                    │   │
│  │  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐         │   │
│  │  │  K8s in     │     │  VM-based   │      │ k3s in      │         │   │
│  │  │  Docker     │     │  local dev  │      │ Docker      │         │   │
│  │  │  (testing)  │     │  (original) │      │ (fast)      │         │   │
│  │  └─────────────┘     └─────────────┘      └─────────────┘         │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HARDENED / ENTERPRISE                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RKE2                 OpenShift             Talos                  │   │
│  │  ┌─────────────┐     ┌─────────────┐      ┌─────────────┐         │   │
│  │  │ Federal/CIS │     │ Enterprise  │      │ Immutable   │         │   │
│  │  │ FIPS secure │     │ Batteries-in│      │ API-only    │         │   │
│  │  └─────────────┘     └─────────────┘      └─────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MANAGED KUBERNETES                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EKS (AWS)     │  GKE (Google)   │  AKS (Azure)   │  DOKS (DO)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Use Case Decision Tree

```
USE CASE DECISION TREE
─────────────────────────────────────────────────────────────────────────────

Start: What's your primary use case?
                    │
    ┌───────────────┼───────────────┬───────────────┬───────────────┐
    │               │               │               │               │
    ▼               ▼               ▼               ▼               ▼
Edge/IoT?      Development?    Production?    Air-gapped?    Federal/Compliance?
    │               │               │               │               │
    │ Yes           │ Yes           │ Yes           │ Yes           │ Yes
    ▼               ▼               ▼               ▼               ▼
k3s             Kind/k3d       Assess needs    k3s or k0s      RKE2
(smallest,      (fastest,      │               (both support   (FIPS 140-2,
 most proven)    ephemeral)    │               offline install) CIS hardened)
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
              <100 nodes?            >100 nodes?
                    │                     │
                    ▼                     ▼
              k3s or k0s            kubeadm/EKS/GKE
              (either works,        (need full scale)
               choose ecosystem)

RESOURCE CONSTRAINTS:
─────────────────────────────────────────────────────────────────────────────
<1GB RAM available        →  k3s (most optimized for low memory)
1-2GB RAM available       →  k3s, k0s, or MicroK8s (all work)
>2GB RAM available        →  Any distribution, consider features
>4GB RAM available        →  RKE2 (ideal for security over efficiency)
ARM devices               →  k3s (best ARM support), k0s, MicroK8s
x86_64 only               →  All options available
```

## Study Path

```
Module 14.1: k3s
     │
     │  Most popular lightweight K8s
     │  Best for edge and IoT
     │  CNCF Sandbox project
     ▼
Module 14.2: k0s
     │
     │  Zero dependencies
     │  Clean architecture
     │  Cluster API support
     ▼
Module 14.3: MicroK8s
     │
     │  Snap-based
     │  Add-on ecosystem
     │  Ubuntu integration
     ▼
Module 14.4: Talos
     │
     │  Immutable OS
     │  API-only management
     │  Maximum security
     ▼
Module 14.5: OpenShift
     │
     │  Enterprise platform
     │  Batteries included
     │  Red Hat support
     ▼
Module 14.6: Managed Kubernetes
     │
     │  EKS vs GKE vs AKS
     │  Provider comparison
     │  Cost optimization
     ▼
Module 14.7: RKE2
     │
     │  Enterprise hardened
     │  CIS Benchmark compliance
     │  FIPS 140-2 validated
     ▼
[Toolkit Complete] → Next: CI/CD Pipelines Toolkit
```

## Resource Requirements

```
RESOURCE COMPARISON
─────────────────────────────────────────────────────────────────────────────

                    k3s         k0s         MicroK8s    RKE2        kubeadm
─────────────────────────────────────────────────────────────────────────────
MINIMUM (Dev/Test):
─────────────────────────────────────────────────────────────────────────────
RAM (server)       512MB       512MB       540MB       4GB         2GB
RAM (agent)        75MB        100MB       100MB       2GB         100MB
Disk               200MB       300MB       2GB         10GB        2GB
CPU                1 core      1 core      1 core      2 cores     2 cores

RECOMMENDED (Production):
─────────────────────────────────────────────────────────────────────────────
RAM (server)       2GB         2GB         2GB         8GB         4GB
RAM (agent)        512MB       512MB       512MB       4GB         1GB
Disk               10GB        10GB        20GB        40GB        20GB
CPU                2 cores     2 cores     2 cores     4 cores     2 cores
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| k3s | Deploy HA cluster, run workloads, configure storage |
| k0s | Zero-dependency install, cluster-api bootstrap |
| MicroK8s | Snap install, enable add-ons, cluster join |
| Talos | Deploy cluster, verify security, API management |
| OpenShift | S2I builds, Routes, BuildConfigs |
| Managed K8s | Multi-provider comparison, cost analysis |
| RKE2 | Deploy CIS hardened cluster, verify air-gap registry |

## Related Tracks

- **Before**: [Container Registries Toolkit](../../cicd-delivery/container-registries/) — Store images for your cluster
- **Related**: [Developer Experience Toolkit](../../developer-experience/) — Local K8s options
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Automate cluster provisioning
- **After**: [CI/CD Pipelines Toolkit](../../cicd-delivery/ci-cd-pipelines/) — Deploy to your clusters

---

*"The best Kubernetes distribution is the one that fits your constraints. Sometimes that's vanilla K8s, sometimes it's 60MB running on a Raspberry Pi."*

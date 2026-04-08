---
title: "Kubernetes Distributions Toolkit"
sidebar:
  order: 0
  label: "K8s Distributions"
---
> **Toolkit Track** | 6 Modules | ~5 hours total

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

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy k3s** — The most popular lightweight Kubernetes for edge
2. **Run k0s** — Zero-friction Kubernetes for any environment
3. **Use MicroK8s** — Canonical's snap-based Kubernetes
4. **Understand Talos** — Immutable OS built specifically for Kubernetes
5. **Navigate OpenShift** — Enterprise Kubernetes with batteries included
6. **Compare managed services** — EKS vs GKE vs AKS decision making
7. **Choose the right distribution** — Match requirements to distribution strengths

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
                    k3s         k0s         MicroK8s    kubeadm
─────────────────────────────────────────────────────────────────────────────
Min RAM            512MB       512MB       512MB       2GB
Binary size        ~60MB       ~180MB      Via snap    ~300MB
Architecture       ARM/AMD64   ARM/AMD64   ARM/AMD64   ARM/AMD64
HA built-in        ✓ (embed)   ✓           ✓           Manual
Datastore          SQLite/etc  SQLite/etc  Dqlite      etcd
Install method     curl|bash   curl|bash   snap        apt/yum
CNCF project       Sandbox     No          No          Yes
Air-gap support    ✓           ✓           ✓           ✓
Windows nodes      ✓           ✓           Limited     ✓
Cert rotation      Auto        Auto        Auto        Manual
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
│  MANAGED KUBERNETES                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EKS (AWS)     │  GKE (Google)   │  AKS (Azure)   │  DOKS (DO)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SPECIALIZED                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OpenShift      │  Rancher         │  Tanzu          │  K8s@Home   │   │
│  │  (Enterprise)   │  (Multi-cluster) │  (VMware)       │  (Hobby)    │   │
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
    ┌───────────────┼───────────────┬───────────────┐
    │               │               │               │
    ▼               ▼               ▼               ▼
Edge/IoT?      Development?    Production?    Air-gapped?
    │               │               │               │
    │ Yes           │ Yes           │ Yes           │ Yes
    ▼               ▼               ▼               ▼
k3s             Kind/k3d       Assess needs    k3s or k0s
(smallest,      (fastest,      │               (both support
 most proven)    ephemeral)    │               offline install)
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
ARM devices               →  k3s (best ARM support), k0s, MicroK8s
x86_64 only               →  All options available
```

## Architecture Comparison

### k3s Architecture

```
k3s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                    ┌─────────────────────────────────────────┐
                    │           k3s Server (Master)           │
                    │                                         │
                    │  ┌─────────────────────────────────────┐│
                    │  │          k3s Binary (~60MB)         ││
                    │  │                                     ││
                    │  │  API Server │ Controller │ Scheduler││
                    │  │  ─────────────────────────────────  ││
                    │  │  kube-proxy │ kubelet │ containerd  ││
                    │  │  ─────────────────────────────────  ││
                    │  │  Traefik │ CoreDNS │ Local Path    ││
                    │  │  ─────────────────────────────────  ││
                    │  │       Flannel (default CNI)         ││
                    │  └─────────────────────────────────────┘│
                    │                    │                    │
                    │  ┌─────────────────▼─────────────────┐  │
                    │  │   SQLite (default) / etcd / MySQL │  │
                    │  │          PostgreSQL                │  │
                    │  └───────────────────────────────────┘  │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
           │   k3s Agent   │    │   k3s Agent   │    │   k3s Agent   │
           │   (Worker)    │    │   (Worker)    │    │   (Worker)    │
           │               │    │               │    │               │
           │  kubelet      │    │  kubelet      │    │  kubelet      │
           │  kube-proxy   │    │  kube-proxy   │    │  kube-proxy   │
           │  containerd   │    │  containerd   │    │  containerd   │
           └───────────────┘    └───────────────┘    └───────────────┘

WHAT'S REMOVED FROM UPSTREAM K8S:
─────────────────────────────────────────────────────────────────────────────
✗ etcd (replaced with SQLite for single-node)
✗ Cloud controller manager
✗ Legacy/alpha features
✗ In-tree storage drivers
✗ In-tree cloud providers

WHAT'S BUNDLED:
─────────────────────────────────────────────────────────────────────────────
✓ Traefik Ingress Controller
✓ CoreDNS
✓ Flannel CNI
✓ Local Path Provisioner
✓ Service Load Balancer
✓ Network Policy Controller
```

### k0s Architecture

```
k0s ARCHITECTURE
─────────────────────────────────────────────────────────────────────────────

                    ┌─────────────────────────────────────────┐
                    │          k0s Controller Node            │
                    │                                         │
                    │  ┌─────────────────────────────────────┐│
                    │  │         k0s Binary (~180MB)         ││
                    │  │                                     ││
                    │  │  API Server │ Controller │ Scheduler││
                    │  │  ─────────────────────────────────  ││
                    │  │  kube-proxy │ konnectivity-server   ││
                    │  │  ─────────────────────────────────  ││
                    │  │           kube-router              ││
                    │  │  (CNI, network policy, service LB) ││
                    │  └─────────────────────────────────────┘│
                    │                    │                    │
                    │  ┌─────────────────▼─────────────────┐  │
                    │  │     etcd (embedded) / SQLite      │  │
                    │  │           MySQL / PostgreSQL       │  │
                    │  └───────────────────────────────────┘  │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
           ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
           │   k0s Worker  │    │   k0s Worker  │    │   k0s Worker  │
           │               │    │               │    │               │
           │  kubelet      │    │  kubelet      │    │  kubelet      │
           │  containerd   │    │  containerd   │    │  containerd   │
           │  kube-proxy   │    │  kube-proxy   │    │  kube-proxy   │
           └───────────────┘    └───────────────┘    └───────────────┘

KEY DIFFERENTIATOR: Zero Host Dependencies
─────────────────────────────────────────────────────────────────────────────
• All components bundled in single binary
• No kubelet or containerd required on host
• k0s brings its own container runtime
• Clean /var/lib/k0s directory for all state
```

## Common Architectures

### Single Node (Development/Edge)

```
SINGLE NODE DEPLOYMENT
─────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────┐
│                         Single Node                                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    k3s/k0s/MicroK8s                              │   │
│  │                                                                   │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                │   │
│  │  │ Control    │  │  Worker    │  │  Storage   │                │   │
│  │  │ Plane      │  │  (kubelet) │  │  (SQLite)  │                │   │
│  │  └────────────┘  └────────────┘  └────────────┘                │   │
│  │                                                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                     Workloads                             │   │   │
│  │  │  [App1] [App2] [App3] [DB] [Cache]                       │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Use cases:
• Development workstations
• Edge devices (retail, manufacturing)
• CI/CD runners
• Home lab / learning
```

### High Availability (Production)

```
HIGH AVAILABILITY DEPLOYMENT
─────────────────────────────────────────────────────────────────────────────

        ┌───────────────────────────────────────────────────────┐
        │                   Load Balancer                       │
        │              (HAProxy / cloud LB)                     │
        └───────────────────────────┬───────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  Server 1     │           │  Server 2     │           │  Server 3     │
│  (control)    │◄─────────▶│  (control)    │◄─────────▶│  (control)    │
│               │           │               │           │               │
│  ┌─────────┐  │           │  ┌─────────┐  │           │  ┌─────────┐  │
│  │  etcd   │◄─┼───────────┼─▶│  etcd   │◄─┼───────────┼─▶│  etcd   │  │
│  └─────────┘  │           │  └─────────┘  │           │  └─────────┘  │
└───────────────┘           └───────────────┘           └───────────────┘
        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   Agent 1     │           │   Agent 2     │           │   Agent N     │
│   (worker)    │           │   (worker)    │           │   (worker)    │
└───────────────┘           └───────────────┘           └───────────────┘

HA OPTIONS BY DISTRIBUTION:
─────────────────────────────────────────────────────────────────────────────
k3s:      --cluster-init (embedded etcd) or external DB
k0s:      k0sctl for automated HA setup
MicroK8s: microk8s add-node (Dqlite clustering)
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
[Toolkit Complete] → Next: CI/CD Pipelines Toolkit
```

## Resource Requirements

```
RESOURCE COMPARISON
─────────────────────────────────────────────────────────────────────────────

                    k3s         k0s         MicroK8s    kubeadm
─────────────────────────────────────────────────────────────────────────────
MINIMUM (Dev/Test):
─────────────────────────────────────────────────────────────────────────────
RAM (server)       512MB       512MB       540MB       2GB
RAM (agent)        75MB        100MB       100MB       100MB
Disk               200MB       300MB       2GB         2GB
CPU                1 core      1 core      1 core      2 cores

RECOMMENDED (Production):
─────────────────────────────────────────────────────────────────────────────
RAM (server)       2GB         2GB         2GB         4GB
RAM (agent)        512MB       512MB       512MB       1GB
Disk               10GB        10GB        20GB        20GB
CPU                2 cores     2 cores     2 cores     2 cores
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

## Related Tracks

- **Before**: [Container Registries Toolkit](../../cicd-delivery/container-registries/) — Store images for your cluster
- **Related**: [Developer Experience Toolkit](../../developer-experience/) — Local K8s options
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Automate cluster provisioning
- **After**: [CI/CD Pipelines Toolkit](../../cicd-delivery/ci-cd-pipelines/) — Deploy to your clusters

---

*"The best Kubernetes distribution is the one that fits your constraints. Sometimes that's vanilla K8s, sometimes it's 60MB running on a Raspberry Pi."*

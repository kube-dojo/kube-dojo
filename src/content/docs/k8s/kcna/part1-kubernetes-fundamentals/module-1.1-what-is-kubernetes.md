---
title: "Module 1.1: What is Kubernetes?"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.1-what-is-kubernetes
sidebar:
  order: 2
---
> **Complexity**: `[QUICK]` - Foundational concepts
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: None

---

## Why This Module Matters

"What is Kubernetes?" might seem like a simple question, but understanding it deeply is crucial. KCNA tests whether you truly understand Kubernetes' purpose, not just its features.

This module establishes the foundation everything else builds on.

---

## The Problem Kubernetes Solves

```
┌─────────────────────────────────────────────────────────────┐
│              BEFORE KUBERNETES                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Traditional Deployment:                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Server 1         Server 2         Server 3         │   │
│  │  ┌─────────┐     ┌─────────┐     ┌─────────┐       │   │
│  │  │  App A  │     │  App B  │     │  App C  │       │   │
│  │  └─────────┘     └─────────┘     └─────────┘       │   │
│  │  ┌─────────┐     ┌─────────┐     ┌─────────┐       │   │
│  │  │   OS    │     │   OS    │     │   OS    │       │   │
│  │  └─────────┘     └─────────┘     └─────────┘       │   │
│  │  ┌─────────┐     ┌─────────┐     ┌─────────┐       │   │
│  │  │Hardware │     │Hardware │     │Hardware │       │   │
│  │  └─────────┘     └─────────┘     └─────────┘       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Problems:                                                 │
│  • One app per server = waste                              │
│  • Server dies = app dies                                  │
│  • Manual scaling                                          │
│  • Deployment is risky                                     │
│  • No standard way to manage                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## What is Kubernetes?

**Kubernetes** (K8s) is an open-source **container orchestration platform** that automates deploying, scaling, and managing containerized applications.

### Breaking That Down

| Term | Meaning |
|------|---------|
| **Open-source** | Free, community-driven, no vendor lock-in |
| **Container orchestration** | Managing many containers as a system |
| **Platform** | Foundation to build on, not just a tool |
| **Automates** | Reduces manual work and human error |

### The Name

- **Kubernetes** = Greek for "helmsman" or "pilot"
- **K8s** = K + 8 letters + s (shorthand)
- Originated at Google (based on Borg)
- Donated to CNCF in 2015

---

## What Kubernetes Does

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CAPABILITIES                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DEPLOYMENT                                             │
│     "Run my app"                                           │
│     ├── Deploy containers                                  │
│     ├── Rolling updates                                    │
│     └── Rollback if needed                                 │
│                                                             │
│  2. SCALING                                                │
│     "Handle more traffic"                                  │
│     ├── Scale up (more replicas)                          │
│     ├── Scale down (fewer replicas)                       │
│     └── Autoscale based on metrics                        │
│                                                             │
│  3. HEALING                                                │
│     "Keep it running"                                      │
│     ├── Restart failed containers                          │
│     ├── Replace unhealthy nodes                           │
│     └── Reschedule if node dies                           │
│                                                             │
│  4. SERVICE DISCOVERY                                      │
│     "Let apps find each other"                            │
│     ├── DNS-based discovery                               │
│     ├── Load balancing                                    │
│     └── Internal networking                               │
│                                                             │
│  5. CONFIGURATION                                          │
│     "Manage settings"                                      │
│     ├── ConfigMaps for config                             │
│     ├── Secrets for sensitive data                        │
│     └── Environment injection                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubernetes vs Alternatives

### Why Not Just Use VMs?

| Aspect | Virtual Machines | Kubernetes + Containers |
|--------|------------------|------------------------|
| Startup time | Minutes | Seconds |
| Resource usage | Heavy (full OS) | Light (shared kernel) |
| Density | ~10s per host | ~100s per host |
| Portability | Limited | High |
| Scaling | Slow | Fast |

### Why Not Just Use Docker?

Docker runs containers. Kubernetes **orchestrates** them:

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER vs KUBERNETES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DOCKER:                                                   │
│  "Run this container on this machine"                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  docker run nginx                                   │   │
│  │  → Runs ONE container on ONE machine                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  KUBERNETES:                                               │
│  "Run 3 copies, keep them healthy, balance traffic"        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Deployment: nginx, replicas: 3                     │   │
│  │  → Runs across cluster                              │   │
│  │  → Self-heals if one dies                           │   │
│  │  → Load balances traffic                            │   │
│  │  → Scales up/down automatically                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Docker = Container runtime                                │
│  Kubernetes = Container orchestrator                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Kubernetes Concepts

### Declarative Configuration

You tell Kubernetes **what you want**, not **how to do it**:

```yaml
# You declare: "I want 3 nginx replicas"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3  # Desired state
  ...
```

Kubernetes continuously works to make reality match your declaration.

### Desired State vs Current State

```
┌─────────────────────────────────────────────────────────────┐
│              DESIRED STATE RECONCILIATION                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  You declare:     "I want 3 replicas"                      │
│                         │                                   │
│                         ▼                                   │
│  Kubernetes:      Checks current state                     │
│                         │                                   │
│           ┌─────────────┴─────────────┐                    │
│           │                           │                     │
│           ▼                           ▼                     │
│     If 2 running:              If 4 running:               │
│     "Create 1 more"            "Terminate 1"               │
│                                                             │
│  This loop runs CONTINUOUSLY                               │
│  Kubernetes never stops trying to match desired state      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Immutable Infrastructure

- Containers aren't modified in place
- Updates create new containers
- Old containers are replaced, not changed
- This ensures consistency and reproducibility

---

## Where Kubernetes Runs

Kubernetes can run:

| Environment | Examples |
|-------------|----------|
| **Public Cloud** | EKS (AWS), GKE (Google), AKS (Azure) |
| **Private Cloud** | OpenStack, VMware |
| **On-Premises** | Bare metal, data centers |
| **Edge** | Retail stores, factories |
| **Development** | minikube, kind, Docker Desktop |

This flexibility is a key advantage—no vendor lock-in.

---

## Did You Know?

- **Kubernetes came from Google's Borg** - Google ran Borg internally for 10+ years before creating Kubernetes as an open-source version.

- **K8s handles massive scale** - Large clusters can run 5,000+ nodes and 150,000+ pods.

- **Most CNCF projects integrate with K8s** - Kubernetes is the foundation of the cloud native ecosystem.

- **The release cycle is predictable** - New Kubernetes versions come out every ~4 months with a 14-month support window.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "K8s is just Docker" | Missing orchestration value | K8s orchestrates containers; Docker runs them |
| "K8s replaces VMs" | They serve different purposes | K8s runs ON VMs or bare metal |
| "K8s is only for big companies" | Missing development value | K8s works at any scale |
| "K8s is a container runtime" | Confusing layers | K8s uses runtimes like containerd |

---

## Quiz

1. **What does K8s stand for?**
   <details>
   <summary>Answer</summary>
   K8s is shorthand for Kubernetes. K + 8 letters (ubernete) + s.
   </details>

2. **What is the primary function of Kubernetes?**
   <details>
   <summary>Answer</summary>
   Container orchestration—automating deployment, scaling, and management of containerized applications across a cluster.
   </details>

3. **What's the difference between Docker and Kubernetes?**
   <details>
   <summary>Answer</summary>
   Docker is a container runtime (runs containers). Kubernetes is a container orchestrator (manages containers across multiple machines, handles scaling, healing, etc.).
   </details>

4. **What does "declarative configuration" mean in Kubernetes?**
   <details>
   <summary>Answer</summary>
   You declare the desired state (what you want), and Kubernetes works to make reality match. You don't give step-by-step commands.
   </details>

5. **Where did Kubernetes originate?**
   <details>
   <summary>Answer</summary>
   Google. It's based on their internal system called Borg. Google donated Kubernetes to CNCF in 2015.
   </details>

---

## Summary

**Kubernetes is**:
- An open-source container orchestration platform
- Automates deployment, scaling, and management
- Uses declarative configuration (desired state)
- Runs anywhere (cloud, on-prem, edge)

**Kubernetes does**:
- Deploys and updates containers
- Scales applications up and down
- Self-heals when things fail
- Provides service discovery
- Manages configuration

**Key insight**: Kubernetes is NOT a container runtime—it orchestrates containers that runtimes like containerd actually run.

---

## Next Module

[Module 1.2: Container Fundamentals](../module-1.2-container-fundamentals/) - Understanding containers before diving into Kubernetes architecture.

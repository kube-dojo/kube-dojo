---
title: "Module 1.3: What Is Kubernetes?"
slug: prerequisites/cloud-native-101/module-1.3-what-is-kubernetes
sidebar:
  order: 4
---
> **Complexity**: `[QUICK]` - High-level overview
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Module 1 (Containers), Module 2 (Docker)

---

## Why This Module Matters

You know what containers are. You can build and run them with Docker. But Docker runs containers on ONE machine. What happens when you need:
- Hundreds of containers?
- High availability (no downtime)?
- Automatic scaling?
- Multiple machines?

That's where Kubernetes comes in. This module gives you the big picture before diving into details.

---

## The Problem: Containers at Scale

Docker is great for running a few containers on your laptop. But production needs more:

```
┌─────────────────────────────────────────────────────────────┐
│              SINGLE MACHINE LIMITATIONS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Your Docker Host:                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  🐳 Container 1  🐳 Container 2  🐳 Container 3    │    │
│  │  🐳 Container 4  🐳 Container 5  🐳 Container 6    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Problems:                                                  │
│  ❌ Machine dies = ALL containers die                      │
│  ❌ Need more capacity? Buy bigger machine                 │
│  ❌ No automatic recovery                                  │
│  ❌ Manual load balancing                                  │
│  ❌ Updates require downtime                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What Production Needs

```
✅ Run containers across multiple machines
✅ Automatic restart when containers crash
✅ Automatic placement (which machine has capacity?)
✅ Load balancing between containers
✅ Rolling updates without downtime
✅ Scaling up/down based on demand
✅ Self-healing when things break
```

This is **container orchestration**, and Kubernetes is the industry standard.

---

## What Is Kubernetes?

Kubernetes (K8s) is an open-source container orchestration platform. It:

1. **Manages container deployment** across multiple machines
2. **Ensures desired state** - if something breaks, K8s fixes it
3. **Handles networking** - containers find and talk to each other
4. **Manages storage** - persistent data for stateful apps
5. **Automates operations** - scaling, updates, recovery

### The Analogy: Airport Operations

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES AS AIRPORT OPERATIONS               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Airport Control Tower = Kubernetes Control Plane          │
│  - Assigns planes to gates (schedules pods to nodes)        │
│  - Monitors all activity (tracks cluster state)             │
│  - Responds to incidents (restarts failed containers)       │
│                                                             │
│  Gates/Runways = Worker Nodes                               │
│  - Physical infrastructure where work happens               │
│  - Control tower assigns, gates execute                     │
│                                                             │
│  Planes = Pods (containers)                                 │
│  - Arrive, depart, get serviced                            │
│  - Control tower tracks status of each                      │
│                                                             │
│  Airlines = Namespaces                                      │
│  - Delta uses gates 1-10                                   │
│  - United uses gates 11-20                                 │
│  - Isolation between tenants                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubernetes Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CLUSTER                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           CONTROL PLANE (Master)                    │   │
│  │  ┌───────────┐  ┌──────────┐  ┌───────────────┐    │   │
│  │  │ API       │  │Scheduler │  │ Controller    │    │   │
│  │  │ Server    │  │          │  │ Manager       │    │   │
│  │  └───────────┘  └──────────┘  └───────────────┘    │   │
│  │  ┌───────────────────────────────────────────┐     │   │
│  │  │              etcd (database)              │     │   │
│  │  └───────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   WORKER NODES                      │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │   Node 1     │  │   Node 2     │  │  Node 3  │  │   │
│  │  │ ┌──┐ ┌──┐    │  │ ┌──┐ ┌──┐    │  │ ┌──┐     │  │   │
│  │  │ │P1│ │P2│    │  │ │P3│ │P4│    │  │ │P5│     │  │   │
│  │  │ └──┘ └──┘    │  │ └──┘ └──┘    │  │ └──┘     │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  P1-P5 = Pods (your containers)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Control Plane Components

| Component | What It Does |
|-----------|--------------|
| **API Server** | Front door to K8s. All commands go through it. |
| **etcd** | Database storing all cluster state |
| **Scheduler** | Decides which node runs each pod |
| **Controller Manager** | Ensures desired state matches actual state |

### Worker Node Components

| Component | What It Does |
|-----------|--------------|
| **kubelet** | Agent on each node, manages pods |
| **Container Runtime** | Actually runs containers (containerd) |
| **kube-proxy** | Handles networking for services |

---

## Core Concepts Preview

### Pods
The smallest deployable unit. Usually one container, sometimes multiple related containers.

```yaml
# You don't run containers directly—you create Pods
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
```

### Deployments
Manage multiple identical pods. Handle updates and scaling.

```yaml
# "I want 3 nginx pods, always"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
```

### Services
Stable networking for pods. Pods come and go; Services provide consistent access.

```yaml
# "Make my nginx pods accessible on port 80"
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
```

---

## Why Not Just Docker?

| Feature | Docker (single host) | Kubernetes |
|---------|---------------------|------------|
| Multi-node | ❌ | ✅ |
| Auto-scaling | ❌ | ✅ |
| Self-healing | ❌ | ✅ |
| Rolling updates | Manual | ✅ Automatic |
| Load balancing | Manual | ✅ Built-in |
| Service discovery | Manual | ✅ Built-in |
| Secrets management | ❌ | ✅ |
| Resource limits | Per container | Cluster-wide |

Docker is for running containers. Kubernetes is for operating containers at scale.

---

## Where Kubernetes Runs

### Cloud Managed (Easiest)
- **AWS**: EKS (Elastic Kubernetes Service)
- **Google Cloud**: GKE (Google Kubernetes Engine)
- **Azure**: AKS (Azure Kubernetes Service)

Cloud providers manage the control plane. You just run workloads.

### Self-Managed
- **kubeadm**: Official K8s installer
- **k3s**: Lightweight K8s (good for edge/IoT)
- **OpenShift**: Red Hat's enterprise K8s

You manage everything.

### Local Development
- **kind**: Kubernetes in Docker
- **minikube**: Local K8s VM/container
- **Docker Desktop**: Includes K8s option

For learning and development.

---

## Visualization: Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│              HOW A REQUEST FLOWS IN K8S                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User runs kubectl command                               │
│     ┌─────────────┐                                        │
│     │ kubectl     │──────────────────┐                     │
│     │ apply -f    │                  │                     │
│     │ deploy.yaml │                  ▼                     │
│     └─────────────┘          ┌──────────────┐              │
│                              │  API Server  │              │
│                              └──────┬───────┘              │
│                                     │                       │
│  2. API Server validates & stores   ▼                       │
│                              ┌──────────────┐              │
│                              │    etcd      │              │
│                              └──────┬───────┘              │
│                                     │                       │
│  3. Scheduler assigns pod to node   ▼                       │
│                              ┌──────────────┐              │
│                              │  Scheduler   │              │
│                              └──────┬───────┘              │
│                                     │                       │
│  4. Kubelet on node starts pod      ▼                       │
│                              ┌──────────────┐              │
│                              │   kubelet    │              │
│                              │  (on node)   │              │
│                              └──────┬───────┘              │
│                                     │                       │
│  5. Container runtime runs it       ▼                       │
│                              ┌──────────────┐              │
│                              │  containerd  │──► 🐳 Running│
│                              └──────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **"Kubernetes" is Greek for "helmsman"** (one who steers a ship). The logo is a ship's wheel with 7 spokes—for the 7 original developers.

- **K8s is a numeronym.** K-[8 letters]-s. Like i18n (internationalization) or a11y (accessibility).

- **Google runs everything on Kubernetes.** Gmail, Search, YouTube—all on Borg (K8s's predecessor) or K8s.

- **The largest known K8s cluster** has 15,000 nodes running 300,000+ pods (Alibaba).

---

## Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "K8s replaces Docker" | K8s orchestrates containers. You still use Docker to build images. |
| "K8s is only for huge companies" | Small startups use K8s too. Managed services make it accessible. |
| "K8s is complicated" | K8s IS complex, but managed services handle most complexity. |
| "K8s solves everything" | K8s is infrastructure. You still need to design good applications. |

---

## Quiz

1. **What problem does Kubernetes solve that Docker alone cannot?**
   <details>
   <summary>Answer</summary>
   Running containers across multiple machines with automatic scheduling, self-healing, scaling, load balancing, and zero-downtime updates. Docker alone only manages containers on a single host.
   </details>

2. **What is the relationship between a Pod and a Container?**
   <details>
   <summary>Answer</summary>
   A Pod is Kubernetes' smallest deployable unit, which contains one or more containers. You don't deploy containers directly—you create Pods. Containers in a Pod share network and storage.
   </details>

3. **What does the Kubernetes Scheduler do?**
   <details>
   <summary>Answer</summary>
   The Scheduler decides which worker node should run a new pod. It considers resource availability, constraints, affinity rules, and other factors to make optimal placement decisions.
   </details>

4. **Why would you use a managed Kubernetes service (EKS, GKE, AKS)?**
   <details>
   <summary>Answer</summary>
   Managed services handle the control plane (API server, etcd, scheduler, controllers). You don't need to worry about control plane availability, upgrades, or maintenance. You just run workloads.
   </details>

---

## Hands-On Exercise

**Task**: Explore a Kubernetes cluster (preview of what's coming).

```bash
# If you have a cluster running (kind, minikube, or other):

# 1. See your cluster nodes
kubectl get nodes
# Output shows the machines in your cluster

# 2. See running system components
kubectl get pods -n kube-system
# These are the components that make K8s work

# 3. See all namespaces (like folders for resources)
kubectl get namespaces

# 4. Create something simple
kubectl run hello --image=nginx --restart=Never
kubectl get pods
# You just created a Pod!

# 5. See what Kubernetes knows about it
kubectl describe pod hello
# Lots of information about scheduling, containers, events

# 6. Clean up
kubectl delete pod hello

# Don't worry if this is confusing now - you'll learn all of it
# The goal is just to see K8s in action
```

**No cluster yet?** That's OK! The Kubernetes Basics track will walk you through setting one up. This is just a preview.

**Success criteria**: See that Kubernetes provides an API to manage containers across machines.

---

## Summary

Kubernetes is a container orchestration platform that:

- **Schedules** containers across multiple machines
- **Self-heals** by restarting failed containers
- **Scales** based on demand
- **Load balances** traffic to containers
- **Updates** without downtime
- **Manages** networking and storage

Key concepts:
- **Cluster**: Control plane + worker nodes
- **Pod**: Smallest deployable unit
- **Deployment**: Manages replicated pods
- **Service**: Stable networking for pods

---

## Next Module

[Module 4: The Cloud Native Ecosystem](../module-1.4-cloud-native-ecosystem/) - Understanding the CNCF landscape and where Kubernetes fits.

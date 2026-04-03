---
title: "Module 1.3: Kubernetes Architecture - Control Plane"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.3-control-plane
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Core architecture concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Modules 1.1, 1.2

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the role of each control plane component: API server, etcd, scheduler, and controller manager
2. **Trace** how a pod creation request flows through the control plane components
3. **Identify** which component is responsible for a given cluster behavior or failure
4. **Compare** single control plane vs. high-availability control plane architectures

---

## Why This Module Matters

The control plane is the **brain of Kubernetes**. Understanding what each component does is essential for KCNA—expect multiple questions about control plane architecture.

---

## Kubernetes Cluster Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CLUSTER ARCHITECTURE                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              CONTROL PLANE (Master)                 │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │   │
│  │  │  API     │ │ Scheduler│ │Controller│           │   │
│  │  │ Server   │ │          │ │ Manager  │           │   │
│  │  └──────────┘ └──────────┘ └──────────┘           │   │
│  │         ┌──────────┐  ┌──────────┐                 │   │
│  │         │   etcd   │  │  Cloud   │                 │   │
│  │         │          │  │Controller│                 │   │
│  │         └──────────┘  └──────────┘                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          │ API calls                        │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   WORKER NODES                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   Node 1    │  │   Node 2    │  │   Node 3    │ │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │ │   │
│  │  │ │ kubelet │ │  │ │ kubelet │ │  │ │ kubelet │ │ │   │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │ │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │ │   │
│  │  │ │kube-proxy│ │  │ │kube-proxy│ │  │ │kube-proxy│ │ │   │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │ │   │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │ │   │
│  │  │ │Container│ │  │ │Container│ │  │ │Container│ │ │   │
│  │  │ │ Runtime │ │  │ │ Runtime │ │  │ │ Runtime │ │ │   │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Control Plane Components

### 1. kube-apiserver

The **API server** is the front door to Kubernetes:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-APISERVER                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Exposes the Kubernetes API (REST interface)             │
│  • All communication goes through it                       │
│  • Authenticates and authorizes requests                   │
│  • Validates API objects                                   │
│  • Only component that talks to etcd                       │
│                                                             │
│  Who talks to it:                                          │
│  ─────────────────────────────────────────────────────────  │
│  kubectl ────────→ ┌──────────────┐                       │
│  Dashboard ──────→ │ API Server   │ ←──── kubelet          │
│  Other tools ────→ └──────────────┘ ←──── Controllers      │
│                                                             │
│  Key point:                                                │
│  The API server is the ONLY component that reads/writes    │
│  to etcd. Everything else talks to the API server.        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. etcd

The **etcd** is the cluster's database:

```
┌─────────────────────────────────────────────────────────────┐
│              ETCD                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it is:                                               │
│  ─────────────────────────────────────────────────────────  │
│  • Distributed key-value store                             │
│  • Stores ALL cluster state                                │
│  • Highly available (usually 3 or 5 nodes)                 │
│  • Uses Raft consensus algorithm                           │
│                                                             │
│  What it stores:                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Pod definitions                                         │
│  • Service configurations                                  │
│  • Secrets and ConfigMaps                                  │
│  • Node information                                        │
│  • RBAC policies                                           │
│  • Everything in the cluster!                              │
│                                                             │
│  Key point:                                                │
│  If etcd is lost, the entire cluster state is lost.       │
│  Backup etcd regularly!                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. kube-scheduler

The **scheduler** places Pods on nodes:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-SCHEDULER                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Watches for newly created Pods with no node assigned    │
│  • Selects a node for each Pod to run on                  │
│  • Does NOT run the Pod (kubelet does)                    │
│                                                             │
│  How it decides:                                           │
│  ─────────────────────────────────────────────────────────  │
│  Filtering:                                                │
│  • Does node have enough resources?                        │
│  • Does node match Pod's node selector?                   │
│  • Does node satisfy affinity rules?                      │
│                                                             │
│  Scoring:                                                  │
│  • Spread Pods across nodes (balance)                     │
│  • Prefer nodes with image already cached                 │
│  • Consider custom priorities                              │
│                                                             │
│  New Pod → Scheduler → "Run on Node 2" → kubelet runs it  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. kube-controller-manager

The **controller manager** runs controllers:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-CONTROLLER-MANAGER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Runs controller processes                               │
│  • Each controller watches for specific resources          │
│  • Controllers make current state match desired state     │
│                                                             │
│  Important controllers:                                    │
│  ─────────────────────────────────────────────────────────  │
│  Node Controller:                                          │
│  • Monitors node health                                    │
│  • Responds when nodes go down                            │
│                                                             │
│  Replication Controller:                                   │
│  • Maintains correct number of Pods                       │
│  • Creates/deletes Pods as needed                         │
│                                                             │
│  Endpoints Controller:                                     │
│  • Populates Endpoints objects                            │
│  • Links Services to Pods                                 │
│                                                             │
│  ServiceAccount Controller:                                │
│  • Creates default ServiceAccounts                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. cloud-controller-manager

The **cloud controller manager** integrates with cloud providers:

```
┌─────────────────────────────────────────────────────────────┐
│              CLOUD-CONTROLLER-MANAGER                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Cloud-specific control logic                            │
│  • Only present in cloud environments                      │
│  • Separates cloud code from core K8s                     │
│                                                             │
│  Controllers it runs:                                      │
│  ─────────────────────────────────────────────────────────  │
│  Node Controller:                                          │
│  • Checks if node still exists in cloud                   │
│                                                             │
│  Route Controller:                                         │
│  • Sets up routes in cloud infrastructure                 │
│                                                             │
│  Service Controller:                                       │
│  • Creates cloud load balancers for Services              │
│                                                             │
│  Example:                                                  │
│  Service type: LoadBalancer → cloud-controller creates    │
│  an AWS ELB, GCP Load Balancer, or Azure LB              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Control Plane Communication

```
┌─────────────────────────────────────────────────────────────┐
│              HOW COMPONENTS COMMUNICATE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌──────────────┐                        │
│                    │   kubectl    │                        │
│                    └──────┬───────┘                        │
│                           │                                 │
│                           ▼                                 │
│                    ┌──────────────┐                        │
│  Controller ─────→ │  API Server  │ ←───── Scheduler       │
│  Manager           └──────┬───────┘                        │
│                           │                                 │
│                           ▼                                 │
│                    ┌──────────────┐                        │
│                    │     etcd     │                        │
│                    └──────────────┘                        │
│                                                             │
│  Flow example - Creating a Deployment:                    │
│                                                             │
│  1. kubectl creates Deployment via API Server             │
│  2. API Server stores it in etcd                          │
│  3. Deployment Controller sees new Deployment             │
│  4. Controller creates ReplicaSet                         │
│  5. ReplicaSet Controller creates Pods                    │
│  6. Scheduler sees unscheduled Pods                       │
│  7. Scheduler assigns Pods to nodes                       │
│  8. kubelet on node sees assignment, runs Pods           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## High Availability

In production, control plane components are replicated:

```
┌─────────────────────────────────────────────────────────────┐
│              HIGH AVAILABILITY SETUP                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Load Balancer                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│         ┌────────────────┼────────────────┐                │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Master 1   │  │ Master 2   │  │ Master 3   │           │
│  │            │  │            │  │            │           │
│  │ API Server │  │ API Server │  │ API Server │           │
│  │ Scheduler  │  │ Scheduler  │  │ Scheduler  │           │
│  │ Controller │  │ Controller │  │ Controller │           │
│  │ etcd       │  │ etcd       │  │ etcd       │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                                                             │
│  • Multiple API servers (all active)                       │
│  • Scheduler/Controller use leader election               │
│  • etcd requires quorum (odd number: 3, 5, 7)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **etcd means "/etc distributed"** - It's named after the Unix /etc directory where configuration is stored, plus "distributed."

- **Leader election prevents conflicts** - Only one scheduler and controller-manager is active at a time. Others are on standby.

- **API server is stateless** - It stores nothing locally. All state is in etcd. This makes scaling easy.

- **Controllers use a watch pattern** - They don't poll. They receive notifications when objects change, making them efficient.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "Scheduler runs Pods" | Missing kubelet's role | Scheduler assigns; kubelet runs |
| "etcd is optional" | Undervaluing cluster state | Without etcd, no cluster state |
| "API server stores data" | Confusing with etcd | API server is stateless gateway |
| "Controllers are optional" | Missing automation | Controllers make K8s self-healing |

---

## Quiz

1. **Which component is the only one that communicates directly with etcd?**
   <details>
   <summary>Answer</summary>
   kube-apiserver. All other components read and write cluster state through the API server.
   </details>

2. **What does the kube-scheduler do?**
   <details>
   <summary>Answer</summary>
   It watches for newly created Pods with no assigned node and selects a node for them to run on. It does NOT actually run the Pods.
   </details>

3. **What is etcd?**
   <details>
   <summary>Answer</summary>
   A distributed key-value store that holds all cluster state. It's the single source of truth for the Kubernetes cluster.
   </details>

4. **What does the controller manager do?**
   <details>
   <summary>Answer</summary>
   It runs controller processes that watch the cluster state and make changes to move current state toward desired state. Examples: Node Controller, ReplicaSet Controller.
   </details>

5. **Why do production clusters run multiple control plane nodes?**
   <details>
   <summary>Answer</summary>
   High availability. If one control plane node fails, others continue operating. etcd requires a quorum, so odd numbers (3, 5) are used.
   </details>

---

## Summary

**Control plane components**:

| Component | Purpose |
|-----------|---------|
| **kube-apiserver** | API gateway, authentication, validation |
| **etcd** | Distributed storage for all cluster state |
| **kube-scheduler** | Assigns Pods to nodes |
| **kube-controller-manager** | Runs controllers (reconciliation loops) |
| **cloud-controller-manager** | Cloud provider integration |

**Key points**:
- Only API server talks to etcd
- Scheduler decides WHERE; kubelet runs
- Controllers ensure desired state = current state
- HA requires multiple control plane nodes

---

## Next Module

[Module 1.4: Kubernetes Architecture - Node Components](../module-1.4-node-components/) - Understanding the workers that run your applications.

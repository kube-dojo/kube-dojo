---
title: "Module 1.4: Kubernetes Architecture - Node Components"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.4-node-components
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Core architecture concepts
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 1.3

---

## Why This Module Matters

While the control plane makes decisions, worker nodes do the actual work of running containers. Understanding node components completes your picture of Kubernetes architecture—a key KCNA topic.

---

## What is a Node?

A **node** is a worker machine in Kubernetes:

```
┌─────────────────────────────────────────────────────────────┐
│              WHAT IS A NODE?                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  A node can be:                                            │
│  • Physical server (bare metal)                            │
│  • Virtual machine (EC2, GCE VM, Azure VM)                │
│  • Cloud instance                                          │
│                                                             │
│  Every node runs:                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  kubelet      - Node agent                          │   │
│  │  kube-proxy   - Network proxy                       │   │
│  │  Container runtime - Runs containers                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Nodes register themselves with the control plane          │
│  Control plane assigns Pods to nodes                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Node Components

### 1. kubelet

The **kubelet** is the primary node agent:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBELET                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Runs on every node in the cluster                       │
│  • Watches for Pod assignments from API server             │
│  • Ensures containers are running and healthy              │
│  • Reports node and Pod status back to API server          │
│                                                             │
│  How it works:                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  API Server: "Node 2, run Pod X"                          │
│       │                                                     │
│       ▼                                                     │
│  kubelet:                                                  │
│  1. Receives Pod spec                                      │
│  2. Pulls container images                                 │
│  3. Creates containers via runtime                         │
│  4. Monitors container health                              │
│  5. Reports status to API server                          │
│                                                             │
│  Key point:                                                │
│  kubelet doesn't manage containers not created by K8s     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. kube-proxy

The **kube-proxy** handles networking:

```
┌─────────────────────────────────────────────────────────────┐
│              KUBE-PROXY                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Maintains network rules on nodes                        │
│  • Enables Service abstraction                             │
│  • Handles connection forwarding to Pods                   │
│                                                             │
│  How Services work:                                        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│       Client                                               │
│          │                                                  │
│          │ Request to Service IP                           │
│          ▼                                                  │
│    ┌───────────┐                                           │
│    │kube-proxy │ → Looks up which Pods back this Service   │
│    └───────────┘                                           │
│          │                                                  │
│          │ Forwards to Pod IP                              │
│          ▼                                                  │
│    ┌───────────┐                                           │
│    │   Pod     │                                           │
│    └───────────┘                                           │
│                                                             │
│  Modes:                                                    │
│  • iptables (default) - Uses iptables rules               │
│  • IPVS - Higher performance for large clusters           │
│  • userspace - Legacy, rarely used                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Container Runtime

The **container runtime** actually runs containers:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER RUNTIME                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Pulls images from registries                            │
│  • Creates and starts containers                           │
│  • Manages container lifecycle                             │
│                                                             │
│  Kubernetes uses CRI (Container Runtime Interface):        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│       kubelet                                              │
│          │                                                  │
│          │ CRI (gRPC)                                      │
│          ▼                                                  │
│    ┌─────────────────────────────────────────────────┐     │
│    │  containerd  │  CRI-O  │  Other CRI runtime    │     │
│    └─────────────────────────────────────────────────┘     │
│          │                                                  │
│          │ OCI (Open Container Initiative)                 │
│          ▼                                                  │
│    ┌───────────────┐                                       │
│    │  runc / kata  │  (low-level runtime)                 │
│    └───────────────┘                                       │
│                                                             │
│  Common runtimes:                                          │
│  • containerd - Default in most distributions              │
│  • CRI-O - Lightweight, Kubernetes-focused                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Node Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│              NODE LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Node Joins Cluster                                     │
│     • kubelet starts and registers with API server         │
│     • Node appears in "kubectl get nodes"                  │
│                                                             │
│  2. Node Ready                                             │
│     • Passes health checks                                 │
│     • Scheduler can place Pods on it                       │
│     Status: Ready                                          │
│                                                             │
│  3. Node Running                                           │
│     • Runs assigned Pods                                   │
│     • kubelet reports status periodically                  │
│                                                             │
│  4. Node Issues                                            │
│     • Misses heartbeats → Status: Unknown                 │
│     • Low resources → Status: NotReady                    │
│                                                             │
│  5. Node Removed                                           │
│     • Drained (Pods moved elsewhere)                      │
│     • Deleted from cluster                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Node Conditions

| Condition | Meaning |
|-----------|---------|
| **Ready** | Node is healthy and can accept Pods |
| **DiskPressure** | Disk capacity is low |
| **MemoryPressure** | Memory is running low |
| **PIDPressure** | Too many processes |
| **NetworkUnavailable** | Network not configured |

---

## How Pods Get Scheduled and Run

```
┌─────────────────────────────────────────────────────────────┐
│              POD SCHEDULING AND EXECUTION                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User creates Pod                                       │
│     kubectl apply -f pod.yaml                              │
│            │                                                │
│            ▼                                                │
│  2. API Server stores Pod                                  │
│     Pod stored in etcd (no node assigned yet)             │
│            │                                                │
│            ▼                                                │
│  3. Scheduler watches, sees unscheduled Pod               │
│     Evaluates nodes, picks best one                       │
│     Updates Pod with node assignment                       │
│            │                                                │
│            ▼                                                │
│  4. kubelet on target node sees assignment                │
│     "I need to run this Pod"                              │
│            │                                                │
│            ▼                                                │
│  5. kubelet instructs container runtime                   │
│     Pull image, create container, start it                │
│            │                                                │
│            ▼                                                │
│  6. Container runs                                         │
│     kubelet monitors health                               │
│     Reports status to API server                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Node vs Control Plane Summary

```
┌─────────────────────────────────────────────────────────────┐
│              CONTROL PLANE vs NODE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTROL PLANE (Brain)          NODE (Muscle)              │
│  ──────────────────────────────────────────────────────    │
│                                                             │
│  Makes decisions                Executes decisions         │
│  Stores cluster state           Runs workloads             │
│  Schedules Pods                 Runs Pods                  │
│  Usually 3+ for HA             Many (10s to 1000s)        │
│                                                             │
│  Components:                    Components:                 │
│  • API Server                   • kubelet                  │
│  • etcd                         • kube-proxy               │
│  • Scheduler                    • Container runtime        │
│  • Controller Manager                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **kubelet doesn't run as a container** - It's a system service that runs directly on the node OS. It needs to manage containers, so it can't be one.

- **kube-proxy is being replaced** - Newer CNI plugins (like Cilium) can handle Service routing without kube-proxy, using eBPF.

- **Nodes can have taints** - Taints prevent certain Pods from running on a node. Pods need matching tolerations to schedule there.

- **The pause container** - Every Pod has a hidden "pause" container that holds the network namespace. Other containers in the Pod share it.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| "kubelet is on control plane" | Confusing location | kubelet is on EVERY node, including workers |
| "kube-proxy is a proxy server" | Misleading name | It maintains iptables rules, not a traditional proxy |
| "Container runtime is Docker" | Outdated | containerd is now the default |
| "Nodes are always VMs" | Missing flexibility | Nodes can be bare metal, VMs, or cloud instances |

---

## Quiz

1. **What is the primary function of kubelet?**
   <details>
   <summary>Answer</summary>
   kubelet is the node agent that ensures containers are running in Pods. It watches for Pod assignments and works with the container runtime to create/manage containers.
   </details>

2. **What does kube-proxy do?**
   <details>
   <summary>Answer</summary>
   kube-proxy maintains network rules on nodes that enable the Service abstraction. It forwards traffic destined for Service IPs to the appropriate Pod IPs.
   </details>

3. **What is CRI?**
   <details>
   <summary>Answer</summary>
   Container Runtime Interface - the standard API that kubelet uses to communicate with container runtimes like containerd and CRI-O.
   </details>

4. **Which components run on EVERY node?**
   <details>
   <summary>Answer</summary>
   kubelet, kube-proxy, and a container runtime (like containerd). These three are required on every node.
   </details>

5. **What happens when a node misses heartbeats?**
   <details>
   <summary>Answer</summary>
   The node's status changes to Unknown. If it remains unreachable, the Node Controller marks it NotReady and Pods may be rescheduled to healthy nodes.
   </details>

---

## Summary

**Node components**:

| Component | Purpose |
|-----------|---------|
| **kubelet** | Node agent, manages Pods and containers |
| **kube-proxy** | Network rules for Service routing |
| **Container runtime** | Actually runs containers (containerd) |

**Key points**:
- Every node needs all three components
- kubelet is the only component talking to API server
- kube-proxy enables Service discovery
- Container runtime uses CRI to talk to kubelet

**Pod execution flow**:
1. API server stores Pod
2. Scheduler assigns node
3. kubelet sees assignment
4. Container runtime runs containers
5. kubelet monitors and reports

---

## Next Module

[Module 1.5: Pods](../module-1.5-pods/) - The fundamental building block of Kubernetes workloads.

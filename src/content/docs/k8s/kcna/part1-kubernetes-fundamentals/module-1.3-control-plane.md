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

The **API server** acts as the front door to the Kubernetes cluster. It is the central management entity that receives all REST requests, validates them, and updates the state in etcd:

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

The **etcd** component serves as the highly available, consistent, and distributed database for your cluster:

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

> **Pause and predict**: The API server is the only component that directly talks to etcd. Why do you think the architecture was designed this way, instead of letting all components read and write to etcd independently?

### 3. kube-scheduler

The **kube-scheduler** acts as the cluster's decision-maker for workload placement, determining exactly which node should host each newly created Pod:

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

The **kube-controller-manager** operates as the cluster's continuous background reconciliation engine, running various controllers that work to match the current state to the desired state:

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

The **cloud-controller-manager** bridges the gap between your Kubernetes cluster and the underlying cloud provider's APIs (like AWS, GCP, or Azure):

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

> **Stop and think**: If the scheduler is responsible for assigning Pods to nodes but does not actually run them, what component does? Trace the complete path: a user creates a Deployment—what exact sequence of components is involved before a container is actively running on a worker node?

## High Availability

In production environments, control plane components are heavily replicated to prevent a single point of failure:

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

> **Pause and predict**: Notice that etcd clusters usually run with an odd number of nodes (3, 5, or 7). Based on how distributed consensus algorithms work, what specific failure scenario does having an odd number of nodes prevent compared to an even number?

---

## Did You Know?

- **etcd means "/etc distributed"** - It's named after the Unix /etc directory where configuration is stored, plus "distributed."

- **Leader election prevents conflicts** - Only one scheduler and controller-manager is active at a time. Others are on standby.

- **API server is stateless** - It stores nothing locally. All state is in etcd. This makes scaling easy.

- **Controllers use a watch pattern** - They don't poll. They receive notifications when objects change, making them incredibly efficient compared to continuous polling.

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

1. **Your team is investigating a catastrophic failure where the cluster's etcd database became corrupted and all data was lost. Unfortunately, no backups exist. What exactly happens to the cluster's operations, and which specific resources are affected?**
   <details>
   <summary>Answer</summary>
   Because etcd serves as the single source of truth for all Kubernetes objects, the entire cluster state is lost permanently. Every Pod definition, Service configuration, Secret, ConfigMap, RBAC policy, and node registration is wiped out. Interestingly, running containers will continue to execute because the kubelet on each node keeps them alive locally based on its last known state. However, the control plane cannot manage them anymore, meaning no new scheduling, no self-healing, and no scaling can occur. This catastrophic scenario highlights exactly why regular etcd backups are a critical production requirement, as you must otherwise rebuild the entire cluster configuration from scratch.
   </details>

2. **An intern is reviewing the cluster architecture and asks: "If the API server goes down, does everything stop running?" How would you explain the impact on existing workloads versus the impact on new cluster operations?**
   <details>
   <summary>Answer</summary>
   You should explain that existing workloads will continue running normally because the kubelet on each node independently manages its assigned containers. The pods that are already scheduled and running will keep serving traffic without interruption. However, the cluster becomes entirely "frozen" regarding any new operations or changes. No new pods can be created, no scaling events can occur, no scheduling decisions can be made, and all `kubectl` commands will fail. This split behavior perfectly illustrates why production clusters run multiple API server instances behind a load balancer to maintain high availability for cluster management.
   </details>

3. **During a system design discussion, a colleague claims that the `kube-scheduler` both decides where Pods should run and is responsible for actually starting them on the target node. Is this understanding correct? If not, what is the actual mechanism that gets a container running after the scheduler makes its decision?**
   <details>
   <summary>Answer</summary>
   Your colleague's understanding is incorrect, as the scheduler only makes the placement decision and writes the node assignment to the Pod object via the API server. It is actually the `kubelet` on the assigned node that watches the API server, notices a new Pod has been assigned to its node, and takes action. The `kubelet` then instructs the local container runtime (such as containerd) to pull the necessary image and start the container. This strict separation of concerns is a deliberate architectural design choice. It allows the scheduler to focus entirely on optimal placement algorithms while the `kubelet` focuses exclusively on local container lifecycle management.
   </details>

4. **Your production cluster runs three control plane nodes, each hosting an etcd member. During a routine update, one node experiences a severe hardware failure. Can the cluster still function normally, and what would happen to the cluster's state if a second node were to fail simultaneously?**
   <details>
   <summary>Answer</summary>
   With one node down, leaving two out of three nodes operational, the cluster will continue functioning normally. This is because etcd relies on the Raft consensus algorithm, which requires a quorum of strictly more than half the members to operate. With three members, the required quorum is two, making the loss of a single node perfectly safe. However, if a second node fails, leaving only one operational node, the cluster loses its quorum and etcd immediately becomes read-only to prevent split-brain scenarios. In this state, no new writes can be processed, meaning no new pods can be deployed, scaling stops, and configuration changes are impossible until quorum is restored.
   </details>

5. **You execute a command to create a new Deployment with 3 replicas. Walk through the exact chain of control plane components involved, step-by-step, from the moment you hit enter until the requested pods are actually running on the worker nodes.**
   <details>
   <summary>Answer</summary>
   The sequence begins when `kubectl` sends the Deployment object to the API server, which validates the request and stores the new desired state in etcd. Next, the Deployment controller detects this new Deployment and creates a corresponding ReplicaSet, which in turn causes the ReplicaSet controller to create three individual Pod objects. At this point, the `kube-scheduler` detects three unscheduled Pods, evaluates the available nodes, and assigns each Pod to an optimal node by updating the API server. Finally, the `kubelet` on each assigned node sees the new Pod assignment, pulls the container image using the local container runtime, and starts the containers. Throughout this entire process, each component operates independently by watching the API server for changes and reacting only to its specific responsibilities.
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
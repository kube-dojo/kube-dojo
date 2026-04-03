---
title: "Module 1.6: Workload Resources"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.6-workload-resources
sidebar:
  order: 7
---
> **Complexity**: `[MEDIUM]` - Core resource concepts
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Module 1.5 (Pods)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Compare** Deployments, ReplicaSets, DaemonSets, StatefulSets, and Jobs by use case
2. **Identify** which workload resource to use for a given application scenario
3. **Explain** how Deployments manage rolling updates and rollbacks through ReplicaSets
4. **Evaluate** the relationship between controllers and the Pods they manage

---

## Why This Module Matters

You rarely create Pods directly—you use **workload resources** that manage Pods for you. Understanding Deployments, ReplicaSets, DaemonSets, and other controllers is essential for KCNA.

---

## The Workload Resource Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│              WORKLOAD RESOURCE HIERARCHY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  You create:         Deployment                            │
│                           │                                 │
│                           │ creates & manages               │
│                           ▼                                 │
│  Auto-created:       ReplicaSet                            │
│                           │                                 │
│                           │ creates & manages               │
│                           ▼                                 │
│  Auto-created:    Pod    Pod    Pod                        │
│                                                             │
│  Why this hierarchy?                                       │
│  ─────────────────────────────────────────────────────────  │
│  • Deployment: Handles updates and rollbacks               │
│  • ReplicaSet: Maintains desired number of Pods            │
│  • Pod: Runs the actual containers                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployments

The **Deployment** is the most common way to run applications:

```
┌─────────────────────────────────────────────────────────────┐
│              DEPLOYMENT                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Declaratively manages ReplicaSets and Pods              │
│  • Provides rolling updates                                 │
│  • Supports rollbacks                                       │
│  • Scales applications up/down                             │
│                                                             │
│  Example:                                                  │
│  ─────────────────────────────────────────────────────────  │
│  "I want 3 replicas of nginx:1.25"                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Deployment: nginx                                   │   │
│  │  replicas: 3                                         │   │
│  │  image: nginx:1.25                                   │   │
│  │                                                      │   │
│  │  └─→ ReplicaSet: nginx-7b8d6c                       │   │
│  │       │                                              │   │
│  │       ├─→ Pod: nginx-7b8d6c-abc12                   │   │
│  │       ├─→ Pod: nginx-7b8d6c-def34                   │   │
│  │       └─→ Pod: nginx-7b8d6c-ghi56                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  When to use: Stateless applications                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Rolling Updates

```
┌─────────────────────────────────────────────────────────────┐
│              ROLLING UPDATE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Update from nginx:1.25 to nginx:1.26:                    │
│                                                             │
│  Step 1: Create new ReplicaSet                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Old RS (nginx:1.25): ●●●  (3 pods)                 │   │
│  │  New RS (nginx:1.26): ○    (1 pod starting)         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Step 2: Scale new up, old down                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Old RS (nginx:1.25): ●●   (2 pods)                 │   │
│  │  New RS (nginx:1.26): ○○   (2 pods)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Step 3: Complete                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Old RS (nginx:1.25):      (0 pods, kept for rollback)│  │
│  │  New RS (nginx:1.26): ○○○  (3 pods)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Benefits:                                                 │
│  • Zero downtime                                           │
│  • Gradual rollout                                         │
│  • Automatic rollback on failure                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ReplicaSets

A **ReplicaSet** maintains a stable set of replica Pods:

```
┌─────────────────────────────────────────────────────────────┐
│              REPLICASET                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Ensures specified number of Pods are running            │
│  • Creates new Pods if too few                             │
│  • Deletes Pods if too many                                │
│  • Uses labels to identify Pods it owns                    │
│                                                             │
│  Example:                                                  │
│  ─────────────────────────────────────────────────────────  │
│  ReplicaSet wants: 3 pods                                  │
│  Currently: 2 pods                                         │
│  Action: Create 1 more pod                                 │
│                                                             │
│  ReplicaSet wants: 3 pods                                  │
│  Currently: 4 pods                                         │
│  Action: Delete 1 pod                                      │
│                                                             │
│  Important:                                                │
│  ─────────────────────────────────────────────────────────  │
│  You rarely create ReplicaSets directly!                  │
│  Use Deployments—they manage ReplicaSets for you.         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## StatefulSets

For **stateful applications** that need stable identities:

```
┌─────────────────────────────────────────────────────────────┐
│              STATEFULSET                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it provides:                                         │
│  ─────────────────────────────────────────────────────────  │
│  • Stable, unique network identifiers                      │
│  • Stable, persistent storage                              │
│  • Ordered, graceful deployment and scaling                │
│  • Ordered, graceful deletion and termination              │
│                                                             │
│  Example: Database cluster                                 │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  StatefulSet: mysql                                  │   │
│  │                                                      │   │
│  │  mysql-0  ──→ PVC: mysql-data-0  (10GB)            │   │
│  │  mysql-1  ──→ PVC: mysql-data-1  (10GB)            │   │
│  │  mysql-2  ──→ PVC: mysql-data-2  (10GB)            │   │
│  │                                                      │   │
│  │  DNS: mysql-0.mysql.default.svc.cluster.local      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Key differences from Deployment:                          │
│  • Pods get persistent names (mysql-0, mysql-1)           │
│  • Each Pod gets its own PVC                               │
│  • Created in order (0, then 1, then 2)                   │
│                                                             │
│  When to use: Databases, clustered apps, ordered startup  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## DaemonSets

For running a Pod on **every node**:

```
┌─────────────────────────────────────────────────────────────┐
│              DAEMONSET                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • Runs one Pod per node                                   │
│  • Automatically adds Pod when new node joins              │
│  • Removes Pod when node leaves                            │
│                                                             │
│  Example: Log collector                                    │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Node 1  │  │ Node 2  │  │ Node 3  │  │ Node 4  │      │
│  │┌───────┐│  │┌───────┐│  │┌───────┐│  │┌───────┐│      │
│  ││fluent-││  ││fluent-││  ││fluent-││  ││fluent-││      │
│  ││  bit  ││  ││  bit  ││  ││  bit  ││  ││  bit  ││      │
│  │└───────┘│  │└───────┘│  │└───────┘│  │└───────┘│      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
│                                                             │
│  Common use cases:                                         │
│  • Log collectors (Fluentd, Fluent Bit)                   │
│  • Monitoring agents (Prometheus Node Exporter)           │
│  • Network plugins (CNI)                                   │
│  • Storage drivers                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Jobs and CronJobs

For **batch and scheduled workloads**:

```
┌─────────────────────────────────────────────────────────────┐
│              JOB                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  • Creates Pods that run to completion                     │
│  • Retries if Pod fails                                    │
│  • Tracks successful completions                           │
│                                                             │
│  Example: Database backup                                  │
│  Job "backup" → Creates Pod → Pod runs backup → Completes │
│                                                             │
│  Options:                                                  │
│  • completions: 5  (run 5 times total)                    │
│  • parallelism: 2  (run 2 at a time)                      │
│  • backoffLimit: 3 (retry 3 times on failure)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              CRONJOB                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What it does:                                             │
│  • Creates Jobs on a schedule                              │
│  • Uses cron syntax                                        │
│                                                             │
│  Example: Nightly backup                                   │
│  schedule: "0 2 * * *"  # Every day at 2 AM              │
│                                                             │
│  ┌──────┐    ┌──────┐    ┌──────┐                        │
│  │ Day 1│    │ Day 2│    │ Day 3│                        │
│  │ 2 AM │    │ 2 AM │    │ 2 AM │                        │
│  │  ↓   │    │  ↓   │    │  ↓   │                        │
│  │ Job  │    │ Job  │    │ Job  │                        │
│  └──────┘    └──────┘    └──────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Workload Resource Comparison

| Resource | Purpose | Pod Identity | Replicas |
|----------|---------|--------------|----------|
| **Deployment** | Stateless apps | Random names | Variable |
| **ReplicaSet** | Maintain count | Random names | Fixed |
| **StatefulSet** | Stateful apps | Stable names | Ordered |
| **DaemonSet** | Per-node agent | Per node | One per node |
| **Job** | Run to completion | Temporary | Until done |
| **CronJob** | Scheduled Jobs | Temporary | Per schedule |

---

## When to Use What?

```
┌─────────────────────────────────────────────────────────────┐
│              CHOOSING A WORKLOAD RESOURCE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Is it a one-time task?                                    │
│  └─→ YES: Job                                              │
│                                                             │
│  Does it need to run on a schedule?                        │
│  └─→ YES: CronJob                                          │
│                                                             │
│  Does it need to run on every node?                        │
│  └─→ YES: DaemonSet                                        │
│                                                             │
│  Does it need stable identity and storage?                 │
│  └─→ YES: StatefulSet                                      │
│                                                             │
│  Is it a stateless application?                            │
│  └─→ YES: Deployment (most common!)                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Deployments keep old ReplicaSets** - By default, Kubernetes keeps 10 old ReplicaSets to enable rollback. This is configurable.

- **StatefulSet Pods are created sequentially** - Pod-0 must be running before Pod-1 is created. This ensures ordered startup.

- **DaemonSets bypass the scheduler** - Originally, DaemonSets placed Pods directly. Now they use the scheduler by default.

- **CronJob time zone is controller-manager's time** - Be careful about time zones when scheduling CronJobs.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Creating ReplicaSets directly | Lose update features | Use Deployments |
| Using Deployment for databases | Lose data on reschedule | Use StatefulSet |
| Manual scaling | No automation | Use HPA or set replicas |
| Ignoring Job failures | Silent errors | Check completions and status |

---

## Quiz

1. **What workload resource manages ReplicaSets?**
   <details>
   <summary>Answer</summary>
   Deployment. When you create a Deployment, it creates and manages ReplicaSets, which in turn create and manage Pods.
   </details>

2. **What makes StatefulSet different from Deployment?**
   <details>
   <summary>Answer</summary>
   StatefulSet provides stable, persistent identity (Pod names like mysql-0), stable storage (each Pod gets its own PVC), and ordered deployment/scaling. Deployment Pods have random names and share storage.
   </details>

3. **When would you use a DaemonSet?**
   <details>
   <summary>Answer</summary>
   When you need exactly one Pod running on every node (or a subset of nodes). Common uses: log collectors, monitoring agents, network plugins.
   </details>

4. **What's the difference between Job and Deployment?**
   <details>
   <summary>Answer</summary>
   A Job runs Pods to completion (finite tasks like backups). A Deployment runs Pods continuously (long-running services). Jobs end; Deployments keep running.
   </details>

5. **What does a ReplicaSet do?**
   <details>
   <summary>Answer</summary>
   A ReplicaSet ensures that a specified number of identical Pods are running at all times. If Pods die, it creates new ones. If there are too many, it removes some.
   </details>

---

## Summary

**Workload resources manage Pods**:

| Resource | Use Case |
|----------|----------|
| **Deployment** | Stateless apps (web servers, APIs) |
| **StatefulSet** | Stateful apps (databases, caches) |
| **DaemonSet** | Per-node agents (logging, monitoring) |
| **Job** | One-time tasks (backups, migrations) |
| **CronJob** | Scheduled tasks (nightly jobs) |

**Key hierarchy**:
- Deployment → ReplicaSet → Pods
- You create Deployment
- K8s creates the rest

**Best practice**: Almost never create Pods or ReplicaSets directly. Use higher-level resources.

---

## Next Module

[Module 1.7: Services](../module-1.7-services/) - How Pods are exposed and discovered within and outside the cluster.

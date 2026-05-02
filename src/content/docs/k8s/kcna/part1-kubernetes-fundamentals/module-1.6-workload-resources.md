---
revision_pending: false
title: "Module 1.6: Workload Resources"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.6-workload-resources
sidebar:
  order: 7
---

# Module 1.6: Workload Resources

> **Complexity**: `[MEDIUM]` - Core resource concepts
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Module 1.5 (Pods)
>
> **Context**: This module assumes you can read a Pod manifest and now need to choose the controller that should own those Pods in a real cluster.

## Learning Outcomes

After completing this module, you will be able to make workload choices from observable requirements rather than from memorized resource names:

1. **Compare** Kubernetes workload controllers by Pod identity, lifecycle, scheduling scope, and update behavior.
2. **Design** an appropriate workload resource choice for stateless services, stateful systems, per-node agents, one-time Jobs, and CronJobs.
3. **Diagnose** Deployment rollout behavior by tracing how Deployments, ReplicaSets, and Pods share ownership during scaling, updates, and rollback.
4. **Implement** basic Kubernetes 1.35+ workload resources with `k` commands, labels, selectors, and status checks.

## Why This Module Matters

At 09:18 on a busy retail morning, an operations team rolled a payment API from one container image to another and expected Kubernetes to keep the service steady. They had tested the new image, but they had deployed it as a bare Pod because that seemed simpler during the previous sprint. When the node hosting that Pod was drained for an urgent kernel patch, the application disappeared until a human noticed failed checkouts, recreated the Pod by hand, and restored the Service endpoint. The incident report estimated more than $120,000 in abandoned carts, yet the root cause was not a broken container or a mysterious platform failure. The team had chosen the wrong workload resource for the job.

Another team in the same company made the opposite mistake a week later. They placed a clustered database into a Deployment because Deployments were familiar, then watched one replacement Pod come back with a new name and a different volume claim than the database member expected. Replication lag grew while the application retried writes, and the engineers spent the afternoon separating storage identity from stateless rollout thinking. Their problem was not that Deployments are bad; their problem was that Deployments solve a different class of problem than StatefulSets, Jobs, CronJobs, and DaemonSets.

This module teaches the decision skill behind those incidents. Kubernetes gives you controllers that watch desired state and reconcile Pods toward that state, but each controller carries a different promise about identity, lifetime, scheduling, update behavior, and recovery. KCNA expects you to recognize those promises, and production work expects you to apply them before you write YAML. By the end, you should be able to look at an application requirement and decide whether it wants a Deployment, ReplicaSet, StatefulSet, DaemonSet, Job, or CronJob, then verify that the controller is doing the work you intended.

## Controllers Turn Pods Into Managed Workloads

A Pod is the smallest runnable unit in Kubernetes, but a Pod alone is closer to a single process than to an application management strategy. If that Pod exits, moves, or needs a new image, a higher-level controller must decide what should happen next. Workload resources are those higher-level controllers. They hold the desired state, compare it to the current cluster state, and take action until the two match closely enough for the controller's rules.

The key mental model is reconciliation. You declare that you want three web Pods, one log collector on each node, a database member named `mysql-0`, or a migration that completes once. Kubernetes controllers continually ask, "What exists now, what should exist, and what change moves reality closer to the request?" That loop is why deleting a Pod created by a Deployment usually results in a replacement, while deleting a completed Job Pod does not mean the Job should run forever.

The original hierarchy diagram is worth keeping because it shows the most common controller chain you will meet first. A Deployment is not a more decorative Pod file. It manages ReplicaSets, and those ReplicaSets manage Pods. This extra layer gives Kubernetes a place to represent old and new versions during a rollout, which is why a Deployment can undo a bad release without asking you to remember every previous Pod template by hand.

```text
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

Controllers also use labels and selectors as their ownership language. A ReplicaSet does not own every Pod that happens to run the same image; it owns Pods matching its selector, and it creates Pods from its template when matching Pods are missing. This detail matters because selector mistakes can create orphaned Pods, unexpected adoption, or two controllers fighting over the same application shape. Labels look small, but they are the glue between controller intent and Pod reality.

Think of a workload controller like a kitchen expeditor rather than a cook. The Pod cooks the food by running containers, while the controller watches the order board and keeps the kitchen staffed for the current demand. A Deployment expeditor cares about steady service and controlled replacements. A Job expeditor cares that a finite task finishes. A DaemonSet expeditor cares that every station has exactly the agent it needs.

Pause and predict: if a Deployment wants three replicas and you manually delete one of its Pods, what object notices the missing Pod first, and why does the Deployment not need you to run a second command? Your answer should mention the selector and the desired replica count, because those are the facts the controller can observe.

KCNA questions often phrase this as a resource choice, but real operations phrase it as a consequence. Will a replacement Pod keep the same name? Will the controller create a Pod on a new node automatically? Does successful completion stop the workload, or does the platform treat exit as failure and restart it? Those questions are more reliable than memorizing a list because they map directly to the promises each workload resource makes.

The table below previews the decision surface. Do not treat it as a substitute for the rest of the module; treat it as a compact map you will revisit after seeing how each controller behaves under change. The most useful column is Pod identity, because identity often reveals whether you are managing replaceable application workers or named members of a coordinated system.

| Resource | Purpose | Pod Identity | Replicas |
|----------|---------|--------------|----------|
| **Deployment** | Stateless apps | Random names | Variable |
| **ReplicaSet** | Maintain count | Random names | Fixed |
| **StatefulSet** | Stateful apps | Stable names | Ordered |
| **DaemonSet** | Per-node agent | Per node | One per node |
| **Job** | Run to completion | Temporary | Until done |
| **CronJob** | Scheduled Jobs | Temporary | Per schedule |

## Deployments and ReplicaSets Manage Stateless Change

The Deployment is the everyday workload resource for stateless applications such as web servers, API services, background workers that can be replaced freely, and small internal tools that store durable data somewhere else. "Stateless" does not mean the application has no data at all. It means any single Pod can disappear and be replaced without losing unique local state required for correctness, because durable state is held in a database, queue, object store, or another service designed for persistence.

Deployments exist because production applications change. You scale them, roll out new images, undo bad versions, and inspect status while traffic is still flowing. A bare Pod cannot provide that release history, and a direct ReplicaSet can maintain a replica count but does not give you the same rollout interface. A Deployment owns the rollout strategy, creates ReplicaSets for versions of the Pod template, and uses those ReplicaSets to move capacity from old to new without dropping the desired service shape all at once.

The preserved Deployment diagram gives the practical picture. You say, "I want three replicas of this template," and Kubernetes creates lower-level objects to make that true. The generated Pod names are not contractual identities; they are implementation details. If one Pod dies, a replacement with a different suffix is acceptable because every replica is supposed to be equivalent from the application's point of view.

```text
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

The rollout diagram shows why the middle layer matters. During an image update, the Deployment does not mutate the old ReplicaSet in place. It creates a new ReplicaSet for the new Pod template, then scales the old and new ReplicaSets according to the rollout strategy. That gives Kubernetes two visible versions to compare, pause, scale, and roll back, instead of a single blurred object whose history has already been overwritten.

```text
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

The word "automatic" in rollout discussions deserves care. Kubernetes automatically reconciles toward the rollout you declared, and it can stop considering a rollout healthy when progress deadlines are exceeded, but it does not magically know your business metric or database compatibility rule. A Deployment can tell you that new Pods are not becoming available, and `k rollout undo` can move back to an earlier ReplicaSet, but you still need readiness probes, monitoring, and release discipline to decide when rollback is the right operational action.

ReplicaSets are the counting mechanism underneath Deployments. A ReplicaSet's core responsibility is simple: ensure a specified number of matching Pods exist. If too few Pods match the selector, it creates more from the template. If too many Pods match, it deletes extras. That behavior is powerful, but it is intentionally narrower than a Deployment's release management behavior, which is why most application teams should not create ReplicaSets directly.

```text
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

A useful worked example starts with a tiny Deployment. The manifest below targets Kubernetes 1.35+ and uses labels that connect the Deployment selector to the Pod template. The `app: quote-api` label is not decoration; it is the contract that tells the controller which Pods count toward the desired replica total. If the selector and template labels do not match, the API server rejects the Deployment because the controller could never safely manage its own Pods.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quote-api
  labels:
    app: quote-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: quote-api
  template:
    metadata:
      labels:
        app: quote-api
    spec:
      containers:
        - name: quote-api
          image: nginx:1.26
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 3
            periodSeconds: 5
```

Throughout the hands-on commands in this module, `k` means the kubectl command-line tool. If your shell does not already define that shortcut, run the alias once in your current terminal session before using commands such as `k get deploy`, `k describe rs`, and `k rollout status`.

```bash
alias k=kubectl
```

Before running this, what output do you expect from `k get deploy,rs,pod -l app=quote-api` after the Deployment is applied? The important prediction is not the exact generated suffix. The important prediction is that you should see one Deployment, one active ReplicaSet for the current template, and three Pods whose names include the ReplicaSet hash because the ReplicaSet created them.

The ownership chain becomes visible with normal inspection commands. `k get deployment quote-api -o wide` tells you desired, updated, ready, and available replica counts. `k get rs -l app=quote-api` shows the ReplicaSet that satisfies the current template. `k describe deployment quote-api` shows rollout events and conditions, which are often the fastest way to notice an image pull problem, a readiness probe failure, or a rollout that is not making progress.

```bash
k apply -f quote-api-deployment.yaml
k get deploy,rs,pod -l app=quote-api
k describe deployment quote-api
k rollout status deployment/quote-api
```

When the image changes, the Deployment creates a new ReplicaSet because the Pod template changed. Scaling replicas from three to five, by contrast, changes desired capacity without necessarily creating a new ReplicaSet because the template can remain the same. This distinction helps with troubleshooting: a new ReplicaSet suggests a template revision, while a changed replica count suggests scaling pressure or a manual capacity adjustment.

```bash
k set image deployment/quote-api quote-api=nginx:1.27
k rollout status deployment/quote-api
k get rs -l app=quote-api
k rollout history deployment/quote-api
```

A real operations war story illustrates the difference. A team once thought a rollout had failed because old ReplicaSets were still visible after a successful release. They deleted the old ReplicaSets to "clean up," then discovered they had removed the easiest rollback path minutes before a client-side regression appeared. The old ReplicaSet with zero replicas was not clutter; it was revision history represented as a Kubernetes object.

Deployments are the correct default for replaceable application replicas, but they are not a universal answer. If the Pod name becomes part of cluster membership, if each replica needs a unique persistent volume, if a task should stop after success, or if one Pod must run on every node, a Deployment's strengths become mismatches. Good Kubernetes design starts by asking what promise the workload needs before choosing the familiar resource.

## StatefulSets Preserve Identity and Storage

StatefulSets serve applications where each replica has a durable identity. A database member, message broker node, or clustered coordination process may need a stable hostname, an ordinal number, and storage that remains associated with that member across rescheduling. A Deployment can recreate capacity, but it treats replicas as interchangeable. A StatefulSet says that `mysql-0` is not merely "some database Pod"; it is a named member with identity that other members can recognize.

The preserved StatefulSet diagram captures those guarantees. The names are predictable, the volume claims are tied to the ordinal identity, and startup or shutdown can be ordered. That order is not ceremonial. Many stateful systems need a primary to initialize before followers join, or need graceful termination so a member can leave a quorum without corrupting replication assumptions.

```text
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

StatefulSet identity has two main parts: ordinal naming and stable network identity. Pods are named from zero upward, such as `mysql-0`, `mysql-1`, and `mysql-2`. With a headless Service, each Pod can also receive a stable DNS name. That gives clustered software a reliable way to form peer lists and preserve roles, even though the underlying node or container runtime may change over time.

Storage is the other half. A StatefulSet can use `volumeClaimTemplates` so each Pod gets its own PersistentVolumeClaim derived from the same template. When `mysql-1` is rescheduled, it should return with the storage claim for `mysql-1`, not borrow a random volume from another member. This is the difference between scaling interchangeable workers and managing named participants in a durable system.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.4
          ports:
            - containerPort: 3306
              name: mysql
          volumeMounts:
            - name: mysql-data
              mountPath: /var/lib/mysql
  volumeClaimTemplates:
    - metadata:
        name: mysql-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

This manifest is intentionally incomplete for a production database because credentials, probes, configuration, backup, and operational safety need more design. It is complete enough to teach the controller promise: the StatefulSet owns named Pods, and the volume claim template creates per-Pod storage. A KCNA-level question will usually focus on that controller choice rather than on the full database administration burden.

Stop and think: a database cluster needs Pods with stable network identities such as `mysql-0`, `mysql-1`, and `mysql-2` that persist across restarts. Why can't a regular Deployment provide this, and what would happen to a database replication setup if Pod names were random? A strong answer separates application-level identity from mere replica count.

StatefulSets also change the way you reason about scaling down. Removing a replica from a Deployment usually removes an interchangeable worker. Removing a StatefulSet replica removes the highest ordinal Pod first, and its persistent volume claim may remain for safety depending on retention policy and storage setup. That conservative behavior prevents accidental data loss, but it also means cleanup is a deliberate storage operation rather than an automatic side effect.

The tradeoff is operational complexity. StatefulSets give stronger identity guarantees, but they do not make stateful software simple. You still need to understand backup, restore, upgrades, quorum, storage performance, and failure modes of the application itself. Kubernetes provides the stable envelope; it does not turn every database into a self-healing distributed system.

Use a StatefulSet when the application protocol cares about named members, ordered changes, or per-replica durable storage. Use a Deployment when replicas are intentionally replaceable and any Pod can handle any request after it becomes ready. That distinction is more important than whether the application "has data" in a vague sense, because many stateless services read and write data through external systems without requiring local identity.

## DaemonSets Place Agents on Nodes

DaemonSets solve a different scheduling problem: run a copy of a Pod on selected nodes. The usual examples are log collectors, metrics agents, node-local networking components, and storage drivers. These workloads are not scaled by request volume in the same way as application replicas. Their job is to accompany nodes, observe nodes, or provide node-level functionality, so the scheduling unit is the node rather than an arbitrary replica count.

The preserved DaemonSet diagram shows why a Deployment is the wrong abstraction for this case. A Deployment with four replicas might put two Pods on one node, one on another, and none on a third depending on scheduling constraints and available capacity. A DaemonSet ties the desired state to node membership. When a new eligible node joins, the DaemonSet should create a Pod there; when a node leaves, the associated Pod disappears with it.

```text
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

DaemonSets still use Pod templates, labels, update strategies, and scheduling rules, but their replica count is derived from eligible nodes. You can limit eligibility with node selectors, node affinity, or taints and tolerations, which is common when an agent should run only on Linux nodes, GPU nodes, storage nodes, or a particular node pool. The controller's promise is "one per matching node," not "N replicas somewhere."

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-observer
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: node-observer
  template:
    metadata:
      labels:
        app: node-observer
    spec:
      containers:
        - name: node-observer
          image: busybox:1.36
          command: ["sh", "-c", "while true; do date; sleep 30; done"]
```

The operational failure mode is easy to miss. If you deploy a log collector as a Deployment and then scale the cluster, some nodes may never run the collector, which means incidents on those nodes leave fewer traces. If you deploy a business API as a DaemonSet just to "spread it out," you tie application capacity to node count and make normal autoscaling harder. The controller should match the unit of need.

DaemonSets are also involved in cluster infrastructure, which is why they can feel more advanced than Deployments in day-to-day application work. Networking plugins, storage interface components, and node exporters often live as DaemonSets because every node needs local help before higher-level workloads behave normally. When troubleshooting a cluster-wide observability gap, `k get daemonset -A` can tell you whether node-level agents are actually present everywhere they should be.

Which approach would you choose here and why: a fraud detection API that needs ten replicas during peak traffic, or a metrics exporter that must read local node files on every worker? The first wants a Deployment because replicas are interchangeable service capacity. The second wants a DaemonSet because node coverage is the requirement.

## Jobs and CronJobs Model Finite Work

Not every workload should run forever. A migration, backup, report generator, image cleanup, or data import may have a clear finish line. If you place that task in a Deployment, Kubernetes interprets container exit as a problem because Deployments are designed to keep application Pods running. A Job flips that assumption: successful completion is the desired end state, and retry behavior exists to help the task reach that end state reliably.

The preserved Job diagram shows the finite contract. The Job creates Pods, watches their exit status, retries failures within configured limits, and records completions. Options such as `completions`, `parallelism`, and `backoffLimit` let you express whether work should run once, many times, or with controlled concurrency. That is a different design surface from a Deployment, whose core concern is available serving capacity.

```text
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

A Job manifest is often small, but the semantics are important. The restart policy for Job Pods is usually `Never` or `OnFailure`, not `Always`, because the Job controller is responsible for tracking attempts and completions. `backoffLimit` prevents endless retry loops when a bad command, missing configuration, or unavailable dependency would otherwise keep burning cluster resources without making progress.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: schema-check
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: schema-check
          image: busybox:1.36
          command: ["sh", "-c", "echo checking schema; sleep 5; echo complete"]
```

CronJobs add scheduling on top of Jobs. A CronJob does not run your command directly; it creates Jobs according to a cron expression, and those Jobs create Pods. That extra layer gives you history limits, concurrency policy, suspension, missed schedule handling, and timezone behavior. If the schedule is the product requirement, use a CronJob. If a human or pipeline triggers the finite task when needed, use a Job.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-schema-check
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: schema-check
              image: busybox:1.36
              command: ["sh", "-c", "date; echo complete"]
```

The most common CronJob surprise is overlap. If a nightly task sometimes takes longer than a day, should the next run start anyway, skip, or replace the old run? Kubernetes exposes that choice with `concurrencyPolicy`. `Allow` permits overlap, `Forbid` skips a new run when the previous one is still active, and `Replace` stops the current run and starts a new one. None is universally correct; the right answer depends on whether duplicate work is safe.

Jobs and CronJobs also have observability habits that differ from Deployments. A completed Job may have no running Pods, so `k get pods` alone can mislead you into thinking nothing happened. Inspect `k get jobs`, `k describe job`, and Pod logs while history remains available. For CronJobs, inspect both the CronJob and the Jobs it created, because scheduling and execution failures live at different layers.

Before running a backup as a CronJob, predict what should happen if yesterday's backup is still active when today's schedule fires. Then choose `Allow`, `Forbid`, or `Replace` based on the risk of duplicate writes, missed recovery points, and partial output. This is the kind of operational reasoning the resource choice is meant to force into the design.

## Patterns & Anti-Patterns

The most reliable pattern is to start from lifecycle semantics. If the process should keep serving, use a controller built for ongoing availability. If the process should finish, use a controller built for completion. This sounds obvious, but many production mistakes come from copying a familiar Deployment manifest and changing only the command. Kubernetes does exactly what the selected controller promises, so the design error can look like platform stubbornness when the controller faithfully restarts a task that was supposed to run once.

A second pattern is to treat Pod identity as an application contract. For a stateless API, identity belongs outside the Pod, usually in the Service, database, queue, or client request path. For a clustered database, identity may live inside the application protocol, where member names and storage locations carry meaning. Choosing between Deployment and StatefulSet is therefore not about whether the application is valuable; it is about whether a replacement Pod can safely become "any replica" or must return as a specific member.

A third pattern is to inspect ownership from the top down. Start with `k get deployment`, `k get statefulset`, `k get daemonset`, `k get job`, or `k get cronjob`, then follow the owned objects downward. This order keeps desired state in view while you troubleshoot symptoms. If you start by staring at a single Pod, you may miss that the Deployment is paused, the Job has already reached its backoff limit, or the DaemonSet is intentionally excluding a node through affinity.

Scaling patterns also differ by controller. Deployment scaling changes service capacity, so it pairs naturally with readiness probes, horizontal autoscaling, and rollout budgets. StatefulSet scaling changes named membership, so it requires application-specific thought about quorum, replication, and storage cleanup. DaemonSet scaling is mostly node scaling because eligible nodes determine Pod count. Job scaling means completions and parallelism, while CronJob scaling usually means schedule frequency and overlap policy.

The dangerous anti-pattern is controller cargo culting. A team learns Deployments first, so every workload becomes a Deployment until a migration repeats, a database loses identity, or a node agent misses half the fleet. Another team learns StatefulSets during a database project, so they overuse stable identity where interchangeable replicas would be simpler. Kubernetes gives these resources similar YAML shapes, but similar syntax does not imply similar operational promises.

Another anti-pattern is treating generated names as stable interface contracts. A Deployment Pod name can change whenever the controller replaces a Pod, and a ReplicaSet hash can change whenever the Pod template changes. If scripts, dashboards, or peer configuration depend on those generated names, the next rollout can break assumptions outside Kubernetes. Use Services, labels, selectors, StatefulSet ordinals, or application-level discovery depending on which identity is meant to be stable.

Avoid using cleanup as a substitute for understanding. Old ReplicaSets, completed Jobs, and CronJob history can look like clutter, but they often explain what happened during rollout or scheduled execution. Deleting them too early removes evidence and sometimes removes rollback options. A better pattern is to set history limits deliberately, keep enough operational context for diagnosis, and clean resources after you know which controller produced them and why.

Finally, avoid equating "controller created the Pod" with "application is healthy." A Deployment can maintain three Pods that all fail readiness. A StatefulSet can preserve storage identity for an incorrectly configured database. A DaemonSet can run everywhere while the agent lacks permissions. Jobs and CronJobs can complete with a command that produced bad business output. Workload resources manage Kubernetes lifecycle; they do not replace application validation.

## Decision Framework

The original decision diagram gives a quick route through the common choices. Its order is useful because finite work and per-node placement are sharper constraints than the general question of whether an application is "stateless." If the workload is a one-time task, choose Job before debating Deployment. If it must run on every node, choose DaemonSet before thinking about replica count. If it needs stable identity and storage, choose StatefulSet before reaching for familiar Deployment YAML.

```text
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

A stronger decision framework asks five questions in sequence. First, does success mean the process exits? If yes, use a Job or CronJob. Second, is the schedule part of the requirement? If yes, CronJob wraps Job creation. Third, is the desired placement tied to each node? If yes, use a DaemonSet. Fourth, does each replica need a stable name or its own durable volume? If yes, use a StatefulSet. Fifth, are replicas interchangeable service capacity? If yes, use a Deployment.

| Requirement Signal | Best Starting Resource | Reasoning Check | Watch Carefully |
|--------------------|------------------------|-----------------|-----------------|
| Replaceable web or API Pods | Deployment | Replica identity is not important, but rollout and scaling are important. | Readiness probes, rollout history, and selector labels. |
| Direct ReplicaSet management | ReplicaSet | Rarely appropriate outside special controller experiments or learning. | Lost rollout behavior and confusing ownership. |
| Named clustered members | StatefulSet | Pod ordinal and storage identity matter to the application protocol. | PersistentVolumeClaim lifecycle and ordered operations. |
| One agent per node | DaemonSet | Node coverage is the unit of desired state. | Node selectors, tolerations, and eligible node count. |
| Finite task triggered once | Job | Completion is success rather than failure. | Backoff limits, logs, and completed Pod history. |
| Finite task on a schedule | CronJob | The schedule creates Jobs, and each Job creates Pods. | Concurrency policy, missed schedules, and history limits. |

Patterns emerge from that framework. Use Deployments as the default for stateless serving workloads because they combine replica management, rollout status, rollback history, and scaling into one familiar API. Use StatefulSets when the application itself names members, because Kubernetes cannot guess that a random Pod suffix should keep a database role. Use DaemonSets for node infrastructure because missing one node may mean missing the exact node that fails during an incident.

Anti-patterns are the mirror image. Do not use a bare Pod for anything that should survive rescheduling, because no controller will recreate it for you. Do not use a Deployment for a finite migration, because exit will look like something to restart rather than something to record as complete. Do not use a CronJob for high-frequency event processing when a queue consumer Deployment would provide clearer backpressure and scaling.

The "best practice" summary from the original module still holds, but it is more convincing after the deeper tour. Almost never create Pods or ReplicaSets directly for ordinary applications. Create the controller that matches the workload promise, then let Kubernetes create and repair Pods as implementation details. This is how you move from "I can start a container" to "the platform can keep the right kind of workload alive."

| Resource | Use Case |
|----------|----------|
| **Deployment** | Stateless apps (web servers, APIs) |
| **StatefulSet** | Stateful apps (databases, caches) |
| **DaemonSet** | Per-node agents (logging, monitoring) |
| **Job** | One-time tasks (backups, migrations) |
| **CronJob** | Scheduled tasks (nightly jobs) |

In troubleshooting, always inspect the controller before inspecting individual Pods too deeply. A failing Pod can show you symptoms, but the controller explains intent: desired replicas, selector match, rollout status, completion counts, or node coverage. That context prevents you from fixing the wrong layer, such as deleting a Pod that a ReplicaSet immediately recreates with the same bad template.

The controller hierarchy also explains why Kubernetes object lists can feel noisy. A single Deployment can produce a Deployment row, one or more ReplicaSet rows, and multiple Pod rows. A CronJob can produce Job rows and Pod rows over time. The noise is meaningful if you read it as ownership history rather than as unrelated clutter.

You can turn the framework into a quick design review habit. Ask the application owner to describe what should happen when the container exits, when a node disappears, when the image changes, and when two copies of the work run at the same time. Those four questions reveal most workload mismatches before anyone writes a manifest. They also keep the discussion grounded in behavior, which is easier to validate than a vague claim that an application is "cloud native."

For stateless services, the exit question usually has a simple answer: the Pod should be replaced because service capacity should remain available. That answer points toward a Deployment, but it should also trigger questions about readiness, rollout pace, and rollback confidence. A Deployment can replace Pods gradually, yet it depends on accurate readiness signals to know when a new Pod should receive traffic. Choosing the resource is the beginning of the design, not the end of the production checklist.

For stateful systems, the node disappearance question is more revealing. If the application says, "bring the same member back with the same storage," you are in StatefulSet territory. If it says, "start any healthy worker and reconnect to shared storage or an external database," a Deployment may still be correct. This is why the same broad category, such as "cache," can lead to different choices depending on whether the cache is a disposable performance layer or a clustered system with membership rules.

For node agents, the image-change question should include blast radius. Updating a DaemonSet can touch every node-level agent, so a bad image may reduce observability, networking, or storage support across the cluster. Kubernetes supports DaemonSet update strategies, but the operational review should still consider whether the agent is critical infrastructure and whether nodes should roll gradually. The controller gives you placement; your rollout policy controls how much node-level risk moves at once.

For finite work, the overlap question is often the most important one. A backup, billing export, report, or migration may be harmless when repeated in a toy lab and dangerous when repeated against production state. Jobs and CronJobs let you express completion and schedule semantics, but they cannot decide whether duplicate work is safe. That decision belongs in the workload design, and the manifest should make the chosen policy visible through fields such as `backoffLimit` and `concurrencyPolicy`.

Verification should mirror those same design questions. For a Deployment, verify rollout status, active ReplicaSets, and available replicas. For a StatefulSet, verify ordered Pod names and volume claims. For a DaemonSet, compare desired Pods with eligible nodes rather than with a manually chosen replica count. For a Job, verify completion conditions and logs. For a CronJob, verify the schedule, concurrency policy, and Jobs created from the template. Each check proves the controller promise you selected.

This habit also helps during incident response. When an alert says "Pods are failing," the first useful question is which controller owns those Pods. If a Deployment owns them, you may be looking at a bad rollout, readiness failure, or capacity issue. If a Job owns them, you may be looking at retries and backoff. If a DaemonSet owns them, you may be looking at node eligibility or infrastructure drift. The controller narrows the diagnosis before the logs add detail.

## Did You Know?

- **Deployments keep old ReplicaSets** - By default, Kubernetes keeps 10 old ReplicaSets through `revisionHistoryLimit`, which gives `k rollout undo` a concrete previous template to scale back up.
- **StatefulSet Pods are created sequentially by default** - Ordered behavior means `pod-0` normally becomes ready before `pod-1` starts, which protects applications that need predictable cluster formation.
- **DaemonSets now work with the scheduler by default** - Modern Kubernetes schedules DaemonSet Pods through normal scheduler paths, which lets node affinity, taints, tolerations, and resource pressure participate in placement.
- **CronJob time zones are explicit in modern Kubernetes** - CronJobs support a `.spec.timeZone` field, so teams can avoid accidental dependence on the controller-manager's local timezone.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Creating a bare Pod for a service | A single Pod manifest feels simpler while learning, but no workload controller recreates it after deletion, node drain, or template change. | Use a Deployment for replaceable stateless service replicas, then inspect Deployment and ReplicaSet status instead of treating Pods as the source of truth. |
| Creating ReplicaSets directly | ReplicaSets expose the replica-count mechanism, so they look like a smaller Deployment, but they do not provide the same rollout and rollback workflow. | Create Deployments for ordinary applications and let the Deployment manage ReplicaSets as revision objects. |
| Using a Deployment for a database member | Deployments give random Pod names and interchangeable replicas, which conflicts with database membership, stable DNS, and per-member storage. | Use a StatefulSet with a headless Service and volume claim templates when the application requires stable identity. |
| Running a node agent as a Deployment | A Deployment replica count does not guarantee one Pod per node, so some nodes may lack logging, monitoring, networking, or storage support. | Use a DaemonSet and restrict eligible nodes with affinity, selectors, or tolerations when needed. |
| Running a finite migration as a Deployment | The Deployment controller treats container exit as a reason to restart, so a successful migration can become a repeated migration. | Use a Job for one-time finite work and set a clear `backoffLimit`, then check Job completion and logs. |
| Ignoring CronJob concurrency policy | Scheduled tasks can overlap when a previous run takes longer than expected, causing duplicate writes or confusing report output. | Choose `Allow`, `Forbid`, or `Replace` based on whether overlapping runs are safe for the workload. |
| Debugging only the newest Pod | Pods show symptoms, but controller conditions explain desired state, rollout progress, selector matching, and completion tracking. | Start with `k describe deployment`, `k describe job`, `k get daemonset`, or `k get statefulset`, then drill into Pods. |

## Quiz

<details><summary>Your team deployed a checkout API as a bare Pod, and the Pod disappeared during node maintenance. Which workload resource should replace it, and what controller behavior prevents the repeat incident?</summary>

Use a Deployment because the checkout API replicas should be replaceable service capacity. The Deployment maintains desired state through a ReplicaSet, so if a matching Pod disappears, the controller creates a replacement from the Pod template. This does not mean the application is automatically correct under every release, but it does mean node maintenance should not erase the entire workload. The answer should mention both the Deployment and the ReplicaSet because the ReplicaSet performs the replica-count reconciliation under the Deployment's rollout management.

</details>

<details><summary>A database cluster needs members named `db-0`, `db-1`, and `db-2`, and each member must keep its own volume after rescheduling. Why is a StatefulSet a better fit than a Deployment?</summary>

A StatefulSet is better because it preserves stable Pod identity through ordinal names and can create per-replica PersistentVolumeClaims from a template. A Deployment treats replicas as interchangeable and gives Pods generated names that can change across replacement. For clustered databases, names and volumes often participate in replication, quorum, and recovery logic, so random replacement can break assumptions the database makes. The controller choice is about identity and storage guarantees, not about whether databases are important.

</details>

<details><summary>A security team wants an agent on every Linux worker node to collect local audit logs. They propose a Deployment with the same replica count as the current node count. What should you recommend?</summary>

Recommend a DaemonSet because the requirement is node coverage, not an arbitrary number of replicas. A Deployment with today's node count can still place multiple Pods on one node and none on another, and it will not automatically adjust in the right way when eligible nodes join or leave. A DaemonSet creates one Pod on each matching node and can be constrained to Linux workers with selectors or affinity. This makes the workload resource match the operational promise.

</details>

<details><summary>A schema migration should run once, retry a few times if it fails, and stop after success. Why is a Job safer than a Deployment for this workload?</summary>

A Job treats successful completion as the desired state, while a Deployment treats a stopped container as something to replace. The Job controller can track completions, create replacement Pods for failed attempts within `backoffLimit`, and then stop creating Pods after success. A Deployment would keep trying to maintain running replicas, which can repeat a migration that was supposed to be finite. The safer design is to make the controller's success condition match the task's success condition.

</details>

<details><summary>During a Deployment rollout, you see two ReplicaSets for the same app label: one with zero replicas and one with three. Is this automatically a problem?</summary>

No, this can be normal rollout history. A Deployment creates a new ReplicaSet when the Pod template changes and scales the old ReplicaSet down after the new one becomes available. The old ReplicaSet may remain with zero replicas so Kubernetes can roll back to that template if needed. You should check rollout status and conditions before deleting old ReplicaSets, because they may represent useful revision history rather than orphaned objects.

</details>

<details><summary>A nightly report CronJob sometimes takes longer than the interval between schedules, and duplicate reports confuse downstream users. Which CronJob setting should you evaluate first?</summary>

Evaluate `concurrencyPolicy`, especially `Forbid` if a new run should be skipped while the previous one is active. The setting exists because CronJobs create Jobs over time, and the controller needs a rule for overlapping schedules. `Allow` may be fine for independent work, but report generation often writes shared outputs or sends notifications, so overlap can be harmful. The answer should connect the scheduling layer to Job creation rather than treating CronJob as just a command timer.

</details>

<details><summary>You apply a Deployment manifest, then `k get pods` shows Pods but `k rollout status deployment/web` never completes. What do you inspect next, and why?</summary>

Inspect the Deployment and ReplicaSet conditions with `k describe deployment web`, `k get rs -l app=web`, and Pod details for readiness, image pull, or scheduling failures. The Pod list shows that objects exist, but rollout status depends on updated and available replicas becoming ready according to the Deployment's rules. A readiness probe failure can leave Pods running but unavailable, while an image pull problem can keep new Pods from starting at all. Diagnosing the controller first keeps you focused on desired state and rollout progress.

</details>

## Hands-On Exercise

In this exercise you will create and inspect several workload resources in a Kubernetes 1.35+ cluster. A local kind, minikube, or managed development cluster is enough, provided you have permission to create resources in a disposable namespace. The commands use the `k` alias introduced earlier, and the manifests intentionally use small images and simple commands so the controller behavior stays visible.

Create a namespace first so cleanup is predictable. The namespace is not the lesson, but it gives you a clear boundary for listing resources and deleting everything at the end. If you already have a personal practice namespace, you can substitute it, but keep the commands consistent while you compare controller behavior.

```bash
k create namespace workload-lab
k config set-context --current --namespace=workload-lab
```

- [ ] Create a Deployment named `quote-api` with three replicas and verify the Deployment, ReplicaSet, and Pod ownership chain.

<details><summary>Solution</summary>

```bash
cat > quote-api-deployment.yaml <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quote-api
  labels:
    app: quote-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: quote-api
  template:
    metadata:
      labels:
        app: quote-api
    spec:
      containers:
        - name: quote-api
          image: nginx:1.26
          ports:
            - containerPort: 80
YAML
k apply -f quote-api-deployment.yaml
k rollout status deployment/quote-api
k get deploy,rs,pod -l app=quote-api
```

Success means you can point to one Deployment, one active ReplicaSet, and three Pods whose generated names show ReplicaSet ownership. If the rollout does not complete, inspect `k describe deployment quote-api` before changing the manifest.

</details>

- [ ] Update the Deployment image and verify that a new ReplicaSet appears while rollout history remains available.

<details><summary>Solution</summary>

```bash
k set image deployment/quote-api quote-api=nginx:1.27
k rollout status deployment/quote-api
k get rs -l app=quote-api
k rollout history deployment/quote-api
```

Success means the new ReplicaSet owns the active replicas and at least one older ReplicaSet remains visible with zero replicas. That old object is useful because rollback needs a previous Pod template to restore.

</details>

- [ ] Create a Job named `schema-check`, watch it complete, and compare its status with the still-running Deployment.

<details><summary>Solution</summary>

```bash
cat > schema-check-job.yaml <<'YAML'
apiVersion: batch/v1
kind: Job
metadata:
  name: schema-check
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: schema-check
          image: busybox:1.36
          command: ["sh", "-c", "echo checking schema; sleep 5; echo complete"]
YAML
k apply -f schema-check-job.yaml
k wait --for=condition=complete job/schema-check --timeout=90s
k get job,pod -l job-name=schema-check
k logs job/schema-check
```

Success means the Job reaches the complete condition and does not keep a permanently running Pod. Compare that with the Deployment, which keeps maintaining three running API Pods.

</details>

- [ ] Create a CronJob in suspended mode, inspect the schedule, then manually trigger one Job from its template.

<details><summary>Solution</summary>

```bash
cat > report-cronjob.yaml <<'YAML'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: report-check
spec:
  schedule: "0 2 * * *"
  suspend: true
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: report-check
              image: busybox:1.36
              command: ["sh", "-c", "date; echo report complete"]
YAML
k apply -f report-cronjob.yaml
k get cronjob report-check
k create job report-check-manual --from=cronjob/report-check
k wait --for=condition=complete job/report-check-manual --timeout=90s
k logs job/report-check-manual
```

Success means the CronJob exists without automatically firing in the lab, and the manually created Job completes from the CronJob template. The `Forbid` concurrency policy is visible in the manifest for discussion even though the lab does not wait for overlapping schedules.

</details>

- [ ] Explain, using the resources you created, why a Deployment is not a Job and why a CronJob is not just a Pod with a timer.

<details><summary>Solution</summary>

Use `k get deploy,rs,pod,job,cronjob` and compare the object hierarchy. The Deployment owns ReplicaSets that keep Pods running, while the Job records completion and stops after success. The CronJob owns a schedule and a Job template, then creates Jobs rather than running the command directly. A complete answer should describe the controller promise for each resource, not just list object names.

</details>

When you finish, clean up the lab namespace. Deleting the namespace removes the resources you created for this exercise, but production cleanup should be more deliberate when PersistentVolumeClaims, external load balancers, or shared namespaces are involved.

```bash
k delete namespace workload-lab
```

Use this success criteria checklist to confirm that you practiced the controller promises rather than only applying the YAML files:

- [ ] You can explain the Deployment to ReplicaSet to Pod hierarchy from live `k get` output.
- [ ] You can identify which ReplicaSet represents the current Deployment template after an image update.
- [ ] You can show that a Job records completion instead of maintaining a running Pod forever.
- [ ] You can explain how a CronJob creates Jobs on a schedule and why `concurrencyPolicy` matters.
- [ ] You can choose between Deployment, StatefulSet, DaemonSet, Job, and CronJob for a new scenario without relying on memorized names alone.

## Sources

- [Kubernetes documentation: Workloads](https://kubernetes.io/docs/concepts/workloads/)
- [Kubernetes documentation: Workload management](https://kubernetes.io/docs/concepts/workloads/controllers/)
- [Kubernetes documentation: Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes documentation: ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [Kubernetes documentation: StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Kubernetes documentation: DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [Kubernetes documentation: Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Kubernetes documentation: CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Kubernetes documentation: Labels and selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
- [Kubernetes documentation: Managing resources with kubectl](https://kubernetes.io/docs/reference/kubectl/)

## Next Module

[Module 1.7: Services](../module-1.7-services/) - Next you will connect these managed Pods to stable discovery and traffic paths inside and outside the cluster.

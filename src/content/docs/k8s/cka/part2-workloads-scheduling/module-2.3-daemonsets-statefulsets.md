---
title: "Module 2.3: DaemonSets & StatefulSets"
slug: k8s/cka/part2-workloads-scheduling/module-2.3-daemonsets-statefulsets
sidebar:
  order: 4
---

> **Complexity**: `[MEDIUM]` - Specialized workload patterns
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.1 (Pods), Module 2.2 (Deployments)

---

## What You'll Be Able to Do

After completing this comprehensive module, you will be able to:
- **Deploy** DaemonSets for node-level services and StatefulSets for stateful applications across diverse architectures.
- **Explain** how StatefulSet pod naming, PVC binding, and ordered deployment differ from standard Deployments.
- **Configure** DaemonSet tolerations and node selectors to run workloads on specific node pools or control plane nodes when needed.
- **Troubleshoot** StatefulSet issues, including stuck PVC binding, ordered rollout failures, and headless service DNS resolution.
- **Design** highly available systems that correctly leverage DaemonSets for log collection and monitoring agents.
- **Evaluate** application state requirements to choose appropriately between Deployments and StatefulSets for critical production workloads.

---

## Why This Module Matters

Deployments work exceptionally well for stateless applications like web servers, frontend applications, and lightweight microservices. However, not everything in a modern enterprise architecture is stateless. Some workloads have very specific, specialized requirements:

- **DaemonSets**: When you need exactly one pod per node (logging, monitoring, network plugins).
- **StatefulSets**: When pods need stable identities and persistent storage (databases, distributed systems).

In 2019, a major fintech company experienced a catastrophic, multi-hour outage affecting millions of transactions. The root cause? They had deployed their distributed messaging queue (Kafka) using standard Deployments rather than StatefulSets. When a brief network partition caused several nodes to drop, the Deployment controller eagerly spun up replacement pods. Because Deployments provide no guarantees regarding stable network identities or ordered startup, the new brokers came online with entirely new hostnames and immediately began attempting to form a new cluster split-brain style, utterly corrupting the topic metadata.

This incident cost the company over $4 million in SLA penalties and required a full weekend of manual data reconciliation. It perfectly illustrates why understanding specialized workload controllers is not just an exam requirement for the CKA, but a critical survival skill for production Kubernetes. Deployments work great for stateless applications, but when state, identity, or node-locality matter, you must reach for the right tools.

> **The Specialist Teams Analogy**
>
> Think of your cluster as a hospital. **Deployments** are like general practitioners—you can have any number, they're interchangeable, and patients don't care which one they see. **DaemonSets** are like security guards—you need exactly one per entrance (node), no more, no less. **StatefulSets** are like surgeons—each has a unique identity, their own dedicated tools (storage), and patients specifically request "Dr. Smith" (stable network identity).

---

## What You'll Learn

By the end of this module, you'll deeply understand and be able to:
- Create and manage DaemonSets to maintain node-level infrastructure.
- Understand when to use DaemonSets vs Deployments for edge cases.
- Create and manage StatefulSets to run robust databases inside Kubernetes.
- Understand stable network identity and storage mechanisms.
- Troubleshoot DaemonSet and StatefulSet issues effectively in production environments.

---

## Part 1: DaemonSets

### 1.1 What Is a DaemonSet?

A DaemonSet ensures that **all (or some) nodes run a copy of a pod**. As nodes are added to the cluster, pods are automatically added to them. As nodes are removed from the cluster, those pods are garbage collected. Deleting a DaemonSet will clean up the pods it created.

This behavior is fundamentally different from a Deployment, which simply ensures a specific *number* of pods are running somewhere in the cluster, completely regardless of which nodes they land on.

Here is the modern architectural representation:

```mermaid
flowchart TD
    subgraph Cluster Architecture
        subgraph Node 1
            DS1[DS Pod<br/>fluentd]
            App1[App Pods]
        end
        subgraph Node 2
            DS2[DS Pod<br/>fluentd]
            App2[App Pods]
        end
        subgraph Node 3
            DS3[DS Pod<br/>fluentd]
            App3[App Pods]
        end
        Node4[Node 4 Joins] -.-> |Auto-creates pod| DS4[DS Pod<br/>fluentd]
    end
    style DS1 fill:#f9f,stroke:#333,stroke-width:2px
    style DS2 fill:#f9f,stroke:#333,stroke-width:2px
    style DS3 fill:#f9f,stroke:#333,stroke-width:2px
    style DS4 fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
```

For historical completeness, here is the classical representation:

```text
┌────────────────────────────────────────────────────────────────┐
│                       DaemonSet                                 │
│                                                                 │
│   Node 1              Node 2              Node 3               │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌─────────┐ │      │
│   │ │ DS Pod  │ │     │ │ DS Pod  │ │     │ │ DS Pod  │ │      │
│   │ │(fluentd)│ │     │ │(fluentd)│ │     │ │(fluentd)│ │      │
│   │ └─────────┘ │     │ └─────────┘ │     │ └─────────┘ │      │
│   │             │     │             │     │             │      │
│   │ [App Pods] │     │ [App Pods] │     │ [App Pods] │      │
│   │             │     │             │     │             │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                 │
│   When Node 4 joins → DaemonSet automatically creates pod      │
│   When Node 2 leaves → Pod is terminated                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Common DaemonSet Use Cases

DaemonSets are the backbone of Kubernetes cluster administration. You typically use them to run cluster-level infrastructure daemons rather than user-facing applications.

| Use Case | Example |
|----------|---------|
| Log collection | Fluentd, Filebeat |
| Node monitoring | Node Exporter, Datadog agent |
| Network plugins | Calico, Cilium, Weave |
| Storage daemons | GlusterFS, Ceph |
| Security agents | Falco, Sysdig |

### 1.3 Creating a DaemonSet

Creating a DaemonSet looks remarkably similar to creating a Deployment. The primary difference is the `kind: DaemonSet` declaration and the lack of a `replicas` field (since the number of replicas is strictly determined by the number of matching nodes).

```yaml
# fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  labels:
    app: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluentd:v1.35
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

Apply it to your cluster:

```bash
kubectl apply -f fluentd-daemonset.yaml
```

> **Pause and predict**: You have a 5-node cluster and create a DaemonSet. Then a 6th node joins the cluster. What happens automatically? Now imagine you do the same with a Deployment set to 5 replicas -- what happens when the 6th node joins?

### 1.4 DaemonSet vs Deployment

It is critical to distinguish between these two controllers, as picking the wrong one leads to resource starvation or incomplete coverage.

| Aspect | DaemonSet | Deployment |
|--------|-----------|------------|
| Pod count | One per node (automatic) | Specified replicas |
| Scheduling | Bypasses scheduler | Uses scheduler |
| Node addition | Auto-creates pod | No automatic action |
| Use case | Node-level services | Application workloads |

### 1.5 DaemonSet Commands

Managing DaemonSets via the command line is straightforward and mirrors Deployment management commands.

```bash
# List DaemonSets
kubectl get daemonsets
kubectl get ds           # Short form

# Describe DaemonSet
kubectl describe ds fluentd

# Check pods created by DaemonSet
kubectl get pods -l app=fluentd -o wide

# Delete DaemonSet
kubectl delete ds fluentd
```

> **Did You Know?**
>
> DaemonSets ignore most scheduling constraints by default. They even run on control plane nodes if there are no taints preventing it. Use `nodeSelector` or `tolerations` to control placement.

---

## Part 2: DaemonSet Scheduling

### 2.1 Running on Specific Nodes

You don't always want a DaemonSet to run on *every single node*. For example, you might have a DaemonSet that manages specialized GPU hardware. It makes no sense to run this on standard CPU compute nodes. You can use a `nodeSelector` to restrict the DaemonSet.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ssd-monitor
spec:
  selector:
    matchLabels:
      app: ssd-monitor
  template:
    metadata:
      labels:
        app: ssd-monitor
    spec:
      nodeSelector:
        disk: ssd            # Only nodes with this label
      containers:
      - name: monitor
        image: busybox
        command: ["sleep", "infinity"]
```

Applying the label to dictate scheduling:

```bash
# Label a node
kubectl label node worker-1 disk=ssd

# DaemonSet only runs on labeled nodes
kubectl get pods -l app=ssd-monitor -o wide
```

### 2.2 Tolerating Taints

Nodes often have taints applied to repel normal workloads (e.g., control plane nodes are usually tainted). DaemonSets often need to run on tainted nodes to provide full cluster monitoring or network coverage.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      tolerations:
      # Tolerate control-plane taint
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      # Tolerate all taints (run everywhere)
      - operator: Exists
      containers:
      - name: monitor
        image: prom/node-exporter
```

### 2.3 Update Strategy

DaemonSets handle updates carefully to ensure node-level services aren't all taken down simultaneously.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  updateStrategy:
    type: RollingUpdate        # Default
    rollingUpdate:
      maxUnavailable: 1        # Update one node at a time
  selector:
    matchLabels:
      app: fluentd
  template:
    # ...
```

| Strategy | Behavior |
|----------|----------|
| `RollingUpdate` | Gradually update pods, one node at a time |
| `OnDelete` | Only update when pod is manually deleted |

---

## Part 3: StatefulSets

### 3.1 What Is a StatefulSet?

StatefulSets manage stateful applications with precise, guaranteed behaviors that Deployments lack:
- **Stable, unique network identifiers**
- **Stable, persistent storage**
- **Ordered, graceful deployment and scaling**

```mermaid
flowchart TD
    subgraph StatefulSet Architecture
        subgraph pod-0 [web-0]
            direction TB
            DNS0[DNS: web-0...]
            PVC0[(PVC: data-0)]
        end
        subgraph pod-1 [web-1]
            direction TB
            DNS1[DNS: web-1...]
            PVC1[(PVC: data-1)]
        end
        subgraph pod-2 [web-2]
            direction TB
            DNS2[DNS: web-2...]
            PVC2[(PVC: data-2)]
        end
    end
    
    Crash[web-1 Crashes] -.-> |Recreated as| pod-1
    style PVC0 fill:#f96,stroke:#333,stroke-width:2px
    style PVC1 fill:#f96,stroke:#333,stroke-width:2px
    style PVC2 fill:#f96,stroke:#333,stroke-width:2px
```

```text
┌────────────────────────────────────────────────────────────────┐
│                       StatefulSet                               │
│                                                                 │
│   Unlike Deployments, pods have stable identities:             │
│                                                                 │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│   │    web-0      │  │    web-1      │  │    web-2      │      │
│   │  (always 0)   │  │  (always 1)   │  │  (always 2)   │      │
│   │               │  │               │  │               │      │
│   │ PVC: data-0   │  │ PVC: data-1   │  │ PVC: data-2   │      │
│   │ DNS: web-0... │  │ DNS: web-1... │  │ DNS: web-2... │      │
│   └───────────────┘  └───────────────┘  └───────────────┘      │
│                                                                 │
│   If web-1 dies and restarts:                                  │
│   - Still named web-1 (not web-3)                              │
│   - Reattaches to PVC data-1                                   │
│   - Same DNS name: web-1.nginx.default.svc.cluster.local       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 StatefulSet Use Cases

- **StatefulSets**: When pods need stable identities and persistent storage (databases, distributed systems).

| Use Case | Example |
|----------|---------|
| Databases | PostgreSQL, MySQL, MongoDB |
| Distributed systems | Kafka, Zookeeper, etcd |
| Search engines | Elasticsearch |
| Message queues | RabbitMQ |

> **Pause and predict**: If you delete pod `web-1` from a StatefulSet, what name will the replacement pod get -- `web-1` or `web-3`? What happens to the PVC that was bound to `web-1`?

### 3.3 StatefulSet Requirements

StatefulSets require a **Headless Service** to establish their network identity. 

First, we define the Headless Service:

```yaml
# Headless Service (required)
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None          # This makes it headless
  selector:
    app: nginx
```

Then, we define the StatefulSet, linking it to the Headless Service via `serviceName`:

```yaml
# StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx       # Must reference the headless service
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
        image: nginx
        ports:
        - containerPort: 80
        volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:    # Creates PVC for each pod
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

### 3.4 Stable Network Identity

The combination of the StatefulSet controller and the Headless Service yields highly predictable DNS records for every individual pod.

```bash
# Pod DNS names follow pattern:
# <pod-name>.<service-name>.<namespace>.svc.cluster.local

# For StatefulSet "web" with headless service "nginx":
web-0.nginx.default.svc.cluster.local
web-1.nginx.default.svc.cluster.local
web-2.nginx.default.svc.cluster.local

# Other pods can reach specific instances:
curl web-0.nginx
curl web-1.nginx
```

### 3.5 Stable Storage

Through the `volumeClaimTemplates` field, the StatefulSet dynamically provisions unique storage for each pod ordinal.

```bash
# Each pod gets its own PVC named:
# <volumeClaimTemplates.name>-<pod-name>
data-web-0
data-web-1
data-web-2

# When pod restarts, it reattaches to its specific PVC
# Data persists across pod restarts
```

> **Did You Know?**
>
> When you delete a StatefulSet, the PVCs are NOT automatically deleted. This is a safety feature—you keep your data. To clean up, manually delete the PVCs after deleting the StatefulSet.

---

## Part 4: StatefulSet Operations

### 4.1 Ordered Creation and Deletion

StatefulSets enforce strict ordering to prevent race conditions during distributed cluster formation.

```text
Scaling Up (0 → 3):
web-0 created and ready → web-1 created and ready → web-2 created

Scaling Down (3 → 1):
web-2 terminated → web-1 terminated → web-0 remains

Each pod waits for previous to be Running and Ready
```

### 4.2 Pod Management Policy

You can override the strict ordering if your application doesn't require it (e.g., a massive array of independent processing nodes that still need stable storage).

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  podManagementPolicy: OrderedReady   # Default - sequential
  # podManagementPolicy: Parallel     # All at once (like Deployment)
```

| Policy | Behavior |
|--------|----------|
| `OrderedReady` | Sequential creation/deletion (default) |
| `Parallel` | All pods created/deleted simultaneously |

> **Stop and think**: You're running a 3-replica StatefulSet for a database cluster. You want to test a new version on just one replica before rolling it out to all. How would you use the `partition` field to achieve a canary deployment? Which pod gets updated first -- web-0 or web-2?

### 4.3 Update Strategy

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2          # Only update pods >= 2
```

**Partition** enables canary deployments:
- With `partition: 2`, only web-2 gets updated
- web-0 and web-1 keep the old version
- Useful for testing updates on subset of pods

### 4.4 StatefulSet Commands

```bash
# List StatefulSets
kubectl get statefulsets
kubectl get sts           # Short form

# Describe
kubectl describe sts web

# Scale
kubectl scale sts web --replicas=5

# Check pods (notice ordered names)
kubectl get pods -l app=nginx

# Check PVCs (one per pod)
kubectl get pvc

# Delete StatefulSet (PVCs remain!)
kubectl delete sts web

# Delete PVCs manually
kubectl delete pvc data-web-0 data-web-1 data-web-2
```

---

## Part 5: Deployment vs StatefulSet

### 5.1 Comparison

| Aspect | Deployment | StatefulSet |
|--------|------------|-------------|
| Pod names | Random suffix (nginx-5d5dd5d5fb-xyz) | Ordinal index (web-0, web-1) |
| Network identity | None (use Service) | Stable DNS per pod |
| Storage | Shared or none | Dedicated PVC per pod |
| Scaling order | Any order | Sequential (ordered) |
| Rolling update | Random order | Reverse order (N-1 first) |
| Use case | Stateless apps | Stateful apps |

### 5.2 When to Use What

```mermaid
flowchart TD
    Start[Does each pod need unique identity?]
    Start -->|No| NodeLevel[Does each node need one pod?]
    Start -->|Yes| Storage[Does it need persistent storage?]
    
    NodeLevel -->|Yes| DS[DaemonSet]
    NodeLevel -->|No| Deploy[Deployment]
    
    Storage -->|Yes or No| STS[StatefulSet]
    
    style DS fill:#bbf,stroke:#333,stroke-width:2px
    style Deploy fill:#bfb,stroke:#333,stroke-width:2px
    style STS fill:#fbb,stroke:#333,stroke-width:2px
```

```text
┌────────────────────────────────────────────────────────────────┐
│                   Choosing the Right Controller                 │
│                                                                 │
│   Does each pod need unique identity?                          │
│         │                                                       │
│         ├── No ──► Does each node need one pod?                │
│         │                │                                      │
│         │                ├── Yes ──► DaemonSet                 │
│         │                │                                      │
│         │                └── No ──► Deployment                 │
│         │                                                       │
│         └── Yes ──► Does it need persistent storage?           │
│                          │                                      │
│                          └── Yes/No ──► StatefulSet            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **War Story: The Database Disaster**
>
> A team deployed PostgreSQL using a Deployment with a PVC. It worked—until the pod was rescheduled. The new pod got a different IP, replication broke, and the standby couldn't find the primary. Switching to a StatefulSet with stable network identity fixed everything. Use the right tool!

---

## Part 6: Headless Services Deep Dive

### 6.1 What Is a Headless Service?

A Service with `clusterIP: None` is referred to as a "Headless" Service. Instead of load balancing traffic across endpoints via a single Virtual IP, the DNS server directly returns the individual pod IPs.

Here is a regular service:
```yaml
# Regular Service
apiVersion: v1
kind: Service
metadata:
  name: nginx-regular
spec:
  selector:
    app: nginx
  ports:
  - port: 80
# DNS: nginx-regular → ClusterIP (load balanced)
```

And here is its headless counterpart:
```yaml
# Headless Service
apiVersion: v1
kind: Service
metadata:
  name: nginx-headless
spec:
  clusterIP: None           # Headless!
  selector:
    app: nginx
  ports:
  - port: 80
# DNS: nginx-headless → Returns all pod IPs
# DNS: web-0.nginx-headless → Specific pod IP
```

### 6.2 DNS Resolution Comparison

When querying CoreDNS inside the cluster, the structural difference is obvious:

```bash
# Regular service - returns ClusterIP
nslookup nginx-regular
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name: nginx-regular.default.svc.cluster.local
# Address: 10.96.100.50  (ClusterIP)

# Headless service - returns pod IPs
nslookup nginx-headless
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name: nginx-headless.default.svc.cluster.local
# Address: 10.244.1.5  (Pod IP)
# Address: 10.244.2.6  (Pod IP)
# Address: 10.244.3.7  (Pod IP)
```

> **Did You Know?**
>
> CoreDNS automatically creates multiple A records for a headless service. If your StatefulSet has 5 replicas, doing a DNS lookup on the headless service name returns 5 different IP addresses in a randomized order, enabling basic client-side load balancing!

> **Did You Know?**
>
> StatefulSet pod ordinals always start at 0 and strictly go up to N-1. If you scale a StatefulSet to 100 replicas, the highest pod name will be `app-99`. There is no native configuration to start the index at 1 or skip numbers.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| StatefulSet without headless Service | Pods don't get stable DNS names | Create headless Service with matching selector |
| Deleting StatefulSet expecting PVC cleanup | Data remains, storage quota consumed | Manually delete PVCs if data not needed |
| Using Deployment for databases | No stable identity, storage issues | Use StatefulSet for stateful workloads |
| DaemonSet on all nodes unexpectedly | Runs on control plane too | Add appropriate tolerations/nodeSelector |
| Wrong serviceName in StatefulSet | DNS resolution fails | Ensure serviceName matches headless Service name |
| Scaling StatefulSet too quickly during crash | Ordered rollout gets stuck waiting for failing pod | Fix the failing pod or use `Parallel` podManagementPolicy |
| Updating StatefulSet with `OnDelete` strategy | Pods don't update automatically | Delete pods manually or change to `RollingUpdate` |
| Forgetting to match labels in DaemonSet | DaemonSet controller creates infinite pods or fails | Ensure `spec.selector.matchLabels` matches `template.metadata.labels` |

---

## Quiz

1. **Your monitoring team needs exactly one log collector pod on every node, including nodes added later. A colleague suggests using a Deployment with `replicas` set to the node count and pod anti-affinity. Why would a DaemonSet be a better choice, and what happens when a new node joins the cluster?**
   <details>
   <summary>Answer</summary>
   A DaemonSet is better because it automatically creates a pod on every new node that joins the cluster and removes pods from nodes that leave. With a Deployment and anti-affinity, you'd need to manually increase the replica count each time a node is added, and the anti-affinity only *prefers* spreading -- it doesn't guarantee one-per-node. Additionally, DaemonSets can tolerate taints that normal Deployments cannot, ensuring coverage on special-purpose nodes like GPU nodes or control plane nodes.
   </details>

2. **You're deploying a 3-node PostgreSQL cluster with primary-standby replication. The standby nodes need to connect to the primary by a stable DNS name, and each node needs its own persistent volume that survives pod restarts. Which controller do you use, and what additional resource is required? What happens if `web-1` (a standby) crashes?**
   <details>
   <summary>Answer</summary>
   Use a StatefulSet with a headless Service (`clusterIP: None`). The headless Service is required because it provides stable DNS names like `web-0.postgres.default.svc.cluster.local` for each pod. The `volumeClaimTemplates` field ensures each pod gets its own PVC (e.g., `data-web-0`, `data-web-1`). When `web-1` crashes, the StatefulSet controller recreates it with the exact same name `web-1` (not `web-3`), and it reattaches to its original PVC `data-web-1`, preserving all data. The standby configuration pointing to `web-0.postgres` continues to work because the DNS name is stable.
   </details>

3. **You deleted a StatefulSet with `kubectl delete sts web`, but your storage costs haven't decreased. A colleague says the data should have been cleaned up automatically. What actually happened, and what must you do to reclaim the storage?**
   <details>
   <summary>Answer</summary>
   PVCs created by a StatefulSet's `volumeClaimTemplates` are NOT automatically deleted when the StatefulSet is deleted. This is an intentional safety feature to prevent accidental data loss -- database data is precious. The PVCs (e.g., `data-web-0`, `data-web-1`, `data-web-2`) still exist and are bound to their PersistentVolumes, consuming storage. You must manually delete them with `kubectl delete pvc data-web-0 data-web-1 data-web-2`. Always audit PVCs after deleting StatefulSets to avoid ongoing storage costs.
   </details>

4. **You need to scale a StatefulSet from 3 replicas to 5. In what order are the new pods created? Then you scale back down to 2. In what order are pods terminated, and why does this ordering matter for distributed databases?**
   <details>
   <summary>Answer</summary>
   Scaling up: `web-3` is created first and must become Running and Ready before `web-4` is created. Scaling down: `web-4` is terminated first, then `web-3`, then `web-2`. This reverse-ordinal ordering matters for distributed databases because higher-numbered replicas are typically the newest members of the cluster. Removing them first ensures the most established members (which may hold leadership roles or have the most data) are the last to be removed. For example, in a database cluster, `web-0` is often the primary, and removing it last prevents unnecessary leader elections during scale-down.
   </details>

5. **You need to test a risky new configuration on just a single instance of your 5-replica StatefulSet without affecting the rest of the cluster. How can you accomplish this gracefully using native StatefulSet features?**
   <details>
   <summary>Answer</summary>
   You can utilize the `partition` field within the `rollingUpdate` strategy. By setting `partition: 4`, only the pod with ordinal 4 (`web-4`) will be updated to the new configuration. The pods `web-0` through `web-3` will remain untouched. Once you have verified the configuration on `web-4`, you can gradually lower the partition number to roll the update out to the remaining pods.
   </details>

6. **You have deployed a DaemonSet intended to run a security scanner on every node, but you notice it is completely absent from all three of your control plane nodes. What is the most likely cause, and how do you resolve it?**
   <details>
   <summary>Answer</summary>
   The control plane nodes are likely tainted with `node-role.kubernetes.io/control-plane:NoSchedule` to prevent standard workloads from running on them. The DaemonSet controller respects taints by default. To force the DaemonSet to run on these nodes, you must add a matching `toleration` to the DaemonSet's pod template spec that explicitly tolerates the control plane taint.
   </details>

7. **A developer is confused why running `nslookup my-database` on a StatefulSet's headless service returns a list of IPs instead of a single load-balancer IP. What is happening fundamentally under the hood with CoreDNS?**
   <details>
   <summary>Answer</summary>
   Because the service is defined with `clusterIP: None` (making it headless), Kubernetes does not allocate a virtual IP or configure kube-proxy iptables rules for it. Instead, CoreDNS directly monitors the Endpoints associated with the service's selector. It creates multiple standard A records—one for each underlying pod IP—and returns the full list of IPs to the client, allowing the client application to handle its own connection pooling or target specific pods directly.
   </details>

---

## Hands-On Exercise

**Task**: Create a DaemonSet and StatefulSet, understand their behaviors, and observe network identity.

**Steps**:

### Part A: DaemonSet

1. **Create a DaemonSet**:
```bash
cat > node-monitor-ds.yaml << 'EOF'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      containers:
      - name: monitor
        image: busybox
        command: ["sh", "-c", "while true; do echo $(hostname); sleep 60; done"]
        resources:
          limits:
            memory: 50Mi
            cpu: 50m
EOF

kubectl apply -f node-monitor-ds.yaml
```

2. **Verify one pod per node**:
```bash
kubectl get pods -l app=node-monitor -o wide
kubectl get ds node-monitor
# DESIRED = CURRENT = READY = number of nodes
```

3. **Check logs from a specific node's pod**:
```bash
kubectl logs -l app=node-monitor --all-containers
```

4. **Cleanup DaemonSet**:
```bash
kubectl delete ds node-monitor
rm node-monitor-ds.yaml
```

### Part B: StatefulSet

1. **Create headless Service and StatefulSet**:
```bash
cat > statefulset-demo.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  clusterIP: None
  selector:
    app: nginx
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
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
        image: nginx
        ports:
        - containerPort: 80
EOF

kubectl apply -f statefulset-demo.yaml
```

2. **Watch ordered creation**:
```bash
kubectl get pods -l app=nginx -w
# web-0 Running, then web-1, then web-2
```

3. **Verify stable network identity**:
```bash
# Create a test pod
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-0.nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-1.nginx
```

4. **Scale down and observe order**:
```bash
kubectl scale sts web --replicas=1
kubectl get pods -l app=nginx -w
# web-2 terminates, then web-1
```

5. **Scale back up**:
```bash
kubectl scale sts web --replicas=3
kubectl get pods -l app=nginx -w
# web-1 created, then web-2
```

6. **Cleanup**:
```bash
kubectl delete -f statefulset-demo.yaml
rm statefulset-demo.yaml
```

**Success Criteria**:
- [ ] Can create DaemonSets across diverse node topologies.
- [ ] Understand one pod per node behavior natively.
- [ ] Can create StatefulSets with properly linked headless Services.
- [ ] Understand ordered scaling and the guarantees it provides.
- [ ] Know when to use each controller to prevent production disasters.
- [ ] Understand stable network identity and storage.

---

## Practice Drills

### Drill 1: DaemonSet Creation (Target: 3 minutes)

```bash
# Create DaemonSet
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      containers:
      - name: collector
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Verify
kubectl get ds log-collector
kubectl get pods -l app=log-collector -o wide

# Cleanup
kubectl delete ds log-collector
```

### Drill 2: DaemonSet with nodeSelector (Target: 5 minutes)

```bash
# Label one node
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE disk=ssd

# Create DaemonSet with nodeSelector
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ssd-only
spec:
  selector:
    matchLabels:
      app: ssd-only
  template:
    metadata:
      labels:
        app: ssd-only
    spec:
      nodeSelector:
        disk: ssd
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Verify - should only run on labeled node
kubectl get pods -l app=ssd-only -o wide

# Cleanup
kubectl delete ds ssd-only
kubectl label node $NODE disk-
```

### Drill 3: StatefulSet Basic (Target: 5 minutes)

```bash
# Create headless service and StatefulSet
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  clusterIP: None
  selector:
    app: db
  ports:
  - port: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
      - name: postgres
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Watch ordered creation
kubectl get pods -l app=db -w &
sleep 30
kill %1

# Verify names
kubectl get pods -l app=db

# Cleanup
kubectl delete sts db
kubectl delete svc db
```

### Drill 4: StatefulSet DNS Test (Target: 5 minutes)

```bash
# Create StatefulSet with headless service
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  clusterIP: None
  selector:
    app: nginx
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
  replicas: 2
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
        image: nginx
EOF

# Wait for ready
kubectl wait --for=condition=ready pod/web-0 pod/web-1 --timeout=60s

# Test DNS resolution
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-0.nginx
kubectl run dns-test --image=busybox --rm -it --restart=Never -- nslookup web-1.nginx

# Cleanup
kubectl delete sts web
kubectl delete svc nginx
```

### Drill 5: StatefulSet Scaling Order (Target: 3 minutes)

```bash
# Create StatefulSet
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: order-test
spec:
  clusterIP: None
  selector:
    app: order-test
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: order
spec:
  serviceName: order-test
  replicas: 1
  selector:
    matchLabels:
      app: order-test
  template:
    metadata:
      labels:
        app: order-test
    spec:
      containers:
      - name: nginx
        image: nginx
EOF

# Scale up and watch order
kubectl scale sts order --replicas=3
kubectl get pods -l app=order-test -w &
sleep 30
kill %1

# Scale down and watch reverse order
kubectl scale sts order --replicas=1
kubectl get pods -l app=order-test -w &
sleep 30
kill %1

# Cleanup
kubectl delete sts order
kubectl delete svc order-test
```

### Drill 6: Troubleshooting - DaemonSet Not Running on Node

```bash
# Taint a node
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl taint node $NODE special=true:NoSchedule

# Create DaemonSet without toleration
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: no-toleration
spec:
  selector:
    matchLabels:
      app: no-toleration
  template:
    metadata:
      labels:
        app: no-toleration
    spec:
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

# Check - won't run on tainted node
kubectl get pods -l app=no-toleration -o wide
kubectl get ds no-toleration

# YOUR TASK: Fix by adding toleration
# (Delete and recreate with toleration)

# Cleanup
kubectl delete ds no-toleration
kubectl taint node $NODE special-
```

<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: with-toleration
spec:
  selector:
    matchLabels:
      app: with-toleration
  template:
    metadata:
      labels:
        app: with-toleration
    spec:
      tolerations:
      - key: special
        operator: Equal
        value: "true"
        effect: NoSchedule
      containers:
      - name: app
        image: busybox
        command: ["sleep", "infinity"]
EOF

kubectl get pods -l app=with-toleration -o wide
kubectl delete ds with-toleration
```

</details>

### Drill 7: Challenge - Identify the Right Controller

For each scenario, identify whether to use Deployment, DaemonSet, or StatefulSet:

1. Web application with 5 replicas
2. Log collector on every node
3. PostgreSQL database cluster
4. REST API service
5. Prometheus node exporter
6. Kafka cluster
7. nginx reverse proxy

<details>
<summary>Answers</summary>

1. **Deployment** - Stateless web app
2. **DaemonSet** - Need one per node
3. **StatefulSet** - Needs stable identity and storage
4. **Deployment** - Stateless REST API
5. **DaemonSet** - Monitoring agent per node
6. **StatefulSet** - Distributed system with stable identity
7. **Deployment** - Stateless proxy (unless specific instance needed)

</details>

---

## Next Module

[Module 2.4: Jobs & CronJobs](../module-2.4-jobs-cronjobs/) - Dive into batch workloads and scheduled tasks to round out your knowledge of specialized workload controllers.
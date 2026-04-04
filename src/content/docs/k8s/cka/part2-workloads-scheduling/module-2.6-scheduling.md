---
title: "Module 2.6: Scheduling"
slug: k8s/cka/part2-workloads-scheduling/module-2.6-scheduling
sidebar:
  order: 7
lab:
  id: cka-2.6-scheduling
  url: https://killercoda.com/kubedojo/scenario/cka-2.6-scheduling
  duration: "45 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical exam topic
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 2.1 (Pods), Module 2.5 (Resource Management)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Configure** nodeSelector, node affinity, and pod affinity/anti-affinity rules
- **Use** taints and tolerations to control which pods can run on specific nodes
- **Implement** pod topology spread constraints for high availability across zones
- **Debug** Pending pods by reading scheduler events and matching them to node constraints

---

## Why This Module Matters

By default, the scheduler places pods on any node with available resources. But in production, you need control:
- Run database pods on nodes with SSDs
- Keep certain pods apart for high availability
- Spread workloads across availability zones
- Reserve nodes for specific workloads

The CKA exam frequently tests scheduling constraints. You'll need to use nodeSelector, affinity rules, and taints/tolerations.

> **The Event Planner Analogy**
>
> Think of scheduling like seating at a wedding. **nodeSelector** is "VIPs at Table 1." **Node affinity** is "Prefer tables near the stage, but anywhere is fine." **Taints** are reserved tables with "Staff Only" signs. **Tolerations** are staff badges that let you sit at reserved tables. **Anti-affinity** is "Don't seat the exes at the same table."

---

## What You'll Learn

By the end of this module, you'll be able to:
- Use nodeSelector for simple node selection
- Configure node affinity and anti-affinity
- Apply taints to nodes and tolerations to pods
- Spread pods across topology domains
- Troubleshoot scheduling issues

---

## Part 1: nodeSelector

### 1.1 The Simplest Approach

nodeSelector is the simplest way to constrain pods to specific nodes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ssd-pod
spec:
  nodeSelector:
    disk: ssd              # Only schedule on nodes with this label
  containers:
  - name: nginx
    image: nginx
```

### 1.2 Working with Node Labels

```bash
# List node labels
kubectl get nodes --show-labels

# Label a node
kubectl label node worker-1 disk=ssd

# Remove a label
kubectl label node worker-1 disk-

# Overwrite a label
kubectl label node worker-1 disk=hdd --overwrite
```

### 1.3 Common Built-in Labels

| Label | Description |
|-------|-------------|
| `kubernetes.io/hostname` | Node hostname |
| `kubernetes.io/os` | Operating system (linux, windows) |
| `kubernetes.io/arch` | Architecture (amd64, arm64) |
| `topology.kubernetes.io/zone` | Cloud availability zone |
| `topology.kubernetes.io/region` | Cloud region |
| `node.kubernetes.io/instance-type` | Instance type (cloud) |

```yaml
# Example: Schedule only on Linux nodes
spec:
  nodeSelector:
    kubernetes.io/os: linux
```

> **Did You Know?**
>
> You can combine multiple nodeSelector labels. The pod only schedules on nodes that match ALL labels (AND logic).

---

## Part 2: Node Affinity

> **Pause and predict**: You want a pod to run on SSD nodes but also accept NVMe nodes. With `nodeSelector`, you can only specify one value per key. How would you express "disk must be SSD OR NVMe" as a scheduling constraint?

### 2.1 Why Node Affinity?

Node affinity is more expressive than nodeSelector:
- **Soft preferences** ("prefer but don't require")
- **Multiple match options** (OR logic)
- **Operators** (In, NotIn, Exists, DoesNotExist, Gt, Lt)

### 2.2 Affinity Types

| Type | Behavior |
|------|----------|
| `requiredDuringSchedulingIgnoredDuringExecution` | Hard requirement (like nodeSelector) |
| `preferredDuringSchedulingIgnoredDuringExecution` | Soft preference |

> **Key Point**: "IgnoredDuringExecution" means if labels change after scheduling, the pod stays. There's no rescheduling.

### 2.3 Required Affinity (Hard)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-required
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disk
            operator: In
            values:
            - ssd
            - nvme
  containers:
  - name: nginx
    image: nginx
```

### 2.4 Preferred Affinity (Soft)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-preferred
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80               # Higher weight = stronger preference
        preference:
          matchExpressions:
          - key: disk
            operator: In
            values:
            - ssd
      - weight: 20
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - us-west-1a
  containers:
  - name: nginx
    image: nginx
```

> **War Story: The Lopsided Cluster**
>
> A team used `preferredDuringSchedulingIgnoredDuringExecution` to attract all CI/CD builder pods to nodes with a `builder=true` label. Because it was only a soft preference, the cluster autoscaler didn't provision new builder nodes when they got full; it just dumped the overflow pods onto general-purpose web nodes. The web applications were starved for CPU by the greedy builder pods. If a workload absolutely requires specific hardware isolation, use hard affinity or taints, not soft affinity.

### 2.5 Operators

| Operator | Meaning |
|----------|---------|
| `In` | Label value is in set |
| `NotIn` | Label value not in set |
| `Exists` | Label exists (any value) |
| `DoesNotExist` | Label doesn't exist |
| `Gt` | Greater than (integer comparison) |
| `Lt` | Less than (integer comparison) |

```yaml
# Example: Node must have "gpu" label with any value
matchExpressions:
  - key: gpu
    operator: Exists

# Example: Node must NOT be in zone us-east-1c
matchExpressions:
  - key: topology.kubernetes.io/zone
    operator: NotIn
    values:
    - us-east-1c
```

---

## Part 3: Pod Affinity and Anti-Affinity

### 3.1 Why Pod Affinity?

Control pod placement relative to other pods:
- **Pod Affinity**: "Schedule near pods with label X" (co-location)
- **Pod Anti-Affinity**: "Don't schedule near pods with label X" (spreading)

### 3.2 Pod Affinity Example

"Schedule this pod on the same node as pods with app=cache":

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-pod
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: cache
        topologyKey: kubernetes.io/hostname    # Same node
  containers:
  - name: web
    image: nginx
```

### 3.3 Pod Anti-Affinity Example

"Don't schedule on nodes that already have app=web pods":

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-pod
  labels:
    app: web
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: web
        topologyKey: kubernetes.io/hostname
  containers:
  - name: web
    image: nginx
```

> **War Story: The Scheduling Gridlock**
>
> In a large multi-tenant cluster, every team started adding required pod anti-affinity to ensure their microservices didn't share nodes with each other. Eventually, to schedule a simple 5-replica deployment, the scheduler had to find 5 completely empty nodes because every node already contained a pod that repelled the new ones. The cluster was only 20% utilized on CPU and memory, but couldn't schedule anything new. Over-constraining causes massive resource waste. Stick to soft constraints unless strictly necessary.

### 3.4 Topology Key

The `topologyKey` determines the "zone" for affinity:

| topologyKey | Meaning |
|-------------|---------|
| `kubernetes.io/hostname` | Same node |
| `topology.kubernetes.io/zone` | Same availability zone |
| `topology.kubernetes.io/region` | Same region |

```
┌────────────────────────────────────────────────────────────────┐
│            Anti-Affinity with Different topologyKeys           │
│                                                                 │
│   topologyKey: kubernetes.io/hostname                          │
│   → Pods spread across nodes (one per node)                    │
│                                                                 │
│   Node1: [web-1]    Node2: [web-2]    Node3: [web-3]          │
│                                                                 │
│   topologyKey: topology.kubernetes.io/zone                     │
│   → Pods spread across zones (one per zone)                    │
│                                                                 │
│   Zone-A            Zone-B            Zone-C                   │
│   [web-1]           [web-2]           [web-3]                  │
│   Node1,Node2       Node3,Node4       Node5,Node6              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Exam Tip**
>
> For spreading replicas across nodes, use pod anti-affinity with `topologyKey: kubernetes.io/hostname`. For spreading across zones for HA, use `topology.kubernetes.io/zone`.

---

## Part 4: Taints and Tolerations

### 4.1 How Taints Work

Taints are applied to **nodes** and repel pods unless the pod has a matching toleration.

```
┌────────────────────────────────────────────────────────────────┐
│                   Taints and Tolerations                        │
│                                                                 │
│   Node with taint: gpu=true:NoSchedule                         │
│   ┌─────────────────────────────────────────────┐              │
│   │                                             │              │
│   │  Regular Pod:      ❌ Cannot schedule       │              │
│   │                                             │              │
│   │  Pod with matching  ✅ Can schedule         │              │
│   │  toleration:                                │              │
│   │                                             │              │
│   └─────────────────────────────────────────────┘              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Stop and think**: An SRE needs to perform maintenance on a node. They want to prevent new pods from being scheduled there, but existing pods should keep running until they complete naturally. Which taint effect should they use -- `NoSchedule`, `PreferNoSchedule`, or `NoExecute`? What if they need to evict existing pods too?

### 4.2 Taint Effects

| Effect | Behavior |
|--------|----------|
| `NoSchedule` | Pods won't be scheduled (existing pods stay) |
| `PreferNoSchedule` | Soft version - avoid but allow if necessary |
| `NoExecute` | Evict existing pods, prevent new scheduling |

### 4.3 Managing Taints

```bash
# Add taint to node
kubectl taint nodes worker-1 gpu=true:NoSchedule

# View taints
kubectl describe node worker-1 | grep Taints

# Remove taint (note the minus sign)
kubectl taint nodes worker-1 gpu=true:NoSchedule-

# Multiple taints
kubectl taint nodes worker-1 dedicated=ml:NoSchedule
kubectl taint nodes worker-1 gpu=nvidia:NoSchedule
```

### 4.4 Adding Tolerations to Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  tolerations:
  - key: "gpu"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  containers:
  - name: cuda-app
    image: nvidia/cuda
```

### 4.5 Toleration Operators

| Operator | Meaning |
|----------|---------|
| `Equal` | Key and value must match |
| `Exists` | Key exists (any value matches) |

```yaml
# Match specific value
tolerations:
- key: "gpu"
  operator: "Equal"
  value: "nvidia"
  effect: "NoSchedule"

# Match any value for key
tolerations:
- key: "gpu"
  operator: "Exists"
  effect: "NoSchedule"

# Tolerate all taints (wildcard)
tolerations:
- operator: "Exists"
```

### 4.6 Common Taint Use Cases

| Use Case | Taint Example |
|----------|---------------|
| GPU nodes | `gpu=true:NoSchedule` |
| Dedicated nodes | `dedicated=team-a:NoSchedule` |
| Control plane nodes | `node-role.kubernetes.io/control-plane:NoSchedule` |
| Draining nodes | `node.kubernetes.io/unschedulable:NoSchedule` |

> **War Story: The Disappeared Pods**
>
> An SRE added `NoExecute` taint for maintenance instead of `NoSchedule`. Existing pods were immediately evicted, causing a production outage. Know your taint effects! Use `NoSchedule` to prevent new pods. Use `NoExecute` only when you want to evict running pods.

---

## Part 5: Pod Topology Spread Constraints

> **Pause and predict**: You have a 3-replica Deployment with pod anti-affinity using `requiredDuringSchedulingIgnoredDuringExecution` on `kubernetes.io/hostname`, but your cluster only has 2 nodes. What happens to the third replica?

### 5.1 Why Topology Spread?

Distribute pods evenly across failure domains:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: spread-pod
  labels:
    app: web
spec:
  topologySpreadConstraints:
  - maxSkew: 1                              # Max difference between zones
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule        # Hard requirement
    labelSelector:
      matchLabels:
        app: web
  containers:
  - name: nginx
    image: nginx
```

### 5.2 Parameters Explained

| Parameter | Description |
|-----------|-------------|
| `maxSkew` | Maximum allowed difference in pod count across domains |
| `topologyKey` | Label key defining domains (zone, node, etc.) |
| `whenUnsatisfiable` | `DoNotSchedule` (hard) or `ScheduleAnyway` (soft) |
| `labelSelector` | Which pods to count for distribution |

### 5.3 Visualization

```
┌────────────────────────────────────────────────────────────────┐
│              Topology Spread (maxSkew: 1)                       │
│                                                                 │
│   Zone A          Zone B          Zone C                       │
│   [pod][pod]      [pod]           [pod]                        │
│   Count: 2        Count: 1        Count: 1                     │
│                                                                 │
│   Max difference = 2-1 = 1 ≤ maxSkew ✓                         │
│                                                                 │
│   New pod arrives - where can it go?                           │
│   Zone A: 3 pods → difference 3-1=2 > maxSkew ❌               │
│   Zone B: 2 pods → difference 2-1=1 ≤ maxSkew ✓               │
│   Zone C: 2 pods → difference 2-1=1 ≤ maxSkew ✓               │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **War Story: The Un-Scalable Spread**
>
> An engineering team set a strict `maxSkew: 1` with `whenUnsatisfiable: DoNotSchedule` across 3 zones, but their cloud provider ran out of spot instances in `us-east-1c`. The cluster autoscaler couldn't add nodes in zone C. Because of the strict `maxSkew`, the scheduler refused to place pods in zones A and B (which had plenty of capacity) because it would make the skew greater than 1. Their deployment stalled completely. They learned to use `ScheduleAnyway` for soft spreading, or ensure autoscaler and instance types are highly available across all zones.

---

## Part 6: Scheduling Decision Flow

```
┌────────────────────────────────────────────────────────────────┐
│                   Scheduling Decision Flow                      │
│                                                                 │
│   Pod Created                                                   │
│       │                                                         │
│       ▼                                                         │
│   Filter Nodes                                                  │
│   ├── nodeSelector matches?                                    │
│   ├── Node affinity required matches?                          │
│   ├── Taints tolerated?                                        │
│   ├── Resources available?                                     │
│   ├── Pod anti-affinity satisfied?                             │
│   └── Topology spread constraints ok?                          │
│       │                                                         │
│       ▼                                                         │
│   Score Remaining Nodes                                         │
│   ├── Node affinity preferred                                  │
│   ├── Pod affinity preferred                                   │
│   └── Resource optimization                                    │
│       │                                                         │
│       ▼                                                         │
│   Select Highest Scoring Node                                   │
│       │                                                         │
│       ▼                                                         │
│   Bind Pod to Node                                              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

> **Production Trade-offs: The Cost of Control**
>
> - **Hard vs. Soft Affinity**: Hard rules (`required`) guarantee placement but increase the risk of Pending pods and failed deployments if capacity is constrained. Soft rules (`preferred`) maximize scheduling success but can lead to localized hotspots or performance degradation.
> - **Cross-AZ Network Costs**: Using topology spread across availability zones provides excellent high availability. However, if those pods communicate heavily with each other, cloud providers will charge you for cross-AZ data transfer.
> - **Taint and Toleration Overhead**: At scale, managing dozens of custom taints creates administrative bloat. It becomes difficult to onboard new applications because developers must remember to add a huge list of tolerations just to get their pods to run.

---

## Part 7: Common Production Patterns

### 7.1 Databases (Stateful Workloads)
Databases need fast I/O and must not run on the same physical hardware as their replicas.
- **Node Affinity**: Required affinity for nodes labeled `disk=ssd` or `instance-family=storage-optimized`.
- **Pod Anti-Affinity**: Required pod anti-affinity using `topologyKey: kubernetes.io/hostname` to ensure replicas never share a node (avoiding a single point of failure).

### 7.2 Web Tiers (Stateless Workloads)
Web servers need high availability and can run on almost any node.
- **Topology Spread**: Soft or hard constraints across `topology.kubernetes.io/zone` to survive datacenter outages.
- **Node Affinity**: Preferred affinity for newer, cost-effective instance types, falling back to older instances if necessary.

### 7.3 Batch Jobs (Cost Optimization)
Background processing jobs are fault-tolerant and perfect for preemptible or spot instances.
- **Tolerations**: Tolerate taints like `node.kubernetes.io/lifecycle=spot:NoSchedule`.
- **Node Affinity**: Required affinity to strictly run on spot nodes, keeping regular nodes free for critical user-facing services.

---

## Part 8: Troubleshooting Scheduling

### 8.1 Common Issues

| Symptom | Likely Cause | Debug Command |
|---------|--------------|---------------|
| Pending (no events) | No nodes match constraints | `kubectl describe pod` |
| Pending (Insufficient) | Resource shortage | Check node resources |
| Pending (Taints) | No toleration for taint | Check node taints, pod tolerations |
| Pending (Affinity) | No nodes match affinity rules | Simplify/remove affinity |

### 8.2 Debug Commands

```bash
# Check pod events
kubectl describe pod <pod-name> | grep -A10 Events

# Check node labels
kubectl get nodes --show-labels

# Check node taints
kubectl describe node <node> | grep Taints

# Check node resources
kubectl describe node <node> | grep -A10 "Allocated resources"

# Simulate scheduling
kubectl get pods -o wide  # See where pods landed
```

---

## Did You Know?

- **Control plane nodes** are tainted by default with `node-role.kubernetes.io/control-plane:NoSchedule`. That's why regular pods don't run there.

- **Affinity can be combined**. You can have nodeAffinity, podAffinity, and podAntiAffinity all on the same pod.

- **Multiple topologySpreadConstraints** are ANDed. All constraints must be satisfied.

- **DaemonSets ignore taints** by default for certain system taints. That's how they run on every node.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| nodeSelector typo | Pod stays Pending | Verify label exists on target node |
| Missing toleration | Pod can't schedule on tainted node | Add matching toleration |
| Wrong topologyKey | Affinity doesn't work as expected | Use correct label key |
| NoExecute instead of NoSchedule | Pods evicted unexpectedly | Use NoSchedule for new pods only |
| Anti-affinity too strict | Not enough nodes for all replicas | Use preferred or reduce replicas |

---

## Quiz

1. **Your team needs pods to run on SSD nodes but also accept NVMe nodes. A junior engineer used `nodeSelector: {disk: ssd}` but that excludes NVMe nodes. You need both SSD and NVMe without creating two separate Deployments. How do you solve this, and what type of affinity rule do you write?**
   <details>
   <summary>Answer</summary>
   Use `requiredDuringSchedulingIgnoredDuringExecution` node affinity with the `In` operator, which supports multiple values (OR logic). Write a `matchExpressions` rule with `key: disk, operator: In, values: [ssd, nvme]`. This schedules the pod on any node where the `disk` label is either `ssd` or `nvme`. `nodeSelector` can't do this because it only supports exact single-value matching. Node affinity also supports soft preferences via `preferredDuringSchedulingIgnoredDuringExecution`, which nodeSelector cannot express at all.
   </details>

2. **Your cluster has 3 nodes. Node-1 has taint `gpu=nvidia:NoSchedule`, node-2 has taint `dedicated=ml-team:NoSchedule`, and node-3 has no taints. You deploy a pod with only a toleration for `gpu=nvidia:NoSchedule`. On which node(s) can this pod be scheduled, and why?**
   <details>
   <summary>Answer</summary>
   The pod can schedule on node-1 and node-3. Node-1 has the `gpu=nvidia:NoSchedule` taint, which the pod tolerates, so it passes the taint filter. Node-3 has no taints, so any pod can schedule there (tolerations are only needed when taints exist). Node-2 has a taint `dedicated=ml-team:NoSchedule` that the pod does NOT tolerate, so it is excluded. A common misconception is that a toleration *requires* the taint to be present -- it doesn't. Tolerations are permissive: they allow scheduling on tainted nodes but don't prevent scheduling on untainted ones. To restrict a pod to only tainted nodes, combine tolerations with node affinity or nodeSelector.
   </details>

3. **You're deploying a critical web application across 3 availability zones for high availability. You have 6 replicas. Using pod anti-affinity with `requiredDuringSchedulingIgnoredDuringExecution` and `topologyKey: topology.kubernetes.io/zone`, you notice some pods stay Pending. Why? What would you use instead for a more flexible approach?**
   <details>
   <summary>Answer</summary>
   With `required` anti-affinity by zone and 6 replicas across 3 zones, the first 3 pods schedule fine (one per zone). But the 4th pod cannot find a zone without an existing pod, so it stays Pending -- the hard constraint means "never place two pods in the same zone." Switch to `preferredDuringSchedulingIgnoredDuringExecution` (soft preference) or use `topologySpreadConstraints` with `maxSkew: 1`, which distributes pods evenly (2 per zone for 6 replicas) rather than requiring strict uniqueness. Topology spread constraints are generally better for HA because they balance pods across domains instead of imposing a hard one-per-domain limit.
   </details>

4. **During a CKA exam scenario, you see a pod stuck in Pending with the event: `0/3 nodes are available: 2 insufficient cpu, 1 node(s) had taint {node-role.kubernetes.io/control-plane: NoSchedule}`. Walk through your diagnosis. What are the two separate issues, and what are your options to resolve each?**
   <details>
   <summary>Answer</summary>
   There are two distinct issues. First, 2 worker nodes don't have enough allocatable CPU for this pod's resource requests -- check with `kubectl describe node` and compare the pod's `requests.cpu` against the node's available capacity. Fix by reducing the pod's CPU request, scaling down other workloads on those nodes, or adding nodes with more capacity. Second, the third node is a control plane node with the standard `NoSchedule` taint. Fix by adding a toleration for `node-role.kubernetes.io/control-plane` (only appropriate for infrastructure pods, not application workloads) or by adding more worker nodes. In production, the control plane node should generally stay reserved for system components.
   </details>

---

## Hands-On Exercise

**Task**: Practice all scheduling techniques.

**Steps**:

### Part A: nodeSelector

1. **Label a node and use nodeSelector**:
```bash
# Get a node name
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Label the node
kubectl label node $NODE disk=ssd

# Create pod with nodeSelector
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: ssd-pod
spec:
  nodeSelector:
    disk: ssd
  containers:
  - name: nginx
    image: nginx
EOF

# Verify placement
kubectl get pod ssd-pod -o wide

# Cleanup
kubectl delete pod ssd-pod
kubectl label node $NODE disk-
```

### Part B: Taints and Tolerations

2. **Add taint and create pod with toleration**:
```bash
# Taint the node
kubectl taint nodes $NODE dedicated=special:NoSchedule

# Try to create pod without toleration
kubectl run no-toleration --image=nginx

# Check - should be Pending or on different node
kubectl get pod no-toleration -o wide

# Create pod with toleration
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: with-toleration
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "special"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
EOF

# Verify placement
kubectl get pod with-toleration -o wide

# Cleanup
kubectl delete pod no-toleration with-toleration
kubectl taint nodes $NODE dedicated-
```

### Part C: Pod Anti-Affinity

3. **Spread pods across nodes**:
```bash
cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spread-deploy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spread
  template:
    metadata:
      labels:
        app: spread
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: spread
              topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx
        image: nginx
EOF

# Check pod distribution
kubectl get pods -l app=spread -o wide

# Cleanup
kubectl delete deployment spread-deploy
```

**Success Criteria**:
- [ ] Can use nodeSelector
- [ ] Can add/remove node taints
- [ ] Can add tolerations to pods
- [ ] Understand affinity vs anti-affinity
- [ ] Can troubleshoot scheduling issues

---

## Practice Drills

### Drill 1: nodeSelector (Target: 3 minutes)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Label node
kubectl label node $NODE env=production

# Create pod with nodeSelector
kubectl run selector-test --image=nginx --dry-run=client -o yaml | \
  kubectl patch --dry-run=client -o yaml -f - \
  -p '{"spec":{"nodeSelector":{"env":"production"}}}' | kubectl apply -f -

# Or simpler - just use YAML
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: selector-test
spec:
  nodeSelector:
    env: production
  containers:
  - name: nginx
    image: nginx
EOF

# Verify
kubectl get pod selector-test -o wide

# Cleanup
kubectl delete pod selector-test
kubectl label node $NODE env-
```

### Drill 2: Taints (Target: 5 minutes)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Add taint
kubectl taint nodes $NODE app=critical:NoSchedule

# View taint
kubectl describe node $NODE | grep Taints

# Pod without toleration - will be Pending or elsewhere
kubectl run no-tol --image=nginx
kubectl get pod no-tol -o wide

# Pod with toleration
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: with-tol
spec:
  tolerations:
  - key: "app"
    operator: "Equal"
    value: "critical"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
EOF

kubectl get pod with-tol -o wide

# Cleanup
kubectl delete pod no-tol with-tol
kubectl taint nodes $NODE app-
```

### Drill 3: Node Affinity (Target: 5 minutes)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE size=large

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: affinity-test
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: size
            operator: In
            values:
            - large
            - xlarge
  containers:
  - name: nginx
    image: nginx
EOF

kubectl get pod affinity-test -o wide

# Cleanup
kubectl delete pod affinity-test
kubectl label node $NODE size-
```

### Drill 4: Pod Anti-Affinity (Target: 5 minutes)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anti-affinity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anti-test
  template:
    metadata:
      labels:
        app: anti-test
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: anti-test
            topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx
        image: nginx
EOF

# Check distribution (each pod on different node)
kubectl get pods -l app=anti-test -o wide

# Cleanup
kubectl delete deployment anti-affinity
```

### Drill 5: Troubleshooting - Pending Pod (Target: 5 minutes)

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

# Create impossible scenario
kubectl taint nodes $NODE impossible=true:NoSchedule

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pending-pod
spec:
  nodeSelector:
    nonexistent: label
  containers:
  - name: nginx
    image: nginx
EOF

# Diagnose
kubectl get pod pending-pod
kubectl describe pod pending-pod | grep -A10 Events

# YOUR TASK: Why is it Pending? Fix it.

# Cleanup
kubectl delete pod pending-pod
kubectl taint nodes $NODE impossible-
```

<details>
<summary>Solution</summary>

The pod is pending for two reasons:
1. nodeSelector requires label `nonexistent=label` which no node has
2. All nodes have taint that the pod doesn't tolerate

Fix by either:
- Adding the label to a node: `kubectl label node $NODE nonexistent=label`
- Adding toleration and removing nodeSelector

</details>

### Drill 6: Challenge - Complex Scheduling

Create a pod that:
1. Must run on nodes with label `tier=frontend`
2. Prefers nodes with label `zone=us-east-1a`
3. Tolerates taint `frontend=true:NoSchedule`

```bash
# YOUR TASK: Create this pod
```

<details>
<summary>Solution</summary>

```bash
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl label node $NODE tier=frontend zone=us-east-1a
kubectl taint nodes $NODE frontend=true:NoSchedule

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: complex-schedule
spec:
  tolerations:
  - key: "frontend"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tier
            operator: In
            values:
            - frontend
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - us-east-1a
  containers:
  - name: nginx
    image: nginx
EOF

kubectl get pod complex-schedule -o wide

# Cleanup
kubectl delete pod complex-schedule
kubectl label node $NODE tier- zone-
kubectl taint nodes $NODE frontend-
```

</details>

---

## Next Module

[Module 2.7: ConfigMaps & Secrets](../module-2.7-configmaps-secrets/) - Application configuration management.
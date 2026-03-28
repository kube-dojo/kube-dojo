---
title: "Module 1.4: Cluster Scaling & Compute Optimization"
slug: platform/disciplines/finops/module-1.4-compute-optimization
sidebar:
  order: 5
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 3h

## Prerequisites

Before starting this module:
- **Required**: [Module 1.3: Workload Rightsizing](module-1.3-rightsizing/) — VPA, rightsizing workflows
- **Required**: Understanding of Kubernetes node pools and autoscaling
- **Required**: Familiarity with Karpenter or Cluster Autoscaler concepts
- **Recommended**: AWS experience (Karpenter examples use AWS terminology)
- **Recommended**: Understanding of EC2 instance types and pricing

---

## Why This Module Matters

Module 1.3 taught you to rightsize individual workloads — giving each Pod exactly the resources it needs. But even with perfectly rightsized Pods, your cluster can still waste enormous amounts of money if the *nodes* underneath those Pods are inefficient.

Consider this scenario:

```
Before Node Optimization:
┌──────────────────────────────────────────────────┐
│ Node 1 (m6i.2xlarge - 8 vCPU, 32GB - $285/mo)   │
│ ┌──────────┐ ┌──────────┐                        │
│ │ Pod A    │ │ Pod B    │        Empty space     │
│ │ 500m/2Gi │ │ 300m/1Gi │        = 7.2 CPU idle │
│ └──────────┘ └──────────┘        = 29 GB idle   │
│                                   ($253 wasted)  │
│──────────────────────────────────────────────────│
│ Node 2 (m6i.2xlarge - 8 vCPU, 32GB - $285/mo)   │
│ ┌──────────┐                                     │
│ │ Pod C    │                     Empty space     │
│ │ 200m/512M│                     = 7.8 CPU idle │
│ └──────────┘                     = 31.5 GB idle │
│                                   ($277 wasted)  │
│──────────────────────────────────────────────────│
│ Node 3 (m6i.2xlarge - 8 vCPU, 32GB - $285/mo)   │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│ │ Pod D    │ │ Pod E    │ │ Pod F    │          │
│ │ 1CPU/4Gi │ │ 1CPU/4Gi │ │ 500m/2Gi│          │
│ └──────────┘ └──────────┘ └──────────┘          │
│                              5.5 CPU / 22GB idle│
└──────────────────────────────────────────────────┘
Total: 3 nodes × $285 = $855/mo
Utilization: ~15% CPU, ~14% memory
```

After optimization (consolidation + right-sized nodes):

```
After Node Optimization:
┌──────────────────────────────────────────────────┐
│ Node 1 (m6i.xlarge - 4 vCPU, 16GB - $140/mo)    │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐│
│ │ A   │ │ B   │ │ C   │ │ D   │ │ E   │ │ F   ││
│ │500m │ │300m │ │200m │ │1CPU │ │1CPU │ │500m ││
│ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘│
│ Utilization: 87.5% CPU, 84% memory              │
└──────────────────────────────────────────────────┘
Total: 1 node × $140 = $140/mo
Savings: $715/mo (84% reduction)
```

This module covers the tools and strategies that make this consolidation happen automatically: **Karpenter, Cluster Autoscaler, Spot instances, bin-packing, and ARM migration**.

---

## Did You Know?

- **Karpenter can provision a new node in under 60 seconds** — compared to Cluster Autoscaler's typical 3-5 minutes. Karpenter talks directly to the EC2 API instead of going through Auto Scaling Groups, eliminating an entire layer of indirection.

- **AWS reports that customers using Graviton (ARM) instances save an average of 20% on compute costs** while getting up to 40% better price-performance. Since most containerized workloads are already compiled for multiple architectures (via multi-arch images), migrating to ARM is often as simple as changing a node selector.

- **Spot instance interruption rates vary dramatically by instance type.** While the average across all types is roughly 5-7% per month, some instance families (like older m5 types) see rates below 2%, while GPU instances can exceed 15%. Diversifying across multiple instance types and availability zones is the key to reliable Spot usage.

---

## Cluster Autoscaler vs Karpenter

### Cluster Autoscaler (CAS)

The original Kubernetes node autoscaler. Works with cloud provider Auto Scaling Groups (ASGs).

```
Cluster Autoscaler Workflow:
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Pod is   │────▶│ CAS sees │────▶│ CAS asks │────▶│ ASG adds │
│ Pending  │     │ unschedul│     │ ASG to   │     │ a node   │
│ (no node)│     │ -able pod│     │ scale up │     │ (3-5 min)│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

**How it works**:
1. Pods become `Pending` because no node has enough capacity
2. CAS detects pending pods and calculates which node group could fit them
3. CAS increases the desired count of the matching ASG
4. ASG launches a new EC2 instance
5. The instance joins the cluster and the pod is scheduled

**Limitations**:
- Must pre-define node groups (ASGs) with fixed instance types
- Can't mix instance types within a node group (without managed node groups)
- Slow: ASG → EC2 → kubelet bootstrap → ready = 3-5 minutes
- Scale-down is conservative (10+ minutes by default)
- No built-in Spot diversification

### Karpenter

The next-generation Kubernetes node provisioner. Replaces ASGs entirely.

```
Karpenter Workflow:
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Pod is   │────▶│ Karpenter│────▶│ EC2 Fleet│
│ Pending  │     │ calculates     │ API spins│
│ (no node)│     │ optimal  │     │ up node  │
│          │     │ instance │     │ (~1 min) │
└──────────┘     └──────────┘     └──────────┘
```

**How it works**:
1. Pods become `Pending`
2. Karpenter evaluates all pending pods' requirements (CPU, memory, GPU, architecture, topology)
3. Karpenter selects the optimal instance type from a pool of candidates
4. Karpenter calls the EC2 Fleet API directly (bypassing ASGs)
5. Node joins the cluster in ~60 seconds

**Advantages over CAS**:
- No pre-defined node groups needed
- Selects from hundreds of instance types automatically
- Bin-packs pods onto right-sized nodes
- Built-in Spot diversification and fallback
- Faster provisioning (EC2 Fleet API vs ASG)
- Native consolidation (replaces under-utilized nodes)

### Comparison

| Feature | Cluster Autoscaler | Karpenter |
|---------|-------------------|-----------|
| Node provisioning | Via ASGs (pre-defined) | Direct EC2 API (dynamic) |
| Instance selection | Fixed per node group | Dynamic, any compatible type |
| Provisioning speed | 3-5 minutes | ~60 seconds |
| Spot support | Manual ASG config | Built-in with fallback |
| Bin-packing | Basic (fits into existing groups) | Advanced (picks optimal size) |
| Consolidation | Scale-down only | Replace + consolidate |
| Multi-arch (ARM) | Separate node groups | Automatic with constraints |
| Cloud support | AWS, GCP, Azure | AWS (native), Azure (beta) |
| Maturity | Mature, battle-tested | Rapidly maturing (CNCF Sandbox) |

### When to Use Each

| Scenario | Recommendation |
|----------|---------------|
| AWS EKS cluster | Karpenter (first choice) |
| GKE cluster | Cluster Autoscaler (GKE Autopilot handles it) |
| AKS cluster | Cluster Autoscaler or Karpenter (Azure preview) |
| On-premises | Cluster Autoscaler (if supported by your platform) |
| Need maximum cost optimization | Karpenter (better bin-packing and Spot) |
| Want simplicity and stability | Cluster Autoscaler (simpler to understand) |

---

## Karpenter Deep Dive

### NodePool Configuration

Karpenter uses `NodePool` resources (formerly Provisioners) to define what kinds of nodes it can create:

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    metadata:
      labels:
        team: shared
    spec:
      requirements:
        # Instance categories
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]     # Compute, General, Memory optimized

        # Instance sizes (avoid tiny and huge)
        - key: karpenter.k8s.aws/instance-size
          operator: In
          values: ["medium", "large", "xlarge", "2xlarge"]

        # Capacity type — prefer Spot, fall back to On-Demand
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]

        # Architecture — allow both x86 and ARM
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]

      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default

  # Disruption settings
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s

  # Budget limits
  limits:
    cpu: "100"           # Max 100 CPU cores across all nodes
    memory: "400Gi"      # Max 400 GB RAM

  # Weight for priority (higher = preferred)
  weight: 50
```

### EC2NodeClass

Defines the AWS-specific configuration for nodes:

```yaml
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiSelectorTerms:
    - alias: "bottlerocket@latest"     # Optimized container OS

  subnetSelectorTerms:
    - tags:
        kubernetes.io/cluster/my-cluster: "*"

  securityGroupSelectorTerms:
    - tags:
        kubernetes.io/cluster/my-cluster: owned

  blockDeviceMappings:
    - deviceName: /dev/xvdb           # Bottlerocket data volume (container storage)
      ebs:
        volumeSize: 50Gi
        volumeType: gp3
        encrypted: true
```

### Spot Priority with On-Demand Fallback

The real power of Karpenter for cost optimization: use Spot by default, fall back to On-Demand only when Spot isn't available.

```yaml
# NodePool 1: Spot (higher weight = preferred)
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: spot-preferred
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-size
          operator: In
          values: ["large", "xlarge", "2xlarge", "4xlarge"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  weight: 80               # Higher weight — preferred
  limits:
    cpu: "80"
---
# NodePool 2: On-Demand (lower weight = fallback)
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: on-demand-fallback
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-size
          operator: In
          values: ["large", "xlarge", "2xlarge"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  weight: 20               # Lower weight — fallback only
  limits:
    cpu: "40"
```

---

## Node Consolidation

Consolidation is Karpenter's killer feature for cost savings. It continuously evaluates whether the current set of nodes is optimal, and replaces or removes nodes that are wasteful.

### How Consolidation Works

```
Before Consolidation:
┌────────────────────┐  ┌────────────────────┐
│ Node A (xlarge)    │  │ Node B (xlarge)    │
│ 4 CPU, 16 GB      │  │ 4 CPU, 16 GB      │
│                    │  │                    │
│ ┌─────┐ ┌─────┐   │  │ ┌─────┐           │
│ │Pod 1│ │Pod 2│   │  │ │Pod 3│ (mostly   │
│ │1CPU │ │500m │   │  │ │300m │  empty)    │
│ └─────┘ └─────┘   │  │ └─────┘           │
│ Used: 1.5/4 CPU   │  │ Used: 0.3/4 CPU   │
│ Cost: $140/mo     │  │ Cost: $140/mo      │
└────────────────────┘  └────────────────────┘
Total: $280/mo, 1.8 CPU used of 8 available (22%)

After Consolidation:
┌────────────────────┐
│ Node C (large)     │  Karpenter replaced 2 xlarge
│ 2 CPU, 8 GB       │  with 1 large
│                    │
│ ┌─────┐┌─────┐┌────┐│
│ │Pod 1││Pod 2││Pod3││
│ │1CPU ││500m ││300m││
│ └─────┘└─────┘└────┘│
│ Used: 1.8/2 CPU   │
│ Cost: $70/mo       │
└────────────────────┘
Total: $70/mo, 1.8 CPU used of 2 available (90%)
Savings: $210/mo (75%)
```

### Consolidation Policies

```yaml
spec:
  disruption:
    # Option 1: Consolidate when nodes are empty or under-utilized
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s     # How long to wait before acting

    # Option 2: Consolidate only when nodes are completely empty
    # consolidationPolicy: WhenEmpty
    # consolidateAfter: 60s

    # Disruption budgets — limit how many nodes can be disrupted at once
    budgets:
    - nodes: "10%"             # Max 10% of nodes disrupted simultaneously
    - nodes: "0"               # Block disruption during these times
      schedule: "0 9 * * 1-5"  # No disruption 9 AM weekdays
      duration: 8h             # For 8 hours (business hours)
```

### Consolidation Considerations

| Concern | Mitigation |
|---------|-----------|
| Pod disruption during consolidation | Use PodDisruptionBudgets (PDBs) |
| Data loss on local storage | Avoid local storage or use `do-not-disrupt` annotation |
| Stateful workloads | Use `karpenter.sh/do-not-disrupt: "true"` annotation |
| Too frequent consolidation | Set `consolidateAfter` to 5-10 minutes |
| Business-hours protection | Use disruption budget schedules |

---

## Bin-Packing Strategies

Bin-packing is the art of fitting pods onto nodes with minimal wasted space — like a game of Tetris.

### Default Kubernetes Scheduling

The default scheduler (`kube-scheduler`) uses a `MostRequestedPriority` or `LeastRequestedPriority` scoring function:

```
LeastRequestedPriority (default):
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Node A   │  │ Node B   │  │ Node C   │
│ 60% full │  │ 30% full │  │ 80% full │
│          │  │  ← Pod   │  │          │
│          │  │  goes    │  │          │
│          │  │  HERE    │  │          │
└──────────┘  └──────────┘  └──────────┘
Spreads pods across nodes (good for availability)
Bad for cost (keeps more nodes active)

MostRequestedPriority:
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Node A   │  │ Node B   │  │ Node C   │
│ 60% full │  │ 30% full │  │ 80% full │
│          │  │          │  │  ← Pod   │
│          │  │          │  │  goes    │
│          │  │          │  │  HERE    │
└──────────┘  └──────────┘  └──────────┘
Packs pods onto fullest nodes (good for cost)
Node B can potentially be removed
```

### Cost-Optimized Scheduler Profile

```yaml
# In kube-scheduler configuration
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: cost-optimized
  plugins:
    score:
      enabled:
      - name: NodeResourcesFit
        weight: 2     # Higher weight for resource packing
      disabled:
      - name: NodeResourcesBalancedAllocation  # Disable spreading
  pluginConfig:
  - name: NodeResourcesFit
    args:
      scoringStrategy:
        type: MostAllocated    # Pack pods tightly
        resources:
        - name: cpu
          weight: 1
        - name: memory
          weight: 1
```

### Karpenter's Bin-Packing

Karpenter naturally bin-packs because it selects the optimal instance size for pending pods:

```
Pending pods need: 2.5 CPU, 6 GB total

Cluster Autoscaler (ASG with m6i.2xlarge):
  → Adds m6i.2xlarge (8 CPU, 32 GB) = $285/mo
  → Utilization: 31% CPU, 19% memory
  → Wasted: $196/mo

Karpenter (flexible instance selection):
  → Selects m6i.large (2 CPU, 8 GB) = $70/mo  ← too small
  → Selects c6i.xlarge (4 CPU, 8 GB) = $122/mo ← fits!
  → Utilization: 63% CPU, 75% memory
  → Wasted: $45/mo

Savings: $163/mo per node decision
```

---

## Spot Instance Strategies

### Spot Basics for Kubernetes

Spot instances offer 60-90% savings but can be reclaimed with 2 minutes' notice. The key is diversification and graceful handling.

### Diversification Strategy

Never rely on a single instance type for Spot:

```yaml
# Karpenter automatically diversifies, but you control the pool
spec:
  template:
    spec:
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]          # 3 categories
        - key: karpenter.k8s.aws/instance-size
          operator: In
          values: ["large", "xlarge", "2xlarge"]  # 3 sizes
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]       # 2 architectures
        # = 3 × 3 × 2 = 18+ instance type candidates
        # Karpenter picks from the cheapest available
```

### Handling Spot Interruptions

```yaml
# Ensure workloads handle interruptions gracefully
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
spec:
  replicas: 4
  template:
    spec:
      # Spread across nodes for Spot resilience
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: payment-api
      containers:
      - name: api
        image: payments/api:v2
        # Handle SIGTERM gracefully
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
      terminationGracePeriodSeconds: 30
---
# PDB ensures at least 3 replicas always running
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: payment-api-pdb
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: payment-api
```

### What Should and Shouldn't Run on Spot

| Workload Type | Spot Suitable? | Why |
|---------------|---------------|-----|
| Stateless APIs (with replicas > 2) | Yes | Replicas provide redundancy |
| CI/CD runners | Yes | Jobs can be retried |
| Batch processing | Yes | Checkpointable, retriable |
| ML training (with checkpointing) | Yes | Checkpoints prevent data loss |
| Databases / StatefulSets | No | Data loss risk, replication lag |
| Single-replica services | No | No redundancy during interruption |
| Long-running critical jobs | Depends | Need checkpointing and retry logic |

---

## ARM (Graviton) Migration

### Why ARM for Cost Savings

AWS Graviton processors (ARM architecture) offer:
- **20% lower cost** than equivalent x86 instances
- **Up to 40% better price-performance** for many workloads
- **Lower energy consumption** (sustainability bonus)

```
Price Comparison:
┌─────────────────────────────────────────────────┐
│ Instance Type    │ Arch │  $/hr  │ Monthly(730h)│
├──────────────────┼──────┼────────┼──────────────│
│ m6i.xlarge       │ x86  │ $0.192 │ $140.16      │
│ m6g.xlarge       │ ARM  │ $0.154 │ $112.42      │
│ Savings          │      │  20%   │ $27.74/mo    │
│──────────────────┼──────┼────────┼──────────────│
│ c6i.2xlarge      │ x86  │ $0.340 │ $248.20      │
│ c6g.2xlarge      │ ARM  │ $0.272 │ $198.56      │
│ Savings          │      │  20%   │ $49.64/mo    │
└─────────────────────────────────────────────────┘
```

### Migrating Workloads to ARM

Most containerized workloads work on ARM if you use multi-arch images:

```bash
# Check if your image supports multiple architectures
docker manifest inspect nginx:alpine | jq '.manifests[].platform'
```

```json
{ "architecture": "amd64", "os": "linux" }
{ "architecture": "arm64", "os": "linux" }
```

If the image supports `arm64`, you can schedule it on Graviton nodes immediately.

### Building Multi-Arch Images

```bash
# Build multi-arch image using Docker buildx
docker buildx create --name multiarch --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag myapp:v1.0 \
  --push .
```

### Karpenter ARM Configuration

```yaml
# Allow Karpenter to choose ARM instances when cheaper
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]   # Both architectures
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
```

Karpenter will automatically select Graviton instances when they're cheaper and pods don't have architecture-specific constraints.

---

## DaemonSet Overhead

DaemonSets run on every node — and they eat into capacity that could run your workloads. This overhead matters more as you add more nodes.

### Calculating DaemonSet Tax

```bash
# List all DaemonSets and their resource requests
kubectl get ds -A -o custom-columns=\
NAMESPACE:.metadata.namespace,\
NAME:.metadata.name,\
CPU_REQ:.spec.template.spec.containers[0].resources.requests.cpu,\
MEM_REQ:.spec.template.spec.containers[0].resources.requests.memory
```

Typical DaemonSet overhead per node:

| DaemonSet | CPU Request | Memory Request |
|-----------|------------|----------------|
| kube-proxy | 100m | 128Mi |
| aws-node (VPC CNI) | 25m | 128Mi |
| ebs-csi-node | 10m | 40Mi |
| fluent-bit (logging) | 100m | 128Mi |
| datadog-agent | 200m | 256Mi |
| node-exporter | 50m | 64Mi |
| **Total per node** | **485m** | **744Mi** |

On a `m6i.large` (2 CPU, 8 GB):
- DaemonSets consume **24% of CPU** and **9% of memory** before any workload pods
- Only **1515m CPU** and **7.3 GB** available for your actual workloads
- On a 20-node cluster: **9.7 CPU** and **14.5 GB** consumed by DaemonSets alone

### Reducing DaemonSet Overhead

| Strategy | Impact | Effort |
|----------|--------|--------|
| Use fewer, larger nodes | DaemonSet overhead is per-node; fewer nodes = less waste | Low |
| Rightsize DaemonSet requests | Many DaemonSets over-request | Medium |
| Replace DaemonSets with sidecars | Kubernetes 1.28+ sidecar containers | High |
| Use managed alternatives | AWS CloudWatch instead of fluent-bit DaemonSet | Medium |
| Consolidate agents | One observability agent instead of three | Medium |

```
DaemonSet overhead impact by node size:
┌──────────────────────────────────────────────────────┐
│ Node Type    │ Total CPU │ DS Overhead │ % Overhead │
├──────────────┼───────────┼─────────────┼────────────│
│ m6i.medium   │  1 CPU    │   485m      │    49%     │ ← terrible
│ m6i.large    │  2 CPU    │   485m      │    24%     │
│ m6i.xlarge   │  4 CPU    │   485m      │    12%     │
│ m6i.2xlarge  │  8 CPU    │   485m      │     6%     │
│ m6i.4xlarge  │ 16 CPU    │   485m      │     3%     │ ← efficient
└──────────────────────────────────────────────────────┘
```

**Takeaway**: With significant DaemonSet overhead, fewer large nodes are more cost-effective than many small nodes.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Using only one instance type | Default ASG config | Enable Karpenter or diversify ASGs across 5+ types |
| Running all workloads on On-Demand | Risk aversion | Move stateless workloads to Spot (start with dev/staging) |
| Too many small nodes | "Blast radius" concerns | Use PDBs instead; larger nodes are more cost-efficient |
| Ignoring DaemonSet overhead | Invisible cost | Calculate per-node overhead and factor into node sizing |
| No consolidation enabled | Default Karpenter is conservative | Enable `WhenEmptyOrUnderutilized` consolidation |
| Spot without diversification | Single instance type Spot | Use 10+ instance types across 3+ categories |
| Skipping PDBs on Spot workloads | "It'll be fine" | Always set PDBs; Spot interruptions happen |
| Not using ARM/Graviton | "Our code doesn't work on ARM" | Test it — most containers already support multi-arch |

---

## Quiz

### Question 1
What is the key architectural difference between Cluster Autoscaler and Karpenter?

<details>
<summary>Show Answer</summary>

**Cluster Autoscaler** works through Auto Scaling Groups (ASGs). You pre-define node groups with specific instance types, and CAS scales those groups up or down. It can only add instances of the types configured in each ASG.

**Karpenter** bypasses ASGs entirely and calls the EC2 Fleet API directly. It evaluates pending pods' requirements and selects the optimal instance type from a large pool of candidates — potentially choosing an instance type you never explicitly configured. This makes it faster (~60s vs 3-5 minutes) and more cost-efficient (right-sized instance selection, better bin-packing).
</details>

### Question 2
Why are fewer, larger nodes generally more cost-efficient than many small nodes in Kubernetes?

<details>
<summary>Show Answer</summary>

**DaemonSet overhead.** Every node runs the same set of DaemonSets (kube-proxy, CNI, logging, monitoring, etc.) regardless of node size. On a small node (2 CPU), DaemonSets might consume 25% of capacity. On a large node (16 CPU), the same DaemonSets consume only 3%. Additionally, Kubernetes reserves resources on each node for system components (kubelet, OS). Fewer, larger nodes mean less total overhead and more capacity available for actual workloads.
</details>

### Question 3
A team wants to run their payment processing service on Spot instances to save money. What's your advice?

<details>
<summary>Show Answer</summary>

It depends on the architecture:

**Yes, if**: The service runs 3+ replicas, is stateless, handles SIGTERM gracefully, and has PodDisruptionBudgets ensuring minimum availability. Spread replicas across multiple AZs and instance types. Use Spot for the majority of replicas, keep 1-2 on On-Demand as a baseline.

**No, if**: It's a single replica, maintains critical in-memory state, or has long-running transactions that can't be interrupted. Payment processing often has strict reliability requirements — a 2-minute interruption could mean failed transactions.

**Compromise**: Run the stateless API tier on Spot, but keep the database and any stateful components on On-Demand.
</details>

### Question 4
Karpenter's consolidation policy is set to `WhenEmptyOrUnderutilized`. Explain what happens when a node is only 15% utilized.

<details>
<summary>Show Answer</summary>

Karpenter detects that the node is under-utilized (15%) and evaluates whether the pods on that node could fit onto other existing nodes — or onto a smaller, cheaper replacement node. If consolidation is possible:

1. Karpenter cordons the node (prevents new pods from scheduling)
2. It respects PodDisruptionBudgets and `do-not-disrupt` annotations
3. Pods are drained and rescheduled onto other nodes (or a new smaller node)
4. The under-utilized node is terminated
5. This happens after `consolidateAfter` duration (e.g., 30 seconds of being under-utilized)

The result: a tighter, more cost-efficient cluster with higher average utilization.
</details>

### Question 5
Your cluster runs 30 `m6i.xlarge` (x86) nodes. A colleague suggests migrating to `m6g.xlarge` (Graviton/ARM) for 20% savings. What steps would you take?

<details>
<summary>Show Answer</summary>

1. **Audit container images**: Check which images support `linux/arm64` using `docker manifest inspect`. Most official images (nginx, redis, postgres, etc.) already support multi-arch.

2. **Identify blockers**: Find images that are x86-only. These need multi-arch builds (`docker buildx`) or vendor updates.

3. **Start with non-critical workloads**: Move development and staging to Graviton first.

4. **Add ARM to Karpenter NodePool**: Set `kubernetes.io/arch` to `["amd64", "arm64"]` — Karpenter will automatically prefer cheaper Graviton instances.

5. **Use node affinity for testing**: Schedule specific workloads on ARM nodes while keeping the rest on x86.

6. **Monitor performance**: Compare latency, throughput, and error rates between x86 and ARM pods.

7. **Gradual rollout**: Move production workloads one service at a time, starting with the easiest (stateless, multi-arch image available).

Expected savings on 30 nodes: ~$835/month (30 * $27.74).
</details>

---

## Hands-On Exercise: Karpenter with Spot Priority and Consolidation

This exercise demonstrates Karpenter's cost optimization features using a local simulation. Since Karpenter requires AWS, we'll simulate the key concepts and provide AWS commands for real clusters.

### Part A: Understanding Bin-Packing (Local)

```bash
# Create a kind cluster
cat > /tmp/kind-compute.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        system-reserved: "cpu=100m,memory=128Mi"
- role: worker
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        system-reserved: "cpu=100m,memory=128Mi"
- role: worker
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        system-reserved: "cpu=100m,memory=128Mi"
EOF

kind create cluster --name compute-lab --config /tmp/kind-compute.yaml

# Label nodes to simulate different instance types
kubectl label node compute-lab-worker instance-type=m6i.xlarge cost-per-hour=0.192
kubectl label node compute-lab-worker2 instance-type=c6g.large cost-per-hour=0.068
kubectl label node compute-lab-worker3 instance-type=m6g.xlarge cost-per-hour=0.154
```

### Deploy workloads and analyze placement:

```bash
# Deploy workloads of varying sizes
kubectl create namespace compute-lab

# Small workload (should be packed tightly)
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: small-api
  namespace: compute-lab
spec:
  replicas: 6
  selector:
    matchLabels:
      app: small-api
  template:
    metadata:
      labels:
        app: small-api
    spec:
      containers:
      - name: api
        image: nginx:alpine
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "100m"
            memory: "128Mi"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medium-service
  namespace: compute-lab
spec:
  replicas: 3
  selector:
    matchLabels:
      app: medium-service
  template:
    metadata:
      labels:
        app: medium-service
    spec:
      containers:
      - name: service
        image: nginx:alpine
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heavy-worker
  namespace: compute-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: heavy-worker
  template:
    metadata:
      labels:
        app: heavy-worker
    spec:
      containers:
      - name: worker
        image: nginx:alpine
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
EOF

kubectl rollout status deployment/small-api -n compute-lab
kubectl rollout status deployment/medium-service -n compute-lab
kubectl rollout status deployment/heavy-worker -n compute-lab
```

### Analyze pod placement and node utilization:

```bash
cat > /tmp/analyze_placement.sh << 'SCRIPT'
#!/bin/bash
echo "============================================"
echo "  Node Utilization & Pod Placement Report"
echo "============================================"
echo ""

for node in $(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o name); do
  node_name=$(echo "$node" | cut -d/ -f2)
  instance=$(kubectl get "$node" -o jsonpath='{.metadata.labels.instance-type}' 2>/dev/null)
  cost=$(kubectl get "$node" -o jsonpath='{.metadata.labels.cost-per-hour}' 2>/dev/null)

  echo "--- $node_name ($instance @ \$$cost/hr) ---"

  # Get pods on this node
  kubectl get pods --all-namespaces --field-selector="spec.nodeName=$node_name" \
    -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,CPU:.spec.containers[0].resources.requests.cpu,MEMORY:.spec.containers[0].resources.requests.memory \
    2>/dev/null | grep -v "^kube-system"

  # Calculate total requests on this node
  total_cpu=$(kubectl get pods --all-namespaces --field-selector="spec.nodeName=$node_name" -o json | \
    python3 -c "
import json, sys
data = json.load(sys.stdin)
total = 0
for pod in data.get('items', []):
    for c in pod['spec']['containers']:
        req = c.get('resources', {}).get('requests', {}).get('cpu', '0')
        if 'm' in str(req): total += int(str(req).replace('m', ''))
        elif req != '0': total += int(float(req) * 1000)
print(total)" 2>/dev/null)

  echo "  Total CPU requested: ${total_cpu}m"
  echo ""
done

echo "--- Summary ---"
echo "Optimization questions:"
echo "  1. Are pods spread evenly or packed tightly?"
echo "  2. Could we remove a node if pods were consolidated?"
echo "  3. Which node has the most idle capacity?"
SCRIPT

chmod +x /tmp/analyze_placement.sh
bash /tmp/analyze_placement.sh
```

### Part B: Karpenter Configuration for AWS (Reference)

If you have an AWS EKS cluster, here's the complete Karpenter setup for cost optimization:

```bash
# Install Karpenter on EKS (reference commands)
# Prerequisites: EKS cluster, IRSA configured

export KARPENTER_VERSION="1.0.0"
export CLUSTER_NAME="my-cluster"

helm install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --version "${KARPENTER_VERSION}" \
  --namespace kube-system \
  --set "settings.clusterName=${CLUSTER_NAME}" \
  --set "settings.interruptionQueueName=${CLUSTER_NAME}" \
  --wait

# Apply the cost-optimized NodePool from earlier in this module
# (spot-preferred + on-demand-fallback configuration)
```

### Part C: Cleanup

```bash
kind delete cluster --name compute-lab
```

### Success Criteria

You've completed this exercise when you:
- [ ] Created a multi-node cluster with simulated instance types
- [ ] Deployed workloads of varying sizes across nodes
- [ ] Analyzed pod placement and identified utilization gaps
- [ ] Understood how bin-packing reduces node count
- [ ] Reviewed Karpenter NodePool configuration for Spot priority and consolidation
- [ ] Identified which nodes could be removed through consolidation

---

## Key Takeaways

1. **Karpenter outperforms Cluster Autoscaler for cost** — dynamic instance selection, faster provisioning, built-in consolidation
2. **Spot instances save 60-90%** — use diversification across 10+ instance types and always have PDBs
3. **Node consolidation is automatic cost reduction** — Karpenter continuously replaces under-utilized nodes with smaller ones
4. **Bin-packing saves money by reducing node count** — pack pods tightly instead of spreading them
5. **ARM/Graviton saves 20%** — most containerized workloads already support multi-arch images
6. **DaemonSet overhead favors larger nodes** — fewer big nodes waste less on per-node overhead

---

## Further Reading

**Projects**:
- **Karpenter** — karpenter.sh (next-gen Kubernetes node provisioner, CNCF Sandbox)
- **Cluster Autoscaler** — github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler

**Articles**:
- **"Karpenter Best Practices"** — aws.github.io/aws-eks-best-practices/karpenter
- **"Spot Instance Advisor"** — aws.amazon.com/ec2/spot/instance-advisor (interruption rates by type)
- **"Graviton Getting Started"** — github.com/aws/aws-graviton-getting-started

**Talks**:
- **"Karpenter: Scalable, Cost-Effective Kubernetes Compute"** — KubeCon NA (YouTube)
- **"Saving Millions with Spot on Kubernetes"** — Spotify Engineering (YouTube)

---

## Summary

Cluster-level compute optimization is the next frontier after workload rightsizing. Karpenter transforms node provisioning from a static, pre-defined process into a dynamic, cost-aware system that selects the cheapest compatible instance, prefers Spot, consolidates under-utilized nodes, and supports ARM — all automatically. Combined with bin-packing strategies and DaemonSet overhead awareness, these techniques can reduce compute costs by 50-75% beyond what workload rightsizing alone achieves.

---

## Next Module

Continue to [Module 1.5: Storage & Network Cost Management](module-1.5-storage-network-costs/) to learn how to tame the often-overlooked costs of persistent volumes, data transfer, and cross-AZ traffic.

---

*"The cheapest instance is the one you don't run."* — Karpenter philosophy

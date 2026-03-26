---
title: "Module 1.3: Cluster Topology Planning"
slug: on-premises/planning/module-1.3-cluster-topology
sidebar:
  order: 4
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 1.2: Server Sizing](module-1.2-server-sizing/), [CKA Part 1: Cluster Architecture](../../k8s/cka/part1-cluster-architecture/)

---

## Why This Module Matters

In 2021, a European insurance company ran a single 400-node Kubernetes cluster in their on-premises datacenter. Everything — customer portal, claims processing, actuarial calculations, internal tooling — ran on one cluster. When they upgraded from Kubernetes 1.22 to 1.23, a breaking change in the PodSecurityPolicy API caused 60% of their workloads to fail admission. The entire company was down for 4 hours. Their postmortem identified the root cause as "catastrophic blast radius" — a single cluster meant a single failure domain for 200+ applications across 15 business units.

They spent the next six months splitting into 7 clusters: one per business domain plus a shared platform cluster. The migration cost $800K in engineering time. The CTO's lesson: "The most expensive architecture decision is the one you make on day one and have to undo on day 300."

How many clusters should you run? Where should the control planes live? Should clusters span racks or stay within one? These topology decisions are hard to change later and have cascading implications for networking, storage, security, and operations.

> **The City Planning Analogy**
>
> Cluster topology is like city planning. One massive city (monocluster) has traffic congestion, single points of failure, and one mayor who controls everything. Multiple smaller cities (multi-cluster) have independent governance, isolated failures, and clear boundaries — but need highways (networking) and trade agreements (service mesh) between them. The right answer depends on your population size and how much autonomy each district needs.

---

## What You'll Learn

- Single cluster vs multi-cluster decision framework
- Control plane placement strategies for on-premises
- Rack-aware topology and failure domain design
- etcd topology patterns (stacked vs external)
- Namespace-based vs cluster-based isolation trade-offs
- How to plan for cluster lifecycle (creation, upgrade, decommission)

---

## Single Cluster vs Multi-Cluster

### When One Cluster Is Enough

```
┌─────────────────────────────────────────────────────────────┐
│                   SINGLE CLUSTER                             │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Kubernetes Cluster                     │   │
│  │                                                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │  │ Team A   │ │ Team B   │ │ Team C   │             │   │
│  │  │ ns: app-a│ │ ns: app-b│ │ ns: app-c│             │   │
│  │  └──────────┘ └──────────┘ └──────────┘             │   │
│  │                                                       │   │
│  │  Pros:                                                │   │
│  │  ✓ Simple operations (1 cluster to manage)           │   │
│  │  ✓ Easy service discovery (DNS within cluster)       │   │
│  │  ✓ Shared resources (better utilization)             │   │
│  │  ✓ Single control plane cost                         │   │
│  │                                                       │   │
│  │  Cons:                                                │   │
│  │  ✗ Blast radius = everything                         │   │
│  │  ✗ Noisy neighbors (one team's load spike hits all)  │   │
│  │  ✗ Upgrade = upgrade everything at once              │   │
│  │  ✗ RBAC complexity scales with teams                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  Best for: < 100 nodes, < 5 teams, homogeneous workloads    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### When You Need Multiple Clusters

```
┌─────────────────────────────────────────────────────────────┐
│                  MULTI-CLUSTER                               │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Platform │  │  Prod    │  │ Staging  │  │   Dev    │   │
│  │ Cluster  │  │ Cluster  │  │ Cluster  │  │ Cluster  │   │
│  │          │  │          │  │          │  │          │   │
│  │ Shared   │  │ Customer │  │ Pre-prod │  │ Sandbox  │   │
│  │ services │  │ facing   │  │ testing  │  │ for devs │   │
│  │ (CI/CD,  │  │ workloads│  │          │  │          │   │
│  │  observ) │  │          │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│  Best for:                                                    │
│  - Strict environment isolation (prod vs non-prod)          │
│  - Multi-tenant platforms (cluster per tenant/BU)           │
│  - Different K8s versions per environment                   │
│  - Regulatory boundaries (PCI scope isolation)              │
│  - > 200 nodes (split for operational sanity)               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Decision Matrix

| Factor | Single Cluster | Multi-Cluster |
|--------|---------------|---------------|
| Teams | < 5 | 5+ or strict isolation needed |
| Nodes | < 100-200 | 200+ or split by purpose |
| Environments | Namespace separation OK | Need hard isolation (prod/staging/dev) |
| Compliance | No PCI/HIPAA scope concerns | Need regulatory boundary isolation |
| K8s versions | All teams on same version | Teams need different versions |
| Blast radius tolerance | High (startup mentality) | Low (enterprise, regulated) |
| Operational team size | 2-3 engineers | 4+ engineers |

---

## Control Plane Placement

On-premises, you decide where control plane nodes physically live. This decision determines your failure tolerance.

### Pattern 1: Stacked Control Plane (Simple)

Control plane components and etcd run on the same nodes:

```
┌─────────────────────────────────────────────────────────────┐
│               STACKED CONTROL PLANE                          │
│                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐│
│  │   CP Node 1    │  │   CP Node 2    │  │   CP Node 3    ││
│  │                │  │                │  │                ││
│  │ API Server     │  │ API Server     │  │ API Server     ││
│  │ Controller Mgr │  │ Controller Mgr │  │ Controller Mgr ││
│  │ Scheduler      │  │ Scheduler      │  │ Scheduler      ││
│  │ etcd           │  │ etcd           │  │ etcd           ││
│  │                │  │                │  │                ││
│  │ 8 cores, 32GB  │  │ 8 cores, 32GB  │  │ 8 cores, 32GB  ││
│  │ 200GB NVMe     │  │ 200GB NVMe     │  │ 200GB NVMe     ││
│  └────────────────┘  └────────────────┘  └────────────────┘│
│                                                               │
│  ✓ Simple: fewer servers to manage                          │
│  ✓ kubeadm default: easy to set up                         │
│  ✗ etcd failure = CP node failure (coupled)                 │
│  ✗ Cannot scale etcd independently                         │
│                                                               │
│  Best for: clusters < 200 nodes                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Pattern 2: External etcd (Production)

etcd runs on dedicated servers with NVMe, separate from API servers:

```
┌─────────────────────────────────────────────────────────────┐
│               EXTERNAL ETCD TOPOLOGY                         │
│                                                               │
│  API Server Nodes:              etcd Nodes:                  │
│  ┌──────────────┐              ┌──────────────┐             │
│  │ API Server 1 │──────────────│ etcd Node 1  │             │
│  │ Ctrl Mgr     │              │ 4 cores, 16GB│             │
│  │ Scheduler    │              │ 200GB NVMe   │             │
│  │ 8 cores, 16GB│              └──────────────┘             │
│  └──────────────┘              ┌──────────────┐             │
│  ┌──────────────┐              │ etcd Node 2  │             │
│  │ API Server 2 │──────────────│ 4 cores, 16GB│             │
│  │ 8 cores, 16GB│              │ 200GB NVMe   │             │
│  └──────────────┘              └──────────────┘             │
│  ┌──────────────┐              ┌──────────────┐             │
│  │ API Server 3 │──────────────│ etcd Node 3  │             │
│  │ 8 cores, 16GB│              │ 4 cores, 16GB│             │
│  └──────────────┘              │ 200GB NVMe   │             │
│                                └──────────────┘             │
│                                                               │
│  ✓ etcd on dedicated NVMe (no resource contention)          │
│  ✓ Scale API servers independently from etcd                │
│  ✓ etcd failures don't take down API server process         │
│  ✗ More servers (6 instead of 3)                            │
│  ✗ More complex setup                                       │
│                                                               │
│  Best for: clusters > 200 nodes, high-throughput workloads  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Pattern 3: Shared Management Cluster

One management cluster hosts control planes for multiple tenant clusters:

```
┌─────────────────────────────────────────────────────────────┐
│            MANAGEMENT CLUSTER PATTERN                        │
│                                                               │
│  ┌────────────────────────────────────────────┐             │
│  │        Management Cluster (3 nodes)        │             │
│  │                                            │             │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐   │             │
│  │  │ Cluster │  │ Cluster │  │ Cluster │   │             │
│  │  │ API: Dev│  │API: Stg │  │API: Prod│   │             │
│  │  │ etcd    │  │ etcd    │  │ etcd    │   │             │
│  │  └────┬────┘  └────┬────┘  └────┬────┘   │             │
│  └───────┼─────────────┼───────────┼─────────┘             │
│          │             │           │                         │
│     ┌────▼────┐   ┌────▼────┐ ┌────▼────┐                  │
│     │Workers  │   │Workers  │ │Workers  │                  │
│     │Dev (5)  │   │Stg (10) │ │Prod (50)│                  │
│     └─────────┘   └─────────┘ └─────────┘                  │
│                                                               │
│  Technologies: vCluster, Kamaji, Cluster API                │
│  Savings: 3 servers for N cluster control planes            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rack-Aware Topology

On-premises, you must design for physical failure domains that cloud abstracts away.

### Failure Domain Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│              FAILURE DOMAIN HIERARCHY                        │
│                                                               │
│  Datacenter ──── Entire site power/cooling failure          │
│    │                                                         │
│    ├── Room ──── Fire suppression, cooling zone             │
│    │    │                                                    │
│    │    ├── Row ──── PDU circuit, top-of-row switch         │
│    │    │    │                                               │
│    │    │    ├── Rack ──── PDU, ToR switch, single UPS      │
│    │    │    │    │                                          │
│    │    │    │    └── Server ──── PSU, disk, NIC, CPU       │
│    │    │    │                                               │
│    │    │    └── Rack                                        │
│    │    │                                                    │
│    │    └── Row                                              │
│    │                                                         │
│    └── Room                                                  │
│                                                               │
│  Rule: Spread control plane across failure domains          │
│  Minimum: 1 CP node per rack (survive rack failure)         │
│  Ideal: CP nodes across rows or rooms                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Kubernetes Topology Labels

```yaml
# Label nodes with physical topology
kubectl label node worker-01 \
  topology.kubernetes.io/zone=rack-a \
  topology.kubernetes.io/region=dc-east \
  node.kubernetes.io/room=server-room-1 \
  node.kubernetes.io/row=row-3

# Use topology spread constraints to distribute pods
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
spec:
  replicas: 6
  template:
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone  # = rack
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: payment-api
      # This ensures: max 1 pod difference between racks
      # With 6 replicas across 3 racks: 2-2-2 distribution
      # If rack-a fails: 0-2-2 (still 4 replicas running)
```

### Recommended Rack Layout

```
┌─────────────────────────────────────────────────────────────┐
│                RACK LAYOUT (per rack)                        │
│                                                               │
│  42U Rack                                                    │
│  ┌────────────────────────────────────┐                     │
│  │ U42: Patch panel (fiber/copper)    │                     │
│  │ U41: ToR Switch 1 (25GbE)         │                     │
│  │ U40: ToR Switch 2 (25GbE, redundant)│                    │
│  │ U39: ── empty (airflow) ──        │                     │
│  │ U38: Management switch (1GbE)     │                     │
│  │ U37: ── empty ──                  │                     │
│  │ U36-U35: Control plane node       │ 2U                  │
│  │ U34-U33: Worker node 1            │ 2U                  │
│  │ U32-U31: Worker node 2            │ 2U                  │
│  │ U30-U29: Worker node 3            │ 2U                  │
│  │ U28-U27: Worker node 4            │ 2U                  │
│  │ U26-U25: Worker node 5            │ 2U                  │
│  │ U24-U23: Worker node 6            │ 2U                  │
│  │ U22-U21: Storage node (Ceph OSD)  │ 2U                  │
│  │ U20-U01: ── expansion space ──    │ 20U spare           │
│  │ U00: PDU (2x redundant, A+B feed) │                     │
│  └────────────────────────────────────┘                     │
│                                                               │
│  Power budget: ~8-12 kW per rack (check PDU rating)         │
│  Cooling: 1 ton per 3.5 kW of IT load (rule of thumb)      │
│  Weight: ~1,200 lbs fully loaded (check floor rating)       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## etcd Topology Patterns

etcd is a distributed consensus system. Its topology determines your cluster's durability and performance.

### Quorum and Failure Tolerance

| etcd Members | Quorum | Tolerates Failures | Recommended For |
|-------------|--------|-------------------|-----------------|
| 1 | 1 | 0 | Dev/test only |
| 3 | 2 | 1 | Standard production |
| 5 | 3 | 2 | Mission-critical |
| 7 | 4 | 3 | Rarely needed (higher write latency) |

**Critical**: etcd latency between members must be < 10ms RTT. Do not stretch etcd across datacenters unless they have dedicated low-latency links (< 2ms RTT).

```bash
# Check etcd member health and latency
ETCDCTL_API=3 etcdctl \
  --endpoints=https://10.0.1.10:2379,https://10.0.1.11:2379,https://10.0.1.12:2379 \
  --cert=/etc/kubernetes/pki/etcd/peer.crt \
  --key=/etc/kubernetes/pki/etcd/peer.key \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  endpoint health --write-out=table

# Check etcd performance
ETCDCTL_API=3 etcdctl check perf --endpoints=https://10.0.1.10:2379 \
  --cert=/etc/kubernetes/pki/etcd/peer.crt \
  --key=/etc/kubernetes/pki/etcd/peer.key \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt
```

---

## Did You Know?

- **Google runs approximately 15,000 Kubernetes clusters internally** (Borg/GKE hybrid). They do not run one giant cluster — they use the multi-cluster pattern with automated lifecycle management. Even at Google's scale, the operational overhead of one massive cluster is worse than many smaller ones.

- **The maximum tested cluster size for Kubernetes is 5,000 nodes**. Beyond that, the API server's watch cache, etcd's storage, and the scheduler's throughput become bottlenecks. Most production clusters stay under 500 nodes and split beyond that.

- **etcd's Raft consensus requires a majority quorum for every write.** With 5 members, every write must be acknowledged by 3 before it is committed. Adding a 6th member does not improve fault tolerance (still tolerates 2 failures) but increases write latency. Always use odd numbers.

- **Spotify runs 150+ Kubernetes clusters** across their infrastructure, each scoped to a team or service domain. They invest heavily in automation via Backstage (which they created) to manage the lifecycle of all these clusters.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| One giant cluster | Blast radius = entire company | Split by environment, then by domain |
| Too many clusters | Operational overhead exceeds team capacity | 1 engineer can manage ~5-10 clusters with good automation |
| CP nodes in same rack | Rack failure = cluster down | Spread CP across racks or rows |
| Stretching etcd across DCs | Latency kills consensus performance | etcd in one DC; use federation for multi-DC |
| No lifecycle automation | Manual cluster creation takes days | Cluster API + GitOps for declarative lifecycle |
| Namespace isolation only | Namespaces don't provide hard security boundaries | Use clusters for trust boundaries, namespaces for organization |
| Not labeling nodes | Cannot use topology spread constraints | Label every node with rack, row, room, DC |
| Even number of etcd members | Split-brain risk with no tiebreaker | Always odd: 3, 5, or 7 |

---

## Quiz

### Question 1
Your company has 300 nodes, 8 teams, and a regulatory requirement to isolate PCI-scoped workloads. How many clusters would you recommend?

<details>
<summary>Answer</summary>

**Minimum 3 clusters, recommended 4-5:**

1. **PCI cluster** — Dedicated to payment processing workloads. Hard isolation boundary for audit scope. Minimal node count (only what payment services need). Separate control plane, separate network segment.

2. **Production cluster** — Non-PCI production workloads. The bulk of your 300 nodes.

3. **Non-production cluster** — Dev, staging, QA. Can share one cluster with namespace isolation.

4. **Platform cluster** (optional) — CI/CD, monitoring, logging, GitOps controllers. Separates platform tooling from application workloads.

5. **Management cluster** (optional) — Hosts Cluster API controllers, manages lifecycle of other clusters.

The PCI cluster is non-negotiable — regulatory scope isolation requires a hard boundary. The prod/non-prod split prevents staging incidents from affecting production. The platform cluster is a maturity decision.
</details>

### Question 2
You have 3 racks in one datacenter. Where do you place your 3 control plane nodes?

<details>
<summary>Answer</summary>

**One control plane node per rack.** This ensures that a rack failure (PDU, ToR switch, or cooling issue) takes down at most 1 of 3 CP nodes. The remaining 2 maintain quorum (2/3 majority).

```
Rack A: CP-1 + Workers
Rack B: CP-2 + Workers
Rack C: CP-3 + Workers
```

If you only have 2 racks, place 2 CP nodes in one rack and 1 in the other. A failure in the 2-node rack will lose quorum, but a failure in the 1-node rack will not. This is not ideal — 3 racks is the minimum for proper CP distribution.

Label nodes with `topology.kubernetes.io/zone=rack-{a,b,c}` and use topology spread constraints to distribute application pods across racks.
</details>

### Question 3
When should you use external etcd instead of stacked?

<details>
<summary>Answer</summary>

Use **external etcd** when:

1. **Cluster size > 200 nodes** — etcd write throughput becomes critical; dedicated NVMe servers with no resource contention are essential.

2. **etcd performance is paramount** — Financial services, real-time systems where API latency matters. External etcd eliminates CPU/memory contention with API server.

3. **You need to scale API servers independently** — If API server load is high (many controllers, webhooks, CRDs) but etcd is not the bottleneck, you can add more API server nodes without adding etcd members.

4. **You want independent failure domains** — API server crash should not affect etcd data integrity and vice versa.

Use **stacked** when:
- Cluster < 200 nodes
- Simplicity is valued over maximum performance
- You have limited server count (3 servers = 3 stacked CP nodes)
</details>

### Question 4
What is the maximum recommended RTT latency between etcd members, and why?

<details>
<summary>Answer</summary>

**< 10ms round-trip time**, ideally < 2ms.

etcd uses the Raft consensus protocol, which requires a leader to replicate log entries to a majority of members on every write. The default heartbeat interval is 100ms, and the election timeout is 1,000ms (10x heartbeat).

If network latency between etcd members exceeds ~10ms, the time for a write to be committed (leader → majority acknowledgment) approaches the heartbeat interval. Under load, this causes:
1. Slow API server responses (every kubectl command waits for etcd)
2. Leader election instability (heartbeats arrive too late)
3. Write throughput collapse (Raft serializes writes through the leader)

This is why etcd should **never be stretched across datacenters** unless they have a dedicated low-latency link (dark fiber, < 2ms RTT). For multi-DC, use separate clusters with federation or replication at the application layer.
</details>

---

## Hands-On Exercise: Design a Cluster Topology

**Task**: Given an organization's requirements, design a complete cluster topology with physical placement.

### Scenario

A manufacturing company is deploying Kubernetes on-premises:
- 2 datacenters (DC-East and DC-West, 50km apart, 5ms RTT)
- 150 total nodes needed
- 4 teams: Platform, Product, Data Science, QA
- PCI compliance for payment processing (20 nodes)
- GPU workloads for quality inspection ML models (10 nodes)
- Need to survive a full datacenter failure

### Steps

1. **Determine cluster count:**
   - PCI cluster (dedicated, DC-East): 20 worker nodes + 3 CP
   - Production cluster (DC-East primary): 80 worker nodes + 3 CP
   - GPU cluster (DC-East): 10 worker nodes + 3 CP (can share CP with prod)
   - DR/Standby cluster (DC-West): 40 worker nodes + 3 CP
   - Non-prod cluster (DC-West): 20 worker nodes + 3 CP

2. **Place control planes:**

```bash
# DC-East (3 racks)
# Rack A: PCI CP-1, Prod CP-1, 8 workers
# Rack B: PCI CP-2, Prod CP-2, 8 workers
# Rack C: PCI CP-3, Prod CP-3, 8 workers + GPU nodes

# DC-West (2 racks)
# Rack D: DR CP-1, NonProd CP-1, 15 workers
# Rack E: DR CP-2, NonProd CP-2, 15 workers
# Rack F: DR CP-3, NonProd CP-3, 10 workers
```

3. **Label nodes:**

```bash
# DC-East nodes
kubectl label node east-rack-a-01 \
  topology.kubernetes.io/region=dc-east \
  topology.kubernetes.io/zone=rack-a \
  node.kubernetes.io/purpose=worker

# GPU nodes
kubectl label node east-rack-c-gpu-01 \
  topology.kubernetes.io/region=dc-east \
  topology.kubernetes.io/zone=rack-c \
  node.kubernetes.io/gpu=nvidia-a100 \
  node.kubernetes.io/purpose=gpu
```

4. **Define topology spread:**

```yaml
# Production deployment spread across racks
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
```

### Success Criteria
- [ ] Cluster count justified with reasoning
- [ ] PCI workloads in dedicated cluster
- [ ] Control planes spread across failure domains (racks)
- [ ] etcd not stretched across DCs (< 10ms RTT within cluster)
- [ ] DR strategy handles full DC failure
- [ ] Node labels defined for topology-aware scheduling
- [ ] GPU nodes isolated with labels and taints

---

## Next Module

Continue to [Module 1.4: TCO & Budget Planning](module-1.4-tco-budget/) to learn how to build a comprehensive cost model for your on-premises Kubernetes platform.

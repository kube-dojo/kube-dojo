---
title: "Module 1.2: Server Sizing & Hardware Selection"
slug: on-premises/planning/module-1.2-server-sizing
sidebar:
  order: 3
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 1.1: The Case for On-Premises K8s](../module-1.1-case-for-on-prem/), [Linux: Kernel Architecture](../../linux/foundations/system-essentials/module-1.1-kernel-architecture/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** server configurations matched to specific workload profiles (CPU-bound, memory-bound, storage-bound, GPU-accelerated)
2. **Evaluate** hardware vendors and SKUs using benchmark data, TCO projections, and workload requirements
3. **Configure** control plane nodes with appropriate NVMe storage, ECC RAM, and CPU specifications for etcd performance
4. **Plan** hardware procurement that accounts for 3-5 year growth projections and avoids stranded capacity

---

## Why This Module Matters

In September 2022, a logistics company ordered twelve Dell PowerEdge R750xs servers for their new Kubernetes platform. Each server had dual 24-core Intel Xeon Gold 5317 processors, 256GB of RAM, and four 1.92TB SATA SSDs. The hardware cost $216,000. When the platform team deployed their first workloads — a real-time vehicle tracking system processing 50,000 GPS events per second — they discovered two critical mistakes.

First, the SATA SSDs could not keep up with etcd's fsync requirements. etcd commit latency exceeded 100ms during peak hours, causing leader elections every few minutes. The API server became unreliable. They needed NVMe drives for the control plane nodes — a $24,000 additional investment and two weeks of downtime for hardware replacement.

Second, the vehicle tracking pods needed 2GB of RAM each but only 0.5 vCPU — a 1:4 CPU-to-RAM ratio per pod. But their servers had a 1:2.7 ratio (96 vCPUs, 256GB RAM) — too CPU-heavy for this workload. They ran out of RAM with 33% of CPU unused. They had ordered compute-optimized servers for a memory-intensive workload. The remaining CPU capacity sat idle for the next three years.

Hardware mistakes are expensive and permanent. You live with them for 3-5 years. This module teaches you how to size servers correctly the first time.

> **The Apartment Analogy**
>
> Buying servers is like signing a 3-year apartment lease. You cannot easily add rooms (RAM slots are finite), move walls (CPU sockets are fixed), or change the plumbing (storage bus is soldered). If you get it wrong, you either waste money on space you do not use or squeeze into space that is too small. Measure twice, buy once.

---

## What You'll Learn

- How to calculate CPU, memory, and storage requirements for Kubernetes nodes
- NUMA architecture and why it matters for pod scheduling
- Control plane sizing (etcd is the bottleneck, not the API server)
- Worker node sizing strategies for different workload profiles
- GPU node considerations for ML/AI workloads
- How to avoid the most common hardware mistakes

---

## Server Architecture for Kubernetes

### Anatomy of a Modern Server

```
┌─────────────────────────────────────────────────────────────┐
│                     2U RACK SERVER                           │
│                                                               │
│  ┌───────────────────┐    ┌───────────────────┐             │
│  │    CPU Socket 0    │    │    CPU Socket 1    │             │
│  │  (32 cores, 64 HT) │    │  (32 cores, 64 HT) │             │
│  │                    │    │                    │             │
│  │  L3 Cache: 48MB   │    │  L3 Cache: 48MB   │             │
│  └────────┬───────────┘    └────────┬───────────┘             │
│           │                         │                         │
│  ┌────────▼───────────┐    ┌────────▼───────────┐             │
│  │  NUMA Node 0       │    │  NUMA Node 1       │             │
│  │  RAM: 256GB DDR5  │    │  RAM: 256GB DDR5  │             │
│  │  (8x 32GB DIMMs)  │    │  (8x 32GB DIMMs)  │             │
│  └────────┬───────────┘    └────────┬───────────┘             │
│           │                         │                         │
│  ┌────────▼──────────────────────────▼───────────┐           │
│  │              PCIe Gen 5 Bus                    │           │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │           │
│  │  │NVMe 0│ │NVMe 1│ │NVMe 2│ │NVMe 3│         │           │
│  │  │3.84TB│ │3.84TB│ │3.84TB│ │3.84TB│         │           │
│  │  └──────┘ └──────┘ └──────┘ └──────┘         │           │
│  │                                                │           │
│  │  ┌──────┐ ┌──────┐                            │           │
│  │  │NIC 0 │ │NIC 1 │  (25GbE or 100GbE)        │           │
│  │  └──────┘ └──────┘                            │           │
│  └────────────────────────────────────────────────┘           │
│                                                               │
│  BMC / IPMI / iDRAC / iLO  (out-of-band management)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### NUMA: Why CPU Topology Matters

Non-Uniform Memory Access (NUMA) means each CPU socket has "local" memory that is fast to access and "remote" memory (on the other socket) that is slower:

```
┌─────────────────────────────────────────────────────────────┐
│                    NUMA TOPOLOGY                              │
│                                                               │
│   NUMA Node 0                    NUMA Node 1                 │
│   ┌──────────────┐              ┌──────────────┐            │
│   │   CPU 0      │              │   CPU 1      │            │
│   │  32 cores    │◄── QPI/UPI ──►│  32 cores    │            │
│   └──────┬───────┘    (~100ns)   └──────┬───────┘            │
│          │                              │                    │
│   ┌──────▼───────┐              ┌──────▼───────┐            │
│   │ Local RAM    │              │ Local RAM    │            │
│   │ 256GB        │              │ 256GB        │            │
│   │ (~80ns)      │              │ (~80ns)      │            │
│   └──────────────┘              └──────────────┘            │
│                                                               │
│   Pod A on CPU 0 accessing:                                  │
│     Local RAM (Node 0):  ~80ns  ← Fast                      │
│     Remote RAM (Node 1): ~180ns ← 2.25x slower              │
│                                                               │
│   Impact: in-memory DBs (Redis) on cross-NUMA = 30-50% slower│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Pause and predict**: You are running Redis (an in-memory database) on a dual-socket server. The Redis process is scheduled on CPU socket 0, but half of its allocated memory lands on NUMA node 1. What performance impact would you expect, and how would you verify it?

**Kubernetes NUMA awareness:**

The following kubelet configuration tells Kubernetes to pin all of a pod's resources to a single NUMA node. This is essential for latency-sensitive workloads like in-memory databases where cross-NUMA memory access would add 100ns per access -- enough to degrade throughput by 30-50%:

```bash
# Check NUMA topology on a node
numactl --hardware

# Kubernetes Topology Manager policies:
# - none: default, no NUMA alignment (fine for most workloads)
# - best-effort: try to align, don't fail if impossible
# - restricted: fail pods that can't be NUMA-aligned
# - single-numa-node: all resources from one NUMA node (for latency-sensitive)

# Configure kubelet for NUMA-aware scheduling:
# /var/lib/kubelet/config.yaml
# topologyManagerPolicy: "single-numa-node"
# topologyManagerScope: "pod"
```

---

## Control Plane Sizing

The control plane is the brain of your cluster. Under-sizing it causes cascading failures. Over-sizing wastes expensive resources.

### etcd is the Bottleneck

etcd is the most resource-sensitive component. It requires:
- **Low-latency storage**: <10ms p99 fsync latency (NVMe required, SATA SSDs are insufficient)
- **Consistent IOPS**: 500-1000 sustained writes for a 100-node cluster
- **RAM**: Proportional to the number of objects (1GB per 10K objects is a rough estimate)
- **CPU**: 2-4 dedicated cores (etcd is single-threaded for writes but multi-threaded for reads)

```
┌─────────────────────────────────────────────────────────────┐
│               CONTROL PLANE SIZING GUIDE                     │
│                                                               │
│  Cluster Size    │ CP Nodes │ CPU/Node │ RAM/Node │ Storage  │
│  ────────────────┼──────────┼──────────┼──────────┼──────────│
│  < 10 nodes      │    3     │  4 cores │   8 GB   │ 50GB SSD │
│  10-100 nodes    │    3     │  8 cores │  16 GB   │ 100GB NVMe│
│  100-500 nodes   │    3     │ 16 cores │  32 GB   │ 200GB NVMe│
│  500-2000 nodes  │    5     │ 32 cores │  64 GB   │ 500GB NVMe│
│  2000+ nodes     │    5     │ 64 cores │ 128 GB   │ 1TB NVMe │
│                                                               │
│  CRITICAL: etcd storage MUST be NVMe with < 10ms p99 fsync  │
│  CRITICAL: 3 CP nodes = tolerate 1 failure                  │
│  CRITICAL: 5 CP nodes = tolerate 2 failures (recommended    │
│            for production clusters > 500 nodes)              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: Your team is debating whether to save $8,000 per control plane node by using SATA SSDs instead of NVMe. The SATA SSDs have 80K IOPS and 2ms p99 latency. Based on what you know about etcd's fsync requirements, would you approve this cost saving? What specific metric would you test before making the decision?

**Test your storage before deploying etcd:**

The fio benchmark below simulates etcd's Write-Ahead Log pattern -- small sequential writes with an fsync after each one. This is the single most important benchmark for control plane hardware because etcd's performance directly determines API server responsiveness:

```bash
# Install fio for storage benchmarking
apt-get install fio

# Test sequential write latency (simulates etcd WAL writes)
fio --name=etcd-wal-test \
    --filename=/var/lib/etcd/fio-test \
    --rw=write \
    --bs=2300 \
    --fsync=1 \
    --size=22m \
    --runtime=60 \
    --time_based

# PASS: 99th percentile fsync < 10ms
# FAIL: 99th percentile fsync > 10ms → etcd will have leader elections

# Test random write IOPS (simulates etcd snapshot + compaction)
fio --name=etcd-iops-test \
    --filename=/var/lib/etcd/fio-test \
    --rw=randwrite \
    --bs=4k \
    --direct=1 \
    --numjobs=1 \
    --size=1g \
    --runtime=60 \
    --time_based

# Target: > 500 IOPS for clusters < 100 nodes
# Target: > 2000 IOPS for clusters > 500 nodes
```

### Shared Control Planes: Multiple Clusters on 3 Servers

For organizations running multiple small clusters, a dedicated 3-node control plane per cluster is wasteful. Consider:

```
┌─────────────────────────────────────────────────────────────┐
│          SHARED CONTROL PLANE ARCHITECTURE                   │
│                                                               │
│  Option A: vCluster (virtual clusters)                       │
│  ┌────────────────────────────────────────┐                  │
│  │  Host Cluster (3 physical nodes)       │                  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │                  │
│  │  │vCluster │ │vCluster │ │vCluster │  │                  │
│  │  │  Dev    │ │ Staging │ │  Prod   │  │                  │
│  │  └─────────┘ └─────────┘ └─────────┘  │                  │
│  │  Each vCluster: own API server, etcd   │                  │
│  │  Shares: worker nodes, networking      │                  │
│  └────────────────────────────────────────┘                  │
│                                                               │
│  Option B: Kamaji (hosted control planes)                    │
│  ┌────────────────────────────────────────┐                  │
│  │  Management Cluster (3 nodes)          │                  │
│  │  ┌──────────────────────────────────┐  │                  │
│  │  │  Kamaji Operator                 │  │                  │
│  │  │  ┌────────┐ ┌────────┐ ┌──────┐ │  │                  │
│  │  │  │ TCP 1  │ │ TCP 2  │ │TCP 3 │ │  │                  │
│  │  │  │(Dev CP)│ │(Stg CP)│ │(Prd) │ │  │                  │
│  │  │  └────────┘ └────────┘ └──────┘ │  │                  │
│  │  └──────────────────────────────────┘  │                  │
│  └────────────────────────────────────────┘                  │
│  Worker nodes join remote — no CP hardware per cluster       │
│                                                               │
│  Savings: 3 servers host 10+ cluster control planes          │
│  vs 30+ servers for dedicated CPs                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Worker Node Sizing

### Workload Profiles

Different workloads need different server configurations:

| Profile | CPU:RAM Ratio | Example Workloads | Recommended Server |
|---------|--------------|--------------------|--------------------|
| **Compute-heavy** | 1:2 | CI/CD, compilation, encryption | High clock speed, fewer cores |
| **Balanced** | 1:4 | Web services, APIs, microservices | Standard dual-socket |
| **Memory-heavy** | 1:8 | Databases, caching, JVM apps | Max DIMM slots, lower-clock CPUs |
| **Storage-heavy** | N/A | Ceph OSDs, data pipelines | Many NVMe bays, high bandwidth |
| **GPU** | N/A | ML training, inference, rendering | PCIe Gen5 slots, high power |

### Sizing Formula

```
┌─────────────────────────────────────────────────────────────┐
│                WORKER NODE SIZING                            │
│                                                               │
│  Total cluster capacity needed:                              │
│    CPU = Sum of all pod CPU requests × 1.3 (30% headroom)   │
│    RAM = Sum of all pod RAM requests × 1.3 (30% headroom)   │
│                                                               │
│  Per-node calculation:                                       │
│    Allocatable CPU = Total cores - system reserved (2 cores) │
│    Allocatable RAM = Total RAM - system reserved (2-4 GB)    │
│    Allocatable RAM -= kubelet eviction threshold (100Mi)     │
│                                                               │
│  Number of nodes:                                            │
│    nodes = max(CPU_needed / allocatable_cpu_per_node,         │
│               RAM_needed / allocatable_ram_per_node)         │
│                                                               │
│  Add N+1 or N+2 for failure tolerance:                       │
│    Production: at least N+2 (survive 2 node failures)        │
│    Non-prod: N+1 is acceptable                               │
│                                                               │
│  Example:                                                    │
│    Workload: 200 pods, avg 1 CPU + 2GB RAM each             │
│    Cluster needs: 200 CPU, 400GB RAM (+ 30% = 260 CPU, 520GB)│
│    Server: 32-core (64 vCPUs with SMT), 256GB RAM            │
│    Allocatable: 62 vCPUs, 252GB RAM                          │
│    By CPU: 260/62 = 5 nodes                                 │
│    By RAM: 520/252 = 3 nodes                                │
│    Bottleneck: CPU (5 nodes)                                 │
│    With N+2: 7 nodes                                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### CPU: Intel vs AMD

| Factor | Intel Xeon (Sapphire Rapids) | AMD EPYC (Genoa) |
|--------|---------------------------|-------------------|
| Max cores/socket | 60 | 96 |
| Max RAM/socket | 4TB DDR5 | 6TB DDR5 |
| PCIe lanes | 80 (Gen5) | 128 (Gen5) |
| Price/core | Higher (~$30-50/core) | Lower (~$15-30/core) |
| Single-thread perf | Slightly higher | Slightly lower |
| Power efficiency | ~300W TDP | ~280W TDP |
| K8s recommendation | Good for latency-sensitive | Better for density |

**For most Kubernetes workloads, AMD EPYC offers better value** — more cores per dollar, more PCIe lanes for NVMe and NICs, and competitive power efficiency. Intel wins for specific workloads that benefit from higher single-thread performance (some databases, compilation).

> **Pause and predict**: You have two server options at the same price: (A) a single-socket AMD EPYC 9654 with 96 cores and 384GB RAM, or (B) a dual-socket Intel Xeon 6430 with 64 total cores and 512GB RAM. Your workload is 200 Java microservices averaging 0.5 CPU and 2GB RAM each. Which server gives you better pod density, and why?

### How Many Pods Per Node?

```bash
# Kubernetes default: 110 pods per node
# This is a soft limit configurable via kubelet:
# --max-pods=250

# Practical limits depend on:
# 1. CNI (some CNIs have per-node IP limits)
# 2. Available resources (CPU, RAM)
# 3. Pod density (many small pods vs few large pods)

# Calculate realistic pod density:
# If average pod = 0.5 CPU, 512Mi RAM
# Node = 64 cores, 256GB RAM
# By CPU: 64 / 0.5 = 128 pods
# By RAM: 256GB / 512Mi = 512 pods
# Practical limit: ~128 pods (CPU-bound)
# With overhead: ~100 pods (leave room for system pods)
```

---

## Storage Selection

### Storage Tiers

| Tier | Technology | IOPS | Latency | Use Case | Cost/TB |
|------|-----------|------|---------|----------|---------|
| **Tier 0** | NVMe (PCIe Gen5) | 1M+ | <100us | etcd, databases | $150-300 |
| **Tier 1** | NVMe (PCIe Gen4) | 500K+ | <200us | Application data, Ceph OSD | $100-200 |
| **Tier 2** | SATA SSD | 50-100K | 1-5ms | Logs, bulk storage | $50-100 |
| **Tier 3** | HDD (SAS/SATA) | 100-200 | 5-15ms | Backups, cold data | $15-30 |

**Critical rule**: etcd MUST run on Tier 0 or Tier 1 storage. SATA SSDs (Tier 2) will cause etcd leader elections under load.

### Networking

| Speed | Use Case | Cost per Port |
|-------|----------|---------------|
| 1GbE | Management/IPMI only | ~$20 |
| 10GbE | Small clusters (<20 nodes) | ~$50 |
| 25GbE | Standard production | ~$100 |
| 100GbE | High-throughput (storage, ML) | ~$300 |

**Minimum recommendation**: 25GbE for Kubernetes east-west traffic. 1GbE is insufficient for any production workload.

---

## Did You Know?

- **A single modern server can replace 20-30 cloud instances.** A 2U server with dual 64-core AMD EPYC processors (128 cores, 256 threads), 1TB RAM, and 8x NVMe drives provides more compute than a fleet of m6i.xlarge instances — at a fraction of the 3-year cost.

- **ECC (Error-Correcting Code) memory is non-negotiable for servers.** Non-ECC RAM experiences approximately 1 bit error per 8GB per 72 hours. In a 512GB server, that is multiple undetected memory corruptions per day. ECC costs ~10% more but prevents silent data corruption that can corrupt etcd, databases, and filesystems.

- **NUMA topology can cause a 2x performance difference** for the same workload on the same hardware. A database running entirely within one NUMA node can be twice as fast as one whose memory is split across two NUMA nodes. Kubernetes Topology Manager was created specifically to solve this.

- **The most common server lifecycle is 5 years**, but most organizations refresh at 3 years for warranty and performance reasons. After 3 years, maintenance contracts become expensive and newer hardware offers 30-50% better performance per watt.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| SATA SSDs for etcd | Leader elections under load, cluster instability | NVMe only for control plane storage |
| Wrong CPU:RAM ratio | Stranded resources (idle CPU or insufficient RAM) | Profile your workloads first, then buy hardware to match |
| Skipping NUMA planning | 30-50% latency increase for latency-sensitive pods | Enable Topology Manager for critical workloads |
| Buying consumer drives | No power-loss protection, shorter lifespan | Enterprise NVMe with PLP (Power Loss Protection) |
| Uniform hardware | Every node is identical regardless of workload needs | Different node pools: compute, memory, storage, GPU |
| Maxing out day one | No expansion room for growth | Fill 60-70% of rack capacity, leave room to grow |
| Ignoring power budget | Servers draw more power than the rack PDU supports | Calculate TDP per server x nodes vs PDU capacity |
| No spare nodes | A single failure causes capacity pressure | Maintain N+2 spare capacity at minimum |

---

## Quiz

### Question 1
You are building a Kubernetes cluster for a real-time analytics platform. The workload consists of 50 pods, each requiring 4 vCPU and 32GB RAM. What server configuration would you choose?

<details>
<summary>Answer</summary>

**Analysis:**
- Total CPU needed: 50 x 4 = 200 vCPU + 30% headroom = 260 vCPU
- Total RAM needed: 50 x 32GB = 1,600GB + 30% = 2,080GB
- CPU:RAM ratio of workload: 1:8 (memory-heavy)

**Server selection:**
Choose memory-optimized servers. For example:
- Server: Single AMD EPYC 9354 (32 cores, 64 threads), 512GB DDR5
- Note: Kubernetes counts 1 CPU = 1 hyperthread (vCPU), so this server provides 64 allocatable vCPUs
- Allocatable: ~62 vCPUs, ~508GB RAM
- By CPU: 260 / 62 = 5 nodes
- By RAM: 2,080 / 508 = 5 nodes (balanced!)
- With N+2: 7 nodes

This is a well-balanced configuration because the vCPU:RAM ratio of the server (1:8) matches the workload profile. With compute-optimized servers (1:4 ratio, like the ones in the intro story), you would need 9+ nodes to satisfy RAM, wasting 50% of CPU.
</details>

### Question 2
Why is NVMe required for etcd and not just "recommended"?

<details>
<summary>Answer</summary>

etcd uses a Write-Ahead Log (WAL) that requires `fsync` on every write to guarantee data durability. The `fsync` latency directly determines how fast etcd can commit transactions.

- **NVMe fsync latency**: 0.1-1ms (99th percentile)
- **SATA SSD fsync latency**: 2-10ms (99th percentile)
- **HDD fsync latency**: 10-50ms

etcd's leader election timeout defaults to 1 second (10x the heartbeat interval of 100ms). If commit latency consistently exceeds 50-100ms, the leader cannot send heartbeats fast enough, triggering leader elections. During elections, the cluster is read-only — no API server writes succeed.

Under load (many concurrent kubectl commands, controller reconciliations, or webhook calls), SATA SSD latency spikes to 10ms+, which cascades into slow API responses, failed deployments, and cluster instability. This is not theoretical — it is one of the most common production issues in self-managed Kubernetes.
</details>

### Question 3
Your company has 3 servers with 128 cores and 512GB RAM each. You want to run 5 Kubernetes clusters (dev, staging, 3 production environments). How would you architect this?

<details>
<summary>Answer</summary>

**Do not run 5 separate clusters with dedicated control planes** — that would need 15 control plane nodes (3 per cluster), consuming most of your capacity for control planes alone.

Instead, use **virtual clusters or hosted control planes**:

**Option A — vCluster:**
- 1 host cluster across all 3 servers (3 control plane + 3 worker)
- 5 vClusters running as pods inside the host cluster
- Each vCluster gets its own API server and etcd (as pods)
- Worker capacity is shared across all virtual clusters
- Total control plane overhead: ~20 cores, ~40GB RAM (instead of 120 cores with dedicated CPs)

**Option B — Kamaji:**
- 1 management cluster (3 nodes, stacked etcd)
- 5 Tenant Control Planes (TCPs) running as pods
- Worker nodes join respective TCPs
- Even lighter than vCluster — control plane pods are ~2 cores, 4GB RAM each

**The key insight**: With 3 servers, you cannot afford to waste 60%+ of capacity on control planes. Shared control plane architectures are designed for exactly this constraint.
</details>

### Question 4
You are told to "just buy the biggest servers available." Why is this a bad strategy?

<details>
<summary>Answer</summary>

**Blast radius.** The bigger the server, the more pods run on it. When it fails, more workloads are disrupted simultaneously.

A single server with 256 cores and 2TB RAM might run 500+ pods. If it has a hardware failure (RAM error, PSU failure, NVMe death), you lose 500 pods at once. Rescheduling 500 pods to other nodes causes:
1. **Resource pressure** on remaining nodes (may not have enough capacity)
2. **Thundering herd** of container image pulls across the cluster
3. **Cascading failures** if the remaining nodes are already near capacity

**Better approach**: Medium-sized servers (64-96 cores, 256-512GB RAM) provide a good balance of density and blast radius. You need enough nodes that losing one does not exceed your N+2 headroom.

**Exception**: GPU servers are inherently large and expensive. For GPU workloads, accept the larger blast radius and compensate with redundancy at the application layer (checkpointing, model replica sets).
</details>

---

## Hands-On Exercise: Size a Kubernetes Cluster

**Task**: Given a workload profile, calculate the hardware requirements for an on-premises Kubernetes cluster.

### Scenario
Your company is deploying a microservices platform:

**Workloads:**
- 120 API pods: 0.5 CPU, 1GB RAM each
- 30 worker pods: 2 CPU, 4GB RAM each
- 10 database pods: 4 CPU, 16GB RAM each
- 5 cache pods: 1 CPU, 8GB RAM each (Redis)
- 15 monitoring pods: 0.25 CPU, 512MB each (Prometheus, Grafana, exporters)

**Requirements:**
- Production environment (high availability)
- 30% headroom for growth
- N+2 node failure tolerance
- etcd on dedicated NVMe

### Steps

1. **Calculate total resource needs:**

```bash
# CPU calculation
API:       120 x 0.5  = 60 cores
Workers:    30 x 2.0  = 60 cores
Databases:  10 x 4.0  = 40 cores
Cache:       5 x 1.0  =  5 cores
Monitoring: 15 x 0.25 =  3.75 cores
                Total = 168.75 cores
         + 30% headroom = 219 cores

# RAM calculation
API:       120 x 1GB   = 120 GB
Workers:    30 x 4GB   = 120 GB
Databases:  10 x 16GB  = 160 GB
Cache:       5 x 8GB   =  40 GB
Monitoring: 15 x 512MB =   7.5 GB
                 Total = 447.5 GB
          + 30% headroom = 582 GB
```

2. **Choose server configuration:**

```bash
# CPU:RAM ratio of workload: 219:582 ≈ 1:2.7 (balanced/slightly memory-heavy)
# Choose: Dual 32-core servers with 256GB RAM
# Note: K8s sees 1 CPU = 1 hyperthread (vCPU), so dual 32-core with SMT = 128 vCPUs

# Per node allocatable:
# CPU: 128 vCPUs - 2 system = 126 vCPUs
# RAM: 256GB - 4GB system = 252GB

# By CPU: 219 / 126 = 2 nodes (rounded up)
# By RAM: 582 / 252 = 3 nodes (rounded up)
# Bottleneck: RAM → need 3 worker nodes

# With N+2: 5 worker nodes
# Plus 3 control plane nodes (dedicated, smaller)

# TOTAL: 8 servers
# - 3x CP: 8 cores, 32GB RAM, 200GB NVMe each
# - 5x Worker: dual 32-core (128 vCPUs), 256GB RAM, 2x 3.84TB NVMe each
```

3. **Estimate costs:**

```bash
# Control plane servers: 3 x ~$6K = $18K
# Worker servers: 5 x ~$15K = $75K
# Networking (2 ToR + cabling): ~$20K
# Total hardware: ~$113K
#
# Compare to cloud (5 x m6i.8xlarge equivalent):
# 5 x $1,228/mo = $6,140/mo = $74K/year = $221K over 3 years
# On-prem 3-year TCO (incl ops): ~$113K + $150K ops = $263K
# On-prem slightly more expensive at this scale — wins at larger scale
```

### Success Criteria
- [ ] Total CPU and RAM calculated with 30% headroom
- [ ] CPU:RAM ratio identified and matched to server profile
- [ ] Node count includes N+2 redundancy
- [ ] Control plane and worker nodes sized separately
- [ ] etcd storage requirement identified (NVMe)
- [ ] Hardware cost estimated and compared to cloud equivalent

---

## Next Module

Continue to [Module 1.3: Cluster Topology Planning](../module-1.3-cluster-topology/) to learn how to organize your clusters — how many, where, and what architecture pattern to use.

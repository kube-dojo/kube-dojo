---
title: "Module 4.1: Storage Architecture Decisions"
slug: on-premises/storage/module-4.1-storage-architecture
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` | Time: 45 minutes
>
> **Prerequisites**: [Module 1.2: Server Sizing](../planning/module-1.2-server-sizing/), [CKA: Storage](../../k8s/cka/part4-storage/)

---

## Why This Module Matters

A data analytics company deployed a 40-node Kubernetes cluster on bare metal with local SATA SSDs in each server. For the first six months, everything worked. Then they deployed Apache Kafka, which needed persistent storage that survived node rescheduling. When a worker node failed, Kafka brokers were rescheduled to new nodes — but their data was on the dead node's local SSDs. They lost 4 hours of event data and spent 3 days manually rebalancing partitions.

They then deployed Ceph via Rook on the same SSDs. Performance dropped 60%. Ceph's replication tripled the write load on drives that were already serving application I/O. The OSD processes competed with Kubernetes workloads for CPU and memory. Their monitoring showed that Ceph rebalancing after a node failure consumed 80% of cluster I/O bandwidth for 4 hours, making all applications sluggish.

The fix was dedicating 6 servers as Ceph OSD nodes with NVMe drives, separated from the Kubernetes worker nodes. Storage traffic ran on a dedicated VLAN with jumbo frames. The lesson: **storage architecture decisions must be made before you buy hardware, not after you deploy workloads.**

---

## What You'll Learn

- Direct-Attached Storage (DAS) vs Network-Attached Storage (NAS) vs SAN
- NVMe vs SSD vs HDD tiering for Kubernetes workloads
- etcd storage requirements (the most demanding component)
- When to use local storage vs distributed storage
- Dedicated storage nodes vs hyper-converged (storage on worker nodes)
- IOPS, throughput, and latency benchmarking

---

## Storage Options for On-Premises K8s

### The Three Storage Models

```
┌─────────────────────────────────────────────────────────────┐
│              STORAGE MODELS                                  │
│                                                               │
│  DAS (Direct-Attached Storage)                              │
│  ┌──────────────────────────────┐                           │
│  │  Server                      │                           │
│  │  ┌──────┐ ┌──────┐ ┌──────┐│                           │
│  │  │NVMe 1│ │NVMe 2│ │NVMe 3││ ← drives inside server   │
│  │  └──────┘ └──────┘ └──────┘│                           │
│  └──────────────────────────────┘                           │
│  ✓ Lowest latency (no network hop)                         │
│  ✓ Highest IOPS (direct PCIe)                              │
│  ✗ Data lost if node fails (no replication)                │
│  ✗ Cannot move PVs between nodes                           │
│  Best for: etcd, databases with app-level replication       │
│                                                               │
│  NAS (Network-Attached Storage)                             │
│  ┌──────────────────────────────┐                           │
│  │  NFS/SMB Server              │                           │
│  │  ┌──────────────────────────┐│  ← shared over network   │
│  │  │  File System (XFS/ZFS)   ││                           │
│  │  │  ┌──────┐ ┌──────┐      ││                           │
│  │  │  │Disk 1│ │Disk 2│ ...  ││                           │
│  │  │  └──────┘ └──────┘      ││                           │
│  │  └──────────────────────────┘│                           │
│  └──────────────────────────────┘                           │
│  ✓ Shared access (ReadWriteMany)                           │
│  ✓ Simple to set up (NFS CSI driver)                       │
│  ✗ Higher latency (network + file protocol overhead)       │
│  ✗ Single point of failure (unless HA NFS)                 │
│  Best for: shared data, ML datasets, media files            │
│                                                               │
│  SDS/SAN (Software-Defined / Storage Area Network)         │
│  ┌──────────────────────────────┐                           │
│  │  Ceph / StorageClass         │                           │
│  │  ┌─────┐ ┌─────┐ ┌─────┐   │  ← distributed across    │
│  │  │OSD 1│ │OSD 2│ │OSD 3│   │    multiple nodes         │
│  │  └─────┘ └─────┘ └─────┘   │                           │
│  │  Data replicated 3x         │                           │
│  └──────────────────────────────┘                           │
│  ✓ Replicated (survives node failures)                     │
│  ✓ PVs can be accessed from any node                       │
│  ✓ Self-healing (auto-rebalances)                          │
│  ✗ Higher latency than DAS (network + replication)         │
│  ✗ Requires dedicated storage nodes (or hyper-converged)   │
│  Best for: general-purpose PVs, databases without replication│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Decision Matrix

| Workload | Storage Type | Why |
|----------|-------------|-----|
| **etcd** | DAS (NVMe) | Requires <10ms p99 fsync; network storage too slow |
| **PostgreSQL** (with streaming replication) | DAS (NVMe) | App handles replication; local NVMe gives best latency |
| **PostgreSQL** (single instance) | Ceph RBD | Needs to survive node failure; no app-level replication |
| **Kafka** | DAS or Ceph | Kafka replicates data; DAS is faster but Ceph is safer |
| **Prometheus TSDB** | DAS (NVMe) | Write-heavy, latency-sensitive; Thanos handles replication |
| **ML training data** | NFS / CephFS | Large datasets, read-heavy, shared access needed |
| **CI/CD workspace** | DAS (SSD) | Ephemeral, high IOPS for builds, data is disposable |
| **Container images** | Ceph RBD or NFS | Harbor/registry storage, moderate IOPS, shared access |
| **Backup targets** | NFS / HDD | Large capacity, low IOPS, cost-optimized |

---

## Storage Tiers

```
┌─────────────────────────────────────────────────────────────┐
│                 STORAGE TIER GUIDE                            │
│                                                               │
│  Tier   Tech           IOPS      Latency   $/TB    Use      │
│  ────   ────           ────      ───────   ────    ───      │
│  0      NVMe Gen5      1M+       <100μs    $300    etcd,    │
│         (PCIe 5.0)                                  hot DB   │
│                                                               │
│  1      NVMe Gen4      500K+     <200μs    $150    App data │
│         (PCIe 4.0)                                  Ceph OSD │
│                                                               │
│  2      SATA SSD       50-100K   1-5ms     $80     Logs,    │
│         (enterprise)                                 bulk    │
│                                                               │
│  3      HDD SAS        100-200   5-15ms    $20     Backup,  │
│         (10K/15K RPM)                               cold     │
│                                                               │
│  CRITICAL RULES:                                             │
│  • etcd: Tier 0 or 1 ONLY (SATA SSD will cause elections)  │
│  • Ceph OSD: Tier 1 minimum (SATA SSD limits throughput)    │
│  • Ceph WAL/DB: Tier 0 on separate device from OSD data    │
│  • Backup: Tier 3 is fine (capacity over speed)             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Dedicated Storage Nodes vs Hyper-Converged

### Dedicated Storage Nodes

```
┌─────────────────────────────────────────────────────────────┐
│          DEDICATED STORAGE NODES                             │
│                                                               │
│  Worker Nodes (compute only):    Storage Nodes (Ceph only): │
│  ┌──────────┐ ┌──────────┐     ┌──────────┐ ┌──────────┐  │
│  │ Worker 1 │ │ Worker 2 │     │ Ceph OSD1│ │ Ceph OSD2│  │
│  │ K8s pods │ │ K8s pods │     │ 12x NVMe │ │ 12x NVMe │  │
│  │ 2x NVMe │ │ 2x NVMe │     │ 256GB RAM│ │ 256GB RAM│  │
│  │ (OS only)│ │ (OS only)│     │ No K8s   │ │ No K8s   │  │
│  └──────────┘ └──────────┘     │ workloads│ │ workloads│  │
│                                 └──────────┘ └──────────┘  │
│                                                               │
│  ✓ No resource contention (storage doesn't compete with pods)│
│  ✓ Storage can have different hardware (more drives, less CPU)│
│  ✓ Storage failures don't affect compute                    │
│  ✗ More servers needed (higher cost)                        │
│  ✗ Network is the bottleneck (all I/O crosses the network)  │
│                                                               │
│  Best for: > 100 nodes, high I/O workloads, regulated envs │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Hyper-Converged (Storage on Worker Nodes)

```
┌─────────────────────────────────────────────────────────────┐
│          HYPER-CONVERGED                                      │
│                                                               │
│  Each worker runs BOTH K8s pods AND Ceph OSD:               │
│  ┌───────────────────┐ ┌───────────────────┐                │
│  │ Worker/OSD Node 1 │ │ Worker/OSD Node 2 │                │
│  │                   │ │                   │                │
│  │ K8s pods          │ │ K8s pods          │                │
│  │ Ceph OSD          │ │ Ceph OSD          │                │
│  │ NVMe 1: OS + pods │ │ NVMe 1: OS + pods │                │
│  │ NVMe 2-4: Ceph    │ │ NVMe 2-4: Ceph    │                │
│  └───────────────────┘ └───────────────────┘                │
│                                                               │
│  ✓ Fewer servers (lower CapEx)                              │
│  ✓ Data locality (pods can read from local OSD)             │
│  ✗ Resource contention (OSD competes with pods for CPU/RAM) │
│  ✗ Node failure loses both compute AND storage              │
│  ✗ Harder to size (need enough CPU/RAM for both)            │
│                                                               │
│  Best for: < 50 nodes, budget-constrained, moderate I/O     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Benchmarking Storage

Always benchmark before deploying workloads:

```bash
# Install fio
apt-get install fio

# Test sequential write throughput (simulates log writes)
fio --name=seq-write \
    --rw=write --bs=128k --direct=1 \
    --size=4g --numjobs=4 --runtime=60 \
    --group_reporting --filename=/data/fio-test

# Test random read IOPS (simulates database reads)
fio --name=rand-read \
    --rw=randread --bs=4k --direct=1 \
    --size=4g --numjobs=8 --runtime=60 \
    --group_reporting --filename=/data/fio-test

# Test etcd-like workload (sequential write with fsync)
fio --name=etcd-wal \
    --rw=write --bs=2300 --fsync=1 \
    --size=22m --runtime=60 --time_based \
    --filename=/data/etcd-test

# Expected results by storage type:
# NVMe Gen4: seq write ~3 GB/s, rand read ~500K IOPS, fsync ~0.1ms
# SATA SSD:  seq write ~500 MB/s, rand read ~80K IOPS, fsync ~2-5ms
# HDD SAS:   seq write ~200 MB/s, rand read ~200 IOPS, fsync ~5-15ms
```

---

## Did You Know?

- **Ceph was created at UC Santa Cruz** as a PhD thesis by Sage Weil in 2004. It became the storage backbone for most OpenStack deployments and is now the default distributed storage for on-premises Kubernetes via Rook.

- **NVMe drives can fail faster under sustained write loads** than SATA SSDs because they have higher write amplification at full speed. Enterprise NVMe drives (like Samsung PM9A3) have much higher endurance (DWPD — Drive Writes Per Day) than consumer NVMe. Always use enterprise-grade drives for Ceph OSDs.

- **A single NVMe drive provides more IOPS than an entire SAN array from 10 years ago.** A Samsung PM9A3 (3.84TB) delivers 1M random read IOPS. A mid-range EMC VNX from 2014 delivered ~200K IOPS from 120 spinning disks. Modern on-prem storage can outperform legacy enterprise storage at 1/10th the cost.

- **Kubernetes persistent volumes are statically provisioned by default** — you create a PV manually and a PVC claims it. Dynamic provisioning (via StorageClass + CSI driver) is essential for on-prem. Without it, every PV request becomes a manual ticket.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| SATA SSD for etcd | Leader elections under load | NVMe only for etcd (Tier 0 or 1) |
| Hyper-converged without resource limits | Ceph OSD steals CPU/RAM from pods | Use cgroup limits: `2 cores + 4GB per OSD` |
| No separate storage network | Ceph replication competes with pod traffic | Dedicated VLAN with jumbo frames for storage |
| Single replication factor | Data loss on node failure | Ceph replication factor 3 (tolerates 1 failure) |
| Ceph on worker nodes at scale | Rebalancing kills application performance | Dedicated storage nodes above 100 nodes |
| Not benchmarking before deploy | Discover performance issues in production | fio benchmark on every storage tier before use |
| Mixing drive types in one pool | Inconsistent performance across PVs | Separate storage classes per tier |
| No monitoring for disk health | Drives fail silently until data loss | smartctl monitoring + Prometheus alerts |

---

## Quiz

### Question 1
You need persistent storage for a PostgreSQL database that uses streaming replication across 3 pods. Should you use local NVMe or Ceph RBD?

<details>
<summary>Answer</summary>

**Local NVMe (DAS).**

PostgreSQL with streaming replication handles data replication at the application level — each replica maintains its own copy of the data. Adding Ceph replication on top would mean triple replication (Ceph 3x) times triple replication (PostgreSQL 3 replicas) = 9 copies of every write. This wastes storage and adds unnecessary latency.

With local NVMe:
- Write latency: <0.1ms (direct PCIe, no network)
- No double-replication overhead
- If a node fails, PostgreSQL promotes a replica (application-level failover)

Use `local-path-provisioner` or `TopoLVM` as the CSI driver for local NVMe volumes with topology awareness.

**Exception**: If PostgreSQL is a single instance without replication (dev/test), use Ceph RBD so the volume can be remounted on another node if the original fails.
</details>

### Question 2
Your Ceph cluster shows 80% I/O bandwidth consumed during rebalancing after a node failure. How do you prevent this from affecting application performance?

<details>
<summary>Answer</summary>

**Limit Ceph recovery/backfill bandwidth:**

```bash
# Set recovery limits (Ceph CLI)
ceph config set osd osd_recovery_max_active 1          # default 3
ceph config set osd osd_recovery_sleep 0.5              # 500ms sleep between ops
ceph config set osd osd_max_backfills 1                 # default 1
ceph config set osd osd_recovery_op_priority 1          # lowest priority (default 3)

# Set client I/O priority higher than recovery
ceph config set osd osd_client_op_priority 63           # highest priority
```

**Architectural solutions:**
1. **Dedicated storage network**: Recovery traffic on VLAN 30, application I/O on VLAN 20
2. **More OSDs**: Distribute data across more drives so each OSD rebalances less data
3. **Faster drives**: NVMe for OSDs so recovery completes faster
4. **Spare capacity**: Keep cluster below 70% utilization so rebalancing has headroom
</details>

### Question 3
What is the minimum number of Ceph OSD nodes for a production deployment, and why?

<details>
<summary>Answer</summary>

**Minimum 3 OSD nodes** with replication factor 3.

Why 3:
- Ceph replicates each object to N different OSDs (default N=3)
- Each replica must be on a different failure domain (different node)
- With 3 nodes, each object has one copy on each node
- If one node fails, 2 copies remain (no data loss)
- Ceph can rebuild the third copy using the remaining 2

**Why not 2**: With replication factor 3 and only 2 nodes, Ceph cannot place 3 replicas on 3 different nodes. It will either place 2 replicas on one node (unsafe) or refuse to create the volume.

**Recommended for production**: 5+ OSD nodes. This allows:
- Node failure with no capacity pressure
- Rolling maintenance (take one node offline, still have 4)
- Better data distribution (more OSDs = more even load)
</details>

### Question 4
Your etcd nodes use SATA SSDs and you see frequent leader elections. Explain the root cause and the fix.

<details>
<summary>Answer</summary>

**Root cause**: etcd uses Raft consensus, which requires the leader to fsync the Write-Ahead Log (WAL) on every write. SATA SSDs have fsync latency of 2-10ms (99th percentile). Under load, this can spike to 20-50ms.

etcd's heartbeat interval is 100ms, and the election timeout is 1,000ms (10x heartbeat). If the leader's fsync latency consistently exceeds 50ms, it cannot process writes fast enough to send heartbeats within the 100ms interval. Followers assume the leader is dead and trigger an election. During the election, the cluster is read-only.

**Fix**: Replace SATA SSDs with NVMe drives for etcd data directory (`/var/lib/etcd`). NVMe fsync latency is 0.05-0.5ms (99th percentile) — 10-100x faster than SATA.

**Verification**:
```bash
# Before (SATA SSD):
etcdctl check perf
# ... PASS: Throughput is ... FAIL: Slowest request took ...

# After (NVMe):
etcdctl check perf
# ... PASS: Throughput is ... PASS: Slowest request took ...
```

This is one of the most common on-premises Kubernetes issues and is entirely preventable by selecting the right storage during hardware procurement.
</details>

---

## Hands-On Exercise: Benchmark Storage Tiers

**Task**: Benchmark different storage types and compare performance.

```bash
# Create a test directory
mkdir -p /tmp/storage-benchmark

# Test 1: Sequential write throughput
echo "=== Sequential Write ==="
fio --name=seq-write --rw=write --bs=128k --direct=1 \
    --size=1g --numjobs=1 --runtime=30 --time_based \
    --group_reporting --filename=/tmp/storage-benchmark/seq-test

# Test 2: Random read IOPS
echo "=== Random Read IOPS ==="
fio --name=rand-read --rw=randread --bs=4k --direct=1 \
    --size=1g --numjobs=4 --runtime=30 --time_based \
    --group_reporting --filename=/tmp/storage-benchmark/iops-test

# Test 3: etcd WAL simulation
echo "=== etcd WAL (fsync) ==="
fio --name=etcd-wal --rw=write --bs=2300 --fsync=1 \
    --size=22m --runtime=30 --time_based \
    --filename=/tmp/storage-benchmark/etcd-test

# Record results and compare against the tier guide above
# NVMe should show: >1 GB/s seq, >100K IOPS rand, <1ms fsync
# SATA SSD: ~400 MB/s seq, ~50K IOPS rand, ~2-5ms fsync

# Cleanup
rm -rf /tmp/storage-benchmark
```

### Success Criteria
- [ ] Sequential write throughput measured (MB/s)
- [ ] Random read IOPS measured
- [ ] fsync latency measured (p99)
- [ ] Results compared against tier guide
- [ ] Storage tier identified for the tested device

---

## Next Module

Continue to [Module 4.2: Software-Defined Storage (Ceph/Rook)](module-4.2-ceph-rook/) to learn how to deploy and operate Ceph as distributed storage for Kubernetes.

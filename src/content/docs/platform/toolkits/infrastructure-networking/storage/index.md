---
title: "K8s Storage Deep Dive Toolkit"
sidebar:
  order: 1
  label: "Storage"
---
> **Toolkit Track** | 3 Modules | ~2.5 hours total

## Overview

The K8s Storage Deep Dive Toolkit covers software-defined storage solutions that run on Kubernetes itself. Instead of depending on cloud-provider storage or external SANs, these tools turn your cluster nodes into a distributed storage platform. This is essential for bare-metal deployments, multi-cloud portability, and use cases where you need full control over your data layer.

This toolkit applies concepts from [Distributed Systems Foundation](../../../foundations/distributed-systems/) and [Reliability Engineering Foundation](../../../foundations/reliability-engineering/).

## Prerequisites

Before starting this toolkit:
- Solid Kubernetes fundamentals (PersistentVolumes, PVCs, StorageClasses, CSI)
- Understanding of StatefulSets and volume lifecycle
- Basic Linux storage concepts (block devices, filesystems, object storage)
- [Distributed Systems Foundation](../../../foundations/distributed-systems/) - Replication, consistency
- [Reliability Engineering Foundation](../../../foundations/reliability-engineering/) - SLOs, failure modes

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 16.1 | [Rook/Ceph](module-16.1-rook-ceph/) | `[COMPLEX]` | 55-65 min |
| 16.2 | [MinIO](module-16.2-minio/) | `[MEDIUM]` | 45-50 min |
| 16.3 | [Longhorn](module-16.3-longhorn/) | `[MEDIUM]` | 45-55 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy Rook/Ceph** — Full-featured distributed storage providing block, filesystem, and object from one cluster
2. **Run MinIO** — S3-compatible object storage for ML pipelines, backup targets, and artifact storage
3. **Use Longhorn** — Lightweight distributed block storage with built-in backup and DR
4. **Choose the right storage** — Understand trade-offs between Rook/Ceph, MinIO, Longhorn, and cloud storage

## Tool Selection Guide

```
WHICH KUBERNETES STORAGE SOLUTION?
─────────────────────────────────────────────────────────────────

"I need block, filesystem, AND object storage from one platform"
└──▶ Rook/Ceph
     • Enterprise-grade, battle-tested at scale
     • Three storage types from one cluster
     • Highest operational complexity
     • Best for: large clusters, bare-metal, full storage platform

"I need S3-compatible object storage on K8s"
└──▶ MinIO
     • High-performance object storage
     • Drop-in S3 replacement
     • Great for ML pipelines, log backends, artifact storage
     • Best for: object storage workloads, Loki/Tempo backends

"I need simple, reliable block storage for K8s"
└──▶ Longhorn
     • Lightweight and easy to operate
     • Built-in backup to S3
     • Incremental snapshots, DR across clusters
     • Best for: edge, small-medium clusters, simplicity

"I'm on a single cloud and want managed storage"
└──▶ Cloud Provider CSI (EBS, GCE PD, Azure Disk)
     • Zero operational burden
     • Limited to one cloud
     • No multi-cloud portability
     • Best for: single-cloud deployments

COMPARISON MATRIX:
─────────────────────────────────────────────────────────────────
                    Rook/Ceph    MinIO        Longhorn     Cloud CSI
─────────────────────────────────────────────────────────────────
Block storage       ✓✓           ✗            ✓✓           ✓✓
Shared filesystem   ✓✓ (CephFS)  ✗            ✗            ✗*
Object storage      ✓ (RGW)      ✓✓           ✗            Managed**
Performance         ✓✓           ✓✓           ✓            ✓
Operational burden  High         Medium       Low          None
Multi-cloud         ✓            ✓            ✓            ✗
Bare-metal          ✓✓           ✓            ✓            ✗
Backup/DR           ✓            ✓            ✓✓           ✓
CNCF status         Graduated    ✗            Incubating   N/A
Min cluster size    3 nodes      4 nodes      3 nodes      1 node

* EFS/Filestore available as managed add-ons
** S3/GCS/Azure Blob are separate managed services
```

## The Storage-on-Kubernetes Evolution

```
┌─────────────────────────────────────────────────────────────────┐
│           STORAGE ON KUBERNETES - THE EVOLUTION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  2015-2017: "STATELESS ONLY"                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • hostPath was the only option                           │  │
│  │  • No CSI standard                                        │  │
│  │  • "Kubernetes is for stateless apps"                     │  │
│  │  • Persistent storage was an afterthought                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  2018-2020: "CSI CHANGES EVERYTHING"                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • CSI (Container Storage Interface) standardized         │  │
│  │  • Rook reached v1.0, joined CNCF                         │  │
│  │  • Longhorn created by Rancher Labs                       │  │
│  │  • MinIO Operator launched                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  2021-NOW: "SOFTWARE-DEFINED STORAGE IS MAINSTREAM"             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Rook graduated CNCF (2020)                             │  │
│  │  • Longhorn joined CNCF Incubating (2021)                 │  │
│  │  • MinIO became go-to for S3 on K8s                       │  │
│  │  • Bare-metal K8s storage is production-ready             │  │
│  │  • DoK (Data on Kubernetes) community thriving            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 16.1: Rook/Ceph
     │
     │  Full storage platform (block + FS + object)
     │  Ceph architecture and Rook operator
     │  Enterprise-scale storage
     ▼
Module 16.2: MinIO
     │
     │  S3-compatible object storage
     │  ML pipelines, backup targets
     │  High-performance object workloads
     ▼
Module 16.3: Longhorn
     │
     │  Lightweight block storage
     │  Backup, DR, snapshots
     │  When to use which storage solution
     ▼
[Toolkit Complete] → Cloud-Native Databases or Security Tools
```

## Architecture Patterns

### Converged Storage (Rook/Ceph)

```
CONVERGED STORAGE - ONE CLUSTER, THREE STORAGE TYPES
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Rook Operator                       │   │
│  └──────────┬───────────────┬──────────────┬────────────┘   │
│             │               │              │                 │
│         Block (RBD)    Filesystem      Object (RGW)         │
│             │          (CephFS)            │                 │
│             ▼               ▼              ▼                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Databases   │  │   ML Data    │  │  Backups     │      │
│  │  StatefulSets│  │  Shared Vols │  │  Artifacts   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Ceph Storage Cluster                      │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐     │   │
│  │  │ OSD    │  │ OSD    │  │ OSD    │  │ OSD    │     │   │
│  │  │ /dev/  │  │ /dev/  │  │ /dev/  │  │ /dev/  │     │   │
│  │  │ sdb    │  │ sdb    │  │ sdb    │  │ sdb    │     │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘     │   │
│  │   Node 1      Node 2      Node 3      Node 4        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Rook/Ceph | Deploy Rook/Ceph on kind, create StorageClass, provision block and filesystem PVCs |
| MinIO | Deploy MinIO, create bucket, upload/download objects with mc CLI |
| Longhorn | Deploy Longhorn, create PVCs, test replica failover and snapshots |

## Related Tracks

- **Before**: [Distributed Systems Foundation](../../../foundations/distributed-systems/) — Replication, consensus
- **Before**: [Reliability Engineering Foundation](../../../foundations/reliability-engineering/) — SLOs, failure modes
- **Related**: [Cloud-Native Databases](../../data-ai-platforms/cloud-native-databases/) — Databases that run on this storage
- **Related**: [Scaling & Reliability](../../developer-experience/scaling-reliability/) — Velero for backup
- **Related**: [Observability Toolkit](../../observability-intelligence/observability/) — Storage monitoring

---

*"Storage is the foundation that everything stateful sits on. Get it wrong, and your databases, ML pipelines, and backups all inherit the same problems."*

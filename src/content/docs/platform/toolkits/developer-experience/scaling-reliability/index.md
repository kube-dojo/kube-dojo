---
title: "Scaling & Reliability Toolkit"
sidebar:
  order: 1
  label: "Scaling & Reliability"
---
> **Toolkit Track** | 3 Modules | ~2.5 hours total

## Overview

The Scaling & Reliability Toolkit covers advanced autoscaling and disaster recovery for Kubernetes. Karpenter provides intelligent node provisioning, KEDA enables event-driven workload scaling, and Velero ensures you can recover from disasters.

This toolkit applies concepts from [SRE Discipline](../../../disciplines/core-platform/sre/) and [Reliability Engineering](../../../foundations/reliability-engineering/).

## Prerequisites

Before starting this toolkit:
- [SRE Discipline](../../../disciplines/core-platform/sre/) — Scaling and reliability concepts
- Kubernetes HPA basics
- Persistent Volume concepts
- Cloud provider fundamentals

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 6.1 | [Karpenter](module-6.1-karpenter/) | `[COMPLEX]` | 45-50 min |
| 6.2 | [KEDA](module-6.2-keda/) | `[MEDIUM]` | 40-45 min |
| 6.3 | [Velero](module-6.3-velero/) | `[MEDIUM]` | 40-45 min |
| 6.4 | [FinOps with OpenCost](module-6.4-finops-opencost/) | `[MEDIUM]` | 40-45 min |
| 6.5 | [Chaos Engineering](module-6.5-chaos-engineering/) | `[COMPLEX]` | 50 min |
| 6.6 | [Knative](module-6.6-knative/) | `[MEDIUM]` | 40-45 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Configure Karpenter** — Intelligent node provisioning, spot instances, consolidation
2. **Implement KEDA** — Event-driven scaling, scale to zero, custom metrics
3. **Set up Velero** — Backups, restores, cluster migration
4. **Design for reliability** — Autoscaling strategies, disaster recovery plans

## Tool Selection Guide

```
WHICH SCALING/RELIABILITY TOOL?
─────────────────────────────────────────────────────────────────

"I need faster, smarter node autoscaling"
└──▶ Karpenter
     • Provisions nodes in seconds
     • Right-sizes for actual workloads
     • Automatic consolidation
     • Better than Cluster Autoscaler

"I need to scale workloads on queues/events"
└──▶ KEDA
     • 60+ scalers (SQS, Kafka, Prometheus...)
     • Scale to zero
     • Event-driven, not just metrics

"I need backup and disaster recovery"
└──▶ Velero
     • Application-aware backups
     • PV snapshots
     • Cross-cluster migration

SCALING COMPARISON:
─────────────────────────────────────────────────────────────────
                     HPA        Cluster-AS    Karpenter     KEDA
─────────────────────────────────────────────────────────────────
Scales              Pods        Nodes         Nodes         Pods
Based on            CPU/mem     Pending pods  Pending pods  Any metric
Min replicas        1           ASG min       0 (with KEDA) 0
Speed               Seconds     Minutes       Seconds       Seconds
Custom metrics      Complex     N/A           N/A           Built-in
```

## The Reliability Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                KUBERNETES RELIABILITY STACK                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WORKLOAD SCALING                                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  HPA (CPU/memory)  │  KEDA (events, custom metrics)       │ │
│  │  VPA (right-size)  │  Custom metrics adapter              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  NODE SCALING                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Karpenter (intelligent)  │  Cluster Autoscaler (legacy)  │ │
│  │  Node pools              │  Auto-scaling groups           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  DISASTER RECOVERY                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Velero (application)     │  etcd backup (cluster)        │ │
│  │  PV snapshots            │  GitOps (configuration)        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 6.1: Karpenter
     │
     │  Node provisioning fundamentals
     │  Spot instances, consolidation
     ▼
Module 6.2: KEDA
     │
     │  Event-driven workload scaling
     │  Custom metric triggers
     ▼
Module 6.3: Velero
     │
     │  Backup and disaster recovery
     │  Cluster migration
     ▼
[Toolkit Complete] → Platforms Toolkit
```

## Key Concepts

### Scaling Levels

| Level | Tool | What Scales | Trigger |
|-------|------|-------------|---------|
| **Application** | HPA, KEDA | Pod replicas | Metrics, events |
| **Infrastructure** | Karpenter | Nodes | Pending pods |
| **Cost** | Karpenter + Spot | Instance types | Availability, price |

### Reliability Layers

```
RELIABILITY LAYERS
─────────────────────────────────────────────────────────────────

1. PREVENT OUTAGES
   • HPA/KEDA: Scale before overload
   • Karpenter: Provision capacity fast
   • Pod disruption budgets: Safe updates

2. SURVIVE OUTAGES
   • Multi-AZ: Survive zone failure
   • Spot instance handling: Graceful interruption
   • Circuit breakers: Prevent cascade

3. RECOVER FROM OUTAGES
   • Velero: Restore applications
   • etcd backup: Restore cluster
   • GitOps: Rebuild from source
```

## Common Architectures

### High-Availability Scaling

```
HA SCALING ARCHITECTURE
─────────────────────────────────────────────────────────────────

                    ┌─────────────┐
                    │   Metrics   │
                    │  (Prom/CW)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         ┌────────┐   ┌────────┐   ┌────────┐
         │  HPA   │   │  KEDA  │   │ Custom │
         │ (CPU)  │   │(events)│   │  Alert │
         └────┬───┘   └────┬───┘   └────┬───┘
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Deployment │
                    │  (replicas) │
                    └──────┬──────┘
                           │
                           │ Pending pods?
                           ▼
                    ┌─────────────┐
                    │  Karpenter  │
                    │   (nodes)   │
                    └─────────────┘
```

### Disaster Recovery Architecture

```
DR ARCHITECTURE
─────────────────────────────────────────────────────────────────

PRIMARY CLUSTER                    DR CLUSTER
(us-west-2)                       (us-east-1)

┌─────────────────┐              ┌─────────────────┐
│   Production    │              │   Standby       │
│   Workloads     │              │   (scaled down) │
└────────┬────────┘              └────────┬────────┘
         │                                │
         │ Velero backup                  │
         ▼                                │
┌─────────────────┐                       │
│   S3 Bucket     │───── Replication ────▶│
│  (backups)      │                       │
└─────────────────┘              ┌────────▼────────┐
                                 │   S3 Bucket     │
                                 │  (replica)      │
                                 └─────────────────┘

FAILOVER: Restore from replicated backup to DR cluster
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Karpenter | Configure NodePool, observe provisioning |
| KEDA | Scale on Prometheus metrics, test zero |
| Velero | Backup namespace, delete, restore |

## Related Tracks

- **Before**: [SRE Discipline](../../../disciplines/core-platform/sre/) — SRE concepts
- **Before**: [Reliability Engineering](../../../foundations/reliability-engineering/) — Theory
- **Related**: [IaC Tools Toolkit](../../infrastructure-networking/iac-tools/) — Terraform modules for Karpenter, KEDA
- **Related**: [Observability Toolkit](../../observability-intelligence/observability/) — Metrics for scaling
- **After**: [Platforms Toolkit](../../infrastructure-networking/platforms/) — Platform features

---

*"Scale automatically. Recover gracefully. Sleep peacefully."*

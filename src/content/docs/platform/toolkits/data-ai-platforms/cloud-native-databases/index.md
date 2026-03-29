---
title: "Cloud-Native Databases Toolkit"
sidebar:
  order: 1
  label: "Cloud-Native Databases"
---
> **Toolkit Track** | 5 Modules | ~4 hours total

## Overview

The Cloud-Native Databases Toolkit covers running databases on Kubernetes—something that went from "don't do it" to "actually, it's great now" in just a few years. Modern operators, distributed architectures, and serverless models have made stateful workloads on Kubernetes not just viable, but often preferable to traditional deployments.

This toolkit applies concepts from [Distributed Systems Foundation](../../../foundations/distributed-systems/) and [Reliability Engineering Foundation](../../../foundations/reliability-engineering/).

## Prerequisites

Before starting this toolkit:
- Solid Kubernetes fundamentals (StatefulSets, PVCs, Services)
- Basic SQL and database concepts
- Understanding of replication and high availability
- [Distributed Systems Foundation](../../../foundations/distributed-systems/) - Consensus, consistency
- [Reliability Engineering Foundation](../../../foundations/reliability-engineering/) - SLOs, failure modes

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 15.1 | [CockroachDB](module-15.1-cockroachdb/) | `[COMPLEX]` | 55-65 min |
| 15.2 | [CloudNativePG](module-15.2-cloudnativepg/) | `[MEDIUM]` | 45-50 min |
| 15.3 | [Neon & PlanetScale](module-15.3-serverless-databases/) | `[MEDIUM]` | 40-45 min |
| 15.4 | [Vitess](module-15.4-vitess/) | `[COMPLEX]` | 50-55 min |
| 15.5 | [etcd-operator](module-15.5-etcd-operator/) | `[MEDIUM]` | 40-45 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy CockroachDB** — Globally distributed SQL that survives regional failures
2. **Run PostgreSQL on K8s** — CloudNativePG operator for day-2 operations
3. **Use serverless databases** — Neon and PlanetScale for developer productivity
4. **Scale MySQL horizontally** — Vitess for YouTube/Slack-scale sharding
5. **Manage etcd with operators** — etcd-operator for automated TLS, upgrades, and cluster lifecycle
6. **Choose the right database** — Understand trade-offs for your use case

## Tool Selection Guide

```
WHICH CLOUD-NATIVE DATABASE?
─────────────────────────────────────────────────────────────────

"I need multi-region, survive datacenter failures"
└──▶ CockroachDB
     • Distributed SQL (PostgreSQL wire protocol)
     • Automatic sharding and rebalancing
     • Strong consistency across regions
     • Sleep through outages

"I want PostgreSQL with great K8s operations"
└──▶ CloudNativePG
     • Best PostgreSQL operator
     • Declarative configuration
     • Automated failover, backups, PITR
     • You manage the database, not K8s complexity

"I need database branching for dev/preview environments"
└──▶ Neon or PlanetScale
     • Branch databases like git branches
     • Serverless scaling (pay for usage)
     • Neon = PostgreSQL, PlanetScale = MySQL
     • Perfect for preview environments

"I need to scale MySQL to millions of QPS"
└──▶ Vitess
     • Horizontal MySQL sharding
     • YouTube, Slack, Square scale
     • Keep your MySQL app, add scale
     • Complex but proven

"I need simple, single-node database on K8s"
└──▶ CloudNativePG or Bitnami charts
     • Don't over-engineer
     • Simple HA with replicas
     • Managed backups to S3

COMPARISON MATRIX:
─────────────────────────────────────────────────────────────────
                    CockroachDB  CloudNativePG  Neon     Vitess
─────────────────────────────────────────────────────────────────
Database type       Distributed  PostgreSQL     Postgres MySQL
Multi-region        ✓✓           Manual         ✓        Manual
Auto-sharding       ✓            ✗              ✓        ✓✓
Consistency         Strong       Strong         Strong   Eventually*
Wire protocol       PostgreSQL   PostgreSQL     Postgres MySQL
Serverless          ✓ (cloud)    ✗              ✓✓       ✗
Database branching  ✗            ✗              ✓✓       ✗
K8s native          ✓            ✓✓             Managed  ✓
Self-hosted cost    $$$          $              N/A      $$
Operational burden  Medium       Low            None     High
CNCF status         ✗            Sandbox        ✗        Graduated

* Vitess supports various consistency modes
```

## The Database-on-Kubernetes Evolution

```
┌─────────────────────────────────────────────────────────────────┐
│           DATABASES ON KUBERNETES - THE EVOLUTION                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  2015-2017: "DON'T RUN DATABASES ON KUBERNETES"                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • StatefulSets were new and scary                        │  │
│  │  • Persistent volumes unreliable                          │  │
│  │  • No good operators                                      │  │
│  │  • "Pets vs cattle" mentality                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  2018-2020: "MAYBE FOR DEV/TEST..."                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Operators emerged (Zalando, KubeDB)                    │  │
│  │  • CSI standardized storage                               │  │
│  │  • Success stories appeared                               │  │
│  │  • Still nervous about production                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  2021-NOW: "ACTUALLY, IT'S GREAT"                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • CloudNativePG (CNCF Sandbox)                           │  │
│  │  • CockroachDB on K8s is default                          │  │
│  │  • Vitess (CNCF Graduated)                                │  │
│  │  • Major banks running production DBs on K8s              │  │
│  │  • DoK (Data on Kubernetes) community thriving            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  THE FUTURE: SERVERLESS + KUBERNETES HYBRID                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Neon, PlanetScale for dev/preview                      │  │
│  │  • Self-hosted for production compliance                  │  │
│  │  • eBPF for database observability                        │  │
│  │  • AI-assisted query optimization                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Why Databases on Kubernetes?

```
BENEFITS OF DATABASES ON KUBERNETES
─────────────────────────────────────────────────────────────────

✓ UNIFIED OPERATIONS
  └── Same tools (kubectl, Helm, ArgoCD) for apps AND databases
      Same monitoring (Prometheus), same alerts, same runbooks

✓ DECLARATIVE CONFIGURATION
  └── Database config in Git, version controlled
      "I want 3 replicas with 100GB storage" = YAML

✓ AUTOMATED DAY-2 OPERATIONS
  └── Operators handle: failover, backups, scaling, upgrades
      No more 3 AM manual failover procedures

✓ CONSISTENCY WITH APPLICATIONS
  └── Same deployment patterns, same CI/CD pipelines
      Database changes go through same review process

✓ COST EFFICIENCY (sometimes)
  └── Right-size database instances
      Scale down dev/test environments
      Bin-packing with other workloads

RISKS TO CONSIDER
─────────────────────────────────────────────────────────────────

⚠ STORAGE COMPLEXITY
  └── CSI driver quality varies
      Local NVMe vs network storage trade-offs
      Snapshot/backup integration

⚠ NETWORKING
  └── Pod IP changes on restart (use Services)
      Cross-AZ latency for replicas
      Network policies for security

⚠ RESOURCE CONTENTION
  └── "Noisy neighbor" with shared nodes
      Need proper resource limits and node affinity
      Consider dedicated node pools for databases

⚠ OPERATIONAL MATURITY
  └── Team needs K8s AND database expertise
      Debugging is harder (more layers)
      Disaster recovery is different
```

## Architecture Patterns

### Single-Region HA (Most Common)

```
SINGLE-REGION HIGH AVAILABILITY
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                     (3 Availability Zones)                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 CloudNativePG Cluster                │    │
│  │                                                      │    │
│  │   AZ-1              AZ-2              AZ-3          │    │
│  │  ┌──────┐         ┌──────┐         ┌──────┐        │    │
│  │  │ Pod  │         │ Pod  │         │ Pod  │        │    │
│  │  │PRIMARY│◄───────│REPLICA│         │REPLICA│        │    │
│  │  └──┬───┘  sync   └──┬───┘  async  └──┬───┘        │    │
│  │     │                │                │             │    │
│  │  ┌──┴───┐         ┌──┴───┐         ┌──┴───┐        │    │
│  │  │ PVC  │         │ PVC  │         │ PVC  │        │    │
│  │  │100GB │         │100GB │         │100GB │        │    │
│  │  └──────┘         └──────┘         └──────┘        │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                    ┌───────┴───────┐                        │
│                    │   Service     │                        │
│                    │  (LoadBalancer)│                       │
│                    └───────────────┘                        │
│                            │                                 │
└────────────────────────────┼────────────────────────────────┘
                             │
                      Application Pods
```

### Multi-Region Active-Active

```
MULTI-REGION WITH COCKROACHDB
─────────────────────────────────────────────────────────────────

┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│    US-EAST        │     │    US-WEST        │     │    EU-WEST        │
│                   │     │                   │     │                   │
│  ┌─────────────┐  │     │  ┌─────────────┐  │     │  ┌─────────────┐  │
│  │ CockroachDB │◄─┼─────┼─▶│ CockroachDB │◄─┼─────┼─▶│ CockroachDB │  │
│  │   Nodes     │  │     │  │   Nodes     │  │     │  │   Nodes     │  │
│  └─────────────┘  │     │  └─────────────┘  │     │  └─────────────┘  │
│        │         │     │        │         │     │        │         │
│        ▼          │     │        ▼          │     │        ▼          │
│   ┌─────────┐     │     │   ┌─────────┐     │     │   ┌─────────┐     │
│   │  Apps   │     │     │   │  Apps   │     │     │   │  Apps   │     │
│   └─────────┘     │     │   └─────────┘     │     │   └─────────┘     │
│        ▲          │     │        ▲          │     │        ▲          │
│        │          │     │        │          │     │        │          │
└────────┼──────────┘     └────────┼──────────┘     └────────┼──────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                          Global Load Balancer
                          (GeoDNS / Anycast)

• Writes go to any region (CockroachDB handles consensus)
• Reads are local (low latency)
• Region failure = automatic failover
• Data locality controls for compliance
```

### Serverless for Development

```
SERVERLESS DATABASE WORKFLOW
─────────────────────────────────────────────────────────────────

Developer Workflow with Neon:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  main branch (production)                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │████████████████████████████████████ 500GB data       │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                    │
│       │ git checkout -b feature/new-schema                 │
│       │ neon branch create feature/new-schema              │
│       ▼                                                    │
│  feature branch (copy-on-write, instant)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │████████████████████████████████████ 500GB (shared)   │   │
│  │░░░░░░░░░ Changes only (10MB)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                    │
│       │ Run migrations, test, PR approved                  │
│       │                                                    │
│       ▼                                                    │
│  Merge to main                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │████████████████████████████████████ 500GB + changes  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Feature branch deleted (only paid for 10MB, not 500GB)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 15.1: CockroachDB
     │
     │  Distributed SQL fundamentals
     │  Multi-region deployment
     │  Consensus and consistency
     ▼
Module 15.2: CloudNativePG
     │
     │  PostgreSQL on Kubernetes
     │  Operator-managed operations
     │  Backup and restore
     ▼
Module 15.3: Neon & PlanetScale
     │
     │  Serverless database model
     │  Database branching
     │  Developer productivity
     ▼
Module 15.4: Vitess
     │
     │  Horizontal MySQL sharding
     │  Migration from monolith
     │  Extreme scale patterns
     ▼
[Toolkit Complete] → IaC Tools or Security Tools
```

## Key Concepts

### CAP Theorem in Practice

```
CAP THEOREM - PICK TWO
─────────────────────────────────────────────────────────────────

                    Consistency
                        │
                        │
            ┌───────────┴───────────┐
            │                       │
            │    CockroachDB        │
            │    (CP - sacrifices   │
            │     availability      │
            │     during network    │
            │     partitions)       │
            │                       │
Availability├───────────────────────┤Partition
            │                       │ Tolerance
            │    Cassandra          │
            │    (AP - sacrifices   │
            │     consistency       │
            │     for availability) │
            │                       │
            └───────────────────────┘

REALITY CHECK:
─────────────────────────────────────────────────────────────────
• Network partitions are rare but happen
• "Consistency" has different meanings (linearizable vs eventual)
• Most cloud-native DBs are "CP" with good availability
• CockroachDB: 99.99% available while strongly consistent
• Trade-offs are about WHAT happens during rare partitions
```

### Operators and Custom Resources

```yaml
# CloudNativePG Custom Resource
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: my-postgres
spec:
  instances: 3

  storage:
    size: 100Gi
    storageClass: premium-ssd

  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"

  backup:
    barmanObjectStore:
      destinationPath: s3://my-backups/postgres
      s3Credentials:
        accessKeyId:
          name: backup-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: gzip

  # Automated operations the operator handles:
  # ✓ Leader election and failover
  # ✓ Replica synchronization
  # ✓ Continuous WAL archiving
  # ✓ Point-in-time recovery
  # ✓ Certificate rotation
  # ✓ Configuration changes (rolling restart)
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| CockroachDB | Deploy 3-region cluster, simulate region failure |
| CloudNativePG | Deploy cluster, perform failover, restore from backup |
| Neon/PlanetScale | Create database branches, test schema migrations |
| Vitess | Shard a MySQL database, run cross-shard queries |

## Cost Considerations

```
TOTAL COST COMPARISON (100GB, 10K QPS workload)
─────────────────────────────────────────────────────────────────

CockroachDB Self-Hosted (3 nodes):
├── Compute: 3x 8 vCPU, 32GB ≈ $600/month
├── Storage: 3x 200GB SSD ≈ $60/month
├── Bandwidth: Inter-region ≈ $100/month
├── Engineering: 0.2 FTE ≈ $3,000/month
└── Total: ~$3,800/month

CockroachDB Serverless:
├── Storage: 100GB × $1 ≈ $100/month
├── Compute: 10K RU/s × $0.20 ≈ $200/month
└── Total: ~$300/month (but less control)

CloudNativePG Self-Hosted (3 replicas):
├── Compute: 3x 4 vCPU, 16GB ≈ $300/month
├── Storage: 3x 100GB SSD ≈ $30/month
├── Engineering: 0.1 FTE ≈ $1,500/month
└── Total: ~$1,830/month

RDS PostgreSQL (Multi-AZ):
├── Instance: db.r6g.xlarge × 2 ≈ $500/month
├── Storage: 100GB gp3 ≈ $15/month
├── Engineering: Minimal
└── Total: ~$515/month + less control

Neon (Serverless PostgreSQL):
├── Storage: 100GB × $0.25 ≈ $25/month
├── Compute: Pay per active time
└── Total: ~$50-200/month (depends on usage)

WHEN SELF-HOSTED WINS:
─────────────────────────────────────────────────────────────────
• Multi-cloud / hybrid requirements
• Data residency / compliance
• Extreme scale (>1PB, >1M QPS)
• Already have K8s expertise

WHEN MANAGED/SERVERLESS WINS:
─────────────────────────────────────────────────────────────────
• Small-medium scale
• Developer productivity priority
• Limited platform team
• Variable workloads (scale to zero)
```

## Related Tracks

- **Before**: [Distributed Systems Foundation](../../../foundations/distributed-systems/) — Consensus, consistency
- **Before**: [Reliability Engineering Foundation](../../../foundations/reliability-engineering/) — SLOs, failure modes
- **Related**: [Observability Toolkit](../../observability-intelligence/observability/) — Database monitoring
- **Related**: [GitOps & Deployments](../../cicd-delivery/gitops-deployments/) — Database GitOps
- **Related**: [Security Tools](../../security-quality/security-tools/) — Database encryption, access control

---

*"The question isn't 'should I run databases on Kubernetes?' anymore. It's 'which databases, and how?'"*

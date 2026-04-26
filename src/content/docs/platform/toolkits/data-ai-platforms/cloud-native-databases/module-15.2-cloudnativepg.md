---
qa_pending: true
title: "Module 15.2: CloudNativePG - PostgreSQL Done Right on Kubernetes"
slug: platform/toolkits/data-ai-platforms/cloud-native-databases/module-15.2-cloudnativepg
sidebar:
  order: 3
---

## Complexity: [MEDIUM]

## Time to Complete: 50-60 minutes

## Track: Toolkits

## Prerequisites

Before starting this module, you should already be comfortable with Kubernetes workloads, persistent storage, and basic PostgreSQL operations. You do not need to be a PostgreSQL internals expert, but you should understand what a primary database does, why replicas exist, and why losing the write leader during an outage is different from losing a stateless application pod.

You should have completed or reviewed these topics before working through the lab:

- [Module 15.1: CockroachDB](../module-15.1-cockroachdb/) for distributed database tradeoffs and failure-domain thinking.
- PostgreSQL fundamentals, including SQL basics, Write-Ahead Logging, streaming replication, and connection limits.
- Kubernetes fundamentals, including StatefulSets, Services, PersistentVolumeClaims, Secrets, and custom resources.
- [Reliability Engineering Foundation](/platform/foundations/reliability-engineering/) for availability, recovery objectives, and incident thinking.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a CloudNativePG PostgreSQL cluster that separates write traffic, read traffic, storage, backup, and failover responsibilities clearly.
- **Debug** primary failure, replica lag, backup failure, and connection exhaustion scenarios by reading Kubernetes and CloudNativePG status signals.
- **Evaluate** when CloudNativePG is a better fit than a managed database service, another PostgreSQL operator, or a manually operated StatefulSet.
- **Implement** backup, WAL archiving, scheduled backup, and point-in-time recovery patterns using CloudNativePG custom resources.
- **Plan** Day-2 operations for scaling, rolling updates, planned switchovers, pooler placement, monitoring, and restore testing.

---

## Why This Module Matters

The database incident did not begin with a database crash. It began with a normal migration, a normal deployment window, and a team that had successfully shipped dozens of schema changes before. At 13:42, a developer started a PostgreSQL migration that had completed quickly in staging. In production, the table was larger, the write pattern was heavier, and the migration moved from a metadata change into a long-running update that saturated CPU and consumed every available connection.

By the time the incident channel filled with messages, the team had three choices and none of them were comfortable. They could manually repair inconsistent rows while the payment API remained unhealthy, restore from last night's backup and reconcile hours of transactions, or recover to a precise timestamp just before the damaging statement began. The third option existed only because the platform team had already configured continuous WAL archiving, practiced recovery, and understood how CloudNativePG represented a restored cluster as a normal Kubernetes object.

CloudNativePG matters because PostgreSQL is stateful infrastructure in a scheduler built around replacement. Kubernetes can reschedule a pod, attach a volume, and update a Service, but it does not automatically know which PostgreSQL instance is safe to promote, whether a standby has replayed enough WAL, or whether a backup is usable for point-in-time recovery. The operator fills that gap by watching declared intent, observing PostgreSQL state, and applying database-specific decisions through Kubernetes primitives.

This is not magic, and treating it as magic is dangerous. CloudNativePG can automate failover, backups, recovery, service routing, and rolling changes, but it cannot choose your recovery objective, validate your application retry behavior, or decide whether a cross-zone synchronous replica is worth the latency cost. The goal of this module is to move from "I can apply a YAML file" to "I can reason about how this database behaves when something breaks."

---

## Core Concept 1: What the Operator Owns

A plain StatefulSet can keep PostgreSQL pods alive, but it cannot operate PostgreSQL safely by itself. PostgreSQL high availability requires database-aware actions: choosing a primary, promoting a standby, fencing a failed instance, keeping replicas aligned, archiving WAL, restoring from base backups, and routing clients to the right role. CloudNativePG packages those decisions into a Kubernetes operator so the cluster can converge toward a declared state instead of depending on humans to run commands during an outage.

The important mental model is that CloudNativePG manages a PostgreSQL cluster, not just a set of pods. A `Cluster` custom resource describes how many instances you want, how storage should be allocated, how PostgreSQL should be configured, how backups should be written, and how the operator should expose traffic. The operator then creates and reconciles lower-level Kubernetes resources, but those resources are implementation details rather than the primary interface you operate.

```text
CLOUDNATIVEPG ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CloudNativePG Operator (Deployment)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Watches Cluster, Backup, ScheduledBackup, and Pooler CRs │  │
│  │  Reconciles PostgreSQL lifecycle and configuration        │  │
│  │  Handles failover, promotion, and instance rebuilds       │  │
│  │  Coordinates base backups and WAL archiving               │  │
│  │  Updates role-based Services for application routing      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            │ manages                            │
│                            ▼                                    │
│  PostgreSQL Cluster (Pods + PVCs)                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │   │   Pod 1     │  │   Pod 2     │  │   Pod 3     │      │  │
│  │   │  PRIMARY    │  │  REPLICA    │  │  REPLICA    │      │  │
│  │   │             │  │             │  │             │      │  │
│  │   │ PostgreSQL  │──│ PostgreSQL  │──│ PostgreSQL  │      │  │
│  │   │ WAL source  │  │ WAL replay  │  │ WAL replay  │      │  │
│  │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │  │
│  │          │                │                │             │  │
│  │   ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐      │  │
│  │   │    PVC      │  │    PVC      │  │    PVC      │      │  │
│  │   │  data dir   │  │  data dir   │  │  data dir   │      │  │
│  │   └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Role-Based Services                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  cluster-rw  ─────────▶ current primary for writes        │  │
│  │  cluster-ro  ─────────▶ replicas for read-only traffic    │  │
│  │  cluster-r   ─────────▶ any available instance for reads  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Backup Storage                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Object store: S3, GCS, Azure Blob, or compatible target  │  │
│  │  Base backups: consistent full recovery starting points   │  │
│  │  WAL archive: continuous replay stream for PITR           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The diagram shows the first practical distinction a senior operator makes: the application should not know pod names. Applications connect to Services whose endpoints follow database roles, because pod identities can change during failover, rebuild, or maintenance. If an application writes directly to `my-postgres-1`, it has coupled itself to a temporary implementation detail and will eventually break during the exact incident the operator was meant to handle.

CloudNativePG's design also reduces the number of separate high-availability components you need to reason about. Some PostgreSQL stacks rely on a combination of Patroni, distributed consensus, custom proxying, and external routing layers. Those designs can work well, but each extra component adds another failure mode and another operational interface. CloudNativePG leans heavily on Kubernetes primitives plus PostgreSQL-native mechanisms, which makes the system easier to inspect when the pressure is high.

> **Pause and predict:** If the primary pod disappears and your application connects through `my-postgres-rw`, what should change first: the application configuration, the Service endpoints, or the Deployment manifest? Write down your prediction before reading the failover section, because this distinction is the core reason role-based Services matter.

A useful analogy is an air traffic controller rather than a mechanic. PostgreSQL still does the database work, Kubernetes still schedules pods, and the storage layer still persists bytes. The operator coordinates those moving parts so that the right instance receives writes, replicas follow the right timeline, and recovery objects become real running clusters.

### Worked Example: Reading the Ownership Boundary

Suppose a team reports that writes are failing after a node drain, but the database pods appear healthy. A beginner might immediately exec into a pod and restart PostgreSQL. A better first move is to check whether the role-based Service still points to the current primary, because applications should reach the database through `-rw` rather than through a pod.

```bash
kubectl get cluster my-postgres
kubectl get pods -l cnpg.io/cluster=my-postgres -o wide
kubectl get service my-postgres-rw my-postgres-ro my-postgres-r
kubectl get endpoints my-postgres-rw
kubectl describe cluster my-postgres
```

The reasoning sequence matters more than the individual commands. First, ask whether the CloudNativePG `Cluster` reports a healthy state. Second, verify which pods exist and where they landed after the drain. Third, inspect the role-based Service, because a healthy primary is not useful if clients are routed incorrectly. Finally, read the cluster events and conditions to see whether the operator is still reconciling a switchover, rebuilding an instance, or waiting on storage.

---

## Core Concept 2: Deploying the First Cluster

The safest way to learn CloudNativePG is to begin with a small cluster that exposes the essential pattern without hiding behind production-specific details. You install the operator once per Kubernetes cluster, then create one or more PostgreSQL `Cluster` resources. The operator's namespace and your database namespace can be different, which is common in production because platform teams own the operator while application teams own database instances.

As of this module's rewrite, CloudNativePG 1.29 is the current minor release family. In production, always read the release notes before applying an operator upgrade, because operator upgrades can trigger instance-manager rolling updates and sometimes planned switchovers. For learning, using the current release manifest is enough to see the reconciliation model.

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.29/releases/cnpg-1.29.0.yaml

kubectl rollout status deployment/cnpg-controller-manager \
  -n cnpg-system \
  --timeout=180s

kubectl get pods -n cnpg-system
```

A minimal PostgreSQL cluster needs fewer fields than many examples show. Start with instance count, storage, and bootstrap settings, then add backup, tuning, affinity, monitoring, and poolers as you understand the operational need. This staged approach reduces cognitive load and helps you connect each field to a behavior you can observe.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: my-postgres
  namespace: default
spec:
  instances: 3

  storage:
    size: 20Gi

  bootstrap:
    initdb:
      database: app
      owner: app_user
      secret:
        name: app-user-secret

  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "768MB"
      checkpoint_completion_target: "0.9"

  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "2"
      memory: "4Gi"

  affinity:
    topologyKey: topology.kubernetes.io/zone
```

```bash
kubectl create secret generic app-user-secret \
  --from-literal=username=app_user \
  --from-literal=password='change-this-in-real-environments'

kubectl apply -f my-postgres.yaml

kubectl wait --for=condition=Ready cluster/my-postgres --timeout=300s

kubectl get cluster my-postgres
kubectl get pods -l cnpg.io/cluster=my-postgres -o wide
kubectl get service my-postgres-rw my-postgres-ro my-postgres-r
```

Do not mistake a successful apply for a production-ready database. The YAML above starts a highly available topology, but it does not yet define an object-store backup target, a restore drill, application connection pooling, alert thresholds, or an upgrade policy. In platform engineering terms, the `Cluster` resource is the beginning of the service contract, not the end of it.

The `instances: 3` field deserves careful attention. Three instances usually means one primary and two replicas, which gives the operator options during failover and maintenance. A single instance can be appropriate for disposable development, but it is not a highly available database. Two instances are better than one, but many teams prefer three because it gives more flexibility during upgrades, replica rebuilds, and zone-level failures.

| Design Choice | What It Gives You | What It Costs | When to Use It |
|---|---|---|---|
| Single instance | Lowest cost and simplest lab setup | No database failover when the instance is unavailable | Local experiments and disposable development |
| Three instances | Primary plus multiple failover candidates | More storage, CPU, and scheduling constraints | Default starting point for production workloads |
| Zone spread | Survives many node or zone failures | Potential cross-zone latency and storage constraints | Production clusters with multi-zone node pools |
| Explicit resource requests | Predictable scheduling and fewer surprise evictions | Requires capacity planning and right-sizing | Any cluster that carries real application traffic |
| Backup object store | Enables recovery beyond live replicas | Requires credentials, retention, and restore testing | Any environment where data matters |

The connection string is also part of the design. CloudNativePG creates Secrets for application credentials, and the generated URI points at the read-write Service. You can inspect the Secret to confirm what the application should use, but you should not paste the decoded value into tickets, chat messages, or documentation because it contains credentials.

```bash
kubectl get secret my-postgres-app -o jsonpath='{.data.uri}' | base64 -d
printf '\n'

kubectl get service my-postgres-rw -o wide
kubectl get service my-postgres-ro -o wide
```

A common beginner mistake is to treat the primary pod as the connection target because it feels concrete. That approach works only until the primary changes. The correct abstraction is the role Service, because CloudNativePG updates the Service endpoints when roles change and the application can keep the same hostname.

---

## Core Concept 3: Failover, Promotion, and Client Behavior

Failover is not a single event. It is a sequence of detection, decision, promotion, routing, and repair. CloudNativePG must decide that the current primary cannot safely continue, choose a suitable replica, promote it, update Services so clients find the new primary, and then reconcile the failed instance back into the cluster as a replica or replacement. Each step has a different observable signal, which is why incident responders should read conditions, events, Services, and PostgreSQL state together.

```text
AUTOMATED FAILOVER SEQUENCE
─────────────────────────────────────────────────────────────────

BEFORE: Normal operation
─────────────────────────────────────────────────────────────────
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Pod 1     │    │   Pod 2     │    │   Pod 3     │
│  PRIMARY    │───▶│  REPLICA    │───▶│  REPLICA    │
│  writes     │    │  replay     │    │  replay     │
└──────┬──────┘    └─────────────┘    └─────────────┘
       │
       │ my-postgres-rw Service points here
       ▼
  Applications

DURING: Primary fails
─────────────────────────────────────────────────────────────────
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Pod 1     │    │   Pod 2     │    │   Pod 3     │
│ UNAVAILABLE │ X  │  REPLICA    │    │  REPLICA    │
│             │    │ candidate   │    │ candidate   │
└─────────────┘    └─────────────┘    └─────────────┘

Operator observations:
• PostgreSQL health checks fail or the instance becomes unreachable
• Streaming replication from the primary stops
• Cluster conditions and events show failover progress
• The operator chooses a replica that can become the new primary

AFTER: Failover completes
─────────────────────────────────────────────────────────────────
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Pod 1     │    │   Pod 2     │    │   Pod 3     │
│ REBUILDING  │◀───│  PRIMARY    │───▶│  REPLICA    │
│ as replica  │    │ promoted    │    │ replay      │
└─────────────┘    └──────┬──────┘    └─────────────┘
                          │
                          │ my-postgres-rw Service updated
                          ▼
                     Applications

Expected application behavior:
• Existing database sessions may fail and need retry logic
• New write connections should resolve through the same Service name
• Read-only traffic can continue through replica Services when replicas are healthy
```

The operator can reduce failover time, but it cannot make existing TCP sessions immortal. Applications still need database retry logic, transaction retry behavior where appropriate, and connection pools that do not hold broken connections forever. This is where platform and application responsibilities meet: the platform exposes stable Services, while the application handles transient database errors as part of normal distributed-system behavior.

> **Stop and think:** Your application receives connection errors for a few seconds during a primary failure, then recovers without a new deployment. Is that a CloudNativePG failure, an application success, or both? The senior answer is that the platform provided stable routing, while the application still needed retry behavior for interrupted sessions.

Planned switchovers use the same conceptual pieces but happen under operator control rather than emergency detection. You might perform a switchover before node maintenance, during a controlled upgrade, or when you want to move the primary away from an overloaded zone. Planned operations are usually less risky because you can check replica health, alert silence windows, and application readiness before changing the write leader.

```bash
kubectl cnpg status my-postgres

kubectl cnpg promote my-postgres my-postgres-2

kubectl get cluster my-postgres
kubectl get endpoints my-postgres-rw
```

If the `cnpg` plugin is not installed, you can still operate through Kubernetes annotations and custom resources, but the plugin provides useful status and administrative commands. In teams that run CloudNativePG at scale, installing the plugin for platform engineers is usually worth it because it shortens the path from "something looks wrong" to a database-specific view of the cluster.

### Worked Example: Diagnosing a Failover Complaint

Imagine an application team says, "CloudNativePG failed over, but our service stayed down for two minutes." The beginner response is to argue about the operator's failover duration. The senior response is to split the incident into database failover time, Service endpoint update time, application retry behavior, and connection pool recovery time.

```bash
kubectl describe cluster my-postgres
kubectl get events --field-selector involvedObject.name=my-postgres --sort-by=.lastTimestamp
kubectl get endpoints my-postgres-rw -o yaml
kubectl logs deployment/api-server --since=10m
kubectl logs deployment/api-server --since=10m | grep -i "connection"
```

If the CloudNativePG events show a quick promotion but application logs show repeated attempts to connect to an old pod IP, the problem is likely outside the operator. The application may have cached DNS too aggressively, held stale connections in a pool, or used a hard-coded pod hostname. If the Service endpoint did not update or the cluster condition stayed unhealthy, the platform team should continue investigating CloudNativePG and Kubernetes events.

---

## Core Concept 4: Backups, WAL, and Point-in-Time Recovery

Replicas are not backups. A replica faithfully copies many kinds of damage, including accidental deletes, bad migrations, corrupted logical state, and application bugs. Backups give you an independent recovery path, and WAL archiving gives you a way to replay changes to a specific point in time rather than accepting the age of the last full backup as your data-loss boundary.

CloudNativePG commonly uses Barman-compatible object storage for base backups and WAL archives. A base backup gives recovery a consistent starting point, while archived WAL files let PostgreSQL replay changes forward until a chosen target. This is why point-in-time recovery is powerful: you can recover to just before a damaging statement, validate the restored cluster, and then decide how to move application traffic.

```text
BACKUP AND PITR MODEL
─────────────────────────────────────────────────────────────────

┌──────────────────────┐
│  Primary PostgreSQL  │
│  accepts writes      │
└──────────┬───────────┘
           │ produces WAL records for every data change
           ▼
┌──────────────────────┐
│  WAL Archive Stream  │
│  continuous upload   │
└──────────┬───────────┘
           │ stored with base backups
           ▼
┌──────────────────────────────────────────────┐
│  Object Storage                              │
│  ┌────────────────────────────────────────┐  │
│  │ Base backup at 02:00                   │  │
│  │ WAL files from 02:00 through now       │  │
│  │ Retention policy controls expiry       │  │
│  └────────────────────────────────────────┘  │
└──────────┬───────────────────────────────────┘
           │ recovery reads base backup and replays WAL
           ▼
┌──────────────────────┐
│  Restored Cluster    │
│  new Kubernetes CR   │
└──────────────────────┘
```

A backup configuration is not complete until you can answer four operational questions. Where is the object store, which credentials can write to it, how long do you retain recoverable data, and how often do you prove that restore actually works? Teams often spend time on the first three questions and skip the fourth, which means they discover backup drift during an incident.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: my-postgres
spec:
  instances: 3

  storage:
    size: 50Gi

  backup:
    barmanObjectStore:
      destinationPath: s3://my-backups/postgres/my-postgres/
      endpointURL: https://s3.us-east-1.amazonaws.com
      s3Credentials:
        accessKeyId:
          name: backup-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: gzip
        maxParallel: 2
      data:
        compression: gzip
    retentionPolicy: "30d"
```

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: my-postgres-daily
spec:
  schedule: "0 0 2 * * *"
  backupOwnerReference: self
  cluster:
    name: my-postgres
```

A manual backup is useful before a risky operation, but it should not be your only backup mechanism. Scheduled base backups plus continuous WAL archiving are what make recovery windows predictable. Manual backups are tactical checkpoints; automated backups are the reliability control.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: my-postgres-before-billing-migration
spec:
  cluster:
    name: my-postgres
```

```bash
kubectl apply -f backup-before-billing-migration.yaml

kubectl get backup my-postgres-before-billing-migration

kubectl describe backup my-postgres-before-billing-migration
```

> **Pause and predict:** A developer drops the wrong table at 10:15. Your last base backup finished at 02:00, and WAL archiving is healthy through 10:14. Which object does recovery start from, and why is the answer not "the latest replica"? Explain the sequence before you look at the recovery manifest.

Point-in-time recovery creates a new cluster from backup material. That new cluster should be treated as a separate environment until you validate data, permissions, extensions, and application compatibility. In many incidents, the safest pattern is to recover into a new cluster, verify it, and then change application routing intentionally rather than trying to mutate the damaged cluster in place.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: my-postgres-restored
spec:
  instances: 3

  storage:
    size: 50Gi

  bootstrap:
    recovery:
      source: my-postgres-backup-source
      recoveryTarget:
        targetTime: "2026-04-15 10:14:00.000000+00"

  externalClusters:
    - name: my-postgres-backup-source
      barmanObjectStore:
        destinationPath: s3://my-backups/postgres/my-postgres/
        endpointURL: https://s3.us-east-1.amazonaws.com
        s3Credentials:
          accessKeyId:
            name: backup-creds
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: backup-creds
            key: SECRET_ACCESS_KEY
        wal:
          compression: gzip
```

Recovery time depends on database size, object-store performance, network throughput, WAL volume, and Kubernetes scheduling. A small lab database may restore in minutes, while a large production database can take much longer. This is why restore drills are not bureaucracy: they convert an assumed recovery time objective into measured operational evidence.

---

## Core Concept 5: Day-2 Operations

Day-2 operations are the difference between a successful demo and a database platform. After the first cluster is running, you still need to scale replicas, resize storage, rotate credentials, patch the operator, upgrade PostgreSQL, test restores, watch replication lag, and keep application connection patterns healthy. CloudNativePG automates many of these actions, but automation is still a system you must observe and govern.

Scaling read replicas is a declarative patch to the `Cluster` resource. The operator creates or removes instances, coordinates PostgreSQL replication, and updates Services as roles remain valid. Scale-down deserves more caution than scale-up because removing replicas can reduce failover choices and temporarily concentrate read traffic.

```bash
kubectl patch cluster my-postgres --type merge -p '{"spec":{"instances":5}}'

kubectl get pods -l cnpg.io/cluster=my-postgres -w

kubectl patch cluster my-postgres --type merge -p '{"spec":{"instances":3}}'

kubectl get cluster my-postgres
```

Configuration changes are also declarative, but not all PostgreSQL settings behave the same way. Some settings reload without restart, some require instance restart, and some require a more careful operational plan because they change memory use, connection behavior, or write-ahead-log pressure. The operator can roll pods, but it cannot tell you whether `max_connections` is a good value for your workload.

```bash
kubectl patch cluster my-postgres --type merge -p '
{
  "spec": {
    "postgresql": {
      "parameters": {
        "max_connections": "300",
        "shared_buffers": "512MB"
      }
    }
  }
}'
```

Rolling updates happen at two different layers. Upgrading the CloudNativePG operator updates the controller and may trigger instance-manager updates inside PostgreSQL pods. Upgrading PostgreSQL itself is a database-version decision with compatibility, extension, application, and rollback implications. Treat operator patches and PostgreSQL major upgrades as separate changes unless you have a strong reason to combine them.

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.29/releases/cnpg-1.29.0.yaml

kubectl rollout status deployment/cnpg-controller-manager \
  -n cnpg-system \
  --timeout=180s

kubectl get cluster my-postgres
```

Connection pooling becomes important when applications create too many PostgreSQL sessions or when failover leaves stale client connections behind. CloudNativePG supports PgBouncer through a `Pooler` custom resource, which lets teams declare a pooler near the database while still preserving the distinction between read-write and read-only traffic. A pooler is not a substitute for fixing abusive application behavior, but it is often an important control for protecting PostgreSQL.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Pooler
metadata:
  name: my-postgres-rw-pooler
spec:
  cluster:
    name: my-postgres
  instances: 2
  type: rw
  pgbouncer:
    poolMode: transaction
    parameters:
      max_client_conn: "1000"
      default_pool_size: "50"
```

Monitoring should reflect user impact, PostgreSQL health, and operator progress rather than only pod uptime. A database pod can be Running while replication is lagging, WAL archiving is failing, or every connection slot is consumed. Good dashboards show the relationship between application errors, connection counts, slow queries, replication lag, backup recency, and cluster conditions.

```text
CLOUDNATIVEPG METRICS
─────────────────────────────────────────────────────────────────

Cluster Health:
├── cnpg_collector_up                         # Metrics collector availability
├── cnpg_pg_replication_lag                   # Replica lag measured from PostgreSQL
├── cnpg_pg_replication_streaming             # Streaming replication status

Database Activity:
├── cnpg_pg_database_size_bytes               # Database size for capacity planning
├── cnpg_pg_stat_activity_count               # Active and waiting sessions
├── cnpg_pg_stat_replication_*                # Per-replica replication signals

Performance:
├── cnpg_pg_stat_bgwriter_*                   # Checkpoint and background writer behavior
├── cnpg_pg_stat_database_*                   # Per-database transaction and block stats
├── cnpg_pg_locks_*                           # Lock pressure and blocked work

Backup and Recovery:
├── cnpg_pg_wal_archive_status                # WAL archiving success or failure
├── cnpg_collector_last_backup_timestamp      # Age of the latest observed backup
└── backup custom resources                   # Phase, target, and error details
```

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: my-postgres
spec:
  instances: 3
  monitoring:
    enablePodMonitor: true
```

The `enablePodMonitor` field is convenient in clusters that run the Prometheus Operator, but production monitoring should still be owned intentionally. Decide which namespace owns monitoring resources, how alerts route, who responds to backup failures, and which service-level indicators represent database user pain. A quiet dashboard is not the same as a reliable database if no alert fires when WAL archiving breaks.

> **Active check:** Before the hands-on exercise, choose one Day-2 operation from this section and write the exact failure you would expect if it went wrong. For example, "If WAL archiving fails, PITR can only replay to the last archived segment," or "If the app bypasses the `-rw` Service, failover may complete while writes still fail." This check forces you to connect a Kubernetes object to an operational consequence.

### Day-2 Runbook Pattern

A useful runbook separates detection, diagnosis, decision, and verification. Detection asks how you know something is wrong. Diagnosis asks which component owns the symptom. Decision asks whether you should wait for reconciliation, intervene, or roll back. Verification asks how you prove the system is healthy from both database and application perspectives.

| Operation | Detection Signal | Diagnosis Question | Verification Signal |
|---|---|---|---|
| Replica lag | Replication lag metric or stale read complaints | Is lag caused by write volume, network, storage, or a broken replica? | Lag returns to expected range and read traffic is current enough |
| Backup failure | Backup CR phase, WAL archive metric, or alert | Are credentials, object-store reachability, or retention settings broken? | New base backup completes and WAL archive resumes |
| Primary failure | Cluster condition, Service endpoint change, app errors | Did promotion finish, and are clients using the role Service? | Writes succeed through `cluster-rw` and replicas follow new primary |
| Connection exhaustion | Active sessions near limit and app connection errors | Is the problem application pooling, query duration, or too low a limit? | Session count stabilizes and app latency recovers |
| Rolling update | Pods cycling and cluster events | Is the operator progressing one instance at a time? | Cluster returns Ready and application error rate stays acceptable |

The runbook pattern keeps operational thinking concrete. Instead of saying "check CloudNativePG," you specify which object, metric, event, or log answers the next question. This is the difference between a platform that depends on one expert and a platform that a whole on-call rotation can operate.

---

## Core Concept 6: Choosing CloudNativePG Deliberately

CloudNativePG is a strong option when you want PostgreSQL to be part of a Kubernetes-native platform contract. It gives platform teams a declarative API, integrates naturally with GitOps, supports backup and recovery workflows, and uses Kubernetes Services for role-based routing. It is especially compelling when teams already run Kubernetes well and want database operations to fit the same review, reconciliation, and observability model as other platform services.

It is not automatically the right answer for every PostgreSQL workload. A managed database service may provide better cloud-provider integration, lower operational burden, mature compliance features, or specialized support for storage and backups. Another operator may fit better if your organization already has deep experience with its architecture. A self-managed PostgreSQL stack may be justified for unusual requirements, but it should be chosen with full awareness of the operational cost.

```text
POSTGRESQL OPERATOR COMPARISON
─────────────────────────────────────────────────────────────────

                    CloudNativePG  Zalando     CrunchyData   KubeDB
─────────────────────────────────────────────────────────────────
ARCHITECTURE
Primary/replica     yes            yes         yes           yes
Streaming repl.     yes            yes         yes           yes
External etcd       no             yes         no            no
External proxy      optional       common      optional      common
CNCF project        Sandbox        no          no            no

FEATURES
Auto failover       strong         strong      strong        strong
PITR                strong         supported   strong        supported
Backup to object    native         supported   strong        supported
Connection pooling  Pooler CR      supported   supported    supported
Logical replication supported      supported   supported    limited

OPERATIONS
Rolling updates     supported      supported   supported    supported
Clone from backup   supported      supported   supported    supported
Declarative config  strong         strong      strong        strong
Observability       Prometheus     Prometheus  Prometheus    Prometheus

BEST FIT
CloudNativePG: Kubernetes-native PostgreSQL with fewer external HA components
Zalando: Teams that already operate Patroni-centered PostgreSQL successfully
CrunchyData: Enterprise PostgreSQL programs that value vendor tooling depth
KubeDB: Organizations standardizing several database engines through one API
```

Use comparison tables as decision support, not as a scoreboard. The best operator is the one your team can patch, observe, restore, and explain during an incident. A feature you do not test is not a capability; it is an assumption waiting for production to challenge it.

| Option | Strong Fit | Weak Fit | Senior Evaluation Question |
|---|---|---|---|
| CloudNativePG | Kubernetes-native platform teams that want declarative PostgreSQL operations | Teams without Kubernetes storage, networking, or operator experience | Can we operate Kubernetes well enough that putting PostgreSQL there reduces total risk? |
| Managed PostgreSQL | Teams that want lower infrastructure burden and cloud-native integrations | Workloads needing tight in-cluster control or unusual topology | Are we paying for reduced operational responsibility, and does the provider meet our recovery needs? |
| Another operator | Teams with existing experience, support contracts, or required features | Teams adopting it only because a comparison table shows more checkmarks | Can our on-call team explain its failover and recovery model clearly? |
| Manual StatefulSet | Disposable labs or highly specialized expert-owned systems | Most production application databases | What database-specific operations are we accepting as manual incident work? |

The final decision should include failure testing. Install the candidate, kill the primary, corrupt a test table, fill a volume in a controlled environment, simulate object-store credential failure, and run an application through a failover. The product that looks best in architecture review may feel very different during hands-on incident rehearsal.

---

## War Story: The Migration That Made Recovery Real

The team had backup dashboards, green status checks, and a calendar entry for quarterly restore testing. What they did not have was recent muscle memory. Their production PostgreSQL cluster ran on CloudNativePG, the backup configuration had been copied from a reference environment, and everyone assumed point-in-time recovery would work because no alert said otherwise.

At 13:42, a billing migration started with a harmless-looking schema change. The first statement added a nullable column and completed quickly. The next statement updated historical rows using a classification function that had been tested on a small staging dataset. In production, it scanned tens of millions of rows, consumed CPU, held locks longer than expected, and caused application requests to queue behind database work.

At 13:44, customer-facing requests started timing out. At 13:45, an engineer canceled the migration. Canceling stopped the active statement, but it did not restore the system to a clean business state. Some rows had been changed, some had not, and downstream code assumed a consistency boundary that no longer existed.

The incident commander forced the discussion into recovery options instead of blame. Manual repair would preserve every transaction but keep the system impaired for days. Restoring from the previous nightly backup would be technically simple but would lose too much legitimate business data. Recovering to 13:41 would lose only the narrow window before the migration began, but only if WAL archiving was current and the team could create a restored cluster quickly.

```bash
kubectl cnpg status prod-postgres

kubectl get backup -n payments

kubectl describe cluster prod-postgres -n payments

kubectl get events -n payments --sort-by=.lastTimestamp
```

The first useful signal was not the base backup age; it was WAL archive health. The latest archived WAL segment gave the team confidence that recovery could replay close to the target time. The second useful signal was that CloudNativePG recovery would create a separate cluster, which meant the team could validate the restored state before switching application traffic.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: prod-postgres-recovered
  namespace: payments
spec:
  instances: 3

  storage:
    size: 500Gi
    storageClass: premium-ssd

  bootstrap:
    recovery:
      source: prod-postgres-source
      recoveryTarget:
        targetTime: "2026-04-15 13:41:00.000000+00"

  externalClusters:
    - name: prod-postgres-source
      barmanObjectStore:
        destinationPath: s3://company-backups/postgres/prod-postgres/
        s3Credentials:
          accessKeyId:
            name: backup-creds
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: backup-creds
            key: SECRET_ACCESS_KEY
        wal:
          compression: gzip
```

```bash
kubectl apply -f recovery.yaml

kubectl wait --for=condition=Ready cluster/prod-postgres-recovered \
  -n payments \
  --timeout=1800s

kubectl exec -n payments prod-postgres-recovered-1 -- psql -U app_user -d app -c \
  "SELECT COUNT(*) FROM transactions WHERE category IS NOT NULL;"
```

The restored cluster showed zero migrated rows, which matched the target time before the damaging update. The team then ran application smoke checks against the recovered read-write Service, compared transaction counts against external payment records, and switched the API to the recovered cluster through a controlled Deployment patch. The outage was not free, but it was measured in minutes of recovery work rather than days of manual data repair.

```text
INCIDENT TIMELINE
─────────────────────────────────────────────────────────────────

13:41 │ Normal operations
      │ WAL files are archived continuously to object storage
      │
13:42 │ Migration starts with a fast metadata change
      │ ███░░░░░░░░░░░░░░░░░░░░░░░░░░ quick statement
      │
13:43 │ Large UPDATE begins against production-scale data
      │ █████████████████████████████ long-running table work
      │
13:44 │ CPU and connections saturate
      │ █████████████████████████████ customer impact begins
      │
13:45 │ Migration is canceled
      │ █████████████████████████████ data is left inconsistent
      │
13:48 │ PITR decision is made after checking WAL health
      │ ░░░░░░░░░░░░░░░░░░░░░░░░░░ recovery cluster starts
      │
14:00 │ Recovered cluster passes validation checks
      │ ░░░░░░░░░░░░░░░░░░░░░░░░░░ application cutover begins
      │
14:03 │ API points at recovered read-write Service
      │ ░░░░░░░░░░░░░░░░░░░░░░░░░░ incident moves to monitoring

Operational lesson:
The recovery feature mattered because it had already been configured, observed, and practiced.
```

| Recovery Option | Data Loss | Business Impact | Operational Risk |
|---|---|---|---|
| Manual repair in place | None in theory | Multiple days of impaired billing behavior | High because the damaged state remains live |
| Restore from nightly backup | Many hours | Large reconciliation workload with external systems | Medium because procedure is familiar but data loss is broad |
| PITR to pre-migration timestamp | Narrow incident window | Small reconciliation window and faster service recovery | Lower when WAL archive health and restore drills are proven |

The post-incident changes were concrete. Large data migrations moved to reviewed background jobs with batching and pauses. Staging gained production-scale anonymized data for migration testing. Restore drills moved from quarterly calendar reminders to measured platform objectives. Most importantly, the team stopped calling backups "configured" until someone had restored from them and connected an application to the restored cluster.

---

## Did You Know?

- **CloudNativePG entered the CNCF Sandbox as a Kubernetes-native PostgreSQL operator.** That matters because project maturity and governance are part of platform risk, especially when a tool becomes a shared service used by many teams.

- **Point-in-time recovery depends on both base backups and archived WAL.** A base backup without a healthy WAL stream gives you a coarse recovery point, while WAL replay lets you target a precise timestamp within the retention window.

- **The read-write Service is part of the failover contract.** Applications that connect through the `-rw` Service can survive primary replacement more cleanly than applications that connect directly to pod names.

- **A successful backup is not the same as a successful restore.** Backup jobs prove that data was written somewhere, while restore drills prove that the team can use that data to recover a working database under realistic constraints.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Connecting applications directly to a PostgreSQL pod | Failover can complete while applications still target an old or rebuilt instance | Use the generated `-rw`, `-ro`, or `-r` Services according to traffic role |
| Running production with no object-store backup target | Replicas will copy logical mistakes and cannot recover from accidental destructive changes | Configure base backups, WAL archiving, retention, and restore drills before production launch |
| Treating a single instance as highly available | Kubernetes may restart the pod, but there is no standby to promote during instance loss | Use multiple instances and test failover behavior with the real application |
| Ignoring application retry and pooling behavior | Existing sessions can break during failover even when Service routing updates correctly | Implement retry logic, set pool timeouts, and test failover under application load |
| Scaling down replicas without checking read traffic | Removing replicas can overload remaining instances or reduce failover choices | Review read routing, replica lag, and failure-domain coverage before scaling down |
| Combining operator upgrades with PostgreSQL major upgrades casually | Two change types can produce confusing symptoms and harder rollback decisions | Separate platform upgrades from database-version upgrades unless a plan explicitly couples them |
| Monitoring only pod readiness | A Running pod can still have broken WAL archiving, high lag, locks, or exhausted connections | Alert on database metrics, backup freshness, cluster conditions, and user-facing errors |
| Never practicing recovery | The first restore attempt happens during the incident, when time pressure is highest | Schedule restore drills and record measured recovery time and validation steps |

---

## Quiz

### Question 1

Your team deploys a three-instance CloudNativePG cluster, and the application connects to `my-postgres-1.default.svc.cluster.local` because that pod was the primary during launch. A node failure later promotes `my-postgres-2`, but writes still fail from the application. What should you change, and why?

<details>
<summary>Show Answer</summary>

The application should connect through the CloudNativePG read-write Service, usually `my-postgres-rw`, instead of a pod-specific hostname. The operator can promote a new primary and update the Service endpoint, but it cannot fix an application that bypasses the Service contract. After changing the connection target, you should also verify application DNS caching and connection pool retry behavior because existing sessions may still fail during the transition.
</details>

### Question 2

A developer accidentally runs `DELETE FROM invoices` at 10:15. Your latest base backup completed at 02:00, WAL archiving is healthy through 10:14, and all replicas have already replayed the delete. Which recovery path should you recommend?

<details>
<summary>Show Answer</summary>

Recommend point-in-time recovery into a new CloudNativePG cluster targeting a timestamp before 10:15, such as 10:14 if that matches the business boundary. Replicas are not useful because they copied the delete. The base backup provides the starting point, and archived WAL replays the database forward to the chosen target. The restored cluster should be validated before application traffic is switched.
</details>

### Question 3

During a failover test, CloudNativePG promotes a replica quickly, but the application reports errors for almost a minute. Cluster events show the read-write Service endpoint changed promptly. What should you investigate next?

<details>
<summary>Show Answer</summary>

Investigate application-side connection handling, DNS behavior, and connection pool settings. A prompt Service update means the platform routing contract likely worked, but existing database sessions can still break during failover. Look for stale connections, long DNS cache lifetimes, missing retry logic, pool health-check intervals, and application code that pins a resolved pod IP.
</details>

### Question 4

A platform team wants to raise `max_connections` from 200 to 1000 because the application frequently exhausts connections. What should you evaluate before accepting that change?

<details>
<summary>Show Answer</summary>

Evaluate whether the application is creating too many sessions, whether PgBouncer or another pooler should absorb client connection spikes, and whether PostgreSQL has enough memory for the higher connection count. Increasing `max_connections` can hide poor pooling and increase database memory pressure. A better design may combine application pool tuning, a CloudNativePG `Pooler`, query-duration fixes, and a more modest PostgreSQL setting.
</details>

### Question 5

Your backup job reports `completed`, but a quarterly restore drill fails because the restored cluster cannot replay WAL after the base backup. What does this reveal about your reliability control?

<details>
<summary>Show Answer</summary>

It reveals that backup completion was not a sufficient control by itself. The team also needed to monitor WAL archiving, retention, object-store permissions, and restore validity. A reliable backup program includes base backup success, continuous WAL archive health, restore drills, and documented validation steps for the recovered database.
</details>

### Question 6

A team asks whether CloudNativePG is always better than a managed PostgreSQL service because it is Kubernetes-native. How would you evaluate that claim for a regulated production workload?

<details>
<summary>Show Answer</summary>

Compare operational responsibility, compliance requirements, recovery objectives, support model, storage reliability, upgrade process, network controls, and team expertise. CloudNativePG can be excellent when the organization operates Kubernetes well and wants declarative in-cluster PostgreSQL. A managed service may be better if the provider offers stronger compliance evidence, automated maintenance, mature backups, or lower operational burden for the same workload.
</details>

### Question 7

You plan to drain a Kubernetes node that currently hosts the PostgreSQL primary. The application is latency-sensitive, and the maintenance window is approved. What CloudNativePG operation should you consider before the drain?

<details>
<summary>Show Answer</summary>

Consider a planned switchover or promotion to move the primary to a healthy replica before draining the node. A planned operation lets you check replica health, control timing, watch application behavior, and avoid mixing node maintenance with emergency-style failover. After the switchover, verify the `-rw` Service endpoint and application write behavior before proceeding with the drain.
</details>

### Question 8

A read-heavy application uses `my-postgres-ro` for reporting queries. After a large import, reports show stale data and users complain that recent records are missing. The write path is healthy. What should you check and how might you respond?

<details>
<summary>Show Answer</summary>

Check replica lag, streaming replication status, query load on replicas, storage latency, and whether the import generated more WAL than replicas could replay quickly. The read-only Service can load balance across replicas, but it does not guarantee that every replica is perfectly current at all times. Responses might include temporarily routing freshness-sensitive reads to `-rw`, reducing report load, scaling replicas carefully, tuning storage, or setting application-level freshness expectations.
</details>

---

## Hands-On Exercise

### Task: Deploy PostgreSQL, Test Failover, and Prove Recovery Plumbing

In this exercise, you will deploy CloudNativePG, create a three-instance PostgreSQL cluster, insert data, delete the primary pod, verify automatic failover, configure an in-cluster S3-compatible MinIO target, and trigger a backup. The lab is designed for a disposable Kubernetes environment such as kind, minikube, or a non-production namespace. Do not run these commands against a production cluster.

Before starting, create a clean namespace and define the `k` alias. The alias is used after this point to keep commands shorter; it is simply `kubectl`.

```bash
alias k=kubectl

k create namespace cnpg-lab

k config set-context --current --namespace=cnpg-lab
```

### Step 1: Install the Operator

Install the CloudNativePG operator into its default system namespace and wait for the controller to become available. In production, you would pin the version through your normal release process and read the release notes before upgrading.

```bash
k apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.29/releases/cnpg-1.29.0.yaml

k rollout status deployment/cnpg-controller-manager \
  -n cnpg-system \
  --timeout=180s

k get pods -n cnpg-system
```

Success criteria for this step:

- [ ] The `cnpg-system` namespace exists.
- [ ] The `cnpg-controller-manager` Deployment is available.
- [ ] No CloudNativePG controller pod is stuck in `CrashLoopBackOff` or `ImagePullBackOff`.

### Step 2: Deploy MinIO for Lab Backups

A real production cluster usually writes backups to cloud object storage. For a local lab, MinIO gives you an S3-compatible target inside Kubernetes so you can exercise the CloudNativePG backup path without needing cloud credentials.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: minio
---
apiVersion: v1
kind: Secret
metadata:
  name: minio-root
  namespace: minio
type: Opaque
stringData:
  rootUser: minioadmin
  rootPassword: minioadmin123
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: quay.io/minio/minio:RELEASE.2026-03-28T09-41-46Z
          args:
            - server
            - /data
          env:
            - name: MINIO_ROOT_USER
              valueFrom:
                secretKeyRef:
                  name: minio-root
                  key: rootUser
            - name: MINIO_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: minio-root
                  key: rootPassword
          ports:
            - name: api
              containerPort: 9000
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: minio
spec:
  selector:
    app: minio
  ports:
    - name: api
      port: 9000
      targetPort: api
```

```bash
cat > minio-lab.yaml <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: minio
---
apiVersion: v1
kind: Secret
metadata:
  name: minio-root
  namespace: minio
type: Opaque
stringData:
  rootUser: minioadmin
  rootPassword: minioadmin123
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: quay.io/minio/minio:RELEASE.2026-03-28T09-41-46Z
          args:
            - server
            - /data
          env:
            - name: MINIO_ROOT_USER
              valueFrom:
                secretKeyRef:
                  name: minio-root
                  key: rootUser
            - name: MINIO_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: minio-root
                  key: rootPassword
          ports:
            - name: api
              containerPort: 9000
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: minio
spec:
  selector:
    app: minio
  ports:
    - name: api
      port: 9000
      targetPort: api
EOF

k apply -f minio-lab.yaml

k rollout status deployment/minio \
  -n minio \
  --timeout=120s
```

Create a bucket using a temporary MinIO client pod. The bucket name must match the `destinationPath` you will configure on the PostgreSQL cluster.

```bash
k run minio-client \
  -n minio \
  --image=quay.io/minio/mc:RELEASE.2026-03-26T17-29-24Z \
  --restart=Never \
  --command -- sh -c '
    mc alias set local http://minio:9000 minioadmin minioadmin123 &&
    mc mb --ignore-existing local/cnpg-backups &&
    mc ls local
  '

k wait --for=condition=Ready pod/minio-client \
  -n minio \
  --timeout=60s || true

k logs pod/minio-client -n minio

k delete pod minio-client -n minio --ignore-not-found=true
```

Success criteria for this step:

- [ ] The `minio` Deployment is available.
- [ ] The `cnpg-backups` bucket exists.
- [ ] You understand that this MinIO setup is disposable lab infrastructure, not durable production backup storage.

### Step 3: Create the PostgreSQL Cluster

Create the application user Secret, backup credential Secret, and CloudNativePG `Cluster`. This manifest uses three instances so failover has a real standby to promote. It also configures WAL archiving to the MinIO bucket so the backup path is exercised during the lab.

```bash
k create secret generic app-user-secret \
  --from-literal=username=app_user \
  --from-literal=password='lab-password-change-me'

k create secret generic backup-creds \
  --from-literal=ACCESS_KEY_ID=minioadmin \
  --from-literal=SECRET_ACCESS_KEY=minioadmin123

cat > postgres-lab.yaml <<'EOF'
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: lab-postgres
spec:
  instances: 3

  storage:
    size: 5Gi

  bootstrap:
    initdb:
      database: app
      owner: app_user
      secret:
        name: app-user-secret

  postgresql:
    parameters:
      max_connections: "100"

  backup:
    barmanObjectStore:
      destinationPath: s3://cnpg-backups/lab-postgres/
      endpointURL: http://minio.minio.svc.cluster.local:9000
      s3Credentials:
        accessKeyId:
          name: backup-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: gzip
        maxParallel: 2
      data:
        compression: gzip
    retentionPolicy: "7d"
EOF

k apply -f postgres-lab.yaml

k wait --for=condition=Ready cluster/lab-postgres --timeout=300s

k get cluster lab-postgres
k get pods -l cnpg.io/cluster=lab-postgres -o wide
k get service lab-postgres-rw lab-postgres-ro lab-postgres-r
```

Success criteria for this step:

- [ ] The `lab-postgres` cluster reaches the Ready condition.
- [ ] Three PostgreSQL pods exist.
- [ ] The `lab-postgres-rw`, `lab-postgres-ro`, and `lab-postgres-r` Services exist.

### Step 4: Insert Data Through the Current Primary

Identify the primary through the read-write Service endpoint. This avoids assuming that pod ordinal `1` is always the primary. Then insert a table and sample data.

```bash
PRIMARY_POD=$(k get endpoints lab-postgres-rw \
  -o jsonpath='{.subsets[0].addresses[0].targetRef.name}')

echo "Current primary: ${PRIMARY_POD}"

k exec -i "${PRIMARY_POD}" -- psql -U app_user -d app <<'SQL'
CREATE TABLE IF NOT EXISTS important_data (
  id SERIAL PRIMARY KEY,
  value TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO important_data (value)
SELECT 'Record ' || generate_series(1, 1000);

SELECT COUNT(*) AS record_count FROM important_data;
SQL
```

Success criteria for this step:

- [ ] The primary pod name comes from the `lab-postgres-rw` endpoint.
- [ ] The `important_data` table exists.
- [ ] The row count query returns `1000` or more if you repeated the insert.

### Step 5: Simulate Primary Failure

Delete the current primary pod and watch CloudNativePG promote a replacement. This tests operator behavior, Service routing, and PostgreSQL replication under a controlled failure.

```bash
OLD_PRIMARY="${PRIMARY_POD}"

echo "Deleting primary pod: ${OLD_PRIMARY}"

k delete pod "${OLD_PRIMARY}"

sleep 10

k get pods -l cnpg.io/cluster=lab-postgres -o wide

NEW_PRIMARY=$(k get endpoints lab-postgres-rw \
  -o jsonpath='{.subsets[0].addresses[0].targetRef.name}')

echo "Old primary: ${OLD_PRIMARY}"
echo "New primary: ${NEW_PRIMARY}"
```

Now verify that the data is still available through the new primary. A real application might see a short interruption, but it should reconnect through the same Service name once the endpoint changes.

```bash
k exec -i "${NEW_PRIMARY}" -- psql -U app_user -d app <<'SQL'
SELECT COUNT(*) AS record_count FROM important_data;
INSERT INTO important_data (value) VALUES ('after failover');
SELECT COUNT(*) AS record_count_after_failover FROM important_data;
SQL

k describe cluster lab-postgres | sed -n '/Status:/,$p'
```

Success criteria for this step:

- [ ] The read-write endpoint changes to a live pod after deleting the primary.
- [ ] The table still contains the previously inserted rows.
- [ ] A new write succeeds after failover.
- [ ] The cluster returns to a healthy state after reconciliation.

### Step 6: Trigger and Inspect a Backup

Create an on-demand `Backup` resource and confirm that CloudNativePG marks it complete. This is not a full restore drill yet, but it proves that the cluster can write backup material to the configured object store.

```bash
cat > backup-lab.yaml <<'EOF'
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: lab-postgres-manual-backup
spec:
  cluster:
    name: lab-postgres
EOF

k apply -f backup-lab.yaml

k get backup lab-postgres-manual-backup -w
```

Stop the watch after the backup reaches a completed phase, then inspect the object-store bucket.

```bash
k describe backup lab-postgres-manual-backup

k run minio-client \
  -n minio \
  --image=quay.io/minio/mc:RELEASE.2026-03-26T17-29-24Z \
  --restart=Never \
  --command -- sh -c '
    mc alias set local http://minio:9000 minioadmin minioadmin123 &&
    mc ls --recursive local/cnpg-backups
  '

k wait --for=condition=Ready pod/minio-client \
  -n minio \
  --timeout=60s || true

k logs pod/minio-client -n minio

k delete pod minio-client -n minio --ignore-not-found=true
```

Success criteria for this step:

- [ ] The `Backup` resource reaches a completed phase.
- [ ] MinIO contains objects under the `cnpg-backups` bucket.
- [ ] You can explain why this proves backup write path health, but not full restore readiness.

### Step 7: Explain the Recovery Plan

Do not skip the reasoning step. Before cleanup, write a short recovery plan in your own notes using the specific names from this lab. Your plan should explain which base backup and WAL archive a restored cluster would use, which new cluster name you would choose, and how you would validate the recovered data before changing application traffic.

Success criteria for this step:

- [ ] Your plan restores into a new cluster rather than mutating `lab-postgres` in place.
- [ ] Your plan includes data validation queries, not only Kubernetes readiness checks.
- [ ] Your plan explains how application traffic would move only after validation.

### Step 8: Clean Up

Delete the lab resources when you are done. This removes the disposable database and MinIO environment from your cluster.

```bash
k delete backup lab-postgres-manual-backup --ignore-not-found=true
k delete cluster lab-postgres --ignore-not-found=true
k delete secret app-user-secret backup-creds --ignore-not-found=true
k delete namespace cnpg-lab --ignore-not-found=true
k delete namespace minio --ignore-not-found=true
```

Final success criteria:

- [ ] You deployed the CloudNativePG operator.
- [ ] You created a three-instance PostgreSQL cluster.
- [ ] You inserted data and verified it through PostgreSQL.
- [ ] You deleted the primary pod and observed automatic failover.
- [ ] You verified that data survived and writes continued through the new primary.
- [ ] You configured an S3-compatible backup target and completed an on-demand backup.
- [ ] You can explain why backup completion is not enough without a restore drill.

---

## Next Module

[Module 15.3: Neon & PlanetScale](../module-15.3-serverless-databases/) covers serverless database platforms, branching workflows, autoscaling tradeoffs, and the operational boundary between application teams and managed data services.

---

## Further Reading

- [CloudNativePG GitHub](https://github.com/cloudnative-pg/cloudnative-pg)
- [PostgreSQL Streaming Replication](https://www.postgresql.org/docs/current/warm-standby.html)
- [Data on Kubernetes Community](https://dok.community/)

---

*"The database operator is useful only when the team can explain what it will do during failure, prove that recovery works, and keep applications connected through the abstractions the operator maintains."*

## Sources

- [cncf.io: cloudnativepg](https://www.cncf.io/projects/cloudnativepg/) — The CNCF project page directly states CloudNativePG's Sandbox maturity level and acceptance date.
- [github.com: cloudnative pg](https://github.com/cloudnative-pg/cloudnative-pg) — The upstream README directly describes the no-external-HA design and these operator-managed lifecycle actions.
- [github.com: architecture.md](https://github.com/cloudnative-pg/cloudnative-pg/blob/main/docs/src/architecture.md) — The architecture documentation explicitly lists the service types and says the `-rw` service is updated on failover.
- [github.com: connection pooling.md](https://github.com/cloudnative-pg/cloudnative-pg/blob/main/docs/src/connection_pooling.md) — The connection-pooling documentation directly states native PgBouncer support via the `Pooler` custom resource.
- [github.com: backup.md](https://github.com/cloudnative-pg/cloudnative-pg/blob/main/docs/src/backup.md) — The backup documentation directly covers Barman/object-store backups, WAL archiving, and PITR.
- [github.com: monitoring.md](https://github.com/cloudnative-pg/cloudnative-pg/blob/main/docs/src/monitoring.md) — The monitoring documentation directly covers PodMonitor-based monitoring and the deprecation status of `.spec.monitoring.enablePodMonitor`.
- [CloudNativePG Service management](https://github.com/cloudnative-pg/cloudnative-pg/blob/main/docs/src/service_management.md) — Explains the `rw`, `ro`, and `r` service model that applications should use to survive failovers cleanly.

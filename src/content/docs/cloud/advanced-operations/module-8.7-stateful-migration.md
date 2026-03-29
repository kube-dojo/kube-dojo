---
title: "Module 8.7: Stateful Workload Migration & Data Gravity"
slug: cloud/advanced-operations/module-8.7-stateful-migration
sidebar:
  order: 8
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 2.5 hours
>
> **Prerequisites**: [Module 8.5: Disaster Recovery](module-8.5-disaster-recovery/), experience with PersistentVolumes and at least one database
>
> **Track**: Advanced Cloud Operations

---

## Why This Module Matters

**September 2022. A media streaming company. 18 months into a cloud migration.**

The engineering team had successfully migrated 90% of their stateless microservices from on-premises VMs to EKS. The remaining 10% was the hard part: a 12TB PostgreSQL database, a 3TB Elasticsearch cluster, a Redis cluster with 200GB of hot data, and a legacy media processing service with 50TB of files on local NFS. Every migration attempt was estimated at "two weeks of downtime," which the business rejected. The database was too large for a simple dump-and-restore within the maintenance window. The media files were too numerous for a single bulk copy. And every day they waited, the data grew larger.

After six months of delay, the team discovered the concept of "data gravity" -- the idea that large datasets attract applications and services to them, making migration progressively harder over time. Their 12TB database had grown to 16TB. Their 50TB media store had reached 68TB. The maintenance window they needed had grown from two weeks to three.

They eventually migrated using a combination of Change Data Capture for the database, incremental rsync for the media files, and the Strangler Fig pattern to gradually route traffic from old to new. The full migration took four months of parallel operation. This module teaches you those techniques: how to move stateful workloads without downtime, how to handle data gravity, and the specific Kubernetes tools and patterns that make database migration tractable.

---

## Understanding Data Gravity

Data gravity is a concept coined by Dave McCrory in 2010. The core insight: data has mass. As data accumulates in one location, it becomes harder and more expensive to move. Applications, services, and users are pulled toward the data, like objects toward a gravitational body.

```
DATA GRAVITY MODEL
════════════════════════════════════════════════════════════════

  Small dataset (1TB):          Large dataset (50TB):
  Easy to move                  Extremely hard to move

  ┌─────────┐                   ┌─────────────────────────┐
  │         │                   │                         │
  │  1TB DB │  ← Apps orbit     │        50TB DB          │
  │         │    loosely        │                         │
  └─────────┘                   │    Apps stuck in orbit  │
                                │    (high escape velocity)│
  Migration: hours              │                         │
  Downtime: minutes             └─────────────────────────┘
  Risk: low
                                Migration: weeks
                                Downtime: days (or zero with CDC)
                                Risk: high

  Data gravity formula (informal):
  Migration difficulty = Data size x Access frequency x Integration count

  A 1TB database accessed by 2 services: easy
  A 1TB database accessed by 50 services: hard (not because of size,
    but because of integration count)
```

### Migration Velocity

| Data Size | Migration Method | Expected Duration | Downtime |
|---|---|---|---|
| < 1 TB | pg_dump / mysqldump | 1-4 hours | 1-4 hours |
| 1-10 TB | Logical replication + cutover | 1-3 days | Minutes |
| 10-100 TB | CDC (Debezium/DMS) + catchup | 1-4 weeks | Minutes |
| 100+ TB | Physical replication + CDC | 1-3 months | Minutes |
| Files (any size) | Incremental sync (rsync/rclone) | Days-weeks | Minutes |

---

## The Strangler Fig Pattern

Named after the strangler fig tree that grows around a host tree until it replaces it entirely, this pattern lets you migrate services incrementally by routing traffic to the new system one piece at a time.

```
STRANGLER FIG MIGRATION
════════════════════════════════════════════════════════════════

Phase 1: Proxy all traffic through a router
  ┌──────────┐     ┌──────────┐     ┌──────────────────┐
  │  Users   │────▶│  Router  │────▶│  Legacy System   │
  │          │     │ (Ingress)│     │  (VM / on-prem)  │
  └──────────┘     └──────────┘     └──────────────────┘

Phase 2: New system handles some routes
  ┌──────────┐     ┌──────────┐     ┌──────────────────┐
  │  Users   │────▶│  Router  │──┬─▶│  Legacy System   │
  │          │     │          │  │  │  /api/users       │
  └──────────┘     └──────────┘  │  │  /api/payments    │
                                  │  └──────────────────┘
                                  │  ┌──────────────────┐
                                  └─▶│  New K8s Service  │
                                     │  /api/search      │
                                     │  /api/catalog     │
                                     └──────────────────┘

Phase 3: Most routes migrated
  ┌──────────┐     ┌──────────┐     ┌──────────────────┐
  │  Users   │────▶│  Router  │──┬─▶│  Legacy System   │
  │          │     │          │  │  │  /api/payments    │
  └──────────┘     └──────────┘  │  └──────────────────┘
                                  │  ┌──────────────────┐
                                  └─▶│  New K8s Services │
                                     │  /api/search      │
                                     │  /api/catalog     │
                                     │  /api/users       │
                                     │  /api/orders      │
                                     └──────────────────┘

Phase 4: Legacy system decommissioned
  ┌──────────┐     ┌──────────┐     ┌──────────────────┐
  │  Users   │────▶│  Router  │────▶│  New K8s Services │
  │          │     │ (Ingress)│     │  (all routes)     │
  └──────────┘     └──────────┘     └──────────────────┘
```

### Implementing Strangler Fig with Kubernetes Ingress

```yaml
# Phase 2: Route some paths to new service, rest to legacy
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: strangler-fig-router
  namespace: migration
  annotations:
    nginx.ingress.kubernetes.io/upstream-vhost: "legacy.internal.company.com"
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          # New services (migrated to K8s)
          - path: /api/search
            pathType: Prefix
            backend:
              service:
                name: search-service
                port:
                  number: 8080
          - path: /api/catalog
            pathType: Prefix
            backend:
              service:
                name: catalog-service
                port:
                  number: 8080
          # Everything else goes to the legacy system
          - path: /
            pathType: Prefix
            backend:
              service:
                name: legacy-proxy
                port:
                  number: 80
---
# ExternalName service pointing to legacy system
apiVersion: v1
kind: Service
metadata:
  name: legacy-proxy
  namespace: migration
spec:
  type: ExternalName
  externalName: legacy.internal.company.com
```

### Canary Routing During Migration

```yaml
# Use traffic splitting to gradually shift traffic
# (Istio VirtualService example)
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: user-service-migration
  namespace: migration
spec:
  hosts:
    - api.example.com
  http:
    - match:
        - uri:
            prefix: /api/users
      route:
        - destination:
            host: legacy-user-service
            port:
              number: 80
          weight: 80    # 80% to legacy
        - destination:
            host: new-user-service
            port:
              number: 8080
          weight: 20    # 20% to new K8s service
```

---

## Lift-and-Shift vs. Re-Platform vs. Re-Architect

The migration strategy for each workload depends on its complexity and the business value of modernizing it.

```
MIGRATION STRATEGY DECISION TREE
════════════════════════════════════════════════════════════════

  Start here:
  │
  ├── Is the application actively developed?
  │   ├── NO ──▶ LIFT-AND-SHIFT (containerize as-is)
  │   │          Move the VM contents into a container.
  │   │          Don't change the application.
  │   │          Cost: Low. Risk: Low. Benefit: Low.
  │   │
  │   └── YES ──▶ Does it need fundamental architecture changes?
  │               ├── NO ──▶ RE-PLATFORM (adapt for K8s)
  │               │          Use managed services (RDS instead of self-managed PG).
  │               │          Add health checks, 12-factor config.
  │               │          Cost: Medium. Risk: Medium. Benefit: Medium.
  │               │
  │               └── YES ──▶ RE-ARCHITECT (rebuild for cloud-native)
  │                           Break into microservices.
  │                           Use event-driven patterns.
  │                           Design for horizontal scaling.
  │                           Cost: High. Risk: High. Benefit: High.
```

| Strategy | When to Use | Database Approach | Timeline |
|---|---|---|---|
| Lift-and-shift | Legacy app, no active development, just need it running | Same DB, just in cloud (EC2/GCE + disk) | Days-weeks |
| Re-platform | Active app, keep architecture, use managed services | Migrate to RDS/CloudSQL/Azure SQL | Weeks-months |
| Re-architect | Active app, want cloud-native benefits, willing to invest | New schema, potentially new DB engine | Months-quarters |

---

## CSI Volume Snapshots for Migration

Kubernetes CSI (Container Storage Interface) volume snapshots provide a portable way to snapshot and restore PersistentVolume data. This is the foundation for migrating stateful workloads between clusters.

```yaml
# Step 1: Create a VolumeSnapshot of the source PV
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-data-snapshot
  namespace: databases
spec:
  volumeSnapshotClassName: ebs-csi-snapclass
  source:
    persistentVolumeClaimName: postgres-data
---
# VolumeSnapshotClass (must exist in cluster)
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Retain
parameters:
  tagSpecification_1: "Name=migration-snapshot"
```

```bash
# Check snapshot status
k get volumesnapshot postgres-data-snapshot -n databases
# NAME                     READYTOUSE   RESTORESIZE   AGE
# postgres-data-snapshot   true         100Gi         2m

# The underlying cloud snapshot can be shared across accounts/regions
# AWS: Copy EBS snapshot to another region
SNAPSHOT_ID=$(k get volumesnapshot postgres-data-snapshot -n databases \
  -o jsonpath='{.status.boundVolumeSnapshotContentName}')

# Get the actual EBS snapshot ID
EBS_SNAPSHOT=$(k get volumesnapshotcontent $SNAPSHOT_ID \
  -o jsonpath='{.status.snapshotHandle}')

# Copy to DR region
aws ec2 copy-snapshot \
  --source-region us-east-1 \
  --source-snapshot-id $EBS_SNAPSHOT \
  --destination-region eu-west-1 \
  --description "Migration snapshot for postgres-data"
```

```yaml
# Step 2: In the destination cluster, create a PVC from the snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-restored
  namespace: databases
spec:
  storageClassName: gp3
  dataSource:
    name: postgres-data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

---

## Database Migration Patterns

### Pattern 1: Dump and Restore (Small Databases)

For databases under 10GB, the simplest approach works.

```bash
# PostgreSQL: Dump from source, restore to target
# Use pg_dump with parallel jobs for speed
pg_dump \
  --host=source-db.internal \
  --port=5432 \
  --username=migration_user \
  --format=directory \
  --jobs=4 \
  --file=/tmp/pg_backup \
  mydb

# Restore to the new database (managed service or K8s operator)
pg_restore \
  --host=target-db.rds.amazonaws.com \
  --port=5432 \
  --username=admin \
  --dbname=mydb \
  --jobs=4 \
  --no-owner \
  /tmp/pg_backup

# Downtime = dump time + restore time + DNS switch
# For 5GB database: ~15-30 minutes total
```

### Pattern 2: Logical Replication (Medium Databases)

For databases between 1TB and 10TB, use the database's built-in replication to minimize downtime.

```bash
# PostgreSQL logical replication: continuous sync with near-zero downtime

# On the SOURCE database: enable logical replication
# (postgresql.conf)
# wal_level = logical
# max_replication_slots = 4

# Create a publication (what to replicate)
psql -h source-db.internal -U admin -d mydb <<'SQL'
CREATE PUBLICATION migration_pub FOR ALL TABLES;
SQL

# On the TARGET database: create subscription
psql -h target-db.rds.amazonaws.com -U admin -d mydb <<'SQL'
-- Schema must already exist on the target
-- Create the subscription to start replicating
CREATE SUBSCRIPTION migration_sub
  CONNECTION 'host=source-db.internal port=5432 dbname=mydb user=replication_user password=xxx'
  PUBLICATION migration_pub;

-- Monitor replication lag
SELECT
  slot_name,
  pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) AS lag_bytes
FROM pg_replication_slots
WHERE slot_name = 'migration_sub';
SQL
```

```
LOGICAL REPLICATION MIGRATION TIMELINE
════════════════════════════════════════════════════════════════

Day 1: Set up replication
  Source ──────────── replicating ──────────── Target
  (primary)          (catching up)             (replica)

Day 2-5: Initial sync completes, enters real-time replication
  Source ──────────── real-time sync ──────────Target
  (primary)          (lag < 1 second)          (replica)

Day 5 (cutover window):
  1. Stop writes to source (read-only mode)
  2. Wait for replication lag to reach 0
  3. Verify row counts match
  4. Point application to target
  5. Drop subscription on target
  6. Total write downtime: 30-60 seconds
```

### Pattern 3: Change Data Capture (Large Databases)

For databases over 10TB or when you need zero-downtime migration, use CDC tools like Debezium or AWS DMS.

```
CDC MIGRATION WITH DEBEZIUM
════════════════════════════════════════════════════════════════

  Source Database              Kafka (or Kinesis)        Target Database
  ┌──────────────┐           ┌──────────────┐          ┌──────────────┐
  │              │  Debezium  │              │  Sink    │              │
  │  PostgreSQL  │───────────▶│   Topic per  │─────────▶│  RDS / K8s   │
  │  (on-prem)  │  connector │   table      │ connector│  Operator    │
  │              │           │              │          │              │
  │  WAL ──────▶│           │  orders.cdc  │          │  Applies     │
  │  (change    ││           │  users.cdc   │          │  changes in  │
  │   stream)   ││           │  payments.cdc│          │  order       │
  └──────────────┘           └──────────────┘          └──────────────┘

  Debezium reads the PostgreSQL WAL (Write-Ahead Log)
  and publishes every INSERT, UPDATE, DELETE as a Kafka event.
  A sink connector applies those events to the target database.

  Benefits:
  - Zero downtime (source continues normal operations)
  - Handles any database size
  - Events can be used by other consumers (analytics, search index)
  - Built-in support for schema changes during migration
```

```yaml
# Debezium connector for PostgreSQL (running in K8s via Strimzi)
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: postgres-source-connector
  namespace: kafka
  labels:
    strimzi.io/cluster: kafka-connect
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  tasksMax: 1
  config:
    database.hostname: "source-db.internal"
    database.port: "5432"
    database.user: "debezium"
    database.password: "${file:/opt/kafka/external-configuration/db-credentials/password}"
    database.dbname: "mydb"
    database.server.name: "source"
    plugin.name: "pgoutput"
    publication.name: "debezium_pub"
    slot.name: "debezium_slot"
    snapshot.mode: "initial"
    transforms: "route"
    transforms.route.type: "org.apache.kafka.connect.transforms.RegexRouter"
    transforms.route.regex: "source\\.public\\.(.*)"
    transforms.route.replacement: "$1.cdc"
```

### Pattern 4: Kubernetes Operator Migration

When migrating from a self-managed database to a Kubernetes operator (e.g., CloudNativePG, Percona Operator), you can use the operator's built-in migration capabilities.

```yaml
# CloudNativePG: Create a cluster from an external database backup
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: payments-db
  namespace: databases
spec:
  instances: 3
  storage:
    size: 100Gi
    storageClass: gp3

  # Bootstrap from an external backup (S3)
  bootstrap:
    recovery:
      source: external-backup
      recoveryTarget:
        targetTime: "2026-03-24T10:00:00Z"

  externalClusters:
    - name: external-backup
      barmanObjectStore:
        destinationPath: "s3://pg-backups/source-db/"
        s3Credentials:
          accessKeyId:
            name: s3-creds
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: s3-creds
            key: SECRET_ACCESS_KEY
        wal:
          compression: gzip
```

```bash
# Alternative: Use pg_basebackup to seed the operator
# Run from within the K8s cluster
kubectl run pg-migration --rm -it --restart=Never \
  --image=postgres:16 -- bash -c '
    pg_basebackup \
      --host=source-db.internal \
      --port=5432 \
      --username=replication_user \
      --pgdata=/var/lib/postgresql/data \
      --wal-method=stream \
      --progress \
      --verbose
  '
```

---

## Zero-Downtime Migration Checklist

Every migration follows the same high-level pattern: replicate, verify, cutover, verify again.

```
ZERO-DOWNTIME MIGRATION RUNBOOK
════════════════════════════════════════════════════════════════

PRE-MIGRATION (Days before):
□ Set up replication (logical rep / CDC / DMS)
□ Wait for initial sync to complete
□ Verify row counts match (source vs target)
□ Run application test suite against target database
□ Measure replication lag under normal load
□ Prepare DNS/config changes (but don't apply yet)
□ Notify stakeholders of cutover window

CUTOVER (The actual switch):
□ Enable read-only mode on source (or pause writes)
□ Wait for replication lag to reach 0
□ Run final verification:
  □ Row counts match
  □ Checksums match for sample tables
  □ Sequences are correct on target
□ Update application config to point to target
  (ConfigMap change + rolling restart, or DNS switch)
□ Verify application health after switch
□ Monitor error rates for 30 minutes

POST-MIGRATION:
□ Keep source database running for 48 hours (rollback safety net)
□ Stop replication
□ Remove old connection strings from configs
□ Decommission source database after 1 week
□ Update documentation
```

```bash
# Verification script: compare source and target
#!/bin/bash
set -e

SOURCE_HOST="source-db.internal"
TARGET_HOST="target-db.rds.amazonaws.com"
DB_NAME="mydb"

echo "Comparing table row counts..."
TABLES=$(psql -h $SOURCE_HOST -U admin -d $DB_NAME -t -c \
  "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")

MISMATCH=0
for TABLE in $TABLES; do
  SOURCE_COUNT=$(psql -h $SOURCE_HOST -U admin -d $DB_NAME -t -c \
    "SELECT COUNT(*) FROM $TABLE")
  TARGET_COUNT=$(psql -h $TARGET_HOST -U admin -d $DB_NAME -t -c \
    "SELECT COUNT(*) FROM $TABLE")

  if [ "$SOURCE_COUNT" != "$TARGET_COUNT" ]; then
    echo "MISMATCH: $TABLE - source=$SOURCE_COUNT target=$TARGET_COUNT"
    MISMATCH=1
  else
    echo "OK: $TABLE - $SOURCE_COUNT rows"
  fi
done

if [ "$MISMATCH" -eq 1 ]; then
  echo "VERIFICATION FAILED: Row count mismatches detected"
  exit 1
fi

echo "Comparing sequences..."
psql -h $SOURCE_HOST -U admin -d $DB_NAME -t -c \
  "SELECT sequencename, last_value FROM pg_sequences WHERE schemaname = 'public'" | \
while read -r SEQ_NAME SEQ_VAL; do
  TARGET_VAL=$(psql -h $TARGET_HOST -U admin -d $DB_NAME -t -c \
    "SELECT last_value FROM pg_sequences WHERE sequencename = '$SEQ_NAME'")
  if [ "$SEQ_VAL" != "$TARGET_VAL" ]; then
    echo "SEQUENCE MISMATCH: $SEQ_NAME - source=$SEQ_VAL target=$TARGET_VAL"
  fi
done

echo "Verification complete."
```

---

## Did You Know?

1. **AWS Database Migration Service (DMS) has migrated over 2.5 million databases** since its launch in 2016. The most common migration path is Oracle-to-PostgreSQL, followed by SQL Server-to-Aurora. DMS handles schema conversion (via the Schema Conversion Tool) and ongoing CDC replication. For Kubernetes teams, DMS can replicate to an RDS instance that a K8s operator or application then connects to.

2. **The Strangler Fig pattern was coined by Martin Fowler in 2004**, inspired by the actual strangler fig trees he saw in Australia. These trees germinate in the canopy of a host tree, send roots down to the ground, and gradually envelop the host until the original tree dies. Fowler saw this as the perfect metaphor for gradually replacing a legacy system. The pattern has become the default migration strategy for monolith-to-microservices transitions.

3. **Data transfer over the internet at 1 Gbps takes 9.3 hours for 1TB of data.** For a 50TB database, that's 19 days of continuous transfer -- assuming the network link is fully saturated, which it won't be. AWS Snowball Edge devices transfer 80TB via physical shipping and typically take 4-6 business days door-to-door, making physical transfer faster than network transfer for datasets above ~10TB. GCP has Transfer Appliance and Azure has Data Box for the same purpose.

4. **PostgreSQL's logical replication was introduced in version 10 (2017)** and significantly improved migration tooling. Before logical replication, the primary options for near-zero-downtime migration were: physical replication (requires same PG version and OS), third-party tools like Slony (complex, fragile), or CDC via trigger-based capture (high overhead). Logical replication made it possible to replicate between different PG versions, different platforms (on-prem to cloud), and even different schemas -- transforming database migration from a high-risk event to a routine operation.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Attempting big-bang migration for large databases | "Let's just do it over the weekend" | Use CDC or logical replication for databases over 1TB. Big-bang migrations have unpredictable duration and high rollback cost. |
| Not testing the target database under production load | "It works with test data" | Before cutover, replay production traffic against the target using shadow traffic or load testing. Verify query performance, connection limits, and disk I/O. |
| Forgetting about sequences and auto-increment values | "The data replicated fine" | After replication, sequences on the target may not match. Explicitly advance sequences to match or exceed source values before cutover. |
| Skipping the rollback plan | "The migration will succeed" | Keep the source database running for at least 48 hours after cutover. If the target has issues, you can switch back. Without a rollback plan, you're stuck. |
| Migrating data and application simultaneously | "Let's do it all at once" | Migrate data first (with replication). Verify data. Then switch application. Two independent, reversible steps are safer than one combined step. |
| Ignoring timezone and charset differences | "UTF-8 is UTF-8" | Cloud-managed databases may have different default timezones, collations, or character sets. Verify these match before migration. Mismatches cause subtle data corruption. |
| Not accounting for DNS caching during cutover | "We changed the DNS, it should work immediately" | Application connection pools cache DNS. Even with low TTLs, a rolling restart of application pods may be needed to force new DNS resolution. |
| Using the same credentials for source and target during migration | "It's easier" | Use separate credentials for migration replication. This lets you revoke migration access independently and provides better audit trails. |

---

## Quiz

<details>
<summary>1. What is data gravity and how does it affect migration planning?</summary>

Data gravity is the observation that as data accumulates in one location, it becomes progressively harder and more expensive to move. Applications, services, and integrations develop dependencies on the data's location. Migration difficulty grows with three factors: data size (larger = longer transfer), access frequency (active data has more connections to sever), and integration count (more services reading/writing = more things to migrate simultaneously). Data gravity affects planning by: (a) requiring earlier migration of data-heavy services before they grow further, (b) suggesting CDC/streaming approaches over big-bang for large datasets, and (c) favoring strategies that keep data in place while migrating applications around it.
</details>

<details>
<summary>2. When would you choose the Strangler Fig pattern over a big-bang migration?</summary>

Choose Strangler Fig when: (a) the system is too large or complex to migrate all at once, (b) the business cannot tolerate extended downtime, (c) you want to validate each migrated component independently before proceeding, (d) different components have different migration complexities (some are easy to move, others require rearchitecting), or (e) you need to maintain the ability to roll back individual components. The Strangler Fig pattern trades migration speed for safety and flexibility. The trade-off is that you run two systems in parallel for an extended period, which increases operational cost and requires maintaining routing logic. Choose big-bang only for small systems where the total migration time is within an acceptable downtime window.
</details>

<details>
<summary>3. What is the difference between logical replication and CDC (Change Data Capture) for database migration?</summary>

Logical replication is a database-native feature (built into PostgreSQL 10+, MySQL 5.7+) that replicates SQL-level changes (INSERT, UPDATE, DELETE) from a publication to a subscription. It operates within the database engine and requires both source and target to be the same database type (PG-to-PG, MySQL-to-MySQL). CDC tools like Debezium read the database's transaction log (WAL in PostgreSQL, binlog in MySQL) and publish changes as events to a message broker (Kafka). CDC is more flexible: it works across different database types, can feed multiple consumers, and integrates with stream processing. For a simple same-engine migration, logical replication is simpler. For cross-engine migration or when you need the change stream for other purposes (rebuilding search indexes, analytics), use CDC.
</details>

<details>
<summary>4. You need to migrate a 15TB PostgreSQL database from on-premises to RDS with minimal downtime. Describe the approach.</summary>

Step 1: Set up AWS DMS or Debezium CDC to replicate from the on-premises PostgreSQL to RDS. The initial full load will take several days for 15TB. Step 2: Once the initial load completes, CDC enters real-time replication mode, capturing ongoing changes. Monitor replication lag -- it should stabilize under 1 second. Step 3: Run verification: compare row counts, checksums on sample tables, and test application queries against the target. Step 4: During the cutover window (which can be as short as 60 seconds), set the source to read-only, wait for replication lag to reach zero, update the application's database connection string (via ConfigMap update + rolling restart), and verify the application works against the target. Step 5: Keep the source available for 48 hours as a rollback option. Total downtime: under 2 minutes for the DNS/config switch.
</details>

<details>
<summary>5. Why is it important to advance sequences on the target database before cutover?</summary>

Database sequences generate unique identifiers (auto-incrementing IDs). During replication, the actual ID values are copied, but the sequence counter on the target may not advance because the replicated rows use explicit ID values. After cutover, when new rows are inserted via the target's sequence, the sequence might generate IDs that conflict with replicated data. For example, if the source's sequence is at 1,000,000 but the target's sequence is at 1 (never used), the first insert on the target generates ID=1, which already exists. The fix is to explicitly set each sequence on the target to at least the current value on the source, plus a safety margin, before cutover.
</details>

<details>
<summary>6. How do CSI volume snapshots help with Kubernetes stateful workload migration?</summary>

CSI volume snapshots provide a Kubernetes-native, portable way to capture the state of a PersistentVolume at a point in time. For migration, you snapshot the source PV, which creates a cloud-provider snapshot (EBS snapshot, GCE PD snapshot, Azure disk snapshot). This snapshot can be copied to another region or shared with another account. In the target cluster, you create a new PVC with a `dataSource` referencing the snapshot, which provisions a new volume pre-populated with the snapshot data. This avoids the need for application-level data export/import. The limitation is that CSI snapshots are cloud-provider-specific -- you cannot snapshot an EBS volume and restore it as a GCE PD. For cross-cloud migration, application-level backup/restore (Velero, pg_dump, etc.) is required.
</details>

---

## Hands-On Exercise: Migrate a Database to Kubernetes

In this exercise, you will migrate a PostgreSQL database from a standalone deployment to a CloudNativePG-managed cluster using logical replication.

### Prerequisites

- kind cluster running
- kubectl installed
- PostgreSQL client (psql) installed

### Task 1: Deploy a "Legacy" PostgreSQL Instance

<details>
<summary>Solution</summary>

```bash
# Create the kind cluster
kind create cluster --name migration-lab

# Deploy a standalone PostgreSQL as the "legacy" database
kubectl create namespace legacy

kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: legacy-postgres
  namespace: legacy
spec:
  serviceName: legacy-postgres
  replicas: 1
  selector:
    matchLabels:
      app: legacy-postgres
  template:
    metadata:
      labels:
        app: legacy-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          env:
            - name: POSTGRES_DB
              value: myapp
            - name: POSTGRES_USER
              value: admin
            - name: POSTGRES_PASSWORD
              value: legacy-password
          args:
            - -c
            - wal_level=logical
            - -c
            - max_replication_slots=4
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: legacy-postgres
  namespace: legacy
spec:
  selector:
    app: legacy-postgres
  ports:
    - port: 5432
EOF

# Wait for it to be ready
kubectl wait --for=condition=Ready pod legacy-postgres-0 -n legacy --timeout=120s

# Load sample data
kubectl exec -n legacy legacy-postgres-0 -- psql -U admin -d myapp -c "
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (name, email) VALUES
  ('Alice Johnson', 'alice@example.com'),
  ('Bob Smith', 'bob@example.com'),
  ('Charlie Brown', 'charlie@example.com'),
  ('Diana Prince', 'diana@example.com'),
  ('Eve Torres', 'eve@example.com');

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  total DECIMAL(10,2),
  status VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO orders (user_id, total, status) VALUES
  (1, 99.99, 'completed'),
  (2, 149.50, 'completed'),
  (1, 75.00, 'pending'),
  (3, 200.00, 'completed'),
  (4, 50.25, 'shipped');
"

echo "Legacy database ready with sample data"
```
</details>

### Task 2: Set Up Logical Replication to a New Instance

<details>
<summary>Solution</summary>

```bash
# Deploy a new PostgreSQL instance (simulating the migration target)
kubectl create namespace target

kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: target-postgres
  namespace: target
spec:
  serviceName: target-postgres
  replicas: 1
  selector:
    matchLabels:
      app: target-postgres
  template:
    metadata:
      labels:
        app: target-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          env:
            - name: POSTGRES_DB
              value: myapp
            - name: POSTGRES_USER
              value: admin
            - name: POSTGRES_PASSWORD
              value: target-password
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: target-postgres
  namespace: target
spec:
  selector:
    app: target-postgres
  ports:
    - port: 5432
EOF

kubectl wait --for=condition=Ready pod target-postgres-0 -n target --timeout=120s

# Create the schema on the target (required for logical replication)
kubectl exec -n legacy legacy-postgres-0 -- pg_dump -U admin -d myapp --schema-only | \
  kubectl exec -i -n target target-postgres-0 -- psql -U admin -d myapp

# Set up publication on source
kubectl exec -n legacy legacy-postgres-0 -- psql -U admin -d myapp -c "
CREATE PUBLICATION migration_pub FOR ALL TABLES;
"

# Set up subscription on target
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "
CREATE SUBSCRIPTION migration_sub
  CONNECTION 'host=legacy-postgres.legacy.svc.cluster.local port=5432 dbname=myapp user=admin password=legacy-password'
  PUBLICATION migration_pub;
"

# Verify replication is working
sleep 5
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "SELECT COUNT(*) FROM users;"
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "SELECT COUNT(*) FROM orders;"
```
</details>

### Task 3: Verify Data Consistency

<details>
<summary>Solution</summary>

```bash
# Compare row counts
echo "=== Source ==="
kubectl exec -n legacy legacy-postgres-0 -- psql -U admin -d myapp -c "
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'orders', COUNT(*) FROM orders;"

echo "=== Target ==="
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'orders', COUNT(*) FROM orders;"

# Insert new data on source and verify it appears on target
kubectl exec -n legacy legacy-postgres-0 -- psql -U admin -d myapp -c "
INSERT INTO users (name, email) VALUES ('Frank Castle', 'frank@example.com');
INSERT INTO orders (user_id, total, status) VALUES (6, 175.00, 'pending');
"

# Wait for replication
sleep 3

# Verify on target
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "
SELECT * FROM users WHERE name = 'Frank Castle';
SELECT * FROM orders WHERE user_id = 6;"
```
</details>

### Task 4: Perform the Cutover

<details>
<summary>Solution</summary>

```bash
# Step 1: Verify replication is caught up
kubectl exec -n legacy legacy-postgres-0 -- psql -U admin -d myapp -c "
SELECT slot_name, confirmed_flush_lsn
FROM pg_replication_slots
WHERE slot_name = 'migration_sub';"

# Step 2: Set source to read-only (simulate stopping writes)
kubectl exec -n legacy legacy-postgres-0 -- psql -U admin -d myapp -c "
ALTER DATABASE myapp SET default_transaction_read_only = true;"

# Step 3: Final verification
echo "=== Final Source Count ==="
kubectl exec -n legacy legacy-postgres-0 -- psql -U admin -d myapp -c "
SELECT 'users' as t, COUNT(*) FROM users UNION ALL SELECT 'orders', COUNT(*) FROM orders;"

sleep 2

echo "=== Final Target Count ==="
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "
SELECT 'users' as t, COUNT(*) FROM users UNION ALL SELECT 'orders', COUNT(*) FROM orders;"

# Step 4: Fix sequences on target
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders));"

# Step 5: Drop subscription (stop replication)
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "
DROP SUBSCRIPTION migration_sub;"

# Step 6: Verify new inserts work on target
kubectl exec -n target target-postgres-0 -- psql -U admin -d myapp -c "
INSERT INTO users (name, email) VALUES ('Grace Hopper', 'grace@example.com');
SELECT * FROM users ORDER BY id DESC LIMIT 3;"

echo "Cutover complete! Target is now the primary database."
```
</details>

### Clean Up

```bash
kind delete cluster --name migration-lab
```

### Success Criteria

- [ ] Legacy PostgreSQL deployed with sample data
- [ ] Logical replication established between source and target
- [ ] New data on source automatically appears on target
- [ ] Row counts verified as matching before cutover
- [ ] Sequences advanced on target before cutover
- [ ] New inserts work on target after replication is dropped

---

## Next Module

[Module 8.8: Cloud Cost Optimization (Advanced)](module-8.8-cloud-cost/) -- Your workloads are migrated, replicated, and running across regions. Now learn how to stop hemorrhaging money. Multi-tenant cost allocation, spot instances, savings plans, and the tools that give you visibility into where every dollar goes.

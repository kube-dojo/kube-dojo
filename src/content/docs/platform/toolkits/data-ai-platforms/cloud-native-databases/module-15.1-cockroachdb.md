---
title: "Module 15.1: CockroachDB - Distributed SQL That Survives Anything"
slug: platform/toolkits/data-ai-platforms/cloud-native-databases/module-15.1-cockroachdb
sidebar:
  order: 2
---

## Complexity: [COMPLEX]

## Time to Complete: 65-80 minutes

---

## Prerequisites

Before starting this module, you should have completed:

- [Distributed Systems Foundation](/platform/foundations/distributed-systems/) - consensus, quorum, CAP trade-offs, and failure domains.
- [Reliability Engineering Foundation](/platform/foundations/reliability-engineering/) - SLOs, RPO, RTO, error budgets, and incident response.
- Kubernetes fundamentals - StatefulSets, Services, PersistentVolumeClaims, scheduling, and pod disruption behavior.
- Basic SQL and PostgreSQL familiarity - schemas, indexes, transactions, connection strings, and query plans.

This module assumes you can read Kubernetes manifests and SQL statements, but it does not assume you have operated a distributed SQL database before. The goal is to build the mental model first, then connect that model to concrete CockroachDB operations: deployment, locality, failover, backups, changefeeds, and production trade-off decisions.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a CockroachDB Kubernetes topology that maps replicas, ranges, Raft leaders, and failure domains to concrete availability goals.
- **Configure** multi-region database locality so rows, reads, and writes are placed close to the users and services that need them.
- **Implement** CockroachDB backup schedules, manual restore checks, and changefeed validation commands that support explicit RPO and RTO targets.
- **Diagnose** common failure symptoms such as under-replicated ranges, hot ranges, regional latency spikes, and failed scheduled backups.
- **Evaluate** when CockroachDB is a stronger fit than single-writer PostgreSQL, managed cloud databases, or other distributed SQL systems.

---

## Why This Module Matters

A payments company had a database failover plan that looked excellent in a review document and frightening during the incident. The primary region became unstable during a cloud networking event, the read replica lagged behind the write leader, and the team discovered that the failover checklist had never been tested under real transaction load. One engineer watched customer checkouts time out while another engineer tried to decide whether the replica was fresh enough to promote. The system had backups, dashboards, runbooks, and senior people online, but it still depended on humans making high-pressure decisions while the business was losing money.

The painful lesson was not that PostgreSQL had failed the team. The lesson was that a single-primary database design had pushed too much operational responsibility into the incident window. A regional outage should not be the first time the team learns whether its quorum, replication, application retries, backups, and restore process actually work together. CockroachDB exists for organizations that want SQL semantics while moving more of the replication and failover mechanism into the database layer itself.

CockroachDB does not make reliability automatic, and it does not remove the need for capacity planning, testing, or backup discipline. It gives you a different set of controls: ranges instead of one monolithic storage engine, Raft replication instead of asynchronous replica promotion, locality rules instead of hand-written data placement scripts, and scheduled backups that can be inspected as first-class database objects. The senior skill is knowing which risks CockroachDB reduces, which risks it moves, and which risks remain your responsibility.

| Incident Pressure Point | Single-Primary Pattern | CockroachDB Pattern | Operator Question |
|-------------------------|------------------------|---------------------|-------------------|
| Region loss | Promote a replica or activate DR | Preserve quorum across surviving replicas | Did the topology really place replicas across independent failures? |
| Write availability | Depends on primary reachability | Depends on range quorum and leader movement | Can the majority of replicas still communicate? |
| Read latency | Usually low near the primary, worse elsewhere | Can be local with follower reads or locality-aware placement | Is staleness acceptable for this query path? |
| Data residency | Often enforced by separate databases | Can be modeled with multi-region table locality | Does the schema match the legal and product boundary? |
| Backup operations | External jobs or managed service schedules | SQL-level backup schedules with inspectable state | Has the team restored from the schedule recently? |

The rest of the module teaches CockroachDB as an operating system for distributed SQL. You will start with the internal shape of the system, then deploy it, then make placement decisions, then add backup schedules and restore checks, and finally practice diagnosing a realistic failure. That sequence matters because a command is only useful when you know what failure mode it is meant to control.

---

## Core Content

### 1. The Mental Model: SQL at the Door, Distributed Storage Behind It

CockroachDB looks familiar at the connection boundary because applications speak the PostgreSQL wire protocol and issue SQL statements. That familiarity is useful, but it can also be misleading. A single SQL transaction may coordinate work across multiple nodes, multiple ranges, and multiple Raft groups. The client sees one database endpoint, while the database internally routes requests through layers that split, replicate, rebalance, and persist data across the cluster.

```ascii
COCKROACHDB REQUEST PATH
────────────────────────────────────────────────────────────────────────────

  Application Pod
  ┌─────────────────────┐
  │ PostgreSQL driver   │
  │ SQL transaction     │
  └──────────┬──────────┘
             │
             ▼
  Public SQL Service
  ┌─────────────────────┐
  │ Any Cockroach node  │
  │ parses and plans    │
  └──────────┬──────────┘
             │
             ▼
  Distributed SQL Layer
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Plans scans, joins, writes, and transaction coordination across nodes│
  └──────────┬──────────────────────────────────────────────────────────┘
             │
             ▼
  Range / Raft Layer
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Finds the range that owns each key and reaches quorum for writes     │
  └──────────┬──────────────────────────────────────────────────────────┘
             │
             ▼
  Pebble Storage
  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
  │ Node 1 local disk   │     │ Node 2 local disk   │     │ Node 3 local disk   │
  │ replica copies      │     │ replica copies      │     │ replica copies      │
  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

The most important shift is that CockroachDB distributes data by key ranges, not by whole databases or whole tables. A table starts as one or more contiguous key ranges, and those ranges split as data grows. Each range has replicas on different nodes, and one replica acts as the Raft leaseholder for reads and leader-like coordination for writes. The database can therefore move leadership and replicas for a small part of the keyspace without moving the entire table.

**Pause and predict:** If one table has a million small rows and another table has ten huge rows, which one is more likely to benefit from automatic range splitting? Write down your answer before reading on. The million-row table usually gives the database more natural key boundaries to split and rebalance; the ten huge rows may still create pressure, but the pressure is concentrated in a much smaller set of keys.

This distinction explains why a CockroachDB migration is not just a connection-string change. Your schema, primary keys, indexes, transaction boundaries, and query patterns influence where ranges form and where load concentrates. A monotonically increasing primary key can put heavy write pressure on the end of an index, while a high-cardinality UUID key often spreads writes more evenly. The system automates distribution, but it distributes the workload you give it.

| Concept | What It Means | Why Operators Care |
|---------|---------------|--------------------|
| Node | A CockroachDB process with local storage | Nodes are failure and capacity units that Kubernetes schedules and restarts. |
| Range | A contiguous slice of the keyspace | Ranges are the unit CockroachDB splits, replicates, and rebalances. |
| Replica | A copy of a range on a node | Replicas determine quorum, durability, and locality for that range. |
| Leaseholder | Replica that serves strongly consistent reads for a range | Leaseholder placement affects read latency and hot range behavior. |
| Raft group | Consensus group for one range | Writes need agreement from a quorum of replicas in the group. |

CockroachDB uses serializable isolation by default, which is a strong guarantee for application correctness. Serializable isolation means concurrent transactions behave as if they ran one at a time in some valid order. The trade-off is that conflicting transactions may need to retry, especially when many clients update the same rows or indexes. A production application must therefore treat retryable transaction errors as normal distributed-system behavior, not as rare exceptions.

```sql
CREATE DATABASE shop;

USE shop;

CREATE TABLE inventory (
  sku STRING PRIMARY KEY,
  region STRING NOT NULL,
  available INT NOT NULL CHECK (available >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX inventory_region_idx (region)
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sku STRING NOT NULL REFERENCES inventory (sku),
  region STRING NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX orders_region_created_idx (region, created_at DESC)
);
```

This schema is small enough for a lab but rich enough to show real design pressure. Inventory rows can become hot when many users buy the same product. Orders are naturally append-heavy and can be queried by region and time. The indexes support useful access paths, but they also create additional key ranges that must be replicated and maintained. In CockroachDB, index design is also distribution design.

A beginner often asks, "Is CockroachDB just PostgreSQL with more nodes?" A better senior-level answer is, "CockroachDB offers a PostgreSQL-compatible interface, but it has a distributed transaction and storage engine underneath." That difference affects latency, contention, operational procedures, and failure analysis. You still use SQL, but you must think about geography, quorum, retries, and data movement.

### 2. Ranges, Raft, and Failure Behavior

Raft is the mechanism that lets CockroachDB replicas agree on the order of writes for each range. When a write touches one range, the replicas for that range must replicate the write to a quorum before the write is acknowledged. With three replicas, a quorum is two replicas. If one replica fails, the range can continue accepting writes as long as two replicas can still communicate and one can act as leader for the consensus group.

```ascii
ONE RANGE WITH THREE REPLICAS
────────────────────────────────────────────────────────────────────────────

                  Range: /Table/orders/Keyspace-A
                  Replication target: 3 replicas

       Node A                         Node B                         Node C
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│ Replica A       │            │ Replica B       │            │ Replica C       │
│ Raft leader     │───────────▶│ Raft follower   │───────────▶│ Raft follower   │
│ accepts write   │            │ persists write  │            │ persists write  │
└────────┬────────┘            └────────┬────────┘            └────────┬────────┘
         │                              │                              │
         └──────────── quorum reached when two replicas agree ─────────┘

Result: the write is acknowledged after the required quorum confirms the log entry.
```

The failure behavior is more granular than a traditional primary/replica database because each range has its own replication group. Node A might be the leader for one range, a follower for another range, and not involved at all for many others. When Node A fails, only the ranges with replicas or leadership on Node A need to react. Other ranges continue without caring about that node.

**Stop and think:** Your cluster has three nodes and the replication target is three. One node is deleted and Kubernetes starts recreating it. Should you expect zero operational impact, partial impact, or total outage? The right expectation is partial impact. Available ranges can keep serving through quorum, but some leadership changes, connection resets, and temporary under-replication are normal until the node returns and replicas catch up.

The dangerous misunderstanding is believing that CockroachDB removes the need to reason about failure domains. Three replicas on three pods do not protect you if all three pods are scheduled onto the same worker node, the same zone, or the same storage failure domain. Kubernetes placement, PersistentVolume behavior, node disruption budgets, and cloud topology still matter. CockroachDB can only survive the failures your replica placement actually separates.

```ascii
GOOD AND BAD FAILURE DOMAIN PLACEMENT
────────────────────────────────────────────────────────────────────────────

Bad: replicas separated by pod name only
┌────────────────────────────────────────────────────────────────────────┐
│ Kubernetes Worker: node-1                                              │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │
│ │ crdb-0        │  │ crdb-1        │  │ crdb-2        │               │
│ │ replica copy  │  │ replica copy  │  │ replica copy  │               │
│ └───────────────┘  └───────────────┘  └───────────────┘               │
│ A single worker failure can remove every replica for some ranges.      │
└────────────────────────────────────────────────────────────────────────┘

Better: replicas separated by node and zone
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ Zone A / node-a     │    │ Zone B / node-b     │    │ Zone C / node-c     │
│ ┌─────────────────┐ │    │ ┌─────────────────┐ │    │ ┌─────────────────┐ │
│ │ crdb-0          │ │    │ │ crdb-1          │ │    │ │ crdb-2          │ │
│ │ replica copy    │ │    │ │ replica copy    │ │    │ │ replica copy    │ │
│ └─────────────────┘ │    │ └─────────────────┘ │    │ └─────────────────┘ │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
A zone failure removes one copy, while quorum remains possible in the other zones.
```

A healthy CockroachDB operator watches for unavailable ranges and under-replicated ranges because those symptoms reveal whether the system has enough copies and enough quorum. An unavailable range means the database cannot serve that part of the keyspace. An under-replicated range means the database is serving with fewer replicas than intended, which may be acceptable briefly during recovery but dangerous if it persists.

```sql
SELECT
  sum((ranges_unavailable)::INT) AS unavailable_ranges,
  sum((ranges_underreplicated)::INT) AS underreplicated_ranges
FROM crdb_internal.kv_store_status;
```

The SQL above is useful because it turns a distributed storage condition into a small operator decision. If unavailable ranges are above zero, you are in a customer-impacting database availability event. If under-replicated ranges are above zero after a pod restart, you watch recovery and investigate placement, disk, or network issues if the number does not fall. This is the beginning of operational reasoning, not just metric collection.

### 3. Deploying CockroachDB on Kubernetes

CockroachDB on Kubernetes is usually deployed through a Helm chart or an operator because the database needs StatefulSets, stable network identities, persistent volumes, certificates, Services, and topology labels. A handwritten manifest can be useful for learning, but production teams usually want a supported deployment path that handles common lifecycle details. The important decision is not "Helm versus operator" in the abstract; it is whether your team wants release control through chart values or reconciliation through a custom resource.

| Deployment Option | Best Fit | Trade-Off |
|-------------------|----------|-----------|
| Helm chart | Teams that already manage platform components through GitOps and chart values | Simple to inspect, but upgrades and day-two changes still depend on your process. |
| CockroachDB operator | Teams that prefer a Kubernetes custom resource for database lifecycle | More automation, but another controller must be installed, upgraded, and trusted. |
| Managed CockroachDB | Teams that want Cockroach Labs to operate the control plane | Lower operational burden, but less direct control over Kubernetes placement details. |
| Handwritten manifests | Labs, demos, and learning environments | Good for understanding primitives, risky as a production baseline. |

The examples in this module use `kubectl` first so the commands are obvious. In the hands-on lab, after the first command, you may create the common alias with `alias k=kubectl`; the remaining shell commands use `k` to match the rest of the KubeDojo curriculum. If you paste commands into a fresh shell later, run the alias line again or replace `k` with `kubectl`.

```bash
kubectl create namespace cockroachdb
alias k=kubectl

k get namespace cockroachdb
```

A minimal Helm-based installation starts with the repository, a namespace, a replica count, and persistent storage. This is enough to learn the mechanics, but it is not enough for production because production also needs TLS configuration, topology labels, PodDisruptionBudgets, resource sizing, backup destinations, monitoring, and upgrade procedures. Treat the first deployment as scaffolding, not as a finished platform.

```bash
helm repo add cockroachdb https://charts.cockroachdb.com/
helm repo update

k create namespace cockroachdb --dry-run=client -o yaml | k apply -f -

helm install cockroachdb cockroachdb/cockroachdb \
  --namespace cockroachdb \
  --set statefulset.replicas=3 \
  --set storage.persistentVolume.size=20Gi \
  --set conf.cache=256MiB \
  --set conf.max-sql-memory=256MiB
```

After installation, the first operational check is not "Can I connect?" but "Did Kubernetes give the database stable pods, stable volumes, and enough readiness to initialize?" StatefulSet ordering matters because each pod gets a stable ordinal identity. PersistentVolumeClaims matter because losing a volume is different from restarting a process. Services matter because CockroachDB nodes need predictable peer addresses.

```bash
k rollout status statefulset/cockroachdb -n cockroachdb --timeout=300s

k get pods -n cockroachdb -o wide

k get pvc -n cockroachdb

k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach init --insecure
```

The example uses insecure mode because it keeps the local lab focused on distributed database behavior rather than certificate management. That is acceptable for a disposable learning cluster and unacceptable for production. In production, use TLS, protect SQL users, restrict network access to the SQL and Admin UI ports, and avoid embedding passwords in shell history or application manifests.

```bash
k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure -e "SHOW CLUSTER SETTING version;"

k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach node status --insecure
```

A Kubernetes deployment also needs scheduling intent. If your cluster has zone labels, use anti-affinity and topology spread constraints so pods do not collapse into one failure domain. The database cannot infer your cloud architecture unless Kubernetes exposes it and your manifests use it. The following fragment illustrates the intent: keep CockroachDB pods apart by hostname and spread them across zones when possible.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cockroachdb
  namespace: cockroachdb
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app.kubernetes.io/name: cockroachdb
              topologyKey: kubernetes.io/hostname
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: cockroachdb
```

This fragment is not a complete StatefulSet, and that is intentional: you should normally configure these fields through your Helm values or operator custom resource rather than copy a partial manifest over a chart-managed object. The teaching point is the shape of the control. CockroachDB failure tolerance depends on both database replication and Kubernetes placement.

### 4. Locality and Multi-Region Design

Multi-region CockroachDB design starts with the business question, not the SQL command. Do you need lower read latency for users in different regions, survival through a full regional outage, data residency for regulated users, or all three? Each goal changes replica placement, leaseholder behavior, cost, and write latency. The strongest design is the one that states the goal explicitly before choosing database locality.

```ascii
MULTI-REGION DESIGN QUESTIONS
────────────────────────────────────────────────────────────────────────────

Business goal
     │
     ├── Need regional outage survival?
     │       └── Choose survival goal and enough independent regions.
     │
     ├── Need low-latency regional reads?
     │       └── Place data and leaseholders near read-heavy traffic.
     │
     ├── Need data residency?
     │       └── Model regions in schema and table locality.
     │
     └── Need low-latency global writes?
             └── Reconsider transaction shape, contention, and quorum distance.
```

The most common beginner mistake is assuming that multi-region always improves latency. It can improve read latency when data and leaseholders are close to readers, but it can also increase write latency because quorum may cross geographic distance. A write that must be acknowledged by replicas in multiple regions cannot be faster than the network path required to reach those replicas. CockroachDB gives you controls, not physics exemption.

```sql
ALTER DATABASE shop PRIMARY REGION "us-east1";

ALTER DATABASE shop ADD REGION "us-west1";

ALTER DATABASE shop ADD REGION "europe-west1";

ALTER DATABASE shop SURVIVE REGION FAILURE;
```

The survival goal tells CockroachDB how to place replicas so the database can keep serving when a region is lost, assuming the remaining regions can still form quorum. This is a powerful instruction, but it also increases the importance of capacity planning. The surviving regions must have enough compute, storage, and connection capacity to absorb the work when one region is unavailable.

For user-owned data, `REGIONAL BY ROW` lets the table place rows according to a region column. That is useful when a user's profile, shopping cart, or account state should usually live near that user. It is also useful when the product and legal teams have clear data-residency boundaries. It is not a magic compliance switch because logs, backups, analytics exports, application caches, and support tooling may still move data elsewhere.

```sql
USE shop;

ALTER TABLE inventory ADD COLUMN crdb_region crdb_internal_region NOT NULL DEFAULT default_to_database_primary_region(gateway_region());

ALTER TABLE inventory SET LOCALITY REGIONAL BY ROW;

ALTER TABLE orders ADD COLUMN crdb_region crdb_internal_region NOT NULL DEFAULT default_to_database_primary_region(gateway_region());

ALTER TABLE orders SET LOCALITY REGIONAL BY ROW;
```

This example uses CockroachDB's regional-by-row pattern so the database can place rows based on region metadata. The schema now carries an operational decision: a row is not just an application object, it has a geographic home. Queries that filter by regional data can be served more locally, while global queries may still need cross-region coordination. Senior operators therefore ask developers to include locality in query design, not only in database DDL.

**Pause and predict:** Your application writes an order in Europe but immediately runs a strongly consistent global report from a service in the United States. Which path should be fast, and which path may cross regions? The local order write can be optimized for the row's region, but the global report may still scan or coordinate across regions because it asks a global question.

```sql
EXPLAIN SELECT *
FROM orders
WHERE crdb_region = 'europe-west1'
ORDER BY created_at DESC
LIMIT 20;
```

`EXPLAIN` is your first check when locality does not behave as expected. If the query does not filter on the columns that let CockroachDB narrow the keyspace, the database may still need to scan more data than the application team expects. The database can only optimize around the access pattern expressed in SQL and supported by indexes.

```ascii
LOCALITY-AWARE ORDER FLOW
────────────────────────────────────────────────────────────────────────────

EU user request
     │
     ▼
EU application pod
     │
     ▼
Cockroach SQL gateway in europe-west1
     │
     ├── Write order row with crdb_region = europe-west1
     │
     ├── Keep regional row replicas and leaseholders near EU when possible
     │
     └── Return confirmation after required consensus succeeds

US analytics request
     │
     ▼
US reporting service
     │
     └── Global report may touch ranges from many regions and pay wider latency.
```

This is where CockroachDB becomes a platform engineering topic rather than only a database topic. The platform team must expose safe patterns to application teams: region-aware connection strings, retry wrappers, schema review guidance, dashboard panels, and backup schedule templates. Without those paved roads, every service team rediscovers the same distributed SQL lessons in production.

### 5. Worked Example: Designing Backups for a Regional Commerce Database

Before you write a backup schedule, you must translate business language into technical objectives. Suppose the product team says, "Checkout data must be recoverable if a bad migration corrupts the orders table, and we can tolerate at most 15 minutes of lost order writes." That statement implies a recovery point objective of 15 minutes for critical tables. If the support team also says, "We need a restored copy available within one hour for investigation," that adds a recovery time objective that must be tested, not assumed.

The worked example below models the decision process before asking you to perform a similar task in the hands-on lab. The database is `shop`, the critical tables are `orders` and `inventory`, and the local lab uses `nodelocal://1` as the backup destination. Production would normally use object storage such as S3, GCS, or Azure Blob with IAM controls, encryption, lifecycle rules, and cross-region durability.

```ascii
BACKUP DECISION FLOW
────────────────────────────────────────────────────────────────────────────

Start with business requirement
     │
     ▼
Define RPO and RTO
     │
     ├── RPO 15 minutes means backup or change capture frequency must be close enough.
     │
     └── RTO 60 minutes means restore procedure must be rehearsed and measured.
     │
     ▼
Choose backup scope
     │
     ├── Database backup protects schema plus data for the selected database.
     │
     └── Table backup can reduce blast radius for targeted recovery.
     │
     ▼
Choose destination
     │
     ├── nodelocal for lab only.
     │
     └── Object storage for production.
     │
     ▼
Create schedule, inspect schedule state, and run restore verification.
```

Step one is to create a manual backup so the team knows the destination works before it delegates the task to a schedule. A schedule that points at a broken destination is just delayed failure. In a production review, this is the difference between "we configured backups" and "we have evidence that backups can be written and read."

```sql
BACKUP DATABASE shop INTO 'nodelocal://1/shop-manual-backup';

SHOW BACKUPS IN 'nodelocal://1/shop-manual-backup';
```

Step two is to create a recurring schedule that matches the RPO. The following schedule runs every 15 minutes for the lab database. In a larger production environment, you would usually combine full backups, incremental backups, protected timestamps, storage lifecycle rules, and monitoring around schedule execution. The point is not that every system needs this exact interval; the point is that the interval must follow from the recovery objective.

```sql
CREATE SCHEDULE shop_orders_15_minute
FOR BACKUP DATABASE shop
INTO 'nodelocal://1/shop-scheduled-backups'
RECURRING '*/15 * * * *'
WITH SCHEDULE OPTIONS first_run = now();

SHOW SCHEDULES;
```

Step three is to inspect schedule state after it runs. A backup schedule is an operational object with state, failures, and next-run information. If you never query it, you are trusting a checkbox rather than operating the system. A senior reviewer will ask for the alert that fires when scheduled backups stop succeeding and the evidence that someone restored from the backup recently.

```sql
SELECT
  schedule_id,
  label,
  owner,
  next_run,
  state
FROM [SHOW SCHEDULES]
WHERE label = 'shop_orders_15_minute';
```

Step four is to practice a restore into a separate database name. Restoring over the original database during an incident is rarely the first move because you need to inspect the recovered state before deciding what to replace. A safer workflow restores into an isolated database, compares row counts or checksums, and then plans the application cutover or targeted data repair.

```sql
RESTORE DATABASE shop
FROM LATEST IN 'nodelocal://1/shop-manual-backup'
WITH new_db_name = 'shop_restore';

SELECT count(*) AS restored_orders
FROM shop_restore.orders;
```

Step five is to connect backups to changefeeds. Backups are excellent for point-in-time recovery and disaster recovery, while changefeeds are useful for downstream systems that need a stream of row changes. A changefeed is not a replacement for backups because a corrupt write can be faithfully streamed to downstream consumers. A backup gives you a recovery point; a changefeed gives you movement and integration.

```sql
CREATE CHANGEFEED FOR TABLE shop.orders WITH resolved = '10s';
```

In a real platform, the changefeed would usually write to Kafka, cloud storage, or another supported sink. The sinkless form above is useful for learning because it shows that CockroachDB can emit changes from SQL without requiring you to deploy Kafka first. The operator decision is whether a downstream system needs an ordered stream of changes, a periodic backup, or both.

**Stop and think:** A developer accidentally deploys a migration that sets every order status to `cancelled`, and the changefeed streams those updates successfully. Which recovery tool helps you reconstruct the pre-migration state: the changefeed, the backup, or both? The backup is the safer source for pre-migration state, while the changefeed may help identify the timing and scope of the bad writes. Streaming the wrong update quickly is still wrong.

The worked example shows the reasoning pattern you should reuse: state the recovery objective, prove the destination works, schedule the recurring backup, inspect schedule state, practice restore, and decide where changefeeds fit. The hands-on exercise later asks you to apply the same sequence in a disposable cluster and then observe what happens when a pod fails.

### 6. Monitoring, Hot Ranges, and Operational Signals

CockroachDB exposes both SQL-level introspection and Prometheus metrics. The built-in Admin UI is valuable for exploring the cluster, but production operations should not depend on a person opening a dashboard after an incident starts. Critical signals should become alerts with runbooks: unavailable ranges, under-replicated ranges, high SQL latency, failed backup schedules, disk capacity pressure, and excessive retry errors.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cockroachdb
  namespace: cockroachdb
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: cockroachdb
  endpoints:
    - port: http
      path: /_status/vars
      interval: 15s
```

The most useful monitoring design separates symptoms from causes. High p99 latency is a symptom. A hot range, slow disk, cross-region quorum path, overloaded leaseholder, or retry storm may be the cause. Your dashboard should make that investigation easier by placing workload, range health, node health, and backup schedule state near each other.

```ascii
OPERATIONAL TRIAGE MAP
────────────────────────────────────────────────────────────────────────────

User symptom: checkout latency is high
     │
     ├── SQL latency high?
     │       ├── One statement slow: inspect query plan and indexes.
     │       └── Many statements slow: inspect node, network, and range health.
     │
     ├── Ranges unavailable or under-replicated?
     │       ├── Yes: treat as availability or recovery event.
     │       └── No: continue toward workload and capacity causes.
     │
     ├── Hot ranges visible?
     │       ├── Yes: inspect key design, leaseholder placement, and contention.
     │       └── No: inspect connection pool, CPU, storage, and retries.
     │
     └── Backup schedule failing?
             ├── Yes: fix recovery protection even if serving path is healthy.
             └── No: continue normal incident triage.
```

A hot range happens when too much traffic concentrates on one slice of the keyspace. It often appears when many clients update the same row, insert into a narrow key range, or query through an index that funnels work toward one range. CockroachDB can split and rebalance ranges, but it cannot make a single product inventory row accept infinite conflicting writes without contention. Sometimes the correct fix is schema design, not database tuning.

```sql
SELECT
  range_id,
  lease_holder,
  queries_per_second,
  writes_per_second
FROM crdb_internal.kv_hot_ranges
ORDER BY writes_per_second DESC
LIMIT 10;
```

The query above is a starting point, not a full diagnosis. If the top hot range maps to `inventory` and a single SKU is being updated by every checkout, you may need to redesign the inventory reservation model. Options include splitting inventory into regional buckets, using reservation rows instead of one counter, or moving extremely hot flash-sale logic to a specialized queue. Distributed SQL is powerful, but contention is still contention.

Backup monitoring deserves equal attention because a database can serve traffic perfectly while silently losing recoverability. A failed backup schedule may not wake customers today, but it removes your recovery option for tomorrow's bad migration or regional storage event. Treat scheduled backup failures as reliability incidents with a different clock, not as housekeeping warnings.

```sql
SELECT
  schedule_id,
  label,
  state,
  next_run,
  schedule_expr
FROM [SHOW SCHEDULES]
ORDER BY next_run;
```

This operational view connects directly to the learning outcomes. You are not simply remembering that CockroachDB has backups, Raft, and locality. You are learning how to inspect whether those mechanisms are supporting the actual system goals. That is the difference between deploying a database and operating a database.

---

## Did You Know?

- **CockroachDB uses many Raft groups rather than one global consensus group** - each range has its own replication group, which lets the database rebalance and recover parts of the keyspace independently.
- **Serializable isolation is the default behavior** - applications should include retry handling for transaction conflicts instead of assuming every failed transaction is a permanent application error.
- **Regional-by-row locality turns schema design into placement design** - the region column is not just application metadata because it influences where CockroachDB tries to keep the row.
- **A successful changefeed does not prove recoverability** - changefeeds can stream incorrect writes too, so backups and restore tests remain necessary even when downstream streaming works.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---------|--------------|-----------------|
| Treating CockroachDB as "PostgreSQL with replicas" | The application misses distributed transaction retries, range locality, and cross-region latency effects. | Keep PostgreSQL compatibility in mind, but review transaction boundaries, indexes, and retry behavior as distributed-system concerns. |
| Scheduling all pods into one failure domain | Three database pods can still fail together if Kubernetes places them on the same worker, zone, or storage domain. | Use anti-affinity, topology spread constraints, and database locality settings that match real infrastructure boundaries. |
| Enabling multi-region without stating the goal | Teams may pay higher write latency without knowing whether they are optimizing residency, reads, or regional survival. | Document the availability, latency, and residency goals before choosing survival settings and table locality. |
| Ignoring transaction retry handling | Serializable conflicts and leadership changes can surface as retryable errors that break naive application code. | Use client libraries and application patterns that detect retryable errors and safely retry idempotent transaction blocks. |
| Assuming backups are covered by replication | Replication preserves current state, including accidental deletes and corrupt writes. | Create backup schedules, alert on schedule failures, and restore into an isolated database on a recurring cadence. |
| Creating changefeeds without backpressure planning | A slow sink can lag, fail, or push operational pressure back into the database workflow. | Monitor changefeed lag, sink errors, and downstream capacity before using feeds for critical integrations. |
| Diagnosing latency only from application logs | App logs show symptoms but often hide range, leaseholder, node, and quorum causes. | Correlate SQL latency with hot ranges, node status, range health, and regional network conditions. |
| Skipping restore rehearsals | A backup that has never been restored is an unproven promise during an incident. | Practice restore into a separate database, measure duration, and keep the runbook current. |

---

## Quiz

### Question 1

Your team deploys a three-node CockroachDB cluster on Kubernetes. During a node maintenance window, one CockroachDB pod is evicted and several users report brief checkout latency spikes, but most writes continue succeeding. What should you check first, and why?

<details>
<summary>Show Answer</summary>

Check range health and leadership movement before assuming a full database outage. With three replicas, a one-node loss should still leave quorum for many ranges, but leadership changes, connection resets, and temporary under-replication can increase latency. Start with `crdb_internal.kv_store_status`, `cockroach node status`, pod readiness, and under-replicated range counts. If unavailable ranges are zero and under-replicated ranges recover, the cluster behaved as expected; if unavailable ranges appear, the replica placement or failure scope is worse than the design assumed.
</details>

### Question 2

A product team wants lower latency for European users and asks you to add Europe as a CockroachDB region. Their heaviest transaction writes an order row, updates a global inventory counter, and immediately updates a global promotion budget. What design concern should you raise before approving the request?

<details>
<summary>Show Answer</summary>

You should raise the concern that multi-region placement may not reduce latency for a transaction that still writes globally contended rows. Regional-by-row order placement can help keep order data near European users, but a global inventory counter and global promotion budget may still require cross-region coordination and may create hot ranges. The better design conversation is to split regional state where the business allows it, reduce global contention, and define which queries need strong global consistency versus local latency.
</details>

### Question 3

A developer says the cluster does not need backups because every range has three replicas and the database can survive a node failure. How do you respond in operational terms?

<details>
<summary>Show Answer</summary>

Replication and backups protect against different failure classes. Replication helps preserve availability and durability when nodes or zones fail, but it faithfully replicates bad writes, accidental deletes, and corrupt migrations. A backup schedule gives the team a prior recovery point, and a restore rehearsal proves the team can use that point within the RTO. The correct response is to implement scheduled backups, alert on failed schedules, and practice restore into an isolated database.
</details>

### Question 4

Your scheduled backups show `state = paused` after a maintenance change, and the application is still healthy. The product manager asks whether this can wait until next week because no users are affected. What is the reliability argument for fixing it sooner?

<details>
<summary>Show Answer</summary>

A paused backup schedule is a recoverability incident even if the serving path is healthy. The system is accumulating time without a new recovery point, so the actual RPO is drifting away from the stated objective. If a bad migration or data deletion happens before the schedule resumes, the team may have to restore from an older point than the business agreed to tolerate. Fixing the schedule and confirming a new backup protects future recovery options.
</details>

### Question 5

After enabling `REGIONAL BY ROW`, a service still sees high latency for a regional query. The query filters by `created_at` but not by the region column. What should you investigate?

<details>
<summary>Show Answer</summary>

Investigate the query plan and index design because the query may not be giving CockroachDB a selective regional access path. Regional-by-row locality helps place rows, but a query that does not filter by region may still scan data from multiple regions or use an index that is not aligned with the locality goal. Use `EXPLAIN`, review indexes that include region plus the common sort or filter columns, and verify that the service connects through an appropriate regional gateway.
</details>

### Question 6

During a flash sale, the database remains available but one range shows far higher writes per second than the others. The hot range maps to an inventory table where every checkout decrements the same SKU row. Which fix is most likely to address the root cause?

<details>
<summary>Show Answer</summary>

The root cause is workload contention on a narrow key, so a schema or workflow change is more likely to help than simply adding nodes. You could model inventory as regional or bucketed reservation rows, queue extremely hot purchase attempts, or separate reservation from final settlement. Adding nodes may help other workloads, but it cannot remove the conflict created when every transaction updates the same row.
</details>

### Question 7

A team wants to use a changefeed as its only recovery mechanism because it streams every order update to object storage. What scenario shows the weakness in that plan?

<details>
<summary>Show Answer</summary>

A bad migration or application bug can update many rows incorrectly, and the changefeed will stream those incorrect updates just as successfully as correct ones. The stream may help identify when the corruption began, but it does not automatically give you a clean pre-corruption database state. You still need backups and restore tests so you can recover a known good point and compare it with the change history.
</details>

### Question 8

You are reviewing a proposed CockroachDB migration from Aurora PostgreSQL. The application uses long transactions that update many tables, stores session state in the database, and has no retry wrapper for serialization failures. What should block the migration plan until it is fixed?

<details>
<summary>Show Answer</summary>

The lack of retry handling and the long, broad transactions should block the plan because CockroachDB's serializable distributed transactions can surface retryable conflicts under contention or leadership movement. The team should shorten transaction scopes, make retryable operations safe, move ephemeral session patterns out of critical transactional paths where possible, and load test the changed behavior before production cutover. A compatibility test that only checks SQL syntax is not enough.
</details>

---

## Hands-On Exercise

### Task: Deploy CockroachDB, Configure Backups, and Simulate a Node Failure

**Objective**: Build a disposable three-node CockroachDB cluster on Kubernetes, load a small commerce schema, create and inspect a backup schedule, verify a manual restore path, and observe cluster behavior during a pod failure.

**Scenario**: Your platform team is evaluating whether CockroachDB is a good fit for a regional commerce service. The service needs SQL, node-failure tolerance, scheduled backups with a 15-minute RPO target in the lab, and enough operational visibility that an on-call engineer can tell the difference between a temporary pod restart and a real data availability event.

**Success Criteria**:

- [ ] A three-node CockroachDB StatefulSet is running in a local Kubernetes cluster.
- [ ] The `shop` database contains `inventory` and `orders` data loaded through SQL.
- [ ] A manual backup is created and listed from the configured backup destination.
- [ ] A recurring backup schedule exists and can be inspected with `SHOW SCHEDULES`.
- [ ] A restore into `shop_restore` succeeds and returns the expected order count.
- [ ] Deleting one CockroachDB pod does not delete the `shop` data.
- [ ] You record the difference between pod recovery, under-replication, and unavailable ranges.

### Step 1: Create a Local Kubernetes Cluster

This lab uses kind because it gives you a disposable Kubernetes cluster with multiple worker nodes. The cluster is not a production topology, but it is enough to observe StatefulSet identity, pod restart behavior, and basic CockroachDB replication. The `extraMounts` section gives each node a local directory that CockroachDB can use for `nodelocal` backup examples.

```bash
cat > kind-crdb-config.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraMounts:
      - hostPath: /tmp/crdb-lab-backups-control
        containerPath: /cockroach-backups
  - role: worker
    extraMounts:
      - hostPath: /tmp/crdb-lab-backups-worker-1
        containerPath: /cockroach-backups
  - role: worker
    extraMounts:
      - hostPath: /tmp/crdb-lab-backups-worker-2
        containerPath: /cockroach-backups
  - role: worker
    extraMounts:
      - hostPath: /tmp/crdb-lab-backups-worker-3
        containerPath: /cockroach-backups
EOF

kind create cluster --name crdb-lab --config kind-crdb-config.yaml

kubectl cluster-info --context kind-crdb-lab

alias k=kubectl
```

### Step 2: Deploy a Three-Node CockroachDB Cluster

The manifest below uses insecure mode and small memory settings so the lab can run on a laptop. It also sets `--external-io-dir=/cockroach-backups`, which is required for the `nodelocal` backup destination used later. Production clusters should use TLS, real storage classes, resource requests sized from load tests, and supported chart or operator configuration.

```bash
k create namespace cockroachdb

cat > cockroachdb-lab.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: cockroachdb-public
  namespace: cockroachdb
  labels:
    app: cockroachdb
spec:
  selector:
    app: cockroachdb
  ports:
    - name: sql
      port: 26257
      targetPort: 26257
    - name: http
      port: 8080
      targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: cockroachdb
  namespace: cockroachdb
  labels:
    app: cockroachdb
spec:
  clusterIP: None
  selector:
    app: cockroachdb
  ports:
    - name: grpc
      port: 26257
      targetPort: 26257
    - name: http
      port: 8080
      targetPort: 8080
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: cockroachdb
  namespace: cockroachdb
spec:
  serviceName: cockroachdb
  replicas: 3
  selector:
    matchLabels:
      app: cockroachdb
  template:
    metadata:
      labels:
        app: cockroachdb
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: cockroachdb
          image: cockroachdb/cockroach:v23.2.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 26257
              name: sql
            - containerPort: 8080
              name: http
          command:
            - /cockroach/cockroach
            - start
            - --insecure
            - --join=cockroachdb-0.cockroachdb,cockroachdb-1.cockroachdb,cockroachdb-2.cockroachdb
            - --advertise-addr=$(POD_NAME).cockroachdb
            - --listen-addr=0.0.0.0
            - --http-addr=0.0.0.0:8080
            - --cache=256MiB
            - --max-sql-memory=256MiB
            - --external-io-dir=/cockroach-backups
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          volumeMounts:
            - name: datadir
              mountPath: /cockroach/cockroach-data
            - name: backupdir
              mountPath: /cockroach-backups
      volumes:
        - name: backupdir
          hostPath:
            path: /cockroach-backups
            type: DirectoryOrCreate
  volumeClaimTemplates:
    - metadata:
        name: datadir
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
EOF

k apply -f cockroachdb-lab.yaml

k rollout status statefulset/cockroachdb -n cockroachdb --timeout=300s

k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach init --insecure
```

### Step 3: Load the Commerce Schema

This schema intentionally includes a small inventory table and an orders table because those tables create different operational questions. Inventory can become contentious when many transactions update the same SKU, while orders are append-heavy and useful for backup and restore verification. The row counts are small so you can focus on mechanism rather than waiting for a load test.

```bash
k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure <<'EOF'
CREATE DATABASE IF NOT EXISTS shop;

USE shop;

CREATE TABLE IF NOT EXISTS inventory (
  sku STRING PRIMARY KEY,
  region STRING NOT NULL,
  available INT NOT NULL CHECK (available >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX inventory_region_idx (region)
);

CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sku STRING NOT NULL REFERENCES inventory (sku),
  region STRING NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX orders_region_created_idx (region, created_at DESC)
);

UPSERT INTO inventory (sku, region, available) VALUES
  ('keyboard-pro', 'us-east1', 1000),
  ('monitor-wide', 'us-west1', 500),
  ('dock-station', 'europe-west1', 250);

INSERT INTO orders (sku, region, quantity)
SELECT
  sku,
  region,
  ((random() * 5)::INT + 1)
FROM inventory, generate_series(1, 40);

SELECT count(*) AS order_count FROM orders;
EOF
```

### Step 4: Create a Manual Backup and Inspect It

The manual backup proves the backup destination works before you create a schedule. In production, this step would use cloud object storage and credentials managed outside the SQL statement. In this lab, `nodelocal://1` stores the backup under the external I/O directory for node one, which is good enough for practicing the command sequence.

```bash
k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure <<'EOF'
BACKUP DATABASE shop INTO 'nodelocal://1/shop-manual-backup';

SHOW BACKUPS IN 'nodelocal://1/shop-manual-backup';
EOF
```

### Step 5: Create and Inspect a Backup Schedule

Now create a recurring schedule that matches the lab's 15-minute RPO target. You are not waiting 15 minutes for the whole lesson; the purpose is to see that CockroachDB stores the schedule as an inspectable object. If the statement fails, fix the destination or SQL before moving on, because a broken schedule is not a recovery plan.

```bash
k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure <<'EOF'
CREATE SCHEDULE shop_orders_15_minute
FOR BACKUP DATABASE shop
INTO 'nodelocal://1/shop-scheduled-backups'
RECURRING '*/15 * * * *'
WITH SCHEDULE OPTIONS first_run = now();

SELECT
  schedule_id,
  label,
  owner,
  next_run,
  state
FROM [SHOW SCHEDULES]
WHERE label = 'shop_orders_15_minute';
EOF
```

### Step 6: Restore into an Isolated Database

A restore test should avoid overwriting the original database. Restoring into `shop_restore` lets you compare data without changing the serving path. If this step fails, treat it as a serious finding: your backup exists, but your recovery procedure is not yet proven.

```bash
k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure <<'EOF'
RESTORE DATABASE shop
FROM LATEST IN 'nodelocal://1/shop-manual-backup'
WITH new_db_name = 'shop_restore';

SELECT count(*) AS restored_orders
FROM shop_restore.orders;
EOF
```

### Step 7: Observe Cluster Health Before Failure

Capture a baseline before deleting a pod. This baseline helps you distinguish normal restart turbulence from a real availability problem. If your baseline already shows unavailable ranges or unhealthy pods, do not start the failure test yet because you would be testing a broken starting condition.

```bash
k get pods -n cockroachdb -o wide

k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach node status --insecure

k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure -e \
  "SELECT sum((ranges_unavailable)::INT) AS unavailable_ranges, sum((ranges_underreplicated)::INT) AS underreplicated_ranges FROM crdb_internal.kv_store_status;"
```

### Step 8: Simulate One Pod Failure

Delete one pod and watch the StatefulSet recreate it. A pod deletion is not the same as a regional outage, but it is a useful first failure because it shows how Kubernetes process recovery and CockroachDB replica recovery interact. Expect some temporary movement and reconnection, not a need to manually promote a primary.

```bash
k delete pod cockroachdb-1 -n cockroachdb

k get pods -n cockroachdb -w
```

Open a second terminal for the next commands while the watch runs, or stop the watch after the recreated pod is visible. The goal is to observe the system rather than stare at a single command. A senior operator gathers multiple signals: pod state, node status, range health, and application data checks.

```bash
k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure -e \
  "SELECT count(*) AS orders_after_pod_delete FROM shop.orders;"

k exec -n cockroachdb cockroachdb-0 -- \
  /cockroach/cockroach sql --insecure -e \
  "SELECT sum((ranges_unavailable)::INT) AS unavailable_ranges, sum((ranges_underreplicated)::INT) AS underreplicated_ranges FROM crdb_internal.kv_store_status;"
```

### Step 9: Record Your Findings

Write down what happened in operational language. Did the pod return? Did the order count remain stable? Did under-replication appear and then recover? Did unavailable ranges stay at zero? Your answer should separate the Kubernetes event from the database health result because those are related but not identical.

```bash
cat > crdb-lab-notes.md <<'EOF'
# CockroachDB Lab Notes

## Baseline
- Pods ready:
- Order count:
- Unavailable ranges:
- Under-replicated ranges:

## Failure Test
- Deleted pod:
- Time until pod recreated:
- Order count after deletion:
- Unavailable ranges after deletion:
- Under-replicated ranges after deletion:

## Interpretation
- Did the cluster preserve data?
- Was there a serving outage or only recovery activity?
- What would need to change for a real multi-zone or multi-region production design?
EOF

sed -n '1,120p' crdb-lab-notes.md
```

### Step 10: Clean Up

Remove the kind cluster when you are finished. The backup directories under `/tmp` are lab artifacts and can also be removed if you do not need them for inspection. Do not run cleanup until you have captured your notes and verification outputs.

```bash
kind delete cluster --name crdb-lab

rm -rf /tmp/crdb-lab-backups-control \
  /tmp/crdb-lab-backups-worker-1 \
  /tmp/crdb-lab-backups-worker-2 \
  /tmp/crdb-lab-backups-worker-3
```

---

## Next Module

- **Next Module**: [Module 15.2: CloudNativePG](../module-15.2-cloudnativepg/) — PostgreSQL on Kubernetes with operators

---

## Sources

- [In Search of an Understandable Consensus Algorithm](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro) — Primary reference for Raft, the consensus algorithm discussed in the module.

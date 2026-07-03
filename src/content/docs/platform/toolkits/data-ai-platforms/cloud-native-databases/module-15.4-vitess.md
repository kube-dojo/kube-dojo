---
revision_pending: false
title: "Module 15.4: Vitess - Scaling MySQL to YouTube Numbers"
slug: platform/toolkits/data-ai-platforms/cloud-native-databases/module-15.4-vitess
sidebar:
  order: 5
---
## Complexity: `[COMPLEX]`
## Time to Complete: 50-55 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 15.1: CockroachDB](../module-15.1-cockroachdb/) - Distributed database concepts
- [Module 15.3: Neon & PlanetScale](../module-15.3-serverless-databases/) - PlanetScale is built on Vitess
- MySQL fundamentals (basic SQL, replication concepts)
- Kubernetes fundamentals (StatefulSets, Services, Operators)
- [Distributed Systems Foundation](/platform/foundations/distributed-systems/) - Sharding concepts

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Vitess on Kubernetes for horizontal scaling of MySQL with transparent sharding**
- **Configure Vitess VSchema and sharding strategies for distributing data across multiple MySQL instances**
- **Implement Vitess schema migrations, resharding operations, and backup/restore workflows**
- **Evaluate Vitess's MySQL-compatible sharding against CockroachDB, Citus, and Spanner for relational scale-out needs**

---

## Why This Module Matters

Every relational database eventually hits a wall. A single MySQL server can only handle so many writes per second, store so many rows, and accept so many concurrent connections before latency spikes and the system degrades. You can buy a bigger machine — vertical scaling — but that path has a hard ceiling defined by the largest available instance size, and the cost curve bends upward sharply near that ceiling. The durable alternative is horizontal scaling: splitting your data across multiple independent MySQL instances, each responsible for a subset of rows, so that write throughput, storage capacity, and connection count all scale with the number of shards rather than with a single machine's limits.

Horizontal sharding solves the scaling problem but introduces its own costs: cross-shard queries become more expensive or impossible, transactions that span shards require distributed coordination, and the operational burden of managing a fleet of MySQL instances is significantly higher than managing one. Vitess is a CNCF Graduated project, originally built at YouTube to solve exactly this tension: it wraps a fleet of MySQL instances behind a MySQL-protocol-compatible proxy so that applications continue to issue standard SQL, while Vitess handles query routing, shard topology, schema changes, failover, and online resharding beneath that surface.

The durable lesson of Vitess is not the tool itself but the pattern it codifies. The decision to shard a relational database forces you to choose a sharding key — the column whose value determines which shard owns a row — and that choice reverberates through every query, every join, and every future resharding operation for the lifetime of the dataset. This module teaches that decision, the serving architecture that makes it transparent to applications, and the operational workflows that let you reshape a sharded cluster without downtime. These concepts transfer directly to any sharded relational system, whether you are evaluating Vitess, Citus for Postgres, or a managed sharding service.

> **Hypothetical scenario:** Consider a team running a multi-tenant SaaS platform on a single MySQL primary. The database handles roughly 5,000 queries per second across 50 tenants, with the largest tenant generating about 800 QPS alone. Growth projections show that tenant count will double within 18 months and the largest tenant could reach 3,000 QPS — well past what a single MySQL instance can serve with acceptable latency. A rewrite onto a different database engine would take an estimated 18 months and risk regressions across every feature. Manual application-level sharding would require breaking the codebase's assumption of a single logical database, touching every query path. The team deploys Vitess as a proxy layer, keeps their MySQL schema and SQL, chooses `tenant_id` as the sharding key so each tenant's data stays co-located on a single shard, and scales horizontally by adding shards as tenant count grows — all without application changes beyond pointing the connection string at VTGate instead of MySQL directly.

---

## The Durable Spine: Why Sharding

### The Scaling Wall of a Single Primary

A single MySQL server faces several distinct limits that compound as a workload grows. The first is **write throughput**: every INSERT, UPDATE, and DELETE must serialize through the primary's write path. InnoDB's redo log, buffer pool contention, and disk I/O bandwidth all impose an upper bound — typically somewhere between a few thousand and a few tens of thousands of writes per second on modern hardware, depending on workload characteristics and tuning. Read replicas can offload SELECT traffic, but they do not help with writes; the primary remains the sole writer, and adding replicas actually increases the write load slightly because the primary must ship binlog events to each replica.

The second limit is **dataset size**. As tables grow into the hundreds of gigabytes or terabytes, even well-indexed queries scan more internal B-tree pages, and maintenance operations like schema changes, backups, and crash recovery all take longer in proportion to data volume. Working-set memory — the portion of the dataset that must reside in the buffer pool for acceptable performance — grows with the dataset, and when the working set exceeds available RAM, the database begins to thrash on disk I/O. Vertical scaling by moving to a larger instance helps up to the largest available machine in a cloud region, but the cost of that machine is often disproportionate to the capacity gained.

The third limit is **connection count**. Every application instance opens a connection pool to the database, and MySQL's thread-per-connection model means that thousands of concurrent connections consume memory and CPU for thread scheduling even when most connections are idle. Connection pooling at the application layer helps, but at internet scale the aggregate connection count across all application instances can still overwhelm a single server.

These limits are not independent. A table scan on a large dataset during a peak write period compounds all three: it consumes I/O bandwidth that could be serving writes, pulls data pages into the buffer pool that may evict hot rows, and holds connections open while the scan runs. The result is not a graceful degradation but a nonlinear collapse — latency spikes, connection timeouts cascade, and the database enters a death spiral that can take minutes to hours to recover from.

### Horizontal Sharding as the Answer — and Its Costs

Horizontal sharding addresses all three limits by splitting a logical table across multiple independent MySQL instances, each responsible for a disjoint subset of rows. Because each shard is a full MySQL instance with its own storage, buffer pool, and write path, aggregate write throughput scales linearly with the number of shards, total storage capacity is the sum of per-shard capacity, and connections are distributed across shards rather than concentrated on one server.

The mechanism that makes this work is the **sharding key**: a column (or set of columns) whose value determines which shard owns a given row. A hash function maps the sharding key to a shard identifier, and every query that includes the sharding key in its WHERE clause can be routed to exactly one shard — a single-shard query that is as fast as querying a standalone MySQL instance. This is the best-case scenario and the one you design for.

The costs emerge when a query does not include the sharding key. A `SELECT COUNT(*) FROM orders WHERE status = 'pending'` must be sent to every shard — a scatter query — and the results merged by the routing layer. Aggregations, full-table scans, and joins between tables sharded on different keys all become scatter operations that grow more expensive with shard count. Cross-shard transactions, where a single logical transaction must atomically update rows on multiple shards, require a two-phase commit protocol that doubles the round trips and introduces a period where partial failure can leave data inconsistent — a problem that a single-primary MySQL avoids entirely.

The operational burden also rises. Each shard is a MySQL instance that needs monitoring, backup, schema management, and failover handling. A cluster of 16 shards running with replication (each shard having a primary and two replicas) means 48 MySQL instances to operate. Without automation, this is unsustainable. Vitess absorbs this operational complexity by managing the fleet through its own control plane.

---

## The Vitess Sharding Model

### Keyspaces, Shards, and Vindexes

Vitess organizes data into three conceptual layers that build on each other. A **keyspace** is a logical database — analogous to a MySQL database — that may be either unsharded (all data lives on a single MySQL instance) or sharded (data is distributed across multiple MySQL instances according to a sharding scheme). An unsharded keyspace is how you begin: you deploy Vitess in front of your existing MySQL server with no sharding, giving you the serving topology and operational tooling without the complexity of data distribution. You shard a keyspace later, when scaling demands it, using Vitess's online resharding workflow.

A **shard** is a horizontal partition of a sharded keyspace. Each shard is a fully independent MySQL deployment — typically a primary with one or more replicas — that owns a contiguous range of the keyspace's address space. Vitess uses a 64-bit keyspace ID to identify each shard's range. A simple two-shard split might assign keyspace IDs `0x00–0x7F` to shard `-80` and `0x80–0xFF` to shard `80-`. When you reshard to four shards, those ranges are subdivided further: `-40`, `40-80`, `80-c0`, and `c0-`. The keyspace ID is an internal identifier computed from the sharding key; applications never see it.

A **vindex** — short for Vitess index — is the function that maps a sharding key value to a keyspace ID, and therefore to a specific shard. This is the most consequential design decision in any Vitess deployment, because it determines which rows are co-located and which queries are single-shard versus scatter. The simplest vindex type is `hash`: Vitess hashes the sharding key value (typically with a 64-bit hash function) and maps the hash to a keyspace ID range. Hash vindexes distribute rows uniformly across shards, which is ideal for write throughput and storage balance, but they destroy any locality that the sharding key's natural ordering might provide — consecutive `user_id` values end up on different shards, so range scans like `WHERE user_id BETWEEN 1000 AND 2000` become scatter queries.

A **lookup vindex** solves a different problem. Sometimes the column you want to use as a sharding key is not the column your queries filter on. For example, you might shard an orders table by `user_id` so that all of one user's orders are co-located, but your application also needs to look up an order by its `order_id` — and you do not know the `user_id` at query time. A consistent lookup vindex maintains a separate lookup table that maps `order_id` to the keyspace ID (and therefore to the shard), allowing Vitess to resolve a single-shard query from `order_id` alone. The cost is an extra round trip to the lookup table on every insert and on queries that use the secondary key.

### Primary Versus Secondary Vindexes

Every sharded table has one **primary vindex** — the column whose value determines the shard for every row. The primary vindex is mandatory, and it is the only vindex used during INSERT and DELETE operations to decide where a row lives. When you define a table's VSchema, the `column_vindexes` array specifies the primary vindex first; every subsequent entry in that array is a secondary vindex that provides alternative lookup paths for SELECT queries.

Choosing the primary vindex well means identifying the column that appears most frequently in your application's WHERE clauses and that naturally groups related rows together. For a multi-tenant application, `tenant_id` is the canonical choice: all of one tenant's data across all tables lives on the same shard, so joins between tables within a tenant are local single-shard operations. For a social network, `user_id` co-locates all of one user's content but scatters their followers' content across shards — a tradeoff you must understand before committing to the design.

The decision is hard to reverse. Changing the primary vindex requires a full reshard — copying every row to new shards organized around the new key — which is supported as an online operation but is still a major cluster event. This is why Vitess encourages starting unsharded, profiling real query patterns under load, and only choosing a sharding key once you have empirical data about which columns drive your most frequent and most expensive queries.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**

> Vitess has been a **CNCF Graduated** project since November 5, 2019 — the highest maturity level in the CNCF ecosystem, indicating widespread production adoption, a healthy committer community, and a documented governance process. The current stable release line is v21.x (v21.0 released 2024-12), and the project maintains backward compatibility across major versions for the MySQL protocol, VSchema format, and topology service schema. The Vitess Operator for Kubernetes (maintained by PlanetScale) is the recommended deployment path for Kubernetes-native Vitess clusters, though the older Helm chart and manual `vtctld`-based deployment remain supported. Vitess's core architecture — VTGate, VTTablet, the topology service abstraction, and the VReplication subsystem — has been stable across releases for years; the churn is in Kubernetes operator features, version support for underlying MySQL releases, and the managed service landscape around Vitess (PlanetScale, managed Vitess on various cloud marketplaces).

---

## The Serving Topology

```text
VITESS ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                       Your Application                          │
│                       (unchanged!)                              │
│                              │                                  │
│                              │ mysql://                         │
│                              ▼                                  │
├─────────────────────────────────────────────────────────────────┤
│                           VTGate                                │
│                    (Proxy / Query Router)                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  * MySQL protocol (apps think they're talking to MySQL)   │ │
│  │  * Query parsing and planning                             │ │
│  │  * Routes queries to correct shard(s)                     │ │
│  │  * Aggregates results from multiple shards                │ │
│  │  * Connection pooling                                      │ │
│  │  * Query rewriting                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│           ┌──────────────────┼──────────────────┐              │
│           │                  │                  │              │
│           ▼                  ▼                  ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  VTTablet   │    │  VTTablet   │    │  VTTablet   │        │
│  │  (Shard 0)  │    │  (Shard 1)  │    │  (Shard 2)  │        │
│  │             │    │             │    │             │        │
│  │  ┌───────┐  │    │  ┌───────┐  │    │  ┌───────┐  │        │
│  │  │ MySQL │  │    │  │ MySQL │  │    │  │ MySQL │  │        │
│  │  │Primary│  │    │  │Primary│  │    │  │Primary│  │        │
│  │  └───────┘  │    │  └───────┘  │    │  └───────┘  │        │
│  │  ┌───────┐  │    │  ┌───────┐  │    │  ┌───────┐  │        │
│  │  │Replica│  │    │  │Replica│  │    │  │Replica│  │        │
│  │  └───────┘  │    │  └───────┘  │    │  └───────┘  │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     Topology Service                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  etcd / ZooKeeper / Consul                                │ │
│  │  * Stores cluster topology                                │ │
│  │  * Shard locations                                        │ │
│  │  * VSchema (sharding configuration)                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│                          VTOrc                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  * Automatic failover (primary crash)                     │ │
│  │  * Replication health monitoring                          │ │
│  │  * Reparenting decisions                                  │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### VTGate: The Stateless Query-Routing Proxy

VTGate is the entry point for all application traffic in a Vitess cluster. It speaks the MySQL wire protocol on port 3306, which means any MySQL client — your application's ORM, the `mysql` command-line tool, or a JDBC driver — can connect to VTGate exactly as it would to a standalone MySQL server. This protocol compatibility is Vitess's most important architectural property: it decouples the application's data-access code from the sharding topology, so the decision to shard or reshard does not require application changes beyond updating the connection string.

When a query arrives, VTGate parses it to extract the table names and WHERE clause filters, consults the VSchema to determine which vindexes apply, computes the keyspace ID from the sharding key value if present, and routes the query to the correct VTTablet. For a single-shard query — one whose WHERE clause includes the primary vindex column with an equality condition — this is a direct pass-through to one shard. For a scatter query, VTGate fans out to all shards in parallel, collects the results, merges them (performing any ORDER BY, GROUP BY, or LIMIT that spans shards), and returns the final result set to the application.

VTGate is stateless and horizontally scalable: you deploy multiple VTGate instances behind a load balancer, and each one independently handles queries using the topology service as its source of truth for shard locations and VSchema definitions. Because VTGates do not coordinate with each other, adding VTGate instances linearly increases query throughput up to the point where the underlying shards become the bottleneck.

### VTTablet: The Per-MySQL-Instance Manager

Every MySQL instance in a Vitess cluster — whether primary or replica — is paired with a VTTablet process that runs alongside it, typically as a sidecar container in Kubernetes or as a co-located process on a bare-metal host. VTTablet is the agent that manages that MySQL instance's lifecycle: it handles health checks and reports status to the topology service, it enforces query rewrite rules and connection pooling, and it executes the VReplication streams that power online resharding and schema changes.

VTTablet also owns the authoritative view of the MySQL instance's replication state. When a primary fails, VTOrc (the Vitess Orchestrator) detects the failure through VTTablet's health reporting and promotes a replica to primary by issuing a reparent command through the VTTablet on the chosen replica. This reparenting updates the topology service, and VTGates pick up the change within seconds, redirecting write traffic to the new primary without application intervention.

### The Topology Service

The topology service is the distributed consensus store that holds the Vitess cluster's global state: which shards exist, where each tablet (MySQL instance) lives and which host it runs on, what the current VSchema definition is, and metadata about in-flight workflows like resharding operations. Vitess supports etcd, ZooKeeper, and Consul as topology service backends — etcd is the most common choice on Kubernetes because it ships as a built-in component of the Vitess Operator deployment and is already familiar to Kubernetes operators.

The topology service is the single source of truth for all Vitess components. VTGates watch the topology for changes so they can route queries to the correct shards without restarting. VTTablets write their health status into the topology so that VTOrc can make failover decisions. The `vtctld` management server provides a gRPC API (and the `vtctlclient` CLI) that reads from and writes to the topology service for administrative operations. Because the topology service is the cluster's brain, its availability and consistency are prerequisites for all Vitess operations; a topology service outage freezes the cluster — existing connections continue to serve queries from cached topology data, but no administrative operations can proceed and VTGate eventually loses the ability to route to newly added shards.

### VTOrc: Automated Failover

VTOrc — the Vitess Orchestrator — watches the health of every MySQL instance through VTTablet's heartbeat reporting and, when it detects that a primary has failed unrecoverably, selects the most up-to-date replica and promotes it to primary. This reparenting operation updates the topology service, and VTGates begin routing writes to the new primary within seconds.

VTOrc is designed for the reality of sharded MySQL at scale: with dozens or hundreds of MySQL instances in a cluster, primary failures are statistically frequent even when each individual instance is reliable. A human operator cannot respond to every failure at 3 AM; VTOrc automates the detection, decision, and cutover so that failover becomes a routine cluster event rather than an incident.

---

## How a Query Flows: Worked Example

Consider a two-shard keyspace named `commerce` with a `hash` vindex on `user_id` and the following VSchema:

```json
{
  "sharded": true,
  "vindexes": {
    "hash": {
      "type": "hash"
    }
  },
  "tables": {
    "users": {
      "column_vindexes": [
        {
          "column": "user_id",
          "name": "hash"
        }
      ]
    },
    "orders": {
      "column_vindexes": [
        {
          "column": "user_id",
          "name": "hash"
        }
      ]
    },
    "products": {
      "type": "reference"
    }
  }
}
```

When a user with `user_id = 1001` places an order, the application issues:

```sql
INSERT INTO orders (order_id, user_id, product_id, amount)
VALUES (5001, 1001, 42, 99.99);
```

VTGate receives this query, parses it, identifies that the `orders` table is sharded on `user_id` with a `hash` vindex, hashes the value `1001` to produce a keyspace ID, maps that keyspace ID to a shard (say, shard `-80`), and forwards the INSERT to the VTTablet managing that shard's primary MySQL instance. The application never knows which shard received the row — it sees a single logical `orders` table.

Later, the application retrieves all orders for user 1001:

```sql
SELECT * FROM orders WHERE user_id = 1001;
```

Because the WHERE clause includes the sharding key with an equality condition, VTGate routes this entirely to shard `-80`. This is a single-shard query — the fastest path through Vitess and the one you design your schema to maximize.

Now consider a query that does not include the sharding key:

```sql
SELECT COUNT(*) FROM orders WHERE amount > 100.00;
```

VTGate cannot determine which shard(s) might contain matching rows from the WHERE clause alone, so it fans this query out to both shards. Each shard's MySQL instance executes the COUNT locally and returns a partial result. VTGate sums the two counts and returns the total to the application. This scatter-gather pattern is correct but slower than a single-shard query, and its latency grows with the number of shards because VTGate waits for the slowest shard to respond before returning.

The `products` table is declared as `type: reference` — meaning it is small, changes infrequently, and is replicated in full to every shard. When a query joins `orders` to `products`, the join executes locally on whichever shard owns the relevant user's orders, without any cross-shard data movement.

```sql
SELECT o.order_id, p.name, o.amount
FROM orders o
JOIN products p ON o.product_id = p.id
WHERE o.user_id = 1001;
```

This query hits only shard `-80`, joins `orders` and the local copy of `products`, and returns results. The reference table pattern is one of the most effective optimizations in a sharded Vitess deployment — it eliminates cross-shard joins for dimension tables, lookup tables, and other small datasets that are joined frequently but updated rarely.

---

## Online Schema Changes and Resharding

### The VReplication Subsystem

The capability that distinguishes Vitess from a manual sharding scheme is VReplication: a row-streaming subsystem that copies data between shards while the source shards continue to serve live traffic. VReplication is the engine beneath three critical workflows — MoveTables (migrating a table from one keyspace to another), Reshard (splitting or merging shards), and online DDL (schema changes without locking).

VReplication works by establishing a replication stream from source to target, much like MySQL's built-in replication but operating at the row level and filtered through Vitess's query planning. When you initiate a MoveTables or Reshard workflow, Vitess creates a VReplication stream that reads rows from the source shard, transforms them if necessary, and writes them to the target shard. The stream starts by copying existing data in bulk and then switches to continuous change-data-capture mode, tailing the source's binary log to apply ongoing changes to the target. This means the target is always catching up to the source; once the lag is negligible, you can switch traffic over with only a brief moment of read-only state while the final few changes are applied.

### MoveTables: Sharding an Existing Unsharded Keyspace

The most common Vitess migration pattern begins with an unsharded keyspace running on a single MySQL instance behind VTGate. When the instance approaches its scaling limits, you use MoveTables to copy selected tables into a new, sharded keyspace. The workflow proceeds in phases that each have a rollback path:

```text
VITESS MIGRATION STRATEGY
─────────────────────────────────────────────────────────────────

Phase 1: Shadow Vitess (Read-only)
─────────────────────────────────────────────────────────────────
                    ┌─────────────────┐
                    │  Application    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  MySQL Primary  │◀──── All traffic
                    └────────┬────────┘
                             │ replication
                    ┌────────┴────────┐
                    │ Vitess (shadow) │◀──── Replicating
                    │  Unsharded      │      Monitoring
                    └─────────────────┘

Phase 2: VTGate Proxy (All traffic through Vitess)
─────────────────────────────────────────────────────────────────
                    ┌─────────────────┐
                    │  Application    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │    VTGate       │◀──── All traffic
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  MySQL Primary  │
                    │  (single shard) │
                    └─────────────────┘

Phase 3: Horizontal Sharding
─────────────────────────────────────────────────────────────────
                    ┌─────────────────┐
                    │  Application    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │    VTGate       │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
    │  Shard -40  │   │ Shard 40-80 │   │  Shard 80-  │
    └─────────────┘   └─────────────┘   └─────────────┘

Each phase is reversible. Rollback at any point.
```

The MoveTables CLI workflow, using `vtctlclient`, proceeds through these commands:

```bash
# Step 1: Start MoveTables (copies data to Vitess)
vtctlclient MoveTables --source commerce --tables 'users,orders' \
  Create commerce.commerce2vitess

# Step 2: Monitor progress
vtctlclient MoveTables commerce.commerce2vitess Progress

# Step 3: Verify data consistency
vtctlclient MoveTables commerce.commerce2vitess VDiff

# Step 4: Switch reads to Vitess
vtctlclient MoveTables commerce.commerce2vitess SwitchTraffic -- --tablet_types=rdonly,replica

# Step 5: Switch writes to Vitess
vtctlclient MoveTables commerce.commerce2vitess SwitchTraffic -- --tablet_types=primary

# Step 6: Complete migration (drop source tables)
vtctlclient MoveTables commerce.commerce2vitess Complete
```

The VDiff step is not optional. VDiff performs a row-by-row comparison between the source and target, verifying that every row was copied correctly and that no writes were lost during the catch-up phase. Running VDiff after a migration without errors is the signal that the traffic switch is safe. Skipping VDiff and discovering data inconsistencies after switching writes is a production outage that is difficult to unwind, because the writes that went to the target shard with missing or incorrect data cannot be easily replayed onto the source.

### Reshard: Splitting and Merging Shards

Once a keyspace is sharded, you may need to change the number of shards — adding shards to accommodate data growth, or (rarely) merging underutilized shards. Vitess's Reshard workflow uses the same VReplication engine as MoveTables but operates within a single keyspace, moving data from source shards to target shards according to a new sharding scheme:

```bash
# Current: 2 shards (-80, 80-)
# Target: 4 shards (-40, 40-80, 80-c0, c0-)

# Step 1: Create target shards
vtctlclient Reshard --source_shards '-80,80-' \
  --target_shards '-40,40-80,80-c0,c0-' \
  Create commerce.reshard2to4

# Step 2: Monitor copy progress
vtctlclient Reshard commerce.reshard2to4 Progress

# Step 3: Verify data
vtctlclient Reshard commerce.reshard2to4 VDiff

# Step 4: Switch reads
vtctlclient Reshard commerce.reshard2to4 SwitchTraffic -- --tablet_types=rdonly,replica

# Step 5: Switch writes (cutover)
vtctlclient Reshard commerce.reshard2to4 SwitchTraffic -- --tablet_types=primary

# Step 6: Cleanup old shards
vtctlclient Reshard commerce.reshard2to4 Complete
```

The Reshard workflow is designed so that applications continue to read and write throughout the entire process. During the bulk copy phase, VReplication streams existing data to the new shards while new writes continue to land on the old shards and are streamed along with the catch-up. When traffic is switched, there is a brief (sub-second) period where the keyspace is read-only while the final delta is applied, after which writes begin flowing to the new shards. The old shards remain available as a rollback target until the Complete step explicitly removes them.

### Online DDL

Schema changes in a sharded MySQL deployment are operationally painful when done manually: you must apply the ALTER TABLE to every shard, coordinate the changes so that all shards are consistent, and avoid locking tables during the migration. Vitess's online DDL system sends schema change requests through `vtctlclient ApplySchema`, which propagates the change to all shards using a migration strategy (declarative, `online` with `gh-ost`, or `pt-online-schema-change`) that avoids table locking. Because VTGate enforces the VSchema definition, it can also handle the transition period where some shards have the new schema and others do not — for example, by refusing queries that reference a column that does not yet exist on all shards.

---

## Vitess Query Patterns

### Query Types and Performance Characteristics

```text
VITESS QUERY ROUTING
─────────────────────────────────────────────────────────────────

SINGLE-SHARD QUERIES (Fast)
─────────────────────────────────────────────────────────────────
-- Query includes sharding key
SELECT * FROM orders WHERE user_id = 12345;
-- VTGate routes to exactly one shard

-- Insert with sharding key
INSERT INTO orders (user_id, product_id, amount)
VALUES (12345, 100, 99.99);
-- Goes to shard owning user_id 12345

SCATTER QUERIES (Slower, but work)
─────────────────────────────────────────────────────────────────
-- No sharding key - must query all shards
SELECT * FROM orders WHERE status = 'pending';
-- VTGate queries all shards, aggregates results

-- Aggregations across shards
SELECT COUNT(*) FROM orders;
-- VTGate sums counts from each shard

-- ORDER BY with LIMIT (VTGate sorts)
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
-- Each shard returns top 10, VTGate merges and returns final 10

CROSS-SHARD JOINS (Expensive, avoid if possible)
─────────────────────────────────────────────────────────────────
-- Join between sharded tables
SELECT u.name, o.amount
FROM users u JOIN orders o ON u.user_id = o.user_id
WHERE o.status = 'pending';
-- If same sharding key: efficient (single shard)
-- If different keys: cross-shard join (expensive)

REFERENCE TABLES (Replicated everywhere)
─────────────────────────────────────────────────────────────────
-- Small tables (countries, currencies, categories)
-- Copied to all shards for fast local joins
SELECT o.*, p.name as product_name
FROM orders o JOIN products p ON o.product_id = p.id
WHERE o.user_id = 12345;
-- orders sharded by user_id, products is reference table
-- Join happens locally on the shard
```

The performance difference between a single-shard query and a scatter query is not marginal — it is the difference between querying one MySQL instance and querying all of them in parallel and waiting for the slowest. In a cluster with 16 shards, a scatter query that takes 2 milliseconds on each shard still takes at least 2 milliseconds of wall-clock time (assuming the slowest shard responds in 2 ms), but the total work done — and the total I/O and CPU consumed — is 16 times that of a single-shard query. This multiplicative cost means that a workload that is mostly scatter queries will saturate shard resources at a much lower request rate than a workload that is mostly single-shard queries, even if the per-query latency is acceptable. Designing for Vitess therefore means designing for single-shard queries as the common case and treating scatter queries as a necessary but expensive fallback.

### Designing Your Schema for Vitess

The principle that makes Vitess performant is **co-location**: rows that are queried together should live on the same shard. This is achieved by sharding related tables on the same key, so that joins between them are local operations. If `users` and `orders` are both sharded on `user_id`, a query that fetches a user and all their orders hits exactly one shard. If `orders` were sharded on `order_id` instead, a `SELECT * FROM orders WHERE user_id = 1001` would scatter across all shards because no single shard can claim to own all of user 1001's orders — they are distributed by `order_id` hash.

```sql
-- GOOD: Co-located data (same sharding key)
-- users and orders both sharded by user_id
-- Queries for a user hit single shard

CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255)
);

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT,  -- Sharding key
    product_id BIGINT,
    amount DECIMAL(10,2),
    created_at TIMESTAMP,
    INDEX (user_id)
);

-- BAD: Orphaned data (no sharding key relationship)
-- Leads to scatter queries everywhere

CREATE TABLE audit_logs (
    log_id BIGINT PRIMARY KEY,
    entity_type VARCHAR(50),  -- 'user', 'order', 'product'
    entity_id BIGINT,          -- Could be any ID
    action VARCHAR(50),
    created_at TIMESTAMP
);
-- No clear sharding key - every query is a scatter
```

The `audit_logs` example illustrates a pattern that works fine on a single MySQL instance but becomes toxic in a sharded deployment. Because `entity_id` can refer to any entity type, there is no single column you can shard on that would co-locate all audit log entries related to a given piece of data. A common solution is to shard `audit_logs` by `entity_type` (so all user-related entries are together) and accept that cross-type queries will scatter, or to use a time-based sharding key and treat audit logs as an append-only dataset that is queried by time range rather than by entity.

---

## Vitess on Kubernetes

### The Vitess Operator

The recommended way to run Vitess on Kubernetes is the Vitess Operator, maintained in the `planetscale/vitess-operator` repository. The operator manages the full lifecycle of a Vitess cluster: it creates the StatefulSets and Deployments for VTGate, VTTablet, VTOrc, and the MySQL instances; it configures the topology service (etcd by default); it handles rolling updates when images or configuration change; and it exposes the cluster through Kubernetes Services so that applications can reach VTGate via a stable DNS name.

```bash
# Install the Vitess Operator
kubectl apply -f https://raw.githubusercontent.com/planetscale/vitess-operator/v2.17.0/deploy/operator.yaml

# Wait for operator to be ready
kubectl wait --for=condition=Available deployment/vitess-operator \
  -n vitess-operator-system --timeout=120s
```

A VitessCluster custom resource defines the entire cluster topology declaratively. The operator reconciles this specification against the running state, creating or updating resources as needed. This is the same pattern as any Kubernetes operator — you describe the desired state in a CR, and the operator makes it so.

### Creating a Vitess Cluster

```yaml
# vitess-cluster.yaml
apiVersion: planetscale.com/v2
kind: VitessCluster
metadata:
  name: my-vitess
spec:
  images:
    vtctld: vitess/lite:v21.0.0
    vtgate: vitess/lite:v21.0.0
    vttablet: vitess/lite:v21.0.0
    vtbackup: vitess/lite:v21.0.0
    mysqld:
      mysql80Compatible: vitess/lite:v21.0.0

  cells:
    - name: zone1
      gateway:
        replicas: 2
        resources:
          requests:
            cpu: 500m
            memory: 512Mi

  keyspaces:
    - name: commerce
      turndownPolicy: Immediate
      partitionings:
        - equal:
            parts: 2
            shardTemplate:
              databaseInitScriptSecret:
                name: commerce-schema
                key: schema.sql
              tabletPools:
                - cell: zone1
                  type: replica
                  replicas: 3
                  vttablet:
                    resources:
                      requests:
                        cpu: 500m
                        memory: 512Mi
                  mysqld:
                    resources:
                      requests:
                        cpu: 500m
                        memory: 1Gi
                  dataVolumeClaimTemplate:
                    accessModes: ["ReadWriteOnce"]
                    resources:
                      requests:
                        storage: 50Gi

  updateStrategy:
    type: Immediate

  vitessDashboard:
    cells: ["zone1"]
    replicas: 1

  etcd:
    createEtcd: true
    etcdVersion: "3.5.7"
```

```bash
# Create schema secret
kubectl create secret generic commerce-schema \
  --from-file=schema.sql=./schema.sql

# Deploy the cluster
kubectl apply -f vitess-cluster.yaml

# Watch pods come up
kubectl get pods -w
```

### Verify Installation

```bash
# Check cluster status
kubectl get vitessclusters

# Port-forward to VTGate
kubectl port-forward svc/my-vitess-vtgate-zone1 3306:3306

# Connect with mysql client
mysql -h 127.0.0.1 -P 3306 -u user

# Check shards
mysql> SHOW VITESS_SHARDS;
+----------------+
| Shards         |
+----------------+
| commerce/-80   |
| commerce/80-   |
+----------------+
```

The key operational insight for running Vitess on Kubernetes is that each MySQL instance is a StatefulSet pod with its own PersistentVolumeClaim. Vitess's built-in backup system, `vtbackup`, can populate a new PVC from an existing backup so that a new shard or a replacement pod starts with data rather than replicating from scratch. The operator handles this lifecycle, but the operator's own understanding of the underlying storage class, backup location, and restore performance is essential for planning recovery time objectives. The operator also manages the topology service deployment when `createEtcd: true` is set in the VitessCluster spec, provisioning etcd as a separate StatefulSet and wiring VTGate and VTTablet instances to discover shard topology through it. For production deployments, most teams run the topology service externally — outside the VitessCluster CR — so that etcd survives cluster deletion events, and they configure the operator with an existing etcd endpoint rather than letting the operator create one.

---

## Patterns and Anti-Patterns

### Patterns

1. **Start unsharded, shard later.** Deploy Vitess in front of your existing MySQL instance with a single unsharded keyspace. This gives you the serving topology, connection pooling, monitoring, and operational tooling without the complexity of data distribution. When scaling demands it — and only then — use MoveTables to shard the keyspace. Starting sharded before you understand your query patterns risks locking in a sharding key that does not match your real access patterns.

2. **Shard on the column that dominates your WHERE clauses.** Profile your production query workload before choosing a sharding key. The column that appears in the most equality-filter WHERE clauses, and that naturally groups related rows, is the best candidate. For a multi-tenant system, `tenant_id` is almost always correct. For a user-centric system, `user_id` usually is. For an append-only time-series system, a composite key on `(tenant_id, time_bucket)` may be optimal.

3. **Use reference tables for small, slowly-changing dimension data.** Tables like countries, currencies, product categories, and configuration lookups should be declared as reference tables in the VSchema. Vitess copies them to every shard, so joins between sharded tables and reference tables execute locally without cross-shard overhead. The constraint is that reference tables must be small — copying a multi-gigabyte table to every shard defeats the purpose of sharding.

4. **Always run VDiff before switching traffic.** The VDiff step in a MoveTables or Reshard workflow verifies row-level consistency between source and target. Skipping it is gambling that the VReplication stream is perfect. Production incidents caused by unverified migrations are painful to unwind; spending the few minutes to run VDiff is insurance against data corruption.

### Anti-Patterns

1. **Sharding by a column that is never used in WHERE clauses.** If your primary vindex is on `id` (an auto-increment primary key) and all your application queries filter by `user_id`, every query becomes a scatter because Vitess cannot route on `id` when the query does not include it. The primary vindex must match your access patterns, not your table's internal key structure.

2. **Running frequent scatter queries as a core access pattern.** A query like `SELECT * FROM orders WHERE status = 'pending'` that runs every second on a 16-shard cluster consumes 16 times the resources of the same query on a single instance. If scatter queries make up a significant fraction of your workload, either the sharding key was chosen poorly or the query pattern cannot be sharded — in which case Vitess may not be the right tool.

3. **Using cross-shard transactions for business logic.** Vitess supports distributed transactions via two-phase commit, but they are dramatically slower than single-shard transactions and introduce partial-failure modes that single-shard transactions do not have. Design your data model so that each logical unit of work — creating an order, updating a user profile, processing a payment — touches rows that share a sharding key and therefore lives on a single shard.

4. **Treating the topology service as optional or low-priority infrastructure.** An under-provisioned etcd cluster that loses quorum freezes the Vitess cluster. The topology service should be deployed with the same availability guarantees as the database itself: at least three nodes spread across failure domains, with sufficient CPU and disk I/O to handle the write load from VTTablet health updates and VTGate topology watches.

5. **Using the wrong vindex type for the access pattern.** A `hash` vindex distributes rows uniformly but makes range scans scatter. A `numeric` vindex preserves ordering but can create hot shards if the sharding key distribution is skewed (e.g., all new rows land on the highest-numbered shard). A `lookup` vindex adds a round trip on every write and on queries that use the secondary key. Choose the vindex type that matches the query pattern, not the one that is simplest to configure.

---

## Decision Framework

Use this decision tree to evaluate Vitess against the alternatives. Start from the root and follow the path that matches your context.

```text
START: "My relational database needs to scale beyond a single server."
│
├─ Is your existing application tightly coupled to MySQL?
│  ├─ YES → Can you tolerate the operational complexity of managing
│  │         shards yourself?
│  │       ├─ YES → Vitess (MySQL-proxy sharding) OR
│  │       │         PlanetScale (managed Vitess)
│  │       └─ NO  → Evaluate a rewrite to CockroachDB (PostgreSQL-
│  │                 wire-compatible, built-in sharding) or
│  │                 Spanner (fully managed, SQL, no shard ops)
│  │
│  └─ NO  → Is your workload write-heavy with geographically
│            distributed users?
│           ├─ YES → CockroachDB (serializable cross-region
│           │         transactions) OR Spanner (managed global)
│           └─ NO  → Is your data model naturally shardable by
│                     a single key?
│                    ├─ YES → Vitess OR Citus (if Postgres)
│                    └─ NO  → CockroachDB (no sharding-key
│                              constraint; automatic distribution)
```

This framework focuses on the durable decision factors — MySQL coupling, operational appetite, data-model shardability — rather than on version-specific features or pricing. The tool choice follows from the constraints; the constraints do not change with vendor roadmaps.

---

## Landscape Rosetta

Rows are durable capabilities; columns are tools/peers compared on those capabilities. No ranking implied — every tool is the right choice for some context and the wrong choice for others.

| Capability | Vitess | Citus (Postgres) | CockroachDB | Spanner | PlanetScale |
|---|---|---|---|---|---|
| **Horizontal sharding** | Hash/range/lookup vindexes, user-defined | Hash/range distribution key on table creation | Automatic range-based, no user shard-key choice | Automatic split-based, no user shard-key choice | Same as Vitess (managed) |
| **MySQL protocol** | Native MySQL wire protocol on VTGate | PostgreSQL wire protocol only (fork of PG) | PostgreSQL wire protocol | gRPC + Cloud Spanner API (not MySQL) | Native MySQL wire protocol (managed VTGate) |
| **Online resharding** | VReplication-based, zero-downtime Reshard/MoveTables | Shard rebalancer (less mature than Vitess) | Automatic rebalancing, no user workflow | Fully automatic, no user workflow | Same as Vitess (managed) |
| **K8s-native deployment** | Vitess Operator (CRD-based) | Citus operator or CloudNativePG + Citus extension | CockroachDB Operator (CRD-based) | Not self-hosted (GCP managed only) | Fully managed, no self-hosted option |
| **Managed option** | PlanetScale (separate company, built on Vitess) | Azure Cosmos DB for PostgreSQL (Citus mode) | CockroachDB Cloud (SaaS) | Cloud Spanner (GCP only) | PlanetScale (the only option; no self-hosted Vitess from PlanetScale) |
| **CNCF maturity** | Graduated (2019) | Not a CNCF project | Not a CNCF project | Not a CNCF project | Not a CNCF project (PlanetScale is a company, not a CNCF project) |
| **Transaction isolation** | READ-COMMITTED (MySQL default), 2PC for cross-shard | READ-COMMITTED (Postgres default), 2PC for cross-shard | Serializable by default (strongest) | Serializable by default (strongest) | Same as Vitess |
| **SQL dialect** | MySQL (with Vitess-specific extensions) | PostgreSQL (with Citus-specific extensions) | PostgreSQL (with some limitations) | GoogleSQL or PostgreSQL interface | MySQL |

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.** The Rosetta above reflects the state of each project at the time of writing. CockroachDB and Spanner offer stronger consistency guarantees (serializable isolation) at the cost of higher write latency and the inability to run MySQL-native queries. Citus and Vitess both wrap existing relational engines (Postgres and MySQL respectively) with sharding layers, giving you the full SQL dialect of the underlying engine but requiring you to design for the sharding key. PlanetScale is Vitess as a managed service — it removes the operational burden of running the Vitess control plane but also removes the ability to self-host. The CNCF maturity column is relevant only for governance and community health assessment, not for technical capability comparison; a tool not being a CNCF project is not a technical disadvantage.

---

## Did You Know?

- **Vitess was built at YouTube** in 2010-2011 to solve MySQL scaling as video upload volume grew past what a single server could handle. The core architecture — a stateless query-routing proxy that speaks the MySQL protocol, backed by a topology service for shard discovery — was shaped by the constraint that YouTube could not afford a multi-year application rewrite.

- **VTGate can pool thousands of connections** from hundreds of application instances into a much smaller number of connections to each MySQL shard. This connection multiplexing is essential at scale because MySQL's thread-per-connection model means that every connection consumes memory; without VTGate pooling, a fleet of 500 application pods each holding 50 connections would open 25,000 connections — enough to overwhelm a single MySQL instance.

- **Reference tables are atomically updated** during schema changes. When you alter a reference table, Vitess applies the change to every shard and ensures that all shards see the new schema before any query uses it, avoiding the inconsistency window where some shards have the new column and others do not.

- **The Vitess query planner can rewrite queries** to make them shard-safe. For example, `SELECT * FROM users LIMIT 10` becomes a scatter-gather with a merge step, but `SELECT * FROM users WHERE user_id IN (1, 2, 3)` is decomposed into individual single-shard lookups and merged efficiently. Use `VExplain` to see how Vitess plans to execute a given query before running it in production.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Choosing a sharding key without profiling query patterns | Scatter queries dominate the workload, throughput degrades with shard count | Profile production queries for 1-2 weeks, identify the column in most WHERE clauses, and shard on that column |
| Ignoring scatter query performance | Scatter queries that are fast on 2 shards become slow on 16; resource consumption multiplies | Monitor scatter query rate and latency per shard; design schema so scatter queries are the exception, not the norm |
| Using cross-shard transactions for core write paths | Two-phase commit doubles latency and introduces partial-failure modes | Co-locate all rows touched by a single logical unit of work on the same shard key |
| Making a reference table too large | Copying a 5 GB table to 16 shards wastes 80 GB of storage and slows schema changes | Only reference tables under a few hundred MB; larger dimension tables should be sharded or accessed via a service |
| Running without VTGate connection pooling | Every application instance opens connections directly to VTTablets, eventually exhausting MySQL connection limits | Point all application connections at VTGate and let it pool to the underlying MySQL instances |
| Skipping VDiff before traffic switch | Uncaught replication gaps cause data inconsistencies that are hard to unwind after writes are switched | Always run VDiff as the final gate before SwitchTraffic; never skip it to save time |
| Under-provisioning the topology service | etcd quorum loss freezes all Vitess operations; topology writes are steady and not bursty | At least 3 etcd nodes across failure domains; monitor etcd disk latency and leader election frequency |
| Deploying Vitess without understanding the chosen vindex's tradeoffs | A hash vindex chosen for simplicity makes range queries scatter; a lookup vindex adds write overhead | Understand the read and write patterns of each table before choosing its vindex type |

---

## Quiz

### Question 1
VTGate is the component every application connects to, yet it stores no data itself. Understanding its role — parsing MySQL-protocol queries, mapping them to shards via the VSchema, and aggregating results from distributed MySQL instances — is the foundation for reasoning about Vitess query performance and cluster architecture. What is VTGate's specific role in a Vitess cluster?

<details>
<summary>Answer</summary>

**VTGate is the stateless, MySQL-protocol-compatible query-routing proxy that serves as the entry point for all application traffic.** It parses incoming SQL queries, consults the VSchema to determine which shard or shards must execute the query, forwards single-shard queries to the correct VTTablet, fans out scatter queries to all relevant shards and merges the results, and pools connections so that thousands of application connections are multiplexed into a manageable number of connections to each MySQL instance. VTGate is horizontally scalable — you add more VTGate instances behind a load balancer to increase query throughput, and each instance independently reads shard topology from the topology service.

</details>

### Question 2
The sharding key is the most consequential design decision in any Vitess deployment, because it determines which queries are fast single-shard lookups and which are expensive scatter operations — and changing it later requires a full online reshard that moves every row in the keyspace. What determines which shard a row lives on, and what are the consequences of a poor choice?

<details>
<summary>Answer</summary>

**The primary vindex — the sharding key column and its hash or lookup function — determines which shard owns every row in a sharded table.** When you insert a row, Vitess hashes (or looks up) the sharding key value to produce a keyspace ID, then maps that keyspace ID to exactly one shard. The consequence of a poor choice is that your most frequent queries become scatter queries: if your application always filters by `user_id` but you sharded by `order_id`, every user-focused query fans out to all shards, multiplying resource consumption and latency by the shard count. Changing the primary vindex requires a full online reshard, which is supported but is a major cluster operation.

</details>

### Question 3
Every distributed query engine has a fast path and a slow path. In Vitess, the fast path is a single-shard query that hits exactly one MySQL instance; the slow path is a scatter query that fans out to every shard and merges results. Recognizing which queries scatter and why is essential for designing a Vitess schema that stays fast as shard count grows. What is a scatter query, and why is it expensive at scale?

<details>
<summary>Answer</summary>

**A scatter query is any query that cannot be routed to a single shard because its WHERE clause does not include the sharding key with an equality condition.** VTGate must send the query to every shard in the keyspace, collect the partial results, and merge them. The expense is multiplicative: a scatter query on a 16-shard cluster consumes roughly 16 times the CPU and I/O of a single-shard query, because every shard's MySQL instance executes the query independently. Latency is bounded by the slowest shard's response, and aggregate resource consumption rises linearly with shard count. Designing a Vitess schema means maximizing the fraction of queries that are single-shard and treating scatter queries as a necessary but limited fallback.

</details>

### Question 4
Not every table in a Vitess keyspace needs to be sharded. Small dimension tables — countries, currencies, product categories — can be designated as reference tables and replicated in full to every shard, enabling local joins without cross-shard data movement. The tradeoff is storage amplification multiplied by shard count. What distinguishes a reference table from a sharded table in Vitess, and when should you use one?

<details>
<summary>Answer</summary>

**A reference table is replicated in full to every shard in the keyspace, while a sharded table's rows are partitioned across shards by the primary vindex.** Reference tables are appropriate for small, slowly-changing dimension data — lookup tables like countries, currencies, product categories, and configuration values — that are joined frequently with sharded tables. Because a copy of the reference table exists on every shard, joins between a sharded table and a reference table execute locally on the shard that owns the relevant rows, with no cross-shard data movement. The constraint is size: a reference table that is hundreds of megabytes or larger wastes significant storage (size × shard count) and slows schema changes that must be applied to every shard's copy.

</details>

### Question 5
Online resharding — splitting or merging shards while the database continues to serve live traffic — is one of Vitess's most operationally significant capabilities, because it means you are not locked into an initial shard count or sharding key choice forever. The mechanism that makes this possible is VReplication, Vitess's change-data-capture and bulk-copy subsystem. How does Vitess perform online resharding without application downtime?

<details>
<summary>Answer</summary>

**Vitess uses the VReplication subsystem to stream rows from source shards to target shards while live traffic continues to be served.** The workflow proceeds in phases: first, Vitess creates the new target shards and starts VReplication streams that copy existing data in bulk, then switch to continuous change-data-capture mode, tailing the source's binary log to apply ongoing writes to the target. When the replication lag approaches zero, the operator runs VDiff to verify row-level consistency, then switches read traffic to the new shards, and finally switches write traffic — during which there is a brief (sub-second) read-only window while the final delta is applied. The old shards remain available as a rollback target until the Complete step explicitly removes them. Throughout the entire process, applications read and write through VTGate as normal.

</details>

### Question 6
Choosing a sharding key is an exercise in understanding your application's access patterns. The column that appears most often in WHERE clauses, that groups related entities together naturally, and that aligns with your join patterns is the right candidate — and in a multi-tenant or user-facing application, the user or tenant identifier is almost always that column. Consider a concrete e-commerce schema: why would you shard by `user_id` rather than by a synthetic `order_id`?

<details>
<summary>Answer</summary>

**Sharding by `user_id` co-locates all of one user's data on a single shard, making the most common access patterns — "get all orders for user X," "get user profile," and joins between users and their orders — into single-shard queries.** If you shard by `order_id` instead, each order is distributed independently based on its ID hash, so a user's 50 orders might be spread across 50 shards (if the cluster is large enough). Every query that retrieves data by user becomes a scatter query across all shards, multiplying resource consumption and latency. The principle is to choose the sharding key that makes your most frequent queries single-shard. For an e-commerce system where most queries are user-scoped, `user_id` is the natural choice.

</details>

### Question 7
Data migrations are the highest-risk operations in any database system because a mistake can cause permanent data loss that is difficult to detect until queries return wrong results. Vitess provides VDiff as a mandatory safety gate — a row-level integrity check that compares every row on the source and target before traffic is switched. What does VDiff verify, and why is running it mandatory before switching traffic?

<details>
<summary>Answer</summary>

**VDiff performs a row-by-row comparison between the source and target of a VReplication workflow (MoveTables or Reshard) to verify that every row was copied correctly and that no writes were lost during the catch-up phase.** It is mandatory because VReplication can encounter transient errors, binary log parsing issues, or network interruptions that cause silent data gaps — the stream continues to run, but some rows are missing on the target. Running VDiff is the final integrity check before traffic is switched; a clean VDiff result is the signal that the migration can proceed safely. Skipping VDiff and discovering data inconsistencies after writes have been switched to the target is a hard problem to unwind, because the writes that went to the target with missing data cannot be easily replayed onto the source.

</details>

### Question 8
Vitess is not the only way to scale a relational database horizontally — CockroachDB, Citus for Postgres, and Google Cloud Spanner all address the same problem with different architectural tradeoffs. Understanding when Vitess's MySQL-transparency and explicit sharding model is the right fit, versus when a system that distributes data automatically with stronger transactional guarantees is a better choice, is essential for making a durable architectural decision. What conditions would lead you to choose CockroachDB over Vitess for a scale-out relational workload?

<details>
<summary>Answer</summary>

**Choose CockroachDB over Vitess when you are not tightly coupled to MySQL, when your data model does not have a natural sharding key that dominates your query patterns, or when you need serializable cross-shard transactions without designing around shard boundaries.** CockroachDB automatically distributes data across nodes without requiring the user to choose a sharding key — the system handles range splits, rebalancing, and failure recovery internally. Its serializable isolation by default means that cross-row transactions are safe without the restrictions that Vitess's two-phase commit imposes. The tradeoffs are that CockroachDB speaks the PostgreSQL wire protocol (not MySQL), has higher per-operation latency due to its consensus-based replication, and is not a drop-in replacement for an existing MySQL application — it requires a migration, whereas Vitess can wrap your existing MySQL deployment transparently.

</details>

---

## Hands-On Exercise

### Task: Deploy Vitess and Shard a Table

**Objective**: Deploy a minimal Vitess cluster on Kubernetes, create a sharded keyspace, define a VSchema, and verify that queries route correctly based on the sharding key.

**Success Criteria**:
- [ ] Vitess cluster running on Kubernetes with VTGate accessible
- [ ] A sharded `commerce` keyspace with 2 shards, users and orders tables sharded on `user_id` with a hash vindex
- [ ] Inserted rows are distributed across shards as verified by `SHOW VITESS_SHARDS`
- [ ] Single-shard queries (`WHERE user_id = N`) return correct results from the correct shard
- [ ] Scatter queries (`SELECT COUNT(*)`) aggregate across both shards correctly

### Steps

```bash
# 1. Install the Vitess operator
kubectl apply -f https://raw.githubusercontent.com/planetscale/vitess-operator/v2.17.0/deploy/operator.yaml

kubectl wait --for=condition=Available deployment/vitess-operator \
  -n vitess-operator-system --timeout=120s

# 2. Create schema file
cat > /tmp/schema.sql << 'EOF'
CREATE TABLE users (
    user_id BIGINT NOT NULL,
    name VARCHAR(100),
    email VARCHAR(255),
    PRIMARY KEY (user_id)
);

CREATE TABLE orders (
    order_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id),
    INDEX idx_user (user_id)
);
EOF

kubectl create secret generic commerce-schema --from-file=schema.sql=/tmp/schema.sql

# 3. Create minimal Vitess cluster
cat > vitess-lab.yaml << 'EOF'
apiVersion: planetscale.com/v2
kind: VitessCluster
metadata:
  name: vitess-lab
spec:
  images:
    vtctld: vitess/lite:v21.0.0
    vtgate: vitess/lite:v21.0.0
    vttablet: vitess/lite:v21.0.0
    mysqld:
      mysql80Compatible: vitess/lite:v21.0.0

  cells:
    - name: zone1
      gateway:
        replicas: 1
        resources:
          requests:
            cpu: 100m
            memory: 256Mi

  keyspaces:
    - name: commerce
      turndownPolicy: Immediate
      partitionings:
        - equal:
            parts: 2  # 2 shards
            shardTemplate:
              databaseInitScriptSecret:
                name: commerce-schema
                key: schema.sql
              tabletPools:
                - cell: zone1
                  type: replica
                  replicas: 1
                  vttablet:
                    resources:
                      requests:
                        cpu: 100m
                        memory: 256Mi
                  mysqld:
                    resources:
                      requests:
                        cpu: 100m
                        memory: 512Mi
                  dataVolumeClaimTemplate:
                    accessModes: ["ReadWriteOnce"]
                    resources:
                      requests:
                        storage: 5Gi

  etcd:
    createEtcd: true
    etcdVersion: "3.5.7"
    resources:
      requests:
        cpu: 100m
        memory: 256Mi

  vitessDashboard:
    cells: ["zone1"]
    replicas: 1
EOF

kubectl apply -f vitess-lab.yaml

# 4. Wait for cluster to be ready (this takes a few minutes)
echo "Waiting for Vitess cluster to be ready..."
sleep 120  # Vitess takes time to initialize

kubectl get pods

# 5. Create VSchema for sharding
cat > vschema.json << 'EOF'
{
  "sharded": true,
  "vindexes": {
    "hash": {
      "type": "hash"
    }
  },
  "tables": {
    "users": {
      "column_vindexes": [
        {
          "column": "user_id",
          "name": "hash"
        }
      ]
    },
    "orders": {
      "column_vindexes": [
        {
          "column": "user_id",
          "name": "hash"
        }
      ]
    }
  }
}
EOF

# Apply VSchema (requires vtctld access)
kubectl port-forward svc/vitess-lab-vtctld 15999:15999 &
sleep 5

# 6. Port-forward to VTGate and test
kubectl port-forward svc/vitess-lab-vtgate-zone1 3306:3306 &
sleep 5

# 7. Insert test data
mysql -h 127.0.0.1 -P 3306 << 'EOF'
USE commerce;

-- Insert users (will be distributed across shards)
INSERT INTO users (user_id, name, email) VALUES
    (1, 'Alice', 'alice@example.com'),
    (2, 'Bob', 'bob@example.com'),
    (100, 'Charlie', 'charlie@example.com'),
    (200, 'Diana', 'diana@example.com');

-- Insert orders
INSERT INTO orders (order_id, user_id, amount) VALUES
    (1001, 1, 99.99),
    (1002, 1, 49.99),
    (1003, 2, 149.99),
    (1004, 100, 199.99);

SELECT * FROM users;
SELECT * FROM orders;
EOF

# 8. Verify sharding - show which shard each row is on
mysql -h 127.0.0.1 -P 3306 -e "SHOW VITESS_SHARDS"

# 9. Test single-shard query (fast)
mysql -h 127.0.0.1 -P 3306 -e "SELECT * FROM commerce.users WHERE user_id = 1"

# 10. Test scatter query (all shards)
mysql -h 127.0.0.1 -P 3306 -e "SELECT COUNT(*) FROM commerce.users"

# Clean up
kubectl delete vitesscluster vitess-lab
kubectl delete secret commerce-schema
```

---

## Sources

- [Vitess Documentation](https://vitess.io/docs/) — Official Vitess documentation covering architecture, sharding, VSchema, VTGate, VTTablet, VReplication, and Vitess Operator usage.
- [Vitess GitHub Repository](https://github.com/vitessio/vitess) — Primary upstream repository with source code, release notes, and contribution guide for the Vitess database clustering system.
- [CNCF Vitess Project Page](https://www.cncf.io/projects/vitess/) — Project status, maturity level (Graduated), community statistics, and adoption case studies maintained by the CNCF.
- [CNCF Vitess Graduation Announcement](https://www.cncf.io/announcements/2019/11/05/cloud-native-computing-foundation-announces-vitess-graduation/) — Official CNCF press release confirming Vitess graduated on November 5, 2019, alongside the adoption metrics and endorser statements supporting the graduation decision.
- [Vitess Operator for Kubernetes](https://github.com/planetscale/vitess-operator) — Kubernetes operator for deploying and managing Vitess clusters using custom resources, maintained by PlanetScale.
- [Vitess Sharding Concepts](https://vitess.io/docs/24.0/reference/features/sharding/) — Official overview of Vitess sharding primitives: keyspaces, shards, vindexes, and the relationship between sharding keys and query routing.
- [Vitess VTGate Reference](https://vitess.io/docs/24.0/concepts/vtgate/) — Reference documentation for VTGate, covering query routing, connection pooling, scatter-gather logic, and the MySQL protocol implementation.
- [Vitess Operator User Guide](https://vitess.io/docs/24.0/get-started/operator/) — Step-by-step guide for deploying Vitess clusters using the Vitess Operator on Kubernetes, including keyspace and cell configuration.
- [Slack Engineering: Scaling Datastores with Vitess](https://slack.engineering/scaling-datastores-at-slack-with-vitess/) — Engineering blog post describing Slack's migration from a single MySQL cluster to a sharded Vitess deployment, including the sharding key selection, phased traffic migration, and noisy-neighbor isolation gained.
- [PlanetScale Documentation](https://planetscale.com/docs) — Managed Vitess platform documentation covering database branching, query insights, and operational workflows built on Vitess.
- [CockroachDB Documentation](https://cockroachlabs.com/docs/stable/) — Official CockroachDB documentation covering its distributed SQL engine, automatic sharding, serializable transactions, and Kubernetes operator.
- [Citus Data Documentation](https://docs.citusdata.com/) — Official Citus documentation for the Postgres extension that provides distributed tables, reference tables, and a shard rebalancer for horizontal scaling of Postgres.
- [Cloud Spanner Documentation](https://cloud.google.com/spanner/docs) — Google Cloud Spanner documentation covering its globally distributed, strongly consistent SQL database with automatic sharding and no operational shard management.

---

## Next Module

Continue to [Module 15.5: etcd-operator](../module-15.5-etcd-operator/) — the final module in this toolkit — to manage etcd clusters that back Kubernetes and other distributed control planes.

- **Related**: [Module 15.3: PlanetScale](../module-15.3-serverless-databases/) — Managed Vitess experience
- **Related**: [Distributed Systems Foundation](/platform/foundations/distributed-systems/) — Sharding theory and CAP theorem foundations
- **Related**: [Observability Toolkit](/platform/toolkits/observability-intelligence/observability/) — Monitoring Vitess clusters with Prometheus and Grafana

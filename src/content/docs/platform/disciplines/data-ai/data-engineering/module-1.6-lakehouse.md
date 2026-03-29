---
title: "Module 1.6: Building a Data Lakehouse on Kubernetes"
slug: platform/disciplines/data-ai/data-engineering/module-1.6-lakehouse
sidebar:
  order: 7
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 3.5 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.2 — Apache Kafka on Kubernetes](../module-1.2-kafka/) — Understanding event streaming and data pipelines
- **Required**: [Module 1.4 — Batch Processing & Apache Spark on K8s](../module-1.4-spark/) — Spark fundamentals and the Spark Operator
- **Recommended**: SQL proficiency (joins, window functions, CTEs, partitioning)
- **Recommended**: Familiarity with S3/object storage concepts (buckets, prefixes, object lifecycle)

---

## Why This Module Matters

For 30 years, the data world has been split into two camps.

**Data lakes** store everything cheaply in open formats on object storage — Parquet, JSON, CSV — but struggle with consistency, transactions, and performance at query time. You can dump petabytes into S3 for pennies per gigabyte, but querying it feels like searching a library where the books are shelved randomly and some have missing pages.

**Data warehouses** (Snowflake, BigQuery, Redshift) offer blazing-fast SQL queries, ACID transactions, and schema enforcement — but they are expensive, proprietary, and force you to load data into their walled garden before you can query it.

The **data lakehouse** is the third option: the reliability and performance of a warehouse, built on the openness and cost of a lake. It achieves this through **open table formats** (Apache Iceberg, Delta Lake, Apache Hudi) that add transaction logs, schema evolution, and time travel on top of plain Parquet files in object storage.

On Kubernetes, you can build a complete lakehouse with open-source components: object storage for data, Iceberg or Delta Lake for table management, Hive Metastore for metadata, and Trino or Spark for SQL queries. No vendor lock-in. No per-query pricing. Full control.

This module teaches you every layer of the lakehouse stack and how to deploy it on Kubernetes.

---

## Did You Know?

- **Netflix was one of the earliest adopters of the lakehouse pattern.** Before the term existed, Netflix built Apache Iceberg internally to manage their petabyte-scale data on S3. They open-sourced it in 2018, and it became an Apache top-level project in 2020.
- **The cost difference between a lakehouse and a traditional warehouse is staggering.** Storing 1 PB in Snowflake costs approximately $23,000/month in storage alone. Storing the same data in S3 with Iceberg tables costs about $750/month. The query engines (Trino, Spark) run only when you need them.
- **Iceberg's hidden partition feature eliminates a class of query errors entirely.** Unlike Hive-style partitioning where users must know the partition scheme to write efficient queries, Iceberg automatically prunes partitions based on filter predicates — no partition column in the WHERE clause needed.

---

## Data Lake vs Data Warehouse vs Data Lakehouse

### The Evolution

```
ERA 1 (2000s): Data Warehouse
┌─────────────────────────────────────────┐
│  Structured data only                   │
│  Expensive proprietary storage          │
│  ACID transactions  ✓                   │
│  Schema enforcement ✓                   │
│  Fast SQL queries   ✓                   │
│  Open formats       ✗                   │
│  Cheap storage      ✗                   │
│  All data types     ✗                   │
└─────────────────────────────────────────┘

ERA 2 (2010s): Data Lake (Hadoop/S3)
┌─────────────────────────────────────────┐
│  All data types (structured + raw)      │
│  Cheap object storage                   │
│  ACID transactions  ✗  ← "data swamp"  │
│  Schema enforcement ✗                   │
│  Fast SQL queries   ✗                   │
│  Open formats       ✓                   │
│  Cheap storage      ✓                   │
│  All data types     ✓                   │
└─────────────────────────────────────────┘

ERA 3 (2020s): Data Lakehouse
┌─────────────────────────────────────────┐
│  Best of both worlds                    │
│  Open table formats on object storage   │
│  ACID transactions  ✓                   │
│  Schema enforcement ✓                   │
│  Fast SQL queries   ✓                   │
│  Open formats       ✓                   │
│  Cheap storage      ✓                   │
│  All data types     ✓                   │
└─────────────────────────────────────────┘
```

### What Makes a Lakehouse Work

The secret sauce is the **table format layer** that sits between the query engine and the raw files:

```
┌──────────────────────────────────────────────────┐
│               QUERY ENGINES                      │
│   Trino    Spark    Flink    Presto    Dremio    │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│             TABLE FORMAT                         │
│   Apache Iceberg  │  Delta Lake  │  Apache Hudi  │
│                                                  │
│   • Transaction log (ACID)                       │
│   • Schema evolution                             │
│   • Time travel                                  │
│   • Partition evolution                          │
│   • Metadata management                          │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│             FILE FORMATS                         │
│   Apache Parquet  │  Apache ORC  │  Apache Avro  │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│             OBJECT STORAGE                       │
│   Amazon S3  │  MinIO  │  GCS  │  Azure Blob    │
└──────────────────────────────────────────────────┘
```

Each layer is independent and interchangeable. You can switch from Trino to Spark without changing your data. You can move from S3 to GCS without changing your table format. This is the power of open standards.

---

## Open Table Formats: The Core Innovation

### Apache Iceberg

Iceberg is the most widely adopted open table format. Originally developed at Netflix, it is now used by Apple, LinkedIn, Airbnb, and hundreds of other organizations.

**How Iceberg works:**

```
Traditional Hive table:
  /data/events/year=2026/month=03/day=24/*.parquet
  (Just files in directories. No transactions. No schema history.)

Iceberg table:
  /warehouse/events/
  ├── metadata/
  │   ├── v1.metadata.json      ← Table schema, partition spec, snapshot list
  │   ├── v2.metadata.json      ← Updated after each write operation
  │   ├── snap-1234.avro        ← Manifest list: which manifests belong to snapshot
  │   └── manifest-5678.avro    ← Manifest: which data files, their stats
  └── data/
      ├── 00001-abc.parquet     ← Actual data files
      ├── 00002-def.parquet
      └── 00003-ghi.parquet
```

The **metadata layer** is what gives Iceberg its powers:

| Feature | How It Works | Why It Matters |
|---------|-------------|---------------|
| **ACID transactions** | Atomic swap of metadata pointers | Concurrent readers never see partial writes |
| **Schema evolution** | Schema stored in metadata, not file names | Add/rename/drop columns without rewriting data |
| **Time travel** | Each transaction creates a snapshot | Query data as of any point in time |
| **Partition evolution** | Partition spec in metadata, not directory layout | Change partitioning without rewriting data |
| **Hidden partitioning** | Engine auto-prunes based on transforms | Users write `WHERE date = '2026-03-24'`, Iceberg handles the rest |
| **File-level statistics** | Min/max/null counts per column per file | Skip entire files that cannot contain matching rows |

### Delta Lake

Created by Databricks, Delta Lake uses a transaction log (`_delta_log/`) stored alongside the data:

```
/warehouse/events/
├── _delta_log/
│   ├── 00000000000000000000.json   ← Initial commit
│   ├── 00000000000000000001.json   ← Second commit
│   ├── 00000000000000000010.checkpoint.parquet  ← Checkpoint (every 10 commits)
│   └── _last_checkpoint
└── part-00000-xxx.parquet
└── part-00001-xxx.parquet
```

Delta Lake's transaction log is simpler than Iceberg's multi-level metadata. Each JSON file records the actions (add file, remove file, change metadata) for one transaction.

### Comparison

| Feature | Apache Iceberg | Delta Lake | Apache Hudi |
|---------|---------------|------------|-------------|
| **Origin** | Netflix (2018) | Databricks (2019) | Uber (2017) |
| **License** | Apache 2.0 | Apache 2.0 | Apache 2.0 |
| **ACID transactions** | Yes | Yes | Yes |
| **Schema evolution** | Full (add, drop, rename, reorder) | Add, rename, change nullability | Add columns |
| **Time travel** | Yes (snapshot-based) | Yes (version-based) | Yes (timeline-based) |
| **Partition evolution** | Yes (change without rewrite) | Partial | Partial |
| **Hidden partitioning** | Yes | No | No |
| **Engine support** | Spark, Flink, Trino, Presto, Dremio, Snowflake | Spark, Flink (limited), Trino, Presto | Spark, Flink, Presto |
| **Streaming support** | Via Flink sink | Structured Streaming | Native (core feature) |
| **Community momentum** | Highest (2025-2026) | Strong (Databricks ecosystem) | Growing |

**Recommendation for new projects:** Apache Iceberg. It has the broadest engine support, the most advanced features (partition evolution, hidden partitioning), and the strongest community momentum outside any single vendor's ecosystem.

---

## The Metadata Layer: Hive Metastore and Alternatives

### Why You Need a Catalog

Table formats store metadata alongside the data (in the `metadata/` or `_delta_log/` directory). But how does a query engine know WHERE a table's metadata lives? That is the catalog's job.

```
User: "SELECT * FROM analytics.events"

Query Engine: "Where is the 'analytics.events' table?"
      │
      ▼
Catalog (Hive Metastore): "It's at s3://warehouse/analytics/events/"
      │
      ▼
Table Format (Iceberg): "Current snapshot is snap-1234, which includes files 00001, 00002, 00003"
      │
      ▼
Query Engine reads: s3://warehouse/analytics/events/data/00001-abc.parquet ...
```

### Hive Metastore on Kubernetes

Hive Metastore (HMS) is the original and most widely supported catalog. It is a standalone service backed by a relational database:

```yaml
# hive-metastore.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hive-metastore
  namespace: lakehouse
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hive-metastore
  template:
    metadata:
      labels:
        app: hive-metastore
    spec:
      initContainers:
        - name: init-schema
          image: apache/hive:4.0.1
          command:
            - /opt/hive/bin/schematool
            - -dbType
            - postgres
            - -initSchema
            - -ifNotExists
          env:
            - name: HIVE_METASTORE_DB_DRIVER
              value: org.postgresql.Driver
            - name: HIVE_METASTORE_DB_URL
              value: jdbc:postgresql://postgres.lakehouse.svc:5432/metastore
            - name: HIVE_METASTORE_DB_USER
              valueFrom:
                secretKeyRef:
                  name: metastore-db
                  key: username
            - name: HIVE_METASTORE_DB_PASS
              valueFrom:
                secretKeyRef:
                  name: metastore-db
                  key: password
      containers:
        - name: metastore
          image: apache/hive:4.0.1
          command:
            - /opt/hive/bin/hive
            - --service
            - metastore
          ports:
            - containerPort: 9083
              name: thrift
          env:
            - name: SERVICE_NAME
              value: metastore
            - name: HIVE_METASTORE_DB_DRIVER
              value: org.postgresql.Driver
            - name: HIVE_METASTORE_DB_URL
              value: jdbc:postgresql://postgres.lakehouse.svc:5432/metastore
            - name: HIVE_METASTORE_DB_USER
              valueFrom:
                secretKeyRef:
                  name: metastore-db
                  key: username
            - name: HIVE_METASTORE_DB_PASS
              valueFrom:
                secretKeyRef:
                  name: metastore-db
                  key: password
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              memory: 2Gi
          readinessProbe:
            tcpSocket:
              port: 9083
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: hive-metastore
  namespace: lakehouse
spec:
  selector:
    app: hive-metastore
  ports:
    - port: 9083
      targetPort: thrift
      name: thrift
```

### Alternatives to Hive Metastore

| Catalog | Description | When To Use |
|---------|-------------|-------------|
| **Hive Metastore** | Original catalog, broadest support | Default choice, works with everything |
| **AWS Glue Catalog** | Managed HMS-compatible service | AWS-native deployments |
| **Nessie** | Git-like catalog with branching and tagging | Multi-table transactions, data-as-code workflows |
| **Polaris (Iceberg REST Catalog)** | Snowflake-donated OSS REST catalog | Iceberg-first deployments, vendor neutral |
| **Unity Catalog** | Databricks-donated OSS catalog | Delta Lake-first or multi-format deployments |

---

## Trino: The SQL Query Engine

### What Is Trino?

Trino (formerly PrestoSQL, originally Presto from Facebook) is a distributed SQL query engine that can query data where it lives — S3, databases, Kafka, Elasticsearch — without requiring you to move or copy data first.

```
┌───────────────────────────────────────────────────────────┐
│                    TRINO CLUSTER                          │
│                                                           │
│  ┌─────────────────┐                                      │
│  │   Coordinator    │  ← Parses SQL, plans execution,     │
│  │   (1 Pod)        │    distributes to workers            │
│  └────────┬─────────┘                                     │
│           │                                               │
│  ┌────────▼─────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Worker 1       │  │   Worker 2   │  │  Worker 3  │ │
│  │   (Pod)          │  │   (Pod)      │  │  (Pod)     │ │
│  └──────────────────┘  └──────────────┘  └────────────┘ │
│                                                           │
│  Connectors:                                              │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │ Iceberg │ │PostgreSQL│ │   Kafka   │ │ Hive/S3    │  │
│  └─────────┘ └──────────┘ └───────────┘ └────────────┘  │
└───────────────────────────────────────────────────────────┘
```

Trino does not store data. It is a pure compute engine that:
- Reads from configured **connectors** (data sources)
- Executes SQL queries across multiple data sources
- Can **join data across different systems** in a single query

### Deploying Trino on Kubernetes

```yaml
# trino-coordinator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trino-coordinator
  namespace: lakehouse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: trino
      role: coordinator
  template:
    metadata:
      labels:
        app: trino
        role: coordinator
    spec:
      initContainers:
        - name: init-config
          image: busybox:1.37
          command: ["sh", "-c"]
          args:
            - |
              # Copy configs to writable directory
              cp /etc/trino-cm/* /etc/trino/
              mkdir -p /etc/trino/catalog
              cp /etc/trino-catalog/* /etc/trino/catalog/
              # Generate unique node.id (required by Trino)
              NODE_ID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || hostname)
              sed -i "s|^node.data-dir=|node.id=${NODE_ID}\nnode.data-dir=|" /etc/trino/node.properties
          volumeMounts:
            - name: config-cm
              mountPath: /etc/trino-cm
            - name: catalog-cm
              mountPath: /etc/trino-catalog
            - name: config
              mountPath: /etc/trino
      containers:
        - name: trino
          image: trinodb/trino:467
          ports:
            - containerPort: 8080
              name: http
          env:
            - name: TRINO_ENVIRONMENT
              value: production
          volumeMounts:
            - name: config
              mountPath: /etc/trino
          resources:
            requests:
              cpu: "2"
              memory: 8Gi
            limits:
              memory: 8Gi
          readinessProbe:
            httpGet:
              path: /v1/info
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
      volumes:
        - name: config-cm
          configMap:
            name: trino-coordinator-config
        - name: catalog-cm
          configMap:
            name: trino-catalog
        - name: config
          emptyDir: {}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trino-worker
  namespace: lakehouse
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trino
      role: worker
  template:
    metadata:
      labels:
        app: trino
        role: worker
    spec:
      initContainers:
        - name: init-config
          image: busybox:1.37
          command: ["sh", "-c"]
          args:
            - |
              cp /etc/trino-cm/* /etc/trino/
              mkdir -p /etc/trino/catalog
              cp /etc/trino-catalog/* /etc/trino/catalog/
              NODE_ID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || hostname)
              sed -i "s|^node.data-dir=|node.id=${NODE_ID}\nnode.data-dir=|" /etc/trino/node.properties
          volumeMounts:
            - name: config-cm
              mountPath: /etc/trino-cm
            - name: catalog-cm
              mountPath: /etc/trino-catalog
            - name: config
              mountPath: /etc/trino
      containers:
        - name: trino
          image: trinodb/trino:467
          volumeMounts:
            - name: config
              mountPath: /etc/trino
          resources:
            requests:
              cpu: "4"
              memory: 16Gi
            limits:
              memory: 16Gi
      volumes:
        - name: config-cm
          configMap:
            name: trino-worker-config
        - name: catalog-cm
          configMap:
            name: trino-catalog
        - name: config
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: trino
  namespace: lakehouse
spec:
  selector:
    app: trino
    role: coordinator
  ports:
    - port: 8080
      targetPort: http
```

### Trino Configuration

```yaml
# trino-coordinator-config ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: trino-coordinator-config
  namespace: lakehouse
data:
  config.properties: |
    coordinator=true
    node-scheduler.include-coordinator=false
    http-server.http.port=8080
    discovery.uri=http://trino.lakehouse.svc:8080
    query.max-memory=20GB
    query.max-memory-per-node=8GB
    query.max-total-memory-per-node=10GB

  node.properties: |
    node.environment=production
    node.data-dir=/data/trino

  jvm.config: |
    -server
    -Xmx6G
    -XX:+UseG1GC
    -XX:G1HeapRegionSize=32M
    -XX:+ExplicitGCInvokesConcurrent
    -XX:+ExitOnOutOfMemoryError
    -Djdk.attach.allowAttachSelf=true

  log.properties: |
    io.trino=INFO
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: trino-worker-config
  namespace: lakehouse
data:
  config.properties: |
    coordinator=false
    http-server.http.port=8080
    discovery.uri=http://trino.lakehouse.svc:8080
    query.max-memory-per-node=12GB
    query.max-total-memory-per-node=14GB

  node.properties: |
    node.environment=production
    node.data-dir=/data/trino

  jvm.config: |
    -server
    -Xmx12G
    -XX:+UseG1GC
    -XX:G1HeapRegionSize=32M
    -XX:+ExplicitGCInvokesConcurrent
    -XX:+ExitOnOutOfMemoryError
    -Djdk.attach.allowAttachSelf=true

  log.properties: |
    io.trino=INFO
```

### Catalog Configuration (Connectors)

```yaml
# trino-catalog ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: trino-catalog
  namespace: lakehouse
data:
  iceberg.properties: |
    connector.name=iceberg
    iceberg.catalog.type=hive_metastore
    hive.metastore.uri=thrift://hive-metastore.lakehouse.svc:9083
    hive.s3.endpoint=http://minio.lakehouse.svc:9000
    hive.s3.aws-access-key=minioadmin
    hive.s3.aws-secret-key=minioadmin
    hive.s3.path-style-access=true
    iceberg.file-format=PARQUET
    iceberg.compression-codec=ZSTD

  postgres.properties: |
    connector.name=postgresql
    connection-url=jdbc:postgresql://postgres.lakehouse.svc:5432/analytics
    connection-user=trino
    connection-password=trino_password

  tpch.properties: |
    connector.name=tpch
```

---

## Access Control

### Trino Security

Trino supports fine-grained access control:

```yaml
# In trino-coordinator-config ConfigMap, add:
data:
  access-control.properties: |
    access-control.name=file
    security.config-file=/etc/trino/rules/rules.json
    security.refresh-period=60s
```

```json
{
  "catalogs": [
    {
      "catalog": "iceberg",
      "allow": "all"
    },
    {
      "catalog": "postgres",
      "allow": "read-only"
    }
  ],
  "schemas": [
    {
      "catalog": "iceberg",
      "schema": "raw",
      "owner": true
    }
  ],
  "tables": [
    {
      "catalog": "iceberg",
      "schema": "pii",
      "table": ".*",
      "privileges": ["SELECT"],
      "grantee": "analyst",
      "columns": [
        {
          "name": "ssn",
          "allow": false
        },
        {
          "name": "email",
          "mask": "'***@***.***'"
        }
      ]
    }
  ]
}
```

This configuration:
- Gives full access to the Iceberg catalog
- Gives read-only access to PostgreSQL
- Masks PII columns for the `analyst` role
- Blocks access to SSN entirely

---

## Building the Lakehouse: End-to-End

### The Reference Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAKEHOUSE ON K8s                         │
│                                                                 │
│  ┌───────────┐  ┌─────────────┐  ┌────────────┐               │
│  │  Kafka    │  │  Airflow    │  │  Trino     │               │
│  │ (ingest)  │  │ (orchestrate)│  │  (query)   │               │
│  └─────┬─────┘  └──────┬──────┘  └──────┬─────┘               │
│        │               │                │                       │
│        ▼               ▼                ▼                       │
│  ┌──────────────────────────────────────────────┐              │
│  │            ICEBERG TABLE FORMAT              │              │
│  │  • ACID transactions                         │              │
│  │  • Schema evolution                          │              │
│  │  • Time travel                               │              │
│  └──────────────────────┬───────────────────────┘              │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────┐              │
│  │         HIVE METASTORE (catalog)             │              │
│  └──────────────────────┬───────────────────────┘              │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────┐              │
│  │         OBJECT STORAGE (MinIO / S3)          │              │
│  │  s3://warehouse/                              │              │
│  │    ├── raw/          (landing zone)          │              │
│  │    ├── curated/      (cleaned, validated)    │              │
│  │    └── aggregated/   (business-ready)        │              │
│  └──────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### The Medallion Architecture

The most common lakehouse data organization pattern:

```
BRONZE (Raw)           SILVER (Curated)        GOLD (Aggregated)
┌─────────────┐       ┌─────────────┐         ┌─────────────┐
│ Raw events  │──────→│ Cleaned     │────────→│ Business    │
│ as received │  ETL  │ Validated   │  Agg    │ Metrics     │
│             │       │ Deduped     │         │ Reports     │
│ Schema:     │       │             │         │             │
│ evolving    │       │ Schema:     │         │ Schema:     │
│             │       │ enforced    │         │ stable      │
└─────────────┘       └─────────────┘         └─────────────┘

Retention: 90 days     Retention: 2 years      Retention: forever
Format: JSON→Parquet   Format: Parquet          Format: Parquet
Updates: append-only   Updates: upsert          Updates: overwrite
```

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Using Hive partitioning with Iceberg | Old habits from Hive/Spark | Use Iceberg's hidden partitioning. Define partition transforms in the table spec, not in directory paths |
| Not compacting small files | Streaming ingestion creates many tiny files | Schedule compaction jobs (Spark or Trino `OPTIMIZE`) to merge small files into optimal sizes (128-512 MB) |
| Skipping the catalog layer | "I'll just point at the S3 path" | Without a catalog, every engine needs hardcoded paths. Use Hive Metastore or a REST catalog for a single source of truth |
| Choosing table format based on marketing | "We use Databricks, so Delta Lake" | Choose based on engine compatibility. If you use Trino + Spark + Flink, Iceberg has the broadest support |
| Not monitoring query performance | "Queries are running, so they must be fine" | Track query duration, data scanned per query, and failed queries. A single bad query can scan terabytes unnecessarily |
| Ignoring file format and compression | "Parquet is Parquet" | Use ZSTD compression (better ratio than Snappy, comparable speed). Use Parquet with appropriate row group sizes (64-128 MB) |
| Storing everything in one schema | "We'll organize later" | Use the medallion architecture from day one. Bronze/Silver/Gold schemas with clear ownership and SLAs |
| Running Trino coordinator and workers on the same node | Resource contention | Use pod anti-affinity to spread workers across nodes. The coordinator should be on a separate node |
| Not enabling Iceberg metadata cleanup | Metadata files accumulate indefinitely | Configure `write.metadata.delete-after-commit.enabled=true` and run `expire_snapshots` regularly |

---

## Quiz

**Question 1:** What problem do open table formats (Iceberg, Delta Lake) solve that plain Parquet files on S3 do not?

<details>
<summary>Show Answer</summary>

Plain Parquet files on S3 are just files — they have no concept of:
1. **ACID transactions**: Without a table format, a failed write can leave partial data visible to readers. Iceberg/Delta use atomic metadata swaps so writes are all-or-nothing.
2. **Schema enforcement/evolution**: Plain files have no schema registry. Different files can have different schemas. Table formats track schema history and enforce compatibility.
3. **Time travel**: Without snapshots, you cannot query historical data or roll back a bad write.
4. **Efficient pruning**: Query engines must list and open every file to find relevant data. Table formats store file-level statistics (min/max per column) enabling engines to skip irrelevant files.
5. **Consistent reads**: Without isolation, a reader can see a partially-written set of files. Table formats provide snapshot isolation.

</details>

**Question 2:** Explain Iceberg's hidden partitioning and why it is an improvement over Hive-style partitioning.

<details>
<summary>Show Answer</summary>

**Hive-style partitioning** encodes partition values in directory names: `/data/year=2026/month=03/day=24/`. Users MUST include the partition columns in their queries (`WHERE year=2026 AND month=3 AND day=24`) to get partition pruning. If they write `WHERE date = '2026-03-24'`, Hive scans ALL partitions.

**Iceberg hidden partitioning** stores partition transforms in the table metadata, not in file paths. You define a transform (e.g., `day(timestamp)`) when creating the table, and Iceberg automatically applies partition pruning when users filter on the source column. A query with `WHERE timestamp > '2026-03-24'` automatically prunes to the relevant day partitions — the user does not need to know the partitioning scheme at all.

Additional benefit: **partition evolution**. With Hive, changing from daily to hourly partitioning requires rewriting all data. With Iceberg, you alter the partition spec and new data uses the new scheme while old data retains the old scheme. No data rewrite needed.

</details>

**Question 3:** What is the role of a catalog (like Hive Metastore) in the lakehouse architecture?

<details>
<summary>Show Answer</summary>

A catalog maps **logical names** (database.schema.table) to **physical locations** (s3://bucket/path/to/metadata). It serves as the registry that query engines consult to find tables.

Without a catalog, every tool that accesses the data needs to know the exact S3 path to the table's metadata. With a catalog:
- Users write `SELECT * FROM analytics.events` instead of pointing to an S3 path
- Multiple engines (Trino, Spark, Flink) share the same table definitions
- Table metadata (current snapshot, schema, partition spec) has a single source of truth
- Access control can be applied at the catalog level

The catalog does NOT store the actual data — it stores pointers to where the table format's metadata lives.

</details>

**Question 4:** Why would you choose Trino over Spark for ad-hoc SQL queries on a lakehouse?

<details>
<summary>Show Answer</summary>

Trino is optimized for **interactive, low-latency SQL queries**:
1. **No startup overhead**: Trino workers are always running. Spark must start a driver and executors for each query (5-30 seconds on Kubernetes).
2. **Streaming execution**: Trino begins returning results before reading all data. Spark processes in stages and returns results only after all stages complete.
3. **MPP architecture**: Trino's massively parallel processing engine is designed for sub-second to minute-range queries.
4. **Cross-catalog joins**: Trino can join Iceberg tables with PostgreSQL tables and Kafka topics in a single query.

Spark is better for: large-scale transformations (ETL), machine learning, and jobs that need to process entire datasets. Trino is better for: dashboards, data exploration, ad-hoc analysis, and any query where response time matters.

</details>

**Question 5:** What is the medallion architecture and what purpose does each layer serve?

<details>
<summary>Show Answer</summary>

The medallion architecture organizes lakehouse data into three quality tiers:

**Bronze (Raw)**: Landing zone for raw data as received from sources. No transformations applied. Append-only. Retains the original format for debugging and reprocessing. Short to medium retention.

**Silver (Curated)**: Cleaned, validated, deduplicated data with enforced schemas. This layer handles data quality (null checks, type coercion, deduplication) and is the "single source of truth" for downstream consumers. Medium to long retention.

**Gold (Aggregated)**: Business-ready aggregations, metrics, and report tables optimized for specific use cases. Pre-joined, pre-aggregated data that dashboards and analysts consume directly. Long to permanent retention.

Each layer has increasing data quality and decreasing data volume. The pattern enables: reprocessing (re-derive Silver from Bronze if logic changes), clear data lineage, and separation of concerns between ingestion and consumption.

</details>

**Question 6:** A data engineer notices that Trino queries are scanning 10x more data than expected on Iceberg tables. What are two likely causes?

<details>
<summary>Show Answer</summary>

1. **Small file problem**: Streaming ingestion or poorly-configured Spark jobs created thousands of tiny files (< 1 MB each). Each file has its own metadata entry, and the overhead of opening many files dominates query time. Fix by running compaction (`OPTIMIZE` in Trino or `rewriteDataFiles` in Spark) to merge small files into 128-512 MB files.

2. **Missing or stale statistics**: Iceberg uses file-level column statistics (min/max values) for data pruning. If statistics are missing (e.g., written by an old engine version) or the data is not well-sorted, Iceberg cannot skip files effectively. Fix by running `ANALYZE` to compute statistics, or sort data by commonly-filtered columns during writes using Iceberg's `write.distribution-mode=hash` or explicit sorting.

Other possible causes: queries not filtering on partitioned columns, using `SELECT *` when only a few columns are needed (column pruning still reads metadata for all columns), or expired snapshot data not being cleaned up (orphan files being scanned).

</details>

---

## Hands-On Exercise: Trino on K8s + MinIO + Hive Metastore + SQL on Iceberg Tables

### Objective

Deploy a complete lakehouse stack on Kubernetes: MinIO for object storage, Hive Metastore for the catalog, and Trino for SQL queries. Create Iceberg tables, load data, and run analytical queries.

### Environment Setup

```bash
# Create the kind cluster
kind create cluster --name lakehouse-lab

# Create namespace
kubectl create namespace lakehouse
```

### Step 1: Deploy MinIO (Object Storage)

```yaml
# minio.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: lakehouse
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
          image: quay.io/minio/minio:RELEASE.2025-02-28T09-55-16Z
          args: ["server", "/data", "--console-address", ":9001"]
          ports:
            - containerPort: 9000
              name: api
            - containerPort: 9001
              name: console
          env:
            - name: MINIO_ROOT_USER
              value: minioadmin
            - name: MINIO_ROOT_PASSWORD
              value: minioadmin
          volumeMounts:
            - name: data
              mountPath: /data
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              memory: 1Gi
      volumes:
        - name: data
          emptyDir:
            sizeLimit: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: lakehouse
spec:
  selector:
    app: minio
  ports:
    - port: 9000
      targetPort: api
      name: api
    - port: 9001
      targetPort: console
      name: console
```

```bash
kubectl apply -f minio.yaml
kubectl -n lakehouse wait --for=condition=Available deployment/minio --timeout=120s

# Create the warehouse bucket
kubectl -n lakehouse run mc --rm -it --restart=Never \
  --image=quay.io/minio/mc:latest -- \
  sh -c "mc alias set myminio http://minio:9000 minioadmin minioadmin && \
         mc mb myminio/warehouse && \
         mc ls myminio/"
```

### Step 2: Deploy PostgreSQL for Hive Metastore

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: lakehouse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: metastore
            - name: POSTGRES_USER
              value: hive
            - name: POSTGRES_PASSWORD
              value: hive_password
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              memory: 512Mi
      volumes:
        - name: data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: lakehouse
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: v1
kind: Secret
metadata:
  name: metastore-db
  namespace: lakehouse
type: Opaque
stringData:
  username: hive
  password: hive_password
```

```bash
kubectl apply -f postgres.yaml
kubectl -n lakehouse wait --for=condition=Available deployment/postgres --timeout=120s
```

### Step 3: Deploy Trino with Iceberg Connector

For this lab, we use Trino's built-in Iceberg connector with a JDBC catalog (pointing to our PostgreSQL), which simplifies the setup by eliminating the need for a separate Hive Metastore service.

```yaml
# trino-lab.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trino-config
  namespace: lakehouse
data:
  config.properties: |
    coordinator=true
    node-scheduler.include-coordinator=true
    http-server.http.port=8080
    discovery.uri=http://localhost:8080
    query.max-memory=2GB
    query.max-memory-per-node=1GB

  node.properties: |
    node.environment=lab
    node.data-dir=/data/trino

  jvm.config: |
    -server
    -Xmx1G
    -XX:+UseG1GC
    -XX:+ExitOnOutOfMemoryError

  log.properties: |
    io.trino=INFO
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: trino-catalog-config
  namespace: lakehouse
data:
  iceberg.properties: |
    connector.name=iceberg
    iceberg.catalog.type=jdbc
    iceberg.jdbc-catalog.driver-class=org.postgresql.Driver
    iceberg.jdbc-catalog.connection-url=jdbc:postgresql://postgres.lakehouse.svc:5432/metastore
    iceberg.jdbc-catalog.connection-user=hive
    iceberg.jdbc-catalog.connection-password=hive_password
    iceberg.jdbc-catalog.catalog-name=lakehouse
    fs.native-s3.enabled=true
    s3.endpoint=http://minio.lakehouse.svc:9000
    s3.region=us-east-1
    s3.path-style-access=true
    s3.aws-access-key=minioadmin
    s3.aws-secret-key=minioadmin
    iceberg.file-format=PARQUET

  tpch.properties: |
    connector.name=tpch
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trino
  namespace: lakehouse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: trino
  template:
    metadata:
      labels:
        app: trino
    spec:
      initContainers:
        - name: init-config
          image: busybox:1.37
          command: ["sh", "-c"]
          args:
            - |
              # Copy configs to a writable directory (ConfigMap mounts are read-only)
              cp /etc/trino-cm/* /etc/trino/
              mkdir -p /etc/trino/catalog
              cp /etc/trino-catalog/* /etc/trino/catalog/
              # Generate unique node.id (required by Trino to start)
              NODE_ID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || hostname)
              sed -i "s|^node.data-dir=|node.id=${NODE_ID}\nnode.data-dir=|" /etc/trino/node.properties
          volumeMounts:
            - name: config-cm
              mountPath: /etc/trino-cm
            - name: catalog-cm
              mountPath: /etc/trino-catalog
            - name: config
              mountPath: /etc/trino
      containers:
        - name: trino
          image: trinodb/trino:467
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: config
              mountPath: /etc/trino
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              memory: 2Gi
          readinessProbe:
            httpGet:
              path: /v1/info
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
      volumes:
        - name: config-cm
          configMap:
            name: trino-config
        - name: catalog-cm
          configMap:
            name: trino-catalog-config
        - name: config
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: trino
  namespace: lakehouse
spec:
  selector:
    app: trino
  ports:
    - port: 8080
      targetPort: 8080
```

```bash
kubectl apply -f trino-lab.yaml
kubectl -n lakehouse wait --for=condition=Available deployment/trino --timeout=180s
```

### Step 4: Create Iceberg Tables and Load Data

```bash
# Connect to Trino CLI
kubectl -n lakehouse run trino-cli --rm -it --restart=Never \
  --image=trinodb/trino:467 -- trino --server http://trino:8080 --catalog iceberg
```

Inside the Trino CLI:

```sql
-- Create a schema (database)
CREATE SCHEMA IF NOT EXISTS iceberg.analytics
  WITH (location = 's3://warehouse/analytics/');

-- Create an Iceberg table from TPCH sample data
CREATE TABLE iceberg.analytics.orders
  WITH (
    format = 'PARQUET',
    partitioning = ARRAY['month(orderdate)']
  )
  AS SELECT
    orderkey,
    custkey,
    orderstatus,
    totalprice,
    orderdate,
    orderpriority,
    clerk,
    shippriority
  FROM tpch.sf1.orders;
-- This creates an Iceberg table with ~1.5M rows

-- Verify the table
SELECT count(*) AS total_orders FROM iceberg.analytics.orders;

-- Create a customers table
CREATE TABLE iceberg.analytics.customers
  WITH (format = 'PARQUET')
  AS SELECT * FROM tpch.sf1.customer;

-- Check metadata
SELECT * FROM iceberg.analytics."orders$snapshots";
SELECT * FROM iceberg.analytics."orders$files" LIMIT 5;
```

### Step 5: Run Analytical Queries

```sql
-- Revenue by order status and month
SELECT
    orderstatus,
    date_trunc('month', orderdate) AS order_month,
    count(*) AS order_count,
    round(sum(totalprice), 2) AS total_revenue,
    round(avg(totalprice), 2) AS avg_order_value
FROM iceberg.analytics.orders
WHERE orderdate >= DATE '1996-01-01'
  AND orderdate < DATE '1997-01-01'
GROUP BY orderstatus, date_trunc('month', orderdate)
ORDER BY order_month, orderstatus;

-- Top 10 customers by total spend (cross-table join)
SELECT
    c.name AS customer_name,
    c.mktsegment AS market_segment,
    count(o.orderkey) AS order_count,
    round(sum(o.totalprice), 2) AS total_spend
FROM iceberg.analytics.orders o
JOIN iceberg.analytics.customers c ON o.custkey = c.custkey
GROUP BY c.name, c.mktsegment
ORDER BY total_spend DESC
LIMIT 10;

-- Time travel: see data as of a specific snapshot
SELECT snapshot_id, committed_at FROM iceberg.analytics."orders$snapshots";
-- Use a snapshot ID from the output:
-- SELECT count(*) FROM iceberg.analytics.orders FOR VERSION AS OF <snapshot_id>;
```

### Step 6: Schema Evolution

```sql
-- Add a new column (no data rewrite needed)
ALTER TABLE iceberg.analytics.orders ADD COLUMN region VARCHAR;

-- Verify the column was added
DESCRIBE iceberg.analytics.orders;

-- Update the new column for some rows
UPDATE iceberg.analytics.orders
SET region = 'NORTH AMERICA'
WHERE clerk LIKE '%000001%';

-- Verify: check the snapshot history shows the update
SELECT snapshot_id, committed_at, operation
FROM iceberg.analytics."orders$snapshots"
ORDER BY committed_at DESC;
```

### Step 7: Clean Up

```bash
kubectl delete namespace lakehouse
kind delete cluster --name lakehouse-lab
```

### Success Criteria

You have completed this exercise when you:
- [ ] Deployed MinIO, PostgreSQL, and Trino on Kubernetes
- [ ] Created an Iceberg schema pointing to MinIO (S3)
- [ ] Created partitioned Iceberg tables from TPCH sample data
- [ ] Ran analytical SQL queries with joins across Iceberg tables
- [ ] Inspected Iceberg metadata (snapshots, file listing)
- [ ] Performed schema evolution (added a column without rewriting data)

---

## Key Takeaways

1. **The lakehouse combines the best of lakes and warehouses** — Cheap, open storage with ACID transactions, schema enforcement, and fast queries.
2. **Open table formats are the key innovation** — Iceberg, Delta Lake, and Hudi add a metadata layer on top of Parquet files that enables transactions, time travel, and schema evolution.
3. **The catalog (Hive Metastore) is the bridge** — It maps logical table names to physical storage locations, enabling multiple engines to share the same data.
4. **Trino is the interactive SQL layer** — It queries data where it lives without moving it, supporting sub-second to minute-range analytical queries.
5. **The medallion architecture organizes data quality** — Bronze (raw), Silver (curated), Gold (aggregated) layers provide clear data lineage and quality guarantees.
6. **File compaction is not optional** — Streaming ingestion and frequent writes create small files that destroy query performance. Schedule regular compaction.

---

## Further Reading

**Books:**
- **"Apache Iceberg: The Definitive Guide"** — Tomer Shiran, Jason Hughes, Alex Merced (O'Reilly)
- **"The Data Lakehouse"** — Bill Inmon, Mary Levins, Ranjeet Srivastava (Technics Publications)

**Articles:**
- **"Lakehouse: A New Generation of Open Platforms"** — Databricks Research Paper (cidrdb.org/cidr2021)
- **"Apache Iceberg Documentation"** — iceberg.apache.org
- **"Trino Documentation"** — trino.io/docs/current

**Talks:**
- **"The Rise of the Data Lakehouse"** — Ali Ghodsi, Data + AI Summit 2023 (YouTube)
- **"Apache Iceberg: An Architectural Look Under the Covers"** — Alex Merced, Dremio (YouTube)

---

## Summary

The data lakehouse is not a single product — it is an architecture pattern built from composable, open-source components. Object storage provides durability at scale. Open table formats (Iceberg) add reliability and governance. Catalogs provide discoverability. Query engines (Trino, Spark) provide compute.

On Kubernetes, each of these components runs as a managed workload: scalable, declarative, and replaceable. You are not locked into any vendor. If a better query engine emerges, swap it in. If your storage needs change, switch backends. The data stays in open formats on storage you control.

This is the promise of the lakehouse: warehouse-grade reliability, lake-scale economics, and cloud-native flexibility.

---

## Next Steps

You have completed the Data Engineering on Kubernetes discipline. From here, consider:
- **[SRE Discipline](../../core-platform/sre/)** — Learn to operate these data systems reliably in production
- **[Observability Toolkit](../../../toolkits/observability-intelligence/observability/)** — Monitor your data platform with Prometheus, Grafana, and OpenTelemetry
- **[MLOps Discipline](../mlops/)** — Build ML pipelines on top of your lakehouse

---

*"The best data architecture is the one that does not make you choose between cost, performance, and openness."* — Ryan Blue, Apache Iceberg co-creator

---
title: "Module 1.3: Stream Processing with Apache Flink"
slug: platform/disciplines/data-ai/data-engineering/module-1.3-flink
sidebar:
  order: 4
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 3.5 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.2 — Apache Kafka on Kubernetes](module-1.2-kafka/) — Kafka fundamentals, topics, partitions, consumer groups
- **Required**: Basic Java or Python programming knowledge
- **Recommended**: Understanding of SQL (SELECT, GROUP BY, JOIN, window functions)
- **Recommended**: Familiarity with event-driven architecture concepts

---

## Why This Module Matters

Kafka gives you a firehose of data. But raw data flowing through topics is not insight — it is noise. You need something that can read millions of events per second, transform them, aggregate them, join them with other streams, and output results in real time.

That something is Apache Flink.

Flink is not the only stream processor (Spark Structured Streaming, Kafka Streams, and Apache Beam all exist), but it has won the stream processing war for a simple reason: **it was built for streaming from day one.** While other frameworks bolted streaming onto batch engines, Flink treats bounded data (batch) as a special case of unbounded data (streaming). This seemingly philosophical difference gives Flink unique capabilities: exactly-once processing, event-time semantics, and millisecond-latency state access that other engines struggle to match.

LinkedIn, Alibaba, Uber, Netflix, and Stripe all run Flink at massive scale. Alibaba processes over 40 billion events per day through Flink during Singles' Day. When you need to detect fraud in real time, compute live dashboards, or react to events as they happen, Flink is the tool.

This module teaches you to deploy Flink on Kubernetes, understand its execution model, and build real streaming pipelines that consume from Kafka and produce results in real time.

---

## Did You Know?

- **Flink started as a research project at TU Berlin called Stratosphere.** It was donated to Apache in 2014 and graduated to a top-level project in just 8 months — one of the fastest graduations in Apache history.
- **Flink can maintain terabytes of application state** while processing millions of events per second. It uses RocksDB as an embedded state backend, storing state on local disk with in-memory caching, and takes asynchronous snapshots without stopping processing.
- **Alibaba modified Flink so heavily that they open-sourced their version as "Blink."** Many of Blink's optimizations (including the unified batch/streaming SQL engine) were later merged back into mainline Flink.

---

## Bounded vs Unbounded Data

### The Fundamental Distinction

Every data processing system must answer one question: **does the data have an end?**

```
BOUNDED DATA (Batch):
┌──────────────────────────────────────────┐
│  [record] [record] [record] ... [END]    │
│                                          │
│  "Process all records, then output"      │
│  Example: Last month's sales CSV         │
└──────────────────────────────────────────┘

UNBOUNDED DATA (Streaming):
┌──────────────────────────────────────────→  (never ends)
│  [event] [event] [event] [event] ...
│
│  "Process each event as it arrives"
│  Example: Live clickstream from website
└──────────────────────────────────────────→
```

Traditional batch systems (MapReduce, Spark) were designed for bounded data. They read all input, process it, and write output. Clean, simple, and completely useless for real-time applications.

Flink's insight: **batch is just streaming with an end**. Build your engine for unbounded data, and bounded data becomes trivial. The reverse is not true — bolting streaming onto a batch engine produces awkward compromises.

### Why This Matters in Practice

Consider computing the average purchase amount per customer:

- **Batch approach**: Wait for all data, compute average, output. Easy but delayed by hours.
- **Micro-batch approach** (Spark Streaming): Collect events for 1-30 seconds, compute average over that window. Lower latency but introduces artificial boundaries.
- **True streaming approach** (Flink): Maintain a running average for each customer, update it with every event, output continuously. Lowest latency, most accurate, but requires sophisticated state management.

Flink handles the hard case natively, which is why it excels at streaming.

---

## Flink Architecture

### The Two Key Processes

```
┌──────────────────────────────────────────────────────────────┐
│                      FLINK CLUSTER                           │
│                                                              │
│  ┌────────────────────────────┐    ┌──────────────────────┐  │
│  │      JobManager           │    │    TaskManagers       │  │
│  │                            │    │                      │  │
│  │  ┌──────────────────────┐ │    │  ┌────────────────┐  │  │
│  │  │ Job Scheduling       │ │    │  │ Task Slots     │  │  │
│  │  │ Checkpoint Coord.    │ │    │  │ ┌──┐┌──┐┌──┐  │  │  │
│  │  │ Resource Management  │ │    │  │ │T1││T2││T3│  │  │  │
│  │  │ Failure Recovery     │ │    │  │ └──┘└──┘└──┘  │  │  │
│  │  └──────────────────────┘ │    │  └────────────────┘  │  │
│  └────────────────────────────┘    │                      │  │
│                                    │  ┌────────────────┐  │  │
│                                    │  │ Task Slots     │  │  │
│                                    │  │ ┌──┐┌──┐┌──┐  │  │  │
│                                    │  │ │T4││T5││T6│  │  │  │
│                                    │  │ └──┘└──┘└──┘  │  │  │
│                                    │  └────────────────┘  │  │
│                                    └──────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**JobManager** (the brain):
- Accepts job submissions and creates execution graphs
- Coordinates checkpoints across all TaskManagers
- Manages resource allocation and failover
- Runs as a Deployment (1 replica, or 3 for HA)

**TaskManager** (the muscle):
- Executes the actual data processing tasks
- Manages local state (in-memory or RocksDB)
- Exchanges data with other TaskManagers via network buffers
- Runs as Pods managed by the Flink Kubernetes Operator

### Task Slots and Parallelism

Each TaskManager has a fixed number of **task slots**. A slot is a unit of resource isolation — it gets a fraction of the TaskManager's memory and can run one parallel pipeline.

```
TaskManager (8 GB memory, 4 slots):
┌──────────────────────────────────────┐
│ Slot 1 (2GB)  │ Slot 2 (2GB)        │
│ Source → Map  │ Source → Map         │
│               │                      │
│ Slot 3 (2GB)  │ Slot 4 (2GB)        │
│ Source → Map  │ Source → Map         │
└──────────────────────────────────────┘
```

**Parallelism** determines how many slots a job uses. A job with parallelism 8 running on 2 TaskManagers with 4 slots each uses all 8 slots.

---

## The Flink Kubernetes Operator

### Why Use the Operator?

The Flink Kubernetes Operator is the official CNCF way to run Flink on Kubernetes. It manages:

| Feature | What It Does |
|---------|-------------|
| **Job lifecycle** | Submit, cancel, suspend, and resume Flink jobs |
| **Savepoints** | Trigger savepoints before upgrades, restore after |
| **Autoscaling** | Scale TaskManagers based on backpressure or lag |
| **Rolling upgrades** | Update job code with automatic savepoint/restore |
| **Health monitoring** | Restart failed jobs automatically |
| **Resource management** | Dynamic resource allocation per job |

### Installing the Operator

```bash
# Add the Flink Helm repository
helm repo add flink-operator https://downloads.apache.org/flink/flink-kubernetes-operator-1.10.0/
helm repo update

# Install the operator
kubectl create namespace flink
helm install flink-kubernetes-operator flink-operator/flink-kubernetes-operator \
  --namespace flink \
  --set webhook.create=true \
  --set metrics.port=9999

# Verify installation
kubectl -n flink wait --for=condition=Available \
  deployment/flink-kubernetes-operator --timeout=120s
```

### Deployment Modes

The operator supports two deployment modes:

**Application Mode** (recommended for production):
Each Flink application runs in its own dedicated cluster. The JobManager starts the application's `main()` method directly.

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: fraud-detector
  namespace: flink
spec:
  image: my-registry.io/fraud-detector:v2.1.0
  flinkVersion: v1_20
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "4"
    state.backend.type: rocksdb
    state.checkpoints.dir: s3://flink-state/fraud-detector/checkpoints
    state.savepoints.dir: s3://flink-state/fraud-detector/savepoints
    execution.checkpointing.interval: "60000"
    execution.checkpointing.min-pause: "30000"
    restart-strategy.type: exponential-delay
    restart-strategy.exponential-delay.initial-backoff: 1s
    restart-strategy.exponential-delay.max-backoff: 60s
  serviceAccount: flink
  jobManager:
    resource:
      memory: "2048m"
      cpu: 1
    replicas: 1
  taskManager:
    resource:
      memory: "4096m"
      cpu: 2
    replicas: 3
  job:
    jarURI: local:///opt/flink/usrlib/fraud-detector.jar
    entryClass: com.example.FraudDetector
    parallelism: 12
    upgradeMode: savepoint
    state: running
    savepointTriggerNonce: 0
```

**Session Mode** (for development and ad-hoc queries):
A long-running Flink cluster accepts multiple job submissions.

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: flink-session
  namespace: flink
spec:
  image: flink:1.20-java17
  flinkVersion: v1_20
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "4"
    state.backend.type: hashmap
  serviceAccount: flink
  jobManager:
    resource:
      memory: "2048m"
      cpu: 1
  taskManager:
    resource:
      memory: "4096m"
      cpu: 2
    replicas: 2
```

---

## State Management: Flink's Superpower

### Why State Matters

Stateless transformations (filter, map) are easy. The hard problems — deduplication, windowed aggregation, pattern detection, joins — all require **state**.

Consider counting page views per URL in the last 5 minutes. For every incoming event, you need to:
1. Look up the current count for that URL
2. Increment it
3. Remove expired entries older than 5 minutes

This requires maintaining a continuously-updated data structure — that is state.

### State Backends

Flink offers two state backends:

| Backend | Storage | Best For |
|---------|---------|----------|
| **HashMapStateBackend** | JVM heap | Small state (< 1 GB), development, low latency |
| **EmbeddedRocksDBStateBackend** | Local disk + memory cache | Large state (TB+), production |

```yaml
# In FlinkDeployment spec.flinkConfiguration
flinkConfiguration:
  state.backend.type: rocksdb
  state.backend.rocksdb.memory.managed: "true"
  state.backend.rocksdb.block.cache-size: 256mb
  state.backend.rocksdb.writebuffer.size: 128mb
  state.backend.rocksdb.writebuffer.count: "4"
```

RocksDB is the production choice because it can handle state far larger than available memory. It stores data on local SSD with an in-memory cache, and Flink manages its memory usage through the managed memory framework.

---

## Checkpointing and Savepoints

### The Problem: What Happens When Things Crash?

Flink processes millions of events per second while maintaining state. If a TaskManager crashes, all the state on that process is lost. Without checkpointing, you would have to reprocess everything from the beginning.

### Checkpoints: Automatic Recovery

Checkpoints are periodic, consistent snapshots of the entire job's state. They are taken automatically and stored on durable storage (S3, HDFS, GCS).

```
Time ──────────────────────────────────────────────→

Events:  e1  e2  e3  e4  e5  e6  e7  e8  e9  e10
              │              │              │
         Checkpoint 1   Checkpoint 2   Checkpoint 3

If crash after e7:
  → Restore from Checkpoint 2 (state at e5)
  → Replay e6, e7 from Kafka
  → Continue processing e8+
```

**The barrier mechanism:**

Flink uses a clever algorithm called **aligned checkpointing** (inspired by the Chandy-Lamport algorithm):

```
Source ──[e1]──[e2]──[BARRIER]──[e3]──[e4]──→ Operator
                         │
                    "Snapshot your state now,
                     then forward the barrier"
```

The barrier flows through the dataflow graph like a regular event. When an operator receives a barrier, it snapshots its state. This ensures the checkpoint is a consistent cut across all operators without stopping processing.

**Configuration:**

```yaml
flinkConfiguration:
  # Take a checkpoint every 60 seconds
  execution.checkpointing.interval: "60000"
  # Minimum 30 seconds between checkpoints
  execution.checkpointing.min-pause: "30000"
  # Exactly-once semantics
  execution.checkpointing.mode: EXACTLY_ONCE
  # Tolerate 3 consecutive checkpoint failures
  execution.checkpointing.tolerable-failed-checkpoints: "3"
  # Checkpoint timeout
  execution.checkpointing.timeout: "600000"
  # Store on S3
  state.checkpoints.dir: s3://flink-state/checkpoints
  # Keep last 3 checkpoints
  state.checkpoints.num-retained: "3"
```

### Savepoints: Planned Snapshots

Savepoints are like checkpoints but manually triggered. Use them for:
- **Job upgrades**: Savepoint, deploy new code, restore from savepoint
- **A/B testing**: Fork a job into two versions from the same state
- **Migration**: Move a job between clusters

```bash
# Trigger a savepoint via the Flink Kubernetes Operator
# Update the FlinkDeployment CR:
kubectl -n flink patch flinkdeployment fraud-detector --type merge \
  -p '{"spec":{"job":{"savepointTriggerNonce": 1}}}'

# The operator triggers a savepoint and stores it at state.savepoints.dir
# Check status:
kubectl -n flink get flinkdeployment fraud-detector -o yaml | grep -A5 savepointInfo
```

---

## Event Time and Watermarks

### The Three Notions of Time

```
┌──────────────────────────────────────────────────────┐
│                TIME IN STREAM PROCESSING             │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Event Time      │  When the event actually happened │
│  (embedded in    │  e.g., sensor reading at 14:05:03 │
│   the event)     │                                   │
│                  │                                   │
│  Ingestion Time  │  When Flink received the event    │
│                  │  e.g., arrived at 14:05:07         │
│                  │                                   │
│  Processing Time │  When Flink processes the event   │
│                  │  e.g., processed at 14:05:09       │
└──────────────────────────────────────────────────────┘
```

**Why event time matters:** Events arrive out of order. A mobile app might batch events and send them minutes later. A network partition might delay events. If you use processing time, your windowed aggregations will include events in the wrong window.

### Watermarks: Tracking Progress

A watermark is Flink's way of saying: "I believe all events with timestamps up to time T have arrived."

```
Events arriving (event time shown):

  14:05:01  14:05:03  14:05:02  14:05:05  14:05:04  14:05:07
     │         │         │         │         │         │
     ▼         ▼         ▼         ▼         ▼         ▼

Watermark progression:
  W(14:05:00)          W(14:05:01)          W(14:05:05)
  "All events          "All events          "All events
   before 14:05:00      before 14:05:01      before 14:05:05
   have arrived"        have arrived"        have arrived"
```

**Watermark strategies:**

```java
// Bounded out-of-orderness: allow up to 5 seconds of late data
WatermarkStrategy
    .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(5))
    .withTimestampAssigner((event, timestamp) -> event.getTimestamp());

// Monotonously increasing timestamps (no late data expected)
WatermarkStrategy
    .<Event>forMonotonousTimestamps()
    .withTimestampAssigner((event, timestamp) -> event.getTimestamp());
```

When the watermark passes the end of a window, Flink fires that window and emits results. Late events (events with timestamps before the watermark) are either dropped or handled by a side output.

---

## Windows: Slicing Unbounded Data

Windows group events into finite chunks for aggregation.

### Window Types

```
TUMBLING WINDOW (fixed, non-overlapping):
|  Window 1  |  Window 2  |  Window 3  |
|  0-5 min   |  5-10 min  | 10-15 min  |

SLIDING WINDOW (fixed, overlapping):
|  Window 1 (0-10 min)   |
     |  Window 2 (5-15 min)   |
          |  Window 3 (10-20 min)  |
(window size = 10 min, slide = 5 min)

SESSION WINDOW (dynamic, gap-based):
|  Session 1  |        |  Session 2       |  |  Session 3  |
events: ●●●●           ●●●●●●●●●             ●●●
(gap timeout = 5 min)

GLOBAL WINDOW (single window per key):
|  All events for key  ───────────────────────────→ |
(requires custom trigger)
```

### Flink SQL Example

Flink SQL makes windowed aggregations accessible without Java/Scala code:

```sql
-- Tumbling window: count events per URL every 5 minutes
SELECT
    url,
    TUMBLE_START(event_time, INTERVAL '5' MINUTE) AS window_start,
    TUMBLE_END(event_time, INTERVAL '5' MINUTE) AS window_end,
    COUNT(*) AS page_views,
    COUNT(DISTINCT user_id) AS unique_visitors
FROM page_events
GROUP BY
    url,
    TUMBLE(event_time, INTERVAL '5' MINUTE);

-- Sliding window: moving average over 1 hour, updated every 5 minutes
SELECT
    sensor_id,
    HOP_START(event_time, INTERVAL '5' MINUTE, INTERVAL '1' HOUR) AS window_start,
    AVG(temperature) AS avg_temp,
    MAX(temperature) AS max_temp,
    MIN(temperature) AS min_temp
FROM sensor_readings
GROUP BY
    sensor_id,
    HOP(event_time, INTERVAL '5' MINUTE, INTERVAL '1' HOUR);
```

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Using processing time for business logic | Simpler to implement | Use event time with watermarks. Processing time gives inconsistent results on replays |
| Setting parallelism higher than Kafka partitions | "More parallelism = faster" | Flink can only read from as many Kafka partitions as you have parallel readers. Extra parallelism is wasted |
| Not configuring checkpoint storage durably | Works on local disk in dev | Use S3/GCS/HDFS for checkpoints. Local disk means state is lost on Pod restart |
| Putting too much state on heap (HashMapStateBackend) | Default backend, works fine initially | Switch to RocksDB for any state larger than 500 MB. JVM GC pauses will destroy latency |
| Skipping savepoints during upgrades | "Checkpoints will handle it" | Checkpoints are tied to a specific job version. Savepoints are portable across versions |
| Ignoring backpressure signals | "Everything seems to be running" | Monitor backpressure metrics. Sustained backpressure means your sink or an operator is the bottleneck |
| Using a single global parallelism for all operators | Simplicity | Set parallelism per operator. Sources might need 12 but sinks only 4 |
| Not handling late data | "Events always arrive on time" | Define a late data side output. Even 0.1% late events corrupt aggregation results over time |
| Deploying in Session Mode for production jobs | Easy to submit jobs interactively | Use Application Mode. Session clusters share resources and a bad job can crash the whole cluster |

---

## Quiz

**Question 1:** What is the difference between a checkpoint and a savepoint?

<details>
<summary>Show Answer</summary>

**Checkpoints** are automatic, periodic, lightweight snapshots taken by Flink for failure recovery. They are tied to a specific job graph and may use incremental state. Flink manages their lifecycle (creation, deletion).

**Savepoints** are manually triggered, full snapshots designed for operational use cases: job upgrades, migration, A/B testing. They are portable across job versions (as long as state schema is compatible) and must be explicitly managed by the user.

Key difference: checkpoints are for crash recovery, savepoints are for planned operations.

</details>

**Question 2:** Why does Flink use watermarks, and what problem do they solve?

<details>
<summary>Show Answer</summary>

Watermarks solve the problem of **out-of-order event arrival**. In the real world, events generated at time T do not arrive at the processing system at time T — network delays, batching, and retries cause events to arrive late and out of order.

A watermark W(T) tells Flink: "I believe all events with timestamps <= T have arrived." When a watermark passes the end of a window, Flink knows it is safe to compute and emit results for that window.

Without watermarks, Flink would either have to wait indefinitely (never emitting results) or use processing time (producing incorrect results for late events).

</details>

**Question 3:** A Flink job reads from a Kafka topic with 24 partitions. You set the job's parallelism to 36. How many source operator instances actually process data?

<details>
<summary>Show Answer</summary>

Only **24 source operator instances** will process data. Each Kafka partition can only be assigned to one parallel source instance. The remaining 12 instances will be idle with no partitions assigned. This wastes resources. You should set the source operator's parallelism to match (or be less than) the number of Kafka partitions. Downstream operators can have different parallelism if needed.

</details>

**Question 4:** When should you use RocksDB state backend instead of the HashMapStateBackend?

<details>
<summary>Show Answer</summary>

Use **RocksDB** when:
- State size exceeds a few hundred MB (RocksDB stores state on disk with an in-memory cache, so it is not limited by JVM heap)
- You need incremental checkpoints (only changed state is checkpointed, reducing checkpoint size and duration)
- You are running in production (RocksDB is more predictable under load)

Use **HashMapStateBackend** when:
- State is small (< 500 MB) and fits comfortably in memory
- You need minimum latency (no disk I/O for state access)
- You are developing or testing locally

</details>

**Question 5:** Explain the difference between tumbling and sliding windows. Give a use case for each.

<details>
<summary>Show Answer</summary>

**Tumbling windows** are fixed-size, non-overlapping time intervals. Each event belongs to exactly one window. Use case: computing hourly revenue — each hour is a distinct window, and every transaction counts toward exactly one hour.

**Sliding windows** are fixed-size but overlapping. Each event can belong to multiple windows. Use case: computing a 1-hour moving average updated every 5 minutes — this creates a new window every 5 minutes, each covering the last 60 minutes, so events near window boundaries appear in multiple windows.

The key difference: tumbling windows partition time, sliding windows sample time.

</details>

**Question 6:** What happens to in-flight state when a Flink TaskManager crashes and restarts?

<details>
<summary>Show Answer</summary>

When a TaskManager crashes:
1. The JobManager detects the failure (via heartbeat timeout).
2. The JobManager cancels all tasks in the affected job.
3. The JobManager restores the job from the **last completed checkpoint** — all operator state is reloaded from durable storage (S3/GCS/HDFS).
4. Source operators (e.g., Kafka consumer) rewind to the offsets recorded in that checkpoint.
5. Events between the checkpoint and the crash are **replayed** from Kafka.
6. Processing continues from the restored state.

With `EXACTLY_ONCE` checkpointing, no events are lost or double-counted. The recovery time depends on state size and checkpoint storage throughput.

</details>

---

## Hands-On Exercise: Flink Consuming from Kafka with Windowed Aggregations

### Objective

Deploy a Flink job that reads events from a Kafka topic, performs windowed aggregations using event time, and writes results to an output topic. You will observe checkpointing, watermark progression, and the effect of late data.

### Environment Setup

```bash
# Create cluster
kind create cluster --name flink-lab

# Install Strimzi and create a Kafka cluster
kubectl create namespace kafka
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
kubectl -n kafka wait --for=condition=Available \
  deployment/strimzi-cluster-operator --timeout=180s
```

```yaml
# kafka-for-flink.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: combined
  namespace: kafka
  labels:
    strimzi.io/cluster: flink-lab
spec:
  replicas: 1
  roles:
    - controller
    - broker
  storage:
    type: ephemeral
  resources:
    requests:
      cpu: 250m
      memory: 1Gi
    limits:
      memory: 1Gi
---
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: flink-lab
  namespace: kafka
  annotations:
    strimzi.io/kraft: enabled
    strimzi.io/node-pools: enabled
spec:
  kafka:
    version: 3.9.0
    metadataVersion: "3.9"
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      auto.create.topics.enable: false
      num.partitions: 3
      default.replication.factor: 1
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
  entityOperator:
    topicOperator: {}
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: sensor-readings
  namespace: kafka
  labels:
    strimzi.io/cluster: flink-lab
spec:
  partitions: 3
  replicas: 1
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: sensor-aggregates
  namespace: kafka
  labels:
    strimzi.io/cluster: flink-lab
spec:
  partitions: 3
  replicas: 1
```

```bash
kubectl apply -f kafka-for-flink.yaml
kubectl -n kafka wait kafka/flink-lab --for=condition=Ready --timeout=300s
```

### Step 1: Install the Flink Kubernetes Operator

```bash
# Install cert-manager (required by Flink Operator webhooks)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.3/cert-manager.yaml
kubectl -n cert-manager wait --for=condition=Available deployment --all --timeout=120s

# Install Flink Operator
kubectl create namespace flink
helm repo add flink-operator https://downloads.apache.org/flink/flink-kubernetes-operator-1.10.0/
helm repo update
helm install flink-kubernetes-operator flink-operator/flink-kubernetes-operator \
  --namespace flink \
  --set webhook.create=true

kubectl -n flink wait --for=condition=Available \
  deployment/flink-kubernetes-operator --timeout=120s
```

### Step 2: Create the Flink Session Cluster and Submit a SQL Job

Since the Flink Kubernetes Operator manages job lifecycle, we deploy a **session cluster** and then use the Flink SQL Client to submit our streaming query.

```yaml
# flink-session.yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: sensor-aggregator
  namespace: flink
spec:
  image: flink:1.20-java17
  flinkVersion: v1_20
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "2"
    state.backend.type: hashmap
    execution.checkpointing.interval: "30000"
    execution.checkpointing.mode: EXACTLY_ONCE
    state.checkpoints.num-retained: "3"
    rest.flamegraph.enabled: "true"
  serviceAccount: flink
  jobManager:
    resource:
      memory: "1024m"
      cpu: 0.5
  taskManager:
    resource:
      memory: "2048m"
      cpu: 1
    replicas: 2
```

```bash
# Create RBAC for Flink
kubectl -n flink create serviceaccount flink
kubectl create clusterrolebinding flink-role-binding \
  --clusterrole=edit --serviceaccount=flink:flink

kubectl apply -f flink-session.yaml

# Wait for the session cluster to be ready
kubectl -n flink get flinkdeployment sensor-aggregator -w
# Wait until READY status shows True
```

Next, download the Kafka SQL connector JAR into the Flink cluster and submit the SQL job:

```bash
# Copy the Kafka connector into the running JobManager
FLINK_JM=$(kubectl -n flink get pod -l component=jobmanager,app=sensor-aggregator -o jsonpath='{.items[0].metadata.name}')

# Download the Flink SQL Kafka connector into the JobManager
kubectl -n flink exec $FLINK_JM -- bash -c '
  wget -q -P /opt/flink/lib/ \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar &&
  echo "Kafka connector downloaded"
'

# Submit the SQL job via the SQL Client
kubectl -n flink exec -it $FLINK_JM -- /opt/flink/bin/sql-client.sh embedded -e "
CREATE TABLE sensor_readings (
    sensor_id STRING,
    temperature DOUBLE,
    humidity DOUBLE,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'sensor-readings',
    'properties.bootstrap.servers' = 'flink-lab-kafka-bootstrap.kafka.svc.cluster.local:9092',
    'properties.group.id' = 'flink-sensor-aggregator',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);

CREATE TABLE sensor_aggregates (
    sensor_id STRING,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    avg_temperature DOUBLE,
    max_temperature DOUBLE,
    min_temperature DOUBLE,
    avg_humidity DOUBLE,
    reading_count BIGINT
) WITH (
    'connector' = 'kafka',
    'topic' = 'sensor-aggregates',
    'properties.bootstrap.servers' = 'flink-lab-kafka-bootstrap.kafka.svc.cluster.local:9092',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);

SET 'parallelism.default' = '3';
SET 'pipeline.name' = 'sensor-aggregator';

INSERT INTO sensor_aggregates
SELECT
    sensor_id,
    window_start,
    window_end,
    AVG(temperature) AS avg_temperature,
    MAX(temperature) AS max_temperature,
    MIN(temperature) AS min_temperature,
    AVG(humidity) AS avg_humidity,
    COUNT(*) AS reading_count
FROM TABLE(
    TUMBLE(TABLE sensor_readings, DESCRIPTOR(event_time), INTERVAL '1' MINUTE)
)
GROUP BY
    sensor_id, window_start, window_end;
"
```

### Step 3: Produce Test Events

```bash
# Generate sensor readings with event-time timestamps
kubectl -n kafka run producer --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.9.0 -- bash -c '
NOW=$(date +%s)
for i in $(seq 1 200); do
  SENSOR="sensor-$((RANDOM % 5 + 1))"
  TEMP=$(echo "20 + $((RANDOM % 15))" | bc)
  HUMID=$(echo "40 + $((RANDOM % 40))" | bc)
  # Vary event times within a 5-minute window
  EVENT_TS=$((NOW - RANDOM % 300))
  ISO_TS=$(date -u -d @$EVENT_TS +"%Y-%m-%dT%H:%M:%S.000" 2>/dev/null || date -u -r $EVENT_TS +"%Y-%m-%dT%H:%M:%S.000")
  echo "{\"sensor_id\":\"$SENSOR\",\"temperature\":$TEMP,\"humidity\":$HUMID,\"event_time\":\"$ISO_TS\"}"
done | bin/kafka-console-producer.sh \
  --bootstrap-server flink-lab-kafka-bootstrap:9092 \
  --topic sensor-readings
echo "Produced 200 events"
'
```

### Step 4: Consume Aggregated Results

```bash
# Read the aggregated output
kubectl -n kafka run consumer --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.9.0 -- \
  bin/kafka-console-consumer.sh \
    --bootstrap-server flink-lab-kafka-bootstrap:9092 \
    --topic sensor-aggregates \
    --from-beginning \
    --max-messages 20

# You should see JSON objects with per-sensor, per-minute aggregations
```

### Step 5: Monitor the Flink Job

```bash
# Port-forward to the Flink Web UI
kubectl -n flink port-forward svc/sensor-aggregator-rest 8081:8081 &

# Open http://localhost:8081 in your browser
# Explore:
# - Running Jobs → click on your job → see the execution graph
# - Checkpoints tab → verify checkpoints are completing
# - Backpressure tab → check for bottlenecks
```

### Step 6: Clean Up

```bash
kubectl -n flink delete flinkdeployment sensor-aggregator
helm -n flink uninstall flink-kubernetes-operator
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.3/cert-manager.yaml
kubectl -n kafka delete kafka flink-lab
kubectl -n kafka delete kafkanodepool combined
kubectl delete -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
kubectl delete namespace kafka flink
kind delete cluster --name flink-lab
```

### Success Criteria

You have completed this exercise when you:
- [ ] Deployed Kafka with input and output topics
- [ ] Installed the Flink Kubernetes Operator
- [ ] Deployed a Flink SQL job that reads from Kafka
- [ ] Produced 200+ test events with event-time timestamps
- [ ] Consumed and verified windowed aggregation results
- [ ] Observed the Flink Web UI (execution graph, checkpoints)

---

## Key Takeaways

1. **Flink is streaming-first** — Batch is treated as a special case of streaming, not the other way around. This gives Flink natural advantages for unbounded data processing.
2. **Event time and watermarks are essential** — Without them, out-of-order events produce incorrect results. Always use event time for business-critical aggregations.
3. **Checkpoints provide exactly-once guarantees** — Combined with Kafka's offset management, Flink can guarantee that every event is processed exactly once, even across failures.
4. **The Flink Kubernetes Operator handles lifecycle** — Savepoints, upgrades, scaling, and recovery are automated through Custom Resources, enabling GitOps workflows.
5. **State backend choice matters** — RocksDB for production (handles TB of state), HashMapStateBackend for development (lower latency, limited by heap).
6. **Parallelism must match your sources** — Setting parallelism higher than Kafka partitions wastes resources.

---

## Further Reading

**Books:**
- **"Stream Processing with Apache Flink"** — Fabian Hueske, Vasiliki Kalavri (O'Reilly)
- **"Streaming Systems"** — Tyler Akidau, Slava Chernyak, Reuven Lax (O'Reilly) — The theoretical foundation

**Articles:**
- **"Flink Kubernetes Operator Documentation"** — Apache Flink (nightlies.apache.org/flink/flink-kubernetes-operator-docs-stable/)
- **"A Practical Guide to Broadcast State in Flink"** — Flink blog (flink.apache.org/posts)

**Talks:**
- **"Flink Forward"** — Annual conference with deep-dive talks (youtube.com/c/FlinkForward)
- **"Stateful Functions: Building General-Purpose Applications with Flink"** — Stephan Ewen, Flink Forward 2023

---

## Summary

Apache Flink is the gold standard for stream processing because it was designed for streaming from the ground up. Its event-time processing, watermark-based progress tracking, and checkpoint-based exactly-once guarantees make it the right choice for any application where timeliness and correctness both matter.

On Kubernetes, the Flink Operator transforms Flink from a complex distributed system into a declarative workload. You describe what you want — a streaming job with specific parallelism, state backend, and checkpointing configuration — and the operator handles the rest: deployment, scaling, upgrades, and failure recovery.

The combination of Kafka (for durable event transport) and Flink (for stateful stream processing) forms the backbone of modern real-time data platforms.

---

## Next Module

Continue to [Module 1.4: Batch Processing & Apache Spark on Kubernetes](module-1.4-spark/) to learn how to handle large-scale batch processing — the other half of the data processing story.

---

*"Streaming is not the future of data processing. It is the present. Batch is just streaming that waits."* — Tyler Akidau

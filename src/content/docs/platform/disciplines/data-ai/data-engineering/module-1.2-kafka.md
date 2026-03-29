---
title: "Module 1.2: Apache Kafka on Kubernetes (Strimzi)"
slug: platform/disciplines/data-ai/data-engineering/module-1.2-kafka
sidebar:
  order: 3
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 3.5 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1 — Stateful Workloads & Storage Deep Dive](module-1.1-stateful-workloads/) — StatefulSets, Operators, storage fundamentals
- **Required**: Understanding of distributed systems concepts (replication, partitioning, consensus)
- **Recommended**: Experience with any messaging or event system (RabbitMQ, SQS, Pub/Sub, etc.)
- **Recommended**: Familiarity with TLS certificates and mutual authentication concepts

---

## Why This Module Matters

Every modern data platform has Kafka at its center. Not sometimes — virtually always.

LinkedIn built Kafka in 2011 to solve a specific problem: connecting hundreds of microservices without point-to-point spaghetti. Today, over 80% of Fortune 100 companies run Kafka. Netflix processes 7 million events per second through it. The New York Times uses it to deliver articles in real time. Uber routes every trip through Kafka.

Running Kafka well is hard. Running Kafka on Kubernetes is harder — but also better, because Kubernetes solves Kafka's most painful operational challenges: broker replacement, rolling upgrades, certificate rotation, and configuration management.

The Strimzi Operator is the CNCF-incubating project that makes Kafka on Kubernetes a first-class experience. It manages the entire Kafka lifecycle through Kubernetes Custom Resources, turning what used to be weeks of manual work into a single YAML file.

This module teaches you to deploy, configure, secure, and operate a production-grade Kafka cluster on Kubernetes using Strimzi.

---

## Did You Know?

- **Kafka was named after the author Franz Kafka** because Jay Kreps, its creator, thought a system optimized for writing deserved a writer's name. The name has no deeper connection to Kafka's literary themes.
- **A single Kafka broker can sustain 800 MB/s of throughput** on appropriate hardware. That is roughly 2.8 TB per hour, per broker. Most performance problems are caused by misconfiguration, not Kafka's limits.
- **KRaft mode eliminates ZooKeeper entirely.** Since Kafka 3.3, the metadata quorum runs inside the brokers themselves using the Raft consensus protocol. Strimzi fully supports KRaft, and ZooKeeper-based deployments are now deprecated.

---

## Kafka Architecture: The 10-Minute Version

### Core Concepts

Kafka is a **distributed commit log**. Producers append messages to the end of the log. Consumers read from the log at their own pace. The log is durable, ordered, and replayable.

```
┌──────────────────────────────────────────────────────────────┐
│                    KAFKA CLUSTER                             │
│                                                              │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐               │
│  │ Broker 0 │     │ Broker 1 │     │ Broker 2 │              │
│  │          │     │          │     │          │               │
│  │ Topic A  │     │ Topic A  │     │ Topic A  │              │
│  │ Part 0 ★ │     │ Part 1 ★ │     │ Part 2 ★ │              │
│  │ Part 1   │     │ Part 2   │     │ Part 0   │              │
│  │          │     │          │     │          │               │
│  └─────────┘     └─────────┘     └─────────┘               │
│                                                              │
│  ★ = Partition Leader    (unmarked) = Follower replica       │
└──────────────────────────────────────────────────────────────┘
         ▲                                    │
         │           ┌────────────┐           │
    Producers ──────→│  Network   │──────→ Consumers
                     └────────────┘
```

**Key terms:**

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| **Broker** | A Kafka server process | A librarian managing shelves |
| **Topic** | A named stream of records | A bookshelf for one subject |
| **Partition** | An ordered, immutable log within a topic | A single shelf on the bookshelf |
| **Replica** | A copy of a partition on another broker | A backup copy of that shelf |
| **Leader** | The replica that handles reads/writes | The primary librarian for that shelf |
| **Consumer Group** | A set of consumers sharing work | A reading club splitting chapters |
| **Offset** | Position in the partition log | A bookmark |

### Why Partitions Matter

Partitions are Kafka's unit of parallelism. A topic with 12 partitions can be consumed by up to 12 consumers in a group simultaneously. More partitions = more throughput, but also more overhead.

```
Topic: user-events (3 partitions, replication factor 2)

Partition 0: [msg1] [msg2] [msg3] [msg4] [msg5] ───→
Partition 1: [msg6] [msg7] [msg8] [msg9]         ───→
Partition 2: [msg10] [msg11] [msg12]              ───→

Consumer Group "analytics":
  Consumer A reads ← Partition 0
  Consumer B reads ← Partition 1
  Consumer C reads ← Partition 2
```

Messages within a partition are strictly ordered. Messages across partitions have no ordering guarantee. If you need ordering for a specific entity (e.g., all events for user-123), use a partition key — Kafka hashes the key to determine the partition.

### KRaft: Kafka Without ZooKeeper

Until Kafka 3.3, every Kafka cluster required a separate ZooKeeper ensemble to manage metadata (broker registration, topic configuration, partition leadership). This doubled operational complexity.

KRaft (Kafka Raft) moves metadata management inside the Kafka brokers themselves:

```
BEFORE (ZooKeeper mode):                 AFTER (KRaft mode):
┌───────────────────────┐               ┌───────────────────────┐
│    ZooKeeper Cluster  │               │    Kafka Cluster      │
│  ┌────┐┌────┐┌────┐  │               │                       │
│  │ ZK ││ ZK ││ ZK │  │               │  ┌────────────────┐   │
│  └────┘└────┘└────┘  │               │  │ Controller     │   │
└───────┬───────────────┘               │  │ Quorum (KRaft) │   │
        │                               │  │ Built into     │   │
┌───────▼───────────────┐               │  │ brokers        │   │
│    Kafka Cluster      │               │  └────────────────┘   │
│  ┌────┐┌────┐┌────┐  │               │  ┌────┐┌────┐┌────┐  │
│  │ B0 ││ B1 ││ B2 │  │               │  │ B0 ││ B1 ││ B2 │  │
│  └────┘└────┘└────┘  │               │  └────┘└────┘└────┘  │
└───────────────────────┘               └───────────────────────┘

5+ processes to manage                  3 processes to manage
```

**KRaft advantages:**
- Simpler operations (no ZooKeeper to babysit)
- Faster controller failover (seconds vs. minutes)
- Better scalability (millions of partitions)
- Unified security model

Strimzi supports KRaft as the default deployment mode. All examples in this module use KRaft.

---

## Strimzi: Kafka's Kubernetes Operator

### What Strimzi Manages

Strimzi is not just a Helm chart that deploys Kafka. It is a full lifecycle manager that handles:

| Lifecycle Phase | What Strimzi Does |
|----------------|-------------------|
| **Deployment** | Creates StatefulSets, Services, ConfigMaps, NetworkPolicies |
| **Configuration** | Generates broker configs, validates settings, applies rolling changes |
| **Security** | Auto-generates and rotates TLS certificates, manages SASL/SCRAM users |
| **Scaling** | Adds/removes brokers, triggers partition rebalancing |
| **Upgrades** | Rolling broker upgrades with automatic protocol version negotiation |
| **Monitoring** | Deploys JMX exporters, creates Prometheus ServiceMonitors |
| **Connectivity** | Configures external access via NodePort, LoadBalancer, Ingress, or Route |

### Strimzi Custom Resources

Strimzi introduces several CRDs:

```
Kafka                    ─── The Kafka cluster itself
KafkaNodePool            ─── Groups of broker nodes with distinct configs
KafkaTopic               ─── Managed Kafka topics
KafkaUser                ─── Managed Kafka users with ACLs
KafkaConnect             ─── Kafka Connect clusters
KafkaConnector           ─── Individual connectors within a Connect cluster
KafkaMirrorMaker2        ─── Cross-cluster replication
KafkaBridge              ─── HTTP bridge for REST-based access
KafkaRebalance           ─── Cruise Control rebalancing proposals
```

### Deploying Strimzi

```bash
# Install Strimzi Operator (latest stable)
kubectl create namespace kafka
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

# Wait for the operator to be ready
kubectl -n kafka wait --for=condition=Available \
  deployment/strimzi-cluster-operator --timeout=180s
```

### A Production-Grade Kafka Cluster

```yaml
# kafka-cluster.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: broker
  namespace: kafka
  labels:
    strimzi.io/cluster: production
spec:
  replicas: 3
  roles:
    - broker
  storage:
    type: persistent-claim
    size: 100Gi
    class: fast-ssd
    deleteClaim: false
  resources:
    requests:
      cpu: "2"
      memory: 8Gi
    limits:
      memory: 8Gi
  template:
    pod:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  strimzi.io/cluster: production
                  strimzi.io/kind: Kafka
              topologyKey: kubernetes.io/hostname
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: controller
  namespace: kafka
  labels:
    strimzi.io/cluster: production
spec:
  replicas: 3
  roles:
    - controller
  storage:
    type: persistent-claim
    size: 20Gi
    class: fast-ssd
    deleteClaim: false
  resources:
    requests:
      cpu: "1"
      memory: 4Gi
    limits:
      memory: 4Gi
---
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: production
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
      - name: tls
        port: 9093
        type: internal
        tls: true
        authentication:
          type: tls
      - name: external
        port: 9094
        type: nodeport
        tls: true
        authentication:
          type: scram-sha-512
    config:
      # Replication settings
      default.replication.factor: 3
      min.insync.replicas: 2
      # Performance tuning
      num.network.threads: 8
      num.io.threads: 16
      socket.send.buffer.bytes: 102400
      socket.receive.buffer.bytes: 102400
      socket.request.max.bytes: 104857600
      # Log settings
      log.retention.hours: 168            # 7 days
      log.segment.bytes: 1073741824       # 1 GB segments
      log.retention.check.interval.ms: 300000
      # Topic defaults
      num.partitions: 12
      auto.create.topics.enable: false    # Explicit topic creation only
    metricsConfig:
      type: jmxPrometheusExporter
      valueFrom:
        configMapKeyRef:
          name: kafka-metrics
          key: kafka-metrics-config.yml
  entityOperator:
    topicOperator:
      resources:
        requests:
          cpu: 250m
          memory: 512Mi
        limits:
          memory: 512Mi
    userOperator:
      resources:
        requests:
          cpu: 250m
          memory: 512Mi
        limits:
          memory: 512Mi
```

**Key configuration decisions explained:**

| Setting | Value | Why |
|---------|-------|-----|
| `default.replication.factor: 3` | 3 copies of every partition | Survives loss of 1 broker without data loss |
| `min.insync.replicas: 2` | At least 2 replicas must acknowledge writes | Prevents data loss when one replica is down |
| `auto.create.topics.enable: false` | Topics must be created explicitly | Prevents typos from silently creating garbage topics |
| `log.retention.hours: 168` | 7-day retention | Balance between replay capability and disk usage |
| `num.partitions: 12` | Default 12 partitions per topic | Reasonable parallelism without excessive overhead |

---

## High Throughput vs Low Latency Configuration

Kafka can be tuned for throughput or latency. These are opposing forces.

### High Throughput Configuration

When you need maximum messages per second (log aggregation, analytics pipelines):

```yaml
# In the Kafka CR spec.kafka.config
config:
  # Producer-side (configure in producer clients)
  # batch.size: 65536              # 64 KB batches
  # linger.ms: 50                  # Wait 50ms to fill batches
  # compression.type: lz4          # Compress for throughput

  # Broker-side
  num.network.threads: 8           # Handle more concurrent connections
  num.io.threads: 16               # More disk I/O threads
  socket.send.buffer.bytes: 1048576    # 1 MB send buffer
  socket.receive.buffer.bytes: 1048576 # 1 MB receive buffer
  log.flush.interval.messages: 50000   # Batch disk flushes
  replica.fetch.max.bytes: 10485760    # 10 MB replica fetch
```

### Low Latency Configuration

When you need sub-10ms end-to-end latency (payment processing, real-time bidding):

```yaml
config:
  # Producer-side (configure in producer clients)
  # batch.size: 16384             # Small batches
  # linger.ms: 0                  # Send immediately
  # acks: 1                       # Acknowledge after leader write only
  # compression.type: none        # No compression overhead

  # Broker-side
  num.network.threads: 16         # More threads for responsiveness
  num.io.threads: 8               # Fewer I/O threads, less contention
  socket.send.buffer.bytes: 65536
  socket.receive.buffer.bytes: 65536
  log.flush.interval.messages: 1  # Flush every message (if durability needed)
```

### The Tradeoff Spectrum

```
HIGH THROUGHPUT ◄──────────────────────────────► LOW LATENCY

Large batches                            Small/no batches
linger.ms = 50-200                       linger.ms = 0
Compression: lz4/zstd                    No compression
acks = 1                                 acks = all
Bigger buffers                           Smaller buffers
Fewer, larger requests                   Many, smaller requests
```

---

## Schema Management

### Why Schemas Matter

Without schemas, producers and consumers are in a trust-based relationship. Producer sends JSON with field `user_id`. Consumer expects `userId`. Things break silently.

Schemas enforce a contract between producers and consumers:

```
Producer ──→ Schema Registry ──→ Consumer
   │              │                  │
   │  "Does my    │  "Is this       │  "What format
   │   message    │   compatible    │   should I
   │   match?"    │   with v1?"     │   expect?"
```

### Apicurio Registry on Kubernetes

Apicurio Registry is the open-source schema registry that works with Kafka (alternative to Confluent Schema Registry):

```yaml
# apicurio-registry.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apicurio-registry
  namespace: kafka
spec:
  replicas: 2
  selector:
    matchLabels:
      app: apicurio-registry
  template:
    metadata:
      labels:
        app: apicurio-registry
    spec:
      containers:
        - name: registry
          image: apicurio/apicurio-registry:3.0.4
          ports:
            - containerPort: 8080
          env:
            - name: APICURIO_STORAGE_KIND
              value: kafkasql
            - name: APICURIO_KAFKASQL_BOOTSTRAP_SERVERS
              value: production-kafka-bootstrap.kafka.svc.cluster.local:9092
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              memory: 512Mi
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: apicurio-registry
  namespace: kafka
spec:
  selector:
    app: apicurio-registry
  ports:
    - port: 8080
      targetPort: 8080
```

### Compatibility Modes

| Mode | Rule | When To Use |
|------|------|-------------|
| **BACKWARD** | New schema can read old data | Default. Consumers upgrade first |
| **FORWARD** | Old schema can read new data | Producers upgrade first |
| **FULL** | Both backward and forward compatible | Most restrictive, safest |
| **NONE** | No compatibility check | Never in production |

---

## Kafka Connect: Moving Data In and Out

Kafka Connect is the framework for streaming data between Kafka and external systems without writing code.

### Deploying Kafka Connect with Strimzi

```yaml
# kafka-connect.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnect
metadata:
  name: data-connect
  namespace: kafka
  annotations:
    strimzi.io/use-connector-resources: "true"  # Enable KafkaConnector CRs
spec:
  version: 3.9.0
  replicas: 3
  bootstrapServers: production-kafka-bootstrap:9093
  tls:
    trustedCertificates:
      - secretName: production-cluster-ca-cert
        pattern: "*.crt"
  config:
    group.id: data-connect-cluster
    offset.storage.topic: connect-offsets
    config.storage.topic: connect-configs
    status.storage.topic: connect-status
    offset.storage.replication.factor: 3
    config.storage.replication.factor: 3
    status.storage.replication.factor: 3
    key.converter: org.apache.kafka.connect.json.JsonConverter
    value.converter: org.apache.kafka.connect.json.JsonConverter
    key.converter.schemas.enable: false
    value.converter.schemas.enable: false
  build:
    output:
      type: docker
      image: my-registry.io/kafka-connect:latest
      pushSecret: registry-credentials
    plugins:
      - name: debezium-postgres
        artifacts:
          - type: tgz
            url: https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/2.7.3.Final/debezium-connector-postgres-2.7.3.Final-plugin.tar.gz
      - name: camel-s3
        artifacts:
          - type: tgz
            url: https://repo1.maven.org/maven2/org/apache/camel/kafkaconnector/camel-aws-s3-sink-kafka-connector/4.8.2/camel-aws-s3-sink-kafka-connector-4.8.2-package.tar.gz
  resources:
    requests:
      cpu: "1"
      memory: 2Gi
    limits:
      memory: 2Gi
```

### Example: CDC with Debezium

Change Data Capture (CDC) streams database changes to Kafka in real time:

```yaml
# debezium-connector.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: postgres-cdc
  namespace: kafka
  labels:
    strimzi.io/cluster: data-connect
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  tasksMax: 1
  config:
    database.hostname: postgres.default.svc.cluster.local
    database.port: 5432
    database.user: debezium
    database.password: "${file:/opt/kafka/external-configuration/db-credentials/password}"
    database.dbname: orders
    topic.prefix: cdc
    plugin.name: pgoutput
    publication.autocreate.mode: filtered
    slot.name: debezium_slot
    table.include.list: "public.orders,public.customers"
    transforms: unwrap
    transforms.unwrap.type: io.debezium.transforms.ExtractNewRecordState
    transforms.unwrap.drop.tombstones: false
    heartbeat.interval.ms: 10000
```

This creates topics `cdc.public.orders` and `cdc.public.customers` with every INSERT, UPDATE, and DELETE streamed in real time.

---

## Securing Kafka: TLS, mTLS, and SCRAM

### Security Layers

```
┌─────────────────────────────────────────────────┐
│              KAFKA SECURITY STACK               │
├─────────────────────────────────────────────────┤
│  Authorization   │  ACLs: who can do what       │
├──────────────────┼──────────────────────────────┤
│  Authentication  │  TLS, SCRAM, OAuth           │
├──────────────────┼──────────────────────────────┤
│  Encryption      │  TLS for data in transit     │
├──────────────────┼──────────────────────────────┤
│  Network         │  NetworkPolicies             │
└─────────────────────────────────────────────────┘
```

### Strimzi TLS: Automatic Certificate Management

Strimzi automatically generates a CA and issues certificates:

```
┌──────────────────────────────────────────┐
│         Strimzi Certificate Chain        │
│                                          │
│  Cluster CA ──→ Broker Certificates      │
│             ──→ Controller Certificates  │
│             ──→ Entity Operator Cert     │
│                                          │
│  Client CA  ──→ KafkaUser Certificates   │
└──────────────────────────────────────────┘
```

Certificates are stored as Kubernetes Secrets and automatically rotated by the operator.

### Creating Authenticated Users with ACLs

```yaml
# kafka-user-producer.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: events-producer
  namespace: kafka
  labels:
    strimzi.io/cluster: production
spec:
  authentication:
    type: scram-sha-512
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: user-events
          patternType: literal
        operations:
          - Write
          - Describe
        host: "*"
      - resource:
          type: topic
          name: user-events
          patternType: literal
        operations:
          - Create
        host: "*"
---
# kafka-user-consumer.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: analytics-consumer
  namespace: kafka
  labels:
    strimzi.io/cluster: production
spec:
  authentication:
    type: tls
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: user-events
          patternType: literal
        operations:
          - Read
          - Describe
        host: "*"
      - resource:
          type: group
          name: analytics-
          patternType: prefix
        operations:
          - Read
        host: "*"
```

Strimzi creates a Secret for each user containing the credentials:
- **SCRAM**: Secret contains `password` and `sasl.jaas.config`
- **TLS**: Secret contains `user.crt`, `user.key`, and `ca.crt`

### mTLS Client Configuration

```yaml
# Application Pod mounting mTLS credentials
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-consumer
  namespace: kafka
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytics-consumer
  template:
    metadata:
      labels:
        app: analytics-consumer
    spec:
      containers:
        - name: consumer
          image: my-registry.io/analytics-consumer:v1.4.0
          env:
            - name: KAFKA_BOOTSTRAP_SERVERS
              value: production-kafka-bootstrap.kafka.svc.cluster.local:9093
            - name: KAFKA_SECURITY_PROTOCOL
              value: SSL
            - name: KAFKA_SSL_TRUSTSTORE_LOCATION
              value: /etc/kafka/certs/ca.p12
            - name: KAFKA_SSL_TRUSTSTORE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: production-cluster-ca-cert
                  key: ca.password
            - name: KAFKA_SSL_KEYSTORE_LOCATION
              value: /etc/kafka/certs/user.p12
            - name: KAFKA_SSL_KEYSTORE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: analytics-consumer
                  key: user.password
          volumeMounts:
            - name: kafka-certs
              mountPath: /etc/kafka/certs
              readOnly: true
      volumes:
        - name: kafka-certs
          projected:
            sources:
              - secret:
                  name: production-cluster-ca-cert
                  items:
                    - key: ca.p12
                      path: ca.p12
              - secret:
                  name: analytics-consumer
                  items:
                    - key: user.p12
                      path: user.p12
```

---

## Managing Topics as Code

```yaml
# kafka-topics.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: user-events
  namespace: kafka
  labels:
    strimzi.io/cluster: production
spec:
  partitions: 24
  replicas: 3
  config:
    retention.ms: 604800000         # 7 days
    cleanup.policy: delete
    min.insync.replicas: 2
    compression.type: lz4
    max.message.bytes: 1048576      # 1 MB max message
    segment.bytes: 536870912        # 512 MB segments
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: user-events-dlq
  namespace: kafka
  labels:
    strimzi.io/cluster: production
spec:
  partitions: 6
  replicas: 3
  config:
    retention.ms: 2592000000        # 30 days (DLQ gets longer retention)
    cleanup.policy: delete
    min.insync.replicas: 2
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: user-profiles
  namespace: kafka
  labels:
    strimzi.io/cluster: production
spec:
  partitions: 12
  replicas: 3
  config:
    cleanup.policy: compact          # Keep latest value per key
    min.cleanable.dirty.ratio: 0.5
    delete.retention.ms: 86400000    # 1 day tombstone retention
    min.insync.replicas: 2
```

**Topic naming conventions** that prevent chaos:

| Pattern | Example | When |
|---------|---------|------|
| `domain.entity.event` | `payments.order.completed` | Domain events |
| `source.table` | `cdc.public.orders` | CDC topics |
| `topic-name-dlq` | `user-events-dlq` | Dead letter queues |
| `connect-offsets` | `connect-offsets` | Internal Connect topics |

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Setting partition count too low (1-3) | Underestimating future throughput | Start with 12-24 partitions. You can increase later but never decrease |
| Using `auto.create.topics.enable: true` | Convenient for development | Disable in production. Use KafkaTopic CRs for explicit management |
| Setting `acks=0` or `acks=1` for critical data | Chasing low latency | Use `acks=all` with `min.insync.replicas=2` for data you cannot afford to lose |
| Ignoring consumer lag monitoring | "It seems to be working" | Monitor consumer group lag. Growing lag is the first sign of a failing pipeline |
| Running Kafka with ZooKeeper in 2026 | Following outdated tutorials | Use KRaft mode. ZooKeeper is deprecated and will be removed |
| Not setting `podAntiAffinity` | Trusting the scheduler | Always spread brokers across nodes. Two brokers on one node = two failures at once |
| Using `replication.factor: 1` | Works fine in dev | In production, always replicate 3x with `min.insync.replicas: 2` |
| Skipping dead letter queues | "We'll handle errors later" | Set up DLQs from day one. Unprocessable messages will corrupt your pipeline silently |

---

## Quiz

**Question 1:** What is the relationship between partitions, consumer groups, and parallelism?

<details>
<summary>Show Answer</summary>

A partition can only be consumed by **one consumer within a consumer group** at a time. This means the maximum parallelism equals the number of partitions. If you have a topic with 12 partitions and a consumer group with 15 consumers, 3 consumers will be idle. If you have 12 partitions and 4 consumers, each consumer reads from 3 partitions.

Different consumer groups are independent — each group reads the full topic independently.

</details>

**Question 2:** Explain the difference between `cleanup.policy: delete` and `cleanup.policy: compact`.

<details>
<summary>Show Answer</summary>

- **delete**: Messages are removed after the retention period expires (e.g., after 7 days). This is suitable for event streams where you want a time-bounded window.
- **compact**: Kafka keeps only the **latest value for each key**. Older values for the same key are removed during log compaction. This is ideal for state/lookup data (user profiles, configuration) where you always want the latest version. Messages with a `null` value (tombstones) delete the key entirely after a configurable retention period.

</details>

**Question 3:** What happens when `min.insync.replicas: 2` and one of three brokers hosting a partition goes down?

<details>
<summary>Show Answer</summary>

With `replication.factor: 3` and `min.insync.replicas: 2`, losing one broker leaves 2 in-sync replicas. Since 2 >= `min.insync.replicas`, **producers with `acks=all` can still write successfully**. The partition remains fully functional for both reads and writes. If a second broker goes down, writes would be rejected with `NotEnoughReplicasException` because only 1 replica remains, which is less than the required 2.

</details>

**Question 4:** Why does Strimzi generate its own TLS certificates instead of relying on cert-manager?

<details>
<summary>Show Answer</summary>

Strimzi manages its own CA and certificate lifecycle for several reasons:
1. **Tight integration** — Broker certificates, inter-broker communication, and client certificates are all coordinated together.
2. **Automatic rotation** — Strimzi handles certificate renewal and rolling restarts automatically.
3. **No external dependencies** — The operator works out of the box without requiring cert-manager to be installed.

However, Strimzi **can** be configured to use externally provided certificates (including cert-manager-issued ones) if organizational policy requires a centralized CA.

</details>

**Question 5:** Why should `auto.create.topics.enable` be set to `false` in production?

<details>
<summary>Show Answer</summary>

When `auto.create.topics.enable` is `true`, any producer that writes to a non-existent topic automatically creates it with default settings. This is dangerous because:
1. **Typos create garbage topics** — Writing to `user-evnets` instead of `user-events` silently creates a new topic.
2. **Default settings are wrong** — Auto-created topics use default partition count and replication factor, which may not match requirements.
3. **No governance** — Teams lose visibility into what topics exist and why.
4. **Resource waste** — Phantom topics consume broker memory and disk.

Use KafkaTopic CRs for declarative topic management instead.

</details>

---

## Hands-On Exercise: Multi-Broker Kafka with Strimzi + Producer/Consumer Benchmarks

### Objective

Deploy a 3-broker Kafka cluster using Strimzi in KRaft mode, create topics, run producer and consumer performance benchmarks, and observe the impact of different configurations on throughput and latency.

### Environment Setup

```bash
# Create a kind cluster with enough resources
kind create cluster --name kafka-lab

# Install Strimzi Operator
kubectl create namespace kafka
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
kubectl -n kafka wait --for=condition=Available \
  deployment/strimzi-cluster-operator --timeout=180s
```

### Step 1: Deploy the Kafka Cluster

```yaml
# kafka-lab-cluster.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: combined
  namespace: kafka
  labels:
    strimzi.io/cluster: lab
spec:
  replicas: 3
  roles:
    - controller
    - broker
  storage:
    type: persistent-claim
    size: 10Gi
    deleteClaim: true
  resources:
    requests:
      cpu: 500m
      memory: 2Gi
    limits:
      memory: 2Gi
---
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: lab
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
      default.replication.factor: 3
      min.insync.replicas: 2
      auto.create.topics.enable: false
      num.partitions: 6
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
  entityOperator:
    topicOperator: {}
```

```bash
kubectl apply -f kafka-lab-cluster.yaml
# Wait for all 3 brokers to be ready (this takes 3-5 minutes)
kubectl -n kafka wait kafka/lab --for=condition=Ready --timeout=300s
```

### Step 2: Create Benchmark Topics

```yaml
# benchmark-topics.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: benchmark-throughput
  namespace: kafka
  labels:
    strimzi.io/cluster: lab
spec:
  partitions: 12
  replicas: 3
  config:
    retention.ms: 3600000
    min.insync.replicas: 2
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: benchmark-latency
  namespace: kafka
  labels:
    strimzi.io/cluster: lab
spec:
  partitions: 6
  replicas: 3
  config:
    retention.ms: 3600000
    min.insync.replicas: 2
```

```bash
kubectl apply -f benchmark-topics.yaml
```

### Step 3: Run Producer Throughput Benchmark

```bash
# High throughput producer benchmark
# 1 million messages, 1 KB each, batched
kubectl -n kafka run producer-throughput --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.9.0 -- \
  bin/kafka-producer-perf-test.sh \
    --topic benchmark-throughput \
    --throughput -1 \
    --num-records 1000000 \
    --record-size 1024 \
    --producer-props \
      bootstrap.servers=lab-kafka-bootstrap:9092 \
      acks=all \
      batch.size=65536 \
      linger.ms=50 \
      compression.type=lz4 \
      buffer.memory=67108864

# Record the results:
# - Messages/sec
# - MB/sec
# - Average latency (ms)
# - P99 latency (ms)
```

### Step 4: Run Low-Latency Producer Benchmark

```bash
# Low latency producer benchmark — same message count, different config
kubectl -n kafka run producer-latency --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.9.0 -- \
  bin/kafka-producer-perf-test.sh \
    --topic benchmark-latency \
    --throughput -1 \
    --num-records 100000 \
    --record-size 1024 \
    --producer-props \
      bootstrap.servers=lab-kafka-bootstrap:9092 \
      acks=all \
      batch.size=16384 \
      linger.ms=0 \
      compression.type=none

# Compare: throughput will be lower, but P99 latency should be better
```

### Step 5: Run Consumer Benchmark

```bash
# Consumer benchmark — read 1 million messages
kubectl -n kafka run consumer-bench --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:latest-kafka-3.9.0 -- \
  bin/kafka-consumer-perf-test.sh \
    --bootstrap-server lab-kafka-bootstrap:9092 \
    --topic benchmark-throughput \
    --messages 1000000 \
    --group benchmark-consumer-group

# Record:
# - Messages/sec consumed
# - MB/sec consumed
```

### Step 6: Compare Results

Create a comparison table from your benchmarks:

| Metric | High Throughput | Low Latency |
|--------|----------------|-------------|
| Messages/sec | (your result) | (your result) |
| MB/sec | (your result) | (your result) |
| Avg Latency | (your result) | (your result) |
| P99 Latency | (your result) | (your result) |

### Step 7: Clean Up

```bash
kubectl delete kafkatopic benchmark-throughput benchmark-latency -n kafka
kubectl delete kafka lab -n kafka
kubectl delete kafkanodepool combined -n kafka
kubectl delete -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
kubectl delete namespace kafka
kind delete cluster --name kafka-lab
```

### Success Criteria

You have completed this exercise when you:
- [ ] Deployed a 3-broker Kafka cluster in KRaft mode via Strimzi
- [ ] Created topics with explicit partition and replication settings
- [ ] Ran high-throughput producer benchmark and recorded results
- [ ] Ran low-latency producer benchmark and recorded results
- [ ] Compared throughput vs latency trade-offs with actual numbers
- [ ] Ran a consumer benchmark and measured consumption throughput

---

## Key Takeaways

1. **KRaft eliminates ZooKeeper** — Kafka manages its own metadata via the Raft consensus protocol, simplifying operations and improving failover speed.
2. **Strimzi makes Kafka a Kubernetes-native workload** — Topics, users, and connectors are all managed via Custom Resources, enabling GitOps workflows.
3. **Throughput and latency are opposing forces** — Batching increases throughput but adds latency. Choose based on your use case.
4. **Security is not optional** — Use TLS for encryption, mTLS or SCRAM for authentication, and ACLs for authorization. Strimzi automates certificate management.
5. **Schemas prevent pipeline corruption** — Always use a schema registry in production to enforce contracts between producers and consumers.

---

## Further Reading

**Books:**
- **"Kafka: The Definitive Guide"** (2nd edition) — Gwen Shapira, Todd Palino, Rajini Sivaram, Krit Petty (O'Reilly)
- **"Designing Event-Driven Systems"** — Ben Stopford (Confluent, free download)

**Articles:**
- **"Running Apache Kafka on Kubernetes"** — Strimzi documentation (strimzi.io/documentation)
- **"KRaft: Kafka Without ZooKeeper"** — Apache Kafka KIP-500 (cwiki.apache.org)

**Talks:**
- **"Strimzi: Kafka on Kubernetes"** — Jakub Scholz, KubeCon EU 2024 (YouTube)
- **"Kafka Performance Tuning"** — Tim Berglund, Confluent (YouTube)

---

## Summary

Apache Kafka is the backbone of modern data engineering, and Strimzi makes it a first-class Kubernetes citizen. By managing Kafka through Custom Resources, you get declarative configuration, automated security, rolling upgrades, and integration with the entire Kubernetes ecosystem.

The key to running Kafka well is understanding the trade-offs: partitions vs overhead, throughput vs latency, replication vs performance. There is no single correct configuration — only the correct configuration for your specific workload.

---

## Next Module

Continue to [Module 1.3: Stream Processing with Apache Flink](module-1.3-flink/) to learn how to process the data flowing through your Kafka topics in real time.

---

*"Kafka is like a central nervous system for data. Every event that happens in your business flows through it."* — Jay Kreps, creator of Apache Kafka

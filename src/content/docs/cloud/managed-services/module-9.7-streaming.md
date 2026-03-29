---
title: "Module 9.7: Streaming Data Pipelines (MSK / Confluent / Dataflow)"
slug: cloud/managed-services/module-9.7-streaming
sidebar:
  order: 8
---
**Complexity**: [COMPLEX] | **Time to Complete**: 3h | **Prerequisites**: Module 9.2 (Message Brokers), Module 9.6 (Search & Analytics), distributed systems basics

## Why This Module Matters

In February 2024, an online marketplace processed 850,000 orders per day. Their event pipeline -- order-placed, payment-confirmed, inventory-updated, shipment-created -- ran through a self-managed Kafka cluster on EKS. Six brokers, each on r6i.2xlarge instances with 2 TB of gp3 storage. Total monthly cost: $9,400. The platform team spent 15 hours per week on Kafka operations: broker rolling restarts, partition rebalancing, disk monitoring, ZooKeeper maintenance, and upgrading between Kafka versions.

One Tuesday, a broker lost its EBS volume due to an AZ-level storage event. Kafka's under-replicated partitions jumped to 340. The cluster's ISR (In-Sync Replicas) dropped below the minimum for 28 topic-partitions, blocking producers. The team spent 6 hours manually reassigning partitions and rebuilding replicas. During that time, the order pipeline was partially degraded -- 12% of orders were delayed by up to 4 hours.

They evaluated Amazon MSK (Managed Streaming for Kafka) and Confluent Cloud. The migration to MSK took five weeks. The same 6-broker cluster now costs $7,200/month (cheaper because MSK handles the control plane), and the platform team spends 2 hours per week on Kafka-related tasks instead of 15. Broker replacements happen automatically. ZooKeeper is gone (MSK uses KRaft since 2024). The operational difference is transformative.

This module teaches you when to use managed Kafka versus running Strimzi in-cluster, how partitioning and consumer groups work at scale, how to monitor consumer lag and prevent data loss, how schema registries maintain data contracts, and how to build stream processing pipelines on Kubernetes.

---

## Managed Kafka vs In-Cluster Strimzi

### Decision Framework

| Factor | Managed (MSK/Confluent) | In-Cluster (Strimzi on K8s) |
|--------|------------------------|-----------------------------|
| Operational burden | Provider handles brokers, patching, storage | You handle everything |
| Cost at small scale | Higher (minimum 2-3 brokers) | Lower (share cluster resources) |
| Cost at large scale | Often cheaper (no ops engineer time) | Higher (hidden ops costs) |
| Network latency | 1-5ms (VPC connectivity) | < 1ms (in-cluster) |
| Customization | Limited (provider-defined configs) | Full control |
| Multi-cluster | Each cluster is independent | Strimzi MirrorMaker2 for replication |
| Kafka version | Provider cadence (1-3 months behind) | Any version you want |
| ZooKeeper | Gone (KRaft mode on MSK since 2024) | Strimzi manages for you |

### When to Choose Each

**Choose managed Kafka when:**
- Your team does not have Kafka expertise
- You process more than 100 MB/s sustained
- You need guaranteed durability (financial, healthcare)
- You want to focus on producers/consumers, not broker operations

**Choose Strimzi when:**
- Sub-millisecond latency matters (in-cluster communication)
- You are on a tight budget with low volume
- You need full control over Kafka configuration
- You are running in environments without managed services (on-prem, edge)

### Strimzi Quick Setup (for comparison)

```yaml
# Strimzi Kafka cluster in Kubernetes
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: event-cluster
  namespace: kafka
spec:
  kafka:
    version: 3.8.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      num.partitions: 12
    storage:
      type: jbod
      volumes:
        - id: 0
          type: persistent-claim
          size: 500Gi
          class: gp3-encrypted
    resources:
      requests:
        memory: 4Gi
        cpu: "2"
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 50Gi
      class: gp3-encrypted
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

---

## Partitioning: The Foundation of Kafka Scalability

A Kafka topic is divided into partitions. Partitions are the unit of parallelism -- more partitions means more consumers can process data concurrently.

### How Partitions Work

```
Topic: order-events (6 partitions)

  Producer
     |
     | key: order-123 --> hash(key) % 6 = partition 2
     v
  +----+----+----+----+----+----+
  | P0 | P1 | P2 | P3 | P4 | P5 |
  +----+----+----+----+----+----+
                |
                v
           offset 0: order-123 created
           offset 1: order-123 confirmed
           offset 2: order-123 shipped
           (ordered within partition)
```

### Partition Count Guidelines

| Throughput | Partitions | Reasoning |
|-----------|-----------|-----------|
| < 10 MB/s | 6 | Enough for small workloads, easy to manage |
| 10-100 MB/s | 12-24 | Allows 12-24 parallel consumers |
| 100 MB/s - 1 GB/s | 50-100 | Match consumer count to partition count |
| > 1 GB/s | 100+ | Carefully test; more partitions = more overhead |

**Rule of thumb**: partitions should equal or exceed the maximum number of consumers in your largest consumer group.

### Partition Key Design

The partition key determines which partition a message lands in. All messages with the same key go to the same partition (in order).

```python
from confluent_kafka import Producer

producer = Producer({
    'bootstrap.servers': 'msk-broker1:9092,msk-broker2:9092',
    'acks': 'all',
    'enable.idempotence': True,
    'max.in.flight.requests.per.connection': 5,
})

# Key by order_id -- all events for one order are in the same partition
def publish_order_event(order_id, event_type, payload):
    producer.produce(
        topic='order-events',
        key=str(order_id).encode('utf-8'),
        value=json.dumps({
            'order_id': order_id,
            'event_type': event_type,
            'payload': payload,
            'timestamp': datetime.utcnow().isoformat()
        }).encode('utf-8'),
        callback=delivery_report,
    )
    producer.flush()

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")
```

**Common key strategies:**
- **Customer ID**: All events for one customer in order
- **Order ID**: All order lifecycle events in order
- **Null key**: Round-robin across partitions (maximum throughput, no ordering)
- **Tenant ID**: Multi-tenant isolation per partition

---

## Consumer Groups and Lag Monitoring

### Consumer Group Mechanics

```
Topic: order-events (6 partitions)

Consumer Group: order-processor (3 pods)

  +----+----+----+----+----+----+
  | P0 | P1 | P2 | P3 | P4 | P5 |
  +--+-+--+-+----+----+--+-+--+-+
     |    |              |    |
     v    v              v    v
  +------+  +------+  +------+
  | Pod1 |  | Pod2 |  | Pod3 |
  | P0,P1|  | P2,P3|  | P4,P5|
  +------+  +------+  +------+

Each pod gets an equal share of partitions.
Adding a 4th pod triggers rebalancing.
A 7th pod would be idle (6 partitions, 7 consumers).
```

### Kubernetes Consumer Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-processor
  namespace: streaming
spec:
  replicas: 6    # Match partition count
  selector:
    matchLabels:
      app: order-processor
  template:
    metadata:
      labels:
        app: order-processor
    spec:
      serviceAccountName: kafka-consumer
      containers:
        - name: consumer
          image: mycompany/order-processor:2.3.0
          env:
            - name: KAFKA_BROKERS
              value: "b-1.msk-cluster.abc123.kafka.us-east-1.amazonaws.com:9092,b-2.msk-cluster.abc123.kafka.us-east-1.amazonaws.com:9092"
            - name: KAFKA_TOPIC
              value: "order-events"
            - name: KAFKA_GROUP_ID
              value: "order-processor"
            - name: KAFKA_AUTO_OFFSET_RESET
              value: "earliest"
            - name: KAFKA_SECURITY_PROTOCOL
              value: "SASL_SSL"
            - name: KAFKA_SASL_MECHANISM
              value: "AWS_MSK_IAM"
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
```

### Consumer Lag Monitoring

Consumer lag is the difference between the latest message in a partition and the last message processed by a consumer. High lag means consumers are falling behind.

```
Partition 3:
  Latest offset:    1,000,000
  Consumer offset:    985,000
  Lag:                 15,000 messages
```

### Monitoring with Prometheus and Kafka Exporter

```yaml
# Deploy kafka-exporter for Prometheus metrics
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-exporter
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kafka-exporter
  template:
    metadata:
      labels:
        app: kafka-exporter
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9308"
    spec:
      containers:
        - name: exporter
          image: danielqsj/kafka-exporter:v1.8.0
          args:
            - --kafka.server=b-1.msk-cluster.abc123.kafka.us-east-1.amazonaws.com:9092
            - --kafka.server=b-2.msk-cluster.abc123.kafka.us-east-1.amazonaws.com:9092
            - --topic.filter=order-.*
            - --group.filter=.*
          ports:
            - containerPort: 9308
```

```yaml
# PrometheusRule for consumer lag alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: kafka-lag-alerts
  namespace: monitoring
spec:
  groups:
    - name: kafka-consumer-lag
      rules:
        - alert: KafkaConsumerLagHigh
          expr: |
            sum by (consumergroup, topic) (kafka_consumergroup_lag) > 50000
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Consumer group {{ $labels.consumergroup }} has high lag on {{ $labels.topic }}"
        - alert: KafkaConsumerLagCritical
          expr: |
            sum by (consumergroup, topic) (kafka_consumergroup_lag) > 500000
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Consumer group {{ $labels.consumergroup }} critically behind on {{ $labels.topic }}"
```

### KEDA Scaling on Consumer Lag

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-processor-scaler
  namespace: streaming
spec:
  scaleTargetRef:
    name: order-processor
  minReplicaCount: 3
  maxReplicaCount: 12    # Never exceed partition count
  pollingInterval: 10
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: b-1.msk-cluster.abc123.kafka.us-east-1.amazonaws.com:9092
        consumerGroup: order-processor
        topic: order-events
        lagThreshold: "1000"
        offsetResetPolicy: earliest
```

---

## Schema Registry: Data Contracts for Events

Without schema management, producers can change the event structure without warning, breaking consumers.

### The Problem

```
Week 1: {"order_id": "123", "amount": 49.99, "currency": "USD"}
Week 2: {"orderId": "123", "total": 49.99}  <-- broke every consumer
```

### Schema Registry Architecture

```
  Producer                           Consumer
     |                                  |
     | 1. Register schema               | 3. Get schema by ID
     v                                  v
  +---------------------+    +---------------------+
  | Schema Registry     |    | Schema Registry     |
  | (schema ID: 42)     |    | (schema ID: 42)     |
  +---------------------+    +---------------------+
     |                                  |
     | 2. Produce with schema ID        | 4. Deserialize with schema
     v                                  v
  +-------------------------------------------+
  |              Kafka Cluster                 |
  |  [schema_id=42][serialized_data]           |
  +-------------------------------------------+
```

### Confluent Schema Registry on Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: schema-registry
  namespace: streaming
spec:
  replicas: 2
  selector:
    matchLabels:
      app: schema-registry
  template:
    metadata:
      labels:
        app: schema-registry
    spec:
      containers:
        - name: schema-registry
          image: confluentinc/cp-schema-registry:7.7.0
          ports:
            - containerPort: 8081
          env:
            - name: SCHEMA_REGISTRY_HOST_NAME
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
            - name: SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS
              value: "b-1.msk-cluster.abc123.kafka.us-east-1.amazonaws.com:9092"
            - name: SCHEMA_REGISTRY_KAFKASTORE_SECURITY_PROTOCOL
              value: "SASL_SSL"
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: schema-registry
  namespace: streaming
spec:
  selector:
    app: schema-registry
  ports:
    - port: 8081
```

### Registering and Using Schemas

```bash
# Register an Avro schema for order events
curl -XPOST "http://schema-registry:8081/subjects/order-events-value/versions" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{
  "schema": "{\"type\":\"record\",\"name\":\"OrderEvent\",\"namespace\":\"com.example\",\"fields\":[{\"name\":\"order_id\",\"type\":\"string\"},{\"name\":\"event_type\",\"type\":{\"type\":\"enum\",\"name\":\"EventType\",\"symbols\":[\"CREATED\",\"CONFIRMED\",\"SHIPPED\",\"DELIVERED\",\"CANCELLED\"]}},{\"name\":\"amount\",\"type\":\"double\"},{\"name\":\"currency\",\"type\":\"string\"},{\"name\":\"timestamp\",\"type\":\"long\",\"logicalType\":\"timestamp-millis\"}]}"
}'

# Set compatibility mode (BACKWARD = new schema can read old data)
curl -XPUT "http://schema-registry:8081/config/order-events-value" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"compatibility": "BACKWARD"}'
```

### Schema Compatibility Modes

| Mode | Rule | Example |
|------|------|---------|
| **BACKWARD** | New schema can read old data | Adding optional field with default |
| **FORWARD** | Old schema can read new data | Removing optional field |
| **FULL** | Both backward and forward | Only adding/removing optional fields with defaults |
| **NONE** | No compatibility checking | Any change allowed (dangerous) |

For most pipelines, **BACKWARD** compatibility is the safest choice. It ensures that new consumers can always read messages produced by older producers.

---

## Stream Processing on Kubernetes

### Architecture Options

| Tool | Deployment Model | Best For | Complexity |
|------|-----------------|----------|------------|
| Kafka Streams | Library (runs in your pods) | Simple transformations, joins | Low |
| Apache Flink | Operator (FlinkDeployment) | Complex event processing, windows | High |
| ksqlDB | Deployment | SQL-like stream processing | Medium |
| Google Dataflow | Managed (GCP only) | Batch + stream unified | Medium |

### Kafka Streams Application on Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-enricher
  namespace: streaming
spec:
  replicas: 6
  selector:
    matchLabels:
      app: order-enricher
  template:
    metadata:
      labels:
        app: order-enricher
    spec:
      containers:
        - name: enricher
          image: mycompany/order-enricher:1.0.0
          env:
            - name: KAFKA_BROKERS
              value: "b-1.msk-cluster.abc123.kafka.us-east-1.amazonaws.com:9092"
            - name: APPLICATION_ID
              value: "order-enricher"
            - name: INPUT_TOPIC
              value: "raw-orders"
            - name: OUTPUT_TOPIC
              value: "enriched-orders"
            - name: SCHEMA_REGISTRY_URL
              value: "http://schema-registry:8081"
            - name: STATE_DIR
              value: "/tmp/kafka-streams"
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
          volumeMounts:
            - name: state-store
              mountPath: /tmp/kafka-streams
      volumes:
        - name: state-store
          emptyDir:
            sizeLimit: 10Gi
```

### Flink on Kubernetes (Flink Operator)

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: order-analytics
  namespace: streaming
spec:
  image: mycompany/flink-order-analytics:1.0.0
  flinkVersion: v1_19
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "2"
    state.backend: rocksdb
    state.checkpoints.dir: s3://flink-checkpoints/order-analytics
    execution.checkpointing.interval: "60000"
  serviceAccount: flink-sa
  jobManager:
    resource:
      memory: "2048m"
      cpu: 1
  taskManager:
    resource:
      memory: "4096m"
      cpu: 2
    replicas: 3
  job:
    jarURI: local:///opt/flink/usrlib/order-analytics.jar
    parallelism: 6
    upgradeMode: savepoint
```

---

## Setting Up Amazon MSK

```bash
# Create MSK Serverless cluster (simplest option)
aws kafka create-cluster-v2 \
  --cluster-name orders-streaming \
  --serverless '{
    "vpcConfigs": [{
      "subnetIds": ["subnet-aaa", "subnet-bbb", "subnet-ccc"],
      "securityGroupIds": ["sg-kafka"]
    }],
    "clientAuthentication": {
      "sasl": {"iam": {"enabled": true}}
    }
  }'

# Or create a provisioned cluster for predictable costs
aws kafka create-cluster \
  --cluster-name orders-streaming \
  --kafka-version 3.7.0 \
  --number-of-broker-nodes 3 \
  --broker-node-group-info '{
    "InstanceType": "kafka.m7g.large",
    "ClientSubnets": ["subnet-aaa", "subnet-bbb", "subnet-ccc"],
    "SecurityGroups": ["sg-kafka"],
    "StorageInfo": {
      "EbsStorageInfo": {"VolumeSize": 500}
    }
  }' \
  --encryption-info '{
    "EncryptionInTransit": {"ClientBroker": "TLS", "InCluster": true},
    "EncryptionAtRest": {"DataVolumeKMSKeyId": "alias/msk-key"}
  }'
```

---

## Did You Know?

1. **Apache Kafka processes over 7 trillion messages per day at LinkedIn**, where it was originally created. LinkedIn's Kafka clusters handle over 35 PB of data per day across 100+ clusters. The project was open-sourced in 2011 and is now the most widely deployed streaming platform in the world.

2. **Amazon MSK Serverless eliminates cluster capacity planning entirely**. You create a topic, produce and consume data, and AWS automatically provisions and scales the underlying infrastructure. Pricing is per-partition-hour and per-GB of data, which can save 30-50% for workloads with variable throughput compared to provisioned MSK.

3. **The KRaft mode (Kafka Raft) replaced ZooKeeper** starting with Kafka 3.3 (2022) and became production-ready in Kafka 3.5. ZooKeeper was the #1 operational pain point for Kafka clusters -- it required separate monitoring, backup, and scaling. KRaft eliminates ZooKeeper entirely by embedding metadata management in Kafka brokers themselves.

4. **Schema Registry compatibility checking has prevented billions of dollars in downstream damage** according to Confluent's estimates. A single incompatible schema change in a high-throughput pipeline can corrupt millions of messages before anyone notices. The registry acts as a gatekeeper, rejecting incompatible schemas at registration time rather than at consumption time.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| More consumers than partitions | "More pods = more throughput" | Extra consumers sit idle; scale partitions first, then consumers |
| Not using a partition key when ordering matters | Null key gives best throughput | Use customer/order ID as key for ordered event processing |
| Setting `auto.offset.reset=latest` in production | "We only want new messages" | Use `earliest` and let the consumer group track its position; `latest` loses messages on restart |
| Not monitoring consumer lag | "If messages are flowing, everything is fine" | Deploy kafka-exporter and alert on lag > threshold |
| Skipping schema registry | "We will coordinate schema changes manually" | Manual coordination fails at scale; registry enforces compatibility |
| Under-replicating topics (replication factor = 1) | Testing configuration leaked to production | Always use replication factor >= 3 and `min.insync.replicas >= 2` |
| Running Kafka Streams without persistent state store volumes | Using `emptyDir` for state | State is lost on pod restart, causing full reprocessing; use PVCs for state stores |
| Not setting producer `acks=all` for critical data | Default was `acks=1` before Kafka 3.0 | Always set `acks=all` and `enable.idempotence=true` for data safety |

---

## Quiz

<details>
<summary>1. Why should you never have more consumer pods than topic partitions in a consumer group?</summary>

In a Kafka consumer group, each partition is assigned to exactly one consumer. If you have 6 partitions and 8 consumers, 2 consumers will be completely idle -- they receive no messages. They consume cluster resources (CPU, memory, network connections) without doing any work. The maximum useful parallelism equals the partition count. If you need more throughput, increase the partition count first, then add consumers to match. Note that increasing partitions is a one-way operation in Kafka -- you cannot reduce partition count after creation.
</details>

<details>
<summary>2. Explain the difference between managed Kafka (MSK) and in-cluster Kafka (Strimzi) and when you would choose each.</summary>

Managed Kafka (MSK, Confluent Cloud) handles broker provisioning, patching, storage management, and automatic recovery. You pay more per-broker but save significant engineering time on operations. Choose managed when your team lacks Kafka expertise, when durability is critical, or when you process high volumes. In-cluster Kafka (Strimzi) runs Kafka as a StatefulSet in your Kubernetes cluster. It gives you sub-millisecond latency (no VPC hop), full control over configuration, and lower base cost. Choose it for development environments, low-volume workloads, or when you need Kafka in environments without managed services (air-gapped, on-premises).
</details>

<details>
<summary>3. What is consumer lag and why is it the most important Kafka metric to monitor?</summary>

Consumer lag is the difference between the latest offset in a partition (the most recent message produced) and the committed offset of a consumer group (the last message the consumer acknowledged). High lag means consumers are not keeping up with producers -- messages are accumulating faster than they can be processed. This indicates either under-provisioned consumers, slow processing logic, or a sudden spike in production rate. If lag grows continuously, it will eventually exceed the topic's retention period, causing data loss as old messages are deleted before being consumed. Monitoring lag is critical because everything can appear healthy (no errors, pods running) while data is silently falling behind.
</details>

<details>
<summary>4. Why is BACKWARD compatibility the recommended schema compatibility mode?</summary>

BACKWARD compatibility means that a new version of a schema can read data written by the previous version. This is the safest default because in Kubernetes environments, consumers are typically updated before producers (or independently). When you deploy a new consumer with an updated schema, it must still be able to read messages that were produced with the old schema. Backward compatibility allows adding new fields (with defaults) and removing optional fields. It prevents breaking changes like renaming fields or changing types, which would cause deserialization failures in the new consumer when reading old messages.
</details>

<details>
<summary>5. How does KEDA scale Kafka consumers differently from CPU-based HPA scaling?</summary>

CPU-based HPA measures how busy consumer pods are, but Kafka consumers are often I/O-bound, not CPU-bound. A consumer waiting on network I/O uses minimal CPU even when the queue is backing up. KEDA scales based on consumer lag -- the actual number of unprocessed messages. If lag increases, KEDA adds pods regardless of CPU usage. If lag is zero, KEDA can scale down. This directly aligns scaling with the business metric that matters: how many messages are waiting to be processed. KEDA also respects the partition count limit, preventing over-scaling beyond useful parallelism.
</details>

<details>
<summary>6. What is the purpose of `min.insync.replicas` and why should it be set to 2 when using `acks=all`?</summary>

`min.insync.replicas` (ISR) defines the minimum number of replicas that must acknowledge a write before the producer considers it successful. With `acks=all`, the producer waits for all in-sync replicas to acknowledge. Setting ISR to 2 (with replication factor 3) means at least 2 of 3 replicas must be available and up-to-date for writes to succeed. If only 1 replica is in-sync (because 2 brokers are down), writes are rejected rather than accepted with insufficient replication. This prevents data loss scenarios where a single remaining replica fails after acknowledging a write. The trade-off is reduced availability -- writes fail when fewer than ISR replicas are healthy.
</details>

---

## Hands-On Exercise: Kafka Pipeline with Strimzi

### Setup

```bash
# Create kind cluster with extra resources
cat > /tmp/kind-kafka.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
  - role: worker
EOF

kind create cluster --name kafka-lab --config /tmp/kind-kafka.yaml

# Install Strimzi operator
k create namespace kafka
k apply -f https://strimzi.io/install/latest?namespace=kafka

k wait --for=condition=ready pod -l name=strimzi-cluster-operator \
  --namespace kafka --timeout=180s
```

### Task 1: Create a Kafka Cluster

Deploy a 3-broker Kafka cluster using Strimzi.

<details>
<summary>Solution</summary>

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: lab-cluster
  namespace: kafka
spec:
  kafka:
    version: 3.8.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      num.partitions: 6
    storage:
      type: ephemeral
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
  zookeeper:
    replicas: 3
    storage:
      type: ephemeral
    resources:
      requests:
        memory: 512Mi
        cpu: 250m
  entityOperator:
    topicOperator: {}
```

```bash
k apply -f /tmp/kafka-cluster.yaml
# This takes 3-5 minutes
k wait kafka/lab-cluster --for=condition=Ready --timeout=300s -n kafka
```
</details>

### Task 2: Create a Topic and Produce Messages

Create an `order-events` topic and publish messages.

<details>
<summary>Solution</summary>

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: order-events
  namespace: kafka
  labels:
    strimzi.io/cluster: lab-cluster
spec:
  partitions: 6
  replicas: 3
  config:
    retention.ms: 86400000
    min.insync.replicas: 2
```

```bash
k apply -f /tmp/topic.yaml

# Produce messages
k run kafka-producer --rm -it --image=quay.io/strimzi/kafka:0.44.0-kafka-3.8.0 \
  -n kafka --restart=Never -- \
  bin/kafka-console-producer.sh \
  --broker-list lab-cluster-kafka-bootstrap:9092 \
  --topic order-events \
  --property "parse.key=true" \
  --property "key.separator=:" << 'EOF'
order-001:{"order_id":"001","event":"created","amount":29.99}
order-002:{"order_id":"002","event":"created","amount":49.99}
order-001:{"order_id":"001","event":"confirmed","amount":29.99}
order-003:{"order_id":"003","event":"created","amount":99.99}
order-002:{"order_id":"002","event":"confirmed","amount":49.99}
order-001:{"order_id":"001","event":"shipped","amount":29.99}
order-003:{"order_id":"003","event":"confirmed","amount":99.99}
order-002:{"order_id":"002","event":"shipped","amount":49.99}
order-003:{"order_id":"003","event":"shipped","amount":99.99}
order-001:{"order_id":"001","event":"delivered","amount":29.99}
EOF
```
</details>

### Task 3: Deploy Consumer Group and Observe Partition Assignment

Create a consumer Deployment with 3 replicas and verify partition distribution.

<details>
<summary>Solution</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-consumer
  namespace: kafka
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-consumer
  template:
    metadata:
      labels:
        app: order-consumer
    spec:
      containers:
        - name: consumer
          image: quay.io/strimzi/kafka:0.44.0-kafka-3.8.0
          command:
            - /bin/sh
            - -c
            - |
              bin/kafka-console-consumer.sh \
                --bootstrap-server lab-cluster-kafka-bootstrap:9092 \
                --topic order-events \
                --group order-processor \
                --from-beginning \
                --property print.key=true \
                --property print.partition=true
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
```

```bash
k apply -f /tmp/consumer-deployment.yaml
sleep 15

# Check consumer group partition assignments
k run check-group --rm -it --image=quay.io/strimzi/kafka:0.44.0-kafka-3.8.0 \
  -n kafka --restart=Never -- \
  bin/kafka-consumer-groups.sh \
  --bootstrap-server lab-cluster-kafka-bootstrap:9092 \
  --describe --group order-processor
```
</details>

### Task 4: Monitor Consumer Lag

Produce more messages and observe lag building up.

<details>
<summary>Solution</summary>

```bash
# Produce 1000 messages rapidly
k run bulk-producer --rm -it --image=quay.io/strimzi/kafka:0.44.0-kafka-3.8.0 \
  -n kafka --restart=Never -- \
  /bin/sh -c '
  for i in $(seq 1 1000); do
    echo "order-$((i % 100)):$(printf "{\"order_id\":\"%03d\",\"event\":\"created\",\"amount\":%d.%02d}" $i $((RANDOM % 100)) $((RANDOM % 100)))"
  done | bin/kafka-console-producer.sh \
    --broker-list lab-cluster-kafka-bootstrap:9092 \
    --topic order-events \
    --property "parse.key=true" \
    --property "key.separator=:"
  echo "Produced 1000 messages"
  '

# Check lag
k run check-lag --rm -it --image=quay.io/strimzi/kafka:0.44.0-kafka-3.8.0 \
  -n kafka --restart=Never -- \
  bin/kafka-consumer-groups.sh \
  --bootstrap-server lab-cluster-kafka-bootstrap:9092 \
  --describe --group order-processor
```
</details>

### Task 5: Verify Ordering Within Partitions

Confirm that messages with the same key always appear in order.

<details>
<summary>Solution</summary>

```bash
# Consume from a specific partition to verify ordering
k run partition-check --rm -it --image=quay.io/strimzi/kafka:0.44.0-kafka-3.8.0 \
  -n kafka --restart=Never -- \
  bin/kafka-console-consumer.sh \
  --bootstrap-server lab-cluster-kafka-bootstrap:9092 \
  --topic order-events \
  --partition 0 \
  --from-beginning \
  --max-messages 20 \
  --property print.key=true \
  --property print.offset=true

# All messages with the same key will have increasing offsets
# within the same partition, confirming order is preserved
```
</details>

### Success Criteria

- [ ] 3-broker Kafka cluster is running and Ready
- [ ] order-events topic has 6 partitions with replication factor 3
- [ ] Consumer group shows 3 consumers with 2 partitions each
- [ ] Consumer lag is visible after bulk production
- [ ] Messages with the same key appear in order within their partition

### Cleanup

```bash
kind delete cluster --name kafka-lab
```

---

**Next Module**: [Module 9.8: Secrets Management Deep Dive](module-9.8-secrets-deep/) -- Learn how External Secrets Operator, Secrets Store CSI, and HashiCorp Vault integrate with Kubernetes to manage dynamic secrets, TTLs, and credential rotation at scale.

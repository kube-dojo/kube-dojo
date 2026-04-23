---
title: "Module 8.9: Large-Scale Observability & Telemetry"
slug: cloud/advanced-operations/module-8.9-observability-scale
sidebar:
  order: 10
---

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 2.5 hours
>
> **Prerequisites**: Basic understanding of Prometheus, Grafana, and logging concepts
>
> **Track**: Advanced Cloud Operations

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Diagnose** performance bottlenecks and out-of-memory crashes in Prometheus due to high-cardinality metrics, implementing robust recording rules to mitigate them.
- **Design** highly available, scalable, multi-cluster observability architectures utilizing Thanos, Loki, and OpenTelemetry to unify metrics, logs, and distributed traces.
- **Implement** advanced log filtering, transformation, and sampling strategies via OpenTelemetry Collector pipelines to drastically reduce logging costs and storage overhead.
- **Evaluate** the architectural trade-offs between centralized push-based metric systems (like Grafana Mimir) and decentralized pull-based sidecar models (like Thanos).
- **Debug** cross-cluster distributed trace contexts using OpenTelemetry and tail-based sampling, ensuring complete transaction visibility across complex microservice boundaries.

---

## Why This Module Matters

In August 2023, a rapidly growing global fintech platform, managing 14 Kubernetes clusters and over 2,800 active pods, experienced a catastrophic observability failure that cost the organization an estimated $2.5 million in strict service-level agreement (SLA) penalties. Their entire monitoring backbone relied on a single, massive Prometheus server. When their engineering teams deployed a major microservices expansion to handle new payment regions, the metric cardinality exploded to over 12 million unique time series within a matter of hours. The Prometheus instance's memory consumption rapidly climbed from 16GB to 64GB, query latency degraded to over 30 seconds, and the server began violently crash-looping with out-of-memory (OOM) errors every two days.

The platform engineering team attempted to mitigate the issue by vertically scaling the Prometheus pod, eventually allocating a staggering 128GB of RAM. While this temporarily stabilized the data ingestion, the architectural side-effects were devastating. Whenever the monolithic pod restarted, replaying the massive Write-Ahead Log (WAL) took upwards of 25 minutes. During one of these vulnerable WAL replay windows, a critical payment gateway service suffered a cascading failure. Because the primary monitoring system was effectively offline and recovering, the on-call engineers were flying completely blind. They were forced to manually parse unstructured text logs across hundreds of nodes using raw `grep` commands, transforming a routine infrastructure blip into a prolonged global outage.

This incident underscores a fundamental truth about cloud-native infrastructure: observability data volume naturally grows at a much faster rate than the underlying applications. The real fix for the fintech company was not adding more RAM; it was a complete architectural overhaul. They needed to shard Prometheus across independent clusters, implement Thanos for long-term distributed queries, aggressively filter and route data using OpenTelemetry collectors, and enforce strict cardinality limits across all development teams. This module will teach you how to build exactly this kind of resilient, multi-cluster observability platform that gracefully handles millions of time series and terabytes of logs without ever becoming the bottleneck.

---

## The Observability Scale Problem

Observability at scale is fundamentally a distributed data management problem. As you add more clusters, nodes, pods, and microservices to your Kubernetes v1.35 environment, the volume of metrics, logs, and traces multiplies exponentially. The computational cost and operational complexity of transmitting, processing, and querying this telemetry data inevitably grows faster than the physical infrastructure it is designed to monitor.

When a platform scales up, a standard out-of-the-box monitoring stack rapidly hits physical limitations. A single node's disk input/output operations per second (IOPS) cannot keep up with thousands of log lines written every second. A single process's memory cannot hold millions of active time series chunks. 

| Telemetry Volume at Scale | Small | Medium | Large |
| :--- | :--- | :--- | :--- |
| **Nodes** | 10 | 50 | 200 |
| **Pods** | 200 | 2,000 | 15,000 |
| **Services** | 20 | 100 | 500 |
| **Metrics: Time series** | 50K | 500K | 5M+ |
| **Metrics: Samples/second** | 5K | 50K | 500K |
| **Metrics: Storage (30 days)** | 10GB | 100GB | 1TB+ |
| **Logs: Lines/second** | 500 | 5,000 | 50,000 |
| **Logs: Storage (30 days)** | 50GB | 500GB | 5TB+ |
| **Traces: Spans/second** | 100 | 1,000 | 10,000 |
| **Traces: Storage (30 days)**| 5GB | 50GB | 500GB+ |

As demonstrated in the table above, enterprise-scale telemetry demands tiered storage architectures, aggressive downsampling, and decentralized processing to remain economically viable.

---

## Multi-Cluster Prometheus with Thanos

Prometheus was originally designed for localized, single-cluster deployments. It utilizes a highly optimized local Time Series Database (TSDB) but lacks native capabilities for distributed querying, horizontal scaling, or seamless long-term object storage. When operating multiple clusters, you need a mechanism to query data across all of them globally, store historical data economically (beyond the brief retention period of local SSDs), and deduplicate incoming metrics from highly available (HA) Prometheus pairs.

### Thanos Architecture

Thanos solves the multi-cluster observability problem by injecting a sidecar container alongside your existing Prometheus instances. This sidecar bridges the gap between local, ephemeral storage and global, persistent storage.

```mermaid
flowchart TD
    subgraph Cluster A
        A_Prom[Prometheus] -->|scrape| A_Sidecar[Thanos Sidecar]
    end
    subgraph Cluster B
        B_Prom[Prometheus] -->|scrape| B_Sidecar[Thanos Sidecar]
    end
    
    A_Sidecar -->|Upload TSDB blocks| ObjStore[(Object Storage\nS3/GCS/Azure)]
    B_Sidecar -->|Upload TSDB blocks| ObjStore
    
    subgraph Thanos Components
        StoreGW[Store Gateway\nreads old data]
        Compactor[Compactor\ndownsample blocks]
        Querier[Querier\nfan-out to all sources]
    end
    
    ObjStore --> StoreGW
    ObjStore --> Compactor
    
    A_Sidecar -.-> Querier
    B_Sidecar -.-> Querier
    StoreGW -.-> Querier
    
    Grafana[Grafana] -->|queries| Querier
```

In this decentralized architecture, Prometheus continues to scrape targets and evaluate local alerting rules. Every two hours, Prometheus cuts a new immutable TSDB block to disk. The Thanos Sidecar detects this new block and uploads it to an inexpensive object store (like AWS S3 or Google Cloud Storage). 

### Deploying Thanos with Prometheus Operator

To deploy this architecture, you configure the Prometheus Operator to inject the Thanos Sidecar and mount the necessary credentials for the external object storage.

```yaml
# Prometheus with Thanos sidecar (per cluster)
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 2  # HA pair
  retention: 6h  # Short local retention (Thanos handles long-term)
  externalLabels:
    cluster: "prod-us-east-1"
    region: "us-east-1"
  thanos:
    image: quay.io/thanos/thanos:v0.36.1
    objectStorageConfig:
      key: objstore.yml
      name: thanos-objstore-config
  storage:
    volumeClaimTemplate:
      spec:
        storageClassName: gp3
        resources:
          requests:
            storage: 50Gi
  serviceMonitorSelector:
    matchLabels:
      release: prometheus
```

```yaml
# Object storage configuration
apiVersion: v1
kind: Secret
metadata:
  name: thanos-objstore-config
  namespace: monitoring
stringData:
  objstore.yml: |
    type: S3
    config:
      bucket: thanos-metrics-longterm
      endpoint: s3.us-east-1.amazonaws.com
      region: us-east-1
```

### Thanos Querier (Central Query Endpoint)

To view the data, you deploy a Thanos Querier in a central management cluster. The Querier exposes a standard PromQL API. When it receives a query from Grafana, it intelligently fans out the request. It asks the local Sidecars for recent, un-uploaded data, and asks the Store Gateway for older historical data fetched from S3.

```yaml
# Deploy in a central management cluster
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-querier
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: thanos-querier
  template:
    metadata:
      labels:
        app: thanos-querier
    spec:
      containers:
        - name: querier
          image: quay.io/thanos/thanos:v0.36.1
          args:
            - query
            - --http-address=0.0.0.0:9090
            - --grpc-address=0.0.0.0:10901
            # Connect to Thanos sidecars in each cluster
            - --store=thanos-sidecar.cluster-a.monitoring.svc:10901
            - --store=thanos-sidecar.cluster-b.monitoring.svc:10901
            # Connect to Thanos Store Gateway (for historical data)
            - --store=thanos-store-gateway:10901
            # Deduplicate HA Prometheus pairs
            - --query.replica-label=prometheus_replica
          ports:
            - name: http
              containerPort: 9090
            - name: grpc
              containerPort: 10901
```

```yaml
# Thanos Store Gateway (serves data from object storage)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-store-gateway
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: thanos-store
  template:
    metadata:
      labels:
        app: thanos-store
    spec:
      containers:
        - name: store
          image: quay.io/thanos/thanos:v0.36.1
          args:
            - store
            - --data-dir=/data
            - --objstore.config-file=/etc/thanos/objstore.yml
            - --grpc-address=0.0.0.0:10901
          volumeMounts:
            - name: data
              mountPath: /data
            - name: objstore-config
              mountPath: /etc/thanos
      volumes:
        - name: objstore-config
          secret:
            secretName: thanos-objstore-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        storageClassName: gp3
        resources:
          requests:
            storage: 20Gi  # Cache for frequently accessed blocks
```

### Thanos vs. Cortex vs. Mimir

When architecting for scale, engineers typically weigh Thanos against push-based alternatives like Grafana Mimir. Both solve the long-term storage and global query problem, but they do so using fundamentally different topological designs. 

| Feature | Thanos | Cortex | Grafana Mimir |
|---|---|---|---|
| Architecture | Sidecar-based (near Prometheus) | Push-based (remote_write) | Push-based (remote_write) |
| Query | Fan-out to sidecars + store | Centralized query frontend | Centralized query frontend |
| Storage | Object storage (S3/GCS) | Object storage + index store | Object storage |
| Multi-tenancy | Labels only | Native (per-tenant storage) | Native (per-tenant limits) |
| Operational complexity | Medium (many components) | High (many microservices) | Medium (simplified Cortex) |
| Best for | Multi-cluster with existing Prometheus | Large multi-tenant platforms | Large multi-tenant platforms |
| License | Apache 2.0 | Apache 2.0 | AGPL 3.0 |

> **Stop and think**: If the Thanos Compactor goes down for 48 hours, what happens to your Grafana dashboards? Would you lose data, or just experience slower queries when looking at historical data from a week ago?

---

## OpenTelemetry Collector at Scale

The OpenTelemetry (OTel) Collector acts as a vendor-agnostic ingestion pipeline, standardizing the receipt, processing, and exportation of all telemetry signals: metrics, logs, and distributed traces. At enterprise scale, the Collector becomes the single most critical data router in your architecture.

Deploying OTel as a DaemonSet ensures that every Kubernetes node has a localized agent capable of collecting node-level metrics (from kubelet), intercepting standard out logs, and receiving application traces with minimal network latency.

```mermaid
flowchart LR
    subgraph Applications
        Pod1[Pod OTLP]
        Pod2[Pod OTLP]
        Pod3[Pod Prom]
    end
    
    Kubelet[kubelet metrics]
    cAdvisor[cadvisor metrics]
    NodeExp[node-exporter]
    
    subgraph OTel Collector per node
        direction TB
        subgraph Receivers
            R_OTLP[OTLP gRPC/HTTP]
            R_Prom[Prometheus scrape]
            R_Filelog[Filelog container logs]
        end
        subgraph Processors
            P_Batch[batch]
            P_Filter[filter]
            P_Trans[transform]
            P_Samp[tail_sampling]
            P_Mem[memory_limiter]
        end
        subgraph Exporters
            E_Prom[prometheusremotewrite]
            E_Loki[loki]
            E_OTLP[otlp to Tempo]
        end
        Receivers --> Processors --> Exporters
    end
    
    Pod1 --> R_OTLP
    Pod2 --> R_OTLP
    Pod3 -.-> R_Prom
    
    Kubelet --> R_Prom
    cAdvisor --> R_Prom
    NodeExp --> R_Prom
    
    E_Prom --> Thanos[Thanos/Mimir\nmetrics]
    E_Loki --> Loki[Loki/Elasticsearch\nlogs]
    E_OTLP --> Tempo[Tempo/Jaeger\ntraces]
```

### OTel Collector Configuration

A production-grade Collector configuration heavily utilizes Processors. The `memory_limiter` processor is particularly vital; it forcefully drops telemetry data when the pod's memory usage approaches critical thresholds, ensuring the Collector does not trigger a cascading node-level OOM kill.

```yaml
# OTel Collector deployed as DaemonSet (one per node)
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata:
  name: otel-node-collector
  namespace: monitoring
spec:
  mode: daemonset
  config:
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

      # Scrape Prometheus endpoints from pods with annotations
      prometheus:
        config:
          scrape_configs:
            - job_name: 'kubernetes-pods'
              kubernetes_sd_configs:
                - role: pod
              relabel_configs:
                - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
                  action: keep
                  regex: true

      # Collect container logs from the node
      filelog:
        include:
          - /var/log/pods/*/*/*.log
        operators:
          - type: router
            routes:
              - output: parse_json
                expr: 'body matches "^\\{"'
              - output: parse_plain
                expr: 'true'
          - id: parse_json
            type: json_parser
          - id: parse_plain
            type: regex_parser
            regex: '^(?P<message>.*)$'

    processors:
      # Prevent OOM by limiting memory usage
      memory_limiter:
        check_interval: 5s
        limit_percentage: 80
        spike_limit_percentage: 25

      # Batch telemetry for efficient export
      batch:
        send_batch_size: 1024
        timeout: 5s

      # Add Kubernetes metadata to all telemetry
      k8sattributes:
        auth_type: serviceAccount
        extract:
          metadata:
            - k8s.pod.name
            - k8s.namespace.name
            - k8s.deployment.name
            - k8s.node.name
          labels:
            - tag_name: team
              key: team
            - tag_name: app
              key: app

      # Filter out noisy metrics to reduce cardinality
      filter:
        metrics:
          exclude:
            match_type: regexp
            metric_names:
              - go_.*           # Go runtime metrics (usually not needed)
              - process_.*      # Process metrics (usually not needed)
              - promhttp_.*     # Prometheus client metrics

    exporters:
      prometheusremotewrite:
        endpoint: "http://thanos-receive:19291/api/v1/receive"
        tls:
          insecure: true

      loki:
        endpoint: "http://loki-gateway:3100/loki/api/v1/push"

      otlp/tempo:
        endpoint: "tempo-distributor:4317"
        tls:
          insecure: true

    service:
      pipelines:
        metrics:
          receivers: [otlp, prometheus]
          processors: [memory_limiter, k8sattributes, filter, batch]
          exporters: [prometheusremotewrite]
        logs:
          receivers: [filelog]
          processors: [memory_limiter, k8sattributes, batch]
          exporters: [loki]
        traces:
          receivers: [otlp]
          processors: [memory_limiter, k8sattributes, batch]
          exporters: [otlp/tempo]
```

> **Pause and predict**: If you configure the `memory_limiter` processor in the OTel Collector to drop telemetry when it hits 90% memory, and there is a sudden spike in log volume, which signal (metrics, logs, or traces) gets dropped first? Or are they dropped equally?

---

## Centralized Logging at Scale with Loki

Traditional log aggregation systems, such as Elasticsearch, ingest textual logs and build extensive, full-text inverted indices. While this permits ultra-fast keyword searches, the index itself frequently grows larger than the raw log data, resulting in exorbitant storage costs and massive memory overhead.

### Loki: The Log Aggregation System Built for Kubernetes

Grafana Loki addresses this by adopting a design philosophy heavily inspired by Prometheus. Loki does not index the actual text content of a log line. Instead, it groups log lines into compressed chunks and exclusively indexes the metadata labels attached to them (e.g., `namespace="production"`, `app="payment-gateway"`).

```mermaid
flowchart TD
    subgraph Clusters
        C_A[Cluster A OTel]
        C_B[Cluster B OTel]
        C_C[Cluster C OTel]
    end
    
    subgraph Loki Distributed
        Distributor[Distributor\nreceives streams]
        Ingester[Ingester\nWAL + in-memory index]
        ObjStore[(Object Storage\nchunks + index)]
        Querier[Querier\nreads ingesters + storage]
        QueryFE[Query Frontend\ncaching, splitting]
    end
    
    C_A --> Distributor
    C_B --> Distributor
    C_C --> Distributor
    
    Distributor --> Ingester
    Ingester --> ObjStore
    
    QueryFE --> Querier
    Querier --> Ingester
    Querier --> ObjStore
```

This deliberate trade-off makes ingestion and long-term storage exponentially cheaper. When executing a search query, Loki quickly identifies the relevant compressed chunks using the label index and then brute-force scans (greps) through the chunk content in memory.

### Loki Deployment for Multi-Cluster

Loki can be deployed in a distributed mode, breaking apart the read and write paths into discrete microservices (Distributor, Ingester, Querier). This allows you to independently scale ingestion bandwidth separately from query processing power.

```yaml
# Loki values for Helm (distributed mode)
# helm install loki grafana/loki -n monitoring -f loki-values.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: monitoring
data:
  loki.yaml: |
    auth_enabled: true  # Multi-tenant mode

    server:
      http_listen_port: 3100

    common:
      storage:
        s3:
          bucketnames: loki-chunks-prod
          region: us-east-1

    limits_config:
      retention_period: 30d
      max_query_lookback: 30d
      ingestion_rate_mb: 20       # Per-tenant rate limit
      ingestion_burst_size_mb: 30
      max_streams_per_user: 50000
      max_label_name_length: 1024
      max_label_value_length: 2048

    schema_config:
      configs:
        - from: 2026-01-01
          store: tsdb
          object_store: s3
          schema: v13
          index:
            prefix: loki_index_
            period: 24h

    compactor:
      working_directory: /data/compactor
      retention_enabled: true
```

### Log Volume Control

At a massive scale, an unoptimized service blindly logging at the `DEBUG` level can single-handedly saturate a cluster's network interfaces and exhaust centralized storage budgets. OpenTelemetry allows you to assert authoritative control over log volumes before they ever leave the node.

```yaml
# OTel Collector: Filter noisy logs before they reach Loki
processors:
  filter/logs:
    logs:
      exclude:
        match_type: regexp
        bodies:
          - "health check"
          - "GET /healthz"
          - "GET /readyz"
          - "GET /metrics"
        resource_attributes:
          - key: k8s.namespace.name
            value: "kube-system"  # Drop kube-system logs

  # Sample verbose logs (keep 10% of DEBUG logs)
  probabilistic_sampler:
    sampling_percentage: 10
    # Only applied to logs where severity == DEBUG

  # Transform: drop specific log fields to reduce size
  transform/logs:
    log_statements:
      - context: log
        statements:
          - delete_key(attributes, "request_headers")
          - delete_key(attributes, "response_body")
          - truncate_all(attributes, 4096)
```

> **Stop and think**: You just deployed a new microservice that logs a unique `request_id` as a label for every single log line. What will happen to your Loki cluster's performance and storage costs over the next few hours?

---

## Cardinality and Cost Management

In time-series databases, cardinality refers to the total number of unique time series actively being tracked. The cardinality of a single metric is determined by multiplying the number of unique values for each associated label. High-cardinality labels—such as explicit IP addresses, unique session tokens, or unsanitized HTTP request paths—are the primary culprits behind Prometheus OOM crashes.

```mermaid
flowchart TD
    Metric["Metric: http_requests_total"]
    
    subgraph Labels ["Labels Contributing to Cardinality"]
        direction TB
        Method["methods: 4 (GET, POST, etc.)"]
        Path["paths: 500 (one per endpoint)"]
        Status["status_codes: 20 (200, 404, etc.)"]
        Pod["pods: 100 (across deployments)"]
        Instance["instances: 50 (nodes)"]
    end
    
    Metric --> Labels
    Labels --> Total["Total time series: 4 * 500 * 20 * 100 * 50 = 200,000,000"]
    
    Total --> Impact["Impact at 200M series:\n- ~400GB memory\n- ~2TB disk (30 days)\n- Minute-long query latency"]
    
    subgraph Fix ["THE FIX: Reduce label cardinality"]
        direction TB
        DropPod["Remove pod label (aggregate at deployment)"]
        BucketPath["Bucket path into categories (/api/users/*)"]
        DropInstance["Remove instance label (aggregate at cluster)"]
    end
    
    Impact --> Fix
    Fix --> NewTotal["After Fix: 4 * 50 * 20 = 4,000 time series\n(50,000x reduction)"]
```

### Controlling Cardinality

By utilizing Prometheus recording rules, platform operators can execute heavy, computationally expensive aggregations directly on the backend, generating new, streamlined metrics. This means when a developer loads a dashboard, Grafana queries the pre-aggregated data rather than forcing Prometheus to calculate massive sums on the fly.

```yaml
# Prometheus recording rules: pre-aggregate to reduce cardinality
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cardinality-reduction
  namespace: monitoring
spec:
  groups:
    - name: aggregated-http-metrics
      interval: 30s
      rules:
        # Aggregate per-pod metrics to per-deployment
        - record: http_requests:rate5m:by_deployment
          expr: |
            sum by (namespace, deployment, method, status_code) (
              rate(http_requests_total[5m])
            )

        # Bucket paths into categories
        - record: http_requests:rate5m:by_path_group
          expr: |
            sum by (namespace, deployment, path_group, method) (
              label_replace(
                rate(http_requests_total[5m]),
                "path_group",
                "$1",
                "path",
                "(/api/[^/]+)/.*"
              )
            )
```

To actively hunt down cardinality offenders within an environment, operators can leverage specific PromQL queries directly against the TSDB metadata.

```bash
# Find the highest cardinality metrics in Prometheus
# (Run this PromQL query in Grafana)

# Top 10 metrics by cardinality
topk(10, count by (__name__)({__name__=~".+"}))

# Find labels causing cardinality explosion for a specific metric
count by (pod) (http_requests_total)
# If this returns 500+ series, "pod" label is too granular
```

> **Pause and predict**: If you implement a recording rule to aggregate metrics by deployment, what happens to the historical data stored under the original pod-level metric name?

---

## Cross-Cloud Distributed Tracing

As architectures fracture into dozens of microservices deployed across disparate Kubernetes clusters, traditional single-service logging becomes insufficient for diagnosing systemic latency. Distributed tracing tracks the complete lifecycle of a single request as it traverses network boundaries, database calls, and inter-service HTTP requests. 

This relies heavily on trace context propagation, where standard HTTP headers (such as the W3C standard `traceparent`) are seamlessly injected and extracted by each service.

```mermaid
flowchart TD
    subgraph Cluster A us-east-1
        FES[Frontend Service\ntrace_id: abc123\nspan_id: span-1]
        API[API Gateway\ntrace_id: abc123\nspan_id: span-2\nparent: span-1]
    end
    
    subgraph Cluster B eu-west-1
        Pay[Payment Service\ntrace_id: abc123\nspan_id: span-3\nparent: span-2]
        Fraud[Fraud Check Service\ntrace_id: abc123\nspan_id: span-4\nparent: span-3]
    end
    
    FES -->|HTTP header: traceparent| Pay
    FES --> API
    Pay --> Fraud
    
    OTelA[OTel Collector]
    OTelB[OTel Collector]
    
    API --> OTelA
    Fraud --> OTelB
    
    Tempo[(Tempo / Jaeger\nStores all spans for abc123)]
    
    OTelA --> Tempo
    OTelB --> Tempo
```

> **Pause and predict**: If the Frontend Service and Payment Service belong to different teams using different tracing instrumentation (e.g., Jaeger vs. Zipkin clients), what happens to the trace context when the HTTP request crosses the cluster boundary?

### Tail-Based Sampling for Traces

Ingesting and storing 100% of generated distributed traces is often financially unviable. Most systems implement sampling strategies. Standard "head-based" sampling makes a random drop-or-keep decision the moment a request starts. However, this means you will frequently drop traces for transactions that eventually fail later in the pipeline.

Tail-based sampling resolves this by holding all constituent spans of a trace in a temporary memory buffer until the entire request completes. Only then does it execute policy decisions, guaranteeing that any trace containing an error or exceeding latency thresholds is preserved.

```yaml
# OTel Collector with tail-based sampling
# Deploy as a Deployment (NOT DaemonSet) for trace aggregation
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata:
  name: otel-trace-sampler
  namespace: monitoring
spec:
  mode: deployment
  replicas: 3
  config:
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317

    processors:
      # Tail-based sampling: decide AFTER seeing the full trace
      tail_sampling:
        decision_wait: 10s  # Wait for all spans to arrive
        num_traces: 100000  # Buffer size
        policies:
          # Always keep error traces
          - name: errors
            type: status_code
            status_code:
              status_codes:
                - ERROR
          # Always keep slow traces (>2s)
          - name: slow-traces
            type: latency
            latency:
              threshold_ms: 2000
          # Sample 5% of normal traces
          - name: normal-sampling
            type: probabilistic
            probabilistic:
              sampling_percentage: 5

    exporters:
      otlp/tempo:
        endpoint: "tempo-distributor:4317"
        tls:
          insecure: true

    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [tail_sampling]
          exporters: [otlp/tempo]
```

---

## Did You Know?

1. **Prometheus was created at SoundCloud in 2012** and was the second project (after Kubernetes) to join the CNCF in 2016. It now monitors over 10 million Kubernetes clusters worldwide. Despite this ubiquity, Prometheus was never designed for multi-cluster or long-term storage -- those capabilities come from ecosystem projects like Thanos, Cortex, and Mimir. The Prometheus project maintainers have explicitly stated that horizontal scalability is not a goal of the core project.

2. **A single Kubernetes node generates approximately 500-800 metric time series** just from kubelet and cAdvisor metrics, before any application metrics. A 100-node cluster starts with 50,000-80,000 baseline time series. Application metrics typically add 3-10x on top of this. This means a 100-node cluster with microservices easily reaches 500K-1M time series -- the point where a single Prometheus instance starts struggling.

3. **Grafana Loki's index is 10-100x smaller than Elasticsearch's** for the same log volume. Loki achieves this by indexing only labels (key-value metadata like namespace, pod name, and level), not the full text content. This means Loki is dramatically cheaper for storage but slower for full-text search queries. The design bet is that most log queries in Kubernetes filter by namespace and pod first, then grep through a small subset -- a bet that has proven correct for the majority of operational use cases.

4. **OpenTelemetry became the second most active CNCF project** (after Kubernetes itself) in 2023 by contributor count. The project unified three competing standards: OpenTracing, OpenCensus, and the W3C Trace Context specification. The OTel Collector alone processes billions of telemetry signals per day across production deployments worldwide, making it arguably the most widely deployed data pipeline in cloud-native infrastructure.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Running a single Prometheus for all clusters | "Prometheus can handle it" | Shard Prometheus per cluster. Use Thanos or Mimir for cross-cluster querying. No single Prometheus should scrape more than 1M time series. |
| Storing metrics at full resolution forever | "We might need it" | Use Thanos Compactor to downsample: 5-second resolution for 2 weeks, 1-minute for 3 months, 5-minute for 1 year. Saves 90%+ storage. |
| No cardinality limits on application metrics | "Developers know best" | Set ingestion limits (per-tenant in Mimir, series limits in Prometheus). Add pre-aggregation rules. High-cardinality labels (user_id, request_id) should be trace attributes, not metric labels. |
| Logging everything at DEBUG level in production | "We might need the details" | Default to INFO in production. Use dynamic log level changes for debugging specific services. A single DEBUG-level service can generate more log volume than the rest of the cluster. |
| Not using tail-based sampling for traces | "We keep all traces" | At 10,000 spans/second, storing all traces costs thousands per month. Tail-based sampling keeps errors and slow traces (the ones you investigate) while sampling 5-10% of normal traces. |
| Running OTel Collector as a Deployment instead of DaemonSet for logs | "One collector is simpler" | A single Collector becomes a bottleneck and SPOF. DaemonSet (one per node) distributes the load and ensures logs are collected even if a collector crashes. Use Deployment only for aggregation/sampling tiers. |
| No resource limits on monitoring components | "Monitoring should always run" | A memory-unlimited Prometheus that OOM-kills takes down monitoring AND the node. Set memory limits and use memory_limiter processor in OTel Collector. |
| Separate dashboards per cluster | "Each team manages their own Grafana" | Use a central Grafana with Thanos as the data source. Cluster-specific dashboards with a cluster selector variable. Single pane of glass for on-call. |

---

## Quiz

<details>
<summary>1. Your organization has just acquired a startup, adding 5 new Kubernetes clusters to your existing 3. You decide to point your central Prometheus instance to scrape all 8 clusters. Within hours, Prometheus starts crash-looping. Why did this architectural decision fail, and what specific limitations were hit?</summary>

Prometheus was designed with a single-node, pull-based architecture that fundamentally assumes all targets are within the same cluster boundaries. When you point a single Prometheus at 8 clusters, it attempts to hold all active time series from every cluster in memory simultaneously, which quickly leads to catastrophic out-of-memory (OOM) crashes. Additionally, pulling metrics across cluster networks introduces significant latency and requires exposing secure metric endpoints to the public internet or managing complex VPNs. By adopting a distributed approach like Thanos or Mimir, you can keep a lightweight Prometheus scraper inside each cluster to handle local ingestion. These tools then push or serve the data to a centralized query tier, preventing any single instance from bearing the memory burden of the entire fleet.
</details>

<details>
<summary>2. You are tasked with designing a multi-cluster metrics platform. Your manager asks you to choose between Thanos and Grafana Mimir. You currently have Prometheus deployed in all clusters and rely heavily on it for local alerting. Which architectural differences should drive your decision?</summary>

The core architectural difference lies in how data is transported and queried across the platform. Thanos uses a decentralized, sidecar-based approach where your existing Prometheus instances continue to store short-term data, while the Thanos Querier reaches into each cluster to fan-out queries. This is ideal when you want to heavily leverage existing Prometheus deployments for local alerting, as local data remains accessible even if the central control plane is disconnected. Grafana Mimir, conversely, uses a push-based model where Prometheus simply acts as an agent forwarding data via `remote_write` to a centralized Mimir backend. Mimir is generally preferred if you need robust multi-tenancy and want to centralize all storage and querying, but it requires completely offloading storage responsibilities from your local Prometheus instances.
</details>

<details>
<summary>3. During a major marketing event, your Prometheus memory usage spikes from 32GB to 128GB in 10 minutes, and queries for `http_requests_total` time out. You discover this metric now has 200 million unique time series. What specific anti-pattern likely caused this sudden cardinality explosion, and how do you resolve it?</summary>

This sudden explosion in time series is almost certainly caused by developers injecting high-cardinality data—such as unique user IDs, transaction IDs, or raw request paths—into metric labels. Because every unique combination of label values creates an entirely new time series in the TSDB, a surge in unique users directly translates to a surge in memory consumption. To resolve this, you should quickly drop the offending labels using Prometheus relabeling rules or OTel Collector processors to stabilize the system. Moving forward, high-cardinality identifiers should be migrated to distributed trace attributes or structured logs, while metrics should only use bounded categories like HTTP status codes or normalized route templates.
</details>

<details>
<summary>4. Your security team is complaining that searching for a specific IP address across a month of Loki logs takes several minutes, whereas it took seconds in their old Elasticsearch cluster. However, your infrastructure bill is now 90% lower. What fundamental design choice in Loki explains both the cost savings and the slow query performance for this specific task?</summary>

Loki deliberately avoids building full-text inverted indexes of the actual log content, which is the primary driver of both storage costs and compute overhead in systems like Elasticsearch. Instead, Loki only indexes the metadata labels (such as namespace, application name, and log level) attached to the log streams. When the security team searches for an IP address, Loki must first use the label index to find the relevant chunks of compressed log text, and then literally scan through those text chunks to find the IP matches. This architectural trade-off sacrifices raw full-text search speed in exchange for massive storage efficiency, making it perfect for targeted operational debugging but less optimal for needle-in-a-haystack security forensics.
</details>

<details>
<summary>5. You are implementing distributed tracing for a high-traffic e-commerce site. You configure your OTel Collectors to sample 10% of all traces. The next day, developers complain that whenever a checkout fails, the corresponding trace is almost always missing from Tempo. Why did this sampling strategy fail your team, and what approach would guarantee error traces are kept?</summary>

You implemented head-based sampling, which makes a randomized keep-or-drop decision at the very beginning of the request lifecycle before the system knows whether the transaction will succeed or fail. Because failures are statistically rare, a 10% random sample means there is a 90% chance that the trace for a failed checkout is immediately discarded. To guarantee that valuable traces are retained, you must implement tail-based sampling in your OTel Collector architecture. Tail-based sampling buffers the entire trace in memory until it completes, allowing you to evaluate the full transaction and apply intelligent policies that typically keep traces containing errors or high latency while randomly sampling the successful, routine requests.
</details>

<details>
<summary>6. A poorly configured Java application goes into a crash loop, spamming multiline stack traces at DEBUG level. Within an hour, it consumes your entire daily logging quota in Loki, causing logs from other critical services to be dropped. How can you design a multi-layered filtering strategy to prevent this single service from monopolizing your log pipeline?</summary>

To prevent a single runaway application from taking down your logging infrastructure, you must implement controls at multiple stages of the telemetry pipeline. First, establish strict log level configurations at the application level to ensure production services default to INFO or WARN, preventing DEBUG spam from ever being emitted. Second, deploy OpenTelemetry Collectors configured with filtering processors to drop known noisy patterns or truncate excessively large log bodies before they consume network bandwidth. Finally, configure tenant-based rate limiting and quota enforcement within Loki itself. This ensures that even if an application bypasses local filters, it will only exhaust its own isolated namespace quota without impacting the observability of other critical infrastructure.
</details>

---

## Hands-On Exercise: Build a Multi-Cluster Monitoring Stack

In this advanced exercise, you will manually provision and configure a robust monitoring stack featuring Prometheus, a simulated Thanos Sidecar arrangement, an OpenTelemetry Collector, Loki for log aggregation, and Grafana for visualization. 

### Prerequisites

- kind cluster configured locally
- Helm package manager installed
- kubectl installed and configured

### Task 1: Deploy Prometheus with Thanos Sidecar

Initiate the deployment of the kube-prometheus-stack, injecting the Thanos sidecar to simulate local metric persistence destined for object storage.

<details>
<summary>Solution</summary>

```bash
# Create cluster
kind create cluster --name obs-lab --image kindest/node:v1.35.0

# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack with Thanos sidecar
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.replicas=1 \
  --set prometheus.prometheusSpec.retention=6h \
  --set 'prometheus.prometheusSpec.externalLabels.cluster=obs-lab' \
  --set 'prometheus.prometheusSpec.externalLabels.region=local' \
  --set alertmanager.enabled=false

# Wait for Prometheus to be ready
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s

echo "Prometheus deployed with cluster labels"
```
</details>

### Task 2: Deploy Loki and OpenTelemetry Collector

Establish the log ingestion pathway. You will deploy Loki to store the logs and immediately overlay an OpenTelemetry Collector configured to dynamically process local container standard outputs.

<details>
<summary>Solution</summary>

```bash
# Add Loki helm repo
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Loki in single-binary mode for the lab
helm install loki grafana/loki \
  --namespace monitoring \
  --set deploymentMode=SingleBinary \
  --set loki.auth_enabled=false \
  --set loki.commonConfig.replication_factor=1 \
  --set loki.storage.type=filesystem \
  --set singleBinary.replicas=1

# Install OpenTelemetry Operator/Collector
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

# Create OTel Collector values
cat <<'EOF' > otel-values.yaml
mode: daemonset
config:
  receivers:
    filelog:
      include: [ /var/log/pods/*/*/*.log ]
  processors:
    memory_limiter:
      check_interval: 1s
      limit_percentage: 75
      spike_limit_percentage: 15
    batch:
      send_batch_size: 10000
      timeout: 10s
  exporters:
    loki:
      endpoint: "http://loki:3100/loki/api/v1/push"
  service:
    pipelines:
      logs:
        receivers: [filelog]
        processors: [memory_limiter, batch]
        exporters: [loki]
EOF

helm install otel-collector open-telemetry/opentelemetry-collector \
  --namespace monitoring \
  -f otel-values.yaml

# Wait for components
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=loki -n monitoring --timeout=300s
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=opentelemetry-collector -n monitoring --timeout=300s

echo "Loki and OTel Collector deployed successfully"
```
</details>

### Task 3: Deploy Sample Workloads with Metrics

To verify the ingestion engines are functioning properly, spin up a transient workload emitting standard Nginx metrics. Ensure that the namespace matches the pre-configured scraping annotations.

<details>
<summary>Solution</summary>

```bash
# Deploy a sample app with Prometheus metrics
kubectl create namespace sample-app

kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
  namespace: sample-app
  labels:
    team: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
        team: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "80"
    spec:
      containers:
        - name: nginx
          image: nginx:stable
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: web-server
  namespace: sample-app
spec:
  selector:
    app: web-server
  ports:
    - port: 80
EOF

kubectl wait --for=condition=Ready pod -l app=web-server -n sample-app --timeout=60s
```
</details>

### Task 4: Query Cross-Cluster Metrics

Execute direct PromQL requests using `curl` against the exposed Prometheus API to validate the existence of cluster external labels—a necessity for multi-cluster disambiguation.

<details>
<summary>Solution</summary>

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &

sleep 3

# Query metrics using curl (PromQL API)
echo "=== Node Count ==="
curl -s 'http://localhost:9090/api/v1/query?query=count(up{job="kubelet"})' | jq '.data.result[0].value[1]'

echo "=== Pod Count by Namespace ==="
curl -s 'http://localhost:9090/api/v1/query?query=count(kube_pod_info)%20by%20(namespace)' | jq '.data.result[]'

echo "=== Top CPU Consumers ==="
curl -s 'http://localhost:9090/api/v1/query?query=topk(5,%20sum%20by%20(namespace,%20pod)%20(rate(container_cpu_usage_seconds_total{container!=""}[5m])))' | jq '.data.result[]'

echo "=== Cluster Label (confirms external labels work) ==="
curl -s 'http://localhost:9090/api/v1/query?query=up{job="kubelet"}' | jq '.data.result[0].metric.cluster'

# Stop port-forward
kill %1 2>/dev/null
```
</details>

### Task 5: Query Loki Logs via CLI

Validate that the OpenTelemetry log pipeline is successfully intercepting file logs and flushing them to Loki by leveraging the LogQL API.

<details>
<summary>Solution</summary>

```bash
# Port-forward to Loki
kubectl port-forward -n monitoring svc/loki 3100:3100 &

sleep 3

echo "=== Recent Log Lines from Sample App ==="
# We use LogQL to fetch logs from the sample app namespace
curl -s -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="sample-app"}' \
  --data-urlencode 'limit=5' | jq '.data.result[0].stream'

kill %1 2>/dev/null
```
</details>

### Task 6: Create a Cardinality Report

Diagnose potential TSDB bloat by generating an automated cardinality report, showcasing the metrics responsible for creating the most time series inside the database block.

<details>
<summary>Solution</summary>

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &

sleep 3

echo "=== Total Active Time Series ==="
curl -s 'http://localhost:9090/api/v1/query?query=prometheus_tsdb_head_series' | \
  jq '.data.result[0].value[1]'

echo ""
echo "=== Top 10 Metrics by Series Count ==="
curl -s 'http://localhost:9090/api/v1/query?query=topk(10,%20count%20by%20(__name__)({__name__=~".%2B"}))' | \
  jq -r '.data.result[] | "\(.metric.__name__): \(.value[1]) series"'

echo ""
echo "=== Series Count by Job ==="
curl -s 'http://localhost:9090/api/v1/query?query=count%20by%20(job)%20({__name__=~".%2B"})' | \
  jq -r '.data.result[] | "\(.metric.job): \(.value[1]) series"'

echo ""
echo "=== Cardinality Recommendations ==="
echo "- If any single metric exceeds 10,000 series: investigate labels"
echo "- If total series > 500K: consider pre-aggregation with recording rules"
echo "- If 'pod' label creates >100 unique values: aggregate to deployment level"

kill %1 2>/dev/null
```
</details>

### Task 7: Set Up Grafana Dashboard

Conclude the setup by provisioning an interactive visualization layer, proving that all the previously verified metrics flow successfully into graphical panels.

<details>
<summary>Solution</summary>

```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &

sleep 3

# Default credentials: admin / prom-operator
echo "Grafana available at http://localhost:3000"
echo "Username: admin"
echo "Password: prom-operator"

echo ""
echo "=== Dashboard Setup Steps ==="
echo "1. Log in to Grafana at http://localhost:3000"
echo "2. Navigate to Dashboards > New > Import"
echo "3. Import dashboard ID 315 (Kubernetes Cluster Monitoring)"
echo "4. Select the 'Prometheus' data source"
echo "5. Verify metrics appear with cluster=obs-lab label"

# Alternative: create dashboard via API
curl -s -X POST http://admin:prom-operator@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "Cost Audit - Cluster Overview",
      "panels": [
        {
          "title": "Active Time Series",
          "type": "stat",
          "targets": [{"expr": "prometheus_tsdb_head_series"}],
          "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
        },
        {
          "title": "Pods by Namespace",
          "type": "piechart",
          "targets": [{"expr": "count(kube_pod_info) by (namespace)"}],
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
        }
      ]
    },
    "overwrite": true
  }' 2>/dev/null && echo "Dashboard created" || echo "Dashboard creation via API (optional)"

kill %1 2>/dev/null
```
</details>

### Clean Up

Always tear down infrastructure locally to free up resources immediately after laboratory exercises.

```bash
kind delete cluster --name obs-lab
```

### Success Criteria

- [ ] Prometheus correctly deployed with external labels injected (`cluster`, `region`).
- [ ] Loki and OpenTelemetry Collector daemonsets deployed and streaming unstructured pod logs without crashing.
- [ ] Sample Nginx workloads successfully scraped by Prometheus and their output logs retrieved by OTel.
- [ ] Manual PromQL validation queries consistently return JSON results with cluster labels intact.
- [ ] Native LogQL queries cleanly return application logs from Loki's backend.
- [ ] The automated cardinality report accurately identifies the specific top metrics driving series count bloat.
- [ ] The main Grafana service is highly accessible over a secure port forward, with the correct Prometheus data source globally configured.

---

## Next Module

[Module 8.10: Scaling IaC & State Management](../module-8.10-iac-scale/) -- Your clusters are now highly observable, your ingestion costs are firmly optimized, and your architecture cleanly spans multiple regions. It is time to learn how to actively manage the infrastructure as code (IaC) that holds it all together. Delve into advanced Terraform state partitioning, robust module design, enterprise GitOps integration, and aggressive drift detection at massive operational scale.

## Sources

- [Grafana Loki Overview](https://grafana.com/docs/loki/latest/get-started/overview/) — Covers Loki's label-based indexing model, storage design, and deployment modes for scalable logging.
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) — Primary overview of the Collector's role as a vendor-agnostic telemetry ingestion, processing, and export pipeline.

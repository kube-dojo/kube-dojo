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

- **Design large-scale observability architectures that handle millions of time series and terabytes of log data**
- **Implement centralized logging pipelines using Fluentd/Fluent Bit, cloud-native log services, and retention policies**
- **Configure distributed tracing with OpenTelemetry across multi-cluster Kubernetes environments**
- **Optimize observability costs by implementing sampling strategies, metric aggregation, and tiered storage retention**

---

## Why This Module Matters

**August 2023. A fintech company. 14 Kubernetes clusters. 2,800 pods. One Prometheus server.**

The single Prometheus instance had been the monitoring backbone for two years. Then the company doubled its microservices count in six months. Prometheus memory usage climbed from 16GB to 64GB. Query latency went from sub-second to 30 seconds. Cardinality -- the number of unique time series -- hit 12 million. Prometheus started OOM-killing every 48 hours. The on-call team's dashboards took so long to load that they switched to `kubectl logs` for incident response, which meant they were debugging production with grep instead of metrics.

The team tried the obvious fix: give Prometheus more memory. At 128GB, it stabilized but startup time after a crash was 25 minutes (replaying the WAL). During those 25 minutes, there was no monitoring. They were flying blind during the most critical moment -- right after a failure that had already crashed their monitoring system.

The real fix required architectural changes: sharding Prometheus across clusters, adding Thanos for long-term storage and cross-cluster queries, deploying OpenTelemetry collectors to pre-aggregate and filter telemetry before it hit storage, and implementing cardinality controls to prevent the next explosion. This module teaches you how to build observability infrastructure that scales to hundreds of clusters and millions of time series without becoming the problem it's supposed to solve.

---

## The Observability Scale Problem

Observability at scale is fundamentally a data problem. More clusters, more pods, more services means more metrics, more logs, and more traces. The cost and complexity of processing this data grows faster than the infrastructure it monitors.

```
TELEMETRY VOLUME AT SCALE
════════════════════════════════════════════════════════════════

  Cluster size:           Small        Medium       Large
  Nodes:                  10           50           200
  Pods:                   200          2,000        15,000
  Services:               20           100          500

  Metrics:
  Time series:            50K          500K         5M+
  Samples/second:         5K           50K          500K
  Storage (30 days):      10GB         100GB        1TB+

  Logs:
  Lines/second:           500          5,000        50,000
  Storage (30 days):      50GB         500GB        5TB+

  Traces:
  Spans/second:           100          1,000        10,000
  Storage (30 days):      5GB          50GB         500GB+

  At scale, the monitoring infrastructure can become the
  most expensive service in the cluster.
```

---

## Multi-Cluster Prometheus with Thanos

Prometheus was designed for a single cluster. When you have multiple clusters, you need a way to query across all of them, store data long-term (beyond Prometheus's local retention), and deduplicate data from HA pairs.

### Thanos Architecture

```
THANOS ARCHITECTURE
════════════════════════════════════════════════════════════════

  Cluster A                    Cluster B
  ┌───────────────────────┐   ┌───────────────────────┐
  │ Prometheus + Sidecar  │   │ Prometheus + Sidecar  │
  │ ┌─────────┐┌────────┐│   │ ┌─────────┐┌────────┐│
  │ │Prometheus││ Thanos ││   │ │Prometheus││ Thanos ││
  │ │ (scrape) ││Sidecar ││   │ │ (scrape) ││Sidecar ││
  │ │          ││(upload) ││   │ │          ││(upload) ││
  │ └─────────┘└───┬────┘│   │ └─────────┘└───┬────┘│
  └───────────────┬┘──────┘   └───────────────┬┘──────┘
                  │                            │
                  │  Upload TSDB blocks        │
                  ▼                            ▼
          ┌──────────────────────────────────────┐
          │     Object Storage (S3/GCS/Azure)    │
          │     Long-term metric storage         │
          │     (unlimited retention, cheap)      │
          └──────────────┬───────────────────────┘
                         │
          ┌──────────────┴───────────────────────┐
          │          Thanos Components            │
          │                                      │
          │  ┌─────────────┐  ┌───────────────┐  │
          │  │ Store Gateway│  │    Compactor  │  │
          │  │ (reads from  │  │ (downsample,  │  │
          │  │  object store│  │  compact      │  │
          │  │  for old data│  │  blocks)      │  │
          │  └──────┬──────┘  └───────────────┘  │
          │         │                            │
          │  ┌──────┴──────┐                     │
          │  │   Querier   │  ← Grafana queries  │
          │  │ (fan-out to │     this endpoint    │
          │  │  all sources│                     │
          │  │  Prom+Store)│                     │
          │  └─────────────┘                     │
          └──────────────────────────────────────┘
```

### Deploying Thanos with Prometheus Operator

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
---
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
---
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

| Feature | Thanos | Cortex | Grafana Mimir |
|---|---|---|---|
| Architecture | Sidecar-based (near Prometheus) | Push-based (remote_write) | Push-based (remote_write) |
| Query | Fan-out to sidecars + store | Centralized query frontend | Centralized query frontend |
| Storage | Object storage (S3/GCS) | Object storage + index store | Object storage |
| Multi-tenancy | Labels only | Native (per-tenant storage) | Native (per-tenant limits) |
| Operational complexity | Medium (many components) | High (many microservices) | Medium (simplified Cortex) |
| Best for | Multi-cluster with existing Prometheus | Large multi-tenant platforms | Large multi-tenant platforms |
| License | Apache 2.0 | Apache 2.0 | AGPL 3.0 |

---

## OpenTelemetry Collector at Scale

The OpenTelemetry Collector is a vendor-agnostic pipeline for receiving, processing, and exporting telemetry data (metrics, logs, traces). At scale, it becomes the single most important component in your observability architecture.

```
OTEL COLLECTOR PIPELINE
════════════════════════════════════════════════════════════════

  Applications          OTel Collector (per node)     Backends
  ┌────────────┐       ┌──────────────────────────┐
  │ Pod (OTLP) │──────▶│  Receivers:              │
  │ Pod (OTLP) │       │  - OTLP (gRPC + HTTP)    │
  │ Pod (prom)  │       │  - Prometheus scrape      │──▶ Thanos/Mimir
  └────────────┘       │  - Filelog (container logs)│      (metrics)
                        │                          │
  kubelet metrics ────▶│  Processors:             │──▶ Loki/Elasticsearch
  cadvisor metrics ──▶│  - batch (aggregate)      │      (logs)
  node-exporter ─────▶│  - filter (drop noise)    │
                        │  - transform (enrich)     │──▶ Tempo/Jaeger
                        │  - tail_sampling          │      (traces)
                        │  - memory_limiter         │
                        │                          │
                        │  Exporters:              │
                        │  - prometheusremotewrite  │
                        │  - loki                   │
                        │  - otlp (to Tempo)        │
                        └──────────────────────────┘
```

### OTel Collector Configuration

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

---

## Centralized Logging at Scale

### Loki: The Log Aggregation System Built for Kubernetes

```
LOKI ARCHITECTURE
════════════════════════════════════════════════════════════════

  Cluster A              Cluster B              Cluster C
  ┌────────────┐        ┌────────────┐        ┌────────────┐
  │OTel Collector       │OTel Collector       │OTel Collector
  │  (filelog   │        │  (filelog   │        │  (filelog   │
  │   receiver) │        │   receiver) │        │   receiver) │
  └──────┬─────┘        └──────┬─────┘        └──────┬─────┘
         │                      │                      │
         └──────────────┬───────┴──────────────────────┘
                        │
                        ▼
  ┌──────────────────────────────────────────────┐
  │              Loki (Distributed)               │
  │                                              │
  │  Distributor ──▶ Ingester ──▶ Object Storage │
  │  (receives      (WAL +        (S3/GCS:       │
  │   log streams)   in-memory     chunks +       │
  │                  index)        index)         │
  │                                              │
  │  Querier ◀── Query Frontend                  │
  │  (reads from    (caching,                    │
  │   ingesters     query splitting)             │
  │   + storage)                                 │
  └──────────────────────────────────────────────┘

  Key insight: Loki indexes LABELS, not log content.
  This makes it 10-100x cheaper than Elasticsearch for logs.
  Trade-off: full-text search is slower (grep over chunks).
```

### Loki Deployment for Multi-Cluster

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

At scale, log volume becomes the dominant cost in your observability stack. A single chatty service can generate more logs than the rest of the cluster combined.

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

---

## Cardinality and Cost Management

Cardinality -- the number of unique time series -- is the single biggest factor in metrics cost. Each unique combination of metric name and label values creates a new time series.

```
CARDINALITY EXPLOSION EXAMPLE
════════════════════════════════════════════════════════════════

  Metric: http_requests_total
  Labels: method, path, status_code, pod, instance

  Cardinality calculation:
  methods: 4 (GET, POST, PUT, DELETE)
  paths: 500 (one per API endpoint)
  status_codes: 20 (200, 201, 301, 400, 401, 403, 404, 500...)
  pods: 100 (across all deployments)
  instances: 50 (nodes)

  Total time series: 4 x 500 x 20 x 100 x 50 = 200,000,000

  At 200M time series, Prometheus will use:
  - ~400GB memory
  - ~2TB disk (30-day retention)
  - Query latency: minutes (not seconds)

  THE FIX: Reduce label cardinality
  - Remove "pod" label (aggregate at deployment level)
  - Bucket "path" into categories (/api/users/*, /api/orders/*)
  - Remove "instance" label (aggregate at cluster level)

  After: 4 x 50 x 20 = 4,000 time series (50,000x reduction)
```

### Controlling Cardinality

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

```bash
# Find the highest cardinality metrics in Prometheus
# (Run this PromQL query in Grafana)

# Top 10 metrics by cardinality
topk(10, count by (__name__)({__name__=~".+"}))

# Find labels causing cardinality explosion for a specific metric
count by (pod) (http_requests_total)
# If this returns 500+ series, "pod" label is too granular
```

---

## Cross-Cloud Distributed Tracing

Tracing across clusters and clouds requires a unified trace context that propagates through every service call, regardless of where the services run.

```
CROSS-CLUSTER TRACING
════════════════════════════════════════════════════════════════

  Cluster A (us-east-1)                Cluster B (eu-west-1)
  ┌─────────────────────────┐         ┌─────────────────────────┐
  │  Frontend Service       │         │  Payment Service        │
  │  trace_id: abc123       │  HTTP   │  trace_id: abc123       │
  │  span_id: span-1        │────────▶│  span_id: span-3        │
  │  parent: none           │ header: │  parent: span-2         │
  │                         │ tracep- │                         │
  │  API Gateway            │ arent   │  Fraud Check Service    │
  │  trace_id: abc123       │         │  trace_id: abc123       │
  │  span_id: span-2        │         │  span_id: span-4        │
  │  parent: span-1         │         │  parent: span-3         │
  └─────────────────────────┘         └─────────────────────────┘
         │                                     │
         │  OTel Collector                     │  OTel Collector
         ▼                                     ▼
  ┌──────────────────────────────────────────────────┐
  │              Tempo (Grafana)                      │
  │  or Jaeger / Zipkin                              │
  │                                                  │
  │  Stores all spans for trace abc123               │
  │  Displays the full trace across both clusters    │
  └──────────────────────────────────────────────────┘
```

### Tail-Based Sampling for Traces

At scale, storing every trace is prohibitively expensive. Tail-based sampling keeps interesting traces (errors, slow requests) and drops routine ones.

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
<summary>1. Why does a single Prometheus instance fail at multi-cluster scale?</summary>

Prometheus was designed for a single cluster with a pull-based scraping model. At multi-cluster scale, it faces several limits: (a) memory -- every active time series is held in memory, and 1M+ series requires 32-64GB RAM; (b) single-node architecture -- Prometheus does not support horizontal scaling; (c) network -- scraping targets across cluster boundaries requires exposing metrics endpoints or using federation, both of which add latency and complexity; (d) long-term storage -- local disk retention is limited by disk size and query performance degrades with data volume; (e) HA -- running two Prometheus instances for redundancy doubles the scrape load on targets. Thanos and Mimir solve these by distributing the query and storage layers while keeping Prometheus as the per-cluster scraper.
</details>

<details>
<summary>2. How does Thanos differ architecturally from Grafana Mimir?</summary>

Thanos uses a sidecar-based architecture: a Thanos Sidecar runs alongside each Prometheus instance, uploading TSDB blocks to object storage and serving real-time data to the Thanos Querier. Prometheus continues to scrape and store data locally; Thanos adds long-term storage and cross-cluster querying on top. Mimir uses a push-based architecture: Prometheus uses `remote_write` to push metrics to Mimir's centralized ingest tier. Prometheus is just a scraper; Mimir handles all storage, querying, and compaction. Thanos is better for adding multi-cluster capabilities to existing Prometheus setups. Mimir is better for large-scale multi-tenant platforms where centralized control over ingestion, limits, and storage is important.
</details>

<details>
<summary>3. A metric has 200 million unique time series. What is the likely cause and how do you fix it?</summary>

200M time series indicates a cardinality explosion caused by high-cardinality labels. Common culprits: a label containing user IDs, request IDs, UUIDs, IP addresses, or full URL paths (each unique value creates a new time series). To fix: (1) identify the high-cardinality labels using `count by (<label>) (<metric_name>)` in PromQL, (2) remove or bucket the offending label -- e.g., replace full URL paths with path patterns (/api/users/* instead of /api/users/12345), (3) add recording rules to pre-aggregate at a lower cardinality, (4) set per-metric series limits in Prometheus or Mimir to prevent future explosions, (5) move high-cardinality data to traces (where unique IDs are appropriate) instead of metrics.
</details>

<details>
<summary>4. Why does Loki index only labels, not full log content, and what are the trade-offs?</summary>

Loki indexes only labels (like namespace, pod name, log level) to minimize storage costs. A full-text index (like Elasticsearch's) stores an inverted index of every word in every log line, which can be 10-100x larger than the original log data. By indexing only labels, Loki's index is tiny, making it dramatically cheaper to operate. The trade-off is query performance: a full-text search (e.g., "find all logs containing 'NullPointerException'") requires Loki to scan through compressed log chunks, which is slower than Elasticsearch's index lookup. In practice, this trade-off works well for Kubernetes because most log queries start with a label filter (namespace=payments, pod=api-server-xyz) that narrows the search space, and then grep within that subset.
</details>

<details>
<summary>5. What is tail-based sampling for traces and why is it superior to head-based sampling?</summary>

Head-based sampling makes the keep/drop decision at the start of a trace (when the first span is created). It uses a probability: "keep 10% of traces." The problem is that it randomly drops traces, including traces that contain errors or high latency -- the exact traces you want to investigate. Tail-based sampling waits until the entire trace is complete (all spans have arrived), then makes the decision. It can apply intelligent policies: always keep traces with errors, always keep traces slower than 2 seconds, and sample 5% of everything else. This ensures you have 100% of interesting traces while dramatically reducing storage volume. The trade-off is that tail-based sampling requires buffering complete traces in memory, which adds complexity and memory usage to the sampling collector.
</details>

<details>
<summary>6. How do you control log volume at scale without losing important data?</summary>

Layer multiple controls: (1) At the source: set log levels appropriately (INFO in production, DEBUG only for active debugging). (2) In the OTel Collector: filter out known noise (health check logs, metrics endpoint access logs, kube-system routine logs). (3) Sampling: for very verbose services, use probabilistic sampling to keep 10-20% of DEBUG/TRACE logs while keeping 100% of WARN/ERROR. (4) Truncation: limit individual log line length (4KB is typical) and drop oversized payloads like full request/response bodies. (5) Retention policies: keep recent logs at full fidelity (7 days), then age out to cheaper storage (30 days), then delete. (6) Per-namespace quotas: set ingestion rate limits in Loki to prevent one team's chatty service from consuming the entire logging budget.
</details>

---

## Hands-On Exercise: Build a Multi-Cluster Monitoring Stack

In this exercise, you will deploy a monitoring stack with Prometheus, Thanos Sidecar, and Grafana in a local cluster.

### Prerequisites

- kind cluster
- Helm installed
- kubectl installed

### Task 1: Deploy Prometheus with Thanos Sidecar

<details>
<summary>Solution</summary>

```bash
# Create cluster
kind create cluster --name obs-lab

# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
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

### Task 2: Deploy Sample Workloads with Metrics

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

### Task 3: Query Cross-Cluster Metrics

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

### Task 4: Create a Cardinality Report

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

### Task 5: Set Up Grafana Dashboard

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

```bash
kind delete cluster --name obs-lab
```

### Success Criteria

- [ ] Prometheus deployed with external labels (cluster, region)
- [ ] Sample workloads scraped by Prometheus
- [ ] PromQL queries return results with cluster labels
- [ ] Cardinality report identifies top metrics by series count
- [ ] Grafana accessible with Prometheus data source configured

---

## Next Module

[Module 8.10: Scaling IaC & State Management](../module-8.10-iac-scale/) -- Your clusters are observable, your costs are optimized, and your architecture spans multiple regions. Now learn how to manage the infrastructure code that holds it all together. Large Terraform state, module design, GitOps integration, and drift detection at enterprise scale.

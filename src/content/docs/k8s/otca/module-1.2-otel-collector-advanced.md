---
title: "Module 1.2: OTel Collector Advanced"
slug: k8s/otca/module-1.2-otel-collector-advanced/
sidebar:
  order: 3
---
> **Complexity**: `[COMPLEX]` - Multiple interacting components, pipeline logic
>
> **Time to Complete**: 60-75 minutes
>
> **Prerequisites**: Module 1 (OpenTelemetry Fundamentals), basic Kubernetes knowledge
>
> **OTCA Domain**: Domain 3 - OTel Collector (26% of exam)

---

## Why This Module Matters

The OpenTelemetry Collector is the **backbone of every production observability pipeline**. It receives, processes, and exports telemetry data — traces, metrics, and logs — and it does so at scale, reliably, and vendor-neutrally. Domain 3 accounts for 26% of your OTCA exam. You cannot pass without mastering the Collector.

If OpenTelemetry is the universal language of observability, the Collector is the postal service. It picks up signals from your applications, routes them through processing, and delivers them wherever they need to go. Misconfigure it and you get data loss, memory explosions, or a pipeline that silently drops the traces you need most.

> **War Story: The Silent Pipeline**
>
> A platform team deployed the OTel Collector to replace their vendor-specific agents. Everything looked green — health checks passed, pods were running. But after two weeks, the on-call engineer noticed zero traces for their payment service. The culprit? A `filter` processor with a regex that accidentally matched the `payment-` service prefix. The Collector was healthy. The pipeline was working. It was just filtering out exactly the data they needed most. Lesson: always validate your pipeline end-to-end with the `debug` exporter before going to production. Trust, but verify.

---

## Did You Know?

- The OTel Collector can process **over 1 million spans per second** on a single instance with proper tuning. Most teams hit config issues long before they hit performance limits.
- The `spanmetrics` connector can **generate RED metrics (Rate, Errors, Duration) automatically from traces** — meaning you get metrics for free without instrumenting anything twice.
- The Collector's `transform` processor uses **OTTL (OpenTelemetry Transformation Language)**, a purpose-built language that lets you modify, filter, and route telemetry using SQL-like expressions.
- There are **three official distributions** of the Collector: Core (minimal), Contrib (batteries-included), and Custom (build your own with `ocb`). The exam expects you to know when to use each.

---

## Part 1: Collector Architecture and Config Structure

### 1.1 The config.yaml Anatomy

Every Collector configuration has **five top-level sections**. Think of it as assembling a factory: you define what comes in (receivers), how it gets processed (processors), where it goes out (exporters), and then you wire them together (service/pipelines).

```yaml
# The five building blocks of every Collector config
receivers:    # How data gets IN to the Collector
processors:   # How data gets TRANSFORMED inside the Collector
exporters:    # How data gets OUT of the Collector
connectors:   # Bridge between pipelines (output of one, input of another)
extensions:   # Auxiliary services (health checks, auth, debugging)

service:      # Wires everything together into pipelines
  extensions: [health_check, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/backend]
    metrics:
      receivers: [otlp, prometheus]
      processors: [batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp, filelog]
      processors: [batch]
      exporters: [otlp/backend]
```

**Key rules for the service section:**
- A component declared in `receivers`/`processors`/`exporters` does **nothing** until it appears in a pipeline under `service`.
- Processors execute **in the order listed** — order matters.
- A single receiver/exporter can appear in **multiple pipelines**.
- Pipeline names under `traces`, `metrics`, and `logs` are the three signal types.

### 1.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      OTel Collector                             │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │Receivers │──▶│Processors│──▶│Exporters │──▶│ Backends │   │
│  │          │   │          │   │          │   │          │   │
│  │ otlp     │   │ batch    │   │ otlp     │   │ Jaeger   │   │
│  │ prometheus│   │ filter   │   │ prometheus│   │ Prometheus│   │
│  │ filelog   │   │ transform│   │ debug    │   │ Loki     │   │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Extensions: health_check, zpages, pprof, bearertokenauth  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Receivers — Getting Data In

Receivers listen for or pull telemetry data. They are the **entry point** of every pipeline.

### 2.1 OTLP Receiver (The Universal Input)

The `otlp` receiver is the **most important receiver** on the exam. It accepts data over both gRPC (port 4317) and HTTP (port 4318).

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
        max_recv_msg_size_mib: 4       # Default: 4 MiB
      http:
        endpoint: 0.0.0.0:4318
        cors:
          allowed_origins: ["*"]       # For browser-based apps
```

**gRPC vs HTTP — when to use each:**

| Aspect | gRPC (:4317) | HTTP (:4318) |
|--------|-------------|-------------|
| Performance | Higher throughput, streaming | Slightly lower |
| Compression | Built-in (gzip, zstd) | Requires config |
| Firewall-friendly | No (HTTP/2, specific ports) | Yes (standard HTTP) |
| Browser support | No (needs proxy) | Yes (for web apps) |
| Best for | Service-to-collector, collector-to-collector | Browser RUM, edge ingestion |

**Exam tip**: Default OTLP ports — **4317 for gRPC, 4318 for HTTP**. These are tested frequently.

### 2.2 Prometheus Receiver

Scrapes Prometheus-format metrics endpoints. Useful when you want the Collector to replace or augment a Prometheus server.

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'k8s-pods'
          scrape_interval: 15s
          kubernetes_sd_configs:
            - role: pod
```

### 2.3 Filelog Receiver

Reads logs from files on disk — essential for collecting container logs from nodes.

```yaml
receivers:
  filelog:
    include: [/var/log/pods/*/*/*.log]
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.time
          layout: '%Y-%m-%dT%H:%M:%S.%LZ'
```

### 2.4 Host Metrics Receiver

Collects system-level metrics (CPU, memory, disk, network) from the host.

```yaml
receivers:
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu: {}
      memory: {}
      disk: {}
      filesystem: {}
      network: {}
      load: {}
```

### 2.5 Kubernetes Cluster Receiver

Collects cluster-level metrics from the Kubernetes API server — node count, pod phases, resource quotas.

```yaml
receivers:
  k8s_cluster:
    collection_interval: 30s
    node_conditions_to_report: [Ready, MemoryPressure]
    allocatable_types_to_report: [cpu, memory]
```

> This receiver needs RBAC access to the Kubernetes API. It typically runs in **gateway mode** (one instance), not on every node.

---

## Part 3: Processors — Transforming Data In-Flight

Processors modify telemetry between receivers and exporters. **Order matters** — they execute sequentially as listed in the pipeline.

### 3.1 Batch Processor

Groups data into batches before sending. This is **almost always the first processor you should add** — it dramatically reduces export overhead.

```yaml
processors:
  batch:
    send_batch_size: 8192         # Number of items per batch
    send_batch_max_size: 10000    # Hard upper limit
    timeout: 200ms                # Flush interval even if batch isn't full
```

### 3.2 Memory Limiter Processor

Prevents the Collector from running out of memory. **Should be the first processor in every pipeline.**

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512                # Hard limit
    spike_limit_mib: 128          # Buffer for spikes
```

When memory exceeds `limit_mib - spike_limit_mib` (384 MiB in this example), the processor starts refusing data. When it exceeds `limit_mib`, it force-drops data. This prevents OOM kills.

### 3.3 Filter Processor

Drops telemetry that matches (or doesn't match) conditions. Use it to reduce costs by discarding noisy, low-value data.

```yaml
processors:
  filter:
    error_mode: ignore
    traces:
      span:
        - 'attributes["http.route"] == "/healthz"'     # Drop health checks
        - 'attributes["http.route"] == "/readyz"'
    metrics:
      metric:
        - 'name == "http.server.duration" and resource.attributes["service.name"] == "debug-svc"'
```

### 3.4 Attributes Processor

Add, update, delete, or hash attributes on spans, metrics, or logs.

```yaml
processors:
  attributes:
    actions:
      - key: environment
        value: production
        action: upsert             # Insert or update
      - key: db.password
        action: delete             # Remove sensitive data
      - key: user.email
        action: hash               # Hash PII
```

### 3.5 Transform Processor (OTTL)

The most powerful processor. Uses **OTTL (OpenTelemetry Transformation Language)** for arbitrary transformations.

```yaml
processors:
  transform:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - set(attributes["deployment.env"], "prod") where resource.attributes["k8s.namespace.name"] == "production"
          - truncate_all(attributes, 256)           # Limit attribute value length
          - replace_pattern(attributes["http.url"], "token=([^&]*)", "token=***")
    metric_statements:
      - context: datapoint
        statements:
          - convert_sum_to_gauge() where metric.name == "system.cpu.time"
    log_statements:
      - context: log
        statements:
          - merge_maps(attributes, ParseJSON(body), "insert") where IsMatch(body, "^\\{")
```

OTTL is a **high-priority exam topic**. Know these key functions: `set`, `delete`, `truncate_all`, `replace_pattern`, `merge_maps`, `ParseJSON`, `IsMatch`.

### 3.6 Tail Sampling Processor

Makes sampling decisions **after seeing complete traces**. Runs only in gateway mode (needs full traces).

```yaml
processors:
  tail_sampling:
    decision_wait: 10s              # Wait for trace to complete
    num_traces: 100000              # Traces held in memory
    policies:
      - name: errors-always
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 1000}
      - name: low-volume-sample
        type: probabilistic
        probabilistic: {sampling_percentage: 10}
```

This keeps 100% of errors, 100% of slow traces, and 10% of everything else. The `decision_wait` must be long enough for all spans in a trace to arrive.

---

## Part 4: Exporters — Sending Data Out

Exporters send processed telemetry to backends.

### 4.1 OTLP Exporter (gRPC)

The default for Collector-to-Collector or Collector-to-backend communication.

```yaml
exporters:
  otlp:
    endpoint: tempo.observability.svc.cluster.local:4317
    tls:
      insecure: false
      cert_file: /certs/client.crt
      key_file: /certs/client.key
    compression: gzip              # or zstd
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s
      max_elapsed_time: 300s
```

### 4.2 OTLP HTTP Exporter

Same protocol, HTTP transport. Use when gRPC is blocked by firewalls or proxies.

```yaml
exporters:
  otlphttp:
    endpoint: https://ingest.example.com
    compression: gzip
    headers:
      Authorization: "Bearer ${env:API_TOKEN}"
```

### 4.3 Prometheus Exporter

Exposes a `/metrics` endpoint that Prometheus can scrape. Converts OTLP metrics to Prometheus format.

```yaml
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: otel
    resource_to_telemetry_conversion:
      enabled: true                 # Promote resource attributes to labels
```

### 4.4 Debug Exporter

Prints telemetry to stdout. **Essential for development and troubleshooting.**

```yaml
exporters:
  debug:
    verbosity: detailed            # basic | normal | detailed
    sampling_initial: 5            # First N items logged
    sampling_thereafter: 200       # Then every Nth item
```

### 4.5 File Exporter

Writes telemetry to files in JSON format. Useful for audit trails or offline analysis.

```yaml
exporters:
  file:
    path: /data/otel-output.json
    rotation:
      max_megabytes: 100
      max_days: 7
      max_backups: 5
```

---

## Part 5: Connectors — Bridging Pipelines

Connectors are both an **exporter for one pipeline** and a **receiver for another**. They transform one signal type into another.

### 5.1 Span Metrics Connector

Generates **RED metrics from traces** automatically — no additional instrumentation needed.

```yaml
connectors:
  spanmetrics:
    histogram:
      explicit:
        buckets: [5ms, 10ms, 25ms, 50ms, 100ms, 500ms, 1s, 5s]
    dimensions:
      - name: http.method
      - name: http.status_code
    namespace: traces.spanmetrics

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo, spanmetrics]     # spanmetrics is an exporter here
    metrics:
      receivers: [otlp, spanmetrics]            # spanmetrics is a receiver here
      processors: [batch]
      exporters: [prometheus]
```

This is one of the most elegant features in OTel. Traces flow into the `spanmetrics` connector, and metrics flow out — giving you `traces.spanmetrics.calls_total`, `traces.spanmetrics.duration_*`, and error counts.

### 5.2 Count Connector

Counts spans, metrics, or log records and emits the counts as metrics.

```yaml
connectors:
  count:
    traces:
      spans:
        - name: span.count
          description: "Count of spans"
    logs:
      log_records:
        - name: log.record.count
          description: "Count of log records"
```

---

## Part 6: Extensions

Extensions provide auxiliary capabilities that are **not part of the data pipeline** but support it.

```yaml
extensions:
  health_check:
    endpoint: 0.0.0.0:13133       # Liveness/readiness probe target

  zpages:
    endpoint: 0.0.0.0:55679       # Internal debug UI at /debug/tracez, /debug/pipelinez

  pprof:
    endpoint: 0.0.0.0:1777        # Go pprof profiling

  bearertokenauth:
    token: "${env:OTEL_AUTH_TOKEN}"

service:
  extensions: [health_check, zpages, pprof, bearertokenauth]
```

| Extension | Purpose | Default Port |
|-----------|---------|-------------|
| `health_check` | K8s liveness/readiness probes | 13133 |
| `zpages` | Debug UI: pipeline status, trace samples | 55679 |
| `pprof` | Performance profiling | 1777 |
| `bearertokenauth` | Authenticate incoming/outgoing requests | N/A |

**Exam tip**: `zpages` at `/debug/pipelinez` shows if pipelines are running. `/debug/tracez` shows sample traces passing through the Collector. This is your first stop when debugging.

---

## Part 7: Deployment Patterns

### 7.1 Agent vs Gateway

```
Agent Mode (DaemonSet)                Gateway Mode (Deployment)
──────────────────────                ─────────────────────────

┌─────────────────────┐              ┌─────────────────────┐
│      Node 1         │              │      Node 1         │
│ ┌─────┐ ┌────────┐ │              │ ┌─────┐             │
│ │App A│─▶│Collector│─┤              │ │App A│──┐          │
│ └─────┘ │(Agent) │ │              │ └─────┘  │          │
│ ┌─────┐ │        │ │              │ ┌─────┐  │          │
│ │App B│─▶│        │ │              │ │App B│──┤          │
│ └─────┘ └───┬────┘ │              │ └─────┘  │          │
└─────────────┼──────┘              └──────────┼──────────┘
              │                                │
              ▼                                │
┌─────────────────────┐                        │
│      Node 2         │              ┌─────────▼──────────┐
│ ┌─────┐ ┌────────┐ │              │  Gateway Collector  │
│ │App C│─▶│Collector│─┤───▶Backend  │  (Deployment, 2+   │
│ └─────┘ │(Agent) │ │              │   replicas)         │──▶Backend
│         └───┬────┘ │              │                     │
└─────────────┼──────┘              └─────────▲──────────┘
              │                                │
              ▼                     ┌──────────┼──────────┐
         Backend                    │      Node 2         │
                                    │ ┌─────┐  │          │
                                    │ │App C│──┘          │
                                    │ └─────┘             │
                                    └─────────────────────┘
```

| Aspect | Agent (DaemonSet) | Gateway (Deployment) |
|--------|-------------------|---------------------|
| Deployment | One per node | Shared pool (2+ replicas) |
| Resource use | Light per node | Heavier but centralized |
| Tail sampling | Not possible (incomplete traces) | Yes (full traces arrive) |
| Host metrics | Yes (local access) | No |
| Filelog | Yes (local files) | No |
| Scaling | Scales with nodes | HPA on CPU/memory |
| Best for | Collection, basic processing | Aggregation, sampling, routing |

**Production pattern**: Use **both**. Agents on every node collect and forward. A gateway pool handles sampling, enrichment, and export.

```
Apps ──▶ Agent (DaemonSet) ──▶ Gateway (Deployment) ──▶ Backends
         - hostmetrics            - tail_sampling
         - filelog                - spanmetrics
         - memory_limiter         - routing
         - batch                  - export to N backends
```

### 7.2 Scaling the Gateway

For horizontal scaling, use the **load balancing exporter** on agents to distribute traces across gateway replicas. This is critical for tail sampling — all spans of a trace must reach the **same gateway** instance.

```yaml
# On the Agent
exporters:
  loadbalancing:
    protocol:
      otlp:
        tls:
          insecure: true
    resolver:
      dns:
        hostname: otel-gateway-headless.observability.svc.cluster.local
        port: 4317
```

The `loadbalancing` exporter uses **trace ID-based routing** — all spans with the same trace ID go to the same gateway. This is what makes tail sampling possible in a scaled deployment.

---

## Part 8: OTLP Protocol Deep-Dive

OTLP (OpenTelemetry Protocol) is the **native wire protocol** of OpenTelemetry.

### 8.1 Protocol Comparison

| Feature | OTLP/gRPC | OTLP/HTTP |
|---------|-----------|-----------|
| Transport | HTTP/2 with Protocol Buffers | HTTP/1.1 with Protobuf or JSON |
| Port | 4317 | 4318 |
| Compression | gzip, zstd (built-in) | gzip (via Content-Encoding) |
| Streaming | Yes (bidirectional) | No (request/response) |
| Path (traces) | N/A (gRPC service) | `/v1/traces` |
| Path (metrics) | N/A | `/v1/metrics` |
| Path (logs) | N/A | `/v1/logs` |
| Proxy support | Needs HTTP/2-aware proxy | Works with any HTTP proxy |

**When to choose gRPC**: Internal service-to-collector and collector-to-collector traffic where performance matters and you control the network.

**When to choose HTTP**: Browser telemetry (RUM), crossing firewalls/load balancers that don't support HTTP/2, or when you need JSON-encoded payloads for debugging.

### 8.2 Compression

Always enable compression in production. The difference is significant:

```yaml
exporters:
  otlp:
    endpoint: gateway:4317
    compression: zstd        # Best ratio for telemetry data
  otlphttp:
    endpoint: https://ingest.example.com
    compression: gzip        # More widely supported
```

`zstd` offers better compression ratios and speed than `gzip` but is less universally supported. For internal traffic, prefer `zstd`. For external endpoints, use `gzip`.

---

## Part 9: OTel Operator for Kubernetes

The **OpenTelemetry Operator** extends Kubernetes to manage Collectors and auto-instrument applications.

### 9.1 Installing the Operator

```bash
# Install cert-manager first (required dependency)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.5/cert-manager.yaml

# Install the OTel Operator
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
```

### 9.2 OpenTelemetryCollector CRD

The Operator manages Collector instances via a custom resource:

```yaml
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata:
  name: otel-agent
  namespace: observability
spec:
  mode: daemonset                    # daemonset | deployment | statefulset | sidecar
  image: otel/opentelemetry-collector-contrib:0.98.0
  config:
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    processors:
      memory_limiter:
        check_interval: 1s
        limit_mib: 512
      batch: {}
    exporters:
      otlp:
        endpoint: otel-gateway.observability.svc.cluster.local:4317
        tls:
          insecure: true
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [otlp]
```

### 9.3 Auto-Instrumentation with the Instrumentation CRD

The Operator can **inject instrumentation into pods automatically** — no code changes required.

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: auto-instrumentation
  namespace: observability
spec:
  exporter:
    endpoint: http://otel-agent-collector.observability.svc.cluster.local:4318
  propagators:
    - tracecontext
    - baggage
  sampler:
    type: parentbased_traceidratio
    argument: "0.25"
  java:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-java:latest
  python:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-python:latest
  nodejs:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-nodejs:latest
```

Then annotate pods to opt in:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-java-app
spec:
  template:
    metadata:
      annotations:
        instrumentation.opentelemetry.io/inject-java: "true"     # Java auto-instrument
        # Other options:
        # instrumentation.opentelemetry.io/inject-python: "true"
        # instrumentation.opentelemetry.io/inject-nodejs: "true"
        # instrumentation.opentelemetry.io/inject-dotnet: "true"
    spec:
      containers:
        - name: app
          image: my-java-app:latest
```

The Operator injects an init container with the instrumentation agent. The application starts with zero code changes and produces traces automatically.

---

## Part 10: Collector Distributions

### 10.1 Core vs Contrib vs Custom

| Distribution | Components | Use Case |
|-------------|-----------|----------|
| **Core** (`otel/opentelemetry-collector`) | ~20 components (otlp, batch, debug, etc.) | Minimal footprint, security-sensitive environments |
| **Contrib** (`otel/opentelemetry-collector-contrib`) | 200+ components (all community receivers, processors, exporters) | Development, when you need specific integrations |
| **Custom** (built with `ocb`) | Exactly what you choose | Production — include only what you use |

### 10.2 Building a Custom Collector

The **OpenTelemetry Collector Builder** (`ocb`) creates purpose-built distributions:

```yaml
# builder-config.yaml
dist:
  name: my-collector
  description: "Production collector"
  output_path: ./dist
  otelcol_version: "0.98.0"

receivers:
  - gomod: go.opentelemetry.io/collector/receiver/otlpreceiver v0.98.0
  - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/receiver/filelogreceiver v0.98.0

processors:
  - gomod: go.opentelemetry.io/collector/processor/batchprocessor v0.98.0
  - gomod: go.opentelemetry.io/collector/processor/memorylimiterprocessor v0.98.0

exporters:
  - gomod: go.opentelemetry.io/collector/exporter/otlpexporter v0.98.0
  - gomod: go.opentelemetry.io/collector/exporter/debugexporter v0.98.0
```

```bash
# Build it
ocb --config builder-config.yaml
```

**Why custom?** Smaller binary (50MB vs 200MB+), smaller attack surface, faster startup, only the dependencies you actually audit.

---

## Part 11: Debug Pipeline

When things go wrong (and they will), here is your debugging toolkit.

### 11.1 Debug Exporter

Add it to any pipeline to see what data is flowing:

```yaml
exporters:
  debug:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/backend, debug]    # Add debug alongside real exporter
```

### 11.2 Internal Telemetry

The Collector can report its **own** metrics:

```yaml
service:
  telemetry:
    logs:
      level: debug                  # debug | info | warn | error
      encoding: json                # For structured log parsing
    metrics:
      level: detailed               # none | basic | normal | detailed
      address: 0.0.0.0:8888        # Collector's own /metrics endpoint
```

Key internal metrics to watch:
- `otelcol_receiver_accepted_spans` — Are spans arriving?
- `otelcol_processor_dropped_spans` — Is the filter/sampling dropping too much?
- `otelcol_exporter_sent_spans` — Are spans leaving?
- `otelcol_exporter_send_failed_spans` — Is the backend rejecting data?

### 11.3 zpages for Live Debugging

With the `zpages` extension enabled at port 55679:

| Endpoint | What It Shows |
|----------|---------------|
| `/debug/pipelinez` | Active pipelines and their components |
| `/debug/tracez` | Sample traces flowing through the Collector |
| `/debug/rpcz` | gRPC call statistics |
| `/debug/extensionz` | Running extensions |

```bash
# Port-forward to access zpages
kubectl port-forward svc/otel-collector 55679:55679
# Then open http://localhost:55679/debug/pipelinez
```

---

## Complete Multi-Pipeline Configuration Example

This is a production-grade config with traces, metrics, and logs flowing through separate pipelines, with `spanmetrics` bridging traces to metrics:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  prometheus:
    config:
      scrape_configs:
        - job_name: 'k8s-pods'
          scrape_interval: 15s
          kubernetes_sd_configs:
            - role: pod
  filelog:
    include: [/var/log/pods/*/*/*.log]
    operators:
      - type: json_parser
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu: {}
      memory: {}
      disk: {}

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 1024
    spike_limit_mib: 256
  batch:
    send_batch_size: 8192
    timeout: 200ms
  filter/healthz:
    error_mode: ignore
    traces:
      span:
        - 'attributes["http.route"] == "/healthz"'
        - 'attributes["http.route"] == "/readyz"'
  transform/redact:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - replace_pattern(attributes["http.url"], "token=([^&]*)", "token=REDACTED")
    log_statements:
      - context: log
        statements:
          - replace_pattern(body, "password=\\S+", "password=***")

exporters:
  otlp/tempo:
    endpoint: tempo.observability.svc.cluster.local:4317
    tls:
      insecure: true
  otlp/loki:
    endpoint: loki.observability.svc.cluster.local:3100
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889
  debug:
    verbosity: basic

connectors:
  spanmetrics:
    histogram:
      explicit:
        buckets: [5ms, 10ms, 25ms, 50ms, 100ms, 500ms, 1s, 5s]
    dimensions:
      - name: http.method
      - name: http.status_code

extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  zpages:
    endpoint: 0.0.0.0:55679

service:
  extensions: [health_check, zpages]
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, filter/healthz, transform/redact, batch]
      exporters: [otlp/tempo, spanmetrics, debug]
    metrics:
      receivers: [otlp, prometheus, hostmetrics, spanmetrics]
      processors: [memory_limiter, batch]
      exporters: [prometheus, debug]
    logs:
      receivers: [otlp, filelog]
      processors: [memory_limiter, transform/redact, batch]
      exporters: [otlp/loki, debug]
```

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| Declaring a component but not adding it to a pipeline | Component is silently ignored | Always check the `service.pipelines` section |
| Wrong processor order (batch before memory_limiter) | OOM kills under load | `memory_limiter` first, `batch` last |
| Tail sampling on agents (DaemonSet) | Incomplete traces, bad sampling decisions | Tail sampling only in gateway mode |
| Using Contrib image in production | 200MB+ image, unused attack surface | Build custom distribution with `ocb` |
| Forgetting `error_mode: ignore` on filter/transform | One bad record crashes the pipeline | Always set `error_mode: ignore` in production |
| OTLP exporter with `tls.insecure: false` but no certs | Connection refused, export failures | Set `insecure: true` for internal traffic or provide valid certs |
| Not enabling compression on exporters | 3-5x more bandwidth usage | Always set `compression: gzip` or `zstd` |
| Running k8s_cluster receiver on every agent | Duplicate metrics, API server overload | Run k8s_cluster on a single gateway or Deployment |

---

## Quiz

Test your understanding of Domain 3 content.

**Q1: What are the default OTLP ports for gRPC and HTTP?**

<details>
<summary>Answer</summary>

gRPC: **4317**, HTTP: **4318**. These are standard across all OTel components.
</details>

**Q2: In what order should `memory_limiter` and `batch` appear in a pipeline's processor list?**

<details>
<summary>Answer</summary>

`memory_limiter` should be **first**, `batch` should be **last**. The memory limiter needs to reject data before it accumulates in the batch buffer. The batch processor should be the final step before export to maximize batch efficiency.
</details>

**Q3: Why can't you run tail sampling on a DaemonSet (agent mode) Collector?**

<details>
<summary>Answer</summary>

Tail sampling needs to see the **complete trace** before making a sampling decision. In agent mode, spans from different services land on different nodes, so no single agent sees all spans of a distributed trace. Tail sampling must run in **gateway mode** where all spans are forwarded to a central pool, and the `loadbalancing` exporter ensures all spans with the same trace ID reach the same gateway instance.
</details>

**Q4: What is the purpose of a connector like `spanmetrics`?**

<details>
<summary>Answer</summary>

A connector acts as both an **exporter** in one pipeline and a **receiver** in another. The `spanmetrics` connector receives traces from the traces pipeline and emits RED metrics (Rate, Errors, Duration) into the metrics pipeline. This lets you generate metrics from traces automatically without double-instrumentation.
</details>

**Q5: What is the difference between Core, Contrib, and Custom Collector distributions?**

<details>
<summary>Answer</summary>

- **Core**: Minimal set of ~20 components maintained by the OTel project. Small binary, limited functionality.
- **Contrib**: Community-maintained, 200+ components. Large binary, everything included.
- **Custom**: Built with `ocb` (OpenTelemetry Collector Builder) to include only the specific components you need. Best for production — minimal attack surface, optimized size.
</details>

**Q6: How does the `loadbalancing` exporter route data?**

<details>
<summary>Answer</summary>

It routes based on **trace ID** using consistent hashing. All spans belonging to the same trace are sent to the same backend (gateway) instance. This is essential for tail sampling to work correctly in a horizontally scaled gateway deployment. It uses a DNS resolver to discover backend instances via a headless Kubernetes Service.
</details>

**Q7: What annotation would you add to a Java Deployment to enable auto-instrumentation via the OTel Operator?**

<details>
<summary>Answer</summary>

```yaml
instrumentation.opentelemetry.io/inject-java: "true"
```

This tells the OTel Operator's webhook to inject an init container with the Java auto-instrumentation agent. The `Instrumentation` CRD must exist in the same namespace (or the annotation must reference a specific one).
</details>

**Q8: You added a `filter` processor but telemetry is not being filtered. What is the most likely cause?**

<details>
<summary>Answer</summary>

The filter processor is defined in the `processors` section but **not included in the pipeline** under `service.pipelines`. A component must appear in both its definition section and in a pipeline to be active. Check `service.pipelines.<signal>.processors` to confirm it is listed.
</details>

**Q9: What zpages endpoint shows the status of active pipelines?**

<details>
<summary>Answer</summary>

`/debug/pipelinez` — It shows all configured pipelines and their component status (receivers, processors, exporters). Access it by port-forwarding to port **55679** on the Collector.
</details>

**Q10: When should you use OTLP/HTTP instead of OTLP/gRPC?**

<details>
<summary>Answer</summary>

Use OTLP/HTTP when:
- Sending telemetry from **browsers** (gRPC doesn't work in browsers)
- Crossing **firewalls or proxies** that don't support HTTP/2
- You need **JSON encoding** for debugging
- Working with load balancers that only support HTTP/1.1

Use gRPC for internal collector-to-collector and service-to-collector traffic where performance matters.
</details>

---

## Hands-On Exercise: Build a Multi-Signal Pipeline

**Objective**: Deploy an OTel Collector that receives all three signals, generates spanmetrics, and outputs to debug.

### Setup

```bash
# Create a kind cluster (skip if you already have one)
kind create cluster --name otel-lab

# Create namespace
kubectl create namespace observability
```

### Step 1: Deploy the Collector

```bash
kubectl apply -n observability -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

    processors:
      memory_limiter:
        check_interval: 1s
        limit_mib: 256
        spike_limit_mib: 64
      batch:
        send_batch_size: 1024
        timeout: 1s

    connectors:
      spanmetrics:
        dimensions:
          - name: http.method

    exporters:
      debug:
        verbosity: detailed

    extensions:
      health_check:
        endpoint: 0.0.0.0:13133
      zpages:
        endpoint: 0.0.0.0:55679

    service:
      extensions: [health_check, zpages]
      telemetry:
        metrics:
          address: 0.0.0.0:8888
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [debug, spanmetrics]
        metrics:
          receivers: [otlp, spanmetrics]
          processors: [memory_limiter, batch]
          exporters: [debug]
        logs:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [debug]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib:0.98.0
          args: ["--config=/etc/otel/config.yaml"]
          ports:
            - containerPort: 4317
            - containerPort: 4318
            - containerPort: 13133
            - containerPort: 55679
          volumeMounts:
            - name: config
              mountPath: /etc/otel
          livenessProbe:
            httpGet:
              path: /
              port: 13133
          readinessProbe:
            httpGet:
              path: /
              port: 13133
      volumes:
        - name: config
          configMap:
            name: otel-collector-config
---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
spec:
  selector:
    app: otel-collector
  ports:
    - name: otlp-grpc
      port: 4317
    - name: otlp-http
      port: 4318
    - name: health
      port: 13133
    - name: zpages
      port: 55679
EOF
```

### Step 2: Send Test Telemetry

```bash
# Wait for the collector to be ready
kubectl wait --for=condition=ready pod -l app=otel-collector -n observability --timeout=60s

# Port-forward to send data
kubectl port-forward -n observability svc/otel-collector 4318:4318 &

# Send a test trace via OTLP/HTTP
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test-service"}}]},
      "scopeSpans": [{
        "spans": [{
          "traceId": "5b8aa5a2d2c872e8321cf37308d69df2",
          "spanId": "051581bf3cb55c13",
          "name": "GET /api/users",
          "kind": 2,
          "startTimeUnixNano": "1000000000",
          "endTimeUnixNano": "2000000000",
          "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
            {"key": "http.status_code", "value": {"intValue": "200"}}
          ]
        }]
      }]
    }]
  }'
```

### Step 3: Verify

```bash
# Check collector logs — you should see the trace in debug output
kubectl logs -n observability -l app=otel-collector --tail=50

# Check zpages
kubectl port-forward -n observability svc/otel-collector 55679:55679 &
# Open http://localhost:55679/debug/pipelinez in your browser

# Check Collector's own metrics
kubectl port-forward -n observability svc/otel-collector 8888:8888 &
curl -s http://localhost:8888/metrics | grep otelcol_receiver_accepted
```

### Success Criteria

You should see:
- The debug exporter printing the trace span with service name `test-service`
- The `spanmetrics` connector generating metrics (visible in the debug output for the metrics pipeline)
- `otelcol_receiver_accepted_spans` > 0 in the Collector's own metrics
- zpages showing all three pipelines active at `/debug/pipelinez`

---

## Key Takeaways for the Exam

1. **Config structure**: Five sections (receivers, processors, exporters, connectors, extensions) + service to wire them.
2. **OTLP ports**: gRPC = 4317, HTTP = 4318. Know these cold.
3. **Processor order**: `memory_limiter` first, `batch` last.
4. **Agent vs Gateway**: Agents (DaemonSet) collect, Gateways (Deployment) aggregate and sample.
5. **Tail sampling**: Gateway-only. Requires `loadbalancing` exporter for horizontal scaling.
6. **Connectors**: Bridge pipelines. `spanmetrics` generates RED metrics from traces.
7. **Auto-instrumentation**: OTel Operator + `Instrumentation` CRD + pod annotation.
8. **Distributions**: Core (minimal), Contrib (everything), Custom via `ocb` (production).
9. **Debug toolkit**: `debug` exporter, zpages (`/debug/pipelinez`), internal telemetry metrics on `:8888`.
10. **OTTL**: The transform processor's language — `set`, `delete`, `replace_pattern`, `merge_maps`.

---

> **Next Module**: [OTCA Track Overview]() — Instrument applications using OTel SDKs across multiple languages.

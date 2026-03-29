---
title: "Module 1.5: Distributed Tracing"
slug: platform/toolkits/observability-intelligence/observability/module-1.5-tracing
sidebar:
  order: 6
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

---

*The VP of Engineering stared at the Slack channel in disbelief. "Customer checkout is failing. Intermittently. For the past 3 hours." The e-commerce platform processed $47 million daily during the holiday season, with each minute of checkout failures costing roughly $32,000 in abandoned carts. Metrics showed elevated error rates, but which of the 67 microservices was failing? Logs flooded in from everywhere—millions of lines—but without correlation, they were useless. The war room had 15 engineers from 8 teams, each defending their service. "It's not us," became the mantra. Three hours became six. Lost revenue: $5.8 million. The root cause, discovered only after implementing distributed tracing: a single misconfigured timeout in a third-party payment validation service, buried five hops deep in the request flow. One service. Five layers down. Invisible without tracing.*

---

## Prerequisites

Before starting this module:
- [Module 1.2: OpenTelemetry](../module-1.2-opentelemetry/) — Instrumentation fundamentals
- [Module 1.1: Prometheus](../module-1.1-prometheus/) — Understanding metrics
- [Module 1.4: Loki](../module-1.4-loki/) — Log correlation (recommended)
- Familiarity with microservices architecture

## Why This Module Matters

In a monolith, debugging is straightforward: stack traces tell you what happened. In microservices, a single user request might touch 20 services across 5 teams. When something fails, you need to see the entire journey.

Distributed tracing solves this. It connects the dots across services, showing exactly where latency hides and where errors originate. Without tracing, debugging distributed systems is guesswork.

## Did You Know?

- **Google's Dapper paper (2010) started it all**—it described how Google traces every request across their massive infrastructure, inspiring Jaeger, Zipkin, and eventually OpenTelemetry
- **A single trace can have thousands of spans**—complex e-commerce transactions might generate 500+ spans across dozens of services
- **Traces are sampled, not exhaustive**—storing every trace would be prohibitively expensive; most systems sample 1-10% of traffic
- **The W3C Trace Context standard ensures interoperability**—headers like `traceparent` work across languages, frameworks, and vendors

## Tracing Concepts

### The Anatomy of a Trace

```
┌─────────────────────────────────────────────────────────────────┐
│                          TRACE                                   │
│  trace_id: abc123                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Time ──────────────────────────────────────────────────────▶   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ SPAN: api-gateway                                           ││
│  │ span_id: s1  parent: none  duration: 500ms                  ││
│  │ ┌───────────────────────────────────────────────────────┐   ││
│  │ │                                                       │   ││
│  │ │  ┌──────────────────────────────────────────────────┐ │   ││
│  │ │  │ SPAN: user-service                               │ │   ││
│  │ │  │ span_id: s2  parent: s1  duration: 150ms        │ │   ││
│  │ │  │ ┌──────────────────────────┐                    │ │   ││
│  │ │  │ │ SPAN: postgres          │                    │ │   ││
│  │ │  │ │ span_id: s3  parent: s2 │                    │ │   ││
│  │ │  │ │ duration: 50ms          │                    │ │   ││
│  │ │  │ └──────────────────────────┘                    │ │   ││
│  │ │  └──────────────────────────────────────────────────┘ │   ││
│  │ │                                                       │   ││
│  │ │  ┌──────────────────────────────────────────────────┐ │   ││
│  │ │  │ SPAN: order-service                              │ │   ││
│  │ │  │ span_id: s4  parent: s1  duration: 300ms        │ │   ││
│  │ │  │ ┌────────────────┐ ┌─────────────────────┐      │ │   ││
│  │ │  │ │ SPAN: redis   │ │ SPAN: payment-api   │      │ │   ││
│  │ │  │ │ s5 (20ms)     │ │ s6 (200ms)          │      │ │   ││
│  │ │  │ └────────────────┘ └─────────────────────┘      │ │   ││
│  │ │  └──────────────────────────────────────────────────┘ │   ││
│  │ │                                                       │   ││
│  │ └───────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Terminology

| Term | Definition |
|------|------------|
| **Trace** | The complete journey of a request through the system |
| **Span** | A single unit of work (e.g., HTTP call, DB query) |
| **Trace ID** | Unique identifier for the entire trace |
| **Span ID** | Unique identifier for a specific span |
| **Parent Span ID** | Links child span to parent |
| **Baggage** | Key-value pairs propagated across all spans |
| **Context Propagation** | Passing trace context between services |

### W3C Trace Context

```http
# Standard headers for trace propagation
traceparent: 00-abc123def456-789xyz-01
              │  │              │     │
              │  │              │     └── Flags (sampled)
              │  │              └── Parent span ID
              │  └── Trace ID
              └── Version

tracestate: vendor1=value1,vendor2=value2
            └── Vendor-specific data
```

## Tracing Backends

### Comparing Solutions

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRACING BACKENDS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  JAEGER                         TEMPO                            │
│  ┌─────────────────────┐       ┌─────────────────────┐          │
│  │ • CNCF graduated    │       │ • Grafana project   │          │
│  │ • Battle-tested     │       │ • Object storage    │          │
│  │ • Full-text search  │       │ • Cost-effective    │          │
│  │ • Cassandra/ES      │       │ • Log correlation   │          │
│  │ • Self-contained UI │       │ • Grafana native    │          │
│  └─────────────────────┘       └─────────────────────┘          │
│                                                                  │
│  ZIPKIN                         AWS X-RAY                        │
│  ┌─────────────────────┐       ┌─────────────────────┐          │
│  │ • Original OSS      │       │ • AWS native        │          │
│  │ • Simple setup      │       │ • Service maps      │          │
│  │ • Limited scale     │       │ • AWS integration   │          │
│  │ • MySQL/Cassandra   │       │ • Vendor lock-in    │          │
│  └─────────────────────┘       └─────────────────────┘          │
│                                                                  │
│  RECOMMENDATION:                                                 │
│  • Grafana stack → Tempo (seamless integration)                 │
│  • Need search → Jaeger (tag-based queries)                     │
│  • AWS-native → X-Ray (no extra infrastructure)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Jaeger

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    JAEGER ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Applications                                                    │
│  ┌──────┐ ┌──────┐ ┌──────┐                                     │
│  │ App1 │ │ App2 │ │ App3 │                                     │
│  └──┬───┘ └──┬───┘ └──┬───┘                                     │
│     │        │        │                                          │
│     └────────┼────────┘                                          │
│              │ OTLP / Jaeger protocol                            │
│              ▼                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    JAEGER COLLECTOR                       │   │
│  │  • Validates spans                                        │   │
│  │  • Processes and indexes                                  │   │
│  │  • Writes to storage                                      │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│              ┌────────────┼────────────┐                        │
│              ▼            ▼            ▼                        │
│  ┌────────────────┐ ┌──────────┐ ┌──────────┐                  │
│  │  Elasticsearch │ │ Cassandra│ │ Badger   │                  │
│  │  (production)  │ │ (scale)  │ │ (dev)    │                  │
│  └────────────────┘ └──────────┘ └──────────┘                  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    JAEGER QUERY                           │   │
│  │  • Serves UI                                              │   │
│  │  • REST/gRPC API                                          │   │
│  │  • Search by tags, service, operation                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Deploying Jaeger

```yaml
# jaeger-allinone.yaml (development)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: tracing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
        - name: jaeger
          image: jaegertracing/all-in-one:1.50
          ports:
            - containerPort: 16686  # UI
            - containerPort: 4317   # OTLP gRPC
            - containerPort: 4318   # OTLP HTTP
            - containerPort: 14268  # Jaeger HTTP
            - containerPort: 6831   # Jaeger UDP (compact)
          env:
            - name: COLLECTOR_OTLP_ENABLED
              value: "true"
          resources:
            limits:
              memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: tracing
spec:
  ports:
    - name: ui
      port: 16686
    - name: otlp-grpc
      port: 4317
    - name: otlp-http
      port: 4318
  selector:
    app: jaeger
```

### Jaeger with Elasticsearch (Production)

```yaml
# jaeger-production.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger-collector
  namespace: tracing
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jaeger-collector
  template:
    metadata:
      labels:
        app: jaeger-collector
    spec:
      containers:
        - name: collector
          image: jaegertracing/jaeger-collector:1.50
          ports:
            - containerPort: 4317
            - containerPort: 14268
          env:
            - name: SPAN_STORAGE_TYPE
              value: elasticsearch
            - name: ES_SERVER_URLS
              value: http://elasticsearch:9200
            - name: ES_INDEX_PREFIX
              value: jaeger
            - name: COLLECTOR_OTLP_ENABLED
              value: "true"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger-query
  namespace: tracing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jaeger-query
  template:
    metadata:
      labels:
        app: jaeger-query
    spec:
      containers:
        - name: query
          image: jaegertracing/jaeger-query:1.50
          ports:
            - containerPort: 16686
          env:
            - name: SPAN_STORAGE_TYPE
              value: elasticsearch
            - name: ES_SERVER_URLS
              value: http://elasticsearch:9200
```

### Jaeger Operator

```yaml
# Operator-based deployment
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: production
  namespace: tracing
spec:
  strategy: production  # vs allInOne

  collector:
    replicas: 3
    resources:
      limits:
        cpu: 1
        memory: 1Gi

  query:
    replicas: 2

  storage:
    type: elasticsearch
    elasticsearch:
      nodeCount: 3
      resources:
        limits:
          memory: 4Gi
      redundancyPolicy: SingleRedundancy

  ingress:
    enabled: true
```

## Grafana Tempo

### Why Tempo?

```
TEMPO'S KEY INSIGHT: Traces are append-only, search by ID is enough

Traditional (Jaeger):                 Tempo:
─────────────────────────────────────────────────────────────────

Store + Index everything:            Store only, index nothing:
• Elasticsearch cluster              • Object storage (S3/GCS)
• Index spans by tags                • Traces by ID only
• Search: service, operation         • Search: trace ID
• Cost: $$$                          • Cost: $

Finding traces:                      Finding traces:
1. Search Jaeger UI                  1. Metrics show problem
2. Find trace by tags                2. Exemplars link to trace ID
                                     3. Logs contain trace ID
                                     4. Look up trace directly

Best for:                            Best for:
• Need tag-based search              • Grafana stack users
• Unknown trace IDs                  • Cost-conscious
• Debugging without metrics          • Metrics-to-traces workflow
```

### Tempo Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEMPO ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Spans via OTLP                                                  │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    DISTRIBUTOR                            │   │
│  │  • Receives spans                                         │   │
│  │  • Hashes trace ID                                        │   │
│  │  • Routes to ingester                                     │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    INGESTER                               │   │
│  │  • Batches spans by trace                                 │   │
│  │  • Holds in memory (WAL)                                  │   │
│  │  • Flushes to object storage                              │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 OBJECT STORAGE                            │   │
│  │  ┌─────────────────┐ ┌─────────────────┐                 │   │
│  │  │  Blocks         │ │  Bloom Filters  │                 │   │
│  │  │  (compressed    │ │  (trace ID      │                 │   │
│  │  │   trace data)   │ │   lookup)       │                 │   │
│  │  └─────────────────┘ └─────────────────┘                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ▲                                      │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    QUERIER                                │   │
│  │  • Receives trace ID queries                              │   │
│  │  • Checks bloom filters                                   │   │
│  │  • Fetches matching blocks                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ▲                                      │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    QUERY FRONTEND                         │   │
│  │  • Caching                                                │   │
│  │  • Query splitting                                        │   │
│  │  • TraceQL processing                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Deploying Tempo

```yaml
# tempo-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tempo-config
  namespace: tracing
data:
  tempo.yaml: |
    server:
      http_listen_port: 3200

    distributor:
      receivers:
        otlp:
          protocols:
            grpc:
              endpoint: 0.0.0.0:4317
            http:
              endpoint: 0.0.0.0:4318
        jaeger:
          protocols:
            thrift_http:
              endpoint: 0.0.0.0:14268

    ingester:
      trace_idle_period: 10s
      max_block_bytes: 1_000_000
      max_block_duration: 5m

    compactor:
      compaction:
        block_retention: 48h

    storage:
      trace:
        backend: s3
        s3:
          bucket: tempo-traces
          endpoint: s3.amazonaws.com
          region: us-east-1
        wal:
          path: /var/tempo/wal
        local:
          path: /var/tempo/blocks

    querier:
      frontend_worker:
        frontend_address: tempo-query-frontend:9095

    query_frontend:
      search:
        duration_slo: 5s
        throughput_bytes_slo: 1073741824
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tempo
  namespace: tracing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tempo
  template:
    metadata:
      labels:
        app: tempo
    spec:
      containers:
        - name: tempo
          image: grafana/tempo:2.3.0
          args:
            - -config.file=/etc/tempo/tempo.yaml
          ports:
            - containerPort: 3200  # HTTP
            - containerPort: 4317  # OTLP gRPC
            - containerPort: 4318  # OTLP HTTP
          volumeMounts:
            - name: config
              mountPath: /etc/tempo
            - name: storage
              mountPath: /var/tempo
      volumes:
        - name: config
          configMap:
            name: tempo-config
        - name: storage
          emptyDir: {}
```

### TraceQL (Tempo's Query Language)

```traceql
# Find traces by service name
{ resource.service.name = "api-gateway" }

# Find slow spans
{ span.http.status_code >= 500 && duration > 1s }

# Find traces with errors
{ status = error }

# Find specific operation
{ name = "HTTP GET /users" }

# Combine conditions
{
  resource.service.name = "payment-service" &&
  span.http.method = "POST" &&
  duration > 500ms
}

# Aggregate: Find slowest operations
{ resource.service.name = "api" } | avg(duration) by (name)

# Pipeline: Filter then aggregate
{ duration > 100ms } | count() by (resource.service.name)
```

## Sampling Strategies

### Why Sample?

```
THE SAMPLING MATH:

1000 requests/second × 50 spans/request × 1KB/span = 50 MB/second
                                                    = 4.3 TB/day
                                                    = 130 TB/month

At 10% sampling:
100 requests/second × 50 spans/request × 1KB/span = 5 MB/second
                                                   = 432 GB/day
                                                   = 13 TB/month

RULE OF THUMB: Sample enough to catch errors, not so much you go broke
```

### Sampling Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAMPLING STRATEGIES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  HEAD-BASED SAMPLING                                             │
│  Decision at trace start                                         │
│  ┌─────┐                                                         │
│  │ App │──▶ Random: 10% sampled ──▶ Propagate decision          │
│  └─────┘                           (all or nothing)              │
│                                                                  │
│  Pros: Simple, consistent                                        │
│  Cons: Might miss errors (if not sampled)                       │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  TAIL-BASED SAMPLING                                             │
│  Decision after trace complete                                   │
│  ┌─────┐     ┌─────────────┐     ┌──────────────────┐           │
│  │ App │──▶  │  Collector  │──▶  │ Keep if:         │           │
│  └─────┘     │  (buffer)   │     │ • Error occurred │           │
│              └─────────────┘     │ • Latency > 1s   │           │
│                                  │ • Important user │           │
│                                  └──────────────────┘           │
│                                                                  │
│  Pros: Never miss errors, smart decisions                       │
│  Cons: Complex, memory-intensive                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### OpenTelemetry Collector Tail Sampling

```yaml
# otel-collector-config.yaml
processors:
  tail_sampling:
    decision_wait: 10s  # Wait for all spans
    num_traces: 100000  # Traces in memory
    policies:
      # Always keep errors
      - name: errors
        type: status_code
        status_code:
          status_codes: [ERROR]

      # Always keep slow traces
      - name: slow-traces
        type: latency
        latency:
          threshold_ms: 1000

      # Always keep specific endpoints
      - name: important-endpoints
        type: string_attribute
        string_attribute:
          key: http.url
          values: ["/checkout", "/payment"]

      # Sample everything else at 10%
      - name: probabilistic
        type: probabilistic
        probabilistic:
          sampling_percentage: 10

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [tail_sampling, batch]
      exporters: [jaeger]
```

## Correlating Signals

### The Three Pillars Connected

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL CORRELATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WORKFLOW: Something is broken, find out why                    │
│                                                                  │
│  1. METRICS show problem                                         │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ http_request_duration_seconds{...} = 5.2s ◀── SLOW!     │ │
│     │                                                          │ │
│     │ histogram has "exemplar" → trace_id: abc123             │ │
│     └─────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  2. TRACE shows journey                                          │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ trace_id: abc123                                         │ │
│     │ ├─ api-gateway (50ms)                                    │ │
│     │ │  └─ user-service (100ms)                               │ │
│     │ │     └─ postgres (3000ms) ◀── HERE'S THE PROBLEM!      │ │
│     │ └─ order-service (200ms)                                 │ │
│     └─────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  3. LOGS show details                                            │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ {trace_id="abc123"} | json                               │ │
│     │                                                          │ │
│     │ 10:30:01 user-service: Query started                     │ │
│     │ 10:30:04 postgres: Lock wait timeout exceeded           │ │
│     │ 10:30:04 user-service: Query failed, retrying           │ │
│     └─────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Exemplars in Prometheus

```yaml
# Enable exemplars in your app
from prometheus_client import Histogram
from opentelemetry import trace

histogram = Histogram('http_request_duration_seconds', 'Request duration')

def handle_request():
    span = trace.get_current_span()
    trace_id = span.get_span_context().trace_id

    with histogram.time() as metric:
        # Handle request
        process_request()

    # Attach trace_id as exemplar
    metric.observe(duration, {'trace_id': format(trace_id, '032x')})
```

```yaml
# Prometheus config to scrape exemplars
scrape_configs:
  - job_name: 'my-app'
    scrape_interval: 15s
    # Enable exemplar scraping (requires Prometheus 2.27+)
    enable_exemplars: true
```

### Grafana Correlation

```yaml
# Grafana data sources configured for correlation
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    jsonData:
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: tempo

  - name: Tempo
    type: tempo
    uid: tempo
    url: http://tempo:3200
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        tags: ['service.name']
        mappedTags: [{ key: 'service.name', value: 'app' }]
        mapTagNamesEnabled: true

  - name: Loki
    type: loki
    uid: loki
    url: http://loki:3100
    jsonData:
      derivedFields:
        - name: TraceID
          matcherRegex: '"trace_id":"(\w+)"'
          url: '${__value.raw}'
          datasourceUid: tempo
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Storing 100% of traces | Costs explode, storage overload | Sample at 1-10%, keep all errors |
| Missing context propagation | Traces disconnect at service boundaries | Use OTel auto-instrumentation, verify headers |
| Too many spans | Cardinality issues, hard to read | Span meaningful operations, not every function |
| Not correlating signals | Miss the full picture | Add trace_id to logs, use exemplars |
| Ignoring sampling bias | Missing rare errors | Use tail-based sampling for errors |
| No service name in spans | Can't filter by service | Always set `service.name` resource attribute |

## War Story: The $4.2 Million Black Friday Ghost

```
┌─────────────────────────────────────────────────────────────────┐
│  THE $4.2 MILLION BLACK FRIDAY GHOST                            │
│  ───────────────────────────────────────────────────────────────│
│  Company: Major online retailer                                 │
│  Architecture: 127 microservices across 3 cloud regions         │
│  Black Friday target: $89 million in 24 hours                   │
│  The nightmare: Checkout failures, no visibility, finger-pointing│
└─────────────────────────────────────────────────────────────────┘
```

**10:00 AM - Black Friday**

The traffic surge began as expected. Everything looked green on dashboards. Then customers started complaining: "Payment accepted, but no order confirmation." Not errors—just silence. The orders vanished into the void.

**11:30 AM - The War Room Assembles**

Fifteen engineers from payment, inventory, fulfillment, and notification teams. Each team's metrics looked healthy. Each team's logs showed successful operations. "It's not us," echoed around the room.

```
METRICS ANALYSIS (All services "green"):
─────────────────────────────────────────────────────────────────
payment-service:      error_rate: 0.02%  ✓  (within SLA)
inventory-service:    error_rate: 0.01%  ✓  (within SLA)
fulfillment-service:  error_rate: 0.03%  ✓  (within SLA)
notification-service: error_rate: 0.00%  ✓  (within SLA)

But checkout completion rate: DOWN 23%
```

**2:00 PM - Desperation Sets In**

Revenue loss was mounting. Engineers manually correlated logs by timestamp—needle in a haystack across 127 services. Someone suggested "Let's just restart everything." They did. Problem persisted.

**4:30 PM - The Breakthrough**

A junior engineer had been implementing distributed tracing as a "20% project." It wasn't fully deployed, but it covered the payment flow. She enabled sampling to 100% and captured a failing request.

```
TRACE: f8d2e4a1-7b3c-4e5f-9a1b-2c3d4e5f6a7b
─────────────────────────────────────────────────────────────────
api-gateway (12ms)
 └─ checkout-orchestrator (2,847ms) ← SUSPICIOUSLY LONG
     ├─ payment-service (156ms) ✓
     ├─ inventory-reserve (89ms) ✓
     └─ fulfillment-queue (2,589ms) ← THE BOTTLENECK
         └─ kafka-producer (TIMEOUT) ✗

Root cause: Kafka broker rebalancing during traffic spike
- Producer timeout: 3000ms
- Actual wait: 2589ms (retrying internally, not reporting errors)
- Result: fire-and-forget message lost, no error logged
```

**The Root Cause**

The fulfillment service used Kafka with `acks=1` and fire-and-forget publishing. During the traffic spike, Kafka brokers started rebalancing. Messages were accepted by the producer but never delivered. No errors because the producer configured timeouts to fail silently.

```yaml
# The problematic Kafka config (production)
producer:
  acks: 1                    # ← Only leader ack, not replicas
  retries: 0                 # ← No retry on failure
  linger.ms: 0              # ← Send immediately, no batching
  request.timeout.ms: 3000  # ← 3s timeout, then silent drop
  # No error callback configured
```

**The Fix (Applied at 5:15 PM)**

```yaml
# Fixed Kafka config
producer:
  acks: all                  # ← Wait for all replicas
  retries: 3                 # ← Retry on transient failures
  enable.idempotence: true   # ← Prevent duplicates
  delivery.timeout.ms: 120000
  # Error callback: log and alert on failed delivery
```

**The Financial Impact**

```
BLACK FRIDAY DAMAGE ASSESSMENT
─────────────────────────────────────────────────────────────────
Duration of incident:      7.25 hours (10:00 AM → 5:15 PM)
Peak revenue rate:         $62,000/minute
Lost orders:               ~6,800 checkouts
Average order value:       $617
Direct lost revenue:       $4,195,600

Additional costs:
- Emergency escalation:    $47,000 (contractor callouts)
- Customer service surge:  $23,000 (extended hours)
- Reputation damage:       Immeasurable (social media storm)

Total quantifiable impact: ~$4.3 million in one day
```

**Why Tracing Saved Them**

```
WITHOUT TRACING:                    WITH TRACING:
─────────────────────────────────────────────────────────────────
• 15 engineers, 7 hours            • 1 engineer, 45 minutes
• Each service looked healthy      • Saw exact failure point
• Finger-pointing war              • Objective evidence
• "Restart everything"             • Targeted fix
• Would have continued failing     • Identified silent failure mode
```

**The Monday After**

The team mandated distributed tracing across all 127 services. Within 6 weeks, full coverage. The junior engineer's "20% project" became the company's standard. Her promotion followed.

**Key Lessons**

1. **Silent failures are the deadliest**: Services that fail without logging are invisible to everything except traces
2. **Green dashboards can lie**: Individual service metrics don't show cross-service failures
3. **Timeouts must be instrumented**: Any timeout should create a span with explicit failure status
4. **Fire-and-forget is gambling**: Async operations need delivery confirmation and tracing
5. **Traces show what logs and metrics cannot**: The request's journey through time and services

## Quiz

### Question 1
Why is tail-based sampling more expensive than head-based sampling?

<details>
<summary>Show Answer</summary>

Tail-based sampling requires:

1. **Memory**: Must buffer all spans until the trace is complete (could be seconds or minutes)
2. **Compute**: Analyzes every span to decide if the trace is interesting (errors, high latency)
3. **Network**: Must receive ALL spans before deciding, then discard most

Head-based sampling decides at trace start:
- Uses minimal memory (just a random number)
- No analysis needed
- Discarded spans never sent

A trace with 100 spans: tail-based must process all 100 before discarding 90%. Head-based discards 90% immediately, never sending the spans at all.
</details>

### Question 2
How would you find all traces where a payment-service call took longer than 500ms?

<details>
<summary>Show Answer</summary>

**In Jaeger:**
1. Service: payment-service
2. Tags: `http.status_code=*` (any)
3. Min Duration: 500ms
4. Search

**In Tempo with TraceQL:**
```traceql
{
  resource.service.name = "payment-service" &&
  duration > 500ms
}
```

**Via metrics → exemplars:**
1. Query Prometheus: `histogram_quantile(0.99, http_request_duration_seconds_bucket{service="payment"})`
2. Click data point with high latency
3. View exemplar → links to trace ID
4. Open in Tempo/Jaeger
</details>

### Question 3
A trace shows gaps—services A→B→C are traced, but C→D appears as a separate trace. What's likely wrong?

<details>
<summary>Show Answer</summary>

Context propagation is broken between C and D. Common causes:

1. **Missing instrumentation**: Service C might be making HTTP calls without the OTel HTTP client instrumentation. The outgoing call doesn't include `traceparent` header.

2. **Header stripping**: A proxy, API gateway, or service mesh between C and D might be removing the trace headers.

3. **Async communication**: If C→D uses a message queue, you need specific instrumentation to propagate context through messages. Default HTTP instrumentation won't help.

4. **Different tracing systems**: C might use Jaeger client, D might use Zipkin—they need compatible propagation format (W3C Trace Context works across both).

Debug by checking: Do the HTTP requests from C include `traceparent` header? Does D receive and extract it?
</details>

### Question 4
You see a trace where user-service took 2 seconds, but all its child spans (db queries, cache calls) total only 200ms. Where did 1.8 seconds go?

<details>
<summary>Show Answer</summary>

The 1.8 seconds is "dark time"—work happening outside of instrumented operations. Common causes:

1. **CPU-bound code**: JSON parsing, business logic, serialization—typically not instrumented as spans

2. **Uninstrumented I/O**: File system operations, non-HTTP network calls, DNS lookups

3. **Garbage collection**: Long GC pauses appear as gaps in traces

4. **Thread pool waiting**: Time waiting for a thread to become available

5. **Missing child spans**: Some operations might not be instrumented (internal service calls, cache client)

To find it:
- Add spans around suspicious code blocks
- Profile the application (CPU, memory)
- Check for GC pauses in JVM/runtime logs
- Verify all I/O operations are instrumented
</details>

### Question 5
Your system processes 5,000 requests/second with an average of 40 spans per trace at 800 bytes per span. You're using 5% head sampling. Calculate daily storage requirements and explain why tail sampling might still be needed.

<details>
<summary>Show Answer</summary>

**Storage calculation:**
```
5,000 req/s × 40 spans × 800 bytes = 160 MB/second raw
With 5% sampling: 8 MB/second = 691 GB/day

Monthly storage: ~21 TB
At $0.023/GB (S3): ~$480/month
```

**Why tail sampling is still needed:**

Head sampling randomly keeps 5% of traces. But consider:
- Error rate: 0.1% of requests fail
- At 5% sampling, you capture: 5,000 × 0.001 × 0.05 = 0.25 errors/second
- Some error traces will be discarded!

Tail sampling ensures:
1. **All errors captured**: Sample 100% of traces with `status=error`
2. **All slow requests captured**: Keep traces where `duration > SLA`
3. **Important users**: Keep traces for premium customers
4. **Then sample the rest**: 5% of normal successful traces

Configuration pattern:
```yaml
policies:
  - name: keep-errors
    type: status_code
    status_codes: [ERROR]
  - name: keep-slow
    type: latency
    threshold_ms: 2000
  - name: sample-rest
    type: probabilistic
    sampling_percentage: 5
```
</details>

### Question 6
Your traces are breaking at a Kafka message boundary. Service A publishes, Service B consumes, but they appear as separate traces. How do you fix this?

<details>
<summary>Show Answer</summary>

Kafka (and other message queues) don't automatically propagate trace context like HTTP does. You must:

**1. Inject context when producing:**
```python
from opentelemetry import trace
from opentelemetry.propagate import inject

def produce_message(topic, message):
    headers = {}
    # Inject current trace context into headers
    inject(headers)

    producer.send(topic,
                  value=message,
                  headers=[(k, v.encode()) for k, v in headers.items()])
```

**2. Extract context when consuming:**
```python
from opentelemetry.propagate import extract

def consume_message(message):
    # Convert Kafka headers to dict
    headers = {k: v.decode() for k, v in message.headers}

    # Extract and use as parent context
    ctx = extract(headers)

    with tracer.start_as_current_span("process_message", context=ctx):
        # Now this span is linked to producer's trace
        process(message)
```

**3. Use OTel instrumentation libraries:**
```python
from opentelemetry.instrumentation.kafka import KafkaInstrumentor

KafkaInstrumentor().instrument()  # Auto-instruments produce/consume
```

The key insight: HTTP auto-propagates via headers. Message queues need explicit instrumentation for each message system (Kafka, RabbitMQ, SQS, etc.).
</details>

### Question 7
You're comparing Jaeger and Tempo for your organization. Given this scenario, which would you choose and why?

**Scenario**: 80 microservices, Grafana already deployed, storing 500GB traces/day, need to search by custom business attributes (customer_id, order_id), budget-conscious.

<details>
<summary>Show Answer</summary>

**Recommendation: Jaeger** for this scenario, despite the budget focus.

**Analysis:**

| Factor | Jaeger | Tempo |
|--------|--------|-------|
| Grafana integration | Good (via datasource) | Native (built-in) |
| Custom tag search | ✓ Full support | ✗ Requires exemplars/logs |
| Storage cost | Higher (requires indexing) | Lower (object storage) |
| 500GB/day | ~$3,000-5,000/month (ES) | ~$350/month (S3) |

**Why Jaeger wins here:**

The requirement "search by customer_id, order_id" is critical. Tempo's architecture is trace-ID-only lookup. To find traces by customer_id:

With Tempo:
1. Customer calls support: "Order 12345 failed"
2. You search Loki for `order_id=12345`
3. Find log line with trace_id
4. Look up trace_id in Tempo

With Jaeger:
1. Customer calls support: "Order 12345 failed"
2. Search Jaeger: `order_id=12345`
3. Get traces directly

**If budget is paramount:**

Consider Tempo + richer logging:
- Log every transaction with trace_id
- Accept the two-hop lookup workflow
- Save $2,500-4,000/month

**Hybrid approach:**
- Tempo for storage (cheap)
- Sample 100% of errors/slow requests into Jaeger (searchable)
- This gives searchability for interesting traces, cheap storage for the rest
</details>

### Question 8
Given this TraceQL query, explain what it finds and write an equivalent Jaeger search:

```traceql
{ resource.service.name = "checkout" && span.http.status_code >= 500 } | avg(duration) by (span.http.route) | > 1s
```

<details>
<summary>Show Answer</summary>

**What this query finds:**

1. `resource.service.name = "checkout"` - Traces from the checkout service
2. `span.http.status_code >= 500` - Only spans with server errors (5xx)
3. `avg(duration) by (span.http.route)` - Calculate average duration grouped by HTTP endpoint
4. `> 1s` - Filter to routes where average error duration exceeds 1 second

**In plain English**: "Find which API endpoints in checkout service have slow 5xx errors (averaging over 1 second), so we can prioritize fixing the slowest failure modes."

**Equivalent Jaeger search:**

Jaeger doesn't support aggregations in queries. You would:

1. **Search in Jaeger UI:**
   - Service: checkout
   - Tags: `http.status_code >= 500`
   - Min Duration: 1s

2. **Export and analyze externally:**
   ```bash
   # Fetch traces via API
   curl "http://jaeger:16686/api/traces?service=checkout&tags=http.status_code:500" \
     | jq '.data[].spans[] | select(.duration > 1000000) | {route: .tags["http.route"], duration: .duration}'
   ```

3. **Use Jaeger metrics (if enabled):**
   ```promql
   histogram_quantile(0.5,
     rate(jaeger_trace_duration_bucket{service="checkout", status_code=~"5.."}[5m])
   ) > 1
   ```

**Key insight**: TraceQL is more powerful for ad-hoc analysis. Jaeger excels at finding individual traces but requires external tools for aggregation.
</details>

## Hands-On Exercise

### Scenario: End-to-End Tracing Investigation

Set up a traced application and practice navigating from metrics to traces to logs.

### Setup

```bash
# Create kind cluster
kind create cluster --name tracing-lab

# Install the full observability stack
kubectl create namespace tracing

# Deploy Tempo
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: tempo-config
  namespace: tracing
data:
  tempo.yaml: |
    server:
      http_listen_port: 3200
    distributor:
      receivers:
        otlp:
          protocols:
            grpc:
              endpoint: 0.0.0.0:4317
    ingester:
      trace_idle_period: 10s
      max_block_duration: 5m
    storage:
      trace:
        backend: local
        local:
          path: /var/tempo/traces
        wal:
          path: /var/tempo/wal
    query_frontend:
      search:
        duration_slo: 5s
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tempo
  namespace: tracing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tempo
  template:
    metadata:
      labels:
        app: tempo
    spec:
      containers:
        - name: tempo
          image: grafana/tempo:2.3.0
          args: ["-config.file=/etc/tempo/tempo.yaml"]
          ports:
            - containerPort: 3200
            - containerPort: 4317
          volumeMounts:
            - name: config
              mountPath: /etc/tempo
            - name: storage
              mountPath: /var/tempo
      volumes:
        - name: config
          configMap:
            name: tempo-config
        - name: storage
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: tempo
  namespace: tracing
spec:
  ports:
    - name: http
      port: 3200
    - name: otlp-grpc
      port: 4317
  selector:
    app: tempo
EOF

# Wait for Tempo
kubectl -n tracing wait --for=condition=ready pod -l app=tempo --timeout=120s
```

### Deploy Traced Application

```yaml
# traced-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: traced-demo
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: traced-demo
  template:
    metadata:
      labels:
        app: traced-demo
    spec:
      containers:
        - name: app
          image: jaegertracing/example-hotrod:1.50
          ports:
            - containerPort: 8080
          env:
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://tempo.tracing.svc.cluster.local:4317"
            - name: OTEL_SERVICE_NAME
              value: "hotrod"
```

```bash
kubectl apply -f traced-app.yaml

# Port forward to access the demo app
kubectl port-forward svc/traced-demo 8080:8080 &

# Port forward Tempo
kubectl -n tracing port-forward svc/tempo 3200:3200 &
```

### Investigation Tasks

1. **Generate traces**
   - Open http://localhost:8080
   - Click different buttons to request rides
   - Each click generates a multi-service trace

2. **Query Tempo**
   ```bash
   # List trace IDs
   curl "http://localhost:3200/api/search?limit=10"

   # Get a specific trace
   curl "http://localhost:3200/api/traces/<trace-id>"
   ```

3. **Use TraceQL**
   ```traceql
   # Find slow driver lookups
   { name = "SQL SELECT" && duration > 100ms }

   # Find errors
   { status = error }
   ```

4. **Practice correlation**
   - Note a trace ID from a slow request
   - Search logs for that trace ID
   - Understand the full request journey

### Success Criteria

- [ ] Can generate traces from the demo app
- [ ] Can query traces by service name
- [ ] Can find slow operations within a trace
- [ ] Understand parent-child span relationships
- [ ] Can explain where latency accumulates

### Cleanup

```bash
kind delete cluster --name tracing-lab
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain trace anatomy: trace ID, span ID, parent span ID, and how they connect
- [ ] Describe W3C Trace Context headers (`traceparent`, `tracestate`) and their format
- [ ] Compare Jaeger vs Tempo trade-offs: searchability vs cost, indexed vs ID-only
- [ ] Calculate trace storage costs: requests/sec × spans × size × sampling rate
- [ ] Configure head vs tail sampling and explain when each is appropriate
- [ ] Propagate trace context through HTTP (automatic) and message queues (manual)
- [ ] Use TraceQL to find slow spans, errors, and aggregate by attributes
- [ ] Correlate the three signals: metrics → exemplars → traces → logs
- [ ] Identify "dark time" in traces where uninstrumented code hides latency
- [ ] Deploy Jaeger or Tempo in Kubernetes and instrument applications with OTel

## Next Steps

Congratulations! You've completed the Observability Toolkit. You now understand:
- **Prometheus** for metrics
- **OpenTelemetry** for instrumentation
- **Grafana** for visualization
- **Loki** for logs
- **Jaeger/Tempo** for traces

Consider exploring:
- [GitOps & Deployments Toolkit](../../cicd-delivery/gitops-deployments/) — Deploy your observable applications
- [SRE Discipline](../../../disciplines/core-platform/sre/) — Apply observability for reliability

---

*"A trace is a story. Each span is a chapter. The trace ID is how you find the book. Learn to read the story, and you'll solve mysteries others can't even see."*

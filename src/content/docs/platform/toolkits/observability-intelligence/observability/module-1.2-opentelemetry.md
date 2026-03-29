---
title: "Module 1.2: OpenTelemetry"
slug: platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

## Prerequisites

Before starting this module:
- [Module 1.1: Prometheus](module-1.1-prometheus/)
- [Observability Theory Track](../../../foundations/observability-theory/)
- Basic understanding of distributed tracing
- Familiarity with at least one programming language

---

The platform team at a major European bank faced an impossible decision. Their 400-microservice system used three different tracing solutions—legacy services on Zipkin, newer Java services on Jaeger, and a recent Python rewrite with DataDog instrumentation. When a critical payment flow crossed all three systems, traces simply... stopped. Each tool saw only its fragment of the transaction.

A regulatory audit demanded end-to-end transaction tracing within 90 days. The vendor quotes came back: €2.4 million to migrate everything to a single commercial solution, with 18 months of engineering effort. The platform architect stared at the numbers, knowing they had neither the budget nor the timeline.

Then she discovered OpenTelemetry. Within three weeks, her team deployed the OTel Collector as a proxy between all existing instrumentation and a unified backend. Legacy Zipkin spans flowed through. Jaeger spans converted automatically. DataDog traces joined the stream. The entire payment flow appeared as a single trace for the first time in the company's history.

The cost? Zero licensing fees. The migration effort? Six engineers for three weeks. The audit? Passed with commendation.

---

## Why This Module Matters

The observability landscape was fragmented. Prometheus for metrics, Jaeger for traces, different agents for different backends. Each vendor had its own SDK. Switching vendors meant rewriting instrumentation code.

OpenTelemetry (OTel) unifies this chaos. One SDK, one protocol, any backend. Instrument once, export anywhere. It's become the industry standard—backed by every major observability vendor and cloud provider.

If you're building new services, OpenTelemetry is the instrumentation layer you should use.

## Did You Know?

- **OpenTelemetry merged OpenTracing and OpenCensus** in 2019, unifying two competing standards and ending years of fragmentation
- **OTel is the second most active CNCF project** after Kubernetes—with contributions from Google, Microsoft, AWS, and every major observability vendor
- **Auto-instrumentation can capture 80% of telemetry** with zero code changes—just deploy the OTel agent
- **The OTel Collector processes millions of spans per second** on modest hardware—it's designed for scale

## OpenTelemetry Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 OPENTELEMETRY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  APPLICATION                                                     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │     │
│  │  │   Traces     │  │   Metrics    │  │    Logs      │ │     │
│  │  │  (spans)     │  │  (counters)  │  │  (records)   │ │     │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │     │
│  │         │                 │                 │          │     │
│  │  ┌──────▼─────────────────▼─────────────────▼───────┐ │     │
│  │  │              OTel SDK                            │ │     │
│  │  │  • Context propagation                           │ │     │
│  │  │  • Batching & sampling                           │ │     │
│  │  │  • Export to collector                           │ │     │
│  │  └──────────────────────┬───────────────────────────┘ │     │
│  └─────────────────────────┼─────────────────────────────┘     │
│                            │                                    │
│                            │ OTLP (gRPC/HTTP)                   │
│                            ▼                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                   OTEL COLLECTOR                        │    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐          │    │
│  │  │ Receivers│───▶│Processors│───▶│ Exporters│          │    │
│  │  │ (OTLP,   │    │ (batch,  │    │ (Jaeger, │          │    │
│  │  │  Jaeger, │    │  filter, │    │  Prom,   │          │    │
│  │  │  Zipkin) │    │  sample) │    │  Loki)   │          │    │
│  │  └──────────┘    └──────────┘    └──────────┘          │    │
│  └───────────────────────────┬────────────────────────────┘    │
│                              │                                  │
│           ┌──────────────────┼──────────────────┐              │
│           ▼                  ▼                  ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │    Jaeger    │   │  Prometheus  │   │    Loki      │       │
│  │   (traces)   │   │   (metrics)  │   │    (logs)    │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Purpose |
|-----------|---------|
| **SDK** | Instrument applications, create telemetry |
| **API** | Vendor-neutral interface for instrumentation |
| **OTLP** | OpenTelemetry Protocol—standard wire format |
| **Collector** | Receive, process, export telemetry |
| **Auto-instrumentation** | Instrument common libraries automatically |

### The Three Pillars in OTel

```
TRACES                    METRICS                   LOGS
─────────────────────────────────────────────────────────────────

Spans with context        Aggregated numbers        Discrete events
│                         │                         │
├─ TraceID (links)        ├─ Counter                ├─ Timestamp
├─ SpanID                 ├─ Gauge                  ├─ Severity
├─ ParentSpanID           ├─ Histogram              ├─ Body
├─ Attributes             ├─ Attributes             ├─ Attributes
└─ Events                 └─ Exemplars (→trace)     └─ TraceID (→trace)

All three can be correlated via TraceID and common attributes
```

### War Story: The $1.8 Million Vendor Lock-In Escape

An e-commerce company had built their entire observability stack on a commercial APM vendor. Every service, 127 of them, contained vendor-specific SDK calls hardcoded into the application logic. Annual licensing: $890,000.

**Year 3**: The vendor raised prices 40%. The CFO demanded alternatives.

**The Audit Results**:
```
Vendor SDK Calls Across Codebase
─────────────────────────────────────────────────────────────────
Python services:     847 direct SDK imports
Java services:       2,341 agent configurations
Node.js services:    523 custom instrumentations
Mobile apps:         189 embedded SDK calls
─────────────────────────────────────────────────────────────────
Total touchpoints:   3,900+
Estimated rewrite:   18 months, 12 engineers
Cost at new rates:   $2.4M over 2 years
```

**The OpenTelemetry Migration**:

**Week 1-2**: Deployed OTel Collector as a sidecar, configured to receive the vendor's proprietary protocol and export to both the old vendor AND a new backend.

**Week 3-4**: Auto-instrumentation agents replaced 80% of manual SDK calls. Java services: one JVM flag. Python: one wrapper command.

**Month 2-3**: Migrated remaining 20% of custom instrumentation to OTel SDK. Most changes were search-and-replace.

**Month 4**: Cut over to the new backend. Cancelled the old vendor contract.

```
Migration Financial Summary
─────────────────────────────────────────────────────────────────
Engineering effort:       4 months, 6 engineers = $480,000
New backend licensing:    $180,000/year
Year 1 savings:          $230,000
Year 2+ savings:         $710,000/year
5-year savings:          $3,070,000
─────────────────────────────────────────────────────────────────
ROI: 640%
```

**The Lesson**: Vendor-neutral instrumentation isn't about today's costs—it's about tomorrow's negotiating leverage. With OpenTelemetry, you can change backends by editing a config file, not rewriting your codebase.

## SDK Instrumentation

### Python Example

```python
# Install: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Configure resource (service identity)
resource = Resource.create({
    "service.name": "order-service",
    "service.version": "1.0.0",
    "deployment.environment": "production",
})

# Configure tracer provider
provider = TracerProvider(resource=resource)

# Add OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Set global tracer provider
trace.set_tracer_provider(provider)

# Get tracer
tracer = trace.get_tracer(__name__)

# Use tracer
@tracer.start_as_current_span("process_order")
def process_order(order_id: str):
    span = trace.get_current_span()
    span.set_attribute("order.id", order_id)

    # Nested span
    with tracer.start_as_current_span("validate_order") as child_span:
        child_span.set_attribute("validation.type", "full")
        validate(order_id)

    with tracer.start_as_current_span("save_order"):
        save(order_id)
```

### Java Example

```java
// Add dependency: io.opentelemetry:opentelemetry-api
// Add dependency: io.opentelemetry:opentelemetry-sdk
// Add dependency: io.opentelemetry:opentelemetry-exporter-otlp

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;

public class OrderService {
    private static final Tracer tracer =
        GlobalOpenTelemetry.getTracer("order-service", "1.0.0");

    public void processOrder(String orderId) {
        Span span = tracer.spanBuilder("process_order")
            .setAttribute("order.id", orderId)
            .startSpan();

        try (Scope scope = span.makeCurrent()) {
            validateOrder(orderId);
            saveOrder(orderId);
        } catch (Exception e) {
            span.recordException(e);
            throw e;
        } finally {
            span.end();
        }
    }

    private void validateOrder(String orderId) {
        Span span = tracer.spanBuilder("validate_order").startSpan();
        try (Scope scope = span.makeCurrent()) {
            // validation logic
        } finally {
            span.end();
        }
    }
}
```

### Metrics Example (Python)

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Configure meter provider
exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317")
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=1000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

# Get meter
meter = metrics.get_meter(__name__)

# Create instruments
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total HTTP requests",
    unit="1",
)

request_duration = meter.create_histogram(
    name="http_request_duration_seconds",
    description="HTTP request duration",
    unit="s",
)

# Use instruments
def handle_request(method: str, path: str):
    start = time.time()
    try:
        # handle request
        request_counter.add(1, {"method": method, "path": path, "status": "200"})
    finally:
        duration = time.time() - start
        request_duration.record(duration, {"method": method, "path": path})
```

## Auto-Instrumentation

### Zero-Code Instrumentation

```
AUTO-INSTRUMENTATION
─────────────────────────────────────────────────────────────────

Without OTel Agent:              With OTel Agent:
┌────────────────────┐           ┌────────────────────┐
│  Your Application  │           │  Your Application  │
│                    │           │  (unchanged code)  │
│  No telemetry :(   │           │         │          │
│                    │           │         ▼          │
└────────────────────┘           │  ┌──────────────┐  │
                                 │  │  OTel Agent  │  │
                                 │  │  (injected)  │  │
                                 │  └──────┬───────┘  │
                                 │         │          │
                                 │  Traces, metrics,  │
                                 │  logs automatically │
                                 └────────────────────┘

Instruments:
• HTTP clients/servers (requests, Flask, FastAPI, Spring)
• Database clients (SQLAlchemy, JDBC, psycopg2)
• Message queues (Kafka, RabbitMQ)
• gRPC, Redis, AWS SDK, and more...
```

### Python Auto-Instrumentation

```bash
# Install
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install

# Run with auto-instrumentation
opentelemetry-instrument \
  --traces_exporter otlp \
  --metrics_exporter otlp \
  --service_name my-service \
  --exporter_otlp_endpoint http://otel-collector:4317 \
  python app.py
```

### Java Agent

```bash
# Download agent
wget https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar

# Run with agent
java -javaagent:opentelemetry-javaagent.jar \
  -Dotel.service.name=my-service \
  -Dotel.exporter.otlp.endpoint=http://otel-collector:4317 \
  -jar myapp.jar
```

### Kubernetes Auto-Instrumentation

```yaml
# Using OTel Operator
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: auto-instrumentation
spec:
  exporter:
    endpoint: http://otel-collector:4317
  propagators:
    - tracecontext
    - baggage
  python:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-python:latest
  java:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-java:latest
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        # Enable auto-instrumentation for Python
        instrumentation.opentelemetry.io/inject-python: "true"
    spec:
      containers:
        - name: app
          image: my-python-app
```

## OTel Collector

### Collector Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OTEL COLLECTOR                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RECEIVERS                PROCESSORS              EXPORTERS      │
│  ┌──────────┐            ┌──────────┐           ┌──────────┐   │
│  │   otlp   │───────────▶│  batch   │──────────▶│   otlp   │   │
│  └──────────┘            └──────────┘           └──────────┘   │
│  ┌──────────┐            ┌──────────┐           ┌──────────┐   │
│  │  jaeger  │───────────▶│ memory   │──────────▶│  jaeger  │   │
│  └──────────┘            │ limiter  │           └──────────┘   │
│  ┌──────────┐            └──────────┘           ┌──────────┐   │
│  │prometheus│───────────▶┌──────────┐──────────▶│prometheus│   │
│  └──────────┘            │ filter   │           └──────────┘   │
│  ┌──────────┐            └──────────┘           ┌──────────┐   │
│  │  zipkin  │───────────▶┌──────────┐──────────▶│   loki   │   │
│  └──────────┘            │ sampling │           └──────────┘   │
│                          └──────────┘                           │
│                                                                  │
│  PIPELINES (connect receivers → processors → exporters)         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ traces:   receivers: [otlp]                              │   │
│  │           processors: [batch, sampling]                  │   │
│  │           exporters: [jaeger, otlp]                      │   │
│  │                                                          │   │
│  │ metrics:  receivers: [otlp, prometheus]                  │   │
│  │           processors: [batch]                            │   │
│  │           exporters: [prometheus]                        │   │
│  │                                                          │   │
│  │ logs:     receivers: [otlp]                              │   │
│  │           processors: [batch]                            │   │
│  │           exporters: [loki]                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Collector Configuration

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  # Scrape Prometheus endpoints
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          static_configs:
            - targets: ['localhost:8888']

processors:
  # Batch for efficiency
  batch:
    timeout: 1s
    send_batch_size: 1024

  # Prevent OOM
  memory_limiter:
    check_interval: 1s
    limit_mib: 1000
    spike_limit_mib: 200

  # Add resource attributes
  resource:
    attributes:
      - key: environment
        value: production
        action: upsert

  # Filter out health checks
  filter:
    spans:
      exclude:
        match_type: regexp
        span_names:
          - "health.*"
          - "readiness.*"

exporters:
  # Export to Jaeger
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  # Export to Prometheus
  prometheus:
    endpoint: 0.0.0.0:8889

  # Export to another OTLP endpoint
  otlp:
    endpoint: tempo:4317
    tls:
      insecure: true

  # Debug logging
  logging:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, filter]
      exporters: [jaeger, otlp]

    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch, resource]
      exporters: [prometheus]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [logging]
```

### Sampling Strategies

```yaml
processors:
  # Tail-based sampling (requires trace completion)
  tail_sampling:
    decision_wait: 10s
    num_traces: 100
    expected_new_traces_per_sec: 10
    policies:
      # Always sample errors
      - name: errors
        type: status_code
        status_code:
          status_codes: [ERROR]

      # Sample 10% of successful traces
      - name: success-sampling
        type: probabilistic
        probabilistic:
          sampling_percentage: 10

      # Always sample slow traces
      - name: latency
        type: latency
        latency:
          threshold_ms: 1000

  # Head-based sampling (decision at trace start)
  probabilistic_sampler:
    sampling_percentage: 25
```

## Context Propagation

### How Context Flows

```
CONTEXT PROPAGATION
─────────────────────────────────────────────────────────────────

Service A                    Service B                   Service C
┌──────────────┐            ┌──────────────┐           ┌──────────────┐
│   Span A     │            │   Span B     │           │   Span C     │
│  TraceID: X  │───HTTP────▶│  TraceID: X  │───gRPC───▶│  TraceID: X  │
│  SpanID: 1   │   Headers  │  SpanID: 2   │  Metadata │  SpanID: 3   │
│  Parent: -   │            │  Parent: 1   │           │  Parent: 2   │
└──────────────┘            └──────────────┘           └──────────────┘
       │                           │                          │
       │                           │                          │
       ▼                           ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DISTRIBUTED TRACE                        │
│                                                                 │
│  Span A ─────────────────────────────────────────────          │
│         └── Span B ──────────────────────────                  │
│                     └── Span C ────────────                    │
│                                                                 │
│  TraceID: X (same across all services)                         │
│  Each span knows its parent → forms tree                       │
└─────────────────────────────────────────────────────────────────┘
```

### Propagator Configuration

```python
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

# Use multiple propagators for compatibility
propagator = CompositePropagator([
    TraceContextTextMapPropagator(),  # W3C standard
    W3CBaggagePropagator(),           # W3C baggage
    B3MultiFormat(),                   # Zipkin B3 (legacy)
])
set_global_textmap(propagator)
```

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No resource attributes | Can't identify service | Set service.name, environment |
| Unbatched exports | High overhead | Use batch processor |
| No memory limits | Collector OOM | Configure memory_limiter |
| Missing propagation | Broken traces | Configure propagators consistently |
| Over-sampling | Cost explosion | Use tail sampling |
| No collector | Direct export overhead | Deploy collector as buffer |

## Quiz

Test your understanding:

<details>
<summary>1. Why use the OTel Collector instead of exporting directly from apps?</summary>

**Answer**: The Collector provides:
- **Buffering**: Handles backend unavailability
- **Batching**: Efficient network usage
- **Processing**: Filter, sample, transform
- **Protocol conversion**: Receive in one format, export in another
- **Centralized config**: Change exporters without app changes
- **Reduced app overhead**: Offload processing to collector
</details>

<details>
<summary>2. What's the difference between head-based and tail-based sampling?</summary>

**Answer**:
- **Head-based**: Decision made at trace start (probabilistic). Simple, but might miss interesting traces.
- **Tail-based**: Decision made after trace completes. Can sample based on latency, errors, attributes. More powerful but requires buffering complete traces.

Use tail-based when you need to capture all errors or slow traces.
</details>

<details>
<summary>3. How does context propagation work across services?</summary>

**Answer**: Context flows via HTTP headers or gRPC metadata:
1. Service A creates span, injects TraceID/SpanID into headers
2. HTTP client adds headers: `traceparent: 00-{traceId}-{spanId}-01`
3. Service B extracts headers, creates child span with same TraceID
4. Child span's ParentSpanID = Service A's SpanID

This creates a linked trace across all services.
</details>

<details>
<summary>4. When should you use auto-instrumentation vs. manual?</summary>

**Answer**:
- **Auto-instrumentation**: HTTP, database, messaging libraries. Get 80% coverage with zero code.
- **Manual instrumentation**: Business logic, custom spans for important operations, adding specific attributes.

Best practice: Start with auto-instrumentation, add manual spans for business-critical paths.
</details>

<details>
<summary>5. Your OTel Collector is consuming 8GB RAM and pages are getting killed. What's likely wrong and how do you fix it?</summary>

**Answer**: The Collector is likely missing memory limits or buffering too much data.

**Diagnosis**:
1. Check if `memory_limiter` processor is configured
2. Look at queue sizes in `exporters` section
3. Check if backend is slow/unavailable (causing backup)

**Fix**:
```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 4000        # Hard limit
    spike_limit_mib: 800   # Spike allowance
```

**Root causes**:
- Missing memory_limiter processor (most common)
- Backend unavailable, queue growing indefinitely
- Tail sampling buffering too many traces (reduce `num_traces`)
- Too many concurrent exporters

Always deploy the Collector with resource limits AND the memory_limiter processor.
</details>

<details>
<summary>6. Calculate: You have 1000 req/s, each request generates 50 spans averaging 2KB. With 10% head sampling, how much data per day reaches your backend?</summary>

**Answer**: **~864 GB per day**

Calculation:
```
Without sampling:
1000 req/s × 50 spans × 2KB = 100,000 KB/s = 100 MB/s
100 MB/s × 86,400 sec/day = 8,640,000 MB = 8.64 TB/day

With 10% head sampling:
8.64 TB × 10% = 864 GB/day
```

**Practical implications**:
- At $0.50/GB ingestion (typical vendor pricing): $432/day = $157,680/year
- Tail sampling at 10% with error capture might sample 15-20% (errors are rare)
- Consider: Do you need 1000 req/s sampled, or would 1% (8.64 GB/day) suffice?
</details>

<details>
<summary>7. Service A → Service B → Service C. Traces show A and C, but B appears as a separate trace. What's wrong?</summary>

**Answer**: Context propagation is broken at Service B.

**Diagnostic steps**:
1. **Check incoming headers at B**: Does B receive `traceparent` from A?
2. **Check B's instrumentation**: Is it extracting context before creating spans?
3. **Check B's outgoing calls**: Is it injecting context into requests to C?

**Common causes**:
- B uses a custom HTTP client not instrumented by OTel
- Proxy/gateway between A and B strips unknown headers
- B manually creates spans without setting parent from context
- B uses async message queue without message propagation

**Quick test**:
```bash
# Add debug logging to see if headers arrive
curl -H "traceparent: 00-12345678901234567890123456789012-1234567890123456-01" \
     http://service-b/endpoint
```
</details>

<details>
<summary>8. What's the difference between OTLP/gRPC and OTLP/HTTP? When would you choose each?</summary>

**Answer**:

| Aspect | OTLP/gRPC (4317) | OTLP/HTTP (4318) |
|--------|------------------|------------------|
| **Protocol** | HTTP/2 + Protobuf | HTTP/1.1 + Protobuf or JSON |
| **Performance** | Higher throughput | Lower throughput |
| **Connection** | Persistent, multiplexed | Per-request or keep-alive |
| **Compatibility** | Requires gRPC support | Works through any HTTP proxy |
| **Browser** | Not supported | Supported (for frontend) |

**Choose gRPC when**:
- High throughput requirements
- Internal service-to-collector communication
- Network supports HTTP/2

**Choose HTTP when**:
- Behind load balancer/proxy that doesn't support gRPC
- Browser-based instrumentation (RUM)
- Debugging (can inspect with standard tools)
- Serverless environments (cold start overhead)
</details>

## Hands-On Exercise: End-to-End Observability

Deploy OTel Collector and instrument an application:

### Setup

```bash
# Create namespace
kubectl create namespace observability

# Deploy OTel Collector
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: observability
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
      batch:
        timeout: 1s
      memory_limiter:
        check_interval: 1s
        limit_mib: 512

    exporters:
      logging:
        verbosity: detailed
      prometheus:
        endpoint: 0.0.0.0:8889

    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [logging]
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [prometheus]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: observability
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
          image: otel/opentelemetry-collector-contrib:latest
          args: ["--config=/etc/otel/config.yaml"]
          ports:
            - containerPort: 4317
            - containerPort: 4318
            - containerPort: 8889
          volumeMounts:
            - name: config
              mountPath: /etc/otel
      volumes:
        - name: config
          configMap:
            name: otel-collector-config
---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
  namespace: observability
spec:
  selector:
    app: otel-collector
  ports:
    - name: otlp-grpc
      port: 4317
    - name: otlp-http
      port: 4318
    - name: prometheus
      port: 8889
EOF
```

### Step 1: Create Instrumented App

```python
# app.py
from flask import Flask, request
import time
import random

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Configure resource
resource = Resource.create({
    "service.name": "demo-app",
    "service.version": "1.0.0",
})

# Configure tracing
trace_provider = TracerProvider(resource=resource)
trace_exporter = OTLPSpanExporter(endpoint="otel-collector.observability:4317", insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)

# Configure metrics
metric_exporter = OTLPMetricExporter(endpoint="otel-collector.observability:4317", insecure=True)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)

# Create instruments
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter("http_requests_total")

# Create Flask app
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def hello():
    request_counter.add(1, {"path": "/", "method": "GET"})
    return "Hello, OTel!"

@app.route("/slow")
def slow():
    with tracer.start_as_current_span("slow_operation") as span:
        delay = random.uniform(0.5, 2.0)
        span.set_attribute("delay", delay)
        time.sleep(delay)
    request_counter.add(1, {"path": "/slow", "method": "GET"})
    return f"Slept for {delay:.2f}s"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Step 2: Deploy App

```yaml
# demo-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
  namespace: observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo-app
  template:
    metadata:
      labels:
        app: demo-app
    spec:
      containers:
        - name: app
          image: python:3.10
          command: ["python", "-u", "/app/app.py"]
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: app-code
              mountPath: /app
          env:
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://otel-collector:4317"
      volumes:
        - name: app-code
          configMap:
            name: demo-app-code
```

### Step 3: Verify Telemetry

```bash
# Check collector logs for traces
kubectl logs -n observability -l app=otel-collector -f

# Port-forward to Prometheus endpoint
kubectl port-forward -n observability svc/otel-collector 8889:8889

# Query metrics
curl localhost:8889/metrics | grep http_requests
```

### Success Criteria

You've completed this exercise when you can:
- [ ] Deploy OTel Collector with OTLP receiver
- [ ] See traces in collector logs
- [ ] Query metrics from Prometheus endpoint
- [ ] Understand the trace → span relationship

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **Vendor neutrality**: OTel instrumentation works with any backend—change exporters, not code
- [ ] **Three signals unified**: Traces, metrics, and logs share common attributes and context
- [ ] **Collector architecture**: Receivers → Processors → Exporters in configurable pipelines
- [ ] **Auto-instrumentation**: Java agents, Python wrappers, K8s operator inject spans with zero code changes
- [ ] **Manual instrumentation**: Use for business-critical paths and custom attributes
- [ ] **Context propagation**: W3C `traceparent` header carries TraceID/SpanID across service boundaries
- [ ] **OTLP protocol**: Native OTel format; use gRPC for throughput, HTTP for compatibility
- [ ] **Memory limiter**: Essential processor to prevent Collector OOM
- [ ] **Sampling strategies**: Head-based (simple, probabilistic) vs. tail-based (smart, memory-intensive)
- [ ] **Resource attributes**: `service.name`, `service.version`, `deployment.environment` identify telemetry sources

## Further Reading

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/) — Official docs
- [OTel Collector Contrib](https://github.com/open-telemetry/opentelemetry-collector-contrib) — Additional components
- [OTel Demo App](https://github.com/open-telemetry/opentelemetry-demo) — Full reference architecture
- [Practical OpenTelemetry](https://www.honeycomb.io/opentelemetry) — Honeycomb's guide

## Summary

OpenTelemetry is the future of observability instrumentation. Its vendor-neutral approach, comprehensive language support, and powerful Collector make it the standard for cloud-native applications. Auto-instrumentation provides immediate value, while manual instrumentation adds business context. The Collector centralizes processing and enables flexible routing to any backend.

---

## Next Module

Continue to [Module 1.3: Grafana](module-1.3-grafana/) to learn about visualization and dashboards for your telemetry.

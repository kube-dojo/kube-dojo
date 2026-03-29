---
title: "Module 1.1: OTel API & SDK Deep Dive"
slug: k8s/otca/module-1.1-otel-sdk-deep-dive
sidebar:
  order: 2
---
> **Complexity**: `[COMPLEX]` - Core domain, 46% of OTCA exam weight
>
> **Time to Complete**: 90-120 minutes
>
> **Prerequisites**: Basic familiarity with distributed systems, HTTP, and at least one programming language (Python or Go)

---

## Why This Module Matters

A team at a mid-size fintech company had Jaeger deployed, Prometheus scraping, and Fluentd shipping logs. Three separate instrumentation libraries, three configuration surfaces, three vendor lock-in vectors. When they needed to switch from Jaeger to Grafana Tempo, it took six weeks to re-instrument 40 services. Then OpenTelemetry arrived, and the next migration — Tempo to an OTLP-native backend — took an afternoon. One SDK, one wire protocol, swap the exporter.

That is the entire point of OpenTelemetry: **decouple instrumentation from backends**. Domain 2 of the OTCA exam (46% of your score) tests whether you understand the machinery that makes this possible — the Provider/Processor/Exporter pipelines for traces, metrics, and logs.

Get this module right and you have nearly half the exam locked down.

---

## Did You Know?

- **OpenTelemetry is the second most active CNCF project** after Kubernetes itself, with 1,000+ contributors across 11 language SIGs.
- **The OTel Collector is optional.** The SDK can export directly to backends. The Collector adds routing, batching, and multi-backend fan-out, but it is a deployment choice, not a requirement.
- **Semantic conventions took years to stabilize.** The rename from `http.method` to `http.request.method` (v1.23+) broke dashboards everywhere — which is why the exam tests whether you know the *current* stable names.
- **Zero-code instrumentation in Java modifies bytecode at load time.** The Java agent uses `java.lang.instrument` and byte-buddy to rewrite class files before the JVM executes them — no source changes needed.

---

## Part 1: The Three Pillars — Provider Pipelines

Every signal in OTel follows the same pattern: **Provider → Processor/Reader → Exporter**. Understand one and you understand all three.

### 1.1 TracerProvider Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                        TracerProvider                             │
│                                                                  │
│  Resource: { service.name="cart-svc", deployment.env="prod" }    │
│                                                                  │
│  ┌────────┐    ┌──────────────────┐    ┌──────────────────────┐  │
│  │ Tracer │───▶│  SpanProcessor   │───▶│    SpanExporter      │  │
│  │        │    │                  │    │                      │  │
│  │ start  │    │ SimpleProcessor  │    │  OTLPSpanExporter    │  │
│  │ span() │    │   (sync, dev)    │    │  ConsoleSpanExporter │  │
│  │        │    │                  │    │  JaegerExporter      │  │
│  │ end    │    │ BatchProcessor   │    │  ZipkinExporter      │  │
│  │ span() │    │   (async, prod)  │    │                      │  │
│  └────────┘    └──────────────────┘    └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**SpanProcessor** — controls *when* spans are handed to the exporter:

| Processor | Behavior | Use Case |
|-----------|----------|----------|
| `SimpleSpanProcessor` | Exports each span immediately, synchronously | Local dev, debugging |
| `BatchSpanProcessor` | Buffers spans, exports in batches on a timer | **Production** (always) |

`BatchSpanProcessor` tuning knobs (and their env vars):

| Parameter | Env Var | Default | What It Does |
|-----------|---------|---------|--------------|
| `maxQueueSize` | `OTEL_BSP_MAX_QUEUE_SIZE` | 2048 | Buffer capacity before dropping |
| `scheduledDelayMillis` | `OTEL_BSP_SCHEDULE_DELAY` | 5000 | Flush interval in ms |
| `maxExportBatchSize` | `OTEL_BSP_MAX_EXPORT_BATCH_SIZE` | 512 | Spans per export call |

**SpanExporter** — controls *where* spans go:

| Exporter | Protocol | Notes |
|----------|----------|-------|
| OTLP (gRPC) | `grpc` on port 4317 | **Default, preferred** |
| OTLP (HTTP) | `http/protobuf` on port 4318 | Firewall-friendly |
| Console | stdout | Debugging only |
| Jaeger | Thrift/gRPC | Legacy — use OTLP instead |
| Zipkin | HTTP/JSON | Legacy — use OTLP instead |

> **Exam tip**: OTLP is the only exporter the spec mandates SDKs implement. Jaeger and Zipkin exporters are community add-ons.

### 1.2 MeterProvider Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                        MeterProvider                             │
│                                                                  │
│  Resource: { service.name="cart-svc" }                           │
│                                                                  │
│  ┌────────┐    ┌──────────────────┐    ┌──────────────────────┐  │
│  │ Meter  │───▶│   MetricReader   │───▶│   MetricExporter     │  │
│  │        │    │                  │    │                      │  │
│  │counter │    │ PeriodicReader   │    │  OTLPMetricExporter  │  │
│  │histo   │    │  (push, 60s)     │    │  ConsoleExporter     │  │
│  │gauge   │    │                  │    │                      │  │
│  │        │    │ PrometheusReader │    │  (pull: /metrics)    │  │
│  └────────┘    └──────────────────┘    └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**MetricReader** — controls *how* metric data is collected:

| Reader | Model | Use Case |
|--------|-------|----------|
| `PeriodicExportingMetricReader` | Push (exports on interval) | OTLP backends, Collector |
| `PrometheusMetricReader` | Pull (exposes `/metrics`) | Prometheus scrape targets |

### 1.3 LoggerProvider Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                       LoggerProvider                             │
│                                                                  │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │ Log Bridge   │───▶│  LogProcessor    │───▶│  LogExporter   │  │
│  │              │    │                  │    │                │  │
│  │ Python       │    │ SimpleProcessor  │    │  OTLP          │  │
│  │  stdlib      │    │ BatchProcessor   │    │  Console       │  │
│  │ Java Log4j   │    │                  │    │                │  │
│  │ .NET ILogger │    │                  │    │                │  │
│  └──────────────┘    └──────────────────┘    └────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Key concept**: OTel does NOT replace your logging library. A **log bridge** connects existing loggers (Python `logging`, Java Log4j/SLF4J) to the OTel pipeline. You keep writing `logger.info("order placed")` — the bridge enriches log records with trace context and routes them through the OTel exporter.

### 1.4 Signal Maturity — Know This for the Exam

| Signal | Spec Status | SDK Status | Notes |
|--------|-------------|------------|-------|
| Traces | **Stable** | Stable in all major languages | Safe for production |
| Metrics | **Stable** | Stable in most languages | GA since 2023 |
| Logs | **Stable** (data model) | Mixed (bridge APIs vary) | Bridges are the integration point |
| Baggage | **Stable** | Stable | Propagation mechanism |
| Profiling | **Experimental** | Early development | Not on exam yet |

---

## Part 2: Span Anatomy

A span is not just "a timer with a name." The exam expects you to know every field.

### 2.1 Span Structure

```
Span {
  trace_id:     "abc123..."          ← 16-byte, shared across all spans in trace
  span_id:      "def456..."          ← 8-byte, unique to this span
  parent_id:    "789abc..."          ← links to parent span (or empty for root)
  name:         "GET /api/cart"      ← operation name
  kind:         SERVER               ← see below
  start_time:   1711234567.123       ← nanosecond precision
  end_time:     1711234567.456
  status:       { code: OK }         ← Unset, Ok, Error
  attributes:   { "http.request.method": "GET", "http.response.status_code": 200 }
  events:       [ { name: "cache.miss", timestamp: ... } ]
  links:        [ { trace_id: "other_trace", span_id: "other_span" } ]
  resource:     { "service.name": "cart-svc", "host.name": "node-1" }
}
```

### 2.2 Span Kinds

| Kind | Who Creates It | Example |
|------|---------------|---------|
| `INTERNAL` | Default, in-process operations | Business logic, helper functions |
| `SERVER` | The service **receiving** a request | HTTP handler, gRPC server method |
| `CLIENT` | The service **making** a request | HTTP client call, DB query |
| `PRODUCER` | Enqueuing a message (async) | Kafka producer, SQS send |
| `CONSUMER` | Processing a queued message | Kafka consumer, SQS handler |

> **Exam trap**: A span for "calling the database" is `CLIENT`, not `INTERNAL`. The span kind describes the role in the communication, not whether it is "internal to your code."

### 2.3 Attributes vs Resources

This distinction trips people up constantly.

| | Attributes | Resources |
|-|-----------|-----------|
| **Scope** | Per-span (or per-metric data point) | Per-Provider (applies to ALL telemetry) |
| **Set when** | During span/metric creation | At SDK initialization |
| **Example** | `http.request.method=GET` | `service.name=cart-svc` |
| **Changes** | Different per operation | Same for entire process lifetime |

### 2.4 Events and Exceptions

**Events** are timestamped annotations within a span. The most common use is recording exceptions:

```python
from opentelemetry import trace

span = trace.get_current_span()
try:
    process_order(order_id)
except Exception as e:
    span.set_status(trace.StatusCode.ERROR, str(e))
    span.record_exception(e)  # adds an event with exception.type, exception.message, exception.stacktrace
    raise
```

`record_exception` is syntactic sugar — it creates an event named `exception` with attributes from semantic conventions.

### 2.5 Span Links

Links connect spans across **separate** traces. Unlike parent-child (which is within one trace), links say "this span is related to that other span."

Use cases:
- A batch job that processes items from multiple incoming requests
- Fan-in: a span that aggregates results from several independent traces
- Retries where each attempt creates a new trace

---

## Part 3: Metric Instruments

### 3.1 Sync vs Async Instruments

**Synchronous** instruments are called inline with your code — you call `.add()` or `.record()` at the point of measurement.

**Asynchronous** (observable) instruments register a callback. The SDK calls your function at collection time to read the current value.

| Instrument | Sync/Async | Monotonic? | Example |
|-----------|-----------|-----------|---------|
| **Counter** | Sync | Yes (only increases) | `requests_total`, `bytes_sent` |
| **UpDownCounter** | Sync | No (increases and decreases) | `active_connections`, `queue_depth` |
| **Histogram** | Sync | N/A (records distributions) | `request_duration_ms`, `response_size` |
| **Observable Counter** | Async | Yes | CPU time (read from `/proc`) |
| **Observable UpDownCounter** | Async | No | Current memory usage |
| **Observable Gauge** | Async | No (point-in-time value) | Temperature, current CPU % |

> **When to use async**: When the value already exists somewhere (OS counter, connection pool stats) and you just want to observe it at collection time. Do NOT poll in a loop — let the SDK invoke your callback.

### 3.2 Metric Temporality

This is one of the most tested concepts in Domain 2.

| Temporality | What It Reports | Who Prefers It |
|-------------|----------------|---------------|
| **Cumulative** | Total since process start (e.g., counter = 1042) | Prometheus, OTLP default for counters |
| **Delta** | Change since last collection (e.g., counter += 17) | StatsD, some commercial backends |

**Why it matters**: If your exporter expects delta but the SDK sends cumulative, you get nonsense numbers. The SDK's `MetricReader` determines temporality preference.

```
Cumulative:  |---100---|---250---|---430---|  (running total)
Delta:       |---100---|---150---|---180---|  (per-interval change)
```

### 3.3 Aggregation

The SDK aggregates raw measurements before export:

| Instrument | Default Aggregation |
|-----------|-------------------|
| Counter | Sum |
| Histogram | Explicit Bucket Histogram |
| Gauge | Last Value |

### 3.4 Exemplars — Linking Metrics to Traces

Exemplars attach a `trace_id` and `span_id` to a metric data point. When you see a latency spike on a dashboard, exemplars let you click through to the exact trace that caused it.

```
histogram bucket [200ms-500ms]: count=47, exemplar={trace_id="abc123", value=423ms}
```

Exemplars are configured on the SDK level and typically sampled (not every data point gets one).

---

## Part 4: Context Propagation

### 4.1 How Context Crosses Service Boundaries

```
  Service A                          Service B
┌──────────────┐   HTTP Request    ┌──────────────┐
│              │                   │              │
│  span-A      │   headers:        │  span-B      │
│  trace=abc   │──────────────────▶│  trace=abc   │
│              │   traceparent:    │  parent=A    │
│              │   00-abc...-A..   │              │
└──────────────┘                   └──────────────┘
```

The SDK uses **propagators** to inject context into carriers (HTTP headers, message attributes) and extract it on the receiving side.

### 4.2 W3C TraceContext (Default)

The `traceparent` header:
```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              ^^  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^  ^^
           version          trace-id                   span-id     flags
                                                                  (sampled)
```

The `tracestate` header carries vendor-specific data (e.g., sampling decisions for a particular backend).

### 4.3 Baggage

Baggage propagates **arbitrary key-value pairs** across service boundaries. Unlike trace context (which carries IDs), baggage carries business data.

```python
from opentelemetry import baggage, context

ctx = baggage.set_baggage("user.tier", "premium")
# attach ctx — now all downstream services can read user.tier
```

**Warning**: Baggage is sent in headers to every downstream service. Do NOT put sensitive data (PII, tokens) in baggage. It is visible on the wire.

---

## Part 5: SDK Configuration

### 5.1 Environment Variables (Exam Favorites)

| Variable | Purpose | Example |
|----------|---------|---------|
| `OTEL_SERVICE_NAME` | Sets `service.name` resource attribute | `cart-service` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Base URL for all OTLP signals | `http://collector:4317` |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Wire protocol | `grpc`, `http/protobuf` |
| `OTEL_EXPORTER_OTLP_HEADERS` | Auth headers | `api-key=secret123` |
| `OTEL_TRACES_EXPORTER` | Trace exporter type | `otlp`, `console`, `none` |
| `OTEL_METRICS_EXPORTER` | Metric exporter type | `otlp`, `prometheus`, `none` |
| `OTEL_LOGS_EXPORTER` | Log exporter type | `otlp`, `console`, `none` |
| `OTEL_TRACES_SAMPLER` | Sampling strategy | `always_on`, `traceidratio` |
| `OTEL_TRACES_SAMPLER_ARG` | Sampler parameter | `0.1` (10% sampling) |
| `OTEL_RESOURCE_ATTRIBUTES` | Additional resource attrs | `deployment.env=prod,service.version=2.1` |

> **Exam tip**: Env vars take lowest precedence. Programmatic config overrides env vars. Signal-specific env vars (e.g., `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`) override the general one (`OTEL_EXPORTER_OTLP_ENDPOINT`).

### 5.2 Semantic Conventions (Stable Naming Standards)

The exam tests whether you know the correct attribute names. These are the most common:

| Convention | Attribute | Example Value |
|-----------|-----------|---------------|
| HTTP | `http.request.method` | `GET` |
| HTTP | `http.response.status_code` | `200` |
| HTTP | `url.full` | `https://api.example.com/cart` |
| Service | `service.name` | `cart-service` |
| Service | `service.version` | `1.4.2` |
| Database | `db.system` | `postgresql` |
| Database | `db.statement` | `SELECT * FROM orders` |
| Messaging | `messaging.system` | `kafka` |
| Messaging | `messaging.operation` | `publish` |

> **Watch out**: The old convention `http.method` was renamed to `http.request.method`. The exam uses the current stable names from semconv v1.23+.

---

## Part 6: Zero-Code Instrumentation

Zero-code (auto) instrumentation wraps library calls without changing your source.

### 6.1 How It Works

| Language | Mechanism | Command |
|----------|-----------|---------|
| **Java** | Bytecode manipulation via `java.lang.instrument` agent | `java -javaagent:opentelemetry-javaagent.jar -jar myapp.jar` |
| **Python** | Monkey-patching libraries at import time | `opentelemetry-instrument python myapp.py` |
| **.NET** | CLR profiler API and startup hooks | Via env vars: `CORECLR_ENABLE_PROFILING=1` |
| **Node.js** | Require hooks / module patching | `node --require @opentelemetry/auto-instrumentations-node myapp.js` |

### 6.2 What Gets Instrumented Automatically

Auto-instrumentation covers **libraries**, not **business logic**:

- HTTP servers and clients (Flask, requests, net/http)
- Database drivers (psycopg2, JDBC, database/sql)
- Messaging (Kafka clients, RabbitMQ)
- gRPC

You still need **manual instrumentation** for:
- Custom business spans ("process-order", "validate-cart")
- Custom metrics (order value, queue depth)
- Adding attributes specific to your domain

---

## Part 7: Code Examples

### 7.1 Python — Manual Tracing with TracerProvider

```python
# trace_example.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

# 1. Create a Resource (identifies this service)
resource = Resource.create({"service.name": "order-service", "service.version": "1.0.0"})

# 2. Build the pipeline: Provider → Processor → Exporter
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)

# 3. Register globally
trace.set_tracer_provider(provider)

# 4. Get a tracer (scoped by instrumentation library name + version)
tracer = trace.get_tracer("order.instrumentation", "0.1.0")

# 5. Create spans
with tracer.start_as_current_span("process-order", kind=trace.SpanKind.INTERNAL) as span:
    span.set_attribute("order.id", "ORD-12345")
    span.set_attribute("order.item_count", 3)

    with tracer.start_as_current_span("validate-payment", kind=trace.SpanKind.CLIENT) as child:
        child.set_attribute("payment.provider", "stripe")
        # ... call payment API
        child.set_status(trace.StatusCode.OK)

    span.add_event("order.confirmed", {"order.total": 59.99})

# 6. Flush before exit
provider.shutdown()
```

### 7.2 Python — Custom Metric Instruments

```python
# metrics_example.py
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource

resource = Resource.create({"service.name": "order-service"})
reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=5000)
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("order.instrumentation", "0.1.0")

# Sync Counter — total orders placed (only goes up)
order_counter = meter.create_counter("orders.placed", unit="1", description="Total orders placed")

# Sync Histogram — order processing duration
duration_hist = meter.create_histogram("orders.duration", unit="ms", description="Order processing time")

# Sync UpDownCounter — items currently in carts
cart_items = meter.create_up_down_counter("cart.items", unit="1", description="Active cart items")

# Async Gauge — current queue depth (observed, not recorded)
def read_queue_depth(options):
    depth = get_queue_depth()  # your function that reads the real value
    options.observe(depth, {"queue.name": "orders"})

meter.create_observable_gauge("queue.depth", callbacks=[read_queue_depth])

# Usage
order_counter.add(1, {"order.type": "standard"})
duration_hist.record(142.5, {"order.type": "standard"})
cart_items.add(3, {"user.id": "u-123"})   # customer adds 3 items
cart_items.add(-1, {"user.id": "u-123"})  # customer removes 1 item
```

### 7.3 Go — Manual Tracing with Context Propagation

```go
package main

import (
    "context"
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/propagation"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    "go.opentelemetry.io/otel/sdk/resource"
    semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
    "go.opentelemetry.io/otel/trace"
    "go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
)

func initTracer() *sdktrace.TracerProvider {
    exporter, _ := stdouttrace.New(stdouttrace.WithPrettyPrint())
    res, _ := resource.New(context.Background(),
        resource.WithAttributes(semconv.ServiceName("order-service")),
    )
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(res),
    )
    otel.SetTracerProvider(tp)
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{}, propagation.Baggage{},
    ))
    return tp
}

func handleOrder(w http.ResponseWriter, r *http.Request) {
    // Extract incoming context from headers (continues the trace from upstream)
    ctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))
    tracer := otel.Tracer("order.instrumentation")

    ctx, span := tracer.Start(ctx, "handle-order", trace.WithSpanKind(trace.SpanKindServer))
    defer span.End()
    span.SetAttributes(attribute.String("order.id", "ORD-12345"))

    callPaymentService(ctx)
}

func callPaymentService(ctx context.Context) {
    tracer := otel.Tracer("order.instrumentation")
    ctx, span := tracer.Start(ctx, "call-payment", trace.WithSpanKind(trace.SpanKindClient))
    defer span.End()

    // Inject context into outgoing request — payment-svc continues the trace
    req, _ := http.NewRequestWithContext(ctx, "POST", "http://payment-svc/charge", nil)
    otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))
    http.DefaultClient.Do(req)
}
```

### 7.4 Go — Custom Metrics

```go
func recordMetrics() {
    meter := otel.Meter("order.instrumentation")

    orderCounter, _ := meter.Int64Counter("orders.placed",
        metric.WithUnit("1"), metric.WithDescription("Total orders placed"))

    durationHist, _ := meter.Float64Histogram("orders.duration",
        metric.WithUnit("ms"), metric.WithDescription("Order processing time"))

    // Async Gauge — SDK calls this callback at collection time
    meter.Float64ObservableGauge("queue.depth",
        metric.WithFloat64Callback(func(_ context.Context, o metric.Float64Observer) error {
            o.Observe(42.0, metric.WithAttributes(attribute.String("queue.name", "orders")))
            return nil
        }),
    )

    ctx := context.Background()
    orderCounter.Add(ctx, 1, metric.WithAttributes(attribute.String("order.type", "standard")))
    durationHist.Record(ctx, 142.5, metric.WithAttributes(attribute.String("order.type", "standard")))
}
```

---

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|---------------|-----|
| Using `SimpleSpanProcessor` in production | Exports synchronously on the hot path, adds latency | Always use `BatchSpanProcessor` in prod |
| Setting `service.name` as a span attribute | It's a **resource** attribute, not per-span | Set it on the `Resource` passed to the Provider |
| Using `INTERNAL` kind for outgoing HTTP calls | Misrepresents the span's role in the trace | Use `CLIENT` for outgoing requests, `SERVER` for incoming |
| Putting PII in Baggage | Baggage is propagated in cleartext HTTP headers | Only put non-sensitive routing/context data in Baggage |
| Confusing cumulative and delta temporality | Backends interpret the numbers differently | Match temporality to your backend's expectation |
| Calling `record_exception` without setting Error status | Exception is logged as event but span shows OK | Always call `set_status(ERROR)` alongside `record_exception` |
| Using deprecated `http.method` attribute name | Old semconv, will fail exam questions | Use `http.request.method` (semconv v1.23+) |
| Creating a new TracerProvider per request | Massive overhead, breaks batching | Create ONE provider at startup, share it globally |

---

## Quiz

Test yourself — these mirror OTCA exam style questions.

<details>
<summary><strong>Q1: Which SpanProcessor should you use in production and why?</strong></summary>

**BatchSpanProcessor**. It buffers spans and exports them asynchronously in batches, avoiding the latency overhead of synchronous per-span exports that `SimpleSpanProcessor` introduces.
</details>

<details>
<summary><strong>Q2: A service receives an HTTP request and then calls a database. What span kinds are correct for (a) the HTTP handler span and (b) the database call span?</strong></summary>

(a) `SERVER` — the service is receiving an inbound request.
(b) `CLIENT` — the service is making an outbound call to the database.
</details>

<details>
<summary><strong>Q3: What is the difference between span attributes and resources?</strong></summary>

**Resources** are set once at SDK initialization and apply to ALL telemetry from that provider (e.g., `service.name`, `host.name`). **Attributes** are per-span (or per-metric data point) and describe the specific operation (e.g., `http.request.method`, `db.statement`).
</details>

<details>
<summary><strong>Q4: You set OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317 and OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://traces-collector:4317. Which endpoint do traces go to?</strong></summary>

`http://traces-collector:4317`. Signal-specific env vars override the general `OTEL_EXPORTER_OTLP_ENDPOINT`.
</details>

<details>
<summary><strong>Q5: Name three differences between a Counter and a Histogram instrument.</strong></summary>

1. Counter records **monotonically increasing sums** (e.g., total requests); Histogram records **distributions** of values (e.g., latency).
2. Counter uses `.add()`; Histogram uses `.record()`.
3. Counter aggregates to a **Sum**; Histogram aggregates to **bucket counts, sum, min, max**.
</details>

<details>
<summary><strong>Q6: What does a log bridge do, and why doesn't OTel replace existing logging libraries?</strong></summary>

A log bridge connects existing language-native loggers (Python `logging`, Java Log4j) to the OTel LoggerProvider pipeline. OTel does not replace loggers because applications already have extensive logging — the bridge enriches existing logs with trace context and routes them to OTel exporters without requiring code changes.
</details>

<details>
<summary><strong>Q7: Explain cumulative vs delta temporality for a Counter that receives: +10, +20, +5 over three collection intervals.</strong></summary>

**Cumulative** reports the running total: 10, 30, 35.
**Delta** reports the per-interval change: 10, 20, 5.
</details>

<details>
<summary><strong>Q8: What header does W3C TraceContext use for propagation, and what are its four fields?</strong></summary>

The `traceparent` header. Its four fields are: **version** (2 hex chars, currently `00`), **trace-id** (32 hex chars), **parent-id/span-id** (16 hex chars), and **trace-flags** (2 hex chars, `01` = sampled).
</details>

<details>
<summary><strong>Q9: A Java application needs OpenTelemetry instrumentation but the team cannot modify source code. What approach should they use?</strong></summary>

Use the **OpenTelemetry Java agent** (`-javaagent:opentelemetry-javaagent.jar`). It uses bytecode manipulation at class load time to automatically instrument supported libraries (HTTP, gRPC, JDBC, etc.) without any source code changes.
</details>

<details>
<summary><strong>Q10: What are exemplars and when would you use them?</strong></summary>

Exemplars are sample `trace_id`/`span_id` references attached to metric data points. They link metrics to traces — when you see a latency spike in a histogram bucket on your dashboard, exemplars let you jump directly to a representative trace that contributed to that bucket.
</details>

---

## Hands-On Exercise: Build an Instrumented Python Service

**Goal**: Wire up a complete OTel pipeline with traces and metrics, then verify the output.

### Setup

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
```

### Task

1. Create a Python script that initializes a `TracerProvider` with a `BatchSpanProcessor` and `ConsoleSpanExporter`.
2. Create a `MeterProvider` with a `PeriodicExportingMetricReader` (5-second interval) and `ConsoleMetricExporter`.
3. Set the resource to `service.name=exercise-svc`.
4. Create a parent span called `handle-request` with kind `SERVER`.
5. Inside it, create a child span `call-database` with kind `CLIENT` and attribute `db.system=postgresql`.
6. Record a counter increment for `requests.total` with attribute `http.request.method=GET`.
7. Record a histogram observation for `request.duration` with value 142.5 ms.
8. In the child span, simulate an exception: call `record_exception` and set status to `ERROR`.
9. Flush and verify you see both spans and metrics in console output.

### Success Criteria

- [ ] Console output shows two spans with correct parent-child relationship (same `trace_id`, child's `parent_id` matches parent's `span_id`)
- [ ] Parent span kind is `SPAN_KIND_SERVER`, child is `SPAN_KIND_CLIENT`
- [ ] Child span has status `ERROR` and an `exception` event
- [ ] Metrics output shows `requests.total` counter and `request.duration` histogram
- [ ] Resource on all telemetry shows `service.name=exercise-svc`

---

## Key Takeaways

1. **All three signals follow the same pattern**: Provider → Processor/Reader → Exporter. Learn one, understand all.
2. **BatchSpanProcessor for production, always.** SimpleSpanProcessor is for debugging only.
3. **Resources describe the service, attributes describe the operation.** Never put `service.name` on a span attribute.
4. **Span kind describes the communication role**, not whether code is "internal." Outgoing calls are CLIENT.
5. **OTLP is the standard export protocol.** Jaeger and Zipkin exporters exist but OTLP is preferred and spec-mandated.
6. **Env vars configure everything** but programmatic config wins. Signal-specific vars override general ones.
7. **Auto-instrumentation covers libraries, not business logic.** You still need manual spans for domain-specific operations.
8. **Cumulative vs delta temporality must match your backend.** Getting this wrong produces garbage data.

---

**Next Module**: [Module 2: OTel Collector Architecture](../module-1.2-otel-collector-advanced/) — how to receive, process, and export telemetry at scale.

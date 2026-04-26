---
title: "Module 1.2: OpenTelemetry"
slug: platform/toolkits/observability-intelligence/observability/module-1.2-opentelemetry
sidebar:
  order: 3
---

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 60-75 min

## Prerequisites

Before starting this module, you should be comfortable reading service logs, reasoning about HTTP request flows, and interpreting basic Prometheus metrics. You do not need to be an OpenTelemetry expert yet, but you should already understand why distributed systems need more than single-process logging.

Complete these first:

- [Module 1.1: Prometheus](../module-1.1-prometheus/)
- [Observability Theory Track](/platform/foundations/observability-theory/)
- Basic understanding of distributed tracing concepts such as traces, spans, and parent-child relationships
- Basic Kubernetes skills with `kubectl`; this module uses `k` as a shorthand alias after the first command

## Learning Outcomes

After completing this module, you will be able to:

- **Design** an OpenTelemetry signal flow that routes traces, metrics, and logs through a Collector without locking applications to one backend.
- **Implement** automatic and manual instrumentation choices for services, then justify where each approach fits.
- **Debug** broken traces by inspecting resource attributes, propagation headers, Collector pipelines, and backend export behavior.
- **Evaluate** head sampling, tail sampling, filtering, and batching trade-offs for cost, reliability, and incident usefulness.
- **Operate** an OpenTelemetry Collector in Kubernetes with memory limits, health checks, and verification steps that expose configuration mistakes.

## Why This Module Matters

A platform team at a large European bank inherited a payment system with more than four hundred services and three separate tracing stacks. Legacy workloads emitted Zipkin spans, newer Java services sent data to Jaeger, and a Python rewrite had vendor-specific DataDog instrumentation baked into business code. When a card authorization crossed all three generations, the trace did not show a failed payment journey; it showed three disconnected fragments that each team interpreted differently.

The problem became urgent when an audit required end-to-end transaction tracing for regulated payment flows. The expensive answer was to migrate every service to one commercial agent, rewrite old instrumentation, and accept a long period where observability would be worse before it became better. The platform architect chose a different route: put OpenTelemetry between the applications and the backends, let existing signals enter through compatible receivers, normalize the data in one Collector layer, and export to a single tracing backend while teams gradually cleaned up code.

That decision mattered because it changed the migration from an application rewrite into an infrastructure rollout. The teams could prove the payment path first, then improve service instrumentation one workload at a time. OpenTelemetry did not magically fix missing spans, bad service names, or sampling mistakes, but it gave the platform a standard vocabulary and a neutral transport. That is the skill you are building in this module: not memorizing OpenTelemetry terms, but designing and debugging a telemetry path that survives real production constraints.

## Core Content

### 1. The Problem OpenTelemetry Solves

OpenTelemetry is the instrumentation and telemetry transport standard for modern observability. It gives application teams a common API and SDK for creating telemetry, a protocol called OTLP for moving it, and a Collector for receiving, processing, and exporting it. The practical result is that your application code can describe what happened without caring whether the backend is Jaeger, Tempo, Prometheus, Loki, Honeycomb, Datadog, New Relic, or another system.

The important word is standard, not tool. OpenTelemetry is not a full observability backend by itself. It does not replace dashboards, long-term storage, alerting rules, or incident workflows. Instead, it sits at the boundary where applications produce telemetry and platforms decide where that telemetry should go. This boundary is where vendor lock-in usually grows, so standardizing it gives the platform team leverage.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         OPENTELEMETRY SIGNAL PATH                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Application Code                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Business operation: "create order", "charge card", "ship item"          │  │
│  │                                                                        │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐               │  │
│  │  │    Traces    │   │   Metrics    │   │     Logs     │               │  │
│  │  │ span trees   │   │ measurements │   │ event lines  │               │  │
│  │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘               │  │
│  │         │                  │                  │                       │  │
│  │         └──────────────────┼──────────────────┘                       │  │
│  │                            ▼                                          │  │
│  │              OpenTelemetry API and SDK                                │  │
│  └────────────────────────────┬──────────────────────────────────────────┘  │
│                               │ OTLP gRPC or OTLP HTTP                      │
│                               ▼                                              │
│  Collector Layer                                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Receivers ─────────▶ Processors ─────────▶ Exporters                   │  │
│  │ otlp, jaeger, zipkin   batch, filter, memory   otlp, prometheus, debug │  │
│  └────────────────────────────┬──────────────────────────────────────────┘  │
│                               │                                              │
│                               ▼                                              │
│  Backends: tracing store, metrics store, log store, commercial APM, archive  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

A service can emit telemetry directly to a backend, but that choice pushes platform concerns into every workload. When you need to add a second backend, filter noisy spans, change sampling policy, or buffer during an outage, every service becomes part of the migration. The Collector moves those concerns into infrastructure where platform teams can operate them consistently.

| Component | What It Does | Design Question |
|---|---|---|
| API | Defines vendor-neutral calls used by instrumentation libraries and application code | Can developers create telemetry without importing backend-specific packages? |
| SDK | Implements batching, sampling, resource metadata, and export behavior inside the process | What work should happen in the application before data leaves the process? |
| OTLP | Carries traces, metrics, and logs over gRPC or HTTP | Which transport fits the network path between workloads and collectors? |
| Collector | Receives, processes, and exports telemetry outside the application | What should be centralized so teams do not repeat it in every service? |
| Semantic conventions | Standardize attribute names for common operations | Will dashboards and queries work across services written by different teams? |

**Stop and think:** If your organization changed tracing vendors next quarter, which parts of your current applications would need code changes? Separate the answer into instrumentation code, runtime configuration, Collector configuration, and backend dashboard work. The more work you find inside application repositories, the more value a vendor-neutral instrumentation layer can provide.

OpenTelemetry also helps with correlation. A trace explains how one request moved through services. Metrics explain aggregate behavior such as request rate, error rate, and latency distribution. Logs explain individual events with detailed context. When these signals share resource attributes and trace identifiers, an engineer can move from an alert to a metric, from the metric to an exemplar, from the exemplar to a trace, and from the trace to logs for the failing span.

```text
TRACES                         METRICS                         LOGS
──────────────────────────────────────────────────────────────────────────────
Span tree for one request       Aggregated measurements          Timestamped events
│                               │                                │
├─ trace_id                     ├─ counter                       ├─ severity
├─ span_id                      ├─ gauge                         ├─ body
├─ parent_span_id               ├─ histogram                     ├─ attributes
├─ attributes                   ├─ resource attributes           ├─ trace_id
├─ events                       └─ exemplars to traces           └─ span_id
└─ status

Shared correlation keys: service.name, deployment.environment, trace_id, span_id
```

A mature platform treats these signals as connected evidence, not separate products. If `checkout-service` latency spikes, a metric should show the spike, a trace should identify whether the delay is payment, inventory, or shipping, and logs should show the local details around the span that failed. OpenTelemetry gives you the shared identifiers and transport needed to make that investigation possible.

### 2. Instrumentation Strategy: Automatic First, Manual Where It Matters

Instrumentation is the act of making software describe its behavior. Automatic instrumentation attaches to common frameworks and libraries, such as HTTP servers, database clients, message queues, and gRPC clients. Manual instrumentation adds spans, attributes, metrics, and events around business operations that generic library hooks cannot understand.

Start with automatic instrumentation because it gives fast coverage and exposes the request graph quickly. A Java agent can instrument Spring, JDBC, and HTTP clients without changing application code. A Python wrapper can instrument Flask, FastAPI, SQLAlchemy, requests, and other common libraries. This is especially useful when your first goal is to find missing service-to-service edges rather than model every business decision.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                          AUTO VS MANUAL INSTRUMENTATION                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Automatic instrumentation                                                    │
│  ┌─────────────────────┐      captures      ┌────────────────────────────┐   │
│  │ HTTP framework      │───────────────────▶│ inbound request spans       │   │
│  │ DB client           │───────────────────▶│ query spans                 │   │
│  │ Message library     │───────────────────▶│ publish and consume spans   │   │
│  └─────────────────────┘                    └────────────────────────────┘   │
│                                                                              │
│  Manual instrumentation                                                       │
│  ┌─────────────────────┐      explains      ┌────────────────────────────┐   │
│  │ approve_loan()      │───────────────────▶│ business decision span      │   │
│  │ calculate_risk()    │───────────────────▶│ domain attributes           │   │
│  │ reserve_inventory() │───────────────────▶│ failure reason events       │   │
│  └─────────────────────┘                    └────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Manual instrumentation is still necessary because the most important production questions are often business questions. A generic HTTP span can tell you that `POST /orders` took too long. It cannot tell you whether the delay happened while validating a coupon, reserving inventory, retrying payment authorization, or waiting on fraud scoring. You add manual spans at the boundaries where business meaning changes.

Here is a runnable Python example that creates a trace, adds business attributes, records an exception, and exports through OTLP. It is deliberately small so you can see the mechanics before Kubernetes, sampling, and Collector processing add more layers.

```python
# requirements:
# pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

from random import random

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


resource = Resource.create(
    {
        "service.name": "order-service",
        "service.version": "1.0.0",
        "deployment.environment": "dev",
    }
)

provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4317", insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("order-service")


def validate_order(order_id: str) -> None:
    with tracer.start_as_current_span("validate_order") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("validation.type", "full")
        if random() < 0.2:
            raise ValueError("inventory reservation failed")


def save_order(order_id: str) -> None:
    with tracer.start_as_current_span("save_order") as span:
        span.set_attribute("order.id", order_id)


def process_order(order_id: str) -> None:
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        try:
            validate_order(order_id)
            save_order(order_id)
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
            raise


if __name__ == "__main__":
    process_order("order-123")
    provider.shutdown()
```

The worked example has a root span called `process_order` and child spans for validation and saving. If validation fails, the exception is recorded on the business span, not only in a log line. That difference matters during incidents because the failing decision becomes visible in the trace tree, and the backend can keep error traces even when successful traces are sampled aggressively.

**Pause and predict:** If the `service.name` resource attribute is missing from the example, what will the backend show? Most systems will still ingest the spans, but they may appear under an unknown service or be grouped with unrelated telemetry. Predict how that would affect ownership, alert routing, and dashboard filters before reading further.

The resource is not decoration. It is the identity card attached to telemetry. `service.name`, `service.version`, and `deployment.environment` let backends group data correctly and let platform teams distinguish a production checkout failure from a development test. Missing or inconsistent resource attributes are one of the most common causes of "OpenTelemetry is working, but nobody can find anything."

Metrics follow the same principle. You use counters for events that only increase, histograms for distributions such as latency and payload size, and gauges for values that rise and fall. The code below records request counts and durations with attributes that are useful for aggregation. Avoid putting high-cardinality values such as raw user IDs, order IDs, or full URLs into metrics labels because they can explode storage costs.

```python
# requirements:
# pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

import time
from random import uniform

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


resource = Resource.create(
    {
        "service.name": "order-service",
        "deployment.environment": "dev",
    }
)

exporter = OTLPMetricExporter(endpoint="http://127.0.0.1:4317", insecure=True)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("order-service")
request_counter = meter.create_counter(
    name="http.server.requests",
    unit="1",
    description="Total HTTP requests handled by the service",
)
duration_histogram = meter.create_histogram(
    name="http.server.duration",
    unit="s",
    description="HTTP request duration in seconds",
)


def handle_request(route: str, method: str, status_code: int) -> None:
    start = time.time()
    time.sleep(uniform(0.01, 0.2))
    elapsed = time.time() - start
    attributes = {
        "http.route": route,
        "http.request.method": method,
        "http.response.status_code": status_code,
    }
    request_counter.add(1, attributes)
    duration_histogram.record(elapsed, attributes)


if __name__ == "__main__":
    handle_request("/orders/{id}", "GET", 200)
    provider.shutdown()
```

This example uses route templates rather than raw paths. `/orders/{id}` is safe because it groups many requests into one series. `/orders/123`, `/orders/124`, and every other concrete ID would create a new time series, which raises cost and makes dashboards slower. Senior observability work is often about this kind of restraint: record the attribute that supports a decision, not every value that happens to exist.

### 3. Context Propagation: The Difference Between Spans and Traces

A span is one timed operation. A trace is a connected tree of spans that share a trace ID. The connection depends on context propagation: each service must extract incoming trace context, create child spans under that context, and inject updated context into outgoing requests. When propagation breaks, the backend receives spans but cannot connect them into one request journey.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CONTEXT PROPAGATION                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Client request                                                               │
│      │                                                                       │
│      ▼                                                                       │
│  ┌──────────────┐    HTTP headers     ┌──────────────┐    gRPC metadata     │
│  │ Service A    │────────────────────▶│ Service B    │────────────────────▶ │
│  │ span_id: a1  │ traceparent header  │ span_id: b1  │ traceparent metadata │
│  │ parent: none │                     │ parent: a1   │                     │
│  └──────┬───────┘                     └──────┬───────┘                     │
│         │                                    │                              │
│         │                                    ▼                              │
│         │                              ┌──────────────┐                     │
│         │                              │ Service C    │                     │
│         │                              │ span_id: c1  │                     │
│         │                              │ parent: b1   │                     │
│         │                              └──────────────┘                     │
│         │                                                                   │
│         ▼                                                                   │
│  One trace ID ties A, B, and C together; parent span IDs build the tree.      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

The W3C `traceparent` header is the default modern propagation format. Some environments also need B3 propagation for compatibility with Zipkin-era services. During migrations, it is common to accept more than one propagator so that old and new workloads can share context while teams gradually standardize.

```python
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


set_global_textmap(
    CompositePropagator(
        [
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
            B3MultiFormat(),
        ]
    )
)
```

The most useful propagation debugging habit is to follow the boundary, not the service. If Service A and Service C appear in one trace but Service B appears as a separate root trace, inspect the request into B and the request out of B. The failure may be an uninstrumented custom client, a reverse proxy stripping headers, an async queue that does not copy message attributes, or manual spans created without the active parent context.

**Stop and think:** A team says, "The Collector is losing spans because checkout and payment are in separate traces." What evidence would prove or disprove that claim? Think about where trace IDs are created, where headers cross process boundaries, and whether a Collector can reconstruct a parent-child relationship that the applications never emitted.

A Collector can transform, filter, sample, and export telemetry, but it cannot infer missing parentage reliably after the fact. If two services create different trace IDs because propagation failed, the Collector sees two independent traces. This is why propagation debugging starts in application boundaries and network intermediaries before blaming the backend.

### 4. The Collector: Receivers, Processors, Exporters, and Pipelines

The OpenTelemetry Collector is the operational control point for telemetry. Receivers accept data, processors modify or decide what to keep, exporters send data onward, and pipelines connect those pieces per signal type. A Collector can receive OTLP from applications, scrape Prometheus endpoints, accept legacy Zipkin traffic, batch data, apply memory limits, remove noisy spans, and export to multiple destinations.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              OTEL COLLECTOR                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RECEIVERS                         PROCESSORS                  EXPORTERS      │
│  ┌──────────────┐                  ┌──────────────┐            ┌──────────┐ │
│  │ otlp/grpc    │─────────────────▶│ memory_limit │───────────▶│ otlp     │ │
│  └──────────────┘                  └──────────────┘            └──────────┘ │
│  ┌──────────────┐                  ┌──────────────┐            ┌──────────┐ │
│  │ otlp/http    │─────────────────▶│ batch        │───────────▶│ prometheus││
│  └──────────────┘                  └──────────────┘            └──────────┘ │
│  ┌──────────────┐                  ┌──────────────┐            ┌──────────┐ │
│  │ prometheus   │─────────────────▶│ resource     │───────────▶│ debug    │ │
│  └──────────────┘                  └──────────────┘            └──────────┘ │
│  ┌──────────────┐                  ┌──────────────┐            ┌──────────┐ │
│  │ zipkin       │─────────────────▶│ filter       │───────────▶│ archive  │ │
│  └──────────────┘                  └──────────────┘            └──────────┘ │
│                                                                              │
│  Pipelines bind selected receivers, processors, and exporters per signal.     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

A minimal production-minded Collector configuration should include a memory limiter before expensive processing, batching before export, explicit endpoints, and health or debug extensions for operations. The configuration below uses the `debug` exporter for local verification and an OTLP exporter for a tracing backend such as Tempo or Jaeger with OTLP enabled.

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
        - job_name: otel-collector
          static_configs:
            - targets:
                - 127.0.0.1:8888

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

  batch:
    timeout: 1s
    send_batch_size: 1024

  resource:
    attributes:
      - key: deployment.environment
        value: dev
        action: upsert

  filter/drop_health_checks:
    traces:
      span:
        - 'name == "GET /healthz"'
        - 'name == "GET /readyz"'

exporters:
  debug:
    verbosity: detailed

  otlp/tempo:
    endpoint: tempo.observability.svc.cluster.local:4317
    tls:
      insecure: true

  prometheus:
    endpoint: 0.0.0.0:8889

extensions:
  health_check:
    endpoint: 0.0.0.0:13133

service:
  extensions:
    - health_check
  pipelines:
    traces:
      receivers:
        - otlp
      processors:
        - memory_limiter
        - filter/drop_health_checks
        - batch
      exporters:
        - debug
        - otlp/tempo
    metrics:
      receivers:
        - otlp
        - prometheus
      processors:
        - memory_limiter
        - resource
        - batch
      exporters:
        - prometheus
    logs:
      receivers:
        - otlp
      processors:
        - memory_limiter
        - batch
      exporters:
        - debug
```

Processor order matters. The memory limiter should run early because it protects the Collector from overload before queues grow. Filters usually run before batching so unwanted telemetry does not consume batch capacity. Batching should run late because it improves export efficiency after data has been shaped.

A common senior-level mistake is treating one Collector as both a node-local agent and a central gateway. Agent Collectors run near workloads and usually focus on receiving local telemetry, adding Kubernetes metadata, and forwarding efficiently. Gateway Collectors run as shared services and usually apply routing, sampling, redaction, and multi-backend export. Combining both roles can work in small environments, but separating them becomes cleaner as traffic and ownership grow.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         AGENT AND GATEWAY DEPLOYMENT                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Kubernetes Node A                         Observability Namespace           │
│  ┌──────────────────────────────┐          ┌──────────────────────────────┐ │
│  │ app pod ─────┐               │          │ gateway collector replica 1   │ │
│  │ app pod ─────┼──▶ agent      │─────────▶│ gateway collector replica 2   │ │
│  │ app pod ─────┘   collector   │          │ gateway collector replica 3   │ │
│  └──────────────────────────────┘          └──────────────┬───────────────┘ │
│                                                           │                 │
│  Kubernetes Node B                                        ▼                 │
│  ┌──────────────────────────────┐          ┌──────────────────────────────┐ │
│  │ app pod ─────┐               │          │ trace backend, metrics store,│ │
│  │ app pod ─────┼──▶ agent      │─────────▶│ log backend, archive export  │ │
│  │ app pod ─────┘   collector   │          └──────────────────────────────┘ │
│  └──────────────────────────────┘                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5. Sampling, Filtering, and Cost Control

Sampling decides which traces are kept. Filtering removes telemetry that should not be exported. Batching changes how telemetry is sent. These controls are operationally connected because they all affect cost, memory, and incident usefulness. A platform that samples too aggressively saves money but misses rare failures. A platform that keeps everything may discover the incident quickly and then lose budget or storage capacity.

Head sampling makes the decision near the beginning of a trace. It is simple, cheap, and easy to run in application SDKs or agent Collectors. Its weakness is that it decides before the system knows whether the trace will become slow or fail, so rare but important traces can be dropped.

Tail sampling waits until a trace is complete or until a decision timeout is reached. It can keep all error traces, all slow traces, and a smaller percentage of normal traces. Its weakness is complexity: the Collector must buffer spans long enough to make the decision, and horizontally scaled tail-sampling gateways must see all spans for the same trace or use a load-balancing strategy that routes trace IDs consistently.

```text
HEAD SAMPLING                                      TAIL SAMPLING
──────────────────────────────────────────────────────────────────────────────
Decision time: trace start                         Decision time: after spans arrive
Memory cost: low                                   Memory cost: higher
Can keep all errors: no                            Can keep all errors: yes
Can keep slow traces: no                           Can keep slow traces: yes
Operational risk: missed incidents                 Operational risk: buffering and routing
Best fit: edge, high-volume normal traffic         Best fit: central gateway, incident analysis
```

Here is a Collector tail-sampling configuration that keeps error traces, keeps slow traces, and samples a small percentage of normal traces. The numbers are intentionally conservative for a small lab. In production, you would size `num_traces`, `expected_new_traces_per_sec`, memory limits, and gateway replicas using measured traffic rather than guesses.

```yaml
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 5000
    expected_new_traces_per_sec: 300
    policies:
      - name: keep-errors
        type: status_code
        status_code:
          status_codes:
            - ERROR

      - name: keep-slow
        type: latency
        latency:
          threshold_ms: 1000

      - name: sample-normal-traffic
        type: probabilistic
        probabilistic:
          sampling_percentage: 5
```

**Pause and predict:** Your gateway Collector runs three replicas behind a normal Kubernetes Service, and you enable tail sampling. Some spans from one trace land on replica one, while other spans from the same trace land on replica two. What will happen to sampling decisions? Predict the failure mode before reading the answer.

Tail sampling only works well when the decision maker sees enough of the trace. If spans from the same trace are scattered across independent Collectors, each replica may make incomplete decisions. One replica may keep a partial trace because it saw an error span, while another may drop related normal spans. Production designs usually place tail sampling in a gateway layer and add routing that keeps spans for the same trace together, or they accept head sampling when the operational complexity of tail sampling is not justified.

| Control | Strength | Risk | Good Use |
|---|---|---|---|
| Head sampling | Simple and low overhead | Drops traces before knowing whether they matter | Reducing high-volume normal traffic near the source |
| Tail sampling | Keeps traces based on outcome | Requires buffering and trace-aware routing | Preserving errors and slow requests under cost limits |
| Filtering | Removes predictable noise | Can hide useful signals if rules are too broad | Dropping health checks and synthetic probes |
| Batching | Improves export efficiency | Can delay visibility slightly | Almost every Collector pipeline |
| Memory limiting | Protects Collector stability | Drops telemetry under pressure | All production Collectors |

Cost control is not only about sampling percentages. Attribute design can be more important. A metric with `user.id`, `order.id`, or full URL paths can create millions of series even when request volume is moderate. A trace attribute with sensitive data can create compliance risk even if ingestion cost is acceptable. Good OpenTelemetry design asks: "Will this attribute help us route, aggregate, debug, or explain behavior?" If not, leave it out or put it somewhere safer.

### 6. Debugging an OpenTelemetry Pipeline

Debugging OpenTelemetry works best when you test one boundary at a time. First prove the application creates telemetry. Then prove the SDK exports it. Then prove the Collector receives it. Then prove processors keep it. Then prove exporters deliver it. Jumping straight to the backend often wastes time because a missing dashboard can be caused by a missing resource attribute, a network policy, a dropped processor rule, or a backend authentication error.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         TELEMETRY DEBUGGING CHECKLIST                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Application creates telemetry                                             │
│     └─ Is the SDK initialized before requests start?                          │
│                                                                              │
│  2. Resource attributes identify the service                                  │
│     └─ Is service.name set consistently?                                      │
│                                                                              │
│  3. SDK exports to the expected endpoint                                      │
│     └─ Is the app using 4317 for gRPC or 4318 for HTTP?                       │
│                                                                              │
│  4. Collector receives the signal                                             │
│     └─ Do Collector logs or self-metrics show accepted spans or metrics?      │
│                                                                              │
│  5. Processors keep the signal                                                │
│     └─ Did a filter, sampler, or memory limiter drop the data?                │
│                                                                              │
│  6. Exporter delivers to backend                                              │
│     └─ Are auth, TLS, DNS, and backend limits correct?                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Collector self-metrics are an underused debugging tool. Metrics such as accepted spans, refused spans, processor drops, exporter queue size, and send failures can tell you whether the problem is upstream or downstream. If accepted spans increase but exporter failures also increase, the Collector is receiving data and failing to deliver it. If accepted spans stay at zero, focus on application endpoints, protocol mismatch, DNS, and network policy.

A protocol mismatch is easy to miss. OTLP/gRPC commonly uses port `4317`; OTLP/HTTP commonly uses port `4318`. Sending HTTP payloads to the gRPC receiver, or gRPC traffic to the HTTP receiver, often looks like a generic connection or parsing failure. During incident response, explicitly verify the exporter type and endpoint instead of assuming the port is enough.

```bash
# Verify Collector pods and service endpoints.
kubectl get pods -n observability
kubectl get svc -n observability otel-collector

# After this module introduces the alias, use k for shorter commands.
alias k=kubectl

# Check Collector logs for receiver, processor, and exporter errors.
k logs -n observability -l app=otel-collector --tail=100

# Port-forward the Collector's Prometheus exporter from the lab.
k port-forward -n observability svc/otel-collector 8889:8889

# Inspect exported metrics from the Collector lab endpoint.
curl -s http://127.0.0.1:8889/metrics | grep -E "otelcol|http"
```

When telemetry is missing, resist the urge to change several things at once. Add the `debug` exporter temporarily, send one known request, and confirm whether the Collector prints the span. If it does, the application-to-Collector path works and you should focus on processors and backend export. If it does not, focus on SDK configuration, service discovery, protocol, and network connectivity.

## Did You Know?

- OpenTelemetry was created by merging OpenTracing and OpenCensus, which ended a split between two major open instrumentation efforts.
- OTLP can carry traces, metrics, and logs, but each signal still needs a correctly configured pipeline in the Collector.
- The Collector can run as an agent, gateway, sidecar, or standalone process; the right shape depends on traffic volume, ownership, and failure isolation.
- Tail sampling can preserve important traces, but it becomes a distributed-systems problem when gateway replicas do not consistently receive all spans for the same trace.

## Common Mistakes

| Mistake | What Breaks | How to Diagnose | Better Practice |
|---|---|---|---|
| Missing `service.name` or environment attributes | Telemetry arrives but cannot be grouped, owned, or routed correctly | Search the backend for unknown services and inspect resource attributes in debug export | Set resource attributes in SDKs, operators, or Collector resource processors |
| Exporting directly from every app to every backend | Backend changes require application redeploys and repeated configuration | Count how many repositories contain backend exporter settings | Send workloads to a Collector and change backend routing centrally |
| Using OTLP/HTTP against the gRPC receiver, or the reverse | Export attempts fail with connection, parsing, or unavailable errors | Compare exporter type with port `4317` or `4318` and receiver configuration | Standardize endpoint names and document which protocol each port expects |
| Running the Collector without `memory_limiter` and resource limits | Spikes or backend outages can cause OOM kills and telemetry loss | Check pod restarts, memory usage, and exporter queue growth | Put `memory_limiter` early in every pipeline and set Kubernetes memory limits |
| Applying broad filters before proving signal value | Useful traces disappear and teams blame instrumentation | Temporarily add a debug exporter before and after filter changes | Filter predictable noise such as health checks, not whole routes or services casually |
| Enabling tail sampling without trace-aware gateway routing | Traces become partial or sampling decisions appear inconsistent | Compare spans for one trace across Collector replicas and gateway logs | Use routing that keeps trace IDs together, or use head sampling until routing is ready |
| Adding high-cardinality attributes to metrics | Storage cost and query latency grow rapidly | Inspect label values for user IDs, order IDs, raw paths, or request IDs | Use route templates and bounded labels; keep unique IDs in traces or logs |
| Assuming auto-instrumentation captures business meaning | Traces show framework calls but not why the operation mattered | Look for spans named only after HTTP routes or database calls | Add manual spans around domain decisions, retries, and external dependency boundaries |

## Quiz

<details>
<summary>1. Your team deploys auto-instrumentation and sees HTTP spans, but all services appear as `unknown_service`. What do you check and how do you fix it?</summary>

Check resource attributes first, especially `service.name`, `service.version`, and `deployment.environment`. The instrumentation may be creating spans correctly, but the backend cannot group them under useful service identities. Fix the SDK, agent environment variables, OpenTelemetry Operator configuration, or Collector `resource` processor so every workload emits a stable `service.name`. Then send one request and verify the debug exporter or backend shows the corrected resource.
</details>

<details>
<summary>2. A payment trace shows checkout and inventory, but payment appears as a separate root trace. The Collector is receiving spans from all three services. Where should you investigate first?</summary>

Investigate context propagation at the payment service boundary. Confirm checkout injects `traceparent`, confirm any proxy preserves the header, confirm payment extracts the incoming context before creating spans, and confirm payment injects context into further outgoing calls. Since the Collector receives spans from all services, the missing relationship is probably created before collection, not inside the backend.
</details>

<details>
<summary>3. Your platform wants to keep every error trace but only a small percentage of successful traces. Which sampling approach fits, and what operational risk must you manage?</summary>

Tail sampling fits because it can wait until spans reveal status codes, latency, or attributes before deciding what to keep. The operational risk is buffering and trace completeness. Gateway Collectors need enough memory and must receive all or most spans for the same trace, usually through trace-aware routing. Without that, tail sampling can create partial traces or inconsistent decisions.
</details>

<details>
<summary>4. A Collector receives spans, but the backend shows none. What sequence of checks would isolate whether the problem is processing or export?</summary>

First add or enable a `debug` exporter in the same traces pipeline to prove spans survive receivers and early processors. Then inspect Collector self-metrics and logs for processor drops, memory limiter pressure, exporter queue growth, and send failures. If debug output shows spans but backend export fails, focus on exporter endpoint, protocol, TLS, authentication, DNS, and backend ingestion limits. If debug output shows no spans, move upstream to SDK endpoint and receiver configuration.
</details>

<details>
<summary>5. A developer adds `user.id` and full request URL labels to a latency histogram so incidents are easier to debug. What do you recommend?</summary>

Do not put unbounded identifiers into metric attributes. They create high-cardinality series that increase cost and slow queries. Use route templates such as `/orders/{id}`, bounded dimensions such as method and status code, and keep unique identifiers in traces or logs where they support point investigation. If a user-specific investigation is required, link from metrics to exemplars or traces rather than turning every user into a metric series.
</details>

<details>
<summary>6. Your app exports to `http://otel-collector:4317`, but the SDK is configured for OTLP/HTTP. The Collector has gRPC on `4317` and HTTP on `4318`. What symptom do you expect and what is the fix?</summary>

The application will likely fail export with connection, protocol, or parsing errors because OTLP/HTTP is being sent to the gRPC receiver. Change the endpoint to `http://otel-collector:4318` for OTLP/HTTP, or change the exporter to OTLP/gRPC if you want to use `4317`. After changing it, verify accepted spans or metrics in Collector logs or self-metrics.
</details>

<details>
<summary>7. A team wants to remove all health-check spans with a filter processor. How do you make the change without hiding real traffic?</summary>

Start by identifying exact span names or route attributes for health checks, then add a narrow filter such as `GET /healthz` and `GET /readyz`. Keep a debug exporter during the change or compare accepted and dropped span counts before and after rollout. Avoid broad patterns such as every route containing `health` unless you have proved they only match probes. The goal is to reduce predictable noise while preserving user-facing failure evidence.
</details>

<details>
<summary>8. During a backend outage, Collector memory grows and pods restart. Which Collector settings and Kubernetes settings do you inspect?</summary>

Inspect the `memory_limiter` processor, exporter queue settings, batch processor settings, and Kubernetes memory limits. A backend outage can cause queued telemetry to accumulate, especially if the Collector has no early memory protection. The better design sets pod memory limits, places `memory_limiter` early in each pipeline, uses bounded queues, and accepts that telemetry may be dropped under pressure rather than allowing the Collector to crash repeatedly.
</details>

## Hands-On Exercise: Build and Debug an OpenTelemetry Pipeline

In this exercise you will deploy an OpenTelemetry Collector, send traces and metrics from a small Python application, and verify the pipeline from the application to the Collector. The goal is not to build a perfect production stack. The goal is to practice the debugging sequence you will use when a real platform says, "Telemetry is missing."

### Step 1: Create a Namespace

```bash
kubectl create namespace observability
alias k=kubectl
```

Success criteria:

- [ ] The `observability` namespace exists.
- [ ] You can run `k get ns observability` successfully.
- [ ] You understand that the alias is only a shell shortcut for this exercise.

### Step 2: Deploy the Collector

```bash
k apply -f - <<'EOF'
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
      memory_limiter:
        check_interval: 1s
        limit_mib: 256
        spike_limit_mib: 64
      batch:
        timeout: 1s
        send_batch_size: 256
      resource:
        attributes:
          - key: deployment.environment
            value: lab
            action: upsert

    exporters:
      debug:
        verbosity: detailed
      prometheus:
        endpoint: 0.0.0.0:8889

    extensions:
      health_check:
        endpoint: 0.0.0.0:13133

    service:
      extensions:
        - health_check
      pipelines:
        traces:
          receivers:
            - otlp
          processors:
            - memory_limiter
            - resource
            - batch
          exporters:
            - debug
        metrics:
          receivers:
            - otlp
          processors:
            - memory_limiter
            - resource
            - batch
          exporters:
            - prometheus
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
          image: otel/opentelemetry-collector-contrib:0.99.0
          args:
            - --config=/etc/otel/config.yaml
          ports:
            - name: otlp-grpc
              containerPort: 4317
            - name: otlp-http
              containerPort: 4318
            - name: metrics
              containerPort: 8889
            - name: health
              containerPort: 13133
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
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
      targetPort: 4317
    - name: otlp-http
      port: 4318
      targetPort: 4318
    - name: metrics
      port: 8889
      targetPort: 8889
    - name: health
      port: 13133
      targetPort: 13133
EOF
```

Success criteria:

- [ ] `k get pods -n observability` shows the Collector pod running.
- [ ] `k logs -n observability -l app=otel-collector --tail=50` shows no configuration errors.
- [ ] You can explain why `memory_limiter` appears before `batch` in the pipelines.
- [ ] You can identify which port is OTLP/gRPC and which port is OTLP/HTTP.

### Step 3: Deploy a Small Instrumented Application

```bash
k apply -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: demo-app-code
  namespace: observability
data:
  app.py: |
    import random
    import time

    from flask import Flask
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": "demo-app",
            "service.version": "1.0.0",
        }
    )

    trace_provider = TracerProvider(resource=resource)
    trace_exporter = OTLPSpanExporter(
        endpoint="http://otel-collector.observability.svc.cluster.local:4317",
        insecure=True,
    )
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    metric_exporter = OTLPMetricExporter(
        endpoint="http://otel-collector.observability.svc.cluster.local:4317",
        insecure=True,
    )
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=5000,
    )
    metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(metric_provider)

    tracer = trace.get_tracer("demo-app")
    meter = metrics.get_meter("demo-app")
    request_counter = meter.create_counter("demo.requests", unit="1")
    request_duration = meter.create_histogram("demo.request.duration", unit="s")

    app = Flask(__name__)
    FlaskInstrumentor().instrument_app(app)

    @app.route("/")
    def index():
        start = time.time()
        request_counter.add(1, {"http.route": "/", "http.request.method": "GET"})
        request_duration.record(time.time() - start, {"http.route": "/"})
        return "Hello from OpenTelemetry\n"

    @app.route("/checkout")
    def checkout():
        start = time.time()
        with tracer.start_as_current_span("reserve_inventory") as span:
            delay = random.uniform(0.05, 0.3)
            span.set_attribute("inventory.delay_seconds", delay)
            time.sleep(delay)

        with tracer.start_as_current_span("authorize_payment") as span:
            approved = random.random() > 0.2
            span.set_attribute("payment.approved", approved)
            if not approved:
                span.set_attribute("payment.failure_reason", "issuer_declined")

        elapsed = time.time() - start
        request_counter.add(1, {"http.route": "/checkout", "http.request.method": "GET"})
        request_duration.record(elapsed, {"http.route": "/checkout"})
        return f"checkout completed in {elapsed:.3f}s\n"

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8080)
---
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
          image: python:3.12-slim
          command:
            - /bin/sh
            - -c
          args:
            - |
              pip install --no-cache-dir flask opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-flask &&
              python -u /app/app.py
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: app-code
              mountPath: /app
      volumes:
        - name: app-code
          configMap:
            name: demo-app-code
---
apiVersion: v1
kind: Service
metadata:
  name: demo-app
  namespace: observability
spec:
  selector:
    app: demo-app
  ports:
    - name: http
      port: 8080
      targetPort: 8080
EOF
```

Success criteria:

- [ ] `k get pods -n observability -l app=demo-app` shows the demo application running.
- [ ] The application code sets `service.name` before creating traces and metrics.
- [ ] You can identify the manually created spans inside the `/checkout` handler.
- [ ] You can explain which spans Flask auto-instrumentation should add.

### Step 4: Generate Traffic and Verify Traces

```bash
k port-forward -n observability svc/demo-app 8080:8080
```

In a second terminal:

```bash
curl -s http://127.0.0.1:8080/
curl -s http://127.0.0.1:8080/checkout
curl -s http://127.0.0.1:8080/checkout
```

Then inspect Collector logs:

```bash
k logs -n observability -l app=otel-collector --tail=200 | grep -E "demo-app|reserve_inventory|authorize_payment"
```

Success criteria:

- [ ] You see evidence of `demo-app` in Collector debug output.
- [ ] You see spans for the `/checkout` request.
- [ ] You can distinguish framework spans from manual business spans.
- [ ] You can explain why the `debug` exporter is useful during first deployment.

### Step 5: Verify Metrics

```bash
k port-forward -n observability svc/otel-collector 8889:8889
```

In a second terminal:

```bash
curl -s http://127.0.0.1:8889/metrics | grep demo
```

Success criteria:

- [ ] You can query the Collector's Prometheus exporter.
- [ ] You see `demo.requests` or translated metric names exposed for scraping.
- [ ] You can explain why route templates are safer metric labels than raw URLs.
- [ ] You can describe how Prometheus from Module 1.1 would scrape this endpoint.

### Step 6: Break One Thing on Purpose

Change the application exporter endpoint from port `4317` to `4318` while still using the gRPC exporter, redeploy the application, and generate traffic again. Then inspect the application logs and Collector logs.

Success criteria:

- [ ] You can observe export failures or missing accepted telemetry.
- [ ] You can explain why OTLP/gRPC and OTLP/HTTP are not interchangeable just because both are OTLP.
- [ ] You can restore the correct endpoint and verify telemetry returns.
- [ ] You can write a short debugging note that names the boundary you tested.

### Step 7: Clean Up

```bash
k delete namespace observability
```

Success criteria:

- [ ] The namespace and lab workloads are removed.
- [ ] You can summarize the full signal path from application SDK to Collector exporter.
- [ ] You can name at least two places where telemetry could be dropped intentionally.
- [ ] You can name at least two places where telemetry could be lost accidentally.

## Next Module

Continue to [Module 1.3: Grafana](../module-1.3-grafana/) to learn how dashboards and visual exploration turn telemetry into operational decisions.

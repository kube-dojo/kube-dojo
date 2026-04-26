---
title: "Module 1.5: Distributed Tracing"
slug: platform/toolkits/observability-intelligence/observability/module-1.5-tracing
sidebar:
  order: 6
---

# Module 1.5: Distributed Tracing

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 55-70 min

> **Prerequisites**: [Module 1.2: OpenTelemetry](../module-1.2-opentelemetry/), [Module 1.1: Prometheus](../module-1.1-prometheus/), [Module 1.4: Loki](../module-1.4-loki/), and working familiarity with HTTP services, Kubernetes Deployments, and basic microservice request flows.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Debug** a slow or failing distributed request by reading trace structure, span timing, span status, and parent-child relationships.
- **Instrument** an HTTP service with OpenTelemetry so it emits useful spans, resource attributes, and trace context headers.
- **Compare** Jaeger, Grafana Tempo, and managed tracing options using search needs, storage cost, operational complexity, and incident workflow fit.
- **Design** a sampling strategy that keeps important traces, controls storage cost, and avoids hiding rare failures.
- **Evaluate** correlated observability evidence by moving from metrics to traces to logs during an incident investigation.

---

## Why This Module Matters

A platform team at a payments company had a checkout incident that looked impossible from the dashboards. The public API showed elevated latency, the payment service looked healthy, the inventory service had no obvious errors, and the message broker was still accepting writes. Every team could prove its own service was mostly fine, yet customers were seeing timeouts after submitting orders. The hardest part was not fixing the bug; it was finding the exact place where the request stopped behaving like the system diagram promised.

The incident dragged because each signal answered only part of the question. Metrics proved that checkout latency had moved outside the service objective, but metrics could not show which hop inside the request path was responsible. Logs contained useful details, but they were spread across independent services that did not share a reliable request identifier. By the time an engineer found one suspicious timeout in a downstream dependency, the team still could not prove whether it explained the customer-facing failure or was just background noise.

Distributed tracing changes the shape of that investigation. Instead of asking every service owner to defend a local dashboard, the team can inspect one request as it crosses boundaries. A trace shows which service accepted the request, which downstream calls it made, where time accumulated, where errors were recorded, and whether context was lost at HTTP, messaging, or proxy boundaries. Tracing does not replace metrics or logs; it gives them a shared request story so engineers can move from symptom to cause with less guessing.

This module teaches tracing as a production debugging skill, not as a vendor feature checklist. You will start with the mental model of traces and spans, then walk through a worked example that instruments a small service from zero. From there, you will compare storage backends, sampling decisions, correlation patterns, and operational mistakes that separate useful traces from expensive noise. The goal is that by the end, you can look at a trace during an incident and make a defensible next move.

---

## Core Content

### 1. Trace Anatomy: A Request Becomes A Timeline

A trace is the complete recorded journey of one logical operation through a distributed system. In a simple service, that operation might be one HTTP request handled by one process. In a real platform, the same operation might touch an API gateway, authentication service, checkout service, inventory database, payment provider, message broker, and notification worker. The trace gives that operation one stable identity so the system can be read as a sequence instead of as disconnected logs.

A span is one timed unit of work inside that trace. A span usually represents an inbound HTTP request, an outbound HTTP call, a database query, a cache lookup, a queue publish, or a manually instrumented block of business logic. The span records when the work started, when it ended, which span was its parent, whether it failed, and which attributes describe the work. The parent-child relationship is what turns a pile of timings into a tree that explains causality.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                              TRACE: checkout-9a21                          │
│  One customer checkout request, crossing service and infrastructure edges.  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Time ─────────────────────────────────────────────────────────────────▶   │
│                                                                            │
│  api-gateway             18 ms                                             │
│  └── checkout-api        620 ms                                            │
│      ├── auth-service     31 ms                                            │
│      ├── inventory-api    88 ms                                            │
│      │   └── postgres     63 ms                                            │
│      ├── payment-api     420 ms                                            │
│      │   └── bank-http   392 ms  status=ERROR timeout=true                 │
│      └── publish-order    26 ms                                            │
│                                                                            │
│  Root span: api-gateway                                                    │
│  Slow branch: checkout-api → payment-api → bank-http                       │
│  Failing span: bank-http, which explains the customer-visible timeout       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

The first senior habit is to read a trace from the outside in. Start with the root span and ask whether the total duration matches the symptom that users saw. Then follow the longest branch, because latency is often hidden in one branch rather than evenly spread across all services. Finally, inspect error status, retry attributes, and missing children, because a trace can reveal both explicit failures and uninstrumented gaps.

A trace ID identifies the whole request, while a span ID identifies one span inside that trace. A parent span ID connects a child span back to the operation that caused it. When service A calls service B, service A must inject the current trace context into the outbound request, and service B must extract that context before creating its server span. If either side fails, the backend sees two unrelated traces instead of one continuous request story.

| Term | What It Means | Debugging Question It Answers |
|------|---------------|-------------------------------|
| Trace | The complete request journey across services and dependencies. | Which path did this user operation take through the system? |
| Span | One timed operation inside the trace. | Which specific work consumed time or failed? |
| Trace ID | The identifier shared by every span in the same trace. | Which logs, metrics exemplars, and spans belong to the same request? |
| Span ID | The identifier for one span. | Which operation is this, and can another span point to it as parent? |
| Parent span ID | The link from a child operation to the operation that caused it. | Did this downstream call happen because of this upstream request? |
| Resource attributes | Metadata about the process emitting spans, such as service name and namespace. | Which workload, version, or environment produced this span? |
| Span attributes | Metadata about the operation, such as route, status code, database system, or queue name. | What exactly was the operation doing when latency or failure appeared? |
| Baggage | Propagated key-value context intended for cross-service use with care. | Does downstream code need a small business context value to make a decision? |

> **Pause and predict:** If `checkout-api` calls `payment-api`, and both services emit spans but the HTTP client in `checkout-api` does not inject `traceparent`, what will the tracing backend show? Write down whether you expect one trace, two traces, or no traces before reading the next paragraph.

The backend will usually show two traces. The inbound request to `checkout-api` still creates a trace, and the inbound request to `payment-api` may create another trace, but there is no parent-child link between them. This is one reason tracing can appear to be "working" while still being operationally weak: spans exist, dashboards have data, and storage grows, yet the exact boundary you need during an incident is broken.

The W3C Trace Context standard defines the headers that make this boundary reliable across languages and vendors. The `traceparent` header carries the trace ID, parent span ID, and sampling flag in a predictable format. The `tracestate` header lets vendors add implementation-specific data without breaking interoperability. You do not usually hand-write these headers in production code; instrumentation libraries should inject and extract them for HTTP, gRPC, and supported messaging clients.

```http
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              │  │                                │                │
              │  │                                │                └─ sampled flag
              │  │                                └────────────────── parent span ID
              │  └─────────────────────────────────────────────────── trace ID
              └────────────────────────────────────────────────────── version

tracestate: vendorA=state,vendorB=another-state
```

There is an important difference between propagation and instrumentation. Propagation keeps the request identity connected across boundaries. Instrumentation creates the spans and attributes that make the trace useful. A service can propagate context without recording rich spans, and a service can record spans without correctly joining the upstream trace. Production tracing needs both, because a beautifully detailed disconnected trace still leaves teams guessing across the service edge.

A useful span has a clear operation name, a correct parent, a status, a duration, and enough attributes to support investigation without creating dangerous cardinality. Good names look like `HTTP GET /checkout/{cart_id}`, `SELECT inventory by sku`, or `publish order.created`. Weak names look like `request`, `handler`, or `function_call`, because they force the reader to inspect every span manually. The best span names are stable enough for aggregation and specific enough for debugging.

The main risk is over-instrumentation. If every helper function becomes a span, traces become expensive and unreadable. If only service entry points become spans, traces hide database calls, queue operations, and business decisions. The practitioner balance is to span boundaries, expensive operations, failure-prone operations, and business checkpoints that explain why a request took a branch. You are not trying to record every CPU instruction; you are trying to reconstruct the request story when the system surprises you.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                         USEFUL SPAN BOUNDARIES                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Always consider spans for:                                                 │
│                                                                            │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────┐ │
│  │ Inbound requests    │────▶│ Outbound calls      │────▶│ Datastores   │ │
│  │ HTTP, gRPC, events  │     │ HTTP, gRPC, queues  │     │ SQL, cache   │ │
│  └─────────────────────┘     └─────────────────────┘     └──────────────┘ │
│                                                                            │
│  Add manual spans around:                                                   │
│                                                                            │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────┐ │
│  │ Risky decisions     │────▶│ Retries/timeouts    │────▶│ Async handoff│ │
│  │ fraud, routing      │     │ backoff, fallback   │     │ publish jobs │ │
│  └─────────────────────┘     └─────────────────────┘     └──────────────┘ │
│                                                                            │
│  Avoid spans for tiny deterministic helper functions unless they explain    │
│  a latency problem, a business branch, or a failure mode you routinely debug.│
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2. Worked Example: Instrument A Service Before You Deploy A Lab

Before configuring a tracing backend, it helps to see the smallest useful instrumentation loop. The goal of this worked example is not to build a production service. The goal is to take one ordinary HTTP handler, add OpenTelemetry, generate one normal request and one failing request, and inspect the emitted spans locally. This is the "I do" part before the hands-on exercise asks you to perform a fuller Kubernetes investigation.

Create a tiny FastAPI service with one checkout endpoint. The service has one manual span around inventory reservation and another around payment authorization, because those operations represent business steps that would matter during an incident. The code deliberately makes `cart_id=slow` slow and `cart_id=fail` fail so you can see how latency and errors appear in traces. The service is small enough to understand, but the instrumentation pattern is the same one you would apply inside a larger service.

```bash
mkdir -p tracing-worked-example
cd tracing-worked-example
```

```bash
cat > requirements.txt <<'EOF'
fastapi
uvicorn
opentelemetry-api
opentelemetry-sdk
opentelemetry-distro
opentelemetry-exporter-otlp
opentelemetry-instrumentation-fastapi
EOF
```

```python
# app.py
import time

from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

app = FastAPI()
tracer = trace.get_tracer("checkout-api.instrumentation")


@app.get("/checkout/{cart_id}")
def checkout(cart_id: str) -> dict[str, str]:
    with tracer.start_as_current_span("reserve_inventory") as span:
        span.set_attribute("cart.id", cart_id)
        span.set_attribute("inventory.system", "demo-postgres")
        time.sleep(0.05)

    with tracer.start_as_current_span("authorize_payment") as span:
        span.set_attribute("payment.provider", "demo-bank")
        span.set_attribute("payment.currency", "USD")

        if cart_id == "slow":
            span.set_attribute("payment.slow_path", True)
            time.sleep(0.55)
        else:
            time.sleep(0.08)

        if cart_id == "fail":
            span.set_status(Status(StatusCode.ERROR, "payment authorization failed"))
            span.record_exception(ValueError("demo payment decline"))
            raise HTTPException(status_code=502, detail="payment authorization failed")

    return {"cart_id": cart_id, "status": "confirmed"}
```

Install the dependencies into the repository virtual environment or into an equivalent local virtual environment. In this repository, commands use `.venv/bin/python` explicitly because the project standard is to avoid ambiguous interpreter selection. The command below also installs the OpenTelemetry bootstrap instrumentation packages for the libraries it detects. If the bootstrap command reports that a package is already installed, that is fine.

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/opentelemetry-bootstrap --action=install
```

Now run the service with console trace export. Console export is intentionally simple: it prints span data to the terminal instead of requiring Jaeger, Tempo, or a collector. In production you would export to an OpenTelemetry Collector over OTLP, but local console output is the fastest way to verify that spans exist, attributes are populated, and errors are marked.

```bash
OTEL_SERVICE_NAME=checkout-api \
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=local,service.version=1.0.0 \
OTEL_TRACES_EXPORTER=console \
.venv/bin/opentelemetry-instrument \
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8080
```

In another terminal, send three requests. The first request should be normal, the second should be slow, and the third should fail with an HTTP 502 response. You are not looking for a pretty UI yet. You are checking whether the emitted spans tell the same story as the behavior you intentionally created.

```bash
curl -s http://127.0.0.1:8080/checkout/normal
curl -s http://127.0.0.1:8080/checkout/slow
curl -s -i http://127.0.0.1:8080/checkout/fail
```

> **Stop and think:** Before inspecting the terminal output, predict which span should have the largest duration for `cart_id=slow` and which span should carry error status for `cart_id=fail`. If your prediction does not match the trace output, the mismatch is a clue about where your instrumentation is incomplete or misleading.

The normal request should show an inbound FastAPI server span with two child spans. The slow request should show `authorize_payment` taking longer than `reserve_inventory`. The failing request should show the server span returning an error response and the `authorize_payment` manual span recording an exception and error status. If the manual payment span is missing, you instrumented the service entry point but not the business operation that explains the incident.

A shortened console span will look similar to the following. Your exact span IDs and trace IDs will differ, because they are generated per request. The important parts are the shared trace ID, the parent-child relationship, the service name, the span name, the status, and the attributes that explain what operation occurred.

```json
{
  "name": "authorize_payment",
  "context": {
    "trace_id": "0x7d3f0d9e8c1a4b3a9c8f1e2d3c4b5a60",
    "span_id": "0x2f7a9d1c8b4e6a20"
  },
  "parent_id": "0x6b1d9e3a2c8f5b10",
  "status": {
    "status_code": "ERROR",
    "description": "payment authorization failed"
  },
  "attributes": {
    "payment.provider": "demo-bank",
    "payment.currency": "USD"
  }
}
```

This worked example demonstrates the minimum useful loop for initial instrumentation. First, set a stable `service.name` so traces can be grouped by workload. Second, enable automatic instrumentation for inbound and outbound framework boundaries. Third, add manual spans only where business operations clarify the request story. Fourth, generate known normal, slow, and failing traffic so you can verify the trace shape before depending on it during an incident.

When you move this pattern into Kubernetes, the same environment variables usually become Deployment configuration. The service emits spans to an OpenTelemetry Collector or directly to a backend over OTLP. A collector is preferred in production because it centralizes retries, batching, redaction, sampling, and routing. Direct-to-backend export can be acceptable in a lab, but it spreads operational policy across every service.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout-api
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: checkout-api
  template:
    metadata:
      labels:
        app: checkout-api
    spec:
      containers:
        - name: checkout-api
          image: registry.example.com/platform/checkout-api:1.0.0
          ports:
            - containerPort: 8080
          env:
            - name: OTEL_SERVICE_NAME
              value: checkout-api
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: deployment.environment=prod,k8s.namespace.name=default,service.version=1.0.0
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: http://otel-collector.tracing.svc.cluster.local:4317
            - name: OTEL_EXPORTER_OTLP_PROTOCOL
              value: grpc
            - name: OTEL_TRACES_EXPORTER
              value: otlp
```

The most common beginner mistake is to stop after installing an SDK and seeing any spans at all. A senior practitioner verifies trace quality with targeted questions. Does every service have a stable name? Do outbound calls carry `traceparent`? Are error spans marked as errors, or are they merely logged as text? Do the spans include route templates such as `/checkout/{cart_id}` instead of high-cardinality paths such as `/checkout/abc123`? Can a person on call understand the trace without reading the service source code?

### 3. Backends: Jaeger, Tempo, And The Storage Trade-Off

A tracing backend stores traces and lets engineers retrieve them during investigations. The backend is not the tracing system by itself; the system includes instrumentation libraries, propagation, collectors, sampling policy, storage, query, dashboards, and operational habits. Choosing a backend is therefore less about brand preference and more about the workflow you need during incidents. The central question is how your team usually finds the trace it needs.

Jaeger is a strong fit when engineers need direct search over trace attributes. If support receives an order ID, a customer tier, or a custom business tag, Jaeger-style indexed search can help locate candidate traces without first finding a trace ID elsewhere. That power has a cost: indexing span data requires more storage infrastructure, tuning, and operational care. Jaeger can be excellent for teams that value exploratory trace search and accept the cost of running indexed storage.

Grafana Tempo takes a different position. Tempo is optimized around cheap trace storage and trace-ID lookup, with strong integration into Grafana workflows. Instead of indexing every span attribute heavily, Tempo expects you to arrive with a trace ID from metrics exemplars, logs, or TraceQL-supported search paths depending on deployment mode and version. This can be a better fit for teams already using Prometheus, Grafana, and Loki, especially when trace volume is high and cost pressure is real.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                       TRACING BACKEND DECISION VIEW                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  How do engineers find a trace during an incident?                          │
│                                                                            │
│  ┌──────────────────────────────┐        ┌──────────────────────────────┐  │
│  │ Search by attributes first   │        │ Start from metrics or logs    │  │
│  │ order_id, customer_id, route │        │ exemplar trace_id, log field  │  │
│  └──────────────┬───────────────┘        └──────────────┬───────────────┘  │
│                 │                                       │                  │
│                 ▼                                       ▼                  │
│  ┌──────────────────────────────┐        ┌──────────────────────────────┐  │
│  │ Jaeger-style indexed search  │        │ Tempo-style trace retrieval  │  │
│  │ Better exploratory lookup    │        │ Lower-cost object storage    │  │
│  └──────────────────────────────┘        └──────────────────────────────┘  │
│                                                                            │
│  Managed backends can fit either workflow, but you still own instrumentation│
│  quality, propagation correctness, retention policy, and sampling behavior. │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

| Backend Pattern | Strength | Trade-Off | Best Fit |
|-----------------|----------|-----------|----------|
| Jaeger with indexed storage | Direct search by service, operation, duration, and tags. | More storage and index operations to run and tune. | Teams that frequently search by custom attributes during support or incident work. |
| Grafana Tempo | Cost-efficient storage and strong Grafana correlation. | Trace ID discovery workflow must be designed carefully. | Teams already using Prometheus, Grafana, and Loki at significant trace volume. |
| Zipkin | Simple open-source tracing model with broad historical support. | Less common as a primary new platform choice at large scale. | Smaller systems, legacy Zipkin instrumentation, or educational environments. |
| Managed tracing service | Reduced backend operations and cloud integration. | Pricing, data residency, and vendor-specific workflow constraints. | Teams that prefer buying storage and UI operations over running them. |
| OpenTelemetry Collector plus multiple exporters | Flexible routing to several destinations. | More policy design and collector capacity planning. | Migration periods, hybrid environments, and teams separating hot and cold trace paths. |

A practical architecture puts the OpenTelemetry Collector between services and the backend. The collector receives OTLP from applications, batches spans, applies processors, and exports traces to storage. It can also redact attributes, drop noisy spans, add Kubernetes metadata, perform tail sampling, and route different traces to different destinations. This keeps application teams focused on instrumentation while platform teams manage policy centrally.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION TRACE COLLECTION PATH                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────┐    OTLP     ┌──────────────────────┐    OTLP/Native      │
│  │ checkout-api │────────────▶│ OpenTelemetry        │─────────────────┐   │
│  └──────────────┘             │ Collector Gateway    │                 │   │
│                               │                      │                 │   │
│  ┌──────────────┐    OTLP     │ receivers: otlp      │                 ▼   │
│  │ payment-api  │────────────▶│ processors: batch    │        ┌────────────┐│
│  └──────────────┘             │ processors: redact   │        │ Jaeger or  ││
│                               │ processors: sampling │        │ Tempo      ││
│  ┌──────────────┐    OTLP     │ exporters: backend   │        └────────────┘│
│  │ worker       │────────────▶│                      │                       │
│  └──────────────┘             └──────────────────────┘                       │
│                                                                            │
│  Applications should not each invent their own retry, sampling, redaction,  │
│  or backend routing behavior when the collector can centralize that policy. │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

A minimal Jaeger all-in-one deployment is useful for development and workshops. It stores data in memory by default, exposes the UI, and accepts OTLP when enabled. It is not a production architecture, because it has one pod, ephemeral storage, and no durable index. Its value is speed: learners can send spans, open a UI, and see trace structure without deploying a storage cluster.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tracing
---
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
          image: jaegertracing/all-in-one:1.57
          ports:
            - name: ui
              containerPort: 16686
            - name: otlp-grpc
              containerPort: 4317
            - name: otlp-http
              containerPort: 4318
            - name: thrift-http
              containerPort: 14268
          env:
            - name: COLLECTOR_OTLP_ENABLED
              value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: tracing
spec:
  selector:
    app: jaeger
  ports:
    - name: ui
      port: 16686
      targetPort: 16686
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
    - name: otlp-http
      port: 4318
      targetPort: 4318
    - name: thrift-http
      port: 14268
      targetPort: 14268
```

A minimal Tempo deployment is also useful for development, but the mental model is different. Tempo is happiest when you can find trace IDs from another signal, so the surrounding Grafana, Prometheus, and Loki configuration matters more. For a lab, local filesystem storage is acceptable. For production, object storage and separate scalable components are the normal direction, with careful retention and query planning.

```yaml
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

    ingester:
      trace_idle_period: 10s
      max_block_duration: 5m

    compactor:
      compaction:
        block_retention: 48h

    storage:
      trace:
        backend: local
        local:
          path: /var/tempo/traces
        wal:
          path: /var/tempo/wal
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
          image: grafana/tempo:2.5.0
          args:
            - -config.file=/etc/tempo/tempo.yaml
          ports:
            - name: http
              containerPort: 3200
            - name: otlp-grpc
              containerPort: 4317
            - name: otlp-http
              containerPort: 4318
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
  selector:
    app: tempo
  ports:
    - name: http
      port: 3200
      targetPort: 3200
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
    - name: otlp-http
      port: 4318
      targetPort: 4318
```

TraceQL gives Tempo users a query language for finding and analyzing traces. You should treat it as an investigation tool rather than a substitute for good service-level metrics. Metrics tell you whether the system is violating an objective. TraceQL helps you inspect the shape of traces matching service, duration, status, or attribute conditions. Logs then explain local details that should not be stuffed into span attributes.

```traceql
{ resource.service.name = "checkout-api" }

{ resource.service.name = "checkout-api" && duration > 750ms }

{ status = error }

{ name = "authorize_payment" && span.payment.provider = "demo-bank" }

{ resource.service.name = "checkout-api" && span.http.response.status_code >= 500 }

{ duration > 250ms } | count() by (resource.service.name)

{ resource.service.name = "payment-api" } | avg(duration) by (name)
```

> **Pause and predict:** Your team already has Prometheus, Grafana, and Loki, but support must often find traces by `order_id` before anyone has a trace ID. Which backend pattern sounds easier for the first search step, and what extra workflow would Tempo need to make the same support case practical?

Jaeger-style indexed search is usually easier for the first search step because the support engineer can search by `order_id` directly if that attribute is indexed and retained. Tempo can still work, but the platform must make `order_id` searchable somewhere else, usually in structured logs that include `trace_id`, or in a metric exemplar workflow that starts from a customer-visible symptom. The important decision is not which tool sounds more modern; it is whether the incident workflow has a reliable way to get from the question to the trace.

### 4. Sampling: Keep The Evidence Without Keeping Everything

Trace volume grows faster than many teams expect. A service receiving one thousand requests per second with dozens of spans per request can generate a large amount of telemetry every day. Storing every trace can be reasonable for a small service, but it becomes expensive and noisy for a busy platform. Sampling is the policy that decides which traces are kept, which traces are dropped, and which traces deserve special treatment.

The first calculation is simple enough to do during design reviews. Multiply requests per second by spans per request by bytes per span, then multiply by time and sampling percentage. This rough math is not a billing guarantee, because compression, indexes, metadata, and backend implementation matter. It is still useful because it forces the team to see whether the default plan is measured in gigabytes, terabytes, or something operationally unrealistic.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                            TRACE VOLUME MATH                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  requests_per_second × spans_per_request × bytes_per_span = bytes_per_second│
│                                                                            │
│  Example:                                                                  │
│                                                                            │
│  2,000 requests/s × 35 spans/request × 900 bytes/span                       │
│  = 63,000,000 bytes/s                                                       │
│  ≈ 60 MB/s before compression and backend overhead                          │
│                                                                            │
│  At full capture, that is several TB each day.                              │
│  At 10 percent head sampling, storage falls sharply but rare failures may   │
│  still be missed unless the sampling policy protects important traces.       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Head-based sampling decides at the beginning of the trace whether the request will be sampled. It is simple, cheap, and easy to propagate because the sampled decision travels in the trace context. The weakness is that the decision happens before the system knows whether the request will be slow, fail, or hit an unusual path. A random decision at the start can discard the one trace that would have explained the incident.

Tail-based sampling waits until enough of the trace has arrived to make a smarter decision. The collector can keep traces with errors, traces above a latency threshold, traces for important routes, or traces for selected tenants. The cost is that the collector must receive and buffer many traces before deciding, which uses memory and adds operational complexity. Tail sampling is powerful, but it is not free.

| Sampling Strategy | Decision Time | Keeps Errors Reliably | Cost Profile | Good Use |
|-------------------|---------------|-----------------------|--------------|----------|
| Always on | No sampling decision; keep everything. | Yes. | Highest storage and backend load. | Low-volume services, temporary incident windows, regulated audit paths. |
| Head-based probabilistic | At trace start. | Not reliably, unless error volume is high enough by chance. | Lowest collection overhead. | Broad baseline visibility for high-volume normal traffic. |
| Parent-based head sampling | At trace start, respecting upstream decision. | Not reliably by itself. | Low overhead with consistent trace trees. | Multi-service systems where all spans in a sampled trace should stay together. |
| Tail-based status policy | After observing spans. | Yes, when error status is set correctly. | Higher collector memory and processing. | Production incidents and services with rare but important failures. |
| Tail-based latency policy | After observing duration. | Captures slow traces, not all errors. | Higher collector memory and processing. | SLO investigations and performance regression analysis. |
| Hybrid policy | Combination of rules. | Yes, if rules prioritize errors and critical paths. | Balanced but requires tuning. | Mature platforms with both cost pressure and incident requirements. |

A good production policy usually combines several rules. Keep all traces with error status. Keep traces above a latency threshold tied to the user-facing service objective. Keep a higher percentage for critical routes such as checkout, login, or payment. Sample a smaller percentage of routine successful traffic. Revisit the thresholds after real incidents, because sampling policy should reflect the failures your organization actually needs to investigate.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch: {}

  tail_sampling:
    decision_wait: 10s
    num_traces: 50000
    policies:
      - name: keep-errors
        type: status_code
        status_code:
          status_codes:
            - ERROR

      - name: keep-slow-checkout
        type: latency
        latency:
          threshold_ms: 1000

      - name: keep-critical-routes
        type: string_attribute
        string_attribute:
          key: http.route
          values:
            - /checkout/{cart_id}
            - /payment/{payment_id}

      - name: sample-normal-traffic
        type: probabilistic
        probabilistic:
          sampling_percentage: 10

exporters:
  otlp/jaeger:
    endpoint: jaeger.tracing.svc.cluster.local:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers:
        - otlp
      processors:
        - tail_sampling
        - batch
      exporters:
        - otlp/jaeger
```

Sampling depends on correct span status and attributes. If application code catches an exception, logs it, returns a fallback, and never marks the span as error, a tail-sampling error policy may drop the trace. If the route attribute contains raw IDs instead of route templates, policies become noisy and expensive. If services disagree on propagation format, the collector sees fragments rather than complete traces. Sampling is therefore not just a collector problem; it is an instrumentation quality problem.

> **Stop and think:** A team says, "We sample ten percent of all traces, so we should have enough data." Their production error rate is tiny but business-critical, and some failures happen only once every few minutes. What would you challenge in their reasoning, and what sampling rule would you add first?

The weak assumption is that random coverage guarantees diagnostic coverage. Ten percent of normal traffic may be excellent for aggregate latency exploration, but it can still miss rare errors. The first rule to add is usually "keep all traces with error status," followed by "keep all traces above the user-facing latency threshold." Only after protecting important traces should the team tune the percentage for ordinary successful traffic.

### 5. Correlation: Metrics Tell You When, Traces Tell You Where, Logs Tell You Why

Observability becomes much stronger when the three major signals share identifiers. Metrics are the fastest way to notice a broad symptom, such as elevated latency or error rate. Traces show where a specific request spent time or crossed a failing dependency. Logs provide local detail, such as the exact exception message, retry count, database lock, or business rule decision. Correlation means you can move between these signals without starting the investigation over each time.

The best incident workflow often starts with metrics because metrics are compact and objective-oriented. A latency alert points to a service-level objective burn, a route, or a dependency. An exemplar can attach a trace ID to a specific metric observation, letting an engineer jump from a slow histogram bucket to a real trace. The trace then identifies the suspicious span, and logs filtered by `trace_id` reveal the local details around that span.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                         CORRELATED DEBUGGING FLOW                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. METRIC                                                                  │
│     checkout latency p95 exceeds objective for route /checkout/{cart_id}    │
│     exemplar includes trace_id=7d3f0d9e8c1a4b3a9c8f1e2d3c4b5a60             │
│                                      │                                     │
│                                      ▼                                     │
│  2. TRACE                                                                   │
│     same trace_id shows checkout-api → payment-api → bank-http timeout      │
│     payment branch explains most of the request duration                    │
│                                      │                                     │
│                                      ▼                                     │
│  3. LOGS                                                                    │
│     logs filtered by trace_id show retry exhaustion and provider response   │
│     local exception message explains the failure mechanism                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

For logs, the minimum useful practice is to include `trace_id` and `span_id` in structured log records. Application frameworks can often inject these fields automatically when logging occurs inside an active span. The fields should be plain strings that Loki, Elasticsearch, or another log backend can parse and filter. Avoid hiding trace IDs inside unstructured messages, because incident responders should not need regular-expression archaeology while customers are waiting.

For metrics, exemplars are the bridge from aggregate measurement to a specific trace. A histogram records many observations, while an exemplar points to one representative trace for a particular bucket or sample. Exemplars are especially valuable for high-latency requests because they let an engineer move from "p99 is bad" to "this exact p99 request waited on this exact dependency." Not every dashboard needs exemplars, but latency and error dashboards are strong candidates.

```python
from prometheus_client import Histogram
from opentelemetry import trace

request_duration = Histogram(
    "checkout_request_duration_seconds",
    "Checkout request duration in seconds",
    ["route", "method"],
)


def record_checkout_duration(route: str, method: str, seconds: float) -> None:
    span = trace.get_current_span()
    context = span.get_span_context()

    if context.is_valid:
        trace_id = format(context.trace_id, "032x")
        request_duration.labels(route=route, method=method).observe(
            seconds,
            exemplar={"trace_id": trace_id},
        )
    else:
        request_duration.labels(route=route, method=method).observe(seconds)
```

A common senior-level design question is which attributes belong on spans, logs, and metrics. Put low-cardinality dimensions needed for aggregation on metrics, such as route, method, status class, and service. Put request-path details needed to understand one operation on spans, such as database system, queue name, retry count, peer service, and sanitized business operation. Put verbose local details in logs, especially full error messages and structured context that would create high-cardinality span attributes.

| Signal | Best At | Should Include | Should Avoid |
|--------|---------|----------------|--------------|
| Metrics | Alerting, trends, SLOs, and aggregate comparison. | Low-cardinality labels such as service, route, method, and status class. | User IDs, order IDs, stack traces, and unbounded labels. |
| Traces | Request path, timing, dependency shape, and causal relationships. | Service name, operation name, status, route template, dependency attributes, and trace ID. | Huge payloads, secrets, and spans for every tiny helper call. |
| Logs | Local details, exceptions, retries, decisions, and audit-style facts. | Trace ID, span ID, severity, message, error type, and structured context. | Being the only place where cross-service request identity exists. |

Trace context can also cross asynchronous boundaries, but it usually needs explicit attention. HTTP libraries commonly propagate headers automatically once instrumented. Messaging systems vary by client and instrumentation maturity, so a producer may need to inject context into message headers and a consumer may need to extract it before starting work. If this is missing, the producer trace and consumer trace become disconnected, which is exactly when teams lose visibility into background workflows.

```python
from opentelemetry import propagate, trace

tracer = trace.get_tracer("order-worker")


def publish_order_created(producer, topic: str, order: bytes) -> None:
    carrier: dict[str, str] = {}
    propagate.inject(carrier)

    headers = [(key, value.encode("utf-8")) for key, value in carrier.items()]

    with tracer.start_as_current_span("publish order.created"):
        producer.send(topic, value=order, headers=headers)


def consume_order_created(message) -> None:
    carrier = {key: value.decode("utf-8") for key, value in message.headers}
    context = propagate.extract(carrier)

    with tracer.start_as_current_span("process order.created", context=context):
        process_order(message.value)
```

The careful part is privacy and data minimization. Trace data often travels farther and is retained differently from application logs. Do not put secrets, tokens, full addresses, payment details, or sensitive personal data into span attributes. If a support workflow needs to find traces by business identifiers, prefer stable internal IDs that are permitted by your data policy, and consider hashing or redaction at the collector. Tracing is evidence, and evidence needs governance.

### 6. Production Operations: Make Tracing Boring Before The Incident

Production tracing fails when it is treated as a one-time instrumentation project. Services change, libraries change, routes change, and new communication patterns appear. A platform team needs trace quality checks just like it needs health checks and SLO reviews. The goal is that every important user journey has enough trace coverage before the outage, not after a vice president asks why the dashboard is green while customers are angry.

Start by defining trace coverage for critical journeys. A checkout journey might require spans for gateway entry, authentication, cart read, inventory reservation, payment authorization, order persistence, event publication, and notification enqueue. A deployment is not "traced" merely because one service emits spans. The journey is traced when the most important branches and failure modes are visible end to end with useful names and attributes.

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                     CHECKOUT TRACE COVERAGE CHECKLIST                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  api-gateway                                                               │
│    └── checkout-api                                                        │
│        ├── auth-service                                                    │
│        ├── cart-store                                                      │
│        ├── inventory-api                                                   │
│        │   └── inventory-db                                                │
│        ├── payment-api                                                     │
│        │   └── external-bank                                               │
│        ├── order-db                                                        │
│        └── message-broker publish order.created                            │
│                                                                            │
│  Coverage is acceptable only when critical boundaries appear in one trace,  │
│  error status is recorded, and logs can be filtered by the same trace ID.   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Set service resource attributes consistently. `service.name` should be stable and human-readable. `service.version` should let you compare traces before and after a deploy. `deployment.environment`, `k8s.namespace.name`, and cluster attributes help separate production from staging and one cluster from another. Without consistent resource attributes, trace queries become brittle and incident responders waste time guessing which workload emitted a span.

Use route templates instead of raw paths. The attribute `http.route=/checkout/{cart_id}` is useful because many requests aggregate under one route. The attribute `http.target=/checkout/9f31a2` is useful in logs but dangerous as a metric or high-cardinality span search dimension. The same principle applies to database statements, queue names, tenant identifiers, and user identifiers. Useful observability data is descriptive without being unbounded.

Plan collector capacity as part of the platform, not as a sidecar afterthought. Tail sampling needs memory because traces must wait for a decision. Batching needs CPU and network capacity. Redaction processors need testing so they remove sensitive fields without deleting the attributes responders need. Exporters need retry behavior that does not back up indefinitely when the backend is down. The collector is now on the telemetry path for many services, so it deserves operational ownership.

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 1024
    spike_limit_mib: 256

  attributes/redact:
    actions:
      - key: http.request.header.authorization
        action: delete
      - key: user.email
        action: delete
      - key: payment.card_number
        action: delete

  k8sattributes:
    auth_type: serviceAccount
    extract:
      metadata:
        - k8s.namespace.name
        - k8s.pod.name
        - k8s.deployment.name

  batch:
    timeout: 5s
    send_batch_size: 8192
```

Finally, make trace review part of incident review and service readiness. After a major incident, ask which trace would have shortened diagnosis and whether it existed before the incident. During service launch, ask whether the service propagates context over every outbound protocol it uses. During dependency changes, ask whether new clients are instrumented. These are engineering questions, not dashboard polish questions, because the quality of traces directly affects mean time to understand.

---

## Did You Know?

- **W3C Trace Context made tracing portable across vendors**: the `traceparent` header lets services written in different languages and instrumented by different libraries stay in the same trace when propagation is configured correctly.
- **Trace volume is usually dominated by successful requests**: without sampling rules that protect errors and slow paths, a platform can spend most of its trace budget storing routine traffic while missing rare failures.
- **A disconnected trace can be more misleading than no trace**: engineers may believe a dependency was never called when the real problem is broken propagation at an HTTP, proxy, or message boundary.
- **The OpenTelemetry Collector is often the production control point**: teams use it to batch, redact, enrich, sample, and route traces without requiring every application team to reimplement those policies.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---------|--------------|-----------------|
| Setting no stable `service.name` | Traces become hard to group, query, and assign to the owning team during incidents. | Set `OTEL_SERVICE_NAME` or equivalent resource attributes in every workload and enforce naming standards. |
| Recording spans without propagation | Each service appears to have traces, but request paths break at service boundaries. | Verify `traceparent` injection and extraction for HTTP, gRPC, proxies, and message clients. |
| Sampling only random successful traffic | Rare errors and slow requests can be discarded before anyone knows they mattered. | Use tail or hybrid sampling rules that keep errors, slow requests, and critical routes. |
| Adding high-cardinality span attributes | Storage and query systems become expensive, noisy, and sometimes unstable. | Use route templates and bounded dimensions on spans; put detailed per-request values in structured logs when policy allows. |
| Treating the backend as the whole tracing system | A Jaeger or Tempo UI may be deployed while instrumentation quality remains poor. | Own the full path: SDKs, propagation, collector policy, storage, query, dashboards, and operational review. |
| Marking errors only in logs | Tail sampling and trace search may miss the failing request because span status looks successful. | Set span status to error and record exceptions when the operation fails or returns an error response. |
| Instrumenting every helper function | Traces become unreadable and expensive without improving incident diagnosis. | Span service boundaries, dependency calls, slow operations, retries, and business decisions that explain request behavior. |
| Putting secrets or sensitive data in attributes | Trace data can spread to backends, dashboards, exports, and longer retention stores. | Redact at source and collector, and define an allowlist for business identifiers permitted in telemetry. |

---

## Quiz

### Question 1

Your team deploys OpenTelemetry to five services. Each service now emits spans, but a request from `frontend` to `checkout` to `payment` appears as three separate traces in Jaeger. During the incident review, someone says, "Tracing is installed, so the backend must be broken." What do you check first, and why?

<details>
<summary>Show Answer</summary>

Check context propagation before blaming the backend. The likely failure is that one or more outbound clients are not injecting `traceparent`, or one or more inbound handlers are not extracting it. Confirm this by inspecting an actual request between services and checking whether the `traceparent` header leaves the caller and arrives at the receiver. If spans exist but trace IDs differ across services, instrumentation is present but propagation is broken. The backend can only connect spans that share trace context.
</details>

### Question 2

A checkout trace has a root span duration of 1.8 seconds. The visible child spans show authentication at 20 ms, inventory at 70 ms, payment at 150 ms, and order storage at 90 ms. There is still more than one second unaccounted for inside the checkout service span. How would you investigate the missing time?

<details>
<summary>Show Answer</summary>

Treat the missing time as uninstrumented work inside the checkout service. First, compare timestamps to locate where the gap appears between child spans. Then inspect code around that region for CPU-heavy serialization, synchronous waits, lock contention, retry loops, DNS resolution, garbage collection, or uninstrumented I/O. Add one or two manual spans around the suspected business operations rather than instrumenting every helper function. Also check runtime logs and profiles, because traces show where time disappeared but profiles may explain why CPU or memory behavior caused it.
</details>

### Question 3

A platform currently stores every trace from a high-volume API. Storage cost is rising quickly, but the on-call team insists that dropping traces will make incidents harder. Design a sampling strategy that protects debugging value while reducing cost.

<details>
<summary>Show Answer</summary>

Use a hybrid strategy rather than random-only sampling. Keep all traces with error status, keep traces above the service latency objective, and keep a higher percentage for critical routes such as checkout, login, and payment. Then sample ordinary successful traffic at a lower percentage. This preserves evidence for failures and slow paths while reducing the storage consumed by routine successful requests. The plan also requires accurate span status and route attributes; otherwise the collector cannot reliably identify the traces that deserve retention.
</details>

### Question 4

Support receives a complaint that order `A123` failed, but the customer did not provide a timestamp precise enough to search a narrow incident window. Your organization uses Tempo as the primary trace store. What workflow would let support find the trace without direct indexed trace search by order ID?

<details>
<summary>Show Answer</summary>

The practical workflow is to search structured logs for the order ID, because logs can retain business identifiers and include `trace_id`. Once support finds a log line for order `A123`, they copy the trace ID into Tempo and inspect the trace. This requires applications to include `trace_id` in structured logs and to log permitted business identifiers consistently. If the organization does not want raw order IDs in logs, it can use an approved internal identifier or hashed value, but the lookup path must exist before the incident.
</details>

### Question 5

A payment service catches provider exceptions, returns a fallback response, and logs an error message. The trace still shows the payment span as successful. Later, tail sampling drops many of these traces because it keeps only error traces and slow traces. What change should the service team make?

<details>
<summary>Show Answer</summary>

The service should mark the relevant span with error status and record the exception when the provider call fails, even if the service returns a controlled fallback. Logs alone are not enough because the sampling policy makes decisions from span data. The team should also add attributes that distinguish fallback behavior, such as `payment.fallback=true`, if that attribute is bounded and allowed by policy. After the change, a tail-sampling error policy can retain these traces for investigation.
</details>

### Question 6

A team adds `customer_id` and full request URLs as span attributes to make traces easier to search. Within a week, the tracing backend becomes expensive and query performance worsens. How do you preserve diagnostic value without keeping the damaging attribute pattern?

<details>
<summary>Show Answer</summary>

Replace unbounded attributes with bounded and policy-approved fields. Use route templates such as `/checkout/{cart_id}` instead of full URLs, and avoid raw customer identifiers on spans unless the data policy explicitly permits them and the backend can handle the cardinality. Put detailed request identifiers in structured logs with `trace_id`, or use hashed/internal IDs if support workflows require lookup. The goal is to keep traces useful for path and timing analysis while moving high-cardinality details to a signal designed for that lookup pattern.
</details>

### Question 7

Your service publishes an `order.created` message to Kafka, and a worker consumes it. The producer trace ends at `publish order.created`, while the consumer creates a new trace starting at `process order.created`. What implementation change connects the two traces, and what should you verify after deploying it?

<details>
<summary>Show Answer</summary>

Inject trace context into the message headers when producing, and extract that context from headers before starting the consumer span. Many HTTP clients handle propagation automatically after instrumentation, but message clients often need explicit instrumentation or client-specific support. After deploying the change, verify that the producer publish span and consumer processing span share the same trace ID and have a sensible causal relationship. Also confirm that retries and dead-letter handling preserve or intentionally link context according to your platform policy.
</details>

### Question 8

An incident starts with a Prometheus alert: checkout p95 latency is above the objective. Grafana shows exemplars on the latency histogram, Loki stores structured logs, and Tempo stores traces. Walk through the investigation path you would use and explain why that order is efficient.

<details>
<summary>Show Answer</summary>

Start with the metric because it identifies the symptom, affected route, and time window. Use the exemplar on a high-latency bucket to jump to a representative trace in Tempo. In the trace, find the longest branch or error span to identify the likely dependency or operation causing latency. Then filter Loki logs by the same trace ID to inspect local details such as retry messages, exception types, provider responses, or database lock warnings. This order is efficient because each signal narrows the question: metrics say when and how broad, traces say where in the request path, and logs say why the local operation behaved that way.
</details>

---

## Hands-On Exercise

### Scenario: Trace A Checkout Request Across A Kubernetes Lab

You are the platform engineer supporting a team that is preparing a checkout service for production. The service owners say they have "added tracing" because a demo UI shows spans. Your job is to verify the tracing path in Kubernetes, generate normal and slow traffic, inspect a trace, and decide whether the trace is useful enough for incident response. The exercise uses a local kind cluster targeting Kubernetes 1.35+ behavior and a small Jaeger deployment for fast feedback.

This exercise uses `kubectl` for the first command and then uses `k` as a shorter alias. If your shell does not already define it, run `alias k=kubectl` before the remaining commands. The alias is only a typing convenience; every command works the same with `kubectl`.

### Step 1: Create The Lab Cluster

```bash
kind create cluster --name tracing-lab --image kindest/node:v1.35.0
kubectl cluster-info --context kind-tracing-lab
alias k=kubectl
```

Success criteria for this step:

- [ ] The `tracing-lab` kind cluster exists.
- [ ] `kubectl cluster-info` returns a reachable Kubernetes control plane.
- [ ] You can run `k get nodes` and see at least one Ready node.

### Step 2: Deploy Jaeger For Trace Storage And UI

```bash
k apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: tracing
---
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
          image: jaegertracing/all-in-one:1.57
          ports:
            - name: ui
              containerPort: 16686
            - name: otlp-grpc
              containerPort: 4317
            - name: otlp-http
              containerPort: 4318
            - name: thrift-http
              containerPort: 14268
          env:
            - name: COLLECTOR_OTLP_ENABLED
              value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: tracing
spec:
  selector:
    app: jaeger
  ports:
    - name: ui
      port: 16686
      targetPort: 16686
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
    - name: otlp-http
      port: 4318
      targetPort: 4318
    - name: thrift-http
      port: 14268
      targetPort: 14268
EOF
```

```bash
k -n tracing wait --for=condition=available deployment/jaeger --timeout=180s
k -n tracing get pods -l app=jaeger
```

Success criteria for this step:

- [ ] The `tracing` namespace exists.
- [ ] The Jaeger deployment is Available.
- [ ] The Jaeger service exposes UI and OTLP ports.

### Step 3: Deploy A Traced Demo Application

The HotROD demo is intentionally small but useful for trace reading because one user action creates several spans. It is not a model for production code structure, but it gives you a working trace source without building a custom image. The important platform lesson is to inspect whether the trace tree helps you answer where latency appears.

```bash
k apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hotrod
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hotrod
  template:
    metadata:
      labels:
        app: hotrod
    spec:
      containers:
        - name: hotrod
          image: jaegertracing/example-hotrod:1.57
          args:
            - all
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: JAEGER_ENDPOINT
              value: http://jaeger.tracing.svc.cluster.local:14268/api/traces
---
apiVersion: v1
kind: Service
metadata:
  name: hotrod
  namespace: default
spec:
  selector:
    app: hotrod
  ports:
    - name: http
      port: 8080
      targetPort: 8080
EOF
```

```bash
k wait --for=condition=available deployment/hotrod --timeout=180s
k get pods -l app=hotrod
```

Success criteria for this step:

- [ ] The `hotrod` deployment becomes Available.
- [ ] The service `hotrod` exists on port 8080.
- [ ] The pod logs do not show repeated exporter connection failures.

### Step 4: Generate Traffic And Open The UIs

```bash
k port-forward svc/hotrod 8080:8080 > /tmp/hotrod-port-forward.log 2>&1 &
k -n tracing port-forward svc/jaeger 16686:16686 > /tmp/jaeger-port-forward.log 2>&1 &
sleep 3
```

```bash
curl -s http://127.0.0.1:8080/dispatch?customer=123
curl -s http://127.0.0.1:8080/dispatch?customer=392
curl -s http://127.0.0.1:8080/dispatch?customer=731
```

Open `http://127.0.0.1:16686` in a browser and search for traces from the HotROD services. If the UI does not show traces immediately, generate a few more requests and widen the time range. Jaeger all-in-one is in-memory and local, so the feedback loop should be quick once the application is exporting correctly.

Success criteria for this step:

- [ ] You can call the demo application through the local port-forward.
- [ ] You can open the Jaeger UI through the local port-forward.
- [ ] At least one trace appears after generating traffic.

### Step 5: Read One Trace Like An Incident Responder

Pick one trace and answer the following questions in your own notes. Do not just admire the waterfall view. Treat the trace as evidence in an incident where a customer says dispatch is slow and the service teams disagree about responsibility.

- [ ] Which span is the root span, and what user-visible operation does it represent?
- [ ] Which branch consumes the most time, and which downstream dependency sits on that branch?
- [ ] Are there errors, retries, or suspicious gaps between child spans?
- [ ] Do the service names make ownership clear enough for an on-call handoff?
- [ ] If this were a production trace, which log query would you run next using the trace ID?

### Step 6: Break The Mental Model On Purpose

Now imagine that one service boundary stopped propagating context. You do not need to edit the demo image to practice the reasoning. Instead, inspect the trace and identify which edge would hurt most if it became disconnected. For example, losing context between an API service and a downstream dependency would make the downstream operation appear as a separate trace, weakening the evidence chain during an incident.

Write a short diagnosis using this format:

```text
If propagation broke between <caller> and <callee>, Jaeger would show <expected symptom>.
The first thing I would inspect is <header/client/proxy/instrumentation point>.
The operational impact would be <why this makes incident response harder>.
```

Success criteria for this step:

- [ ] You can describe the difference between missing spans and disconnected traces.
- [ ] You can name the boundary where `traceparent` injection or extraction would need verification.
- [ ] You can explain why a backend cannot repair missing propagation after the fact.

### Step 7: Design A Sampling Policy For The Demo Scenario

Assume this dispatch application becomes a real production service with high request volume. Design a sampling policy in prose, then map it to collector rules. Your answer should keep all errors, keep slow dispatch traces, keep more traces for important customer-facing routes, and sample routine successful traffic at a lower percentage.

Use this starter configuration and adjust the route names or thresholds to match your reasoning:

```yaml
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 25000
    policies:
      - name: keep-errors
        type: status_code
        status_code:
          status_codes:
            - ERROR

      - name: keep-slow-dispatch
        type: latency
        latency:
          threshold_ms: 1000

      - name: keep-dispatch-route
        type: string_attribute
        string_attribute:
          key: http.route
          values:
            - /dispatch

      - name: sample-normal-traffic
        type: probabilistic
        probabilistic:
          sampling_percentage: 10
```

Success criteria for this step:

- [ ] Your policy explains why random-only sampling is not enough.
- [ ] Your policy keeps error traces before sampling ordinary successful traffic.
- [ ] Your policy connects latency thresholds to user-facing investigation needs.
- [ ] Your policy avoids relying on high-cardinality identifiers as the primary sampling dimension.

### Step 8: Cleanup

```bash
kind delete cluster --name tracing-lab
```

Final success criteria for the exercise:

- [ ] You deployed a tracing backend into Kubernetes.
- [ ] You generated traces from an application and found them in the UI.
- [ ] You interpreted a trace using parent-child structure, duration, service names, and status.
- [ ] You explained how broken propagation would appear and where to inspect it.
- [ ] You designed a sampling policy that preserves incident evidence while controlling cost.
- [ ] You can connect the worked example instrumentation steps to the Kubernetes lab investigation.

---

## Next Module

Continue to [GitOps & Deployments Toolkit](/platform/toolkits/cicd-delivery/gitops-deployments/) to learn how observable services are delivered and operated through declarative deployment workflows.

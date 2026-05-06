---
title: "Module 1.1: OTel API & SDK Deep Dive"
slug: k8s/otca/module-1.1-otel-sdk-deep-dive
sidebar:
  order: 2
revision_pending: false
---

> **Complexity**: `[COMPLEX]` - Core domain, 46% of OTCA exam weight
>
> **Time to Complete**: 90-120 minutes
>
> **Prerequisites**: Basic familiarity with distributed systems, HTTP request flow, service-to-service calls, and either Python or Go

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Design** an OpenTelemetry SDK pipeline that routes traces, metrics, and logs through the correct providers, processors, readers, and exporters for a production service.
2. **Debug** broken trace continuity by analyzing span kinds, parent-child relationships, W3C TraceContext headers, propagators, and baggage usage.
3. **Implement** manual instrumentation that adds business-relevant spans, attributes, events, exceptions, metrics, and resources without duplicating what auto-instrumentation already provides.
4. **Evaluate** tradeoffs between synchronous and asynchronous metric instruments, cumulative and delta temporality, console and OTLP exporters, and simple and batch processing.
5. **Refactor** reference-style SDK snippets into runnable input-to-solution instrumentation patterns that you can adapt for real services and OTCA exam scenarios.

---

## Why This Module Matters

Hypothetical scenario: a platform team at a payment company has a familiar observability problem: every service emits telemetry, but no two services describe the same operation the same way.
The Java checkout service used a vendor-specific tracer, the Python fraud service logged request IDs by hand, and the Go payment gateway exported Prometheus metrics with labels that did not match the trace names.
When a production incident crossed all three services, the on-call engineer spent more time translating telemetry than debugging the customer-facing failure.

Their first attempted fix was to standardize on a single backend.
That helped dashboards look consistent, but it did not solve the deeper problem because instrumentation was still coupled to one vendor's library and one export format.
When the company later moved from one trace backend to another, teams had to touch application code, redeploy services, and re-check every custom integration.
The migration risk came from a design mistake: the telemetry pipeline was embedded in application logic instead of being treated as a configurable SDK boundary.

OpenTelemetry changes that boundary.
Application code creates spans, metrics, logs, attributes, and context using a stable API, while the SDK decides how telemetry is sampled, batched, aggregated, and exported.
That separation is the reason a team can keep business instrumentation in source code while changing exporters, collectors, sampling policies, or backends through configuration.
For OTCA, this is not trivia; it is the mechanism behind almost every scenario question in the API and SDK domain.

This module teaches the SDK from the inside out.
You will first build the mental model for provider pipelines, then inspect spans and metrics as data structures, then connect that data across service boundaries through propagation.
After that, you will turn reference snippets into worked examples where an uninstrumented service becomes a traceable and measurable service step by step.
The goal is not to memorize class names; the goal is to recognize where telemetry is created, enriched, buffered, transformed, and shipped.

A senior practitioner does not ask only, "Can I emit a span?"
They ask, "Will this span help the next engineer isolate the failure without reading the source?"
They also ask whether a metric will aggregate correctly, whether a resource attribute belongs on every signal, whether baggage leaks sensitive data, and whether exporter configuration can change without rebuilding the service.
That is the level this module targets.
Although the OTCA exam is not a Kubernetes operations test, most production OpenTelemetry deployments you meet in this curriculum will run beside Kubernetes 1.35+ workloads, collectors, sidecars, gateways, and admission-controlled namespaces.
That matters because SDK decisions made inside application code become platform behaviors once hundreds of pods inherit the same environment variables and export to the same collector fleet.
If one service chooses unstable metric attributes or leaks baggage, the damage is not limited to a local library choice; it becomes a cluster-wide cost, privacy, and incident-response problem.
This module therefore treats the SDK as the first control point in a larger observability system.

---

## Core Content

## Part 1: The SDK Pipeline Mental Model

OpenTelemetry has many language-specific classes, but the model is deliberately repetitive.
For each signal, application code talks to an API object, the SDK provider owns configuration, a processor or reader prepares data, and an exporter sends data somewhere else.
Once you recognize that shape, a new language SDK becomes easier to read because the names change less than the responsibilities.
The provider is the boundary between "my code creates telemetry" and "the SDK manages telemetry."

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                      One OpenTelemetry SDK Boundary                         │
│                                                                            │
│  Application code                                                           │
│  creates telemetry                                                          │
│        │                                                                    │
│        ▼                                                                    │
│  ┌──────────────┐      ┌──────────────────┐      ┌──────────────────────┐  │
│  │ API object   │─────▶│ SDK provider     │─────▶│ Processor or reader  │  │
│  │ tracer/meter │      │ owns resource    │      │ batches or collects  │  │
│  └──────────────┘      └──────────────────┘      └──────────┬───────────┘  │
│                                                              │              │
│                                                              ▼              │
│                                                    ┌──────────────────────┐ │
│                                                    │ Exporter sends data  │ │
│                                                    │ to console, OTLP,    │ │
│                                                    │ Prometheus, backend  │ │
│                                                    └──────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

The API is intentionally small because instrumentation code should not know much about backend plumbing.
A handler should be able to start a span, set an attribute, record a metric, and keep doing business work.
The SDK provider then applies resource identity, sampling, aggregation, batching, and export policy.
This is the design that lets the same instrumented code run in a laptop demo, a staging namespace, or a production cluster with different export destinations.

| Signal | API Object Used by Code | SDK Owner | Middle Component | Export Destination Examples |
|---|---|---|---|---|
| Traces | `Tracer` | `TracerProvider` | `SpanProcessor` | Console, OTLP, trace backend |
| Metrics | `Meter` | `MeterProvider` | `MetricReader` | Console, OTLP, Prometheus scrape |
| Logs | Logger bridge | `LoggerProvider` | `LogRecordProcessor` | Console, OTLP, log backend |

The trace pipeline is usually the first one learners understand because a span feels concrete.
Your application starts and ends spans, the provider attaches a resource and sampling behavior, the processor decides when ended spans are exported, and the exporter serializes them to a destination.
The most important production choice is almost always the processor, because exporting on the request path can turn observability into latency.
That is why batch processing is the normal production default.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                              TracerProvider                                 │
│                                                                            │
│  Resource: service.name="checkout", deployment.environment="prod"           │
│                                                                            │
│  ┌──────────────┐      ┌──────────────────┐      ┌──────────────────────┐  │
│  │ Tracer       │─────▶│ SpanProcessor    │─────▶│ SpanExporter         │  │
│  │              │      │                  │      │                      │  │
│  │ start span   │      │ Simple: sync     │      │ Console: local debug │  │
│  │ set attrs    │      │ Batch: async     │      │ OTLP: collector      │  │
│  │ add events   │      │                  │      │ Backend: vendor API  │  │
│  │ end span     │      │                  │      │                      │  │
│  └──────────────┘      └──────────────────┘      └──────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

| Span Processor | How It Behaves | Practical Use | Risk If Misused |
|---|---|---|---|
| `SimpleSpanProcessor` | Exports each ended span immediately on the caller path | Local debugging and tiny demos | Adds exporter latency to application requests |
| `BatchSpanProcessor` | Queues ended spans and exports them asynchronously in groups | Production services and load tests | Drops spans if the process crashes before flushing |
| Custom filtering processor | Drops or changes spans before export | Reducing cost or removing unsafe attributes | Can hide failures if filtering is too broad |

A batch processor is not a magic lossless queue.
It has a queue size, a flush interval, and a maximum export batch size, so the tuning question is really about tradeoffs.
A larger queue absorbs bursts but uses more memory, a shorter delay gives fresher traces but increases export overhead, and a larger batch improves throughput but may create bigger export spikes.
For OTCA, focus on the behavior first: batch means asynchronous buffering; simple means synchronous export.

| Batch Setting | Common Environment Variable | What You Tune | Failure Mode When Wrong |
|---|---|---|---|
| Queue size | `OTEL_BSP_MAX_QUEUE_SIZE` | How many ended spans can wait for export | High-cardinality bursts drop spans |
| Flush delay | `OTEL_BSP_SCHEDULE_DELAY` | How often the processor attempts export | Incidents appear late in the backend |
| Batch size | `OTEL_BSP_MAX_EXPORT_BATCH_SIZE` | How many spans go in one export call | Export calls become too small or too bursty |

Metrics use the same provider idea but a different middle component.
A meter creates instruments, instruments record measurements, and the reader decides when collection happens and which temporality the exporter prefers.
This distinction matters because metrics are not shipped one measurement at a time; the SDK aggregates many recordings into sums, histograms, last values, or other forms.
When a metric looks wrong in a backend, the bug is often in instrument choice, aggregation, label cardinality, or temporality rather than in the exporter.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                               MeterProvider                                 │
│                                                                            │
│  Resource: service.name="checkout", service.version="2.4.1"                │
│                                                                            │
│  ┌──────────────┐      ┌──────────────────┐      ┌──────────────────────┐  │
│  │ Meter        │─────▶│ MetricReader     │─────▶│ MetricExporter       │  │
│  │              │      │                  │      │                      │  │
│  │ counter      │      │ Periodic: push   │      │ OTLP: collector      │  │
│  │ histogram    │      │ Prometheus: pull │      │ Console: local debug │  │
│  │ observable   │      │                  │      │ Prometheus endpoint  │  │
│  └──────────────┘      └──────────────────┘      └──────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

| Metric Reader | Collection Model | Best Fit | Design Implication |
|---|---|---|---|
| `PeriodicExportingMetricReader` | Push on an interval | OTLP exporters and collector pipelines | Application initiates exports on schedule |
| Prometheus reader | Pull through a scrape endpoint | Prometheus-native environments | Prometheus controls scrape timing |
| Manual collection reader | Explicit collection trigger | Tests and specialized integrations | Caller must remember to collect |

Logs complete the three-signal picture, but they are easy to misunderstand.
OpenTelemetry usually does not replace the logging API that application teams already use; instead, a bridge connects existing log records into the OTel log pipeline.
That bridge can attach trace context so a log line written inside a request span carries the same trace and span identifiers as the trace data.
This lets logs, metrics, and traces point at the same incident without forcing every team to abandon familiar logging libraries.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                              LoggerProvider                                 │
│                                                                            │
│  ┌──────────────────┐    ┌────────────────────┐    ┌────────────────────┐  │
│  │ Existing logger  │───▶│ OTel log bridge    │───▶│ LogRecordProcessor │  │
│  │                  │    │                    │    │                    │  │
│  │ Python logging   │    │ adds trace context │    │ simple or batch    │  │
│  │ Java Log4j       │    │ maps severity      │    │ filtering possible │  │
│  │ .NET ILogger     │    │ preserves message  │    │                    │  │
│  └──────────────────┘    └────────────────────┘    └─────────┬──────────┘  │
│                                                               │             │
│                                                               ▼             │
│                                                     ┌────────────────────┐  │
│                                                     │ LogExporter        │  │
│                                                     │ console or OTLP    │  │
│                                                     └────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

| Signal | Mature Concept to Know | What Usually Goes Wrong | Debugging Question |
|---|---|---|---|
| Traces | Parent-child span relationships and span kinds | Broken propagation or missing server spans | Do downstream spans share the same trace ID? |
| Metrics | Instrument choice, aggregation, temporality, cardinality | Counters reset unexpectedly or histograms lack useful buckets | Is the backend interpreting the temporality correctly? |
| Logs | Bridge behavior and trace correlation | Logs arrive but cannot be joined to traces | Was the log emitted while a span was current? |
| Baggage | Business context propagated as headers | Sensitive data leaks downstream | Would this value be safe on the wire? |

> **Stop and think:** Your team says "OpenTelemetry is slow" after adding console export to every request in a high-traffic service.
> Before blaming tracing itself, identify which component in the trace pipeline is on the request path and which processor choice would remove most of that overhead.

The answer should point at the simple processor and console exporter combination.
Tracing APIs do add some work, but synchronous export is a much larger problem because it makes every request wait for serialization and output.
A batch processor moves export off the hot path, and an OTLP exporter to a collector usually behaves more like a production architecture.
This is the difference between debugging a symptom and diagnosing the pipeline design.

## Part 2: Span Anatomy and Trace Design

A span is a structured record of work, not just a timer with a name.
It has identity fields that connect it to a trace, timing fields that define duration, a kind that describes communication role, attributes that describe the operation, events that mark notable moments, and status that summarizes the outcome.
If any of those fields are wrong, the trace can still appear in the backend but mislead the engineer reading it.
High-quality instrumentation is therefore a design task, not a decoration task.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                                  Span                                       │
│                                                                            │
│  Identity:    trace_id, span_id, parent_span_id                             │
│  Operation:   name, kind, start_time, end_time                              │
│  Outcome:     status code and optional description                          │
│  Detail:      attributes and timestamped events                             │
│  Context:     links to other traces when parent-child is not correct         │
│  Resource:    service, host, process, deployment, runtime identity           │
└────────────────────────────────────────────────────────────────────────────┘
```

A trace ID groups spans that belong to the same distributed operation.
A span ID identifies one unit of work inside that operation, and a parent span ID describes the tree.
When Service A receives a request and calls Service B, Service B should usually create a server span with the same trace ID and the Service A client span as its parent.
When that continuity breaks, the backend shows two separate traces and the incident timeline becomes harder to reconstruct.

| Field | Scope | Example Value | Design Question |
|---|---|---|---|
| `trace_id` | Whole distributed operation | One checkout request across services | Are related spans grouped together? |
| `span_id` | One span | The database query span | Can another span name this one as parent? |
| `parent_span_id` | Parent-child tree | HTTP client span as parent of server span | Does the timeline show cause and effect? |
| `name` | Operation label | `POST /checkout` or `charge-card` | Would this name group similar work? |
| `kind` | Communication role | `SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER`, `INTERNAL` | Does the span describe a boundary crossing correctly? |

Span kind is one of the most useful small details in a trace because it tells readers what role the service played.
A server span means the service received work, a client span means it called another service or dependency, a producer span means it put work onto a queue, and a consumer span means it processed work from a queue.
Internal spans are still valuable, but they should represent in-process work rather than outbound communication.
Mislabeling outbound calls as internal makes dependency maps and latency breakdowns less useful.

| Span Kind | Use It When | Example | Common Mislabel |
|---|---|---|---|
| `SERVER` | The service receives a request | HTTP handler or gRPC method | Marking an inbound handler as `INTERNAL` |
| `CLIENT` | The service calls another dependency | HTTP client, database query, cache call | Marking a database call as `INTERNAL` |
| `PRODUCER` | The service enqueues or publishes work | Kafka publish or queue send | Treating publish as a generic client call |
| `CONSUMER` | The service receives work from messaging | Worker processing a queue message | Losing the relationship to the producer |
| `INTERNAL` | Work stays inside the process | Validation, pricing calculation, template rendering | Using it for every custom span |

Attributes and resources are different because they answer different questions.
A resource describes the entity producing telemetry, such as the service, deployment environment, version, host, process, or Kubernetes pod.
An attribute describes one operation or one metric data point, such as HTTP method, route, status code, database system, order type, or queue name.
Putting `service.name` on every span attribute instead of on the resource creates noisy telemetry and breaks resource-based grouping.

| Question | Use a Resource When | Use an Attribute When |
|---|---|---|
| Does this describe the process or service? | Yes, set it on the provider resource | No, avoid repeating it per span |
| Does it change per request or operation? | Usually no | Usually yes |
| Does every signal from this SDK share it? | Yes | No |
| Example | `service.name=checkout` | `http.request.method=POST` |
| Example | `deployment.environment=prod` | `http.response.status_code=200` |

Events are useful when a span needs a timeline inside the timeline.
For example, a checkout span may add events for `cart.validated`, `payment.authorized`, and `inventory.reserved`, especially when those steps are too small or too numerous to deserve separate spans.
Exception recording is a special case of events: the SDK records exception type, message, and stack trace as an event.
However, recording an exception event does not automatically prove the span failed in every SDK and configuration; setting error status makes the outcome visible to trace readers and alert rules.

| Span Detail | Best Use | Poor Use | Better Alternative |
|---|---|---|---|
| Attribute | Stable dimensions used for filtering and grouping | Unique IDs with unbounded cardinality everywhere | Use selective attributes and logs for high-cardinality values |
| Event | Moment inside the span timeline | Replacing every child span with events | Use child spans for meaningful nested work |
| Status | Final operation result | Setting error for every handled retry | Set error when the span's operation failed |
| Link | Relationship across traces | Replacing normal parent-child propagation | Use parent-child when one operation directly caused another |

Links are the right tool when a parent-child tree would lie.
A batch worker may process messages that came from several independent requests, so one consumer span cannot have all of those producer spans as parents.
A span link lets the worker say, "this processing is related to those earlier spans," while keeping its own trace structure.
Links are especially important in fan-in, batching, and retry designs where causal relationships are real but not tree-shaped.

> **Pause and predict:** A checkout service receives an HTTP request, creates a `SERVER` span, then calls PostgreSQL and Redis.
> If both dependency calls are marked `INTERNAL`, what will the trace viewer probably hide or misrepresent when someone investigates slow checkout requests?

The trace viewer may fail to show those operations as outbound dependencies, and service maps may understate how much checkout depends on PostgreSQL and Redis.
The spans might still show duration, but the communication role is wrong, so readers lose the boundary-crossing signal.
The correct design is a server span for the inbound request and client spans for the outbound database and cache calls.
Internal spans should be reserved for meaningful in-process work such as pricing or validation.

## Part 3: Metrics That Preserve Meaning

Metrics are easy to emit and easy to ruin.
A counter with the wrong attributes can create too many time series, a gauge used where a histogram belongs can hide latency distribution, and a temporality mismatch can make a healthy service look broken.
The SDK helps by giving you instrument types with specific semantics, but it cannot decide your measurement intent for you.
The first design question is always, "What decision should this metric help someone make?"

Synchronous instruments are called when your code knows that something happened.
A counter increments when a request completes, a histogram records the duration when a handler finishes, and an up-down counter changes when a connection opens or closes.
Asynchronous instruments are callbacks that observe a value that already exists somewhere else, such as queue depth, memory usage, or connection pool size.
Using an asynchronous callback to poll a remote service on every collection interval is a performance and reliability smell.

| Instrument | Sync or Async | Can Decrease | Good Example | Bad Example |
|---|---|---|---|---|
| Counter | Synchronous | No | Total successful checkouts | Current queue depth |
| UpDownCounter | Synchronous | Yes | Active WebSocket connections | Total requests since start |
| Histogram | Synchronous | Not applicable | Request duration or response size | Current CPU percent |
| Observable Counter | Asynchronous | No | CPU time read from the OS | Business event count in request code |
| Observable UpDownCounter | Asynchronous | Yes | Current worker pool size | Latency distribution |
| Observable Gauge | Asynchronous | Yes | Queue depth or temperature | Total completed orders |

Histograms deserve extra attention because they answer questions that averages cannot answer.
If the average checkout duration is acceptable but a small group of customers sees extreme latency, a histogram can preserve that distribution while a simple gauge cannot.
A well-named histogram such as `http.server.request.duration` or `orders.processing.duration` lets dashboards show percentiles, bucket counts, and exemplars.
For performance debugging, histograms are often the bridge from "something got slower" to "which traces should I inspect?"

| Measurement Need | Recommended Instrument | Why It Fits | Example Attribute |
|---|---|---|---|
| Count business events | Counter | Events only move forward | `order.type=standard` |
| Track active work | UpDownCounter | Value increases and decreases | `worker.pool=checkout` |
| Measure latency | Histogram | Distribution matters | `http.route=/checkout` |
| Observe queue depth | Observable Gauge | Value exists outside request flow | `queue.name=orders` |
| Observe total CPU time | Observable Counter | OS counter increases over time | `cpu.state=user` |

Temporality defines what a metric value means over time.
Cumulative temporality reports the total since a starting point, while delta temporality reports the change since the last collection.
If a counter records increments of ten, twenty, and five across three collection windows, cumulative reports ten, thirty, and thirty-five, while delta reports ten, twenty, and five.
Neither is universally better; the backend and reader must agree on interpretation.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         Counter Temporality Example                         │
│                                                                            │
│  Raw increments:        +10          +20          +5                        │
│                                                                            │
│  Cumulative export:      10           30          35                        │
│  Delta export:           10           20           5                        │
│                                                                            │
│  Reader and backend must agree on which row the exported values represent.  │
└────────────────────────────────────────────────────────────────────────────┘
```

| Temporality | What the Exported Value Means | Backend Preference Example | Debugging Symptom |
|---|---|---|---|
| Cumulative | Total since start or reset | Prometheus-style counter interpretation | Reset handling matters during restarts |
| Delta | Change since previous collection | Some StatsD-like or vendor pipelines | Values look too small if read as totals |
| Backend conversion | Collector or backend converts meaning | Mixed estate during migrations | Rate graphs disagree between tools |

Aggregation is the SDK's way of turning many raw measurements into exportable data.
Counters commonly aggregate as sums, gauges as last values, and histograms as bucketed distributions.
This is why a metric instrument is not just a method name; it determines what math will be possible later.
If you record request duration in a counter, no downstream backend can recover a useful latency distribution because the raw shape was lost at collection time.

| Instrument | Typical Aggregation | Useful Dashboard View | Risk to Watch |
|---|---|---|---|
| Counter | Sum | Request rate, error rate, throughput | High-cardinality attributes explode series |
| UpDownCounter | Sum with positive and negative changes | Active sessions or in-flight work | Missing decrement leaves value inflated |
| Histogram | Explicit buckets or exponential buckets | Percentiles and latency heatmaps | Poor buckets hide important ranges |
| Observable Gauge | Last value | Queue depth or current utilization | Callback latency affects collection |

Exemplars connect metrics back to traces.
When a histogram bucket contains a latency spike, an exemplar can attach a sampled trace ID and span ID to one measurement in that bucket.
That lets an engineer click from "the p99 checkout latency spiked" to "here is one trace that contributed to that spike."
Exemplars are not a replacement for traces or metrics; they are a bridge between aggregate behavior and individual request evidence.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         Histogram With Exemplar                             │
│                                                                            │
│  orders.duration bucket 250ms-500ms                                         │
│  count=18                                                                   │
│  exemplar: value=392ms, trace_id=0af7651916cd43dd8448eb211c80319c           │
│                                                                            │
│  Dashboard question: "Which trace explains this slow bucket?"               │
└────────────────────────────────────────────────────────────────────────────┘
```

A metric naming decision should survive operational use.
Names should describe what is measured, units should be explicit, and attributes should be bounded enough to aggregate.
For example, `orders.duration` with unit `ms` and attribute `order.type` is useful, while adding `user.id` to every duration measurement can create one series per user.
High cardinality is not merely expensive; it can make dashboards slow, alerts noisy, and backends drop data.

## Part 4: Context Propagation and Baggage

A distributed trace only works when context crosses process boundaries.
The upstream service must inject context into a carrier such as HTTP headers or message attributes, and the downstream service must extract that context before starting its own span.
When either side forgets its half, the trace tree breaks even though both services may be individually instrumented.
This is why propagation bugs often show up as "we have spans, but they are in separate traces."

```ascii
┌──────────────────────────┐       HTTP request        ┌────────────────────┐
│ Service A: checkout      │──────────────────────────▶│ Service B: payment │
│                          │   traceparent header      │                    │
│ client span: call-payment│                            │ server span: POST  │
│ trace_id: same value     │                            │ trace_id: same     │
│ span_id: parent candidate│                            │ parent: A client   │
└──────────────────────────┘                            └────────────────────┘
```

The W3C TraceContext format is the default propagation standard in modern OpenTelemetry configurations.
The `traceparent` header carries a version, trace ID, parent span ID, and trace flags, while `tracestate` carries vendor-specific state.
In a debugging scenario, you rarely need to recite the header grammar; you need to recognize whether the same trace ID survived the boundary and whether the downstream service used the extracted parent.
That practical interpretation matters more than memorizing field widths.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                          traceparent Header Shape                           │
│                                                                            │
│  traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01      │
│               │  │                                │                │       │
│               │  │                                │                └ flags │
│               │  │                                └ parent span ID          │
│               │  └ trace ID shared across the distributed operation         │
│               └ version                                                    │
└────────────────────────────────────────────────────────────────────────────┘
```

| Propagation Piece | What It Carries | Why It Matters | Debugging Check |
|---|---|---|---|
| `traceparent` | Trace ID, parent span ID, flags | Establishes distributed trace continuity | Same trace ID across services |
| `tracestate` | Vendor or platform-specific state | Preserves backend-specific decisions | Present when a backend requires it |
| Propagator | Injects and extracts context | Connects SDK to carrier format | Same propagator configured on both sides |
| Carrier | HTTP headers or message metadata | Moves context over a boundary | Header or metadata visible on the wire |

Baggage is separate from trace identity.
It carries application context as key-value pairs, and that context travels downstream with requests.
This can be useful for routing, experiment cohort, tenant tier, or other non-sensitive operational hints.
The danger is that baggage is transmitted in headers or metadata, so it must be treated as data visible to downstream systems and infrastructure.

| Baggage Candidate | Good or Bad | Reason | Safer Alternative |
|---|---|---|---|
| `tenant.tier=enterprise` | Good if non-sensitive | Useful for routing or sampling policy | Keep value low-cardinality |
| `user.email=person@example.com` | Bad | Personal data travels downstream | Use internal user category instead |
| `auth.token=secret` | Bad | Credential leakage risk | Never propagate secrets as baggage |
| `experiment.group=B` | Good if bounded | Useful for analysis and debugging | Document allowed values |
| `cart.value=123.45` | Depends | Could be sensitive or high-cardinality | Record as span attribute selectively |

Propagation also behaves differently across synchronous and asynchronous boundaries.
An HTTP call has an obvious request and response, so a client span and downstream server span usually form a clear parent-child relationship.
A message queue may decouple producer and consumer in time, may batch messages, or may retry delivery, so links may be a better representation than a direct parent in some designs.
A strong OTCA answer explains the relationship, not just the mechanism.

> **Stop and think:** A queue consumer processes one batch that contains messages created by several different user requests.
> Would a single parent span accurately represent the batch, or would span links preserve the relationship more honestly?

Span links usually preserve the relationship more honestly because the batch work is related to multiple earlier traces.
Choosing one parent would imply a single causal chain and hide the fan-in nature of the workload.
The consumer can still create a span for batch processing, but links let it reference the producer contexts attached to each message.
This is a good example of trace design serving the reader rather than forcing every workflow into a tree.

## Part 5: SDK Configuration and Export Choices

OpenTelemetry SDKs are configurable through code and environment variables.
Code is useful when an application must construct providers, processors, instruments, or resources directly.
Environment variables are useful when platform teams need consistent behavior across many services without rebuilding each application.
The practical rule is to keep business instrumentation in code and keep deployment-specific export decisions in configuration whenever possible.

| Configuration Area | Programmatic Example | Environment Example | Prefer Environment When |
|---|---|---|---|
| Service identity | Resource attributes in SDK setup | `OTEL_SERVICE_NAME` | Each deployment sets its own name |
| OTLP endpoint | Exporter constructor argument | `OTEL_EXPORTER_OTLP_ENDPOINT` | Endpoint differs by environment |
| Export protocol | Exporter configuration | `OTEL_EXPORTER_OTLP_PROTOCOL` | Firewall or collector policy differs |
| Trace sampling | Sampler object | `OTEL_TRACES_SAMPLER` | Platform owns sampling policy |
| Signal enablement | Provider setup | `OTEL_TRACES_EXPORTER` | Service needs quick disable or console debug |

Signal-specific configuration generally overrides general configuration.
For example, a platform may set a general OTLP endpoint for all signals but send traces to a specialized trace collector during a migration.
This precedence lets teams change one signal without disturbing the others.
In exam scenarios, look for the more specific variable when two settings appear to conflict.

| Environment Variable | Purpose | Example Value | Operational Meaning |
|---|---|---|---|
| `OTEL_SERVICE_NAME` | Sets `service.name` resource attribute | `checkout` | Groups telemetry by service |
| `OTEL_RESOURCE_ATTRIBUTES` | Adds resource attributes | `deployment.environment=prod,service.version=2.4.1` | Enriches every signal from the process |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | General OTLP endpoint | `http://collector:4317` | Default destination for OTLP signals |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | Trace-specific OTLP endpoint | `http://trace-collector:4317` | Overrides the general endpoint for traces |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | OTLP transport encoding | `grpc` or `http/protobuf` | Must match collector receiver configuration |
| `OTEL_TRACES_SAMPLER` | Trace sampling strategy | `always_on` or `traceidratio` | Controls which traces are sampled |
| `OTEL_TRACES_SAMPLER_ARG` | Sampler argument | `0.10` | Ten percent sampling for ratio sampler |

OTLP is the standard export protocol you should expect to see in modern OTel designs.
The exporter may send directly to a backend, but many production architectures send to an OpenTelemetry Collector first.
The collector can receive telemetry, batch it, filter it, enrich it, and fan it out to one or more backends.
This module focuses on the SDK side, but the export choice should already make you think about the collector architecture in the next module.

| Exporter Choice | Good Fit | Tradeoff | Senior-Level Question |
|---|---|---|---|
| Console exporter | Local learning and debugging | Not suitable for production throughput | Did we accidentally leave this in a hot path? |
| OTLP exporter | Standard production path | Requires collector or backend endpoint | Is protocol and endpoint configured consistently? |
| Prometheus reader/export path | Prometheus-native metric scraping | Pull model differs from trace export | Does this service expose a scrape endpoint securely? |
| Legacy Jaeger or Zipkin exporter | Older estates during migration | Less portable than OTLP | Can the collector translate OTLP instead? |
| No-op exporter | Tests or temporary disablement | Telemetry disappears | Is this intentionally disabled or misconfigured? |

Semantic conventions are naming standards that make telemetry portable.
They help dashboards, alert rules, and queries work across libraries and languages.
For HTTP spans, current stable conventions use names such as `http.request.method` and `http.response.status_code`.
Old names may still appear in older dashboards or examples, but exam scenarios expect you to understand that semantic conventions evolve and that consistent naming is part of portability.

| Domain | Recommended Attribute | Example Value | Why It Helps |
|---|---|---|---|
| HTTP request | `http.request.method` | `POST` | Groups requests by method |
| HTTP response | `http.response.status_code` | `201` | Supports error-rate analysis |
| URL | `url.full` | `https://api.example.test/checkout` | Preserves complete request target when safe |
| Service | `service.name` | `checkout` | Identifies the emitting service |
| Service | `service.version` | `2.4.1` | Correlates telemetry with releases |
| Database | `db.system` | `postgresql` | Identifies dependency technology |
| Messaging | `messaging.system` | `kafka` | Identifies messaging backend |

The most important semantic convention habit is consistency.
If half the fleet uses `http.method` and the other half uses `http.request.method`, a dashboard filter may silently miss data.
If one team records `service.name` as a span attribute and another sets it as a resource, resource-based service views become incomplete.
Instrumentation is not just about creating telemetry; it is about creating telemetry that can be queried with confidence.

## Part 6: Auto-Instrumentation, Manual Instrumentation, and the Boundary Between Them

Auto-instrumentation wraps supported libraries without requiring application developers to edit every call site.
In Java, an agent can modify bytecode at class load time; in Python, instrumentation commonly patches libraries during import; in Node.js, require hooks can wrap modules; in .NET, profiling and startup hooks can attach instrumentation.
This is powerful because it gives teams baseline traces for HTTP frameworks, clients, databases, messaging libraries, and gRPC quickly.
It is not enough for business observability because libraries do not know what your checkout, renewal, refund, or fraud decision means.

| Language | Common Auto-Instrumentation Mechanism | Typical Command or Setup | What It Usually Captures |
|---|---|---|---|
| Java | Java agent and bytecode instrumentation | `java -javaagent:opentelemetry-javaagent.jar -jar app.jar` | HTTP, JDBC, gRPC, messaging libraries |
| Python | Import-time monkey patching | `opentelemetry-instrument .venv/bin/python app.py` | Flask, FastAPI, requests, database clients |
| .NET | CLR profiler and startup hooks | Environment variables and runtime hooks | ASP.NET, HTTP clients, database libraries |
| Node.js | Require hooks and instrumentation packages | `node --require @opentelemetry/auto-instrumentations-node/register app.js` | Express, HTTP, database clients |

Manual instrumentation should fill the semantic gaps that libraries cannot see.
A library can tell that an HTTP request happened, but it cannot know that `reserve-inventory` is the critical business step or that `order.type=subscription` is the dimension operations needs.
A database library can record a query span, but it cannot decide whether a failed payment authorization should mark the parent checkout span as error.
Manual spans, metrics, attributes, and events should therefore describe the domain, not duplicate what auto-instrumentation already creates.

| Situation | Auto-Instrumentation Enough? | Add Manual Instrumentation? | Reason |
|---|---|---|---|
| Basic HTTP server latency | Often yes | Maybe add route naming if missing | Framework instrumentation knows request boundaries |
| Payment authorization business step | No | Yes | Library cannot infer business meaning |
| Database query timing | Often yes | Add attributes carefully if needed | Driver instrumentation captures dependency call |
| Queue depth from broker API | No | Yes, usually async metric | Value exists outside request flow |
| Feature flag branch taken | No | Yes, event or attribute | Business context matters during incidents |

A good instrumentation review asks whether the next engineer can debug a real incident from the telemetry.
If auto-instrumentation creates ten spans but none of them reveal which business decision failed, manual instrumentation is needed.
If manual instrumentation creates dozens of nested spans around every helper function, the trace becomes noisy and expensive.
The best result is a layered trace: automatic spans show technical boundaries, while manual spans and metrics show business intent.

| Design Smell | What It Looks Like | Refactor Direction |
|---|---|---|
| Duplicate spans | Manual HTTP span wraps an auto-generated HTTP server span with the same name | Keep the auto span and add attributes or events |
| Missing business context | Trace shows database and HTTP calls but not checkout decision points | Add manual internal spans for domain steps |
| Attribute overload | Every span carries user ID, email, cart ID, and request payload | Move sensitive or high-cardinality data out of span attributes |
| Broken correlation | Logs have request IDs but no trace IDs | Configure log bridge and current span context |
| Backend lock-in | Application imports vendor tracing APIs directly | Use OTel API and SDK exporters |

## Part 7: Worked Examples From Input to Solution

The audit failure called out a common curriculum problem: code snippets that sit on the page as reference material do not teach learners how to move from a problem to a solution.
This section uses the input-to-solution pattern instead.
Each example starts with an operational problem, shows the uninstrumented or incomplete input, states the desired telemetry, then walks through the solution.
After the worked example, you will get a similar "your turn" task in the exercise.

### 7.1 Worked Example A: Turn an Unobservable Checkout Function Into a Trace

The starting problem is intentionally small.
A checkout function validates a cart, calls a payment function, records an order, and returns an order ID.
When it fails in production, logs may show an exception, but there is no trace structure showing which step failed or how long each step took.
The goal is to create one parent span for the checkout operation and child spans for meaningful business steps without instrumenting every helper line.

**Input file: `checkout_plain.py`**

```python
import random
import time


def validate_cart(cart_id: str) -> None:
    time.sleep(0.03)
    if not cart_id:
        raise ValueError("cart_id is required")


def charge_payment(cart_id: str) -> str:
    time.sleep(0.05)
    if random.random() < 0.20:
        raise RuntimeError("payment gateway timeout")
    return "PAY-1001"


def record_order(cart_id: str, payment_id: str) -> str:
    time.sleep(0.02)
    return f"ORD-{cart_id}-{payment_id}"


def checkout(cart_id: str) -> str:
    validate_cart(cart_id)
    payment_id = charge_payment(cart_id)
    return record_order(cart_id, payment_id)


if __name__ == "__main__":
    print(checkout("CART-123"))
```

The first design decision is where the root span belongs.
The checkout function is the operation the business cares about, so it should be the parent span.
The validation and payment steps are meaningful enough to become child spans because failures there lead to different operational actions.
The `record_order` helper is short in this example, but it still crosses a persistence boundary in many real services, so a child span is reasonable if it represents a database write.

| Design Choice | Decision | Reason |
|---|---|---|
| Parent span name | `checkout` | Describes the business operation |
| Validation span kind | `INTERNAL` | Work stays inside the process |
| Payment span kind | `CLIENT` | Represents an outbound dependency |
| Order recording span kind | `CLIENT` in real persistence path | Database writes are dependency calls |
| Cart ID handling | Attribute in demo only | In production, evaluate sensitivity and cardinality |

The solution starts by creating one `TracerProvider` at process startup.
The resource goes on the provider because every span from this process belongs to the same service.
The batch processor is used even though the exporter is console because learners should practice the production shape early.
Finally, exception handling records the exception event, sets error status, and re-raises so instrumentation does not swallow real failures.

**Solution file: `checkout_traced.py`**

```python
import random
import time

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode


resource = Resource.create(
    {
        "service.name": "checkout-service",
        "service.version": "1.0.0",
        "deployment.environment": "local",
    }
)

trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer("kubedojo.checkout", "0.1.0")


def validate_cart(cart_id: str) -> None:
    with tracer.start_as_current_span("validate-cart", kind=SpanKind.INTERNAL) as span:
        span.set_attribute("cart.present", bool(cart_id))
        time.sleep(0.03)
        if not cart_id:
            error = ValueError("cart_id is required")
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            raise error


def charge_payment(cart_id: str) -> str:
    with tracer.start_as_current_span("charge-payment", kind=SpanKind.CLIENT) as span:
        span.set_attribute("payment.provider", "demo-gateway")
        span.set_attribute("cart.id", cart_id)
        time.sleep(0.05)
        if random.random() < 0.20:
            error = RuntimeError("payment gateway timeout")
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            raise error
        span.set_status(Status(StatusCode.OK))
        return "PAY-1001"


def record_order(cart_id: str, payment_id: str) -> str:
    with tracer.start_as_current_span("record-order", kind=SpanKind.CLIENT) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("payment.id", payment_id)
        time.sleep(0.02)
        order_id = f"ORD-{cart_id}-{payment_id}"
        span.add_event("order.recorded", {"order.id": order_id})
        return order_id


def checkout(cart_id: str) -> str:
    with tracer.start_as_current_span("checkout", kind=SpanKind.INTERNAL) as span:
        span.set_attribute("cart.id", cart_id)
        try:
            validate_cart(cart_id)
            payment_id = charge_payment(cart_id)
            order_id = record_order(cart_id, payment_id)
            span.add_event("checkout.completed", {"order.id": order_id})
            return order_id
        except Exception as error:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            raise


if __name__ == "__main__":
    try:
        print(checkout("CART-123"))
    finally:
        trace_provider.shutdown()
```

Run the solution in a clean virtual environment so the command matches the repository's local Python convention.
The console exporter prints span records after shutdown, so the `finally` block is part of the example rather than an optional cleanup detail.
In a long-running service, shutdown would happen during process termination instead of after one function call.
For a short script, failing to flush before exit can make learners think instrumentation failed.

```bash
.venv/bin/python -m pip install opentelemetry-api opentelemetry-sdk
.venv/bin/python checkout_traced.py
```

When you inspect the output, look for the same trace ID across the parent and child spans.
The `checkout` span should be the parent, and the validation, payment, and record-order spans should appear as children.
If the simulated payment failure occurs, both the payment span and parent checkout span should show error status.
That propagation of failure status is a design choice: the dependency failed, and therefore the checkout operation failed.

### 7.2 Worked Example B: Add Metrics Without Turning Attributes Into a Cost Problem

The traced function tells you which request failed, but it does not answer aggregate questions such as "how many checkout attempts are failing?" or "how long does checkout usually take?"
That is where metrics belong.
The goal is to add a counter for attempts, a counter for failures, a histogram for duration, and an observable gauge for queue depth.
The important constraint is to choose bounded attributes, because metric attributes define time series cardinality.

**Metric design input**

| Operational Question | Metric Needed | Instrument | Attribute Plan |
|---|---|---|---|
| How many checkout attempts occurred? | `checkout.attempts` | Counter | `checkout.channel` only |
| How many failed? | `checkout.failures` | Counter | `error.type` with bounded exception names |
| How long did checkout take? | `checkout.duration` | Histogram | `checkout.channel` only |
| How deep is the queue now? | `checkout.queue.depth` | Observable Gauge | `queue.name` only |

A tempting but poor metric design would attach `cart.id` or `user.id` to every metric.
That might feel useful during one investigation, but it creates many time series and makes aggregate dashboards worse.
Trace attributes can sometimes carry a request-level identifier when justified, and logs can hold more detailed request data.
Metrics should usually use attributes that are bounded, stable, and useful for grouping.

**Solution file: `checkout_traces_metrics.py`**

```python
import random
import time
from typing import Iterable

from opentelemetry import metrics, trace
from opentelemetry.metrics import Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode


resource = Resource.create(
    {
        "service.name": "checkout-service",
        "service.version": "1.0.0",
        "deployment.environment": "local",
    }
)

trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(trace_provider)

metric_reader = PeriodicExportingMetricReader(
    ConsoleMetricExporter(),
    export_interval_millis=1000,
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

tracer = trace.get_tracer("kubedojo.checkout", "0.1.0")
meter = metrics.get_meter("kubedojo.checkout", "0.1.0")

checkout_attempts = meter.create_counter(
    "checkout.attempts",
    unit="1",
    description="Total checkout attempts",
)
checkout_failures = meter.create_counter(
    "checkout.failures",
    unit="1",
    description="Total failed checkout attempts",
)
checkout_duration = meter.create_histogram(
    "checkout.duration",
    unit="ms",
    description="Checkout processing duration",
)


def current_queue_depth() -> int:
    return 3


def observe_queue_depth(options) -> Iterable[Observation]:
    return [Observation(current_queue_depth(), {"queue.name": "checkout"})]


meter.create_observable_gauge(
    "checkout.queue.depth",
    callbacks=[observe_queue_depth],
    unit="1",
    description="Current checkout queue depth",
)


def charge_payment() -> str:
    with tracer.start_as_current_span("charge-payment", kind=SpanKind.CLIENT) as span:
        span.set_attribute("payment.provider", "demo-gateway")
        time.sleep(0.05)
        if random.random() < 0.20:
            error = RuntimeError("payment gateway timeout")
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            raise error
        return "PAY-1001"


def checkout(cart_id: str, channel: str) -> str:
    start = time.perf_counter()
    checkout_attempts.add(1, {"checkout.channel": channel})

    with tracer.start_as_current_span("checkout", kind=SpanKind.INTERNAL) as span:
        span.set_attribute("cart.id", cart_id)
        span.set_attribute("checkout.channel", channel)
        try:
            payment_id = charge_payment()
            order_id = f"ORD-{cart_id}-{payment_id}"
            span.add_event("checkout.completed", {"order.id": order_id})
            return order_id
        except Exception as error:
            checkout_failures.add(1, {"error.type": type(error).__name__})
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            checkout_duration.record(elapsed_ms, {"checkout.channel": channel})


if __name__ == "__main__":
    try:
        for index in range(5):
            try:
                print(checkout(f"CART-{index}", "web"))
            except RuntimeError as error:
                print(f"checkout failed: {error}")
            time.sleep(0.20)
        time.sleep(1.50)
    finally:
        meter_provider.shutdown()
        trace_provider.shutdown()
```

The metric example adds one more mental model: metrics record aggregate facts even when traces are sampled.
If a production sampler keeps only a fraction of traces, counters and histograms can still represent the whole workload.
That is why traces and metrics are complementary rather than redundant.
During an incident, metrics usually tell you that something is wrong, and traces help you inspect representative examples.

```bash
.venv/bin/python checkout_traces_metrics.py
```

After running the file, inspect the console output for metric names and resource attributes.
You should see counters and histograms associated with `service.name=checkout-service`.
You should not see `cart.id` attached to the metric streams, because the example intentionally keeps that request-specific detail on the trace.
That boundary is a senior-level instrumentation habit: put high-cardinality request evidence where it helps debugging, and keep metrics aggregatable.

### 7.3 Worked Example C: Continue a Trace Across an HTTP Boundary

The third worked example focuses on propagation rather than local spans.
Imagine a gateway service receives an inbound request and calls a payment service.
The gateway can create a client span, but the payment service will not join the trace unless the gateway injects context and the payment service extracts it.
A broken propagator configuration creates two valid-looking traces that fail to connect.

**Propagation design**

| Boundary | Sender Responsibility | Receiver Responsibility | Failure Symptom |
|---|---|---|---|
| Gateway to payment over HTTP | Inject context into request headers | Extract context before starting server span | Payment trace appears separate |
| Producer to queue | Store context in message metadata | Extract or link context during consume | Consumer work loses upstream cause |
| Service to background thread | Carry context into task execution | Start span with carried context | Child work appears as a new root |

The following Go example is complete enough to show the required imports and SDK setup, but it intentionally keeps the HTTP server small.
The key lines are the propagator configuration, extraction from inbound headers, and injection into outbound headers.
Without those lines, spans may still exist, but trace continuity across services will be broken.
This is the difference between local instrumentation and distributed tracing.

```go
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	stdouttrace "go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"
)

func initTracer() (*sdktrace.TracerProvider, error) {
	exporter, err := stdouttrace.New(stdouttrace.WithPrettyPrint())
	if err != nil {
		return nil, err
	}

	res, err := resource.New(
		context.Background(),
		resource.WithAttributes(attribute.String("service.name", "gateway-service")),
	)
	if err != nil {
		return nil, err
	}

	provider := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
	)

	otel.SetTracerProvider(provider)
	otel.SetTextMapPropagator(
		propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{},
			propagation.Baggage{},
		),
	)

	return provider, nil
}

func gatewayHandler(w http.ResponseWriter, r *http.Request) {
	ctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))
	tracer := otel.Tracer("kubedojo.gateway")

	ctx, span := tracer.Start(ctx, "POST /checkout", trace.WithSpanKind(trace.SpanKindServer))
	defer span.End()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, "http://127.0.0.1:8081/pay", nil)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))

	clientSpanCtx, clientSpan := tracer.Start(ctx, "POST payment-service", trace.WithSpanKind(trace.SpanKindClient))
	defer clientSpan.End()

	_ = clientSpanCtx
	time.Sleep(25 * time.Millisecond)
	fmt.Fprintln(w, "checkout accepted")
}

func main() {
	provider, err := initTracer()
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		_ = provider.Shutdown(context.Background())
	}()

	http.HandleFunc("/checkout", gatewayHandler)
	log.Fatal(http.ListenAndServe("127.0.0.1:8080", nil))
}
```

This example also shows why span kind matters during propagation.
The gateway handler span is a server span because it receives a request.
The outbound payment span is a client span because it calls another service.
The payment service, if implemented separately, should extract the headers and create its own server span with the extracted context, causing the trace tree to show both sides of the boundary.

## Patterns & Anti-Patterns

The safest OpenTelemetry SDK designs separate three concerns that are often tangled together in early instrumentation efforts: application code describes meaningful work, the SDK pipeline controls collection behavior, and deployment configuration chooses export destinations.
When those concerns stay separate, a service can keep stable business spans while the platform changes collectors, sampling ratios, or backend vendors through environment configuration.
When those concerns are mixed, every backend migration becomes an application release, every local debugging choice risks leaking into production, and every service invents a slightly different telemetry dialect.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---|---|---|---|
| Provider-owned resource identity | Every service, job, worker, and CLI that emits telemetry | One resource attaches shared identity to traces, metrics, and logs | Standardize `service.name`, `service.version`, and `deployment.environment` across Kubernetes 1.35+ workloads |
| Batch traces, bounded metrics | Production paths with real request volume | Export work moves off the request path while metrics remain aggregatable | Tune queue size, export interval, and metric attributes before adding traffic |
| Auto plus manual layering | Services with supported frameworks and important business steps | Libraries capture technical boundaries while manual spans capture domain intent | Review traces for duplicate spans after enabling auto-instrumentation |
| Environment-owned export policy | Multiple environments, collectors, or backends | Applications avoid hard-coded endpoints and protocols | Document precedence between general and signal-specific OTLP variables |

The provider-owned resource pattern looks ordinary, but it removes a surprising amount of operational friction.
If every service sets `service.name` differently, dashboards fragment even when spans are valid.
If a deployment writes version information as a span attribute instead of as a resource, metrics and logs may not carry the same release identity as traces.
A good review asks whether a person could filter every signal from the same pod, rollout, and service without knowing which language SDK produced it.

The batch-traces and bounded-metrics pattern keeps observability from competing with the workload it is supposed to explain.
Trace export can tolerate asynchronous buffering because the request already finished when a span ends, while metrics need disciplined attributes because every new label combination becomes a new time series.
This is why a batch processor and an attribute review often belong in the same pull request.
One protects latency, and the other protects the backend from a cardinality problem that only appears after real traffic arrives.

The auto-plus-manual pattern is the one most teams eventually converge on.
Auto-instrumentation is excellent at showing inbound HTTP requests, outbound HTTP calls, database queries, and messaging operations, but it cannot name the business decision that matters during an incident.
Manual instrumentation should add the missing business layer without replacing the library layer.
If a trace already contains a framework server span named `POST /checkout`, a manual span with the same name is noise; a manual span named `fraud-decision` or `reserve-inventory` is evidence.

| Anti-Pattern | What Goes Wrong | Why Teams Fall Into It | Better Alternative |
|---|---|---|---|
| Exporter in business logic | Backend changes require source edits and redeploys | The first demo hard-codes console or vendor exporters | Keep exporter choice in SDK setup and environment variables |
| Metric attributes copied from logs | Series count grows with users, carts, orders, or request IDs | Engineers want per-request debugging from aggregate data | Use traces and logs for request evidence, metrics for bounded grouping |
| Baggage as a hidden context bag | Headers carry sensitive or high-cardinality values downstream | Baggage feels like convenient distributed storage | Allow only documented, non-sensitive, low-cardinality baggage keys |
| Manual spans around every helper | Traces become long, expensive, and hard to read | More spans feel like more observability | Instrument meaningful operations and dependency boundaries |

These anti-patterns share a common mistake: they optimize for the first person writing instrumentation instead of the next person debugging with it.
The first person may want a quick exporter, every local variable as an attribute, or a span around each function to prove the SDK works.
The next person needs a trace that tells a coherent story, a metric that aggregates across thousands of requests, and a log that correlates without exposing secrets.
Good SDK design is therefore a reader-centered discipline.

## Decision Framework

Use this framework when you review an instrumentation change, answer an OTCA scenario, or refactor a reference snippet into a runnable service pattern.
Start with the signal question, then work outward to pipeline behavior and deployment control.
That order prevents a common mistake where a team debates exporters before deciding what the telemetry should mean.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         SDK Design Decision Flow                            │
│                                                                            │
│  1. What operational question must be answered?                             │
│        │                                                                    │
│        ▼                                                                    │
│  2. Is the evidence per operation, aggregate, or log-like narrative?         │
│        │                                                                    │
│        ├── Per operation ─────▶ trace span, event, status, or link           │
│        ├── Aggregate ────────▶ counter, histogram, observable instrument     │
│        └── Narrative ────────▶ log bridge with current trace context         │
│        │                                                                    │
│        ▼                                                                    │
│  3. Which attributes are safe, bounded, and semantically consistent?         │
│        │                                                                    │
│        ▼                                                                    │
│  4. Which SDK component controls delivery: processor, reader, exporter?      │
│        │                                                                    │
│        ▼                                                                    │
│  5. Which settings belong in code, and which belong in environment config?   │
└────────────────────────────────────────────────────────────────────────────┘
```

The first branch separates traces, metrics, and logs by the job they perform.
If the question is "which step failed for this checkout request?", a span, event, status, or linked trace context is the right shape because the evidence belongs to one operation.
If the question is "are failures increasing for the checkout workload?", a counter or histogram is the right shape because the evidence must aggregate across many operations.
If the question is "what message did the application write while this span was current?", a log bridge with trace correlation is the right shape because the evidence is narrative and timestamped.

| Decision Point | Choose This | When the Scenario Says | Watch For |
|---|---|---|---|
| Span processor | `BatchSpanProcessor` | Production service, latency-sensitive path, OTLP export | Shutdown flush and queue overflow behavior |
| Span processor | `SimpleSpanProcessor` | Local demo, unit test, one-shot script with console output | Do not carry this into high-traffic request paths |
| Metric instrument | Counter | Count only increases, such as attempts or errors | Avoid current-state values such as queue depth |
| Metric instrument | Histogram | Distribution matters, especially latency or size | Pick units and attributes that preserve meaning |
| Propagation design | Parent-child | One operation directly causes the next operation | Same trace ID and correct span kind across boundary |
| Propagation design | Links | Batch, fan-in, retry, or async work relates to multiple causes | Do not force one arbitrary parent |
| Configuration location | Environment variables | Endpoint, protocol, sampler, service name differ by deployment | Signal-specific variables may override general variables |
| Configuration location | Code | Business spans, metric names, and resource defaults are part of the service | Avoid hard-coding backend endpoints |

Pause and predict: if you move `OTEL_EXPORTER_OTLP_ENDPOINT` from the deployment manifest into application code, what happens when a staging collector changes hostnames but the service image is already built?
The service now needs a new build or a code-specific override, even though the telemetry destination is a deployment concern.
That is an avoidable coupling between source code and platform routing.
Keeping export configuration outside the business logic lets a Kubernetes rollout change collector topology without changing the instrumentation that describes checkout behavior.

The same framework helps you refactor reference-style snippets.
A snippet that only creates a tracer and prints a span is not yet a production pattern because it lacks resource identity, shutdown behavior, error status, and a deployment-owned export path.
To turn it into a reusable pattern, ask which provider owns the signal, which processor or reader controls delivery, which attributes are safe to query, and which final check proves the signal answers the original operational question.
That refactoring habit is what makes SDK knowledge useful outside exam flashcards.

## Did You Know?

- **OpenTelemetry separates API from SDK intentionally.** Libraries can depend on the API to create telemetry without forcing applications to use a specific exporter, processor, sampler, or backend.
- **The Collector is optional from the SDK perspective.** An SDK can export directly to a backend, but production teams often use the Collector for routing, batching, filtering, and backend migration flexibility.
- **Semantic conventions are operational contracts.** A small naming mismatch such as using an old HTTP attribute can break dashboards even when spans are technically being exported.
- **Auto-instrumentation is a starting point, not a complete observability strategy.** It captures common library boundaries, while manual instrumentation captures business meaning and incident-specific evidence.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Using `SimpleSpanProcessor` in production services | Export happens synchronously and can add backend or console latency to request handling | Use `BatchSpanProcessor` and flush during shutdown |
| Setting `service.name` as a span attribute | Service identity belongs to the resource and should apply to all emitted telemetry | Set `service.name` on the provider resource or through `OTEL_SERVICE_NAME` |
| Marking outbound database or HTTP calls as `INTERNAL` | Dependency maps and trace readers lose the communication-role signal | Use `CLIENT` for outbound dependency calls and `SERVER` for inbound handlers |
| Recording exceptions without setting span error status | The exception event exists, but the span may not summarize the operation as failed | Record the exception and set `StatusCode.ERROR` when the operation fails |
| Putting user identifiers, tokens, or emails in baggage | Baggage propagates downstream through headers or metadata and may leak sensitive data | Use bounded, non-sensitive context or keep details in protected logs |
| Adding high-cardinality request IDs to metric attributes | Each unique value can create a separate time series and overload dashboards or backends | Keep metrics aggregatable and put request-specific evidence in traces or logs |
| Confusing cumulative and delta temporality | Backend graphs can show misleading rates, resets, or totals | Match reader/exporter temporality with backend expectations |
| Duplicating auto-instrumented spans manually | Traces become noisy, costs rise, and readers see two spans for the same operation | Keep auto spans for technical boundaries and add manual spans for business steps |

---

## Quiz

Test yourself with scenario-based OTCA-style questions. Each question asks you to apply the SDK model to a realistic situation, not to recite a definition.

<details>
<summary><strong>Q1: Your team added OpenTelemetry to a high-traffic API, and p95 latency increased after enabling console trace export with a simple processor. What do you change first, and why?</strong></summary>

Change the trace pipeline to use a `BatchSpanProcessor`, and stop treating console export as a production destination. The simple processor exports ended spans synchronously on the request path, so exporter latency becomes application latency. A batch processor buffers spans and exports asynchronously, which preserves trace emission while removing most export work from request handling.
</details>

<details>
<summary><strong>Q2: A checkout trace shows an inbound HTTP span, but the payment-service spans appear as separate root traces. Both services have OTel installed. What do you inspect next?</strong></summary>

Inspect propagation at the service boundary. The gateway must inject context into outbound HTTP headers, and payment-service must extract context before starting its server span. Check that both sides use compatible propagators such as W3C TraceContext, then verify that the same trace ID appears on both sides of the request.
</details>

<details>
<summary><strong>Q3: A dashboard for checkout latency is useless because every metric series includes `cart.id`. What instrumentation change should you recommend?</strong></summary>

Remove `cart.id` from metric attributes and keep the metric dimensions bounded, such as `checkout.channel` or `order.type` if those values have controlled sets. Request-specific identifiers can belong in trace attributes or protected logs when justified. Metrics should preserve aggregate behavior, and high-cardinality identifiers create too many time series.
</details>

<details>
<summary><strong>Q4: A Python service records exceptions with `span.record_exception(error)`, but trace search does not show failed operations reliably. What is missing?</strong></summary>

The code should also set the span status to error when the operation fails, for example with `Status(StatusCode.ERROR, str(error))`. Recording an exception adds a timestamped event, but status summarizes the outcome of the span. A trace reader or alert often relies on the status field to identify failed spans quickly.
</details>

<details>
<summary><strong>Q5: A batch worker processes messages that came from several different checkout requests. A learner wants to choose one incoming message as the parent span. How would you evaluate that design?</strong></summary>

Choosing one message as the parent misrepresents the fan-in relationship because the batch work is related to multiple earlier traces. A better design is to create a consumer or batch-processing span and add links to the contexts carried by the messages. Parent-child relationships are best for direct causal chains, while links preserve relationships across batching and fan-in.
</details>

<details>
<summary><strong>Q6: Auto-instrumentation gives a service HTTP and database spans, but incident responders still cannot tell whether failures happen during fraud checks or inventory reservation. What should the team add?</strong></summary>

They should add manual instrumentation around meaningful business steps, such as `fraud-check` and `reserve-inventory`, with carefully chosen attributes and events. Auto-instrumentation captures library boundaries, but it cannot infer domain intent. Manual spans should complement the automatic spans rather than duplicate HTTP or database spans already created by the instrumentation library.
</details>

<details>
<summary><strong>Q7: A service sends cumulative counters to a backend that expects delta values, and request-rate graphs look wrong after every restart. What part of the SDK/export path should you investigate?</strong></summary>

Investigate the metric reader, exporter, collector conversion, and backend temporality expectations. Cumulative values represent totals since start or reset, while delta values represent changes since the previous collection. If the backend interprets one as the other, rates and resets can look misleading even though the application increments the counter correctly.
</details>

<details>
<summary><strong>Q8: A teammate copied a reference-style SDK snippet into a service: it creates one span, hard-codes an OTLP endpoint, omits resource attributes, and never shuts down the provider. How would you refactor it into an input-to-solution pattern suitable for this module?</strong></summary>

Start by writing the operational input: which request, dependency, or business step should the telemetry explain. Then create a provider with resource attributes, use a production-shaped processor or reader, move endpoint and protocol choices to environment configuration, and add shutdown or flush behavior so short-lived processes export data. Finally, add a validation step that inspects trace identity, span kinds, metric names, and bounded attributes, because a refactor is not complete until the output proves it answers the original debugging question.
</details>

---

## Hands-On Exercise: Build and Diagnose an Instrumented Checkout Script

**Goal**: Convert a small checkout script into a complete OpenTelemetry SDK example that emits useful traces and metrics, then diagnose the output as if you were reviewing a teammate's instrumentation.

### Scenario

Your team has a checkout job that sometimes fails when the payment gateway times out.
The current script prints success or failure, but it does not show where time is spent, which step failed, or whether failures are increasing.
You need to add tracing and metrics in a way that would still make sense if the script became a long-running service.
Use console exporters for the exercise so you can inspect the output locally.

### Setup

Create or reuse the repository virtual environment, then install the packages required for console trace and metric export.

```bash
.venv/bin/python -m pip install opentelemetry-api opentelemetry-sdk
```

### Starting File

Create `otel_checkout_exercise.py` with this uninstrumented input.

```python
import random
import time


def validate_cart(cart_id: str) -> None:
    time.sleep(0.02)
    if not cart_id:
        raise ValueError("cart_id is required")


def charge_payment() -> str:
    time.sleep(0.04)
    if random.random() < 0.25:
        raise RuntimeError("payment gateway timeout")
    return "PAY-1001"


def reserve_inventory() -> None:
    time.sleep(0.03)


def checkout(cart_id: str, channel: str) -> str:
    validate_cart(cart_id)
    payment_id = charge_payment()
    reserve_inventory()
    return f"ORD-{cart_id}-{payment_id}"


if __name__ == "__main__":
    for index in range(6):
        try:
            print(checkout(f"CART-{index}", "web"))
        except RuntimeError as error:
            print(f"checkout failed: {error}")
```

### Tasks

1. Add a `Resource` with `service.name=checkout-exercise`, `service.version=0.1.0`, and `deployment.environment=local`.
2. Configure one `TracerProvider` at startup with a `BatchSpanProcessor` and `ConsoleSpanExporter`.
3. Configure one `MeterProvider` at startup with a `PeriodicExportingMetricReader` and `ConsoleMetricExporter`.
4. Create a parent span named `checkout` for the business operation and child spans named `validate-cart`, `charge-payment`, and `reserve-inventory`.
5. Use `INTERNAL` for validation and inventory reservation unless your implementation simulates a real dependency call.
6. Use `CLIENT` for payment because the payment gateway represents an outbound dependency.
7. Add a counter named `checkout.attempts` with a bounded attribute such as `checkout.channel`.
8. Add a counter named `checkout.failures` with a bounded attribute such as `error.type`.
9. Add a histogram named `checkout.duration` with unit `ms` and record elapsed checkout time.
10. When an exception occurs, record it on the active span, set error status, update the failure counter, and re-raise or handle it deliberately.
11. Flush both providers before the script exits so console output is visible.
12. Review the output and write down which field proves parent-child trace continuity.

### Success Criteria

- [ ] The script runs with `.venv/bin/python otel_checkout_exercise.py` and exits without import errors.
- [ ] Console trace output shows a `checkout` parent span and child spans for validation, payment, and inventory reservation.
- [ ] Payment failures show an exception event and error status on the payment span.
- [ ] The parent checkout span also reflects failure when checkout cannot complete.
- [ ] All spans include the resource attribute `service.name=checkout-exercise`.
- [ ] Metric output includes `checkout.attempts`, `checkout.failures`, and `checkout.duration`.
- [ ] Metric attributes do not include `cart.id`, `user.id`, email addresses, tokens, or other high-cardinality or sensitive values.
- [ ] You can explain whether each span kind describes in-process work, inbound work, outbound work, producer work, or consumer work.

### Verification Prompts

After running the script, inspect one successful trace and one failed trace.
Confirm that child spans share the parent trace ID and that their parent span ID points back to the checkout span.
If a span appears as a separate root, revisit where the span was started and whether current context was preserved.
For this single-process exercise, current context should flow automatically through nested `start_as_current_span` blocks.

Now inspect the metrics.
The attempt counter should increase for every checkout attempt, the failure counter should increase only when checkout fails, and the duration histogram should record both successful and failed attempts.
If the histogram only records successes, move the duration recording into a `finally` block so failed requests are included.
This is a realistic production concern because excluding failures can make the slowest or most important requests disappear from latency data.

Finally, review your attributes.
If you added `cart.id` to metrics, remove it and explain why it belongs in trace evidence, not aggregate metric dimensions.
If you put `service.name` on every span manually, move it to the resource and explain why provider-level identity is the correct scope.
If you used `SimpleSpanProcessor`, switch to batch processing and explain how request-path export changes latency behavior.

---

## Sources

- [OpenTelemetry traces concepts](https://opentelemetry.io/docs/concepts/signals/traces/)
- [OpenTelemetry metrics concepts](https://opentelemetry.io/docs/concepts/signals/metrics/)
- [OpenTelemetry logs concepts](https://opentelemetry.io/docs/concepts/signals/logs/)
- [OpenTelemetry context propagation concepts](https://opentelemetry.io/docs/concepts/context-propagation/)
- [OpenTelemetry baggage concepts](https://opentelemetry.io/docs/concepts/signals/baggage/)
- [OpenTelemetry SDK environment variable configuration](https://opentelemetry.io/docs/languages/sdk-configuration/)
- [OpenTelemetry Protocol exporter specification](https://opentelemetry.io/docs/specs/otel/protocol/exporter/)
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/)
- [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [OpenTelemetry Go instrumentation](https://opentelemetry.io/docs/languages/go/instrumentation/)
- [W3C Trace Context Recommendation](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry Kubernetes getting started](https://opentelemetry.io/docs/kubernetes/getting-started/)

## Next Module

**Next Module**: [Module 2: OTel Collector Architecture](../module-1.2-otel-collector-advanced/) — how to receive, process, route, and export telemetry at scale.

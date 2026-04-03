---
title: "Module 3.4: Observability Fundamentals"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.4-observability-fundamentals
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Observability concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 3.3 (Cloud Native Patterns)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the three pillars of observability: logs, metrics, and traces
2. **Compare** monitoring (known-unknowns) with observability (unknown-unknowns)
3. **Identify** which observability signal to use for different debugging scenarios
4. **Evaluate** observability maturity levels and what each level enables for operations teams

---

## Why This Module Matters

You can't fix what you can't see. **Observability** is how you understand what's happening inside your systems. It's especially critical in distributed systems where debugging is complex. KCNA tests your understanding of observability pillars and practices.

---

## What is Observability?

```
┌─────────────────────────────────────────────────────────────┐
│              OBSERVABILITY                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Definition:                                               │
│  ─────────────────────────────────────────────────────────  │
│  The ability to understand the internal state of a system │
│  by examining its external outputs                        │
│                                                             │
│  Monitoring vs Observability:                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  MONITORING:                                               │
│  "Is the system working?"                                 │
│  • Pre-defined metrics                                    │
│  • Known failure modes                                    │
│  • Dashboards and alerts                                  │
│                                                             │
│  OBSERVABILITY:                                            │
│  "Why isn't the system working?"                          │
│  • Explore unknown problems                               │
│  • Debug novel issues                                     │
│  • Understand system behavior                             │
│                                                             │
│  Monitoring is a subset of observability                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Three Pillars

```
┌─────────────────────────────────────────────────────────────┐
│              THREE PILLARS OF OBSERVABILITY                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   METRICS   │  │    LOGS     │  │   TRACES    │         │
│  │             │  │             │  │             │         │
│  │  Numbers    │  │  Events     │  │  Requests   │         │
│  │  over time  │  │  text       │  │  across     │         │
│  │             │  │             │  │  services   │         │
│  │  "How much?"│  │  "What?"    │  │  "Where?"   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  Together they answer:                                     │
│  • What is happening? (metrics)                           │
│  • What exactly happened? (logs)                          │
│  • How did it happen across services? (traces)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Metrics

**Metrics** are numerical measurements over time:

```
┌─────────────────────────────────────────────────────────────┐
│              METRICS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What metrics measure:                                     │
│  ─────────────────────────────────────────────────────────  │
│  • Request rate (requests/second)                         │
│  • Error rate (errors/second)                             │
│  • Duration (response time)                               │
│  • Saturation (CPU %, memory %)                          │
│                                                             │
│  Example metric:                                          │
│  ─────────────────────────────────────────────────────────  │
│  http_requests_total{method="GET", status="200"} 1234    │
│        │               │                          │       │
│        │               │                          │       │
│     metric name     labels/tags               value       │
│                                                             │
│  Time series:                                             │
│  ─────────────────────────────────────────────────────────  │
│  Value                                                     │
│    │                                                       │
│ 100├      ┌──┐                                            │
│    │  ┌──┐│  │   ┌──┐                                    │
│  50├──┘  └┘  └───┘  └──┐                                 │
│    │                     └──                              │
│    └─────────────────────────→ Time                      │
│                                                             │
│  Metric types:                                            │
│  • Counter: Only goes up (requests, errors)              │
│  • Gauge: Goes up and down (temperature, memory)         │
│  • Histogram: Distribution of values (latency buckets)   │
│  • Summary: Statistical distribution (percentiles)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The RED Method

For services, track:

| Metric | Description |
|--------|-------------|
| **R**ate | Requests per second |
| **E**rrors | Failed requests per second |
| **D**uration | Time per request |

### The USE Method

For resources, track:

| Metric | Description |
|--------|-------------|
| **U**tilization | % time resource is busy |
| **S**aturation | Work queued/waiting |
| **E**rrors | Error count |

---

## Logs

**Logs** are timestamped records of events:

```
┌─────────────────────────────────────────────────────────────┐
│              LOGS                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  What logs capture:                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Application events                                      │
│  • Errors and stack traces                                │
│  • Audit trails                                           │
│  • Debug information                                       │
│                                                             │
│  Log example:                                              │
│  ─────────────────────────────────────────────────────────  │
│  2024-01-15T10:23:45.123Z INFO [order-service]            │
│    orderId=12345 customerId=67890 action=created          │
│    "Order created successfully"                           │
│                                                             │
│  Log levels:                                               │
│  ─────────────────────────────────────────────────────────  │
│  DEBUG → INFO → WARN → ERROR → FATAL                      │
│  (verbose)              (critical)                        │
│                                                             │
│  Structured logging (recommended):                        │
│  ─────────────────────────────────────────────────────────  │
│  {                                                        │
│    "timestamp": "2024-01-15T10:23:45.123Z",              │
│    "level": "INFO",                                       │
│    "service": "order-service",                           │
│    "orderId": "12345",                                   │
│    "message": "Order created successfully"               │
│  }                                                        │
│                                                             │
│  Benefits of structured logs:                             │
│  • Easily searchable                                      │
│  • Machine parseable                                      │
│  • Consistent format                                      │
│                                                             │
│  In Kubernetes:                                           │
│  ─────────────────────────────────────────────────────────  │
│  Containers write to stdout/stderr                        │
│  Log collectors (Fluentd, Fluent Bit) gather logs        │
│  Send to storage (Elasticsearch, Loki)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Traces

**Traces** track requests across distributed systems:

```
┌─────────────────────────────────────────────────────────────┐
│              DISTRIBUTED TRACING                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Problem: Request flows through multiple services         │
│  ─────────────────────────────────────────────────────────  │
│  User → API Gateway → Order Service → Payment → Database │
│                                                             │
│  Where did it slow down? Where did it fail?              │
│                                                             │
│  Solution: Traces                                         │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Trace: The complete journey of a request                │
│  Span: One operation within a trace                      │
│                                                             │
│  Trace ID: abc-123                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │ ├── API Gateway (span 1)                           │   │
│  │ │   └── 50ms                                       │   │
│  │ │                                                   │   │
│  │ ├── Order Service (span 2)                         │   │
│  │ │   └── 120ms                                      │   │
│  │ │   │                                              │   │
│  │ │   ├── Payment Service (span 3)                  │   │
│  │ │   │   └── 200ms  ← Slow!                        │   │
│  │ │   │                                              │   │
│  │ │   └── Database (span 4)                         │   │
│  │ │       └── 30ms                                   │   │
│  │ │                                                   │   │
│  │ └── Total: 400ms                                   │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Trace ID propagated through all services                 │
│  Each service adds its span                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Trace Terminology

| Term | Description |
|------|-------------|
| **Trace** | Complete request journey (all spans) |
| **Span** | Single operation within trace |
| **Trace ID** | Unique identifier for the trace |
| **Span ID** | Unique identifier for the span |
| **Parent Span** | The calling operation |
| **Context propagation** | Passing trace ID between services |

---

## Connecting the Pillars

```
┌─────────────────────────────────────────────────────────────┐
│              CONNECTING METRICS, LOGS, TRACES              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Scenario: Users report slow checkout                     │
│                                                             │
│  1. METRICS show the problem                              │
│     ─────────────────────────────────────────────────────  │
│     Dashboard: checkout_duration_p99 = 5s (normally 1s)  │
│     "Checkout is slow, but why?"                         │
│                                                             │
│  2. TRACES identify where                                 │
│     ─────────────────────────────────────────────────────  │
│     Trace shows payment service taking 4s               │
│     "Payment is the bottleneck, but why?"               │
│                                                             │
│  3. LOGS explain why                                      │
│     ─────────────────────────────────────────────────────  │
│     Log: "Connection pool exhausted, waiting for         │
│           connection to external payment gateway"        │
│     "Ah! Connection pool needs tuning"                   │
│                                                             │
│  The journey:                                              │
│  Metrics (detect) → Traces (locate) → Logs (diagnose)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Alerting

```
┌─────────────────────────────────────────────────────────────┐
│              ALERTING                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Turn metrics into notifications                          │
│                                                             │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ Metrics │ →  │ Alert Rules │ →  │ Notification│        │
│  │         │    │ "If X > Y"  │    │ Slack/Page │        │
│  └─────────┘    └─────────────┘    └─────────────┘        │
│                                                             │
│  Good alerting practices:                                 │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  • Alert on symptoms, not causes                          │
│    Bad:  "CPU > 90%"                                     │
│    Good: "Response time > 500ms"                         │
│                                                             │
│  • Avoid alert fatigue                                    │
│    Too many alerts = ignore them all                      │
│                                                             │
│  • Actionable alerts                                      │
│    If you can't act on it, don't alert                   │
│                                                             │
│  • Severity levels                                        │
│    Critical: Page someone NOW                            │
│    Warning: Check tomorrow                               │
│    Info: FYI only                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Observability term origin** - Comes from control theory, where a system is "observable" if internal states can be determined from external outputs.

- **OpenTelemetry is unifying observability** - It provides a single standard for metrics, traces, and logs, replacing vendor-specific instrumentation.

- **Cardinality matters** - High-cardinality labels (like user ID) in metrics can explode storage costs. Be careful what you label.

- **The 4 Golden Signals** - Google's SRE book recommends: latency, traffic, errors, and saturation as the key metrics for any service.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Only using one pillar | Incomplete picture | Use all three together |
| Unstructured logs | Hard to search | Use structured JSON logs |
| Too many alerts | Alert fatigue | Alert on symptoms, not causes |
| Not propagating trace context | Broken traces | Pass trace IDs between services |

---

## Quiz

1. **What are the three pillars of observability?**
   <details>
   <summary>Answer</summary>
   Metrics (numerical measurements over time), Logs (timestamped event records), and Traces (request paths across distributed services). Together they provide complete visibility into system behavior.
   </details>

2. **What's the difference between a trace and a span?**
   <details>
   <summary>Answer</summary>
   A trace is the complete journey of a request through all services. A span is a single operation within that trace. One trace contains multiple spans, forming a tree of operations.
   </details>

3. **What is the RED method?**
   <details>
   <summary>Answer</summary>
   A methodology for monitoring services: Rate (requests/second), Errors (failed requests/second), Duration (time per request). It focuses on user-facing symptoms.
   </details>

4. **Why use structured logging?**
   <details>
   <summary>Answer</summary>
   Structured logs (JSON format) are machine-parseable, easily searchable, and have consistent format. Unstructured text logs are harder to query and analyze at scale.
   </details>

5. **How do metrics, logs, and traces work together?**
   <details>
   <summary>Answer</summary>
   Metrics detect problems (dashboard shows high latency), traces locate problems (which service is slow), logs explain problems (what error occurred). You investigate from metrics → traces → logs.
   </details>

---

## Summary

**Observability**:
- Understanding internal state from external outputs
- Goes beyond monitoring (known issues)
- Enables exploring unknown problems

**Three pillars**:
- **Metrics**: Numerical data over time
- **Logs**: Event records with context
- **Traces**: Request paths across services

**Methods**:
- **RED**: Rate, Errors, Duration (services)
- **USE**: Utilization, Saturation, Errors (resources)
- **4 Golden Signals**: Latency, traffic, errors, saturation

**Best practices**:
- Use all three pillars together
- Structured logging
- Alert on symptoms
- Propagate trace context

---

## Next Module

[Module 3.5: Observability Tools](../module-3.5-observability-tools/) - Prometheus, Grafana, Jaeger, and other observability tools in Kubernetes.

---
title: "Module 3.2: The Three Pillars of Observability"
slug: platform/foundations/observability-theory/module-3.2-the-three-pillars
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: [Module 3.1: What is Observability?](../module-3.1-what-is-observability/)
>
> **Track**: Foundations

---

## The Engineer Who Had Everything and Nothing

**October 2015. A Major Rideshare Company. 7:43 PM on New Year's Eve.**

The platform is about to handle 440% of normal traffic. The engineering team has prepared for months. They have comprehensive Prometheus metrics on every service. They have Elasticsearch with 2TB of logs. They have distributed tracing through Jaeger. All three pillars, best-in-class tooling.

At 11:52 PM, surge pricing stops working.

The on-call engineer opens Grafana. Latency spike on the pricing service—p99 jumped from 150ms to 8 seconds. Great, the metrics show *that* something is wrong.

She switches to Jaeger to find slow traces. But the trace UI only lets her search by trace ID or service name. She doesn't have a trace ID. She searches for "pricing-service" and gets 2 million results in the last hour. No way to filter by duration. No way to find the slow ones.

She pivots to Elasticsearch. Searches for "pricing" and "error." 847,000 results. None have trace IDs—the team never added them to logs. She can see errors happened but can't connect them to specific requests or traces.

**90 minutes**. That's how long it took to find the root cause: a database connection pool exhaustion that only manifested under New Year's Eve load. The fix was a single config change. But finding it required manually correlating timestamps across three disconnected tools.

**Cost**: $12.4 million in lost surge pricing revenue. 340,000 customer complaints. A PR crisis that took weeks to contain.

**The lesson**: They had all three pillars. What they didn't have was *correlation*. Without trace IDs in logs, without the ability to drill from metrics to traces, without exemplars connecting aggregates to specifics—the pillars were just three separate silos. Three blind investigators who couldn't share notes.

```
THE THREE PILLARS PARADOX
═══════════════════════════════════════════════════════════════════════════════

WHAT THE TEAM HAD                          WHAT THEY COULD DO
─────────────────────────────────────      ─────────────────────────────────────
☑ Prometheus metrics (2M series)           ✗ Find which specific requests failed
☑ Elasticsearch logs (2TB/day)             ✗ Connect a log to its trace
☑ Jaeger traces (100M spans/day)           ✗ Find traces matching a metric spike
                                           ✗ Query logs by trace_id
                                           ✗ Drill down from aggregate to specific

Having the pillars ≠ Having observability

WHAT THEY ADDED AFTER THE INCIDENT
─────────────────────────────────────────────────────────────────────────────
✓ trace_id in every log line
✓ Exemplars linking p99 metrics to sample traces
✓ Duration-based trace search
✓ Unified query UI that links all three

Same tools. 10-minute resolution time for similar incidents.
```

---

## Why This Module Matters

You've learned what observability is. Now, how do you actually achieve it?

The industry has converged on three complementary data types—**logs**, **metrics**, and **traces**—often called the "three pillars." Each has strengths and weaknesses. Used together with proper correlation, they give you the visibility to understand any system behavior.

This module teaches you what each pillar provides, when to use which, and critically—how to connect them so you can move seamlessly between different views of the same problem.

> **The Crime Scene Analogy**
>
> Investigating an incident is like investigating a crime. **Logs** are witness statements—detailed accounts of what happened. **Metrics** are statistics—how many, how often, trends over time. **Traces** are the timeline—reconstructing the sequence of events. A good investigator uses all three: statistics to find patterns, witnesses for details, timelines to understand causation.

---

## What You'll Learn

- What each pillar provides and its limitations
- When to use logs vs. metrics vs. traces
- How the three pillars work together
- The importance of correlation (trace IDs, request IDs)
- Modern alternatives and the "single pane of glass"

---

## Part 1: Logs

### 1.1 What Are Logs?

**Logs** are timestamped records of discrete events. They capture what happened, when, and context about the event.

```
LOGS: DISCRETE EVENTS
═══════════════════════════════════════════════════════════════

2024-01-15T10:32:15.123Z level=info msg="Request received"
    method=POST path=/api/checkout user_id=12345 request_id=abc-123

2024-01-15T10:32:15.456Z level=info msg="Payment processed"
    amount=99.99 currency=USD request_id=abc-123 duration_ms=333

2024-01-15T10:32:15.789Z level=error msg="Inventory check failed"
    item_id=SKU-789 error="connection timeout" request_id=abc-123

Each log entry is a snapshot of a moment in time.
```

### 1.2 Structured vs. Unstructured Logs

```
UNSTRUCTURED LOG (hard to query)
═══════════════════════════════════════════════════════════════
[2024-01-15 10:32:15] ERROR: Payment failed for user 12345,
order #789, amount $99.99 - connection timeout

- Human readable
- Hard to parse programmatically
- Can't easily filter by user_id or order
- Regex required for extraction


STRUCTURED LOG (easy to query)
═══════════════════════════════════════════════════════════════
{
  "timestamp": "2024-01-15T10:32:15.789Z",
  "level": "error",
  "message": "Payment failed",
  "user_id": 12345,
  "order_id": 789,
  "amount": 99.99,
  "currency": "USD",
  "error": "connection timeout",
  "request_id": "abc-123",
  "service": "payment-api",
  "version": "2.3.1"
}

- Machine parseable
- Easy to filter: WHERE user_id = 12345
- Easy to aggregate: COUNT BY error
- Context preserved as queryable fields
```

### 1.3 Log Strengths and Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| Rich detail and context | High storage cost |
| Flexible schema | Can be noisy |
| Good for debugging specifics | Hard to see patterns |
| Audit trail | Performance overhead if excessive |
| Natural for developers | Query can be slow at scale |

### 1.4 When to Use Logs

- **Debugging specific issues**: "What happened to request abc-123?"
- **Audit trails**: "Who did what when?"
- **Error details**: Stack traces, error messages, context
- **State changes**: "User X upgraded to premium"
- **Unusual events**: Things that don't happen often enough for metrics

> **Try This (2 minutes)**
>
> Look at a recent log line from your system. Does it have:
> - [ ] Timestamp with timezone
> - [ ] Log level
> - [ ] Request/trace ID
> - [ ] User identifier
> - [ ] Structured format (JSON)
>
> Each missing item reduces your ability to query and correlate.

---

## Part 2: Metrics

### 2.1 What Are Metrics?

**Metrics** are numeric measurements collected over time. They're optimized for aggregation and trending.

```
METRICS: NUMERIC TIME SERIES
═══════════════════════════════════════════════════════════════

http_requests_total{method="POST", path="/api/checkout", status="200"} 45623
http_requests_total{method="POST", path="/api/checkout", status="500"} 127

http_request_duration_seconds{quantile="0.99"} 0.456
http_request_duration_seconds{quantile="0.50"} 0.089

db_connections_active 47
db_connections_max 100

Each metric is a name + labels + numeric value over time.
```

### 2.2 Metric Types

| Type | What It Measures | Example |
|------|------------------|---------|
| **Counter** | Cumulative total (only goes up) | Total requests, total errors |
| **Gauge** | Current value (goes up and down) | Active connections, queue depth |
| **Histogram** | Distribution of values | Request latency distribution |
| **Summary** | Similar to histogram, pre-calculated quantiles | p50, p99 latencies |

```
METRIC TYPES VISUALIZED
═══════════════════════════════════════════════════════════════

COUNTER (monotonically increasing)
                                              ●
                                          ●
                                      ●
                                  ●
                              ●
                          ●
────────●────●────●────●──────────────────────────────────────▶
        ↑
    Resets only on restart

GAUGE (fluctuates)
           ●     ●
       ●       ●   ●        ●
    ●               ●    ●    ●
                       ●        ●
────────────────────────────────────────────────────────────▶
Current value at each point

HISTOGRAM (distribution)
    Count
    │
    │        ████
    │      ████████
    │    ████████████
    │  ████████████████
    └──────────────────────▶ Latency (ms)
      0   100  200  300  400
```

### 2.3 Metric Strengths and Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| Low storage cost | Loses individual event detail |
| Fast queries | Limited cardinality |
| Good for trends and alerting | Can't debug specific requests |
| Efficient aggregation | Pre-aggregated, can't re-aggregate differently |
| Compact representation | Choosing what to measure is hard |

### 2.4 When to Use Metrics

- **Alerting**: "Error rate above threshold"
- **Dashboards**: Real-time system health
- **Capacity planning**: Trends over time
- **SLI measurement**: Availability, latency percentiles
- **Business KPIs**: Requests per second, revenue per minute

> **Gotcha: The Cardinality Trap**
>
> Metrics with high-cardinality labels (user_id, request_id) explode storage costs. A metric with labels for 1 million users creates 1 million time series. Use logs for high-cardinality data, metrics for bounded dimensions (endpoint, region, status_code).

---

## Part 3: Traces

### 3.1 What Are Traces?

**Traces** capture the journey of a request through a distributed system. A trace is a tree of **spans**, each representing work done by a service.

```
DISTRIBUTED TRACE
═══════════════════════════════════════════════════════════════

Trace ID: abc-123-def-456

    ┌─────────────────────────────────────────────────────────┐
    │  API Gateway (50ms)                                     │
    │  └── Auth Service (10ms)                               │
    │  └── Order Service (35ms)                              │
    │       └── Inventory Service (15ms)                     │
    │       └── Payment Service (18ms)                       │
    │            └── Database Query (12ms)                   │
    │            └── External Payment API (5ms)              │
    └─────────────────────────────────────────────────────────┘

    Timeline:
    0ms    10ms   20ms   30ms   40ms   50ms
    |------|------|------|------|------|
    [====== API Gateway ====================]
      [Auth]
           [======= Order Service =========]
             [Inventory]
                    [=== Payment ====]
                      [DB]
                          [API]
```

### 3.2 Trace Components

| Component | What It Is | Example |
|-----------|------------|---------|
| **Trace** | Full request journey | trace_id: abc-123 |
| **Span** | Single unit of work | "Database query", "HTTP call" |
| **Parent Span** | The span that triggered this one | Order Service is parent of Payment Service |
| **Tags/Attributes** | Metadata on spans | http.status=200, db.query="SELECT..." |
| **Events/Logs** | Timestamped annotations within span | "Cache miss", "Retry attempt 2" |

### 3.3 Trace Propagation

For traces to work across services, trace context must be propagated:

```
TRACE CONTEXT PROPAGATION
═══════════════════════════════════════════════════════════════

Request from client:
    Headers: (none)

API Gateway generates trace:
    trace_id: abc-123
    span_id: span-001

API Gateway → Order Service:
    Headers:
      traceparent: 00-abc123-span001-01

Order Service creates child span:
    trace_id: abc-123 (same)
    span_id: span-002
    parent_id: span-001

Order Service → Payment Service:
    Headers:
      traceparent: 00-abc123-span002-01

All spans share trace_id, linked by parent relationships.
```

### 3.4 Trace Strengths and Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| Shows request flow across services | Storage cost (many spans per request) |
| Identifies slow components | Sampling often required |
| Reveals dependencies | Instrumentation overhead |
| Debug specific requests | Requires propagation (can break) |
| Shows parallelism and waiting | Complex to implement well |

### 3.5 When to Use Traces

- **"Where did the time go?"**: Identifying slow spans
- **Dependency mapping**: What calls what?
- **Debugging specific requests**: "What happened to request X?"
- **Finding bottlenecks**: Which service is the problem?
- **Understanding system architecture**: Visualizing flow

> **Did You Know?**
>
> Google processes over 10 billion requests per day. Even with aggressive sampling (0.01%), that's 1 million traces daily. Dapper, their tracing system, was designed around sampling from the start. Most tracing systems sample to control costs—you don't need every trace, just representative ones.

---

## Part 4: Connecting the Pillars

### 4.1 The Correlation Problem

Each pillar alone has blind spots:

```
PILLAR BLIND SPOTS
═══════════════════════════════════════════════════════════════

LOGS ALONE:
    ✅ "Error occurred in payment service"
    ❌ "Was this the slow request? What called payment service?"

METRICS ALONE:
    ✅ "Error rate increased at 3pm"
    ❌ "Which specific requests failed? What was the error?"

TRACES ALONE:
    ✅ "Request took 500ms, 400ms in database"
    ❌ "Is this normal? How many requests are affected?"

CONNECTED:
    ✅ Metric alert fires (error rate up)
    ✅ Drill into traces (which requests are errors)
    ✅ Look at logs (what's the error message)
    ✅ Full picture: "Database connection pool exhausted,
       affecting 5% of checkout requests"
```

### 4.2 Correlation via IDs

The key to connecting pillars: **shared identifiers**.

```
CORRELATION WITH TRACE ID
═══════════════════════════════════════════════════════════════

                    trace_id: abc-123
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌────────┐          ┌──────────┐          ┌────────┐
│  LOGS  │          │  TRACES  │          │ METRICS│
│        │          │          │          │        │
│trace_id│          │ trace_id │          │trace_id│
│=abc-123│          │ =abc-123 │          │exemplar│
│        │          │          │          │=abc-123│
└────────┘          └──────────┘          └────────┘

Query: "Show me everything for trace abc-123"
    → Logs from all services for this request
    → Trace showing timing and flow
    → Metrics at the time of this request
```

### 4.3 Exemplars: Connecting Metrics to Traces

**Exemplars** link aggregated metrics back to specific traces:

```
EXEMPLARS
═══════════════════════════════════════════════════════════════

Metric: http_request_duration_seconds (p99 = 450ms)

Without exemplar:
    "p99 latency is high, but which requests?"

With exemplar:
    "p99 latency is high, here's a trace showing one: abc-123"

Prometheus Exemplar format:
http_request_duration_seconds{path="/checkout"} 0.45 # {trace_id="abc-123"} 0.48

    ↓ Click trace_id

See full trace of a slow request that contributed to the p99.
```

### 4.4 The Correlation Workflow

```
INVESTIGATION WORKFLOW
═══════════════════════════════════════════════════════════════

1. ALERT (Metrics)
   "Error rate > 1% for /api/checkout"
   │
   ▼
2. SCOPE (Metrics)
   Break down by: region, user_tier, version
   "Errors concentrated in US-West, v2.3.1"
   │
   ▼
3. SAMPLE (Traces via Exemplar)
   Find example error traces
   "Trace abc-123 shows timeout to payment service"
   │
   ▼
4. DETAIL (Logs)
   Filter logs by trace_id
   "Connection refused: payment-db-03.us-west"
   │
   ▼
5. ROOT CAUSE
   "payment-db-03 was down for maintenance"
   "Traffic should have failed over but didn't"
```

> **Try This (3 minutes)**
>
> Map your current investigation workflow:
>
> | Step | Your Tool/Method | What's Missing? |
> |------|------------------|-----------------|
> | Alert | | |
> | Scope | | |
> | Sample | | |
> | Detail | | |
>
> Where do you get stuck? That's your correlation gap.

> **War Story: The $6.7 Million Investigation Gap**
>
> **2018. A Major Trading Platform. Monday Morning, Market Open.**
>
> At 9:31 AM Eastern, order execution latency jumped from 3ms to 400ms. For a high-frequency trading platform, this was catastrophic. Every millisecond of delay meant lost arbitrage opportunities. Customers were losing money—and switching to competitors in real-time.
>
> The platform had excellent tooling: Prometheus metrics with 50,000 time series, Elasticsearch ingesting 500GB of logs daily, and Zipkin handling 10 million spans per hour. On paper, world-class observability.
>
> **9:31 AM**: Alert fires. P99 latency above threshold.
> **9:34 AM**: Engineer opens Grafana. Confirms latency spike. Can see *which* services are slow but not *why*.
> **9:41 AM**: Switches to Zipkin. Searches for "order-execution" service. Gets 847,000 traces. No way to filter to just the slow ones. No latency-based search.
> **9:52 AM**: Opens Elasticsearch. Searches for "order" and "slow." 2.3 million results. Logs have timestamps but no trace IDs. Can't correlate to traces.
> **10:14 AM**: Resorts to manually comparing timestamps across tools. Tedious, error-prone.
> **10:47 AM**: Finally identifies pattern—slow requests all touched a specific Redis cluster.
> **10:52 AM**: Root cause found—Redis master failover during maintenance window wasn't announced. Connections were timing out during reconnection.
> **10:54 AM**: Fix applied—bump connection pool retry settings.
>
> **Time to resolution: 83 minutes.** Fix took 2 minutes. Finding the problem took 81.
>
> **Financial Impact**:
> - Lost trading volume during outage: $847,000
> - Customer churn (3 major clients left): $5.8 million annual revenue
> - Regulatory fine for execution delay: $120,000
> - **Total: $6.77 million**
>
> **The Postmortem**:
>
> | What They Had | What They Couldn't Do |
> |---------------|----------------------|
> | 50,000 Prometheus metrics | Find slow traces from metric spikes |
> | 500GB/day logs in Elasticsearch | Search logs by trace_id |
> | 10M spans/hour in Zipkin | Filter traces by duration |
> | Three world-class tools | Navigate between them |
>
> **What They Built After**:
> - Added trace_id to every log line (2 hours of work)
> - Added exemplars to latency histograms (4 hours)
> - Built unified search UI linking all three (2 weeks)
> - Next similar incident: 9 minutes to resolution
>
> **The math**: $6.77M cost ÷ 2 weeks engineering time = worth it.

---

## Part 5: Beyond the Three Pillars

### 5.1 The Pillars Critique

The "three pillars" framing has critics:

```
PILLAR PROBLEMS
═══════════════════════════════════════════════════════════════

SILOED THINKING
    "We have a logging system, a metrics system, a tracing system"
    → Three separate UIs, three separate queries, manual correlation

THE REAL NEED
    "We have events that describe system behavior"
    → Events can be viewed as logs, aggregated into metrics,
      connected into traces
    → Same underlying data, different lenses
```

### 5.2 Events-Based Observability

Modern observability thinking centers on **events**:

```
EVENTS-FIRST MODEL
═══════════════════════════════════════════════════════════════

Every interesting thing is an EVENT:
{
  "timestamp": "2024-01-15T10:32:15.789Z",
  "trace_id": "abc-123",
  "span_id": "span-001",
  "service": "payment-api",
  "operation": "process_payment",
  "duration_ms": 333,
  "user_id": "12345",
  "amount": 99.99,
  "status": "success",
  "db_queries": 3,
  "cache_hit": false
}

From this event, you can:
    → View as LOG: Full details of this operation
    → Compute METRICS: avg(duration_ms), count by status
    → Build TRACE: Connect via trace_id and span_id

One data model, multiple views.
```

### 5.3 OpenTelemetry: Unified Approach

**OpenTelemetry** (OTel) is becoming the standard for observability instrumentation:

```
OPENTELEMETRY
═══════════════════════════════════════════════════════════════

                    Application Code
                          │
                          ▼
              ┌──────────────────────┐
              │   OpenTelemetry SDK  │
              │                      │
              │  - Traces            │
              │  - Metrics           │
              │  - Logs              │
              └──────────┬───────────┘
                         │
              ┌──────────▼───────────┐
              │   OTel Collector     │
              │                      │
              │  Process, batch,     │
              │  export to backends  │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌─────────┐
    │ Jaeger  │    │Prometheus│    │  Loki   │
    │(Traces) │    │(Metrics) │    │ (Logs)  │
    └─────────┘    └──────────┘    └─────────┘

Benefits:
- Vendor-neutral instrumentation
- Consistent correlation (trace_id everywhere)
- One library, multiple signals
- Easy to switch backends
```

---

## Did You Know?

- **Netflix streams over 1 billion hours of video per week** and traces every request. They sample aggressively but keep 100% of traces for errors—you always want the full picture when something goes wrong.

- **The W3C Trace Context standard** defines how trace IDs propagate in HTTP headers. Before this standard, every tracing system had its own headers (Zipkin used B3, AWS used X-Amzn-Trace-Id). Now `traceparent` and `tracestate` are standard.

- **Logs are the oldest pillar**—Unix systems have had syslog since the 1980s. Metrics became common in the 2000s (RRDtool, Graphite). Traces emerged in the 2010s with Dapper and microservices. The history reflects increasing system complexity.

- **Uber built their own tracing system** called Jaeger (German for "hunter") in 2015, then open-sourced it. It was designed to handle their scale: billions of spans per day across thousands of microservices. Jaeger became a CNCF project and is now one of the most popular tracing backends.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No trace propagation | Traces break at service boundaries | Use OTel SDK, verify headers |
| High-cardinality metrics | Storage explosion, slow queries | Use logs for high-cardinality, metrics for bounded |
| Unstructured logs | Can't query or correlate | JSON with consistent fields |
| No request ID in logs | Can't find logs for a trace | Add trace_id to every log line |
| Separate tools, no correlation | Manual jumping between UIs | Use exemplars, linked IDs |
| Logging everything | Noise, cost, performance | Log meaningful events with context |

---

## Quiz

1. **When would you use logs instead of metrics?**
   <details>
   <summary>Answer</summary>

   Use **logs** when you need:
   - **Rich context**: Error messages, stack traces, request details
   - **High cardinality**: Data with many unique values (user_id, request_id)
   - **Specific debugging**: "What happened to this exact request?"
   - **Audit trails**: Who did what when
   - **Infrequent events**: Things that don't happen often enough to aggregate

   Use **metrics** when you need:
   - **Trends and aggregations**: "How many requests per second?"
   - **Alerting on thresholds**: "Error rate > 1%"
   - **Low-cardinality breakdowns**: By endpoint, by region
   - **Efficient storage**: Numeric data compresses well
   - **Fast dashboards**: Pre-aggregated for quick display
   </details>

2. **What is trace context propagation and why is it essential?**
   <details>
   <summary>Answer</summary>

   **Trace context propagation** is passing trace identifiers (trace_id, span_id, flags) from one service to the next as a request flows through a distributed system.

   It's essential because:
   1. **Without it, traces break**: Each service would start a new trace
   2. **Enables correlation**: All services' spans share the same trace_id
   3. **Shows causation**: Parent-child relationships reveal what called what
   4. **Allows debugging**: You can find all work done for a single request

   Propagation happens via HTTP headers (traceparent) or message metadata. If any service doesn't propagate, the trace is broken at that point.
   </details>

3. **What are exemplars and why do they matter?**
   <details>
   <summary>Answer</summary>

   **Exemplars** are links from aggregated metrics back to specific traces that contributed to those metrics.

   Why they matter:
   1. **Bridge metrics → traces**: "p99 latency is high" becomes "here's a specific slow request"
   2. **Enable drill-down**: Click a metric spike to see example traces
   3. **Reduce MTTR**: Go from aggregate problem to specific example quickly
   4. **Connect pillars**: Metrics alone don't show details; exemplars provide the path to details

   Without exemplars, you see "latency is high" but must manually hunt for examples. With exemplars, you click through immediately.
   </details>

4. **Why do critics argue the "three pillars" framing is problematic?**
   <details>
   <summary>Answer</summary>

   Critics (like Charity Majors) argue:

   1. **Creates silos**: Teams build separate logging, metrics, and tracing systems that don't talk to each other
   2. **Misses the point**: Observability is about understanding behavior, not about having three data types
   3. **Events are fundamental**: Logs, metrics, and traces are really different views of underlying events
   4. **Correlation is key**: The pillars only help if they're connected; treating them as separate defeats the purpose

   The better framing: "We collect rich events about system behavior. We can view them as logs (individual events), metrics (aggregates over time), or traces (connected journeys). They're the same data, different lenses."
   </details>

5. **A company generates 10,000 requests/second. They want to trace all requests but storage costs are prohibitive. If they sample at 1%, how many traces per day will they store? What requests should NOT be sampled?**
   <details>
   <summary>Answer</summary>

   **Calculation**:
   - 10,000 requests/second × 60 seconds × 60 minutes × 24 hours = 864,000,000 requests/day
   - At 1% sampling: 864,000,000 × 0.01 = **8,640,000 traces/day**

   **Requests that should NOT be sampled (keep 100%)**:
   1. **Errors**: Always trace failed requests—you need full details to debug
   2. **Slow requests**: Any request above p99 latency threshold
   3. **Key business transactions**: Payments, order completions, sign-ups
   4. **Known problematic endpoints**: Routes that historically have issues
   5. **Debug-flagged requests**: When a user reports an issue, they can add a header to force tracing

   **Head-based vs tail-based sampling**:
   - Head-based: Decide at request start (easy, but might miss interesting requests)
   - Tail-based: Decide at request end (can keep all errors/slow requests, harder to implement)
   </details>

6. **Your team has Prometheus metrics showing p99 latency increased. You want to find an example slow request to investigate. Without exemplars, list the steps you'd need to take. How do exemplars simplify this?**
   <details>
   <summary>Answer</summary>

   **Without exemplars (manual correlation)**:
   1. Note the timestamp of the p99 spike from Prometheus
   2. Switch to your tracing tool (Jaeger, Zipkin)
   3. Search for traces from that service around that timestamp
   4. Manually filter for traces with duration > p99 value
   5. If tracing tool doesn't support duration filtering, export traces and filter externally
   6. Hope you find a representative example

   **Time**: 10-30 minutes. Error-prone. Might not find the right trace.

   **With exemplars**:
   1. View p99 latency metric in Grafana
   2. Click the exemplar marker on the graph
   3. Jump directly to a trace that contributed to that p99 value
   4. Investigate

   **Time**: 30 seconds. Guaranteed to find a relevant trace.

   Exemplars are the bridge between "something is slow" and "here's a specific slow thing to investigate."
   </details>

7. **An engineer says "We use structured JSON logging, so we have observability." What's missing from this statement? What else would they need?**
   <details>
   <summary>Answer</summary>

   Structured logging is necessary but not sufficient for observability.

   **What structured logging provides**:
   - Queryable fields (can filter by user_id, error_code)
   - Consistent format (easy to parse)
   - Context preservation

   **What's still missing**:
   1. **Trace IDs**: Can they connect logs to traces? Without trace_id in logs, they're still isolated.
   2. **Request correlation**: Can they find all logs for a single request across services?
   3. **Metrics**: Logs alone don't show trends, aggregates, or enable alerting
   4. **Traces**: Logs don't show request flow, timing, or service dependencies
   5. **High-cardinality queries**: Can they ask "show me all logs where user_id=X AND error_code=Y"?
   6. **Cross-signal navigation**: Can they click from a log to its trace? From a metric spike to sample logs?

   Structured logs are the foundation. Full observability requires all three pillars connected via shared IDs.
   </details>

8. **Your checkout service makes 5 downstream calls (inventory, pricing, payment, shipping, notification). A trace shows total latency of 850ms. The spans show: inventory (45ms), pricing (180ms), payment (320ms), shipping (90ms), notification (40ms). The sum is 675ms, but total is 850ms. What explains the 175ms gap?**
   <details>
   <summary>Answer</summary>

   The 175ms gap (850ms - 675ms = 175ms) represents time spent in the **parent checkout service itself**, not in downstream calls.

   **This time could be**:
   1. **Service overhead**: Request parsing, response assembly
   2. **Sequential processing**: Time between finishing one call and starting another
   3. **Business logic**: Validation, transformation, calculations
   4. **Network latency**: Not captured in span duration (time waiting for response to arrive)
   5. **Queue time**: Time waiting in thread pool before processing

   **To investigate**:
   - Add more granular spans within the checkout service
   - Look for "gaps" in the waterfall view between child spans
   - Add spans for "validation," "marshal_request," "await_response"
   - Check if calls are sequential when they could be parallel (inventory + pricing could run in parallel)

   **Key insight**: Trace spans only show what you instrument. Missing time = missing instrumentation.
   </details>

---

## Key Takeaways

```
THREE PILLARS ESSENTIALS CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

UNDERSTANDING EACH PILLAR
☑ Logs = detailed events (what happened, high cardinality OK)
☑ Metrics = numeric aggregates (how many, low cardinality required)
☑ Traces = request journey (where time went, shows dependencies)

WHEN TO USE WHAT
☑ Debugging specific requests → Logs + Traces
☑ Alerting on thresholds → Metrics
☑ Finding patterns across users → Logs with structured fields
☑ Identifying slow components → Traces
☑ Capacity planning → Metrics (trends over time)

THE CORRELATION IMPERATIVE
☑ trace_id in EVERY log line (non-negotiable)
☑ Exemplars connecting metrics to sample traces
☑ Same timestamp format across all pillars
☑ Unified UI or linked navigation between tools

CARDINALITY RULES
☑ Metrics: bounded dimensions only (endpoint, region, status_code)
☑ Logs: high cardinality welcome (user_id, request_id, session_id)
☑ Traces: sampling for volume control, 100% for errors

THE EVENTS PERSPECTIVE
☑ Pillars are views, not silos
☑ Same underlying data, different lenses
☑ OpenTelemetry unifies instrumentation
☑ Goal: answer questions you didn't anticipate
```

---

## Hands-On Exercise

**Task**: Design an observability strategy using all three pillars.

**Scenario**: You're building a checkout service that:
- Receives orders from users
- Validates inventory
- Processes payments
- Sends confirmation emails

**Part 1: Design Structured Logs (10 minutes)**

For each key event, define the log structure:

| Event | Log Level | Key Fields |
|-------|-----------|------------|
| Order received | INFO | timestamp, trace_id, user_id, order_id, items[], total |
| Inventory checked | INFO | timestamp, trace_id, order_id, items_available, items_unavailable |
| Payment attempt | INFO | timestamp, trace_id, order_id, amount, payment_method |
| Payment failed | ERROR | timestamp, trace_id, order_id, error_code, error_message |
| Email sent | INFO | timestamp, trace_id, order_id, email_type, recipient |

Add 2-3 more events relevant to your scenario:

| Event | Log Level | Key Fields |
|-------|-----------|------------|
| | | |
| | | |
| | | |

**Part 2: Design Metrics (10 minutes)**

Define metrics for monitoring and alerting:

| Metric Name | Type | Labels | Purpose |
|-------------|------|--------|---------|
| checkout_requests_total | Counter | status, payment_method | Track volume and success rate |
| checkout_duration_seconds | Histogram | step (validate, pay, email) | Track latency by phase |
| inventory_availability | Gauge | item_category | Monitor stock levels |
| payment_failures_total | Counter | error_code, provider | Track payment issues |

Add 2-3 more metrics:

| Metric Name | Type | Labels | Purpose |
|-------------|------|--------|---------|
| | | | |
| | | | |
| | | | |

**Part 3: Design Traces (10 minutes)**

Define the span structure for a checkout request:

```
Trace: checkout-{order_id}
│
├── Span: receive_order
│   └── Tags: user_id, item_count, total_amount
│
├── Span: validate_inventory
│   └── Tags: items_checked, items_available
│   └── Child: db_query (inventory lookup)
│
├── Span: process_payment
│   └── Tags: amount, method, provider
│   └── Child: external_api_call (payment gateway)
│
└── Span: send_confirmation
    └── Tags: email_type, recipient
    └── Child: smtp_send
```

Add timing expectations:
- Total checkout: ____ms expected
- Which span is likely the bottleneck? ____

**Part 4: Correlation Plan (5 minutes)**

How will you connect the three pillars?

| Correlation Need | Solution |
|------------------|----------|
| Find logs for a trace | Include trace_id in every log |
| Find traces for a metric spike | Use exemplars with trace_id |
| Find metrics for a time window | Query by timestamp range |
| | |

**Success Criteria**:
- [ ] At least 5 meaningful log events defined with fields
- [ ] At least 4 metrics with appropriate types and labels
- [ ] Trace structure with at least 4 spans
- [ ] Correlation strategy defined (trace_id in logs, exemplars)

---

## Further Reading

- **"Distributed Systems Observability"** - Cindy Sridharan. Excellent coverage of all three pillars.

- **OpenTelemetry Documentation** - https://opentelemetry.io/docs/. The emerging standard for instrumentation.

- **"Three Pillars with Zero Answers"** - Charity Majors (blog post). The critique of pillar-centric thinking.

---

## Next Module

[Module 3.3: Instrumentation Principles](../module-3.3-instrumentation-principles/) - How to add observability to your code: what to instrument, where, and how.

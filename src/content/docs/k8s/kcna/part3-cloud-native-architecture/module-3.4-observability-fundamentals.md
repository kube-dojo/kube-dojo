---
revision_pending: false
title: "Module 3.4: Observability Fundamentals"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.4-observability-fundamentals
sidebar:
  order: 5
---

# Module 3.4: Observability Fundamentals

Complexity: `[MEDIUM]` - Observability concepts for Kubernetes 1.35 and newer. Time to complete: 45-55 minutes. Prerequisites: Module 3.3, Cloud Native Patterns, plus basic comfort reading Pods, Services, and application logs in a Kubernetes cluster.

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Compare** monitoring and observability when a team must move from known-unknowns to unknown-unknowns.
2. **Diagnose** a service incident by combining metrics, logs, traces, and trace IDs in a repeatable investigation.
3. **Design** Kubernetes alerting and instrumentation practices using RED, USE, and symptom-based paging.
4. **Evaluate** observability maturity, cardinality, retention, and security tradeoffs before they damage operations.

## Why This Module Matters

At 2:13 a.m. during a regional retail promotion, a checkout platform began returning slow responses from only a fraction of requests. The uptime probe still said the site was available, the load balancer looked healthy, and the database dashboard showed no obvious outage, yet support tickets were arriving faster than the on-call engineer could read them. The business impact was not abstract: several minutes of degraded checkout during a high-demand event can mean abandoned carts, expensive incident coordination, and damaged trust that takes longer to repair than the actual bug.

The team that recovered quickly was not the team with the prettiest dashboard. It was the team that could connect user-facing symptoms to service-level metrics, follow one slow request across several services, and land on the log line that explained the bottleneck without guessing. Observability matters because cloud native systems fail in combinations: a safe deployment, a warm cache, a retry policy, and a small connection pool can interact in a way no single alert rule predicted.

This module teaches observability as an operating discipline rather than a product category. You will compare monitoring with observability, learn how metrics, logs, and traces answer different questions, and practice choosing the right signal during a Kubernetes incident. The goal is not to memorize tool names for the KCNA exam. The goal is to reason like an operator who can turn confusing symptoms into a defensible next action.

## What Observability Means in Practice

Observability is the ability to infer the internal state of a system by examining its external outputs. In a Kubernetes application, those outputs usually include metrics emitted by services and infrastructure, logs written by containers to standard streams, and traces that preserve the path of a request across service boundaries. The word is older than cloud native computing, but the need became urgent when a single user action started depending on many independently deployed components.

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

Monitoring and observability are related, but they are not interchangeable. Monitoring works best when the team already knows which symptoms matter and can encode those symptoms as dashboards or alert rules. Observability becomes valuable when the failure is unfamiliar, the blast radius is partial, or the system is technically up while customers are still harmed. A smoke alarm is monitoring; a building inspection with floor plans, sensor history, and witness accounts is observability.

The known-unknown and unknown-unknown distinction is useful because it changes how you ask questions. A known-unknown is something like "will CPU saturation exceed our alert threshold tonight?" because the risk is understood and the measurement is predefined. An unknown-unknown is something like "why do only first-time buyers using one payment method see slow checkout after a harmless deployment?" because the shape of the problem emerges during investigation. Good observability lets you ask that second question without shipping new debugging code during the incident.

In Kubernetes, the platform gives you useful raw material but not a complete observability system. The kubelet can expose container resource data, Pods can write logs to stdout and stderr, and service meshes or instrumented libraries can propagate trace context, yet those signals still need collection, storage, indexing, correlation, and retention policies. A cluster can be technically observable in small pieces while still being operationally opaque to the people on call.

Pause and predict: if a checkout service is returning errors for only one region while the global uptime check stays green, which signal would prove the user-facing symptom first, and which signal would help you avoid blaming the wrong dependency?

The most important mental shift is that observability is designed around questions, not around screens. A dashboard that nobody trusts is decoration, while a narrow metric with the right labels can immediately show whether an incident affects one route, one status code, or one version. A beautiful trace waterfall is not enough either if logs do not include trace IDs, because the trace can show where time was spent but not always why a database client refused a connection.

## The Three Pillars as Complementary Evidence

The classic three pillars are metrics, logs, and traces. That framing is sometimes criticized because modern observability also includes profiles, events, exemplars, service graphs, and continuous runtime data, but it remains a practical KCNA foundation. The pillars are not three competing tools. They are three kinds of evidence that become stronger when they share time windows, service names, deployment versions, and correlation IDs.

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

Think of observability like diagnosing a patient in a hospital, but be precise about the analogy. Metrics are the vitals: heart rate, blood pressure, oxygen saturation, and temperature tell clinicians that something is changing and whether the patient is improving. Traces are the imaging study because they reveal where a request traveled and which part of the body of services absorbed the delay. Logs are the patient history and clinical notes because they provide detailed facts about specific events at specific times.

Metrics are numerical measurements over time, and they are usually the first signal an operator sees during an incident. A service might emit request counts, error totals, duration histograms, queue depth, memory usage, garbage collection pauses, or database pool saturation. Metrics are compact and cheap compared with full logs, which makes them excellent for dashboards and alerts, but the same compression that makes them efficient also removes detail.

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

The RED method is a service-oriented way to choose metrics. Rate tells you how much traffic the service receives, errors tell you how much of that traffic fails, and duration tells you how long successful or failed requests take. RED is powerful because it maps directly to user experience: a service that is slow, failing, or receiving unusual traffic deserves attention even if every node still has spare CPU.

### The RED Method

For services, track:

| Metric | Description |
|--------|-------------|
| **R**ate | Requests per second |
| **E**rrors | Failed requests per second |
| **D**uration | Time per request |

The USE method complements RED by focusing on resources instead of request paths. Utilization asks how busy the resource is, saturation asks whether work is waiting, and errors ask whether the resource itself reports failure. In Kubernetes, USE can apply to CPU, memory, disks, network interfaces, queues, connection pools, and any shared dependency that can become a bottleneck. A node at high utilization is not automatically an incident, but a saturated queue plus rising request duration is a serious clue.

### The USE Method

For resources, track:

| Metric | Description |
|--------|-------------|
| **U**tilization | % time resource is busy |
| **S**aturation | Work queued/waiting |
| **E**rrors | Error count |

Logs are timestamped records of events, and they carry the details that metrics intentionally omit. A useful log line says which service emitted it, when it happened, what operation was attempted, which request or trace it belonged to, and which safe identifiers help connect it to other evidence. The difference between "payment failed" and a structured event with `service`, `level`, `trace_id`, `order_id`, and a sanitized error code is the difference between searching a haystack and querying a record.

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

Kubernetes shapes logging practices in a specific way. Containers should generally write application logs to stdout and stderr, then a node-level or sidecar collector can move those logs to a backend such as Loki, Elasticsearch, or another system. That approach decouples application code from log shipping, but it also means teams must standardize fields before logs leave the Pod. If every service invents different names for request identifiers, logs become hard to correlate during exactly the moment when clarity matters most.

Traces follow requests across distributed systems by representing the total journey as a trace and each operation as a span. When a request enters an API gateway, calls an order service, reaches a payment service, and then queries a database, a trace can show which hop consumed time and which parent operation caused it. Tracing is most useful when context propagation works across every boundary, including HTTP, gRPC, messaging systems, background jobs, and service mesh proxies.

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

Trace terminology is simple, but the operational consequences are important. A trace ID should let you find the full request journey, while span IDs and parent span relationships preserve the shape of the work. Context propagation is the act of passing those identifiers onward so the next service can attach its work to the same trace. When propagation breaks, the system may still collect spans, but the request appears as disconnected fragments.

### Trace Terminology

| Term | Description |
|------|-------------|
| **Trace** | Complete request journey (all spans) |
| **Span** | Single operation within trace |
| **Trace ID** | Unique identifier for the trace |
| **Span ID** | Unique identifier for the span |
| **Parent Span** | The calling operation |
| **Context propagation** | Passing trace ID between services |

Before running this in a real cluster, what output would you expect if an application includes trace IDs in logs but one downstream service does not propagate trace context? The logs may still contain request details for each service, but the tracing backend will show a gap or a separate trace where you expected one continuous waterfall. That mismatch is a diagnostic clue, not just a tooling annoyance.

## Connecting Signals During an Incident

The best incident investigations move from broad symptoms to specific causes without pretending that one signal can answer every question. Metrics detect and scope the problem, traces locate the slow or failing segment of a request path, and logs explain the local reason for the failure. That sequence is not a law, because sometimes a log-based alert or a trace exemplar is the first clue, but it is a reliable default when the incident starts with a user-facing symptom.

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

Consider the Black Friday outage pattern from the original lesson. During a massive holiday sale, the monitoring dashboard lit up red because order success rates dropped, which gave the team a clear metric symptom. They opened tracing and found requests stuck inside the `inventory-service` span, which narrowed the search from the whole platform to one dependency path. Then they queried logs by trace ID and found connection timeouts to a legacy database with a full connection pool.

The reason that story matters is not the specific inventory database. The lesson is that each signal changed the search space. Metrics turned customer complaints into a measurable incident, traces prevented the team from investigating unrelated services, and logs revealed the concrete failure mode that could be mitigated. Without correlation, the same team might have stared at aggregate dashboards while restarting healthy components.

In Kubernetes, a disciplined triage often starts with service-level symptoms and then moves down to Pod and node evidence. You might compare error rate by route and deployment version, inspect a slow trace for the service span that dominates latency, and then use `k logs` or a log backend to inspect events near the same trace ID. The command-line habit still matters, so introduce the shortcut once in your shell with `alias k=kubectl` and then use `k` consistently in exercises and runbooks.

The alias is small, but the surrounding discipline is not. A runbook that says "look at the dashboard" is weaker than a runbook that says "confirm user-facing latency, choose a representative slow trace, query logs by trace ID, and record the suspected resource saturation." Precision reduces debate during an incident because it makes the next action observable too. The on-call engineer should know what evidence would confirm or disprove the current theory.

Pause and predict: a user reports slow checkout, metrics show `checkout_duration_p99` rising, and a trace shows payment calls consuming most of the request time. Which log fields would make the next query decisive, and what would be missing if the logs only contained free-form text?

There is a second ordering skill that beginners often miss: use the signal that matches the question. "How many users are affected?" is usually a metrics question. "Which service absorbed the delay?" is usually a trace question. "Which exception, rejection, or timeout happened inside that service?" is usually a log question. When teams mix these questions, they waste time asking logs to estimate fleet-wide impact or asking dashboards to explain one stack trace.

## Alerting, Instrumentation, and Kubernetes Reality

Alerting turns measurements into human interruptions, so it deserves the same design care as application code. A useful alert should describe a user-facing symptom, point to a likely investigation path, and fire only when a human can take meaningful action. A noisy alert trains the team to ignore the monitoring system, which is worse than having no alert because it creates false confidence before the real incident arrives.

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

Symptom-based paging does not mean cause-based metrics are useless. CPU, memory, queue depth, garbage collection time, disk latency, and connection pool saturation are excellent diagnostic data, and they often explain why the symptom occurred. The difference is where they belong. A page should usually wake someone for latency, error budget burn, failed requests, or customer-visible unavailability, while cause metrics should enrich dashboards, annotations, and runbooks.

Instrumentation is the work of making software emit useful signals before an incident. For Kubernetes workloads, that can include application metrics on a scrape endpoint, structured logs with consistent fields, OpenTelemetry tracing, Kubernetes events, and workload labels that identify service, namespace, version, and environment. Instrumentation is not finished when data exists. It is finished when the data can be joined across tools quickly enough to guide a decision.

Kubernetes adds useful metadata, but teams must avoid turning every label into a metric dimension. A metric label such as HTTP method or status code has bounded values, which makes it safe for time-series storage. A label such as user ID, session ID, or raw URL path can create millions of series, raising memory cost and making queries unreliable. Put high-cardinality details in logs or traces where they can be searched for specific investigations instead of stored as always-on metric dimensions.

The same caution applies to security and privacy. Logs should never contain plain-text passwords, payment card numbers, private tokens, or full request bodies that expose sensitive data. Traces can also leak data through span attributes if instrumentation captures raw headers or query strings. Observability exists to make systems operable, not to create a second database of secrets. Sanitization, allowlisted fields, retention limits, and role-based access are part of the design.

Maturity grows in stages, and each stage enables a different kind of operation. A low-maturity team may have basic uptime checks and raw logs, which helps detect total outages but makes partial failures painful. A mid-maturity team has RED metrics, structured logs, and traces for critical paths, which supports faster triage. A high-maturity team connects signals to deployments, service ownership, error budgets, and runbooks, which supports learning after the incident rather than only surviving it.

Which approach would you choose here and why: adding a `user_id` label to a high-volume request counter, or adding the same user identifier as a structured log field and trace attribute with retention controls? The metric label makes broad queries expensive and unstable, while the log or trace field preserves targeted debugging value without multiplying every time series by the user population. That tradeoff is central to observability design.

One practical Kubernetes workflow is to pair platform signals with application signals. The platform can show whether Pods restarted, whether a Deployment rolled out, whether CPU throttling appeared, or whether a node experienced pressure. The application can show request rates, dependency errors, business operation failures, and trace spans. Incidents become clearer when deployment annotations, Pod labels, and application versions appear in the same timeline as latency and error changes.

The KCNA exam expects vocabulary, but real operation expects judgment. Metrics without labels cannot segment impact; metrics with reckless labels can take down the monitoring backend. Logs without structure are cheap to write but expensive to search; logs with sensitive data create security risk. Traces without sampling may be unaffordable at high traffic; traces with bad sampling may miss the one request that explains the incident. Good teams make these tradeoffs deliberately.

### Worked Example: A Cart Service That Is Slow Only Sometimes

Imagine a cart service that normally responds in 180 milliseconds but now has a p99 duration above three seconds for a subset of requests. The first mistake would be to ask every engineer for a theory before agreeing on the symptom. A better first move is to confirm the metric, determine whether errors rose with latency, and segment the data by safe dimensions such as route, status code, namespace, and application version. That turns "the cart is slow" into an operationally useful statement.

The metric view might show that `GET /cart` latency rose only for requests that include inventory enrichment. That does not prove inventory is broken, but it narrows the next question enough to choose tracing. A representative slow trace could show a frontend span, a cart span, an inventory span, and a database span under inventory. If the inventory span consumes nearly all of the request time, the team has evidence that the bottleneck sits beyond the cart service rather than inside the frontend.

At that point, logs become valuable because the trace has identified where to look. Querying inventory logs by trace ID might reveal repeated messages about connection pool waits, retry attempts, or timeouts from a database client. The strongest log record includes a timestamp, service name, version, trace ID, safe request identifier, dependency name, error class, and duration. With those fields present, the investigation can move from "inventory is slow" to "inventory is waiting for database connections after version 2026.05.02 was deployed."

Now compare that evidence chain with a weaker one. If the team had only CPU dashboards, they might notice that the inventory Pods are using more CPU than usual and restart them, even though CPU is a consequence of retries rather than the root cause. If the team had only raw text logs, they might search for "timeout" across every service and drown in unrelated messages. If the team had only traces without log correlation, they might know where time was spent but not why the dependency refused work.

The same example also shows why service ownership metadata matters. When the inventory span appears in a trace, the on-call engineer should know which team owns it, which runbook applies, which dashboard shows its RED metrics, and which recent deployments changed it. Without that metadata, observability still produces data, but coordination becomes slow. High-quality observability shortens both the technical search and the human handoff.

### Sampling, Retention, and Cost Are Design Choices

New teams sometimes assume observability data should be complete forever. That instinct is understandable because missing data during an incident is frustrating, but unlimited collection is rarely affordable or safe. Metrics are usually retained longer because they are compact after aggregation, logs often need tiered retention because volume is high, and traces commonly require sampling because high-traffic services can produce enormous event streams. The design question is what evidence must be available for the decisions the team actually makes.

Sampling is easiest to understand with traces. Keeping every trace for every request may be useful in a small lab, but a busy production service can generate far more traces than the team can store or inspect. Head-based sampling chooses whether to keep a trace near the start of the request, which is simple but may miss rare failures. Tail-based sampling decides after seeing the request outcome, which can preserve slow or failed traces but requires more collector capacity and buffering.

Metrics have a different cost shape because the dangerous variable is usually cardinality. A counter with method and status labels may produce a small, predictable number of series. The same counter with user ID, raw URL, session ID, and request ID can produce a new series for almost every request. The storage backend must track those series in memory and on disk, so the cost explosion can happen even before anyone writes an expensive query.

Logs sit between those worlds. They are detailed enough to answer specific questions, but that detail makes them heavy and risky if teams log everything. Retention should reflect operational value and sensitivity: recent error logs may need fast search, older routine info logs may move to cheaper storage, and sensitive audit data may require stricter access or shorter retention. A good logging policy says what to keep, what to redact, who can read it, and how long it remains useful.

The cost conversation should happen during design, not only after the bill arrives. Ask which signals support alerting, which support incident diagnosis, which support compliance, and which are merely interesting. A signal that nobody uses in a runbook, service review, audit, or post-incident analysis may not justify long retention. Observability is valuable because it enables decisions, so every expensive signal should be tied to a decision it improves.

### What Kubernetes Adds and What It Does Not Add

Kubernetes gives workloads a common operating substrate, which makes some observability tasks easier. Pods have namespaces, labels, owners, restart counts, resource requests, limits, and events. Services and Ingress objects identify traffic paths. Deployments and ReplicaSets describe rollout state. These platform objects provide context that bare processes do not have, and observability systems can attach that context to metrics, logs, and traces so incidents can be segmented by workload and version.

Kubernetes does not automatically make an application observable. A Pod can restart often while the application emits no useful logs. A Service can route traffic while the application provides no request duration metric. A Deployment can roll out cleanly while a downstream dependency starts timing out under a new traffic pattern. Platform health and application health overlap, but neither replaces the other. Operators need both views during a real incident.

One practical habit is to annotate dashboards and traces with deployment changes. If latency rises immediately after a rollout, the team should see that event in the same timeline as the symptom. That does not prove the rollout caused the incident, but it makes the hypothesis testable. The team can compare old and new versions, check whether only new Pods fail, and decide whether a rollback is safer than deeper investigation while customers are affected.

Another habit is to distinguish readiness from true service quality. A readiness probe tells Kubernetes whether a Pod should receive traffic, but it may not cover every dependency or business path. A service can pass readiness while one important route fails. Observability closes that gap by measuring real request outcomes, dependency spans, and application-level errors. Readiness protects routing; observability protects reasoning.

### From Incident Response to Learning

The strongest observability programs feed post-incident learning back into instrumentation. After an incident, the team should ask which signal first detected the problem, which signal narrowed the search, which signal was missing, and which alert or dashboard created noise. Those answers are more useful than a generic demand for more monitoring. They point to concrete improvements such as adding trace IDs to error logs, bounding a metric label, or creating a symptom alert for a critical workflow.

Post-incident work should also remove misleading signals. If an alert fired repeatedly without requiring action, tune it, route it differently, or delete it. If a dashboard panel is always ignored because it never changes decisions, replace it with a view that answers a real runbook question. Observability quality is not measured by the number of panels or retained terabytes. It is measured by whether the next incident becomes easier to detect, explain, and resolve.

For KCNA learners, this learning loop is important because the exam vocabulary can sound static. Metrics, logs, traces, RED, USE, and golden signals are not flashcards floating in isolation. They are tools in a feedback system where production experience improves the next design. A team that treats observability as continuous improvement will gradually turn unknown-unknowns into known-unknowns, then encode the most important known-unknowns as reliable monitoring.

This is also why observability belongs early in application design. Adding instrumentation after a crisis is possible, but it often produces inconsistent field names, fragile dashboards, and panic-driven alerts. When teams define service names, metric labels, log fields, trace propagation, and ownership metadata during development, they create a shared language before stress arrives. That shared language is what lets a beginner follow the same evidence path as a senior engineer during an incident.

### Reviewing Observability Before Production

A useful pre-production review starts with the critical user journeys rather than the infrastructure inventory. For each journey, name the symptom that would matter to a user, the service that owns the journey, and the metric that would prove degradation. Then ask whether a trace can follow the journey across the main dependencies and whether logs can explain failures at each service boundary. This keeps the review grounded in decisions instead of drifting into tool coverage.

The next review question is whether the data will still be useful when the system is under stress. A metric that works during a demo may be too high-cardinality during a launch. A trace that works for synchronous HTTP may lose context when work moves through a queue. A log field that looks safe in development may contain sensitive values once real payloads arrive. Production readiness means testing the assumptions behind the signals, not only checking that exporters are running.

Teams should also review names as carefully as they review code. If one service logs `traceId`, another logs `trace_id`, and a third logs `correlation`, incident queries become slower and more error-prone. If metrics use different service labels than traces, dashboards cannot link cleanly to request examples. Consistent naming sounds mundane, but it is the index that lets people move between tools while pressure is high and memory is unreliable.

Ownership is another production-readiness signal. Every alert should have an owner, every critical dashboard should have a maintenance path, and every runbook should say what evidence changes the responder's next action. Without ownership, observability assets decay into archived good intentions. With ownership, the team can tune thresholds, retire noisy panels, and keep instrumentation aligned with how the service actually behaves.

The final review question is what the team will deliberately ignore. Not every possible measurement deserves collection, storage, or paging. Some debug logs should stay disabled until needed, some traces can be sampled aggressively, and some infrastructure metrics belong in capacity planning rather than incident paging. A mature team is not the team that collects everything. It is the team that can explain why each retained signal is worth its cost, risk, and operational attention.

These review habits make the hands-on triage later in the module more realistic. During an incident, you should not be inventing service names, debating whether logs contain trace IDs, or discovering that a critical dependency was never instrumented. The purpose of pre-production observability work is to make the stressful path boring: confirm the symptom, follow the request, read the local explanation, and choose the next mitigation with evidence.

There is one more habit that separates useful observability from expensive telemetry: write down the question before adding the signal. If the question is "are customers harmed," the signal should measure customer-facing behavior. If the question is "which dependency is slow," the signal should preserve request path and timing. If the question is "why did this operation fail," the signal should carry safe local context. That discipline prevents teams from collecting data because it is available and pushes them to collect data because it changes a decision.

## Patterns & Anti-Patterns

Strong observability patterns make investigations repeatable. They do not require every team to use the same vendor or store all data forever, but they do require shared conventions for service names, environments, versions, trace IDs, and severity. When those conventions are stable, a new engineer can follow evidence across tools without knowing every service in advance. That is why observability is as much a sociotechnical practice as a technical one.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Symptom-first alerting | Paging humans for production incidents | It ties interruption to customer impact instead of internal noise | Keep cause metrics on dashboards and link them from alert runbooks |
| Correlated signals | Investigating distributed requests | Shared trace IDs and service labels connect metrics, logs, and traces | Standardize field names across languages and teams |
| Bounded metric labels | Designing Prometheus-style metrics | Low-cardinality labels keep storage predictable and queries fast | Move high-cardinality facts to logs, traces, or exemplars |
| Deployment-aware timelines | Debugging after releases | Version and rollout annotations reveal whether symptoms follow a change | Automate annotations from CI/CD rather than relying on memory |

Anti-patterns usually come from reasonable instincts taken too far. A team adds more alerts because it missed an incident, then alert fatigue makes the next incident easier to miss. A developer adds user-level labels because they want better debugging, then the time-series database collapses under cardinality. A platform team collects every log forever because storage feels cheap, then security auditors find sensitive data spread across a system nobody treats as a database.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Dashboard theater | Teams maintain many panels but cannot answer incident questions | Start from runbook questions and build only the views that support decisions |
| Cause-only paging | CPU or memory alerts wake people even when users are fine | Page on latency, errors, availability, or error budget burn |
| Broken trace context | Request paths appear as disconnected spans | Enforce propagation headers and test instrumentation in integration paths |
| Raw payload logging | Sensitive data and noisy records enter the log backend | Log allowlisted fields, sanitize values, and apply retention by data class |

The shorthand table below preserves the operational warnings from the original lesson. Read it as a compact checklist after you understand the tradeoffs behind each row, not as a replacement for the investigation discipline described above.

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Only using one pillar | Incomplete picture | Use all three together |
| Unstructured logs | Hard to search | Use structured JSON logs |
| Too many alerts | Alert fatigue | Alert on symptoms, not causes |
| Not propagating trace context | Broken traces | Pass trace IDs between services |
| High cardinality metrics | Explodes storage costs | Use labels with bounded values |
| Alerting on internal causes | Unnecessary wake-ups | Alert on user-facing symptoms |
| Logging sensitive data | Security breaches | Sanitize and mask PII |
| Infinite metric retention | Consumes expensive storage | Downsample older metrics |

## Decision Framework

When an incident starts, choose the first signal based on the decision you need to make. If the decision is whether to declare an incident, start with metrics that measure user impact. If the decision is which dependency to inspect, start with traces that show the request path. If the decision is which fix to apply, use logs and resource metrics to confirm the local cause. The signal should reduce uncertainty, not simply add more data to the room.

| Decision Question | Start With | Confirm With | Avoid |
|-------------------|------------|--------------|-------|
| Are users affected right now? | RED metrics and availability checks | Error budget burn, regional or route breakdowns | Starting with CPU and assuming impact |
| Where is the request slowing down? | Distributed trace for a representative slow request | Service metrics for the suspected span | Reading every service log in order |
| Why did this service fail locally? | Structured logs filtered by trace ID and time | Resource saturation, dependency errors, deployment events | Grepping unstructured logs across all Pods |
| Should this wake someone? | Symptom severity and duration | Runbook actionability and business impact | Paging on every cause metric threshold |
| Can we afford this signal? | Cardinality and retention review | Sampling policy, access controls, storage estimates | Treating all observability data as free |

Use this simple flow during a Kubernetes service incident. First, confirm the symptom with service metrics such as rate, errors, and duration. Second, segment the symptom by namespace, service, route, status code, region, and version without adding unbounded labels. Third, inspect a trace that represents the failure path and identify the span that dominates latency or returns the error. Fourth, query logs for the same trace ID and compare the result with platform evidence such as Pod restarts or rollout events.

The framework also helps when no incident is active. During design review, ask whether each critical service has at least one symptom alert, a small set of RED metrics, structured logs with trace IDs, and traces for important request paths. During cost review, ask which labels produce the most series, which logs carry sensitive fields, and which trace sampling policy balances coverage with expense. Observability design is never separate from reliability design because both decide what the team can know under pressure.

## Did You Know?

- **The term has control theory roots.** Observability originally described whether a system's internal state could be determined from external outputs, a concept that became newly practical for software as distributed systems made direct inspection impossible.
- **OpenTelemetry became a CNCF project in 2019.** It unified earlier OpenTracing and OpenCensus efforts so teams could instrument metrics, logs, and traces without binding every application to one vendor from the start.
- **Cardinality can dominate cost faster than traffic.** A single metric label with millions of possible values can create millions of time series, even if the application emits only one counter name.
- **The SRE golden signals are four user-centered views.** Latency, traffic, errors, and saturation give teams a compact way to monitor services without pretending that every internal metric deserves a page.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Treating monitoring and observability as synonyms | Dashboards feel like proof that the system is observable | Keep dashboards for known-unknowns, and add logs, traces, and correlation fields for unknown-unknowns |
| Alerting on CPU before user impact | Cause metrics are easy to collect and easy to threshold | Page on symptoms such as latency, errors, and availability, then link CPU views for diagnosis |
| Adding user IDs as metric labels | Teams want per-user debugging from every tool | Keep metric labels bounded, and place user identifiers in sanitized logs or traces with access control |
| Leaving trace IDs out of logs | Logging and tracing are implemented by different libraries or teams | Standardize fields so every error log can be joined to a trace and service version |
| Collecting unstructured log text | Developers optimize for quick local printing rather than fleet-wide search | Emit structured logs with consistent keys, levels, timestamps, service names, and safe identifiers |
| Forgetting Kubernetes rollout context | The team investigates runtime symptoms without checking recent changes | Add deployment annotations and version labels to metrics, logs, traces, and incident timelines |
| Storing sensitive data in observability systems | Debug logging captures payloads, headers, or secrets during development | Use allowlisted fields, redaction, retention limits, and restricted access for observability backends |

## Quiz

<details><summary>Your team has uptime monitoring and CPU dashboards, but a partial checkout failure is affecting only new buyers in one region. How would you compare monitoring and observability for this known-unknown versus unknown-unknown situation?</summary>

Monitoring can confirm predefined conditions such as uptime, CPU load, and known service thresholds, so it helps with known-unknowns that the team anticipated. The partial checkout failure is an unknown-unknown because the affected population and cause are not captured by a single existing check. Observability adds the ability to segment metrics by safe dimensions, inspect traces for representative failing requests, and query logs by trace ID or region. The practical answer is not to discard monitoring, but to use it as the entry point into exploratory evidence.

</details>

<details><summary>A checkout latency metric jumps from normal to several seconds, and traces show the payment span consuming most of the request. How should you diagnose the service incident with metrics, logs, traces, and trace IDs?</summary>

Start with the metric to confirm the symptom, measure severity, and determine whether the problem is widespread or limited to a route, region, or version. Then inspect slow traces to locate the service span that contributes most of the latency, which prevents the team from guessing across the whole call graph. Use the trace ID from a representative slow request to query structured logs in the payment service for timeouts, pool exhaustion, dependency rejections, or validation errors. The diagnosis is strongest when all three signals point to the same failure mode within the same time window.

</details>

<details><summary>A developer wants to add `user_id` to `http_requests_total` so support can investigate individual customers. How would you evaluate the cardinality and security tradeoffs?</summary>

Adding `user_id` as a metric label creates an unbounded or very high-cardinality dimension, which can multiply the number of time series and make the metrics backend expensive or unstable. Individual customer investigation is a valid need, but it fits better in structured logs or traces where targeted search, retention controls, and access restrictions can be applied. The team should also review whether the identifier is sensitive and whether it must be hashed, redacted, or protected by stricter permissions. A safe design preserves debugging value without turning every user into a permanent metric series.

</details>

<details><summary>Your Kubernetes service has RED metrics, but alerts still wake the team for CPU spikes that do not affect users. How would you design a better alerting practice?</summary>

Keep CPU as a diagnostic metric, but stop using it as the primary paging condition unless it directly predicts user harm for that service. A better alert starts from symptoms such as high error rate, high request duration, failed availability checks, or rapid error budget burn over a meaningful duration. The alert should link to dashboards and runbook steps that include CPU, saturation, Pod restarts, and recent rollouts for diagnosis. This design reduces alert fatigue because humans are interrupted for problems that require action rather than for every internal fluctuation.

</details>

<details><summary>A trace shows an API gateway span and an order service span, but the expected payment service span is missing even though payment logs exist. What is the likely issue, and how should the team fix it?</summary>

The most likely issue is broken trace context propagation between the order service and the payment service, or missing instrumentation inside the payment service. The payment logs prove that work happened, but the tracing system cannot attach it to the original request without the trace context. The team should verify propagation headers, instrumentation middleware, message metadata, and any proxy behavior between the services. Adding the trace ID to structured logs also helps confirm the fix because logs and traces should refer to the same request.

</details>

<details><summary>After a deployment, errors rise while request rate falls for one service. How would you use observability maturity practices to avoid blaming the wrong component?</summary>

First segment the metrics by deployment version, route, and status code to see whether the symptom follows the rollout or a specific path. Then inspect traces for failing requests to identify whether the service itself fails or whether an upstream dependency sends fewer valid requests. Query logs by trace ID and compare them with Kubernetes rollout events, Pod restarts, and readiness changes. Mature observability connects symptoms to ownership, deployment context, and runbooks, so the team can decide whether to roll back, scale, or fix a dependency.

</details>

<details><summary>A security review finds payment card numbers in centralized logs, but developers rely on logs for debugging production incidents. What should change?</summary>

The team should treat observability data as production data with security requirements, not as harmless debug output. Replace raw payload logging with structured, allowlisted fields that preserve operational context without storing sensitive values. Add redaction for risky keys, restrict access to log backends, and apply retention based on data sensitivity. Debugging remains possible when logs include service names, trace IDs, safe customer references, action names, and sanitized error codes.

</details>

## Hands-On Exercise: Observability Triage

In this exercise, you are the on-call engineer for a cloud-native e-commerce platform running on Kubernetes 1.35 or newer. Users report that the shopping cart occasionally fails to load, and your task is to move from symptom to likely root cause without guessing. If you have a real cluster, define `alias k=kubectl` in your shell before you begin; if you are reading offline, treat each task as a runbook design exercise and write the evidence you would expect to collect.

### Setup

Use a namespace, service name, and observability backend from your own lab environment if available. The examples assume an application namespace named `shop`, a frontend service, a cart service, and an inventory dependency, but the workflow works with any comparable multi-service application. Do not paste real tokens, customer data, or production payloads into a training document or shared chat while completing the exercise.

### Tasks

- [ ] **Compare monitoring and observability signals** by writing down which existing dashboard or alert proves the cart symptom and which evidence would let you explore unknown-unknowns.
- [ ] **Diagnose the service incident with metrics, logs, traces, and trace IDs** by selecting one slow cart request, identifying the longest span, and finding the matching structured log records.
- [ ] **Design Kubernetes alerting and instrumentation improvements** by checking whether the cart service has RED metrics, bounded labels, trace propagation, and logs that include the trace ID.
- [ ] **Evaluate observability maturity and tradeoffs** by listing one cardinality risk, one sensitive logging risk, and one retention decision for the cart workflow.
- [ ] **Implement a concise triage note** that states the symptom, affected scope, suspected service, supporting metric, supporting trace, supporting log line, and next mitigation.

### Solution Guidance

<details><summary>One possible triage path</summary>

Begin by confirming the symptom with a service-level metric such as cart request duration, cart error rate, or frontend requests that return an error while loading the cart. Segment by namespace, route, version, and region if those labels are bounded and already available. Pick a representative slow trace and identify whether the frontend, cart service, inventory service, or database span dominates the request. Query logs for the same trace ID and time window, then compare the result with Kubernetes events such as recent rollouts, Pod restarts, readiness failures, or node pressure.

</details>

<details><summary>One possible root-cause statement</summary>

A strong incident note might say: "Cart load failures began after the latest inventory rollout, affected only requests that required inventory enrichment, and correlated with a rise in cart duration p99 plus inventory dependency timeouts. Traces show the inventory span consuming most of the request time, and structured logs for the same trace IDs report connection pool exhaustion. The next mitigation is to roll back the inventory deployment or reduce concurrency while the pool configuration is corrected." The exact root cause in your lab may differ, but the evidence chain should be equally specific.

</details>

### Success Criteria

- [ ] The symptom is confirmed with a user-facing metric rather than an internal cause alone.
- [ ] At least one trace ID connects the metric symptom to a specific slow or failing service span.
- [ ] Structured logs for the same trace ID explain the local failure mode or narrow the next question.
- [ ] The alerting recommendation pages on symptoms and keeps cause metrics for diagnosis.
- [ ] The final triage note includes a cardinality or sensitive-data tradeoff that should be improved after the incident.

## Sources

- [Kubernetes: Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes: Resource Metrics Pipeline](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)
- [Kubernetes: Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)
- [OpenTelemetry: Observability Primer](https://opentelemetry.io/docs/concepts/observability-primer/)
- [OpenTelemetry: Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
- [OpenTelemetry: Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Prometheus: Metric Types](https://prometheus.io/docs/concepts/metric_types/)
- [Prometheus: Instrumentation Best Practices](https://prometheus.io/docs/practices/instrumentation/)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Google SRE Book: Practical Alerting](https://sre.google/sre-book/practical-alerting/)
- [CNCF TAG Observability Whitepaper](https://github.com/cncf/tag-observability/blob/main/whitepaper.md)
- [Fluent Bit: Kubernetes Logging](https://docs.fluentbit.io/manual/pipeline/filters/kubernetes)

## Next Module

[Module 3.5: Observability Tools](../module-3.5-observability-tools/) - Prometheus, Grafana, Jaeger, OpenTelemetry, and the practical tool choices behind the observability signals you learned here.

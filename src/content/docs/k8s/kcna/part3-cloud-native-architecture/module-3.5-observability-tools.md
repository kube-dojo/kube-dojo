---
title: "Module 3.5: Observability Tools"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.5-observability-tools
sidebar:
  order: 6
---
> **Complexity**: `[QUICK]` - Tool overview
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Module 3.4 (Observability Fundamentals)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Identify** the purpose and role of Prometheus, Grafana, Jaeger, Fluentd, and OpenTelemetry
2. **Compare** push-based vs. pull-based metrics collection approaches
3. **Explain** how OpenTelemetry unifies logging, metrics, and tracing instrumentation
4. **Evaluate** which observability tools fit different cluster monitoring requirements

---

## Why This Module Matters

Knowing the concepts is one thing; knowing the tools is another. KCNA tests your familiarity with popular observability tools in the cloud native ecosystem. This module covers the key tools you need to know.

---

## Observability Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│              TYPICAL OBSERVABILITY STACK                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              VISUALIZATION                           │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │                 GRAFANA                         │ │   │
│  │  │  Dashboards for metrics, logs, traces          │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│         ┌───────────────┼───────────────┐                  │
│         ▼               ▼               ▼                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  METRICS    │ │   LOGS      │ │   TRACES    │          │
│  │             │ │             │ │             │          │
│  │ Prometheus  │ │ Loki        │ │ Jaeger      │          │
│  │ or          │ │ or          │ │ or          │          │
│  │ Mimir       │ │ Elasticsearch│ │ Tempo      │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│         ▲               ▲               ▲                  │
│         │               │               │                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              COLLECTION                              │   │
│  │                                                      │   │
│  │  Metrics: Prometheus scrapes / OpenTelemetry       │   │
│  │  Logs: Fluentd / Fluent Bit / OpenTelemetry       │   │
│  │  Traces: OpenTelemetry / Jaeger agent             │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ▲                                   │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              APPLICATIONS                            │   │
│  │  [Pod] [Pod] [Pod] [Pod] [Pod] [Pod]              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Prometheus

```
┌─────────────────────────────────────────────────────────────┐
│              PROMETHEUS                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CNCF Graduated project for metrics                       │
│                                                             │
│  Key characteristics:                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Pull-based model (scrapes targets)                     │
│  • Time-series database                                    │
│  • PromQL query language                                  │
│  • AlertManager for alerting                              │
│                                                             │
│  How it works:                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  ┌──────────┐                                       │   │
│  │  │Prometheus│ ──── scrape ────→ /metrics endpoint  │   │
│  │  │  Server  │                                       │   │
│  │  │          │ ←─── metrics ────  Target (Pod)      │   │
│  │  └──────────┘                                       │   │
│  │       │                                              │   │
│  │       ├──→ Store time series data                   │   │
│  │       ├──→ Evaluate alert rules                     │   │
│  │       └──→ Respond to PromQL queries               │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  PromQL example:                                          │
│  ─────────────────────────────────────────────────────────  │
│  rate(http_requests_total[5m])                           │
│  "Requests per second over last 5 minutes"               │
│                                                             │
│  histogram_quantile(0.99, rate(request_duration_bucket   │
│    [5m]))                                                 │
│  "99th percentile latency"                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Prometheus Components

| Component | Purpose |
|-----------|---------|
| **Prometheus Server** | Scrapes and stores metrics |
| **AlertManager** | Handles alerts, routing, silencing |
| **Pushgateway** | For short-lived jobs (push metrics) |
| **Exporters** | Expose metrics from systems |
| **Client libraries** | Instrument your code |

---

## Grafana

```
┌─────────────────────────────────────────────────────────────┐
│              GRAFANA                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Visualization and dashboarding (not CNCF, but essential) │
│                                                             │
│  What Grafana does:                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Create dashboards                                       │
│  • Query multiple data sources                            │
│  • Alerting (also has its own alerting)                   │
│  • Explore mode for ad-hoc queries                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Dashboard: Application Overview                    │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │  Request Rate          Error Rate              │ │   │
│  │  │  ┌────────────┐        ┌────────────┐         │ │   │
│  │  │  │ ▂▃▅▇█▇▅▃▂ │        │ ▂▁▁▃▁▁▁▁▂ │         │ │   │
│  │  │  │  1.2k/s   │        │   0.5%    │         │ │   │
│  │  │  └────────────┘        └────────────┘         │ │   │
│  │  ├────────────────────────────────────────────────┤ │   │
│  │  │  Latency p99: 245ms   Active Pods: 5          │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Data sources supported:                                  │
│  • Prometheus                                              │
│  • Loki (logs)                                            │
│  • Jaeger/Tempo (traces)                                  │
│  • Elasticsearch                                          │
│  • And many more...                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Logging Tools

```
┌─────────────────────────────────────────────────────────────┐
│              LOGGING TOOLS                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FLUENTD (CNCF Graduated)                                 │
│  ─────────────────────────────────────────────────────────  │
│  • Unified logging layer                                  │
│  • Collects from many sources                             │
│  • Routes to many destinations                            │
│  • Plugin ecosystem                                        │
│                                                             │
│  FLUENT BIT (CNCF Graduated, part of Fluentd)            │
│  ─────────────────────────────────────────────────────────  │
│  • Lightweight version of Fluentd                        │
│  • Lower resource usage                                   │
│  • Better for edge/resource-constrained                  │
│                                                             │
│  Typical flow:                                            │
│  ─────────────────────────────────────────────────────────  │
│  Container stdout → Fluent Bit → Elasticsearch/Loki     │
│                                                             │
│  LOKI (Grafana Labs)                                      │
│  ─────────────────────────────────────────────────────────  │
│  • Log aggregation system                                 │
│  • Designed to be cost-effective                         │
│  • Only indexes metadata (labels)                        │
│  • Pairs with Grafana                                     │
│                                                             │
│  ELK/EFK Stack:                                           │
│  ─────────────────────────────────────────────────────────  │
│  • Elasticsearch (storage)                               │
│  • Logstash/Fluentd (collection)                        │
│  • Kibana (visualization)                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tracing Tools

```
┌─────────────────────────────────────────────────────────────┐
│              TRACING TOOLS                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  JAEGER (CNCF Graduated)                                  │
│  ─────────────────────────────────────────────────────────  │
│  • End-to-end distributed tracing                         │
│  • Originally from Uber                                   │
│  • OpenTracing compatible                                 │
│  • Service dependency analysis                            │
│                                                             │
│  Components:                                               │
│  • Jaeger Client (in your app)                           │
│  • Jaeger Agent (per node)                               │
│  • Jaeger Collector                                       │
│  • Jaeger Query/UI                                        │
│                                                             │
│  TEMPO (Grafana Labs)                                     │
│  ─────────────────────────────────────────────────────────  │
│  • Cost-effective trace storage                          │
│  • Only stores trace IDs and spans                       │
│  • Integrates with Grafana                               │
│                                                             │
│  ZIPKIN                                                   │
│  ─────────────────────────────────────────────────────────  │
│  • One of the first distributed tracers                  │
│  • Originally from Twitter                               │
│  • Simple to set up                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## OpenTelemetry

```
┌─────────────────────────────────────────────────────────────┐
│              OPENTELEMETRY                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CNCF Incubating project - THE unified standard          │
│                                                             │
│  What it provides:                                         │
│  ─────────────────────────────────────────────────────────  │
│  • APIs for instrumenting code                            │
│  • SDKs for multiple languages                            │
│  • Collector for receiving/processing telemetry          │
│  • Unified protocol (OTLP)                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  [App with OTel SDK] ──→ [OTel Collector] ──→      │   │
│  │                              │                      │   │
│  │                    ┌─────────┼─────────┐            │   │
│  │                    ▼         ▼         ▼            │   │
│  │              Prometheus   Jaeger    Loki            │   │
│  │              (metrics)   (traces)  (logs)          │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Why OpenTelemetry matters:                               │
│  ─────────────────────────────────────────────────────────  │
│  • Vendor neutral (switch backends easily)               │
│  • Single instrumentation for metrics+traces+logs        │
│  • Replaces OpenTracing and OpenCensus                  │
│  • Becoming the industry standard                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubernetes-Specific Observability

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES OBSERVABILITY                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Built-in Kubernetes metrics:                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  METRICS SERVER                                           │
│  • Resource metrics (CPU, memory)                        │
│  • Used by kubectl top                                   │
│  • Used by HPA for autoscaling                          │
│                                                             │
│  KUBE-STATE-METRICS                                       │
│  • Kubernetes object state                               │
│  • Deployment replicas, Pod status, etc.                │
│  • Complements metrics server                            │
│                                                             │
│  Example queries:                                         │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  # Pod resource usage                                     │
│  container_memory_usage_bytes{pod="my-app-xyz"}         │
│                                                             │
│  # Deployment availability                                │
│  kube_deployment_status_replicas_available               │
│  {deployment="frontend"}                                  │
│                                                             │
│  # Node conditions                                        │
│  kube_node_status_condition{condition="Ready"}           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tool Comparison

| Category | Tool | Maturity | Notes |
|----------|------|----------|-------|
| **Metrics** | Prometheus | CNCF Graduated | De facto standard |
| **Metrics** | Mimir | Grafana Labs | Scalable Prometheus |
| **Logs** | Fluentd | CNCF Graduated | Feature-rich |
| **Logs** | Fluent Bit | CNCF Graduated | Lightweight |
| **Logs** | Loki | Grafana Labs | Cost-effective |
| **Traces** | Jaeger | CNCF Graduated | Full-featured |
| **Traces** | Tempo | Grafana Labs | Cost-effective |
| **Unified** | OpenTelemetry | CNCF Incubating | Standard API |
| **Viz** | Grafana | Independent | Multi-source |

---

## Did You Know?

- **Prometheus is pull-based** - Unlike most monitoring systems that receive pushed metrics, Prometheus actively scrapes targets. This makes it easier to detect if targets are down.

- **OpenTelemetry merged projects** - It combined OpenTracing (tracing API) and OpenCensus (Google's observability library) into one standard.

- **Loki doesn't index log content** - Unlike Elasticsearch, Loki only indexes labels, making it cheaper but slower for full-text search.

- **Service meshes provide observability** - Istio and Linkerd automatically collect metrics, traces, and logs without code changes.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Pushing metrics to Prometheus | Not how it works | Prometheus pulls (except Pushgateway) |
| Separate dashboards per pillar | Context switching | Use Grafana for unified view |
| No resource limits on collectors | Collectors crash nodes | Set proper resource limits |
| Using Elasticsearch for all logs | Expensive | Consider Loki for cost savings |

---

## Quiz

1. **How does Prometheus collect metrics?**
   <details>
   <summary>Answer</summary>
   Pull-based model: Prometheus scrapes HTTP endpoints (usually /metrics) at configured intervals. Targets expose metrics in Prometheus format. This is different from push-based systems.
   </details>

2. **What is the relationship between Fluentd and Fluent Bit?**
   <details>
   <summary>Answer</summary>
   Both are CNCF graduated log collectors. Fluent Bit is a lightweight version of Fluentd, using fewer resources. Fluent Bit is often used as an agent on nodes, sometimes forwarding to Fluentd for more complex processing.
   </details>

3. **What is OpenTelemetry?**
   <details>
   <summary>Answer</summary>
   A CNCF incubating project providing vendor-neutral APIs, SDKs, and tools for generating and collecting telemetry data (metrics, traces, logs). It unifies observability instrumentation across languages and tools.
   </details>

4. **What does Grafana do?**
   <details>
   <summary>Answer</summary>
   Visualization and dashboarding. It queries multiple data sources (Prometheus for metrics, Loki for logs, Jaeger for traces) and displays them in customizable dashboards. It's the common UI for the observability stack.
   </details>

5. **What is Jaeger used for?**
   <details>
   <summary>Answer</summary>
   Distributed tracing. It tracks requests as they flow through microservices, showing the path, timing, and relationships between services. It's a CNCF graduated project originally from Uber.
   </details>

---

## Summary

**Metrics tools**:
- **Prometheus**: CNCF graduated, pull-based, PromQL
- **Grafana**: Dashboards, multi-source visualization

**Logging tools**:
- **Fluentd/Fluent Bit**: CNCF graduated collectors
- **Loki**: Cost-effective log storage
- **ELK**: Elasticsearch, Logstash, Kibana

**Tracing tools**:
- **Jaeger**: CNCF graduated, full-featured
- **Tempo**: Cost-effective trace storage

**Unified**:
- **OpenTelemetry**: Standard APIs for all telemetry

**Kubernetes-specific**:
- **Metrics Server**: Resource metrics (kubectl top)
- **kube-state-metrics**: Object state metrics

---

## Part 3 Complete!

You've finished **Cloud Native Architecture** (12% of the exam, including Observability). You now understand:
- Cloud native principles and the CNCF ecosystem
- Architectural patterns: service mesh, serverless, GitOps
- The three pillars of observability: metrics, logs, traces
- Key tools: Prometheus, Grafana, Fluentd, Jaeger, OpenTelemetry

**Next Part**: [Part 4: Application Delivery](../part4-application-delivery/module-4.1-ci-cd/) - Continuous Integration, Continuous Delivery, and deployment strategies (16% of the exam).

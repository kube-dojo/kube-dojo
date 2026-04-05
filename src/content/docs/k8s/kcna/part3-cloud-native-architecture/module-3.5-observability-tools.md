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

Think of a Kubernetes cluster like a massive hospital:
- **Prometheus (Metrics)** is the heart rate monitor attached to every patient. It regularly checks their pulse, telling you *something* is wrong (e.g., heart rate is 180!).
- **Fluentd/Loki (Logs)** are the detailed medical charts. When the monitor alarms, the doctor reads the charts to see *what* exactly happened leading up to it.
- **Jaeger (Traces)** is the MRI scan. It traces a specific issue across the entire system to pinpoint exactly *where* the blockage or slowdown occurred.
- **Grafana** is the central nurse's station screen, bringing all the monitors, charts, and scans into a single pane of glass.

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

> **Pause and predict**: Most monitoring systems use a push model where applications send metrics to a central server. Prometheus uses a pull model where it actively scrapes metrics from applications. What advantage might pulling have over pushing for detecting when a service goes down?

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

> **War Story: The Billion Time-Series Bug**
> A team once decided to track HTTP requests by adding the user's unique ID as a label in their Prometheus metrics (e.g., `http_requests_total{user_id="12345"}`). When their app went viral, they suddenly generated millions of unique labels. Prometheus creates a new time-series for every unique combination of labels. This "cardinality explosion" consumed all the node's memory and crashed Prometheus in minutes. *Lesson:* Never use highly unique values (like user IDs or session IDs) as metric labels! Keep labels restricted to bounded sets like HTTP status codes.

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

> **Worked Example: The 3 AM Page**
> At 3:00 AM, PagerDuty wakes you up. The alert says: `HighErrorRate on PaymentService`.
> 1. **Grafana**: You open the main dashboard and see a huge spike in 500 errors.
> 2. **Prometheus**: You check the Prometheus metrics panel inside Grafana to see *which* pod is throwing errors. It's `payment-pod-abc`.
> 3. **Loki/Fluentd**: Still in Grafana, you switch over to the logs view for `payment-pod-abc`. The logs clearly show `Connection timeout to Database`.
> 4. **Jaeger**: To be absolutely sure, you click a Trace ID found in the logs. Jaeger opens, showing the exact journey: User -> API Gateway -> PaymentService -> (30-second red bar) -> Database.
> You've found the issue in 2 minutes without ever leaving your browser or SSHing into a single server.

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

> **Stop and think**: OpenTelemetry provides a single API for metrics, traces, and logs. Before OpenTelemetry, teams had to use separate instrumentation libraries for each pillar. Why is having one unified standard important, especially for organizations with services written in different programming languages?

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

> **Decision Exercise: Startups vs. Enterprises**
> *Scenario*: You are an architect for a small, budget-conscious startup. You need logging for a 5-node cluster. Do you choose the ELK stack (Elasticsearch, Logstash, Kibana) or the PLG stack (Prometheus, Loki, Grafana)?
> *Decision*: Go with PLG. Elasticsearch is powerful but resource-hungry (often requiring dedicated nodes and high RAM footprint). Loki only indexes metadata labels (like `app="frontend"`), dropping the actual heavy log text into cheap object storage. It uses a fraction of the memory, perfect for a startup, even if full-text search ends up being slightly slower.

---

## Hands-On Exercise: Exploring the Stack

In this exercise, you'll spin up a local Kubernetes cluster and deploy the Prometheus/Grafana stack to see it in action.

**Prerequisites:** `minikube` or `kind` installed, `helm` installed.

- [ ] **Step 1: Start a local cluster and add the Prometheus Helm repo**
  ```bash
  minikube start
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update
  ```
- [ ] **Step 2: Install the Kube-Prometheus Stack**
  ```bash
  helm install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
  ```
  *Note: This incredibly popular chart installs Prometheus, Grafana, Alertmanager, and kube-state-metrics all at once.*
- [ ] **Step 3: Wait for Pods to be ready**
  ```bash
  kubectl get pods -n monitoring -w
  ```
- [ ] **Step 4: Port-forward to Grafana**
  ```bash
  kubectl port-forward svc/monitoring-grafana 8080:80 -n monitoring
  ```
- [ ] **Step 5: Access the Dashboard**
  Open your browser to `http://localhost:8080`.
  Username: `admin`, Password: `prom-operator` (default).
  Navigate to **Dashboards > Kubernetes / Compute Resources / Cluster** to see rich metrics pulled directly from your local minikube cluster!
- [ ] **Step 6: Clean up**
  ```bash
  minikube delete
  ```

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

1. **Your team runs a short-lived batch Job that completes in 30 seconds. Prometheus scrapes metrics every 15 seconds. By the time Prometheus scrapes, the Job's Pod is already terminated. How would you get metrics from this Job into Prometheus?**
   <details>
   <summary>Answer</summary>
   Use the Prometheus Pushgateway. Since Prometheus uses a pull model (scraping endpoints), it cannot collect metrics from Pods that have already terminated. The Pushgateway is specifically designed for short-lived jobs: the Job pushes its metrics to the Pushgateway before exiting, and Prometheus scrapes the Pushgateway at its normal interval. The metrics persist on the Pushgateway until they are scraped. This is the exception to Prometheus's pull model and is one of the few valid use cases for push-based metrics in the Prometheus ecosystem.
   </details>

2. **Your cluster runs 500 Pods across 20 nodes. You need to collect logs from every Pod and send them to a centralized logging system. Would you deploy Fluent Bit as a Deployment with 3 replicas or as a DaemonSet? Why?**
   <details>
   <summary>Answer</summary>
   Deploy Fluent Bit as a DaemonSet so one instance runs on every node. Container logs are stored on the node's filesystem (in `/var/log/containers/`), so the log collector must run on the same node to access them. A Deployment with 3 replicas would only collect logs from the 3 nodes those replicas happen to run on, missing logs from the other 17 nodes. DaemonSets also automatically add a Fluent Bit Pod when new nodes join the cluster. Fluent Bit is preferred over Fluentd as a per-node agent because it is more lightweight (lower CPU and memory footprint).
   </details>

3. **Your company uses Prometheus for metrics, Elasticsearch for logs, and Jaeger for traces. A new CTO wants to standardize instrumentation across 15 services written in Go, Python, and Java. Currently, each service uses different client libraries. What CNCF project would unify this, and what benefits would it provide?**
   <details>
   <summary>Answer</summary>
   OpenTelemetry (CNCF Incubating) provides a single, vendor-neutral instrumentation API with SDKs for Go, Python, Java, and many other languages. Instead of each service using a different Prometheus client, Jaeger client, and logging library, teams instrument once with OpenTelemetry and the OTel Collector routes telemetry to the appropriate backends. If you later switch from Jaeger to Tempo for traces, you change the Collector configuration -- not the application code. OpenTelemetry replaced both OpenTracing and OpenCensus, becoming the industry standard for telemetry instrumentation.
   </details>

4. **An engineer sets up Grafana dashboards showing Prometheus metrics, Loki logs, and Jaeger traces. A manager asks why they need Grafana when Prometheus already has a built-in UI. What does Grafana provide that individual tool UIs do not?**
   <details>
   <summary>Answer</summary>
   Grafana provides a unified visualization layer across all three observability pillars. While Prometheus has a basic UI for running PromQL queries, it cannot display logs or traces. Each tool's native UI only shows its own data. Grafana connects to multiple data sources simultaneously, enabling dashboards that correlate metrics, logs, and traces in one view. You can click from a metric spike to the related logs and traces without switching tools. This cross-pillar correlation is what makes debugging efficient -- a single pane of glass for the entire observability stack.
   </details>

5. **Your HPA needs CPU metrics to make scaling decisions, and your dashboards need detailed application metrics like request latency and error rates. What is the difference between Metrics Server and Prometheus in this context, and do you need both?**
   <details>
   <summary>Answer</summary>
   Yes, you typically need both. Metrics Server provides lightweight, real-time resource metrics (CPU and memory usage per Pod) that the HPA and `kubectl top` command consume. It only stores the most recent data point, not historical time series. Prometheus provides rich, customizable application metrics (request rates, latency percentiles, error counts) stored as time series over time. Prometheus can also feed custom metrics to HPA via the custom metrics API adapter. Metrics Server handles the "how much CPU is this Pod using right now?" question. Prometheus handles "what is the p99 latency trend over the last 24 hours?" question.
   </details>

6. **Your company recently suffered an outage because a database's disk filled up. Prometheus was running and actively collecting metrics, but nobody was looking at the dashboard. What Prometheus component was missing from your observability strategy?**
   <details>
   <summary>Answer</summary>
   AlertManager. While the Prometheus Server scrapes and stores metrics, and Grafana visualizes them, you cannot rely on humans staring at dashboards 24/7. AlertManager is the component responsible for evaluating alerting rules (e.g., `disk_usage > 90%`) and routing those alerts to notification channels like PagerDuty, Slack, or email. Without AlertManager, your metrics are passive; with it, they become proactive.
   </details>

7. **You are migrating a monolithic application to microservices. Developers complain that when a user request fails, they have to manually search through the logs of 5 different services to figure out where the failure occurred. What specific observability tool or concept solves this problem?**
   <details>
   <summary>Answer</summary>
   Distributed Tracing (e.g., Jaeger or Tempo). In a microservices architecture, a single user action might traverse dozens of services. Distributed tracing solves this by injecting a unique "Trace ID" at the entry point (like the API Gateway) and passing it along in the HTTP headers to every subsequent service. Tools like Jaeger then reconstruct the entire request path as a visual waterfall graph, immediately showing which specific microservice caused the error or latency bottleneck.
   </details>

8. **You want to collect metrics from a proprietary, legacy database that doesn't have a native `/metrics` endpoint for Prometheus to scrape. How can you get this database's metrics into Prometheus without modifying the database code?**
   <details>
   <summary>Answer</summary>
   Use an Exporter. An exporter is a small proxy service that sits next to the application you want to monitor. It connects to the legacy system using its native protocols (like running SQL queries against the database), translates that data into the Prometheus time-series format, and exposes a `/metrics` HTTP endpoint. Prometheus then scrapes the exporter instead of the database directly. There are hundreds of community-built exporters for systems like MySQL, Redis, and various hardware appliances.
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
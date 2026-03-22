# PCA - Prometheus Certified Associate

> **Multiple-choice exam** | 90 minutes | Passing score: 75% | $250 USD | **CNCF Certification**

## Overview

The PCA (Prometheus Certified Associate) validates your understanding of Prometheus, PromQL, instrumentation, and the broader Prometheus monitoring ecosystem. This is a **knowledge-based exam** — multiple-choice questions, not hands-on tasks. But don't underestimate it: Domain 3 (PromQL) is 28% of the exam and requires you to read, write, and debug queries fluently.

**KubeDojo covers ~95% of PCA topics** through existing observability modules plus two dedicated PCA modules covering PromQL depth and instrumentation/alerting specifics.

> **Prometheus is the de facto standard for metrics in cloud-native.** Born at SoundCloud in 2012, second CNCF project to graduate (after Kubernetes), and the foundation every other monitoring tool builds on. PCA validates the single most important observability skill: understanding Prometheus deeply.

---

## PCA-Specific Modules

These modules cover the areas between KubeDojo's existing observability modules and the PCA exam requirements:

| # | Module | Topic | Domains Covered |
|---|--------|-------|-----------------|
| 1 | [PromQL Deep Dive](module-1-promql-deep-dive.md) | Selectors, rates, aggregation, histograms, binary ops, subqueries, recording rules | Domain 3 (28%) |
| 2 | [Instrumentation & Alerting](module-2-instrumentation-alerting.md) | Client libraries, metric types, naming conventions, exporters, Alertmanager config | Domain 4 (16%) + Domain 5 (18%) |

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| Observability Concepts | 18% | Excellent (4 foundation modules) |
| Prometheus Fundamentals | 20% | Excellent (module-1.1-prometheus.md) |
| PromQL | 28% | Excellent ([PromQL Deep Dive](module-1-promql-deep-dive.md) + fundamentals module) |
| Instrumentation & Exporters | 16% | Excellent ([Instrumentation & Alerting](module-2-instrumentation-alerting.md)) |
| Alerting & Dashboarding | 18% | Excellent ([Instrumentation & Alerting](module-2-instrumentation-alerting.md) + Grafana module) |

---

## Domain 1: Observability Concepts (18%)

### Competencies
- Understanding metrics, logs, traces, and their relationships
- Distinguishing monitoring from observability
- Understanding the role of metrics in the observability ecosystem
- Knowing push vs. pull models and their trade-offs

### KubeDojo Learning Path

**Theory (start here):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability.md) | What is Observability? Observability vs. monitoring | Direct |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars.md) | Metrics, Logs, Traces — the three pillars | Direct |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles.md) | Instrumentation principles: what to measure, how | Direct |
| [Observability 3.4](../../platform/foundations/observability-theory/module-3.4-from-data-to-insight.md) | From data to insight — making metrics actionable | Direct |

**Tools (context):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Pull model, architecture, TSDB, service discovery | Direct |
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | OTel as instrumentation standard, relationship to Prometheus | Partial |

---

## Domain 2: Prometheus Fundamentals (20%)

### Competencies
- Understanding Prometheus architecture (server, TSDB, Alertmanager, Pushgateway)
- Configuring scrape targets and service discovery
- Understanding the pull model, scrape intervals, and staleness
- Working with labels, relabeling, and metric metadata
- Deploying Prometheus on Kubernetes (Operator, ServiceMonitor, PodMonitor)

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Architecture, pull model, TSDB, service discovery, K8s deployment | Direct |
| [SRE 1.2](../../platform/disciplines/sre/module-1.2-slos.md) | SLOs and how Prometheus implements them | Direct |
| [SRE 1.3](../../platform/disciplines/sre/module-1.3-error-budgets.md) | Error budgets, burn rate alerts — Prometheus in practice | Direct |

### Key Exam Topics — Coverage Notes
- **Prometheus architecture** — Fully covered in module-1.1-prometheus.md (pull model, TSDB, Alertmanager, Pushgateway)
- **Service discovery** — Kubernetes SD, ServiceMonitor, PodMonitor, relabel_configs covered in module-1.1
- **Scrape configuration** — scrape_interval, scrape_timeout, honor_labels, metric_relabel_configs covered in module-1.1
- **Storage** — TSDB internals (blocks, WAL, compaction, retention) covered in module-1.1

---

## Domain 3: PromQL (28%)

> **This is the largest domain.** More than a quarter of your score depends on PromQL fluency. You need to write queries from scratch, debug broken ones, and understand the evaluation model.

### Competencies
- Writing instant and range vector selectors with label matchers
- Using rate(), irate(), increase() correctly on counters
- Applying aggregation operators (sum, avg, count, topk) with by/without
- Computing percentiles with histogram_quantile()
- Using binary operators and vector matching (on, ignoring, group_left)
- Writing recording rules for performance
- Understanding subqueries and the evaluation model

### KubeDojo Learning Path

**Existing coverage:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | PromQL basics: selectors, rate, aggregation, histograms | Partial |
| [SLO Tooling](../../platform/toolkits/observability/module-1.10-slo-tooling.md) | SLO-focused PromQL (burn rates, error budgets) | Partial |
| [PromQL Deep Dive](module-1-promql-deep-dive.md) | Complete PromQL coverage: all selector types, rate functions, aggregation, binary operators, histogram_quantile, recording rules, subqueries | Direct |

### Key Exam Topics — Now Covered

All of the following are covered in the [PromQL Deep Dive](module-1-promql-deep-dive.md):

- **Selector types**: Instant vectors, range vectors, label matchers (`=`, `!=`, `=~`, `!~`)
- **Rate functions**: `rate()` vs `irate()` vs `increase()` — when to use each, counter reset handling
- **Aggregation operators**: `sum`, `avg`, `min`, `max`, `count`, `topk`, `bottomk`, `quantile` with `by`/`without`
- **Binary operators**: Arithmetic (`+`, `-`, `*`, `/`), comparison (`>`, `<`, `==`), logical (`and`, `or`, `unless`)
- **Vector matching**: `on()`, `ignoring()`, `group_left()`, `group_right()` for joining metrics
- **Histogram queries**: `histogram_quantile()`, bucket selection, interpolation behavior
- **Recording rules**: Naming conventions (`level:metric:operations`), when and why to use them
- **Subqueries**: `metric[range:resolution]` syntax, use cases for alerting over aggregated data
- **Offset modifier**: Comparing current values to historical data

---

## Domain 4: Instrumentation & Exporters (16%)

### Competencies
- Understanding the four metric types (Counter, Gauge, Histogram, Summary)
- Instrumenting applications with client libraries (Go, Python, Java)
- Following metric naming conventions
- Using exporters (node_exporter, blackbox_exporter, custom exporters)
- Understanding the /metrics endpoint format (OpenMetrics, Prometheus exposition format)

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles.md) | What to instrument, instrumentation principles | Direct |
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Metric types overview, exporters basics | Partial |
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | OTel SDK instrumentation (complementary approach) | Partial |
| [Instrumentation & Alerting](module-2-instrumentation-alerting.md) | Client libraries (Go/Python/Java), naming conventions, metric type selection, exporters deep dive | Direct |

### Key Exam Topics — Now Covered

All of the following are covered in the [Instrumentation & Alerting](module-2-instrumentation-alerting.md):

- **Four metric types**: Counter (monotonic), Gauge (up/down), Histogram (distribution with buckets), Summary (client-side quantiles)
- **When to use which type**: Decision framework for choosing the right metric type
- **Client libraries**: Go (`prometheus/client_golang`), Python (`prometheus_client`), Java (`simpleclient`) with code examples
- **Naming conventions**: `<namespace>_<name>_<unit>_total`, unit suffixes, label best practices
- **Exporters**: node_exporter (hardware/OS), blackbox_exporter (probing), custom exporters
- **Exposition format**: Prometheus text format, OpenMetrics format, TYPE/HELP/UNIT metadata

---

## Domain 5: Alerting & Dashboarding (18%)

### Competencies
- Configuring Alertmanager (routing tree, receivers, inhibition, silencing)
- Writing alerting rules with appropriate thresholds and `for` durations
- Understanding alert states (pending, firing, resolved)
- Creating effective dashboards in Grafana
- Using recording rules to optimize dashboard queries

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Alerting rules basics, Alertmanager overview | Partial |
| [Grafana](../../platform/toolkits/observability/module-1.3-grafana.md) | Dashboards, data sources, provisioning, variables | Direct |
| [SRE 1.2](../../platform/disciplines/sre/module-1.2-slos.md) | SLO-based alerting philosophy | Direct |
| [SRE 1.3](../../platform/disciplines/sre/module-1.3-error-budgets.md) | Error budget burn rate alerting | Direct |
| [Instrumentation & Alerting](module-2-instrumentation-alerting.md) | Alertmanager routing, receivers, inhibition, silencing, recording rules, alerting rule patterns | Direct |

### Key Exam Topics — Now Covered

- **Alertmanager routing tree** — Covered in [Instrumentation & Alerting](module-2-instrumentation-alerting.md): route hierarchy, `match`/`match_re`, `continue`, `group_by`
- **Receivers** — Slack, PagerDuty, email, webhook configuration
- **Inhibition rules** — Suppress dependent alerts when root-cause alert fires
- **Silences** — Temporarily mute alerts during maintenance
- **Alert states** — `inactive` -> `pending` -> `firing` -> `resolved` lifecycle
- **Recording rules** — Naming convention, when to use, performance optimization
- **Grafana dashboards** — Covered in existing [Grafana module](../../platform/toolkits/observability/module-1.3-grafana.md)

---

## Study Strategy

```
PCA PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1: Observability Foundations (Domain 1 — 18%)
├── Observability Theory 3.1-3.4 (existing KubeDojo modules)
├── Understand metrics vs logs vs traces
└── Know push vs pull model trade-offs cold

Week 2: Prometheus Fundamentals (Domain 2 — 20%)
├── Prometheus module 1.1 (existing KubeDojo module)
├── Deploy Prometheus on kind/minikube
├── Configure scrape targets, ServiceMonitor, PodMonitor
├── Understand TSDB internals (WAL, blocks, compaction)
└── Practice relabel_configs

Week 3-4: PromQL (Domain 3 — 28%!)
├── PromQL Deep Dive module (new PCA module)
├── Practice 20+ queries on a live Prometheus instance
├── Master rate() vs irate() vs increase()
├── Know aggregation operators with by/without
├── Practice histogram_quantile() with various bucket configs
├── Understand binary operators and vector matching
└── Write recording rules

Week 5: Instrumentation & Exporters (Domain 4 — 16%)
├── Instrumentation & Alerting module (new PCA module)
├── Instrument a simple Go or Python app
├── Deploy node_exporter, blackbox_exporter
├── Memorize naming conventions
└── Know all four metric types and when to use each

Week 6: Alerting & Dashboarding (Domain 5 — 18%)
├── Instrumentation & Alerting module (alerting sections)
├── Grafana module 1.3 (existing KubeDojo module)
├── Configure Alertmanager: routing, receivers, inhibition
├── Write alerting rules with proper for durations
├── Create Grafana dashboards from PromQL queries
└── Final review: focus 50% of time on Domain 3 (PromQL)
```

---

## Exam Tips

- **PromQL is almost a third of the exam** — you cannot pass without writing queries fluently. Practice on a real Prometheus instance, not just reading docs.
- **Know the four metric types cold** — Counter (only goes up), Gauge (goes up and down), Histogram (buckets), Summary (quantiles). Know when to use each.
- **rate() vs irate() is heavily tested** — `rate()` for dashboards and alerts (smoothed), `irate()` for debugging (instant). Never use `irate()` in alerting rules.
- **Alertmanager routing tree** — understand the hierarchy: global route -> child routes -> receivers. `group_by`, `group_wait`, `group_interval`, `repeat_interval`.
- **Naming conventions matter** — `<namespace>_<name>_<unit>_total` for counters, `_seconds` not `_milliseconds`, `_bytes` not `_kilobytes`.
- **Recording rules** — naming convention is `level:metric:operations` (colons, not underscores). Know when they improve performance.
- **histogram_quantile() interpolation** — understand that results are estimates interpolated between bucket boundaries. More buckets = more accuracy.
- **Don't neglect service discovery** — Kubernetes SD roles (pod, service, endpoints, node), relabel_configs for filtering and transforming labels.

---

## Gap Analysis

KubeDojo's observability modules plus the two dedicated PCA modules provide comprehensive coverage across all five domains.

| Topic | Status | Notes |
|-------|--------|-------|
| Observability theory (three pillars) | Covered | Existing foundation modules 3.1-3.4 |
| Prometheus architecture and fundamentals | Covered | Existing module-1.1-prometheus.md |
| PromQL selectors and label matchers | Covered | [PromQL Deep Dive](module-1-promql-deep-dive.md) |
| rate/irate/increase functions | Covered | [PromQL Deep Dive](module-1-promql-deep-dive.md) + module-1.1 |
| Aggregation operators | Covered | [PromQL Deep Dive](module-1-promql-deep-dive.md) |
| Binary operators and vector matching | Covered | [PromQL Deep Dive](module-1-promql-deep-dive.md) |
| histogram_quantile() | Covered | [PromQL Deep Dive](module-1-promql-deep-dive.md) + module-1.1 |
| Recording rules | Covered | [PromQL Deep Dive](module-1-promql-deep-dive.md) + module-1.1 |
| Client libraries (Go/Python/Java) | Covered | [Instrumentation & Alerting](module-2-instrumentation-alerting.md) |
| Metric naming conventions | Covered | [Instrumentation & Alerting](module-2-instrumentation-alerting.md) |
| Exporters (node, blackbox) | Covered | [Instrumentation & Alerting](module-2-instrumentation-alerting.md) |
| Alertmanager configuration | Covered | [Instrumentation & Alerting](module-2-instrumentation-alerting.md) |
| Inhibition and silencing | Covered | [Instrumentation & Alerting](module-2-instrumentation-alerting.md) |
| Grafana dashboarding | Covered | Existing module-1.3-grafana.md |
| Prometheus remote write/read | Minor gap | Review [Prometheus docs on remote storage](https://prometheus.io/docs/prometheus/latest/storage/#remote-storage-integrations) |
| Thanos/Cortex federation | Minor gap | Out of scope for PCA; covered lightly in module-1.1 |

---

## Essential Study Resources

- **Prometheus Documentation**: [prometheus.io/docs](https://prometheus.io/docs/) — the primary source of truth
- **PromQL Cheat Sheet**: [promlabs.com/promql-cheat-sheet](https://promlabs.com/promql-cheat-sheet/) — quick reference
- **PromLabs Training**: [promlabs.com](https://promlabs.com/) — Julius Volz's PromQL training (Prometheus co-founder)
- **Robust Perception Blog**: [robustperception.io/blog](https://www.robustperception.io/blog/) — Brian Brazil's deep dives
- **CNCF PCA Page**: [training.linuxfoundation.org](https://training.linuxfoundation.org/) — official exam details
- **Prometheus Operator**: [prometheus-operator.dev](https://prometheus-operator.dev/) — Kubernetes-native deployment

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Observability Track:
├── KCNA (Cloud Native Associate) — includes observability basics
├── PCA (Prometheus Certified Associate) ← YOU ARE HERE
├── OTCA (OpenTelemetry Certified Associate) — instrumentation standard
└── Future: Advanced Prometheus certification (TBD)

Complementary Certifications:
├── CKA (K8s Administrator) — deploy/manage monitoring stacks
├── CNPE (Platform Engineer) — 20% observability & operations
└── CKS (K8s Security Specialist) — audit logging, runtime monitoring

Recommended Order:
  KCNA → PCA → OTCA → CKA → CNPE
```

The PCA pairs naturally with OTCA (OpenTelemetry Certified Associate) — PCA covers the storage/querying side (Prometheus, PromQL, Alertmanager) while OTCA covers the instrumentation/collection side (OTel SDK, Collector). Together they validate full-stack observability expertise.

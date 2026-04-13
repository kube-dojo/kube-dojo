---
title: "Module 1.2: Instrumentation & Alerting"
slug: k8s/pca/module-1.2-instrumentation-alerting
sidebar:
  order: 3
---

> **PCA Track** | Complexity: `[COMPLEX]` | Time: 45-55 min

## Prerequisites

Before starting this module, ensure you have completed the foundational requirements:
- **Prometheus Architecture Fundamentals**: Understanding of the pull model and basic scraping.
- **PromQL Deep Dive**: Mastery of vector matching and time-series selections.
- **Observability Theory**: Comprehension of the basic pillars of observability.
- **Programming Proficiency**: Ability to read basic Go, Python, or Java to understand client library patterns.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** a comprehensive observability strategy using the correct Prometheus metric types (counters, gauges, histograms, summaries).
2. **Implement** application-level instrumentation using Prometheus client libraries across multiple programming languages.
3. **Evaluate** label cardinality limits and naming conventions to preserve time-series database performance.
4. **Diagnose** external availability and hardware utilization using standard exporters like node_exporter and blackbox_exporter.
5. **Configure** robust Alertmanager routing trees, inhibition rules, and recording rules to eliminate alert fatigue.

---

## Why This Module Matters

The database team at a large ride-sharing company added a custom Prometheus metric to track query latency. They were proud of it — `db_query_duration_milliseconds`. It worked perfectly in development and passed initial code reviews.

Three weeks later, the infrastructure team tried to create an SLO dashboard combining API latency (measured in seconds using `http_request_duration_seconds`) with database latency. The query looked simple:

```promql
histogram_quantile(0.99,
  sum by (le)(rate(http_request_duration_seconds_bucket[5m]))
)
+
histogram_quantile(0.99,
  sum by (le)(rate(db_query_duration_milliseconds_bucket[5m]))
)
```

The P99 total latency showed **3,000.2 seconds**. It took 45 minutes of confusion during a major incident before someone realized: one metric was in seconds, the other in milliseconds. The query was adding 0.2 seconds of API latency to 3,000 milliseconds of DB latency. The result was mathematically correct but semantically nonsensical, leading the incident commanders to chase ghost bottlenecks in the network layer rather than the overloaded database. The financial impact of the extended downtime ran into the millions.

The fix required a massive migration effort: renaming the metric across hundreds of repositories, updating dozens of Grafana dashboards, modifying critical alerting rules, and coordinating a rolling deployment across thousands of pods. This consumed two engineer-weeks of work, all because of a single naming convention violation.

Instrumentation and alerting form the foundation of cloud-native reliability. If your instrumentation is flawed, your metrics are useless. If your alerting is noisy, your engineers will ignore the pages. This module ensures you build signals that operators can trust and maintain long-term system integrity.

---

## Section 1: The Four Prometheus Metric Types

Prometheus uses a pull-based model, meaning your applications expose the current state of their metrics, and the Prometheus server fetches them at regular intervals. To make this data meaningful, Prometheus categorizes time-series data into four core metric types. Choosing the correct type is the most critical decision in the instrumentation process.

### Counter

A counter is a cumulative metric that only goes up. It acts as an odometer for your application, resetting to zero only when the process restarts. Because it resets, you must never query a counter directly; you must always use rate functions to calculate the per-second increase.

```text
COUNTER: Mon
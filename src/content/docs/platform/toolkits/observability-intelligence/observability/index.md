---
title: "Observability Toolkit"
sidebar:
  order: 1
  label: "Observability"
---
> **Toolkit Track** | 8 Modules | ~6.5 hours total

## Overview

The Observability Toolkit covers the essential tools for monitoring, logging, and tracing cloud-native applications. These are the instruments you'll use daily to understand what's happening in your systems.

This toolkit builds on the theoretical foundations from [Observability Theory](../../foundations/observability-theory/) and shows you how to implement those concepts with production-grade tools.

## Prerequisites

Before starting this toolkit:
- [Observability Theory Track](../../foundations/observability-theory/) — Conceptual foundation
- [SRE Discipline](../../disciplines/core-platform/sre/) — Where observability fits (recommended)
- Basic Kubernetes knowledge
- Command-line familiarity

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 1.1 | [Prometheus](module-1.1-prometheus/) | `[COMPLEX]` | 45-50 min |
| 1.2 | [OpenTelemetry](module-1.2-opentelemetry/) | `[COMPLEX]` | 45-50 min |
| 1.3 | [Grafana](module-1.3-grafana/) | `[COMPLEX]` | 40-45 min |
| 1.4 | [Loki](module-1.4-loki/) | `[COMPLEX]` | 40-45 min |
| 1.5 | [Distributed Tracing](module-1.5-tracing/) | `[COMPLEX]` | 45-50 min |
| 1.6 | [Pixie](module-1.6-pixie/) | `[MEDIUM]` | 90 min |
| 1.7 | [Hubble](module-1.7-hubble/) | `[MEDIUM]` | 90 min |
| 1.8 | [Coroot](module-1.8-coroot/) | `[MEDIUM]` | 90 min |
| 1.9 | [Continuous Profiling](module-1.9-continuous-profiling/) | `[MEDIUM]` | 40 min |
| 1.10 | [SLO Tooling](module-1.10-slo-tooling/) | `[MEDIUM]` | 40 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy Prometheus** — Scraping, PromQL, alerting, service discovery
2. **Instrument with OpenTelemetry** — SDK, Collector, auto-instrumentation
3. **Build Grafana dashboards** — Variables, Four Golden Signals, Explore
4. **Aggregate logs with Loki** — LogQL, Promtail, multi-tenancy
5. **Trace distributed requests** — Jaeger, Tempo, TraceQL, sampling
6. **Use Pixie for zero-instrumentation observability** — eBPF, PxL queries, instant debugging
7. **Deploy Hubble for network observability** — Cilium integration, network policy debugging
8. **Deploy Coroot for auto-instrumented observability** — Zero-code tracing, SLOs, profiling

## The Observability Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY STACK                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  YOUR APPLICATION                                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      Instrumented Code                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │ Metrics  │  │  Logs    │  │  Traces  │               │   │
│  │  │ /metrics │  │ stdout   │  │ spans    │               │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘               │   │
│  └───────┼─────────────┼─────────────┼──────────────────────┘   │
│          │             │             │                          │
│          │             │             │ OTLP                     │
│          ▼             ▼             ▼                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              OPENTELEMETRY COLLECTOR                      │   │
│  │  (receives, processes, exports all signals)               │   │
│  └───────┬─────────────┬─────────────┬──────────────────────┘   │
│          │             │             │                          │
│          ▼             ▼             ▼                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                  │
│  │ PROMETHEUS │ │   LOKI     │ │   TEMPO    │                  │
│  │ (metrics)  │ │  (logs)    │ │ (traces)   │                  │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘                  │
│        │              │              │                          │
│        └──────────────┼──────────────┘                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     GRAFANA                               │   │
│  │  (unified visualization, dashboards, exploration)         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Tool Selection Guide

| Need | Tool | Why |
|------|------|-----|
| Metrics storage | Prometheus | Industry standard, PromQL, native K8s |
| Metrics at scale | Thanos/Mimir | Multi-cluster, long-term, HA |
| Instrumentation | OpenTelemetry | Vendor-neutral, complete SDK |
| Log aggregation | Loki | Cost-effective, Grafana native |
| Log search (heavy) | Elasticsearch | Full-text, complex queries |
| Tracing (search) | Jaeger | Tag-based search, standalone UI |
| Tracing (cheap) | Tempo | Object storage, trace ID only |
| Dashboards | Grafana | Unifies all signals, plugins |

## Study Path

```
Module 1.1: Prometheus
     │
     │  Foundation: metrics collection
     ▼
Module 1.2: OpenTelemetry
     │
     │  Modern instrumentation standard
     ▼
Module 1.3: Grafana
     │
     │  Visualization for all signals
     ▼
Module 1.4: Loki
     │
     │  Log aggregation "Prometheus-style"
     ▼
Module 1.5: Distributed Tracing
     │
     │  Jaeger, Tempo, correlation
     ▼
[Toolkit Complete] → GitOps & Deployments Toolkit
```

## Key Concepts

### The Three Pillars

| Pillar | Question Answered | Tool |
|--------|-------------------|------|
| **Metrics** | What is happening? (quantitative) | Prometheus |
| **Logs** | Why did it happen? (context) | Loki |
| **Traces** | Where did it happen? (request flow) | Jaeger/Tempo |

### When to Use What

```
INVESTIGATING AN INCIDENT:

1. METRICS → "Is something wrong?"
   • Dashboard shows latency spike
   • Error rate increasing
   • CPU/memory abnormal

2. TRACES → "Where is the problem?"
   • Find slow trace via exemplar
   • See which service is slow
   • Identify bottleneck span

3. LOGS → "What exactly happened?"
   • Filter by trace_id
   • See error messages
   • Get full context
```

## Related Tracks

- **Before**: [Observability Theory](../../foundations/observability-theory/) — Why these tools exist
- **Related**: [SRE Discipline](../../disciplines/core-platform/sre/) — How to apply observability
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Deploy observability stack with Terraform
- **After**: [GitOps & Deployments Toolkit](../gitops-deployments/) — Deploy observable apps

---

*"You can't improve what you can't measure. You can't debug what you can't see. Observability gives you both."*

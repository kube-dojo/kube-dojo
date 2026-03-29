---
title: "AIOps Tools Toolkit"
sidebar:
  order: 1
  label: "AIOps Tools"
---
> **Toolkit Track** | 4 Modules | ~3 hours total

## Overview

The AIOps Tools Toolkit covers practical implementations of AIOps capabilities—from open-source anomaly detection libraries to enterprise correlation platforms. You'll learn when to use Prophet vs. Isolation Forest, how commercial platforms like BigPanda and Moogsoft work, and how to build custom AIOps pipelines on Kubernetes.

This toolkit applies concepts from [AIOps Discipline](../../../disciplines/data-ai/aiops/).

## Prerequisites

Before starting this toolkit:
- [AIOps Discipline](../../../disciplines/data-ai/aiops/) — Complete the conceptual foundation
- [Observability Toolkit](../observability/) — Data collection layer
- Python proficiency for anomaly detection exercises
- Kubernetes basics for custom pipeline exercises

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 10.1 | [Anomaly Detection Tools](module-10.1-anomaly-detection-tools/) | `[MEDIUM]` | 40-45 min |
| 10.2 | [Event Correlation Platforms](module-10.2-event-correlation-platforms/) | `[MEDIUM]` | 40-45 min |
| 10.3 | [Observability AI Features](module-10.3-observability-ai-features/) | `[MEDIUM]` | 40-45 min |
| 10.4 | [Building Custom AIOps](module-10.4-building-custom-aiops/) | `[COMPLEX]` | 50-60 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Choose anomaly detection tools** — Prophet, Luminaire, PyOD for different use cases
2. **Evaluate correlation platforms** — BigPanda, Moogsoft, PagerDuty AIOps
3. **Leverage observability AI** — Datadog Watchdog, Dynatrace Davis, New Relic AI
4. **Build custom pipelines** — Python + Kafka + Kubernetes for custom AIOps

## Tool Selection Guide

```
WHICH AIOPS TOOL?
─────────────────────────────────────────────────────────────────

"I need time series anomaly detection with seasonality"
└──▶ Prophet (Facebook)
     • Handles multiple seasonalities
     • Trend detection
     • Holiday effects
     • Good for forecasting

"I need fast, streaming anomaly detection"
└──▶ Luminaire (Zillow)
     • Real-time detection
     • Minimal configuration
     • Handles structural breaks
     • Python-native

"I need multi-dimensional anomaly detection"
└──▶ PyOD / Isolation Forest
     • High-dimensional data
     • Multiple algorithms
     • Scikit-learn compatible
     • Good for logs, metrics together

"I need enterprise event correlation"
└──▶ BigPanda / Moogsoft
     • Topology-aware correlation
     • ML-based grouping
     • Integration ecosystem
     • SLA management

"I need AI built into my observability platform"
└──▶ Datadog Watchdog / Dynatrace Davis
     • No additional setup
     • Correlates with metrics/traces
     • Auto-baselining
     • Root cause suggestions

"I need custom AIOps for my unique requirements"
└──▶ Build with Python + Kafka + K8s
     • Full control
     • Domain-specific models
     • Data stays in-house
     • Higher engineering investment
```

## The AIOps Tool Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│                   AIOPS TOOL LANDSCAPE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OPEN SOURCE / LIBRARIES                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ANOMALY DETECTION        TIME SERIES        ML TOOLKITS  │  │
│  │  ┌─────────┐             ┌─────────┐       ┌─────────┐   │  │
│  │  │  PyOD   │             │ Prophet │       │Scikit-  │   │  │
│  │  │(library)│             │(Facebook│       │learn    │   │  │
│  │  └─────────┘             └─────────┘       └─────────┘   │  │
│  │  ┌─────────┐             ┌─────────┐       ┌─────────┐   │  │
│  │  │Luminaire│             │ Kats    │       │ PyTorch │   │  │
│  │  │(Zillow) │             │(Facebook│       │LSTM etc.│   │  │
│  │  └─────────┘             └─────────┘       └─────────┘   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  EVENT CORRELATION PLATFORMS                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│  │  │BigPanda │  │Moogsoft │  │PagerDuty│  │ServiceNow    │  │
│  │  │         │  │         │  │  AIOps  │  │  ITOM   │     │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  OBSERVABILITY PLATFORM AI                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│  │  │ Datadog │  │Dynatrace│  │New Relic│  │ Splunk  │     │  │
│  │  │Watchdog │  │ Davis   │  │   AI    │  │  ITSI   │     │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  STREAM PROCESSING (For Custom Solutions)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│  │  │  Kafka  │  │  Flink  │  │ Spark   │  │  Beam   │     │  │
│  │  │Streams  │  │         │  │Streaming│  │         │     │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## When to Build vs Buy

| Factor | Build Custom | Buy Platform |
|--------|-------------|--------------|
| **Time to value** | Months | Days/Weeks |
| **Customization** | Unlimited | Limited |
| **Maintenance** | Your team | Vendor |
| **Data control** | Full | Vendor dependent |
| **Integration** | Any | Ecosystem |
| **Cost model** | Engineering time | License + usage |
| **Best for** | Unique requirements | Standard ops |

**Recommendation**: Start with a platform (Datadog, PagerDuty), build custom components only for unique requirements.

## Study Path

```
Module 10.1: Anomaly Detection Tools
     │
     │  Prophet, Luminaire, PyOD
     │  When to use each
     ▼
Module 10.2: Event Correlation Platforms
     │
     │  BigPanda, Moogsoft, PagerDuty
     │  Enterprise capabilities
     ▼
Module 10.3: Observability AI Features
     │
     │  Built-in AI in monitoring platforms
     │  Datadog, Dynatrace, New Relic
     ▼
Module 10.4: Building Custom AIOps
     │
     │  Python + Kafka + Kubernetes
     │  End-to-end custom pipeline
     ▼
[Toolkit Complete] → Production AIOps!
```

## Key Tools Summary

### Anomaly Detection

| Tool | Best For | Complexity | License |
|------|----------|------------|---------|
| **Prophet** | Time series with seasonality | Low | MIT |
| **Luminaire** | Real-time streaming | Low | Apache 2.0 |
| **PyOD** | Multi-dimensional, many algorithms | Medium | BSD |
| **Isolation Forest** | High-dimensional data | Low | BSD (sklearn) |

### Event Correlation

| Platform | Strength | Deployment | Pricing |
|----------|----------|------------|---------|
| **BigPanda** | Topology correlation | SaaS | Enterprise |
| **Moogsoft** | ML-based clustering | SaaS/On-prem | Enterprise |
| **PagerDuty AIOps** | Incident management integration | SaaS | Tiered |
| **ServiceNow ITOM** | ITSM integration | SaaS/On-prem | Enterprise |

### Observability AI

| Platform | AI Feature | Best For |
|----------|------------|----------|
| **Datadog** | Watchdog | Broad monitoring, auto-detection |
| **Dynatrace** | Davis AI | Full-stack, auto-instrumentation |
| **New Relic** | Applied Intelligence | APM-centric, anomaly detection |
| **Splunk** | ITSI | Log-heavy environments |

## Integration Architecture

```
INTEGRATED AIOPS ARCHITECTURE
─────────────────────────────────────────────────────────────────

DATA SOURCES
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Metrics │  Logs   │ Traces  │ Events  │ Changes │
└────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘
     │         │         │         │         │
     └─────────┴─────────┴─────────┴─────────┘
                         │
COLLECTION               ▼
              ┌─────────────────────┐
              │ Observability Stack │
              │ (Prometheus, OTel)  │
              └──────────┬──────────┘
                         │
ANALYSIS                 ▼
              ┌─────────────────────┐
              │   AIOps Platform    │
              │  ┌──────┬──────┐   │
              │  │Anomaly│Correl│   │
              │  │Detect │ation │   │
              │  └──────┴──────┘   │
              │  ┌──────┬──────┐   │
              │  │ RCA  │Predict   │
              │  │Engine│  Ops │   │
              │  └──────┴──────┘   │
              └──────────┬──────────┘
                         │
ACTION                   ▼
              ┌─────────────────────┐
              │    Remediation      │
              │  (Auto/Manual)      │
              └─────────────────────┘
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Anomaly Detection | Build detector with Prophet + Luminaire |
| Event Correlation | Evaluate platform with sample data |
| Observability AI | Configure Datadog Watchdog alerts |
| Custom AIOps | Build end-to-end pipeline on K8s |

## Common Patterns

### Pattern 1: Open Source Stack

```
Open Source AIOps Stack
─────────────────────────────────────────────────────────────────

Prometheus + Grafana (Metrics)
        │
        ▼
Prophet/Luminaire (Anomaly Detection)
        │
        ▼
Custom Python (Correlation)
        │
        ▼
PagerDuty (Alerting)
```

### Pattern 2: Commercial Platform

```
Commercial AIOps Stack
─────────────────────────────────────────────────────────────────

Datadog (Full Observability)
        │
        ├── Watchdog (Anomaly Detection)
        │
        ▼
BigPanda (Event Correlation)
        │
        ▼
PagerDuty (Incident Management)
```

### Pattern 3: Hybrid

```
Hybrid AIOps Stack
─────────────────────────────────────────────────────────────────

Prometheus + Datadog (Metrics)
        │
        ├── Datadog Watchdog (Standard metrics)
        │
        ├── Custom ML (Domain-specific)
        │
        ▼
Custom Correlation (Topology-aware)
        │
        ▼
Auto-Remediation (Kubernetes operators)
```

## Related Tracks

- **Before**: [AIOps Discipline](../../../disciplines/data-ai/aiops/) — Conceptual foundation
- **Related**: [IaC Tools Toolkit](../../infrastructure-networking/iac-tools/) — Terraform modules for AIOps infrastructure
- **Related**: [Observability Toolkit](../observability/) — Data collection layer
- **Related**: [SRE Discipline](../../../disciplines/core-platform/sre/) — Operational practices
- **After**: Build production AIOps!

---

*"The best AIOps tool is the one your team will actually use. Start simple, prove value, then expand."*

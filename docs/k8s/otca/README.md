# OTCA - OpenTelemetry Certified Associate

> **Multiple-choice exam** | 90 minutes | Passing score: 75% | $250 USD | **CNCF Certification**

## Overview

The OTCA (OpenTelemetry Certified Associate) validates your understanding of OpenTelemetry concepts, architecture, and the OTel ecosystem. Unlike CKA/CKS, this is a **knowledge-based exam** — multiple-choice questions, not hands-on tasks. But don't let that fool you: Domain 2 (API & SDK) is 46% of the exam and requires deep understanding of TracerProviders, MeterProviders, span processors, sampling strategies, and context propagation internals.

**KubeDojo covers ~90% of OTCA topics** through existing observability modules plus two dedicated OTCA modules covering SDK pipeline internals and advanced Collector configuration.

> **OpenTelemetry is the second most active CNCF project** after Kubernetes. If you work with observability in any capacity, OTCA validates the skill that matters most: understanding the universal telemetry standard.

---

## OTCA-Specific Modules

These modules fill the gaps between KubeDojo's existing observability modules and the OTCA exam requirements:

| # | Module | Topic | Domains Covered |
|---|--------|-------|-----------------|
| 1 | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) | TracerProvider, MeterProvider, span processors, sampling, context propagation | Domain 2 (46%) |
| 2 | [OTel Collector Advanced](module-2-otel-collector-advanced.md) | Collector pipelines, deployment patterns, connectors, distributions | Domain 3 (26%) |

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage |
|--------|--------|-------------------|
| Fundamentals of Observability | 18% | Excellent (4 foundation modules) |
| OTel API and SDK | 46% | Excellent ([OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) + overview module) |
| OTel Collector | 26% | Excellent ([OTel Collector Advanced](module-2-otel-collector-advanced.md) + overview module) |
| Ecosystem | 10% | Good (covered across multiple modules) |

---

## Domain 1: Fundamentals of Observability (18%)

### Competencies
- Understanding the three pillars of observability (metrics, logs, traces)
- Applying semantic conventions for consistent telemetry
- Distinguishing instrumentation approaches (auto vs. manual)
- Understanding signals and their relationships

### KubeDojo Learning Path

**Theory (start here):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability.md) | What is Observability? Observability vs. monitoring | Direct |
| [Observability 3.2](../../platform/foundations/observability-theory/module-3.2-the-three-pillars.md) | Metrics, Logs, Traces — the three pillars | Direct |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles.md) | Instrumentation principles: auto vs. manual, what to measure | Direct |
| [Observability 3.4](../../platform/foundations/observability-theory/module-3.4-from-data-to-insight.md) | From data to insight | Partial |

**Tools (context):**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | OTel architecture overview, signals, auto-instrumentation | Direct |
| [Tracing](../../platform/toolkits/observability/module-1.5-tracing.md) | Distributed tracing concepts, Jaeger/Tempo | Direct |
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Metrics fundamentals, metric types, PromQL | Partial |

### Key Exam Topics — Additional Study
- **Semantic conventions** — Covered in [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md); supplement with the [official semconv reference](https://opentelemetry.io/docs/specs/semconv/)
- **Signal relationships** — Exemplars linking metrics to traces are covered in [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md)
- **Resource vs. attribute semantics** — Resource describes the entity, attributes describe the event — covered in [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md)

---

## Domain 2: OTel API and SDK (46%)

> **This is the exam.** Nearly half your score comes from this domain. You need to understand the SDK pipeline architecture at a level deeper than "it collects telemetry."

### Competencies
- Understanding the OTel data model (traces, metrics, logs, baggage)
- Configuring TracerProvider, MeterProvider, and LoggerProvider
- Understanding span processors (Simple vs. Batch) and their trade-offs
- Implementing sampling strategies (AlwaysOn, AlwaysOff, TraceIdRatio, ParentBased)
- Working with context propagation (W3C TraceContext, B3, Baggage)
- Understanding metric instruments (Counter, Histogram, Gauge, UpDownCounter)
- Configuring exporters and SDK pipelines
- Using the OTel agent for auto-instrumentation

### KubeDojo Learning Path

**Existing coverage:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | OTel SDK overview, auto-instrumentation basics | Partial |
| [Tracing](../../platform/toolkits/observability/module-1.5-tracing.md) | Spans, trace context, propagation basics | Partial |
| [Observability 3.3](../../platform/foundations/observability-theory/module-3.3-instrumentation-principles.md) | Instrumentation theory and principles | Partial |
| [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) | TracerProvider, MeterProvider, span processors, sampling, context propagation, metric instruments | Direct |

### Key Exam Topics — Now Covered

All of the following are covered in the [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md):

- **TracerProvider pipeline**: `TracerProvider` -> `SpanProcessor` -> `SpanExporter` — how spans flow from creation to export
- **MeterProvider pipeline**: `MeterProvider` -> `MetricReader` -> `MetricExporter` — push vs. pull metric export
- **LoggerProvider pipeline**: `LoggerProvider` -> `LogRecordProcessor` -> `LogRecordExporter`
- **Span processors**: `SimpleSpanProcessor` (sync, for debugging) vs. `BatchSpanProcessor` (async, for production) — know the trade-offs cold
- **Sampling strategies**: `AlwaysOnSampler`, `AlwaysOffSampler`, `TraceIdRatioBasedSampler`, `ParentBasedSampler`, head vs. tail sampling
- **Context propagation internals**: `TextMapPropagator`, `TextMapGetter/Setter`, injection/extraction, composite propagators
- **Metric instruments in detail**: Synchronous (Counter, UpDownCounter, Histogram) and Asynchronous (ObservableCounter, ObservableGauge, ObservableUpDownCounter), aggregation temporality
- **Exemplars**: Linking metrics to trace samples
- **Baggage**: Cross-cutting concerns propagated through context (not telemetry data itself)
- **SDK configuration**: Environment variables (`OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES_SAMPLER`), programmatic vs. file-based config

---

## Domain 3: OTel Collector (26%)

### Competencies
- Understanding Collector architecture and deployment patterns
- Configuring receivers, processors, and exporters
- Building pipelines for traces, metrics, and logs
- Deploying Collector as agent (DaemonSet) vs. gateway (Deployment)
- Understanding Collector distributions (core vs. contrib)

### KubeDojo Learning Path

**Existing coverage:**

| Module | Topic | Relevance |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | Collector overview, receiver/processor/exporter basics | Partial |
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Prometheus receiver/exporter context | Partial |
| [Tracing](../../platform/toolkits/observability/module-1.5-tracing.md) | Trace pipeline concepts | Partial |
| [OTel Collector Advanced](module-2-otel-collector-advanced.md) | Pipeline configuration, deployment patterns, connectors, distributions, processors | Direct |

### Key Exam Topics — Now Covered

All of the following are covered in the [OTel Collector Advanced](module-2-otel-collector-advanced.md):

- **Collector configuration deep dive**: Full pipeline YAML (receivers, processors, exporters, service.pipelines)
- **Deployment patterns**: Agent (sidecar/DaemonSet) vs. Gateway (Deployment) — when to use each
- **Collector distributions**: `otelcol` (core) vs. `otelcol-contrib` (200+ components) vs. custom builds with `ocb` (OpenTelemetry Collector Builder)
- **Key processors**: `batch`, `memory_limiter`, `filter`, `attributes`, `resource`, `tail_sampling`, `transform`
- **Connector component**: Connects two pipelines (e.g., `spanmetrics` connector generates RED metrics from traces)
- **OTLP protocol**: gRPC and HTTP/protobuf transports
- **OTel Operator for Kubernetes**: Auto-instrumentation injection, Collector CRD management
- **Health and observability**: Collector's own metrics, `zpages` extension, health check extension

---

## Domain 4: Ecosystem (10%)

### Competencies
- Understanding OpenTelemetry project status and maturity levels
- Knowing signal stability (traces = stable, metrics = stable, logs = stable, profiling = development)
- Understanding OTLP (OpenTelemetry Protocol) and its role
- Knowing the relationship between OTel and CNCF
- Understanding backend integrations and vendor neutrality

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [OpenTelemetry](../../platform/toolkits/observability/module-1.2-opentelemetry.md) | OTel project overview, CNCF status, architecture | Direct |
| [Observability 3.1](../../platform/foundations/observability-theory/module-3.1-what-is-observability.md) | Observability landscape and evolution | Partial |
| [Prometheus](../../platform/toolkits/observability/module-1.1-prometheus.md) | Prometheus as OTel metrics backend | Partial |
| [Tracing](../../platform/toolkits/observability/module-1.5-tracing.md) | Jaeger/Tempo as OTel trace backends | Partial |
| [Continuous Profiling](../../platform/toolkits/observability/module-1.9-continuous-profiling.md) | Profiling signal (newest addition) | Partial |

### Key Exam Topics — Coverage Notes

- **OTLP protocol details** — Covered in [OTel Collector Advanced](module-2-otel-collector-advanced.md) (gRPC, HTTP/protobuf transports, OTLP/JSON)
- **OpenTelemetry Operator for Kubernetes** — Covered in [OTel Collector Advanced](module-2-otel-collector-advanced.md) (auto-instrumentation injection, Collector CRD)
- **Signal maturity model** — Supplement with the [OTel status page](https://opentelemetry.io/status/); traces/metrics/logs = stable, profiling = development
- **Community structure** — SIGs, language SIGs, Collector SIG, specification process; review [OTel community docs](https://opentelemetry.io/community/)
- **Compatibility guarantees** — What "stable" means for API vs. SDK vs. Collector components; review [OTel versioning spec](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/)

---

## Study Strategy

```
OTCA PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1: Observability Foundations (Domain 1 — 18%)
├── Observability Theory 3.1-3.4 (existing KubeDojo modules)
├── Review semantic conventions: https://opentelemetry.io/docs/specs/semconv/
└── Understand signal types and their relationships

Week 2-3: OTel API and SDK (Domain 2 — 46%!)
├── OTel module 1.2 (existing KubeDojo overview)
├── OTel docs: https://opentelemetry.io/docs/concepts/
├── Study TracerProvider/MeterProvider/LoggerProvider pipelines
├── Practice: instrument a simple app in your preferred language
├── Deep dive: sampling strategies (ParentBased wrapping TraceIdRatio)
├── Deep dive: context propagation (W3C TraceContext headers)
└── Memorize: environment variable configuration options

Week 4: OTel Collector (Domain 3 — 26%)
├── Deploy a Collector locally (Docker or K8s)
├── Build pipelines: receivers -> processors -> exporters
├── Practice: agent vs. gateway deployment patterns
├── Configure: batch, memory_limiter, filter processors
├── Know: core vs. contrib distributions, ocb builder
└── Study the connector component (spanmetrics, count)

Week 5: Ecosystem + Review (Domain 4 — 10%)
├── Read OTel project status pages
├── Understand OTLP protocol (gRPC + HTTP transports)
├── Review OpenTelemetry Operator for Kubernetes
├── Practice exam questions (see resources below)
└── Final review: focus 60% of time on Domain 2 + Domain 3
```

---

## Exam Tips

- **Domain 2 is nearly half the exam** — you cannot pass without solid SDK knowledge. Understand the provider/processor/exporter pipeline pattern for all three signal types.
- **Know the configuration** — environment variables like `OTEL_SERVICE_NAME`, `OTEL_TRACES_SAMPLER`, `OTEL_EXPORTER_OTLP_ENDPOINT` are heavily tested.
- **Understand sampling trade-offs** — head sampling (SDK-side, cheaper) vs. tail sampling (Collector-side, more intelligent but requires all spans).
- **Collector config is YAML** — know the structure: `receivers`, `processors`, `exporters`, `connectors`, `extensions`, `service.pipelines`.
- **Don't confuse API and SDK** — the API defines interfaces (safe for libraries), the SDK implements them (configured by applications). Libraries use the API; applications configure the SDK.
- **Baggage is NOT telemetry** — it's context propagation for application data, not observability data. This distinction is commonly tested.
- **Study the specification** — the exam tests OTel concepts, not specific language implementations. Focus on the language-agnostic spec.

---

## Gap Analysis

KubeDojo's observability modules plus the two dedicated OTCA modules now provide comprehensive coverage across all four domains.

| Topic | Status | Notes |
|-------|--------|-------|
| Three pillars / observability theory | Covered | Existing foundation modules 3.1-3.4 |
| Semantic conventions | Covered | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) |
| TracerProvider / MeterProvider pipelines | Covered | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) |
| Span processors (Simple vs. Batch) | Covered | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) |
| Sampling strategies (head vs. tail) | Covered | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) |
| Context propagation internals | Covered | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) |
| Metric instruments (sync vs. async) | Covered | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) |
| Exemplars | Covered | [OTel SDK Deep Dive](module-1-otel-sdk-deep-dive.md) |
| Collector configuration deep dive | Covered | [OTel Collector Advanced](module-2-otel-collector-advanced.md) |
| Collector deployment patterns | Covered | [OTel Collector Advanced](module-2-otel-collector-advanced.md) |
| Collector connectors | Covered | [OTel Collector Advanced](module-2-otel-collector-advanced.md) |
| OTLP protocol details | Covered | [OTel Collector Advanced](module-2-otel-collector-advanced.md) |
| OTel Operator for Kubernetes | Covered | [OTel Collector Advanced](module-2-otel-collector-advanced.md) |
| Signal maturity levels | Minor gap | Review [OTel status page](https://opentelemetry.io/status/) for current signal maturity levels |

---

## Essential Study Resources

- **OpenTelemetry Documentation**: [opentelemetry.io/docs](https://opentelemetry.io/docs/) — the primary source of truth
- **OTel Specification**: [github.com/open-telemetry/opentelemetry-specification](https://github.com/open-telemetry/opentelemetry-specification) — the exam tests spec concepts
- **OTel Collector Docs**: [opentelemetry.io/docs/collector](https://opentelemetry.io/docs/collector/)
- **Semantic Conventions**: [opentelemetry.io/docs/specs/semconv](https://opentelemetry.io/docs/specs/semconv/)
- **CNCF OTCA Page**: [training.linuxfoundation.org](https://training.linuxfoundation.org/) — official exam details

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Observability Track:
├── KCNA (Cloud Native Associate) — includes observability basics
├── OTCA (OTel Certified Associate) ← YOU ARE HERE
└── Future: Advanced OTel certification (TBD)

Complementary Certifications:
├── CKA (K8s Administrator) — deploy/manage observability stacks
├── CNPE (Platform Engineer) — 20% observability & operations
└── Prometheus Certified Associate (PCA) — deep metrics expertise

Recommended Order:
  KCNA → OTCA → PCA → CKA → CNPE
```

The OTCA pairs naturally with PCA (Prometheus Certified Associate) — together they cover the full metrics pipeline from instrumentation (OTel) through storage and querying (Prometheus/PromQL). If you've completed KubeDojo's observability toolkit modules, you have a head start on both.

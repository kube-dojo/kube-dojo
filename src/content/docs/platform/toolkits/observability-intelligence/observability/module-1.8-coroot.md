---
title: "Module 1.8: Coroot - Zero-Instrumentation Observability"
slug: platform/toolkits/observability-intelligence/observability/module-1.8-coroot
sidebar:
  order: 9
---
## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 1.1 (Prometheus), Module 1.2 (OpenTelemetry), Basic Kubernetes concepts
**Learning Objectives**:
- Understand eBPF-based auto-instrumentation observability
- Deploy Coroot on Kubernetes
- Use service maps and automatic SLO tracking
- Correlate metrics, traces, logs, and profiles without code changes

---

## Why This Module Matters

The engineering director stared at the spreadsheet, calculating the true cost of their "modern" observability stack. Fifty-three microservices. Each one needed instrumentation.

| Service Type | Count | Instrumentation Time | Engineer Cost |
|--------------|-------|---------------------|---------------|
| Node.js services | 23 | 4 hours each | $13,800 |
| Python services | 18 | 6 hours each | $16,200 |
| Go services | 8 | 5 hours each | $6,000 |
| Legacy Java | 4 | 12 hours each | $7,200 |
| **Total** | **53** | **276 hours** | **$43,200** |

And that was just the initial setup. Every new service needed instrumentation. Every framework upgrade risked breaking telemetry. Two full-time engineers spent 40% of their time maintaining observability code—not application features.

Then there was the incident that changed everything. A production outage lasted 47 minutes because traces ended at a legacy Java service with no instrumentation. The root cause—a database connection pool exhaustion—was invisible. Post-mortem cost: $127,000 in SLA credits.

"What if we didn't need to instrument anything?" an SRE asked during the incident review.

**Coroot eliminates the instrumentation burden.**

Using eBPF to observe applications at the kernel level, Coroot automatically discovers services, tracks their dependencies, monitors SLOs, and provides distributed tracing—all without a single line of instrumentation code. It's like having a full observability stack installed on day one, even for legacy applications you can't modify.

That e-commerce company deployed Coroot on a Friday afternoon. By Monday morning: all 53 services visible, service map auto-generated, SLOs calculated, traces flowing through the legacy Java monolith that had been a black box for two years. Time invested: 2 hours of Helm commands. Not 276 hours of SDK integration.

---

## Did You Know?

- **One fintech saved $380,000 annually by replacing Datadog with Coroot** — Their 200-service deployment cost $31K/month in APM fees. Coroot (open source) plus ClickHouse hosting: ~$800/month. They got better visibility into legacy systems that Datadog's agents couldn't instrument.

- **Coroot detected a $2.1M incident in 3 minutes—traditional APM missed it entirely** — A cryptocurrency exchange experienced a trading halt from TCP retransmissions between their matching engine and database. Application metrics showed nothing wrong. Coroot's kernel-level TCP monitoring caught the network degradation immediately.

- **Zero-instrumentation tracing saves 2-4 weeks per microservice** — Traditional distributed tracing requires SDK integration, context propagation code, and careful testing. Companies report 40-80 hours of engineering time per service. Coroot captures trace context at the kernel level—instant tracing for any application, any language.

- **eBPF profiling found a $450K memory leak invisible to APM** — A SaaS company's Go service had a native memory leak in a C library (CGO). Application heap metrics were stable, but container memory grew until OOMKill. Coroot's continuous profiling saw the off-heap growth that Datadog and New Relic couldn't detect.

---

## Coroot Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Kubernetes Cluster                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Coroot Components                                │   │
│  │                                                                      │   │
│  │  ┌──────────────────┐     ┌──────────────────┐                      │   │
│  │  │   Coroot Server  │     │   ClickHouse     │                      │   │
│  │  │                  │────▶│   (Time-series)  │                      │   │
│  │  │  - API Server    │     │                  │                      │   │
│  │  │  - UI Dashboard  │     │  - Metrics       │                      │   │
│  │  │  - SLO Engine    │     │  - Traces        │                      │   │
│  │  │  - Alerting      │     │  - Logs          │                      │   │
│  │  └────────┬─────────┘     │  - Profiles      │                      │   │
│  │           │               └──────────────────┘                      │   │
│  │           │ Pull metrics                                             │   │
│  │           ▼                                                          │   │
│  │  ┌──────────────────┐                                               │   │
│  │  │    Prometheus    │◀─── Scrapes coroot-node-agent                 │   │
│  │  └──────────────────┘                                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                  │
│  │    Node 1     │  │    Node 2     │  │    Node 3     │                  │
│  │  ┌─────────┐  │  │  ┌─────────┐  │  │  ┌─────────┐  │                  │
│  │  │ coroot  │  │  │  │ coroot  │  │  │  │ coroot  │  │                  │
│  │  │ node    │  │  │  │ node    │  │  │  │ node    │  │                  │
│  │  │ agent   │  │  │  │ agent   │  │  │  │ agent   │  │                  │
│  │  └────┬────┘  │  │  └────┬────┘  │  │  └────┬────┘  │                  │
│  │       │eBPF   │  │       │eBPF   │  │       │eBPF   │                  │
│  │  ┌────┴────┐  │  │  ┌────┴────┐  │  │  ┌────┴────┐  │                  │
│  │  │ Kernel  │  │  │  │ Kernel  │  │  │  │ Kernel  │  │                  │
│  │  │ Events  │  │  │  │ Events  │  │  │  │ Events  │  │                  │
│  │  └─────────┘  │  │  └─────────┘  │  │  └─────────┘  │                  │
│  └───────────────┘  └───────────────┘  └───────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Role | Description |
|-----------|------|-------------|
| **coroot-node-agent** | Data collection | DaemonSet running eBPF programs to capture kernel-level events |
| **Coroot Server** | Processing & UI | Aggregates data, calculates SLOs, serves dashboard |
| **ClickHouse** | Storage | Columnar database for metrics, traces, logs, profiles |
| **Prometheus** | Metrics pipeline | Optional—Coroot can scrape Prometheus or use its own |

---

## What Coroot Captures Automatically

### Application Metrics (No SDK Required)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Auto-Captured Metrics                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HTTP/gRPC Requests        TCP Connections        System        │
│  ├─ Request rate           ├─ Connection count    ├─ CPU usage  │
│  ├─ Error rate             ├─ Retransmits         ├─ Memory     │
│  ├─ Latency (p50/95/99)    ├─ RTT latency         ├─ Disk I/O   │
│  └─ Status codes           └─ Failed connects     └─ Network    │
│                                                                 │
│  DNS Queries               Container Metrics      Profiling     │
│  ├─ Query count            ├─ Restarts            ├─ CPU        │
│  ├─ Resolution time        ├─ OOM kills           ├─ Memory     │
│  └─ NXDOMAIN errors        └─ Resource limits     └─ Off-CPU    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Automatic Service Discovery

Coroot discovers services by observing actual network traffic:

```
Discovered Services (auto-detected from traffic):
├── frontend (10 pods)
│   ├── Talks to: api-gateway, redis
│   └── SLO: 99.9% availability, P99 < 200ms
├── api-gateway (5 pods)
│   ├── Talks to: user-service, order-service, postgres
│   └── SLO: 99.95% availability, P99 < 100ms
├── user-service (3 pods)
│   ├── Talks to: postgres, redis
│   └── SLO: 99.9% availability, P99 < 50ms
└── postgres (1 pod)
    ├── Accepts from: api-gateway, user-service, order-service
    └── SLO: 99.99% availability
```

---

## Installing Coroot

### Prerequisites

```bash
# Coroot requires:
# - Kubernetes 1.21+
# - Linux kernel 4.16+ (for eBPF)
# - BTF (BPF Type Format) support in kernel

# Check BTF support
cat /sys/kernel/btf/vmlinux >/dev/null 2>&1 && echo "BTF supported" || echo "BTF not supported"

# Most modern distributions (Ubuntu 20.04+, RHEL 8+, Debian 11+) support BTF
```

### Installation with Helm

```bash
# Add Coroot Helm repository
helm repo add coroot https://coroot.github.io/helm-charts
helm repo update

# Create namespace
kubectl create namespace coroot

# Install Coroot with ClickHouse
helm install coroot coroot/coroot \
  --namespace coroot \
  --set clickhouse.enabled=true \
  --set clickhouse.persistence.size=50Gi

# Install node agent (DaemonSet)
helm install coroot-node-agent coroot/coroot-node-agent \
  --namespace coroot \
  --set coroot.url=http://coroot.coroot:8080
```

### Verify Installation

```bash
# Check all pods are running
kubectl get pods -n coroot

# Expected output:
# NAME                              READY   STATUS    RESTARTS   AGE
# coroot-0                          1/1     Running   0          2m
# coroot-clickhouse-0               1/1     Running   0          2m
# coroot-node-agent-xxxxx           1/1     Running   0          2m
# coroot-node-agent-yyyyy           1/1     Running   0          2m

# Check node agent is collecting data
kubectl logs -n coroot -l app.kubernetes.io/name=coroot-node-agent --tail=20

# Access the UI
kubectl port-forward -n coroot svc/coroot 8080:8080

# Open http://localhost:8080
```

---

## The Coroot Dashboard

### Service Map

The service map is automatically generated from observed traffic:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Coroot Service Map                               │
│                                                                         │
│    ┌──────────┐                                                         │
│    │ Internet │                                                         │
│    └────┬─────┘                                                         │
│         │                                                               │
│         ▼                                                               │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐                      │
│    │ ingress  │────▶│ frontend │────▶│   api    │                      │
│    │  nginx   │     │  (React) │     │ (Node.js)│                      │
│    └──────────┘     └──────────┘     └────┬─────┘                      │
│                                           │                             │
│                     ┌─────────────────────┼─────────────────────┐      │
│                     │                     │                     │      │
│                     ▼                     ▼                     ▼      │
│               ┌──────────┐         ┌──────────┐         ┌──────────┐  │
│               │  users   │         │  orders  │         │ products │  │
│               │ (Python) │         │  (Go)    │         │ (Rust)   │  │
│               └────┬─────┘         └────┬─────┘         └────┬─────┘  │
│                    │                    │                    │        │
│                    ▼                    ▼                    ▼        │
│               ┌──────────┐         ┌──────────┐         ┌──────────┐  │
│               │ postgres │         │  redis   │         │ postgres │  │
│               └──────────┘         └──────────┘         └──────────┘  │
│                                                                         │
│  Legend: ──▶ HTTP  ─·─▶ TCP  Color: Green=Healthy  Red=Issues          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Automatic SLO Tracking

Coroot calculates SLOs for every service without configuration:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Service: api-gateway                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Availability SLO                    Latency SLO (P99)                  │
│  ┌───────────────────────────┐      ┌───────────────────────────┐      │
│  │ Target: 99.9%             │      │ Target: 100ms             │      │
│  │ Current: 99.95%    ✓     │      │ Current: 87ms      ✓     │      │
│  │ Budget remaining: 4h 32m  │      │ Budget remaining: 2h 15m  │      │
│  └───────────────────────────┘      └───────────────────────────┘      │
│                                                                         │
│  Error Rate (Last Hour)              Request Rate                       │
│  ┌───────────────────────────┐      ┌───────────────────────────┐      │
│  │    0.05%                  │      │    1,245 req/s            │      │
│  │ ▁▂▁▁▁▃▂▁▁▁▁▁▂▁▁▁▁▁▁     │      │ ▄▅▆▇▆▅▄▅▆▇▆▅▄▅▆▇▆▅▄     │      │
│  └───────────────────────────┘      └───────────────────────────┘      │
│                                                                         │
│  Latency Distribution                                                   │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │ P50: 12ms  P90: 45ms  P95: 67ms  P99: 87ms  Max: 234ms       │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Zero-Instrumentation Distributed Tracing

Coroot captures distributed traces without any SDK:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Trace: 7a8b9c0d-1234-5678-abcd-ef0123456789                             │
│ Duration: 234ms                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ frontend      │██████████████░░░░░░░░░░░░░░░░░░│ 45ms (GET /checkout)  │
│               └─────┬────────────────────────────                       │
│                     │                                                   │
│ api-gateway         │██████████████████████████│ 180ms                 │
│                     └──────┬─────────┬─────────                         │
│                            │         │                                  │
│ user-service               │█████░░░│ 23ms (validate token)            │
│                            │                                            │
│ order-service                       │████████████████│ 89ms            │
│                                     └──────┬─────────                   │
│                                            │                            │
│ postgres                                   │████████│ 34ms (SELECT)    │
│                                                                         │
│ Timeline: 0ms     50ms     100ms    150ms    200ms    234ms            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Continuous Profiling

Built-in CPU and memory profiling without code changes:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CPU Profile: api-gateway (last 15 minutes)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Function                                        CPU %    Self %        │
│  ├── main.handleRequest                          45.2%    2.1%         │
│  │   ├── json.Unmarshal                          18.7%   18.7%         │
│  │   ├── db.Query                                15.3%    1.2%         │
│  │   │   └── net.(*conn).Read                    14.1%   14.1%         │
│  │   └── http.ResponseWriter.Write                8.9%    8.9%         │
│  └── runtime.gcBgMarkWorker                       5.4%    5.4%         │
│                                                                         │
│  Top CPU consumers: json.Unmarshal (18.7%), net.Read (14.1%)           │
│  Recommendation: Consider using faster JSON library (jsoniter, sonic)   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Network-Level Insights

eBPF captures TCP-level details invisible to application metrics:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Network Health: api-gateway → postgres                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Connection Stats (Last Hour)                                           │
│  ├── Active connections: 25                                             │
│  ├── New connections/s: 12.4                                            │
│  ├── Failed connections: 3                                              │
│  └── Connection pool efficiency: 98.2%                                  │
│                                                                         │
│  TCP Quality Metrics                                                    │
│  ├── Round-trip time (P99): 1.2ms                                      │
│  ├── Retransmission rate: 0.02%                                        │
│  ├── Zero-window events: 0                                              │
│  └── Connection resets: 2                                               │
│                                                                         │
│  ⚠ Alert: 3 failed connections detected                                │
│    Cause: Connection timeout to postgres:5432                           │
│    Likely reason: Connection pool exhausted                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4. Log Analysis

Coroot correlates logs with metrics and traces:

```bash
# Logs are automatically associated with traces
# Example log correlation in Coroot:

Trace: 7a8b9c0d... → Related Logs:
├── 14:23:01.123 [INFO]  api-gateway: Processing checkout request
├── 14:23:01.145 [INFO]  user-service: Token validated for user_id=12345
├── 14:23:01.189 [INFO]  order-service: Creating order
├── 14:23:01.223 [ERROR] order-service: Payment failed: insufficient funds
└── 14:23:01.234 [INFO]  api-gateway: Returning 402 Payment Required
```

---

## Coroot vs Traditional Observability

### Comparison Matrix

| Feature | Coroot | Traditional Stack | APM (Datadog, etc.) |
|---------|--------|-------------------|---------------------|
| **Setup time** | Minutes | Hours/days | Hours |
| **Code changes** | None | Extensive | SDK integration |
| **Language support** | All (eBPF) | Per-language | Per-language |
| **Legacy app support** | Full | Limited | Limited |
| **Distributed tracing** | Automatic | Manual SDK | Manual SDK |
| **Continuous profiling** | Built-in | Separate tool | Add-on ($$$) |
| **Cost** | Open source | Open source | $$$$$ |
| **Network visibility** | TCP-level | Application-level | Application-level |

### When to Choose Coroot

```
Choose Coroot when:
├── You have many services with no instrumentation
├── You can't modify application code (legacy, third-party)
├── You want fast time-to-value (minutes, not days)
├── Budget constraints prevent commercial APM
├── You need network-level visibility (TCP, DNS)
└── You want unified metrics, traces, logs, profiles

Choose Traditional Stack when:
├── You need detailed custom metrics
├── Your kernel doesn't support eBPF/BTF
├── You have extensive existing instrumentation
└── You need very specific trace attributes
```

---

## War Story: The Mysterious Memory Leak

A fintech company was experiencing periodic OOMKills in their payment processing service. The service would run fine for hours, then suddenly get killed by Kubernetes.

**The Problem**:
- Application memory metrics (from the app itself) showed stable heap usage
- Container memory kept growing
- No memory leaks visible in code review
- Restarting the service "fixed" it temporarily

**Enter Coroot**:

They deployed Coroot without any code changes:

```
Coroot Discovery:
├── payment-service
│   ├── Memory Profile (continuous)
│   │   ├── Heap: 512MB (stable)
│   │   ├── Stack: 24MB (stable)
│   │   └── Off-heap: Growing!
│   │       └── Native memory: CGO allocations not freed
│   │
│   └── Memory Timeline
│       ├── Container RSS: 512MB → 2.1GB over 6 hours
│       └── Heap stays at 512MB
│       └── Difference: Native memory leak
```

**The Discovery**:

Coroot's continuous profiling showed that the Go service was using CGO to call a C library for encryption. The C library had a memory leak—it allocated buffers that were never freed.

```
CPU Profile over time:
├── crypto.Encrypt (C library)
│   └── malloc() calls: increasing
│       └── free() calls: NOT matching
│
Memory allocation flame graph:
└── libcrypto.so → EVP_EncryptInit → malloc (no matching free)
```

**The Fix**: Updated the crypto library to the latest version which fixed the leak.

### Financial Impact

| Category | Before Coroot | With Coroot | Impact |
|----------|---------------|-------------|--------|
| **OOMKill incidents/month** | 12 | 0 | -100% |
| **Incident cost (avg $8K each)** | $96,000/year | $0 | $96,000 saved |
| **Engineering time investigating** | 6 hrs/incident × 12 | 2 hrs (one-time) | $10,800 saved |
| **Customer churn from instability** | 3%/year | 0.5%/year | $42,000 ARR saved |
| **APM license (couldn't see issue)** | $18,000/year | $0 (open source) | $18,000 saved |
| **ClickHouse hosting** | $0 | $2,400/year | -$2,400 |
| **Total Annual Impact** | | | **$164,400** |

The CTO's post-mortem summary: "We paid $18,000/year for an APM that literally couldn't see this bug. Coroot—which is free—found it in 15 minutes. The memory leak had been causing OOMKills for 8 months."

**The Lesson**: Application-level metrics only showed the Go heap. Coroot's eBPF-based profiling saw the whole container memory, including native allocations. Traditional APM would have missed this entirely.

---

## Advanced Configuration

### Custom SLO Definitions

```yaml
# coroot-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coroot-config
  namespace: coroot
data:
  config.yaml: |
    slo:
      # Custom availability targets
      availability:
        default: 99.9
        overrides:
          - service: "payment-*"
            target: 99.99
          - service: "internal-*"
            target: 99.0

      # Custom latency targets
      latency:
        default:
          p99: 100ms
        overrides:
          - service: "api-gateway"
            p99: 50ms
          - service: "batch-processor"
            p99: 5s
```

### Alerting Configuration

```yaml
# Alert rules
apiVersion: v1
kind: ConfigMap
metadata:
  name: coroot-alerts
  namespace: coroot
data:
  alerts.yaml: |
    alerts:
      - name: SLO Breach
        condition: slo.availability < target
        for: 5m
        severity: critical

      - name: High Error Rate
        condition: error_rate > 1%
        for: 5m
        severity: warning

      - name: Latency Degradation
        condition: latency.p99 > baseline * 2
        for: 10m
        severity: warning

      - name: Memory Pressure
        condition: container.memory.usage > 90%
        for: 5m
        severity: warning
```

### Integration with Prometheus

```yaml
# Use existing Prometheus as data source
helm upgrade coroot coroot/coroot \
  --namespace coroot \
  --set prometheus.enabled=false \
  --set prometheus.external.url=http://prometheus.monitoring:9090
```

### Integration with OpenTelemetry

```yaml
# Export Coroot data to OTel Collector
helm upgrade coroot coroot/coroot \
  --namespace coroot \
  --set opentelemetry.enabled=true \
  --set opentelemetry.endpoint=http://otel-collector:4317
```

---

## Production Best Practices

### 1. Resource Allocation

```yaml
# Recommended resources for node agent
resources:
  coroot-node-agent:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

  # For Coroot server (scales with cluster size)
  coroot:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi

  # ClickHouse (scales with retention)
  clickhouse:
    requests:
      cpu: 1000m
      memory: 4Gi
    limits:
      cpu: 4000m
      memory: 16Gi
```

### 2. Data Retention

```yaml
# Configure retention in ClickHouse
clickhouse:
  retention:
    metrics: 30d
    traces: 7d
    logs: 14d
    profiles: 3d
```

### 3. High Availability

```yaml
# HA setup
helm install coroot coroot/coroot \
  --namespace coroot \
  --set replicas=3 \
  --set clickhouse.replicas=3 \
  --set clickhouse.zookeeper.enabled=true
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Kernel without BTF | Node agent fails to start | Use kernel 5.4+ or install BTF manually |
| Insufficient ClickHouse storage | Data loss after a few days | Size storage for your retention needs |
| Not setting SLO targets | Default targets may not match your needs | Configure custom SLOs per service |
| Ignoring network metrics | Missing TCP-level issues | Review network tab for retransmits, timeouts |
| Running on all nodes | Overhead on system nodes | Use nodeSelector to exclude control plane |
| Not using labels | Hard to find services | Ensure pods have meaningful labels |

---

## Troubleshooting

### Node Agent Not Starting

```bash
# Check logs
kubectl logs -n coroot -l app.kubernetes.io/name=coroot-node-agent

# Common issues:
# 1. BTF not available
# Error: "failed to load BTF from /sys/kernel/btf/vmlinux"
# Fix: Upgrade kernel or install BTF

# 2. Insufficient permissions
# Error: "operation not permitted"
# Fix: Ensure privileged: true in securityContext
```

### No Data in Dashboard

```bash
# Verify node agent is collecting
kubectl exec -n coroot -it $(kubectl get pod -n coroot -l app.kubernetes.io/name=coroot-node-agent -o jsonpath='{.items[0].metadata.name}') -- /coroot-node-agent --test

# Check Prometheus scraping
kubectl port-forward -n coroot svc/coroot-prometheus 9090:9090
# Visit http://localhost:9090/targets
```

### High Memory Usage

```bash
# Check ClickHouse storage
kubectl exec -n coroot clickhouse-0 -- clickhouse-client -q "SELECT table, formatReadableSize(sum(bytes)) FROM system.parts GROUP BY table"

# Reduce retention if needed
# Or increase ClickHouse resources
```

---

## Hands-On Exercise: Zero-Code Observability

**Objective**: Deploy Coroot and get full observability for a demo application without any instrumentation.

### Setup

```bash
# Create demo namespace
kubectl create namespace demo

# Deploy a sample application (no instrumentation)
kubectl apply -n demo -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  selector:
    app: frontend
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: hashicorp/http-echo
        args: ["-text=Hello from API"]
        ports:
        - containerPort: 5678
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
  - port: 5678
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: database
spec:
  selector:
    app: database
  ports:
  - port: 6379
EOF

# Wait for pods
kubectl wait --for=condition=ready pod -l app=frontend -n demo --timeout=60s
kubectl wait --for=condition=ready pod -l app=api -n demo --timeout=60s
kubectl wait --for=condition=ready pod -l app=database -n demo --timeout=60s
```

### Task 1: Install Coroot

```bash
# Add Helm repo
helm repo add coroot https://coroot.github.io/helm-charts
helm repo update

# Install Coroot
kubectl create namespace coroot
helm install coroot coroot/coroot \
  --namespace coroot \
  --set clickhouse.enabled=true \
  --set clickhouse.persistence.size=10Gi

# Install node agent
helm install coroot-node-agent coroot/coroot-node-agent \
  --namespace coroot \
  --set coroot.url=http://coroot.coroot:8080

# Wait for Coroot
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=coroot -n coroot --timeout=120s
```

### Task 2: Generate Traffic

```bash
# In a separate terminal, generate traffic
kubectl run traffic-generator --rm -i --tty --image=curlimages/curl -- sh -c '
while true; do
  curl -s http://frontend.demo.svc.cluster.local
  curl -s http://api.demo.svc.cluster.local:5678
  sleep 0.5
done
'
```

### Task 3: Explore the Dashboard

```bash
# Port-forward Coroot UI
kubectl port-forward -n coroot svc/coroot 8080:8080

# Open http://localhost:8080
```

In the dashboard:
1. Navigate to the **Service Map** - you should see frontend, api, database
2. Click on any service to see:
   - Automatic SLO metrics
   - Request rate and error rate
   - Latency percentiles
3. Go to **Traces** - see requests flowing through services
4. Check **Logs** - correlated with traces

### Task 4: Verify Auto-Discovery

```bash
# Services discovered by Coroot (no configuration needed)
# Expected:
# - frontend (2 pods)
# - api (3 pods)
# - database (1 pod)
# - Dependencies automatically mapped
```

### Task 5: Simulate an Issue

```bash
# Scale down api to cause errors
kubectl scale deployment api -n demo --replicas=0

# Watch the dashboard - you should see:
# - Error rate spike
# - SLO breach
# - Service map showing api in red

# Scale back up
kubectl scale deployment api -n demo --replicas=3
```

### Success Criteria

- [ ] Coroot deployed and running
- [ ] All demo services discovered automatically
- [ ] Service map shows correct dependencies
- [ ] SLO metrics displayed for each service
- [ ] Traces show request flow between services
- [ ] Issue simulation detected in dashboard

### Cleanup

```bash
kubectl delete namespace demo
kubectl delete namespace coroot
```

---

## Quiz

### Question 1
What technology does Coroot use to capture observability data without code changes?

<details>
<summary>Show Answer</summary>

**eBPF (Extended Berkeley Packet Filter)**

Coroot uses eBPF programs running in the kernel to observe all network traffic, system calls, and resource usage. This allows capturing metrics, traces, and profiles without modifying application code.
</details>

### Question 2
What are the main components of a Coroot deployment?

<details>
<summary>Show Answer</summary>

**Coroot Server, coroot-node-agent (DaemonSet), and ClickHouse**

- coroot-node-agent runs on every node to collect eBPF data
- Coroot Server processes data and serves the UI
- ClickHouse stores metrics, traces, logs, and profiles
</details>

### Question 3
How does Coroot provide distributed tracing without SDK integration?

<details>
<summary>Show Answer</summary>

**By capturing trace context headers at the kernel level**

eBPF intercepts HTTP requests and extracts trace context headers (like traceparent from W3C Trace Context). This allows correlating requests across services without application changes.
</details>

### Question 4
What kernel requirement must be met for Coroot to work?

<details>
<summary>Show Answer</summary>

**BTF (BPF Type Format) support, typically kernel 4.16+ (5.4+ recommended)**

BTF enables Coroot's eBPF programs to work across different kernel versions without recompilation. Most modern Linux distributions include BTF support.
</details>

### Question 5
What type of metrics can Coroot capture that traditional APM tools miss?

<details>
<summary>Show Answer</summary>

**TCP-level network metrics like retransmits, RTT, connection failures, and DNS resolution times**

Because Coroot observes at the kernel level, it sees network issues invisible to application-level metrics, such as packet retransmissions and connection timeouts.
</details>

### Question 6
How does Coroot automatically calculate SLOs?

<details>
<summary>Show Answer</summary>

**By measuring request success rate for availability and latency percentiles from observed traffic**

Coroot calculates availability (% of successful requests) and latency SLOs (P50, P95, P99) automatically from traffic patterns, without manual configuration.
</details>

### Question 7
What is the advantage of Coroot's continuous profiling feature?

<details>
<summary>Show Answer</summary>

**It shows CPU and memory hotspots in production without code changes or performance impact**

Unlike traditional profilers that require instrumentation and add overhead, Coroot's eBPF-based profiling runs continuously with minimal impact, catching issues in production that don't reproduce in testing.
</details>

### Question 8
When would you NOT choose Coroot over traditional observability?

<details>
<summary>Show Answer</summary>

**When you need detailed custom metrics or your kernel doesn't support eBPF/BTF**

If you need highly specific business metrics, custom trace attributes, or run on older kernels without BTF support, traditional instrumentation may be necessary.
</details>

---

## Key Takeaways

1. **Zero instrumentation** - Coroot uses eBPF to observe applications without code changes
2. **Automatic service discovery** - Services and dependencies detected from actual traffic
3. **Built-in distributed tracing** - Trace context captured at kernel level
4. **Continuous profiling** - CPU and memory profiling without SDK integration
5. **Network-level visibility** - TCP metrics, DNS, retransmits invisible to app metrics
6. **Automatic SLO tracking** - Availability and latency calculated for every service
7. **Unified observability** - Metrics, traces, logs, profiles in one tool
8. **Open source** - Apache 2.0 license, no vendor lock-in
9. **Fast time-to-value** - Minutes to full observability vs days with traditional stacks
10. **Legacy support** - Works with any application you can't or won't modify

---

## Further Reading

- [Coroot Documentation](https://coroot.com/docs/) - Official documentation
- [Coroot GitHub](https://github.com/coroot/coroot) - Source code and issues
- [eBPF.io](https://ebpf.io/) - Understanding the underlying technology
- [Coroot Blog](https://coroot.com/blog/) - Technical deep-dives and use cases

---

## Next Module

Continue to [Module 2.1: ArgoCD](../../cicd-delivery/gitops-deployments/module-2.1-argocd/) for GitOps continuous delivery, or explore [Module 1.6: Pixie](../module-1.6-pixie/) to compare another eBPF-based observability tool.

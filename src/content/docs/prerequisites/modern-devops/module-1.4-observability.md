---
title: "Module 1.4: Observability Fundamentals"
slug: prerequisites/modern-devops/module-1.4-observability
sidebar:
  order: 5
---
> **Complexity**: `[MEDIUM]` - Critical operational skill
>
> **Time to Complete**: 35-40 minutes
>
> **Prerequisites**: Basic understanding of distributed systems

---

## Why This Module Matters

"Is the system working?" seems like a simple question. In distributed systems like Kubernetes, it's not. Applications span multiple pods, nodes, and services. Observability gives you the ability to understand what's happening inside your system based on its external outputs. Without it, you're flying blind.

---

## What is Observability?

Observability is **the ability to understand the internal state of a system by examining its outputs**.

```
┌─────────────────────────────────────────────────────────────┐
│              MONITORING vs OBSERVABILITY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MONITORING (Traditional)                                   │
│  "Is it up? Is it slow?"                                   │
│  - Predefined dashboards                                   │
│  - Known failure modes                                     │
│  - Reactive: alert when threshold breached                 │
│                                                             │
│  OBSERVABILITY (Modern)                                     │
│  "Why is it slow? What's different?"                       │
│  - Explore arbitrary questions                             │
│  - Discover unknown failure modes                          │
│  - Proactive: understand before it breaks                  │
│                                                             │
│  Key insight: Monitoring tells you WHAT is wrong           │
│               Observability tells you WHY                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Three Pillars

```
┌─────────────────────────────────────────────────────────────┐
│              THREE PILLARS OF OBSERVABILITY                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   METRICS   │  │    LOGS     │  │   TRACES    │        │
│  │             │  │             │  │             │        │
│  │  Numbers    │  │  Events     │  │  Requests   │        │
│  │  over time  │  │  with text  │  │  across     │        │
│  │             │  │             │  │  services   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         ▼                ▼                ▼                │
│  "CPU at 90%"    "Error: DB      "Request took           │
│  "5xx errors     connection      300ms: 150ms in         │
│   increasing"    failed"         service A, 150ms        │
│                                  in service B"           │
│                                                             │
│  WHEN to use:    WHEN to use:    WHEN to use:            │
│  - Dashboards    - Debugging     - Performance           │
│  - Alerting      - Auditing      - Dependencies          │
│  - Trends        - Security      - Bottlenecks           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Metrics

Metrics are **numeric measurements collected over time**.

### Types of Metrics

```
Counter (always increases):
  - http_requests_total
  - errors_total
  - bytes_sent_total

Gauge (can go up or down):
  - temperature_celsius
  - memory_usage_bytes
  - active_connections

Histogram (distribution):
  - request_duration_seconds
  - Shows: p50, p90, p99 latencies
```

### Prometheus (The Standard)

```yaml
# Prometheus collects metrics by scraping endpoints
# Your app exposes metrics at /metrics

# Example metrics endpoint output:
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api",status="200"} 1234
http_requests_total{method="POST",path="/api",status="500"} 12

# HELP request_duration_seconds Request latency
# TYPE request_duration_seconds histogram
request_duration_seconds_bucket{le="0.1"} 800
request_duration_seconds_bucket{le="0.5"} 1100
request_duration_seconds_bucket{le="1.0"} 1200
```

### PromQL (Query Language)

```promql
# Rate of requests per second over 5 minutes
rate(http_requests_total[5m])

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))

# 99th percentile latency
histogram_quantile(0.99, rate(request_duration_seconds_bucket[5m]))
```

---

## Logs

Logs are **timestamped records of discrete events**.

### Structured vs Unstructured

```
UNSTRUCTURED (hard to parse):
2024-01-15 10:23:45 ERROR Failed to connect to database: connection refused

STRUCTURED (JSON, easy to query):
{
  "timestamp": "2024-01-15T10:23:45Z",
  "level": "error",
  "message": "Failed to connect to database",
  "error": "connection refused",
  "service": "api",
  "pod": "api-7d8f9-abc12",
  "trace_id": "abc123def456"
}
```

### Log Levels

| Level | When to Use |
|-------|-------------|
| DEBUG | Detailed info for debugging (disabled in prod) |
| INFO | Normal operations, milestones |
| WARN | Something unexpected, but recoverable |
| ERROR | Something failed, needs attention |
| FATAL | Application cannot continue |

### Kubernetes Logging

```bash
# View logs
kubectl logs pod-name
kubectl logs pod-name -c container-name  # Multi-container
kubectl logs pod-name --previous         # Previous crash
kubectl logs -f pod-name                 # Follow (tail)
kubectl logs -l app=nginx                # By label

# In production, logs go to a central system
# Common stacks:
# - ELK (Elasticsearch, Logstash, Kibana)
# - EFK (Elasticsearch, Fluentd, Kibana)
# - Loki + Grafana
```

---

## Traces

Traces **follow a request across multiple services**.

```
┌─────────────────────────────────────────────────────────────┐
│              DISTRIBUTED TRACE                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Request (trace_id: abc123)                           │
│  Total time: 500ms                                         │
│                                                             │
│  ├─ Frontend (100ms)                                       │
│  │   └─ Render page                                        │
│  │                                                          │
│  ├─ API Gateway (50ms)                                     │
│  │   └─ Auth check                                         │
│  │                                                          │
│  ├─ User Service (150ms)                                   │
│  │   ├─ Get user data (50ms)                              │
│  │   └─ Database query (100ms)  ← Slow!                   │
│  │                                                          │
│  └─ Order Service (200ms)                                  │
│      ├─ Fetch orders (50ms)                               │
│      └─ Cache lookup (150ms)   ← Also slow!               │
│                                                             │
│  Traces answer: "Why is this request slow?"               │
│  Answer: DB query in User Service + Cache in Orders       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Term | Definition |
|------|------------|
| Trace | Complete journey of a request |
| Span | Single operation within a trace |
| Trace ID | Unique identifier for the trace |
| Span ID | Unique identifier for a span |
| Parent ID | Links child spans to parents |

### Tracing Tools

- **Jaeger**: CNCF graduated, popular for Kubernetes
- **Zipkin**: Twitter-originated, mature
- **OpenTelemetry**: Standard for instrumentation

---

## The Observability Stack

```
┌─────────────────────────────────────────────────────────────┐
│              TYPICAL KUBERNETES OBSERVABILITY STACK         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  COLLECTION                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Prometheus     Fluentd/      OpenTelemetry         │   │
│  │  (metrics)      Fluent Bit    (traces)              │   │
│  │                 (logs)                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  STORAGE                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Prometheus    Elasticsearch   Jaeger/              │   │
│  │  (time series) or Loki         Tempo                │   │
│  │                (logs)          (traces)             │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  VISUALIZATION                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   GRAFANA                            │   │
│  │  - Dashboards for all three pillars                 │   │
│  │  - Unified view                                     │   │
│  │  - Alerting                                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Kubernetes-Native Metrics

```bash
# First, install metrics-server (kind clusters don't include it by default)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# For kind/local clusters, patch it to work without TLS verification:
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
# Wait ~60 seconds for metrics to start collecting, then:
kubectl top nodes
kubectl top pods

# Resource usage
NAME          CPU(cores)   MEMORY(bytes)
node-1        250m         1024Mi
node-2        100m         512Mi
```

### Key Kubernetes Metrics

| Metric | What It Tells You |
|--------|-------------------|
| `container_cpu_usage_seconds_total` | CPU consumption |
| `container_memory_usage_bytes` | Memory consumption |
| `kube_pod_status_phase` | Pod lifecycle state |
| `kube_deployment_status_replicas_available` | Healthy replicas |
| `apiserver_request_duration_seconds` | API server latency |

---

## Alerting

```yaml
# Prometheus AlertManager rule
groups:
  - name: kubernetes
    rules:
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pod {{ $labels.pod }} is crash looping"

      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate above 5%"
```

### Alert Best Practices

```
Good alerts:
✓ Actionable (someone can fix it)
✓ Urgent (needs immediate attention)
✓ Not noisy (low false positives)

Bad alerts:
✗ "CPU at 80%" (so what?)
✗ Every pod restart (expected sometimes)
✗ Alert fatigue = ignored alerts
```

---

## Golden Signals

Google's SRE book defines four golden signals:

```
┌─────────────────────────────────────────────────────────────┐
│              FOUR GOLDEN SIGNALS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. LATENCY                                                │
│     Time to service a request                              │
│     "How long do requests take?"                           │
│                                                             │
│  2. TRAFFIC                                                │
│     Demand on your system                                  │
│     "How many requests per second?"                        │
│                                                             │
│  3. ERRORS                                                 │
│     Rate of failed requests                                │
│     "What percentage of requests fail?"                    │
│                                                             │
│  4. SATURATION                                             │
│     How "full" your service is                            │
│     "How close to capacity?"                               │
│                                                             │
│  If you track these four things well, you'll catch        │
│  most problems before users notice.                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Netflix engineers** can see every request's journey across hundreds of microservices. Their observability system processes billions of events per second.

- **The term "observability"** comes from control theory (1960s). Rudolf E. Kálmán defined a system as "observable" if its internal state can be inferred from its outputs.

- **Alert fatigue is real.** Studies show that when teams receive too many alerts, they start ignoring them. Some teams have over 90% of alerts ignored.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Unstructured logs | Can't query or aggregate | Use JSON logging |
| No trace correlation | Can't debug distributed issues | Add trace IDs everywhere |
| Too many alerts | Alert fatigue | Alert on symptoms, not causes |
| Dashboard overload | Information paralysis | Golden signals dashboard |
| No retention policy | Storage explosion | Define TTLs for each data type |

---

## Quiz

1. **What's the difference between metrics, logs, and traces?**
   <details>
   <summary>Answer</summary>
   Metrics: Numeric measurements over time (counters, gauges). Logs: Timestamped text records of discrete events. Traces: Records of requests as they flow through distributed services.
   </details>

2. **What are the four golden signals?**
   <details>
   <summary>Answer</summary>
   Latency (request time), Traffic (requests per second), Errors (failure rate), and Saturation (resource utilization). These are the key indicators of system health.
   </details>

3. **Why use structured logging?**
   <details>
   <summary>Answer</summary>
   Structured logs (JSON) can be parsed and queried programmatically. You can aggregate, filter, and alert on specific fields. Unstructured logs require regex parsing and are error-prone.
   </details>

4. **When would you use traces instead of logs?**
   <details>
   <summary>Answer</summary>
   When debugging performance issues across multiple services. Traces show the complete journey of a request, including time spent in each service. Logs only show individual service events.
   </details>

---

## Hands-On Exercise

**Task**: Explore Kubernetes observability basics.

```bash
# 1. Deploy a sample application
kubectl create deployment web --image=nginx:1.25 --replicas=3
kubectl expose deployment web --port=80

# 2. View logs
kubectl logs -l app=web --all-containers
kubectl logs -l app=web -f  # Follow logs

# 3. Check resource usage
# Install metrics-server first (if not already done):
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
# Wait ~60 seconds, then:
kubectl top pods
kubectl top nodes

# 4. Simulate a problem
# Scale down to 0 (break it)
kubectl scale deployment web --replicas=0

# Check events (kubernetes logs)
kubectl get events --sort-by='.lastTimestamp'

# 5. View pod status (basic metrics)
kubectl get pods -o wide
kubectl describe pod -l app=web

# 6. Generate some logs
kubectl scale deployment web --replicas=1
kubectl exec -it $(kubectl get pod -l app=web -o name | head -1) -- \
  curl -s localhost > /dev/null

# View nginx access logs
kubectl logs -l app=web | tail

# 7. Explore with JSONPath (metrics-like queries)
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# 8. Cleanup
kubectl delete deployment web
kubectl delete service web
```

**Success criteria**: Understand logs, events, and basic resource monitoring.

---

## Summary

**Observability** is about understanding your system:

**Three pillars**:
- **Metrics**: Numbers over time (Prometheus)
- **Logs**: Event records (ELK, Loki)
- **Traces**: Request journeys (Jaeger)

**Golden signals** (what to monitor):
- Latency
- Traffic
- Errors
- Saturation

**Kubernetes specifics**:
- `kubectl logs` for pod logs
- `kubectl top` for resource metrics
- Events for cluster activity
- Prometheus for comprehensive metrics

**Key insight**: Observability is not just monitoring. It's the ability to ask arbitrary questions about your system and get answers.

---

## Next Module

[Module 5: Platform Engineering Concepts](../module-1.5-platform-engineering/) - Building internal developer platforms.

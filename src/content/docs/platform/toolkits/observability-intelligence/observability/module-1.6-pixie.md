---
title: "Module 1.6: Pixie - Zero-Instrumentation Observability"
slug: platform/toolkits/observability-intelligence/observability/module-1.6-pixie
sidebar:
  order: 7
---
## Complexity: [MEDIUM]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 1.1 (Prometheus), Module 1.2 (OpenTelemetry basics), Basic Kubernetes knowledge
**Learning Objectives**:
- Understand eBPF-based auto-instrumentation
- Deploy Pixie to a Kubernetes cluster
- Use PxL (Pixie Language) to query telemetry data
- Debug production issues without deploying any instrumentation code

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Pixie for instant Kubernetes observability using eBPF-based auto-instrumentation**
- **Implement PxL scripts for querying HTTP traffic, DNS requests, and database queries without code changes**
- **Configure Pixie's data retention and export pipelines for long-term observability storage**
- **Evaluate Pixie's zero-instrumentation approach against traditional APM for rapid debugging workflows**


## Why This Module Matters

Traditional observability requires you to **modify your code**: add metrics libraries, instrument spans, configure log formats. This takes weeks of engineering effort and often means you can't debug production issues you didn't anticipate instrumenting.

**Pixie changes this equation entirely.**

Using eBPF (extended Berkeley Packet Filter), Pixie captures telemetry data directly from the Linux kernel—no code changes, no sidecars, no redeployments. It sees every HTTP request, every SQL query, every DNS lookup happening in your cluster. You get observability as a **platform capability**, not an application responsibility.

> "It's like having X-ray vision for your cluster. You see everything happening at the kernel level, without asking applications to cooperate."

---

## Did You Know?

- Pixie can capture **full request/response bodies** including HTTP, MySQL, PostgreSQL, and gRPC—without any code changes
- eBPF runs in the Linux kernel, so Pixie sees traffic that never reaches application-level instrumentation
- Pixie stores data **locally in the cluster** using only 5% of node memory, meaning sensitive data never leaves your infrastructure
- The PxL query language was designed to be learnable in under an hour—it's Python-like with DataFrames
- Pixie was acquired by New Relic but remains **fully open-source** under Apache 2.0

---

## The eBPF Revolution

### What is eBPF?

eBPF allows you to run sandboxed programs inside the Linux kernel without changing kernel source code or loading kernel modules:

```
┌─────────────────────────────────────────────────────────┐
│                    User Space                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  App A   │  │  App B   │  │  App C   │             │
│  │  (no     │  │  (no     │  │  (no     │             │
│  │  changes)│  │  changes)│  │  changes)│             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │             │                    │
├───────┴─────────────┴─────────────┴────────────────────┤
│                    Kernel Space                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                    eBPF Programs                  │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │  │
│  │  │ Network │  │  Syscall│  │ Schedule│          │  │
│  │  │ Probes  │  │  Probes │  │  Probes │          │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘          │  │
│  │       └──────────┬─┴───────────┘                │  │
│  │                  ▼                               │  │
│  │         ┌────────────────┐                      │  │
│  │         │  eBPF Maps     │ ◄── Data collection  │  │
│  │         └───────┬────────┘                      │  │
│  └─────────────────┴────────────────────────────────┘  │
│                        │                               │
│                        ▼                               │
│              ┌──────────────────┐                      │
│              │   Pixie Agent    │ ◄── Reads eBPF maps │
│              │   (per node)     │                      │
│              └──────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

### Why eBPF for Observability?

| Traditional Approach | eBPF Approach |
|---------------------|---------------|
| Modify application code | No code changes |
| Deploy new versions | Immediate visibility |
| SDK/library overhead | Near-zero overhead (~1% CPU) |
| Application-level only | Kernel-level visibility |
| Miss uninstrumented services | See everything |
| Data leaves cluster | Data stays local |

---

## Pixie Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                        pl namespace                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │
│  │  │  Vizier     │  │  Cloud      │  │   NATS               │  │   │
│  │  │  (Query     │  │  Connector  │  │   (Message bus)      │  │   │
│  │  │   Engine)   │  │  (optional) │  │                      │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │    Node 1     │  │    Node 2     │  │    Node 3     │          │
│  │  ┌─────────┐  │  │  ┌─────────┐  │  │  ┌─────────┐  │          │
│  │  │  PEM    │  │  │  │  PEM    │  │  │  │  PEM    │  │          │
│  │  │ (Pixie  │  │  │  │ (Pixie  │  │  │  │ (Pixie  │  │          │
│  │  │  Edge   │  │  │  │  Edge   │  │  │  │  Edge   │  │          │
│  │  │ Module) │  │  │  │ Module) │  │  │  │ Module) │  │          │
│  │  └─────────┘  │  │  └─────────┘  │  │  └─────────┘  │          │
│  │       ▲       │  │       ▲       │  │       ▲       │          │
│  │       │eBPF   │  │       │eBPF   │  │       │eBPF   │          │
│  │  ┌────┴────┐  │  │  ┌────┴────┐  │  │  ┌────┴────┐  │          │
│  │  │ Kernel  │  │  │  │ Kernel  │  │  │  │ Kernel  │  │          │
│  │  └─────────┘  │  │  └─────────┘  │  │  └─────────┘  │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Role | Description |
|-----------|------|-------------|
| **PEM** | Data collection | DaemonSet running eBPF probes on each node |
| **Vizier** | Query engine | Executes PxL scripts, aggregates data from PEMs |
| **Cloud Connector** | Optional UI | Connects to Pixie Cloud for web UI (or self-host) |
| **NATS** | Message bus | Internal communication between components |
| **Metadata Service** | K8s context | Enriches data with pod names, services, etc. |

---

## Installing Pixie

### Prerequisites

Pixie requires:
- Kubernetes 1.21+
- Linux kernel 4.14+ (5.3+ recommended for full features)
- x86_64 architecture (ARM support experimental)
- Nodes with eBPF support (most modern distributions)

### Option 1: Pixie CLI (Recommended)

```bash
# Install the Pixie CLI
bash -c "$(curl -fsSL https://withpixie.ai/install.sh)"

# Deploy Pixie to your cluster
px deploy

# The CLI will:
# 1. Check cluster compatibility
# 2. Create a Pixie account (or use existing)
# 3. Deploy all Pixie components
```

### Option 2: Helm Installation

```bash
# Add Pixie Helm repo
helm repo add pixie https://pixie-operator-charts.storage.googleapis.com
helm repo update

# Create namespace
kubectl create namespace pl

# Install Pixie operator
helm install pixie pixie/pixie-operator-chart \
  --namespace pl \
  --set deployKey=<your-deploy-key> \
  --set clusterName=my-cluster
```

### Option 3: Self-Hosted (Air-Gapped)

For environments without internet access:

```bash
# Deploy self-hosted Pixie cloud
git clone https://github.com/pixie-io/pixie.git
cd pixie

# Build and deploy (requires significant resources)
./scripts/deploy_cloud.sh

# Then deploy Vizier pointing to self-hosted cloud
px deploy --cloud_addr=<your-cloud-addr>
```

### Verify Installation

```bash
# Check Pixie status
px get viziers

# Output:
# CLUSTER_NAME  ID          STATUS   LAST_HEARTBEAT
# my-cluster    abc-123     CS_HEALTHY   2s

# Check all pods are running
kubectl get pods -n pl
```

---

## The PxL Query Language

PxL (Pixie Language) is a Python-like language for querying telemetry data:

```python
# Basic structure of a PxL script
import px

# Get HTTP events
df = px.DataFrame('http_events')

# Filter and transform
df = df[df.resp_status >= 400]  # Only errors
df.latency_ms = df.resp_latency / 1000000  # Convert to ms

# Aggregate
df = df.groupby(['service', 'req_path']).agg(
    error_count=('latency_ms', px.count),
    avg_latency=('latency_ms', px.mean),
)

# Display results
px.display(df)
```

### Key Data Sources

| DataFrame | What It Contains |
|-----------|-----------------|
| `http_events` | All HTTP requests/responses with full headers |
| `mysql_events` | MySQL queries with response times |
| `pgsql_events` | PostgreSQL queries with timing |
| `dns_events` | DNS lookups and resolutions |
| `conn_stats` | TCP connection statistics |
| `process_stats` | CPU, memory per process |
| `network_stats` | Network I/O per pod |

---

## Practical Use Cases

### 1. Find Slow Endpoints (No Instrumentation Needed)

```python
import px

# Get all HTTP requests from the last 5 minutes
df = px.DataFrame('http_events', start_time='-5m')

# Calculate latency in milliseconds
df.latency_ms = df.resp_latency / 1000000

# Find the slowest endpoints
df = df.groupby(['service', 'req_path', 'req_method']).agg(
    count=('latency_ms', px.count),
    p50=('latency_ms', px.quantiles(0.5)),
    p99=('latency_ms', px.quantiles(0.99)),
    error_rate=('resp_status', lambda x: px.mean(x >= 400)),
)

# Filter to endpoints with significant traffic
df = df[df.count > 10]

# Sort by p99 latency
df = df.sort('p99', ascending=False)

px.display(df, 'Slowest Endpoints')
```

### 2. Trace a Specific Request

```python
import px

# Find requests with specific trace ID (or any header)
df = px.DataFrame('http_events', start_time='-1h')

# Filter by a specific header or path
df = df[df.req_path.contains('/api/users/123')]

# Show full request/response details
df = df[['time_', 'service', 'req_method', 'req_path',
         'req_body', 'resp_status', 'resp_body', 'resp_latency']]

px.display(df)
```

### 3. Database Query Analysis

```python
import px

# Analyze PostgreSQL queries
df = px.DataFrame('pgsql_events', start_time='-10m')

# Calculate query latency
df.latency_ms = df.resp_latency / 1000000

# Group by normalized query pattern
df = df.groupby(['service', 'req_body']).agg(
    count=('latency_ms', px.count),
    avg_latency=('latency_ms', px.mean),
    max_latency=('latency_ms', px.max),
)

# Find slow queries
df = df[df.avg_latency > 100]  # Queries averaging over 100ms
df = df.sort('avg_latency', ascending=False)

px.display(df, 'Slow PostgreSQL Queries')
```

### 4. Service Dependency Map

```python
import px

# Build service-to-service communication map
df = px.DataFrame('http_events', start_time='-5m')

# Extract source and destination services
df.source = df.ctx['pod']
df.destination = df.remote_addr

# Count connections between services
df = df.groupby(['source', 'destination']).agg(
    request_count=('latency', px.count),
    avg_latency_ms=('resp_latency', lambda x: px.mean(x) / 1000000),
    error_count=('resp_status', lambda x: px.sum(x >= 400)),
)

px.display(df, 'Service Dependencies')
```

### 5. Network Troubleshooting

```python
import px

# Find network issues - DNS failures, connection errors
df = px.DataFrame('dns_events', start_time='-5m')

# Find DNS lookup failures
df = df[df.resp_code != 0]  # Non-zero = error

df = df.groupby(['service', 'query_name']).agg(
    failure_count=('resp_code', px.count),
)

px.display(df, 'DNS Failures')
```

---

## Pixie vs Traditional APM

| Aspect | Traditional APM (Datadog, New Relic) | Pixie |
|--------|-------------------------------------|-------|
| **Setup Time** | Days to weeks (instrument each service) | Minutes (cluster-wide) |
| **Code Changes** | Required for each application | None |
| **Data Location** | Sent to vendor cloud | Stays in cluster |
| **Cost Model** | Per-host, per-span pricing | Free (open-source) |
| **Overhead** | SDK overhead varies | ~1% CPU from eBPF |
| **Protocol Support** | What you instrument | Automatic for common protocols |
| **Historical Data** | Unlimited (you pay for it) | ~24 hours on-cluster |

### When to Choose Pixie

**Pixie is ideal when:**
- You need immediate observability without code changes
- You have security/compliance requirements keeping data on-premise
- You're debugging issues in services you don't own
- You want to explore what's happening before deciding what to instrument permanently
- You're cost-conscious about observability spend

**Traditional APM is better when:**
- You need long-term historical data
- You want managed dashboards and alerting
- Your applications have custom business logic metrics
- You need distributed tracing across cloud boundaries

### The Best of Both Worlds

Many teams use Pixie alongside traditional observability:

```
┌────────────────────────────────────────────────────────────┐
│                    Observability Strategy                   │
│                                                            │
│  ┌──────────────┐     ┌──────────────┐    ┌─────────────┐ │
│  │   Pixie      │     │ OpenTelemetry│    │  Prometheus │ │
│  │   (eBPF)     │     │  (SDK)       │    │  (Metrics)  │ │
│  └──────┬───────┘     └──────┬───────┘    └──────┬──────┘ │
│         │                    │                   │        │
│         ▼                    ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Unified Observability                   │ │
│  │  - Pixie for instant debugging & exploration        │ │
│  │  - OTel for business-specific spans                  │ │
│  │  - Prometheus for long-term metrics                  │ │
│  └─────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## War Story: The Mystery of the Slow API

A fintech company's payment service was experiencing intermittent slowdowns. The traditional APM showed normal latencies. The problem appeared and disappeared randomly.

**The Investigation**:
- APM showed: Payment service processing time = 50ms
- Users reported: 3-5 second delays
- Where was the missing time?

**Enter Pixie**:

```python
# They ran this query:
import px
df = px.DataFrame('http_events', start_time='-1h')
df = df[df.req_path.contains('/payments')]
df.latency_ms = df.resp_latency / 1000000

# Added network-level visibility
df.client_pod = df.ctx['pod']
df.dns_time = df.dns_resp_latency / 1000000

px.display(df[['time_', 'client_pod', 'latency_ms', 'dns_time', 'remote_addr']])
```

**The Discovery**:
DNS lookups were timing out and falling back to secondary DNS servers. The payment service made a DNS lookup for each request to an internal fraud detection service. CoreDNS was being overwhelmed during traffic spikes.

```
Request latency breakdown:
- Application processing: 50ms (what APM saw)
- DNS lookup (primary): 3000ms timeout
- DNS lookup (secondary): 50ms
- Total user experience: 3100ms
```

**The Fix**: Added DNS caching and increased CoreDNS replicas.

**The Lesson**: Without kernel-level visibility, they would have blamed the payment service for weeks. Pixie saw what application instrumentation couldn't.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Deploying on incompatible kernel | eBPF programs fail to load | Check kernel version: `uname -r` (need 4.14+, prefer 5.3+) |
| Running on GKE Autopilot | Can't run privileged pods | Use GKE Standard or another provider |
| Expecting unlimited retention | Pixie stores ~24h on-cluster | Export important data to long-term storage |
| Querying encrypted traffic | Can't see TLS content | Deploy Pixie's SSL library support or use service mesh |
| High cardinality queries | PEM memory pressure | Aggregate data, limit result sets |
| Ignoring protocol support | Not all protocols are traced | Check supported protocols (HTTP/MySQL/PgSQL/DNS/gRPC) |

---

## Advanced: Exporting Data

### Export to Prometheus

```python
# In your PxL script, use px.export
import px

df = px.DataFrame('http_events', start_time='-1m')
df = df.groupby(['service', 'req_path']).agg(
    request_count=('resp_latency', px.count),
    latency_p99=('resp_latency', px.quantiles(0.99)),
)

# Export as Prometheus metrics
px.export(df, px.otel.Data(
    endpoint='prometheus-pushgateway:9091',
    resource={'service.name': 'pixie-export'},
))
```

### Export to OpenTelemetry

```bash
# Deploy Pixie OpenTelemetry plugin
helm upgrade pixie pixie/pixie-operator-chart \
  --namespace pl \
  --set otel.enabled=true \
  --set otel.endpoint=otel-collector:4317
```

This sends Pixie traces to any OTLP-compatible backend.

---

## Hands-On Exercise: Debug a Performance Issue with Pixie

**Objective**: Use Pixie to identify and diagnose a performance bottleneck without any application instrumentation.

### Setup

```bash
# Create a test namespace
kubectl create namespace pixie-demo

# Deploy a sample microservices application
kubectl apply -n pixie-demo -f https://raw.githubusercontent.com/pixie-io/pixie-demos/main/simple-gotracing/k8s/demo.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=demo -n pixie-demo --timeout=120s
```

### Task 1: Identify Slow Services

Using the Pixie CLI:

```bash
# Open the Pixie live view
px live

# Run the built-in service stats script
px script run px/service_stats
```

Or using a custom PxL script:

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df.latency_ms = df.resp_latency / 1000000

stats = df.groupby('service').agg(
    request_count=('latency_ms', px.count),
    avg_latency=('latency_ms', px.mean),
    p99_latency=('latency_ms', px.quantiles(0.99)),
    error_rate=('resp_status', lambda x: px.mean(x >= 400) * 100),
)

stats = stats.sort('p99_latency', ascending=False)
px.display(stats, 'Service Performance')
```

### Task 2: Find the Slow Endpoint

```python
import px

df = px.DataFrame('http_events', start_time='-5m')
df.latency_ms = df.resp_latency / 1000000

# Find the slowest endpoint
endpoints = df.groupby(['service', 'req_path', 'req_method']).agg(
    count=('latency_ms', px.count),
    avg_latency=('latency_ms', px.mean),
    max_latency=('latency_ms', px.max),
)

endpoints = endpoints[endpoints.count > 5]  # Filter noise
endpoints = endpoints.sort('avg_latency', ascending=False)

px.display(endpoints.head(10), 'Slowest Endpoints')
```

### Task 3: Analyze Database Queries

```python
import px

# Check if there are slow database queries
df = px.DataFrame('pgsql_events', start_time='-5m')
df.latency_ms = df.resp_latency / 1000000

queries = df.groupby(['service', 'req_body']).agg(
    exec_count=('latency_ms', px.count),
    avg_latency=('latency_ms', px.mean),
)

queries = queries.sort('avg_latency', ascending=False)
px.display(queries.head(10), 'Database Query Analysis')
```

### Task 4: Create a Service Map

```python
import px

df = px.DataFrame('http_events', start_time='-5m')

# Build service dependency graph
df.source_service = df.ctx['service']
df.dest_service = df.service

edges = df.groupby(['source_service', 'dest_service']).agg(
    request_count=('resp_latency', px.count),
    p50_latency=('resp_latency', lambda x: px.quantiles(x / 1000000, 0.5)),
)

px.display(edges, 'Service Map')
```

### Success Criteria

- [ ] Identified which service has the highest latency
- [ ] Found the specific endpoint causing slowness
- [ ] Discovered whether database queries are the bottleneck
- [ ] Created a service dependency map showing communication patterns
- [ ] Did all of this without deploying any instrumentation code

### Cleanup

```bash
kubectl delete namespace pixie-demo
```

---

## Quiz

### Question 1
What technology does Pixie use to capture telemetry without code changes?

<details>
<summary>Show Answer</summary>

**eBPF (extended Berkeley Packet Filter)**

eBPF allows Pixie to run sandboxed programs inside the Linux kernel that capture network traffic, syscalls, and other events without requiring any application modifications.
</details>

### Question 2
Where does Pixie store collected telemetry data by default?

<details>
<summary>Show Answer</summary>

**Locally in the Kubernetes cluster**

Pixie stores data in-cluster using approximately 5% of each node's memory. This means sensitive data never leaves your infrastructure, making it suitable for environments with strict data residency requirements.
</details>

### Question 3
What is the Pixie Edge Module (PEM)?

<details>
<summary>Show Answer</summary>

**A DaemonSet that runs on each node to collect telemetry**

The PEM is deployed as a DaemonSet, running one pod per node. It loads eBPF programs into the kernel and collects telemetry data from all pods on that node.
</details>

### Question 4
What minimum kernel version does Pixie require?

<details>
<summary>Show Answer</summary>

**Linux kernel 4.14+ (5.3+ recommended)**

Kernel 4.14 is the minimum for basic functionality, but 5.3+ is recommended for full feature support including newer eBPF capabilities.
</details>

### Question 5
Which protocols can Pixie automatically trace without instrumentation?

<details>
<summary>Show Answer</summary>

**HTTP, MySQL, PostgreSQL, DNS, gRPC, Kafka, Redis**

Pixie uses protocol-specific eBPF probes to automatically parse and trace these protocols. Encrypted traffic (TLS) requires additional configuration.
</details>

### Question 6
What is PxL and what is it used for?

<details>
<summary>Show Answer</summary>

**PxL (Pixie Language) is a Python-like query language for analyzing telemetry data**

PxL uses DataFrames similar to pandas and allows you to filter, aggregate, and analyze the telemetry data collected by Pixie.
</details>

### Question 7
How long does Pixie retain data by default?

<details>
<summary>Show Answer</summary>

**Approximately 24 hours**

Pixie is designed for real-time debugging and exploration, not long-term storage. Data is stored in memory on each node and typically retained for about 24 hours depending on available resources and data volume.
</details>

### Question 8
What is the typical CPU overhead of running Pixie?

<details>
<summary>Show Answer</summary>

**Approximately 1% CPU**

eBPF programs run very efficiently in the kernel. The typical overhead is around 1% CPU per node, making Pixie suitable for production workloads.
</details>

---

## Key Takeaways

1. **eBPF enables zero-instrumentation observability** - see everything without changing code
2. **Pixie captures data at the kernel level** - sees traffic that application APM misses
3. **Data stays in your cluster** - no privacy concerns with vendor cloud storage
4. **PxL makes querying intuitive** - Python-like syntax with DataFrames
5. **Sub-minute deployment** - instant observability for any cluster
6. **Protocol-aware tracing** - automatic parsing of HTTP, SQL, DNS, gRPC
7. **Complement, don't replace** - use alongside traditional APM
8. **Short-term by design** - export important data for long-term storage
9. **Debugging superpower** - find issues that instrumentation would miss
10. **Open-source with enterprise option** - Apache 2.0 with optional cloud UI

---

## Further Reading

- [Pixie Documentation](https://docs.px.dev/) - Official guides and reference
- [PxL Language Reference](https://docs.px.dev/reference/pxl/) - Complete PxL syntax
- [eBPF Explained](https://ebpf.io/what-is-ebpf/) - Understanding the underlying technology
- [Pixie GitHub](https://github.com/pixie-io/pixie) - Source code and examples
- [PxL Script Library](https://github.com/pixie-io/pixie/tree/main/src/pxl_scripts) - Community scripts

---

## Next Module

Continue to [Module 1.7: Hubble - Network Observability with Cilium](../module-1.7-hubble/) to learn about eBPF-based network observability and visualization.

# Module 4: Istio Observability

## Complexity: `[MEDIUM]`
## Time to Complete: 40-50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 1: Installation & Architecture](module-1-istio-installation-architecture.md) — istiod, Envoy, sidecar injection
- [Module 2: Traffic Management](module-2-istio-traffic-management.md) — VirtualService, DestinationRule, Gateway
- [Module 3: Security & Troubleshooting](module-3-istio-security-troubleshooting.md) — mTLS, AuthorizationPolicy, debugging
- Basic understanding of Prometheus metrics and distributed tracing concepts

---

## Why This Module Matters

Observability accounts for **10% of the ICA exam**. You'll be asked to configure telemetry collection, understand Istio's built-in metrics, and integrate with tools like Prometheus, Grafana, Kiali, and Jaeger. These aren't just exam topics — they're the reason most teams adopt Istio in the first place.

Without a service mesh, you'd need every development team to instrument their code with metrics, tracing headers, and structured logging. Istio gives you all three for free through the Envoy sidecar — no code changes required. The catch? You need to know how to configure, customize, and query that telemetry.

> **The Security Camera Analogy**
>
> Imagine a building with hundreds of rooms (services). Without Istio, you'd need to install cameras inside each room (application instrumentation). With Istio, you install cameras at every doorway (Envoy sidecars). You automatically see who enters, who leaves, how long they stay, and whether they were turned away. The **Telemetry API** controls what each camera records. **Prometheus** stores the footage. **Grafana** builds the dashboards. **Kiali** draws the floor plan. **Jaeger** lets you follow one person's path through every room they visited.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Configure Istio's Telemetry API v2 to control what telemetry is collected
- Understand and query Istio standard metrics (`istio_requests_total`, `istio_request_duration_milliseconds`)
- Configure Prometheus scraping for Istio metrics
- Set up distributed tracing with configurable sampling rates
- Enable and customize Envoy access logging
- Use Kiali for service mesh visualization and health monitoring
- Build Grafana dashboards for mesh, service, and workload views

---

## Did You Know?

- **Istio generates metrics with zero application code changes**: Every HTTP/gRPC/TCP request passing through an Envoy sidecar automatically emits request count, duration, and size metrics. A 200-microservice mesh gets full observability from day one.

- **Trace context propagation still requires application help**: While Envoy generates spans automatically, your application must forward trace headers (`x-request-id`, `x-b3-traceid`, etc.) between inbound and outbound requests. Without this, traces break into disconnected fragments.

- **Kiali can detect misconfigurations that `istioctl analyze` misses**: Kiali validates your mesh at runtime — it can spot services with missing sidecars, traffic flowing to unexpected destinations, and mTLS inconsistencies by watching actual traffic patterns.

---

## 1. Istio Telemetry API v2

The Telemetry API (introduced in Istio 1.12, stable since 1.18) is the single control point for all observability configuration. It replaces the older `EnvoyFilter`-based approach and the deprecated Mixer component.

### How Telemetry Works

```
┌──────────────────────────────────────────────────────────┐
│  Telemetry Resource (CRD)                                │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐     │
│  │ Metrics  │   │ Tracing  │   │ Access Logging   │     │
│  │          │   │          │   │                  │     │
│  │ Enable/  │   │ Sampling │   │ Envoy format /  │     │
│  │ Disable  │   │ rate     │   │ custom filters  │     │
│  │ Override │   │ provider │   │ provider        │     │
│  └──────────┘   └──────────┘   └──────────────────┘     │
│                                                          │
│  Applied at: mesh-wide → namespace → workload            │
└──────────────────────────────────────────────────────────┘
```

The Telemetry API has three pillars: **metrics**, **tracing**, and **access logging**. Each can be configured independently at three scopes:

| Scope | Where to apply | Example |
|-------|---------------|---------|
| **Mesh-wide** | `istio-system` namespace, no selector | Default for all workloads |
| **Namespace** | Target namespace, no selector | Override for a specific namespace |
| **Workload** | Target namespace + `selector` | Override for specific pods |

More specific scopes override broader ones. A workload-level Telemetry overrides namespace-level, which overrides mesh-wide.

### Mesh-Wide Telemetry Configuration

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: mesh-default
  namespace: istio-system        # mesh-wide scope
spec:
  # Enable metrics for Prometheus
  metrics:
    - providers:
        - name: prometheus
      overrides:
        - match:
            metric: ALL_METRICS
            mode: CLIENT_AND_SERVER
          tagOverrides:
            request_protocol:
              operation: UPSERT
              value: "request.protocol"
  # Enable tracing with 1% sampling
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 1.0
  # Enable access logging
  accessLogging:
    - providers:
        - name: envoy
```

### Namespace-Level Override

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: payments-telemetry
  namespace: payments             # namespace scope
spec:
  # Higher trace sampling for critical namespace
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 10.0
```

### Workload-Level Override

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: checkout-debug
  namespace: payments
spec:
  selector:
    matchLabels:
      app: checkout               # workload scope
  # Full sampling for debugging a specific service
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 100.0
  accessLogging:
    - providers:
        - name: envoy
      filter:
        expression: "response.code >= 400"
```

### Disabling Telemetry

You can disable specific telemetry types for workloads that generate too much noise:

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: disable-healthcheck-logging
  namespace: default
spec:
  selector:
    matchLabels:
      app: high-traffic-proxy
  accessLogging:
    - disabled: true
```

---

## 2. Istio Standard Metrics

Envoy sidecars emit a standard set of metrics for every request. These are the metrics you'll query on the exam and in production.

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `istio_requests_total` | Counter | Total requests processed, labeled by response code, source, destination |
| `istio_request_duration_milliseconds` | Histogram | Request duration distribution |
| `istio_request_bytes` | Histogram | Request body sizes |
| `istio_response_bytes` | Histogram | Response body sizes |
| `istio_tcp_sent_bytes_total` | Counter | Total bytes sent for TCP connections |
| `istio_tcp_received_bytes_total` | Counter | Total bytes received for TCP connections |
| `istio_tcp_connections_opened_total` | Counter | Total TCP connections opened |
| `istio_tcp_connections_closed_total` | Counter | Total TCP connections closed |

### Important Labels

Every metric carries labels that let you slice traffic by source, destination, and response:

```
istio_requests_total{
  reporter="source",                          # "source" or "destination"
  source_workload="productpage-v1",
  source_workload_namespace="default",
  destination_workload="reviews-v2",
  destination_workload_namespace="default",
  destination_service="reviews.default.svc.cluster.local",
  request_protocol="http",
  response_code="200",
  response_flags="-",
  connection_security_policy="mutual_tls"
}
```

### Prometheus Queries for Istio

```promql
# Request rate per service (last 5 minutes)
rate(istio_requests_total{reporter="destination"}[5m])

# Error rate for a specific service
sum(rate(istio_requests_total{
  reporter="destination",
  destination_service="reviews.default.svc.cluster.local",
  response_code=~"5.*"
}[5m]))
/
sum(rate(istio_requests_total{
  reporter="destination",
  destination_service="reviews.default.svc.cluster.local"
}[5m]))

# P99 latency for a service
histogram_quantile(0.99,
  sum(rate(istio_request_duration_milliseconds_bucket{
    reporter="destination",
    destination_service="reviews.default.svc.cluster.local"
  }[5m])) by (le)
)
```

### Prometheus Integration

Istio exposes metrics on each sidecar's port 15020 at `/stats/prometheus`. Prometheus discovers these via standard Kubernetes service discovery. If you installed Istio with the `demo` profile, Prometheus is pre-configured. Otherwise, add scrape configs:

```yaml
# Prometheus scrape config for Istio sidecars
scrape_configs:
  - job_name: 'envoy-stats'
    metrics_path: /stats/prometheus
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_container_name]
        action: keep
        regex: istio-proxy
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:15020
        target_label: __address__
```

---

## 3. Distributed Tracing

Istio's Envoy sidecars automatically generate trace spans for every request. But there's a critical nuance that trips up many engineers.

### What Envoy Does Automatically

Each sidecar creates a **span** (a timed record of a single hop). The span captures:
- Source and destination service
- Request duration
- HTTP method, URL, response code

### What Your Application Must Do

Your application **must propagate trace headers** between incoming and outgoing requests. Without this, Envoy creates isolated spans that can't be stitched into a full trace.

Headers to propagate:

```
x-request-id
x-b3-traceid
x-b3-spanid
x-b3-parentspanid
x-b3-sampled
x-b3-flags
b3
traceparent          # W3C Trace Context
tracestate           # W3C Trace Context
```

### Configuring Trace Sampling

Sampling controls what percentage of requests generate traces. High sampling means more visibility but more overhead and storage.

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: tracing-config
  namespace: istio-system
spec:
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 1.0    # 1% of requests — good for production
      customTags:
        environment:
          literal:
            value: "production"
        my_tag:
          header:
            name: x-custom-header
            defaultValue: "unknown"
```

| Sampling Rate | Use Case |
|--------------|----------|
| 0.1% | High-traffic production (>10K rps) |
| 1% | Standard production |
| 10% | Staging / pre-production |
| 100% | Debugging a specific issue (temporary!) |

### Zipkin/Jaeger Provider Configuration

Tracing backends are configured in the Istio `MeshConfig`. With the `demo` profile, Zipkin is pre-configured:

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    defaultConfig:
      tracing:
        zipkin:
          address: zipkin.istio-system:9411
    extensionProviders:
      - name: zipkin
        zipkin:
          service: zipkin.istio-system.svc.cluster.local
          port: 9411
      - name: jaeger
        zipkin:                   # Jaeger accepts Zipkin format
          service: jaeger-collector.istio-system.svc.cluster.local
          port: 9411
```

> **Exam Tip**: Jaeger's collector accepts Zipkin-format spans on port 9411. This is why the provider configuration looks the same for both — Istio sends Zipkin-format traces regardless of the backend.

---

## 4. Envoy Access Logging

Access logs capture every request flowing through the mesh. They're invaluable for debugging, but generate significant volume in large meshes.

### Enabling Access Logs

The simplest way is through the Telemetry API:

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: access-log-config
  namespace: istio-system
spec:
  accessLogging:
    - providers:
        - name: envoy
```

Alternatively, enable via `MeshConfig` during installation:

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    accessLogFile: /dev/stdout
    accessLogEncoding: JSON          # TEXT or JSON
```

### Filtering Access Logs

In production, logging every request is expensive. Filter to capture only errors or slow requests:

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: error-only-logging
  namespace: default
spec:
  accessLogging:
    - providers:
        - name: envoy
      filter:
        expression: "response.code >= 400 || connection.mtls == false"
```

Common filter expressions:

| Expression | What it captures |
|-----------|-----------------|
| `response.code >= 400` | Client and server errors only |
| `response.code >= 500` | Server errors only |
| `response.duration > 1000` | Slow requests (>1s) |
| `connection.mtls == false` | Non-mTLS traffic (security auditing) |

### Reading Envoy Access Logs

```bash
# View access logs for a specific pod's sidecar
kubectl logs deploy/productpage-v1 -c istio-proxy --tail=20

# Example log line (TEXT format):
# [2024-01-15T10:30:45.123Z] "GET /reviews/0 HTTP/1.1" 200 - via_upstream
#   - "-" 0 295 24 23 "-" "Mozilla/5.0" "abc-123" "reviews:9080"
#   outbound|9080||reviews.default.svc.cluster.local 10.244.1.5:39012
#   10.244.2.8:9080 10.244.1.5:33456 - default
```

Key fields in order: timestamp, method/path/protocol, response code, response flags, authority, upstream host, request duration (ms).

---

## 5. Kiali: Service Mesh Visualization

Kiali is Istio's official observability console. It provides real-time visualization of your service mesh topology, traffic flows, and configuration health.

### What Kiali Shows You

| View | What You See |
|------|-------------|
| **Graph** | Live service topology with traffic animation, error rates, latency |
| **Applications** | Grouped view of workloads forming an application |
| **Workloads** | Individual deployment health, pod logs, Envoy config |
| **Services** | Kubernetes services with Istio routing info |
| **Istio Config** | Validation of VirtualService, DestinationRule, etc. |

### Accessing Kiali

```bash
# If installed with demo profile, Kiali is already running
kubectl get svc -n istio-system kiali

# Port-forward to access the dashboard
kubectl port-forward svc/kiali -n istio-system 20001:20001

# Or use istioctl dashboard shortcut
istioctl dashboard kiali
```

### Kiali for the ICA Exam

Kiali is most useful for:

1. **Verifying traffic routing** — After applying a VirtualService, watch the graph to confirm traffic splits match your weights
2. **Spotting misconfigurations** — Kiali flags invalid Istio resources with warning icons
3. **Checking mTLS status** — The security badge on each edge shows whether mTLS is active
4. **Identifying unhealthy services** — Red nodes indicate error rates above threshold

> **Exam Tip**: You likely won't have Kiali on the exam itself, but understanding what it shows and how it integrates is fair game for questions.

---

## 6. Grafana Dashboards for Istio

Istio ships with pre-built Grafana dashboards that visualize the Prometheus metrics described in Section 2. There are three main dashboards:

### Mesh Dashboard

Shows the global view across your entire mesh:
- Total request volume
- Global success rate
- Aggregate P50/P90/P99 latency

### Service Dashboard

Drill into a specific service:
- Inbound request volume and success rate
- Client workloads (who's calling this service)
- Request duration distribution
- Request/response sizes

### Workload Dashboard

Drill into a specific workload (deployment):
- Inbound and outbound request metrics
- TCP connection metrics
- Per-destination breakdowns

### Accessing Grafana

```bash
# Port-forward (if installed with demo profile)
kubectl port-forward svc/grafana -n istio-system 3000:3000

# Or use istioctl shortcut
istioctl dashboard grafana
```

### Building a Custom Dashboard

If the pre-built dashboards don't cover your use case, build custom panels using Istio metrics:

```json
{
  "targets": [
    {
      "expr": "sum(rate(istio_requests_total{reporter=\"destination\", destination_service=~\"$service\"}[5m])) by (response_code)",
      "legendFormat": "{{response_code}}"
    }
  ],
  "title": "Request Rate by Response Code",
  "type": "timeseries"
}
```

---

## Common Mistakes

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| Setting 100% trace sampling in production | Massive storage costs, performance degradation | Use 0.1-1% for production, increase temporarily for debugging |
| Forgetting to propagate trace headers in app code | Traces show disconnected spans, no end-to-end visibility | Forward all `x-b3-*` and `traceparent` headers in your application |
| Enabling TEXT access logs in high-traffic mesh | Log volume overwhelms storage, costs spike | Use JSON encoding with filters, or disable for noisy workloads |
| Querying `reporter="source"` when you want destination metrics | Double-counting or inconsistent numbers | Use `reporter="destination"` for server-side metrics (more reliable) |
| Not installing Prometheus/Grafana with Istio | Metrics are generated but not stored or visualized | Install addons or configure external Prometheus to scrape Istio metrics |
| Applying Telemetry in wrong namespace | Config silently ignored because scope doesn't match | `istio-system` for mesh-wide, target namespace for namespace scope |

---

## Quiz

### Question 1
What are the three scopes at which the Istio Telemetry API can be configured?

<details>
<summary>Show Answer</summary>

**Mesh-wide** (applied in `istio-system` with no selector), **namespace** (applied in target namespace with no selector), and **workload** (applied in target namespace with a `selector.matchLabels`). More specific scopes override broader ones.
</details>

### Question 2
Which Istio metric would you query to calculate the error rate of a service?

<details>
<summary>Show Answer</summary>

`istio_requests_total` with a filter on `response_code=~"5.*"` divided by total `istio_requests_total`. For example:
```promql
sum(rate(istio_requests_total{response_code=~"5.*", destination_service="myservice.default.svc.cluster.local"}[5m]))
/
sum(rate(istio_requests_total{destination_service="myservice.default.svc.cluster.local"}[5m]))
```
</details>

### Question 3
Why do distributed traces sometimes show disconnected spans even when Istio tracing is configured?

<details>
<summary>Show Answer</summary>

The **application is not propagating trace headers**. Envoy generates spans automatically, but the application must forward headers like `x-b3-traceid`, `x-b3-spanid`, `x-b3-parentspanid`, `x-b3-sampled`, and `traceparent` from incoming requests to outgoing requests. Without propagation, each hop creates an independent trace instead of a connected chain.
</details>

### Question 4
How would you enable access logging only for requests that return HTTP 500+ errors?

<details>
<summary>Show Answer</summary>

Use the Telemetry API with a CEL filter expression:
```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: error-logging
  namespace: default
spec:
  accessLogging:
    - providers:
        - name: envoy
      filter:
        expression: "response.code >= 500"
```
</details>

### Question 5
What port does Envoy expose Prometheus metrics on, and what is the metrics path?

<details>
<summary>Show Answer</summary>

Port **15020**, path `/stats/prometheus`. Prometheus scrapes this endpoint on each sidecar to collect Istio standard metrics.
</details>

---

## Hands-On Exercise: Configuring Istio Observability

### Objective

Configure telemetry for a running Istio mesh: enable metrics, set up tracing with custom sampling, and configure filtered access logging.

### Setup

```bash
# Ensure you have a kind cluster with Istio demo profile
# (see README.md for full setup instructions)
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled --overwrite

# Deploy the bookinfo sample app
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/bookinfo/platform/kube/bookinfo.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=productpage --timeout=120s

# Generate some traffic
for i in $(seq 1 20); do
  kubectl exec deploy/ratings-v1 -- curl -s productpage:9080/productpage > /dev/null
done
```

### Task 1: Apply Mesh-Wide Telemetry

Create a Telemetry resource in `istio-system` that enables Prometheus metrics, sets tracing to 5% sampling, and enables access logging:

```bash
kubectl apply -f - <<EOF
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: mesh-defaults
  namespace: istio-system
spec:
  metrics:
    - providers:
        - name: prometheus
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 5.0
  accessLogging:
    - providers:
        - name: envoy
EOF
```

Verify the telemetry resource was created:

```bash
kubectl get telemetry -n istio-system
```

### Task 2: Override Tracing for a Specific Namespace

Create a namespace-level override that increases trace sampling to 50% for the default namespace (simulating a debugging scenario):

```bash
kubectl apply -f - <<EOF
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: debug-tracing
  namespace: default
spec:
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 50.0
EOF
```

### Task 3: Filter Access Logs for Errors Only

Apply a workload-level Telemetry that only logs errors for the `productpage` service:

```bash
kubectl apply -f - <<EOF
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: productpage-logging
  namespace: default
spec:
  selector:
    matchLabels:
      app: productpage
  accessLogging:
    - providers:
        - name: envoy
      filter:
        expression: "response.code >= 400"
EOF
```

### Task 4: Verify Metrics Are Flowing

```bash
# Check that Envoy is emitting Istio metrics
kubectl exec deploy/productpage-v1 -c istio-proxy -- \
  curl -s localhost:15020/stats/prometheus | grep istio_requests_total | head -5

# Generate more traffic and check again
for i in $(seq 1 10); do
  kubectl exec deploy/ratings-v1 -- curl -s productpage:9080/productpage > /dev/null
done

# Query Prometheus (if available)
# kubectl port-forward svc/prometheus -n istio-system 9090:9090
# Then open http://localhost:9090 and query: istio_requests_total
```

### Task 5: View Access Logs

```bash
# Generate a request that should succeed (no log due to filter)
kubectl exec deploy/ratings-v1 -- curl -s productpage:9080/productpage > /dev/null

# Generate a request that should fail (logged due to filter)
kubectl exec deploy/ratings-v1 -- curl -s productpage:9080/nonexistent-page > /dev/null

# Check productpage sidecar logs — only the 404 should appear
kubectl logs deploy/productpage-v1 -c istio-proxy --tail=5
```

### Success Criteria

- [ ] Mesh-wide Telemetry resource exists in `istio-system` with metrics, tracing (5%), and access logging
- [ ] Namespace-level Telemetry in `default` overrides tracing to 50%
- [ ] Workload-level Telemetry for `productpage` filters access logs to errors only
- [ ] `istio_requests_total` metric is visible from the Envoy stats endpoint
- [ ] Access logs for `productpage` only show error responses (4xx/5xx)

### Cleanup

```bash
kubectl delete telemetry mesh-defaults -n istio-system
kubectl delete telemetry debug-tracing -n default
kubectl delete telemetry productpage-logging -n default
kubectl delete -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/bookinfo/platform/kube/bookinfo.yaml
```

---

## Next Module

You've now completed all four ICA modules:
- **Module 1**: Installation, profiles, sidecar injection, architecture (20%)
- **Module 2**: Traffic management, fault injection, resilience (35% + 10%)
- **Module 3**: Security, authorization, troubleshooting (15% + 10%)
- **Module 4**: Observability — metrics, tracing, logging, dashboards (10%)

For deeper dives into the tools referenced here, see:
- [Observability Theory](../../platform/foundations/observability-theory/README.md) — Metrics, logs, traces fundamentals
- [Observability Tools](../../platform/toolkits/observability/README.md) — Prometheus, Grafana, Jaeger in depth

### Final Exam Prep Checklist

- [ ] Can install Istio with `istioctl` using different profiles
- [ ] Can configure automatic and manual sidecar injection
- [ ] Can write VirtualService for traffic splitting, header routing, fault injection
- [ ] Can write DestinationRule for subsets, circuit breaking, outlier detection
- [ ] Can configure Gateway for ingress with TLS
- [ ] Can set up ServiceEntry for egress control
- [ ] Can configure PeerAuthentication (STRICT/PERMISSIVE)
- [ ] Can write AuthorizationPolicy (ALLOW/DENY)
- [ ] Can use `istioctl analyze`, `proxy-status`, `proxy-config` for debugging
- [ ] Can configure Telemetry API for metrics, tracing, and access logging
- [ ] Can query Istio standard metrics with PromQL
- [ ] Can configure trace sampling rates and understand header propagation
- [ ] Can filter access logs using CEL expressions
- [ ] Can use Kiali, Grafana, and Jaeger for mesh observability

Good luck on your ICA exam!

---
title: "Module 1.4: Istio Observability"
slug: k8s/ica/module-1.4-istio-observability
sidebar:
  order: 5
revision_pending: false
---

## Complexity: `[MEDIUM]`

## Time to Complete: 50-70 minutes

---

## Prerequisites

Before starting this module, you should have completed the earlier ICA modules because observability only becomes useful when the mesh already has traffic, policy, and routing behavior worth explaining.

- [Module 1: Installation & Architecture](../module-1.1-istio-installation-architecture/) — `istiod`, Envoy sidecars, injection, and data plane control
- [Module 2: Traffic Management](../module-1.2-istio-traffic-management/) — `VirtualService`, `DestinationRule`, `Gateway`, retries, and traffic splits
- [Module 3: Security & Troubleshooting](../module-1.3-istio-security-troubleshooting/) — mTLS, `AuthorizationPolicy`, `istioctl analyze`, and proxy debugging
- Basic Kubernetes operational comfort with Deployments, Services, namespaces, labels, and `kubectl logs`
- Basic familiarity with metrics, logs, traces, and Prometheus-style time series queries

This module assumes Kubernetes 1.35+ and a modern Istio installation using the Telemetry API. Older Istio material may mention Mixer, global-only tracing flags, or heavy `EnvoyFilter` customization for basic telemetry. Treat those patterns as historical unless a legacy cluster forces you to maintain them.

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Design** an Istio observability configuration that chooses the right Telemetry scope for mesh-wide, namespace-level, and workload-level requirements.
2. **Debug** service behavior by combining Istio standard metrics, Envoy access logs, Kiali graph evidence, and distributed traces instead of relying on one signal.
3. **Evaluate** PromQL queries for request rate, error rate, and latency so dashboards measure the behavior a team actually needs to operate.
4. **Configure** tracing and access logging with practical sampling, filtering, and header propagation choices that avoid noisy or misleading telemetry.
5. **Compare** Grafana, Kiali, Jaeger, Envoy stats, and raw logs so you can pick the fastest tool for a production incident or ICA scenario.

---

## Why This Module Matters

A payments platform team rolls out a new checkout service on Friday afternoon. The deployment looks healthy, the Pods are ready, and the Kubernetes Service has endpoints. Ten minutes later, customer support reports that some orders complete, some time out, and some fail only when traffic comes through a canary route.

The team does not need another command that says the Pods are running. They need to know which service path is failing, whether failures are isolated to one workload version, whether mTLS or routing policy changed, and whether the slow hop is checkout, inventory, payment authorization, or the external fraud API.

Istio observability is useful because the Envoy sidecars sit on the request path. They see request counts, response codes, latency, byte sizes, mTLS state, routing decisions, and trace identifiers even when application teams did not instrument every service perfectly. That does not remove the need for application telemetry, but it gives platform engineers a common baseline across many languages and teams.

That baseline is especially valuable in a certification or production incident because it gives you a neutral view before every team has explained its own component. Kubernetes readiness tells you whether a Pod should receive traffic; Istio telemetry tells you what happened after traffic actually arrived. When those two views disagree, the disagreement is not noise. It is a clue that the fault may live in routing, policy, retries, endpoints, propagation, or the proxy path rather than in the application process alone.

The ICA exam treats observability as a separate domain because it ties the other domains together. Traffic management creates routes that need to be verified. Security policies create authorization decisions that need to be explained. Troubleshooting starts with symptoms, but it becomes reliable only when you can turn those symptoms into evidence.

A senior operator does not ask, "Which dashboard should I open?" as the first question. They ask, "What kind of evidence would prove or disprove my current theory?" If the theory is that a route sends traffic to the wrong subset, Kiali and destination labels may answer quickly. If the theory is that a backend hop is slow, Prometheus latency histograms and traces are better. If the theory is that only denied or failed calls matter, filtered access logs give the most concrete record.

This module therefore treats observability as an operating method, not as a tour of dashboards. You will learn how to scope Telemetry resources, how to read the labels that make Istio metrics useful, how tracing depends on header propagation, and how access logs reveal proxy-observed request facts. More importantly, you will practice moving between signals without losing the original question, because the fastest investigation is usually the one that keeps narrowing the evidence instead of collecting every possible graph.

> **Mental model**
>
> Think of Istio observability as four coordinated signals rather than one dashboard. Metrics answer "how much and how often." Logs answer "what happened to this request at this proxy." Traces answer "where did this request spend time across hops." Topology views answer "which services are actually talking right now."

---

## 1. Build the Observability Mental Model

Istio observability starts with a simple mechanism: every injected workload has an Envoy proxy, and traffic that passes through Envoy can be measured consistently. The application still matters, especially for business events and trace propagation, but the mesh gives you a shared layer of network and request telemetry.

The most important beginner mistake is treating metrics, logs, traces, and topology as interchangeable. They overlap, but they do not answer the same question. A metric can show that error rate rose at 14:05, but it usually cannot show the exact request headers that triggered the failure. A trace can show one slow request path, but it cannot prove how many users were affected without metrics.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         Istio Observability Flow                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Client                                                                    │
│    │                                                                       │
│    ▼                                                                       │
│  ┌────────────────┐        ┌────────────────┐        ┌────────────────┐    │
│  │ Envoy sidecar  │───────▶│ Envoy sidecar  │───────▶│ Envoy sidecar  │    │
│  │ source proxy   │        │ destination    │        │ next service   │    │
│  └───────┬────────┘        └───────┬────────┘        └───────┬────────┘    │
│          │                         │                         │             │
│          │ metrics                 │ metrics                 │ metrics     │
│          │ access logs             │ access logs             │ access logs │
│          │ trace spans             │ trace spans             │ trace spans │
│          ▼                         ▼                         ▼             │
│  ┌────────────────┐        ┌────────────────┐        ┌────────────────┐    │
│  │ Prometheus     │        │ Log backend    │        │ Jaeger/Zipkin  │    │
│  │ RED metrics    │        │ request facts  │        │ request path   │    │
│  └────────────────┘        └────────────────┘        └────────────────┘    │
│          │                                                   │             │
│          ▼                                                   ▼             │
│  ┌────────────────┐                                 ┌────────────────┐     │
│  │ Grafana        │                                 │ Kiali          │     │
│  │ dashboards     │                                 │ topology       │     │
│  └────────────────┘                                 └────────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

The diagram shows why Istio can provide a baseline without code changes. The proxies emit telemetry because they are already handling the traffic. This is different from application instrumentation, where each service must explicitly record business metrics or create spans with an SDK.

Baseline does not mean complete. Envoy can tell that `checkout` called `payments` and received a `503`, but it cannot know that the failed payment attempt was a premium subscription renewal unless the application records that domain fact. Envoy can start or continue trace spans, but the application must forward trace headers when it makes outbound calls. This division of responsibility keeps the platform honest: the mesh gives every team the same transport evidence, while application instrumentation explains the business meaning behind that evidence.

> **Pause and predict:** If a request goes from `frontend` to `checkout` to `payments`, but `checkout` does not forward trace headers to `payments`, what will Jaeger show?
>
> You should expect separate trace fragments rather than one continuous request path. Envoy can create spans at each hop, but the trace identifiers must travel with the application request for the backend spans to join the same trace.

The four observability signals support different operational questions.

| Signal | Best question | Istio source | Common tool |
|---|---|---|---|
| Metrics | "Is this service getting slower or failing more often?" | Envoy standard metrics | Prometheus and Grafana |
| Access logs | "What did this proxy record for a specific request class?" | Envoy access log provider | `kubectl logs` or log backend |
| Traces | "Which hop was slow for this request path?" | Envoy spans plus propagated headers | Jaeger or Zipkin |
| Topology | "Who is talking to whom right now?" | Metrics and Istio config analysis | Kiali |

A senior workflow usually starts broad and narrows quickly. First, metrics identify whether the symptom is real and which service owns it. Then topology verifies whether traffic is flowing through the expected route and workload version. Then traces or logs explain one representative request in enough detail to decide the fix.

This order matters because observability tools can mislead you when used in isolation. A single trace may look terrible because it sampled an unusually slow request. A graph may look healthy because traffic volume is low. Logs may be complete but too noisy to read during a high-volume incident.

The same discipline applies when a dashboard already points at a likely cause. If a panel shows errors from `reviews-v2`, resist the temptation to edit the route immediately. First ask whether the query uses the intended reporter, whether the errors are concentrated in one response code, whether Kiali confirms traffic is reaching that workload, and whether logs show Envoy flags that would change your interpretation. Those extra checks turn a plausible theory into a defensible operational decision.

```ascii
┌──────────────────────────────────────────────────────────────────┐
│                     Choosing the First Signal                     │
├───────────────────────────────┬──────────────────────────────────┤
│ Symptom                       │ Start with                       │
├───────────────────────────────┼──────────────────────────────────┤
│ Users report intermittent 5xx │ Prometheus error-rate query       │
│ One request path is slow      │ Trace for the slow path           │
│ Canary route seems wrong      │ Kiali graph plus route labels     │
│ Security policy denies calls  │ Access logs plus mTLS labels      │
│ Dashboard shows odd totals    │ Metric labels and reporter choice │
└───────────────────────────────┴──────────────────────────────────┘
```

Do not memorize the table as trivia. Use it as a triage habit. The tool is not the goal; the goal is choosing evidence that can change your next action.

> **Active check:** A team says, "Kiali shows a red edge, so Prometheus must be broken." What is the more likely explanation?
>
> Kiali often visualizes Prometheus data and Istio configuration together. A red edge usually means the underlying request metrics show errors or degraded health, not that Prometheus is broken. You would inspect the relevant `istio_requests_total` series and the destination workload before blaming the tool.

---

## 2. Configure Telemetry by Scope

The Telemetry API is the main Istio resource for controlling mesh observability behavior. It configures metrics, tracing, and access logging without asking you to edit every workload or write low-level Envoy configuration for routine cases.

The API is powerful because it is scoped. A mesh-wide Telemetry resource gives a safe default. A namespace resource can raise sampling for a business-critical area. A workload resource can enable intense debugging for one service without flooding the entire cluster with logs and spans.

```ascii
┌──────────────────────────────────────────────────────────────────────────┐
│                       Telemetry Scope Precedence                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Mesh-wide default                                                       │
│  namespace: istio-system                                                 │
│  selector: none                                                          │
│        │                                                                 │
│        ▼                                                                 │
│  Namespace override                                                      │
│  namespace: target application namespace                                 │
│  selector: none                                                          │
│        │                                                                 │
│        ▼                                                                 │
│  Workload override                                                       │
│  namespace: target application namespace                                 │
│  selector: matchLabels for selected Pods                                 │
│                                                                          │
│  More specific configuration wins when settings overlap.                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

| Scope | Where the resource lives | Selector | Use when |
|---|---|---|---|
| Mesh-wide | `istio-system` | None | You need a default for every injected workload |
| Namespace | Application namespace | None | One team or environment needs different telemetry behavior |
| Workload | Application namespace | `spec.selector.matchLabels` | One Deployment needs temporary or special handling |

Here is a mesh-wide default that enables Prometheus metrics, sends traces to a configured Zipkin-compatible provider, and enables Envoy access logging. In a real platform, you may choose filtered logging rather than logging every request, but seeing the unfiltered shape first makes the later filter easier to understand.

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: mesh-observability-defaults
  namespace: istio-system
spec:
  metrics:
    - providers:
        - name: prometheus
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 1.0
  accessLogging:
    - providers:
        - name: envoy
```

A namespace override changes behavior for workloads in that namespace. This example raises trace sampling for `payments` during an investigation. It does not require a redeploy because Istio pushes updated proxy configuration through the control plane.

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: payments-debug-tracing
  namespace: payments
spec:
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 25.0
```

A workload override should be more surgical. The following resource selects only Pods with `app: checkout` in the `payments` namespace and records access logs only for failed requests. This is the kind of targeted change that helps during an incident without creating a storage problem for every service.

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: checkout-error-logs
  namespace: payments
spec:
  selector:
    matchLabels:
      app: checkout
  accessLogging:
    - providers:
        - name: envoy
      filter:
        expression: "response.code >= 400"
```

> **Pause and predict:** If a mesh-wide Telemetry sets trace sampling to `1.0`, a namespace Telemetry in `payments` sets it to `25.0`, and a workload Telemetry for `checkout` sets it to `100.0`, what sampling should `checkout` use?
>
> `checkout` should use the workload-level setting because it is the most specific matching scope. Other workloads in `payments` should use the namespace-level setting, and workloads outside `payments` should use the mesh-wide default.

A common source of silent confusion is namespace placement. A mesh-wide resource belongs in `istio-system` with no selector. A namespace-wide resource belongs in the application namespace with no selector. A workload resource also belongs in the application namespace, and its selector must match the workload Pod labels, not the Kubernetes Service labels unless those labels are actually present on the Pods.

You can inspect the labels before writing a workload selector. This avoids a situation where the YAML applies successfully but matches nothing useful.

```bash
kubectl get pods -n payments --show-labels

kubectl get deploy checkout -n payments -o jsonpath='{.spec.template.metadata.labels}'
```

The distinction between Service labels and Pod template labels is worth slowing down for because it causes many quiet failures. Kubernetes Services select Pods, but Istio workload-scoped Telemetry selects the workload labels on the Pods themselves. If you copy labels from the Service object without checking the Deployment template, you can create a valid Telemetry resource that never affects the proxy you meant to investigate. Always verify the target labels before treating a workload override as active evidence.

The Telemetry API can also add or remove metric tags. Be conservative with custom labels because high-cardinality labels can overload Prometheus. A label like `destination_service` is expected because the number of services is bounded. A label like `user_id` is dangerous because it can create a time series per user.

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: add-environment-tag
  namespace: istio-system
spec:
  metrics:
    - providers:
        - name: prometheus
      overrides:
        - match:
            metric: ALL_METRICS
            mode: CLIENT_AND_SERVER
          tagOverrides:
            environment:
              operation: UPSERT
              value: '"production"'
```

| Tag choice | Cardinality risk | Operational value | Recommendation |
|---|---|---|---|
| `environment` | Low | Good for separating prod, staging, and dev | Usually safe |
| `team` | Low to medium | Useful for ownership dashboards | Safe if controlled |
| `request_path` | Medium to high | Useful only when paths are normalized | Avoid raw paths with IDs |
| `user_id` | Very high | Tempting but dangerous | Do not use as a metric label |
| `trace_id` | Very high | Better in logs and traces | Do not use as a metric label |

> **Active check:** You are asked to add `customer_id` as a Prometheus label so the business team can debug one account. What should you recommend instead?
>
> Do not add `customer_id` to mesh metrics because it creates high-cardinality time series and can harm Prometheus performance. Put request identifiers in logs or traces, then correlate a specific customer investigation through a trace ID, request ID, or application-level event.

The senior skill here is not knowing every Telemetry field by memory. It is matching the scope and cardinality of the configuration to the operational problem. Broad defaults should be cheap and stable. Expensive telemetry should be temporary, targeted, and easy to remove.

Think about Telemetry scope the same way you think about a blast radius for a routing change. A mesh-wide setting should be safe enough to forget about during a busy day, because it affects every injected workload. A namespace setting should align with a team, environment, or investigation boundary. A workload setting should be precise enough that another operator can remove it after the incident without wondering whether it was secretly carrying platform behavior.

---

## 3. Use Istio Metrics for RED Dashboards

Istio standard metrics let you build RED dashboards: rate, errors, and duration. These three signals are enough to answer the first operational question for most HTTP and gRPC services: how much traffic is arriving, how much is failing, and how long successful or failed requests take.

The main counter for request volume and errors is `istio_requests_total`. The main histogram for latency is `istio_request_duration_milliseconds`. Request and response size histograms help when payload growth or compression behavior affects performance.

| Metric | Type | Primary question |
|---|---|---|
| `istio_requests_total` | Counter | How many requests happened, grouped by labels such as service and response code? |
| `istio_request_duration_milliseconds` | Histogram | What latency distribution did Envoy observe for requests? |
| `istio_request_bytes` | Histogram | How large were request bodies? |
| `istio_response_bytes` | Histogram | How large were response bodies? |
| `istio_tcp_sent_bytes_total` | Counter | How much TCP data was sent for non-HTTP traffic? |
| `istio_tcp_received_bytes_total` | Counter | How much TCP data was received for non-HTTP traffic? |
| `istio_tcp_connections_opened_total` | Counter | How many TCP connections opened? |
| `istio_tcp_connections_closed_total` | Counter | How many TCP connections closed? |

Istio metrics include labels that describe the reporter, source, destination, response code, protocol, and security policy. These labels make the metrics useful, but they also create opportunities for wrong queries. The same request may be observed from the source side and destination side, so you need to choose the reporter intentionally.

```text
istio_requests_total{
  reporter="destination",
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

| Label | Why it matters | Frequent mistake |
|---|---|---|
| `reporter` | Distinguishes source-side and destination-side observation | Mixing reporters and double-counting traffic |
| `destination_service` | Groups traffic by Kubernetes service identity | Querying workload when service-level SLOs are needed |
| `destination_workload` | Identifies the serving Deployment or workload version | Missing a bad canary because service totals look normal |
| `response_code` | Separates success, client errors, and server errors | Treating all non-200 responses as server failures |
| `response_flags` | Shows Envoy-level conditions such as resets or timeouts | Ignoring proxy failures when app logs look clean |
| `connection_security_policy` | Shows whether mTLS protected the connection | Assuming policy state without checking observed traffic |

> **Pause and predict:** A service dashboard uses `reporter="source"` for one panel and `reporter="destination"` for another. Why might the request totals disagree?
>
> The source proxy and destination proxy observe traffic from different positions. Retries, missing sidecars, passthrough traffic, or telemetry gaps can make the two perspectives differ. For service reliability dashboards, `reporter="destination"` is usually the cleaner server-side view.

A worked example makes the query pattern concrete. Suppose support reports that the `reviews` service is failing after a canary release. You first need service-level request rate, then the server-error fraction, then latency for the destination service.

```promql
sum(rate(istio_requests_total{
  reporter="destination",
  destination_service="reviews.default.svc.cluster.local"
}[5m]))
```

That query answers volume only. It should not be used as an error-rate query because it includes all response codes. The next query divides server-error traffic by all traffic for the same service and the same reporter.

```promql
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
```

Now imagine the error rate is acceptable but users still complain about slowness. Latency histograms require a different shape because the raw metric has bucket series. `histogram_quantile` estimates a percentile from the per-bucket rates.

```promql
histogram_quantile(0.99,
  sum(rate(istio_request_duration_milliseconds_bucket{
    reporter="destination",
    destination_service="reviews.default.svc.cluster.local"
  }[5m])) by (le)
)
```

The senior review step is checking whether a query matches the operational question. A P99 latency query by service is useful for user experience, but it may hide one bad workload version. If a canary is involved, add `destination_workload` or `destination_version` if that label exists in your telemetry.

```promql
histogram_quantile(0.95,
  sum(rate(istio_request_duration_milliseconds_bucket{
    reporter="destination",
    destination_service="reviews.default.svc.cluster.local"
  }[5m])) by (le, destination_workload)
)
```

> **Active check:** A canary receives only ten percent of traffic, and the service-level P95 looks fine. What query change helps you find whether the canary is slow?
>
> Break the latency query down by workload or version label instead of aggregating the whole service. A small canary can be hidden inside service-level aggregates because most requests still go to the stable version.

Prometheus must scrape Envoy stats for these queries to work. In many demo installations the addon is already configured. In production, a platform team usually integrates Istio metrics into an existing Prometheus or managed metrics backend.

```yaml
scrape_configs:
  - job_name: envoy-stats
    metrics_path: /stats/prometheus
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_container_name]
        action: keep
        regex: istio-proxy
      - source_labels: [__address__]
        action: replace
        regex: ([^:]+)(?::\d+)?
        replacement: $1:15020
        target_label: __address__
```

You can verify a sidecar emits metrics without waiting for Prometheus. This check is useful when the dashboard is blank and you need to separate "Envoy is not emitting" from "Prometheus is not scraping."

```bash
kubectl exec deploy/productpage-v1 -c istio-proxy -- \
  curl -s 127.0.0.1:15020/stats/prometheus | grep '^istio_requests_total' | head -5
```

A blank result does not always mean telemetry is broken. The workload may not have received traffic yet, the proxy may not be injected, or the command may target the wrong container. Generate traffic, confirm the `istio-proxy` container exists, and check the workload labels before changing Telemetry configuration.

| Symptom | Likely cause | First check |
|---|---|---|
| No `istio_requests_total` from sidecar | No traffic has passed through the proxy | Generate traffic and retry the stats endpoint |
| Metrics from sidecar but no Prometheus data | Scrape job or target discovery is wrong | Check Prometheus targets for `istio-proxy` Pods |
| Service totals look doubled | Query mixed source and destination reporters | Filter explicitly on one `reporter` |
| Canary issue hidden in aggregate | Query grouped only by service | Group by workload or version label |
| Unexpected plaintext label | Traffic bypasses mTLS or policy is permissive | Check `connection_security_policy` and PeerAuthentication |

The exam may ask for a metric name, but production asks for judgment. You should be able to explain why a query isolates the symptom, what labels could distort it, and what signal you would inspect next if the result is surprising.

When you review a PromQL expression, read it from the inside out. The selector should name the service, reporter, and response class that match the question. The range window should be long enough to smooth normal jitter but short enough to show a recent change. The aggregation should preserve labels that matter, such as workload version during a canary, while dropping labels that only add noise. That habit catches many dashboard errors before they become incident folklore.

---

## 4. Trace Requests Across Service Boundaries

Distributed tracing connects spans into a request path. In Istio, Envoy can create spans for proxy-observed hops, but the application must propagate trace headers when it makes outbound requests. This distinction is one of the most important observability concepts in the mesh.

A trace is the whole request journey. A span is one timed unit of work inside that journey. If `frontend` calls `checkout`, and `checkout` calls `payments`, a healthy trace should show related spans that share trace context. If `checkout` drops the headers, `payments` may still create a span, but it appears as a separate trace.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                          Trace Context Propagation                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Good path                                                                 │
│  frontend ──headers──▶ checkout ──same trace headers──▶ payments           │
│      │                    │                              │                 │
│      ▼                    ▼                              ▼                 │
│  span A               span B                         span C                │
│      └────────────────────┴──────────────────────────────┘                 │
│                  one connected trace                                       │
│                                                                            │
│  Broken path                                                               │
│  frontend ──headers──▶ checkout ──headers dropped──▶ payments              │
│      │                    │                              │                 │
│      ▼                    ▼                              ▼                 │
│  span A               span B                         span X                │
│      └────────────────────┘                         separate trace         │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Common headers include the B3 family and the W3C Trace Context family. You do not need to memorize every header for daily operations, but you do need to recognize that applications must forward the incoming context to outgoing requests.

```text
x-request-id
x-b3-traceid
x-b3-spanid
x-b3-parentspanid
x-b3-sampled
x-b3-flags
b3
traceparent
tracestate
```

> **Pause and predict:** A Java service uses an HTTP client that creates a fresh outbound request and copies no inbound headers. Istio tracing is enabled at `100.0` percent for that workload. Will the backend call join the frontend trace?
>
> No. Full sampling increases how often traces are recorded, but it does not repair missing propagation. The application or its tracing library still needs to copy or inject the trace context into outbound requests.

Trace sampling is a cost and visibility trade-off. Low sampling reduces storage and query cost in high-volume systems, but it may miss rare failures. High sampling is appropriate during targeted debugging, but it can become expensive if applied broadly.

| Sampling rate | Practical use | Risk |
|---|---|---|
| `0.1` | Very high-volume production paths | Rare errors may not be sampled |
| `1.0` | Standard production default | Usually balanced for broad visibility |
| `10.0` | Staging or short production investigation | More storage and backend load |
| `25.0` | Focused namespace debugging | Should be time-boxed |
| `100.0` | One workload during an active investigation | Dangerous as a long-term default |

Configure tracing with Telemetry after the tracing provider exists in mesh configuration. The provider name in Telemetry must match an extension provider configured for the mesh.

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    extensionProviders:
      - name: zipkin
        zipkin:
          service: zipkin.istio-system.svc.cluster.local
          port: 9411
      - name: jaeger
        zipkin:
          service: jaeger-collector.istio-system.svc.cluster.local
          port: 9411
```

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: tracing-default
  namespace: istio-system
spec:
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 1.0
      customTags:
        cluster:
          literal:
            value: "primary"
        request_id:
          header:
            name: x-request-id
            defaultValue: "missing"
```

Jaeger can accept Zipkin-format spans through a compatible collector endpoint, which is why many examples use a `zipkin` provider shape even when the backend is Jaeger. The important operational check is not the brand name in the YAML; it is whether the collector service, port, protocol, and Telemetry provider name line up.

> **Active check:** A team says, "Jaeger is empty, so Istio tracing is disabled." What checks should you make before accepting that conclusion?
>
> Confirm the Telemetry resource references an existing provider, confirm the collector service is reachable, generate sampled traffic, and verify applications propagate headers across service boundaries. Also check whether sampling is so low that your small test did not produce a stored trace.

You can use traces as a guided debugging tool rather than a visual curiosity. Start from a user-facing slow request, find the trace, identify the slow span, then switch to metrics for the affected service to see whether the issue is widespread. That sequence prevents overreacting to a single unusual trace.

A useful trace review asks concrete questions. Which span consumes most of the total time? Are retries visible? Did the request cross the expected services? Did the response code change at a particular hop? Are there missing spans that suggest header propagation failed?

| Trace symptom | Likely meaning | Next action |
|---|---|---|
| One backend span dominates latency | Downstream service or dependency is slow | Check service metrics and application logs for that backend |
| Trace stops at a middle service | Headers were not propagated or traffic left the mesh | Inspect application HTTP client and sidecar injection |
| Many short retry spans | Retries are masking upstream instability | Check `VirtualService` retry policy and error metrics |
| Root span is missing | Entry traffic may bypass the expected proxy | Check Gateway, injection, and request path |
| Spans have no useful tags | Telemetry custom tags or app instrumentation is thin | Add safe tags with bounded cardinality |

The senior habit is correlating traces with other evidence. A trace proves what happened to one sampled request. Metrics prove whether the pattern is common. Access logs can verify exact response codes and flags. Kiali can show whether the trace path matches real service topology.

This correlation is also how you avoid overfitting to a beautiful trace. A trace with a slow `payments` span might represent the main failure pattern, or it might be one unlucky request captured by sampling. Before you escalate the payments team, check whether destination metrics show elevated latency for that workload and whether access logs show matching response codes or flags. The trace gives you the story of one request; the surrounding signals tell you whether that story explains the incident.

---

## 5. Filter and Read Envoy Access Logs

Access logs are the most concrete mesh signal. They record request-level facts from Envoy, including method, path, response code, response flags, upstream service, duration, and connection information. They are also the easiest signal to overproduce.

The default operational question for access logs should be, "Which request class do I need to capture?" Logging every successful request for every service may be acceptable in a tiny lab, but it creates cost, retention, and privacy problems in real systems. Istio Telemetry lets you enable logging broadly or filter it narrowly.

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: access-log-default
  namespace: istio-system
spec:
  accessLogging:
    - providers:
        - name: envoy
```

A production-oriented resource is usually filtered. This example captures client errors, server errors, and non-mTLS traffic for one namespace. It gives operators evidence for failure and policy investigation without recording every normal request.

```yaml
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: suspicious-request-logs
  namespace: default
spec:
  accessLogging:
    - providers:
        - name: envoy
      filter:
        expression: "response.code >= 400 || connection.mtls == false"
```

| Filter expression | Captures | Use case |
|---|---|---|
| `response.code >= 400` | Client and server errors | General failure investigation |
| `response.code >= 500` | Server errors only | Backend reliability triage |
| `response.duration > 1000` | Slow requests above one second | Latency investigation |
| `connection.mtls == false` | Plaintext or non-mTLS traffic | Security validation |
| `response.code == 403` | Authorization denials | Policy debugging |
| `response.flags != "-"` | Envoy-level anomalies | Proxy timeout or reset triage |

> **Pause and predict:** You enable an access log filter for `response.code >= 500`, then test a missing page that returns `404`. Should that request appear in the sidecar access logs?
>
> It should not appear because the filter captures only server errors. If you need both missing routes and backend failures, use `response.code >= 400` instead.

You can read access logs directly from the `istio-proxy` container. Direct log inspection is useful during a lab or when the centralized log backend is delayed, but production workflows normally forward these logs to a searchable backend.

```bash
kubectl logs deploy/productpage-v1 -c istio-proxy --tail=20
```

A text access log line can look dense because it compresses many facts into one record. Focus first on timestamp, method, path, response code, flags, duration, upstream host, and destination. Those fields usually tell you whether the proxy saw an application response, an Envoy-generated failure, or an upstream connection problem.

```text
[2026-04-26T10:30:45.123Z] "GET /reviews/0 HTTP/1.1" 200 - via_upstream
  "-" 0 295 24 23 "-" "curl/8.0" "abc-123" "reviews:9080"
  outbound|9080||reviews.default.svc.cluster.local 10.244.1.5:39012
  10.244.2.8:9080 10.244.1.5:33456 - default
```

| Field | What to inspect | Why it matters |
|---|---|---|
| Response code | `200`, `404`, `503`, `403` | Separates success, route misses, backend failures, and policy denials |
| Response flags | `-`, reset, timeout, upstream failure indicators | Shows whether Envoy generated or observed an abnormal condition |
| Duration | Request time in milliseconds | Helps connect logs to latency symptoms |
| Upstream cluster | `outbound|port||service` | Confirms the destination Envoy selected |
| Request ID | `x-request-id` value | Correlates logs with traces and application logs |
| Authority and path | Host and route path | Helps debug Gateway and VirtualService matching |

> **Active check:** A user reports a `503`, but the application container logs show no request. What access log clue suggests Envoy failed before the request reached the app?
>
> Look for non-empty response flags and upstream connection failure indicators in the sidecar access log. If Envoy could not connect to an upstream endpoint or timed out before the app handled the request, the application logs may be empty.

Access log format can be configured through mesh settings and providers. JSON encoding is easier for log systems to parse, while text is easier for a human to read quickly in a terminal. The right choice depends on the downstream log pipeline, not personal preference.

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    accessLogFile: /dev/stdout
    accessLogEncoding: JSON
```

Be careful with sensitive data. Proxies can observe headers and paths, and those may include tokens, account identifiers, or personal data if applications use unsafe URL patterns. Logging only error classes does not automatically remove sensitive content, so production teams should review formats, retention, and redaction rules.

Logs are a scalpel when filtered and a flood when enabled without intent. During incidents, prefer a workload-level filter that captures the suspicious condition. After the incident, remove or lower the logging scope so the temporary debugging configuration does not become permanent platform cost.

The privacy angle matters as much as the storage angle. Even if your access log format does not include request bodies, URLs and headers can carry sensitive identifiers when applications put account numbers, session hints, or tokens in unsafe places. Mesh operators should treat access logging as a production data flow with retention and review rules, not as a harmless terminal convenience. That mindset keeps observability useful without turning it into an accidental data exposure path.

---

## 6. Operate with Kiali, Grafana, and Jaeger Together

Kiali, Grafana, and Jaeger are not competing views of the same data. They are complementary tools that sit at different points in the debugging process. Kiali helps you see topology and Istio configuration health. Grafana helps you quantify behavior over time. Jaeger helps you inspect one sampled request path.

| Tool | Strength | Weakness | Best first use |
|---|---|---|---|
| Kiali | Service graph, mTLS badges, Istio config validation | Depends on metrics and may lag slightly | Verify who talks to whom and whether config looks suspicious |
| Grafana | Time-series dashboards and SLO panels | Requires good queries and labels | Confirm rate, error, and latency trends |
| Jaeger | Per-request path and span timing | Sampling means it may not show every request | Analyze one slow or failed request path |
| Envoy stats | Raw proxy metric endpoint | Per-pod and low-level | Separate proxy emission problems from scraping problems |
| Access logs | Concrete request records | Can be noisy and costly | Inspect filtered failures or policy denials |

Kiali is especially helpful after traffic-management changes. If a `VirtualService` should split traffic between `reviews-v1` and `reviews-v2`, Kiali can show whether traffic actually reaches both workloads. That graph view makes route mistakes visible faster than reading YAML line by line.

```bash
kubectl get svc -n istio-system kiali

kubectl port-forward svc/kiali -n istio-system 20001:20001
```

```bash
istioctl dashboard kiali
```

Grafana is better when the question involves time. If an incident started after a rollout, a dashboard can show whether error rate rose at the rollout time, whether latency rose only for one destination, and whether the issue is still happening. Dashboards should be designed around questions, not around every available metric.

```bash
kubectl port-forward svc/grafana -n istio-system 3000:3000
```

```bash
istioctl dashboard grafana
```

A custom Grafana panel can use the same PromQL you would run directly in Prometheus. This panel groups request rate by response code for a selected service, which helps separate normal traffic from client and server errors.

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

Jaeger is most useful after you have a representative request. A trace can show that the frontend was fast, checkout spent most of the time waiting for payments, and payments made a slow call to an external dependency. That is more actionable than saying "the site is slow."

```bash
kubectl port-forward svc/jaeger-query -n istio-system 16686:16686
```

> **Pause and predict:** A Grafana dashboard shows a rising P99 for `checkout`, but Kiali shows all nodes green. Which tool should you use next, and why?
>
> Use Jaeger or another tracing backend to inspect slow sampled requests, then confirm with workload-level latency queries. Kiali health color may not expose tail latency clearly, while traces can show which downstream hop contributes most of the slow path.

Kiali can also validate Istio configuration. It may flag a `VirtualService` that references a missing `Gateway`, a `DestinationRule` subset that does not match workload labels, or traffic flowing to an unexpected destination. This validation is runtime-oriented and complements `istioctl analyze`.

```bash
istioctl analyze -n default
```

```bash
kubectl get virtualservice,destinationrule,telemetry -A
```

> **Active check:** A `VirtualService` claims to send ten percent of traffic to `reviews-v2`, but Kiali shows only `reviews-v1` receiving traffic. What should you compare?
>
> Compare the `VirtualService` route destinations, the `DestinationRule` subset labels, and the actual Pod labels on `reviews-v2`. A subset name can be correct while the label selector behind it matches no Pods.

An effective incident workflow combines the tools in a deliberate order. Start with Grafana or Prometheus to prove the symptom and scope. Use Kiali to verify topology and route behavior. Use Jaeger to inspect one representative path. Use access logs to confirm exact proxy-observed request outcomes. Use `istioctl` and Kubernetes commands to inspect the configuration that explains the evidence.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         Practical Debugging Loop                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Symptom                                                                   │
│    │                                                                       │
│    ▼                                                                       │
│  Prometheus/Grafana: quantify rate, errors, duration                       │
│    │                                                                       │
│    ▼                                                                       │
│  Kiali: confirm topology, route split, mTLS, config warnings               │
│    │                                                                       │
│    ▼                                                                       │
│  Jaeger: inspect one slow or failed request path                           │
│    │                                                                       │
│    ▼                                                                       │
│  Access logs: verify exact proxy-observed request outcome                  │
│    │                                                                       │
│    ▼                                                                       │
│  Kubernetes and Istio config: change the smallest thing that explains data │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

This loop keeps you from guessing. Each tool narrows the problem until a configuration change, rollout fix, policy adjustment, or application bug becomes the most plausible next step.

The loop is intentionally reversible. If Jaeger suggests a backend is slow but Prometheus shows no broad latency increase, you may decide the trace is not representative and return to metrics with a different grouping. If Kiali shows an unexpected edge, you may jump back to access logs to confirm whether traffic is real user traffic, synthetic probes, or a misrouted call. Good operators move between tools because the evidence demands it, not because a fixed checklist says the next dashboard is mandatory.

---

## Did You Know?

- **Istio can emit request metrics without application code changes**, because Envoy sidecars observe traffic on the request path and export standard metrics for HTTP, gRPC, and TCP behavior.

- **Trace sampling and trace propagation solve different problems**, because sampling decides which requests are stored while propagation decides whether downstream spans join the same trace.

- **Kiali often reveals configuration mistakes through runtime behavior**, because it combines Istio resources, service graph data, traffic health, and security indicators instead of showing only static YAML.

- **Access log filters are an observability control, not just a cost control**, because filtering forces teams to define which request outcomes are important enough to preserve during normal operation.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Setting `100.0` trace sampling mesh-wide in production | Trace storage and collector load can spike across every service | Use low mesh defaults and raise sampling only for targeted namespaces or workloads |
| Forgetting to propagate trace headers in application code | Jaeger shows disconnected trace fragments even though Envoy creates spans | Forward B3 or W3C trace context headers through every outbound request |
| Querying Istio metrics without filtering `reporter` | Dashboards may double-count or mix source and destination perspectives | Choose `reporter="destination"` for service-side reliability views unless you need source perspective |
| Adding user or request identifiers as metric tags | Prometheus creates huge numbers of time series and becomes expensive or unstable | Put high-cardinality identifiers in logs or traces instead of metric labels |
| Applying workload Telemetry with labels that match only the Service | The resource applies but affects no Pods | Inspect Pod template labels and match `spec.selector.matchLabels` to those labels |
| Logging every request permanently in a busy mesh | Log volume overwhelms storage and makes failure records harder to find | Use filtered access logs and time-box verbose logging during investigations |
| Treating Kiali, Grafana, and Jaeger as interchangeable | Teams jump between tools without proving or narrowing a theory | Use metrics for scope, topology for flow, traces for paths, and logs for exact request records |
| Assuming a blank dashboard means Istio is broken | Prometheus scraping, traffic generation, injection, or query labels may be wrong | Verify sidecar stats directly before changing mesh telemetry configuration |

---

## Quiz

### Question 1

Your team deploys `checkout-v2` as a canary behind the existing `checkout` service. The service-level Grafana dashboard shows normal average latency, but a few users report slow checkouts. What query change would you make first, and why?

<details>
<summary>Show Answer</summary>

Break the latency query down by workload or version instead of aggregating the whole service. A canary can receive a small share of traffic, so service-level averages and even percentiles may hide its behavior. Query `istio_request_duration_milliseconds_bucket` with `reporter="destination"` and group by a label such as `destination_workload` or version if available.
</details>

### Question 2

A namespace-level Telemetry resource sets tracing to `25.0` percent for `payments`, and a workload-level Telemetry resource sets tracing to `100.0` percent for Pods labeled `app: fraud-checker`. During an incident, traces for `fraud-checker` are still sparse. What should you verify before changing the sampling value again?

<details>
<summary>Show Answer</summary>

Verify that the workload selector matches the actual Pod labels, that the Telemetry resource is in the same namespace as the workload, that the provider name exists in mesh configuration, and that enough traffic is reaching the workload. If traces are disconnected rather than sparse, also verify that applications propagate trace headers.
</details>

### Question 3

A developer reports that Jaeger shows one trace from `frontend` to `checkout` and a separate trace from `payments` to `inventory` for the same user action. Istio tracing is enabled and the sampling rate is high. What is the most likely cause, and what fix would you request?

<details>
<summary>Show Answer</summary>

The most likely cause is missing trace context propagation in one of the application hops, commonly between `checkout` and `payments`. Envoy can create spans, but the application or tracing library must forward B3 or W3C trace headers on outbound requests. The fix is to update the service's HTTP client or tracing middleware to propagate incoming trace headers.
</details>

### Question 4

A production service receives thousands of requests per second. Security asks for evidence of non-mTLS traffic, but the platform team does not want to log every request. How would you configure access logging for this investigation?

<details>
<summary>Show Answer</summary>

Use a targeted Telemetry resource with an access log filter such as `connection.mtls == false`, optionally combined with response-code conditions. Scope it to the relevant namespace or workload rather than the whole mesh if possible. This captures the security-relevant requests without turning every successful mTLS request into a log record.
</details>

### Question 5

A dashboard panel for `reviews.default.svc.cluster.local` shows twice the request rate expected from load-test traffic. The query sums `istio_requests_total` but does not filter on `reporter`. What is wrong with the query, and how would you correct it?

<details>
<summary>Show Answer</summary>

The query is likely mixing source and destination reporter series, which can double-count or otherwise distort the result. Filter explicitly on one perspective, usually `reporter="destination"` for service-side request rate. Then keep the same reporter choice across related rate, error, and latency panels.
</details>

### Question 6

After applying a `VirtualService` that should route some traffic to `reviews-v2`, Kiali still shows all traffic going to `reviews-v1`. The Pods are healthy. Which configuration relationships should you inspect?

<details>
<summary>Show Answer</summary>

Inspect the `VirtualService` route destinations, the `DestinationRule` subsets, and the actual Pod labels for `reviews-v2`. A route can reference a subset name that exists in YAML but whose labels match no Pods. Also confirm that traffic is entering through the host and gateway the `VirtualService` actually matches.
</details>

### Question 7

A team says their Prometheus dashboard is empty after enabling Telemetry. You can exec into the `istio-proxy` container and see `istio_requests_total` at `127.0.0.1:15020/stats/prometheus`. What does that prove, and where should you investigate next?

<details>
<summary>Show Answer</summary>

It proves Envoy is emitting the metric from the sidecar, so the next investigation should focus on Prometheus scraping, target discovery, relabeling, or dashboard query labels. Check Prometheus targets for the `istio-proxy` Pods and confirm the scrape path and address rewrite point to port `15020`.
</details>

---

## Hands-On Exercise: Configure and Debug Istio Observability

### Objective

Configure telemetry for a running Istio mesh, generate traffic, verify raw Envoy metrics, inspect filtered access logs, and practice choosing the right observability signal for a failure scenario.

This exercise uses the Bookinfo sample because it has multiple services and enough request flow to make metrics, topology, and traces meaningful. The commands assume a local Kubernetes cluster with Istio installed using a profile that includes or allows observability addons. If your environment uses external Prometheus, Grafana, or tracing, adapt only the addon access commands.

### Setup

Run the setup commands from a shell with access to your cluster. The commands use the full `kubectl` binary name so they work when copied into a non-interactive script as well as in an interactive terminal.

```bash
istioctl install --set profile=demo -y

kubectl label namespace default istio-injection=enabled --overwrite

kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.27/samples/bookinfo/platform/kube/bookinfo.yaml

kubectl wait --for=condition=ready pod -l app=productpage --timeout=180s

kubectl wait --for=condition=ready pod -l app=reviews --timeout=180s

kubectl wait --for=condition=ready pod -l app=ratings --timeout=180s
```

Generate baseline traffic before you inspect metrics. Without traffic, many request metrics will be absent or uninteresting.

```bash
for i in $(seq 1 30); do
  kubectl exec deploy/ratings-v1 -- curl -s productpage:9080/productpage > /dev/null
done
```

### Task 1: Apply Mesh-Wide Telemetry Defaults

Apply a mesh-wide Telemetry resource that enables Prometheus metrics, configures tracing at a moderate lab sampling rate, and enables access logging. In production, you would normally use lower tracing and more selective logging, but the lab starts visibly so you can verify the signal path.

```bash
kubectl apply -f - <<'EOF'
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: mesh-observability-defaults
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

Verify that the resource exists.

```bash
kubectl get telemetry -n istio-system mesh-observability-defaults -o yaml
```

### Task 2: Create a Namespace Debug Override

Create a namespace-level tracing override for the `default` namespace. This simulates a temporary investigation where the application team needs more traces for Bookinfo without changing the mesh-wide default.

```bash
kubectl apply -f - <<'EOF'
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: default-debug-tracing
  namespace: default
spec:
  tracing:
    - providers:
        - name: zipkin
      randomSamplingPercentage: 25.0
EOF
```

Check that both Telemetry resources exist at their expected scopes.

```bash
kubectl get telemetry -A
```

### Task 3: Filter Productpage Access Logs

Apply a workload-level Telemetry resource that logs only errors for `productpage`. Before applying it, inspect the Pod labels so you can confirm the selector matches the workload.

```bash
kubectl get pods -l app=productpage --show-labels
```

```bash
kubectl apply -f - <<'EOF'
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: productpage-error-logs
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

Generate one successful request and one missing-page request. The missing-page request should be more likely to appear under the error-only filter.

```bash
kubectl exec deploy/ratings-v1 -- curl -s -o /dev/null -w '%{http_code}\n' productpage:9080/productpage

kubectl exec deploy/ratings-v1 -- curl -s -o /dev/null -w '%{http_code}\n' productpage:9080/does-not-exist
```

Inspect the productpage sidecar logs.

```bash
kubectl logs deploy/productpage-v1 -c istio-proxy --tail=20
```

### Task 4: Verify Raw Envoy Metrics

Check the sidecar stats endpoint directly. This tells you whether Envoy is emitting metrics before you debug Prometheus or Grafana.

```bash
kubectl exec deploy/productpage-v1 -c istio-proxy -- \
  curl -s 127.0.0.1:15020/stats/prometheus | grep '^istio_requests_total' | head -10
```

If the command returns nothing, generate more traffic and retry.

```bash
for i in $(seq 1 20); do
  kubectl exec deploy/ratings-v1 -- curl -s productpage:9080/productpage > /dev/null
done

kubectl exec deploy/productpage-v1 -c istio-proxy -- \
  curl -s 127.0.0.1:15020/stats/prometheus | grep '^istio_requests_total' | head -10
```

### Task 5: Practice PromQL Reasoning

If Prometheus is installed in your Istio system namespace, port-forward it and run the queries in the UI. Use `127.0.0.1` in the browser address.

```bash
kubectl port-forward svc/prometheus -n istio-system 9090:9090
```

Open `http://127.0.0.1:9090` and run a request-rate query for the Bookinfo productpage service.

```promql
sum(rate(istio_requests_total{
  reporter="destination",
  destination_service="productpage.default.svc.cluster.local"
}[5m]))
```

Run an error-rate query. If your generated traffic did not produce errors through the same service identity, adjust the destination service or generate more failed requests.

```promql
sum(rate(istio_requests_total{
  reporter="destination",
  destination_service="productpage.default.svc.cluster.local",
  response_code=~"5.*"
}[5m]))
/
sum(rate(istio_requests_total{
  reporter="destination",
  destination_service="productpage.default.svc.cluster.local"
}[5m]))
```

Run a latency query. Then change the grouping to include `destination_workload` and compare what the query can reveal.

```promql
histogram_quantile(0.95,
  sum(rate(istio_request_duration_milliseconds_bucket{
    reporter="destination",
    destination_service="productpage.default.svc.cluster.local"
  }[5m])) by (le)
)
```

### Task 6: Inspect Topology and Traces

Open Kiali if the addon is present. Use it to verify that Bookinfo services are connected and traffic is flowing between `productpage`, `details`, `reviews`, and `ratings`.

```bash
istioctl dashboard kiali
```

If a tracing backend is present, open it and look for recent Bookinfo traces. Generate additional traffic if no traces appear, then check whether spans are connected across services.

```bash
for i in $(seq 1 40); do
  kubectl exec deploy/ratings-v1 -- curl -s productpage:9080/productpage > /dev/null
done

istioctl dashboard jaeger
```

When reviewing a trace, identify the slowest span, the response code, and whether the request path includes all expected services. If the trace breaks into fragments, connect that observation to header propagation rather than assuming the backend is down.

### Task 7: Diagnose a Designed Failure

Create a short failure investigation using the signals you configured. The goal is not to memorize the answer, but to practice moving from symptom to evidence.

Generate a failed request.

```bash
kubectl exec deploy/ratings-v1 -- curl -s -o /dev/null -w '%{http_code}\n' productpage:9080/does-not-exist
```

Use access logs to confirm whether the proxy recorded the failed request.

```bash
kubectl logs deploy/productpage-v1 -c istio-proxy --tail=30
```

Use Prometheus or raw Envoy metrics to decide whether the failure affected one request or a broader pattern. Use Kiali to confirm that the service graph still shows expected traffic flow. If tracing is available, look for a sampled request and decide whether it adds useful information beyond the log.

### Success Criteria

- [ ] A mesh-wide Telemetry resource exists in `istio-system` and configures metrics, tracing, and access logging.
- [ ] A namespace-level Telemetry resource exists in `default` and overrides tracing without changing the mesh-wide default.
- [ ] A workload-level Telemetry resource selects `productpage` Pods and filters access logs to error responses.
- [ ] You can explain why workload Telemetry is more specific than namespace and mesh-wide Telemetry.
- [ ] You can retrieve `istio_requests_total` directly from the Envoy stats endpoint on port `15020`.
- [ ] You can write or evaluate a PromQL request-rate query using `reporter="destination"`.
- [ ] You can write or evaluate an error-rate query that divides server-error requests by total requests for the same service.
- [ ] You can explain why disconnected traces usually indicate missing header propagation rather than missing Envoy spans.
- [ ] You can choose between Kiali, Grafana, Jaeger, and access logs for a specific troubleshooting question.

### Cleanup

Remove the Telemetry resources and Bookinfo sample when you finish. The cleanup intentionally names each resource explicitly so you do not delete unrelated observability configuration.

```bash
kubectl delete telemetry mesh-observability-defaults -n istio-system

kubectl delete telemetry default-debug-tracing -n default

kubectl delete telemetry productpage-error-logs -n default

kubectl delete -f https://raw.githubusercontent.com/istio/istio/release-1.27/samples/bookinfo/platform/kube/bookinfo.yaml
```

If you installed Istio only for this lab and no other module needs it, you can uninstall it separately.

```bash
istioctl uninstall --purge -y

kubectl delete namespace istio-system
```

---

## Sources

- https://istio.io/latest/docs/tasks/observability/
- https://istio.io/latest/docs/tasks/observability/metrics/
- https://istio.io/latest/docs/tasks/observability/logs/access-log/
- https://istio.io/latest/docs/tasks/observability/distributed-tracing/
- https://istio.io/latest/docs/reference/config/telemetry/
- https://istio.io/latest/docs/reference/config/metrics/
- https://istio.io/latest/docs/ops/integrations/prometheus/
- https://istio.io/latest/docs/ops/integrations/grafana/
- https://istio.io/latest/docs/ops/integrations/kiali/
- https://istio.io/latest/docs/ops/integrations/jaeger/
- https://istio.io/latest/docs/examples/bookinfo/
- https://prometheus.io/docs/practices/histograms/

---

## Next Module

You have completed the ICA observability module and the core ICA sequence. Use the next review step to connect installation, traffic management, security, troubleshooting, and observability into one operating model.

Next: [ICA Track Review](../)

For deeper practice, revisit these modules and ask the same operational question in each one: "What evidence would prove that this configuration behaves as intended?"

- [Module 1: Installation & Architecture](../module-1.1-istio-installation-architecture/) — verify injection, proxy readiness, and control-plane health.
- [Module 2: Traffic Management](../module-1.2-istio-traffic-management/) — verify route matches, subsets, retries, timeouts, and traffic splits.
- [Module 3: Security & Troubleshooting](../module-1.3-istio-security-troubleshooting/) — verify mTLS state, authorization decisions, and proxy configuration.
- [This module](./) — verify metrics, logs, traces, topology, and dashboard queries.

### Final ICA Observability Checklist

- [ ] I can decide whether a telemetry change belongs at mesh, namespace, or workload scope.
- [ ] I can avoid high-cardinality metric labels and explain why they are dangerous.
- [ ] I can query request rate, server-error rate, and latency using Istio standard metrics.
- [ ] I can explain when to use `reporter="destination"` and when source-side metrics may be useful.
- [ ] I can configure trace sampling and explain why sampling does not replace header propagation.
- [ ] I can identify disconnected traces as a propagation or path problem to investigate.
- [ ] I can enable filtered access logs for errors, slow requests, or non-mTLS traffic.
- [ ] I can read an Envoy access log line well enough to identify response code, flags, duration, and upstream destination.
- [ ] I can use Kiali to validate service graph behavior, mTLS indicators, and Istio config warnings.
- [ ] I can use Grafana or Prometheus to prove whether a symptom is broad, isolated, improving, or worsening.
- [ ] I can use Jaeger to inspect a representative request path and then validate the pattern with metrics.
- [ ] I can combine observability signals into a disciplined debugging loop instead of guessing from one dashboard.

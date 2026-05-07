---
title: "Module 1.1: Prometheus"
slug: platform/toolkits/observability-intelligence/observability/module-1.1-prometheus
sidebar:
  order: 2
---

# Module 1.1: Prometheus

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

## Prerequisites

Before starting this module, you should be comfortable with Kubernetes Services, labels, selectors, Pods, Deployments, and basic HTTP request behavior.

You should also have completed the [Observability Theory Track](/platform/foundations/observability-theory/) or have equivalent experience with metrics, logs, traces, and SLO language.

The [SRE Discipline](/platform/disciplines/core-platform/sre/) module is recommended because this lesson connects Prometheus mechanics to incident response, alert design, and operational ownership.

Examples target Kubernetes 1.35+ and assume you can run `kubectl` against a disposable cluster where you are allowed to install monitoring components.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Debug** a missing Prometheus target by tracing the path from Kubernetes labels and annotations through service discovery and relabeling.
- **Design** PromQL queries that turn raw counters and histograms into request-rate, error-ratio, and latency signals for SLO dashboards.
- **Evaluate** when to use raw queries, recording rules, alerting rules, federation, and remote write in a production observability architecture.
- **Optimize** a Prometheus deployment by identifying high-cardinality metrics, unsafe labels, and expensive dashboard patterns before they cause outages.
- **Implement** a working Prometheus setup in Kubernetes, deploy a sample metrics endpoint, and verify that alerts are based on the same signals taught in the module.

---

## Why This Module Matters

At 02:18, a platform team at a large subscription commerce company sees checkout latency rise across three regions while Kubernetes still reports every Deployment as healthy. The application pods are running, readiness probes are green, and the load balancer is still accepting traffic, but customers are abandoning carts because confirmation pages take several seconds to load. The incident commander needs a way to compare request rate, error ratio, database latency, and pod restarts across thousands of time series without reading logs from every replica.

Prometheus gives that team a working map of the system while the system is changing under pressure. It does not merely store numbers; it continuously asks every discovered target for current measurements, labels those measurements with operational context, and lets engineers ask focused questions such as "which service is producing most 5xx responses" or "which latency bucket crossed the SLO boundary." When those questions are designed well, the team can move from vague outage symptoms to a narrow hypothesis in minutes.

The difficult part is that Prometheus rewards precise thinking and punishes casual configuration. A single mismatched Service selector can make an application invisible, a single unbounded label can create millions of time series, and a single noisy alert can train an on-call rotation to ignore real symptoms. This module teaches Prometheus as a production tool: how it collects data, how PromQL builds answers step by step, and how platform engineers keep the monitoring system trustworthy when the environment grows.

---

## Prometheus as an Operating Model

Prometheus is a metrics system built around a simple contract: [targets expose measurements over HTTP, and the Prometheus server periodically scrapes those targets](https://prometheus.io/docs/introduction/overview/). This pull model sounds modest, but it changes how operators reason about availability. If Prometheus cannot scrape a target, the failure itself becomes observable through the `up` metric, which is often the first signal that a network policy, Service selector, endpoint, or application process has broken.

The pull model also centralizes scrape frequency, timeout behavior, target labels, and failure visibility inside the monitoring system. Application teams do not need to embed a complex agent that knows where the monitoring backend lives, and platform teams can inspect the target list from the Prometheus UI during an incident. The trade-off is reachability: Prometheus must be able to make an HTTP request to each target, so private networks, pod security, and service discovery rules become part of the monitoring design.

```ascii
+--------------------------------------------------------------------------------+
|                         PROMETHEUS OPERATING MODEL                             |
+--------------------------------------------------------------------------------+
|                                                                                |
|  Kubernetes API          Service Discovery             Prometheus Server        |
|  +-------------+         +----------------+            +--------------------+   |
|  | Pods        | labels  | target groups  | relabel    | scrape scheduler   |   |
|  | Services    +-------->+ metadata       +----------->+ retrieval engine   |   |
|  | Endpoints   |         | annotations    |            | local TSDB         |   |
|  +------+------+         +-------+--------+            | PromQL API         |   |
|         |                        |                     +-----+--------------+   |
|         |                        |                           |                  |
|         |                        |                           | alert queries    |
|         |                        |                           v                  |
|  +------v------+          +------v------+              +-----+--------------+   |
|  | App /metrics|<---------+ scrape HTTP |              | Alertmanager       |   |
|  | Exporters   |          | every N sec |              | group, route, mute |   |
|  +-------------+          +-------------+              +--------------------+   |
|                                                                                |
+--------------------------------------------------------------------------------+
```

A useful mental model is to treat Prometheus as a controlled polling engine plus a label-aware database. The polling engine decides what exists and whether it can be reached, while the database stores samples with metric names and labels. PromQL then works over those labeled samples, so the quality of the answer depends heavily on the quality of labels chosen during instrumentation and service discovery.

The local storage engine, often called the TSDB, stores time series as samples over time. [A time series is not just a metric name; it is the metric name plus one exact set of labels.](https://prometheus.io/docs/concepts/) `http_requests_total{service="checkout",status="500"}` and `http_requests_total{service="checkout",status="200"}` are different series, which is why label design becomes an operational concern rather than a documentation detail.

> **Stop and think:** If a platform team adds `user_id` as a label to every HTTP request metric, how many new time series could one busy endpoint create in a day, and what part of Prometheus would feel that cost first?

The answer is that Prometheus would create a separate series for each unique label combination, and those series must be indexed in memory before they are useful. Disk size matters, but the immediate pain is often memory pressure and slow queries because the active head block must track a large number of changing series. Good Prometheus practice therefore starts before installation: decide which labels help operators aggregate and compare behavior, and reject labels that identify individual requests, users, sessions, or other unbounded values.

| Component | What it does | Production question it answers |
|-----------|--------------|--------------------------------|
| Prometheus server | Scrapes targets, stores samples, evaluates rules, and serves PromQL | Can we collect, query, and evaluate the signals we need during an outage? |
| Service discovery | Converts platform metadata into scrape targets | Can Prometheus find every workload that should expose metrics? |
| Relabeling | Keeps, drops, rewrites, and enriches targets or samples | Are target labels stable, useful, and low-cardinality? |
| TSDB | Stores time-series samples locally in blocks | How long can this server retain data before disk or memory becomes a constraint? |
| Alertmanager | Groups, deduplicates, silences, and routes alerts | Can the right human receive one actionable notification instead of many noisy ones? |
| Exporters | Translate external systems into Prometheus metrics | Can we observe systems that do not natively expose Prometheus metrics? |
| Recording rules | Precompute expensive or reused PromQL expressions | Can dashboards stay fast and consistent as query volume increases? |
| Remote write | Streams samples to another long-term system | Can we keep durable historical data without overloading local Prometheus storage? |

Prometheus is not a log database, a distributed tracing backend, or a general analytics warehouse. It is strongest when the question can be expressed as a numeric time series with useful labels, such as requests per second by service, error ratio by route family, or p99 latency by dependency. If the question requires reconstructing a single user journey, you probably need traces; if it requires reading stack traces or payloads, you probably need logs.

That boundary matters because many teams try to compensate for weak traces or logs by adding more labels to metrics. They add request identifiers, tenant names, raw paths, or exception messages to metrics because those values feel useful during debugging. The result is a metrics system that becomes expensive exactly when traffic is highest, and the team loses the fast aggregate view that Prometheus was meant to provide.

---

## Scraping, Targets, and the Pull Model

A scrape is an HTTP request from Prometheus to a target endpoint, usually `/metrics`, where the target returns measurements in the Prometheus exposition format. Each scrape produces a batch of samples at one point in time, and [Prometheus attaches labels such as `job` and `instance` before storing them. When scrapes fail, Prometheus records `up{...} == 0`](https://prometheus.io/docs/concepts/jobs_instances/), which gives operators a direct way to distinguish "the app is reporting bad numbers" from "the monitoring system cannot reach the app."

A typical Kubernetes scrape path begins with metadata, not with HTTP. [Prometheus asks the Kubernetes API for Pods, Services, Endpoints, or EndpointSlices, then relabeling rules decide which discovered objects become scrape targets.](https://prometheus.io/docs/prometheus/latest/configuration/configuration/) This distinction is essential: a healthy application can be invisible to Prometheus if service discovery filters it out, and a dead endpoint can remain visible if stale metadata still matches the discovery rule until Kubernetes updates the endpoint list.

```ascii
+--------------------------------------------------------------------------------+
|                         FROM KUBERNETES OBJECT TO SAMPLE                       |
+--------------------------------------------------------------------------------+
|                                                                                |
|  1. Pod has labels and annotations                                             |
|     app.kubernetes.io/name=checkout                                            |
|     prometheus.io/scrape=true                                                  |
|                                                                                |
|           |                                                                    |
|           v                                                                    |
|  2. Kubernetes service discovery emits meta labels                             |
|     __meta_kubernetes_pod_label_app_kubernetes_io_name=checkout                |
|     __meta_kubernetes_pod_annotation_prometheus_io_scrape=true                 |
|                                                                                |
|           |                                                                    |
|           v                                                                    |
|  3. Relabel rules keep or drop the target and rewrite scrape address           |
|     keep only prometheus.io/scrape=true                                        |
|     set __metrics_path__ from prometheus.io/path                               |
|                                                                                |
|           |                                                                    |
|           v                                                                    |
|  4. Prometheus scrapes http://pod-ip:port/metrics                              |
|     stores http_requests_total{job="kubernetes-pods",pod="checkout-abc"}       |
|                                                                                |
+--------------------------------------------------------------------------------+
```

Pull and push models both appear in monitoring systems, and neither is universally superior. Prometheus chooses pull for normal services because it makes target health visible and gives the server control over scrape intervals. [Pushgateway exists for short-lived batch jobs that would disappear before Prometheus could scrape them, but it should not become the default path for long-running services](https://prometheus.io/docs/practices/pushing/) because it weakens the clean "can I reach this target" signal.

```ascii
+------------------------------------+    +------------------------------------+
| PULL MODEL                         |    | PUSH MODEL                         |
| Prometheus -> target /metrics       |    | Agent or job -> monitoring backend |
+------------------------------------+    +------------------------------------+
| Target health is visible as up      |    | Sender may vanish silently         |
| Scrape interval is centrally owned  |    | Sender controls send behavior      |
| Easy to inspect with curl           |    | Useful behind some network limits  |
| Requires target reachability        |    | Useful for short-lived jobs        |
+------------------------------------+    +------------------------------------+
```

When you debug a scrape problem, start with the target lifecycle rather than the dashboard. A blank Grafana panel may mean the query is wrong, the metric name changed, the target disappeared, the scrape endpoint returns an error, or relabeling dropped the target before any scrape happened. Prometheus exposes each stage through its own UI pages and internal metrics, so a disciplined investigation can narrow the failure without guessing.

A senior operational habit is to use the Prometheus target page as a contract test for monitoring coverage. If a team ships a new service, the target should appear with the expected labels, the expected scrape interval, and a recent successful scrape time. If the target does not appear, the problem is often outside application code, and the fastest path is to inspect labels, Service selectors, endpoint names, and relabeling decisions.

> **Pause and predict:** A Deployment has the annotation `prometheus.io/scrape: "true"`, but the Pod template exposes port name `web` while the ServiceMonitor endpoint expects port name `metrics`. Would you expect Prometheus to scrape it successfully, and where would you look first?

You should predict a discovery or endpoint mismatch rather than an application instrumentation bug. The Pod can expose a `/metrics` handler correctly and still fail discovery if Prometheus is configured to look through Services and the Service endpoint does not have the port name selected by the monitor. In that case, checking the Service, EndpointSlice, and ServiceMonitor selector is more useful than reading application logs.

The simplest manual scrape test is still valuable because it removes Prometheus from the path. If you can port-forward to the service and fetch `/metrics`, the application endpoint works. If Prometheus still cannot scrape it, the remaining problem is likely service discovery, relabeling, RBAC, networking, or the address and port Prometheus derived from metadata.

```bash
kubectl -n monitoring port-forward svc/example-app 8080:80
curl -fsS http://127.0.0.1:8080/metrics | head
```

After the endpoint works manually, inspect the Prometheus target labels. Labels such as `job`, `instance`, `namespace`, `service`, `pod`, and application-specific labels are the bridge between target discovery and PromQL. A query that filters on `app="checkout"` will return nothing if the actual label is `app_kubernetes_io_name="checkout"` or `service="checkout-api"`.

---

## Worked Example: Building PromQL From a Symptom

PromQL becomes much less intimidating when you build queries in layers. The mistake beginners make is to jump directly to a full SLO expression and then wonder which part is wrong. A better approach is to start with one raw metric, confirm labels, convert counters into rates, aggregate away noisy instance labels, and only then combine numerator and denominator into a ratio.

Imagine the checkout team reports that customers see intermittent failures after a new release. The service exposes a counter named `http_requests_total` with labels `service`, `route`, `method`, and `status`. The operational question is not "what is the metric value" because a counter only increases; the question is "what fraction of recent requests failed for checkout, grouped in a way that supports a rollback decision."

Step one is to confirm that the metric exists and that the labels match your mental model. This raw selector is not a final dashboard query, but it is a useful inspection step because it shows the series Prometheus has stored. If this returns nothing, you do not yet have a PromQL math problem; you have a metric name, label, scrape, or discovery problem.

```promql
http_requests_total{service="checkout"}
```

Step two is to filter the failure series. Most HTTP dashboards treat 5xx as server-side errors, while 4xx may represent client behavior, authentication failures, or validation errors that need a different SLO decision. The regex matcher keeps the query compact, but it also makes the label dependency explicit: this works only if the application uses status codes as label values.

```promql
http_requests_total{service="checkout",status=~"5.."}
```

Step three is to convert the counter into a per-second rate over a range window. Counters reset when a process restarts, so subtracting two raw samples by hand is fragile. [`rate()` understands counter resets and estimates the average per-second increase across the selected time range.](https://prometheus.io/docs/prometheus/2.55/querying/functions/)

```promql
rate(http_requests_total{service="checkout",status=~"5.."}[5m])
```

Step four is to aggregate across pods and instances because the incident commander usually needs service behavior, not a separate time series for every replica. Keeping `route` can be useful when one route is failing, but keeping `pod` or `instance` in the first dashboard view often adds noise. The correct aggregation depends on the decision you need to make.

```promql
sum by (service, route) (
  rate(http_requests_total{service="checkout",status=~"5.."}[5m])
)
```

Step five is to build the denominator with the same grouping shape. This is where many broken SLO queries are born: the numerator groups by route while the denominator groups only by service, or one side keeps a label that the other side does not. PromQL vector matching rules can produce confusing results when label sets do not line up, so make the grouping intentionally symmetrical.

```promql
sum by (service, route) (
  rate(http_requests_total{service="checkout"}[5m])
)
```

Step six is to divide the failure rate by the total request rate. The result is an error ratio, not a percentage, so `0.02` means two percent. This expression is finally useful for alerting, dashboard panels, and release analysis because it asks a question aligned with an SLO: "what fraction of recent checkout requests failed."

```promql
sum by (service, route) (
  rate(http_requests_total{service="checkout",status=~"5.."}[5m])
)
/
sum by (service, route) (
  rate(http_requests_total{service="checkout"}[5m])
)
```

The same layering pattern works for latency histograms. [Histograms store cumulative bucket counters, so you first rate the bucket counters, then aggregate by the labels that should define one distribution, and then ask `histogram_quantile()` to estimate the percentile. The `le` label must remain in the aggregation because it identifies the bucket boundaries.](https://prometheus.io/docs/prometheus/2.55/querying/functions/)

```promql
histogram_quantile(
  0.99,
  sum by (service, route, le) (
    rate(http_request_duration_seconds_bucket{service="checkout"}[5m])
  )
)
```

> **Stop and think:** If you remove `le` from the `sum by (...)` clause before calling `histogram_quantile()`, what information did you destroy, and why can Prometheus no longer estimate a percentile?

You destroyed the bucket boundary labels that describe how many requests were less than or equal to each latency threshold. Without those boundaries, Prometheus has only a merged number and cannot reconstruct the distribution. This is a common example of a query that is syntactically close to correct but semantically wrong because it aggregates away the label that gives the function meaning.

`rate()` and `irate()` are both useful, but they answer different operational questions. [`rate()` uses the full range and is therefore better for alerting, SLOs, and dashboards that should not flap on a single scrape. `irate()` uses the last two samples and is better for short debugging sessions where you want to see an immediate spike while accepting that the value is noisy.](https://prometheus.io/docs/prometheus/3.9/querying/functions/)

```ascii
+--------------------------------------------------------------------------------+
|                              RATE AND IRATE                                    |
+--------------------------------------------------------------------------------+
|                                                                                |
|  rate(counter[5m])                                                              |
|  + uses samples across the selected range                                       |
|  + smooths short spikes and scrape jitter                                       |
|  + fits alerts, SLO panels, and capacity trends                                 |
|                                                                                |
|  irate(counter[5m])                                                             |
|  + uses the last two samples inside the selected range                          |
|  + reacts quickly to sudden changes                                             |
|  + fits interactive investigation, not stable paging rules                      |
|                                                                                |
+--------------------------------------------------------------------------------+
```

A practical rule is that alerting queries should be boring. They should evaluate the same way during a quiet morning and a busy incident, tolerate one missed scrape, and map clearly to a human action. If a query requires a long explanation during a post-incident review, it may belong as a dashboard investigation query rather than a paging alert.

PromQL also has failure modes around empty vectors and division by zero. If a denominator has no matching series, the result may disappear instead of returning zero, which can hide absence as well as failure. Senior teams often pair SLO alerts with target coverage alerts so they know whether a clean error-ratio panel reflects healthy service behavior or missing telemetry.

```promql
up{job="kubernetes-pods",service="checkout"} == 0
```

Recording rules become useful once a query is expensive, reused, or semantically important. Instead of repeating the same service request-rate expression across several dashboards and alerts, [you can evaluate it once and store the result as a new time series. That improves query speed, reduces repeated work, and creates a stable vocabulary for operational signals.](https://prometheus.io/docs/practices/rules/)

```yaml
groups:
  - name: checkout-recording-rules
    interval: 30s
    rules:
      - record: service_route:http_requests:rate5m
        expr: |
          sum by (service, route) (
            rate(http_requests_total[5m])
          )
      - record: service_route:http_errors:rate5m
        expr: |
          sum by (service, route) (
            rate(http_requests_total{status=~"5.."}[5m])
          )
      - record: service_route:http_error_ratio:rate5m
        expr: |
          service_route:http_errors:rate5m
          /
          service_route:http_requests:rate5m
```

Recording rule names should encode the aggregation and range because they become part of your platform language. A name such as `service_route:http_error_ratio:rate5m` tells the reader that the series is grouped by service and route, represents an error ratio, and was built from a five-minute rate. That is easier to review than a dashboard panel containing a dense expression nobody recognizes.

---

## Worked Example: Fixing Kubernetes Service Discovery

Service discovery failures are common because Kubernetes gives you several layers of naming and selection. A Deployment has Pod template labels, a Service has a selector, an EndpointSlice reflects actual ready endpoints, and a ServiceMonitor or scrape configuration has its own selector. Prometheus does not scrape "the app" in the abstract; it scrapes a concrete address and port produced by those layers.

Consider a team that deploys `payment-api` and expects Prometheus to scrape it through the Prometheus Operator. The Deployment uses the recommended Kubernetes label `app.kubernetes.io/name: payment-api`, but the ServiceMonitor was copied from an older service that selected `app: payment-api`. The application is healthy, `/metrics` works locally, and yet Prometheus shows no target for the service.

First inspect the workload labels that actually exist on the Pods. The important point is to read the Pod template labels, not only the Deployment metadata labels, because Services select Pods. A label mismatch at this layer prevents the Service from building endpoints even if the Deployment object itself looks correct.

```bash
kubectl -n payments get pods -l app.kubernetes.io/name=payment-api --show-labels
kubectl -n payments get pods -l app=payment-api --show-labels
```

If the first command returns Pods and the second command returns none, the Service or ServiceMonitor must use the modern label key. Next inspect the Service selector and endpoints. If the Service selector is wrong, the ServiceMonitor may select the Service object but Prometheus still has no usable backend endpoints to scrape.

```bash
kubectl -n payments get service payment-api -o yaml
kubectl -n payments get endpointslice -l kubernetes.io/service-name=payment-api
```

A correct Service for the example should select the same label used by the Pod template and should name the metrics port consistently. [The port name matters because many ServiceMonitor configurations select endpoints by port name rather than by number.](https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/Documentation/api-reference/api.md) A numeric port mismatch is visible, but a name mismatch is easier to overlook during review.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: payment-api
  namespace: payments
  labels:
    app.kubernetes.io/name: payment-api
spec:
  selector:
    app.kubernetes.io/name: payment-api
  ports:
    - name: metrics
      port: 8080
      targetPort: metrics
```

Now inspect the ServiceMonitor selector. The selector matches Service labels, not Pod labels, which is another common source of confusion. [The ServiceMonitor below selects Services labeled `app.kubernetes.io/name: payment-api`, then scrapes the endpoint named `metrics` at `/metrics` every fifteen seconds.](https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/Documentation/api-reference/api.md)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: payment-api
  namespace: payments
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: payment-api
  namespaceSelector:
    matchNames:
      - payments
  endpoints:
    - port: metrics
      path: /metrics
      interval: 15s
      scrapeTimeout: 10s
```

The `release` label in this example is not universal; it depends on how your Prometheus Operator installation selects ServiceMonitor resources. [Many Helm installations of `kube-prometheus-stack` configure Prometheus to select monitors with a release label matching the Helm release name.](https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/README.md) If your monitor is valid but Prometheus ignores it, inspect the Prometheus custom resource selector before changing application code.

```bash
kubectl -n monitoring get prometheus -o yaml
kubectl -n payments get servicemonitor payment-api -o yaml
```

> **Pause and predict:** If the ServiceMonitor selector matches the Service, but the Service has zero EndpointSlice addresses, should the target page show a healthy scrape, a failed scrape, or no target at all?

In most operator-managed configurations, you should expect no useful target because the discovery pipeline has no concrete endpoint address to scrape. That points you back to the Service selector, Pod readiness, named ports, and EndpointSlice contents. A failed scrape is more likely when a target address exists but the HTTP request times out, returns an error, or exposes metrics on a different path.

The annotation-based approach follows the same logic but uses Pod annotations instead of ServiceMonitor custom resources. It is common in lightweight setups and tutorials, but larger platforms often prefer ServiceMonitor because it separates monitoring intent from application Pod templates. Either approach can work if the labels, ports, and paths are tested as part of deployment.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
  namespace: payments
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: payment-api
  template:
    metadata:
      labels:
        app.kubernetes.io/name: payment-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: payment-api
          image: quay.io/brancz/prometheus-example-app:v0.3.0
          ports:
            - name: metrics
              containerPort: 8080
```

[Raw Prometheus `kubernetes_sd_configs` expose Kubernetes metadata as labels beginning with `__meta_kubernetes_`.](https://prometheus.io/docs/prometheus/latest/configuration/configuration/) Relabeling rules can keep only annotated Pods, set the metrics path, and copy useful Kubernetes labels into normal labels. This is powerful, but it is also sharp: one incorrect `keep` rule can drop every target before the scrape stage.

```yaml
scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels:
          - __meta_kubernetes_pod_annotation_prometheus_io_scrape
        action: keep
        regex: "true"
      - source_labels:
          - __meta_kubernetes_pod_annotation_prometheus_io_path
        action: replace
        target_label: __metrics_path__
        regex: "(.+)"
      - source_labels:
          - __address__
          - __meta_kubernetes_pod_annotation_prometheus_io_port
        action: replace
        target_label: __address__
        regex: "([^:]+)(?::\\d+)?;(\\d+)"
        replacement: "$1:$2"
      - source_labels:
          - __meta_kubernetes_namespace
        action: replace
        target_label: namespace
      - source_labels:
          - __meta_kubernetes_pod_name
        action: replace
        target_label: pod
      - source_labels:
          - __meta_kubernetes_pod_label_app_kubernetes_io_name
        action: replace
        target_label: service
```

Read that configuration as a sequence of transformations rather than a blob of YAML. The first rule keeps only Pods that opted into scraping. The second rule changes the path if the annotation exists. The third rule constructs the host and port Prometheus will call. The final rules copy Kubernetes context into stable labels that PromQL can use.

A service discovery fix is complete only when you verify the full path. Check that the Pod exposes metrics, the Service selects the Pod, the EndpointSlice contains addresses, the ServiceMonitor selects the Service, Prometheus lists the target, and a simple `up` query returns one for the expected labels. That sounds like many checks, but it is faster than repeatedly editing YAML and waiting for dashboards to change.

```promql
up{namespace="payments",service="payment-api"}
```

Service discovery is where platform standards pay off. If every service uses `app.kubernetes.io/name`, exposes a named `metrics` port, and receives a generated ServiceMonitor from the same template, engineers can debug by exception. If every team invents its own labels and port names, Prometheus becomes a maze of special cases.

---

## Alerting Rules, Recording Rules, and Human Action

An alerting rule is a PromQL expression plus timing and metadata. The expression defines the symptom, the `for` duration controls how long the symptom must remain true, labels control routing and severity, and annotations explain the situation to a human. A useful alert is not "a metric crossed a threshold"; it is "a symptom threatens a user-facing or platform-facing objective and a responder can take a meaningful action."

Start alert design from the user impact, then work backward to the metric. For a request-driven service, a high error ratio often pages more cleanly than a high error count because traffic changes throughout the day. For a batch system, failed job count or missed completion time may be more meaningful than HTTP errors. Prometheus can evaluate many expressions, but not every expression deserves to wake someone.

```yaml
groups:
  - name: checkout-alerts
    interval: 30s
    rules:
      - alert: CheckoutHighErrorRatio
        expr: |
          (
            sum(rate(http_requests_total{service="checkout",status=~"5.."}[5m]))
            /
            sum(rate(http_requests_total{service="checkout"}[5m]))
          ) > 0.02
        for: 10m
        labels:
          severity: page
          team: checkout
        annotations:
          summary: "Checkout error ratio is above the paging threshold"
          description: "More than two percent of checkout requests have returned 5xx responses for ten minutes."
```

The `for` field is not a way to hide bad signals; it is a way to align alert timing with response value. A one-scrape spike can be useful on a dashboard but harmful as a page because it creates noise without giving humans enough evidence to act. A sustained ten-minute breach of an error-ratio threshold is more likely to represent a real customer-impacting symptom.

Alertmanager receives firing alerts from Prometheus and decides how humans see them. [It groups related alerts so a regional outage does not produce hundreds of separate notifications, deduplicates repeated alerts, supports silences during planned work, and routes by labels such as `team`, `severity`, or `service`.](https://prometheus.io/docs/alerting/latest/alertmanager/) Prometheus decides that a condition is true; Alertmanager decides how to communicate it.

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: default
  group_by:
    - alertname
    - team
    - service
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - receiver: platform-page
      matchers:
        - severity="page"

receivers:
  - name: default
  - name: platform-page
```

This Alertmanager configuration is intentionally minimal and valid, but a real environment would connect receivers to PagerDuty, Slack, email, or webhooks. The important teaching point is that routing depends on alert labels, so alert labels become an operational API. If rules use inconsistent labels such as `owner`, `team`, and `squad` for the same concept, routing becomes fragile.

Recording rules should be introduced before alerting rules become too complex. If several alerts depend on the same request-rate or error-ratio calculation, record that calculation once and alert on the recorded series. This reduces query duplication and lets reviewers focus on alert thresholds and durations instead of revalidating the same math repeatedly.

```yaml
groups:
  - name: service-slo-recording
    interval: 30s
    rules:
      - record: service:http_requests:rate5m
        expr: |
          sum by (service) (
            rate(http_requests_total[5m])
          )
      - record: service:http_errors:rate5m
        expr: |
          sum by (service) (
            rate(http_requests_total{status=~"5.."}[5m])
          )
      - record: service:http_error_ratio:rate5m
        expr: |
          service:http_errors:rate5m
          /
          service:http_requests:rate5m

  - name: service-slo-alerts
    interval: 30s
    rules:
      - alert: ServiceHighErrorRatio
        expr: service:http_error_ratio:rate5m > 0.02
        for: 10m
        labels:
          severity: page
        annotations:
          summary: "Service error ratio is above threshold"
          description: "{{ $labels.service }} has a sustained 5xx error ratio above two percent."
```

> **Stop and think:** If a dashboard and an alert use different PromQL expressions for "error ratio," what could happen during an incident review when the page fired but the dashboard looked healthy?

The team may spend valuable time arguing about which number is true instead of resolving the incident. Recording rules reduce that risk by giving dashboards and alerts a shared source of calculated truth. They do not remove the need to review thresholds, but they make the math consistent and easier to test.

A good alert also needs absence coverage. If a service disappears from scraping, the error-ratio alert may stop returning data, which looks quiet unless another rule checks target health. Pair user-impact alerts with coverage alerts so the monitoring system tells you when its own view is incomplete.

```yaml
groups:
  - name: monitoring-coverage
    interval: 30s
    rules:
      - alert: PrometheusTargetDown
        expr: up == 0
        for: 5m
        labels:
          severity: ticket
        annotations:
          summary: "Prometheus target is down"
          description: "{{ $labels.job }} target {{ $labels.instance }} has not been scraped successfully for five minutes."
```

The severity of a target-down alert depends on ownership and blast radius. A single development Pod failing to scrape may be a ticket, while every target in a production namespace disappearing may be a page because it creates a monitoring blind spot. Mature platforms express those distinctions with labels and routing rules rather than asking every responder to infer severity from raw metric names.

---

## Storage, Cardinality, and Production Scale

Prometheus stores one time series for each unique metric name and label set, so scale is often driven more by cardinality than by raw traffic volume. A service handling many requests can be cheap to monitor if it emits a small, stable set of labeled counters and histograms. A low-traffic service can be expensive if it emits [labels for user IDs, request IDs, raw URLs, exception messages, or dynamically generated tenant keys](https://prometheus.io/docs/practices/naming/).

High cardinality has several symptoms. Memory usage rises because active series must be indexed, query latency increases because selectors match more series, compaction gets heavier, and restarts may take longer. The system may appear fine until a deployment or traffic spike creates many new label combinations, at which point the monitoring system becomes another incident participant.

```promql
prometheus_tsdb_head_series
```

The `prometheus_tsdb_head_series` metric tells you how many active series Prometheus is tracking in the head block. It does not identify the culprit by itself, but it is a useful first indicator. When this number rises sharply after a release, suspect a new metric, a new label, a service discovery expansion, or a change that caused Prometheus to scrape far more targets than expected.

```promql
topk(10, count by (__name__) ({__name__=~".+"}))
```

This query estimates which metric names have the most series. It is a starting point, not a final diagnosis, because the metric name alone may not show which label is exploding. Once you find a suspicious metric, inspect its label dimensions and compare them to the labels operators actually need for aggregation and troubleshooting.

```promql
topk(10, count by (service) (http_requests_total))
```

If one service owns most of the series for a shared metric, inspect that service's instrumentation. A common mistake is to record raw URL paths such as `/users/123/orders/456` instead of route templates such as `/users/{user_id}/orders/{order_id}`. The route template preserves operational meaning while preventing every resource identifier from becoming a new label value.

```ascii
+--------------------------------------------------------------------------------+
|                            LABEL CARDINALITY EXAMPLE                            |
+--------------------------------------------------------------------------------+
|                                                                                |
|  Safe label shape                                                               |
|  http_requests_total{service="checkout",route="/orders/{id}",status="200"}      |
|  + service values are bounded by deployed services                              |
|  + route values are bounded by application route definitions                    |
|  + status values are bounded by HTTP status codes                               |
|                                                                                |
|  Unsafe label shape                                                             |
|  http_requests_total{service="checkout",path="/orders/928391",user_id="7319"}   |
|  + path values grow with customer activity                                      |
|  + user_id values grow with customer count                                      |
|  + series count changes with traffic, not architecture                          |
|                                                                                |
+--------------------------------------------------------------------------------+
```

Cardinality control belongs in multiple places. Application libraries should avoid unbounded labels, code review should treat metric labels as production API, [scrape configs can drop unsafe labels, and Prometheus can enforce sample limits on noisy scrape jobs](https://prometheus.io/docs/prometheus/latest/configuration/configuration/). No single layer is enough because a platform team may not control every exporter or application library.

```yaml
scrape_configs:
  - job_name: application-pods
    sample_limit: 10000
    label_limit: 40
    label_name_length_limit: 120
    label_value_length_limit: 240
    metric_relabel_configs:
      - source_labels:
          - request_id
        action: labeldrop
      - source_labels:
          - user_id
        action: labeldrop
```

Metric relabeling can protect Prometheus from some bad labels after scraping, but it is not a substitute for fixing instrumentation. Prometheus still has to scrape and parse the response before applying metric relabeling, and the application still spends CPU creating those labels. Treat relabeling as a guardrail and migration tool, not as permission to emit unbounded metrics.

Retention decisions should reflect query needs and architecture. [Local Prometheus storage is excellent for recent operational investigation, but long-term reporting often belongs in a remote storage system designed for durable retention and larger historical queries.](https://prometheus.io/docs/introduction/overview/) Keeping years of data in a single local Prometheus server usually creates operational risk without giving users a good analytics experience.

```yaml
server:
  retention: 15d
  persistentVolume:
    enabled: true
    size: 50Gi
```

Remote write streams samples from Prometheus to another system. It is useful for long-term storage, centralized analytics, multi-cluster views, and compliance retention, but it adds a dependency and can amplify cardinality costs. If the local Prometheus is already overloaded by bad labels, remote write may faithfully export the same problem to a larger bill.

```yaml
remote_write:
  - url: "http://thanos-receive.monitoring.svc.cluster.local:19291/api/v1/receive"
    queue_config:
      max_samples_per_send: 2000
      capacity: 10000
      max_shards: 8
```

Federation is different from remote write. [Federation lets one Prometheus scrape selected time series from another Prometheus, often for aggregated regional or global views. Remote write streams raw or selected samples to a storage backend, while federation usually pulls curated metrics.](https://prometheus.io/docs/prometheus/latest/federation/) The right choice depends on whether you need durable raw history, aggregated status, or a hierarchy of operational views.

```yaml
scrape_configs:
  - job_name: federate-regional-prometheus
    honor_labels: true
    metrics_path: /federate
    params:
      match[]:
        - '{__name__=~"service:.*"}'
        - 'up'
    static_configs:
      - targets:
          - prometheus-us-east.monitoring.svc.cluster.local:9090
          - prometheus-eu-west.monitoring.svc.cluster.local:9090
```

A senior platform design often uses local Prometheus servers for fast regional alerting and a separate system for global retention and exploration. Local alerting keeps the paging path close to the workload and reduces dependency on a central system during network partitions. Global storage gives leadership and service teams a longer historical view without asking one Prometheus server to do every job.

---

## Dashboards, SLOs, and Query Review

Dashboards are most useful when they follow the shape of a human investigation. A first panel should answer whether users are affected, the next panels should separate request rate, error ratio, and latency, and deeper panels should isolate dependencies, saturation, and recent changes. A dashboard that begins with CPU graphs may be comfortable for infrastructure engineers but weak for incident triage if the symptom is customer checkout failure.

The RED pattern is a practical starting point for request-driven services: rate, errors, and duration. Rate shows demand, errors show failed outcomes, and duration shows latency distribution. Prometheus supports that pattern well because counters and histograms can be aggregated across replicas, compared by route or service, and connected to SLO thresholds.

The USE pattern is a practical starting point for resources: utilization, saturation, and errors. For nodes, disks, queues, and connection pools, you often need to know how busy the resource is, whether work is waiting, and whether operations are failing. Prometheus can represent all three, but the metric names depend on the exporter and the system being observed.

| Signal pattern | Best for | Example Prometheus signal | Decision it supports |
|----------------|----------|---------------------------|----------------------|
| RED | Request-serving applications | Request rate, 5xx ratio, latency histogram | Roll back, scale, or inspect a dependency |
| USE | Infrastructure resources | CPU utilization, disk saturation, network errors | Add capacity, move workload, or fix hardware |
| Coverage | Monitoring health | `up`, scrape duration, target count | Trust or distrust dashboard silence |
| Saturation | Queues and pools | Queue depth, active connections, pending work | Increase workers or reduce admission |
| Cost | Platform economics | Samples ingested, active series, storage bytes | Control cardinality and retention |

Dashboard queries deserve review because they run repeatedly and shape operational decisions. [A query that scans every series every few seconds can become an invisible load generator. A panel that groups by `pod` may help a developer during debugging but overload an executive overview. Good dashboards use recording rules for shared expensive expressions](https://prometheus.io/docs/prometheus/latest/querying/basics/) and reserve high-cardinality breakdowns for drill-down pages.

Prometheus has its own metrics for query and scrape health. If dashboards slow down, do not guess only at Grafana. Inspect Prometheus query duration, rule evaluation duration, scrape sample counts, and TSDB series metrics. The monitoring system is itself a production service, and it should have dashboards and alerts like any other platform component.

```promql
prometheus_engine_query_duration_seconds
```

```promql
prometheus_rule_group_last_duration_seconds
```

```promql
scrape_samples_post_metric_relabeling
```

When teams connect Prometheus to SLOs, they should write the SLO in human language before writing PromQL. For example, "99.9 percent of checkout requests should complete successfully over thirty days" is a product reliability statement. The PromQL implementation then needs a numerator, denominator, window, labels, and exclusions that match that statement rather than merely approximate a convenient metric.

A useful review question is, "What decision would change if this panel turns red?" If the answer is unclear, the panel may be decorative or too low-level for the dashboard. Prometheus makes it easy to graph almost anything, but platform maturity comes from graphing the few things that change response, design, or investment decisions.

---

## Did You Know?

1. **Prometheus was designed to stay useful during partial failure**, which is why local scraping and local alert evaluation remain central even when teams add remote storage.

2. **The `up` metric is generated by Prometheus rather than by the target**, so it tells you whether the scrape succeeded from Prometheus's point of view.

3. **Histogram buckets are cumulative in Prometheus**, which is why queries for percentiles must preserve the `le` label until `histogram_quantile()` consumes it.

4. **Labels are part of the identity of a time series**, so changing or adding a label is an operational data-model change rather than a harmless formatting tweak.

---

## Common Mistakes

| Mistake | Problem | Better Practice |
|---------|---------|-----------------|
| Using raw counters directly in dashboards | Counters only increase, so the graph shows lifetime activity instead of recent behavior | Wrap counters with `rate()` or `increase()` over a range that fits the decision |
| Alerting on `irate()` | The last two samples can create noisy pages during brief spikes or scrape jitter | Use `rate()` for alerts and reserve `irate()` for interactive debugging |
| Dropping `le` before `histogram_quantile()` | Prometheus loses the bucket boundaries needed to estimate percentiles | Aggregate histogram buckets with `sum by (..., le)` before calculating quantiles |
| Adding `user_id`, `request_id`, or raw path labels | Each unique value creates new time series and can exhaust memory | Use bounded labels such as service, route template, method, status, and region |
| Assuming a healthy Pod is a scraped target | Service discovery can fail even when the workload is running correctly | Verify Pod labels, Service selectors, EndpointSlices, ServiceMonitors, and the Prometheus target page |
| Using different math in dashboards and alerts | Responders see conflicting numbers during incidents and lose trust in monitoring | Put shared SLO calculations in recording rules and reuse them consistently |
| Treating Pushgateway as the default path | Long-running services lose the simple target-health signal that pull scraping provides | Use normal scraping for services and reserve Pushgateway for short-lived jobs |
| Keeping every historical sample locally forever | Local Prometheus becomes overloaded and difficult to operate | Use reasonable local retention and remote storage or federation for broader needs |

---

## Quiz

<details>
<summary>1. Your team deploys a checkout service, and Grafana shows no request-rate data. The Pod responds to `curl /metrics` during a port-forward, but `up{service="checkout"}` returns no series. What do you check next, and why?</summary>

You should treat this as a discovery or labeling problem before treating it as an instrumentation problem. The endpoint works when called directly, so inspect the Service selector, EndpointSlice contents, ServiceMonitor selector, port name, namespace selector, and target labels in Prometheus. The query may also be filtering on a label that does not exist, so compare the actual target labels with the labels used in PromQL.
</details>

<details>
<summary>2. A release adds `path="/customers/12345/orders/98765"` to `http_requests_total`, and Prometheus memory rises sharply within an hour. How would you explain the failure and change the metric?</summary>

The raw path creates many unique label values, so each customer and order identifier can produce a new time series. Prometheus must track those series in memory and index them for queries, which can overwhelm the server even if request volume is moderate. Replace the raw path with a bounded route template such as `route="/customers/{customer_id}/orders/{order_id}"`, and consider dropping the unsafe label with metric relabeling while the application fix rolls out.
</details>

<details>
<summary>3. During an incident, an engineer proposes this alert: `irate(http_requests_total{status=~"5.."}[5m]) > 10`. What risks do you point out, and what shape would you prefer?</summary>

The query uses `irate()`, so it reacts to the last two samples and can flap on a brief spike or scrape jitter. It also uses an absolute error rate, which may page during high traffic but miss severe low-traffic failure ratios. Prefer a sustained error-ratio alert using `rate()` for both failed and total requests, with a `for` duration and labels that route the alert to the owning team.
</details>

<details>
<summary>4. A p99 latency query returns nonsense after someone changes `sum by (service, route, le)` to `sum by (service, route)`. What broke, and how do you fix it?</summary>

The query aggregated away the `le` label, which contains the histogram bucket boundaries. `histogram_quantile()` needs those cumulative bucket counts to estimate percentiles, so removing `le` destroys the distribution shape. Restore `le` in the aggregation before calling `histogram_quantile()`, and review whether the remaining labels define the distribution you actually want to compare.
</details>

<details>
<summary>5. A dashboard and a paging alert both claim to show checkout error ratio, but the dashboard says one percent while the alert says four percent. How do you resolve the design issue, not just the immediate confusion?</summary>

First compare the numerator, denominator, labels, range windows, and aggregation groups used by both expressions. Then move the shared calculation into a recording rule with a clear name such as `service:http_error_ratio:rate5m`, and have both the dashboard and alert use that recorded series. This makes future reviews focus on threshold and response policy rather than hidden query drift.
</details>

<details>
<summary>6. Prometheus shows `up == 0` for every target in one namespace immediately after a NetworkPolicy change. What is your investigation path?</summary>

Start by confirming that the targets still exist in service discovery, because `up == 0` means Prometheus has targets but cannot scrape them successfully. Check whether the NetworkPolicy allows traffic from the Prometheus Pod namespace to the metrics ports, then test a direct request from a temporary Pod in the Prometheus namespace if policy allows. Also inspect scrape errors on the target page, because timeouts, connection refusals, and HTTP errors point to different fixes.
</details>

<details>
<summary>7. A team wants one central Prometheus to scrape every Pod in every cluster so they can have one place for all alerts. How do you evaluate that proposal?</summary>

A single central scraper can create reachability, latency, blast-radius, and scale problems, especially during network partitions. A stronger design usually keeps local Prometheus servers close to workloads for fast scraping and local alerting, then uses remote write or federation for global views and longer retention. The final decision should consider failure isolation, alert reliability, cardinality, retention needs, and the cost of central query load.
</details>

<details>
<summary>8. Your SLO says checkout success rate should stay above 99.9 percent, but the service has very low traffic overnight. How would you adapt the Prometheus alert to avoid misleading pages?</summary>

Low traffic makes short-window ratios volatile because a small number of failures can produce a large percentage. Use a window and `for` duration that match the SLO decision, consider minimum traffic guards, and pair fast-burn alerts with slower burn-rate alerts if the organization uses error-budget policies. The goal is to page on meaningful user impact while still surfacing small-sample failures as tickets or dashboard signals.
</details>

---

## Hands-On Exercise: Deploy, Discover, Query, and Alert

In this exercise, you will install Prometheus with the Prometheus Operator, deploy a sample application that exposes metrics, verify discovery, build PromQL queries from raw series to SLO-style signals, and add a simple alert rule. Use a disposable cluster because the commands install monitoring resources and custom resource definitions. The examples start with `kubectl`; after that, `k` is used as the common alias for `kubectl`.

### Step 1: Create the monitoring namespace and install Prometheus

Install the community Helm chart that includes Prometheus Operator support. The chart creates Prometheus, Alertmanager, exporters, and the custom resources needed for ServiceMonitor-based discovery. The exact chart version can vary by environment, so the exercise focuses on the stable resource contracts rather than a chart-specific UI detail.

```bash
kubectl create namespace monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.retention=7d \
  --set prometheus.prometheusSpec.resources.requests.cpu=200m \
  --set prometheus.prometheusSpec.resources.requests.memory=1Gi
```

Wait until the Prometheus resources are ready. This command does not prove that every target is healthy, but it confirms that the main Pods are running before you start debugging discovery. If your cluster is slow to pull images, rerun the `get pods` command until the Prometheus and operator Pods show a ready state.

```bash
kubectl -n monitoring get pods
kubectl -n monitoring get prometheus
kubectl -n monitoring get alertmanager
```

### Step 2: Open Prometheus locally

Port-forward the Prometheus service and open the UI at `http://127.0.0.1:9090`. Keep this terminal running while you use the Prometheus target page and expression browser. If your chart names the service differently, list services in the namespace and choose the service that points at Prometheus.

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
```

In another terminal, define the shorter alias used by the remaining commands. The alias is only a typing shortcut; every command still uses the Kubernetes API in the same way as `kubectl`.

```bash
alias k=kubectl
```

### Step 3: Deploy a sample application with a metrics endpoint

Create a namespace for the application and deploy a small example app that exposes Prometheus-format metrics. The Deployment and Service use the same stable label key, and the Service names its port `metrics` so the ServiceMonitor can select it without relying on a fragile port number. This mirrors the label discipline you should expect from production service templates.

```bash
kubectl create namespace prometheus-lab
cat > prometheus-sample-app.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: prometheus-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: sample-app
  template:
    metadata:
      labels:
        app.kubernetes.io/name: sample-app
    spec:
      containers:
        - name: app
          image: quay.io/brancz/prometheus-example-app:v0.3.0
          ports:
            - name: metrics
              containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: sample-app
  namespace: prometheus-lab
  labels:
    app.kubernetes.io/name: sample-app
spec:
  selector:
    app.kubernetes.io/name: sample-app
  ports:
    - name: metrics
      port: 80
      targetPort: metrics
EOF
kubectl apply -f prometheus-sample-app.yaml
```

Verify that the Service actually selects Pods before creating the ServiceMonitor. This step is deliberate because a ServiceMonitor can be perfectly valid while the Service has no endpoints. Debugging in this order teaches you to check each link in the discovery chain.

```bash
k -n prometheus-lab get pods --show-labels
k -n prometheus-lab get service sample-app -o wide
k -n prometheus-lab get endpointslice -l kubernetes.io/service-name=sample-app
```

### Step 4: Create a ServiceMonitor

Create a ServiceMonitor that selects the Service label and scrapes the named `metrics` port. The `release: kube-prometheus-stack` label matches the common Helm release selector used by the chart installation above. If your Prometheus custom resource uses a different selector, adapt the ServiceMonitor metadata labels to match it.

```bash
cat > sample-app-servicemonitor.yaml <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: sample-app
  namespace: prometheus-lab
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: sample-app
  namespaceSelector:
    matchNames:
      - prometheus-lab
  endpoints:
    - port: metrics
      path: /metrics
      interval: 15s
      scrapeTimeout: 10s
EOF
kubectl apply -f sample-app-servicemonitor.yaml
```

Open the Prometheus target page and search for `sample-app`. If the target does not appear after a short wait, inspect the ServiceMonitor selector, the Service labels, and the Prometheus custom resource's monitor selector. If the target appears but is down, inspect the scrape error and manually test the endpoint through a port-forward.

```bash
k -n prometheus-lab port-forward svc/sample-app 8080:80
curl -fsS http://127.0.0.1:8080/metrics | head
```

### Step 5: Generate traffic and inspect raw series

Generate a small amount of traffic so counters have samples to rate. This command runs a temporary curl Pod and repeatedly calls the service. Stop it with `Ctrl+C` after a minute or leave it running while you test queries.

```bash
kubectl -n prometheus-lab run traffic \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm -it -- \
  sh -c 'while true; do curl -fsS http://sample-app/metrics >/dev/null; sleep 1; done'
```

In Prometheus, start with target health before application metrics. This confirms that discovery and scraping work. If the result is empty, compare the actual target labels on the status page with the labels in your query.

```promql
up{namespace="prometheus-lab"}
```

Now inspect the sample application's HTTP counter. The exact label set may differ by exporter, so use this step to learn what labels are actually available before writing a final query. Treat the label list as evidence rather than assuming it matches an example from another service.

```promql
http_requests_total
```

### Step 6: Build request-rate and error-ratio queries

Convert the counter into a rate. If the query returns no data, expand the range window or confirm that traffic has actually occurred since Prometheus discovered the target. A range window should usually contain several scrape samples, so a five-minute window is a reasonable default for this exercise.

```promql
rate(http_requests_total[5m])
```

Aggregate the rate across replicas. Keep only labels that help you make a decision. If the sample app exposes different labels from your production services, adapt the grouping to the labels you actually see.

```promql
sum by (job) (
  rate(http_requests_total[5m])
)
```

Build an error-ratio query if the metric has a status or code label. If your sample metric does not expose a status label, use the worked example from the module as the production pattern and note the missing label as an instrumentation gap. The important skill is constructing numerator and denominator with matching aggregation.

```promql
sum by (job) (
  rate(http_requests_total{code=~"5.."}[5m])
)
/
sum by (job) (
  rate(http_requests_total[5m])
)
```

### Step 7: Add a PrometheusRule

Create a simple alert rule that fires when the sample app target is down. This alert tests the rule pipeline without needing to force application errors. In production you would combine target coverage alerts with user-impact alerts, but coverage is the right first rule for a discovery-focused lab.

```bash
cat > sample-app-rule.yaml <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: sample-app-coverage
  namespace: prometheus-lab
  labels:
    release: kube-prometheus-stack
spec:
  groups:
    - name: sample-app-coverage
      interval: 30s
      rules:
        - alert: SampleAppTargetDown
          expr: up{namespace="prometheus-lab"} == 0
          for: 2m
          labels:
            severity: ticket
            team: platform
          annotations:
            summary: "Sample app target is down"
            description: "Prometheus cannot scrape a sample-app target in the prometheus-lab namespace."
EOF
kubectl apply -f sample-app-rule.yaml
```

Check that Prometheus loaded the rule. In the UI, visit the rules page and search for `SampleAppTargetDown`. If the rule does not appear, inspect the Prometheus custom resource rule selector and the labels on the PrometheusRule.

```bash
k -n prometheus-lab get prometheusrule sample-app-coverage -o yaml
k -n monitoring get prometheus -o yaml
```

### Step 8: Break discovery intentionally and repair it

Patch the Service selector to a label that does not match the Pods. This simulates the real production failure where a chart migration changed label conventions. Watch the EndpointSlice change, then restore the selector and confirm that Prometheus target health recovers.

```bash
kubectl -n prometheus-lab patch service sample-app \
  --type='merge' \
  -p '{"spec":{"selector":{"app.kubernetes.io/name":"does-not-match"}}}'
kubectl -n prometheus-lab get endpointslice -l kubernetes.io/service-name=sample-app
```

Now repair the selector and verify the endpoints return. The lesson is that the monitoring failure is not always inside Prometheus; sometimes Prometheus is faithfully reporting that Kubernetes no longer gives it a reachable endpoint. This is why service discovery checks belong in deployment validation.

```bash
kubectl -n prometheus-lab patch service sample-app \
  --type='merge' \
  -p '{"spec":{"selector":{"app.kubernetes.io/name":"sample-app"}}}'
kubectl -n prometheus-lab get endpointslice -l kubernetes.io/service-name=sample-app
```

### Success Criteria

You have completed the exercise when all of the following are true:

- [ ] You can open the Prometheus UI through `http://127.0.0.1:9090`.
- [ ] You can explain whether the sample app is discovered through a ServiceMonitor or through annotations.
- [ ] You can verify that the Service selector produces EndpointSlice addresses for the sample app.
- [ ] You can find the sample app target in Prometheus and explain the labels attached to it.
- [ ] You can query `up{namespace="prometheus-lab"}` and interpret missing data, zero values, and one values correctly.
- [ ] You can build a request-rate query by moving from a raw counter to `rate()` and then to `sum by (...)`.
- [ ] You can explain why an error-ratio query needs matching numerator and denominator aggregation.
- [ ] You can create a PrometheusRule and confirm that Prometheus loaded it.
- [ ] You can intentionally break a Service selector, observe the discovery impact, and repair it.
- [ ] You can identify one label in your environment that would be safe for aggregation and one label that would be dangerous if it were unbounded.

### Cleanup

Remove the lab resources when you are finished. Cleanup matters because monitoring stacks create custom resources, persistent volumes in some configurations, and cluster-wide permissions. If you installed into a shared cluster, confirm with the cluster owner before deleting anything outside the lab namespace.

```bash
kubectl delete -f sample-app-rule.yaml
kubectl delete -f sample-app-servicemonitor.yaml
kubectl delete -f prometheus-sample-app.yaml
kubectl delete namespace prometheus-lab
helm uninstall kube-prometheus-stack --namespace monitoring
kubectl delete namespace monitoring
```

---

## Next Module

Continue to [Module 1.2: OpenTelemetry](../module-1.2-opentelemetry/) to learn how vendor-neutral instrumentation connects metrics, traces, and logs across services.

## Sources

- [Prometheus Overview](https://prometheus.io/docs/introduction/overview/) — Backs Prometheus as a pull-based metrics system with labeled time series, HTTP scraping, service discovery, local storage, recording rules, alert generation, and common ecosystem components such as Alertmanager and Grafana.
- [prometheus.io: jobs instances](https://prometheus.io/docs/concepts/jobs_instances/) — The jobs/instances concept page explicitly defines the auto-generated labels and the `up` time series semantics.
- [prometheus.io: concepts](https://prometheus.io/docs/concepts/) — This is a direct statement from the Prometheus data model documentation.
- [prometheus.io: naming](https://prometheus.io/docs/practices/naming/) — Prometheus naming guidance explicitly warns that every unique label set is a new series and warns against unbounded labels.
- [prometheus.io: pushing](https://prometheus.io/docs/practices/pushing/) — Prometheus best-practice guidance states both the intended Pushgateway use case and its tradeoffs.
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/) — Backs Kubernetes service discovery roles, scrape configuration, relabeling-related target metadata, and the mechanics used to debug missing or mislabeled scrape targets in Kubernetes.
- [prometheus.io: functions](https://prometheus.io/docs/prometheus/2.55/querying/functions/) — The Prometheus query functions documentation explicitly defines counter behavior and `rate()` semantics.
- [prometheus.io: functions](https://prometheus.io/docs/prometheus/3.9/querying/functions/) — The official PromQL function reference distinguishes `irate()` from `rate()` on exactly these terms.
- [prometheus.io: rules](https://prometheus.io/docs/practices/rules/) — Prometheus recording-rules guidance explicitly describes precomputing reused or expensive expressions.
- [raw.githubusercontent.com: api.md](https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/Documentation/api-reference/api.md) — The Operator API reference on raw GitHub directly documents both `ServiceMonitor` purpose and `serviceMonitorSelector` behavior.
- [github.com: README.md](https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/README.md) — The kube-prometheus-stack README documents the default release-tag-based monitor discovery behavior.
- [prometheus.io: alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) — The official Alertmanager concepts page directly documents these responsibilities.
- [prometheus.io: federation](https://prometheus.io/docs/prometheus/latest/federation/) — The federation documentation explicitly defines federation as scraping selected time series from another Prometheus server.
- [prometheus.io: basics](https://prometheus.io/docs/prometheus/latest/querying/basics/) — The querying basics page explicitly warns about slow or overload-prone queries and recommends pre-recording expensive expressions.

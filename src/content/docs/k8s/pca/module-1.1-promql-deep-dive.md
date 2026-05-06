---
revision_pending: false
title: "Module 1.1: PromQL Deep Dive"
slug: k8s/pca/module-1.1-promql-deep-dive
sidebar:
  order: 2
---
# Module 1.1: PromQL Deep Dive

> **PCA Track** | Complexity: `[COMPLEX]` | Time: 50-60 min | Kubernetes target: 1.35+ for the lab examples and operational assumptions.

## Prerequisites

Before starting this module, make sure the following foundations are comfortable enough that you can focus on PromQL reasoning instead of environment setup:
- [Prometheus Module](/platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) — architecture, pull model, basic PromQL
- [Observability Theory](/platform/foundations/observability-theory/) — metrics concepts
- Basic Kubernetes knowledge
- A running Prometheus instance (kind/minikube with kube-prometheus-stack)

---

## What You'll Be Able to Do

After completing this module, you will be able to perform these PromQL tasks against Kubernetes observability data and explain the tradeoffs behind each query:

1. **Construct** PromQL queries using range vectors, aggregation operators, and binary operations to answer production questions about latency, error rates, and saturation.
2. **Apply** `histogram_quantile` and `rate()` correctly to compute percentile latencies and per-second rates from counter and histogram metrics.
3. **Build** recording rules that pre-compute expensive queries for dashboard performance and SLO tracking.
4. **Diagnose** misleading metric behavior, including counter resets, label cardinality explosions, stale markers, and empty joins, by reasoning about PromQL evaluation mechanics.

At traffic spikes, averages can stay inside SLOs while percentile latency and selected request cohorts degrade badly. PromQL tail analysis is the first step to discovering which labels are carrying the pain and why. Keep the investigation explicit and label-specific to catch bottlenecks that aggregate graphs hide.

```promql
histogram_quantile(0.99,
  sum by (le, payment_method)(rate(http_request_duration_seconds_bucket{service="checkout"}[5m]))
)
```

## Why This Module Matters

Hypothetical scenario: a checkout service is receiving normal total traffic, its CPU graph looks ordinary, and the average request duration is still below the service objective. Support tickets are rising anyway because one payment method is timing out during authorization, and the failure is hidden when every route, status code, pod, and payment method is averaged together. During that incident, a useful operator does not ask Prometheus for "the latency"; they ask for the distribution of latency by the labels that represent user experience, then narrow the query until the damaged cohort is visible.

PromQL is the language you use to ask those operational questions under pressure. It is also a major part of the Prometheus Certified Associate exam, because Prometheus without PromQL is mostly a storage engine full of samples you cannot interpret. The important skill is not memorizing isolated functions; it is learning how vector selectors, range selectors, functions, aggregations, and joins compose into answers that can drive a decision during an outage or a design review.

This module builds that skill from the inside out. You will start by selecting the right time series, then turn raw counters into rates, aggregate labels without destroying meaning, compute histogram percentiles, join metrics safely, and decide when an expensive expression should become a recording rule. The examples use Kubernetes and Prometheus conventions current for Kubernetes 1.35+, but the reasoning transfers to any Prometheus-backed system because the evaluation model is the same.

## Reading PromQL as a Data Pipeline

PromQL feels less mysterious when you read each expression as a pipeline that transforms sets of labeled samples. A metric selector fetches series from the time-series database, a range selector changes each matching series into a short sample history, a function turns that history into a value, and an aggregation decides which labels survive. If you can say what each stage receives and returns, you can debug most broken queries without guessing at syntax.

The first mental model is the difference between an instant vector and a range vector. An instant vector contains one sample per matching series at the evaluation timestamp, while a range vector contains many samples per matching series over a lookback window. Dashboards and binary operators generally want instant vectors, but functions such as `rate()`, `increase()`, and `avg_over_time()` need a range vector because they must inspect how a value changed or behaved across time.

```promql
# Select all series with this metric name
http_requests_total

# Filter by exact label match
http_requests_total{method="GET"}

# Filter by multiple labels (AND logic)
http_requests_total{method="GET", status="200"}

# Regex match (RE2 syntax)
http_requests_total{status=~"2.."}

# Negative match
http_requests_total{status!="500"}

# Negative regex match
http_requests_total{method!~"OPTIONS|HEAD"}
```

Selectors are your first cardinality decision, so treat them as more than filters. A broad selector such as `http_requests_total` may return every service, status, route, pod, and instance that emits that metric, which can be useful for exploration and expensive for production dashboards. A narrow selector such as `{service="checkout", status=~"5.."}` carries intent, reduces work, and makes the result easier to explain to another engineer during review.

| Matcher | Meaning | Example |
|---------|---------|---------|
| `=` | Exact match | `{job="api"}` |
| `!=` | Not equal | `{job!="test"}` |
| `=~` | Regex match | `{status=~"5.."}` |
| `!~` | Negative regex | `{path!~"/health\|/ready"}` |

Every selector must have at least one matcher that does not match the empty string, because Prometheus needs a bounded starting point for evaluation. A selector such as `{job=~".*"}` is invalid because it could match an absent label, while `{job=~".+"}` says the `job` label must exist and contain at least one character. This small rule prevents accidental whole-database scans disguised as harmless regular expressions.

```promql
# Last 5 minutes of samples
http_requests_total{method="GET"}[5m]

# Last 1 hour
http_requests_total[1h]

# Valid time durations: ms, s, m, h, d, w, y
# 5m = 5 minutes, 1h30m = 90 minutes, 1d = 1 day
```

You cannot graph a range vector directly because it is a collection of sample histories, not a single value for each series. That is why the most common beginner error is typing `http_requests_total[5m]` into the graph tab and expecting a line. The range vector is an ingredient; a function such as `rate()` or `increase()` is what cooks it into an instant vector that the graph can display.

```promql
# WRONG: Cannot graph this
http_requests_total[5m]

# RIGHT: rate() converts range vector to instant vector
rate(http_requests_total[5m])
```

The `offset` modifier lets you compare a current expression with an earlier evaluation period, which is useful for incident review and seasonal traffic patterns. It does not change the shape of the expression; it changes the time from which the samples are read. If a dashboard compares this hour with last week, using `offset 7d` is often clearer than exporting values into a spreadsheet and manually lining up timestamps.

```promql
# Current request rate
rate(http_requests_total[5m])

# Request rate 1 hour ago
rate(http_requests_total[5m] offset 1h)

# Request rate 1 week ago (for week-over-week comparison)
rate(http_requests_total[5m] offset 7d)

# How much has the rate changed compared to 1 hour ago?
rate(http_requests_total[5m])
-
rate(http_requests_total[5m] offset 1h)
```

The `@` modifier pins evaluation to a specific timestamp, the start of a displayed range, or the end of that range. This is helpful when a query looked suspicious during a past incident and you need to reproduce the value that an alerting rule or dashboard would have seen. Pause and predict: if you combine `offset 1h` with `@ end()`, which part controls the displayed evaluation timestamp, and which part controls the samples read by the selector?

```promql
# Value at a specific Unix timestamp
http_requests_total @ 1704067200

# Value at the start of the query range
http_requests_total @ start()

# Value at the end of the query range
http_requests_total @ end()
```

## Turning Counters into Operational Rates

Counters are designed to represent accumulated work, not the current speed of that work. A raw request counter going from one million to two million does not tell you whether the service is currently calm or overloaded, because the number depends on process lifetime. In PromQL you almost always convert counters into rates or increases before graphing, alerting, or comparing them with other signals.

```promql
# Average requests per second over last 5 minutes
rate(http_requests_total[5m])
# If counter went from 1000 to 1300 over 5 min:
# rate = (1300 - 1000) / 300 seconds = 1.0 req/s

# CPU usage rate (seconds of CPU per second of wall time)
rate(process_cpu_seconds_total[5m])
# Result of 0.25 means 25% of one CPU core
```

`rate()` calculates a per-second average across the selected range, handles missing scrape alignment, and compensates for counter resets. That reset handling matters in Kubernetes because pods restart, containers move, and exporters get replaced during normal operations. If you used a naive subtraction, a restarted pod could look like a negative request rate; Prometheus detects the drop and treats it as a reset instead of a real decrease.

```
COUNTER RESET HANDLING
──────────────────────────────────────────────────────────────

Normal:    100 → 200 → 300 → 400
           rate = (400 - 100) / time = normal calculation

With reset: 100 → 200 → 50 → 150
            Prometheus detects 200 → 50 (decrease = reset)
            Assumes: previous total was 200, new counter starts at 0
            Effective increase: 200 + 150 = 350
            rate = 350 / time

This is why rate() is safe to use even when pods restart!
```

The practical tradeoff in `rate()` is the length of the range. Short windows respond quickly but can be noisy or empty when a scrape is missed; longer windows smooth noise but hide sudden changes. For alerting and SLO calculations, a stable value is usually more valuable than a dramatic spike, because the alert needs to represent sustained user impact rather than one unusual scrape.

```promql
# Instantaneous request rate
irate(http_requests_total[5m])
# Only uses the last 2 samples within the 5m window
# Much more volatile than rate()
```

`irate()` exists for a different job: showing what is happening at the sharp edge of the graph. Because it uses only the last two samples inside the range, it can reveal a spike that `rate()` smooths away, but it can also exaggerate one scrape anomaly. Use `irate()` while investigating a live issue, then translate confirmed findings back into `rate()` or recording rules for dashboards and alerts.

```
RATE vs IRATE DECISION
──────────────────────────────────────────────────────────────

rate(metric[5m])
├── Smoothed average over the range
├── Stable, predictable values
├── USE FOR: alerting rules, SLO calculations, recording rules
├── USE FOR: dashboard panels showing trends
└── The range [5m] matters — it's the averaging window

irate(metric[5m])
├── Instantaneous rate (last 2 points only)
├── Volatile, shows spikes and drops
├── USE FOR: debugging during incidents
├── USE FOR: "what's happening right now?" panels
└── The range [5m] only sets lookback for finding 2 points
```

`increase()` answers a human-count question rather than a speed question. When a product owner asks how many requests were processed today, a per-second rate is awkward, but an increase over a day gives a total count. Internally, `increase()` is closely related to `rate()` multiplied by the range length, so the same cautions about counter resets and range selection still apply.

```promql
# Total requests in the last hour
increase(http_requests_total[1h])
# If rate was 100 req/s, increase ≈ 100 * 3600 = 360,000

# Total errors in the last 24 hours
increase(http_errors_total[24h])

# Useful for human-readable counts:
# "We processed 1.2 million requests today"
increase(http_requests_total[24h])
```

The relationship between `rate()` and `increase()` is useful when checking your own work. If `increase(http_requests_total[1h])` says a service handled roughly three hundred sixty thousand requests, then `rate(http_requests_total[1h])` should be close to one hundred requests per second. When those two values disagree wildly, you may be querying a different label set, aggregating differently, or reading a counter that resets too often.

```promql
# These are approximately equivalent:
increase(http_requests_total[1h])  ≈  rate(http_requests_total[1h]) * 3600
```

Counter reset counts are also operational signals. A service that restarts repeatedly may still have a normal request rate, but its reset count can reveal instability before users notice a full outage. Before running this, what output do you expect from a stable pod over the last hour, and how would that expectation change for a pod in a crash loop?

```promql
# How many times has this counter reset in the last hour?
resets(http_requests_total[1h])

# High reset count may indicate crash loops
resets(process_start_time_seconds[1h]) > 5
```

The common rule for rate windows is at least four times the scrape interval. With a fifteen-second scrape interval, a one-minute range usually gives enough points for a meaningful slope, while a thirty-second range can collapse into two samples or become empty after one missed scrape. The rule is not magic, but it is a practical lower bound that keeps dashboard lines from becoming scrape-alignment artifacts.

```
THE 4x RULE
──────────────────────────────────────────────────────────────

If scrape_interval = 15s, minimum useful range for rate() = 60s (4 × 15s)

Why? rate() needs at least 2 data points in the range.
     With 15s interval, a 30s range may contain only 1-2 points.
     A 60s range guarantees at least 4 points for reliable calculation.

Rule of thumb: range >= 4 × scrape_interval

rate(metric[15s])  ← BAD:  might have only 1 point
rate(metric[30s])  ← RISKY: might have only 2 points
rate(metric[1m])   ← OK:   typically 4 points
rate(metric[5m])   ← SAFE: ~20 points, good smoothing
```

## Aggregation and Label Shape

Aggregation is where PromQL becomes an operational language instead of a metric browser. A Kubernetes cluster can expose the same metric across namespaces, pods, containers, nodes, jobs, endpoints, and status codes; aggregation decides which of those dimensions remain visible. The danger is that every aggregation also discards information, so a query must preserve the labels needed for the question and remove the labels that only add noise or cardinality.

```promql
# SUM: total across all series
sum(rate(http_requests_total[5m]))
# Result: single number — total requests/sec across all pods

# AVG: average across all series
avg(rate(http_requests_total[5m]))
# Result: average requests/sec per pod

# MIN / MAX: extremes
min(node_filesystem_avail_bytes)
max(container_memory_usage_bytes)

# COUNT: number of series
count(up == 1)
# Result: how many targets are up

# STDDEV / STDVAR: statistical spread
stddev(rate(http_requests_total[5m]))
# High stddev = uneven load distribution

# TOPK / BOTTOMK: highest/lowest N series
topk(5, rate(http_requests_total[5m]))
# Top 5 pods by request rate

# QUANTILE: compute quantile across series
quantile(0.95, rate(http_requests_total[5m]))
# 95th percentile of request rate across all pods
# (NOT histogram_quantile — this works across series, not buckets)

# COUNT_VALUES: count unique values
count_values("version", build_info)
# How many instances are running each version
```

The difference between `sum`, `avg`, `topk`, and `quantile` is not only mathematical; it changes the story you tell. `sum` answers total demand, `avg` answers typical per-series behavior, `topk` finds the worst contributors, and `stddev` tells you whether load is evenly distributed. During incident triage, it is common to start with a service-level sum, then use `topk` or grouping labels to find the pods or routes responsible for the service-level symptom.

```promql
# GROUP BY specific labels (keep only these)
sum by (method)(rate(http_requests_total[5m]))
# Result: one series per method (GET, POST, PUT, etc.)

sum by (method, status)(rate(http_requests_total[5m]))
# Result: one series per method+status combination

# EXCLUDE specific labels (keep all others)
sum without (instance)(rate(http_requests_total[5m]))
# Result: removes instance label, keeps everything else

# Equivalent forms:
sum by (method)(metric)     = sum without (instance, job, ...)(metric)
```

`by` and `without` are complementary ways to describe the label shape you want after aggregation. `sum by (service)` is a whitelist: keep only `service` and drop every other label. `sum without (instance, pod)` is a blacklist: remove noisy instance-level labels while keeping any other dimensions, which is powerful but can preserve more labels than you intended when instrumentation changes.

```promql
# Request rate per service
sum by (service)(rate(http_requests_total[5m]))

# Error rate per service (percentage)
sum by (service)(rate(http_requests_total{status=~"5.."}[5m]))
/
sum by (service)(rate(http_requests_total[5m]))
* 100

# Top 10 pods by memory usage
topk(10, container_memory_usage_bytes{container!=""})

# Average CPU per namespace
avg by (namespace)(rate(container_cpu_usage_seconds_total[5m]))

# Total network received per node
sum by (node)(rate(node_network_receive_bytes_total[5m]))
```

Error-rate queries show why consistent label shape matters. The numerator and denominator both need to aggregate by `service`, because Prometheus matches series by labels during division. If the numerator keeps `status` and the denominator does not, the division may return an empty result or a result with surprising labels, even though both halves look reasonable when run alone.

Aggregation is also the first defense against label cardinality explosions. A dashboard panel that groups by `pod`, `container`, `path`, `status`, and `user_id` is not just hard to read; it may create enough series work to slow Prometheus. In production dashboards, keep high-cardinality labels for drill-down panels and use low-cardinality labels such as `service`, `namespace`, `job`, and `status_class` for first-page views.

## Binary Operators and Vector Matching

Binary operators let you turn raw metrics into ratios, percentages, comparisons, and enriched vectors. The important rule is that Prometheus must match one series on the left with one compatible series on the right unless you explicitly tell it how to handle a different cardinality. SQL users often search for a `JOIN` keyword, but PromQL expresses joins through matching modifiers such as `on()`, `ignoring()`, `group_left()`, and `group_right()`.

```promql
# Simple arithmetic with scalars
node_memory_MemTotal_bytes / 1024 / 1024 / 1024
# Convert bytes to GiB

# Arithmetic between two vectors
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100
# Memory utilization percentage
# Labels must match on both sides!
```

Scalar arithmetic is straightforward because each series is transformed independently. Vector arithmetic is more fragile because label sets must match. If memory usage includes `namespace`, `pod`, and `container`, but memory limit also includes an extra `resource` label, the division may silently return fewer series than expected, which is why a broken join often looks like missing data instead of a syntax error.

```promql
# Filter: only series where value > threshold
http_requests_total > 1000
# Returns only series with value > 1000

# Boolean mode: returns 1 or 0 instead of filtering
http_requests_total > bool 1000
# Returns 1 (true) or 0 (false) for each series

# Useful in alerting:
rate(http_requests_total{status=~"5.."}[5m])
/ rate(http_requests_total[5m])
> 0.05
# Only returns series where error rate exceeds 5%
```

Comparison operators are filters by default, not boolean expressions. That means `metric > 0` removes series whose value is not greater than zero, while `metric > bool 0` keeps every matched series and changes the value to one or zero. This distinction is useful for alert expressions because filtering keeps only active alert candidates, while boolean mode is useful when you want to graph condition state over time.

```promql
# AND: returns left side where right side also has matches
up == 1 and on(job) rate(http_requests_total[5m]) > 100
# Targets that are up AND have high request rates

# OR: union of both sides
rate(http_requests_total{status="500"}[5m]) > 10
or
rate(http_requests_total{status="503"}[5m]) > 10
# Series matching either condition

# UNLESS: returns left side where right side has NO match
up == 1 unless on(job) alerts{alertname="Maintenance"}
# Targets that are up but NOT in maintenance
```

Logical and set operators work on series identity rather than numeric combination. `and` keeps left-side series that have a matching right-side series, `or` forms a union, and `unless` removes left-side series that have a match on the right. These operators are useful for suppressions, maintenance windows, or existence checks where the presence of another time series is more important than its numeric value.

```promql
# DEFAULT: all labels must match
container_memory_usage_bytes / container_spec_memory_limit_bytes
# Works if both sides have identical label sets

# ON: match only on specific labels
container_memory_usage_bytes / on(container, namespace) container_spec_memory_limit_bytes
# Match only on container + namespace, ignore other labels

# IGNORING: match on everything EXCEPT specific labels
http_requests_total / ignoring(status) group_left http_requests_total_sum
# Ignore the "status" label when matching
```

Use `on()` when you know the exact keys that define the relationship, such as `namespace`, `pod`, and `container`. Use `ignoring()` when most labels should match and only a small set should be excluded, such as ignoring `status` to divide per-status errors by total requests. Which approach would you choose here and why: a dashboard maintained across several teams, where new labels may appear over time, or a tightly controlled recording rule that defines its own output labels?

```promql
# PROBLEM: node_info has labels (node, os, kernel_version)
#          node_memory_MemTotal_bytes has labels (node)
# Many info series per node vs one memory series per node

# SOLUTION: group_left brings labels from the "one" side
node_memory_MemTotal_bytes
* on(node) group_left(os, kernel_version)
node_info
# Result has memory bytes with os and kernel_version labels added

# Real-world example: add service owner labels to metrics
rate(http_requests_total[5m])
* on(service) group_left(team, oncall)
service_owner_info
# Now your request rate has team and oncall labels!
```

`group_left()` and `group_right()` should feel like warning labels, because they allow one-to-many or many-to-one matching. They are powerful for enriching metrics with metadata, but they can also multiply series if the relationship is not unique. Before using either modifier, check the right-hand and left-hand cardinality with `count by (...)` so you know whether each join key maps to exactly the number of series you expect.

```
VECTOR MATCHING VISUAL
──────────────────────────────────────────────────────────────

ONE-TO-ONE (default):
  Left:  {method="GET", status="200"}  →  matches  → Right: {method="GET", status="200"}
  Left:  {method="POST", status="200"} →  matches  → Right: {method="POST", status="200"}

MANY-TO-ONE (group_left):
  Left:  {node="a", cpu="0"}  ─┐
  Left:  {node="a", cpu="1"}  ─┼── on(node) group_left ──→ Right: {node="a"}
  Left:  {node="a", cpu="2"}  ─┘

ONE-TO-MANY (group_right):
  Left:  {node="a"} ──── on(node) group_right ──┬─ Right: {node="a", disk="sda"}
                                                  └─ Right: {node="a", disk="sdb"}
```

When a binary expression returns nothing, do not immediately assume the metric is missing. Run the left side alone, run the right side alone, and compare their labels. Empty joins are usually label-shape problems, and the fix is to make the matching relationship explicit rather than adding broader selectors that create more ambiguity.

## Histograms, Percentiles, and User Experience

Histograms are how Prometheus stores distributions such as request duration, response size, and queue wait time. A single observed request increments several cumulative bucket counters, plus the `_sum` and `_count` series. That design makes histograms queryable with ordinary counter tools, but it also means percentile accuracy depends on bucket boundaries chosen before the data was collected.

```
HISTOGRAM STRUCTURE
──────────────────────────────────────────────────────────────

Metric: http_request_duration_seconds

Generated series:
  http_request_duration_seconds_bucket{le="0.005"}   = 24054   (≤5ms)
  http_request_duration_seconds_bucket{le="0.01"}    = 33444   (≤10ms)
  http_request_duration_seconds_bucket{le="0.025"}   = 100392  (≤25ms)
  http_request_duration_seconds_bucket{le="0.05"}    = 129389  (≤50ms)
  http_request_duration_seconds_bucket{le="0.1"}     = 133988  (≤100ms)
  http_request_duration_seconds_bucket{le="0.25"}    = 144320  (≤250ms)
  http_request_duration_seconds_bucket{le="0.5"}     = 144700  (≤500ms)
  http_request_duration_seconds_bucket{le="1"}       = 144838  (≤1s)
  http_request_duration_seconds_bucket{le="+Inf"}    = 144927  (all)
  http_request_duration_seconds_sum                   = 53423.4 (total seconds)
  http_request_duration_seconds_count                 = 144927  (total requests)

Key insight: buckets are CUMULATIVE. le="0.1" includes
             everything from le="0.005" through le="0.1"
```

Because buckets are cumulative counters, you apply `rate()` before computing a recent percentile. The `le` label is not decoration; it is the bucket boundary that tells Prometheus how the distribution is shaped. If you aggregate away `le`, `histogram_quantile()` no longer knows where the bucket edges are, so it cannot interpolate a meaningful percentile.

```promql
# P50 (median) latency
histogram_quantile(0.5,
  rate(http_request_duration_seconds_bucket[5m])
)

# P90 latency
histogram_quantile(0.90,
  rate(http_request_duration_seconds_bucket[5m])
)

# P99 latency per service
histogram_quantile(0.99,
  sum by (le, service)(rate(http_request_duration_seconds_bucket[5m]))
)
# IMPORTANT: always keep "le" in the by() clause!
# histogram_quantile() needs the le label to work.

# P99.9 latency (the "three nines" percentile)
histogram_quantile(0.999,
  sum by (le)(rate(http_request_duration_seconds_bucket[5m]))
)
```

Percentiles answer a different question from averages. The average duration tells you total time divided by total requests, which can remain low while a smaller cohort suffers severe tail latency. A P99 query asks for the duration below which ninety-nine percent of observations fell, making it much better for user-facing SLOs where a small fraction of slow requests can still damage experience.

```promql
# WRONG: drops le label — histogram_quantile cannot work
histogram_quantile(0.99,
  sum by (service)(rate(http_request_duration_seconds_bucket[5m]))
)

# RIGHT: keeps le label
histogram_quantile(0.99,
  sum by (le, service)(rate(http_request_duration_seconds_bucket[5m]))
)
```

Average latency is still useful, especially for capacity analysis and cost reasoning. It comes from the histogram sum divided by the histogram count, using the same rate window on both counters. If the average and P99 diverge sharply, the system is telling you that total work is manageable but the distribution has a long tail that needs route, dependency, or cohort analysis.

```promql
# Average request duration (sum of all durations / count of requests)
rate(http_request_duration_seconds_sum[5m])
/
rate(http_request_duration_seconds_count[5m])

# Per service
sum by (service)(rate(http_request_duration_seconds_sum[5m]))
/
sum by (service)(rate(http_request_duration_seconds_count[5m]))
```

Apdex is a compact way to convert a latency distribution into a satisfaction-style score. It counts requests at or below a target as satisfied, requests at or below a tolerating threshold as partially satisfied, and slower requests as unsatisfied. The formula is only meaningful when your buckets include the target and tolerating thresholds, because otherwise the score depends on interpolation across boundaries that may be too wide.

```promql
# Apdex with target = 300ms (satisfied ≤ 300ms, tolerating ≤ 1.2s)
(
  sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m]))
  +
  sum(rate(http_request_duration_seconds_bucket{le="1.2"}[5m]))
)/ 2
/
sum(rate(http_request_duration_seconds_count[5m]))

# Result interpretation:
# 1.0    = all users satisfied
# 0.85+  = excellent
# 0.7-0.85 = good
# < 0.5  = poor
```

Bucket design is an instrumentation decision with query consequences. More buckets around the SLO target give better percentile accuracy where you care most, while too many buckets across too many labels multiply the number of time series. For a web API with a two hundred millisecond target, dense buckets around fast-path and SLO values are more valuable than fine resolution across very slow outliers.

```
CHOOSING HISTOGRAM BUCKETS
──────────────────────────────────────────────────────────────

Default Prometheus buckets:
  [.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10]

Custom buckets (for a web API with 200ms SLO):
  [.01, .025, .05, .1, .2, .3, .5, .75, 1, 2, 5]
  ^^^                    ^^^
  Fine resolution        Bucket AT your SLO target
  for fast path          for accurate SLO reporting

Rules:
1. Always have a bucket at or near your SLO target
2. More buckets near expected values = better accuracy
3. Wider gaps at extremes (>1s) are fine
4. Too many buckets = high cardinality (each bucket is a series)
5. The +Inf bucket is always auto-created
```

Native histograms add another option in newer Prometheus versions, but classic bucket histograms remain common in Kubernetes ecosystems and exam material. The operational principle stays the same: know whether your query is reading bucket counters, sum and count counters, or native histogram samples. If a percentile looks impossibly precise, check the bucket layout before trusting the result.

## Subqueries and Recording Rules

Subqueries evaluate an instant-vector expression repeatedly over a range, producing a range vector that can feed an over-time function. They are useful when the question is about the behavior of a computed expression, not the raw metric itself. For example, "what was the peak error ratio over six hours" requires computing the error ratio many times and then taking the maximum of those computed values.

```promql
# Basic syntax: <instant_query>[<range>:<resolution>]

# Average of the max over last hour, sampled every 5 minutes
avg_over_time(max by (instance)(rate(http_requests_total[5m]))[1h:5m])

# Standard deviation of error rate over the last 6 hours
stddev_over_time(
  (
    sum(rate(http_requests_total{status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total[5m]))
  )[6h:1m]
)

# Min value over last hour (useful for detecting dips)
min_over_time(up[1h:1m])
# Returns 0 if target was down at any point in the last hour
```

Subqueries are expressive, but they shift work to query time. A dashboard that evaluates a complex subquery every refresh can make Prometheus repeatedly scan and recompute data that could have been stored once as a recording rule. Use subqueries for exploration, one-off diagnosis, and low-traffic panels; promote them to recording rules when they become shared operational interfaces.

| Function | Purpose | Example Use |
|----------|---------|-------------|
| `avg_over_time()` | Average over range | Smooth volatile metric |
| `min_over_time()` | Minimum in range | Detect any downtime in window |
| `max_over_time()` | Maximum in range | Find peak usage |
| `sum_over_time()` | Sum of all samples | Total accumulation |
| `count_over_time()` | Count of samples | Detect missing scrapes |
| `quantile_over_time()` | Percentile over time | P95 of a gauge over 1 hour |
| `stddev_over_time()` | Standard deviation | Detect unusual variance |
| `last_over_time()` | Most recent value | Fill gaps in sparse metrics |
| `present_over_time()` | 1 if any sample exists | Check metric existence |

Over-time functions help with gauges, existence checks, and computed ratios, but they are not substitutes for counter functions. `avg_over_time(http_requests_total[5m])` averages raw counter values and usually tells you very little; `rate(http_requests_total[5m])` tells you request speed. When a query feels awkward, name the metric type first, then choose a function that matches that type.

```
RECORDING RULE NAMING: level:metric:operations
──────────────────────────────────────────────────────────────

level    = aggregation level (e.g., job, instance, cluster)
metric   = the original metric name
operations = list of operations applied (e.g., rate5m)

Examples:
  job:http_requests:rate5m
  instance:node_cpu:ratio
  cluster:http_errors:rate5m_ratio

IMPORTANT: Use colons (:) as separators.
           Raw metrics use underscores (_).
           Recording rules use colons (:).
           This makes it instantly clear which metrics are computed.
```

Recording rule names should encode the aggregation level, the underlying metric idea, and the operation already performed. That convention makes dashboards easier to audit because a metric such as `job:http_requests:rate5m` tells you it is already a job-level five-minute rate. It also prevents double-rating mistakes, where someone accidentally applies `rate()` to a recorded rate because the name looked like a raw counter.

```yaml
groups:
  - name: http_recording_rules
    interval: 30s
    rules:
      # Request rate per job
      - record: job:http_requests:rate5m
        expr: sum by (job)(rate(http_requests_total[5m]))

      # Error rate per job
      - record: job:http_errors:rate5m
        expr: sum by (job)(rate(http_requests_total{status=~"5.."}[5m]))

      # Error ratio per job (for SLO dashboards)
      - record: job:http_error_ratio:rate5m
        expr: |
          job:http_errors:rate5m
          /
          job:http_requests:rate5m

      # P99 latency per job
      - record: job:http_latency_p99:rate5m
        expr: |
          histogram_quantile(0.99,
            sum by (job, le)(rate(http_request_duration_seconds_bucket[5m]))
          )

      # Memory utilization per namespace
      - record: namespace:container_memory_utilization:ratio
        expr: |
          sum by (namespace)(container_memory_usage_bytes{container!=""})
          /
          sum by (namespace)(container_spec_memory_limit_bytes{container!=""} > 0)

      # CPU utilization per node
      - record: node:node_cpu_utilization:ratio_rate5m
        expr: |
          1 - avg by (node)(rate(node_cpu_seconds_total{mode="idle"}[5m]))
```

Rules also create a contract between teams. An application team can own raw instrumentation, a platform team can own cluster-level recording rules, and dashboard authors can depend on the recorded metric shape without copying complex expressions everywhere. That contract only works if the rule is reviewed like code: check labels, cardinality, evaluation interval, and whether the expression hides a failure mode that an alert still needs to see.

```
CREATE A RECORDING RULE WHEN:
──────────────────────────────────────────────────────────────

1. Dashboard query takes > 1 second to execute
2. Same query is used in multiple dashboards
3. Query is used in alerting rules (pre-compute = faster evaluation)
4. You need to aggregate high-cardinality metrics down
5. You want consistent values across different consumers
6. You need longer time ranges on an expensive query

DON'T create a recording rule when:
1. Query is simple and fast (e.g., up == 0)
2. Only used in one place
3. The metric is already low-cardinality
```

The decision is partly technical and partly social. A recording rule speeds up repeated reads, but it also creates another metric name that people will use and misunderstand if it is poorly named. Treat recording rules as public APIs for observability, and reserve ad hoc PromQL for exploration until the query has proven its value.

## Worked Example: From Symptom to Query

Exercise scenario: the platform on-call receives a page that says checkout latency is breaching its objective, but the first dashboard only shows average latency and total request rate. The average line is slightly higher than usual, not alarming, and the request rate is normal. A weak response would be to reload the dashboard repeatedly; a stronger response is to turn the symptom into a sequence of PromQL questions that preserve the dimensions most likely to explain user impact.

Start with the distribution, because latency incidents are rarely uniform. A service-level P99 query using `histogram_quantile()` and `sum by (le, service)` answers whether checkout has a tail problem at all. If checkout is the only affected service, keep `service` and add one customer-experience label at a time, such as route, status class, region, or payment method. Adding every label at once creates a noisy table; adding one meaningful label at a time creates a diagnostic path.

Once a cohort appears, compare latency with error ratio for the same label shape. If payment-card traffic has high P99 latency and also high five-hundred-level responses, the user experience is probably failing rather than merely slow. If latency is high but errors stay normal, the next question might be dependency wait time, queue depth, or saturation. PromQL is useful here because each query result changes the next question instead of simply adding more charts.

The label shape must stay consistent while you compare signals. If latency is grouped by `payment_method` and error ratio is grouped by `service`, you are not comparing the same population. Rewrite the error-ratio numerator and denominator so both aggregate by the same labels that identified the latency cohort. This is the same constructive-alignment skill the quiz tests: the query must preserve enough labels to answer the operational question and drop labels that would distort the comparison.

Now check whether the apparent cohort could be a data artifact. Run the numerator and denominator of the error-ratio query separately, inspect labels, and look for empty joins or missing series. Then check `resets()` for the relevant counters, because a wave of pod restarts can create confusing graphs around the incident window. Prometheus compensates for counter resets in `rate()`, but reset frequency is still evidence about workload health and deployment behavior.

If the latency query is expensive, do not immediately turn it into a recording rule. First decide whether the expression is a one-time investigation or a query that should become part of the team’s normal SLO view. One-time investigation queries can be expensive because humans run them sparingly. Shared dashboards and alerting rules need predictable cost, stable label shape, and names that explain exactly what computation has already happened.

Suppose the cohort is real and the team wants a permanent panel for P99 checkout latency by payment method. The recording rule should preserve `payment_method` and the percentile result, but it should not preserve pod-level or instance-level labels that would make the panel unstable after every rollout. A useful rule name communicates both level and operation, while the expression documents why `le` was preserved until `histogram_quantile()` finished.

Next evaluate whether the alert should fire on the percentile directly or on an error-budget style ratio. Direct percentile alerts can be helpful for simple services, but they may page during short traffic bursts that do not consume meaningful budget. Ratio-based SLO alerts often provide better operational signal because they connect bad events with an allowed budget. The PromQL lesson is that syntax is only the entry point; alert quality comes from matching the expression to the service objective.

During this investigation, avoid the temptation to use `irate()` simply because it makes the spike more dramatic. If the question is "what changed in the last two scrapes," `irate()` is a good debugging lens. If the question is "should a human be paged," a stable `rate()` window plus an alert `for` duration is usually more responsible. The same raw counter can support both workflows when each query is honest about its purpose.

Stale series deserve a final check when a target disappeared near the incident. Prometheus marks series stale when targets stop exposing them, and range functions can still see recent samples inside their windows. If a dashboard appears to show an old pod contributing traffic after it was replaced, compare the graph range, selector labels, and scrape target status before treating the value as current behavior. This prevents a stale diagnostic branch from wasting investigation time.

The whole flow is deliberately mechanical: distribution first, cohort next, ratio comparison, data-artifact checks, then promotion to a dashboard or recording rule only after the query earns that status. Experienced operators look fast because these steps become habits, not because they skip reasoning. In PromQL, speed comes from knowing which labels and functions can answer the next question with the least distortion.

This worked example also explains why practice should happen in a live Prometheus UI. Static examples teach syntax, but live labels teach humility. You will see missing limits, renamed jobs, empty joins, and exporters that expose slightly different labels than a copied query expected. Treat those mismatches as part of the lesson, because production PromQL is mostly the craft of adapting correct ideas to the label reality in front of you.

## Patterns & Anti-Patterns

A strong PromQL pattern starts with the question, then chooses the smallest label set that can answer it. For service health, aggregate to `service` and perhaps `namespace`, then drill down to `pod` or `route` only after the service-level symptom is visible. This keeps overview dashboards readable and reduces the chance that Prometheus spends most of its time computing panels nobody can interpret quickly.

Another reliable pattern is to build ratios from two expressions with identical output labels. Error ratio, saturation ratio, request success ratio, and memory utilization all become safer when the numerator and denominator use the same `sum by (...)` clause before division. The query becomes easier to review because each side answers the same dimensional question before Prometheus matches the vectors.

For latency, prefer histograms or native histograms over client-side summary quantiles when you need aggregation across pods or services. Histogram buckets can be summed by `le` and service labels before `histogram_quantile()`, which lets you compute fleet-level percentiles. Client-side quantiles are already calculated per process, so averaging or summing them across replicas produces numbers that look precise but do not represent the combined distribution.

The matching anti-pattern is to begin with a dashboard panel copied from another service and then add labels until it seems to work. This encourages accidental joins, stale selectors, and hidden cardinality costs. A better approach is to write the query in stages, inspect labels at each stage, and record why each aggregation keeps or drops a label.

The alerting anti-pattern is using `irate()` or a very short `rate()` range because it makes a demo alert fire quickly. That alert will flap in production when scrape timing shifts or one sample jumps. Use a stable `rate()` window, add a reasonable `for` duration in the alerting rule, and reserve sharper queries for debugging dashboards where human judgment is present.

The recording-rule anti-pattern is precomputing every expression before anyone has used it. Recording rules consume storage, evaluation time, and naming attention, so premature rules become clutter that looks authoritative. Promote a query when it is shared, expensive, used for alerting, or needed as a stable SLO input; otherwise keep it close to the investigation that created it.

## Decision Framework

When choosing a PromQL approach, first identify the metric type. If the metric is a counter, ask whether you need speed or total count, then choose `rate()` for per-second behavior or `increase()` for total change over a range. If the metric is a gauge, avoid counter functions and consider direct aggregation, `avg_over_time()`, `max_over_time()`, or comparisons depending on whether the value represents current state or history.

Next decide the label shape of the answer. If the audience is an on-call engineer looking at an overview page, preserve low-cardinality ownership and service labels. If the audience is actively debugging, include route, pod, status, or dependency labels only when they narrow the question. The best query is not the one that preserves the most dimensions; it is the one that leaves exactly the dimensions needed for the next decision.

Then choose whether the expression should remain ad hoc, become a dashboard query, or become a recording rule. Ad hoc queries are allowed to be expensive and exploratory. Dashboard queries should be predictable and readable. Recording rules should be named, reviewed, and stable enough that other teams can build on them without rereading the full expression each time.

Finally, test the query against failure modes. Ask whether a counter reset would distort it, whether a missing label would make a join empty, whether a new high-cardinality label would survive aggregation, and whether stale series could make an old target appear current. PromQL skill is the habit of checking those mechanics before the graph becomes evidence in an incident.

Use this framework as a review checklist before you paste a query into an alert, a shared dashboard, or a recording rule file. A query that is acceptable for exploration can be too expensive, too noisy, or too ambiguous for shared operational use. The promotion step should include a plain-language statement of the question, the metric type involved, the labels intentionally preserved, the labels intentionally dropped, and the failure modes already checked.

The same review habit helps during exams because many PromQL questions are disguised label-shape questions. If the expression divides two vectors, inspect whether both sides produce compatible labels. If the expression computes a percentile, inspect whether `le` survived until the quantile function. If the expression uses a range, inspect whether the function expects a range vector and whether the window contains enough samples. These checks are faster than trying to remember every example by rote.

In production, write down the final query reasoning near the dashboard panel or recording rule when the system allows it. Future operators need to know why a five-minute range was chosen, why a label was excluded, and why a percentile is grouped at one level rather than another. Good observability is not only a set of correct expressions; it is a set of correct expressions whose intent remains understandable after the original author has moved on.

## Did You Know?

- **PromQL processes queries in a pull-style evaluation path too.** When you query, Prometheus reads time-series data from disk or memory and evaluates expressions; it does not pre-compute arbitrary expressions unless you define recording rules.
- **The `rate()` function handles counter resets automatically.** It detects decreases in counter values and compensates, which is why pod restarts do not automatically break well-formed rate queries.
- **`histogram_quantile()` uses interpolation between bucket boundaries.** If your buckets are sparse around the SLO target, the percentile can be technically valid while still too imprecise for a service-level decision.
- **PromQL has no `JOIN` keyword.** Binary operators with `on()`, `ignoring()`, `group_left()`, and `group_right()` provide join-like behavior with time-series label matching.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Using `rate()` on gauges | The query writer remembers that rates are common but forgets that gauges can rise and fall naturally. | Use `rate()` only on counters; for gauges, use direct values, over-time functions, or `deriv()` when a trend is really needed. |
| Forgetting `rate()` on counters | Raw counters look like active traffic in a graph because the line keeps rising. | Wrap request, error, CPU, and bucket counters in `rate()` or `increase()` before aggregation or comparison. |
| Choosing a range that is too short | The range contains too few scrapes, so one missed scrape or one noisy sample dominates the result. | Use at least four times the scrape interval, then lengthen the range for alerting or SLO stability. |
| Dropping `le` before `histogram_quantile()` | The aggregation is written like ordinary service aggregation and destroys bucket boundaries. | Always keep `le` in the `by()` clause until after `histogram_quantile()` has computed the percentile. |
| Alerting on `irate()` | A debugging query is promoted directly into an alert because it reacts quickly in a test. | Use `rate()` for alerts, pair it with an alert `for` duration, and keep `irate()` for human-driven investigation. |
| Grouping by high-cardinality labels on overview dashboards | Labels such as path, pod, container, or user identifiers feel useful during exploration. | Start with service-level or namespace-level aggregation, then provide drill-down panels for higher-cardinality dimensions. |
| Dividing vectors with mismatched labels | Each side works alone, so the empty or partial division result looks surprising. | Compare labels on both sides and use matching modifiers such as `on()` or `ignoring()` deliberately. |
| Treating recording rules as harmless shortcuts | A copied query becomes a permanent metric without review of naming, labels, or cost. | Promote only shared or expensive expressions, use `level:metric:operations` names, and review rules as observability APIs. |

## Quiz

Test your PromQL knowledge with scenario-style prompts that mirror the decisions you make during operations, especially when labels, counters, histograms, and recording rules interact under pressure.

<details>
<summary>1. Your team graphs `http_requests_total[5m]` and gets no useful graph. What should you change, and why?</summary>

Use `rate(http_requests_total[5m])` if you need requests per second, or `increase(http_requests_total[5m])` if you need total requests over the window. The selector with `[5m]` returns a range vector, which is a history of samples per series rather than one value per series. Graphing and arithmetic generally need an instant vector, so a range function must convert the sample history into a current value. This also tests the outcome about constructing PromQL queries from the correct vector type.
</details>

<details>
<summary>2. A service-level error ratio returns an empty result even though the numerator and denominator each return data alone. What do you inspect first?</summary>

Inspect the labels produced by each side of the division, especially the labels left after `sum by (...)` or `sum without (...)`. Prometheus matches vectors by labels, so a numerator grouped by `service,status` will not divide cleanly by a denominator grouped only by `service`. The fix is usually to make both sides produce the same output label set before division, or to use `ignoring(status)` only when retaining the status label is intentional. Do not widen selectors first, because that can hide the label-shape bug and add cardinality.

```promql
sum by (service)(rate(http_requests_total{status=~"5.."}[5m]))
/
sum by (service)(rate(http_requests_total[5m]))
* 100
```
</details>

<details>
<summary>3. A P99 latency query uses `sum by (service)(rate(http_request_duration_seconds_bucket[5m]))` inside `histogram_quantile()`. What is wrong?</summary>

The aggregation drops the `le` label, which removes the bucket boundaries that `histogram_quantile()` needs for interpolation. The corrected query should keep both `le` and the desired grouping label, such as `sum by (le, service)(rate(http_request_duration_seconds_bucket[5m]))`. Without `le`, the bucket counters are merged into a value that no longer describes a distribution. This is why histogram queries must be reviewed for label preservation, not only for syntax.

```promql
# WRONG — le is dropped, buckets are merged:
histogram_quantile(0.99, sum by (service)(rate(metric_bucket[5m])))

# RIGHT — le is preserved, buckets remain separate:
histogram_quantile(0.99, sum by (le, service)(rate(metric_bucket[5m])))
```
</details>

<details>
<summary>4. During a live incident, `irate()` shows a spike that `rate()` barely moves. Which query should become the alert condition?</summary>

The alert condition should normally use `rate()`, not `irate()`, because alerts need sustained and stable signals. `irate()` is useful for debugging what changed between the last two samples, but that sensitivity makes it prone to flapping when scrape timing shifts or one sample is unusual. A good workflow is to use `irate()` to see the sharp edge, confirm user impact with `rate()` over an appropriate window, and add an alert `for` duration. This keeps the alert focused on operational impact rather than graph noise.
</details>

<details>
<summary>5. A checkout dashboard averages latency and shows the SLO is fine, but users still report timeouts. Which PromQL approach should you try next?</summary>

Use histogram percentiles grouped by the labels that represent user cohorts, such as route, service, status class, or payment method, while keeping `le` for the percentile calculation. The average can hide a small but painful slow cohort because it divides total duration by total requests. A query such as `histogram_quantile(0.99, sum by (le, payment_method)(rate(http_request_duration_seconds_bucket{service="checkout"}[5m])))` exposes tail behavior by cohort. If the P99 is high for one label value, you have a focused path for dependency and saturation checks.
</details>

<details>
<summary>6. A dashboard repeats a six-hour subquery in several panels and Prometheus query latency is rising. What design change should you evaluate?</summary>

Evaluate converting the repeated expression into a recording rule with a name such as `job:http_error_ratio:rate5m` or another `level:metric:operations` form that matches the query. Subqueries are evaluated at query time, so repeated dashboard refreshes can force Prometheus to recompute the same expensive expression many times. A recording rule stores the precomputed result at evaluation intervals, making dashboards faster and values consistent across consumers. The tradeoff is that the recorded metric becomes a public observability contract, so review labels and naming carefully.

```promql
max_over_time(
  (
    sum(rate(http_requests_total{status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total[5m]))
  )[6h:5m]
)
```
</details>

<details>
<summary>7. A memory utilization query joins usage with limits and suddenly doubles the number of output series. What is the likely cause?</summary>

The likely cause is a many-to-one or one-to-many matching relationship that is not unique for the chosen join labels. A `group_left()` or `group_right()` modifier can legally expand series, but it should only be used when you understand the cardinality on both sides. Check `count by (namespace, pod, container)` or the relevant join keys for each metric before trusting the result. Then narrow the match with `on(...)`, remove duplicate metadata series, or aggregate one side to a unique shape before division.

```promql
sum by (node)(
  container_memory_usage_bytes{container!=""}
  * on(namespace, pod) group_left(node)
  kube_pod_info
)
```
</details>

<details>
<summary>8. A query uses `rate(metric[30s])` while Prometheus scrapes every fifteen seconds. Why can that mislead you, and what should you use instead?</summary>

A thirty-second range may contain only two samples, and one missed scrape can leave too little data for a reliable rate. In that case `rate()` behaves much like a very sharp instantaneous slope, which is fragile for dashboards and worse for alerts. Use at least a one-minute range for a fifteen-second scrape interval, and often use five minutes for stable operational views. The exact window should match how quickly the signal must react and how much noise the consumer can tolerate.

```
Time:    0s    15s    30s    45s    60s
Scrape:  |      |      |      |      |
         [--- 30s window ---]

Best case: 3 points (0s, 15s, 30s)
Worst case: 2 points (if window doesn't align perfectly)
```

```promql
rate(metric[1m])   # 4 points minimum — acceptable
rate(metric[5m])   # ~20 points — good smoothing, standard choice
```
</details>

## Hands-On Exercise: PromQL Workout

Practice PromQL on a live Prometheus instance with real metrics. The lab uses kube-prometheus-stack so you can query Kubernetes control-plane, node, pod, and container metrics in one place.

### Setup

```bash
# Create a kind cluster if you don't have one
kind create cluster --name promql-lab

# Install kube-prometheus-stack (includes Prometheus, Grafana, node-exporter)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.scrapeInterval=15s

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=monitoring \
  -n monitoring --timeout=120s
```

Before you run queries, confirm the stack is healthy enough to produce meaningful samples. A Prometheus UI with only one scrape does not give `rate()` enough history, and a cluster with missing node-exporter targets will make some examples look empty. Wait at least a few scrape intervals after the pods become ready so range functions can see real sample windows.

### Step 1: Access Prometheus UI

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090

# Open http://localhost:9090 in your browser
```

Keep one tab on the expression browser and another on the graph view. The expression browser helps you inspect labels and raw values, while the graph view makes rate window and `irate()` behavior easier to see. When a query returns nothing, use the expression browser to run smaller pieces before assuming the metric is absent.

### Step 2: Selector Practice

Type these queries in the Prometheus UI expression browser, and pause after each result to inspect the returned label names before continuing:

```promql
# 1. Find all targets
up

# 2. Filter by job
up{job="kubelet"}

# 3. Regex: find all kube-state-metrics series starting with "kube_pod"
{__name__=~"kube_pod.*"}

# 4. Negative filter: all HTTP metrics except health checks
{__name__=~"http.*", handler!~"/health|/ready"}
```

For each selector, click a returned series and read its labels before moving on. This habit trains you to see label shape as part of the data, not as a secondary detail. In the success criteria, treat "write selectors" as including the ability to predict which labels remain available for later aggregation or matching.

### Step 3: Rate Function Practice

```promql
# 5. CPU usage rate per node
rate(node_cpu_seconds_total{mode!="idle"}[5m])

# 6. Compare rate vs irate (switch between Graph tab to see difference)
rate(node_cpu_seconds_total{mode="user", cpu="0"}[5m])
irate(node_cpu_seconds_total{mode="user", cpu="0"}[5m])

# 7. Network bytes received (increase over 1 hour)
increase(node_network_receive_bytes_total{device="eth0"}[1h])
```

Graph the `rate()` and `irate()` expressions on the same time range, then change the graph range from a short window to a longer one. You should see that `irate()` is more jagged because it only uses the last two samples, while `rate()` smooths across the selected range. That visual difference is the reason the two functions belong in different operational contexts.

### Step 4: Aggregation Practice

```promql
# 8. Total CPU usage per node (aggregate across CPU cores)
sum by (instance)(rate(node_cpu_seconds_total{mode!="idle"}[5m]))

# 9. Top 3 pods by memory usage
topk(3, container_memory_usage_bytes{container!=""})

# 10. Count running pods per namespace
count by (namespace)(kube_pod_status_phase{phase="Running"})

# 11. Average memory usage per namespace
avg by (namespace)(container_memory_usage_bytes{container!=""})
```

After each aggregation, compare the label set with the unaggregated query. The value changed, but the more important teaching point is which labels survived. If a later binary operation or dashboard legend needs a label that was removed here, the query must be redesigned before the aggregation point.

### Step 5: Binary Operators and Joins

```promql
# 12. Memory utilization percentage per container
container_memory_usage_bytes{container!=""}
/ on(namespace, pod, container)
container_spec_memory_limit_bytes{container!=""}
* 100

# 13. Node CPU utilization (1 - idle ratio)
1 - avg by (instance)(rate(node_cpu_seconds_total{mode="idle"}[5m]))

# 14. Filesystem usage percentage per node
(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"})
/
node_filesystem_size_bytes{mountpoint="/"}
* 100
```

If the memory utilization query returns fewer series than expected, run both sides separately and inspect their labels. You are practicing diagnosis, not just syntax, so the goal is to explain whether missing limits, mismatched labels, or zero-valued limits caused the result. This same workflow applies to service ownership joins and node metadata enrichment.

### Step 6: Histogram Queries

```promql
# 15. P99 API server request latency
histogram_quantile(0.99,
  sum by (le)(rate(apiserver_request_duration_seconds_bucket[5m]))
)

# 16. P50 vs P99 comparison — add both to Graph tab
histogram_quantile(0.5,
  sum by (le)(rate(apiserver_request_duration_seconds_bucket[5m]))
)

# 17. Average request duration from histogram
rate(apiserver_request_duration_seconds_sum[5m])
/
rate(apiserver_request_duration_seconds_count[5m])
```

Compare P50, P99, and average request duration over the same displayed time range. If P50 and average are calm but P99 jumps, the control plane has a tail-latency problem rather than a general slowdown. That distinction is exactly why histogram query mechanics matter for both exam readiness and real Kubernetes operations.

### Success Criteria

You've completed this exercise when you can satisfy each checklist item from memory and explain the PromQL evaluation mechanics behind your answer:
- [ ] Construct PromQL queries with instant vector selectors, range vector selectors, and all four matcher types.
- [ ] Apply `rate()`, `irate()`, and `increase()` to counters and explain when each function is appropriate.
- [ ] Aggregate with `sum by`, `avg by`, and `topk` while explaining the difference between `by` and `without`.
- [ ] Compute histogram percentiles with `histogram_quantile()` while preserving the `le` label.
- [ ] Join two metrics using `on()` and `group_left()` after checking label cardinality.
- [ ] Diagnose misleading behavior from counter resets, stale or missing series, short ranges, and empty vector matches.
- [ ] Build a recording rule from a complex query using the `level:metric:operations` naming convention.

## Sources

- [Prometheus querying basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Prometheus operators](https://prometheus.io/docs/prometheus/latest/querying/operators/)
- [Prometheus functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Prometheus recording rules](https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/)
- [Prometheus recording rule best practices](https://prometheus.io/docs/practices/rules/)
- [Prometheus metric types](https://prometheus.io/docs/concepts/metric_types/)
- [Prometheus histograms and summaries](https://prometheus.io/docs/practices/histograms/)
- [Prometheus native histograms specification](https://prometheus.io/docs/specs/native_histograms/)
- [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Prometheus Operator API reference](https://prometheus-operator.dev/docs/api-reference/api/)
- [Helm chart repository for kube-prometheus-stack](https://prometheus-community.github.io/helm-charts)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [PromLabs Blog](https://promlabs.com/blog/)
- [Robust Perception Blog](https://www.robustperception.io/blog/)

## Next Module

Continue to [Module 1.2: Instrumentation & Alerting](../module-1.2-instrumentation-alerting/) to learn how client libraries, metric naming, exporters, and Alertmanager turn PromQL knowledge into production observability.

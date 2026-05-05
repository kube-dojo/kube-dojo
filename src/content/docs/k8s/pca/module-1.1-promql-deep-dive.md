---
revision_pending: true
title: "Module 1.1: PromQL Deep Dive"
slug: k8s/pca/module-1.1-promql-deep-dive
sidebar:
  order: 2
---
> **PCA Track** | Complexity: `[COMPLEX]` | Time: 50-60 min

## Prerequisites

Before starting this module:
- [Prometheus Module](/platform/toolkits/observability-intelligence/observability/module-1.1-prometheus/) — architecture, pull model, basic PromQL
- [Observability Theory](/platform/foundations/observability-theory/) — metrics concepts
- Basic Kubernetes knowledge
- A running Prometheus instance (kind/minikube with kube-prometheus-stack)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Construct** PromQL queries using range vectors, aggregation operators, and binary operations to answer production questions about latency, error rates, and saturation
2. **Apply** `histogram_quantile` and `rate()` correctly to compute percentile latencies and per-second rates from counter and histogram metrics
3. **Build** recording rules that pre-compute expensive queries for dashboard performance and SLO tracking
4. **Diagnose** misleading metric behavior (counter resets, label cardinality explosions, stale markers) by reasoning about PromQL evaluation mechanics

---

At traffic spikes, averages can stay inside SLOs while percentile latency and selected request cohorts degrade badly. PromQL tail-analysis is the first step to discovering which labels are carrying the pain and why. Keep the investigation explicit and label-specific to catch bottlenecks that aggregate graphs hide.

```promql
histogram_quantile(0.99,
  sum by (le, payment_method)(rate(http_request_duration_seconds_bucket{service="checkout"}[5m]))
)
```

---

## Why This Module Matters

PromQL is 28% of the PCA exam — the single largest domain. But more importantly, PromQL is the language you use to answer questions during outages. Can you write a query that shows the error rate by service? Can you compute the 99th percentile latency? Can you join two metrics to calculate resource utilization as a percentage?

This module takes you beyond the basics covered in the Prometheus fundamentals module. You'll learn every selector type, master rate functions, build complex aggregations, work with histograms deeply, use binary operators for metric joins, write recording rules, and understand subqueries.

## Did You Know?

- **PromQL processes queries in a "pull" fashion too** — when you query, Prometheus reads time-series data from disk/memory and evaluates expressions. It doesn't pre-compute results (that's what recording rules are for).
- **The `rate()` function is mathematically sophisticated** — it handles counter resets automatically by detecting decreases in values and compensating. This means you never need to worry about pod restarts breaking your rate calculations.
- **`histogram_quantile()` uses linear interpolation** between bucket boundaries. If your buckets are `[0.1, 0.5, 1.0, +Inf]` and the 95th percentile falls between 0.5 and 1.0, Prometheus draws a straight line between those points to estimate the value. Poor bucket choices = poor accuracy.
- **PromQL has no `JOIN` keyword** — but binary operators with `on()` and `group_left()` effectively give you the same power as SQL joins, just with different syntax.

---

## Selectors: Finding Your Data

### Instant Vector Selectors

An instant vector selector returns the most recent sample for each matching time series.

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

**Label matcher types:**

| Matcher | Meaning | Example |
|---------|---------|---------|
| `=` | Exact match | `{job="api"}` |
| `!=` | Not equal | `{job!="test"}` |
| `=~` | Regex match | `{status=~"5.."}` |
| `!~` | Negative regex | `{path!~"/health\|/ready"}` |

**Important**: Every selector must have at least one matcher that doesn't match the empty string. `{job=~".*"}` alone is invalid because it matches everything including empty — use `{job=~".+"}` instead.

### Range Vector Selectors

A range vector returns a window of samples for each series. Required for functions like `rate()`.

```promql
# Last 5 minutes of samples
http_requests_total{method="GET"}[5m]

# Last 1 hour
http_requests_total[1h]

# Valid time durations: ms, s, m, h, d, w, y
# 5m = 5 minutes, 1h30m = 90 minutes, 1d = 1 day
```

**You cannot graph a range vector directly.** Range vectors are inputs to functions:

```promql
# WRONG: Cannot graph this
http_requests_total[5m]

# RIGHT: rate() converts range vector to instant vector
rate(http_requests_total[5m])
```

### Offset Modifier

Compare current values to historical data:

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

### The @ Modifier

Pin a query to a specific timestamp (useful for debugging past incidents):

```promql
# Value at a specific Unix timestamp
http_requests_total @ 1704067200

# Value at the start of the query range
http_requests_total @ start()

# Value at the end of the query range
http_requests_total @ end()
```

---

## Rate Functions: The Counter Toolkit

Counters only go up (except on reset). You almost never want the raw counter value — you want the *rate of change*.

### rate()

Calculates the average per-second rate of increase over the range:

```promql
# Average requests per second over last 5 minutes
rate(http_requests_total[5m])
# If counter went from 1000 to 1300 over 5 min:
# rate = (1300 - 1000) / 300 seconds = 1.0 req/s

# CPU usage rate (seconds of CPU per second of wall time)
rate(process_cpu_seconds_total[5m])
# Result of 0.25 means 25% of one CPU core
```

**How rate() handles counter resets:**

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

### irate()

Uses only the last two data points to compute an instantaneous rate:

```promql
# Instantaneous request rate
irate(http_requests_total[5m])
# Only uses the last 2 samples within the 5m window
# Much more volatile than rate()
```

**When to use which:**

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

### increase()

Total increase over the range (like rate * seconds):

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

**Relationship between rate and increase:**

```promql
# These are approximately equivalent:
increase(http_requests_total[1h])  ≈  rate(http_requests_total[1h]) * 3600
```

### resets()

Count the number of counter resets (pod restarts, process crashes):

```promql
# How many times has this counter reset in the last hour?
resets(http_requests_total[1h])

# High reset count may indicate crash loops
resets(process_start_time_seconds[1h]) > 5
```

### Common Pitfall: Range Too Short

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

---

## Aggregation Operators

Aggregation operators combine multiple time series into fewer series.

### Core Aggregation Functions

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

### Grouping: by and without

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

**Real-world aggregation examples:**

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

---

## Binary Operators and Vector Matching

### Arithmetic Operators

```promql
# Simple arithmetic with scalars
node_memory_MemTotal_bytes / 1024 / 1024 / 1024
# Convert bytes to GiB

# Arithmetic between two vectors
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100
# Memory utilization percentage
# Labels must match on both sides!
```

### Comparison Operators

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

### Logical/Set Operators

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

### Vector Matching: on() and ignoring()

When binary operations involve two vectors, Prometheus must match series from each side. By default, all labels must match. Use `on()` or `ignoring()` to control matching.

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

### Many-to-One and One-to-Many: group_left() / group_right()

When one side has more series than the other (different cardinality), you need `group_left` or `group_right`:

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

---

## Histogram Queries

### Understanding Histogram Metrics

A histogram metric generates three types of series:

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

### histogram_quantile()

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

**Critical rule**: When aggregating before `histogram_quantile()`, you MUST keep the `le` label:

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

### Average Latency from Histogram

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

### Apdex Score from Histogram

Application Performance Index — user satisfaction metric:

```promql
# Apdex with target = 300ms (satisfied ≤ 300ms, tolerating ≤ 1.2s)
(
  sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m]))
  +
  sum(rate(http_request_duration_seconds_bucket{le="1.2"}[5m]))
)
/ 2
/
sum(rate(http_request_duration_seconds_count[5m]))

# Result interpretation:
# 1.0    = all users satisfied
# 0.85+  = excellent
# 0.7-0.85 = good
# < 0.5  = poor
```

### Histogram Bucket Selection Guidelines

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

---

## Subqueries

Subqueries let you evaluate an instant vector expression over a range, creating a range vector that can be fed to functions.

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

**Common *_over_time functions:**

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

**Subquery vs recording rule**: Subqueries are evaluated at query time (expensive). If you use a subquery frequently, convert it to a recording rule.

---

## Recording Rules

### Naming Convention

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

### Recording Rule Examples

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

### When to Create Recording Rules

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

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `rate()` on gauges | Nonsensical results | Use `rate()` only on counters; use `deriv()` for gauge rate-of-change |
| Forgetting `rate()` on counters | Dashboard shows ever-increasing line | Always wrap counter queries in `rate()` or `increase()` |
| Range too short for `rate()` | Missing or inaccurate results | Range >= 4x scrape_interval (e.g., `[1m]` for 15s scrape) |
| Dropping `le` in histogram agg | `histogram_quantile()` fails | Always include `le` in `by()` clause |
| Alerting on `irate()` | Flapping alerts | Use `rate()` for alerts; `irate()` for debugging only |
| High-cardinality `by()` | Slow queries, memory issues | Group by low-cardinality labels; drop instance/pod where possible |
| `sum without ()` vs `sum()` | Unexpected label retention | `sum()` drops all labels; `sum without(x)` drops only `x` |
| Dividing without matching labels | Empty result or wrong joins | Use `on()` and `group_left()` for cross-metric division |
| `count()` instead of `count_over_time()` | Counts series, not samples | `count(up)` = number of series; `count_over_time(up[1h])` = samples per series |
| Subquery without resolution | Prometheus picks default | Always specify resolution: `metric[1h:5m]` not `metric[1h:]` |

---

## Quiz

Test your PromQL knowledge — these reflect PCA exam difficulty:

<details>
<summary>1. What is the difference between an instant vector and a range vector? When does PromQL require each?</summary>

**Answer**:

- **Instant vector**: Returns one sample per time series (the most recent value within the lookback window). Used for graphing, comparison, and most operations.
  - Example: `http_requests_total{method="GET"}`

- **Range vector**: Returns multiple samples per time series over a time window. Cannot be graphed directly — must be passed to a function.
  - Example: `http_requests_total{method="GET"}[5m]`

**When each is required**:
- `rate()`, `increase()`, `irate()`, `resets()`, `*_over_time()` functions require range vectors
- Arithmetic, comparison, aggregation, and `histogram_quantile()` operate on instant vectors
- A range vector is only valid as a direct argument to a function that expects one
</details>

<details>
<summary>2. Write a PromQL query to calculate the error rate (as a percentage) for each service, where errors are HTTP 5xx responses.</summary>

**Answer**:

```promql
sum by (service)(rate(http_requests_total{status=~"5.."}[5m]))
/
sum by (service)(rate(http_requests_total[5m]))
* 100
```

Key points:
- Use `rate()` on the counter, not the raw counter value
- Use `sum by (service)` to aggregate across instances/pods
- Both numerator and denominator must have the same `by()` clause
- Multiply by 100 to convert ratio to percentage
- `status=~"5.."` matches 500, 501, 502, etc.
</details>

<details>
<summary>3. Why must you always include the `le` label when aggregating before `histogram_quantile()`? What happens if you don't?</summary>

**Answer**:

`histogram_quantile()` works by examining the cumulative bucket counts across different `le` (less-than-or-equal) boundaries. It uses these boundaries to interpolate where the requested percentile falls.

If you drop the `le` label during aggregation:
- All buckets get summed together into a single number
- `histogram_quantile()` has no bucket boundaries to interpolate between
- The result will be **meaningless or produce an error**

```promql
# WRONG — le is dropped, buckets are merged:
histogram_quantile(0.99, sum by (service)(rate(metric_bucket[5m])))

# RIGHT — le is preserved, buckets remain separate:
histogram_quantile(0.99, sum by (le, service)(rate(metric_bucket[5m])))
```
</details>

<details>
<summary>4. Explain the difference between `quantile()` and `histogram_quantile()`. When would you use each?</summary>

**Answer**:

- **`quantile(phi, instant_vector)`**: Computes the phi-quantile *across series*. Takes a set of instant vector values and finds the value at the given quantile.
  - Example: `quantile(0.95, rate(http_requests_total[5m]))` — "the 95th percentile of request rates across all pods"
  - Input: instant vector (multiple series, each with one value)

- **`histogram_quantile(phi, instant_vector)`**: Computes the phi-quantile *within a histogram*. Uses cumulative bucket counts to estimate the value at the given quantile.
  - Example: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` — "the request duration that 95% of requests were faster than"
  - Input: instant vector that MUST contain `le` labels (histogram buckets)

**Use `quantile()`** when you want a percentile across a set of gauge-like values (e.g., "what's the 95th percentile CPU usage across my fleet?").

**Use `histogram_quantile()`** when computing latency percentiles or any distribution metric stored as a histogram.
</details>

<details>
<summary>5. You have two metrics: `container_memory_usage_bytes` (labels: namespace, pod, container) and `kube_pod_info` (labels: namespace, pod, node, host_ip). Write a query that shows memory usage per node.</summary>

**Answer**:

```promql
sum by (node)(
  container_memory_usage_bytes{container!=""}
  * on(namespace, pod) group_left(node)
  kube_pod_info
)
```

Explanation:
- `container_memory_usage_bytes` has no `node` label
- `kube_pod_info` has the `node` label and can be joined on `namespace, pod`
- `on(namespace, pod)` specifies the join keys
- `group_left(node)` brings the `node` label from the right side (many-to-one: many containers per pod info)
- `sum by (node)` aggregates the result by node
- `container!=""` excludes the pause container
</details>

<details>
<summary>6. What is a subquery? Write a subquery that finds the maximum error rate over the last 6 hours, sampled every 5 minutes.</summary>

**Answer**:

A **subquery** evaluates an instant vector expression repeatedly over a range at a specified resolution, producing a range vector. This range vector can then be passed to `*_over_time()` functions.

Syntax: `<instant_query>[<range>:<resolution>]`

```promql
max_over_time(
  (
    sum(rate(http_requests_total{status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total[5m]))
  )[6h:5m]
)
```

This evaluates the error rate expression every 5 minutes over the past 6 hours, then takes the maximum of all those values. Useful for answering: "What was the peak error rate in the last 6 hours?"

Note: Subqueries are expensive because Prometheus must evaluate the inner expression at every step. For frequently-used subqueries, consider a recording rule instead.
</details>

<details>
<summary>7. What is the recording rule naming convention? Why do recording rules use colons while raw metrics use underscores?</summary>

**Answer**:

**Naming convention**: `level:metric:operations`

- `level`: The aggregation level (e.g., `job`, `instance`, `namespace`, `cluster`)
- `metric`: The base metric name
- `operations`: Functions applied (e.g., `rate5m`, `ratio`)

Examples:
- `job:http_requests:rate5m` — request rate aggregated to job level
- `instance:node_cpu:ratio` — CPU ratio at instance level
- `namespace:container_memory:sum` — memory summed per namespace

**Why colons?** Convention separates raw metrics (underscores only) from computed metrics (colons). When you see `job:http_requests:rate5m`, you immediately know:
1. This is a recording rule, not a raw metric
2. It's aggregated to the job level
3. It's a 5-minute rate

This makes it easy to audit which metrics are "real" vs. pre-computed.
</details>

<details>
<summary>8. Given a 15-second scrape interval, explain why `rate(metric[30s])` might give inaccurate results. What range should you use?</summary>

**Answer**:

With a 15-second scrape interval, a 30-second range window will contain at most 2-3 data points (depending on alignment):

```
Time:    0s    15s    30s    45s    60s
Scrape:  |      |      |      |      |
         [--- 30s window ---]

Best case: 3 points (0s, 15s, 30s)
Worst case: 2 points (if window doesn't align perfectly)
```

Problems:
- With only 2 points, `rate()` becomes equivalent to `irate()` — it's just the slope between two points with no smoothing
- A single anomalous scrape will dominate the result
- If one scrape is missed (network blip), you might have only 1 point — `rate()` returns nothing

**Minimum recommended range**: `4 × scrape_interval = 60s`

```promql
rate(metric[1m])   # 4 points minimum — acceptable
rate(metric[5m])   # ~20 points — good smoothing, standard choice
```

The `[5m]` range is the de facto standard because it balances responsiveness with stability.
</details>

---

## Hands-On Exercise: PromQL Workout

Practice PromQL on a live Prometheus instance with real metrics.

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

### Step 1: Access Prometheus UI

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090

# Open http://localhost:9090 in your browser
```

### Step 2: Selector Practice

Type these queries in the Prometheus UI expression browser:

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

### Success Criteria

You've completed this exercise when you can:
- [ ] Write instant and range vector selectors with all four matcher types
- [ ] Use `rate()`, `irate()`, and `increase()` and explain when to use each
- [ ] Aggregate with `sum by`, `avg by`, `topk` and understand `by` vs `without`
- [ ] Compute histogram percentiles with `histogram_quantile()`
- [ ] Join two metrics using `on()` and `group_left()`
- [ ] Explain why the 4x scrape_interval rule matters for `rate()` ranges
- [ ] Convert a complex query into a recording rule with proper naming

---

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **Selector types**: Instant vectors (one sample per series) vs range vectors (multiple samples per series over a time window)
- [ ] **Label matchers**: `=`, `!=`, `=~`, `!~` — regex uses RE2 syntax, every selector needs at least one non-empty matcher
- [ ] **rate() vs irate() vs increase()**: `rate` = smoothed per-second average (alerting), `irate` = instantaneous (debugging), `increase` = total count over range
- [ ] **4x rule**: Range for `rate()` should be >= 4 times the scrape interval
- [ ] **Aggregation operators**: `sum`, `avg`, `min`, `max`, `count`, `topk`, `quantile` with `by`/`without` for grouping
- [ ] **Binary operators**: Arithmetic, comparison, and logical operators with vector matching via `on()`/`ignoring()` and `group_left()`/`group_right()`
- [ ] **histogram_quantile()**: Needs `le` label, uses linear interpolation between buckets, bucket selection affects accuracy
- [ ] **Recording rules**: `level:metric:operations` naming convention with colons, pre-compute expensive queries
- [ ] **Subqueries**: `expr[range:resolution]` syntax for evaluating an expression over time, feed to `*_over_time()` functions

---

## Further Reading

- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/) — Quick reference by Julius Volz
- [Prometheus Querying Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/) — Official PromQL reference
- [PromLabs Blog](https://promlabs.com/blog/) — Deep PromQL articles
- [Robust Perception Blog](https://www.robustperception.io/blog/) — Brian Brazil's PromQL patterns
- [Recording Rules Best Practices](https://prometheus.io/docs/practices/rules/) — Official conventions

---

## Next Module

Continue to [Module 2: Instrumentation & Alerting](../module-1.2-instrumentation-alerting/) to learn about client libraries, metric naming, exporters, and Alertmanager configuration.

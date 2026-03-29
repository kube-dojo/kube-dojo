---
title: "Module 1.3: Grafana"
slug: platform/toolkits/observability-intelligence/observability/module-1.3-grafana
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- [Module 1.1: Prometheus](../module-1.1-prometheus/)
- [Module 1.2: OpenTelemetry](../module-1.2-opentelemetry/)
- Basic PromQL knowledge
- Understanding of metrics and time series

---

At 11:47 PM on Black Friday, the director of engineering at a major retail company pulled up the main Grafana dashboard on the war room TV. Three hundred engineers stared at the screen. Revenue was down 40% from projections and nobody knew why.

The dashboard showed 200 panels. Graphs for every conceivable metric—CPU, memory, disk, network, HTTP status codes, queue depths, cache hit rates. Everything looked... fine. Green across the board. Yet customers were abandoning carts at record rates.

"Which of these panels matters?" asked the CEO, who had flown in from vacation.

Silence. The dashboards had been built over three years by different teams. Some showed production data, others showed staging. Some used 5-minute rates, others used instantaneous values. Nobody knew what "green" actually meant because thresholds had never been set.

The team spent 47 minutes just figuring out which dashboard showed the real checkout service. By the time they found the problem—a third-party payment provider timing out—they had lost $3.2 million in sales.

The next quarter, they rebuilt their dashboards from scratch: one overview, four golden signals per service, consistent thresholds, linked drill-downs. The following Black Friday, they identified and routed around a similar payment issue in 4 minutes.

---

## Why This Module Matters

Data without visualization is just numbers. Grafana transforms raw metrics into actionable insights. It's the window into your systems—the first place you look during an incident, the source of truth for SLOs, the tool that makes observability accessible to everyone.

Grafana has evolved from a dashboarding tool into a complete observability platform. Understanding it deeply—beyond basic charts—unlocks powerful capabilities for correlation, alerting, and investigation.

## Did You Know?

- **Grafana is used by millions of users** at companies like Bloomberg, PayPal, and CERN—from startups to enterprises
- **The name "Grafana"** comes from combining "graphite" and "graphana" (an earlier fork). It was created in 2014 by Torkel Ödegaard
- **Grafana Labs' LGTM stack** (Loki, Grafana, Tempo, Mimir) provides a complete open-source alternative to commercial observability platforms
- **Dashboard variables** can reduce a 100-dashboard sprawl to 10 reusable dashboards—most teams don't use them enough

## Grafana Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GRAFANA ECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GRAFANA (Visualization)                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│    │
│  │  │Dashboards│  │ Explore  │  │ Alerting │  │  Users   ││    │
│  │  │          │  │          │  │          │  │  & Auth  ││    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘│    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │              DATA SOURCE PLUGINS                  │  │    │
│  │  │  Prometheus │ Loki │ Tempo │ Elasticsearch │ ...  │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│           ┌──────────────────┼──────────────────┐               │
│           ▼                  ▼                  ▼               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │  Prometheus  │   │    Loki      │   │    Tempo     │        │
│  │   (Mimir)    │   │   (logs)     │   │   (traces)   │        │
│  │   metrics    │   │              │   │              │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Grafana Stack (LGTM)

| Component | Purpose |
|-----------|---------|
| **Loki** | Log aggregation (like Prometheus for logs) |
| **Grafana** | Visualization and exploration |
| **Tempo** | Distributed tracing |
| **Mimir** | Scalable Prometheus metrics storage |

### War Story: The Dashboard That Cried Wolf

A fintech startup prided itself on comprehensive monitoring. They had 847 alert rules across 312 dashboards. "We monitor everything," the VP of Engineering boasted to investors.

**Monday 3:00 AM**: PagerDuty fires. "High CPU on auth-service." The on-call engineer checks—87% CPU but everything working. Acknowledges. Goes back to sleep.

**Monday 3:47 AM**: Another alert. "Memory pressure on auth-service." Same story. Acknowledges.

**Monday 4:12 AM**: "Disk I/O high on auth-service." The engineer starts wondering why auth-service is so needy tonight. Acknowledges.

**Monday 4:38 AM**: "Latency spike on auth-service." By now, the engineer is exhausted and frustrated. Just acknowledges without checking.

**Monday 5:15 AM**: Customer complaints start rolling in. Logins are failing. The actual problem? A credential rotation job had stalled, causing auth retries to spike. The first three alerts were symptoms. The fourth one—latency—was the real signal.

But by then, alert fatigue had set in. The engineer ignored the one alert that mattered.

```
Dashboard/Alert Audit Results
─────────────────────────────────────────────────────────────────
Total dashboards:           312
Dashboards viewed monthly:  47
Total alert rules:          847
Alerts/week average:        156
True positives:             12 (7.7%)
MTTA (Mean Time to Ack):    23 minutes (should be <5)
Incidents missed due to fatigue: 3 in 6 months
─────────────────────────────────────────────────────────────────
Cost of alert fatigue: $1.2M in incident impact
```

**The Fix**:
1. **Deleted 734 alert rules** (kept only SLO-based alerts)
2. **Consolidated to 28 dashboards** (overview → service → component)
3. **Added thresholds with meaningful colors** (green/yellow/red = actual SLO risk)
4. **Created runbooks** linked from each alert
5. **Implemented alert routing**: Page for customer-facing, ticket for internal

**After 3 months**:
- Alerts per week: 156 → 12
- True positive rate: 7.7% → 89%
- MTTA: 23 min → 3 min
- Incidents missed: 0

**The Lesson**: More dashboards ≠ better visibility. The goal isn't monitoring everything—it's surfacing what matters.

## Dashboard Design Principles

### The Four Golden Signals

```
FOUR GOLDEN SIGNALS
─────────────────────────────────────────────────────────────────

Every dashboard should answer these questions:

1. LATENCY - How long does it take?
   └── Histogram quantiles (p50, p95, p99)

2. TRAFFIC - How much load are we handling?
   └── Requests per second

3. ERRORS - What's failing?
   └── Error rate as percentage

4. SATURATION - How "full" is the system?
   └── CPU, memory, queue depth


DASHBOARD LAYOUT
─────────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────────┐
│  SERVICE: $service    ENVIRONMENT: $env    TIME: $__interval  │
├────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │    Latency      │ │    Traffic      │ │    Errors       │ │
│  │    (p99)        │ │    (RPS)        │ │    (%)          │ │
│  │   STAT PANEL    │ │   STAT PANEL    │ │   STAT PANEL    │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐│
│  │                      REQUEST RATE                          ││
│  │  ════════════════════════════════════════════════         ││
│  │                                                            ││
│  └───────────────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────────────┐│
│  │                      LATENCY                               ││
│  │  ────────── p99  ────────── p95  ────────── p50           ││
│  │                                                            ││
│  └───────────────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────────────┐│
│  │                      ERROR RATE                            ││
│  │  ════════════════════════════════════════════════         ││
│  │                                                            ││
│  └───────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

### Dashboard Hierarchy

```
DASHBOARD ORGANIZATION
─────────────────────────────────────────────────────────────────

LEVEL 1: Overview Dashboard
├── All services at a glance
├── Traffic heatmap
├── Error hotspots
└── Click to drill down

LEVEL 2: Service Dashboard
├── Golden signals for one service
├── Dependencies (upstream/downstream)
├── Resource utilization
└── Click to drill down

LEVEL 3: Component Dashboard
├── Individual pods/instances
├── Detailed metrics
├── Debug information
└── Linked to logs/traces
```

## Dashboard Variables

### Variable Types

```
GRAFANA VARIABLES
─────────────────────────────────────────────────────────────────

QUERY VARIABLE (dynamic from data source)
  Name: service
  Query: label_values(http_requests_total, service)
  Result: Dropdown with all services

CUSTOM VARIABLE (static list)
  Name: percentile
  Values: 50,90,95,99
  Result: Dropdown with percentile options

INTERVAL VARIABLE (time-based)
  Name: interval
  Values: 1m,5m,15m,1h
  Auto: Based on time range

DATASOURCE VARIABLE
  Name: datasource
  Type: prometheus
  Result: Switch between Prometheus instances

TEXT VARIABLE (user input)
  Name: filter
  Type: text
  Result: Free-text filter input
```

### Using Variables

```promql
# In queries, use $variable or ${variable}
rate(http_requests_total{service="$service"}[$interval])

# Multi-value with regex
rate(http_requests_total{service=~"$service"}[$interval])

# With custom variable for percentile
histogram_quantile(0.$percentile,
  sum by (le)(rate(http_request_duration_bucket{service="$service"}[$interval]))
)
```

### Variable Configuration

```json
{
  "templating": {
    "list": [
      {
        "name": "service",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(http_requests_total, service)",
        "multi": true,
        "includeAll": true,
        "allValue": ".*",
        "refresh": 2
      },
      {
        "name": "interval",
        "type": "interval",
        "auto": true,
        "auto_min": "10s",
        "options": [
          {"value": "1m", "text": "1 minute"},
          {"value": "5m", "text": "5 minutes"},
          {"value": "15m", "text": "15 minutes"}
        ]
      }
    ]
  }
}
```

## Panel Types

### Choosing the Right Panel

| Panel Type | Use Case | Example |
|------------|----------|---------|
| **Time series** | Metrics over time | Request rate, latency trends |
| **Stat** | Single current value | Current error rate, RPS |
| **Gauge** | Value vs. thresholds | CPU usage, SLO budget |
| **Bar gauge** | Compare values | Top 5 endpoints by latency |
| **Table** | Detailed data | Pod status, error details |
| **Heatmap** | Distribution over time | Latency distribution |
| **Logs** | Log entries | Loki integration |
| **Traces** | Distributed traces | Tempo/Jaeger integration |

### Time Series Best Practices

```
TIME SERIES CONFIGURATION
─────────────────────────────────────────────────────────────────

LEGEND
├── Format: {{service}} - {{method}}
├── Placement: Bottom or Right
└── Hide if too many series (use tooltip)

AXES
├── Left Y: Main metric (e.g., RPS)
├── Right Y: Secondary (e.g., error %)
└── Label units explicitly

THRESHOLDS
├── Warning: Yellow line
├── Critical: Red line
└── Fill below threshold for visibility

SERIES OVERRIDES
├── Error series: Red
├── Success series: Green
└── Specific series styling
```

### Stat Panel with Thresholds

```json
{
  "type": "stat",
  "title": "Error Rate",
  "targets": [
    {
      "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
      "legendFormat": ""
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 1},
          {"color": "red", "value": 5}
        ]
      },
      "mappings": [],
      "color": {"mode": "thresholds"}
    }
  },
  "options": {
    "colorMode": "background",
    "graphMode": "none",
    "textMode": "value"
  }
}
```

## Grafana Alerting

### Alert Rules

```yaml
# Grafana alerting (unified alerting)
apiVersion: 1
groups:
  - name: service-alerts
    folder: Production
    interval: 1m
    rules:
      - uid: high-error-rate
        title: High Error Rate
        condition: C
        data:
          # Query A: Error requests
          - refId: A
            datasourceUid: prometheus
            model:
              expr: sum(rate(http_requests_total{status=~"5.."}[5m]))

          # Query B: Total requests
          - refId: B
            datasourceUid: prometheus
            model:
              expr: sum(rate(http_requests_total[5m]))

          # Expression C: Error rate
          - refId: C
            datasourceUid: __expr__
            model:
              type: math
              expression: $A / $B * 100
              conditions:
                - evaluator:
                    type: gt
                    params: [5]  # > 5%

        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate is {{ $values.C }}%"
```

### Contact Points

```yaml
# Contact points configuration
apiVersion: 1
contactPoints:
  - name: slack-alerts
    receivers:
      - uid: slack-1
        type: slack
        settings:
          url: https://hooks.slack.com/services/...
          recipient: "#alerts"
          title: "{{ .CommonLabels.alertname }}"
          text: "{{ .CommonAnnotations.summary }}"

  - name: pagerduty
    receivers:
      - uid: pd-1
        type: pagerduty
        settings:
          integrationKey: "<key>"
          severity: "{{ .CommonLabels.severity }}"
```

## Explore Mode

### Ad-hoc Investigation

```
EXPLORE MODE
─────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│  [Prometheus ▼]    [Loki ▼]    [Tempo ▼]                       │
├────────────────────────────────────────────────────────────────┤
│  QUERY: rate(http_requests_total{service="api"}[5m])           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  [Run Query]  [Add Query]  [Split]                       │ │
│  └──────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RESULT:                                                        │
│  ════════════════════════════════════════════════              │
│                                          ^                      │
│                                         /                       │
│  ──────────────────────────────────────/──────────             │
│                                                                 │
│  [Split] Split panes for comparison                            │
│  [Logs]  Link to Loki for this time range                      │
│  [Traces] Link to Tempo for this trace ID                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

Use Cases:
• Incident investigation
• Metric exploration
• Query building before dashboard
• Correlating metrics, logs, traces
```

### Correlating Signals

```
SIGNAL CORRELATION
─────────────────────────────────────────────────────────────────

1. Start with metric anomaly
   rate(http_requests_total{status="500"}[5m]) > 0

2. Click "Explore" on spike timestamp

3. Split view → Add Loki
   {service="api"} |= "error" | json

4. Find error with trace_id

5. Split view → Add Tempo
   Paste trace_id → See full trace

6. Identify root cause in upstream service
```

## Dashboard as Code

### Provisioning

```yaml
# provisioning/dashboards/dashboards.yaml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: 'Production'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
```

### Grafonnet (Jsonnet)

```jsonnet
// dashboard.jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local prometheus = grafana.prometheus;
local graphPanel = grafana.graphPanel;

dashboard.new(
  'Service Dashboard',
  tags=['production', 'service'],
  time_from='now-1h',
)
.addTemplate(
  grafana.template.datasource(
    'datasource',
    'prometheus',
    'Prometheus',
  )
)
.addTemplate(
  grafana.template.query(
    'service',
    'label_values(http_requests_total, service)',
    datasource='$datasource',
  )
)
.addRow(
  row.new(
    title='Golden Signals',
  )
  .addPanel(
    graphPanel.new(
      'Request Rate',
      datasource='$datasource',
    )
    .addTarget(
      prometheus.target(
        'sum(rate(http_requests_total{service="$service"}[5m]))',
        legendFormat='RPS',
      )
    )
  )
  .addPanel(
    graphPanel.new(
      'Error Rate',
      datasource='$datasource',
    )
    .addTarget(
      prometheus.target(
        'sum(rate(http_requests_total{service="$service",status=~"5.."}[5m])) / sum(rate(http_requests_total{service="$service"}[5m]))',
        legendFormat='Error %',
      )
    )
  )
)
```

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Too many panels | Slow, overwhelming | Focus on golden signals |
| No variables | Duplicate dashboards | Use template variables |
| Hardcoded time ranges | Stale data | Use relative ranges |
| Missing units | Unclear data | Always set units |
| No thresholds | Can't spot issues | Add visual thresholds |
| Direct queries everywhere | Slow dashboards | Use recording rules |

## Quiz

Test your understanding:

<details>
<summary>1. Why are dashboard variables important?</summary>

**Answer**: Variables provide:
- **Reusability**: One dashboard for many services
- **Exploration**: Easy switching between environments
- **Maintenance**: Fewer dashboards to maintain
- **Consistency**: Same layout, different data

Without variables, teams create duplicate dashboards for each service, leading to maintenance nightmares.
</details>

<details>
<summary>2. What are the Four Golden Signals and why use them?</summary>

**Answer**: The Four Golden Signals are:
1. **Latency**: How long requests take
2. **Traffic**: Request volume
3. **Errors**: Failure rate
4. **Saturation**: Resource utilization

They provide a complete picture of service health. If all four are healthy, the service is likely healthy. They're recommended by Google's SRE book as the minimum monitoring.
</details>

<details>
<summary>3. When should you use Explore vs. Dashboards?</summary>

**Answer**:
- **Dashboards**: Known questions, ongoing monitoring, team visibility
- **Explore**: Ad-hoc investigation, incident response, query building

Explore is for investigation, dashboards are for monitoring. Build dashboards from queries developed in Explore.
</details>

<details>
<summary>4. How does Grafana help with signal correlation?</summary>

**Answer**: Grafana enables correlation through:
- **Linked data sources**: Jump from metric to logs to traces
- **Common labels**: TraceID, service name across signals
- **Split view**: Compare signals side-by-side
- **Time synchronization**: Same time range across panels

This enables rapid root cause analysis: metric spike → related logs → distributed trace.
</details>

<details>
<summary>5. A dashboard has 50 panels and takes 30 seconds to load. What's likely wrong and how would you fix it?</summary>

**Answer**: Common causes and fixes:

**1. Too many queries executing**:
- Each panel fires separate query
- Fix: Use recording rules to pre-compute, reduce panels

**2. Long time ranges with high resolution**:
- Querying months of data at 1-second granularity
- Fix: Use `$__interval` variable, implement step adjustment

**3. High cardinality queries**:
- `topk(100, ...)` or unbounded label matches
- Fix: Add filters, reduce cardinality, use recording rules

**4. No caching**:
- Same queries repeatedly hit Prometheus
- Fix: Enable query caching, set appropriate cache TTL

**5. Slow data source**:
- Prometheus itself is overwhelmed
- Fix: Add capacity, shard Prometheus, use Thanos/Mimir

**Diagnostic approach**:
1. Open browser DevTools → Network tab
2. Identify slowest queries
3. Run those queries directly in Prometheus to isolate
</details>

<details>
<summary>6. You need one dashboard to work for 100 microservices. How would you design the variable structure?</summary>

**Answer**: Multi-level variable cascade:

```
Variable: namespace
  Query: label_values(up, namespace)

Variable: service
  Query: label_values(up{namespace="$namespace"}, service)
  Depends on: namespace

Variable: instance
  Query: label_values(up{namespace="$namespace", service="$service"}, instance)
  Depends on: namespace, service

Variable: interval
  Type: interval
  Auto: true
  Auto_min: 10s
```

**Key techniques**:
- **Cascading dependencies**: Each variable filters the next
- **Include All option**: `.*` regex for multi-select
- **Refresh on load**: Keep data current
- **Default values**: Pre-select production namespace

**In panels**: Use `{namespace="$namespace", service=~"$service"}` with regex match for multi-select support.
</details>

<details>
<summary>7. What's the difference between Stat, Gauge, and Bar Gauge panels? When would you use each?</summary>

**Answer**:

| Panel | Best For | Example |
|-------|----------|---------|
| **Stat** | Current value, large display | Error rate: 0.5%, uptime: 99.95% |
| **Gauge** | Value vs. thresholds, radial | CPU: 75% of 100%, memory: 8/16 GB |
| **Bar Gauge** | Comparing multiple values | Top 5 endpoints by latency |

**Decision tree**:
- Single value, big number display? → **Stat**
- Single value, progress toward limit? → **Gauge**
- Multiple values, comparing? → **Bar Gauge**
- Time series needed? → **Time series** (not these)

**Threshold configuration**: All three support color thresholds (green/yellow/red) which should map to SLO states, not arbitrary percentages.
</details>

<details>
<summary>8. How would you set up Grafana to correlate a metric spike to logs and then traces?</summary>

**Answer**: Configure data source links:

**1. Prometheus → Loki (metrics to logs)**:
```yaml
datasources:
  - name: Prometheus
    jsonData:
      derivedFields:
        - datasourceUid: loki
          matcherRegex: service="([^"]+)"
          name: ServiceLogs
          url: '/explore?left={"queries":[{"expr":"{service=\"${__value.raw}\"}"}]}'
```

**2. Prometheus → Tempo (via exemplars)**:
```yaml
    jsonData:
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: tempo
```

**3. Loki → Tempo (logs to traces)**:
```yaml
datasources:
  - name: Loki
    jsonData:
      derivedFields:
        - name: TraceID
          matcherRegex: 'trace_id=(\w+)'
          datasourceUid: tempo
          url: '${__value.raw}'
```

**Workflow**:
1. See latency spike in dashboard (Prometheus)
2. Click exemplar → opens trace in Tempo
3. See slow span, click service → opens Loki with filtered logs
4. Find error message with stack trace
</details>

## Hands-On Exercise: Build a Service Dashboard

Create a complete service dashboard:

### Setup

```bash
# Deploy Grafana using Helm
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install grafana grafana/grafana \
  --namespace monitoring \
  --set adminPassword=admin \
  --set persistence.enabled=true \
  --set persistence.size=10Gi
```

### Step 1: Access Grafana

```bash
# Get admin password
kubectl get secret -n monitoring grafana -o jsonpath="{.data.admin-password}" | base64 -d

# Port forward
kubectl port-forward -n monitoring svc/grafana 3000:80

# Login at http://localhost:3000 (admin / <password>)
```

### Step 2: Add Prometheus Data Source

1. Go to Configuration → Data Sources
2. Add Prometheus
3. URL: `http://prometheus-server:80`
4. Save & Test

### Step 3: Create Dashboard with Variables

```json
{
  "title": "Service Dashboard",
  "templating": {
    "list": [
      {
        "name": "service",
        "type": "query",
        "datasource": "Prometheus",
        "query": "label_values(up, job)",
        "multi": false,
        "includeAll": false
      },
      {
        "name": "interval",
        "type": "interval",
        "auto": true,
        "auto_min": "10s",
        "options": [
          {"value": "1m", "text": "1m"},
          {"value": "5m", "text": "5m"},
          {"value": "15m", "text": "15m"}
        ]
      }
    ]
  }
}
```

### Step 4: Add Golden Signal Panels

**Request Rate (Time Series)**:
```promql
sum(rate(http_requests_total{job="$service"}[$interval]))
```

**Error Rate (Stat Panel)**:
```promql
sum(rate(http_requests_total{job="$service",status=~"5.."}[$interval]))
/
sum(rate(http_requests_total{job="$service"}[$interval]))
* 100
```

**Latency P99 (Time Series)**:
```promql
histogram_quantile(0.99,
  sum by (le)(rate(http_request_duration_seconds_bucket{job="$service"}[$interval]))
)
```

**CPU Usage (Gauge)**:
```promql
avg(rate(process_cpu_seconds_total{job="$service"}[$interval])) * 100
```

### Step 5: Configure Thresholds

For Error Rate Stat:
- Green: < 1%
- Yellow: 1-5%
- Red: > 5%

For CPU Gauge:
- Green: < 70%
- Yellow: 70-85%
- Red: > 85%

### Success Criteria

You've completed this exercise when you can:
- [ ] Create dashboard with variables
- [ ] Switch services using dropdown
- [ ] See all four golden signals
- [ ] Thresholds change panel colors
- [ ] Export dashboard as JSON

## Key Takeaways

Before moving on, ensure you understand:

- [ ] **Four Golden Signals**: Every service dashboard should show Latency, Traffic, Errors, and Saturation
- [ ] **Dashboard hierarchy**: Overview (all services) → Service (one service) → Component (instances/pods)
- [ ] **Variables are essential**: Query, interval, and custom variables enable reusable dashboards
- [ ] **Panel selection**: Stat (single value), Gauge (vs. threshold), Bar Gauge (comparison), Time Series (trends)
- [ ] **Thresholds must be meaningful**: Map to SLO states (green = healthy, yellow = warning, red = breaching)
- [ ] **Explore for investigation**: Ad-hoc queries, split view, incident response; dashboards for monitoring
- [ ] **Signal correlation**: Configure exemplars (Prometheus → Tempo), derived fields (Loki → Tempo)
- [ ] **Dashboard as code**: Use Grafonnet/JSON provisioning for version control and consistency
- [ ] **Alert fatigue is deadly**: Fewer, high-signal alerts beat many noisy ones
- [ ] **Units and legends**: Always label axes, set units, format legends for clarity

## Further Reading

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/) — Official docs
- [Grafonnet](https://grafana.github.io/grafonnet-lib/) — Dashboard as code
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/) — Official guide
- [LGTM Stack](https://grafana.com/oss/) — Complete observability

## Summary

Grafana transforms metrics into insights. The Four Golden Signals provide a framework for service health. Variables create reusable, maintainable dashboards. Explore mode enables rapid investigation during incidents. Dashboard as code brings version control to visualization. Together with Prometheus, Loki, and Tempo, Grafana forms a complete observability platform.

---

## Next Module

Continue to [Module 1.4: Logging with Loki](../module-1.4-loki/) to learn about log aggregation and analysis.

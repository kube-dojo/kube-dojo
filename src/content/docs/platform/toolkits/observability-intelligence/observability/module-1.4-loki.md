---
title: "Module 1.4: Loki"
slug: platform/toolkits/observability-intelligence/observability/module-1.4-loki
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 40-45 min

## Prerequisites

Before starting this module:
- [Module 1.1: Prometheus](../module-1.1-prometheus/) — Labels and querying concepts
- [Module 1.3: Grafana](../module-1.3-grafana/) — Visualization and exploration
- Basic understanding of log aggregation
- kubectl log experience

---

The infrastructure team at a fast-growing SaaS company stared at their AWS bill in disbelief. Elasticsearch: $127,000 last month. For logs. Not revenue-generating features, not customer-facing services—just storing text that nobody read 99% of the time.

"We need these logs for compliance," the security team argued. "Seven years retention, fully searchable."

The math was brutal: 2TB of logs per day, indexed across 12 fields, replicated 3x, stored for 2,555 days. The five-year projection showed $8.4 million in Elasticsearch infrastructure costs alone.

Then the platform architect discovered Loki. Same 2TB/day, but stored in S3 at $0.023/GB instead of hot Elasticsearch nodes at $0.30/GB. Labels indexed, content compressed. The seven-year compliance requirement? Achievable for $340,000—a 96% cost reduction.

Six months after migration, the CFO asked the infrastructure team to present at the board meeting. "This is the first time anyone's ever invited infrastructure to talk about cost savings," the architect joked. The board approved their next three proposals on the spot.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Loki for cost-effective log aggregation with label-based indexing and object storage backends**
- **Implement LogQL queries for log exploration, metric extraction, and pattern-based alerting**
- **Configure Promtail and Grafana Alloy agents for Kubernetes log collection with label enrichment**
- **Optimize Loki's storage configuration and retention policies for high-volume log environments**


## Why This Module Matters

Logs tell you what happened. Metrics tell you something is wrong; logs tell you why. But traditional logging solutions (ELK, Splunk) are expensive—indexing every field in every log line costs storage and compute.

Loki takes a different approach: index only labels, store logs compressed. It's "Prometheus for logs"—same label-based discovery, fraction of the cost. At scale, this matters enormously.

## Did You Know?

- **Loki was inspired by frustration**—Grafana engineers were tired of running expensive Elasticsearch clusters just to find a needle in a haystack of logs
- **Loki can be 10-100x cheaper than Elasticsearch** for the same volume—because it doesn't index log content, only labels
- **The name comes from Norse mythology**—Loki is the trickster god, fitting for a system that "tricks" you into thinking you have full-text search
- **Loki's query language (LogQL) borrows heavily from PromQL**—if you know Prometheus, you're 80% there

## Loki Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      LOKI ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LOG SOURCES                                                     │
│  ┌──────────────┐                                               │
│  │   App Pods   │                                               │
│  │   stdout/err │─────┐                                         │
│  └──────────────┘     │                                         │
│  ┌──────────────┐     │     ┌─────────────────────────────────┐│
│  │  System Logs │     ├────▶│           PROMTAIL              ││
│  │  /var/log/*  │     │     │  ┌───────────────────────────┐  ││
│  └──────────────┘     │     │  │ • Discover log files      │  ││
│  ┌──────────────┐     │     │  │ • Extract labels          │  ││
│  │   K8s Events │─────┘     │  │ • Push to Loki            │  ││
│  └──────────────┘           │  └───────────────────────────┘  ││
│                             └──────────────┬──────────────────┘│
│                                            │                    │
│                                            ▼                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    LOKI CLUSTER                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ Distributor│  │   Ingester │  │    Querier         │  │  │
│  │  │            │  │            │  │                    │  │  │
│  │  │ Receives   │─▶│ Builds     │  │ Queries chunks     │  │  │
│  │  │ logs       │  │ chunks     │  │ from ingesters     │  │  │
│  │  │            │  │ in memory  │  │ and object store   │  │  │
│  │  └────────────┘  └─────┬──────┘  └────────────────────┘  │  │
│  │                        │                                  │  │
│  │                        ▼                                  │  │
│  │  ┌──────────────────────────────────────────────────────┐│  │
│  │  │              OBJECT STORAGE (S3/GCS/Minio)           ││  │
│  │  │  ┌─────────────────┐  ┌─────────────────────────┐   ││  │
│  │  │  │   Chunks        │  │   Index                 │   ││  │
│  │  │  │   (compressed   │  │   (labels → chunk refs) │   ││  │
│  │  │  │    log lines)   │  │                         │   ││  │
│  │  │  └─────────────────┘  └─────────────────────────┘   ││  │
│  │  └──────────────────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **Promtail** | Agent that discovers, labels, and pushes logs |
| **Distributor** | Receives log streams, validates, routes to ingesters |
| **Ingester** | Builds compressed chunks, holds recent data |
| **Querier** | Executes LogQL queries across ingesters and storage |
| **Compactor** | Merges and deduplicates index files |

### Why Labels Matter

```
LOKI'S KEY INSIGHT: Only index labels, not log content

Traditional (Elasticsearch):                 Loki:
─────────────────────────────────────────────────────────────────

Every word indexed:                          Only labels indexed:
{                                            {
  "timestamp": "2024-01-15T10:30:00Z",        namespace="production",
  "message": "User login failed",  ◀─ idx    app="api-gateway",
  "user": "john@example.com",      ◀─ idx    pod="api-gateway-xyz",
  "error": "invalid password",     ◀─ idx    container="api"
  "ip": "192.168.1.100",           ◀─ idx  }
  "pod": "api-gateway-xyz"         ◀─ idx
}                                            Log line: stored compressed

Storage: 10GB                                Storage: 1GB
Index: 8GB                                   Index: 100MB
```

## LogQL: Query Language

### Basic Syntax

```
{label="value"} |= "search term" | json | line_format "{{.field}}"
  └── stream    └── filter      └── parser └── formatter
      selector
```

### Stream Selectors

```logql
# Exact match
{namespace="production"}

# Regex match
{namespace=~"prod.*"}

# Not equal
{namespace!="kube-system"}

# Multiple labels (AND)
{namespace="production", app="api-gateway"}

# Regex OR
{namespace=~"production|staging"}
```

### Line Filters

```logql
# Contains (case-sensitive)
{app="api"} |= "error"

# Does not contain
{app="api"} != "debug"

# Regex match
{app="api"} |~ "error|warn|fatal"

# Regex not match
{app="api"} !~ "health|ready"
```

### Parsers

```logql
# JSON parser - extracts all JSON fields as labels
{app="api"} | json

# JSON with specific fields
{app="api"} | json status_code="response.status"

# Logfmt parser (key=value format)
{app="api"} | logfmt

# Pattern parser (custom format)
{app="nginx"} | pattern `<ip> - - [<timestamp>] "<method> <path> <_>" <status> <size>`

# Regex parser
{app="api"} | regexp `(?P<level>\w+) (?P<msg>.*)`
```

### Label Filters (after parsing)

```logql
# Filter by extracted label
{app="api"} | json | status_code >= 500

# String comparison
{app="api"} | json | level = "error"

# Duration comparison
{app="api"} | logfmt | duration > 1s

# Size comparison
{app="api"} | json | bytes > 1MB
```

### Aggregations (Metric Queries)

```logql
# Count logs per minute
count_over_time({app="api"} |= "error" [1m])

# Rate of logs per second
rate({app="api"} |= "error" [5m])

# Bytes processed
bytes_rate({app="api"} [5m])

# Sum by label
sum by (status_code) (
  count_over_time({app="api"} | json [5m])
)

# Top 5 error sources
topk(5,
  sum by (pod) (
    count_over_time({app="api"} |= "error" [1h])
  )
)
```

### Practical LogQL Examples

```logql
# Find all errors in production in the last hour
{namespace="production"} |= "error" [1h]

# Parse JSON logs and filter by status
{app="api-gateway"}
  | json
  | status_code >= 400
  | line_format "{{.method}} {{.path}} - {{.status_code}}"

# Calculate error rate per service
sum by (app) (
  rate({namespace="production"} |= "error" [5m])
)

# Find slow requests (>1s) with context
{app="api"}
  | json
  | duration > 1s
  | line_format "{{.path}} took {{.duration}} - user: {{.user_id}}"

# Logs around a specific time (context)
{app="api"}
  | json
  | ts >= "2024-01-15T10:30:00Z"
  | ts <= "2024-01-15T10:35:00Z"
```

## Promtail Configuration

### Basic Promtail Setup

```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml  # Track file read positions

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod

    relabel_configs:
      # Keep only pods with logging enabled
      - source_labels: [__meta_kubernetes_pod_annotation_promtail_io_scrape]
        action: keep
        regex: true

      # Extract namespace label
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace

      # Extract pod name
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod

      # Extract container name
      - source_labels: [__meta_kubernetes_pod_container_name]
        target_label: container

      # Extract app label from pod
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app
```

### Pipeline Stages

```yaml
scrape_configs:
  - job_name: app-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: app
          __path__: /var/log/app/*.log

    pipeline_stages:
      # Parse JSON logs
      - json:
          expressions:
            level: level
            msg: message
            user_id: user.id

      # Add labels from parsed fields
      - labels:
          level:
          user_id:

      # Drop debug logs in production
      - match:
          selector: '{job="app"}'
          stages:
            - drop:
                expression: '.*level=debug.*'

      # Restructure log line
      - output:
          source: msg

      # Add timestamp from log
      - timestamp:
          source: ts
          format: RFC3339
```

### Multiline Logs (Stack Traces)

```yaml
scrape_configs:
  - job_name: java-app
    static_configs:
      - targets:
          - localhost
        labels:
          job: java
          __path__: /var/log/java/*.log

    pipeline_stages:
      # Combine multiline stack traces
      - multiline:
          firstline: '^\d{4}-\d{2}-\d{2}'  # Starts with date
          max_wait_time: 3s
          max_lines: 128

      # Then parse as usual
      - json:
          expressions:
            level: level
            exception: exception.class
```

## Loki Deployment Patterns

### Monolithic (Simple)

```yaml
# Good for: < 100GB/day, single team
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
        - name: loki
          image: grafana/loki:2.9.0
          args:
            - -config.file=/etc/loki/loki.yaml
          ports:
            - containerPort: 3100
          volumeMounts:
            - name: config
              mountPath: /etc/loki
            - name: storage
              mountPath: /loki
      volumes:
        - name: config
          configMap:
            name: loki-config
        - name: storage
          persistentVolumeClaim:
            claimName: loki-storage
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: monitoring
data:
  loki.yaml: |
    auth_enabled: false

    server:
      http_listen_port: 3100

    common:
      path_prefix: /loki
      storage:
        filesystem:
          chunks_directory: /loki/chunks
          rules_directory: /loki/rules
      replication_factor: 1
      ring:
        kvstore:
          store: inmemory

    schema_config:
      configs:
        - from: 2020-10-24
          store: boltdb-shipper
          object_store: filesystem
          schema: v11
          index:
            prefix: index_
            period: 24h

    ruler:
      alertmanager_url: http://alertmanager:9093

    limits_config:
      retention_period: 168h  # 7 days
```

### Microservices Mode (Scale)

```yaml
# Good for: > 100GB/day, multi-tenant
# Deploy each component separately

# Distributor (2+ replicas)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki-distributor
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: distributor
          image: grafana/loki:2.9.0
          args:
            - -target=distributor
            - -config.file=/etc/loki/loki.yaml

# Ingester (3+ replicas, StatefulSet)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: loki-ingester
spec:
  replicas: 3
  serviceName: loki-ingester
  template:
    spec:
      containers:
        - name: ingester
          image: grafana/loki:2.9.0
          args:
            - -target=ingester
            - -config.file=/etc/loki/loki.yaml
          volumeMounts:
            - name: wal
              mountPath: /loki/wal
  volumeClaimTemplates:
    - metadata:
        name: wal
      spec:
        accessModes: [ReadWriteOnce]
        resources:
          requests:
            storage: 10Gi

# Querier (2+ replicas)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki-querier
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: querier
          image: grafana/loki:2.9.0
          args:
            - -target=querier
            - -config.file=/etc/loki/loki.yaml
```

### Object Storage Configuration (Production)

```yaml
# loki-config.yaml for S3-compatible storage
auth_enabled: true  # Enable multi-tenancy

storage_config:
  aws:
    s3: s3://access-key:secret-key@region/bucket-name
    s3forcepathstyle: true

  boltdb_shipper:
    active_index_directory: /loki/index
    shared_store: s3
    cache_location: /loki/cache

# Or for GCS
storage_config:
  gcs:
    bucket_name: my-loki-bucket

  boltdb_shipper:
    active_index_directory: /loki/index
    shared_store: gcs

# Or for Azure
storage_config:
  azure:
    account_name: mystorageaccount
    account_key: base64-encoded-key
    container_name: loki-logs
```

## Multi-Tenancy

### Enabling Multi-Tenancy

```yaml
# loki-config.yaml
auth_enabled: true  # This is all it takes

limits_config:
  # Per-tenant limits
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20
  max_streams_per_user: 10000
  max_global_streams_per_user: 0  # 0 = unlimited

# Override for specific tenants
overrides:
  tenant-a:
    ingestion_rate_mb: 50
    retention_period: 720h  # 30 days

  tenant-b:
    ingestion_rate_mb: 5
    retention_period: 168h  # 7 days
```

### Sending Logs with Tenant ID

```yaml
# Promtail config - send tenant header
clients:
  - url: http://loki:3100/loki/api/v1/push
    tenant_id: team-a

# Or via HTTP header
# X-Scope-OrgID: team-a
```

### Querying with Tenant ID

```bash
# Grafana: Configure data source with HTTP header
# X-Scope-OrgID: team-a

# Or query directly:
curl -H "X-Scope-OrgID: team-a" \
  "http://loki:3100/loki/api/v1/query?query={app=\"api\"}"
```

## Alerting with Loki

### Recording Rules

```yaml
# loki-rules.yaml
groups:
  - name: recording-rules
    interval: 1m
    rules:
      # Create a metric from logs
      - record: http_requests:rate5m
        expr: |
          sum by (app, status_code) (
            rate({namespace="production"} | json [5m])
          )

      # Error rate by service
      - record: error_rate:1m
        expr: |
          sum by (app) (
            rate({namespace="production"} |= "error" [1m])
          )
          /
          sum by (app) (
            rate({namespace="production"} [1m])
          )
```

### Alerting Rules

```yaml
# loki-rules.yaml
groups:
  - name: alerting-rules
    rules:
      - alert: HighErrorRate
        expr: |
          sum by (app) (
            rate({namespace="production"} |= "error" [5m])
          ) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate for {{ $labels.app }}"
          description: "{{ $labels.app }} has {{ $value }} errors/sec"

      - alert: NoLogsReceived
        expr: |
          sum(rate({namespace="production"}[5m])) == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "No logs from production"
          description: "Haven't received logs from production in 10 minutes"

      - alert: HighLatencyRequests
        expr: |
          count_over_time(
            {app="api"} | json | duration > 5s [5m]
          ) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Many slow requests in API"
```

## Grafana Integration

### Adding Loki Data Source

```yaml
# grafana-datasources.yaml
apiVersion: 1
datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
      httpHeaderName1: X-Scope-OrgID
    secureJsonData:
      httpHeaderValue1: my-tenant
```

### Correlating Metrics and Logs

```
In Grafana:
1. Metrics panel: Prometheus query showing error spike
2. Click data point → "Explore" → switch to Loki
3. Automatic time range correlation
4. See exact logs during incident

Or use "Derived Fields":
- Extract trace_id from logs
- Link to Tempo/Jaeger for traces
- Full observability correlation
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Too many labels | Cardinality explosion, slow queries | Use 5-10 static labels, parse dynamic values at query time |
| Storing structured data as labels | Labels should be low-cardinality | Keep user_id, request_id in log content, not labels |
| No retention policy | Disk fills up, costs explode | Set retention_period, use lifecycle policies on S3 |
| Querying all namespaces | Slow, expensive queries | Always filter by namespace first |
| Not using time ranges | Scans entire history | Always include time range `[1h]` or use Grafana time picker |
| Ignoring line limits | Returning millions of lines | Use `| limit 100` or topk/bottomk aggregations |

## War Story: The Stream Explosion That Killed Production

A startup migrated from Elasticsearch to Loki for cost savings. Initial results were spectacular: 80% cost reduction, faster queries, simpler operations. The VP of Engineering sent a company-wide email celebrating the win.

**Week 3, Tuesday 2:14 PM**: Developers noticed log queries timing out.

**Week 3, Tuesday 2:45 PM**: Loki ingesters started OOMing. Kubernetes restarted them in a loop.

**Week 3, Tuesday 3:30 PM**: Complete logging blackout. No logs ingested or queryable.

**Week 3, Tuesday 4:00 PM**: Root cause identified. A well-intentioned developer had added a "helpful" label to make debugging easier:

```yaml
# The problematic Promtail config
pipeline_stages:
  - json:
      expressions:
        request_id: request_id  # ← This created a new stream per request
  - labels:
      request_id:  # ← Labels must be low-cardinality!
```

**The Math That Broke Everything**:
```
Request volume:       1,000,000 requests/day
Labels before:        ~500 unique combinations (namespace × service × pod)
Labels after:         500 × 1,000,000 = 500,000,000 stream combinations

Ingester memory:
  Before: 500 streams × 64KB each = 32MB
  After:  500M streams × 64KB each = 32TB (impossible)
```

**Financial Impact**:
```
─────────────────────────────────────────────────────────────────
Incident duration:           4 hours
Logs lost:                   ~2.8 million events
Compliance gap:              SOC 2 finding (minor)
Engineering hours:           8 engineers × 6 hours = $9,600
Cluster rebuild:             $2,400 (new nodes, data migration)
Audit remediation:           $15,000 (documentation, controls)
─────────────────────────────────────────────────────────────────
Total Impact:                ~$27,000
```

**The Fix**: Move high-cardinality values to log content, query with parsers:

```yaml
# Correct approach
pipeline_stages:
  - json:
      expressions:
        request_id: request_id
  # Don't add request_id as label!
  - output:
      source: message  # Keep request_id in log content
```

Query at runtime:
```logql
{app="api"} | json | request_id="abc123-def456"
```

**The Lesson**: Labels are for grouping, not for unique identifiers. If a value has more than ~100 unique values, it should be parsed at query time, not indexed as a label.

## Quiz

### Question 1
What makes Loki cheaper than Elasticsearch for the same log volume?

<details>
<summary>Show Answer</summary>

Loki only indexes labels, not log content. Elasticsearch indexes every word in every log line. For 1TB of logs, Elasticsearch might need 800GB of index storage, while Loki needs only a few GB for label indices. The logs themselves are stored compressed without content indexing.

This trade-off means Loki queries are "grep at scale" - they must scan log content at query time. But for most use cases, filtering by labels first makes this fast enough.
</details>

### Question 2
Given this LogQL query, explain what it returns:
```logql
topk(3,
  sum by (pod) (
    count_over_time({namespace="prod", app="api"} |= "error" | json | status_code >= 500 [1h])
  )
)
```

<details>
<summary>Show Answer</summary>

This query returns the top 3 pods with the most 5xx errors in the last hour.

Breaking it down:
1. `{namespace="prod", app="api"}` - Select logs from API pods in production
2. `|= "error"` - Filter lines containing "error"
3. `| json` - Parse as JSON
4. `| status_code >= 500` - Keep only 5xx status codes
5. `count_over_time(...[1h])` - Count matching lines in 1-hour windows
6. `sum by (pod)` - Sum counts per pod
7. `topk(3, ...)` - Return top 3 results

This is useful for finding which pods are generating the most errors during an incident.
</details>

### Question 3
Why would you use a StatefulSet for Loki ingesters instead of a Deployment?

<details>
<summary>Show Answer</summary>

Ingesters need stable network identities and persistent storage for the Write-Ahead Log (WAL).

1. **Stable identity**: The hash ring uses pod names to distribute log streams. If pod names change on restart (as with Deployments), streams could be assigned to wrong ingesters.

2. **WAL persistence**: Ingesters buffer logs in memory and write to a WAL before flushing to object storage. If a pod crashes, the WAL allows recovery of unflushed data. This requires persistent volumes that survive pod restarts.

3. **Ordered deployment**: StatefulSets deploy pods one at a time, allowing the cluster to rebalance between each. Deployments might start all replicas simultaneously, causing thundering herd issues.
</details>

### Question 4
How would you configure Promtail to combine Java stack traces into a single log entry?

<details>
<summary>Show Answer</summary>

Use the multiline pipeline stage with a regex that matches the start of a new log entry:

```yaml
pipeline_stages:
  - multiline:
      firstline: '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
      max_wait_time: 3s
      max_lines: 128
```

This tells Promtail:
- A new log entry starts with a timestamp (ISO format in this case)
- Wait up to 3 seconds for more lines before flushing
- Combine up to 128 lines into one entry

Without this, each line of a stack trace becomes a separate log entry, making them impossible to search together.
</details>

### Question 5
Calculate: You have 500GB of logs per day. Elasticsearch costs $0.30/GB/month for hot storage. Loki with S3 costs $0.023/GB/month. What's the monthly and annual savings?

<details>
<summary>Show Answer</summary>

**Monthly calculation**:
```
Daily volume:    500 GB
Monthly volume:  500 × 30 = 15,000 GB

Elasticsearch:   15,000 × $0.30 = $4,500/month
Loki + S3:       15,000 × $0.023 = $345/month

Monthly savings: $4,155 (92% reduction)
```

**Annual calculation**:
```
Elasticsearch:   $4,500 × 12 = $54,000/year
Loki + S3:       $345 × 12 = $4,140/year

Annual savings:  $49,860
```

**Caveats**:
- Elasticsearch may need 3x replication (multiply by 3)
- Loki needs querier/ingester compute (add ~$500-1000/month)
- S3 has request costs (add ~$50-100/month for GET/PUT)
- True savings: ~85-90% after all factors

**Real-world**: Companies typically see 80-95% cost reduction migrating from ELK to Loki.
</details>

### Question 6
Your LogQL query `{app="api"} |= "error"` returns 10 million results and times out. How would you make it efficient?

<details>
<summary>Show Answer</summary>

**Step 1: Add time constraints** (most important):
```logql
{app="api"} |= "error" [1h]  # Query only last hour
```

**Step 2: Add more label filters**:
```logql
{app="api", namespace="production", level="error"} [1h]
```

**Step 3: Use aggregation instead of raw logs**:
```logql
# Count errors per 5 minutes
sum by (service) (
  count_over_time({app="api"} |= "error" [5m])
)
```

**Step 4: Limit output**:
```logql
{app="api"} |= "error" | limit 1000
```

**Step 5: Parse and filter**:
```logql
{app="api"}
  | json
  | level="error"
  | status_code >= 500
  | limit 100
```

**Root cause**: Loki scans all chunks matching labels. More specific labels + shorter time range = fewer chunks scanned.
</details>

### Question 7
What's the difference between `count_over_time()`, `rate()`, and `bytes_rate()` in LogQL?

<details>
<summary>Show Answer</summary>

| Function | Returns | Use Case |
|----------|---------|----------|
| `count_over_time({...}[5m])` | Number of log lines | "How many errors in 5 minutes?" |
| `rate({...}[5m])` | Log lines per second | "What's the error rate per second?" |
| `bytes_rate({...}[5m])` | Bytes per second | "How much log data am I ingesting?" |

**Relationship**:
```logql
rate() = count_over_time() / range_in_seconds

# These are equivalent:
rate({app="api"}[5m])
# ≈ count_over_time({app="api"}[5m]) / 300
```

**Practical examples**:
```logql
# Alert: More than 100 errors per minute
rate({app="api"} |= "error" [1m]) > 100

# Dashboard: Errors per 5-minute window
count_over_time({app="api"} |= "error" [5m])

# Capacity planning: Log ingestion rate
sum(bytes_rate({namespace="production"}[5m]))
```
</details>

### Question 8
How would you set up Loki alerting to page when a specific error message appears more than 10 times in 5 minutes?

<details>
<summary>Show Answer</summary>

**Loki ruler configuration**:
```yaml
# /etc/loki/rules/alerts.yaml
groups:
  - name: critical-errors
    interval: 1m
    rules:
      - alert: CriticalDatabaseError
        expr: |
          sum(
            count_over_time(
              {app="api"} |= "FATAL: database connection failed" [5m]
            )
          ) > 10
        for: 0m  # Alert immediately when condition is true
        labels:
          severity: critical
          team: database
        annotations:
          summary: "Database connection failures spiking"
          description: "{{ $value }} database connection failures in last 5 minutes"
          runbook: "https://wiki.company.com/runbooks/db-connection"

      - alert: PaymentProcessingError
        expr: |
          sum by (payment_provider) (
            count_over_time(
              {app="payment-service"}
                | json
                | level="error"
                | error_type="payment_declined" [5m]
            )
          ) > 10
        for: 2m  # Sustained for 2 minutes
        labels:
          severity: warning
        annotations:
          summary: "Payment failures for {{ $labels.payment_provider }}"
```

**Key elements**:
- `for: 0m` vs `for: 2m`: How long condition must be true
- `sum()`: Aggregate across all matching streams
- `by (label)`: Group results for per-dimension alerting
- Route to Alertmanager just like Prometheus alerts
</details>

## Hands-On Exercise

### Scenario: Debug a Production Issue

You're on-call and receive an alert: "API error rate spiked." Use Loki to investigate.

### Setup

```bash
# Create kind cluster
kind create cluster --name loki-lab

# Install Loki stack
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install loki grafana/loki-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set prometheus.enabled=true \
  --set promtail.enabled=true

# Wait for pods
kubectl -n monitoring wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=120s

# Get Grafana password
kubectl -n monitoring get secret loki-grafana -o jsonpath="{.data.admin-password}" | base64 -d
echo

# Port forward
kubectl -n monitoring port-forward svc/loki-grafana 3000:80 &
```

### Deploy Test Application

```yaml
# error-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: error-generator
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: error-generator
  template:
    metadata:
      labels:
        app: error-generator
    spec:
      containers:
        - name: app
          image: busybox
          command: ["/bin/sh", "-c"]
          args:
            - |
              while true; do
                # Generate mix of logs
                echo '{"level":"info","msg":"Request processed","status_code":200,"path":"/api/users","duration":"50ms"}'
                echo '{"level":"info","msg":"Request processed","status_code":200,"path":"/api/orders","duration":"120ms"}'

                # Occasionally generate errors
                if [ $((RANDOM % 5)) -eq 0 ]; then
                  echo '{"level":"error","msg":"Database connection failed","status_code":500,"path":"/api/users","error":"connection timeout"}'
                fi
                if [ $((RANDOM % 10)) -eq 0 ]; then
                  echo '{"level":"error","msg":"External API error","status_code":502,"path":"/api/payments","error":"upstream unavailable"}'
                fi

                sleep 1
              done
```

```bash
kubectl apply -f error-app.yaml
```

### Investigation Tasks

1. **Find the error spike**
   - Open Grafana (http://localhost:3000)
   - Go to Explore, select Loki
   - Query: `{app="error-generator"} |= "error"`
   - Observe error patterns

2. **Calculate error rate**
   ```logql
   sum(rate({app="error-generator"} |= "error" [1m]))
   ```

3. **Break down by error type**
   ```logql
   sum by (path, status_code) (
     count_over_time({app="error-generator"} | json | level="error" [5m])
   )
   ```

4. **Find slow requests**
   ```logql
   {app="error-generator"}
     | json
     | duration > 100ms
     | line_format "{{.path}} took {{.duration}}"
   ```

5. **Create a dashboard** showing:
   - Error rate over time
   - Errors by path (pie chart)
   - Recent error logs (logs panel)

### Success Criteria

- [ ] Can query logs by namespace and app
- [ ] Can filter by log level using JSON parser
- [ ] Can calculate error rates
- [ ] Can create LogQL aggregation queries
- [ ] Dashboard shows error trends

### Cleanup

```bash
kind delete cluster --name loki-lab
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain why Loki is cheaper than Elasticsearch (index-free design, label-based)
- [ ] Calculate approximate storage costs: logs/day × compression ratio × retention
- [ ] Configure Promtail with pipeline stages for JSON extraction and multiline parsing
- [ ] Write LogQL queries using stream selectors, line filters, and parsers
- [ ] Calculate log rates using `rate()` and `count_over_time()` functions
- [ ] Identify and avoid high-cardinality labels (request IDs, user IDs as labels)
- [ ] Set up Grafana dashboards with log panels and LogQL variables
- [ ] Configure recording rules for expensive queries run frequently
- [ ] Design retention policies balancing compliance and cost
- [ ] Troubleshoot common issues: dropped logs, stream explosion, ingestion limits

## Next Module

Continue to [Module 1.5: Distributed Tracing](../module-1.5-tracing/) where we'll connect logs to traces using Jaeger and Tempo.

---

*"Logs tell the story. Labels help you find the right chapter. LogQL lets you skip to the good parts."*

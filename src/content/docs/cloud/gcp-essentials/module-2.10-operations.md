---
title: "Module 2.10: GCP Cloud Operations (Monitoring & Logging)"
slug: cloud/gcp-essentials/module-2.10-operations
sidebar:
  order: 11
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: Module 2.3 (Compute Engine), Module 2.7 (Cloud Run)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Cloud Monitoring dashboards with custom metrics, uptime checks, and alerting policies**
- **Implement structured logging with Cloud Logging and build log-based metrics for application-level observability**
- **Deploy Cloud Trace and Cloud Profiler to diagnose latency bottlenecks in distributed GCP applications**
- **Design multi-project monitoring with metrics scoping and centralized alerting across GCP organizations**

---

## Why This Module Matters

In November 2022, a fintech company's payment processing service began failing intermittently. Customers reported that approximately 5% of transactions were being declined with a generic "server error." The on-call engineer checked the Cloud Run dashboard and saw that CPU and memory utilization were normal. Request count looked steady. Everything appeared healthy from the infrastructure layer. The issue persisted for 4 hours before a senior engineer noticed an anomaly in the application logs: a third-party payment gateway was returning HTTP 429 (rate limit exceeded) for requests from a specific IP range. This log signal was buried in 2 million log lines per hour because the team had no log-based metrics, no alerting on error rates, and no structured logging. They were flying blind in a sea of unstructured text. The 4-hour delay in diagnosis cost them $340,000 in failed transactions and a significant hit to customer trust.

This incident demonstrates a truth that every platform engineer learns the hard way: **metrics tell you that something is wrong; logs tell you why.** You need both, and you need them working together. Cloud Operations (formerly Stackdriver) is GCP's integrated suite for monitoring, logging, and alerting. It is not a separate product you bolt on---it is deeply integrated into every GCP service. Cloud Logging automatically captures logs from managed services like Cloud Run, GKE, and Cloud Functions. Compute Engine instances require the Cloud Ops Agent for application and OS log collection. Cloud Monitoring automatically collects metrics from all GCP resources.

In this module, you will learn how Cloud Logging's architecture works (the log router, sinks, and exclusions), how to create log-based metrics that turn log patterns into alertable signals, how Cloud Monitoring dashboards and alerting policies work, and how to set up uptime checks for external monitoring of your services.

---

## Cloud Logging Architecture

### The Log Router

Every log entry generated in GCP flows through the **Log Router**. The router evaluates each log entry against a set of rules (called "sinks") to determine where the log goes.

```text
  Log Sources                     Log Router                   Destinations
  ───────────                     ──────────                   ────────────
  ┌──────────────┐
  │ Compute Engine│─────┐         ┌──────────────┐
  └──────────────┘     │         │              │            ┌──────────────┐
                        │         │  Inclusion   │───────────>│ Cloud Logging │
  ┌──────────────┐     ├────────>│  Filters     │            │ (default)     │
  │ Cloud Run    │─────┤         │              │            └──────────────┘
  └──────────────┘     │         │  Exclusion   │
                        │         │  Filters     │            ┌──────────────┐
  ┌──────────────┐     │         │              │───────────>│ Cloud Storage │
  │ GKE          │─────┤         │  Sinks       │            │ (long-term)   │
  └──────────────┘     │         │              │            └──────────────┘
                        │         │              │
  ┌──────────────┐     │         │              │            ┌──────────────┐
  │ Cloud Functions│────┘         │              │───────────>│ BigQuery      │
  └──────────────┘               │              │            │ (analytics)   │
                                  │              │            └──────────────┘
  ┌──────────────┐               │              │
  │ Cloud Audit   │──────────────>│              │            ┌──────────────┐
  │ Logs          │               │              │───────────>│ Pub/Sub       │
  └──────────────┘               └──────────────┘            │ (streaming)   │
                                                              └──────────────┘
```

### Log Types

| Log Type | Auto-collected | Cost | Retention | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Admin Activity** | Yes (always on) | Free | 400 days | IAM changes, resource creation |
| **Data Access** | Must enable | Paid | 30 days (default) | Who read what data |
| **System Event** | Yes (always on) | Free | 400 days | Live migration, auto-scaling |
| **Platform Logs** | Yes | Paid | 30 days (default) | Cloud Run requests, GKE events |
| **Application Logs** | Yes (stdout/stderr) | Paid | 30 days (default) | Your application output |

### Querying Logs

```bash
# Basic log query
gcloud logging read 'resource.type="cloud_run_revision"' \
  --limit=20 \
  --format=json

# Filter by severity
gcloud logging read 'severity>=ERROR AND resource.type="cloud_run_revision"' \
  --limit=10

# Filter by time range
gcloud logging read 'resource.type="gce_instance" AND timestamp>="2024-01-15T00:00:00Z" AND timestamp<"2024-01-16T00:00:00Z"' \
  --limit=50

# Search for specific text in log messages
gcloud logging read 'textPayload:"connection refused"' \
  --limit=10

# Structured log query (jsonPayload)
gcloud logging read 'jsonPayload.status>=500 AND resource.type="cloud_run_revision"' \
  --limit=20

# Query specific resource
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="my-api"' \
  --limit=10 \
  --format="table(timestamp, severity, textPayload)"
```

### Log Explorer Query Language

The Log Explorer in the console uses a powerful query language:

```text
# Compound queries
resource.type="cloud_run_revision"
AND resource.labels.service_name="my-api"
AND severity>=WARNING
AND jsonPayload.latency_ms>500
AND timestamp>="2024-01-15T10:00:00Z"

# NOT operator
resource.type="gce_instance"
AND NOT severity="DEBUG"

# Regex matching
textPayload=~"error.*timeout"

# Specific labels
labels."compute.googleapis.com/resource_name"="my-vm"
```

---

## Log Sinks: Routing Logs to Destinations

Sinks route copies of log entries to destinations outside the default Cloud Logging storage. This is essential for long-term retention, analytics, and compliance.

```bash
# Create a sink to Cloud Storage (long-term archival)
gcloud logging sinks create archive-all-logs \
  storage.googleapis.com/my-log-archive-bucket \
  --log-filter='severity>=INFO'

# Create a sink to BigQuery (analytics)
gcloud logging sinks create errors-to-bigquery \
  bigquery.googleapis.com/projects/my-project/datasets/error_logs \
  --log-filter='severity>=ERROR'

# Create a sink to Pub/Sub (real-time streaming)
gcloud logging sinks create critical-to-pubsub \
  pubsub.googleapis.com/projects/my-project/topics/critical-logs \
  --log-filter='severity=CRITICAL'

# After creating a sink, grant the sink's writer identity access
# to the destination
WRITER_IDENTITY=$(gcloud logging sinks describe archive-all-logs \
  --format="value(writerIdentity)")

gcloud storage buckets add-iam-policy-binding gs://my-log-archive-bucket \
  --member="$WRITER_IDENTITY" \
  --role="roles/storage.objectCreator"

# List all sinks
gcloud logging sinks list

# Update a sink's filter
gcloud logging sinks update archive-all-logs \
  --log-filter='severity>=WARNING'

# Delete a sink
gcloud logging sinks delete archive-all-logs
```

### Log Exclusions (Reducing Cost)

Exclusion filters prevent specific log entries from being ingested into Cloud Logging, reducing costs.

```bash
# Exclude debug logs from Cloud Run (they are noisy and expensive)
gcloud logging sinks create exclude-debug-logs \
  --log-filter='resource.type="cloud_run_revision" AND severity="DEBUG"' \
  --exclusion \
  --description="Exclude debug-level Cloud Run logs"

# Exclude health check logs (extremely noisy)
gcloud logging sinks create exclude-health-checks \
  --log-filter='httpRequest.requestUrl="/health" OR httpRequest.requestUrl="/healthz"' \
  --exclusion \
  --description="Exclude health check logs"

# View exclusions
gcloud logging sinks list --filter="exclusions"
```

---

## Log-Based Metrics: Turning Logs into Signals

Log-based metrics are the bridge between logging and monitoring. They count log entries matching a filter and expose that count as a metric you can alert on.

### Counter Metrics

```bash
# Create a metric that counts 5xx errors in Cloud Run
gcloud logging metrics create cloud_run_5xx_errors \
  --description="Count of 5xx errors in Cloud Run" \
  --log-filter='resource.type="cloud_run_revision" AND httpRequest.status>=500'

# Create a metric that counts authentication failures
gcloud logging metrics create auth_failures \
  --description="Authentication failures across all services" \
  --log-filter='jsonPayload.event="auth_failure" OR textPayload:"authentication failed"'

# List log-based metrics
gcloud logging metrics list

# View metric details
gcloud logging metrics describe cloud_run_5xx_errors
```

### Distribution Metrics

Distribution metrics capture the distribution of values (like latency) extracted from log fields.

```bash
# Create a distribution metric for response latency
gcloud logging metrics create api_latency \
  --description="API response latency distribution" \
  --log-filter='resource.type="cloud_run_revision" AND httpRequest.latency!=""' \
  --bucket-options='linear-buckets={"numFiniteBuckets": 20, "width": 100, "offset": 0}' \
  --value-extractor='EXTRACT(httpRequest.latency)'
```

---

## Cloud Monitoring: Dashboards and Metrics

### Built-in Metrics

GCP automatically collects hundreds of metrics from every service. You do not need to install agents or configure anything for these.

| Service | Example Metrics |
| :--- | :--- |
| **Compute Engine** | `compute.googleapis.com/instance/cpu/utilization`, `disk/read_bytes_count` |
| **Cloud Run** | `run.googleapis.com/request_count`, `request_latencies`, `container/cpu/utilization` |
| **Cloud SQL** | `cloudsql.googleapis.com/database/cpu/utilization`, `connections` |
| **Cloud Storage** | `storage.googleapis.com/api/request_count`, `total_bytes` |
| **Cloud Functions** | `cloudfunctions.googleapis.com/function/execution_count`, `execution_times` |

```bash
# List available metric types for a service
gcloud monitoring metrics-descriptors list \
  --filter='metric.type = starts_with("run.googleapis.com")' \
  --format="table(type, description)" \
  --limit=20

# Query a specific metric (requires Monitoring Query Language - MQL)
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count" AND resource.labels.service_name="my-api"' \
  --interval-start-time=$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --format=json
```

### Creating Dashboards

Dashboards can be created via the console (recommended for exploration) or via JSON/YAML (recommended for infrastructure-as-code).

```bash
# Create a dashboard from a JSON definition
cat > /tmp/dashboard.json << 'EOF'
{
  "displayName": "Cloud Run API Dashboard",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Count by Status",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"my-api\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM",
                      "groupByFields": ["metric.labels.response_code_class"]
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "P99 Latency",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"my-api\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_PERCENTILE_99"
                    }
                  }
                }
              }
            ]
          }
        }
      }
    ]
  }
}
EOF

gcloud monitoring dashboards create --config-from-file=/tmp/dashboard.json

# List dashboards
gcloud monitoring dashboards list --format="table(displayName, name)"
```

### PromQL in Cloud Monitoring

Cloud Monitoring natively supports PromQL for users familiar with Prometheus.

```text
# Request rate for a Cloud Run service
rate(run_googleapis_com:request_count{service_name="my-api"}[5m])

# Error rate (5xx responses)
rate(run_googleapis_com:request_count{service_name="my-api", response_code_class="5xx"}[5m])
  /
rate(run_googleapis_com:request_count{service_name="my-api"}[5m])
  * 100

# P95 latency
histogram_quantile(0.95, rate(run_googleapis_com:request_latencies_bucket{service_name="my-api"}[5m]))

# CPU utilization above 80%
compute_googleapis_com:instance_cpu_utilization{instance_name=~"web-.*"} > 0.8
```

---

## Alerting Policies

### Creating Alert Policies

```bash
# Create an alert policy for high error rate
cat > /tmp/alert-policy.json << 'EOF'
{
  "displayName": "Cloud Run 5xx Error Rate > 5%",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "5xx error rate exceeds 5%",
      "conditionThreshold": {
        "filter": "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND metric.labels.response_code_class=\"5xx\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_SUM",
            "groupByFields": ["resource.labels.service_name"]
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.05,
        "duration": "300s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "notificationChannels": [],
  "alertStrategy": {
    "autoClose": "604800s"
  }
}
EOF

gcloud monitoring policies create --policy-from-file=/tmp/alert-policy.json

# List alert policies
gcloud monitoring policies list \
  --format="table(displayName, enabled, conditions[0].displayName)"
```

### Notification Channels

```bash
# Create an email notification channel
gcloud monitoring channels create \
  --display-name="Ops Team Email" \
  --type=email \
  --channel-labels="email_address=ops@example.com"

# Create a Slack notification channel
gcloud monitoring channels create \
  --display-name="Incidents Slack" \
  --type=slack \
  --channel-labels="channel_name=#incidents,auth_token=xoxb-..."

# List notification channels
gcloud monitoring channels list \
  --format="table(displayName, type, name)"

# Update an alert policy to use a notification channel
CHANNEL_ID=$(gcloud monitoring channels list --filter="displayName='Ops Team Email'" --format="value(name)")

gcloud monitoring policies update POLICY_ID \
  --add-notification-channels=$CHANNEL_ID
```

### Alert Policy Best Practices

| Practice | Why | Example |
| :--- | :--- | :--- |
| **Alert on symptoms, not causes** | Symptoms affect users; causes are for investigation | Alert on error rate, not CPU usage |
| **Use multi-condition alerts** | Reduce noise from transient spikes | Error rate > 5% AND request count > 100 |
| **Set appropriate windows** | Too short = noise; too long = late | 5-minute window for critical; 15-minute for warning |
| **Include runbook links** | Reduce MTTR by guiding responders | Link to troubleshooting playbook in alert description |
| **Avoid alert fatigue** | Too many alerts = ignored alerts | Only alert on actionable conditions |

---

## Uptime Checks

Uptime checks monitor the availability of your public endpoints from multiple global locations.

```bash
# Create an HTTP uptime check
gcloud monitoring uptime create my-api-uptime \
  --display-name="My API Health Check" \
  --resource-type=uptime-url \
  --monitored-resource="host=my-api-abc123-uc.a.run.app,project_id=my-project" \
  --http-check-path="/health" \
  --http-check-port=443 \
  --period=60 \
  --timeout=10 \
  --checker-type=STATIC_IP_CHECKERS

# List uptime checks
gcloud monitoring uptime list-configs \
  --format="table(displayName, httpCheck.path, period)"

# Create an alert policy for uptime check failure
# (alert if the check fails from 2+ regions)
cat > /tmp/uptime-alert.json << 'EOF'
{
  "displayName": "API Uptime Check Failed",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Uptime check failing",
      "conditionThreshold": {
        "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_NEXT_OLDER",
            "crossSeriesReducer": "REDUCE_COUNT_FALSE",
            "groupByFields": ["resource.labels.host"]
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 2,
        "duration": "0s"
      }
    }
  ]
}
EOF

gcloud monitoring policies create --policy-from-file=/tmp/uptime-alert.json
```

---

## Structured Logging

Writing structured (JSON) logs instead of plain text enables powerful querying and log-based metrics.

### Python Structured Logging for Cloud Run

```python
import json
import logging
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "component": record.name,
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "latency_ms"):
            log_entry["latency_ms"] = record.latency_ms

        return json.dumps(log_entry)

# Configure logging
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("my-api")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("Request processed",
            extra={"request_id": "abc-123", "latency_ms": 45, "user_id": "user-456"})
# Output: {"severity": "INFO", "message": "Request processed",
#          "request_id": "abc-123", "latency_ms": 45, "user_id": "user-456"}
```

In Cloud Logging, this is parsed as `jsonPayload`, allowing queries like:

```text
jsonPayload.latency_ms > 200
jsonPayload.user_id = "user-456"
jsonPayload.severity = "ERROR"
```

---

## Did You Know?

1. **Cloud Logging ingests over 150 petabytes of log data per month** across all GCP customers. The log router processes over 50 billion log entries per day. Despite this scale, the median query response time in the Log Explorer is under 3 seconds for queries spanning a 1-hour time window.

2. **Log-based metrics are evaluated in real-time as logs flow through the log router**, not after they are stored. This means you can create an alert based on a log-based metric and receive a notification within 60-90 seconds of the triggering log entry being written---even before you could find it manually in the Log Explorer.

3. **Cloud Monitoring's uptime checks run from 6 global regions simultaneously** (USA-Oregon, USA-Virginia, South America, Europe, Asia Pacific-1, Asia Pacific-2). A check is considered "failed" only when it fails from multiple regions, reducing false positives from network partitions. You can see the per-region results in the uptime check dashboard.

4. **The Ops Agent (successor to the legacy Monitoring and Logging agents) supports both Prometheus metric scraping and fluent-bit log collection** in a single agent. If you are running custom metrics in Prometheus format on your VMs, the Ops Agent can scrape them and send them to Cloud Monitoring without running a separate Prometheus server.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Not creating log sinks for long-term retention | Default 30-day retention seems enough | Create sinks to Cloud Storage for compliance; 30 days passes quickly during incident investigation |
| Logging too much at DEBUG level | Verbose logging during development | Use INFO as default; enable DEBUG only in non-production; use exclusion filters |
| Not creating log-based metrics | Relying on manual log searching | Create metrics for key patterns (errors, auth failures, latency thresholds) |
| Setting alert thresholds too sensitive | Wanting to catch every issue | Use multi-condition alerts and appropriate duration windows (5-15 minutes) |
| Not using structured logging | Plain text seems simpler | JSON logs enable powerful filtering in Log Explorer; use structured logging from day one |
| Ignoring uptime checks | Internal monitoring seems sufficient | Uptime checks verify from external perspective; catches DNS, certificate, and network issues |
| Alert fatigue from too many alerts | Adding alerts without reviewing existing ones | Quarterly alert hygiene review; delete alerts that are never actionable |
| Not routing audit logs to BigQuery | Do not know about log sinks | Create a sink for audit logs to BigQuery for security analytics and compliance |

---

## Quiz

<details>
<summary>1. What is the Log Router, and why is it important?</summary>

The Log Router is the central component in Cloud Logging that receives **every** log entry generated in GCP and decides where it goes. It evaluates each log entry against inclusion filters, exclusion filters, and sink configurations. This is important because it gives you control over log storage costs and destinations. You can route error logs to BigQuery for analytics, archive all logs to Cloud Storage for compliance, stream critical logs to Pub/Sub for real-time processing, and exclude noisy debug logs to reduce costs. Without the Log Router, all logs would simply go to the default Cloud Logging storage, which has a 30-day retention and can be expensive at scale.
</details>

<details>
<summary>2. What is the difference between a log-based counter metric and a log-based distribution metric?</summary>

A **counter metric** counts the number of log entries matching a filter. For example, "count all log entries where `httpRequest.status >= 500`" gives you the number of 5xx errors per time period. A **distribution metric** captures the distribution of numeric values extracted from log entries. For example, extracting `httpRequest.latency` from each log entry gives you a histogram of latency values, allowing you to compute percentiles (P50, P95, P99). Counter metrics answer "how many?" while distribution metrics answer "how long/how big?" Both are computed in real-time as logs flow through the router.
</details>

<details>
<summary>3. How do exclusion filters reduce Cloud Logging costs?</summary>

Exclusion filters tell the Log Router to **drop** specific log entries before they are ingested into Cloud Logging. Dropped logs are never stored and never billed. This is critical because Cloud Logging charges per volume of ingested data. Common exclusions include: health check logs (extremely high volume, low value), debug-level logs in production, and repetitive informational messages. Important caveat: excluded logs are still available to sinks that were created **before** the exclusion---so you can exclude logs from default storage while still routing them to a cheaper destination like Cloud Storage.
</details>

<details>
<summary>4. Why should you "alert on symptoms, not causes"?</summary>

Symptoms are what users experience (high error rate, slow response times, service unavailable). Causes are internal implementation details (high CPU, full disk, memory pressure). Alerting on symptoms means you get notified when users are actually affected, reducing false positives. A VM at 95% CPU is not inherently a problem if response times are still within SLA. Conversely, a VM at 50% CPU might have a memory leak causing request failures. If you alert on error rate exceeding 5%, you catch the user-facing problem regardless of the underlying cause. The cause is what you investigate after the alert fires, not what triggers the alert.
</details>

<details>
<summary>5. You need to keep all logs for 7 years for regulatory compliance, but the default Cloud Logging retention is 30 days. How do you solve this?</summary>

Create a **log sink** that routes all logs to a **Cloud Storage bucket** with a 7-year retention policy. Set a lifecycle rule on the bucket to transition logs from STANDARD to NEARLINE at 30 days, COLDLINE at 90 days, and ARCHIVE at 365 days to optimize costs. Lock the retention policy on the bucket to prevent anyone from deleting logs early. The logs are still available in Cloud Logging for 30 days for real-time querying, and in Cloud Storage for the full 7-year compliance period. For analytical queries on older logs, create a second sink to BigQuery (for the subset of logs you need to query regularly).
</details>

<details>
<summary>6. What are the benefits of structured (JSON) logging compared to plain text logging?</summary>

Structured logging outputs log entries as JSON objects with named fields, while plain text logging writes free-form strings. Benefits of structured logging: (1) **Queryable fields** - you can filter on specific fields like `jsonPayload.user_id="user-123"` instead of regex-matching text. (2) **Log-based metrics** - you can create metrics based on specific JSON fields (e.g., count entries where `status >= 500`). (3) **Automatic severity mapping** - Cloud Logging recognizes the `severity` field in JSON. (4) **Contextual data** - you can include structured metadata (request IDs, user IDs, latency) that is directly filterable. (5) **Machine parseable** - downstream systems (BigQuery, SIEM) can process structured logs without custom parsers.
</details>

---

## Hands-On Exercise: Monitoring and Alerting for Cloud Run

### Objective

Deploy a Cloud Run service with structured logging, create log-based metrics, set up a monitoring dashboard, and configure alerting.

### Prerequisites

- `gcloud` CLI installed and authenticated
- A GCP project with billing enabled

### Tasks

**Task 1: Deploy a Cloud Run Service with Structured Logging**

<details>
<summary>Solution</summary>

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com

mkdir -p /tmp/ops-lab && cd /tmp/ops-lab

cat > main.py << 'PYEOF'
import json
import logging
import os
import random
import sys
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
        }
        for key in ["latency_ms", "status_code", "path", "error_type"]:
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        return json.dumps(entry)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("ops-lab")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@app.route("/")
def home():
    start = time.time()
    latency_ms = int((time.time() - start) * 1000) + random.randint(5, 50)

    logger.info("Request processed",
                extra={"latency_ms": latency_ms, "status_code": 200, "path": "/"})
    return jsonify({"status": "ok", "latency_ms": latency_ms})

@app.route("/slow")
def slow():
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
    latency_ms = int(delay * 1000)

    logger.warning("Slow request detected",
                   extra={"latency_ms": latency_ms, "status_code": 200, "path": "/slow"})
    return jsonify({"status": "ok", "latency_ms": latency_ms})

@app.route("/error")
def error():
    error_types = ["DatabaseTimeout", "AuthenticationFailed", "RateLimitExceeded"]
    error_type = random.choice(error_types)

    logger.error("Request failed",
                 extra={"latency_ms": 0, "status_code": 500, "path": "/error",
                        "error_type": error_type})
    return jsonify({"status": "error", "error": error_type}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
PYEOF

cat > requirements.txt << 'EOF'
flask>=3.0.0
gunicorn>=21.2.0
EOF

cat > Dockerfile << 'DEOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "main:app"]
DEOF

gcloud run deploy ops-lab-api \
  --source=. \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=256Mi

SERVICE_URL=$(gcloud run services describe ops-lab-api \
  --region=$REGION --format="value(status.url)")
echo "Service URL: $SERVICE_URL"
```
</details>

**Task 2: Generate Traffic and Logs**

<details>
<summary>Solution</summary>

```bash
SERVICE_URL=$(gcloud run services describe ops-lab-api \
  --region=$REGION --format="value(status.url)")

# Generate normal traffic
for i in $(seq 1 15); do
  curl -s "$SERVICE_URL/" > /dev/null
done

# Generate slow requests
for i in $(seq 1 5); do
  curl -s "$SERVICE_URL/slow" > /dev/null
done

# Generate errors
for i in $(seq 1 8); do
  curl -s "$SERVICE_URL/error" > /dev/null
done

echo "Traffic generated. Waiting for logs to appear..."
sleep 15

# View logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="ops-lab-api" AND jsonPayload.message!=""' \
  --limit=15 \
  --format="table(timestamp, jsonPayload.severity, jsonPayload.message, jsonPayload.status_code, jsonPayload.latency_ms)"
```
</details>

**Task 3: Create Log-Based Metrics**

<details>
<summary>Solution</summary>

```bash
# Metric: Count of 500 errors
gcloud logging metrics create ops_lab_errors \
  --description="Count of 500 errors in ops-lab-api" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ops-lab-api" AND jsonPayload.status_code=500'

# Metric: Count of slow requests (latency > 500ms)
gcloud logging metrics create ops_lab_slow_requests \
  --description="Count of slow requests (>500ms) in ops-lab-api" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="ops-lab-api" AND jsonPayload.latency_ms>500'

# List metrics
gcloud logging metrics list \
  --format="table(name, description, filter)"
```
</details>

**Task 4: Create an Uptime Check**

<details>
<summary>Solution</summary>

```bash
# Get the Cloud Run hostname
SERVICE_HOST=$(echo $SERVICE_URL | sed 's|https://||')

# Create an uptime check
# Note: uptime checks via gcloud have limited support;
# using the REST API is more reliable for complex configs
gcloud monitoring uptime create ops-lab-uptime \
  --display-name="Ops Lab API Health" \
  --resource-type=uptime-url \
  --resource-labels="host=$SERVICE_HOST,project_id=$PROJECT_ID" \
  --http-check-path="/health" \
  --http-check-port=443 \
  --http-check-request-method=GET \
  --period=60 \
  --timeout=10

# List uptime checks
gcloud monitoring uptime list-configs \
  --format="table(displayName, httpCheck.path, period)"

echo "Uptime check created. Results will appear in ~2 minutes."
```
</details>

**Task 5: Query Monitoring Metrics**

<details>
<summary>Solution</summary>

```bash
# Generate more traffic for metrics to populate
for i in $(seq 1 20); do
  curl -s "$SERVICE_URL/" > /dev/null
  curl -s "$SERVICE_URL/error" > /dev/null 2>&1
done

sleep 30

# Query Cloud Run request count
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count" AND resource.labels.service_name="ops-lab-api"' \
  --interval-start-time=$(date -u -v-15M +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "15 minutes ago" +%Y-%m-%dT%H:%M:%SZ) \
  --format="table(metric.labels.response_code, points[0].value.int64Value)" \
  --limit=10

# Query the log-based error metric
gcloud monitoring time-series list \
  --filter='metric.type="logging.googleapis.com/user/ops_lab_errors"' \
  --interval-start-time=$(date -u -v-15M +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "15 minutes ago" +%Y-%m-%dT%H:%M:%SZ) \
  --format=json \
  --limit=5
```
</details>

**Task 6: Clean Up**

<details>
<summary>Solution</summary>

```bash
# Delete Cloud Run service
gcloud run services delete ops-lab-api --region=$REGION --quiet

# Delete log-based metrics
gcloud logging metrics delete ops_lab_errors --quiet
gcloud logging metrics delete ops_lab_slow_requests --quiet

# Delete uptime check
UPTIME_ID=$(gcloud monitoring uptime list-configs \
  --filter="displayName='Ops Lab API Health'" --format="value(name)" | head -1)
gcloud monitoring uptime delete $UPTIME_ID --quiet 2>/dev/null || true

# Clean up local files
rm -rf /tmp/ops-lab

echo "Cleanup complete."
```
</details>

### Success Criteria

- [ ] Cloud Run service deployed with structured JSON logging
- [ ] Traffic generated (normal, slow, and error requests)
- [ ] Structured logs visible in Cloud Logging with queryable fields
- [ ] Log-based metrics created for errors and slow requests
- [ ] Uptime check configured and running
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 2.11: Cloud Build & CI/CD](../module-2.11-cloud-build/)** --- Learn how to define build pipelines with `cloudbuild.yaml`, use built-in and custom builders, set up triggers from GitHub and GitLab, and orchestrate deployments with Cloud Deploy.

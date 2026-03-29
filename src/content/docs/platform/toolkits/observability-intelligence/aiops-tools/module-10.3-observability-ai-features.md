---
title: "Module 10.3: Observability AI Features"
slug: platform/toolkits/observability-intelligence/aiops-tools/module-10.3-observability-ai-features
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Prerequisites

Before starting this module:
- [AIOps Discipline](../../disciplines/data-ai/aiops/) — Conceptual foundation
- [Observability Toolkit](../observability/) — Platform fundamentals
- Basic understanding of observability platforms (Datadog, Dynatrace, New Relic)

## Why This Module Matters

Modern observability platforms have **AI capabilities built-in**. These aren't separate products—they're intelligent features woven throughout the platform. Understanding these capabilities helps you:

1. **Maximize existing investments** — You may already have AI features you're not using
2. **Reduce alert fatigue** — Platform AI automatically baselines and detects anomalies
3. **Accelerate troubleshooting** — AI-powered root cause analysis saves hours
4. **Avoid duplicate tooling** — Don't build what's already included

## Did You Know?

- **Dynatrace Davis AI** processes over **1 trillion dependencies per hour** across customer environments. It uses Smartscape topology to understand causation, not just correlation—meaning it can tell you "A caused B" rather than just "A and B happened together."

- **Datadog Watchdog** automatically monitors **all your metrics** without configuration. The engineering team built it after realizing customers weren't using 80% of their anomaly detection features because setup was too complex.

- **New Relic's Applied Intelligence** reduces alert noise by up to **80%** through automatic correlation. Their ML models were trained on data from millions of incidents across thousands of customers.

- **Splunk ITSI** pioneered the concept of **service health scores**—aggregating hundreds of KPIs into a single number. A Fortune 100 retailer uses these scores to predict outages 30 minutes before they impact customers.

## War Story: The $4.2M AI That Nobody Trusted

A financial services company invested heavily in observability AI features—Datadog Watchdog plus New Relic Applied Intelligence running in parallel. Their monthly spend exceeded $350,000. Six months in, they calculated the ROI and found it was negative.

**What went wrong:**

The AI was working perfectly. Watchdog detected anomalies accurately. Applied Intelligence correlated alerts into incidents. The problem? Nobody trusted the AI output.

When on-call engineers received AI-generated alerts, they'd manually verify everything anyway. "Watchdog says there's an anomaly in the payment service, but let me check the dashboards myself..." They treated AI as another noise source rather than a trusted assistant.

**Root causes:**
1. **No human-in-the-loop training**: Engineers never provided feedback on AI accuracy
2. **Alert fatigue transfer**: Previous noisy alerts trained engineers to ignore everything
3. **Black box distrust**: Engineers couldn't understand why AI flagged certain events
4. **Missing runbooks**: AI detected problems but didn't guide resolution

**The fix:**

They implemented a 3-month "trust building" program:
1. Weekly reviews of AI vs. human detection accuracy (AI was 94% accurate)
2. Added "AI Explanation" field showing why Watchdog flagged each anomaly
3. Linked every AI alert to relevant runbooks
4. Gamified feedback—engineers earned points for confirming/rejecting AI calls

After the program, AI-assisted MTTR dropped from 47 minutes to 12 minutes. Engineers now trust the AI because they understand it.

**The lesson**: AI features are only as valuable as the trust your team places in them. Invest in explainability and feedback loops, not just technology.

---

## The Built-In AI Landscape

```
OBSERVABILITY PLATFORM AI FEATURES
────────────────────────────────────────────────────────────────

DATADOG                     DYNATRACE                   NEW RELIC
┌─────────────┐            ┌─────────────┐            ┌─────────────┐
│  Watchdog   │            │  Davis AI   │            │  Applied    │
│             │            │             │            │Intelligence │
├─────────────┤            ├─────────────┤            ├─────────────┤
│• Auto-detect│            │• Causation  │            │• Incident   │
│• Anomalies  │            │• Root cause │            │  Intel      │
│• Root cause │            │• Impact     │            │• Anomaly    │
│  analysis   │            │  analysis   │            │  detection  │
│• Forecasts  │            │• Forecasts  │            │• Correlation│
└─────────────┘            └─────────────┘            └─────────────┘

SPLUNK                      ELASTIC                     GRAFANA
┌─────────────┐            ┌─────────────┐            ┌─────────────┐
│    ITSI     │            │  ML Jobs    │            │ ML Features │
│             │            │             │            │             │
├─────────────┤            ├─────────────┤            ├─────────────┤
│• Predictive │            │• Anomaly    │            │• Forecasting│
│  analytics  │            │  detection  │            │• Anomaly    │
│• Service    │            │• Forecasting│            │  detection  │
│  health     │            │• Outliers   │            │• (Limited)  │
│• Event      │            │             │            │             │
│  correlation│            │             │            │             │
└─────────────┘            └─────────────┘            └─────────────┘
```

---

## Datadog Watchdog

Datadog Watchdog is an **automatic anomaly detection engine** that continuously monitors all your metrics, traces, and logs without any configuration.

### How Watchdog Works

```
WATCHDOG ARCHITECTURE
────────────────────────────────────────────────────────────────

DATA COLLECTION                 ANALYSIS                  ALERTS
┌─────────────┐              ┌─────────────┐          ┌─────────────┐
│   Metrics   │──────────────▶             │          │             │
├─────────────┤              │  Watchdog   │          │  Watchdog   │
│    Logs     │──────────────▶   Engine    │──────────▶   Stories   │
├─────────────┤              │             │          │             │
│   Traces    │──────────────▶• Baselining │          │• Root cause │
├─────────────┤              │• Detection  │          │• Impact     │
│   Events    │──────────────▶• Correlation│          │• Timeline   │
└─────────────┘              └─────────────┘          └─────────────┘

KEY CAPABILITIES:
─────────────────────────────────────────────────────────────────

✓ Zero configuration — Works on all metrics automatically
✓ Seasonal awareness — Understands daily/weekly patterns
✓ Multi-metric correlation — Groups related anomalies
✓ Root cause analysis — Identifies probable cause
✓ Impact assessment — Shows affected services
```

### Watchdog Detection Types

| Type | What It Detects | Example |
|------|-----------------|---------|
| **Metric Anomalies** | Unusual metric behavior | CPU 40% higher than baseline |
| **APM Anomalies** | Performance degradation | API latency 3x normal |
| **Log Anomalies** | Error rate spikes | 500 errors up 10x |
| **Deployment Tracking** | Post-deployment issues | Error rate spiked after deploy |

### Configuring Watchdog Alerts

While Watchdog runs automatically, you can customize alerting:

```yaml
# Watchdog Monitor Configuration (via Terraform)
resource "datadog_monitor" "watchdog_alert" {
  name = "Watchdog Alert - Payment Service"
  type = "event alert"

  query = "events('sources:watchdog priority:all tags:service:payment-service').rollup('count').last('5m') > 0"

  message = <<-EOT
    Watchdog detected an anomaly in the payment service.

    {{#is_alert}}
    **Anomaly Details:**
    - Story: {{event.title}}
    - Impact: Check Watchdog for affected endpoints

    [View Watchdog Story](https://app.datadoghq.com/watchdog)
    {{/is_alert}}

    @slack-platform-team @pagerduty-oncall
  EOT

  tags = ["service:payment-service", "team:platform"]

  priority = 3
}
```

### Watchdog Root Cause Analysis

```
WATCHDOG RCA EXAMPLE
────────────────────────────────────────────────────────────────

DETECTED ANOMALY: Checkout service latency increased 300%

WATCHDOG ANALYSIS:
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  ROOT CAUSE IDENTIFIED:                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Database Query Time                                  │ │
│  │ payments-db.query.time increased 400%                │ │
│  │ Started: 14:32 UTC                                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  IMPACT CHAIN:                                             │
│  payments-db ──▶ payment-service ──▶ checkout-service     │
│       ↑               ↑                    ↑              │
│     ROOT          AFFECTED             DETECTED           │
│                                                            │
│  CORRELATED EVENTS:                                        │
│  • 14:30 - Deployment: payments-db schema migration       │
│  • 14:32 - payments-db slow queries started               │
│  • 14:33 - payment-service p99 latency increased          │
│  • 14:35 - checkout-service errors started                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Watchdog Forecasts

Datadog Watchdog can also forecast metric values:

```python
# Query Watchdog forecasts via Datadog API
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.metrics_api import MetricsApi

def get_forecast(metric_name: str, hours_ahead: int = 24):
    """Get Watchdog forecast for a metric."""

    configuration = Configuration()

    with ApiClient(configuration) as api_client:
        api = MetricsApi(api_client)

        # Use forecast function in query
        query = f"forecast({metric_name}{{*}}, 'linear', {hours_ahead})"

        now = int(time.time())
        response = api.query_metrics(
            _from=now - 3600,  # Last hour for baseline
            to=now + (hours_ahead * 3600),  # Future
            query=query
        )

        return response.series

# Example: Forecast disk usage
forecast = get_forecast("system.disk.used", hours_ahead=72)
print(f"Predicted disk usage in 72 hours: {forecast[-1].pointlist[-1][1]} bytes")
```

---

## Dynatrace Davis AI

Davis is Dynatrace's **deterministic AI engine** that provides causation-based analysis rather than correlation-based.

### Davis Architecture

```
DAVIS AI ARCHITECTURE
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                     SMARTSCAPE                               │
│  (Real-time dependency mapping of your entire environment)  │
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │  Host   │────│ Process │────│ Service │────│ User    │  │
│  │  Layer  │    │  Layer  │    │  Layer  │    │ Actions │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┘        │
│                           │                                  │
│                           ▼                                  │
│                    ┌─────────────┐                          │
│                    │  Davis AI   │                          │
│                    │             │                          │
│                    │• Causation  │                          │
│                    │• Not just   │                          │
│                    │  correlation│                          │
│                    │• Deterministic                          │
│                    └─────────────┘                          │
│                           │                                  │
│                           ▼                                  │
│                    ┌─────────────┐                          │
│                    │  Problems   │                          │
│                    │  (Tickets)  │                          │
│                    └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘

DAVIS DIFFERENTIATOR:
─────────────────────────────────────────────────────────────────
Correlation: "A and B happened together"
Causation:   "A caused B because of dependency chain X → Y → Z"
```

### Davis Problem Detection

Davis automatically creates **Problems** that group related issues:

```
DAVIS PROBLEM EXAMPLE
────────────────────────────────────────────────────────────────

PROBLEM: Response time degradation affecting real users
Status: OPEN | Impact: 847 users affected | Duration: 12 min

ROOT CAUSE:
┌─────────────────────────────────────────────────────────────┐
│ Container restart on kubernetes-node-3                       │
│ payment-service-pod-7d9f8 restarted due to OOMKilled        │
└─────────────────────────────────────────────────────────────┘

IMPACT CHAIN (Smartscape-derived):
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  kubernetes-node-3 (infrastructure)                          │
│         │                                                    │
│         ▼                                                    │
│  payment-service-pod-7d9f8 (container)                       │
│         │ OOMKilled                                          │
│         ▼                                                    │
│  PaymentService (service)                                    │
│         │ Service unavailable 3 min                          │
│         ▼                                                    │
│  CheckoutService (service)                                   │
│         │ Degraded response                                  │
│         ▼                                                    │
│  /checkout (user action)                                     │
│         │ 847 users affected                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘

RELATED EVENTS:
• 14:32:15 - Memory usage exceeded limit (1.5GB)
• 14:32:16 - Container OOMKilled
• 14:32:17 - Pod restarting
• 14:35:18 - Pod running again
```

### Davis Data Units (DDU) and Configuration

```yaml
# Dynatrace configuration via Monaco (Monitoring as Code)
# davis-problem-notification.yaml

config:
  - notification: "davis-slack-notification"

notification:
  - name: "Davis Slack Notification"
    type: "SLACK"
    enabled: true
    url: "{{ .Env.SLACK_WEBHOOK_URL }}"
    channel: "#alerts-production"

    # Filter which problems trigger notifications
    alertingProfile: "production-critical"

    # Message template
    payload: |
      {
        "text": "🚨 Davis Problem Detected",
        "attachments": [{
          "color": "danger",
          "fields": [
            {"title": "Problem", "value": "{ProblemTitle}", "short": true},
            {"title": "Impact", "value": "{ImpactedEntities}", "short": true},
            {"title": "Root Cause", "value": "{RootCauseEntity}", "short": false}
          ]
        }]
      }
```

### Davis Natural Language Queries

Davis supports natural language queries via Dynatrace Grail:

```
DAVIS NATURAL LANGUAGE EXAMPLES
────────────────────────────────────────────────────────────────

Query: "What caused the slowdown yesterday at 3pm?"
Davis: "Response time degradation was caused by database
        connection pool exhaustion on payments-db-primary.
        This occurred after a deployment at 14:45."

Query: "Which services are at risk of failure?"
Davis: "payment-service has 3 reliability risks:
        1. Memory usage trending toward limit (85% → 92%)
        2. Error rate increasing (0.1% → 0.8%)
        3. CPU saturation during peak hours"

Query: "Why did we have outages last week?"
Davis: "4 problems detected last week:
        1. Network timeout (Tuesday, 12 min, 1.2k users)
        2. Database failover (Wednesday, 8 min, 856 users)
        3. Deployment failure (Thursday, 23 min, 2.1k users)
        4. Memory leak (Friday, 45 min, 3.4k users)"
```

---

## New Relic Applied Intelligence

New Relic's Applied Intelligence focuses on **incident intelligence**—reducing noise and accelerating response.

### Applied Intelligence Components

```
NEW RELIC APPLIED INTELLIGENCE
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                  APPLIED INTELLIGENCE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │   INCIDENT    │  │   ANOMALY     │  │    PROACTIVE  │   │
│  │   INTEL       │  │   DETECTION   │  │    DETECTION  │   │
│  ├───────────────┤  ├───────────────┤  ├───────────────┤   │
│  │• Correlation  │  │• Automatic    │  │• Predictive   │   │
│  │• Noise reduc  │  │  baselines    │  │  alerts       │   │
│  │• Root cause   │  │• Outlier      │  │• Capacity     │   │
│  │• Grouping     │  │  detection    │  │  forecasts    │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  DECISIONS                             │  │
│  │  (ML-powered workflow routing and enrichment)         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Incident Intelligence Configuration

```python
# Configure New Relic Incident Intelligence via NerdGraph API
import requests

NERDGRAPH_URL = "https://api.newrelic.com/graphql"
API_KEY = os.environ["NEW_RELIC_API_KEY"]

def create_correlation_policy(account_id: int, policy_name: str):
    """Create an incident intelligence correlation policy."""

    mutation = """
    mutation CreateIncidentIntelligencePolicy($accountId: Int!, $policy: IncidentIntelligencePolicyInput!) {
      incidentIntelligenceCreatePolicy(accountId: $accountId, policy: $policy) {
        policy {
          id
          name
        }
        errors {
          description
        }
      }
    }
    """

    variables = {
        "accountId": account_id,
        "policy": {
            "name": policy_name,
            "description": "Correlate alerts from same service",
            "priority": "HIGH",
            "conditions": [
                {
                    "attribute": "service",
                    "operator": "EQUALS"
                },
                {
                    "attribute": "environment",
                    "operator": "EQUALS"
                }
            ],
            "timeWindow": {
                "minutes": 5
            }
        }
    }

    response = requests.post(
        NERDGRAPH_URL,
        headers={
            "Content-Type": "application/json",
            "API-Key": API_KEY
        },
        json={"query": mutation, "variables": variables}
    )

    return response.json()

# Example: Create policy for payment service
policy = create_correlation_policy(
    account_id=12345,
    policy_name="Payment Service Correlation"
)
```

### Applied Intelligence Workflows

```
APPLIED INTELLIGENCE WORKFLOW
────────────────────────────────────────────────────────────────

BEFORE APPLIED INTELLIGENCE:
┌────────────────────────────────────────────────────────────┐
│ Alert Storm: 150 alerts in 10 minutes                      │
│                                                            │
│ ⚠ CPU High - web-server-1                                  │
│ ⚠ CPU High - web-server-2                                  │
│ ⚠ Memory High - web-server-1                               │
│ ⚠ Response Time High - /api/checkout                       │
│ ⚠ Response Time High - /api/payment                        │
│ ⚠ Error Rate High - payment-service                        │
│ ⚠ Error Rate High - checkout-service                       │
│ ... 143 more alerts ...                                    │
│                                                            │
│ On-call engineer: 😱 Where do I even start?                │
└────────────────────────────────────────────────────────────┘

AFTER APPLIED INTELLIGENCE:
┌────────────────────────────────────────────────────────────┐
│ Incident: Payment System Degradation                       │
│                                                            │
│ 📊 150 alerts → 1 incident                                 │
│                                                            │
│ ROOT CAUSE ANALYSIS:                                       │
│ ┌────────────────────────────────────────────────────────┐│
│ │ Database connection pool exhausted                     ││
│ │ payments-db max_connections reached                    ││
│ │ Confidence: 87%                                        ││
│ └────────────────────────────────────────────────────────┘│
│                                                            │
│ SUGGESTED ACTIONS:                                         │
│ 1. Scale database connections                              │
│ 2. Review connection leak in payment-service               │
│ 3. Enable connection pooling                               │
│                                                            │
│ RELATED DEPLOYMENTS:                                       │
│ • payment-service v2.3.1 deployed 15 min ago              │
│                                                            │
│ On-call engineer: 😌 Clear next steps                      │
└────────────────────────────────────────────────────────────┘
```

### NRQL Anomaly Detection

```sql
-- Anomaly detection with NRQL
-- Find metrics that deviate from their baseline

-- Basic anomaly detection
SELECT
  average(duration) as 'Avg Duration',
  percentile(duration, 99) as 'P99',
  anomaly(duration, 3) as 'Anomaly Score'
FROM Transaction
WHERE appName = 'payment-service'
FACET name
SINCE 1 hour ago

-- Forecast with confidence bands
SELECT
  average(duration) as 'Actual',
  predictor(duration, 24 HOURS) as 'Predicted'
FROM Transaction
WHERE appName = 'payment-service'
SINCE 7 days ago
UNTIL 24 hours from now

-- Automatic baseline comparison
SELECT
  average(duration) as 'Current',
  compare with 1 week ago as 'Last Week'
FROM Transaction
WHERE appName = 'payment-service'
FACET name
SINCE 1 hour ago
```

---

## Splunk ITSI

Splunk IT Service Intelligence provides **service-level AI** for enterprise environments.

### ITSI Architecture

```
SPLUNK ITSI ARCHITECTURE
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                     SPLUNK ITSI                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SERVICE MODELING                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Business Services ─▶ Application Services ─▶ Entities │  │
│  │                                                       │  │
│  │ ┌─────────┐    ┌─────────┐    ┌─────────┐           │  │
│  │ │E-Commerce    │Checkout │    │payment- │           │  │
│  │ │Platform │────│Service  │────│service  │           │  │
│  │ └─────────┘    └─────────┘    │-pod-1   │           │  │
│  │                               └─────────┘           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  KPI INTELLIGENCE                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • Adaptive thresholds (learns normal behavior)        │  │
│  │ • Anomaly detection per KPI                          │  │
│  │ • Predictive health scoring                          │  │
│  │ • Service health aggregation                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  EVENT ANALYTICS                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • Notable event correlation                          │  │
│  │ • Episode creation (group related events)            │  │
│  │ • Multi-KPI anomaly detection                        │  │
│  │ • Service health prediction                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### ITSI Adaptive Thresholds

```spl
# SPL search with ITSI predictive analytics
| mstats avg(cpu.percent) as cpu
  WHERE index=itsi_summary service="payment-service"
  span=5m
| predict cpu algorithm=LLP5 holdback=0 future_timespan=24
| eval anomaly=if(cpu > upper95, 1, 0)
| where anomaly=1
| table _time, cpu, predicted_cpu, upper95

# Service health prediction
| inputlookup itsi_service_health_history
| where service_name="Payment Platform"
| timechart span=1h avg(health_score) as current_health
| predict current_health algorithm=LLP holdback=24
| eval health_risk=if(predicted_current_health < 0.7, "HIGH",
                     if(predicted_current_health < 0.85, "MEDIUM", "LOW"))
```

---

## Platform Comparison

| Feature | Datadog Watchdog | Dynatrace Davis | New Relic AI | Splunk ITSI |
|---------|------------------|-----------------|--------------|-------------|
| **Approach** | Statistical | Deterministic | ML Hybrid | Service-centric |
| **Auto-discovery** | Metrics only | Full stack | Partial | Manual/Discovery |
| **Root Cause** | Correlation | Causation | Correlation | Service chain |
| **Configuration** | Zero config | Minimal | Moderate | Significant |
| **Best For** | Cloud-native | Enterprise full-stack | APM-heavy | Log-heavy |
| **Deployment** | SaaS | SaaS/Managed | SaaS | On-prem/Cloud |

### Decision Matrix

```
WHICH PLATFORM AI TO USE?
────────────────────────────────────────────────────────────────

"I need zero-config anomaly detection"
└──▶ Datadog Watchdog
     • Works on all metrics automatically
     • No ML expertise needed
     • Fast time to value

"I need causation, not just correlation"
└──▶ Dynatrace Davis
     • Full-stack auto-discovery
     • Deterministic root cause
     • Best for complex enterprise environments

"I need to reduce alert noise dramatically"
└──▶ New Relic Applied Intelligence
     • Strong incident correlation
     • Good noise reduction
     • Workflow automation

"I have significant Splunk investment"
└──▶ Splunk ITSI
     • Integrates with existing Splunk
     • Service-level intelligence
     • Good for log-heavy environments
```

---

## Common Mistakes

| Mistake | Impact | Solution |
|---------|--------|----------|
| Ignoring platform AI | Missing valuable insights | Enable and configure AI features |
| Not tuning baselines | False positives | Let AI learn for 2+ weeks before alerting |
| Over-alerting on AI | Alert fatigue | Start with high-severity only |
| Expecting perfection | Disappointment | AI augments humans, doesn't replace |
| Duplicate tooling | Wasted spend | Inventory existing capabilities first |

---

## Quiz

Test your understanding of observability AI features:

### Question 1
What makes Dynatrace Davis different from correlation-based AI?

<details>
<summary>Show Answer</summary>

Davis uses **causation-based analysis** through Smartscape topology mapping. Rather than just saying "A and B happened together" (correlation), Davis can determine "A caused B because of dependency chain X → Y → Z" (causation). This deterministic approach provides more accurate root cause identification.
</details>

### Question 2
How does Datadog Watchdog detect anomalies without configuration?

<details>
<summary>Show Answer</summary>

Watchdog automatically:
1. **Monitors all metrics** submitted to Datadog
2. **Builds baselines** using historical data
3. **Detects deviations** considering seasonality (daily/weekly patterns)
4. **Correlates anomalies** across related metrics
5. **Creates stories** grouping related issues with root cause analysis

No user configuration is required—it works on every metric by default.
</details>

### Question 3
What is the main benefit of New Relic Applied Intelligence for on-call engineers?

<details>
<summary>Show Answer</summary>

**Noise reduction** is the primary benefit. Applied Intelligence:
- Correlates related alerts into single incidents
- Reduces 150 alerts to 1 actionable incident
- Provides suggested root cause and actions
- Routes to the right team automatically

This prevents alert fatigue and accelerates response time.
</details>

### Question 4
When should you use Splunk ITSI over other platforms?

<details>
<summary>Show Answer</summary>

Use Splunk ITSI when:
1. **Heavy Splunk investment** — Already using Splunk for logs
2. **Service-level monitoring** — Need business service health scores
3. **Enterprise IT** — Complex service dependencies to model
4. **On-prem requirements** — Cannot use SaaS platforms
5. **Log-centric** — Primary data source is logs, not metrics
</details>

---

## Hands-On Exercise

### Objective
Evaluate observability AI features using free trials or documentation.

### Exercise: Platform AI Feature Assessment

Since observability platforms require accounts and data, this exercise focuses on research and evaluation.

**Step 1: Research Watchdog**

Visit Datadog's Watchdog documentation and answer:
1. What data sources does Watchdog analyze?
2. How long does Watchdog need to establish baselines?
3. What is a "Watchdog Story"?

**Step 2: Research Davis**

Visit Dynatrace's Davis AI documentation and answer:
1. What is Smartscape and how does Davis use it?
2. What's the difference between "Problems" and "Alerts"?
3. How does Davis handle problem noise reduction?

**Step 3: Create Comparison Matrix**

Fill out this matrix for your environment:

```
| Feature                    | Your Priority | Best Platform |
|----------------------------|---------------|---------------|
| Zero-config detection      |               |               |
| Full-stack visibility      |               |               |
| Log analysis              |               |               |
| Trace correlation         |               |               |
| Noise reduction           |               |               |
| Root cause accuracy       |               |               |
| On-prem option            |               |               |
| Cost                      |               |               |
```

### Success Criteria
- [ ] Documented Watchdog capabilities
- [ ] Documented Davis capabilities
- [ ] Completed platform comparison matrix
- [ ] Identified best fit for your environment

---

## Key Takeaways

1. **Built-in AI is valuable** — Don't build what's already included in your platform
2. **Zero-config is real** — Watchdog and Davis work without configuration
3. **Causation beats correlation** — Davis's deterministic approach provides better RCA
4. **Noise reduction is measurable** — 80%+ reduction is achievable
5. **Platform lock-in is real** — AI features increase switching costs

### Feature Summary

| Platform | Killer Feature |
|----------|----------------|
| **Datadog** | Zero-config Watchdog on all metrics |
| **Dynatrace** | Causation-based Davis with Smartscape |
| **New Relic** | Incident correlation and noise reduction |
| **Splunk** | Service health scoring with KPI intelligence |

---

## Further Reading

### Official Documentation
- [Datadog Watchdog](https://docs.datadoghq.com/watchdog/) — Watchdog documentation
- [Dynatrace Davis](https://www.dynatrace.com/platform/artificial-intelligence/) — Davis AI overview
- [New Relic Applied Intelligence](https://docs.newrelic.com/docs/alerts-applied-intelligence/applied-intelligence/incident-intelligence/get-started-incident-intelligence/) — Applied Intelligence docs
- [Splunk ITSI](https://docs.splunk.com/Documentation/ITSI/latest/) — ITSI documentation

### Comparison Resources
- [Gartner Magic Quadrant for APM and Observability](https://www.gartner.com/reviews/market/application-performance-monitoring-and-observability)
- [CNCF Observability Landscape](https://landscape.cncf.io/card-mode?category=observability-and-analysis)

---

## Summary

Observability platforms have evolved beyond data collection into intelligent analysis engines. Rather than building custom AI, leverage the built-in capabilities of platforms like Datadog Watchdog, Dynatrace Davis, New Relic Applied Intelligence, and Splunk ITSI. Each has strengths: Watchdog for zero-config detection, Davis for causation-based RCA, Applied Intelligence for noise reduction, and ITSI for service-level intelligence. Evaluate based on your existing investments and requirements.

---

## Next Module

Continue to [Building Custom AIOps](module-10.4-building-custom-aiops/) to learn how to build your own AIOps pipelines when platform AI isn't enough.

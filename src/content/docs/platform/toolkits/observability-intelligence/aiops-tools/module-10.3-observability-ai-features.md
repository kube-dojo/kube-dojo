---
qa_pending: true
title: "Module 10.3: Observability AI Features"
slug: platform/toolkits/observability-intelligence/aiops-tools/module-10.3-observability-ai-features
sidebar:
  order: 4
---

# Module 10.3: Observability AI Features

> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 50-65 minutes

## Prerequisites

Before starting this module, you should be comfortable reading service dashboards, alert timelines, logs, traces, and basic dependency maps.
You do not need to be a data scientist, but you do need enough observability background to judge whether an AI explanation is plausible.
If you have not recently reviewed observability fundamentals, revisit the observability toolkit modules before treating platform AI as an incident-response tool.

- [AIOps Discipline](/platform/disciplines/data-ai/aiops/) - Conceptual foundation for operational machine learning and automation.
- [Observability Toolkit](/platform/toolkits/observability-intelligence/observability/) - Metrics, logs, traces, dashboards, and alerting patterns.
- Basic understanding of Datadog, Dynatrace, New Relic, Splunk, Grafana, or similar observability platforms.
- Familiarity with Kubernetes services, deployments, pods, and resource limits on Kubernetes 1.35 or newer.

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** whether an observability AI feature is explaining a symptom, a correlated event, or a defensible root cause.
- **Configure** AI-assisted detection and alert enrichment patterns so they reduce noise without hiding urgent incidents.
- **Debug** an AI-generated incident summary by tracing evidence from anomaly to dependency graph to operational action.
- **Compare** Datadog Watchdog, Dynatrace Davis, New Relic Applied Intelligence, Splunk ITSI, Elastic ML, and Grafana AI-assisted features against real platform requirements.
- **Design** a human-in-the-loop operating model that turns AI suggestions into trusted, auditable incident-response decisions.

## Why This Module Matters

A staff engineer is paged at 02:10 because checkout latency has crossed the customer-facing SLO for the third time in a week.
The observability platform says an AI assistant has found the probable cause, but the summary points to a database pool, a recent deployment, and a Kubernetes node restart.
The engineer has to decide whether to trust the recommendation, roll back the deployment, scale a service, or keep digging while customers are still failing checkout.

This is the real tension behind observability AI.
The value is not that a vendor can put an "AI" label on an alert screen; the value is that a tired human can move from raw telemetry to a safer action faster.
When the AI feature is grounded in topology, baselines, service ownership, and recent changes, it can shorten the reasoning loop.
When it is treated as an oracle, it can amplify confusion and create a second stream of noisy output that responders must manually disprove.

Senior platform teams therefore evaluate observability AI as an operating capability, not as a novelty feature.
They ask what evidence the platform used, how it grouped symptoms, where it may be blind, how humans can correct it, and whether the resulting workflow improves the next incident.
This module teaches that evaluation path: start with the telemetry, inspect the model's reasoning, act in a controlled way, and feed the result back into the system.

## Core Content

### 1. What Observability AI Actually Does

Observability AI is a set of features that helps a platform notice unusual behavior, connect related signals, and suggest likely explanations.
The term is broad enough to include statistical anomaly detection, machine-learning baselines, topology-aware root cause analysis, natural-language query assistants, incident grouping, and automated runbook suggestions.
The important question is not whether the feature uses a fashionable model; the important question is whether it improves the quality and speed of operational decisions.

A useful mental model is to separate detection, correlation, causation, and action.
Detection asks whether something changed in a meaningful way.
Correlation asks which signals changed around the same time or in the same service boundary.
Causation asks whether a dependency relationship makes one change a credible cause of another.
Action asks what a responder should do next, how risky that action is, and how to verify the result.

```ascii
OBSERVABILITY AI DECISION CHAIN
-----------------------------------------------------------------------

  raw telemetry          interpreted evidence          operational move
  -------------          --------------------          ----------------

  metrics        ----\
  logs            ----> [detect anomaly] ----> [group signals] ----\
  traces          ----/                                             |
  events          ----------------------------------------------\   |
  deployments     -----------------------------------------------\  |
  topology map    ------------------------------------------------> [explain]
  ownership map   -----------------------------------------------/  |
  runbooks        ----------------------------------------------/   |
                                                                      v
                                                               [act and verify]

  The strongest systems keep the evidence path visible from telemetry to action.
```

The first senior-level skill is to avoid treating every AI output as the same kind of claim.
"Latency is unusual" is a detection claim.
"Latency and error rate changed together after a deployment" is a correlation claim.
"The checkout failures are caused by payment-service connection exhaustion because checkout depends on payment and payment depends on the database pool" is a causation claim.
Each claim needs a different level of evidence before you let it change production behavior.

| AI Claim Type | What The Platform Is Saying | Evidence You Should Expect | Safe First Response |
|---|---|---|---|
| Detection | A signal is outside its normal range or pattern. | Baseline window, seasonality model, current deviation, affected scope. | Inspect whether the signal maps to user impact or a known maintenance window. |
| Correlation | Several changes happened close together or share tags. | Shared service, host, trace span, deployment event, or time window. | Check whether the grouped signals describe one incident or several unrelated events. |
| Causation | One entity likely caused downstream symptoms. | Dependency path, ordering, resource event, topology, and service impact. | Validate the dependency path before rolling back, scaling, or changing limits. |
| Recommendation | A remediation may reduce impact. | Runbook link, confidence rationale, blast-radius warning, verification query. | Execute the smallest reversible action and verify with independent telemetry. |

A common beginner mistake is to ask, "Which tool has the best AI?"
A better platform-engineering question is, "Which tool has the best evidence for the decisions my responders need to make?"
A payment platform with strong distributed traces may benefit from topology-aware causation.
A log-heavy enterprise estate may benefit more from service health scoring and event correlation.
A small cloud-native team may get the most value from zero-configuration anomaly detection that works without a dedicated operations analytics group.

> **Stop and think:** Your platform reports that checkout latency, database CPU, and a payment deployment all changed within the same ten-minute window.
> Which of those facts is detection, which is correlation, and what additional evidence would you need before calling the deployment the root cause?

This distinction matters because AI features often fail at the boundary between insight and authority.
A detection engine can be excellent at spotting unusual behavior while still being weak at explaining why it happened.
A natural-language assistant can summarize dashboards convincingly while still lacking permissions, topology, or complete telemetry.
The platform engineer's job is to design the workflow so the AI improves human reasoning instead of replacing it with an unreviewed guess.

### 2. The Built-In AI Landscape

Most major observability platforms now ship AI-assisted features directly inside their existing products.
Datadog emphasizes Watchdog for automatic anomaly detection, event correlation, and story generation.
Dynatrace emphasizes Davis AI for topology-aware causation across its Smartscape model.
New Relic emphasizes Applied Intelligence for incident correlation, noise reduction, and workflow automation.
Splunk ITSI emphasizes service modeling, KPI health scores, and enterprise event analytics.

```ascii
OBSERVABILITY PLATFORM AI LANDSCAPE
-----------------------------------------------------------------------

DATADOG                     DYNATRACE                   NEW RELIC
+-------------+            +-------------+            +-------------+
|  Watchdog   |            |  Davis AI   |            |  Applied    |
|             |            |             |            |Intelligence |
+-------------+            +-------------+            +-------------+
| Auto-detect |            | Topology    |            | Incident    |
| anomalies   |            | causation   |            | grouping    |
| Correlate   |            | Root cause  |            | Noise       |
| events      |            | Impact map  |            | reduction   |
| Forecasts   |            | Problems    |            | Workflows   |
+-------------+            +-------------+            +-------------+

SPLUNK                      ELASTIC                     GRAFANA
+-------------+            +-------------+            +-------------+
|    ITSI     |            |  ML Jobs    |            |  AI-Assisted|
|             |            |             |            |  Features   |
+-------------+            +-------------+            +-------------+
| Service     |            | Anomaly     |            | Query help  |
| health      |            | detection   |            | Forecasting |
| KPI scores  |            | Forecasting |            | Alert hints |
| Event       |            | Outliers    |            | Summaries   |
| analytics   |            | Jobs        |            |             |
+-------------+            +-------------+            +-------------+
```

The platforms overlap, but their center of gravity differs.
Datadog is often strongest when a team wants broad automatic detection across cloud-native telemetry with minimal setup.
Dynatrace is often strongest when the environment is complex enough that dependency topology and deterministic analysis are more valuable than simple time-window grouping.
New Relic is often strongest when the operational problem is too many alerts and not enough incident structure.
Splunk ITSI is often strongest where the organization already models business services and runs a large Splunk estate.

| Platform | Primary AI Pattern | Best-Fit Environment | Main Risk To Manage |
|---|---|---|---|
| Datadog Watchdog | Automatic anomaly detection and story generation. | Cloud-native teams with strong metric, log, and trace tagging. | Treating every story as page-worthy before severity rules mature. |
| Dynatrace Davis | Topology-aware causation and impact analysis. | Complex enterprise estates with full-stack instrumentation. | Trusting causation when topology coverage has gaps or stale ownership. |
| New Relic Applied Intelligence | Alert correlation, incident grouping, and workflow routing. | APM-heavy teams trying to reduce alert storms. | Over-grouping unrelated alerts into one incident and hiding parallel failures. |
| Splunk ITSI | Service health scoring and KPI-driven event analytics. | Log-heavy enterprise environments with mature service models. | Spending too much effort on model maintenance without action validation. |
| Elastic ML | Configurable anomaly jobs, outlier analysis, and forecasting. | Teams already centralizing search and log analytics in Elastic. | Creating many jobs without clear ownership or incident workflows. |
| Grafana AI-Assisted Features | Query help, summaries, forecasting, and assistant workflows. | Teams using Grafana as the observability front end across data sources. | Assuming a visualization assistant has the same evidence as the source platform. |

The platform comparison should not be read as a vendor ranking.
A mature team can use more than one platform, but each AI feature needs a clear job in the incident workflow.
If Watchdog detects anomalies, New Relic groups incidents, and a separate assistant summarizes runbooks, responders need to know which system is authoritative for paging, which is advisory for triage, and which is only a research helper.
Without that division of responsibility, adding AI increases coordination cost instead of reducing it.

A practical selection conversation starts with the operating pain.
If the team misses incidents because static thresholds do not follow traffic patterns, anomaly detection is the primary need.
If the team gets paged by hundreds of derivative alerts, incident grouping and deduplication are the primary need.
If the team spends most of its time proving which dependency caused customer impact, topology-aware causation becomes more valuable.
If service owners disagree about whether a business process is healthy, service health scoring may be the right abstraction.

```ascii
AI FEATURE SELECTION BY OPERATIONAL PAIN
-----------------------------------------------------------------------

  "We miss unusual behavior until customers complain"
          |
          v
  choose anomaly detection and seasonal baselines
          |
          v
  verify with user-impact metrics and alert precision

  "We get many alerts for one incident"
          |
          v
  choose incident correlation and event grouping
          |
          v
  verify with alert-to-incident compression and missed-parallel-failure review

  "We cannot find the root cause quickly"
          |
          v
  choose topology-aware causation and dependency analysis
          |
          v
  verify with dependency coverage and post-incident accuracy scoring

  "Executives need service-level health, not host graphs"
          |
          v
  choose service modeling and KPI health scores
          |
          v
  verify with business-service SLOs and runbook-backed actions
```

### 3. Datadog Watchdog: Automatic Detection With Guardrails

Datadog Watchdog continuously analyzes metrics, traces, logs, events, and service behavior to surface anomalies and related stories.
Its practical advantage is low setup cost: teams can get useful findings without hand-crafting a detection rule for every metric.
That makes it attractive for environments where service teams ship quickly and the platform team cannot tune every alert by hand.
The trade-off is that automatic detection still needs a response policy; otherwise, every unusual signal can become a new kind of noise.

```ascii
WATCHDOG ANALYSIS PATH
-----------------------------------------------------------------------

DATA COLLECTION                 ANALYSIS                  OUTPUT
+-------------+              +-------------+          +-------------+
|   Metrics   |------------->|             |          |             |
+-------------+              |  Watchdog   |          |  Stories    |
|    Logs     |------------->|   Engine    |--------->|             |
+-------------+              |             |          | Root cause  |
|   Traces    |------------->| Baselining  |          | Impact      |
+-------------+              | Detection   |          | Timeline    |
|   Events    |------------->| Correlation |          | Related     |
+-------------+              +-------------+          +-------------+

A strong Watchdog workflow connects stories to paging rules, ownership, and verification queries.
```

Watchdog-style anomaly detection works best when telemetry tags are consistent.
If the same service appears as `payment`, `payments`, `payment-service`, and `checkout-payment`, the AI engine has a harder time grouping the right evidence.
If deploy events are missing, the platform may notice the symptom but fail to connect it to the change that introduced the regression.
If SLO indicators are not available, the platform may overemphasize infrastructure anomalies that do not matter to users.

| Watchdog Detection Area | Useful When | Evidence To Inspect | Common Response |
|---|---|---|---|
| Metric anomalies | A metric deviates from learned behavior. | Baseline, current value, seasonality, affected tags, and duration. | Compare with SLO and traffic metrics before paging broadly. |
| APM anomalies | Latency, throughput, or error rate shifts in services. | Trace spans, endpoint facets, deployment markers, and error classes. | Identify the smallest service boundary that explains user impact. |
| Log anomalies | Error patterns or volume change unexpectedly. | Log pattern, sample events, host or pod tags, and related traces. | Link the pattern to a runbook or suppress known benign signatures. |
| Deployment tracking | A release is followed by changed behavior. | Deploy event, version tag, service metric change, and timing. | Consider rollback only after validating the change is causal, not coincidental. |
| Forecasting | A capacity metric trends toward a limit. | Forecast window, confidence band, growth rate, and recent changes. | Create capacity work with lead time instead of paging on long-term drift. |

A useful Watchdog alert is not simply "AI found something."
It should say which service is affected, why the finding is page-worthy, where the story can be inspected, and what the first verification step is.
The monitor can still be event-based, but the response path must be explicit enough for an engineer to act under pressure.
The following Terraform pattern shows the shape of an event alert that routes only high-value Watchdog stories for a production service.

```hcl
resource "datadog_monitor" "watchdog_payment_story" {
  name = "Watchdog story for payment service"
  type = "event alert"

  query = "events(\"source:watchdog service:payment-service env:prod\").rollup(\"count\").last(\"10m\") > 0"

  message = <<-EOT
    Watchdog found an anomaly story for payment-service in prod.

    First checks:
    1. Open the Watchdog story and confirm affected endpoints.
    2. Compare p95 latency, error rate, and checkout conversion.
    3. Check whether a deployment or resource event happened before the anomaly.
    4. Use the payment-service rollback runbook only if independent telemetry confirms impact.

    Runbook: https://runbooks.example.com/payment/watchdog-triage
    Owner: platform-payments
  EOT

  tags = [
    "service:payment-service",
    "env:prod",
    "team:platform-payments",
    "ai-feature:watchdog"
  ]

  priority = 3
}
```

The senior move is to route the AI story into a controlled triage path instead of sending it directly to every responder.
A story that is informative during office hours may not deserve a night page.
A story that matches customer impact and a recent deployment may deserve immediate attention.
This is why platform teams often start with notification-only mode, review precision for a few weeks, and then promote selected classes of AI findings into paging policy.

> **Active check:** Imagine Watchdog reports high CPU on `payment-service`, but checkout success rate and payment error rate are normal.
> Would you page the application team, create a ticket, or suppress the story? State the evidence that would change your decision.

A Watchdog finding can also be wrong for understandable reasons.
The platform may see a new traffic pattern after a marketing campaign and flag it as anomalous.
It may group events by time even though two incidents are independent.
It may miss causation when deployment metadata, Kubernetes labels, or ownership tags are incomplete.
These are not reasons to ignore the feature; they are reasons to build feedback into the operating model.

### 4. Dynatrace Davis: Causation Needs Topology

Dynatrace Davis is strongest when its topology model is strong.
The key idea is that root cause analysis should use dependency relationships, not just event timing.
If a database slowdown begins before a payment-service latency increase, and payment-service depends on that database, and checkout depends on payment-service, then the platform has a stronger argument than simple correlation.
This is why Dynatrace emphasizes Smartscape and entity relationships as part of its AI story.

```ascii
DAVIS AI ARCHITECTURE
-----------------------------------------------------------------------

+---------------------------------------------------------------------+
|                              SMARTSCAPE                             |
|      real-time dependency mapping across infrastructure and apps     |
|                                                                     |
|  +---------+     +---------+     +---------+     +-------------+    |
|  |  Host   |---->| Process |---->| Service |---->| User Action |    |
|  | Layer   |     | Layer   |     | Layer   |     | Layer       |    |
|  +---------+     +---------+     +---------+     +-------------+    |
|       |               |               |                |            |
|       +---------------+---------------+----------------+            |
|                       |                                            |
|                       v                                            |
|                +-------------+                                     |
|                |  Davis AI   |                                     |
|                | Causation   |                                     |
|                | Impact      |                                     |
|                | Problems    |                                     |
|                +-------------+                                     |
|                       |                                            |
|                       v                                            |
|                +-------------+                                     |
|                |  Problem    |                                     |
|                |  Record     |                                     |
|                +-------------+                                     |
+---------------------------------------------------------------------+
```

The phrase "deterministic AI" can sound like marketing unless you translate it into operational checks.
A deterministic root-cause claim should show the entity that failed, the downstream services it affected, the users or transactions that experienced impact, and the event order that makes the explanation plausible.
If any of those pieces are missing, the responder should lower confidence.
Topology-aware analysis is powerful, but only when instrumentation coverage and entity relationships are accurate.

| Davis Evidence Layer | What It Adds | What To Verify During An Incident |
|---|---|---|
| Entity topology | Shows which hosts, processes, services, and user actions depend on each other. | Confirm the impacted service path matches the current production architecture. |
| Event ordering | Shows which symptom appeared first and which symptoms followed. | Check whether the proposed cause started before downstream impact. |
| Impact analysis | Connects technical symptoms to users, requests, or business transactions. | Confirm the affected user actions match the page severity. |
| Problem grouping | Combines related events into a single operational problem. | Look for parallel failures that might have been grouped incorrectly. |
| Root-cause entity | Identifies the likely entity that started the chain. | Inspect logs, traces, resource events, and recent changes for that entity. |

Consider a Kubernetes payment incident.
A pod is OOMKilled after memory usage exceeds its limit.
The payment service loses capacity, checkout calls begin timing out, and user actions fail.
A topology-aware platform can present this as a cause-and-effect chain instead of showing four unrelated alerts.
That lets the responder verify the pod restart, compare it with memory limits, and decide whether to roll back, increase memory, or patch a leak.

```ascii
DAVIS-STYLE PROBLEM EXAMPLE
-----------------------------------------------------------------------

PROBLEM: Checkout response time degradation affecting real users
Status: OPEN | Impact: 860 users affected | Duration: 12 min

ROOT CAUSE ENTITY:
+-------------------------------------------------------------------+
| payment-service-pod-7d9f8 restarted after OOMKilled on node-3      |
+-------------------------------------------------------------------+

IMPACT CHAIN:
+-------------------------------------------------------------------+
| kubernetes-node-3                                                  |
|        |                                                           |
|        v                                                           |
| payment-service-pod-7d9f8                                          |
|        | OOMKilled after memory limit breach                       |
|        v                                                           |
| PaymentService                                                     |
|        | reduced capacity and request timeouts                     |
|        v                                                           |
| CheckoutService                                                    |
|        | degraded response for checkout flow                       |
|        v                                                           |
| /checkout user action                                              |
|        | failed or slow requests for affected users                 |
+-------------------------------------------------------------------+

RELATED EVENTS:
- 14:32:15 memory usage crossed pod limit
- 14:32:16 container terminated with OOMKilled
- 14:32:17 replacement container started
- 14:35:18 service recovered after warm-up
```

The same example also shows where AI can mislead.
If the pod restart happened after checkout latency increased, then the pod may be a symptom rather than the cause.
If the payment service has multiple replicas and traffic shifted cleanly, the OOMKilled event may not explain customer impact.
If checkout depends on another fraud-check service that is missing from topology, Davis may overstate the payment path.
Senior responders read the explanation as a hypothesis with evidence, not as a command.

Dynatrace problem notifications should therefore include impact and root-cause fields, but they should also point responders toward verification.
The following Monitoring as Code style configuration shows a notification pattern that routes production-critical problems and includes the entity fields responders need.
The exact schema may differ by Dynatrace account setup, but the operating intent is stable: route fewer, richer problem records with enough context to start triage.

```yaml
config:
  - notification: "davis-production-slack-notification"

notification:
  - name: "Davis Production Slack Notification"
    type: "SLACK"
    enabled: true
    url: "{{ .Env.SLACK_WEBHOOK_URL }}"
    channel: "#alerts-production"
    alertingProfile: "production-critical"
    payload: |
      {
        "text": "Davis problem detected in production",
        "attachments": [
          {
            "color": "danger",
            "fields": [
              {"title": "Problem", "value": "{ProblemTitle}", "short": true},
              {"title": "Impact", "value": "{ImpactedEntities}", "short": true},
              {"title": "Root Cause", "value": "{RootCauseEntity}", "short": false},
              {"title": "Verification", "value": "Check service impact, entity timeline, and latest deployment before acting.", "short": false}
            ]
          }
        ]
      }
```

The operational lesson is that Davis-style causation raises the ceiling on AI usefulness, but it also raises the importance of instrumentation hygiene.
Broken service naming, incomplete Kubernetes metadata, missing process relationships, and untagged deployments all weaken the reasoning path.
A platform team adopting topology-aware AI should treat telemetry taxonomy as production infrastructure.
The AI feature can only reason from the map it has.

### 5. New Relic Applied Intelligence: From Alert Storm To Incident

New Relic Applied Intelligence focuses heavily on turning alert noise into incidents that humans can manage.
This is a different problem from pure anomaly detection.
A team may already know something is wrong because every dashboard is red; the hard part is identifying which alerts describe the same failure, which team should own it, and which evidence matters first.
Incident intelligence is valuable when it compresses noise without deleting meaning.

```ascii
NEW RELIC APPLIED INTELLIGENCE FLOW
-----------------------------------------------------------------------

BEFORE INCIDENT INTELLIGENCE
+-------------------------------------------------------------------+
| Alert storm during payment degradation                             |
|                                                                   |
| CPU high on web-server-1                                           |
| CPU high on web-server-2                                           |
| Memory high on payment pod                                         |
| Response time high on /api/checkout                                |
| Response time high on /api/payment                                 |
| Error rate high on payment-service                                 |
| Error rate high on checkout-service                                |
| Many more derivative alerts from related symptoms                  |
+-------------------------------------------------------------------+

AFTER INCIDENT INTELLIGENCE
+-------------------------------------------------------------------+
| Incident: Payment system degradation                               |
|                                                                   |
| Grouped alerts: one operational incident                           |
| Probable cause: database connection pool exhaustion                 |
| Evidence: payment spans wait on database connection acquisition     |
| Related change: payment-service version v2.3.1 deployed recently   |
| Suggested first action: inspect connection pool and rollback path   |
+-------------------------------------------------------------------+
```

Grouping is useful only if the grouping logic reflects service boundaries.
Alerts from the same service, environment, deployment, and dependency chain often belong together.
Alerts from the same minute but unrelated business flows may not.
A correlation policy that groups too aggressively can hide parallel incidents; a policy that groups too weakly leaves responders in the same alert storm they had before.
The goal is not maximum compression; the goal is operational clarity.

| Correlation Input | Why It Matters | Poor Configuration Symptom | Better Practice |
|---|---|---|---|
| Service name | Keeps alerts aligned to ownership and dependency boundaries. | Alerts from unrelated apps collapse into one incident. | Enforce consistent `service` or `entity.name` tags across telemetry. |
| Environment | Prevents staging, canary, and production events from mixing. | Test failures appear inside production incidents. | Require `env` or equivalent attributes on alerts and deployments. |
| Time window | Controls how far apart related symptoms may be. | Old alerts attach to a new incident or related alerts split apart. | Tune windows using real incident timelines and postmortems. |
| Deployment metadata | Connects change events to symptoms. | The AI misses obvious release regressions. | Emit deployment markers from CI/CD for every production release. |
| Ownership | Routes the grouped incident to the team that can act. | Incidents bounce across teams during triage. | Maintain service catalog ownership and escalation metadata. |

Natural-language features can make this workflow faster, but they should remain evidence-driven.
A responder might ask, "What changed before payment latency increased?" or "Which endpoints contribute most to the error budget burn?"
The answer is useful if it cites underlying queries, spans, events, or dashboards.
It is less useful if it generates a fluent summary without exposing the telemetry path.
For operational work, transparency beats polish.

```sql
-- Example NRQL investigation pattern for a payment latency incident.
-- This query is intended for New Relic accounts that ingest Transaction events.

SELECT
  percentile(duration, 95) AS 'p95_seconds',
  percentage(count(*), WHERE error IS true) AS 'error_percentage'
FROM Transaction
WHERE appName = 'payment-service'
FACET name
SINCE 30 minutes ago
COMPARE WITH 1 hour ago
```

A good incident-intelligence policy also includes a review loop.
After each significant incident, responders should mark whether the grouping was helpful, whether the proposed cause was accurate, and whether the suggested action matched the eventual fix.
Those judgments should feed tag cleanup, policy tuning, runbook updates, and automation thresholds.
Without this loop, the platform may keep making the same plausible but unhelpful suggestion.

> **Stop and think:** Your alert-correlation policy grouped checkout errors, inventory timeouts, and a failed deployment into one incident.
> What evidence would convince you this is one incident, and what evidence would make you split it into separate investigations?

### 6. Splunk ITSI, Elastic ML, and Grafana AI-Assisted Workflows

Splunk ITSI approaches observability AI through service modeling and KPI health.
Instead of starting with a single metric anomaly, ITSI asks whether a business or technical service is healthy based on multiple indicators.
This is powerful in enterprise environments where services are made of many infrastructure, application, network, and dependency components.
It is also more maintenance-heavy because the service model and KPIs must reflect reality.

```ascii
SPLUNK ITSI SERVICE MODEL
-----------------------------------------------------------------------

+---------------------------------------------------------------------+
|                              SPLUNK ITSI                            |
|                                                                     |
|  BUSINESS SERVICE                                                   |
|  +---------------------------------------------------------------+  |
|  | E-Commerce Platform                                           |  |
|  |                                                               |  |
|  |  +----------------+       +----------------+                  |  |
|  |  | Checkout       | ----> | Payment        |                  |  |
|  |  | Service        |       | Service        |                  |  |
|  |  +----------------+       +----------------+                  |  |
|  |          |                         |                            |
|  |          v                         v                            |
|  |  +----------------+       +----------------+                  |  |
|  |  | Web Frontend   |       | Payment DB     |                  |  |
|  |  +----------------+       +----------------+                  |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
|  KPI HEALTH                                                         |
|  latency, error rate, throughput, queue depth, dependency failures   |
|                                                                     |
|  EVENT ANALYTICS                                                    |
|  notable event grouping, episode review, and service impact scoring |
+---------------------------------------------------------------------+
```

ITSI-style health scoring is especially useful when executives, support teams, and service owners need a shared language.
A service health score can express that checkout is degraded even if no single host is down.
However, a health score must be connected to action.
If a score drops but responders do not know which KPI drove it, which dependency changed, or which runbook applies, the score becomes a dashboard decoration rather than an operational tool.

Elastic ML provides a more configurable analytics approach.
Teams define anomaly detection jobs, forecasting jobs, and outlier analyses against data in Elastic.
This is useful when the team wants control over the job, data view, and detection logic.
The trade-off is ownership: every ML job needs someone to tune it, review false positives, and retire it when the underlying service changes.

Grafana's AI-assisted features usually sit closer to the operator interface.
They may help users write queries, summarize panels, explain alert history, or explore data across connected sources.
This is valuable because Grafana often spans Prometheus, Loki, Tempo, Mimir, Pyroscope, and third-party data sources.
The limitation is that an assistant in the visualization layer may not know everything the source systems know about topology, deployment events, or alert ownership.

| Tool Family | Strength | Senior-Level Use | Failure Mode |
|---|---|---|---|
| Splunk ITSI | Service modeling, KPI health, and enterprise event analytics. | Map business service health to actionable KPIs and ownership. | A beautiful health model that nobody maintains after reorgs or architecture changes. |
| Elastic ML | Configurable anomaly jobs and forecasting over indexed data. | Build targeted detection where the data and ownership are well understood. | Dozens of jobs with unclear responders, stale baselines, and no review loop. |
| Grafana AI-assisted features | Query help, summarization, and cross-source exploration. | Speed up investigation while keeping source queries visible. | Fluent summaries that responders accept without inspecting source evidence. |
| Custom AIOps pipeline | Full control over models, data, and automation. | Fill gaps that built-in tools cannot cover safely or economically. | Rebuilding vendor features without enough data, maintenance capacity, or governance. |

The safest pattern is to let each tool do the job it is structurally good at.
Use source platforms for detection when they have the best data.
Use topology-aware systems for causation when their dependency maps are trustworthy.
Use Grafana assistants for exploration when the operator needs fast query help across systems.
Use service health models when the business service is the right abstraction for decision-making.
Avoid turning every AI feature into an independent pager.

### 7. Worked Example: Debugging An AI Incident Summary

Now we will walk through a complete reasoning path before asking you to solve a similar problem in the hands-on exercise.
The scenario is a Kubernetes payment platform running on version 1.35 or newer.
An observability AI feature has generated an incident summary that says payment latency is probably caused by database connection pool exhaustion after a deployment.
Your task as the platform engineer is to validate the claim before recommending an action.

```ascii
WORKED INCIDENT TOPOLOGY
-----------------------------------------------------------------------

                         customer checkout
                                |
                                v
+----------------+      +----------------+      +----------------+
| web-frontend   | ---> | checkout-svc   | ---> | payment-svc    |
+----------------+      +----------------+      +----------------+
                                                        |
                                                        v
                                                +----------------+
                                                | payments-db    |
                                                +----------------+

Recent event:
- payment-svc version v2.3.1 deployed at 14:20
- AI incident summary created at 14:31
- checkout p95 latency crossed SLO at 14:34
```

The first step is to classify the AI claims.
"Payment latency increased" is a detection claim.
"Database connection waits increased around the same time" is a correlation claim.
"Deployment v2.3.1 caused a connection leak that exhausted the database pool" is a causation claim.
"Rollback payment-svc" is a recommendation.
Each layer needs stronger evidence than the previous one because the operational consequence becomes more serious.

| Claim In Summary | Claim Type | Evidence Found | Confidence |
|---|---|---|---|
| Payment p95 latency increased after 14:28. | Detection | Service latency panel shows p95 rose from 180 ms to 1.9 s. | High |
| Checkout errors increased after payment slowed. | Correlation | Checkout traces spend most failed span time inside payment calls. | High |
| Database connection acquisition time increased. | Correlation | Payment spans show wait time before database query execution. | Medium |
| Version v2.3.1 caused connection exhaustion. | Causation | Deployment occurred before the anomaly, and only new pods show leaked connections. | Medium-high |
| Roll back payment-svc immediately. | Recommendation | Prior version is healthy, rollback is tested, and error budget burn is high. | High if rollback blast radius is acceptable |

The second step is to look for counterevidence.
If database CPU was already saturated before the deployment, the deployment may have exposed an existing bottleneck rather than caused it.
If only one availability zone is affected, a node or network problem may be more likely than an application leak.
If a feature flag changed after the deployment, rolling back the binary may not remove the behavior.
A senior responder does not look for evidence that confirms the AI; they look for evidence that could disprove it.

The third step is to choose a reversible action.
If the platform shows high customer impact and the prior version is known healthy, rollback may be appropriate.
If the impact is limited and the issue is connection pool size, a temporary configuration change may be lower risk.
If the evidence is weak, the safest action may be to disable a feature flag or remove a canary from traffic while collecting more data.
The action should be small enough to verify quickly and safe enough to undo if the AI was wrong.

```ascii
WORKED RESPONSE DECISION
-----------------------------------------------------------------------

AI says: payment deployment caused database connection exhaustion

        |
        v
Is there user impact on checkout or payment SLO?
        |
        +-- no --> create ticket, keep observing, do not page broadly
        |
        +-- yes
             |
             v
Does evidence show the deployment started before the connection wait?
             |
             +-- no --> investigate database, node, and network paths first
             |
             +-- yes
                  |
                  v
Is rollback tested and lower risk than live patching?
                  |
                  +-- no --> apply smallest safe mitigation and verify
                  |
                  +-- yes --> roll back, watch p95 latency and error rate
```

The final step is to update the AI operating loop.
If the recommendation was right, capture which evidence made it trustworthy and link it to the runbook.
If it was wrong, record the missing signal or incorrect grouping.
If it was partially right, tune the policy so future incidents separate detection from action more clearly.
This is how teams move from "nobody trusts the AI" to "the AI is a useful junior analyst whose work we can audit."

### 8. Designing Trust, Feedback, and Governance

The hardest part of observability AI is not enabling the feature.
The hardest part is building enough trust that responders use it, without giving it enough unchecked authority to harm production.
Trust grows when the system is accurate, explainable, useful, and correctable.
A black-box answer that cannot be corrected will eventually be ignored, even if it is often right.

A practical trust model has four loops.
The evidence loop shows the telemetry behind every claim.
The decision loop maps each class of AI finding to a safe response policy.
The feedback loop lets humans mark findings as correct, wrong, noisy, or useful but not urgent.
The governance loop reviews automation scope, cost, privacy, and access control.
Skipping any loop turns AI into either shelfware or uncontrolled automation.

```ascii
HUMAN-IN-THE-LOOP TRUST MODEL
-----------------------------------------------------------------------

+------------------+       +------------------+       +------------------+
| Evidence Loop    | ----> | Decision Loop    | ----> | Action Loop      |
| telemetry,       |       | severity, owner, |       | runbook,         |
| topology, events |       | policy, risk     |       | rollback, verify |
+------------------+       +------------------+       +------------------+
          ^                                                     |
          |                                                     v
+------------------+       +------------------+       +------------------+
| Governance Loop  | <---- | Feedback Loop    | <---- | Incident Review  |
| access, privacy, |       | correct, noisy,  |       | outcome, timing, |
| cost, automation |       | stale, missing   |       | missed evidence  |
+------------------+       +------------------+       +------------------+
```

Governance matters because observability data is sensitive.
Logs may contain customer identifiers, traces may reveal business workflows, and incident summaries may expose security-relevant architecture details.
AI features that send data to vendor-hosted assistants or large language models require review by security, privacy, and legal stakeholders.
Even when data stays inside the observability platform, access controls should prevent broad query assistants from revealing telemetry a user could not otherwise inspect.

| Governance Question | Why It Matters | Example Control |
|---|---|---|
| What telemetry can the AI feature read? | The assistant may summarize sensitive logs, traces, or deployment data. | Scope access by role, account, environment, and data classification. |
| Can the AI feature trigger actions? | Automation can create incidents, pages, rollbacks, or tickets. | Start read-only, then require approval for production changes. |
| How are recommendations audited? | Post-incident review needs to know what the system suggested and why. | Store AI summaries, evidence links, human decisions, and outcomes. |
| How are false positives corrected? | Repeated wrong findings train responders to ignore the system. | Add feedback buttons and review them during weekly operations meetings. |
| How is cost controlled? | AI features can increase platform spend through data volume or premium tiers. | Track feature usage, alert value, incident reduction, and duplicate tooling. |

A mature rollout usually starts in advisory mode.
The team enables AI findings, routes them to a low-risk channel, reviews precision, and documents examples where the finding did or did not help.
Next, the team promotes high-confidence classes into incident enrichment, where AI evidence appears inside pages but does not create new pages by itself.
Only after the team has measured accuracy and runbook quality should selected AI findings create pages or trigger automation.

> **Active check:** Your team wants the AI assistant to open rollback pull requests automatically when it sees a deployment-related incident.
> What controls would you require before allowing that behavior in production, and what evidence would still require a human approval step?

### 9. Platform Comparison and Selection Patterns

A selection matrix should combine technical capability with operating constraints.
The most advanced root-cause engine may be a poor choice if the team cannot instrument dependencies well enough to feed it.
The easiest anomaly detector may be a poor choice if the main pain is cross-service ownership.
The cheapest feature may be expensive in practice if it creates alert noise, duplicates tooling, or requires manual investigation for every finding.

| Requirement | Datadog Watchdog | Dynatrace Davis | New Relic Applied Intelligence | Splunk ITSI | Elastic ML | Grafana AI-Assisted Features |
|---|---|---|---|---|---|---|
| Zero-configuration detection | Strong | Strong with full instrumentation | Moderate | Limited | Limited | Limited |
| Topology-aware causation | Moderate | Strong | Moderate | Moderate when modeled | Limited | Depends on data source |
| Alert noise reduction | Moderate | Strong problem grouping | Strong | Strong episode grouping | Limited by job design | Limited |
| Service health scoring | Moderate | Strong impact views | Moderate | Strong | Custom | Dashboard-driven |
| Log-heavy analytics | Strong | Moderate | Moderate | Strong | Strong | Strong when backed by Loki or Elastic |
| On-prem or controlled deployment | Limited | Available in managed patterns | Limited | Strong | Strong | Strong depending on stack |
| Natural-language exploration | Emerging | Strong in platform context | Strong | Varies by deployment | Varies | Strong for query assistance |
| Custom detection control | Moderate | Moderate | Moderate | Strong | Strong | Depends on source |

The decision should be tied to a specific incident workflow.
For example, a platform team might keep Datadog Watchdog for automatic detection, use service catalog ownership for routing, and rely on runbooks for action.
Another team might standardize on Dynatrace because the primary outage cost is slow root-cause analysis across legacy and Kubernetes systems.
A Splunk-heavy enterprise might invest in ITSI because business-service health is more valuable than adopting another APM platform.
The correct answer depends on what decision the AI must improve.

```ascii
SELECTION WORKFLOW
-----------------------------------------------------------------------

Start with the operational pain
        |
        v
Is the pain missed anomalies?
        |
        +-- yes --> prioritize automatic detection and baseline quality
        |
        +-- no
             |
             v
Is the pain alert storms?
             |
             +-- yes --> prioritize correlation, grouping, and routing
             |
             +-- no
                  |
                  v
Is the pain slow root cause analysis?
                  |
                  +-- yes --> prioritize topology, traces, and causation
                  |
                  +-- no
                       |
                       v
Is the pain business-service visibility?
                       |
                       +-- yes --> prioritize service models and KPI health
                       |
                       +-- no --> improve telemetry hygiene before buying more AI
```

The best teams also evaluate the "exit cost" of platform AI.
AI features often become sticky because they encode policies, baselines, incident history, and runbooks.
That stickiness is not automatically bad; reliable operational memory has value.
But it should be intentional.
Before adopting a feature deeply, decide which parts are portable, which are vendor-specific, and which are worth the lock-in because they reduce real incident cost.

## Did You Know?

- **Topology quality often matters more than model sophistication**: A simple dependency-aware rule with accurate service relationships can outperform a sophisticated model that sees incomplete or inconsistent telemetry.
- **Alert compression has a failure mode**: Reducing many alerts into one incident is helpful only when the grouped alerts share a cause; excessive compression can hide simultaneous independent failures.
- **Natural-language observability is safest when it cites queries**: An assistant that shows the PromQL, NRQL, SPL, trace filter, or dashboard behind its answer is easier to audit during an incident.
- **Human feedback is operational data**: Marking AI findings as correct, wrong, noisy, or useful creates a training and governance signal for future tuning, even when the vendor model itself is not retrained by your team.

## Common Mistakes

| Mistake | Impact | Better Approach |
|---|---|---|
| Enabling every AI alert as a page on day one. | Responders get a new source of noise before accuracy, severity, and ownership are understood. | Start in advisory mode, review precision, then promote only high-value findings into paging paths. |
| Treating correlation as causation during rollback decisions. | Teams roll back healthy deployments because unrelated symptoms happened in the same time window. | Require dependency evidence, event order, and service-impact validation before acting on root-cause claims. |
| Ignoring telemetry taxonomy and service tags. | AI features group the wrong entities or fail to connect symptoms to owners and deployments. | Standardize service names, environments, versions, owners, and deployment events across telemetry sources. |
| Letting natural-language answers hide source evidence. | Responders accept fluent summaries that may not reflect the actual metrics, logs, or traces. | Require links to queries, dashboards, trace examples, and event timelines for incident-critical answers. |
| Building custom AIOps before inventorying built-in features. | The platform team spends months recreating detection, grouping, or forecasting already available in existing tools. | Map current platform capabilities first, then build only for gaps with clear operating value. |
| Over-grouping alerts to chase high noise-reduction numbers. | Parallel failures disappear inside one incident, slowing diagnosis and assigning the wrong owner. | Tune grouping with post-incident examples and measure missed separate incidents, not only compression ratio. |
| Skipping feedback after incidents. | The same false positives, stale ownership, and weak recommendations recur until responders stop trusting the feature. | Add human feedback fields to incident review and convert findings into policy, tag, and runbook updates. |
| Allowing AI-triggered remediation without blast-radius controls. | An incorrect recommendation can restart services, roll back releases, or suppress alerts during a real outage. | Keep production actions approval-gated until evidence quality, runbook safety, and rollback verification are proven. |

## Quiz

### Question 1

Your team enabled automatic anomaly detection for a payment platform.
At 09:10, the AI feature reports that database CPU is thirty percent above its usual weekday baseline, but payment success rate, checkout latency, and error budget burn are normal.
The product manager asks whether this should page the payment on-call engineer immediately.
What decision would you make, and what evidence would you inspect before changing the policy?

<details>
<summary>Show Answer</summary>

This should usually start as a ticket or advisory notification, not an immediate page, because the signal does not yet connect to user impact.
You should inspect the baseline window, seasonality, current traffic, database query latency, payment-service latency, and any recent capacity or maintenance events.
If the CPU increase is sustained, approaching a hard limit, or correlated with rising user-impact metrics, the policy can escalate.
The key reasoning is that anomaly detection alone is a detection claim, while paging should be tied to impact, urgency, or a credible path to imminent impact.
</details>

### Question 2

A Dynatrace-style problem says checkout failures are caused by `payment-service-pod-9a12` being OOMKilled.
When you inspect the timeline, checkout errors started five minutes before the pod restart, and traces show fraud-check calls timing out before payment calls.
How should you handle the AI root-cause recommendation?

<details>
<summary>Show Answer</summary>

You should lower confidence in the recommendation and treat the OOMKilled pod as a possible symptom or secondary failure rather than the root cause.
The event order contradicts the proposed causation because checkout errors began before the pod restart.
The trace evidence also points toward fraud-check as an earlier dependency problem.
A good response is to split the investigation, inspect fraud-check latency and dependencies, and avoid rolling back payment-service solely because the AI summary named that pod.
</details>

### Question 3

New Relic Applied Intelligence groups 120 alerts into one incident named "Checkout degradation."
The grouped alerts include production checkout errors, staging inventory test failures, and a canary deployment warning from a different service.
What policy changes would you make to improve the grouping?

<details>
<summary>Show Answer</summary>

The grouping policy is too broad because it mixed environments and likely mixed ownership boundaries.
You should require environment attributes such as `env=prod`, service or entity names, and possibly deployment identifiers before alerts can join the same incident.
You should also exclude staging from production incident grouping and tune the time window using real incident examples.
The goal is not to minimize incident count at any cost; the goal is to group alerts that represent one operational problem with one likely owner.
</details>

### Question 4

A Grafana assistant answers, "The outage was caused by a bad payment deployment," but it does not show the PromQL query, Loki log query, trace filter, or deployment event it used.
The incident commander wants to announce rollback immediately based on the assistant summary.
What should you do next?

<details>
<summary>Show Answer</summary>

You should ask for or manually gather the source evidence before recommending rollback.
A natural-language summary without visible queries is not enough for a production action.
You should inspect payment error rate, latency, trace spans, deployment markers, and any feature flag or dependency changes around the incident window.
If those independent signals confirm the deployment introduced user impact and rollback is tested, rollback may be appropriate.
The assistant can guide investigation, but it should not be the sole authority for a risky production decision.
</details>

### Question 5

Splunk ITSI shows the "E-Commerce Platform" health score dropping from healthy to degraded, but the on-call engineer cannot tell which KPI drove the score.
The service owner says the score is useless and wants it removed from the incident channel.
How would you improve the design instead of abandoning service health scoring?

<details>
<summary>Show Answer</summary>

The health score needs to expose its contributing KPIs and connect each unhealthy KPI to an action path.
You should configure the incident message or dashboard to show which latency, error, dependency, queue, or infrastructure indicators drove the score.
Each critical KPI should have an owner, a threshold or adaptive baseline rationale, and a runbook link.
Service health scoring is valuable when it summarizes complexity while preserving drill-down; it becomes useless when it hides the evidence behind a single number.
</details>

### Question 6

Your platform team wants to build a custom AIOps pipeline because the vendor AI feature "does not understand our business."
During discovery, you find that the existing observability platform already supports deployment markers, service ownership tags, anomaly stories, and incident grouping, but most teams have not configured those fields.
What should you recommend first?

<details>
<summary>Show Answer</summary>

You should recommend improving telemetry hygiene and built-in feature configuration before building a custom AIOps pipeline.
The current failure is not necessarily a missing model; it is missing context such as deployment markers, ownership tags, and consistent service metadata.
A custom system would likely suffer from the same missing data while adding maintenance cost.
After the built-in features are configured and measured, the team can identify remaining gaps that justify custom development.
</details>

### Question 7

An AI feature has correctly identified three recent payment incidents, but responders still ignore it because older alerting systems trained them to distrust automated recommendations.
You are asked to design a trust-building rollout.
What concrete steps would you include?

<details>
<summary>Show Answer</summary>

Start by keeping the feature advisory while collecting accuracy examples in weekly operations review.
For each significant finding, record whether the AI detected the right symptom, grouped the right signals, named the right likely cause, and suggested a useful next action.
Add explanation fields and links to the evidence used by the AI, then connect high-confidence findings to runbooks.
Only after responders see repeated, auditable value should selected findings move into paging or automation.
Trust is built through visible evidence, correction mechanisms, and measured outcomes, not through a launch announcement.
</details>

## Hands-On Exercise

### Objective

You will simulate an observability AI triage workflow without needing a paid SaaS account.
The exercise gives you incident evidence, asks you to classify AI claims, then has you run a small local analyzer that produces a recommendation.
You will then change the evidence, rerun the analyzer, and decide whether the recommendation remains safe.
This creates the missing "Act" phase: you will not only research features, you will apply a policy, take a simulated remediation decision, and verify the outcome.

### Scenario

A Kubernetes 1.35 payment platform has a checkout incident.
An AI feature claims that a recent payment deployment caused database connection pool exhaustion.
Your job is to validate the claim, choose a simulated action, and verify whether the action improved the incident.
The analyzer is intentionally simple so you can inspect the logic; the learning goal is the operational reasoning, not machine-learning implementation.

### Step 1: Create The Local Incident Analyzer

Create a file named `aiops_triage_sim.py` with the following Python code.
The script uses only the Python standard library and can be run with `.venv/bin/python` from this repository if you are working inside KubeDojo.
It reads embedded incident data, scores evidence, recommends an action, and simulates the effect of that action.

```python
#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Action = Literal["observe", "ticket", "scale_pool", "rollback"]


@dataclass(frozen=True)
class IncidentEvidence:
    service: str
    user_impact: bool
    p95_latency_ms: int
    error_rate_percent: float
    deployment_minutes_before_anomaly: int | None
    db_connection_wait_ms: int
    pod_restarts: int
    traces_point_to_database: bool
    previous_version_healthy: bool


def score_root_cause(evidence: IncidentEvidence) -> int:
    score = 0

    if evidence.user_impact:
        score += 2

    if evidence.deployment_minutes_before_anomaly is not None:
        if 0 <= evidence.deployment_minutes_before_anomaly <= 30:
            score += 2
        elif evidence.deployment_minutes_before_anomaly > 30:
            score += 1

    if evidence.db_connection_wait_ms >= 500:
        score += 2

    if evidence.traces_point_to_database:
        score += 2

    if evidence.pod_restarts > 0:
        score -= 1

    if evidence.previous_version_healthy:
        score += 1

    return score


def recommend_action(evidence: IncidentEvidence) -> Action:
    score = score_root_cause(evidence)

    if not evidence.user_impact:
        return "ticket"

    if score >= 7 and evidence.previous_version_healthy:
        return "rollback"

    if evidence.db_connection_wait_ms >= 500 and evidence.traces_point_to_database:
        return "scale_pool"

    if evidence.error_rate_percent < 1.0:
        return "observe"

    return "ticket"


def simulate_action(evidence: IncidentEvidence, action: Action) -> dict[str, object]:
    if action == "rollback":
        return {
            "action": action,
            "expected_latency_ms": 240,
            "expected_error_rate_percent": 0.2,
            "verification": "p95 latency and error rate return near baseline after version rollback",
        }

    if action == "scale_pool":
        return {
            "action": action,
            "expected_latency_ms": 480,
            "expected_error_rate_percent": 0.8,
            "verification": "database wait falls, but deployment-related leak may continue",
        }

    if action == "ticket":
        return {
            "action": action,
            "expected_latency_ms": evidence.p95_latency_ms,
            "expected_error_rate_percent": evidence.error_rate_percent,
            "verification": "no immediate production change; review during business hours or normal triage",
        }

    return {
        "action": action,
        "expected_latency_ms": evidence.p95_latency_ms,
        "expected_error_rate_percent": evidence.error_rate_percent,
        "verification": "continue observing because user impact or confidence is not high enough",
    }


def print_decision(evidence: IncidentEvidence) -> None:
    score = score_root_cause(evidence)
    action = recommend_action(evidence)
    result = simulate_action(evidence, action)

    print(f"service={evidence.service}")
    print(f"user_impact={evidence.user_impact}")
    print(f"root_cause_score={score}")
    print(f"recommended_action={action}")
    print(f"expected_latency_ms={result['expected_latency_ms']}")
    print(f"expected_error_rate_percent={result['expected_error_rate_percent']}")
    print(f"verification={result['verification']}")


if __name__ == "__main__":
    incident = IncidentEvidence(
        service="payment-service",
        user_impact=True,
        p95_latency_ms=1900,
        error_rate_percent=6.4,
        deployment_minutes_before_anomaly=8,
        db_connection_wait_ms=850,
        pod_restarts=0,
        traces_point_to_database=True,
        previous_version_healthy=True,
    )

    print_decision(incident)
```

### Step 2: Run The Baseline Scenario

Run the analyzer and capture its output.
The script should recommend a rollback because user impact is present, the deployment happened shortly before the anomaly, traces point to database waits, and the previous version is known healthy.

```bash
.venv/bin/python aiops_triage_sim.py
```

Expected output shape:

```bash
service=payment-service
user_impact=True
root_cause_score=9
recommended_action=rollback
expected_latency_ms=240
expected_error_rate_percent=0.2
verification=p95 latency and error rate return near baseline after version rollback
```

Do not stop at reading the recommendation.
Classify each part of the evidence as detection, correlation, causation, or action.
This is the skill you need during real incidents: the AI can propose a path, but you must know which claims are strong enough to justify production change.

### Step 3: Create A Counterevidence Scenario

Modify only the incident data at the bottom of the script.
Change `pod_restarts` to `2`, change `deployment_minutes_before_anomaly` to `None`, and change `previous_version_healthy` to `False`.
This simulates a case where the deployment evidence is missing, pod instability exists, and rollback safety is unclear.
Run the script again and compare the recommendation.

```python
incident = IncidentEvidence(
    service="payment-service",
    user_impact=True,
    p95_latency_ms=1900,
    error_rate_percent=6.4,
    deployment_minutes_before_anomaly=None,
    db_connection_wait_ms=850,
    pod_restarts=2,
    traces_point_to_database=True,
    previous_version_healthy=False,
)
```

The correct learning outcome is not a specific vendor behavior.
The outcome is that weaker causation evidence should lead to a less aggressive action.
If the script recommends scaling the pool instead of rollback, explain why that is safer under uncertainty.
If you change the scoring logic, document which operational assumption you changed and why.

### Step 4: Add A No-User-Impact Scenario

Now change `user_impact` to `False`, reduce `error_rate_percent` to `0.1`, and keep the database wait high.
This simulates a platform AI finding that is technically real but not currently customer-impacting.
Run the script again and decide whether this belongs in a page, a ticket, or an observation channel.

```python
incident = IncidentEvidence(
    service="payment-service",
    user_impact=False,
    p95_latency_ms=700,
    error_rate_percent=0.1,
    deployment_minutes_before_anomaly=10,
    db_connection_wait_ms=650,
    pod_restarts=0,
    traces_point_to_database=True,
    previous_version_healthy=True,
)
```

A mature policy usually avoids paging on this scenario unless there is imminent risk.
You may create a ticket, notify the service channel, or attach it to capacity review.
The important point is that anomaly detection does not automatically equal emergency response.
This is how teams prevent AI features from recreating alert fatigue under a new label.

### Step 5: Design The Production Policy

Write a short policy for your team using the structure below.
The policy should decide which AI findings are advisory, which enrich existing incidents, and which can create a new page.
Make sure your rules mention user impact, evidence links, service ownership, and rollback safety.

```markdown
# Observability AI Response Policy

## Advisory Only
AI findings are advisory when they detect unusual behavior without user impact, imminent capacity risk, or a confirmed dependency path.

## Incident Enrichment
AI findings enrich an incident when a human-triggered or SLO-triggered page already exists and the AI provides evidence links, topology context, or likely related changes.

## Page-Creating Findings
AI findings may create a page only when user impact is present, ownership is known, the finding includes source evidence, and the recommended first action has a runbook.

## Production Action Approval
Rollback, scaling, traffic shifting, or alert suppression requires human approval until the feature has demonstrated sustained accuracy in incident review.
```

### Step 6: Compare Vendor Features Against Your Policy

Use the comparison table from the module and fill in the matrix for your current or target observability platform.
Do not mark a feature as "good" only because it exists.
Mark it as good only if it produces the evidence your policy requires.
This is the difference between feature evaluation and operational evaluation.

| Policy Need | Evidence Required | Current Platform Support | Gap To Close |
|---|---|---|---|
| Advisory anomaly detection | Baseline, deviation, affected service, and environment. | | |
| Incident enrichment | Related traces, logs, events, deployments, and topology. | | |
| Page creation | User impact, owner, severity, and runbook. | | |
| Production action | Reversible action, approval path, and verification query. | | |
| Feedback loop | Human accuracy rating and post-incident review field. | | |

### Success Criteria

- [ ] You ran the local analyzer with the baseline incident and explained why rollback was recommended.
- [ ] You created a counterevidence scenario and explained why the recommended action became less aggressive.
- [ ] You created a no-user-impact scenario and chose a non-paging response unless you documented imminent risk.
- [ ] You classified at least four AI claims as detection, correlation, causation, or action.
- [ ] You wrote an observability AI response policy that separates advisory findings, incident enrichment, page creation, and production actions.
- [ ] You completed the platform comparison matrix using evidence requirements rather than vendor marketing labels.
- [ ] You identified one telemetry hygiene improvement that would make AI recommendations more trustworthy in your environment.
- [ ] You identified one governance control required before any AI-triggered remediation could run in production.

## Next Module

Continue to [Building Custom AIOps](../module-10.4-building-custom-aiops/) to learn how to build your own AIOps pipelines when built-in platform AI is not enough.

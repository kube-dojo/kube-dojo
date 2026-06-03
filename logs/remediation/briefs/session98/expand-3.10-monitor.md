Expand the module at: src/content/docs/cloud/azure-essentials/module-3.10-monitor.md

Current body_words ≈ 1369 — needs to reach >= 5000. Also fails `sources_min_10`.
Follow ALL rules in logs/remediation/briefs/session98/_shared-expand-rules.md.

Work inside the worktree you were given; edit the file IN PLACE; commit at the end.

### DEEPEN these core sections (add genuine NEW Azure Monitor depth):
1. **The data planes: metrics vs logs** — platform **metrics** (near-real-time,
   cheap, multi-dimensional, the metrics explorer) vs **Log Analytics** (Kusto/KQL
   over structured logs, the workspace model, data retention/archive tiers, basic vs
   analytics table plans). Explain Diagnostic Settings as the pipe that routes
   resource logs/metrics to a workspace / storage / Event Hub.
2. **Application Insights & distributed tracing** — APM for apps: requests,
   dependencies, exceptions, the Application Map, live metrics, distributed tracing /
   correlation, sampling, and the workspace-based (vs classic) resource model. When
   to instrument with the SDK vs auto-instrumentation/OpenTelemetry.
3. **Alerting & response** — alert rules (metric, log, activity-log), signal logic
   and dynamic thresholds, **action groups** (email/SMS/webhook/Logic App/ITSM),
   alert processing rules and suppression, and **autoscale** rules driven by metrics.
   Include a short KQL example for a log alert and explain WHY (e.g. error-rate query).

### COST LENS: Log Analytics per-GB ingestion + retention-beyond-free + Basic-vs-
Analytics table plans + commitment tiers; Application Insights ingestion (now
workspace-based) and sampling to cut cost; metric alerts per-rule + per-time-series
cost; how verbose debug logging silently dominates the bill.

### ADD (currently missing): Patterns & Anti-Patterns + Decision Framework
(decision matrix: metric alert vs log alert; what to send to Logs vs Storage vs Event
Hub; sampling/retention to control cost).

Web-verify every new fact against learn.microsoft.com. Report final body_words.

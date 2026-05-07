---
revision_pending: true
title: "Module 1.10: SLO Tooling - Sloth, Pyrra, and the OpenSLO Ecosystem"
slug: platform/toolkits/observability-intelligence/observability/module-1.10-slo-tooling
sidebar:
  order: 11
---
## Complexity: [MEDIUM]

**Time to Complete**: 40 minutes
**Prerequisites**: [SRE Module 1.2: SLOs](/platform/disciplines/core-platform/sre/module-1.2-slos/), [SRE Module 1.3: Error Budgets](/platform/disciplines/core-platform/sre/module-1.3-error-budgets/), [Module 1.1: Prometheus](../module-1.1-prometheus/)
**Learning Objectives**:
- Define SLOs as code using Sloth and the OpenSLO specification
- Generate Prometheus recording rules and burn-rate alerts automatically
- Visualize error budgets with Pyrra dashboards
- Choose the right SLO tooling for your organization

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure SLO definitions using Sloth or Pyrra with error budget calculations and burn rate alerts**
- **Implement multi-window burn rate alerting for reliable SLO breach detection without alert fatigue**
- **Deploy SLO dashboards that communicate service reliability status to engineering and business stakeholders**
- **Evaluate SLO tooling approaches and integrate them with existing Prometheus monitoring infrastructure**


## Why This Module Matters

The SRE lead at a mid-size fintech company had done everything by the book. She had SLOs documented in Confluence. The team agreed on 99.9% availability for the payment API and a 200ms p99 latency target for the checkout flow. Error budget policies were signed off by engineering leadership. Textbook SRE.

A deployment can introduce a subtle correctness bug that slips past coarse availability alerts, especially when the team only measures HTTP 5xx responses.

Without burn-rate alerts and an error-budget view, a team can spend a large portion of its budget before anyone notices.

The answer was painful. SLOs lived in a wiki. The Prometheus rules were hand-written, outdated, and only covered availability -- not correctness. Nobody had a dashboard showing error budget consumption in real time. There were no burn-rate alerts. The SLOs existed on paper but not in the system.

**SLO tooling bridges the gap between SRE theory and production reality.** Tools like Sloth and Pyrra turn SLO definitions into working Prometheus rules, burn-rate alerts, and real-time dashboards -- automatically. You define your SLOs once in YAML, and the tooling generates everything needed to actually enforce them.

Putting SLOs into working tooling can shorten detection and response time by surfacing burn-rate alerts and current error-budget status during an incident.

---

## Did You Know?

- **Hand-written SLO recording rules are easy to get wrong** -- the Google SRE workbook recommends multi-window burn-rate alerting, and tools like Sloth reduce manual rule-writing by generating the recording and alert rules from an SLO spec.

- **Pyrra focuses on SLO visibility** -- it generates Prometheus recording rules from SLO objects and provides UI views for error budgets, burn rates, and alert status.

- **OpenSLO is a vendor-neutral SLO specification** -- it provides a common YAML format for expressing SLOs as code and is intended to make definitions more portable across tooling.

- **Multi-window burn-rate alerting improves precision over a single threshold** -- the Google SRE workbook recommends pairing long and short windows so alerts focus on sustained budget burn, and tools like Sloth automate that rule generation.

---

## The SLO Tooling Landscape

Before diving into individual tools, here is how they fit together:

```
┌─────────────────────────────────────────────────────┐
│                   SLO Definition                     │
│                                                     │
│   Sloth YAML    OpenSLO Spec    Nobl9 / SaaS       │
│       │              │               │              │
│       ▼              ▼               ▼              │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐      │
│  │  Sloth   │  │  Adapters │  │  SaaS Tools │      │
│  │ CLI/K8s  │  │           │  │             │      │
│  └────┬─────┘  └─────┬────┘  └──────┬──────┘      │
│       │              │              │               │
│       ▼              ▼              ▼               │
│  ┌──────────────────────────────────────────┐      │
│  │         Prometheus Recording Rules        │      │
│  │         + Multi-Burn-Rate Alerts          │      │
│  └──────────────────┬───────────────────────┘      │
│                     │                               │
│          ┌──────────┴──────────┐                    │
│          ▼                     ▼                    │
│   ┌────────────┐       ┌────────────┐              │
│   │   Pyrra    │       │  Grafana   │              │
│   │ Dashboard  │       │ Dashboards │              │
│   └────────────┘       └────────────┘              │
└─────────────────────────────────────────────────────┘
```

---

## Sloth: SLOs as Code

Sloth takes a simple YAML definition and [generates all the Prometheus recording rules and alerting rules you need](https://github.com/slok/sloth). You still define the SLI queries, but Sloth handles the repetitive rule generation and alert math.

### How Sloth Works

1. You write an SLO spec in YAML (5-20 lines)
2. Sloth generates Prometheus recording rules (~30 rules per SLO)
3. Sloth generates multi-window burn-rate alerts
4. You load the rules into Prometheus
5. Alerts fire when your error budget burns too fast

### Sloth SLO Specification

```yaml
# sloth.yaml
version: "prometheus/v1"
service: "payment-api"
labels:
  owner: "platform-team"
  tier: "critical"
slos:
  - name: "requests-availability"
    objective: 99.9
    description: "Payment API requests succeed without 5xx errors."
    sli:
      events:
        error_query: sum(rate(http_requests_total{service="payment-api",code=~"5.."}[{{.window}}]))
        total_query: sum(rate(http_requests_total{service="payment-api"}[{{.window}}]))
    alerting:
      name: PaymentAPIHighErrorRate
      labels:
        severity: critical
      annotations:
        summary: "Payment API error budget burn rate is too high."
      page_alert:
        labels:
          severity: page
      ticket_alert:
        labels:
          severity: ticket
```

The `{{.window}}` placeholder is key. Sloth substitutes different time windows (5m, 30m, 1h, 6h) automatically to build multi-window burn-rate detection.

### Generating Rules with the CLI

```bash
# Install Sloth
brew install sloth

# Generate Prometheus rules from your SLO spec
sloth generate -i sloth.yaml -o prometheus-rules.yaml

# Preview what gets generated (without writing files)
sloth generate -i sloth.yaml --dry-run
```

### What Sloth Generates

For a single SLO, Sloth produces:

| Rule Type | Count | Purpose |
|-----------|-------|---------|
| SLI recording rules | 4 | Error ratios at 5m, 30m, 1h, 6h windows |
| Error budget recording rules | 2 | Remaining budget and consumption rate |
| Burn-rate alert rules | 2 | Page alert (fast burn) + ticket alert (slow burn) |
| Metadata recording rules | ~4 | Labels, objectives, periods for dashboards |

That turns a short SLO spec into multiple recording and alerting rules, which is much easier to maintain than writing them all by hand.

### Running Sloth as a Kubernetes Operator

Sloth also runs as a controller inside your cluster:

```bash
# Install Sloth operator via Helm
helm repo add sloth https://slok.github.io/sloth
helm install sloth sloth/sloth -n monitoring

# Apply your SLO as a Kubernetes custom resource
kubectl apply -f - <<'EOF'
apiVersion: sloth.slok.dev/v1
kind: PrometheusServiceLevel
metadata:
  name: payment-api-slo
  namespace: monitoring
spec:
  service: "payment-api"
  labels:
    owner: "platform-team"
  slos:
    - name: "requests-availability"
      objective: 99.9
      sli:
        events:
          errorQuery: sum(rate(http_requests_total{service="payment-api",code=~"5.."}[{{.window}}]))
          totalQuery: sum(rate(http_requests_total{service="payment-api"}[{{.window}}]))
      alerting:
        name: PaymentAPIHighErrorRate
        pageAlert:
          labels:
            severity: page
        ticketAlert:
          labels:
            severity: ticket
EOF
```

The operator watches for `PrometheusServiceLevel` resources and automatically generates `PrometheusRule` objects that Prometheus Operator picks up. SLOs become part of your GitOps pipeline.

---

## Pyrra: SLO Dashboards and Error Budget Visualization

Pyrra complements Sloth by providing a dedicated UI for SLO tracking. While Sloth focuses on rule generation, Pyrra focuses on visibility.

### What Pyrra Provides

- **Error budget dashboard**: See remaining budget at a glance
- **Burn-rate visualization**: Charts showing how fast budget is consumed
- **Multi-window views**: multiple burn-rate and error-budget views for the same SLO
- **Alert status**: Which SLOs are currently alerting
- **Prometheus-native**: works alongside Prometheus and queries it for SLO data

### Deploying Pyrra

```bash
# Install Pyrra with Helm
helm repo add pyrra https://pyrra.dev
helm install pyrra pyrra/pyrra -n monitoring \
  --set "prometheusUrl=http://prometheus-server.monitoring.svc:9090"
```

### Defining SLOs in Pyrra

Pyrra uses its own CRD format:

```yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata:
  name: payment-api-availability
  namespace: monitoring
  labels:
    pyrra.dev/team: "platform"
spec:
  target: "99.9"
  window: 30d
  description: "Payment API returns successful responses."
  indicator:
    ratio:
      errors:
        metric: http_requests_total{service="payment-api",code=~"5.."}
      total:
        metric: http_requests_total{service="payment-api"}
```

Once applied, [Pyrra generates Prometheus rules and displays the SLO in its web UI](https://github.com/pyrra-dev/pyrra) with error budget graphs, burn-rate charts, and alert status.

### Pyrra + Grafana Integration

Pyrra exposes Prometheus metrics that you can query in Grafana:

```promql
# Remaining error budget (0 to 1, where 1 = 100% remaining)
pyrra_objective_error_budget_remaining{service="payment-api"}

# Current burn rate
pyrra_objective_burn_rate{service="payment-api", window="1h"}
```

---

## The OpenSLO Specification

OpenSLO is a [vendor-neutral YAML format for defining SLOs](https://github.com/OpenSLO/OpenSLO). Think of it as the "OpenAPI but for SLOs."

```yaml
apiVersion: openslo/v1
kind: SLO
metadata:
  name: payment-api-availability
spec:
  service: payment-api
  description: "Payment API serves requests successfully."
  budgetingMethod: Occurrences
  objectives:
    - displayName: Availability
      target: 0.999
      op: gte
  indicator:
    metadata:
      name: payment-api-success-rate
    spec:
      ratioMetric:
        counter: true
        good:
          metricSource:
            type: Prometheus
            spec:
              query: sum(rate(http_requests_total{service="payment-api",code!~"5.."}[5m]))
        total:
          metricSource:
            type: Prometheus
            spec:
              query: sum(rate(http_requests_total{service="payment-api"}[5m]))
  timeWindow:
    - duration: 30d
      isRolling: true
```

The advantage of OpenSLO is portability. It gives teams a common way to express SLOs as code and makes translation between compatible tools easier.

---

## Tool Comparison

| Feature | Sloth | Pyrra | Nobl9 | Google SLO Generator |
|---------|-------|-------|-------|---------------------|
| **Type** | CLI / K8s Operator | K8s Operator + UI | SaaS Platform | [CLI Tool](https://github.com/google/slo-generator) |
| **SLO Definition** | Custom YAML | Custom CRD | Web UI / Terraform | YAML config |
| **Rule Generation** | Prometheus rules | Prometheus rules | Managed backend | Stackdriver / Prometheus |
| **Dashboard** | No (use Grafana) | Built-in web UI | Built-in web UI | No (use Grafana) |
| **Error Budget Viz** | Via Grafana | Built-in | Built-in | Via Grafana |
| **Burn-Rate Alerts** | Auto-generated | Auto-generated | Auto-generated | Auto-generated |
| **OpenSLO Support** | Partial | No | Full | No |
| **GitOps Friendly** | Yes (YAML + CRD) | Yes (CRD) | Yes (Terraform) | Yes (YAML) |
| **Cost** | Free / OSS | Free / OSS | Commercial | Free / OSS |
| **Best For** | Rule generation | Visibility + rules | Enterprise / multi-cloud | GCP-heavy teams |

**When to use what:**

- **Sloth** when you want precise control over generated Prometheus rules and already have Grafana for dashboards
- **Pyrra** when you want an out-of-the-box SLO dashboard with minimal setup
- **Sloth + Pyrra** together when you want the best of both -- Sloth for rule generation, Pyrra for visualization
- **Nobl9** when you need enterprise features, multi-cloud SLO tracking, or SaaS management
- **Google SLO Generator** when you are deep in the GCP ecosystem

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix |
|---------|---------------|------------|
| SLI query does not match real traffic | Copy-pasted a query without verifying label names | Run the SLI query in Prometheus first; confirm it returns data |
| Objective set too high (99.99%) | Ambition without measuring current baseline | Measure actual performance for 2 weeks, then set an objective slightly above it |
| Forgetting the `{{.window}}` placeholder in Sloth | Hardcoding a time window like `[5m]` | In most cases, use `{{.window}}`; Sloth substitutes the correct windows |
| Not loading generated rules into Prometheus | Generating rules but never applying them | Use Prometheus Operator CRDs or mount rules into the Prometheus config |
| Only tracking availability, ignoring latency | Availability is the easiest SLI to define | Define at least two SLOs: availability and latency (p99 or p95) |
| Alert thresholds that page on slow burns | Using a single burn-rate threshold for all alert severities | Use Sloth's page vs ticket alert separation; page on fast burns, ticket on slow burns |
| No error budget policy defined | Tooling works but nobody acts when budget runs out | Document what happens at 50%, 25%, and 0% budget remaining |

---

## Hands-On Exercise: SLO Tooling Pipeline

### Objective

Define SLOs for a sample web service, generate Prometheus rules with Sloth, and visualize error budgets with Pyrra.

### Setup

```bash
# Create a kind cluster
kind create cluster --name slo-lab

# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  --set grafana.enabled=true
```

### Step 1: Deploy a Sample Application

```bash
kubectl create namespace demo

kubectl apply -n demo -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-service
  template:
    metadata:
      labels:
        app: web-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      containers:
        - name: web
          image: quay.io/brancz/prometheus-example-app:v0.5.0
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web-service
  ports:
    - port: 80
      targetPort: 8080
EOF
```

### Step 2: Define the SLO with Sloth

```bash
# Install Sloth CLI
brew install sloth  # macOS
# Or: go install github.com/slok/sloth/cmd/sloth@latest

# Create the SLO definition
cat > web-service-slo.yaml <<'EOF'
version: "prometheus/v1"
service: "web-service"
labels:
  owner: "platform-team"
  tier: "standard"
slos:
  - name: "availability"
    objective: 99.5
    description: "Web service responds without server errors."
    sli:
      events:
        error_query: sum(rate(http_requests_total{job="web-service",code=~"5.."}[{{.window}}]))
        total_query: sum(rate(http_requests_total{job="web-service"}[{{.window}}]))
    alerting:
      name: WebServiceAvailability
      page_alert:
        labels:
          severity: page
      ticket_alert:
        labels:
          severity: ticket
EOF

# Generate Prometheus rules
sloth generate -i web-service-slo.yaml -o web-service-rules.yaml

# Review what was generated
cat web-service-rules.yaml
```

### Step 3: Load Rules into Prometheus

```bash
# Apply as a PrometheusRule CRD (for Prometheus Operator)
kubectl apply -n monitoring -f web-service-rules.yaml

# Verify the rules are loaded
kubectl get prometheusrules -n monitoring
```

### Step 4: Deploy Pyrra for Visualization

```bash
helm repo add pyrra https://pyrra.dev
helm install pyrra pyrra/pyrra -n monitoring \
  --set "prometheusUrl=http://kube-prometheus-prometheus.monitoring.svc:9090"

# Port-forward to access the Pyrra UI
kubectl port-forward -n monitoring svc/pyrra 9099:9099
```

Open `http://localhost:9099` in your browser. You should see the web-service SLO with its error budget status.

### Step 5: Simulate an Incident

```bash
# Generate some error traffic to burn the error budget
kubectl run load-gen --image=busybox -n demo --restart=Never -- \
  sh -c 'while true; do wget -q -O- http://web-service/err 2>/dev/null; sleep 0.1; done'

# Watch the error budget burn in Pyrra (refresh the dashboard)
# After a few minutes, check if burn-rate alerts fire
kubectl get alerts -n monitoring
```

### Success Criteria

- [ ] Sloth generates Prometheus recording rules and alert rules from your YAML
- [ ] PrometheusRule resource is created in the cluster
- [ ] Pyrra dashboard shows the SLO with a remaining error budget percentage
- [ ] Simulated errors cause the burn rate to increase visibly in the dashboard

### Cleanup

```bash
kind delete cluster --name slo-lab
```

---

## Quiz

**Question 1**: What does Sloth's `{{.window}}` placeholder do in an SLI query?

<details>
<summary>Show Answer</summary>

Sloth substitutes `{{.window}}` with different time windows (5m, 30m, 1h, 6h) to generate multi-window burn-rate recording rules. This is how it calculates burn rates across multiple time horizons from a single SLI definition.
</details>

**Question 2**: Why use multi-window burn-rate alerting instead of a simple error rate threshold?

<details>
<summary>Show Answer</summary>

A simple threshold (e.g., "alert if error rate > 1%") fires on brief spikes that burn negligible budget, causing alert fatigue. Multi-window burn-rate alerting compares fast windows (e.g., 5m) against slow windows (e.g., 1h) to distinguish real incidents from noise. It catches genuine budget-burning events while ignoring transient blips, reducing false positives by up to 90%.
</details>

**Question 3**: When would you choose Pyrra over Sloth?

<details>
<summary>Show Answer</summary>

Choose Pyrra when you want a built-in web dashboard for SLO visualization without building custom Grafana dashboards. Pyrra provides error budget views, burn-rate charts, and alert status out of the box. Sloth is better when you only need rule generation and already have Grafana. Many teams use both together -- Sloth for precise rule generation and Pyrra for quick visibility.
</details>

**Question 4**: What is the main benefit of the OpenSLO specification?

<details>
<summary>Show Answer</summary>

OpenSLO provides a vendor-neutral, portable format for defining SLOs. You define your SLO once and can translate it to any platform that supports the spec (Nobl9, Datadog, open-source tools). This prevents vendor lock-in and lets teams standardize SLO definitions across different monitoring backends.
</details>

**Question 5**: A Sloth-generated page alert fires. What does this tell you about the error budget?

<details>
<summary>Show Answer</summary>

A page alert means the error budget is burning at a rate that will exhaust it well before the SLO window ends. Specifically, Sloth's page alerts use a fast burn rate (typically 14.4x for a 30-day window with a 5m/1h multi-window check). This means the budget would be fully consumed in roughly 2 days at the current rate -- an urgent situation requiring immediate action.
</details>

---

## Further Reading

- [Sloth GitHub Repository](https://github.com/slok/sloth) -- Full documentation and examples
- [Pyrra GitHub Repository](https://github.com/pyrra-dev/pyrra) -- Installation and CRD reference
- [OpenSLO Specification](https://openslo.com/) -- The vendor-neutral SLO standard
- [Google SRE Workbook: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) -- The theory behind multi-window burn-rate alerting
- [KubeDojo SRE Module 1.2: SLOs](/platform/disciplines/core-platform/sre/module-1.2-slos/) -- SLO theory foundations
- [KubeDojo SRE Module 1.3: Error Budgets](/platform/disciplines/core-platform/sre/module-1.3-error-budgets/) -- Error budget concepts and policies

---

## Next Module

[Module 1.11 (Coming Soon)] -- Continue exploring the observability toolkit.

## Sources

- [github.com: sloth](https://github.com/slok/sloth) — The Sloth README directly describes generation of Prometheus SLO metrics and multi-window multi-burn alerts from an SLO spec.
- [github.com: pyrra](https://github.com/pyrra-dev/pyrra) — The Pyrra README describes the UI, error-budget views, burn rates, and backend generation of Prometheus recording rules.
- [OpenSLO Specification](https://github.com/OpenSLO/OpenSLO) — Backs OpenSLO as a vendor-neutral specification for expressing SLOs, SLIs, objectives, alert policies, services, and budgeting methods in portable YAML.
- [github.com: slo generator](https://github.com/google/slo-generator) — The official repository README directly describes the CLI, YAML/JSON configuration, supported backends, and computed SLO outputs.

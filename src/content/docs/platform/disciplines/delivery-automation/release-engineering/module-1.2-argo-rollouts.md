---
title: "Module 1.2: Advanced Canary Deployments with Argo Rollouts"
slug: platform/disciplines/delivery-automation/release-engineering/module-1.2-argo-rollouts
sidebar:
  order: 3
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 3 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.1: Release Strategies](../module-1.1-release-strategies/) — Canary concepts, blast radius, progressive delivery
- **Required**: Prometheus basics — PromQL queries, metrics scraping, alerting fundamentals
- **Required**: Kubernetes Services and Ingress — Traffic routing, selectors, ingress controllers
- **Recommended**: Familiarity with Helm or Kustomize for templating
- **Recommended**: Understanding of HTTP status codes and latency percentiles

---

## Why This Module Matters

In the previous module, you learned that canary deployments send a small percentage of traffic to a new version and gradually increase it. You did this manually — patching Services, eyeballing dashboards, making gut-feeling decisions about whether to proceed.

Now imagine doing that at 3 AM. Or for 50 services simultaneously. Or when the person who understands the metrics is on vacation.

Manual canary deployments do not scale. They depend on a human watching dashboards, interpreting graphs, and making timely decisions. Humans get tired. Humans get distracted. Humans have slow reaction times compared to automated systems that can detect a spike in 5xx errors within 30 seconds and roll back within 60.

**Argo Rollouts** transforms canary deployments from a manual art into an automated science. It watches your Prometheus metrics, evaluates them against thresholds you define, and makes promotion or rollback decisions faster and more reliably than any human operator.

After this module, you will have a fully automated canary pipeline that promotes good releases and kills bad ones — without you lifting a finger.

---

## What is Argo Rollouts?

### The Gap in Native Kubernetes

Kubernetes Deployments support two strategies: `RollingUpdate` and `Recreate`. Neither gives you:

- Fine-grained traffic percentage control (5%, then 10%, then 25%)
- Metrics-driven promotion decisions
- Automated rollback based on business metrics
- Pause-and-verify steps between traffic increases
- Integration with service meshes or ingress controllers for traffic splitting

Argo Rollouts fills this gap with a custom `Rollout` resource that replaces the standard `Deployment`.

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Argo Rollouts Controller                    │
│                                                                │
│   Watches Rollout CRDs → Manages ReplicaSets → Runs Analyses  │
└───────────────┬──────────────────────────────┬─────────────────┘
                │                              │
                ▼                              ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│   Rollout Resource         │   │   AnalysisTemplate Resource   │
│                           │   │                               │
│  - Canary strategy         │   │  - Prometheus queries          │
│  - Traffic weight steps    │   │  - Success criteria            │
│  - Analysis references     │   │  - Failure thresholds          │
│  - Rollback rules          │   │  - Measurement intervals       │
└──────────┬────────────────┘   └───────────────┬───────────────┘
           │                                    │
           ▼                                    ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│   ReplicaSets             │   │   AnalysisRun (instance)       │
│                           │   │                               │
│  - Stable (current live)   │   │  - Running metrics queries     │
│  - Canary (new version)    │   │  - Evaluating pass/fail        │
│                           │   │  - Reporting to controller      │
└───────────────────────────┘   └───────────────────────────────┘
```

### Core CRDs

Argo Rollouts introduces four Custom Resource Definitions:

| CRD | Purpose |
|-----|---------|
| **Rollout** | Replaces Deployment; defines the canary/blue-green strategy |
| **AnalysisTemplate** | Defines what metrics to check and their success criteria |
| **AnalysisRun** | A running instance of an AnalysisTemplate (created automatically) |
| **Experiment** | Runs temporary ReplicaSets for A/B testing (advanced use) |

---

## Rollout Resource Deep Dive

### From Deployment to Rollout

Converting a Deployment to a Rollout is straightforward. The key changes:

```yaml
# Before: Standard Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
  selector:
    matchLabels:
      app: my-app
  template:
    # ... pod template ...
```

```yaml
# After: Argo Rollout
apiVersion: argoproj.io/v1alpha1      # ← Changed
kind: Rollout                          # ← Changed
metadata:
  name: my-app
spec:
  replicas: 5
  strategy:                            # ← Completely different
    canary:
      steps:
        - setWeight: 5
        - pause: { duration: 5m }
        - setWeight: 20
        - pause: { duration: 5m }
        - setWeight: 50
        - pause: { duration: 10m }
        - setWeight: 80
        - pause: { duration: 5m }
  selector:
    matchLabels:
      app: my-app
  template:
    # ... same pod template ...
```

### Canary Steps Explained

The `steps` array defines the rollout progression:

```yaml
steps:
  # Step 1: Send 5% of traffic to canary
  - setWeight: 5

  # Step 2: Wait 5 minutes (auto-proceed after duration)
  - pause: { duration: 5m }

  # Step 3: Run an analysis — metrics must pass to proceed
  - analysis:
      templates:
        - templateName: success-rate
      args:
        - name: service-name
          value: my-app

  # Step 4: If analysis passed, increase to 20%
  - setWeight: 20

  # Step 5: Indefinite pause — requires manual approval
  - pause: {}

  # Step 6: After manual approval, go to 50%
  - setWeight: 50

  # Step 7: Another analysis check at higher traffic
  - analysis:
      templates:
        - templateName: success-rate
        - templateName: latency-check

  # Step 8: Full rollout
  - setWeight: 100
```

### Step Types

| Step | Behavior |
|------|----------|
| `setWeight: N` | Route N% of traffic to canary |
| `pause: {duration: 5m}` | Wait, then auto-proceed |
| `pause: {}` | Wait indefinitely for manual promotion |
| `analysis:` | Run AnalysisTemplate; proceed on success, rollback on failure |
| `setCanaryScale:` | Set exact replica count for canary (instead of weight-based) |
| `setHeaderRoute:` | Route by HTTP header (A/B testing) |

---

## Traffic Routing

### How Traffic Splitting Works

Argo Rollouts supports multiple traffic routing mechanisms:

**1. Replica-based splitting (default, no extra infra):**

Traffic is split proportionally by pod count. If you have 10 replicas and set canary weight to 20%, Argo Rollouts runs 2 canary pods and 8 stable pods.

```
Limitation: You can only achieve traffic splits that align with replica counts.
With 5 replicas, your options are 20%, 40%, 60%, 80% — not 5% or 10%.
```

**2. Ingress-controller-based splitting (recommended):**

Argo Rollouts integrates with NGINX Ingress, ALB, Istio, Traefik, and others to achieve precise traffic percentages regardless of replica count.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  strategy:
    canary:
      canaryService: my-app-canary     # Service for canary pods
      stableService: my-app-stable     # Service for stable pods
      trafficRouting:
        nginx:
          stableIngress: my-app-ingress  # Your existing Ingress
          additionalIngressAnnotations:
            canary-by-header: X-Canary
            canary-weight: "5"
      steps:
        - setWeight: 5
        - pause: { duration: 5m }
        - setWeight: 25
        - pause: { duration: 5m }
        - setWeight: 50
        - pause: { duration: 10m }
```

This requires two Services:

```yaml
# Stable service (existing users)
apiVersion: v1
kind: Service
metadata:
  name: my-app-stable
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
---
# Canary service (canary traffic)
apiVersion: v1
kind: Service
metadata:
  name: my-app-canary
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
```

Argo Rollouts manages the selectors on these Services automatically, pointing the stable Service to the stable ReplicaSet and the canary Service to the canary ReplicaSet.

**3. Service Mesh integration (Istio):**

```yaml
trafficRouting:
  istio:
    virtualServices:
      - name: my-app-vsvc
        routes:
          - primary
    destinationRule:
      name: my-app-destrule
      canarySubsetName: canary
      stableSubsetName: stable
```

### Traffic Routing Comparison

| Method | Precision | Extra Infra | Best For |
|--------|-----------|-------------|----------|
| Replica-based | Low (limited to replica ratios) | None | Simple setups, development |
| NGINX Ingress | High (any percentage) | NGINX Ingress Controller | Most production use cases |
| Istio | Very High (percentage + headers + more) | Istio service mesh | Complex routing, header-based canaries |
| AWS ALB | High | AWS ALB Ingress | AWS-native environments |
| Traefik | High | Traefik | Traefik-based clusters |

---

## AnalysisTemplates: Metrics-Driven Decisions

### The Core Innovation

AnalysisTemplates are what make Argo Rollouts transformative. Instead of a human watching Grafana, you encode your promotion criteria as code:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      # Check every 60 seconds
      interval: 60s
      # Need at least 3 measurements before deciding
      count: 3
      # All 3 must pass
      successCondition: result[0] >= 0.95
      # If any single measurement is below 0.90, fail immediately
      failureCondition: result[0] < 0.90
      failureLimit: 0
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}",
                status!~"5.."
              }[5m]
            )) /
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}"}[5m]
              ))
```

This template says: "Query Prometheus every 60 seconds. The success rate (non-5xx / total) must be at least 95%. If it ever drops below 90%, fail immediately."

### Multiple Metrics

Real-world analysis checks multiple signals:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: canary-health
spec:
  args:
    - name: service-name
    - name: canary-hash
  metrics:
    # Metric 1: Error rate must stay below 5%
    - name: error-rate
      interval: 60s
      count: 5
      successCondition: result[0] < 0.05
      failureLimit: 1
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}",
                rollouts_pod_template_hash="{{args.canary-hash}}",
                status=~"5.."}[5m]
            )) /
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}",
                rollouts_pod_template_hash="{{args.canary-hash}}"}[5m]
            ))

    # Metric 2: P99 latency must stay below 500ms
    - name: latency-p99
      interval: 60s
      count: 5
      successCondition: result[0] < 500
      failureLimit: 1
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            histogram_quantile(0.99,
              sum(rate(
                http_request_duration_milliseconds_bucket{
                  service="{{args.service-name}}",
                  rollouts_pod_template_hash="{{args.canary-hash}}"
                }[5m]
              )) by (le)
            )

    # Metric 3: No OOM kills
    - name: no-oom-kills
      interval: 120s
      count: 3
      successCondition: result[0] == 0
      failureLimit: 0
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(increase(
              kube_pod_container_status_last_terminated_reason{
                reason="OOMKilled",
                pod=~"my-app-.*-{{args.canary-hash}}-.*"
              }[5m]
            )) or vector(0)
```

### AnalysisRun Lifecycle

When a Rollout step triggers an analysis, an AnalysisRun is created:

```
AnalysisTemplate (definition)
         │
         ▼
  AnalysisRun (instance)
         │
         ├── Measurement 1: ✓ Pass (success rate: 0.98)
         ├── Measurement 2: ✓ Pass (success rate: 0.97)
         ├── Measurement 3: ✓ Pass (success rate: 0.96)
         │
         └── Result: Successful → Rollout proceeds to next step
```

If a measurement fails:

```
  AnalysisRun (instance)
         │
         ├── Measurement 1: ✓ Pass (success rate: 0.97)
         ├── Measurement 2: ✗ Fail (success rate: 0.82)
         │
         └── Result: Failed → Rollout automatically rolls back
```

### Supported Providers

| Provider | Use Case |
|----------|----------|
| **Prometheus** | Most common; query any Prometheus metric |
| **Datadog** | SaaS monitoring; native Datadog queries |
| **New Relic** | NRQL queries for application metrics |
| **Wavefront** | Wavefront ts() queries |
| **CloudWatch** | AWS-native metrics |
| **Kayenta** | Netflix's automated canary analysis |
| **Web** | Generic HTTP endpoint (any JSON API) |
| **Job** | Run a Kubernetes Job as the analysis |

---

## Automated Rollback

### How Rollback Works

When an AnalysisRun fails, Argo Rollouts:

1. Immediately scales the canary ReplicaSet to zero
2. Sets the stable ReplicaSet to the desired replica count
3. Updates the traffic routing to send 100% to stable
4. Marks the Rollout as "Degraded"

```
Before failure:
  Stable (v1): 8 pods, 80% traffic
  Canary (v2): 2 pods, 20% traffic

After AnalysisRun failure:
  Stable (v1): 10 pods, 100% traffic
  Canary (v2): 0 pods, 0% traffic
  Status: Degraded
```

### Rollback Timing

The speed of automated rollback depends on your analysis configuration:

```yaml
metrics:
  - name: error-rate
    interval: 30s        # Check every 30 seconds
    failureLimit: 0      # Fail immediately on first bad measurement
```

With this configuration, the worst-case detection time is 30 seconds (one interval). Total rollback time:

```
Detection:  30 seconds (one interval)
Decision:    ~1 second (controller processes failure)
Scale down:  ~5 seconds (canary pods terminated)
Traffic:     ~1 second (routing updated)
─────────────────────────────────────
Total:      ~37 seconds
```

Compare this to a human operator who has to: notice the alert (minutes), open the dashboard (seconds), analyze the data (minutes), decide to rollback (seconds to minutes), execute the rollback (seconds). Total: 5-30 minutes.

### Abort vs Retry

```bash
# Manually abort a rollout (instant rollback)
kubectl argo rollouts abort my-app

# Retry a failed/aborted rollout
kubectl argo rollouts retry my-app

# Manually promote (skip remaining steps)
kubectl argo rollouts promote my-app

# Promote but only to the next step
kubectl argo rollouts promote my-app --step 1
```

---

## Anti-Affinity Between Canary and Stable

### Why It Matters

If canary and stable pods run on the same node and the new version has a memory leak that crashes the node, both versions go down. Use anti-affinity to separate them:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  strategy:
    canary:
      antiAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
          weight: 100
```

This tells Kubernetes to prefer scheduling canary pods on different nodes than stable pods. A canary crashing its node will not take down the stable version.

---

## Rollout Lifecycle & Status

### Understanding Rollout Phases

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Healthy │ ──► │ Paused   │ ──► │Progressing──► │  Healthy │
│  (v1)    │     │ (canary) │     │ (promote)│     │  (v2)    │
└──────────┘     └────┬─────┘     └──────────┘     └──────────┘
                      │
                      ▼ (analysis failure)
                ┌──────────┐
                │ Degraded │
                │(rollback)│
                └──────────┘
```

### Monitoring Rollouts

```bash
# Watch rollout status in real-time
kubectl argo rollouts get rollout my-app --watch

# Output:
# Name:            my-app
# Namespace:       default
# Status:          ॥ Paused
# Message:         CanaryPauseStep
# Strategy:        Canary
#   Step:          2/8
#   SetWeight:     20
#   ActualWeight:  20
# Images:          my-app:v1 (stable)
#                  my-app:v2 (canary)
# Replicas:
#   Desired:       10
#   Current:       12
#   Updated:       2
#   Ready:         12
#   Available:     12

# List all AnalysisRuns
kubectl get analysisrun

# Check specific AnalysisRun results
kubectl describe analysisrun my-app-abc123-2
```

### The Argo Rollouts Dashboard

Argo Rollouts includes a web dashboard for visualization:

```bash
# Install the dashboard
kubectl argo rollouts dashboard

# Open in browser
# http://localhost:3100
```

The dashboard shows:
- Current rollout step and progress
- Traffic weight distribution
- AnalysisRun results with individual measurements
- Rollout history
- One-click promote/abort buttons

---

## Advanced Patterns

### Background Analysis

Run analysis continuously during the entire rollout, not just at specific steps:

```yaml
strategy:
  canary:
    analysis:
      templates:
        - templateName: continuous-success-rate
      startingStep: 1    # Start analysis after first weight change
      args:
        - name: service-name
          value: my-app
    steps:
      - setWeight: 5
      - pause: { duration: 5m }
      - setWeight: 25
      - pause: { duration: 10m }
      - setWeight: 50
      - pause: { duration: 10m }
```

The background analysis runs from step 1 until the rollout completes or fails. If the analysis fails at any point, the rollout rolls back regardless of which step it is on.

### Inline Analysis (One-Off Checks)

For step-specific checks that differ from the background analysis:

```yaml
steps:
  - setWeight: 5
  - pause: { duration: 2m }
  - analysis:
      templates:
        - templateName: smoke-test   # Quick health check
      args:
        - name: url
          value: http://my-app-canary/health
  - setWeight: 50
  - analysis:
      templates:
        - templateName: load-test    # Performance check at higher traffic
      args:
        - name: target-rps
          value: "1000"
```

### Header-Based Routing

Route specific users to the canary based on HTTP headers:

```yaml
strategy:
  canary:
    trafficRouting:
      nginx:
        stableIngress: my-app-ingress
        additionalIngressAnnotations:
          canary-by-header: X-Canary-Test
    steps:
      # First: Only internal testers (via header) see canary
      - setHeaderRoute:
          name: canary-header
          match:
            - headerName: X-Canary-Test
              headerValue:
                exact: "true"
      - pause: {}    # Manual verification by testers

      # Then: Percentage-based rollout to real users
      - setWeight: 5
      - analysis:
          templates:
            - templateName: success-rate
      - setWeight: 50
      - pause: { duration: 10m }
```

Internal testers add `X-Canary-Test: true` to their requests and see the canary. Everyone else sees stable. After testers approve, the percentage-based rollout begins.

---

## Did You Know?

1. **Argo Rollouts was created by Intuit (the TurboTax company)** in 2019 because they needed automated canary deployments for their tax season releases — when a bad deployment could affect millions of taxpayers filing at deadline. They open-sourced it as part of the Argo project, and it is now a CNCF graduated project used by thousands of organizations.

2. **Netflix's canary analysis system (Kayenta) compares statistical distributions, not just thresholds**. Instead of checking "is the error rate below 5%?", it asks "is the canary's error rate distribution statistically different from the baseline's?" This catches subtle performance degradations that simple threshold checks miss. Argo Rollouts can use Kayenta as an analysis provider.

3. **Google reportedly deploys changes to a single cluster first and waits 24 hours before propagating globally**. Their "bake time" concept means that even after a canary passes metrics checks, it soaks in production for a full day cycle to catch time-dependent bugs (like a midnight cron job interaction or a timezone-specific issue). You can replicate this with Argo Rollouts pause steps.

4. **The mean time to detect a bad canary with automated analysis is under 2 minutes in most implementations**, compared to 15-45 minutes for human-driven detection. In a 2023 survey by the CD Foundation, teams using automated canary analysis reported 73% fewer production incidents from deployments compared to teams using manual canary evaluation.

---

## War Story: The Canary That Should Have Died

A payment processing team deployed a new version with an edge-case bug: transactions over $10,000 would fail silently. Their canary analysis checked error rates — but the error rate looked fine because:

1. Only 0.1% of transactions exceeded $10,000
2. The 5xx error rate barely moved (from 0.3% to 0.35%)
3. The failure was silent — the service returned 200 OK but did not process the payment

The canary was promoted. The bug hit production at full scale. Hundreds of high-value transactions were lost over two hours.

**What they learned:**

1. **Check business metrics, not just HTTP metrics**. They added an analysis metric for `payment_completion_rate` (payments received vs. payments successfully processed).
2. **Test at the extremes**. They added synthetic canary tests that specifically triggered edge cases.
3. **Silent failures are the deadliest**. They changed the service to return 500 on processing failures instead of swallowing errors.

Their updated AnalysisTemplate included:

```yaml
metrics:
  - name: payment-completion-rate
    successCondition: result[0] >= 0.999
    provider:
      prometheus:
        query: |
          sum(rate(payments_completed_total{...}[5m])) /
          sum(rate(payments_received_total{...}[5m]))
```

**Lesson**: Your canary analysis is only as good as the metrics it watches. If you only check infrastructure metrics, you will miss business logic failures.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using only error rate as the canary metric | Misses latency degradation, silent failures, resource issues | Check error rate AND p99 latency AND business metrics AND resource usage |
| Setting failureLimit too high | Bad canary runs for too long before rollback | Use `failureLimit: 0` or `1` for critical metrics; detect fast |
| Canary weight steps too large | Jumping from 5% to 50% loses the benefit of gradual rollout | Use increments: 5% → 10% → 25% → 50% → 75% → 100% |
| Not using background analysis | Only checking metrics at step boundaries misses degradation between steps | Add background analysis from `startingStep: 1` to catch issues anytime |
| Skipping anti-affinity | Canary crash takes down stable pods on the same node | Set `antiAffinity` in the Rollout spec |
| Using Rollouts without traffic routing integration | Traffic split is approximate, limited by replica count | Integrate with NGINX Ingress, Istio, or ALB for precise control |
| No bake time after metrics pass | Time-dependent bugs slip through | Add a long pause (1-24h) after final analysis before full promotion |
| Forgetting to test rollback | Rollback mechanism itself might fail | Regularly trigger deliberate rollbacks; test the unhappy path |

---

## Quiz: Check Your Understanding

### Question 1
What is the difference between an AnalysisTemplate and an AnalysisRun?

<details>
<summary>Show Answer</summary>

An **AnalysisTemplate** is a definition — a template that specifies which metrics to check, how often to check them, and what constitutes success or failure. It is like a class definition.

An **AnalysisRun** is an instance — a running execution of an AnalysisTemplate created automatically by the Rollout controller when a rollout step triggers analysis. It contains the actual measurements and results. It is like an object instantiated from the class.

You create AnalysisTemplates. Argo Rollouts creates AnalysisRuns for you.

</details>

### Question 2
Why is replica-based traffic splitting insufficient for most production canary deployments?

<details>
<summary>Show Answer</summary>

Replica-based splitting divides traffic proportionally by pod count. With 10 replicas, your traffic increments are limited to multiples of 10% (1 pod = 10%, 2 pods = 20%, etc.).

Problems with this approach:
- You cannot achieve small percentages like 1% or 5% without running many replicas
- With 5 replicas, your minimum canary weight is 20% — far too high for initial canary exposure
- The traffic split is approximate because Kubernetes load balancing is not perfectly even

Ingress controller or service mesh integration solves this by splitting traffic at the routing layer, independent of pod count. You can send exactly 1% to the canary while running a single canary pod.

</details>

### Question 3
What happens when an AnalysisRun fails during a canary rollout?

<details>
<summary>Show Answer</summary>

When an AnalysisRun fails:

1. The Rollout controller scales the canary ReplicaSet to zero
2. The stable ReplicaSet scales to the full desired replica count
3. Traffic routing is updated to send 100% of traffic to stable
4. The Rollout status is set to "Degraded"
5. The AnalysisRun is marked as "Failed" with the failing measurements recorded

This entire process typically completes in under 60 seconds. The Rollout stays in "Degraded" state until a new version is deployed or the operator manually retries (`kubectl argo rollouts retry`).

</details>

### Question 4
When should you use background analysis vs inline (step-based) analysis?

<details>
<summary>Show Answer</summary>

**Background analysis** runs continuously from a specified step until the rollout completes. Use it for:
- Core health metrics that should always be monitored (error rate, latency)
- Metrics that need time to accumulate statistical significance
- Catching degradation between steps, not just at step boundaries

**Inline analysis** runs at a specific step and must complete before proceeding. Use it for:
- Step-specific validations (smoke test after first deployment)
- Different criteria at different traffic levels (stricter checks at higher weight)
- One-off checks like load tests or integration tests

Best practice: use background analysis for core metrics AND inline analysis for step-specific checks. They complement each other.

</details>

### Question 5
A team's canary analysis checks HTTP error rate and P99 latency, yet they still experience production issues after canary promotion. What metrics might they be missing?

<details>
<summary>Show Answer</summary>

Common metrics that HTTP error rate and P99 latency miss:

1. **Business metrics**: Payment completion rate, signup conversion, order success rate — a bug could return 200 OK but produce wrong results
2. **Resource metrics**: Memory usage trending upward (slow leak), CPU utilization, connection pool exhaustion
3. **Downstream dependency health**: Increased errors from services that the canary calls
4. **Error distribution**: Overall error rate might be fine, but a specific endpoint could have 50% errors
5. **Client-side metrics**: JavaScript errors, mobile crash rates, client-observed latency
6. **Data quality**: Correct results returned but data corruption in writes

The lesson: canary analysis should check multiple layers — infrastructure, application, and business metrics.

</details>

### Question 6
How would you implement a "soak test" with Argo Rollouts — where the canary runs at 100% for 24 hours before being fully promoted?

<details>
<summary>Show Answer</summary>

Use a combination of weight steps, background analysis, and a long pause:

```yaml
strategy:
  canary:
    analysis:
      templates:
        - templateName: continuous-health
      startingStep: 1
    steps:
      - setWeight: 5
      - pause: { duration: 30m }
      - setWeight: 25
      - pause: { duration: 1h }
      - setWeight: 100
      - pause: { duration: 24h }    # 24-hour soak at full traffic
```

The background analysis monitors health continuously during the entire 24-hour soak period. If any metric fails at any point during those 24 hours, the rollout rolls back automatically. Only after 24 hours of clean metrics does the rollout complete and the canary become the new stable version.

This catches time-dependent bugs: midnight cron interactions, timezone issues, daily traffic pattern variations, and slow resource leaks.

</details>

---

## Hands-On Exercise: Automated Canary with Prometheus-Based Rollback

### Objective

Deploy Argo Rollouts with Prometheus analysis that automatically promotes a healthy canary and rolls back a bad one.

### Setup

```bash
# Create cluster
kind create cluster --name argo-rollouts-lab

# Install Argo Rollouts
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install the kubectl plugin
# macOS:
brew install argoproj/tap/kubectl-argo-rollouts
# Linux:
# curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
# chmod +x kubectl-argo-rollouts-linux-amd64
# sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# Install Prometheus (lightweight, for the lab)
kubectl create namespace monitoring
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup/0namespace-namespace.yaml 2>/dev/null || true

# For this lab, we'll use a minimal Prometheus deployment
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
        - name: prometheus
          image: prom/prometheus:v2.53.0
          ports:
            - containerPort: 9090
          args:
            - "--config.file=/etc/prometheus/prometheus.yml"
            - "--storage.tsdb.retention.time=1h"
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
      volumes:
        - name: config
          configMap:
            name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
    - port: 9090
      targetPort: 9090
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 10s
    scrape_configs:
      - job_name: 'apps'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            target_label: __address__
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: ${1}:${2}
EOF
```

Wait for Argo Rollouts and Prometheus to be ready:

```bash
kubectl -n argo-rollouts rollout status deployment argo-rollouts
kubectl -n monitoring rollout status deployment prometheus
```

### Step 1: Create the AnalysisTemplate

```yaml
# analysis-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate-check
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 30s
      count: 3
      successCondition: result[0] >= 0.95
      failureCondition: result[0] < 0.90
      failureLimit: 0
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(
              http_requests_total{
                app="{{args.service-name}}",
                status!~"5.."
              }[1m]
            )) /
            sum(rate(
              http_requests_total{
                app="{{args.service-name}}"
              }[1m]
            ))
```

```bash
kubectl apply -f analysis-template.yaml
```

### Step 2: Create the Rollout

```yaml
# rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: demo-app
spec:
  replicas: 5
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: { duration: 30s }
        - analysis:
            templates:
              - templateName: success-rate-check
            args:
              - name: service-name
                value: demo-app
        - setWeight: 50
        - pause: { duration: 30s }
        - setWeight: 80
        - pause: { duration: 30s }
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: demo-app
  template:
    metadata:
      labels:
        app: demo-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      containers:
        - name: demo-app
          image: hashicorp/http-echo:0.2.3
          args:
            - "-text=Version 1 - Healthy"
            - "-listen=:8080"
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: demo-app
spec:
  selector:
    app: demo-app
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl apply -f rollout.yaml
kubectl argo rollouts get rollout demo-app --watch
```

Wait until the rollout is "Healthy" (all 5 pods running v1).

### Step 3: Deploy a "Good" Canary

Update the image to trigger a canary rollout:

```bash
kubectl argo rollouts set image demo-app demo-app=hashicorp/http-echo:0.2.3 \
  -- -text="Version 2 - Also Healthy" -listen=:8080

# Watch the rollout progress
kubectl argo rollouts get rollout demo-app --watch
```

You should see:
1. Weight set to 20%
2. Pause for 30 seconds
3. AnalysisRun created and (assuming metrics pass) succeeding
4. Weight progressing to 50%, 80%, then 100%
5. Rollout status changes to "Healthy"

### Step 4: Deploy a "Bad" Canary (Observe Rollback)

To simulate a bad deployment, deploy a version that will produce errors. Since we are using http-echo for simplicity, we will manually fail the AnalysisRun to demonstrate the rollback mechanism:

```bash
# Trigger a new rollout
kubectl argo rollouts set image demo-app demo-app=hashicorp/http-echo:0.2.3 \
  -- -text="Version 3 - Bad Version" -listen=:8080

# Watch in one terminal
kubectl argo rollouts get rollout demo-app --watch

# In another terminal, when the AnalysisRun appears, abort to simulate failure
# (In production, the Prometheus query would detect real errors)
kubectl argo rollouts abort demo-app
```

You should see:
1. Weight set to 20%
2. When aborted: canary pods immediately scale to zero
3. All traffic goes back to stable
4. Status shows "Degraded"

### Step 5: Explore the AnalysisRun

```bash
# List all AnalysisRuns
kubectl get analysisrun

# Describe the latest one
LATEST_AR=$(kubectl get analysisrun --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl describe analysisrun $LATEST_AR
```

### Step 6: Recover from Degraded State

```bash
# Retry with a fix
kubectl argo rollouts retry rollout demo-app

# Or deploy a new (fixed) version
kubectl argo rollouts set image demo-app demo-app=hashicorp/http-echo:0.2.3 \
  -- -text="Version 4 - Fixed" -listen=:8080
```

### Clean Up

```bash
kind delete cluster --name argo-rollouts-lab
```

### Success Criteria

You have completed this exercise when you can confirm:

- [ ] Argo Rollouts controller is running in the `argo-rollouts` namespace
- [ ] An AnalysisTemplate was created with Prometheus query configuration
- [ ] A Rollout resource replaced the standard Deployment
- [ ] A "good" canary progressed through all steps and was promoted
- [ ] A "bad" canary was aborted/rolled back, returning traffic to stable
- [ ] You inspected an AnalysisRun and understood its measurement results
- [ ] The rollout recovered from Degraded state with a new version
- [ ] You can explain the difference between background and inline analysis

---

## Key Takeaways

1. **Argo Rollouts replaces Deployment** with a `Rollout` CRD that supports fine-grained canary and blue-green strategies
2. **AnalysisTemplates encode promotion criteria as code** — no more human dashboard-watching at 3 AM
3. **Traffic routing integrations** (NGINX, Istio, ALB) enable precise traffic splitting independent of replica count
4. **Background analysis catches problems between steps** — not just at step boundaries
5. **Automated rollback is faster than any human** — detection to recovery in under 60 seconds
6. **Check multiple metric layers** — infrastructure, application, AND business metrics
7. **Anti-affinity protects stable from canary failures** — do not let a bad canary take down the working version

---

## Further Reading

**Documentation:**
- **Argo Rollouts Official Docs** — argoproj.github.io/argo-rollouts
- **Argo Rollouts Best Practices** — argoproj.github.io/argo-rollouts/best-practices/
- **Analysis and Progressive Delivery** — argoproj.github.io/argo-rollouts/features/analysis/

**Articles:**
- **"Progressive Delivery with Argo Rollouts"** — Intuit Engineering Blog
- **"Canary Deployments Made Easy"** — CNCF Blog
- **"Automated Canary Analysis at Netflix"** — Netflix Tech Blog (Kayenta)

**Talks:**
- **"Argo Rollouts: Scalable Progressive Delivery"** — KubeCon (YouTube)
- **"Lessons Learned from Argo Rollouts at Scale"** — ArgoCon (YouTube)

---

## Summary

Argo Rollouts transforms canary deployments from manual guesswork into automated, metrics-driven progressive delivery. By defining success criteria as AnalysisTemplates and integrating with Prometheus, your deployments promote themselves when healthy and roll back within seconds when they are not. Combined with traffic routing integration for precise control and background analysis for continuous monitoring, Argo Rollouts gives you confidence that bad code will never reach more users than necessary.

---

## Next Module

Continue to [Module 1.3: Feature Management at Scale](../module-1.3-feature-flags/) to learn how to decouple deployment from release using feature flags, enabling trunk-based development and instant kill switches.

---

*"The best rollback is the one that happens before your users notice."* — Argo Rollouts philosophy

---
title: "Module 2.2: Argo Rollouts"
slug: platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

---

*Progressive delivery lets teams [expose only a small slice of traffic to a new version, watch service metrics, and automatically abort a rollout when the canary regresses](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/) before the whole user base is affected.*

---

## Prerequisites

Before starting this module:
- [Module 2.1: ArgoCD](../module-2.1-argocd/) — GitOps fundamentals
- [GitOps Discipline](/platform/disciplines/delivery-automation/gitops/) — Deployment concepts
- Understanding of Kubernetes Deployments and Services
- Basic networking concepts (traffic splitting)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure canary deployments with automated analysis using Prometheus metrics queries**
- **Implement blue-green deployments with traffic management and automated promotion criteria**
- **[Integrate Argo Rollouts with service meshes and ingress controllers for traffic splitting](https://argoproj.github.io/rollouts/)**
- **Evaluate progressive delivery strategies and select appropriate rollout patterns for different risk profiles**


## Why This Module Matters

[Kubernetes Deployments use rolling updates by default](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)—gradually replacing old pods with new ones. But [rolling updates can't answer: "Is this new version actually better?" They blindly proceed until all pods are replaced.](https://argoproj.github.io/rollouts/)

[Argo Rollouts enables progressive delivery: canary deployments, blue-green switches, and automated rollbacks based on metrics](https://argoproj.github.io/rollouts/). You can deploy to 10% of traffic, verify metrics look good, then automatically promote to 100%—or roll back if they don't.

## Did You Know?

- **Argo Rollouts addresses gaps in standard Kubernetes rollout behavior**—it adds progressive delivery patterns and analysis-driven control for safer releases.
- **The canary deployment pattern is named after canaries in coal mines**—miners brought canaries underground; if the canary died, the air was toxic
- **Automated canary analysis is an established practice**—[Argo Rollouts can integrate with systems such as Kayenta](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/).
- **Blue-green deployments require extra capacity during promotion**—[both versions can run at the same time until traffic switches and the old version scales down](https://argo-rollouts.readthedocs.io/en/stable/features/bluegreen/).

## Rollout Strategies

### Rolling Update vs. Progressive Delivery

```
ROLLING UPDATE (Native Kubernetes)
─────────────────────────────────────────────────────────────────

Time ──────────────────────────────────────────────────────────▶

Pods:  [v1][v1][v1][v1][v1]
       [v1][v1][v1][v1][v2] → 1 pod replaced
       [v1][v1][v1][v2][v2] → 2 pods replaced
       [v1][v1][v2][v2][v2] → 3 pods replaced
       [v1][v2][v2][v2][v2] → 4 pods replaced
       [v2][v2][v2][v2][v2] → Done!

Traffic: No control - pods receive traffic as soon as ready
Rollback: Must wait for new rolling update
Analysis: None - hope for the best

─────────────────────────────────────────────────────────────────

CANARY (Argo Rollouts)
─────────────────────────────────────────────────────────────────

Time ──────────────────────────────────────────────────────────▶

Pods:  [v1][v1][v1][v1][v1]
       [v1][v1][v1][v1][v1] + [v2]  → Canary pod added

Traffic: v1 (90%) ─────────────────────────────────────────────▶
         v2 (10%) ─────────────────────────────────────────────▶

Analysis: Is error rate OK? Is latency OK?
          ├── Yes: Increase to 50%, then 100%
          └── No: Rollback immediately, alert on-call

Result: Bad versions never reach more than 10% of users
```

### Blue-Green Strategy

```
BLUE-GREEN DEPLOYMENT
─────────────────────────────────────────────────────────────────

BEFORE:
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  BLUE (Active)              GREEN (Inactive)                  │
│  ┌─────────────────┐       ┌─────────────────┐               │
│  │     v1 pods     │       │    (empty)      │               │
│  │  [v1][v1][v1]   │       │                 │               │
│  └────────┬────────┘       └─────────────────┘               │
│           │                                                   │
│           ▼                                                   │
│      ┌─────────┐                                             │
│      │ Service │ ──────▶ 100% traffic                        │
│      └─────────┘                                             │
│                                                               │
└──────────────────────────────────────────────────────────────┘

AFTER DEPLOYMENT:
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  BLUE (Inactive)            GREEN (Active)                    │
│  ┌─────────────────┐       ┌─────────────────┐               │
│  │     v1 pods     │       │     v2 pods     │               │
│  │  [v1][v1][v1]   │       │  [v2][v2][v2]   │               │
│  └─────────────────┘       └────────┬────────┘               │
│                                     │                         │
│                                     ▼                         │
│                               ┌─────────┐                     │
│                               │ Service │ ──────▶ 100%       │
│                               └─────────┘                     │
│                                                               │
│  (kept for instant rollback)                                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Installing Argo Rollouts

```bash
# Install controller
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install kubectl plugin
brew install argoproj/tap/kubectl-argo-rollouts  # macOS
# or
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# Verify
kubectl argo rollouts version
```

## Canary Rollouts

### Basic Canary

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 5
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: myapp:v2
          ports:
            - containerPort: 8080

  strategy:
    canary:
      # Traffic split steps
      steps:
        - setWeight: 10
        - pause: {duration: 5m}   # Wait 5 minutes
        - setWeight: 30
        - pause: {duration: 5m}
        - setWeight: 60
        - pause: {duration: 5m}
        # 100% happens automatically after last step

      # Traffic routing (for service mesh / ingress)
      canaryService: my-app-canary
      stableService: my-app-stable

      # Analysis at each step
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 1
        args:
          - name: service-name
            value: my-app-canary
```

### Canary with Traffic Management

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 5
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: myapp:v2

  strategy:
    canary:
      canaryService: my-app-canary
      stableService: my-app-stable

      trafficRouting:
        # NGINX Ingress
        nginx:
          stableIngress: my-app-ingress
          annotationPrefix: nginx.ingress.kubernetes.io

        # OR Istio
        # istio:
        #   virtualService:
        #     name: my-app-vs

        # OR AWS ALB
        # alb:
        #   ingress: my-app-ingress
        #   servicePort: 80

      steps:
        - setWeight: 10
        - pause: {duration: 2m}
        - setWeight: 30
        - pause: {duration: 2m}
        - setWeight: 60
        - pause: {duration: 2m}
---
# Services for traffic splitting
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

### Canary with Manual Approval

```yaml
strategy:
  canary:
    steps:
      - setWeight: 10
      - pause: {}          # Infinite pause - requires manual promotion
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 100
```

```bash
# Check rollout status
kubectl argo rollouts get rollout my-app

# Promote past the pause
kubectl argo rollouts promote my-app

# Or abort and rollback
kubectl argo rollouts abort my-app
```

## Blue-Green Rollouts

### Basic Blue-Green

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: myapp:v2

  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview

      # Wait for analysis before promotion
      prePromotionAnalysis:
        templates:
          - templateName: smoke-tests
        args:
          - name: service-name
            value: my-app-preview

      # Require manual approval
      autoPromotionEnabled: false

      # Keep old ReplicaSet for quick rollback
      scaleDownDelaySeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-active
spec:
  selector:
    app: my-app
  ports:
    - port: 80
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-preview
spec:
  selector:
    app: my-app
  ports:
    - port: 80
```

### Blue-Green with Automatic Promotion

```yaml
strategy:
  blueGreen:
    activeService: my-app-active
    previewService: my-app-preview

    # Auto-promote after preview is ready
    autoPromotionEnabled: true
    autoPromotionSeconds: 60  # Wait 60s after ready

    # Analysis before switching
    prePromotionAnalysis:
      templates:
        - templateName: smoke-tests

    # Analysis after switching
    postPromotionAnalysis:
      templates:
        - templateName: success-rate
      args:
        - name: duration
          value: "5m"
```

## Analysis Templates

### Prometheus Metrics Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
    - name: threshold
      value: "0.95"  # 95% success rate

  metrics:
    - name: success-rate
      interval: 1m
      count: 5  # Run 5 times
      successCondition: result[0] >= {{args.threshold}}
      failureLimit: 3

      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}",
                status=~"2.."
              }[1m]
            )) /
            sum(rate(
              http_requests_total{
                service="{{args.service-name}}"
              }[1m]
            ))
```

### Latency Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: latency-check
spec:
  args:
    - name: service-name
    - name: percentile
      value: "0.99"
    - name: threshold-ms
      value: "500"

  metrics:
    - name: p99-latency
      interval: 1m
      count: 5
      successCondition: result[0] < {{args.threshold-ms}}
      failureLimit: 2

      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            histogram_quantile(
              {{args.percentile}},
              sum(rate(
                http_request_duration_seconds_bucket{
                  service="{{args.service-name}}"
                }[2m]
              )) by (le)
            ) * 1000
```

### Web Hook Analysis (Custom Checks)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: custom-check
spec:
  args:
    - name: canary-hash

  metrics:
    - name: integration-tests
      successCondition: result.passed == true
      failureLimit: 1

      provider:
        web:
          url: https://ci.example.com/api/test
          method: POST
          headers:
            - key: Content-Type
              value: application/json
          body: |
            {
              "pod_hash": "{{args.canary-hash}}",
              "test_suite": "smoke"
            }
          jsonPath: "{$.result}"
```

### Kayenta Analysis (Automated Canary Analysis)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: kayenta-analysis
spec:
  args:
    - name: start-time
    - name: end-time

  metrics:
    - name: kayenta
      provider:
        kayenta:
          address: http://kayenta.monitoring:8090
          application: my-app
          canaryConfigName: my-canary-config
          metricsAccountName: prometheus-account
          storageAccountName: gcs-account
          threshold:
            pass: 95
            marginal: 75
          scopes:
            - name: default
              controlScope:
                scope: production
                start: "{{args.start-time}}"
                end: "{{args.end-time}}"
              experimentScope:
                scope: canary
                start: "{{args.start-time}}"
                end: "{{args.end-time}}"
```

## Analysis Runs

### Inline Analysis

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {duration: 2m}

      # Run analysis at this step
      - analysis:
          templates:
            - templateName: success-rate
          args:
            - name: service-name
              value: my-app-canary

      - setWeight: 50
      - pause: {duration: 2m}
      - setWeight: 100
```

### Background Analysis

```yaml
strategy:
  canary:
    analysis:
      # Start analysis after first step
      startingStep: 1

      templates:
        - templateName: success-rate
        - templateName: latency-check

      args:
        - name: service-name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
```

### Analysis with Dry-Run

```yaml
strategy:
  canary:
    analysis:
      templates:
        - templateName: success-rate

      # Don't fail rollout, just report
      dryRun:
        - metricName: success-rate
```

## Experiments

### A/B Testing

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Experiment
metadata:
  name: homepage-experiment
spec:
  duration: 1h

  templates:
    - name: control
      replicas: 2
      selector:
        matchLabels:
          app: homepage
          variant: control
      template:
        metadata:
          labels:
            app: homepage
            variant: control
        spec:
          containers:
            - name: app
              image: homepage:v1

    - name: experiment
      replicas: 2
      selector:
        matchLabels:
          app: homepage
          variant: experiment
      template:
        metadata:
          labels:
            app: homepage
            variant: experiment
        spec:
          containers:
            - name: app
              image: homepage:v2-new-design

  analyses:
    - name: conversion-rate
      templateName: conversion-analysis
      args:
        - name: control-service
          value: homepage-control
        - name: experiment-service
          value: homepage-experiment
```

### Experiment as Part of Rollout

```yaml
strategy:
  canary:
    steps:
      - setWeight: 0

      # Run experiment before any traffic
      - experiment:
          duration: 30m
          templates:
            - name: experiment
              specRef: canary
              replicas: 2
          analyses:
            - name: smoke-test
              templateName: smoke-tests

      - setWeight: 20
      - pause: {duration: 5m}
      - setWeight: 100
```

## Observing Rollouts

### CLI Commands

```bash
# Watch rollout in real-time
kubectl argo rollouts get rollout my-app --watch

# See rollout history
kubectl argo rollouts history rollout my-app

# Get detailed status
kubectl argo rollouts status my-app

# List all rollouts
kubectl argo rollouts list rollouts

# Dashboard (web UI)
kubectl argo rollouts dashboard
```

### Rollout Status

```
NAME                                  KIND        STATUS     AGE
my-app                                Rollout     ✔ Healthy  5d
├──# revision:3
│  └──⧫ my-app-7f8b9c6d4-xxxxx       Pod         ✔ Running  1h
│  └──⧫ my-app-7f8b9c6d4-yyyyy       Pod         ✔ Running  1h
│  └──⧫ my-app-7f8b9c6d4-zzzzz       Pod         ✔ Running  1h
├──# revision:2
│  └──⧫ my-app-5f7b8c5d3-aaaaa       Pod         ◌ ScaledDown  2h
└──# revision:1
   └──⧫ my-app-4f6b7c4d2-bbbbb       Pod         ◌ ScaledDown  3d
```

### Notifications

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
  annotations:
    notifications.argoproj.io/subscribe.on-rollout-completed.slack: rollouts-channel
    notifications.argoproj.io/subscribe.on-rollout-step-completed.slack: rollouts-channel
    notifications.argoproj.io/subscribe.on-analysis-run-failed.slack: rollouts-alerts
spec:
  # ...
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| No analysis templates | Blind deployment, no safety | Always add success-rate and latency analysis |
| Too aggressive steps | Problems hit many users | Start with a small canary percentage and pause long enough to observe meaningful metrics |
| Ignoring canary metrics | Analysis passes but users suffer | Include business metrics, not just infrastructure |
| No scaleDownDelay | Fast rollback is harder once old pods are gone | Keep the old version available long enough for traffic to drain and rollback to remain practical |
| Same replica count | Canary gets equal load despite traffic | Scale canary based on traffic weight |
| Manual promotion in prod | Human bottleneck, slow deployments | Use automated analysis for well-understood services |

## War Story: How Progressive Delivery Can Stop a Bad Deployment Early

```
┌─────────────────────────────────────────────────────────────────┐
│  THE $8.3 MILLION DEPLOYMENT THAT TOOK 90 SECONDS TO STOP      │
│  ───────────────────────────────────────────────────────────────│
│  Company: Global food delivery platform                         │
│  Scale: High-volume production traffic                          │
│  The crisis: Memory leak shipped to production Friday evening   │
└─────────────────────────────────────────────────────────────────┘
```

**Friday, 6:47 PM - The Deploy**

A memory leak can pass unit tests and light staging traffic, then surface quickly under production load, which is why progressive analysis should watch for resource-growth regressions before full promotion.

**Before Argo Rollouts (The Old World)**

A similar incident without progressive delivery can look like this:

```
PREVIOUS INCIDENT - WITHOUT PROGRESSIVE DELIVERY
─────────────────────────────────────────────────────────────────
18:47  Deploy started (Kubernetes rolling update)
18:49  100% traffic on new version (maxSurge, maxUnavailable)
19:02  First OOM kill (dismissed as transient)
19:15  15 pods OOM killed, orders failing
19:23  On-call paged, starts investigation
19:35  Root cause identified: memory leak
19:40  Rollback initiated
19:47  Rollback complete, but...
19:47  → Database connection pool exhausted (thundering herd)
20:15  Full recovery

Total impact: a prolonged outage with substantial business loss
Plus: SLA violations, restaurant refunds, customer credits
Total incident cost: significant
```

**With Argo Rollouts (The New World)**

A team facing this failure mode can implement Argo Rollouts with automated analysis like this:

```yaml
# The rollout configuration that saved them
strategy:
  canary:
    steps:
      - setWeight: 5           # Start with 5% traffic
      - pause: {duration: 5m}  # Watch for 5 minutes
      - analysis:
          templates:
            - templateName: memory-stability
      - setWeight: 25
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 10m}
      - setWeight: 100

---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: memory-stability
spec:
  metrics:
    - name: memory-growth-rate
      interval: 1m
      count: 5
      # Fail if memory grows more than 10% in 5 minutes
      successCondition: result[0] < 0.1
      provider:
        prometheus:
          query: |
            (
              avg(container_memory_working_set_bytes{pod=~"order-service-canary.*"})
              - avg(container_memory_working_set_bytes{pod=~"order-service-canary.*"} offset 5m)
            ) / avg(container_memory_working_set_bytes{pod=~"order-service-canary.*"} offset 5m)
```

**A Timeline Showing Early Automated Abort**

```
FRIDAY 6:47 PM - WITH ARGO ROLLOUTS
─────────────────────────────────────────────────────────────────
18:47:00  Rollout started
18:47:05  Canary pods created (5% traffic)
18:48:00  Memory baseline: 256MB per pod
18:50:00  Memory trending: 312MB (normal startup)
18:52:00  Memory trending: 489MB (⚠️ growing fast)
18:52:30  Analysis check 1: Growth rate 91% - FAIL
18:52:31  Analysis status: Failed
18:52:32  Rollout aborted automatically
18:52:35  Canary pods terminating
18:52:40  100% traffic back to stable

Total time exposed: only a short validation window
Traffic affected: only a small fraction of total traffic
Failed orders: 0 (caught before OOM)
```

**The Financial Math**

```
COST COMPARISON
─────────────────────────────────────────────────────────────────
WITHOUT ARGO ROLLOUTS:
─────────────────────────────────────────────────────────────────
Downtime:                28 minutes
Revenue loss:            28 × $17,000 = $476,000
SLA violations:          $320,000
Restaurant compensation: $180,000
Customer credits:        $120,000
Engineering overtime:    $45,000
Reputation damage:       Immeasurable
─────────────────────────────────────────────────────────────────
Total:                   $1,141,000+

WITH ARGO ROLLOUTS:
─────────────────────────────────────────────────────────────────
Canary exposure:         5.7 minutes at 5% traffic
Revenue loss:            ~$4,800 (delayed orders, not lost)
Customer impact:         2,500 slightly delayed orders
SLA violations:          $0 (within tolerance)
Engineering response:    $0 (automatic)
─────────────────────────────────────────────────────────────────
Total:                   <$5,000

SAVINGS PER INCIDENT:    potentially substantial
```

**Why Memory Analysis Caught It**

The key insight: memory leaks are progressive. They don't fail immediately—they compound. Traditional health checks (readiness probes) don't catch memory leaks because pods stay "healthy" until they suddenly aren't.

```
MEMORY TRAJECTORY COMPARISON
─────────────────────────────────────────────────────────────────
                    Stable Version         Leaky Version
─────────────────────────────────────────────────────────────────
t=0 (startup)      256 MB                 256 MB
t=2 min            260 MB                 340 MB    ← Diverging
t=5 min            262 MB                 520 MB    ← Analysis fails here
t=10 min           265 MB                 890 MB
t=15 min           268 MB                 OOM KILL  ← Would have failed here
```

**Key Lessons**

1. **Analysis timing matters**: Memory-leak detection needs enough observation time to reveal a trend
2. **Rate of change, not absolute values**: Looking at growth rate catches leaks before OOM
3. **Start small**: Use a small initial canary so failures stay contained
4. **Automated response is faster**: Machines detect and act in seconds, humans take minutes
5. **The analysis pays for itself**: One prevented incident justifies the implementation effort

## Quiz

### Question 1
What's the key difference between canary and blue-green deployments?

<details>
<summary>Show Answer</summary>

**Canary**: Gradually shifts traffic from old to new (e.g., 10% → 30% → 60% → 100%). Both versions run simultaneously with controlled traffic split. Good for: detecting problems with minimal user impact.

**Blue-Green**: Maintains two complete environments. Traffic switches 100% at once (0% → 100%). Good for: instant rollback, testing full environment before switch.

Trade-offs:
- Canary uses fewer resources (one set of pods scaled up/down)
- Blue-Green requires double capacity but offers instant rollback
- Canary detects issues gradually; blue-green is all-or-nothing
</details>

### Question 2
Your analysis template uses `count: 3` and `interval: 1m`. How long will the analysis run before passing?

<details>
<summary>Show Answer</summary>

At least 3 minutes (3 runs × 1 minute apart).

The analysis runs every minute for 3 iterations:
- t=0: First measurement
- t=1m: Second measurement
- t=2m: Third measurement
- t=2m+: Analysis completes if all passed

If any measurement fails and `failureLimit` is reached, analysis fails immediately. If not, it retries until `count` successes are achieved or `failureLimit` is exceeded.
</details>

### Question 3
Write a PromQL query for analysis that checks if error rate is below 1% for a canary service.

<details>
<summary>Show Answer</summary>

```yaml
query: |
  sum(rate(
    http_requests_total{
      service="{{args.service-name}}",
      status=~"5.."
    }[2m]
  )) /
  sum(rate(
    http_requests_total{
      service="{{args.service-name}}"
    }[2m]
  )) < 0.01

# Or as successCondition:
successCondition: result[0] < 0.01
query: |
  sum(rate(http_requests_total{service="{{args.service-name}}",status=~"5.."}[2m])) /
  sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
```

Key points:
- Use `rate()` for per-second rates
- Time range (2m) should be 2x the analysis interval
- Compare 5xx status codes to total requests
- Threshold of 0.01 = 1%
</details>

### Question 4
Your rollout is stuck in "Paused" state. What commands would you use to investigate and resolve?

<details>
<summary>Show Answer</summary>

```bash
# See detailed status and reason for pause
kubectl argo rollouts get rollout my-app

# Check analysis runs
kubectl argo rollouts get rollout my-app --watch

# If analysis failed, check why
kubectl get analysisruns -l rollout=my-app

# View analysis run details
kubectl describe analysisrun <name>

# Options to resolve:
# 1. If pause is intentional (manual gate):
kubectl argo rollouts promote my-app

# 2. If analysis failed, fix and retry:
kubectl argo rollouts retry rollout my-app

# 3. If you want to abort and rollback:
kubectl argo rollouts abort my-app

# 4. Force to stable version:
kubectl argo rollouts undo my-app
```
</details>

### Question 5
You're using a canary strategy with NGINX Ingress for traffic splitting. Your canary is at 30% but monitoring shows it's receiving 50% of traffic. What's wrong?

<details>
<summary>Show Answer</summary>

**Common causes for traffic split mismatch:**

1. **Pod ratio vs traffic weight**: Without a traffic router, Argo Rollouts scales pods proportionally. With 5 replicas at 30% canary:
   - Stable: 3-4 pods
   - Canary: 1-2 pods
   - Kubernetes round-robin = ~30-40% traffic

   But if HPA or manual scaling changed pod counts, the ratio shifts.

2. **Missing ingress annotation**: NGINX traffic splitting requires the correct annotation:
   ```yaml
   trafficRouting:
     nginx:
       stableIngress: my-app-ingress
       annotationPrefix: nginx.ingress.kubernetes.io
   ```
   Without it, traffic routes to both services equally.

3. **Session affinity**: If sticky sessions are enabled, returning users often hit the same version, skewing observed percentages.

4. **Health check traffic**: Kubernetes probes hit all pods equally, inflating canary traffic in metrics.

**Debug steps:**
```bash
# Check ingress annotations
kubectl get ingress my-app-ingress -o yaml | grep -A5 annotations

# Verify canary service selector
kubectl get svc my-app-canary -o yaml

# Check rollout's view of traffic
kubectl argo rollouts get rollout my-app
```
</details>

### Question 6
Design an analysis template that checks THREE conditions: error rate < 1%, p99 latency < 500ms, AND successful health checks. All must pass.

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: comprehensive-check
spec:
  args:
    - name: service-name
    - name: namespace

  metrics:
    # Check 1: Error rate < 1%
    - name: error-rate
      interval: 1m
      count: 5
      successCondition: result[0] < 0.01
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{
              service="{{args.service-name}}",
              namespace="{{args.namespace}}",
              status=~"5.."
            }[2m])) /
            sum(rate(http_requests_total{
              service="{{args.service-name}}",
              namespace="{{args.namespace}}"
            }[2m]))

    # Check 2: P99 latency < 500ms
    - name: p99-latency
      interval: 1m
      count: 5
      successCondition: result[0] < 500
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_ms_bucket{
                service="{{args.service-name}}",
                namespace="{{args.namespace}}"
              }[2m])) by (le)
            )

    # Check 3: Health endpoint returns 200
    - name: health-check
      interval: 30s
      count: 10
      successCondition: result.status == "200"
      failureLimit: 1
      provider:
        web:
          url: "http://{{args.service-name}}.{{args.namespace}}.svc.cluster.local/health"
          method: GET
          jsonPath: "{$.status}"
```

All three metrics run in parallel. The analysis passes only if ALL metrics succeed within their failure limits.
</details>

### Question 7
Your company requires that production deployments be approved by a team lead before reaching 50% traffic. How do you configure this in Argo Rollouts?

<details>
<summary>Show Answer</summary>

Use **infinite pause** at the approval checkpoint:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  strategy:
    canary:
      steps:
        # Automated: Start canary
        - setWeight: 10
        - pause: {duration: 5m}
        - analysis:
            templates:
              - templateName: success-rate

        # Automated: If analysis passes, go to 30%
        - setWeight: 30
        - pause: {duration: 10m}

        # MANUAL APPROVAL REQUIRED
        - pause: {}  # ← Infinite pause

        # After approval: Continue to 50%+
        - setWeight: 50
        - pause: {duration: 5m}
        - setWeight: 75
        - pause: {duration: 5m}
        - setWeight: 100
```

**Approval workflow:**

```bash
# 1. Rollout reaches 30% and pauses
kubectl argo rollouts get rollout my-app
# Status: Paused - CanaryPauseStep

# 2. Team lead reviews metrics, approves
kubectl argo rollouts promote my-app

# 3. Rollout continues to 50%+
```

**Alternative: Notifications + manual gate:**

```yaml
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-rollout-step-completed.slack: approvals-channel
```

This posts to Slack when the pause is reached, alerting approvers.
</details>

### Question 8
Calculate the blast radius for a canary deployment with these parameters: 10,000 requests/second, 10% canary weight, 5-minute analysis interval, and analysis fails on 3rd check. How many requests hit the bad version?

<details>
<summary>Show Answer</summary>

**Calculation:**

```
BLAST RADIUS CALCULATION
─────────────────────────────────────────────────────────────────
Total traffic:           10,000 req/s
Canary weight:           10%
Canary traffic:          1,000 req/s

Analysis configuration:
- interval: 1m (assumed)
- count: 5 (5 checks to pass)
- failureLimit: 3 (assumed)

Timeline to failure:
- Check 1 (t=1m): Pass
- Check 2 (t=2m): Pass
- Check 3 (t=3m): FAIL
- Check 4 (t=4m): FAIL
- Check 5 (t=5m): FAIL ← Analysis fails, rollback triggered

Time at canary weight: ~5 minutes
Requests to canary: 1,000 req/s × 300 seconds = 300,000 requests

BLAST RADIUS: 300,000 requests (3% of 5-minute total)
```

**Compare to rolling update:**

```
ROLLING UPDATE (NO CANARY)
─────────────────────────────────────────────────────────────────
Time to 100%:            ~2 minutes (typical rolling update)
Time to detect:          +5 minutes (alert fires)
Time to rollback:        +3 minutes (human response + rollback)

Total exposure:          10 minutes at 100% traffic
Requests affected:       10,000 × 600 = 6,000,000 requests

Rolling update blast radius: 6,000,000 requests
Canary blast radius:        300,000 requests

RISK REDUCTION: 95%
```

**Key insight:** Canary at 10% with 5-minute analysis exposes 20× fewer users than a rolling update with the same detection time.
</details>

## Hands-On Exercise

### Scenario: Progressive Delivery Pipeline

Implement a canary deployment with automated analysis.

### Setup

```bash
# Create kind cluster
kind create cluster --name rollouts-lab

# Install Argo Rollouts
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install Prometheus for analysis
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=false

# Wait for components
kubectl -n argo-rollouts wait --for=condition=ready pod -l app.kubernetes.io/name=argo-rollouts --timeout=120s
```

### Deploy Demo Application

```yaml
# rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: demo-rollout
spec:
  replicas: 5
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      containers:
        - name: demo
          image: argoproj/rollouts-demo:blue
          ports:
            - containerPort: 8080

  strategy:
    canary:
      canaryService: demo-canary
      stableService: demo-stable

      steps:
        - setWeight: 20
        - pause: {duration: 30s}
        - setWeight: 50
        - pause: {duration: 30s}
        - setWeight: 80
        - pause: {duration: 30s}
---
apiVersion: v1
kind: Service
metadata:
  name: demo-stable
spec:
  selector:
    app: demo
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: demo-canary
spec:
  selector:
    app: demo
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl apply -f rollout.yaml

# Watch the rollout
kubectl argo rollouts get rollout demo-rollout --watch
```

### Trigger a New Release

```bash
# Update to new image (yellow version)
kubectl argo rollouts set image demo-rollout demo=argoproj/rollouts-demo:yellow

# Watch the canary progress
kubectl argo rollouts get rollout demo-rollout --watch
```

### Add Analysis

```yaml
# analysis.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: always-pass
spec:
  metrics:
    - name: always-pass
      count: 3
      interval: 10s
      successCondition: result == "true"
      provider:
        job:
          spec:
            template:
              spec:
                containers:
                  - name: check
                    image: busybox
                    command: [sh, -c, 'echo "true"']
                restartPolicy: Never
            backoffLimit: 0
```

```bash
kubectl apply -f analysis.yaml

# Update rollout to use analysis
kubectl patch rollout demo-rollout --type merge -p '
spec:
  strategy:
    canary:
      analysis:
        templates:
          - templateName: always-pass
'

# Trigger new rollout
kubectl argo rollouts set image demo-rollout demo=argoproj/rollouts-demo:green

# Watch analysis
kubectl argo rollouts get rollout demo-rollout --watch
```

### Test Rollback

```bash
# Abort during rollout
kubectl argo rollouts set image demo-rollout demo=argoproj/rollouts-demo:red

# While in progress, abort
kubectl argo rollouts abort demo-rollout

# Check that pods rolled back
kubectl argo rollouts get rollout demo-rollout
```

### Success Criteria

- [ ] Argo Rollouts controller is running
- [ ] Can perform canary deployment with weight steps
- [ ] Can observe rollout progress with CLI
- [ ] Analysis runs and affects promotion
- [ ] Can abort and rollback a rollout

### Cleanup

```bash
kind delete cluster --name rollouts-lab
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain why progressive delivery reduces blast radius (traffic percentage × detection time)
- [ ] Choose between canary and blue-green strategies based on traffic routing capabilities
- [ ] Write a Rollout spec with setWeight, pause, and analysis steps
- [ ] Create AnalysisTemplates with Prometheus queries and success conditions
- [ ] Calculate blast radius: (traffic % × requests/sec × time-to-detect)
- [ ] Configure traffic routing with NGINX, Istio, or pod-based splitting
- [ ] Use the Argo Rollouts CLI: get, promote, abort, retry, undo
- [ ] Design multi-metric analysis checking error rate, latency, and health
- [ ] Implement manual approval gates with infinite pause steps
- [ ] Troubleshoot common issues: traffic mismatch, stuck pauses, analysis failures

## Next Module

Continue to [Module 2.3: Flux](../module-2.3-flux/) where we'll explore the alternative GitOps toolkit approach.

---

*"Ship fast, but ship safe. Progressive delivery lets you have both."*

## Sources

- [Argo Rollouts Analysis and Progressive Delivery](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/) — Backs canary and blue-green rollout behavior, AnalysisTemplate and AnalysisRun CRDs, Prometheus-driven automated analysis, abort conditions, experiments, and progressive delivery control beyond native Deployments.
- [https://argo-rollouts.readthedocs.io/en/stable/features/bluegreen/](https://argo-rollouts.readthedocs.io/en/stable/features/bluegreen/) — The blue-green sequence of events shows the preview ReplicaSet running before promotion and the old ReplicaSet scaling down only after the switch and delay.
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — Use this as the baseline for native rolling-update behavior that Argo Rollouts extends.

---
title: "Module 2.2: Argo Rollouts"
slug: platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts
sidebar:
  order: 3
---

# Module 2.2: Argo Rollouts

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-65 min

## Prerequisites

Before starting this module, you should already be comfortable with Kubernetes Deployments, ReplicaSets, Services, labels, selectors, and the reason GitOps teams prefer declarative changes over manual cluster edits.

You should also have completed [Module 2.1: ArgoCD](../module-2.1-argocd/) or have equivalent experience with reconciliation loops, desired state, application sync, and the difference between committing a manifest and forcing a runtime change.

This module assumes you can read basic Prometheus queries, but it does not assume you can design production-grade canary analysis yet. We will build that skill progressively, starting with a plain Rollout and adding traffic control, pauses, and analysis only after the earlier pieces are clear.

For commands, examples start with the full `kubectl` command. After the alias is introduced, `k` means `kubectl`; configure it with `alias k=kubectl` in your shell if you want to follow the shorter commands exactly.

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a canary or blue-green rollout strategy that matches a service's traffic profile, rollback needs, and operational risk tolerance.
- **Debug** paused, degraded, or aborted Argo Rollouts by inspecting Rollout status, AnalysisRuns, ReplicaSets, Services, and traffic-routing resources.
- **Implement** a progressively safer Rollout by starting with weight and pause steps, then adding manual gates, job-based analysis, and Prometheus-backed metrics.
- **Evaluate** whether pod-ratio routing, ingress routing, service mesh routing, or blue-green switching is the right control mechanism for a production release.
- **Compare** native Kubernetes Deployments with Argo Rollouts and justify when the extra controller, plugin, metrics, and operating model are worth the complexity.

## Why This Module Matters

A staff engineer at a busy marketplace watches a normal Kubernetes Deployment roll forward during peak traffic. The pods become Ready, the rolling update completes, and the deployment controller reports success. Ten minutes later, customer support reports checkout failures that never appeared in staging because the bug only emerges under production traffic mix, real cache pressure, and real payment-provider latency.

That team did not fail because Kubernetes was broken. Kubernetes did exactly what it was asked to do: replace old pods with new pods while keeping enough replicas available. The missing question was not "are the pods running?" but "is the new version serving users safely enough to continue?" Native Deployments do not answer that product and reliability question, because readiness is a scheduling signal rather than a release-quality decision.

Argo Rollouts adds a progressive delivery controller beside the normal Kubernetes controllers. It can expose a small slice of traffic to a new version, pause while metrics accumulate, run automated analysis, promote when evidence is good, and abort when evidence is bad. The value is not the YAML itself; the value is turning a release from a hopeful replacement into a controlled experiment with bounded blast radius.

This module starts with the simplest useful mental model: a Rollout is a Deployment-shaped object with a smarter strategy section. From there, we add the pieces in a deliberate order. First you will see how traffic moves, then how humans approve a gate, then how automated analysis works, and only then how senior teams combine metrics, routing layers, and rollback policy into a production design.

## Core Section 1: From Rolling Updates to Progressive Delivery

Kubernetes Deployments are excellent at converging pods from one template to another. They compare the desired pod template with existing ReplicaSets, create a new ReplicaSet, and scale old and new replicas according to `maxSurge` and `maxUnavailable`. That solves availability during replacement, but it does not solve release validation because the controller does not know whether conversion rates dropped, p99 latency spiked, or one customer segment started failing.

Argo Rollouts keeps the familiar Deployment shape but replaces the rollout decision engine. Instead of moving directly from old ReplicaSet to new ReplicaSet, it creates checkpoints where the rollout can pause, gather evidence, and decide whether to continue. This is why progressive delivery is a control system rather than a different packaging format.

```ascii
NATIVE KUBERNETES DEPLOYMENT
──────────────────────────────────────────────────────────────────────────────
Desired image changes from v1 to v2.

┌──────────────┐      creates       ┌──────────────┐      scales       ┌──────────────┐
│ Deployment   │ ─────────────────▶ │ ReplicaSet v2│ ───────────────▶ │ Pods v2      │
│ strategy:    │                    │              │                  │ become Ready │
│ RollingUpdate│                    └──────────────┘                  └──────────────┘
└──────┬───────┘
       │
       │ scales down
       ▼
┌──────────────┐
│ ReplicaSet v1│
│ old pods     │
└──────────────┘

Decision signal: pod readiness and availability.
Missing signal: service quality, business health, user impact, traffic slice.
```

```ascii
ARGO ROLLOUTS PROGRESSIVE DELIVERY
──────────────────────────────────────────────────────────────────────────────
Desired image changes from v1 to v2.

┌──────────────┐      creates       ┌──────────────┐
│ Rollout      │ ─────────────────▶ │ ReplicaSet v2│
│ strategy:    │                    │ canary pods  │
│ canary       │                    └──────┬───────┘
└──────┬───────┘                           │
       │                                   │ receives a controlled share
       │                                   ▼
       │                            ┌──────────────┐
       │                            │ Metrics and  │
       │                            │ AnalysisRuns │
       │                            └──────┬───────┘
       │                                   │
       ├──────────── continue if healthy ◀─┤
       │
       └──────────── abort if unhealthy ──▶ stable ReplicaSet remains serving users

Decision signal: readiness plus traffic weight, pauses, metric analysis, and policy.
```

The most important distinction is that a Rollout can make release progress conditional. A Deployment treats a Ready pod as enough evidence to keep replacing replicas. A Rollout can treat a Ready pod as only the first gate, then require request success rate, latency, memory growth, smoke tests, or manual approval before more traffic moves.

> **Pause and predict:** If a new pod passes readiness but starts returning HTTP 500 responses for one customer path, which controller is more likely to stop the release before most users are affected: a native Deployment or an Argo Rollout with request metrics? Write down the signal each controller can actually observe before you continue.

Progressive delivery has two main patterns in Argo Rollouts: canary and blue-green. A canary release exposes a small percentage of traffic to the new version and expands that percentage over time. A blue-green release runs a complete preview version, validates it, and then switches active traffic in one promotion event.

```ascii
CANARY RELEASE SHAPE
──────────────────────────────────────────────────────────────────────────────
Time moves left to right.

Traffic:
stable v1  100% ────── 90% ────── 75% ────── 50% ────── 0%
canary v2    0% ────── 10% ────── 25% ────── 50% ────── 100%

Control points:
            pause       analysis    pause       analysis    promote
```

```ascii
BLUE-GREEN RELEASE SHAPE
──────────────────────────────────────────────────────────────────────────────
Before promotion:

             ┌──────────────────────┐
users ─────▶ │ active Service        │ ─────▶ blue pods, image v1
             └──────────────────────┘

             ┌──────────────────────┐
testers ───▶ │ preview Service       │ ─────▶ green pods, image v2
             └──────────────────────┘

After promotion:

             ┌──────────────────────┐
users ─────▶ │ active Service        │ ─────▶ green pods, image v2
             └──────────────────────┘

             blue pods are kept briefly for rollback, then scaled down by policy.
```

Canary is usually the better fit when you can split traffic reliably and want gradual exposure. Blue-green is often better when a version must be tested as a whole environment, when traffic percentages are hard to enforce, or when instant rollback is more important than gradual learning. Neither pattern is automatically safer; the safer pattern is the one whose assumptions match your routing layer, metrics quality, capacity, and approval process.

| Release Pattern | Primary Control | Best Fit | Main Trade-Off |
|---|---|---|---|
| Native rolling update | Replica replacement | Low-risk internal services with strong tests and simple rollback needs | No built-in analysis or traffic gate |
| Canary rollout | Gradual traffic weight | User-facing services where small exposure gives useful evidence | Needs meaningful metrics and routing confidence |
| Blue-green rollout | Service selector switch | Services needing full-environment preview or fast rollback | Requires extra capacity during overlap |
| Manual gated rollout | Human promotion at a pause | Regulated, high-risk, or change-window-driven systems | Human approval can become a queue bottleneck |

A senior rollout design starts by choosing the feedback loop, not by copying a manifest. If the only reliable signal is whether pods start, Argo Rollouts will add little value until observability improves. If the team has trustworthy service-level metrics, the Rollout can turn those metrics into release decisions and reduce both detection time and user exposure.

## Core Section 2: Installing the Controller and the kubectl Plugin

Argo Rollouts has two separate installation concerns: the controller in the cluster and the `kubectl` plugin on an operator's workstation. The controller is the required runtime component because it watches Rollout, AnalysisTemplate, AnalysisRun, and Experiment resources, then creates and scales ReplicaSets according to the strategy. Without the controller, the custom resources may exist in the API server, but nothing will reconcile them into actual rollout behavior.

The `kubectl argo rollouts` plugin is not the controller. It is an operator interface that makes Rollout state readable and gives you commands such as `promote`, `abort`, `retry`, `undo`, and the live dashboard. You can inspect raw resources with normal `kubectl`, but the plugin saves time because it understands the relationship between Rollouts, ReplicaSets, pods, pauses, and AnalysisRuns.

This distinction matters during incident response. If the controller is unhealthy, promotions and aborts may not reconcile even when the plugin command succeeds at sending a request. If the plugin is missing, the Rollout can still progress because the controller is running, but the operator loses the purpose-built view and must inspect lower-level resources manually.

```ascii
INSTALLATION RESPONSIBILITIES
──────────────────────────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────────────────────────┐
│ Cluster                                                                    │
│                                                                            │
│  ┌──────────────────────────┐       watches       ┌─────────────────────┐  │
│  │ argo-rollouts controller │ ──────────────────▶ │ Rollout resources   │  │
│  │ required for reconciliation │                   │ AnalysisRuns        │  │
│  └────────────┬─────────────┘                     └─────────────────────┘  │
│               │                                                            │
│               └──────── creates/scales ReplicaSets and updates status ───▶ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│ Operator workstation                                                       │
│                                                                            │
│  ┌──────────────────────────┐       talks to       ┌─────────────────────┐ │
│  │ kubectl argo rollouts    │ ───────────────────▶ │ Kubernetes API      │ │
│  │ useful for humans        │                      │ via kubeconfig      │ │
│  └──────────────────────────┘                      └─────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Install the controller into its own namespace so the operational boundary is clear. The upstream manifest includes the controller Deployment, service account, RBAC rules, and CustomResourceDefinitions. In production, teams usually pin a release version instead of using `latest`, but a lab can use the latest release URL for simplicity.

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

kubectl -n argo-rollouts wait \
  --for=condition=available deployment/argo-rollouts \
  --timeout=120s
```

Install the plugin on the machine where you run release operations. On macOS with Homebrew, the plugin is packaged as `kubectl-argo-rollouts`, which lets `kubectl` discover it as the subcommand `kubectl argo rollouts`. On Linux, place the executable somewhere on your `PATH` with the same name.

```bash
brew install argoproj/tap/kubectl-argo-rollouts

kubectl argo rollouts version
```

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

kubectl argo rollouts version
```

The normal `kubectl` commands still matter because Rollouts are Kubernetes resources. You will use `kubectl get`, `kubectl describe`, and `kubectl apply` for generic inspection, while the plugin gives you rollout-specific views. A practical operator learns both because plugin output answers "where is the release stuck?" and raw Kubernetes output answers "which object is failing underneath?"

```bash
alias k=kubectl

k get crd | grep rollouts.argoproj.io
k -n argo-rollouts get pods
kubectl argo rollouts version
```

> **Pause and predict:** A teammate says, "The plugin is installed, so the rollout controller must be installed too." What command would prove or disprove that claim? Decide before reading the answer: the plugin version checks your workstation, while `k -n argo-rollouts get deployment argo-rollouts` checks the controller running in the cluster.

A clean installation test verifies both sides. First, confirm the API server knows the Rollout custom resource. Second, confirm the controller pod is Ready. Third, confirm the plugin can talk to the cluster. If any one of those fails, troubleshoot that layer directly rather than reinstalling everything.

## Core Section 3: A Minimal Canary Rollout Before Analysis

The easiest way to understand Argo Rollouts is to start with a Rollout that has no metric analysis. This is not the final production pattern, but it removes extra cognitive load while you learn the object shape. The first mental bridge is simple: a Rollout looks like a Deployment until the `strategy` field, where it defines canary steps instead of a native rolling update policy.

A Rollout owns ReplicaSets just like a Deployment does. The selector must match the pod template labels, and the Service selector must match those same labels. If these three label sets drift apart, the controller can create pods successfully while traffic still goes nowhere useful.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: color-api
spec:
  replicas: 5
  selector:
    matchLabels:
      app: color-api
  template:
    metadata:
      labels:
        app: color-api
    spec:
      containers:
        - name: color-api
          image: argoproj/rollouts-demo:blue
          ports:
            - containerPort: 8080
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {duration: 60s}
        - setWeight: 50
        - pause: {duration: 60s}
        - setWeight: 100
---
apiVersion: v1
kind: Service
metadata:
  name: color-api
spec:
  selector:
    app: color-api
  ports:
    - port: 80
      targetPort: 8080
```

Apply this manifest exactly as you would apply any Kubernetes resource. The first deployment becomes stable because there is no previous version to compare against. The canary behavior appears when you change the pod template, usually by changing the container image or an environment variable.

```bash
k apply -f color-rollout.yaml
kubectl argo rollouts get rollout color-api

kubectl argo rollouts set image color-api color-api=argoproj/rollouts-demo:yellow
kubectl argo rollouts get rollout color-api --watch
```

The `setWeight` field means "move the rollout to this target canary percentage." If you do not configure an ingress controller or service mesh for traffic routing, Argo Rollouts approximates the weight by scaling stable and canary ReplicaSets. With five replicas and a twenty percent canary, that often means one canary pod and four stable pods, which is close enough for a lab but not precise for high-stakes user traffic.

```ascii
POD-RATIO CANARY WITHOUT TRAFFIC ROUTER
──────────────────────────────────────────────────────────────────────────────
Rollout target: 20% canary
Replica count: 5

┌────────────────────────────────────────────────────────────────────────────┐
│ Service selector: app=color-api                                            │
│                                                                            │
│  stable ReplicaSet, image blue       canary ReplicaSet, image yellow        │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐        ┌────┐                                │
│  │ v1 │ │ v1 │ │ v1 │ │ v1 │        │ v2 │                                │
│  └────┘ └────┘ └────┘ └────┘        └────┘                                │
│                                                                            │
│ Kubernetes Service load-balances across ready endpoints.                   │
└────────────────────────────────────────────────────────────────────────────┘
```

This approximation is useful but limited. It assumes traffic is evenly distributed across pods, that each pod has similar capacity, and that clients do not create sticky or long-lived connections that skew request distribution. For many HTTP services, it is acceptable during early adoption; for services with strict blast-radius requirements, a real traffic router is usually needed.

A pause step is a deliberate stop in the release sequence. A duration pause resumes automatically after time passes, while an empty pause waits for a human promotion. Manual pauses are useful when a team needs a lead engineer, product owner, or incident commander to inspect dashboards before traffic crosses a threshold.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: color-api
spec:
  replicas: 5
  selector:
    matchLabels:
      app: color-api
  template:
    metadata:
      labels:
        app: color-api
    spec:
      containers:
        - name: color-api
          image: argoproj/rollouts-demo:blue
          ports:
            - containerPort: 8080
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: {duration: 2m}
        - setWeight: 25
        - pause: {}
        - setWeight: 50
        - pause: {duration: 2m}
        - setWeight: 100
```

```bash
kubectl argo rollouts get rollout color-api
kubectl argo rollouts promote color-api
kubectl argo rollouts abort color-api
```

> **Design checkpoint:** Your team wants an engineer to approve before the release reaches half of production traffic. Place the empty pause before or after `setWeight: 50`? The safer answer is before the weight increase, because the approval should happen while the canary is still below the threshold being governed.

A worked example makes the planning process concrete. Suppose `checkout-api` serves 8,000 requests per second, and the team can tolerate at most 120,000 requests reaching a bad version before an automatic abort. A ten percent canary receives about 800 requests per second, so a two-minute observation window exposes roughly 96,000 canary requests. That is inside the limit, while a five-minute window at the same weight would expose about 240,000 requests.

```ascii
BLAST-RADIUS WORKED EXAMPLE
──────────────────────────────────────────────────────────────────────────────
Total traffic:              8,000 requests/second
Canary weight:              10%
Canary traffic:             800 requests/second
Observation window:         120 seconds

Estimated exposed requests: 800 * 120 = 96,000 requests
Risk budget:                120,000 requests

Decision: 10% for 2 minutes fits the stated risk budget.
```

That calculation is intentionally simple, but it teaches the right instinct. A rollout step is not just a percentage in YAML; it is an exposure decision. Senior teams reason about canary weight, duration, detection speed, and rollback speed together because user impact is the product of all four.

## Core Section 4: Traffic Routing and Blue-Green Switching

Canary routing becomes more precise when Argo Rollouts can program a traffic manager. Instead of relying on pod counts to approximate percentages, the controller updates an ingress, service mesh, or load balancer integration so the routing layer sends a defined share of requests to the canary Service. This separation matters because replica count controls capacity, while traffic weight controls exposure.

A traffic-routed canary normally uses two Services: one stable and one canary. Argo Rollouts updates selectors on those Services so the stable Service points at the stable ReplicaSet and the canary Service points at the canary ReplicaSet. The ingress or mesh then splits traffic between those Services according to rollout weight.

```ascii
TRAFFIC-ROUTED CANARY
──────────────────────────────────────────────────────────────────────────────
                         ┌────────────────────────────┐
users ─────────────────▶ │ Ingress or service mesh    │
                         │ weight: stable 90, canary 10│
                         └──────────────┬─────────────┘
                                        │
                      ┌─────────────────┴─────────────────┐
                      │                                   │
                      ▼                                   ▼
             ┌────────────────┐                 ┌────────────────┐
             │ stable Service │                 │ canary Service │
             └───────┬────────┘                 └───────┬────────┘
                     │                                  │
                     ▼                                  ▼
             ┌────────────────┐                 ┌────────────────┐
             │ ReplicaSet v1  │                 │ ReplicaSet v2  │
             └────────────────┘                 └────────────────┘
```

The following example shows the Rollout fields for NGINX Ingress traffic splitting. The `stableIngress` is the existing user-facing Ingress, while the two Services are controlled by Rollouts. In a real cluster, the Ingress object must already route to the stable Service, and the NGINX controller must support the annotations Argo Rollouts writes.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: color-api
spec:
  replicas: 6
  selector:
    matchLabels:
      app: color-api
  template:
    metadata:
      labels:
        app: color-api
    spec:
      containers:
        - name: color-api
          image: argoproj/rollouts-demo:blue
          ports:
            - containerPort: 8080
  strategy:
    canary:
      stableService: color-api-stable
      canaryService: color-api-canary
      trafficRouting:
        nginx:
          stableIngress: color-api
          annotationPrefix: nginx.ingress.kubernetes.io
      steps:
        - setWeight: 10
        - pause: {duration: 2m}
        - setWeight: 25
        - pause: {duration: 3m}
        - setWeight: 50
        - pause: {}
        - setWeight: 100
---
apiVersion: v1
kind: Service
metadata:
  name: color-api-stable
spec:
  selector:
    app: color-api
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: color-api-canary
spec:
  selector:
    app: color-api
  ports:
    - port: 80
      targetPort: 8080
```

Traffic routing adds power, but it also adds a new failure surface. If the Rollout looks correct and the traffic percentage is wrong, inspect the integration resource rather than only staring at pods. The problem may be missing annotations, a mismatched ingress name, a service selector issue, session affinity, long-lived connections, or metrics that count probes rather than user requests.

| Routing Mode | How Weight Is Enforced | What To Verify During Debugging | Practical Risk |
|---|---|---|---|
| Pod-ratio canary | Stable and canary ReplicaSet sizes approximate weight | Replica counts, HPA behavior, Service endpoints | Percentages drift with uneven traffic |
| NGINX Ingress | Controller annotations split traffic between Services | Ingress annotations, stableIngress name, canary Service | Annotation mismatch causes wrong routing |
| Istio or mesh | VirtualService or mesh routing sends weighted traffic | Route destinations, subsets, sidecar health | Mesh config can override rollout intent |
| AWS ALB or load balancer | Load balancer rules split traffic by service target | Ingress rules, target groups, health checks | External controller timing affects rollout |
| Blue-green Services | Active Service selector switches to preview ReplicaSet | activeService, previewService, scale-down delay | Needs spare capacity during preview |

Blue-green uses Services differently from a canary. Instead of splitting traffic by percentage, it maintains an active Service for users and a preview Service for validation. When promotion happens, Argo Rollouts changes the active Service selector to point at the new ReplicaSet, creating a fast switch from old to new.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: color-api
spec:
  replicas: 4
  selector:
    matchLabels:
      app: color-api
  template:
    metadata:
      labels:
        app: color-api
    spec:
      containers:
        - name: color-api
          image: argoproj/rollouts-demo:blue
          ports:
            - containerPort: 8080
  strategy:
    blueGreen:
      activeService: color-api-active
      previewService: color-api-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 120
---
apiVersion: v1
kind: Service
metadata:
  name: color-api-active
spec:
  selector:
    app: color-api
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: color-api-preview
spec:
  selector:
    app: color-api
  ports:
    - port: 80
      targetPort: 8080
```

The `scaleDownDelaySeconds` field is more than cleanup timing. It gives the routing layer time to stop sending traffic to old pods and preserves a rollback window while connections drain. Too short a delay can make rollback less reliable; too long a delay consumes capacity and can hide resource pressure until several releases overlap.

> **Pause and predict:** A blue-green rollout has `autoPromotionEnabled: false`, and the preview pods are Ready. Users still see the old version. Is that failure or expected behavior? It is expected behavior because preview readiness only prepares the new ReplicaSet; promotion is the action that switches active traffic.

Blue-green can also use analysis before and after promotion. Pre-promotion analysis checks the preview version before users see it, which is useful for smoke tests and synthetic checks. Post-promotion analysis checks real user traffic after the switch, which is useful because some defects only appear under production traffic patterns.

```yaml
strategy:
  blueGreen:
    activeService: color-api-active
    previewService: color-api-preview
    autoPromotionEnabled: false
    scaleDownDelaySeconds: 120
    prePromotionAnalysis:
      templates:
        - templateName: smoke-check
      args:
        - name: service-url
          value: http://color-api-preview.default.svc.cluster.local
    postPromotionAnalysis:
      templates:
        - templateName: success-rate
      args:
        - name: service-name
          value: color-api-active
```

A senior design often combines blue-green with manual promotion for risky database-compatible changes, schema migrations, or external dependency upgrades. Canary is stronger when the main question is "how does the new version behave under a small share of live traffic?" Blue-green is stronger when the main question is "can the new complete environment pass validation before any user traffic moves?"

## Core Section 5: AnalysisTemplates One Layer at a Time

AnalysisTemplates are where Argo Rollouts becomes evidence-driven instead of merely staged. An AnalysisTemplate defines one or more metrics, each with a provider, interval, count, and success condition. A Rollout creates AnalysisRuns from those templates, injects arguments, and then uses the result to continue, pause, fail, or abort depending on the strategy configuration.

The mental jump from `setWeight` to a complex Prometheus template can feel large, so we will build analysis in layers. First, use a job-based template that always passes so you can see the mechanics. Next, introduce a realistic smoke test. Then add Prometheus success rate, latency, and multi-metric behavior.

```ascii
ANALYSIS SCAFFOLDING LADDER
──────────────────────────────────────────────────────────────────────────────
Layer 1: Rollout steps only
         setWeight -> pause -> setWeight

Layer 2: Manual gate
         setWeight -> pause {} -> human promote

Layer 3: Simple AnalysisTemplate
         run a Kubernetes Job that returns success or failure

Layer 4: Service metric analysis
         query Prometheus for success rate or latency

Layer 5: Multi-signal production analysis
         combine error rate, latency, saturation, and business checks
```

The simplest useful AnalysisTemplate can run a Kubernetes Job. This teaches the structure without requiring Prometheus or a service mesh. The Job exits successfully, and the Rollout treats that metric as passed.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: smoke-check
spec:
  args:
    - name: service-url
  metrics:
    - name: http-smoke-check
      count: 3
      interval: 20s
      successCondition: result == "ok"
      failureLimit: 1
      provider:
        job:
          spec:
            template:
              spec:
                containers:
                  - name: check
                    image: curlimages/curl:8.8.0
                    command:
                      - sh
                      - -c
                      - |
                        curl -fsS "{{args.service-url}}/" >/dev/null
                        echo ok
                restartPolicy: Never
            backoffLimit: 0
```

Use this template inline as a canary step when you want the analysis to block the next step. Inline analysis is easier to reason about because the rollout sequence stops at the analysis step and waits for the result. This is a good first production pattern for smoke checks, migration checks, and short synthetic validation.

```yaml
strategy:
  canary:
    stableService: color-api-stable
    canaryService: color-api-canary
    steps:
      - setWeight: 10
      - pause: {duration: 60s}
      - analysis:
          templates:
            - templateName: smoke-check
          args:
            - name: service-url
              value: http://color-api-canary.default.svc.cluster.local
      - setWeight: 50
      - pause: {}
      - setWeight: 100
```

Background analysis starts separately from the step list and runs while the canary progresses. It is useful when a metric needs multiple samples across time, such as success rate, latency, memory growth, or queue depth. The trade-off is that the learner and operator must understand two timelines: rollout steps and analysis measurements.

```yaml
strategy:
  canary:
    stableService: color-api-stable
    canaryService: color-api-canary
    analysis:
      startingStep: 1
      templates:
        - templateName: success-rate
      args:
        - name: service-name
          value: color-api-canary
    steps:
      - setWeight: 10
      - pause: {duration: 2m}
      - setWeight: 25
      - pause: {duration: 3m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 100
```

> **Pause and predict:** If background analysis starts at step one and fails while the rollout is paused at twenty-five percent, what should happen next? The rollout should become degraded or abort according to failure policy, because the analysis is not just reporting; it is part of the release decision.

A Prometheus metric template introduces three new ideas at once: a query returns data, the success condition interprets that data, and limits decide how many bad samples are tolerated. Keep those ideas separate. The query asks "what happened?" The success condition asks "is that acceptable?" The `failureLimit` asks "how much bad evidence is enough to stop?"

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
    - name: namespace
      value: default
    - name: threshold
      value: "0.99"
  metrics:
    - name: http-success-rate
      interval: 1m
      count: 5
      successCondition: result[0] >= {{args.threshold}}
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus-kube-prometheus-prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{
              service="{{args.service-name}}",
              namespace="{{args.namespace}}",
              status=~"2..|3.."
            }[2m])) /
            sum(rate(http_requests_total{
              service="{{args.service-name}}",
              namespace="{{args.namespace}}"
            }[2m]))
```

The query window should usually be longer than the scrape interval and at least as long as the analysis interval. If the window is too short, a single scrape or traffic burst can create noisy results. If the window is too long, the canary may continue serving bad traffic while the metric slowly catches up.

Latency analysis is similar, but histogram queries demand more care. The unit must match the threshold, and the aggregation must preserve the `le` label for `histogram_quantile`. A common production mistake is comparing seconds to milliseconds or aggregating away the bucket boundary label.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: p99-latency
spec:
  args:
    - name: service-name
    - name: namespace
      value: default
    - name: threshold-ms
      value: "500"
  metrics:
    - name: p99-latency-ms
      interval: 1m
      count: 5
      successCondition: result[0] < {{args.threshold-ms}}
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus-kube-prometheus-prometheus.monitoring:9090
          query: |
            histogram_quantile(
              0.99,
              sum(rate(http_request_duration_seconds_bucket{
                service="{{args.service-name}}",
                namespace="{{args.namespace}}"
              }[2m])) by (le)
            ) * 1000
```

A multi-metric analysis passes only when every required metric stays within its success criteria. This is powerful because user impact is rarely captured by one number. A canary with low error rate but terrible latency is still bad; a canary with good HTTP metrics but failing background jobs may still be unsafe.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: release-health
spec:
  args:
    - name: service-name
    - name: namespace
      value: default
  metrics:
    - name: error-rate
      interval: 1m
      count: 5
      successCondition: result[0] < 0.01
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus-kube-prometheus-prometheus.monitoring:9090
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
    - name: p99-latency-ms
      interval: 1m
      count: 5
      successCondition: result[0] < 500
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus-kube-prometheus-prometheus.monitoring:9090
          query: |
            histogram_quantile(
              0.99,
              sum(rate(http_request_duration_seconds_bucket{
                service="{{args.service-name}}",
                namespace="{{args.namespace}}"
              }[2m])) by (le)
            ) * 1000
    - name: smoke-check
      interval: 30s
      count: 5
      successCondition: result == "ok"
      failureLimit: 1
      provider:
        job:
          spec:
            template:
              spec:
                containers:
                  - name: check
                    image: curlimages/curl:8.8.0
                    command:
                      - sh
                      - -c
                      - |
                        curl -fsS "http://{{args.service-name}}.{{args.namespace}}.svc.cluster.local/" >/dev/null
                        echo ok
                restartPolicy: Never
            backoffLimit: 0
```

A mature AnalysisTemplate has an owner and a hypothesis. "Success rate must stay above ninety-nine percent for five minutes" is a hypothesis about acceptable user impact. "Run every metric we can find" is not a hypothesis; it is noise that can block releases without teaching the team which risk mattered.

Dry-run analysis is useful during adoption because it reports what would have happened without failing the rollout. Use it when a metric is promising but not yet trusted. Remove dry-run once the team has validated the query, threshold, and alerting behavior across several real releases.

```yaml
strategy:
  canary:
    analysis:
      templates:
        - templateName: release-health
      args:
        - name: service-name
          value: color-api-canary
      dryRun:
        - metricName: p99-latency-ms
```

The senior-level move is to align rollout analysis with service-level objectives rather than arbitrary tool defaults. If your SLO is based on successful checkout requests, a canary should probably inspect checkout success and latency, not only pod CPU. Infrastructure metrics explain symptoms, but user-facing metrics decide whether the release is safe.

## Core Section 6: Operating, Debugging, and Making Release Decisions

Operating Argo Rollouts requires reading a release as a chain of objects. The Rollout shows the high-level strategy and status. ReplicaSets show which pod templates exist. Services show which ReplicaSet receives traffic. AnalysisRuns show which evidence was gathered. Ingress or mesh resources show whether traffic weights match the intended rollout step.

```ascii
DEBUGGING MAP
──────────────────────────────────────────────────────────────────────────────
Symptom: rollout is stuck, unhealthy, or routing wrong.

┌──────────────┐
│ Rollout      │  first: desired strategy, current step, phase, message
└──────┬───────┘
       │
       ├──▶ ReplicaSets      pod-template hashes, stable/canary scale
       │
       ├──▶ Pods             readiness, crashes, image pull, app logs
       │
       ├──▶ Services         selectors, endpoints, active/preview mapping
       │
       ├──▶ AnalysisRuns     metric results, provider errors, conditions
       │
       └──▶ Routing layer    ingress annotations, mesh routes, load balancer rules
```

Start with the plugin view because it groups the release tree for humans. If the plugin says the Rollout is paused, determine whether the pause is expected, manual, analysis-related, or caused by progress deadline behavior. Then move to raw Kubernetes resources when you need exact events, selectors, logs, or provider errors.

```bash
kubectl argo rollouts get rollout color-api
kubectl argo rollouts status color-api
kubectl argo rollouts history rollout color-api

k get rollout color-api -o yaml
k get rs -l app=color-api
k get pods -l app=color-api
k get analysisruns
```

When analysis fails, inspect the AnalysisRun before changing the Rollout. The failure could mean the canary is genuinely unhealthy, but it could also mean Prometheus is unreachable, the query returns an empty vector, the metric name changed, or the success condition expects a different data shape. Treat the AnalysisRun as evidence, not as a vague red light.

```bash
k get analysisruns
k describe analysisrun color-api-release-health-1
k logs job/color-api-release-health-1-smoke-check
```

A stuck pause has several possible resolutions. Promote only if the pause is an intentional gate and the evidence supports continuing. Retry only if the failure was transient or the analysis dependency has been fixed. Abort when the canary itself appears unsafe. Undo when the stable revision should be restored from history.

```bash
kubectl argo rollouts promote color-api
kubectl argo rollouts retry rollout color-api
kubectl argo rollouts abort color-api
kubectl argo rollouts undo color-api
```

> **Operational checkpoint:** Your Rollout is paused at twenty-five percent, the service dashboard looks healthy, but the AnalysisRun failed with a Prometheus connection error. Should you promote, retry, or abort? A defensible answer is to fix Prometheus connectivity and retry analysis before promotion, because promoting without the intended evidence weakens the release policy.

Notifications help connect rollout state to team workflow. Argo Rollouts notifications can send messages when rollouts complete, pause, or fail analysis. The important design point is to notify the channel that can act; broadcasting every step to a noisy room trains people to ignore release signals.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: color-api
  annotations:
    notifications.argoproj.io/subscribe.on-rollout-completed.slack: delivery-events
    notifications.argoproj.io/subscribe.on-analysis-run-failed.slack: delivery-alerts
    notifications.argoproj.io/subscribe.on-rollout-step-completed.slack: release-approvals
spec:
  replicas: 5
  selector:
    matchLabels:
      app: color-api
  template:
    metadata:
      labels:
        app: color-api
    spec:
      containers:
        - name: color-api
          image: argoproj/rollouts-demo:blue
          ports:
            - containerPort: 8080
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: {duration: 2m}
        - setWeight: 25
        - pause: {}
        - setWeight: 100
```

Experiments are useful when you need to run multiple versions for comparison without treating one as the immediate stable replacement. In a Rollout, an experiment step can create temporary ReplicaSets and run analysis before any live traffic reaches the canary. This is more advanced than a basic canary, so use it when you have a specific comparison to make, not as a default release ritual.

```yaml
strategy:
  canary:
    steps:
      - setWeight: 0
      - experiment:
          duration: 10m
          templates:
            - name: baseline
              specRef: stable
              replicas: 2
            - name: candidate
              specRef: canary
              replicas: 2
          analyses:
            - name: smoke-check
              templateName: smoke-check
              args:
                - name: service-url
                  value: http://color-api-canary.default.svc.cluster.local
      - setWeight: 10
      - pause: {duration: 2m}
      - setWeight: 100
```

A release decision should end with a clear action and a clear reason. "Promoted because error rate stayed below one percent, p99 latency stayed below five hundred milliseconds, and the checkout smoke test passed" is operationally useful. "Promoted because the Rollout looked fine" is not specific enough to audit or improve later.

The highest-performing teams treat progressive delivery as a learning loop. They review failed rollouts to tune metrics, adjust thresholds, and remove noisy checks. They also review successful rollouts to confirm that analysis duration and canary weights are not needlessly slowing safe changes. Argo Rollouts provides the mechanism; the team still owns the release policy.

## Worked Example: Designing a Production Rollout Policy

Imagine a payments-adjacent API that handles authorization requests. It has high traffic, strong observability, and a hard requirement that no unapproved release may exceed twenty-five percent traffic. The team also knows that the worst historical regressions showed up as increased p99 latency before outright failures.

A reasonable first design uses a small ten percent canary, two minutes of observation, automated success-rate and latency analysis, then a twenty-five percent gate with manual approval. After approval, the rollout moves to half traffic, observes again, and then promotes to full traffic only if analysis continues to pass.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: authorization-api
spec:
  replicas: 12
  selector:
    matchLabels:
      app: authorization-api
  template:
    metadata:
      labels:
        app: authorization-api
    spec:
      containers:
        - name: authorization-api
          image: example.com/platform/authorization-api:2.8.0
          ports:
            - containerPort: 8080
  strategy:
    canary:
      stableService: authorization-api-stable
      canaryService: authorization-api-canary
      analysis:
        startingStep: 1
        templates:
          - templateName: release-health
        args:
          - name: service-name
            value: authorization-api-canary
          - name: namespace
            value: payments
      steps:
        - setWeight: 10
        - pause: {duration: 2m}
        - setWeight: 25
        - pause: {}
        - setWeight: 50
        - pause: {duration: 5m}
        - setWeight: 100
```

The design is defensible because each step maps to a risk. Ten percent limits early blast radius. The first pause gives metrics time to observe real traffic. The empty pause enforces the approval requirement before the threshold is crossed. The fifty percent step validates that the canary still behaves under larger load, while the final promotion only happens after the higher-load observation succeeds.

This is also not the only valid answer. A lower-traffic service might need longer pauses because it takes more time to collect enough requests. A stateless internal service with excellent test coverage might use a faster path. A service with weak metrics might start with manual gates and dry-run analysis until the team trusts the signals.

## Did You Know?

- **Argo Rollouts does not replace Argo CD**: Argo CD syncs desired manifests into the cluster, while Argo Rollouts controls how a changed workload progresses after the manifest is applied.
- **A Rollout can use pod-ratio traffic before adding ingress or mesh routing**: This makes adoption easier, but exact percentage enforcement usually requires a traffic manager.
- **AnalysisRuns are ordinary Kubernetes custom resources**: You can inspect them with `kubectl get`, `kubectl describe`, labels, events, and logs from generated Jobs.
- **Blue-green promotion changes traffic by changing Service targeting**: The old ReplicaSet can remain available for a short rollback window before scale-down policy removes it.

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Installing only the plugin and forgetting the controller | The workstation command exists, but no cluster component reconciles Rollout resources into ReplicaSets and status changes. | Verify the `argo-rollouts` Deployment is available and the CRDs exist before testing release behavior. |
| Treating readiness probes as release analysis | A pod can be Ready while returning bad business results, slow responses, or customer-specific failures. | Use readiness for traffic eligibility and AnalysisTemplates for release-quality decisions based on service metrics. |
| Jumping directly to complex Prometheus templates | Learners and teams cannot debug whether the issue is rollout logic, provider connectivity, query shape, or threshold design. | Start with steps and pauses, then add a simple job analysis, then add one Prometheus metric at a time. |
| Using canary percentages without checking routing mode | Pod-ratio routing may not match exact request percentages, especially with sticky sessions or uneven connection patterns. | Decide whether pod-ratio approximation is acceptable or configure ingress, mesh, or load-balancer traffic routing. |
| Promoting through a failed analysis without investigation | The team trains itself to bypass the safety mechanism whenever it slows delivery. | Inspect the AnalysisRun, determine whether the failure is service health or measurement failure, then retry or abort deliberately. |
| Setting pause durations shorter than metric windows | The rollout may advance before Prometheus has enough fresh samples to evaluate the new version. | Align scrape interval, query range, analysis interval, and pause duration so evidence can accumulate before promotion. |
| Forgetting blue-green capacity requirements | Preview and active versions can run at the same time, which may overload a cluster during promotion windows. | Reserve capacity or use scheduling limits before choosing blue-green for high-replica workloads. |
| Letting notification noise hide important gates | Teams ignore rollout messages when every minor step posts to the same crowded channel. | Send approval gates and failed analysis to actionable channels with clear ownership and response expectations. |

## Quiz

### Question 1

Your team replaced a native Deployment with an Argo Rollout, but the first incident review shows the bad version still reached most users before anyone reacted. The Rollout used `setWeight` and timed pauses, but no AnalysisTemplate and no manual gate. What would you change first, and why?

<details>
<summary>Show Answer</summary>

The first change should be to add a real decision gate, either automated analysis or a manual pause at a meaningful threshold. Weight steps alone slow the release, but they do not evaluate whether the release is safe. If the team has trustworthy metrics, add an AnalysisTemplate for success rate, latency, or the most important user journey. If metrics are not trustworthy yet, add an empty pause before a risky threshold and require an operator to inspect dashboards before promotion.

A strong answer also mentions detection time. A ten percent canary still creates user impact if it runs for a long time without evidence-based evaluation. Progressive delivery reduces blast radius when small exposure is paired with fast detection and decisive abort behavior.
</details>

### Question 2

A teammate reports that `kubectl argo rollouts version` works from their laptop, but `k get rollout` returns "the server doesn't have a resource type rollout." What layer is missing, and how would you verify the fix?

<details>
<summary>Show Answer</summary>

The plugin is installed locally, but the cluster likely does not have the Argo Rollouts CRDs installed. The plugin command proves the workstation has the CLI extension; it does not prove the API server knows the Rollout custom resource or that the controller is running.

Verify the fix by installing the controller manifest, then checking both CRDs and controller availability:

```bash
k get crd | grep rollouts.argoproj.io
k -n argo-rollouts get deployment argo-rollouts
k -n argo-rollouts wait --for=condition=available deployment/argo-rollouts --timeout=120s
```

After that, `k get rollout` should be recognized by the API server.
</details>

### Question 3

Your canary is configured for twenty-five percent traffic, but dashboards show roughly half of requests hitting the new version. The Rollout has no `trafficRouting` section and uses four replicas. What is the likely explanation, and what options do you have?

<details>
<summary>Show Answer</summary>

Without a traffic router, Argo Rollouts approximates canary weight by scaling ReplicaSets. With four replicas, the closest pod ratios are coarse. One canary pod is twenty-five percent by pod count, while two canary pods are half by pod count. Real traffic can drift even more because Services distribute across endpoints, not exact request percentages, and client behavior may be uneven.

Options include increasing replica count for finer pod-ratio approximation, accepting the coarse split for low-risk workloads, or configuring a traffic manager such as NGINX Ingress, Istio, or a supported load balancer. For strict blast-radius control, a traffic router is usually the better answer.
</details>

### Question 4

A blue-green rollout has healthy preview pods and a successful smoke test, but users still reach the old version. The manifest sets `autoPromotionEnabled: false`. The release manager asks whether this is broken. How do you respond and what command would complete the switch?

<details>
<summary>Show Answer</summary>

This is expected behavior. With `autoPromotionEnabled: false`, preview readiness and pre-promotion analysis prepare the new version, but they do not switch user traffic. The active Service remains pointed at the old ReplicaSet until someone promotes the Rollout.

The command to complete the switch is:

```bash
kubectl argo rollouts promote color-api
```

Before running it, verify the smoke test result, preview Service behavior, and any required approval. Promotion is the traffic switch, so it should be treated as the controlled release action.
</details>

### Question 5

Your Prometheus-backed AnalysisRun fails immediately with an empty result, but application dashboards show normal traffic. The query filters on `service="color-api-canary"`, while the metrics use `service="color-api"`. What should you fix, and why is aborting the canary not automatically the right first action?

<details>
<summary>Show Answer</summary>

Fix the metric label mismatch or change the AnalysisTemplate argument so the query matches the labels actually emitted by the application. An empty result is a measurement failure, not direct evidence that the canary is unhealthy. The correct response is to inspect the AnalysisRun, test the query in Prometheus, and retry after correcting the template or arguments.

Aborting may still be appropriate if the team cannot validate safety and the release is risky, but the root cause is the analysis signal rather than the canary behavior. A senior operator distinguishes service failure from instrumentation failure before changing policy.
</details>

### Question 6

Your service receives only a few requests per minute overnight. A canary step uses `pause: {duration: 60s}` and an analysis query with a two-minute Prometheus window. The canary often promotes with very little evidence. How would you redesign the rollout?

<details>
<summary>Show Answer</summary>

Increase the observation window or use a request-count-aware signal. For low-traffic services, a short time-based pause may not collect enough samples to make the success rate meaningful. The team could lengthen pauses, run synthetic smoke traffic against the canary, use job-based checks for critical paths, or schedule production rollouts during periods with enough representative traffic.

The key is to align the rollout step with evidence volume. A canary is not safer merely because time passed; it is safer when enough relevant requests or checks have passed through the new version to support a decision.
</details>

### Question 7

A team wants to use one AnalysisTemplate for error rate, p99 latency, memory growth, and checkout conversion. During adoption, the p99 latency query is noisy and would fail most healthy releases. How should they introduce this safely without weakening the whole rollout policy?

<details>
<summary>Show Answer</summary>

They can keep trusted metrics enforcing the rollout and place the noisy latency metric in dry-run mode while they tune it. Dry-run lets the team observe whether the metric would have failed without actually blocking or aborting releases. After several releases prove that the query and threshold match real user impact, they can remove dry-run and make it part of the enforced analysis.

This preserves the safety value of known-good checks while avoiding a habit of bypassing failed releases. It also creates a clean adoption path from observation to enforcement.
</details>

### Question 8

Your team must choose between canary and blue-green for a database-compatible API change. Traffic splitting is unavailable, but the team can run full smoke tests against a preview Service and has enough capacity for both versions. Which strategy is more defensible, and what risk remains?

<details>
<summary>Show Answer</summary>

Blue-green is more defensible because traffic splitting is unavailable, but preview validation and spare capacity are available. The team can run the new version behind a preview Service, execute smoke tests, and then promote the active Service when ready. The old ReplicaSet can remain available during the scale-down delay for fast rollback.

The remaining risk is that preview tests are not the same as real user traffic. Post-promotion analysis is still useful because some failures appear only after real traffic, real headers, real payloads, or production dependency timing reaches the new version.
</details>

## Hands-On Exercise

### Scenario: Build a Progressive Delivery Path in Layers

You are the platform engineer helping a product team adopt Argo Rollouts for a small HTTP service. The team currently uses a native Deployment, has no traffic router in the lab, and wants to understand the release mechanics before adding Prometheus-backed analysis. Your job is to build the rollout in layers so each safety mechanism is visible and testable.

### Step 1: Create a Lab Cluster and Install Argo Rollouts

Create a local kind cluster and install the controller. This step proves the cluster side of the system exists before you test the plugin or any Rollout manifests.

```bash
kind create cluster --name rollouts-lab

kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

kubectl -n argo-rollouts wait \
  --for=condition=available deployment/argo-rollouts \
  --timeout=120s

kubectl get crd | grep rollouts.argoproj.io
```

### Step 2: Install or Verify the kubectl Plugin

Install the plugin on your workstation if it is missing. This step gives you the rollout-specific view used throughout the rest of the lab.

```bash
kubectl argo rollouts version
```

If that command is not available on macOS, install it with Homebrew:

```bash
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

### Step 3: Deploy a Minimal Canary Rollout

Save this file as `color-rollout.yaml`. It intentionally uses pod-ratio canary behavior because the lab has no ingress or service mesh traffic router yet.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: color-api
spec:
  replicas: 5
  selector:
    matchLabels:
      app: color-api
  template:
    metadata:
      labels:
        app: color-api
    spec:
      containers:
        - name: color-api
          image: argoproj/rollouts-demo:blue
          ports:
            - containerPort: 8080
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {duration: 30s}
        - setWeight: 50
        - pause: {duration: 30s}
        - setWeight: 100
---
apiVersion: v1
kind: Service
metadata:
  name: color-api
spec:
  selector:
    app: color-api
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl apply -f color-rollout.yaml
kubectl argo rollouts get rollout color-api
```

### Step 4: Trigger a Canary Release and Observe the ReplicaSets

Change the image through the plugin so you can watch the rollout move through its steps. While it progresses, inspect ReplicaSets to connect the high-level Rollout view with the Kubernetes objects underneath.

```bash
kubectl argo rollouts set image color-api color-api=argoproj/rollouts-demo:yellow
kubectl argo rollouts get rollout color-api --watch
```

In a second terminal, run:

```bash
kubectl get rs -l app=color-api
kubectl get pods -l app=color-api -o wide
```

### Step 5: Add a Manual Approval Gate

Patch the Rollout so it pauses indefinitely before moving beyond twenty-five percent. This simulates a production approval requirement before traffic crosses a defined risk threshold.

```bash
kubectl patch rollout color-api --type merge -p '
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause:
            duration: 30s
        - setWeight: 25
        - pause: {}
        - setWeight: 50
        - pause:
            duration: 30s
        - setWeight: 100
'
```

Trigger another image update and promote only after you verify the paused state.

```bash
kubectl argo rollouts set image color-api color-api=argoproj/rollouts-demo:green
kubectl argo rollouts get rollout color-api

kubectl argo rollouts promote color-api
kubectl argo rollouts get rollout color-api --watch
```

### Step 6: Add a Simple Job-Based AnalysisTemplate

Save this file as `smoke-analysis.yaml`. It uses a Job provider so the lab can demonstrate analysis behavior without requiring Prometheus metrics.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: smoke-check
spec:
  args:
    - name: service-url
  metrics:
    - name: homepage-check
      count: 3
      interval: 10s
      successCondition: result == "ok"
      failureLimit: 1
      provider:
        job:
          spec:
            template:
              spec:
                containers:
                  - name: check
                    image: curlimages/curl:8.8.0
                    command:
                      - sh
                      - -c
                      - |
                        curl -fsS "{{args.service-url}}/" >/dev/null
                        echo ok
                restartPolicy: Never
            backoffLimit: 0
```

```bash
kubectl apply -f smoke-analysis.yaml
```

Patch the Rollout so the smoke check runs after the first canary pause.

```bash
kubectl patch rollout color-api --type merge -p '
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause:
            duration: 30s
        - analysis:
            templates:
              - templateName: smoke-check
            args:
              - name: service-url
                value: http://color-api.default.svc.cluster.local
        - setWeight: 25
        - pause: {}
        - setWeight: 100
'
```

Trigger a new image and inspect the AnalysisRun.

```bash
kubectl argo rollouts set image color-api color-api=argoproj/rollouts-demo:purple
kubectl argo rollouts get rollout color-api --watch

kubectl get analysisruns
kubectl describe analysisrun "$(kubectl get analysisruns -o jsonpath='{.items[-1:].metadata.name}')"
```

### Step 7: Practice Abort and Recovery

Trigger a new release, abort it while it is in progress, and confirm the stable revision remains serving. This step teaches the operator motion before a real incident requires it.

```bash
kubectl argo rollouts set image color-api color-api=argoproj/rollouts-demo:red
kubectl argo rollouts get rollout color-api

kubectl argo rollouts abort color-api
kubectl argo rollouts get rollout color-api
kubectl argo rollouts history rollout color-api
```

### Step 8: Write a Production Design Note

Write a short design note for how you would adapt this lab for a real user-facing service. Include the routing mode, initial canary weight, pause duration, analysis metrics, manual gates, and rollback policy. The goal is not to copy the lab YAML; the goal is to justify each release control with a risk it reduces.

### Success Criteria

- [ ] The `argo-rollouts` controller Deployment is available in the `argo-rollouts` namespace.
- [ ] The `kubectl argo rollouts` plugin can show version and Rollout status.
- [ ] A canary Rollout progresses through weight and pause steps after an image update.
- [ ] You can explain the difference between pod-ratio approximation and traffic-manager routing.
- [ ] You can add an empty pause and promote the Rollout manually after inspection.
- [ ] A job-based AnalysisTemplate creates an AnalysisRun that affects rollout progression.
- [ ] You can inspect a Rollout, ReplicaSets, pods, and AnalysisRuns during a release.
- [ ] You can abort an in-progress rollout and explain what stable state remains.
- [ ] Your production design note connects weights, pauses, analysis, and rollback to concrete service risks.

### Cleanup

```bash
kind delete cluster --name rollouts-lab
```

## Next Module

Continue to [Module 2.3: Flux](../module-2.3-flux/) where you will compare another GitOps toolkit approach and evaluate how its reconciliation model changes day-two operations.

## Sources

- [Argo Rollouts Analysis and Progressive Delivery](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/) — Backs canary and blue-green rollout behavior, AnalysisTemplate and AnalysisRun CRDs, Prometheus-driven automated analysis, abort conditions, experiments, and progressive delivery control beyond native Deployments.
- [argo-rollouts.readthedocs.io: bluegreen](https://argo-rollouts.readthedocs.io/en/stable/features/bluegreen/) — The blue-green sequence of events shows the preview ReplicaSet running before promotion and the old ReplicaSet scaling down only after the switch and delay.
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — Use this as the baseline for native rolling-update behavior that Argo Rollouts extends.

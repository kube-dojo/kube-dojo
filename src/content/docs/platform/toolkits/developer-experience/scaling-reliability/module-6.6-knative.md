---
title: "Module 6.6: Knative -- Serverless Workloads on Kubernetes"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.6-knative
sidebar:
  order: 7
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~55 minutes

## Overview

You have 200 microservices running in your cluster. Most of them sit idle 80% of the time, burning CPU and memory doing nothing. Knative brings serverless to Kubernetes -- your workloads scale to zero when nobody is using them and spin back up in seconds when traffic arrives. No proprietary FaaS lock-in, no cloud-specific APIs. Just Kubernetes, with an off switch.

**What You'll Learn**:
- What "serverless on Kubernetes" actually means (and what it does not mean)
- Knative Serving: Services, Configurations, Revisions, Routes, and scale-to-zero
- Knative Eventing: CloudEvents, Brokers, Triggers, and Sources
- How the activator proxy and cold starts work under the hood
- Traffic splitting for blue-green and canary deployments
- Installing Knative with different networking layers
- When Knative is the right tool and when it is not

**Prerequisites**:
- Kubernetes Deployments, Services, and Ingress basics
- [KEDA](./module-6.2-keda/) -- Understanding scale-to-zero concepts
- [Reliability Engineering](../../../foundations/reliability-engineering/) -- SLO awareness
- Familiarity with Helm and kubectl

---

## Why This Module Matters

A mid-size fintech company was running 200 microservices on EKS. The team had sized every deployment for peak load because nobody wanted to be the person whose service fell over during the monthly billing run. The result: 80% of services sat idle most of the day, consuming reserved CPU and memory. The monthly cloud bill was $45,000.

A platform engineer analyzed the traffic patterns and found that 140 of those 200 services received fewer than 10 requests per hour outside of business hours. Many received zero. The team migrated those 140 low-traffic services to Knative Serving with scale-to-zero enabled. Services that previously ran 24/7 now spun down after 60 seconds of inactivity and cold-started in under 2 seconds when traffic returned.

The result: the monthly bill dropped to $12,000. The 60 always-on services kept their regular Deployments. The 140 bursty services got Knative. Nobody noticed the difference in latency because a 1.5-second cold start on an internal admin dashboard is invisible. The only thing that changed was the bill.

The lesson: not every workload needs to run 24/7. The hard part is knowing which ones can sleep.

---

> **Did You Know?**
>
> 1. Knative was originally created by Google, Pivotal, IBM, Red Hat, and SAP in 2018. Google Cloud Run is literally Knative running as a managed service -- when you deploy to Cloud Run, you are deploying a Knative Service.
> 2. Knative can scale a service from 0 to 1,000 pods in under 30 seconds. The activator proxy buffers incoming requests during cold start so that no requests are dropped -- they just wait.
> 3. The Knative project removed its Build component in 2019 and handed that responsibility to Tekton (Module 3.2). This is a rare example of a project intentionally shrinking its scope to do fewer things better.
> 4. As of 2025, Knative is a CNCF incubating project. It powers serverless platforms at companies including IBM (Code Engine), VMware (Tanzu), and Google (Cloud Run), processing billions of requests daily across these platforms.

---

## What Is Serverless on Kubernetes?

Let us clear up the biggest misconception first.

```
"SERVERLESS" DOES NOT MEAN "NO SERVERS"
================================================================

What marketing says:
  "No servers to manage!"

What it actually means:
  "Servers that manage themselves."

Specifically:
  1. Scale to zero when idle (no pods running = no cost)
  2. Scale up automatically when requests arrive
  3. Developer provides container, platform handles the rest
  4. Pay for what you use, not what you reserve

================================================================

TRADITIONAL DEPLOYMENT vs KNATIVE
================================================================

Traditional:
  3 replicas ──────────────────────────── 3 replicas
  Running 24/7, even at 3 AM with zero traffic

Knative:
  0 pods ─── request ──▶ 1 pod ─── idle ──▶ 0 pods
  Only running when actively serving traffic

Cost comparison (per service):
  Traditional: ~$50/month (always on)
  Knative:     ~$3/month  (runs 2 hours/day average)
================================================================
```

Serverless on Kubernetes means your cluster still exists, your nodes still run, but individual workloads can sleep. Think of it like the difference between leaving every light in your house on 24/7 versus installing motion sensors.

---

## Knative Serving

Knative Serving is the component that manages your serverless workloads. It introduces four Kubernetes Custom Resources that work together.

### The Four Resources

```
KNATIVE SERVING RESOURCE MODEL
================================================================

┌─────────────────────────────────────────────────────────────┐
│  SERVICE (ksvc)                                             │
│  Top-level resource. You create this.                       │
│  Manages everything below automatically.                    │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CONFIGURATION                                        │  │
│  │  Desired state of your workload.                      │  │
│  │  Each change creates a new Revision.                  │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Revision v1 │  │ Revision v2 │  │ Revision v3 │  │  │
│  │  │ (image:1.0) │  │ (image:1.1) │  │ (image:1.2) │  │  │
│  │  │             │  │             │  │  (latest)   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ROUTE                                                │  │
│  │  Maps traffic to Revisions.                           │  │
│  │  Enables traffic splitting.                           │  │
│  │                                                       │  │
│  │  100% ──▶ Revision v3 (latest)                       │  │
│  │   OR                                                  │  │
│  │   90% ──▶ Revision v2, 10% ──▶ Revision v3 (canary) │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Key insight: You only create the SERVICE.
Knative creates Configuration, Revisions, and Route for you.
================================================================
```

- **Service (ksvc)**: The only resource you need to create. It manages the entire lifecycle.
- **Configuration**: Describes the desired state (container image, env vars, resource limits). Every update creates a new Revision.
- **Revision**: An immutable snapshot of your Configuration at a point in time. Think of it like a Git commit for your deployment.
- **Route**: Maps network traffic to one or more Revisions. This is how traffic splitting works.

### Your First Knative Service

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    metadata:
      annotations:
        # Scale to zero after 60 seconds of no traffic
        autoscaling.knative.dev/scale-to-zero-pod-retention-period: "60s"
    spec:
      containers:
      - image: gcr.io/knative-samples/helloworld-go
        ports:
        - containerPort: 8080
        env:
        - name: TARGET
          value: "World"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
```

```bash
# Apply the service
kubectl apply -f hello-service.yaml

# Check the Knative service
kubectl get ksvc hello

# Output:
# NAME    URL                                 LATESTCREATED   LATESTREADY     READY
# hello   http://hello.default.example.com    hello-00001     hello-00001     True

# Check the automatically created resources
kubectl get configuration hello
kubectl get revision -l serving.knative.dev/service=hello
kubectl get route hello
```

### Autoscaling: From 0 to N

Knative uses the Knative Pod Autoscaler (KPA) by default, which is more responsive than the standard HPA for serverless workloads.

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: autoscale-demo
spec:
  template:
    metadata:
      annotations:
        # Autoscaler class: kpa (default) or hpa
        autoscaling.knative.dev/class: "kpa.autoscaling.knative.dev"

        # Target concurrent requests per pod
        autoscaling.knative.dev/target: "10"

        # Minimum replicas (0 enables scale-to-zero)
        autoscaling.knative.dev/min-scale: "0"

        # Maximum replicas
        autoscaling.knative.dev/max-scale: "50"

        # Scale down delay (seconds of idle before scaling to zero)
        autoscaling.knative.dev/scale-to-zero-pod-retention-period: "30s"

        # Initial scale when waking from zero
        autoscaling.knative.dev/initial-scale: "1"
    spec:
      containers:
      - image: gcr.io/knative-samples/autoscale-go
        ports:
        - containerPort: 8080
```

The key metric is **concurrency** -- how many simultaneous requests each pod should handle. If `target` is 10 and 50 requests arrive simultaneously, Knative scales to 5 pods.

---

## Scale to Zero: How It Actually Works

This is the magic of Knative, and understanding the mechanics helps you tune it properly.

```
SCALE-TO-ZERO LIFECYCLE
================================================================

Phase 1: ACTIVE (pods running, serving traffic)
─────────────────────────────────────────────────
  Client ──▶ Ingress ──▶ Pod (serving requests)
                         Pod
                         Pod

Phase 2: GRACE PERIOD (no traffic, counting down)
─────────────────────────────────────────────────
  No requests for 30s...
  Knative Autoscaler: "Scale-to-zero timer started."
  Pods still running, ready to serve.

Phase 3: SCALED TO ZERO (no pods, activator watching)
─────────────────────────────────────────────────
  Knative terminates all pods.
  Ingress now points to the ACTIVATOR (a Knative system component).
  No application pods exist. Zero resource consumption.

Phase 4: COLD START (request arrives, waking up)
─────────────────────────────────────────────────
  Client ──▶ Ingress ──▶ Activator (holds the request)
                              │
                              ├── Signals autoscaler: "Wake up!"
                              ├── Autoscaler creates pod(s)
                              ├── Waits for pod to be Ready
                              └── Forwards buffered request to pod
                                        │
  Client ◀── Response ◀── Pod ◀─────────┘

Phase 5: ACTIVE AGAIN
─────────────────────────────────────────────────
  Ingress switches from Activator back to pod directly.
  Subsequent requests go straight to pods (no activator overhead).
================================================================
```

### The Activator

The activator is Knative's secret weapon. It is a reverse proxy that sits in the data path only when a service is scaled to zero. When a request arrives for a sleeping service:

1. The activator receives the request and **buffers it** (the client waits)
2. It tells the autoscaler to create pods
3. Once a pod passes its readiness probe, the activator forwards the buffered request
4. The ingress layer switches to routing directly to pods
5. The activator steps out of the data path

No requests are dropped. The client just experiences a delay (the cold start latency).

### Cold Start Latency

Cold start is the time between "request arrives" and "pod is ready to serve." It depends on:

```
COLD START BREAKDOWN
================================================================

Component                         Typical Time
─────────────────────────────────────────────────
Activator receives request        ~5ms
Autoscaler decision               ~50ms
API server creates pod            ~100ms
Scheduler places pod              ~50ms
Container image pull              0ms (cached) to 30s+ (not cached)
Container startup                 ~200ms to 5s (app dependent)
Readiness probe passes            ~100ms to 10s (app dependent)
─────────────────────────────────────────────────
TOTAL (image cached, fast app)    ~500ms to 2s
TOTAL (image not cached, slow)    5s to 45s

HOW TO MINIMIZE COLD START:
1. Use small container images (distroless, alpine)
2. Pre-pull images on nodes (DaemonSet trick)
3. Keep application startup fast (lazy initialization)
4. Set min-scale: 1 for latency-sensitive services
5. Use initial-scale to start multiple pods on wake
================================================================
```

---

## Knative Eventing

Knative Serving handles request/response workloads. Knative Eventing handles event-driven architectures -- reacting to things that happen rather than requests that arrive.

### Core Concepts

```
KNATIVE EVENTING ARCHITECTURE
================================================================

┌──────────────────────────────────────────────────────────┐
│                      SOURCES                              │
│  (Where events come from)                                 │
│                                                           │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Kafka   │  │ GitHub   │  │ Cron     │  │ API      │ │
│  │ Source  │  │ Source   │  │ Source   │  │ Source   │ │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼────────────┼────────────┼────────────┼──────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌──────────────────────────────────────────────────────────┐
│                      BROKER                               │
│  (Central event bus, receives all events)                 │
│  Events are CloudEvents (standard format)                 │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Event: {type: "dev.knative.kafka.event",           │ │
│  │          source: "kafka-cluster",                    │ │
│  │          data: {...}}                                │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────┬────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Trigger    │ │  Trigger    │ │  Trigger    │
│  filter:    │ │  filter:    │ │  filter:    │
│  type=order │ │  type=payment│ │  type=*    │
│      │      │ │      │      │ │      │      │
│      ▼      │ │      ▼      │ │      ▼      │
│  Order Svc  │ │  Payment   │ │  Audit Log  │
│  (ksvc)     │ │  Svc (ksvc)│ │  (ksvc)     │
└─────────────┘ └─────────────┘ └─────────────┘
================================================================
```

- **Source**: Produces events. Connects external systems (Kafka, GitHub webhooks, cron schedules, APIs) to the Knative eventing mesh.
- **Broker**: A central event bus. Receives events and distributes them to Triggers.
- **Trigger**: A filter that routes events from a Broker to a subscriber (typically a Knative Service). You define which event types each subscriber cares about.
- **CloudEvents**: A CNCF specification for describing events in a standard way. Every event in Knative Eventing is a CloudEvent with `type`, `source`, `id`, `data`, and other metadata.

### Eventing Example

```yaml
# 1. Create a Broker (event bus)
apiVersion: eventing.knative.dev/v1
kind: Broker
metadata:
  name: default
  namespace: default
---
# 2. Create an event Source (cron job that fires every minute)
apiVersion: sources.knative.dev/v1
kind: PingSource
metadata:
  name: heartbeat
  namespace: default
spec:
  schedule: "*/1 * * * *"
  contentType: "application/json"
  data: '{"message": "heartbeat"}'
  sink:
    ref:
      apiVersion: eventing.knative.dev/v1
      kind: Broker
      name: default
---
# 3. Create a Trigger (route heartbeat events to our service)
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  name: heartbeat-trigger
  namespace: default
spec:
  broker: default
  filter:
    attributes:
      type: dev.knative.sources.ping
  subscriber:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: event-display
---
# 4. Create the subscriber service
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: event-display
  namespace: default
spec:
  template:
    spec:
      containers:
      - image: gcr.io/knative-releases/knative.dev/eventing/cmd/event_display
```

Events flow: PingSource fires every minute, sends a CloudEvent to the Broker, the Trigger matches the event type and forwards it to the `event-display` service. If the service is scaled to zero, it wakes up to process the event.

---

## Traffic Splitting

One of Knative's most powerful features is built-in traffic splitting across Revisions. No service mesh required.

### Blue-Green Deployment

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: my-app
spec:
  template:
    metadata:
      name: my-app-v2  # Name this revision explicitly
    spec:
      containers:
      - image: my-registry/my-app:2.0
  traffic:
  # All traffic goes to the new revision
  - revisionName: my-app-v2
    percent: 100
  # Tag the old revision so you can access it directly
  - revisionName: my-app-v1
    percent: 0
    tag: previous
```

With the `previous` tag, you can access the old version at `previous-my-app.default.example.com` for testing -- even though it gets 0% of production traffic.

### Canary Deployment

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: my-app
spec:
  template:
    metadata:
      name: my-app-v3
    spec:
      containers:
      - image: my-registry/my-app:3.0
  traffic:
  # 90% to current stable version
  - revisionName: my-app-v2
    percent: 90
    tag: stable
  # 10% to new canary version
  - revisionName: my-app-v3
    percent: 10
    tag: canary
```

```bash
# Gradually shift traffic
# 10% -> 25% -> 50% -> 100%

# Check current traffic split
kubectl get ksvc my-app -o jsonpath='{.status.traffic[*]}'

# Each tagged revision gets its own URL:
# stable-my-app.default.example.com  (always hits v2)
# canary-my-app.default.example.com  (always hits v3)
# my-app.default.example.com         (split 90/10)
```

---

## Installation

Knative requires a networking layer. You have three main choices.

### Option 1: Knative with Kourier (Lightweight)

Kourier is the simplest option -- an Envoy-based ingress built specifically for Knative.

```bash
# Install Knative Serving CRDs and core
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-core.yaml

# Install Kourier networking layer
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.16.0/kourier.yaml

# Configure Knative to use Kourier
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Install Knative Eventing (optional)
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/eventing-crds.yaml
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/eventing-core.yaml

# Install the in-memory channel (for development)
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/in-memory-channel.yaml

# Install the MT-Channel-based broker
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.16.0/mt-channel-broker.yaml

# Verify
kubectl get pods -n knative-serving
kubectl get pods -n knative-eventing
```

### Option 2: Knative Operator (Production)

```bash
# Install the Knative Operator
kubectl apply -f https://github.com/knative/operator/releases/download/knative-v1.16.0/operator.yaml

# Create a KnativeServing instance
cat <<EOF | kubectl apply -f -
apiVersion: operator.knative.dev/v1beta1
kind: KnativeServing
metadata:
  name: knative-serving
  namespace: knative-serving
spec:
  ingress:
    kourier:
      enabled: true
  config:
    network:
      ingress-class: "kourier.ingress.networking.knative.dev"
EOF

# Create a KnativeEventing instance
cat <<EOF | kubectl apply -f -
apiVersion: operator.knative.dev/v1beta1
kind: KnativeEventing
metadata:
  name: knative-eventing
  namespace: knative-eventing
EOF
```

### Networking Layer Comparison

| Feature | Kourier | Istio | Contour |
|---------|---------|-------|---------|
| **Complexity** | Low | High | Medium |
| **Resource usage** | ~100MB | ~500MB+ | ~200MB |
| **mTLS** | No | Yes | No |
| **Service mesh features** | No | Yes | No |
| **Best for** | Dev, simple production | Already using Istio | Already using Contour |
| **Setup time** | 2 minutes | 15+ minutes | 5 minutes |

**Recommendation**: Use Kourier unless you already have Istio or Contour in your cluster. Adding Istio just for Knative is overkill.

---

## Comparison: Knative vs the Alternatives

| Feature | Knative | KEDA | AWS Lambda | Cloud Run |
|---------|---------|------|------------|-----------|
| **Runs on** | Any Kubernetes | Any Kubernetes | AWS only | GCP only |
| **Scale to zero** | Yes | Yes | Yes | Yes |
| **Cold start** | 1-5s typical | 1-5s typical | 100ms-10s | 0-5s |
| **Max execution time** | Unlimited | Unlimited | 15 minutes | 60 minutes |
| **Container support** | Any container | Any container | Custom runtime | Any container |
| **Event-driven** | Yes (Eventing) | Yes (60+ scalers) | Yes (native) | Yes (via Eventarc) |
| **Traffic splitting** | Built-in | No | Weighted aliases | Built-in |
| **Vendor lock-in** | None | None | High | Medium |
| **Networking** | Configurable | Uses existing | VPC/API Gateway | Managed |
| **Serving + Eventing** | Both | Scaling only | Both | Serving only |
| **Best for** | Portable serverless | Scaling existing deployments | AWS-native functions | GCP-native containers |

### When to Choose What

- **Knative**: You want serverless on Kubernetes without cloud vendor lock-in. You need both serving and eventing. You want built-in traffic splitting.
- **KEDA**: You already have Deployments and just want smarter autoscaling (especially event-driven). You do not need the full Knative serving model.
- **AWS Lambda**: You are all-in on AWS, your functions run under 15 minutes, and you want the lowest possible cold start times.
- **Cloud Run**: You are on GCP and want managed Knative without running the control plane yourself.

---

## When to Use Knative

```
GOOD FIT FOR KNATIVE
================================================================

1. LOW-TRAFFIC SERVICES
   Internal tools, admin dashboards, reporting APIs
   that get 0-100 requests per hour.
   Scale-to-zero saves significant resources.

2. EVENT PROCESSORS
   Webhook receivers, queue consumers, notification handlers.
   Wake up when an event arrives, process it, go back to sleep.

3. BATCH JOBS WITH HTTP TRIGGERS
   Report generation, data exports, PDF rendering.
   Triggered on demand, no need to run 24/7.

4. DEV/STAGING ENVIRONMENTS
   200 microservices in staging, most idle.
   Knative can cut staging costs by 60-80%.

5. MULTI-TENANT PLATFORMS
   Each tenant gets their own service instance.
   Inactive tenants scale to zero.

6. CANARY DEPLOYMENTS WITHOUT A SERVICE MESH
   Built-in traffic splitting means you do not
   need Istio just for canary releases.
================================================================
```

```
BAD FIT FOR KNATIVE
================================================================

1. LATENCY-SENSITIVE SERVICES
   If p99 < 100ms matters, cold starts are unacceptable.
   Set min-scale: 1 (but then you lose scale-to-zero).

2. STATEFUL WORKLOADS
   Databases, caches, message brokers.
   These cannot be stopped and restarted on demand.

3. ALWAYS-ON HIGH-TRAFFIC SERVICES
   If your API handles 1000+ req/s 24/7, it will never
   scale to zero anyway. Knative adds overhead with no benefit.

4. LONG-RUNNING CONNECTIONS
   WebSockets, gRPC streams, SSE.
   Knative's activator does not handle persistent connections well.

5. WORKLOADS WITH EXPENSIVE STARTUP
   If your app takes 30+ seconds to start (JVM with huge
   classpath, ML model loading), cold starts become painful.

6. SERVICES WITH LARGE PERSISTENT VOLUMES
   PVCs cannot be dynamically attached/detached on scale events.
   Use regular Deployments with volume mounts.
================================================================
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using Knative for all services | Always-on services gain nothing; Knative adds overhead and complexity | Profile traffic patterns first; only migrate services that are idle 50%+ of the time |
| Ignoring cold start latency | Users see 2-5 second delays on first request after idle period | Set `min-scale: 1` for user-facing services, or use scale-to-zero only for internal/async workloads |
| Large container images | 500MB+ images cause 10-30 second cold starts when not cached on the node | Use distroless or alpine base images; keep images under 100MB; pre-pull with a DaemonSet |
| Not setting resource requests | Knative autoscaler cannot make good decisions without knowing pod resource consumption | Always set CPU and memory requests; the autoscaler uses these for scheduling decisions |
| Installing Istio just for Knative | Adds 500MB+ of memory overhead and significant operational complexity | Use Kourier unless you already have Istio for other reasons |
| Forgetting to configure DNS | Knative generates URLs like `hello.default.example.com` that do not resolve | Configure a real domain with a wildcard DNS record, or use Magic DNS (sslip.io) for development |
| Not testing cold start path | The warm path works fine, but the cold start path has different failure modes | Always test by scaling to zero manually (`kubectl scale ksvc hello --replicas=0`) and then sending a request |
| Setting scale-to-zero window too short | Service oscillates between 0 and 1 pods, wasting resources on repeated cold starts | Set `scale-to-zero-pod-retention-period` to at least 60s; longer for services with bursty traffic patterns |
| No readiness probe | Knative routes traffic before the app is actually ready, causing 503 errors during cold start | Define a readiness probe; Knative waits for it to pass before sending traffic |
| Mixing Knative and regular Services on same port | Network routing conflicts between Knative's ingress and regular Kubernetes Services | Use separate namespaces or ensure no port/hostname overlap between Knative and standard services |

---

## Quiz

### Question 1
What are the four Knative Serving resources, and which one do you actually create?

<details>
<summary>Show Answer</summary>

The four resources are **Service** (ksvc), **Configuration**, **Revision**, and **Route**.

You only create the **Service**. Knative automatically creates and manages the Configuration, Revisions, and Route. The Configuration describes the desired state, each change produces an immutable Revision (like a Git commit), and the Route determines how traffic is split across Revisions.

</details>

### Question 2
Explain how the activator enables scale-to-zero without dropping requests.

<details>
<summary>Show Answer</summary>

When a Knative service scales to zero, the ingress layer routes traffic to the **activator** instead of directly to application pods (which no longer exist). When a request arrives:

1. The activator **buffers** the request (the client waits)
2. It signals the autoscaler to create pods
3. The autoscaler schedules pod(s) and waits for the readiness probe to pass
4. The activator **forwards** the buffered request to the now-ready pod
5. The ingress switches to routing directly to pods, removing the activator from the data path

The client experiences a delay (cold start latency) but never a dropped request or an error.

</details>

### Question 3
What is a Knative Revision and why is it immutable?

<details>
<summary>Show Answer</summary>

A Revision is an immutable snapshot of a Knative Configuration at a point in time. Every time you update a Knative Service (change the image, environment variables, resource limits, etc.), a new Revision is created.

Immutability is critical because it enables:
- **Traffic splitting**: You can route percentages of traffic to different Revisions for canary deployments
- **Rollback**: You can instantly shift 100% of traffic back to a previous Revision without redeploying
- **Auditability**: You can see exactly what was running at any point in time

Think of Revisions like Git commits -- each one is a permanent record of a specific configuration state.

</details>

### Question 4
You have a Knative Service with `autoscaling.knative.dev/target: "10"` and 75 concurrent requests arrive. How many pods will Knative create?

<details>
<summary>Show Answer</summary>

Knative will target **8 pods** (75 / 10 = 7.5, rounded up to 8). The KPA (Knative Pod Autoscaler) uses the concurrency target to determine the desired replica count. With a target of 10 concurrent requests per pod and 75 total concurrent requests, it needs at least 8 pods to keep each pod at or below the target concurrency.

In practice, the autoscaler also considers a panic window for rapid scaling and a stable window for gradual adjustment, so the actual pod count may briefly be higher or lower depending on how quickly the traffic ramp occurred.

</details>

### Question 5
What is the difference between Knative Eventing's Broker and a Trigger?

<details>
<summary>Show Answer</summary>

A **Broker** is a central event bus that receives CloudEvents from Sources. It holds events and makes them available for filtering.

A **Trigger** is a subscription with a filter. It watches a Broker and routes matching events to a subscriber (typically a Knative Service). You define filter criteria on the Trigger -- for example, only events with `type: order.created` -- and the Broker delivers matching events to the Trigger's subscriber.

The Broker/Trigger model decouples event producers from consumers. Producers send events to the Broker without knowing who will consume them. Consumers subscribe via Triggers without knowing who produces the events.

</details>

### Question 6
Why is Kourier recommended over Istio for most Knative installations?

<details>
<summary>Show Answer</summary>

Kourier is recommended because:

1. **Resource usage**: Kourier uses ~100MB of memory; Istio uses 500MB+ and adds sidecar proxies to every pod
2. **Complexity**: Kourier is a single component purpose-built for Knative; Istio is a full service mesh with many components to manage
3. **Setup time**: Kourier installs in 2 minutes; Istio takes 15+ minutes and requires ongoing configuration
4. **Scope**: Unless you need mTLS, distributed tracing, or other service mesh features for your entire cluster, Istio is overkill

The only time to choose Istio is when you already have it installed for other reasons (mTLS, advanced traffic policies) and want Knative to use the existing infrastructure.

</details>

### Question 7
A team deploys all 50 of their microservices on Knative with scale-to-zero. Users complain about intermittent slowness. What went wrong?

<details>
<summary>Show Answer</summary>

The team used Knative for services that should not scale to zero. The intermittent slowness is caused by cold starts -- when a user hits a service that has scaled to zero, they wait 1-5 seconds (or more) while the pod starts up.

The fix is to profile traffic patterns and categorize services:
- **High-traffic, user-facing services**: Set `min-scale: 1` (or use regular Deployments)
- **Internal/async services with bursty traffic**: Scale-to-zero is appropriate
- **Latency-sensitive services**: Never scale to zero

Not every service benefits from scale-to-zero. The savings only matter for services that are idle a significant portion of the time, and the cold start penalty must be acceptable for the use case.

</details>

### Question 8
How would you implement a canary deployment with Knative that sends 5% of traffic to a new version?

<details>
<summary>Show Answer</summary>

Update the Knative Service with a traffic split in the `traffic` section:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: my-app
spec:
  template:
    metadata:
      name: my-app-v2
    spec:
      containers:
      - image: my-registry/my-app:2.0
  traffic:
  - revisionName: my-app-v1
    percent: 95
    tag: stable
  - revisionName: my-app-v2
    percent: 5
    tag: canary
```

Each tagged revision gets its own URL (`canary-my-app.default.example.com`) for direct testing. To promote the canary, gradually increase the percentage (5 -> 25 -> 50 -> 100). To rollback, set the canary to 0% and stable to 100%.

No service mesh is needed -- Knative handles traffic splitting natively through its Route resource.

</details>

---

## Hands-On Exercise

### Objective

Deploy a Knative service, watch it scale to zero, send a request to trigger cold start, observe it scale back up, and then perform a traffic split between two revisions.

### Environment Setup

```bash
# Create a kind cluster with port mapping for Kourier
cat <<EOF | kind create cluster --name knative-lab --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 31080
    hostPort: 8080
    protocol: TCP
EOF

# Install Knative Serving
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-core.yaml

# Install Kourier
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.16.0/kourier.yaml

# Configure Knative to use Kourier
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Configure Magic DNS (sslip.io) for local development
kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"127.0.0.1.sslip.io":""}}'

# Patch Kourier to use NodePort for kind
kubectl patch service kourier -n kourier-system \
  --type merge \
  --patch '{"spec":{"type":"NodePort","ports":[{"port":80,"targetPort":8080,"nodePort":31080}]}}'

# Wait for Knative to be ready
kubectl wait --for=condition=Ready pods --all -n knative-serving --timeout=120s
kubectl wait --for=condition=Ready pods --all -n kourier-system --timeout=120s

# Verify installation
kubectl get pods -n knative-serving
kubectl get pods -n kourier-system
```

### Tasks

**Step 1: Deploy a Knative Service.**

```yaml
# Save as hello-knative.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/scale-to-zero-pod-retention-period: "30s"
    spec:
      containers:
      - image: gcr.io/knative-samples/helloworld-go
        ports:
        - containerPort: 8080
        env:
        - name: TARGET
          value: "KubeDojo Student"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
```

```bash
kubectl apply -f hello-knative.yaml

# Check the service
kubectl get ksvc hello

# Watch all created resources
kubectl get configuration hello
kubectl get revision -l serving.knative.dev/service=hello
kubectl get route hello
```

**Step 2: Send a request and observe pods.**

Open a second terminal to watch pods:

```bash
# Terminal 2: watch pods
kubectl get pods -l serving.knative.dev/service=hello -w
```

In the first terminal:

```bash
# Send a request
curl -H "Host: hello.default.127.0.0.1.sslip.io" http://localhost:8080

# Expected output: "Hello KubeDojo Student!"
```

**Step 3: Watch scale-to-zero.**

```bash
# Wait 30+ seconds with no traffic
# In Terminal 2, you should see the pod terminate

# Verify: no pods running
kubectl get pods -l serving.knative.dev/service=hello
# Expected: No resources found
```

**Step 4: Trigger cold start.**

```bash
# Time the cold start
time curl -H "Host: hello.default.127.0.0.1.sslip.io" http://localhost:8080

# Note the total time -- this includes cold start latency
# Expected: 1-5 seconds depending on your system

# Check pods again -- one should be running now
kubectl get pods -l serving.knative.dev/service=hello
```

**Step 5: Deploy a second revision and split traffic.**

```yaml
# Save as hello-v2.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/scale-to-zero-pod-retention-period: "30s"
    spec:
      containers:
      - image: gcr.io/knative-samples/helloworld-go
        ports:
        - containerPort: 8080
        env:
        - name: TARGET
          value: "KubeDojo Graduate"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
  traffic:
  - latestRevision: false
    revisionName: hello-00001
    percent: 80
    tag: stable
  - latestRevision: true
    percent: 20
    tag: canary
```

```bash
kubectl apply -f hello-v2.yaml

# Verify two revisions exist
kubectl get revision -l serving.knative.dev/service=hello

# Send multiple requests and observe the split
for i in $(seq 1 20); do
  curl -s -H "Host: hello.default.127.0.0.1.sslip.io" http://localhost:8080
done

# You should see ~80% "Hello KubeDojo Student!" and ~20% "Hello KubeDojo Graduate!"

# Test tagged routes directly
curl -H "Host: stable-hello.default.127.0.0.1.sslip.io" http://localhost:8080
# Always returns: "Hello KubeDojo Student!"

curl -H "Host: canary-hello.default.127.0.0.1.sslip.io" http://localhost:8080
# Always returns: "Hello KubeDojo Graduate!"
```

**Step 6: Promote the canary.**

```bash
# Shift all traffic to the new revision
kubectl patch ksvc hello --type merge --patch '{
  "spec": {
    "traffic": [
      {"revisionName": "hello-00001", "percent": 0, "tag": "previous"},
      {"latestRevision": true, "percent": 100}
    ]
  }
}'

# Verify
curl -H "Host: hello.default.127.0.0.1.sslip.io" http://localhost:8080
# Should always return: "Hello KubeDojo Graduate!"
```

### Success Criteria

- [ ] Knative Serving is installed and all pods are running in knative-serving namespace
- [ ] A Knative Service is deployed and accessible via curl
- [ ] You observed the service scale to zero (0 pods) after the idle period
- [ ] You triggered a cold start and measured the latency
- [ ] You deployed a second revision and verified traffic splitting (80/20)
- [ ] You accessed individual revisions via tagged routes
- [ ] You promoted the canary to 100% traffic

### Bonus Challenge

Install Knative Eventing and create a PingSource that fires every 30 seconds, a Broker, a Trigger, and an event-display service. Verify that the event-display service scales to zero between events and wakes up each time a CloudEvent arrives.

---

## Further Reading

- [Knative Documentation](https://knative.dev/docs/)
- [Knative Serving Autoscaling](https://knative.dev/docs/serving/autoscaling/)
- [CloudEvents Specification](https://cloudevents.io/)
- [Knative Cookbook (O'Reilly)](https://www.oreilly.com/library/view/knative-cookbook/9781492061182/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs) (managed Knative)

---

## Next Module

Return to [Module 6.2: KEDA](./module-6.2-keda/) to compare event-driven autoscaling approaches, or explore [Module 6.4: FinOps with OpenCost](./module-6.4-finops-opencost/) to measure the cost savings from scale-to-zero.

---

*"The cheapest pod is the one that is not running."*

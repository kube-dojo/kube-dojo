---
revision_pending: false
title: "Module 6.2: KEDA"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.2-keda
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy KEDA and configure ScaledObjects for event-driven autoscaling beyond CPU and memory metrics**
- **Implement KEDA scalers for message queues, databases, Prometheus metrics, and custom event sources**
- **Configure KEDA's scale-to-zero capability for cost optimization of intermittent workloads**
- **Integrate KEDA with HPA for composite scaling strategies combining event-driven and resource-based triggers**
- **Troubleshoot common KEDA misconfigurations including thrashing, cold-start latency, and authentication failures**

---

## Why This Module Matters

> **Hypothetical scenario:** Your team runs a video-transcoding pipeline on Kubernetes. During the day, the queue holds roughly 200 jobs. The native Horizontal Pod Autoscaler sees CPU at 80% and adds pods — but by the time it reacts, the queue has doubled. At 2 AM the queue is empty, yet your deployment idles at the HPA minimum of 2 replicas, burning compute for nothing. Your cloud bill for idle worker replicas across dev, staging, and production climbs to roughly $3,000 per month. Worse, a spike of 5,000 files on a Monday morning creates lag so severe that the processing SLA breaks before the HPA catches up.

This is the mismatch KEDA addresses. The HPA reads lagging resource symptoms; KEDA reads the work itself — queue depth, stream lag, request rate, or a cron schedule — and scales the workload to match. When the queue is empty, KEDA scales the deployment to zero replicas, eliminating idle cost entirely. When work arrives, KEDA activates the workload from zero in seconds and hands off ongoing scaling to a HPA it creates and manages internally.

The durable capability here is **event-driven autoscaling**: connecting scaling decisions to the actual units of work — pending messages, unprocessed records, HTTP request rate — rather than to CPU and memory, which are symptoms of work, not definitions of it. KEDA is the tool that operationalises this capability on Kubernetes, but the capability itself transcends any single tool: the distinction between symptom-driven and work-driven scaling is a design principle every platform engineer should internalise before choosing an autoscaling strategy. When you understand *why* this distinction matters, you can evaluate any autoscaling solution — KEDA, cloud-managed alternatives, or a future competitor — on its merits, not just its popularity.

---

## The Core Distinction: Resource-Based vs Event-Driven Autoscaling

To understand what KEDA brings to a Kubernetes cluster, start with what the native Horizontal Pod Autoscaler (HPA) was designed to solve and where its design assumptions break down.

The HPA scales pods based on observed resource utilisation — CPU, memory, or custom metrics exposed through the Kubernetes metrics pipeline. This model works well when the relationship between work and resource consumption is linear and stable. A web server handling HTTP requests consumes CPU roughly in proportion to request rate. If you double the request rate, you double the CPU consumption, and the HPA responds by adding pods. The HPA's metric pipeline — metrics-server, the `/apis/custom.metrics.k8s.io` and `/apis/external.metrics.k8s.io` APIs — connects a metrics source to a scaling decision, with the HPA controller computing the desired replica count using the formula `desiredReplicas = ceil(currentMetricValue / targetMetricValue) * currentReplicas`.

Three structural limitations emerge from this model.

First, the HPA cannot scale to zero replicas. The `minReplicas` field in a HorizontalPodAutoscaler resource has a practical floor of 1 because, with zero replicas, there are no pods generating the metrics the HPA needs to decide when to scale back up. The HPA's control loop requires a running pod to observe metrics; without one, it is blind. This means every deployment managed by the HPA carries an idle-cost floor of at least one replica, even when there is no work to do. For workloads with intermittent demand — a batch processor that runs hourly, a CI/CD runner triggered by pull requests, a cron-activated data pipeline — this idle floor wastes resources continuously.

Second, the HPA's default metric set (CPU and memory) is a proxy for work, not a measurement of work. When a deployment processes items from a queue, CPU utilisation tells you the pod is busy, but it does not tell you how many items are waiting. Queue depth can grow before CPU reaches its threshold, creating a lag between work arrival and the scaling response. In the worst case — an I/O-bound workload waiting on external services — CPU stays low while the real bottleneck (queue depth, database connection pool, API rate limit) saturates silently. The HPA scales on the smoke, not the fire.

Third, custom and external metrics in Kubernetes require infrastructure that is operationally heavy to set up and maintain. The `custom.metrics.k8s.io` API expects a metrics adapter to aggregate pod-level metrics and expose them as an API server extension. The `external.metrics.k8s.io` API, introduced in Kubernetes 1.10, allows scaling on metrics from outside the cluster, but still requires a metrics adapter that implements the API Server extension protocol. Writing or configuring such an adapter for a queue, a database, or a cron schedule involves non-trivial engineering effort: the adapter must authenticate to the external system, poll it safely without triggering rate limits, and translate the results into the Kubernetes metrics format. Most teams never build this; they default to CPU-based scaling and accept the mismatch.

This is where event-driven autoscaling enters as a durable capability: instead of scaling on resource proxy signals, you scale directly on the work that is waiting. The key insight is that the source of work — a queue, a stream, an HTTP endpoint, a database query result — knows how much work is pending. The autoscaling system should ask that source directly, not infer workload from how hard the existing pods are running. Event-driven autoscaling replaces the CPU/memory proxy with a direct measurement of the work backlog, and it treats the zero-work state as a valid, desirable target — scaling the workload all the way to zero when there is nothing to process.

---

## How KEDA Bridges the Gap

KEDA — Kubernetes Event-Driven Autoscaling — is a CNCF Graduated project (graduated August 22, 2023) that implements event-driven autoscaling on Kubernetes by extending the HPA rather than replacing it. KEDA installs as an operator and a metrics adapter in the cluster, watching custom resources that you define and managing the full scaling lifecycle from zero-to-N and back to zero.

The conceptual model has three layers. At the top, you write a **ScaledObject** (for Deployments, StatefulSets, and custom resources with a `/scale` subresource) or a **ScaledJob** (for Jobs). These resources declare which workload to scale, what event source to consult, and the scaling parameters: minimum and maximum replicas, polling interval, cooldown period, and so on. In the middle, the **KEDA operator** watches these resources and takes responsibility for the activation phase — scaling a workload from zero to one replica when work arrives, and from one back to zero when the event source reports no work. The operator also creates and manages a Kubernetes HPA resource for each ScaledObject. At the bottom, the **KEDA metrics adapter** (keda-metrics-apiserver) implements the Kubernetes external metrics API, exposing the event-source metrics to the HPA so it can handle scaling from one to N replicas using Kubernetes' own HPA controller.

This two-track design — KEDA for activation (0 to 1, 1 to 0), HPA for scaling (1 to N) — is the architecture's central insight. KEDA does not reimplement the HPA's scaling logic, which is battle-tested in the Kubernetes control plane and benefits from features like stabilisation windows, scaling policies, and the `behavior` section for tuning scale-up and scale-down rates. Instead, KEDA focuses on what the HPA cannot do: react to external events and scale to zero. Once the workload has at least one running replica, KEDA steps back and lets the HPA controller drive scaling, feeding it external metrics through the metrics adapter.

KEDA's architecture also includes an **admission webhooks** component that validates ScaledObject and ScaledJob resources at creation time, catching misconfigurations — such as two ScaledObjects targeting the same deployment, or a ScaledObject with a missing authentication reference — before they reach the cluster.

---

## Inside a ScaledObject: Activation, Scaling, and Zero

The `ScaledObject` custom resource (API group `keda.sh/v1alpha1`) is the primary interface for connecting a workload to an event source. Understanding its fields in depth is the difference between a configuration that works on the first try and one that thrashes unpredictably.

A minimal ScaledObject has three required sections: `scaleTargetRef` identifies the workload by name and kind (Deployment, StatefulSet, or any custom resource with a `/scale` subresource); `triggers` lists one or more scalers that define where to read the event metric and what target value to maintain; and the scaling boundaries, `minReplicaCount` and `maxReplicaCount`, constrain the range the workload can occupy.

Here is a concrete example — a ScaledObject scaling a consumer deployment on AWS SQS queue depth, with scale-to-zero enabled:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: sqs-worker-scaler
  namespace: production
spec:
  scaleTargetRef:
    name: sqs-worker
  minReplicaCount: 0
  maxReplicaCount: 100
  pollingInterval: 15
  cooldownPeriod: 300
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: "https://sqs.us-west-2.amazonaws.com/123456789/my-queue"
      queueLength: "10"
      awsRegion: "us-west-2"
    authenticationRef:
      name: aws-credentials
```

The fields at work here deserve careful attention because they govern two separate scaling decisions.

**minReplicaCount** and the activation phase. When `minReplicaCount` is set to 0, the KEDA operator enters the activation/deactivation loop. Every `pollingInterval` seconds (here, 15 seconds), the operator invokes the scaler's `IsActive` function, which asks the event source whether work is pending. If the scaler reports a metric value above zero (or above the optional `activationThreshold`), KEDA activates the deployment by setting its replica count to 1. If the metric value returns to zero and stays there for the duration of the `cooldownPeriod` (here, 300 seconds), KEDA deactivates the deployment: it sets replicas to 0 and the workload disappears from the cluster, freeing all compute resources. This is the scale-to-zero loop.

**pollingInterval** controls how frequently KEDA queries the event source. A shorter interval gives faster activation response but increases load on the event source's API, which may incur costs or hit rate limits. A longer interval saves API calls but adds latency between work arrival and pod activation. The default is 30 seconds; for latency-sensitive workloads, 15 seconds is common. For batch workloads where a 60-second delay is acceptable, a longer interval reduces operational overhead.

**cooldownPeriod** is the deactivation gate. After the event source reports no work, KEDA waits this many seconds before scaling the workload to zero. This prevents a pattern where the workload bounces between 0 and 1 replicas — scaling down, then immediately scaling back up because a message arrived during the shutdown window. A cooldown of 300 seconds (5 minutes) gives the workload time to prove it is truly idle. Setting `cooldownPeriod` too low is the single most common cause of thrashing — we will cover this in the Common Mistakes section.

**Activation threshold vs scaling threshold.** Many scalers support separate values for activation and scaling. In the SQS example, `queueLength: "10"` sets the scaling target at 10 messages per replica, meaning the HPA aims for `ceil(queueDepth / 10)` replicas. But the activation threshold — when to go from 0 to 1 — can be different. The optional `activationQueueLength: "5"` would activate at 5 messages, even though steady-state scaling targets 10 messages per replica. This separation is useful when you want aggressive activation (respond to the first sign of work) but conservative steady-state scaling (don't spin up pods for every individual message). When the `activation` counterpart is omitted, the activation threshold defaults to 0, meaning the scaler activates as soon as any work appears.

**Fallback.** KEDA supports a `fallback` section on the ScaledObject that defines what happens when the event source is unreachable. If the scaler fails `failureThreshold` consecutive polls, KEDA sets the workload to `fallback.replicas` — a static replica count that keeps the workload running even without metric data. This prevents the failure mode where a temporary monitoring outage causes KEDA to scale the workload to zero (because it cannot confirm work exists) and then cannot scale it back up (because it still cannot reach the event source). Fallback decouples metric availability from workload availability.

---

## Scalers: The Durable Extensibility Framework

KEDA's scaler catalog — the over 60 built-in event-source connectors — is often presented as a feature list: "KEDA supports Kafka, RabbitMQ, SQS, Prometheus, cron, ..." But the more durable way to think about scalers is as a **category**: an extensibility framework for connecting arbitrary event sources to Kubernetes autoscaling decisions. The list of scalers grows over time, but the category itself — an event source that exposes a metric, which KEDA polls and feeds to the HPA — is stable.

KEDA scalers fall into a few durable families.

**Queue-based scalers** measure pending work directly. The Apache Kafka scaler reads consumer group lag — the difference between the latest offset and the current consumer offset. The RabbitMQ scaler counts messages in a named queue. The AWS SQS, Azure Service Bus, GCP Pub/Sub, and Redis List scalers all follow the same pattern: count the items waiting and scale to match. This is the most natural fit for event-driven autoscaling because the metric — "how many messages are waiting?" — is exactly what we want the autoscaler to respond to.

```yaml
# Kafka: scale on consumer lag
triggers:
- type: kafka
  metadata:
    bootstrapServers: kafka-broker:9092
    consumerGroup: my-consumer-group
    topic: events
    lagThreshold: "100"
```

**Time-based scalers** use the cron scaler to scale a workload on a schedule. This is event-driven in the temporal sense: the "event" is a clock tick at a specific time. The cron scaler accepts `start` and `end` cron expressions and a `desiredReplicas` value. It is ideal for workloads with predictable demand patterns — scaling up before business hours and down overnight — and it composes naturally with other scalers on the same ScaledObject: you can set a cron baseline of 5 replicas during the day and let a queue scaler drive additional scaling on top of that baseline.

```yaml
# Cron: scale to 10 replicas during business hours
triggers:
- type: cron
  metadata:
    timezone: America/New_York
    start: 0 8 * * 1-5
    end: 0 18 * * 1-5
    desiredReplicas: "10"
```

**Query-based scalers** generalise the pattern by allowing arbitrary queries against metric stores and databases. The Prometheus scaler accepts any PromQL query and a threshold value; if the query result exceeds the threshold, KEDA scales up. This opens the door to business-metric-driven autoscaling: scale on "active users per region," "orders per minute," or "unprocessed support tickets." The PostgreSQL and MySQL scalers accept SQL queries and a target value. The Metrics API scaler hits an arbitrary HTTP endpoint and reads a numeric value from the JSON response. These scalers decouple the scaling decision from infrastructure metrics entirely — if you can express the work backlog as a number, you can scale on it.

```yaml
# Prometheus: scale on HTTP request rate
triggers:
- type: prometheus
  metadata:
    serverAddress: http://prometheus.monitoring:9090
    metricName: http_requests_per_second
    query: |
      sum(rate(http_requests_total{app="web-api"}[2m]))
    threshold: "100"
```

```yaml
# PostgreSQL: scale on pending jobs
triggers:
- type: postgresql
  metadata:
    connectionFromEnv: DATABASE_URL
    query: "SELECT COUNT(*) FROM jobs WHERE status = 'pending'"
    targetQueryValue: "10"
```

**The KEDA HTTP Add-on** extends the scaler model to HTTP traffic, a domain KEDA's core scalers do not address directly. The HTTP Add-on installs as a separate component and introduces the `HTTPScaledObject` custom resource. It intercepts incoming HTTP requests through an interceptor proxy, counts pending requests, and feeds that count to a ScaledObject so the workload can scale to zero between requests. This is the event-driven equivalent of a serverless HTTP endpoint — the workload runs only when requests are waiting — and it fills the gap between queue-based autoscaling and the standard Kubernetes Ingress model.

```yaml
# HTTP Add-on: scale on pending requests
apiVersion: http.keda.sh/v1alpha1
kind: HTTPScaledObject
metadata:
  name: web-api
spec:
  hosts:
  - api.example.com
  targetPendingRequests: 100
  scaleTargetRef:
    deployment: web-api
    service: web-api
    port: 80
  replicas:
    min: 0
    max: 50
```

Scalers represent a durable extensibility category: a new event source — a cloud queue, a streaming platform, a proprietary monitoring system — slots into KEDA as a new scaler. The KEDA community and third parties can write external scalers that implement the gRPC scaler interface, making any metric source a potential autoscaling trigger. The scaler catalog is volatile (the list grows), but the scaler *concept* is stable.

---

## ScaledJobs: Event-Driven Batch Processing

The `ScaledJob` custom resource extends KEDA's model from long-running services to run-to-completion batch workloads. Where a ScaledObject adjusts the replica count of a running Deployment, a ScaledJob creates new Kubernetes Jobs in response to events — one Job per event, or one Job per batch of events, depending on the scaler configuration.

This distinction matters because it maps to two fundamentally different workload patterns. A ScaledObject is right for a consumer that runs continuously, pulling messages from a queue and processing them in a loop. A ScaledJob is right when each unit of work is an independent, finite task — transcoding a video, training a model iteration, processing a database export — and you want a fresh, isolated execution environment for each task.

The ScaledJob embeds a `jobTargetRef` that defines the Job template: the container image, command, environment variables, resource requests, and restart policy. When the scaler detects work, KEDA creates one or more Jobs from this template, respecting `maxReplicaCount` as a parallelism cap. Completed Jobs are pruned according to `successfulJobsHistoryLimit` and `failedJobsHistoryLimit`, preventing the cluster from accumulating completed Job objects indefinitely.

```yaml
# ScaledJob: one Job per SQS message
apiVersion: keda.sh/v1alpha1
kind: ScaledJob
metadata:
  name: batch-processor
spec:
  jobTargetRef:
    parallelism: 1
    completions: 1
    backoffLimit: 4
    template:
      spec:
        containers:
        - name: processor
          image: batch-processor:latest
          command: ["/app/process"]
        restartPolicy: Never
  pollingInterval: 30
  maxReplicaCount: 50
  successfulJobsHistoryLimit: 10
  failedJobsHistoryLimit: 10
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: "https://sqs.us-west-2.amazonaws.com/123456/batch-queue"
      queueLength: "1"
```

An important operational consideration for ScaledJobs is the interaction between long-running task execution and the default scaling behaviour. Imagine a ScaledJob with a Kafka trigger where each job processes a batch of messages over 30 minutes. If the Kafka lag drops, KEDA may decide to stop creating new Jobs, but the running Jobs continue until they complete — Kubernetes does not terminate a running Job pod mid-execution just because the scaling signal changed. This is different from a ScaledObject, where the HPA can terminate pods during scale-down. ScaledJobs therefore provide stronger execution guarantees — a Job, once started, runs to completion (or to `backoffLimit` retries) — at the cost of less granular control over total parallelism during rapid demand shifts.

---

## Authenticating to Event Sources

Most scalers need credentials to access the event source — an AWS IAM role to read SQS, a connection string for PostgreSQL, a bearer token for the Metrics API endpoint. KEDA encapsulates authentication in the `TriggerAuthentication` and `ClusterTriggerAuthentication` custom resources, keeping credentials separate from the ScaledObject definition.

A `TriggerAuthentication` is namespace-scoped and referenced by name in the ScaledObject's trigger. It specifies a provider — the authentication method — and the parameters that method requires:

```yaml
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: aws-credentials
  namespace: production
spec:
  podIdentity:
    provider: aws
```

The `podIdentity` provider delegates authentication to the cloud provider's workload identity mechanism — IRSA (IAM Roles for Service Accounts) on AWS, workload identity on GCP, or Azure AD Workload Identity. This is the preferred approach because it avoids static credentials: no access keys in Kubernetes Secrets, no connection strings in environment variables, no credentials that need rotation. The pod assumes the identity of its Kubernetes service account, and the cloud provider issues short-lived tokens.

For environments where pod identity is not available, KEDA supports alternative providers:
- **Environment variables** (`env`): read credentials from a container environment variable, typically injected from a Kubernetes Secret.
- **Secrets** (`secretTargetRef`): reference specific keys within a Kubernetes Secret.
- **HashiCorp Vault**: read secrets from a Vault path.
- **Azure Key Vault** and **GCP Secret Manager**: read secrets from the cloud provider's secret store.

Separating authentication from the scaling configuration is a design pattern worth internalising. When credentials are embedded in the ScaledObject, changing a key or rotating a secret requires editing every ScaledObject that references it — and risks exposing credentials in version control if the YAML is committed. When credentials live in a separate `TriggerAuthentication` resource that references a dynamic secret store, rotation is transparent: update the secret in Vault or Key Vault, and every ScaledObject referencing that authentication continues to work without modification.

---

## Two-Track Scaling: Architecture in Detail

KEDA's architecture diagram shows the flow from event source to running pods, but understanding the *why* of each component makes the diagram actionable rather than decorative.

```
KEDA ARCHITECTURE
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                      KEDA COMPONENTS                             │
│                                                                  │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │ KEDA Operator   │      │ KEDA Metrics    │                  │
│  │                 │      │ Adapter         │                  │
│  │ Watches         │      │                 │                  │
│  │ ScaledObjects   │      │ Exposes         │                  │
│  │ Creates HPA     │      │ external        │                  │
│  │ Scale to zero   │      │ metrics to      │                  │
│  │                 │      │ HPA             │                  │
│  └────────┬────────┘      └────────┬────────┘                  │
│           │                        │                            │
└───────────┼────────────────────────┼────────────────────────────┘
            │                        │
            v                        v
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES API                                │
│                                                                  │
│  ScaledObject --> KEDA --> HPA --> Deployment                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
            │
            │ Query metrics from
            v
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL SOURCES                               │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │   SQS   │  │  Kafka  │  │Prometheus│  │  Cron   │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The scaling flow runs in two complementary tracks.

**Track 1 — Activation (0 to 1, 1 to 0):** This is the KEDA operator's exclusive responsibility. When a ScaledObject has `minReplicaCount: 0`, the operator polls the scaler every `pollingInterval` seconds. If the scaler reports that the event source is active (metric above the activation threshold), the operator sets the deployment's replica count to 1. If the event source has been inactive for `cooldownPeriod` seconds, the operator sets replicas to 0. In this track, the HPA does nothing — it cannot act when there are zero replicas.

**Track 2 — Scaling (1 to N):** Once at least one replica is running, the HPA takes over. The KEDA metrics adapter exposes the scaler's metric value through the `external.metrics.k8s.io` API. The HPA controller queries this API every 15 seconds (the default `--horizontal-pod-autoscaler-sync-period`), computes the desired replica count using the standard HPA formula, and updates the deployment. The KEDA operator continues to monitor the ScaledObject, but during this phase its role is limited to keeping the HPA resource in sync — if someone edits the ScaledObject to change a trigger threshold, the operator updates the HPA accordingly.

This split is why you cannot have both a manual HPA and a KEDA ScaledObject targeting the same Deployment. A ScaledObject creates its own HPA internally. If you also define a separate HorizontalPodAutoscaler for the same Deployment, two controllers will fight over the replica count, producing unpredictable scaling behaviour. The correct approach is to express all triggers — CPU, memory, external metrics — within the ScaledObject's `triggers` list. KEDA does support CPU and memory scalers, but they operate through the HPA's resource metrics API (not the external metrics API), and they do not support scale-to-zero for the reason given earlier: without running pods, there are no CPU or memory metrics to observe.

When a ScaledObject has multiple triggers, KEDA takes the **maximum** of all trigger values when computing the desired replica count. This is the conservative choice: if the Kafka lag calls for 5 replicas and the CPU trigger calls for 3, KEDA scales to 5. The alternative — taking the minimum or an average — would risk under-provisioning for whichever bottleneck is most constrained. For scenarios where maximum-of-triggers is not the right policy, KEDA's scaling modifiers (introduced in version 2.10) allow writing a formula that composes trigger values using arithmetic, conditionals, and nil-coalescing for trigger failover.

---

## Operational Concerns

Operationalising KEDA in production requires attention to several interactions that are not obvious from the initial installation.

**Thundering-herd on cold start.** When a workload scales from zero to one replica after a period of idleness, that first replica faces the entire accumulated work backlog. If the backlog grew over a long cooldown period, the single pod may be overwhelmed, causing high latency or crashes, while the HPA — which only starts its next sync cycle 15 seconds after activation — catches up slowly. Mitigation strategies include: (a) keeping a baseline of at least 1 replica for latency-sensitive workloads (accept the idle cost), (b) setting an activation threshold that triggers activation early, before the backlog grows large, or (c) using the `fallback.replicas` mechanism to maintain a minimum safe replica count when the scaler is unreachable. KEDA's activation mechanism is a binary switch — active or inactive — so the transition from idle to active must be paired with fast HPA scale-out to handle the backlog.

**Scale-to-zero latency tradeoff.** Scale-to-zero eliminates idle cost but adds cold-start latency to every activation. The latency has three components: the `pollingInterval` (up to 30 seconds before KEDA notices the event), the pod scheduling time (seconds to low tens of seconds on a warm node, longer if the cluster autoscaler needs to provision a node), and the application startup time (depends on the image size, initialisation logic, and any external dependencies). For workloads with strict latency SLAs, scale-to-zero may not be appropriate; for batch and background workloads, the tradeoff is almost always favourable.

**Interaction with the cluster autoscaler and Karpenter.** Scaling pods from zero to N requires nodes to run them on. If the cluster is at capacity, the cluster autoscaler or Karpenter must provision a new node before the pods can be scheduled, adding 2 to 4 minutes to the activation latency on most cloud providers. This interaction is not specific to KEDA — it applies to any horizontal pod autoscaling — but KEDA's scale-to-zero capability makes it more visible because the cluster is more likely to be at a state where pods need new nodes after a scale-to-zero period. Operating KEDA effectively means tuning the cluster-level autoscaling to be fast enough for your activation SLAs: overprovisioning warm nodes adds cost, underprovisioning adds latency, and the right balance is workload-specific.

**Not double-managing a workload.** A KEDA-managed workload must not also have a manually defined HPA targeting it. KEDA handles the HPA lifecycle; a second HPA creates a conflicting control loop. Similarly, the Vertical Pod Autoscaler (VPA) can coexist with KEDA/HPA for resource recommendation purposes (right-sizing CPU and memory requests) but must not run in "Auto" mode, where it would change resource requests and potentially evict pods that the HPA is counting on. Use VPA in "Off" or "Initial" mode alongside KEDA — let VPA recommend, but apply the recommendations through your deployment pipeline rather than letting VPA act autonomously.

---

## Landscape Snapshot — as of 2026-06

This snapshot captures the state of the Kubernetes autoscaling landscape at the time of writing. The tools, maturity levels, and feature sets listed here will evolve. Verify against vendor documentation before relying on specifics.

**KEDA** is a CNCF Graduated project (graduated August 2023). It extends Kubernetes with event-driven autoscaling, scales workloads to zero, supports over 60 built-in scalers covering queues, databases, monitoring systems, and cron schedules, and drives scaling through a managed HPA. The HTTP Add-on extends KEDA to HTTP workloads. Version 2.20 is the current stable release as of mid-2026. KEDA installs via Helm (`kedacore/keda`) and runs its own operator, metrics adapter, and admission webhooks within the cluster.

**Kubernetes native HPA** (Horizontal Pod Autoscaler) is built into the Kubernetes control plane. It scales on CPU, memory, and custom/external metrics (with adapter configuration) but cannot scale to zero. The HPA is the correct choice for workloads whose demand correlates linearly with resource consumption and that should always have at least one replica running.

**Kubernetes native VPA** (Vertical Pod Autoscaler) adjusts CPU and memory requests and limits for individual pods based on historical usage, rather than changing the number of replicas. It is complementary to both HPA and KEDA — addressing the "right-size the pod" problem rather than the "how many pods?" problem.

**Cloud-managed autoscalers** (AWS Application Auto Scaling, GCP Managed Instance Groups autoscaling, Azure Autoscale) provide managed, out-of-the-box scaling for compute instances or container services in their respective clouds. They reduce operational burden but tie scaling behaviour to a specific cloud provider's API and pricing model.

### Rosetta: Autoscaling Capability Comparison

| Capability | KEDA | Native HPA | Native VPA | Cloud-Managed |
|---|---|---|---|---|
| Event-driven scaling (queue, stream, DB) | Built-in (60+ scalers) | External metrics adapter required | Not applicable | Varies by provider |
| Scale-to-zero | Yes (core feature) | No (min 1 replica) | No | Supported on some serverless compute |
| Drives through HPA | Yes (creates and manages HPA) | Self (is the HPA) | Not applicable | Usually custom controller |
| Batch/Job scaling | ScaledJob | Not applicable | Not applicable | Varies |
| Architecture | In-cluster operator + metrics adapter | Built-in controller | In-cluster recommender + updater | Provider-managed |
| Maturity (CNCF) | Graduated (2023) | Built-in (GA since 1.8) | Not a CNCF project (K8s SIG) | N/A |

This Rosetta maps durable capabilities to tools. When evaluating an autoscaling decision, ask which capabilities your workload needs and which constraints (operational, cost, cloud-vendor lock-in) you are willing to accept, then select the tool that meets the capability requirement with minimal constraint.

---

## Patterns and Anti-Patterns

### Patterns

**Pattern 1 — Scale on the work, not the symptom.** Write scalers that measure pending work directly. For a queue-based worker, use a queue-length scaler (Kafka lag, SQS queue depth, RabbitMQ message count), not a CPU scaler. The queue depth answers the question "how much work is waiting?"; CPU answers "how busy are the current pods?" and lags behind the real demand.

**Pattern 2 — Baseline with cron, burst with queue.** Combine a cron scaler and a queue scaler on the same ScaledObject. Set the cron scaler to maintain a minimum replica count during business hours (say, 5 replicas from 8 AM to 6 PM) and drop to 0 overnight. The queue scaler adds replicas above the cron baseline when demand spikes. This handles both predictable and unpredictable load in a single configuration.

**Pattern 3 — Separate activation from scaling.** Use an `activationThreshold` lower than the scaling `threshold`. For a Kafka consumer, set `activationLagThreshold: "1"` (activate as soon as any message arrives) but `lagThreshold: "100"` (maintain 100 messages per replica in steady state). This gives fast response to the first work while preventing over-provisioning once the workload is running.

**Pattern 4 — Fallback as a safety net.** Configure `spec.fallback` on every production ScaledObject. A `failureThreshold` of 3 to 5 and a `replicas` value that keeps the workload alive (not zero, not max) ensures that a monitoring outage does not cascade into a workload outage.

### Anti-Patterns

**Anti-Pattern 1 — Cooldown too short.** Setting `cooldownPeriod` to 30 seconds or less on a workload with intermittent activity. The workload scales to 0, a message arrives during the shutdown, KEDA scales back to 1, processes the message, waits 30 seconds, scales to 0 again — and the cycle repeats. Each cycle incurs scheduling and startup overhead. Solution: set `cooldownPeriod` to at least 300 seconds (5 minutes); for very intermittent workloads, even longer.

**Anti-Pattern 2 — Manual HPA and KEDA on the same workload.** Defining a HorizontalPodAutoscaler and a ScaledObject for the same Deployment creates two controllers that both try to set the replica count. The result is oscillating replica counts and confusing metrics. Solution: express all scaling triggers in the ScaledObject; remove the manual HPA.

**Anti-Pattern 3 — Polling interval too aggressive.** Setting `pollingInterval` to 5 seconds for a cloud API scaler (SQS, CloudWatch, Azure Monitor) generates API calls at a rate that may exceed free-tier quotas or hit rate limits. Solution: poll at 30 seconds or longer for cloud APIs; use 15 seconds only for in-cluster metrics (Prometheus, Redis) where API cost is not a concern.

**Anti-Pattern 4 — Executing long-running work in a ScaledObject-managed Deployment.** A Deployment consumer that processes 30-minute tasks is managed by KEDA via an HPA that can terminate pods during scale-down. If the pod is 25 minutes into a task, termination loses the work. Solution: either use a ScaledJob for long-running atomic tasks, or implement graceful shutdown with `terminationGracePeriodSeconds` and `preStop` hooks that finish the current unit of work before the pod exits.

### Decision Framework

When should you reach for KEDA rather than the native HPA? The decision tree below maps the most common scenarios.

```
Autoscaling Decision Framework
---------------------------------------------------------

Does the workload need to scale to zero when idle?
├── Yes ──> Can't use native HPA alone ──> KEDA
├── No ──> Continue...
│
Does the workload's demand signal come from
something other than CPU/memory?
├── Yes ──> Is the signal a queue, stream, or DB query?
│           ├── Yes ──> KEDA (built-in scaler)
│           └── No (custom metric) ──> HPA + custom adapter OR KEDA external scaler
└── No (CPU/memory is sufficient) ──> Native HPA
│
Is the workload batch/job-oriented?
├── Yes ──> KEDA ScaledJob
└── No ──> KEDA ScaledObject or Native HPA
```

---

## Did You Know?

- **KEDA was created by Microsoft and Red Hat** and donated to the CNCF in March 2020. It reached the Incubating maturity level in August 2021 and Graduated in August 2023, making it one of the faster-moving projects through the CNCF maturity pipeline.
- **KEDA's Prometheus scaler can scale on any PromQL query.** Teams have used it for business-metric autoscaling: "active users per region," "orders pending fulfilment," or "unacknowledged alerts." If the business metric is exposed to Prometheus, it can drive autoscaling decisions without custom adapter code.
- **KEDA's scaling modifiers** support a formula language based on the `expr` library, allowing arithmetic, conditionals, and nil-coalescing across multiple triggers. You can express rules like "if the Kafka lag is above 100, use the Kafka trigger; otherwise fall back to the Prometheus query" — trigger-level failover without external orchestration.
- **ScaledJobs clean up after themselves.** The `successfulJobsHistoryLimit` and `failedJobsHistoryLimit` fields control how many completed Job objects KEDA retains. This prevents the etcd database from growing unboundedly with completed Job history, a common operational pitfall with manually managed Jobs in Kubernetes.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Setting `cooldownPeriod` too low (< 60 s) | Workload thrashes between 0 and 1 replicas, incurring scheduling overhead on every activation cycle | Use at least 300 s (5 min); increase for workloads with intermittent activity patterns |
| Setting `queueLength: "1"` without `maxReplicaCount` | Each message creates a new replica; a burst of 1,000 messages requests 1,000 replicas, potentially crashing the cluster | Set `queueLength` to a batch size (10-100 messages per replica) and always define `maxReplicaCount` |
| Defining a manual HPA for a KEDA-managed workload | Two controllers fight over replica count; scaling behaviour is unpredictable and metrics are inconsistent | Remove the manual HPA; express all triggers in the ScaledObject definition |
| Omitting `TriggerAuthentication` for a scaler that needs credentials | The scaler cannot access the event source; the workload stays at 0 replicas with no visible error | Always define and reference a `TriggerAuthentication` for any scaler connecting to an authenticated service |
| Using `minReplicaCount: 0` on a latency-critical service without a warm-up strategy | First request after idle period suffers full cold-start latency (polling + scheduling + startup) | Use `minReplicaCount: 1` or higher for latency-sensitive services; accept the idle-cost tradeoff |
| Polling cloud APIs at very short intervals (< 10 s) | Exceeds free-tier API call quotas; incurs unexpected costs or triggers rate limits | Set `pollingInterval` to 30+ seconds for cloud API scalers; 15 s only for in-cluster metric sources |
| Not configuring `spec.fallback` on production ScaledObjects | A monitoring outage causes the scaler to return errors; KEDA cannot determine the correct replica count and the workload may scale to zero or stall | Define `fallback` with `failureThreshold: 3` and a safe `replicas` value to maintain workload availability during metric outages |
| Forgetting that KEDA creates and manages the HPA internally | Surprise when an HPA appears for the deployment; confusion about why editing the HPA directly has no lasting effect | Understand that the HPA is owned by the ScaledObject; edit the ScaledObject, not the HPA, to change scaling behaviour |

---

## Quiz

### Question 1
What is the fundamental difference between resource-based autoscaling (native HPA) and event-driven autoscaling (KEDA), and why does this distinction matter for scaling accuracy?

<details>
<summary>Answer</summary>

Resource-based autoscaling scales on observed resource consumption — CPU utilisation, memory usage — which are symptoms of work, not measurements of work. Event-driven autoscaling scales on the work itself: queue depth, stream lag, HTTP request rate, or any external metric that directly measures pending work.

This distinction matters because resource metrics are lagging indicators. A workload that is I/O-bound or blocked on external services may have low CPU utilisation even as a queue grows behind it. The HPA sees healthy CPU and does nothing while the backlog builds. Event-driven autoscaling reads the backlog directly and scales before the resource symptoms appear, eliminating the lag between demand arrival and scaling response. Additionally, only event-driven autoscaling supports scale-to-zero, because the event source — not the pod — provides the metric that signals when to scale back up.

</details>

### Question 2
Explain the activation phase and scaling phase in KEDA's two-track architecture. Why are these phases handled by different components?

<details>
<summary>Answer</summary>

KEDA's architecture splits scaling into two phases handled by different components.

The **activation phase** (0 to 1 replica, and 1 to 0) is handled by the KEDA operator. The operator polls the scaler every `pollingInterval` seconds. When the scaler reports that the event source is active (metric above the activation threshold), the operator sets the deployment replica count to 1. When the event source has been inactive for `cooldownPeriod` seconds, the operator sets replicas to 0. This phase must be handled by KEDA because the native HPA cannot act with zero replicas — there are no pods to generate metrics, so the HPA is blind.

The **scaling phase** (1 to N replicas) is handled by the Kubernetes HPA controller. Once at least one replica is running, KEDA's metrics adapter exposes the scaler metrics through the `external.metrics.k8s.io` API, and the HPA controller computes the desired replica count using its standard algorithm. KEDA delegates this phase to the HPA because the HPA's scaling logic is battle-tested, supports stabilisation windows and scaling policies, and is already integrated with the Kubernetes control plane — there is no reason to reimplement it.

This split is the architecture's core insight: KEDA adds only what the HPA lacks (event-source polling and scale-to-zero), and delegates everything else to the standard HPA controller.

</details>

### Question 3
You have configured a ScaledObject with `minReplicaCount: 0` and a queue scaler. The queue receives a single message, but the workload does not activate. What are two possible causes?

<details>
<summary>Answer</summary>

Two common causes:

1. **Missing or misconfigured `TriggerAuthentication`.** If the scaler needs credentials to access the queue (e.g., an AWS IAM role for SQS, a connection string for RabbitMQ) and the `authenticationRef` is not defined or references a `TriggerAuthentication` that does not exist or has incorrect credentials, the scaler cannot read the queue and reports no activity. KEDA stays at 0 replicas with no visible error on the deployment — the failure is in the scaler's ability to connect, not in the scaling decision. Check KEDA operator logs for authentication errors.

2. **The `activation` threshold is set higher than 1.** If the scaler has an `activationQueueLength` or `activationTargetValue` set to a value greater than 1 (e.g., `activationQueueLength: "5"`), a single message will not trigger activation — it is below the threshold. KEDA uses separate activation and scaling thresholds for precisely this reason: you may want to activate only when a minimum batch of work has accumulated. Set `activationQueueLength` to `"1"` or omit it (default 0) for activation on the first message.

</details>

### Question 4
Your deployment processes long-running tasks (approximately 20 minutes each) and is managed by a KEDA ScaledObject with a Kafka scaler. During a scale-down event, the HPA terminates a pod that is 18 minutes into processing a task. What went wrong, and what is the correct fix?

<details>
<summary>Answer</summary>

This is the interaction between long-running tasks and the HPA-driven scale-down of a ScaledObject-managed Deployment. When the HPA decides to scale down (because the Kafka lag dropped below the target), it selects a pod to terminate and sends a `SIGTERM`. The pod has `terminationGracePeriodSeconds` (default 30 seconds) to shut down gracefully. If the pod is in the middle of a 20-minute task, it cannot finish within the grace period — Kubernetes kills it, and the task's progress is lost (unless the application checkpoints or uses at-least-once delivery with idempotent processing in Kafka).

The correct fix depends on the workload pattern. **Option A:** Use a ScaledJob instead of a ScaledObject. ScaledJobs create a new Job per event (or batch), and Jobs run to completion — Kubernetes does not terminate a running Job pod during scale-down. This gives the strongest execution guarantee. **Option B:** Implement graceful shutdown in the consumer. Use a `preStop` lifecycle hook and a long `terminationGracePeriodSeconds` (e.g., 1,800 seconds). When the pod receives `SIGTERM`, the `preStop` hook signals the application to finish its current task, stop pulling new messages, and exit. The application drains its in-flight work before the grace period expires. This works but requires application-level support and blocks scale-down for up to the grace period duration.

The root cause is using a long-running consumer in a Deployment (which the HPA can terminate at any time) when a Job (which runs to completion) is the correct workload primitive.

</details>

### Question 5
You define a ScaledObject with two triggers: a Kafka scaler (`lagThreshold: 100`) and a CPU scaler (`value: "70"`). The Kafka lag suggests 5 replicas, and the CPU utilisation suggests 3 replicas. How many replicas does KEDA request, and why?

<details>
<summary>Answer</summary>

KEDA requests 5 replicas. When a ScaledObject has multiple triggers, KEDA takes the **maximum** of all trigger values when computing the desired replica count.

This is the conservative choice: the trigger demanding the most replicas represents the most constrained resource. If KEDA took the minimum (3 replicas), the Kafka consumer would be under-provisioned — 3 replicas cannot process the queue as fast as 5, and the lag would grow. If KEDA took an average (4 replicas), the consumer would still be slightly under-provisioned for the Kafka lag.

The max-of-triggers policy ensures that the workload is always scaled to meet the most demanding constraint. The tradeoff is that you may occasionally over-provision for other constraints (CPU in this case), but over-provisioning CPU is generally less harmful than under-provisioning queue processing. For scenarios where max-of-triggers is not the right policy, KEDA's scaling modifiers allow defining a custom formula that composes trigger values using arithmetic, conditionals, and nil-coalescing.

</details>

### Question 6
A platform team wants to reduce their cloud compute bill by scaling non-production deployments to zero outside business hours. They deploy KEDA and configure a cron scaler for all staging deployments. After the first weekend, they find that the staging cluster's node count did not decrease. What is the most likely explanation?

<details>
<summary>Answer</summary>

The most likely explanation is that the cluster autoscaler or Karpenter has not scaled down the nodes after the pods were removed. KEDA scaled the deployments to zero replicas, which freed the pods and reduced the workload's compute demand. But the Kubernetes scheduler does not automatically remove nodes — the cluster autoscaler or Karpenter must detect that nodes are underutilised and remove them.

The cluster autoscaler waits for nodes to be underutilised for a configured period (default 10 minutes) before considering them for scale-down. It also checks whether any pods on the node have PodDisruptionBudgets, local storage, or `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"` annotations that would prevent eviction. If other workloads (system daemonsets, monitoring agents, logging sidecars) are still running on those nodes, the autoscaler may consider the nodes "in use" and not remove them.

To get node-level cost savings from KEDA's scale-to-zero, the platform team needs to: (a) ensure the cluster autoscaler is configured and running, (b) check node utilisation after KEDA has scaled down, (c) verify that remaining pods on the nodes do not block scale-down, and (d) consider using node taints or separate node groups for workloads that scale to zero, so the autoscaler can remove entire node groups when they become empty.

</details>

### Question 7
How does KEDA's `ScaledJob` differ from a `CronJob` in Kubernetes, and when would you choose one over the other?

<details>
<summary>Answer</summary>

A Kubernetes `CronJob` creates Jobs on a fixed time schedule — it is **time-driven**: "run this Job every hour" or "run this Job at 2 AM daily." A KEDA `ScaledJob` creates Jobs in response to external events — it is **event-driven**: "run this Job for every message in the queue" or "run this Job when the database query returns a non-zero count."

The operational difference is that a CronJob runs on a schedule regardless of whether there is work to do. If the queue is empty at the scheduled time, the Job still runs, discovers nothing to process, and exits — wasting compute time. A ScaledJob only creates Jobs when the scaler detects work, so it never runs idle.

Choose a CronJob when the task is inherently time-bound: generating a daily report, rotating certificates, renewing TLS certificates, or archiving logs — tasks where the trigger is the calendar, not an external event. Choose a ScaledJob when the task is work-bound: processing messages from a queue, reacting to file uploads in a storage bucket, or running a data pipeline when new data arrives — tasks where the trigger is the arrival of work, and idle runs are wasteful.

</details>

### Question 8
You need to scale an HTTP service to zero when there are no incoming requests, similar to a serverless function. What KEDA component enables this, and how does it differ from the core KEDA scalers?

<details>
<summary>Answer</summary>

The **KEDA HTTP Add-on** enables HTTP-based scale-to-zero. It installs as a separate component from core KEDA and introduces the `HTTPScaledObject` custom resource along with an interceptor proxy that sits in front of the HTTP service.

The core KEDA scalers (Kafka, SQS, Prometheus, etc.) poll external metric sources on a timer (`pollingInterval`). This pull-based model works for queues and monitoring systems but is poorly suited to HTTP: an HTTP request arrives asynchronously, and polling an endpoint to check for pending requests would add latency and complexity. The HTTP Add-on solves this differently: it uses an **interceptor** (an Envoy-based proxy or, in newer versions, a sidecar model) that sits in the request path and buffers incoming requests. When requests are pending, the interceptor signals KEDA to activate the workload. When the buffer is empty, KEDA scales the workload to zero.

This differs from core scalers in two ways. First, it is push-based rather than pull-based — the interceptor pushes activation signals to KEDA when requests arrive, rather than KEDA polling at intervals. This reduces cold-start latency to near-zero for the first queued request. Second, it requires deploying and configuring the interceptor and routing traffic through it, adding operational complexity compared to a queue-based scaler. The HTTP Add-on is the correct tool when you need serverless-style HTTP scaling on Kubernetes without adopting a full serverless platform like KNative.</details>

---

## Hands-On Exercise

### Objective

Deploy KEDA in a Kubernetes cluster, configure event-driven scaling with multiple trigger types, and observe the full activation and scaling lifecycle — including scale-to-zero.

### Environment Setup

```bash
# Add KEDA Helm repository and install into the keda namespace
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda \
  --namespace keda \
  --create-namespace \
  --set watchNamespace=""

# Verify all KEDA components are running
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=keda-operator -n keda --timeout=120s
kubectl get pods -n keda
kubectl get crd | grep keda
```

### Tasks

1. **Deploy a sample consumer application:**

   ```bash
   kubectl apply -f - <<EOF
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: sample-consumer
     labels:
       app: sample-consumer
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: sample-consumer
     template:
       metadata:
         labels:
           app: sample-consumer
       spec:
         containers:
         - name: consumer
           image: nginx
           resources:
             requests:
               cpu: 100m
               memory: 128Mi
   EOF
   ```

2. **Create a ScaledObject with CPU trigger enabling scale-to-zero:**

   ```bash
   kubectl apply -f - <<EOF
   apiVersion: keda.sh/v1alpha1
   kind: ScaledObject
   metadata:
     name: sample-consumer-scaler
   spec:
     scaleTargetRef:
       name: sample-consumer
     minReplicaCount: 0
     maxReplicaCount: 10
     cooldownPeriod: 120
     pollingInterval: 15
     triggers:
     - type: cpu
       metricType: Utilization
       metadata:
         value: "50"
   EOF
   ```

   Note: A CPU scaler with `minReplicaCount: 0` demonstrates the restriction that CPU-based scale-to-zero is not possible — KEDA cannot observe CPU metrics from zero replicas. In this exercise, the min of 0 is set to show that the workload will eventually scale down only when the cooldown elapses with no metrics activity. In practice, use an external scaler (Kafka, SQS, Prometheus) for true scale-to-zero.

3. **Verify scaling infrastructure:**

   ```bash
   kubectl get scaledobject
   kubectl get hpa --watch
   # KEDA creates an HPA automatically for the ScaledObject
   kubectl describe hpa keda-hpa-sample-consumer-scaler
   ```

4. **Add a Prometheus trigger for event-driven scaling:**

   If a Prometheus instance is available in the `monitoring` namespace:

   ```bash
   kubectl patch scaledobject sample-consumer-scaler --type merge -p '
   {
     "spec": {
       "triggers": [
         {
           "type": "cpu",
           "metricType": "Utilization",
           "metadata": { "value": "50" }
         },
         {
           "type": "prometheus",
           "metadata": {
             "serverAddress": "http://prometheus.monitoring:9090",
             "metricName": "http_requests_per_second",
             "query": "sum(rate(nginx_http_requests_total[1m]))",
             "threshold": "100"
           }
         }
       ]
     }
   }'
   ```

5. **Observe the scale-to-zero cycle:**

   ```bash
   # Watch pod count during cooldown
   kubectl get pods -l app=sample-consumer -w

   # After cooldownPeriod with no load, pods should scale to 0
   # Check the ScaledObject status
   kubectl get scaledobject sample-consumer-scaler -o yaml | grep -A 10 status
   ```

### Success Criteria

- [ ] KEDA operator, metrics adapter, and admission webhooks running in the `keda` namespace
- [ ] `ScaledObject` custom resource created and reporting a healthy status
- [ ] HPA resource automatically created by KEDA and referencing the correct deployment
- [ ] Deployment scales to 0 replicas after cooldown period elapses without load
- [ ] HPA scales the deployment from 1 to N replicas when the trigger threshold is exceeded

### Bonus Challenge

Configure a `ScaledJob` that creates one Kubernetes Job for every new message in a Redis list. Use `redis-cli` to push test messages and observe Job creation. Configure `successfulJobsHistoryLimit: 3` and verify that completed Jobs are pruned.

---

## Sources

- [KEDA Concepts — Official Documentation](https://keda.sh/docs/concepts/)
- [KEDA Scaling Deployments Documentation](https://keda.sh/docs/concepts/scaling-deployments/)
- [KEDA Scaling Jobs Documentation](https://keda.sh/docs/concepts/scaling-jobs/)
- [KEDA Scalers Reference](https://keda.sh/docs/scalers/)
- [KEDA Apache Kafka Scaler Documentation](https://keda.sh/docs/scalers/apache-kafka/)
- [KEDA Prometheus Scaler Documentation](https://keda.sh/docs/scalers/prometheus/)
- [KEDA HTTP Add-on Documentation](https://keda.sh/http-add-on/latest/)
- [KEDA GitHub Repository](https://github.com/kedacore/keda)
- [CNCF KEDA Project Page — Graduated Status](https://www.cncf.io/projects/keda/)
- [Kubernetes Horizontal Pod Autoscaling Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Kubernetes Autoscaling Concepts](https://kubernetes.io/docs/concepts/workloads/autoscaling/)

---

## Next Module

Continue to [Module 6.3: Velero](../module-6.3-velero/) to learn backup and disaster recovery for Kubernetes clusters.

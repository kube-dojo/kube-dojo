---
title: "Module 6.2: KEDA"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.2-keda
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

Kubernetes HPA scales on CPU and memory. But what if your app's bottleneck is queue depth? Or database connections? Or time of day? KEDA (Kubernetes Event-Driven Autoscaling) extends Kubernetes autoscaling to virtually any metric—from AWS SQS to Prometheus to cron schedules.

**What You'll Learn**:
- KEDA architecture and scalers
- Scaling to and from zero
- Custom metrics and external triggers
- Combining KEDA with HPA

**Prerequisites**:
- Kubernetes HPA basics
- [SRE Discipline](../../../disciplines/core-platform/sre/) — Scaling concepts
- Understanding of message queues (nice to have)

---

## Why This Module Matters

CPU-based scaling makes sense for compute-bound workloads. But most real applications are I/O-bound—waiting on databases, queues, APIs. KEDA lets you scale on what actually matters: pending messages, request latency, business metrics. Scale to zero when idle, scale up instantly when work arrives.

> 💡 **Did You Know?** KEDA was created by Microsoft and Red Hat, and is now a CNCF graduated project. It supports 60+ built-in scalers for everything from AWS services to Apache Kafka to cron schedules. If you can query it, you can scale on it.

---

## HPA vs KEDA

```
HPA (BUILT-IN KUBERNETES)
════════════════════════════════════════════════════════════════════

What it scales on:
• CPU utilization
• Memory utilization
• Custom metrics (with extra setup)

Limitations:
• Can't scale to zero (minimum 1 replica)
• Limited metric sources
• No event-driven triggers
• Complex custom metrics setup

═══════════════════════════════════════════════════════════════════

KEDA (EXTENDS HPA)
════════════════════════════════════════════════════════════════════

What it scales on:
• All HPA metrics PLUS:
• Message queues (SQS, Kafka, RabbitMQ, Azure Service Bus)
• Databases (PostgreSQL, MySQL, Redis)
• Prometheus queries
• HTTP endpoints
• Cron schedules
• Cloud metrics (CloudWatch, Azure Monitor)
• ... 60+ scalers

Advantages:
• Scales to zero (and back!)
• Simple declarative config
• Event-driven, not just metric-driven
• Works alongside existing HPA
```

---

## Architecture

```
KEDA ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                      KEDA COMPONENTS                             │
│                                                                  │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │ KEDA Operator   │      │ KEDA Metrics    │                  │
│  │                 │      │ Adapter         │                  │
│  │ • Watches       │      │                 │                  │
│  │   ScaledObjects │      │ • Exposes       │                  │
│  │ • Creates HPA   │      │   external      │                  │
│  │ • Scale to zero │      │   metrics to    │                  │
│  │                 │      │   HPA           │                  │
│  └────────┬────────┘      └────────┬────────┘                  │
│           │                        │                            │
│           │                        │                            │
└───────────┼────────────────────────┼────────────────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES API                                │
│                                                                  │
│  ScaledObject ──▶ KEDA ──▶ HPA ──▶ Deployment                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
            │
            │ Query metrics from
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL SOURCES                               │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │   SQS   │  │  Kafka  │  │Prometheus│  │  Cron   │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### How Scaling to Zero Works

```
SCALE TO ZERO MECHANISM
════════════════════════════════════════════════════════════════════

Normal HPA: minimum replicas = 1 (can't go lower)

KEDA adds:
1. ScaledObject with minReplicaCount: 0
2. KEDA watches external metrics
3. When metric = 0 (no messages, no events):
   → KEDA sets deployment replicas to 0
   → Pods terminated, saving resources

4. When metric > 0 (work arrives):
   → KEDA immediately sets replicas to 1
   → HPA takes over for further scaling

Timeline:
─────────────────────────────────────────────────────────────────
No messages    ──▶ 0 pods (sleeping)
Message arrives ──▶ 1 pod (KEDA activates)
More messages   ──▶ HPA scales to N pods
Queue empty     ──▶ Back to 0 pods
```

---

## Installation

```bash
# Add KEDA Helm repo
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

# Install KEDA
helm install keda kedacore/keda \
  --namespace keda \
  --create-namespace \
  --set watchNamespace=""  # Watch all namespaces

# Verify installation
kubectl get pods -n keda
kubectl get crd | grep keda
```

---

## ScaledObject Configuration

### Basic Example: AWS SQS

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: sqs-worker-scaler
  namespace: production
spec:
  scaleTargetRef:
    name: sqs-worker  # Deployment to scale
  minReplicaCount: 0   # Scale to zero when queue empty
  maxReplicaCount: 100
  pollingInterval: 15   # Check every 15 seconds
  cooldownPeriod: 300   # Wait 5 min before scaling down
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-west-2.amazonaws.com/123456789/my-queue
      queueLength: "10"     # Target: 10 messages per replica
      awsRegion: us-west-2
    authenticationRef:
      name: aws-credentials  # TriggerAuthentication reference
```

### AWS Credentials

```yaml
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: aws-credentials
  namespace: production
spec:
  podIdentity:
    provider: aws  # Uses IRSA (IAM Roles for Service Accounts)
```

### Prometheus-Based Scaling

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: http-requests-scaler
spec:
  scaleTargetRef:
    name: web-api
  minReplicaCount: 2    # Keep minimum 2 for availability
  maxReplicaCount: 50
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus.monitoring:9090
      metricName: http_requests_per_second
      query: |
        sum(rate(http_requests_total{app="web-api"}[2m]))
      threshold: "100"  # Target: 100 req/s per replica
```

> 💡 **Did You Know?** KEDA's Prometheus scaler lets you scale on any PromQL query. Teams use it for business metrics like "active users per region" or "orders per minute." If you can express it in PromQL, you can scale on it. This enables true business-driven autoscaling.

---

## Common Scalers

### Message Queues

```yaml
# Apache Kafka
triggers:
- type: kafka
  metadata:
    bootstrapServers: kafka-broker:9092
    consumerGroup: my-consumer-group
    topic: events
    lagThreshold: "100"  # Scale when lag > 100 messages

# RabbitMQ
triggers:
- type: rabbitmq
  metadata:
    host: amqp://guest:guest@rabbitmq:5672/
    queueName: tasks
    queueLength: "50"

# Redis Lists
triggers:
- type: redis
  metadata:
    address: redis:6379
    listName: job-queue
    listLength: "10"
```

### Databases

```yaml
# PostgreSQL - scale based on pending jobs
triggers:
- type: postgresql
  metadata:
    connectionFromEnv: DATABASE_URL
    query: "SELECT COUNT(*) FROM jobs WHERE status = 'pending'"
    targetQueryValue: "10"  # 10 pending jobs per replica

# MySQL
triggers:
- type: mysql
  metadata:
    connectionStringFromEnv: MYSQL_CONNECTION_STRING
    query: "SELECT COUNT(*) FROM orders WHERE processed = 0"
    queryValue: "20"
```

### Time-Based (Cron)

```yaml
# Scale up during business hours
triggers:
- type: cron
  metadata:
    timezone: America/New_York
    start: 0 8 * * 1-5     # 8 AM weekdays
    end: 0 18 * * 1-5      # 6 PM weekdays
    desiredReplicas: "10"

# Scale down at night
- type: cron
  metadata:
    timezone: America/New_York
    start: 0 18 * * 1-5    # 6 PM weekdays
    end: 0 8 * * 1-5       # 8 AM weekdays
    desiredReplicas: "2"
```

> 💡 **Did You Know?** KEDA's cron scaler is perfect for known traffic patterns like business hours, but it can also combine with other scalers. You can set a baseline with cron (minimum 10 replicas during business hours) and let SQS or HTTP metrics scale above that baseline. This "layered scaling" approach handles both predictable and unpredictable load.

### HTTP Metrics

```yaml
# Scale based on response time
triggers:
- type: metrics-api
  metadata:
    url: "http://monitoring-api/metrics"
    valueLocation: "latency_p99"
    targetValue: "200"  # Keep p99 below 200ms
```

---

## Advanced Patterns

### Multiple Triggers

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: multi-trigger-scaler
spec:
  scaleTargetRef:
    name: worker
  minReplicaCount: 1
  maxReplicaCount: 100
  triggers:
  # Scale on queue depth
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-west-2.amazonaws.com/123/main-queue
      queueLength: "10"
  # AND scale on CPU (whichever triggers first)
  - type: cpu
    metricType: Utilization
    metadata:
      value: "70"
  # KEDA uses MAX of all triggers
```

### ScaledJobs for Batch Processing

```yaml
# For Jobs instead of Deployments
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
        restartPolicy: Never
  pollingInterval: 30
  maxReplicaCount: 50
  successfulJobsHistoryLimit: 10
  failedJobsHistoryLimit: 10
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-west-2.amazonaws.com/123/batch-queue
      queueLength: "1"  # One job per message
```

### Scaling HTTP Services (HTTP Add-on)

```yaml
# KEDA HTTP Add-on: scale on pending HTTP requests
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

> 💡 **Did You Know?** KEDA's ScaledJob feature was a game-changer for batch processing. Unlike Deployments (which run continuously), ScaledJobs spin up Jobs on demand—one Job per message, automatically parallelized. Teams processing video uploads, data pipelines, or ML training batches use ScaledJobs to go from zero to 50 parallel workers in seconds, then back to zero when the queue is empty.

---

## Combining KEDA with HPA

```
KEDA + HPA TOGETHER
════════════════════════════════════════════════════════════════════

You CAN'T have both KEDA and HPA on the same Deployment.
KEDA creates an HPA internally.

Instead, use multiple triggers in one ScaledObject:

┌─────────────────────────────────────────────────────────────────┐
│                    ScaledObject                                  │
│                                                                  │
│  triggers:                                                       │
│  - type: prometheus    # Business metric                        │
│  - type: cpu           # Resource metric                        │
│  - type: memory        # Resource metric                        │
│  - type: kafka         # Event metric                           │
│                                                                  │
│  KEDA scales to MAX of all triggers                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Too low cooldownPeriod | Thrashing (scale up/down repeatedly) | Set cooldownPeriod to 5-10 minutes |
| No minReplicaCount on critical services | Zero replicas = outage | Use minReplicaCount: 2 for HA |
| Polling too frequently | High API costs, rate limiting | Use pollingInterval: 30+ seconds |
| Not handling scale-to-zero properly | Cold start latency | Pre-warm or use activation threshold |
| Single trigger for complex apps | Doesn't capture all bottlenecks | Use multiple triggers |
| Forgetting authenticationRef | Scaler can't access metrics | Always configure authentication |

---

## War Story: The Queue That Cried Wolf

*A team set queueLength: "1" on their SQS scaler. Every message triggered a new replica. With bursts of 1000 messages, they'd get 1000 pods—then crash the cluster.*

**What went wrong**:
1. queueLength: "1" means "1 message per replica"
2. 1000 messages → 1000 replicas requested
3. Cluster couldn't handle 1000 pods
4. Everything crashed

**The fix**:
```yaml
triggers:
- type: aws-sqs-queue
  metadata:
    queueLength: "50"   # 50 messages per replica
    activationQueueLength: "1"  # But activate at 1 message

# maxReplicaCount: 20 limits total scale
# activationQueueLength: minimum to activate from zero
```

**Lesson**: `queueLength` is messages PER REPLICA, not total. Set maxReplicaCount to prevent runaway scaling.

---

## Quiz

### Question 1
How is KEDA different from standard HPA?

<details>
<summary>Show Answer</summary>

**Standard HPA**:
- Scales on CPU/memory (built-in)
- Custom metrics require adapter setup
- Minimum 1 replica (can't scale to zero)
- Pulls from metrics API only

**KEDA**:
- 60+ built-in scalers for external metrics
- Scales to zero and back
- Simple declarative config (ScaledObject)
- Event-driven, not just metric-driven
- Creates HPA internally for scaling 1→N

KEDA extends HPA rather than replacing it.

</details>

### Question 2
What's the difference between ScaledObject and ScaledJob?

<details>
<summary>Show Answer</summary>

**ScaledObject**:
- Scales Deployments/StatefulSets
- Long-running pods
- Adjusts replica count
- Good for services (web, workers)

**ScaledJob**:
- Creates new Jobs per event
- Short-lived, run-to-completion pods
- Each trigger creates a new Job
- Good for batch processing, one-time tasks

Use ScaledJob when each message should be processed exactly once by a new pod.

</details>

### Question 3
Why would you set minReplicaCount: 2 instead of 0?

<details>
<summary>Show Answer</summary>

**minReplicaCount: 0** (scale to zero):
- Saves cost when idle
- But: cold start latency when scaling up
- But: no availability during scale-up

**minReplicaCount: 2** (always running):
- Instant response (no cold start)
- High availability (survives 1 pod failure)
- Costs more during idle periods

Use 0 for: batch jobs, dev environments, cost-sensitive non-critical services

Use 2+ for: production services, latency-sensitive APIs, critical workloads

</details>

---

## Hands-On Exercise

### Objective
Deploy KEDA and configure scaling based on Prometheus metrics.

### Environment Setup

```bash
# Install KEDA
helm install keda kedacore/keda -n keda --create-namespace

# Wait for KEDA
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=keda-operator -n keda --timeout=120s

# Ensure Prometheus is running (from Observability Toolkit)
# kubectl get pods -n monitoring -l app=prometheus
```

### Tasks

1. **Deploy sample app**:
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: sample-app
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: sample-app
     template:
       metadata:
         labels:
           app: sample-app
       spec:
         containers:
         - name: app
           image: nginx
           resources:
             requests:
               cpu: 100m
               memory: 128Mi
   EOF
   ```

2. **Create ScaledObject with CPU trigger**:
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: keda.sh/v1alpha1
   kind: ScaledObject
   metadata:
     name: sample-app-scaler
   spec:
     scaleTargetRef:
       name: sample-app
     minReplicaCount: 0
     maxReplicaCount: 10
     cooldownPeriod: 60
     triggers:
     - type: cpu
       metricType: Utilization
       metadata:
         value: "50"
   EOF
   ```

3. **Verify ScaledObject**:
   ```bash
   kubectl get scaledobject
   kubectl get hpa  # KEDA creates this
   ```

4. **Watch scaling**:
   ```bash
   kubectl get pods -w
   ```

5. **Test scale to zero** (wait for cooldown):
   ```bash
   # After cooldownPeriod with no load, pods should scale to 0
   kubectl get pods
   ```

6. **Add Prometheus trigger** (if Prometheus available):
   ```yaml
   triggers:
   - type: prometheus
     metadata:
       serverAddress: http://prometheus.monitoring:9090
       query: |
         sum(rate(nginx_http_requests_total[1m]))
       threshold: "100"
   ```

### Success Criteria
- [ ] KEDA operator running
- [ ] ScaledObject created
- [ ] HPA created automatically by KEDA
- [ ] Deployment scales to 0 after cooldown (no load)
- [ ] Deployment scales up when trigger threshold exceeded

### Bonus Challenge
Configure a cron trigger that scales the app to 5 replicas during work hours (9 AM - 5 PM) and 1 replica otherwise.

---

## Further Reading

- [KEDA Documentation](https://keda.sh/docs/)
- [KEDA Scalers](https://keda.sh/docs/scalers/)
- [KEDA HTTP Add-on](https://github.com/kedacore/http-add-on)

---

## Next Module

Continue to [Module 6.3: Velero](../module-6.3-velero/) to learn backup and disaster recovery for Kubernetes clusters.

---

*"Scale on what matters, not just what's easy to measure. KEDA makes any metric a scaling trigger."*

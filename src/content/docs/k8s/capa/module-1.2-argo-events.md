---
title: "Module 1.2: Argo Events \u2014 Event-Driven Automation for Kubernetes"
slug: k8s/capa/module-1.2-argo-events/
sidebar:
  order: 3
---
> **Complexity**: `[COMPLEX]` — Multiple interacting CRDs and integration patterns
>
> **Time to Complete**: 50-60 minutes
>
> **Prerequisites**: Module 1 (Argo Workflows basics), familiarity with Kubernetes CRDs
>
> **CAPA Domain**: 4 — Argo Events (12% of exam)

---

## Why This Module Matters

Imagine you push code to GitHub. You want a build to start. You upload a file to S3. You want a processing pipeline to kick off. A cron timer fires at midnight. You want a cleanup workflow to run.

Without Argo Events, teams build fragile glue: polling scripts, webhook receivers hacked together in Flask, cron jobs that shell out to `kubectl`. When one of those breaks at 3 AM, nobody knows why.

Argo Events gives Kubernetes a native nervous system — events flow in, decisions are made, actions are triggered. No polling. No glue code. Everything declared in YAML, version-controlled, and observable.

If the CAPA exam gives you 12% for this domain, that is roughly 7-8 questions. You need to know the architecture, the CRDs, and how events flow from source to action.

> **War Story: The Polling Team**
>
> A platform team at a fintech company had 14 CronJobs that polled GitHub every 60 seconds looking for new commits across their monorepo. Each poller ran `curl` against the GitHub API, parsed JSON with `jq`, compared SHAs stored in a ConfigMap, and triggered builds via `kubectl create`. The GitHub API rate-limited them twice a week. The ConfigMap had race conditions. One Friday, a poller overwrote another poller's SHA and triggered 200+ duplicate builds that saturated their cluster. The migration to Argo Events took three days. They replaced 14 CronJobs and ~400 lines of bash with 3 EventSources, 1 EventBus, and 5 Sensors. The polling stopped. The rate-limiting stopped. The 3 AM pages stopped.

---

## Did You Know?

- **Argo Events processes millions of events daily** at companies like Intuit, Tesla, and BlackRock — it is not a toy project but production-grade infrastructure.
- **CloudEvents is a CNCF graduated specification** — Argo Events adopted it early, meaning your event payloads are portable across any CloudEvents-compatible system.
- **The EventBus uses NATS JetStream by default** — giving you at-least-once delivery, persistence, and replay without managing a separate message broker.
- **A single Sensor can watch multiple EventSources** with AND/OR logic — so you can express "trigger only when BOTH the GitHub push AND the security scan complete" in pure YAML.

---

## Part 1: Event-Driven Architecture (EDA) Fundamentals

### 1.1 Why Events?

There are two ways to detect that something happened:

| Approach | How It Works | Downside |
|----------|-------------|----------|
| **Polling** | Ask "did anything change?" on a timer | Wastes resources, delayed detection, API rate limits |
| **Reactive (events)** | Get notified the instant something changes | Requires event infrastructure |

Events win because they are **immediate**, **efficient**, and **decoupled**. The producer does not know or care who consumes the event. The consumer does not know or care how the event was produced.

### 1.2 The CloudEvents Specification

CloudEvents is the CNCF standard envelope for event data. Argo Events uses it internally.

```json
{
  "specversion": "1.0",
  "type": "com.github.push",
  "source": "https://github.com/myorg/myrepo",
  "id": "A234-1234-1234",
  "time": "2025-11-05T17:31:00Z",
  "datacontenttype": "application/json",
  "data": {
    "ref": "refs/heads/main",
    "commits": [{"message": "fix: update config"}]
  }
}
```

Key fields: `specversion`, `type`, `source`, `id`. Every event has these. The `data` field carries the actual payload.

---

## Part 2: Argo Events Architecture

### 2.1 The Four Components

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ARGO EVENTS ARCHITECTURE                      │
│                                                                      │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────────┐  │
│  │  EventSource   │    │   EventBus     │    │     Sensor         │  │
│  │                │    │  (NATS         │    │                    │  │
│  │  - Webhook     │───▶│   JetStream)   │───▶│  - Dependencies   │  │
│  │  - GitHub      │    │                │    │  - Filters         │  │
│  │  - S3          │    │  Namespace-    │    │  - Trigger         │  │
│  │  - Cron        │    │  scoped msg    │    │    templates       │  │
│  │  - Kafka       │    │  broker        │    │                    │  │
│  │  - SNS/SQS     │    │                │    │                    │  │
│  └────────────────┘    └────────────────┘    └───────┬────────────┘  │
│                                                      │               │
│                                                      ▼               │
│                                            ┌────────────────────┐    │
│                                            │    Triggers        │    │
│                                            │                    │    │
│                                            │  - Argo Workflow   │    │
│                                            │  - K8s Resource    │    │
│                                            │  - HTTP Request    │    │
│                                            │  - Notification    │    │
│                                            └────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

The data flow is always left-to-right:

1. **EventSource** — Connects to the outside world (GitHub, S3, webhooks, etc.) and publishes events
2. **EventBus** — The internal transport layer; receives events and makes them available to Sensors
3. **Sensor** — Listens for specific events, applies filters, evaluates dependency logic
4. **Trigger** — The action taken when a Sensor's conditions are met (start a workflow, create a resource, etc.)

### 2.2 How the Pieces Connect

```
GitHub push ──▶ EventSource "github" ──▶ EventBus "default"
                                              │
S3 upload ────▶ EventSource "s3" ─────▶ EventBus "default"
                                              │
                                              ▼
                                     Sensor "build-on-push"
                                     (depends on: github push)
                                              │
                                              ▼
                                     Trigger: submit Argo Workflow
```

Each component is a **separate Kubernetes Custom Resource**. You deploy them independently.

---

## Part 3: EventSource

The EventSource is where events enter the system. Each EventSource CR can define multiple named event producers of the **same type**.

### 3.1 Webhook EventSource

The simplest starting point — expose an HTTP endpoint that receives POST requests:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: webhook-events
spec:
  webhook:
    build-trigger:
      port: "12000"
      endpoint: /build
      method: POST
    deploy-trigger:
      port: "12000"
      endpoint: /deploy
      method: POST
```

This creates a pod that listens on port 12000 with two endpoints. Any POST to `/build` or `/deploy` publishes an event to the EventBus.

### 3.2 GitHub EventSource

Listens for GitHub webhook events (push, PR, issues, etc.):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: github-events
spec:
  github:
    code-push:
      repositories:
        - owner: myorg
          names:
            - myrepo
      webhook:
        endpoint: /push
        port: "13000"
        method: POST
        url: https://events.example.com
      events:
        - push
        - pull_request
      apiToken:
        name: github-access       # K8s Secret name
        key: token                 # Key within the Secret
      webhookSecret:
        name: github-access
        key: webhook-secret
```

### 3.3 S3 EventSource

Watches an S3-compatible bucket for object changes:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: s3-events
spec:
  s3:
    data-upload:
      bucket:
        name: data-pipeline-input
      events:
        - s3:ObjectCreated:*
      filter:
        prefix: "uploads/"
        suffix: ".csv"
      endpoint: s3.amazonaws.com
      region: us-east-1
      accessKey:
        name: s3-credentials
        key: accesskey
      secretKey:
        name: s3-credentials
        key: secretkey
```

### 3.4 Calendar (Cron) EventSource

Time-based events — replaces CronJobs for event-driven pipelines:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: calendar-events
spec:
  calendar:
    nightly-cleanup:
      schedule: "0 0 * * *"       # Midnight daily
      timezone: "America/New_York"
    hourly-check:
      schedule: "0 * * * *"       # Every hour
      timezone: "UTC"
```

### 3.5 Other EventSource Types

| Type | Use Case |
|------|----------|
| **Kafka** | Consume messages from Kafka topics |
| **AWS SNS** | Subscribe to SNS topics |
| **AWS SQS** | Poll SQS queues |
| **GCP PubSub** | Subscribe to Pub/Sub topics |
| **NATS** | Consume from NATS subjects |
| **Redis Streams** | Consume from Redis streams |
| **Slack** | Slash commands and interactive messages |
| **Generic** | Any custom event source via a sidecar container |

The exam may test whether you know which EventSource type to use for a given scenario. Know the table above.

---

## Part 4: EventBus

The EventBus is the internal message broker. It decouples EventSources from Sensors.

### 4.1 Creating the Default EventBus

By convention, you create one EventBus named `default` per namespace. If no `eventBusName` is specified in EventSource/Sensor specs, they use `default`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventBus
metadata:
  name: default
spec:
  jetstream:
    version: "2.9.22"
    replicas: 3
    persistence:
      storageClassName: standard
      volumeSize: 10Gi
```

### 4.2 EventBus Backends

| Backend | Status | Notes |
|---------|--------|-------|
| **JetStream** (NATS) | Recommended | At-least-once delivery, persistence, built-in |
| **Kafka** | Supported | Use when you already run Kafka and want a single broker |
| **STAN** | Deprecated | Legacy NATS Streaming; migrate to JetStream |

### 4.3 Key Properties

- **Namespace-scoped**: Each namespace gets its own EventBus. Events do not cross namespace boundaries by default.
- **Managed lifecycle**: Argo Events deploys and manages the JetStream/Kafka pods for you.
- **Multiple EventBuses**: You can create more than one EventBus in a namespace and reference them by name in your EventSource/Sensor specs using `eventBusName`.

---

## Part 5: Sensor

The Sensor is where logic lives. It declares which events it cares about (dependencies), how to filter them, and what action to take (triggers).

### 5.1 Basic Sensor Structure

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: build-sensor
spec:
  dependencies:
    - name: github-push
      eventSourceName: github-events
      eventName: code-push
  triggers:
    - template:
        name: trigger-build
        argoWorkflow:
          operation: submit
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
              metadata:
                generateName: build-
              spec:
                entrypoint: build
                templates:
                  - name: build
                    container:
                      image: golang:1.22
                      command: [make, build]
```

### 5.2 Event Dependencies — AND/OR Logic

By default, when a Sensor lists multiple dependencies, **all must be satisfied** (AND logic). You can customize this:

```yaml
spec:
  dependencies:
    - name: github-push
      eventSourceName: github-events
      eventName: code-push
    - name: security-scan
      eventSourceName: webhook-events
      eventName: scan-complete
  # AND logic (default): trigger fires when BOTH events arrive
```

For OR logic, define separate triggers that each reference a single dependency:

```yaml
spec:
  dependencies:
    - name: github-push
      eventSourceName: github-events
      eventName: code-push
    - name: manual-trigger
      eventSourceName: webhook-events
      eventName: build-trigger
  triggers:
    - template:
        name: build-on-push
        conditions: "github-push"     # fires on github-push alone
        argoWorkflow:
          # ...workflow spec...
    - template:
        name: build-on-manual
        conditions: "manual-trigger"  # fires on manual-trigger alone
        argoWorkflow:
          # ...workflow spec...
```

The `conditions` field supports boolean expressions: `"github-push && security-scan"`, `"github-push || manual-trigger"`.

### 5.3 Dependency Filters

Filter events before they reach the trigger. Only matching events proceed.

**Data filter** — filter on the event payload:

```yaml
dependencies:
  - name: github-push
    eventSourceName: github-events
    eventName: code-push
    filters:
      data:
        - path: body.ref
          type: string
          value:
            - "refs/heads/main"
```

This fires only for pushes to the `main` branch.

**Expression filter** — complex boolean expressions over event data:

```yaml
filters:
  exprs:
    - expr: body.action == "opened" || body.action == "synchronize"
      fields:
        - name: body.action
          path: body.action
```

**Context filter** — filter on CloudEvents metadata (type, source, subject):

```yaml
filters:
  context:
    type: com.github.push
    source: myorg/myrepo
```

You can combine all three filter types. They are evaluated with AND logic — all filters must pass.

---

## Part 6: Triggers

The trigger is the action. When a Sensor's dependencies and filters are satisfied, the trigger fires.

### 6.1 Argo Workflow Trigger

The most common trigger — submit an Argo Workflow:

```yaml
triggers:
  - template:
      name: run-build
      argoWorkflow:
        operation: submit        # submit, resubmit, resume, retry, stop, terminate
        source:
          resource:
            apiVersion: argoproj.io/v1alpha1
            kind: Workflow
            metadata:
              generateName: build-
            spec:
              entrypoint: main
              arguments:
                parameters:
                  - name: git-sha
              templates:
                - name: main
                  container:
                    image: builder:latest
                    command: [./build.sh]
        parameters:
          - src:
              dependencyName: github-push
              dataKey: body.after      # Git SHA from the push event
            dest: spec.arguments.parameters.0.value
```

The `parameters` section is critical — it maps event data into the Workflow's arguments. `src.dataKey` uses dot notation to traverse the event JSON. `dest` is the JSON path in the Workflow resource where the value is injected.

### 6.2 Kubernetes Resource Trigger

Create or update any Kubernetes resource:

```yaml
triggers:
  - template:
      name: create-namespace
      k8s:
        operation: create
        source:
          resource:
            apiVersion: v1
            kind: Namespace
            metadata:
              generateName: pr-env-
        parameters:
          - src:
              dependencyName: github-pr
              dataKey: body.number
            dest: metadata.labels.pr-number
```

### 6.3 HTTP Trigger

Call an external HTTP endpoint:

```yaml
triggers:
  - template:
      name: notify-slack
      http:
        url: https://hooks.slack.com/services/T00/B00/XXXX
        method: POST
        headers:
          Content-Type: application/json
        payload:
          - src:
              dependencyName: github-push
              dataKey: body.head_commit.message
            dest: text
```

### 6.4 Trigger Conditions Summary

| Trigger Type | Use Case |
|-------------|----------|
| `argoWorkflow` | Start CI/CD pipelines, data processing, ML training |
| `k8s` | Create/patch any K8s resource (ConfigMap, Job, Namespace) |
| `http` | Call external APIs, send notifications |
| `log` | Debug — print event to sensor logs |

---

## Part 7: Authentication and Secrets

Never put tokens or passwords in your EventSource YAML. Always reference Kubernetes Secrets.

### 7.1 Webhook Secrets

GitHub webhook secrets validate that incoming requests truly come from GitHub:

```yaml
# Create the secret
kubectl create secret generic github-access \
  --from-literal=token=ghp_xxxxxxxxxxxxx \
  --from-literal=webhook-secret=mysecretvalue

# Reference in EventSource
spec:
  github:
    code-push:
      apiToken:
        name: github-access
        key: token
      webhookSecret:
        name: github-access
        key: webhook-secret
```

### 7.2 S3 / Cloud Provider Credentials

```yaml
kubectl create secret generic s3-credentials \
  --from-literal=accesskey=AKIAIOSFODNN7EXAMPLE \
  --from-literal=secretkey=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 7.3 Kafka Authentication

For SASL/TLS-authenticated Kafka clusters:

```yaml
spec:
  kafka:
    events:
      url: kafka-broker:9093
      topic: events
      tls:
        caCertSecret:
          name: kafka-tls
          key: ca.crt
      sasl:
        mechanism: PLAIN
        userSecret:
          name: kafka-sasl
          key: user
        passwordSecret:
          name: kafka-sasl
          key: password
```

**Exam tip**: If a question asks how to securely pass credentials to an EventSource, the answer is always Kubernetes Secrets referenced by `name` and `key`.

---

## Part 8: Integration with Argo Workflows

### 8.1 Passing Event Data as Workflow Parameters

This is the most testable pattern on the CAPA exam. The flow:

```
GitHub push event
  └─▶ Sensor extracts body.after (commit SHA)
       └─▶ Injects into Workflow spec.arguments.parameters.0.value
            └─▶ Workflow template uses {{workflow.parameters.git-sha}}
```

The parameter mapping in the Sensor trigger:

```yaml
parameters:
  - src:
      dependencyName: github-push
      dataKey: body.after           # JSON path in event payload
    dest: spec.arguments.parameters.0.value  # JSON path in Workflow resource
```

### 8.2 Passing Event Data to Multiple Parameters

```yaml
parameters:
  - src:
      dependencyName: github-push
      dataKey: body.after
    dest: spec.arguments.parameters.0.value
  - src:
      dependencyName: github-push
      dataKey: body.repository.full_name
    dest: spec.arguments.parameters.1.value
  - src:
      dependencyName: github-push
      dataKey: body.ref
    dest: spec.arguments.parameters.2.value
```

### 8.3 Using a WorkflowTemplate Reference

Instead of embedding the full Workflow spec in the Sensor, reference a WorkflowTemplate:

```yaml
triggers:
  - template:
      name: trigger-build
      argoWorkflow:
        operation: submit
        source:
          resource:
            apiVersion: argoproj.io/v1alpha1
            kind: Workflow
            metadata:
              generateName: build-
            spec:
              workflowTemplateRef:
                name: build-pipeline
              arguments:
                parameters:
                  - name: git-sha
                    value: placeholder    # will be overwritten by parameter mapping
        parameters:
          - src:
              dependencyName: github-push
              dataKey: body.after
            dest: spec.arguments.parameters.0.value
```

This is the recommended pattern — keep your Workflow logic in WorkflowTemplates and your event wiring in Sensors.

---

## Part 9: Practical Patterns

### Pattern 1: GitHub Push Triggers a Build

```
┌──────────┐     ┌──────────────┐     ┌─────────┐     ┌──────────────┐
│  GitHub   │────▶│ EventSource  │────▶│ EventBus│────▶│    Sensor    │
│  webhook  │     │ (github)     │     │(default)│     │ (build-on-   │
└──────────┘     └──────────────┘     └─────────┘     │   push)      │
                                                       └──────┬───────┘
                                                              │
                                                              ▼
                                                       ┌──────────────┐
                                                       │ Argo Workflow│
                                                       │ (build +     │
                                                       │  test + push)│
                                                       └──────────────┘
```

### Pattern 2: S3 Upload Triggers a Data Processing Pipeline

EventSource watches for `.csv` files in `uploads/`. Sensor triggers a multi-step Workflow that validates, transforms, and loads the data.

```yaml
# EventSource
spec:
  s3:
    csv-upload:
      bucket:
        name: data-pipeline
      events:
        - s3:ObjectCreated:*
      filter:
        prefix: "uploads/"
        suffix: ".csv"

# Sensor trigger passes the object key to the Workflow
parameters:
  - src:
      dependencyName: csv-upload
      dataKey: notification.0.s3.object.key
    dest: spec.arguments.parameters.0.value
```

### Pattern 3: Cron Schedule Triggers a Cleanup Workflow

No external events — just a timer. The calendar EventSource fires nightly, and the Sensor submits a cleanup Workflow.

```yaml
# EventSource
spec:
  calendar:
    nightly:
      schedule: "0 2 * * *"       # 2 AM daily
      timezone: "UTC"

# Sensor — no data mapping needed, just submit the Workflow
triggers:
  - template:
      name: nightly-cleanup
      argoWorkflow:
        operation: submit
        source:
          resource:
            apiVersion: argoproj.io/v1alpha1
            kind: Workflow
            metadata:
              generateName: cleanup-
            spec:
              workflowTemplateRef:
                name: cleanup-old-resources
```

---

## Common Mistakes

| Mistake | Why It Happens | Solution |
|---------|---------------|----------|
| No EventBus created | People deploy EventSource + Sensor and forget the bus | Always create an EventBus named `default` in the namespace first |
| Wrong `dataKey` path | Event payload structure is not what you expected | Use a `log` trigger first to print the raw event, then build your path |
| Sensor dependency name mismatch | Typo between `dependencies[].name` and `triggers[].parameters[].src.dependencyName` | Copy-paste the dependency name; do not retype it |
| Secrets in wrong namespace | Secret exists in `default` but EventSource is in `argo-events` | Secrets must be in the same namespace as the EventSource that references them |
| Webhook not reachable | EventSource pod has no Ingress or Service exposing it | Create a Service and Ingress/Route for the EventSource pod's port |
| STAN backend used in new install | Old tutorials still reference STAN | Always use JetStream — STAN is deprecated |
| Filters too broad | Sensor fires on every push, not just `main` | Add a data filter on `body.ref` to match `refs/heads/main` |

---

## Quiz

Test your understanding before the hands-on exercise.

**Question 1**: What are the four Argo Events CRDs in order of data flow?

<details>
<summary>Answer</summary>

EventSource, EventBus, Sensor, Trigger (the trigger is defined within the Sensor CR, not a separate CRD — but the conceptual flow is EventSource → EventBus → Sensor → Trigger action).

</details>

**Question 2**: What is the recommended EventBus backend, and what technology does it use?

<details>
<summary>Answer</summary>

JetStream, which is built on NATS. It provides at-least-once delivery with persistence. STAN (NATS Streaming) is deprecated.

</details>

**Question 3**: How do you make a Sensor trigger only when events from two different EventSources BOTH arrive?

<details>
<summary>Answer</summary>

List both as dependencies in the Sensor spec. By default, all dependencies use AND logic — the trigger fires only when all dependencies are satisfied. You can also be explicit with the `conditions` field: `"dep-one && dep-two"`.

</details>

**Question 4**: A GitHub EventSource is deployed but events never reach the Sensor. The EventBus pods are running. What is the most likely issue?

<details>
<summary>Answer</summary>

The EventSource pod's webhook port is not exposed to the internet. GitHub cannot deliver webhooks to a pod that has no Service, Ingress, or external URL. Check that the `webhook.url` in the EventSource spec is reachable from GitHub and that a Service/Ingress routes traffic to the correct port.

</details>

**Question 5**: How do you pass the Git commit SHA from a GitHub push event into an Argo Workflow parameter?

<details>
<summary>Answer</summary>

In the Sensor trigger's `parameters` section, set `src.dependencyName` to the dependency name, `src.dataKey` to `body.after` (the field in the GitHub push payload that contains the new SHA), and `dest` to the JSON path in the Workflow resource, e.g., `spec.arguments.parameters.0.value`.

</details>

**Question 6**: What is the scope of an EventBus? Can events published in namespace A be consumed by a Sensor in namespace B?

<details>
<summary>Answer</summary>

The EventBus is namespace-scoped. Events published to the EventBus in namespace A are only available to Sensors in namespace A. Cross-namespace event delivery is not supported by default. If you need cross-namespace communication, use an external broker (Kafka) or HTTP triggers between namespaces.

</details>

**Question 7**: You want a Sensor to fire on GitHub push events, but ONLY for pushes to the `main` branch. Which filter type do you use and what does it look like?

<details>
<summary>Answer</summary>

Use a data filter on the dependency:

```yaml
filters:
  data:
    - path: body.ref
      type: string
      value:
        - "refs/heads/main"
```

This inspects the event payload and only allows events where `body.ref` equals `refs/heads/main`.

</details>

---

## Hands-On Exercise: Event-Driven Build Pipeline

### Goal

Deploy a complete Argo Events pipeline: a webhook EventSource receives a POST, publishes to the EventBus, a Sensor picks it up, and triggers an Argo Workflow that prints the event data.

### Prerequisites

- A running Kubernetes cluster (kind or minikube)
- Argo Events installed (`kubectl create namespace argo-events && kubectl apply -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/install.yaml`)
- Argo Workflows installed (from Module 1)

### Step 1: Create the EventBus

```bash
cat <<'EOF' | k apply -n argo-events -f -
apiVersion: argoproj.io/v1alpha1
kind: EventBus
metadata:
  name: default
spec:
  jetstream:
    version: "2.9.22"
    replicas: 3
EOF
```

Wait for the EventBus pods:

```bash
k get pods -n argo-events -l eventbus-name=default --watch
```

**Success criteria**: 3 JetStream pods in `Running` state.

### Step 2: Create the Webhook EventSource

```bash
cat <<'EOF' | k apply -n argo-events -f -
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: webhook
spec:
  webhook:
    build:
      port: "12000"
      endpoint: /build
      method: POST
EOF
```

Verify the EventSource pod starts:

```bash
k get pods -n argo-events -l eventsource-name=webhook
```

**Success criteria**: EventSource pod is `Running`.

### Step 3: Create the Sensor with Workflow Trigger

```bash
cat <<'EOF' | k apply -n argo-events -f -
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: build-sensor
spec:
  dependencies:
    - name: webhook-build
      eventSourceName: webhook
      eventName: build
  triggers:
    - template:
        name: trigger-workflow
        argoWorkflow:
          operation: submit
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
              metadata:
                generateName: event-build-
              spec:
                entrypoint: print-event
                arguments:
                  parameters:
                    - name: message
                templates:
                  - name: print-event
                    inputs:
                      parameters:
                        - name: message
                    container:
                      image: alpine:3.19
                      command: [sh, -c]
                      args:
                        - echo "Received event data:" && echo "{{inputs.parameters.message}}"
          parameters:
            - src:
                dependencyName: webhook-build
                dataKey: body.project
              dest: spec.arguments.parameters.0.value
EOF
```

### Step 4: Fire an Event

Port-forward to the EventSource pod and send a webhook:

```bash
k port-forward -n argo-events svc/webhook-eventsource-svc 12000:12000 &

curl -X POST http://localhost:12000/build \
  -H "Content-Type: application/json" \
  -d '{"project": "kubedojo", "branch": "main", "commit": "abc123"}'
```

### Step 5: Verify the Workflow Was Triggered

```bash
k get workflows -n argo-events
k logs -n argo-events -l workflows.argoproj.io/workflow  # check the output
```

**Success criteria**: A Workflow named `event-build-xxxxx` appears and completes with output `Received event data: kubedojo`.

### Cleanup

```bash
k delete sensor build-sensor -n argo-events
k delete eventsource webhook -n argo-events
k delete eventbus default -n argo-events
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| EDA vs Polling | Events are immediate and efficient; polling wastes resources and hits rate limits |
| EventSource | Entry point — connects external systems to the EventBus |
| EventBus | Internal broker (JetStream recommended), namespace-scoped |
| Sensor | Decision-maker — dependencies, filters, AND/OR logic |
| Triggers | Actions — submit Workflows, create K8s resources, call HTTP endpoints |
| Filters | Data, expression, and context filters narrow which events fire triggers |
| Secrets | Always use K8s Secrets; never inline credentials |
| Parameter mapping | `src.dataKey` extracts from event, `dest` injects into trigger resource |

---

## Next Module

[Module 3: Argo CD — GitOps Delivery](../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/) — Declarative, Git-driven continuous delivery for Kubernetes.

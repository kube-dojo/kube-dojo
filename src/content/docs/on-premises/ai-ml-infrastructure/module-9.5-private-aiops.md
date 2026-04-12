---
title: "Private AIOps"
description: Implement anomaly detection, predictive scaling, and AI-augmented incident response on bare-metal Kubernetes using Robusta, Prometheus, and local LLMs.
sidebar:
  order: 95
---

# Private AIOps

Operating Kubernetes on bare metal often involves strict data privacy, compliance, or air-gapped constraints that preclude the use of SaaS observability platforms like Datadog, New Relic, or cloud-vendor AIOps tools. Private AIOps brings machine learning (ML) and artificial intelligence (AI) directly into your cluster to automate root cause analysis (RCA), detect metric anomalies, and execute self-healing workflows without transmitting cluster state or telemetry over the internet.

This module covers the architecture and implementation of in-cluster AIOps, focusing on localized telemetry anomaly detection, AI-augmented incident response using Robusta and local Large Language Models (LLMs), and predictive scaling.

## Learning Outcomes

* **Design** an air-gapped, privacy-preserving AIOps architecture using local LLMs and open-source telemetry pipelines.
* **Configure** Robusta to enrich Prometheus alerts with cluster context and AI-generated root cause analysis without relying on external SaaS APIs.
* **Implement** statistical anomaly detection rules in Prometheus and VictoriaMetrics to replace brittle static alerting thresholds.
* **Evaluate** predictive scaling mechanisms against reactive Horizontal Pod Autoscaler (HPA) behaviors for spiky workloads.
* **Establish** operational guardrails to constrain automated self-healing workflows, preventing cascading failures caused by AI hallucinations or aggressive remediation loops.

## Architectural Paradigms for Private AIOps

A Private AIOps stack shifts the computational burden of telemetry analysis and natural language reasoning to the local cluster infrastructure. 

:::tip
Running local LLMs and ML models requires dedicated GPU resources or significant CPU overhead. On bare metal, isolate these workloads using node selectors, taints, and tolerations (e.g., `nvidia.com/gpu`) to prevent them from starving critical control plane or application workloads.
:::

The architecture consists of four distinct pillars:

1. **Telemetry Ingestion & Storage:** Prometheus, VictoriaMetrics, or Thanos for metrics; Vector or Fluent Bit for logs.
2. **Anomaly Detection Engine:** Statistical engines (VictoriaMetrics `vmanomaly`) or advanced PromQL queries that generate dynamic alerts based on historical baselines rather than static thresholds.
3. **Incident Response & Automation:** Robusta or custom Kubernetes Operators acting as the glue between alerts, cluster state, and the AI backend.
4. **Local AI Backend:** An OpenAI-compatible API serving local models (e.g., Ollama or vLLM running Llama 3, Qwen, or Mistral).

```mermaid
graph TD
    subgraph Bare-Metal Cluster
        P[Prometheus / VictoriaMetrics] -->|Fires Alert| A[Alertmanager]
        A -->|Webhook| R[Robusta Runner]
        
        K[kube-apiserver] -.->|Fetch Pod Logs / Events| R
        
        R -->|System Prompt + Context| L[Local LLM via vLLM/Ollama]
        L -->|RCA & Remediation Steps| R
        
        R -->|Formats Message| S[Notification Sink: Slack/Teams/Email]
        R -->|Trigger Playbook| K
    end
```

### Trade-offs: Local vs. SaaS AIOps

| Feature | Private AIOps (Local LLM / vmanomaly) | SaaS AIOps (Datadog / OpenAI) |
| :--- | :--- | :--- |
| **Data Privacy** | Absolute. Telemetry never leaves the cluster. | High risk. Cluster state and secrets may leak in prompts. |
| **Latency** | Dependent on local GPU/CPU hardware. Can be slow. | Low latency for API calls, fast inference. |
| **Model Capability** | Limited by local VRAM (typically 7B-70B parameter models). | State-of-the-art reasoning (GPT-4, Claude 3.5 Sonnet). |
| **Cost** | High CapEx (GPUs, power, cooling). Zero OpEx. | Low CapEx. High, unpredictable OpEx based on token usage. |

## Anomaly Detection in Cluster Metrics

Static thresholds in Prometheus (`container_memory_usage_bytes > 8Gi`) inevitably lead to alert fatigue. Workloads have diurnal patterns, weekly cycles, and seasonal spikes. Anomaly detection identifies deviations from expected patterns.

### PromQL Statistical Baselines

Before deploying complex ML models, leverage Prometheus's native statistical functions. You can calculate a rolling baseline using `avg_over_time` and standard deviations with `stddev_over_time` to detect anomalies based on Z-scores.

```yaml
# prometheus-rules.yaml
groups:
- name: node-anomaly-detection
  rules:
  - record: node:cpu_usage:z_score
    expr: >
      (
        instance:node_cpu_utilisation:rate1m
        -
        avg_over_time(instance:node_cpu_utilisation:rate1m[1w])
      )
      /
      stddev_over_time(instance:node_cpu_utilisation:rate1m[1w])

  - alert: NodeCPUUsageAnomaly
    expr: node:cpu_usage:z_score > 3 # 3 standard deviations above the 1-week norm
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Anomalous CPU usage detected on {{ $labels.instance }}"
```

:::caution
PromQL evaluation of long time windows (`[1w]`) is extremely memory-intensive. On large clusters, this will cause Prometheus OOM kills. Offload these calculations to Thanos Ruler or VictoriaMetrics.
:::

### Machine Learning with VictoriaMetrics Anomaly Detection (vmanomaly)

For environments already utilizing VictoriaMetrics, `vmanomaly` provides an external service that queries historical data, applies ML models (like Prophet or Holt-Winters), and pushes an anomaly score metric (`anomaly_score`) back into the time-series database.

A typical `vmanomaly` configuration defines a model and a schedule:

```yaml
# vmanomaly-config.yaml
models:
  prophet_model:
    class: "prophet"
    args:
      interval_width: 0.98

reader:
  datasource_url: "http://victoria-metrics:8428"
  queries:
    ingress_latency: "histogram_quantile(0.99, sum(rate(nginx_ingress_controller_request_duration_seconds_bucket[5m])) by (le, ingress))"

writer:
  datasource_url: "http://victoria-metrics:8428"
```

You then alert on the resulting metric:

```yaml
  - alert: IngressLatencyAnomaly
    expr: anomaly_score{model="prophet_model", query_name="ingress_latency"} > 1.0
    for: 5m
```

## AI-Augmented Incident Response with Robusta

When an alert fires, engineers waste minutes (or hours) manually gathering context: running `kubectl get events`, checking logs, and viewing associated Grafana dashboards. Robusta automates this triage phase.

Robusta consists of an in-cluster runner that intercepts Alertmanager webhooks, runs predefined Python "playbooks" to gather cluster state, and forwards the enriched package to a sink.

### Integrating Local LLMs

To utilize Robusta for RCA without leaking data to OpenAI, you must point Robusta's AI features to a local, OpenAI-compatible endpoint. Ollama or vLLM are the standard choices.

The LLM is prompted with the alert details, recent events, and pod logs. The model returns a structured RCA and suggested remediation steps.

**Prerequisite hardware:** A 7B parameter model (e.g., `llama3.1:8b` or `mistral`) requires ~6-8GB of VRAM. A 70B parameter model requires ~40GB of VRAM. For pure log analysis and RCA, smaller models often suffice if the system prompt is well-engineered.

### Configuring the Robusta LLM Endpoint

In your `values.yaml` for the Robusta Helm chart, override the ChatGPT integration settings to point to your in-cluster LLM service:

```yaml
# robusta-values.yaml
globalConfig:
  chat_gpt_api_key: "dummy-key" # Required by the API client, but ignored by Ollama
  chat_gpt_endpoint: "http://ollama.monitoring.svc.cluster.local:11434/v1"
  chat_gpt_model: "llama3.1:8b" # Must match the model pulled in Ollama

sinksConfig:
  - slack_sink:
      name: main_slack_sink
      slack_channel: "production-alerts"
      api_key: "xoxb-your-slack-bot-token"

enablePrometheusStack: false # Set to false if you already have kube-prometheus-stack
```

When Robusta receives an alert (e.g., `CrashLoopBackOff`), it automatically queries the local endpoint, analyzes the crash logs, and appends the AI's explanation to the Slack message.

## Predictive Scaling

Standard Horizontal Pod Autoscaler (HPA) is reactive. It scales up *after* CPU spikes or queue lengths increase. This causes a cold-start latency window where incoming requests are dropped or degraded while new pods initialize.

Predictive scaling analyzes historical metric patterns to scale out proactively, *before* the anticipated load arrives.

### KEDA Predictive Scaling

KEDA (Kubernetes Event-driven Autoscaling) can integrate with predictive models via external metric scalers. While native predictive scaling in KEDA is still maturing, the standard pattern involves deploying a custom metrics API server that exposes predictions generated by an ML model as standard Kubernetes custom metrics.

Alternatively, operators use tools like **Predictive Horizontal Pod Autoscaler (PHPA)** which acts as a drop-in replacement or wrapper around the standard HPA. It fetches historical metrics, runs statistical models (like Holt-Winters), and overrides the replica count ahead of time.

### The Dangers of Black-Box Scaling

Predictive scaling introduces significant operational risk. If the model hallucinates a traffic spike (e.g., due to anomalous historical data from a previous outage), it may scale deployments to their maximum limits, exhausting node resources and starving other workloads.

**Guardrails for Predictive Scaling:**
1. **Tight `maxReplicas` bounds:** Never set `maxReplicas` arbitrarily high. Cap it at 120% of your known peak capacity.
2. **Fallback to Reactive HPA:** If the predictive metric server goes down or returns NaN, the system must immediately fall back to standard CPU/Memory reactive scaling.
3. **Ignore Anomaly Windows:** The training pipeline for the predictive model must strip out data generated during outages or DDoS attacks, otherwise the model will predict "outages" as standard seasonal traffic.

## Self-Healing Workflows and Guardrails

The ultimate goal of AIOps is automated remediation: the system detects an anomaly, the LLM determines the fix, and an operator applies it. On bare metal, automated remediation usually involves node cordoning, pod evictions, restarting deadlocked services, or rolling back deployments.

### Implementing Playbooks

Robusta allows you to define custom Python playbooks triggered by specific Prometheus alerts.

```yaml
# Example Robusta custom playbook trigger
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: HighErrorRate
    actions:
      - custom_rollback_action:
          namespace: "{{ alert.labels.namespace }}"
          deployment: "{{ alert.labels.deployment }}"
```

### The "Human-in-the-Loop" Mandate

Permitting an LLM to autonomously execute state-mutating commands (`kubectl delete`, `kubectl rollout undo`) is a severe anti-pattern in production environments. Models hallucinate, and incorrect remediation can transform a localized failure into a cluster-wide outage.

**Strict Guardrails for Remediation:**
1. **Read-Only Service Accounts:** The RBAC token mounted to the AIOps engine must strictly be bound to `get`, `list`, and `watch` verbs.
2. **Action Suggestions, Not Execution:** The LLM should generate the specific `kubectl` commands required to fix the issue and output them in the notification sink. The human operator copies, validates, and executes the command.
3. **Approval Webhooks:** If automated execution is required, implement a Slack interactive button (e.g., "Approve Rollback"). The button triggers an intermediary service that validates the request against an allowlist of permitted actions before executing it with elevated privileges.
4. **Rate Limiting:** If a self-healing loop initiates, it must be rate-limited. If a node is cordoned and workloads are evicted, the system must wait for cluster stabilization before cordoning a second node. Failure to rate-limit can lead to all nodes being cordoned simultaneously.

## Hands-on Lab: AI-Enriched Alerting with Robusta and Local LLMs

In this lab, you will deploy a local Ollama instance running a small LLM, install Robusta, and configure it to intercept a failing Pod alert, utilizing the local AI to explain the failure.

### Prerequisites
* A Kubernetes cluster (v1.32+). `kind` or `minikube` is sufficient if you have at least 8GB of RAM available.
* `helm` and `kubectl` installed.
* `kube-prometheus-stack` installed in the `monitoring` namespace.

### Step 1: Deploy Local LLM (Ollama)

Deploy Ollama to serve the AI model locally. We will use `llama3.2:1b` for lab environments due to its low memory footprint. In production, use a larger model.

Create `ollama.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:0.5.4
        ports:
        - containerPort: 11434
        # Allocate sufficient resources. Adjust based on your hardware.
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            memory: "8Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: monitoring
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
```

Apply the manifests:
```bash
kubectl apply -f ollama.yaml
```

Wait for the pod to be ready, then exec into it to pull the model:
```bash
kubectl wait --for=condition=ready pod -l app=ollama -n monitoring --timeout=120s
kubectl exec -it deploy/ollama -n monitoring -- ollama run llama3.2:1b
```
*(Type `/bye` to exit the Ollama prompt once the model is pulled).*

### Step 2: Configure and Install Robusta

Generate a Robusta configuration. You will need a Robusta account for the UI sink (optional) or you can configure a Slack sink. For this lab, we will configure Robusta to use the local Ollama instance and output to stdout for verification.

Create `robusta-values.yaml`:

```yaml
globalConfig:
  cluster_name: "lab-cluster"
  # Point to the local Ollama service using the OpenAI compatibility layer
  chat_gpt_endpoint: "http://ollama.monitoring.svc.cluster.local:11434/v1"
  chat_gpt_model: "llama3.2:1b"
  chat_gpt_api_key: "dummy-key" # Required field, but ignored by Ollama

sinksConfig:
  # Output alerts to the robusta-runner logs for easy viewing in the lab
  - stdout_sink:
      name: main_stdout_sink

enablePlatform: false # Disable cloud UI for true private AIOps
enablePrometheusStack: false # We assume you already have Prometheus

# Configure the AI enrichment playbook
customPlaybooks:
  - triggers:
      - on_prometheus_alert: {}
    actions:
      - ask_chat_gpt:
          prompt: "Analyze this Prometheus alert and the provided Kubernetes context. Provide a concise root cause analysis and exactly two kubectl commands to investigate or remediate the issue."
```

Install Robusta via Helm:
```bash
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update
helm install robusta robusta/robusta -f robusta-values.yaml -n monitoring
```

Verify the runner is active:
```bash
kubectl get pods -n monitoring -l app=robusta-runner
# EXPECTED: READY 1/1
```

### Step 3: Configure Alertmanager to forward to Robusta

Update your `kube-prometheus-stack` values to forward alerts to Robusta.

```yaml
# prometheus-values.yaml
alertmanager:
  config:
    route:
      receiver: 'robusta'
      group_by: ['alertname', 'namespace']
      group_wait: 10s
      group_interval: 1m
      repeat_interval: 4h
    receivers:
      - name: 'robusta'
        webhook_configs:
          - url: 'http://robusta-runner.monitoring.svc.cluster.local/api/alerts'
            send_resolved: true
```

Apply the update:
```bash
helm upgrade kube-prometheus-stack prometheus-community/kube-prometheus-stack -f prometheus-values.yaml -n monitoring
```

### Step 4: Trigger an Alert and Verify AI Enrichment

Deploy a failing pod to trigger a standard `KubePodCrashLooping` or `KubePodNotReady` alert.

```yaml
# crashing-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: failing-app
  namespace: default
  labels:
    app: failing
spec:
  containers:
  - name: app
    image: busybox
    command: ["/bin/sh", "-c", "echo 'Connecting to database...'; sleep 2; exit 1"]
```

```bash
kubectl apply -f crashing-pod.yaml
```

Wait 5-10 minutes for Prometheus to fire the alert and Alertmanager to route it to Robusta.

Tail the Robusta runner logs to observe the AI enrichment:
```bash
kubectl logs -f deploy/robusta-runner -n monitoring
```

**Expected Output (Truncated):**
You should see Robusta intercept the webhook, make an HTTP POST to the Ollama endpoint, and output the enriched alert containing the LLM's response.

```text
[INFO] Triggering playbook ask_chat_gpt for alert KubePodCrashLooping
[INFO] Querying LLM endpoint http://ollama.monitoring.svc.cluster.local:11434/v1
...
[STDOUT_SINK] Alert: KubePodCrashLooping in default
AI Analysis: The pod 'failing-app' is in a CrashLoopBackOff state. The logs indicate the process exits with code 1 immediately after printing "Connecting to database...". This suggests a missing configuration, network policy blocking DB access, or missing credentials.

Suggested Actions:
1. View detailed pod events: `kubectl describe pod failing-app -n default`
2. Check recent logs: `kubectl logs failing-app -n default --previous`
```

### Troubleshooting
* **LLM Connection Refused:** Ensure the Ollama pod is running and the service endpoint `http://ollama.monitoring.svc.cluster.local:11434` resolves from within the `robusta-runner` pod.
* **Alerts not arriving:** Check Alertmanager logs (`kubectl logs statefulset/alertmanager-kube-prometheus-stack-alertmanager -n monitoring`) to ensure the webhook to Robusta is succeeding.
* **OOMKilled Ollama:** Local LLMs consume significant memory. If the Ollama pod restarts with `OOMKilled`, increase the memory limits or use a smaller model quantization (e.g., `q4_0`).

## Practitioner Gotchas

* **Context Window Truncation:** Feeding `kubectl describe pod` and 500 lines of logs into a local LLM will rapidly exceed the model's context window (often 8k tokens for smaller models), resulting in truncated prompts or HTTP 500 errors. Implement log tailing limits (e.g., last 50 lines) before sending data to the AI backend.
* **LLM API Timeout Constraints:** Robusta and Alertmanager webhooks expect relatively fast responses. Inference on CPU-only bare metal nodes for a 8B parameter model can take 30-60 seconds. This will cause webhook timeouts. You must increase Alertmanager webhook timeout configurations or ensure GPU acceleration for the LLM inference server.
* **Hallucinated Kubernetes Objects:** LLMs confidently hallucinate CRDs and specific resource names. An AI might suggest running `kubectl restart deployment/db-backend` when the actual resource is a StatefulSet named `postgres-db`. Never pipe AI output directly into `bash` or `kubectl`.
* **Standard Deviation Alert Flapping:** Using Z-scores for anomaly detection on metrics with low baseline variance (e.g., a service that receives exactly 1 request per hour) will cause minor fluctuations to appear as massive anomalies (Z-score > 10). Always combine statistical anomaly detection with an absolute minimum threshold (e.g., `z_score > 3 AND rate > 100`).

## Quiz

**1. You are configuring Robusta to use a local LLM running in your cluster to ensure strict data privacy. The Robusta Helm chart requires a `chat_gpt_api_key`. What is the correct approach?**
* A) Leave the field empty or comment it out; the local API doesn't need it.
* B) Provide a dummy string; the OpenAI compatible client requires the field to be populated, but the local backend (like Ollama) will ignore it.
* C) Generate an API key from the OpenAI platform and use it to authenticate the local traffic.
* D) Configure the Robusta runner RBAC to read the key dynamically from the `kube-system` namespace.
<details>
<summary>Answer</summary>
**Correct Answer: B.** The underlying Python OpenAI client library used by Robusta strictly requires an API key string to initialize, even if the base URL is pointed to a local unauthenticated service like Ollama. A dummy string satisfies the client.
</details>

**2. Which of the following is a critical operational guardrail when implementing Predictive Horizontal Pod Autoscaling (PHPA)?**
* A) Setting the minimum replica count to zero to maximize resource utilization during off-peak hours.
* B) Ensuring the predictive model has admin access to the cluster to create new node pools.
* C) Capping the `maxReplicas` to a conservative boundary (e.g., 120% of expected peak) to prevent hallucinated traffic spikes from exhausting cluster resources.
* D) Disabling the reactive HPA entirely to prevent conflict with the predictive scaler.
<details>
<summary>Answer</summary>
**Correct Answer: C.** Predictive models can hallucinate or over-predict based on dirty historical data. Tight `maxReplicas` bounds prevent the scaler from requesting infinite pods and crashing the cluster.
</details>

**3. When implementing PromQL-based anomaly detection using Z-scores (`expr: node:cpu_usage:z_score > 3`), you notice the alert is flapping continuously on a low-traffic development cluster. What is the most likely architectural flaw?**
* A) The standard deviation is too high, masking the true anomalies.
* B) The baseline time window (`1w`) is too short to capture standard variance.
* C) Evaluating long time windows is causing Prometheus to silently drop metrics.
* D) The metric has a near-zero baseline variance, meaning tiny absolute changes generate massive Z-scores.
<details>
<summary>Answer</summary>
**Correct Answer: D.** If a baseline is perfectly flat, the standard deviation approaches zero. Any minor change divided by near-zero results in a massive Z-score, triggering the anomaly alert. You must add an absolute minimum threshold to the rule.
</details>

**4. Why is routing automated remediation playbooks directly from an LLM to the Kubernetes API server (e.g., `kubectl delete pod`) considered a severe anti-pattern?**
* A) The API server rate limits incoming requests from service accounts by default.
* B) LLMs hallucinate resource names and remediation steps, which can escalate a localized failure into a cluster outage if executed autonomously.
* C) Robusta does not support executing commands against the local cluster.
* D) Local LLMs cannot process JSON output required by the Kubernetes API.
<details>
<summary>Answer</summary>
**Correct Answer: B.** LLMs lack situational awareness and absolute determinism. They may hallucinate a fix that destroys healthy resources. Human-in-the-loop verification is mandatory for destructive actions.
</details>

**5. You are running a 7B parameter local LLM for private AIOps on bare metal without GPUs. You notice that Robusta often fails to attach AI summaries to Slack alerts, and the Robusta logs show `HTTP 504 Gateway Timeout`. What is the primary cause?**
* A) The Alertmanager webhook timeout is shorter than the CPU-bound inference time required by the LLM.
* B) Robusta cannot communicate with services in the `monitoring` namespace.
* C) The LLM's context window has been exceeded by the size of the Slack payload.
* D) The Slack API is rejecting messages that contain AI-generated content.
<details>
<summary>Answer</summary>
**Correct Answer: A.** Inference on CPU is slow. Generating a response might take 30-60 seconds, which easily exceeds standard webhook timeout defaults (often 10s or 15s) configured in Alertmanager or the Robusta client.
</details>

## Further Reading

* [Robusta Official Documentation: Custom LLMs](https://docs.robusta.dev/master/configuration/ai-analysis/custom-llms.html)
* [VictoriaMetrics Anomaly Detection (vmanomaly) Guide](https://docs.victoriametrics.com/vmanomaly/)
* [KEDA Predictive Scaling Discussion (GitHub)](https://github.com/kedacore/keda/issues/2301)
* [Ollama Kubernetes Deployment Examples](https://github.com/ollama/ollama/tree/main/docs)
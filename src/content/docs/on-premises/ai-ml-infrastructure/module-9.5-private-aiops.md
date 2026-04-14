---
title: "Private AIOps"
description: Implement anomaly detection, predictive scaling, and AI-augmented incident response on bare-metal Kubernetes using Robusta, Prometheus, and local LLMs.
slug: on-premises/ai-ml-infrastructure/module-9.5-private-aiops
sidebar:
  order: 95
---

# Private AIOps

## Why This Module Matters

In April 2023, Samsung Electronics experienced a severe data exposure incident when semiconductor engineers pasted highly confidential source code and internal meeting notes into a public SaaS LLM to debug errors and optimize workflows. Within weeks, the company realized its most sensitive intellectual property had been ingested into a public model's training data. The financial and strategic impact was immeasurable, forcing the company to temporarily ban external generative AI tools across its devices and internal networks, effectively crippling their engineers' ability to use modern AI-assisted debugging until private alternatives could be built.

This incident perfectly illustrates the central conflict of modern platform engineering: the capabilities of AIOps and Large Language Models (LLMs) are far too powerful to ignore, but the risk of exfiltrating internal telemetry, cluster state, and proprietary logs to external SaaS platforms is too great for regulated environments. Operating Kubernetes on bare metal often involves strict data privacy, compliance, or air-gapped constraints that preclude the use of SaaS observability platforms like Datadog, New Relic, or cloud-vendor AIOps tools. You simply cannot forward your Alertmanager webhooks to a public API when those payloads contain sensitive customer data.

Private AIOps solves this dilemma by bringing the intelligence to the data, rather than sending the data to the intelligence. By deploying local anomaly detection engines and strictly constrained local LLMs within the cluster boundary, organizations achieve the automated root-cause analysis (RCA) and predictive self-healing of modern SaaS tools while maintaining absolute data sovereignty. This module dives deep into architecting that private intelligence layer without compromising cluster stability or data security.

## Learning Outcomes

* **Design** an air-gapped, privacy-preserving AIOps architecture using local LLMs and open-source telemetry pipelines.
* **Configure** Robusta to enrich Prometheus alerts with cluster context and AI-generated root cause analysis without relying on external SaaS APIs.
* **Implement** statistical anomaly detection rules in Prometheus and VictoriaMetrics to replace brittle static alerting thresholds.
* **Evaluate** predictive scaling mechanisms against reactive Horizontal Pod Autoscaler (HPA) behaviors for spiky workloads.
* **Establish** operational guardrails to constrain automated self-healing workflows, preventing cascading failures caused by AI hallucinations or aggressive remediation loops.
* **Diagnose** performance bottlenecks when executing local LLM inference on standard bare-metal Kubernetes nodes.

## Did You Know?

* **Prometheus v3.11.1** is the current stable release (released April 7, 2026), continuing the legacy of a project that was the second ever to reach CNCF Graduated status on August 9, 2018.
* **OpenTelemetry** production adoption has exploded, tripling from 3% to 10% year-over-year according to the CNCF 2026 Observability Summit data.
* **Grafana OnCall OSS** entered maintenance mode on March 11, 2025, and completely archived its cloud-connected features by March 24, 2026, pushing bare-metal operators toward independent local responders.
* **Apache Kafka v4.2.0** (released February 17, 2026) remains a massive data backbone, yet interestingly, the CNCF landscape does not have a dedicated "AIOps" category; tooling spans the Observability, Machine Learning, and AI Inference categories.

## The Landscape of Private AIOps

When building a private AIOps stack, you are stitching together projects from disparate domains. The underlying orchestration for data pipelines often relies on Argo Workflows v4.0.4 (released April 2, 2026). If you are training custom anomaly detection models, you might utilize Kubeflow v1.10 (released March 31, 2025, and holding CNCF Incubating status). Kubeflow follows a reliable twice-yearly release cadence aligned with KubeCon EU (March) and KubeCon NA (October). 

For experiment tracking and model registry, teams widely adopt MLflow. Notably, MLflow is governed by the Linux Foundation AI & Data (LF AI & Data), not the CNCF. 

### State of the Ecosystem Note
Because the open-source data landscape moves rapidly, versioning requires nuance. For instance, OpenSearch has moved to the v3.x major version line, and MLflow is broadly supported at v3.10+, though exact patch numbers shift constantly. While the community generally understands Kafka 4.x aims to run exclusively in KRaft mode by removing ZooKeeper entirely, definitive confirmation requires checking the Apache Kafka 4.0 release notes directly. Similarly, while Elasticsearch includes Machine Learning capabilities for anomaly detection, verifying exactly which Elastic Subscription tier includes these features requires checking their current pricing page. Community research suggests SigNoz is around v0.114.1 as of early 2026, and while the parent Argo Project is a CNCF project, the specific graduation status of Argo Workflows alone requires direct verification on the CNCF directory.

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

### Telemetry Ingestion & Storage Deep Dive

Single-node Prometheus is rarely sufficient for AIOps, which requires months of historical data to train accurate models. You must offload long-term storage to Thanos (CNCF Incubating, accepted August 19, 2020) or Cortex (CNCF Incubating, accepted August 20, 2020). 

For unified ingestion, the OpenTelemetry Collector v0.149.0 (released March 31, 2026) is the definitive industry standard. For logging, Grafana Loki v3.7 is the current stable release. Crucially, operators must realize that Promtail officially reached end-of-life on March 2, 2026, and its functionality was merged into Grafana Alloy. Migration to Alloy is required for modern Loki deployments. Furthermore, Loki Helm charts migrated from the `grafana/helm-charts` repository to `grafana-community/helm-charts` effective March 16, 2026. Tracing is handled by Grafana Tempo v2.10.0, tying into the broader Grafana stable release line at v12.x.

### Anomaly Detection Engines: Beyond Static Thresholds

Static thresholds (e.g., alerting when `container_memory_usage_bytes > 8Gi`) inevitably lead to alert fatigue. Workloads have diurnal patterns, weekly cycles, and seasonal spikes. Anomaly detection identifies deviations from expected patterns. Various tools offer embedded intelligence:

* **OpenSearch Anomaly Detection:** Uses the Random Cut Forest (RCF) algorithm to detect anomalies in streaming log data natively.
* **Netdata:** In v2.10.1, Netdata trains an ensemble of 18 ML models per metric locally at the data source, using consensus to minimize false positives.
* **Grafana Machine Learning:** While Grafana offers powerful ML-based anomaly detection and forecasting (like the Sift tool), these features are strictly available only in Grafana Cloud and Grafana Enterprise, not in the open-source distribution.
* **VictoriaMetrics:** The `vmanomaly` component is powerful, but requires an Enterprise license key since v1.5.0 and cannot run in production without it.

#### PromQL Statistical Baselines

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

> **Stop and think**: Why is `avg_over_time` combined with `stddev_over_time` inherently memory-intensive in Prometheus, and how does Thanos or Cortex mitigate this architectural limitation? 
> *(Answer: Single-node Prometheus must load every single data point for that metric over the last week into active memory to compute the standard deviation, easily causing OOM kills. Thanos mitigates this through query pushdown and parallel processing across multiple remote store gateways.)*

#### Machine Learning with VictoriaMetrics Anomaly Detection (vmanomaly)

For enterprise environments already utilizing VictoriaMetrics, `vmanomaly` provides an external service that queries historical data, applies ML models (like Prophet or Holt-Winters), and pushes an anomaly score metric (`anomaly_score`) back into the time-series database.

A typical `vmanomaly` configuration defines a model and a schedule. Notice the `interval_width` parameter defining the confidence boundary:

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

To utilize Robusta for RCA without leaking data to OpenAI, you must point Robusta's AI features to a local, OpenAI-compatible endpoint. Ollama or vLLM are the standard choices. The LLM is prompted with the alert details, recent events, and pod logs. The model returns a structured RCA and suggested remediation steps.

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

> **Pause and predict**: If you apply a Holt-Winters predictive scaling model to a deployment that suffered a massive DDoS attack exactly one week ago, how will the autoscaler behave today, assuming it uses a standard 7-day seasonality window?
> *(Answer: The model will perceive the historical DDoS attack as a seasonal traffic spike and scale your replicas to maximum capacity today, potentially starving other critical cluster resources. This highlights the danger of blind predictive scaling.)*

### The Dangers of Black-Box Scaling

Predictive scaling introduces significant operational risk. If the model hallucinates a traffic spike, it may scale deployments to their maximum limits.

**Guardrails for Predictive Scaling:**
1. **Tight `maxReplicas` bounds:** Never set `maxReplicas` arbitrarily high. Cap it at 120% of your known peak capacity.
2. **Fallback to Reactive HPA:** If the predictive metric server goes down or returns NaN, the system must immediately fall back to standard CPU/Memory reactive scaling.
3. **Ignore Anomaly Windows:** The training pipeline for the predictive model must strip out data generated during outages or attacks.

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

## Trade-offs: Local vs SaaS AIOps

Visualizing the dichotomy between local and SaaS AIOps reveals fundamental architectural choices.

```mermaid
graph TD
    A[AIOps Architectural Trade-offs] --> B[Private AIOps]
    A --> C[SaaS AIOps]
    
    B --> B1[Data Privacy: Absolute. Telemetry never leaves the cluster.]
    B --> B2[Latency: Dependent on local hardware. Can be slow.]
    B --> B3[Model Capability: Limited by VRAM 7B-70B.]
    B --> B4[Cost: High CapEx, Zero OpEx.]
    
    C --> C1[Data Privacy: High risk. Cluster state may leak.]
    C --> C2[Latency: Low latency for API calls, fast inference.]
    C --> C3[Model Capability: State-of-the-art reasoning.]
    C --> C4[Cost: Low CapEx. High unpredictable OpEx.]
```

For detailed tabular comparison:

| Feature | Private AIOps (Local LLM / vmanomaly) | SaaS AIOps (Datadog / OpenAI) |
| :--- | :--- | :--- |
| **Data Privacy** | Absolute. Telemetry never leaves the cluster. | High risk. Cluster state and secrets may leak in prompts. |
| **Latency** | Dependent on local GPU/CPU hardware. Can be slow. | Low latency for API calls, fast inference. |
| **Model Capability** | Limited by local VRAM (typically 7B-70B parameter models). | State-of-the-art reasoning (GPT-4, Claude 3.5 Sonnet). |
| **Cost** | High CapEx (GPUs, power, cooling). Zero OpEx. | Low CapEx. High, unpredictable OpEx based on token usage. |

## Common Mistakes

| Mistake | Why It Happens | Fix |
| :--- | :--- | :--- |
| **Exposing the local LLM endpoint externally** | Local LLMs (Ollama/vLLM) lack built-in authentication layers. | Keep the service strictly inside the cluster (`ClusterIP`) and use network policies. |
| **Piping LLM output directly to `kubectl`** | LLMs hallucinate resource names and can confidently issue destructive commands. | Implement human-in-the-loop validation via Slack interactive approval buttons. |
| **Running 70B models on CPU nodes** | CPU inference is painfully slow, causing `504 Gateway Timeout` errors in Alertmanager webhooks. | Pin large models to GPU nodes using nodeSelectors or taints (e.g., `nvidia.com/gpu`). |
| **Using Z-scores on flat baseline metrics** | Near-zero standard deviation causes minor fluctuations to trigger massive Z-score alerts. | Add an absolute minimum rate threshold to the PromQL rule. |
| **Ignoring `maxReplicas` in predictive scaling** | Historical anomalies (like load testing) cause the model to scale out infinitely. | Cap `maxReplicas` strictly at 120% of expected peak traffic. |
| **Relying on Promtail for Loki v3.7+** | Promtail officially reached end-of-life on March 2, 2026. | Migrate log collection agents to Grafana Alloy. |
| **Running vmanomaly without a license** | VictoriaMetrics requires an Enterprise license for `vmanomaly` since v1.5.0. | Procure an enterprise license or fall back to native PromQL statistical rules. |
| **Using standard YAML parsers for multi-doc manifests** | Pipelines fail with `expected a single document` errors when reading full manifest streams containing `---`. | Use `yaml.safe_load_all()` in automation scripts or logically split deployments and services. |

---

## Hands-on Lab: AI-Enriched Alerting with Robusta and Local LLMs

In this lab, you will deploy a local Ollama instance running a small LLM, install Robusta, and configure it to intercept a failing Pod alert, utilizing the local AI to explain the failure.

### Prerequisites
* A Kubernetes cluster (v1.35+). `kind` or `minikube` is sufficient if you have at least 8GB of RAM available.
* `helm` and `kubectl` installed.
* `kube-prometheus-stack` installed in the `monitoring` namespace.

### Task 1: Deploying the Local Inference Endpoint (Ollama)

Deploy Ollama to serve the AI model locally. We will use `llama3.2:1b` for lab environments due to its low memory footprint. In production, use a larger model.

<details>
<summary>Solution</summary>

Create `ollama.yaml`:

```kubernetes
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

</details>

### Task 2: Configuring the AI Incident Responder (Robusta)

Generate a Robusta configuration. For this lab, we will configure Robusta to use the local Ollama instance and output to stdout for verification.

<details>
<summary>Solution</summary>

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

</details>

### Task 3: Configuring the Telemetry Router (Alertmanager)

Update your `kube-prometheus-stack` values to forward incoming alerts to Robusta for processing.

<details>
<summary>Solution</summary>

Update your `prometheus-values.yaml`:

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

</details>

### Task 4: Triggering the AI Triage

Deploy a failing pod to trigger a standard `KubePodCrashLooping` alert.

<details>
<summary>Solution</summary>

Create `crashing-pod.yaml`:

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

Apply the pod:

```bash
kubectl apply -f crashing-pod.yaml
```

Wait 5-10 minutes for Prometheus to fire the alert and Alertmanager to route it to Robusta.

</details>

### Task 5: Evaluating the Output

Tail the Robusta runner logs to observe the HTTP request to the Ollama API and the generated AI enrichment.

<details>
<summary>Solution</summary>

Read the logs:

```bash
kubectl logs -f deploy/robusta-runner -n monitoring
```

**Expected Output (Truncated):**

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

**Lab Success Checklist:**
- [ ] Ollama successfully pulled the `llama3.2:1b` model.
- [ ] Robusta runner deployed without CrashLoop errors.
- [ ] Alertmanager webhook successfully triggered Robusta.
- [ ] Robusta runner logged the AI Analysis text generated by the local LLM.

</details>

---

## Quiz

<details>
<summary>1. You are configuring Robusta to use a local LLM running in your cluster to ensure strict data privacy. The Robusta Helm chart requires a `chat_gpt_api_key`. What is the correct approach?</summary>
**Correct Answer: B.** The underlying Python OpenAI client library used by Robusta strictly requires an API key string to initialize its internal state. This requirement holds true even if the base URL is pointed to a local unauthenticated service like Ollama, which does not actually validate the key. Providing a dummy string (such as `dummy-key` or `ollama`) successfully satisfies the client library's initialization checks without compromising security. If you leave the field blank or omit it, the application will crash during startup before it even attempts to make an API call.
</details>

<details>
<summary>2. Your team is implementing Predictive Horizontal Pod Autoscaling (PHPA) for a critical payment gateway service. Following a recent load test that generated massive artificial traffic spikes, you are concerned the model might over-scale during normal operations. Which operational guardrail is most critical to prevent the predictive scaler from crashing the cluster?</summary>
**Correct Answer: C.** Predictive models can hallucinate or over-predict based on dirty historical data, such as a previous load test or a DDoS attack that the model misinterprets as a recurring seasonal trend. Implementing tight `maxReplicas` bounds is an essential operational guardrail in these scenarios. This hard limit prevents the predictive scaler from requesting an infinite number of pods, which would otherwise exhaust cluster resources and potentially crash critical control plane components. A common best practice is to cap this limit at approximately 120% of your known, legitimate peak capacity.
</details>

<details>
<summary>3. When implementing PromQL-based anomaly detection using Z-scores (`expr: node:cpu_usage:z_score > 3`), you notice the alert is flapping continuously on a low-traffic development cluster. What is the most likely architectural flaw?</summary>
**Correct Answer: D.** In low-traffic environments, a metric's baseline is often perfectly flat for extended periods, causing its calculated standard deviation to approach zero. Because the Z-score formula divides the deviation from the mean by the standard deviation, any minor fluctuation (like a single background cron job) gets divided by this near-zero value. This mathematical quirk results in an artificially massive Z-score, which instantly triggers the anomaly alert despite no real problem existing. To prevent this flapping, you must add an absolute minimum rate threshold to the PromQL rule, ensuring the alert only evaluates when baseline traffic is actually present.
</details>

<details>
<summary>4. Your platform team wants to reduce mean-time-to-recovery (MTTR) by allowing a local LLM to directly execute `kubectl` remediation commands, such as deleting failing pods or rolling back deployments via the Kubernetes API server. Why is this direct execution architecture considered a severe anti-pattern for production environments?</summary>
**Correct Answer: B.** LLMs fundamentally lack contextual situational awareness and absolute determinism when evaluating complex distributed systems. If granted direct write access to the Kubernetes API server, a hallucinated troubleshooting step could easily result in the deletion of healthy production resources or the cordoning of critical nodes. Because automated remediation can transform a localized failure into a cascading cluster-wide outage in seconds, enforcing human-in-the-loop verification is absolutely mandatory. While operators can technically configure tools like Robusta to execute these commands, doing so without strict RBAC limitations and explicit manual approval steps is a severe operational risk.
</details>

<details>
<summary>5. You are running a 7B parameter local LLM for private AIOps on bare metal without GPUs. You notice that Robusta often fails to attach AI summaries to Slack alerts, and the Robusta logs show `HTTP 504 Gateway Timeout`. What is the primary cause?</summary>
**Correct Answer: A.** Running LLM inference purely on standard CPUs is incredibly slow compared to utilizing dedicated GPU hardware. Generating a comprehensive RCA response for a complex alert might take 30 to 60 seconds of compute time on a CPU node. This extended latency easily exceeds the standard webhook timeout defaults—often configured to 10 or 15 seconds—within Alertmanager or the Robusta HTTP client. As a result, the client drops the connection with an `HTTP 504 Gateway Timeout` before the local model has finished generating and returning the text.
</details>

<details>
<summary>6. Your organization is upgrading its bare-metal observability stack and migrating to Grafana Loki v3.7. You need to deploy a log shipping agent to all your Kubernetes nodes to forward container logs to the new Loki instance. What is the correct architectural approach for this deployment?</summary>
**Correct Answer: B.** You must deploy Grafana Alloy as your log aggregation agent when moving to modern Loki architectures. The legacy Promtail agent officially reached end-of-life on March 2, 2026, meaning it no longer receives updates, bug fixes, or security patches. All of Promtail's core functionality was directly merged into Grafana Alloy, making it the definitive replacement for shipping logs to Loki v3.7 and beyond. Continuing to deploy Promtail introduces unnecessary technical debt and security risks into your observability pipeline.
</details>

<details>
<summary>7. Your organization wants to use Grafana's machine learning anomaly detection feature, Sift, to automatically investigate log anomalies on an air-gapped bare-metal cluster running open-source Grafana v12.x. What prevents this?</summary>
**Correct Answer: B.** Grafana's advanced machine learning capabilities, including the Sift automated anomaly investigation tool and timeseries forecasting, are proprietary features. They are exclusively licensed for use within Grafana Cloud and Grafana Enterprise deployments. These features are fundamentally absent from the open-source Grafana v12.x distribution that you would run on an air-gapped bare-metal cluster. Organizations requiring private, on-premises ML anomaly detection must instead integrate alternative open-source tools like OpenSearch or statistical PromQL rules.
</details>

<details>
<summary>8. You are configuring an MLOps pipeline to feed model training data from your observability stack. You decide to orchestrate the pipeline with Argo Workflows and track model experiments. Which tool should you use for experiment tracking according to the LF AI & Data foundation?</summary>
**Correct Answer: C.** MLflow is the industry standard tool specifically designed for machine learning experiment tracking, model registry, and lifecycle management. It is officially governed by the Linux Foundation AI & Data (LF AI & Data) rather than the CNCF, reflecting its specialized focus on data science workflows rather than general cloud-native infrastructure. By integrating MLflow with Argo Workflows, teams can effectively decouple the orchestration of training pipelines from the nuanced tracking of model hyperparameters and evaluation metrics. This creates a robust, standardized stack for managing predictive AIOps models.
</details>

## Next Module

Ready to take your bare-metal clusters to the next level? In the next module, [Module 9.6: Edge Inference and Hardware Acceleration](/on-premises/ai-ml-infrastructure/module-9.6-edge-inference), we will explore how to configure SR-IOV, MIG (Multi-Instance GPU), and optimized scheduling to squeeze maximum inference performance out of your local hardware infrastructure.

## Key Links

* [Robusta Official Documentation: Custom LLMs](https://docs.robusta.dev/master/configuration/ai-analysis/custom-llms.html)
* [VictoriaMetrics Anomaly Detection (vmanomaly) Guide](https://docs.victoriametrics.com/vmanomaly/)
* [KEDA Predictive Scaling Discussion (GitHub)](https://github.com/kedacore/keda/issues/2301)
* [Ollama Kubernetes Deployment Examples](https://github.com/ollama/ollama/tree/main/docs)
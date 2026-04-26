---
qa_pending: true
title: "Module 3.8: AI/ML on Cloud Native Infrastructure"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.8-ai-ml-cloud-native
sidebar:
  order: 9
---

> **Complexity**: `[MEDIUM]` - Cloud native architecture and workload design
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles), Module 3.3 (Cloud Native Patterns), basic familiarity with Pods, Deployments, Jobs, and scheduling

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Apply** Kubernetes resource and scheduling concepts to choose appropriate runtime patterns for AI/ML training, fine-tuning, batch inference, and real-time inference workloads.
2. **Compare** GPU-enabled Kubernetes components such as device plugins, node labels, taints, autoscaling, and specialized schedulers in realistic platform design scenarios.
3. **Design** a basic cloud native serving architecture for a model endpoint that balances privacy, latency, scaling behavior, and operational responsibility.
4. **Debug** common AI/ML scheduling failures by reading Pod status, scheduler events, node capacity, and accelerator resource requests.
5. **Evaluate** when ecosystem tools such as Kubeflow, KServe, Ray, vLLM, GPU Operator, and Volcano fit the problem instead of treating every model workload as an ordinary web service.

---

## Why This Module Matters

A retail company launched a recommendation feature that worked perfectly during a small pilot, then failed during the holiday traffic surge. The application Pods scaled, the frontend remained healthy, and the database had spare capacity, yet the recommendation endpoint became slow and then unavailable. The platform team eventually found the real problem: the model server needed GPUs, the cluster autoscaler was only adding CPU nodes, and half the inference replicas were stuck Pending while users waited for product suggestions that never arrived.

That failure is common because AI/ML workloads look familiar from a distance but behave differently under pressure. They still run in containers, they still need networking, and they still benefit from Kubernetes controllers, but their most expensive resources are accelerators and memory rather than ordinary CPU. A learner who treats model serving like a normal stateless API will miss the scheduling constraints, startup time, GPU capacity, model size, and latency behavior that determine whether the system works.

KCNA does not expect you to become a machine learning engineer or install every tool in the ecosystem. It does expect you to reason about why Kubernetes is used for AI/ML, how accelerators become schedulable resources, why training and inference need different workload patterns, and how cloud native practices apply to systems that may cost more per hour than the rest of the cluster combined. This module builds that reasoning step by step, starting with the platform problem and ending with a hands-on scheduler investigation.

---

## 1. Kubernetes Is Useful for AI/ML Because It Coordinates Scarce Infrastructure

Kubernetes did not become popular for AI/ML because it understands neural networks. It became useful because AI/ML platforms need repeatable scheduling, isolation, rollout control, observability, secret management, storage integration, and APIs that many teams can share. Those are cloud native platform concerns, and Kubernetes already provides a control plane for them.

The important shift is that AI/ML workloads often care about resources Kubernetes did not originally manage. A web API may need a small amount of CPU and memory on any general-purpose node. A model training job may need multiple GPUs, large local scratch space, high-throughput storage, and workers that start together. A model server may need one GPU, enough VRAM to load the model, and autoscaling policies tied to request latency or queue depth rather than CPU alone.

```text
┌─────────────────────────────────────────────────────────────┐
│              WHY K8S FOR AI/ML?                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Kubernetes provides what AI/ML workloads need:             │
│                                                             │
│  1. GPU SCHEDULING                                          │
│     ─────────────────────────────────────────────────────   │
│     K8s schedules GPUs like CPU/memory after a device       │
│     plugin advertises accelerator capacity to each kubelet  │
│                                                             │
│  2. DEVICE PLUGINS                                          │
│     ─────────────────────────────────────────────────────   │
│     Extend K8s to manage specialized hardware:              │
│     • NVIDIA GPUs exposed as nvidia.com/gpu                 │
│     • AMD GPUs, Intel accelerators, Google TPUs             │
│     • Any accelerator integrated through the plugin model   │
│                                                             │
│  3. BATCH PROCESSING                                        │
│     ─────────────────────────────────────────────────────   │
│     Jobs and training operators handle runs that finish,    │
│     unlike services that are expected to run continuously   │
│                                                             │
│  4. AUTOSCALING                                             │
│     ─────────────────────────────────────────────────────   │
│     Scale inference endpoints with traffic, queue length,   │
│     latency, or custom metrics when capacity exists         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

A useful mental model is to separate Kubernetes into two layers. The core platform knows how to run Pods, place them on nodes, observe their status, and reconcile desired state. The AI/ML extensions teach the platform about specialized hardware, distributed training, model serving, and experiment workflows. When a Pod requests a GPU, Kubernetes is not running a machine learning algorithm; it is matching a resource request against node capacity published by a device plugin.

> **Pause and predict:** A cluster has three CPU-only nodes and one GPU node. A Pod requests `nvidia.com/gpu: 1` but does not include any node selector or affinity. If the NVIDIA device plugin is installed only on the GPU node, where can the scheduler place the Pod, and what status will you expect if that GPU is already allocated?

The answer is that the Pod can only run where the requested extended resource is available. If the GPU is already allocated, the Pod remains Pending because GPU resources are non-compressible. CPU can sometimes be oversubscribed and throttled, but a Pod that requests an integer GPU either receives the device or it does not start.

---

## 2. How GPUs Become Schedulable Kubernetes Resources

Kubernetes does not automatically discover every accelerator in the data center. The kubelet receives accelerator capacity from a device plugin, and the plugin usually runs as a DaemonSet on nodes that have the hardware. The device plugin reports resources such as `nvidia.com/gpu`, and the node status then includes that resource as allocatable capacity.

A Pod requests GPUs in the `resources.limits` field. Extended resources are requested as whole units in limits, and for many common GPU configurations the request and limit are effectively the same scheduling signal. The scheduler then checks node allocatable capacity and existing allocations before binding the Pod to a node.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-smoke-test
spec:
  restartPolicy: Never
  containers:
    - name: cuda-container
      image: nvidia/cuda:12.4.1-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
```

This manifest is intentionally small because the important lesson is the resource request, not the application. If the cluster has a GPU node, the device plugin is healthy, and the GPU is free, the Pod can run and execute `nvidia-smi`. If any of those assumptions are false, Kubernetes will not invent a GPU; the Pod stays Pending and the scheduler event explains which resource is missing.

| Concept | What It Means | Why It Matters in Practice |
|---------|---------------|----------------------------|
| **Device Plugin** | A node-level component, commonly deployed as a DaemonSet, that advertises accelerator devices to the kubelet. | Without it, Kubernetes usually sees ordinary CPU and memory but no GPU resource to schedule. |
| **`nvidia.com/gpu`** | The common extended resource name used by NVIDIA GPU plugins. | Pods request this name, so a typo or missing plugin produces Pending Pods rather than slower execution. |
| **GPU time-slicing** | A configuration that allows multiple Pods to share one physical GPU over time. | It can improve utilization for light workloads, but it weakens isolation and may hurt latency predictability. |
| **MIG** | Multi-Instance GPU partitioning on supported NVIDIA hardware, exposing hardware-isolated GPU slices. | It gives stronger isolation than time-slicing for suitable workloads, but it requires compatible hardware and planning. |
| **Whole GPU allocation** | One Pod receives exclusive access to a full physical GPU. | It is the simplest model and often best for heavy training or latency-sensitive inference. |

Node labels and taints often appear alongside GPU resources. Labels help target workloads to specific node groups, such as nodes with a particular GPU model. Taints help keep ordinary workloads away from expensive accelerator nodes unless those workloads explicitly tolerate the taint. The GPU resource request itself is still essential because a label alone says "run on this kind of node" while `nvidia.com/gpu: 1` says "allocate one device to this container."

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommender-inference
spec:
  replicas: 2
  selector:
    matchLabels:
      app: recommender-inference
  template:
    metadata:
      labels:
        app: recommender-inference
    spec:
      nodeSelector:
        accelerator: nvidia
      tolerations:
        - key: "accelerator"
          operator: "Equal"
          value: "gpu"
          effect: "NoSchedule"
      containers:
        - name: model-server
          image: ghcr.io/example/recommender:1.0.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "2"
              memory: 8Gi
            limits:
              nvidia.com/gpu: 1
              memory: 16Gi
```

Notice the separation of concerns in this Deployment. The `nodeSelector` and toleration steer the Pod toward the GPU node group, while the GPU limit reserves the accelerator. CPU and memory requests tell the scheduler how much ordinary capacity the Pod needs, and the memory limit prevents one model server from exhausting the node. This is the kind of combined reasoning KCNA expects: not just naming a feature, but applying several platform mechanisms together.

---

## 3. Training, Fine-Tuning, Batch Inference, and Real-Time Inference Are Different Workloads

The biggest beginner mistake is calling every model-related container "AI" and then deploying it the same way. Kubernetes architecture starts with workload shape. Does the process finish or run forever? Does it need all workers at once? Does it serve users synchronously? Does it need one GPU, many GPUs, or no GPU after preprocessing?

```text
┌─────────────────────────────────────────────────────────────┐
│              AI/ML WORKLOAD TYPES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRAINING                                                   │
│  ─────────────────────────────────────────────────────────  │
│  • Runs for hours, days, or sometimes longer                │
│  • May need many GPUs distributed across nodes              │
│  • Batch workload that should complete successfully         │
│  • Distributed runs may need gang scheduling                │
│                                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │ GPU worker │ │ GPU worker │ │ GPU worker │ │ GPU lead │ │
│  │   node A   │ │   node A   │ │   node B   │ │  node B  │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
│                                                             │
│  INFERENCE SERVING                                          │
│  ─────────────────────────────────────────────────────────  │
│  • Runs continuously and serves predictions                 │
│  • Latency-sensitive because users or applications wait     │
│  • Often scales by adding replicas behind a Service         │
│  • May use one GPU per replica or partitioned GPU capacity  │
│                                                             │
│  Request ──▶ [Model Server] ──▶ Prediction                  │
│             [Model Server]      Autoscaled replicas         │
│             [Model Server]                                 │
│                                                             │
│  FINE-TUNING                                                │
│  ─────────────────────────────────────────────────────────  │
│  • Starts from a pretrained model and adapts it to data     │
│  • Usually shorter than full training                       │
│  • Still sensitive to checkpointing, storage, and GPUs      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Training is usually a batch problem. A data science team starts a run, waits for it to finish, and expects artifacts such as model weights, metrics, or checkpoints. Kubernetes Jobs fit simple training because they track completion and do not restart successful Pods forever. Larger teams may use training operators such as PyTorchJob or TFJob because those operators understand worker roles, distributed launch behavior, and training-specific lifecycle events.

Real-time inference is usually a service problem. A model endpoint accepts requests, returns predictions, and must stay available while traffic changes. Deployments, Services, autoscalers, and rollout strategies fit this shape because replicas can be replaced gradually and traffic can be routed away from unhealthy Pods. Inference also has special constraints: model startup may take minutes, GPU memory may be the limiting factor, and CPU utilization may not reflect the actual bottleneck.

Batch inference sits between those two patterns. It uses a trained model to score a large offline dataset, such as millions of images or transactions, and then writes results to storage. It does not need a public endpoint because nobody is waiting on each individual request. A Job or workflow engine is usually a better fit than a Deployment, because completion and retry behavior matter more than steady request latency.

| Aspect | Training | Fine-Tuning | Batch Inference | Real-Time Inference |
|--------|----------|-------------|-----------------|---------------------|
| **Duration** | Long-running but finite, often hours or days. | Finite and usually shorter than full training. | Finite, tied to a dataset or queue. | Continuous, serving as long as the product needs predictions. |
| **Kubernetes pattern** | Job, training operator, or batch scheduler. | Job or specialized operator. | Job, workflow, or queue-driven workers. | Deployment, Service, autoscaler, and rollout controls. |
| **Scaling concern** | Throughput, parallel workers, and checkpoint restart. | GPU cost, storage access, and repeatability. | Dataset throughput and failure recovery. | Latency, concurrency, readiness, and traffic spikes. |
| **Failure handling** | Resume from checkpoints or restart a failed run. | Save intermediate adapters or checkpoints. | Retry failed chunks without duplicating output. | Route around unhealthy replicas and roll out safely. |
| **Scheduling risk** | Partial worker placement can waste GPUs. | A few GPUs may block other teams if priorities are unclear. | Large queues can starve interactive workloads. | Replicas may start too slowly for sudden traffic. |

> **Stop and decide:** Your team has a script that reads yesterday's support tickets, classifies each ticket with an existing model, writes labels to a database, and exits. Would you run it as a Deployment, a Job, or a DaemonSet? Write down the Kubernetes behavior you need before choosing the resource.

A good answer chooses a Job or workflow task because the process has a clear end condition. A Deployment would keep restarting the classifier after it finishes, and a DaemonSet would run one copy on every matching node whether or not the data pipeline needs that. The decision comes from workload shape, not from the fact that a model is involved.

---

## 4. Distributed Training Needs Scheduling Guarantees That Default Kubernetes May Not Provide

Default Kubernetes schedules Pods one at a time. That is enough for many independent services, but distributed training often needs a group of workers to start together. If a training job needs sixteen workers and only eight are scheduled, those eight may hold expensive GPUs while waiting for peers that cannot start. The result is poor utilization and sometimes a deadlock-like condition from the user's point of view.

Gang scheduling solves that problem by treating a set of Pods as a unit. The scheduler admits the group only when enough resources exist for the whole gang, or it waits without binding partial workers. Tools such as Volcano add batch scheduling capabilities including gang scheduling, queues, and fair sharing. KCNA does not require deep configuration knowledge, but it does expect you to recognize why the default scheduler's one-Pod-at-a-time behavior can be a poor fit for distributed AI/ML jobs.

```text
┌─────────────────────────────────────────────────────────────┐
│          DEFAULT SCHEDULING VS. GANG SCHEDULING             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Default scheduler:                                         │
│                                                             │
│  worker-1 ──▶ scheduled ──▶ holds GPU                       │
│  worker-2 ──▶ scheduled ──▶ holds GPU                       │
│  worker-3 ──▶ Pending   ──▶ no GPU left                     │
│  worker-4 ──▶ Pending   ──▶ no GPU left                     │
│                                                             │
│  Result: partial job may hold GPUs while doing no work       │
│                                                             │
│  Gang scheduler:                                            │
│                                                             │
│  workers 1-4 ──▶ enough GPUs? ──▶ yes: schedule all          │
│                         │                                   │
│                         └────▶ no: schedule none yet         │
│                                                             │
│  Result: fewer stranded GPUs and clearer queue behavior      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Distributed training also makes storage and networking more important. Workers may read large datasets, exchange gradients, and write checkpoints. A platform design that focuses only on GPU count can still fail if the storage path is slow or if workers cannot communicate reliably. Senior-level Kubernetes reasoning means asking which resource becomes the bottleneck next, not stopping after the first successful Pod start.

Priorities and quotas matter because GPU clusters are shared. A research notebook, a production inference endpoint, and a training run should not all compete without policy. ResourceQuota, PriorityClass, queueing systems, and separate node pools are ways to express business intent. The platform should answer questions such as "Can an experiment preempt production inference?" and "How many GPUs can one namespace consume?" before a traffic spike or training deadline forces the issue.

---

## 5. Model Serving Adds Latency, Rollout, and Privacy Trade-Offs

Serving a model is not just running a Python process in a container. The model has to be loaded, kept warm, monitored, scaled, and updated without breaking callers. A small model may behave like an ordinary web API, but a large language model can take significant time to start and may consume most of a GPU's memory before receiving a single request.

Organizations self-host inference for several reasons. Privacy is a common driver because prompts, documents, images, or customer records may be too sensitive to send to an external API. Latency can improve when the model server is close to the application and data. Cost can improve at sustained high volume if the team can keep GPUs highly utilized. Control improves because the organization chooses model versions, quantization settings, rollout timing, and observability.

```text
┌─────────────────────────────────────────────────────────────┐
│              WHY SELF-HOST LLMs?                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIVACY      Sensitive data stays in controlled systems    │
│  COST         Sustained high volume may beat per-token APIs │
│  LATENCY      Co-locate model servers with applications     │
│  COMPLIANCE   Meet data residency and audit requirements    │
│  CONTROL      Choose model, version, runtime, and rollout   │
│                                                             │
│  Trade-off: The platform team owns GPUs, drivers, scaling,  │
│  model rollout, capacity planning, and incident response.   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The trade-off is operational responsibility. A public model API hides GPU drivers, capacity planning, batching, runtime tuning, and model-server upgrades. A self-hosted platform exposes all of those concerns to the organization. Kubernetes helps coordinate the system, but it does not remove the need to understand accelerator scarcity, model memory, autoscaling metrics, or release safety.

For inference, readiness probes are especially important. A container can be running while the model is still loading, and sending traffic too early creates failed requests. A readiness probe should report ready only after the server can actually answer predictions. For large models, startup probes may also be necessary so Kubernetes does not kill a slow-loading container before it has a fair chance to become healthy.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ticket-classifier
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ticket-classifier
  template:
    metadata:
      labels:
        app: ticket-classifier
    spec:
      containers:
        - name: classifier
          image: ghcr.io/example/ticket-classifier:2.1.0
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 5
            failureThreshold: 6
          startupProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 10
            failureThreshold: 30
          resources:
            requests:
              cpu: "1"
              memory: 4Gi
            limits:
              memory: 8Gi
              nvidia.com/gpu: 1
```

This Deployment teaches two subtle points. First, readiness is about serving capability, not container existence. Second, resource limits and probes must match the model's real behavior. If the model takes four minutes to load but the startup probe gives it only one minute, Kubernetes will create a crash loop even though the image and code are correct.

---

## 6. Ecosystem Tools Solve Different Parts of the AI/ML Lifecycle

The AI/ML on Kubernetes ecosystem is large because the lifecycle is larger than "run a container." Teams need notebooks for exploration, pipelines for repeatable training, registries for model versions, serving systems for inference, schedulers for batch jobs, and monitoring for performance drift. No single tool should be selected just because it appears in an AI/ML architecture diagram.

Kubeflow is often discussed as an end-to-end ML platform on Kubernetes. It can include notebooks, pipelines, training operators, and serving integrations. It is useful when the organization wants a platform for data scientists and ML engineers rather than isolated YAML files. It also increases platform complexity, so a small team serving one model may not need the full stack.

KServe focuses on model serving. It provides abstractions for inference services, canary rollout patterns, autoscaling integrations, and model-server conventions. vLLM is a high-throughput inference engine often used for large language models, where batching and memory management strongly affect cost and latency. Ray is a distributed computing framework used for training, data processing, and serving patterns that need flexible distributed execution.

| Tool | What It Does | Best-Fit Scenario |
|------|-------------|-------------------|
| **Kubeflow** | Provides a Kubernetes-native ML platform with notebooks, pipelines, training components, and serving integrations. | A platform team wants a shared ML workflow environment for multiple teams. |
| **KServe** | Standardizes model inference serving on Kubernetes with rollout and scaling patterns. | A team needs production model endpoints rather than only training jobs. |
| **Ray** | Runs distributed Python workloads for training, data processing, and serving. | A workload needs flexible distributed execution beyond a single Pod. |
| **vLLM** | Serves large language models efficiently using optimized batching and memory handling. | An organization self-hosts LLM inference and needs high throughput per GPU. |
| **NVIDIA GPU Operator** | Automates GPU driver, container runtime, monitoring, and device plugin setup. | A platform team manages NVIDIA GPU node pools and wants repeatable operations. |
| **Volcano** | Adds batch scheduling features such as gang scheduling, queues, and fair sharing. | Distributed training jobs need all workers scheduled together or predictable queue behavior. |

```text
┌─────────────────────────────────────────────────────────────┐
│              ML PIPELINE ON KUBERNETES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Data Prep ──▶ Training ──▶ Evaluation ──▶ Serving ──▶ Monitor│
│     │             │              │             │          │ │
│  [Spark or     [Kubeflow      [tests,       [KServe,   [Prom │
│   Ray jobs]     Training]      metrics]      vLLM]      + logs│
│                                                             │
│  Kubernetes provides the API, Pods, Services, controllers,  │
│  scheduling hooks, secrets, storage integration, and events. │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Architecture check:** Your organization has one fraud model that is retrained weekly and served behind an internal API. The data science team does not need notebooks in the cluster. Which is more likely to be the first useful platform investment: a full Kubeflow installation, a small Job plus Deployment pattern, or a serving-focused tool such as KServe? Justify the operational cost of your choice.

A practical answer might start with a Job for retraining and a Deployment or KServe-based inference endpoint, then add Kubeflow only when repeated workflows, notebooks, or multi-team standardization justify the overhead. Tool selection should follow workflow pain. Installing a large platform before the team has a lifecycle problem can create more work than it removes.

---

## 7. Worked Example: Debug a Pending GPU Inference Deployment

A worked example shows the reasoning process before you attempt a similar hands-on task. In this scenario, a team deploys a model server for real-time inference. The Deployment is correct enough to create Pods, but no replica becomes Running. Your goal is to move from symptom to cause using Kubernetes evidence rather than guessing.

The team applies this Deployment to a development cluster. They expect one replica to start because they believe the cluster has a GPU node. The platform uses the common `k` alias for `kubectl`; after defining the alias once with `alias k=kubectl`, the commands below use `k` for brevity.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-ranker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: image-ranker
  template:
    metadata:
      labels:
        app: image-ranker
    spec:
      containers:
        - name: ranker
          image: ghcr.io/example/image-ranker:1.0.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "1"
              memory: 4Gi
            limits:
              memory: 8Gi
              nvidia.com/gpu: 1
```

### Step 1: Start with the controller, then inspect the Pod

A beginner often starts by changing YAML immediately, but a stronger habit is to inspect what Kubernetes created. The Deployment owns a ReplicaSet, and the ReplicaSet owns Pods. If the Deployment has unavailable replicas, the next useful evidence is usually the Pod status and events.

```bash
k get deployment image-ranker
k get pods -l app=image-ranker
```

Example output:

```text
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
image-ranker    0/1     1            0           2m

NAME                             READY   STATUS    RESTARTS   AGE
image-ranker-6c9d7f8d9b-hp2lm    0/1     Pending   0          2m
```

Pending means the container has not started. That is different from CrashLoopBackOff, where the Pod was scheduled and a container started but failed. For scheduling problems, the `describe pod` output is the main source of truth because it includes scheduler events.

```bash
k describe pod -l app=image-ranker
```

Example event:

```text
Events:
  Type     Reason             Age   From               Message
  ----     ------             ----  ----               -------
  Warning  FailedScheduling   2m    default-scheduler  0/4 nodes are available: 4 Insufficient nvidia.com/gpu.
```

### Step 2: Interpret the event instead of memorizing the answer

The scheduler says it cannot find enough `nvidia.com/gpu` capacity. That does not prove the cluster has no physical GPU. It proves the Kubernetes scheduler does not currently see allocatable free capacity for that resource. The cause could be missing device plugin, no GPU nodes, a consumed GPU, a node taint without toleration, or node affinity that excludes the right node.

The next command checks whether any node advertises GPU capacity. If no node shows `nvidia.com/gpu` under allocatable resources, the problem is lower than the workload manifest. The platform team needs to confirm GPU nodes, drivers, and the device plugin.

```bash
k describe nodes | grep -A5 -E "Name:|Allocatable:"
```

A healthy GPU node would include a line like this somewhere under `Allocatable`:

```text
nvidia.com/gpu:  1
```

If no such line appears, deploying more model replicas will not help. The scheduler cannot allocate a resource that the nodes do not advertise. The likely fix is to install or repair the GPU device plugin, or use a managed GPU node pool that includes the required integration.

### Step 3: Check whether the workload is missing placement rules

Suppose a node does advertise `nvidia.com/gpu`, but the Pod is still Pending. The next useful question is whether the node has taints that repel ordinary Pods. GPU nodes are commonly tainted because they are expensive, and the platform team wants only GPU-aware workloads to land there.

```bash
k describe node gpu-node-1 | grep -A4 Taints
```

Example output:

```text
Taints: accelerator=gpu:NoSchedule
```

The Deployment above requests a GPU but does not tolerate the taint. The fix is to add a matching toleration, and many teams also add a node selector or affinity rule to express the intended node pool.

```yaml
spec:
  template:
    spec:
      nodeSelector:
        accelerator: nvidia
      tolerations:
        - key: "accelerator"
          operator: "Equal"
          value: "gpu"
          effect: "NoSchedule"
```

### Step 4: Verify the corrected scheduling path

After updating the Deployment, verify the Pod again instead of assuming the fix worked. A successful result should move from Pending to ContainerCreating and then Running, assuming image pulls and model startup succeed. If it moves to CrashLoopBackOff, that is progress in the debugging sequence because the problem changed from scheduling to runtime.

```bash
k rollout status deployment/image-ranker
k get pods -l app=image-ranker -o wide
k describe pod -l app=image-ranker
```

The key lesson is the order of investigation. Start with the observed status, read scheduler events, confirm node allocatable resources, then inspect placement constraints such as taints, tolerations, selectors, and affinity. That same pattern works for the hands-on exercise later in the module, even when your local cluster has no real GPU hardware.

---

## Did You Know?

1. **GPU waste is a platform finance problem, not only a technical problem.** A single accelerator node can cost enough that low utilization becomes visible in cloud bills quickly, so scheduling policies, sharing strategies, and right-sized model serving directly affect business outcomes.

2. **Gang scheduling is not part of the default scheduler behavior most learners use first.** Kubernetes normally binds Pods independently, so distributed training teams often add schedulers such as Volcano when partial placement would strand GPUs and block useful work.

3. **A model server can be Running but still not ready to serve predictions.** Large models may need time to download weights, allocate GPU memory, compile kernels, or warm caches, which is why readiness and startup probes matter for inference reliability.

4. **Kubernetes won AI/ML infrastructure work through extensibility rather than original design.** Device plugins, custom controllers, operators, and specialized schedulers let the platform adapt to accelerators and ML workflows without requiring every feature in the core API.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Thinking Kubernetes automatically detects GPUs after installation. | Pods request `nvidia.com/gpu`, but nodes advertise no such resource, so scheduling fails. | Install and verify the vendor device plugin or GPU operator before deploying GPU workloads. |
| Using a Deployment for a training script that should finish. | A successful training container exits, then the Deployment starts it again because it wants continuous replicas. | Use a Job, workflow engine, or training operator for finite training and batch inference tasks. |
| Relying only on node labels for GPU workloads. | A Pod may target a GPU node without actually reserving a GPU, or request a GPU without tolerating the node taint. | Combine resource limits, selectors or affinity, and tolerations according to the node pool policy. |
| Scaling inference only on CPU utilization. | GPU memory, request queue depth, or latency may saturate while CPU looks moderate. | Choose autoscaling signals that match the model server's real bottleneck and user-facing objective. |
| Ignoring model load time during rollouts. | Kubernetes may send traffic before the model is ready, causing errors during deployments or scale-ups. | Use startup and readiness probes that reflect actual model-serving readiness. |
| Treating GPU time-slicing as equivalent to hardware isolation. | Shared GPUs can create noisy-neighbor effects and unpredictable latency for sensitive workloads. | Use whole GPUs or MIG where isolation matters, and reserve time-slicing for suitable light workloads. |
| Installing a full ML platform before defining the workflow problem. | The team inherits operational complexity before it has repeatable notebooks, pipelines, or multi-team needs. | Start with the smallest pattern that solves the workload, then adopt Kubeflow or KServe when their abstractions pay off. |
| Forgetting that cluster autoscaling must understand GPU node groups. | Pending GPU Pods may not cause useful scale-out if the autoscaler can only add CPU nodes. | Configure autoscaling for accelerator node pools and verify that Pending events trigger the expected capacity path. |

---

## Quiz

**1. Your team deploys a real-time recommendation model as a Deployment with three replicas. During a traffic spike, the HorizontalPodAutoscaler creates more replicas, but the new Pods stay Pending with `Insufficient nvidia.com/gpu`. The web tier continues scaling normally. What should you investigate first, and why?**

A) Whether the model image contains the newest Python dependencies, because Pending usually means the container crashed before startup.  
B) Whether GPU node groups and the device plugin expose enough allocatable accelerator capacity, because the scheduler cannot place Pods without free extended resources.  
C) Whether the Service selector points to the right Pods, because a wrong selector prevents the scheduler from binding replicas.  
D) Whether the Deployment strategy is set to Recreate, because rolling updates are unsupported for GPU workloads.

<details>
<summary>Answer</summary>

**B) Whether GPU node groups and the device plugin expose enough allocatable accelerator capacity.** Pending means the Pod has not been scheduled, so image dependencies and runtime crashes are not the first issue. The event names the missing extended resource, which points to GPU capacity, device plugin health, existing allocations, or autoscaler configuration for GPU nodes.
</details>

**2. A data science team has a script that trains a model for twelve hours, writes checkpoints every hour, uploads final weights, and then exits successfully. They ask you to run it as a Deployment so Kubernetes will "keep it reliable." What should you recommend?**

A) Use a Job or training operator, because the process has a clear completion condition and should not be restarted after success.  
B) Use a DaemonSet, because every node should participate in training automatically.  
C) Use a StatefulSet, because every machine learning workload needs a stable network identity.  
D) Use a Deployment with one replica, because Deployments are the only Kubernetes resource that supports restarts.

<details>
<summary>Answer</summary>

**A) Use a Job or training operator.** The workload is finite: it starts, performs training, writes output, and exits. A Deployment tries to maintain continuously running replicas, so it would restart the training after successful completion and could waste expensive resources or duplicate output.
</details>

**3. A distributed training run needs eight GPU workers to start together. Four workers are Running and holding GPUs, while four are Pending because the cluster has no remaining capacity. The Running workers wait indefinitely for peers. Which platform change best addresses the architecture problem?**

A) Add a readiness probe to the worker Pods so Kubernetes sends traffic only when all workers are ready.  
B) Add gang scheduling through a batch scheduler so either the full worker group is admitted or none is scheduled yet.  
C) Convert the training job into a Service so the Pending workers can be load balanced.  
D) Remove GPU limits so the scheduler can place all workers on CPU nodes.

<details>
<summary>Answer</summary>

**B) Add gang scheduling through a batch scheduler.** The failure is partial placement of a distributed workload, not HTTP readiness or service discovery. Gang scheduling prevents a subset of workers from consuming GPUs when the full set cannot run, which improves utilization and makes queue behavior clearer.
</details>

**4. A compliance team requires that customer documents used in prompts must not leave company-controlled infrastructure. Product leadership also requires low latency because the model response is part of an interactive workflow. Which design best fits those constraints?**

A) Self-host the inference service close to the application on Kubernetes, while accepting responsibility for GPU capacity, model rollout, and monitoring.  
B) Run training as a CronJob once per day, because scheduled training automatically satisfies prompt privacy.  
C) Send requests to any public model API and rely on Kubernetes NetworkPolicy to hide the data from the provider.  
D) Use a DaemonSet on every node so each application Pod has a local model server.

<details>
<summary>Answer</summary>

**A) Self-host the inference service close to the application.** Keeping inference in controlled infrastructure helps address data handling constraints, and co-location can reduce network latency. The trade-off is operational: the team now owns accelerator nodes, model-server readiness, scaling, rollout safety, and incident response.
</details>

**5. A platform team has one weekly fraud-model retraining job and one internal fraud inference endpoint. They are considering installing a large end-to-end ML platform immediately. What is the most defensible first step?**

A) Install Kubeflow before defining workflows, because every Kubernetes ML system requires notebooks and pipelines.  
B) Start with a Job for retraining and a Deployment or serving-focused abstraction for inference, then add larger platform components when repeated workflow pain appears.  
C) Avoid Kubernetes completely because model workloads cannot be scheduled with ordinary Pods.  
D) Run both retraining and serving in the same long-running Deployment to reduce YAML.

<details>
<summary>Answer</summary>

**B) Start with the smallest pattern that solves the workload.** A weekly finite retraining task maps naturally to a Job or workflow, and the internal endpoint maps to serving infrastructure. Kubeflow can be valuable later, but adopting it before the team needs notebooks, pipelines, or multi-team governance may add avoidable operational complexity.
</details>

**6. A model-serving Pod is Running, but users receive errors for the first few minutes after every rollout. Logs show the container is downloading weights and warming the model during that time. What should you change in the Kubernetes configuration?**

A) Add or adjust startup and readiness probes so traffic is withheld until the model server can actually answer requests.  
B) Remove memory limits because readiness problems are always caused by resource limits.  
C) Convert the Deployment to a Job so the model can finish loading and exit.  
D) Add more replicas without changing probes, because Services only route to warm model servers automatically.

<details>
<summary>Answer</summary>

**A) Add or adjust startup and readiness probes.** Running only means the container process exists; it does not prove the model is loaded and ready. Readiness should reflect prediction capability, and startup probes can give slow-loading models enough time before liveness checks or restarts interfere.
</details>

**7. A development cluster has one GPU shared by several lightweight notebook users. Whole-GPU allocation leaves most of the accelerator idle, but production workloads are not allowed on this cluster. Which approach could improve utilization while preserving a reasonable understanding of the trade-off?**

A) Configure GPU time-slicing for suitable development workloads and document that isolation and latency predictability are weaker than whole-GPU allocation.  
B) Remove all GPU resource requests so every notebook can be scheduled on the same node.  
C) Use a DaemonSet to start one notebook on every node, regardless of who needs the GPU.  
D) Replace the device plugin with CPU requests because Kubernetes can emulate GPUs through CPU throttling.

<details>
<summary>Answer</summary>

**A) Configure GPU time-slicing for suitable development workloads.** Time-slicing can improve utilization when workloads are light and strict isolation is not required. It is not the same as hardware isolation, so it should be used deliberately and separated from production latency-sensitive workloads.
</details>

**8. An inference Deployment requests `nvidia.com/gpu: 1` and the cluster has a GPU node with allocatable capacity. The Pod is still Pending. `kubectl describe node` shows the node has the taint `accelerator=gpu:NoSchedule`. What is the most likely fix?**

A) Add a matching toleration to the Pod, and optionally add node selection or affinity to make the intended GPU node pool explicit.  
B) Remove the GPU resource limit because taints only apply to Pods that request extended resources.  
C) Change the container port because the scheduler validates ports before taints.  
D) Convert the Pod to a ConfigMap so it can tolerate node taints.

<details>
<summary>Answer</summary>

**A) Add a matching toleration and make placement explicit.** A taint repels Pods unless they have a matching toleration. The GPU request reserves the device, while the toleration permits scheduling onto the tainted node; selectors or affinity can also express the intended hardware pool.
</details>

---

## Hands-On Exercise: Simulate and Debug a GPU Scheduling Request

In this exercise, you will create a Pod that requests a GPU and then inspect the scheduling result. You do not need a physical GPU for the exercise. In a typical local or CPU-only cluster, the expected result is a Pending Pod with a scheduler event showing that no node has enough `nvidia.com/gpu` capacity.

Before starting, define the common Kubernetes alias once if you want to use the shorter commands shown below. The full command `kubectl` works the same way, and the alias is only for convenience after the first explanation.

```bash
alias k=kubectl
```

1. Create a file named `gpu-pod.yaml` with a Pod that requests one NVIDIA GPU. The image and command are real, but the scheduler must find a node advertising `nvidia.com/gpu` before the container can run.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test-pod
spec:
  restartPolicy: Never
  containers:
    - name: cuda-container
      image: nvidia/cuda:12.4.1-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
```

2. Apply the manifest to your current Kubernetes context. Use a disposable namespace if your environment requires one, but keep the Pod name unchanged so the later commands match.

```bash
k apply -f gpu-pod.yaml
```

3. Check the Pod status and observe whether it starts. In a CPU-only cluster, it should remain Pending because no node advertises the extended GPU resource.

```bash
k get pod gpu-test-pod
```

4. Describe the Pod and read the scheduler events near the bottom of the output. Look for a `FailedScheduling` event that mentions `nvidia.com/gpu`, because that event connects the symptom to the missing schedulable resource.

```bash
k describe pod gpu-test-pod
```

5. Inspect node allocatable resources to connect the Pod event to cluster state. If no node lists `nvidia.com/gpu`, Kubernetes has no GPU capacity to allocate, even if a physical machine somewhere in the environment has accelerator hardware but no device plugin integration.

```bash
k describe nodes
```

6. Clean up the Pod after you have captured the result. Leaving a Pending Pod behind is harmless in a lab, but cleanup is part of good cluster hygiene.

```bash
k delete pod gpu-test-pod
```

**Success Criteria:**

- [ ] You created `gpu-pod.yaml` with a container resource limit requesting `nvidia.com/gpu: 1`.
- [ ] You applied the manifest with `kubectl` or the `k` alias after defining the alias.
- [ ] You observed the Pod status and correctly distinguished Pending scheduling failure from a container runtime failure.
- [ ] You found a `FailedScheduling` event or equivalent scheduler message explaining insufficient GPU resources in a CPU-only cluster.
- [ ] You inspected node descriptions and connected missing allocatable `nvidia.com/gpu` capacity to the scheduling result.
- [ ] You can explain what would need to change in a real GPU cluster: GPU nodes, drivers, device plugin or GPU Operator, available capacity, and any required tolerations or node selection.
- [ ] You deleted the lab Pod after completing the investigation.

For extra practice, modify the manifest by adding a fake node selector such as `accelerator: nvidia` and apply it again. Compare the scheduler event with the previous result. The exact wording may differ by Kubernetes version, but the reasoning should be the same: the scheduler can only bind a Pod when resource requests, node labels, taints, tolerations, and available capacity all line up.

---

## Next Module

[Module 3.9: WebAssembly and Cloud Native](../module-3.9-webassembly/) - The emerging technology that can complement containers for fast-starting, portable, and strongly sandboxed workloads.

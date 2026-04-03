---
title: "Module 3.8: AI/ML on Cloud Native Infrastructure"
slug: k8s/kcna/part3-cloud-native-architecture/module-3.8-ai-ml-cloud-native
sidebar:
  order: 9
---
> **Complexity**: `[MEDIUM]` - Conceptual awareness
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 3.1 (Cloud Native Principles), Module 3.3 (Cloud Native Patterns)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** why Kubernetes is the dominant platform for AI/ML workloads
2. **Identify** key tools in the ML on Kubernetes ecosystem: Kubeflow, KServe, and GPU scheduling
3. **Compare** training vs. inference workload requirements and their Kubernetes resource patterns
4. **Evaluate** how Kubernetes scheduling and resource management support GPU and TPU workloads

---

## Why This Module Matters

Artificial Intelligence and Machine Learning workloads are rapidly becoming the largest consumers of cloud infrastructure. Kubernetes is evolving into "the operating system for AI" — not because it was designed for it, but because its extensibility, scheduling, and resource management capabilities make it the natural platform. KCNA expects you to understand how AI/ML intersects with cloud native.

---

## Kubernetes as the AI/ML Platform

```
┌─────────────────────────────────────────────────────────────┐
│              WHY K8S FOR AI/ML?                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Kubernetes provides what AI/ML workloads need:             │
│                                                             │
│  1. GPU SCHEDULING                                          │
│     ─────────────────────────────────────────────────────   │
│     K8s schedules GPUs like CPU/memory — request them,     │
│     the scheduler places your Pod on a node that has them  │
│                                                             │
│  2. DEVICE PLUGINS                                          │
│     ─────────────────────────────────────────────────────   │
│     Extend K8s to manage specialized hardware:             │
│     • NVIDIA GPUs (nvidia.com/gpu)                         │
│     • AMD GPUs, Intel FPGAs, Google TPUs                   │
│     • Any accelerator via the device plugin framework      │
│                                                             │
│  3. BATCH PROCESSING                                        │
│     ─────────────────────────────────────────────────────   │
│     Jobs and CronJobs handle training runs that finish     │
│     (unlike web servers that run forever)                   │
│                                                             │
│  4. AUTOSCALING                                             │
│     ─────────────────────────────────────────────────────   │
│     Scale inference endpoints up/down based on traffic     │
│     Scale to zero when no requests arrive                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### GPU Resources in Kubernetes

GPUs are treated as extended resources. A Pod requests them just like CPU or memory:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1   # Request one NVIDIA GPU
```

Key concepts at KCNA level:

| Concept | What It Means |
|---------|---------------|
| **Device Plugin** | A DaemonSet that advertises hardware (GPUs) to the kubelet |
| **nvidia.com/gpu** | The resource name for NVIDIA GPUs in K8s |
| **GPU time-slicing** | Sharing one physical GPU across multiple Pods (not full isolation) |
| **MIG (Multi-Instance GPU)** | Hardware-level GPU partitioning on NVIDIA A100/H100 |
| **Whole GPU** | One Pod gets exclusive access to one GPU (simplest model) |

> **Key insight**: GPUs are non-compressible resources. Unlike CPU (which can be throttled), if a Pod needs a GPU and none is available, it stays Pending until one frees up.

---

## AI/ML Workload Patterns

```
┌─────────────────────────────────────────────────────────────┐
│              AI/ML WORKLOAD TYPES                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TRAINING                                                   │
│  ─────────────────────────────────────────────────────────  │
│  • Runs for hours/days/weeks                               │
│  • Needs many GPUs (distributed across nodes)              │
│  • Batch workload — runs then completes                    │
│  • Gang scheduling: all workers start together or none do  │
│                                                             │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                          │
│  │GPU 0│ │GPU 1│ │GPU 2│ │GPU 3│  ← Distributed training  │
│  │Node1│ │Node1│ │Node2│ │Node2│    across nodes           │
│  └─────┘ └─────┘ └─────┘ └─────┘                          │
│                                                             │
│  INFERENCE (SERVING)                                        │
│  ─────────────────────────────────────────────────────────  │
│  • Runs continuously, serves predictions                   │
│  • Latency-sensitive (users are waiting)                   │
│  • Needs autoscaling based on request volume               │
│  • Often 1 GPU per replica is enough                       │
│                                                             │
│  Request → [Model Server] → Prediction                     │
│            [Model Server] → (autoscaled replicas)          │
│            [Model Server]                                   │
│                                                             │
│  FINE-TUNING                                                │
│  ─────────────────────────────────────────────────────────  │
│  • Take a pre-trained model, adapt to your data            │
│  • Shorter than full training, fewer GPUs                  │
│  • Increasingly popular with LLMs (LoRA, QLoRA)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Training vs Inference Comparison

| Aspect | Training | Inference |
|--------|----------|-----------|
| **Duration** | Hours to weeks | Continuous |
| **GPU count** | Many (distributed) | Fewer per replica |
| **Pattern** | Batch Job | Long-running Deployment |
| **Scaling** | Fixed during run | Autoscale with traffic |
| **Priority** | Throughput | Latency |
| **Failure handling** | Checkpointing + restart | Load balancer reroutes |

---

## LLM Inference on Kubernetes

Running Large Language Models on your own Kubernetes cluster is a growing trend. Here is why organizations do it:

```
┌─────────────────────────────────────────────────────────────┐
│              WHY SELF-HOST LLMs?                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIVACY      Data never leaves your infrastructure        │
│  COST         No per-token API fees at scale               │
│  LATENCY      Co-locate model with application             │
│  COMPLIANCE   Meet data residency requirements             │
│  CONTROL      Choose model, version, and configuration     │
│                                                             │
│  Trade-off: You manage GPUs, scaling, and model updates    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Tools (Awareness Level)

You do not need to know how to install or configure these tools for KCNA. Know **what they do** and **when you would use them**.

| Tool | What It Does | CNCF Status |
|------|-------------|-------------|
| **Kubeflow** | End-to-end ML platform on K8s: pipelines, notebooks, training, serving | CNCF Incubating |
| **KServe** | Standardized inference serving on K8s — model serving with autoscaling, canary rollouts | Part of Kubeflow ecosystem |
| **Ray** | Distributed computing framework — popular for training and serving at scale | Not CNCF (Anyscale) |
| **vLLM** | High-throughput LLM inference engine — optimized for serving large language models | Open source (UC Berkeley) |
| **NVIDIA GPU Operator** | Automates GPU driver and device plugin setup on K8s nodes | NVIDIA open source |
| **Volcano** | Batch scheduling system for K8s — gang scheduling, fair-share queuing for AI/ML jobs | CNCF Incubating |

```
┌─────────────────────────────────────────────────────────────┐
│              ML PIPELINE ON KUBERNETES                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Data Prep → Training → Evaluation → Serving → Monitoring  │
│     │           │            │           │          │       │
│  [Spark/    [Kubeflow    [Automated   [KServe   [Prometheus │
│   Argo]     Training]    testing]     /vLLM]    + custom]   │
│                                                             │
│  All running as Pods on Kubernetes                         │
│  All managed through the K8s API                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **GPUs cost more than the rest of the cluster combined** — A single NVIDIA H100 GPU node can cost $30,000+, making GPU scheduling and utilization the most expensive resource management problem in Kubernetes. Wasting 10% of GPU time is far more costly than wasting 10% of CPU.

- **Gang scheduling does not exist in default Kubernetes** — The standard kube-scheduler places Pods one at a time. Distributed training needs all workers to start together (gang scheduling), which requires add-ons like Volcano or Coscheduling. Without it, you can get deadlocks where half the workers start and wait forever for the other half.

- **vLLM can serve models 24x faster than naive approaches** — By using PagedAttention (managing GPU memory like an OS manages virtual memory), vLLM dramatically improves throughput for LLM serving. This is why it became the default serving engine for many LLM deployments on K8s.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Thinking K8s natively supports GPUs | GPUs need device plugins installed first | The NVIDIA device plugin (DaemonSet) must be deployed to expose GPUs to K8s |
| Using Deployments for training jobs | Training finishes — Deployments restart forever | Use Jobs or specialized training operators (PyTorchJob, TFJob) |
| One GPU per cluster = enough | LLM training needs many GPUs in parallel | Large models need distributed training across dozens or hundreds of GPUs |
| Ignoring GPU memory (VRAM) | Models that do not fit in VRAM crash | A 70B parameter model needs ~140GB VRAM — more than one GPU holds |
| Treating inference like a batch job | Users expect low latency responses | Use Deployments with autoscaling, not Jobs, for inference endpoints |

---

## Quiz

**1. What is the primary mechanism Kubernetes uses to manage GPU resources?**

A) Built-in GPU scheduler
B) Device plugins that advertise GPUs to the kubelet
C) A special GPU namespace
D) Container runtime GPU detection

<details>
<summary>Answer</summary>

**B) Device plugins that advertise GPUs to the kubelet.** The device plugin framework lets vendors (like NVIDIA) register hardware resources with the kubelet, which then reports them to the scheduler. GPUs are not built into K8s core.
</details>

**2. What is gang scheduling in the context of AI/ML workloads?**

A) Scheduling Pods across as many nodes as possible
B) Running all workers of a distributed job together or not at all
C) Assigning multiple GPUs to a single Pod
D) Scheduling inference requests in batches

<details>
<summary>Answer</summary>

**B) Running all workers of a distributed job together or not at all.** Distributed training requires all workers to communicate. If only half start, they waste GPU resources waiting. Gang scheduling ensures the entire group launches together.
</details>

**3. Which tool is a CNCF Incubating project for end-to-end ML pipelines on Kubernetes?**

A) vLLM
B) Ray
C) Kubeflow
D) TensorFlow

<details>
<summary>Answer</summary>

**C) Kubeflow.** Kubeflow is the CNCF Incubating project that provides ML pipelines, training operators, notebooks, and serving capabilities on Kubernetes. vLLM and Ray are not CNCF projects; TensorFlow is an ML framework, not a K8s platform.
</details>

**4. Why do organizations run LLM inference on their own Kubernetes clusters instead of using cloud APIs?**

A) It is always cheaper than cloud APIs
B) Privacy, latency, compliance, and cost control at scale
C) Cloud APIs do not support large models
D) Kubernetes is required to run LLMs

<details>
<summary>Answer</summary>

**B) Privacy, latency, compliance, and cost control at scale.** Self-hosting keeps data on your infrastructure, reduces per-token costs at high volume, and meets data residency requirements. It is not always cheaper (especially at low volume), and cloud APIs do support large models.
</details>

**5. What Kubernetes resource type is most appropriate for a model training job that runs for 8 hours and then completes?**

A) Deployment
B) DaemonSet
C) Job
D) StatefulSet

<details>
<summary>Answer</summary>

**C) Job.** Training is a batch workload that runs to completion. Jobs are designed for this — they track completions and do not restart Pods after success. Deployments keep Pods running indefinitely, which wastes resources after training finishes.
</details>

**6. What is GPU time-slicing?**

A) Splitting GPU memory into isolated hardware partitions
B) Sharing one GPU across multiple Pods by rotating access in time
C) Running GPU workloads only during off-peak hours
D) Scheduling GPUs across different time zones

<details>
<summary>Answer</summary>

**B) Sharing one GPU across multiple Pods by rotating access in time.** Time-slicing allows multiple Pods to share a single GPU by taking turns, improving utilization for lightweight workloads. It does not provide memory isolation — for that, you need hardware-level MIG (Multi-Instance GPU).
</details>

---

## Summary

- Kubernetes is becoming the standard platform for AI/ML because of its scheduling, extensibility (device plugins), and autoscaling
- **GPU resources** are managed through device plugins (e.g., nvidia.com/gpu) — they are not built into K8s core
- **Training** = batch, distributed, many GPUs, gang scheduling needed
- **Inference** = continuous, latency-sensitive, autoscaled, fewer GPUs per replica
- **Fine-tuning** = adapting pre-trained models, less resource-intensive than full training
- Key ecosystem: **Kubeflow** (CNCF, full platform), **KServe** (serving), **vLLM** (LLM inference), **Ray** (distributed computing), **Volcano** (batch scheduling)
- Self-hosted LLM inference is driven by privacy, cost, latency, and compliance

---

## Next Module

[Module 3.9: WebAssembly and Cloud Native](../module-3.9-webassembly/) - The emerging technology that could complement (or sometimes replace) containers.

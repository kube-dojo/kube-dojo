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

> **Pause and predict**: GPUs are "non-compressible" resources in Kubernetes, unlike CPU which can be throttled. If a Pod requests a GPU but none is available, what happens? How is this different from what happens when a Pod requests more CPU than is available?

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

> **Stop and think**: Training a model runs for days and then completes. Inference serves predictions continuously and must be fast. Which Kubernetes workload resource (Job or Deployment) fits each pattern, and why?

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

- **Kubernetes was not built for AI** — When Kubernetes was released in 2014, deep learning was still in its infancy. The device plugin framework that makes GPU scheduling possible wasn't introduced until late 2017 (Kubernetes 1.8), proving that K8s won the AI platform war through extensibility, not initial design.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Thinking K8s natively supports GPUs | GPUs need device plugins installed first | The NVIDIA device plugin (DaemonSet) must be deployed to expose GPUs to K8s |
| Using Deployments for training jobs | Training finishes — Deployments restart forever | Use Jobs or specialized training operators (PyTorchJob, TFJob) |
| One GPU per cluster = enough | LLM training needs many GPUs in parallel | Large models need distributed training across dozens or hundreds of GPUs |
| Ignoring GPU memory (VRAM) | Models that do not fit in VRAM crash | A 70B parameter model needs ~140GB VRAM — more than one GPU holds |
| Treating inference like a batch job | Users expect low latency responses | Use Deployments with autoscaling, not Jobs, for inference endpoints |
| Using Deployments for batch inference | Batch inference tasks are meant to complete | Use Jobs or specialized batch frameworks for processing large offline datasets, saving Deployments for real-time serving |
| Assuming GPUs scale automatically | Pending GPU Pods won't trigger standard CPU node scaling | Cluster Autoscaler must be explicitly configured with GPU-specific node groups to provision new hardware when requested |

---

## Hands-On Exercise: Simulating a GPU Request

In this exercise, you will create a Pod specification that requests a GPU, even if you don't have a physical GPU in your cluster. This helps you understand how the Kubernetes scheduler handles extended resources.

1. Create a file named `gpu-pod.yaml` with the following content:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: gpu-test-pod
   spec:
     containers:
     - name: cuda-container
       image: nvidia/cuda:11.4.2-base-ubuntu20.04
       command: ["nvidia-smi"]
       resources:
         limits:
           nvidia.com/gpu: 1
   ```
2. Apply the Pod to your cluster: `kubectl apply -f gpu-pod.yaml`
3. Check the Pod's status: `kubectl get pods gpu-test-pod`
4. Describe the Pod to see why it is in that state: `kubectl describe pod gpu-test-pod`

**Success Criteria:**
- [ ] You have successfully created the `gpu-pod.yaml` file.
- [ ] You applied the file and observed that the Pod remains in a `Pending` state (assuming no GPU nodes exist).
- [ ] You identified the `FailedScheduling` event in the describe output indicating insufficient `nvidia.com/gpu` resources.

---

## Quiz

**1. Your engineering team just purchased a cluster of physical servers with NVIDIA H100 GPUs. After installing Kubernetes, developers report that their Pods requesting `nvidia.com/gpu: 1` are stuck in the Pending state. What is the most likely missing component that must be deployed to resolve this issue?**

A) A specialized GPU Scheduler add-on
B) A Device Plugin deployed as a DaemonSet
C) A Custom Resource Definition for the `GPU` object
D) The Container Network Interface (CNI) plugin optimized for AI

<details>
<summary>Answer</summary>

**B) A Device Plugin deployed as a DaemonSet.** The Kubernetes core system does not natively understand or detect GPUs out of the box. Hardware vendors provide Device Plugins, typically deployed as DaemonSets, which inspect the node hardware and advertise the available resources to the local kubelet. The kubelet then updates the node's status with the API server, allowing the scheduler to finally place Pods requesting those specific resources. Without this plugin, the scheduler assumes no GPUs exist.
</details>

**2. A data science team is training a large language model across 16 different GPU nodes. They frequently experience "deadlocks" where 8 Pods start running and hold their GPU resources indefinitely while waiting for the remaining 8 Pods, which are stuck Pending due to cluster capacity. Which scheduling concept must be implemented to fix this problem?**

A) Time-slicing scheduling
B) Priority and Preemption scheduling
C) Gang scheduling
D) Topology-aware scheduling

<details>
<summary>Answer</summary>

**C) Gang scheduling.** Distributed training workloads require all participating worker Pods to communicate with each other simultaneously to process the data effectively. If standard Kubernetes scheduling places only half of the Pods, those Pods will reserve valuable GPUs but do no actual work while waiting for the rest to appear. Gang scheduling (provided by tools like Volcano) solves this by ensuring that the entire group of required Pods is scheduled together at the exact same time, or none of them are scheduled at all.
</details>

**3. Your organization wants to deploy an end-to-end machine learning platform on top of your existing Kubernetes infrastructure. The platform engineering team insists on using a CNCF-backed project that provides notebooks, pipeline orchestration, and model serving out of the box. Which tool best fits these requirements?**

A) vLLM
B) Ray
C) Kubeflow
D) TensorFlow

<details>
<summary>Answer</summary>

**C) Kubeflow.** Kubeflow is a CNCF Incubating project specifically designed to make deployments of machine learning workflows on Kubernetes simple, portable, and scalable. It provides a comprehensive ecosystem including Jupyter notebooks for exploration, pipelines for workflow orchestration, and integrated model serving. While vLLM and Ray are powerful tools in the ML space, they are not CNCF projects and focus on more specific niches like inference throughput or distributed compute rather than an end-to-end platform.
</details>

**4. A financial institution currently uses a public cloud API for their customer service chatbot. The security team mandates that customer data can no longer be sent to external APIs, but the business requires the chatbot to maintain its current response latency. Why would deploying an LLM inference workload directly on their own Kubernetes cluster address these concerns?**

A) It eliminates the need for expensive GPU hardware purchases.
B) It automatically scales better than public cloud provider APIs.
C) It ensures data privacy while allowing the model to be co-located with the application.
D) It prevents the need to manage container networking and storage.

<details>
<summary>Answer</summary>

**C) It ensures data privacy while allowing the model to be co-located with the application.** Self-hosting LLM inference directly on an organization's Kubernetes cluster keeps sensitive data entirely within their own infrastructure, satisfying strict privacy and compliance requirements. Furthermore, co-locating the inference engine within the same cluster as the frontend application reduces network hops, which helps maintain or even improve response latency. The tradeoff is that the platform team must now take on the operational burden of managing specialized GPU nodes, drivers, and scaling policies.
</details>

**5. A machine learning engineer has written a script to process 10,000 images, train a computer vision model, and output the final weights to an S3 bucket. The entire process takes approximately 14 hours. Which Kubernetes workload resource is the most appropriate choice for running this task?**

A) Deployment
B) StatefulSet
C) Job
D) DaemonSet

<details>
<summary>Answer</summary>

**C) Job.** A model training task is fundamentally a batch workload because it has a clear beginning and a definitive end once the model weights are generated. The Job resource in Kubernetes is specifically designed for these types of ephemeral tasks, ensuring that the Pod executes successfully and tracking its completion status. If a Deployment were used instead, Kubernetes would continuously restart the Pod after the 14-hour script finished, wasting expensive compute resources and potentially overwriting the output.
</details>

**6. Your startup operates a Kubernetes cluster with a limited number of physical GPUs. You have several lightweight inference APIs and development notebooks that each require minimal GPU acceleration, but they are currently blocking each other because standard Kubernetes assigns an entire GPU to a single Pod. Which technique should you implement to maximize your hardware utilization?**

A) Multi-Instance GPU (MIG) hardware partitioning
B) CPU emulation for GPU requests
C) GPU time-slicing
D) Dedicated GPU node pools per environment

<details>
<summary>Answer</summary>

**C) GPU time-slicing.** Standard Kubernetes extended resource scheduling allocates whole integer GPUs exclusively to a single Pod, meaning a lightweight workload will strand the remaining compute capacity of that hardware. GPU time-slicing allows the cluster administrator to configure the device plugin to oversubscribe the physical GPU, exposing multiple virtual GPUs to the scheduler. These Pods then share the physical GPU by rotating access over time, which dramatically improves utilization for workloads that do not require full isolation or massive continuous throughput.
</details>

**7. An operations team notices that during high-traffic events, their web application scales up perfectly, but their newly deployed AI recommendation engine crashes because new Pods are assigned to nodes without GPUs. How should the team ensure the recommendation engine only scales onto appropriate hardware?**

A) Implement a horizontal pod autoscaler tied exclusively to GPU utilization metrics.
B) Use node selectors, affinity rules, or specific tolerations to target GPU-enabled node groups.
C) Rewrite the application to fall back to CPU inference when GPUs are unavailable.
D) Deploy the application as a DaemonSet across the entire cluster.

<details>
<summary>Answer</summary>

**B) Use node selectors, affinity rules, or specific tolerations to target GPU-enabled node groups.** Kubernetes does not automatically know that a specific application requires specialized hardware unless the Pod specification explicitly demands it. By applying node selectors or node affinity rules, the scheduler is constrained to only place these Pods on nodes labeled with specific GPU characteristics. Additionally, GPU nodes are often tainted to repel normal workloads, requiring the AI Pods to possess the matching tolerations to be scheduled there successfully.
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
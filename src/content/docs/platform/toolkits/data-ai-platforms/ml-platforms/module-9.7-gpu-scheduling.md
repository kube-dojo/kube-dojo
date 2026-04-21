---
title: "Module 9.7: GPU Scheduling & NVIDIA GPU Operator on Kubernetes"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.7-gpu-scheduling
sidebar:
  order: 8
---
## Complexity: [COMPLEX]

**Time to Complete**: 50 minutes
**Prerequisites**: Kubernetes scheduling (taints, tolerations, node affinity), Module 9.1 (Kubeflow basics), basic ML/AI concepts
**Learning Objectives**:
- Understand GPU device plugin architecture in Kubernetes
- Install and configure the NVIDIA GPU Operator
- Configure GPU sharing with time-slicing and MIG
- Optimize GPU node pools for cost and utilization
- Monitor GPU workloads with DCGM and Prometheus

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Kubernetes GPU scheduling with device plugins, resource limits, and multi-GPU node management**
- **Implement GPU sharing strategies using MIG, time-slicing, and MPS for cost-effective GPU utilization**
- **Deploy GPU-aware autoscaling with Karpenter or Cluster Autoscaler for dynamic ML workload demand**
- **Monitor GPU utilization metrics and optimize scheduling policies for mixed ML training and inference workloads**


## Why This Module Matters

GPUs are the most expensive resource in any Kubernetes cluster. A single NVIDIA A100 node costs $12-30/hour on cloud providers. Most ML teams treat GPU scheduling as an afterthought: they request whole GPUs for jobs that use 15% of capacity, leave nodes idle overnight, and never set up proper monitoring.

The result? Teams routinely waste $50K-$100K/month on underutilized GPU infrastructure.

**Proper GPU scheduling is the highest-ROI infrastructure work you can do for an ML team.**

> A Series B startup came to us after their cloud bill hit $240K/month. Their ML team had 32 A100 GPUs running 24/7 across three clusters. Average utilization? 11%. Fine-tuning jobs that needed 2 GPUs were requesting 8 "just in case." Inference workloads sat on dedicated A100s when an L4 would have been fine. Nobody had configured time-slicing. Nobody had set up preemption. Within three weeks, we cut their GPU spend to $80K/month--same throughput, same training times--by implementing proper scheduling, right-sizing, and spot instances for fault-tolerant jobs. The lead ML engineer said, "We were basically lighting $160K on fire every month."

---

## Did You Know?

- A single NVIDIA H100 GPU costs **$30,000-$40,000** to purchase, and cloud instances with 8 H100s can exceed **$98/hour** ($72K/month if left running)
- NVIDIA's MIG technology can split one A100 into **7 independent GPU instances**, each with isolated memory and compute--turning one $15K GPU into 7 smaller ones
- The average GPU utilization in enterprise Kubernetes clusters is **under 15%**, according to Run.ai's 2025 GPU Utilization Report--meaning 85% of GPU spend is wasted
- Google's Borg system (Kubernetes' predecessor) supported GPU scheduling internally **4 years before** Kubernetes added device plugin support in v1.10 (2018)

---

## GPU Device Plugin Architecture

Before we touch the NVIDIA operator, you need to understand how Kubernetes discovers and allocates GPUs. Kubernetes itself knows nothing about GPUs. It relies on **device plugins** to advertise specialized hardware.

```
┌────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Node                            │
│                                                                    │
│  ┌──────────────┐         ┌──────────────────────────────────┐    │
│  │   kubelet    │◄───────►│      Device Plugin (gRPC)        │    │
│  │              │  gRPC   │                                  │    │
│  │  • Allocate  │  socket │  1. ListAndWatch()               │    │
│  │  • Track     │         │     → Reports available GPUs     │    │
│  │  • Advertise │         │     → "nvidia.com/gpu: 4"        │    │
│  │              │         │                                  │    │
│  │  Extended    │         │  2. Allocate()                   │    │
│  │  Resources:  │         │     → Returns device paths       │    │
│  │  nvidia.com/ │         │     → /dev/nvidia0, /dev/nvidia1 │    │
│  │  gpu: 4      │         │     → Sets NVIDIA_VISIBLE_DEVICES│    │
│  └──────┬───────┘         └──────────────┬───────────────────┘    │
│         │                                │                        │
│         │  Schedule pod                  │  Expose devices        │
│         ▼                                ▼                        │
│  ┌──────────────┐         ┌──────────────────────────────────┐    │
│  │   Pod        │         │      GPU Hardware                │    │
│  │              │         │                                  │    │
│  │  Container:  │────────►│  GPU 0: A100 80GB (allocated)    │    │
│  │  nvidia.com/ │         │  GPU 1: A100 80GB (allocated)    │    │
│  │  gpu: 2      │         │  GPU 2: A100 80GB (free)         │    │
│  │              │         │  GPU 3: A100 80GB (free)          │    │
│  └──────────────┘         └──────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

Key takeaway: GPU allocation is **all-or-nothing by default**. If you request `nvidia.com/gpu: 1`, you get an entire physical GPU. There is no native fractional GPU support in Kubernetes--that requires time-slicing or MIG, which we cover below.

---

## NVIDIA GPU Operator

Managing GPU software on Kubernetes nodes is painful. You need the NVIDIA driver, container toolkit, device plugin, monitoring tools, and optionally MIG configuration--all version-matched. The **GPU Operator** automates the entire stack.

### Components

| Component | What It Does | Why You Need It |
|---|---|---|
| **NVIDIA Driver** | Kernel module for GPU access | Without it, the GPU is invisible to software |
| **Container Toolkit** | nvidia-container-runtime | Enables containers to access GPU devices |
| **Device Plugin** | Advertises GPUs to kubelet | Kubernetes scheduling of `nvidia.com/gpu` |
| **DCGM Exporter** | GPU metrics in Prometheus format | Monitoring utilization, temperature, errors |
| **GPU Feature Discovery** | Labels nodes with GPU details | Schedule workloads to specific GPU types |
| **MIG Manager** | Configures Multi-Instance GPU | Split A100/H100 into isolated instances |
| **Node Status Exporter** | Reports operator health | Alerts when GPU stack is unhealthy |

### Installation

```bash
# Add the NVIDIA Helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install the GPU Operator (installs ALL components)
helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --set driver.enabled=true \
  --set toolkit.enabled=true \
  --set devicePlugin.enabled=true \
  --set dcgmExporter.enabled=true \
  --set migManager.enabled=false \
  --set gfd.enabled=true

# Verify installation (all pods should be Running)
k get pods -n gpu-operator

# Check that GPUs are discovered
k get nodes -o json | jq '.items[].status.capacity | select(."nvidia.com/gpu")'
```

After installation, every GPU node automatically gets labeled with GPU metadata:

```bash
# GPU Feature Discovery labels examples
k get node gpu-node-1 --show-labels | tr ',' '\n' | grep nvidia

# nvidia.com/cuda.driver.major=535
# nvidia.com/cuda.runtime.major=12
# nvidia.com/gpu.count=4
# nvidia.com/gpu.memory=81920
# nvidia.com/gpu.product=NVIDIA-A100-SXM4-80GB
# nvidia.com/mig.capable=true
```

### Running Your First GPU Workload

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test
spec:
  restartPolicy: Never
  containers:
  - name: cuda-test
    image: nvidia/cuda:12.3.1-base-ubuntu22.04
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 1  # Request exactly 1 GPU
```

```bash
k apply -f gpu-test.yaml
k logs gpu-test
# Should show nvidia-smi output with GPU details
```

---

## GPU Sharing: Time-Slicing and MIG

By default, one pod gets one whole GPU. For many workloads--especially inference, development, and small training jobs--this wastes massive capacity. Two solutions exist.

### Time-Slicing (Software Sharing)

Time-slicing lets multiple pods share a single physical GPU by rapidly switching between them, similar to how a CPU time-shares between processes. There is **no memory isolation**--a misbehaving pod can OOM the entire GPU.

```yaml
# ConfigMap for time-slicing configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpu-sharing-config
  namespace: gpu-operator
data:
  any: |-
    version: v1
    sharing:
      timeSlicing:
        renameByDefault: false
        failRequestsGreaterThanOne: false
        resources:
        - name: nvidia.com/gpu
          replicas: 4  # Each physical GPU appears as 4 schedulable units
```

```bash
# Patch the GPU Operator to enable time-slicing
helm upgrade gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --set devicePlugin.config.name=gpu-sharing-config

# Now each physical GPU reports 4 allocatable units
k get node gpu-node-1 -o json | jq '.status.allocatable["nvidia.com/gpu"]'
# "16"  (4 physical GPUs x 4 replicas each)
```

**When to use time-slicing**: Inference workloads, Jupyter notebooks, development environments, workloads that do not need memory isolation.

**When to avoid it**: Training jobs that need guaranteed GPU memory, production inference with strict latency SLAs.

### MIG (Multi-Instance GPU) for A100/H100

MIG provides **hardware-level isolation**. An A100 can be partitioned into up to 7 independent GPU instances, each with its own memory, cache, and compute units. A crashed process in one MIG instance cannot affect another.

```
┌─────────────────────────────────────────────────────┐
│                NVIDIA A100 80GB                      │
│                                                      │
│  Full GPU Mode:                                      │
│  ┌─────────────────────────────────────────────────┐│
│  │           1 x 80GB Instance                     ││
│  └─────────────────────────────────────────────────┘│
│                                                      │
│  MIG Mode (3g.40gb + 2g.20gb + 2g.20gb):            │
│  ┌─────────────────────────┬──────────┬──────────┐  │
│  │   3g.40gb (42 SMs)      │ 2g.20gb  │ 2g.20gb  │  │
│  │   40GB Memory           │ 20GB Mem │ 20GB Mem │  │
│  │   Pod A: Training       │ Pod B:   │ Pod C:   │  │
│  │                         │ Inference│ Notebook │  │
│  └─────────────────────────┴──────────┴──────────┘  │
│                                                      │
│  MIG Mode (7 x 1g.10gb):                            │
│  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐ │
│  │1g.10g│1g.10g│1g.10g│1g.10g│1g.10g│1g.10g│1g.10g│ │
│  │Pod A │Pod B │Pod C │Pod D │Pod E │Pod F │Pod G │ │
│  └──────┴──────┴──────┴──────┴──────┴──────┴──────┘ │
└─────────────────────────────────────────────────────┘
```

```yaml
# MIG configuration via GPU Operator
apiVersion: v1
kind: ConfigMap
metadata:
  name: mig-parted-config
  namespace: gpu-operator
data:
  config.yaml: |
    version: v1
    mig-configs:
      mixed-workload:
        - devices: [0]
          mig-enabled: true
          mig-devices:
            "3g.40gb": 1
            "2g.20gb": 2
      all-small:
        - devices: [0]
          mig-enabled: true
          mig-devices:
            "1g.10gb": 7
```

```yaml
# Request a specific MIG instance in a pod
apiVersion: v1
kind: Pod
metadata:
  name: inference-pod
spec:
  containers:
  - name: model
    image: my-inference:latest
    resources:
      limits:
        nvidia.com/mig-2g.20gb: 1  # Request a 2g.20gb MIG slice
```

---

## GPU Node Management

### GPU Node Pools with Taints and Tolerations

GPU nodes are expensive. You do not want random pods landing on them. Use taints to reserve GPU nodes exclusively for GPU workloads.

```bash
# Taint GPU nodes so only GPU workloads schedule there
k taint nodes gpu-pool-node-1 nvidia.com/gpu=present:NoSchedule
k taint nodes gpu-pool-node-2 nvidia.com/gpu=present:NoSchedule
```

```yaml
# Training job that tolerates the GPU taint
apiVersion: batch/v1
kind: Job
metadata:
  name: model-training
spec:
  template:
    spec:
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Equal"
        value: "present"
        effect: "NoSchedule"
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-A100-SXM4-80GB
      containers:
      - name: trainer
        image: my-training:latest
        resources:
          limits:
            nvidia.com/gpu: 4
      restartPolicy: Never
```

### Cost Optimization with Spot GPU Instances

Spot/preemptible GPU instances cost 60-90% less than on-demand. For fault-tolerant workloads (training with checkpointing), this is free money.

```yaml
# Karpenter NodePool for spot GPU instances
# (See Module 6.1: Karpenter for NodePool fundamentals)
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: gpu-spot-training
spec:
  template:
    spec:
      requirements:
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot"]
      - key: node.kubernetes.io/instance-type
        operator: In
        values: ["p4d.24xlarge", "p5.48xlarge"]
      taints:
      - key: nvidia.com/gpu
        value: "present"
        effect: NoSchedule
  limits:
    nvidia.com/gpu: 32  # Max 32 GPUs in this pool
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 5m
```

**Checkpointing is mandatory for spot GPU training**. When a spot instance is reclaimed, your training job loses all progress unless it saves checkpoints. Most frameworks (PyTorch Lightning, Hugging Face Trainer) have built-in checkpointing--make sure it is enabled.

---

## Gang Scheduling for Distributed Training

Distributed training jobs need **all** their GPUs simultaneously. If a job needs 8 GPUs across 2 nodes and only 6 are available, the job cannot start--but those 6 GPUs sit reserved and idle, blocking other work.

**Gang scheduling** solves this by ensuring all pods in a group are scheduled together or not at all. Kubernetes 1.35 introduced the **CoScheduling** feature gate as an alpha API.

```yaml
# Using the scheduling.k8s.io/pod-group API (K8s 1.35+ alpha)
apiVersion: scheduling.k8s.io/v1alpha1
kind: PodGroup
metadata:
  name: distributed-training
spec:
  scheduleTimeoutSeconds: 300
  minMember: 4  # All 4 pods must be scheduled together
---
apiVersion: batch/v1
kind: Job
metadata:
  name: distributed-training
spec:
  parallelism: 4
  completions: 4
  template:
    metadata:
      labels:
        scheduling.k8s.io/pod-group: distributed-training
    spec:
      schedulerName: coscheduling
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Equal"
        value: "present"
        effect: "NoSchedule"
      containers:
      - name: worker
        image: my-distributed-training:latest
        resources:
          limits:
            nvidia.com/gpu: 2
        env:
        - name: WORLD_SIZE
          value: "4"
        - name: NCCL_DEBUG
          value: "INFO"
      restartPolicy: Never
```

For production use today, consider **Volcano** (CNCF sandbox project) or **Coscheduling plugin** for kube-scheduler, which provide mature gang scheduling support.

---

## GPU Monitoring with DCGM Exporter

The DCGM (Data Center GPU Manager) Exporter ships GPU metrics to Prometheus. If you installed the GPU Operator with `dcgmExporter.enabled=true`, it is already running.

### Key Metrics

| Metric | What It Tells You | Alert Threshold |
|---|---|---|
| `DCGM_FI_DEV_GPU_UTIL` | GPU compute utilization % | < 10% for 30min = wasted |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | Memory bandwidth utilization % | Indicates data transfer bottleneck |
| `DCGM_FI_DEV_FB_USED` | GPU memory used (MB) | Near limit = OOM risk |
| `DCGM_FI_DEV_GPU_TEMP` | GPU temperature (C) | > 85C = throttling risk |
| `DCGM_FI_DEV_POWER_USAGE` | Power draw (W) | Track for cost allocation |
| `DCGM_FI_DEV_XID_ERRORS` | Hardware/driver errors | Any value > 0 = investigate |

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dcgm-exporter
  namespace: gpu-operator
spec:
  selector:
    matchLabels:
      app: nvidia-dcgm-exporter
  endpoints:
  - port: gpu-metrics
    interval: 15s
```

### Grafana Dashboard Query Examples

```promql
# Average GPU utilization across all GPUs
avg(DCGM_FI_DEV_GPU_UTIL) by (gpu, Hostname)

# GPU memory usage percentage
DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_FREE * 100

# Idle GPUs (utilization below 5% for 30 minutes)
avg_over_time(DCGM_FI_DEV_GPU_UTIL[30m]) < 5
```

Import NVIDIA's official Grafana dashboard (ID: **12239**) for an out-of-the-box GPU monitoring view.

---

## GPU Vendor Comparison

| Feature | NVIDIA (CUDA) | AMD (ROCm) | Intel (oneAPI) |
|---|---|---|---|
| **K8s Device Plugin** | Mature, GPU Operator | Community `amd-gpu` plugin | Intel Device Plugins Operator |
| **ML Framework Support** | Broad (PyTorch, TF, JAX) | PyTorch (good), TF (limited) | PyTorch (growing), oneAPI DPC++ |
| **GPU Sharing** | Time-slicing + MIG | No equivalent to MIG | SR-IOV based partitioning |
| **Monitoring** | DCGM Exporter (Prometheus) | ROCm SMI Exporter | Intel GPU metrics (limited) |
| **Cloud Availability** | All major clouds | Limited (Azure, some AWS) | Intel Flex/Max on select clouds |
| **Ecosystem Maturity** | Production-grade | Catching up rapidly | Early stage for ML |
| **Cost** | Premium ($10K-$40K/GPU) | 30-50% cheaper for similar perf | Competitive for inference |
| **Best For** | Training + inference (default) | Budget-conscious training | Intel-shop inference |

**The honest take**: NVIDIA dominates. ROCm has made impressive strides--PyTorch on AMD MI300X is competitive with H100 for many workloads--but the ecosystem gap in tooling, monitoring, and community support is still significant. Choose AMD or Intel only if you have a specific cost or vendor strategy.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix |
|---|---|---|
| Requesting whole GPUs for inference | Copy-paste from training configs | Use time-slicing or MIG for inference workloads |
| No GPU node taints | Did not realize non-GPU pods would land there | Taint GPU nodes with `NoSchedule` from day one |
| Ignoring GPU utilization metrics | DCGM exporter not installed or not dashboarded | Install GPU Operator with DCGM, import Grafana dashboard 12239 |
| Running training on on-demand instances | Default instance type in node pool config | Use spot/preemptible for fault-tolerant training with checkpointing |
| No resource quotas on GPU namespaces | Single team hoards all GPUs | Set `ResourceQuota` with `nvidia.com/gpu` limits per namespace |
| Using A100 for small inference | Over-provisioning "just in case" | Right-size: use T4/L4 for inference, A100/H100 for training |
| Not enabling MIG on multi-tenant clusters | Unaware of MIG or think it is complex | GPU Operator MIG Manager automates partitioning |
| Distributed training without gang scheduling | Pods scheduled piecemeal, deadlocking | Use Volcano or CoScheduling for all-or-nothing scheduling |

---

## Quiz

**Question 1**: A pod requests `nvidia.com/gpu: 1`. The node has 4 physical GPUs with time-slicing configured at `replicas: 4`. How many pods requesting 1 GPU can this node run simultaneously?

<details>
<summary>Show Answer</summary>

**16 pods.** Time-slicing with `replicas: 4` makes each physical GPU appear as 4 schedulable units. 4 physical GPUs x 4 replicas = 16 allocatable `nvidia.com/gpu` units. Note that all 16 pods share the physical GPU memory, so actual capacity depends on memory usage.

</details>

**Question 2**: Why is MIG preferred over time-slicing for production multi-tenant GPU sharing?

<details>
<summary>Show Answer</summary>

MIG provides **hardware-level isolation**. Each MIG instance has dedicated compute units (SMs), memory, and L2 cache. A process in one MIG instance cannot access another's memory or cause it to OOM. Time-slicing has **no memory isolation**--a single pod can exhaust all GPU memory and crash every other pod sharing that GPU.

</details>

**Question 3**: Your distributed training job needs 8 GPUs across 4 nodes (2 GPUs each). Only 6 GPUs are currently available. Without gang scheduling, what happens?

<details>
<summary>Show Answer</summary>

Without gang scheduling, the scheduler places pods on the 6 available GPUs. The remaining 2 pods stay `Pending`. The 6 running pods cannot start training (they need all 8 workers for NCCL communication). Result: 6 expensive GPUs sit **completely idle** waiting for the last 2, while blocking other jobs from using those GPUs. Gang scheduling prevents this by requiring all 8 pods to be schedulable before any are placed.

</details>

**Question 4**: You notice `DCGM_FI_DEV_GPU_UTIL` averaging 8% on your inference nodes. What are two actions to improve utilization?

<details>
<summary>Show Answer</summary>

1. **Enable time-slicing or MIG** to pack multiple inference workloads onto each GPU. At 8% utilization, each GPU could likely serve 4-8 models simultaneously.
2. **Right-size the GPU type**. If inference workloads only need 2-4GB of GPU memory, switch from A100 ($12/hr) to T4 ($0.70/hr) or L4 ($1.20/hr). A 8% utilized A100 is doing work that a fully utilized T4 handles for 95% less cost.

</details>

---

## Hands-On Exercise: GPU Scheduling with Time-Slicing

**Goal**: Configure GPU time-slicing and demonstrate multi-pod GPU sharing.

> **Note**: This exercise requires a GPU-equipped cluster. If you do not have GPU hardware, you can follow along conceptually or use a cloud provider's GPU node pool (even a single T4 instance works).

### Step 1: Install the GPU Operator

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --wait --timeout 10m
```

### Step 2: Verify GPU Discovery

```bash
# Wait for all operator pods to be Running
k get pods -n gpu-operator -w

# Confirm GPU count on your node
k describe node <gpu-node> | grep nvidia.com/gpu
# Expected: nvidia.com/gpu: 1 (or however many GPUs your node has)
```

### Step 3: Enable Time-Slicing (4 replicas per GPU)

```bash
k create configmap gpu-sharing-config -n gpu-operator --from-literal=any='
version: v1
sharing:
  timeSlicing:
    resources:
    - name: nvidia.com/gpu
      replicas: 4
'

helm upgrade gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --set devicePlugin.config.name=gpu-sharing-config

# Verify: allocatable GPUs should now be 4x physical count
k describe node <gpu-node> | grep nvidia.com/gpu
# Expected: nvidia.com/gpu: 4 (1 physical GPU x 4 replicas)
```

### Step 4: Run 4 Pods on 1 Physical GPU

```bash
for i in 1 2 3 4; do
  k run gpu-pod-$i --image=nvidia/cuda:12.3.1-base-ubuntu22.04 \
    --limits=nvidia.com/gpu=1 \
    --command -- sleep 3600
done

# All 4 should be Running on the same node
k get pods -o wide | grep gpu-pod
```

### Step 5: Verify GPU Sharing

```bash
# Each pod sees the same physical GPU
for i in 1 2 3 4; do
  echo "=== gpu-pod-$i ==="
  k exec gpu-pod-$i -- nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
done
```

### Success Criteria

- [ ] GPU Operator pods all Running in `gpu-operator` namespace
- [ ] Node reports 4x allocatable GPUs after time-slicing config
- [ ] All 4 pods are Running simultaneously on a single physical GPU
- [ ] Each pod can execute `nvidia-smi` and sees the GPU

### Cleanup

```bash
k delete pod gpu-pod-1 gpu-pod-2 gpu-pod-3 gpu-pod-4
```

---

## Current Landscape

| Tool | Purpose | When to Use |
|---|---|---|
| **NVIDIA GPU Operator** | Full GPU stack management | Any NVIDIA GPU cluster |
| **Run.ai** | GPU virtualization and scheduling | Enterprise multi-tenant GPU sharing |
| **Volcano** | Batch/gang scheduling for K8s | Distributed training (production-ready today) |
| **Kueue** | K8s-native job queueing | GPU job queuing with fair sharing |
| **Karpenter** | Node autoscaling | Auto-provision GPU nodes on demand ([Module 6.1](/platform/toolkits/developer-experience/scaling-reliability/module-6.1-karpenter/)) |

For MLOps pipeline integration with GPU workloads, see [Module 9.1: Kubeflow](../module-9.1-kubeflow/).

---

## Best Practices

1. **Taint every GPU node** from the moment it joins the cluster. No exceptions.
2. **Set namespace-level GPU quotas** to prevent a single team from monopolizing GPUs.
3. **Use time-slicing for dev/inference**, MIG for multi-tenant production.
4. **Monitor utilization weekly**. Any GPU averaging under 20% needs right-sizing or consolidation.
5. **Use spot instances** for all training workloads that support checkpointing.
6. **Right-size GPU types**: T4/L4 for inference, A100/H100 for training.
7. **Enable gang scheduling** for any distributed training job.
8. **Label GPU nodes** with GPU type, memory, and MIG capability for precise scheduling.

---

## Further Reading

- [NVIDIA GPU Operator Documentation](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/)
- [Kubernetes Device Plugin Framework](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [NVIDIA MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/)
- [Volcano Project - Gang Scheduling](https://volcano.sh/en/)
- [DCGM Exporter for Prometheus](https://github.com/NVIDIA/dcgm-exporter)
- [Run.ai GPU Utilization Report 2025](https://www.run.ai/guides/gpu-optimization)

---

## Next Module

[Module 10.1: Anomaly Detection Tools](/platform/toolkits/observability-intelligence/aiops-tools/module-10.1-anomaly-detection-tools/) - Apply AI to your infrastructure with AIOps.

## Sources

- [Kubernetes: Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) — This is the canonical upstream reference for how Kubernetes exposes and schedules GPU resources.
- [Kubernetes: Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) — This explains the kubelet registration flow, integer extended resources, and why GPU access depends on device plugins.
- [Kubernetes: Gang Scheduling](https://kubernetes.io/docs/concepts/scheduling-eviction/gang-scheduling/) — This is the upstream description of the v1.35 alpha gang-scheduling model and its all-or-nothing semantics.
- [NVIDIA GPU Operator](https://github.com/NVIDIA/gpu-operator) — This upstream repository describes the operator-managed NVIDIA GPU stack and is the best allowlisted source for operator scope.

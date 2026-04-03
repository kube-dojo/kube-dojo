---
title: "Module 1.1: GPU Provisioning & Device Plugins"
slug: platform/disciplines/data-ai/ai-infrastructure/module-1.1-gpu-provisioning
sidebar:
  order: 2
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 3 hours

## Prerequisites

Before starting this module:
- **Required**: Kubernetes administration experience (Deployments, DaemonSets, RBAC, Helm)
- **Required**: Basic Linux hardware awareness (PCI devices, drivers, kernel modules)
- **Recommended**: [Observability Theory](../../../foundations/observability-theory/) — Understanding metrics pipelines
- **Recommended**: Access to a node with at least one NVIDIA GPU (even a modest T4 or RTX 3060 works)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure GPU node pools on Kubernetes with proper device plugins, drivers, and runtime settings**
- **Design GPU provisioning strategies that balance availability, cost, and workload requirements**
- **Implement node affinity and toleration rules that schedule GPU workloads on appropriate hardware**
- **Evaluate GPU instance types across cloud providers to optimize price-performance for your AI workloads**

## Why This Module Matters

GPUs are the engine of the AI revolution — and they are absurdly expensive. A single NVIDIA H100 costs more than most engineers' annual salary. An 8-GPU DGX H100 node lists north of $300,000.

If your organization is investing in AI, someone has to make those GPUs available to data scientists, ML engineers, and inference pipelines **reliably, securely, and without waste**. That someone is the platform team.

**Here's the uncomfortable truth**: Kubernetes was designed for CPUs. GPUs are a bolt-on. The Device Plugin API, the GPU Operator, the container toolkit — these exist because GPUs don't fit neatly into the Kubernetes resource model. Understanding these seams is the difference between a GPU platform that works and one that burns money while scientists wait.

This module teaches you how GPUs become first-class citizens in your cluster.

---

## The GPU Landscape in Kubernetes

### Why GPUs Are Different

A CPU is a **general-purpose** processor. Kubernetes understands CPUs intimately: it can measure usage in millicores, throttle processes, and share a single CPU across dozens of containers.

A GPU is a **specialized** processor. It has its own memory (VRAM), its own driver stack, and its own rules:

| Property | CPU | GPU |
|----------|-----|-----|
| Sharing model | Time-slicing built into OS | Requires explicit configuration |
| Memory | Shared system RAM, overcommittable | Dedicated VRAM, not overcommittable by default |
| Driver | Kernel built-in | Proprietary, version-sensitive |
| Kubernetes awareness | Native | Via Device Plugin API |
| Failure mode | Graceful degradation | Hard crash (OOM, Xid errors) |

### The Software Stack

From bottom to top, here is every layer involved in running a GPU workload on Kubernetes:

```
┌────────────────────────────────────────────────┐
│           User Pod (PyTorch, TensorFlow)        │
├────────────────────────────────────────────────┤
│         CUDA Libraries (libcuda, cuDNN)         │
├────────────────────────────────────────────────┤
│       nvidia-container-toolkit (libnvidia)       │
├────────────────────────────────────────────────┤
│             Container Runtime (containerd)       │
├────────────────────────────────────────────────┤
│          NVIDIA Device Plugin (DaemonSet)        │
├────────────────────────────────────────────────┤
│        NVIDIA Driver (kernel module)             │
├────────────────────────────────────────────────┤
│              Linux Kernel                        │
├────────────────────────────────────────────────┤
│          Physical GPU (PCIe / NVLink)            │
└────────────────────────────────────────────────┘
```

Every layer matters. A mismatch between the CUDA version in your container and the driver on the host will give you cryptic errors that waste hours.

---

## The Kubernetes Device Plugin API

### How It Works

The Device Plugin API (stable since Kubernetes 1.26) is the mechanism that lets Kubernetes discover and allocate hardware devices — GPUs, FPGAs, InfiniBand NICs, anything the kubelet doesn't know about natively.

The flow:

1. **Registration**: The device plugin registers itself with the kubelet via a Unix domain socket at `/var/lib/kubelet/device-plugins/`
2. **Discovery**: The plugin reports available devices and their health to the kubelet via gRPC `ListAndWatch`
3. **Allocation**: When a Pod requests a device (e.g., `nvidia.com/gpu: 1`), the kubelet calls the plugin's `Allocate` RPC
4. **Injection**: The plugin returns device paths, environment variables, and mounts that the kubelet injects into the container

```
┌──────────┐     Register      ┌──────────┐
│  Device   │ ───────────────→ │  Kubelet  │
│  Plugin   │                  │           │
│           │ ◄─ ListAndWatch  │           │
│  (gRPC    │ ──→ DeviceList   │           │
│   server) │                  │           │
│           │ ◄─ Allocate()    │           │
│           │ ──→ Devices,Envs │           │
└──────────┘                   └──────────┘
```

### What the Plugin Advertises

After registration, your node will show GPU resources:

```bash
kubectl describe node gpu-worker-01 | grep -A 6 "Capacity:"
```

```
Capacity:
  cpu:                64
  memory:             256Gi
  nvidia.com/gpu:     4
Allocatable:
  cpu:                63500m
  memory:             254Gi
  nvidia.com/gpu:     4
```

### Requesting GPUs in Pod Specs

GPUs are requested in the `resources.limits` field. **You cannot request fractional GPUs through the standard API** — it is always whole integers:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cuda-vectoradd
spec:
  restartPolicy: OnFailure
  containers:
    - name: vectoradd
      image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda12.5.0
      resources:
        limits:
          nvidia.com/gpu: 1    # Request exactly 1 GPU
```

Three critical rules to remember:

1. **Limits only**: You specify GPUs in `limits`, not `requests`. The kubelet sets `requests` equal to `limits` automatically.
2. **No overcommit**: If you request 1 GPU, you get exactly 1 GPU. There is no CPU-like "fractional usage."
3. **No cross-node**: A single Pod cannot use GPUs from multiple nodes (for that, you need distributed training — Module 1.3).

---

## Node Feature Discovery (NFD)

### The Problem

You have a heterogeneous cluster: some nodes have A100 GPUs, some have T4s, some have no GPUs at all. How do you ensure workloads land on the right hardware?

Labels. But **manually** labeling nodes is error-prone and doesn't scale.

### The Solution

Node Feature Discovery (NFD) is a Kubernetes add-on that automatically detects hardware features and labels nodes:

```bash
# NFD automatically adds labels like:
feature.node.kubernetes.io/pci-10de.present=true        # NVIDIA PCI device
feature.node.kubernetes.io/cpu-model.vendor_id=Intel
feature.node.kubernetes.io/kernel-version.major=5
```

When combined with the GPU Operator, NFD adds GPU-specific labels:

```bash
nvidia.com/gpu.product=NVIDIA-A100-SXM4-80GB
nvidia.com/gpu.memory=81920
nvidia.com/gpu.count=8
nvidia.com/gpu.machine=DGX-A100
nvidia.com/cuda.driver.major=535
nvidia.com/mig.capable=true
```

Now you can write `nodeSelector` or `nodeAffinity` rules that are precise:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: nvidia.com/gpu.product
              operator: In
              values:
                - NVIDIA-A100-SXM4-80GB
                - NVIDIA-H100-SXM5-80GB
```

This ensures your large training job lands on A100/H100 nodes, not on a T4 that would take 15x longer.

---

## nvidia-container-toolkit

### What It Does

The nvidia-container-toolkit (formerly nvidia-docker2) is the bridge between containers and GPUs. Without it, a container cannot see or use any GPU on the host.

It works by hooking into the container runtime (containerd or CRI-O) and:

1. **Mounting the NVIDIA driver** libraries from the host into the container
2. **Creating device nodes** (`/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-uvm`) inside the container
3. **Setting environment variables** (`NVIDIA_VISIBLE_DEVICES`, `NVIDIA_DRIVER_CAPABILITIES`)

### The Container Runtime Flow

```
Pod created
    │
    ▼
kubelet calls containerd
    │
    ▼
containerd invokes nvidia-container-runtime-hook
    │
    ▼
Hook calls libnvidia-container
    │
    ▼
libnvidia-container:
  - Discovers host GPU driver
  - Mounts /usr/lib/x86_64-linux-gnu/libnvidia-*.so
  - Creates /dev/nvidia* device nodes
  - Sets CUDA_VISIBLE_DEVICES
    │
    ▼
Container starts with GPU access
```

### Configuration

The toolkit is configured at `/etc/nvidia-container-runtime/config.toml`:

```toml
[nvidia-container-cli]
# Root of the driver installation
root = "/"
# Path to the ldconfig binary
ldconfig = "@/sbin/ldconfig"

[nvidia-container-runtime]
# Use cdi (Container Device Interface) mode for modern setups
mode = "cdi"
# Log level
log-level = "info"
```

Modern setups (Kubernetes 1.28+) prefer **CDI mode** (Container Device Interface), which generates CDI specification files that the container runtime reads directly, removing the need for the runtime hook.

---

## The NVIDIA GPU Operator

### Why It Exists

Installing GPUs on Kubernetes requires managing at least 6 separate components:

1. NVIDIA drivers
2. nvidia-container-toolkit
3. Kubernetes device plugin
4. DCGM-Exporter (metrics)
5. Node Feature Discovery
6. GPU Feature Discovery

Managing these independently — especially driver upgrades across a fleet — is a nightmare. The GPU Operator bundles everything into a single Helm chart with a CRD-driven lifecycle.

### Architecture

```
┌──────────────────────────────────────────────────────┐
│                  GPU Operator Controller               │
│            (watches ClusterPolicy CRD)                │
└───────────────────┬──────────────────────────────────┘
                    │ Creates and manages
        ┌───────────┼───────────────────────┐
        ▼           ▼                       ▼
┌──────────┐  ┌──────────────┐  ┌────────────────────┐
│   NFD     │  │ Driver       │  │ Container Toolkit  │
│ DaemonSet │  │ DaemonSet    │  │ DaemonSet          │
└──────────┘  └──────────────┘  └────────────────────┘
        ┌───────────┼───────────────────────┐
        ▼           ▼                       ▼
┌──────────┐  ┌──────────────┐  ┌────────────────────┐
│  Device   │  │ DCGM         │  │ GPU Feature        │
│  Plugin   │  │ Exporter     │  │ Discovery          │
│ DaemonSet │  │ DaemonSet    │  │ DaemonSet          │
└──────────┘  └──────────────┘  └────────────────────┘
```

### Installation

```bash
# Add the NVIDIA Helm repository
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install the GPU Operator
helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --version v24.9.0 \
  --set driver.enabled=true \
  --set toolkit.enabled=true \
  --set dcgmExporter.enabled=true \
  --set mig.strategy=single \
  --set nfd.enabled=true
```

### The ClusterPolicy CRD

The GPU Operator is configured through a `ClusterPolicy` custom resource:

```yaml
apiVersion: nvidia.com/v1
kind: ClusterPolicy
metadata:
  name: cluster-policy
spec:
  operator:
    defaultRuntime: containerd
  driver:
    enabled: true
    version: "550.127.08"
    repository: nvcr.io/nvidia
    image: driver
    licensingConfig:
      configMapName: ""
  toolkit:
    enabled: true
    version: v1.16.2-ubuntu22.04
  devicePlugin:
    enabled: true
    version: v0.16.2
    config:
      name: device-plugin-config
      default: default
  dcgmExporter:
    enabled: true
    version: 3.3.8-3.6.0-ubuntu22.04
    serviceMonitor:
      enabled: true         # Create ServiceMonitor for Prometheus
  mig:
    strategy: single        # "single" or "mixed"
  nodeFeatureDiscovery:
    enabled: true
  gfd:
    enabled: true
```

### Verifying the Installation

After installation, verify that every component is running:

```bash
# Check all GPU Operator pods
kubectl get pods -n gpu-operator

# Expected output (9-12 pods depending on config):
# NAME                                                  READY   STATUS
# gpu-operator-7b8f6d4c5-xk9m2                        1/1     Running
# nvidia-container-toolkit-daemonset-8x7zk             1/1     Running
# nvidia-cuda-validator-gpu-worker-01                   0/1     Completed
# nvidia-dcgm-exporter-5k2j8                           1/1     Running
# nvidia-device-plugin-daemonset-lr4nt                 1/1     Running
# nvidia-driver-daemonset-550.127.08-gpu-worker-01     1/1     Running
# nvidia-node-feature-discovery-master-6c4b8f7-m9xj2  1/1     Running
# nvidia-node-feature-discovery-worker-7g8x4           1/1     Running
# nvidia-operator-validator-gpu-worker-01               1/1     Running

# Verify GPU resources are advertised
kubectl describe node gpu-worker-01 | grep nvidia.com/gpu

# Run a CUDA validation pod
kubectl run cuda-test --rm -it --restart=Never \
  --image=nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda12.5.0 \
  --overrides='{"spec":{"containers":[{"name":"cuda-test","image":"nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda12.5.0","resources":{"limits":{"nvidia.com/gpu":"1"}}}]}}' \
  -- ./vectoradd

# Expected: "Test PASSED"
```

---

## DCGM-Exporter: GPU Metrics for Prometheus

### Why GPU Metrics Matter

You cannot manage what you cannot measure. Without GPU metrics, you are flying blind:

- Is the GPU actually being used, or is it idle while you pay $3/hr for it?
- Is the GPU memory full, or is the workload only using 10% of VRAM?
- Is the GPU throttling due to temperature?
- Are there ECC memory errors that predict hardware failure?

### What DCGM-Exporter Provides

DCGM (Data Center GPU Manager) is NVIDIA's tool for monitoring GPUs. DCGM-Exporter wraps it as a Prometheus exporter. Key metrics:

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| `DCGM_FI_DEV_GPU_UTIL` | GPU compute utilization (%) | Is the GPU busy or idle? |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | Memory bandwidth utilization (%) | Data transfer bottleneck? |
| `DCGM_FI_DEV_FB_USED` | Framebuffer memory used (MiB) | How much VRAM is consumed? |
| `DCGM_FI_DEV_FB_FREE` | Framebuffer memory free (MiB) | How much VRAM is available? |
| `DCGM_FI_DEV_GPU_TEMP` | GPU temperature (C) | Thermal throttling? |
| `DCGM_FI_DEV_POWER_USAGE` | Power draw (W) | Energy cost tracking |
| `DCGM_FI_DEV_SM_CLOCK` | Streaming multiprocessor clock (MHz) | Is the GPU at full speed? |
| `DCGM_FI_DEV_XID_ERRORS` | Xid error count | Hardware problems? |
| `DCGM_FI_DEV_PCIE_TX_THROUGHPUT` | PCIe TX throughput (KB/s) | Data transfer bottleneck? |
| `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | Ratio of time the GPU was active | More precise than utilization |

### Custom Metrics Configuration

You can control which metrics DCGM-Exporter collects via a ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dcgm-metrics
  namespace: gpu-operator
data:
  default-counters.csv: |
    DCGM_FI_DEV_GPU_UTIL,         gauge, GPU utilization (%).
    DCGM_FI_DEV_MEM_COPY_UTIL,    gauge, Memory utilization (%).
    DCGM_FI_DEV_FB_FREE,          gauge, Framebuffer memory free (MiB).
    DCGM_FI_DEV_FB_USED,          gauge, Framebuffer memory used (MiB).
    DCGM_FI_DEV_GPU_TEMP,         gauge, GPU temperature (C).
    DCGM_FI_DEV_POWER_USAGE,      gauge, Power draw (W).
    DCGM_FI_DEV_PCIE_TX_THROUGHPUT, gauge, PCIe TX throughput (KB/s).
    DCGM_FI_DEV_PCIE_RX_THROUGHPUT, gauge, PCIe RX throughput (KB/s).
    DCGM_FI_DEV_XID_ERRORS,       gauge, Value of the last XID error.
    DCGM_FI_PROF_GR_ENGINE_ACTIVE, gauge, Ratio of time the graphics engine is active.
    DCGM_FI_PROF_PIPE_TENSOR_ACTIVE, gauge, Ratio of time the tensor cores are active.
```

### Grafana Dashboard

Once DCGM-Exporter feeds Prometheus, you can import the official NVIDIA dashboard (Grafana ID: **12239**) or build your own. Essential panels:

```
┌──────────────────────────────────────────────────────┐
│  GPU Cluster Overview                                 │
├──────────────┬───────────────┬───────────────────────┤
│ GPU Util %   │ Memory Used   │ Temperature           │
│   ▓▓▓▓░░ 67%│  ▓▓▓▓▓░ 72GB │  ▓▓▓░░ 62°C          │
├──────────────┴───────────────┴───────────────────────┤
│ Per-GPU Utilization Timeline                         │
│ ┌──────────────────────────────────────────────────┐ │
│ │ GPU0 ████████████░░░░  78%                       │ │
│ │ GPU1 ████████████████░ 94%                       │ │
│ │ GPU2 ██░░░░░░░░░░░░░░ 12%  ← investigate this   │ │
│ │ GPU3 ████████████████  100%                      │ │
│ └──────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────┤
│ Xid Errors (last 24h): 0    Power Draw: 1,247W     │
└──────────────────────────────────────────────────────┘
```

### Alerting on GPU Metrics

Create PrometheusRules for GPU health:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: gpu-alerts
  namespace: monitoring
spec:
  groups:
    - name: gpu.rules
      rules:
        - alert: GPUHighTemperature
          expr: DCGM_FI_DEV_GPU_TEMP > 85
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "GPU {{ $labels.gpu }} on {{ $labels.node }} is at {{ $value }}C"

        - alert: GPUMemoryNearFull
          expr: (DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE)) > 0.95
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "GPU {{ $labels.gpu }} VRAM is {{ $value | humanizePercentage }} full"

        - alert: GPUXidError
          expr: DCGM_FI_DEV_XID_ERRORS != 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "GPU {{ $labels.gpu }} Xid error {{ $value }} — check dmesg"

        - alert: GPUUnderutilized
          expr: DCGM_FI_DEV_GPU_UTIL < 10
          for: 30m
          labels:
            severity: info
          annotations:
            summary: "GPU {{ $labels.gpu }} has been below 10% utilization for 30m — waste?"
```

---

## Try This: Explore nvidia-smi Inside a Container

If you have a GPU node, run this to understand what the nvidia-container-toolkit actually injects:

```bash
kubectl run nvidia-smi --rm -it --restart=Never \
  --image=nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04 \
  --overrides='{"spec":{"containers":[{"name":"nvidia-smi","image":"nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04","resources":{"limits":{"nvidia.com/gpu":"1"}}}]}}' \
  -- bash -c '
    echo "=== nvidia-smi ==="
    nvidia-smi
    echo ""
    echo "=== NVIDIA device nodes ==="
    ls -la /dev/nvidia*
    echo ""
    echo "=== CUDA_VISIBLE_DEVICES ==="
    echo $CUDA_VISIBLE_DEVICES
    echo ""
    echo "=== NVIDIA libraries mounted ==="
    ldconfig -p | grep nvidia | head -15
  '
```

Notice how the device nodes and libraries appear inside the container even though the container image has no NVIDIA driver installed. That is the nvidia-container-toolkit at work.

---

## Did You Know?

1. **A single NVIDIA H100 GPU draws up to 700W of power** — roughly the same as a microwave oven. An 8-GPU server can draw 10kW, which is why GPU data centers require specialized cooling. Some hyperscalers spend more on electricity for GPUs than on the GPUs themselves over a 3-year lifecycle.

2. **The Kubernetes Device Plugin API was originally designed for FPGAs, not GPUs**. Intel proposed it in 2017 for their Arria/Stratix FPGAs. NVIDIA adopted it quickly, and GPUs became the dominant use case — but the API's design (whole-device allocation, no fractional sharing) reflects its FPGA origins.

3. **Xid error 79 (GPU has fallen off the bus)** is the most dreaded error in GPU operations. It means the GPU has become unreachable via PCIe and usually requires a full node reboot. In large clusters, teams see this several times per week and automate node drain/reboot workflows around it.

---

## War Story: The $47,000 Idle GPU Weekend

A platform team I advised provisioned a cluster of 16 A100 nodes on a cloud provider for a major training run. The training job finished on Friday afternoon. Nobody remembered to scale down the cluster. The nodes sat idle — 128 GPUs doing absolutely nothing — for the entire weekend.

**Cost**: 128 GPUs x $3.06/hr x 60 hours = **$23,500**. And this happened twice before anyone noticed the pattern.

**The fix**: Three changes saved them:

1. **DCGM-Exporter alerts** for GPUs below 5% utilization for more than 1 hour
2. **Karpenter** (Module 1.6) configured to scale GPU nodes to zero when no pending GPU pods exist
3. **A Slack webhook** that posts to #gpu-costs when any GPU node has been idle for 30 minutes

The monitoring paid for itself on the first prevented incident.

**Lesson**: GPU observability is not optional. Every minute an idle GPU runs costs real money.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Requesting GPUs in `requests` only | Kubelet ignores `requests` for extended resources; Pod gets no GPU | Always specify `limits` for `nvidia.com/gpu` |
| Mismatched CUDA/driver versions | `CUDA error: no kernel image is available` or `driver version insufficient` | Check compatibility matrix at docs.nvidia.com/deploy/cuda-compatibility |
| Not installing nvidia-container-toolkit | Container starts but `nvidia-smi` returns "command not found" | GPU Operator handles this; if manual, install toolkit and restart containerd |
| Manually labeling GPU nodes | Labels drift, new nodes missed | Use NFD + GPU Feature Discovery for automatic labeling |
| Ignoring Xid errors | Silent data corruption or crashes during training | Alert on `DCGM_FI_DEV_XID_ERRORS` and drain nodes with persistent Xid errors |
| Deploying GPU Operator without monitoring | GPUs are idle or overheated without anyone knowing | Always enable DCGM-Exporter and create PrometheusRules |
| Using `nvidia-docker2` (deprecated) | Outdated, no CDI support | Migrate to nvidia-container-toolkit with CDI mode |

---

## Quiz: Check Your Understanding

### Question 1
What gRPC methods does a Kubernetes Device Plugin implement, and what is the lifecycle of GPU allocation?

<details>
<summary>Show Answer</summary>

A Device Plugin implements three key gRPC methods:

1. **`Register`**: The plugin registers itself with the kubelet, advertising its resource name (e.g., `nvidia.com/gpu`)
2. **`ListAndWatch`**: The plugin continuously reports the list of available devices and their health status to the kubelet
3. **`Allocate`**: When a Pod requests a GPU, the kubelet calls `Allocate`, and the plugin returns the device paths (`/dev/nvidia0`), environment variables (`CUDA_VISIBLE_DEVICES`), and mount points to inject into the container

The lifecycle: Registration -> continuous health reporting -> allocation on Pod scheduling -> deallocation on Pod termination.
</details>

### Question 2
Why can't you request 0.5 GPUs in a standard Kubernetes Pod spec?

<details>
<summary>Show Answer</summary>

Extended resources (like `nvidia.com/gpu`) only support **integer quantities** in Kubernetes. The Device Plugin API allocates whole devices. This is by design — the API was created for discrete hardware devices where fractional allocation requires hardware-level support (like MIG) or software-level sharing (like time-slicing).

To share GPUs, you need additional mechanisms covered in Module 1.2: MIG partitioning, time-slicing, MPS, or Dynamic Resource Allocation (DRA).
</details>

### Question 3
What is the role of NFD in a GPU cluster, and why shouldn't you manually label GPU nodes?

<details>
<summary>Show Answer</summary>

Node Feature Discovery (NFD) automatically detects hardware features (GPU model, count, memory, CUDA version, MIG capability) and applies labels to nodes. Combined with GPU Feature Discovery, it provides labels like `nvidia.com/gpu.product=NVIDIA-A100-SXM4-80GB`.

Manual labeling should be avoided because:
- It doesn't scale — new nodes need manual intervention
- Labels drift when hardware changes (e.g., failed GPU replaced with different model)
- Human error leads to misscheduled workloads
- NFD re-detects on every node restart, keeping labels accurate
</details>

### Question 4
A Pod using `nvidia.com/gpu: 1` starts successfully but the training job reports "CUDA out of memory" after 2 minutes. The GPU has 80GB VRAM. What could cause this?

<details>
<summary>Show Answer</summary>

Several possible causes:

1. **Another process on the same GPU**: If time-slicing is enabled, multiple containers share the same GPU memory. The Pod may have the GPU but shares VRAM with other workloads.
2. **VRAM fragmentation**: The model fits in 80GB total, but memory fragmentation prevents allocating a contiguous block. Setting `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` can help.
3. **The model is larger than expected**: Mixed precision was not enabled, so the model uses FP32 instead of FP16/BF16, doubling memory usage.
4. **Driver memory overhead**: The NVIDIA driver and CUDA context consume 500MB-2GB of VRAM before your code runs.

Check with `nvidia-smi` inside the container to see actual memory allocation at the time of the OOM.
</details>

### Question 5
What is Xid error 79 and how should a platform team handle it?

<details>
<summary>Show Answer</summary>

Xid 79 means **"GPU has fallen off the bus"** — the GPU is no longer reachable via PCIe. This is a hardware-level failure that typically requires a node reboot.

A platform team should:
1. **Alert** on `DCGM_FI_DEV_XID_ERRORS == 79` immediately (severity: critical)
2. **Automatically drain** the node (`kubectl drain --ignore-daemonsets --delete-emptydir-data`)
3. **Reboot** the node (via IPMI/BMC or cloud API)
4. **Verify** GPU health after reboot with `nvidia-smi` and a CUDA validation test
5. **Track frequency** — if a node hits Xid 79 more than 3 times in a month, escalate to hardware replacement
</details>

---

## Hands-On Exercise: GPU Operator Installation with DCGM Metrics

### Objective

Install the NVIDIA GPU Operator on a Kubernetes cluster, run a GPU workload, and verify that DCGM metrics are scraped by Prometheus.

### Environment Setup

You need a Kubernetes cluster with at least one GPU node. Options:

- **Cloud**: GKE with `nvidia-tesla-t4` accelerator, EKS with `g4dn.xlarge`, AKS with `Standard_NC4as_T4_v3`
- **On-prem**: Any node with an NVIDIA GPU (driver installed or not — the Operator handles drivers)
- **Local**: Not practical — kind/minikube cannot access host GPUs without passthrough

```bash
# Verify you have a GPU node (look for NVIDIA PCI device)
kubectl get nodes -o wide
kubectl debug node/<gpu-node-name> -it --image=ubuntu -- lspci | grep -i nvidia
```

### Step 1: Install Prometheus Stack (if not present)

```bash
# Install kube-prometheus-stack for Prometheus + Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=kubedojo \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

### Step 2: Install the GPU Operator

```bash
# Add NVIDIA Helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install GPU Operator with DCGM-Exporter ServiceMonitor enabled
helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --version v24.9.0 \
  --set dcgmExporter.serviceMonitor.enabled=true \
  --set dcgmExporter.serviceMonitor.additionalLabels.release=kube-prometheus

# Wait for all pods to be ready (this takes 5-10 minutes)
kubectl -n gpu-operator wait --for=condition=Ready pods --all --timeout=600s
```

### Step 3: Verify GPU Resources

```bash
# Check that GPU resources are advertised
kubectl get nodes -o json | jq '.items[] | select(.status.capacity["nvidia.com/gpu"] != null) | {name: .metadata.name, gpus: .status.capacity["nvidia.com/gpu"], gpu_allocatable: .status.allocatable["nvidia.com/gpu"]}'

# Check GPU labels from NFD
kubectl get nodes --show-labels | grep nvidia
```

### Step 4: Run a GPU Workload

```bash
# Create a namespace for experiments
kubectl create namespace ai-lab

# Run a CUDA benchmark that exercises the GPU
cat <<'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: gpu-burn-test
  namespace: ai-lab
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: gpu-burn
          image: nvcr.io/nvidia/k8s/cuda-sample:nbody-cuda12.5.0
          args: ["-benchmark", "-numbodies=1024000", "-iterations=50"]
          resources:
            limits:
              nvidia.com/gpu: 1
  backoffLimit: 0
EOF

# Watch the job
kubectl -n ai-lab logs -f job/gpu-burn-test
```

### Step 5: Verify DCGM Metrics in Prometheus

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-prometheus 9090:9090 &

# Query DCGM metrics (wait 2-3 minutes for first scrape)
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL' | jq '.data.result[] | {gpu: .metric.gpu, node: .metric.node, utilization: .value[1]}'

# Check memory usage
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_FB_USED' | jq '.data.result[] | {gpu: .metric.gpu, node: .metric.node, vram_used_mib: .value[1]}'

# Check temperature
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_DEV_GPU_TEMP' | jq '.data.result[] | {gpu: .metric.gpu, temp_celsius: .value[1]}'
```

### Step 6: Import Grafana Dashboard

```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &

# Login: admin / kubedojo
# Import dashboard ID 12239 (NVIDIA DCGM Exporter Dashboard)
# Or use the API:
curl -X POST http://admin:kubedojo@localhost:3000/api/dashboards/import \
  -H 'Content-Type: application/json' \
  -d '{
    "dashboard": {"id": 12239},
    "overwrite": true,
    "inputs": [{"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": "Prometheus"}],
    "folderId": 0
  }'
```

### Step 7: Cleanup

```bash
kubectl delete namespace ai-lab
# Only if you want to remove the GPU Operator:
# helm uninstall gpu-operator -n gpu-operator
```

### Success Criteria

You have completed this exercise when you can verify:
- [ ] GPU Operator pods are all Running/Completed in `gpu-operator` namespace (9+ pods)
- [ ] `nvidia.com/gpu` appears in `kubectl describe node` output
- [ ] A CUDA test Pod runs and prints "Test PASSED" or produces benchmark output
- [ ] `DCGM_FI_DEV_GPU_UTIL` metric returns data in Prometheus
- [ ] `DCGM_FI_DEV_GPU_TEMP` metric returns data in Prometheus
- [ ] `DCGM_FI_DEV_FB_USED` metric returns data in Prometheus
- [ ] Grafana dashboard shows GPU utilization graph for the benchmark job

---

## Key Takeaways

1. **GPUs are not native to Kubernetes** — the Device Plugin API bridges this gap by advertising GPU resources to the kubelet and injecting device access into containers
2. **The GPU Operator is the standard way to manage NVIDIA GPUs** on Kubernetes — it handles drivers, toolkit, device plugin, metrics, and discovery as a single lifecycle
3. **NFD + GPU Feature Discovery** replace manual node labeling with automatic hardware detection, enabling precise scheduling across heterogeneous GPU fleets
4. **nvidia-container-toolkit** is the invisible layer that makes containers GPU-aware by mounting drivers and creating device nodes at runtime
5. **DCGM-Exporter is non-negotiable** — without GPU metrics in Prometheus, you cannot detect idle GPUs, thermal throttling, hardware errors, or memory pressure
6. **GPU resources use `limits` only** and must be whole integers — fractional sharing requires the techniques covered in Module 1.2

---

## Further Reading

**Documentation**:
- **NVIDIA GPU Operator**: docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/
- **Kubernetes Device Plugin API**: kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/
- **DCGM User Guide**: docs.nvidia.com/datacenter/dcgm/latest/user-guide/

**Talks**:
- **"GPUs in Kubernetes at Scale"** — Kevin Klues, NVIDIA, KubeCon EU 2024
- **"GPU Operator Deep Dive"** — Pramod Ramarao, NVIDIA, KubeCon NA 2023

**Tools**:
- **nvtop**: An htop-like GPU monitor (github.com/Syllo/nvtop)
- **nvidia-smi**: The essential GPU CLI tool bundled with every NVIDIA driver

---

## Summary

GPU provisioning on Kubernetes is a multi-layered problem: drivers, container integration, device advertisement, scheduling, and monitoring. The NVIDIA GPU Operator packages these layers into a manageable whole, while DCGM-Exporter provides the visibility needed to avoid wasting these expensive resources. Master this stack, and you have the foundation for everything else in the AI infrastructure discipline.

---

## Next Module

Continue to [Module 1.2: Advanced GPU Scheduling & Sharing](../module-1.2-gpu-scheduling/) to learn how to share GPUs across workloads using MIG, time-slicing, MPS, and Dynamic Resource Allocation.

---

*"The most expensive GPU is the one doing nothing."* — Every platform engineer who has seen the cloud bill

---
title: "Module 1.1: GPU Provisioning & Device Plugins"
slug: platform/disciplines/data-ai/ai-infrastructure/module-1.1-gpu-provisioning
sidebar:
  order: 2
revision_pending: false
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 3 hours
>
> **Prerequisites**: Kubernetes administration experience with Deployments, DaemonSets, RBAC, and Helm; basic Linux hardware awareness including PCI devices, drivers, and kernel modules; recommended familiarity with observability pipelines; access to at least one NVIDIA GPU node if you want to run every command.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Diagnose** why a Kubernetes node with physical GPUs is not advertising `nvidia.com/gpu` capacity to the scheduler.
- **Implement** a GPU Operator installation that includes drivers, container runtime integration, device plugins, discovery labels, and DCGM metrics.
- **Design** GPU node selection rules that place AI workloads on appropriate hardware without depending on manual labels.
- **Evaluate** GPU provisioning strategies for cost, reliability, observability, and workload fit across training and inference use cases.
- **Debug** common GPU workload failures involving CUDA compatibility, missing runtime injection, Xid errors, and idle expensive capacity.

## Why This Module Matters

Hypothetical scenario: a data science team has reserved a short window on a cluster with eight premium GPU nodes. Their training job is ready, the dataset is staged, and the business stakeholders expect results in the morning. The Pod stays `Pending` because Kubernetes sees ordinary CPU and memory capacity but no `nvidia.com/gpu` resource, while the cloud bill continues to run because the nodes are already provisioned. The immediate symptom looks like scheduling, but the actual fault could live in the host driver, the container runtime, the device plugin, a node label, or the monitoring path that should have caught the idle hardware earlier.

That scenario is common because Kubernetes did not grow up with accelerators as native resources. CPU and memory are part of the kubelet's core accounting model, while GPUs enter the cluster through extension points, vendor drivers, runtime hooks, and health-reporting daemons. The platform engineer's job is to turn that layered stack into a boring service: workloads ask for a GPU, the scheduler finds the right node, the container receives only the devices it was allocated, and the monitoring system shows whether the expensive hardware is actually doing useful work.

This module teaches the provisioning layer that makes the rest of an AI platform possible on Kubernetes 1.35 and newer. You will trace how physical NVIDIA devices become schedulable extended resources, how the NVIDIA GPU Operator assembles the required DaemonSets, how Node Feature Discovery turns hardware facts into scheduling labels, and how DCGM-Exporter gives Prometheus enough signal to catch waste and hardware trouble. Later modules build on this foundation with advanced sharing, distributed training, model serving, and cost-aware autoscaling, so the goal here is not memorizing commands; the goal is learning where each layer starts, where it stops, and how to prove it is working.

## The GPU Provisioning Model in Kubernetes

GPUs are specialized processors with their own memory, driver stack, failure modes, and scheduling constraints. Kubernetes can divide CPU time into millicores because the operating system kernel already knows how to schedule CPU execution among many processes, but a GPU is not automatically safe to overcommit in the same way. A Pod that receives a full GPU usually receives a discrete hardware device with dedicated VRAM, and anything more subtle than whole-device allocation requires deliberate technologies such as MIG, time-slicing, MPS, or Dynamic Resource Allocation, which are covered after this introductory provisioning module.

The first operational mistake is treating GPU provisioning as a single installation step. A working cluster needs the host kernel module, user-space CUDA libraries, a container runtime integration layer, a Kubernetes device plugin, discovery labels, monitoring exporters, and workload manifests that request the resource correctly. If any layer is missing, the failure usually appears somewhere else; for example, a container may start but fail to find `/dev/nvidia0`, or a scheduler may reject a Pod even though `lspci` proves the node contains an NVIDIA device.

| Property | CPU | GPU |
|----------|-----|-----|
| Sharing model | Time-slicing built into OS | Requires explicit configuration |
| Memory | Shared system RAM, overcommittable | Dedicated VRAM, not overcommittable by default |
| Driver | Kernel built-in | Proprietary, version-sensitive |
| Kubernetes awareness | Native | Via Device Plugin API |
| Failure mode | Graceful degradation | Hard crash (OOM, Xid errors) |

The stack is easiest to reason about from the workload downward. A PyTorch or TensorFlow process calls CUDA libraries inside the container, those libraries talk through NVIDIA user-space components that must match the host driver contract, the container runtime exposes device files and libraries, and the kubelet allows that only after a device plugin has allocated a specific GPU to the container. When you debug, work in the opposite direction: prove the node sees the hardware, prove the driver is loaded, prove the plugin reports healthy devices, prove Kubernetes advertises capacity, and only then debug the application.

```mermaid
flowchart TD
    A[User Pod <br/> PyTorch, TensorFlow] --> B[CUDA Libraries <br/> libcuda, cuDNN]
    B --> C[nvidia-container-toolkit <br/> libnvidia]
    C --> D[Container Runtime <br/> containerd]
    D --> E[NVIDIA Device Plugin <br/> DaemonSet]
    E --> F[NVIDIA Driver <br/> kernel module]
    F --> G[Linux Kernel]
    G --> H[Physical GPU <br/> PCIe / NVLink]
```

Pause and predict: if a CUDA sample image works on one GPU node but the same image fails on a newly added node, which layer would you inspect first, and what evidence would convince you that the problem is below Kubernetes rather than inside the Pod spec? A strong answer starts with host-level driver and PCI evidence, then moves upward toward the device plugin and runtime injection path. The key habit is avoiding a blind restart loop; restarts only help when you know which layer is stale or unhealthy.

Cloud instance selection adds another dimension because the hardware shape controls both performance and blast radius. A single modest inference Pod may need a T4 or L4 class accelerator, while a large training job may require A100 or H100 capacity with high-bandwidth interconnects and enough host CPU to feed the GPUs. Platform teams should encode those decisions as node pools, labels, taints, and quotas rather than asking every data scientist to know cloud SKU details. The Kubernetes API should expose a clean resource request, while the platform layer maps that request to reliable hardware.

There is also a social contract hidden inside provisioning. When a user writes `nvidia.com/gpu: 1`, they usually expect a working accelerator, not a research assignment about kernel modules, device files, and driver ABI compatibility. The platform team can honor that expectation only by treating the GPU stack as a product surface with version policy, health checks, ownership labels, and documented failure modes. If the stack is assembled manually by whoever first needed it, the next team will inherit a fragile bundle of node-specific assumptions that no one can confidently upgrade.

Think of a GPU node as a small hardware appliance inside your cluster rather than as a slightly larger CPU node. It has scarce inventory, high replacement cost, thermal constraints, specialized firmware and driver dependencies, and workloads that can waste hours before failing. That appliance model changes operational priorities: capacity planning must include lead time, monitoring must include physical health, scheduling must prevent accidental use, and incident response must know when to restart a Pod versus when to remove a node from service.

## Device Plugins, Extended Resources, and Workload Requests

The Kubernetes Device Plugin API is the bridge between the kubelet and hardware that Kubernetes does not manage natively. The device plugin is a gRPC server, commonly deployed as a DaemonSet, that registers with the kubelet over a Unix domain socket and streams the list of available devices. Once the kubelet trusts that stream, it exposes a vendor-scoped extended resource such as `nvidia.com/gpu` in node capacity and allocatable fields, and the scheduler can place Pods that request the resource.

The important design decision is that the kubelet remains generic. It does not need proprietary NVIDIA logic compiled into Kubernetes, and it does not need to understand every possible accelerator vendor. Instead, the plugin owns discovery, health, and allocation details, while the kubelet owns resource accounting and container admission. That separation is powerful, but it also means a broken plugin can make a perfectly healthy physical GPU disappear from Kubernetes scheduling.

```mermaid
sequenceDiagram
    participant Plugin as Device Plugin (gRPC server)
    participant Kubelet as Kubelet
    Plugin->>Kubelet: Register
    Kubelet->>Plugin: ListAndWatch
    Plugin-->>Kubelet: DeviceList
    Kubelet->>Plugin: Allocate()
    Plugin-->>Kubelet: Devices, Envs
```

The `Register` call tells kubelet which resource name the plugin provides, and `ListAndWatch` is the ongoing inventory and health feed. When a Pod requesting `nvidia.com/gpu: 1` is assigned to the node, kubelet calls `Allocate`, and the plugin returns enough information for the runtime to expose device files, environment variables, and mounts. If a node shows no GPU capacity, focus on registration and `ListAndWatch`; if capacity exists but containers cannot use CUDA, focus on allocation and runtime injection.

```bash
kubectl describe node gpu-worker-01 | grep -A 6 "Capacity:"
```

```text
Capacity:
  cpu:                64
  memory:             256Gi
  nvidia.com/gpu:     4
Allocatable:
  cpu:                63500m
  memory:             254Gi
  nvidia.com/gpu:     4
```

GPU resource requests also surprise teams because extended resources are requested through `limits`. For extended resources, Kubernetes requires the request and limit to be equal; if you specify only a limit, the request is defaulted to that same value. In normal manifests, write the GPU quantity under `resources.limits`, use a whole integer, and avoid implying fractional sharing unless your cluster has a configured sharing layer that advertises separate resource names or partitioned devices.

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

There are three rules worth making automatic in code review. First, a Pod cannot consume GPUs from multiple nodes, so distributed jobs need framework-level coordination rather than a larger single-Pod request. Second, a standard `nvidia.com/gpu` request is whole-device accounting, so `0.5` is invalid even when the workload's actual utilization is low. Third, node capacity is not enough; the Pod must also tolerate the GPU node taints and match any labels or affinity rules your platform uses to separate GPU families.

Before running this, what output do you expect from `kubectl describe node` on a healthy GPU node after the plugin registers? You should expect both `Capacity` and `Allocatable` to contain the same `nvidia.com/gpu` count unless something else has already reserved or consumed devices. If the resource exists in capacity but not allocatable, inspect kubelet health, plugin logs, and node conditions before blaming the workload.

A useful diagnostic shortcut is to separate "Kubernetes cannot see the GPU" from "the container cannot use the GPU." If `kubectl describe node` lacks `nvidia.com/gpu`, the failure is before scheduling: driver, plugin, kubelet registration, or plugin health reporting. If the node advertises capacity and the Pod schedules, but CUDA cannot initialize inside the container, the failure is after allocation: runtime injection, library compatibility, device node visibility, or image contents. This split keeps troubleshooting focused and prevents application teams from rewriting manifests that were already correct.

Resource accounting also affects fairness. Without namespace quotas or admission policy, a single user can submit several one-GPU Jobs and consume the entire accelerator pool even if each Job is idle most of the time. GPU quotas should be aligned with organizational ownership and workload class, not just namespace convenience, because accelerator capacity is usually purchased for specific business priorities. Pair quotas with clear denial messages so users understand whether they need a different queue, a smaller accelerator, or an approval path for temporary burst capacity.

## Discovery Labels and Container Runtime Integration

Scheduling a GPU Pod to any node with `nvidia.com/gpu` is rarely good enough. In a mixed fleet, a T4 inference node, an A100 training node, and an H100 high-end training node all expose the same basic resource name unless you add more information. Node Feature Discovery solves the scaling problem by detecting hardware and kernel features on each node and publishing them as labels, while GPU Feature Discovery adds NVIDIA-specific facts such as product, memory, count, driver, and MIG capability.

Manual labels are tempting during the first lab because they are fast, visible, and easy to understand. They become dangerous when nodes are replaced, images are rebuilt, autoscalers create fresh nodes, or hardware revisions change under an existing node pool name. A stale label can strand expensive jobs in `Pending` or, worse, schedule a model onto a smaller GPU where it fails after downloading data and initializing the training loop. Discovery labels let the platform treat hardware facts as measured state rather than tribal knowledge.

```bash
# NFD automatically adds labels like:
feature.node.kubernetes.io/pci-10de.present=true        # NVIDIA PCI device
feature.node.kubernetes.io/cpu-model.vendor_id=Intel
feature.node.kubernetes.io/kernel-version.major=5
```

```bash
nvidia.com/gpu.product=NVIDIA-A100-SXM4-80GB
nvidia.com/gpu.memory=81920
nvidia.com/gpu.count=8
nvidia.com/gpu.machine=DGX-A100
nvidia.com/cuda.driver.major=535
nvidia.com/mig.capable=true
```

Those labels become the vocabulary for safe placement. A large model that expects 80 GiB of VRAM should not land on a smaller card simply because both nodes report one GPU. Use required node affinity when the workload truly cannot run elsewhere, and prefer a higher-level scheduling abstraction or platform template when you want users to choose intent, such as `training-large` or `inference-small`, without copying hardware product names into every manifest.

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

The other half of the story is container runtime integration. Even after Kubernetes assigns a GPU to a Pod, a Linux container does not magically gain access to physical device files or host driver libraries. The NVIDIA Container Toolkit integrates with containerd or CRI-O so the runtime can create `/dev/nvidia*` device nodes, mount compatible libraries, and set environment variables such as `NVIDIA_VISIBLE_DEVICES` and `CUDA_VISIBLE_DEVICES` for the allocated GPU.

```mermaid
flowchart TD
    A[Pod created] --> B[kubelet calls containerd]
    B --> C[containerd invokes nvidia-container-runtime-hook]
    C --> D[Hook calls libnvidia-container]
    D --> E["libnvidia-container: <br/> - Discovers host GPU driver <br/> - Mounts /usr/lib/x86_64-linux-gnu/libnvidia-*.so <br/> - Creates /dev/nvidia* device nodes <br/> - Sets CUDA_VISIBLE_DEVICES"]
    E --> F[Container starts with GPU access]
```

Modern deployments increasingly use Container Device Interface mode because CDI describes devices in runtime-readable specification files rather than relying on older hook behavior. The operational benefit is simpler integration across runtimes and less hidden mutation at container start. The tradeoff is that your driver, toolkit, runtime, and device plugin versions must be aligned well enough for CDI generation and consumption to agree, so version pinning and upgrade testing matter.

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

Which approach would you choose here and why: one generic GPU node pool with labels, or separate node pools for each accelerator family? A small platform can begin with one pool and strict labels, but production teams usually separate families because autoscaling, quotas, driver lifecycle, and cost attribution become clearer. The right design depends on whether your primary failure risk is underutilization, accidental misplacement, or operational drift during upgrades.

Taints and tolerations complete the scheduling boundary. Labels attract the right workloads to GPU nodes, while taints repel ordinary workloads that do not explicitly declare they belong there. This distinction matters because a CPU-only batch job can consume memory, local disk, network bandwidth, or Pod slots on a costly accelerator node even though it never asks for a GPU. A good baseline is to taint GPU pools with a key such as `accelerator=nvidia:NoSchedule`, then provide a platform-approved workload template that includes the matching toleration only for jobs that request GPU resources.

Runtime classes can also be useful when the cluster supports multiple container runtime configurations. Some environments define a runtime class for NVIDIA-aware execution, while others rely on CDI and default runtime behavior. Whichever path you choose, document it in terms a workload owner can test: "a Pod requesting one GPU should see exactly one device through `nvidia-smi` and should not require privileged mode." Privileged containers are a warning sign in this context because the device plugin and runtime integration are supposed to provide constrained access without handing the application broad host control.

## Installing and Verifying the NVIDIA GPU Operator

The NVIDIA GPU Operator exists because installing GPUs manually requires coordinating too many moving parts across every GPU node. You need the driver DaemonSet when the host image does not already include a supported driver, the container toolkit DaemonSet for runtime integration, the device plugin DaemonSet for extended resources, DCGM-Exporter for metrics, Node Feature Discovery for labels, and GPU Feature Discovery for NVIDIA-specific labels. Installing those components one by one is possible, but operating them as separate lifecycles increases the odds of a version mismatch or partial rollout.

The Operator packages that stack behind a Helm chart and a `ClusterPolicy` custom resource. It is still not magic; it is a controller that creates and reconciles DaemonSets, validators, ConfigMaps, and related objects. Treat it like any other infrastructure controller: pin versions, test upgrades on a small node group, watch its rollout status, and understand which components it manages versus which components are already supplied by your cloud provider or base node image.

```mermaid
flowchart TD
    Controller["GPU Operator Controller <br/> (watches ClusterPolicy CRD)"]
    Controller --> NFD["NFD DaemonSet"]
    Controller --> Driver["Driver DaemonSet"]
    Controller --> Toolkit["Container Toolkit DaemonSet"]
    Controller --> Plugin["Device Plugin DaemonSet"]
    Controller --> DCGM["DCGM Exporter DaemonSet"]
    Controller --> GFD["GPU Feature Discovery DaemonSet"]
```

For a first installation, keep the configuration explicit even when defaults would work. The values below enable the major stack components, turn on DCGM-Exporter, select a MIG strategy, and install NFD. In a managed Kubernetes environment, you may disable driver management if the node image already includes the correct driver, but do that intentionally and document the owner of driver upgrades. Version pins belong in a short-lived release plan, not scattered through teaching prose, because the Operator, driver branch, container toolkit, device plugin, and exporter move on their own release schedules.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> | Volatile item | Verified value | Why it is quarantined |
> |---------------|----------------|-----------------------|
> | GPU Operator Helm chart | `v26.3.2` is the current patch release in the NVIDIA install docs | Chart releases change quickly, and old pins can silently pull unsupported operands |
> | GPU Operator support window | `26.3.x` is supported; `25.10.x` is deprecated; `25.3.x` and older are end of support | Support status changes with the Operator lifecycle rather than with Kubernetes itself |
> | v26.3.2 default or recommended operands | Driver `580.126.20` default, driver `580.159.04` recommended, Container Toolkit `1.19.1`, device plugin and GPU Feature Discovery `0.19.2`, DCGM Exporter `v4.5.3-4.8.2`, Node Feature Discovery `v0.18.3`, MIG Manager `0.14.2` | These are release-matrix facts; let the chart defaults carry them unless your upgrade test plan pins specific operands |
> | H100 power envelope | H100 SXM lists maximum TDP up to `700W`; H100 NVL in PCIe form factor lists `350-400W`, configurable by SKU | Power and cooling plans must use the exact SKU and server BOM, not a generic H100 statement |
> | CUDA sample images used below | `nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda12.5.0` and `nvcr.io/nvidia/k8s/cuda-sample:nbody` resolved with registry manifest inspection | Public sample tags can appear or disappear; production validation should pin a verified digest in your own runbook |

```bash
# Add the NVIDIA Helm repository
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Pin the chart release you have tested; refresh this against NVIDIA docs before reuse.
RELEASE_TAG=v26.3.2

# Install the GPU Operator
helm install gpu-operator nvidia/gpu-operator \
  --wait \
  --namespace gpu-operator \
  --create-namespace \
  --version "${RELEASE_TAG}" \
  --set driver.enabled=true \
  --set toolkit.enabled=true \
  --set dcgmExporter.enabled=true \
  --set mig.strategy=single \
  --set nfd.enabled=true
```

The `ClusterPolicy` is the declarative contract for the Operator. Read it the same way you would read a CNI or storage operator configuration: each field names an operational responsibility that must be owned somewhere. Driver policy controls compatibility with CUDA user-space expectations, toolkit policy controls runtime injection behavior, device plugin policy controls resource advertisement, DCGM policy controls metric availability, and MIG strategy controls whether partitioned GPU instances are exposed in a consistent way across the node. Leave operand versions on the chart's supported defaults unless you have a documented compatibility reason to pin them, and keep any pins in a dated release note that can be refreshed as a unit.

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
    repository: nvcr.io/nvidia
    image: driver
    licensingConfig:
      configMapName: ""
  toolkit:
    enabled: true
  devicePlugin:
    enabled: true
    config:
      name: device-plugin-config
      default: default
  dcgmExporter:
    enabled: true
    serviceMonitor:
      enabled: true         # Create ServiceMonitor for Prometheus
  mig:
    strategy: single        # "single" or "mixed"
  nodeFeatureDiscovery:
    enabled: true
  gfd:
    enabled: true
```

Verification should prove each layer rather than only checking that the Helm release exists. Confirm Operator Pods, validator Pods, driver Pods, toolkit Pods, device plugin Pods, NFD Pods, and DCGM Pods reach the expected state. Then check that node capacity advertises `nvidia.com/gpu`, run a CUDA sample that requests a GPU, and inspect the sample output. That sequence narrows failure quickly: if Pods are unhealthy, fix the Operator rollout; if node capacity is missing, inspect plugin and driver logs; if capacity exists but CUDA fails, inspect toolkit and compatibility.

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
# nvidia-driver-daemonset-<driver-version>-gpu-worker-01  1/1     Running
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

Exercise scenario: imagine a validator Pod completed successfully yesterday, but today a new node group joins and only the driver DaemonSet is failing there. Do not assume the old cluster-wide success applies to new nodes. GPU provisioning is node-local, so every autoscaled or replaced node must satisfy the same driver, runtime, plugin, and monitoring checks before workloads depend on it.

Driver management is the part of the Operator that deserves the most caution. In some clusters, the Operator installs the driver into a generic GPU node image; in others, the cloud provider or image pipeline ships a preinstalled driver and the Operator should not replace it. Both approaches can work, but mixing them accidentally creates confusing ownership. Decide whether your platform owns drivers through the Operator or through node images, then make the other path explicitly disabled. During upgrades, run representative CUDA workloads before rolling across every node pool because driver compatibility failures often show up only when real application images start.

Validation should be repeatable enough to run after scale-out, replacement, and upgrade events. A one-time installation checklist is weaker than a small conformance Job that proves the resource is advertised, the container sees the device, and a CUDA operation completes. Store the exact image tags used for validation because "latest" images can change beneath you and blur whether a failure came from the platform or the test itself. When a new GPU family is introduced, add a validation case for that family rather than assuming the old test covers new memory sizes, compute capability, or MIG behavior.

Operationally, the Operator namespace is a service boundary. Give it the same attention you give networking and storage operators: collect logs, watch DaemonSet rollout status, alert when desired and ready Pods diverge, and require a change plan for version bumps. GPU teams sometimes focus on application dashboards while forgetting that a failed device plugin DaemonSet can remove all scheduling capacity without any model code changing. If your monitoring only watches user namespaces, the root cause will be invisible until users start reporting stuck Jobs.

## Observability, Idle Capacity, and GPU Health

GPU observability is not an optional dashboard project; it is part of provisioning. A cluster that can schedule GPU Pods but cannot show utilization, VRAM pressure, temperatures, power draw, or Xid errors is not production-ready because it cannot distinguish healthy acceleration from expensive idleness. DCGM, the Data Center GPU Manager, exposes low-level NVIDIA telemetry, and DCGM-Exporter turns that telemetry into Prometheus metrics that platform teams can alert on, trend, and use for cost conversations.

GPU utilization needs careful interpretation. A training job may show bursty utilization if input pipelines starve the device, an inference service may deliberately run below peak to preserve latency, and a memory-heavy model may be constrained by VRAM rather than compute. The point is not to punish every low-utilization minute; the point is to make invisible waste visible enough that teams can decide whether to batch, downsize, share, autoscale, or move work to a different accelerator class.

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| `DCGM_FI_DEV_GPU_UTIL` | GPU compute utilization (%) | Is the GPU busy or idle? |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | Memory bandwidth utilization (%) | Data transfer bottleneck? |
| `DCGM_FI_DEV_FB_USED` | Framebuffer memory used (MiB) | How much VRAM is consumed? |
| `DCGM_FI_DEV_FB_FREE` | Framebuffer memory free (MiB) | How much VRAM is available? |
| `DCGM_FI_DEV_GPU_TEMP` | GPU temperature (C) | Thermal throttling? |
| `DCGM_FI_DEV_POWER_USAGE` | Power draw (W) | Energy cost tracking |
| `DCGM_FI_DEV_SM_CLOCK` | Streaming multiprocessor clock (MHz) | Is the GPU at full speed? |
| `DCGM_FI_DEV_XID_ERRORS` | Last Xid error code/value | Hardware or driver fault event? |
| `DCGM_FI_DEV_PCIE_TX_THROUGHPUT` | PCIe TX throughput (KB/s) | Data transfer bottleneck? |
| `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | Ratio of time the GPU was active | More precise than utilization |

DCGM-Exporter can be configured to expose the counters your team actually uses. More metrics are not always better because cardinality, scrape volume, and dashboard noise can hide the signals that matter. Start with utilization, memory, temperature, power, PCIe throughput, the last Xid error code, and profiling engine activity; add specialized counters when you have a concrete question about tensor cores, NVLink, ECC behavior, or application-level performance.

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
    DCGM_FI_DEV_XID_ERRORS,       gauge, Value of the last Xid error.
    DCGM_FI_PROF_GR_ENGINE_ACTIVE, gauge, Ratio of time the graphics engine is active.
    DCGM_FI_PROF_PIPE_TENSOR_ACTIVE, gauge, Ratio of time the tensor cores are active.
```

The original NVIDIA DCGM Grafana dashboard is useful for a first view, but production teams should add panels that map metrics to decisions. Show per-node and per-Pod utilization together, because a node-level graph without workload labels does not tell you who owns the waste. Show VRAM used and free together, because compute utilization alone misses memory-bound failures. Show Xid codes as latest-event signals rather than counters or rates, because one severe hardware fault deserves immediate investigation even when an aggregate dashboard looks quiet.

```mermaid
xychart-beta
    title "Per-GPU Utilization Timeline (%)"
    x-axis ["GPU0", "GPU1", "GPU2", "GPU3"]
    y-axis "Utilization (%)" 0 --> 100
    bar [78, 94, 12, 100]
```

In the chart, GPU2 is the interesting line, not because low utilization is always wrong, but because it is inconsistent with the other devices during what is supposedly a training run. That gap could be input starvation, an imbalanced distributed job, a failed worker, a model shard that is smaller than expected, or accidental placement of a lightweight process on a premium accelerator. A good alert points to investigation, while a good dashboard gives enough context to avoid guessing.

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
            summary: "GPU {{ $labels.gpu }} reported last Xid code {{ $value }} — check dmesg"

        - alert: GPUUnderutilized
          expr: DCGM_FI_DEV_GPU_UTIL < 10
          for: 30m
          labels:
            severity: info
          annotations:
            summary: "GPU {{ $labels.gpu }} has been below 10% utilization for 30m — waste?"
```

Hypothetical scenario: a team reserves a weekend training window and the job exits cleanly on Saturday morning, but the GPU nodes remain attached until Monday because no autoscaler can scale them down and no alert detects sustained idleness. The fix is not a clever invoice spreadsheet after the fact; the fix is a provisioning pattern that combines DCGM utilization alerts, ownership labels, quota boundaries, and autoscaling rules that let unused GPU pools return to zero when no pending GPU Pods exist. Monitoring pays for itself when it changes scheduling and lifecycle behavior.

Cost alerts should be framed as engineering feedback, not blame. Low utilization can be perfectly reasonable for latency-sensitive serving or for a training phase that alternates compute with checkpointing, so the alert should provide context and invite investigation. Useful labels include namespace, workload name, node pool, accelerator product, and team owner. With that context, a platform engineer can ask whether the workload should move to a smaller GPU, use a sharing mode, batch more requests, or keep the current allocation because the business requirement values latency over utilization.

Health alerts need a different posture. Temperature and Xid alerts are not cost optimization signals; they are reliability signals that can threaten correctness, availability, or job progress. The runbook should distinguish transient single samples from persistent or severe faults, but it should also be willing to cordon a node quickly when the hardware path is suspect. Long-running training jobs are expensive to restart, so a conservative node-remediation policy often costs less than repeatedly rescheduling onto a device that is already showing failure symptoms.

The fastest way to connect these concepts is to inspect a GPU container directly. The command below asks Kubernetes for one GPU and then prints the visible NVIDIA state from inside the container. If `nvidia-smi` works and device files appear, runtime injection is working; if the Pod schedules but these are missing, inspect the toolkit and runtime configuration rather than the scheduler.

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

Notice that the container image does not need to contain the host NVIDIA driver. It needs compatible user-space CUDA components, while the runtime injects the host driver libraries and device nodes needed to talk to the allocated GPU. That distinction is why CUDA compatibility matrices matter during upgrades: the image, host driver, and runtime layer must agree on a supported contract, even though they are delivered by different teams and artifacts.

This is also why base image governance matters in AI platforms. If every team builds from a different CUDA image tag, the platform team must test a wide compatibility surface for every driver change. A curated set of approved base images reduces that surface while still giving users enough flexibility for PyTorch, TensorFlow, JAX, and custom native extensions. The goal is not to centralize all model code; it is to centralize the fragile boundary where application dependencies meet host driver policy.

## Patterns & Anti-Patterns

GPU provisioning patterns are mostly about making the invisible parts explicit. The platform should know which component owns drivers, which labels define placement, which metrics prove utilization, and which guardrails prevent users from accidentally consuming scarce accelerators. A working demo can survive with manual steps; a shared AI platform needs repeatable patterns because GPUs are too expensive for informal operations.

| Pattern | When to Use | Why It Works | Scaling Consideration |
|---------|-------------|--------------|-----------------------|
| Operator-managed GPU stack | You need consistent driver, toolkit, plugin, discovery, and metrics lifecycle across many nodes | The Operator reconciles the components as a declared cluster policy instead of relying on runbooks | Pin versions and test upgrades on one node group before rolling fleet-wide |
| Hardware labels from NFD and GPU Feature Discovery | Your cluster has mixed GPU generations, memory sizes, or MIG capability | Scheduling decisions follow detected hardware facts instead of manual labels | Standardize workload templates so users choose intent rather than raw product labels |
| DCGM metrics tied to ownership labels | You need to control idle cost and hardware health | Metrics become actionable when they identify node, GPU, namespace, and workload owner | Keep cardinality under control and alert on sustained conditions rather than noisy samples |
| Dedicated GPU node pools with taints | GPU capacity is scarce or expensive compared with general compute | Taints keep ordinary Pods off accelerator nodes and make cost boundaries visible | Combine with quotas and autoscaling so unused pools can shrink safely |

Anti-patterns usually come from trying to make GPUs look simpler than they are. Teams either hide too much behind a single generic resource name, or they expose every hardware detail directly to every user. The better path is a platform contract that is honest about constraints while still shielding most application teams from low-level driver and SKU decisions.

| Anti-pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|-------------------|
| Treating `nvidia.com/gpu` as the only placement signal | Workloads land on the wrong accelerator family and fail late or run inefficiently | Use discovery labels, affinity templates, or higher-level workload classes |
| Upgrading drivers without CUDA compatibility review | Containers that worked yesterday fail with driver or kernel image errors | Test representative CUDA images against the target driver before rollout |
| Installing the device plugin but skipping runtime integration | Nodes advertise GPUs, but containers cannot access `/dev/nvidia*` or driver libraries | Install and validate the NVIDIA Container Toolkit or CDI path as part of the same change |
| Alerting only on node readiness | Hardware faults and idle accelerators remain invisible while Kubernetes looks healthy | Alert on DCGM temperature, Xid errors, utilization, memory pressure, and exporter availability |

One useful mental model is a four-part contract: discovery tells Kubernetes what exists, allocation tells kubelet what a Pod receives, injection makes the device usable inside the container, and telemetry proves the device remains useful after start. If your platform design cannot name the component responsible for each part, it is not ready for production GPU workloads. This contract also gives you a practical review checklist for manifests, Helm values, and incident runbooks.

Another pattern is to separate experimentation from production serving at the namespace, quota, and node-pool level. Experiments benefit from flexible scheduling, burst capacity, and quick cleanup, while serving workloads need predictable availability and carefully managed upgrades. When both classes share the same pool without policy, experiments can starve serving, and serving can pin capacity that experiments assume will scale down. The separation does not require separate clusters in every organization, but it does require explicit resource boundaries and dashboards that show which class is consuming each accelerator.

Finally, make failure drills part of the platform lifecycle. Simulate a missing toleration, a broken affinity label, a disabled device plugin, and an unreachable DCGM exporter in a non-production environment. These drills teach the team which symptoms appear at scheduling time, container start time, and monitoring time. They also reveal whether runbooks contain enough concrete commands for an engineer who did not build the platform to diagnose the issue under pressure.

## Decision Framework

GPU provisioning decisions should begin with the workload's bottleneck, not the cloud provider's instance catalog. Training jobs may need high VRAM, fast interconnects, and long uninterrupted runs, while inference services may need lower latency, smaller accelerators, or the ability to scale horizontally. Batch experiments may tolerate preemption, but model serving usually needs predictable availability. The platform's job is to translate those needs into node pools, labels, taints, quotas, monitoring, and lifecycle automation.

```mermaid
flowchart TD
    A[Start with workload need] --> B{Needs GPU?}
    B -- No --> C[Use general compute pool]
    B -- Yes --> D{Memory-bound model?}
    D -- Yes --> E[Select high-VRAM GPU family and enforce product or memory labels]
    D -- No --> F{Latency-sensitive inference?}
    F -- Yes --> G[Use dedicated inference pool with quotas, metrics, and autoscaling]
    F -- No --> H{Large training or distributed job?}
    H -- Yes --> I[Use training pool with compatible accelerator family and topology awareness]
    H -- No --> J[Use shared or smaller GPU pool, then monitor utilization]
```

The first branch protects the cluster from accidental GPU consumption. If a workload can run on CPU during development, keep that path available so early tests do not tie up expensive accelerators. The second branch separates memory constraints from compute constraints because VRAM exhaustion is one of the fastest ways to waste time: a model that cannot fit will fail regardless of how much aggregate cluster capacity exists. The third branch separates serving from training because availability and scaling patterns differ.

| Decision | Choose This When | Avoid This When | Evidence to Collect |
|----------|------------------|-----------------|---------------------|
| Operator-managed drivers | You own the node image or need consistent fleet upgrades | A managed service already supplies and tests the driver stack | Operator rollout status, driver Pod logs, CUDA validation output |
| Pre-baked driver node image | Startup time and immutable infrastructure matter more than in-cluster driver rollout | You need frequent driver changes without rebuilding images | Image build provenance, `nvidia-smi`, driver compatibility tests |
| Required node affinity | The workload only runs on specific GPU families or memory sizes | A fallback accelerator is acceptable and cost-effective | NFD labels, model memory profile, benchmark results |
| GPU taints plus tolerations | You must keep ordinary Pods away from costly nodes | GPU nodes are dedicated by separate clusters or hard isolation | Pending Pod events, node utilization, quota reports |
| DCGM alerting at provisioning time | Any production GPU workload will run in the cluster | The cluster is a short-lived throwaway lab | Prometheus targets, DCGM metric samples, alert rule tests |

Use this framework during design reviews. Ask whether the workload can tolerate a smaller GPU, whether it needs a specific CUDA capability, whether the node pool can scale down, how ownership is recorded, and how a device fault will be remediated. A GPU platform is mature when these questions have boring answers in manifests, dashboards, and runbooks rather than in one engineer's memory.

For early platforms, the most pragmatic default is conservative isolation with strong observability. Give expensive accelerator families their own node pools, taint those pools, require explicit GPU requests, install the Operator with DCGM enabled, and expose a small number of approved workload templates. Once you have utilization data and user demand patterns, you can introduce more advanced sharing and autoscaling. Starting with aggressive sharing before you have metrics usually hides the very signals you need to decide whether sharing is safe.

For mature platforms, the decision framework should feed a service catalog. Users should be able to choose something like "small inference GPU," "large training GPU," or "partitioned development GPU" and receive the right tolerations, affinity, resource requests, and monitoring labels automatically. The catalog can still compile down to ordinary Kubernetes manifests, but it prevents every team from rediscovering the same placement rules. This is the difference between allowing GPUs in a cluster and offering GPU infrastructure as a platform capability.

## Did You Know?

1. **H100 power and cooling plans are SKU-specific, not generic.** A high-density SXM accelerator and a PCIe-form-factor H100 NVL do not have the same thermal design target, so use the dated hardware snapshot and your vendor BOM before sizing rack power, cooling, or autoscaling boundaries.

2. **The Kubernetes Device Plugin API became stable in Kubernetes 1.26, but the operational pattern remains important in Kubernetes 1.35 and newer.** Stability means the API contract is mature; it does not mean every vendor plugin, driver version, and runtime integration is interchangeable without testing.

3. **Xid errors are NVIDIA driver-reported hardware or driver fault events, and some values indicate severe device loss.** When a GPU falls off the PCIe bus, restarting the application container is usually not enough; the node often needs cordon, drain, and reboot or hardware investigation.

4. **DCGM-Exporter can expose both coarse utilization counters and profiling counters such as graphics engine or tensor activity.** That distinction matters because a GPU can look partly busy while the model is still bottlenecked on input pipelines, memory transfers, or uneven work distribution.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Requesting GPUs in `requests` only | Engineers copy CPU and memory patterns and forget that extended resources are handled as whole, non-overcommitted limits | Put `nvidia.com/gpu` under `resources.limits` and review manifests for integer quantities |
| Mismatching CUDA image and host driver compatibility | Application teams choose a CUDA image independently from the platform driver lifecycle | Maintain a tested compatibility matrix for approved base images and driver versions |
| Installing the device plugin without validating runtime injection | The scheduler path is visible first, so teams stop once nodes advertise capacity | Run a CUDA validation Pod and inspect `/dev/nvidia*`, `CUDA_VISIBLE_DEVICES`, and `nvidia-smi` inside the container |
| Manually labeling GPU nodes | Manual labels work in small static labs but drift when nodes are replaced or autoscaled | Use Node Feature Discovery and GPU Feature Discovery as the source of scheduling labels |
| Ignoring Xid errors after Pods restart | Kubernetes may make the Pod look recovered while the underlying device remains unstable | Alert on `DCGM_FI_DEV_XID_ERRORS`, cordon suspect nodes, and require hardware-level remediation for recurring faults |
| Deploying GPU capacity without DCGM metrics | The initial goal is often "make the Pod run," so utilization and health are delayed | Treat DCGM-Exporter and Prometheus targets as part of the provisioning definition of done |
| Letting ordinary workloads run on GPU nodes | Missing taints allow CPU-only Pods to consume memory, network, and scheduling space on costly nodes | Taint GPU pools, require explicit tolerations, and enforce namespace quotas for accelerator usage |

## Quiz

<details>
<summary>Question 1: A Pod is stuck in `Pending` with `Insufficient nvidia.com/gpu`, but `lspci` on the node shows NVIDIA hardware and the driver is loaded. Which layer do you inspect first, and why?</summary>

Inspect the NVIDIA device plugin registration and `ListAndWatch` path first, especially the device plugin DaemonSet logs and kubelet device plugin socket directory. The scheduler can only consider `nvidia.com/gpu` after kubelet reports that extended resource in node capacity, and kubelet learns that from the plugin rather than from PCI directly. Driver evidence proves the hardware is visible to Linux, but it does not prove Kubernetes has received a healthy device inventory. If the plugin is failing, the fix is to restore registration and health reporting before changing the workload manifest.
</details>

<details>
<summary>Question 2: A developer requests `nvidia.com/gpu: 0.5` for a lightweight inference Pod and the API rejects the manifest. How do you explain the failure and propose a production-safe alternative?</summary>

The standard extended resource request for `nvidia.com/gpu` represents whole devices, so Kubernetes expects an integer quantity and does not divide the accelerator the way it divides CPU. A production-safe alternative depends on hardware and isolation needs: MIG can expose partitioned GPU instances on supported cards, while time-slicing can improve utilization when weaker isolation is acceptable. The platform should advertise those sharing modes through explicit configuration and documentation rather than letting users invent fractional quantities. The key is to make the sharing boundary visible in scheduling and monitoring.
</details>

<details>
<summary>Question 3: A new autoscaled node group joins with A100 GPUs, but large training jobs using `nvidia.com/gpu.product: NVIDIA-A100-SXM4-80GB` remain pending. What do you check before changing the training manifest?</summary>

Check whether Node Feature Discovery and GPU Feature Discovery ran successfully on the new nodes and applied the expected product labels. The training manifest may be correct if the workload truly requires that accelerator family, while the node state may be incomplete because discovery DaemonSets are unhealthy, taints are missing tolerations, or the new hardware reports a slightly different product string. You should compare labels on old working nodes and new nodes, inspect discovery logs, and confirm GPU capacity exists. Only relax the manifest if the workload can actually run on the reported hardware.
</details>

<details>
<summary>Question 4: A CUDA validation Pod schedules successfully, but `nvidia-smi` inside the container cannot find NVIDIA devices. Which provisioning layer is most suspicious?</summary>

The most suspicious layer is container runtime integration through the NVIDIA Container Toolkit or CDI configuration. Scheduling proves the device plugin advertised capacity and kubelet allocated a GPU, but the container still needs device nodes and driver libraries injected at start. Inspect the toolkit DaemonSet, containerd or CRI-O runtime configuration, generated CDI specs if used, and kubelet allocation logs. Reinstalling the application image is unlikely to help unless the image also lacks compatible CUDA user-space components.
</details>

<details>
<summary>Question 5: DCGM shows one GPU at 12 percent utilization while three peers sit above 75 percent during a supposedly balanced training run. What investigation path gives the highest signal?</summary>

Start by correlating the low-utilization GPU with the owning Pod, process, and training worker rather than treating the node as a single black box. Then inspect application logs, input pipeline throughput, distributed training membership, and VRAM usage to see whether that worker is starved, smaller, failed, or waiting on synchronization. The GPU may be healthy; the anomaly is the mismatch with peer devices under the same job. A useful remediation might be data loading changes, worker restart, job rescheduling, or a training framework fix rather than hardware replacement.
</details>

<details>
<summary>Question 6: An alert fires for `DCGM_FI_DEV_XID_ERRORS` on a node running a critical training job. The Pod restarts, but the alert returns after a few minutes. What should the runbook do?</summary>

The runbook should treat recurring Xid errors as a node or device health problem, not merely an application crash. Cordon the node to stop new GPU placements, drain or reschedule affected workloads according to the job's recovery policy, and collect driver logs and DCGM evidence for hardware analysis. If the error indicates device loss or persists after reboot, mark the node for repair or replacement. Repeated container restarts can hide the hardware fault while wasting training time.
</details>

<details>
<summary>Question 7: A platform team wants to prove its GPU provisioning is production-ready before onboarding model-serving workloads. What evidence should it gather?</summary>

The team should gather evidence across the full contract: node hardware discovery, driver health, device plugin resource advertisement, runtime injection, workload scheduling, and DCGM telemetry. A strong readiness packet includes `kubectl describe node` capacity, successful CUDA validation logs, NFD and GPU labels, toolkit or CDI configuration evidence, Prometheus samples for utilization and health metrics, and alert rules for temperature, Xid errors, and sustained idleness. It should also show taints, tolerations, quotas, and ownership labels so model-serving workloads do not share capacity accidentally. Production readiness is a chain, and every link needs observable proof.
</details>

## Hands-On Exercise

In this exercise, you will install the NVIDIA GPU Operator, run a CUDA workload, and verify that DCGM metrics reach Prometheus. The commands assume a Kubernetes 1.35 or newer cluster with at least one NVIDIA GPU node and Helm installed on your workstation. If you are using a managed cloud GPU node image that already includes drivers, adapt the Operator values deliberately rather than copying `driver.enabled=true` blindly.

Exercise scenario: you are preparing a shared GPU pool for a data science team that will run both validation jobs and early training experiments. Your definition of done is not just a successful Helm release; it is proof that Kubernetes advertises GPU capacity, a workload can use CUDA, and Prometheus receives GPU health and utilization metrics. Keep notes as you go, because those notes become the seed of your production runbook.

### Setup

You need a Kubernetes cluster with at least one GPU node. Cloud options include GKE nodes with NVIDIA accelerators, EKS nodes such as GPU-backed instance families, and AKS GPU virtual machine sizes. On premises, any supported NVIDIA GPU node can work if the driver path is compatible with the Operator strategy. Local clusters are usually poor candidates because kind and minikube cannot access host GPUs without additional passthrough work.

```bash
# Verify you have a GPU node (look for NVIDIA PCI device)
kubectl get nodes -o wide
kubectl debug node/<gpu-node-name> -it --profile=sysadmin --image=ubuntu:24.04 -- bash -lc '
  apt-get update >/dev/null
  apt-get install -y pciutils >/dev/null
  lspci | grep -i nvidia
'
```

The debug command uses the `sysadmin` profile because Kubernetes mounts the node root filesystem at `/host` for node debugging, but the default debug Pod is not privileged enough for every host inspection pattern. Installing `pciutils` inside the temporary Ubuntu debug container makes `lspci` available without assuming the node image already carries that troubleshooting package.

### Task 1: Install Prometheus Stack

Install Prometheus and Grafana if your cluster does not already have them. The important setting here is allowing ServiceMonitors created by other releases to be selected, because the GPU Operator can create a DCGM ServiceMonitor that Prometheus must scrape. In a production cluster, align these values with your monitoring team's release labels and retention settings.

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

<details>
<summary>Solution notes</summary>

The `kube-prometheus-stack` release should create Prometheus, Grafana, Alertmanager, and the CRDs used by `ServiceMonitor` and `PrometheusRule`. If your organization already runs this stack, do not install a second copy; instead, confirm the existing Prometheus instance can discover ServiceMonitors in the `gpu-operator` namespace. The success signal is a healthy Prometheus target list after the DCGM exporter appears later.
</details>

### Task 2: Install the GPU Operator

Install the GPU Operator with DCGM ServiceMonitor creation enabled. The wait command may take several minutes because driver installation and validation are node-local operations, and new GPU nodes need time to converge. Watch the Pods if the wait times out; a timeout is diagnostic data, not a reason to immediately delete and retry.

```bash
# Add NVIDIA Helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Pin the chart release you have tested; refresh this against NVIDIA docs before reuse.
RELEASE_TAG=v26.3.2

# Install GPU Operator with DCGM-Exporter ServiceMonitor enabled
helm install gpu-operator nvidia/gpu-operator \
  --wait \
  --namespace gpu-operator \
  --create-namespace \
  --version "${RELEASE_TAG}" \
  --set dcgmExporter.serviceMonitor.enabled=true \
  --set dcgmExporter.serviceMonitor.additionalLabels.release=kube-prometheus

# Wait for all pods to be ready (this takes 5-10 minutes)
kubectl -n gpu-operator wait --for=condition=Ready pods --all --timeout=600s
```

<details>
<summary>Solution notes</summary>

If the wait fails, run `kubectl get pods -n gpu-operator` and separate driver failures from toolkit, plugin, NFD, or DCGM failures. Driver Pods often reveal kernel header, secure boot, or node image issues. Device plugin failures often reveal missing devices or driver initialization problems. The right fix depends on the failing component, so avoid reinstalling the chart until you have read the relevant logs.
</details>

### Task 3: Verify GPU Resources and Labels

Now prove Kubernetes has a schedulable accelerator resource and enough labels for placement decisions. Capacity tells you the device plugin is reporting GPUs to kubelet, while labels tell you discovery is describing the hardware in a way workload manifests can use. Save the output for comparison when future node groups are added.

```bash
# Check that GPU resources are advertised
kubectl get nodes -o json | jq '.items[] | select(.status.capacity["nvidia.com/gpu"] != null) | {name: .metadata.name, gpus: .status.capacity["nvidia.com/gpu"], gpu_allocatable: .status.allocatable["nvidia.com/gpu"]}'

# Check GPU labels from NFD
kubectl get nodes --show-labels | grep nvidia
```

<details>
<summary>Solution notes</summary>

The JSON output should list at least one node with `gpus` and `gpu_allocatable`. If that output is empty, inspect the device plugin and driver before editing workload manifests. The label output should include NVIDIA-specific labels when GPU Feature Discovery is enabled; if it does not, inspect NFD and GFD Pods and verify the Operator values include discovery components.
</details>

### Task 4: Run a GPU Workload

Run a CUDA sample Job that requests one GPU and performs enough work to produce useful DCGM metrics. A validation Pod that exits immediately proves basic access, but a benchmark with multiple iterations gives Prometheus time to scrape utilization, memory, and temperature. Keep the namespace separate so cleanup is simple and ownership is clear.

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
          image: nvcr.io/nvidia/k8s/cuda-sample:nbody
          command: ["nbody"]
          args: ["-gpu", "-benchmark", "-numbodies=1024000", "-iterations=50"]
          resources:
            limits:
              nvidia.com/gpu: 1
  backoffLimit: 0
EOF

# Watch the job
kubectl -n ai-lab logs -f job/gpu-burn-test
```

<details>
<summary>Solution notes</summary>

The Job should schedule onto a GPU node, start the CUDA sample, and print benchmark output. If it remains pending, inspect events for missing tolerations, node affinity mismatch, or insufficient `nvidia.com/gpu`. If it starts but CUDA fails, inspect runtime injection and driver compatibility. If it completes too quickly to scrape, rerun with more iterations or query metrics immediately after completion while the exporter still exposes recent samples.
</details>

### Task 5: Verify DCGM Metrics in Prometheus

Query Prometheus directly before relying on Grafana. Dashboards can hide scrape problems with cached panels or wrong data sources, while the API query shows whether the metric series exists. Use `127.0.0.1` for the local port-forward target so the command behaves consistently in local environments that treat hostnames differently.

```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-prometheus 9090:9090 &

# Query DCGM metrics (wait 2-3 minutes for first scrape)
curl -s 'http://127.0.0.1:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL' | jq '.data.result[] | {gpu: .metric.gpu, node: .metric.node, utilization: .value[1]}'

# Check memory usage
curl -s 'http://127.0.0.1:9090/api/v1/query?query=DCGM_FI_DEV_FB_USED' | jq '.data.result[] | {gpu: .metric.gpu, node: .metric.node, vram_used_mib: .value[1]}'

# Check temperature
curl -s 'http://127.0.0.1:9090/api/v1/query?query=DCGM_FI_DEV_GPU_TEMP' | jq '.data.result[] | {gpu: .metric.gpu, temp_celsius: .value[1]}'
```

<details>
<summary>Solution notes</summary>

Each query should return at least one result with GPU and node labels. Empty results usually mean Prometheus is not scraping DCGM-Exporter, the ServiceMonitor labels do not match the Prometheus selector, or the exporter is not healthy. If utilization is zero after the benchmark completes, repeat the workload and query while it runs so you can distinguish scrape failure from a quiet device.
</details>

### Task 6: Import a Grafana Dashboard

Import the NVIDIA DCGM dashboard or build an equivalent internal dashboard. The dashboard is not the goal by itself; it is a shared view for spotting idle devices, thermal trouble, memory pressure, and workload imbalance. In production, add panels that group by namespace and workload owner so the platform team can act without manually mapping GPUs back to Pods.

```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &
```

Log in with `admin` and the password from your Helm values, then use Grafana's dashboard import UI with ID `12239` and select your Prometheus data source. If you automate this later, download or export the full dashboard JSON first and post a complete dashboard body; a stub payload that contains only the dashboard ID is not a valid import request and will fail because Grafana has no title, panels, or datasource mapping to import.

<details>
<summary>Solution notes</summary>

If the dashboard imports but panels are empty, check the Prometheus data source name and the metric names used by your DCGM-Exporter version. Do not treat dashboard import as a substitute for API verification. The best production dashboard is usually a fork of the vendor dashboard with local ownership labels, quota views, and alert links added.
</details>

### Cleanup

Clean up the experiment namespace when you are done. Leave the Operator installed if this cluster is meant to keep serving GPU workloads; remove it only in a temporary lab where no other users depend on the GPU stack. If you uninstall the Operator, confirm whether it also removes CRDs, driver artifacts, or monitoring objects you may want to keep.

```bash
kubectl delete namespace ai-lab
# Only if you want to remove the GPU Operator:
# helm uninstall gpu-operator -n gpu-operator
```

### Success Criteria

- [ ] GPU Operator Pods are Running or Completed in the `gpu-operator` namespace.
- [ ] `nvidia.com/gpu` appears in node capacity and allocatable output.
- [ ] GPU product, memory, count, or MIG labels appear on GPU nodes.
- [ ] A CUDA sample Pod or Job runs and prints successful validation or benchmark output.
- [ ] `DCGM_FI_DEV_GPU_UTIL` returns data from Prometheus.
- [ ] `DCGM_FI_DEV_GPU_TEMP` returns data from Prometheus.
- [ ] `DCGM_FI_DEV_FB_USED` returns data from Prometheus.
- [ ] Grafana shows GPU utilization for the benchmark or validation workload.

## Sources

- [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Kubernetes Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes Node Debugging with kubectl](https://kubernetes.io/docs/tasks/debug/debug-cluster/kubectl-node-debug/)
- [NVIDIA GPU Operator Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html)
- [NVIDIA GPU Operator Platform Support and Component Matrix](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/platform-support.html)
- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/)
- [NVIDIA DCGM Exporter Documentation](https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/latest/dcgm-exporter.html)
- [NVIDIA DCGM Field Identifiers](https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html)
- [NVIDIA DCGM User Guide](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/)
- [NVIDIA CUDA Compatibility Documentation](https://docs.nvidia.com/deploy/cuda-compatibility/)
- [NVIDIA H100 Tensor Core GPU](https://www.nvidia.com/en-us/data-center/h100/)
- [NVIDIA CUDA Samples on NGC](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/k8s/containers/cuda-sample)
- [NVIDIA Kubernetes Device Plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [Kubernetes SIG Node Feature Discovery](https://github.com/kubernetes-sigs/node-feature-discovery)
- [Container Device Interface Specification](https://github.com/cncf-tags/container-device-interface)
- [Prometheus Operator Getting Started](https://prometheus-operator.dev/docs/developer/getting-started/)
- [Grafana NVIDIA DCGM Exporter Dashboard](https://grafana.com/grafana/dashboards/12239-nvidia-dcgm-exporter-dashboard/)
- [Grafana Dashboard APIs](https://grafana.com/docs/grafana/latest/developer-resources/api-reference/http-api/dashboard/)

## Next Module

Continue to [Module 1.2: Advanced GPU Scheduling & Sharing](../module-1.2-gpu-scheduling/) to learn how to share GPUs across workloads using MIG, time-slicing, MPS, and Dynamic Resource Allocation.

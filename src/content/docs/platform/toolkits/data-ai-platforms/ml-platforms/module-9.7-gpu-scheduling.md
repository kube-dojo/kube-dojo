---
revision_pending: false
title: "Module 9.7: GPU Scheduling & NVIDIA GPU Operator on Kubernetes"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.7-gpu-scheduling
sidebar:
  order: 8
---
> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 70-85 minutes
>
> **Prerequisites**: Kubernetes scheduling fundamentals, taints and tolerations, node affinity, resource requests and limits, basic ML training and inference concepts, and Module 9.1 for the broader ML platform context.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Explain** how the Kubernetes device-plugin model advertises GPUs as integer extended resources and why GPU requests behave differently from CPU and memory requests.
- **Operate** the NVIDIA GPU Operator as a worked example for managing drivers, the container runtime integration, device plugin, DCGM metrics, feature discovery, and MIG lifecycle.
- **Choose** between whole-GPU allocation, time-slicing, MIG, MPS, and Dynamic Resource Allocation based on isolation, utilization, flexibility, and workload shape.
- **Design** GPU placement policies with labels, taints, topology awareness, queueing, and gang-scheduling tools for mixed training and inference clusters.
- **Validate** a GPU-sharing rollout with runnable Pod specs, Operator configuration, scheduler events, and utilization signals before exposing the tier to users.

## Why This Module Matters

Hypothetical scenario: your platform team has one GPU pool that supports ten product teams. Four teams run periodic training jobs, three teams serve latency-sensitive models, two teams need interactive notebook access, and one research team runs bursty experiments that may be idle for most of a day. Every workload says "I need a GPU," but each one means something different: a training job may need exclusive memory and high-bandwidth peer-to-peer paths, an inference service may need predictable latency on a small slice, and a notebook may only need occasional CUDA access for exploration.

The default Kubernetes scheduling model cannot infer those differences from `nvidia.com/gpu: 1`. Once a GPU device plugin advertises a resource, the scheduler treats it as an integer extended resource. A Pod either consumes one unit or it does not. That is deliberately simple, and it is the reason the model works across many kinds of devices, but it also means the platform team must design the resource shapes, labels, taints, and queueing rules that express real workload intent.

The durable practice in this module is not "install one vendor chart and memorize flags." The practice is learning how accelerator scheduling works in Kubernetes: how devices are discovered, how node capacity is advertised, how Pods request devices, how sharing changes isolation, and how placement decisions become support commitments. We use the NVIDIA GPU stack as the running worked example because it shows the major patterns clearly, but the mental model carries to AMD, Intel, future DRA-native drivers, and accelerator types that are not GPUs at all.

Think of a GPU platform like a workshop that owns a small number of specialized machines. A table saw, a laser cutter, and a CNC mill are not like shared hand tools that anyone can borrow for a few seconds. Some jobs need the whole machine, some can share time safely, and some require a jig or enclosure before another person can work nearby. Kubernetes is the booking desk, the device plugin is the inventory clerk, and the platform team writes the rules that stop one person's "quick cut" from ruining another person's production run.

This module is also intentionally narrower than the AI infrastructure discipline modules. Those modules cover GPU infrastructure strategy, provisioning, networking, training architecture, and cost governance across the broader platform. Here we stay close to the toolkit mechanics: how a Kubernetes cluster exposes GPUs, how the NVIDIA GPU Operator reconciles the node software stack, how sharing modes change the scheduler's view of capacity, and how to verify the behavior with real manifests.

## The Device-Plugin Model

Kubernetes does not natively know what a GPU is. The scheduler understands CPU, memory, ephemeral storage, Pods, taints, affinities, topology hints, and extended resources, but it does not include vendor-specific code for every accelerator. That separation is a feature. Device owners provide a device plugin that registers with the kubelet, reports healthy devices, and tells the kubelet how to prepare a container when a Pod is assigned a device.

The kubelet is the bridge between hardware inventory and the Kubernetes API. A device plugin runs on each node, opens a well-known registration socket, and serves a gRPC interface. After registration, the plugin streams device health and capacity to the kubelet. The kubelet then updates the Node object so the control plane sees capacity such as `nvidia.com/gpu: 4`, `amd.com/gpu: 4`, or a profile-specific MIG resource. The scheduler never probes PCI devices directly; it schedules against the capacity reported on the Node object.

That architecture explains why GPU requests are written under `resources.limits`. Extended resources are integer resources, they cannot be overcommitted by the core scheduler, and the Kubernetes GPU scheduling documentation says GPU requests and limits must be equal when both are specified. A Pod that requests one device consumes one advertised unit, regardless of whether the model inside the container uses the device continuously, occasionally, or barely at all. Utilization is an operational metric; allocation is the scheduler contract.

The simplest Pod demonstrates the entire path. The YAML does not say "run on node gpu-worker-01" or "mount `/dev/nvidia0`." It says the container needs one unit of the vendor resource. If a healthy node advertises a free unit, the scheduler can bind the Pod there, and the kubelet asks the plugin to allocate the device for the container. The container runtime integration then makes the device files, libraries, and environment visible inside the container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-smoke-test
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
```

The important operational consequence is that the scheduler can only place against what it can see. If a node has four physical GPUs but the plugin is unhealthy, the node may advertise no GPU capacity. If the plugin advertises a time-sliced resource name, users must request that name. If MIG mode changes the resource inventory from whole GPUs to profile resources, a Pod asking for `nvidia.com/gpu` may remain Pending even though the physical card is present and busy with smaller instances.

The device-plugin model is also why GPU scheduling is vendor-agnostic at the Kubernetes layer but vendor-specific at the node layer. Kubernetes provides the extension point, not the driver stack. NVIDIA, AMD, Intel, and other device owners decide how the plugin discovers devices, what resource names it advertises, what health checks it performs, and what runtime setup it returns. A platform engineer has to understand both halves: the Kubernetes contract and the device owner's implementation.

```text
GPU scheduling path

1. Node boots with accelerator hardware
2. Driver and runtime support make the hardware usable on the host
3. Device plugin registers with kubelet
4. Kubelet advertises extended resources on the Node object
5. Pod requests the extended resource in resources.limits
6. Scheduler binds the Pod to a node with enough allocatable capacity
7. Kubelet calls Allocate on the plugin before starting the container
8. Runtime exposes the selected device to the container
```

If a user asks why Kubernetes cannot simply schedule "half a GPU" the way it schedules half a CPU, this is the answer. CPU and memory are core resources with built-in accounting, cgroups, and overcommit behavior. GPUs are devices behind a plugin boundary. Fractional or shared behavior must be created by the device stack, exposed as a resource shape, and taught to users as a different service tier.

## GPU Operator as the Worked Example

Installing only a device plugin is rarely enough for a production GPU node. A useful GPU node also needs a compatible kernel driver, container runtime integration, device discovery, monitoring, optional MIG management, validation, and upgrade behavior. When those pieces are installed by hand, the cluster accumulates hidden state: one node has a different driver branch, another missed a container toolkit update, a third advertises GPUs but has broken metrics, and nobody knows which change made a workload fail.

The operator pattern improves that situation by making the node software stack declarative and reconciled. The NVIDIA GPU Operator is the worked example in this module. It manages the NVIDIA driver container when appropriate, configures the NVIDIA Container Toolkit, deploys the NVIDIA Kubernetes device plugin, deploys GPU Feature Discovery and Node Feature Discovery integration, runs DCGM Exporter for GPU metrics, and can manage MIG configuration through MIG Manager. The operator does not remove the need for platform policy, but it gives the policy a stable control plane object and a repeatable rollout path.

Operator-managed installation beats hand-installed drivers for the same reason Kubernetes beats SSH scripts for applications: desired state is visible, upgrades are reviewable, and drift is easier to diagnose. If the device plugin DaemonSet fails, you can inspect a Kubernetes object. If DCGM Exporter is not scraping metrics, you can inspect the Pod, Service, and ServiceMonitor path. If a MIG profile fails to apply, the relevant node labels and MIG Manager logs show whether the node is pending, rebooting, successful, or failed.

The operator is still not magic. It reconciles the NVIDIA software stack, but it cannot decide whether an inference service should use a full GPU, a MIG profile, a time-sliced replica, or MPS. It cannot know whether a training job needs NVLink locality. It cannot make a node safe to repartition while user workloads are still using the card. Those are platform decisions, and the operator is the mechanism that applies them consistently after you make them.

> **Landscape snapshot -- as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> | Area | Current fact | Why it belongs in the snapshot |
> |---|---|---|
> | KubeDojo Kubernetes target | Examples in this module target Kubernetes 1.35. | The curriculum target is a moving compatibility baseline. |
> | Kubernetes DRA status | The upstream DRA concept page marks core Dynamic Resource Allocation as Kubernetes v1.35 stable and enabled by default. | DRA has moved through alpha, beta, and stable states quickly, and adjacent DRA features have separate gates. |
> | GPU Operator patch level | NVIDIA's installation docs list GPU Operator v26.3.2 as the current patch release for the documented version. | Operator versions and operand versions change frequently. |
> | GPU Operator v26.3.2 operands | NVIDIA's component matrix lists device plugin 0.19.2, GPU Feature Discovery 0.19.2, MIG Manager 0.14.2, DCGM Exporter v4.5.3-4.8.2, and Node Feature Discovery v0.18.3. | These are release-matrix facts, not durable scheduling concepts. |
> | Kubernetes native gang scheduling | The upstream gang scheduling page marks the Kubernetes 1.35 feature as alpha and disabled by default. | Production scheduling choices may use native alpha features, Kueue, Volcano, or another batch scheduler depending on cluster policy. |

The right way to read the snapshot is to separate capability from currency. "A device plugin advertises extended resources" is durable. "This GPU Operator patch release includes this device plugin version" is volatile. If a future review updates only the snapshot and keeps the surrounding explanations intact, the module is doing its job.

### GPU Scheduling Rosetta

| Durable capability | NVIDIA GPU Operator running example | AMD device plugin and operator path | Intel device plugins path | DRA-native path |
|---|---|---|---|---|
| Whole-GPU allocation | Device plugin advertises `nvidia.com/gpu`; Pods request integer units. | AMD plugin advertises AMD GPU resources such as `amd.com/gpu` after AMD drivers and plugin are installed. | Intel GPU plugin advertises Intel GPU resources such as `gpu.intel.com/i915` or newer plugin-specific names. | A DRA driver publishes devices through ResourceSlices; workloads claim devices with ResourceClaims. |
| Time-slicing | NVIDIA device plugin can advertise replicas of `nvidia.com/gpu` or `nvidia.com/gpu.shared`; isolation is weaker than MIG. | Use vendor-supported sharing features only when the AMD stack exposes them; otherwise treat allocation as whole-device. | Use plugin-supported modes documented for the target Intel hardware and driver. | Model sharing as claim parameters only if the DRA driver implements and documents that behavior. |
| MIG-style hardware isolation | MIG Manager configures supported NVIDIA GPUs into profile resources such as `nvidia.com/mig-1g.10gb`. | Hardware partitioning semantics depend on the AMD device and operator support; do not assume MIG equivalence. | Hardware partitioning semantics depend on Intel GPU generation, driver, and plugin support. | DeviceClass and ResourceClaim attributes can express device shape when the driver publishes structured parameters. |
| MPS-style concurrent contexts | NVIDIA device plugin documents MPS sharing as experimental in the plugin path and incompatible with MIG-enabled devices. | Use only an AMD-documented equivalent if the driver and platform expose one. | Use only an Intel-documented equivalent if the driver and platform expose one. | DRA can describe allocation, but execution semantics still belong to the device driver. |
| Device metadata and selection | GPU Feature Discovery and Node Feature Discovery labels help steer Pods to product, memory, MIG, and driver characteristics. | AMD node labelling and device plugin metadata can provide scheduler selectors when enabled. | Intel Device Plugins commonly pair with Node Feature Discovery and NodeFeatureRules. | DeviceClass selectors and ResourceSlice attributes reduce dependence on hand-maintained node labels. |
| Multi-GPU training placement | Use node labels, topology policy, queueing, and scheduler extensions; keep NCCL and topology validation outside the basic Pod spec. | Same scheduling concerns apply, with vendor-specific collective libraries and driver validation. | Same scheduling concerns apply, with hardware-specific topology and runtime validation. | DRA may improve structured selection, but gang semantics and topology policy still need explicit design. |

The Rosetta table is not a ranking. It is a translation tool. A team that learns "device plugin, resource name, sharing mode, topology, and observability" can evaluate a new accelerator stack by asking which parts of that contract it implements, which parts remain manual, and which parts are not supported yet.

## GPU Sharing Taxonomy

Whole-GPU allocation is the safest baseline. One Pod consumes one advertised GPU resource, and the device is not intentionally shared through the scheduler. This is the right starting point for large training jobs, latency-sensitive inference with strict performance commitments, and debugging sessions where you need to remove noisy-neighbor variables. It is also the easiest model to explain to users: one requested unit means one exclusive device unit from the scheduler's perspective.

The downside is that whole-GPU allocation confuses allocation with usage. A service can reserve one GPU while using only occasional compute bursts. A notebook can hold a GPU while the user reads logs. A small model can fit into a small fraction of the device memory. Kubernetes has honored the request, but the platform may still be inefficient. That mismatch is the pressure that leads teams toward sharing.

Time-slicing is software sharing. The NVIDIA device plugin can advertise multiple replicas for a physical GPU, optionally renaming the resource to make the sharing tier explicit. Several Pods can then request one shared replica each, and the driver interleaves their work on the same physical device. This can improve access for notebooks, development environments, and small inference services that are bursty or tolerant of variable performance.

Time-slicing does not provide the memory and fault isolation that MIG provides. That point must be written into the platform contract. If four Pods share one physical device, they also share the underlying device memory pressure and failure domain. A badly behaved workload can harm neighbors in ways that would not happen with exclusive allocation. Time-slicing should therefore be presented as a lower-isolation tier, not as a free way to multiply GPUs.

MIG, or Multi-Instance GPU, is hardware partitioning on supported NVIDIA data-center GPUs. Instead of pretending one device is many through scheduler accounting, MIG creates smaller GPU instances with dedicated compute and memory slices. Kubernetes then sees profile-specific resources, such as `nvidia.com/mig-1g.10gb` on an A100 80 GB profile. A Pod requesting that profile receives a smaller but more isolated resource shape than a time-sliced whole GPU.

MIG is best when workload shapes are predictable. Inference services with known memory envelopes, managed notebooks with service tiers, and small training jobs can fit into a profile catalog. The catalog matters because MIG profiles are not arbitrary decimals. If every tenant asks for a custom shape, the platform can strand unusable slices and spend too much time repartitioning nodes. A small catalog of approved profiles is usually easier to support than a wide-open menu.

MPS, or Multi-Process Service, is a CUDA runtime service that lets compatible CUDA processes share one GPU context path more efficiently than ordinary context switching. It is useful for trusted workloads that launch many small kernels or have underutilized single-process execution. In Kubernetes, the NVIDIA device plugin documents MPS sharing separately from time-slicing and notes important constraints, including that sharing mode is node-wide and MPS is not supported on devices with MIG enabled in that plugin path.

MPS sits between "simple sharing" and "application-aware performance tuning." It can improve concurrency for compatible CUDA workloads, but it is not a generic multi-tenant isolation boundary. Treat it as a specialist mode for trusted tenants and measured workloads. If the operational problem is untrusted multi-team inference, MIG is usually easier to reason about. If the problem is developer access, time-slicing may be simpler. If the problem is a known CUDA application that underutilizes the GPU, MPS is worth a controlled pilot.

Dynamic Resource Allocation is the forward-looking Kubernetes path for richer accelerator requests. Classic device plugins expose names and integer counts. DRA adds API objects such as DeviceClass, ResourceClaim, ResourceClaimTemplate, and ResourceSlice so a workload can claim devices based on structured attributes instead of encoding every distinction in node labels and resource names. The durable idea is that devices become claimable objects with attributes, not just opaque integer counters.

DRA does not eliminate the need for device drivers, sharing policy, or operational validation. A DRA driver still has to publish accurate ResourceSlices, implement allocation behavior, prepare devices, and expose a supportable contract. The scheduler can reason about more structure, but the device owner still defines what "one suitable accelerator" means. A practical adoption plan starts with one workload family where DRA makes requests clearer than the existing device-plugin and label design.

The taxonomy is easiest to remember as a tradeoff triangle. Whole GPUs maximize isolation and simplicity. Time-slicing maximizes access and flexibility but weakens isolation. MIG offers stronger isolation with less flexibility because profiles must be selected and maintained. MPS can improve utilization for trusted CUDA workloads but requires careful compatibility testing. DRA changes how requests are expressed and allocated, but it does not magically decide the right sharing policy for you.

```text
Sharing decision spectrum

Exclusive GPU
  - strongest scheduling simplicity
  - strongest tenant separation
  - lowest packing density for small workloads

MIG profile
  - hardware-backed partition on supported devices
  - good for predictable inference and notebook tiers
  - profile catalog and reconfiguration discipline required

Time-sliced replica
  - many Pods can access one device
  - useful for bursty development and lower-risk inference
  - no MIG-like memory or fault isolation

MPS sharing
  - concurrent CUDA execution through MPS runtime
  - useful for trusted compatible workloads
  - not a general isolation boundary

DRA claim
  - richer, structured device request and allocation API
  - depends on DRA-capable driver implementation
  - complements rather than replaces policy design
```

## Placement Mechanics

A GPU resource request answers only one question: "does this node advertise enough allocatable units of the requested resource?" Real placement usually needs more. You often need to keep non-GPU Pods off expensive nodes, route training to nodes with fast interconnects, route inference to a shared pool, prevent one namespace from consuming every device, and avoid partial placement of distributed jobs. Those concerns are scheduler policy, not driver installation.

Taints are the first guardrail. A GPU node should normally carry a `NoSchedule` taint so ordinary Pods do not land there accidentally. Workloads that intentionally use the GPU pool add a matching toleration. This is not about security; it is about capacity hygiene. A CPU-only logging sidecar or unrelated batch job can waste the most constrained nodes in the cluster if the default scheduler sees them as ordinary Linux workers.

```bash
kubectl taint nodes gpu-worker-01 nvidia.com/gpu=present:NoSchedule
```

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: trainer
spec:
  template:
    spec:
      restartPolicy: Never
      tolerations:
        - key: nvidia.com/gpu
          operator: Equal
          value: present
          effect: NoSchedule
      containers:
        - name: train
          image: nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04
          command: ["bash", "-lc", "nvidia-smi && sleep 30"]
          resources:
            limits:
              nvidia.com/gpu: 1
```

Labels are the second guardrail. Node Feature Discovery detects hardware and system features and advertises them as labels. GPU Feature Discovery adds NVIDIA-specific labels such as GPU count, memory, product, MIG capability, and sharing state when the NVIDIA stack is installed. A workload that needs a specific GPU family, a MIG-capable pool, or a shared tier should select labels that describe the pool policy, not just the physical product. Platform-owned labels such as `platform.example.com/gpu-tier=shared-inference` are often easier for users than raw vendor labels.

Topology is the third guardrail. Multi-GPU training performance depends on how GPUs, CPUs, PCIe roots, NVLink, NVSwitch, and network interfaces are connected. A two-GPU job can run correctly but poorly if the GPUs are far apart in the node topology or if the CPU and network placement fight the collective communication path. Kubernetes Topology Manager can help align CPU and device placement on a node, but cluster-level policy still needs node labels, queueing, and validated node pools for serious distributed training.

Bin-packing and spreading are policy choices, not universal rules. For shared inference, packing small workloads onto a few GPUs can free entire nodes for scale-down or maintenance. For training, spreading jobs may reduce noisy-neighbor contention and preserve topology. For interactive notebooks, fairness may matter more than raw utilization. A good platform names these tiers separately so a user's Pod spec communicates intent before the scheduler makes placement decisions.

Queueing matters because GPUs are scarce and workloads are bursty. Kueue, Volcano, native Kubernetes gang scheduling, or another batch layer can decide when a job is admitted, which resource flavor it uses, and whether the entire job should wait instead of partially occupying devices. This is especially important for distributed training, where a job with several workers may be useless unless the minimum set can start together. Partial placement can burn GPU allocation while making no training progress.

Native Kubernetes gang scheduling in the 1.35 target is alpha and disabled by default, so treat it as a feature to evaluate rather than a default assumption. Kueue is a Kubernetes SIG project that focuses on job queueing, quota, and admission, and it commonly appears in ML batch scheduling designs. Volcano is another scheduler-oriented ecosystem option in many GPU clusters. The durable point is not which project you choose; the durable point is that multi-Pod accelerator jobs need all-or-nothing admission semantics somewhere in the design.

ResourceQuota and PriorityClass complete the basic policy set. A namespace-level quota can cap how many GPU resources one team can request. PriorityClass and preemption rules can let urgent production inference recover capacity from lower-priority experiments, but they must be used carefully because GPU workloads may not tolerate interruption unless they checkpoint or can restart cleanly. The scheduler can enforce the rules, but platform owners must decide which interruptions are acceptable.

## Worked Example: Request, Share, and Observe

The worked example uses the NVIDIA GPU Operator because it exposes the common mechanics in one path. You will install the operator, run a whole-GPU smoke test, configure a named time-slicing tier, run multiple shared Pods, and inspect scheduler behavior. The same lab can be adapted to MIG by changing node labels and requesting a MIG profile, but time-slicing is easier to demonstrate because it does not require MIG-capable hardware.

Before running the lab, check whether this is a disposable cluster, a development pool, or a production pool. Changing device plugin configuration can affect new Pod scheduling on GPU nodes. MIG changes can be disruptive because the node may need to stop GPU clients or reboot depending on the environment. If you are not allowed to change GPU node configuration, read the lab as a runbook review exercise and practice the inspection commands in a safe cluster.

Install or upgrade the GPU Operator. The snapshot records the version verified during authoring; production users should verify the current patch release before running the command. The command pins the version so the exercise is reproducible, while the prose teaches that pinning is an operational decision and not a permanent truth.

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

GPU_OPERATOR_VERSION=v26.3.2

helm upgrade --install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace \
  --version "${GPU_OPERATOR_VERSION}" \
  --wait \
  --timeout 10m
```

Verify that the operator Pods are healthy and that at least one node advertises GPU capacity. The first command checks the reconciled software stack. The second command inspects the scheduler-facing contract. If Pods are running but the node does not advertise `nvidia.com/gpu`, investigate the device plugin and driver path before blaming scheduler policy.

```bash
kubectl get pods -n gpu-operator

kubectl get nodes -o json | \
  jq '.items[] | {name: .metadata.name, gpu: .status.allocatable["nvidia.com/gpu"]}'
```

Run the smoke-test Pod. A successful log proves that the Pod scheduled, the kubelet allocated the device, the runtime exposed the device, and the container can call `nvidia-smi`. If the Pod remains Pending, read scheduler events. If it starts and fails, inspect the container log and the GPU Operator Pods because the problem may be driver or runtime setup rather than scheduling.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-smoke-test
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
EOF

kubectl wait --for=condition=Ready pod/gpu-smoke-test --timeout=120s || true
kubectl logs gpu-smoke-test
kubectl delete pod gpu-smoke-test
```

Create a named time-slicing configuration. The example uses `renameByDefault: true` so users must request `nvidia.com/gpu.shared` instead of silently receiving a shared unit under the same name as an exclusive GPU. It also uses `failRequestsGreaterThanOne: true` because asking for several shared replicas does not guarantee several physical GPUs or a linear performance increase. This setting turns a confusing over-request into an explicit admission failure.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpu-sharing-config
  namespace: gpu-operator
data:
  timeslice-4: |-
    version: v1
    sharing:
      timeSlicing:
        renameByDefault: true
        failRequestsGreaterThanOne: true
        resources:
          - name: nvidia.com/gpu
            replicas: 4
EOF

kubectl patch clusterpolicies.nvidia.com cluster-policy --type=merge -p '{
  "spec": {
    "devicePlugin": {
      "config": {
        "name": "gpu-sharing-config",
        "default": "timeslice-4"
      }
    }
  }
}'

kubectl -n gpu-operator rollout status daemonset/nvidia-device-plugin-daemonset --timeout=180s
```

Inspect the node inventory after the device plugin restarts. If the node has one physical GPU and the configuration advertises four replicas, you should see four shared units. If the node has more physical GPUs, multiply by the physical count. If the shared resource does not appear, confirm that the `ClusterPolicy` references the ConfigMap name and key, and then inspect the device plugin DaemonSet logs.

```bash
GPU_NODE=$(kubectl get nodes -l nvidia.com/gpu.present=true -o jsonpath='{.items[0].metadata.name}')

kubectl describe node "${GPU_NODE}" | grep -E 'nvidia.com/gpu|nvidia.com/gpu.shared'
```

Deploy several Pods that request the shared resource. These Pods are deliberately simple. They sleep so you can inspect placement, device visibility, and events without adding model-server complexity. A production inference deployment would also set CPU and memory limits, readiness probes, application-level concurrency, and model-specific GPU memory controls.

```bash
kubectl create namespace gpu-sharing-demo

for i in 1 2 3; do
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: shared-gpu-${i}
  namespace: gpu-sharing-demo
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04
      command: ["sleep", "3600"]
      resources:
        limits:
          nvidia.com/gpu.shared: 1
EOF
done

kubectl -n gpu-sharing-demo get pods -o wide
```

Observe the difference between scheduling and isolation. All three Pods may be Running, and each may see a GPU from inside the container. That does not mean each Pod owns a private hardware partition. Compare GPU UUIDs and memory totals from inside the containers, then decide whether the observed behavior matches the service tier you plan to offer.

```bash
for pod in $(kubectl -n gpu-sharing-demo get pods -o name); do
  echo "--- ${pod} ---"
  kubectl -n gpu-sharing-demo exec "${pod}" -- \
    nvidia-smi --query-gpu=gpu_name,gpu_uuid,memory.total --format=csv,noheader
done
```

Now test the scheduler boundary. If the node has one physical GPU and four shared replicas, a fourth Pod should schedule and a fifth Pod should remain Pending. If your node has more GPUs, adjust the expected count. The important signal is the Pending event, because it proves Kubernetes is enforcing the advertised shared-resource count even though the resource is backed by software sharing.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: shared-gpu-extra
  namespace: gpu-sharing-demo
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04
      command: ["sleep", "3600"]
      resources:
        limits:
          nvidia.com/gpu.shared: 1
EOF

kubectl -n gpu-sharing-demo get pods
kubectl -n gpu-sharing-demo describe pod shared-gpu-extra | sed -n '/Events:/,$p'
```

If your cluster has Prometheus scraping DCGM Exporter, inspect utilization and memory signals. Aggregate utilization may rise when several workloads share a GPU, but memory remains the risk to watch. A dashboard that celebrates higher utilization without showing memory pressure and per-tenant placement is incomplete for shared GPU operations.

```bash
curl -s 'http://127.0.0.1:9090/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL' | \
  jq '.data.result[] | {gpu: .metric.gpu, value: .value[1]}'

curl -s 'http://127.0.0.1:9090/api/v1/query?query=DCGM_FI_DEV_FB_USED' | \
  jq '.data.result[] | {gpu: .metric.gpu, value: .value[1]}'
```

Clean up the demonstration workloads and decide whether to keep the shared tier enabled. Deleting the namespace removes the Pods, but it does not remove the operator configuration. If this was only a lab, revert the `ClusterPolicy` to the previous device plugin configuration or move the shared configuration to a clearly labelled development pool.

```bash
kubectl delete namespace gpu-sharing-demo
```

## Reading Scheduler and Runtime Signals

A GPU scheduling problem should be diagnosed in layers, because each layer answers a different question. The Kubernetes scheduler answers whether a Pod can be placed against advertised capacity and constraints. The kubelet and device plugin answer whether the selected device can be allocated to the container. The runtime answers whether the container can see the device files and libraries. The application answers whether the model actually uses the GPU correctly. Jumping straight to framework logs can waste time when the Pod never had a schedulable resource in the first place.

Start with the Pod phase and events. A Pending Pod with "Insufficient nvidia.com/gpu" is not evidence of broken CUDA, broken drivers, or broken ML code. It means the scheduler could not find enough allocatable units of the requested resource after applying taints, tolerations, affinity, node selectors, quotas, and other scheduling rules. A Pending Pod that asks for `nvidia.com/gpu.shared` on a cluster that only advertises `nvidia.com/gpu` is also working as designed: the resource name is part of the contract, and a mismatched name is a different resource.

Next read the Node object rather than the cloud console or hardware inventory. A provider UI can show that a VM has physical accelerators attached, while Kubernetes may show no allocatable GPU resources because the driver, runtime, or device plugin has not completed successfully. Conversely, a node can advertise shared replicas after time-slicing even though the number of physical devices has not changed. The Node object is the scheduler's truth, so platform runbooks should capture `status.capacity`, `status.allocatable`, and relevant labels before changing any sharing policy.

Then inspect the GPU Operator components by role. Driver Pods reveal kernel header, secure boot, operating system, and driver installation issues. Toolkit Pods reveal runtime wiring issues. The device plugin reveals whether healthy devices were discovered and registered. GPU Feature Discovery and Node Feature Discovery reveal whether labels were produced. DCGM Exporter reveals whether metrics are available. MIG Manager reveals whether profile state moved from pending to success or failed. Treating every failure as "the operator is broken" hides the component that actually owns the symptom.

Runtime failures have a different shape. A Pod can be scheduled and still fail if the runtime cannot expose the device correctly, the image lacks expected user-space tooling, or the application expects a CUDA version that is incompatible with the driver path. A smoke test using `nvidia-smi` is useful because it isolates scheduling and runtime exposure from model-server complexity. It is not a full application test, but it tells you whether the container can see the GPU before you debug PyTorch, TensorFlow, Triton, vLLM, or a custom CUDA extension.

Metrics should be interpreted after allocation is understood. `DCGM_FI_DEV_GPU_UTIL` can tell you whether compute is active, and memory metrics can show pressure, but those metrics do not explain why a Pod is Pending. In a shared tier, aggregate utilization can look healthy while one tenant is close to exhausting memory. In an exclusive tier, low utilization may be acceptable for latency-critical inference. A platform dashboard should therefore combine scheduler state, resource names, Pod owner labels, queue age, utilization, memory, and error signals instead of presenting utilization as a single verdict.

The most useful troubleshooting question is often "which contract did this workload request?" If the Pod requested a whole GPU, inspect whole-GPU capacity and exclusive pool labels. If it requested a MIG profile, inspect the node's MIG profile labels and advertised profile resources. If it requested a shared resource, inspect the device plugin configuration and shared capacity. If it used a queueing layer, inspect admission state before inspecting individual Pods. This habit keeps teams from applying the right command to the wrong layer.

## Rolling Out GPU Sharing Safely

GPU sharing should be rolled out like a new platform product, not like a hidden optimization. The first step is to define the user-facing contract in plain language: which workloads the tier accepts, which workloads it rejects, what isolation it provides, what performance variability users should expect, how quotas work, and who owns incidents. If the contract says "development and low-risk inference only," admission policy, namespace policy, and documentation should reinforce that boundary rather than relying on informal reminders.

Begin with one node pool and one sharing method. A small pilot reduces blast radius and makes measurements easier to interpret. If you enable time-slicing, choose one replica count and one resource name. If you enable MIG, choose one or two profiles from a catalog and avoid live profile churn. If you evaluate MPS, keep it in a trusted workload pool and require application owners to prove compatibility. A pilot that changes hardware shape, scheduler policy, queueing, and application concurrency all at once is hard to debug because every symptom has too many possible causes.

Before the pilot admits users, write the rollback path. For time-slicing, rollback might mean removing the device plugin configuration from the `ClusterPolicy`, restarting the device plugin DaemonSet, and confirming that the shared resource disappears from node allocatable capacity. For MIG, rollback might require cordoning, draining GPU clients, relabeling the node to `all-disabled` or another known profile, waiting for MIG Manager, and verifying the advertised resources. Rollback commands should be tested in the same kind of lab where the feature was tested.

Quotas should be applied before broad access. Without namespace limits, a single user can consume every shared replica even if each replica maps to the same physical device. Quotas also make the platform contract easier to explain: a team receives a certain number of shared seats, profile slices, or whole GPUs, and the queue or scheduler enforces that agreement. Quota design should follow the service tier. A notebook tier may cap users tightly, while a production inference tier may reserve capacity for specific namespaces and avoid opportunistic access.

Admission policy can prevent confusing requests. If a shared tier uses `nvidia.com/gpu.shared`, reject Pods that request more than one shared replica unless your platform has a documented reason to allow it. If a MIG tier supports only approved profiles, reject unknown profile resources before users wait through unclear Pending events. If a production namespace is not allowed to use time-slicing, block that request at admission. Good admission policy turns tribal knowledge into an immediate, actionable error.

Capacity planning should count fragments, not only devices. A node with MIG profiles can be full for one profile while still having stranded capacity that no workload can use. A time-sliced node can have available shared replicas while memory pressure makes additional placement risky. A queue can have enough total GPUs over the next hour but not enough simultaneous GPUs for one distributed job. GPU platform capacity is therefore multidimensional: physical cards, advertised resources, profile shapes, memory, topology, quotas, and time all matter.

User education is part of the rollout. A short examples page should show the exact resource name for exclusive GPUs, shared GPUs, and each supported MIG profile. It should show how to read a Pending event, how to request the right toleration, and how to decide whether a workload belongs in the tier. This is not hand-holding; it is incident prevention. When the examples are clear, users file better tickets, copy safer manifests, and stop treating accelerator scheduling as a mysterious cluster behavior.

Finally, schedule a review after real usage appears. Compare queue age, Pending reasons, utilization, memory pressure, error rates, and tenant feedback against the original contract. If shared notebooks are stable but shared inference has noisy latency, split the tiers instead of arguing with the dashboard. If a MIG profile is rarely used, remove it from the catalog or combine demand into a more useful shape. If users keep requesting the wrong resource, rename the tier or strengthen admission feedback. A GPU platform improves when the operating data changes the policy, not when the policy is frozen because the first rollout succeeded.

## Patterns & Anti-Patterns

Good GPU scheduling patterns make the resource contract visible before a workload is deployed. The user should be able to tell whether they are asking for exclusive hardware, a MIG slice, a time-sliced replica, or a queued training job. The operator should be able to tell which policy applied from labels, resource names, quotas, and events. Ambiguous resource names create expensive support tickets because everyone has to rediscover the platform's intent after something goes wrong.

| Pattern | Why it works | Example policy |
|---|---|---|
| Name service tiers explicitly | Users understand the isolation and performance contract before requesting capacity. | Use `nvidia.com/gpu.shared` for time-sliced tiers and platform labels such as `platform.example.com/gpu-tier=dev-shared`. |
| Keep profile catalogs small | Standard shapes improve quota, documentation, alerting, and capacity planning. | Offer small, medium, and full-GPU tiers before adding custom MIG profiles. |
| Treat topology as a workload requirement | Multi-GPU jobs need locality and communication paths, not just any available device count. | Route distributed training through validated node pools and queueing policy. |
| Verify scheduler events before metrics | Pending Pods are explained by requested resources and constraints before utilization dashboards matter. | Use `kubectl describe pod` events before tuning DCGM alerts. |

Anti-patterns usually come from hiding tradeoffs. A platform that silently time-slices `nvidia.com/gpu` under the same resource name as exclusive hardware may look efficient until a production workload gets unstable latency. A platform that lets every team create arbitrary MIG layouts may look flexible until capacity is fragmented. A platform that admits half of a distributed training job may look busy while useful work is blocked.

| Anti-pattern | Failure mode | Better approach |
|---|---|---|
| Silent sharing under the exclusive resource name | Users believe they received private hardware and debug noisy-neighbor behavior as an application bug. | Rename shared resources and document the tier. |
| One GPU pool for every workload class | Training, inference, notebooks, and experiments fight over incompatible scheduling expectations. | Separate pools or resource flavors by isolation, topology, and interruption tolerance. |
| Repartitioning MIG nodes during normal traffic | Existing GPU clients may be stopped, evicted, or left Pending during profile changes. | Cordon, drain, communicate, reconfigure, verify, and reopen capacity deliberately. |
| Treating utilization as the only success metric | Higher utilization can hide memory contention, latency variance, and broken tenant expectations. | Pair utilization with placement, memory, errors, queue age, and workload SLO signals. |

### Decision Framework

| Workload need | Prefer | Avoid | Reasoning |
|---|---|---|---|
| Large multi-GPU training with collective communication | Whole GPUs in a validated training pool plus queueing or gang scheduling | Time-slicing or arbitrary mixed placement | Throughput and topology predictability matter more than packing density. |
| Predictable production inference on supported NVIDIA hardware | MIG profiles from a small catalog | Unlabeled time-slicing under the default resource name | Hardware partitioning gives stronger isolation while preserving useful density. |
| Interactive notebooks and low-risk development | Time-sliced shared tier with quotas and clear naming | Exclusive GPUs for idle notebooks | Access and fairness matter more than strict performance guarantees. |
| Trusted CUDA workloads with small kernels and measured underutilization | MPS pilot on a dedicated pool | MPS as a broad multi-tenant default | MPS is an execution optimization, not a general isolation model. |
| Attribute-heavy device selection across changing hardware | DRA pilot with a DRA-capable driver | A growing maze of hand-written node selectors | Structured claims can reduce brittle label logic when driver support is ready. |

The framework should be applied as a review habit. Start with workload intent, choose the weakest sharing mode that still satisfies isolation and performance needs, then prove the scheduler and runtime behavior in a lab. If a design requires users to remember unwritten exceptions, convert those exceptions into resource names, labels, quotas, or admission policy before the service becomes self-service.

## Did You Know?

- Kubernetes device-plugin documentation states that extended resources are integer resources and cannot be overcommitted by the core scheduler.
- NVIDIA's GPU Operator v26.3.2 component matrix lists the NVIDIA Kubernetes device plugin and GPU Feature Discovery at 0.19.2.
- NVIDIA's time-slicing documentation explicitly describes the tradeoff: broader sharing in exchange for weaker memory and fault isolation than MIG.
- Kubernetes native gang scheduling is documented as a Kubernetes 1.35 alpha feature that is disabled by default.

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Requesting `nvidia.com/gpu` for every workload | Small inference and notebook workloads reserve the same scheduler unit as large training jobs. | Publish separate exclusive, shared, and MIG resource tiers. |
| Leaving GPU nodes untainted | CPU-only workloads can land on scarce accelerator nodes. | Taint GPU nodes and require explicit tolerations from GPU workloads. |
| Hiding time-slicing behind the default resource name | Users cannot tell whether they received exclusive or shared capacity. | Enable shared-resource naming and document the weaker isolation contract. |
| Treating MIG as dynamically free to change | Repartitioning affects real devices and may require workload disruption. | Change MIG layouts through a maintenance runbook with cordon, drain, and verification. |
| Ignoring scheduler events | Teams chase driver or framework issues when the Pod is simply unschedulable. | Read `kubectl describe pod` events before investigating runtime metrics. |
| Running distributed training without queueing or gang semantics | Partial placement can hold GPUs without making useful training progress. | Use Kueue, native gang scheduling where appropriate, Volcano, or another all-or-nothing admission layer. |
| Using utilization alone for chargeback or health | A shared GPU can look efficient while one tenant causes memory pressure or latency variance. | Combine DCGM utilization, memory, errors, Pod placement, queue age, and tenant labels. |
| Assuming vendor features map one-to-one | MIG, MPS, and plugin naming are vendor-specific implementation details. | Translate capabilities through the Rosetta model and verify each vendor's current docs. |

## Quiz

1. A Pod requests `nvidia.com/gpu: 1`, and the cluster has one node with four physical GPUs advertised by the NVIDIA device plugin. What does the scheduler know, and what does it not know?

<details>
<summary>Answer</summary>

The scheduler knows that the Pod needs one integer unit of the extended resource named `nvidia.com/gpu`, and it can bind the Pod to a node with one allocatable unit available. It does not know the model's actual utilization, memory footprint, CUDA behavior, or whether the workload would be safe to share. This is the **Explain** outcome: the device-plugin model advertises devices as extended resources, while runtime behavior remains outside the core scheduler's native CPU and memory accounting.
</details>

2. Your platform wants one install path that manages the NVIDIA driver, container runtime integration, device plugin, DCGM metrics, GPU Feature Discovery, and MIG Manager. Why is an operator-managed stack preferable to hand-installed node scripts?

<details>
<summary>Answer</summary>

An operator-managed stack makes the GPU software lifecycle visible as Kubernetes objects and reconciles drift across nodes. Hand-installed scripts can work initially, but they often hide version skew, missed upgrades, and broken metrics until a workload fails. This is the **Operate** outcome: use the NVIDIA GPU Operator as a worked example for driver, runtime, device plugin, DCGM, feature discovery, and MIG lifecycle management, while still keeping policy decisions in the platform layer.
</details>

3. A team wants to run several low-risk notebook Pods on one physical GPU. They do not need strong latency guarantees, but they do need users to understand that the tier is shared. Which sharing mode and naming choice fit best?

<details>
<summary>Answer</summary>

Time-slicing is a reasonable starting point because notebooks are often bursty and can tolerate weaker isolation than production inference. The platform should enable shared-resource naming, such as `nvidia.com/gpu.shared`, so users do not confuse the tier with exclusive `nvidia.com/gpu` allocation. This is part of the **Choose** outcome: select time-slicing when flexibility and access matter more than MIG-style isolation, then make the tradeoff visible in the resource name.
</details>

4. A production inference service has a predictable memory footprint and runs on supported NVIDIA data-center GPUs. The service owner wants stronger isolation than time-slicing without reserving a whole card. Which option should you evaluate first?

<details>
<summary>Answer</summary>

Evaluate a MIG profile from a small platform-approved catalog. MIG partitions supported GPUs into hardware-backed instances with stronger memory and fault isolation than time-slicing, which fits predictable inference better than a generic shared rotation. This answer reinforces the **Choose** outcome because the right sharing method depends on isolation, utilization, flexibility, and workload shape rather than on a blanket rule that all inference should share GPUs the same way.
</details>

5. A distributed training Job creates eight worker Pods, but only six can schedule. The six scheduled Pods hold GPUs and wait for the remaining workers, so no useful training begins. What scheduling design is missing?

<details>
<summary>Answer</summary>

The design is missing all-or-nothing admission for the worker set. A queueing or gang-scheduling layer should admit the job only when the required worker group can run, or keep the whole job waiting without occupying partial GPU capacity. This is the **Design** outcome: GPU placement policy is not only labels and taints; multi-Pod training needs queueing, topology awareness, and gang semantics so capacity is used for work that can actually proceed.
</details>

6. After enabling time-slicing with four replicas, a fifth shared Pod remains Pending on a single-GPU node. A teammate says the GPU is not busy and asks why Kubernetes refuses the Pod. What do you inspect and how do you explain it?

<details>
<summary>Answer</summary>

Inspect the Pod events and the node's advertised allocatable resources before looking at utilization metrics. Kubernetes schedules against the four shared replicas advertised by the device plugin, not against a live estimate of how busy the silicon feels. This is the **Validate** outcome: verify a GPU-sharing rollout with node capacity, scheduler events, and observed runtime behavior so the team can distinguish allocation limits from utilization.
</details>

7. Your team is considering DRA because raw node selectors have become hard to maintain across several accelerator models. What problem should DRA solve before you introduce it?

<details>
<summary>Answer</summary>

DRA should solve a real device-selection problem, such as claiming devices by structured attributes through DeviceClasses and ResourceClaims instead of encoding every distinction in resource names and node labels. It should not be adopted merely because it is newer, and it does not remove the need for quotas, driver validation, or sharing policy. This answer connects the **Choose** and **Design** outcomes: DRA changes how accelerator requests are expressed, but the platform must still decide isolation, topology, and admission behavior.
</details>

## Hands-On

This exercise is a safety-focused runbook for one GPU-enabled Kubernetes cluster. Use a disposable lab or a development GPU pool, because device plugin and MIG configuration can affect new scheduling decisions. If you only have read access to a production cluster, complete the inspection steps and write down which commands would require a change window.

### Task 1: Verify the Device-Plugin Contract

Install or confirm the GPU Operator, then inspect the Node object for advertised GPU resources. The purpose is to prove the scheduler-facing contract before you run any workload. If no node advertises GPU capacity, do not continue to sharing configuration until the driver, runtime, and device plugin path is healthy.

```bash
kubectl get pods -n gpu-operator

kubectl get nodes -o json | \
  jq '.items[] | {name: .metadata.name, capacity: .status.capacity, allocatable: .status.allocatable}'
```

### Task 2: Run an Exclusive GPU Smoke Test

Apply the smoke-test Pod and inspect its logs. A successful run confirms that Kubernetes can schedule the request, kubelet can allocate the device, and the container can see the GPU. A Pending Pod points to scheduler constraints, while a failed container points to runtime or driver setup.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-smoke-test
spec:
  restartPolicy: Never
  containers:
    - name: cuda
      image: nvcr.io/nvidia/cuda:12.5.0-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
EOF

kubectl describe pod gpu-smoke-test
kubectl logs gpu-smoke-test
kubectl delete pod gpu-smoke-test
```

### Task 3: Configure and Observe a Shared Tier

Use the time-slicing ConfigMap from the worked example, then deploy several Pods that request `nvidia.com/gpu.shared`. Compare node allocatable capacity, Pod placement, scheduler events, and GPU UUIDs. The goal is not to prove time-slicing is always right; the goal is to prove that the platform can explain exactly what the shared tier does.

```bash
kubectl -n gpu-sharing-demo get pods -o wide

for pod in $(kubectl -n gpu-sharing-demo get pods -o name); do
  kubectl -n gpu-sharing-demo exec "${pod}" -- \
    nvidia-smi --query-gpu=gpu_name,gpu_uuid,memory.total --format=csv,noheader
done
```

### Success Criteria

- [ ] At least one node advertises the expected exclusive GPU resource before sharing is configured.
- [ ] The exclusive smoke-test Pod runs `nvidia-smi` successfully or produces a scheduler event that explains why it cannot run.
- [ ] After time-slicing is configured, the node advertises the expected shared resource name rather than silently reusing the exclusive tier.
- [ ] Multiple shared Pods reach Running and can report GPU identity from inside the container.
- [ ] A Pod that exceeds the advertised shared capacity remains Pending with an event that references insufficient GPU shared capacity.
- [ ] You can explain whether the observed tier is exclusive GPU, time-sliced GPU, MIG profile, MPS, or a DRA-style future claim path.

## Sources

- [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Kubernetes Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [Kubernetes Dynamic Resource Allocation](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [Kubernetes DRA Structured Parameters KEP](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/4381-dra-structured-parameters/README.md)
- [Kubernetes Gang Scheduling](https://kubernetes.io/docs/concepts/scheduling-eviction/gang-scheduling/)
- [Kubernetes Topology Manager](https://kubernetes.io/docs/tasks/administer-cluster/topology-manager/)
- [NVIDIA GPU Operator Installation](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html)
- [NVIDIA GPU Operator Platform Support and Component Matrix](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/platform-support.html)
- [NVIDIA GPU Operator GPU Sharing](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
- [NVIDIA GPU Operator with MIG](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-operator-mig.html)
- [NVIDIA Kubernetes Device Plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [NVIDIA Multi-Instance GPU User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/latest/index.html)
- [NVIDIA Multi-Process Service](https://docs.nvidia.com/deploy/mps/latest/index.html)
- [Node Feature Discovery Introduction](https://kubernetes-sigs.github.io/node-feature-discovery/v0.18/get-started/introduction.html)
- [Kueue Overview](https://kueue.sigs.k8s.io/docs/overview/)
- [Kueue Workload Concept](https://kueue.sigs.k8s.io/docs/concepts/workload/)
- [AMD GPU Device Plugin for Kubernetes](https://instinct.docs.amd.com/projects/k8s-device-plugin/en/latest/)
- [Intel GPU Device Plugin for Kubernetes](https://github.com/intel/intel-device-plugins-for-kubernetes/blob/main/cmd/gpu_plugin/README.md)
- [NVIDIA DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter)

## Next Module

Continue to [Module 9.8: KServe](../module-9.8-kserve/) to learn how Kubernetes-native model serving platforms build on scheduling, autoscaling, and resource isolation for production inference.

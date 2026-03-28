---
title: "Module 1.4: High-Performance Storage for AI"
slug: platform/disciplines/ai-infrastructure/module-1.4-ai-storage
sidebar:
  order: 5
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 3 hours

## Prerequisites

Before starting this module:
- **Required**: Kubernetes storage fundamentals (PersistentVolumes, PersistentVolumeClaims, StorageClasses, CSI drivers)
- **Required**: Basic understanding of ML training data pipelines (datasets, batches, data loaders)
- **Recommended**: [Module 1.1: GPU Provisioning](module-1.1-gpu-provisioning/) — GPU workload basics
- **Recommended**: Experience with object storage (S3, GCS, MinIO)

---

## Why This Module Matters

You spent months building a beautiful GPU platform. The GPUs are provisioned, shared efficiently, connected by InfiniBand. Then your ML team starts training and reports this:

> "Our 8-GPU job only uses 40% GPU utilization. The GPUs are waiting for data."

This is the **IO bottleneck** — the most common and most underestimated performance killer in AI infrastructure. Your $300,000 DGX node is sitting idle 60% of the time because the storage system cannot feed data to the GPUs fast enough.

The numbers are stark:

| Component | Throughput | Latency |
|-----------|-----------|---------|
| GPU compute (A100 BF16) | 312 TFLOPS | nanoseconds |
| GPU memory (HBM3) | 2 TB/s | nanoseconds |
| NVMe SSD (local) | 7 GB/s | 10-100 μs |
| Network storage (CephFS) | 1-5 GB/s | 0.5-5 ms |
| Object storage (S3) | 100-500 MB/s | 10-100 ms |

There is a **1,000x gap** between GPU memory speed and network storage speed. Bridging this gap is what this module is about.

---

## The IO Bottleneck in ML Workloads

### Where IO Happens

Every training step involves IO at multiple stages:

```
┌─────────────────────────────────────────────────────────────┐
│                      Training Loop                           │
│                                                               │
│  1. Load batch          2. Transfer to GPU    3. Compute     │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │ Read from    │      │ CPU RAM →    │     │ Forward +  │ │
│  │ storage      │ ──→  │ GPU VRAM     │ ──→ │ Backward   │ │
│  │ (IO bound)   │      │ (PCIe bound) │     │ (compute)  │ │
│  └──────────────┘      └──────────────┘     └────────────┘ │
│  100ms - 5s              1-10ms               10-100ms       │
│                                                               │
│  ← This dominates when storage is slow                       │
└─────────────────────────────────────────────────────────────┘
```

### Workload IO Profiles

Different ML workloads have radically different IO characteristics:

| Workload | Data Size | Access Pattern | Read Size | Throughput Need |
|----------|-----------|---------------|-----------|-----------------|
| Image classification (ImageNet) | 150 GB | Random, small files | 100-500 KB | 2-5 GB/s |
| Object detection (COCO) | 20 GB | Random, medium files | 200 KB - 5 MB | 1-3 GB/s |
| NLP pre-training (C4) | 800 GB | Sequential, large files | 1-100 MB | 5-20 GB/s |
| Video training | 5-50 TB | Sequential, very large | 50-500 MB | 10-50 GB/s |
| LLM fine-tuning (tokenized) | 10-100 GB | Sequential | 1-10 MB | 1-5 GB/s |
| Checkpoint save | 1-50 GB per save | Sequential write | Full model | 5-20 GB/s burst |

The key insight: **image training** does millions of small random reads (hard for network storage), while **LLM training** does large sequential reads (easier to cache).

### Profiling IO Bottlenecks

Before optimizing, measure. Run your training job with GPU utilization monitoring:

```bash
# Monitor GPU utilization during training
# If GPU util is < 80% and you're not memory-bound, you're IO-bound

# Quick check: watch nvidia-smi during training
kubectl exec -it training-pod -- watch -n 1 'nvidia-smi --query-gpu=utilization.gpu,utilization.memory --format=csv,noheader'

# Better: check PyTorch DataLoader timing
# Add this to your training script:
# import time
# for batch in dataloader:
#     load_end = time.time()
#     print(f"Data load: {load_end - load_start:.3f}s")
#     # ... training step ...
#     load_start = time.time()
```

---

## Storage Tiers for AI

### The Storage Pyramid

AI workloads need a multi-tier storage architecture:

```
                    ┌─────────────┐
                    │   GPU VRAM   │  2 TB/s, μs latency
                    │  (training)  │  Managed by framework
                    ├─────────────┤
                 ┌──┤  Local NVMe  │  3-14 GB/s, 10-100 μs
                 │  │  (hot cache) │  TopoLVM, OpenEBS LVM
                 │  ├─────────────┤
              ┌──┤  │ Distributed  │  1-10 GB/s, 0.5-5 ms
              │  │  │  FS (warm)   │  CephFS, GlusterFS, JuiceFS
              │  │  ├─────────────┤
           ┌──┤  │  │   Object     │  100 MB-5 GB/s, 10-100 ms
           │  │  │  │  Storage     │  S3, GCS, MinIO
           │  │  │  │  (cold)      │
           │  │  │  ├─────────────┤
           │  │  │  │   Tape/      │  Archival
           │  │  │  │  Archive     │  Glacier, Coldline
           │  │  │  └─────────────┘
           │  │  │
      Cost │  │  │ Speed
       ▼   │  │  │   ▲
       $   $$  $$$  $$$$
```

The platform team's job is to build infrastructure that automatically moves data between tiers based on access patterns.

---

## Local NVMe Caching

### Why Local Storage Matters

A modern NVMe SSD delivers 3-7 GB/s sequential read and 500K-1M IOPS random read. This is 10-50x faster than network storage for the random small-file reads that image training demands.

The strategy: keep the active dataset (or a cache of it) on local NVMe while the canonical copy lives in object storage.

### TopoLVM: Topology-Aware Local Volumes

TopoLVM is a CSI driver that provisions PersistentVolumes from local LVM volume groups, with **topology awareness** — it ensures Pods are scheduled on nodes that have available local storage.

```bash
# Install TopoLVM
helm repo add topolvm https://topolvm.github.io/topolvm
helm repo update

helm install topolvm topolvm/topolvm \
  --namespace topolvm-system \
  --create-namespace \
  --set controller.replicaCount=2 \
  --set node.volumeGroup.name=nvme-vg    # LVM VG name on each node
```

Create a StorageClass:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nvme-local
provisioner: topolvm.io
parameters:
  topolvm.io/device-class: nvme       # Maps to a device class in TopoLVM config
volumeBindingMode: WaitForFirstConsumer # Delay binding until Pod is scheduled
allowVolumeExpansion: true
reclaimPolicy: Delete
```

Use in a training Pod:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: training-cache
  namespace: ml-training
spec:
  storageClassName: nvme-local
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: image-trainer
  namespace: ml-training
spec:
  containers:
    - name: trainer
      image: nvcr.io/nvidia/pytorch:24.09-py3
      volumeMounts:
        - name: cache
          mountPath: /data/cache
        - name: dataset
          mountPath: /data/s3     # S3 FUSE mount or pre-downloaded
      resources:
        limits:
          nvidia.com/gpu: 4
  volumes:
    - name: cache
      persistentVolumeClaim:
        claimName: training-cache
    - name: dataset
      persistentVolumeClaim:
        claimName: imagenet-s3
```

### OpenEBS LVM Local PV

OpenEBS provides a simpler alternative for local NVMe provisioning:

```bash
# Install OpenEBS LVM LocalPV
helm repo add openebs https://openebs.github.io/openebs
helm repo update

helm install openebs openebs/openebs \
  --namespace openebs \
  --create-namespace \
  --set lvm-localpv.enabled=true \
  --set engines.replicated.mayastor.enabled=false
```

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: openebs-nvme
provisioner: local.csi.openebs.io
parameters:
  storage: "lvm"
  vgPattern: "nvme-vg"          # LVM volume group pattern
  fsType: "xfs"                  # XFS recommended for large files
volumeBindingMode: WaitForFirstConsumer
```

### Init Container Pattern for Data Staging

A common pattern: use an init container to stage data from object storage to local NVMe before training begins:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: training-with-staging
  namespace: ml-training
spec:
  template:
    spec:
      initContainers:
        - name: stage-data
          image: amazon/aws-cli:2.17
          command: ["sh", "-c"]
          args:
            - |
              echo "Staging dataset from S3..."
              start=$(date +%s)
              aws s3 sync s3://my-datasets/imagenet/ /data/cache/imagenet/ \
                --no-sign-request --quiet
              end=$(date +%s)
              size=$(du -sh /data/cache/imagenet/ | cut -f1)
              echo "Staged $size in $((end-start)) seconds"
          volumeMounts:
            - name: cache
              mountPath: /data/cache
          resources:
            requests:
              cpu: "4"
              memory: 8Gi
      containers:
        - name: trainer
          image: nvcr.io/nvidia/pytorch:24.09-py3
          command: ["torchrun", "--nproc_per_node=4", "train.py", "--data_dir=/data/cache/imagenet"]
          volumeMounts:
            - name: cache
              mountPath: /data/cache
          resources:
            limits:
              nvidia.com/gpu: 4
      volumes:
        - name: cache
          persistentVolumeClaim:
            claimName: training-cache
      restartPolicy: OnFailure
```

---

## Distributed Filesystems

### CephFS

Ceph is the most widely deployed distributed storage system in Kubernetes. CephFS provides a POSIX-compatible filesystem backed by the Ceph cluster.

**Strengths for AI**:
- POSIX semantics (training frameworks expect filesystem APIs)
- Scalable metadata server (can handle millions of small files)
- Multi-reader access (ReadWriteMany) for data-parallel training
- Integrated with Rook for Kubernetes-native deployment

**Weaknesses for AI**:
- Latency: 0.5-5ms per operation (100-1000x slower than local NVMe)
- Throughput ceiling: limited by network and OSD count
- Small file performance: poor for millions of tiny files (image datasets)

```yaml
# Rook-Ceph CephFS StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cephfs-ai
provisioner: rook-ceph.cephfs.csi.ceph.com
parameters:
  clusterID: rook-ceph
  fsName: ai-filesystem
  pool: ai-data-pool
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-cephfs-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-cephfs-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
mountOptions:
  - noatime                    # Disable access time updates (major perf win)
  - nodiratime
```

### JuiceFS

JuiceFS is a cloud-native distributed filesystem purpose-built for the gap between object storage and high-performance compute. It separates metadata (stored in Redis, PostgreSQL, or TiKV) from data (stored in any object storage).

```
┌─────────────────────────────────────────────────────┐
│                    JuiceFS Architecture               │
│                                                       │
│  ┌────────────┐    ┌──────────────┐    ┌──────────┐ │
│  │  POSIX     │    │   Metadata   │    │  Object  │ │
│  │  Client    │──→ │   Engine     │    │  Storage │ │
│  │ (FUSE/CSI) │    │ (Redis/PG)   │    │  (S3)    │ │
│  │            │    └──────────────┘    │          │ │
│  │            │──────────────────────→ │          │ │
│  └────────────┘     Data path          └──────────┘ │
│       │                                              │
│       ▼                                              │
│  ┌────────────┐                                     │
│  │ Local Cache │  ← NVMe or RAM                    │
│  │ (read/write)│                                    │
│  └────────────┘                                     │
└─────────────────────────────────────────────────────┘
```

**Why JuiceFS excels for AI**:
1. **Transparent caching**: Reads are cached on local NVMe. Second read of same file is at NVMe speed.
2. **POSIX compatible**: Drop-in replacement for local filesystem in training scripts.
3. **Any object store backend**: S3, GCS, Azure Blob, MinIO — your data stays where it is.
4. **Metadata engine flexibility**: Redis for speed, PostgreSQL for durability, TiKV for scale.
5. **Kubernetes-native**: CSI driver with dynamic provisioning.

### Installing JuiceFS CSI Driver

```bash
# Install JuiceFS CSI Driver
helm repo add juicefs https://juicedata.github.io/charts/
helm repo update

helm install juicefs-csi juicefs/juicefs-csi-driver \
  --namespace kube-system \
  --set storageClasses[0].name=juicefs-sc \
  --set storageClasses[0].enabled=true \
  --set storageClasses[0].backend.name=ai-data \
  --set storageClasses[0].backend.metaurl=redis://:password@redis-master:6379/1 \
  --set storageClasses[0].backend.storage=s3 \
  --set storageClasses[0].backend.bucket=s3://my-ai-datasets \
  --set storageClasses[0].backend.accessKey=AKIAIOSFODNN7EXAMPLE \
  --set storageClasses[0].backend.secretKey=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --set storageClasses[0].cachePVC=juicefs-cache
```

### JuiceFS StorageClass with Caching

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: juicefs-ai
provisioner: csi.juicefs.com
parameters:
  csi.storage.k8s.io/provisioner-secret-name: juicefs-secret
  csi.storage.k8s.io/provisioner-secret-namespace: kube-system
  juicefs/mount-options: |
    cache-dir=/var/jfsCache
    cache-size=512000          # 500GB local cache
    buffer-size=1024           # 1GB read-ahead buffer
    prefetch=3                 # Prefetch 3 blocks ahead
    max-uploads=40             # Parallel upload threads
    metacache-expire=300       # Metadata cache TTL (seconds)
    open-cache=300             # Open file handle cache
reclaimPolicy: Retain
volumeBindingMode: Immediate
```

---

## Dataset Caching: Fluid and Alluxio

### The Caching Problem

Consider this scenario: 50 ML engineers share a 500GB ImageNet dataset stored in S3. Without caching:

```
Engineer 1 training job: Downloads 500GB from S3 → 30 min
Engineer 2 training job: Downloads 500GB from S3 → 30 min
...
Engineer 50 training job: Downloads 500GB from S3 → 30 min

Total: 25 TB downloaded, 25 hours of wait time, $50+ in S3 egress
```

With a caching layer:

```
Engineer 1 training job: Downloads 500GB from S3 → 30 min (cold)
Engineer 2 training job: Reads from cache → 2 min (warm)
...
Engineer 50 training job: Reads from cache → 2 min (warm)

Total: 500GB downloaded, 2 hours total wait, $1 in S3 egress
```

### Fluid: Kubernetes-Native Dataset Orchestration

Fluid is a CNCF sandbox project that brings dataset-aware scheduling to Kubernetes. It manages datasets as first-class resources and uses cache engines (Alluxio, JuiceFS, JindoFS) under the hood.

```bash
# Install Fluid
helm repo add fluid https://fluid-cloudnative.github.io/charts
helm repo update

helm install fluid fluid/fluid \
  --namespace fluid-system \
  --create-namespace
```

Define a dataset and its caching runtime:

```yaml
apiVersion: data.fluid.io/v1alpha1
kind: Dataset
metadata:
  name: imagenet
  namespace: ml-training
spec:
  mounts:
    - mountPoint: s3://my-datasets/imagenet/
      name: imagenet
      options:
        aws.accessKeyId: AKIAIOSFODNN7EXAMPLE
        aws.region: us-east-1
      encryptOptions:
        - name: aws.secretAccessKey
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: secretAccessKey
---
apiVersion: data.fluid.io/v1alpha1
kind: AlluxioRuntime
metadata:
  name: imagenet
  namespace: ml-training
spec:
  replicas: 3                    # 3 cache workers
  tieredstore:
    levels:
      - mediumtype: SSD
        path: /dev/shm,/var/cache/alluxio
        quota: 100Gi,400Gi       # 100GB RAM + 400GB SSD cache per worker
        high: "0.95"
        low: "0.7"
  fuse:
    args:
      - fuse
      - --attr-timeout=7200s
      - --entry-timeout=7200s
    cleanPolicy: OnDemand
  properties:
    alluxio.user.metadata.cache.enabled: "true"
    alluxio.user.metadata.cache.expireTime: "2day"
    alluxio.user.streaming.data.timeout: "300sec"
```

Use the dataset in a training Pod:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: imagenet-training
  namespace: ml-training
spec:
  template:
    spec:
      containers:
        - name: trainer
          image: nvcr.io/nvidia/pytorch:24.09-py3
          command: ["python", "train.py", "--data_dir=/data/imagenet"]
          volumeMounts:
            - name: imagenet
              mountPath: /data/imagenet
              readOnly: true
          resources:
            limits:
              nvidia.com/gpu: 4
      volumes:
        - name: imagenet
          persistentVolumeClaim:
            claimName: imagenet    # Automatically created by Fluid
      restartPolicy: OnFailure
```

### Fluid's Data-Aware Scheduling

Fluid tracks where cached data resides and preferentially schedules Pods on nodes that already have the data cached:

```yaml
# Fluid automatically injects scheduling hints
# Pods using the 'imagenet' dataset prefer nodes where Alluxio workers
# have already cached ImageNet data

# You can also trigger pre-warming:
apiVersion: data.fluid.io/v1alpha1
kind: DataLoad
metadata:
  name: imagenet-warmup
  namespace: ml-training
spec:
  dataset:
    name: imagenet
    namespace: ml-training
  loadMetadata: true
  target:
    - path: /
      replicas: 2    # Cache 2 copies for fault tolerance
```

### Alluxio Standalone (without Fluid)

For teams that want more control, Alluxio can be deployed independently:

```bash
helm repo add alluxio https://alluxio-charts.storage.googleapis.com/openSource
helm repo update

helm install alluxio alluxio/alluxio \
  --namespace alluxio \
  --create-namespace \
  --set master.count=1 \
  --set worker.count=3 \
  --set worker.resources.limits.memory=32Gi \
  --set tieredStore.levels[0].level=0 \
  --set tieredStore.levels[0].mediumtype=MEM \
  --set tieredStore.levels[0].path=/dev/shm \
  --set tieredStore.levels[0].quota=16Gi \
  --set tieredStore.levels[1].level=1 \
  --set tieredStore.levels[1].mediumtype=SSD \
  --set tieredStore.levels[1].path=/mnt/nvme/alluxio \
  --set tieredStore.levels[1].quota=500Gi \
  --set properties."alluxio.underfs.s3.region"=us-east-1
```

---

## Checkpoint Storage

### Why Checkpoint IO Matters

During training, checkpoints must be saved periodically. A checkpoint for a 70B parameter model is:

```
Model parameters:   70B × 2 bytes (BF16)  = 140 GB
Optimizer state:    70B × 8 bytes (Adam)   = 560 GB
Total:              ~700 GB per checkpoint
```

If your storage can write at 2 GB/s, saving one checkpoint takes **350 seconds** — almost 6 minutes. During this time, GPUs are either idle (synchronous checkpoint) or must continue while carefully not overwriting the in-flight checkpoint (asynchronous).

### Strategies for Fast Checkpointing

**Synchronous (simple, slow)**:
```python
# Training pauses during save
torch.save(model.state_dict(), "/checkpoints/latest.pt")
# 6 minutes of idle GPUs
```

**Asynchronous with background thread**:
```python
import threading

def save_async(state_dict, path):
    torch.save(state_dict, path)

# Clone state dict to CPU, then save in background
state_dict_cpu = {k: v.cpu().clone() for k, v in model.state_dict().items()}
thread = threading.Thread(target=save_async, args=(state_dict_cpu, path))
thread.start()
# Training continues immediately
```

**Sharded checkpoints** (PyTorch FSDP / DeepSpeed):
```python
# Each GPU saves its own shard in parallel
# 8 GPUs writing 87.5 GB each at 2 GB/s = 44 seconds (vs 350 seconds serial)
from torch.distributed.checkpoint import save
save(model.state_dict(), checkpoint_id=f"/checkpoints/step_{step}")
```

### Recommended Checkpoint Storage

| Storage Type | Write Speed | Best For |
|-------------|-------------|----------|
| Local NVMe (TopoLVM) | 5-7 GB/s | Fastest saves; risk of data loss on node failure |
| CephFS / GlusterFS (RWX) | 1-5 GB/s | Shared access, multi-node distributed saves |
| JuiceFS (NVMe cache + S3) | 3-7 GB/s local, async to S3 | Best of both: fast writes, durable storage |
| NFS | 0.5-2 GB/s | Simple, widely available; potential bottleneck |

---

## Try This: Measure Your Storage Performance

Run this inside a Pod on your cluster to understand your storage baseline:

```bash
# Create a test pod with your storage class
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: storage-bench
  namespace: default
spec:
  containers:
    - name: bench
      image: ubuntu:22.04
      command: ["sleep", "infinity"]
      volumeMounts:
        - name: test-vol
          mountPath: /data
      resources:
        requests:
          cpu: "4"
          memory: 8Gi
  volumes:
    - name: test-vol
      persistentVolumeClaim:
        claimName: bench-pvc
EOF

# Inside the pod:
kubectl exec -it storage-bench -- bash

apt-get update && apt-get install -y fio

# Sequential read (simulates loading a large dataset)
fio --name=seq-read --rw=read --bs=1M --size=10G \
  --numjobs=4 --direct=1 --directory=/data \
  --runtime=60 --time_based --group_reporting

# Random read (simulates image dataset loading)
fio --name=rand-read --rw=randread --bs=256K --size=10G \
  --numjobs=8 --direct=1 --directory=/data \
  --runtime=60 --time_based --group_reporting \
  --iodepth=32

# Sequential write (simulates checkpoint saves)
fio --name=seq-write --rw=write --bs=1M --size=10G \
  --numjobs=4 --direct=1 --directory=/data \
  --runtime=60 --time_based --group_reporting
```

---

## Did You Know?

1. **ImageNet, the dataset that launched the deep learning revolution, contains 14 million images totaling about 150GB**. But the images are tiny JPEG files (average ~10KB each). This means loading ImageNet requires 14 million random reads — a worst case for any storage system. This is why ImageNet training was one of the first workloads to expose storage bottlenecks in GPU clusters.

2. **The concept of "data gravity" is literal in AI infrastructure**. Moving a 10TB dataset across the internet takes hours to days, but computing on it takes seconds to minutes. This is why cloud providers offer "data import" services where they physically ship hard drives. Google's Transfer Appliance can hold 1 PB and ships via FedEx — sometimes the highest-bandwidth network is a truck full of disks.

3. **Meta reported that during Llama 3 training, their storage system served 240 PB of data over the 54-day run** — roughly 4.4 PB per day, or 51 GB per second sustained. This required a custom distributed filesystem (Tectonic) because no off-the-shelf system could handle this throughput at this scale.

---

## War Story: The Cache That Saved $200K

A medical imaging startup trained models on a 2TB dataset of CT scans stored in Google Cloud Storage (GCS). They had 20 GPU nodes, each running training jobs that loaded the full dataset.

**Before caching**: Each job downloaded 2TB from GCS at ~500 MB/s = 67 minutes startup time. With 20 nodes running 3 jobs/day each, they downloaded **120 TB/day** from GCS.

- GCS egress cost: $0.12/GB × 120,000 GB/day = $14,400/day = **$432,000/month**
- GPU idle time during downloads: 20 nodes × 3 jobs × 67 min = 67 GPU-hours/day wasted

**After JuiceFS with NVMe cache**: First job on each node downloads from GCS (cold cache). Subsequent jobs read from local NVMe cache at 5 GB/s = 7 minutes.

- GCS egress: 20 nodes × 2TB × 1 download/week = 40TB/week = **$19,200/month**
- GPU idle time: negligible (7 min cached vs 67 min uncached)

**Monthly savings**: $432,000 - $19,200 = **$412,800/month**. The caching infrastructure (JuiceFS + NVMe on each node) cost $3,000/month.

**Lesson**: In AI infrastructure, the most impactful optimization is often the simplest: cache the dataset close to the GPUs.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using S3 FUSE mounts for training | FUSE adds 2-10x latency overhead per IO operation | Use JuiceFS or Alluxio with local NVMe cache; or download to local disk first |
| Network storage for ImageNet-style training | Millions of small random reads kill network storage | Cache dataset on local NVMe; or use WebDataset/TFRecord for sequential access |
| Synchronous checkpoints on slow storage | GPUs idle for minutes during each checkpoint save | Use async checkpointing or sharded distributed checkpoints |
| No `noatime` mount option | Every file read triggers a metadata write (access time update) | Always mount with `noatime,nodiratime` for training volumes |
| RWO volumes for multi-node training | ReadWriteOnce cannot be mounted on multiple nodes | Use RWX storage (CephFS, NFS, JuiceFS) or local cache per node |
| Ignoring storage class `volumeBindingMode` | PVC binds to wrong node before Pod is scheduled | Always use `WaitForFirstConsumer` for local storage |
| Not pre-warming cache before training | First epoch runs at cold-cache speed, skewing benchmark results | Use Fluid's `DataLoad` CRD or an init container to warm cache |
| Using ext4 for large files | ext4 fragments large sequential writes | Use XFS for datasets and checkpoint volumes; it handles large files better |

---

## Quiz: Check Your Understanding

### Question 1
Why is storing a dataset of 14 million small images on S3 problematic for GPU training?

<details>
<summary>Show Answer</summary>

Three compounding issues:

1. **Latency**: Each S3 GET request has 10-100ms latency. With 14M random reads, the cumulative latency is enormous even with parallelism.

2. **Request overhead**: S3 is optimized for throughput on large objects, not IOPS on small objects. Each 10KB image requires a full HTTP GET with TLS handshake, authentication, etc. The protocol overhead exceeds the data size.

3. **No prefetching**: S3 has no concept of "read the next file" — each read is independent. Local filesystems and caching layers can prefetch adjacent files, but S3 cannot.

Solutions: (a) Convert to sequential formats like WebDataset or TFRecord, (b) cache on local NVMe with JuiceFS/Alluxio, or (c) download the entire dataset to local storage before training.
</details>

### Question 2
Explain the difference between JuiceFS and Alluxio as caching solutions for AI workloads.

<details>
<summary>Show Answer</summary>

**JuiceFS** is a full POSIX filesystem with caching:
- Separates metadata (Redis/PostgreSQL) from data (any object store)
- Provides a complete filesystem (create, write, read, delete, rename)
- Client-side caching on local NVMe
- Can be used as primary storage, not just a cache layer
- Simpler architecture (no separate master/worker topology)

**Alluxio** is a caching middleware layer:
- Sits between compute and existing storage systems
- Master/worker architecture with distributed cache
- Does not store data itself — always backed by an "under filesystem" (S3, HDFS)
- Richer data management: pinning, TTL, replication policies
- More complex to operate but more features for large-scale deployments

**When to choose which**:
- JuiceFS: when you need a filesystem that also caches, or when simplicity matters
- Alluxio (via Fluid): when you need dataset-aware scheduling, multi-tier caching, or already have complex data infrastructure
</details>

### Question 3
A training job saves a 700GB checkpoint every 1000 steps. Steps take 2 seconds each. Checkpoint save takes 350 seconds on the current storage. What percentage of GPU time is wasted on checkpointing, and how would you reduce it?

<details>
<summary>Show Answer</summary>

**Waste calculation**:
- Steps between checkpoints: 1000 × 2s = 2000s of training
- Checkpoint time: 350s
- Waste: 350 / (2000 + 350) = **14.9%** of total time

**Reduction strategies**:

1. **Sharded checkpoints**: 8 GPUs each save 87.5GB in parallel → 44s instead of 350s → waste drops to 2.1%

2. **Async checkpointing**: Clone state dict to CPU RAM (takes ~10s), save in background thread while training continues → waste drops to ~0.5%

3. **Faster storage**: Local NVMe at 7 GB/s → 100s → waste drops to 4.8%. Combined with sharding: 12.5s → 0.6%

4. **Less frequent checkpoints**: Every 2000 steps instead of 1000 → halves the waste, but doubles max lost work on failure

The best approach combines sharded + async: each GPU clones its shard to CPU, then background threads write to fast storage while training continues. This achieves <1% waste.
</details>

### Question 4
What does Fluid's data-aware scheduling do that a regular PVC does not?

<details>
<summary>Show Answer</summary>

A regular PVC binds to a volume and any node that can access that volume can run the Pod. It has **no awareness of data locality** — a Pod might run on a node that has no cached data, causing a cold-cache start.

Fluid's data-aware scheduling:

1. **Tracks cache location**: Knows which nodes' Alluxio workers have cached which datasets
2. **Prefers warm nodes**: Injects scheduling hints (nodeAffinity) so Pods prefer nodes where their dataset is already cached
3. **Enables pre-warming**: `DataLoad` CRD can prefill cache before Pods start
4. **Manages cache lifecycle**: Evicts stale data, rebalances across workers, manages multi-tier (RAM + SSD) caching
5. **Abstracts the cache engine**: User sees a PVC; Fluid manages Alluxio/JuiceFS/JindoFS underneath
</details>

---

## Hands-On Exercise: JuiceFS Cache Over S3 with Latency Measurement

### Objective

Deploy JuiceFS with a local NVMe cache backed by S3-compatible object storage, load a dataset, and measure the difference between cold-cache and warm-cache read performance.

### Environment

- Kubernetes cluster with at least one node
- MinIO or any S3-compatible storage (we will deploy MinIO for this exercise)
- A node with local storage available (emptyDir is acceptable for the exercise)

### Step 1: Deploy MinIO (S3-compatible Object Store)

```bash
# Install MinIO for local S3-compatible storage
kubectl create namespace storage

cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: storage
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: minio/minio:RELEASE.2024-10-13T13-34-11Z
          args: ["server", "/data", "--console-address", ":9001"]
          env:
            - name: MINIO_ROOT_USER
              value: minioadmin
            - name: MINIO_ROOT_PASSWORD
              value: minioadmin123
          ports:
            - containerPort: 9000
            - containerPort: 9001
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          emptyDir:
            sizeLimit: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: storage
spec:
  ports:
    - port: 9000
      targetPort: 9000
      name: api
    - port: 9001
      targetPort: 9001
      name: console
  selector:
    app: minio
EOF

kubectl -n storage wait --for=condition=Ready pod -l app=minio --timeout=120s
```

### Step 2: Create a Test Dataset in MinIO

```bash
# Create a bucket and upload test data
kubectl -n storage run mc --rm -it --restart=Never \
  --image=minio/mc:RELEASE.2024-10-08T09-37-26Z -- bash -c '
  mc alias set local http://minio:9000 minioadmin minioadmin123
  mc mb local/ai-datasets

  # Create a 1GB test dataset (256 files of 4MB each)
  for i in $(seq 1 256); do
    dd if=/dev/urandom of=/tmp/data_${i}.bin bs=4M count=1 2>/dev/null
    mc cp /tmp/data_${i}.bin local/ai-datasets/training/
    rm /tmp/data_${i}.bin
  done

  echo "Dataset created:"
  mc ls local/ai-datasets/training/ | wc -l
  mc du local/ai-datasets/
'
```

### Step 3: Deploy Redis (JuiceFS Metadata Engine)

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: storage
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: storage
spec:
  ports:
    - port: 6379
  selector:
    app: redis
EOF
```

### Step 4: Install JuiceFS CSI Driver

```bash
helm repo add juicefs https://juicedata.github.io/charts/
helm repo update

# Create the JuiceFS secret
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: juicefs-secret
  namespace: storage
type: Opaque
stringData:
  name: ai-data
  metaurl: redis://redis.storage.svc:6379/1
  storage: s3
  bucket: http://minio.storage.svc:9000/ai-datasets
  access-key: minioadmin
  secret-key: minioadmin123
EOF

# Install the CSI driver
helm install juicefs-csi juicefs/juicefs-csi-driver \
  --namespace kube-system \
  --version v0.24.8
```

### Step 5: Create JuiceFS StorageClass and PVC

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: juicefs-cache
provisioner: csi.juicefs.com
parameters:
  csi.storage.k8s.io/provisioner-secret-name: juicefs-secret
  csi.storage.k8s.io/provisioner-secret-namespace: storage
  csi.storage.k8s.io/node-publish-secret-name: juicefs-secret
  csi.storage.k8s.io/node-publish-secret-namespace: storage
  juicefs/mount-options: "cache-size=10240,buffer-size=512"
reclaimPolicy: Delete
volumeBindingMode: Immediate
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: juicefs-data
  namespace: storage
spec:
  storageClassName: juicefs-cache
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 20Gi
EOF
```

### Step 6: Measure Cold vs Warm Cache Performance

```bash
cat <<'BENCHEOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: cache-benchmark
  namespace: storage
spec:
  containers:
    - name: bench
      image: ubuntu:22.04
      command: ["bash", "-c"]
      args:
        - |
          apt-get update -qq && apt-get install -y -qq time bc 2>/dev/null

          echo "=== COLD CACHE READ (first access, data fetched from S3) ==="
          sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

          cold_start=$(date +%s%N)
          total_bytes=0
          for f in /data/training/data_*.bin; do
            cat "$f" > /dev/null 2>&1
            total_bytes=$((total_bytes + $(stat -c%s "$f" 2>/dev/null || echo 0)))
          done
          cold_end=$(date +%s%N)

          cold_ms=$(( (cold_end - cold_start) / 1000000 ))
          cold_mbps=$(echo "scale=2; $total_bytes / 1048576 / ($cold_ms / 1000)" | bc 2>/dev/null || echo "N/A")
          echo "Cold read: ${cold_ms}ms for $(echo "$total_bytes / 1048576" | bc)MB = ${cold_mbps} MB/s"
          echo ""

          echo "=== WARM CACHE READ (second access, data from local cache) ==="
          warm_start=$(date +%s%N)
          for f in /data/training/data_*.bin; do
            cat "$f" > /dev/null 2>&1
          done
          warm_end=$(date +%s%N)

          warm_ms=$(( (warm_end - warm_start) / 1000000 ))
          warm_mbps=$(echo "scale=2; $total_bytes / 1048576 / ($warm_ms / 1000)" | bc 2>/dev/null || echo "N/A")
          echo "Warm read: ${warm_ms}ms for $(echo "$total_bytes / 1048576" | bc)MB = ${warm_mbps} MB/s"
          echo ""

          speedup=$(echo "scale=1; $cold_ms / $warm_ms" | bc 2>/dev/null || echo "N/A")
          echo "=== RESULT: Warm cache is ${speedup}x faster than cold ==="

          sleep 3600
      volumeMounts:
        - name: data
          mountPath: /data
      resources:
        requests:
          cpu: "2"
          memory: 4Gi
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: juicefs-data
  restartPolicy: Never
BENCHEOF

# Wait and check results
kubectl -n storage wait --for=condition=Ready pod/cache-benchmark --timeout=300s
sleep 60
kubectl -n storage logs cache-benchmark
```

### Step 7: Cleanup

```bash
kubectl delete namespace storage
```

### Success Criteria

You have completed this exercise when:
- [ ] MinIO is running and contains a 1GB test dataset (256 files)
- [ ] Redis metadata engine is running
- [ ] JuiceFS CSI driver is installed and StorageClass is created
- [ ] PVC is bound and mountable
- [ ] Cold cache read time is measured (expect: 30-120 seconds for 1GB)
- [ ] Warm cache read time is measured (expect: 2-10 seconds for 1GB)
- [ ] Warm cache read is at least 3x faster than cold cache read
- [ ] You can explain why the speedup occurs (local NVMe/memory vs S3 network round-trip)

---

## Key Takeaways

1. **IO is the most common bottleneck in GPU training** — if GPU utilization is below 80%, investigate storage first
2. **Local NVMe is 10-50x faster than network storage** for the random small-file reads that image training demands
3. **JuiceFS bridges the gap** between object storage (cheap, durable, slow) and local NVMe (fast, ephemeral)
4. **Fluid/Alluxio add data-aware scheduling** — Pods prefer nodes that already have their dataset cached
5. **Checkpointing must be fast** — synchronous saves to slow storage can waste 15%+ of GPU time; use sharded async checkpoints
6. **Mount with `noatime`** — a one-line fix that eliminates unnecessary metadata writes on every file read
7. **Measure before optimizing** — use `fio` to benchmark your storage and `nvidia-smi` to correlate with GPU utilization
8. **The init container pattern** for data staging is simple, reliable, and often sufficient for datasets under 1TB

---

## Further Reading

**Documentation**:
- **JuiceFS**: juicefs.com/docs/
- **Fluid**: github.com/fluid-cloudnative/fluid
- **Alluxio**: docs.alluxio.io
- **TopoLVM**: github.com/topolvm/topolvm
- **Rook-Ceph**: rook.io/docs/rook/latest/

**Papers**:
- **"Analyzing and Mitigating Data Stalls in DNN Training"** — Jayaram et al. (IO bottleneck analysis)
- **"CoorDL: Coordinated and Progressive Data Loading for Deep Learning"** — Mohan et al.

**Talks**:
- **"Building a Petabyte-Scale AI Data Platform on Kubernetes"** — KubeCon EU 2024
- **"JuiceFS: A Cloud-Native Distributed File System for AI Workloads"** — CNCF Webinar

---

## Summary

Storage is the hidden bottleneck that prevents expensive GPUs from reaching their potential. A multi-tier approach — local NVMe for hot data, distributed filesystem for warm data, object storage for cold data — combined with intelligent caching (JuiceFS, Fluid/Alluxio) bridges the 1,000x performance gap between GPU memory and network storage. Fast checkpoint storage with async and sharded writes minimizes GPU idle time during saves. Measure, cache, and measure again.

---

## Next Module

Continue to [Module 1.5: Serving LLMs at Scale](module-1.5-llm-serving/) to learn how to deploy large language models for inference with vLLM, continuous batching, and KEDA autoscaling.

---

*"Data is the new oil, but storage is the pipeline. A clogged pipeline makes the oil worthless."* — Anonymous infrastructure engineer

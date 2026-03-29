---
title: "Module 16.1: Rook/Ceph - Enterprise Storage for Kubernetes"
slug: platform/toolkits/infrastructure-networking/storage/module-16.1-rook-ceph
sidebar:
  order: 2
---
## Complexity: [COMPLEX]
## Time to Complete: 55-65 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Distributed Systems Foundation](../../foundations/distributed-systems/) - Replication, consistency
- [Reliability Engineering Foundation](../../foundations/reliability-engineering/) - SLOs, failure modes
- Kubernetes fundamentals (PVCs, StorageClasses, CSI, StatefulSets)
- Basic Linux storage concepts (block devices, filesystems)

---

## Why This Module Matters

**The $3.8 Million Bare-Metal Bet**

The storage engineering team at a European financial services company stared at their AWS bill. They were spending $4.1 million per year on EBS volumes alone. Their 200-node Kubernetes cluster ran databases, analytics pipelines, and compliance archives that collectively consumed 800TB of persistent storage.

The CTO had approved a bare-metal migration to three on-premise datacenters for regulatory reasons. But there was a problem: who provides the storage when there is no cloud provider?

| Before (AWS EBS) | After (Rook/Ceph) |
|-------------------|--------------------|
| EBS gp3 volumes: $3.2M/year | Hardware (amortized 3yr): $1.1M/year |
| EBS snapshots: $480K/year | Ceph S3 (RGW) for backups: included |
| S3 for objects: $420K/year | CephFS for shared data: included |
| **Total storage cost** | **$4.1M/year → $1.1M/year** |
| Storage types | Block, FS, Object from one platform |
| Multi-AZ replication | 3x replication across datacenters |
| Vendor lock-in | Portable across any infrastructure |

The migration took four months. The Rook operator automated what previously required a dedicated storage team of three engineers. Six months later, the cluster was running 1.2PB across all three datacenters with zero data loss incidents.

**Rook turns Ceph—the most battle-tested distributed storage system in existence—into a Kubernetes-native service. One operator, three storage types, and the same storage platform that powers CERN's 600PB of physics data.**

---

## Did You Know?

- **CERN runs over 600 petabytes on Ceph** — The world's largest physics experiments generate roughly 1 GB/second of data. Ceph has been their primary storage platform since 2013, surviving hardware failures daily without a single byte lost. When particle physicists trust it with irreplaceable data about the universe, your production databases are in good hands.

- **Rook was the first storage project to graduate from the CNCF** — Accepted in 2018 and graduated in 2020, Rook proved that complex distributed storage could be tamed by Kubernetes operators. The Rook operator manages the entire Ceph lifecycle: deployment, scaling, upgrades, and self-healing—tasks that previously required dedicated storage engineers.

- **A single Ceph cluster can serve block, filesystem, AND object storage simultaneously** — Most storage solutions do one thing. Ceph provides RBD (block volumes for databases), CephFS (shared POSIX filesystem for ML training data), and RGW (S3-compatible object storage for backups)—all from the same pool of disks. One platform replaces three separate storage systems.

- **Bloomberg runs Rook/Ceph across thousands of nodes** — Their financial data platform uses Rook/Ceph to provide storage for analytics workloads on bare-metal Kubernetes. The combination of performance, reliability, and the ability to run on-premise (critical for financial data sovereignty) made it the clear choice over cloud storage.

---

## Ceph Architecture

Before understanding Rook, you need to understand what it manages. Ceph is a distributed storage system with four core daemon types:

```
CEPH ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                       CEPH CLUSTER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MONITORS (MON) - The Brain                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Maintain cluster map (what data is where)              │  │
│  │  • Paxos consensus for high availability                  │  │
│  │  • Minimum 3 MONs (odd number required)                   │  │
│  │  • Lightweight—no data flows through MONs                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  OBJECT STORAGE DAEMONS (OSD) - The Muscle                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • One OSD per physical disk (SSD/HDD)                    │  │
│  │  • Stores actual data as objects                          │  │
│  │  • Handles replication between OSDs                       │  │
│  │  • Self-healing: re-replicates when peers fail            │  │
│  │  • Uses BlueStore engine (direct disk, no filesystem)     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│              ┌─────────────┼─────────────┐                      │
│              │             │             │                       │
│              ▼             ▼             ▼                       │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │  MDS          │ │  RGW          │ │  MGR          │         │
│  │  (Metadata    │ │  (RADOS       │ │  (Manager)    │         │
│  │   Server)     │ │   Gateway)    │ │               │         │
│  │               │ │               │ │  • Dashboard  │         │
│  │  Required for │ │  S3/Swift     │ │  • Prometheus │         │
│  │  CephFS only  │ │  compatible   │ │    metrics    │         │
│  │               │ │  object API   │ │  • Modules    │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
│                                                                  │
│  DATA FLOW (CRUSH algorithm):                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Client → CRUSH map → OSD primary → Replicate to 2 OSDs  │  │
│  │                                                            │  │
│  │  No central bottleneck! Clients calculate placement        │  │
│  │  directly using the CRUSH algorithm.                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The CRUSH Algorithm

What makes Ceph special is CRUSH (Controlled Replication Under Scalable Hashing). Instead of a central metadata server that becomes a bottleneck, every client computes where data lives using the same deterministic algorithm:

```
CRUSH - HOW CEPH DISTRIBUTES DATA
─────────────────────────────────────────────────────────────────

Traditional Storage:        Ceph with CRUSH:
┌────────┐                  ┌────────┐
│ Client │                  │ Client │
└───┬────┘                  └───┬────┘
    │                           │
    ▼                           │  CRUSH(object_id, cluster_map)
┌────────┐                     │  = OSD 7 (primary)
│Metadata│ ← bottleneck!       │  = OSD 12, OSD 3 (replicas)
│ Server │                     │
└───┬────┘                     ├──────────────────┐
    │                          │                  │
    ▼                          ▼                  ▼
┌──────────┐            ┌──────────┐       ┌──────────┐
│ Storage  │            │  OSD 7   │       │  OSD 12  │
│ Nodes    │            │ (primary)│       │ (replica)│
└──────────┘            └──────────┘       └──────────┘

No single point of failure for metadata lookups.
Clients talk directly to OSDs.
Adding/removing OSDs = minimal data movement.
```

---

## Rook: The Kubernetes Operator for Ceph

Rook translates Ceph's complexity into Kubernetes-native Custom Resources:

```
ROOK OPERATOR ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   ROOK OPERATOR                             │  │
│  │                                                             │  │
│  │  Watches CRDs:                                              │  │
│  │  • CephCluster      → Deploys MON, MGR, OSD                │  │
│  │  • CephBlockPool    → Creates RBD pool + StorageClass       │  │
│  │  • CephFilesystem   → Deploys MDS + creates CephFS          │  │
│  │  • CephObjectStore  → Deploys RGW + S3 endpoint             │  │
│  │  • CephObjectStoreUser → Creates S3 access credentials      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│              ┌─────────────┼─────────────┐                      │
│              ▼             ▼             ▼                       │
│  ┌────────────────┐ ┌──────────┐ ┌──────────────────┐          │
│  │  CSI Driver    │ │ Ceph     │ │ Ceph Dashboard   │          │
│  │  (rook-ceph-  │ │ Cluster  │ │ (Web UI)         │          │
│  │   csi plugin)  │ │ Daemons  │ │                  │          │
│  │                │ │          │ │  Port 8443       │          │
│  │  Provisions   │ │ MON ×3   │ │  Health, perf,   │          │
│  │  PVCs via     │ │ MGR ×2   │ │  capacity        │          │
│  │  StorageClass │ │ OSD ×N   │ │                  │          │
│  └────────────────┘ └──────────┘ └──────────────────┘          │
│                                                                  │
│  THREE STORAGE TYPES FROM ONE CLUSTER:                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Block (RBD)  │ │ Filesystem   │ │ Object (RGW) │            │
│  │              │ │ (CephFS)     │ │              │            │
│  │ ReadWrite-   │ │ ReadWrite-   │ │ S3-compatible│            │
│  │ Once PVCs    │ │ Many PVCs    │ │ API endpoint │            │
│  │              │ │              │ │              │            │
│  │ Databases,   │ │ ML training, │ │ Backups,     │            │
│  │ StatefulSets │ │ shared logs  │ │ artifacts    │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation via Helm

### Step 1: Install the Rook Operator

```bash
# Add the Rook Helm repository
helm repo add rook-release https://charts.rook.io/release
helm repo update

# Install the Rook operator
helm install --create-namespace --namespace rook-ceph \
  rook-ceph rook-release/rook-ceph \
  --version v1.15.0 \
  --set csi.enableRbdDriver=true \
  --set csi.enableCephfsDriver=true

# Wait for operator to be ready
kubectl -n rook-ceph rollout status deployment/rook-ceph-operator
```

### Step 2: Deploy the Ceph Cluster

```yaml
# ceph-cluster.yaml
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata:
  name: rook-ceph
  namespace: rook-ceph
spec:
  cephVersion:
    image: quay.io/ceph/ceph:v19.2
    allowUnsupported: false
  dataDirHostPath: /var/lib/rook
  mon:
    count: 3                    # Always odd number
    allowMultiplePerNode: false # One MON per node for HA
  mgr:
    count: 2                    # Active + standby
    modules:
      - name: dashboard
        enabled: true
      - name: prometheus
        enabled: true
  dashboard:
    enabled: true
    ssl: true
  storage:
    useAllNodes: true
    useAllDevices: true         # Rook will use all available raw devices
    # Or specify devices explicitly:
    # nodes:
    #   - name: "worker-1"
    #     devices:
    #       - name: "sdb"
    #       - name: "sdc"
  resources:
    mon:
      requests:
        cpu: "500m"
        memory: "1Gi"
    osd:
      requests:
        cpu: "500m"
        memory: "2Gi"
    mgr:
      requests:
        cpu: "250m"
        memory: "512Mi"
```

```bash
kubectl apply -f ceph-cluster.yaml

# Monitor deployment progress
kubectl -n rook-ceph get pods -w
# Wait until all MON, MGR, and OSD pods are Running
```

### Step 3: Create a Block Pool and StorageClass

```yaml
# ceph-block-pool.yaml
apiVersion: ceph.rook.io/v1
kind: CephBlockPool
metadata:
  name: replicapool
  namespace: rook-ceph
spec:
  failureDomain: host          # Replicas on different hosts
  replicated:
    size: 3                    # 3 copies of every block
    requireSafeReplicaSize: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-ceph-block
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  clusterID: rook-ceph
  pool: replicapool
  imageFormat: "2"
  imageFeatures: layering
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-rbd-provisioner
  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
reclaimPolicy: Delete
allowVolumeExpansion: true
```

### Step 4: Create a Shared Filesystem (CephFS)

```yaml
# ceph-filesystem.yaml
apiVersion: ceph.rook.io/v1
kind: CephFilesystem
metadata:
  name: ceph-shared
  namespace: rook-ceph
spec:
  metadataPool:
    replicated:
      size: 3
  dataPools:
    - name: data0
      replicated:
        size: 3
  metadataServer:
    activeCount: 1             # Active MDS instances
    activeStandby: true        # Standby for failover
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-cephfs
provisioner: rook-ceph.cephfs.csi.ceph.com
parameters:
  clusterID: rook-ceph
  fsName: ceph-shared
  pool: ceph-shared-data0
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-cephfs-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-cephfs-provisioner
  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-cephfs-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
reclaimPolicy: Delete
allowVolumeExpansion: true
```

### Step 5: Create an Object Store (S3-Compatible)

```yaml
# ceph-object-store.yaml
apiVersion: ceph.rook.io/v1
kind: CephObjectStore
metadata:
  name: ceph-objectstore
  namespace: rook-ceph
spec:
  metadataPool:
    failureDomain: host
    replicated:
      size: 3
  dataPool:
    failureDomain: host
    replicated:
      size: 3
  gateway:
    type: s3
    port: 80
    instances: 2               # RGW instances for HA
    resources:
      requests:
        cpu: "500m"
        memory: "512Mi"
---
# Create S3 user credentials
apiVersion: ceph.rook.io/v1
kind: CephObjectStoreUser
metadata:
  name: s3-user
  namespace: rook-ceph
spec:
  store: ceph-objectstore
  displayName: "S3 User"
```

---

## Using Rook/Ceph Storage

### Block Storage (RBD) for Databases

```yaml
# postgres-with-rook-block.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce            # Block = single pod access
  storageClassName: rook-ceph-block
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_PASSWORD
              value: "secretpassword"
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: postgres-data
```

### Shared Filesystem (CephFS) for ML Training

```yaml
# ml-shared-data.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: training-data
spec:
  accessModes:
    - ReadWriteMany            # CephFS = multiple pods can read/write
  storageClassName: rook-cephfs
  resources:
    requests:
      storage: 100Gi
---
# Multiple training pods can mount the same volume
apiVersion: batch/v1
kind: Job
metadata:
  name: training-worker
spec:
  parallelism: 4               # 4 workers share the same data
  template:
    spec:
      containers:
        - name: trainer
          image: pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
          command: ["python", "train.py", "--data-dir=/data"]
          volumeMounts:
            - name: shared-data
              mountPath: /data
      restartPolicy: Never
      volumes:
        - name: shared-data
          persistentVolumeClaim:
            claimName: training-data
```

### Object Storage (RGW) Access

```bash
# Get S3 credentials from the secret Rook creates
kubectl -n rook-ceph get secret rook-ceph-object-user-ceph-objectstore-s3-user \
  -o jsonpath='{.data.AccessKey}' | base64 --decode
kubectl -n rook-ceph get secret rook-ceph-object-user-ceph-objectstore-s3-user \
  -o jsonpath='{.data.SecretKey}' | base64 --decode

# Get the RGW endpoint
kubectl -n rook-ceph get svc rook-ceph-rgw-ceph-objectstore

# Use AWS CLI or any S3-compatible tool
export AWS_ACCESS_KEY_ID=<access-key>
export AWS_SECRET_ACCESS_KEY=<secret-key>
export AWS_ENDPOINT_URL=http://rook-ceph-rgw-ceph-objectstore.rook-ceph.svc

aws s3 mb s3://my-backups --endpoint-url $AWS_ENDPOINT_URL
aws s3 cp backup.tar.gz s3://my-backups/ --endpoint-url $AWS_ENDPOINT_URL
```

---

## Monitoring Rook/Ceph

```bash
# Check Ceph cluster health
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status

# Check OSD status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd status

# Check pool usage
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph df

# Access Ceph Dashboard
kubectl -n rook-ceph get secret rook-ceph-dashboard-password \
  -o jsonpath='{.data.password}' | base64 --decode
kubectl -n rook-ceph port-forward svc/rook-ceph-mgr-dashboard 8443:8443
# Open https://localhost:8443 (user: admin)
```

```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: rook-ceph-mgr
  namespace: rook-ceph
spec:
  selector:
    matchLabels:
      app: rook-ceph-mgr
      rook_cluster: rook-ceph
  endpoints:
    - port: http-metrics
      path: /metrics
      interval: 15s
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Running MONs on fewer than 3 nodes | Loses quorum if one MON fails | Always 3 or 5 MONs on separate nodes |
| Using `useAllDevices: true` in production blindly | May consume OS disks | Explicitly list devices per node |
| Skipping `failureDomain: host` | Replicas may land on same node | Set failure domain to `host` or `zone` |
| No resource limits on OSDs | OSD compaction starves other pods | Set CPU and memory requests/limits |
| Ignoring `HEALTH_WARN` status | Warns become errors under load | Investigate and resolve all warnings |
| Not deploying the Ceph toolbox | Cannot debug storage issues | Deploy `rook-ceph-tools` pod always |
| Provisioning erasure coding for small clusters | Needs minimum 4 nodes, slower writes | Use replication for clusters under 10 nodes |
| Forgetting volume expansion | PVCs fill up and workloads crash | Enable `allowVolumeExpansion: true` in StorageClass |

---

## Hands-On Exercise

### Task: Deploy Rook/Ceph on kind and Provision Storage

**Objective**: Deploy a Rook/Ceph cluster on a local kind cluster, create block and filesystem StorageClasses, and provision PVCs that workloads can consume.

**Success Criteria**:
1. Rook operator and Ceph cluster running
2. Block StorageClass provisioning PVCs
3. CephFS StorageClass with ReadWriteMany access
4. A pod successfully writing data to a Ceph-backed PVC
5. Ceph health check returns HEALTH_OK

### Steps

```bash
# 1. Create a kind cluster with 3 workers (extra mounts for OSD emulation)
cat > kind-rook-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
  - role: worker
EOF

kind create cluster --name rook-lab --config kind-rook-config.yaml

# 2. Install the Rook operator
helm repo add rook-release https://charts.rook.io/release
helm repo update

helm install --create-namespace --namespace rook-ceph \
  rook-ceph rook-release/rook-ceph \
  --version v1.15.0

kubectl -n rook-ceph rollout status deployment/rook-ceph-operator --timeout=300s

# 3. Deploy CephCluster (using directory-based storage for kind — no raw disks)
cat > ceph-cluster-kind.yaml << 'EOF'
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata:
  name: rook-ceph
  namespace: rook-ceph
spec:
  cephVersion:
    image: quay.io/ceph/ceph:v19.2
    allowUnsupported: true
  dataDirHostPath: /var/lib/rook
  mon:
    count: 3
    allowMultiplePerNode: true   # Required for kind (3 workers)
  mgr:
    count: 1
  dashboard:
    enabled: true
  storage:
    useAllNodes: true
    useAllDevices: false
    directories:
      - path: /var/lib/rook-osd   # Directory-based OSDs for kind
EOF

kubectl apply -f ceph-cluster-kind.yaml

echo "Waiting for Ceph cluster to come up (this takes 3-5 minutes)..."
kubectl -n rook-ceph wait --for=condition=Ready cephcluster/rook-ceph --timeout=600s

# 4. Deploy the Ceph toolbox for debugging
kubectl apply -f https://raw.githubusercontent.com/rook/rook/release-1.15/deploy/examples/toolbox.yaml

# 5. Create a Block Pool and StorageClass
cat > ceph-block.yaml << 'EOF'
apiVersion: ceph.rook.io/v1
kind: CephBlockPool
metadata:
  name: replicapool
  namespace: rook-ceph
spec:
  failureDomain: host
  replicated:
    size: 2                      # 2 replicas for kind (limited nodes)
    requireSafeReplicaSize: false
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-ceph-block
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  clusterID: rook-ceph
  pool: replicapool
  imageFormat: "2"
  imageFeatures: layering
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
reclaimPolicy: Delete
allowVolumeExpansion: true
EOF

kubectl apply -f ceph-block.yaml

# 6. Create a CephFS Filesystem and StorageClass
cat > ceph-fs.yaml << 'EOF'
apiVersion: ceph.rook.io/v1
kind: CephFilesystem
metadata:
  name: ceph-shared
  namespace: rook-ceph
spec:
  metadataPool:
    replicated:
      size: 2
  dataPools:
    - name: data0
      replicated:
        size: 2
  metadataServer:
    activeCount: 1
    activeStandby: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-cephfs
provisioner: rook-ceph.cephfs.csi.ceph.com
parameters:
  clusterID: rook-ceph
  fsName: ceph-shared
  pool: ceph-shared-data0
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-cephfs-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-cephfs-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
reclaimPolicy: Delete
allowVolumeExpansion: true
EOF

kubectl apply -f ceph-fs.yaml

# 7. Provision a Block PVC and run a pod that writes data
cat > test-block-pvc.yaml << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: rook-ceph-block
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: block-test
spec:
  containers:
    - name: writer
      image: busybox
      command: ["sh", "-c"]
      args:
        - |
          echo "Writing data to Rook/Ceph block volume..."
          dd if=/dev/urandom of=/data/testfile bs=1M count=100
          echo "Wrote 100MB to /data/testfile"
          md5sum /data/testfile
          echo "Block storage test PASSED"
          sleep 3600
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: test-block-pvc
EOF

kubectl apply -f test-block-pvc.yaml
kubectl wait --for=condition=Ready pod/block-test --timeout=120s
kubectl logs block-test

# 8. Verify Ceph cluster health
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph df
```

### Verification

```bash
# Confirm PVC is bound
kubectl get pvc test-block-pvc
# STATUS should be "Bound"

# Confirm pod wrote data successfully
kubectl logs block-test | grep "PASSED"

# Confirm Ceph health
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph health
# Should output: HEALTH_OK (or HEALTH_WARN with explanation in kind)

# Confirm StorageClasses exist
kubectl get storageclass | grep rook

# Clean up
kind delete cluster --name rook-lab
```

---

## Quiz

### Question 1
What are the four core Ceph daemon types, and what does each one do?

<details>
<summary>Show Answer</summary>

**MON (Monitor)**, **OSD (Object Storage Daemon)**, **MDS (Metadata Server)**, and **MGR (Manager)**.

- **MON**: Maintains the cluster map and uses Paxos consensus. Required for cluster operation.
- **OSD**: One per disk, stores actual data, handles replication between peers.
- **MDS**: Required only for CephFS. Manages POSIX filesystem metadata (directory hierarchy, permissions).
- **MGR**: Provides dashboard, Prometheus metrics, and plugin modules. Active/standby for HA.
</details>

### Question 2
What is the CRUSH algorithm, and why does it matter for performance?

<details>
<summary>Show Answer</summary>

**CRUSH (Controlled Replication Under Scalable Hashing)** is a deterministic algorithm that computes data placement without a central metadata server.

It matters because clients calculate which OSD holds their data locally, then talk directly to that OSD. There is no metadata lookup bottleneck, which means Ceph scales linearly—adding more OSDs increases throughput proportionally. This is fundamentally different from storage systems that route all requests through a central controller.
</details>

### Question 3
What three types of storage can Rook/Ceph provide from a single cluster?

<details>
<summary>Show Answer</summary>

1. **Block storage (RBD)** — ReadWriteOnce volumes for databases and StatefulSets. Provisioned via `rook-ceph.rbd.csi.ceph.com`.
2. **Shared filesystem (CephFS)** — ReadWriteMany volumes for shared data across multiple pods. Requires MDS daemons.
3. **Object storage (RGW)** — S3-compatible API for backups, artifacts, and unstructured data. Deploys RADOS Gateway pods.
</details>

### Question 4
Why should you always deploy an odd number of Ceph Monitors?

<details>
<summary>Show Answer</summary>

Ceph Monitors use **Paxos consensus**, which requires a majority (quorum) to make decisions. With an odd number:
- 3 MONs: survives 1 failure (2/3 quorum)
- 5 MONs: survives 2 failures (3/5 quorum)

An even number (e.g., 4) wastes a node because it still only survives 1 failure (needs 3/4 for quorum)—the same as 3 MONs. Odd numbers maximize fault tolerance per MON deployed.
</details>

### Question 5
When would you choose CephFS over RBD?

<details>
<summary>Show Answer</summary>

Choose **CephFS** when you need **ReadWriteMany (RWX)** access—multiple pods reading and writing to the same volume simultaneously. Common use cases:

- ML training jobs where multiple workers read the same dataset
- Shared configuration or log directories
- Content management systems with shared media storage

Choose **RBD** when you need **ReadWriteOnce (RWO)**—a dedicated volume for a single pod, which offers better performance for databases and single-writer workloads.
</details>

---

## Key Takeaways

1. **Ceph is battle-tested** — Powers CERN, Bloomberg, and thousands of production deployments at petabyte scale
2. **Rook makes Ceph manageable** — Kubernetes operator automates deployment, scaling, upgrades, and self-healing
3. **Three storage types from one cluster** — Block (RBD), filesystem (CephFS), and object (RGW) all from the same pool of disks
4. **CRUSH eliminates bottlenecks** — No central metadata server; clients compute placement directly
5. **Minimum 3 nodes** — MONs and OSDs need separate failure domains for real HA
6. **High operational complexity** — Most powerful option, but requires understanding Ceph internals for production
7. **CSI-native** — Standard Kubernetes StorageClass and PVC workflow; applications never know they're using Ceph

---

## Next Steps

- **Next Module**: [Module 16.2: MinIO](module-16.2-minio/) — S3-compatible object storage on Kubernetes
- **Related**: [Cloud-Native Databases](../cloud-native-databases/) — Databases that run on Ceph storage
- **Related**: [Observability Toolkit](../observability/) — Monitoring storage with Prometheus

---

## Further Reading

- [Rook Documentation](https://rook.io/docs/rook/latest/)
- [Ceph Documentation](https://docs.ceph.com/)
- [Rook GitHub Repository](https://github.com/rook/rook)
- [CRUSH: Controlled, Scalable, Decentralized Placement (Paper)](https://ceph.com/assets/pdfs/weil-crush-sc06.pdf)
- [Data on Kubernetes Community](https://dok.community/)

---

*"Rook/Ceph is the Swiss Army knife of Kubernetes storage. It does everything—block, filesystem, object—but like a Swiss Army knife, you need to know which blade to use and when."*

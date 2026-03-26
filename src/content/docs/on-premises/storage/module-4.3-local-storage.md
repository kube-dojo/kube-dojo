---
title: "Module 4.3: Local Storage & Alternatives"
slug: on-premises/storage/module-4.3-local-storage
sidebar:
  order: 4
---

> **Complexity**: `[INTERMEDIATE]` | Time: 45 minutes
>
> **Prerequisites**: [Module 4.1: Storage Architecture](module-4.1-storage-architecture/), [Module 4.2: Ceph & Rook](module-4.2-ceph-rook/)

---

## Why This Module Matters

A fintech startup ran six microservices on three bare-metal servers. They deployed Rook-Ceph because "everyone uses Ceph." Within a week, the Ceph monitors consumed 2 GB of RAM each, the OSD recovery traffic saturated their 10 GbE links during a node reboot, and a junior engineer accidentally deleted the mon keyring while debugging. Total downtime: 14 hours.

They replaced Ceph with Longhorn. Deployment took 20 minutes. Each microservice got a 3-replica volume backed by local NVMe. The total storage overhead dropped from 9 pods (3 MONs, 3 MGRs, 3 OSDs) to a single DaemonSet. Six months later, they have had zero storage incidents.

Not every on-premises cluster needs a distributed storage system. If your workloads are stateless, or if each pod can tolerate node-local storage that disappears when the node dies, local storage solutions are simpler, faster, and cheaper. Even when you need replication, lightweight alternatives like Longhorn and OpenEBS provide it without the operational complexity of Ceph.

This module covers the full spectrum: from zero-overhead local-path-provisioner to replicated-but-simple Longhorn, with LVM-based solutions in between.

---

## What You'll Learn

- When local storage is the right choice (and when it is not)
- local-path-provisioner for development and ephemeral workloads
- TopoLVM and LVM CSI for production local volumes with topology awareness
- OpenEBS local engines (LocalPV-HostPath, LocalPV-LVM, LocalPV-ZFS)
- Longhorn for replicated storage without Ceph complexity
- Topology-aware provisioning and scheduler constraints
- Decision framework for choosing the right storage solution

---

## The Local Storage Spectrum

```
┌─────────────────────────────────────────────────────────────────────┐
│                  LOCAL STORAGE SPECTRUM                              │
│                                                                      │
│   Simplest                                                 Most     │
│   ─────────────────────────────────────────────────> Capable        │
│                                                                      │
│   hostPath      local-path     LVM CSI     OpenEBS     Longhorn    │
│   (manual)      provisioner    TopoLVM     LocalPV     (replicated)│
│                                                                      │
│   No CSI        CSI driver     LVM thin    LVM/ZFS    Cross-node   │
│   No dynamic    Dynamic PV     Snapshots   Snapshots   replication  │
│   No cleanup    Auto cleanup   Quota       Quota       Snapshots    │
│   ───────       ───────────    ─────────   ─────────   ──────────  │
│   Dev only      Dev / Edge     Production  Production  Production  │
│                                                                      │
│   Risk: data on one node. Node failure = volume gone.              │
│   Exception: Longhorn replicates across nodes.                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## local-path-provisioner

Rancher's local-path-provisioner is the simplest dynamic provisioner. It creates a directory on the node's filesystem and binds it to a PV. No LVM, no snapshots, no replication. Just a directory.

### When to Use

- Development clusters (kind, k3s, single-node labs)
- Edge deployments where simplicity outweighs durability
- Workloads that already handle their own replication (etcd, CockroachDB, Kafka)

### How It Works

```
┌──────────────────────────────────────────┐
│  Node: worker-01                          │
│                                           │
│  /opt/local-path-provisioner/             │
│  ├── pvc-abc123/    (PV for Pod A)       │
│  ├── pvc-def456/    (PV for Pod B)       │
│  └── pvc-ghi789/    (PV for Pod C)       │
│                                           │
│  PVC created ──> Provisioner creates dir  │
│  PVC deleted ──> Provisioner deletes dir  │
│  Pod scheduled ──> Must land on this node │
└──────────────────────────────────────────┘
```

### Deployment

```bash
# Install local-path-provisioner
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.30/deploy/local-path-storage.yaml

# Create a PVC (stays Pending until a Pod references it)
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-local
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: local-path
  resources:
    requests:
      storage: 1Gi
EOF
```

**Key limitation**: The PVC has no actual size enforcement. You requested 1 Gi but nothing prevents the pod from using the entire node disk. For real quota enforcement, use LVM-based solutions.

---

## TopoLVM: Production-Grade Local Volumes

TopoLVM uses LVM (Logical Volume Manager) to carve local disks into thin-provisioned volumes with actual capacity enforcement. It integrates with the Kubernetes scheduler via a mutating webhook to ensure pods land on nodes that have enough free space.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TopoLVM ARCHITECTURE                     │
│                                                               │
│   ┌───────────────┐         ┌───────────────┐              │
│   │ kube-scheduler │ ◄──── │ topolvm-sched  │              │
│   │  (filter/score)│        │  (webhook)     │              │
│   └───────────────┘         └───────────────┘              │
│          │                                                    │
│          │ Schedule pod to node with enough VG space         │
│          ▼                                                    │
│   ┌───────────────┐         ┌───────────────┐              │
│   │  topolvm-node │ ◄──── │ topolvm-csi    │              │
│   │  (DaemonSet)  │        │  (controller)  │              │
│   │               │        │                │              │
│   │ Reports VG    │        │ Creates LVs    │              │
│   │ free space to │        │ via CSI calls  │              │
│   │ scheduler     │        │                │              │
│   └───────────────┘         └───────────────┘              │
│          │                                                    │
│          ▼                                                    │
│   ┌───────────────┐                                         │
│   │  LVM VG       │  Volume Group on local NVMe/SSD        │
│   │  ├── lv-pvc1  │  Thin-provisioned logical volumes      │
│   │  ├── lv-pvc2  │  Actual capacity enforcement           │
│   │  └── lv-pvc3  │  Snapshots supported                   │
│   └───────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

### Setup

```bash
# Prerequisite: Create an LVM Volume Group on each worker node
# (run on each node via SSH or DaemonSet)
pvcreate /dev/nvme1n1
vgcreate myvg /dev/nvme1n1

# Install TopoLVM via Helm
helm repo add topolvm https://topolvm.github.io/topolvm
helm install topolvm topolvm/topolvm \
  --namespace topolvm-system --create-namespace \
  --set storageClasses[0].name=topolvm-provisioner \
  --set storageClasses[0].volumeGroup=myvg \
  --set storageClasses[0].fsType=xfs \
  --set storageClasses[0].isDefaultClass=true
```

### StorageClass with Device Classes

```yaml
# Use device classes to separate NVMe from HDD
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: topolvm-nvme
provisioner: topolvm.io
parameters:
  topolvm.io/device-class: "nvme"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: topolvm-hdd
provisioner: topolvm.io
parameters:
  topolvm.io/device-class: "hdd"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

---

## OpenEBS Local Engines

OpenEBS provides three local engines: **LocalPV-HostPath** (simple directory-based, like local-path with OpenEBS scheduling), **LocalPV-LVM** (LVM thin provisioning with quota enforcement and snapshots), and **LocalPV-ZFS** (ZFS pools with checksums, compression, and native snapshots).

### OpenEBS LocalPV-LVM

```bash
# Install OpenEBS LocalPV-LVM
helm repo add openebs https://openebs.github.io/openebs
helm install openebs openebs/openebs \
  --namespace openebs --create-namespace \
  --set engines.local.lvm.enabled=true \
  --set engines.replicated.mayastor.enabled=false

# Create a VolumeGroup on each node first
# (same as TopoLVM: pvcreate + vgcreate)

# StorageClass
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: openebs-lvmpv
provisioner: local.csi.openebs.io
parameters:
  storage: "lvm"
  volgroup: "lvmvg"
  fsType: "xfs"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
```

OpenEBS also offers **LocalPV-ZFS** for workloads needing data integrity guarantees: checksums on every block, copy-on-write snapshots, native compression (lz4/zstd), and self-healing with mirrors. Create a ZFS pool on each node (`zpool create zfspv-pool /dev/nvme1n1`) and reference it in a StorageClass with `provisioner: zfs.csi.openebs.io`.

---

## Longhorn: Replicated Storage Without Ceph

Longhorn occupies a unique position: it provides cross-node replication (like Ceph) but with drastically simpler operations. Each volume is an independent replicated block device. There is no global storage pool, no placement groups, no CRUSH map.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LONGHORN ARCHITECTURE                         │
│                                                                   │
│  Volume: pvc-abc123 (3 replicas)                                │
│                                                                   │
│  ┌──────────────┐                                               │
│  │   Engine      │  iSCSI target (runs on the pod's node)       │
│  │  (worker-01)  │  Coordinates reads/writes to replicas        │
│  └──────┬───────┘                                               │
│         │                                                        │
│    ┌────┴────┬──────────┐                                       │
│    ▼         ▼          ▼                                        │
│  ┌────┐   ┌────┐   ┌────┐                                      │
│  │ R1 │   │ R2 │   │ R3 │   Replicas (sparse files on disk)    │
│  │w-01│   │w-02│   │w-03│   Each replica is a full copy         │
│  └────┘   └────┘   └────┘   Written synchronously               │
│                                                                   │
│  Node failure (worker-02):                                       │
│  - Engine continues with R1 + R3                                │
│  - Longhorn rebuilds R2 on worker-04 (if available)             │
│  - No manual intervention required                               │
│                                                                   │
│  Key difference from Ceph:                                       │
│  - No global pool, no CRUSH map, no placement groups            │
│  - Each volume is independent — no blast radius                  │
│  - Simpler to debug: one volume = one engine + N replicas        │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment

```bash
# Install Longhorn via Helm
helm repo add longhorn https://charts.longhorn.io
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace \
  --set defaultSettings.defaultDataPath=/var/lib/longhorn \
  --set defaultSettings.defaultReplicaCount=3

# Verify all components are running
kubectl -n longhorn-system get pods
# longhorn-manager-xxxxx    (DaemonSet - one per node)
# longhorn-driver-xxxxx     (CSI driver)
# longhorn-ui-xxxxx         (Web UI)

# Default StorageClass is created automatically
kubectl get sc longhorn
# NAME       PROVISIONER          RECLAIMPOLICY   VOLUMEBINDINGMODE
# longhorn   driver.longhorn.io   Delete          Immediate

# Create a replicated PVC
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-test
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: longhorn
  resources:
    requests:
      storage: 5Gi
EOF
```

---

## Comparison Table

| Feature | local-path | TopoLVM | OpenEBS LVM | OpenEBS ZFS | Longhorn |
|---------|-----------|---------|-------------|-------------|----------|
| Dynamic provisioning | Yes | Yes | Yes | Yes | Yes |
| Capacity enforcement | No | Yes | Yes | Yes | Yes |
| Snapshots | No | Yes | Yes | Yes (native) | Yes |
| Volume expansion | No | Yes | Yes | Yes | Yes |
| Replication | No | No | No | Mirror only | Yes (cross-node) |
| Topology-aware scheduling | Basic | Advanced | Yes | Yes | N/A (Immediate) |
| Compression | No | No | No | Yes (lz4/zstd) | No |
| Checksums | No | No | No | Yes | No |
| Overhead (RAM per node) | ~10 MB | ~50 MB | ~50 MB | ~100 MB | ~500 MB |
| Complexity | Minimal | Low | Low | Medium | Medium |
| Best for | Dev/edge | Prod local | Prod local | Data integrity | Replicated local |

---

## Topology-Aware Provisioning

All local storage solutions must handle a fundamental constraint: once a volume is created on a node, the pod must always run on that node. Kubernetes manages this through topology keys and `WaitForFirstConsumer` binding mode.

```yaml
# StorageClass with WaitForFirstConsumer
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-nvme
provisioner: topolvm.io
volumeBindingMode: WaitForFirstConsumer  # CRITICAL
allowedTopologies:
  - matchLabelExpressions:
      - key: node.kubernetes.io/instance-type
        values:
          - storage-optimized
```

Without `WaitForFirstConsumer`, the PV is provisioned on a random node before the pod is scheduled, causing conflicts. With it, the PV is provisioned on the same node the scheduler chose for the pod.

---

## When to Use Local vs Distributed Storage

```
┌────────────────────────────────────────────────────┐
│           DECISION TREE: LOCAL vs DISTRIBUTED       │
│                                                      │
│   Does your app handle its own replication?         │
│   (etcd, CockroachDB, Kafka, Cassandra, Elastic)   │
│         │                                            │
│    Yes ─┤                                            │
│         └──> Use LOCAL storage (TopoLVM / OpenEBS)  │
│              App replicates data, no need to pay    │
│              for storage-level replication.          │
│                                                      │
│    No ──┤                                            │
│         │   Do you need ReadWriteMany?              │
│         │         │                                  │
│         │    Yes ─┴──> Use Ceph (CephFS) or NFS     │
│         │                                            │
│         │    No ──┤                                  │
│         │         │   Can you tolerate 30-60s        │
│         │         │   failover to another node?      │
│         │         │         │                        │
│         │         │    Yes ─┴──> Use Longhorn        │
│         │         │                                  │
│         │         │    No ──┴──> Use Ceph (RBD)      │
│         │         │         with fast failover       │
└────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **local-path-provisioner powers all default k3s installations.** When you run k3s on an edge device, the `local-path` StorageClass is created automatically. Over 100,000 edge clusters worldwide rely on it for lightweight persistent storage without any distributed storage overhead.

- **TopoLVM was created by Cybozu**, the Japanese enterprise software company that also created the `coil` CNI plugin and the `accurate` namespace controller. Cybozu runs hundreds of Kubernetes clusters on bare metal and needed a storage solution that enforced LVM quotas without the complexity of a distributed system.

- **Longhorn was originally a Rancher Labs project** before SUSE acquired Rancher in 2020. It became a CNCF sandbox project in 2019 and graduated to incubating status. Unlike Ceph, each Longhorn volume is an independent replicated unit -- a failure in one volume's engine does not affect any other volume.

- **OpenEBS was the first CNCF sandbox storage project** (joined in 2019) and pioneered the concept of "Container Attached Storage" -- the idea that storage controllers should run as containers alongside application containers, not as a separate infrastructure layer.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `hostPath` in production | No lifecycle management, no cleanup, security risk | Use local-path-provisioner at minimum |
| Missing `WaitForFirstConsumer` | PV created on wrong node, pod cannot start | Always set `volumeBindingMode: WaitForFirstConsumer` for local storage |
| Longhorn on slow networks | Synchronous replication adds write latency proportional to network RTT | Ensure dedicated storage network or 10 GbE minimum |
| No VG space monitoring | Node runs out of LVM space, new PVCs fail | Monitor VG free space with Prometheus + node-exporter textfile collector |
| Choosing Ceph for 3-node clusters | Ceph overhead dominates small clusters (9+ pods just for storage) | Use Longhorn or TopoLVM for clusters under 6 nodes |
| Ignoring disk I/O isolation | One pod's heavy writes starve other pods on the same disk | Use LVM thin pools with I/O limits, or separate VGs per workload class |
| Running databases on local-path | No capacity enforcement, no snapshots, no backup integration | Use TopoLVM or OpenEBS LVM for databases |
| Longhorn replica count > node count | Replicas cannot be placed, volume stays degraded | Set replica count to min(3, number_of_nodes) |

---

## Quiz

### Question 1
You have a 3-node bare-metal cluster running PostgreSQL with streaming replication (1 primary, 2 replicas). Should you use Longhorn or TopoLVM for the database volumes?

<details>
<summary>Answer</summary>

**Use TopoLVM (or OpenEBS LVM).** PostgreSQL streaming replication already handles data replication at the application level. Each PostgreSQL instance maintains a full copy of the data.

Adding Longhorn replication would mean:
- Each PostgreSQL replica (3 copies at the app level) is stored with 3 copies at the storage level
- Total copies: 3 x 3 = 9 copies of the same data
- Triple the write amplification (every PostgreSQL write goes to 3 Longhorn replicas)
- Triple the network traffic for storage replication

With TopoLVM:
- Each PostgreSQL instance gets a local LVM volume on its node
- PostgreSQL handles replication itself (WAL shipping)
- Total copies: 3 (one per PostgreSQL instance)
- Writes go directly to local NVMe with no network overhead

**Rule of thumb**: If the application replicates, the storage should not.
</details>

### Question 2
A developer creates a PVC with `storageClassName: local-path` requesting 50 Gi. The node has 100 Gi free. Can the pod use more than 50 Gi?

<details>
<summary>Answer</summary>

**Yes.** local-path-provisioner does not enforce capacity limits. The `50Gi` in the PVC is purely informational. The pod can write up to the full 100 Gi of free disk space on the node (or until the filesystem is full).

This is because local-path-provisioner creates a plain directory on the host filesystem. There is no LVM logical volume, no quota, no cgroup constraint limiting the directory's size.

To enforce actual capacity:
- **TopoLVM**: Creates an LVM logical volume of exactly the requested size. Writes beyond that size fail with ENOSPC.
- **OpenEBS LVM**: Same LVM-based enforcement.
- **OpenEBS ZFS**: ZFS quota on the dataset.

```bash
# With TopoLVM, the LV has a fixed size
lvs myvg
# LV          VG    Size
# pvc-abc123  myvg  50.00g   # Cannot exceed this
```
</details>

### Question 3
Your Longhorn volume shows 2 of 3 replicas healthy. The third replica is on a node that was permanently removed from the cluster. What happens?

<details>
<summary>Answer</summary>

**Longhorn automatically rebuilds the missing replica on another available node.** The process:

1. Longhorn detects the node is gone (node controller marks it as not ready)
2. After the `replica-replenishment-wait-interval` (default: 600 seconds / 10 minutes), Longhorn schedules a new replica on a healthy node with sufficient disk space
3. The engine copies data from one of the 2 healthy replicas to the new replica
4. During rebuild, reads and writes continue normally (served by the 2 healthy replicas)
5. Once complete, the volume returns to 3 healthy replicas

**If no other node has space**, the volume remains degraded at 2 replicas. It is still fully operational but has reduced redundancy. Longhorn will continuously retry placing the third replica.

You can check replica status:
```bash
kubectl -n longhorn-system get replicas.longhorn.io \
  -l longhornvolume=pvc-abc123
```
</details>

### Question 4
You need to store 500 Gi of ML training data that 8 pods read simultaneously. The data is written once and read many times. Which local storage solution should you use?

<details>
<summary>Answer</summary>

**None of the local storage solutions in this module are appropriate.** This workload requires `ReadWriteMany` (RWX) access mode, which none of the local storage options support natively:

- local-path, TopoLVM, OpenEBS LVM/ZFS: Only `ReadWriteOnce` (RWO) -- one node at a time
- Longhorn: Supports RWX only via NFS export, which adds a single-node bottleneck

**Better options**:
1. **CephFS** (from Module 4.2): True distributed filesystem, handles concurrent reads well
2. **NFS server**: Simple, good for read-heavy workloads
3. **Object storage** (MinIO): If the ML framework supports S3-compatible storage
4. **Pre-load to local storage**: Copy the dataset to each node's local volume, accept the storage duplication

If the data fits on a single NVMe and performance matters more than storage efficiency, the pre-load approach is fastest:
```bash
# Init container copies data from shared source to local volume
initContainers:
  - name: data-loader
    image: busybox
    command: ["cp", "-r", "/shared/dataset", "/local/dataset"]
```
</details>

---

## Hands-On Exercise: Compare local-path and Longhorn

```bash
# Create a kind cluster with 3 worker nodes
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
  - role: worker
EOF

# Step 1: local-path is already included in kind
kubectl get sc standard

# Step 2: Create a PVC and pod with local-path
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: standard
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: writer
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "echo 'hello' > /data/test.txt && sleep 3600"]
      volumeMounts:
        - mountPath: /data
          name: vol
  volumes:
    - name: vol
      persistentVolumeClaim:
        claimName: local-pvc
EOF

# Step 3: Verify pod is pinned to a specific node
kubectl get pod writer -o jsonpath='{.spec.nodeName}'

# Step 4: Install Longhorn and create a replicated PVC
helm repo add longhorn https://charts.longhorn.io
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace \
  --set defaultSettings.defaultReplicaCount=2 --wait --timeout 5m

kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: longhorn
  resources:
    requests:
      storage: 1Gi
EOF

# Step 5: Verify Longhorn replicas span multiple nodes
kubectl -n longhorn-system get replicas.longhorn.io

# Cleanup
kubectl delete pod writer && kubectl delete pvc local-pvc longhorn-pvc
kind delete cluster
```

### Success Criteria

- [ ] local-path PVC bound and data written successfully
- [ ] Pod pinned to specific node (verified with `spec.nodeName`)
- [ ] Longhorn PVC has replicas on multiple nodes
- [ ] Understood the difference: local-path has no replication, Longhorn does

---

## Next Module

Continue to [Module 5.1: Private Cloud Platforms](../../multi-cluster/module-5.1-private-cloud/) to learn how VMware vSphere, OpenStack, and Harvester provide infrastructure abstraction layers for on-premises Kubernetes.

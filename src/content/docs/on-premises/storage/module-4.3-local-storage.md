---
qa_pending: true
title: "Module 4.3: Local Storage & Alternatives"
slug: on-premises/storage/module-4.3-local-storage
sidebar:
  order: 4
---

> **Complexity**: `[INTERMEDIATE]` | Time: 60 minutes
>
> **Prerequisites**: [Module 4.1: Storage Architecture](../module-4.1-storage-architecture/), [Module 4.2: Ceph & Rook](../module-4.2-ceph-rook/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Evaluate** when local storage, Longhorn, OpenEBS, or LVM-based solutions are appropriate compared to a full distributed storage system, and justify that choice against workload, blast-radius, and operational-cost criteria.
2. **Implement** local-path-provisioner and TopoLVM for workloads that tolerate node-local storage semantics, including the topology, scheduling, and quota concerns that determine whether the volume actually does what the manifest claims.
3. **Deploy** Longhorn as a lightweight replicated storage solution with automated backups, snapshots, and a tested restore drill, and read the resulting Volume/Replica/Engine custom resources fluently when something misbehaves.
4. **Operate** OpenEBS LocalPV-LVM (and the LocalPV-ZFS variant) end-to-end: volume group preparation, StorageClass shape, snapshot lifecycle, and the verification queries that confirm storage actually reached the disk you intended.
5. **Design** a multi-tier on-premises storage strategy that maps each workload class (databases with internal replication, replicated stateful services, RWX share, ephemeral scratch) to the right backend, and explain the failure modes the alternative choices would have introduced.

---

## Why This Module Matters

A fintech startup ran six microservices on three bare-metal servers. They deployed Rook-Ceph because "everyone uses Ceph." Within a week, the Ceph monitors consumed 2 GB of RAM each, OSD recovery traffic saturated their 10 GbE links during a node reboot, and a junior engineer accidentally deleted the mon keyring while debugging. Total downtime was 14 hours, two of which were spent finding a backup of the keyring on a laptop.

They replaced Ceph with Longhorn the following weekend. Deployment took 20 minutes. Each microservice received a three-replica volume backed by local NVMe. The total storage overhead dropped from nine pods (three MONs, three MGRs, three OSDs, plus the operator) down to a single per-node DaemonSet. Six months later, they have had zero storage incidents, and the on-call rotation no longer dreads pages from the storage layer.

That story repeats across small clusters every month, and it points at a deeper truth: not every on-premises cluster needs a distributed storage system. If your workloads are stateless, or if each pod can tolerate node-local storage that disappears with the node, local storage is simpler, faster, and dramatically cheaper to operate. Even when you do need replication, lightweight alternatives like Longhorn and OpenEBS provide it without the operational complexity, blast radius, and learning curve that Ceph imposes on a team.

The temptation is to pick a single storage platform and use it for every workload, on the theory that uniformity reduces operational toil. That theory only holds when the platform is genuinely the best fit for every workload, and it almost never is. A PostgreSQL streaming replica wants raw local NVMe; a multi-pod read-only model artifact share wants RWX; a developer's prototype wants something that goes from `helm install` to a bound PVC in under 30 seconds. This module covers the full spectrum, from zero-overhead local-path-provisioner up through replicated-but-simple Longhorn, with LVM-based and ZFS-based solutions in between, so you can place each workload on the storage backend that actually fits its persistence and performance contract.

---

## What You'll Learn

- When local storage is the right choice, and the failure modes that make it the wrong one
- local-path-provisioner for development, edge, and self-replicating workloads
- TopoLVM and LVM CSI for production local volumes with topology-aware scheduling and real capacity enforcement
- OpenEBS local engines (LocalPV-HostPath, LocalPV-LVM, LocalPV-ZFS) with a worked snapshot and restore walkthrough
- Longhorn for replicated storage without Ceph complexity, including backups, recurring jobs, and disaster-recovery drills
- Topology-aware provisioning, `volumeBindingMode`, and the scheduler integration that makes any of this work
- A decision framework you can defend in design review for choosing the right storage solution per workload tier

---

## The Local Storage Spectrum

Local storage is not a single technology; it is a spectrum that runs from "directory on a host" to "iSCSI-backed replicated block device that survives node loss." Choosing well requires understanding where each option sits on that spectrum, because the operational and durability properties change dramatically as you move from left to right. The cheapest tools impose almost no overhead but offer almost no guarantees, and the most capable tools recover automatically from node failure but pay for that capability with measurable RAM, network, and complexity costs. You should match each workload to the simplest tool that still satisfies its durability contract, not default to the most capable tool everywhere.

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

The diagram above is the mental model you should carry into every storage design conversation. Move left when the workload replicates itself or doesn't care about durability; move right when the storage layer is responsible for surviving a node loss without the application noticing. The cliff in the middle is whether the volume can survive a node disappearing: everything to the left of Longhorn loses the volume when the node it lives on dies, and you must either restore from backup or accept data loss. Everything we cover in this module before Longhorn is, in that sense, a single-node storage system; the durability property is what changes once you cross into Longhorn or distributed alternatives like Ceph.

---

## local-path-provisioner

Rancher's local-path-provisioner is the simplest dynamic provisioner that still respects the Kubernetes contract. It listens for PVCs that target its StorageClass, creates a directory on the chosen node's filesystem, binds a PV to that directory, and cleans the directory up when the PVC is deleted. There is no LVM, no thin pool, no snapshot, no replication, no quota. It is a directory provisioner with a CSI-shaped face, and that minimalism is exactly what makes it the right tool for a narrow but useful slice of workloads.

### When to Use

- Development clusters (kind, k3s, single-node labs) where simplicity beats every other property
- Edge deployments where the node and the cluster are effectively the same blast radius
- Workloads that already replicate at the application layer and treat node-local storage as their primary durability assumption (etcd, CockroachDB, Kafka, Cassandra, ScyllaDB, Vitess shards)

> **Pause and predict**: Your cluster has a mix of workloads: some are stateless web services, some are databases with built-in replication (like CockroachDB), and some are single-instance PostgreSQL databases serving a small internal tool. Which of these need distributed storage, and which can use local-path? What happens to a local-path PVC when its node fails permanently, and which of those three workload classes is the worst fit for that failure mode?

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

The mechanism is intentionally boring. When a PVC referencing the `local-path` StorageClass is bound, a helper pod created by the provisioner runs `mkdir` inside a hostPath mount on the chosen node, and the PV's `nodeAffinity` then pins any consumer pod to that same node forever. Reclaim is the same shape in reverse: a helper pod runs `rm -rf` on the directory and the PV is released. Because the implementation is essentially a controller plus two helper-pod templates, it has almost no failure surface and almost no operational cost; the price you pay for that simplicity is that everything interesting (capacity enforcement, snapshots, replication) has to come from somewhere else in your stack.

### Deployment

```bash
# Install local-path-provisioner
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.30/deploy/local-path-storage.yaml

# Create a PVC (stays Pending until a Pod references it because the
# StorageClass uses WaitForFirstConsumer by default)
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

The most important thing to internalize about this StorageClass is what `1Gi` does *not* mean here. The PVC has no actual size enforcement: the provisioner created a directory, and a directory can be written until the underlying filesystem fills. A pod that requested 1 GiB can consume the entire node disk and there is nothing in this pipeline that will stop it short of `ENOSPC`. For genuine quota enforcement and snapshots you need an LVM-backed or ZFS-backed CSI driver, which is precisely the gap the next two sections close.

---

## TopoLVM: Production-Grade Local Volumes

TopoLVM uses LVM (Logical Volume Manager) to carve local disks into thin-provisioned logical volumes with actual capacity enforcement. It integrates with the Kubernetes scheduler via a mutating webhook so that pods land on nodes that have enough free space in the relevant volume group, and it exposes per-node free-space metrics so the scheduler can score candidates rather than guess. This is the moment where local storage stops being "best effort" and starts being a production-grade primitive: the LV size is enforced by the kernel, snapshots are real, and the scheduler is no longer flying blind.

### TopoLVM Architecture

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

The four components in that diagram each play a specific role and are easiest to reason about as a pipeline. The mutating webhook (`topolvm-sched`) sits in front of the scheduler and rewrites pod specs so the scheduler can see TopoLVM's free-space extended resource per node. The DaemonSet (`topolvm-node`) runs an `lvmd` instance on each node, which is the thing that actually shells out to LVM and reports real-time volume-group statistics back upward. The CSI controller translates `CreateVolume` and `DeleteVolume` requests into LVM operations on the right node, and the volume group on the local NVMe is where all of the actual data ends up. When something misbehaves, the order in which you check those components is exactly the order in which they appear in the pipeline, and almost every TopoLVM bug is "the webhook isn't seeing the pod" or "the lvmd can't see the device."

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
  --set lvmd.deviceClasses[0].name=nvme \
  --set lvmd.deviceClasses[0].volume-group=myvg \
  --set lvmd.deviceClasses[0].default=true \
  --set storageClasses[0].name=topolvm-provisioner \
  --set storageClasses[0].storageClass.fsType=xfs \
  --set storageClasses[0].storageClass.isDefaultClass=true
```

You should treat the volume-group preparation step as part of your node-provisioning pipeline rather than something you do by hand once. In practice this means the cluster's image build, kickstart, or Ignition flow runs `pvcreate` and `vgcreate` against a known device, and the node enters the cluster with `myvg` already present and empty. If you skip that and try to create the VG on a running node, you will eventually forget to do it on one node, and that node will quietly fail to schedule TopoLVM volumes; the symptom looks like "the pod is stuck Pending" and the root cause is "no node advertises capacity in the right device class."

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

Device classes are the single most underrated feature in TopoLVM. They let you advertise multiple volume groups per node (`nvme` for hot databases, `hdd` for cold archives, `mixed` for general workloads) and pick between them in the StorageClass. The scheduler treats free space in each device class as a separate extended resource, so a database PVC that targets `topolvm-nvme` will only land on nodes that have NVMe capacity, even if those nodes are full of HDD space. This pattern lets you operate hybrid hardware without forcing every workload onto the same disk tier, and it is the cleanest way to keep noisy analytics workloads off the same spindles as your latency-sensitive databases.

---

## OpenEBS Local Engines

OpenEBS provides three local engines that cover the same conceptual space as TopoLVM but with a more flexible operator model. **LocalPV-HostPath** is a directory-based engine in the spirit of local-path-provisioner but with OpenEBS's scheduling integration. **LocalPV-LVM** is LVM thin-provisioning with quota enforcement, snapshots, and clones, comparable to TopoLVM but driven by OpenEBS's CSI driver and CRDs. **LocalPV-ZFS** layers OpenEBS on top of ZFS pools to deliver checksums, copy-on-write snapshots, native compression (lz4/zstd), and self-healing mirrors when you run multi-disk pools. You typically choose one engine per node-type and keep that choice consistent across a node pool, because the volume-group or pool preparation is engine-specific and changing it later requires a node-by-node migration.

### Installing LocalPV-LVM

```bash
# Install OpenEBS LocalPV-LVM
helm repo add openebs https://openebs.github.io/openebs
helm install openebs openebs/openebs \
  --namespace openebs --create-namespace \
  --set engines.local.lvm.enabled=true \
  --set engines.replicated.mayastor.enabled=false

# Create a VolumeGroup on each node first
# (same as TopoLVM: pvcreate + vgcreate, but name it lvmvg)

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

The Helm install lays down the OpenEBS CSI controller, the LocalPV-LVM node DaemonSet, and the CRDs (`LVMVolume`, `LVMSnapshot`, `LVMNode`) that you will use later to inspect state. The shape mirrors what you saw with TopoLVM: a controller pod issues CSI calls, a node-local agent shells out to LVM, and the CRDs make the volume group visible inside the API. The notable difference is that OpenEBS exposes those CRDs to you directly, which is useful for debugging because you can query `LVMVolume` objects exactly like Pods or PVCs, and the CRD status carries the node placement, the LV name, and the underlying volume group.

### Worked Example: Provision, Verify, Snapshot, Restore

To make this concrete, walk through a complete LocalPV-LVM lifecycle on a three-node cluster. The goal is to provision a volume, write known data, take a snapshot, simulate corruption, restore from the snapshot, and verify the data is intact. This is the OpenEBS analog of the Longhorn restore drill later in the module, and it is the shortest path to building real confidence in the engine.

```bash
# Step 1: create a PVC and a writer pod that produces deterministic data
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lvm-demo
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: openebs-lvmpv
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: writer
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c"]
      args:
        - |
          echo "v1-original" > /data/marker.txt
          dd if=/dev/urandom of=/data/payload.bin bs=1M count=64
          sha256sum /data/payload.bin > /data/payload.sha256
          sleep 3600
      volumeMounts:
        - mountPath: /data
          name: vol
  volumes:
    - name: vol
      persistentVolumeClaim:
        claimName: lvm-demo
EOF
```

Once the writer pod is `Running`, the PVC is bound, and the LV exists on whichever node the scheduler chose. You should now verify three things in order: that the LVMVolume CRD reports the correct placement, that the underlying logical volume actually exists on the right node, and that the data the pod wrote matches what we expect. This three-layer verification (CRD → kernel → application) is the right habit to develop for any local-storage engine, because it tells you which layer to look at when something goes wrong later.

```bash
# Step 2: verify at the CRD layer
kubectl -n openebs get lvmvolumes.local.openebs.io
# NAME                    VOLGROUP   NODE        SIZE         STATUS
# pvc-2f...-lvm           lvmvg      worker-02   5368709120   Ready

PV_NAME=$(kubectl get pvc lvm-demo -o jsonpath='{.spec.volumeName}')
NODE=$(kubectl -n openebs get lvmvolume "$PV_NAME" -o jsonpath='{.spec.ownerNodeID}')
echo "Volume $PV_NAME lives on $NODE"

# Step 3: verify at the LVM layer (run on the chosen node)
ssh "$NODE" sudo lvs lvmvg
#   LV                                       VG     Attr       LSize
#   pvc-2f8a...-d31c                         lvmvg  -wi-ao----  5.00g

# Step 4: verify the application-level checksum
kubectl exec writer -- sh -c 'sha256sum -c /data/payload.sha256'
# /data/payload.bin: OK
```

With the volume verified end-to-end, take a snapshot. OpenEBS LocalPV-LVM uses Kubernetes `VolumeSnapshot` and `VolumeSnapshotClass` objects, which are translated into LVM thin-pool snapshots that point at the same underlying extents until a write triggers copy-on-write. The snapshot is therefore extremely cheap to create and very cheap to keep around for short windows, but it lives on the same volume group as the source, so it is *not* a substitute for a backup; if the node dies, the snapshot dies with it.

```bash
# Step 5: install the snapshot class and snapshot the volume
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: openebs-lvm-snap
driver: local.csi.openebs.io
deletionPolicy: Delete
parameters:
  snapshotNamespace: openebs
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: lvm-demo-snap-v1
spec:
  volumeSnapshotClassName: openebs-lvm-snap
  source:
    persistentVolumeClaimName: lvm-demo
EOF

# Step 6: confirm the snapshot reached READY_TO_USE=true
kubectl get volumesnapshot lvm-demo-snap-v1 \
  -o jsonpath='{.status.readyToUse}'
# true

# Step 7: simulate corruption by overwriting the marker file
kubectl exec writer -- sh -c 'echo "v2-corrupted" > /data/marker.txt'
kubectl exec writer -- cat /data/marker.txt
# v2-corrupted
```

Now restore. With LocalPV-LVM you restore by creating a new PVC whose `dataSource` references the snapshot, which produces a fresh LV on the same node populated from the snapshot's CoW state. Mount that PVC into a verification pod and confirm that the marker file reads `v1-original` and the checksum still matches. If both checks pass, you have proven that snapshots actually capture point-in-time state and that the restore path works end-to-end on this engine.

```bash
# Step 8: restore the snapshot into a brand-new PVC
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lvm-demo-restored
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: openebs-lvmpv
  resources:
    requests:
      storage: 5Gi
  dataSource:
    apiGroup: snapshot.storage.k8s.io
    kind: VolumeSnapshot
    name: lvm-demo-snap-v1
---
apiVersion: v1
kind: Pod
metadata:
  name: verifier
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "sleep 3600"]
      volumeMounts:
        - mountPath: /data
          name: vol
  volumes:
    - name: vol
      persistentVolumeClaim:
        claimName: lvm-demo-restored
EOF

# Step 9: verify the restore actually rewound the marker file
kubectl exec verifier -- cat /data/marker.txt
# v1-original  <-- back to the pre-corruption state
kubectl exec verifier -- sh -c 'sha256sum -c /data/payload.sha256'
# /data/payload.bin: OK
```

Two failure modes are worth noting before you put this engine in production. First, the snapshot lives in the same thin pool as the source LV, so if the source LV writes a lot of new data, the thin pool can fill and *both* the source and the snapshot will start failing writes; you must monitor `Data%` on the thin pool with `lvs -o name,data_percent,metadata_percent` and alert before it hits 80%. Second, if the node hosting the volume goes away permanently, every snapshot for every LV on that node goes with it; LocalPV-LVM is a node-local engine, and snapshots are a fast-rollback mechanism, not a disaster-recovery mechanism. For DR you still need either a replicated engine like Longhorn or an out-of-cluster backup of snapshot contents.

### LocalPV-ZFS in One Pass

OpenEBS LocalPV-ZFS uses the same general shape but swaps LVM for a ZFS pool, which gives you three things that LVM does not: per-block checksums that detect silent corruption, native compression that often pays for itself in throughput because the disk does less work, and dataset-level snapshots that are even cheaper than LVM's because of ZFS's copy-on-write design. To use it, create a pool on each node (`zpool create zfspv-pool /dev/nvme1n1`), enable the engine via Helm (`engines.local.zfs.enabled=true`), and target the pool from a StorageClass with `provisioner: zfs.csi.openebs.io` and `poolname: zfspv-pool`. The verification and snapshot walkthrough above ports almost line-for-line: the CRD becomes `ZFSVolume`, the kernel verification becomes `zfs list` and `zfs get all <dataset>`, and `VolumeSnapshot` works identically. Reach for ZFS when data integrity matters more than RAM efficiency, and stick with LVM when you want the leanest engine that still enforces quota.

---

## Longhorn: Replicated Storage Without Ceph

Longhorn occupies a unique position on the spectrum: it provides cross-node replication, like Ceph, but with drastically simpler operations and a far smaller mental model. Each Longhorn volume is an independent replicated block device with its own engine and its own set of replicas, and that per-volume isolation is the core architectural choice that makes Longhorn easier to reason about than a pooled distributed storage system. There is no global storage pool, no placement-group calculus, no CRUSH map, no monitor quorum, and no concept of cluster-wide rebalancing. When something is wrong with one volume, the blast radius is one volume.

> **Stop and think**: A team is debating between Ceph and Longhorn for a five-node cluster running ten stateful services. Ceph would require three MON pods, two MGR pods, and at least five OSD pods (ten storage pods total before you count operators and the CSI plumbing). Longhorn requires a single DaemonSet (five pods) plus a CSI driver. Beyond operational complexity, what is the architectural difference that makes Longhorn simpler per volume but potentially less efficient at scale, and at what cluster size does that trade-off start to flip?

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
│  - Each volume is independent, no cross-volume blast radius      │
│  - Simpler to debug: one volume = one engine + N replicas        │
└─────────────────────────────────────────────────────────────────┘
```

For each volume, Longhorn places one *engine* pod on the node where the consumer pod is currently running, and one *replica* per node up to the volume's `replicaCount`. The engine exposes an iSCSI target that the kernel mounts as a block device; reads can come from any healthy replica, and writes are mirrored synchronously to every replica before the engine acknowledges. When the consumer pod is rescheduled to a different node, Longhorn moves the engine to follow it, but the replicas stay where they are; the block device on the new node simply talks to the same set of replicas across the network. This per-volume engine model is the source of both Longhorn's simplicity and its scaling ceiling: each volume is independent so debugging is local, but each volume also pays the engine-pod overhead, and at very high volume counts that adds up.

### Longhorn Deployment

```bash
# Install Longhorn via Helm
helm repo add longhorn https://charts.longhorn.io
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace \
  --set defaultSettings.defaultDataPath=/var/lib/longhorn \
  --set defaultSettings.defaultReplicaCount=3

# Verify all components are running
kubectl -n longhorn-system get pods
# longhorn-manager-xxxxx    (DaemonSet, one per node)
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

After the chart settles, you will see `longhorn-manager` running on every node as a DaemonSet, the CSI plumbing pods on a couple of nodes, and the UI pod somewhere convenient. Two operational habits pay off immediately: install the iSCSI initiator on every node *before* you deploy Longhorn (`open-iscsi` on Debian-family, `iscsi-initiator-utils` on RHEL-family), because the iSCSI target the engine exposes is consumed by the host kernel; and reserve a dedicated mount point for `/var/lib/longhorn` on each node, sized for the worst-case sum of replicas you expect that node to host, so a runaway replica cannot fill the node's root filesystem.

### Automated Backups and Restore

Snapshots stay inside the cluster and protect against accidental writes; backups copy snapshot data to an external backupstore (typically an S3-compatible object store such as MinIO, or an NFS export) and protect against node loss, cluster loss, and ransomware. For Longhorn, snapshots are the right tool for short rollback windows measured in hours, and backups are the right tool for recovery measured in days, weeks, or after the cluster itself has been rebuilt. Treat them as two separate disciplines with two separate retention policies, and resist the temptation to fold one into the other.

```bash
# Example: point Longhorn at an S3-compatible target (for example, MinIO)
kubectl -n longhorn-system create secret generic longhorn-backup-secret \
  --from-literal=AWS_ACCESS_KEY_ID=longhorn-access-key \
  --from-literal=AWS_SECRET_ACCESS_KEY=longhorn-secret-key \
  --from-literal=AWS_ENDPOINTS=https://minio.storage.svc:9000

# The trailing / on the backup target URL matters
helm upgrade longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --reuse-values \
  --set defaultBackupStore.backupTarget=s3://longhorn-backups@us-east-1/ \
  --set defaultBackupStore.backupTargetCredentialSecret=longhorn-backup-secret \
  --set defaultBackupStore.pollInterval=300

# Create a recurring backup policy
kubectl apply -f - <<EOF
apiVersion: longhorn.io/v1beta2
kind: RecurringJob
metadata:
  name: daily-backup
  namespace: longhorn-system
spec:
  cron: "0 2 * * *"
  task: backup
  retain: 7
  concurrency: 1
  labels:
    backup-tier: daily
  parameters:
    full-backup-interval: "6"
EOF

# Opt this PVC into label-driven recurring jobs
kubectl -n default label pvc/longhorn-test recurring-job.longhorn.io/source=enabled
kubectl -n default label pvc/longhorn-test recurring-job.longhorn.io/daily-backup=enabled
```

This policy keeps seven daily recovery points. The `retain: 7` setting is the retention control Longhorn understands, and you should not pile bucket lifecycle rules on top that delete backup objects behind Longhorn's back, because Longhorn's bookkeeping will desync from the bucket and you will discover that during a restore drill rather than from a dashboard. The `full-backup-interval: "6"` setting forces a fresh full backup every six incremental runs, which keeps the delta chain bounded and keeps restore times predictable. If you want to verify the workflow during a lab session instead of waiting until 02:00, temporarily change the cron expression to `*/15 * * * *`, confirm backups are appearing in the bucket, and then switch back to the daily schedule before you walk away.

Validate the setup after the next backup window:

```bash
kubectl -n longhorn-system get setting backup-target
kubectl -n longhorn-system get recurringjobs.longhorn.io daily-backup
kubectl -n default get pvc longhorn-test --show-labels
kubectl -n longhorn-system get backups.longhorn.io
```

A practical restore drill is the only way you will know whether your backup configuration is real, and you should run it every quarter on a non-production volume that you have deliberately corrupted. The shape of the drill is straightforward: pick a backup, restore it to a new volume, mount that volume into a verification pod, and prove that the data inside matches a known checksum or marker that you set before triggering the corruption.

1. In the Longhorn UI, open `Backup`, select the latest backup for `longhorn-test`, and choose `Restore Latest Backup`.
2. Restore it as `longhorn-test-restore`, then create a PVC and PV pair for the restored volume, or attach it to a temporary validation pod that simply runs `cat` and `sha256sum` against the data you wrote earlier.
3. If you also want the recurring-job schedule to come back with the volume, enable `restore-volume-recurring-jobs` first, otherwise the restored volume will not be on any schedule until you re-label it.

```bash
kubectl -n longhorn-system get setting restore-volume-recurring-jobs
kubectl -n longhorn-system get volumes.longhorn.io longhorn-test-restore
```

### Reading Longhorn Custom Resources

Longhorn exposes its internal state as CRDs, and learning to read them directly is the difference between "I open the UI and click around" and "I diagnose this in 30 seconds from a terminal." The four CRDs you will look at most often are `volumes.longhorn.io` (per-volume desired and observed state, including replica count and current robustness), `engines.longhorn.io` (one per active volume, showing which node hosts the engine and which replicas it considers healthy), `replicas.longhorn.io` (one per replica, including its node, disk, and rebuild progress), and `backups.longhorn.io` (one per backup, with size and creation time). When a volume is "degraded" the answer almost always lives in the difference between the desired replica list on the volume and the actual list on the engine, and a single `kubectl get` will tell you which replica is unhealthy and on what node.

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
| RWX support | No | No | No | No | Yes (via NFS) |
| Best for | Dev/edge | Prod local | Prod local | Data integrity | Replicated local |

The table above is a starting point, not an answer. Two columns that look the same in a feature matrix can behave very differently in production, and the column that often decides the choice is the one labelled "Overhead." Longhorn's roughly 500 MB of RAM per node for the manager and engines is invisible at three nodes and very visible at fifty; TopoLVM's 50 MB is barely worth measuring at any cluster size; local-path is below the noise floor. Pair this table with a workload-by-workload review rather than picking the row with the most "Yes" cells.

---

> **Pause and predict**: You deploy a StatefulSet with three replicas using a local storage StorageClass, but the binding mode is set to `Immediate` instead of `WaitForFirstConsumer`. What happens during initial scheduling, what happens if the scheduler later tries to move one of the pods to a different node, and what is the smallest YAML change that fixes the problem?

## Topology-Aware Provisioning

All local storage solutions must handle a fundamental constraint: once a volume is created on a node, the consumer pod must always run on that node, because the data only exists there. Kubernetes manages this through the `nodeAffinity` field on each PV and through the `volumeBindingMode` on the StorageClass. The default `Immediate` mode binds a PV as soon as the PVC is created, which works for cluster-wide storage like Ceph but is actively harmful for local storage because the scheduler has not yet decided where the pod should run.

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

`WaitForFirstConsumer` flips the order: the PVC stays Pending until a pod that references it is scheduled, the scheduler picks a node based on every other constraint (resources, affinity, taints, topology), and only then is the PV provisioned on that chosen node. This is the only correct mode for any local storage backend except Longhorn, where the volume is replicated cross-node and the storage is no longer pinned to a single host. Pair `WaitForFirstConsumer` with `allowedTopologies` to constrain *which* nodes are eligible (for example, only the storage-optimized node pool), and you have a clean way to keep stateful workloads on the right hardware without resorting to manual node selectors on every Pod.

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

Read this tree from the top, and answer each branch honestly. The first branch is the one most teams get wrong, because it is tempting to claim that "PostgreSQL has streaming replication so it counts" without actually deploying that replication or owning the failover runbook. Application-level replication is only a real answer when there are at least two replicas of the application, the replicas are on different nodes, and you have practiced the failover. If the answer is "we run a single PostgreSQL pod and hope," then the application does *not* replicate itself and you should treat it like a non-replicated app from the rest of the tree. The second branch (RWX) is the one that pushes you out of the local-storage spectrum entirely, because nothing in this module can serve a read-write-many filesystem natively. The last branch is a cost-versus-RTO trade-off: Longhorn fails over in tens of seconds, Ceph RBD with proper tuning can fail over in single-digit seconds, and that gap is sometimes the deciding factor.

---

## Did You Know?

- **local-path-provisioner powers all default k3s installations.** When you run k3s on an edge device, the `local-path` StorageClass is created automatically, and over 100,000 edge clusters in production today rely on it for lightweight persistent storage without any distributed-storage overhead. K3s ships it as the out-of-box answer because the typical k3s cluster is a single node and there is nothing useful to replicate to.
- **TopoLVM was created by Cybozu**, the Japanese enterprise software company that also produced the `coil` CNI plugin and the `accurate` namespace controller. Cybozu runs hundreds of Kubernetes clusters on bare metal and needed a storage solution that enforced LVM quotas without the complexity of a distributed system; the design choice to integrate with the scheduler via webhook rather than via a CSI extension is a direct consequence of that operational pragmatism.
- **Longhorn was originally a Rancher Labs project** before SUSE acquired Rancher in 2020, became a CNCF sandbox project in 2019, and graduated to incubating status. Unlike Ceph, each Longhorn volume is an independent replicated unit, so a failure in one volume's engine does not affect any other volume; that per-volume blast radius is the architectural property that lets two-engineer platform teams operate Longhorn at production scale.
- **OpenEBS was the first CNCF sandbox storage project** (joined in 2019) and pioneered the concept of "Container Attached Storage": the idea that storage controllers should run as containers alongside application containers rather than as a separate infrastructure layer. That choice is why OpenEBS's local engines compose so cleanly with Helm, GitOps, and per-namespace RBAC, where traditional storage appliances assume a separate operations team and a separate lifecycle.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `hostPath` in production | No lifecycle management, no cleanup, security risk | Use local-path-provisioner at minimum |
| Missing `WaitForFirstConsumer` | PV created on wrong node, pod cannot start | Always set `volumeBindingMode: WaitForFirstConsumer` for local storage |
| Longhorn on slow networks | Synchronous replication adds write latency proportional to network RTT | Ensure dedicated storage network or 10 GbE minimum |
| No VG space monitoring | Node runs out of LVM space, new PVCs fail | Monitor VG free space with Prometheus + node-exporter textfile collector |
| Choosing Ceph for 3-node clusters | Ceph overhead dominates small clusters (10+ pods just for storage) | Use Longhorn or TopoLVM for clusters under six nodes |
| Ignoring disk I/O isolation | One pod's heavy writes starve other pods on the same disk | Use LVM thin pools with I/O limits, or separate VGs per workload class |
| Running databases on local-path | No capacity enforcement, no snapshots, no backup integration | Use TopoLVM or OpenEBS LVM for databases |
| Longhorn replica count above node count | Replicas cannot be placed, volume stays degraded | Set replica count to `min(3, number_of_nodes)` |

---

## Quiz

### Question 1
You have a three-node bare-metal cluster running PostgreSQL with streaming replication (one primary, two replicas). Should you use Longhorn or TopoLVM for the database volumes, and how would you justify that choice in a design review?

<details>
<summary>Answer</summary>

**Use TopoLVM (or OpenEBS LVM).** PostgreSQL streaming replication already handles data replication at the application level, so each PostgreSQL instance maintains a full copy of the data on its own node.

If you layered Longhorn underneath:
- Each PostgreSQL replica (three application copies) would be stored with three Longhorn replicas
- Total copies: 3 × 3 = 9 copies of the same data on disk
- Triple the write amplification, because every PostgreSQL write goes to three Longhorn replicas synchronously
- Triple the cross-node replication traffic for storage, on top of PostgreSQL's WAL traffic

With TopoLVM:
- Each PostgreSQL instance gets a local LVM volume on its node
- PostgreSQL handles replication itself via WAL shipping
- Total copies: three (one per PostgreSQL instance), exactly the durability you actually want
- Writes go directly to local NVMe with no network overhead, and the application's failover machinery is the one source of truth

**Rule of thumb**: if the application replicates, the storage should not. The exception is when the storage layer's failover is dramatically faster than the application's, and even then the right move is usually to invest in faster application-layer failover rather than double-paying for replication.
</details>

### Question 2
A developer creates a PVC with `storageClassName: local-path` requesting 50 Gi. The node has 100 Gi free. The pod ends up writing 90 Gi before anyone notices. What happened, and what would have prevented it?

<details>
<summary>Answer</summary>

**The pod successfully wrote 90 Gi.** local-path-provisioner does not enforce capacity limits; the `50Gi` in the PVC is purely informational and does not become a quota anywhere. The pod can write up to the full 100 Gi of free disk space on the node, or until the underlying filesystem returns `ENOSPC`, whichever comes first.

This is because local-path-provisioner creates a plain directory on the host filesystem. There is no LVM logical volume, no quota, no project quota, no cgroup constraint, and no CSI capability that limits the directory's size. The "limit" you put in the PVC is never converted into an enforcement primitive on disk.

To enforce actual capacity:
- **TopoLVM**: creates an LVM logical volume of exactly the requested size. Writes beyond that size fail with `ENOSPC` at the block layer.
- **OpenEBS LocalPV-LVM**: same LVM-based enforcement.
- **OpenEBS LocalPV-ZFS**: per-dataset quota enforced by ZFS.

```bash
# With TopoLVM, the LV has a fixed size
lvs myvg
# LV          VG    Size
# pvc-abc123  myvg  50.00g   # writes beyond this fail
```

**Operational moral**: never let a workload that has any chance of generating significant data land on local-path. Reserve local-path for genuinely small, ephemeral, or trusted workloads; everything else gets an engine that enforces its own promises.
</details>

### Question 3
Your Longhorn volume shows two of three replicas healthy. The third replica was on a node that you just permanently removed from the cluster. Walk through what Longhorn does, what it cannot do, and what you should monitor.

<details>
<summary>Answer</summary>

**Longhorn automatically rebuilds the missing replica on another available node** if there is one with sufficient disk space and the right scheduling tags.

The sequence:
1. Longhorn detects the node is gone (the node controller marks it `NotReady`, then the cluster eventually deletes the Node object).
2. After the `replica-replenishment-wait-interval` (default 600 seconds, ten minutes), Longhorn schedules a new replica on a healthy node that has enough free space and matches any disk-tag constraints on the volume.
3. The engine copies data from one of the two healthy replicas to the new replica in the background.
4. During the rebuild, reads and writes continue normally and are served by the two healthy replicas; latency may rise slightly because of rebuild bandwidth competition.
5. Once the rebuild is complete, the volume returns to three healthy replicas and the alert clears.

**What Longhorn cannot do**: place a replica where there is no eligible node. If no other node has space, or if every other node is excluded by anti-affinity or by disk-tag selection, the volume stays degraded at two replicas. It is still fully operational but has reduced redundancy, and Longhorn will continuously retry placement.

**What to monitor**:
```bash
# Look at replicas for this specific volume
kubectl -n longhorn-system get replicas.longhorn.io \
  -l longhornvolume=pvc-abc123

# Check the volume's robustness condition
kubectl -n longhorn-system get volume pvc-abc123 \
  -o jsonpath='{.status.robustness}'   # healthy | degraded | unknown
```

Set an alert on `longhorn_volume_robustness != "healthy"` for longer than fifteen minutes; that is the canonical Longhorn health signal.
</details>

### Question 4
You need to store 500 GiB of ML training data that eight pods read simultaneously, all on different nodes. The data is written once and read many times. None of the local storage solutions in this module fit by themselves. Why not, and what are your real options?

<details>
<summary>Answer</summary>

**No local storage option in this module supports `ReadWriteMany` (RWX) cleanly across nodes**, which is what eight pods on eight nodes reading the same dataset requires:

- local-path, TopoLVM, OpenEBS LVM, OpenEBS ZFS: only `ReadWriteOnce` (RWO), one node at a time.
- Longhorn: supports RWX but only via an internal NFS share fronting the volume, which adds a single-node bottleneck and re-introduces the durability question for that NFS pod.

**Real options, in order of preference**:
1. **CephFS** (from Module 4.2): a true distributed POSIX filesystem, handles fan-out concurrent reads exceptionally well, and is the default answer if Ceph is already in the cluster.
2. **NFS server (or Trident-NAS, or Synology, etc.)**: simple, well understood, fine for read-heavy workloads, but the single NFS server is your blast radius unless you cluster it.
3. **Object storage (MinIO, Ceph RGW)**: if the ML framework supports S3-compatible reads natively (most modern frameworks do), this is often the fastest path because S3 is naturally fan-out-friendly.
4. **Pre-load to local storage**: copy the dataset to each node's local volume during pod startup, accept the storage duplication, and read locally. Often the fastest at run-time and the cheapest at scale, at the cost of slower pod startup and 8× storage usage.

If the dataset fits on a single NVMe and run-time performance matters more than storage efficiency, the pre-load approach is fastest:
```yaml
initContainers:
  - name: data-loader
    image: busybox
    command: ["cp", "-r", "/shared/dataset", "/local/dataset"]
```
The init container fans the dataset out from a shared source (CephFS, S3, NFS) onto each node's local NVMe once, and the application then reads at local-NVMe speed for the rest of its lifetime.
</details>

### Question 5
A platform engineer installed Longhorn on a five-node cluster, set `defaultReplicaCount: 3`, and then provisioned 200 small PVCs for a developer-platform self-service portal. CPU on the longhorn-manager pods spikes to several cores per node and the pods start OOMKilling. Diagnose the root cause and propose two mitigations.

<details>
<summary>Answer</summary>

**Root cause: per-volume engine-pod overhead at scale.** Longhorn creates one engine pod per active volume on the node hosting the consumer pod, and one replica per node up to `replicaCount`. With 200 PVCs at three replicas each, the cluster is running 200 engine pods and 600 replica pods on top of the manager DaemonSet, even before any data is written. The `longhorn-manager` is responsible for reconciling all of these custom resources, and at 200 volumes the controller queue depth grows enough to push CPU and memory well past the chart's default requests/limits.

This is the architectural tradeoff highlighted in the "Stop and think" prompt: per-volume isolation is great for blast radius and debugging, but it is linear in volume count, and Ceph's pooled architecture wins at high volume counts because it amortizes the controller overhead.

**Mitigations**:

1. **Cap volume count per cluster, or shard.** Set a soft cap (for example, 100 volumes per Longhorn instance) and either deny PVC creation past the cap or stand up a second cluster for the next wave. The hard truth is that Longhorn's per-volume model is not the right tool for "cattle PVCs" at very high counts.

2. **Raise the manager's resources and tune intervals.** Increase `longhorn-manager` `resources.requests` and `resources.limits` (commonly to one CPU and 1 GiB), increase the `replica-replenishment-wait-interval` so the controller is not constantly recomputing placement, and consider lowering the default replica count to two for non-critical volumes to halve the replica-pod count.

3. **Reconsider the storage choice for self-service.** A self-service developer portal whose PVCs are mostly small, ephemeral, and not durability-critical is exactly the workload that fits TopoLVM or OpenEBS LocalPV-LVM. If you can tolerate the per-volume node pin (which you can for most dev workloads), switching the developer-platform StorageClass to TopoLVM eliminates the engine-pod overhead entirely.
</details>

### Question 6
You took an OpenEBS LocalPV-LVM snapshot of a database volume at 10:00, the database team kept writing through the day, and at 16:00 you tried to take a second snapshot and it failed with thin-pool errors. The LV itself is fine. What happened, and what should the runbook say?

<details>
<summary>Answer</summary>

**The thin pool filled, not the logical volume.** LocalPV-LVM uses LVM thin provisioning: the volume group has a thin pool, and each LV (including snapshots) consumes extents from that pool only as data is written. A snapshot starts at zero extents and grows by copy-on-write whenever the source LV is written; if the database wrote heavily through the day, every changed block had to be copied to preserve the 10:00 view, and the thin pool grew accordingly.

When the thin pool's `Data%` approaches 100%, two things happen: existing LVs may start failing writes (the kernel will return I/O errors rather than silently dropping data), and new snapshot creation fails because there are no free extents to allocate the new snapshot's metadata. The LV itself looks fine because its size is unchanged; the *pool* is the resource that ran out.

**Runbook entries the team should add**:

- **Monitor**: alert on `Data%` and `Meta%` of every thin pool with `lvs -o name,data_percent,metadata_percent` exported via the node-exporter textfile collector. Page at 80%, urgent at 90%.
- **Snapshot retention**: do not keep LVM thin snapshots indefinitely. Treat them as short-window rollback (hours to days), and schedule deletion of old snapshots so the CoW divergence is bounded.
- **Capacity planning**: size the thin pool with explicit headroom for the worst-case CoW scenario, which is the largest expected source LV times the number of snapshots you keep, plus a margin for legitimate growth.
- **Recovery**: when a pool is full, the immediate fix is to delete the oldest snapshots (which frees the CoW extents they were holding) before the source LVs hit write errors. There is no graceful "extend on the fly" if the underlying VG itself is also full.
</details>

### Question 7
Your cluster has both NVMe-equipped nodes and HDD-equipped nodes. A team's analytics workload has been scheduling onto NVMe nodes and pushing your Postgres pods off them. Using TopoLVM, design the StorageClass and scheduling story that keeps the analytics workload on HDD without breaking Postgres.

<parameter name="summary"></parameter>
<details>
<summary>Answer</summary>

**Use TopoLVM device classes plus pod-level constraints, not the StorageClass alone.** The StorageClass tells TopoLVM which volume group to allocate from; it does not by itself prevent the pod from also requesting CPU or memory on a non-storage-matched node. You need two layers working together.

**Layer 1: device classes per node type.** On NVMe nodes, configure `lvmd` with a device class named `nvme` backed by the NVMe volume group; on HDD nodes, configure a device class named `hdd` backed by the HDD volume group. Define two StorageClasses (`topolvm-nvme` and `topolvm-hdd`) that target those device classes respectively, both with `volumeBindingMode: WaitForFirstConsumer`. The scheduler now sees `topolvm.io/capacity-nvme` and `topolvm.io/capacity-hdd` as separate extended resources per node, and a PVC that targets `topolvm-hdd` cannot land on a node that has only NVMe capacity.

**Layer 2: workload-level node selection.** Label nodes with `tier=nvme` or `tier=hdd`. The Postgres StatefulSet uses `nodeAffinity: tier=nvme` and `storageClassName: topolvm-nvme`; the analytics workload uses `nodeAffinity: tier=hdd` and `storageClassName: topolvm-hdd`. The combination guarantees that Postgres lands on NVMe nodes with NVMe storage, the analytics job lands on HDD nodes with HDD storage, and neither workload can starve the other for the wrong disk tier.

**Why both layers**: device classes alone keep the *volume* on the right disk but do not stop the analytics *pod* from scheduling onto an NVMe node and consuming CPU there. Node affinity alone keeps the pod on the right node but, with a single device class, would let TopoLVM allocate from the wrong VG. Use both, and the scheduler enforces the design at every layer it can.
</details>

### Question 8
Your team operates a four-node cluster with Longhorn, and a junior engineer asks "why don't we just set replicaCount to four so every volume is on every node?" Give two concrete reasons that is a bad idea, and explain the right default.

<details>
<summary>Answer</summary>

**Two concrete reasons**:

1. **Linear write-amplification cost.** Every write the application issues is mirrored synchronously to every replica before the engine acknowledges. At three replicas, every write touches three nodes and three disks; at four, every write touches four nodes and four disks. You have just increased the disk write bandwidth, the network bandwidth between nodes, and the tail-latency surface area by 33% with no durability gain that the workload can actually use. Three replicas already survive any two simultaneous node failures with degraded service, which is more than the four-node cluster can tolerate operationally anyway (losing two of four nodes leaves a 50% cluster, which is usually fatal for the rest of the workload regardless of storage).

2. **No headroom for replica rebuild.** When a node goes away and Longhorn tries to rebuild the missing replica on another node, it needs at least one *other* node with free space to place the new replica on. With four nodes and four replicas, there is nowhere to rebuild: the replica is on every node already. The volume is stuck at three healthy replicas (degraded) until the failed node returns; if a second node goes away in that window, you are running on two replicas with zero rebuild target, which is exactly the brittle state Longhorn was supposed to prevent.

**Right default**: `replicaCount: min(3, number_of_nodes)` for production volumes. Three replicas is the standard durability/cost trade-off for replicated block storage; if you only have two nodes, use two and accept the reduced durability; if you have many nodes, three is still the right answer because the marginal durability gain past three is dominated by correlated failure modes (rack power, network partition) that more storage replicas cannot fix anyway. The right way to spend the durability budget past three is on cross-node *backups* to an external store, not on more in-cluster replicas.
</details>

---

## Hands-On Exercise: Compare local-path, TopoLVM, and Longhorn

This exercise walks all three classes of local storage end-to-end on a single kind cluster, so you experience the operational shape of each engine rather than just reading about it. Plan on roughly 30 minutes including the Longhorn install. The goal is to internalize the three behaviors that matter most: pod-to-node pinning, capacity enforcement, and cross-node replica placement.

```bash
# Create a kind cluster with three worker nodes
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

# Step 3: Verify pod is pinned to a specific node and confirm the PV's nodeAffinity
kubectl get pod writer -o jsonpath='{.spec.nodeName}'
PV=$(kubectl get pvc local-pvc -o jsonpath='{.spec.volumeName}')
kubectl get pv "$PV" -o jsonpath='{.spec.nodeAffinity}' | jq

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
kubectl -n longhorn-system get replicas.longhorn.io \
  -o custom-columns=NAME:.metadata.name,VOLUME:.spec.volumeName,NODE:.spec.nodeID

# Step 6 (optional, if you have lvm tooling on the kind nodes):
# Try the OpenEBS LocalPV-LVM walkthrough from earlier in the module
# against a sparse loopback device, take a snapshot, simulate corruption,
# and restore. This is the highest-value step in the exercise.

# Cleanup
kubectl delete pod writer
kubectl delete pvc local-pvc longhorn-pvc
kind delete cluster
```

### Success Criteria

- [ ] local-path PVC bound and data written successfully
- [ ] Pod pinned to a specific node, confirmed both via `spec.nodeName` and via the PV's `nodeAffinity`
- [ ] Longhorn PVC has replicas on multiple nodes, verified via the `replicas.longhorn.io` CRD
- [ ] You can articulate, in one sentence each, when local-path, TopoLVM, OpenEBS LocalPV-LVM, OpenEBS LocalPV-ZFS, and Longhorn are each the right answer
- [ ] (Stretch) You completed the OpenEBS LocalPV-LVM snapshot-and-restore worked example and observed the marker file rewinding from the corrupted state back to the original

---

## Next Module

Continue to [Module 5.1: Private Cloud Platforms](../../multi-cluster/module-5.1-private-cloud/) to learn how VMware vSphere, OpenStack, and Harvester provide infrastructure abstraction layers for on-premises Kubernetes, including how those platforms handle storage, networking, and scheduling above the bare-metal layer you have been working at in this part of the curriculum.

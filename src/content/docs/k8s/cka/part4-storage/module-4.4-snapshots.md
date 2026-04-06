---
title: "Module 4.4: Volume Snapshots & Cloning"
slug: k8s/cka/part4-storage/module-4.4-snapshots
sidebar:
  order: 5
lab:
  id: cka-4.4-snapshots
  url: https://killercoda.com/kubedojo/scenario/cka-4.4-snapshots
  duration: "30 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Data protection and cloning
>
> **Time to Complete**: 30-40 minutes
>
> **Prerequisites**: Module 4.2 (PV & PVC), Module 4.3 (StorageClasses)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Create** VolumeSnapshots and restore PVCs from snapshots for backup and recovery
- **Configure** VolumeSnapshotClasses and explain how they relate to StorageClasses
- **Implement** a snapshot-based backup strategy for stateful workloads
- **Debug** snapshot failures by checking snapshot controller logs and CSI driver capabilities

---

## Why This Module Matters

Volume snapshots provide point-in-time copies of your persistent data - essential for backups, disaster recovery, and creating test environments. Volume cloning lets you create new volumes from existing ones. The CKA exam may test your understanding of these data protection primitives, especially as they become more common in production Kubernetes environments.

> **The Camera Analogy**
>
> Think of a VolumeSnapshot like taking a photo of your data at a specific moment. The photo captures exactly what your disk looked like at that instant. Later, you can use that photo to restore your disk to that exact state, or create a new disk that starts as a copy of that moment. The VolumeSnapshotClass is like your camera settings - it determines how the snapshot is taken and stored.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand the snapshot architecture (VolumeSnapshotClass, VolumeSnapshot, VolumeSnapshotContent)
- Create VolumeSnapshots from existing PVCs
- Restore volumes from snapshots
- Clone volumes using dataSource
- Understand CSI requirements for snapshots

---

## Did You Know?

- **Snapshots are incremental**: Most storage backends store snapshots as diffs from the original, saving space
- **CSI is required**: The legacy in-tree volume plugins don't support snapshots - you need CSI drivers
- **Copy-on-write**: Many storage systems use CoW for snapshots, making them nearly instant to create
- **Cross-namespace restore**: VolumeSnapshotContent is cluster-scoped, enabling disaster recovery patterns

---

## Part 1: Snapshot Architecture

### 1.1 The Three Snapshot Resources

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Snapshot Architecture                              │
│                                                                       │
│   Similar to PV/PVC model:                                           │
│                                                                       │
│   VolumeSnapshotClass         VolumeSnapshot        VolumeSnapshot   │
│   (cluster-scoped)            (namespaced)          Content          │
│   ┌─────────────────┐         ┌─────────────┐      (cluster-scoped)  │
│   │ Defines HOW     │         │ Request to  │      ┌─────────────┐  │
│   │ snapshots are   │         │ snapshot a  │      │ Actual      │  │
│   │ created         │◄────────│ specific PVC│─────►│ snapshot    │  │
│   │                 │         │             │      │ reference   │  │
│   │ - driver        │         │ - source    │      │             │  │
│   │ - deletionPolicy│         │ - class     │      │ - driver    │  │
│   └─────────────────┘         └─────────────┘      │ - handle    │  │
│                                                     └─────────────┘  │
│                                                                       │
│   Admin creates               Dev creates          Auto-created      │
│   (once per cluster)          (when needed)        (by controller)   │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 How It Maps to PV/PVC

| Storage | Snapshots |
|---------|-----------|
| StorageClass | VolumeSnapshotClass |
| PersistentVolume | VolumeSnapshotContent |
| PersistentVolumeClaim | VolumeSnapshot |

### 1.3 Prerequisites

Before using snapshots, you need:
1. **CSI driver** that supports snapshots (not all do)
2. **Snapshot controller** deployed in cluster
3. **Snapshot CRDs** installed
4. **VolumeSnapshotClass** created

```bash
# Check if snapshot CRDs are installed
k get crd | grep snapshot
# volumesnapshotclasses.snapshot.storage.k8s.io
# volumesnapshotcontents.snapshot.storage.k8s.io
# volumesnapshots.snapshot.storage.k8s.io

# Check for snapshot controller
k get pods -n kube-system | grep snapshot
```

---

## Part 2: VolumeSnapshotClass

### 2.1 Creating a VolumeSnapshotClass

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
  annotations:
    snapshot.storage.kubernetes.io/is-default-class: "true"  # Optional
driver: ebs.csi.aws.com                    # Must match CSI driver
deletionPolicy: Delete                      # Delete or Retain
parameters:                                 # Driver-specific params
  # Example for some drivers:
  # csi.storage.k8s.io/snapshotter-secret-name: snap-secret
  # csi.storage.k8s.io/snapshotter-secret-namespace: default
```

### 2.2 Deletion Policies

| Policy | Behavior |
|--------|----------|
| Delete | VolumeSnapshotContent and underlying snapshot deleted when VolumeSnapshot deleted |
| Retain | VolumeSnapshotContent and snapshot retained after VolumeSnapshot deletion |

### 2.3 Cloud-Specific Examples

**AWS EBS CSI**:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
```

**GCP PD CSI**:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: gcp-snapclass
driver: pd.csi.storage.gke.io
deletionPolicy: Delete
parameters:
  storage-locations: us-central1
```

**Azure Disk CSI**:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: azure-snapclass
driver: disk.csi.azure.com
deletionPolicy: Delete
parameters:
  incremental: "true"
```

---

## Part 3: Creating Snapshots

### 3.1 Creating a VolumeSnapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: data-snapshot
  namespace: production
spec:
  volumeSnapshotClassName: csi-snapclass   # Reference to class
  source:
    persistentVolumeClaimName: data-pvc    # PVC to snapshot
```

### 3.2 Snapshot Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Snapshot Creation Flow                          │
│                                                                      │
│   1. Create VolumeSnapshot                                          │
│          │                                                          │
│          ▼                                                          │
│   2. Snapshot controller validates                                  │
│      - PVC exists                                                   │
│      - VolumeSnapshotClass exists                                   │
│      - CSI driver supports snapshots                                │
│          │                                                          │
│          ▼                                                          │
│   3. CSI driver creates snapshot on storage backend                 │
│          │                                                          │
│          ▼                                                          │
│   4. VolumeSnapshotContent created (auto)                          │
│          │                                                          │
│          ▼                                                          │
│   5. VolumeSnapshot status: readyToUse=true                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Checking Snapshot Status

```bash
# List snapshots
k get volumesnapshot -n production
# NAME            READYTOUSE   SOURCEPVC   SOURCESNAPSHOTCONTENT   RESTORESIZE   SNAPSHOTCLASS
# data-snapshot   true         data-pvc                           10Gi          csi-snapclass

# Detailed status
k describe volumesnapshot data-snapshot -n production

# Check the VolumeSnapshotContent
k get volumesnapshotcontent
```

### 3.4 Snapshot Status Fields

```yaml
status:
  boundVolumeSnapshotContentName: snapcontent-xxxxx
  creationTime: "2024-01-15T10:30:00Z"
  readyToUse: true                        # Snapshot is ready
  restoreSize: 10Gi                       # Size when restored
  error:                                  # If failed, error message here
```

> **Pause and predict**: You take a snapshot of a 50Gi PVC that only has 2Gi of data written. When you restore from this snapshot, must the new PVC request 50Gi, or can it request just 2Gi? What does the `restoreSize` field tell you?

---

## Part 4: Restoring from Snapshots

### 4.1 Creating PVC from Snapshot

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-data
  namespace: production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd              # StorageClass for new PVC
  resources:
    requests:
      storage: 10Gi                       # Must be >= snapshot size
  dataSource:                             # The magic part!
    name: data-snapshot                   # Name of VolumeSnapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### 4.2 Restore Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Restore from Snapshot                           │
│                                                                      │
│   VolumeSnapshot                    New PVC                          │
│   ┌─────────────┐                   ┌─────────────┐                 │
│   │ data-snap   │                   │ restored    │                 │
│   │             │                   │             │                 │
│   │ restoreSize:│◄──dataSource──────│ storage:    │                 │
│   │ 10Gi        │                   │ 10Gi        │                 │
│   └──────┬──────┘                   └──────┬──────┘                 │
│          │                                 │                         │
│          ▼                                 ▼                         │
│   VolumeSnapshotContent             New PV (with data)              │
│   (contains snapshot                (provisioned from               │
│    handle)                           snapshot)                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Cross-Namespace Restore

VolumeSnapshotContent is cluster-scoped, so you can restore in different namespaces:

```yaml
# In namespace "dr-test"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dr-restore
  namespace: dr-test              # Different namespace!
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
  dataSourceRef:                  # Use dataSourceRef for cross-namespace
    name: data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
    namespace: production         # Source namespace
```

**Note**: Cross-namespace restore requires Kubernetes 1.26+ and proper RBAC.

---

## Part 5: Volume Cloning

### 5.1 What Is Volume Cloning?

Cloning creates a new PVC with data from an existing PVC, without creating a snapshot first.

```
┌─────────────────────────────────────────────────────────────────────┐
│               Snapshot vs Clone                                      │
│                                                                      │
│   SNAPSHOT                          CLONE                            │
│   ────────                          ─────                            │
│   PVC → Snapshot → New PVC          PVC → New PVC (direct)          │
│                                                                      │
│   Two-step process                  One-step process                 │
│   Point-in-time backup              Immediate copy                   │
│   Can restore multiple times        Single copy operation            │
│   Snapshot persists                 No intermediate artifact         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Creating a Clone

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cloned-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi                 # Must be >= source PVC
  dataSource:                       # Clone from existing PVC
    name: source-pvc                # Name of source PVC
    kind: PersistentVolumeClaim     # Different kind than snapshot!
```

### 5.3 Clone Requirements

- Source and clone must be in **same namespace**
- Storage backend must support cloning
- Clone size must be >= source size
- Same StorageClass typically required

> **Stop and think**: You need to create a test environment with a copy of production data. You have two options: (1) snapshot the production PVC and restore in the test namespace, or (2) clone the production PVC directly. Which approach works for cross-namespace scenarios, and which does not? What are the trade-offs?

### 5.4 Clone Use Cases

| Use Case | Description |
|----------|-------------|
| Dev/Test environments | Clone production data for testing |
| Pre-upgrade backups | Clone before risky changes |
| Data analysis | Clone for analytics without affecting production |
| Parallel processing | Multiple clones for parallel workloads |

---

## Part 6: Best Practices

### 6.1 Backup Strategy

```yaml
# Create snapshots on schedule using CronJob or external tool
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: daily-backup-2024-01-15
  labels:
    backup-type: daily
    source-pvc: database-data
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: database-data
```

### 6.2 Snapshot Retention

```bash
# Clean up old snapshots (example script concept)
# Keep last 7 daily, 4 weekly, 12 monthly

# List snapshots older than 7 days with daily label
k get volumesnapshot -l backup-type=daily --sort-by=.metadata.creationTimestamp
```

### 6.3 Application Consistency

> **Pause and predict**: You take a snapshot of a MySQL database PVC while the database is actively processing transactions. When you restore from this snapshot, will the database start cleanly, or will it be in an inconsistent state? What should you do before taking the snapshot?

For consistent snapshots:
1. **Pause writes** before snapshot (if possible)
2. **Flush buffers** to disk
3. **Take snapshot** quickly
4. **Resume writes**

```bash
# Example: MySQL flush before snapshot
k exec mysql-pod -- mysql -e "FLUSH TABLES WITH READ LOCK;"
# Create snapshot here
k exec mysql-pod -- mysql -e "UNLOCK TABLES;"
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No CSI driver | Snapshots not supported | Install CSI driver with snapshot support |
| Missing snapshot CRDs | VolumeSnapshot resource unknown | Install snapshot CRDs |
| Wrong driver in SnapshotClass | Snapshot fails silently | Match driver to CSI driver name |
| Restore size too small | PVC won't provision | Use size >= restoreSize |
| Clone cross-namespace | Not allowed | Clones must be same namespace as source |
| Deleting source PVC | Clones may fail | Ensure clone completes before deleting source |

---

## Quiz

### Q1: Disaster Recovery Decision
Your production PostgreSQL database has corrupted data after a bad migration. You have both a VolumeSnapshot from 1 hour ago and the original PVC (now corrupted) still running. Your manager asks: "Should we clone the PVC or restore from the snapshot?" What do you recommend and why?

<details>
<summary>Answer</summary>

You should **restore from the snapshot**, not clone the PVC. Cloning copies the PVC's **current** state, which contains the corrupted data from the bad migration. The VolumeSnapshot captured a point-in-time copy from 1 hour ago, before the corruption occurred. Create a new PVC with `dataSource` referencing the snapshot (`kind: VolumeSnapshot`), then point the application at the restored PVC. The key distinction: snapshots preserve historical state (a "photo" of a past moment), while clones copy the live current state. In a corruption scenario, you always want the historical snapshot, not a clone of the corruption.

</details>

### Q2: Snapshot Setup Failure
A developer creates a VolumeSnapshot resource, but it stays in `readyToUse: false` indefinitely. Running `kubectl get volumesnapshotclass` returns "No resources found." The cluster uses the AWS EBS CSI driver for storage. What is missing, and what are all the components that must be in place before snapshots work?

<details>
<summary>Answer</summary>

The cluster is missing the snapshot infrastructure. Three things must be installed: (1) **Snapshot CRDs** -- the custom resource definitions for VolumeSnapshot, VolumeSnapshotClass, and VolumeSnapshotContent (install from the kubernetes-csi/external-snapshotter repository). (2) **Snapshot controller** -- a controller deployment that watches VolumeSnapshot resources and orchestrates the lifecycle (deployed in kube-system). (3) **VolumeSnapshotClass** -- defines which CSI driver handles snapshots and the deletion policy. Without the VolumeSnapshotClass, the snapshot controller does not know which driver to call. Note that just having the EBS CSI driver installed is not enough -- the snapshot sidecar and controller are separate components that must be explicitly deployed.

</details>

### Q3: Cross-Namespace Test Environment
You need to create a test environment in the `staging` namespace using production data from the `production` namespace. You try cloning the production PVC from staging, but it fails. You then try creating a VolumeSnapshot in `production` and restoring it in `staging`. Explain why the clone failed and whether the snapshot approach works.

<details>
<summary>Answer</summary>

The clone failed because PVC cloning requires the **source and destination to be in the same namespace** -- this is a hard limitation. The snapshot approach **does work** because VolumeSnapshotContent (the actual snapshot reference) is **cluster-scoped**, not namespaced. The workflow is: (1) Create a VolumeSnapshot in the `production` namespace pointing at the production PVC. (2) In the `staging` namespace, create a new PVC with `dataSourceRef` referencing the snapshot (using the `namespace: production` field, available in Kubernetes 1.26+). The new PVC gets a fresh PV provisioned from the snapshot data. This is the standard pattern for cross-namespace data copies and disaster recovery testing.

</details>

### Q4: Restore Size Gotcha
You snapshot a 100Gi PVC that only contains 5Gi of actual data. When restoring, you create a new PVC with `resources.requests.storage: 10Gi`, thinking you only need enough for the 5Gi of data. The restore fails. Why, and what size should you request?

<details>
<summary>Answer</summary>

The restore fails because the new PVC's requested size must be **greater than or equal to the snapshot's `restoreSize`**, which reflects the original PVC's capacity (100Gi), not the amount of data written. The `restoreSize` field in the VolumeSnapshot status tells you the minimum size required. Even though only 5Gi of data exists, the snapshot captures the entire volume structure at 100Gi. You must request at least 100Gi for the new PVC. You can request more (e.g., 200Gi) but never less. This is important for capacity planning -- snapshots of large volumes require equally large (or larger) restore targets.

</details>

### Q5: Application Consistency Dilemma
A team takes hourly VolumeSnapshots of their MySQL database PVC using a CronJob. After a failure, they restore from the latest snapshot, but MySQL reports corrupted InnoDB tables and refuses to start. The snapshot was taken while the database was actively processing transactions. What went wrong, and how should the backup strategy be redesigned?

<details>
<summary>Answer</summary>

The snapshot captured the volume while MySQL had **unflushed data in memory buffers** and **uncommitted transactions in flight**. This creates a "crash-consistent" snapshot (equivalent to pulling the power cord), not an "application-consistent" one. InnoDB can usually recover from crash-consistent state, but complex in-flight transactions may cause corruption. The fix is to make snapshots **application-consistent**: before each snapshot, run `FLUSH TABLES WITH READ LOCK` to flush all buffers to disk and pause writes, take the snapshot, then `UNLOCK TABLES` to resume. In production, tools like Velero with pre-snapshot hooks automate this. Alternatively, use MySQL's built-in replication to take snapshots from a read-replica that can be temporarily paused without affecting production.

</details>

---

## Hands-On Exercise: Snapshot and Restore

### Prerequisites
This exercise requires a cluster with:
- CSI driver that supports snapshots
- Snapshot controller and CRDs installed

If using kind or minikube, you may need to install these manually.

> **Local Environment Setup**: To install the Snapshot CRDs and Controller in local environments like `kind` or `minikube`, you can apply the manifests directly from the official Kubernetes CSI external-snapshotter repository:
> ```bash
> # Install Snapshot CRDs
> kubectl kustomize https://github.com/kubernetes-csi/external-snapshotter/client/config/crd | kubectl create -f -
> 
> # Install Snapshot Controller
> kubectl -n kube-system kustomize https://github.com/kubernetes-csi/external-snapshotter/deploy/kubernetes/snapshot-controller | kubectl create -f -
> ```
> For more detailed instructions and to ensure compatibility with your cluster version, refer to the [external-snapshotter documentation](https://github.com/kubernetes-csi/external-snapshotter).

### Task 1: Check Snapshot Support

```bash
# Verify CRDs exist
k get crd | grep snapshot

# Check for VolumeSnapshotClass
k get volumesnapshotclass

# If none exists, you'll need to create one based on your CSI driver
```

### Task 2: Create Test Data

```bash
# Create namespace
k create ns snapshot-lab

# Create a PVC
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: source-data
  namespace: snapshot-lab
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard    # Use your cluster's StorageClass
EOF

# Create pod to write data
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-writer
  namespace: snapshot-lab
spec:
  containers:
  - name: writer
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Important data created at $(date)" > /data/important.txt; sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: source-data
EOF

# Wait for data to be written
sleep 10
k exec -n snapshot-lab data-writer -- cat /data/important.txt
```

### Task 3: Create VolumeSnapshotClass (if needed)

```bash
# Example for AWS EBS CSI (modify for your driver)
cat <<EOF | k apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com    # Change to your CSI driver
deletionPolicy: Delete
EOF
```

### Task 4: Create Snapshot

```bash
cat <<EOF | k apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: source-snapshot
  namespace: snapshot-lab
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: source-data
EOF

# Wait for snapshot to be ready
k get volumesnapshot -n snapshot-lab -w
# Wait until READYTOUSE shows "true"
```

### Task 5: "Corrupt" the Original Data

```bash
# Simulate data loss
k exec -n snapshot-lab data-writer -- sh -c 'echo "Corrupted!" > /data/important.txt'
k exec -n snapshot-lab data-writer -- cat /data/important.txt
# Shows: Corrupted!
```

### Task 6: Restore from Snapshot

```bash
# Delete the pod (to release PVC)
k delete pod -n snapshot-lab data-writer

# Create new PVC from snapshot
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-data
  namespace: snapshot-lab
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 1Gi
  dataSource:
    name: source-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
EOF

# Create pod to verify restored data
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: data-reader
  namespace: snapshot-lab
spec:
  containers:
  - name: reader
    image: busybox:1.36
    command: ['sh', '-c', 'cat /data/important.txt; sleep 3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: restored-data
EOF

# Verify original data is restored
k logs -n snapshot-lab data-reader
# Should show: Important data created at <original timestamp>
```

### Success Criteria
- [ ] VolumeSnapshotClass created
- [ ] VolumeSnapshot shows readyToUse: true
- [ ] New PVC created from snapshot
- [ ] Restored data matches original (not corrupted version)

### Cleanup

```bash
k delete ns snapshot-lab
k delete volumesnapshotclass csi-snapclass
```

---

## Practice Drills

### Drill 1: List Snapshot Resources (1 min)
```bash
# Task: Find all snapshot-related resources
k api-resources | grep snapshot
```

### Drill 2: Create VolumeSnapshotClass (2 min)
```bash
# Task: Create SnapshotClass for your CSI driver with Delete policy
cat <<EOF | k apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: practice-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
EOF
```

### Drill 3: Check Snapshot Status (1 min)
```bash
# Task: Verify a snapshot is ready to use
k get volumesnapshot <name> -o jsonpath='{.status.readyToUse}'
```

### Drill 4: Restore from Snapshot (2 min)
```bash
# Task: Create PVC from snapshot "backup-snap"
# Key: dataSource with kind: VolumeSnapshot
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  dataSource:
    name: backup-snap
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
EOF
```

### Drill 5: Clone PVC (2 min)
```bash
# Task: Clone PVC "source-pvc" to "clone-pvc"
# Key: dataSource with kind: PersistentVolumeClaim
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: clone-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  dataSource:
    name: source-pvc
    kind: PersistentVolumeClaim
EOF
```

### Drill 6: Find Snapshot Size (1 min)
```bash
# Task: Get the restore size of a snapshot
k get volumesnapshot <name> -o jsonpath='{.status.restoreSize}'
```

### Drill 7: Check VolumeSnapshotContent (1 min)
```bash
# Task: Find the VolumeSnapshotContent for a VolumeSnapshot
k get volumesnapshot <name> -o jsonpath='{.status.boundVolumeSnapshotContentName}'
```

---

## Next Module

Continue to [Module 4.5: Storage Troubleshooting](../module-4.5-troubleshooting/) to learn how to diagnose and fix common storage problems.
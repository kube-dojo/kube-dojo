---
title: "Module 6.4: GKE Storage"
slug: cloud/gke-deep-dive/module-6.4-gke-storage
sidebar:
  order: 5
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Module 6.1 (GKE Architecture)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Persistent Disks (pd-standard, pd-ssd, pd-balanced) and Filestore CSI driver for GKE workloads**
- **Implement volume snapshots and backup schedules using Backup for GKE for stateful application protection**
- **Deploy regional persistent disks for cross-zone high availability of stateful workloads on GKE**
- **Evaluate GKE storage options (Persistent Disk, Filestore, Cloud Storage FUSE) for different access patterns**

---

## Why This Module Matters

In August 2023, an online gaming company running on GKE lost 6 hours of player progress data for 180,000 active users. Their PostgreSQL database was running on a single-zone Persistent Disk attached to a StatefulSet pod. When `us-central1-a` experienced a partial zone outage, the node hosting the database went offline. Because the PD was zonal, it could not be attached to a node in another zone. The StatefulSet controller created a replacement pod in `us-central1-b`, but it could not mount the volume---zonal PDs are locked to their zone. The database was down for 6 hours until the zone recovered. The company's VP of Engineering later estimated the revenue loss at $420,000 and the player trust damage as "incalculable." The fix was straightforward: switch to a **Regional Persistent Disk**, which synchronously replicates data to two zones and can failover in under a minute. It cost 16 cents more per GB per month.

Storage in Kubernetes is where the "cattle, not pets" philosophy meets reality. Stateless pods can be replaced instantly, but pods with Persistent Volumes carry data that must survive restarts, rescheduling, and zone failures. GKE offers multiple storage options---Persistent Disks (block storage), Filestore (managed NFS), Cloud Storage FUSE (object storage as a filesystem), and Backup for GKE (disaster recovery). Choosing the right storage backend and configuring it for resilience is often the difference between a minor disruption and a catastrophic data loss event.

In this module, you will learn the full GKE storage landscape: how the PD CSI driver provisions and attaches disks, when to use regional PDs for high availability, how Filestore provides shared NFS access across pods, how Cloud Storage FUSE mounts GCS buckets as local filesystems, and how Backup for GKE protects your stateful workloads.

---

## Persistent Disk CSI Driver

The **Compute Engine Persistent Disk CSI driver** is the primary block storage driver for GKE. It is installed by default on all GKE clusters and provisions Google Cloud Persistent Disks as Kubernetes PersistentVolumes.

### Disk Types

| Disk Type | Identifier | IOPS (Read) | Throughput (Read) | Use Case | Cost (us-central1) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard** | `pd-standard` | 0.75/GB | 12 MB/s/GB | Logs, cold data, backups | ~$0.040/GB/mo |
| **Balanced** | `pd-balanced` | 6/GB | 28 MB/s/GB | General purpose (default) | ~$0.100/GB/mo |
| **SSD** | `pd-ssd` | 30/GB | 48 MB/s/GB | Databases, latency-sensitive | ~$0.170/GB/mo |
| **Extreme** | `pd-extreme` | Configurable (up to 120K) | Configurable (up to 2.4 GB/s) | SAP HANA, Oracle, high-IOPS | ~$0.125/GB/mo + IOPS |
| **Hyperdisk Balanced** | `hyperdisk-balanced` | Configurable | Configurable | Next-gen general purpose | Variable |

### StorageClasses

GKE provides default StorageClasses, but you should define your own for production workloads.

```bash
# List default StorageClasses
kubectl get storageclasses

# NAME                     PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE
# premium-rwo              pd.csi.storage.gke.io   Delete          WaitForFirstConsumer
# standard                 pd.csi.storage.gke.io   Delete          Immediate
# standard-rwo             pd.csi.storage.gke.io   Delete          WaitForFirstConsumer
```

```yaml
# Custom StorageClass for production databases
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-regional
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd  # Synchronous replication across 2 zones
volumeBindingMode: WaitForFirstConsumer  # Bind when pod is scheduled
reclaimPolicy: Retain  # Do NOT delete the disk when PVC is deleted
allowVolumeExpansion: true  # Allow resizing without downtime

---
# StorageClass for dev/test (cheaper, zonal)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: dev-standard
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-balanced
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
```

### Volume Binding Modes

This is a subtle but important setting:

| Mode | Behavior | When to Use |
| :--- | :--- | :--- |
| `Immediate` | PV is provisioned as soon as PVC is created | Pre-provisioning, when zone does not matter |
| `WaitForFirstConsumer` | PV is provisioned when a pod mounts it | Regional clusters (ensures disk is in the same zone as the pod) |

**War Story**: A team used `Immediate` binding mode in a regional cluster. The PD was provisioned in `us-central1-a`, but the pod was scheduled to `us-central1-c`. The pod hung in `Pending` with the error "disk is in zone us-central1-a, which does not match the zone of node us-central1-c." Always use `WaitForFirstConsumer` in regional clusters.

---

## Regional Persistent Disks

Regional PDs synchronously replicate data to two zones within the same region. This is the critical feature for high-availability stateful workloads.

### How Regional PDs Work

```text
  Zonal PD:                          Regional PD:
  ┌─────────────────┐               ┌─────────────────┐
  │  us-central1-a  │               │  us-central1-a  │
  │  ┌─────────┐    │               │  ┌─────────┐    │
  │  │ PD-SSD  │    │               │  │ PD-SSD  │◄───┼──── Synchronous
  │  │ (data)  │    │               │  │ (copy 1)│    │     replication
  │  └─────────┘    │               │  └─────────┘    │
  │                 │               └─────────────────┘
  │  If zone fails: │               ┌─────────────────┐
  │  DATA IS        │               │  us-central1-b  │
  │  INACCESSIBLE   │               │  ┌─────────┐    │
  └─────────────────┘               │  │ PD-SSD  │◄──── If zone-a fails:
                                    │  │ (copy 2)│    │  Pod restarts in
                                    │  └─────────┘    │  zone-b, mounts
                                    └─────────────────┘  copy 2 (<60 sec)
```

### Provisioning Regional PDs

```yaml
# StatefulSet with Regional PD
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
          value: "change-me-in-production"
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: "2"
            memory: 4Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-regional  # Uses our regional PD StorageClass
      resources:
        requests:
          storage: 50Gi
```

### Failover Behavior

When a zone fails and the pod is rescheduled to another zone:

1. GKE detects the node is unhealthy (~5 minutes by default)
2. The StatefulSet controller creates a replacement pod
3. The pod is scheduled to a healthy zone
4. The Regional PD is detached from the failed zone and attached in the new zone (~30-60 seconds)
5. The pod starts with the same data

```bash
# Force-detach a stuck PD (emergency use only)
gcloud compute disks detach my-disk \
  --zone=us-central1-a \
  --instance=failed-node

# Monitor PV/PVC status during failover
kubectl get pv,pvc -o wide
kubectl describe pv <pv-name> | grep -A 5 "Status"
```

### Volume Snapshots

The PD CSI driver supports Kubernetes VolumeSnapshots for point-in-time backups.

```yaml
# Create a VolumeSnapshotClass
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: pd-snapshot-class
driver: pd.csi.storage.gke.io
deletionPolicy: Retain
parameters:
  storage-locations: us-central1

---
# Take a snapshot of the PostgreSQL PVC
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot-20240315
spec:
  volumeSnapshotClassName: pd-snapshot-class
  source:
    persistentVolumeClaimName: data-postgres-0
```

```bash
# Verify the snapshot
kubectl get volumesnapshot
kubectl describe volumesnapshot postgres-snapshot-20240315

# Restore from snapshot (create a new PVC from the snapshot)
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-restored
spec:
  storageClassName: fast-regional
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  dataSource:
    name: postgres-snapshot-20240315
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
EOF
```

---

## Filestore CSI Driver (Managed NFS)

Filestore provides managed NFS file shares that can be mounted by **multiple pods simultaneously** with `ReadWriteMany` access. This is essential for workloads that need shared filesystem access.

### When to Use Filestore

| Use Case | Why Filestore | Alternative |
| :--- | :--- | :--- |
| CMS shared uploads | Multiple pods write to the same directory | N/A (PD is ReadWriteOnce) |
| ML training data | Large dataset shared across training pods | Cloud Storage FUSE (cheaper) |
| Legacy apps requiring NFS | Application expects a POSIX filesystem | Refactor to use object storage |
| Build artifacts | CI/CD pods share build cache | Cloud Storage (if latency is okay) |

### Filestore Tiers

| Tier | Min Capacity | IOPS | Throughput | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Basic HDD** | 1 TiB | 600 (read) | 100 MB/s (read) | Cold data, infrequent access |
| **Basic SSD** | 2.5 TiB | 60K (read) | 1.2 GB/s (read) | General purpose shared storage |
| **Zonal** | 1 TiB | Up to 170K | Up to 3.6 GB/s | High-performance, single zone |
| **Enterprise** | 1 TiB | Up to 120K | Up to 2.4 GB/s | HA across zones, SLA-backed |

### Setting Up Filestore CSI

```bash
# Enable the Filestore CSI driver on the cluster
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --update-addons=GcpFilestoreCsiDriver=ENABLED

# Verify the driver is installed
kubectl get csidriver filestore.csi.storage.gke.io
```

```yaml
# StorageClass for Filestore
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: filestore-shared
provisioner: filestore.csi.storage.gke.io
parameters:
  tier: basic-ssd
  network: default
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Retain
allowVolumeExpansion: true

---
# PVC requesting shared storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data
spec:
  accessModes:
  - ReadWriteMany  # Multiple pods can write simultaneously
  storageClassName: filestore-shared
  resources:
    requests:
      storage: 2560Gi  # Minimum 2.5 TiB for basic-ssd
```

```yaml
# Two Deployments sharing the same Filestore volume
apiVersion: apps/v1
kind: Deployment
metadata:
  name: writer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: writer
  template:
    metadata:
      labels:
        app: writer
    spec:
      containers:
      - name: writer
        image: busybox
        command: ["sh", "-c", "while true; do echo $(hostname) $(date) >> /shared/log.txt; sleep 5; done"]
        volumeMounts:
        - name: shared
          mountPath: /shared
        resources:
          requests:
            cpu: 50m
            memory: 32Mi
      volumes:
      - name: shared
        persistentVolumeClaim:
          claimName: shared-data

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reader
spec:
  replicas: 3
  selector:
    matchLabels:
      app: reader
  template:
    metadata:
      labels:
        app: reader
    spec:
      containers:
      - name: reader
        image: busybox
        command: ["sh", "-c", "while true; do tail -5 /shared/log.txt; sleep 10; done"]
        volumeMounts:
        - name: shared
          mountPath: /shared
          readOnly: true
        resources:
          requests:
            cpu: 50m
            memory: 32Mi
      volumes:
      - name: shared
        persistentVolumeClaim:
          claimName: shared-data
```

---

## Cloud Storage FUSE CSI Driver

Cloud Storage FUSE mounts GCS buckets as local filesystems inside pods. This gives pods access to petabytes of object storage through standard file system operations.

### How It Works

```text
  ┌──────────────────────────────────────────────┐
  │  Pod                                         │
  │  ┌──────────────────────────────────────┐   │
  │  │  Application                         │   │
  │  │  open("/data/model.bin", "r")        │   │
  │  └──────────────┬───────────────────────┘   │
  │                 │ POSIX file operations      │
  │  ┌──────────────▼───────────────────────┐   │
  │  │  FUSE sidecar (gcsfuse)              │   │
  │  │  Translates file ops → GCS API calls │   │
  │  └──────────────┬───────────────────────┘   │
  └─────────────────┼──────────────────────────┘
                    │ GCS JSON API
  ┌─────────────────▼──────────────────────────┐
  │  Cloud Storage Bucket                      │
  │  gs://my-ml-datasets/model.bin             │
  └────────────────────────────────────────────┘
```

### Enabling Cloud Storage FUSE

```bash
# Enable the Cloud Storage FUSE CSI driver
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --update-addons=GcsFuseCsiDriver=ENABLED

# Verify
kubectl get csidriver gcsfuse.csi.storage.gke.io
```

### Using Cloud Storage FUSE in Pods

```yaml
# PersistentVolume pointing to a GCS bucket
apiVersion: v1
kind: PersistentVolume
metadata:
  name: gcs-pv
spec:
  accessModes:
  - ReadWriteMany
  capacity:
    storage: 5Ti  # Informational only (GCS is unlimited)
  storageClassName: ""
  mountOptions:
  - implicit-dirs  # Show directories from object prefixes
  - uid=1000       # Map files to application user
  - gid=1000
  csi:
    driver: gcsfuse.csi.storage.gke.io
    volumeHandle: my-ml-datasets  # GCS bucket name
    readOnly: false

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gcs-pvc
spec:
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 5Ti
  storageClassName: ""
  volumeName: gcs-pv

---
apiVersion: v1
kind: Pod
metadata:
  name: ml-training
  annotations:
    gke-gcsfuse/volumes: "true"  # Required annotation to inject sidecar
spec:
  serviceAccountName: ml-sa  # Must have Workload Identity with GCS access
  containers:
  - name: trainer
    image: us-central1-docker.pkg.dev/my-project/ml/trainer:v3
    volumeMounts:
    - name: datasets
      mountPath: /data
    resources:
      requests:
        cpu: "4"
        memory: 16Gi
  volumes:
  - name: datasets
    persistentVolumeClaim:
      claimName: gcs-pvc
```

### Cloud Storage FUSE Limitations

| Limitation | Impact | Workaround |
| :--- | :--- | :--- |
| Not POSIX-compliant | No atomic renames, no file locking | Use for read-heavy workloads, not databases |
| Higher latency than PD | Each file op is a GCS API call | Enable file caching for repeated reads |
| Eventual consistency for listings | New files may not appear immediately in `ls` | Use `--stat-cache-ttl=0` for real-time needs |
| No append support | Cannot append to existing files | Write new files instead of appending |

```yaml
# Enable file caching for better read performance
# Add to the pod annotation or PV mount options
metadata:
  annotations:
    gke-gcsfuse/volumes: "true"
    gke-gcsfuse/cpu-limit: "500m"
    gke-gcsfuse/memory-limit: "512Mi"
    gke-gcsfuse/ephemeral-storage-limit: "10Gi"  # Cache size
```

---

## Backup for GKE

Backup for GKE provides managed backup and restore for your entire GKE workloads---including both the Kubernetes configuration (Deployments, Services, ConfigMaps) and the persistent volume data.

### Architecture

```text
  ┌──────────────────────────────────────────────────┐
  │  Backup for GKE                                  │
  │                                                  │
  │  ┌────────────────┐    ┌────────────────┐       │
  │  │  Backup Plan    │    │  Backup Plan    │       │
  │  │  (daily, 30d    │    │  (weekly, 90d   │       │
  │  │   retention)    │    │   retention)    │       │
  │  └───────┬────────┘    └───────┬────────┘       │
  │          │                     │                 │
  │          ▼                     ▼                 │
  │  ┌──────────────────────────────────────┐       │
  │  │  Backups                              │       │
  │  │  backup-2024-03-15-0200 (config+data)│       │
  │  │  backup-2024-03-14-0200 (config+data)│       │
  │  │  backup-2024-03-13-0200 (config+data)│       │
  │  └──────────────────────────────────────┘       │
  │                                                  │
  │  Restores:                                       │
  │  - Same cluster (in-place rollback)              │
  │  - Different cluster (migration/DR)              │
  │  - Selective (specific namespaces only)          │
  └──────────────────────────────────────────────────┘
```

### Setting Up Backup for GKE

```bash
# Enable the Backup for GKE API
gcloud services enable gkebackup.googleapis.com

# Enable the backup agent on the cluster
gcloud container clusters update my-cluster \
  --region=us-central1 \
  --update-addons=BackupRestore=ENABLED

# Create a backup plan (daily backups, 30-day retention)
gcloud beta container backup-restore backup-plans create daily-backup \
  --project=$PROJECT_ID \
  --location=$REGION \
  --cluster=projects/$PROJECT_ID/locations/$REGION/clusters/my-cluster \
  --all-namespaces \
  --include-volume-data \
  --include-secrets \
  --backup-retain-days=30 \
  --backup-delete-lock-days=7 \
  --cron-schedule="0 2 * * *" \
  --paused=false
```

### Creating Manual Backups

```bash
# Create an on-demand backup (before a risky deployment)
gcloud beta container backup-restore backups create pre-deploy-backup \
  --project=$PROJECT_ID \
  --location=$REGION \
  --backup-plan=daily-backup \
  --wait-for-completion

# List backups
gcloud beta container backup-restore backups list \
  --project=$PROJECT_ID \
  --location=$REGION \
  --backup-plan=daily-backup \
  --format="table(name, state, completeTime, resourceCount, volumeCount)"
```

### Restoring from Backup

```bash
# Create a restore plan (defines how backups are restored)
gcloud beta container backup-restore restore-plans create full-restore \
  --project=$PROJECT_ID \
  --location=$REGION \
  --cluster=projects/$PROJECT_ID/locations/$REGION/clusters/my-cluster \
  --backup-plan=projects/$PROJECT_ID/locations/$REGION/backupPlans/daily-backup \
  --all-namespaces \
  --volume-data-restore-policy=RESTORE_VOLUME_DATA_FROM_BACKUP \
  --cluster-resource-conflict-policy=USE_BACKUP_VERSION \
  --namespaced-resource-restore-mode=MERGE_SKIP_ON_CONFLICT

# Execute a restore
gcloud beta container backup-restore restores create restore-20240315 \
  --project=$PROJECT_ID \
  --location=$REGION \
  --restore-plan=full-restore \
  --backup=projects/$PROJECT_ID/locations/$REGION/backupPlans/daily-backup/backups/pre-deploy-backup \
  --wait-for-completion
```

### Selective Namespace Restore

```bash
# Restore only the "payments" namespace from a backup
gcloud beta container backup-restore restore-plans create payments-restore \
  --project=$PROJECT_ID \
  --location=$REGION \
  --cluster=projects/$PROJECT_ID/locations/$REGION/clusters/my-cluster \
  --backup-plan=projects/$PROJECT_ID/locations/$REGION/backupPlans/daily-backup \
  --selected-namespaces=payments \
  --volume-data-restore-policy=RESTORE_VOLUME_DATA_FROM_BACKUP \
  --namespaced-resource-restore-mode=DELETE_AND_RESTORE
```

---

## Storage Decision Matrix

Choosing the right storage for your workload:

```text
  Need block storage for a single pod?
  │
  ├── YES → Is HA required?
  │         ├── YES → Regional PD (pd-ssd or pd-balanced)
  │         └── NO  → Zonal PD (cheaper, dev/test)
  │
  Need shared filesystem across pods?
  │
  ├── YES → How much data?
  │         ├── < 10 TiB, need POSIX → Filestore
  │         └── > 10 TiB, read-heavy → Cloud Storage FUSE
  │
  Need object storage access from pods?
  │
  └── YES → Cloud Storage FUSE (or use GCS client libraries directly)
```

| Factor | PD (Block) | Filestore (NFS) | Cloud Storage FUSE |
| :--- | :--- | :--- | :--- |
| **Access mode** | ReadWriteOnce | ReadWriteMany | ReadWriteMany |
| **Latency** | Sub-ms | Low ms | 10-50ms per operation |
| **Max size** | 64 TiB | 100 TiB | Unlimited |
| **POSIX compliant** | Yes (ext4/xfs) | Yes | No (partial) |
| **Best for** | Databases, stateful apps | Shared data, CMS | ML datasets, logs, archives |
| **Min size** | 10 GiB | 1 TiB (HDD), 2.5 TiB (SSD) | N/A (bucket) |
| **Cost** | $0.04-0.17/GB/mo | $0.20-0.36/GB/mo | $0.020-0.026/GB/mo |

---

## Did You Know?

1. **Regional Persistent Disks perform synchronous replication across exactly two zones in the same region.** Every write to the primary copy must be acknowledged by the secondary copy before the write returns to the application. This adds approximately 1-2ms of write latency compared to a zonal PD, but guarantees zero data loss (RPO=0) during a zone failover. The two zones are chosen automatically by GKE based on the cluster's node topology and cannot be manually selected.

2. **Cloud Storage FUSE was originally developed inside Google for Borg workloads** that needed to read training data from Colossus (Google's internal distributed storage system). The open-source version was released in 2015 and the GKE CSI driver followed in 2023. Internally, Google ML training jobs read petabytes of data per day through FUSE-like interfaces. The GKE CSI driver injects a sidecar container that runs the gcsfuse process, which is why pods need the `gke-gcsfuse/volumes: "true"` annotation.

3. **Backup for GKE does not just snapshot disks---it captures the full Kubernetes state.** A backup includes all Kubernetes resource configurations (Deployments, Services, ConfigMaps, Secrets, CRDs, custom resources), PersistentVolume data (via disk snapshots), and namespace metadata. This means you can restore an entire application stack---not just the data---to a different cluster in a different region. This is what distinguishes it from simply taking PD snapshots manually.

4. **You can expand a Persistent Volume online without stopping the pod.** The PD CSI driver supports volume expansion when the StorageClass has `allowVolumeExpansion: true`. You simply edit the PVC to request a larger size, and the driver resizes the underlying disk and expands the filesystem---all while the pod continues running. However, you can only increase size, never decrease. Shrinking a PV requires creating a new smaller PV, copying data, and switching over.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| Using zonal PD for production databases | Default StorageClass creates zonal disks | Create a StorageClass with `replication-type: regional-pd` |
| Using `Immediate` volume binding in regional clusters | Copied from single-zone examples | Always use `WaitForFirstConsumer` to match disk zone with pod zone |
| Setting reclaim policy to `Delete` on production PVs | Default StorageClass behavior | Use `Retain` for production; manually delete PVs after confirming data is safe |
| Not planning IP ranges for pod CIDR (storage-related) | Forgetting that Filestore needs VPC access | Ensure Filestore network matches the GKE cluster's VPC |
| Choosing Filestore for object storage workloads | Assuming NFS is always better | Use Cloud Storage FUSE for read-heavy, large-scale data; it is 10x cheaper per GB |
| Skipping backup configuration for stateful workloads | "We have replication, we are fine" | Replication protects against hardware failure; backups protect against human error and data corruption |
| Not testing restore procedures | Creating backups but never testing restores | Schedule quarterly restore drills to a test cluster; an untested backup is not a backup |
| Using Cloud Storage FUSE for database storage | Seeing "ReadWriteMany" and assuming POSIX compliance | Cloud Storage FUSE lacks atomic renames and file locking; never use it for databases |

---

## Quiz

<details>
<summary>1. What is the difference between a zonal Persistent Disk and a Regional Persistent Disk?</summary>

A **zonal PD** stores data in a single zone. If that zone becomes unavailable, the disk cannot be accessed or attached to nodes in other zones. A **Regional PD** synchronously replicates data to two zones within the same region. Every write is confirmed in both zones before returning to the application. During a zone failure, the regional PD can be attached to a node in the surviving zone, typically within 60 seconds. Regional PDs cost approximately twice as much as zonal PDs because they store two copies, but they provide zero data loss (RPO=0) and rapid failover (RTO under 1 minute). For any stateful production workload, regional PDs are strongly recommended.
</details>

<details>
<summary>2. Why is `WaitForFirstConsumer` volume binding mode important in regional clusters?</summary>

In a regional cluster, nodes exist across multiple zones (typically 3). With `Immediate` binding, the PV is created as soon as the PVC is submitted, and the PD CSI driver picks a zone for the disk. If the scheduler later places the pod in a different zone, the pod cannot mount the volume because PDs can only be attached to nodes in the same zone (for zonal PDs) or one of two zones (for regional PDs). `WaitForFirstConsumer` delays volume provisioning until a pod references the PVC. At that point, the scheduler picks a node, and the CSI driver creates the disk in the same zone as the node. This guarantees the disk and pod are always co-located.
</details>

<details>
<summary>3. When would you choose Filestore over Cloud Storage FUSE?</summary>

Choose Filestore when your workload requires **true POSIX filesystem semantics**: atomic renames, file locking (`flock`), hard links, or low-latency random reads and writes. Common examples include content management systems with concurrent file uploads, legacy applications that rely on NFS mounts, and build systems with shared caches. Choose Cloud Storage FUSE when you need to access **large datasets** (especially read-heavy ML training data), when data is already in GCS, or when cost is the primary concern. Cloud Storage FUSE is roughly 10x cheaper per GB than Filestore, but it lacks full POSIX compliance and has higher per-operation latency.
</details>

<details>
<summary>4. How does Backup for GKE differ from simply taking PD snapshots?</summary>

PD snapshots capture only the **disk data** for a single Persistent Disk. They do not capture any Kubernetes resource configuration. To restore an application from PD snapshots alone, you need to manually recreate all Kubernetes resources (Deployments, Services, ConfigMaps, Secrets, etc.) and then attach the restored PV. Backup for GKE captures **both** the Kubernetes resource state and the volume data in a single backup. It can restore complete application stacks, including custom resources and CRDs, to the same or a different cluster. It also supports selective namespace restore, backup scheduling, retention policies, and delete locks to prevent accidental deletion of backups.
</details>

<details>
<summary>5. Can you shrink a Persistent Volume after expanding it?</summary>

**No.** Persistent Volume expansion is a one-way operation. Once you increase the size of a PVC, you cannot decrease it. The underlying Google Cloud Persistent Disk does not support shrinking. If you need a smaller volume, you must: (1) create a new PVC with the desired smaller size, (2) copy the data from the old volume to the new one (using a pod that mounts both volumes), (3) update your workload to reference the new PVC, and (4) delete the old PVC. This is an important consideration when planning storage---over-provisioning is hard to undo.
</details>

<details>
<summary>6. What are the minimum capacity requirements for Filestore tiers?</summary>

Filestore has significant minimum capacity requirements that surprise many users. **Basic HDD** requires a minimum of 1 TiB. **Basic SSD** requires a minimum of 2.5 TiB. **Zonal** (high-performance) requires a minimum of 1 TiB. **Enterprise** requires a minimum of 1 TiB. These minimums exist because Filestore provisions dedicated infrastructure for each instance. If you need less than 1 TiB of shared storage, Filestore may be overkill. Consider alternatives like using a PD with an NFS server deployment, or Cloud Storage FUSE if your workload tolerates eventual consistency.
</details>

---

## Hands-On Exercise: Regional PD Failover and Backup for GKE

### Objective

Deploy a stateful application with Regional PDs, simulate a zone failure to observe failover behavior, and use Backup for GKE to backup and restore the application.

### Prerequisites

- `gcloud` CLI installed and authenticated
- A GCP project with billing enabled
- GKE and Backup for GKE APIs enabled

### Tasks

**Task 1: Create a GKE Cluster and Regional StorageClass**

<details>
<summary>Solution</summary>

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1

# Enable APIs
gcloud services enable container.googleapis.com gkebackup.googleapis.com

# Create a regional cluster
gcloud container clusters create storage-demo \
  --region=$REGION \
  --num-nodes=1 \
  --machine-type=e2-standard-2 \
  --release-channel=regular \
  --enable-ip-alias \
  --workload-pool=$PROJECT_ID.svc.id.goog \
  --addons=BackupRestore

# Get credentials
gcloud container clusters get-credentials storage-demo --region=$REGION

# Create the Regional PD StorageClass
kubectl apply -f - <<'EOF'
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: regional-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Retain
allowVolumeExpansion: true
EOF

kubectl get storageclasses
```
</details>

**Task 2: Deploy a Stateful Application with Regional PD**

<details>
<summary>Solution</summary>

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: counter-db
spec:
  clusterIP: None
  selector:
    app: counter-db
  ports:
  - port: 5432

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: counter-db
spec:
  serviceName: counter-db
  replicas: 1
  selector:
    matchLabels:
      app: counter-db
  template:
    metadata:
      labels:
        app: counter-db
    spec:
      terminationGracePeriodSeconds: 10
      containers:
      - name: postgres
        image: postgres:16
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: counter
        - name: POSTGRES_USER
          value: app
        - name: POSTGRES_PASSWORD
          value: demo-password-change-me
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: regional-ssd
      resources:
        requests:
          storage: 10Gi
EOF

# Wait for the StatefulSet to be ready
kubectl rollout status statefulset/counter-db --timeout=180s

# Insert test data
kubectl exec counter-db-0 -- psql -U app -d counter -c \
  "CREATE TABLE visits (id SERIAL PRIMARY KEY, ts TIMESTAMP DEFAULT NOW());"
kubectl exec counter-db-0 -- psql -U app -d counter -c \
  "INSERT INTO visits DEFAULT VALUES; INSERT INTO visits DEFAULT VALUES; INSERT INTO visits DEFAULT VALUES;"
kubectl exec counter-db-0 -- psql -U app -d counter -c \
  "SELECT count(*) FROM visits;"

# Verify the PV is a regional PD
PV_NAME=$(kubectl get pvc data-counter-db-0 -o jsonpath='{.spec.volumeName}')
kubectl get pv $PV_NAME -o yaml | grep -A 5 "nodeAffinity"
```
</details>

**Task 3: Simulate Zone Failure and Observe Failover**

<details>
<summary>Solution</summary>

```bash
# Find which node and zone the pod is running on
NODE=$(kubectl get pod counter-db-0 -o jsonpath='{.spec.nodeName}')
ZONE=$(kubectl get node $NODE -o jsonpath='{.metadata.labels.topology\.kubernetes\.io/zone}')
echo "Pod is on node: $NODE in zone: $ZONE"

# Cordon and drain the node to simulate zone failure
kubectl cordon $NODE
kubectl delete pod counter-db-0 --grace-period=10

# Watch the pod reschedule to another zone
echo "Watching pod reschedule..."
kubectl get pods -w -l app=counter-db &
WATCH_PID=$!
sleep 60
kill $WATCH_PID 2>/dev/null

# Verify the pod restarted in a different zone
NEW_NODE=$(kubectl get pod counter-db-0 -o jsonpath='{.spec.nodeName}')
NEW_ZONE=$(kubectl get node $NEW_NODE -o jsonpath='{.metadata.labels.topology\.kubernetes\.io/zone}')
echo "Pod is now on node: $NEW_NODE in zone: $NEW_ZONE"

# Verify data survived the failover
kubectl exec counter-db-0 -- psql -U app -d counter -c \
  "SELECT count(*) FROM visits;"
# Should still show 3 rows

# Uncordon the original node
kubectl uncordon $NODE
```
</details>

**Task 4: Set Up Backup for GKE**

<details>
<summary>Solution</summary>

```bash
# Create a backup plan
gcloud beta container backup-restore backup-plans create storage-demo-backup \
  --project=$PROJECT_ID \
  --location=$REGION \
  --cluster=projects/$PROJECT_ID/locations/$REGION/clusters/storage-demo \
  --all-namespaces \
  --include-volume-data \
  --include-secrets \
  --backup-retain-days=7

# Create a manual backup
gcloud beta container backup-restore backups create manual-backup-1 \
  --project=$PROJECT_ID \
  --location=$REGION \
  --backup-plan=storage-demo-backup \
  --wait-for-completion

# Verify the backup
gcloud beta container backup-restore backups describe manual-backup-1 \
  --project=$PROJECT_ID \
  --location=$REGION \
  --backup-plan=storage-demo-backup \
  --format="yaml(state, resourceCount, volumeCount, sizeBytes)"
```
</details>

**Task 5: Simulate Data Loss and Restore from Backup**

<details>
<summary>Solution</summary>

```bash
# Simulate accidental data deletion
kubectl exec counter-db-0 -- psql -U app -d counter -c \
  "DROP TABLE visits;"
kubectl exec counter-db-0 -- psql -U app -d counter -c \
  "SELECT count(*) FROM visits;" 2>&1 || echo "Table is gone!"

# Delete the StatefulSet and PVC to simulate total loss
kubectl delete statefulset counter-db
kubectl delete pvc data-counter-db-0

# Create a restore plan
gcloud beta container backup-restore restore-plans create full-restore \
  --project=$PROJECT_ID \
  --location=$REGION \
  --cluster=projects/$PROJECT_ID/locations/$REGION/clusters/storage-demo \
  --backup-plan=projects/$PROJECT_ID/locations/$REGION/backupPlans/storage-demo-backup \
  --all-namespaces \
  --volume-data-restore-policy=RESTORE_VOLUME_DATA_FROM_BACKUP \
  --namespaced-resource-restore-mode=DELETE_AND_RESTORE \
  --cluster-resource-conflict-policy=USE_BACKUP_VERSION

# Execute the restore
gcloud beta container backup-restore restores create restore-1 \
  --project=$PROJECT_ID \
  --location=$REGION \
  --restore-plan=full-restore \
  --backup=projects/$PROJECT_ID/locations/$REGION/backupPlans/storage-demo-backup/backups/manual-backup-1 \
  --wait-for-completion

# Wait for the StatefulSet to come back
kubectl rollout status statefulset/counter-db --timeout=300s

# Verify data is restored
kubectl exec counter-db-0 -- psql -U app -d counter -c \
  "SELECT count(*) FROM visits;"
# Should show 3 rows again
```
</details>

**Task 6: Clean Up**

<details>
<summary>Solution</summary>

```bash
# Delete backup resources first
gcloud beta container backup-restore restore-plans delete full-restore \
  --project=$PROJECT_ID --location=$REGION --quiet 2>/dev/null
gcloud beta container backup-restore backups delete manual-backup-1 \
  --project=$PROJECT_ID --location=$REGION \
  --backup-plan=storage-demo-backup --quiet 2>/dev/null
gcloud beta container backup-restore backup-plans delete storage-demo-backup \
  --project=$PROJECT_ID --location=$REGION --quiet

# Delete the cluster
gcloud container clusters delete storage-demo \
  --region=$REGION --quiet

# Check for orphaned regional PDs (reclaim policy was Retain)
gcloud compute disks list --filter="name~pvc" \
  --format="table(name, zone, sizeGb, status)"
# Delete any orphaned disks manually if needed

echo "Cleanup complete."
```
</details>

### Success Criteria

- [ ] Regional PD StorageClass created with `replication-type: regional-pd`
- [ ] StatefulSet deployed with data written to PostgreSQL
- [ ] Pod successfully failed over to a different zone with data intact
- [ ] Backup created with Backup for GKE (includes volume data)
- [ ] Data deleted and StatefulSet destroyed to simulate total loss
- [ ] Application restored from backup with all data intact
- [ ] All resources cleaned up

---

## Next Module

Next up: **[Module 6.5: GKE Observability and Fleet Management](../module-6.5-gke-fleet/)** --- Learn how to monitor GKE with Cloud Operations Suite and Managed Prometheus, manage multiple clusters with Fleet, enable cross-cluster communication with Multi-Cluster Services, and implement cost allocation.

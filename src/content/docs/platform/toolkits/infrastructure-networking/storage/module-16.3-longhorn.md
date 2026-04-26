---
title: "Module 16.3: Longhorn - Lightweight Distributed Block Storage for Kubernetes"
slug: platform/toolkits/infrastructure-networking/storage/module-16.3-longhorn
sidebar:
  order: 4
---

## Complexity: [MEDIUM]

## Time to Complete: 55-70 minutes

---

## Prerequisites

Before starting this module, you should have completed:

- [Distributed Systems Foundation](/platform/foundations/distributed-systems/) - Replication, quorum, failure domains, and degraded-mode behavior
- [Reliability Engineering Foundation](/platform/foundations/reliability-engineering/) - Recovery objectives, backup strategy, and operational risk
- Kubernetes fundamentals: Pods, PersistentVolumeClaims, StorageClasses, StatefulSets, taints, tolerations, and node labels
- [Module 16.1: Rook/Ceph](../module-16.1-rook-ceph/) - Recommended for comparing Longhorn with a full storage platform
- [Module 16.2: MinIO](../module-16.2-minio/) - Recommended for understanding S3-compatible backup targets
- A local test cluster tool such as `kind`, plus `helm` and `kubectl`; this module uses `kubectl` first, then `k` as a shorter alias after explaining it

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a Longhorn deployment for small and medium Kubernetes clusters by choosing replica counts, data locality, backup targets, and failure domains that match the workload risk.
- **Debug** degraded Longhorn volumes by tracing the path from PVC to Longhorn volume, engine, replica, node, and backing disk.
- **Evaluate** when Longhorn is a better fit than Rook/Ceph, MinIO, or cloud CSI storage by comparing access modes, operational burden, recovery model, and scale limits.
- **Implement** snapshots, recurring backups, and restore workflows that support realistic recovery objectives instead of relying on local replicas alone.
- **Analyze** Longhorn health signals and Prometheus metrics to distinguish normal rebuild behavior from storage incidents that require operator action.

---

## Why This Module Matters

A logistics company rolled Kubernetes out to regional warehouses because every site needed local inventory, label printing, barcode scanning, and queue processing even when the WAN link was unreliable. Each warehouse had three compact servers, a handful of NVMe disks, and no local storage engineer. The central platform team wanted persistent storage that could survive a single node failure, recover from accidental deletion, and remain simple enough for an on-call engineer to operate during a shipping outage.

Their first design used Rook/Ceph because it was powerful and familiar from larger datacenter clusters. It worked during a controlled pilot, but the operating model did not fit the edge environment. Ceph monitor memory, OSD recovery traffic, raw disk preparation, version upgrades, and specialist troubleshooting all competed with the actual goal: keeping warehouse applications online. When a server failed during a busy shift, the platform engineer was not solving an abstract storage problem; they were explaining why scanners could not write completed picks back to the local database.

| Problem | Operational impact | Why it mattered during an incident |
|---------|--------------------|------------------------------------|
| Heavy control-plane footprint | Storage components consumed memory needed by application workloads | Small edge nodes had little reserve capacity during rebuilds |
| Broad recovery blast radius | Disk or OSD recovery moved large amounts of data | Warehouse networks were also carrying application traffic |
| Specialist knowledge required | On-call engineers needed Ceph-specific commands and mental models | Escalation delayed recovery when the central expert was unavailable |
| Upgrade risk | Storage upgrades required careful sequencing and rollback planning | A failed upgrade at one site could halt local operations |
| Poor fit for simple RWO workloads | The platform supported more storage modes than the apps needed | Extra capability became extra operational surface area |

The team replaced that design with Longhorn for the edge sites. Longhorn did not try to be a complete storage platform; it gave them Kubernetes-native replicated block volumes, snapshots, S3-compatible backups, a usable dashboard, and predictable per-volume recovery. The operational improvement came from narrowing the problem. The warehouses mostly needed ReadWriteOnce block storage for databases and stateful services, not a shared filesystem or object gateway inside every cluster.

| Metric | Rook/Ceph edge deployment | Longhorn edge deployment | Engineering lesson |
|--------|---------------------------|--------------------------|--------------------|
| Time to deploy one site | Multiple manual storage steps | Helm-based install with standard settings | Repeatability matters more than feature breadth at the edge |
| Storage expertise required | Dedicated storage escalation path | Platform engineer with Kubernetes context | The best tool is often the one the on-call team can reason about |
| Failure recovery model | Storage-pool recovery across many objects | Per-volume replica rebuild | Smaller recovery scope is easier to observe and explain |
| Backup workflow | Separate design and tooling required | Built-in S3-compatible backup target | Backup needs to be part of the day-one storage design |
| Fit for workload | More features than required | RWO block storage with snapshots and backups | A narrow tool can be the senior choice when it matches the job |

Longhorn matters because many Kubernetes teams need durable block storage without becoming storage-system specialists. That does not make Longhorn magic or universally better than Ceph. It means Longhorn is worth understanding as an operating model: replicated volumes managed through Kubernetes objects, backed by node-local disks, protected by snapshots and backups, and repaired through volume-level rebuilds. A senior platform engineer does not merely install it; they decide where it fits, how it fails, what to monitor, and when to choose something else.

---

## Core Content

### 1. Start With The Storage Problem, Not The Product

Kubernetes makes stateful workloads look deceptively simple because a PersistentVolumeClaim hides most of the storage machinery. A developer asks for `20Gi`, a StorageClass provisions a volume, and the Pod receives a mounted filesystem. The platform engineer has to answer the questions behind that abstraction: where the bytes live, how many copies exist, which failures are tolerated, how recovery is triggered, and what happens when the whole cluster is lost.

Longhorn solves a specific version of that problem. It provides replicated block storage for Kubernetes by storing each volume as replicas on node-local disks and presenting that volume back to Pods through the CSI driver. The normal access mode is ReadWriteOnce, which means one node mounts the volume for one workload at a time. If the workload is a PostgreSQL StatefulSet, a queue worker with local state, or a single-writer application, that model can be a strong fit.

Longhorn is not a replacement for every storage pattern. If the workload needs many Pods writing to the same shared filesystem, Longhorn is usually the wrong first choice. If the team needs an S3-compatible object API for artifacts, logs, or model files, MinIO or cloud object storage is a more direct fit. If the organization needs block, file, and object storage from one large storage platform with deep tuning options, Rook/Ceph may be justified despite the operational cost.

```text
STORAGE QUESTION FIRST
────────────────────────────────────────────────────────────────────

  What does the workload need?
  │
  ├── One Pod writes a mounted filesystem
  │   └── Candidate: Longhorn, cloud block CSI, Rook/Ceph RBD
  │
  ├── Many Pods write the same filesystem
  │   └── Candidate: CephFS, NFS, managed file service
  │
  ├── Applications need an S3-compatible API
  │   └── Candidate: MinIO, cloud object storage, Ceph RGW
  │
  └── Cluster-independent disaster recovery is required
      └── Add external backups; replicas inside one cluster are not enough
```

**Pause and predict:** A team tells you they have three worker nodes, one PostgreSQL instance, and a requirement to survive one worker-node loss. They also say they do not need ReadWriteMany. Before reading further, predict whether the important design choice is "which filesystem should Kubernetes mount" or "how many Longhorn replicas should exist and where they should be placed." The second answer is the platform decision; the filesystem inside the volume matters, but the reliability behavior comes from replica placement and backup design.

The key distinction is that local replicas and external backups protect against different failures. Replicas help the application continue when a node or disk fails inside the cluster. Backups help recover when data is deleted, corrupted, encrypted by a bad job, or lost with the cluster. Treating replicas as backups is one of the fastest ways to design a system that survives routine failure but loses data during the incident that actually matters.

### 2. Longhorn Architecture: Manager, Engine, Replica, And CSI

Longhorn has a small set of moving parts, but each part has a different responsibility. The Longhorn manager runs on every node as a DaemonSet and reconciles Longhorn custom resources such as volumes, replicas, engines, nodes, settings, backups, and recurring jobs. The CSI components integrate Longhorn with Kubernetes so a PVC can become an attached block device mounted into a Pod. For each attached volume, Longhorn runs an engine process that coordinates reads and writes to that volume's replicas.

The engine is the center of the live I/O path. When the application writes to the mounted filesystem, the write reaches the Longhorn engine for that volume. The engine synchronously sends the write to the configured replicas and only acknowledges success after the required replica writes complete. This is why replica count affects both reliability and write latency: more replicas improve failure tolerance, but every synchronous write has more destinations.

Replicas are stored on node disks as sparse files under Longhorn's data path. The replica is not a Kubernetes object pretending to be data; it is the actual block data for the volume, managed by Longhorn processes and represented through Longhorn CRDs. If a replica becomes unavailable, Longhorn can rebuild a replacement replica on another suitable node by copying data from a healthy replica. The volume can remain attached during that rebuild, but performance and risk posture change while it is degraded.

```text
LONGHORN ARCHITECTURE
────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────┐                                │
│  │ Longhorn Manager DaemonSet   │  Runs on every storage node     │
│  │                              │  Reconciles Longhorn CRDs       │
│  │ - volume lifecycle           │  Schedules engines/replicas     │
│  │ - node and disk state        │  Coordinates backup operations  │
│  │ - settings and recurring jobs│  Exposes API used by UI         │
│  └───────────────┬──────────────┘                                │
│                  │                                               │
│                  ▼                                               │
│  ┌──────────────────────────────┐                                │
│  │ CSI Driver Components        │  Kubernetes storage interface   │
│  │                              │  Provision, attach, mount       │
│  │ - external provisioner       │  Expands PVCs when supported    │
│  │ - attacher and node plugin   │  Connects kubelet to Longhorn   │
│  └───────────────┬──────────────┘                                │
│                  │                                               │
│                  ▼                                               │
│  ┌──────────────────────────────┐                                │
│  │ Longhorn Engine per Volume   │  Live I/O coordinator           │
│  │                              │  Synchronous write replication  │
│  │ - accepts block I/O          │  Reads from healthy replicas    │
│  │ - tracks snapshot chain      │  Reports volume robustness      │
│  └───────┬──────────────┬───────┘                                │
│          │              │                                        │
│          ▼              ▼                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Replica A    │  │ Replica B    │  │ Replica C    │            │
│  │ Node worker1 │  │ Node worker2 │  │ Node worker3 │            │
│  │ host disk    │  │ host disk    │  │ host disk    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

```text
VOLUME I/O PATH
────────────────────────────────────────────────────────────────────

  Application Pod
  ┌────────────────┐
  │ writes to /data│
  └───────┬────────┘
          │ filesystem write through mounted PVC
          ▼
  ┌────────────────┐
  │ Longhorn Engine│
  │ for this volume│
  └───┬────────┬───┘
      │        │
      │        └───────────────┐
      ▼                        ▼
┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│ Replica A   │          │ Replica B   │          │ Replica C   │
│ Node A disk │          │ Node B disk │          │ Node C disk │
└──────┬──────┘          └──────┬──────┘          └──────┬──────┘
       │ acknowledgement         │ acknowledgement         │ acknowledgement
       └────────────────────────┴─────────────────────────┘
                                │
                                ▼
                     Application write returns
```

**Stop and think:** In the diagram, the application sees one mounted filesystem, but Longhorn is writing to several replicas. If one replica is slow because its node disk is saturated, what should you expect to happen to write latency? The likely result is higher latency for writes because synchronous replication waits on replica acknowledgement. That is why storage-node health, disk pressure, and rebuild traffic belong in application incident analysis.

The CSI abstraction is useful, but it can hide too much during troubleshooting. When a Pod is stuck mounting a PVC, the problem might be the Kubernetes scheduler, the PVC binding process, the Longhorn CSI attacher, the volume engine, a replica scheduling failure, or a node-level dependency such as iSCSI support. A good operator walks the chain in order instead of jumping straight to the Longhorn UI.

```text
PVC TROUBLESHOOTING CHAIN
────────────────────────────────────────────────────────────────────

Pod Pending or ContainerCreating
  │
  ├── Is the PVC Bound?
  │   ├── no  → inspect StorageClass, provisioner, events
  │   └── yes → continue
  │
  ├── Is the Longhorn volume created?
  │   ├── no  → inspect CSI provisioner logs and PVC events
  │   └── yes → continue
  │
  ├── Is the volume attached to the expected node?
  │   ├── no  → inspect attachment tickets and node state
  │   └── yes → continue
  │
  ├── Is the volume robust enough to attach?
  │   ├── no  → inspect replicas, disks, scheduling constraints
  │   └── yes → continue
  │
  └── Is kubelet able to mount the device?
      ├── no  → inspect node packages, kernel support, kubelet events
      └── yes → inspect application container behavior
```

For the rest of this module, the examples use `kubectl` in full form first. In a real terminal, many Kubernetes operators define `alias k=kubectl`; after the alias is shown, the shorter `k` form is used in a few verification commands. The alias is only a shell convenience and should not be confused with a different tool.

```bash
alias k=kubectl
```

### 3. Installation And Day-One Configuration

A Longhorn installation is simple compared with many storage systems, but storage installation should never be treated as a copy-paste step. The day-one choices define how future volumes behave: default replica count, default data locality, backup target, over-provisioning limits, node selection, and whether Longhorn becomes the default StorageClass. These defaults are operational policy, not decoration.

The example below uses Helm because it is common, repeatable, and compatible with GitOps workflows. In production, pin the chart version that your team has tested with your Kubernetes version and node operating system. Do not blindly track the newest chart in storage infrastructure; controlled upgrades and rollback plans matter more than having the newest minor release the day it appears.

```bash
helm repo add longhorn https://charts.longhorn.io
helm repo update

LONGHORN_CHART_VERSION="1.7.2"

helm install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --create-namespace \
  --version "${LONGHORN_CHART_VERSION}" \
  --set defaultSettings.defaultReplicaCount=3 \
  --set defaultSettings.defaultDataLocality="best-effort" \
  --set defaultSettings.backupTarget="s3://longhorn-backups@us-east-1/" \
  --set defaultSettings.backupTargetCredentialSecret=longhorn-backup-secret

kubectl -n longhorn-system rollout status daemonset/longhorn-manager --timeout=300s
kubectl -n longhorn-system rollout status deployment/longhorn-driver-deployer --timeout=300s
kubectl -n longhorn-system rollout status deployment/longhorn-ui --timeout=300s

kubectl -n longhorn-system get pods
```

A backup target secret should be created before enabling backup jobs in production. The exact values depend on the S3-compatible target, but the important idea is stable: Longhorn needs credentials and an endpoint outside the volume it is protecting. Using a MinIO bucket inside the same cluster can be useful for a lab, but it is not sufficient for disaster recovery if the cluster is lost.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: longhorn-backup-secret
  namespace: longhorn-system
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "replace-with-access-key"
  AWS_SECRET_ACCESS_KEY: "replace-with-secret-key"
  AWS_ENDPOINTS: "https://s3.example.internal"
```

The Longhorn UI is useful for learning and incident response, but production access should be authenticated and controlled through the same security model as other cluster operations. A local port-forward is acceptable for a lab because it exposes the service only to the operator's workstation. For shared environments, place the UI behind an ingress with authentication or restrict it to a private administration network.

```bash
kubectl -n longhorn-system port-forward svc/longhorn-frontend 8080:80
```

```text
DAY-ONE SETTINGS DECISION MAP
────────────────────────────────────────────────────────────────────

  Setting
  │
  ├── defaultReplicaCount
  │   ├── 1  → lab only; one disk or node loss can lose availability
  │   ├── 2  → tolerates one replica loss with lower capacity cost
  │   └── 3  → common production default for small clusters
  │
  ├── defaultDataLocality
  │   ├── disabled     → simpler placement; possible remote reads
  │   └── best-effort  → tries to keep a replica near the consuming Pod
  │
  ├── backupTarget
  │   ├── unset        → no cluster-external recovery path
  │   └── configured   → enables recurring backup policy
  │
  └── node and disk tags
      ├── unset        → Longhorn may use any eligible node disk
      └── configured   → storage placement follows hardware tiers
```

**Pause and predict:** Suppose a three-node cluster uses a default replica count of three. One node is cordoned for maintenance and another node already has a full Longhorn disk. What might happen when a new PVC is created? A volume may fail to schedule all requested replicas because Longhorn needs enough eligible disks across nodes. The PVC can look like a Kubernetes provisioning problem even though the real issue is Longhorn replica placement capacity.

A production installation should also define how Longhorn nodes are selected. Many teams run Longhorn only on worker nodes with appropriate disks rather than every node in the cluster. That can be done through node labels, taints, tolerations, and Longhorn disk settings. The principle is more important than the mechanism: storage should land on nodes that have predictable disk capacity, acceptable failure domains, and operational ownership.

### 4. Provisioning Volumes For Stateful Workloads

A StorageClass turns platform policy into an application-facing interface. Developers should not need to understand every Longhorn setting to request storage, but they should receive a class whose behavior matches the workload tier. A common pattern is to expose a default Longhorn class for normal single-writer workloads and a separate class for high-performance or lower-replica lab workloads.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-fast
provisioner: driver.longhorn.io
allowVolumeExpansion: true
parameters:
  numberOfReplicas: "3"
  staleReplicaTimeout: "2880"
  dataLocality: "best-effort"
  diskSelector: "ssd"
  nodeSelector: "storage"
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

The `numberOfReplicas` parameter is the most visible reliability setting, but it is not the only one that matters. `dataLocality: best-effort` attempts to place a replica on the same node as the consuming workload, which can reduce read latency when the local replica is healthy. Disk and node selectors let the platform team constrain placement to appropriate hardware. `reclaimPolicy: Delete` means the volume is deleted when the PVC is deleted, which may be convenient for ephemeral environments and risky for production databases unless backups and retention are well defined.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn-fast
  resources:
    requests:
      storage: 20Gi
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
              value: "replace-me-in-real-clusters"
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: longhorn-fast
        resources:
          requests:
            storage: 20Gi
```

This StatefulSet uses `volumeClaimTemplates`, which is usually better than a separately named PVC when a StatefulSet owns the volume lifecycle. The template causes Kubernetes to create a PVC with a stable name for each replica, such as `data-postgres-0`. For a single PostgreSQL instance, that matches the single-writer model. If you scale this StatefulSet to more application replicas without database clustering, the storage layer will not turn it into a safe multi-primary database.

```bash
kubectl apply -f postgres-longhorn.yaml
kubectl rollout status statefulset/postgres --timeout=180s
kubectl get pvc
kubectl -n longhorn-system get volumes.longhorn.io
```

A useful mental model is that Kubernetes owns the claim and workload relationship, while Longhorn owns the storage implementation behind the claim. When an application incident happens, inspect both sides. Kubernetes can tell you whether the PVC is bound and mounted. Longhorn can tell you whether the volume is attached, healthy, rebuilding, detached, or degraded.

| Layer | Object or signal | What it answers | Example command |
|-------|------------------|-----------------|-----------------|
| Application | Pod logs and readiness | Is the workload using the mounted filesystem correctly? | `kubectl logs statefulset/postgres` |
| Kubernetes storage | PVC and events | Did the claim bind and mount through CSI? | `kubectl describe pvc postgres-data` |
| Longhorn volume | Volume CRD robustness | Is the Longhorn volume healthy, degraded, or detached? | `kubectl -n longhorn-system get volumes.longhorn.io` |
| Longhorn replica | Replica CRDs and node placement | Are enough replicas running on distinct healthy nodes? | `kubectl -n longhorn-system get replicas.longhorn.io -o wide` |
| Node and disk | Node readiness and disk usage | Is a node or backing disk preventing scheduling or rebuild? | `kubectl get nodes -o wide` |

### 5. Snapshots, Backups, And Restore Workflows

Longhorn snapshots and backups are related but not interchangeable. A snapshot is a local point-in-time view of a volume, stored with the volume's replica data. It is fast and useful before migrations, upgrades, or risky application changes. A backup copies snapshot data to an external target, which is what makes it useful when the cluster or all replicas are lost.

This distinction should guide recovery planning. If the team needs a quick rollback after a failed schema migration and the cluster is otherwise healthy, a snapshot may be enough. If the team needs to recover after a mistaken namespace deletion, a ransomware event, a storage-node loss beyond replica tolerance, or a region-level failure, backups matter. A serious platform design uses both and tests both.

```text
SNAPSHOT AND BACKUP FLOW
────────────────────────────────────────────────────────────────────

  Running Volume
  ┌────────────────────┐
  │ live block changes │
  └─────────┬──────────┘
            │ create local snapshot
            ▼
  ┌────────────────────┐
  │ local snapshot     │  Fast rollback inside the same cluster
  │ copy-on-write data │  Depends on Longhorn replicas still existing
  └─────────┬──────────┘
            │ backup operation copies changed blocks
            ▼
  ┌────────────────────┐
  │ S3 backup target   │  Recovery source outside the cluster
  │ incremental blocks │  Used for restore and DR workflows
  └────────────────────┘
```

The Kubernetes VolumeSnapshot API provides a standard way to request snapshots through CSI. This example assumes the Longhorn snapshot class exists in the cluster. In a production workflow, snapshot creation should be coordinated with application consistency. For databases, that may mean using database-native backup mode, flushing writes, or taking logical backups alongside volume snapshots.

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snap-before-migration
spec:
  volumeSnapshotClassName: longhorn-snapshot-vsc
  source:
    persistentVolumeClaimName: data-postgres-0
```

Recurring backup jobs turn backup from a human memory test into cluster policy. The job below creates backups on a schedule and retains a bounded number of restore points. The labels connect a Longhorn volume or PVC to the recurring job group. The exact retention should come from recovery requirements, not from a random default.

```yaml
apiVersion: longhorn.io/v1beta2
kind: RecurringJob
metadata:
  name: daily-backup
  namespace: longhorn-system
spec:
  cron: "0 2 * * *"
  task: backup
  groups:
    - default
  retain: 7
  concurrency: 2
  labels:
    backup-policy: daily
```

```bash
kubectl label pvc data-postgres-0 recurring-job.longhorn.io/source=enabled
kubectl label pvc data-postgres-0 recurring-job-group.longhorn.io/default=enabled
kubectl -n longhorn-system get recurringjobs.longhorn.io
```

A restore workflow should be practiced before it is needed. Longhorn can restore a volume from backup into a cluster, and the restored PVC can then be attached to a workload. The important operational question is not only whether restore succeeds, but how long it takes and how much data the application can afford to lose. Those are recovery time objective and recovery point objective decisions, and storage configuration should be evaluated against them.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-restored
  annotations:
    longhorn.io/volume-from-backup: "s3://longhorn-backups@us-east-1/?backup=backup-example&volume=data-postgres-0"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn-fast
  resources:
    requests:
      storage: 20Gi
```

**Stop and think:** A team says, "We have three Longhorn replicas, so we do not need backups." What failure are they forgetting? Replicas usually copy valid writes, invalid writes, deletes, filesystem corruption, and application-level mistakes. If the application overwrites good data with bad data, Longhorn can faithfully replicate the bad state across all replicas. External backups give the team a way to return to an earlier point in time.

### 6. Rebuilds, Monitoring, And Incident Triage

A Longhorn volume can be healthy, degraded, rebuilding, detached, or faulted depending on the state of its engine and replicas. These states are not merely labels in a dashboard; they describe how many failures the workload can still tolerate. A degraded volume may still serve application traffic, but it has less redundancy. A rebuilding volume may be moving substantial data across the network and disk subsystem. A faulted volume means the application may already be down or unable to mount data.

```bash
kubectl -n longhorn-system get volumes.longhorn.io
kubectl -n longhorn-system get nodes.longhorn.io
kubectl -n longhorn-system get replicas.longhorn.io -o wide
```

When a volume is degraded, start by identifying which replica is missing or unhealthy and which node or disk hosted it. Then check whether Longhorn can schedule a replacement. Common blockers include insufficient disk space, node scheduling disabled, disk tags that do not match the StorageClass, anti-affinity settings that prevent placement, or a node that is NotReady. This is where a senior operator avoids vague "storage is broken" conclusions and turns the incident into a concrete scheduling or health problem.

```text
DEGRADED VOLUME TRIAGE
────────────────────────────────────────────────────────────────────

  Volume robustness is degraded
  │
  ├── Identify affected volume
  │   └── kubectl -n longhorn-system get volumes.longhorn.io
  │
  ├── Inspect replicas for that volume
  │   └── kubectl -n longhorn-system get replicas.longhorn.io -o wide
  │
  ├── Check node and disk eligibility
  │   ├── node Ready?
  │   ├── Longhorn node schedulable?
  │   ├── enough free disk?
  │   └── tags match StorageClass?
  │
  ├── Watch rebuild progress
  │   └── verify new replica reaches running state
  │
  └── Confirm robustness returns to healthy
      └── remove alert only after redundancy is restored
```

Prometheus metrics make this process alertable. Alert on degraded volumes, faulted volumes, nodes not ready, high storage usage, and failed backup state. Avoid alerts that fire only when applications are already down. The best Longhorn alerts tell the platform team that redundancy has been reduced while there is still time to repair it.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: longhorn
  namespace: longhorn-system
spec:
  selector:
    matchLabels:
      app: longhorn-manager
  endpoints:
    - port: manager
      path: /metrics
      interval: 30s
```

```text
KEY LONGHORN METRICS
────────────────────────────────────────────────────────────────────

Volume health
  ├── longhorn_volume_state
  ├── longhorn_volume_robustness
  ├── longhorn_volume_actual_size_bytes
  └── longhorn_volume_capacity_bytes

Node and disk health
  ├── longhorn_node_status
  ├── longhorn_node_storage_capacity_bytes
  ├── longhorn_node_storage_usage_bytes
  └── longhorn_disk_status

Backup health
  ├── longhorn_backup_state
  ├── longhorn_backup_actual_size_bytes
  └── longhorn_backup_last_synced_at
```

The most useful dashboard combines Kubernetes and Longhorn context. Show the application namespace, PVC, Longhorn volume name, volume robustness, replica count, node placement, disk usage, and backup age in one view. During an incident, the on-call engineer should not need to open five pages to answer whether the application is down because of scheduling, mounting, degraded storage, or application behavior.

| Symptom | First check | Likely Longhorn concern | Next action |
|---------|-------------|-------------------------|-------------|
| Pod stuck in `ContainerCreating` | `kubectl describe pod` events | Volume attach or mount problem | Inspect PVC, VolumeAttachment, Longhorn volume state |
| PVC remains `Pending` | `kubectl describe pvc` | StorageClass or CSI provisioning issue | Check Longhorn CSI provisioner and StorageClass name |
| Volume robustness is degraded | Longhorn replicas | Missing or rebuilding replica | Check node readiness, disk space, and scheduling constraints |
| Backup job failing | Longhorn backup state | Credentials, endpoint, or bucket problem | Validate secret, endpoint reachability, and target permissions |
| Rebuild never starts | Longhorn node and disk state | No eligible disk for replacement replica | Adjust disk capacity, tags, node scheduling, or replica policy |
| Application latency spikes during rebuild | Metrics and node I/O | Rebuild traffic competing with workload | Rate-limit, move workload, or add storage capacity |

### 7. Choosing Longhorn Versus Other Storage Options

A mature platform team does not choose Longhorn because it is easier in isolation. It chooses Longhorn when its simplicity matches the workload and failure model. The comparison should include access mode, scale, backup needs, operating skill, and hardware assumptions. A tool that is excellent for one team can be a liability for another team with different workloads.

```text
WHEN TO USE WHICH STORAGE SOLUTION
────────────────────────────────────────────────────────────────────

USE LONGHORN WHEN:
├── You need simple Kubernetes block storage for ReadWriteOnce volumes
├── Your workloads are databases, queues, and single-writer services
├── Your clusters are small to medium or run at edge locations
├── Your team wants built-in snapshots, S3 backups, and a practical UI
├── Your operators are stronger in Kubernetes than storage internals
└── Your recovery model can be expressed as volume replicas plus backups

USE ROOK/CEPH WHEN:
├── You need block, shared filesystem, and object storage in one platform
├── You need ReadWriteMany through CephFS
├── You operate larger storage clusters with dedicated expertise
├── You need deep placement, pool, and performance tuning
├── You can support more complex recovery and upgrade procedures
└── You are building storage as a platform, not just storage for apps

USE MINIO WHEN:
├── Applications need an S3-compatible object API
├── You are storing logs, artifacts, media, backups, or model files
├── The access pattern is object read/write rather than mounted filesystem I/O
├── You want a backup target for other systems
└── You do not need Kubernetes PVC semantics for the consuming workload

USE CLOUD CSI WHEN:
├── Your workloads run in one cloud and portability is less important
├── You prefer managed durability over operating storage nodes
├── Your team accepts provider-specific behavior and costs
├── You want storage failure handling delegated to the cloud provider
└── You do not need cluster-local storage independence
```

| Decision factor | Longhorn | Rook/Ceph | MinIO | Cloud block CSI |
|----------------|----------|-----------|-------|-----------------|
| Primary interface | Kubernetes block PVC | Block, file, and object | S3-compatible object API | Kubernetes block PVC |
| Normal access mode | ReadWriteOnce | RWO and RWX depending on backend | Object API, not PVC filesystem | ReadWriteOnce |
| Operational complexity | Low to medium | High | Medium | Low for cluster team |
| Best environment | Edge, lab, small and medium clusters | Larger clusters with storage expertise | Object-heavy platforms | Single-cloud deployments |
| Backup model | Built-in S3-compatible backups | Depends on Ceph and external tooling | Replication and object lifecycle | Provider snapshots and backups |
| Failure blast radius | Per-volume replica behavior | Pool and placement-group behavior | Object and erasure set behavior | Provider-managed |
| Team skill needed | Kubernetes operator with storage awareness | Storage specialist plus Kubernetes operator | Object storage operator | Cloud platform operator |
| Main limitation | Not a general RWX or object platform | Operational burden | Not block storage for Pods | Cloud lock-in and provider limits |

**Pause and predict:** A team wants to run a shared build cache mounted read-write by twenty build Pods at the same time. They like Longhorn's UI and ask for a Longhorn PVC. What should you recommend? The correct recommendation is not to force Longhorn into an RWX role. Use a shared filesystem option such as CephFS, NFS, or a managed file service, or redesign the cache around an object store if the build tool supports it.

The senior-level conclusion is that Longhorn is an excellent choice when the platform wants reliable block storage with a lightweight operating model. It is a poor choice when the requirement is really shared filesystem semantics, object storage, massive storage-platform consolidation, or provider-managed durability with minimal cluster-level responsibility. Choosing well means defending both the "yes" and the "no."

---

## Did You Know?

- **Longhorn stores replicas as files on node disks rather than requiring raw disks for every storage device.** This makes lab and edge deployments approachable, but it also means node filesystem health and capacity planning remain part of the storage design.
- **Longhorn backups are incremental at the block level after the initial backup.** That reduces repeated transfer volume for changed data, but backup duration still depends on changed blocks, target performance, network path, and concurrency settings.
- **A healthy Longhorn volume can still contain bad application data.** Replication protects availability after infrastructure failures; it does not validate whether an application wrote the correct bytes.
- **Data locality is a performance hint, not a hard guarantee.** `best-effort` tries to place a replica near the consuming Pod, but Longhorn may still attach the volume when perfect locality is impossible.

---

## Common Mistakes

| Mistake | Why it causes trouble | Better operator behavior |
|---------|----------------------|--------------------------|
| Treating replicas as backups | Accidental deletes and corrupt writes are replicated too | Configure external backups and test restore before production |
| Running production volumes with one replica | A single node or disk failure can take the only copy away | Use at least two replicas, commonly three for important workloads |
| Ignoring degraded volumes because the app still works | The next failure may become an outage or data-loss event | Alert on degraded robustness and repair redundancy promptly |
| Using Longhorn for shared multi-writer filesystems | Longhorn's normal model is RWO block storage | Choose CephFS, NFS, or managed file storage for RWX workloads |
| Installing without checking node disk capacity | Replica scheduling and rebuilds fail when eligible disks are full | Plan usable capacity after replica multiplier and reserve headroom |
| Leaving backup target setup until after launch | The first incident may happen before backup policy exists | Configure credentials, target, recurring jobs, and restore tests during rollout |
| Assuming the UI replaces Kubernetes troubleshooting | PVC binding, CSI attachment, and kubelet mount issues span multiple layers | Trace Pod, PVC, StorageClass, Longhorn volume, replica, node, and disk state |
| Letting rebuild traffic compete unmanaged with production I/O | Recovery can increase latency for stateful workloads | Monitor rebuilds, schedule maintenance carefully, and add capacity before saturation |

---

## Quiz

### Question 1

Your team deploys a PostgreSQL StatefulSet on Longhorn with three replicas per volume. The PostgreSQL Pod is running, but Longhorn reports the volume as degraded after one worker node fails. The application is still serving traffic, and a developer asks whether the incident can be ignored because the database is online. What do you check, and what decision do you make?

<details>
<summary>Show Answer</summary>

Check the Longhorn volume robustness, the replica list for that volume, the failed node state, and whether a replacement replica is rebuilding on an eligible disk. The application being online only proves that the remaining replica path can serve I/O; it does not prove the system still has the intended failure tolerance. Keep the incident open until Longhorn has rebuilt the missing replica or until you intentionally accept the reduced redundancy for a bounded maintenance window.
</details>

### Question 2

A warehouse cluster has three worker nodes and uses Longhorn with `numberOfReplicas: "3"`. New PVCs start failing after one node is cordoned and another node's Longhorn disk reaches its reserved capacity threshold. Kubernetes events mention provisioning problems, but the StorageClass name is correct. How do you reason through the failure?

<details>
<summary>Show Answer</summary>

Start with the PVC events, then inspect the Longhorn volume and replica scheduling state. With a three-replica policy, Longhorn needs enough eligible disks across nodes to place all requested replicas. A cordoned or unschedulable storage node plus a full disk can prevent replica placement even though the Kubernetes StorageClass is valid. The fix is to restore node eligibility, free or add disk capacity, adjust disk tags and scheduling settings, or temporarily use a lower-replica StorageClass only if the risk is understood.
</details>

### Question 3

A team proposes Longhorn for a shared build cache because they want a single PVC mounted read-write by many build Pods at the same time. The cluster already runs Longhorn successfully for databases. What should you recommend, and why?

<details>
<summary>Show Answer</summary>

Recommend a storage option designed for ReadWriteMany semantics, such as CephFS, NFS, or a managed file service, unless the build system can use object storage instead. Longhorn is a good fit for ReadWriteOnce block volumes, where one node mounts the volume for a single-writer workload. A tool working well for databases does not mean it is appropriate for shared multi-writer filesystem access.
</details>

### Question 4

Your team takes Longhorn snapshots before every database migration but has not configured an S3 backup target. A migration script accidentally deletes important rows, and the mistake is discovered after the application has continued writing for several hours. What can snapshots help with, and what risk remains?

<details>
<summary>Show Answer</summary>

A local snapshot may help roll the volume back inside the same cluster if the snapshot still exists and the application can tolerate reverting the whole volume to that point. The remaining risk is that snapshots are stored with the cluster's Longhorn data and do not protect against cluster loss, broad storage failure, or snapshot deletion. The team should add external backups and test restore workflows so recovery does not depend only on local snapshot chains.
</details>

### Question 5

A Longhorn-backed application has high write latency during a replica rebuild. The application team says CPU usage is normal and asks why storage could be involved when the Pod is healthy. Which signals do you inspect, and what explanation do you give?

<details>
<summary>Show Answer</summary>

Inspect Longhorn volume robustness, rebuild progress, replica placement, node disk I/O, network throughput, and application latency metrics. During a rebuild, Longhorn copies data to a replacement replica while the live engine continues handling synchronous writes. That recovery traffic can compete with production I/O, and synchronous replication means slow replica paths can increase write latency even when the application container itself is healthy.
</details>

### Question 6

A platform team wants to use a MinIO bucket inside the same Kubernetes cluster as the Longhorn backup target. They say it is still S3-compatible, so it should satisfy disaster recovery. How do you evaluate that design?

<details>
<summary>Show Answer</summary>

It may be useful for a lab or for practicing the backup workflow, but it is weak disaster recovery if the MinIO service and Longhorn volumes fail with the same cluster. A backup target should sit outside the failure domain it protects. For production, use an external S3-compatible service, a separate cluster, or a managed object store with access controls and retention policies that survive loss of the primary cluster.
</details>

### Question 7

A Pod using a Longhorn PVC is stuck in `ContainerCreating`. The developer only sends you the Pod name and says "Longhorn is broken." What step-by-step investigation do you perform before changing storage settings?

<details>
<summary>Show Answer</summary>

First describe the Pod and inspect events to see whether the failure is scheduling, attachment, or mount related. Then check whether the PVC is Bound, whether the StorageClass exists and uses the Longhorn provisioner, whether the Longhorn volume exists, whether it is attached to the expected node, and whether replicas are healthy enough for attachment. If those look correct, inspect CSI component logs and kubelet mount errors on the node, including node-level dependencies required by the Longhorn data path.
</details>

### Question 8

Your organization runs both cloud-hosted production clusters and small disconnected edge clusters. A manager asks for one storage standard everywhere. How do you justify using cloud block CSI in one environment and Longhorn in another without creating unnecessary platform inconsistency?

<details>
<summary>Show Answer</summary>

Explain that the standard should be based on workload contract and operating model, not identical tooling everywhere. In cloud clusters, managed block CSI may reduce operational burden because the provider handles the storage backend. In disconnected edge clusters, Longhorn can provide cluster-local replicated block storage when managed cloud disks are unavailable. The consistent platform contract can be "RWO block PVC with defined backup and restore objectives," while the implementation differs by environment.
</details>

---

## Hands-On Exercise

### Task: Deploy Longhorn, Provision A Volume, Test Recovery Signals, And Validate Data Integrity

**Objective:** Deploy Longhorn in a local multi-node `kind` cluster, create a Longhorn-backed PVC, write data, force a workload restart, inspect Longhorn volume state, and verify that data survives the attach-detach cycle. This lab is not a substitute for a production failover test, but it teaches the basic operator loop: provision, observe, disrupt, verify, and clean up.

**Success Criteria:**

- [ ] A three-worker `kind` cluster exists for the lab.
- [ ] Longhorn is installed in `longhorn-system`, and the manager, UI, and driver components are running.
- [ ] A PVC using the Longhorn StorageClass is Bound.
- [ ] A writer Pod stores a file and checksum on the mounted Longhorn volume.
- [ ] The Longhorn volume and replicas are visible through Kubernetes resources.
- [ ] The writer Pod can be deleted and recreated without losing the stored checksum.
- [ ] The final verification shows matching original and restored checksums.
- [ ] The lab cluster is cleaned up after verification.

### Step 1: Create A Multi-Node kind Cluster

```bash
cat > kind-longhorn-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
  - role: worker
EOF

kind create cluster --name longhorn-lab --config kind-longhorn-config.yaml
kubectl get nodes -o wide
```

### Step 2: Prepare Node Dependencies For The Lab

Longhorn requires node-level storage support. In many real clusters, the operating system image is prepared before Kubernetes joins the node. In this local `kind` lab, install `open-iscsi` inside the worker containers so the Longhorn attach path can function.

```bash
for node in longhorn-lab-worker longhorn-lab-worker2 longhorn-lab-worker3; do
  docker exec "${node}" bash -c "apt-get update && apt-get install -y open-iscsi && systemctl enable iscsid && systemctl start iscsid"
done
```

### Step 3: Install Longhorn With A Lab Replica Policy

This lab uses two replicas to keep scheduling simple on a small `kind` cluster. Production settings should be based on your failure-domain design and capacity plan. The point of the exercise is to observe how Kubernetes PVCs connect to Longhorn volume resources, not to claim that two replicas is always the right production setting.

```bash
helm repo add longhorn https://charts.longhorn.io
helm repo update

LONGHORN_CHART_VERSION="1.7.2"

helm install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --create-namespace \
  --version "${LONGHORN_CHART_VERSION}" \
  --set defaultSettings.defaultReplicaCount=2 \
  --set defaultSettings.defaultDataLocality="best-effort"

kubectl -n longhorn-system rollout status daemonset/longhorn-manager --timeout=300s
kubectl -n longhorn-system rollout status deployment/longhorn-ui --timeout=300s
kubectl -n longhorn-system rollout status deployment/longhorn-driver-deployer --timeout=300s
kubectl -n longhorn-system get pods
```

### Step 4: Create A PVC And Writer Pod

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-test
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 2Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: writer
spec:
  restartPolicy: Never
  containers:
    - name: writer
      image: busybox:1.36
      command:
        - sh
        - -c
      args:
        - |
          set -eu
          echo "Writing test data to Longhorn volume"
          echo "Longhorn storage test $(date)" > /data/test.txt
          dd if=/dev/urandom of=/data/random.bin bs=1M count=32
          md5sum /data/random.bin > /data/checksum.txt
          cat /data/checksum.txt
          sleep 3600
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: longhorn-test
```

```bash
cat > longhorn-test-pvc.yaml << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-test
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 2Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: writer
spec:
  restartPolicy: Never
  containers:
    - name: writer
      image: busybox:1.36
      command:
        - sh
        - -c
      args:
        - |
          set -eu
          echo "Writing test data to Longhorn volume"
          echo "Longhorn storage test $(date)" > /data/test.txt
          dd if=/dev/urandom of=/data/random.bin bs=1M count=32
          md5sum /data/random.bin > /data/checksum.txt
          cat /data/checksum.txt
          sleep 3600
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: longhorn-test
EOF

kubectl apply -f longhorn-test-pvc.yaml
kubectl wait --for=condition=Ready pod/writer --timeout=180s
kubectl get pvc longhorn-test
```

### Step 5: Capture Baseline Data And Inspect Longhorn Objects

```bash
kubectl logs writer
ORIGINAL_CHECKSUM="$(kubectl exec writer -- cat /data/checksum.txt)"
echo "Original checksum: ${ORIGINAL_CHECKSUM}"

WRITER_NODE="$(kubectl get pod writer -o jsonpath='{.spec.nodeName}')"
echo "Writer pod is running on: ${WRITER_NODE}"

kubectl -n longhorn-system get volumes.longhorn.io
kubectl -n longhorn-system get replicas.longhorn.io -o wide
kubectl -n longhorn-system get nodes.longhorn.io
```

At this point, connect the abstract architecture back to the running cluster. The PVC is the application-facing request. The Longhorn volume is the storage object created to satisfy that request. The replicas show where the volume data lives. If the output is confusing, do not move on until you can point to the PVC, the consuming Pod, the Longhorn volume, and at least one replica.

### Step 6: Recreate The Writer Pod And Verify Data Survival

Deleting the Pod tests a normal detach and reattach cycle, not a full node-loss event. That distinction matters because a local lab should not overclaim what it proves. The useful lesson is that the data belongs to the PVC-backed Longhorn volume, not to the original Pod container.

```bash
kubectl delete pod writer
kubectl apply -f longhorn-test-pvc.yaml
kubectl wait --for=condition=Ready pod/writer --timeout=180s

kubectl exec writer -- cat /data/test.txt
RESTORED_CHECKSUM="$(kubectl exec writer -- cat /data/checksum.txt)"
echo "Restored checksum: ${RESTORED_CHECKSUM}"

if [ "${ORIGINAL_CHECKSUM}" = "${RESTORED_CHECKSUM}" ]; then
  echo "CHECKSUM MATCH - storage persistence test passed"
else
  echo "CHECKSUM MISMATCH - investigate before continuing"
  exit 1
fi
```

### Step 7: Optional UI Inspection

```bash
kubectl -n longhorn-system port-forward svc/longhorn-frontend 8080:80 &
LH_PF_PID=$!

echo "Open http://127.0.0.1:8080 and inspect Volumes, Nodes, and Replicas."
echo "When finished, stop the port-forward with: kill ${LH_PF_PID}"
```

Use the UI to confirm the same objects you saw through `kubectl`. The dashboard is not a separate truth source; it is another view into Longhorn state. A good exercise is to find the volume backing `longhorn-test`, identify its replica count, and compare the UI's robustness status with the `volumes.longhorn.io` output.

### Step 8: Clean Up

```bash
kill "${LH_PF_PID:-0}" 2>/dev/null || true
kind delete cluster --name longhorn-lab
rm -f kind-longhorn-config.yaml longhorn-test-pvc.yaml
```

### Verification Checklist

- [ ] `kubectl get pvc longhorn-test` showed the PVC as `Bound` before cleanup.
- [ ] `kubectl -n longhorn-system get volumes.longhorn.io` showed a Longhorn volume for the PVC.
- [ ] `kubectl -n longhorn-system get replicas.longhorn.io -o wide` showed replica placement on worker nodes.
- [ ] The original and restored checksum strings matched exactly.
- [ ] You can explain why deleting the Pod did not delete the data.
- [ ] You can explain why this lab does not replace a production backup-restore test.

---

## Next Module

Continue to [Module 16.4: Storage Performance And Capacity Planning](../module-16.4-storage-performance-capacity/) to design storage classes, capacity limits, rebuild budgets, and performance guardrails for production stateful workloads.

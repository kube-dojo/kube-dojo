# Module 16.3: Longhorn - Lightweight Distributed Block Storage for Kubernetes

## Complexity: [MEDIUM]
## Time to Complete: 45-55 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Distributed Systems Foundation](../../foundations/distributed-systems/README.md) - Replication, fault tolerance
- [Reliability Engineering Foundation](../../foundations/reliability-engineering/README.md) - Backup, disaster recovery
- Kubernetes fundamentals (PVCs, StorageClasses, StatefulSets)
- [Module 16.1: Rook/Ceph](module-16.1-rook-ceph.md) (recommended for comparison)
- [Module 16.2: MinIO](module-16.2-minio.md) (recommended for backup target understanding)

---

## Why This Module Matters

**The $680K Edge Computing Rescue**

A logistics company was rolling out Kubernetes to 45 edge locations—small clusters in regional warehouses running inventory management, barcode scanning, and local analytics. Each site had 3 commodity servers with local NVMe drives. No cloud connectivity guarantees. No storage team.

Their first attempt used Rook/Ceph. It worked in the lab. In production, the story was different:

| Problem | Impact |
|---------|--------|
| Ceph MON memory usage | 2GB+ per monitor on 16GB nodes |
| OSD recovery storms | Saturated warehouse network during rebuilds |
| Operational complexity | Required Ceph expertise at 45 sites |
| Upgrade failures | 3 sites bricked during Ceph version upgrade |
| Mean time to resolution | 4.2 hours (waiting for remote storage expert) |

The total cost of storage incidents across 45 sites in the first quarter: $680,000 in lost warehouse productivity, overtime for the platform team, and two missed SLAs with their largest retail customer.

Their principal architect proposed Longhorn. The migration took six weeks:

| Metric | Rook/Ceph (Edge) | Longhorn (Edge) |
|--------|-------------------|-----------------|
| Memory per node | 2.5GB for storage | 512MB for storage |
| Upgrade process | Manual, risky | One-click via UI or Helm |
| Time to deploy per site | 2 hours | 15 minutes |
| Recovery from node failure | 45 min (re-replication storm) | 8 min (incremental rebuild) |
| Storage incidents (Q2) | 23 across 45 sites | 2 across 45 sites |
| Team needed | 2 storage engineers | 1 platform engineer (part-time) |

Nine months later, they expanded to 120 edge locations. The same single platform engineer managed all of them using Longhorn's built-in UI and GitOps-driven configuration.

**Longhorn is purpose-built for Kubernetes: lightweight, simple to operate, and designed for teams that want reliable block storage without hiring a storage specialist.**

---

## Did You Know?

- **Longhorn is a CNCF Incubating project created by Rancher Labs (now SUSE)** — Originally built to complement the lightweight K3s distribution, Longhorn was designed from the ground up for Kubernetes. It entered the CNCF Sandbox in 2019 and graduated to Incubating in 2021, with over 5,800 GitHub stars and adoption across thousands of clusters.

- **Longhorn replicates at the block level, not the filesystem level** — Each volume has an engine (iSCSI target) and configurable replicas spread across nodes. Replication happens synchronously at the block I/O layer, meaning any filesystem (ext4, xfs) or application (database, cache) works without modification. This is fundamentally simpler than distributed filesystems.

- **Longhorn can back up every volume to S3 (or MinIO) incrementally** — Unlike snapshot-only systems, Longhorn supports full and incremental backups to any S3-compatible target. A 100GB volume with 5GB of daily changes only transfers 5GB per backup—not the full 100GB. Combined with recurring backup jobs, this gives you point-in-time recovery without dedicated backup tooling.

- **Longhorn's "rebuilding replica" process is non-disruptive** — When a node fails and a replica is lost, Longhorn rebuilds the replica on a healthy node from the remaining copies. During rebuilding, the volume remains fully accessible with no I/O pauses. Ceph and some other systems can cause performance degradation during large-scale rebuilds due to recovery I/O competing with production traffic.

---

## Longhorn Architecture

```
LONGHORN ARCHITECTURE
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LONGHORN MANAGER (DaemonSet - runs on every node)              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Kubernetes controller for Longhorn CRDs                 │  │
│  │  • Volume lifecycle management (create, attach, delete)    │  │
│  │  • Scheduling: decides which nodes host replicas           │  │
│  │  • Orchestrates snapshots, backups, restores               │  │
│  │  • Exposes REST API + Web UI                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  LONGHORN ENGINE (one per volume, runs as a process)            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • iSCSI target that the kubelet mounts into pods          │  │
│  │  • Synchronous write replication to all replicas           │  │
│  │  • Read from any replica (load balanced)                   │  │
│  │  • Snapshot: copy-on-write, instant, space-efficient       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│              ┌─────────────┼─────────────┐                      │
│              ▼             ▼             ▼                       │
│  REPLICAS (spread across nodes for fault tolerance)             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │  Replica 1    │ │  Replica 2    │ │  Replica 3    │         │
│  │  Node A       │ │  Node B       │ │  Node C       │         │
│  │  /var/lib/    │ │  /var/lib/    │ │  /var/lib/    │         │
│  │  longhorn/    │ │  longhorn/    │ │  longhorn/    │         │
│  │               │ │               │ │               │         │
│  │  [sparse      │ │  [sparse      │ │  [sparse      │         │
│  │   file on     │ │   file on     │ │   file on     │         │
│  │   host disk]  │ │   host disk]  │   host disk]  │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

VOLUME I/O PATH:
─────────────────────────────────────────────────────────────────

  Pod                Engine              Replicas
  ┌─────┐           ┌──────┐           ┌──────────┐
  │ App │──write──▶│Engine│──sync──▶│ Replica 1│ (Node A)
  │     │           │      │──sync──▶│ Replica 2│ (Node B)
  │     │           │      │──sync──▶│ Replica 3│ (Node C)
  │     │◀──ack────│      │◀──ack───│  (all)   │
  └─────┘           └──────┘           └──────────┘

  Write acknowledged only after ALL replicas confirm.
  Read served from any single replica (fast).

SNAPSHOT AND BACKUP FLOW:
─────────────────────────────────────────────────────────────────

  Volume          Snapshots (local)         Backup (remote S3)
  ┌──────┐       ┌──────┐ ┌──────┐       ┌─────────────────┐
  │ Live │──snap─│ Snap │─│ Snap │──────▶│  S3 / MinIO     │
  │ Data │       │  v1  │ │  v2  │       │                 │
  └──────┘       └──────┘ └──────┘       │  Incremental    │
                                          │  block-level    │
                 Copy-on-write            │  deduplication  │
                 Instant, zero I/O        └─────────────────┘
```

### How Longhorn Differs from Ceph

```
LONGHORN vs CEPH - ARCHITECTURAL DIFFERENCES
─────────────────────────────────────────────────────────────────

                          Longhorn              Ceph
─────────────────────────────────────────────────────────────────
Replication unit          Per-volume engine     Per-object (CRUSH)
Replication method        Synchronous iSCSI     RADOS replication
Metadata                  Kubernetes CRDs       MON (Paxos cluster)
Storage backend           Sparse files on host  BlueStore (raw disk)
Filesystem support        Block only (RWO)      Block + FS + Object
Data placement            Node scheduling       CRUSH algorithm
Recovery scope            Per-volume rebuild    Per-OSD recovery
Memory footprint          ~512MB per node       ~2-4GB per node
Minimum nodes             1 (degraded)          3 (MON quorum)
Operational complexity    Low                   High
Best for                  Simple block storage  Full storage platform
```

---

## Installation via Helm

```bash
# Add the Longhorn Helm repository
helm repo add longhorn https://charts.longhorn.io
helm repo update

# Install Longhorn
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --create-namespace \
  --version 1.7.2 \
  --set defaultSettings.defaultReplicaCount=3 \
  --set defaultSettings.backupTarget="s3://longhorn-backups@us-east-1/" \
  --set defaultSettings.backupTargetCredentialSecret=longhorn-backup-secret

# Wait for all components
kubectl -n longhorn-system rollout status daemonset/longhorn-manager --timeout=300s
kubectl -n longhorn-system rollout status deployment/longhorn-driver-deployer --timeout=300s
kubectl -n longhorn-system rollout status deployment/longhorn-ui --timeout=300s

# Verify
kubectl -n longhorn-system get pods
```

### Configure Backup Target (Optional but Recommended)

```yaml
# longhorn-backup-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: longhorn-backup-secret
  namespace: longhorn-system
stringData:
  AWS_ACCESS_KEY_ID: "admin"
  AWS_SECRET_ACCESS_KEY: "minio-secret-key-change-me"
  AWS_ENDPOINTS: "http://minio.minio.svc:9000"
```

### Access the Longhorn UI

```bash
# Port-forward to the Longhorn dashboard
kubectl -n longhorn-system port-forward svc/longhorn-frontend 8080:80

# Open http://localhost:8080
# Shows: volumes, nodes, backups, snapshots, recurring jobs
```

---

## Using Longhorn Storage

### StorageClass (Created Automatically)

Longhorn installs a default StorageClass. You can customize it:

```yaml
# longhorn-storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-fast
provisioner: driver.longhorn.io
allowVolumeExpansion: true
parameters:
  numberOfReplicas: "3"
  staleReplicaTimeout: "2880"    # Minutes before stale replica cleanup
  dataLocality: "best-effort"    # Try to keep a replica on the consuming node
  diskSelector: "ssd"            # Only use disks tagged as SSD
  nodeSelector: "storage"        # Only use nodes labeled for storage
reclaimPolicy: Delete
```

### Provisioning a PVC

```yaml
# postgres-longhorn.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
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

### Snapshots

```yaml
# volume-snapshot.yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snap-before-migration
spec:
  volumeSnapshotClassName: longhorn-snapshot-vsc
  source:
    persistentVolumeClaimName: postgres-data
```

```bash
# Or via the Longhorn CLI / UI:
# Snapshots are instant (copy-on-write) and consume no extra space
# until the original blocks are modified.
```

### Recurring Backup Jobs

```yaml
# recurring-backup.yaml
apiVersion: longhorn.io/v1beta2
kind: RecurringJob
metadata:
  name: daily-backup
  namespace: longhorn-system
spec:
  cron: "0 2 * * *"             # 2 AM daily
  task: backup                   # "snapshot" or "backup"
  retain: 7                      # Keep last 7 backups
  concurrency: 2                 # Max 2 volumes backing up at once
  labels:
    backup-policy: daily
---
# Apply to volumes via label
# kubectl label pvc postgres-data recurring-job.longhorn.io/source=enabled
# kubectl label pvc postgres-data recurring-job-group.longhorn.io/default=enabled
```

### Disaster Recovery Volumes

```yaml
# dr-volume.yaml
# In the DR cluster, create a volume from the backup in S3
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-dr
  annotations:
    # Restore from a specific backup
    longhorn.io/volume-from-backup: "s3://longhorn-backups@us-east-1/?backup=backup-abc123&volume=postgres-data"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 20Gi
```

---

## Storage Solution Comparison

This is the key decision framework for choosing between Longhorn, Rook/Ceph, MinIO, and cloud storage:

```
WHEN TO USE WHICH STORAGE SOLUTION
─────────────────────────────────────────────────────────────────

USE LONGHORN WHEN:
├── You need simple, reliable block storage (RWO)
├── Your team doesn't have storage specialists
├── You're running edge or small-medium clusters (3-20 nodes)
├── You want built-in backup to S3 without extra tooling
├── You need DR across clusters with minimal setup
└── You're using K3s or lightweight distributions

USE ROOK/CEPH WHEN:
├── You need block AND shared filesystem AND object storage
├── You have 10+ nodes and dedicated storage hardware
├── You need CephFS for ReadWriteMany workloads
├── Your team has (or can hire) storage expertise
├── You're running at 100TB+ scale
└── You're building a full storage platform

USE MINIO WHEN:
├── You need S3-compatible object storage (not block)
├── You're building ML pipelines that need artifact storage
├── You need a self-hosted backend for Loki, Tempo, or Thanos
├── You want maximum object I/O throughput
├── You need to eliminate cloud S3 egress costs
└── You're storing unstructured data (logs, backups, media)

USE CLOUD CSI (EBS, GCE PD) WHEN:
├── You're on a single cloud provider
├── You want zero operational burden
├── Your workloads don't need multi-cloud portability
├── You don't mind vendor lock-in for simplicity
└── Cost is less important than operational simplicity

DETAILED COMPARISON:
─────────────────────────────────────────────────────────────────
                    Longhorn     Rook/Ceph    MinIO       Cloud CSI
─────────────────────────────────────────────────────────────────
Primary use         Block (RWO)  All three    Object      Block
Setup time          15 min       2+ hours     30 min      0 (managed)
Memory per node     ~512MB       ~2-4GB       ~1GB/srv    0
Min nodes           1            3            4           1
CNCF status         Incubating   Graduated    None        N/A
Backup built-in     ✓✓           ✓            ✗           Snapshots
DR built-in         ✓✓           ✓            Replication Varies
ReadWriteMany       ✗            ✓ (CephFS)   ✗           ✗*
Object storage      ✗            ✓ (RGW)      ✓✓          Managed**
Upgrade ease        ✓✓           ✓            ✓✓          N/A
UI dashboard        ✓✓           ✓ (Ceph)     ✓✓          Console
Edge/IoT            ✓✓           ✗            ✓           ✗
Performance         Good         Excellent    Excellent   Good
Operational cost    Low          High         Medium      None

* EFS/Filestore as separate managed service
** S3/GCS/Azure Blob as separate managed service
```

---

## Monitoring Longhorn

```bash
# Check volume health via kubectl
kubectl -n longhorn-system get volumes.longhorn.io

# Check node status
kubectl -n longhorn-system get nodes.longhorn.io

# Check replica status for a specific volume
kubectl -n longhorn-system get replicas.longhorn.io -l longhornvolume=<volume-name>
```

```yaml
# ServiceMonitor for Prometheus
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

```
KEY LONGHORN METRICS
─────────────────────────────────────────────────────────────────

Volume Health:
├── longhorn_volume_state                # 1=attached, 0=detached
├── longhorn_volume_robustness           # 1=healthy, 0=degraded
├── longhorn_volume_actual_size_bytes    # Actual disk usage

Node Health:
├── longhorn_node_status                 # 1=ready, 0=not ready
├── longhorn_node_storage_capacity_bytes # Total capacity per node
├── longhorn_node_storage_usage_bytes    # Used capacity per node

Backup:
├── longhorn_backup_state                # Completed, InProgress, Error
├── longhorn_backup_actual_size_bytes    # Backup size in S3
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Setting `numberOfReplicas: 1` in production | Single point of failure, no recovery | Minimum 2 replicas, ideally 3 |
| Not configuring backup target | Node failure with all replicas = data loss | Configure S3/MinIO backup target from day one |
| Running Longhorn on nodes with <4GB RAM | OOM kills during replica rebuilds | Ensure 512MB+ available for Longhorn per node |
| Ignoring degraded volumes | One more failure away from data loss | Alert on `longhorn_volume_robustness != 1` and investigate |
| Using Longhorn for ReadWriteMany | Longhorn only supports RWO | Use Rook/CephFS or NFS for shared volumes |
| Not setting `dataLocality: best-effort` | Extra network hop for every I/O | Enable data locality to keep a replica on the consuming node |
| Skipping recurring backup jobs | Manual backups get forgotten | Configure `RecurringJob` for all production volumes |
| Over-provisioning on edge nodes | Disk fills up, all volumes fail | Monitor `longhorn_node_storage_usage_bytes`, set overprovisioning limits |

---

## Hands-On Exercise

### Task: Deploy Longhorn, Create PVCs, and Test Replica Failover

**Objective**: Deploy Longhorn on a kind cluster, provision a PVC, write data, simulate a node failure, and verify the volume survives with no data loss.

**Success Criteria**:
1. Longhorn installed and all components running
2. PVC provisioned with 2 replicas
3. Data written to the volume
4. Replica failover tested (volume remains accessible)
5. Snapshot created successfully

### Steps

```bash
# 1. Create a kind cluster with 3 workers
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

# 2. Install open-iscsi on kind nodes (required by Longhorn)
for node in longhorn-lab-worker longhorn-lab-worker2 longhorn-lab-worker3; do
  docker exec $node bash -c "apt-get update && apt-get install -y open-iscsi && systemctl enable iscsid && systemctl start iscsid"
done

# 3. Install Longhorn via Helm
helm repo add longhorn https://charts.longhorn.io
helm repo update

helm install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --create-namespace \
  --version 1.7.2 \
  --set defaultSettings.defaultReplicaCount=2 \
  --set defaultSettings.defaultDataLocality="best-effort"

echo "Waiting for Longhorn to be ready (2-3 minutes)..."
kubectl -n longhorn-system rollout status daemonset/longhorn-manager --timeout=300s
kubectl -n longhorn-system rollout status deployment/longhorn-ui --timeout=300s

# Verify all pods are running
kubectl -n longhorn-system get pods

# 4. Create a PVC using Longhorn
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
  containers:
    - name: writer
      image: busybox
      command: ["sh", "-c"]
      args:
        - |
          echo "Writing test data to Longhorn volume..."
          echo "Longhorn storage test - $(date)" > /data/test.txt
          dd if=/dev/urandom of=/data/random.bin bs=1M count=50
          md5sum /data/random.bin > /data/checksum.txt
          echo "Data written. Checksum:"
          cat /data/checksum.txt
          echo "Sleeping to keep pod alive..."
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
kubectl wait --for=condition=Ready pod/writer --timeout=120s

# 5. Verify data was written
kubectl logs writer
ORIGINAL_CHECKSUM=$(kubectl exec writer -- cat /data/checksum.txt)
echo "Original checksum: $ORIGINAL_CHECKSUM"

# 6. Check which node the writer pod is running on
WRITER_NODE=$(kubectl get pod writer -o jsonpath='{.spec.nodeName}')
echo "Writer pod is on: $WRITER_NODE"

# 7. Check Longhorn volume and replica placement
kubectl -n longhorn-system get volumes.longhorn.io
kubectl -n longhorn-system get replicas.longhorn.io

# 8. Create a snapshot before testing failover
# Access Longhorn API to create snapshot
kubectl -n longhorn-system port-forward svc/longhorn-frontend 8080:80 &
LH_PF_PID=$!
sleep 2

echo "Longhorn UI available at http://localhost:8080"
echo "You can create snapshots via the UI under Volumes > longhorn-test > Snapshots"

# 9. Simulate failure: delete the writer pod (Longhorn volume detaches and reattaches)
kubectl delete pod writer
kubectl apply -f longhorn-test-pvc.yaml
kubectl wait --for=condition=Ready pod/writer --timeout=120s

# 10. Verify data survived
echo "Verifying data integrity after pod restart..."
kubectl exec writer -- cat /data/test.txt
RESTORED_CHECKSUM=$(kubectl exec writer -- cat /data/checksum.txt)
echo "Restored checksum: $RESTORED_CHECKSUM"

if [ "$ORIGINAL_CHECKSUM" = "$RESTORED_CHECKSUM" ]; then
  echo "CHECKSUM MATCH - Failover test PASSED"
else
  echo "CHECKSUM MISMATCH - Failover test FAILED"
fi

# 11. Verify Longhorn volume health
kubectl -n longhorn-system get volumes.longhorn.io
```

### Verification

```bash
# Confirm PVC is bound
kubectl get pvc longhorn-test
# STATUS should be "Bound"

# Confirm volume is healthy
kubectl -n longhorn-system get volumes.longhorn.io -o wide
# STATE should be "attached", ROBUSTNESS should be "healthy"

# Confirm replicas are on different nodes
kubectl -n longhorn-system get replicas.longhorn.io -o wide
# NODE column should show different nodes

# Confirm data integrity
kubectl exec writer -- md5sum /data/random.bin
kubectl exec writer -- cat /data/checksum.txt
# Should match

# Clean up
kill $LH_PF_PID 2>/dev/null
kind delete cluster --name longhorn-lab
```

---

## Quiz

### Question 1
What are the three core components of Longhorn architecture, and what role does each play?

<details>
<summary>Show Answer</summary>

1. **Longhorn Manager** — A DaemonSet running on every node. It acts as the Kubernetes controller for Longhorn CRDs, handles volume lifecycle (create, attach, detach, delete), schedules replica placement, and orchestrates snapshots and backups.

2. **Longhorn Engine** — One instance per volume. It serves as the iSCSI target that kubelet mounts into pods. It handles synchronous write replication to all replicas and serves reads from any available replica.

3. **Replicas** — Stored as sparse files on the host filesystem of each node. Each volume has configurable replicas (default 3) spread across different nodes. They store the actual block data and participate in synchronous replication.
</details>

### Question 2
How does Longhorn's replica rebuild process differ from Ceph's OSD recovery?

<details>
<summary>Show Answer</summary>

**Longhorn rebuilds per-volume**: When a replica is lost, Longhorn rebuilds only the affected volume's replica on a healthy node. The rebuild reads from an existing healthy replica and writes to the new one. The volume remains fully accessible during the rebuild with no I/O pauses.

**Ceph recovers per-OSD**: When an OSD (entire disk) fails, Ceph must re-replicate every placement group (data chunk) that had a replica on that OSD. This can involve hundreds of gigabytes of data movement across the network, potentially impacting performance of all volumes sharing that storage pool.

Longhorn's per-volume approach means the blast radius of a failure is smaller, and rebuild I/O is proportional to the affected volume size rather than the entire disk's data.
</details>

### Question 3
When should you choose Longhorn over Rook/Ceph?

<details>
<summary>Show Answer</summary>

Choose Longhorn when:
- You only need **block storage (RWO)** — not shared filesystems or object storage
- Your team **lacks dedicated storage expertise** — Longhorn is significantly simpler to operate
- You're running **edge or small-medium clusters** (3-20 nodes) where Ceph's memory overhead is problematic
- You want **built-in backup to S3** without configuring a separate backup system
- You need **cross-cluster DR** with minimal setup
- You value **operational simplicity** over maximum features

Choose Rook/Ceph when you need CephFS (ReadWriteMany), object storage (S3 via RGW), 100TB+ scale, or a full converged storage platform.
</details>

### Question 4
What does the `dataLocality: best-effort` setting do, and why does it improve performance?

<details>
<summary>Show Answer</summary>

`dataLocality: best-effort` tells Longhorn to try to schedule one replica on the same node where the consuming pod is running.

This improves performance because reads from the local replica avoid network roundtrips entirely—the I/O goes directly to the local disk. Without data locality, every read and write must traverse the pod network to reach a remote replica, adding latency. The "best-effort" mode means Longhorn will try but won't fail volume attachment if it cannot achieve locality (e.g., if the node's disk is full).
</details>

### Question 5
How do Longhorn snapshots work, and how do they differ from backups?

<details>
<summary>Show Answer</summary>

**Snapshots** are local, instant, copy-on-write captures of a volume's state. When you take a snapshot, Longhorn marks the current data blocks as read-only and writes new changes to a new layer. Snapshots consume no extra space at creation time—space grows only as original blocks are modified. Snapshots are stored on the same nodes as the replicas.

**Backups** are copies of snapshot data sent to an external S3-compatible target (like MinIO or AWS S3). Backups are incremental at the block level—only changed blocks since the last backup are transferred. Backups survive complete cluster loss because they are stored externally.

Use snapshots for quick rollback within the same cluster. Use backups for disaster recovery across clusters.
</details>

---

## Key Takeaways

1. **Purpose-built for Kubernetes** — Not a general-purpose storage system adapted for K8s; designed from scratch for the container era
2. **Lightweight** — ~512MB per node vs 2-4GB for Ceph; viable on edge and resource-constrained nodes
3. **Simple operations** — Web UI, Helm upgrades, and recurring jobs replace complex storage administration
4. **Block storage only** — Does RWO very well; does not attempt CephFS or object storage
5. **Built-in backup and DR** — Incremental backups to S3, cross-cluster disaster recovery volumes
6. **Per-volume replication** — Synchronous replication with configurable replica count per volume
7. **Non-disruptive rebuilds** — Volume remains accessible during replica rebuild with no I/O pauses
8. **CNCF Incubating** — Active community, production-proven, on track toward graduation

---

## Next Steps

- **Previous Module**: [Module 16.2: MinIO](module-16.2-minio.md) — S3 object storage (great backup target for Longhorn)
- **Previous Module**: [Module 16.1: Rook/Ceph](module-16.1-rook-ceph.md) — Full storage platform comparison
- **Related**: [Scaling & Reliability - Velero](../scaling-reliability/module-6.3-velero.md) — Kubernetes-level backup alongside Longhorn volume backup
- **Related**: [K8s Distributions - K3s](../k8s-distributions/module-14.1-k3s.md) — Longhorn is the recommended storage for K3s

---

## Further Reading

- [Longhorn Documentation](https://longhorn.io/docs/)
- [Longhorn GitHub Repository](https://github.com/longhorn/longhorn)
- [Longhorn Architecture](https://longhorn.io/docs/latest/concepts/)
- [Data on Kubernetes Community](https://dok.community/)
- [CNCF Longhorn Case Studies](https://www.cncf.io/projects/longhorn/)

---

*"Longhorn proves that distributed storage doesn't have to be complicated. It does one thing—block storage for Kubernetes—and does it well enough that you can forget it's there. And that's exactly what good infrastructure should be."*

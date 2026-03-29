---
title: "Module 5.4: EKS Storage & Data Management"
slug: cloud/eks-deep-dive/module-5.4-eks-storage
sidebar:
  order: 5
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2h | **Prerequisites**: Module 5.1 (EKS Architecture & Control Plane)

## Why This Module Matters

In June 2023, an ad-tech company migrated their PostgreSQL database from RDS to a StatefulSet on EKS to reduce costs. The database ran on EBS gp3 volumes and performed well in testing. Two months into production, during a routine node upgrade, Kubernetes rescheduled the database pod to a node in a different Availability Zone. The pod came up -- but the EBS volume did not follow. EBS volumes are bound to a single AZ. The database pod sat in `Pending` state for 18 minutes while the on-call engineer figured out what happened. Meanwhile, their real-time bidding pipeline, which required sub-10ms response times, was returning errors on every request. The estimated revenue loss was $340,000.

Storage on Kubernetes is deceptively complex. In a traditional VM world, you attach a disk and forget about it. In Kubernetes, pods are ephemeral, they move between nodes, and they can be rescheduled across Availability Zones. If you do not understand the storage primitives and their constraints, your "highly available" architecture has a silent single-AZ failure mode hiding in plain sight.

In this module, you will learn how to use the EBS CSI driver for high-performance block storage (with gp3 provisioning, snapshots, and online resizing), the EFS CSI driver for shared ReadWriteMany filesystems, the Mountpoint for S3 CSI driver for cost-effective object storage access, and how to design StatefulSets that survive AZ failures.

---

## EBS CSI Driver: Block Storage for Pods

Amazon Elastic Block Store (EBS) provides persistent block-level storage volumes for EC2 instances. The EBS CSI driver lets Kubernetes manage these volumes as PersistentVolumes.

### Installing the EBS CSI Driver

The EBS CSI driver is an EKS Add-on. It requires an IAM role with permissions to create, attach, and manage EBS volumes.

```bash
# Create IAM role for the EBS CSI driver
cat > /tmp/ebs-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"]
  }]
}
EOF

aws iam create-role --role-name AmazonEKS_EBS_CSI_DriverRole \
  --assume-role-policy-document file:///tmp/ebs-trust.json

aws iam attach-role-policy --role-name AmazonEKS_EBS_CSI_DriverRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

# Install the add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EBS_CSI_DriverRole

# Verify
k get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
```

### StorageClass: gp3 Configuration

EBS gp3 volumes are the recommended default. They provide a baseline of 3,000 IOPS and 125 MiB/s throughput, independently configurable up to 16,000 IOPS and 1,000 MiB/s.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
  iops: "3000"       # baseline (free), up to 16000
  throughput: "125"   # baseline (free), up to 1000 MiB/s
  encrypted: "true"
  kmsKeyId: alias/eks-ebs-key   # optional: customer-managed KMS key
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

The `volumeBindingMode: WaitForFirstConsumer` setting is critical. It delays volume creation until a pod actually needs it, ensuring the volume is created in the same AZ as the node running the pod. Without this, Kubernetes might create the volume in AZ-a while the pod gets scheduled to AZ-b, causing a permanent mismatch.

### Using EBS Volumes in Pods

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: database
spec:
  accessModes:
    - ReadWriteOnce    # EBS supports only RWO
  storageClassName: ebs-gp3
  resources:
    requests:
      storage: 100Gi
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: database
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
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
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
        accessModes:
          - ReadWriteOnce
        storageClassName: ebs-gp3
        resources:
          requests:
            storage: 100Gi
```

### EBS Snapshots

The EBS CSI driver supports volume snapshots for backup and cloning.

```yaml
# Create a VolumeSnapshotClass
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Retain
---
# Take a snapshot
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot-20240315
  namespace: database
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: data-postgres-0
```

Restore from a snapshot by referencing it in a new PVC:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-restored
  namespace: database
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-gp3
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: postgres-snapshot-20240315
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### Online Volume Resizing

With `allowVolumeExpansion: true` in the StorageClass, you can grow EBS volumes without downtime:

```bash
# Edit the PVC to request more storage
k patch pvc data-postgres-0 -n database \
  --type merge \
  -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# Check resize progress
k get pvc data-postgres-0 -n database -o json | \
  jq '{requested: .spec.resources.requests.storage, actual: .status.capacity.storage, conditions: .status.conditions}'

# The resize happens in two phases:
# 1. AWS resizes the EBS volume (seconds)
# 2. The filesystem is expanded online (the CSI driver handles this)
```

> **Important**: EBS volumes can only be expanded, never shrunk. You can modify the volume type (gp2 to gp3) and adjust IOPS/throughput without detaching the volume, but there is a 6-hour cooldown between modifications.

---

## EFS CSI Driver: Shared Filesystem (ReadWriteMany)

EBS has a fundamental limitation: a volume can only be attached to one node at a time (`ReadWriteOnce`). When multiple pods across multiple nodes need to read and write the same files, you need Amazon Elastic File System (EFS).

### EFS vs EBS at a Glance

| Feature | EBS (gp3) | EFS |
| :--- | :--- | :--- |
| **Access mode** | ReadWriteOnce (single node) | ReadWriteMany (multi-node) |
| **AZ scope** | Single AZ | Multi-AZ (regional) |
| **Performance** | Consistent, provisioned IOPS | Bursting or provisioned throughput |
| **Latency** | Sub-millisecond | Single-digit milliseconds |
| **Pricing** | $0.08/GB-month (gp3) | $0.30/GB-month (Standard) |
| **Max size** | 64 TiB per volume | Petabytes (elastic) |
| **Best for** | Databases, single-writer workloads | Shared content, CMS, ML training data |

### Setting Up EFS

```bash
# Create IAM role for EFS CSI
aws iam create-role --role-name AmazonEKS_EFS_CSI_DriverRole \
  --assume-role-policy-document file:///tmp/ebs-trust.json  # Same Pod Identity trust

aws iam attach-role-policy --role-name AmazonEKS_EFS_CSI_DriverRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy

# Install the EFS CSI add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-efs-csi-driver \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EFS_CSI_DriverRole

# Create an EFS filesystem
EFS_ID=$(aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --tags Key=Name,Value=eks-shared-storage \
  --query 'FileSystemId' --output text)

# Create mount targets in each subnet (one per AZ)
# The security group must allow NFS (port 2049) from the node security group
EFS_SG=$(aws ec2 create-security-group \
  --group-name EFS-SG \
  --description "Allow NFS from EKS nodes" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Get the cluster security group
CLUSTER_SG=$(aws eks describe-cluster --name my-cluster \
  --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $EFS_SG \
  --protocol tcp --port 2049 \
  --source-group $CLUSTER_SG

# Create mount targets
aws efs create-mount-target \
  --file-system-id $EFS_ID \
  --subnet-id $PRIV_SUB1 \
  --security-groups $EFS_SG

aws efs create-mount-target \
  --file-system-id $EFS_ID \
  --subnet-id $PRIV_SUB2 \
  --security-groups $EFS_SG

echo "EFS filesystem: $EFS_ID"
```

### Using EFS in Pods

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap         # Use EFS Access Points
  fileSystemId: fs-0123456789abcdef
  directoryPerms: "700"
  gidRangeStart: "1000"
  gidRangeEnd: "2000"
  basePath: "/dynamic_provisioning"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-media
  namespace: cms
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 50Gi    # EFS is elastic; this is a soft quota
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cms-web
  namespace: cms
spec:
  replicas: 5    # All 5 replicas share the same EFS volume!
  selector:
    matchLabels:
      app: cms-web
  template:
    metadata:
      labels:
        app: cms-web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          volumeMounts:
            - name: media
              mountPath: /usr/share/nginx/html/media
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
      volumes:
        - name: media
          persistentVolumeClaim:
            claimName: shared-media
```

All five replicas mount the same EFS filesystem at `/usr/share/nginx/html/media`. When one pod writes a file, all other pods can read it immediately. This is the primary use case for EFS on EKS: shared content, user uploads, configuration files, and ML training datasets.

---

## Mountpoint for S3 CSI Driver

Mountpoint for S3 is the newest storage option for EKS. It mounts an S3 bucket as a local filesystem inside your pod, providing read-optimized access to object storage without modifying your application code.

### When to Use Mountpoint for S3

```text
Traditional approach:
  App → AWS SDK → S3 API → Object

Mountpoint for S3:
  App → read("/mnt/s3/data/file.csv") → Mountpoint driver → S3 API → Object
```

This is ideal for ML training workloads, data processing pipelines, and any application that expects data on a local filesystem but the data actually lives in S3.

### Setup

```bash
# Install the Mountpoint for S3 CSI add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-mountpoint-s3-csi-driver \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/S3MountpointRole
```

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: s3-training-data
spec:
  capacity:
    storage: 1Ti    # Informational only; S3 is unlimited
  accessModes:
    - ReadWriteMany
  csi:
    driver: s3.csi.aws.com
    volumeHandle: s3-csi-driver-volume
    volumeAttributes:
      bucketName: my-ml-training-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: training-data-pvc
  namespace: ml
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: ""    # Empty string for pre-provisioned PV
  resources:
    requests:
      storage: 1Ti
  volumeName: s3-training-data
---
apiVersion: batch/v1
kind: Job
metadata:
  name: model-training
  namespace: ml
spec:
  template:
    spec:
      containers:
        - name: trainer
          image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/model-trainer:latest
          command: ["python", "train.py", "--data-dir=/data"]
          volumeMounts:
            - name: training-data
              mountPath: /data
              readOnly: true
          resources:
            requests:
              cpu: "4"
              memory: 16Gi
      volumes:
        - name: training-data
          persistentVolumeClaim:
            claimName: training-data-pvc
      restartPolicy: Never
```

### Mountpoint for S3 Limitations

- **Reads are optimized; writes have restrictions**: Sequential writes to new files work, but random writes, appends to existing files, and file renames are not supported
- **No file locking**: Multiple pods can read simultaneously, but concurrent writes to the same file will cause corruption
- **Eventual consistency**: S3 is strongly consistent for reads-after-writes, but Mountpoint caches directory listings which may briefly show stale results
- **Latency**: Higher than EBS or EFS. First-byte latency to S3 is typically 20-100ms, making it unsuitable for databases or latency-sensitive workloads

---

## StatefulSets Across Availability Zones

The ad-tech company from the opening learned the hard way that EBS volumes are tied to a single AZ. Designing stateful workloads for AZ resilience requires careful planning.

### The Problem

```text
AZ-1a                              AZ-1b
┌─────────────────────┐           ┌─────────────────────┐
│ Node-1              │           │ Node-2              │
│                     │           │                     │
│ postgres-0 ◄── EBS  │           │                     │
│ (AZ-1a volume)      │           │                     │
└─────────────────────┘           └─────────────────────┘

If Node-1 fails, Kubernetes reschedules postgres-0 to Node-2.
But the EBS volume is in AZ-1a. Node-2 is in AZ-1b.
Volume cannot be attached. Pod is stuck in Pending.
```

### Solution 1: Topology-Aware Scheduling

Use `topologySpreadConstraints` and `nodeAffinity` to ensure StatefulSet pods stay in their volume's AZ:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: database
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: postgres
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: ebs-gp3    # WaitForFirstConsumer is key!
        resources:
          requests:
            storage: 100Gi
```

With `WaitForFirstConsumer`, the PVC is not bound until the pod is scheduled. Kubernetes picks the node first, then creates the EBS volume in the same AZ. If the node fails, the pod can only be rescheduled to another node in the same AZ (where the volume lives).

### Solution 2: Multiple Nodes Per AZ

Ensure you have enough nodes in each AZ to absorb a node failure:

```bash
# Create a node group that spans multiple AZs with at least 2 nodes per AZ
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name stateful-workers \
  --node-role arn:aws:iam::123456789012:role/EKSNodeRole \
  --subnets subnet-az1a subnet-az1b subnet-az1c \
  --instance-types m6i.xlarge \
  --scaling-config minSize=6,maxSize=12,desiredSize=6 \
  --labels workload=stateful
```

With 6 nodes across 3 AZs (2 per AZ), if a node fails, the StatefulSet pod can move to the other node in the same AZ, and the EBS volume can follow.

### Solution 3: Application-Level Replication

For truly critical databases, use application-level replication instead of relying on a single EBS volume:

```text
AZ-1a                    AZ-1b                    AZ-1c
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ postgres-0   │        │ postgres-1   │        │ postgres-2   │
│ (primary)    │───────►│ (replica)    │───────►│ (replica)    │
│ EBS: vol-aaa │ stream │ EBS: vol-bbb │ stream │ EBS: vol-ccc │
└──────────────┘  rep.  └──────────────┘  rep.  └──────────────┘
```

Each replica has its own EBS volume in its own AZ. If AZ-1a fails entirely, postgres-1 or postgres-2 can be promoted. This is the pattern used by PostgreSQL (Patroni), MySQL (Group Replication), and MongoDB (replica sets).

---

## Storage Decision Matrix

| Use Case | Storage Type | Access Mode | Key Constraint |
| :--- | :--- | :--- | :--- |
| Database (single writer) | EBS gp3 | ReadWriteOnce | Single AZ, plan for node failure |
| High-IOPS database | EBS io2 | ReadWriteOnce | Expensive ($0.125/GB + $0.065/IOPS) |
| Shared CMS media | EFS | ReadWriteMany | Higher latency, ~4x EBS cost |
| ML training data | Mountpoint S3 | ReadWriteMany | Read-optimized, no random writes |
| Container scratch space | emptyDir / Instance Store | N/A (ephemeral) | Lost on pod restart |
| Log shipping buffer | EBS gp3 (small) | ReadWriteOnce | Use FluentBit buffer, not large volumes |

---

## Did You Know?

1. The `WaitForFirstConsumer` volume binding mode in a StorageClass was added specifically to solve the AZ mismatch problem. Before it existed, Kubernetes would create the EBS volume immediately when the PVC was created, often in a random AZ. Then the pod scheduler would pick a different AZ for the pod, and the volume could never be attached. This single StorageClass setting prevents the most common EKS storage failure mode.

2. EBS gp3 volumes provide 3,000 IOPS and 125 MiB/s of throughput for free at every volume size. In the gp2 era, you needed a 1,000 GB volume to get 3,000 IOPS (because gp2 scales IOPS linearly with size at 3 IOPS/GB). With gp3, even a 1 GB volume gets the full 3,000 IOPS baseline. This makes gp3 cheaper than gp2 for nearly every workload.

3. EFS charges $0.30/GB-month for Standard storage, but offers an Infrequent Access (IA) tier at $0.016/GB-month -- a 95% reduction. With EFS Lifecycle Management, files not accessed for 7, 14, 30, 60, or 90 days are automatically moved to IA. For CMS media storage where most images are uploaded once and rarely re-accessed, IA can reduce EFS costs by 80-90%.

4. Mountpoint for S3 was built using Rust and runs as a FUSE filesystem. It achieves throughput of up to 100 Gbps for sequential reads by splitting large file reads into parallel multi-part downloads to S3. For ML training workloads reading large datasets, this can match or exceed the performance of EBS io2 volumes at a fraction of the cost ($0.023/GB-month for S3 Standard vs $0.125/GB-month for io2).

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Missing `WaitForFirstConsumer` in StorageClass** | Using default `Immediate` binding mode. PVC creates volume in wrong AZ. | Always set `volumeBindingMode: WaitForFirstConsumer` for EBS StorageClasses. This is not optional. |
| **Running StatefulSet with no nodes in volume's AZ** | Auto Scaler scales down nodes in one AZ, leaving orphaned volumes. | Set minimum node counts per AZ. Configure Cluster Autoscaler or Karpenter to respect `topologySpreadConstraints`. |
| **Using EBS for shared storage between pods** | Not knowing EFS exists, or assuming EBS can be mounted RWX. | EBS is ReadWriteOnce only. Use EFS for ReadWriteMany. If sharing between pods on the same node, use `ReadWriteOncePod` (Kubernetes 1.27+). |
| **Not encrypting EBS volumes** | Forgetting to add `encrypted: "true"` in the StorageClass parameters. | Add `encrypted: "true"` to your StorageClass. For compliance, use a customer-managed KMS key via `kmsKeyId`. |
| **EFS without mount target in node's AZ** | Creating EFS mount targets in only one AZ, but nodes run in multiple AZs. | Create a mount target in every AZ where your EKS nodes run. Without a local mount target, pods either fail to mount or route NFS through cross-AZ traffic. |
| **Using Mountpoint S3 for random writes** | Treating S3 like a filesystem. Attempting appends or overwrites. | Mountpoint S3 supports sequential writes to new files only. For read-modify-write patterns, use the S3 SDK directly or use EFS. |
| **Not setting resource requests on storage-heavy pods** | Database pods getting OOM-killed because no memory limits were set. | Always set memory requests and limits on database pods. PostgreSQL, MySQL, and Redis all benefit from explicit memory allocation. |
| **Ignoring EBS modification cooldown** | Attempting to resize or change volume type twice within 6 hours. | AWS imposes a 6-hour cooldown between EBS volume modifications. Plan changes carefully and do not make incremental adjustments. |

---

## Quiz

<details>
<summary>Question 1: You create a PersistentVolumeClaim using a StorageClass with `volumeBindingMode: Immediate`. The PVC is created and bound, but when the pod using it is scheduled, the pod stays in Pending state with an "volume node affinity conflict" error. What happened?</summary>

With `Immediate` binding mode, Kubernetes creates the EBS volume as soon as the PVC is created, before any pod is scheduled. The volume might be created in AZ-1a. When the scheduler tries to place the pod, it might select a node in AZ-1b. Since EBS volumes can only be attached to instances in the same AZ, the pod cannot start. The fix is to use `volumeBindingMode: WaitForFirstConsumer`, which delays volume creation until the pod is scheduled, ensuring the volume is created in the same AZ as the selected node.
</details>

<details>
<summary>Question 2: Your team needs shared storage accessible by 10 pods across 3 nodes in different AZs. Which storage option should you use and why?</summary>

Use **Amazon EFS** with the EFS CSI driver. EFS supports `ReadWriteMany` (RWX) access mode, meaning multiple pods on multiple nodes can read and write simultaneously. EFS is a regional service that spans all AZs automatically (as long as you create mount targets in each AZ). EBS cannot be used because it only supports `ReadWriteOnce` (single node attachment). Mountpoint for S3 could work for read-heavy workloads but does not support random writes or file modifications.
</details>

<details>
<summary>Question 3: You have a 50 GB EBS gp3 volume that needs to be resized to 200 GB. Can this be done without downtime? What about shrinking from 200 GB to 100 GB later?</summary>

**Expanding** from 50 GB to 200 GB can be done online without downtime, provided the StorageClass has `allowVolumeExpansion: true`. You simply edit the PVC to request 200 GB, and the EBS CSI driver handles the volume expansion and filesystem resize in the background. **Shrinking** from 200 GB to 100 GB is **not possible**. EBS volumes can only be expanded, never shrunk. If you need a smaller volume, you must create a new 100 GB volume, copy the data, and switch the PVC. Also remember there is a 6-hour cooldown between volume modifications.
</details>

<details>
<summary>Question 4: When would you choose Mountpoint for S3 over EFS for a machine learning workload?</summary>

Choose Mountpoint for S3 when the ML workload needs to **read large datasets** (training data, feature stores) that already exist in S3 and the application expects filesystem-style access (reading files from a directory path). S3 storage costs $0.023/GB-month vs EFS at $0.30/GB-month -- a 13x cost difference. Mountpoint for S3 also achieves very high sequential read throughput (up to 100 Gbps) via parallel multi-part downloads. Choose EFS instead if the workload needs to write intermediate results, modify files in place, or requires file locking between processes.
</details>

<details>
<summary>Question 5: A StatefulSet has 3 replicas spread across 3 AZs. AZ-1b suffers a complete outage. What happens to the replica in AZ-1b, and can Kubernetes reschedule it to AZ-1a or AZ-1c?</summary>

The replica in AZ-1b becomes unreachable. After the node's `node.kubernetes.io/unreachable` taint timeout (default 5 minutes), Kubernetes marks the pod for deletion. However, Kubernetes **cannot reschedule it to AZ-1a or AZ-1c** because its EBS PersistentVolume is physically in AZ-1b and cannot be attached to nodes in other AZs. The pod will remain unschedulable until AZ-1b recovers or until an administrator manually deletes the PVC and allows a new volume to be created in a healthy AZ (losing the data). This is why application-level replication (e.g., PostgreSQL streaming replication across AZs) is essential for critical stateful workloads.
</details>

<details>
<summary>Question 6: What is the difference between `ReadWriteOnce` and `ReadWriteOncePod`, and when does the distinction matter?</summary>

`ReadWriteOnce` (RWO) allows the volume to be mounted as read-write by a **single node**. However, multiple pods on that same node can all mount the volume simultaneously. `ReadWriteOncePod` (RWOP, available in Kubernetes 1.27+) restricts the volume to a **single pod** across the entire cluster. The distinction matters for databases where only one process should write to the data directory. With RWO, if you accidentally run two database pods on the same node (e.g., during a rolling update), both could write to the volume simultaneously, causing data corruption. RWOP prevents this by ensuring only one pod can mount the volume at a time.
</details>

---

## Hands-On Exercise: CMS with EBS for DB + EFS for Shared Media

In this exercise, you will build a content management system with PostgreSQL on EBS (single-writer database) and shared media storage on EFS (multi-reader/writer for uploaded images).

**What you will build:**

```text
┌────────────────────────────────────────────────────────────────┐
│  EKS Cluster                                                   │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Namespace: cms                                          │  │
│  │                                                          │  │
│  │  ┌─────────────┐     ┌─────────────┐                    │  │
│  │  │ postgres-0  │     │ cms-web     │ x3 replicas       │  │
│  │  │ (StatefulSet)│     │ (Deployment) │                    │  │
│  │  │             │     │             │                    │  │
│  │  │ EBS gp3     │     │ EFS Mount   │ ← all 3 share     │  │
│  │  │ /var/lib/pg │     │ /media      │   same EFS volume  │  │
│  │  └─────────────┘     └─────────────┘                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Task 1: Install EBS and EFS CSI Drivers

<details>
<summary>Solution</summary>

```bash
# Create IAM roles (using Pod Identity trust)
cat > /tmp/csi-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"]
  }]
}
EOF

# EBS CSI Role
aws iam create-role --role-name EKS_EBS_CSI_Role \
  --assume-role-policy-document file:///tmp/csi-trust.json
aws iam attach-role-policy --role-name EKS_EBS_CSI_Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

# EFS CSI Role
aws iam create-role --role-name EKS_EFS_CSI_Role \
  --assume-role-policy-document file:///tmp/csi-trust.json
aws iam attach-role-policy --role-name EKS_EFS_CSI_Role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Install add-ons
aws eks create-addon --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::${ACCOUNT_ID}:role/EKS_EBS_CSI_Role

aws eks create-addon --cluster-name my-cluster \
  --addon-name aws-efs-csi-driver \
  --service-account-role-arn arn:aws:iam::${ACCOUNT_ID}:role/EKS_EFS_CSI_Role

# Verify both drivers are running
k get pods -n kube-system -l 'app.kubernetes.io/name in (aws-ebs-csi-driver,aws-efs-csi-driver)'
```

</details>

### Task 2: Create StorageClasses and EFS Filesystem

<details>
<summary>Solution</summary>

```bash
# Create the EBS gp3 StorageClass
cat <<'EOF' | k apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
  encrypted: "true"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF

# Create EFS filesystem
EFS_ID=$(aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --tags Key=Name,Value=cms-media-storage \
  --query 'FileSystemId' --output text)

# Get cluster VPC and subnets
VPC_ID=$(aws eks describe-cluster --name my-cluster \
  --query 'cluster.resourcesVpcConfig.vpcId' --output text)
CLUSTER_SG=$(aws eks describe-cluster --name my-cluster \
  --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text)

# Create EFS security group
EFS_SG=$(aws ec2 create-security-group \
  --group-name CMS-EFS-SG --description "NFS for CMS" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress \
  --group-id $EFS_SG --protocol tcp --port 2049 --source-group $CLUSTER_SG

# Create mount targets (get private subnet IDs from your cluster)
SUBNET_IDS=$(aws eks describe-cluster --name my-cluster \
  --query 'cluster.resourcesVpcConfig.subnetIds[]' --output text)
for SUBNET in $SUBNET_IDS; do
  aws efs create-mount-target \
    --file-system-id $EFS_ID \
    --subnet-id $SUBNET \
    --security-groups $EFS_SG 2>/dev/null || true
done

echo "EFS filesystem: $EFS_ID"

# Create EFS StorageClass
cat <<EOF | k apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: ${EFS_ID}
  directoryPerms: "755"
  basePath: "/cms-media"
EOF
```

</details>

### Task 3: Deploy PostgreSQL with EBS Storage

<details>
<summary>Solution</summary>

```bash
k create namespace cms

# Create database secret
k create secret generic postgres-secret -n cms \
  --from-literal=password='DojoSecurePass2024!'

# Deploy PostgreSQL StatefulSet
cat <<'EOF' | k apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: cms
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
            - name: POSTGRES_DB
              value: cmsdb
            - name: POSTGRES_USER
              value: cmsadmin
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "cmsadmin", "-d", "cmsdb"]
            initialDelaySeconds: 10
            periodSeconds: 5
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 2Gi
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: ebs-gp3
        resources:
          requests:
            storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: cms
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
  clusterIP: None    # Headless service for StatefulSet
EOF

# Wait for PostgreSQL to be ready
k wait --for=condition=Ready pod/postgres-0 -n cms --timeout=120s

# Verify
k exec -n cms postgres-0 -- pg_isready -U cmsadmin -d cmsdb
```

</details>

### Task 4: Deploy CMS Web Tier with EFS Shared Storage

<details>
<summary>Solution</summary>

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cms-media
  namespace: cms
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cms-web
  namespace: cms
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cms-web
  template:
    metadata:
      labels:
        app: cms-web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          volumeMounts:
            - name: media
              mountPath: /usr/share/nginx/html/media
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
      volumes:
        - name: media
          persistentVolumeClaim:
            claimName: cms-media
---
apiVersion: v1
kind: Service
metadata:
  name: cms-web
  namespace: cms
spec:
  selector:
    app: cms-web
  ports:
    - port: 80
  type: ClusterIP
EOF

# Wait for all pods to be ready
k wait --for=condition=Ready pods -l app=cms-web -n cms --timeout=120s

# Verify all 3 replicas share the same EFS volume
# Write a file from one pod
k exec -n cms $(k get pods -n cms -l app=cms-web -o name | head -1) -- \
  sh -c 'echo "Hello from pod 1" > /usr/share/nginx/html/media/test.txt'

# Read from another pod
k exec -n cms $(k get pods -n cms -l app=cms-web -o name | tail -1) -- \
  cat /usr/share/nginx/html/media/test.txt
# Should print: "Hello from pod 1"
```

</details>

### Task 5: Take an EBS Snapshot and Resize the Volume

<details>
<summary>Solution</summary>

```bash
# Install snapshot CRDs (if not already installed)
k apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/master/client/config/crd/snapshot.storage.k8s.io_volumesnapshotclasses.yaml
k apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/master/client/config/crd/snapshot.storage.k8s.io_volumesnapshotcontents.yaml
k apply -f https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/master/client/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml

# Create VolumeSnapshotClass
cat <<'EOF' | k apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Retain
EOF

# Take a snapshot of the PostgreSQL volume
cat <<'EOF' | k apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-backup
  namespace: cms
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: data-postgres-0
EOF

# Check snapshot status
k get volumesnapshot postgres-backup -n cms -o json | \
  jq '{ready: .status.readyToUse, size: .status.restoreSize}'

# Resize the PVC from 20Gi to 50Gi (online, no downtime)
k patch pvc data-postgres-0 -n cms \
  --type merge \
  -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'

# Monitor the resize
k get pvc data-postgres-0 -n cms -w
# Wait until CAPACITY shows 50Gi

# Verify inside the pod
k exec -n cms postgres-0 -- df -h /var/lib/postgresql/data
```

</details>

### Task 6: Verify AZ Resilience

<details>
<summary>Solution</summary>

```bash
# Check which AZ the PostgreSQL pod and volume are in
PG_NODE=$(k get pod postgres-0 -n cms -o jsonpath='{.spec.nodeName}')
PG_AZ=$(k get node $PG_NODE -o jsonpath='{.metadata.labels.topology\.kubernetes\.io/zone}')
echo "PostgreSQL pod is in AZ: $PG_AZ"

# Check the EBS volume's AZ
PV_NAME=$(k get pvc data-postgres-0 -n cms -o jsonpath='{.spec.volumeName}')
VOL_ID=$(k get pv $PV_NAME -o jsonpath='{.spec.csi.volumeHandle}')
VOL_AZ=$(aws ec2 describe-volumes --volume-ids $VOL_ID \
  --query 'Volumes[0].AvailabilityZone' --output text)
echo "EBS volume is in AZ: $VOL_AZ"

# Verify they match
if [ "$PG_AZ" = "$VOL_AZ" ]; then
  echo "PASS: Pod and volume are in the same AZ ($PG_AZ)"
else
  echo "FAIL: AZ mismatch! Pod=$PG_AZ, Volume=$VOL_AZ"
fi

# Verify EFS is accessible from all AZs
for POD in $(k get pods -n cms -l app=cms-web -o name); do
  POD_NODE=$(k get $POD -n cms -o jsonpath='{.spec.nodeName}')
  POD_AZ=$(k get node $POD_NODE -o jsonpath='{.metadata.labels.topology\.kubernetes\.io/zone}')
  echo "$POD on $POD_NODE in $POD_AZ"
  k exec -n cms $POD -- ls /usr/share/nginx/html/media/test.txt
done
```

</details>

### Clean Up

```bash
k delete namespace cms
k delete volumesnapshotclass ebs-snapshot-class
k delete storageclass ebs-gp3 efs-sc
# Delete EFS filesystem and mount targets
aws efs delete-file-system --file-system-id $EFS_ID
```

### Success Criteria

- [ ] I installed EBS and EFS CSI drivers as EKS add-ons
- [ ] I created an EBS gp3 StorageClass with `WaitForFirstConsumer` binding mode
- [ ] I deployed PostgreSQL as a StatefulSet with EBS persistent storage
- [ ] I created an EFS filesystem with mount targets and deployed a shared media volume
- [ ] I verified 3 web pods can all read and write to the same EFS volume
- [ ] I took an EBS snapshot and resized the volume online from 20Gi to 50Gi
- [ ] I confirmed the PostgreSQL pod and its EBS volume are in the same AZ
- [ ] I can explain why EBS volumes cannot follow pods across AZs

---

## Next Module

Your stateful workloads are running with persistent storage. But how do you scale them efficiently, observe their behavior, and control costs? Head to [Module 5.5: EKS Production -- Scaling, Observability & Cost](../module-5.5-eks-production/) to master Karpenter, Container Insights, and cost optimization with Kubecost.

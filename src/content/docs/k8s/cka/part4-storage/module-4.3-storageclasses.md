---
title: "Module 4.3: StorageClasses & Dynamic Provisioning"
slug: k8s/cka/part4-storage/module-4.3-storageclasses
sidebar:
  order: 4
lab:
  id: cka-4.3-storageclasses
  url: https://killercoda.com/kubedojo/scenario/cka-4.3-storageclasses
  duration: "35 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Automation of storage provisioning
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 4.2 (PV & PVC), Module 1.2 (CSI)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Create** StorageClasses for dynamic provisioning with cloud and local provisioners
- **Configure** binding modes (Immediate vs WaitForFirstConsumer) and explain when each is appropriate
- **Implement** volume expansion on existing PVCs and explain the requirements
- **Debug** dynamic provisioning failures by checking StorageClass, provisioner pods, and events

---

## Why This Module Matters

In Module 4.2, you manually created PersistentVolumes before creating PersistentVolumeClaims. This doesn't scale - imagine an admin creating hundreds of PVs for every storage request! StorageClasses enable **dynamic provisioning**: create a PVC, and Kubernetes automatically provisions the underlying storage. The CKA exam tests both understanding StorageClasses and configuring dynamic provisioning.

> **The Vending Machine Analogy**
>
> Think of static provisioning like ordering custom furniture - someone has to build it before you can use it. Dynamic provisioning is like a vending machine: you select what you want (StorageClass), insert your request (PVC), and out comes your storage (PV). The StorageClass is the vending machine - it knows how to produce different types of storage on demand.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Understand how StorageClasses enable dynamic provisioning
- Create and configure StorageClasses
- Set a default StorageClass for the cluster
- Use parameters to customize provisioned storage
- Understand volume binding modes
- Troubleshoot dynamic provisioning issues

---

## Did You Know?

- **Cloud clusters have defaults**: GKE, EKS, and AKS all come with pre-configured default StorageClasses that provision cloud-native storage
- **kind/minikube have provisioners too**: Even local clusters include dynamic provisioners (rancher.io/local-path for kind, k8s.io/minikube-hostpath for minikube)
- **StorageClasses are immutable**: Once created, you can't change a StorageClass - you must delete and recreate it

---

## Part 1: Understanding StorageClasses

### 1.1 Static vs Dynamic Provisioning

```
┌──────────────────────────────────────────────────────────────────────┐
│               Static vs Dynamic Provisioning                          │
│                                                                       │
│   STATIC (Manual)                   DYNAMIC (Automatic)               │
│   ───────────────                   ────────────────────              │
│                                                                       │
│   1. Admin creates PV               1. Admin creates StorageClass     │
│      │                                 │                              │
│      ▼                                 ▼                              │
│   2. Dev creates PVC                2. Dev creates PVC                │
│      │                                 │                              │
│      ▼                                 ▼                              │
│   3. Kubernetes binds               3. Provisioner creates PV         │
│      PVC to existing PV                │                              │
│                                        ▼                              │
│                                     4. Kubernetes binds PVC to new PV │
│                                                                       │
│   Pro: Full control                 Pro: Self-service, scalable       │
│   Con: Admin bottleneck             Con: Less control per volume      │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 StorageClass Components

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"  # Optional
provisioner: kubernetes.io/aws-ebs    # Who creates the storage
parameters:                            # Provisioner-specific settings
  type: gp3
  iopsPerGB: "10"
reclaimPolicy: Delete                  # What happens when PVC deleted
volumeBindingMode: WaitForFirstConsumer  # When to provision
allowVolumeExpansion: true             # Can resize later?
mountOptions:                          # Mount options for volumes
  - debug
```

### 1.3 Common Provisioners

| Provisioner | Cloud/Platform | Storage Type |
|-------------|---------------|--------------|
| kubernetes.io/aws-ebs | AWS | EBS volumes |
| kubernetes.io/gce-pd | GCP | Persistent Disk |
| kubernetes.io/azure-disk | Azure | Managed Disk |
| kubernetes.io/azure-file | Azure | Azure Files |
| ebs.csi.aws.com | AWS (CSI) | EBS via CSI |
| pd.csi.storage.gke.io | GCP (CSI) | PD via CSI |
| rancher.io/local-path | kind | Local path |
| k8s.io/minikube-hostpath | minikube | Host path |

---

## Part 2: Creating StorageClasses

### 2.1 Basic StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

### 2.2 AWS EBS StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ebs
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iopsPerGB: "50"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789:key/abc-123"
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 2.3 GCP Persistent Disk StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd    # For HA
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 2.4 Azure Disk StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium
provisioner: disk.csi.azure.com
parameters:
  storageaccounttype: Premium_LRS
  kind: Managed
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 2.5 Local Development (kind/minikube)

**kind** (uses local-path-provisioner):
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-path
provisioner: rancher.io/local-path
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

**minikube**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: k8s.io/minikube-hostpath
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

---

## Part 3: Default StorageClass

### 3.1 Setting a Default

Only one StorageClass should be default. Mark it with an annotation:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"  # The magic annotation
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
```

Or patch an existing one:
```bash
k patch storageclass standard -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "true"}}}'
```

### 3.2 Checking Default StorageClass

```bash
k get sc
# NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE
# standard (default)   kubernetes.io/aws-ebs   Delete          WaitForFirstConsumer
# fast-ssd             kubernetes.io/aws-ebs   Delete          Immediate
```

### 3.3 PVC Without StorageClass

When a PVC doesn't specify `storageClassName`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  # No storageClassName specified - uses default!
```

**Behavior**:
- If default StorageClass exists → Uses default, triggers dynamic provisioning
- If no default exists → PVC stays Pending until matching PV appears

### 3.4 Opting Out of Dynamic Provisioning

To explicitly avoid dynamic provisioning:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: static-only-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: ""    # Empty string = no dynamic provisioning
```

---

## Part 4: Volume Binding Modes

### 4.1 Immediate vs WaitForFirstConsumer

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Volume Binding Modes                               │
│                                                                       │
│   IMMEDIATE                         WAITFORFIRSTCONSUMER              │
│   ─────────                         ────────────────────              │
│                                                                       │
│   PVC Created                       PVC Created                       │
│       │                                 │                             │
│       ▼                                 ▼                             │
│   PV Provisioned                    PVC stays Pending                 │
│   immediately                           │                             │
│       │                                 │                             │
│       │                             Pod scheduled                     │
│       │                                 │                             │
│       │                                 ▼                             │
│       │                             PV Provisioned                    │
│       │                             (on same zone as pod)             │
│       │                                 │                             │
│       ▼                                 ▼                             │
│   Pod scheduled                     Pod can use storage               │
│   (may fail if wrong zone!)                                           │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Why WaitForFirstConsumer Matters

**Problem with Immediate**:
```
Node: us-east-1a          Node: us-east-1b
┌─────────────┐           ┌─────────────┐
│             │           │    Pod      │  ← Scheduler puts pod here
│             │           │   (needs    │
│             │           │   storage)  │
└─────────────┘           └─────────────┘
      ↑
      │
   EBS Volume             ✗ Volume in wrong zone!
   (provisioned           ✗ Pod can't start!
    immediately in 1a)
```

**Solution with WaitForFirstConsumer**:
```
Node: us-east-1a          Node: us-east-1b
┌─────────────┐           ┌─────────────┐
│             │           │    Pod      │  ← Scheduler puts pod here
│             │           │   (needs    │
│             │           │   storage)  │
└─────────────┘           └─────────────┘
                                ↑
                                │
                          EBS Volume      ✓ Volume in correct zone!
                          (provisioned    ✓ Pod starts successfully!
                           in 1b AFTER
                           pod scheduled)
```

### 4.3 When to Use Each Mode

| Mode | Use Case |
|------|----------|
| Immediate | NFS, distributed storage, zone-less storage |
| WaitForFirstConsumer | Zone-specific storage (EBS, GCE PD, Azure Disk), local storage |

> **Pause and predict**: You have a StorageClass with `volumeBindingMode: Immediate` for AWS EBS. A developer creates a PVC, and a PV is immediately provisioned in `us-east-1a`. The scheduler then places the pod on a node in `us-east-1b`. What happens when the pod tries to start? How would changing the binding mode prevent this?

---

## Part 5: Volume Expansion

### 5.1 Enabling Volume Expansion

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: expandable
provisioner: kubernetes.io/aws-ebs
allowVolumeExpansion: true    # Must be true to resize PVCs
parameters:
  type: gp3
```

### 5.2 Expanding a PVC

```bash
# Original PVC with 10Gi
k get pvc my-claim
# NAME       STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# my-claim   Bound    pv-001   10Gi       RWO            expandable

# Edit to request more space
k patch pvc my-claim -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'

# Or edit manually
k edit pvc my-claim
# Change spec.resources.requests.storage to 20Gi
```

### 5.3 Expansion Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PVC Expansion Process                             │
│                                                                      │
│   1. Edit PVC ──► 2. Controller resizes      ──► 3. Filesystem     │
│      (increase      underlying storage            expansion         │
│       size)         (e.g., EBS volume)            (when mounted)    │
│                                                                      │
│   Status shows:                                                      │
│   - "Resizing" - storage backend being resized                      │
│   - "FileSystemResizePending" - waiting for pod to mount            │
│                                                                      │
│   ⚠️  Note: Expansion requires pod restart for some provisioners    │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.4 Checking Expansion Status

```bash
k describe pvc my-claim

# Look for conditions:
# Conditions:
#   Type                      Status
#   ----                      ------
#   FileSystemResizePending   True     # Waiting for filesystem resize
#   Resizing                  True     # Backend resize in progress
```

**Important**: You can only **increase** PVC size. Shrinking is not supported!

> **Stop and think**: A PVC was created with a StorageClass that has `allowVolumeExpansion: false`. The database is running out of space. Can you change the StorageClass to `allowVolumeExpansion: true` and then expand the PVC? Or do you need to recreate the PVC? What would your recovery strategy be?

---

## Part 6: StorageClass Parameters

### 6.1 Parameter Reference

Parameters are provisioner-specific. Common examples:

**AWS EBS (CSI)**:
```yaml
parameters:
  type: gp3                    # gp2, gp3, io1, io2, st1, sc1
  iopsPerGB: "50"              # For gp3/io1/io2
  throughput: "250"            # For gp3 (MiB/s)
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:..."
  fsType: ext4                 # ext4, xfs
```

**GCP PD (CSI)**:
```yaml
parameters:
  type: pd-ssd                 # pd-standard, pd-ssd, pd-balanced
  replication-type: none       # none, regional-pd
  disk-encryption-kms-key: "projects/..."
  fsType: ext4
```

**Azure Disk (CSI)**:
```yaml
parameters:
  storageaccounttype: Premium_LRS   # Standard_LRS, Premium_LRS, StandardSSD_LRS
  kind: Managed                      # Managed, Dedicated, Shared
  cachingMode: ReadOnly
  fsType: ext4
```

### 6.2 Mount Options

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: with-mount-options
provisioner: kubernetes.io/aws-ebs
mountOptions:
  - debug
  - noatime
  - nodiratime
parameters:
  type: gp3
  fsType: ext4
```

---

## Part 7: Troubleshooting Provisioning Failures

When dynamic provisioning fails, the PVC remains in `Pending` state. To find the root cause:

1. **Check PVC Events**: `kubectl describe pvc <pvc-name>`. Look for `FailedProvisioning` events from the volume controller.
2. **Check Provisioner Pod Logs**: If the PVC event lacks detail (e.g., a cloud provider API error like IAM denied or quota exceeded), check the logs of the provisioner pod itself (often running in `kube-system` for CSI drivers).
   ```bash
   # Example for AWS EBS CSI driver
   kubectl logs -n kube-system deploy/ebs-csi-controller -c csi-provisioner
   ```
3. **Verify StorageClass**: Ensure the `provisioner` string matches exactly and all `parameters` are valid for the backend.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Multiple default StorageClasses | Uses most recently created default (causes confusion) | Only one should be default |
| Wrong provisioner for platform | PVC stays Pending forever | Use correct provisioner for your cloud |
| Immediate mode with zonal storage | Pods can't mount volumes | Use WaitForFirstConsumer |
| Forgetting allowVolumeExpansion | Can't resize PVCs later | Always set true unless intentional |
| Wrong parameters for provisioner | Provisioning fails | Check provisioner documentation |
| Trying to shrink PVC | Not supported | Only expansion works |

> **Pause and predict**: Your cluster has two StorageClasses both annotated with `storageclass.kubernetes.io/is-default-class: "true"`. A developer creates a PVC without specifying a storageClassName. What happens? Which StorageClass is used?

---

## Quiz

### Q1: Unexpected Dynamic Provisioning
A developer creates a PVC in a cluster that has a default StorageClass called `gp3-standard`. The developer intended to use a manually created PV, so they created the PVC without specifying `storageClassName`. Instead of binding to the manual PV, a new 10Gi EBS volume appears in AWS. The developer is confused and asks why Kubernetes ignored the pre-created PV. What happened, and how should the PVC be configured to bind to the manual PV instead?

<details>
<summary>Answer</summary>

When `storageClassName` is omitted from a PVC, Kubernetes uses the **default StorageClass** (`gp3-standard`), which triggers dynamic provisioning -- it creates a brand new PV via the EBS CSI driver instead of looking for existing manual PVs. To bind to a manually created PV, the developer must explicitly set `storageClassName: ""` (empty string) on the PVC. This tells Kubernetes to skip dynamic provisioning entirely and only look for PVs that also have no StorageClass. The manual PV must also have `storageClassName: ""` for the match to work. This is one of the most common misunderstandings about StorageClasses.

</details>

### Q2: Cross-Zone Mount Failure
A team in a multi-AZ AWS cluster uses a StorageClass with `volumeBindingMode: Immediate`. A developer creates a PVC, and a PV backed by an EBS volume is provisioned in `us-east-1a`. Later, the scheduler places the pod on a node in `us-east-1c`. The pod is stuck in `ContainerCreating` with an attach error. What caused the mismatch, what binding mode should have been used, and why does this problem not affect NFS-backed StorageClasses?

<details>
<summary>Answer</summary>

With `Immediate` binding mode, the PV is provisioned as soon as the PVC is created, **before** the scheduler decides where to place the pod. EBS volumes are zone-specific -- a volume in `us-east-1a` cannot be attached to a node in `us-east-1c`. The fix is to use `volumeBindingMode: WaitForFirstConsumer`, which delays provisioning until the pod is scheduled. The provisioner then creates the EBS volume in the same AZ as the scheduled node. NFS is not affected because NFS is **network storage** accessible from any node in any zone -- it has no zone affinity, so Immediate binding works fine.

</details>

### Q3: Disk Full Emergency
A production database is running out of disk space. The PVC uses a StorageClass with `allowVolumeExpansion: true`. The admin patches the PVC to increase from 50Gi to 100Gi. After 10 minutes, `kubectl get pvc` still shows 50Gi capacity, but `kubectl describe pvc` shows a condition `FileSystemResizePending`. The admin panics. Is something broken? What needs to happen next?

<details>
<summary>Answer</summary>

Nothing is broken -- this is the **expected two-phase expansion process**. Phase 1 (backend resize) already completed: the underlying cloud disk was resized to 100Gi. Phase 2 (filesystem resize) is pending because the filesystem inside the volume needs to be grown, which for many storage backends requires the volume to be mounted by a pod. If the pod is running, the kubelet will expand the filesystem on the next mount. If the pod is not running, you may need to start a pod that mounts the PVC. After the filesystem resize completes, the `FileSystemResizePending` condition clears and `kubectl get pvc` will show 100Gi. Some CSI drivers support online expansion (no pod restart needed), while others require a pod restart.

</details>

### Q4: Multiple Defaults Chaos
An admin accidentally marks two StorageClasses as default: `gp3-fast` and `standard-hdd`. A developer creates a PVC without specifying a storageClassName. What happens, and how should the admin fix this?

<details>
<summary>Answer</summary>

With **multiple default StorageClasses**, Kubernetes uses the **most recently created** default StorageClass. While this resolves the tie, it often causes confusion because developers might expect the older default to be used. The Kubernetes documentation explicitly states only one StorageClass should be marked as default. The admin should fix this by removing the default annotation from one of the StorageClasses: `kubectl patch sc standard-hdd -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'`. Best practice is to verify with `kubectl get sc` that exactly one StorageClass shows `(default)`.

</details>

### Q5: StorageClass Immutability Problem
After creating a StorageClass with `reclaimPolicy: Delete`, the admin realizes it should be `Retain` for production use. Existing PVCs have already provisioned PVs using this StorageClass. Can the admin change the reclaimPolicy on the StorageClass? What happens to the already-provisioned PVs?

<details>
<summary>Answer</summary>

StorageClasses are **immutable** once created -- you cannot change fields like `reclaimPolicy` or `parameters`. The admin must delete and recreate the StorageClass with the corrected policy. However, **already-provisioned PVs keep their original reclaim policy** -- changing the StorageClass does not retroactively update existing PVs. To protect existing production data, the admin should manually patch each PV's reclaim policy: `kubectl patch pv <pv-name> -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'`. New PVCs will use the recreated StorageClass with the correct Retain policy, but every existing PV must be patched individually.

</details>

### Q6: Dev vs Production StorageClass Design
You are designing StorageClasses for a cluster used by both dev and production teams. Dev needs cheap, ephemeral storage. Production needs encrypted, high-IOPS storage with data protection. Design the two StorageClasses and explain your choice of reclaimPolicy, volumeBindingMode, and whether to enable volume expansion for each.

<details>
<summary>Answer</summary>

For **dev**: Use `reclaimPolicy: Delete` (auto-cleanup when PVCs are deleted, no orphaned volumes), `volumeBindingMode: WaitForFirstConsumer` (avoid zone mismatch), `allowVolumeExpansion: true` (devs may need to grow storage during experimentation), and cheap storage parameters (e.g., `type: gp3` with default IOPS). For **production**: Use `reclaimPolicy: Retain` (protect data even if PVC is accidentally deleted), `volumeBindingMode: WaitForFirstConsumer` (same zone rationale), `allowVolumeExpansion: true` (databases grow over time), and add `encrypted: "true"` plus a KMS key in parameters for encryption at rest. The Delete policy for dev prevents storage cost leaks from forgotten PVCs, while Retain for production ensures a human must explicitly approve data deletion.

</details>

---

## Hands-On Exercise: Dynamic Provisioning

### Scenario
Set up a StorageClass and verify dynamic provisioning works correctly.

### Prerequisites
You need a cluster with a working storage provisioner. Kind and minikube have built-in provisioners.

### Task 1: Check Existing StorageClasses

```bash
# See what's available
k get sc

# Check if there's a default
k get sc -o custom-columns='NAME:.metadata.name,PROVISIONER:.provisioner,DEFAULT:.metadata.annotations.storageclass\.kubernetes\.io/is-default-class'
```

### Task 2: Create a StorageClass

```bash
cat <<EOF | k apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: rancher.io/local-path    # For kind; change for your cluster
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
```

### Task 3: Create PVC Using the StorageClass

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: fast
EOF

# Check status - should be Pending (waiting for consumer)
k get pvc dynamic-pvc
```

### Task 4: Create Pod to Trigger Provisioning

```bash
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: dynamic-pod
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Dynamically provisioned!" > /data/message; sleep 3600']
    volumeMounts:
    - name: storage
      mountPath: /data
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: dynamic-pvc
EOF
```

### Task 5: Verify Dynamic Provisioning

```bash
# Wait for pod to trigger provisioning and become ready
k wait --for=condition=Ready pod/dynamic-pod --timeout=60s

# PVC should now be Bound
k get pvc dynamic-pvc
# STATUS: Bound

# A PV was automatically created
k get pv
# Should see a dynamically named PV like pvc-xxxxx

# Check the PV details accurately
PV_NAME=$(k get pvc dynamic-pvc -o jsonpath='{.spec.volumeName}')
k get pv $PV_NAME -o jsonpath='{.spec.storageClassName}'
# Should show: fast

# Verify pod can read the dynamically provisioned storage
k exec dynamic-pod -- cat /data/message
```

### Task 6: Test Default StorageClass (Optional)

```bash
# Make our StorageClass the default
k patch sc fast -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "true"}}}'

# Create PVC without storageClassName
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: default-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  # No storageClassName - uses default!
EOF

# Check it uses the default class
k get pvc default-pvc -o jsonpath='{.spec.storageClassName}'
# Should show: fast
```

### Success Criteria
- [ ] StorageClass created successfully
- [ ] PVC stays Pending until pod created (WaitForFirstConsumer)
- [ ] PV automatically created when pod scheduled
- [ ] Pod can write to dynamically provisioned storage
- [ ] Understand the link between SC → PVC → PV

### Cleanup

```bash
k delete pod dynamic-pod
k delete pvc dynamic-pvc default-pvc
k delete sc fast
```

---

## Practice Drills

### Drill 1: List StorageClasses (1 min)
```bash
# Task: List all StorageClasses and identify the default
k get sc
```

### Drill 2: Create Basic StorageClass (2 min)
```bash
# Task: Create StorageClass "slow" with provisioner rancher.io/local-path
# reclaimPolicy: Retain
```

### Drill 3: Set Default StorageClass (1 min)
```bash
# Task: Make StorageClass "standard" the default
# Use annotation: storageclass.kubernetes.io/is-default-class: "true"
```

### Drill 4: PVC with Specific StorageClass (2 min)
```bash
# Task: Create PVC "data-pvc" requesting 5Gi with StorageClass "fast"
```

### Drill 5: PVC Without Dynamic Provisioning (2 min)
```bash
# Task: Create PVC that won't use any StorageClass
# Hint: storageClassName: ""
```

### Drill 6: Check Why PVC is Pending (2 min)
```bash
# Task: Diagnose why a PVC is stuck in Pending
k describe pvc <name>
# Check Events section for errors
```

### Drill 7: Enable Volume Expansion (2 min)
```bash
# Task: Create StorageClass with volume expansion enabled
# Key field: allowVolumeExpansion: true
```

### Drill 8: Verify Binding Mode (1 min)
```bash
# Task: Check the volumeBindingMode of StorageClass "standard"
k get sc standard -o jsonpath='{.volumeBindingMode}'
```

---

## Next Module

Continue to [Module 4.4: Volume Snapshots & Cloning](../module-4.4-snapshots/) to learn about backup and data protection features.

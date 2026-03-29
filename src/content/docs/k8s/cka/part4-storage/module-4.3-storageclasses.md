---
title: "Module 4.3: StorageClasses & Dynamic Provisioning"
slug: k8s/cka/part4-storage/module-4.3-storageclasses
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Automation of storage provisioning
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 4.2 (PV & PVC), Module 1.2 (CSI)

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

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Multiple default StorageClasses | Unpredictable behavior | Only one should be default |
| Wrong provisioner for platform | PVC stays Pending forever | Use correct provisioner for your cloud |
| Immediate mode with zonal storage | Pods can't mount volumes | Use WaitForFirstConsumer |
| Forgetting allowVolumeExpansion | Can't resize PVCs later | Always set true unless intentional |
| Wrong parameters for provisioner | Provisioning fails | Check provisioner documentation |
| Trying to shrink PVC | Not supported | Only expansion works |

---

## Quiz

### Q1: Default StorageClass
What happens when you create a PVC without specifying storageClassName in a cluster with a default StorageClass?

<details>
<summary>Answer</summary>

The PVC automatically uses the **default StorageClass** and triggers dynamic provisioning. A new PV will be created automatically by the provisioner.

</details>

### Q2: Opt-Out Dynamic Provisioning
How do you create a PVC that explicitly doesn't use dynamic provisioning?

<details>
<summary>Answer</summary>

Set `storageClassName: ""` (empty string) in the PVC spec. This prevents any StorageClass from being used, including the default, and the PVC will only bind to manually created PVs.

</details>

### Q3: WaitForFirstConsumer
Why is WaitForFirstConsumer important for cloud storage like AWS EBS?

<details>
<summary>Answer</summary>

EBS volumes are **zone-specific**. With Immediate binding, the volume might be provisioned in a different zone than where the pod gets scheduled, causing mount failures. WaitForFirstConsumer delays provisioning until after pod scheduling, ensuring the volume is created in the same zone as the pod.

</details>

### Q4: Volume Expansion
A PVC is using a StorageClass with `allowVolumeExpansion: false`. Can you expand it?

<details>
<summary>Answer</summary>

**No**. Volume expansion must be enabled on the StorageClass before the PVC can be expanded. You cannot change this setting after PVC creation (unless you recreate the StorageClass and PVC).

</details>

### Q5: Identifying Default
How do you check which StorageClass is the default?

<details>
<summary>Answer</summary>

```bash
k get sc
```
The default StorageClass will show `(default)` next to its name. Or check the annotation:
```bash
k get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

</details>

### Q6: Reclaim Policy Difference
What's the practical difference between Delete and Retain reclaimPolicy in StorageClasses?

<details>
<summary>Answer</summary>

- **Delete**: When PVC is deleted, the dynamically provisioned PV and underlying storage are automatically deleted. Good for dev/test.
- **Retain**: When PVC is deleted, the PV becomes "Released" but storage is kept. Admin must manually clean up. Good for production data.

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
# PVC should now be Bound
k get pvc dynamic-pvc
# STATUS: Bound

# A PV was automatically created
k get pv
# Should see a dynamically named PV like pvc-xxxxx

# Check the PV details
k get pv -o jsonpath='{.items[0].spec.storageClassName}'
# Should show: fast

# Verify pod is running
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

---
title: "Module 2.3: Storage Orchestration"
slug: k8s/kcna/part2-container-orchestration/module-2.3-storage
sidebar:
  order: 4
---
> **Complexity**: `[MEDIUM]` - Storage concepts
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 2.2 (Scaling)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the relationship between Volumes, PersistentVolumes, PersistentVolumeClaims, and StorageClasses
2. **Compare** access modes (ReadWriteOnce, ReadOnlyMany, ReadWriteMany) and their use cases
3. **Identify** when to use ephemeral vs. persistent storage for different workload types
4. **Evaluate** CSI drivers and their role in providing pluggable storage backends

---

## Why This Module Matters

Containers are ephemeral—when they restart, data is lost. Kubernetes provides storage abstractions that let stateful applications persist data across Pod restarts and rescheduling. KCNA tests your understanding of how Kubernetes manages storage.

---

## The Storage Problem

```
┌─────────────────────────────────────────────────────────────┐
│              WHY STORAGE IS NEEDED                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Without persistent storage:                               │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1. Database Pod writes data                               │
│     [Pod] → writes → [container filesystem]               │
│                                                             │
│  2. Pod crashes or gets rescheduled                        │
│     [Pod] 💥 → deleted                                     │
│                                                             │
│  3. New Pod starts                                         │
│     [New Pod] → empty filesystem! Data lost!              │
│                                                             │
│  With persistent storage:                                  │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1. Database Pod writes to volume                          │
│     [Pod] → writes → [Persistent Volume]                  │
│                                                             │
│  2. Pod crashes or gets rescheduled                        │
│     [Pod] 💥 → [Persistent Volume] still exists!         │
│                                                             │
│  3. New Pod starts and attaches to same volume            │
│     [New Pod] → reads → [Persistent Volume] Data safe!    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Storage Concepts Overview

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES STORAGE MODEL                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Three key resources:                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PersistentVolume (PV)                              │   │
│  │  • Actual storage resource                          │   │
│  │  • Provisioned by admin OR dynamically             │   │
│  │  • Cluster-wide resource                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↑                                   │
│                         │ binds to                         │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PersistentVolumeClaim (PVC)                        │   │
│  │  • Request for storage                              │   │
│  │  • Created by users/applications                    │   │
│  │  • Namespace-scoped resource                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↑                                   │
│                         │ used by                          │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Pod                                                │   │
│  │  • Mounts PVC as volume                            │   │
│  │  • Reads/writes to storage                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## PersistentVolume (PV)

A **PersistentVolume** is a piece of storage in the cluster:

```
┌─────────────────────────────────────────────────────────────┐
│              PERSISTENTVOLUME                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Key attributes:                                           │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  capacity:                                                 │
│    storage: 10Gi          # How much storage              │
│                                                             │
│  accessModes:                                              │
│  - ReadWriteOnce          # How it can be accessed        │
│                                                             │
│  persistentVolumeReclaimPolicy: Retain                    │
│                            # What happens when released   │
│                                                             │
│  storageClassName: fast   # Class of storage              │
│                                                             │
│  Access Modes:                                             │
│  ─────────────────────────────────────────────────────────  │
│  • ReadWriteOnce (RWO): One node can mount read-write     │
│  • ReadOnlyMany (ROX): Many nodes can mount read-only     │
│  • ReadWriteMany (RWX): Many nodes can mount read-write   │
│                                                             │
│  Reclaim Policies:                                         │
│  ─────────────────────────────────────────────────────────  │
│  • Retain: Keep data after PVC deleted (manual cleanup)   │
│  • Delete: Delete storage when PVC deleted               │
│  • Recycle: (Deprecated) Basic scrub and reuse           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## PersistentVolumeClaim (PVC)

A **PersistentVolumeClaim** is a request for storage:

```
┌─────────────────────────────────────────────────────────────┐
│              PERSISTENTVOLUMECLAIM                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User creates PVC:                                         │
│  ─────────────────────────────────────────────────────────  │
│  "I need 5GB of fast storage with ReadWriteOnce access"   │
│                                                             │
│  apiVersion: v1                                            │
│  kind: PersistentVolumeClaim                              │
│  metadata:                                                 │
│    name: my-data                                          │
│  spec:                                                     │
│    accessModes:                                            │
│      - ReadWriteOnce                                      │
│    resources:                                              │
│      requests:                                             │
│        storage: 5Gi                                       │
│    storageClassName: fast                                 │
│                                                             │
│  Kubernetes finds matching PV:                            │
│  ─────────────────────────────────────────────────────────  │
│  ┌───────────┐                     ┌───────────┐          │
│  │   PVC     │                     │    PV     │          │
│  │ 5Gi       │ ────── binds ─────→ │ 10Gi      │          │
│  │ RWO       │                     │ RWO       │          │
│  │ fast      │                     │ fast      │          │
│  └───────────┘                     └───────────┘          │
│                                                             │
│  PVC gets 10Gi (smallest PV that satisfies request)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## StorageClass

A **StorageClass** enables dynamic provisioning:

```
┌─────────────────────────────────────────────────────────────┐
│              STORAGECLASS                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Without StorageClass (Static Provisioning):              │
│  ─────────────────────────────────────────────────────────  │
│  1. Admin creates PV manually                              │
│  2. User creates PVC                                       │
│  3. PVC binds to pre-existing PV                          │
│                                                             │
│  With StorageClass (Dynamic Provisioning):                │
│  ─────────────────────────────────────────────────────────  │
│  1. Admin creates StorageClass                            │
│  2. User creates PVC referencing StorageClass             │
│  3. PV is automatically created!                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  StorageClass: fast                                 │   │
│  │  provisioner: kubernetes.io/aws-ebs               │   │
│  │  parameters:                                        │   │
│  │    type: gp3                                        │   │
│  │    iopsPerGB: "10"                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                 │
│           │ PVC requests "fast" StorageClass              │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Provisioner automatically creates:                 │   │
│  │  • AWS EBS volume                                   │   │
│  │  • PersistentVolume                                │   │
│  │  • Binds PVC to new PV                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Common provisioners:                                      │
│  • kubernetes.io/aws-ebs (AWS)                           │
│  • kubernetes.io/gce-pd (GCP)                            │
│  • kubernetes.io/azure-disk (Azure)                      │
│  • rancher.io/local-path (local)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Volume Types

Kubernetes supports many volume types:

| Type | Description | Persistent |
|------|-------------|------------|
| **emptyDir** | Temporary directory, deleted with Pod | No |
| **hostPath** | Mount from node's filesystem | Node-specific |
| **persistentVolumeClaim** | Use PVC for storage | Yes |
| **configMap** | Mount ConfigMap as files | No |
| **secret** | Mount Secret as files | No |
| **nfs** | Network File System | Yes |
| **awsElasticBlockStore** | AWS EBS volume | Yes |
| **gcePersistentDisk** | GCP persistent disk | Yes |
| **azureDisk** | Azure managed disk | Yes |

---

## Static vs Dynamic Provisioning

```
┌─────────────────────────────────────────────────────────────┐
│              STATIC vs DYNAMIC                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STATIC PROVISIONING:                                      │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Admin                    User                             │
│    │                        │                               │
│    │ 1. Create PV           │                               │
│    ▼                        │                               │
│  [PV: 100Gi]               │                               │
│                             │ 2. Create PVC                 │
│                             ▼                               │
│  [PV: 100Gi] ←── binds ── [PVC: 50Gi]                     │
│                                                             │
│  Pros: Full control, pre-allocate storage                 │
│  Cons: Admin must create PVs in advance                   │
│                                                             │
│  DYNAMIC PROVISIONING:                                     │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Admin creates once:       User                            │
│  [StorageClass: fast]        │                             │
│                              │ 1. Create PVC               │
│                              │    storageClassName: fast   │
│                              ▼                              │
│  Provisioner ───────────→ [PV: 50Gi] ── binds ── [PVC]   │
│  automatically                                              │
│  creates                                                    │
│                                                             │
│  Pros: Self-service, on-demand, efficient                 │
│  Cons: Requires cloud provider or storage system          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## PV Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│              PV LIFECYCLE                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Available ──→ Bound ──→ Released ──→ (Reclaim Policy)    │
│                                                             │
│  AVAILABLE:                                                │
│  • PV exists, not claimed by any PVC                      │
│  • Ready to be bound                                       │
│                                                             │
│  BOUND:                                                    │
│  • PV is claimed by a PVC                                 │
│  • Pod can use it                                         │
│  • One-to-one relationship                                │
│                                                             │
│  RELEASED:                                                 │
│  • PVC deleted, but PV still has data                     │
│  • Not available for new claims                           │
│                                                             │
│  After release (based on reclaimPolicy):                  │
│  • Retain: Stays Released, manual cleanup needed          │
│  • Delete: PV and underlying storage deleted              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Using Storage in Pods

```yaml
# Pod using a PVC
apiVersion: v1
kind: Pod
metadata:
  name: database
spec:
  containers:
  - name: mysql
    image: mysql:8.0
    volumeMounts:
    - name: data
      mountPath: /var/lib/mysql    # Where to mount in container
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: mysql-pvc         # Reference to PVC
```

---

## Did You Know?

- **Volume binding** - Kubernetes only binds PV to PVC when a Pod actually needs it (WaitForFirstConsumer mode). This ensures storage is provisioned in the same zone as the Pod.

- **StorageClass is cluster-scoped** - Unlike PVCs (namespace-scoped), StorageClasses are available to all namespaces.

- **emptyDir survives container restarts** - Data in emptyDir is only lost when the Pod is deleted, not when a container restarts.

- **CSI is the standard** - Container Storage Interface (CSI) is the modern way to integrate storage systems with Kubernetes. Legacy in-tree volume plugins are being migrated to CSI.

---

## Common Mistakes

| Mistake | Why It Hurts | Correct Understanding |
|---------|--------------|----------------------|
| Using emptyDir for permanent data | Data lost when Pod deleted | Use PVC for persistent data |
| Expecting RWX everywhere | Not all storage supports it | Check storage capabilities |
| Forgetting reclaim policy | Might delete data accidentally | Set Retain for important data |
| Static provisioning at scale | Too much admin work | Use dynamic provisioning |

---

## Quiz

1. **What's the difference between PV and PVC?**
   <details>
   <summary>Answer</summary>
   PV (PersistentVolume) is the actual storage resource provisioned in the cluster. PVC (PersistentVolumeClaim) is a request for storage by a user/application. PVC binds to a matching PV to get actual storage.
   </details>

2. **What does ReadWriteOnce (RWO) mean?**
   <details>
   <summary>Answer</summary>
   The volume can be mounted as read-write by a single node. Multiple Pods on the same node can share it, but Pods on different nodes cannot.
   </details>

3. **What is dynamic provisioning?**
   <details>
   <summary>Answer</summary>
   When a PVC references a StorageClass, Kubernetes automatically creates a PV to satisfy the claim. The admin doesn't need to pre-create PVs—they're created on-demand.
   </details>

4. **What happens to data when a PVC is deleted with Retain policy?**
   <details>
   <summary>Answer</summary>
   The PV enters "Released" state but the data is preserved. An admin must manually clean up the PV and data. This protects against accidental data loss.
   </details>

5. **Why use StorageClass instead of pre-creating PVs?**
   <details>
   <summary>Answer</summary>
   StorageClass enables self-service storage: users can create PVCs without admin intervention. It's more efficient (no wasted pre-allocated storage) and scales better.
   </details>

---

## Summary

**Storage resources**:
- **PersistentVolume (PV)**: Actual storage
- **PersistentVolumeClaim (PVC)**: Request for storage
- **StorageClass**: Enables dynamic provisioning

**Access modes**:
- **RWO**: One node read-write
- **ROX**: Many nodes read-only
- **RWX**: Many nodes read-write

**Provisioning**:
- **Static**: Admin creates PVs manually
- **Dynamic**: PVs created automatically via StorageClass

**Reclaim policies**:
- **Retain**: Keep data after PVC deletion
- **Delete**: Remove storage when PVC deleted

---

## Next Module

[Module 2.4: Configuration](../module-2.4-configuration/) - Managing application configuration with ConfigMaps and Secrets.

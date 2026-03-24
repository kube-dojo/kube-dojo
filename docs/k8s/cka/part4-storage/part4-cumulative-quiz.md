# Part 4 Cumulative Quiz: Storage

> **Time Limit**: 30 minutes
>
> **Passing Score**: 80% (20/25 questions)
>
> **Format**: Multiple choice and short answer

This quiz covers all modules from Part 4:
- Module 4.1: Volumes
- Module 4.2: PersistentVolumes & PersistentVolumeClaims
- Module 4.3: StorageClasses & Dynamic Provisioning
- Module 4.4: Volume Snapshots & Cloning
- Module 4.5: Storage Troubleshooting

---

## Section 1: Volumes (5 questions)

### Q1: emptyDir Lifetime
When is an emptyDir volume deleted?

<details>
<summary>Answer</summary>

When the **pod is removed from the node** (deleted, evicted, or node failure). emptyDir survives container restarts but not pod deletion. The data is tied to the pod's lifecycle, not the container's.

</details>

### Q2: Memory-Backed emptyDir
What configuration creates an emptyDir backed by RAM instead of disk?

<details>
<summary>Answer</summary>

```yaml
volumes:
- name: cache
  emptyDir:
    medium: Memory
    sizeLimit: 100Mi    # Important to set limit!
```

Memory-backed emptyDir counts against the container's memory limit.

</details>

### Q3: hostPath Security
Why is hostPath considered a security risk in production?

<details>
<summary>Answer</summary>

hostPath mounts the node's filesystem into the pod, which can:
- Allow container escape to the node
- Expose sensitive node files (credentials, configs)
- Enable writing malicious files to the node
- Bypass container isolation

Most Pod Security Policies/Standards block hostPath.

</details>

### Q4: Projected Volume Sources
Name the four types of sources that can be combined in a projected volume.

<details>
<summary>Answer</summary>

1. **configMap** - ConfigMap data
2. **secret** - Secret data
3. **downwardAPI** - Pod metadata and resource info
4. **serviceAccountToken** - Projected service account tokens

</details>

### Q5: subPath Limitation
What's the key limitation of using subPath when mounting ConfigMaps or Secrets?

<details>
<summary>Answer</summary>

**subPath mounts don't auto-update** when the source ConfigMap or Secret changes. Regular volume mounts receive updates automatically (within ~1 minute), but subPath mounts require a pod restart to see changes.

</details>

---

## Section 2: PersistentVolumes & PVCs (6 questions)

### Q6: PV Scope
Are PersistentVolumes namespaced or cluster-scoped?

<details>
<summary>Answer</summary>

**Cluster-scoped**. PersistentVolumes are available cluster-wide and don't belong to any namespace. PersistentVolumeClaims are namespaced.

</details>

### Q7: Access Mode Abbreviations
What do RWO, ROX, and RWX stand for?

<details>
<summary>Answer</summary>

- **RWO** - ReadWriteOnce: Single node can mount read-write
- **ROX** - ReadOnlyMany: Multiple nodes can mount read-only
- **RWX** - ReadWriteMany: Multiple nodes can mount read-write

</details>

### Q8: Reclaim Policies
What happens to a PV with `reclaimPolicy: Retain` when its PVC is deleted?

<details>
<summary>Answer</summary>

The PV enters **Released** state. The data is preserved and the PV is not automatically available for new claims. An administrator must:
1. Back up data if needed
2. Clean up the underlying storage
3. Remove the claimRef to make PV Available again (or delete/recreate PV)

</details>

### Q9: PV Binding Size
A PVC requests 20Gi. Available PVs are 10Gi, 50Gi, and 100Gi. Which binds?

<details>
<summary>Answer</summary>

**50Gi**. Kubernetes selects the smallest PV that satisfies the request. 10Gi is too small. Between 50Gi and 100Gi, 50Gi minimizes wasted capacity.

</details>

### Q10: Local PV Requirement
What special configuration does a local PersistentVolume require?

<details>
<summary>Answer</summary>

**nodeAffinity**. Local PVs must specify which node has the storage:

```yaml
nodeAffinity:
  required:
    nodeSelectorTerms:
    - matchExpressions:
      - key: kubernetes.io/hostname
        operator: In
        values:
        - specific-node-name
```

</details>

### Q11: Making Released PV Available
How do you make a Released PV available for new claims again?

<details>
<summary>Answer</summary>

Remove the claimRef:

```bash
k patch pv <pv-name> -p '{"spec":{"claimRef": null}}'
```

This clears the binding and changes status from Released to Available.

</details>

---

## Section 3: StorageClasses (5 questions)

### Q12: Default StorageClass
How do you mark a StorageClass as the cluster default?

<details>
<summary>Answer</summary>

Add the annotation:

```yaml
metadata:
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
```

Or patch existing:
```bash
k patch sc <name> -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "true"}}}'
```

</details>

### Q13: Opt-Out Dynamic Provisioning
How do you create a PVC that doesn't use any StorageClass (no dynamic provisioning)?

<details>
<summary>Answer</summary>

Set `storageClassName: ""` (empty string):

```yaml
spec:
  storageClassName: ""
```

This explicitly disables dynamic provisioning and requires manual PV binding.

</details>

### Q14: WaitForFirstConsumer
Why is `volumeBindingMode: WaitForFirstConsumer` important for cloud storage?

<details>
<summary>Answer</summary>

Cloud storage like EBS, GCE PD, and Azure Disk is **zone-specific**. With Immediate binding, the volume might provision in a different zone than where the pod gets scheduled, causing mount failures.

WaitForFirstConsumer delays provisioning until after pod scheduling, ensuring the volume is created in the same zone as the pod.

</details>

### Q15: Volume Expansion
What StorageClass field must be set to allow PVC resizing?

<details>
<summary>Answer</summary>

```yaml
allowVolumeExpansion: true
```

Without this, PVCs cannot be expanded after creation.

</details>

### Q16: PVC Without StorageClassName
What happens when you create a PVC without specifying storageClassName?

<details>
<summary>Answer</summary>

If a **default StorageClass** exists in the cluster, it will be used and dynamic provisioning will occur. If no default exists, the PVC will stay Pending until a matching PV is manually created.

</details>

---

## Section 4: Snapshots & Cloning (5 questions)

### Q17: Snapshot Resources
What are the three main snapshot-related resources?

<details>
<summary>Answer</summary>

1. **VolumeSnapshotClass** - Defines how snapshots are created (cluster-scoped)
2. **VolumeSnapshot** - Request to snapshot a PVC (namespaced)
3. **VolumeSnapshotContent** - Actual snapshot reference (cluster-scoped)

Similar pattern to StorageClass, PVC, and PV.

</details>

### Q18: Snapshot Prerequisites
What must be installed before you can use volume snapshots?

<details>
<summary>Answer</summary>

1. **Snapshot CRDs** - The custom resource definitions
2. **Snapshot controller** - Manages snapshot lifecycle
3. **CSI driver with snapshot support** - Actually creates snapshots

Legacy in-tree volume plugins don't support snapshots.

</details>

### Q19: Restore from Snapshot
What field in a PVC spec specifies it should be created from a snapshot?

<details>
<summary>Answer</summary>

The **dataSource** field:

```yaml
spec:
  dataSource:
    name: snapshot-name
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

</details>

### Q20: Clone vs Snapshot
What's the difference between cloning a PVC and restoring from a snapshot?

<details>
<summary>Answer</summary>

**Cloning** (`kind: PersistentVolumeClaim` in dataSource):
- Direct copy from PVC to new PVC
- No intermediate artifact
- One-step process

**Snapshot restore** (`kind: VolumeSnapshot` in dataSource):
- Two-step: create snapshot, then restore
- Snapshot persists and can be reused
- Point-in-time backup capability

</details>

### Q21: Clone Namespace Restriction
Can you clone a PVC from a different namespace?

<details>
<summary>Answer</summary>

**No**. PVC cloning requires source and destination to be in the **same namespace**. Cross-namespace cloning is not supported.

For cross-namespace data copying, use VolumeSnapshots (VolumeSnapshotContent is cluster-scoped).

</details>

---

## Section 5: Troubleshooting (4 questions)

### Q22: First Debug Step
A pod is stuck in ContainerCreating. What's the first command to run?

<details>
<summary>Answer</summary>

```bash
k describe pod <pod-name>
```

Check the Events section for volume-related errors like FailedMount, FailedAttach, or specific error messages about PVCs.

</details>

### Q23: PVC Pending Debug
A PVC is stuck in Pending. What command reveals why?

<details>
<summary>Answer</summary>

```bash
k describe pvc <pvc-name>
```

The Events section will show:
- "no persistent volumes available" - no matching PV
- "storageclass not found" - wrong SC name
- No events but StorageClass uses WaitForFirstConsumer - expected, create pod

</details>

### Q24: Multi-Attach Error
What does "Multi-Attach error" mean and how do you fix it?

<details>
<summary>Answer</summary>

The error means a **RWO volume is attached to multiple nodes**, typically from an old pod that didn't cleanly unmount.

Fix:
1. Delete the old pod using the volume
2. If stuck: `k delete pod <name> --force --grace-period=0`
3. Check VolumeAttachments: `k get volumeattachment`

</details>

### Q25: Permission Denied Fix
A pod mounts a volume but gets "permission denied" when writing. What's the likely fix?

<details>
<summary>Answer</summary>

Set the pod's securityContext:

```yaml
spec:
  securityContext:
    fsGroup: 1000        # Group ID for volume files
  containers:
  - name: app
    securityContext:
      runAsUser: 1000    # User ID in container
```

The fsGroup ensures the volume is accessible to the container's user.

</details>

---

## Scoring

Count your correct answers:

| Score | Result |
|-------|--------|
| 23-25 | Excellent! Ready for Part 5 |
| 20-22 | Good. Review missed topics, then proceed |
| 16-19 | Review the related modules before continuing |
| <16 | Re-study Part 4 modules |

---

## Review Resources

If you scored below 80%, review these modules:

- **Volume questions (Q1-Q5)**: [Module 4.1](module-4.1-volumes.md)
- **PV/PVC questions (Q6-Q11)**: [Module 4.2](module-4.2-pv-pvc.md)
- **StorageClass questions (Q12-Q16)**: [Module 4.3](module-4.3-storageclasses.md)
- **Snapshot questions (Q17-Q21)**: [Module 4.4](module-4.4-snapshots.md)
- **Troubleshooting questions (Q22-Q25)**: [Module 4.5](module-4.5-troubleshooting.md)

---

## Next Part

Proceed to [Part 5: Troubleshooting](../part5-troubleshooting/README.md) to learn systematic approaches to diagnosing and fixing Kubernetes cluster problems.

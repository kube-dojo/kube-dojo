# Module 4.5: Storage Troubleshooting

> **Complexity**: `[MEDIUM]` - Diagnosing and fixing storage issues
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Modules 4.1-4.4 (all previous storage modules)

---

## Why This Module Matters

Storage issues are among the most common problems in Kubernetes clusters. Pods stuck in ContainerCreating, PVCs that never bind, permission errors, and capacity problems can bring applications to a halt. The CKA exam heavily tests troubleshooting skills, and storage problems appear frequently. This module gives you a systematic approach to diagnose and fix storage issues.

> **The Detective Analogy**
>
> Troubleshooting storage is like being a detective. The pod won't start - that's the crime. Your tools are `kubectl describe`, `kubectl logs`, and `kubectl get events` - your magnifying glass, fingerprint kit, and witness interviews. You follow the evidence: Pod → PVC → PV → StorageClass → CSI driver. Each step reveals clues until you find the culprit.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Systematically troubleshoot storage issues
- Debug PVC binding problems
- Fix volume mount errors
- Diagnose CSI driver issues
- Resolve permissions and capacity problems

---

## Did You Know?

- **Most storage issues are misconfiguration**: Wrong StorageClass name, mismatched access modes, or missing labels cause 80% of problems
- **Events are your best friend**: `kubectl describe` shows recent events that often contain the exact error message
- **CSI drivers have their own logs**: When the usual commands don't help, check CSI controller and node logs

---

## Part 1: Troubleshooting Framework

### 1.1 The Storage Debug Path

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Storage Troubleshooting Path                      │
│                                                                      │
│   Pod Issue                                                          │
│       │                                                              │
│       ▼                                                              │
│   1. k describe pod <name>                                          │
│      └─► Check Events section                                       │
│      └─► Check volume mount errors                                  │
│          │                                                          │
│          ▼                                                          │
│   2. k get pvc <name>                                               │
│      └─► Is STATUS "Bound"?                                         │
│      └─► If "Pending", check Events                                 │
│          │                                                          │
│          ▼                                                          │
│   3. k get pv                                                       │
│      └─► Does matching PV exist?                                    │
│      └─► Is STATUS "Available" or "Bound"?                          │
│          │                                                          │
│          ▼                                                          │
│   4. k get sc <storageclass>                                        │
│      └─► Does StorageClass exist?                                   │
│      └─► Is provisioner correct?                                    │
│          │                                                          │
│          ▼                                                          │
│   5. Check CSI driver                                               │
│      └─► Is driver installed?                                       │
│      └─► Check driver pod logs                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Commands Reference

```bash
# Pod-level debugging
k describe pod <pod-name>
k get pod <pod-name> -o yaml
k logs <pod-name>

# PVC debugging
k get pvc
k describe pvc <pvc-name>
k get pvc <pvc-name> -o yaml

# PV debugging
k get pv
k describe pv <pv-name>
k get pv <pv-name> -o yaml

# StorageClass debugging
k get sc
k describe sc <sc-name>

# Events (often most useful!)
k get events --sort-by='.lastTimestamp'
k get events --field-selector involvedObject.name=<pvc-name>

# CSI debugging
k get pods -n kube-system | grep csi
k logs -n kube-system <csi-pod> -c <container>
```

---

## Part 2: PVC Binding Problems

### 2.1 PVC Stuck in Pending

**Symptoms**: PVC shows `STATUS: Pending`, never becomes Bound

```bash
k get pvc
# NAME     STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# my-pvc   Pending                                       fast-ssd
```

**Debug steps**:
```bash
# Step 1: Check events
k describe pvc my-pvc
# Look at Events section for errors
```

### 2.2 Common Pending Causes

**Cause 1: No matching PV exists (static provisioning)**
```
Events:
  Type     Reason              Message
  ----     ------              -------
  Normal   FailedBinding       no persistent volumes available for this claim
```

**Solution**: Create a PV that matches the PVC requirements:
```bash
# Check what PVC needs
k get pvc my-pvc -o yaml | grep -A5 spec:

# Create matching PV or fix PVC to match existing PV
```

**Cause 2: StorageClass doesn't exist**
```
Events:
  Type     Reason              Message
  ----     ------              -------
  Warning  ProvisioningFailed  storageclass.storage.k8s.io "fast-ssd" not found
```

**Solution**:
```bash
# List available StorageClasses
k get sc

# Fix PVC to use existing StorageClass
k patch pvc my-pvc -p '{"spec":{"storageClassName":"standard"}}'
# Note: You may need to delete and recreate PVC
```

**Cause 3: No CSI driver/provisioner**
```
Events:
  Type     Reason              Message
  ----     ------              -------
  Warning  ProvisioningFailed  failed to provision volume: no csi driver
```

**Solution**: Install the required CSI driver for your storage backend

**Cause 4: WaitForFirstConsumer mode**
```bash
k get pvc my-pvc
# STATUS: Pending (this is normal until pod uses it!)

k get sc fast-ssd -o jsonpath='{.volumeBindingMode}'
# WaitForFirstConsumer
```

**Solution**: This is expected behavior! Create a pod that uses the PVC, and it will bind.

### 2.3 Access Mode Mismatch

**Symptoms**: PVC won't bind even though PV exists

```bash
k get pv
# NAME   CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS
# pv-1   100Gi      RWO            Retain           Available

k get pvc
# NAME     STATUS    ACCESS MODES   STORAGECLASS
# my-pvc   Pending   RWX            manual
```

**Problem**: PVC requests RWX, PV only offers RWO

**Solution**:
```bash
# Option 1: Change PVC to match PV
k delete pvc my-pvc
# Recreate with RWO

# Option 2: Create new PV with RWX (if storage supports it)
```

### 2.4 StorageClass Mismatch

```bash
k get pv pv-1 -o jsonpath='{.spec.storageClassName}'
# manual

k get pvc my-pvc -o jsonpath='{.spec.storageClassName}'
# fast
```

**Problem**: PVC and PV have different storageClassName

**Solution**: Align storageClassName on both resources

---

## Part 3: Volume Mount Errors

### 3.1 Pod Stuck in ContainerCreating

**Symptoms**: Pod stays in ContainerCreating state

```bash
k get pods
# NAME     READY   STATUS              RESTARTS   AGE
# my-pod   0/1     ContainerCreating   0          5m
```

**Debug**:
```bash
k describe pod my-pod
# Look for volume-related errors in Events
```

### 3.2 Common Mount Errors

**Error 1: PVC not found**
```
Events:
  Warning  FailedMount  Unable to attach or mount volumes:
  persistentvolumeclaim "my-pvc" not found
```

**Solution**:
```bash
# Check PVC exists in same namespace
k get pvc my-pvc -n <namespace>

# Fix pod spec if PVC name is wrong
```

**Error 2: Volume already attached to another node**
```
Events:
  Warning  FailedAttachVolume  Multi-Attach error for volume "pvc-xxx":
  Volume is already attached to node "node-1"
```

**Cause**: RWO volume attached to another node (common during node failures)

**Solution**:
```bash
# Wait for old pod to terminate, or force delete
k delete pod <old-pod> --force --grace-period=0

# If using StatefulSet, might need to delete old PV attachment
k get volumeattachment
```

**Error 3: Permission denied**
```
Events:
  Warning  FailedMount  MountVolume.SetUp failed:
  mount failed: exit status 32, permission denied
```

**Solution**:
```yaml
# Add securityContext to pod
spec:
  securityContext:
    fsGroup: 1000        # Group ID for volume
  containers:
  - name: app
    securityContext:
      runAsUser: 1000    # User ID
```

**Error 4: hostPath doesn't exist**
```
Events:
  Warning  FailedMount  hostPath type check failed:
  path /data/myapp does not exist
```

**Solution**:
```yaml
# Use DirectoryOrCreate type
volumes:
- name: data
  hostPath:
    path: /data/myapp
    type: DirectoryOrCreate    # Instead of Directory
```

### 3.3 Mount Timeout

```
Events:
  Warning  FailedMount  Unable to attach or mount volumes:
  timeout expired waiting for volumes to attach
```

**Causes**:
- CSI driver not responding
- Storage backend unreachable
- Node issues

**Debug**:
```bash
# Check CSI driver pods
k get pods -n kube-system | grep csi

# Check CSI driver logs
k logs -n kube-system <csi-controller-pod> -c csi-provisioner

# Check node conditions
k describe node <node-name> | grep -A5 Conditions
```

---

## Part 4: Capacity Problems

### 4.1 Volume Full

**Symptoms**: Application errors about disk space

**Debug**:
```bash
# Check PVC capacity
k get pvc my-pvc
# CAPACITY: 10Gi

# Check actual usage in pod
k exec my-pod -- df -h /data
# Shows actual usage
```

**Solution 1: Expand PVC** (if StorageClass supports it)
```bash
# Check if expansion is allowed
k get sc <storageclass> -o jsonpath='{.allowVolumeExpansion}'
# true

# Expand PVC
k patch pvc my-pvc -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'

# Monitor expansion status
k describe pvc my-pvc | grep -A5 Conditions
```

**Solution 2: Clean up data**
```bash
k exec my-pod -- rm -rf /data/tmp/*
```

### 4.2 Insufficient Capacity

```
Events:
  Warning  ProvisioningFailed  insufficient capacity
```

**Causes**:
- Storage backend is full
- Quota exceeded
- Regional capacity limits (cloud)

**Debug**:
```bash
# Check ResourceQuota
k get resourcequota -n <namespace>

# Check LimitRange
k get limitrange -n <namespace>

# For cloud, check cloud console for capacity
```

---

## Part 5: CSI Driver Issues

### 5.1 CSI Driver Not Installed

**Symptoms**: PVC stuck pending, events mention CSI

```bash
k describe pvc my-pvc
# Events:
#   Warning  ProvisioningFailed  error getting CSI driver name
```

**Debug**:
```bash
# List CSI drivers
k get csidrivers

# Check if driver pods are running
k get pods -n kube-system | grep csi

# Check CSINode objects
k get csinode
```

### 5.2 CSI Driver Crashlooping

```bash
k get pods -n kube-system | grep csi
# NAME                          READY   STATUS             RESTARTS
# ebs-csi-controller-xxx        0/6     CrashLoopBackOff   5
```

**Debug**:
```bash
# Check logs
k logs -n kube-system ebs-csi-controller-xxx -c csi-provisioner
k logs -n kube-system ebs-csi-controller-xxx -c csi-attacher

# Common causes:
# - Missing cloud credentials
# - Wrong IAM permissions
# - Network connectivity issues
```

### 5.3 CSI Driver Permissions

For cloud storage, CSI drivers need appropriate permissions:

**AWS**: IAM role with EBS permissions
```bash
# Check service account
k get sa -n kube-system ebs-csi-controller-sa -o yaml
# Look for eks.amazonaws.com/role-arn annotation
```

**GCP**: Workload Identity or node service account
**Azure**: Managed Identity or service principal

---

## Part 6: Quick Reference: Error Messages

### 6.1 Error Message Cheatsheet

| Error Message | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `no persistent volumes available` | No matching PV for static provisioning | Create matching PV |
| `storageclass not found` | Wrong StorageClass name | Check `k get sc` |
| `waiting for first consumer` | WaitForFirstConsumer mode | Create pod using PVC |
| `Multi-Attach error` | RWO volume on multiple nodes | Delete old pod first |
| `permission denied` | Filesystem permissions | Set fsGroup/runAsUser |
| `path does not exist` | hostPath missing | Use DirectoryOrCreate |
| `timeout waiting for volumes` | CSI driver issue | Check CSI pods/logs |
| `insufficient capacity` | No space in storage backend | Expand or clean up |
| `volume is already attached` | Stale volume attachment | Delete VolumeAttachment |

### 6.2 Quick Debug Commands

```bash
# One-liner for common checks
echo "=== PVCs ===" && k get pvc && \
echo "=== PVs ===" && k get pv && \
echo "=== StorageClasses ===" && k get sc && \
echo "=== Recent Events ===" && k get events --sort-by='.lastTimestamp' | tail -20
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not checking Events | Missing the actual error message | Always `k describe` first |
| Ignoring namespace | PVC in different namespace than pod | Verify namespace matches |
| Forgetting WaitForFirstConsumer | Thinking PVC is broken when Pending | Check volumeBindingMode |
| Deleting PVC before pod | Pod can't unmount properly | Delete pod first |
| Not checking CSI logs | Generic errors hide real cause | Check CSI driver pods |
| Wrong YAML indentation | Volume spec invalid | Use `--dry-run=client -o yaml` |

---

## Quiz

### Q1: First Debug Step
A pod is stuck in ContainerCreating. What's the first command you should run?

<details>
<summary>Answer</summary>

```bash
k describe pod <pod-name>
```

This shows the Events section which typically contains the specific error message about why the pod can't start. Look for volume-related errors like FailedMount or FailedAttach.

</details>

### Q2: PVC Pending Analysis
A PVC is stuck in Pending status. How do you find out why?

<details>
<summary>Answer</summary>

```bash
k describe pvc <pvc-name>
```

Check the Events section for warnings like:
- "no persistent volumes available" - no matching PV
- "storageclass not found" - wrong SC name
- "waiting for first consumer" - expected with WaitForFirstConsumer

</details>

### Q3: Multi-Attach Error
You see "Multi-Attach error for volume". What does this mean and how do you fix it?

<details>
<summary>Answer</summary>

The error means a **RWO** (ReadWriteOnce) volume is already attached to another node, typically from an old pod that didn't cleanly unmount.

Fix:
1. Find and delete the old pod: `k get pods -o wide` to find pod using volume
2. If pod is stuck terminating: `k delete pod <name> --force --grace-period=0`
3. Check VolumeAttachment if needed: `k get volumeattachment`

</details>

### Q4: WaitForFirstConsumer
A PVC shows Pending but there are no error events. The StorageClass uses WaitForFirstConsumer. Is this a problem?

<details>
<summary>Answer</summary>

**No, this is expected behavior**. With WaitForFirstConsumer, the PVC stays Pending until a pod that uses it is scheduled. This is actually desirable for zonal storage to ensure the volume is created in the same zone as the pod.

To proceed, create a pod that references the PVC, and the PV will be provisioned when the pod is scheduled.

</details>

### Q5: Permission Denied
A volume mounts but the application gets "permission denied" when writing. What should you check?

<details>
<summary>Answer</summary>

Check the pod's security context:

```yaml
spec:
  securityContext:
    fsGroup: <gid>      # Group for volume ownership
  containers:
  - securityContext:
      runAsUser: <uid>   # User the container runs as
```

The fsGroup should match the GID that owns the volume's files, or the container user should have write permissions.

</details>

### Q6: Finding CSI Errors
Where do you look for CSI driver errors?

<details>
<summary>Answer</summary>

```bash
# Find CSI pods
k get pods -n kube-system | grep csi

# Check logs of CSI controller
k logs -n kube-system <csi-controller-pod> -c csi-provisioner
k logs -n kube-system <csi-controller-pod> -c csi-attacher

# Check logs of CSI node plugin
k logs -n kube-system <csi-node-pod> -c csi-driver
```

Also check `k get csidrivers` and `k get csinode` for driver registration status.

</details>

---

## Hands-On Exercise: Storage Troubleshooting Scenarios

### Setup

```bash
# Create namespace
k create ns storage-debug

# We'll create broken configurations and fix them
```

### Scenario 1: PVC Won't Bind (Wrong StorageClass)

```bash
# Create a PVC with wrong StorageClass
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: broken-pvc-1
  namespace: storage-debug
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: nonexistent-class
EOF

# Check status
k get pvc -n storage-debug broken-pvc-1

# Debug
k describe pvc -n storage-debug broken-pvc-1
# Look for: storageclass "nonexistent-class" not found

# Fix: List available StorageClasses and recreate PVC
k get sc
k delete pvc -n storage-debug broken-pvc-1

# Recreate with correct StorageClass (use your cluster's SC)
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: broken-pvc-1
  namespace: storage-debug
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard    # Use actual SC name
EOF
```

### Scenario 2: Pod Can't Mount (Wrong PVC Name)

```bash
# Create a valid PVC
cat <<EOF | k apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: correct-pvc
  namespace: storage-debug
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# Create pod with wrong PVC reference
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-1
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: wrong-pvc-name    # This doesn't exist!
EOF

# Check pod status
k get pod -n storage-debug broken-pod-1
# STATUS: ContainerCreating

# Debug
k describe pod -n storage-debug broken-pod-1
# Look for: persistentvolumeclaim "wrong-pvc-name" not found

# Fix
k delete pod -n storage-debug broken-pod-1

cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-1
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: correct-pvc    # Fixed!
EOF
```

### Scenario 3: hostPath Type Error

```bash
# Create pod with strict hostPath type
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-2
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    hostPath:
      path: /tmp/nonexistent-path-xyz
      type: Directory    # Fails if directory doesn't exist
EOF

# Debug
k describe pod -n storage-debug broken-pod-2
# May show: hostPath type check failed

# Fix: Use DirectoryOrCreate
k delete pod -n storage-debug broken-pod-2

cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod-2
  namespace: storage-debug
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sleep', '3600']
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    hostPath:
      path: /tmp/nonexistent-path-xyz
      type: DirectoryOrCreate    # Creates if missing
EOF
```

### Success Criteria
- [ ] Identified StorageClass error from events
- [ ] Fixed PVC to use correct StorageClass
- [ ] Identified wrong PVC name from pod events
- [ ] Fixed pod to reference correct PVC
- [ ] Understood hostPath type requirements

### Cleanup

```bash
k delete ns storage-debug
```

---

## Practice Drills

### Drill 1: Quick Status Check (1 min)
```bash
# Task: Check if all PVCs in namespace are Bound
k get pvc -n <namespace>
# Look for any not showing "Bound"
```

### Drill 2: Find PVC Events (1 min)
```bash
# Task: Get events for a specific PVC
k describe pvc <pvc-name> | grep -A20 Events
```

### Drill 3: Check Volume in Pod (2 min)
```bash
# Task: Verify a volume is mounted correctly in pod
k exec <pod> -- df -h
k exec <pod> -- ls -la /data
```

### Drill 4: Debug ContainerCreating (2 min)
```bash
# Task: Find why pod is stuck in ContainerCreating
k describe pod <pod-name>
# Check Events for mount errors
```

### Drill 5: Check CSI Driver Status (2 min)
```bash
# Task: Verify CSI driver is running
k get pods -n kube-system | grep csi
k get csidrivers
```

### Drill 6: Find Matching PV (2 min)
```bash
# Task: Find why PVC won't bind to existing PV
k get pvc <pvc-name> -o yaml | grep -E 'storage:|accessModes:|storageClassName:'
k get pv <pv-name> -o yaml | grep -E 'storage:|accessModes:|storageClassName:'
# Compare values
```

### Drill 7: Check VolumeAttachments (1 min)
```bash
# Task: List all volume attachments
k get volumeattachment
# Useful for debugging Multi-Attach errors
```

### Drill 8: Get Recent Storage Events (1 min)
```bash
# Task: Get recent events related to PVCs
k get events --field-selector reason=FailedBinding
k get events --field-selector reason=ProvisioningFailed
```

---

## Summary: Storage Troubleshooting Checklist

```
□ Pod stuck? → k describe pod → check Events
□ PVC Pending? → k describe pvc → check Events
□ StorageClass exists? → k get sc
□ PV available? → k get pv
□ Access modes match? → Compare PVC and PV
□ StorageClassName match? → Compare PVC and PV
□ CSI driver running? → k get pods -n kube-system | grep csi
□ Permissions issue? → Check securityContext fsGroup
□ Capacity issue? → Check quotas and storage backend
```

---

## Next Steps

Congratulations! You've completed Part 4: Storage. You should now be able to:
- Configure volumes (emptyDir, hostPath, projected)
- Work with PersistentVolumes and PersistentVolumeClaims
- Use StorageClasses for dynamic provisioning
- Create and restore from volume snapshots
- Troubleshoot common storage issues

Continue to the [Part 4 Cumulative Quiz](part4-cumulative-quiz.md) to test your knowledge, then proceed to [Part 5: Troubleshooting](../part5-troubleshooting/README.md).

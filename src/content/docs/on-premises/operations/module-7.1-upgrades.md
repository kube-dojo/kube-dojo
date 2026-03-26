---
title: "Module 7.1: Kubernetes Upgrades on Bare Metal"
slug: on-premises/operations/module-7.1-upgrades
sidebar:
  order: 2
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 1.3: Cluster Topology](../planning/module-1.3-cluster-topology/), [Module 2.4: Declarative Bare Metal](../provisioning/module-2.4-declarative-bare-metal/)

---

## Why This Module Matters

In October 2023, a financial services company running a 45-node bare metal Kubernetes cluster needed to upgrade from 1.27 to 1.28. They had been delaying upgrades for nine months because the process was manual, undocumented, and everyone who had done the last upgrade had left the company. When the security team mandated the upgrade due to a CVE in the kubelet, the remaining team attempted it on a Friday afternoon. They upgraded the control plane to 1.28, then upgraded all 45 worker nodes simultaneously. Twenty minutes in, they discovered that three nodes had a different kernel version that was incompatible with the new kubelet. Those nodes entered a crash loop. But the drain had already evicted pods from those nodes, and the cluster was running at 60% capacity. The PodDisruptionBudgets they had configured were ignored because they used `kubectl drain --force`. The result: 4 hours of degraded service, 2 hours of complete outage for stateful workloads, and a rollback that took another 3 hours because nobody had tested it.

The fix was straightforward but required discipline: a staging cluster that mirrors production, a written runbook, one-node-at-a-time rolling upgrades, and rollback procedures tested before the upgrade begins. The CTO's postmortem note: "We treated a bare metal upgrade like a cloud upgrade. It is not. Every node is a snowflake until you prove otherwise."

In the cloud, managed Kubernetes upgrades are a button click with automatic rollback. On bare metal, you are the managed service. Every upgrade is a planned operation that must account for heterogeneous hardware, limited spare capacity, and the absence of a safety net.

---

## What You'll Learn

- kubeadm upgrade workflow for control plane and workers
- Version skew policy and why it matters for rolling upgrades
- Draining nodes with limited spare capacity
- Rolling through heterogeneous hardware (different NICs, kernels, BIOS)
- Rollback strategies when an upgrade goes wrong
- Testing upgrades in staging before touching production

---

## Kubernetes Version Skew Policy

Before upgrading anything, you must understand what version combinations are supported. Kubernetes enforces strict version skew limits between components.

```
+---------------------------------------------------------------+
|               VERSION SKEW POLICY (Kubernetes)                 |
|                                                                |
|  kube-apiserver      must be at the HIGHEST version            |
|                                                                |
|  kube-controller-    can be at apiserver version               |
|  manager             or ONE minor version behind               |
|  kube-scheduler      (e.g., apiserver=1.29, scheduler=1.28)   |
|                                                                |
|  kubelet             can be up to THREE minor versions         |
|                       behind apiserver                         |
|                       (e.g., apiserver=1.29, kubelet=1.26)     |
|                                                                |
|  kubectl             can be ONE minor version ahead or         |
|                       behind apiserver                         |
|                                                                |
|  etcd                has its own version scheme                |
|                       kubeadm bundles a compatible version     |
+---------------------------------------------------------------+
```

### Why Three-Version Kubelet Skew Matters on Bare Metal

In the cloud, you upgrade all nodes within hours. On bare metal with 200 nodes and maintenance windows, the upgrade might stretch over weeks. The three-version kubelet skew means you can run apiserver at 1.30 while some workers still run kubelet 1.27 -- but 1.26 kubelets would stop working.

```bash
# Check current versions across all nodes
kubectl get nodes -o custom-columns=\
  NAME:.metadata.name,\
  KUBELET:.status.nodeInfo.kubeletVersion,\
  OS:.status.nodeInfo.osImage,\
  KERNEL:.status.nodeInfo.kernelVersion
```

---

## kubeadm Upgrade Workflow

### Step 1: Upgrade the First Control Plane Node

```bash
# Check available versions
apt-cache madison kubeadm | head -5

# Upgrade kubeadm on the first control plane node
apt-get update && apt-get install -y kubeadm=1.29.0-1.1

# Verify the upgrade plan
kubeadm upgrade plan

# Apply the upgrade (first control plane only)
kubeadm upgrade apply v1.29.0

# Upgrade kubelet and kubectl
apt-get install -y kubelet=1.29.0-1.1 kubectl=1.29.0-1.1
systemctl daemon-reload
systemctl restart kubelet
```

### Step 2: Upgrade Additional Control Plane Nodes

```bash
# On each additional control plane node
apt-get update && apt-get install -y kubeadm=1.29.0-1.1

# Use 'node' instead of 'apply' for additional control planes
kubeadm upgrade node

apt-get install -y kubelet=1.29.0-1.1 kubectl=1.29.0-1.1
systemctl daemon-reload
systemctl restart kubelet
```

### Step 3: Upgrade Worker Nodes (Rolling)

```
+---------------------------------------------------------------+
|            ROLLING WORKER UPGRADE SEQUENCE                     |
|                                                                |
|  Cluster: 12 workers, max unavailable = 2                     |
|                                                                |
|  Batch 1: [worker-01] [worker-02]                             |
|    drain -> upgrade kubeadm -> upgrade node ->                 |
|    upgrade kubelet -> restart -> uncordon                      |
|                                                                |
|  Batch 2: [worker-03] [worker-04]                             |
|    (wait for batch 1 pods to reschedule first)                 |
|                                                                |
|  Batch 3: [worker-05] [worker-06]                             |
|    ...                                                         |
|                                                                |
|  Batch 6: [worker-11] [worker-12]                             |
|    final batch, verify cluster health after                    |
+---------------------------------------------------------------+
```

---

## Draining Nodes with Limited Spare Capacity

On bare metal, you cannot spin up temporary nodes during an upgrade. If your cluster runs at 80% CPU utilization, draining even one node might push the remaining nodes above their limits.

### Capacity Planning Before Drain

```bash
# Check current resource usage across all nodes
kubectl top nodes

# Check how much headroom you have
kubectl get nodes -o json | jq -r '
  .items[] |
  "\(.metadata.name)
    Allocatable CPU: \(.status.allocatable.cpu)
    Allocatable Mem: \(.status.allocatable.memory)"'

# Check PodDisruptionBudgets that might block drains
kubectl get pdb --all-namespaces
```

### Safe Drain Procedure

```bash
# Step 1: Cordon the node (prevent new scheduling)
kubectl cordon worker-07

# Step 2: Check what will be evicted
kubectl get pods --field-selector spec.nodeName=worker-07 \
  --all-namespaces -o wide

# Step 3: Drain with safety rails
kubectl drain worker-07 \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --timeout=300s \
  --pod-selector='app!=critical-singleton'

# NEVER use --force unless you understand the consequences
# --force skips PDB checks and deletes standalone pods
```

### Handling Pods That Refuse to Drain

```bash
# Check which PDB is blocking
kubectl get pdb -A -o wide

# Example output:
# NAMESPACE   NAME        MIN AVAILABLE   ALLOWED DISRUPTIONS
# prod        redis-pdb   2               0

# If allowed disruptions = 0, the drain will hang
# Options:
# 1. Wait for replicas to become healthy
# 2. Scale up the deployment temporarily
kubectl scale deployment redis --replicas=4 -n prod
# Now drain should proceed (3 healthy > 2 min available)
```

---

## Rolling Through Heterogeneous Hardware

On bare metal, not all nodes are identical. You might have three generations of servers with different CPUs, NICs, kernel versions, and firmware. An upgrade that works on one generation might fail on another.

### Categorize Your Hardware

```bash
# Create a hardware inventory
kubectl get nodes -o json | jq -r '
  .items[] | [
    .metadata.name,
    .metadata.labels["node.kubernetes.io/instance-type"] // "unknown",
    .status.nodeInfo.kernelVersion,
    .status.nodeInfo.containerRuntimeVersion,
    .status.nodeInfo.architecture
  ] | @tsv' | sort -k2 | column -t
```

### Upgrade Order by Hardware Generation

```
+---------------------------------------------------------------+
|        UPGRADE ORDER FOR HETEROGENEOUS HARDWARE                |
|                                                                |
|  Phase 1: Canary (1 node per hardware generation)             |
|     [dell-r640-01]  [dell-r740-01]  [hp-dl380-01]             |
|     Monitor for 30 min after each                              |
|                                                                |
|  Phase 2: Remaining Gen 1 (oldest hardware first)             |
|     [dell-r640-02..08]  rolling, 2 at a time                  |
|                                                                |
|  Phase 3: Gen 2                                                |
|     [dell-r740-02..15]  rolling, 3 at a time                  |
|                                                                |
|  Phase 4: Gen 3 (newest hardware last)                        |
|     [hp-dl380-02..20]   rolling, 3 at a time                  |
|                                                                |
|  Why oldest first?                                             |
|  - Oldest hardware is most likely to surface problems          |
|  - If a kernel incompatibility exists, you find it early       |
|  - Newest hardware has the most spare capacity as buffer       |
+---------------------------------------------------------------+
```

### Pre-flight Checks per Hardware Generation

```bash
#!/bin/bash
# pre-flight-check.sh — run on each node before upgrading
set -euo pipefail

echo "=== Pre-flight Check ==="
echo "Hostname: $(hostname) | Kernel: $(uname -r)"
echo "CPU: $(lscpu | grep 'Model name')"

# Check cgroup v2, disk space, container runtime
grep -q cgroup2 /proc/filesystems || { echo "FAIL: no cgroup v2"; exit 1; }
DISK_FREE=$(df /var/lib/kubelet --output=pcent | tail -1 | tr -d ' %')
[ "$DISK_FREE" -gt 85 ] && { echo "FAIL: disk ${DISK_FREE}%"; exit 1; }
crictl info > /dev/null 2>&1 || { echo "FAIL: runtime down"; exit 1; }
echo "=== All checks passed ==="
```

---

## Rollback Strategies

Rolling back a Kubernetes upgrade is harder than the upgrade itself. You must plan for rollback before you begin.

### Control Plane Rollback

```bash
# kubeadm does NOT have a built-in rollback command
# You must manually downgrade packages

# Step 1: Install the previous kubeadm version
apt-get install -y kubeadm=1.28.5-1.1

# Step 2: Downgrade kubelet and kubectl
apt-get install -y kubelet=1.28.5-1.1 kubectl=1.28.5-1.1
systemctl daemon-reload
systemctl restart kubelet

# Step 3: Restore etcd from backup (if schema changed)
# This is why you ALWAYS back up etcd before upgrading
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-pre-upgrade.db \
  --data-dir /var/lib/etcd-restored \
  --name $(hostname) \
  --initial-cluster $(hostname)=https://$(hostname):2380

# Step 4: Point etcd to the restored data
# Edit /etc/kubernetes/manifests/etcd.yaml:
#   --data-dir=/var/lib/etcd-restored
```

### The etcd Backup Rule

```bash
# ALWAYS back up etcd before ANY control plane upgrade
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-pre-upgrade.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify the backup
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-pre-upgrade.db \
  --write-out=table
```

---

## Testing Upgrades in Staging

On bare metal, your staging cluster should mirror production hardware as closely as possible. This means at least one node from each hardware generation.

### Staging Cluster Requirements

```
+---------------------------------------------------------------+
|            STAGING CLUSTER FOR UPGRADE TESTING                 |
|                                                                |
|  Minimum staging cluster:                                      |
|  - 3 control plane nodes (same hardware as production)         |
|  - 1 worker per hardware generation                            |
|  - Same CNI, CSI, and ingress controller versions              |
|  - Representative workloads (not production data)              |
|                                                                |
|  Test matrix:                                                  |
|  +------------------+----------------------------------+       |
|  | Test             | Pass criteria                    |       |
|  +------------------+----------------------------------+       |
|  | kubeadm upgrade  | No errors, all nodes Ready       |       |
|  | Pod scheduling   | Pods schedule on all generations  |       |
|  | CNI networking   | Pod-to-pod across nodes works     |       |
|  | CSI storage      | PVCs bind, data persists          |       |
|  | Ingress          | External traffic routes correctly  |       |
|  | DNS              | CoreDNS resolves internal names    |       |
|  | GPU/SR-IOV       | Device plugins register devices   |       |
|  | Monitoring       | Prometheus scrapes all targets     |       |
|  +------------------+----------------------------------+       |
+---------------------------------------------------------------+
```

---

## The Complete Upgrade Runbook

Here is the sequence for a production bare metal upgrade:

```
+---------------------------------------------------------------+
|              PRODUCTION UPGRADE RUNBOOK                        |
|                                                                |
|  Week -2: Test upgrade on staging cluster                      |
|  Week -1: Back up etcd, verify backups, update runbook         |
|                                                                |
|  Day of upgrade:                                               |
|  1. Notify stakeholders (email + Slack)                        |
|  2. Verify etcd backup is fresh (< 1 hour old)                 |
|  3. Record current versions of all components                  |
|  4. Upgrade first control plane node                           |
|  5. Verify apiserver, scheduler, controller-manager healthy    |
|  6. Upgrade remaining control plane nodes (one at a time)      |
|  7. Verify control plane quorum                                |
|  8. Upgrade canary worker (1 per hardware generation)          |
|  9. Monitor for 30 minutes                                     |
|  10. Roll through remaining workers in batches of 2-3          |
|  11. Wait 5 min between batches                                |
|  12. Run smoke tests after final batch                         |
|  13. Update monitoring dashboards for new version              |
|  14. Send completion notification                              |
|                                                                |
|  Rollback triggers:                                            |
|  - Any control plane node fails to rejoin                      |
|  - > 5% of pods in CrashLoopBackOff after upgrade              |
|  - Networking between nodes fails                              |
|  - Storage mounts fail on upgraded nodes                       |
+---------------------------------------------------------------+
```

---

## Did You Know?

- **Kubernetes drops support for a minor version approximately 14 months after release.** On bare metal, where upgrades take longer to plan and execute, this means you should start planning the next upgrade almost immediately after completing the current one. Falling behind two versions is uncomfortable; falling behind three is an emergency.

- **The kubelet's three-version skew tolerance was expanded from two in Kubernetes 1.28.** This change was specifically motivated by on-premises and air-gapped environments where upgrading all nodes quickly is impractical. The KEP (Kubernetes Enhancement Proposal) cited large bare metal deployments as the primary beneficiary.

- **etcd upgrades are the riskiest part of a control plane upgrade.** etcd uses a WAL (Write-Ahead Log) format that can change between versions. If the new etcd version migrates the WAL format, you cannot simply roll back to the old binary. This is why etcd backup before upgrade is non-negotiable.

- **Google's internal Borg system inspired Kubernetes, but Google upgrades Borg clusters cell-by-cell across thousands of nodes using a dedicated upgrade service.** On bare metal Kubernetes, you are building that upgrade service yourself with shell scripts and kubeadm.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Skipping minor versions | kubeadm only supports +1 minor version upgrades | Upgrade sequentially: 1.27 -> 1.28 -> 1.29 |
| No etcd backup before upgrade | Cannot roll back if etcd schema changes | Always `etcdctl snapshot save` before upgrading |
| Draining all workers at once | Insufficient capacity for running workloads | Roll in batches matching your spare capacity |
| Using `--force` on drain | Skips PDB checks, deletes standalone pods | Use `--timeout` and fix blocked drains properly |
| Not testing on staging | Hardware-specific failures discovered in production | Maintain staging with representative hardware |
| Ignoring version skew | Components stop communicating | Check all component versions before and after |
| Upgrading on Friday afternoon | No time to handle unexpected failures | Schedule upgrades Tuesday-Wednesday morning |
| Not recording pre-upgrade state | Cannot compare before/after | Script the version inventory before starting |

---

## Quiz

### Question 1
You have a 30-node cluster running Kubernetes 1.27. You need to get to 1.30. What is the correct upgrade path, and how long should you expect it to take on bare metal?

<details>
<summary>Answer</summary>

**Upgrade path: 1.27 -> 1.28 -> 1.29 -> 1.30 (three sequential minor version upgrades).**

kubeadm only supports upgrading one minor version at a time. You cannot skip from 1.27 to 1.30 directly.

**Time estimate for bare metal:**
- Each minor version upgrade: 1-2 days (staging test) + 1 day (production rollout)
- Three upgrades: 6-9 days of calendar time, spread across 3-4 weeks
- Include buffer for unexpected issues: plan for 4-6 weeks total

**Per upgrade cycle:**
1. Test on staging (1 day)
2. Upgrade 3 control plane nodes (2-3 hours)
3. Roll 30 workers in batches of 3 (3-4 hours with monitoring gaps)
4. Post-upgrade validation (1 hour)

The kubelet three-version skew policy means your 1.27 kubelets will still work with a 1.30 apiserver, giving you flexibility in the worker rollout timeline. But the control plane must go through each version.
</details>

### Question 2
During an upgrade, `kubectl drain worker-12` hangs indefinitely. What are the most likely causes and how do you resolve each?

<details>
<summary>Answer</summary>

**Most likely causes:**

1. **PodDisruptionBudget blocking eviction**: A PDB with `minAvailable` equal to the current replica count means zero allowed disruptions.
   ```bash
   kubectl get pdb -A -o wide
   # Fix: scale up the deployment, then drain
   kubectl scale deploy my-app --replicas=4
   ```

2. **Pod with no controller (standalone pod)**: Drain skips standalone pods by default but shows a warning. With `--force`, it deletes them permanently.
   ```bash
   kubectl get pods --field-selector spec.nodeName=worker-12 \
     -A -o json | jq '.items[] | select(.metadata.ownerReferences == null) | .metadata.name'
   ```

3. **Local storage (emptyDir)**: Pods using emptyDir block drain unless `--delete-emptydir-data` is specified.

4. **DaemonSet pods**: These block drain unless `--ignore-daemonsets` is specified.

5. **Finalizer stuck on pod**: A pod with a finalizer that never completes will prevent eviction.
   ```bash
   kubectl get pods -n stuck-ns -o json | jq '.items[].metadata.finalizers'
   ```

**Resolution workflow:**
1. Add `--timeout=300s` to see which pod is blocking
2. Check PDBs, then scale up if needed
3. Handle standalone pods case by case
4. Always include `--ignore-daemonsets --delete-emptydir-data`
</details>

### Question 3
Your cluster has three hardware generations: Dell R640 (2018), Dell R740 (2020), and HPE DL380 Gen10 (2022). After upgrading kubelet to 1.29, the R640 nodes show `NotReady`. The R740 and DL380 nodes are fine. What do you investigate?

<details>
<summary>Answer</summary>

**Investigation steps for hardware-generation-specific failures:**

1. **Check kubelet logs on a failing R640:**
   ```bash
   journalctl -u kubelet -n 100 --no-pager
   ```

2. **Check kernel version**: R640 nodes may run an older kernel that lacks features required by the new kubelet (cgroup v2 support, specific sysctls).
   ```bash
   ssh r640-01 "uname -r"
   # Compare with working R740: ssh r740-01 "uname -r"
   ```

3. **Check container runtime compatibility**: Older containerd versions might not support new kubelet CRI requirements.
   ```bash
   ssh r640-01 "containerd --version"
   ```

4. **Check CPU instruction set**: Very old CPUs might lack instructions required by newer Go binaries (kubelet compiled with newer Go versions may use AVX2 or similar).

5. **Check BIOS/firmware**: Older BIOS versions might expose hardware features differently, affecting cgroup mounting or NUMA topology detection.

**Most common root cause**: Kernel version too old for the new kubelet's cgroup requirements. Solution: upgrade the OS kernel on R640 nodes before the Kubernetes upgrade.

**Rollback**: Downgrade kubelet on R640 nodes to 1.28 (within skew policy), fix the kernel, then retry.
</details>

### Question 4
You need to roll back the control plane from 1.29 to 1.28 after discovering a critical bug. Your etcd was upgraded and has already accepted writes in the new format. What is the procedure?

<details>
<summary>Answer</summary>

**This is a critical scenario that requires etcd restore from backup.**

1. **Stop the apiserver on all control plane nodes** to prevent new writes:
   ```bash
   # Move static pod manifests to stop them
   mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
   ```

2. **Restore etcd from pre-upgrade backup** (this is why you always back up):
   ```bash
   # Stop etcd
   mv /etc/kubernetes/manifests/etcd.yaml /tmp/

   # Restore the backup
   ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-pre-upgrade.db \
     --data-dir /var/lib/etcd-restored

   # Replace the data directory
   mv /var/lib/etcd /var/lib/etcd-broken
   mv /var/lib/etcd-restored /var/lib/etcd
   ```

3. **Downgrade kubeadm, kubelet, kubectl** on all control plane nodes:
   ```bash
   apt-get install -y kubeadm=1.28.5-1.1 kubelet=1.28.5-1.1 kubectl=1.28.5-1.1
   ```

4. **Restore static pod manifests** (the old versions from backup):
   ```bash
   # Copy the backed-up manifests from before the upgrade
   cp /backup/manifests-pre-upgrade/* /etc/kubernetes/manifests/
   ```

5. **Restart kubelet** on all control plane nodes:
   ```bash
   systemctl daemon-reload && systemctl restart kubelet
   ```

6. **Verify**: Check all control plane components are running at 1.28 and etcd cluster has quorum.

**Data loss warning**: Any writes between the upgrade and the restore are lost. This is why you should catch upgrade failures as fast as possible and why you run canary workloads that validate behavior immediately after upgrade.

**If you did not back up etcd**: You cannot safely downgrade if etcd migrated its WAL format. Your only options are to fix the 1.29 issue or rebuild the cluster. This is why etcd backup is non-negotiable.
</details>

---

## Hands-On Exercise: Plan and Execute a Cluster Upgrade

**Task**: Using a kind cluster, practice the full kubeadm upgrade workflow.

### Setup

```bash
# Create a kind cluster running an older version
cat <<'KINDEOF' > /tmp/kind-upgrade-lab.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    image: kindest/node:v1.28.0
  - role: worker
    image: kindest/node:v1.28.0
  - role: worker
    image: kindest/node:v1.28.0
KINDEOF

kind create cluster --config /tmp/kind-upgrade-lab.yaml --name upgrade-lab
```

### Steps

1. **Record current versions:**
   ```bash
   kubectl get nodes -o wide
   ```

2. **Deploy a test workload with PDB:**
   ```bash
   kubectl create deployment nginx --image=nginx --replicas=3
   kubectl create pdb nginx-pdb --selector=app=nginx --min-available=2
   ```

3. **Practice draining a worker with PDB enforcement:**
   ```bash
   kubectl drain upgrade-lab-worker --ignore-daemonsets --delete-emptydir-data
   # Observe how PDB affects the drain
   ```

4. **Uncordon and verify pod redistribution:**
   ```bash
   kubectl uncordon upgrade-lab-worker
   kubectl get pods -o wide
   ```

5. **Document your observations:** Which pods were evicted? How long did the drain take? Did the PDB prevent disruption below the minimum?

### Success Criteria

- [ ] Recorded all node versions before starting
- [ ] Deployed workload with PDB
- [ ] Successfully drained a node while PDB was active
- [ ] Verified pods rescheduled to remaining nodes
- [ ] Uncordoned and verified cluster returned to normal
- [ ] Documented the process in a runbook format

### Cleanup

```bash
kind delete cluster --name upgrade-lab
```

---

## Next Module

Continue to [Module 7.2: Hardware Lifecycle & Firmware](../operations/module-7.2-hardware-lifecycle/) to learn how to manage BIOS updates, disk replacements, and firmware patching without cluster downtime.

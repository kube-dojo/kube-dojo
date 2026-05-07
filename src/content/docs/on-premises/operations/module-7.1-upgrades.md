---
title: "Module 7.1: Kubernetes Upgrades on Bare Metal"
slug: on-premises/operations/module-7.1-upgrades
sidebar:
  order: 2
---

> **Complexity**: `[COMPLEX]` | Time: 60 minutes
>
> **Prerequisites**: [Module 1.3: Cluster Topology](/on-premises/planning/module-1.3-cluster-topology/), [Module 2.4: Declarative Bare Metal](/on-premises/provisioning/module-2.4-declarative-bare-metal/)

---

## Why This Module Matters

An undocumented, all-at-once upgrade on heterogeneous bare-metal nodes can turn routine maintenance into an outage, especially when capacity is tight and rollback has not been rehearsed.

The fix was straightforward but required discipline: a staging cluster that mirrors production, a written runbook, one-node-at-a-time rolling upgrades, and rollback procedures tested before the upgrade begins. A useful postmortem conclusion is that bare-metal upgrades need rehearsed runbooks, staged rollouts, and validation of node differences before production changes.

In managed Kubernetes services, the provider automates more of the upgrade workflow. On bare metal, you are the managed service. Every upgrade is a planned operation that must account for heterogeneous hardware, limited spare capacity, and the absence of a safety net.

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Plan** bare-metal Kubernetes upgrades with staging validation, written runbooks, and tested rollback procedures
2. **Implement** rolling node upgrades that respect PodDisruptionBudgets, drain timeouts, and heterogeneous hardware constraints
3. **Design** a staging cluster that mirrors production hardware and workloads for pre-upgrade validation
4. **Troubleshoot** upgrade failures caused by kernel incompatibilities, deprecated APIs, and node-level configuration drift

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

```mermaid
flowchart LR
    API["kube-apiserver<br/>(Highest Version)"]
    CM["kube-controller-manager<br/>kube-scheduler<br/>(Same or 1 minor behind)"]
    Kubelet["kubelet & kube-proxy<br/>(Up to 3 minors behind)"]
    Kubectl["kubectl<br/>(±1 minor version)"]
    Etcd["etcd<br/>(Compatible bundled version)"]

    API --- CM
    API --- Kubelet
    API --- Kubectl
    API --- Etcd
```

[For example, if `kube-apiserver` is at **v1.35**:](https://kubernetes.io/releases/version-skew-policy)
- In highly available (HA) control planes, all `kube-apiserver` instances must be within one minor version of each other.
- `kube-controller-manager` and `kube-scheduler` can be at **v1.35** or **v1.34**.
- `kubelet` and `kube-proxy` can be at **v1.35**, **v1.34**, **v1.33**, or **v1.32**.
- `kubectl` can be at **v1.36**, **v1.35**, or **v1.34**.

### Why Three-Version Kubelet Skew Matters on Bare Metal

In the cloud, you upgrade all nodes within hours. On bare metal with 200 nodes and maintenance windows, the upgrade might stretch over weeks. [The three-version kubelet skew means you can run apiserver at 1.35 while some workers still run kubelet 1.32 -- but 1.31 kubelets would stop working.](https://kubernetes.io/releases/version-skew-policy)

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

> **Pause and predict**: Before reading the upgrade steps, think about why [the first control plane node uses `kubeadm upgrade apply` while subsequent control plane nodes use `kubeadm upgrade node`](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/). What is different about the first node?

> **Prerequisite**: [Your bare-metal cluster must be running with either static control-plane/etcd pods or an external etcd cluster. `kubeadm upgrade` does not support other control plane topologies.](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)

### Step 1: Upgrade the First Control Plane Node

The first control plane upgrade is special: `kubeadm upgrade apply` upgrades the cluster-wide components (API server, controller manager, scheduler manifests) and etcd. Subsequent nodes only need to update their local kubelet and static pod manifests.

> **Note**: For Kubernetes versions released after September 13, 2023, [you must use the community-owned `pkgs.k8s.io` package repositories](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/), which use per-minor URLs. Legacy apt/yum repos are frozen and no longer receive updates.

> **Note**: If `kubeadm upgrade apply` fails partway through, it does not fully roll back automatically. However, [the command is idempotent—you can fix the underlying issue and safely run `kubeadm upgrade apply` again.](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)

```bash
# Check available versions
apt-cache madison kubeadm | head -5

# Unhold packages to allow upgrade
apt-mark unhold kubeadm

# Upgrade kubeadm on the first control plane node
apt-get update && apt-get install -y kubeadm=1.35.3-1.1

# Hold kubeadm to prevent accidental upgrades
apt-mark hold kubeadm

# Verify the upgrade plan
kubeadm upgrade plan

# Apply the upgrade (first control plane only)
kubeadm upgrade apply v1.35.3

# Unhold packages, upgrade kubelet and kubectl, then hold again
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.35.3-1.1 kubectl=1.35.3-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
```

### Step 2: Upgrade Additional Control Plane Nodes

```bash
# On each additional control plane node
apt-mark unhold kubeadm
apt-get update && apt-get install -y kubeadm=1.35.3-1.1
apt-mark hold kubeadm

# Use 'node' instead of 'apply' for additional control planes
kubeadm upgrade node

apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.35.3-1.1 kubectl=1.35.3-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
```

### Step 3: Upgrade Worker Nodes (Rolling)

[In-place minor kubelet upgrades are not supported. You must drain the node before upgrading the packages.](https://kubernetes.io/releases/version-skew-policy)

```mermaid
flowchart TD
    Start["Cluster: 12 workers, max unavailable = 2"] --> B1
    B1["Batch 1: [worker-01] [worker-02]<br>drain -> upgrade kubeadm -> upgrade node -> upgrade kubelet -> restart -> uncordon"] --> W1
    W1{"Wait for batch 1 pods<br>to reschedule first"} --> B2
    B2["Batch 2: [worker-03] [worker-04]"] --> W2
    W2{"Wait for batch 2 pods"} --> B3
    B3["Batch 3: [worker-05] [worker-06]<br>..."] --> B6
    B6["Batch 6: [worker-11] [worker-12]<br>final batch"] --> Done
    Done(["Verify cluster health after"])
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

> **Stop and think**: Your cluster runs at 80% CPU utilization. You need to drain a node for upgrade. Where do those pods go? What happens if the remaining nodes cannot absorb the evicted workloads?

### Safe Drain Procedure

The drain process happens in stages: first cordon the node to prevent new pods from scheduling, then inspect what will be evicted, and finally drain with explicit safety rails. Never use `--force` unless you have a specific reason and understand the consequences.

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
# --force allows drain to proceed for unmanaged pods; bypassing PodDisruptionBudgets requires `--disable-eviction`, which is much riskier.
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

```mermaid
flowchart TD
    subgraph Phase 1: Canary
        C1["[dell-r640-01]"]
        C2["[dell-r740-01]"]
        C3["[hp-dl380-01]"]
        M["Monitor for 30 min after each"]
        C1 & C2 & C3 --> M
    end
    
    subgraph Phase 2: Remaining Gen 1
        G1["[dell-r640-02..08]<br>rolling, 2 at a time"]
        N1["Why oldest first?<br>- Oldest hardware is most likely to surface problems<br>- If a kernel incompatibility exists, you find it early<br>- Newest hardware has the most spare capacity as buffer"]
    end
    
    subgraph Phase 3: Gen 2
        G2["[dell-r740-02..15]<br>rolling, 3 at a time"]
    end
    
    subgraph Phase 4: Gen 3
        G3["[hp-dl380-02..20]<br>rolling, 3 at a time<br>(newest hardware last)"]
    end
    
    Phase 1 --> Phase 2 --> Phase 3 --> Phase 4
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
apt-mark unhold kubeadm
apt-get install -y kubeadm=1.34.6-1.1
apt-mark hold kubeadm

# Step 2: Downgrade kubelet and kubectl
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.34.6-1.1 kubectl=1.34.6-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet

# Step 3: Restore etcd from backup (if schema changed)
# This is why you ALWAYS back up etcd before upgrading
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-pre-upgrade.db \
  --data-dir /var/lib/etcd-restored \
  --name $(hostname) \
  --initial-cluster $(hostname)=https://$(hostname):2380

# Step 4: Swap the etcd data directory
mv /var/lib/etcd /var/lib/etcd-broken
mv /var/lib/etcd-restored /var/lib/etcd

# Step 5: Restore static pod manifests from pre-upgrade backup
# Without this, the control plane containers will still run the newer images
# Note: kubeadm cluster upgrades also create backups under /etc/kubernetes/tmp/kubeadm-backup-manifests-*
cp /backup/manifests-pre-upgrade/* /etc/kubernetes/manifests/
# Alternatively, use the automated backup:
# cp /etc/kubernetes/tmp/kubeadm-backup-manifests-*/... /etc/kubernetes/manifests/
```

> **Pause and predict**: You are about to upgrade your control plane. The etcd snapshot is your safety net. If you skip this step and the upgrade corrupts etcd's WAL format, what are your options for recovery?

### The etcd Backup Rule

This is the single most important step before any control plane upgrade. etcd's Write-Ahead Log format can change between versions, making downgrades impossible without a pre-upgrade snapshot.

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

```mermaid
flowchart TD
    subgraph Staging Cluster For Upgrade Testing
        CP["3 control plane nodes<br>(same hardware as production)"]
        W["1 worker per hardware generation"]
        Env["Same CNI, CSI, and ingress controller versions<br>Representative workloads (not production data)"]
    end
    
    subgraph Test Matrix
        T1["kubeadm upgrade: No errors, all nodes Ready"]
        T2["Pod scheduling: Pods schedule on all generations"]
        T3["CNI networking: Pod-to-pod across nodes works"]
        T4["CSI storage: PVCs bind, data persists"]
        T5["Ingress: External traffic routes correctly"]
        T6["DNS: CoreDNS resolves internal names"]
        T7["GPU/SR-IOV: Device plugins register devices"]
        T8["Monitoring: Prometheus scrapes all targets"]
    end
    
    Staging Cluster For Upgrade Testing --> Test Matrix
```

---

## The Complete Upgrade Runbook

Here is the sequence for a production bare metal upgrade:

```mermaid
flowchart TD
    subgraph Preparation
        W2["Week -2: Test upgrade on staging cluster"]
        W1["Week -1: Back up etcd, verify backups, update runbook"]
    end
    
    subgraph Day of Upgrade
        D1["1. Notify stakeholders (email + Slack)"] --> D2["2. Verify etcd backup is fresh (< 1 hour old)"]
        D2 --> D3["3. Record current versions of all components"]
        D3 --> D4["4. Upgrade first control plane node"]
        D4 --> D5["5. Verify apiserver, scheduler, controller-manager healthy"]
        D5 --> D6["6. Upgrade remaining control plane nodes (one at a time)"]
        D6 --> D7["7. Verify control plane quorum"]
        D7 --> D8["8. Upgrade canary worker (1 per hardware generation)"]
        D8 --> D9["9. Monitor for 30 minutes"]
        D9 --> D10["10. Roll through remaining workers in batches of 2-3"]
        D10 --> D11["11. Wait 5 min between batches"]
        D11 --> D12["12. Run smoke tests after final batch"]
        D12 --> D13["13. Update monitoring dashboards for new version"]
        D13 --> D14["14. Send completion notification"]
    end
    
    subgraph Rollback Triggers
        R1["- Any control plane node fails to rejoin<br>- > 5% of pods in CrashLoopBackOff after upgrade<br>- Networking between nodes fails<br>- Storage mounts fail on upgraded nodes"]
    end
```

---

## Did You Know?

- [**Kubernetes drops support for a minor version approximately 12 months after release.**](https://kubernetes.io/releases/version-skew-policy) On bare metal, where upgrades take longer to plan and execute, this means you should start planning the next upgrade almost immediately after completing the current one. Falling behind two versions is uncomfortable; falling behind three is an emergency.

- **For Kubernetes 1.35 on Linux, the kubelet no longer starts on cgroup v1 nodes by default.** This makes cgroup v2 readiness an important prerequisite when refreshing node operating systems and runtimes.

- [**The kubelet's three-version skew tolerance was expanded from two in Kubernetes 1.28.**](https://kubernetes.io/blog/2023/08/15/kubernetes-v1-28-release/) This change reduced the pressure to upgrade every node immediately during slower rolling-upgrade programs.

- **etcd upgrades are the riskiest part of a control plane upgrade.** etcd uses a WAL (Write-Ahead Log) format that can change between versions. If the new etcd version migrates the WAL format, you cannot simply roll back to the old binary. This is why etcd backup before upgrade is non-negotiable.

- **Kubernetes was heavily influenced by Borg, but on bare metal you still need to design and operate your own upgrade process.**

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Skipping minor versions | kubeadm only supports +1 minor version upgrades | Upgrade sequentially: 1.33 -> 1.34 -> 1.35 |
| No etcd backup before upgrade | Cannot roll back if etcd schema changes | Always `etcdctl snapshot save` before upgrading |
| Draining all workers at once | Insufficient capacity for running workloads | Roll in batches matching your spare capacity |
| Using `--force` or `--disable-eviction` carelessly during drain | `--force` affects unmanaged pods, while `--disable-eviction` bypasses PDB protections | Prefer normal eviction, use timeouts, and fix the blocking condition explicitly |
| Not testing on staging | Hardware-specific failures discovered in production | Maintain staging with representative hardware |
| Ignoring version skew | Components stop communicating | Check all component versions before and after |
| Upgrading on Friday afternoon | No time to handle unexpected failures | Schedule upgrades Tuesday-Wednesday morning |
| Not recording pre-upgrade state | Cannot compare before/after | Script the version inventory before starting |

---

## Quiz

### Question 1
You have a 30-node cluster running Kubernetes 1.32. The security team notes that 1.32 is officially end-of-life and mandates an immediate upgrade to 1.35. What is the correct upgrade path, and how does the version skew policy affect your execution timeline on bare metal?

<details>
<summary>Answer</summary>

The correct upgrade path is 1.32 -> 1.33 -> 1.34 -> 1.35 (three sequential minor version upgrades). `kubeadm` does not support skipping minor versions during an upgrade step. Therefore, the control plane must be upgraded sequentially through 1.33, 1.34, and 1.35. However, thanks to the kubelet's three-version skew policy, a 1.35 API server can still communicate with 1.32 kubelets. This means you have the flexibility to upgrade the control plane rapidly through the intermediate versions while rolling the worker node upgrades over a longer period, reducing immediate disruption.
</details>

### Question 2
During a worker upgrade cycle, you run `kubectl drain worker-12` but it hangs indefinitely. The node has plenty of spare capacity. What are the most likely causes of this hang, and how do you resolve each safely?

<details>
<summary>Answer</summary>

The most common cause of a hanging drain is a PodDisruptionBudget (PDB) blocking eviction. If a deployment has a PDB with `minAvailable` equal to its current healthy replica count, the drain command cannot evict the pod without violating the budget, so it waits indefinitely. You can resolve this safely by temporarily scaling up the deployment so that evicting one pod still leaves enough replicas to satisfy the PDB. Another potential cause is a standalone pod without a controller or a pod with stuck finalizers, which require manual intervention to delete or resolve. Never use `--force` to bypass these checks unless you explicitly accept the risk of application downtime.
</details>

### Question 3
Your bare-metal cluster runs on three hardware generations: Dell R640, Dell R740, and HPE DL380. After successfully upgrading the control plane to 1.35, you upgrade the kubelet on your first R640 canary node, but it fails to start and reports `NotReady`. The R740 nodes upgrade perfectly. What should you investigate, and why did this happen?

<details>
<summary>Answer</summary>

Hardware-generation-specific failures usually stem from OS-level or kernel incompatibilities rather than Kubernetes itself. In Kubernetes 1.35, the kubelet strictly requires cgroups v2 and sets `FailCgroupV1=true` by default, which will cause it to crash if the older R640 node's OS still uses legacy cgroups v1. You should inspect the kubelet logs via `journalctl -u kubelet` to identify the specific error and verify the underlying kernel and cgroup versions. To resolve this safely, you must roll back the kubelet on the R640 to the previous version, update the underlying OS to meet the new cgroups v2 prerequisite, and then re-attempt the upgrade. This scenario highlights why staging environments must mirror production hardware generations.
</details>

### Question 4
You have just upgraded your control plane from 1.34 to 1.35. Twenty minutes later, you discover a critical regression in your workloads that requires a rollback. Your etcd was upgraded and has already accepted writes in the 1.35 format. How do you safely roll back to 1.34?

<details>
<summary>Answer</summary>

Rolling back a control plane is complex because `kubeadm` does not have a built-in downgrade command, and etcd may have migrated its Write-Ahead Log to a new, incompatible format. You usually cannot simply downgrade the etcd binary after an upgrade; instead, restore etcd from the snapshot you took immediately before the upgrade. First, stop the API server on all control plane nodes by temporarily moving their static pod manifests out of `/etc/kubernetes/manifests/` to prevent any further writes. Next, use `etcdctl snapshot restore` to recover the previous state, downgrade the `kubeadm`, `kubelet`, and `kubectl` packages to the 1.34 version, and restore the pre-upgrade static pod manifests from the `/etc/kubernetes/tmp/kubeadm-backup-manifests-*` directory. Finally, restart the kubelet to bring the 1.34 control plane back online, keeping in mind that any cluster state changes made during those twenty minutes will be permanently lost.
</details>

---

## Hands-On Exercise: Practice Node Draining and PDB Enforcement

**Task**: Using a kind cluster, practice node draining with PodDisruptionBudgets. Note: kind nodes are containers with pre-baked binaries, so OS-level package upgrades (`apt-get install kubeadm`) cannot be performed. This exercise focuses on the drain/uncordon workflow that is critical during real upgrades.

### Setup

```bash
# Create a kind cluster running a supported version
cat <<'KINDEOF' > /tmp/kind-upgrade-lab.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    image: kindest/node:v1.34.0
  - role: worker
    image: kindest/node:v1.34.0
  - role: worker
    image: kindest/node:v1.34.0
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

Continue to [Module 7.2: Hardware Lifecycle & Firmware](/on-premises/operations/module-7.2-hardware-lifecycle/) to learn how to manage BIOS updates, disk replacements, and firmware patching without cluster downtime.

## Sources

- [Kubernetes Version Skew Policy](https://kubernetes.io/releases/version-skew-policy) — Supports claims about supported minor-version skew between kube-apiserver, controller-manager, scheduler, kubelet, kube-proxy, and kubectl during staged upgrades and mixed-version maintenance windows.
- [Upgrading kubeadm Clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) — Supports kubeadm upgrade workflow claims: first control plane vs additional control planes, worker upgrade sequencing, drain/uncordon expectations, certificate renewal behavior, and current package-repository guidance for post-2023 releases.
- [kubectl drain Reference](https://v1-35.docs.kubernetes.io/docs/reference/kubectl/generated/kubectl_drain/) — Supports maintenance and upgrade claims around cordon/drain/uncordon behavior, eviction vs delete semantics, daemonset handling, graceful termination, and the risk of bypassing disruption protections.
- [Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) — Backs PodDisruptionBudget behavior, voluntary disruption semantics, and drain/eviction behavior relevant to decommissioning old nodes during capacity expansion.
- [kubernetes.io: kubernetes v1 28 release](https://kubernetes.io/blog/2023/08/15/kubernetes-v1-28-release/) — The Kubernetes 1.28 release announcement states that the supported skew expanded from n-2 to n-3.

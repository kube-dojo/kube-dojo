---
title: "Module 15.5: etcd-operator - Managing Kubernetes' Backbone"
slug: platform/toolkits/data-ai-platforms/cloud-native-databases/module-15.5-etcd-operator
sidebar:
  order: 6
---
## Complexity: [MEDIUM]
## Time to Complete: 40-45 minutes

---

## Learning Outcomes

After completing this module, you will be able to:
- **Explain** why operator-managed etcd is safer than manual management and what the operator automates
- **Deploy** an etcd cluster with TLS using the etcd-operator and verify cluster health
- **Diagnose** common etcd failures (split-brain, member loss, upgrade rejection) by reading operator status and events
- **Evaluate** when to use the etcd-operator vs manual etcd management vs managed Kubernetes control planes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 15.1: CockroachDB](../module-15.1-cockroachdb/) - Distributed consensus concepts
- Kubernetes fundamentals (CRDs, Operators, StatefulSets)
- CKA etcd knowledge (backup, restore, cluster health)
- [Reliability Engineering Foundation](/platform/foundations/reliability-engineering/) - HA concepts

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy etcd clusters on Kubernetes using operators with automated member management and recovery**
- **Configure etcd backup schedules, compaction policies, and performance tuning for production workloads**
- **Implement etcd cluster scaling, member replacement, and disaster recovery procedures**
- **Monitor etcd health metrics and optimize performance for Kubernetes control plane reliability**


## Why This Module Matters

**The Cluster That Forgot Everything**

An etcd quorum failure can make the Kubernetes API effectively unavailable for writes, freezing normal cluster operations until quorum is restored.

Restoring etcd from an out-of-date snapshot can lose recent cluster-state changes and significantly extend an outage.

Operator-managed recovery can reduce manual intervention during member failures, but any claimed outage outcome or timing needs a source.

> **The Heart Transplant Analogy**
>
> etcd is the heart of every Kubernetes cluster — it stores all cluster state. Managing it manually is like performing heart surgery on yourself. The etcd-operator is like having a cardiac surgeon on permanent standby: it monitors health, handles emergencies, manages medication (TLS certificates), and performs procedures (upgrades) with zero downtime.

---

## Did You Know?

- [**etcd stores ALL Kubernetes state** — every pod, service, secret, configmap, and custom resource. Lose etcd, lose your cluster. There is no recovery without a backup.](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)

- [**The official etcd-operator v0.2.0** (March 2026) is from the etcd-io project itself](https://github.com/etcd-io/etcd-operator/releases) — not [the archived CoreOS operator](https://github.com/coreos/etcd-operator) that many tutorials still reference. The old CoreOS operator repository is archived.

- **etcd v3.6.0 introduced major improvements** including downgrade support, livez/readyz health endpoints, and improved compaction — the operator manages upgrades to take advantage of these safely.

- **etcd writes require coordination across the cluster**, so disk and network latency often matter more than CPU. Spreading members across nodes improves failure tolerance.

---

## Part 1: Understanding etcd in Kubernetes

### 1.1 What etcd Stores

```
┌─────────────────────────────────────────────────────────────┐
│                    etcd Data Model                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /registry/                                                  │
│  ├── pods/default/nginx-7d4b5c8f9-abc12                     │
│  ├── services/default/kubernetes                             │
│  ├── secrets/kube-system/bootstrap-token-abc123              │
│  ├── configmaps/default/my-config                           │
│  ├── deployments.apps/default/nginx                         │
│  └── customresources/...                                    │
│                                                              │
│  Every kubectl command reads/writes here.                    │
│  API Server is the ONLY client — nothing else talks          │
│  to etcd directly.                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 How the Operator Works

The etcd-operator follows the standard Kubernetes operator pattern: a reconciliation loop that continuously compares desired state (your EtcdCluster spec) with actual state (the running etcd members).

```
┌──────────────────────────────────────────────────────────────┐
│                  etcd-operator Reconciliation Loop             │
│                                                                │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐             │
│   │ Observe   │────▶│  Diff    │────▶│   Act    │             │
│   │           │     │          │     │          │             │
│   │ Read      │     │ Compare  │     │ Create/  │             │
│   │ EtcdCluster│     │ spec vs  │     │ Delete/  │             │
│   │ + check   │     │ actual   │     │ Upgrade  │             │
│   │ member    │     │ members  │     │ members  │             │
│   │ health    │     │          │     │          │             │
│   └──────────┘     └──────────┘     └──────────┘             │
│        ▲                                    │                  │
│        └────────────────────────────────────┘                  │
│                  (repeat every ~10 seconds)                     │
└──────────────────────────────────────────────────────────────┘
```

> **Pause and think**: What happens if one etcd member dies unexpectedly? The operator observes 2/3 members healthy, diffs that against the desired 3, and acts by creating a new member. The new member joins the existing cluster, syncs data via Raft, and quorum is restored — all without human intervention.

### 1.3 Why Operator-Managed etcd?

| Aspect | Manual etcd | etcd-operator |
|--------|------------|---------------|
| TLS certificates | Generate, distribute, rotate manually | [Automated (cert-manager or auto provider)](https://github.com/etcd-io/etcd-operator/releases) |
| Upgrades | Risky manual process, easy to break quorum | Managed with validation, one version at a time |
| Member replacement | Complex manual procedure | Automatic detection and replacement |
| Monitoring | Set up separately | Built-in health checks via reconciliation loop |
| Backup | Cron jobs, hope they work | Integrated snapshot management |

> **When NOT to use an operator**: Use the etcd-operator for clusters where you run etcd yourself. It is not relevant to hosted control planes where you do not manage the backing etcd.

---

## Part 2: etcd-operator v0.2.0

### 2.1 Installation

```bash
# Install the official etcd-io operator (NOT the archived CoreOS one!)
kubectl apply -f https://github.com/etcd-io/etcd-operator/releases/download/v0.2.0/install.yaml

# Verify the operator is running
kubectl get pods -n etcd-operator-system
# NAME                                READY   STATUS    AGE
# etcd-operator-controller-manager    1/1     Running   30s
```

### 2.2 Create an etcd Cluster

```yaml
apiVersion: operator.etcd.io/v1alpha1
kind: EtcdCluster
metadata:
  name: my-etcd
  namespace: default
spec:
  replicas: 3
  version: "3.6.0"
```

```bash
kubectl apply -f etcd-cluster.yaml

# Watch cluster come up
kubectl get etcdcluster my-etcd -w
# NAME      READY   VERSION   AGE
# my-etcd   3/3     3.6.0     2m
```

---

## Part 3: TLS Certificate Management

The operator provides two TLS providers. TLS is opt-in — not enabled by default.

### 3.1 Auto Provider (Development/Testing)

The operator generates self-signed certificates automatically:

```yaml
apiVersion: operator.etcd.io/v1alpha1
kind: EtcdCluster
metadata:
  name: dev-etcd
spec:
  replicas: 3
  version: "3.6.0"
  tls:
    enabled: true
    provider: auto  # Self-signed, auto-rotated
```

### 3.2 cert-manager Provider (Production)

For production, integrate with cert-manager for proper CA-signed certificates:

```yaml
apiVersion: operator.etcd.io/v1alpha1
kind: EtcdCluster
metadata:
  name: prod-etcd
spec:
  replicas: 3
  version: "3.6.0"
  tls:
    enabled: true
    provider: cert-manager
    certManager:
      issuerRef:
        name: etcd-ca-issuer
        kind: ClusterIssuer
```

[This creates certificates for](https://github.com/etcd-io/etcd-operator/releases):
- **Client-to-member** connections (API server → etcd)
- **Inter-member** connections (etcd peer communication)

> **Security Best Practice**: Use cert-manager in production unless you already have an equivalent PKI-integrated certificate workflow. The auto provider is convenient for development but doesn't integrate with your PKI infrastructure or certificate rotation policies.

---

## Part 4: Managed Upgrades

### 4.1 Upgrade Rules

[The operator enforces etcd's official upgrade rules](https://github.com/etcd-io/etcd-operator/releases):

| Upgrade Type | Example | Supported |
|-------------|---------|-----------|
| Patch (same minor) | 3.6.0 → 3.6.2 | Yes |
| Minor (one at a time) | 3.5.x → 3.6.x | Yes |
| Minor (skip) | 3.4.x → 3.6.x | **No — will fail** |
| Major | 3.x → 4.x | Not yet supported |

### 4.2 Performing an Upgrade

```yaml
# Simply update the version field
apiVersion: operator.etcd.io/v1alpha1
kind: EtcdCluster
metadata:
  name: prod-etcd
spec:
  replicas: 3
  version: "3.6.2"  # Changed from 3.6.0
```

The operator:
1. Validates the upgrade path is supported
2. Upgrades one member at a time (rolling)
3. Verifies cluster health after each member
4. Surfaces the failure so you can investigate before proceeding

> **Warning**: Skipping minor versions (e.g., 3.4 → 3.6) is **not supported** and the operator will reject it. Always upgrade one minor version at a time: 3.4 → 3.5 → 3.6.

### 4.3 Troubleshooting Failed Upgrades

```bash
# Check operator logs
kubectl logs -n etcd-operator-system deploy/etcd-operator-controller-manager

# Check etcd cluster status
kubectl get etcdcluster prod-etcd -o yaml

# Check individual member health
kubectl exec -it prod-etcd-0 -- etcdctl endpoint health --cluster
```

---

## Part 5: Comparison with Alternatives

| Feature | etcd-io/etcd-operator (v0.2.0) | aenix-io/etcd-operator (v0.3.0) | Manual Management |
|---------|-------------------------------|--------------------------------|-------------------|
| Official project | Yes (etcd-io) | No (community) | N/A |
| TLS management | Auto + cert-manager | Check current project docs | Manual |
| Managed upgrades | Patch + minor | Check current project docs | Manual |
| Failure testing | gofail integration | Check current project docs | Manual testing required |
| Maturity | Pre-GA (v0.2.0) | Check current release status | Manual operation patterns are well established |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using the archived CoreOS etcd-operator | Archived and not the current project | Use etcd-io/etcd-operator (official) |
| Skipping minor versions in upgrades | Operator rejects, or data corruption risk | Always upgrade one minor at a time |
| Running all etcd members on same node | Single point of failure | Use pod anti-affinity rules |
| No TLS in production | etcd traffic unencrypted on network | Enable TLS with cert-manager provider |
| Confusing operator version with etcd version | Wrong version in spec | Check the operator release notes for supported etcd versions |
| No etcd backups | Total data loss on cluster failure | Configure periodic snapshots |

---

## Quiz

1. **Your 3-member etcd cluster shows 2/3 READY. The operator hasn't replaced the failed member after 5 minutes. What would you check and why?**
   <details>
   <summary>Answer</summary>
   First, check the operator logs (`kubectl logs -n etcd-operator-system deploy/etcd-operator-controller-manager`) for errors in the reconciliation loop. Common causes: insufficient cluster resources to schedule a new pod (check `kubectl describe pod` for Pending events), PVC binding failure if the storage class can't provision a new volume, or the operator itself being unhealthy. Also check if the failed member left data corruption that prevents the new member from joining — look at etcd member logs for Raft errors.
   </details>

2. **You inherited a cluster running the CoreOS etcd-operator (github.com/coreos/etcd-operator). A security audit flagged it. Why is this a risk, and what's the migration path?**
   <details>
   <summary>Answer</summary>
   The CoreOS operator has been archived and unmaintained since 2019 — it has known CVEs that will never be patched, uses deprecated APIs, and doesn't support recent etcd versions. The migration path: deploy the official etcd-io operator alongside the old one, create a new EtcdCluster CR, restore from a snapshot of the old cluster into the new operator-managed cluster, verify data integrity, then redirect the API server's `--etcd-servers` flag to the new endpoints. This is a high-risk operation that should be rehearsed in staging first.
   </details>

3. **Your team wants to upgrade etcd from 3.4.28 to 3.6.0 to get the new livez/readyz health endpoints. You update the EtcdCluster spec to version "3.6.0" and apply it. What happens?**
   <details>
   <summary>Answer</summary>
   The operator rejects the upgrade because you're skipping minor version 3.5. etcd only supports upgrading one minor version at a time — this is a Raft consensus safety requirement, not an operator limitation. You must upgrade 3.4.28 → 3.5.x first, verify cluster health, then 3.5.x → 3.6.0. Each step involves a rolling restart of all members. The operator enforces this to prevent data corruption that could occur from incompatible Raft protocol versions.
   </details>

4. **You're choosing between the `auto` and `cert-manager` TLS providers for a production etcd cluster that processes financial transactions. Which do you choose and why?**
   <details>
   <summary>Answer</summary>
   cert-manager, without question. The auto provider generates self-signed certificates that don't integrate with your organization's PKI infrastructure, can't be audited by security tools that expect CA-signed certs, and don't follow certificate rotation policies mandated by compliance frameworks (PCI-DSS, SOC 2). cert-manager integrates with your existing certificate authority, supports automated rotation, and provides an audit trail. The auto provider is fine for development and testing where speed matters more than security posture.
   </details>

5. **A junior engineer asks: "We're on EKS — should we deploy the etcd-operator?" How do you respond?**
   <details>
   <summary>Answer</summary>
   No. On managed Kubernetes (EKS, GKE, AKS), the cloud provider manages the etcd cluster as part of the control plane. You have no access to etcd directly, and the provider handles high availability, backups, upgrades, and TLS. The etcd-operator is designed for self-managed clusters — bare metal, kubeadm, or on-premises — where you own and operate the control plane yourself. Deploying it on EKS would create a separate etcd cluster that Kubernetes doesn't use, wasting resources and adding confusion.
   </details>

---

## Hands-On Exercise

**Deploy and Upgrade an etcd Cluster**

```bash
# 1. Install the operator
kubectl apply -f https://github.com/etcd-io/etcd-operator/releases/download/v0.2.0/install.yaml

# 2. Create a 3-member cluster with TLS
cat <<EOF | kubectl apply -f -
apiVersion: operator.etcd.io/v1alpha1
kind: EtcdCluster
metadata:
  name: exercise-etcd
spec:
  replicas: 3
  version: "3.5.12"
  tls:
    enabled: true
    provider: auto
EOF

# 3. Wait for cluster to be ready
kubectl get etcdcluster exercise-etcd -w

# 4. Verify cluster health
kubectl exec -it exercise-etcd-0 -- etcdctl endpoint health --cluster

# 5. Write and read data
kubectl exec -it exercise-etcd-0 -- etcdctl put /test/key "hello from etcd-operator"
kubectl exec -it exercise-etcd-0 -- etcdctl get /test/key

# 6. Upgrade to 3.6.0
kubectl patch etcdcluster exercise-etcd --type merge -p '{"spec":{"version":"3.6.0"}}'

# 7. Watch the rolling upgrade
kubectl get pods -w

# 8. Verify data survived the upgrade
kubectl exec -it exercise-etcd-0 -- etcdctl get /test/key

# 9. Troubleshooting Challenge: The Illegal Jump
# Try an unsupported version skip (3.6.0 → 3.8.0) — this SHOULD fail
kubectl patch etcdcluster exercise-etcd --type merge -p '{"spec":{"version":"3.8.0"}}'

# Check the status — look for validation error
kubectl describe etcdcluster exercise-etcd | grep -A5 "Warning"

# Check operator logs for the rejection reason
kubectl logs -n etcd-operator-system deploy/etcd-operator-controller-manager | grep -i "unsupported\|validation\|upgrade"

# 10. Cleanup
kubectl delete etcdcluster exercise-etcd
kubectl delete -f https://github.com/etcd-io/etcd-operator/releases/download/v0.2.0/install.yaml
```

**Success Criteria:**
- [ ] 3-member etcd cluster running with TLS
- [ ] Data written and read successfully
- [ ] Rolling upgrade from 3.5 to 3.6 completed without data loss
- [ ] Cluster health verified after upgrade

---

## Next Module

[Back to Cloud-Native Databases Overview]()

## Sources

- [Operating etcd clusters for Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/) — Backs claims that etcd is Kubernetes' backing store for all cluster data, that production setups should use odd-sized multi-node clusters with backups, and that etcd reliability directly affects control-plane behavior.
- [Releases: etcd-io/etcd-operator](https://github.com/etcd-io/etcd-operator/releases) — Backs claims about the current official etcd-io operator release line, including v0.2.0 features such as certificate management, TLS-secured clusters, scaling, and upgrade support.
- [Archived coreos/etcd-operator repository](https://github.com/coreos/etcd-operator) — Backs historical claims that the old CoreOS etcd operator is archived and documents its older feature set like failover, rolling upgrades, and backup/restore.
- [etcd CHANGELOG-3.6](https://github.com/etcd-io/etcd/blob/main/CHANGELOG/CHANGELOG-3.6.md) — Useful upstream release detail for version-specific etcd 3.6 behavior and upgrade-related changes.

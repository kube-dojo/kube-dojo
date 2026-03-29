---
title: "Module 15.5: etcd-operator - Managing Kubernetes' Backbone"
slug: platform/toolkits/data-ai-platforms/cloud-native-databases/module-15.5-etcd-operator
sidebar:
  order: 6
---
## Complexity: [MEDIUM]
## Time to Complete: 40-45 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 15.1: CockroachDB](module-15.1-cockroachdb/) - Distributed consensus concepts
- Kubernetes fundamentals (CRDs, Operators, StatefulSets)
- CKA etcd knowledge (backup, restore, cluster health)
- [Reliability Engineering Foundation](../../foundations/reliability-engineering/) - HA concepts

---

## Why This Module Matters

**The Cluster That Forgot Everything**

The SRE team at a fintech processing $2.1B in daily transactions got the alert at 3:12 AM: etcd leader election was failing. Three etcd members, all running on the same rack, had lost quorum when a switch firmware update went wrong. Without etcd, the Kubernetes API server became read-only — no new pods, no scaling, no deployments. The blast radius was total: 847 microservices frozen in place.

Recovery took 4 hours and 23 minutes. Manual etcd restoration from a snapshot that was 6 hours stale. They lost 6 hours of ConfigMap updates, Secret rotations, and custom resource state. The post-incident review calculated $890K in direct losses and 3 SLA violations.

Six months later, after deploying the etcd-operator with automated TLS, anti-affinity rules, and managed upgrades, a similar network event caused zero downtime — the operator detected the unhealthy member, replaced it, and restored quorum in 47 seconds.

> **The Heart Transplant Analogy**
>
> etcd is the heart of every Kubernetes cluster — it stores all cluster state. Managing it manually is like performing heart surgery on yourself. The etcd-operator is like having a cardiac surgeon on permanent standby: it monitors health, handles emergencies, manages medication (TLS certificates), and performs procedures (upgrades) with zero downtime.

---

## Did You Know?

- **etcd stores ALL Kubernetes state** — every pod, service, secret, configmap, and custom resource. Lose etcd, lose your cluster. There is no recovery without a backup.

- **The official etcd-operator v0.2.0** (March 2026) is from the etcd-io project itself — not the archived CoreOS operator that many tutorials still reference. The old CoreOS operator hasn't been maintained since 2019.

- **etcd v3.6.0 introduced major improvements** including downgrade support, livez/readyz health endpoints, and improved compaction — the operator manages upgrades to take advantage of these safely.

- **A single etcd write takes 3 network round trips** (leader propose → follower replicate → commit). This is why etcd performance is dominated by disk and network latency, not CPU. The operator's anti-affinity rules ensure members are on different nodes to survive hardware failures without sacrificing latency.

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

### 1.2 Why Operator-Managed etcd?

| Aspect | Manual etcd | etcd-operator |
|--------|------------|---------------|
| TLS certificates | Generate, distribute, rotate manually | Automated (cert-manager or auto provider) |
| Upgrades | Risky manual process, easy to break quorum | Managed with validation, one version at a time |
| Member replacement | Complex manual procedure | Automatic detection and replacement |
| Monitoring | Set up separately | Built-in health checks |
| Backup | Cron jobs, hope they work | Integrated snapshot management |

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

This creates certificates for:
- **Client-to-member** connections (API server → etcd)
- **Inter-member** connections (etcd peer communication)

> **Security Best Practice**: Always use cert-manager in production. The auto provider is convenient for development but doesn't integrate with your PKI infrastructure or certificate rotation policies.

---

## Part 4: Managed Upgrades

### 4.1 Upgrade Rules

The operator enforces etcd's official upgrade rules:

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
4. Rolls back on failure

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
| TLS management | Auto + cert-manager | cert-manager | Manual |
| Managed upgrades | Patch + minor | Patch + minor | Manual |
| Failure testing | gofail integration | Limited | None |
| Maturity | Pre-GA (v0.2.0) | Pre-GA (v0.3.0) | Proven |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using the archived CoreOS etcd-operator | Unmaintained since 2019, security risks | Use etcd-io/etcd-operator (official) |
| Skipping minor versions in upgrades | Operator rejects, or data corruption risk | Always upgrade one minor at a time |
| Running all etcd members on same node | Single point of failure | Use pod anti-affinity rules |
| No TLS in production | etcd traffic unencrypted on network | Enable TLS with cert-manager provider |
| Confusing operator version with etcd version | Wrong version in spec | Operator v0.2.0 manages etcd v3.5.x/v3.6.x |
| No etcd backups | Total data loss on cluster failure | Configure periodic snapshots |

---

## Quiz

1. **What's the difference between the etcd-io operator and the CoreOS operator?**
   <details>
   <summary>Answer</summary>
   The CoreOS etcd-operator (github.com/coreos/etcd-operator) has been archived and unmaintained since 2019. The etcd-io operator (github.com/etcd-io/etcd-operator) is the official, actively maintained operator from the etcd project itself.
   </details>

2. **Can you upgrade etcd from 3.4 directly to 3.6?**
   <details>
   <summary>Answer</summary>
   No. etcd only supports upgrading one minor version at a time. You must go 3.4 → 3.5 → 3.6. The operator validates this and will reject the upgrade if you try to skip.
   </details>

3. **What are the two TLS providers in etcd-operator v0.2.0?**
   <details>
   <summary>Answer</summary>
   **Auto** (self-signed, for development/testing) and **cert-manager** (CA-signed, for production). TLS is opt-in and covers both client-to-member and inter-member communication.
   </details>

4. **Why is pod anti-affinity important for etcd?**
   <details>
   <summary>Answer</summary>
   etcd requires a quorum (majority of members) to function. If all members run on the same node and that node fails, you lose quorum and the entire cluster becomes read-only. Anti-affinity ensures members are spread across different nodes.
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

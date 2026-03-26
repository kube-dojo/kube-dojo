---
title: "Module 8.1: Multi-Site & Disaster Recovery"
slug: on-premises/resilience/module-8.1-multi-site-dr
sidebar:
  order: 2
---

> **Complexity**: `[ADVANCED]` | Time: 60 minutes
>
> **Prerequisites**: [Cluster Topology Planning](../../on-premises/planning/module-1.3-cluster-topology/), [Storage Architecture](../../on-premises/storage/module-4.1-storage-architecture/)

---

## Why This Module Matters

In March 2021, a fire destroyed OVHcloud's SBG2 datacenter in Strasbourg, France. Thousands of customers lost data permanently. One e-commerce company running Kubernetes on bare metal in that single facility lost their entire cluster -- etcd data, persistent volumes, application state, everything. They had backups, but the backups were stored on the same physical infrastructure. Recovery took 11 days. Revenue loss exceeded 2 million euros.

Six months later, a logistics company in the same datacenter came through the same fire with zero data loss and four minutes of downtime. They ran an active-passive Kubernetes setup across two sites, with Velero backing up to S3-compatible storage in a different facility, etcd snapshots replicated every 15 minutes, and DNS-based failover that redirected traffic within 90 seconds.

Disaster recovery is not a feature you add later. It is a design decision you make on day one.

> **The Insurance Analogy**
>
> DR is like fire insurance. You pay every month and hope you never need it. Companies that skip DR save money every quarter until the quarter they lose everything.

---

## What You'll Learn

- The difference between active-active and active-passive datacenter topologies
- Why stretched etcd clusters have a hard 10ms RTT latency limit
- How to define and measure RTO and RPO
- Velero with MinIO for S3-compatible backup and restore
- etcd snapshot backup and restore procedures
- DNS-based failover between sites

---

## Active-Active vs Active-Passive

```
ACTIVE-ACTIVE                          ACTIVE-PASSIVE

  Site A          Site B               Site A          Site B
  ┌────────┐    ┌────────┐            ┌────────┐    ┌────────┐
  │ etcd   │◄──►│ etcd   │  <10ms    │ etcd   │──►│(standby)│
  │ Workers│    │ Workers│  RTT      │ Workers│    │ Velero  │
  └───┬────┘    └───┬────┘            └───┬────┘    │ restore │
      └──────┬──────┘                     │         └────────┘
        Global LB                      DNS failover
```

| Factor | Active-Active | Active-Passive |
|--------|--------------|----------------|
| **Failover time** | Seconds (DNS TTL) | Minutes to hours |
| **Data consistency** | Synchronous (stretched etcd) | Asynchronous (backup lag) |
| **Network requirement** | <10ms RTT between sites | Any bandwidth |
| **Cost** | 2x infrastructure | 1.3-1.5x (standby can be smaller) |
| **Data loss risk (RPO)** | Near zero | Minutes to hours |
| **Best for** | Finance, real-time systems | Most enterprises |

**Active-active** requires: RPO=0, RTO<60s, sites within 10ms RTT, budget for 2x infra.

**Active-passive** works when: RPO of 15-60 min is acceptable, sites are distant, budget is constrained.

---

## Stretched Clusters and the etcd Latency Wall

A stretched cluster runs a single Kubernetes control plane across two sites. The etcd quorum spans both. Every write must be acknowledged by a majority of etcd members before it is committed.

```
etcd WRITE IN A STRETCHED CLUSTER

  API Server (Site A) ──► etcd Leader (Site A) ──► Replicate
                               │                        │
                          etcd M2 (A)             etcd M3 (B)
                          ACK: 0.1ms              ACK: 4ms (RTT)
                               │                        │
                          Quorum reached ◄──────────────┘
                          Total latency: ~5ms (if RTT=4ms)
```

| RTT Between Sites | etcd Behavior | Recommendation |
|-------------------|---------------|----------------|
| <2ms | Excellent | Same rack / same building |
| 2-5ms | Good, slight latency increase | Same campus / metro |
| 5-10ms | Acceptable with tuning | Same metro, dedicated fiber |
| 10-20ms | Degraded, leader election risk | Not recommended |
| >20ms | Unstable, split brain risk | Do not stretch etcd |

For 5-10ms RTT, tune etcd to compensate:

```yaml
# /etc/kubernetes/manifests/etcd.yaml
spec:
  containers:
  - name: etcd
    command:
    - etcd
    - --heartbeat-interval=250       # Default: 100ms
    - --election-timeout=2500        # Default: 1000ms
    - --snapshot-count=10000
    - --listen-metrics-urls=http://0.0.0.0:2381
```

---

## RTO and RPO

```
  Disaster       RPO Window           Recovery      RTO Window
     │◄──────────►│                      │◄──────────►│
     │  Data loss  │                     │  Downtime   │

  RPO: "How much data can we lose?"    RTO: "How long until operational?"
  RPO=0    → stretched cluster          RTO=0    → active-active
  RPO=15m  → backup every 15 min       RTO=5m   → hot standby
  RPO=1h   → hourly snapshots          RTO=24h  → cold restore
```

| Workload | RPO | RTO | DR Approach |
|----------|-----|-----|-------------|
| Payment processing | 0 | <60s | Active-active, stretched etcd |
| E-commerce | 5 min | 15 min | Hot standby, async replication |
| Internal tools | 1 hour | 4 hours | Warm standby, Velero |
| Dev/staging | 24 hours | 24 hours | Daily backups, cold restore |

---

## Velero with MinIO for Backup

```
  K8s Cluster (Site A)                MinIO (Site B)
  ┌──────────────────┐                ┌──────────────────┐
  │ Velero Server     │──S3 API──────►│ velero-backups/   │
  │  - K8s resources  │               │  ├── daily-03-25/ │
  │  - PV data (fs)   │               │  ├── daily-03-24/ │
  └──────────────────┘                └──────────────────┘
```

### Install and Configure

```bash
# Create Velero credentials
cat > /tmp/velero-credentials <<EOF
[default]
aws_access_key_id=velero-user
aws_secret_access_key=S3cur3P@ssw0rd
EOF

# Install Velero pointing to MinIO
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups \
  --secret-file /tmp/velero-credentials \
  --backup-location-config \
    region=us-east-1,s3ForcePathStyle=true,s3Url=https://minio.site-b.example.com \
  --use-node-agent \
  --default-volumes-to-fs-backup

# Schedule backups
velero schedule create full-cluster \
  --schedule="0 */6 * * *" --ttl 168h0m0s \
  --include-namespaces '*' --default-volumes-to-fs-backup

velero schedule create critical-apps \
  --schedule="0 * * * *" --ttl 48h0m0s \
  --include-namespaces production,payments,database

# Restore to DR site
velero restore create --from-backup full-cluster-20260325060000
```

---

## etcd Snapshot Backup and Restore

Velero backs up at the API level. etcd snapshots capture the entire cluster state at the storage level. Use both -- they serve different recovery scenarios. Velero lets you restore individual namespaces or resources. etcd snapshots restore the entire cluster state in one operation.

### Taking and Verifying Snapshots

```bash
# Take a snapshot on a control plane node
ETCDCTL_API=3 etcdctl snapshot save /var/lib/etcd-backup/snapshot-$(date +%Y%m%d-%H%M%S).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify the snapshot integrity
ETCDCTL_API=3 etcdctl snapshot status /var/lib/etcd-backup/snapshot-latest.db --write-out=table
# +----------+----------+------------+------------+
# |   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
# +----------+----------+------------+------------+
# | 3e6d789a |   458203 |       1847 |     5.2 MB |
# +----------+----------+------------+------------+
```

### Automate with a CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: etcd-snapshot
  namespace: kube-system
spec:
  schedule: "*/15 * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          nodeSelector:
            node-role.kubernetes.io/control-plane: ""
          tolerations:
          - key: node-role.kubernetes.io/control-plane
            effect: NoSchedule
          hostNetwork: true
          containers:
          - name: etcd-backup
            image: registry.k8s.io/etcd:3.5.15-0
            command: ["/bin/sh", "-c"]
            args:
            - |
              SNAPSHOT="/backups/snapshot-$(date +%Y%m%d-%H%M%S).db"
              etcdctl snapshot save "$SNAPSHOT" \
                --endpoints=https://127.0.0.1:2379 \
                --cacert=/etc/kubernetes/pki/etcd/ca.crt \
                --cert=/etc/kubernetes/pki/etcd/server.crt \
                --key=/etc/kubernetes/pki/etcd/server.key
              ls -t /backups/snapshot-*.db | tail -n +21 | xargs rm -f
            volumeMounts:
            - name: etcd-certs
              mountPath: /etc/kubernetes/pki/etcd
              readOnly: true
            - name: backup-dir
              mountPath: /backups
          restartPolicy: OnFailure
          volumes:
          - name: etcd-certs
            hostPath:
              path: /etc/kubernetes/pki/etcd
          - name: backup-dir
            hostPath:
              path: /var/lib/etcd-backup
```

### Restore from Snapshot

```bash
# CRITICAL: Stop API server and etcd on ALL control plane nodes first
sudo mv /var/lib/etcd /var/lib/etcd.bak

ETCDCTL_API=3 etcdctl snapshot restore /var/lib/etcd-backup/snapshot-latest.db \
  --name=cp-1 \
  --initial-cluster=cp-1=https://10.0.1.10:2380,cp-2=https://10.0.1.11:2380,cp-3=https://10.0.1.12:2380 \
  --initial-cluster-token=etcd-cluster-1 \
  --initial-advertise-peer-urls=https://10.0.1.10:2380 \
  --data-dir=/var/lib/etcd

# Repeat on each CP node with its own --name and --initial-advertise-peer-urls
# Then restart kubelet on all control plane nodes
sudo systemctl restart kubelet
```

---

## DNS-Based Failover

```
  Client ──► Authoritative DNS (PowerDNS)
             ┌─────────────────────────────┐
             │ app.example.com              │
             │   Site A: 10.0.1.100 (100)  │ ◄── health checks
             │   Site B: 10.1.1.100 (0)    │
             │                              │
             │   If Site A fails:           │
             │   Site B: 10.1.1.100 (100)  │
             └─────────────────────────────┘
```

| Setting | Value | Reason |
|---------|-------|--------|
| DNS TTL | 30-60 seconds | Faster failover, more DNS queries |
| Health check interval | 10 seconds | Detect failures quickly |
| Failure threshold | 3 consecutive | Avoid flapping |
| Recovery threshold | 5 consecutive | Ensure stability before failback |

> **Warning**: DNS TTL is a suggestion, not a command. Budget for 2-5 minutes of stale DNS in your RTO, even with a 30-second TTL.

---

## Did You Know?

1. **etcd stores everything twice.** Every key lives in both a B-tree index and BoltDB. A 5MB snapshot contains ~2.5MB of unique data. The API server also caches resources in memory, so the cluster state exists in three places simultaneously.

2. **The largest known stretched Kubernetes cluster** spans two datacenters 40km apart on dark fiber with 0.8ms RTT, running over 2,000 nodes. The team spent six months tuning before production. Most organizations that attempt this scale fail within the first year.

3. **Velero was originally "Heptio Ark"**, created by the company founded by Kubernetes co-creators Joe Beda and Craig McLuckie. Renamed after VMware's 2018 acquisition, "Velero" is Spanish for "sailboat."

4. **A 500-node cluster's etcd snapshot** is typically 50-150MB yet contains every Kubernetes resource. This compact size makes etcd snapshots the fastest restore path, often completing in under 30 seconds.

---

## Common Mistakes

| Mistake | Why It Happens | What To Do Instead |
|---------|---------------|-------------------|
| Backing up to the same site | Convenience | Store backups in a separate failure domain from day one |
| DNS TTL too high | Defaults are 300-3600s | Set 30-60s for failover records |
| Never testing DR | "We have backups" | Run quarterly DR drills with actual restores |
| Stretching etcd over high latency | Wanting active-active | Use active-passive if RTT >10ms |
| Ignoring PV data in backups | Velero defaults to resource-only | Enable `--default-volumes-to-fs-backup` |
| Single backup method | Relying on only Velero or only etcd | Use both for different recovery scenarios |

---

## Quiz

### Question 1
Two datacenters 300km apart, 12ms RTT. You want zero-RPO DR. Is stretched etcd appropriate?

<details>
<summary>Answer</summary>

No. 12ms exceeds the 10ms limit. Under load, etcd will miss heartbeats and trigger leader elections. For this distance, use active-passive with RPO of 1-5 minutes via frequent Velero backups and etcd snapshots shipped to the remote site. For zero RPO on data, consider application-level replication (PostgreSQL streaming, Ceph stretch mode).
</details>

### Question 2
Velero runs hourly backups. A developer deletes `production` namespace at 10:42. Last backup: 10:00. What is the data loss and how do you improve?

<details>
<summary>Answer</summary>

Data loss: 42 minutes of changes. Improvements: (1) increase backup frequency for critical namespaces to every 15 minutes, (2) add RBAC preventing namespace deletion by developers, (3) deploy a ValidatingWebhook rejecting deletion of namespaces labeled `protected: "true"`, (4) complement with etcd snapshots every 15 minutes.
</details>

### Question 3
After Velero restore to DR cluster, pods run but services return 503. Most likely causes?

<details>
<summary>Answer</summary>

(1) EndpointSlices not yet populated -- pods still starting. (2) PV data not restored if `--default-volumes-to-fs-backup` was not set. (3) CoreDNS not operational yet. (4) Missing Secrets/ConfigMaps if backup excluded namespaces. (5) Node affinity constraints failing on different node labels. (6) External dependencies still pointing to primary site.
</details>

### Question 4
Design DR for: 200-node cluster, two DCs 50km apart (3ms RTT), payment processing (RPO=0, RTO<60s) and batch analytics (RPO=4h, RTO=24h).

<details>
<summary>Answer</summary>

Tiered strategy. **Payments**: stretched etcd (3ms is safe), pods in both sites via topologySpreadConstraints, synchronous storage replication, DNS GSLB with 30s TTL. **Analytics**: Velero every 4 hours to MinIO at Site B, manual failover. **Layout**: etcd 2 members Site A + 1 Site B, 120 workers Site A + 80 Site B, payment pods across both, analytics pods Site A only. **Testing**: monthly payment failover drill, quarterly full DR exercise.
</details>

---

## Hands-On Exercise: Velero DR Pipeline

**Objective**: Set up Velero with MinIO across two kind clusters and practice backup-restore.

```bash
# 1. Create two clusters and run MinIO
kind create cluster --name site-a
kind create cluster --name site-b
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  quay.io/minio/minio server /data --console-address ":9001"

# 2. Install Velero on site-a and deploy a sample app
kubectl config use-context kind-site-a
cat > /tmp/credentials-velero <<EOF
[default]
aws_access_key_id = minioadmin
aws_secret_access_key = minioadmin
EOF
velero install --provider aws --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups --secret-file /tmp/credentials-velero \
  --backup-location-config region=us-east-1,s3ForcePathStyle=true,s3Url=http://host.docker.internal:9000 \
  --use-node-agent
kubectl create namespace demo-app
kubectl create deployment nginx --image=nginx:1.27 -n demo-app --replicas=3
velero backup create site-a-full --include-namespaces demo-app --wait

# 3. Install Velero on site-b and restore
kubectl config use-context kind-site-b
velero install --provider aws --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups --secret-file /tmp/credentials-velero \
  --backup-location-config region=us-east-1,s3ForcePathStyle=true,s3Url=http://host.docker.internal:9000 \
  --use-node-agent
velero restore create --from-backup site-a-full --wait
kubectl get pods -n demo-app
```

### Success Criteria
- [ ] Velero installed on both clusters pointing to same MinIO
- [ ] Backup created on site-a containing demo-app namespace
- [ ] Restore completed on site-b with all resources present
- [ ] Pods running on site-b match the deployment from site-a

---

## Next Module

Continue to [Module 8.2: Hybrid Cloud Connectivity](../resilience/module-8.2-hybrid-connectivity/) to learn how to connect on-premises clusters to cloud environments using VPNs, direct interconnects, and multi-cluster networking.

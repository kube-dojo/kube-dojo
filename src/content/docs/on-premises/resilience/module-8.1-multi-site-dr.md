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

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Design** multi-site disaster recovery architectures (active-passive, active-active) with defined RPO and RTO targets
2. **Implement** cross-site backup pipelines using Velero with off-site S3-compatible storage and etcd snapshot replication
3. **Configure** DNS-based failover and traffic switching procedures that redirect users to surviving sites within minutes
4. **Plan** DR testing runbooks with regular failover drills that validate recovery procedures before an actual disaster

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

> **Pause and predict**: Your two datacenters are 50km apart with 3ms RTT. Your payment system requires RPO=0 (zero data loss). Can you use a stretched etcd cluster across both sites, or do you need a different approach?

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

> **Stop and think**: Velero backs up at the Kubernetes API level (resources and optionally PV data). etcd snapshots capture the entire cluster state at the storage level. Why would you use both? What recovery scenario does each one handle that the other cannot?

### Install and Configure

Velero uses the S3 API to store backups on MinIO at the DR site. The `--use-node-agent` flag enables file-system-level PV backups, and `--default-volumes-to-fs-backup` ensures PersistentVolume data is included in every backup.

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

Always verify snapshot integrity immediately after creation. A corrupt snapshot is worse than no snapshot -- it gives a false sense of security. The `snapshot status` command confirms the hash, revision, key count, and size.

```bash
# Take a snapshot on a control plane node
ETCDCTL_API=3 etcdctl snapshot save /var/lib/etcd-backup/snapshot-latest.db \
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

etcdutl snapshot restore /var/lib/etcd-backup/snapshot-latest.db \
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

## DR Testing Runbooks and Failover Drills

A disaster recovery plan is only theoretical until it is tested. Regular DR drills validate both the technical recovery procedures and the human runbooks.

### Building the Runbook

Your DR runbook should be a step-by-step document that assumes the reader is sleep-deprived and stressed. It must include:

1. **Declaration Criteria**: Who can declare a disaster? What are the criteria (e.g., site down for >15 minutes)?
2. **Communication Plan**: Which Slack/Teams channels, phone bridges, and status pages to use.
3. **Technical Steps**: Exact commands (like the `etcdutl snapshot restore` and `velero restore` commands) with expected output.
4. **Validation Checklist**: How to verify that the restored applications are actually functioning.

### Drill Cadence

- **Monthly Tabletop**: The team talks through a disaster scenario and the runbook steps without touching keyboards.
- **Quarterly Component Drill**: Fail over a single component to validate the pipeline.
- **Annual Full-Scale Drill**: Fail over the entire primary site to the DR site, run production from DR for a set period, and fail back.

Always document lessons learned from drills and update the runbook immediately.

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
Your company operates two datacenters 300km apart with 12ms RTT. The CTO demands zero-RPO disaster recovery for your Kubernetes-based payment processing system. An architect proposes a stretched etcd cluster across both sites. Should you approve this design?

<details>
<summary>Answer</summary>

**No. A stretched etcd cluster at 12ms RTT will be unstable and should not be used.**

The 12ms round-trip time exceeds etcd's practical 10ms limit. Every write to etcd requires a quorum acknowledgment from members at the remote site. Under load, the added latency causes the etcd leader to miss heartbeat deadlines, triggering leader elections. Frequent leader elections cause API server timeouts, failed pod scheduling, and degraded cluster health -- the opposite of high availability.

**For zero RPO on the payment data specifically**, use application-level synchronous replication (PostgreSQL streaming replication or CockroachDB) rather than trying to achieve it at the Kubernetes infrastructure level. Kubernetes state (Deployments, Services) can tolerate 1-5 minutes of RPO because it is declarative and can be reapplied.

**Recommended architecture**: active-passive with Velero backups every 15 minutes to MinIO at the remote site, etcd snapshots replicated every 15 minutes, and DNS-based failover with a 30-second TTL. This gives RPO of 15 minutes for Kubernetes state and RPO of 0 for the payment database via synchronous replication.
</details>

### Question 2
Your on-premises cluster uses Velero with hourly backup schedules. At 10:42 AM, a developer accidentally runs `kubectl delete namespace production`, wiping all resources in the production namespace. The last Velero backup completed at 10:00 AM. What is the data loss, and how would you prevent this from happening again?

<details>
<summary>Answer</summary>

**Data loss: 42 minutes of changes to the production namespace** -- any Deployments, ConfigMaps, Secrets, or PVCs created or modified between 10:00 and 10:42 are gone from the backup. PersistentVolume data depends on whether `--default-volumes-to-fs-backup` was enabled.

**Immediate recovery**: Restore from the 10:00 backup targeting only the production namespace: `velero restore create --from-backup <latest> --include-namespaces production`. This restores resources to their 10:00 state. Any changes made between 10:00-10:42 must be reapplied manually or via GitOps reconciliation.

**Prevention (defense in depth)**:
1. **Increase backup frequency** for critical namespaces to every 15 minutes, reducing maximum data loss from 60 to 15 minutes.
2. **RBAC**: Remove namespace deletion permission from developer roles. Only platform-admin roles should be able to delete namespaces.
3. **Admission control**: Deploy a ValidatingWebhookConfiguration or Kyverno policy that rejects deletion of namespaces labeled `protected: "true"`.
4. **etcd snapshots**: Run every 15 minutes as a complementary backup mechanism for full cluster state recovery.
5. **GitOps**: If all manifests are in Git (Flux/ArgoCD), the reconciliation loop will automatically recreate deleted resources -- though PV data is still lost.
</details>

### Question 3
During a DR drill, you restore your on-premises cluster from a Velero backup to the DR site. Pods start running, but services return 503 errors. Users cannot access the application. Walk through your troubleshooting process.

<details>
<summary>Answer</summary>

**503 errors after Velero restore indicate that traffic is reaching the cluster but services cannot serve requests.** Troubleshoot layer by layer:

1. **EndpointSlices not populated yet**: Pods may be starting but not yet Ready. The Kubernetes endpoints controller only adds pods to EndpointSlices when their readiness probes pass. Check: `kubectl get endpointslices -n production` -- if empty, wait for pods to pass readiness checks.

2. **PV data not restored**: If `--default-volumes-to-fs-backup` was not set during the original backup, PVCs were restored as empty volumes. Databases, caches, and file-based services would start with no data. Check: `kubectl get pvc -n production` and verify the volumes contain data.

3. **CoreDNS not operational**: If CoreDNS pods are still starting, in-cluster DNS resolution fails, so services cannot find their backends. Check: `kubectl get pods -n kube-system -l k8s-app=kube-dns`.

4. **Missing Secrets/ConfigMaps**: If the backup excluded certain namespaces (e.g., `kube-system`), TLS certificates or configuration may be missing. Check: `kubectl get secrets -n production` and compare against what the application expects.

5. **Node affinity mismatches**: The DR cluster may have different node labels than the primary. Pods with node affinity rules may be stuck in Pending. Check: `kubectl get pods -A --field-selector status.phase=Pending`.

6. **External dependencies**: Applications may hardcode primary-site endpoints (databases, APIs, external services). These endpoints are unreachable from the DR site. Check application logs for connection timeouts.
</details>

### Question 4
Design DR for: 200-node cluster, two DCs 50km apart (3ms RTT), payment processing (RPO=0, RTO<60s) and batch analytics (RPO=4h, RTO=24h).

<details>
<summary>Answer</summary>

Tiered strategy. **Payments**: stretched etcd (3ms is safe), pods in both sites via topologySpreadConstraints, synchronous storage replication, DNS GSLB with 30s TTL. **Analytics**: Velero every 4 hours to MinIO at Site B, manual failover. **Layout**: etcd 3 members Site A + 2 Site B (5-member cluster ensures quorum survives losing either site's minority; odd total avoids split-brain), 120 workers Site A + 80 Site B, payment pods across both, analytics pods Site A only. **Testing**: monthly payment failover drill, quarterly full DR exercise.
</details>

---

## Hands-On Exercise: Velero DR Pipeline

**Objective**: Set up Velero with MinIO across two kind clusters and practice backup-restore.

```bash
# 1. Create two clusters and run MinIO
kind create cluster --name site-a
kind create cluster --name site-b
docker run -d --name minio --network kind -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  quay.io/minio/minio server /data --console-address ":9001"
docker exec minio mkdir -p /data/velero-backups

# Ensure the Velero CLI is installed on your local machine before proceeding.
# See: https://velero.io/docs/main/basic-install/

# 2. Install Velero on site-a and deploy a sample app
kubectl config use-context kind-site-a
cat > /tmp/credentials-velero <<EOF
[default]
aws_access_key_id = minioadmin
aws_secret_access_key = minioadmin
EOF
velero install --provider aws --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups --secret-file /tmp/credentials-velero \
  --backup-location-config region=us-east-1,s3ForcePathStyle=true,s3Url=http://minio:9000 \
  --use-node-agent
kubectl create namespace demo-app
kubectl create deployment nginx --image=nginx:1.27 -n demo-app --replicas=3

# Wait for Velero to be ready before backing up
kubectl wait --for=condition=available deployment/velero -n velero --timeout=300s
kubectl wait --for=condition=available deployment/nginx -n demo-app --timeout=120s

velero backup create site-a-full --include-namespaces demo-app --wait

# 3. Install Velero on site-b and restore
kubectl config use-context kind-site-b
velero install --provider aws --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups --secret-file /tmp/credentials-velero \
  --backup-location-config region=us-east-1,s3ForcePathStyle=true,s3Url=http://minio:9000 \
  --use-node-agent

# Wait for Velero to be ready before restoring
kubectl wait --for=condition=available deployment/velero -n velero --timeout=300s

# Wait for the backup to sync from MinIO before restoring
while ! velero backup get site-a-full &>/dev/null; do sleep 5; done

velero restore create --from-backup site-a-full --wait

# Verify restored application is ready
kubectl wait --for=condition=available deployment/nginx -n demo-app --timeout=120s
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

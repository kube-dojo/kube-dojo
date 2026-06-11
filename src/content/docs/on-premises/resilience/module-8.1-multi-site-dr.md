---
revision_pending: true
title: "Module 8.1: Multi-Site & Disaster Recovery"
slug: on-premises/resilience/module-8.1-multi-site-dr
sidebar:
  order: 2
---

> **Complexity**: `[ADVANCED]` | Time: 60 minutes
>
> **Prerequisites**: [Cluster Topology Planning](/on-premises/planning/module-1.3-cluster-topology/), [Storage Architecture](/on-premises/storage/module-4.1-storage-architecture/)

---

## What You'll Be Able to Do

Disaster recovery design is easiest to misunderstand when it is treated as a single cluster feature. In practice, it is a chain of decisions across facilities, networks, storage systems, DNS, identity, image registries, backup tooling, and human runbooks. A Kubernetes cluster can be healthy in the surviving datacenter and still be unusable if its registry is gone, its DNS records point at the failed site, or the team cannot agree who is authorized to declare a disaster.

After completing this module, you will be able to:

1. **Design** multi-site disaster recovery architectures (active-passive, active-active) with defined RPO and RTO targets
2. **Implement** cross-site backup pipelines using Velero with off-site S3-compatible storage and etcd snapshot replication
3. **Configure** DNS-based failover and traffic switching procedures that redirect users to surviving sites within minutes
4. **Plan** DR testing runbooks with regular failover drills that validate recovery procedures before an actual disaster

---

## Why This Module Matters

Hypothetical scenario: A regional retailer runs a well-maintained on-premises Kubernetes cluster in one datacenter. The cluster has redundant control-plane nodes, redundant top-of-rack switches, mirrored storage shelves, and nightly backups. During a facility-wide incident, the platform team discovers that the backup repository, the image registry, and the DNS automation controller all live in the same building as the cluster they are trying to recover. The cluster was highly available inside one room, but the business needed survivability across failure domains.

That scenario is not about Kubernetes being fragile. It is about the difference between local high availability and disaster recovery. High availability keeps a service running when a node, disk, switch, or control-plane member fails inside the designed fault boundary. Disaster recovery assumes the boundary itself can disappear, so the recovery path must already exist somewhere else, with enough data, credentials, capacity, and procedural clarity to resume service.

The uncomfortable part is that DR must be designed before the emergency, but it only proves itself during the emergency. Backups that were never restored are hopes, not controls. A DNS failover plan that nobody has rehearsed is a document, not an operational capability. A secondary cluster without current secrets, registry access, storage classes, and network routes may look reassuring on an architecture diagram while still being unable to serve traffic.

This module treats disaster recovery as an engineering system with explicit tradeoffs. You will choose between active-active and active-passive patterns, translate business impact into RTO and RPO targets, build layered backup paths with Velero and etcd snapshots, plan DNS-based traffic movement, and define drills that reveal gaps before a real outage does. The goal is not to make every workload survive every possible event. The goal is to make the recovery promise measurable, affordable, and honest.

> **The Insurance Analogy**
>
> DR is like fire insurance combined with an evacuation drill. The policy matters, but the practiced route out of the building matters just as much. A backup is the policy; a tested restore path is the evacuation route.

---

## What You'll Learn

Read this module as a set of design choices rather than a recipe for one universal topology. A payment database, an internal wiki, a monitoring stack, and a nightly analytics platform do not deserve the same DR budget. The first may need synchronous data protection and automated traffic shifting, while the last may be acceptable with a daily backup and a manual restore. Good DR architecture starts by separating those promises instead of forcing the whole cluster into the strictest possible target.

- The difference between active-active and active-passive datacenter topologies
- Why stretched etcd clusters have a hard 10ms RTT latency limit
- How to define and measure RTO and RPO
- Velero with MinIO for S3-compatible backup and restore
- etcd snapshot backup and restore procedures
- DNS-based failover between sites

---

## Active-Active vs Active-Passive

Multi-site Kubernetes starts with one deceptively simple question: is the second site serving production traffic right now, or is it waiting for a disaster declaration? If both sites are serving at the same time, you are in active-active territory. If one site is primary and the other is prepared to take over, you are in active-passive territory. The terms sound binary, but real systems usually mix them per workload and per data layer.

Active-active is attractive because it promises very low downtime. Users can already reach both sites, capacity is already warm, and a failed site can be removed from traffic without waiting for a full restore. The cost is that every shared state problem becomes harder: databases need replication semantics, writes must not diverge, identity and certificates must be valid in both sites, and the control plane must avoid split-brain behavior during partitions.

Active-passive is less glamorous but often more honest for on-premises estates. The DR site may run a smaller control plane, a warm worker pool, replicated backups, and pre-created network paths, but production traffic stays on the primary site until a failover is declared. This pattern accepts a nonzero RPO and a measurable RTO in exchange for lower cost, simpler consistency, and the ability to place the DR site farther away from the primary facility.

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
| **Failover time** | Usually seconds to a few minutes when traffic steering is already live | Usually minutes to hours, depending on restore and validation work |
| **Data consistency** | Synchronous or carefully conflict-managed at the application/data layer | Asynchronous, with data loss bounded by backup or replication lag |
| **Network requirement** | Low, stable latency when sharing a control plane or synchronous data store | Enough bandwidth to move backups, snapshots, images, and logs off-site |
| **Cost** | Roughly duplicate production-grade capacity and operations | Smaller standby is possible, but control-plane, backup, and network costs remain |
| **Data loss risk (RPO)** | Near zero only for systems engineered for synchronous writes | Minutes to hours are common design targets, depending on schedule and workload |
| **Best for** | Selected critical services with strict business targets | Most enterprise platforms and mixed-criticality workloads |

The table hides one important trap: active-active for user traffic does not automatically mean active-active for Kubernetes control-plane state. You can run two independent clusters, one in each site, and use a global load balancer or DNS policy to send users to healthy application endpoints. That is different from stretching one Kubernetes control plane across sites, where a single etcd quorum and one API-server identity span the network. The first pattern is often safer; the second pattern is latency-sensitive and operationally demanding.

Use active-active when the business target justifies the complexity and when the data layer has a real consistency story. A web frontend with stateless pods is easy to run in both sites. A payment ledger, inventory system, or identity database is not safe just because two Deployments exist. For those systems, the deciding architecture usually lives in PostgreSQL, CockroachDB, Kafka, storage replication, or another data product rather than in Kubernetes YAML.

Use active-passive when you can tolerate a known recovery window and want the second site to be geographically or electrically independent. In many on-premises environments, a practical target is to keep Kubernetes manifests, container images, secrets, Velero backups, and etcd snapshots available off-site, then restore selected workloads in priority order. The recovery may not be instant, but it is much easier to test and reason about.

For a stretched control plane, treat single-digit millisecond round-trip time as an engineering warning zone rather than a magic line. Around 5-10ms RTT can sometimes be made to work with careful measurement, dedicated links, and etcd timeout tuning; beyond that, leader elections and write latency often dominate the value of the design. Verify the current etcd tuning guidance and measure your own links under failure and congestion before approving any stretched control-plane design.

---

> **Pause and predict**: Your two datacenters are 50km apart with 3ms RTT. Your payment system requires RPO=0 (zero data loss). Can you use a stretched etcd cluster across both sites, or do you need a different approach?

## Stretched Clusters and the etcd Latency Wall

A stretched cluster runs one Kubernetes cluster across two physical sites. Worker nodes may sit in both datacenters, API servers may be reachable from both, and etcd members may be distributed across the sites. From a user perspective, it can feel elegant: one kubeconfig, one set of Deployments, one scheduler, and one cluster identity. From a failure-mode perspective, it concentrates the hardest problem in one place: the etcd quorum.

Kubernetes stores its authoritative cluster state in etcd. Creating a Pod, updating a ConfigMap, changing a Lease, writing an EndpointSlice, or recording a controller status update eventually becomes an etcd write. etcd uses the Raft consensus algorithm, which means a leader proposes a change and the change is committed only after a majority of members acknowledge it. When the majority includes a member across a slow or lossy link, the control plane pays for that link on the write path.

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

This is why a low-latency metro link can behave very differently from a regional or cross-country link. The Kubernetes API server is not just writing occasional human changes; controllers continuously update status, endpoints, leases, events, and coordination objects. A few extra milliseconds can be acceptable. Jitter, packet loss, microbursts, or a link that performs well at noon and poorly during backups can turn the same topology into a source of intermittent API timeouts.

The etcd tuning documentation explains the relationship between heartbeat interval, election timeout, and round-trip time. The leader sends heartbeats to followers, and followers start a new election if they do not hear from the leader before the election timeout. Longer RTT and higher jitter require more forgiving timeouts, but forgiving timeouts also mean the cluster takes longer to notice a real leader failure. That tradeoff is why stretching etcd is not solved by simply increasing numbers until alerts go quiet.

| RTT Between Sites | etcd Behavior | Recommendation |
|-------------------|---------------|----------------|
| <2ms | Usually excellent if packet loss is low | Same building, campus, or very close metro fabric |
| 2-5ms | Usually workable with visible write-latency impact | Same metro area with dedicated, monitored links |
| 5-10ms | Possible only with careful tuning and load testing | Treat as an exception that needs evidence |
| 10-20ms | High risk of degraded writes and election churn | Prefer independent clusters or active-passive DR |
| >20ms | Poor fit for one etcd quorum in most Kubernetes estates | Do not stretch the control plane without vendor-backed design proof |

Treat this table as a starting point, not a universal guarantee. The current etcd tuning guide should be checked before implementation, and your own test must include realistic control-plane load, backup traffic, link failover, packet loss, and maintenance windows. A link that passes a ping test is not automatically safe for an etcd quorum because quorum writes care about tail latency and consistency, not just average latency.

Stretched clusters also have a quorum placement problem that diagrams often hide. A three-member etcd cluster split across two sites must place two members in one site and one in the other. If the minority site fails, the cluster survives. If the majority site fails, the surviving site has only one member and cannot accept writes. A five-member cluster split three-and-two has the same asymmetry. A third failure domain or witness pattern can help, but it adds another dependency and must still meet the latency budget.

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

Those settings are not a recommendation to stretch every cluster to 10ms. They show the shape of the control you would use after measurement proves that the topology is viable. The heartbeat interval should be related to observed RTT, and the election timeout must leave enough room for variance without making real failures slow to detect. Keep the same timeout values across members, monitor leader changes, and roll back the stretched design if leader elections increase during normal operations.

The safest design review question is: what exact failure do we expect this stretched control plane to survive? If the answer is "either site can disappear and the cluster keeps accepting writes," a two-site etcd layout usually cannot satisfy that without a third quorum participant or an asymmetric majority. If the answer is "we want pods in both sites, but can tolerate restoring control-plane state during a regional failure," two independent clusters plus application-level replication may be simpler and more reliable.

---

## [RTO and RPO](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/disaster-recovery-dr-objectives.html)

Recovery objectives convert fear into engineering constraints. Recovery Point Objective, or RPO, asks how much data the business can afford to lose. Recovery Time Objective, or RTO, asks how long the service can be unavailable before the impact becomes unacceptable. These are business promises first and technology choices second. If the business cannot distinguish between "one minute of orders lost" and "one hour of analytics delayed," the platform team has no rational way to choose a design.

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

Do not assign one RPO and one RTO to "the Kubernetes cluster" unless the cluster runs exactly one business service. Kubernetes state and business data often have different recovery needs. A Deployment manifest can usually be recreated from Git. A Secret can be restored from a secret manager if that manager is available. A database transaction that was acknowledged to a customer may require synchronous replication or an application-specific recovery log. The cluster is the platform; the business data is the promise.

A useful target-setting exercise is to split every workload into control-plane state, persistent application data, external dependencies, and traffic entry points. Control-plane state includes Kubernetes resources, CRDs, RBAC, NetworkPolicies, and controller-managed objects. Persistent data includes databases, object stores, queues, and filesystems. External dependencies include identity providers, registries, license servers, upstream APIs, and monitoring. Traffic entry points include DNS records, load balancers, certificates, and firewall rules.

Once the pieces are visible, the tradeoff becomes concrete. A 15-minute Velero schedule may satisfy Kubernetes object RPO, but it does not protect a database that accepts hundreds of writes per second unless the PV backup is application-consistent or the database has its own replication. A DNS failover record with a short TTL may support an RTO target, but only if the DR cluster has warm capacity, current images, valid certificates, and restored data before the record changes.

Use the following questions during design review. They keep the conversation away from vague phrases like "highly available" and toward recovery evidence that a team can test.

| Question | Why It Matters | Evidence To Collect |
|----------|----------------|--------------------|
| What is the maximum accepted data loss per workload? | Prevents overbuilding low-value systems and underprotecting critical data | RPO table approved by service owners |
| Who can declare disaster and failback? | Avoids hesitation or conflicting commands during an outage | Runbook with named roles and escalation path |
| Where are backups stored relative to the failed site? | Backups inside the same blast radius do not provide site recovery | Object-store bucket, replication policy, access test |
| How long does restore plus validation actually take? | RTO must include human checks, not just command execution | Timed drill logs and post-drill actions |
| Which dependencies must already exist in DR? | A restored cluster can still be unusable without identity, DNS, and registry access | Dependency inventory and periodic smoke tests |

The best RTO/RPO targets are boring because they have been rehearsed. If a runbook says RTO is 30 minutes, the drill record should show when the disaster was declared, when data restore began, when applications became Ready, when synthetic transactions passed, when DNS moved, and when users could complete the critical workflow. Anything not measured during the drill is a hope, not an objective.

---

## Velero with MinIO for Backup

Velero is the Kubernetes-native backup tool most teams reach for first because it understands Kubernetes resources and restore workflows. It can back up API objects, include or exclude namespaces and labels, work with object storage, and optionally protect PersistentVolume data through supported volume backup mechanisms. The [Velero architecture documentation](https://velero.io/docs/main/how-velero-works/) describes backups, schedules, and restores as Kubernetes custom resources processed by Velero controllers, which makes the operational model familiar to cluster administrators.

MinIO is useful in on-premises DR designs because it provides an S3-compatible API without requiring a public cloud account. The key design rule is that the object store must live outside the failure domain it protects. A MinIO bucket in another rack is better than a bucket on the same storage array, but it is not enough if the building, network core, or identity system is shared. Put the backup repository where a primary-site failure cannot destroy both the cluster and its recovery data.

```
  K8s Cluster (Site A)                MinIO (Site B)
  ┌──────────────────┐                ┌──────────────────┐
  │ Velero Server     │──S3 API──────►│ velero-backups/   │
  │  - K8s resources  │               │  ├── daily-03-25/ │
  │  - PV data (fs)   │               │  ├── daily-03-24/ │
  └──────────────────┘                └──────────────────┘
```

> **Stop and think**: Velero backs up at the Kubernetes API level (resources and optionally PV data). etcd snapshots capture the entire cluster state at the storage level. Why would you use both? What recovery scenario does each one handle that the other cannot?

The answer is scope and intent. Velero is excellent when you need a selective restore: one namespace, one application, one cluster migration, or a production clone into a DR cluster. It can also apply restore-time transformations, remap namespaces, and preserve or change certain service details depending on configuration. etcd snapshots are blunt but fast for full control-plane recovery when the entire cluster state must be recreated from a known point.

### Install and Configure

Velero uses the [S3 API to store backups on MinIO](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/main/contributions/minio.md) at the DR site. The `--use-node-agent` flag enables [file-system-level PV backups](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/main/file-system-backup.md), and `--default-volumes-to-fs-backup` ensures PersistentVolume data is included in every backup. Review the current Velero file-system backup limitations before relying on it for databases, because crash-consistent filesystem copies are not the same as application-consistent database backups.

The example below separates a broad full-cluster schedule from a more frequent critical-namespace schedule. That split is intentional. A full-cluster backup captures cluster-wide resources and provides a broad restore point, but it may be too large or slow to run every few minutes. A narrower schedule for production namespaces reduces RPO for the workloads that matter most while keeping backup load manageable. The schedule values are examples, not universal targets; choose them from the workload RPO table and test the object-store throughput.

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

In production, pin the Velero plugin version to one supported by your Velero server and Kubernetes version, then review the current upstream compatibility matrix before upgrades. The example keeps the existing plugin reference to make the lab concrete, but a real platform should not cargo-cult old install commands. Treat backup software like any other critical dependency: version it, test upgrades in a non-production cluster, and document rollback.

The `--ttl` values are also part of the DR design. Short retention lowers storage cost and reduces the number of stale backups that operators can accidentally restore. Longer retention helps with slower corruption discovery, audit needs, and accidental deletion that is noticed days later. You normally want multiple tiers: frequent short-lived backups for low RPO, daily or weekly retained backups for slower discovery, and separate immutable or locked copies if the threat model includes ransomware or malicious deletion.

A Velero backup pipeline is incomplete until the restore path is rehearsed. Use `velero backup describe`, `velero backup logs`, `velero restore describe`, and application-level checks after every drill. The official [Velero disaster recovery guide](https://velero.io/docs/main/disaster-case/) recommends making the backup storage location read-only during restore so a recovering cluster does not create or delete backup objects while you are trying to recover. That small operational detail can matter during chaotic failover.

Finally, decide how images and secrets reach the DR site. Velero can restore Kubernetes objects that refer to container images, but it does not magically recreate an unavailable registry. If the primary registry is in the failed site, restored Pods may stay in `ImagePullBackOff`. Similarly, restored Secrets may be stale or intentionally excluded if the organization uses an external secret manager. Include registry replication and secret-manager reachability in the same runbook as the Velero restore.

---

## etcd Snapshot Backup and Restore

Velero backs up at the API level. etcd snapshots capture the entire cluster state at the storage level. Use both -- they serve different recovery scenarios. Velero lets you [restore individual namespaces or resources](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/main/how-velero-works.md). etcd snapshots restore the entire cluster state in one operation, which is exactly what you need when the control plane itself is damaged and exactly what you do not want when only one namespace was accidentally deleted.

The official Kubernetes etcd administration documentation states that etcd stores all Kubernetes cluster data, and the etcd disaster recovery guide documents snapshot and restore facilities for catastrophic quorum loss. That makes etcd snapshots the last-resort control-plane recovery artifact. They should be frequent enough to satisfy the Kubernetes-state RPO, verified immediately after creation, copied off-site, protected from tampering, and periodically restored into a test environment.

Think of Velero and etcd snapshots as complementary lenses. Velero understands Kubernetes objects and restore filtering, so it is friendlier for application recovery, migration, and namespace-level mistakes. An etcd snapshot is a point-in-time database copy for the control plane, so it can recover objects that Velero omitted but it cannot selectively merge one namespace into a live cluster without replacing cluster state. If you only keep Velero, a broken API server or missing CRD dependency can block restore. If you only keep etcd snapshots, an operator restoring one team namespace may have to roll the whole cluster backward.

### Taking and Verifying Snapshots

Always verify snapshot integrity immediately after creation. A corrupt snapshot is worse than no snapshot because it gives the team confidence right up to the moment recovery fails. The [`snapshot status` command confirms the hash, revision, key count, and size](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/). Store that output with the backup metadata so a drill can prove which snapshot was used and whether it had passed integrity checks when it was created.

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

This command assumes kubeadm-style certificate paths and local access to the etcd endpoint on a control-plane node. If your distribution manages etcd differently, use the vendor-supported backup command and document where credentials live. The key principle is the same: take the snapshot from a healthy member, verify it immediately, then copy it away from the node and the site. A local snapshot directory is a staging location, not a DR repository.

Security matters because an etcd snapshot contains cluster state, including Secrets unless your platform stores secret material outside etcd or uses envelope encryption with externally managed keys. Treat snapshots as sensitive artifacts. Restrict read access, encrypt at rest in the backup repository, rotate credentials used by backup automation, and test whether the restore environment has the decryption material it needs. A perfectly preserved encrypted snapshot is useless if the key-management service failed with the primary site.

### Automate with a CronJob

The CronJob below demonstrates the mechanics of taking snapshots from inside the cluster while scheduling onto a control-plane node and mounting the required host paths. This pattern is convenient, but it carries real power: the Pod can read etcd certificates and write host storage. In production, keep the ServiceAccount tightly scoped, restrict who can modify the CronJob, and consider running backup automation outside the cluster if your security model forbids privileged access from Pods.

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

The example keeps the most recent local snapshots, but DR requires one more step: replicate the verified snapshot to an off-site repository. That replication can be a sidecar, a second job, a node-level agent, or a storage-system policy, but it must be observable. Alert when snapshots are old, when verification fails, when off-site upload fails, or when the backup repository has not received a new object inside the RPO window. A silent backup pipeline is a delayed outage.

Do not let the backup schedule create its own denial of service. etcd snapshots and object-store uploads consume disk, network, and CPU. Start with a schedule derived from the Kubernetes-state RPO, then measure the cost during peak controller activity and during other backup windows. If the cluster is large or controller-heavy, you may need less frequent full snapshots, faster disks, a dedicated backup network, or distribution-specific tooling that takes snapshots outside the API-server hot path.

### Restore from Snapshot

Restoring etcd is intentionally disruptive. You are not applying a patch to the live cluster; you are replacing the authoritative control-plane database with the contents of a snapshot. The etcd disaster recovery guide emphasizes recovering from disastrous quorum loss by restoring from a snapshot, and Kubernetes documentation links to that process for cluster restore examples. Practice this in a non-production environment until the steps are familiar, because improvising during a control-plane outage is how partial recoveries become longer outages.

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

Every control-plane member must be restored consistently from the same snapshot lineage. Do not restore separate snapshots onto separate members and expect Raft to reconcile them safely. In a kubeadm-style cluster, you also need to account for static Pod manifests, certificate validity, member names, advertise URLs, and any load balancer or virtual IP in front of the API servers. The commands are only one part of the recovery; the surrounding inventory is what makes them safe to run.

After the control plane returns, validation must be broader than `kubectl get nodes`. Check API-server health, controller-manager and scheduler leadership, CoreDNS, admission webhooks, CRDs, CNI components, storage provisioners, and application readiness. A restored etcd can bring back objects that refer to infrastructure that no longer exists, such as old node names, old storage backends, or old load balancer addresses. The runbook should list those mismatches and the exact commands used to resolve them.

---

## DNS-Based Failover

Traffic movement is the most visible part of DR because users notice where their requests go. DNS-based failover is common in on-premises designs because it works across many network products and can be operated without putting every application behind the same global load balancer. It is also imperfect: DNS caches, client behavior, recursive resolvers, mobile networks, and long-lived connections mean traffic does not move as cleanly as an architecture diagram suggests.

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
| DNS TTL | 30-60 seconds as an example starting range | Faster failover, more DNS queries, and more resolver churn |
| Health check interval | Around 10 seconds for critical services | Detect failures quickly without turning transient packet loss into failover |
| Failure threshold | 3 consecutive failures as a starting point | Avoid flapping caused by one missed probe or short maintenance event |
| Recovery threshold | 5 consecutive successes as a starting point | Ensure stability before failback or traffic rebalancing |

> **Warning**: DNS TTL is a suggestion, not a command. Budget for a stale-cache tail in your RTO, even when the authoritative record advertises a short TTL.

The [ExternalDNS annotations documentation](https://kubernetes-sigs.github.io/external-dns/latest/docs/annotations/annotations/) shows how Kubernetes resources can request hostnames, targets, and TTLs from supported DNS providers. That is useful for keeping DNS records aligned with Services and Ingresses, but it does not replace a DR policy. You still need to define who changes weights, which health check is authoritative, what happens if the DNS controller itself is unavailable, and how to prevent the failed primary site from automatically reclaiming traffic before data is safe.

For applications served through both sites, DNS can steer users by weight, health, latency, or manual record changes depending on the provider. For active-passive, the common pattern is to advertise the primary site's load balancer while keeping a DR record prepared but inactive or weighted to zero. During failover, the operator or automation promotes the DR target, verifies that authoritative DNS has changed, and watches synthetic checks from multiple networks until traffic reaches the surviving site.

Low TTLs are a tradeoff. They reduce the time many clients cache the old answer, but they increase query volume against recursive and authoritative DNS. They also do not close existing TCP connections or force every resolver to behave perfectly. If the application uses long-lived WebSockets, client-side connection pools, mobile SDKs, or enterprise proxies, the effective traffic drain may be slower than the DNS TTL. Include that long tail in the RTO measurement rather than arguing with it during an incident.

CoreDNS is part of the in-cluster recovery story as well. The [CoreDNS Kubernetes plugin](https://coredns.io/plugins/kubernetes/) watches Kubernetes EndpointSlices and reports readiness after syncing with the API. After a restore, Pods can be Running while service discovery is still catching up, or CoreDNS can return errors for records whose informers have not synchronized. A good DR validation checklist tests both external DNS movement and internal service discovery from a Pod inside the restored cluster.

When service discovery across independent clusters is part of the design, review the [SIG Multicluster Services API](https://multicluster.sigs.k8s.io/concepts/multicluster-services-api/) as a model, not a magic DR switch. ServiceExport and ServiceImport can help standardize cross-cluster service naming, but the API deliberately leaves implementation choices open. You still need to design data replication, identity, network routing, and failure policy around it.

---

## DR Testing Runbooks and Failover Drills

A disaster recovery plan is only theoretical until it is tested. Regular DR drills validate both the technical recovery procedures and the human runbooks. The point is not to prove that the team is competent; it is to discover the hidden dependency, expired credential, missing firewall rule, wrong DNS permission, or confusing handoff while the organization can fix it calmly.

Good drills measure elapsed time and decision quality. Start the timer when the failure is declared, not when the first restore command is typed. Stop only after the critical user journey succeeds through the DR site, monitoring is receiving signals, logs are accessible, and the incident commander has confirmed that the service owner accepts the recovered state. That timing discipline prevents a common self-deception: reporting the restore command duration as the RTO while ignoring investigation, approval, validation, and traffic movement.

### Building the Runbook

Your DR runbook should be a step-by-step document that assumes the reader is sleep-deprived and stressed. It must be specific enough for a trained on-call engineer to execute without guessing, but not so brittle that one changed Pod name invalidates the whole document. Use commands, expected outputs, decision gates, rollback paths, and contact roles. Avoid prose like "restore the database" unless the next line tells the operator which backup to choose and how to verify it.

1. **Declaration Criteria**: Who can declare a disaster? What are the criteria (e.g., site down for >15 minutes)?
2. **Communication Plan**: Which Slack/Teams channels, phone bridges, and status pages to use.
3. **Technical Steps**: Exact commands (like the `etcdutl snapshot restore` and `velero restore` commands) with expected output.
4. **Validation Checklist**: How to verify that the restored applications are actually functioning.

Add a dependency inventory to the same runbook. For each workload, list its namespace, owner, RPO, RTO, backup schedule, restore command, image registry path, secret source, storage class, ingress hostname, DNS provider, external APIs, and validation transaction. That inventory may feel bureaucratic during design, but it becomes the map during a disaster. If a dependency is not listed, assume the first drill will find it the hard way.

Also document failback separately from failover. Failover moves service to the DR site. Failback returns service to the primary site after the original failure domain is repaired. Failback can be more dangerous because data may now be newer in DR than in primary, operators may be tired, and stakeholders may pressure the team to "go back to normal" before replication and validation are complete. Treat failback as a planned migration with its own freeze, data reconciliation, and rollback decision.

### Drill Cadence

- **Monthly Tabletop**: The team talks through a disaster scenario and the runbook steps without touching keyboards.
- **Quarterly Component Drill**: Fail over a single component to validate the pipeline.
- **Annual Full-Scale Drill**: Fail over the entire primary site to the DR site, run production from DR for a set period, and fail back.

The cadence should match the rate of platform change. A stable environment with quarterly releases may learn enough from quarterly component drills and an annual full-site exercise. A fast-moving platform with frequent cluster upgrades, new storage classes, and changing network policy should test more often because the runbook decays quickly. Tie drill scope to recent changes: after a registry migration, test image pulls in DR; after a DNS provider change, test failover authority; after a storage upgrade, test PVC restore.

Use game days to validate assumptions without waiting for a real disaster. A tabletop can ask who declares a disaster and which services recover first. A component drill can restore one namespace into the DR cluster and run synthetic traffic. A full-scale drill can isolate the primary site, promote DR, run production traffic for a controlled period, and then fail back. Each level should produce action items with owners and deadlines, not just a meeting note.

| Drill Type | Primary Question | Typical Evidence |
|------------|------------------|------------------|
| Tabletop | Does everyone understand decisions, roles, and communication? | Updated runbook, clarified authority, dependency gaps |
| Backup restore drill | Can we restore a representative workload from current backups? | Velero restore logs, application smoke tests, elapsed time |
| Control-plane drill | Can we recover or rebuild cluster state from etcd artifacts? | Snapshot status, restore transcript, API health checks |
| DNS failover drill | Can users reach the surviving site through normal names? | DNS query logs, synthetic checks from multiple networks |
| Full-site game day | Can the business operate from DR long enough to matter? | RTO/RPO evidence, stakeholder signoff, failback record |

Always document lessons learned from drills and update the runbook immediately. A drill that finds no issues may mean the platform is mature, but it can also mean the scenario was too narrow. Rotate scenarios across facility loss, control-plane corruption, storage loss, registry outage, DNS provider failure, identity-provider outage, and accidental namespace deletion so the team exercises more than one happy path.

## Did You Know?

1. **etcd quorum failure is a hard stop, not a warning state.** The [etcd disaster recovery guide](https://etcd.io/docs/v3.5/op-guide/recovery/) explains that an N-member cluster tolerates up to `(N-1)/2` permanent failures; once more than that is lost, the cluster loses quorum and cannot continue accepting updates. That is why quorum placement is a DR design decision, not just an installation detail.

2. **Velero stores operations as Kubernetes objects.** The [Velero "How Velero Works" documentation](https://velero.io/docs/main/how-velero-works/) describes on-demand backups, scheduled backups, and restores as custom resources processed by controllers. That makes Velero operationally familiar, but it also means the Velero control plane depends on a healthy target cluster during restore.

3. **[Velero was originally "Heptio Ark"](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/v0.11.0/migrating-to-velero.md)**, created by the company founded by [Kubernetes co-creators Joe Beda and Craig McLuckie](https://kubernetes.io/blog/2018/06/06/4-years-of-k8s/). Renamed after [VMware's 2018 acquisition](https://blogs.vmware.com/tanzu/vmware-completes-heptio-acquisition/), "Velero" is Spanish for "sailboat."

4. **DNS automation still needs policy.** ExternalDNS can publish hostnames, targets, and TTLs from Kubernetes resources, but the annotations documentation also notes provider-specific behavior and alpha annotations. Multi-cluster service discovery can help with service naming, yet neither DNS automation nor ServiceImport objects decide whether data is current, whether users should fail over, or whether the failed site may rejoin automatically.

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

Use a tiered strategy rather than forcing both workloads into the same recovery pattern. **Payments** need zero-RPO protection for payment data and very low RTO for the user path, so the data layer should use synchronous replication or a database designed for multi-site consistency. You may run payment pods in both sites with topology spread constraints and a traffic steering layer, but you should approve a stretched Kubernetes control plane only after proving the 3ms link under load and documenting quorum behavior.

**Analytics** can use a cheaper active-passive path. A Velero schedule every four hours, off-site object storage, replicated images, and a manual restore runbook can satisfy RPO=4h and RTO=24h if drills confirm the restore plus validation time. The payment path should be drilled more often because its RTO target leaves little room for human improvisation, while analytics can be restored later in the service priority order.
</details>

### Question 5
You split a five-member etcd cluster across two sites: three members in Site A and two members in Site B. The platform lead says this means either site can fail with no control-plane outage. Is that statement correct?

<details>
<summary>Answer</summary>

**No. A five-member cluster needs three members for quorum, so losing Site A also loses quorum.** The cluster survives losing Site B because the three Site A members can still form a majority. It does not survive losing Site A because the two remaining Site B members cannot commit writes on their own.

The explanation matters because odd member counts prevent split votes, but they do not magically give both sites a majority. If the requirement is to survive loss of either site while keeping the same control plane writable, the design needs a third failure domain or a vendor-supported witness/quorum pattern that still meets the latency budget.
</details>

### Question 6
Your team has successful Velero restores for application namespaces. A reviewer asks why you still need etcd snapshots. Give two scenarios where etcd snapshots provide value that Velero alone does not.

<details>
<summary>Answer</summary>

**First, etcd snapshots help when the control plane itself is damaged or quorum is lost.** Velero restore operations require a working target cluster and API server, while an etcd snapshot can be used to recreate the authoritative cluster state during catastrophic control-plane recovery.

**Second, etcd snapshots capture cluster-wide state exactly at a storage layer point in time.** That can include resources, CRDs, leases, RBAC, and controller state that a selective Velero backup may have excluded. The tradeoff is that an etcd restore is not surgical; it replaces cluster state, so Velero remains the better tool for namespace-level or application-level recovery.
</details>

### Question 7
During a failover drill, authoritative DNS changes from Site A to Site B in 20 seconds, but some clients continue reaching Site A for several minutes. Did DNS failover fail?

<details>
<summary>Answer</summary>

**Not necessarily. DNS TTLs reduce cache duration but do not force every resolver or client to forget an old answer instantly.** Recursive resolvers, client caches, enterprise proxies, and long-lived application connections can create a stale-traffic tail after the authoritative record has changed.

The drill should record both the authoritative DNS update time and the user-visible traffic migration time. If the business RTO depends on all users moving immediately, DNS alone is probably insufficient; use a global traffic manager, connection draining, application retry logic, or network-level controls that fit the application behavior.
</details>

---

## Hands-On Exercise: Velero DR Pipeline

**Objective**: Set up Velero with MinIO across two kind clusters and practice backup-restore.

This exercise demonstrates the control flow of a DR backup pipeline without pretending that a laptop lab proves production readiness. You will create two kind clusters, use MinIO as the S3-compatible backup repository, back up a namespace from Site A, and restore it into Site B. The important habit is not the specific sample application; it is the sequence of installing the backup controller, waiting for readiness, creating a backup, waiting for backup discovery in the target cluster, restoring, and validating the result.

The lab uses a stateless nginx Deployment so it can run on most machines. In a production validation, repeat the same pattern with a representative stateful workload, a realistic StorageClass, restored Secrets, registry access, DNS routing, and application-level smoke tests. The runbook should tell operators exactly how to distinguish "Kubernetes objects restored" from "the business service is working again."

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

Continue to [Module 8.2: Hybrid Cloud Connectivity](/on-premises/resilience/module-8.2-hybrid-connectivity/) to learn how to connect on-premises clusters to cloud environments using VPNs, direct interconnects, and multi-cluster networking.

## Sources

- [docs.aws.amazon.com: rel planning for recovery disaster recovery.html](https://docs.aws.amazon.com/wellarchitected/2025-02-25/framework/rel_planning_for_recovery_disaster_recovery.html) — General lesson point for an illustrative rewrite.
- [docs.aws.amazon.com: disaster recovery dr objectives.html](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/disaster-recovery-dr-objectives.html) — The AWS Well-Architected DR objectives page directly defines RTO and RPO.
- [velero.io: backup reference](https://velero.io/docs/v1.17/backup-reference/) — Velero's backup reference documents scheduled backups, Cron expressions, and schedule-generated backup names.
- [velero.io: disaster recovery](https://velero.io/docs/main/disaster-case/) — Velero's disaster recovery guide documents restoring from scheduled backups and setting backup storage locations to read-only during recovery.
- [velero.io: restore reference](https://velero.io/docs/main/restore-reference/) — Velero's restore reference explains restore workflow, restore validation, resource ordering, and persistent volume restore behavior.
- [github.com: minio.md](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/main/contributions/minio.md) — Velero's MinIO documentation shows S3-compatible configuration using the AWS provider, s3Url, and path-style access.
- [github.com: file system backup.md](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/main/file-system-backup.md) — Velero's file-system backup documentation directly describes node-agent setup and the default-volumes-to-fs-backup behavior.
- [github.com: how velero works.md](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/main/how-velero-works.md) — The Velero architecture documentation describes backing up and restoring Kubernetes resources through the API.
- [kubernetes.io: configure upgrade etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/) — The Kubernetes etcd administration page directly states etcd stores all cluster data and documents snapshot save and restore.
- [etcd.io: disaster recovery](https://etcd.io/docs/v3.5/op-guide/recovery/) — The etcd disaster recovery guide explains quorum loss, snapshotting, and restoring a failed etcd cluster from a snapshot.
- [etcd.io: tuning](https://etcd.io/docs/v3.4/tuning/) — The etcd tuning guide documents heartbeat interval, election timeout, and their relationship to network round-trip time.
- [external-dns: annotations](https://kubernetes-sigs.github.io/external-dns/latest/docs/annotations/annotations/) — ExternalDNS annotation documentation covers hostname, target, provider-specific, and TTL annotations used in DNS automation.
- [coredns.io: kubernetes plugin](https://coredns.io/plugins/kubernetes/) — CoreDNS Kubernetes plugin documentation explains service discovery behavior, EndpointSlice watching, readiness, TTL, and multicluster options.
- [sig-multicluster: multicluster services api](https://multicluster.sigs.k8s.io/concepts/multicluster-services-api/) — SIG Multicluster documentation describes ServiceExport, ServiceImport, and the scope of the Multi-Cluster Services API.
- [github.com: migrating to velero.md](https://github.com/vmware-tanzu/velero/blob/main/site/content/docs/v0.11.0/migrating-to-velero.md) — The Velero migration documentation directly states that Heptio Ark was renamed Velero.
- [blogs.vmware.com: vmware completes heptio acquisition](https://blogs.vmware.com/tanzu/vmware-completes-heptio-acquisition/) — VMware's acquisition announcement directly confirms the acquisition and leadership names.
- [kubernetes.io: 4 years of k8s](https://kubernetes.io/blog/2018/06/06/4-years-of-k8s/) — The Kubernetes anniversary post discusses the original creation of Kubernetes and names Joe Beda and Craig McLuckie in that origin story.

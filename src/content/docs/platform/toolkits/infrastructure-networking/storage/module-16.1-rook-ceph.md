---
revision_pending: false
title: "Module 16.1: Rook/Ceph - Enterprise Storage for Kubernetes"
slug: platform/toolkits/infrastructure-networking/storage/module-16.1-rook-ceph
sidebar:
  order: 2
---

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 55-65 minutes
>
> **Prerequisites**: [Distributed Systems Foundation](/platform/foundations/distributed-systems/) (replication, consistency), [Reliability Engineering Foundation](/platform/foundations/reliability-engineering/) (SLOs, failure modes), Kubernetes fundamentals (PVCs, StorageClasses, CSI, StatefulSets), basic Linux storage concepts (block devices, filesystems)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy a production-ready Rook/Ceph cluster on Kubernetes for distributed block, file, and object storage**
- **Architect Ceph pools with appropriate replication or erasure coding strategies for different workload profiles**
- **Troubleshoot Ceph cluster health using the toolbox, dashboard, and Prometheus metrics in day-2 operations**
- **Evaluate when Rook/Ceph earns its operational weight versus cloud-managed CSI or lighter in-cluster alternatives**
- **Plan Rook and Ceph version upgrades safely, including the ceph-csi-operator migration introduced in Rook v1.20**

---

## Why This Module Matters

Kubernetes abstracts compute beautifully. Deployments, ReplicaSets, and scheduling make stateless workloads nearly trivial. But the moment a workload needs persistent storage — a database that must survive a pod restart, a shared filesystem for a training pipeline, object storage for compliance archives — Kubernetes hands the problem to you through a deliberately thin abstraction: the PersistentVolumeClaim. The PVC says "I need 50 gigabytes of something that survives pod lifecycles." It does not say where those bytes live, how they are replicated, or what happens when a disk fails at 3 AM.

This is where the gap between Kubernetes-native and enterprise-ready opens. Cloud providers fill it with managed block storage services — EBS, Persistent Disk, Azure Disk — that work seamlessly as long as you stay inside their ecosystem. But the moment you operate on bare metal, need data sovereignty across geographies, require multiple storage types from the same physical hardware, or face a cloud bill measured in millions per year, you need a software-defined storage system that runs inside your cluster.

Rook/Ceph is the answer Kubernetes operators have converged on for that problem. Rook is a CNCF Graduated project — a Kubernetes operator that automates the entire lifecycle of Ceph, the most battle-tested distributed storage system in open source. Ceph, a Linux Foundation project under the Ceph Foundation, provides block storage (RBD), a shared POSIX filesystem (CephFS), and S3-compatible object storage (RGW) from a single pool of physical disks. Together, they give you cloud-provider-grade storage that runs anywhere Kubernetes runs: on-premise, at the edge, or even in a cloud account you control rather than rent.

This module teaches the durable spine of both projects — the architectural primitives that have not changed across a decade of releases — and equips you to make a reasoned decision about when this operational weight is worth carrying.

> **Landscape snapshot — as of 2026-06. This changes fast; verify against vendor docs before relying on specifics.**
>
> - **Rook**: v1.20.1 (latest patch), Helm chart 1.20.0. CNCF Graduated since 2020. Minimum Kubernetes v1.31.
> - **Ceph**: **Tentacle (v20.x, e.g. v20.2.2)** is the current stable series. **Squid (v19.x, e.g. v19.2.4)** is the prior series, still widely deployed.
> - **Architecture change in Rook 1.20**: Rook no longer deploys CSI drivers itself. CSI is now admin-managed via the **ceph-csi-operator**. Settings previously in the `rook-ceph-operator-config` ConfigMap migrate to ceph-csi-operator resources. A separate `ceph-csi-drivers` Helm chart is a **new requirement**.

### Kubernetes-Storage Rosetta

This table compares Rook/Ceph against a representative cloud-managed CSI driver and a simpler in-cluster option, so you can reason about tradeoffs. No "best" — only capability profiles.

| Capability | Rook/Ceph | Cloud-managed CSI (e.g. EBS CSI) | Simpler in-cluster (e.g. Longhorn) |
|---|---|---|---|
| Block storage (RWO) | Yes — RBD, high performance | Yes — native to provider | Yes — iSCSI-based |
| Shared filesystem (RWX) | Yes — CephFS with MDS | No (or NFS-based add-on) | Yes — NFS-based |
| Object storage (S3) | Yes — RGW, S3/Swift API | Separate service (S3, GCS) | Limited or via MinIO sidecar |
| Data placement control | CRUSH — full topology awareness | Provider-managed zones | Replica count + node affinity |
| Replication vs erasure coding | Both, configurable per pool | Replication only (provider-managed) | Replication only |
| Day-2 operations model | Kubernetes operator + Ceph CLI | Provider-managed (minimal surface) | Web UI + kubectl |
| Operational complexity | High — requires understanding Ceph internals | Low — provider abstracts storage layer | Medium — self-managed but simpler |
| Runs on bare metal | Yes — primary use case | No | Yes |
| Multi-datacenter stretch | Yes — stretch clusters + RBD mirroring | Cross-AZ only | Limited |

---

## Part 1: The Stateful-Kubernetes Problem

Before diving into Ceph or Rook, it is worth understanding why distributed storage is fundamentally hard and why Kubernetes alone does not solve it. The problem begins with the observation that containers, by design, are ephemeral. A pod that crashes is replaced by a new pod on potentially a different node. The local disk on the old node — an `emptyDir` volume, a `hostPath` — is lost or orphaned. Applications that need to remember data across restarts cannot rely on container-local storage.

Kubernetes addresses this with the PersistentVolume (PV) and PersistentVolumeClaim (PVC) model. A PV represents a piece of storage in the cluster, provisioned either statically by an administrator or dynamically through a StorageClass. A PVC is a user's request for storage: "give me 50Gi of ReadWriteOnce block storage." The StorageClass defines *how* that storage is provisioned — which provisioner to call, what parameters to pass, whether to retain or delete the backing volume when the PVC is released. The Container Storage Interface (CSI) is the plugin standard that connects StorageClasses to actual storage systems: when a PVC is created, the CSI provisioner creates the volume on the backend, attaches it to the node, and mounts it into the pod.

In a cloud environment, this model works cleanly because the CSI driver delegates to a battle-tested, fully managed storage service — AWS EBS, GCP Persistent Disk, Azure Disk — that handles replication, snapshotting, and hardware replacement transparently. The Kubernetes administrator's responsibility ends at choosing the right StorageClass. But on bare metal, or in an environment where you control the physical infrastructure, there is no managed service to delegate to. You are the provider. You must solve data durability, replication across failure domains, capacity management, and performance isolation yourself. This is where software-defined storage enters.

An in-cluster storage system must contend with several hard realities that cloud abstractions hide. First, disks fail continuously — a fleet of 100 spinning disks will see failures monthly, and even SSDs wear out under sustained write pressure. Second, network partitions can split a cluster, creating the risk of split-brain writes that corrupt data irreversibly. Third, performance varies wildly between workloads: a PostgreSQL database needs low-latency synchronous writes, while an ML training pipeline reads the same dataset from dozens of pods simultaneously and cares more about aggregate throughput than individual latency. A storage system that optimizes for one workload profile will serve the others poorly, which is why Ceph's "three storage types from one cluster" design is a genuine architectural advantage rather than a checklist item.

---

## Part 2: Ceph Fundamentals — The Durable Spine

Ceph is not a single program. It is a distributed system built from four daemon types that each serve a distinct role, co-operating through a shared gossip-based cluster map and the CRUSH algorithm. Understanding the roles of these daemons — and the invariants they maintain — is the prerequisite for operating Ceph in production. The architecture is sometimes summarized as RADOS (Reliable Autonomic Distributed Object Store), the low-level object storage layer on which all higher-level Ceph services are built.

### Object Storage Daemons (OSDs) — Where the Data Lives

The OSD is the fundamental storage primitive. One OSD runs per physical disk (or per partition, though whole-disk is the standard). The OSD owns a raw block device and stores data as RADOS objects, each identified by a pool name and an object name hashed into a Placement Group (PG). OSDs use the BlueStore storage backend by default — a design that writes directly to the raw block device, bypassing the filesystem layer entirely for data, while using a small RocksDB-backed partition for metadata. This eliminates double-write amplification (no filesystem journal between Ceph and the disk) and gives Ceph precise control over data placement and write ordering.

When data is written to a replicated pool, the client sends the write to the primary OSD for the PG that owns the object. The primary OSD writes the data locally, then forwards the write to the secondary OSDs in the PG's acting set. The write is acknowledged to the client only after all replicas have committed it — a synchronous replication model that guarantees durability at the cost of write latency proportional to the slowest replica. This is why Ceph cluster performance is often limited by the slowest disk in the acting set: one struggling HDD among SSDs drags down every PG it participates in.

When an OSD fails, the cluster marks it "down" and, after a configurable timeout (default 300 seconds for `mon_osd_down_out_interval`), marks it "out." At that point, Ceph's self-healing mechanism — the Peering process — recalculates which OSDs should hold the data for the affected PGs and begins backfilling data to restore the configured replication factor. This recovery traffic competes with client I/O and is one of the most common sources of performance degradation during failure events. Production cluster operators learn to tune recovery priorities (`osd_recovery_op_priority`) and backfill limits (`osd_max_backfills`) to maintain acceptable client performance during self-healing.

### Monitors (MONs) — The Consensus Layer

MONs maintain the cluster map: a data structure that records which OSDs are up, which are down, where each PG is placed, and the overall cluster topology. The cluster map is the single source of truth for every participant in the Ceph cluster. When a client wants to read or write data, it first contacts a MON to obtain the latest cluster map, then uses CRUSH to compute data placement locally — it never contacts the MON again for that I/O operation.

MONs achieve fault tolerance through a modified Paxos consensus algorithm. A majority (quorum) of MONs must agree on every cluster map update. This is why MONs must always be deployed in odd numbers: 3 MONs survive 1 failure (quorum is 2 out of 3), 5 MONs survive 2 failures (quorum is 3 out of 5). An even number like 4 MONs still only survives 1 failure because it still requires 3 votes for quorum — the fourth MON adds no additional fault tolerance while consuming resources and adding latency to consensus rounds. MONs are lightweight daemons that store their state in a LevelDB key-value store and consume modest CPU and memory. The rule in production is simple: 3 MONs for most clusters, 5 MONs only when you have more than 5 physical hosts and truly need to survive a double MON failure.

### The CRUSH Algorithm — Why Ceph Scales

CRUSH (Controlled Replication Under Scalable Hashing) is the algorithm that distinguishes Ceph from centralized-metadata storage architectures. In a traditional distributed filesystem, a metadata server maintains a mapping from file paths to block locations. Every read and write operation must consult this server, creating a central bottleneck. As the cluster grows, the metadata server becomes the scaling limit.

CRUSH eliminates this bottleneck by making data placement deterministic and computable. Given an object name, a pool, and the cluster map, any client can compute exactly which OSDs should store the data using a mathematical function. The cluster map encodes the physical topology — hosts, racks, rows, datacenters — as a tree of "buckets" with weights. CRUSH traverses this tree using a hash of the object identifier, selecting OSDs pseudo-randomly but weighted by capacity and constrained by failure-domain rules. The result is that clients talk directly to OSDs without any intermediary. Adding or removing OSDs causes CRUSH to redistribute only the minimal amount of data necessary — a property called "data distribution efficiency" — while preserving the failure-domain constraints.

This architecture has two profound implications for operators. First, Ceph scales horizontally: adding more OSDs increases both capacity and throughput roughly linearly, because the CRUSH computation cost is constant and client-OSD communication is point-to-point. Second, the cluster map is the single point of consensus, not a single point of failure — as long as a quorum of MONs is available, the cluster functions. This is a fundamentally different failure model from systems with dedicated metadata servers, where losing the metadata server means losing access to all data even if the data itself is intact.

### Manager (MGR) and Metadata Server (MDS) — The Auxiliary Daemons

The MGR daemon serves as the extensible management interface for the cluster. It hosts plugin modules — the dashboard (a web UI on port 8443), the Prometheus metrics exporter, the disk prediction module (which forecasts OSD failures using SMART data), and the `restful` API module. MGRs run in active/standby pairs: one is active and handling all requests, while the standby takes over if the active fails. The MGR is required for the cluster to function correctly (it balances PGs, among other duties), but its absence does not cause data loss — only management-plane unavailability.

The MDS (Metadata Server) is required only for CephFS, the POSIX-compliant shared filesystem. CephFS stores file data as RADOS objects (the same as RBD and RGW), but file metadata — directory hierarchies, inode tables, permissions — is managed by MDS daemons that cache the active portion of the metadata in memory for performance. MDS daemons can be deployed in active/standby pairs for high availability. Without at least one active MDS, CephFS file operations hang — the data is still safe in RADOS, but the namespace becomes inaccessible. This is why production CephFS deployments run at least two MDS daemons with `activeStandby: true`.

---

## Part 3: Rook — The Kubernetes Operator for Ceph

Rook is the bridge between Kubernetes' declarative resource model and Ceph's operational complexity. Before Rook, deploying Ceph meant running Ansible playbooks (ceph-ansible) or hand-crafting systemd units across dozens of nodes, maintaining an out-of-band configuration database, and writing custom monitoring to detect OSD failures. Rook replaces all of that with Custom Resource Definitions (CRDs) and a reconciliation loop.

### The Operator Model

At the heart of Rook is the Rook operator pod, which watches Kubernetes API for changes to Rook CRDs and reconciles the desired state with the actual state. When you create a `CephCluster` CR, the operator:
1. Validates the configuration against known Ceph version requirements
2. Creates a Kubernetes Job to detect the exact Ceph version from the specified container image
3. Deploys MON pods with anti-affinity to spread them across nodes
4. Bootstraps the MON quorum and generates the initial cluster map
5. Deploys MGR pods (active + standby)
6. Discovers available block devices on each node using the OSD prepare job
7. Provisions OSDs by formatting devices with BlueStore and registering them with the cluster
8. Deploys the CSI driver components (in Rook v1.19 and earlier) or ensures the ceph-csi-operator resources are configured (in v1.20+)
9. Sets up the Ceph dashboard and monitoring stack

Every subsequent change to the CR — scaling monitor count, adding nodes, changing Ceph configuration — triggers a partial reconciliation that applies only the delta. If the operator pod itself restarts, it re-reads all CRDs and converges to the desired state.

### The Rook 1.20 CSI Architecture Change

This is the single most important architectural change for operators upgrading to Rook v1.20. In previous releases, Rook deployed the CSI drivers (the RBD and CephFS CSI plugins) as sidecar containers within the Rook operator or as separate DaemonSets managed by the operator. CSI settings — driver images, log levels, node plugin tolerations — were configured through the `rook-ceph-operator-config` ConfigMap.

Starting with Rook v1.20, **Rook no longer deploys CSI drivers at all**. Instead, the **ceph-csi-operator** — a separate Kubernetes operator from the Ceph CSI project — manages the CSI driver lifecycle. The Rook operator's responsibility is now limited to creating the necessary `OperatorConfig` and `Driver` custom resources that tell the ceph-csi-operator what CSI configuration to use.

For Helm users, this means the `ceph-csi-drivers` Helm chart is now a **mandatory separate installation** (ordered: `rook-ceph`, then `ceph-csi-drivers`, then `rook-ceph-cluster`). For manifest-based deployments, you must apply `csi-operator.yaml` from the Rook examples directory, and CSI configuration previously in `rook-ceph-operator-config` must be migrated to ceph-csi-operator resources using tools like `kubectl get drivers.csi.ceph.io -o yaml` and `kubectl get operatorconfigs.csi.ceph.io -o yaml`.

This change reduces the Rook operator's scope and recognizes that CSI driver management is a cross-cutting concern better handled by a dedicated operator. For the administrator, it means one additional component to monitor and upgrade, but also a cleaner separation of concerns: Rook manages Ceph, ceph-csi-operator manages CSI, and Kubernetes PV/PVC/StorageClass ties them together.

### CRDs: The Declarative Interface to Ceph

Rook exposes Ceph through six primary CRDs:

- **CephCluster**: The top-level resource. Defines the Ceph version, MON/MGR/OSD counts, network configuration, storage device selection, resource limits, and placement constraints. Creating a CephCluster triggers the full deployment sequence described above.

- **CephBlockPool**: Defines an RBD pool with replication or erasure coding parameters, a failure domain, and CRUSH device class constraints. Rook automatically creates a corresponding StorageClass when a CephBlockPool is created, using the `rook-ceph.rbd.csi.ceph.com` provisioner.

- **CephFilesystem**: Defines a CephFS instance with separate metadata and data pools, MDS placement and count, and mirroring configuration. The corresponding StorageClass uses `rook-ceph.cephfs.csi.ceph.com` as the provisioner and provides ReadWriteMany access mode.

- **CephObjectStore**: Defines an S3-compatible object store backed by RADOS Gateway (RGW) pods. Includes separate metadata and data pools, RGW instance count, and service configuration.

- **CephObjectStoreUser**: Creates S3 access credentials (AccessKey/SecretKey) for an object store. The credentials are stored in a Kubernetes Secret.

- **CephClient** and **CephNFS**: Additional CRDs for direct CephX client authentication and NFS-Ganesha exports, respectively. Less commonly used in Kubernetes-native workflows.

The key insight is that each CRD represents a Ceph concept that previously required `ceph` CLI commands to configure. A `CephBlockPool` CR is equivalent to running `ceph osd pool create`, setting the pool's replication size, and configuring a CRUSH rule — but as a declarative Kubernetes resource that the operator continuously reconciles. If someone manually deletes the pool in Ceph using the CLI, the operator recreates it on the next reconciliation cycle. This is both powerful (infrastructure-as-code) and dangerous (the operator will undo manual emergency interventions unless you pause reconciliation).

### The Toolbox Pod

Rook provides a convenience Deployment called the "toolbox" (`rook-ceph-tools`) — a pod with the full `ceph` CLI, `rados` object manipulation tools, and debugging utilities pre-installed. The toolbox is essential for day-2 operations because many Ceph operational tasks still require CLI interaction: checking cluster health (`ceph status`), inspecting placement group states (`ceph pg stat`), adjusting OSD weights, or running performance benchmarks. The toolbox is deployed as a separate resource, not as part of the CephCluster CR, and should be available in every production cluster. A common anti-pattern is discovering you need the toolbox during an incident and having to deploy it while storage is degraded.

---

## Part 4: Storage Types — RBD, CephFS, and RGW in Practice

Ceph's architecture allows three storage interfaces to coexist on the same RADOS object store, each optimized for different access patterns.

### Block Storage (RBD)

RADOS Block Device (RBD) presents a virtual block device — essentially a network-attached disk — to a single consumer. RBD volumes are striped across RADOS objects (typically 4MB objects by default), meaning a 100Gi RBD image is stored as roughly 25,600 RADOS objects distributed across all OSDs in the pool. This striping enables parallel I/O: large sequential reads and writes benefit from the aggregate throughput of multiple OSDs.

RBD volumes are accessed in Kubernetes through the RBD CSI driver. The access mode is ReadWriteOnce (RWO) because Ceph RBD has a strong consistency model: only one client can map an RBD image at a time (exclusive lock). This makes RBD ideal for databases (PostgreSQL, MySQL, MongoDB), message queues (persistent Kafka volumes), and any StatefulSet where each pod needs a dedicated, high-performance block device.

A critical operational detail: RBD images support snapshots and clones. The CSI driver can create volume snapshots (via the Kubernetes VolumeSnapshot API) that are crash-consistent point-in-time copies stored efficiently using Ceph's copy-on-write mechanism. Cloning a snapshot creates a new RBD image that shares data blocks with the parent until writes diverge them — useful for database forks, test environments, and backup workflows.

### Shared Filesystem (CephFS)

CephFS is a POSIX-compliant distributed filesystem that supports ReadWriteMany (RWX) access — multiple pods can mount and write to the same filesystem simultaneously. This is fundamentally different from RBD: where RBD provides a raw block device with exclusive access, CephFS provides a namespace with directory hierarchies, file permissions, and concurrent readers and writers.

The tradeoff is performance. CephFS must coordinate metadata operations through the MDS, which introduces latency for file creation, deletion, and permission checks. For workloads that do large sequential reads with few metadata operations — ML training pipelines reading sharded datasets, shared media repositories, content management systems — CephFS is excellent. For workloads that churn through many small files with frequent metadata updates, RBD with a filesystem on top (ext4/XFS) often outperforms CephFS because there is no network round-trip to an MDS for inode allocation.

CephFS in Kubernetes supports both kernel and FUSE mounters. The kernel mounter (`mount.ceph`) offers better performance (fewer context switches, direct kernel VFS integration), while the FUSE mounter (`ceph-fuse`) is more portable and easier to debug. The CSI driver can be configured to prefer one over the other via the `cephfs-mounter` StorageClass parameter.

### Object Storage (RGW)

RADOS Gateway (RGW) provides an S3-compatible (and Swift-compatible) HTTP API on top of RADOS. Unlike RBD and CephFS, which are accessed through the kernel block/filesystem layers, RGW is accessed via HTTP requests using standard S3 tools — the AWS CLI, boto3, MinIO clients, or any S3 SDK.

RGW stores objects as RADOS objects with a bucket index that maps S3 keys to RADOS object identifiers. Large objects are automatically split into multiple RADOS objects (multipart upload), and bucket indices can be sharded across multiple RADOS objects to prevent a single bucket from becoming a hotspot. RGW supports S3 features including versioning, lifecycle policies, server-side encryption (SSE-S3 and SSE-KMS), cross-origin resource sharing (CORS), and bucket policies.

In a Rook-managed cluster, the CephObjectStore CR deploys RGW pods behind a Kubernetes Service. Access credentials are created through CephObjectStoreUser CRDs, which generate Kubernetes Secrets containing the AccessKey and SecretKey. This is ideal for backup pipelines (Velero with S3 backend), artifact storage (ML model registries, container image registries), and application data that is naturally object-oriented.

---

## Part 5: Day-2 Operations

Deploying a Ceph cluster is the easy part. Keeping it healthy, performing, and cost-efficient over months and years is where the durable spine earns its weight.

### Scaling OSDs

Adding storage capacity to a running Ceph cluster is a two-step process: add physical disks to nodes, then let Rook discover and provision them. If the CephCluster CR uses `useAllNodes: true` and `useAllDevices: true`, new disks are automatically picked up and provisioned as OSDs within minutes. The cluster then begins rebalancing data — PGs are recalculated with the new OSDs included in the CRUSH map, and data migrates to fill the new capacity. This rebalancing is automatically throttled to avoid saturating the network or starving client I/O, but on large clusters (hundreds of OSDs), rebalancing can take days. Operators should add capacity during maintenance windows and monitor recovery progress with `ceph status` and `ceph osd df`.

Conversely, removing an OSD requires telling the cluster to drain data from it before the disk is decommissioned. The safe sequence is: `ceph osd out <osd-id>` (marks the OSD out of the cluster map), wait for data rebalancing to complete (`ceph status` shows HEALTH_OK), `ceph osd purge <osd-id>` (removes the OSD from the CRUSH map permanently). Rook automates much of this through the `removeOSDsIfOutAndSafeToRemove` CephCluster setting, but understanding the manual sequence is essential for troubleshooting.

### Disk Failure and Rebalancing

When a disk fails, the OSD daemon on that disk stops responding. The MONs detect the heartbeat failure, mark the OSD "down," and after the `mon_osd_down_out_interval` (default 5 minutes), mark it "out." At this point, the self-healing process begins: affected PGs are recalculated, and surviving OSDs begin backfilling data to restore replication.

During recovery, the cluster enters a "degraded" state — some PGs have fewer than the configured number of replicas. Client I/O continues (reads are served from surviving replicas, writes are redirected to new primaries), but performance degrades because recovery I/O competes with client I/O. The impact on client workload depends heavily on the recovery traffic throttle settings: `osd_recovery_max_active` (default 3) limits how many PGs can recover simultaneously per OSD, and `osd_recovery_sleep` can be tuned to introduce intentional delays between recovery operations, trading recovery speed for client performance during business hours. Once all PGs are healthy again, the cluster returns to HEALTH_OK.

Beyond individual disk failures, operators must plan for node-level failures — the loss of an entire host taking down all OSDs on that node simultaneously. The cluster's ability to handle this depends on the CRUSH failure domain configuration. With `failureDomain: host` and `size: 3`, Ceph ensures that no two replicas of the same PG land on the same host. When a node fails, every PG loses at most one replica, and the remaining two replicas keep the data available while recovery backfills a third copy onto other nodes. Without host-level failure domain configuration, it is possible that two replicas of a PG both live on the same physical node — a single power supply failure then causes data unavailability for that PG. This is why `failureDomain: host` is non-negotiable for any production cluster, and why larger deployments graduate to `failureDomain: rack` or `failureDomain: datacenter` as the number of nodes grows into the hundreds.

Two operational tips from hard experience: First, monitor SMART data on SSDs — they often degrade gradually before failing outright, and Ceph's `diskprediction_local` MGR module can forecast failures. Second, keep at least 10-20% free capacity per OSD. When an OSD fills above ~85%, Ceph issues HEALTH_WARN and may refuse writes. Running an OSD to 100% full can cause data loss because there is no space for recovery operations.

### Capacity Planning

Ceph's usable capacity is not simply the sum of raw disk capacities. The formula depends on replication factor and overhead:

- **Replicated pool, size=3, 100TB raw**: Usable ≈ 100TB / 3 ≈ 33TB. The cluster stores 3 copies of every object, so raw capacity divided by replication factor gives usable.
- **Erasure-coded pool, k=4, m=2, 100TB raw**: Usable ≈ 100TB × (4/(4+2)) ≈ 67TB. Erasure coding stores k data chunks and m parity chunks for every k data chunks, so the overhead ratio is (k+m)/k.

Additional overhead comes from the BlueStore space amplification (~10% for metadata), the MON and MGR LevelDB databases, and the operational headroom for recovery. A conservative planning rule: budget 30-40% overhead beyond the raw data you expect to store. If you need 100TB usable, plan for approximately 450TB raw with 3x replication.

### Upgrades

Upgrades in the Rook/Ceph ecosystem proceed in two independent tracks: Rook operator upgrades and Ceph version upgrades. Rook upgrades follow the standard operator pattern — update the operator image, apply updated CRDs and common resources, and the operator reconciles any changes. Ceph upgrades are triggered by changing the `cephVersion.image` field in the CephCluster CR. The Rook operator detects the change and performs a rolling upgrade of Ceph daemons in the correct order: MONs first (one at a time, waiting for quorum after each), then MGRs, then OSDs (configurable parallelism via `osdMaxUpdatesInParallel`, default 20), then MDS and RGW daemons.

The critical constraint is the Rook-Ceph version compatibility matrix. Rook v1.20 supports Ceph Squid (v19) and Tentacle (v20). Upgrading Rook and Ceph simultaneously is not supported: upgrade Rook first, verify cluster health, then upgrade Ceph. Always consult the Rook upgrade documentation for your specific version path.

For the Rook v1.20 upgrade specifically, the "Save existing CSI settings" step is mandatory: before upgrading, export your current CSI configuration with `kubectl get drivers.csi.ceph.io -o yaml` and `kubectl get operatorconfigs.csi.ceph.io -o yaml`. After upgrading the operator, install the `ceph-csi-drivers` chart with compatible settings. The Rook operator will not deploy CSI drivers anymore — it delegates entirely to the ceph-csi-operator.

### Monitoring

Ceph exposes a rich observability surface. The Ceph dashboard (accessible via `kubectl port-forward svc/rook-ceph-mgr-dashboard 8443:8443`) provides capacity utilization, PG status, OSD performance, and cluster health at a glance. The Prometheus module in the MGR exports thousands of metrics: per-OSD latency histograms, per-pool I/O rates, recovery throughput, cluster capacity projections, and daemon health checks.

Essential alerts to configure:
- **PG state**: Any PG that is not `active+clean` for more than a few minutes
- **OSD count**: An OSD going down unexpectedly
- **Capacity**: Cluster approaching nearfull ratio (>85%) or full ratio (>95%)
- **MON quorum**: Fewer MONs than the configured count reporting in
- **Recovery rate**: Backfill or recovery activity that persists abnormally long

The Prometheus ServiceMonitor provided by Rook integrates with the Prometheus Operator, making it straightforward to scrape Ceph metrics and route them to Alertmanager. For clusters without an existing Prometheus stack, the Ceph MGR dashboard alone provides sufficient operational visibility.

---

## Part 6: Decision Framework — When Rook/Ceph Earns Its Weight

Rook/Ceph is the most capable in-cluster storage solution available for Kubernetes, but capability comes with operational complexity. Running Ceph means understanding CRUSH maps, tuning PG counts, monitoring OSD utilization, planning capacity years ahead, and being prepared to debug recovery anomalies during incidents. This weight is justified when at least two of the following conditions apply:

**You are on bare metal or self-managed infrastructure.** If cloud-managed block storage is available and meets your requirements (capacity, performance, cost), using it is almost always simpler. Rook/Ceph shines when there is no cloud provider to delegate to — bare-metal Kubernetes, edge deployments, air-gapped environments, or multi-datacenter setups where data sovereignty requires storage under your control.

**You need multiple storage types from the same hardware.** If your workloads require block storage for databases, a shared filesystem for ML pipelines, and S3-compatible object storage for backups, Ceph provides all three from one cluster. The alternative — managing three separate storage systems — is often more complex than managing one Ceph cluster.

**Your scale justifies the operational investment.** At a few terabytes, a simple NFS server or hostPath volumes with manual replication might suffice. At hundreds of terabytes across dozens of nodes, the self-healing, scaling, and data distribution properties of Ceph become operational necessities rather than luxuries. The "operational investment breakeven" is typically around 10-15 nodes and 50-100TB of managed storage.

**You cannot tolerate vendor lock-in for storage.** When regulatory requirements, cost optimization, or multi-cloud strategy demand portability, Ceph provides a storage layer that runs identically on any infrastructure — on-premise, in any cloud, or at the edge. The Rook operator abstracts the Kubernetes integration, while Ceph abstracts the storage layer. Migrating a workload between environments becomes a matter of moving Kubernetes manifests, not re-architecting the storage backend.

**Hypothetical scenario:** A team running 200 Kubernetes nodes on bare metal with 800TB of mixed storage needs (databases, shared analytics data, and S3 backups). They evaluate three approaches: (a) deploy NFS for shared storage, a separate SAN for block, and MinIO for S3 — three systems to operate, three failure modes to monitor. (b) Use Rook/Ceph — one operator, three storage types, CRUSH-based data placement across racks. (c) Migrate to a managed Kubernetes service with cloud disk CSI. Approach (a) burdens a team of 3 SREs with 3 distinct storage systems. Approach (c) simplifies operationally but costs ~$3M/year in cloud storage fees. Approach (b) requires the team to learn Ceph internals but saves ~60% on storage costs while retaining full control. The decision depends on whether the team can absorb the Ceph learning curve and whether the cost savings justify the operational investment. There is no universal right answer — only the answer that fits your constraints.

### Patterns and Anti-Patterns

**Pattern: Use separate pools for different workload profiles.** Databases need low-latency replication on SSD-backed pools with size=3. Object storage for backups can use erasure coding on HDD-backed pools with k=8, m=3 for efficient capacity. Ceph's CRUSH device classes (`ssd`, `hdd`, `nvme`) automatically route data to the correct device type based on pool rules.

**Pattern: Always deploy the toolbox pod.** The `rook-ceph-tools` pod is a troubleshooting Swiss Army knife that costs almost nothing to run. During an incident, the last thing you want is to figure out how to build a debug container while storage is degraded.

**Pattern: Define explicit device filters in production.** `useAllDevices: true` is convenient for labs but dangerous in production — it can consume OS disks, swap partitions, or boot devices. Use `deviceFilter` or explicit device lists per node to control exactly which block devices become OSDs.

**Anti-Pattern: Running with even-numbered MONs.** Four MONs provide the same fault tolerance as three MONs (both survive 1 failure) while consuming more resources and slowing consensus. Always odd numbers: 3, 5, or — in very large clusters — 7.

**Anti-Pattern: Using the same pool for ReadWriteOnce and ReadWriteMany workloads.** RBD (block) and CephFS (filesystem) serve different access patterns. Provisioning a ReadWriteMany workload on an RBD-backed volume will not work — RBD requires exclusive access. Conversely, using CephFS for a high-throughput database may suffer from MDS metadata latency that RBD avoids.

**Anti-Pattern: Ignoring HEALTH_WARN.** Ceph issues warnings for a reason — nearfull OSDs, degraded PGs, clock skew between MONs. A HEALTH_WARN that persists for weeks often becomes a HEALTH_ERR during the next failure event. Investigate and resolve every warning before it escalates.

**Anti-Pattern: Deploying erasure coding on clusters with fewer than 4 nodes.** Erasure coding requires at least k+m distinct OSD hosts to survive a failure. With k=4, m=2 on a 3-node cluster, losing one node means losing access to data because the remaining 2 nodes cannot reconstruct 4 data chunks from 2 parity chunks. For small clusters, replication is simpler and safer.

---

## Did You Know?

- **CERN's physics data lives on Ceph.** The Large Hadron Collider generates roughly 1 GB/second of experimental data, and Ceph has been CERN's primary storage platform since 2013. The system survives multiple hardware failures daily — disks dying, network switches failing, power supplies burning out — without a single byte lost. When particle physicists trust Ceph with data that might contain evidence of new fundamental particles, your production PostgreSQL databases are in good hands.

- **Rook was the first storage project to graduate from the CNCF.** Accepted as an incubation project in 2018 and graduating in October 2020, Rook proved that complex distributed stateful workloads could be managed by Kubernetes operators. The graduation criteria require demonstrated adoption at scale, a healthy governance model, and a commitment to community sustainability — all met by the Rook project before any other storage project.

- **The CRUSH algorithm was published at SC '06 (Supercomputing 2006) and has not required a fundamental redesign since.** Sage Weil's paper "CRUSH: Controlled, Scalable, Decentralized Placement of Replicated Data" introduced the algorithm that still powers Ceph's data distribution two decades later. The stability of CRUSH is evidence that Ceph's core architecture was well-designed from the start — incremental improvements (straw2 buckets, device classes) have extended it without breaking the original model.

- **Bloomberg runs Rook/Ceph across thousands of nodes for financial data workloads.** Their platform requires on-premise storage for data sovereignty — financial market data cannot legally leave certain jurisdictions — and Rook/Ceph's combination of performance, reliability, and Kubernetes-native management made it the clear choice over proprietary storage appliances.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Running MONs on fewer than 3 separate nodes | Loses quorum if any MON node fails; cluster becomes unavailable | Always 3 or 5 MONs on distinct physical hosts with anti-affinity |
| Using `useAllDevices: true` in production | May consume OS disks, boot partitions, or unintended devices | Explicitly list devices per node with `deviceFilter` or `devices` in `storage.nodes` |
| Skipping `failureDomain: host` on pools | Replicas may land on the same node, making a node failure cause data loss | Set `failureDomain: host` (or `rack`/`zone` for larger clusters) on every pool |
| No resource limits on OSDs | OSD compaction and recovery I/O starve other pods on the same node | Set CPU/memory requests and limits; 2GB minimum memory per OSD |
| Ignoring `HEALTH_WARN` status for weeks | Warnings accumulate and become errors under the next failure event | Investigate every warning; a cluster that is HEALTH_WARN today is one disk failure from HEALTH_ERR |
| Not deploying the Ceph toolbox pod | Cannot run `ceph` commands during an incident | Deploy `rook-ceph-tools` Deployment as part of initial cluster setup |
| Deploying erasure coding on small clusters | Erasure coding with k=4, m=2 requires 6+ distinct failure domains to be safe | Use replication for clusters under 10 nodes; reserve erasure coding for larger deployments |
| Forgetting to enable volume expansion on StorageClasses | PVCs fill up and workloads crash because volumes cannot be resized | Set `allowVolumeExpansion: true` on every StorageClass; test resize workflow before production |

---

## Quiz

### Question 1
You manage a 5-node bare-metal Kubernetes cluster running PostgreSQL on RBD-backed PVCs. One node loses its SSD and the OSD goes down. Describe what Ceph does automatically and what you should verify to confirm recovery is proceeding correctly.

<details>
<summary>Show Answer</summary>

After the MONs detect the OSD heartbeat failure (within seconds), they mark the OSD "down." After the `mon_osd_down_out_interval` (default 300 seconds), the OSD is marked "out." At that point, Ceph recalculates PG placement for every PG that had a replica on the failed OSD, and surviving OSDs begin backfilling data to restore the configured replication factor. The cluster enters a "degraded" state (some PGs have fewer replicas than configured) but client I/O continues — PostgreSQL reads go to surviving replicas, writes are redirected to new primaries.

You should verify: (1) `ceph status` shows recovery progressing and PG states converging toward `active+clean`, not stuck in `down` or `peering`; (2) `ceph osd df` confirms the failed OSD is gone and remaining OSDs have headroom below the nearfull threshold; (3) monitoring shows recovery I/O is not saturating client-facing bandwidth — check `ceph pg dump` for recovery throughput rates. If recovery stalls, investigate whether any PG's acting set includes only unavailable OSDs (requiring manual intervention).
</details>

### Question 2
In Rook v1.20, how has CSI driver management changed compared to v1.19, and what operational steps must an administrator take when upgrading?

<details>
<summary>Show Answer</summary>

In Rook v1.19 and earlier, the Rook operator deployed and managed CSI driver components directly — the RBD and CephFS CSI plugins were configured through the `rook-ceph-operator-config` ConfigMap and deployed as sidecars or DaemonSets managed by the Rook operator lifecycle.

In Rook v1.20, the Rook operator no longer deploys CSI drivers. CSI is now admin-managed via the **ceph-csi-operator**, a separate operator from the Ceph CSI project. The Rook operator's CSI responsibility is limited to creating `OperatorConfig` and `Driver` custom resources that the ceph-csi-operator reconciles. When upgrading: (1) export existing CSI settings with `kubectl get drivers.csi.ceph.io -o yaml` and `kubectl get operatorconfigs.csi.ceph.io -o yaml`; (2) upgrade Rook operator to v1.20; (3) install the `ceph-csi-drivers` Helm chart (or apply `csi-operator.yaml` for manifest installs); (4) verify CSI driver pods are running and StorageClasses are functional. Failing to install the ceph-csi-drivers chart after upgrading will leave CSI in a failed state because the required service accounts and RBAC are no longer created by the Rook operator.
</details>

### Question 3
A team deploys Rook/Ceph with 3 MONs on a 3-node cluster. They configure replication size=3 and `failureDomain: host`. A node goes down for maintenance. Will client I/O continue? What about a second simultaneous node failure?

<details>
<summary>Show Answer</summary>

With 3 MONs on a 3-node cluster, the first node failure leaves 2 MONs running — exactly enough for quorum (2 out of 3). The cluster remains operational, but in a degraded state. PGs that had a replica on the failed node are now under-replicated (only 2 copies instead of 3), triggering recovery. Client I/O continues because reads are served from surviving replicas and writes are directed to available OSDs.

If a second node fails simultaneously, the MON count drops to 1 — below the quorum requirement of 2. The remaining MON stops serving because it can no longer guarantee a consistent cluster map. The cluster becomes **unavailable** for all I/O — no reads, no writes — even though most data may still be physically intact on the surviving disks. This is the classic 3-MON cliff: the cluster survives 1 MON failure gracefully but a second failure is catastrophic. For environments where double-node failure is a realistic scenario (e.g., shared power circuits), deploying 5 MONs across 5 nodes provides survival through 2 MON failures, though the cluster would still be degraded if those MONs also hosted OSDs.
</details>

### Question 4
You need to store 200TB of infrequently accessed archival data with maximum capacity efficiency. Would you choose a replicated pool or an erasure-coded pool? What specific k/m values would you select for a 12-node cluster where you want to survive 2 simultaneous node failures?

<details>
<summary>Show Answer</summary>

Choose an **erasure-coded pool**. For archival data, the access pattern is write-once, read-rarely, so the higher write latency of erasure coding (computing parity chunks on write) is acceptable. The capacity efficiency is dramatically better: replication at size=3 yields 33% usable capacity (200TB usable requires 600TB raw), while erasure coding with k=8, m=3 yields ~73% usable capacity (200TB usable requires ~275TB raw).

For a 12-node cluster surviving 2 node failures, select **k=8, m=3**. This means each PG is split into 8 data chunks and 3 parity chunks, spread across 11 distinct OSDs (ideally on 11 distinct nodes). Losing any 2 nodes can lose at most 2 chunks — with 3 parity chunks, you can reconstruct the data. However, your CRUSH rule must ensure that no more than 1 chunk per PG lands on any single node (using `step chooseleaf` with host-level failure domain). With k=8, m=3, your usable capacity is 8/(8+3) ≈ 73% of raw, and you survive 3 chunk failures, which translates to 2 node failures when chunks are properly distributed.
</details>

### Question 5
Your cluster reports HEALTH_WARN with "1 nearfull OSD(s)." What does this mean, what are the thresholds, and what operations will be blocked if the OSD reaches the full threshold?

<details>
<summary>Show Answer</summary>

Ceph tracks OSD utilization against two configurable thresholds: `mon_osd_nearfull_ratio` (default 0.85, i.e., 85%) and `mon_osd_full_ratio` (default 0.95, i.e., 95%). A "nearfull" OSD has crossed the nearfull threshold — Ceph issues HEALTH_WARN as a soft alert that capacity is running low. At this stage, client I/O continues normally.

If the OSD crosses the full threshold (95%), Ceph **blocks all writes** to pools that have PGs on that OSD — the cluster enters HEALTH_ERR. Reads still work, but any write operation returns ENOSPC (no space). This is catastrophic for any write-dependent workload. Recovery is possible by adding OSDs (which triggers rebalancing and moves data off the full OSD) or by manually reweighting the OSD to drain data, but the process takes time and the cluster is degraded during recovery. The operational lesson: treat nearfull warnings as urgent. Add capacity or rebalance before the full threshold is reached. A healthy cluster should keep OSD utilization below 70-75% to allow headroom for recovery after a disk failure.
</details>

### Question 6
You are evaluating Rook/Ceph versus a cloud-managed CSI driver (EBS CSI) for a new Kubernetes cluster running on AWS EC2 bare-metal instances. List three factors that should push you toward Rook/Ceph and three that should push you toward EBS CSI.

<details>
<summary>Show Answer</summary>

**Factors pushing toward Rook/Ceph:** (1) You need multiple storage types — block for databases, shared filesystem for ML pipelines, and S3-compatible object storage — all from the same physical disks. EBS CSI only provides block; S3 and EFS are separate billed services. (2) You plan to be multi-cloud or need bare-metal portability. Ceph runs identically on any infrastructure; migrating from AWS to on-premise means moving Kubernetes manifests, not re-architecting storage. (3) Your storage costs at scale (hundreds of TB) are dominated by per-GB cloud pricing. Ceph on bare-metal instance storage or attached NVMe drives costs roughly 60-70% less than EBS at large scale when factoring in snapshot and data transfer costs.

**Factors pushing toward EBS CSI:** (1) Your team does not have — and cannot acquire — Ceph operations expertise. EBS CSI requires zero storage administration beyond choosing a StorageClass. (2) Your storage needs are modest (under 50TB) and consist exclusively of block storage for databases. The operational overhead of Ceph is not justified at this scale. (3) You are deeply integrated with AWS services that EBS natively supports — EBS fast snapshot restore, cross-region snapshot copy, EBS-optimized instance networking. Ceph can replicate these capabilities but with more operational effort.
</details>

### Question 7
During a Rook upgrade from v1.19 to v1.20 using Helm, in what order must the three Helm charts be upgraded, and what happens if the `ceph-csi-drivers` chart is not installed?

<details>
<summary>Show Answer</summary>

The required upgrade order is: **(1) `rook-ceph`** (the operator chart, which upgrades the Rook operator and installs the ceph-csi-operator subchart), **(2) `ceph-csi-drivers`** (a new mandatory chart in v1.20 that configures CSI drivers via ceph-csi-operator resources), **(3) `rook-ceph-cluster`** (the cluster chart, which triggers the Ceph daemon upgrade if the Ceph image version changed).

If the `ceph-csi-drivers` chart is not installed after upgrading the `rook-ceph` chart to v1.20, the CSI driver will enter a failed state. The Rook operator no longer creates the CSI driver service accounts or RBAC — those come from the ceph-csi-drivers chart. Existing PVC mounts may continue to work temporarily (the node plugin DaemonSet is still running), but new PVC provisioning will fail because the controller plugin's service account is missing or misconfigured. The fix is to install the ceph-csi-drivers chart with the recommended `values.yaml` from the Rook repository, ensuring the driver name prefix matches the Rook operator namespace.
</details>

---

## Hands-On

### Task: Deploy Rook/Ceph on a Local Cluster and Verify Day-2 Operations

**Objective**: Deploy a Rook/Ceph cluster using Rook v1.20 on a local kind or minikube cluster, create block and filesystem StorageClasses, connect a workload, and verify health monitoring.

**Success Criteria**:
- [ ] Rook operator (v1.20.x) running and CephCluster reporting `Ready` condition
- [ ] Block StorageClass (`rook-ceph-block`) creating and binding PVCs with ReadWriteOnce access
- [ ] CephFS StorageClass (`rook-cephfs`) creating and binding PVCs with ReadWriteMany access
- [ ] A test workload successfully writing and reading data on both block and filesystem volumes
- [ ] Ceph health status returns `HEALTH_OK` (or `HEALTH_WARN` with an explainable reason in kind)
- [ ] Ceph dashboard accessible via port-forward showing cluster capacity and PG status

### Steps

```bash
# 1. Create a kind cluster with 3 worker nodes
cat > kind-rook-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
  - role: worker
EOF

kind create cluster --name rook-lab --config kind-rook-config.yaml

# 2. Install the Rook operator (v1.20)
helm repo add rook-release https://charts.rook.io/release
helm repo update

helm install --create-namespace --namespace rook-ceph \
  rook-ceph rook-release/rook-ceph \
  --version 1.20.0

# The rook-ceph chart now includes ceph-csi-operator as a subchart.
# You still need the separate ceph-csi-drivers chart:
helm repo add ceph-csi-operator https://ceph.github.io/ceph-csi-operator
helm install ceph-csi-drivers --namespace rook-ceph \
  ceph-csi-operator/ceph-csi-drivers \
  -f https://raw.githubusercontent.com/rook/rook/v1.20.1/deploy/charts/ceph-csi-drivers/values.yaml

kubectl -n rook-ceph rollout status deployment/rook-ceph-operator --timeout=300s

# 3. Deploy CephCluster (using directory-based OSDs for kind — no raw disks available)
cat > ceph-cluster-kind.yaml << 'EOF'
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata:
  name: rook-ceph
  namespace: rook-ceph
spec:
  cephVersion:
    image: quay.io/ceph/ceph:v20.2.2
    allowUnsupported: false
  dataDirHostPath: /var/lib/rook
  mon:
    count: 3
    allowMultiplePerNode: true   # Required for kind (3 workers, 3 MONs)
  mgr:
    count: 1
    modules:
      - name: dashboard
        enabled: true
      - name: prometheus
        enabled: true
  dashboard:
    enabled: true
    ssl: true
  storage:
    useAllNodes: true
    useAllDevices: false
    directories:
      - path: /var/lib/rook-osd   # Directory-based OSDs for kind
EOF

kubectl apply -f ceph-cluster-kind.yaml

echo "Waiting for Ceph cluster to become ready (this takes 3-5 minutes)..."
kubectl -n rook-ceph wait --for=condition=Ready cephcluster/rook-ceph --timeout=600s

# 4. Deploy the Ceph toolbox for debugging and health checks
kubectl apply -f https://raw.githubusercontent.com/rook/rook/release-1.20/deploy/examples/toolbox.yaml
kubectl -n rook-ceph wait --for=condition=Ready pod -l app=rook-ceph-tools --timeout=120s

# 5. Create a Block Pool and StorageClass
cat > ceph-block.yaml << 'EOF'
apiVersion: ceph.rook.io/v1
kind: CephBlockPool
metadata:
  name: replicapool
  namespace: rook-ceph
spec:
  failureDomain: host
  replicated:
    size: 2                      # 2 replicas for kind (limited nodes)
    requireSafeReplicaSize: false
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-ceph-block
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  clusterID: rook-ceph
  pool: replicapool
  imageFormat: "2"
  imageFeatures: layering
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
reclaimPolicy: Delete
allowVolumeExpansion: true
EOF

kubectl apply -f ceph-block.yaml

# 6. Create a CephFS Filesystem and StorageClass
cat > ceph-fs.yaml << 'EOF'
apiVersion: ceph.rook.io/v1
kind: CephFilesystem
metadata:
  name: ceph-shared
  namespace: rook-ceph
spec:
  metadataPool:
    replicated:
      size: 2
  dataPools:
    - name: data0
      replicated:
        size: 2
  metadataServer:
    activeCount: 1
    activeStandby: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-cephfs
provisioner: rook-ceph.cephfs.csi.ceph.com
parameters:
  clusterID: rook-ceph
  fsName: ceph-shared
  pool: ceph-shared-data0
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-cephfs-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-cephfs-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
reclaimPolicy: Delete
allowVolumeExpansion: true
EOF

kubectl apply -f ceph-fs.yaml

# 7. Provision a Block PVC and run a pod that writes data
cat > test-block-pvc.yaml << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: rook-ceph-block
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: block-test
spec:
  containers:
    - name: writer
      image: busybox
      command: ["sh", "-c"]
      args:
        - |
          echo "Writing data to Rook/Ceph block volume..."
          dd if=/dev/urandom of=/data/testfile bs=1M count=100
          echo "Wrote 100MB to /data/testfile"
          md5sum /data/testfile
          echo "Block storage test PASSED"
          sleep 3600
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: test-block-pvc
EOF

kubectl apply -f test-block-pvc.yaml
kubectl wait --for=condition=Ready pod/block-test --timeout=120s
kubectl logs block-test

# 8. Verify Ceph cluster health through the toolbox
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph df

# 9. Access the Ceph Dashboard
kubectl -n rook-ceph get secret rook-ceph-dashboard-password \
  -o jsonpath='{.data.password}' | base64 --decode
echo ""  # newline after the password
kubectl -n rook-ceph port-forward svc/rook-ceph-mgr-dashboard 8443:8443
# Open https://localhost:8443 in your browser (accept the self-signed cert)
# Username: admin, Password: (from command above)
```

### Verification

```bash
# Confirm PVC is bound
kubectl get pvc test-block-pvc
# STATUS should be "Bound"

# Confirm pod wrote data successfully
kubectl logs block-test | grep "PASSED"

# Confirm Ceph health
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph health
# Should output: HEALTH_OK (or HEALTH_WARN with explanation in kind)

# Confirm StorageClasses exist and are default-ready
kubectl get storageclass | grep rook

# Confirm CSI driver pods are running (ceph-csi-operator managed in v1.20)
kubectl -n rook-ceph get pods -l app.kubernetes.io/name=ceph-csi-operator

# Clean up when done
kind delete cluster --name rook-lab
```

---

## Sources

- [Rook Documentation — latest release](https://rook.io/docs/rook/latest-release/)
- [Rook CephCluster CRD Reference — v1.20](https://rook.io/docs/rook/latest-release/CRDs/Cluster/ceph-cluster-crd/)
- [Rook Upgrade Guide — v1.19 to v1.20](https://rook.io/docs/rook/latest-release/Upgrade/rook-upgrade/)
- [Rook Helm Charts — ceph-csi-drivers chart](https://rook.io/docs/rook/latest-release/Helm-Charts/csi-drivers-chart/)
- [Rook GitHub Repository](https://github.com/rook/rook)
- [Ceph Documentation — latest stable](https://docs.ceph.com/en/latest/)
- [Ceph Architecture — RADOS overview](https://docs.ceph.com/en/latest/architecture/)
- [Ceph CRUSH Algorithm — documentation](https://docs.ceph.com/en/latest/rados/operations/crush-map/)
- [CRUSH Paper — Weil et al., SC '06](https://ceph.com/assets/pdfs/weil-crush-sc06.pdf)
- [ceph-csi-operator — GitHub](https://github.com/ceph/ceph-csi-operator)
- [Ceph CSI Driver Configuration](https://rook.io/docs/rook/latest-release/Storage-Configuration/Ceph-CSI/ceph-csi-drivers/)
- [Ceph Hardware Recommendations](https://docs.ceph.com/en/latest/start/hardware-recommendations/)
- [Data on Kubernetes Community](https://dok.community/)

---

## Next Module

[Module 16.2: MinIO — S3-Compatible Object Storage on Kubernetes](../module-16.2-minio/)

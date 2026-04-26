---
title: "Module 6.3: Velero"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.3-velero
sidebar:
  order: 4
---

> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes  
> **Prerequisites**: Kubernetes resources, namespaces, PersistentVolumes, cloud object storage, and basic disaster recovery terminology.  
> **Lab assumptions**: Examples target Kubernetes 1.35+, a working `kubectl` context, and the Velero CLI installed locally.

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a Velero backup strategy that separates cluster recovery, application recovery, persistent data recovery, and GitOps configuration recovery.
- **Configure** manual and scheduled Velero backups with namespace filters, resource filters, volume handling, retention periods, and restore validation steps.
- **Debug** failed or incomplete restores by inspecting Backup, Restore, BackupStorageLocation, VolumeSnapshotLocation, and workload status signals.
- **Evaluate** when to use CSI snapshots, file-system backup with node agents, application hooks, or a separate database-native backup system.
- **Operate** Velero as a reliability service by adding restore drills, monitoring, cost controls, access boundaries, and runbook checkpoints.

## Why This Module Matters

A platform team at a growing software company believed it had Kubernetes disaster recovery covered because every cluster had etcd snapshots, GitOps repositories, and a Velero Schedule. Then a storage class migration corrupted the production billing database volume, and the incident commander learned that all three recovery mechanisms protected different pieces of the system. GitOps could recreate Deployments and Services, but it could not recreate runtime data. The etcd snapshot captured cluster state, but it was tied to the damaged control plane and still did not provide a clean application-level rollback. Velero had backups, but nobody had practiced restoring them into an isolated namespace with volume data attached.

The hard lesson is that “we have backups” is not an engineering claim until someone has restored a workload, verified the data, measured the restore time, and documented the decision path. Velero is valuable because it lets teams back up Kubernetes resources in an application-shaped way: namespaces, labels, selected resources, persistent volumes, and restore mappings. It is not magic, and it is not a substitute for every database backup strategy. It is a tool that becomes reliable only when the platform team designs the backup scope, storage backend, volume approach, and operational checks deliberately.

This module teaches Velero from that operational point of view. You will start with the recovery model, then install and scope backups, then reason about resources and volumes, then walk through a formal restore example before building your own lab. The goal is not to memorize Velero commands. The goal is to make backup and restore decisions under pressure without guessing.

## 1. Build the Recovery Model Before Installing Velero

Velero works best when you treat it as one layer in a recovery system, not as the whole recovery system. Kubernetes failures can happen at the control plane, node, namespace, application, storage, cloud account, or human-change layer. A single backup mechanism rarely covers every layer cleanly, so senior platform teams combine several recovery paths and define which one answers which kind of failure.

The first design question is not “how do we install Velero?” but “what are we trying to recover, under what time pressure, and into what environment?” If a developer deletes a namespace, Velero may be the fastest path. If a whole cluster is lost, you may need infrastructure automation to create a replacement cluster, GitOps to reapply platform services, and Velero to restore selected application state. If a database contains logically corrupted data from three days ago, a volume snapshot from last night might restore the corruption faithfully, which means a database-native point-in-time recovery plan may matter more than a Kubernetes restore.

```ascii
+--------------------------------------------------------------------------+
|                         RECOVERY LAYERS IN PRACTICE                      |
+----------------------+-------------------------+-------------------------+
| Layer                | Best recovery source    | What it usually misses  |
+----------------------+-------------------------+-------------------------+
| Cluster control      | etcd snapshot / IaC     | App-level volume data   |
| Platform components  | GitOps + IaC            | Runtime generated state |
| Application objects  | Velero resource backup  | External dependencies   |
| Persistent volumes   | CSI snapshot / FSB      | Logical database intent |
| Database contents    | Database-native backup  | Kubernetes object graph |
| Human runbook        | Restore drill evidence  | Nothing unless tested   |
+----------------------+-------------------------+-------------------------+
```

A useful mental model is to see Velero as “application graph recovery.” It captures Kubernetes API objects and, when configured, the storage artifacts behind PersistentVolumeClaims. That graph includes Deployments, StatefulSets, Services, ConfigMaps, Secrets, PVCs, Ingresses, ServiceAccounts, Roles, RoleBindings, custom resources, and other objects you select. It can restore that graph into the same cluster, a replacement cluster, or a different namespace mapping, which makes it useful for disaster recovery and migration.

Velero does not understand every application’s consistency boundary by default. It can trigger hooks before or after backup, and it can use storage snapshots or file-system backup, but it does not automatically know whether PostgreSQL, Kafka, Elasticsearch, or a custom stateful service is in a recoverable state. For databases, the safest design often combines Velero for Kubernetes objects with database-native backup for the data itself. That split sounds more complex, but it prevents a platform backup tool from pretending to solve application-level consistency alone.

The three common recovery mechanisms should reinforce each other rather than compete. GitOps should describe desired configuration and make platform rebuilds repeatable. Etcd backups should protect the control plane when you operate your own cluster or have access to control-plane restore workflows. Velero should protect application-shaped Kubernetes state and selected persistent data. When these are documented together, responders can choose a path based on failure type instead of trying the most familiar command first.

| Failure scenario | Strong first response | Why that response fits | Velero role |
|---|---|---|---|
| A developer deletes one namespace during cleanup | Restore selected namespace from Velero | The cluster is healthy, and only application resources are missing | Primary recovery mechanism |
| A managed cluster is accidentally destroyed | Recreate cluster with IaC, then restore app state | The control plane no longer exists, so Velero must be reinstalled into a replacement | Restores selected workloads after bootstrap |
| A StatefulSet volume is corrupted by bad writes | Use app-aware backup or known-good snapshot | A snapshot may contain logical corruption if taken after the bad writes | Helpful only if restore point predates corruption |
| A Deployment manifest is changed incorrectly | Revert through GitOps | Desired configuration is the issue, not runtime loss | Secondary, usually not needed |
| A storage region is unavailable | Fail over to another region with replicated backups | Local snapshots may be unavailable with the region | Useful only if object storage and snapshots are replicated |
| A CRD is deleted before its custom resources | Restore CRD and resources in correct order | Kubernetes cannot accept custom resources without their definitions | Velero can help, but restore ordering must be checked |

Active check: imagine your production namespace is deleted at 10:00, and the most recent successful Velero backup completed at 02:00. Before reading further, decide what data can be recovered, what data may be lost, and which system should tell you whether the eight-hour gap is acceptable. The correct answer depends on recovery point objective, application write behavior, and whether persistent data has a more frequent backup path than Kubernetes objects.

Recovery objectives should be written before schedules are created. The recovery point objective describes how much data loss the business can tolerate. The recovery time objective describes how long the service can remain unavailable. A daily Velero backup might satisfy a documentation site, but it may be unacceptable for a billing service with constant writes. A fifteen-minute database backup may be appropriate for the database, while a daily Velero resource backup may still be enough for the Kubernetes object graph because Deployments and Services change less often.

Retention is a second design decision, not a default value to copy. Short retention reduces cost and limits stale data exposure, but it may prevent recovery from slow-moving corruption discovered late. Long retention improves forensic and rollback options, but it increases storage cost and may keep sensitive Secrets longer than intended. Good retention policy usually has tiers: short-lived frequent backups, medium-lived weekly backups, and a smaller set of long-lived monthly backups governed by compliance rules.

The storage location is part of the reliability design. If the cluster and backup bucket live in the same account, region, and access boundary, a single cloud incident or credential compromise can affect both. Production-grade designs usually separate permissions, enable bucket versioning or object lock where appropriate, replicate critical backup data across regions, and restrict who can delete backups. Velero can write the backup, but the platform team must protect the place where the backup lands.

A backup is also a security artifact. It may contain Secrets, ConfigMaps with credentials, Ingress hostnames, database connection strings, and custom resources that expose operational topology. That means backup storage should have encryption at rest, transport encryption, audit logging, lifecycle controls, and least-privilege write access. The people who can restore backups may effectively be able to recreate sensitive workloads, so restore permissions deserve the same scrutiny as production deployment permissions.

```ascii
+------------------+        +---------------------+        +------------------+
| Git repository   |        | Kubernetes cluster  |        | Backup storage   |
| desired config   |        | runtime API objects |        | object + volume  |
+---------+--------+        +----------+----------+        +---------+--------+
          |                            |                             |
          | GitOps reconciles          | Velero reads selected       |
          | known desired state        | objects and volume data     |
          v                            v                             v
+------------------+        +---------------------+        +------------------+
| Recreate intent  |        | Restore app graph   |        | Survive cluster  |
| from reviewed    |        | into same or new    |        | loss when stored |
| commits          |        | cluster             |        | independently    |
+------------------+        +---------------------+        +------------------+
```

A reliable Velero program therefore starts with a recovery matrix. For each application, identify the namespace, labels, PVCs, external dependencies, data consistency mechanism, backup frequency, retention, restore target, and validation command. This matrix prevents the platform team from discovering during an incident that a workload depends on a cloud database, external DNS record, certificate issuer, or object bucket that Velero was never designed to restore.

The backup matrix should be reviewed with application owners because platform teams rarely know every consistency requirement. A queue service may tolerate replay from a checkpoint, while a payment database needs exact transactional guarantees. A stateless API may need only GitOps, while a customer-upload service may need Velero for PVC metadata and a separate object-store replication policy for uploaded files. The conversation matters because the backup tool cannot infer business criticality from Kubernetes YAML.

Stop and think: if you restored a namespace perfectly but the application still pointed at a deleted external database, would you call the Velero restore successful? From a Kubernetes object perspective, it might be complete. From a service recovery perspective, it failed. This is why the runbook must define application-level validation, not only `kubectl get pods`.

## 2. Install Velero and Choose the Backup Boundary

Velero has two major runtime parts: a server inside the cluster and a CLI used by operators. The server watches Velero custom resources such as Backups, Restores, Schedules, BackupStorageLocations, and VolumeSnapshotLocations. The CLI creates and inspects those resources, but the controller logic runs inside the cluster. That separation matters because deleting your local terminal does not stop a backup, while a broken Velero Deployment inside the cluster does.

The storage provider plugin connects Velero to object storage and, when supported, volume snapshot APIs. On AWS, the plugin writes Kubernetes backup data to S3 and can work with EBS snapshots. On other platforms, equivalent plugins connect to GCS, Azure Blob, or S3-compatible systems. The plugin version must match the Velero server version, so production installations should pin compatible versions instead of copying an old blog post command.

For the examples below, `kubectl` is shown first and then abbreviated as `k` after the alias is created. The alias is common in Kubernetes operations because Velero work often alternates between `velero` commands and direct Kubernetes inspection. Run the alias in your shell before using the shorter commands.

```bash
alias k=kubectl
kubectl version --client
velero version --client-only
```

A production AWS installation needs a bucket, credentials or workload identity, a plugin, and region configuration. The command below uses a current AWS plugin family compatible with recent Velero releases, but production teams should verify the compatibility matrix during upgrades. The important teaching point is the shape of the install: provider, plugin image, bucket, backup location configuration, snapshot location configuration, credentials, and an explicit wait for readiness.

```bash
export BUCKET=velero-backups-example
export REGION=us-west-2

velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.13.0 \
  --bucket "$BUCKET" \
  --backup-location-config region="$REGION" \
  --snapshot-location-config region="$REGION" \
  --secret-file ./credentials-velero \
  --use-node-agent \
  --wait
```

The credentials file for a simple lab installation uses the AWS shared credentials format. Production installations should prefer cloud-native workload identity where available, because static keys create rotation and leakage risk. If static credentials are used, their policy should be limited to the specific bucket, snapshot operations required by the environment, and the minimum object actions Velero needs.

```ini
[default]
aws_access_key_id=REPLACE_WITH_ACCESS_KEY
aws_secret_access_key=REPLACE_WITH_SECRET_KEY
```

After installation, verify both Kubernetes readiness and Velero storage readiness. A running Velero Pod only proves that the controller process started. A usable backup location proves that the server can authenticate and reach object storage. Many failed backup programs looked healthy at the Pod level while every backup was failing because a bucket policy, region, endpoint, or credential had drifted.

```bash
k get namespace velero
k get pods -n velero
k get backupstoragelocations -n velero
velero backup-location get
velero version
```

The Velero architecture is easier to reason about if you separate the control resources from the stored artifacts. A Backup custom resource tells the Velero server what to collect. The server writes metadata, Kubernetes object definitions, logs, and related files to object storage. If volume snapshots are enabled and supported, Velero also coordinates snapshot creation through the storage provider or CSI snapshot mechanisms. A Restore custom resource then asks the server to read those artifacts and recreate selected objects.

```ascii
+--------------------------------------------------------------------------------+
|                                KUBERNETES CLUSTER                               |
|                                                                                |
|  +----------------------+       watches        +-----------------------------+  |
|  | Velero custom        |--------------------->| Velero server controllers   |  |
|  | resources            |                      | backup, restore, schedule   |  |
|  +----------+-----------+                      +--------------+--------------+  |
|             |                                                   |               |
|             | status updates                                    | writes/reads   |
|             v                                                   v               |
|  +----------------------+                         +--------------------------+  |
|  | Backup / Restore     |                         | BackupStorageLocation    |  |
|  | status and logs      |                         | object storage endpoint  |  |
|  +----------------------+                         +-------------+------------+  |
|                                                                  |               |
+------------------------------------------------------------------|---------------+
                                                                   |
                                                                   v
+--------------------------------------------------------------------------------+
|                              EXTERNAL BACKUP DATA                               |
|                                                                                |
|  +-----------------------------+        +------------------------------------+  |
|  | Object storage bucket       |        | Volume snapshot service or data    |  |
|  | resources, metadata, logs   |        | mover target for persistent data   |  |
|  +-----------------------------+        +------------------------------------+  |
+--------------------------------------------------------------------------------+
```

The backup boundary is where many teams make their first serious mistake. A whole-cluster backup feels safe because it includes more, but it can be slow, expensive, noisy, and dangerous to restore blindly. A narrow namespace backup is easier to restore and validate, but it may miss cluster-scoped resources such as CRDs, StorageClasses, ClusterRoles, or admission configuration that the namespace depends on. The right boundary is the smallest set of objects that can be restored into a working application with known prerequisites.

Velero supports boundary choices through namespace filters, resource filters, label selectors, and cluster-resource options. Namespace filters are a good starting point when each application has a clear namespace. Label selectors are useful when applications share namespaces or when you want a logical backup that follows `app.kubernetes.io/part-of`. Resource filters help exclude noisy or recreated objects such as Events. Cluster-resource handling should be explicit in runbooks because defaults can surprise teams when namespace filters and custom resources interact.

```bash
velero backup create payments-namespace \
  --include-namespaces payments \
  --exclude-resources events,events.events.k8s.io \
  --ttl 168h

velero backup create payments-by-label \
  --selector app.kubernetes.io/part-of=payments \
  --exclude-resources events,events.events.k8s.io \
  --ttl 168h

velero backup create payments-with-cluster-prereqs \
  --include-namespaces payments \
  --include-cluster-resources=true \
  --exclude-resources events,events.events.k8s.io \
  --ttl 168h
```

A declarative Backup resource is better for reviewable operational patterns than one-off CLI history. The CLI is excellent during incident response and exploration, but a YAML object can be stored in a runbook repository, reviewed by peers, and applied consistently. The manifest below backs up two namespaces, excludes event noise, enables volume snapshots, stores the backup in the default location, and keeps it for thirty days.

```yaml
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: production-apps-manual
  namespace: velero
spec:
  includedNamespaces:
    - payments
    - checkout
  excludedResources:
    - events
    - events.events.k8s.io
  snapshotVolumes: true
  storageLocation: default
  volumeSnapshotLocations:
    - default
  ttl: 720h
```

A Schedule wraps a Backup template in a cron expression. The Schedule itself is not the backup; it creates Backup objects over time. Each Backup receives its own TTL when created, so deleting the Schedule later does not automatically delete every Backup it already produced. This detail matters for cost control and compliance because stale backup objects can remain after an application is decommissioned.

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: payments-daily
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
      - payments
    excludedResources:
      - events
      - events.events.k8s.io
    snapshotVolumes: true
    ttl: 168h
---
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: platform-weekly
  namespace: velero
spec:
  schedule: "0 3 * * 0"
  template:
    includedNamespaces:
      - "*"
    excludedResources:
      - events
      - events.events.k8s.io
    snapshotVolumes: true
    ttl: 720h
```

The command line equivalent is useful when creating a schedule during a lab or an incident. Always inspect the created Schedule afterward, because a typo in the cron expression or namespace name can silently encode the wrong operational promise. Operators should also check the Backups created by the Schedule, not just the Schedule object itself.

```bash
velero schedule create payments-daily \
  --schedule="0 2 * * *" \
  --include-namespaces payments \
  --exclude-resources events,events.events.k8s.io \
  --snapshot-volumes \
  --ttl 168h

velero schedule get
velero schedule describe payments-daily
velero backup get
```

Active check: your team asks for “a backup of production,” and production contains `payments`, `checkout`, `monitoring`, `cert-manager`, and `ingress-nginx` namespaces. Decide whether you would create one whole-cluster Schedule or several application-specific Schedules. A strong answer names the restore blast radius, cluster prerequisites, ownership boundaries, and how you would prove the restored application works.

## 3. Design Backups for Resources, Volumes, and Application Consistency

Kubernetes resources and persistent data have different failure modes, so they need different backup reasoning. A Deployment can be recreated from Git, from Velero, or by a controller after a restore. A PersistentVolume contains mutable state that may not exist anywhere else. A Secret may be included in a Velero backup, but restoring an old Secret can reintroduce retired credentials. Treating all resources equally leads to backups that are either incomplete or risky to restore.

The table below is a practical classification tool. It does not replace application-specific knowledge, but it helps you ask better questions. When reviewing a backup plan, walk through each resource class and decide whether Velero should include it, whether GitOps should own it, whether an external system should own it, and how restore validation proves success.

| Resource or data type | Usually include in Velero | Main risk during restore | Validation signal |
|---|---|---|---|
| Deployments and StatefulSets | Yes, when restoring app graph | Image, config, or admission policy drift may block Pods | Desired replicas become available |
| Services and Ingresses | Yes, with environment awareness | Restored endpoints may conflict with live traffic routing | Service has endpoints and expected DNS path |
| ConfigMaps | Yes, unless fully GitOps-owned | Old configuration can reintroduce a bad setting | App starts with expected config version |
| Secrets | Often yes, with strict storage security | Old or exposed credentials may be restored | App authenticates and audit trail is acceptable |
| PVCs and PV metadata | Yes, when workloads need volumes | Metadata without data is misleading | PVC binds and application sees expected data |
| Volume contents | Only with snapshot or file-system backup | Crash-consistent data may not be app-consistent | Application-level data checks pass |
| Events and transient status | Usually exclude | Noise increases size and restore confusion | Not needed for recovery |
| CRDs and custom resources | Include deliberately | Restoring custom resources before CRDs can fail | Controllers reconcile restored custom resources |

Velero can handle persistent volume data in two broad ways. The first is storage snapshots, commonly through CSI or provider snapshot APIs. Snapshots are fast and efficient because the storage platform creates point-in-time copies. The second is file-system backup through the Velero node agent, which walks volume files and stores them through Velero’s data path. File-system backup is more portable across storage providers, but it can be slower and more sensitive to large file counts.

The choice is not simply “snapshots are better.” CSI snapshots can be very fast, but they are often tied to a storage class, cloud region, account, and restore environment. File-system backup can be slower, but it may work where snapshots are unavailable or when moving across clusters with different storage backends. Database-native backup may be best when the application needs transaction-aware restore points, incremental logs, or point-in-time recovery.

```ascii
+----------------------+----------------------+-----------------------------+
| Volume approach      | Strength             | Watch carefully             |
+----------------------+----------------------+-----------------------------+
| CSI snapshot         | Fast point-in-time   | Provider, region, class     |
| Provider snapshot    | Mature cloud path    | Cloud permissions and quota |
| File-system backup   | Portable data copy   | Runtime and file count      |
| Database-native      | App consistency      | Separate restore workflow   |
+----------------------+----------------------+-----------------------------+
```

A Velero install that uses node agents can enable file-system backup. The flags below install the node agent and make file-system backup the default for volumes. That default is convenient for labs, but production teams often choose per-workload policy because some volumes are too large, too hot, or better protected by application-native tools.

```bash
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.13.0 \
  --bucket "$BUCKET" \
  --backup-location-config region="$REGION" \
  --snapshot-location-config region="$REGION" \
  --secret-file ./credentials-velero \
  --use-node-agent \
  --default-volumes-to-fs-backup \
  --wait
```

Per-pod annotations are useful when you want explicit file-system backup for selected volumes. This example marks the `data` volume for backup. The Pod still needs to mount a PersistentVolumeClaim, and Velero still needs node-agent capability, but the annotation documents intent near the workload.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: report-writer
  namespace: analytics
  annotations:
    backup.velero.io/backup-volumes: data
spec:
  containers:
    - name: app
      image: nginx:1.27
      volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: report-writer-data
```

Application hooks add another consistency tool. A pre-backup hook can flush data, pause writes briefly, create a database dump, or place a marker file. A post-backup hook can resume a process or clean temporary files. Hooks are powerful, but they must be tested carefully because a failing hook can delay backups or leave an application in an unexpected state if written poorly.

The manifest below shows a Backup with a pre-hook that asks a PostgreSQL container to create a dump file inside a mounted backup directory. This is still not a full PostgreSQL backup strategy for every environment, but it demonstrates the pattern. In production, you would review authentication, storage path, dump size, timeout, and whether the database-native backup tool provides a better guarantee.

```yaml
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: orders-with-hook
  namespace: velero
spec:
  includedNamespaces:
    - orders
  snapshotVolumes: true
  ttl: 168h
  hooks:
    resources:
      - name: postgres-dump
        includedNamespaces:
          - orders
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: orders-db
        pre:
          - exec:
              container: postgres
              command:
                - /bin/bash
                - -c
                - pg_dump -U postgres orders > /backup/orders.sql
              onError: Fail
              timeout: 10m
```

Stop and think: a pre-hook creates `/backup/orders.sql`, but the `/backup` path is an emptyDir volume rather than a persistent volume included in the backup. What will happen during restore? The dump command may succeed, the backup may succeed, and the restored workload may still lack the dump file because the data was written to storage that Velero did not preserve. This is why hooks must be paired with storage design, not treated as a checklist item.

Resource filtering should be driven by restore intent. Excluding Secrets may satisfy a security concern, but it can also make restored Pods fail if the target cluster does not provide replacement Secrets. Including cluster-scoped resources may make a migration easier, but it can also overwrite or conflict with target-cluster policy. A careful backup design names what is intentionally included, what is intentionally excluded, and what must already exist in the restore environment.

Velero restore operations can map namespaces, include or exclude resources, and skip volume restore when you only want objects. Namespace mapping is especially useful for validation drills because it lets you restore `payments` into `payments-restore-test` without disturbing production. You still need to watch for cluster-scoped resources, external DNS, Ingress hostnames, and controllers that assume a fixed namespace.

```bash
velero restore create payments-drill \
  --from-backup payments-namespace \
  --namespace-mappings payments:payments-restore-test

velero restore create payments-resources-only \
  --from-backup payments-namespace \
  --namespace-mappings payments:payments-restore-test \
  --restore-volumes=false

velero restore create payments-services-only \
  --from-backup payments-namespace \
  --include-resources services,endpointslices.discovery.k8s.io
```

Restore validation should look beyond Velero status. A Restore can complete with warnings, and Kubernetes can accept objects that later fail admission, scheduling, image pulling, or application startup. Good validation checks Restore status, restore logs, namespace resources, PVC binding, Pod readiness, application health endpoints, and domain-specific data. The restore is not done until the workload proves it can serve the scenario the business cares about.

```bash
velero restore get
velero restore describe payments-drill --details
velero restore logs payments-drill
k get all -n payments-restore-test
k get pvc -n payments-restore-test
k get events -n payments-restore-test --sort-by=.lastTimestamp
```

Senior operators also inspect what Velero decided to back up. `velero backup describe --details` shows included namespaces, included and excluded resources, storage location, volume snapshot information, and warnings. `velero backup logs` shows controller behavior and failures that may not be obvious from the one-line status. A Completed backup with warnings deserves review before it becomes the only recovery point for a critical service.

```bash
velero backup get
velero backup describe payments-namespace --details
velero backup logs payments-namespace
k get backups.velero.io -n velero
k describe backup payments-namespace -n velero
```

The most reliable pattern is a restore drill that runs into an isolated namespace on a schedule. The drill creates a fresh restore namespace, restores the latest backup with namespace mapping, waits for workloads, runs application checks, records results, and deletes the drill namespace after evidence is captured. This turns backup correctness from an assumption into an observable practice.

## 4. Worked Example: Diagnose and Restore a Failed Namespace

A worked example gives you a pattern to copy before the hands-on exercise asks you to perform a similar recovery. In this scenario, the `catalog` namespace was deleted during a cleanup task. The cluster is healthy, GitOps is temporarily paused to avoid fighting the restore, and the team wants to restore the namespace from the latest successful Velero backup. The application has one Deployment, one Service, one ConfigMap, one Secret, and one PVC containing uploaded product images.

**Input**

The incident commander gives you these facts. The `catalog` namespace is gone. The latest known good application behavior was before 09:30. The backup schedule is named `catalog-daily`, and operators believe it runs at 02:15. The team needs a restore into `catalog-restore` first, not directly into `catalog`, because they want to verify data before routing traffic.

```bash
k get ns catalog
velero schedule get
velero backup get
```

Expected symptoms look like this. The exact timestamps will differ in a real cluster, but the shape is what matters: the namespace is missing, the schedule exists, and at least one recent backup completed before the deletion. A missing schedule or a failed latest backup would change the recovery plan.

```bash
Error from server (NotFound): namespaces "catalog" not found

NAME            STATUS    CREATED                         SCHEDULE       BACKUP TTL   LAST BACKUP
catalog-daily   Enabled   2026-04-20 10:18:00 +0000 UTC   15 2 * * *     168h         2026-04-26 02:15:08 +0000 UTC

NAME                         STATUS      ERRORS   WARNINGS   CREATED                         EXPIRES
catalog-daily-202604260215   Completed   0        0          2026-04-26 02:15:08 +0000 UTC   2026-05-03 02:15:08 +0000 UTC
catalog-daily-202604250215   Completed   0        0          2026-04-25 02:15:06 +0000 UTC   2026-05-02 02:15:06 +0000 UTC
```

**Solution step 1: confirm the backup contents before restoring.**

Do not restore only because a backup says Completed. First inspect details to confirm that the backup included the namespace, did not exclude PVCs, and has usable volume information. This step prevents a common incident mistake: spending time restoring a backup that could never recover the missing data.

```bash
velero backup describe catalog-daily-202604260215 --details
velero backup logs catalog-daily-202604260215
```

The decision point is whether this backup matches the recovery objective. If the deletion happened after 09:30 and the backup was at 02:15, the Kubernetes objects are from earlier that morning. That may be acceptable for manifests and ConfigMaps, but the PVC data may be stale if product images changed after the backup. The incident commander must compare this against the recovery point objective instead of assuming “latest” means “good enough.”

**Solution step 2: restore into an isolated namespace.**

Namespace mapping lets the team inspect the restored application without immediately reusing the original namespace. This protects production from accidental routing conflicts and gives responders a place to run data checks. It also reveals whether the application has hard-coded namespace assumptions.

```bash
velero restore create catalog-drill-20260426 \
  --from-backup catalog-daily-202604260215 \
  --namespace-mappings catalog:catalog-restore
```

After creating the restore, watch both Velero and Kubernetes. Velero may finish recreating objects before Pods become ready. Kubernetes may then reveal scheduling, storage, image, or admission problems. Treat these as different layers of evidence rather than one generic “restore failed” signal.

```bash
velero restore describe catalog-drill-20260426 --details
velero restore logs catalog-drill-20260426
k get all -n catalog-restore
k get pvc -n catalog-restore
k get events -n catalog-restore --sort-by=.lastTimestamp
```

**Solution step 3: diagnose an incomplete restore.**

Suppose the Restore completed with one warning and the Deployment is stuck because the PVC remains Pending. The next move is not to rerun the restore blindly. Inspect the PVC, StorageClass, and events to determine whether the target cluster can provision or bind the restored volume. If this is a migration or a new cluster, the original StorageClass may not exist.

```bash
k describe pvc -n catalog-restore
k get storageclass
k get volumesnapshotclasses
k get events -n catalog-restore --sort-by=.lastTimestamp
```

If the StorageClass is missing, the fix may be to create the equivalent StorageClass before restoring again, or to use restore item actions or migration planning to map storage behavior. If the snapshot is region-bound and the target cluster is in a different region, the correct fix may be cross-region snapshot copy or file-system backup, not another restore command. The point is to debug the dependency that Kubernetes reports.

**Solution step 4: validate the restored application, not just the objects.**

Once Pods are running and PVCs are bound, verify data and service behavior. A simple NGINX demo might only need an HTTP check. A catalog service should prove that expected product records and uploaded images exist. Use application-owned validation where possible because generic Kubernetes readiness may not catch logical data loss.

```bash
k rollout status deployment/catalog-api -n catalog-restore --timeout=180s
k port-forward -n catalog-restore svc/catalog-api 8080:80
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/products/sample-product
```

If validation passes, the team can decide whether to restore into the original namespace, promote the restored namespace, or use the findings to repair GitOps and storage dependencies first. That decision should be written in the incident log because restore actions often change the future debugging picture. Responders need to know which backup was used, what warnings occurred, what data checks passed, and what residual risk remains.

**Solution step 5: record evidence and clean up deliberately.**

A restore drill or incident restore should leave evidence. Capture the backup name, restore name, validation commands, warnings, elapsed time, and owner sign-off. If this was only a test namespace, remove it after evidence is saved so later drills do not confuse old restored objects with current ones.

```bash
velero restore describe catalog-drill-20260426 --details
k get all,pvc,secret,configmap -n catalog-restore
k delete namespace catalog-restore
```

This worked example shows the core Velero operating loop: inspect the backup, restore into a controlled boundary, debug Kubernetes dependencies, validate application behavior, then document the result. The hands-on exercise later asks you to apply the same loop to a small workload so the sequence becomes familiar before you need it during a real incident.

## 5. Operate Velero as a Reliability Service

Installing Velero is a project. Operating Velero is a reliability practice. The difference is cadence: backups must keep happening, restores must keep working, storage costs must stay visible, credentials must rotate, and application owners must trust the recovery evidence. A platform team that treats Velero as “set and forget” will eventually discover that a broken schedule, expired credential, full snapshot quota, or changed StorageClass invalidated the recovery plan.

Monitoring should cover both Velero internals and recovery outcomes. Pod readiness is necessary but shallow. Backup success counters, backup duration, last successful backup timestamp, storage location availability, restore failures, and node-agent health are stronger signals. The most important alert is often “no recent successful backup for this critical scope,” because it catches silent drift even when the Velero Deployment is still running.

```yaml
groups:
  - name: velero-reliability
    rules:
      - alert: VeleroBackupFailuresDetected
        expr: increase(velero_backup_failure_total[1h]) > 0
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: Velero backup failures were recorded during the last hour
          description: Inspect Velero backup logs, storage location health, and recent schedule activity.

      - alert: VeleroNoRecentSuccessfulBackup
        expr: time() - velero_backup_last_successful_timestamp > 90000
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: No recent successful Velero backup is visible
          description: A critical backup scope has not completed within the expected recovery window.
```

Metrics alone are not enough because they do not prove restore correctness. A mature team runs restore drills and treats the result as a production reliability artifact. The drill should restore a representative workload, run the same validation commands the real incident would require, and record elapsed time against the recovery time objective. A drill that only checks `velero restore get` is better than nothing, but it does not prove the application works.

Restore drills should be scoped carefully to avoid harming production. Use namespace mapping, isolated DNS names, disabled external traffic, and test credentials where possible. Watch for controllers that react to restored custom resources and create real cloud resources. A restored ExternalDNS record, Certificate, or Crossplane claim can have side effects unless the drill environment is fenced.

```ascii
+-------------------------+      +--------------------------+      +-------------------------+
| Scheduled backup exists |----->| Restore drill namespace  |----->| Application validation  |
| and reports Completed   |      | is created from backup   |      | proves useful recovery  |
+-------------------------+      +--------------------------+      +-------------------------+
            |                                  |                                  |
            v                                  v                                  v
+-------------------------+      +--------------------------+      +-------------------------+
| Storage location ready  |      | PVCs bind and Pods run   |      | Evidence is recorded    |
| and retention enforced  |      | without production DNS   |      | with RTO and warnings   |
+-------------------------+      +--------------------------+      +-------------------------+
```

Security operations matter because Velero has broad visibility into cluster resources. The server often needs permission to read many objects and coordinate volume backups. Backup storage may contain Secrets and sensitive topology. Restore permissions can recreate workloads and credentials. Least privilege, audit logging, bucket encryption, key rotation, and restricted restore authority are therefore part of the backup design, not optional hardening.

Cost control should be visible from the first production rollout. Object storage metadata is usually cheap, but frequent volume snapshots, copied file-system backups, and long retention windows can become expensive. Excluding noisy resources, scoping namespaces, tuning retention, cleaning decommissioned schedules, and reviewing snapshot lifecycle policies prevent backup growth from becoming a hidden platform tax. Cost controls should not be applied blindly during an incident, but they should be designed during normal operations.

Velero upgrades should be handled like other platform controller upgrades. Check the compatibility of the server, CLI, plugins, Kubernetes version, CSI drivers, and storage provider APIs. Run a backup and restore drill in a non-production cluster before upgrading production. Keep the previous restore procedure available until the new version has produced and restored a known-good backup.

Runbooks should describe decision points, not only commands. During an incident, responders need to know which backup to choose, when to restore into a test namespace, who approves production restore, how to handle GitOps reconciliation, how to validate data, and when to stop and escalate to database recovery. Commands without decisions create speed but not judgment.

A practical runbook entry for a critical namespace should include the backup Schedule name, expected frequency, retention, namespace mapping pattern, volume strategy, validation endpoint, data verification command, owner contact, and rollback plan. It should also name resources intentionally excluded from Velero and the system responsible for recreating them. That last field prevents confusion when someone notices that a DNS record, cloud database, or external secret did not return after restore.

The most senior habit is to make restore evidence reviewable. After each drill, record the backup name, restore name, warnings, elapsed time, validation output, and follow-up issues. If a restore takes longer than the recovery time objective, treat it as reliability debt. If a restore completes but application validation fails, treat the backup as incomplete. This posture turns Velero from a tool installation into a tested recovery capability.

## Did You Know?

1. **Velero began as Heptio Ark before being renamed after Heptio joined VMware.** The history matters because many older posts, manifests, and runbooks still use the Ark name or pre-node-agent terminology, so operators should verify commands against the version they actually run.

2. **Velero stores Kubernetes resource backups in object storage even when volume snapshots are handled by a separate storage system.** Losing access to the object bucket can make snapshot metadata difficult or impossible to use through normal Velero restore workflows.

3. **A Velero Schedule creates independent Backup objects with their own TTL values.** Removing a Schedule stops future backups, but existing backups remain until their TTL, lifecycle policy, or manual deletion removes them.

4. **A successful Kubernetes restore can still be an application failure.** Velero may recreate objects correctly while the workload fails because of external databases, cloud identities, DNS records, admission policies, or application-level data corruption.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Treating Velero as a replacement for database-native backup | Crash-consistent volume copies may not provide transaction-aware recovery or point-in-time restore | Pair Velero with database backup tools when the application requires logical consistency guarantees |
| Backing up whole clusters without restore boundaries | Restores become slow, risky, and likely to conflict with live platform services | Define application scopes with namespaces, labels, and explicit cluster prerequisites |
| Never restoring into an isolated namespace | The team discovers missing PVCs, StorageClasses, Secrets, or validation gaps during the real incident | Run scheduled restore drills with namespace mapping and application checks |
| Ignoring Backup warnings because status is Completed | Important resources or volumes may have been skipped while the top-level status still looks reassuring | Review `velero backup describe --details` and logs for critical scopes |
| Storing backups in the same failure domain as the cluster | A regional outage, account compromise, or bucket deletion can remove both production and recovery data | Use separate access boundaries, replication, lifecycle policy, and deletion protection where required |
| Restoring Secrets without a credential plan | Old credentials may reappear, or missing Secrets may block Pods after a restore | Decide which Secrets Velero owns, which are external, and how rotations affect restores |
| Forgetting GitOps during restore | GitOps controllers may immediately revert restored resources or recreate broken desired state | Pause, coordinate, or intentionally reconcile GitOps as part of the runbook |
| Measuring only backup success, not restore success | The organization has evidence that backups run, but no evidence that services can recover | Track restore drill success, elapsed time, warnings, and application validation output |

## Quiz

### Question 1

Your team runs GitOps for every Deployment and Service, and a developer argues that Velero is unnecessary because the repository can recreate the cluster. The `orders` namespace also contains a PostgreSQL StatefulSet with a PVC. What backup design do you recommend, and how do you justify it?

<details>
<summary>Show answer</summary>

Use GitOps for the desired Kubernetes configuration, Velero for the application-shaped Kubernetes resource graph and selected PVC metadata or volume protection, and a database-native PostgreSQL backup strategy for transaction-aware data recovery. GitOps can recreate manifests, but it cannot recreate mutable database contents. Velero can help restore Kubernetes objects and possibly volume data, but it does not automatically provide point-in-time database semantics. A strong design states which system owns each recovery layer and defines validation that proves `orders` can read expected data after restore.
</details>

### Question 2

A Velero Backup for `payments` reports `Completed` with two warnings. The platform team wants to mark the backup as healthy because the status is not `Failed`. During a production readiness review, what should you check before accepting that backup as a recovery point?

<details>
<summary>Show answer</summary>

Inspect `velero backup describe payments-backup --details` and `velero backup logs payments-backup` to identify the warnings. Confirm that included namespaces, excluded resources, volume handling, storage location, and snapshot or file-system backup results match the recovery plan. Then verify that the backup can be restored into an isolated namespace and that application checks pass. A Completed status with warnings may still omit important resources or volumes, so acceptance requires evidence beyond the top-level phase.
</details>

### Question 3

A restore drill maps `catalog` to `catalog-restore`, and the Restore finishes successfully. The Deployment stays unavailable because the PVC is Pending, and events say the original StorageClass does not exist. What is the next debugging move, and what does this reveal about the backup plan?

<details>
<summary>Show answer</summary>

Inspect the PVC, StorageClass list, VolumeSnapshotClass list, and restore logs to confirm the missing storage dependency. The next fix may be to create an equivalent StorageClass before restore, adjust migration planning, or use a different volume backup approach if the original snapshot cannot be restored in the target environment. This reveals that the backup captured application objects, but the restore environment did not satisfy a cluster-level prerequisite. A complete backup plan must name those prerequisites explicitly.
</details>

### Question 4

A team enables file-system backup by default for all volumes because it works across storage providers. After a month, backups for a media-processing namespace take many hours and sometimes overlap with the next scheduled run. How should the team evaluate a better design?

<details>
<summary>Show answer</summary>

Compare file-system backup against CSI snapshots, application-native backup, and selective volume inclusion for that namespace. File-system backup is portable, but it can be slow for large volumes or many files. The team should measure backup duration, restore duration, data consistency requirements, storage cost, and whether all files actually need the same retention. A better design may use storage snapshots for large volumes, application-native backup for critical data, and Velero filters to avoid unnecessary data.
</details>

### Question 5

During an incident, someone proposes restoring the latest whole-cluster backup directly into the production cluster to recover one deleted namespace. What risks should you raise, and what safer restore pattern would you use first?

<details>
<summary>Show answer</summary>

A whole-cluster restore can overwrite or conflict with live resources, cluster-scoped policy, controllers, Secrets, and platform services that were not part of the incident. It may also reintroduce old configuration unrelated to the deleted namespace. A safer pattern is to inspect the backup, restore the affected namespace into an isolated namespace with namespace mapping, validate workloads and data, then decide whether to restore into the original namespace or promote the recovered resources through a controlled process.
</details>

### Question 6

Your backup Schedule runs daily at 02:00 with a seven-day TTL. On Wednesday afternoon, an application owner reports that a bad migration corrupted data on Monday morning, but nobody noticed until now. How do you reason about whether Velero can help?

<details>
<summary>Show answer</summary>

First identify whether any backup predates the corruption and whether the volume or database state in that backup is application-consistent. The seven-day TTL means older backups may still exist, but daily frequency means the recovery point may lose writes between the backup and corruption. If the database requires point-in-time recovery, Velero snapshots alone may not be enough. Velero may restore Kubernetes objects and possibly an older volume, but the final decision depends on data correctness, business-approved data loss, and database-native recovery options.
</details>

### Question 7

A restore drill succeeds in Kubernetes, but the restored application immediately creates real DNS records and connects to production third-party services from the test namespace. What did the drill design miss, and how should future drills change?

<details>
<summary>Show answer</summary>

The drill missed side effects from controllers, Ingress configuration, external DNS, credentials, and application environment settings. Future drills should fence the restore namespace by disabling or changing external routing, using test credentials, excluding or patching resources that create external effects, and validating in an isolated environment. The runbook should explicitly list resources that are safe to restore as-is and resources that need transformation or exclusion during drills.
</details>

## Hands-On Exercise

### Objective

Set up Velero with an in-cluster MinIO object store, back up a small namespace, simulate a namespace deletion, restore into a validation namespace, and create a scheduled backup. The exercise mirrors the worked example, but uses a small workload so you can focus on the recovery sequence rather than cloud account setup.

### Step 1: prepare the shell and confirm the cluster

Run these commands from a shell that has access to your lab cluster. The examples use `k` as a `kubectl` alias after defining it. If your cluster already has Velero installed, use a disposable cluster or change names to avoid touching shared backup resources.

```bash
alias k=kubectl
k version
velero version --client-only
k get nodes
```

### Step 2: deploy MinIO for Velero object storage

This lab uses Velero’s MinIO example so the backup target runs inside the cluster. That is convenient for learning, but it is not a production design because losing the cluster can also lose the backup store. Production backup storage should live outside the failure domain of the cluster.

```bash
k apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/main/examples/minio/00-minio-deployment.yaml
k rollout status deployment/minio -n velero --timeout=180s
```

Create a credentials file for the MinIO example. The values match the example deployment. Keep this file out of source control because real Velero credentials are sensitive.

```bash
cat > credentials-minio <<'EOF'
[default]
aws_access_key_id = minio
aws_secret_access_key = minio123
EOF
```

### Step 3: install Velero against MinIO

Install Velero with the AWS plugin because MinIO speaks an S3-compatible API. This lab disables volume snapshots because the sample workload is resource-focused. Production installations should make an explicit volume decision rather than copying this lab setting.

```bash
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.13.0 \
  --bucket velero \
  --secret-file ./credentials-minio \
  --use-volume-snapshots=false \
  --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio.velero.svc:9000 \
  --wait
```

Verify that the server is running and that the backup location is available. Do not continue if the BackupStorageLocation is unavailable, because later backup failures would only repeat the same storage problem.

```bash
k get pods -n velero
velero backup-location get
k get backupstoragelocations -n velero
```

### Step 4: deploy a sample application namespace

Create a namespace with a Deployment, Service, ConfigMap, and Secret. This gives Velero several resource types to restore and lets you verify that both ordinary configuration and sensitive configuration return after the namespace deletion.

```bash
k create namespace demo-velero

k -n demo-velero create configmap app-config \
  --from-literal=message="restored by velero"

k -n demo-velero create secret generic app-secret \
  --from-literal=token="demo-token"

k -n demo-velero create deployment web \
  --image=nginx:1.27 \
  --replicas=2

k -n demo-velero expose deployment web \
  --port=80 \
  --target-port=80

k rollout status deployment/web -n demo-velero --timeout=180s
k get all,configmap,secret -n demo-velero
```

### Step 5: create and inspect a manual backup

Create a namespace-scoped backup and exclude event resources. The backup is intentionally narrow so the restore exercise is easy to reason about. After creating it, inspect details and logs before simulating failure.

```bash
velero backup create demo-velero-backup \
  --include-namespaces demo-velero \
  --exclude-resources events,events.events.k8s.io \
  --ttl 24h

velero backup describe demo-velero-backup --details
velero backup logs demo-velero-backup
velero backup get
```

### Step 6: simulate a namespace deletion

Delete the namespace to create a controlled failure. Wait until the namespace disappears before restoring, because restoring into a terminating namespace can create confusing results. In a real incident, you would pause or coordinate GitOps before deleting or restoring resources.

```bash
k delete namespace demo-velero
k get namespace demo-velero
```

### Step 7: restore into a validation namespace first

Restore the deleted namespace into `demo-velero-restore` instead of the original namespace. This mirrors the safer incident pattern from the worked example. You can inspect the restored workload without pretending that Kubernetes object creation alone proves production recovery.

```bash
velero restore create demo-velero-restore-test \
  --from-backup demo-velero-backup \
  --namespace-mappings demo-velero:demo-velero-restore

velero restore describe demo-velero-restore-test --details
velero restore logs demo-velero-restore-test
k get all,configmap,secret -n demo-velero-restore
k rollout status deployment/web -n demo-velero-restore --timeout=180s
```

### Step 8: validate service behavior

Port-forward the restored Service and check that NGINX answers. This is a simple application check, not a deep data check, but it demonstrates the habit of validating service behavior after Velero status looks healthy.

```bash
k port-forward -n demo-velero-restore svc/web 8080:80
curl -fsS http://127.0.0.1:8080/ > /tmp/demo-velero-nginx.html
test -s /tmp/demo-velero-nginx.html
```

In another terminal, inspect the restored ConfigMap and Secret. Do not print real production secrets during real operations; this lab uses a harmless value so you can confirm the restore behavior.

```bash
k -n demo-velero-restore get configmap app-config -o yaml
k -n demo-velero-restore get secret app-secret -o jsonpath='{.data.token}' | base64 --decode
printf '\n'
```

### Step 9: create a scheduled backup

Recreate the original namespace so the schedule has something to back up, then create a short-retention schedule. In production, the schedule frequency and TTL should come from the recovery objective and retention policy rather than from a copied command.

```bash
k create namespace demo-velero

k -n demo-velero create deployment web \
  --image=nginx:1.27 \
  --replicas=1

k -n demo-velero expose deployment web \
  --port=80 \
  --target-port=80

velero schedule create demo-velero-hourly \
  --schedule="0 * * * *" \
  --include-namespaces demo-velero \
  --exclude-resources events,events.events.k8s.io \
  --ttl 24h

velero schedule get
velero schedule describe demo-velero-hourly
```

### Step 10: clean up lab resources when finished

Cleanup prevents old lab restores from confusing future exercises. Do not run these commands in a shared environment unless you created these exact resources and understand that the Velero uninstall removes Velero components from the cluster.

```bash
k delete namespace demo-velero --ignore-not-found
k delete namespace demo-velero-restore --ignore-not-found
velero schedule delete demo-velero-hourly --confirm
velero backup delete demo-velero-backup --confirm
velero uninstall --confirm
rm -f credentials-minio /tmp/demo-velero-nginx.html
```

### Success Criteria

- [ ] You verified that Velero CLI and `kubectl` can talk to the lab cluster before installing anything.
- [ ] You deployed MinIO and installed Velero with an available BackupStorageLocation.
- [ ] You created a namespace containing a Deployment, Service, ConfigMap, and Secret.
- [ ] You created a namespace-scoped Velero Backup and inspected its details and logs.
- [ ] You deleted the namespace to simulate a controlled failure.
- [ ] You restored into a different validation namespace using namespace mapping.
- [ ] You verified restored Kubernetes resources, Deployment rollout, and HTTP service behavior.
- [ ] You created and inspected a Velero Schedule with an explicit TTL.
- [ ] You can explain why this lab uses in-cluster MinIO only for learning and not for production disaster recovery.

### Bonus Challenge

Add a PVC-backed workload to the namespace and repeat the exercise using a volume backup strategy appropriate for your lab cluster. If your cluster supports CSI snapshots, compare snapshot behavior with file-system backup through the node agent. Record backup duration, restore duration, PVC binding behavior, and the exact validation command that proves the restored data is present.

## Next Module

Continue to [Platforms Toolkit](/platform/toolkits/infrastructure-networking/platforms/) to learn how platform components such as Backstage, Crossplane, and cert-manager fit into internal developer platforms.

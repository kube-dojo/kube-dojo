---
title: "Module 6.3: Velero"
slug: platform/toolkits/developer-experience/scaling-reliability/module-6.3-velero
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[MEDIUM]` | Time: 40-45 minutes

## Overview

Backups are like insurance—you hope you never need them, but you'll be glad you have them when disaster strikes. Velero provides backup and disaster recovery for Kubernetes clusters, including resources, persistent volumes, and the ability to migrate workloads between clusters.

**What You'll Learn**:
- Velero architecture and backup strategies
- Scheduled backups and retention policies
- Disaster recovery procedures
- Cluster migration patterns

**Prerequisites**:
- Kubernetes resources and persistent volumes
- [SRE Discipline](../../../disciplines/core-platform/sre/) — Disaster recovery concepts
- Cloud storage basics (S3, GCS, Azure Blob)

---

## Why This Module Matters

"We'll restore from etcd backup" sounds good until you realize you also need the PVs, the Secrets, and the correct order of restoration. Velero provides application-aware backups—not just etcd snapshots. It backs up what you need to actually restore a working application.

> 💡 **Did You Know?** Velero was originally called "Heptio Ark" and was created by Heptio (founded by Kubernetes creators Joe Beda and Craig McLuckie). After VMware acquired Heptio, it was renamed to Velero (Latin for "sail fast"). It's now a CNCF sandbox project used by thousands of organizations for Kubernetes disaster recovery.

---

## Backup Strategies

```
KUBERNETES BACKUP APPROACHES
════════════════════════════════════════════════════════════════════

1. ETCD BACKUP (infrastructure level)
─────────────────────────────────────────────────────────────────
• Backs up cluster state database
• All resources, all namespaces
• Doesn't include PV data
• Requires cluster access to restore
• Good for: cluster-level disaster recovery

2. VELERO (application level)
─────────────────────────────────────────────────────────────────
• Backs up selected resources
• Includes PV snapshots
• Namespace-aware
• Can restore to different cluster
• Good for: application DR, migration, namespace backup

3. GITOPS (configuration level)
─────────────────────────────────────────────────────────────────
• Git is the source of truth
• Manifests stored in version control
• Doesn't include runtime state
• Doesn't include PV data
• Good for: configuration recovery, multi-cluster sync

RECOMMENDED: Use ALL THREE
─────────────────────────────────────────────────────────────────
• etcd backup: cluster-level recovery
• Velero: application + data recovery
• GitOps: configuration source of truth
```

---

## Architecture

```
VELERO ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    VELERO SERVER                            │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │  Backup     │  │  Restore    │  │  Schedule   │        │ │
│  │  │  Controller │  │  Controller │  │  Controller │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │              BackupStorageLocation                   │  │ │
│  │  │              VolumeSnapshotLocation                  │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD STORAGE                                 │
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │    Object Storage   │    │   Volume Snapshots  │            │
│  │    (S3, GCS, etc)   │    │   (EBS, GCE PD)     │            │
│  │                     │    │                     │            │
│  │  • Backup metadata  │    │  • PV data copies   │            │
│  │  • Resource YAMLs   │    │  • Point-in-time    │            │
│  │  • Tarball of data  │    │                     │            │
│  └─────────────────────┘    └─────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### What Gets Backed Up

| Component | Default | Configurable |
|-----------|---------|--------------|
| **Resources** | All namespaced resources | Include/exclude by type, label |
| **Cluster resources** | Excluded | Can include (RBAC, CRDs) |
| **Persistent Volumes** | Excluded | Enable with snapshots or Restic/Kopia |
| **Secrets** | Included | Can exclude |
| **ConfigMaps** | Included | Can exclude |

---

## Installation

```bash
# Install Velero CLI
brew install velero  # macOS
# or download from https://velero.io/docs/main/basic-install/

# Install Velero with AWS provider
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups \
  --backup-location-config region=us-west-2 \
  --snapshot-location-config region=us-west-2 \
  --secret-file ./credentials-velero

# Verify installation
velero version
kubectl get pods -n velero
```

### Credentials File (AWS)

```ini
# credentials-velero
[default]
aws_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
```

---

## Backup Operations

### Manual Backup

```bash
# Backup entire cluster
velero backup create full-backup

# Backup specific namespace
velero backup create app-backup --include-namespaces production

# Backup with volume snapshots
velero backup create full-backup --snapshot-volumes

# Backup by label selector
velero backup create app-backup --selector app=myapp

# Backup excluding resources
velero backup create backup --exclude-resources secrets,configmaps

# Check backup status
velero backup describe full-backup
velero backup logs full-backup
```

### Backup Spec (Declarative)

```yaml
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: production-backup
  namespace: velero
spec:
  includedNamespaces:
  - production
  - staging
  excludedResources:
  - events
  - events.events.k8s.io
  snapshotVolumes: true
  storageLocation: default
  volumeSnapshotLocations:
  - default
  ttl: 720h  # 30 days retention
  hooks:
    resources:
    - name: backup-hook
      includedNamespaces:
      - production
      labelSelector:
        matchLabels:
          app: database
      pre:
      - exec:
          container: postgres
          command:
          - /bin/bash
          - -c
          - pg_dump -U postgres > /backup/dump.sql
```

> 💡 **Did You Know?** Velero's backup hooks let you run commands before and after backups. This is crucial for databases—you can flush writes, create consistent snapshots, or dump data to ensure backup consistency. Without hooks, you might backup a database mid-transaction and get corrupted data.

---

## Scheduled Backups

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  template:
    includedNamespaces:
    - production
    snapshotVolumes: true
    ttl: 168h  # 7 day retention
---
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: weekly-backup
  namespace: velero
spec:
  schedule: "0 3 * * 0"  # 3 AM Sundays
  template:
    includedNamespaces:
    - "*"  # All namespaces
    snapshotVolumes: true
    ttl: 720h  # 30 day retention
```

```bash
# Create schedule via CLI
velero schedule create daily-prod \
  --schedule="0 2 * * *" \
  --include-namespaces production \
  --snapshot-volumes \
  --ttl 168h

# List schedules
velero schedule get

# Check scheduled backup history
velero backup get | grep daily-prod
```

---

## Restore Operations

### Basic Restore

```bash
# List available backups
velero backup get

# Restore entire backup
velero restore create --from-backup full-backup

# Restore to different namespace
velero restore create --from-backup app-backup \
  --namespace-mappings production:production-restored

# Restore specific resources only
velero restore create --from-backup full-backup \
  --include-resources deployments,services

# Restore excluding volumes (resources only)
velero restore create --from-backup full-backup \
  --restore-volumes=false

# Check restore status
velero restore describe <restore-name>
velero restore logs <restore-name>
```

### Disaster Recovery Procedure

```
DISASTER RECOVERY STEPS
════════════════════════════════════════════════════════════════════

1. ASSESS THE DAMAGE
─────────────────────────────────────────────────────────────────
$ kubectl get nodes
$ kubectl get pods -A
# Determine what needs recovery

2. VERIFY BACKUP AVAILABILITY
─────────────────────────────────────────────────────────────────
$ velero backup get
# Find most recent successful backup

3. IF CLUSTER IS GONE: Create new cluster
─────────────────────────────────────────────────────────────────
# Re-install Velero pointing to same backup location
$ velero install --provider aws --bucket velero-backups ...

4. RESTORE
─────────────────────────────────────────────────────────────────
$ velero restore create disaster-recovery \
    --from-backup <latest-backup>

5. VERIFY RESTORATION
─────────────────────────────────────────────────────────────────
$ kubectl get pods -A
$ kubectl get pvc -A
# Test applications
```

---

## Volume Backup Options

### CSI Snapshots (Native)

```yaml
# BackupStorageLocation with CSI snapshots
apiVersion: velero.io/v1
kind: VolumeSnapshotLocation
metadata:
  name: aws-default
  namespace: velero
spec:
  provider: aws
  config:
    region: us-west-2
```

### File-Level Backup (Kopia/Restic)

For volumes without snapshot support:

```bash
# Install with file system backup enabled
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups \
  --use-node-agent \  # Enables file-level backup
  --default-volumes-to-fs-backup
```

```yaml
# Enable for specific PVCs with annotation
apiVersion: v1
kind: Pod
metadata:
  annotations:
    backup.velero.io/backup-volumes: data-volume
spec:
  volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: my-pvc
```

---

## Cluster Migration

```
CLUSTER MIGRATION WITH VELERO
════════════════════════════════════════════════════════════════════

SOURCE CLUSTER                           TARGET CLUSTER
─────────────────                        ─────────────────

1. Install Velero                        1. Install Velero
   (pointing to S3)                         (same S3 bucket!)

2. Create backup                         2. Wait for backup
   $ velero backup create                   to sync
     migration-backup                      $ velero backup get

3. Backup completes                      3. Restore
   → Stored in S3                           $ velero restore create
                                              --from-backup
                                              migration-backup

Result: Application running on new cluster with data!
```

### Migration Best Practices

```bash
# 1. Backup source cluster
velero backup create migration-backup \
  --include-namespaces app-namespace \
  --snapshot-volumes

# 2. Wait for backup to complete
velero backup wait migration-backup

# 3. On target cluster, verify backup is visible
velero backup get

# 4. Restore (with any needed transformations)
velero restore create migration-restore \
  --from-backup migration-backup \
  --namespace-mappings old-ns:new-ns

# 5. Verify and test
kubectl get pods -n new-ns
```

---

## Backup Retention and Lifecycle

```yaml
# Different retention for different backup types
---
# Daily backups - keep 7 days
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily
spec:
  schedule: "0 2 * * *"
  template:
    ttl: 168h  # 7 days
---
# Weekly backups - keep 4 weeks
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: weekly
spec:
  schedule: "0 3 * * 0"
  template:
    ttl: 672h  # 28 days
---
# Monthly backups - keep 1 year
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: monthly
spec:
  schedule: "0 4 1 * *"
  template:
    ttl: 8760h  # 365 days
```

> 💡 **Did You Know?** Velero's TTL (Time To Live) is set at backup creation time, not schedule time. This means even if you delete a Schedule, the backups it created will remain until their individual TTL expires. Plan your retention carefully—old backups can accumulate significant storage costs.

> 💡 **Did You Know?** Velero's resource filtering is more powerful than most realize. You can backup by namespace, by label selector, by resource type, or any combination. Teams use this for "logical backups"—backing up just a single application (all resources with `app=payment`) rather than entire namespaces. This makes restores faster and reduces storage costs by excluding unrelated resources.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No PV snapshots | Data lost on restore | Use `--snapshot-volumes` or file-level backup |
| Not testing restores | Discover issues during disaster | Regular restore drills (monthly) |
| Single backup location | Backup lost with region | Cross-region replication |
| No backup hooks | Database corruption | Use pre/post hooks for consistency |
| Backing up too much | Slow backups, high costs | Use include/exclude filters |
| TTL too short | Can't recover from old corruption | Keep long-term backups (monthly/yearly) |

---

## War Story: The Backup That Wasn't

*A team had Velero running for 6 months. Their cluster crashed. They tried to restore. Nothing happened.*

**What went wrong**:
1. Velero server had crashed 3 months ago (OOM)
2. No monitoring on Velero pods
3. No alerts on backup failures
4. They assumed backups were happening

**The fix**:
```yaml
# Alert on backup failures
- alert: VeleroBackupFailure
  expr: velero_backup_failure_total > 0
  for: 1h
  labels:
    severity: critical
  annotations:
    summary: "Velero backup failed"

# Alert on no recent backups
- alert: VeleroNoRecentBackup
  expr: time() - velero_backup_last_successful_timestamp > 86400
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "No successful backup in 24 hours"
```

**Lesson**: Monitor your backups. Test your restores. Backups you can't restore from aren't backups.

---

## Quiz

### Question 1
What's the difference between Velero backup and etcd backup?

<details>
<summary>Show Answer</summary>

**etcd backup**:
- Backs up entire cluster state database
- All resources, all namespaces
- Doesn't include PV data
- Must restore to same cluster (or identical)
- Infrastructure-level backup

**Velero backup**:
- Backs up selected resources (configurable)
- Can include PV data (snapshots or file-level)
- Can restore to different cluster
- Application-level backup
- Supports hooks for application consistency

Use both: etcd for cluster-level DR, Velero for application-level.

</details>

### Question 2
How do you backup persistent volume data with Velero?

<details>
<summary>Show Answer</summary>

Two methods:

**1. CSI Snapshots (native)**:
```bash
velero backup create --snapshot-volumes
```
- Uses cloud provider's snapshot API
- Fast, point-in-time
- Requires CSI snapshot support

**2. File-level backup (Kopia/Restic)**:
```bash
velero install --use-node-agent --default-volumes-to-fs-backup
```
- Copies files from PV to object storage
- Works with any storage
- Slower but more compatible

Choose based on your storage provider's capabilities.

</details>

### Question 3
Why should you test restore regularly?

<details>
<summary>Show Answer</summary>

**Reasons to test restores**:
1. Verify backups are actually complete
2. Validate restore procedure works
3. Measure restore time (RTO)
4. Find issues before real disaster
5. Train team on recovery procedures

**What can go wrong**:
- Backup corrupted
- Missing volumes
- Wrong permissions
- Changed dependencies
- Network/storage issues

**Recommendation**: Monthly restore drill to test environment. Document findings.

</details>

---

## Hands-On Exercise

### Objective
Set up Velero, create backups, and perform a restore.

### Environment Setup

```bash
# For local testing, use Velero with MinIO
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/main/examples/minio/00-minio-deployment.yaml

# Install Velero with MinIO backend
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero \
  --secret-file ./credentials-minio \
  --use-volume-snapshots=false \
  --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio.velero.svc:9000

# credentials-minio:
# [default]
# aws_access_key_id = minio
# aws_secret_access_key = minio123
```

### Tasks

1. **Deploy sample app**:
   ```bash
   kubectl create namespace demo
   kubectl -n demo run nginx --image=nginx
   kubectl -n demo expose pod nginx --port=80
   kubectl -n demo create configmap app-config --from-literal=key=value
   ```

2. **Create backup**:
   ```bash
   velero backup create demo-backup --include-namespaces demo
   velero backup describe demo-backup
   ```

3. **Simulate disaster** (delete namespace):
   ```bash
   kubectl delete namespace demo
   kubectl get namespace demo  # Should be gone
   ```

4. **Restore from backup**:
   ```bash
   velero restore create --from-backup demo-backup
   velero restore describe <restore-name>
   ```

5. **Verify restoration**:
   ```bash
   kubectl get pods -n demo
   kubectl get svc -n demo
   kubectl get configmap -n demo
   ```

6. **Create scheduled backup**:
   ```bash
   velero schedule create demo-daily \
     --schedule="0 * * * *" \
     --include-namespaces demo \
     --ttl 24h
   ```

### Success Criteria
- [ ] Velero installed and running
- [ ] Backup created successfully
- [ ] Namespace deleted (simulated disaster)
- [ ] Restore completed
- [ ] All resources recovered (pods, services, configmaps)
- [ ] Schedule created

### Bonus Challenge
Set up backup hooks to run a command before backing up (simulating database dump).

---

## Further Reading

- [Velero Documentation](https://velero.io/docs/)
- [Velero Plugin for AWS](https://github.com/vmware-tanzu/velero-plugin-for-aws)
- [Disaster Recovery Best Practices](https://velero.io/docs/main/disaster-case/)

---

## Next Module

Continue to [Platforms Toolkit](../../infrastructure-networking/platforms/) to learn about Backstage, Crossplane, and cert-manager for internal developer platforms.

---

*"Hope is not a strategy. Backups are. Test them."*

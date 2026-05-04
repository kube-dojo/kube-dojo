---
title: "Module 1.4: Stateful Chaos \u2014 Databases & Storage"
slug: platform/disciplines/reliability-security/chaos-engineering/module-1.4-stateful-chaos
sidebar:
  order: 5
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 3 hours

## Prerequisites

Before starting this module:
- **Required**: [Module 1.2: Chaos Mesh Fundamentals](../module-1.2-chaos-mesh/) — PodChaos, NetworkChaos, StressChaos
- **Required**: [Kubernetes Basics — StatefulSets](/prerequisites/kubernetes-basics/) — PVs, PVCs, StatefulSets, headless Services
- **Recommended**: Basic PostgreSQL or MySQL administration experience
- **Recommended**: Understanding of database replication concepts (primary/replica, WAL shipping)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design chaos experiments for stateful workloads — databases, queues, caches — with proper data safety controls**
- **Implement storage-level fault injection that tests volume failures, I/O errors, and disk pressure**
- **Evaluate data consistency guarantees under chaos conditions for stateful Kubernetes workloads**
- **Build recovery validation experiments that verify backup, restore, and failover procedures actually work**

## Why This Module Matters

In 2017, GitLab lost 6 hours of production data after all five of their backup and recovery mechanisms failed simultaneously — a canonical lesson that untested backups are not backups and untested failover is not failover. <!-- incident-xref: gitlab-2017-db1 --> For the full case study, see [What Is a Terminal](../../../../prerequisites/zero-to-terminal/module-0.2-what-is-a-terminal/).

Stateless services are straightforward to test with chaos — kill a pod, it restarts, traffic reroutes, life goes on. Stateful systems are fundamentally different. When you kill a database pod, you don't just lose compute — you potentially lose data, corrupt indexes, break replication chains, and violate consistency guarantees. The blast radius of stateful chaos is inherently larger and the consequences more severe.

This module teaches you to safely inject chaos into stateful workloads: databases, caches, message queues, and persistent storage. You'll learn to test failover mechanisms, verify backup integrity, and discover the hidden assumptions in your data layer — all without losing a single byte of production data.

---

## Did You Know?

> **Split-brain incidents** (where two database nodes both believe they are the primary and accept writes) have caused data corruption at companies including LinkedIn, GitHub, <!-- incident-xref: github-2018-split-brain --> and multiple financial institutions. The Redis Sentinel documentation explicitly warns about split-brain during network partitions. Yet fewer than 15% of organizations regularly test their database clusters for split-brain resilience, according to a 2023 Percona survey. For the GitHub October 2018 split-brain case study, see [Advanced Merging](../../../../prerequisites/git-deep-dive/module-2-advanced-merging/).

> **IO latency of just 50ms on a database volume** can cause a 40x increase in query execution time for workloads with heavy random reads. This is because database engines like PostgreSQL and InnoDB use buffer pools that assume sub-millisecond storage access. When that assumption breaks, every page fault becomes 50ms instead of 0.1ms, and queries that normally read 200 pages go from 20ms to 10 seconds. IOChaos at even modest levels reveals whether your application handles slow storage gracefully.

> **The MTTR (Mean Time to Recovery) for database failover** varies wildly across technologies: PostgreSQL with Patroni typically fails over in 10-30 seconds, MySQL with Group Replication in 5-15 seconds, Redis Sentinel in 15-45 seconds, and MongoDB replica sets in 10-30 seconds. But these are vendor-claimed numbers. Real-world MTTR depends on network conditions, replication lag, client reconnection logic, and connection pool behavior — all of which can only be verified through chaos testing.

> **Amazon Aurora's storage layer** was designed specifically to tolerate the loss of an entire Availability Zone plus one additional node without data loss. AWS validated this through continuous chaos testing — they literally kill storage nodes in production regularly. This level of confidence in storage resilience is only possible because they test it constantly, not because they believe their architecture diagrams.

---

## IOChaos: Storage-Level Fault Injection

IOChaos intercepts filesystem operations inside target containers and injects delays, errors, or attribute modifications. This simulates degraded storage, failing disks, and IO controller issues.

### How IOChaos Works

```
Normal IO path:
  Application → write() syscall → Filesystem → Block device → Disk

IOChaos path:
  Application → write() syscall → FUSE (Chaos Mesh) → delay/error → Filesystem → Disk
                                   ↑
                              Chaos Mesh injects
                              faults here
```

Chaos Mesh uses a FUSE (Filesystem in Userspace) layer to intercept and manipulate IO operations. This means:
- The application sees real filesystem errors/delays
- The actual data on disk is never corrupted
- The fault is completely reversible by removing the CRD

### IO Read/Write Delay

**Hypothesis**: "We believe the API will continue responding within 2 seconds even when disk read latency increases to 100ms per operation, because frequently accessed data is cached in PostgreSQL's shared buffers and only cold queries hit disk."

```yaml
# io-delay-experiment.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: postgres-io-delay
  namespace: database
spec:
  action: latency
  mode: one
  selector:
    namespaces:
      - database
    labelSelectors:
      app: postgresql
      role: primary
  volumePath: /var/lib/postgresql/data    # Target the data volume
  path: "**"                               # All files in the volume
  delay: "100ms"                           # 100ms IO delay
  percent: 100                             # Affect 100% of operations
  containerNames:
    - postgresql
  duration: "180s"
```

```bash
# Apply IO delay
kubectl apply -f io-delay-experiment.yaml

# Monitor query performance from the application
kubectl exec -it deployment/api-server -n app -- \
  sh -c 'for i in $(seq 1 10); do
    START=$(date +%s%N)
    curl -s http://localhost:8080/api/products/1 > /dev/null
    END=$(date +%s%N)
    echo "Query $i: $(( (END - START) / 1000000 ))ms"
    sleep 1
  done'

# Check PostgreSQL's internal IO statistics
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "SELECT * FROM pg_stat_io WHERE backend_type = 'client backend';"

# Clean up
kubectl delete iochaos postgres-io-delay -n database
```

### IO Error Injection

Simulate disk errors — files that can't be read or written:

```yaml
# io-error-experiment.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: postgres-io-errors
  namespace: database
spec:
  action: fault
  mode: one
  selector:
    namespaces:
      - database
    labelSelectors:
      app: postgresql
      role: primary
  volumePath: /var/lib/postgresql/data
  path: "/var/lib/postgresql/data/pg_wal/**"   # Target WAL files only
  errno: 5                                      # EIO (Input/Output error)
  percent: 25                                   # 25% of WAL operations fail
  methods:
    - write
    - fsync                                     # Target write and fsync only
  containerNames:
    - postgresql
  duration: "60s"
```

**Warning**: IO errors on WAL (Write-Ahead Log) files can cause PostgreSQL to shut down to protect data integrity. This is expected behavior — PostgreSQL is designed to crash-safe rather than continue with potentially corrupted data. The real test is whether your failover mechanism detects the crash and promotes a replica.

### Selective IO Chaos

Target specific file patterns to test specific behaviors:

| File Pattern | What It Tests |
|-------------|---------------|
| `**/pg_wal/**` | WAL write failures — replication and crash recovery |
| `**/base/**` | Table data access — query performance under IO stress |
| `**/pg_stat_tmp/**` | Statistics collector — monitoring degradation |
| `**/pg_tblspc/**` | Tablespace access — if using custom tablespaces |
| `**/*.idx` | Index file access — query plan changes under IO stress |

---

## Database Failover Testing

### PostgreSQL with Patroni

Patroni is the most common PostgreSQL high-availability solution in Kubernetes. It uses a distributed consensus store (etcd, ZooKeeper, or Kubernetes API) to manage leader election and automated failover.

```
                    ┌─────────────┐
                    │   Patroni   │
                    │   Leader    │
                    │  Election   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼────┐
        │ PG Primary│ │PG Repl │ │PG Repl  │
        │ (pod-0)   │ │(pod-1) │ │(pod-2)  │
        │ read/write│ │readonly│ │readonly │
        └───────────┘ └────────┘ └─────────┘
```

**Failover test using PodChaos:**

```yaml
# patroni-failover-test.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: patroni-primary-kill
  namespace: database
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - database
    labelSelectors:
      app: postgresql
      role: master              # Target the current primary
  gracePeriod: 0                # Immediate kill
  duration: "120s"
```

**What to observe during Patroni failover:**

```bash
# Terminal 1: Watch Patroni cluster state
kubectl exec -it postgresql-0 -n database -- \
  patronictl list

# Terminal 2: Monitor application connectivity
kubectl exec -it deployment/api-server -n app -- \
  sh -c 'while true; do
    RESULT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080/api/health)
    echo "$(date +%H:%M:%S) Health: $RESULT"
    sleep 1
  done'

# Terminal 3: Check for write availability
kubectl exec -it deployment/api-server -n app -- \
  sh -c 'while true; do
    RESULT=$(curl -s -w "\n%{http_code}" --max-time 5 \
      -X POST http://localhost:8080/api/test-write \
      -H "Content-Type: application/json" \
      -d "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}")
    echo "$(date +%H:%M:%S) Write: $RESULT"
    sleep 2
  done'
```

**Expected Patroni failover timeline:**

| Time | Event |
|------|-------|
| T+0s | Primary pod killed |
| T+1-3s | Patroni detects leader loss via DCS (distributed config store) |
| T+5-10s | Leader election begins; replicas check replication lag |
| T+10-20s | New primary promoted; Patroni updates endpoint |
| T+15-30s | Applications reconnect to new primary |
| T+20-45s | Old primary pod restarted by Kubernetes as replica |

**Key metrics to record:**
- Time from kill to new primary promotion
- Number of failed writes during failover
- Number of failed reads during failover (should be zero if read replicas are used)
- Time for the application to reconnect
- Whether any writes were lost (check sequence gaps)

### Redis Sentinel Failover

```yaml
# redis-sentinel-failover.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: redis-primary-kill
  namespace: cache
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - cache
    labelSelectors:
      app: redis
      role: master
  gracePeriod: 0
  duration: "60s"
```

**Redis Sentinel failover verification:**

```bash
# Check Sentinel's view of the cluster
kubectl exec -it redis-sentinel-0 -n cache -- \
  redis-cli -p 26379 SENTINEL masters

# Monitor failover events
kubectl exec -it redis-sentinel-0 -n cache -- \
  redis-cli -p 26379 SUBSCRIBE +sdown +odown +switch-master

# Verify from the application
kubectl exec -it deployment/api-server -n app -- \
  sh -c 'while true; do
    RESULT=$(redis-cli -h redis-sentinel.cache.svc.cluster.local -p 26379 \
      SENTINEL get-master-addr-by-name mymaster 2>/dev/null)
    echo "$(date +%H:%M:%S) Master: $RESULT"
    sleep 1
  done'
```

**Expected Redis Sentinel timeline:**

| Time | Event |
|------|-------|
| T+0s | Primary pod killed |
| T+5s | Sentinel marks primary as `+sdown` (subjectively down) |
| T+15-30s | Quorum agrees on `+odown` (objectively down) |
| T+15-35s | Sentinel elects new primary via Raft consensus |
| T+20-45s | `+switch-master` event; clients reconnect |

---

## Split-Brain Testing

Split-brain is the most feared failure mode in distributed databases: two nodes both believe they are the primary and accept writes. This causes data divergence that is extremely difficult to reconcile.

### Simulating Split-Brain with NetworkChaos

```yaml
# split-brain-simulation.yaml
# Partition the primary from Sentinel, but keep it reachable by clients
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: redis-network-partition
  namespace: cache
spec:
  action: partition
  mode: one
  selector:
    namespaces:
      - cache
    labelSelectors:
      app: redis
      role: master
  direction: both
  target:
    selector:
      namespaces:
        - cache
      labelSelectors:
        app: redis-sentinel
    mode: all
  duration: "120s"
```

**What this creates:**

```
Before partition:                After partition:

Sentinel ←→ Primary ←→ Replica  Sentinel ←─╳─→ Primary (isolated)
                                      ↕
                                  Replica (promoted to new primary)

Result: TWO primaries accepting writes = SPLIT BRAIN
```

**What to observe:**
1. Does the old primary reject writes after losing contact with Sentinel?
2. Does the application reconnect to the new primary?
3. After the partition heals, which primary "wins"?
4. Are any writes lost from the losing primary?

```bash
# During partition: Check if old primary still accepts writes
kubectl exec -it redis-0 -n cache -- redis-cli SET test-key "written-during-partition"

# Check the new primary
kubectl exec -it redis-1 -n cache -- redis-cli GET test-key

# After partition heals: Which value survives?
kubectl exec -it redis-0 -n cache -- redis-cli GET test-key
```

### Quorum Loss Testing

For systems that use quorum (etcd, ZooKeeper, Raft-based databases), losing a majority of nodes should make the cluster read-only, preventing split-brain:

```yaml
# quorum-loss-test.yaml
# Kill 2 of 3 etcd members to lose quorum
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: etcd-quorum-loss
  namespace: etcd
spec:
  action: pod-kill
  mode: fixed
  value: "2"                   # Kill 2 pods
  selector:
    namespaces:
      - etcd
    labelSelectors:
      app: etcd
  gracePeriod: 0
  duration: "60s"
```

**Expected behavior:** The remaining etcd member should refuse writes (no quorum). Applications that depend on etcd should handle the read-only state gracefully.

```bash
# Verify etcd health after killing 2 of 3 members
kubectl exec -it etcd-0 -n etcd -- \
  etcdctl endpoint health --cluster

# Attempt a write — should fail
kubectl exec -it etcd-0 -n etcd -- \
  etcdctl put /test/key "value" 2>&1

# Expected: "etcdserver: no leader" or "context deadline exceeded"
```

---

## PersistentVolume Chaos

### PV Detachment Simulation

What happens when a PersistentVolume is suddenly unavailable? This simulates cloud provider storage detachment, iSCSI timeout, or NFS server failure.

You cannot directly detach a PV with Chaos Mesh, but you can simulate the effect using IOChaos with 100% error rate:

```yaml
# pv-unavailable-simulation.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: pv-detachment-simulation
  namespace: database
spec:
  action: fault
  mode: one
  selector:
    namespaces:
      - database
    labelSelectors:
      app: postgresql
  volumePath: /var/lib/postgresql/data
  path: "**"
  errno: 5                     # EIO - Input/Output error
  percent: 100                 # All IO operations fail
  methods:
    - read
    - write
    - open
    - fsync
  containerNames:
    - postgresql
  duration: "60s"
```

**What to observe:**
1. Does PostgreSQL crash immediately or continue serving cached data?
2. If it crashes, does Patroni detect the failure and trigger failover?
3. How long until the application can write again?
4. After IO is restored, does PostgreSQL recover automatically?

### Testing PV Rescheduling

When a node fails, StatefulSet pods must be rescheduled to another node. The PV must be detached from the failed node and attached to the new node. This process can take 5-10 minutes depending on the cloud provider:

```bash
# Simulate node failure for the node running the database
# WARNING: This is destructive — only run in test clusters

# Find which node runs the database pod
NODE=$(kubectl get pod postgresql-0 -n database -o jsonpath='{.spec.nodeName}')

# Cordon the node (prevent new pods)
kubectl cordon $NODE

# Delete the pod (simulating node failure)
kubectl delete pod postgresql-0 -n database --grace-period=0 --force

# Watch the pod reschedule to another node
kubectl get pods -n database -w

# Monitor PV attachment
kubectl get pv -w

# Uncordon after the test
kubectl uncordon $NODE
```

---

## Backup Verification Through Chaos

The GitLab lesson: backups that haven't been restored are not backups. Use chaos experiments to verify your backup and restore process works.

### Backup Restoration Test

```bash
# Step 1: Create a known dataset
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "
    CREATE TABLE IF NOT EXISTS chaos_test (
      id SERIAL PRIMARY KEY,
      data TEXT,
      created_at TIMESTAMP DEFAULT NOW()
    );
    INSERT INTO chaos_test (data)
    SELECT 'record-' || generate_series(1, 1000);
    SELECT count(*) FROM chaos_test;"
# Expected: 1000 rows

# Step 2: Take a backup
kubectl exec -it postgresql-0 -n database -- \
  pg_dump -U postgres -F c -f /tmp/chaos_backup.dump postgres

# Step 3: Corrupt the data (simulating data loss)
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "DELETE FROM chaos_test WHERE id % 3 = 0;"
# Deleted ~333 rows

# Step 4: Restore from backup
kubectl exec -it postgresql-0 -n database -- \
  pg_restore -U postgres -d postgres --clean --if-exists /tmp/chaos_backup.dump

# Step 5: Verify restoration
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "SELECT count(*) FROM chaos_test;"
# Expected: 1000 rows — backup restoration verified

# Step 6: Clean up test data
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "DROP TABLE IF EXISTS chaos_test;"
```

### Automated Backup Verification Schedule

```yaml
# backup-verification-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-verification
  namespace: database
spec:
  schedule: "0 6 * * 0"        # Every Sunday at 6 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: verify-backup
              image: postgres:16
              command:
                - /bin/bash
                - -c
                - |
                  set -euo pipefail

                  echo "=== Backup Verification Started ==="
                  echo "Time: $(date -u)"

                  # Fetch latest backup from S3
                  aws s3 cp s3://backups/postgresql/latest.dump /tmp/restore.dump

                  # Create a temporary database for verification
                  PGPASSWORD=$POSTGRES_PASSWORD psql -h postgresql.database.svc \
                    -U postgres -c "CREATE DATABASE backup_verify_$(date +%Y%m%d);"

                  # Restore into the temporary database
                  PGPASSWORD=$POSTGRES_PASSWORD pg_restore -h postgresql.database.svc \
                    -U postgres -d "backup_verify_$(date +%Y%m%d)" /tmp/restore.dump

                  # Run verification queries
                  PGPASSWORD=$POSTGRES_PASSWORD psql -h postgresql.database.svc \
                    -U postgres -d "backup_verify_$(date +%Y%m%d)" -c "
                      SELECT 'users' as table_name, count(*) as row_count FROM users
                      UNION ALL
                      SELECT 'orders', count(*) FROM orders
                      UNION ALL
                      SELECT 'products', count(*) FROM products;"

                  # Clean up temporary database
                  PGPASSWORD=$POSTGRES_PASSWORD psql -h postgresql.database.svc \
                    -U postgres -c "DROP DATABASE backup_verify_$(date +%Y%m%d);"

                  echo "=== Backup Verification Complete ==="
              envFrom:
                - secretRef:
                    name: postgresql-credentials
          restartPolicy: OnFailure
```

---

## Message Queue Chaos

Stateful chaos isn't limited to databases. Message queues (RabbitMQ, Kafka) hold state that can be lost or corrupted:

### RabbitMQ Node Failure

```yaml
# rabbitmq-node-kill.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: rabbitmq-node-failure
  namespace: messaging
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - messaging
    labelSelectors:
      app: rabbitmq
  gracePeriod: 0
  duration: "120s"
```

**What to verify:**
1. Are messages in durable queues preserved after pod restart?
2. Do publishers detect the failure and retry or fail gracefully?
3. Do consumers reconnect to surviving nodes automatically?
4. Is the queue mirroring configuration working (messages available on other nodes)?

### Kafka Broker Failure

```yaml
# kafka-broker-kill.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: kafka-broker-failure
  namespace: messaging
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - messaging
    labelSelectors:
      app: kafka
  gracePeriod: 0
  duration: "180s"
```

**What to verify:**
1. Do producers with `acks=all` fail immediately or wait for the ISR to shrink?
2. Do consumers continue reading from partitions on surviving brokers?
3. Does the controller elect new partition leaders within the expected time?
4. After the killed broker restarts, does it rejoin the ISR and catch up?

---

## Common Mistakes

| Mistake | Why It's a Problem | Better Approach |
|---------|-------------------|-----------------|
| Running IOChaos at 100% error rate on a database primary without replicas | The database will crash, and without a replica to failover to, you've just caused an outage with no learning | Always ensure at least one healthy replica exists before injecting IO faults on the primary |
| Not checking replication lag before killing the primary | If the replica is 30 seconds behind and you kill the primary, 30 seconds of committed data is lost during failover | Check replication lag (`SELECT pg_last_wal_replay_lsn()` in PostgreSQL) before running failover tests |
| Testing backup restore on the primary database | A failed restore on the primary corrupts the live database — this is worse than the disaster you're simulating | Always test restores on a separate instance, a read replica, or a temporary database |
| Assuming StatefulSet pod restart means data is safe | StatefulSet pods keep their PVs, but if the PV is corrupted by an IO chaos experiment or interrupted write, the data may be inconsistent | After IO fault experiments, run database consistency checks (e.g., `pg_amcheck` for PostgreSQL) |
| Ignoring application connection pool behavior | Killing a database pod doesn't just test the database — it tests whether your application's connection pool detects dead connections and creates new ones | Monitor connection pool metrics (active, idle, broken connections) during failover tests |
| Running split-brain tests without understanding the consensus protocol | If you don't understand how your database prevents split-brain, you can't design a meaningful test or interpret the results | Read the consensus protocol documentation (Raft, Paxos, PBFT) for your database before testing split-brain scenarios |
| Not testing the "return from partition" scenario | Most teams test what happens when a partition starts but not what happens when it heals — this is where data reconciliation bugs hide | Always extend the experiment past the partition healing point and verify data consistency across all nodes |
| Skipping cleanup verification after IOChaos | FUSE mounts can persist if the chaos-daemon doesn't properly clean up, leaving the volume permanently degraded | After every IOChaos experiment, verify IO performance has returned to baseline; restart the pod if the FUSE mount persists |

---

## Quiz

### Question 1: How does IOChaos inject faults without actually corrupting data on disk?

<details>
<summary>Show Answer</summary>

IOChaos uses **FUSE (Filesystem in Userspace)** to intercept filesystem operations between the application and the actual filesystem. The FUSE layer sits in the IO path and can delay, error, or modify operations before they reach the real filesystem. The actual data on the PersistentVolume is never modified by IOChaos.

When the IOChaos CRD is deleted, the FUSE layer is removed, and IO operations go directly to the filesystem again. This is why IOChaos is safe — it simulates IO failures without causing real data corruption.

However, the **application** may corrupt its own data in response to the simulated failures (e.g., a partially written file due to an injected fsync failure), which is exactly what you're testing for.

</details>

### Question 2: You have a 3-node PostgreSQL cluster managed by Patroni. You kill the primary pod. Describe the expected sequence of events for failover.

<details>
<summary>Show Answer</summary>

1. **T+0s**: Primary pod process killed by chaos-daemon
2. **T+1-3s**: Patroni on the surviving replicas detects that the primary is not updating its leader key in the DCS (distributed configuration store — etcd or Kubernetes API)
3. **T+3-10s**: The DCS leader TTL expires (default 30s in etcd, but Patroni checks health every few seconds)
4. **T+5-15s**: Patroni initiates leader election. Each replica checks its replication lag (WAL position) and the one closest to the primary's last position wins
5. **T+10-20s**: The winning replica runs `pg_ctl promote` to become the new primary. Patroni updates the DCS with the new leader
6. **T+15-25s**: The Kubernetes Service endpoint (managed by Patroni or an endpoint controller) updates to point to the new primary
7. **T+15-30s**: Application connection pools detect broken connections, reconnect, and start sending queries to the new primary
8. **T+30-60s**: Kubernetes restarts the killed pod. Patroni on the restarted pod detects a new primary, initializes as a replica, and starts replicating from the new primary

Total failover time: typically 15-30 seconds for the database, plus 5-15 seconds for application reconnection.

</details>

### Question 3: What is the difference between killing a StatefulSet pod and killing a Deployment pod in terms of data impact?

<details>
<summary>Show Answer</summary>

**Deployment pod kill**: The pod is terminated and a new pod is created (potentially on a different node). The new pod has no persistent state — it starts fresh. Any in-memory state is lost, but there is no disk state to worry about. The Service routes traffic to healthy pods during restart.

**StatefulSet pod kill**: The pod is terminated, but the PersistentVolumeClaim remains bound to the pod's identity (e.g., `postgresql-0`'s PVC is always `data-postgresql-0`). When Kubernetes restarts the pod, it reattaches the same PVC. The data on disk survives the restart. However, there are risks:
- In-flight writes may be incomplete (write was sent but fsync didn't complete before kill)
- WAL files may need recovery on restart
- If the PV is on a node that failed, PV reattachment to a new node can take minutes
- The StatefulSet controller waits for the old pod to be fully terminated before creating a new one (unlike Deployments), so there's a gap

This is why StatefulSet chaos is more complex and requires more careful observation.

</details>

### Question 4: Explain how to test for split-brain in a Redis Sentinel cluster and what you should observe.

<details>
<summary>Show Answer</summary>

**How to test**: Use NetworkChaos to partition the primary from Sentinel nodes while keeping the primary reachable by some clients. This creates a scenario where Sentinel promotes a replica to primary (because it can't see the old primary), but the old primary is still alive and accepting writes from clients that can still reach it.

**What to observe**:
1. **During partition**: Check if the old primary continues accepting writes. If `min-replicas-to-write` is configured, the old primary should reject writes because it has no reachable replicas. If not configured, it accepts writes — this is split-brain.
2. **After partition heals**: The old primary discovers it's no longer the primary. It should demote itself to replica and sync from the new primary. Check: are the writes that happened during the partition on the old primary lost?
3. **Data divergence**: Compare keys that were written to both primaries during the partition. The old primary's writes are typically lost because Redis uses last-writer-wins based on replication, and the old primary becomes a replica that syncs from the new primary.

**Key configuration to verify**: `min-replicas-to-write 1` and `min-replicas-max-lag 10` — these settings prevent the isolated primary from accepting writes when it has no reachable replicas, which is the primary defense against split-brain in Redis.

</details>

### Question 5: Why is it important to check replication lag BEFORE running a database failover test?

<details>
<summary>Show Answer</summary>

Replication lag determines **how much data you lose** during failover. If the replica is 30 seconds behind the primary and you kill the primary, the last 30 seconds of committed transactions are not on the replica. When the replica is promoted, those transactions are lost forever.

Checking replication lag before the test serves three purposes:

1. **Safety**: If lag is unexpectedly high (minutes instead of seconds), you know the failover will cause significant data loss — you may want to abort the experiment
2. **Baseline**: You need to know the normal lag to assess whether the failover test results are representative of a real failure
3. **Measurement**: After failover, you can calculate exactly how many transactions were lost by comparing the primary's last WAL position with the promoted replica's position

For PostgreSQL: `SELECT pg_current_wal_lsn() - replay_lsn AS lag FROM pg_stat_replication;`
For Redis: `INFO replication` shows `master_repl_offset` vs `slave_repl_offset`

</details>

### Question 6: Your backup restore test succeeds, but you notice the restore took 45 minutes for a 20GB database. Is this acceptable? How would you evaluate it?

<details>
<summary>Show Answer</summary>

Whether 45 minutes is acceptable depends entirely on your **Recovery Time Objective (RTO)** — the maximum time your business can tolerate being down.

To evaluate:
1. **Compare against RTO**: If your RTO is 1 hour, 45 minutes of restore plus time for application reconnection and cache warming may be too close for comfort
2. **Consider the full recovery timeline**: Restore time is not the only delay. Add: time to detect the failure (5-15 min), time to decide to restore (variable), time to download the backup (depends on storage), restore time (45 min), application restart (5-10 min), cache warming (variable). Total could be 2+ hours.
3. **Test under realistic conditions**: Was the restore test on the same hardware/storage tier as production? Restoring to a fast SSD in dev doesn't prove the production restore will be as fast.
4. **Calculate restore rate**: 20GB / 45min = ~7.4 MB/s. Is this IO-bound or CPU-bound? Can you parallelize with pg_restore `-j` flag?

If the restore time is too long for your RTO, consider:
- Point-in-time recovery (WAL replay from a base backup) instead of full restore
- Standby replicas that are always up-to-date (failover in seconds, not minutes)
- Incremental backups that reduce restore data volume
- Higher IOPS storage for faster restore throughput

</details>

---

## Hands-On Exercise: IO Delay on PostgreSQL Primary with Failover Validation

### Objective

Inject IO read/write delay on a PostgreSQL primary managed by Patroni, observe the impact on query performance, and validate that automated failover kicks in if the primary becomes unresponsive.

### Architecture

```
┌──────────────────────────────────────────────────┐
│              PostgreSQL Cluster (Patroni)          │
│                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  pg-0        │  │  pg-1        │  │  pg-2      │ │
│  │  PRIMARY     │  │  REPLICA     │  │  REPLICA   │ │
│  │  r/w         │  │  r/o         │  │  r/o       │ │
│  │  ┌────────┐  │  │              │  │            │ │
│  │  │IOChaos │  │  │              │  │            │ │
│  │  │100ms   │  │  │              │  │            │ │
│  │  │delay   │  │  │              │  │            │ │
│  │  └────────┘  │  │              │  │            │ │
│  └──────┬───────┘  └──────────────┘  └────────────┘ │
│         │                                            │
│    ┌────▼────┐                                       │
│    │   PVC   │ ← IO delay injected here              │
│    │ 20Gi    │                                        │
│    └─────────┘                                       │
└──────────────────────────────────────────────────────┘
```

### Prerequisites

For this exercise, you need:
- A Kubernetes cluster with Chaos Mesh installed
- PostgreSQL with Patroni (use the Zalando PostgreSQL Operator or Crunchy PGO for easy setup)
- At least 3 PostgreSQL pods (1 primary + 2 replicas)

If you don't have Patroni available, you can adapt the exercise for any StatefulSet database.

### Step 1: Verify Cluster Health

```bash
# Check PostgreSQL cluster status
kubectl exec -it postgresql-0 -n database -- patronictl list

# Expected output:
# +-------------+--------+---------+----+-----------+
# | Member      | Host   | Role    | .. | Lag in MB |
# +-------------+--------+---------+----+-----------+
# | postgresql-0| ...    | Leader  | .. | 0         |
# | postgresql-1| ...    | Replica | .. | 0         |
# | postgresql-2| ...    | Replica | .. | 0         |
# +-------------+--------+---------+----+-----------+

# Check replication lag
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "SELECT client_addr, state, sent_lsn, replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
    FROM pg_stat_replication;"
```

### Step 2: Create Test Data and Measure Baseline

```bash
# Create a test table and insert data
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "
    CREATE TABLE IF NOT EXISTS chaos_perf_test (
      id SERIAL PRIMARY KEY,
      payload TEXT DEFAULT repeat('x', 1024),
      created_at TIMESTAMP DEFAULT now()
    );
    INSERT INTO chaos_perf_test (payload)
    SELECT repeat('x', 1024) FROM generate_series(1, 5000);
    SELECT count(*) FROM chaos_perf_test;"

# Measure baseline query performance
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "
    \timing on
    SELECT count(*) FROM chaos_perf_test WHERE id BETWEEN 100 AND 4900;
    SELECT * FROM chaos_perf_test ORDER BY id DESC LIMIT 10;
    INSERT INTO chaos_perf_test (payload) VALUES ('baseline-write-test');
    SELECT pg_current_wal_lsn();"

# Record baseline: query time, write time, current WAL position
```

### Step 3: Apply IO Delay

```yaml
# Save as postgres-io-delay.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: postgres-primary-io-delay
  namespace: database
spec:
  action: latency
  mode: one
  selector:
    namespaces:
      - database
    labelSelectors:
      app: postgresql
      role: master
  volumePath: /var/lib/postgresql/data
  path: "**"
  delay: "100ms"
  percent: 100
  containerNames:
    - postgresql
  duration: "300s"
```

```bash
# Apply the IO delay
kubectl apply -f postgres-io-delay.yaml
echo "IO delay started at $(date +%H:%M:%S)"
```

### Step 4: Observe Impact

```bash
# Run the same queries and compare with baseline
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "
    \timing on
    SELECT count(*) FROM chaos_perf_test WHERE id BETWEEN 100 AND 4900;
    SELECT * FROM chaos_perf_test ORDER BY id DESC LIMIT 10;
    INSERT INTO chaos_perf_test (payload) VALUES ('during-io-chaos-write');"

# Monitor Patroni's view — is the primary still healthy?
kubectl exec -it postgresql-0 -n database -- patronictl list

# Check replication lag — has it increased?
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "SELECT client_addr, state,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
    FROM pg_stat_replication;"

# Check PostgreSQL's IO wait statistics
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "SELECT * FROM pg_stat_bgwriter;"
```

### Step 5: Clean Up and Verify Recovery

```bash
# Remove the chaos experiment
kubectl delete iochaos postgres-primary-io-delay -n database

# Wait for IO to normalize
sleep 15

# Run queries again to verify recovery
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "
    \timing on
    SELECT count(*) FROM chaos_perf_test WHERE id BETWEEN 100 AND 4900;
    INSERT INTO chaos_perf_test (payload) VALUES ('post-recovery-write');"

# Verify replication lag has returned to baseline
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "SELECT client_addr, state,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
    FROM pg_stat_replication;"

# Clean up test data
kubectl exec -it postgresql-0 -n database -- \
  psql -U postgres -c "DROP TABLE IF EXISTS chaos_perf_test;"
```

### Success Criteria

- [ ] Cluster health verified before the experiment (3 members, 0 lag)
- [ ] Baseline query performance recorded (read time, write time)
- [ ] IO delay applied successfully (100ms on primary's data volume)
- [ ] Query performance during chaos documented and compared to baseline
- [ ] Replication lag during chaos monitored — did it increase?
- [ ] Patroni cluster status checked during chaos — did it consider failover?
- [ ] Recovery verified after experiment removal (queries back to baseline)
- [ ] At least one finding documented (e.g., "read queries 35x slower," "replication lag grew to 5MB," "Patroni did not trigger failover for IO delay alone")

### Expected Observations

With 100ms IO delay:
- **Read queries**: 10-50x slower (depends on how many pages need to be read from disk vs. shared buffers)
- **Write queries**: 5-20x slower (every WAL write and fsync is delayed)
- **Replication lag**: Will increase because WAL writes on the primary are slower
- **Patroni**: Likely will NOT trigger failover for IO delay alone — the primary is still responding to health checks, just slowly. This is a valuable finding: IO degradation can make a database unusable without triggering automated failover.

If you want to test the failover path, increase the delay to 500ms or higher, which may cause Patroni health checks to time out and trigger failover.

---

## Summary

Stateful chaos is the hardest and most important domain of Chaos Engineering. Databases, caches, and message queues hold state that cannot be trivially recreated, making every experiment higher-stakes than stateless pod kills. IOChaos lets you simulate storage degradation without risking real data. Failover testing verifies that your HA configuration actually works. Split-brain testing reveals the most dangerous failure mode in distributed data systems. And backup verification ensures your last line of defense is functional.

Key takeaways:
- **IOChaos uses FUSE** — it intercepts IO, it doesn't corrupt data
- **Check replication lag before failover tests** — lag determines data loss
- **Split-brain is preventable** — but only if you've configured and tested the prevention mechanisms
- **Untested backups are not backups** — schedule regular restore verification
- **IO degradation may not trigger failover** — this is a finding, not a failure of the experiment
- **Always have a replica before testing the primary** — failover without a target is just an outage

---

## Next Module

Continue to [Module 1.5: Automating Chaos & Game Days](../module-1.5-automating-chaos/) — Integrate chaos experiments into CI/CD pipelines, structure Game Days for maximum learning, and build automated abort mechanisms tied to Prometheus alerts.

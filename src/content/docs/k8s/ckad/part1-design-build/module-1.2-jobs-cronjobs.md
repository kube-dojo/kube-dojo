---
title: "Module 1.2: Jobs and CronJobs"
slug: k8s/ckad/part1-design-build/module-1.2-jobs-cronjobs
sidebar:
  order: 2
lab:
  id: ckad-1.2-jobs-cronjobs
  url: https://killercoda.com/kubedojo/scenario/ckad-1.2-jobs-cronjobs
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Essential CKAD skill with specific patterns
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 1.1 (Container Images), understanding of Pods

---

## Learning Outcomes

After completing this module, you will be able to:
- **Create** Jobs and CronJobs with correct completion counts, parallelism, and backoff limits
- **Configure** CronJob schedules, concurrency policies, and history limits
- **Debug** failed Jobs by inspecting pod logs, events, and restart behavior
- **Compare** Jobs vs CronJobs and choose the right resource for one-off vs recurring batch workloads

---

## Why This Module Matters

Not every workload runs forever. Backups run once. Reports generate hourly. Data migrations complete and exit. These are batch workloads, and Kubernetes handles them with Jobs and CronJobs.

The CKAD heavily tests Jobs because they're a core developer task. You'll see questions like:
- "Create a Job that runs to completion"
- "Create a CronJob that runs every 5 minutes"
- "Fix a failing Job"
- "Configure parallel Jobs"

> **The Factory Shift Analogy**
>
> Deployments are like permanent factory staff—they clock in and stay until fired. Jobs are like contractors hired for specific tasks—they come in, complete the work, and leave. CronJobs are like scheduled maintenance crews—they arrive at specific times (every night, every Monday), do their job, and depart.

---

## Jobs: One-Time Tasks

A Job creates one or more Pods and ensures they run to successful completion.

### Creating Jobs Imperatively

```bash
# Simple job
k create job backup --image=busybox -- echo "Backup complete"

# Job with a shell command
k create job report --image=busybox -- /bin/sh -c "date; echo 'Report generated'"

# Generate YAML
k create job backup --image=busybox --dry-run=client -o yaml -- echo "done" > job.yaml
```

### Job YAML Structure

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: backup-job
spec:
  template:
    spec:
      containers:
      - name: backup
        image: busybox
        command: ["sh", "-c", "echo 'Backing up data' && sleep 10"]
      restartPolicy: Never  # or OnFailure
  backoffLimit: 4           # Retry attempts
  ttlSecondsAfterFinished: 100  # Auto-cleanup
```

### Key Job Properties

| Property | Purpose | Default |
|----------|---------|---------|
| `restartPolicy` | What to do on failure | Must be `Never` or `OnFailure` |
| `backoffLimit` | Max retry attempts | 6 |
| `activeDeadlineSeconds` | Max job runtime | None (runs forever) |
| `ttlSecondsAfterFinished` | Auto-delete after completion | None (keep forever) |
| `completions` | Required successful completions | 1 |
| `parallelism` | Max parallel pods | 1 |

### restartPolicy Explained

```yaml
# Never: Don't restart failed containers (create new pod)
restartPolicy: Never
# Pod fails → New pod created (up to backoffLimit)

# OnFailure: Restart failed container in same pod
restartPolicy: OnFailure
# Container fails → Same pod restarts container
```

---

## Job Patterns

### Pattern 1: Single Completion (Default)

Run one pod, succeed once:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: single-job
spec:
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["echo", "Single task done"]
      restartPolicy: Never
```

### Pattern 2: Multiple Completions (Sequential)

Run task N times, one at a time:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: sequential-job
spec:
  completions: 5        # Run 5 times
  parallelism: 1        # One at a time
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Task $JOB_COMPLETION_INDEX"]
      restartPolicy: Never
```

### Pattern 3: Parallel Processing

Run multiple pods simultaneously:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 10       # 10 total completions
  parallelism: 3        # 3 pods at a time
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Processing batch && sleep 5"]
      restartPolicy: Never
```

### Pattern 4: Work Queue (Parallelism Without Completions)

Process items until queue is empty:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: queue-job
spec:
  parallelism: 3        # 3 workers
  # No completions: workers process until they exit 0
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "process-queue && exit 0"]
      restartPolicy: Never
```

---

## CronJobs: Scheduled Tasks

CronJobs run Jobs on a schedule.

### Creating CronJobs Imperatively

```bash
# Every minute
k create cronjob minute-task --image=busybox --schedule="* * * * *" -- echo "Every minute"

# Every hour at minute 30
k create cronjob hourly-task --image=busybox --schedule="30 * * * *" -- date

# Daily at midnight
k create cronjob daily-cleanup --image=busybox --schedule="0 0 * * *" -- echo "Daily cleanup"

# Generate YAML
k create cronjob backup --image=busybox --schedule="0 2 * * *" --dry-run=client -o yaml -- /backup.sh > cronjob.yaml
```

### CronJob YAML Structure

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-backup
spec:
  schedule: "0 2 * * *"                    # 2 AM daily
  concurrencyPolicy: Forbid                 # Don't overlap
  successfulJobsHistoryLimit: 3             # Keep last 3 successful
  failedJobsHistoryLimit: 1                 # Keep last 1 failed
  startingDeadlineSeconds: 200              # Max delay to start
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command: ["sh", "-c", "echo 'Backup at $(date)'"]
          restartPolicy: OnFailure
```

### Cron Schedule Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

### Common Schedules

| Schedule | Meaning |
|----------|---------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour (at minute 0) |
| `0 */2 * * *` | Every 2 hours |
| `0 0 * * *` | Daily at midnight |
| `0 0 * * 0` | Weekly on Sunday at midnight |
| `0 0 1 * *` | Monthly on the 1st at midnight |
| `30 4 * * 1-5` | 4:30 AM on weekdays |

---

## CronJob Policies

### concurrencyPolicy

What happens if a new schedule triggers while a Job is still running?

```yaml
spec:
  concurrencyPolicy: Allow    # Run concurrent (default)
  # or
  concurrencyPolicy: Forbid   # Skip if previous still running
  # or
  concurrencyPolicy: Replace  # Kill previous, start new
```

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `Allow` | Run concurrent jobs | Independent tasks |
| `Forbid` | Skip if previous running | Avoid resource contention |
| `Replace` | Stop previous, start new | Latest data matters |

### startingDeadlineSeconds

How long a Job can be delayed before it's considered missed:

```yaml
spec:
  startingDeadlineSeconds: 100  # Must start within 100s of schedule
```

If a Job can't start within this window (cluster issues, resource constraints), it's skipped.

---

## Managing Jobs and CronJobs

### Checking Status

```bash
# List jobs
k get jobs

# List cronjobs
k get cronjobs

# Get job pods
k get pods -l job-name=my-job

# Check job status
k describe job my-job

# Watch job completion
k get job my-job -w
```

### Viewing Logs

```bash
# Get logs from job's pod
k logs job/my-job

# Get logs from specific pod
k logs my-job-abc12

# Follow logs
k logs -f job/my-job
```

### Manual Trigger

```bash
# Create job from cronjob immediately
k create job manual-backup --from=cronjob/daily-backup
```

### Cleanup

```bash
# Delete job
k delete job my-job

# Delete cronjob (also deletes jobs it created)
k delete cronjob my-cronjob

# Delete completed jobs older than TTL
# (Automatic if ttlSecondsAfterFinished is set)
```

---

## Troubleshooting Jobs

### Job Won't Complete

```bash
# Check status
k describe job my-job

# Common issues:
# - Container command exits non-zero
# - Image pull fails
# - Resource limits too low
# - restartPolicy not set correctly

# Check pod logs
k logs $(k get pods -l job-name=my-job -o jsonpath='{.items[0].metadata.name}')
```

### Job Keeps Retrying

```bash
# Check backoffLimit
k get job my-job -o jsonpath='{.spec.backoffLimit}'

# If hitting limit, check why pods fail
k describe pods -l job-name=my-job
```

### CronJob Not Running

```bash
# Check cronjob status
k describe cronjob my-cronjob

# Check last schedule time
k get cronjob my-cronjob -o jsonpath='{.status.lastScheduleTime}'

# Check if suspended
k get cronjob my-cronjob -o jsonpath='{.spec.suspend}'

# Resume if suspended
k patch cronjob my-cronjob -p '{"spec":{"suspend":false}}'
```

---

## Did You Know?

- **Jobs track completions with a completion index.** In indexed completion mode, each pod knows its index via the `JOB_COMPLETION_INDEX` environment variable. This is useful for processing sharded data.

- **CronJobs use UTC by default.** If you set `schedule: "0 9 * * *"`, it runs at 9 AM UTC, not your local time. Some clusters support timezone annotations.

- **The `activeDeadlineSeconds` applies to the entire Job runtime.** If a Job takes longer than this, Kubernetes terminates it—even if tasks are still running successfully.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| `restartPolicy: Always` | Invalid for Jobs | Use `Never` or `OnFailure` |
| Forgetting `backoffLimit` | Job retries forever | Set a reasonable limit |
| Wrong cron syntax | Job never runs | Validate with crontab.guru |
| No `ttlSecondsAfterFinished` | Completed jobs accumulate | Set auto-cleanup |
| Overlapping CronJobs | Resource contention | Use `concurrencyPolicy: Forbid` |

---

## Quiz

1. **What's the valid restartPolicy values for a Job?**
   <details>
   <summary>Answer</summary>
   `Never` or `OnFailure`. `Always` is not allowed for Jobs because the container would never terminate.
   </details>

2. **How do you create a CronJob that runs every 15 minutes?**
   <details>
   <summary>Answer</summary>
   `kubectl create cronjob myj --image=busybox --schedule="*/15 * * * *" -- echo done`

   The `*/15` means "every 15 minutes".
   </details>

3. **A Job has `parallelism: 3` and `completions: 10`. What happens?**
   <details>
   <summary>Answer</summary>
   The Job runs up to 3 pods simultaneously until 10 pods have completed successfully. It processes in batches: 3 pods run, when one completes another starts, until 10 completions.
   </details>

4. **What does `concurrencyPolicy: Forbid` do?**
   <details>
   <summary>Answer</summary>
   If a CronJob triggers while a previous Job is still running, the new run is skipped. This prevents overlapping executions that might cause resource contention.
   </details>

---

## Hands-On Exercise

**Task**: Create a backup system with Jobs and CronJobs.

**Part 1: One-time Job**
```bash
# Create a job that simulates a database backup
k create job db-backup --image=busybox -- sh -c "echo 'Backing up database' && sleep 5 && echo 'Backup complete'"

# Watch completion
k get job db-backup -w

# Check logs
k logs job/db-backup
```

**Part 2: Scheduled CronJob**
```bash
# Create cronjob for hourly cleanup
k create cronjob hourly-cleanup \
  --image=busybox \
  --schedule="0 * * * *" \
  -- sh -c "echo 'Cleanup at $(date)'"

# Manually trigger for testing
k create job manual-cleanup --from=cronjob/hourly-cleanup

# Check results
k get jobs
k logs job/manual-cleanup
```

**Part 3: Parallel Job**
```yaml
# Create parallel-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-process
spec:
  completions: 6
  parallelism: 2
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Processing item $JOB_COMPLETION_INDEX && sleep 3"]
      restartPolicy: Never
```

```bash
k apply -f parallel-job.yaml
k get pods -l job-name=parallel-process -w
```

**Cleanup:**
```bash
k delete job db-backup parallel-process
k delete job manual-cleanup
k delete cronjob hourly-cleanup
```

---

## Practice Drills

### Drill 1: Basic Job Creation (Target: 2 minutes)

```bash
# Create a job that:
# - Named: hello-job
# - Runs busybox
# - Echoes "Hello from job"

k create job hello-job --image=busybox -- echo "Hello from job"

# Verify completion
k get job hello-job

# Check logs
k logs job/hello-job

# Cleanup
k delete job hello-job
```

### Drill 2: CronJob with Schedule (Target: 2 minutes)

```bash
# Create a cronjob that:
# - Named: every-minute
# - Runs every minute
# - Prints current date

k create cronjob every-minute --image=busybox --schedule="* * * * *" -- date

# Wait 1 minute and check
sleep 65
k get jobs

# Check logs of triggered job
k logs job/$(k get jobs -o jsonpath='{.items[0].metadata.name}')

# Cleanup
k delete cronjob every-minute
```

### Drill 3: Job with Retry (Target: 3 minutes)

```bash
# Create a job that fails and retries
cat << 'EOF' | k apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: retry-job
spec:
  backoffLimit: 3
  template:
    spec:
      containers:
      - name: fail
        image: busybox
        command: ["sh", "-c", "echo 'Trying...' && exit 1"]
      restartPolicy: Never
EOF

# Watch retries
k get pods -l job-name=retry-job -w

# Check job status
k describe job retry-job | grep -A5 Conditions

# Cleanup
k delete job retry-job
```

### Drill 4: Parallel Job (Target: 4 minutes)

```bash
# Create a parallel job
cat << 'EOF' | k apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel
spec:
  completions: 5
  parallelism: 2
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Worker done && sleep 2"]
      restartPolicy: Never
EOF

# Watch parallel execution
k get pods -l job-name=parallel -w

# Verify all completed
k get job parallel

# Cleanup
k delete job parallel
```

### Drill 5: CronJob with Concurrency (Target: 3 minutes)

```bash
# Create cronjob that forbids overlap
cat << 'EOF' | k apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: no-overlap
spec:
  schedule: "* * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: worker
            image: busybox
            command: ["sh", "-c", "echo 'Start' && sleep 90 && echo 'Done'"]
          restartPolicy: Never
EOF

# Check policy
k get cronjob no-overlap -o jsonpath='{.spec.concurrencyPolicy}'

# Wait 2 minutes and verify only 1 job runs
sleep 120
k get jobs -l job-name=no-overlap

# Cleanup
k delete cronjob no-overlap
```

### Drill 6: Complete Backup Solution (Target: 8 minutes)

**Build a full backup system:**

```bash
# 1. Create configmap with backup script
k create configmap backup-script --from-literal=script.sh='#!/bin/sh
echo "Starting backup at $(date)"
echo "Compressing data..."
sleep 3
echo "Uploading to storage..."
sleep 2
echo "Backup complete at $(date)"
'

# 2. Create CronJob using the script
cat << 'EOF' | k apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-system
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      ttlSecondsAfterFinished: 300
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command: ["sh", "/scripts/script.sh"]
            volumeMounts:
            - name: scripts
              mountPath: /scripts
          restartPolicy: OnFailure
          volumes:
          - name: scripts
            configMap:
              name: backup-script
EOF

# 3. Test with manual trigger
k create job test-backup --from=cronjob/backup-system

# 4. Check logs
k logs job/test-backup

# 5. Verify history limits
k get cronjob backup-system -o jsonpath='{.spec.successfulJobsHistoryLimit}'

# Cleanup
k delete cronjob backup-system
k delete job test-backup
k delete configmap backup-script
```

---

## Next Module

[Module 1.3: Multi-Container Pods](../module-1.3-multi-container-pods/) - Sidecar, init, and ambassador patterns.

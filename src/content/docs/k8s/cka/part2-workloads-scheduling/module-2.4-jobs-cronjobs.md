---
revision_pending: true
title: "Module 2.4: Jobs & CronJobs"
slug: k8s/cka/part2-workloads-scheduling/module-2.4-jobs-cronjobs
sidebar:
  order: 5
lab:
  id: cka-2.4-jobs-cronjobs
  url: https://killercoda.com/kubedojo/scenario/cka-2.4-jobs-cronjobs
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[QUICK]` - Straightforward batch workloads
>
> **Time to Complete**: 30-40 minutes
>
> **Prerequisites**: Module 2.1 (Pods)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Create** Jobs and CronJobs with appropriate parallelism, completion counts, and backoff limits
- **Debug** failed Jobs by checking pod logs, exit codes, and restart policies
- **Configure** CronJob concurrency policies and history limits for production use
- **Explain** when to use Jobs vs Deployments and the implications of each for batch workloads

---

## Why This Module Matters

Not all workloads run forever. Some run once and exit:
- Database migrations
- Batch processing
- Report generation
- Backup operations

**Jobs** handle one-time tasks. **CronJobs** handle scheduled, recurring tasks. The CKA exam tests creating Jobs with specific completion requirements and troubleshooting failed Jobs.

> **The Task Manager Analogy**
>
> Think of Jobs like tasks on a to-do list. A **Job** is a single task: "Generate monthly report." Once done, you check it off. A **CronJob** is a recurring task: "Generate monthly report on the 1st of every month." The task manager (Kubernetes) ensures the task runs, retries if it fails, and tracks completion.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Create Jobs for one-time tasks
- Configure parallelism and completions
- Handle Job failures and retries
- Create CronJobs for scheduled tasks
- Debug failed Jobs

---

## Part 1: Jobs

### 1.1 What Is a Job?

A Job creates pods that run to completion. Unlike Deployments (which keep pods running forever), Jobs expect pods to terminate successfully.

```
┌────────────────────────────────────────────────────────────────┐
│                         Job Lifecycle                           │
│                                                                 │
│   Job Created                                                   │
│       │                                                         │
│       ▼                                                         │
│   Pod Created ─────────────────────────────────────────┐       │
│       │                                                │       │
│       ▼                                                │       │
│   Pod Running                                          │       │
│       │                                                │       │
│       ├───► Exit 0 (Success) ──► Job Complete         │       │
│       │                                                │       │
│       └───► Exit ≠ 0 (Fail) ──► Retry? ──────────────►┘       │
│                                  (based on backoffLimit)       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Creating a Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pi-calculation
spec:
  template:
    spec:
      containers:
      - name: pi
        image: perl
        command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never    # Required for Jobs
  backoffLimit: 4             # Retry up to 4 times on failure
```

```bash
# Create job imperatively
kubectl create job pi --image=perl -- perl -Mbignum=bpi -wle "print bpi(100)"

# Generate YAML
kubectl create job pi --image=perl --dry-run=client -o yaml -- perl -Mbignum=bpi -wle "print bpi(100)"
```

### 1.3 Job Commands

```bash
# List jobs
kubectl get jobs

# Watch job progress
kubectl get jobs -w

# Describe job
kubectl describe job pi-calculation

# Get job logs
kubectl logs job/pi-calculation

# Delete job (also deletes pods)
kubectl delete job pi-calculation
```

> **Pause and predict**: A Job has `restartPolicy: Never` and `backoffLimit: 4`. The container fails on every attempt. How many pods will you see in `kubectl get pods` after the Job gives up? Now consider the same scenario with `restartPolicy: OnFailure` -- how many pods would you see?

### 1.4 Restart Policy

Jobs require either `Never` or `OnFailure`:

| Policy | Behavior |
|--------|----------|
| `Never` | Usually create a new pod after failure |
| `OnFailure` | Restart container in same pod on failure |

```yaml
spec:
  template:
    spec:
      restartPolicy: Never      # New pod per failure
      # restartPolicy: OnFailure  # Restart same pod
```

> **Did You Know?**
>
> With `restartPolicy: Never`, failed attempts usually create new pods until the Job hits its retry or deadline limits. With a backoffLimit of 4, you might see 5 pods (1 original + 4 retries). With `OnFailure`, you see fewer pods because containers restart in place.

---

## Part 2: Job Completions and Parallelism

### 2.1 Running Multiple Completions

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  completions: 5          # Job succeeds when 5 pods complete successfully
  parallelism: 2          # Run 2 pods at a time
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Processing item; sleep 5"]
      restartPolicy: Never
```

### 2.2 Parallelism Patterns

| Pattern | completions | parallelism | Behavior |
|---------|-------------|-------------|----------|
| Single pod | 1 (default) | 1 (default) | One pod runs to completion |
| Fixed completions | N | M | M pods run in parallel until N succeed |
| Work queue | unset | N | N pods run until one succeeds |

```
┌────────────────────────────────────────────────────────────────┐
│              Completions=5, Parallelism=2                       │
│                                                                 │
│   Time ─────────────────────────────────────────────────►      │
│                                                                 │
│   Slot 1: [Pod 1 ✓] [Pod 3 ✓] [Pod 5 ✓]                        │
│   Slot 2: [Pod 2 ✓] [Pod 4 ✓]                                  │
│                                                                 │
│   2 pods run concurrently, until 5 completions achieved        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 Examples

```bash
# Scale parallelism of an existing job (completions is immutable)
kubectl create job batch --image=busybox -- sh -c "echo done; sleep 30"
kubectl patch job batch -p '{"spec":{"parallelism":3}}'

# Or create with YAML
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 10
  parallelism: 3
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Task complete; sleep 2"]
      restartPolicy: Never
EOF

# Wait for completion
kubectl wait --for=condition=complete job/parallel-job --timeout=90s
kubectl get jobs parallel-job
```

---

## Part 3: Job Failure Handling

> **Pause and predict**: A Job with `activeDeadlineSeconds: 60` and `backoffLimit: 10` runs a container that takes 15 seconds per attempt and always fails. Will the Job hit the backoff limit or the deadline first? How many pods will be created?

### 3.1 backoffLimit

Controls how many times to retry:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: failing-job
spec:
  backoffLimit: 3           # Retry 3 times, then fail
  template:
    spec:
      containers:
      - name: fail
        image: busybox
        command: ["sh", "-c", "exit 1"]  # Always fails
      restartPolicy: Never
```

### 3.2 activeDeadlineSeconds

Maximum time for job to run:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: timeout-job
spec:
  activeDeadlineSeconds: 60    # Kill job after 60 seconds
  template:
    spec:
      containers:
      - name: long-task
        image: busybox
        command: ["sleep", "120"]  # Tries to run 2 minutes
      restartPolicy: Never
```

### 3.3 Checking Job Status

```bash
# Job status
kubectl get job myjob
# NAME    COMPLETIONS   DURATION   AGE
# myjob   3/5           2m         5m

# Detailed status
kubectl describe job myjob | grep -A5 "Pods Statuses"

# Check failed pods
kubectl get pods -l job-name=myjob --field-selector=status.phase=Failed
```

---

## Part 4: CronJobs

### 4.1 What Is a CronJob?

A CronJob creates Jobs on a schedule, like cron in Linux.

```
┌────────────────────────────────────────────────────────────────┐
│                        CronJob                                  │
│                                                                 │
│   Schedule: "0 * * * *" (hourly)                               │
│                                                                 │
│   1:00 ──► Creates Job ──► Creates Pod ──► Completes          │
│   2:00 ──► Creates Job ──► Creates Pod ──► Completes          │
│   3:00 ──► Creates Job ──► Creates Pod ──► Completes          │
│   ...                                                           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Cron Schedule Syntax

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

| Schedule | Description |
|----------|-------------|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour |
| `0 0 * * *` | Every day at midnight |
| `0 0 * * 0` | Every Sunday at midnight |
| `*/5 * * * *` | Every 5 minutes |
| `0 9-17 * * 1-5` | Every hour 9-17, Mon-Fri |

### 4.3 Creating a CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "0 2 * * *"           # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command: ["sh", "-c", "echo Backup started; sleep 10; echo Backup done"]
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3   # Keep 3 successful job records
  failedJobsHistoryLimit: 1       # Keep 1 failed job record
```

```bash
# Create CronJob imperatively
kubectl create cronjob backup --image=busybox --schedule="0 2 * * *" -- sh -c "echo Backup done"

# Generate YAML
kubectl create cronjob backup --image=busybox --schedule="*/5 * * * *" --dry-run=client -o yaml -- echo "hello"
```

### 4.4 CronJob Commands

```bash
# List CronJobs
kubectl get cronjobs
kubectl get cj           # Short form

# Describe
kubectl describe cronjob backup

# Manually trigger a job from CronJob
kubectl create job --from=cronjob/backup backup-manual

# Suspend CronJob
kubectl patch cronjob backup -p '{"spec":{"suspend":true}}'

# Resume CronJob
kubectl patch cronjob backup -p '{"spec":{"suspend":false}}'

# Delete CronJob (also deletes Jobs it created)
kubectl delete cronjob backup
```

> **Stop and think**: You have a CronJob that runs a database backup every hour, but sometimes the backup takes 90 minutes. With the default `concurrencyPolicy: Allow`, two backup jobs would overlap. What could go wrong with concurrent backups, and which concurrency policy would you choose instead?

### 4.5 CronJob Concurrency Policy

```yaml
spec:
  concurrencyPolicy: Allow    # Default - allow concurrent jobs
  # concurrencyPolicy: Forbid   # Skip if previous still running
  # concurrencyPolicy: Replace  # Kill previous, start new
```

| Policy | Behavior |
|--------|----------|
| `Allow` | Multiple Jobs can run simultaneously |
| `Forbid` | Skip new Job if previous still running |
| `Replace` | Kill running Job, start new one |

> **Exam Tip**
>
> For scheduled backup tasks, use `concurrencyPolicy: Forbid` to prevent overlapping runs. For quick tasks that shouldn't overlap, `Replace` might be better.

---

## Part 5: Debugging Jobs

### 5.1 Common Job Issues

| Issue | Symptom | Debug Command |
|-------|---------|---------------|
| Image pull failure | Pod in ImagePullBackOff | `kubectl describe pod <pod>` |
| Command failure | Job may not complete successfully | `kubectl logs job/<job-name>` |
| Timeout | Job killed | Check `activeDeadlineSeconds` |
| Too many retries | Multiple failed pods | Check `backoffLimit` |

### 5.2 Debugging Workflow

```bash
# 1. Check job status
kubectl get job myjob
kubectl describe job myjob

# 2. Find pods created by job
kubectl get pods -l job-name=myjob

# 3. Check pod logs
kubectl logs <pod-name>
kubectl logs job/myjob  # Auto-selects a pod

# 4. If still running, exec into pod
kubectl exec -it <pod-name> -- /bin/sh

# 5. Check events
kubectl get events --field-selector involvedObject.name=myjob
```

---

## Did You Know?

- **Jobs don't auto-delete** by default. Set `ttlSecondsAfterFinished` to auto-cleanup completed Jobs.

- **CronJob timezone** is based on the controller-manager's timezone (usually UTC). Plan schedules accordingly.

- **Job pods remain** after completion for log inspection. Delete the Job to clean up pods.

- **Indexed Jobs** (Kubernetes 1.21+) assign unique indexes to pods for parallel processing patterns.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `restartPolicy: Always` | Job is rejected | Use `Never` or `OnFailure` |
| Forgetting backoffLimit | Infinite retries | Set appropriate `backoffLimit` |
| Wrong cron syntax | Job may not trigger as expected | Verify with crontab.guru |
| Not checking logs | Unknown failure cause | Always check `kubectl logs job/name` |
| CronJob overlap | Resource contention | Set `concurrencyPolicy: Forbid` |

---

## Quiz

1. **A developer creates a Job with `restartPolicy: Always` and wonders why it gets rejected. They argue that retrying should mean restarting. Explain why `Always` is invalid for Jobs and describe the practical difference between `Never` and `OnFailure` for a Job that might fail.**
   <details>
   <summary>Answer</summary>
   `restartPolicy: Always` is invalid for Jobs because it would create a pod that never terminates -- the kubelet would restart the container forever, and the Job could never reach a "completed" state. Jobs need pods to eventually exit. With `Never`, each failure creates a new pod (the old failed pod stays for log inspection), so with `backoffLimit: 4` you might see 5 pods total. With `OnFailure`, the same pod's container is restarted in place, so you see only 1 pod but with multiple restarts. Use `Never` when you need to inspect failed pod logs side-by-side; use `OnFailure` to keep your pod count clean.
   </details>

2. **Your data pipeline needs to process 100 items. Each item takes about 30 seconds. You want to finish in under 10 minutes. Design the Job spec with appropriate `completions` and `parallelism` values, and explain what happens if one of the parallel pods fails halfway through.**
   <details>
   <summary>Answer</summary>
   Set `completions: 100` and `parallelism: 6` (or higher). With 6 pods running in parallel, each taking 30 seconds, you can complete 100 items in roughly `ceil(100/6) * 30s = 510s` (about 8.5 minutes), safely under 10 minutes. If one pod fails, the Job controller creates a replacement pod to redo that specific completion (failed completions don't count toward the 100). The `backoffLimit` controls how many total failures are tolerated before the Job is marked as failed. Set it high enough to handle transient failures (e.g., `backoffLimit: 10`) but not so high that a systematic bug creates hundreds of failed pods.
   </details>

3. **It's 3 AM and your on-call pager fires because a CronJob-created backup hasn't run. The CronJob schedule is `0 2 * * *` (daily at 2 AM). You run `kubectl get cronjobs` and see `LAST SCHEDULE: <none>`. How do you investigate, and how do you immediately trigger the backup while you fix the root cause?**
   <details>
   <summary>Answer</summary>
   First, check if the CronJob is suspended: `kubectl get cronjob backup -o yaml | grep suspend`. If `suspend: true`, that explains it. Next, check `kubectl describe cronjob backup` for events -- the CronJob controller may have logged failures. Also verify the cron schedule syntax is correct (a common mistake is swapping minute/hour fields). To trigger the backup immediately while investigating, run `kubectl create job --from=cronjob/backup backup-emergency`. This creates a Job using the CronJob's template without waiting for the next scheduled time. After the emergency run succeeds, fix the root cause (unsuspend, fix schedule, or check RBAC permissions).
   </details>

4. **You have a CronJob that runs every 5 minutes to aggregate metrics, but sometimes the aggregation takes 7 minutes. With `concurrencyPolicy: Allow` (the default), overlapping runs are causing duplicate data. You switch to `Forbid`, but now some scheduled runs are being skipped entirely. What is the trade-off between `Forbid` and `Replace`, and which would you choose for this use case?**
   <details>
   <summary>Answer</summary>
   With `Forbid`, the new scheduled run is silently skipped if the previous is still running. You avoid duplicates but miss data from the skipped interval. With `Replace`, the running Job is terminated and a new one starts fresh, which means the in-progress aggregation is lost but you always have the most recent run executing. For a metrics aggregation use case, `Forbid` is usually better because the long-running job will eventually complete and cover that interval's data. `Replace` would waste the 7 minutes of work already done. However, the real fix is to optimize the aggregation to finish within 5 minutes, or change the schedule to every 10 minutes to prevent overlap entirely.
   </details>

---

## Hands-On Exercise

**Task**: Create Jobs and CronJobs, handle failures.

**Steps**:

1. **Create a simple Job**:
```bash
kubectl create job hello --image=busybox -- echo "Hello from job"
kubectl wait --for=condition=complete job/hello --timeout=60s
kubectl get jobs
kubectl logs job/hello
kubectl delete job hello
```

2. **Create Job with completions**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-processor
spec:
  completions: 5
  parallelism: 2
  template:
    spec:
      containers:
      - name: processor
        image: busybox
        command: ["sh", "-c", "echo Processing $(hostname); sleep 3"]
      restartPolicy: Never
EOF

kubectl wait --for=condition=complete job/batch-processor --timeout=90s
kubectl get jobs batch-processor
kubectl get pods -l job-name=batch-processor
kubectl delete job batch-processor
```

3. **Create a failing Job**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: failing-job
spec:
  backoffLimit: 2
  template:
    spec:
      containers:
      - name: fail
        image: busybox
        command: ["sh", "-c", "echo 'About to fail'; exit 1"]
      restartPolicy: Never
EOF

kubectl wait --for=condition=failed job/failing-job --timeout=60s
kubectl get jobs failing-job
kubectl get pods -l job-name=failing-job  # Multiple failed pods
kubectl logs job/failing-job
kubectl delete job failing-job
```

4. **Create a CronJob**:
```bash
kubectl create cronjob minute-job --image=busybox --schedule="*/1 * * * *" -- date

# Wait for it to run
sleep 70
kubectl get cronjobs
kubectl get jobs
JOB_NAME=$(kubectl get jobs -o name | grep minute-job | head -n 1)
kubectl logs $JOB_NAME

kubectl delete cronjob minute-job
```

5. **Manually trigger CronJob**:
```bash
kubectl create cronjob backup --image=busybox --schedule="0 0 * * *" -- echo "backup"

# Trigger manually
kubectl create job --from=cronjob/backup backup-now
kubectl get jobs
kubectl wait --for=condition=complete job/backup-now --timeout=60s
kubectl logs job/backup-now

kubectl delete cronjob backup
kubectl delete job backup-now
```

**Success Criteria**:
- [ ] Can create Jobs imperatively and declaratively
- [ ] Understand completions and parallelism
- [ ] Can debug failed Jobs
- [ ] Can create CronJobs
- [ ] Can manually trigger CronJobs

---

## Practice Drills

### Drill 1: Job Creation Speed Test (Target: 2 minutes)

```bash
# Create job
kubectl create job quick --image=busybox -- echo "done"

# Wait for completion
kubectl wait --for=condition=complete job/quick --timeout=60s

# Check logs
kubectl logs job/quick

# Cleanup
kubectl delete job quick
```

### Drill 2: Parallel Job (Target: 3 minutes)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel
spec:
  completions: 6
  parallelism: 3
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo Pod: $HOSTNAME; sleep 5"]
      restartPolicy: Never
EOF

# Watch
kubectl get pods -l job-name=parallel -w &
kubectl get job parallel -w &
sleep 30
kill %1 %2 2>/dev/null

# Cleanup
kubectl delete job parallel
```

### Drill 3: Job with Timeout (Target: 3 minutes)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: timeout-test
spec:
  activeDeadlineSeconds: 10
  template:
    spec:
      containers:
      - name: long-task
        image: busybox
        command: ["sleep", "60"]
      restartPolicy: Never
EOF

# Watch job timeout
kubectl get job timeout-test -w &
sleep 15
kill %1 2>/dev/null

# Check status
kubectl describe job timeout-test | grep -A3 "Conditions"

# Cleanup
kubectl delete job timeout-test
```

### Drill 4: CronJob Creation (Target: 2 minutes)

```bash
# Create CronJob
kubectl create cronjob every-minute --image=busybox --schedule="*/1 * * * *" -- date

# Verify
kubectl get cronjob every-minute

# Wait for first run
sleep 70

# Check jobs created
kubectl get jobs

# Cleanup
kubectl delete cronjob every-minute
```

### Drill 5: Manual CronJob Trigger (Target: 2 minutes)

```bash
# Create CronJob (won't run for a while)
kubectl create cronjob daily --image=busybox --schedule="0 0 * * *" -- echo "daily task"

# Trigger manually
kubectl create job --from=cronjob/daily daily-manual-run

# Check
kubectl get jobs
kubectl wait --for=condition=complete job/daily-manual-run --timeout=60s
kubectl logs job/daily-manual-run

# Cleanup
kubectl delete cronjob daily
kubectl delete job daily-manual-run
```

### Drill 6: Troubleshooting Failed Job (Target: 5 minutes)

```bash
# Create intentionally broken job
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: broken
spec:
  backoffLimit: 2
  template:
    spec:
      containers:
      - name: app
        image: busybox
        command: ["sh", "-c", "cat /nonexistent/file"]
      restartPolicy: Never
EOF

# Diagnose
kubectl get job broken
kubectl get pods -l job-name=broken
kubectl describe job broken
kubectl logs job/broken

# Answer: What's the error? How would you fix it?

# Cleanup
kubectl delete job broken
```

### Drill 7: Challenge - Complete Job Workflow

Create a Job that:
1. Runs 4 completions, 2 at a time
2. Each pod echoes its hostname and sleeps 3 seconds
3. Has a backoff limit of 2
4. Automatically deletes after 60 seconds

```bash
# YOUR TASK: Create this Job
```

<details>
<summary>Solution</summary>

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: challenge-job
spec:
  completions: 4
  parallelism: 2
  backoffLimit: 2
  ttlSecondsAfterFinished: 60
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["sh", "-c", "echo $HOSTNAME; sleep 3"]
      restartPolicy: Never
EOF

kubectl wait --for=condition=complete job/challenge-job --timeout=60s
kubectl get job challenge-job
```

</details>

---

## Next Module

[Module 2.5: Resource Management](../module-2.5-resource-management/) - Requests, limits, and QoS classes.

## Sources

- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) — Primary upstream reference for Job lifecycle, retries, completion modes, cleanup, and failure handling.
- [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) — Primary upstream reference for schedules, concurrency policy, history limits, suspension, and timezone handling.
- [Automatic Cleanup for Finished Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/) — Explains `ttlSecondsAfterFinished` and the lifecycle of finished Job cleanup.

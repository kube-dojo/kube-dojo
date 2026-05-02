---
revision_pending: false
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

# Module 1.2: Jobs and CronJobs

> **Complexity**: `[MEDIUM]` - Essential CKAD skill with specific production tradeoffs
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 1.1 (Container Images), basic Pod lifecycle knowledge, and a working Kubernetes 1.35+ cluster

The examples in this module use the standard CKAD shortcut `alias k=kubectl`. Create it in your shell before practicing so the commands match the exam-style workflow and the troubleshooting examples below.

```bash
alias k=kubectl
```

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** Jobs and CronJobs with correct completion counts, parallelism, retry limits, cleanup controls, and schedules.
- **Configure** CronJob concurrency, deadline, suspension, and history behavior for recurring batch workloads.
- **Diagnose** failed batch workloads by correlating Job status, Pod events, container logs, restart policy, and controller retry behavior.
- **Compare** Jobs, CronJobs, Deployments, and ad hoc Pods so you can choose the right controller for one-time, recurring, and long-running work.

## Why This Module Matters

In 2017, GitLab published a detailed incident report after a production database maintenance operation went badly wrong and left the company restoring data under intense customer pressure. The failure was not a Kubernetes Job failure, but the lesson is directly relevant: operational work that feels like "just a script" can become a business incident when retries, scheduling, ownership, and cleanup are vague. A backup, migration, report, or cleanup task is not safer because it is short-lived; it is safer only when the platform knows when it should start, when it should stop, how many times it may retry, and what evidence it should leave behind for diagnosis.

Kubernetes separates this kind of work from Deployments because the desired end state is different. A Deployment tries to keep a number of Pods running indefinitely, while a Job tries to reach a number of successful completions and then stop creating Pods. A CronJob adds time to that model: it creates Jobs on a schedule, applies overlap rules when a previous run is still active, and retains a bounded amount of history so teams can inspect recent successes and failures without letting old Pods fill the namespace.

For CKAD work, Jobs and CronJobs are high-value because they mix API knowledge with debugging judgment. You may be asked to create a Job imperatively, generate YAML for a CronJob, change `parallelism`, fix an invalid `restartPolicy`, or explain why a scheduled backup did not start. This module teaches the mechanics, but it also teaches the operational shape: every batch workload has a start rule, a completion rule, a retry rule, a cleanup rule, and a failure investigation path.

That operational shape is the difference between "a command that happened to run" and "a workload the platform can reason about." If a one-off migration fails on a developer laptop, the evidence may live only in a terminal scrollback. If the same migration runs as a Job, the cluster records status, events, logs, owner references, and retry attempts in places the whole team can inspect. The controller does not make bad scripts good, but it gives good scripts a reliable execution envelope.

CronJobs add another layer of accountability because schedules often outlive the person who wrote them. A cleanup job created during a release crunch may still be running months later, and a backup job may become part of compliance evidence. For that reason, a CronJob manifest should read like an operational policy: when it runs, what happens if it is late, what happens if it overlaps, how much history remains, and how a human can test the same template without waiting for the next scheduled time.

> **The Factory Shift Analogy**
>
> Deployments are like permanent factory staff: they clock in and stay until the business changes the staffing plan. Jobs are like contractors hired for a specific piece of work: they arrive, complete the work, and leave records behind. CronJobs are like scheduled maintenance crews: they arrive at specific times, do the work, and follow rules about whether a late or overlapping shift should still happen.

## Jobs: Completion Controllers For One-Time Work

A Job is a controller for finite work. It owns one or more Pods, watches their exit results, and decides whether enough Pods have succeeded to mark the work complete. That distinction matters because Kubernetes does not read your script and infer whether the backup, migration, or report was meaningful; it only sees whether containers exit with status zero or non-zero. Your container command therefore becomes part of the contract between the application and the control plane.

The simplest Job runs one Pod and needs one successful completion. This is the pattern you use for small migrations, smoke reports, and exam tasks where the command does a single piece of work and exits. The imperative command is fast for CKAD tasks, and the dry-run form is useful when you need to add fields that `k create job` does not expose directly.

```bash
# Simple job
k create job backup --image=busybox -- echo "Backup complete"

# Job with a shell command
k create job report --image=busybox -- /bin/sh -c "date; echo 'Report generated'"

# Generate YAML
k create job backup --image=busybox --dry-run=client -o yaml -- echo "done" > job.yaml
```

When you turn that command into YAML, the important part is not the `kind: Job` line by itself. The important part is the nested Pod template and the Job-level controls around it. The template says what work should run; `backoffLimit`, `activeDeadlineSeconds`, `completions`, `parallelism`, and `ttlSecondsAfterFinished` say how the controller should behave when work succeeds, fails, takes too long, or finishes and needs cleanup.

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

| Property | Purpose | Default |
|----------|---------|---------|
| `restartPolicy` | What to do on failure | Must be `Never` or `OnFailure` |
| `backoffLimit` | Max retry attempts | 6 |
| `activeDeadlineSeconds` | Max job runtime | None (runs forever) |
| `ttlSecondsAfterFinished` | Auto-delete after completion | None (keep forever) |
| `completions` | Required successful completions | 1 |
| `parallelism` | Max parallel pods | 1 |

The `restartPolicy` rule is one of the easiest ways to catch a fake Job manifest. Jobs may use `Never` or `OnFailure`; they may not use `Always`, because an always-restarting Pod can never naturally express successful completion. With `Never`, a failed container leaves a failed Pod and the Job controller creates another Pod if retries remain. With `OnFailure`, kubelet restarts the container inside the same Pod, which can be cheaper but sometimes hides the history you wanted to inspect.

The tradeoff between `Never` and `OnFailure` is partly about evidence. `Never` tends to leave a clearer trail because each failed Pod has its own events, status, and logs, which helps when you are learning or when the failure changes between attempts. `OnFailure` can be better for short transient failures because kubelet can restart the container without forcing the Job controller to create a replacement Pod. Neither policy fixes a broken command; each only changes where retries happen and what evidence remains.

> **Pause and predict**: A Job requires `restartPolicy` to be set to either `Never` or `OnFailure`. Why can't you use `Always`, the default style you may associate with long-running controllers? Think about what a Job is supposed to prove before you read the explanation in the next paragraph.

The reason is that a Job is complete only when the controller can count successful Pod completions. A container that restarts forever is useful for a web server, but it is a poor signal for batch work because it keeps moving instead of finishing. If you need a worker process that continuously watches a queue, a Deployment may be the better controller; if you need a bounded number of successful attempts, a Job is the better controller.

```yaml
# Never: Don't restart failed containers (create new pod)
restartPolicy: Never
# Pod fails -> New pod created (up to backoffLimit)

# OnFailure: Restart failed container in same pod
restartPolicy: OnFailure
# Container fails -> Same pod restarts container
```

The next design choice is how many successful completions you want and how much concurrency the cluster should allow. A single completion is the default and fits one-off work. Multiple sequential completions fit repeatable independent work when order or resource pressure matters. Parallel completions fit a workload where many shards can run at the same time, provided the application can determine which shard to process and can tolerate several Pods executing together.

This is where many learners accidentally over-credit Kubernetes. The Job controller can count successful Pods, but it does not automatically divide your input data into safe units. If ten Pods all run `process-all-files.sh`, you may process the same files ten times unless the script, queue, or indexed-completion design prevents it. Parallelism is a capacity knob, not a correctness guarantee. Correctness still comes from idempotent application behavior, safe task claiming, and output paths that tolerate retries.

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

Sequential completions are useful when the cluster should run the same template several times but keep only one Pod active at a time. This can model a batch import that must respect an external rate limit, a database operation that should not have concurrent writers, or a training task where each completion consumes a separate unit of work from an external system. The key is that Kubernetes counts completions, not business objects, unless your script maps each Pod execution to a specific object.

In practice, sequential Jobs are also useful as a stepping stone while you harden a batch process. You may begin with `completions: 5` and `parallelism: 1` because you want predictable logs and low pressure on a downstream service. After you prove that each attempt is independent and repeatable, you can raise `parallelism` carefully. This staged approach is slower than jumping to maximum concurrency, but it reveals hidden assumptions before they become production outages.

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

Parallel processing changes the capacity profile. The controller still wants a fixed number of successful completions, but it is allowed to keep several Pods active at the same time. That means you must think about shared resources: a CPU-bound image processor may benefit from parallelism, while a schema migration that writes to one database table may become dangerous if several Pods execute the same mutation concurrently.

The safe way to choose parallelism is to start from the narrowest bottleneck, not from the number of nodes. A cluster may have enough CPU for many Pods, but the external API, database connection pool, object store, or license server may tolerate far fewer simultaneous clients. A Job that overwhelms a dependency can look like a Kubernetes failure even when the controller is behaving perfectly. Resource requests protect the cluster; application-level limits protect the systems your Pods call.

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

A work-queue Job is slightly different because the queue, not Kubernetes, defines when there is no more work. In that model you often set `parallelism` and omit `completions`, then let workers pull items until each worker exits successfully. This is powerful, but it shifts correctness into the queue protocol: workers must claim work safely, handle duplicate attempts, and exit when the queue is empty rather than sitting idle forever.

Queue-driven Jobs are common in production because they decouple cluster capacity from business demand. If a queue has many items, you can raise `parallelism` and run more workers; if the queue is empty, workers exit and the Job finishes. The danger is that a worker that polls forever will prevent completion, while a worker that exits too early may leave work behind. A reliable worker needs clear empty-queue semantics, timeout behavior, and logging that explains whether it completed work or found nothing to do.

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

A useful way to debug your own design is to state the completion rule in plain language before writing YAML. For example, "run one backup and stop" maps to default completions and parallelism. "Process ten independent shards with at most three Pods active" maps to `completions: 10` and `parallelism: 3`. "Run workers until Redis says no tasks remain" maps to a queue-driven design, where Kubernetes controls worker count but your application controls task ownership.

One more design habit pays off on both the exam and real teams: decide whether failed attempts are valuable evidence or just noise. During development, you may deliberately keep finished Jobs around so you can compare Pods, logs, and events. In stable scheduled work, you usually keep only a small window of history and rely on alerts or metrics for long-term visibility. Retention is not an aesthetic preference; it controls whether operators can see enough evidence without drowning in stale objects.

## CronJobs: Schedules That Create Jobs

A CronJob is a Job factory with a clock. It does not run your container directly; it creates Jobs from `spec.jobTemplate` whenever the schedule fires, and each created Job then manages its own Pods. This layering is why CronJob debugging often has two levels: first verify whether the CronJob created a Job, then inspect the Job and Pods to learn whether the run succeeded.

The schedule uses the familiar five-field cron format: minute, hour, day of month, month, and day of week. Kubernetes 1.35 CronJobs also support a `timeZone` field, which is safer than relying on controller-manager local time or comments in a manifest. If your schedule represents a business-local deadline, document the time zone directly in the spec so daylight saving changes and operator geography do not become hidden assumptions.

The time-zone detail is easy to underestimate because many lab clusters run everything in UTC and examples often avoid local business rules. Real schedules are rarely that neutral. A payroll export, end-of-day report, or maintenance window may be tied to a region, a legal jurisdiction, or a customer contract. When the schedule is business-local, the manifest should carry that fact. Otherwise, a future platform migration or daylight saving transition can change behavior without any application release.

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

The generated YAML deserves careful reading because the Job template is nested more deeply than a normal Job. Fields such as `schedule`, `concurrencyPolicy`, `successfulJobsHistoryLimit`, `failedJobsHistoryLimit`, `startingDeadlineSeconds`, and `suspend` belong to the CronJob. Fields such as `backoffLimit`, `ttlSecondsAfterFinished`, and the Pod template belong under `jobTemplate.spec`, because they configure each Job the CronJob creates.

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

The cron expression is compact, so use the diagram as a reading tool rather than memorizing examples blindly. The leftmost field changes most often, and the rightmost fields narrow the calendar. In production reviews, the biggest mistake is not a typo; it is a schedule that was technically valid but expressed the wrong business intent because the author confused day-of-month, day-of-week, or UTC.

Cron expressions also hide frequency cost. A schedule of `* * * * *` looks tiny, but it creates up to 1,440 opportunities per day for the controller to create Jobs. That may be fine for a lightweight heartbeat, but it is excessive for a report that pulls large data sets. When you choose a schedule, estimate how many Jobs it creates per day and how much log, event, and object churn that implies. The cost is not only compute; it is also operational noise.

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

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

Concurrency policy is the CronJob field that turns a valid schedule into a safe schedule. The default `Allow` means the controller may create a new Job even if the previous one is still running. `Forbid` skips a new run when the previous run has not finished. `Replace` terminates the old run and starts the new one, which can be correct for freshness-oriented work but dangerous for destructive maintenance.

Choosing among those policies is a business decision disguised as a YAML field. `Allow` says every scheduled time matters independently, even if work overlaps. `Forbid` says completion matters more than strict schedule count, so the system may skip a run to protect shared state. `Replace` says the latest run is more valuable than finishing the previous run. If you cannot explain that choice in one sentence, the CronJob probably needs a design review before it is trusted.

> **Stop and think**: You have a CronJob that runs a database backup every hour, but sometimes the backup takes 75 minutes. What happens when the next scheduled run triggers while the previous one is still running? Which policy would you choose here and why: `Allow`, `Forbid`, or `Replace`?

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

`startingDeadlineSeconds` handles missed schedules, not ordinary runtime. If the controller is unavailable, the cluster is under pressure, or the CronJob is otherwise delayed, this field tells Kubernetes how long after the scheduled time a run is still worth starting. A short deadline is useful for work that loses value quickly, such as frequent cache refreshes; a longer deadline is better for work that must eventually happen, such as compliance exports.

This field is especially important after outages. Without a clear deadline, a recovered controller may need to decide what to do about missed times according to controller behavior and history. A deadline lets you express intent: a cache refresh that is ten minutes late may be pointless, while a daily accounting export may still matter hours later. The more business meaning a run has, the more deliberate you should be about the missed-start policy.

```yaml
spec:
  startingDeadlineSeconds: 100  # Must start within 100s of schedule
```

Suspension is a quieter but important operational control. Setting `spec.suspend: true` stops future schedules without deleting the CronJob, which is useful during incident response, maintenance windows, or risky releases. It does not normally delete already-created Jobs, so you still inspect and clean active Jobs separately. That separation is helpful because stopping future work should not erase the evidence from the current failed run.

Manual triggering pairs well with suspension. During a risky change, you can suspend future scheduled runs, create a manual Job from the current template, watch the result, and then resume the schedule when you are confident. This workflow is safer than editing the schedule to an artificial time because it keeps the production schedule intact. It also gives reviewers a clean audit trail: the CronJob was paused, a manual validation ran, and the schedule was resumed.

## Retry, Cleanup, and Debugging Behavior

Troubleshooting batch workloads begins by identifying which controller state you are looking at. A CronJob may be healthy while the Job it created is failing, and a Job may be retrying while individual Pods have already terminated. Start broad with `k get cronjobs`, `k get jobs`, and labels, then narrow to `k describe`, logs, events, and Pod status. This order prevents a common mistake: reading the newest Pod log and assuming it explains the entire Job history.

The controller hierarchy is your map. CronJob status answers scheduling questions, Job status answers completion and retry questions, Pod status answers scheduling and container lifecycle questions, and container logs answer application questions. Moving down the hierarchy too early wastes time because an application log cannot tell you why the CronJob never created a Job. Moving up too late also wastes time because a healthy CronJob does not prove the created Pod had permission to read a ConfigMap or write output.

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

Logs are easiest when the Job has exactly one active or completed Pod, because `k logs job/my-job` can find the Pod for you. When there have been multiple retries, use the `job-name` label to list Pods and inspect the specific Pod that failed in the way you care about. With `restartPolicy: OnFailure`, remember that the same Pod may contain restarted container attempts, so look at restart counts and previous logs when needed.

Events explain what logs cannot. An image pull error, failed scheduling decision, missing ConfigMap, denied volume mount, or exceeded deadline may happen before your application starts, so there may be no useful application log at all. `k describe` combines status and events in one view, which is why it should be part of every Job investigation. If the container never ran, the fix is usually in the Pod template, permissions, image reference, or cluster capacity rather than in the application script.

```bash
# Get logs from job's pod
k logs job/my-job

# Get logs from specific pod
k logs my-job-abc12

# Follow logs
k logs -f job/my-job
```

Manual triggering is the safest way to test a CronJob template without waiting for the clock. The command below creates a one-off Job from the CronJob's current template, which lets you verify image pull behavior, command syntax, ConfigMap mounts, and RBAC before relying on the schedule. It does not prove the cron expression is correct, but it proves the Job template can run right now.

This distinction is useful in incident response because it narrows the search quickly. If a manual trigger fails the same way as the scheduled run, focus on the Job template and dependencies. If a manual trigger succeeds but the scheduled run did not appear, focus on the CronJob schedule, suspension state, deadline, time zone, and controller events. Separating those two failure classes keeps you from rewriting working container commands while the real problem is a scheduling rule.

```bash
# Create job from cronjob immediately
k create job manual-backup --from=cronjob/daily-backup
```

Cleanup should be designed, not treated as an afterthought. Finished Jobs and Pods are useful evidence, but they also create visual noise and consume API objects. CronJob history limits control how many created Jobs remain attached to the CronJob, while `ttlSecondsAfterFinished` lets the TTL controller remove finished Jobs after a delay. Use both when you want recent evidence without keeping every successful run forever.

The right retention window depends on how quickly humans and monitoring systems notice failures. For a frequent cleanup job, keeping three successful runs and one failed run may be enough because the next failure will happen soon and alerts should fire promptly. For a monthly compliance export, you might keep more history or export evidence elsewhere before TTL removes the Job. Kubernetes retention settings should complement, not replace, logs, metrics, and external audit storage.

```bash
# Delete job
k delete job my-job

# Delete cronjob (also deletes jobs it created)
k delete cronjob my-cronjob

# Delete completed jobs older than TTL
# (Automatic if ttlSecondsAfterFinished is set)
```

When a Job will not complete, read it like a chain of contracts. The image must pull, the Pod must schedule, the command must run, the container must exit with the intended code, and the Job controller must still have retries and time remaining. A non-zero exit code is not inherently bad; it is the application's way of telling Kubernetes that the work did not meet the success contract and should be retried or marked failed.

The exit code contract is why shell wrappers deserve care. A command like `sh -c "step1; step2; echo done"` may print a happy message even when an earlier step failed, depending on how the shell is written. In production scripts, teams often use `set -e` or explicit error checks so the container exits non-zero when the work did not actually succeed. Kubernetes can only act on the exit status it receives, so sloppy scripting can turn real failures into false completions.

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

> **What would happen if**: You create a Job with `backoffLimit: 6`, which is the default, and `restartPolicy: Never`. The container's script has a bug that always exits with code 1. Before running this, what output do you expect from `k get pods -l job-name=my-job`, and why?

The controller will keep creating replacement Pods until the failure policy is exhausted. With `restartPolicy: Never`, each failed attempt is visible as a separate failed Pod, which is noisy but very helpful during diagnosis. With `restartPolicy: OnFailure`, you may instead see restarts inside a smaller number of Pods, so your debugging habit must match the restart policy. In both cases, the root fix is the same: inspect the exit reason and application log, then correct the command, image, dependencies, or permissions.

```bash
# Check backoffLimit
k get job my-job -o jsonpath='{.spec.backoffLimit}'

# If hitting limit, check why pods fail
k describe pods -l job-name=my-job
```

CronJob failures require one extra question: did the schedule create a Job at all? If `lastScheduleTime` is empty or stale, inspect the schedule, suspension flag, deadline, and controller events. If Jobs exist but fail, shift your attention to the Job and Pods. This split keeps you from changing retry fields when the real issue is a suspended CronJob or a missed schedule.

Names can also guide the investigation. Jobs created by a CronJob normally include the CronJob name plus generated suffixes, and their Pods carry labels that link them back to the Job. Use owner references and labels instead of guessing from timestamps when several batch workloads run in the same namespace. This becomes important during outages, when several CronJobs may all create delayed or failed work around the same time.

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

A practical war story makes the difference concrete. A platform team once scheduled a nightly report generator as a CronJob with the default `Allow` policy because the YAML looked smaller and the first few runs finished quickly. At month end, each run took longer, the next schedule created another Job, and several Pods competed for the same database read replica until dashboard latency spiked. The fix was not exotic: they set `concurrencyPolicy: Forbid`, added a runtime deadline, tuned resource requests, and created an alert when a run was skipped because the previous one was still active.

## Patterns & Anti-Patterns

Good batch design starts by making the work idempotent. A Job may retry after a node failure, a container crash, or a deadline miss, and a CronJob may create a later run after an earlier run partially completed. If your script can safely run twice and converge on the same result, Kubernetes retry behavior becomes an asset instead of a threat. If your script cannot tolerate duplicates, you need external locking, transaction boundaries, or a different workflow.

Idempotency does not mean the work has no side effects. It means repeated attempts produce an acceptable final state. Uploading a file to a deterministic object key, marking a database row processed inside a transaction, or writing output with a unique completion index can all be idempotent designs. Appending blindly to a report, deleting by a broad pattern, or charging a customer inside a retrying Job are dangerous unless the application uses safeguards beyond Kubernetes.

| Pattern | When to Use It | Why It Works | Scaling Consideration |
|---------|----------------|--------------|-----------------------|
| Single-completion Job | One migration, one backup test, one report export | The controller needs exactly one successful Pod and then stops | Keep `backoffLimit` low enough that a bad command fails visibly |
| Fixed parallel completions | Many independent shards or files | `completions` defines total work and `parallelism` caps active Pods | Match parallelism to cluster capacity and downstream rate limits |
| Queue-driven workers | Work items live in Redis, a database table, or another queue | Kubernetes controls worker count while the queue controls item ownership | Workers must claim items atomically and exit cleanly when no work remains |
| CronJob with forbidden overlap | Backups, cleanup, compaction, or reports that touch shared state | A new run is skipped instead of stacking onto unfinished work | Alert on missed runs so skipped schedules are visible |

Anti-patterns usually come from treating Jobs as small Deployments or treating CronJobs as ordinary crontab lines. Kubernetes adds controller behavior, status, events, and garbage collection, but it also expects your manifest to define the lifecycle clearly. The safest review question is, "What happens if this command fails halfway through and Kubernetes tries again?"

Another useful review question is, "Who owns the result after the Pod exits?" A Job can tell you that a container exited successfully, but it cannot prove that the backup is restorable, the report is correct, or the cleanup deleted only intended data. Mature batch systems pair Kubernetes controller status with application-level verification, such as checksum validation, row counts, smoke queries, or a restore test. The controller proves execution; the application must prove business correctness.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Using a Deployment for finite migration work | The Pod restarts after success and the migration may run repeatedly | Use a Job with a clear command, retry limit, and cleanup policy |
| Leaving CronJob concurrency at `Allow` for shared-state work | Long runs overlap and compete for the same files, locks, or databases | Use `Forbid` or design the task to be safely concurrent |
| Setting high retries without observability | A broken command burns time and creates many failing Pods before anyone notices | Use a deliberate `backoffLimit`, inspect events, and alert on failed Jobs |
| Keeping every completed run forever | Namespaces become cluttered and humans stop noticing real failures | Combine history limits with `ttlSecondsAfterFinished` |

The pattern that scales best is the one whose failure mode you have rehearsed. A parallel image processor can retry individual shards if the output path includes the shard identity. A database backup should avoid overlap because two backup streams may overload storage and produce confusing evidence. A report generator may use `Replace` if only the newest data matters, but a cleanup job should rarely be replaced mid-delete unless the cleanup operation is explicitly transactional.

For CKAD, you will not build a complete production batch platform, but the same reasoning helps you answer scenario questions quickly. Identify whether the workload is finite or continuous, decide whether time is part of the requirement, choose the controller, then tune retry, concurrency, and cleanup. Most wrong answers violate one of those steps. They use a Deployment for finite work, forget overlap policy for scheduled work, or debug a Pod log when no Job was ever created.

## Decision Framework

Choose the controller by asking what "healthy" means. If healthy means "there should always be three Pods serving traffic," use a Deployment or another long-running controller. If healthy means "this task should eventually complete once," use a Job. If healthy means "a Job should be created on a calendar," use a CronJob. The controller should encode the desired lifecycle, not just happen to launch a container.

After you choose the controller, choose the failure budget for the work. Expensive or destructive jobs usually deserve fewer retries, stronger observability, and manual review when they fail. Cheap and idempotent jobs can often tolerate more retries because repeated attempts are safe and useful. The mistake is to copy retry values from an example without asking what a retry costs. A failed thumbnail job and a failed data migration do not deserve the same operational policy.

```text
Need the workload to keep running?
        |
        +-- yes --> Use a Deployment, StatefulSet, or another long-running controller.
        |
        +-- no --> Is the work scheduled repeatedly?
                  |
                  +-- no --> Use a Job with completions, parallelism, retry, and TTL rules.
                  |
                  +-- yes --> Use a CronJob with schedule, concurrency, deadline, and history rules.
```

| Decision | Prefer This | Avoid This |
|----------|-------------|------------|
| One migration must run once | Job with `parallelism: 1` and deliberate retries | Deployment that restarts the migration container forever |
| Hourly backup sometimes exceeds one hour | CronJob with `concurrencyPolicy: Forbid` | Default overlap that launches competing backup Pods |
| Cache refresh where newest run matters most | CronJob with `Replace` after checking termination safety | Killing non-idempotent work without cleanup guarantees |
| Hundreds of independent files need processing | Job with fixed `completions` and capped `parallelism` | One enormous Pod that serializes everything and hides partial failures |
| Queue workers consume until empty | Job with `parallelism` and queue-aware worker logic | Assuming Kubernetes knows how many external queue items remain |

For CKAD speed, build a mental template that you can adapt under pressure. Create or generate the object, inspect the nested spec, set lifecycle controls, run it, then diagnose from controller to Pod. The exam rarely rewards exotic features; it rewards clear resource choice, valid YAML, and practical debugging. In real clusters, the same habits prevent batch jobs from becoming silent background hazards.

For production speed, make the template readable enough that the next engineer can audit it under stress. Put the important lifecycle decisions in fields, not only in comments or runbooks. A CronJob with explicit concurrency, deadline, history, and time-zone behavior is easier to review than a minimal manifest whose behavior depends on defaults. Defaults are not bad, but hidden defaults are expensive when a scheduled task fails at an inconvenient hour and the responder has to infer the original intent.

## Did You Know?

- **Jobs track completions with a completion index.** In indexed completion mode, each Pod can know its index through `JOB_COMPLETION_INDEX`, which is useful when you shard data and want each Pod to process a different partition.
- **CronJobs support time zones in modern Kubernetes.** The `spec.timeZone` field lets you say that a business schedule should run in a named time zone instead of relying on the controller's local clock behavior.
- **The `activeDeadlineSeconds` field limits the whole Job runtime.** If the deadline expires, Kubernetes terminates active Pods for that Job even if some individual attempts were still making progress.
- **CronJob history limits and Job TTL solve different cleanup problems.** History limits decide how many Jobs a CronJob keeps, while `ttlSecondsAfterFinished` lets the TTL controller remove finished Jobs after a configured delay.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| `restartPolicy: Always` in a Job template | The author copies a Pod or Deployment template and forgets that Jobs must finish | Use `Never` when separate failed Pods help debugging, or `OnFailure` when in-Pod restarts are acceptable |
| Leaving `backoffLimit` implicit for risky commands | The default feels harmless during creation but can hide repeated application failures | Set an explicit retry limit that matches the cost and safety of the operation |
| Using the wrong cron field for business time | Cron expressions are compact, and UTC or time zone assumptions are easy to miss | Validate the expression, set `spec.timeZone` when needed, and test with a manual Job trigger |
| Omitting cleanup controls on frequent CronJobs | Finished Jobs are useful at first, so teams postpone retention decisions | Set `successfulJobsHistoryLimit`, `failedJobsHistoryLimit`, and a Job TTL where appropriate |
| Allowing overlap for shared-state tasks | `Allow` is the default, and short test runs do not reveal month-end runtime | Use `Forbid` for backups, compaction, and cleanup unless concurrent runs are explicitly safe |
| Debugging only the newest Pod log | Retries create several Pods or restarts, and the newest attempt may not show the first error | Inspect Job status, events, all Pods with the `job-name` label, and previous logs when using `OnFailure` |
| Treating `startingDeadlineSeconds` as a runtime limit | The field name sounds like a general timeout, but it controls missed starts | Use `activeDeadlineSeconds` for runtime limits and `startingDeadlineSeconds` for late schedules |

## Quiz

<details><summary>Your team deploys a database migration as a Job, but the manifest uses `restartPolicy: Always` because it was copied from a Deployment. What happens, and what should you change?</summary>

The API server rejects the Job because the Pod template for a Job must use `Never` or `OnFailure`. A Job needs Pods that can finish so the controller can count completions, and `Always` describes long-running behavior instead. Use `Never` if you want each failed attempt preserved as a separate Pod for easier postmortem inspection. Use `OnFailure` if restarting inside the same Pod is acceptable and you want fewer replacement Pods.

</details>

<details><summary>Your operations team needs a log cleanup script to run at 4:30 AM on weekdays only, and the cleanup sometimes takes more than a day. What schedule and concurrency policy would you choose?</summary>

The schedule is `30 4 * * 1-5`, which means minute 30, hour 4, any day of month, any month, Monday through Friday. For the concurrency policy, choose `Forbid` unless the cleanup is proven safe to run concurrently. `Allow` could stack multiple cleanups against the same filesystem or database, and `Replace` could terminate a cleanup halfway through. Skipping an overlapping run is usually safer than multiplying destructive maintenance.

</details>

<details><summary>You need to process 100 images through a thumbnail generator, each image takes about 10 seconds, and the cluster can handle five extra Pods. How should you configure the Job and what must the application handle?</summary>

Set `completions: 100` and `parallelism: 5` so Kubernetes runs at most five Pods while it works toward 100 successful completions. The application still needs a reliable way to map each completion to a specific image, such as an indexed completion strategy or an external queue. Without that mapping, five Pods may all process the same image or skip work. The controller manages completion counts; your application must manage business item ownership.

</details>

<details><summary>A CronJob runs every five minutes, but completed Jobs and Pods are piling up in the namespace. Which controls should you add, and why are there two kinds?</summary>

Add `successfulJobsHistoryLimit` and `failedJobsHistoryLimit` to the CronJob so it keeps only a bounded number of recent Jobs. Add `ttlSecondsAfterFinished` under the Job template when you also want finished Jobs removed after a time delay. The history limits are CronJob retention controls, while TTL is handled for finished Jobs. Using both gives operators recent evidence without letting frequent runs clutter the namespace indefinitely.

</details>

<details><summary>A scheduled backup did not run during a short control-plane outage, and now the CronJob shows no new Job for that schedule. What fields and status would you inspect before changing the image or command?</summary>

First inspect the CronJob with `k describe cronjob` and check `status.lastScheduleTime`, `spec.suspend`, `spec.schedule`, `spec.timeZone`, and `spec.startingDeadlineSeconds`. If the missed schedule exceeded the starting deadline, Kubernetes may correctly skip it rather than starting late. If the CronJob is suspended, no future schedules are created until it is resumed. Only after confirming that a Job was actually created should you move to image, command, Pod, and log debugging.

</details>

<details><summary>A Job with `restartPolicy: Never` and a failing command has several failed Pods. A teammate wants to delete the Job and recreate it immediately. What should you inspect first?</summary>

Inspect `k describe job`, list Pods with `k get pods -l job-name=<name>`, and read logs from the failed Pods before deleting evidence. With `restartPolicy: Never`, each failed attempt can preserve a different event or log sequence, especially if scheduling, image pull, and application failures happened at different times. You should also check `backoffLimit` and any deadline fields to understand whether Kubernetes stopped retrying as configured. Recreating the Job too quickly can erase the trail that explains the root cause.

</details>

<details><summary>Your team is deciding between a Deployment, a Job, and a CronJob for a nightly report generator that exits after publishing a file. Which controller fits, and when would the answer change?</summary>

A CronJob fits because the work is finite and recurring on a schedule. A plain Job would fit for a one-time report, but it would not create future runs by itself. A Deployment would be the wrong default because the desired state is not a continuously running Pod; the report command should exit after success. The answer changes only if the report process is actually a long-running service that watches for requests or queue messages indefinitely.

</details>

## Hands-On Exercise

This exercise builds a small backup and cleanup workflow in layers. You will create a one-time Job, trigger a CronJob manually, run parallel completions, observe retry behavior, and finish with a more complete backup CronJob that uses history and TTL controls. Work in a disposable namespace if you have one, and clean up at the end so your later CKAD practice is not polluted by old Jobs.

As you work through the tasks, keep a small investigation journal in your terminal or notes: object created, expected controller behavior, command used to verify it, and cleanup command. That may feel formal for tiny examples, but it trains the exact loop you need when batch work fails in a shared namespace. The goal is not only to make the commands pass; it is to connect each command to the controller decision it confirms.

### Task 1: Run and Inspect a One-Time Job

Start with the smallest useful Job: one Pod, one successful completion, one log stream to inspect. This task teaches the basic loop you will use throughout the module: create the object, wait for the controller condition, inspect status, and read logs from the Job-owned Pod.

Before running the command, predict what objects should exist after completion. You should have a Job object and at least one Pod owned by that Job. The Job should report a completed condition, and the Pod should be in a succeeded phase. If your cluster keeps finished Pods for inspection, the log should still be available through the Job reference; if retention or cleanup removes evidence quickly, describe the Job first and capture what remains.

```bash
# Create a job that simulates a database backup
k create job db-backup --image=busybox -- sh -c "echo 'Backing up database' && sleep 5 && echo 'Backup complete'"

# Wait for completion
k wait --for=condition=complete job/db-backup --timeout=60s
k get job db-backup

# Check logs
k logs job/db-backup
```

<details><summary>Solution notes for Task 1</summary>

The Job should reach the `Complete` condition, and the logs should show both backup messages. If the wait times out, describe the Job and list Pods with the `job-name=db-backup` label before changing anything. That keeps your investigation aligned with the controller hierarchy.

</details>

### Task 2: Create a CronJob and Trigger It Manually

Now create a scheduled controller, but do not wait for the clock to prove the template works. A manual Job created from the CronJob gives quick feedback on the image, command, and Pod template while keeping schedule debugging separate.

This is the workflow many teams use before enabling a new schedule. They create or update the CronJob, trigger one manual Job, inspect logs and status, and only then trust the schedule. It avoids the awkward pattern of waiting until the next hour, discovering an image or command failure, editing under time pressure, and then waiting again. Manual triggering turns a scheduled workload into a testable template.

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

<details><summary>Solution notes for Task 2</summary>

You should see the `manual-cleanup` Job complete and print the cleanup timestamp. This proves the Job template can run, but it does not prove the hourly schedule has fired. Use `k describe cronjob hourly-cleanup` when you want to inspect schedule status, last schedule time, and events.

</details>

### Task 3: Run a Parallel Job

The next manifest preserves the original parallel-processing example and gives you a concrete way to observe completions and active Pods. Apply it, watch the Pods, and compare what the Job wants with what the cluster is currently running.

Do not expect every `k get pods` call to show exactly two running Pods, because timing matters. Some Pods may finish between list operations, and the controller may create replacements quickly enough that the snapshot changes from second to second. The important evidence is the trend: the Job progresses toward six completions while maintaining no more than the configured parallelism under normal conditions. If it stalls, describe the Job and then inspect the Pods that did not succeed.

```bash
# Create parallel-job.yaml
cat << 'EOF' > parallel-job.yaml
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
EOF

k apply -f parallel-job.yaml
k get pods -l job-name=parallel-process
```

<details><summary>Solution notes for Task 3</summary>

The Job targets six successful completions while allowing two active Pods at a time. Depending on when you list Pods, you may see running Pods, completed Pods, or a mix. The important observation is that Kubernetes launches more Pods as earlier completions finish until the completion target is reached.

</details>

### Task 4: Practice Focused CKAD Drills

These drills are short on purpose, but do not treat them as memorization only. After each command, name the controller behavior you expect before checking the output. That habit makes exam debugging faster because you notice when the object behaves differently from the lifecycle you intended.

The retry drill is especially useful because it creates a controlled failure. A failing Job is not an accident here; it is a lab instrument. Watch how failed Pods accumulate with `restartPolicy: Never`, how `backoffLimit` changes when the controller stops trying, and how `k describe job` summarizes the state. Once you have seen intentional failure, accidental failure is much less mysterious.

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

# Verify retries
sleep 5
k get pods -l job-name=retry-job

# Check job status
k describe job retry-job | grep -A5 Conditions

# Cleanup
k delete job retry-job
```

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

# Verify parallel execution
sleep 5
k get pods -l job-name=parallel

# Verify all completed
k get job parallel

# Cleanup
k delete job parallel
```

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
k get jobs | grep no-overlap

# Cleanup
k delete cronjob no-overlap
```

<details><summary>Solution notes for Task 4</summary>

The basic Job should complete once, the every-minute CronJob should create at least one Job after the schedule fires, the retry Job should show failed attempts until the backoff policy is reached, the parallel Job should run up to two Pods at a time, and the no-overlap CronJob should avoid starting a second active Job while the first one is still running. If your output differs, use `k describe` before deleting anything.

</details>

### Task 5: Build a Complete Backup CronJob

The final task combines a ConfigMap-provided script, a CronJob, forbidden concurrency, history limits, and Job TTL cleanup. This is closer to production shape because the script is separated from the CronJob object and the retention behavior is visible in the spec. In a real cluster, you would also add service account permissions, resource requests, storage credentials from a safe Secret workflow, and monitoring.

Notice that the example still uses BusyBox and simulated output. That is deliberate because the learning target is Kubernetes controller behavior, not storage integration. In a real backup system, the script would need authenticated storage access, encryption decisions, restore validation, and alerting when the backup cannot be verified. The Kubernetes CronJob is the scheduler and execution envelope; it is not a complete backup product by itself.

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

<details><summary>Solution notes for Task 5</summary>

The manual trigger should create `test-backup`, run the script from the ConfigMap, and print the backup steps. The CronJob should show `Forbid` concurrency and the configured history limits. The TTL value applies to Jobs created from the template after they finish, so do not expect it to delete the CronJob itself.

</details>

### Success Criteria

- [ ] You can create a one-time Job, wait for completion, and read its logs through the Job reference.
- [ ] You can create a CronJob and manually trigger a Job from its template for fast validation.
- [ ] You can explain how `completions` and `parallelism` interact in a fixed-size batch.
- [ ] You can diagnose a failing Job by checking Job status, labeled Pods, events, logs, and retry limits.
- [ ] You can configure a CronJob with overlap protection, history limits, and finished-Job cleanup.
- [ ] You can clean up every Job, CronJob, and ConfigMap created during the exercise.

## Sources

- [Kubernetes Documentation: Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Kubernetes Documentation: CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Kubernetes Documentation: TTL Mechanism for Finished Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/)
- [Kubernetes Documentation: Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Kubernetes Documentation: Managing Resources for Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes Documentation: Configure a Pod to Use a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
- [Kubernetes Documentation: Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
- [Kubernetes Documentation: kubectl create job](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_create/kubectl_create_job/)
- [Kubernetes Documentation: kubectl create cronjob](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_create/kubectl_create_cronjob/)
- [Kubernetes API Reference: batch/v1](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/job-v1/)

## Next Module

[Module 1.3: Multi-Container Pods](../module-1.3-multi-container-pods/) - Sidecar, init, and ambassador patterns help you design Pods where multiple containers cooperate instead of forcing every responsibility into one image.

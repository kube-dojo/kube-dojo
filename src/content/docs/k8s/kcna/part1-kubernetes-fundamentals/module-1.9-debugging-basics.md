---
title: "Module 1.9: Debugging Basics (Theory)"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.9-debugging-basics
sidebar:
  order: 10
---
> **Complexity**: `[QUICK]` - Fast triage mindset
>
> **Time to Complete**: 20-25 minutes
>
> **Prerequisites**: Modules 1.1-1.8 (K8s fundamentals)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** a systematic triage approach for diagnosing Kubernetes workload failures
2. **Identify** common failure patterns from pod status, events, and log output
3. **Trace** the debugging path from symptom to root cause using kubectl describe and logs
4. **Compare** different categories of failures: image pull, scheduling, crashloop, and configuration errors

---

## Why This Module Matters

Picture this: Friday at 4:47 PM. The on-call engineer gets paged. The checkout service is down. Revenue is bleeding. Two engineers respond. The first panics -- starts deleting pods, restarting deployments, editing environment variables at random. Twenty minutes later, the situation is worse. The second engineer opens a terminal, runs three commands in sixty seconds, and says: "The new image tag has a typo. Rolling back now." Service restored in under two minutes.

The difference was not talent or experience. It was **method**. The second engineer had a systematic debugging mindset -- a mental checklist that turns chaos into a sequence of calm, logical steps. That is what this module teaches.

The KCNA does not expect you to be a troubleshooting expert. But it expects you to **know where to look** and **understand what the signals mean**. In the real world, this mindset is the single most valuable skill a Kubernetes operator can develop.

---

## Part 1: The Triage Mental Model

### 1.1 Debugging Like an ER Doctor

Emergency rooms do not treat patients by guessing. They triage -- a systematic process that saves lives by checking the most critical signals first and working outward. Kubernetes debugging works the same way.

```
THE ER TRIAGE MODEL FOR KUBERNETES

 Hospital ER                    Kubernetes Cluster
 ──────────────                 ──────────────────
 1. VITALS                      1. POD STATUS
    Heart rate, breathing          Phase, restarts, age
    "Is the patient alive?"        "Is the pod running?"

 2. CHART NOTES                 2. EVENTS & CONDITIONS
    Nurse observations,            Scheduler messages,
    recent medications             kubelet warnings
    "What happened recently?"      "What did the cluster try?"

 3. PATIENT STORY               3. LOGS
    "Where does it hurt?           Application output,
     When did it start?"           error messages, stack traces
                                   "What is the app saying?"

 4. LAB RESULTS                 4. CLUSTER CONTEXT
    Blood work, imaging            Node status, resource
    "What do the tests show?"      pressure, events timeline
                                   "Is the environment healthy?"
```

The golden rule: **never skip to surgery before checking vitals**. In Kubernetes terms, never start editing YAML or deleting pods before you understand what is actually wrong.

### 1.2 The Clue Map

Every debugging session follows this sequence. Memorize it.

```
CLUE MAP -- Your First 60 Seconds

Step  Command                                       What It Tells You
────  ──────────────────────────────────────────     ─────────────────────────────
 1    kubectl get pods -o wide                       Vitals: phase, restarts, node
 2    kubectl describe pod <name>                    Chart: events, conditions, config
 3    kubectl logs <name> [-p] [-c <container>]      Story: what the app is saying
 4    kubectl get events --sort-by=.lastTimestamp     Scene: cluster-wide timeline
```

If the pod is on a specific node and you suspect node problems, add:
```bash
kubectl get nodes -o wide          # Node status and conditions
kubectl describe node <name>       # Resource pressure, taints, capacity
```

> **Key insight**: These four steps solve the vast majority of Kubernetes issues. Resist the urge to Google before you have completed them.

---

## Part 2: Reading Pod State

### 2.1 Pod Lifecycle Phases

Every pod passes through a defined set of phases. Understanding these phases tells you immediately where in the lifecycle something went wrong.

```
POD LIFECYCLE STATE DIAGRAM

                ┌──────────┐
    Pod created │          │
   ────────────>│ Pending  │──── Scheduler cannot place pod
                │          │     (no matching node, insufficient
                └────┬─────┘      resources, PVC not bound)
                     │
                     │ Scheduled to a node
                     v
                ┌──────────┐
                │          │──── Image pull in progress
                │ Pending  │     (ContainerCreating)
                │          │
                └────┬─────┘
                     │
                     │ All containers started
                     v
                ┌──────────┐     ┌────────────┐
                │          │────>│            │
                │ Running  │     │  Failed    │── Container exited non-zero
                │          │<──┐ │            │   or was killed
                └────┬─────┘   │ └────────────┘
                     │         │
                     │         └── CrashLoopBackOff: kubelet
                     │             restarts container with
                     │             exponential backoff
                     v
                ┌────────────┐
                │            │
                │ Succeeded  │── All containers exited 0
                │            │   (normal for Jobs/CronJobs)
                └────────────┘

   Special: Unknown ── kubelet lost contact with control plane
```

### 2.2 Container States and Conditions

Within a running pod, each container has its own state:

| Container State | Meaning | What to Check |
|-----------------|---------|---------------|
| **Waiting** | Container has not started yet | `reason` field: ImagePullBackOff, ContainerCreating, CrashLoopBackOff |
| **Running** | Container is executing | `startedAt` timestamp -- recent restarts suggest instability |
| **Terminated** | Container has exited | `exitCode` (0 = success, non-zero = error), `reason` (OOMKilled, Error, Completed) |

Pod conditions provide additional detail:

| Condition | What It Means |
|-----------|---------------|
| **PodScheduled** | Pod has been assigned to a node |
| **Initialized** | Init containers have completed |
| **ContainersReady** | All containers are passing readiness probes |
| **Ready** | Pod can receive traffic via Services |

### 2.3 Events: The Cluster's Notebook

Events are the single most underused debugging resource. They record what the cluster **tried to do** and **what went wrong**. Key event fields:

- **Reason**: Machine-readable cause (e.g., `FailedScheduling`, `Pulled`, `Killing`)
- **Message**: Human-readable detail (e.g., "0/3 nodes are available: 3 Insufficient memory")
- **Count**: How many times this event fired (high counts suggest persistent problems)
- **Source**: Which component generated it (scheduler, kubelet, controller-manager)

> **Important**: Events are stored only for about one hour by default. If you wait too long, the evidence disappears. Check events early.

---

## Part 3: Common Failure Patterns

These are the five patterns you will see most often. For each one, learn the signal, the cause, and the first response.

### 3.1 CrashLoopBackOff

**What you see**: Pod status shows `CrashLoopBackOff`, restart count climbing (5, 12, 47...).

**What is happening**: The container starts, crashes, and Kubernetes restarts it. Each restart waits longer (10s, 20s, 40s... up to 5 minutes). The "BackOff" means Kubernetes is spacing out retries.

**Common causes**:
- Application error on startup (missing config, bad database connection string)
- Misconfigured command or args in the pod spec
- Missing environment variables or mounted secrets
- Liveness probe failing too aggressively (healthy app gets killed)

**First response**:
```bash
kubectl logs <pod-name> -p    # -p = previous instance (the one that crashed)
kubectl describe pod <pod-name>   # Check events, probe config, env vars
```

### 3.2 ImagePullBackOff / ErrImagePull

**What you see**: Pod stuck in `Pending` or `Waiting` state with reason `ImagePullBackOff`.

**What is happening**: The kubelet cannot download the container image from the registry.

**Common causes**:
- Typo in the image name or tag (`ngnix` instead of `nginx`)
- Private registry without proper `imagePullSecrets` configured
- Image tag does not exist (e.g., `nginx:1.99` when latest is `1.27`)
- Network issue between the node and the registry

**First response**:
```bash
kubectl describe pod <pod-name>   # Check Events section for the exact error message
# Look for: "repository does not exist", "unauthorized", "manifest unknown"
```

### 3.3 Pending (Unschedulable)

**What you see**: Pod stays in `Pending` phase indefinitely. No node is assigned.

**What is happening**: The scheduler cannot find a node that satisfies the pod's requirements.

**Common causes**:
- Insufficient CPU or memory on all nodes (requests exceed available capacity)
- Node taints with no matching tolerations on the pod
- Node affinity rules that no node satisfies
- PersistentVolumeClaim not bound (for pods with volume mounts)

**First response**:
```bash
kubectl describe pod <pod-name>   # Events will say WHY it cannot be scheduled
# Look for: "Insufficient cpu", "Insufficient memory", "didn't match Pod's node affinity"
kubectl get nodes -o wide         # Are nodes Ready? How many exist?
```

### 3.4 OOMKilled

**What you see**: Container status shows `Terminated` with reason `OOMKilled`. Pod may be in `CrashLoopBackOff` if it keeps getting killed.

**What is happening**: The container used more memory than its `resources.limits.memory` allows. The Linux kernel's OOM killer terminated the process.

**Common causes**:
- Memory limit set too low for the application's actual needs
- Memory leak in the application
- Java apps without explicit `-Xmx` that try to use more than the container limit
- Loading large datasets into memory

**First response**:
```bash
kubectl describe pod <pod-name>   # Check Last State: reason=OOMKilled
# Compare resources.limits.memory with actual usage
# Solution: increase memory limit OR fix the application's memory consumption
```

### 3.5 Probe Failures

**What you see**: Pod keeps restarting (liveness probe) or never receives traffic (readiness probe).

**What is happening**: Kubernetes health checks are failing. Liveness failures cause restarts. Readiness failures remove the pod from Service endpoints.

**Common causes**:
- Probe path wrong (`/health` vs `/healthz`)
- Application takes longer to start than `initialDelaySeconds` allows
- Probe timeout too short for slow endpoints
- Application listening on wrong port

**First response**:
```bash
kubectl describe pod <pod-name>   # Check probe configuration and events
# Look for: "Liveness probe failed", "Readiness probe failed"
# Compare probe config with what the application actually exposes
```

---

## Part 4: The Debugging Checklist

When something breaks, follow this checklist in order. Do not skip steps.

### Step 1: Get the Big Picture

```bash
kubectl get pods -o wide -A     # All namespaces, see which pods are unhealthy
```

Ask: Is it one pod or many? One namespace or several? One node or all nodes? The scope of the problem narrows your search immediately.

### Step 2: Read the Pod's Story

```bash
kubectl describe pod <name> -n <namespace>
```

Focus on three sections: **Status** (phase and container states), **Conditions** (what is true/false), and **Events** (what happened recently). Events are listed at the bottom -- scroll down.

### Step 3: Check the Logs

```bash
kubectl logs <name> -n <ns>              # Current instance
kubectl logs <name> -n <ns> -p           # Previous instance (crashed container)
kubectl logs <name> -n <ns> -c <cont>    # Specific container in multi-container pod
```

If the container is crash-looping, `-p` (previous) is essential -- the current instance may not have any logs yet.

### Step 4: Widen the Lens

```bash
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

Events from other resources (ReplicaSets, Deployments, nodes) may explain why your pod is failing. A node running out of disk, for example, affects all pods on that node.

### Step 5: Check the Infrastructure

```bash
kubectl get nodes -o wide
kubectl describe node <node-name>
```

If the problem is node-related (Pending pods, Unknown status), check node conditions: `MemoryPressure`, `DiskPressure`, `PIDPressure`, `NetworkUnavailable`. Check taints that might repel your pods.

> **KCNA exam mindset**: The exam tests whether you understand this systematic approach. Know that events explain scheduling failures, logs explain application failures, and node conditions explain infrastructure failures.

---

## Did You Know?

1. **Exponential backoff in CrashLoopBackOff follows a specific pattern**: 10s, 20s, 40s, 80s, 160s, capped at 300s (5 minutes). If your pod has been crash-looping for a while, you may wait up to 5 minutes between restart attempts -- which is why fixing the root cause is faster than waiting for retries.

2. **Events are not stored permanently**. By default, the API server retains events for only 1 hour (`--event-ttl=1h0m0s`). If you are debugging an issue that happened hours ago, the events may already be gone. This is why centralized logging is critical in production.

3. **A pod can be Running but not Ready**. The `Running` phase means containers are alive. The `Ready` condition means all readiness probes pass. A Running-but-not-Ready pod will not receive traffic from Services. This distinction catches many beginners off guard.

4. **Exit code 137 means OOMKilled (usually)**. When a container is killed by the OOM killer, it receives SIGKILL (signal 9). The exit code is 128 + 9 = 137. Exit code 143 means SIGTERM (128 + 15) -- a graceful shutdown request. These numbers appear in `kubectl describe pod` output.

---

## Common Mistakes

| Mistake | Why It Is Wrong | What to Do Instead |
|---------|-----------------|--------------------|
| Deleting and recreating the pod instead of reading logs | Destroys evidence (logs, events) and the same failure will recur | Read logs with `kubectl logs -p` and events with `kubectl describe` before taking any action |
| Running `kubectl apply` again hoping it fixes things | Re-applying the same broken spec produces the same broken result | Identify what is actually wrong first, then fix the spec |
| Ignoring the Events section in `kubectl describe` | Events contain the most actionable information about scheduling and image pull failures | Always scroll to the bottom of `describe` output and read Events |
| Setting liveness probe `initialDelaySeconds` to 0 | Applications need time to start; aggressive probes kill healthy pods before they initialize | Set `initialDelaySeconds` based on actual application startup time, with margin |
| Only checking one pod when multiple are failing | If all pods on one node fail, the problem is the node, not the pods | Check the scope first: `kubectl get pods -o wide` to see node placement |
| Editing the pod directly instead of the Deployment | Direct pod edits are lost on next restart; the controller recreates from its template | Edit the Deployment (or other controller) spec so changes persist |

---

## Knowledge Check

**Question 1**: A pod shows status `CrashLoopBackOff` with 47 restarts. What is your first command and why?

**Answer**: Run `kubectl logs <pod-name> -p` to read the logs from the previous (crashed) container instance. With 47 restarts, the current container may have just started and produced no useful output yet. The `-p` flag retrieves the logs from the last crashed instance, which will contain the error that caused the crash. After reading the logs, run `kubectl describe pod <pod-name>` to check the probe configuration and events for additional context.

**Question 2**: A pod has been in `Pending` state for 10 minutes. The Events section of `kubectl describe pod` shows: "0/3 nodes are available: 3 Insufficient memory." What does this tell you and what are your options?

**Answer**: The scheduler tried all three nodes in the cluster and none of them have enough free memory to satisfy the pod's `resources.requests.memory`. Your options are: reduce the memory request in the pod spec if the application can run with less, free up memory by removing or scaling down other workloads, or add more nodes to the cluster. The event message is explicit -- it tells you exactly how many nodes were evaluated and why each was rejected.

**Question 3**: You see a pod in `Running` state with 0/1 containers ready. The application seems healthy when you exec into the pod. What is the most likely cause?

**Answer**: The pod's readiness probe is failing. The container is running (the process is alive), but Kubernetes does not consider it ready to receive traffic because the readiness check is not passing. Common reasons include: the probe is configured to check a wrong path or port, the application has not finished initializing, or the probe timeout is too short. Check the probe configuration with `kubectl describe pod` and compare it against what the application actually exposes.

**Question 4**: A container's last state shows `Terminated` with exit code 137. What happened?

**Answer**: Exit code 137 means the process received SIGKILL (signal 9), and 128 + 9 = 137. The most common cause is OOMKilled -- the container exceeded its memory limit and the Linux kernel's OOM killer terminated it. Verify by checking the `reason` field in `kubectl describe pod`, which should say `OOMKilled`. The fix is either to increase the memory limit or to investigate why the application is consuming more memory than expected (a leak, large data loads, or JVM default heap sizing).

**Question 5**: An engineer reports that they deployed a new image tag 30 minutes ago and some pods are working with the new version while others are still running the old version. What should you check?

**Answer**: Run `kubectl rollout status deployment/<name>` to see if the rolling update is stuck or still in progress. Then run `kubectl get pods -o wide` to see which pods are new (recent AGE) and which are old. A partially completed rollout usually means the new pods are failing their readiness probes, which blocks the rollout from proceeding. Check the new pods with `kubectl describe pod` and `kubectl logs` to find what is preventing them from becoming ready. The Deployment's `maxUnavailable` and `maxSurge` settings control rollout behavior.

---

## Scenario Exercise

Work through these three scenarios using the triage method. For each one, identify the phase, state what you would check, and explain the likely cause.

### Scenario A: The Crash Loop

You run `kubectl get pods` and see:
```
NAME                     READY   STATUS             RESTARTS   AGE
api-server-7d4f8c6b5-x   0/1     CrashLoopBackOff   12         18m
api-server-7d4f8c6b5-q   0/1     CrashLoopBackOff   12         18m
api-server-7d4f8c6b5-r   0/1     CrashLoopBackOff   12         18m
```

**Triage walkthrough**: All three replicas are crash-looping, which means this is not a node-specific problem -- it is the application or its configuration. Run `kubectl logs api-server-7d4f8c6b5-x -p` to see the crash output. Common findings: a missing environment variable, a database connection that fails on startup, or a config file that was not mounted. Since all replicas fail identically, the cause is in the shared pod spec (Deployment template), not in any individual pod's environment.

### Scenario B: The Stuck Deployment

You run `kubectl get pods` and see:
```
NAME                      READY   STATUS    RESTARTS   AGE
web-app-5c9b8d7f6-a       1/1     Running   0          2d
web-app-5c9b8d7f6-b       1/1     Running   0          2d
web-app-84f7c6d9e-p       0/1     Pending   0          25m
```

**Triage walkthrough**: Two old replicas are healthy. One new replica is Pending. This looks like a rolling update that stalled because the new pod cannot be scheduled. Run `kubectl describe pod web-app-84f7c6d9e-p` and check the Events section. The scheduler will tell you exactly why: insufficient resources, unmatched taints, or an unbound PVC. The old pods keep serving traffic (they are still Ready), so there is no outage yet -- but the update is blocked until the Pending pod's scheduling constraint is resolved.

### Scenario C: The Memory Killer

You run `kubectl get pods` and see:
```
NAME                        READY   STATUS      RESTARTS   AGE
data-processor-6f8a9c-k     0/1     OOMKilled   8          45m
```

**Triage walkthrough**: The container is being killed by the OOM killer repeatedly. Run `kubectl describe pod data-processor-6f8a9c-k` and check the `Last State` section -- it should confirm reason `OOMKilled` with exit code 137. Check the `resources.limits.memory` value in the pod spec. If the limit is 256Mi but the application needs 512Mi, the fix is to increase the limit. If the limit seems generous, the application may have a memory leak. In either case, the immediate action is to verify the gap between the memory limit and the application's actual memory consumption.

---

## Next Module

Continue to [Part 2: Container Orchestration - Module 2.1: Scheduling](/k8s/kcna/part2-container-orchestration/module-2.1-scheduling/) to learn how Kubernetes decides where to place your pods.

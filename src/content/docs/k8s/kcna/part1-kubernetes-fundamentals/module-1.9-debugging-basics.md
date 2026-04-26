---
title: "Module 1.9: Debugging Basics (Theory)"
slug: k8s/kcna/part1-kubernetes-fundamentals/module-1.9-debugging-basics
sidebar:
  order: 10
---
> **Complexity**: `[QUICK]` - Fast triage mindset for Kubernetes 1.35+
>
> **Time to Complete**: 25-35 minutes
>
> **Prerequisites**: Modules 1.1-1.8, basic `kubectl` access to a practice cluster

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Debug** an unhealthy workload by following a repeatable Kubernetes triage path from symptom to probable root cause.
2. **Analyze** pod phase, container state, conditions, events, and logs to decide which signal matters most in a failure scenario.
3. **Compare** image pull, scheduling, crash loop, out-of-memory, and probe failures using their observable evidence rather than guessing.
4. **Evaluate** whether a problem belongs to the application, the pod specification, the scheduler, the node, or a controller rollout.
5. **Design** a first-response checklist that preserves evidence, narrows scope, and avoids making an incident worse.

---

## Why This Module Matters

At the end of a busy release day, a checkout Deployment starts failing during a rollout. Customers see intermittent errors, product managers ask whether to roll back, and the newest engineer on the rotation opens a terminal with a sinking feeling. One responder deletes pods because that has fixed other problems before; another immediately edits the Deployment because the failure appeared after a change. Neither has first looked at the pod status, the events, or the previous container logs, so each action destroys context while the outage clock keeps moving.

A senior operator behaves differently in the same scene. They first ask whether the failure affects one pod, one node, one namespace, or the whole cluster. They read events before changing the spec, check previous logs before the crashed container restarts again, and separate "Kubernetes could not start the workload" from "the application started and then failed." This method is not magic; it is a disciplined habit that turns noisy symptoms into a short list of testable explanations.

KCNA does not expect you to solve every production incident from memory. It does expect you to understand where Kubernetes records evidence and how the control plane, kubelet, scheduler, and application each leave different clues. Debugging basics are therefore not just an operations skill; they are a way to prove that you understand the Kubernetes object model under pressure.

---

## Part 1: Debugging Is Evidence Collection Before Action

Debugging Kubernetes begins with restraint because the first command can either preserve evidence or erase it. A pod restart, a rollout restart, or a manual edit may temporarily change the symptom while hiding the original cause. Beginners often want to "try a fix" as soon as they see red status, but experienced operators first build a timeline: what was desired, what Kubernetes attempted, what the node reported, and what the application said.

Think of the cluster as several witnesses describing the same event from different angles. The scheduler explains why a pod did or did not get a node. The kubelet explains image pulls, container starts, probe failures, and kills on the assigned node. The application explains its own crash through logs. Controllers such as Deployments explain rollout progress and whether old or new replicas are being created.

```ascii
KUBERNETES DEBUGGING WITNESSES

┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ Desired State       │     │ Cluster Decisions   │     │ Runtime Evidence    │
│ Deployment, Pod     │────▶│ Scheduler, events   │────▶│ Kubelet, logs       │
│ spec, probes, env   │     │ placement, reasons  │     │ exits, restarts     │
└────────────────────┘     └────────────────────┘     └────────────────────┘
          │                            │                            │
          ▼                            ▼                            ▼
 "What did we ask for?"      "What did Kubernetes try?"      "What actually ran?"
```

The first rule is to classify the failure before fixing it. If a pod never got scheduled, application logs will not help because no container ran. If an image cannot be pulled, changing the readiness probe is irrelevant because the process never started. If a container exits with a stack trace, node taints are unlikely to be the first explanation. Classification keeps your search narrow enough to finish under incident pressure.

You will see many Kubernetes commands in debugging guides, but the KCNA-level mental model is compact: get the visible status, describe the object, read the logs when a container has run, then widen the timeline with events and node context. You can alias `kubectl` as `k` in your shell with `alias k=kubectl` after you understand the full command; this module writes commands as `kubectl` so the examples are runnable without shell setup.

```ascii
THE FIRST RESPONSE LOOP

┌───────────────┐
│ 1. Scope      │  kubectl get pods -A -o wide
│ problem size  │  One pod, one node, one namespace, or many?
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 2. Describe   │  kubectl describe pod <pod> -n <namespace>
│ object story  │  Conditions, container states, events, mounts, probes
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 3. Read logs  │  kubectl logs <pod> -n <namespace> [-p] [-c <container>]
│ app witness   │  Current or previous container output
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 4. Widen view │  kubectl get events -n <namespace> --sort-by=.lastTimestamp
│ timeline      │  Related failures from scheduler, kubelet, and controllers
└───────────────┘
```

> **Pause and predict**: A teammate says, "The pod is broken, so I will delete it and let Kubernetes recreate it." Before reading on, decide when that action might be harmless and when it might destroy the best clue you have.

Deleting a pod managed by a Deployment is sometimes a reasonable recovery action after evidence has been collected, because the controller will create a replacement from the same template. It is a poor first action when the previous container logs, event order, or exact restart count matter. The safer habit is to inspect first, record the likely cause, then choose whether a restart, rollback, resource change, or spec fix matches the evidence.

---

## Part 2: Read Pod State Like a Timeline

A pod status line is a compressed timeline, not a final diagnosis. `STATUS` in `kubectl get pods` often shows the most urgent container reason, while the pod phase is a broader lifecycle category. That distinction matters because a pod can be in the `Running` phase while one container is not ready, or a pod can appear `Pending` because it has not been scheduled or because it is waiting for an image pull after scheduling.

```bash
kubectl get pods -n default -o wide
```

```text
NAME                         READY   STATUS             RESTARTS   AGE   IP           NODE
api-6d8b7c9f5c-f2mzp          0/1     CrashLoopBackOff   9          18m   10.244.1.8   worker-a
web-76bc6c9d7b-9nq5p          1/1     Running            0          42m   10.244.2.4   worker-b
report-5d9c997d8d-xr2hg       0/1     Pending            0          11m   <none>       <none>
```

The `READY` column tells you how many containers are ready for traffic compared with how many containers the pod defines. The `STATUS` column gives a human-friendly reason that often comes from the container state. The `RESTARTS` column tells you whether the kubelet has repeatedly started the container after termination. The `NODE` column tells you whether the scheduler has placed the pod, which is crucial for distinguishing scheduling failures from runtime failures.

```ascii
POD LIFECYCLE STATE DIAGRAM

                ┌──────────┐
    Pod created │          │
   ────────────▶│ Pending  │──── Scheduler cannot place pod
                │          │     because resources, taints,
                └────┬─────┘     affinity, or volumes block it
                     │
                     │ Scheduled to a node
                     ▼
                ┌──────────┐
                │ Waiting  │──── Kubelet is preparing containers,
                │          │     pulling images, or mounting volumes
                └────┬─────┘
                     │
                     │ Containers started
                     ▼
                ┌──────────┐     ┌────────────┐
                │ Running  │────▶│ Terminated │
                │          │     │            │
                └────┬─────┘     └─────┬──────┘
                     │                 │
                     │                 ▼
                     │          ┌──────────────┐
                     │          │ Restarted or │
                     │          │ stays failed │
                     │          └──────────────┘
                     ▼
                ┌───────────┐
                │ Succeeded │──── Normal for Jobs when all containers exit 0
                └───────────┘

   Special: Unknown means the control plane cannot determine pod state from the node.
```

A useful habit is to translate the status into a question. `Pending` asks, "Did the scheduler assign a node, and if not, why?" `ImagePullBackOff` asks, "Can the kubelet reach and authenticate to the image registry, and does the image reference exist?" `CrashLoopBackOff` asks, "What did the previous container instance print or exit with?" `Running` with `0/1` readiness asks, "Which readiness condition is false, and what probe or dependency is blocking traffic?"

| Signal | Most Useful First Question | Best First Evidence |
|---|---|---|
| `Pending` with no node | Why could the scheduler not place this pod? | `kubectl describe pod` Events section |
| `ImagePullBackOff` | What exact image pull error did the kubelet report? | Pod events from `kubectl describe pod` |
| `CrashLoopBackOff` | Why did the previous container exit? | `kubectl logs <pod> -p` and Last State |
| `Running` but not `Ready` | Which readiness condition or probe is failing? | Pod conditions, endpoints, and probe events |
| `OOMKilled` | Did the container exceed its memory limit? | Last State reason, exit code, resource limits |
| `Unknown` | Is the node unreachable or unhealthy? | Node conditions and node events |

Pod conditions provide a more structured view than the one-line status. `PodScheduled` means the scheduler assigned a node. `Initialized` means init containers completed. `ContainersReady` means all regular containers are ready. `Ready` means the pod can receive traffic through Services that select it. A pod can be running but not useful if `Ready` is false, which is exactly why Services use readiness rather than process existence.

| Condition | What It Means | Debugging Interpretation |
|---|---|---|
| `PodScheduled` | The pod has been assigned to a node. | If false, focus on scheduler events, resources, taints, affinity, and volumes. |
| `Initialized` | Init containers have completed successfully. | If false, inspect init container logs and volume or permission setup. |
| `ContainersReady` | All app containers report ready. | If false, inspect container states, readiness probes, and dependency errors. |
| `Ready` | The pod should receive Service traffic. | If false, traffic should not be routed to this pod even if it is running. |

Container states are even more specific because each container can be `Waiting`, `Running`, or `Terminated`. In a multi-container pod, one sidecar can be healthy while the main application fails, so always use `-c <container>` for logs when a pod has more than one container. `kubectl describe pod` shows current state and last state, which lets you see both the present attempt and the previous failure.

| Container State | Meaning | What to Check |
|---|---|---|
| `Waiting` | The container has not started or is backing off before the next start attempt. | Reason field such as `ImagePullBackOff`, `ContainerCreating`, or `CrashLoopBackOff`. |
| `Running` | The process is currently executing inside the container. | Start time, readiness, probes, and whether restarts have happened recently. |
| `Terminated` | The process exited or was killed. | Exit code, reason, finished time, and previous logs with `kubectl logs -p`. |

> **What would happen if** you only looked at `kubectl get pods` and saw `Running`, then told your team the service was healthy? Explain why that could be wrong when the `READY` column says `0/1`.

A senior-level reading of pod state avoids two traps. The first trap is treating Kubernetes status as a human diagnosis when it is really a clue generated by one component at one moment. The second trap is assuming all failures are application failures; Kubernetes may be unable to schedule the pod, mount a volume, pull an image, or keep a probe alive even when the application code is correct.

---

## Part 3: Use `describe`, Logs, and Events Without Mixing Their Jobs

`kubectl describe pod` is the best bridge between desired state and cluster behavior. It shows the pod spec, node assignment, IPs, conditions, mounted volumes, container state, resource requests, probes, environment references, and recent events. It is verbose because incidents are rarely solved by one field; you are looking for contradictions, such as a container that starts successfully but fails readiness, or a pod with no node and repeated `FailedScheduling` events.

```bash
kubectl describe pod api-6d8b7c9f5c-f2mzp -n default
```

When reading `describe`, use a consistent order so you do not scan randomly. First confirm the namespace and node because many debugging mistakes come from inspecting the wrong object. Then read `Status`, `Conditions`, and `Containers`, especially current state, last state, restart count, limits, requests, command, args, and probes. Finally, scroll to `Events`; the most actionable line is often at the bottom, where the kubelet or scheduler tells you exactly what failed most recently.

```ascii
HOW TO READ kubectl describe pod

┌──────────────────────────────┐
│ Identity                     │  Name, namespace, labels, owner, node
├──────────────────────────────┤
│ Status and Conditions        │  Phase, Ready, ContainersReady, Scheduled
├──────────────────────────────┤
│ Container Details            │  Image, ports, command, state, last state
├──────────────────────────────┤
│ Configuration References     │  Env, ConfigMaps, Secrets, volumes, probes
├──────────────────────────────┤
│ Events                       │  Scheduler and kubelet timeline of actions
└──────────────────────────────┘
```

Logs answer a different question: what did the application process write to standard output and standard error. Logs are valuable only after a container has actually run, which means they are usually not helpful for unscheduled pods or image pull failures. For crash loops, the `-p` flag is essential because the current container instance may be waiting to restart or may not yet have reproduced the error.

```bash
kubectl logs api-6d8b7c9f5c-f2mzp -n default
kubectl logs api-6d8b7c9f5c-f2mzp -n default -p
kubectl logs api-6d8b7c9f5c-f2mzp -n default -c api
```

Events answer what Kubernetes components attempted. Scheduler events explain placement failures, kubelet events explain image pulls and container lifecycle, and controller events can explain rollout behavior. Events are also time-limited in most clusters, so they are not a substitute for centralized observability, but they are perfect for fresh failures during practice and many real incidents.

```bash
kubectl get events -n default --sort-by=.lastTimestamp
```

A practical rule is to avoid crossing evidence streams too early. If the event says `0/3 nodes are available: 3 Insufficient memory`, do not start reading application code; the container never had a place to run. If previous logs show `FATAL: missing DB_PASSWORD`, do not spend the next ten minutes describing nodes; the app told you its startup dependency is missing. The fastest operators are not the ones who know the most commands; they are the ones who choose the next command based on the last signal.

---

## Part 4: Worked Example - Diagnose Before You Fix

A worked example shows how the clues fit together. Suppose a team deploys version `1.8.2` of an API, and the rollout stalls. The old pods still serve traffic, but the new ReplicaSet creates pods that never become ready. The team asks whether this is a bad image, a scheduling issue, or an application problem.

First, scope the failure. The output shows that only new pods are unhealthy, while old pods are still ready. That narrows the problem to the new pod template, the new image, or resources required only by the new version.

```bash
kubectl get pods -n shop -o wide
```

```text
NAME                       READY   STATUS             RESTARTS   AGE   NODE
api-58c7d5f9b6-m2q8x        1/1     Running            0          2d    worker-a
api-58c7d5f9b6-r6ndk        1/1     Running            0          2d    worker-b
api-7b9c6d4f78-jk2tp        0/1     CrashLoopBackOff   6          9m    worker-a
```

Second, check the previous logs because the new pod has already restarted several times. The `-p` flag asks Kubernetes for the logs from the previous terminated instance, which is often the only instance that captured the actual startup error.

```bash
kubectl logs api-7b9c6d4f78-jk2tp -n shop -p
```

```text
2026-04-26T09:15:12Z starting api service
2026-04-26T09:15:12Z loading configuration from environment
2026-04-26T09:15:12Z FATAL missing required environment variable: DB_PASSWORD
```

Third, verify the pod state and configuration references rather than assuming the log is complete. `describe` should show the crash loop, the restart history, and whether the environment variable is referenced from a Secret, ConfigMap, or literal value. In this case, the logs identify the application-level failure, while `describe` explains how Kubernetes was asked to provide the configuration.

```bash
kubectl describe pod api-7b9c6d4f78-jk2tp -n shop
```

```text
State:          Waiting
  Reason:       CrashLoopBackOff
Last State:     Terminated
  Reason:       Error
  Exit Code:    1
Environment:
  DB_HOST:      postgres.shop.svc.cluster.local
  DB_PASSWORD:  <set to the key 'password' in secret 'api-db'>
Events:
  Warning  BackOff  kubelet  Back-off restarting failed container api
```

The likely root cause is now specific: the new pod expects a Secret key that is missing, renamed, or not present in the `shop` namespace. The right next checks are `kubectl get secret api-db -n shop` and `kubectl describe secret api-db -n shop`, not random pod deletion. The fix should update the Secret or Deployment template consistently, then let the rollout continue and verify readiness.

```bash
kubectl get secret api-db -n shop
kubectl describe secret api-db -n shop
kubectl rollout status deployment/api -n shop
```

This example demonstrates constructive alignment between the symptom and the evidence. `CrashLoopBackOff` points to previous logs. The previous logs point to missing configuration. `describe` confirms Kubernetes is referencing a Secret for that configuration. The rollout command verifies whether the controller recovers after the underlying configuration is corrected.

---

## Part 5: Failure Patterns You Must Recognize

The most common Kubernetes failures are recognizable because each has a different first useful signal. You do not need to memorize every possible message, but you should know which evidence source owns the problem. A scheduler problem appears in scheduling events. An image problem appears in kubelet pull events. A startup problem appears in previous logs and last state. A traffic problem often appears in readiness conditions and Service endpoints.

### 5.1 CrashLoopBackOff

`CrashLoopBackOff` means a container started, exited, and is now being restarted with a delay. Kubernetes is not saying why the application failed; it is saying the kubelet is backing off before trying again. The cause may be a bad command, missing environment variable, application exception, failed dependency, incorrect file permission, or a liveness probe that kills the process after it starts.

```bash
kubectl logs <pod-name> -n <namespace> -p
kubectl describe pod <pod-name> -n <namespace>
```

The previous logs usually tell you what the process believed was wrong. The `describe` output tells you whether Kubernetes killed it, whether a probe failed, and what exit code or reason was recorded. If all replicas of the same Deployment crash the same way, suspect a shared image, command, configuration, Secret, ConfigMap, or dependency rather than an individual node.

### 5.2 ImagePullBackOff and ErrImagePull

`ErrImagePull` and `ImagePullBackOff` mean the kubelet cannot fetch the container image. The application code has not run yet, so logs are usually empty or unavailable. The event message is the primary clue because it can distinguish "image tag does not exist" from "registry requires credentials" from "network or DNS failed."

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Look for event messages containing phrases such as `manifest unknown`, `not found`, `pull access denied`, `unauthorized`, or timeout errors. A correct-looking image name can still fail if the tag was never pushed, the registry path changed, the namespace lacks `imagePullSecrets`, or the node cannot reach the registry. The fix belongs to the image reference, registry credentials, registry availability, or node networking, depending on the exact event.

### 5.3 Pending and FailedScheduling

A pod in `Pending` with no assigned node is a scheduler problem until proven otherwise. The scheduler compares the pod's requests, node selectors, affinity, taints, topology constraints, and volume requirements against available nodes. If no node satisfies the full set, the pod remains unscheduled, and events explain the rejected options.

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get nodes -o wide
```

Common messages include insufficient CPU, insufficient memory, untolerated taints, unmatched node affinity, or unbound PersistentVolumeClaims. The correct response is not to restart the pod because it has not started. You either change the pod's scheduling requirements, reduce resource requests when appropriate, provision capacity, fix the volume binding, or add the needed toleration intentionally.

### 5.4 OOMKilled

`OOMKilled` means the process exceeded its memory limit and the kernel killed it. Kubernetes reports this in container last state, and the exit code is often `137` because the process received `SIGKILL`. The pod may then enter `CrashLoopBackOff` if the controller or restart policy keeps starting the same memory-hungry process.

```bash
kubectl describe pod <pod-name> -n <namespace>
```

The immediate comparison is between the container's memory limit and the application's actual behavior. Increasing a limit can be a valid mitigation when the original limit was unrealistic, but it is not always the complete fix. A memory leak, unbounded cache, large batch job, or runtime heap setting can consume any larger limit eventually, so senior debugging distinguishes capacity mismatch from growth that should be fixed in the application.

### 5.5 Probe Failures and Running-But-Not-Ready Pods

A pod can run but receive no Service traffic because readiness failed. Liveness failures restart the container; readiness failures remove the pod from endpoints; startup probes give slow-starting applications time before liveness begins. Probe failures are common after a port, path, scheme, startup time, or dependency changes.

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get endpoints <service-name> -n <namespace>
```

The dangerous beginner mistake is to see `Running` and assume the workload is serving requests. Always compare `STATUS` with `READY`, then inspect events for messages such as `Readiness probe failed` or `Liveness probe failed`. If the application is healthy but the probe is wrong, fix the probe. If the probe is correct and the application cannot satisfy it, fix the application or its dependency.

| Pattern | Main Signal | First Command | Likely Fix Area |
|---|---|---|---|
| Crash loop | `CrashLoopBackOff`, increasing restarts | `kubectl logs <pod> -p` | App startup, command, config, dependency, probe |
| Image pull | `ImagePullBackOff`, `ErrImagePull` | `kubectl describe pod <pod>` | Image reference, registry auth, registry/network reachability |
| Scheduling | `Pending`, no node assigned | `kubectl describe pod <pod>` | Requests, taints, affinity, PVCs, node capacity |
| Memory kill | `OOMKilled`, exit code `137` | `kubectl describe pod <pod>` | Memory limit, leak, heap sizing, workload shape |
| Readiness failure | `Running` with `0/1` ready | `kubectl describe pod <pod>` | Probe path, port, startup time, dependency health |
| Node issue | Many pods fail on one node | `kubectl describe node <node>` | Node pressure, kubelet, networking, disk, taints |

---

## Part 6: Build a First-Response Checklist

A debugging checklist is valuable because incidents make people skip steps. The goal is not to turn you into a robot; the goal is to protect your attention when several people are waiting for an answer. Use the checklist as a loop: observe, classify, inspect the right evidence source, form a hypothesis, and only then change something.

```ascii
FIRST-RESPONSE CHECKLIST

┌───────────────────────┐
│ 1. Confirm Context     │  Correct cluster, namespace, workload, time window
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 2. Scope Impact        │  One pod, many pods, one node, all namespaces
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 3. Classify Failure    │  Scheduling, image, runtime, readiness, node
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 4. Inspect Evidence    │  Describe, logs, previous logs, events, nodes
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 5. Choose Action       │  Roll back, fix config, scale, adjust resources
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 6. Verify Recovery     │  Rollout status, readiness, events, endpoints
└───────────────────────┘
```

Start every session by confirming context because debugging the wrong namespace wastes time and can cause accidental changes. `kubectl config current-context` and `kubectl get pods -A` are simple guardrails. In a shared cluster, two namespaces can contain similarly named workloads, and the wrong-context mistake is common enough that senior engineers still check it.

```bash
kubectl config current-context
kubectl get pods -A -o wide
```

After scope and classification, choose the narrowest evidence command. Use `describe` for scheduling, image pull, probe, volume, and kubelet lifecycle messages. Use `logs -p` for previous crashed containers. Use node commands when many unrelated pods fail on the same node or when pod status is `Unknown`. Use rollout commands when old and new ReplicaSets behave differently.

```bash
kubectl rollout status deployment/<deployment-name> -n <namespace>
kubectl get rs -n <namespace>
kubectl describe node <node-name>
```

Verification matters because a "fix" that changes status for one pod may not restore the whole workload. For Deployments, verify the rollout status, pod readiness, restart counts, and endpoints for Services. For scheduling fixes, verify that the pod receives a node and then proceeds to image pull and container start. For probe fixes, verify that the pod becomes Ready and that the Service endpoint list includes it.

---

## Did You Know?

1. **Events are temporary evidence**: many clusters retain events for a limited time, so fresh incident data can disappear before a later review. Production teams usually pair events with centralized logs and metrics because the built-in event stream is a short-term debugging tool.

2. **`Running` is not the same as `Ready`**: a container process can be alive while readiness is false, and Services should avoid routing traffic to that pod. This distinction explains many "the pod is running but users still fail" scenarios.

3. **Previous logs are often more useful than current logs**: in a crash loop, the current container may be waiting, starting, or not yet at the failure point. `kubectl logs -p` asks for the logs from the last terminated instance, which often contains the actual error.

4. **Exit code `137` usually points to a forced kill**: it commonly appears when a container is OOMKilled, although you should verify the `reason` field rather than relying on the number alone. The combination of exit code, reason, and memory limit tells a stronger story than any single field.

---

## Common Mistakes

| Mistake | Why It Is Wrong | What to Do Instead |
|---|---|---|
| Deleting a failing pod before inspection | The replacement may hide previous logs, timing, and events while reproducing the same failure. | Read `describe`, previous logs, and events first, then restart only if the evidence supports it. |
| Treating `Running` as healthy | A pod can run while readiness is false, so Service traffic may still be blocked. | Compare `READY`, conditions, probe events, and Service endpoints before declaring recovery. |
| Reading application logs for an unscheduled pod | No container has run yet, so logs cannot explain a scheduler rejection. | Read pod events and scheduling constraints with `kubectl describe pod`. |
| Ignoring namespace and context | Similar workload names in different namespaces can lead to wrong conclusions or unsafe changes. | Confirm `kubectl config current-context` and use `-n <namespace>` deliberately. |
| Fixing the live pod instead of the controller template | A controller will recreate pods from the old template, so direct pod edits do not persist. | Change the Deployment, StatefulSet, Job, or source manifest that owns the pod. |
| Increasing memory limits without checking behavior | A larger limit may postpone a memory leak rather than solve it. | Compare limits with expected usage, inspect app memory behavior, and tune runtime settings when needed. |
| Assuming all replica failures are node failures | Identical failure across replicas often points to shared configuration, image, or dependency issues. | Compare node placement, then inspect shared pod template and previous logs. |
| Skipping verification after a change | One pod may recover while rollout, readiness, or endpoints remain unhealthy. | Verify rollout status, pod readiness, restart counts, events, and Service endpoints. |

---

## Quiz

1. **Your team deploys a new API version, and all new pods show `CrashLoopBackOff` while the old pods remain Ready. What evidence should you collect first, and what kind of root cause are you testing?**

   <details>
   <summary>Answer</summary>

   Start with `kubectl logs <new-pod> -n <namespace> -p` because the container has already run and crashed. Then use `kubectl describe pod <new-pod> -n <namespace>` to confirm last state, exit code, environment references, probes, and events. Because every new replica fails while old replicas work, you are testing a shared new-template problem such as image behavior, command or args, configuration, Secret or ConfigMap references, or a dependency required during startup.

   </details>

2. **A pod has been `Pending` for several minutes, has no node assigned, and `kubectl logs` returns an error because the container is not available. What should you check next, and why?**

   <details>
   <summary>Answer</summary>

   Run `kubectl describe pod <pod> -n <namespace>` and read the Events section. A pod with no node assigned has not reached the point where application logs can exist, so the scheduler's event messages are the primary evidence. The likely causes include insufficient CPU or memory, untolerated taints, unmatched affinity or node selectors, topology constraints, or an unbound PersistentVolumeClaim.

   </details>

3. **A Service receives no traffic for a new pod even though `kubectl get pods` shows the pod as `Running` with zero restarts. The `READY` column says `0/1`. How do you debug without being misled by the `Running` phase?**

   <details>
   <summary>Answer</summary>

   Treat this as a readiness problem until evidence says otherwise. Use `kubectl describe pod <pod> -n <namespace>` to inspect conditions and probe events, then check whether readiness is failing because of the wrong path, port, scheme, startup delay, timeout, or dependency. You can also inspect `kubectl get endpoints <service> -n <namespace>` to verify whether the pod is excluded from Service routing.

   </details>

4. **A container repeatedly terminates with reason `OOMKilled`, and the team proposes a rollout restart. Why is that unlikely to be a complete fix, and what should you evaluate instead?**

   <details>
   <summary>Answer</summary>

   A rollout restart starts the same process under the same memory limit, so it usually reproduces the same kill after memory usage grows again. You should inspect the pod's memory limit in `kubectl describe pod`, compare it with expected application memory needs, and evaluate whether the limit is too low, the application leaks memory, the runtime heap is misconfigured, or the workload is loading too much data. A limit increase can be a mitigation, but it should match evidence rather than guesswork.

   </details>

5. **An image reference looks correct in the manifest, but the pod shows `ImagePullBackOff`. Your teammate wants to exec into the pod to test registry access. What is wrong with that plan, and what should you do instead?**

   <details>
   <summary>Answer</summary>

   You cannot exec into a container that has not been created, and an image pull failure means the application process never started. Use `kubectl describe pod <pod> -n <namespace>` and read the kubelet event messages for the exact pull failure. The message should point toward a missing tag, registry authentication failure, permission problem, DNS or network timeout, or incorrect registry path.

   </details>

6. **Three unrelated workloads become unhealthy at about the same time, and all affected pods are on `worker-b`. Pods for the same Deployments on other nodes remain healthy. How should you widen the investigation?**

   <details>
   <summary>Answer</summary>

   This pattern suggests a node-scoped problem rather than three independent application bugs. Use `kubectl get pods -A -o wide` to confirm placement, then inspect `kubectl describe node worker-b` for conditions such as memory pressure, disk pressure, PID pressure, network unavailable, taints, and recent node events. You should still preserve pod-level evidence, but the shared node is the strongest clue.

   </details>

7. **A rollout is stuck with two old pods Ready and one new pod Pending. The product owner asks whether users are down. What do you check, and how do you explain the risk?**

   <details>
   <summary>Answer</summary>

   Check `kubectl rollout status deployment/<name> -n <namespace>`, `kubectl get pods -n <namespace> -o wide`, and `kubectl describe pod <pending-new-pod> -n <namespace>`. If the old pods remain Ready and selected by the Service, users may still be served, but the rollout is blocked and capacity or redundancy may be reduced. The Pending pod's events will explain whether resources, taints, affinity, or volumes prevent the new version from scheduling.

   </details>

---

## Hands-On Exercise

In this exercise you will create three small failure scenarios in a practice namespace, classify each failure, and collect the correct evidence before cleanup. Use a disposable local or lab cluster, not a production cluster. The commands use `kubectl` explicitly; if you prefer the `k` alias, define it yourself with `alias k=kubectl` before starting.

### Step 1: Create an isolated namespace

Create a namespace so the exercise resources are easy to find and remove. This keeps the practice failures away from other workloads and gives you a clean event timeline.

```bash
kubectl create namespace kcna-debug
kubectl get namespace kcna-debug
```

- [ ] The namespace `kcna-debug` exists and is visible in `kubectl get namespace`.
- [ ] You can run commands with `-n kcna-debug` without changing your default namespace.

### Step 2: Create an image pull failure

Apply a pod that references an image tag that should not exist. The goal is to prove that image pull failures are diagnosed from events, not application logs.

```bash
kubectl apply -n kcna-debug -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: bad-image
spec:
  restartPolicy: Never
  containers:
    - name: app
      image: nginx:no-such-kcna-debug-tag
      ports:
        - containerPort: 80
EOF
```

Wait briefly, then inspect status and events.

```bash
kubectl get pod bad-image -n kcna-debug
kubectl describe pod bad-image -n kcna-debug
kubectl logs bad-image -n kcna-debug
```

- [ ] The pod shows `ErrImagePull` or `ImagePullBackOff` after the kubelet attempts the pull.
- [ ] The `describe` output contains an event explaining the image pull failure.
- [ ] You can explain why `kubectl logs` is not the right evidence source for this scenario.

### Step 3: Create a crash loop failure

Apply a pod whose container starts, prints a message, and exits with a non-zero code. The goal is to use previous logs and last state to explain a runtime failure.

```bash
kubectl apply -n kcna-debug -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: crash-demo
spec:
  containers:
    - name: app
      image: busybox:1.36
      command:
        - /bin/sh
        - -c
        - echo "starting demo"; echo "missing required setting"; exit 1
EOF
```

Watch it restart, then read both pod state and previous logs.

```bash
kubectl get pod crash-demo -n kcna-debug
kubectl logs crash-demo -n kcna-debug -p
kubectl describe pod crash-demo -n kcna-debug
```

- [ ] The pod reaches `CrashLoopBackOff` or shows repeated restarts after several moments.
- [ ] `kubectl logs -p` shows the message from the previous failed container instance.
- [ ] `kubectl describe pod` shows a terminated last state or restart evidence that matches the log output.

### Step 4: Create a scheduling failure

Apply a pod with an intentionally unrealistic memory request. The goal is to diagnose an unscheduled pod from scheduler events.

```bash
kubectl apply -n kcna-debug -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: too-large
spec:
  containers:
    - name: app
      image: busybox:1.36
      command:
        - /bin/sh
        - -c
        - sleep 3600
      resources:
        requests:
          memory: "1000Gi"
          cpu: "1"
EOF
```

Inspect placement and scheduler messages.

```bash
kubectl get pod too-large -n kcna-debug -o wide
kubectl describe pod too-large -n kcna-debug
```

- [ ] The pod remains `Pending` and has no assigned node in `kubectl get pod -o wide`.
- [ ] The Events section explains why the scheduler could not place the pod.
- [ ] You can state why restarting this pod would not solve the scheduling failure.

### Step 5: Build a one-page triage note

Write a short note for each failed pod using the same structure: visible symptom, first useful evidence, likely owner, and next safe action. The note can be in your editor, a terminal scratch file, or a team incident template; the important part is the reasoning, not the format.

```text
Pod:
Visible symptom:
First useful evidence:
Likely owner:
Next safe action:
```

- [ ] `bad-image` is classified as an image pull failure with kubelet events as the first useful evidence.
- [ ] `crash-demo` is classified as a runtime crash with previous logs as the first useful evidence.
- [ ] `too-large` is classified as a scheduling failure with scheduler events as the first useful evidence.
- [ ] Each next action preserves evidence and targets the likely root cause instead of randomly restarting resources.

### Step 6: Clean up the practice namespace

Remove the namespace after you finish so the intentionally broken resources do not keep generating events or restarts.

```bash
kubectl delete namespace kcna-debug
```

- [ ] `kubectl get namespace kcna-debug` no longer shows the namespace after deletion completes.
- [ ] You can explain the three different failure classes without looking up the commands.

---

## Next Module

Continue to [Part 2: Container Orchestration - Module 2.1: Scheduling](/k8s/kcna/part2-container-orchestration/module-2.1-scheduling/) to learn how Kubernetes decides where to place your pods.

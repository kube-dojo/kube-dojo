---
revision_pending: false
title: "Module 3.3: Debugging in Kubernetes"
slug: k8s/ckad/part3-observability/module-3.3-debugging
sidebar:
  order: 3
lab:
  id: ckad-3.3-debugging
  url: https://killercoda.com/kubedojo/scenario/ckad-3.3-debugging
  duration: "45 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical exam skill requiring systematic approach
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: [Module 3.1 (Probes)](../module-3.1-probes/), [Module 3.2 (Logging)](../module-3.2-logging/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Diagnose** pod failures using status, events, logs, and describe output.
- **Debug** CrashLoopBackOff, ImagePullBackOff, Pending, and NotReady pod states under time pressure.
- **Troubleshoot** service and pod networking with endpoints, DNS checks, exec, and ephemeral debug containers.
- **Implement** a repeatable debugging workflow that moves from broad symptoms to specific evidence.

## Why This Module Matters

Hypothetical scenario: you are fifteen minutes into a CKAD task, the Deployment object exists, and the Service has a ClusterIP, but the grader still cannot reach the application. A random approach feels tempting because every command reveals a new detail, yet the fastest path is not more commands; it is a better order for using them. Kubernetes already records the evidence you need in status fields, conditions, events, logs, and object relationships, so your job is to read that evidence before editing anything.

Debugging Kubernetes is different from debugging a single process on your laptop because the failure may sit in several layers at once. A container can crash because the application is wrong, a pod can remain Pending because the scheduler cannot place it, a Service can be healthy while selecting no endpoints, and a readiness probe can remove every backend from traffic even though the containers are still Running. Kubernetes 1.35+ gives you strong inspection tools, but those tools reward sequence and punish guessing.

This module turns the old "try a few commands and hope" habit into an evidence ladder you can run under exam pressure. You will start with status, move into events and container state, read current and previous logs, enter containers only when that evidence says it is useful, add ephemeral debug containers when the application image lacks tools, and finish by tracing a Service from selector to endpoint to DNS. The goal is not to memorize a command list; the goal is to decide which observation changes your next move.

The practical benefit is that you learn to separate causes that look similar in the first screen of output. A pod that never scheduled, a pod that cannot pull its image, and a pod that exits immediately can all appear as a failed workload to the application owner, but each failure belongs to a different Kubernetes actor. The scheduler, kubelet, container runtime, probe manager, and Service controller leave different fingerprints, and reading the right fingerprint is the difference between a surgical edit and a long detour.

## Build a Debugging Map Before You Touch the Pod

The first debugging mistake is treating every symptom as equally important. Kubernetes exposes a noisy surface area, and a broken pod can produce status text, warning events, container state, probe failures, log output, scheduler messages, and network symptoms at the same time. A useful workflow narrows the search space from outside to inside: object status tells you the visible symptom, `describe` tells you what Kubernetes tried to do, logs tell you what the process reported, and `exec` or `debug` lets you inspect the runtime environment when the earlier evidence points there.

Use the workflow as a map, not as a rigid ritual. If a pod is Pending, logs will not help because no container has started, so `describe` and scheduler events matter first. If a pod is CrashLoopBackOff, current logs may show only the newest restart, so previous logs and last termination state become the useful evidence. If a Service has no endpoints, entering the application container is usually premature because the selector, readiness, or port mapping can explain the outage before you test a socket.

The map also protects you from mixing object levels. A Deployment owns a ReplicaSet, the ReplicaSet owns pods, and a Service selects pods by labels rather than by owner reference. Editing the wrong level can appear to work for one pod while leaving the controller ready to recreate the same bug. When the evidence says the template is wrong, fix the Deployment template; when the evidence says one pod is stuck because of its current state, inspect that pod directly before deciding whether the owner needs a patch.

```text
+-----------------------------------------------------------+
|              Systematic Debugging Workflow                |
+-----------------------------------------------------------+
|                                                           |
|  1. GET STATUS                                            |
|     kubectl get pod POD -o wide                           |
|     -> What state? Ready? Restarts? Node?                 |
|                                                           |
|  2. DESCRIBE                                              |
|     kubectl describe pod POD                              |
|     -> Events? Conditions? Container status?              |
|                                                           |
|  3. LOGS                                                  |
|     kubectl logs POD [--previous]                         |
|     -> What did the app say? Errors?                      |
|                                                           |
|  4. EXEC                                                  |
|     kubectl exec -it POD -- sh                            |
|     -> What's inside? Files? Processes? Network?          |
|                                                           |
|  5. EVENTS                                                |
|     kubectl get events --sort-by='.lastTimestamp'         |
|     -> What happened cluster-wide?                        |
|                                                           |
+-----------------------------------------------------------+
```

Start with a status command because it tells you which branch of the decision tree you are on. The `READY` column separates a process that is running from a pod that is actually eligible for Service traffic, `RESTARTS` separates a stable failure from a crash loop, and `NODE` tells you whether scheduling already happened. The wide view matters because a node name, pod IP, or missing pod IP can tell you whether to think about scheduling, runtime, or networking.

Read the namespace and selector context at the same time, especially during CKAD tasks where several objects may share similar names. A status line from the wrong namespace can send you into a false investigation, and a pod selected by a different label can make a Service look broken even when the workload you inspected is fine. The habit is simple: confirm the object name, namespace, owner, readiness, restart count, node, and pod IP before you treat the rest of the output as evidence.

```bash
# Pod status overview
kubectl get pod POD -o wide

# All pods in namespace
kubectl get pods

# Watch for changes
kubectl get pods -w
```

`kubectl describe` is the best second move because it joins several pieces of evidence in one view. It shows pod conditions, each container state, restart counts, image names, mounted volumes, probes, node assignment, and the Events section at the bottom. Events are especially valuable because they are produced by Kubernetes components such as the scheduler, kubelet, and image puller, so they often explain failures that never reach application logs.

The container status block deserves careful reading because it contains current state and last state side by side. `Waiting` with a reason such as `ImagePullBackOff` means the process did not start, `Running` with `Ready: False` points toward probes or application readiness, and `Terminated` or Last State explains how the previous attempt ended. This is the Kubernetes version of a medical chart: the current symptom matters, but the previous state often explains how the patient got there.

```bash
# Full pod details
kubectl describe pod POD

# Key sections to check:
# - Status/Conditions
# - Containers (State, Ready, Restart Count)
# - Events (bottom of output)
```

Logs are most useful after you know a container actually started. A running container has current logs, while a restarted container also has a previous instance whose output is often the only place the fatal error appears. When you debug multi-container pods, always name the container; otherwise you can accidentally read the sidecar and miss the application container that is failing.

Log output should be treated as application testimony rather than as a complete source of truth. The process may report a missing file, but Kubernetes tells you whether the volume was mounted; the process may report a port bind failure, but the pod spec tells you which command and environment variables were supplied. Strong debugging combines the two views, using logs to reveal the application complaint and `describe` to verify whether the platform delivered the inputs the application expected.

On kind and other containerd-backed clusters, `kubectl logs --previous` can return `unable to retrieve container logs` during very fast crash loops because the terminated instance has not been retained yet. When that happens, read Last State and terminationMessage from `kubectl describe pod` instead, and wait for one more restart cycle if the evidence is still empty.

```bash
# Current logs
kubectl logs POD

# Previous instance (after crash)
kubectl logs POD --previous
# Fallback when --previous is empty (fast crash loops on kind/containerd):
kubectl describe pod POD | grep -A5 "Last State"

# Specific container
kubectl logs POD -c CONTAINER

# Stream logs
kubectl logs -f POD
```

`exec` is powerful, but it is not a first move for every problem. It tells you what is true inside the container filesystem, process table, resolver configuration, and network namespace, which makes it ideal for checking a mounted config file, a listening port, or an in-cluster DNS lookup. It does not explain why the scheduler refused placement or why an image could not be pulled, so use it only after status and events say the container is alive enough to enter.

```bash
# Interactive shell
kubectl exec -it POD -- sh
kubectl exec -it POD -- /bin/bash

# Run single command
kubectl exec POD -- ls /app
kubectl exec POD -- cat /etc/config

# Specific container
kubectl exec -it POD -c CONTAINER -- sh
```

Events complete the broad view because they can reveal namespace-wide churn, not just one object's description. Sorting by timestamp helps you see the order in which the scheduler, kubelet, controllers, and image puller acted. Pause and predict: before running the sorted events command during a failure, what event would you expect to see for a bad image tag, and what event would you expect for a pod that requests too much CPU?

Events are not permanent audit logs, so collect them while the failure is fresh. Kubernetes keeps a bounded event history, and repeated failures can compress or replace older messages. In an exam environment this usually matters less than in production, but the habit still helps: when a symptom appears, capture the event reason, message, and involved object before deleting or replacing the pod. Once the object is gone, the most useful clue may be harder to recover.

```bash
# Namespace events (sorted by time)
kubectl get events --sort-by='.lastTimestamp'

# Filter by type
kubectl get events --field-selector type=Warning

# Events for specific pod
kubectl get events --field-selector involvedObject.name=POD
```

The workflow becomes fast once you stop reading every line with equal attention. For a CKAD task, your first pass through status and describe should answer three questions: did scheduling happen, did the image start, and did the process stay alive long enough to become Ready? Those questions place the problem in a layer, and each later command should either confirm that layer or move you one layer inward.

## Decode Pod States and Container Exit Evidence

Kubernetes status words are compact summaries of different controllers and node agents doing work. `Pending` usually points to scheduling, volume binding, or image preparation before the main process exists. `ImagePullBackOff` points at the kubelet trying and failing to fetch an image. `CrashLoopBackOff` means the process started and then exited repeatedly, while `Running` but not Ready means the container is alive but traffic eligibility failed. Treat those words as routing labels for your investigation.

The routing label is only the first clue, not the full diagnosis. `Pending` can mean unschedulable resources, but it can also mean a volume claim is waiting or a runtime sandbox is not ready. `CrashLoopBackOff` can mean a bad command, but it can also mean a liveness probe killed a slow starter. Your job is to use the state word to choose the next evidence source, then let the detailed event or container state name the exact fix.

### Pending

A pod stuck in Pending is often not an application bug. The scheduler may be unable to find a node with enough resources, a node selector or affinity rule may exclude every node, a taint may require a toleration, or a PersistentVolumeClaim may not be bound yet. Logs are unavailable in this state because there is no running container process, so the useful evidence is pod description, scheduler events, node labels, node capacity, and storage binding state.

Pending also teaches an important ownership lesson: you usually fix the declaration that made placement impossible, not the node by hand. If a training pod asks for a huge amount of memory, the correct exam move is to reduce the request to a realistic value, not to drain nodes or chase unrelated workloads. If a selector asks for a label no node has, either correct the selector or add the intended label, depending on what the task asks you to achieve.

```bash
# Check why
kubectl describe pod POD

# Common causes:
# 1. Insufficient resources
#    -> Check node resources: kubectl describe node
#    -> Reduce pod resource requests

# 2. No matching node (nodeSelector/affinity)
#    -> Check node labels: kubectl get nodes --show-labels
#    -> Fix selector or label nodes

# 3. PVC not bound
#    -> Check PVC: kubectl get pvc
#    -> Create matching PV
```

Pause and predict: a pod is stuck in `Pending`, and `kubectl describe pod` shows `0/3 nodes are available: 3 Insufficient cpu.` That is not fixed by restarting the pod because the scheduler will make the same decision again. Your choices are to lower the request, free capacity, add capacity, or change placement rules, and the right exam fix is usually the smallest manifest change that lets the scheduler place the pod.

### ImagePullBackOff / ErrImagePull

Image pull failures happen before the application starts, so the image reference and registry authentication path matter more than the container command. The event text usually names the image, the registry response, and whether the problem is a missing tag, unauthorized access, or a registry lookup failure. `ErrImagePull` is the immediate failure, and `ImagePullBackOff` is the backoff state Kubernetes enters after retrying, so both states should send you to the Events section first.

Backoff is a retry behavior, not a separate root cause. The kubelet waits longer between pull attempts so the node does not hammer the registry forever, but the important message is usually the first clear pull error. In CKAD tasks, the image fix is often a manifest edit with a correct tag or repository. In real clusters, the same pattern may require checking registry credentials, pull secret references, network egress, or whether an admission controller rewrote the image.

```bash
# Check events
kubectl describe pod POD | grep -A5 Events

# Common causes:
# 1. Wrong image name/tag
#    -> Fix image in pod spec

# 2. Private registry without credentials
#    -> Create imagePullSecret

# 3. Image doesn't exist
#    -> Verify image exists in registry
```

The key is to avoid editing unrelated objects when the registry error already explains the failure. If the event says the manifest is unknown, changing Service selectors cannot help. If the event says authentication is required, changing the tag cannot help unless the tag also points to a public image. The fastest path is to read the exact registry message, then edit only the image reference or image pull credentials that the message names.

### CrashLoopBackOff

CrashLoopBackOff means the container has already started at least once, so the evidence splits between application output and Kubernetes termination state. Current logs may be misleading because they come from the newest container attempt, which might not have reached the failing code path yet. Previous logs, last state, termination reason, exit code, and probe events form the core evidence set for this state.

Separate process exits from probe-driven restarts before you change application code. A command that exits immediately with status 0 may be wrong for a server because Kubernetes expected a long-running process, while a process killed by a liveness probe may be healthy enough but too slow for the probe configuration. Those two failures can both restart repeatedly, yet one is fixed by command or args and the other by probe path, port, threshold, or startup timing.

```bash
# Check logs from crashed instance
kubectl logs POD --previous
# Fallback when --previous is empty (fast crash loops):
kubectl describe pod POD | grep -A5 "Last State"

# Check exit code and termination message
kubectl describe pod POD | grep -A5 "Last State"

# Common causes:
# 1. Application error (check logs)
# 2. Missing config/secrets
# 3. Wrong command/args
# 4. Liveness probe killing healthy app
```

Stop and think: a pod shows `CrashLoopBackOff` with exit code 137. That value commonly means the process received SIGKILL, and in Kubernetes it often appears with an OOMKilled reason when the container exceeds its memory limit. Before changing the command, inspect the Last State reason, resource limits, and recent memory behavior, because a perfectly correct application can crash when the limit is too low for its startup workload.

### Running but Not Ready

A pod can be `Running` and still be absent from Service endpoints. Readiness is a traffic contract, not a process-liveness contract, so a failing readiness probe can keep a healthy-looking process out of load balancing. This is one of the most common exam traps because `kubectl get pods` may show the phase as Running, while the `READY` column, probe events, and endpoints reveal that the application is not serving traffic.

Readiness should be debugged from both sides of the contract. From the pod side, check whether the probe path, port, scheme, and initial timing match what the application actually serves. From the Service side, check whether endpoint membership changes after readiness becomes true. If the pod becomes Ready but traffic still fails, then you have moved past readiness and should inspect selector, targetPort, NetworkPolicy, or the application listener.

```bash
# Check readiness probe
kubectl describe pod POD | grep -A5 Readiness

# Check endpoints
kubectl get endpoints SERVICE

# Common causes:
# 1. Wrong readiness probe path/port
# 2. App not fully started
# 3. Dependency not available
```

Before running a network test, decide what result would prove the layer you suspect. If endpoints are empty while pods are Running but not Ready, a failed readiness probe is more likely than DNS. If endpoints contain pod IPs but traffic still fails, then DNS, NetworkPolicy, targetPort, or application listening behavior becomes more plausible. This prediction habit saves time because each command has a job instead of becoming another random sample.

## Debug From Inside the Network Namespace

Once Kubernetes says the pod exists and the container is running, the next question is whether the runtime environment matches the manifest and the application's assumptions. Inside-container debugging can verify mounted files, command arguments, environment variables, listening sockets, DNS resolver configuration, and outbound connectivity. The tradeoff is that application images are often minimal, so the tools you expect may not exist, and entering a production container can tempt you to make manual changes that disappear on restart.

Container inspection is strongest when you already have a hypothesis. "Is the ConfigMap mounted at `/etc/config`?" is a good `exec` question because a single `ls` or `cat` can answer it. "Why is the app broken?" is too broad because it encourages wandering through the filesystem. Before you open a shell, name the exact condition you expect to confirm or disprove, then close the shell once you have that answer.

### Basic Commands

Use `exec` for observation, not configuration drift. A shell lets you inspect files and network behavior, but changes made by hand inside a container are not a durable fix because controllers recreate pods from manifests. In CKAD work, treat `exec` as a way to prove whether a config file mounted, a port listened, or DNS resolved before you patch the declarative object that owns the behavior.

```bash
# Get shell
kubectl exec -it POD -- sh

# Check processes
kubectl exec POD -- ps aux

# Check network (busybox has netstat, not ss)
kubectl exec POD -- netstat -tlnp
# ss -tlnp requires a full image (netshoot/debian); busybox → use netstat

# Check DNS (prefer FQDN — see note below)
kubectl exec POD -- nslookup kubernetes.default.svc.cluster.local
kubectl exec POD -- cat /etc/resolv.conf

# Check connectivity
kubectl exec POD -- wget -qO- http://service:port
kubectl exec POD -- curl -s http://service:port

# Check files
kubectl exec POD -- ls -la /app
kubectl exec POD -- cat /etc/config/file
```

These commands deliberately test different classes of assumptions. Process commands tell you whether the expected process is alive, socket commands tell you whether anything is listening, DNS commands tell you whether the pod resolver can translate service names, and file commands tell you whether volumes and projected configuration appeared where the application expects them. If a command is missing, that is evidence about the image, not a reason to abandon the investigation.

> **Note:** Busybox `nslookup` does not expand the `search` path in `/etc/resolv.conf` the way glibc or netshoot does, so short-name lookups often return `NXDOMAIN` on Kubernetes 1.35 even when cluster DNS is healthy — and the command may exit non-zero even when it printed a useful `Address:` line. Prefer FQDNs such as `SERVICE.NAMESPACE.svc.cluster.local` (for example `kubernetes.default.svc.cluster.local`), or use netshoot `dig` when you need short-name resolution behavior.

### When Shell Isn't Available

Distroless and scratch-style images often omit shells and network tools to reduce attack surface and image size. That design is good for production, but it changes how you debug because `kubectl exec POD -- sh` can fail even when the container is perfectly healthy. In Kubernetes 1.35+ clusters, ephemeral debug containers are the preferred way to bring a toolbox to the pod's namespaces without rebuilding or restarting the application image.

This is also why "just install curl in the image" is not always the right lesson. Production images should be shaped by runtime and security needs, while debugging images can be shaped by diagnostic needs. Kubernetes lets you keep those concerns separate. When a minimal image blocks ordinary `exec`, preserve the minimal production image and attach the tools temporarily through `kubectl debug` or a purpose-built diagnostic pod.

```bash
# Check if shell exists
kubectl exec POD -- /bin/sh -c 'echo works'

# If no shell, use debug container (Kubernetes 1.25+)
kubectl debug POD -it --image=busybox --target=container-name
```

Pause and predict: you need to test network connectivity from inside a distroless container that has no shell, no `curl`, and no `wget`. The right answer is not to rebuild the production image during an exam task. Add a temporary debug container or create a debug copy, then run the network tools from that toolbox while keeping the original application container unchanged.

## Ephemeral Debug Containers

Ephemeral containers are a Kubernetes debugging feature for pods that are already running. They are not regular application containers, they are not restarted by the kubelet like workload containers, and they are not appropriate for serving traffic. Their value is namespace access: a debug container can share the pod's network namespace, and with the right target it can help inspect the environment around a minimal application image.

Because ephemeral containers alter a live pod's debug state, use them with the same discipline as any other operational action. Check whether your role is allowed to create ephemeral containers, choose the smallest toolbox that answers the question, and avoid commands that write into shared volumes unless the exercise explicitly asks for that. The debugging container should leave behind evidence and understanding, not a hidden manual repair.

```bash
# Add debug container to running pod
kubectl debug POD -it --image=busybox --target=container-name

# Debug with specific image
kubectl debug POD -it --image=nicolaka/netshoot

# Copy pod for debugging (doesn't affect original)
kubectl debug POD -it --copy-to=debug-pod --container=debug --image=busybox
```

Choose the debug image based on the evidence you need. BusyBox is small and useful for basic shell, file, and DNS checks, while a network-focused image such as `nicolaka/netshoot` provides richer tools for service and DNS diagnosis. A copied pod is safer when you want to change command arguments or explore a modified environment, because the original pod keeps serving while the debug copy absorbs the experiment.

### Debug Container Use Cases

The following commands preserve the original module's debugging situations: network checks when the app lacks curl, filesystem inspection when you need to verify mounts, and process inspection when the namespace arrangement allows it. Do not assume every cluster grants the same debug permissions, because ephemeral containers still depend on admission policy, security context, and RBAC. When debug is blocked, fall back to a temporary diagnostic pod in the same namespace and test Service DNS or connectivity from there.

```bash
# Network debugging (no curl in original container)
kubectl debug POD -it --image=nicolaka/netshoot --target=app
# Then: curl, dig, nslookup, tcpdump

# File system inspection
kubectl debug POD -it --image=busybox --target=app
# Then: ls, cat, find

# Process debugging (--target shares the target container's process namespace)
kubectl debug POD -it --image=busybox --target=app
# Then: ps aux

# Copy-based alternative (--share-processes requires --copy-to)
kubectl debug POD --copy-to=debug-copy --share-processes --set-image='*=busybox' -- sleep 3600
# Then: kubectl exec debug-copy -- ps aux
```

The `--target` flag attaches the debug container to an existing container and shares that target's process namespace, which is why `ps aux` can see application processes. The `--share-processes` flag applies only with `--copy-to`; it is a no-op on a plain `--target` debug attach. Ephemeral debug containers are powerful precisely because they reduce pressure to mutate the broken workload. Instead of adding tools to the production image, you temporarily place tools beside it. Instead of restarting a pod that is still serving partial traffic, you inspect from the same network context. That separation matters in exams and in real clusters because observation should not create more drift than the original failure.

## Trace Services from Selector to Endpoint to DNS

Service debugging is a relationship problem before it is a packet problem. A Service selects pods by label, Kubernetes publishes ready selected pods as endpoints or EndpointSlices, DNS gives the Service a stable name, and kube-proxy or the cluster dataplane routes traffic toward those backends. If any relationship is broken, a simple "connection refused" or timeout may hide a selector mismatch, a failed readiness probe, a wrong targetPort, or a network policy boundary.

Think of the Service path as a contract with four clauses. The selector clause says which pods are eligible, the readiness clause says which selected pods can receive traffic, the port clause says how Service port maps to container targetPort, and the client clause says where the request originates. A failure in any clause can produce a similar user symptom, so the disciplined route is to validate each clause in order rather than jumping straight to packet-level tooling.

### Check Service-to-Pod Connection

Always compare the Service selector with the actual pod labels before assuming the network is broken. A Service with no endpoints usually means it selects no Ready pods, and the two most common reasons are a label mismatch or a readiness failure. EndpointSlice is the modern scalable API, but `kubectl get endpoints` remains a concise exam-friendly check for whether the Service has usable backends.

```bash
# Verify service exists
kubectl get svc SERVICE

# Check endpoints (should list pod IPs)
kubectl get endpoints SERVICE
# On Kubernetes 1.35+, kubectl may warn that EndpointSlice is preferred; the address list is still valid.

# If no endpoints:
# - Check pod labels match service selector
# - Check pod readiness
kubectl get pods --show-labels
kubectl describe svc SERVICE | grep Selector
```

If endpoints exist, the problem moves down the path. The Service may target a port where the container is not listening, DNS may be queried from the wrong namespace, a NetworkPolicy may block traffic, or the application may return an error even though routing succeeds. The important distinction is that empty endpoints and failing connections require different fixes, so check endpoint membership before launching deeper packet tests.

### Test Service DNS

DNS tests are useful only after you know what name the client should resolve. A short Service name resolves inside the same namespace, while a cross-namespace client needs either `SERVICE.NAMESPACE` or the full cluster DNS name. If the DNS lookup succeeds but HTTP fails, DNS is no longer your primary suspect; move to targetPort, application listener, NetworkPolicy, or readiness behavior.

Name scope is a frequent source of false negatives. A debugging pod in a different namespace may fail to resolve the short name even though the real client in the Service namespace would succeed. Conversely, a full cluster DNS name can resolve from a diagnostic pod while the original client still fails because policy or port mapping differs. Match the test location to the failing client whenever the task gives you that context.

```bash
# From inside a pod (prefer FQDN — busybox nslookup ignores search domains)
kubectl exec POD -- nslookup SERVICE.NAMESPACE.svc.cluster.local

# Create test pod for debugging
kubectl run test --image=busybox --rm -it -- nslookup SERVICE.NAMESPACE.svc.cluster.local
```

### Test Service Connectivity

Connectivity tests should run from the same side of the boundary as the failing client. Testing from your laptop to a ClusterIP is not the same as testing from a pod inside the namespace, and testing from a privileged diagnostics namespace may bypass policies that affect the real client. During an exam, a short-lived BusyBox pod is often enough to prove whether the Service name and port work from inside the cluster.

```bash
# From inside a pod
kubectl exec POD -- wget -qO- http://SERVICE:PORT
kubectl exec POD -- curl -s http://SERVICE:PORT
```

When a Service test fails, write down which layer passed last. Selector matched but endpoints were empty means readiness or label state. Endpoints existed but DNS failed means resolver or name scope. DNS resolved but HTTP failed means targetPort, listener, policy, or application response. That layered summary keeps you from cycling through the same commands after every patch.

## Work Through Exam-Style Debug Scenarios

Worked examples are useful because they show how the evidence ladder changes with the symptom. The goal is not to memorize these exact object names; it is to learn what each state makes impossible or likely. In each scenario below, notice that the first command names the symptom, the second command asks Kubernetes why it reached that symptom, and only then does the sequence move toward a fix.

As you read each scenario, pay attention to commands that deliberately do not appear. The Pending scenario does not start with logs, the Service scenario does not start with `exec`, and the crash scenario does not start with patching a Service. Those omissions are part of the method. A senior debugger is not someone who knows every command; it is someone who can ignore the commands that cannot answer the current layer of the problem.

### Scenario 1: Pod Won't Start

A pod that will not start might be unscheduled, unable to pull an image, blocked by storage, or rejected by a runtime condition. The first two commands separate those possibilities quickly. If `describe` shows `ErrImagePull`, you should fix the image reference instead of trying logs that cannot exist yet; if it shows insufficient resources, you should fix requests or placement instead of editing the container command.

```bash
# Step 1: Check status
kubectl get pod broken-pod

# Step 2: Describe for events
kubectl describe pod broken-pod

# Step 3: Check if image exists
# If ErrImagePull: fix image name
# If Pending: check resources/node selector

# Step 4: Check logs if container started
kubectl logs broken-pod
```

### Scenario 2: Pod Keeps Crashing

A crash loop has different evidence because the container did start. The restart count tells you the loop is real, previous logs show the output from the failed instance, and Last State gives a termination reason that can distinguish application failure from memory pressure or a signal. If a probe kills the container, the application logs may look normal, so always check liveness events before rewriting application arguments.

```bash
# Step 1: Get restart count
kubectl get pod crashing-pod

# Step 2: Check previous logs
kubectl logs crashing-pod --previous
# Fallback when --previous is empty (fast crash loops):
kubectl describe pod crashing-pod | grep -A5 "Last State"

# Step 3: Check exit code and termination message
kubectl describe pod crashing-pod | grep -A5 "Last State"

# Step 4: Check liveness probe
kubectl describe pod crashing-pod | grep -A5 Liveness
```

### Scenario 3: Service Not Reachable

Service failures are easiest when you treat them as a chain of relationships. The Service object must exist, its selector must match pods, the selected pods must be Ready, endpoints must publish backend addresses, and the client must resolve and connect to the correct port. If the endpoints list is empty, fix selector or readiness first; a packet capture will not repair a Service that selected no backends.

```bash
# Step 1: Check service exists
kubectl get svc myservice

# Step 2: Check endpoints
kubectl get endpoints myservice

# Step 3: If no endpoints, check pod labels
kubectl get pods --show-labels
kubectl describe svc myservice | grep Selector

# Step 4: Test from inside cluster
kubectl run test --image=busybox --rm -i -- wget -qO- http://myservice
```

These scenarios also show why a command cheat sheet is not enough. The same `kubectl describe` command means different things depending on whether you are reading scheduler events, image pull errors, probe failures, or last termination state. The habit you are building is to ask "what layer am I testing now?" before you type the next command, then stop reading once the evidence answers that question.

## Patterns & Anti-Patterns

Pattern: use an evidence ladder that moves from cheap, broad observations to invasive, narrow observations. Status and describe are cheap because they do not enter the container or change the object, logs are narrower because they require a container attempt, and debug containers are more invasive because they add temporary runtime state. This pattern scales because it works the same for a single pod, a Deployment rollout, and a Service outage.

Pattern: compare declared intent with observed state at every layer. The pod spec declares an image, resources, probes, labels, ports, and volume mounts, while status and events report what Kubernetes actually did with those declarations. Debugging becomes much clearer when you phrase the mismatch explicitly: the Service declares selector `app=web`, the pod label is `app=api`; the readiness probe declares path `/healthz`, the container serves `/`; the resource request declares memory the nodes cannot satisfy.

Pattern: create temporary diagnostic context instead of changing production containers by hand. A short-lived test pod, an ephemeral debug container, or a copied debug pod can answer DNS, port, and filesystem questions without baking tools into the workload image. This pattern is especially important for minimal images, where the absence of a shell is expected and should not become a reason to weaken the production image permanently.

Pattern: verify the fix at the same layer where you found the failure. If the evidence was an image pull event, the proof is a successful pull and a pod that starts. If the evidence was an empty endpoint list, the proof is endpoints appearing after the selector or readiness fix. If the evidence was a crash exit code, the proof is a stable restart count and useful readiness. Verification should close the same loop that diagnosis opened.

Anti-pattern: restarting objects before reading events destroys timing clues and rarely changes deterministic failures. Teams fall into this habit because a restart feels active, and sometimes it masks transient issues, but it teaches the wrong reflex for CKAD. The better alternative is to capture status, events, previous logs, and last state first, then restart only when the evidence shows a transient runtime condition or after you have changed the declarative source.

Anti-pattern: using `exec` as a repair mechanism creates drift that the controller will erase. Editing a config file inside a container may make one process look fixed for a moment, but a rescheduled pod will return to the broken manifest. Use `exec` to prove that a file or listener is wrong, then patch the ConfigMap, Secret reference, command, args, probe, Service selector, or Deployment template that actually owns the state.

Anti-pattern: treating Service DNS failure, empty endpoints, and HTTP failure as the same problem wastes time. They sit at different layers, and each layer has different evidence. Resolve the name to test DNS, inspect endpoints to test selector and readiness, and connect to the Service port to test routing and application behavior. Fix the first broken relationship in the chain before moving deeper.

Anti-pattern: copying a command from a previous failure without checking the current pod state makes practice feel productive while weakening judgment. The command may be valid, but validity is not the same as relevance. `kubectl logs --previous` is excellent for a crash loop and useless for a pod that never scheduled. The better alternative is to say the state out loud, choose the evidence source for that state, and only then run the familiar command.

## Decision Framework

Use the pod phase and readiness state to choose your first branch. If the pod is Pending, start with `describe`, scheduler events, resource requests, node labels, taints, tolerations, and volume claims. If the pod is waiting with an image pull state, read the image pull event and compare the image reference, registry, tag, and imagePullSecrets. If the pod is Running but not Ready, read probe configuration, probe events, and endpoints before testing arbitrary network paths.

Use restart count and last termination state to choose your crash-loop branch. A growing restart count sends you to `kubectl logs --previous`, Last State, exit code, termination reason, and liveness probe events. Exit code 1 usually points toward application or command failure, exit code 137 often points toward SIGKILL or memory pressure, and exit code 0 can still be wrong when the container was supposed to be a long-running server.

Use endpoint membership to choose your Service branch. Empty endpoints mean selector, readiness, or endpoint publishing; present endpoints mean DNS scope, targetPort, NetworkPolicy, application listener, or response behavior. Which approach would you choose here and why: patch a Service selector after seeing empty endpoints and mismatched labels, or launch a network toolbox first? The selector patch is the better first move because it fixes the first proven broken relationship.

Use debug containers when the evidence says the runtime namespace matters but the application image lacks tools. They are a good fit for DNS lookups, packet-level checks, process inspection, and filesystem review around minimal images. They are a poor fit for permanent changes, application serving, or replacing a real fix in the manifest. The rule is simple: observe with debug tools, then repair the declarative object.

Use time pressure as a reason to narrow the question, not as a reason to skip the workflow. In a short exam window, the right workflow is smaller, not absent: status to classify, describe to read platform evidence, logs or previous logs when the process started, endpoints when traffic is involved, and one verification command after the patch. That compact loop is faster than a long sequence of unrelated commands because each step earns its place.

## Did You Know?

- **Kubernetes v1.25 marked ephemeral containers stable**, which is why modern Kubernetes 1.35+ clusters can use `kubectl debug` as a normal troubleshooting tool rather than an experimental feature.

- **Exit code 137 is commonly interpreted as 128 plus signal 9**, so it often points toward SIGKILL; in Kubernetes descriptions, pair it with the termination reason to confirm whether OOMKilled is involved.

- **`kubectl logs --previous` reads the terminated container instance**, which is why it is often more useful than current logs during CrashLoopBackOff investigations. When `--previous` is empty on fast crash loops, read Last State from `kubectl describe pod` instead.

- **A Service with zero endpoints can still have a valid ClusterIP**, because endpoint membership is controlled by selector matches and readiness, not by whether the Service object itself exists.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Random guessing | A broken pod exposes many symptoms, so it feels faster to try edits than to classify the layer. | Follow the workflow: status, describe, logs, exec or debug, then events for wider context. |
| Skipping `describe` | Learners assume application logs contain every cause, even when the container never started. | Read conditions, container states, and Events before looking for process output. |
| Not checking `--previous` | CrashLoopBackOff creates a fresh container, so current logs can hide the failed instance. | Use `kubectl logs POD --previous`; if empty, read Last State with `kubectl describe pod POD \| grep -A5 "Last State"`. |
| Ignoring exit codes | The same visible crash loop can come from application exit, OOMKilled, or signal termination. | Read termination reason, exit code, resource limits, and probe events together. |
| Forgetting readiness | Running containers look healthy even when readiness removes every backend from traffic. | Check the `READY` column, readiness events, and Service endpoints. |
| Debugging Service traffic before checking selectors | Network tests feel concrete, but a Service with no endpoints has no backend to route toward. | Compare `kubectl describe svc` selector output with `kubectl get pods --show-labels`. |
| Treating debug containers as a permanent fix | A toolbox image solves observation problems, not workload configuration problems. | Use `kubectl debug` to gather evidence, then patch the owning manifest or controller. |

## Quiz

<details>
<summary>Question 1: Your pod is Pending, and `kubectl describe pod` reports that none of the nodes have enough CPU. What should you diagnose first, and what edit is most likely to help?</summary>

Start with scheduling evidence, not logs, because the container has not started. The scheduler event says the resource request cannot fit on the available nodes, so the first useful checks are pod requests, node allocatable resources, and placement rules such as selectors or affinity. The smallest exam fix is usually to reduce an excessive request or remove an unintended placement constraint. Restarting the pod without changing those declarations will produce the same scheduling decision.

</details>

<details>
<summary>Question 2: A pod named `api-server` is in CrashLoopBackOff. Current logs show only a new startup line, but the restart count is increasing. How do you find the real failure?</summary>

Use `kubectl logs api-server --previous` because the previous container instance is the one that exited. If `--previous` returns no logs during a fast crash loop, fall back to `kubectl describe pod api-server | grep -A5 "Last State"` for termination reason, exit code, and terminationMessage. Then inspect liveness probe events in the same describe output. Current logs can be incomplete during a crash loop because they belong to the newest attempt. The fix depends on what the evidence says: application error, missing config, OOMKilled, wrong command, or an aggressive probe.

</details>

<details>
<summary>Question 3: A newly deployed workload shows ImagePullBackOff, and the developer says the image was pushed recently. What evidence separates a typo from a private-registry credential problem?</summary>

Read the Events section from `kubectl describe pod` because the kubelet records the registry response there. A missing image or tag usually produces a not-found style message that names the reference Kubernetes tried to pull. A private registry problem usually shows an authentication or authorization failure, which points toward `imagePullSecrets` or registry credentials. Do not change Service selectors, probes, or ports until the image can actually be pulled.

</details>

<details>
<summary>Question 4: Users cannot reach an application through a Service. Pods are Running, but `kubectl get endpoints myservice` returns no addresses. What is the most likely root cause?</summary>

The most likely causes are a Service selector that matches no pods or readiness that excludes the selected pods. Compare the Service selector from `kubectl describe svc myservice` with actual pod labels from `kubectl get pods --show-labels`, then check the `READY` column and readiness events. DNS and HTTP tests are later checks because an empty endpoint list means the Service has no backend membership yet. Fix the selector or readiness probe before investigating dataplane routing.

</details>

<details>
<summary>Question 5: You need to troubleshoot service and pod networking from a distroless application container that has no shell or curl. The pod is serving traffic and should not restart. What should you do?</summary>

Use an ephemeral debug container with a toolbox image, or create a debug copy if you need to experiment more freely. `kubectl debug POD -it --image=nicolaka/netshoot --target=container-name` lets you test DNS and connectivity from the pod's network context without rebuilding the application image. The debug container is for observation, not a permanent part of the workload. After you identify the broken relationship, patch the manifest, Service, probe, or policy that owns the problem.

</details>

<details>
<summary>Question 6: You have ten minutes left in an exam task. The Deployment exists, the pod restarts repeatedly, and the Service has no usable backend. How do you implement a repeatable debugging workflow without chasing every symptom?</summary>

First classify the pod state with `kubectl get pod -o wide`, then use `kubectl describe pod` to read container state, Last State, events, and probes. Because restarts are present, get `kubectl logs --previous` before relying on current logs; if previous logs are unavailable, use `kubectl describe pod | grep -A5 "Last State"`. Once the pod is stable and Ready, check Service selector and endpoints to confirm it can receive traffic. This sequence separates the crash root cause from the Service symptom and prevents you from patching networking before the backend is eligible.

</details>

## Hands-On Exercise

In this exercise, you will create several broken objects, classify each symptom, gather evidence in the right order, apply the smallest safe fix, and verify that the cluster state changed. Run these commands in a disposable namespace or a local practice cluster. The examples use ordinary pods and Services so you can focus on the debugging method rather than on application-specific behavior.

### Task

Debug and fix the broken pods by classifying their states, reading the evidence that belongs to each state, and applying the smallest manifest-level repair that makes the object converge. The lab intentionally includes one image failure, one process failure, and one scheduling failure so you can practice choosing different evidence sources instead of using the same command sequence for every symptom.

### Setup

```bash
# Create a broken pod (wrong image)
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken1
spec:
  containers:
  - name: app
    image: nginx:nonexistent-tag
EOF

# Create a crashing pod
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken2
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo "Config not found"; exit 1']
EOF

# Create pod with resource issue
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken3
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "999Gi"
EOF
```

Before you fix anything, write down the state that each object shows and the first command that should explain it. `broken1` should send you toward image pull events, `broken2` should send you toward previous logs and Last State, and `broken3` should send you toward scheduling or resource evidence. That short prediction step is not ceremony; it keeps the lab from becoming a copy-paste exercise.

### Debug Each

```bash
# Debug broken1
kubectl get pod broken1
kubectl describe pod broken1 | tail -10
# Fix: Change image to nginx:latest
kubectl set image pod/broken1 app=nginx:latest
# Verify fix
kubectl wait --for=condition=Ready pod/broken1 --timeout=30s

# Debug broken2
kubectl get pod broken2
# Wait for crashloop to trigger a restart (minimum 10s backoff)
sleep 20
kubectl logs broken2 --previous
# Fallback when --previous is empty (fast crash loops):
kubectl describe pod broken2 | grep -A5 "Last State"
# Fix: Provide correct config by replacing the pod
kubectl delete pod broken2
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken2
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'sleep 3600']
EOF
# Verify fix
kubectl wait --for=condition=Ready pod/broken2 --timeout=30s

# Debug broken3
kubectl get pod broken3
kubectl describe pod broken3 | grep -A5 Events
# Fix: Reduce memory request by replacing the pod
kubectl delete pod broken3
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: broken3
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "256Mi"
EOF
# Verify fix
kubectl wait --for=condition=Ready pod/broken3 --timeout=30s
```

<details>
<summary>Solution notes for broken pods</summary>

`broken1` should show image pull errors in Events, so changing the image tag is the right repair. `broken2` should show a failed previous instance, and the replacement pod changes the command from an intentional failure to a long-running sleep. `broken3` should show scheduling pressure from the oversized memory request, so replacing it with a realistic request lets the scheduler place the pod.

</details>

### Cleanup

```bash
kubectl delete pod broken1 broken2 broken3
```

### Practice Drills

These drills preserve the quick exam repetitions from the original module, but the purpose is now sharper: each drill trains one branch of the decision framework. Run them after the main lab and time yourself only after you can explain the expected evidence. Speed that comes before diagnosis is usually just faster guessing.

### Drill 1: Describe and Events (Target: 2 minutes)

```bash
# Create pod
kubectl run drill1 --image=nginx

# Describe it
kubectl describe pod drill1

# Check events
kubectl get events --field-selector involvedObject.name=drill1

# Cleanup
kubectl delete pod drill1
```

### Drill 2: Exec Into Pod (Target: 2 minutes)

```bash
# Create pod
kubectl run drill2 --image=nginx
kubectl wait --for=condition=Ready pod/drill2 --timeout=30s

# Exec into it (non-interactive command execution)
kubectl exec drill2 -- nginx -v

# Cleanup
kubectl delete pod drill2
```

### Drill 3: Debug Crashing Pod (Target: 3 minutes)

```bash
# Create crashing pod
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'echo error; exit 1']
EOF

# Wait for crash and restart
sleep 20
kubectl get pod drill3

# Get logs from previous
kubectl logs drill3 --previous
# Fallback when --previous is empty:
kubectl describe pod drill3 | grep -A5 "Last State"

# Cleanup
kubectl delete pod drill3
```

### Drill 4: Debug ImagePullBackOff (Target: 3 minutes)

```bash
# Create pod with bad image
kubectl run drill4 --image=invalid-registry.io/no-such-image:v1

# Wait for pull failure
sleep 5

# Check status
kubectl get pod drill4

# Describe for details
kubectl describe pod drill4 | grep -A5 Events

# Cleanup
kubectl delete pod drill4
```

### Drill 5: Service Debug (Target: 4 minutes)

```bash
# Create pod and service with mismatched labels
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill5
  labels:
    app: myapp
spec:
  containers:
  - name: nginx
    image: nginx
---
apiVersion: v1
kind: Service
metadata:
  name: drill5-svc
spec:
  selector:
    app: wronglabel
  ports:
  - port: 80
EOF

# Check endpoints (should be empty)
kubectl get endpoints drill5-svc

# Find the problem
kubectl get pod drill5 --show-labels
kubectl describe svc drill5-svc | grep Selector

# Fix by patching service
kubectl patch svc drill5-svc -p '{"spec":{"selector":{"app":"myapp"}}}'

# Verify endpoints now exist
kubectl get endpoints drill5-svc

# Cleanup
kubectl delete pod drill5 svc drill5-svc
```

### Drill 6: Complete Debug Scenario (Target: 5 minutes)

Exercise scenario: an application has been deployed and the Service exists, but the workload is not accessible because readiness prevents the pods from becoming usable backends. Treat this as a full-path debugging exercise: pod state first, endpoint membership second, probe evidence third, and rollout verification after the patch.

```bash
# Create "broken" deployment
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill6
spec:
  replicas: 2
  selector:
    matchLabels:
      app: drill6
  template:
    metadata:
      labels:
        app: drill6
    spec:
      containers:
      - name: nginx
        image: nginx
        readinessProbe:
          httpGet:
            path: /nonexistent
            port: 80
---
apiVersion: v1
kind: Service
metadata:
  name: drill6-svc
spec:
  selector:
    app: drill6
  ports:
  - port: 80
EOF

# Check pods (running but not ready)
kubectl get pods -l app=drill6

# Check endpoints (empty)
kubectl get endpoints drill6-svc

# Describe pod for probe failure
kubectl describe pod -l app=drill6 | grep -A5 Readiness

# Fix readiness probe
kubectl patch deploy drill6 --type='json' -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/"}]'

# Wait for rollout
kubectl rollout status deploy drill6

# Verify endpoints
kubectl get endpoints drill6-svc

# Cleanup
kubectl delete deploy drill6 svc drill6-svc
```

<details>
<summary>Solution notes for service drills</summary>

Drill 5 is a selector problem, so empty endpoints should lead you to compare the Service selector with pod labels. Drill 6 is a readiness problem, so the Deployment creates pods, but the Service receives no ready backends until the probe path is corrected. In both drills, the endpoint check is the proof that the Service relationship changed.

</details>

### Success Criteria

- [ ] Diagnose pod failures by recording status, events, logs, and describe output before editing.
- [ ] Debug CrashLoopBackOff with `kubectl logs --previous`, falling back to Last State in `describe` when previous logs are unavailable.
- [ ] Debug ImagePullBackOff by reading image pull events and fixing only the image reference.
- [ ] Diagnose Pending by reading scheduling or resource events before looking for logs.
- [ ] Troubleshoot service and pod networking by comparing selectors, labels, readiness, endpoints, and DNS.
- [ ] Implement the repeatable debugging workflow without using shell aliases or manual in-container repairs.

## Learner check

Before moving on, confirm you can explain these remediation points in your own words:

> Busybox `nslookup` does not expand the `search` path in `/etc/resolv.conf` the way glibc or netshoot does, so short-name lookups often return `NXDOMAIN` on Kubernetes 1.35 even when cluster DNS is healthy — and the command may exit non-zero even when it printed a useful `Address:` line.

> The `--target` flag attaches the debug container to an existing container and shares that target's process namespace, which is why `ps aux` can see application processes. The `--share-processes` flag applies only with `--copy-to`; it is a no-op on a plain `--target` debug attach.

> On kind and other containerd-backed clusters, `kubectl logs --previous` can return `unable to retrieve container logs` during very fast crash loops because the terminated instance has not been retained yet.

## Sources

- https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/
- https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/
- https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/
- https://kubernetes.io/docs/tasks/debug/debug-application/get-shell-running-container/
- https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- https://kubernetes.io/docs/concepts/services-networking/service/
- https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/
- https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/

## Next Module

[Module 3.4: Monitoring Applications](../module-3.4-monitoring/) - Monitor application health and resource usage after you can already diagnose pod, Service, readiness, and runtime failures from direct Kubernetes evidence.

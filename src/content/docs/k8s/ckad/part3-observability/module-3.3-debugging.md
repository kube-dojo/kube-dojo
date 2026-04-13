---
title: "Module 3.3: Debugging in Kubernetes"
slug: k8s/ckad/part3-observability/module-3.3-debugging
sidebar:
  order: 3
lab:
  id: ckad-3.3-debugging
  url: https://killercoda.com/kubedojo/scenario/ckad-3.3-debugging
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical exam skill requiring systematic approach
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 3.1 (Probes), Module 3.2 (Logging)

---

## Learning Outcomes

After completing this module, you will be able to:
- **Diagnose** pod failures systematically using events, logs, describe, and exec
- **Debug** CrashLoopBackOff, ImagePullBackOff, and Pending pod states under time pressure
- **Troubleshoot** networking issues between pods using temporary debug containers
- **Implement** a repeatable debugging workflow: status, events, logs, exec, network

---

## Why This Module Matters

Debugging is where exam performance is won or lost. When something doesn't work, you need a systematic approach to find the problem quickly. The CKAD exam deliberately includes broken configurations—you must diagnose and fix them under time pressure.

This module covers:
- Debugging pods that won't start
- Debugging running pods with issues
- Using ephemeral containers for debugging
- The systematic debugging workflow

> **The Detective Analogy**
>
> Debugging is detective work. You arrive at a crime scene (broken pod) and must find clues. You check the victim's history (`describe`), examine the evidence (`logs`), interview witnesses (`events`), and sometimes need to go undercover (`exec`) to catch the culprit. Systematic investigation beats random guessing.

> **War Story: The Two-Hour Typo**
>
> During a major production rollout, a critical microservice failed to start. The on-call engineer panicked and spent two hours randomly restarting the deployment, rolling back healthy database changes, and rewriting ingress rules. If they had simply followed a systematic workflow—starting with `kubectl describe pod` and reading the events—they would have immediately seen an `ErrImagePull` event caused by a typo in the image tag. A systematic workflow turns a two-hour panic attack into a two-minute fix. This same panic is what causes candidates to fail the CKAD exam when faced with a broken environment.

---

## The Debugging Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              Systematic Debugging Workflow                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. GET STATUS                                              │
│     k get pod POD -o wide                                   │
│     └── What state? Ready? Restarts? Node?                 │
│                                                             │
│  2. DESCRIBE                                                │
│     k describe pod POD                                      │
│     └── Events? Conditions? Container status?              │
│                                                             │
│  3. LOGS                                                    │
│     k logs POD [--previous]                                 │
│     └── What did the app say? Errors?                      │
│                                                             │
│  4. EXEC                                                    │
│     k exec -it POD -- sh                                    │
│     └── What's inside? Files? Processes? Network?          │
│                                                             │
│  5. EVENTS                                                  │
│     k get events --sort-by='.lastTimestamp'                 │
│     └── What happened cluster-wide?                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Debug Commands

### Quick Status Check

```bash
# Pod status overview
k get pod POD -o wide

# All pods in namespace
k get pods

# Watch for changes
k get pods -w
```

### Describe for Details

```bash
# Full pod details
k describe pod POD

# Key sections to check:
# - Status/Conditions
# - Containers (State, Ready, Restart Count)
# - Events (bottom of output)
```

### View Logs

```bash
# Current logs
k logs POD

# Previous instance (after crash)
k logs POD --previous

# Specific container
k logs POD -c CONTAINER

# Stream logs
k logs -f POD
```

### Execute Commands

```bash
# Interactive shell
k exec -it POD -- sh
k exec -it POD -- /bin/bash

# Run single command
k exec POD -- ls /app
k exec POD -- cat /etc/config

# Specific container
k exec -it POD -c CONTAINER -- sh
```

### View Events

```bash
# Namespace events (sorted by time)
k get events --sort-by='.lastTimestamp'

# Filter by type
k get events --field-selector type=Warning

# Events for specific pod
k get events --field-selector involvedObject.name=POD
```

---

## Common Pod States and Fixes

### Pending

**Pod stuck in Pending state.**

```bash
# Check why
k describe pod POD

# Common causes:
# 1. Insufficient resources
#    → Check node resources: k describe node
#    → Reduce pod resource requests

# 2. No matching node (nodeSelector/affinity)
#    → Check node labels: k get nodes --show-labels
#    → Fix selector or label nodes

# 3. PVC not bound
#    → Check PVC: k get pvc
#    → Create matching PV
```

> **Pause and predict**: A pod is stuck in `Pending` state. You check `kubectl describe pod` and see the event "0/3 nodes are available: 3 Insufficient cpu." Is this a pod problem or a cluster problem? What are your options?

### ImagePullBackOff / ErrImagePull

**Can't pull container image.**

```bash
# Check events
k describe pod POD | grep -A5 Events

# Common causes:
# 1. Wrong image name/tag
#    → Fix image in pod spec

# 2. Private registry without credentials
#    → Create imagePullSecret

# 3. Image doesn't exist
#    → Verify image exists in registry
```

### CrashLoopBackOff

**Container crashes repeatedly.**

```bash
# Check logs from crashed instance
k logs POD --previous

# Check exit code
k describe pod POD | grep "Last State"

# Common causes:
# 1. Application error (check logs)
# 2. Missing config/secrets
# 3. Wrong command/args
# 4. Liveness probe killing healthy app
```

> **Stop and think**: A pod shows `CrashLoopBackOff` with exit code 137. Before looking at the answer section, what does exit code 137 tell you about the cause? What would you check first?

### Running but Not Ready

**Container running but readiness fails.**

```bash
# Check readiness probe
k describe pod POD | grep -A5 Readiness

# Check endpoints
k get endpoints SERVICE

# Common causes:
# 1. Wrong readiness probe path/port
# 2. App not fully started
# 3. Dependency not available
```

---

## Debugging Inside Containers

### Basic Commands

```bash
# Get shell
k exec -it POD -- sh

# Check processes
k exec POD -- ps aux

# Check network
k exec POD -- netstat -tlnp
k exec POD -- ss -tlnp

# Check DNS
k exec POD -- nslookup kubernetes
k exec POD -- cat /etc/resolv.conf

# Check connectivity
k exec POD -- wget -qO- http://service:port
k exec POD -- curl -s http://service:port

# Check files
k exec POD -- ls -la /app
k exec POD -- cat /etc/config/file
```

> **Pause and predict**: You need to test network connectivity from inside a distroless container that has no shell, no curl, no wget. How would you approach this?

### When Shell Isn't Available

Some containers (distroless, scratch) don't have a shell:

```bash
# Check if shell exists
k exec POD -- /bin/sh -c 'echo works'

# If no shell, use debug container (Kubernetes 1.25+)
k debug POD -it --image=busybox --target=container-name
```

---

## Ephemeral Debug Containers

Kubernetes 1.25+ supports ephemeral containers for debugging:

```bash
# Add debug container to running pod
k debug POD -it --image=busybox --target=container-name

# Debug with specific image
k debug POD -it --image=nicolaka/netshoot

# Copy pod for debugging (doesn't affect original)
k debug POD -it --copy-to=debug-pod --container=debug --image=busybox
```

### Debug Container Use Cases

```bash
# Network debugging (no curl in original container)
k debug POD -it --image=nicolaka/netshoot --target=app
# Then: curl, dig, nslookup, tcpdump

# File system inspection
k debug POD -it --image=busybox --target=app
# Then: ls, cat, find

# Process debugging
k debug POD -it --image=busybox --target=app --share-processes
# Then: ps aux
```

---

## Service Debugging

### Check Service-to-Pod Connection

```bash
# Verify service exists
k get svc SERVICE

# Check endpoints (should list pod IPs)
k get endpoints SERVICE

# If no endpoints:
# - Check pod labels match service selector
# - Check pod readiness
k get pods --show-labels
k describe svc SERVICE | grep Selector
```

### Test Service DNS

```bash
# From inside a pod
k exec POD -- nslookup SERVICE
k exec POD -- nslookup SERVICE.NAMESPACE.svc.cluster.local

# Create test pod for debugging
k run test --image=busybox --rm -it -- nslookup SERVICE
```

### Test Service Connectivity

```bash
# From inside a pod
k exec POD -- wget -qO- http://SERVICE:PORT
k exec POD -- curl -s http://SERVICE:PORT
```

---

## Debug Scenarios

### Scenario 1: Pod Won't Start

```bash
# Step 1: Check status
k get pod broken-pod

# Step 2: Describe for events
k describe pod broken-pod

# Step 3: Check if image exists
# If ErrImagePull: fix image name
# If Pending: check resources/node selector

# Step 4: Check logs if container started
k logs broken-pod
```

### Scenario 2: Pod Keeps Crashing

```bash
# Step 1: Get restart count
k get pod crashing-pod

# Step 2: Check previous logs
k logs crashing-pod --previous

# Step 3: Check exit code
k describe pod crashing-pod | grep -A3 "Last State"

# Step 4: Check liveness probe
k describe pod crashing-pod | grep -A5 Liveness
```

### Scenario 3: Service Not Reachable

```bash
# Step 1: Check service exists
k get svc myservice

# Step 2: Check endpoints
k get endpoints myservice

# Step 3: If no endpoints, check pod labels
k get pods --show-labels
k describe svc myservice | grep Selector

# Step 4: Test from inside cluster
k run test --image=busybox --rm -i -- wget -qO- http://myservice
```

---

## Did You Know?

- **`kubectl debug` creates ephemeral containers** that share the pod's network and process namespaces. This means you can see network connections and processes from a debug container.

- **Exit code 137 means OOMKilled** (Out of Memory). The container was killed because it exceeded its memory limit.

- **Exit code 1 is a generic failure**, usually from the application itself. Check logs for details.

- **Exit code 0 means success**—but if a container exits 0 and wasn't supposed to, it's still a problem (wrong command).

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Random guessing | Wastes exam time | Follow systematic workflow |
| Skipping `describe` | Miss obvious events | Always check events first |
| Not checking `--previous` | Miss crash logs | Check previous instance on CrashLoop |
| Ignoring exit codes | Miss OOM/signal issues | Check Last State in describe |
| Forgetting readiness | Pod works but no traffic | Check endpoints and probes |

---

## Quiz

1. **A pod named `api-server` is in CrashLoopBackOff. You run `kubectl logs api-server` but see only a fresh startup message — no errors. How do you find out what caused the crash, and what is your systematic next step?**
   <details>
   <summary>Answer</summary>
   The current logs are from the freshly restarted instance, which hasn't crashed yet. Run `kubectl logs api-server --previous` to see the logs from the instance that actually crashed. If that doesn't reveal the issue, run `kubectl describe pod api-server` and check the "Last State" section for the exit code and reason. Exit code 1 means the application threw an error (check logs more carefully), exit code 137 means OOMKilled (increase memory limits), and exit code 0 means the process exited successfully but shouldn't have (likely a wrong command).
   </details>

2. **A developer deployed a new version of their app. The pods show `ImagePullBackOff`. They swear the image exists because they pushed it 10 minutes ago. What are the three most common causes, and how do you investigate each one?**
   <details>
   <summary>Answer</summary>
   Run `kubectl describe pod` and check the Events section for the exact error message. The three most common causes: (1) Typo in image name or tag — verify by comparing the pod spec image with what's in the registry. (2) Private registry without imagePullSecrets — the image exists but the node can't authenticate. Check if the pod spec has `imagePullSecrets` and if the secret contains valid credentials. (3) The image was pushed to a different registry or repository than what's in the manifest. The describe output usually includes the registry's error message, which tells you exactly which of these is the problem.
   </details>

3. **Users report they can't reach your application through a Service, but all pods show Running and Ready (1/1). You run `kubectl get endpoints myservice` and see `<none>`. What is the most likely root cause and how do you fix it?**
   <details>
   <summary>Answer</summary>
   Empty endpoints with Running pods means the Service's label selector doesn't match the pods' labels. Debug by comparing: run `kubectl describe svc myservice | grep Selector` to see what the Service expects, then `kubectl get pods --show-labels` to see actual pod labels. The fix is to either patch the Service selector to match the pod labels (`kubectl patch svc myservice -p '{"spec":{"selector":{"app":"correct-label"}}}'`) or update the pod/deployment labels to match the Service selector. This is one of the most common debugging scenarios in the CKAD exam.
   </details>

4. **You need to debug a network issue from inside a running pod, but the container image is distroless (no shell, no curl, no network tools). The pod is serving production traffic and you cannot restart it. What do you do?**
   <details>
   <summary>Answer</summary>
   Use an ephemeral debug container: `kubectl debug pod-name -it --image=nicolaka/netshoot --target=container-name`. This attaches a new container to the running pod that shares the pod's network namespace, so you can use tools like `curl`, `dig`, `nslookup`, and `tcpdump` to diagnose the issue. The `--target` flag shares the process namespace with the specified container. The original container continues running unaffected. Alternatively, `kubectl debug pod-name -it --copy-to=debug-pod --image=busybox` creates a copy of the pod for investigation without touching the original.
   </details>

---

## Hands-On Exercise

**Task**: Debug and fix broken pods.

**Setup:**
```bash
# Create a broken pod (wrong image)
cat << 'EOF' | k apply -f -
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
cat << 'EOF' | k apply -f -
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
cat << 'EOF' | k apply -f -
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

**Debug Each:**
```bash
# Debug broken1
k get pod broken1
k describe pod broken1 | tail -10
# Fix: Change image to nginx:latest
k set image pod/broken1 app=nginx:latest
# Verify fix
k wait --for=condition=Ready pod/broken1 --timeout=30s

# Debug broken2
k get pod broken2
# Wait for crashloop to trigger a restart (minimum 10s backoff)
sleep 20
k logs broken2 --previous
# Fix: Provide correct config by replacing the pod
k get pod broken2 -o yaml | sed 's/exit 1/sleep 3600/' | k replace --force -f -
# Verify fix
k wait --for=condition=Ready pod/broken2 --timeout=30s

# Debug broken3
k get pod broken3
k describe pod broken3 | grep -A5 Events
# Fix: Reduce memory request by replacing the pod
k get pod broken3 -o yaml | sed 's/999Gi/256Mi/' | k replace --force -f -
# Verify fix
k wait --for=condition=Ready pod/broken3 --timeout=30s
```

**Cleanup:**
```bash
k delete pod broken1 broken2 broken3
```

---

## Practice Drills

### Drill 1: Describe and Events (Target: 2 minutes)

```bash
# Create pod
k run drill1 --image=nginx

# Describe it
k describe pod drill1

# Check events
k get events --field-selector involvedObject.name=drill1

# Cleanup
k delete pod drill1
```

### Drill 2: Exec Into Pod (Target: 2 minutes)

```bash
# Create pod
k run drill2 --image=nginx
k wait --for=condition=Ready pod/drill2 --timeout=30s

# Exec into it (non-interactive command execution)
k exec drill2 -- bash -c 'ps aux | grep nginx'

# Cleanup
k delete pod drill2
```

### Drill 3: Debug Crashing Pod (Target: 3 minutes)

```bash
# Create crashing pod
cat << 'EOF' | k apply -f -
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
k get pod drill3

# Get logs from previous
k logs drill3 --previous

# Cleanup
k delete pod drill3
```

### Drill 4: Debug ImagePullBackOff (Target: 3 minutes)

```bash
# Create pod with bad image
k run drill4 --image=invalid-registry.io/no-such-image:v1

# Wait for pull failure
sleep 5

# Check status
k get pod drill4

# Describe for details
k describe pod drill4 | grep -A5 Events

# Cleanup
k delete pod drill4
```

### Drill 5: Service Debug (Target: 4 minutes)

```bash
# Create pod and service with mismatched labels
cat << 'EOF' | k apply -f -
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
k get endpoints drill5-svc

# Find the problem
k get pod drill5 --show-labels
k describe svc drill5-svc | grep Selector

# Fix by patching service
k patch svc drill5-svc -p '{"spec":{"selector":{"app":"myapp"}}}'

# Verify endpoints now exist
k get endpoints drill5-svc

# Cleanup
k delete pod drill5 svc drill5-svc
```

### Drill 6: Complete Debug Scenario (Target: 5 minutes)

**Scenario**: Application deployed but not accessible.

```bash
# Create "broken" deployment
cat << 'EOF' | k apply -f -
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
k get pods -l app=drill6

# Check endpoints (empty)
k get endpoints drill6-svc

# Describe pod for probe failure
k describe pod -l app=drill6 | grep -A5 Readiness

# Fix readiness probe
k patch deploy drill6 --type='json' -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/"}]'

# Wait for rollout
k rollout status deploy drill6

# Verify endpoints
k get endpoints drill6-svc

# Cleanup
k delete deploy drill6 svc drill6-svc
```

---

## Next Module

[Module 3.4: Monitoring Applications](../module-3.4-monitoring/) - Monitor application health and resource usage.
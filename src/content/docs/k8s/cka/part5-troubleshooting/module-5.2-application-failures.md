---
title: "Module 5.2: Application Failures"
slug: k8s/cka/part5-troubleshooting/module-5.2-application-failures
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Most common troubleshooting scenarios
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 5.1 (Troubleshooting Methodology), Module 2.1-2.7 (Workloads)

---

## Why This Module Matters

Application failures are the most common issues you'll encounter - both in the exam and in production. A pod that won't start, a container that keeps crashing, or a deployment that won't roll out are daily occurrences. Mastering application troubleshooting is essential for any Kubernetes administrator.

> **The Restaurant Kitchen Analogy**
>
> Think of pods as dishes being prepared in a kitchen. Sometimes the dish fails because of a bad recipe (wrong image), sometimes the ingredients are missing (ConfigMap/Secret), sometimes the chef runs out of space (resources), and sometimes the dish just doesn't come out right (application bug). Each failure has different symptoms and different fixes.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Troubleshoot pods that won't start
- Diagnose CrashLoopBackOff containers
- Fix image pull failures
- Resolve configuration issues
- Handle resource constraints and OOM kills
- Debug deployment rollout problems

---

## Did You Know?

- **CrashLoopBackOff has exponential backoff**: It starts at 10s, then 20s, 40s, up to 5 minutes between restart attempts
- **Init containers run first**: If init containers fail, main containers never start - many people forget to check them
- **ImagePullBackOff vs ErrImagePull**: ErrImagePull is the first failure, ImagePullBackOff is after multiple retries

---

## Part 1: Pod Startup Failures

### 1.1 The Pod Startup Sequence

Understanding what happens when a pod starts:

```
┌──────────────────────────────────────────────────────────────┐
│                    POD STARTUP SEQUENCE                       │
│                                                               │
│   1. Scheduling     2. Preparation      3. Startup           │
│   ┌──────────┐     ┌──────────────┐    ┌──────────────┐     │
│   │ Pending  │────▶│ Container    │───▶│ Init         │     │
│   │          │     │ Creating     │    │ Containers   │     │
│   └──────────┘     └──────────────┘    └──────────────┘     │
│        │                  │                   │              │
│        ▼                  ▼                   ▼              │
│   • Node selection   • Pull images      • Run in order      │
│   • Resource check   • Mount volumes    • Each must exit 0  │
│   • Taints/affinity  • Setup network    • Sequential only   │
│                                                               │
│   4. Running         5. Ready                                │
│   ┌──────────────┐  ┌──────────────┐                        │
│   │ Main         │─▶│ Readiness    │                        │
│   │ Containers   │  │ Probes Pass  │                        │
│   └──────────────┘  └──────────────┘                        │
│        │                   │                                 │
│        ▼                   ▼                                 │
│   • Start all         • Pod marked Ready                    │
│   • Run probes        • Added to Service                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Pending - Scheduling Issues

When a pod is stuck in Pending:

```bash
# Check why pod is pending
k describe pod <pod> | grep -A 10 Events
```

**Common causes**:

| Message | Cause | Solution |
|---------|-------|----------|
| `0/3 nodes available` | No suitable nodes | Check node taints, affinity rules |
| `Insufficient cpu` | Not enough CPU | Reduce requests or add capacity |
| `Insufficient memory` | Not enough memory | Reduce requests or add capacity |
| `node(s) had taint that pod didn't tolerate` | Taints blocking | Add tolerations or remove taints |
| `node(s) didn't match node selector` | nodeSelector mismatch | Fix labels or selector |
| `persistentvolumeclaim not found` | PVC missing | Create PVC |
| `persistentvolumeclaim not bound` | No matching PV | Check StorageClass, create PV |

**Investigation commands**:

```bash
# Check node resources
k describe nodes | grep -A 5 "Allocated resources"
k top nodes

# Check node taints
k get nodes -o custom-columns='NAME:.metadata.name,TAINTS:.spec.taints[*].key'

# Check node labels (for nodeSelector)
k get nodes --show-labels
```

### 1.3 ContainerCreating - Preparation Issues

When a pod is stuck in ContainerCreating:

```bash
# Always check Events first
k describe pod <pod> | grep -A 15 Events
```

**Common causes**:

| Message | Cause | Solution |
|---------|-------|----------|
| `pulling image` (stuck) | Slow/large image | Wait, or use smaller image |
| `ImagePullBackOff` | Wrong image name | Fix image reference |
| `ErrImagePull` | Registry auth failed | Check imagePullSecrets |
| `MountVolume.SetUp failed` | Volume mount issue | Check PVC, ConfigMap, Secret exists |
| `configmap not found` | Missing ConfigMap | Create ConfigMap |
| `secret not found` | Missing Secret | Create Secret |
| `network not ready` | CNI issues | Check CNI pods |

**Investigation commands**:

```bash
# Check image pull issues
k get events --field-selector involvedObject.name=<pod>

# Check if ConfigMap/Secret exists
k get configmap <name>
k get secret <name>

# Check PVC status
k get pvc
k describe pvc <name>
```

---

## Part 2: Container Crash Troubleshooting

### 2.1 Understanding CrashLoopBackOff

```
┌──────────────────────────────────────────────────────────────┐
│                   CRASHLOOPBACKOFF CYCLE                      │
│                                                               │
│   Container Start ──▶ Container Crash ──▶ Wait ──┐           │
│         ▲                                         │           │
│         └─────────────────────────────────────────┘           │
│                                                               │
│   Backoff Times:                                              │
│   1st crash: wait 10s                                         │
│   2nd crash: wait 20s                                         │
│   3rd crash: wait 40s                                         │
│   4th crash: wait 80s                                         │
│   5th crash: wait 160s                                        │
│   6th+ crash: wait 300s (5 min max)                          │
│                                                               │
│   After 10 minutes of running successfully, timer resets     │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 CrashLoopBackOff Investigation

**Step-by-step approach**:

```bash
# Step 1: Check pod status and restart count
k get pod <pod>
# Look at RESTARTS column

# Step 2: Check events
k describe pod <pod> | grep -A 10 Events

# Step 3: Check current container state
k describe pod <pod> | grep -A 10 "State:"

# Step 4: Check PREVIOUS container logs (crucial!)
k logs <pod> --previous

# Step 5: Check exit code
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
```

### 2.3 Exit Codes Decoded

| Exit Code | Signal | Meaning | Common Cause |
|-----------|--------|---------|--------------|
| 0 | - | Success | Normal exit (shouldn't cause CrashLoop) |
| 1 | - | Application error | App logic error, missing config |
| 2 | - | Misuse of shell builtin | Script error |
| 126 | - | Command not executable | Permission issue |
| 127 | - | Command not found | Wrong entrypoint/command |
| 128+N | Signal N | Killed by signal | See below |
| 137 | SIGKILL (9) | Force killed | OOMKilled, or `kill -9` |
| 139 | SIGSEGV (11) | Segmentation fault | Application bug |
| 143 | SIGTERM (15) | Graceful termination | Normal shutdown |

### 2.4 OOMKilled Investigation

When exit code is 137 or status shows OOMKilled:

```bash
# Check for OOMKilled status
k describe pod <pod> | grep -i oom

# Check memory limits
k get pod <pod> -o jsonpath='{.spec.containers[0].resources.limits.memory}'

# Check actual memory usage (if pod is running)
k top pod <pod>

# Fix: Increase memory limit
k patch deployment <name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

### 2.5 Common CrashLoopBackOff Causes

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Exit code 1 | App error | Check logs, fix application |
| Exit code 127 | Command not found | Fix `command` or `args` in spec |
| Exit code 137 + OOMKilled | Memory exceeded | Increase memory limit |
| Exit code 137 no OOM | Killed externally | Check liveness probe |
| Container exits immediately | No foreground process | Add `sleep infinity` or fix command |
| Logs show "file not found" | Missing ConfigMap/Secret | Verify mounts exist |
| Logs show "permission denied" | Security context | Fix runAsUser or fsGroup |

---

## Part 3: Image Pull Failures

### 3.1 Image Pull Error Types

```
┌──────────────────────────────────────────────────────────────┐
│                  IMAGE PULL ERROR FLOW                        │
│                                                               │
│   Attempt Pull ──▶ ErrImagePull ──▶ ImagePullBackOff         │
│        │              │                    │                  │
│        │              │                    │                  │
│   (Success)      (First failure)    (Repeated failures)      │
│                                                               │
│   ErrImagePull causes:                                        │
│   • Image doesn't exist                                       │
│   • Registry unreachable                                      │
│   • Authentication failed                                     │
│   • Rate limited (Docker Hub)                                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Diagnosing Image Pull Issues

```bash
# Check events for specific error
k describe pod <pod> | grep -A 5 "Failed to pull"

# Common error messages:
# "manifest unknown" - Image tag doesn't exist
# "unauthorized" - Registry auth failed
# "timeout" - Registry unreachable
# "toomanyrequests" - Rate limited
```

### 3.3 Fixing Image Pull Issues

**Wrong image name/tag**:
```bash
# Check current image
k get pod <pod> -o jsonpath='{.spec.containers[0].image}'

# Fix with set image
k set image deployment/<name> <container>=<correct-image>

# Or edit directly
k edit deployment <name>
```

**Registry authentication**:
```bash
# Create registry secret
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@example.com

# Add to pod spec
k patch serviceaccount default -p '{"imagePullSecrets":[{"name":"regcred"}]}'

# Or add to specific deployment
k patch deployment <name> -p '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"regcred"}]}}}}'
```

**Docker Hub rate limiting**:
```bash
# Option 1: Use authenticated pulls
k create secret docker-registry dockerhub \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<token>

# Option 2: Use alternative registry (gcr.io, quay.io)
# nginx:latest -> gcr.io/google-containers/nginx:latest
```

---

## Part 4: Configuration Issues

### 4.1 Missing ConfigMap/Secret

**Symptoms**:
- Pod stuck in ContainerCreating
- Events show "configmap not found" or "secret not found"

**Diagnosis**:
```bash
# Check what ConfigMaps/Secrets the pod needs
k get pod <pod> -o yaml | grep -A 5 "configMap\|secret"

# Verify they exist
k get configmap
k get secret

# Check specific one
k describe configmap <name>
```

**Fix**:
```bash
# Create missing ConfigMap
k create configmap <name> --from-literal=key=value

# Create missing Secret
k create secret generic <name> --from-literal=password=secret

# If you have the data file
k create configmap <name> --from-file=config.yaml
k create secret generic <name> --from-file=credentials.json
```

### 4.2 Incorrect ConfigMap/Secret Keys

**Symptoms**:
- Container starts but app fails
- Logs show "file not found" or "key not found"

**Diagnosis**:
```bash
# Check what keys exist in ConfigMap
k get configmap <name> -o yaml

# Check pod's expected keys
k get pod <pod> -o yaml | grep -A 10 configMapKeyRef

# Compare expected vs actual
```

**Fix**:
```bash
# Add missing key to ConfigMap
k patch configmap <name> -p '{"data":{"missing-key":"value"}}'

# Or recreate
k create configmap <name> --from-literal=key1=val1 --from-literal=key2=val2 --dry-run=client -o yaml | k apply -f -
```

### 4.3 Environment Variable Issues

```bash
# Check environment variables in running container
k exec <pod> -- env

# Check what's defined in spec
k get pod <pod> -o jsonpath='{.spec.containers[0].env[*]}'

# Common issue: ConfigMap key name doesn't match env var name
# Check with:
k get pod <pod> -o yaml | grep -A 5 valueFrom
```

---

## Part 5: Deployment Rollout Failures

### 5.1 Stuck Deployments

**Symptoms**:
- `k rollout status deployment/<name>` hangs
- Old and new ReplicaSets both exist
- Pods not reaching Ready state

```bash
# Check deployment status
k get deployment <name>
k describe deployment <name>

# Check ReplicaSets
k get rs -l app=<name>

# Check pods from new ReplicaSet
k get pods -l app=<name>
```

### 5.2 Common Rollout Issues

```
┌──────────────────────────────────────────────────────────────┐
│                  DEPLOYMENT ROLLOUT STATES                    │
│                                                               │
│   Progressing                 Stuck                           │
│   ┌──────────────┐           ┌──────────────┐                │
│   │ New RS       │           │ New RS       │                │
│   │ scaling up   │           │ pods failing │                │
│   └──────────────┘           └──────────────┘                │
│         │                          │                          │
│         ▼                          ▼                          │
│   ┌──────────────┐           ┌──────────────┐                │
│   │ Old RS       │           │ Old RS       │                │
│   │ scaling down │           │ still running│                │
│   └──────────────┘           └──────────────┘                │
│                                                               │
│   Rollout waits for new pods to become Ready                 │
│   If pods never Ready, rollout stalls                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Investigation**:
```bash
# Check deployment conditions
k describe deployment <name> | grep -A 10 Conditions

# Check new ReplicaSet's pods
NEW_RS=$(k get rs -l app=<name> --sort-by='.metadata.creationTimestamp' -o name | tail -1)
k describe $NEW_RS

# Check why pods aren't ready
k get pods -l app=<name> | grep -v Running
k describe pod <failing-pod>
```

### 5.3 Rollback

When new version is broken:

```bash
# Check rollout history
k rollout history deployment/<name>

# Rollback to previous version
k rollout undo deployment/<name>

# Rollback to specific revision
k rollout undo deployment/<name> --to-revision=2

# Verify rollback
k rollout status deployment/<name>
```

### 5.4 Fixing Stuck Rollouts

```bash
# Option 1: Fix the issue and let rollout continue
k set image deployment/<name> <container>=<fixed-image>

# Option 2: Rollback
k rollout undo deployment/<name>

# Option 3: Force restart (deletes and recreates pods)
k rollout restart deployment/<name>

# Option 4: Scale down then up (nuclear option)
k scale deployment/<name> --replicas=0
k scale deployment/<name> --replicas=3
```

---

## Part 6: Readiness and Liveness Probe Failures

### 6.1 Probe Types Review

```
┌──────────────────────────────────────────────────────────────┐
│                     PROBE TYPES                               │
│                                                               │
│   LIVENESS                      READINESS                     │
│   Is container alive?           Is container ready?           │
│                                                               │
│   Failure action:               Failure action:               │
│   RESTART container             REMOVE from service           │
│                                                               │
│   Use for:                      Use for:                      │
│   • Deadlock detection          • Startup dependencies        │
│   • Hung processes              • Warming caches              │
│                                                               │
│   ⚠️ Wrong liveness config      ⚠️ Wrong readiness config     │
│      = crash loops                 = no traffic               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Diagnosing Probe Failures

```bash
# Check probe configuration
k get pod <pod> -o yaml | grep -A 10 "livenessProbe\|readinessProbe"

# Check for probe failures in events
k describe pod <pod> | grep -i "unhealthy\|probe"

# Test probe manually
k exec <pod> -- wget -qO- http://localhost:8080/health
k exec <pod> -- cat /tmp/healthy
```

### 6.3 Common Probe Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Wrong port | Probe fails, container works | Fix port in probe spec |
| Wrong path | 404 errors in events | Fix httpGet path |
| Too aggressive | Containers keep restarting | Increase timeoutSeconds, periodSeconds |
| Missing initialDelaySeconds | Fails during startup | Add initialDelaySeconds |
| App slow to start | CrashLoop at startup | Use startupProbe |

**Fix probe timing**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30   # Wait 30s before first probe
  periodSeconds: 10         # Probe every 10s
  timeoutSeconds: 5         # Timeout after 5s
  failureThreshold: 3       # Restart after 3 failures
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not checking `--previous` | Can't see crash reason | Always check previous logs for CrashLoop |
| Ignoring init containers | Main container never starts | Check init container logs too |
| Fixing symptoms not cause | Problem recurs | Investigate root cause before fixing |
| Wrong resource units | Unexpected OOM or throttling | Use correct units: Mi, Gi, m |
| Liveness probe too aggressive | Healthy containers killed | Increase timeouts and failure threshold |
| Forgetting imagePullSecrets | Private images fail | Add secrets at ServiceAccount or pod level |

---

## Quiz

### Q1: Exit Code Analysis
A container has exit code 1 with logs showing "Error: REDIS_HOST not set". What's the fix?

<details>
<summary>Answer</summary>

The application is missing a required environment variable. Fix by adding it:

```bash
k set env deployment/<name> REDIS_HOST=redis-service
```

Or verify the ConfigMap/Secret that should provide it exists and is correctly referenced.

</details>

### Q2: Image Pull Sequence
What's the difference between ErrImagePull and ImagePullBackOff?

<details>
<summary>Answer</summary>

- **ErrImagePull**: Initial failure to pull the image (first attempt)
- **ImagePullBackOff**: State after multiple failed pull attempts, with exponential backoff between retries

ErrImagePull transitions to ImagePullBackOff after the first failure. The pod alternates between trying to pull and backing off.

</details>

### Q3: Pending Diagnosis
A pod is Pending with message "0/3 nodes are available: 3 Insufficient memory". All nodes have 8GB RAM. What do you check?

<details>
<summary>Answer</summary>

Check:
1. Pod's memory request: `k get pod <pod> -o jsonpath='{.spec.containers[0].resources.requests.memory}'`
2. Allocated resources on nodes: `k describe nodes | grep -A 5 "Allocated resources"`
3. Running pods' requests: `k top nodes`

The requests from existing pods plus this pod's request exceeds available memory. Either reduce requests or add capacity.

</details>

### Q4: CrashLoopBackOff Max
What's the maximum backoff time between container restart attempts?

<details>
<summary>Answer</summary>

**5 minutes (300 seconds)**. The backoff doubles each time: 10s, 20s, 40s, 80s, 160s, 300s. It stays at 300s until the container runs successfully for 10 minutes, then resets.

</details>

### Q5: Init Container Failure
Main container never starts, but there are no errors in its logs. Where do you look?

<details>
<summary>Answer</summary>

Check **init containers**:
```bash
k get pod <pod> -o jsonpath='{.spec.initContainers[*].name}'
k logs <pod> -c <init-container-name>
```

Init containers run first and must all complete successfully before main containers start. If an init container fails, the main container never begins.

</details>

### Q6: Rollback Decision
Deployment is stuck mid-rollout. Old ReplicaSet has 2 pods, new has 1 pod in CrashLoopBackOff. What's the quickest fix?

<details>
<summary>Answer</summary>

```bash
k rollout undo deployment/<name>
```

This immediately rolls back to the previous working version. You can then investigate the failing image/config at leisure.

</details>

---

## Hands-On Exercise: Application Failure Scenarios

### Scenario

Practice diagnosing and fixing various application failures.

### Setup

```bash
# Create namespace
k create ns app-debug-lab
```

### Scenario 1: CrashLoopBackOff

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: crash-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Starting..."; exit 1']
EOF
```

**Task**: Find why it's crashing and what exit code it has.

<details>
<summary>Solution</summary>

```bash
k logs crash-app -n app-debug-lab --previous
k get pod crash-app -n app-debug-lab -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
# Exit code 1 - the command explicitly exits with error
```

</details>

### Scenario 2: Missing ConfigMap

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: config-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: nginx:1.25
    volumeMounts:
    - name: config
      mountPath: /etc/app
  volumes:
  - name: config
    configMap:
      name: app-settings
EOF
```

**Task**: Find why it's stuck in ContainerCreating and fix it.

<details>
<summary>Solution</summary>

```bash
# Diagnose
k describe pod config-app -n app-debug-lab | grep -A 5 Events
# "configmap "app-settings" not found"

# Fix
k create configmap app-settings -n app-debug-lab --from-literal=key=value

# Verify
k get pod config-app -n app-debug-lab
```

</details>

### Scenario 3: Wrong Image Tag

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: image-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: nginx:v99.99.99
EOF
```

**Task**: Diagnose and fix the image pull failure.

<details>
<summary>Solution</summary>

```bash
# Diagnose
k describe pod image-app -n app-debug-lab | grep -A 5 "Failed\|Error"
# "manifest for nginx:v99.99.99 not found"

# Fix - delete and recreate with correct image
k delete pod image-app -n app-debug-lab
k run image-app -n app-debug-lab --image=nginx:1.25
```

</details>

### Scenario 4: Resource Constraint (OOM)

```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: oom-app
  namespace: app-debug-lab
spec:
  containers:
  - name: app
    image: progrium/stress
    args: ['--vm', '1', '--vm-bytes', '500M']
    resources:
      limits:
        memory: "100Mi"
EOF
```

**Task**: Diagnose why the container keeps getting killed.

<details>
<summary>Solution</summary>

```bash
# Diagnose
k describe pod oom-app -n app-debug-lab | grep -i oom
k get pod oom-app -n app-debug-lab -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'
# "OOMKilled"

# The container tries to use 500MB but only has 100Mi limit
# Fix: increase memory limit or reduce app memory usage
```

</details>

### Success Criteria

- [ ] Identified crash-app exit code as 1
- [ ] Created missing ConfigMap for config-app
- [ ] Fixed wrong image tag for image-app
- [ ] Identified OOMKilled status for oom-app

### Cleanup

```bash
k delete ns app-debug-lab
```

---

## Practice Drills

### Drill 1: Quick Pod Status (30 sec)
```bash
# Task: Show all pods with restart count > 0
k get pods -A -o custom-columns='NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount' | awk '$2 > 0'
```

### Drill 2: Previous Logs (30 sec)
```bash
# Task: Get last 50 lines from previous container instance
k logs <pod> --previous --tail=50
```

### Drill 3: Exit Code Check (1 min)
```bash
# Task: Get exit code from crashed container
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
# Or from describe:
k describe pod <pod> | grep "Exit Code"
```

### Drill 4: Image Fix (1 min)
```bash
# Task: Update image in deployment
k set image deployment/<name> <container>=<new-image>
```

### Drill 5: Create Missing ConfigMap (1 min)
```bash
# Task: Create ConfigMap from literal
k create configmap <name> --from-literal=key=value
# From file
k create configmap <name> --from-file=<filename>
```

### Drill 6: Environment Variable Debug (1 min)
```bash
# Task: Check all env vars in running container
k exec <pod> -- env | sort
```

### Drill 7: Rollback Deployment (1 min)
```bash
# Task: Rollback to previous version
k rollout undo deployment/<name>
k rollout status deployment/<name>
```

### Drill 8: Check Probe Config (1 min)
```bash
# Task: View probe configuration
k get pod <pod> -o yaml | grep -A 15 livenessProbe
k get pod <pod> -o yaml | grep -A 15 readinessProbe
```

---

## Next Module

Continue to [Module 5.3: Control Plane Failures](../module-5.3-control-plane/) to learn how to troubleshoot API server, scheduler, controller manager, and etcd issues.

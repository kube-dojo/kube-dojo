---
title: "Module 3.3: Debugging in Kubernetes"
slug: k8s/ckad/part3-observability/module-3.3-debugging
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Critical exam skill requiring systematic approach
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 3.1 (Probes), Module 3.2 (Logging)

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
k run test --image=busybox --rm -it -- wget -qO- http://myservice
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

1. **What command shows logs from a crashed container's previous instance?**
   <details>
   <summary>Answer</summary>
   `kubectl logs POD --previous` or `kubectl logs POD -p`
   </details>

2. **How do you get events sorted by timestamp?**
   <details>
   <summary>Answer</summary>
   `kubectl get events --sort-by='.lastTimestamp'`
   </details>

3. **What does exit code 137 typically indicate?**
   <details>
   <summary>Answer</summary>
   OOMKilled - the container exceeded its memory limit and was killed by the kernel.
   </details>

4. **How do you add an ephemeral debug container to a running pod?**
   <details>
   <summary>Answer</summary>
   `kubectl debug POD -it --image=busybox --target=container-name`
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

# Debug broken2
k get pod broken2
k logs broken2 --previous
# Fix: Provide correct config

# Debug broken3
k get pod broken3
k describe pod broken3 | grep -A5 Events
# Fix: Reduce memory request
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

# Exec into it
k exec -it drill2 -- bash

# Inside: check nginx is running
ps aux | grep nginx
exit

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

# Wait for crash
k get pod drill3 -w

# Get logs from previous
k logs drill3 --previous

# Cleanup
k delete pod drill3
```

### Drill 4: Debug ImagePullBackOff (Target: 3 minutes)

```bash
# Create pod with bad image
k run drill4 --image=invalid-registry.io/no-such-image:v1

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

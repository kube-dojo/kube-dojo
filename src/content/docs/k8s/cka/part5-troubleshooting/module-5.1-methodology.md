---
title: "Module 5.1: Troubleshooting Methodology"
slug: k8s/cka/part5-troubleshooting/module-5.1-methodology
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Foundation for all troubleshooting
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Parts 1-4 completed (cluster architecture, workloads, networking, storage)

---

## Why This Module Matters

Troubleshooting is 30% of the CKA exam - the largest single domain. More importantly, troubleshooting is what separates Kubernetes operators from Kubernetes experts. When a production cluster is down at 3 AM, systematic debugging is the difference between a 5-minute fix and a 5-hour nightmare.

> **The Doctor Analogy**
>
> A good doctor doesn't just guess treatments - they follow a diagnostic process. Symptoms → examination → tests → diagnosis → treatment. Kubernetes troubleshooting works the same way. Random "fixes" might work occasionally, but systematic investigation works every time.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Apply a systematic troubleshooting methodology
- Quickly identify which component is failing
- Use kubectl commands for rapid diagnosis
- Understand where to look for different problem types
- Triage problems using the three-pass strategy

---

## Did You Know?

- **80% of issues are in 5 places**: Pod spec errors, image pull problems, resource constraints, network policies, and misconfigured services
- **Events expire**: Kubernetes events are only kept for 1 hour by default - if you don't check soon, evidence disappears
- **describe > logs**: Most beginners jump straight to logs. Experienced troubleshooters check `describe` first - the Events section often reveals the problem immediately

---

## Part 1: The Troubleshooting Framework

### 1.1 The Four-Step Process

Every troubleshooting session should follow this pattern:

```
┌──────────────────────────────────────────────────────────────┐
│                 TROUBLESHOOTING FRAMEWORK                     │
│                                                               │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│   │ 1. IDENTIFY │────▶│ 2. ISOLATE  │────▶│ 3. DIAGNOSE │   │
│   │   What's    │     │   Where's   │     │   Why's     │   │
│   │   wrong?    │     │   it wrong? │     │   it wrong? │   │
│   └─────────────┘     └─────────────┘     └─────────────┘   │
│                                                  │            │
│                                                  ▼            │
│                                           ┌─────────────┐    │
│                                           │  4. FIX     │    │
│                                           │   Apply     │    │
│                                           │   solution  │    │
│                                           └─────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Step 1: Identify - What's Wrong?

Start with the symptom. Be specific:

| Vague | Specific |
|-------|----------|
| "App is broken" | "Pod is in CrashLoopBackOff" |
| "Network doesn't work" | "Pod can't reach external DNS" |
| "Cluster is slow" | "API server response time > 5s" |

**Initial triage commands**:

```bash
# Cluster-wide health check
k get nodes
k get pods -A | grep -v Running
k get events -A --sort-by='.lastTimestamp' | tail -20

# Component health
k get componentstatuses  # Deprecated but still useful
k -n kube-system get pods
```

### 1.3 Step 2: Isolate - Where's It Wrong?

Narrow down the scope systematically:

```
┌──────────────────────────────────────────────────────────────┐
│                    ISOLATION LAYERS                           │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │                    CLUSTER                           │    │
│   │   ┌─────────────────────────────────────────────┐   │    │
│   │   │                  NODE                        │   │    │
│   │   │   ┌─────────────────────────────────────┐   │   │    │
│   │   │   │               POD                    │   │   │    │
│   │   │   │   ┌─────────────────────────────┐   │   │   │    │
│   │   │   │   │         CONTAINER            │   │   │   │    │
│   │   │   │   │   ┌─────────────────────┐   │   │   │   │    │
│   │   │   │   │   │     APPLICATION     │   │   │   │   │    │
│   │   │   │   │   └─────────────────────┘   │   │   │   │    │
│   │   │   │   └─────────────────────────────┘   │   │   │    │
│   │   │   └─────────────────────────────────────┘   │   │    │
│   │   └─────────────────────────────────────────────┘   │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
│   Start wide, drill down until you find the problem layer    │
└──────────────────────────────────────────────────────────────┘
```

**Isolation questions**:
- Is it all pods or specific pods?
- Is it all nodes or specific nodes?
- Is it all namespaces or specific namespaces?
- Did it ever work? What changed?

### 1.4 Step 3: Diagnose - Why's It Wrong?

Once you've isolated the layer, gather detailed information:

```bash
# Pod-level diagnosis
k describe pod <pod-name>     # Events section is gold
k logs <pod-name>             # Current container logs
k logs <pod-name> --previous  # Previous container (if crashed)

# Node-level diagnosis
k describe node <node-name>
ssh <node> journalctl -u kubelet

# Cluster-level diagnosis
k -n kube-system logs <component-pod>
```

### 1.5 Step 4: Fix - Apply Solution

Only after diagnosis do you fix:

```bash
# Apply the fix
k edit <resource>          # Direct edit
k apply -f <fixed-yaml>    # Apply corrected spec
k delete pod <pod>         # Force restart

# Verify the fix
k get pods -w              # Watch for status change
k logs <pod>               # Check new logs
```

---

## Part 2: The Kubernetes Component Map

### 2.1 Know Your Components

Understanding what each component does helps you know where to look:

```
┌──────────────────────────────────────────────────────────────┐
│                    COMPONENT FAILURE MAP                      │
│                                                               │
│ SYMPTOM                          CHECK THESE COMPONENTS       │
│ ─────────────────────────────────────────────────────────────│
│                                                               │
│ Pods not scheduling           →  kube-scheduler               │
│ Pods stuck Pending            →  scheduler, node resources    │
│ Pods stuck ContainerCreating  →  kubelet, image pull, volumes │
│ Pods CrashLoopBackOff         →  container, app config        │
│ Pods can't communicate        →  CNI, network policies        │
│ Services not working          →  kube-proxy, endpoints        │
│ kubectl times out             →  API server, etcd             │
│ Node NotReady                 →  kubelet, container runtime   │
│ Persistent volume issues      →  CSI driver, storage class    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Control Plane Components

| Component | What It Does | Failure Symptoms |
|-----------|--------------|------------------|
| kube-apiserver | All API operations | kubectl fails, nothing works |
| etcd | State storage | Data loss, inconsistent state |
| kube-scheduler | Pod placement | Pods stuck Pending |
| kube-controller-manager | Reconciliation loops | Resources not updating |

### 2.3 Node Components

| Component | What It Does | Failure Symptoms |
|-----------|--------------|------------------|
| kubelet | Pod lifecycle | Pods not starting, node NotReady |
| kube-proxy | Service networking | Services not reachable |
| Container runtime | Container execution | ContainerCreating stuck |
| CNI plugin | Pod networking | Pods can't communicate |

---

## Part 3: Essential Troubleshooting Commands

### 3.1 The Core Commands

Memorize these - you'll use them constantly:

```bash
# Status overview
k get pods                    # Pod status
k get pods -o wide            # Plus node and IP
k get events --sort-by='.lastTimestamp'  # Recent events

# Deep inspection
k describe pod <pod>          # Full details + events
k logs <pod>                  # Container stdout/stderr
k logs <pod> -c <container>   # Specific container
k logs <pod> --previous       # Previous container instance

# Interactive debugging
k exec -it <pod> -- sh        # Shell into container
k exec <pod> -- cat /etc/resolv.conf  # Run single command

# Resource status
k get <resource> -o yaml      # Full resource spec
k explain <resource.field>    # API documentation
```

### 3.2 Filtering and Searching

```bash
# Find problem pods
k get pods -A | grep -v Running
k get pods -A --field-selector=status.phase!=Running

# Find pods on specific node
k get pods -A --field-selector spec.nodeName=worker-1

# Find pods by label
k get pods -l app=nginx

# Search events for errors
k get events -A | grep -i error
k get events -A | grep -i fail
```

### 3.3 Resource Consumption

```bash
# Node resources
k top nodes
k describe node <node> | grep -A 5 "Allocated resources"

# Pod resources
k top pods
k top pods --containers

# Check resource requests/limits
k get pods -o custom-columns=\
'NAME:.metadata.name,CPU_REQ:.spec.containers[*].resources.requests.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory'
```

### 3.4 Network Debugging

```bash
# DNS resolution
k exec <pod> -- nslookup kubernetes
k exec <pod> -- cat /etc/resolv.conf

# Connectivity
k exec <pod> -- wget -qO- http://service-name
k exec <pod> -- nc -zv service-name 80

# Service endpoints
k get endpoints <service>
k get endpointslices -l kubernetes.io/service-name=<service>
```

---

## Part 4: Reading Pod Status

### 4.1 Pod Phase Meanings

```
┌──────────────────────────────────────────────────────────────┐
│                      POD PHASES                               │
│                                                               │
│   Pending ──────▶ Running ──────▶ Succeeded                  │
│      │              │                                         │
│      │              ▼                                         │
│      │           Failed                                       │
│      │              │                                         │
│      ▼              ▼                                         │
│   [Problem]    [Problem]                                      │
│                                                               │
│   Pending: Waiting for scheduling or image pull              │
│   Running: At least one container running                    │
│   Succeeded: All containers exited 0 (completed)             │
│   Failed: At least one container exited non-zero             │
│   Unknown: Node communication lost                           │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Common Pod Conditions

| Status | Meaning | First Check |
|--------|---------|-------------|
| **Pending** | Not scheduled yet | `k describe pod` - Events section |
| **ContainerCreating** | Image pull or volume mount | `k describe pod` - Events section |
| **Running** | Container(s) running | `k logs` for app issues |
| **CrashLoopBackOff** | Container crashing repeatedly | `k logs --previous` |
| **ImagePullBackOff** | Can't pull image | Image name, registry auth |
| **ErrImagePull** | Image pull failed | Same as above |
| **CreateContainerConfigError** | Config issue | ConfigMap/Secret missing |
| **OOMKilled** | Out of memory | Increase memory limit |
| **Evicted** | Node pressure | Node resources, pod priority |

### 4.3 Decoding CrashLoopBackOff

The most common troubleshooting scenario:

```bash
# Step 1: Check events
k describe pod <pod> | grep -A 20 Events

# Step 2: Check previous logs
k logs <pod> --previous

# Step 3: Check container exit code
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'

# Common exit codes:
# 0   - Success (shouldn't cause CrashLoop)
# 1   - Application error
# 137 - SIGKILL (OOMKilled or killed by system)
# 139 - SIGSEGV (segmentation fault)
# 143 - SIGTERM (graceful termination)
```

---

## Part 5: The Describe Output Deep Dive

### 5.1 Key Sections in describe pod

```bash
k describe pod <pod-name>
```

```
┌──────────────────────────────────────────────────────────────┐
│                 DESCRIBE OUTPUT SECTIONS                      │
│                                                               │
│ Section              What to Look For                         │
│ ─────────────────────────────────────────────────────────────│
│                                                               │
│ Status:              Current phase (Pending/Running/etc)      │
│                                                               │
│ Containers:          State, Ready, Restart Count              │
│                      Last State (for crash info)              │
│                      Image (verify it's correct)              │
│                                                               │
│ Conditions:          Ready, ContainersReady, PodScheduled     │
│                      False = problem                          │
│                                                               │
│ Volumes:             ConfigMaps, Secrets, PVCs                │
│                      Missing = pod won't start                │
│                                                               │
│ Events: ⭐           THE MOST IMPORTANT SECTION               │
│                      Shows what's happening/happened          │
│                      Errors appear here first                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Key Sections in describe node

```bash
k describe node <node-name>
```

| Section | What to Look For |
|---------|------------------|
| Conditions | Ready=True, MemoryPressure=False, DiskPressure=False |
| Capacity | Total CPU, memory, pods |
| Allocatable | Available for pods (after system reservation) |
| Allocated resources | Current usage and requests |
| Events | Evictions, pressure conditions |

---

## Part 6: Exam Troubleshooting Strategy

### 6.1 Three-Pass Applied to Troubleshooting

```
┌──────────────────────────────────────────────────────────────┐
│            THREE-PASS TROUBLESHOOTING STRATEGY                │
│                                                               │
│ PASS 1: Quick Fixes (1-3 min)                                │
│   • Obvious typos in YAML                                    │
│   • Wrong image name/tag                                     │
│   • Missing namespace in command                             │
│   • Label selector mismatch                                  │
│                                                               │
│ PASS 2: Standard Issues (4-6 min)                            │
│   • Missing ConfigMap/Secret                                 │
│   • Resource constraints                                     │
│   • Service selector mismatch                                │
│   • Network policy blocking traffic                          │
│                                                               │
│ PASS 3: Complex Issues (7+ min)                              │
│   • Control plane component failures                         │
│   • Node-level issues                                        │
│   • CNI/networking problems                                  │
│   • Storage/CSI issues                                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Time Management

For a 2-hour exam with troubleshooting worth 30%:
- ~36 minutes for troubleshooting questions
- Probably 3-4 troubleshooting scenarios
- ~9-12 minutes per scenario maximum

**Golden rule**: If you can't identify the problem in 3 minutes of investigation, flag it and move on.

### 6.3 Common Exam Patterns

| Scenario | Likely Issue | Quick Check |
|----------|--------------|-------------|
| Pod not starting | Image, ConfigMap/Secret | `k describe pod` |
| Service not accessible | Selector, endpoints | `k get endpoints` |
| Node NotReady | kubelet, runtime | `ssh node; systemctl status kubelet` |
| DNS not working | CoreDNS pods | `k -n kube-system get pods -l k8s-app=kube-dns` |
| Persistent volume pending | StorageClass, PV | `k describe pvc` |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Jumping to logs first | Miss scheduling/config issues | Always `describe` before `logs` |
| Not checking events | Miss critical error messages | Check events immediately |
| Fixing without diagnosis | Might not fix real issue | Always identify root cause |
| Forgetting `--previous` | Can't see why container crashed | Use for CrashLoopBackOff |
| Ignoring exit codes | Miss OOM vs app error | Check exit code for cause |
| Not checking all containers | Multi-container pods | Use `-c <container>` flag |

---

## Quiz

### Q1: First Command
A pod is in CrashLoopBackOff. What's the first command you should run?

<details>
<summary>Answer</summary>

`k describe pod <pod-name>` - Check the Events section first. It will show why the container is crashing (image issues, volume problems, etc.). Then check `k logs <pod> --previous` to see the crash logs.

</details>

### Q2: Event Retention
Why is it important to check events quickly after a problem occurs?

<details>
<summary>Answer</summary>

Kubernetes events are only retained for **1 hour by default**. If you don't check soon after an incident, the evidence may be gone. The Events section in `describe` output also truncates, so recent events may push out older relevant ones.

</details>

### Q3: Exit Codes
A container has exit code 137. What does this indicate?

<details>
<summary>Answer</summary>

Exit code 137 = 128 + 9 (SIGKILL). This usually means:
1. **OOMKilled** - Container exceeded memory limit
2. System killed the process (node pressure)

Check `k describe pod` for OOMKilled status and verify memory limits.

</details>

### Q4: Pending vs ContainerCreating
What's the difference between Pending and ContainerCreating status?

<details>
<summary>Answer</summary>

- **Pending**: Pod not yet scheduled to a node (scheduler issues, no suitable node, taints, resource constraints)
- **ContainerCreating**: Pod is scheduled, node is preparing to run it (pulling images, mounting volumes, setting up network)

Check `describe` Events to see which step is stuck.

</details>

### Q5: Multi-Container Logs
How do you view logs from a specific container in a multi-container pod?

<details>
<summary>Answer</summary>

```bash
k logs <pod-name> -c <container-name>

# List containers in pod
k get pod <pod-name> -o jsonpath='{.spec.containers[*].name}'
```

Without `-c`, kubectl shows logs from the first container (or errors if multiple exist).

</details>

### Q6: Node Troubleshooting
A node shows NotReady status. What's your systematic approach?

<details>
<summary>Answer</summary>

1. `k describe node <node>` - Check Conditions section
2. SSH to node if accessible
3. `systemctl status kubelet` - Is kubelet running?
4. `journalctl -u kubelet -f` - Check kubelet logs
5. `systemctl status containerd` (or docker) - Is runtime running?
6. Check network connectivity to control plane

</details>

---

## Hands-On Exercise: Systematic Troubleshooting Practice

### Scenario

You'll create several broken resources and practice systematic troubleshooting.

### Setup

```bash
# Create namespace
k create ns troubleshoot-lab

# Create a "broken" deployment - see if you can spot all issues
cat <<'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-app
  namespace: troubleshoot-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: broken-app
  template:
    metadata:
      labels:
        app: broken-app
    spec:
      containers:
      - name: app
        image: nginx:latestt
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "64Mi"
            cpu: "500m"
        volumeMounts:
        - name: config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: config
        configMap:
          name: nginx-config
EOF
```

### Tasks

Apply the troubleshooting methodology:

**1. Identify - What's wrong?**
```bash
k get pods -n troubleshoot-lab
# What status do you see?
```

**2. Isolate - Where's it wrong?**
```bash
k describe pod -n troubleshoot-lab -l app=broken-app
# Look at the Events section
```

**3. Diagnose - Why's it wrong?**
Find all issues (there are at least 2):
- Issue 1: _______________
- Issue 2: _______________

**4. Fix - Apply solutions**
```bash
# Fix issue 1: Image typo
k set image deployment/broken-app -n troubleshoot-lab app=nginx:latest

# Fix issue 2: Missing ConfigMap
k create configmap nginx-config -n troubleshoot-lab --from-literal=placeholder=true

# Verify
k get pods -n troubleshoot-lab -w
```

### Extended Challenge

Create more broken scenarios:

```bash
# Scenario 2: CrashLoopBackOff
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: crash-pod
  namespace: troubleshoot-lab
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'exit 1']
EOF

# Scenario 3: Pending pod
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pending-pod
  namespace: troubleshoot-lab
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "100Gi"
        cpu: "100"
EOF
```

Troubleshoot each one systematically.

### Success Criteria

- [ ] Identified image typo in deployment
- [ ] Identified missing ConfigMap
- [ ] Fixed deployment to Running state
- [ ] Explained why crash-pod is in CrashLoopBackOff
- [ ] Explained why pending-pod stays Pending

### Cleanup

```bash
k delete ns troubleshoot-lab
```

---

## Practice Drills

Practice these scenarios until they're automatic:

### Drill 1: Quick Status Check (30 sec)
```bash
# Task: Find all non-running pods across all namespaces
k get pods -A | grep -v Running
# Or: k get pods -A --field-selector=status.phase!=Running
```

### Drill 2: Recent Events (30 sec)
```bash
# Task: Show last 10 events sorted by time
k get events -A --sort-by='.lastTimestamp' | tail -10
```

### Drill 3: Pod Crash Investigation (2 min)
```bash
# Task: Full investigation of CrashLoopBackOff pod
k describe pod <pod>        # Step 1: Events
k logs <pod> --previous     # Step 2: Crash logs
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'  # Step 3: Exit code
```

### Drill 4: Node Health Check (1 min)
```bash
# Task: Check node health and resources
k get nodes
k describe node <node> | grep -A 5 Conditions
k top nodes
```

### Drill 5: Service Endpoint Check (1 min)
```bash
# Task: Verify service has endpoints
k get svc <service>
k get endpoints <service>
k get pods -l <service-selector>
```

### Drill 6: DNS Verification (1 min)
```bash
# Task: Verify DNS working in cluster
k run dnstest --image=busybox:1.36 --rm -it --restart=Never -- nslookup kubernetes
```

### Drill 7: Container Shell Access (30 sec)
```bash
# Task: Get shell in running container
k exec -it <pod> -- /bin/sh
# If sh not available: k exec -it <pod> -- /bin/bash
```

### Drill 8: Multi-Container Logs (1 min)
```bash
# Task: View logs from specific container and follow
k logs <pod> -c <container> -f
# List all containers: k get pod <pod> -o jsonpath='{.spec.containers[*].name}'
```

---

## Next Module

Continue to [Module 5.2: Application Failures](../module-5.2-application-failures/) to learn how to troubleshoot pods, deployments, and application-level issues.

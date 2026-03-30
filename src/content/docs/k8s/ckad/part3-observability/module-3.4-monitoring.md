---
title: "Module 3.4: Monitoring Applications"
slug: k8s/ckad/part3-observability/module-3.4-monitoring
sidebar:
  order: 4
lab:
  id: ckad-3.4-monitoring
  url: https://killercoda.com/kubedojo/scenario/ckad-3.4-monitoring
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[QUICK]` - Basic commands, conceptual understanding
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: Module 3.1 (Probes), understanding of resource requests/limits

---

## Why This Module Matters

Monitoring tells you how your applications are performing right now. While logging shows what happened, monitoring shows current state—CPU usage, memory consumption, and whether your app is struggling.

The CKAD exam tests:
- Using `kubectl top` for resource metrics
- Understanding resource usage vs. requests/limits
- Basic monitoring concepts (not full Prometheus setup)

> **The Dashboard Analogy**
>
> Monitoring is like a car's dashboard. You don't need to look under the hood to know you're low on fuel (memory) or the engine is overheating (high CPU). A quick glance tells you if everything's normal or if you need to take action.

---

## Metrics Server

Kubernetes doesn't collect metrics by default. The **Metrics Server** is a lightweight component that provides resource metrics.

### Check If Metrics Server Is Running

```bash
# Check for metrics-server deployment
k get deployment -n kube-system metrics-server

# Or check if `top` works
k top nodes
```

### What Metrics Server Provides

- Current CPU and memory usage per node
- Current CPU and memory usage per pod
- Data for Horizontal Pod Autoscaler decisions

### What It Doesn't Provide

- Historical data
- Application-level metrics
- Custom metrics

---

## kubectl top Commands

### Node Metrics

```bash
# All nodes
k top nodes

# Output:
# NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# node-1     250m         12%    1024Mi          25%
# node-2     500m         25%    2048Mi          50%
```

### Pod Metrics

```bash
# All pods in current namespace
k top pods

# All pods in all namespaces
k top pods -A

# Pods in specific namespace
k top pods -n kube-system

# Sort by CPU
k top pods --sort-by=cpu

# Sort by memory
k top pods --sort-by=memory

# Specific pod
k top pod my-pod
```

### Container Metrics

```bash
# Show metrics per container
k top pods --containers

# Output:
# POD          NAME      CPU(cores)   MEMORY(bytes)
# my-pod       app       100m         128Mi
# my-pod       sidecar   10m          32Mi
```

---

## Understanding Metrics Output

### CPU Units

| Value | Meaning |
|-------|---------|
| `1` | 1 full CPU core |
| `1000m` | 1000 millicores = 1 core |
| `500m` | 0.5 cores (half a core) |
| `100m` | 0.1 cores (10% of a core) |

### Memory Units

| Value | Meaning |
|-------|---------|
| `128Mi` | 128 mebibytes |
| `1Gi` | 1 gibibyte (1024 Mi) |
| `256M` | 256 megabytes |

### Reading the Output

```
NAME        CPU(cores)   CPU%     MEMORY(bytes)   MEMORY%
my-pod      100m         10%      256Mi           12%
```

- **100m CPU**: Pod is using 100 millicores (10% of one core)
- **256Mi MEMORY**: Pod is using 256 mebibytes of RAM
- **Percentages**: Based on node capacity (nodes) or requests (pods)

---

## Metrics vs Requests/Limits

### Comparison

```yaml
resources:
  requests:
    cpu: "100m"      # Guaranteed minimum
    memory: "128Mi"
  limits:
    cpu: "500m"      # Maximum allowed
    memory: "256Mi"
```

```bash
# Actual usage from metrics
k top pod my-pod
# CPU: 50m, Memory: 100Mi

# Interpretation:
# - Using 50m CPU (within 100m request, well under 500m limit)
# - Using 100Mi RAM (within 128Mi request, under 256Mi limit)
```

### Health Check with Metrics

```bash
# Check if pods are near their limits
k top pods

# Compare with defined limits
k get pod my-pod -o jsonpath='{.spec.containers[*].resources}'
```

---

## Monitoring Patterns

### Quick Health Check

```bash
# Node status
k top nodes

# Pod status sorted by resource usage
k top pods --sort-by=cpu
k top pods --sort-by=memory
```

### Find Resource Hogs

```bash
# Top CPU consumers
k top pods -A --sort-by=cpu | head -10

# Top memory consumers
k top pods -A --sort-by=memory | head -10
```

### Container-Level Analysis

```bash
# See which container in pod uses most resources
k top pods --containers -l app=myapp
```

---

## Resource Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                  Resource Usage Levels                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Memory Usage Example:                                      │
│                                                             │
│  |                                                          │
│  |  ▓▓▓▓▓▓▓▓▓▓ Limit: 256Mi (max before OOMKill)           │
│  |                                                          │
│  |  ████████ Request: 128Mi (guaranteed)                   │
│  |                                                          │
│  |  ████ Current: 64Mi (from k top)                        │
│  |                                                          │
│  └──────────────────────────────────────────────           │
│                                                             │
│  Status: Healthy (usage < request)                         │
│                                                             │
│  ─────────────────────────────────────────────             │
│                                                             │
│  |                                                          │
│  |  ▓▓▓▓▓▓▓▓▓▓ Limit: 256Mi                                │
│  |                                                          │
│  |  ████████████████ Current: 200Mi (from k top)           │
│  |                                                          │
│  |  ████████ Request: 128Mi                                │
│  |                                                          │
│  └──────────────────────────────────────────────           │
│                                                             │
│  Status: Warning (usage > request, approaching limit)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Exam-Relevant Concepts

### What You Need to Know

1. **`kubectl top`** - View current resource usage
2. **Metrics Server** - Required for `kubectl top` to work
3. **Resource interpretation** - Understanding millicores and memory units

### What You Don't Need to Know (for CKAD)

- Prometheus setup and configuration
- Grafana dashboards
- Custom metrics and metrics APIs
- PromQL queries

---

## Did You Know?

- **Metrics Server samples every 15 seconds** by default. The data isn't real-time but very recent.

- **`kubectl top` shows current usage, not historical.** For trends, you need external monitoring tools.

- **HPA (Horizontal Pod Autoscaler) relies on Metrics Server** to make scaling decisions based on CPU/memory usage.

- **Metrics Server stores data in memory only.** When it restarts, all historical data is lost.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Running `k top` without metrics server | Command fails | Install metrics server first |
| Confusing requests with actual usage | Wrong capacity planning | Use `k top` for real usage |
| Ignoring high memory pods | OOMKill surprise | Sort by memory, watch trends |
| Not checking container-level | Miss sidecar issues | Use `--containers` flag |
| Expecting historical data | `k top` only shows now | Use Prometheus for history |

---

## Quiz

1. **What command shows CPU and memory usage per pod?**
   <details>
   <summary>Answer</summary>
   `kubectl top pods`
   </details>

2. **What does 250m CPU mean?**
   <details>
   <summary>Answer</summary>
   250 millicores, which equals 0.25 of a CPU core (25% of one core).
   </details>

3. **How do you see resource usage per container in multi-container pods?**
   <details>
   <summary>Answer</summary>
   `kubectl top pods --containers`
   </details>

4. **What happens if metrics server isn't installed?**
   <details>
   <summary>Answer</summary>
   `kubectl top` fails with an error because there's no source of metrics data.
   </details>

---

## Hands-On Exercise

**Task**: Monitor resource usage of running applications.

**Setup:**
```bash
# Create a deployment with known resource usage
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: monitor-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: monitor-demo
  template:
    metadata:
      labels:
        app: monitor-demo
    spec:
      containers:
      - name: nginx
        image: nginx
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 100m
            memory: 128Mi
EOF
```

**Part 1: Basic Monitoring**
```bash
# Check if metrics server is running
k top nodes

# View pod metrics
k top pods -l app=monitor-demo

# Sort by CPU
k top pods --sort-by=cpu
```

**Part 2: Compare with Requests**
```bash
# Get resource requests
k get pods -l app=monitor-demo -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}'

# Compare with actual usage
k top pods -l app=monitor-demo
```

**Cleanup:**
```bash
k delete deploy monitor-demo
```

---

## Practice Drills

### Drill 1: Node Metrics (Target: 1 minute)

```bash
# Check node resource usage
k top nodes

# Identify which node has highest CPU
k top nodes --sort-by=cpu
```

### Drill 2: Pod Metrics (Target: 2 minutes)

```bash
# Create test pods
k run drill2a --image=nginx
k run drill2b --image=nginx

# Check their metrics
k top pods

# Cleanup
k delete pod drill2a drill2b
```

### Drill 3: Container Metrics (Target: 2 minutes)

```bash
# Create multi-container pod
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: nginx
    image: nginx
  - name: sidecar
    image: busybox
    command: ['sleep', '3600']
EOF

# View per-container metrics
k top pods drill3 --containers

# Cleanup
k delete pod drill3
```

### Drill 4: Sorted Output (Target: 2 minutes)

```bash
# Get pods sorted by memory usage
k top pods -A --sort-by=memory

# Get pods sorted by CPU usage
k top pods -A --sort-by=cpu
```

### Drill 5: System Pods (Target: 2 minutes)

```bash
# Check kube-system pod resource usage
k top pods -n kube-system

# Sort by CPU to find most active
k top pods -n kube-system --sort-by=cpu
```

### Drill 6: Full Monitoring Workflow (Target: 4 minutes)

**Scenario**: Investigate high resource usage in a deployment.

```bash
# Create deployment with multiple replicas
k create deploy drill6 --image=nginx --replicas=5

# Wait for pods
k get pods -l app=drill6 -w

# Check overall deployment resource usage
k top pods -l app=drill6

# Find highest consumer
k top pods -l app=drill6 --sort-by=cpu

# Check container level
k top pods -l app=drill6 --containers

# Compare to node capacity
k top nodes

# Cleanup
k delete deploy drill6
```

---

## Next Module

[Module 3.5: API Deprecations](../module-3.5-api-deprecations/) - Handle API version changes and deprecations.

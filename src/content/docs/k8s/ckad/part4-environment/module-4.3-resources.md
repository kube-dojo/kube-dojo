---
title: "Module 4.3: Resource Requirements and Limits"
slug: k8s/ckad/part4-environment/module-4.3-resources
sidebar:
  order: 3
lab:
  id: ckad-4.3-resources
  url: https://killercoda.com/kubedojo/scenario/ckad-4.3-resources
  duration: "30 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical for production, affects scheduling
>
> **Time to Complete**: 35-45 minutes
>
> **Prerequisites**: Module 1.1 (Pods), understanding of CPU and memory concepts

---

## Learning Outcomes

After completing this module, you will be able to:
- **Configure** resource requests and limits for CPU and memory in pod specifications
- **Diagnose** OOMKilled and CPU throttling issues by correlating limits with observed behavior
- **Design** resource allocations that balance performance, cost, and scheduling reliability
- **Explain** how requests affect scheduling and limits affect runtime enforcement

---

## Why This Module Matters

Resource requests and limits control how much CPU and memory your containers can use. Without them, a single container could consume all node resources, starving other pods. Proper resource management is essential for cluster stability.

The CKAD exam tests:
- Setting requests and limits
- Understanding the difference between them
- What happens when limits are exceeded
- LimitRanges and ResourceQuotas

> **The Apartment Lease Analogy**
>
> Resource requests are like a guaranteed parking spot—you're assured that space. Limits are like the building's max occupancy—you can use more space temporarily, but there's a hard cap. If you exceed it (memory), you get evicted (OOMKilled). If the building is full (node), new tenants (pods) wait until space opens.

---

## Requests vs Limits

### Definitions

| Term | Meaning | When Enforced |
|------|---------|---------------|
| **Request** | Guaranteed minimum resources | Scheduling time |
| **Limit** | Maximum allowed resources | Runtime |

### How They Work

```
┌─────────────────────────────────────────────────────────────┐
│                 Resource Request vs Limit                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Memory:                                                    │
│  ├── Request: 256Mi (guaranteed, used for scheduling)      │
│  ├── Actual usage can vary between 0 and Limit             │
│  └── Limit: 512Mi (hard cap, exceeding = OOMKill)          │
│                                                             │
│  CPU:                                                       │
│  ├── Request: 100m (guaranteed, used for scheduling)       │
│  ├── Can burst above request if node has spare capacity    │
│  └── Limit: 500m (throttled if exceeded, NOT killed)       │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │                                                    │    │
│  │  0        Request      Actual       Limit          │    │
│  │  |           |           |            |            │    │
│  │  ├───────────┼───────────┼────────────┤            │    │
│  │  │ guaranteed│  burstable │  max      │            │    │
│  │  └───────────┴───────────┴────────────┘            │    │
│  │                                                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Setting Resources

### Basic Syntax

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

### Units

**CPU:**
| Value | Meaning |
|-------|---------|
| `1` | 1 CPU core |
| `1000m` | 1000 millicores = 1 core |
| `500m` | 0.5 cores |
| `100m` | 0.1 cores (10%) |

**Memory:**
| Value | Meaning |
|-------|---------|
| `128Mi` | 128 mebibytes (1024-based) |
| `1Gi` | 1 gibibyte = 1024 Mi |
| `128M` | 128 megabytes (1000-based) |
| `1G` | 1 gigabyte = 1000 M |

---

## What Happens at Limits

> **Pause and predict**: A pod has `requests.cpu: 100m` and `limits.cpu: 500m`. The node has 1 CPU core available. Can this pod use 500m? What if three other pods on the same node also have `limits.cpu: 500m`?

### Memory Limit Exceeded

```
Container uses > limit → OOMKilled → Container restarts
```

```bash
# Check if pod was OOMKilled
k describe pod my-pod | grep -A5 "Last State"
k get pod my-pod -o jsonpath='{.status.containerStatuses[0].lastState}'
```

### CPU Limit Exceeded

```
Container uses > limit → Throttled (slowed down, NOT killed)
```

CPU throttling is invisible to the container—it just runs slower.

---

## QoS Classes

Kubernetes assigns Quality of Service classes based on resource settings:

| QoS Class | Condition | Eviction Priority |
|-----------|-----------|-------------------|
| **Guaranteed** | Requests = Limits for all containers | Last (protected) |
| **Burstable** | Requests < Limits (or only one set) | Middle |
| **BestEffort** | No requests or limits set | First (evicted first) |

> **Stop and think**: A pod has requests but no limits set. Which QoS class will it receive — Guaranteed, Burstable, or BestEffort? What about a pod with limits but no requests?

### Guaranteed Example

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"    # Same as request
    cpu: "100m"        # Same as request
```

### Burstable Example

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"    # Higher than request
    cpu: "500m"        # Higher than request
```

### BestEffort Example

```yaml
resources: {}  # No resources defined
```

---

## Scheduling Impact

### Pod Won't Schedule

If no node has enough **available** resources (capacity - allocated requests):

```bash
# Check why pod is Pending
k describe pod my-pod

# Events will show:
# 0/3 nodes are available: 3 Insufficient cpu.
# or
# 0/3 nodes are available: 3 Insufficient memory.
```

### Check Node Capacity

```bash
# Node capacity and allocatable
k describe node NODE_NAME | grep -A5 Capacity
k describe node NODE_NAME | grep -A5 Allocatable

# Already allocated
k describe node NODE_NAME | grep -A10 "Allocated resources"
```

---

## LimitRange

Namespace-level defaults and constraints:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-memory-limits
spec:
  limits:
  - default:          # Default limits if not specified
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:   # Default requests if not specified
      cpu: "100m"
      memory: "256Mi"
    max:              # Maximum allowed
      cpu: "2"
      memory: "2Gi"
    min:              # Minimum allowed
      cpu: "50m"
      memory: "64Mi"
    type: Container
```

```bash
# View LimitRange
k get limitrange
k describe limitrange cpu-memory-limits
```

---

## ResourceQuota

Namespace-level total resource limits:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
spec:
  hard:
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
    pods: "10"
```

```bash
# View quota usage
k get resourcequota
k describe resourcequota compute-quota
```

---

## Quick Reference

```bash
# Set resources in pod spec
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"

# Check pod resources
k get pod POD -o jsonpath='{.spec.containers[*].resources}'

# Check node capacity
k describe node NODE | grep -A10 "Allocated"

# Check QoS class
k get pod POD -o jsonpath='{.status.qosClass}'
```

---

## Did You Know?

- **CPU is compressible, memory is not.** If you exceed CPU limits, you're throttled. If you exceed memory limits, you're killed.

- **Requests affect scheduling, limits affect runtime.** A pod with 1Gi memory request won't schedule on a node with only 512Mi available, even if the container only uses 100Mi.

- **Kubernetes doesn't prevent memory overcommit.** If all pods burst to their limits simultaneously, the node runs out of memory and starts killing pods.

- **The `cpu: 0.1` syntax** is equivalent to `cpu: 100m` (100 millicores).

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No resources set | BestEffort pods evicted first | Always set requests |
| Request > Limit | Invalid, rejected | Request must be ≤ Limit |
| Memory too low | OOMKilled constantly | Profile app, increase limits |
| CPU too low | App runs slowly | Monitor with `k top`, adjust |
| Same as node capacity | No room for system pods | Leave headroom |

---

## Quiz

1. **A pod keeps getting OOMKilled — you see `Last State: Terminated, Reason: OOMKilled` in `kubectl describe`. The pod has `limits.memory: 128Mi`. The developer says "but the app only uses 80MB." What is likely happening and how do you fix it?**
   <details>
   <summary>Answer</summary>
   The application likely uses more memory than the developer thinks. Memory usage includes the runtime overhead (JVM heap, Go GC, Python interpreter), shared libraries, and any temporary allocations. The developer might be measuring only heap or RSS, not the full container memory. Use `kubectl top pod` to see actual usage approaching the limit. The fix is to increase the memory limit based on observed peak usage (with ~25% headroom), or profile the application to find memory leaks. Also check if the container runs multiple processes — each contributes to the container's memory total. The 128Mi limit might be appropriate for the app code but not for the runtime + app combined.
   </details>

2. **A pod is stuck in Pending state. `kubectl describe` shows: "0/3 nodes are available: 3 Insufficient cpu." The pod requests 2 CPU cores. Each node has 4 cores but already runs several pods. What are your options to get this pod scheduled?**
   <details>
   <summary>Answer</summary>
   The scheduler can't find a node where allocatable CPU minus already-requested CPU is >= 2 cores. Options: (1) Reduce the pod's CPU request if the application doesn't truly need 2 cores — check actual usage with `kubectl top` on similar pods. (2) Scale down or delete other pods to free up capacity. (3) Add more nodes to the cluster. (4) Check if other pods are over-requesting — their requests might be higher than actual usage, wasting schedulable capacity. Run `kubectl describe node` on each node and look at "Allocated resources" to see where CPU is committed. Requests affect scheduling, not actual usage, so over-requesting is a common cause of scheduling failures.
   </details>

3. **A deployment runs 5 replicas with no resource requests or limits set. During a node memory pressure event, all 5 pods are evicted before pods from other deployments. Why were these pods targeted first?**
   <details>
   <summary>Answer</summary>
   Pods without resource requests or limits receive the BestEffort QoS class, which has the lowest priority during eviction. When a node runs low on memory, the kubelet evicts pods in QoS order: BestEffort first, then Burstable, then Guaranteed last. The other deployments likely had requests and/or limits set, giving them Burstable or Guaranteed QoS class. The fix is to always set at least resource requests on production pods. Setting requests equal to limits gives Guaranteed QoS (highest protection), while having requests lower than limits gives Burstable QoS (middle tier).
   </details>

4. **A namespace has a LimitRange with `default.cpu: 200m` and `default.memory: 256Mi`. A developer creates a pod without specifying any resources. They later notice the pod has resource limits they didn't set. What happened, and how does this interact with ResourceQuota?**
   <details>
   <summary>Answer</summary>
   LimitRange automatically injects default resource requests and limits into containers that don't specify them. The developer's pod received `limits.cpu: 200m` and `limits.memory: 256Mi` from the LimitRange defaults. If a ResourceQuota also exists in the namespace, every pod must have resource requests (so the quota can track usage). The LimitRange defaults ensure pods aren't rejected for missing resource specifications when a ResourceQuota is active. Check with `kubectl get pod -o jsonpath='{.spec.containers[0].resources}'` to see the injected values, and `kubectl describe limitrange` to see the namespace defaults.
   </details>

---

## Hands-On Exercise

**Task**: Configure and observe resource behavior.

**Part 1: Basic Resources**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "64Mi"
        cpu: "50m"
      limits:
        memory: "128Mi"
        cpu: "100m"
EOF

# Check QoS class
k get pod resource-demo -o jsonpath='{.status.qosClass}'
echo

# Check resources
k get pod resource-demo -o jsonpath='{.spec.containers[0].resources}'
```

**Part 2: OOMKill Demo**
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: memory-hog
spec:
  containers:
  - name: app
    image: polinux/stress
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "200M", "--vm-hang", "1"]
    resources:
      limits:
        memory: "100Mi"
EOF

# Watch it get OOMKilled
k get pod memory-hog -w

# Check reason
k describe pod memory-hog | grep -A3 "Last State"
```

**Cleanup:**
```bash
k delete pod resource-demo memory-hog
```

---

## Practice Drills

### Drill 1: Basic Resources (Target: 2 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill1
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "200m"
        memory: "256Mi"
EOF

k get pod drill1 -o jsonpath='{.spec.containers[0].resources}'
echo
k delete pod drill1
```

### Drill 2: Check QoS Class (Target: 2 minutes)

```bash
# Guaranteed (requests = limits)
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill2
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "100m"
        memory: "128Mi"
EOF

k get pod drill2 -o jsonpath='{.status.qosClass}'
echo
k delete pod drill2
```

### Drill 3: Generate Pod with Resources (Target: 2 minutes)

```bash
# Use --dry-run to generate, then add resources
k run drill3 --image=nginx --dry-run=client -o yaml > /tmp/drill3.yaml

# Edit to add resources (in exam, use vim)
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: drill3
spec:
  containers:
  - name: drill3
    image: nginx
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 100m
        memory: 128Mi
EOF

k get pod drill3 -o yaml | grep -A8 resources
k delete pod drill3
```

### Drill 4: Deployment with Resources (Target: 3 minutes)

```bash
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill4
spec:
  replicas: 2
  selector:
    matchLabels:
      app: drill4
  template:
    metadata:
      labels:
        app: drill4
    spec:
      containers:
      - name: nginx
        image: nginx
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "100m"
            memory: "128Mi"
EOF

k get pods -l app=drill4
k delete deploy drill4
```

### Drill 5: Check Node Resources (Target: 2 minutes)

```bash
# Get node name
NODE=$(k get nodes -o jsonpath='{.items[0].metadata.name}')

# Check capacity
k describe node $NODE | grep -A5 "Capacity:"

# Check allocatable
k describe node $NODE | grep -A5 "Allocatable:"

# Check allocated
k describe node $NODE | grep -A10 "Allocated resources:"
```

### Drill 6: LimitRange (Target: 4 minutes)

```bash
# Create namespace with LimitRange
k create ns drill6

cat << 'EOF' | k apply -n drill6 -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
spec:
  limits:
  - default:
      cpu: "200m"
      memory: "256Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
EOF

# Create pod without resources
k run drill6-pod --image=nginx -n drill6

# Check defaults were applied
k get pod drill6-pod -n drill6 -o jsonpath='{.spec.containers[0].resources}'
echo

# Cleanup
k delete ns drill6
```

---

## Next Module

[Module 4.4: SecurityContexts](../module-4.4-securitycontext/) - Configure pod and container security settings.

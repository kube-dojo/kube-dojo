---
revision_pending: true
title: "Module 2.5: Resource Management"
slug: k8s/cka/part2-workloads-scheduling/module-2.5-resource-management
sidebar:
  order: 6
lab:
  id: cka-2.5-resource-management
  url: https://killercoda.com/kubedojo/scenario/cka-2.5-resource-management
  duration: "40 min"
  difficulty: intermediate
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical for production workloads
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.1 (Pods), Module 2.2 (Deployments)

---

## What You'll Be Able to Do

After this module, you will be able to:
- **Configure** resource requests and limits for CPU and memory and explain how they affect scheduling
- **Implement** LimitRanges and ResourceQuotas for namespace-level governance
- **Diagnose** resource-related failures (OOMKilled, CPU throttling, Pending due to insufficient resources)
- **Design** a resource strategy that balances cluster utilization with application reliability

---

## Why This Module Matters

In production, containers compete for resources. Without proper configuration:
- A single pod can starve others
- Nodes become overcommitted
- Applications crash randomly
- Debugging becomes a nightmare

Resource management is essential for cluster stability. The CKA exam tests your understanding of requests, limits, QoS classes, and how they affect scheduling.

> **The Hotel Room Analogy**
>
> Think of a Kubernetes node like a hotel. **Requests** are like room reservations—guaranteed capacity you've booked. **Limits** are maximum occupancy rules—you can't exceed them. Without reservations (requests), guests fight for rooms. Without limits, one party takes over the entire hotel. Good resource management ensures everyone gets what they need.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Configure CPU and memory requests and limits
- Understand how requests affect scheduling
- Understand how limits enforce boundaries
- Work with QoS classes
- Use LimitRanges and ResourceQuotas
- Resize pod resources in-place (K8s 1.35+)

---

## Did You Know?

- **In-Place Pod Resize is now GA**: In Kubernetes 1.35, you can update CPU and memory requests and limits for running Pods through the `/resize` subresource. Whether a container restarts depends on its `resizePolicy` and the kind of resource change.

---

## Part 1: Requests and Limits

### 1.1 The Basics

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
      requests:          # Minimum guaranteed resources
        memory: "128Mi"
        cpu: "100m"
      limits:            # Maximum allowed resources
        memory: "256Mi"
        cpu: "500m"
```

### 1.2 Requests vs Limits

| Aspect | Requests | Limits |
|--------|----------|--------|
| Purpose | Scheduling guarantee | Hard cap |
| When used | Scheduler deciding placement | Container runtime enforcement |
| Underutilized | Other pods can use slack | N/A |
| Exceeded | N/A | Container killed (memory) or throttled (CPU) |

```
┌────────────────────────────────────────────────────────────────┐
│                    Requests vs Limits                           │
│                                                                 │
│   Memory: 128Mi request, 256Mi limit                           │
│                                                                 │
│   0        128Mi      256Mi                  Node Memory       │
│   ├─────────┼──────────┼───────────────────────────────────►   │
│   │         │          │                                       │
│   │ Reserved│ Can grow │ OOMKilled if exceeded                │
│   │(guara-  │ into this│                                       │
│   │ nteed)  │ space    │                                       │
│                                                                 │
│   CPU: 100m request, 500m limit                                │
│                                                                 │
│   0       100m       500m                    Node CPU          │
│   ├─────────┼──────────┼───────────────────────────────────►   │
│   │         │          │                                       │
│   │ Reserved│ Can burst│ Throttled (not killed)               │
│   │         │ up to    │                                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 Resource Units

**CPU** (measured in cores):

| Value | Meaning |
|-------|---------|
| `1` | 1 CPU core |
| `1000m` | 1 CPU core (millicores) |
| `100m` | 0.1 CPU core (100 millicores) |
| `500m` | 0.5 CPU core |

**Memory** (measured in bytes):

| Value | Meaning |
|-------|---------|
| `128Mi` | 128 mebibytes (128 × 1024² bytes) |
| `1Gi` | 1 gibibyte |
| `256M` | 256 megabytes (256 × 1000² bytes) |

> **Gotcha**: `Mi` and `M` are different units. `Mi` uses powers of two, while `M` uses powers of ten, so the same numeric prefix represents different byte counts. Use `Mi` consistently when you want binary units.

---

## Part 2: How Requests Affect Scheduling

### 2.1 Scheduling Decision

[The scheduler places pods on nodes with sufficient **allocatable** resources](https://v1-35.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/):

```bash
# Check node allocatable resources
kubectl describe node <node-name> | grep -A6 "Allocatable"

# Allocatable:
#   cpu:                2
#   memory:             4Gi
#   pods:               110
```

```
┌────────────────────────────────────────────────────────────────┐
│                   Scheduling Decision                           │
│                                                                 │
│   Node Capacity: 4Gi memory                                    │
│   Already Requested: 3Gi                                       │
│   Available: 1Gi                                               │
│                                                                 │
│   Pod A requests 2Gi memory                                    │
│   → Cannot schedule (2Gi > 1Gi available)                      │
│   → Pod stays Pending                                          │
│                                                                 │
│   Pod B requests 500Mi memory                                  │
│   → Can schedule (500Mi < 1Gi available)                       │
│   → Pod placed on node                                         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Pending Pods Due to Resources

```bash
# Create pod with huge request
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: big-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "100Gi"
EOF

# Check status
kubectl get pod big-pod
# NAME      READY   STATUS    RESTARTS   AGE
# big-pod   0/1     Pending   0          10s

# Check why
kubectl describe pod big-pod | grep -A5 "Events"
# Warning  FailedScheduling  Insufficient memory
```

### 2.3 Resource Pressure

```bash
# Check node resource pressure
kubectl describe node <node-name> | grep -A10 "Conditions"
# MemoryPressure    False    KubeletHasSufficientMemory
# DiskPressure      False    KubeletHasNoDiskPressure
# PIDPressure       False    KubeletHasSufficientPID
```

---

## Part 3: How Limits Are Enforced

> **Pause and predict**: Two containers are running on the same node. Container A exceeds its CPU limit. Container B exceeds its memory limit. One of them gets killed; the other just slows down. Which is which, and why does Kubernetes treat CPU and memory differently?

### 3.1 CPU Limits (Throttling)

When a container exceeds CPU limits:
- [CPU usage is **throttled**](https://v1-35.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- Process slows down but continues
- No container termination

```bash
# Container trying to use 2 CPUs with 500m limit
# Gets throttled to 500m worth of CPU time
```

### 3.2 Memory Limits (OOMKilled)

When a container exceeds memory limits:
- [Container is **killed** (OOMKilled)](https://v1-35.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- Pod may restart based on restartPolicy
- You see `OOMKilled` in pod status

```bash
# Check for OOMKilled
kubectl describe pod <pod-name> | grep -A5 "Last State"
# Last State:  Terminated
#   Reason:    OOMKilled
#   Exit Code: 137

# Check events
kubectl get events --field-selector reason=OOMKilling
```

### 3.3 Memory Hog Demo

```yaml
# Pod that will be OOMKilled
apiVersion: v1
kind: Pod
metadata:
  name: memory-hog
spec:
  containers:
  - name: memory-hog
    image: polinux/stress
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "200M", "--vm-hang", "1"]
    resources:
      limits:
        memory: "100Mi"     # Limit is less than 200M stress allocates
```

> **War Story: The Silent Memory Leak**
>
> A pod that restarts without obvious application errors may be hitting its memory limit and showing `OOMKilled` in `kubectl describe pod`; resource limits can contain the blast radius while you investigate leaks or traffic spikes.

---

## Part 4: QoS Classes

> **Pause and predict**: A pod has `requests: {cpu: 100m, memory: 128Mi}` and `limits: {memory: 256Mi}` (no CPU limit). What QoS class will it get -- Guaranteed, Burstable, or BestEffort? What happens if it tries to use 300Mi of memory?

### 4.1 The Three QoS Classes

Kubernetes assigns QoS classes based on resource configuration:

| QoS Class | Condition | Eviction Priority |
|-----------|-----------|-------------------|
| **Guaranteed** | requests = limits for all containers | Last (lowest priority) |
| **Burstable** | At least one request or limit set | Middle |
| **BestEffort** | No requests or limits | First (highest priority) |

### 4.2 Guaranteed

[All containers must have requests = limits for both CPU and memory](https://v1-35.docs.kubernetes.io/docs/concepts/workloads/pods/pod-qos/):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"    # Same as request
        cpu: "100m"        # Same as request
```

```bash
# Check QoS class
kubectl get pod guaranteed-pod -o jsonpath='{.status.qosClass}'
# Guaranteed
```

### 4.3 Burstable

At least one request or limit, but not Guaranteed:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        memory: "128Mi"
      limits:
        memory: "256Mi"    # Different from request
```

### 4.4 BestEffort

No resource specifications:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod
spec:
  containers:
  - name: app
    image: nginx
    # No resources section
```

### 4.5 QoS and Eviction

When a node runs low on resources, kubelet evicts pods:

```
Eviction Order (first to last):
1. BestEffort pods exceeding request
2. Burstable pods exceeding request
3. Burstable pods below request
4. Guaranteed pods (last resort)
```

> **Did You Know?**
>
> Limits-only pods are still **not** automatically Guaranteed in the general case. [Guaranteed requires both CPU and memory requests and limits, with matching values for each container.](https://v1-35.docs.kubernetes.io/docs/concepts/workloads/pods/pod-qos/)

---

## Part 5: LimitRanges

### 5.1 What Is a LimitRange?

[LimitRange sets default/min/max resource constraints per namespace](https://v1-35.docs.kubernetes.io/docs/concepts/policy/limit-range/):

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-memory-limits
  namespace: development
spec:
  limits:
  - type: Container
    default:           # Default limits if not specified
      cpu: "500m"
      memory: "256Mi"
    defaultRequest:    # Default requests if not specified
      cpu: "100m"
      memory: "128Mi"
    min:               # Minimum allowed
      cpu: "50m"
      memory: "64Mi"
    max:               # Maximum allowed
      cpu: "1"
      memory: "1Gi"
```

### 5.2 LimitRange Effects

```bash
# Apply LimitRange to namespace
kubectl apply -f limitrange.yaml

# Now create pod without resources
kubectl run test --image=nginx -n development

# Check - default resources were applied!
kubectl get pod test -n development -o yaml | grep -A10 resources
```

### 5.3 LimitRange Types

| Type | Applies To |
|------|------------|
| `Container` | Individual containers |
| `Pod` | Sum of all containers in pod |
| `PersistentVolumeClaim` | PVC storage requests |

---

## Part 6: ResourceQuotas

> **Stop and think**: You create a ResourceQuota in a namespace with `pods: 10` and `requests.cpu: 4`. A developer tries to create a pod without specifying any resource requests. Will it succeed? Why or why not?

### 6.1 What Is a ResourceQuota?

[ResourceQuota limits total resources consumed in a namespace](https://v1-35.docs.kubernetes.io/docs/concepts/policy/resource-quotas/):

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: development
spec:
  hard:
    requests.cpu: "4"           # Total CPU requests
    requests.memory: "8Gi"      # Total memory requests
    limits.cpu: "8"             # Total CPU limits
    limits.memory: "16Gi"       # Total memory limits
    pods: "10"                  # Total number of pods
    persistentvolumeclaims: "5" # Total PVCs
```

### 6.2 Checking Quota Usage

```bash
# View quota
kubectl get resourcequota -n development

# Detailed view
kubectl describe resourcequota compute-quota -n development
# Name:            compute-quota
# Resource         Used    Hard
# --------         ----    ----
# limits.cpu       2       8
# limits.memory    4Gi     16Gi
# pods             5       10
```

### 6.3 Quota Enforcement

```bash
# If quota exceeded
kubectl run new-pod --image=nginx -n development
# Error: exceeded quota: compute-quota, requested: pods=1, used: pods=10, limited: pods=10
```

> **Exam Tip**
>
> If a namespace has compute ResourceQuotas for CPU or memory, new Pods must specify requests or limits for those resources, or receive them from a LimitRange; otherwise admission may be rejected.

---

## Part 7: Practical Resource Configuration

### 7.1 Choosing Values

```bash
# 1. Profile your application
# Run locally or in test environment to measure actual usage

# 2. Set requests slightly above average usage
# Ensures pod gets scheduled

# 3. Set limits to handle bursts
# Allow headroom for spikes but protect the node
```

### 7.2 Common Patterns

| Application Type | Request | Limit | Ratio |
|-----------------|---------|-------|-------|
| Web server | 100m CPU, 128Mi | 500m CPU, 512Mi | 1:5, 1:4 |
| Background worker | 200m CPU, 256Mi | 1 CPU, 1Gi | 1:5, 1:4 |
| Database | 500m CPU, 1Gi | 2 CPU, 4Gi | 1:4, 1:4 |
| Cache | 100m CPU, 512Mi | 200m CPU, 1Gi | 1:2, 1:2 |

### 7.3 Commands for Resource Setting

```bash
# Create with resources using a manifest
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
EOF

# Update existing deployment
kubectl set resources deployment/nginx \
  -c nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=256Mi"

# Check resource usage (requires metrics-server)
kubectl top pods
kubectl top nodes
```

---

## Part 8: Monitoring Resources

### 8.1 kubectl top ([Requires metrics-server](https://github.com/kubernetes-sigs/metrics-server))

```bash
# Check node resource usage
kubectl top nodes
# NAME    CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# node1   250m         12%    1200Mi          60%

# Check pod resource usage
kubectl top pods
kubectl top pods -n kube-system
kubectl top pod nginx --containers
```

### 8.2 Describe Commands

```bash
# Node capacity and allocatable
kubectl describe node <node-name> | grep -A10 "Capacity"
kubectl describe node <node-name> | grep -A10 "Allocatable"

# Node resource usage summary
kubectl describe node <node-name> | grep -A10 "Allocated resources"
```

---

## Part 9: In-Place Pod Resource Resize (K8s 1.35+)

Starting with Kubernetes 1.35, you can resize CPU and memory on running Pods via the `/resize` subresource. Depending on `resizePolicy` and the type of change, a container may be updated in place or restarted.

### 9.1 Resize a Running Pod

```bash
# Check current resources
k get pod nginx -o jsonpath='{.spec.containers[0].resources}'

# Resize CPU and memory without restart
k patch pod nginx --subresource resize --patch '
{
  "spec": {
    "containers": [{
      "name": "nginx",
      "resources": {
        "requests": {"cpu": "200m", "memory": "256Mi"},
        "limits": {"cpu": "500m", "memory": "512Mi"}
      }
    }]
  }
}'

# Verify the resize was applied
k get pod nginx -o jsonpath='{.status.conditions[?(@.type=="PodResizePending")].status}'
k get pod nginx -o jsonpath='{.status.conditions[?(@.type=="PodResizeInProgress")].status}'
# Empty output means the condition is not currently set.
# If either condition is True, the resize is still pending or in progress.
```

### 9.2 Resize Policy

[Containers can specify a `resizePolicy` to control whether resizes require a restart](https://v1-35.docs.kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resize-demo
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 256Mi
    resizePolicy:
    - resourceName: cpu
      restartPolicy: NotRequired    # CPU changes apply live
    - resourceName: memory
      restartPolicy: RestartContainer # Memory changes restart container
```

> **When to Use In-Place Resize**
>
> - **Vertical scaling without downtime**: Scale up during traffic spikes, scale down after
> - **Right-sizing**: Adjust resources based on observed usage without redeploying
> - **Cost optimization**: Reduce over-provisioned resources on running workloads
>
> For automated resizing, use the **Vertical Pod Autoscaler (VPA)** which [can now leverage in-place resize](https://kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/).

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No requests set | Scheduling ignores resource needs | Usually set requests |
| Limits too low | Frequent OOMKills | Profile app and set appropriate limits |
| Requests = Limits by default | No burst capacity | Allow buffer between request and limit |
| Using `M` instead of `Mi` | Slightly off values | Use `Mi` and `Gi` consistently |
| No LimitRange in shared namespaces | Runaway pods | Set namespace defaults |

---

## Quiz

1. **A developer's pod keeps restarting with exit code 137. They've checked the application logs but see no errors -- the process just stops. `kubectl describe pod` shows `Last State: Terminated, Reason: OOMKilled`. The container's memory limit is 256Mi. What is happening, and what are two ways to fix it?**
   <details>
   <summary>Answer</summary>
   Exit code 137 means the process was killed by SIGKILL, and the OOMKilled reason confirms the container exceeded its 256Mi memory limit. The Linux kernel's OOM killer terminated the process because the container's memory usage surpassed what cgroups allow. There are no application-level error logs because the kill happens at the OS level, not within the application. Two fixes: (1) Increase the memory limit to accommodate actual usage (profile the app first with `kubectl top pod`), or (2) fix the memory leak in the application if usage grows unboundedly. A third option for Kubernetes 1.35+ is to use in-place pod resize to increase the limit without restarting.
   </details>

2. **Your team's Node.js application responds slowly during peak hours but `kubectl top pod` shows CPU usage at only 50m while the limit is 200m. However, the developer insists the app is CPU-bound. How can the CPU be throttled when usage appears to be well below the limit?**
   <details>
   <summary>Answer</summary>
   CPU throttling can occur even when average usage appears low. `kubectl top` shows average CPU over a measurement window, but CPU throttling happens on a per-100ms time slice basis. The app might burst to 200m+ for brief moments (handling a request) and get throttled during those spikes, even though the average over the sampling period looks like 50m. This is a well-known issue with CPU limits -- they penalize bursty workloads. Solutions: increase the CPU limit to allow higher bursts, remove the CPU limit entirely (some teams do this, relying only on requests for scheduling), or investigate whether the app is single-threaded and bottlenecking on one core.
   </details>

3. **You have three pods on the same node: Pod A (Guaranteed, using exactly its 512Mi request), Pod B (Burstable, using 800Mi against a 256Mi request), and Pod C (BestEffort, using 200Mi). The node enters memory pressure. In what order will the kubelet evict these pods, and why?**
   <details>
   <summary>Answer</summary>
   The kubelet evicts in QoS order: BestEffort first, then Burstable pods exceeding their requests, then Guaranteed pods. So Pod C (BestEffort, 200Mi, no guarantees) is evicted first. If pressure persists, Pod B (Burstable, using 800Mi against a 256Mi request -- 3x over its reservation) is evicted next. Pod A (Guaranteed, using exactly its request) is evicted last and only if the node is still critically low after evicting the other two. This ordering exists because BestEffort pods made no resource commitment, and Burstable pods exceeding their requests are "borrowing" capacity they didn't reserve.
   </details>

4. **A new team joins your cluster and starts deploying pods without resource requests, consuming all available node resources. Other teams' pods start getting evicted. Design a namespace-level governance strategy using LimitRange and ResourceQuota to prevent this from happening again.**
   <details>
   <summary>Answer</summary>
   Create both a LimitRange and ResourceQuota in the team's namespace. The LimitRange sets default requests/limits so pods without explicit resources still get sensible values (e.g., `defaultRequest: {cpu: 100m, memory: 128Mi}`, `default: {cpu: 500m, memory: 256Mi}`). Set `min` and `max` to prevent absurdly large or tiny pods. The ResourceQuota caps the total namespace consumption (e.g., `requests.cpu: 4`, `requests.memory: 8Gi`, `pods: 20`). With both in place, pods without resource specs get defaults from LimitRange, and total consumption is bounded by ResourceQuota. Note: when a ResourceQuota with compute constraints exists, all pods MUST have resource requests -- the LimitRange defaults ensure this requirement is met automatically.
   </details>

---

## Hands-On Exercise

**Task**: Configure resources, test limits, understand QoS.

**Steps**:

1. **Create pod with resources**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: resource-test
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

kubectl get pod resource-test -o jsonpath='{.status.qosClass}'
# Burstable (because requests ≠ limits)
```

2. **Create Guaranteed pod**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "100m"
EOF

kubectl get pod guaranteed -o jsonpath='{.status.qosClass}'
# Guaranteed
```

3. **Create BestEffort pod**:
```bash
kubectl run besteffort --image=nginx
kubectl get pod besteffort -o jsonpath='{.status.qosClass}'
# BestEffort
```

4. **Create LimitRange**:
```bash
kubectl create namespace limits-test

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: limits-test
spec:
  limits:
  - type: Container
    default:
      cpu: "200m"
      memory: "128Mi"
    defaultRequest:
      cpu: "100m"
      memory: "64Mi"
EOF

# Create pod without resources
kubectl run test-defaults --image=nginx -n limits-test

# Check - defaults applied!
kubectl get pod test-defaults -n limits-test -o yaml | grep -A8 resources
```

5. **Test ResourceQuota**:
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: pod-quota
  namespace: limits-test
spec:
  hard:
    pods: "2"
EOF

# Create pods until quota exceeded
kubectl run pod1 --image=nginx -n limits-test
kubectl run pod2 --image=nginx -n limits-test
kubectl run pod3 --image=nginx -n limits-test  # Should fail

kubectl describe resourcequota pod-quota -n limits-test
```

6. **Cleanup**:
```bash
kubectl delete pod resource-test guaranteed besteffort
kubectl delete namespace limits-test
```

**Success Criteria**:
- [ ] Can set requests and limits
- [ ] Understand difference between CPU and memory enforcement
- [ ] Can identify QoS classes
- [ ] Can create LimitRanges
- [ ] Can create ResourceQuotas

---

## Practice Drills

### Drill 1: Resource Creation (Target: 2 minutes)

```bash
# Create pod with resources
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
EOF

# Verify
kubectl get pod web -o jsonpath='{.spec.containers[0].resources}'

# Check QoS
kubectl get pod web -o jsonpath='{.status.qosClass}'

# Cleanup
kubectl delete pod web
```

### Drill 2: QoS Class Identification (Target: 3 minutes)

```bash
# Create three pods with different QoS classes

# Guaranteed
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: qos-guaranteed
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "100Mi"
      limits:
        cpu: "100m"
        memory: "100Mi"
EOF

# Burstable
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: qos-burstable
spec:
  containers:
  - name: app
    image: nginx
    resources:
      requests:
        cpu: "100m"
EOF

# BestEffort
kubectl run qos-besteffort --image=nginx

# Check all QoS classes
for pod in qos-guaranteed qos-burstable qos-besteffort; do
  echo "$pod: $(kubectl get pod $pod -o jsonpath='{.status.qosClass}')"
done

# Cleanup
kubectl delete pod qos-guaranteed qos-burstable qos-besteffort
```

### Drill 3: LimitRange (Target: 5 minutes)

```bash
kubectl create namespace lr-test

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit
  namespace: lr-test
spec:
  limits:
  - type: Container
    default:
      memory: "256Mi"
    defaultRequest:
      memory: "128Mi"
    min:
      memory: "64Mi"
    max:
      memory: "1Gi"
EOF

# Test default application
kubectl run default-test --image=nginx -n lr-test
kubectl get pod default-test -n lr-test -o jsonpath='{.spec.containers[0].resources}'

# Test exceeding max
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: too-big
  namespace: lr-test
spec:
  containers:
  - name: app
    image: nginx
    resources:
      limits:
        memory: "2Gi"
EOF
# Should fail: exceeds max

# Cleanup
kubectl delete namespace lr-test
```

### Drill 4: ResourceQuota (Target: 5 minutes)

```bash
kubectl create namespace quota-test

cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: quota-test
spec:
  hard:
    requests.cpu: "1"
    requests.memory: "1Gi"
    limits.cpu: "2"
    limits.memory: "2Gi"
    pods: "3"
EOF

# Check quota
kubectl describe resourcequota compute-quota -n quota-test

# Create pods (need resources because quota exists)
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pod1
  namespace: quota-test
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
---
apiVersion: v1
kind: Pod
metadata:
  name: pod2
  namespace: quota-test
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
---
apiVersion: v1
kind: Pod
metadata:
  name: pod3
  namespace: quota-test
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
EOF

# Try to exceed
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pod4
  namespace: quota-test
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
EOF
# Should fail: quota exceeded

# Check quota usage
kubectl describe resourcequota compute-quota -n quota-test

# Cleanup
kubectl delete namespace quota-test
```

### Drill 5: Resource Troubleshooting (Target: 5 minutes)

```bash
# Create pod with insufficient resources
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pending-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "100"
        memory: "100Gi"
EOF

# Check why it's pending
kubectl get pod pending-pod
kubectl describe pod pending-pod | grep -A5 "Events"

# Fix by reducing requests
kubectl delete pod pending-pod
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pending-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
EOF

# Verify running
kubectl get pod pending-pod

# Cleanup
kubectl delete pod pending-pod
```

### Drill 6: Update Resources (Target: 3 minutes)

```bash
# Create deployment
kubectl create deployment resource-update --image=nginx --replicas=2

# Add resources
kubectl set resources deployment/resource-update \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=200m,memory=256Mi"

# Verify (pods will restart)
kubectl get pods -l app=resource-update -w &
sleep 10
kill %1 2>/dev/null

kubectl describe deployment resource-update | grep -A10 "Resources"

# Cleanup
kubectl delete deployment resource-update
```

### Drill 7: Challenge - Complete Resource Setup

Create a namespace with:
1. LimitRange: default 200m CPU, 256Mi memory; max 1 CPU, 1Gi memory
2. ResourceQuota: max 4 pods, 2 CPU total requests, 4Gi total memory requests
3. Deploy a 2-replica deployment with appropriate resources

```bash
# YOUR TASK: Complete this setup
```

<details>
<summary>Solution</summary>

```bash
kubectl create namespace challenge

# LimitRange
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: limits
  namespace: challenge
spec:
  limits:
  - type: Container
    default:
      cpu: "200m"
      memory: "256Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "1"
      memory: "1Gi"
EOF

# ResourceQuota
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota
  namespace: challenge
spec:
  hard:
    pods: "4"
    requests.cpu: "2"
    requests.memory: "4Gi"
EOF

# Deployment
kubectl create deployment app --image=nginx --replicas=2 -n challenge

# Verify
kubectl get all -n challenge
kubectl describe resourcequota quota -n challenge

# Cleanup
kubectl delete namespace challenge
```

</details>

---

## Next Module

[Module 2.6: Scheduling](../module-2.6-scheduling/) - Node selection, affinity, taints, and tolerations.

## Sources

- [Resource Management for Pods and Containers](https://v1-35.docs.kubernetes.io/docs/concepts/configuration/manage-resources-containers/) — Primary source for CPU and memory requests and limits, resource units, scheduler use of requests, allocatable-fit behavior, OOMKilled examples, and in-place Pod resize as stable in Kubernetes 1.35.
- [Pod Quality of Service Classes](https://v1-35.docs.kubernetes.io/docs/concepts/workloads/pods/pod-qos/) — Primary source for Guaranteed, Burstable, and BestEffort classification criteria and for high-level eviction ordering under node resource pressure.
- [Limit Ranges](https://v1-35.docs.kubernetes.io/docs/concepts/policy/limit-range/) — Supports claims about namespace-scoped minimum and maximum resource constraints, default requests and limits, and admission-time enforcement via LimitRange.
- [Resource Quotas](https://v1-35.docs.kubernetes.io/docs/concepts/policy/resource-quotas/) — Supports claims about namespace resource governance, aggregate consumption limits, object-count quotas, and the relationship between quotas and resource requests/limits.
- [Kubernetes Metrics Server](https://github.com/kubernetes-sigs/metrics-server) — Primary source for metrics-server installation manifest URL, requirements, role in the built-in autoscaling pipeline, kubectl top support, 15-second collection interval, and common local-cluster TLS caveats.
- [Resize CPU and Memory Resources assigned to Containers](https://v1-35.docs.kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/) — Primary source for Kubernetes 1.35 in-place container resource resize capability, useful when verifying claims that newer VPA modes can leverage in-place resize instead of always recreating Pods.
- [Vertical Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/) — Primary source for comparing HPA and VPA, including VPA purpose, components, dependency on metrics, and update modes such as InPlaceOrRecreate.

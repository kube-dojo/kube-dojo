---
title: "Module 2.5: Resource Management"
slug: k8s/cka/part2-workloads-scheduling/module-2.5-resource-management
sidebar:
  order: 6
---
> **Complexity**: `[MEDIUM]` - Critical for production workloads
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.1 (Pods), Module 2.2 (Deployments)

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

- **In-Place Pod Resize is now GA**: As of Kubernetes 1.35, you can change CPU and memory requests/limits on running pods **without restarting them**. This feature was alpha since K8s 1.27 and took 3 years to stabilize. Use `kubectl patch` to resize a running pod — no downtime required.

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

> **Gotcha**: `Mi` (mebibyte) ≠ `M` (megabyte). `128Mi` = 134,217,728 bytes. `128M` = 128,000,000 bytes. Use `Mi` for consistency.

---

## Part 2: How Requests Affect Scheduling

### 2.1 Scheduling Decision

The scheduler places pods on nodes with sufficient **allocatable** resources:

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
kubectl run big-pod --image=nginx --requests="memory=100Gi"

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

### 3.1 CPU Limits (Throttling)

When a container exceeds CPU limits:
- CPU usage is **throttled**
- Process slows down but continues
- No container termination

```bash
# Container trying to use 2 CPUs with 500m limit
# Gets throttled to 500m worth of CPU time
```

### 3.2 Memory Limits (OOMKilled)

When a container exceeds memory limits:
- Container is **killed** (OOMKilled)
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
> A team's pod kept restarting randomly. No application errors in logs. They finally checked `kubectl describe pod` and saw `OOMKilled`. The app had a memory leak that slowly consumed memory until it hit the limit. Without the limit, it would have crashed the entire node. Limits saved the cluster, and logs revealed the problem.

---

## Part 4: QoS Classes

### 4.1 The Three QoS Classes

Kubernetes assigns QoS classes based on resource configuration:

| QoS Class | Condition | Eviction Priority |
|-----------|-----------|-------------------|
| **Guaranteed** | requests = limits for all containers | Last (lowest priority) |
| **Burstable** | At least one request or limit set | Middle |
| **BestEffort** | No requests or limits | First (highest priority) |

### 4.2 Guaranteed

All containers must have requests = limits for both CPU and memory:

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
> Even if you only set limits, Kubernetes automatically sets requests to the same value. So `limits: {memory: 128Mi}` without requests makes it Guaranteed, not Burstable!

---

## Part 5: LimitRanges

### 5.1 What Is a LimitRange?

LimitRange sets default/min/max resource constraints per namespace:

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

### 6.1 What Is a ResourceQuota?

ResourceQuota limits total resources consumed in a namespace:

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
> If a ResourceQuota is set in a namespace, pods MUST specify resource requests/limits (or have LimitRange defaults). Otherwise, pod creation fails.

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
# Create with resources
kubectl run nginx --image=nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=256Mi"

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

### 8.1 kubectl top (Requires metrics-server)

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

Starting with Kubernetes 1.35, you can **resize CPU and memory** on running pods without restarting them. This graduated to GA after 3 years of development.

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
k get pod nginx -o jsonpath='{.status.resize}'
# Expected: "" (empty means resize completed)
# If "InProgress": resize is being applied
# If "Infeasible": node doesn't have enough resources
```

### 9.2 Resize Policy

Containers can specify a `resizePolicy` to control whether resizes require a restart:

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
> For automated resizing, use the **Vertical Pod Autoscaler (VPA)** which can now leverage in-place resize.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No requests set | Scheduling ignores resource needs | Always set requests |
| Limits too low | Frequent OOMKills | Profile app and set appropriate limits |
| Requests = Limits (always) | No burst capacity | Allow buffer between request and limit |
| Using `M` instead of `Mi` | Slightly off values | Use `Mi` and `Gi` consistently |
| No LimitRange in shared namespaces | Runaway pods | Set namespace defaults |

---

## Quiz

1. **What happens when a container exceeds its memory limit?**
   <details>
   <summary>Answer</summary>
   The container is killed with OOMKilled status. The pod may restart based on its restartPolicy.
   </details>

2. **What happens when a container exceeds its CPU limit?**
   <details>
   <summary>Answer</summary>
   The container is throttled—it gets less CPU time but continues running. Unlike memory, CPU excess doesn't cause termination.
   </details>

3. **A pod has requests but no limits. What's its QoS class?**
   <details>
   <summary>Answer</summary>
   **Burstable**. To be Guaranteed, requests must equal limits for all containers. BestEffort requires no resources at all.
   </details>

4. **How do you set default resource limits for all pods in a namespace?**
   <details>
   <summary>Answer</summary>
   Create a LimitRange in the namespace with `default` and `defaultRequest` values.
   </details>

---

## Hands-On Exercise

**Task**: Configure resources, test limits, understand QoS.

**Steps**:

1. **Create pod with resources**:
```bash
kubectl run resource-test --image=nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=200m,memory=256Mi"

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
kubectl run web --image=nginx \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=512Mi"

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
kubectl run qos-burstable --image=nginx --requests="cpu=100m"

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
kubectl run pod1 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"
kubectl run pod2 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"
kubectl run pod3 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"

# Try to exceed
kubectl run pod4 --image=nginx -n quota-test --requests="cpu=200m,memory=256Mi"
# Should fail: quota exceeded

# Check quota usage
kubectl describe resourcequota compute-quota -n quota-test

# Cleanup
kubectl delete namespace quota-test
```

### Drill 5: Resource Troubleshooting (Target: 5 minutes)

```bash
# Create pod with insufficient resources
kubectl run pending-pod --image=nginx --requests="cpu=100,memory=100Gi"

# Check why it's pending
kubectl get pod pending-pod
kubectl describe pod pending-pod | grep -A5 "Events"

# Fix by reducing requests
kubectl delete pod pending-pod
kubectl run pending-pod --image=nginx --requests="cpu=100m,memory=128Mi"

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

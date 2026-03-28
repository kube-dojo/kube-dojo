---
title: "Module 1.3: Workload Rightsizing & Optimization"
slug: platform/disciplines/finops/module-1.3-rightsizing
sidebar:
  order: 4
---
> **Discipline Module** | Complexity: `[MEDIUM]` | Time: 2.5h

## Prerequisites

Before starting this module:
- **Required**: [Module 1.2: Kubernetes Cost Allocation](module-1.2-k8s-cost-allocation/) — Cost visibility and attribution
- **Required**: Understanding of Kubernetes resource requests and limits
- **Required**: Familiarity with Deployments, Pods, and container resource management
- **Recommended**: Experience with `kubectl top` and metrics-server
- **Recommended**: Access to a local Kubernetes cluster (kind or minikube)

---

## Why This Module Matters

In Module 1.2, you learned that the average Kubernetes cluster runs at 13-18% CPU utilization. That means for every dollar you spend on compute, roughly 82-87 cents buys unused capacity.

Why does this happen? Because engineers are *rational*.

When a developer sets resource requests, they face an asymmetric risk: **request too little and the app crashes at 3 AM. Request too much and... nothing bad happens.** The cost is invisible, the outage is a PagerDuty alert. So developers round up. Way up.

```
The Developer's Dilemma:
┌────────────────────────────────────────────────────┐
│                                                    │
│  "My app uses ~200m CPU normally, but once last    │
│   quarter it spiked to 800m during Black Friday.   │
│   I'll request 1000m to be safe."                  │
│                                                    │
│   Actual usage (p95):   250m  CPU                  │
│   Requested:           1000m  CPU                  │
│   Wasted:               750m  CPU  (75%)           │
│                                                    │
│   Annual waste per replica: ~$270                  │
│   × 6 replicas: ~$1,620/year                      │
│   × 80 similar services: ~$129,600/year            │
│                                                    │
│   That's one senior engineer's salary in waste.    │
└────────────────────────────────────────────────────┘
```

**Rightsizing** is the practice of aligning resource requests with actual usage. It's the single highest-ROI FinOps activity for Kubernetes — and this module shows you exactly how to do it.

---

## Did You Know?

- **Google's internal research showed that container resource requests are typically set 5-10x higher than actual usage** across most workloads. This isn't laziness — it's rational risk aversion. Nobody gets fired for over-provisioning, but under-provisioning causes visible outages.

- **The Vertical Pod Autoscaler (VPA) was created specifically to solve rightsizing**. Originally developed by Google, it's now a Kubernetes autoscaler project that observes actual resource consumption over time and recommends (or automatically applies) right-sized resource requests.

- **Memory rightsizing is trickier than CPU rightsizing.** If you under-provision CPU, the container gets throttled (slow but alive). If you under-provision memory, the container gets OOM-killed (dead). This asymmetry means memory requests should include a larger safety margin — typically 15-25% above peak observed usage.

---

## Identifying Over-Provisioned Workloads

### The Request-Usage Gap

The first step in rightsizing is finding where the biggest gaps exist between what's requested and what's used.

```bash
# Quick check: resource requests vs actual usage
kubectl top pods -n payments --containers
```

```
NAMESPACE  POD                        CONTAINER  CPU(cores)  MEMORY(bytes)
payments   payment-api-7d8f9c-abc12   api        23m         84Mi
payments   payment-api-7d8f9c-def34   api        31m         91Mi
payments   payment-api-7d8f9c-ghi56   api        18m         78Mi
payments   payment-worker-5b6c7-jkl89 worker     8m          42Mi
payments   payment-worker-5b6c7-mno01 worker     5m          38Mi
```

Compare against requests:

```
payment-api:
  Requested: 200m CPU, 256Mi memory (per replica)
  Actual:    ~24m CPU, ~84Mi memory (average)
  Gap:       176m CPU (88%), 172Mi memory (67%)

payment-worker:
  Requested: 100m CPU, 128Mi memory (per replica)
  Actual:    ~7m CPU, ~40Mi memory (average)
  Gap:       93m CPU (93%), 88Mi memory (69%)
```

### Using Prometheus Queries

For historical analysis over days or weeks (not just a point-in-time snapshot):

```promql
# Average CPU usage vs requests over 7 days, by container
avg by (namespace, pod, container) (
  rate(container_cpu_usage_seconds_total{container!=""}[5m])
) / on(namespace, pod, container) group_left()
kube_pod_container_resource_requests{resource="cpu"}

# Returns values like 0.12, meaning 12% of requested CPU is actually used
```

```promql
# Memory usage vs requests over 7 days
avg by (namespace, pod, container) (
  container_memory_working_set_bytes{container!=""}
) / on(namespace, pod, container) group_left()
kube_pod_container_resource_requests{resource="memory"}

# Returns values like 0.33, meaning 33% of requested memory is used
```

```promql
# Find the worst offenders: pods where avg CPU usage < 10% of requests
avg by (namespace, pod) (
  rate(container_cpu_usage_seconds_total{container!=""}[1h])
) / on(namespace, pod) group_left()
sum by (namespace, pod) (
  kube_pod_container_resource_requests{resource="cpu"}
) < 0.10
```

### The Rightsizing Matrix

Categorize workloads based on their usage patterns:

| Category | CPU Usage vs Request | Memory Usage vs Request | Action |
|----------|---------------------|------------------------|--------|
| **Massively over-provisioned** | < 15% | < 30% | Rightsize immediately (easy win) |
| **Moderately over-provisioned** | 15-40% | 30-60% | Rightsize with monitoring |
| **Reasonably sized** | 40-70% | 60-80% | Monitor, minor adjustments |
| **Tight** | 70-85% | 80-90% | Watch carefully, might need increase |
| **Under-provisioned** | > 85% | > 90% | Increase requests immediately |

---

## The Vertical Pod Autoscaler (VPA)

### What VPA Does

VPA watches actual resource consumption over time and adjusts (or recommends) resource requests accordingly.

```
VPA Workflow:
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Observe  │────▶│ Calculate│────▶│  Apply   │
│ usage    │     │ optimal  │     │ new      │
│ metrics  │     │ requests │     │ requests │
└──────────┘     └──────────┘     └──────────┘
  (Recommender)   (Recommender)   (Updater — optional)
```

### VPA Components

| Component | Role | Required? |
|-----------|------|-----------|
| **Recommender** | Watches usage, calculates recommendations | Yes |
| **Updater** | Evicts pods to apply new requests | Only for Auto mode |
| **Admission Controller** | Sets requests on new pods | Only for Auto/Initial modes |

### VPA Update Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `Off` | Only generates recommendations, applies nothing | **Start here** — review before changing anything |
| `Initial` | Sets requests on pod creation, doesn't change running pods | Safe for new deployments |
| `Auto` | Evicts and recreates pods with updated requests | Fully automated rightsizing |
| `Recreate` | Same as Auto (legacy name) | Avoid, use Auto instead |

**Best practice**: Always start with `Off` mode to review recommendations before trusting VPA to change anything automatically.

### VPA Limitations

Before you go all-in on VPA, know the gotchas:

1. **VPA and HPA conflict on CPU/memory** — Don't use both to scale the same metric. VPA adjusts requests; HPA adjusts replicas. If both try to respond to CPU, they fight.

2. **VPA evicts pods to update** — In Auto mode, VPA kills running pods to apply new resource values. This means brief disruption. Use PodDisruptionBudgets.

3. **VPA needs history** — Recommendations improve with more data. Give VPA at least 24-48 hours (ideally 7 days) of data before trusting its recommendations.

4. **VPA doesn't set limits** — It only manages requests. You need separate policies for limits.

5. **VPA ignores burst patterns** — If your app spikes to 2000m CPU for 5 seconds every hour, VPA might not capture that in its recommendation.

---

## HPA Tuning for Cost

The Horizontal Pod Autoscaler (HPA) scales replicas. Most teams configure it for availability — but it's also a powerful cost optimization tool.

### Aggressive vs Conservative Scaling

```yaml
# Cost-optimized HPA (scales down quickly, scales up carefully)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payment-api
  namespace: payments
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-api
  minReplicas: 2          # Don't go below 2 for HA
  maxReplicas: 12         # Cap the spend
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 65    # Scale up at 65% — more aggressive than default 50%
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 120   # Wait 2 min before scaling up
      policies:
      - type: Pods
        value: 2                         # Add max 2 pods at a time
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300   # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 25                        # Remove max 25% of pods at a time
        periodSeconds: 120
```

### Cost Impact of HPA Settings

| Setting | Cost Impact | Risk |
|---------|-------------|------|
| Higher target utilization (65-80%) | Lower cost — fewer replicas needed | Higher latency during spikes |
| Lower minReplicas | Lower baseline cost | Slower response to sudden load |
| Faster scaleDown | Less idle capacity | Thrashing if load fluctuates |
| Slower scaleUp | Temporary under-capacity | Brief degradation during ramp |
| Custom metrics (queue depth) | Scale on actual demand, not CPU | Requires metrics pipeline setup |

### Combining HPA + VPA Safely

The trick is: let VPA handle resource *requests* and HPA handle *replica count* — but on **different metrics**.

```yaml
# VPA: Right-size the per-pod resources
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: payment-api-vpa
  namespace: payments
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-api
  updatePolicy:
    updateMode: "Off"    # Recommendation only
  resourcePolicy:
    containerPolicies:
    - containerName: api
      controlledResources: ["memory"]  # VPA manages memory ONLY
      minAllowed:
        memory: "64Mi"
      maxAllowed:
        memory: "2Gi"

# HPA: Scale replicas based on CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payment-api-hpa
  namespace: payments
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Rule**: VPA on memory, HPA on CPU. They don't conflict because they manage different dimensions.

---

## Quality of Service (QoS) for Cost

Kubernetes assigns QoS classes to pods based on how requests and limits are configured. QoS affects eviction priority, which has cost implications.

### The Three QoS Classes

```yaml
# Guaranteed — highest priority, evicted last
# requests == limits for ALL containers
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "500m"       # Same as request
    memory: "512Mi"   # Same as request

# Burstable — medium priority
# requests < limits (or limits not set for some resources)
resources:
  requests:
    cpu: "200m"
    memory: "256Mi"
  limits:
    cpu: "1000m"      # Higher than request
    memory: "1Gi"     # Higher than request

# BestEffort — lowest priority, evicted first
# NO requests or limits set at all
resources: {}         # Empty — no guarantees
```

### QoS and Cost Strategy

| QoS Class | When to Use | Cost Implication |
|-----------|-------------|-----------------|
| **Guaranteed** | Critical production workloads (databases, payment APIs) | Highest — you pay for the exact resources at all times |
| **Burstable** | Most production services | Medium — pay for requests, can burst higher when available |
| **BestEffort** | Batch jobs, dev/test, non-critical tasks | Lowest — no cost guarantee, but evicted under pressure |

**Cost-optimized strategy**: Use Guaranteed only for truly critical workloads (< 20% of pods). Make most workloads Burstable. Use BestEffort for development and batch processing.

```
Cost-Optimized QoS Distribution:
┌─────────────────────────────────────────┐
│                                         │
│  Guaranteed  ██████             15%     │
│  (critical)                             │
│                                         │
│  Burstable   ████████████████   65%     │
│  (standard)                             │
│                                         │
│  BestEffort  ████                20%    │
│  (dev/batch)                            │
│                                         │
│  Target utilization: 55-70%             │
└─────────────────────────────────────────┘
```

---

## Profiling vs Utilization-Based Rightsizing

### Utilization-Based (Reactive)

Look at historical usage, set requests to match:

```
Approach: Watch metrics → set requests = p95 usage + margin

payment-api over 14 days:
  CPU p50:  85m     →  Not useful (too low)
  CPU p95: 210m     →  This is the target
  CPU p99: 380m     →  Rare spikes
  CPU max: 820m     →  One-time outlier

Recommendation: requests.cpu = 250m (p95 + 19% margin)
Previous:        requests.cpu = 1000m
Savings:         750m CPU per replica (75% reduction)
```

**Pros**: Simple, data-driven, works for all workloads
**Cons**: Backward-looking, doesn't account for future growth or rare events

### Profiling-Based (Proactive)

Measure actual resource needs through controlled tests:

```bash
# Load test to find true resource ceiling
# Using k6 or similar load testing tool

# Step 1: Deploy with generous resources
kubectl set resources deployment/payment-api \
  --requests=cpu=2000m,memory=2Gi \
  --limits=cpu=4000m,memory=4Gi

# Step 2: Run load test at expected peak traffic
k6 run --vus 200 --duration 30m load-test.js

# Step 3: Observe actual consumption during peak
kubectl top pods -n payments

# Step 4: Set requests = observed peak + 20% margin
```

**Pros**: Accounts for peak load, forward-looking, gives confidence
**Cons**: Requires load testing infrastructure, time-intensive

### Which Approach to Use?

| Scenario | Recommended Approach |
|----------|---------------------|
| Existing service with 30+ days of data | Utilization-based |
| New service, no production data | Profiling (load test first) |
| Seasonal workload (Black Friday, etc.) | Profiling + seasonal adjustment |
| Batch/cron jobs | Utilization-based on last 10 runs |
| Critical path (payment, auth) | Both — profile then validate with utilization |

---

## Rightsizing Workflow

A structured approach to rightsizing across your cluster:

### Phase 1: Discovery (Week 1)

```bash
# Find the biggest gaps between requests and usage
# This script ranks workloads by waste potential

cat > /tmp/rightsizing_discovery.sh << 'SCRIPT'
#!/bin/bash
echo "=== Rightsizing Discovery Report ==="
echo "Date: $(date +%Y-%m-%d)"
echo ""

for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | grep -v kube); do
  echo "--- Namespace: $ns ---"
  kubectl get pods -n "$ns" -o json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pod in data.get('items', []):
    name = pod['metadata']['name']
    for c in pod['spec']['containers']:
        cname = c['name']
        req = c.get('resources', {}).get('requests', {})
        lim = c.get('resources', {}).get('limits', {})
        cpu_req = req.get('cpu', 'none')
        mem_req = req.get('memory', 'none')
        cpu_lim = lim.get('cpu', 'none')
        mem_lim = lim.get('memory', 'none')
        print(f'  {name}/{cname}: req={cpu_req}/{mem_req} lim={cpu_lim}/{mem_lim}')
" 2>/dev/null
  echo ""
done
SCRIPT

chmod +x /tmp/rightsizing_discovery.sh
bash /tmp/rightsizing_discovery.sh
```

### Phase 2: Recommend (Week 2)

Deploy VPA in recommendation mode:

```yaml
# Deploy VPA for all workloads in target namespace
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: payment-api-vpa
  namespace: payments
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-api
  updatePolicy:
    updateMode: "Off"    # Recommendations only
  resourcePolicy:
    containerPolicies:
    - containerName: api
      minAllowed:
        cpu: "25m"
        memory: "64Mi"
      maxAllowed:
        cpu: "2000m"
        memory: "4Gi"
```

After 24-48 hours, check recommendations:

```bash
kubectl get vpa payment-api-vpa -n payments -o json | \
  python3 -c "
import json, sys
vpa = json.load(sys.stdin)
recs = vpa.get('status', {}).get('recommendation', {}).get('containerRecommendations', [])
for r in recs:
    print(f\"Container: {r['containerName']}\")
    print(f\"  Lower bound:  CPU={r['lowerBound']['cpu']}, Mem={r['lowerBound']['memory']}\")
    print(f\"  Target:       CPU={r['target']['cpu']}, Mem={r['target']['memory']}\")
    print(f\"  Upper bound:  CPU={r['upperBound']['cpu']}, Mem={r['upperBound']['memory']}\")
    print(f\"  Uncapped:     CPU={r['uncappedTarget']['cpu']}, Mem={r['uncappedTarget']['memory']}\")
"
```

### Phase 3: Apply (Week 3-4)

Apply changes progressively:

```bash
# Start with non-critical workloads
# Apply VPA target recommendation + 15% margin for CPU, +20% for memory

# Example: VPA recommends cpu=120m, memory=180Mi
# Apply: cpu=138m (round to 150m), memory=216Mi (round to 256Mi)

kubectl set resources deployment/payment-api -n payments \
  --requests=cpu=150m,memory=256Mi \
  --limits=cpu=500m,memory=512Mi
```

### Phase 4: Validate (Week 4+)

```bash
# Monitor after rightsizing
# Watch for OOMKills, CPU throttling, and latency changes

# Check for OOMKills
kubectl get events -n payments --field-selector reason=OOMKilling

# Check for CPU throttling (Prometheus)
# container_cpu_cfs_throttled_seconds_total should stay low

# Check application latency (compare before/after)
# Use your APM tool or Prometheus histograms
```

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|---------------|---------------|
| Rightsizing without monitoring | "Just reduce requests, what could go wrong?" | Always monitor OOMKills and throttling for 72+ hours after changes |
| Setting requests = average usage | Average hides peaks | Use p95 or p99 + margin, never average |
| Rightsizing memory too aggressively | Memory OOMKill is instant death | Keep 20-25% margin above p99 for memory |
| Ignoring JVM/Go runtime overhead | Language runtimes reserve memory beyond app needs | Account for GC heap, goroutine stacks, etc. |
| Rightsizing once and forgetting | Usage patterns change over time | Review VPA recommendations monthly |
| Applying Auto VPA in production immediately | Pod evictions during traffic | Start with Off mode, then Initial, then Auto with PDBs |
| Not setting VPA bounds | VPA might recommend 1m CPU or 100 CPU | Always set minAllowed and maxAllowed |
| Rightsizing without PDBs | VPA evicts pods, service goes down | Set PodDisruptionBudgets before enabling Auto mode |

---

## Quiz

### Question 1
A Pod requests 2 CPU and 8Gi memory. Over 14 days, its CPU p95 usage is 340m and memory p95 is 2.1Gi. What would you recommend as the new resource requests?

<details>
<summary>Show Answer</summary>

**CPU**: p95 is 340m. Add ~15% margin: 340m * 1.15 = 391m. Round to **400m**.
**Memory**: p95 is 2.1Gi. Add ~20% margin (memory needs more headroom): 2.1 * 1.20 = 2.52Gi. Round to **2.5Gi** or **3Gi** for safety.

**New requests**: cpu=400m, memory=3Gi (from cpu=2000m, memory=8Gi)
**Savings**: 80% CPU reduction, 62.5% memory reduction

Check p99 and max values too — if p99 is 600m CPU, you might set 700m instead of 400m. Always validate with a canary first.
</details>

### Question 2
Why is it dangerous to rightsize memory the same way you rightsize CPU?

<details>
<summary>Show Answer</summary>

**CPU under-provisioning causes throttling** — the container runs slower but stays alive. This is graceful degradation.

**Memory under-provisioning causes OOM-killing** — the container is terminated immediately. This is catastrophic for stateful applications and can cause data corruption.

Because of this asymmetry, memory requests should include a larger safety margin (20-25% above p99) compared to CPU (10-15% above p95). It's better to waste a little memory than risk OOM-kills in production.
</details>

### Question 3
Can VPA and HPA run on the same Deployment? If so, how?

<details>
<summary>Show Answer</summary>

Yes, but they must manage **different dimensions**. If both try to scale based on CPU, they conflict: VPA increases per-pod CPU requests while HPA tries to add replicas for the same CPU pressure.

The safe pattern is:
- **VPA manages memory** (rightsize memory requests per pod)
- **HPA manages CPU** (scale replica count based on CPU utilization)

Configure VPA's `controlledResources` to only include `["memory"]` and let HPA use CPU as its scaling metric.
</details>

### Question 4
What are the VPA update modes, and which should you start with?

<details>
<summary>Show Answer</summary>

Four modes:
- **Off**: Only generates recommendations, changes nothing. **Start here.**
- **Initial**: Sets requests on new pod creation, doesn't touch running pods.
- **Auto**: Evicts running pods and recreates them with updated requests.
- **Recreate**: Legacy name for Auto.

Always start with **Off** mode to review recommendations before applying them. This lets you validate that VPA's suggestions are reasonable (check bounds, compare to your knowledge of the workload). After gaining confidence, move to Initial for new deployments, then Auto for full automation — always with PodDisruptionBudgets in place.
</details>

### Question 5
Your cluster has 50 Deployments. How would you prioritize which ones to rightsize first?

<details>
<summary>Show Answer</summary>

Prioritize by **waste potential** = (requested - used) * replicas * cost_per_unit.

1. **Largest request-usage gaps** — workloads at < 15% utilization with high replica counts
2. **Highest absolute cost** — a 3-replica service requesting 4 CPU each wastes more than a 1-replica service requesting 500m
3. **Non-critical workloads first** — staging, dev, batch jobs have lower risk if rightsizing goes wrong
4. **Stateless over stateful** — stateless services recover from OOMKills via restarts; stateful services might lose data

Sort all 50 Deployments by `(cpu_requested - cpu_p95_usage) * replicas` descending, then start from the top.
</details>

---

## Hands-On Exercise: VPA Recommendation Mode

Deploy VPA in recommendation mode on an over-provisioned Deployment and analyze the recommendations.

### Prerequisites

- `kind` or `minikube` cluster running
- `kubectl` configured
- metrics-server installed

### Step 1: Install VPA

```bash
# Clone the VPA repository
git clone https://github.com/kubernetes/autoscaler.git /tmp/autoscaler
cd /tmp/autoscaler/vertical-pod-autoscaler

# Install VPA components
./hack/vpa-up.sh

# Verify VPA is running
kubectl get pods -n kube-system | grep vpa
```

Expected output:
```
vpa-admission-controller-xxx   1/1   Running   0   30s
vpa-recommender-xxx            1/1   Running   0   30s
vpa-updater-xxx                1/1   Running   0   30s
```

### Step 2: Deploy an Over-Provisioned Workload

```bash
# Create namespace
kubectl create namespace rightsizing-lab

# Deploy a massively over-provisioned nginx
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: overprovisioned-app
  namespace: rightsizing-lab
  labels:
    app: overprovisioned-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: overprovisioned-app
  template:
    metadata:
      labels:
        app: overprovisioned-app
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            cpu: "1000m"        # Way too much for nginx
            memory: "1Gi"       # Way too much for nginx
          limits:
            cpu: "2000m"
            memory: "2Gi"
        ports:
        - containerPort: 80
EOF

# Create a Service so the load-generator can reach the app via DNS
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: overprovisioned-app
  namespace: rightsizing-lab
spec:
  selector:
    app: overprovisioned-app
  ports:
    - port: 80
      targetPort: 80
EOF

# Wait for pods to be ready
kubectl rollout status deployment/overprovisioned-app -n rightsizing-lab

# Verify resources
kubectl get pods -n rightsizing-lab -o custom-columns=\
NAME:.metadata.name,\
CPU_REQ:.spec.containers[0].resources.requests.cpu,\
MEM_REQ:.spec.containers[0].resources.requests.memory,\
CPU_LIM:.spec.containers[0].resources.limits.cpu,\
MEM_LIM:.spec.containers[0].resources.limits.memory
```

### Step 3: Create VPA in Off Mode

```bash
kubectl apply -f - << 'EOF'
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: overprovisioned-app-vpa
  namespace: rightsizing-lab
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: overprovisioned-app
  updatePolicy:
    updateMode: "Off"          # Recommendation only — no changes applied
  resourcePolicy:
    containerPolicies:
    - containerName: app
      minAllowed:
        cpu: "10m"
        memory: "32Mi"
      maxAllowed:
        cpu: "2000m"
        memory: "4Gi"
      controlledResources: ["cpu", "memory"]
EOF

echo "VPA created in Off mode. Waiting for recommendations..."
```

### Step 4: Generate Some Load

```bash
# Simulate light traffic to give VPA usage data
kubectl run load-generator \
  --namespace=rightsizing-lab \
  --image=busybox \
  --restart=Never \
  --command -- sh -c "
    while true; do
      wget -q -O- http://overprovisioned-app.rightsizing-lab.svc.cluster.local/ > /dev/null 2>&1
      sleep 0.5
    done
  "

echo "Load generator running. Wait 5-10 minutes for VPA to collect data..."
```

### Step 5: Review VPA Recommendations

```bash
# After 5-10 minutes, check VPA recommendations
kubectl get vpa overprovisioned-app-vpa -n rightsizing-lab -o yaml | \
  grep -A 30 "recommendation:"
```

Expected output (values will vary):
```yaml
recommendation:
  containerRecommendations:
  - containerName: app
    lowerBound:
      cpu: 10m
      memory: 48Mi
    target:
      cpu: 15m
      memory: 62Mi
    uncappedTarget:
      cpu: 15m
      memory: 62Mi
    upperBound:
      cpu: 42m
      memory: 131Mi
```

### Step 6: Analyze the Results

```bash
cat > /tmp/analyze_vpa.sh << 'SCRIPT'
#!/bin/bash
echo "============================================"
echo "  VPA Rightsizing Analysis"
echo "============================================"
echo ""

# Current requests
echo "CURRENT REQUESTS (per replica):"
echo "  CPU:    1000m"
echo "  Memory: 1Gi (1024Mi)"
echo ""

# Get VPA recommendations
VPA_JSON=$(kubectl get vpa overprovisioned-app-vpa -n rightsizing-lab -o json 2>/dev/null)

if [ -z "$VPA_JSON" ]; then
  echo "ERROR: VPA not found or no recommendations yet."
  echo "Wait a few more minutes and try again."
  exit 1
fi

echo "$VPA_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
recs = data.get('status', {}).get('recommendation', {}).get('containerRecommendations', [])
if not recs:
    print('No recommendations available yet. Wait 5-10 minutes.')
    sys.exit(0)
r = recs[0]
print('VPA RECOMMENDATIONS:')
print(f\"  Target:      CPU={r['target']['cpu']}, Memory={r['target']['memory']}\")
print(f\"  Lower bound: CPU={r['lowerBound']['cpu']}, Memory={r['lowerBound']['memory']}\")
print(f\"  Upper bound: CPU={r['upperBound']['cpu']}, Memory={r['upperBound']['memory']}\")
print()

# Parse target values for savings calculation
cpu_target = r['target']['cpu']
if cpu_target.endswith('m'):
    cpu_target_m = int(cpu_target[:-1])
else:
    cpu_target_m = int(float(cpu_target) * 1000)

mem_target = r['target']['memory']
if mem_target.endswith('Mi'):
    mem_target_mi = int(mem_target[:-2])
elif mem_target.endswith('Gi'):
    mem_target_mi = int(float(mem_target[:-2]) * 1024)
elif mem_target.endswith('M'):
    mem_target_mi = int(mem_target[:-1])
else:
    mem_target_mi = int(int(mem_target) / 1048576)

cpu_savings = ((1000 - cpu_target_m) / 1000) * 100
mem_savings = ((1024 - mem_target_mi) / 1024) * 100

print('SAVINGS ANALYSIS:')
print(f'  CPU:    {1000}m → {cpu_target_m}m = {cpu_savings:.0f}% reduction')
print(f'  Memory: 1024Mi → {mem_target_mi}Mi = {mem_savings:.0f}% reduction')
print()

# With margin
cpu_safe = int(cpu_target_m * 1.15 / 5) * 5  # 15% margin, round to 5
mem_safe = int(mem_target_mi * 1.20 / 16) * 16  # 20% margin, round to 16
print('RECOMMENDED NEW REQUESTS (with safety margin):')
print(f'  CPU:    {max(cpu_safe, 25)}m  (target + 15%)')
print(f'  Memory: {max(mem_safe, 64)}Mi (target + 20%)')
print()
print('ESTIMATED MONTHLY SAVINGS (3 replicas):')
cpu_saved = (1000 - max(cpu_safe, 25)) / 1000 * 3
print(f'  CPU:    {cpu_saved:.2f} cores freed across cluster')
print(f'  At \$0.05/CPU-hr: ~\${cpu_saved * 0.05 * 730:.2f}/month')
"
SCRIPT

chmod +x /tmp/analyze_vpa.sh
bash /tmp/analyze_vpa.sh
```

### Step 7: Apply Rightsized Resources

```bash
# Apply the VPA-recommended values with margin
# Adjust these based on your actual VPA output
kubectl set resources deployment/overprovisioned-app \
  -n rightsizing-lab \
  --requests=cpu=25m,memory=64Mi \
  --limits=cpu=100m,memory=256Mi

# Watch the rollout
kubectl rollout status deployment/overprovisioned-app -n rightsizing-lab

# Verify new resource allocation
kubectl get pods -n rightsizing-lab -o custom-columns=\
NAME:.metadata.name,\
CPU_REQ:.spec.containers[0].resources.requests.cpu,\
MEM_REQ:.spec.containers[0].resources.requests.memory
```

### Step 8: Cleanup

```bash
kubectl delete namespace rightsizing-lab
kubectl delete pod load-generator -n rightsizing-lab --ignore-not-found
```

### Success Criteria

You've completed this exercise when you:
- [ ] Deployed VPA and verified all three components are running
- [ ] Created an over-provisioned Deployment (1000m CPU, 1Gi memory for nginx)
- [ ] Deployed VPA in Off mode and generated recommendations
- [ ] Analyzed VPA recommendations and calculated savings
- [ ] Applied rightsized resources with safety margins
- [ ] Verified the Deployment runs correctly with reduced resources

---

## Key Takeaways

1. **The request-usage gap is the largest source of Kubernetes waste** — most workloads use 10-20% of what they request
2. **VPA automates rightsizing recommendations** — start with Off mode, graduate to Auto
3. **Memory needs more margin than CPU** — CPU throttling is graceful, OOM-killing is catastrophic
4. **HPA and VPA can coexist** — VPA on memory, HPA on CPU
5. **Rightsizing is continuous** — usage patterns change, review recommendations monthly

---

## Further Reading

**Projects**:
- **Kubernetes VPA** — github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler
- **Goldilocks** — github.com/FairwindsOps/goldilocks (VPA dashboard for all workloads)

**Articles**:
- **"Right-Sizing Your Kubernetes Workloads"** — learnk8s.io
- **"VPA Best Practices"** — povilasv.me/vertical-pod-autoscaler-best-practices
- **"CPU Limits in Kubernetes Are Harmful"** — robusta.dev (why some teams remove CPU limits)

**Talks**:
- **"To Limit or Not to Limit: Kubernetes Resource Management"** — KubeCon (YouTube)
- **"Goldilocks: Getting Kubernetes Resource Requests Just Right"** — Fairwinds (YouTube)

---

## Summary

Rightsizing is the highest-ROI FinOps activity in Kubernetes. By using VPA recommendations, Prometheus metrics, and structured workflows, teams can typically reduce compute costs by 40-70% without impacting application performance. The key is to start with visibility (Off mode VPA), apply changes gradually (non-critical workloads first), and monitor aggressively after changes (OOMKills, throttling, latency). Rightsizing is not a one-time project — it's a continuous practice that should be reviewed monthly as usage patterns evolve.

---

## Next Module

Continue to [Module 1.4: Cluster Scaling & Compute Optimization](module-1.4-compute-optimization/) to learn how Karpenter, Spot instances, and node consolidation reduce infrastructure costs at the cluster level.

---

*"The most expensive resource is the one nobody's using."* — FinOps proverb

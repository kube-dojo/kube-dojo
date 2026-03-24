# Module 2.9: Workload Autoscaling

> **Complexity**: `[MEDIUM]` - CKA exam topic
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.2 (Deployments), Module 2.5 (Resource Management)

---

## Why This Module Matters

Static replica counts waste money or cause outages. Too many replicas = wasted resources. Too few = users get errors during traffic spikes. Autoscaling dynamically adjusts capacity based on actual demand.

The CKA exam tests your ability to create and configure HorizontalPodAutoscalers. You'll need to do this quickly under pressure.

> **The Thermostat Analogy**
>
> A Horizontal Pod Autoscaler is like a smart thermostat. You set the desired "temperature" (target CPU utilization), and the system automatically turns on more "heaters" (pods) when it's cold (high load) and turns them off when it's warm (low load). You don't manually adjust the heating — the thermostat does it based on the current reading.

---

## Did You Know?

- **HPA checks metrics every 15 seconds** by default (configurable via `--horizontal-pod-autoscaler-sync-period`). Scaling decisions are based on the average metric value across all pods.

- **HPA has a cooldown period**: After scaling up, HPA waits 3 minutes before considering scale-down (configurable). This prevents "flapping" — rapidly scaling up and down.

- **metrics-server is required**: HPA can't function without metrics-server installed in the cluster. It provides the CPU/memory metrics that HPA needs. This is a common gotcha in practice environments.

- **VPA + In-Place Pod Resize (K8s 1.35)**: The Vertical Pod Autoscaler can now leverage in-place pod resize to adjust CPU/memory without restarting pods — a game changer for stateful workloads.

---

## Part 1: Horizontal Pod Autoscaler (HPA)

### 1.1 Prerequisites: metrics-server

HPA needs metrics-server to read CPU/memory usage:

```bash
# Check if metrics-server is installed
k top nodes
# If "error: Metrics API not available", install it:

# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For local clusters (kind/minikube), you may need to add --kubelet-insecure-tls
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

# Verify it works
k top nodes
k top pods
```

### 1.2 Creating an HPA

**Imperative (exam-fast):**

```bash
# Create HPA: scale between 2-10 replicas, target 80% CPU
k autoscale deployment web --min=2 --max=10 --cpu-percent=80

# Verify
k get hpa
# NAME   REFERENCE        TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# web    Deployment/web   12%/80%   2         10        2          30s
```

**Declarative:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
```

### 1.3 How HPA Decides

```
┌─────────────────────────────────────────────────────────────┐
│                 HPA Decision Loop (every 15s)                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Read current metric values from metrics-server           │
│                    │                                         │
│                    ▼                                         │
│  2. Calculate: desired = ceil(current * (actual / target))   │
│     Example: 3 pods at 90% CPU, target 50%                  │
│     desired = ceil(3 * (90/50)) = ceil(5.4) = 6 pods        │
│                    │                                         │
│                    ▼                                         │
│  3. Clamp to min/max range                                   │
│     min: 2, max: 10 → result: 6 (within range)             │
│                    │                                         │
│                    ▼                                         │
│  4. Scale deployment to 6 replicas                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Monitoring HPA

```bash
# Check HPA status
k get hpa web-hpa
k describe hpa web-hpa

# Watch scaling events
k get hpa -w

# Check events for scaling decisions
k get events --field-selector reason=SuccessfulRescale
```

---

## Part 2: Load Testing Your HPA

```bash
# Deploy a test app with resource requests
k create deployment web --image=nginx --replicas=1
k set resources deployment web --requests=cpu=100m,memory=128Mi --limits=cpu=200m,memory=256Mi

# Create HPA
k autoscale deployment web --min=1 --max=5 --cpu-percent=50

# Generate load (in another terminal)
k run load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://web; done"

# Watch HPA respond
k get hpa web -w
# You should see CPU% increase and replicas scale up

# Stop load
k delete pod load-generator

# Watch HPA scale back down (after cooldown)
k get hpa web -w
```

---

## Part 3: Vertical Pod Autoscaler (VPA)

VPA automatically adjusts CPU and memory requests/limits based on observed usage. Unlike HPA (more pods), VPA adjusts the *size* of each pod.

### 3.1 When to Use VPA vs HPA

| Scenario | Use |
|----------|-----|
| Stateless web apps | HPA (add more pods) |
| Databases, caches | VPA (bigger pods — can't easily add replicas) |
| Unknown resource needs | VPA in recommend mode first |
| Batch jobs | VPA (right-size the job pods) |
| Combine both | HPA on custom metrics + VPA on resources |

### 3.2 VPA Modes

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  updatePolicy:
    updateMode: "Auto"  # Options: Off, Initial, Recreate, Auto
```

| Mode | Behavior |
|------|----------|
| `Off` | VPA only recommends — doesn't change anything (safe for auditing) |
| `Initial` | Sets resources only when pods are created (not running ones) |
| `Recreate` | Evicts and recreates pods with new resources |
| `Auto` | Uses in-place resize (K8s 1.35+) when possible, falls back to recreate |

> **K8s 1.35 + VPA**: With in-place pod resize GA, VPA in `Auto` mode can now adjust CPU and memory on running pods without restart — a major improvement for stateful workloads.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No metrics-server | HPA shows `<unknown>` for targets | Install metrics-server first |
| No resource requests on pods | HPA can't calculate utilization | Always set `requests` |
| Min = Max replicas | HPA can't scale | Set different min and max |
| CPU target too low (e.g., 10%) | Scales too aggressively, wastes resources | Start at 50-80% |
| Using HPA + VPA on same metric | Conflict — both try to adjust | Use HPA for scaling, VPA for right-sizing (different metrics) |
| Forgetting cooldown | Wonder why HPA doesn't scale down immediately | Default 5m stabilization window |

---

## Quiz

1. **What does HPA need to function?**
   <details>
   <summary>Answer</summary>
   metrics-server must be installed to provide CPU/memory metrics. Without it, HPA shows `<unknown>` for current values and cannot make scaling decisions.
   </details>

2. **Create an HPA for deployment `api` that scales between 3-15 pods at 70% CPU.**
   <details>
   <summary>Answer</summary>
   `kubectl autoscale deployment api --min=3 --max=15 --cpu-percent=70`
   </details>

3. **What's the difference between HPA and VPA?**
   <details>
   <summary>Answer</summary>
   HPA scales *horizontally* — adds/removes pod replicas based on metrics. VPA scales *vertically* — adjusts CPU/memory requests on individual pods. HPA is for stateless apps; VPA is for stateful workloads or right-sizing.
   </details>

4. **Why shouldn't you use HPA and VPA on the same CPU metric?**
   <details>
   <summary>Answer</summary>
   They'll conflict: HPA tries to add pods to reduce per-pod CPU, while VPA tries to increase per-pod CPU. Use HPA for replica scaling and VPA for resource right-sizing on different metrics.
   </details>

---

## Hands-On Exercise

**Challenge: Auto-Scale a Web Application**

Set up a deployment, configure HPA, generate load, and verify scaling.

```bash
# 1. Create deployment with resource requests
k create deployment challenge-web --image=nginx --replicas=1
k set resources deployment challenge-web \
  --requests=cpu=50m,memory=64Mi --limits=cpu=100m,memory=128Mi

# 2. Expose it
k expose deployment challenge-web --port=80

# 3. Create HPA: 2-8 replicas, 50% CPU target
k autoscale deployment challenge-web --min=2 --max=8 --cpu-percent=50

# 4. Verify HPA is working
k get hpa challenge-web
# Should show TARGETS and current replica count

# 5. Generate load
k run load --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://challenge-web; done"

# 6. Watch scaling happen
k get hpa challenge-web -w
# Wait until you see replicas increase

# 7. Stop load and watch scale-down
k delete pod load
k get hpa challenge-web -w
# Replicas should decrease after cooldown (5 min)

# 8. Cleanup
k delete deployment challenge-web
k delete svc challenge-web
k delete hpa challenge-web
```

**Success Criteria:**
- [ ] HPA created with correct min/max/target
- [ ] Replicas scale up during load
- [ ] Replicas scale down after load stops
- [ ] No `<unknown>` in HPA targets

---

## Next Module

Return to [Part 2 Overview](../part2-workloads-scheduling/README.md).

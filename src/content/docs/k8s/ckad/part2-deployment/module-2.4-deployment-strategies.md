---
title: "Module 2.4: Deployment Strategies"
slug: k8s/ckad/part2-deployment/module-2.4-deployment-strategies
sidebar:
  order: 4
lab:
  id: ckad-2.4-deployment-strategies
  url: https://killercoda.com/kubedojo/scenario/ckad-2.4-deployment-strategies
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Conceptual understanding with practical implementation
>
> **Time to Complete**: 40-50 minutes
>
> **Prerequisites**: Module 2.1 (Deployments), understanding of Services

---

## Learning Outcomes

After completing this module, you will be able to:
- **Implement** blue/green and canary deployments using Kubernetes-native resources
- **Compare** rolling update, blue/green, and canary strategies with their trade-offs
- **Design** a deployment strategy that meets availability and rollback requirements
- **Evaluate** deployment health during a rollout and decide when to proceed or rollback

---

## Why This Module Matters

How you deploy new versions matters. A bad deployment strategy can cause downtime, data corruption, or user-facing errors. The CKAD expects you to understand different deployment strategies and when to use each.

You'll face questions like:
- Implement a blue/green deployment
- Set up a canary release
- Configure rolling update parameters
- Choose the appropriate strategy for a scenario

> **The Restaurant Menu Analogy**
>
> Rolling updates are like gradually replacing menu items—customers ordering at different times might get slightly different menus. Blue/green is like having two complete kitchens—you switch all customers to the new kitchen at once. Canary releases are like giving the new dish to 10% of customers first—if they like it, everyone gets it.

---

## Strategy Overview

### Comparison

| Strategy | Downtime | Rollback | Resource Cost | Risk |
|----------|----------|----------|---------------|------|
| **Rolling Update** | None | Slow (gradual) | Low | Medium |
| **Recreate** | Yes | Fast (redeploy old) | Low | High |
| **Blue/Green** | None | Instant | 2x resources | Low |
| **Canary** | None | Instant | Low-Medium | Very Low |

### When to Use Each

| Strategy | Best For |
|----------|----------|
| Rolling Update | Most applications, default choice |
| Recreate | Apps that can't run multiple versions |
| Blue/Green | Critical apps needing instant rollback |
| Canary | Risk-averse deployments, testing with real traffic |

---

## Rolling Update (Default)

Kubernetes gradually replaces old pods with new ones.

### Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Can exceed replicas by 1
      maxUnavailable: 1  # At most 1 unavailable
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
```

### Update Behavior

```
With replicas=4, maxSurge=1, maxUnavailable=1:

Start:  [v1] [v1] [v1] [v1]     (4 running)
Step 1: [v1] [v1] [v1] [--] [v2] (3 old, 1 new starting)
Step 2: [v1] [v1] [--] [v2] [v2] (2 old, 2 new)
Step 3: [v1] [--] [v2] [v2] [v2] (1 old, 3 new)
Step 4: [v2] [v2] [v2] [v2]     (4 new, complete)
```

### Trigger Rolling Update

```bash
# Update image
k set image deploy/web-app nginx=nginx:1.21

# Watch rollout
k rollout status deploy/web-app

# Check pods transitioning
k get pods -l app=web -w
```

---

## Recreate Strategy

All existing pods are killed before new ones are created.

### Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-app
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: postgres
        image: postgres:13
```

### Update Behavior

```
Start:  [v1] [v1] [v1]
Step 1: [--] [--] [--]  (all old pods terminated)
Step 2: [v2] [v2] [v2]  (all new pods created)
```

### When to Use

- Database applications with single-writer requirement
- Applications with filesystem locks
- Apps that can't handle multiple versions accessing shared state
- Stateful applications without proper migration support

---

## Blue/Green Deployment

Run two identical environments. Switch traffic instantly by updating the Service selector.

### Implementation

**Step 1: Deploy Blue (Current)**

```yaml
# blue-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
      - name: app
        image: myapp:1.0
```

**Step 2: Create Service (Points to Blue)**

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
    version: blue  # Points to blue
  ports:
  - port: 80
```

**Step 3: Deploy Green (New Version)**

```yaml
# green-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: green
  template:
    metadata:
      labels:
        app: myapp
        version: green
    spec:
      containers:
      - name: app
        image: myapp:2.0
```

**Step 4: Switch Traffic**

```bash
# Switch service to green
k patch svc myapp -p '{"spec":{"selector":{"version":"green"}}}'

# Instant rollback if needed
k patch svc myapp -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Complete Blue/Green Script

```bash
# Deploy blue
k apply -f blue-deployment.yaml

# Create service pointing to blue
k apply -f service.yaml

# Test blue
k run test --image=busybox --rm -it --restart=Never -- wget -qO- http://myapp

# Deploy green (without traffic)
k apply -f green-deployment.yaml

# Test green directly (port-forward or separate service)
k port-forward deploy/app-green 8080:80 &
curl localhost:8080

# Switch traffic to green
k patch svc myapp -p '{"spec":{"selector":{"version":"green"}}}'

# If problems, instant rollback
k patch svc myapp -p '{"spec":{"selector":{"version":"blue"}}}'

# Once confirmed, remove blue
k delete deploy app-blue
```

---

## Canary Deployment

Route a small percentage of traffic to the new version. Gradually increase if successful.

### Implementation with Multiple Deployments

**Stable Deployment (90% traffic)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
spec:
  replicas: 9  # 90% of traffic
  selector:
    matchLabels:
      app: myapp
      track: stable
  template:
    metadata:
      labels:
        app: myapp
        track: stable
    spec:
      containers:
      - name: app
        image: myapp:1.0
```

**Canary Deployment (10% traffic)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 1  # 10% of traffic
  selector:
    matchLabels:
      app: myapp
      track: canary
  template:
    metadata:
      labels:
        app: myapp
        track: canary
    spec:
      containers:
      - name: app
        image: myapp:2.0
```

**Service (Routes to Both)**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp  # Matches both stable and canary
  ports:
  - port: 80
```

### Traffic Distribution

With 9 stable pods and 1 canary pod:
- ~90% traffic → stable (v1.0)
- ~10% traffic → canary (v2.0)

### Progressive Canary Rollout

```bash
# Start: 9 stable, 1 canary (10%)
k scale deploy app-canary --replicas=1
k scale deploy app-stable --replicas=9

# Increase canary to 25%
k scale deploy app-canary --replicas=3
k scale deploy app-stable --replicas=9

# Increase canary to 50%
k scale deploy app-canary --replicas=5
k scale deploy app-stable --replicas=5

# Full rollout (100% new version)
k scale deploy app-canary --replicas=10
k scale deploy app-stable --replicas=0

# Cleanup: rename canary to stable
k delete deploy app-stable
k patch deploy app-canary -p '{"metadata":{"name":"app-stable"}}'
```

---

## Rolling Update Parameters Deep Dive

### maxSurge

Maximum number of pods that can be created over desired count:

```yaml
rollingUpdate:
  maxSurge: 25%      # 25% extra pods (default)
  # or
  maxSurge: 2        # 2 extra pods
```

### maxUnavailable

Maximum pods that can be unavailable during update:

```yaml
rollingUpdate:
  maxUnavailable: 25%  # 25% can be down (default)
  # or
  maxUnavailable: 0    # Zero downtime
```

### Common Configurations

```yaml
# Zero downtime (conservative)
rollingUpdate:
  maxSurge: 1
  maxUnavailable: 0

# Fast update (aggressive)
rollingUpdate:
  maxSurge: 100%
  maxUnavailable: 50%

# Balanced (default)
rollingUpdate:
  maxSurge: 25%
  maxUnavailable: 25%
```

---

## Readiness Gates and Probes

Proper probes ensure smooth deployments.

### Readiness Probe for Deployments

```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

Without readiness probes, Kubernetes considers pods ready immediately—traffic might route to pods that aren't fully initialized.

### minReadySeconds

```yaml
spec:
  minReadySeconds: 10  # Pod must be ready 10s before considered available
```

This adds a buffer to catch early crashes.

---

## Practical Exam Scenarios

### Scenario 1: Configure Zero-Downtime Rolling Update

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Key: never reduce below desired
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        readinessProbe:  # Important for zero-downtime
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 2
          periodSeconds: 3
```

### Scenario 2: Quick Blue/Green Switch

```bash
# Create blue deployment
k create deploy app-blue --image=nginx:1.20 --replicas=3
k label deploy app-blue version=blue

# Add version label to pod template
k patch deploy app-blue -p '{"spec":{"template":{"metadata":{"labels":{"version":"blue"}}}}}'

# Create service
k expose deploy app-blue --name=myapp --port=80 --selector=version=blue

# Deploy green
k create deploy app-green --image=nginx:1.21 --replicas=3
k patch deploy app-green -p '{"spec":{"template":{"metadata":{"labels":{"version":"green"}}}}}'

# Switch to green
k patch svc myapp -p '{"spec":{"selector":{"version":"green"}}}'
```

---

## Did You Know?

- **Kubernetes rolling updates are self-healing.** If a new pod fails its readiness probe, the rollout pauses automatically, preventing a bad version from fully deploying.

- **Blue/green deployments require 2x resources** during the switch. This is their main downside but enables instant rollback.

- **Canary deployments originated at Google.** The term comes from "canary in a coal mine"—miners used canaries to detect toxic gases. If the canary died, miners knew to evacuate.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| No readiness probe | Traffic to unready pods | Always add readiness probes |
| `maxUnavailable: 100%` | All pods killed at once | Keep at 25% or less |
| Wrong service selector for blue/green | Traffic doesn't switch | Verify label matching |
| Not testing canary separately | Canary issues undetected | Test canary pods directly first |
| Forgetting to scale down old deployment | Resource waste | Scale down after successful switch |

---

## Quiz

1. **What deployment strategy kills all old pods before creating new ones?**
   <details>
   <summary>Answer</summary>
   `Recreate`. All existing pods are terminated before new pods are created, causing downtime.
   </details>

2. **How do you switch traffic instantly in blue/green?**
   <details>
   <summary>Answer</summary>
   Patch the Service selector to point to the new deployment's labels:
   `kubectl patch svc myapp -p '{"spec":{"selector":{"version":"green"}}}'`
   </details>

3. **With 10 replicas and maxSurge=2, maxUnavailable=1, how many pods can exist during update?**
   <details>
   <summary>Answer</summary>
   Maximum 12 pods (10 + maxSurge of 2). Minimum 9 pods available (10 - maxUnavailable of 1).
   </details>

4. **How do you achieve 10% canary traffic with pod counts?**
   <details>
   <summary>Answer</summary>
   Run 9 stable pods and 1 canary pod, with a Service selecting both. Traffic distributes roughly proportional to pod count: ~90% stable, ~10% canary.
   </details>

---

## Hands-On Exercise

**Task**: Implement all three deployment strategies.

**Part 1: Rolling Update with Parameters**

```bash
# Create deployment with custom rolling update
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rolling-demo
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: rolling
  template:
    metadata:
      labels:
        app: rolling
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
EOF

# Update and watch (should see 5 pods max)
k set image deploy/rolling-demo nginx=nginx:1.21
k get pods -l app=rolling -w

# Cleanup
k delete deploy rolling-demo
```

**Part 2: Blue/Green Deployment**

```bash
# Blue deployment
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo
      version: blue
  template:
    metadata:
      labels:
        app: demo
        version: blue
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
EOF

# Service pointing to blue
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: demo-svc
spec:
  selector:
    app: demo
    version: blue
  ports:
  - port: 80
EOF

# Green deployment
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo
      version: green
  template:
    metadata:
      labels:
        app: demo
        version: green
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
EOF

# Switch to green
k patch svc demo-svc -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback to blue
k patch svc demo-svc -p '{"spec":{"selector":{"version":"blue"}}}'

# Cleanup
k delete deploy blue green
k delete svc demo-svc
```

**Part 3: Canary Deployment**

```bash
# Stable deployment (9 replicas)
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stable
spec:
  replicas: 9
  selector:
    matchLabels:
      app: canary-demo
      track: stable
  template:
    metadata:
      labels:
        app: canary-demo
        track: stable
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
EOF

# Canary deployment (1 replica = ~10%)
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: canary-demo
      track: canary
  template:
    metadata:
      labels:
        app: canary-demo
        track: canary
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
EOF

# Service routes to both
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: canary-svc
spec:
  selector:
    app: canary-demo
  ports:
  - port: 80
EOF

# Gradually increase canary
k scale deploy canary --replicas=3  # ~25%
k scale deploy stable --replicas=7

# Full rollout
k scale deploy canary --replicas=10
k scale deploy stable --replicas=0

# Cleanup
k delete deploy stable canary
k delete svc canary-svc
```

---

## Practice Drills

### Drill 1: Rolling Update Config (Target: 3 minutes)

```bash
# Create with specific rolling update settings
k create deploy drill1 --image=nginx:1.20 --replicas=4

# Patch strategy
k patch deploy drill1 -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxSurge":1,"maxUnavailable":0}}}}'

# Update and observe
k set image deploy/drill1 nginx=nginx:1.21
k rollout status deploy/drill1

# Cleanup
k delete deploy drill1
```

### Drill 2: Recreate Strategy (Target: 2 minutes)

```bash
# Create with recreate strategy
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill2
spec:
  replicas: 3
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: drill2
  template:
    metadata:
      labels:
        app: drill2
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
EOF

# Update (watch all pods terminate first)
k set image deploy/drill2 nginx=nginx:1.21
k get pods -l app=drill2 -w

# Cleanup
k delete deploy drill2
```

### Drill 3: Blue/Green Switch (Target: 4 minutes)

```bash
# Create blue
k create deploy blue --image=nginx:1.20 --replicas=2
k patch deploy blue -p '{"spec":{"selector":{"matchLabels":{"version":"blue"}},"template":{"metadata":{"labels":{"version":"blue"}}}}}'

# Service
k expose deploy blue --name=app --port=80 --selector=version=blue

# Create green
k create deploy green --image=nginx:1.21 --replicas=2
k patch deploy green -p '{"spec":{"selector":{"matchLabels":{"version":"green"}},"template":{"metadata":{"labels":{"version":"green"}}}}}'

# Switch
k patch svc app -p '{"spec":{"selector":{"version":"green"}}}'

# Verify
k get ep app

# Cleanup
k delete deploy blue green
k delete svc app
```

### Drill 4: Canary Percentage (Target: 3 minutes)

```bash
# 10% canary
k create deploy stable --image=nginx:1.20 --replicas=9
k create deploy canary --image=nginx:1.21 --replicas=1

# Add common label
k patch deploy stable -p '{"spec":{"template":{"metadata":{"labels":{"app":"myapp"}}}}}'
k patch deploy canary -p '{"spec":{"template":{"metadata":{"labels":{"app":"myapp"}}}}}'

# Service for both
k expose deploy stable --name=myapp --port=80 --selector=app=myapp

# Verify endpoints include both
k get ep myapp

# Cleanup
k delete deploy stable canary
k delete svc myapp
```

### Drill 5: Zero-Downtime Verification (Target: 3 minutes)

```bash
# Create deployment with readiness probe
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill5
spec:
  replicas: 3
  strategy:
    rollingUpdate:
      maxUnavailable: 0
  selector:
    matchLabels:
      app: drill5
  template:
    metadata:
      labels:
        app: drill5
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        readinessProbe:
          httpGet:
            path: /
            port: 80
EOF

# Service
k expose deploy drill5 --port=80

# Update (zero downtime)
k set image deploy/drill5 nginx=nginx:1.21
k rollout status deploy/drill5

# Cleanup
k delete deploy drill5
k delete svc drill5
```

### Drill 6: Complete Deployment Strategy Scenario (Target: 6 minutes)

**Scenario**: Production deployment with canary testing.

```bash
# 1. Deploy stable version
k create deploy prod --image=nginx:1.20 --replicas=5

# 2. Expose service
k expose deploy prod --name=production --port=80

# 3. Create canary (10%)
k create deploy canary --image=nginx:1.21 --replicas=1

# 4. Point service to both
k patch deploy prod -p '{"spec":{"template":{"metadata":{"labels":{"release":"production"}}}}}'
k patch deploy canary -p '{"spec":{"template":{"metadata":{"labels":{"release":"production"}}}}}'
k patch svc production -p '{"spec":{"selector":{"release":"production"}}}'

# 5. Test canary
k logs -l app=canary

# 6. Gradual rollout
k scale deploy canary --replicas=3
k scale deploy prod --replicas=3

# 7. Full rollout
k scale deploy canary --replicas=5
k scale deploy prod --replicas=0

# 8. Cleanup
k delete deploy prod canary
k delete svc production
```

---

## Next Module

[Part 2 Cumulative Quiz](../part2-cumulative-quiz/) - Test your Application Deployment knowledge.

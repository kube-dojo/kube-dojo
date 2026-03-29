---
title: "Module 1.4: Deployments - Managing Applications"
slug: prerequisites/kubernetes-basics/module-1.4-deployments/
sidebar:
  order: 5
lab:
  id: "prereq-k8s-1.4-deployments"
  url: "https://killercoda.com/kubedojo/scenario/prereq-k8s-1.4-deployments"
  duration: "30 min"
  difficulty: "beginner"
  environment: "kubernetes"
---
> **Complexity**: `[MEDIUM]` - Core workload management
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 3 (Pods)

---

## Why This Module Matters

In production, you never create Pods directly. You use Deployments. Deployments manage Pods for you—handling scaling, updates, and self-healing automatically.

---

## Why Deployments?

Pods alone have problems:

```
┌─────────────────────────────────────────────────────────────┐
│              PODS ALONE vs DEPLOYMENTS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  NAKED POD:                                                │
│  - Pod dies → stays dead                                   │
│  - Node fails → Pod is lost                                │
│  - Can't scale easily                                       │
│  - Updates require manual delete/create                    │
│                                                             │
│  WITH DEPLOYMENT:                                           │
│  - Pod dies → automatically recreated                      │
│  - Node fails → rescheduled elsewhere                      │
│  - Scale with one command                                  │
│  - Rolling updates with zero downtime                      │
│  - Rollback to previous versions                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Creating Deployments

### Imperative (Quick Testing)

```bash
# Create deployment
kubectl create deployment nginx --image=nginx

# With replicas
kubectl create deployment nginx --image=nginx --replicas=3

# Dry run to see YAML
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml
```

### Declarative (Production Way)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 3                    # Number of pod copies
  selector:                      # How to find pods to manage
    matchLabels:
      app: nginx
  template:                      # Pod template
    metadata:
      labels:
        app: nginx               # Must match selector
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
```

```bash
kubectl apply -f deployment.yaml
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              DEPLOYMENT HIERARCHY                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   DEPLOYMENT                         │   │
│  │  - Defines desired state                            │   │
│  │  - Manages ReplicaSets                              │   │
│  │  - Handles updates/rollbacks                        │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   REPLICASET                        │   │
│  │  - Ensures N pods are running                       │   │
│  │  - Created/managed by Deployment                    │   │
│  │  - Usually don't interact directly                  │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                     │
│         ┌─────────────┼─────────────┐                      │
│         ▼             ▼             ▼                      │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐               │
│  │    POD    │ │    POD    │ │    POD    │               │
│  │   nginx   │ │   nginx   │ │   nginx   │               │
│  └───────────┘ └───────────┘ └───────────┘               │
│                                                             │
│  replicas: 3 → 3 pods maintained automatically             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Operations

### View Deployments

```bash
# List deployments
kubectl get deployments
kubectl get deploy              # Short form

# Detailed info
kubectl describe deployment nginx

# See related resources
kubectl get deploy,rs,pods
```

### Scaling

```bash
# Scale up/down
kubectl scale deployment nginx --replicas=5

# Or edit YAML and apply
kubectl edit deployment nginx
# Change replicas, save

# Watch pods scale
kubectl get pods -w
```

### Updates (Rolling)

```bash
# Update image
kubectl set image deployment/nginx nginx=nginx:1.26

# Or edit deployment
kubectl edit deployment nginx

# Watch rollout
kubectl rollout status deployment nginx

# View rollout history
kubectl rollout history deployment nginx
```

### Rollback

```bash
# Undo last change
kubectl rollout undo deployment nginx

# Rollback to specific revision
kubectl rollout history deployment nginx
kubectl rollout undo deployment nginx --to-revision=2
```

---

## Rolling Update Strategy

Deployments update Pods gradually:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max extra pods during update
      maxUnavailable: 25%  # Max pods that can be unavailable
```

```
┌─────────────────────────────────────────────────────────────┐
│              ROLLING UPDATE PROCESS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Initial state (3 replicas, v1):                           │
│  [v1] [v1] [v1]                                            │
│                                                             │
│  Update to v2 begins:                                      │
│  [v1] [v1] [v1] [v2]    ← New pod created                  │
│                                                             │
│  New pod ready:                                            │
│  [v1] [v1] [v2] [v2]    ← Old pod terminated               │
│                                                             │
│  Continue:                                                  │
│  [v1] [v2] [v2] [v2]                                       │
│                                                             │
│  Complete:                                                  │
│  [v2] [v2] [v2]         ← All pods updated                 │
│                                                             │
│  Zero downtime! Traffic served throughout.                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment YAML Explained

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 3                    # Desired pod count
  selector:
    matchLabels:
      app: nginx                 # Must match template labels
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:                      # Pod template (same as Pod spec)
    metadata:
      labels:
        app: nginx               # Labels for service discovery
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

---

## Self-Healing in Action

```bash
# Create deployment
kubectl create deployment nginx --image=nginx --replicas=3

# See pods
kubectl get pods

# Delete a pod
kubectl delete pod <pod-name>

# Immediately check again
kubectl get pods
# A new pod is already being created!

# The deployment maintains desired state
kubectl get deployment nginx
# READY shows 3/3
```

---

## Did You Know?

- **Deployments don't directly manage Pods.** They manage ReplicaSets, which manage Pods. This enables rollback.

- **Each update creates a new ReplicaSet.** Old ReplicaSets are kept (with 0 replicas) for rollback history.

- **`maxSurge: 0, maxUnavailable: 0` is impossible.** You can't update without either creating new pods or terminating old ones.

- **`kubectl rollout restart`** triggers a new rollout without changing the spec. Useful for pulling new images with the same tag.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Selector doesn't match template labels | Deployment won't manage pods | Ensure labels match exactly |
| Using :latest tag | Can't rollback meaningfully | Use specific version tags |
| No resource limits | Can affect other workloads | Always set resources |
| Forgetting to wait for rollout | May see issues later | Use `rollout status` |

---

## Quiz

1. **What's the relationship between Deployment, ReplicaSet, and Pod?**
   <details>
   <summary>Answer</summary>
   Deployment manages ReplicaSets. ReplicaSet manages Pods. You interact with Deployments; they handle the rest automatically. ReplicaSets enable rollback by keeping old versions.
   </details>

2. **What happens if you delete a Pod managed by a Deployment?**
   <details>
   <summary>Answer</summary>
   The Deployment (via ReplicaSet) automatically creates a new Pod to maintain the desired replica count. This is self-healing.
   </details>

3. **How do you rollback a Deployment to the previous version?**
   <details>
   <summary>Answer</summary>
   `kubectl rollout undo deployment DEPLOYMENT_NAME`. For a specific revision: `kubectl rollout undo deployment DEPLOYMENT_NAME --to-revision=N`.
   </details>

4. **What does `maxSurge` control in rolling updates?**
   <details>
   <summary>Answer</summary>
   The maximum number of pods that can be created beyond the desired replica count during an update. `maxSurge: 25%` with 4 replicas allows 5 pods temporarily.
   </details>

---

## Hands-On Exercise

**Task**: Create a Deployment, scale it, update it, and roll back.

```bash
# 1. Create deployment
kubectl create deployment web --image=nginx:1.24

# 2. Scale to 3 replicas
kubectl scale deployment web --replicas=3

# 3. Verify
kubectl get deploy,rs,pods

# 4. Update image
kubectl set image deployment/web nginx=nginx:1.25

# 5. Watch rollout
kubectl rollout status deployment web

# 6. Check history
kubectl rollout history deployment web

# 7. Simulate problem - rollback
kubectl rollout undo deployment web

# 8. Verify rollback
kubectl get deployment web -o jsonpath='{.spec.template.spec.containers[0].image}'
# Should show nginx:1.24

# 9. Cleanup
kubectl delete deployment web
```

**Success criteria**: Deploy, scale, update, rollback all work.

---

## Summary

Deployments manage your applications:

**Features**:
- Declarative updates
- Rolling updates (zero downtime)
- Rollback capability
- Self-healing
- Easy scaling

**Key commands**:
- `kubectl create deployment`
- `kubectl scale deployment`
- `kubectl set image`
- `kubectl rollout status`
- `kubectl rollout undo`

**Best practices**:
- Always use Deployments (not naked Pods)
- Use specific image tags
- Set resource requests/limits

---

## Next Module

[Module 5: Services](module-1.5-services/) - Stable networking for your Pods.

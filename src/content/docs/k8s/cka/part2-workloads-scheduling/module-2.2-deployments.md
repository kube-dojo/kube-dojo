---
title: "Module 2.2: Deployments & ReplicaSets"
slug: k8s/cka/part2-workloads-scheduling/module-2.2-deployments
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Core exam topic
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Module 2.1 (Pods)

---

## Why This Module Matters

In production, you never run standalone pods. You use **Deployments**.

Deployments are the most common workload resource. They handle:
- Running multiple replicas of your app
- Rolling updates with zero downtime
- Automatic rollbacks when things go wrong
- Scaling up and down

The CKA exam tests creating deployments, performing rolling updates, scaling, and rollbacks. These are fundamental skills you'll use daily.

> **The Fleet Manager Analogy**
>
> Think of a Deployment like a fleet manager for a taxi company. The manager doesn't drive taxis directly—they manage drivers (pods). If a driver calls in sick (pod crashes), the manager assigns a replacement. If demand increases (scale up), the manager hires more drivers. During a vehicle upgrade (rolling update), the manager swaps old cars for new ones gradually, ensuring customers always have rides available.

---

## What You'll Learn

By the end of this module, you'll be able to:
- Create and manage Deployments
- Understand how ReplicaSets work
- Perform rolling updates and rollbacks
- Scale applications horizontally
- Pause and resume deployments

---

## Part 1: Deployment Fundamentals

### 1.1 The Deployment Hierarchy

```
┌────────────────────────────────────────────────────────────────┐
│                    Deployment Hierarchy                         │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                     Deployment                           │  │
│   │  - Desired state (replicas, image, strategy)            │  │
│   │  - Manages ReplicaSets                                  │  │
│   └────────────────────────┬────────────────────────────────┘  │
│                            │ creates & manages                  │
│                            ▼                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    ReplicaSet                            │  │
│   │  - Ensures N replicas running                           │  │
│   │  - Creates/deletes pods to match desired count          │  │
│   └────────────────────────┬────────────────────────────────┘  │
│                            │ creates & manages                  │
│                            ▼                                    │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│   │  Pod 1  │  │  Pod 2  │  │  Pod 3  │  │  Pod N  │          │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Why Not Just ReplicaSets?

| Feature | ReplicaSet | Deployment |
|---------|------------|------------|
| Maintain replica count | ✅ | ✅ |
| Rolling updates | ❌ | ✅ |
| Rollback | ❌ | ✅ |
| Update history | ❌ | ✅ |
| Pause/Resume | ❌ | ✅ |

**Rule**: Always use Deployments. Never create ReplicaSets directly.

### 1.3 Deployment Spec

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3                    # Desired pod count
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

> **Critical**: The `spec.selector.matchLabels` must match `spec.template.metadata.labels`. If they don't match, the Deployment won't manage the pods.

---

## Part 2: Creating Deployments

### 2.1 Imperative Commands (Fast for Exam)

```bash
# Create deployment
kubectl create deployment nginx --image=nginx

# Create with specific replicas
kubectl create deployment nginx --image=nginx --replicas=3

# Create with port
kubectl create deployment nginx --image=nginx --port=80

# Generate YAML (essential for exam!)
kubectl create deployment nginx --image=nginx --replicas=3 --dry-run=client -o yaml > deploy.yaml
```

### 2.2 From YAML

```yaml
# nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
```

```bash
kubectl apply -f nginx-deployment.yaml
```

### 2.3 Viewing Deployments

```bash
# List deployments
kubectl get deployments
kubectl get deploy          # Short form

# Detailed view
kubectl get deploy -o wide

# Describe deployment
kubectl describe deployment nginx

# Get deployment YAML
kubectl get deployment nginx -o yaml

# Check rollout status
kubectl rollout status deployment/nginx
```

> **Did You Know?**
>
> The `kubectl rollout status` command blocks until the rollout completes. It's perfect for CI/CD pipelines—if the rollout fails, the command exits with a non-zero status.

---

## Part 3: ReplicaSets Under the Hood

### 3.1 How ReplicaSets Work

When you create a Deployment:
1. Deployment controller creates a ReplicaSet
2. ReplicaSet controller creates pods
3. ReplicaSet ensures desired replicas match actual

```bash
# Create a deployment
kubectl create deployment nginx --image=nginx --replicas=3

# See the ReplicaSet created
kubectl get replicasets
# NAME               DESIRED   CURRENT   READY   AGE
# nginx-5d5dd5d5fb   3         3         3       30s

# See pods with owner reference
kubectl get pods --show-labels
```

### 3.2 ReplicaSet Naming

```
nginx-5d5dd5d5fb
^     ^
|     |
|     └── Hash of pod template
|
└── Deployment name
```

When you update the deployment, a new ReplicaSet is created with a different hash.

### 3.3 Don't Manage ReplicaSets Directly

```bash
# Don't do this - let Deployment manage ReplicaSets
kubectl scale replicaset nginx-5d5dd5d5fb --replicas=5  # BAD

# Do this instead
kubectl scale deployment nginx --replicas=5             # GOOD
```

---

## Part 4: Scaling

### 4.1 Manual Scaling

```bash
# Scale to specific replicas
kubectl scale deployment nginx --replicas=5

# Scale to zero (stop all pods)
kubectl scale deployment nginx --replicas=0

# Scale multiple deployments
kubectl scale deployment nginx webapp --replicas=3
```

### 4.2 Editing Deployment

```bash
# Edit deployment directly
kubectl edit deployment nginx
# Change spec.replicas and save

# Or patch
kubectl patch deployment nginx -p '{"spec":{"replicas":5}}'
```

### 4.3 Verifying Scale

```bash
# Watch pods scale
kubectl get pods -w

# Check deployment status
kubectl get deployment nginx
# NAME    READY   UP-TO-DATE   AVAILABLE   AGE
# nginx   5/5     5            5           10m

# Detailed status
kubectl rollout status deployment/nginx
```

---

## Part 5: Rolling Updates

### 5.1 Update Strategy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 4
  strategy:
    type: RollingUpdate           # Default strategy
    rollingUpdate:
      maxSurge: 1                 # Max pods over desired during update
      maxUnavailable: 1           # Max pods unavailable during update
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
```

### 5.2 Rolling Update Visualization

```
┌────────────────────────────────────────────────────────────────┐
│                     Rolling Update                              │
│                     (maxSurge=1, maxUnavailable=1)             │
│                                                                 │
│   Desired: 4 replicas                                          │
│                                                                 │
│   Step 1: Start with old version                               │
│   [v1] [v1] [v1] [v1]                                          │
│                                                                 │
│   Step 2: Create 1 new pod (maxSurge=1)                        │
│   [v1] [v1] [v1] [v1] [v2-creating]                            │
│                                                                 │
│   Step 3: v2 ready, terminate 1 old (maxUnavailable=1)         │
│   [v1] [v1] [v1] [v2] [v1-terminating]                         │
│                                                                 │
│   Step 4: Continue rolling                                     │
│   [v1] [v1] [v2] [v2] [v1-terminating]                         │
│                                                                 │
│   Step 5: Continue rolling                                     │
│   [v1] [v2] [v2] [v2] [v1-terminating]                         │
│                                                                 │
│   Step 6: Complete                                             │
│   [v2] [v2] [v2] [v2]                                          │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 Triggering Updates

```bash
# Update image (triggers rolling update)
kubectl set image deployment/nginx nginx=nginx:1.26

# Update with record (saves command in history)
kubectl set image deployment/nginx nginx=nginx:1.26 --record

# Update environment variable
kubectl set env deployment/nginx ENV=production

# Update resources
kubectl set resources deployment/nginx -c nginx --limits=cpu=200m,memory=512Mi

# Edit deployment (any change to pod template triggers update)
kubectl edit deployment nginx
```

### 5.4 Watching Updates

```bash
# Watch rollout progress
kubectl rollout status deployment/nginx

# Watch pods during update
kubectl get pods -w

# Watch ReplicaSets
kubectl get rs -w
```

> **Exam Tip**
>
> During the exam, use `kubectl set image` for quick updates. It's faster than editing YAML. Add `--record` to save the command in rollout history.

---

## Part 6: Rollbacks

### 6.1 View Rollout History

```bash
# View history
kubectl rollout history deployment/nginx

# View specific revision
kubectl rollout history deployment/nginx --revision=2
```

### 6.2 Performing Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/nginx

# Rollback to specific revision
kubectl rollout undo deployment/nginx --to-revision=2

# Verify rollback
kubectl rollout status deployment/nginx
kubectl get deployment nginx -o wide
```

### 6.3 How Rollback Works

```
┌────────────────────────────────────────────────────────────────┐
│                     Rollback Process                            │
│                                                                 │
│   Before Rollback:                                             │
│   ┌─────────────────────────────────────────────────┐          │
│   │ ReplicaSet v1  (replicas: 0)  ← old version    │          │
│   │ ReplicaSet v2  (replicas: 4)  ← current        │          │
│   └─────────────────────────────────────────────────┘          │
│                                                                 │
│   kubectl rollout undo deployment/nginx                        │
│                                                                 │
│   After Rollback:                                              │
│   ┌─────────────────────────────────────────────────┐          │
│   │ ReplicaSet v1  (replicas: 4)  ← restored       │          │
│   │ ReplicaSet v2  (replicas: 0)  ← scaled down    │          │
│   └─────────────────────────────────────────────────┘          │
│                                                                 │
│   Deployment keeps old ReplicaSets for rollback capability     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.4 Controlling History

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  revisionHistoryLimit: 10    # Keep 10 old ReplicaSets (default)
  # Set to 0 to disable rollback capability
```

> **War Story: The Accidental Production Outage**
>
> A team deployed a broken image to production. Panic ensued. The engineer who knew about `kubectl rollout undo` saved the day in seconds. The engineer who didn't spent 20 minutes trying to figure out the previous image tag. Know your rollback commands!

---

## Part 7: Pause and Resume

### 7.1 Why Pause?

Pause a deployment to:
- Make multiple changes without triggering multiple rollouts
- Batch updates together
- Debug without new pods being created

### 7.2 Using Pause/Resume

```bash
# Pause deployment
kubectl rollout pause deployment/nginx

# Make multiple changes (no rollout triggered)
kubectl set image deployment/nginx nginx=nginx:1.26
kubectl set resources deployment/nginx -c nginx --limits=cpu=200m
kubectl set env deployment/nginx ENV=production

# Resume - triggers single rollout with all changes
kubectl rollout resume deployment/nginx

# Watch the rollout
kubectl rollout status deployment/nginx
```

---

## Part 8: Recreate Strategy

### 8.1 When to Use Recreate

Use `Recreate` when:
- Application can't run multiple versions simultaneously
- Database schema incompatibility between versions
- Limited resources (can't run extra pods)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
spec:
  replicas: 1
  strategy:
    type: Recreate          # All pods deleted, then new pods created
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: db
        image: postgres:15
```

### 8.2 Recreate vs RollingUpdate

| Aspect | RollingUpdate | Recreate |
|--------|---------------|----------|
| Downtime | Zero (if configured correctly) | Yes |
| Resource usage | Higher during update | Same |
| Complexity | Higher | Simple |
| Use case | Stateless apps | Stateful, incompatible versions |

---

## Part 9: Deployment Conditions

### 9.1 Checking Conditions

```bash
# View conditions
kubectl get deployment nginx -o jsonpath='{.status.conditions[*].type}'

# Detailed conditions
kubectl describe deployment nginx | grep -A10 Conditions
```

### 9.2 Common Conditions

| Condition | Meaning |
|-----------|---------|
| `Available` | Minimum replicas available |
| `Progressing` | Rollout in progress |
| `ReplicaFailure` | Failed to create pods |

---

## Did You Know?

- **Deployments are declarative**: You specify desired state, Kubernetes figures out how to get there.

- **ReplicaSets are immutable**: When you update a Deployment, a new ReplicaSet is created. The old one is kept for rollback.

- **Default strategy is RollingUpdate** with `maxSurge: 25%` and `maxUnavailable: 25%`.

- **`--record` is deprecated** in newer versions but still works. Annotations now track changes automatically.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Labels don't match selector | Deployment doesn't manage pods | Ensure `selector.matchLabels` matches `template.metadata.labels` |
| Missing resource limits | Pods can starve other workloads | Always set requests and limits |
| Rolling back without checking | May restore broken version | Check `rollout history --revision=N` first |
| Using `latest` tag | Rollout may not trigger | Use specific version tags |
| Not verifying rollout | Assuming success | Always run `rollout status` |

---

## Quiz

1. **What happens when you update a Deployment's image?**
   <details>
   <summary>Answer</summary>
   A rolling update is triggered: A new ReplicaSet is created with the new image. Pods are gradually created in the new ReplicaSet while pods in the old ReplicaSet are terminated, controlled by `maxSurge` and `maxUnavailable`.
   </details>

2. **How do you rollback a deployment to revision 3?**
   <details>
   <summary>Answer</summary>
   `kubectl rollout undo deployment/nginx --to-revision=3`

   This scales up the ReplicaSet from revision 3 and scales down the current ReplicaSet.
   </details>

3. **What's the difference between RollingUpdate and Recreate strategies?**
   <details>
   <summary>Answer</summary>
   **RollingUpdate**: Gradually replaces old pods with new ones, maintaining availability. **Recreate**: Terminates all existing pods first, then creates new ones—causes downtime.
   </details>

4. **You need to change image, resources, and env vars. How do you make one rollout instead of three?**
   <details>
   <summary>Answer</summary>
   ```bash
   kubectl rollout pause deployment/nginx
   kubectl set image deployment/nginx nginx=nginx:1.26
   kubectl set resources deployment/nginx -c nginx --limits=cpu=200m
   kubectl set env deployment/nginx ENV=production
   kubectl rollout resume deployment/nginx
   ```
   </details>

---

## Hands-On Exercise

**Task**: Complete deployment lifecycle—create, scale, update, rollback.

**Steps**:

1. **Create a deployment**:
```bash
kubectl create deployment webapp --image=nginx:1.24 --replicas=3
kubectl rollout status deployment/webapp
```

2. **Verify deployment and ReplicaSet**:
```bash
kubectl get deployment webapp
kubectl get replicaset
kubectl get pods -l app=webapp
```

3. **Scale the deployment**:
```bash
kubectl scale deployment webapp --replicas=5
kubectl get pods -w  # Watch pods scale up
```

4. **Update image (rolling update)**:
```bash
kubectl set image deployment/webapp nginx=nginx:1.25 --record
kubectl rollout status deployment/webapp
```

5. **Check rollout history**:
```bash
kubectl rollout history deployment/webapp
kubectl get replicaset  # Notice two ReplicaSets now
```

6. **Deploy a "bad" version**:
```bash
kubectl set image deployment/webapp nginx=nginx:broken --record
kubectl rollout status deployment/webapp  # Will hang or fail
kubectl get pods  # Some in ImagePullBackOff
```

7. **Rollback to previous version**:
```bash
kubectl rollout undo deployment/webapp
kubectl rollout status deployment/webapp
kubectl get pods  # Back to healthy state
```

8. **Check history and rollback to specific revision**:
```bash
kubectl rollout history deployment/webapp
kubectl rollout undo deployment/webapp --to-revision=1
kubectl rollout status deployment/webapp
```

9. **Cleanup**:
```bash
kubectl delete deployment webapp
```

**Success Criteria**:
- [ ] Can create deployments imperatively and declaratively
- [ ] Understand Deployment → ReplicaSet → Pod hierarchy
- [ ] Can scale deployments
- [ ] Can perform rolling updates
- [ ] Can rollback to previous versions
- [ ] Understand rollout history

---

## Practice Drills

### Drill 1: Deployment Creation Speed Test (Target: 2 minutes)

```bash
# Create deployment
kubectl create deployment nginx --image=nginx:1.25 --replicas=3

# Verify
kubectl rollout status deployment/nginx
kubectl get deploy nginx
kubectl get rs
kubectl get pods -l app=nginx

# Cleanup
kubectl delete deployment nginx
```

### Drill 2: Rolling Update (Target: 3 minutes)

```bash
# Create deployment
kubectl create deployment web --image=nginx:1.24 --replicas=4

# Wait for ready
kubectl rollout status deployment/web

# Update image
kubectl set image deployment/web nginx=nginx:1.25

# Watch the rollout
kubectl rollout status deployment/web

# Verify new image
kubectl get deployment web -o jsonpath='{.spec.template.spec.containers[0].image}'

# Cleanup
kubectl delete deployment web
```

### Drill 3: Rollback (Target: 3 minutes)

```bash
# Create deployment
kubectl create deployment app --image=nginx:1.24 --replicas=3
kubectl rollout status deployment/app

# Update 1
kubectl set image deployment/app nginx=nginx:1.25 --record
kubectl rollout status deployment/app

# Update 2 (bad version)
kubectl set image deployment/app nginx=nginx:bad --record
# Don't wait - it will fail

# Check history
kubectl rollout history deployment/app

# Rollback
kubectl rollout undo deployment/app
kubectl rollout status deployment/app

# Verify rolled back
kubectl get deployment app -o jsonpath='{.spec.template.spec.containers[0].image}'
# Should be nginx:1.25

# Cleanup
kubectl delete deployment app
```

### Drill 4: Scaling (Target: 2 minutes)

```bash
# Create deployment
kubectl create deployment scale-test --image=nginx --replicas=2

# Scale up
kubectl scale deployment scale-test --replicas=5
kubectl get pods -l app=scale-test

# Scale down
kubectl scale deployment scale-test --replicas=1
kubectl get pods -l app=scale-test

# Scale to zero
kubectl scale deployment scale-test --replicas=0
kubectl get pods -l app=scale-test  # No pods

# Scale back up
kubectl scale deployment scale-test --replicas=3

# Cleanup
kubectl delete deployment scale-test
```

### Drill 5: Pause and Resume (Target: 3 minutes)

```bash
# Create deployment
kubectl create deployment paused --image=nginx:1.24 --replicas=2
kubectl rollout status deployment/paused

# Pause
kubectl rollout pause deployment/paused

# Make multiple changes (no rollout triggered)
kubectl set image deployment/paused nginx=nginx:1.25
kubectl set env deployment/paused ENV=production
kubectl set resources deployment/paused -c nginx --requests=cpu=100m

# Check - still old image
kubectl get deployment paused -o jsonpath='{.spec.template.spec.containers[0].image}'

# Resume - single rollout
kubectl rollout resume deployment/paused
kubectl rollout status deployment/paused

# Verify all changes applied
kubectl get deployment paused -o yaml | grep -E "image:|ENV|cpu"

# Cleanup
kubectl delete deployment paused
```

### Drill 6: Recreate Strategy (Target: 3 minutes)

```bash
# Create deployment with Recreate strategy
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recreate-demo
spec:
  replicas: 3
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: recreate-demo
  template:
    metadata:
      labels:
        app: recreate-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.24
EOF

kubectl rollout status deployment/recreate-demo

# Update - watch all pods terminate then new ones create
kubectl set image deployment/recreate-demo nginx=nginx:1.25

# Watch pods (all old terminate, then all new create)
kubectl get pods -w -l app=recreate-demo

# Cleanup
kubectl delete deployment recreate-demo
```

### Drill 7: YAML Generation and Modification (Target: 5 minutes)

```bash
# Generate YAML
kubectl create deployment myapp --image=nginx:1.25 --replicas=3 --dry-run=client -o yaml > myapp.yaml

# View generated YAML
cat myapp.yaml

# Add resource limits using sed or edit
cat << 'EOF' >> myapp.yaml
---
# Note: Need to edit the file properly, this is just for demonstration
EOF

# Apply the deployment
kubectl apply -f myapp.yaml

# Update via edit
kubectl edit deployment myapp
# Change replicas to 5, save

# Verify
kubectl get deployment myapp

# Cleanup
kubectl delete -f myapp.yaml
rm myapp.yaml
```

### Drill 8: Challenge - Complete Lifecycle

Without looking at solutions, complete this workflow in under 5 minutes:

1. Create deployment `lifecycle-test` with nginx:1.24, 3 replicas
2. Scale to 5 replicas
3. Update to nginx:1.25
4. Check rollout history
5. Update to nginx:1.26
6. Rollback to nginx:1.24 (revision 1)
7. Delete deployment

```bash
# YOUR TASK: Complete the workflow
```

<details>
<summary>Solution</summary>

```bash
# 1. Create
kubectl create deployment lifecycle-test --image=nginx:1.24 --replicas=3
kubectl rollout status deployment/lifecycle-test

# 2. Scale
kubectl scale deployment lifecycle-test --replicas=5

# 3. Update to 1.25
kubectl set image deployment/lifecycle-test nginx=nginx:1.25 --record
kubectl rollout status deployment/lifecycle-test

# 4. Check history
kubectl rollout history deployment/lifecycle-test

# 5. Update to 1.26
kubectl set image deployment/lifecycle-test nginx=nginx:1.26 --record
kubectl rollout status deployment/lifecycle-test

# 6. Rollback to revision 1
kubectl rollout undo deployment/lifecycle-test --to-revision=1
kubectl rollout status deployment/lifecycle-test

# Verify it's 1.24
kubectl get deployment lifecycle-test -o jsonpath='{.spec.template.spec.containers[0].image}'

# 7. Delete
kubectl delete deployment lifecycle-test
```

</details>

---

## Next Module

[Module 2.3: DaemonSets & StatefulSets](../module-2.3-daemonsets-statefulsets/) - Specialized workload controllers.

# Module 2.1: Deployments Deep Dive

> **Complexity**: `[MEDIUM]` - Core CKAD skill with multiple operations
>
> **Time to Complete**: 45-55 minutes
>
> **Prerequisites**: Part 1 completed, understanding of Pods and ReplicaSets

---

## Why This Module Matters

Deployments are how you run applications in production Kubernetes. They manage ReplicaSets, which manage Pods. Understanding Deployments means understanding rolling updates, rollbacks, scaling, and the entire lifecycle of your application.

The CKAD heavily tests Deployment operations:
- Create and scale Deployments
- Perform rolling updates
- Rollback to previous versions
- Pause and resume rollouts
- Check rollout status and history

> **The Software Release Pipeline Analogy**
>
> A Deployment is like a release manager. When you want to ship a new version, the release manager (Deployment) creates a new production line (ReplicaSet) running the new code. It gradually moves traffic from the old line to the new one. If something goes wrong, it can quickly switch back to the old line. The workers (Pods) just follow instructions—the Deployment orchestrates everything.

---

## Deployment Basics

### Creating Deployments

```bash
# Imperative creation
k create deploy nginx --image=nginx:1.21 --replicas=3

# With port
k create deploy web --image=nginx --port=80

# Generate YAML
k create deploy api --image=httpd --replicas=2 --dry-run=client -o yaml > deploy.yaml
```

### Deployment YAML Structure

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 3
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
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `replicas` | Number of Pod copies to run |
| `selector.matchLabels` | How Deployment finds its Pods |
| `template` | Pod specification (must match selector labels) |
| `strategy` | How updates are performed |

---

## Scaling Deployments

### Manual Scaling

```bash
# Scale to 5 replicas
k scale deploy web-app --replicas=5

# Scale to zero (stop all pods)
k scale deploy web-app --replicas=0

# Scale multiple deployments
k scale deploy web-app api-server --replicas=3
```

### Check Scaling

```bash
# Watch pods scale
k get pods -l app=web -w

# Check deployment status
k get deploy web-app

# Detailed status
k describe deploy web-app | grep -A5 Replicas
```

---

## Rolling Updates

Rolling updates replace Pods gradually, ensuring zero downtime.

### Update Image

```bash
# Update container image
k set image deploy/web-app nginx=nginx:1.22

# Update with record (deprecated but still works)
k set image deploy/web-app nginx=nginx:1.22 --record

# Update using patch
k patch deploy web-app -p '{"spec":{"template":{"spec":{"containers":[{"name":"nginx","image":"nginx:1.22"}]}}}}'
```

### Update Strategy Configuration

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Max pods over desired count during update
      maxUnavailable: 0  # Max pods unavailable during update
```

| Setting | Description | Example |
|---------|-------------|---------|
| `maxSurge` | Extra pods allowed during update | `1` or `25%` |
| `maxUnavailable` | Pods that can be down during update | `0` or `25%` |

> **New in K8s 1.35: StatefulSet MaxUnavailable (Beta)**
>
> StatefulSets now support `maxUnavailable` in their `updateStrategy`, enabling parallel pod updates instead of sequential one-at-a-time. This can make StatefulSet updates **up to 60% faster** — critical for database clusters and stateful workloads:
> ```yaml
> updateStrategy:
>   type: RollingUpdate
>   rollingUpdate:
>     maxUnavailable: 2  # Update 2 pods at a time instead of 1
> ```

### Strategy Types

```yaml
# RollingUpdate (default) - gradual replacement
strategy:
  type: RollingUpdate

# Recreate - kill all, then create new
strategy:
  type: Recreate
```

Use `Recreate` when:
- Application can't run multiple versions simultaneously
- Database migrations require single version
- Downtime is acceptable

---

## Monitoring Rollouts

### Check Rollout Status

```bash
# Watch rollout progress
k rollout status deploy/web-app

# Check if rollout completed
k rollout status deploy/web-app --timeout=60s
```

### View Rollout History

```bash
# List revision history
k rollout history deploy/web-app

# See specific revision details
k rollout history deploy/web-app --revision=2

# Check current revision
k describe deploy web-app | grep -i revision
```

### Pause and Resume

```bash
# Pause rollout (for batched changes)
k rollout pause deploy/web-app

# Make multiple changes while paused
k set image deploy/web-app nginx=nginx:1.23
k set resources deploy/web-app -c nginx --limits=memory=256Mi

# Resume rollout
k rollout resume deploy/web-app
```

---

## Rollbacks

### Rollback to Previous Version

```bash
# Rollback to previous revision
k rollout undo deploy/web-app

# Rollback to specific revision
k rollout undo deploy/web-app --to-revision=2

# Check rollback status
k rollout status deploy/web-app
```

### Understanding Revisions

```bash
# Each change creates a new ReplicaSet
k get rs -l app=web

# Output:
# NAME                  DESIRED   CURRENT   READY   AGE
# web-app-6d8f9b6b4f   3         3         3       5m   (current)
# web-app-7b8c9d4e3a   0         0         0       10m  (previous)
```

Old ReplicaSets are kept (scaled to 0) for rollback capability.

### Limit Revision History

```yaml
spec:
  revisionHistoryLimit: 5  # Keep only 5 old ReplicaSets
```

---

## Deployment Conditions

### Check Deployment Health

```bash
# Get conditions
k get deploy web-app -o jsonpath='{.status.conditions[*].type}'

# Detailed conditions
k describe deploy web-app | grep -A10 Conditions
```

### Common Conditions

| Condition | Meaning |
|-----------|---------|
| `Available` | Minimum replicas are available |
| `Progressing` | Deployment is updating |
| `ReplicaFailure` | Couldn't create pods |

### Deployment Progress Deadline

```yaml
spec:
  progressDeadlineSeconds: 600  # Fail if no progress in 10 min
```

If a rollout stalls (e.g., image pull fails), it's marked as failed after this deadline.

---

## Labels and Selectors

### Selector Rules

The `selector.matchLabels` MUST match `template.metadata.labels`:

```yaml
spec:
  selector:
    matchLabels:
      app: web        # Must match below
      tier: frontend
  template:
    metadata:
      labels:
        app: web      # Must match above
        tier: frontend
        version: v1   # Can have extra labels
```

### Update Labels

```bash
# Add label to deployment (metadata only)
k label deploy web-app environment=production

# Add label to pods via template (triggers rollout)
k patch deploy web-app -p '{"spec":{"template":{"metadata":{"labels":{"version":"v2"}}}}}'
```

---

## Common Operations Quick Reference

```bash
# Create
k create deploy NAME --image=IMAGE --replicas=N

# Scale
k scale deploy NAME --replicas=N

# Update image
k set image deploy/NAME CONTAINER=IMAGE

# Update resources
k set resources deploy NAME -c CONTAINER --limits=cpu=200m,memory=512Mi

# Rollout status
k rollout status deploy/NAME

# Rollout history
k rollout history deploy/NAME

# Rollback
k rollout undo deploy/NAME

# Pause/Resume
k rollout pause deploy/NAME
k rollout resume deploy/NAME

# Restart all pods (rolling)
k rollout restart deploy/NAME
```

---

## Did You Know?

- **`kubectl rollout restart`** triggers a rolling restart without changing the image. It adds an annotation with the current timestamp, causing pods to recreate. Great for picking up ConfigMap changes.

- **Deployments don't delete old ReplicaSets immediately.** They keep them (scaled to 0) for rollback capability. Control this with `revisionHistoryLimit`.

- **The `--record` flag is deprecated** but still works. Kubernetes 1.22+ recommends using annotations instead to track change causes.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Selector doesn't match template labels | Deployment can't find its pods | Ensure labels match exactly |
| Using `Recreate` in production | Causes downtime | Use `RollingUpdate` with proper settings |
| `maxUnavailable: 100%` | All pods killed at once | Set reasonable percentages |
| Forgetting to check rollout status | Don't know if update succeeded | Always run `rollout status` |
| Not setting resource limits | Pods can consume all node resources | Always set requests and limits |

---

## Quiz

1. **How do you rollback a Deployment to revision 3?**
   <details>
   <summary>Answer</summary>
   `kubectl rollout undo deploy/NAME --to-revision=3`
   </details>

2. **What's the difference between `RollingUpdate` and `Recreate` strategies?**
   <details>
   <summary>Answer</summary>
   `RollingUpdate` gradually replaces pods (zero downtime), while `Recreate` terminates all existing pods before creating new ones (causes downtime but ensures only one version runs).
   </details>

3. **How do you trigger a rolling restart without changing the image?**
   <details>
   <summary>Answer</summary>
   `kubectl rollout restart deploy/NAME`. This adds a timestamp annotation that triggers pod recreation.
   </details>

4. **What happens if selector labels don't match template labels?**
   <details>
   <summary>Answer</summary>
   The Deployment won't be able to find or manage its pods. The API server will reject the Deployment with a validation error.
   </details>

---

## Hands-On Exercise

**Task**: Practice the full Deployment lifecycle.

**Part 1: Create and Scale**
```bash
# Create deployment
k create deploy webapp --image=nginx:1.20 --replicas=2

# Verify
k get deploy webapp
k get pods -l app=webapp

# Scale up
k scale deploy webapp --replicas=5

# Verify scaling
k get pods -l app=webapp -w
```

**Part 2: Rolling Update**
```bash
# Update image
k set image deploy/webapp nginx=nginx:1.21

# Watch rollout
k rollout status deploy/webapp

# Check history
k rollout history deploy/webapp

# Update again
k set image deploy/webapp nginx=nginx:1.22
```

**Part 3: Rollback**
```bash
# Rollback to previous
k rollout undo deploy/webapp

# Verify image reverted
k describe deploy webapp | grep Image

# Rollback to specific revision
k rollout history deploy/webapp
k rollout undo deploy/webapp --to-revision=1
```

**Part 4: Pause and Batch Changes**
```bash
# Pause
k rollout pause deploy/webapp

# Make multiple changes
k set image deploy/webapp nginx=nginx:1.23
k set resources deploy/webapp -c nginx --limits=memory=128Mi

# Resume
k rollout resume deploy/webapp

# Verify single rollout
k rollout status deploy/webapp
```

**Cleanup:**
```bash
k delete deploy webapp
```

---

## Practice Drills

### Drill 1: Basic Deployment (Target: 2 minutes)

```bash
# Create deployment with 3 replicas
k create deploy drill1 --image=nginx --replicas=3

# Verify all pods running
k get pods -l app=drill1

# Scale to 5
k scale deploy drill1 --replicas=5

# Verify
k get deploy drill1

# Cleanup
k delete deploy drill1
```

### Drill 2: Image Update (Target: 3 minutes)

```bash
# Create deployment
k create deploy drill2 --image=nginx:1.20

# Update image
k set image deploy/drill2 nginx=nginx:1.21

# Check rollout status
k rollout status deploy/drill2

# Verify new image
k describe deploy drill2 | grep Image

# Cleanup
k delete deploy drill2
```

### Drill 3: Rollback (Target: 3 minutes)

```bash
# Create and update multiple times
k create deploy drill3 --image=nginx:1.19
k set image deploy/drill3 nginx=nginx:1.20
k set image deploy/drill3 nginx=nginx:1.21

# Check history
k rollout history deploy/drill3

# Rollback to revision 1
k rollout undo deploy/drill3 --to-revision=1

# Verify image is 1.19
k describe deploy drill3 | grep Image

# Cleanup
k delete deploy drill3
```

### Drill 4: Rolling Update Settings (Target: 4 minutes)

```bash
# Create deployment with custom strategy
cat << 'EOF' | k apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drill4
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
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
        image: nginx:1.20
EOF

# Update and watch (should see 5 pods max, 4 always ready)
k set image deploy/drill4 nginx=nginx:1.21
k get pods -l app=drill4 -w

# Cleanup
k delete deploy drill4
```

### Drill 5: Pause and Resume (Target: 3 minutes)

```bash
# Create deployment
k create deploy drill5 --image=nginx:1.20

# Pause
k rollout pause deploy/drill5

# Make changes (no rollout yet)
k set image deploy/drill5 nginx=nginx:1.21
k set resources deploy/drill5 -c nginx --requests=cpu=100m

# Verify paused
k rollout status deploy/drill5

# Resume
k rollout resume deploy/drill5

# Check single rollout applied both changes
k rollout status deploy/drill5

# Cleanup
k delete deploy drill5
```

### Drill 6: Complete Deployment Scenario (Target: 6 minutes)

**Scenario**: Deploy an application, update it, encounter an issue, and rollback.

```bash
# 1. Create initial deployment
k create deploy production --image=nginx:1.20 --replicas=3

# 2. Expose as service
k expose deploy production --port=80

# 3. Verify working
k rollout status deploy/production
k get pods -l app=production

# 4. Update to "broken" image (simulate bad release)
k set image deploy/production nginx=nginx:broken-tag

# 5. Check rollout stalled
k rollout status deploy/production --timeout=30s

# 6. See problem pods
k get pods -l app=production

# 7. Rollback quickly
k rollout undo deploy/production

# 8. Verify recovered
k rollout status deploy/production
k get pods -l app=production

# 9. Cleanup
k delete deploy production
k delete svc production
```

---

## Next Module

[Module 2.2: Helm Package Manager](module-2.2-helm.md) - Deploy and manage applications with Helm charts.

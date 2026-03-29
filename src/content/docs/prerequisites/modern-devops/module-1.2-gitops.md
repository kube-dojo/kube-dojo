---
title: "Module 1.2: GitOps"
slug: prerequisites/modern-devops/module-1.2-gitops
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Key operational pattern
>
> **Time to Complete**: 30-35 minutes
>
> **Prerequisites**: Module 1 (Infrastructure as Code), Git basics

---

## Why This Module Matters

GitOps takes Infrastructure as Code to its logical conclusion: Git becomes the single source of truth for everything. Changes to infrastructure happen through pull requests, not direct commands. This pattern is becoming the standard for Kubernetes operations and will make you much more effective.

---

## What is GitOps?

GitOps is an operational model where:

1. **Git is the source of truth** for desired system state
2. **Changes happen through Git** (commits, pull requests)
3. **Automated agents** sync actual state to match Git
4. **Drift is automatically corrected** back to Git state

```
┌─────────────────────────────────────────────────────────────┐
│              TRADITIONAL vs GITOPS                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Traditional CI/CD (Push-based):                           │
│  ┌─────┐    ┌─────┐    ┌─────────┐    ┌─────────┐        │
│  │ Dev │───►│ Git │───►│   CI    │───►│ Cluster │        │
│  └─────┘    └─────┘    │ Pipeline│    └─────────┘        │
│                        └─────────┘                         │
│  CI pipeline pushes to cluster (needs cluster credentials) │
│                                                             │
│  GitOps (Pull-based):                                      │
│  ┌─────┐    ┌─────┐    ┌─────────┐    ┌─────────┐        │
│  │ Dev │───►│ Git │◄───│  GitOps │───►│ Cluster │        │
│  └─────┘    └─────┘    │  Agent  │    └─────────┘        │
│                        └─────────┘                         │
│  Agent pulls from Git and applies (agent lives in cluster) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Four Principles of GitOps

### 1. Declarative

Everything is described declaratively:

```yaml
# Not "run 3 nginx pods"
# But "desired state is 3 nginx pods"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  # ...
```

### 2. Versioned and Immutable

All changes go through Git:

```bash
git log --oneline manifests/
a1b2c3d Scale web to 5 replicas
d4e5f6g Add redis cache
g7h8i9j Initial deployment

# Every change is:
# - Versioned (commit hash)
# - Immutable (can't change history)
# - Attributed (who made it)
# - Reviewable (PR history)
```

### 3. Pulled Automatically

Agents continuously pull and apply:

```
┌─────────────────────────────────────────────────────────────┐
│  GitOps Agent Loop (every 30 seconds - 5 minutes):         │
│                                                             │
│  1. Check Git for changes                                  │
│  2. Compare Git state with cluster state                   │
│  3. If different: apply changes to cluster                 │
│  4. Repeat                                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Continuously Reconciled

Drift is automatically corrected:

```bash
# Someone manually edits production
kubectl scale deployment web --replicas=10

# GitOps agent detects drift
# Git says 3 replicas, cluster has 10
# Agent corrects: scales back to 3

# Result: Git always wins
```

---

## GitOps Tools

### Argo CD

The most popular GitOps tool for Kubernetes:

```
┌─────────────────────────────────────────────────────────────┐
│              ARGO CD ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │              KUBERNETES CLUSTER                  │       │
│  │                                                  │       │
│  │  ┌──────────────────────────────────────────┐  │       │
│  │  │           ARGO CD                         │  │       │
│  │  │  ┌────────────┐  ┌────────────────────┐ │  │       │
│  │  │  │ API Server │  │ Application        │ │  │       │
│  │  │  │            │  │ Controller         │ │  │       │
│  │  │  └────────────┘  │ (sync loop)        │ │  │       │
│  │  │                  └─────────┬──────────┘ │  │       │
│  │  │  ┌────────────┐            │            │  │       │
│  │  │  │ Web UI     │            │            │  │       │
│  │  │  │ (dashboard)│            │            │  │       │
│  │  │  └────────────┘            │            │  │       │
│  │  └────────────────────────────┼────────────┘  │       │
│  │                               │                │       │
│  │         ┌─────────────────────┘                │       │
│  │         ▼                                      │       │
│  │    ┌─────────┐  ┌─────────┐  ┌─────────┐     │       │
│  │    │ App 1   │  │ App 2   │  │ App 3   │     │       │
│  │    │(synced) │  │(synced) │  │(synced) │     │       │
│  │    └─────────┘  └─────────┘  └─────────┘     │       │
│  │                                               │       │
│  └───────────────────────────────────────────────┘       │
│                         ▲                                 │
│                         │ pulls manifests                │
│                    ┌────┴────┐                           │
│                    │   Git   │                           │
│                    │  Repo   │                           │
│                    └─────────┘                           │
│                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Flux CD

The CNCF-graduated alternative:

```yaml
# Flux GitRepository
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/myorg/my-app
  ref:
    branch: main

---
# Flux Kustomization (applies manifests)
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./kubernetes
  prune: true
  sourceRef:
    kind: GitRepository
    name: my-app
```

### Comparison

| Feature | Argo CD | Flux CD |
|---------|---------|---------|
| UI | Beautiful web dashboard | CLI-focused |
| Multi-tenancy | Built-in | Via namespaces |
| RBAC | Comprehensive | Kubernetes-native |
| Helm support | First-class | Via controllers |
| Learning curve | Moderate | Steeper |
| CNCF status | Graduated | Graduated |

---

## Repository Structure

### Monorepo (Everything Together)

```bash
gitops-repo/
├── apps/
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── backend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── database/
│       └── statefulset.yaml
├── infrastructure/
│   ├── ingress-nginx/
│   ├── cert-manager/
│   └── monitoring/
└── clusters/
    ├── production/
    │   └── kustomization.yaml
    └── staging/
        └── kustomization.yaml
```

### Polyrepo (Separate Repos)

```bash
# App repos (developers own)
frontend-app/
  └── kubernetes/
      ├── deployment.yaml
      └── service.yaml

# GitOps repo (ops owns)
gitops-config/
  └── clusters/
      ├── production/
      │   └── apps.yaml  # References app repos
      └── staging/
          └── apps.yaml
```

---

## GitOps Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              GITOPS DEPLOYMENT WORKFLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Developer makes change                                  │
│     └── Updates deployment.yaml (new image tag)            │
│                                                             │
│  2. Creates Pull Request                                    │
│     └── PR triggers: linting, validation, security scan    │
│                                                             │
│  3. Review and Approve                                      │
│     └── Team reviews, comments, approves                   │
│                                                             │
│  4. Merge to main                                          │
│     └── Git now has new desired state                      │
│                                                             │
│  5. GitOps agent detects change                            │
│     └── Compares Git state vs cluster state                │
│                                                             │
│  6. Agent applies change                                    │
│     └── kubectl apply (or Helm upgrade, etc.)              │
│                                                             │
│  7. Cluster reaches new state                              │
│     └── New pods running, old pods terminated              │
│                                                             │
│  Time from merge to deploy: ~30 seconds to 5 minutes       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Image Update Automation

Modern GitOps tools can automatically update image tags:

```yaml
# Argo CD Image Updater annotation
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: myapp=myrepo/myapp
    argocd-image-updater.argoproj.io/myapp.update-strategy: semver

# Flux Image Automation
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageUpdateAutomation
metadata:
  name: flux-system
spec:
  interval: 1m
  sourceRef:
    kind: GitRepository
    name: flux-system
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        email: fluxcdbot@users.noreply.github.com
        name: fluxcdbot
      messageTemplate: 'Update image to {{.NewTag}}'
    push:
      branch: main
```

```
Flow:
1. CI builds new image: myapp:v1.2.3
2. Pushes to registry
3. GitOps detects new tag
4. Updates Git repo with new tag
5. Syncs cluster to new image

Fully automated, fully audited in Git!
```

---

## Environment Promotion

```
┌─────────────────────────────────────────────────────────────┐
│              ENVIRONMENT PROMOTION                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  environments/                                              │
│  ├── base/                 # Common configuration          │
│  │   ├── deployment.yaml                                   │
│  │   └── service.yaml                                      │
│  ├── dev/                  # Dev overrides                 │
│  │   └── kustomization.yaml  (replicas: 1, image: latest) │
│  ├── staging/              # Staging overrides             │
│  │   └── kustomization.yaml  (replicas: 2, image: v1.2.3) │
│  └── prod/                 # Production overrides          │
│      └── kustomization.yaml  (replicas: 5, image: v1.2.2) │
│                                                             │
│  Promotion workflow:                                        │
│  1. Changes go to dev first (auto-deploy)                  │
│  2. Promote to staging (PR: update staging image tag)      │
│  3. Promote to prod (PR: update prod image tag)            │
│                                                             │
│  Each promotion is a Git commit = full audit trail         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Rollback with GitOps

Rollback is just `git revert`:

```bash
# Production has a bug!

# Option 1: Revert the commit
git revert abc123
git push

# GitOps agent syncs: old version restored
# Time to rollback: < 5 minutes

# Option 2: Use Argo CD UI
# Click "Rollback" on the application
# Argo reverts to previous sync state

# All rollbacks are tracked in Git history
git log --oneline
def456 Revert "Deploy v1.2.3"  # ← Rollback recorded
abc123 Deploy v1.2.3           # ← Bad deployment
```

---

## Did You Know?

- **The term "GitOps" was coined by Weaveworks** in 2017. It started as a blog post describing how they managed Kubernetes clusters.

- **GitOps eliminates "kubectl apply" from your workflow.** In a pure GitOps setup, no human ever runs kubectl against production. All changes go through Git.

- **Argo CD's name** comes from Greek mythology. Argo was the ship that carried Jason and the Argonauts. CD stands for Continuous Delivery.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Manual kubectl in production | Bypasses audit trail, causes drift | Use GitOps agent only |
| Secrets in Git | Security breach | Use sealed-secrets or external secrets |
| No PR review process | Bad changes go to prod | Require approvals |
| Sync too frequently | Cluster instability | 1-5 minute intervals |
| No health checks | Broken deployments stay | Configure health probes |

---

## Quiz

1. **What's the key difference between push-based and pull-based deployment?**
   <details>
   <summary>Answer</summary>
   Push-based: CI pipeline pushes changes to cluster (needs cluster credentials). Pull-based (GitOps): Agent in cluster pulls from Git and applies (only agent needs cluster access). GitOps is more secure because credentials stay in the cluster.
   </details>

2. **What happens if someone manually changes production in a GitOps setup?**
   <details>
   <summary>Answer</summary>
   The GitOps agent detects the drift between Git (desired state) and cluster (actual state), then corrects the cluster back to match Git. Manual changes are automatically reverted.
   </details>

3. **How do you rollback a deployment in GitOps?**
   <details>
   <summary>Answer</summary>
   `git revert <commit>` and push. The GitOps agent syncs the reverted state to the cluster. Everything is tracked in Git history.
   </details>

4. **Why is GitOps more secure than traditional CI/CD?**
   <details>
   <summary>Answer</summary>
   In traditional CI/CD, pipelines need cluster credentials (outside the cluster). In GitOps, only the agent (inside the cluster) has credentials. No credentials in CI systems, no credentials to leak.
   </details>

---

## Hands-On Exercise

**Task**: Experience GitOps concepts without installing Argo CD.

```bash
# This simulates GitOps behavior manually
# In real GitOps, an agent does this automatically

# 1. Create a "Git repo" (directory)
mkdir -p ~/gitops-demo/manifests
cd ~/gitops-demo

# 2. Create initial desired state
cat << 'EOF' > manifests/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitops-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gitops-demo
  template:
    metadata:
      labels:
        app: gitops-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.24
EOF

# 3. Apply (simulate GitOps sync)
kubectl apply -f manifests/

# 4. Verify
kubectl get deployment gitops-demo

# 5. Simulate drift (manual change)
kubectl scale deployment gitops-demo --replicas=5

# 6. Check drift
kubectl get deployment gitops-demo
# Shows 5 replicas

# 7. Reconcile (simulate GitOps correction)
kubectl apply -f manifests/
# Back to 2 replicas!

# 8. Make a "Git change"
sed -i '' 's/nginx:1.24/nginx:1.25/' manifests/deployment.yaml

# 9. Apply new state (simulate GitOps sync)
kubectl apply -f manifests/

# 10. Verify update
kubectl get deployment gitops-demo -o jsonpath='{.spec.template.spec.containers[0].image}'
# Shows nginx:1.25

# 11. Cleanup
kubectl delete -f manifests/
rm -rf ~/gitops-demo
```

**Success criteria**: Understand sync and drift correction.

---

## Summary

**GitOps** is the operational model for modern Kubernetes:

**Core principles**:
- Git is the single source of truth
- Changes through pull requests
- Automated sync to cluster
- Drift automatically corrected

**Tools**:
- Argo CD: Full-featured, great UI
- Flux CD: CNCF graduated, Kubernetes-native

**Benefits**:
- Full audit trail (Git history)
- Easy rollback (git revert)
- Better security (no CI cluster access)
- Self-documenting (state in Git)

**Key insight**: In GitOps, you never `kubectl apply` in production. You commit to Git, and the agent does the rest.

---

## Next Module

[Module 3: CI/CD Pipelines](../module-1.3-cicd-pipelines/) - Automating build, test, and deployment.

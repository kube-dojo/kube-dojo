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

## What You'll Be Able to Do

After this module, you will be able to:
- **Explain** the GitOps principle (Git as single source of truth) and how it differs from traditional CI/CD
- **Compare** push-based vs pull-based deployment models and explain why pull is more secure
- **Describe** how ArgoCD or Flux detects and corrects configuration drift automatically
- **Design** a basic GitOps repository structure for a multi-environment application

---

## Why This Module Matters

GitOps takes Infrastructure as Code to its logical conclusion: Git becomes the single source of truth for everything. Changes to infrastructure happen through pull requests, not direct commands. This pattern is becoming the standard for Kubernetes operations and will make you much more effective.

> **War Story**: At a previous fintech company, a senior engineer was troubleshooting a production issue at 2 AM and manually ran `kubectl edit deployment payment-gateway` to add a debug environment variable. The fix worked, but he forgot to update the source code. Two weeks later, a normal release went out, wiping his manual change. The payment gateway silently failed again, causing a 4-hour outage. This is the exact problem GitOps solves: by forcing all changes through Git and automatically overwriting manual cluster edits, your infrastructure repository always reflects reality.

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

> **Stop and think**: If Git is the single source of truth, what happens to imperative commands like `kubectl scale` or `kubectl edit`? Are they still useful in a GitOps environment?

Now that we understand the high-level concept of pull-based synchronization, let's explore the fundamental rules that make this model work in practice.

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

> **Pause and predict**: Based on the concept of continuous reconciliation, how quickly do you think a GitOps agent will revert a manual, unauthorized change made directly to the cluster?

With these principles establishing the foundation, we need specific software to execute the continuous reconciliation loop inside our clusters.

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

Here is a worked Argo CD configuration example that connects a Git repository to a cluster namespace:

```yaml
# A worked ArgoCD Application example
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: frontend-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://github.com/myorg/gitops-config.git'
    path: clusters/production/frontend
    targetRevision: HEAD
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: frontend-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
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

Before fully committing to these tools, it is crucial to understand that shifting to a pull-based model is not a silver bullet.

---

## The GitOps Trade-offs

While GitOps solves many problems, it introduces its own challenges:

- **Pros**: Complete audit trail via Git history, simplified rollback (`git revert`), enhanced security (CI systems don't need cluster credentials), and disaster recovery becomes as simple as pointing a new cluster at the Git repo.
- **Cons**: "Git commit" becomes the bottleneck for every minor change. Dealing with secrets requires additional tooling (like SealedSecrets or External Secrets Operator) since you cannot store plaintext passwords in Git. Finally, templating complex environments can lead to "YAML sprawl" if not managed carefully.

To mitigate some of these cons and maximize the benefits, you must carefully design how your Git repositories are organized.

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
- **GitOps is officially recognized by the CNCF** (Cloud Native Computing Foundation) through the Open GitOps working group, which standardized its core principles.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Manual `kubectl` in production | Bypasses the audit trail and causes configuration drift that gets overwritten. | Restrict cluster access; force all changes through the Git repository. |
| Storing raw secrets in Git | Exposes sensitive API keys and passwords to anyone with repository access. | Implement SealedSecrets, SOPS, or an External Secrets Operator. |
| Missing PR review process | Allows destructive or untested changes to automatically sync to production. | Enforce branch protection rules requiring at least one peer approval. |
| Syncing too frequently | Overloads the Kubernetes API server and causes unnecessary network traffic. | Configure the sync interval to a reasonable timeframe (e.g., 3-5 minutes). |
| Missing health checks | Allows broken deployments to remain running while the sync status shows "Healthy". | Configure proper readiness and liveness probes in your manifests. |
| Putting CI and CD in one repo | Causes infinite loops where CD updates trigger CI pipelines endlessly. | Separate your application code repository from your GitOps manifest repository. |
| Ignoring drift alerts | Leads to a false sense of security where the cluster diverges from Git without notice. | Configure Slack or email notifications for any ArgoCD or Flux "OutOfSync" events. |

---

## Quiz

1. **Scenario**: A critical vulnerability is discovered in your web application at 3 AM. The on-call engineer logs into the cluster and uses `kubectl set image` to immediately deploy a patched container. Ten minutes later, the vulnerability is back. What happened?
   <details>
   <summary>Answer</summary>
   The GitOps agent detected configuration drift between the cluster and the Git repository. Because the manual change was not recorded in Git, the agent assumed the cluster was in an incorrect state. It automatically reconciled the cluster back to the vulnerable image version specified in the repository. To fix this properly, the engineer must update the image tag in the Git repository, allowing the agent to pull the new state.
   </details>

2. **Scenario**: Your team decides to adopt GitOps and removes cluster administrator credentials from your Jenkins CI server. The security team asks how Jenkins will deploy the new application builds without these credentials. How should you explain the new deployment flow?
   <details>
   <summary>Answer</summary>
   Jenkins no longer pushes changes directly into the Kubernetes cluster. Instead, the CI pipeline's final step is to commit and push the newly built container image tag to the Git configuration repository. A GitOps agent running securely inside the cluster monitors this repository. When the agent sees the new commit, it pulls the updated manifests and applies them locally, eliminating the need for external systems to hold cluster credentials.
   </details>

3. **Scenario**: The latest release of your payment microservice contains a bug that is double-charging customers. You need to revert the system to the exact state it was in one hour ago as quickly as possible. How do you accomplish this in a pure GitOps environment?
   <details>
   <summary>Answer</summary>
   You execute a `git revert` command on the commit that introduced the broken payment service manifests, and push that reversion to the main branch. The GitOps agent will immediately detect this new commit and reconcile the cluster state to match the previous, stable configuration. Because Git history is immutable, this process provides a perfectly documented audit trail of both the failure and the rollback action.
   </details>

4. **Scenario**: You are designing the repository structure for a large enterprise with 50 microservices. The lead developer suggests keeping all Kubernetes manifests in the same repository as the application source code. What specific GitOps problem will this likely cause?
   <details>
   <summary>Answer</summary>
   Mixing application code and GitOps manifests in a single repository often triggers infinite CI/CD loops. When the CI pipeline builds a new image and updates the manifest in the repository, that new commit will re-trigger the CI pipeline, which builds another image, updates the manifest again, and so on. Additionally, this structure makes it very difficult to manage multi-environment configurations without massive duplication. To avoid this, teams should use a polyrepo structure with separate repositories for application source code and infrastructure manifests.
   </details>

5. **Scenario**: Your compliance department requires a complete audit log of who made changes to the production database configuration, when the changes were made, and who approved them. How does a pull-based GitOps model satisfy this requirement inherently?
   <details>
   <summary>Answer</summary>
   Because Git serves as the single source of truth, the `git log` acts as the definitive audit trail for all infrastructure changes. Every modification is tied to a specific developer's commit signature and timestamp. Furthermore, by enforcing Pull Requests and branch protection rules in your Git hosting platform, you automatically generate an immutable record of peer reviews and approvals before any change is allowed to sync to the cluster. This completely eliminates the need for external change management boards or manual logging.
   </details>

6. **Scenario**: A developer complains that their new deployment isn't showing up in the cluster, even though ArgoCD shows a green "Synced" status. When you inspect the cluster, the Pods are crashing in a CrashLoopBackOff state. Why didn't GitOps prevent this broken deployment?
   <details>
   <summary>Answer</summary>
   GitOps tools ensure that the requested resources are applied to the cluster, which is what the "Synced" status indicates. However, they rely on Kubernetes health probes to determine actual application health. If the developer failed to configure proper readiness and liveness checks in their deployment manifests, ArgoCD assumes the application is healthy as long as the Kubernetes API accepts the resources. You must configure proper probes so the GitOps agent can accurately report a "Degraded" health status and halt further rollouts.
   </details>

7. **Scenario**: You have an application deployed to a `staging` namespace and a `production` namespace. You want to update the staging environment with a new configuration without affecting production. How do you structure this change in your GitOps repository?
   <details>
   <summary>Answer</summary>
   You should utilize a tool like Kustomize or Helm within your GitOps repository to separate base configurations from environment-specific overrides. You would commit the new configuration strictly to the staging environment's overlay folder, leaving the production configuration untouched. The GitOps agent managing the staging environment will pull this specific path and apply the updates. Meanwhile, the production agent remains unaffected, ensuring safe environment isolation and preventing accidental cross-contamination.
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

**Success criteria**:
- [ ] You created a simulated Git repository directory and an initial deployment manifest.
- [ ] You applied the initial state and verified the correct number of replicas.
- [ ] You manually scaled the deployment to simulate configuration drift.
- [ ] You successfully reconciled the cluster back to the Git state, observing the replicas return to the desired count.
- [ ] You updated the image version in your simulated Git repo and applied it to see the change take effect.

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

[Module 1.3: CI/CD Pipelines](../module-1.3-cicd-pipelines/) - Automating build, test, and deployment.
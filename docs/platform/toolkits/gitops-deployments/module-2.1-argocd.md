# Module 2.1: ArgoCD

> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45-50 min

---

*The on-call engineer's phone buzzed at 2 AM: "Production is down." She SSH'd into the bastion, ran `kubectl get pods`—everything looked fine. But customers were seeing errors. After two hours of frantic debugging, she discovered it: someone had manually scaled the payment service to zero replicas "for testing" three days ago, then forgot to scale it back. No ticket. No pull request. No audit trail. The change existed only in cluster state, invisible to monitoring, unknown to the team. That night cost the e-commerce platform $890,000 in lost Black Friday pre-orders. The next Monday, the CTO demanded answers. "How do we prevent this from ever happening again?" The answer was GitOps—and ArgoCD became the tool that would transform their deployment culture from chaos to confidence.*

---

## Prerequisites

Before starting this module:
- [GitOps Discipline](../../disciplines/gitops/README.md) — GitOps principles and practices
- Kubernetes basics (Deployments, Services, Namespaces)
- Git fundamentals
- kubectl experience

## Why This Module Matters

ArgoCD is the most popular GitOps tool in the Kubernetes ecosystem. It watches Git repositories and automatically syncs your cluster state to match what's defined in version control. No more `kubectl apply` from laptops—every change is auditable, reviewable, and reversible.

Understanding ArgoCD isn't just about knowing the tool—it's about adopting a deployment philosophy that eliminates configuration drift and makes rollbacks trivial.

## Did You Know?

- **ArgoCD syncs over 1 million applications in production**—it's used by Intuit (its creator), Tesla, NVIDIA, and thousands of companies
- **The name "Argo" comes from Greek mythology**—the ship that carried Jason and the Argonauts, fitting for a tool that "navigates" deployments
- **ArgoCD was originally built for Intuit's 150+ Kubernetes clusters**—they needed a way to manage deployments at scale without tribal knowledge
- **ArgoCD supports 50+ config management tools**—Helm, Kustomize, Jsonnet, plain YAML, and custom plugins

## ArgoCD Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARGOCD ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GIT REPOSITORY                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  apps/                                                    │   │
│  │  ├── deployment.yaml                                      │   │
│  │  ├── service.yaml                                         │   │
│  │  └── configmap.yaml                                       │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │                                  │
│                               │ Watch + Fetch                    │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ARGOCD SERVER                          │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │ API Server  │  │ Repo Server │  │ Application │       │   │
│  │  │             │  │             │  │ Controller  │       │   │
│  │  │ • UI/CLI    │  │ • Clone     │  │             │       │   │
│  │  │ • Auth      │  │ • Render    │  │ • Watch     │       │   │
│  │  │ • RBAC      │  │ • Cache     │  │ • Sync      │       │   │
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘       │   │
│  │                                           │               │   │
│  └───────────────────────────────────────────┼──────────────┘   │
│                                              │                   │
│                                              │ Apply             │
│                                              ▼                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   KUBERNETES CLUSTER                      │   │
│  │                                                           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │   │
│  │  │ Deploy  │  │ Service │  │ Config  │  │ Secret  │     │   │
│  │  │         │  │         │  │  Map    │  │         │     │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **API Server** | Serves UI, CLI, RBAC, webhook endpoints |
| **Repo Server** | Clones repos, renders manifests (Helm/Kustomize) |
| **Application Controller** | Watches apps, detects drift, triggers sync |
| **Dex** | OIDC provider for SSO integration |
| **Redis** | Caching for repo server performance |

## Installing ArgoCD

### Quick Install

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods
kubectl -n argocd wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server --timeout=120s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo

# Port forward to access UI
kubectl -n argocd port-forward svc/argocd-server 8080:443 &
```

### Production Install with Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --set server.replicas=2 \
  --set controller.replicas=2 \
  --set repoServer.replicas=2 \
  --set redis.enabled=true \
  --set server.ingress.enabled=true \
  --set server.ingress.hosts[0]=argocd.example.com
```

### ArgoCD CLI

```bash
# Install CLI
brew install argocd  # macOS
# or
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd && sudo mv argocd /usr/local/bin/

# Login
argocd login localhost:8080 --username admin --password <password> --insecure

# Add cluster (if managing external clusters)
argocd cluster add my-cluster-context
```

## Applications

### Basic Application

```yaml
# app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/org/app-manifests.git
    targetRevision: HEAD
    path: apps/my-app

  destination:
    server: https://kubernetes.default.svc
    namespace: my-app

  syncPolicy:
    automated:
      prune: true       # Delete resources removed from Git
      selfHeal: true    # Revert manual changes
    syncOptions:
      - CreateNamespace=true
```

### Application with Helm

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://charts.bitnami.com/bitnami
    chart: nginx
    targetRevision: 15.4.0
    helm:
      releaseName: nginx
      values: |
        replicaCount: 3
        service:
          type: ClusterIP

      # Or reference values file from Git
      # valueFiles:
      #   - values-production.yaml

      # Or set individual parameters
      # parameters:
      #   - name: replicaCount
      #     value: "3"

  destination:
    server: https://kubernetes.default.svc
    namespace: nginx
```

### Application with Kustomize

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-production
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/org/app.git
    targetRevision: HEAD
    path: overlays/production

    # Kustomize-specific options
    kustomize:
      images:
        - myapp=myregistry/myapp:v2.0.0
      namePrefix: prod-
      commonLabels:
        env: production

  destination:
    server: https://kubernetes.default.svc
    namespace: production
```

## Sync Strategies

### Sync Waves and Hooks

```yaml
# Sync waves: Control order of resource creation
apiVersion: v1
kind: Namespace
metadata:
  name: my-app
  annotations:
    argocd.argoproj.io/sync-wave: "-1"  # Create first
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: config
  annotations:
    argocd.argoproj.io/sync-wave: "0"   # Create second
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  annotations:
    argocd.argoproj.io/sync-wave: "1"   # Create third
```

### Resource Hooks

```yaml
# Pre-sync hook: Run before sync
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: myapp:latest
          command: ["./migrate.sh"]
      restartPolicy: Never
---
# Post-sync hook: Run after sync
apiVersion: batch/v1
kind: Job
metadata:
  name: notify-slack
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      containers:
        - name: notify
          image: curlimages/curl
          command:
            - curl
            - -X
            - POST
            - $(SLACK_WEBHOOK)
            - -d
            - '{"text":"Deployment complete!"}'
      restartPolicy: Never
```

### Hook Types

| Hook | When It Runs |
|------|--------------|
| `PreSync` | Before sync begins |
| `Sync` | During sync (with manifests) |
| `PostSync` | After all Sync hooks complete |
| `SyncFail` | When sync fails |
| `Skip` | Skip applying this resource |

## App of Apps Pattern

### Why App of Apps?

```
MANAGING 50 APPLICATIONS:

Without App of Apps:                 With App of Apps:
─────────────────────────────────────────────────────────────────

argocd/                             argocd/
├── app1.yaml                       └── root-app.yaml  ◀── ONE FILE
├── app2.yaml
├── app3.yaml                       apps/
├── ...                             ├── app1/
└── app50.yaml                      │   └── application.yaml
                                    ├── app2/
50 Application CRs to manage        │   └── application.yaml
                                    └── ...

Problem: How do you deploy                ▲
the Application CRs themselves?           │
                                    Root app watches
                                    this directory
```

### Implementing App of Apps

```yaml
# root-app.yaml - The "app of apps"
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/argocd-apps.git
    targetRevision: HEAD
    path: apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

```
# Repository structure
argocd-apps/
├── apps/
│   ├── cert-manager/
│   │   └── application.yaml
│   ├── ingress-nginx/
│   │   └── application.yaml
│   ├── monitoring/
│   │   └── application.yaml
│   └── my-apps/
│       ├── app1.yaml
│       ├── app2.yaml
│       └── app3.yaml
└── root-app.yaml
```

```yaml
# apps/cert-manager/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cert-manager
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-2"  # Install early
spec:
  project: default
  source:
    repoURL: https://charts.jetstack.io
    chart: cert-manager
    targetRevision: v1.13.0
    helm:
      values: |
        installCRDs: true
  destination:
    server: https://kubernetes.default.svc
    namespace: cert-manager
```

## ApplicationSets

### Template-Based Application Generation

```yaml
# Generate apps from Git directories
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: cluster-addons
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/org/cluster-addons.git
        revision: HEAD
        directories:
          - path: addons/*

  template:
    metadata:
      name: '{{path.basename}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/org/cluster-addons.git
        targetRevision: HEAD
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{path.basename}}'
```

### Multi-Cluster Deployment

```yaml
# Deploy to multiple clusters
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: production
            url: https://prod.k8s.example.com
            values:
              replicas: "5"
          - cluster: staging
            url: https://staging.k8s.example.com
            values:
              replicas: "2"

  template:
    metadata:
      name: 'my-app-{{cluster}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/org/my-app.git
        targetRevision: HEAD
        path: deploy
        helm:
          parameters:
            - name: replicas
              value: '{{values.replicas}}'
      destination:
        server: '{{url}}'
        namespace: my-app
```

### Generator Types

| Generator | Use Case |
|-----------|----------|
| `list` | Static list of elements |
| `clusters` | All registered ArgoCD clusters |
| `git` | Directories or files in a Git repo |
| `matrix` | Combine two generators |
| `merge` | Merge multiple generators |
| `pullRequest` | GitHub/GitLab PRs for preview environments |

## Projects and RBAC

### ArgoCD Projects

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-a
  namespace: argocd
spec:
  description: Team A's applications

  # Allowed source repos
  sourceRepos:
    - https://github.com/org/team-a-*
    - https://charts.bitnami.com/bitnami

  # Allowed destination clusters/namespaces
  destinations:
    - namespace: team-a-*
      server: https://kubernetes.default.svc
    - namespace: '*'
      server: https://staging.example.com

  # Allowed resource kinds
  clusterResourceWhitelist:
    - group: ''
      kind: Namespace
  namespaceResourceWhitelist:
    - group: '*'
      kind: '*'

  # Deny specific resources
  namespaceResourceBlacklist:
    - group: ''
      kind: Secret  # Can't create secrets directly

  # Roles for this project
  roles:
    - name: developer
      description: Can sync applications
      policies:
        - p, proj:team-a:developer, applications, sync, team-a/*, allow
        - p, proj:team-a:developer, applications, get, team-a/*, allow
      groups:
        - team-a-developers  # OIDC group
```

### RBAC Policies

```yaml
# argocd-rbac-cm ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly

  policy.csv: |
    # Admin: Full access
    g, admins, role:admin

    # Developer: Sync and view
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */*, allow
    p, role:developer, logs, get, */*, allow

    # Viewer: Read-only
    p, role:viewer, applications, get, */*, allow
    p, role:viewer, projects, get, *, allow

    # Map groups to roles
    g, developers, role:developer
    g, viewers, role:viewer

  scopes: '[groups]'
```

## Multi-Tenancy

### Namespace Isolation

```yaml
# Restrict team to their namespaces
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-payments
  namespace: argocd
spec:
  destinations:
    # Only these namespaces
    - namespace: payments-*
      server: https://kubernetes.default.svc

  # Must use these labels
  clusterResourceWhitelist: []  # No cluster resources

  sourceRepos:
    - https://github.com/company/payments-*

  # Enforce resource quotas via sync waves
  orphanedResources:
    warn: true
```

### Soft Multi-Tenancy Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-TENANT ARGOCD                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TEAM A                        TEAM B                            │
│  ┌────────────────────┐       ┌────────────────────┐            │
│  │ Project: team-a    │       │ Project: team-b    │            │
│  │                    │       │                    │            │
│  │ Repos: org/team-a-*│       │ Repos: org/team-b-*│            │
│  │ NS: team-a-*       │       │ NS: team-b-*       │            │
│  └─────────┬──────────┘       └─────────┬──────────┘            │
│            │                            │                        │
│            ▼                            ▼                        │
│  ┌────────────────────┐       ┌────────────────────┐            │
│  │ team-a-production  │       │ team-b-production  │            │
│  │ team-a-staging     │       │ team-b-staging     │            │
│  └────────────────────┘       └────────────────────┘            │
│                                                                  │
│  SHARED ARGOCD INSTANCE                                          │
│  • SSO via OIDC (groups → project roles)                        │
│  • Audit logging enabled                                         │
│  • Resource quotas per project                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Secrets in Git | Exposed credentials | Use External Secrets, Sealed Secrets, or Vault |
| No sync waves | Resources created in wrong order | Use sync-wave annotations for dependencies |
| Ignoring prune | Orphaned resources accumulate | Enable `prune: true` or manage orphaned resources |
| Manual kubectl changes | Drift from Git source | Enable `selfHeal: true` to revert changes |
| No projects | No isolation between teams | Create projects per team with RBAC |
| Hardcoded image tags | Can't track what's deployed | Use image updater or Git automation |

## War Story: The $1.7 Million Git Merge

```
┌─────────────────────────────────────────────────────────────────┐
│  THE $1.7 MILLION GIT MERGE                                     │
│  ───────────────────────────────────────────────────────────────│
│  Company: B2B SaaS platform (500+ enterprise customers)         │
│  Stack: 127 microservices, 3 clusters, ArgoCD managed           │
│  The disaster: One merge, 47 services deleted, 6 hours down     │
└─────────────────────────────────────────────────────────────────┘
```

**Day 0 - The Merge**

A developer was cleaning up the repository. "Let's remove these old deployment files that are no longer needed." He identified 47 services in the `deprecated/` folder and deleted them. The PR passed code review—reviewers saw only file deletions, nothing alarming.

But there was a problem: the root ArgoCD Application had `prune: true` enabled. And the "deprecated" folder? It wasn't deprecated at all. A naming refactor months earlier had moved services there, but they were still in production.

```
THE MERGE TIMELINE
─────────────────────────────────────────────────────────────────
09:14 AM  PR merged to main
09:14 AM  ArgoCD detected change (30-second sync)
09:15 AM  ArgoCD synced: 47 services deleted from cluster
09:17 AM  First customer reports: "API returning 503"
09:22 AM  PagerDuty: 2,847 alerts in 5 minutes
09:25 AM  Engineering all-hands: "What happened?!"
09:45 AM  Root cause identified: services deleted by GitOps
10:00 AM  Git revert pushed to main
10:02 AM  ArgoCD synced: services recreating
10:15 AM  Database connection pools exhausted (cold start storm)
11:00 AM  Services recovering, still degraded
15:00 PM  Full recovery confirmed
```

**The Fallout**

```
INCIDENT IMPACT ASSESSMENT
─────────────────────────────────────────────────────────────────
Downtime duration:        5 hours 45 minutes
Services affected:        47 of 127 (37%)
Customers impacted:       312 enterprise accounts
SLA violations:           89 customers (99.9% SLA)

Financial Impact:
- SLA credit payouts:     $847,000
- Lost transactions:      $523,000
- Emergency response:     $67,000 (overtime, contractors)
- Customer churn (30d):   $312,000 (7 accounts)

Total quantifiable cost:  $1,749,000
```

**Why ArgoCD "Worked Correctly"**

ArgoCD did exactly what it was configured to do:
1. Git is the source of truth
2. Files were deleted from Git
3. `prune: true` was enabled
4. ArgoCD deleted resources not in Git

The tool wasn't broken—the process was.

**The Fix: Defense in Depth**

```yaml
# 1. Protect critical namespaces with finalizers
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payment-service
  finalizers:
    - resources-finalizer.argocd.argoproj.io
  annotations:
    # Require manual deletion, never auto-prune
    argocd.argoproj.io/sync-options: Prune=false

# 2. Warn before pruning
spec:
  syncPolicy:
    automated:
      prune: false  # Changed from true!
      selfHeal: true
  # Enable orphan warnings instead of auto-delete
  orphanedResources:
    warn: true
```

```yaml
# 3. CODEOWNERS protection for critical paths
# .github/CODEOWNERS
/apps/production/**  @platform-team @security-team
/infrastructure/**   @platform-team
```

**The Cultural Change**

After the incident, the team implemented:

1. **Prune disabled by default**: Services opt-in to pruning with explicit annotation
2. **Two-person review for deletions**: Any PR that removes files requires platform team approval
3. **Staging sync first**: Production ArgoCD syncs only after 1-hour staging bake time
4. **Sync windows**: Critical services can only sync during business hours

**Key Lessons**

1. **`prune: true` is a loaded gun**: Only enable for namespaces you're willing to lose
2. **Git history is your backup**: But recovery requires understanding what ArgoCD will do
3. **Review deletions carefully**: "Removing old files" PRs need scrutiny
4. **Staging isn't optional**: If ArgoCD would destroy staging, it'll destroy production
5. **GitOps amplifies mistakes**: The same property that makes recovery fast makes destruction fast

## Quiz

### Question 1
What's the difference between `selfHeal` and `prune` in ArgoCD sync policy?

<details>
<summary>Show Answer</summary>

**selfHeal**: Reverts manual changes made to the cluster that differ from Git. If someone runs `kubectl edit deployment` and changes replicas, ArgoCD will change it back.

**prune**: Deletes resources from the cluster that no longer exist in Git. If you remove a ConfigMap from your manifests, ArgoCD will delete it from the cluster.

Both can be dangerous if misconfigured:
- `selfHeal` can undo emergency fixes (disable before hotfixes)
- `prune` can delete stateful data (protect PVCs with annotations)
</details>

### Question 2
You have 5 services that must be deployed in order: Namespace → ConfigMap → Secret → Deployment → Ingress. How do you ensure this order?

<details>
<summary>Show Answer</summary>

Use sync waves with annotations:

```yaml
# namespace.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-2"

# configmap.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-1"

# secret.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"

# deployment.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"

# ingress.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"
```

Lower numbers sync first. ArgoCD waits for each wave's resources to be healthy before proceeding.
</details>

### Question 3
How would you deploy the same application to 10 clusters with different configurations per cluster?

<details>
<summary>Show Answer</summary>

Use an ApplicationSet with a list generator:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
spec:
  generators:
    - list:
        elements:
          - cluster: prod-us
            url: https://prod-us.example.com
            replicas: "10"
            region: us-east-1
          - cluster: prod-eu
            url: https://prod-eu.example.com
            replicas: "5"
            region: eu-west-1
          # ... 8 more clusters

  template:
    metadata:
      name: 'my-app-{{cluster}}'
    spec:
      source:
        repoURL: https://github.com/org/my-app.git
        path: deploy
        helm:
          parameters:
            - name: replicas
              value: '{{replicas}}'
            - name: region
              value: '{{region}}'
      destination:
        server: '{{url}}'
        namespace: my-app
```

For dynamic cluster lists, use the `clusters` generator with labels.
</details>

### Question 4
Your team accidentally pushed a broken config to Git and ArgoCD deployed it. How do you roll back?

<details>
<summary>Show Answer</summary>

Several options:

1. **Git revert** (recommended):
   ```bash
   git revert HEAD
   git push
   ```
   ArgoCD syncs the reverted state automatically.

2. **ArgoCD rollback**:
   ```bash
   argocd app rollback my-app --revision 5
   ```
   This syncs to a previous Git commit. Note: If auto-sync is enabled, it will re-sync to HEAD.

3. **Disable auto-sync, fix, re-enable**:
   ```bash
   argocd app set my-app --sync-policy none
   # Fix the issue in Git
   argocd app sync my-app
   argocd app set my-app --sync-policy automated
   ```

Git revert is preferred because it maintains the audit trail and works with any sync policy.
</details>

### Question 5
You're managing 150 applications across 5 clusters. Using individual Application CRs is becoming unwieldy. What ArgoCD pattern would you use?

<details>
<summary>Show Answer</summary>

Use **ApplicationSets** with multiple generators:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: cluster-apps
spec:
  generators:
    # Matrix: Combine clusters × apps
    - matrix:
        generators:
          - clusters: {}  # All registered clusters
          - git:
              repoURL: https://github.com/org/apps.git
              revision: HEAD
              directories:
                - path: apps/*

  template:
    metadata:
      name: '{{name}}-{{path.basename}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/org/apps.git
        path: '{{path}}'
      destination:
        server: '{{server}}'
        namespace: '{{path.basename}}'
```

This generates:
- 5 clusters × 30 apps = 150 Applications from ONE ApplicationSet
- Adding a cluster automatically deploys all apps
- Adding an app automatically deploys to all clusters
</details>

### Question 6
An application is showing "OutOfSync" status even though the Git source hasn't changed. What are the common causes and how do you debug?

<details>
<summary>Show Answer</summary>

**Common causes:**

1. **Defaulted fields**: Kubernetes API adds defaults that weren't in your manifest
2. **Mutations by controllers**: Admission webhooks or operators modify resources
3. **Immutable fields**: Some fields can't be changed after creation
4. **Annotation drift**: Timestamps or hash annotations added by other tools

**Debug steps:**

```bash
# 1. View the diff
argocd app diff my-app

# 2. Check what ArgoCD sees
argocd app get my-app --show-params

# 3. View raw manifests
argocd app manifests my-app --source live
argocd app manifests my-app --source git

# 4. Compare in UI
# ArgoCD UI shows side-by-side diff

# 5. If acceptable drift, ignore specific fields
```

**Fix with ignore differences:**

```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas  # Ignore HPA-managed replicas
    - group: ""
      kind: Service
      jqPathExpressions:
        - .metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"]
```
</details>

### Question 7
You need to prevent Team A from deploying to Team B's namespaces while sharing a single ArgoCD instance. How do you configure this?

<details>
<summary>Show Answer</summary>

Use **AppProjects** for namespace isolation:

```yaml
# Team A project
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-a
  namespace: argocd
spec:
  description: Team A applications

  # Can only deploy to team-a namespaces
  destinations:
    - namespace: team-a-*
      server: https://kubernetes.default.svc

  # Can only use team-a repos
  sourceRepos:
    - https://github.com/org/team-a-*

  # No cluster-wide resources
  clusterResourceWhitelist: []

  # Map OIDC group to project
  roles:
    - name: developer
      policies:
        - p, proj:team-a:developer, applications, *, team-a/*, allow
      groups:
        - team-a-developers  # OIDC group
```

**RBAC enforcement:**

```yaml
# argocd-rbac-cm ConfigMap
data:
  policy.csv: |
    # Team A can only access team-a project
    p, role:team-a-dev, applications, *, team-a/*, allow
    p, role:team-a-dev, logs, get, team-a/*, allow
    g, team-a-developers, role:team-a-dev

    # Default: deny
    p, role:default, *, *, *, deny
  policy.default: role:readonly
```
</details>

### Question 8
Calculate the resource requirements for ArgoCD managing 500 applications with 20 Git repositories, syncing every 3 minutes.

<details>
<summary>Show Answer</summary>

**Calculation approach:**

```
ARGOCD RESOURCE SIZING
─────────────────────────────────────────────────────────────────
Applications: 500
Git repos: 20
Sync interval: 3 minutes
Average manifests per app: 10

API Server:
- Handles UI, CLI, API calls
- Memory: ~200MB base + 1MB per 100 apps = 200 + 5 = 205MB
- Replicas: 2 (HA) = 410MB total
- CPU: 500m per replica

Repo Server:
- Clones repos, renders manifests
- Memory: ~100MB base + 50MB per repo = 100 + 1000 = 1.1GB
- Clones cached, but 20 repos with activity = significant
- Replicas: 2 (HA) = 2.2GB total
- CPU: 1 core per replica (manifest rendering is CPU-intensive)

Application Controller:
- Watches 500 apps, calculates diffs
- Memory: ~500MB base + 2MB per app = 500 + 1000 = 1.5GB
- Single instance (uses leader election)
- CPU: 2 cores (continuous reconciliation)

Redis:
- Caches repo contents, application state
- Memory: 512MB-1GB depending on manifest sizes
- Single instance (or Redis HA)

TOTAL ESTIMATE:
─────────────────────────────────────────────────────────────────
api-server:     2 × (500m CPU, 256MB)  = 1 core, 512MB
repo-server:    2 × (1 core, 1.5GB)    = 2 cores, 3GB
controller:     1 × (2 cores, 2GB)     = 2 cores, 2GB
redis:          1 × (200m CPU, 1GB)    = 200m, 1GB
─────────────────────────────────────────────────────────────────
Total:          ~5 cores, ~6.5GB memory

Plus buffer for spikes: 8 cores, 10GB memory recommended
```

**Scaling tips:**
- Increase repo-server replicas if manifest rendering is slow
- Use `--parallelism-limit` on controller to prevent thundering herd
- Consider sharding controller across clusters for >1000 apps
</details>

## Hands-On Exercise

### Scenario: GitOps for a Multi-Environment Application

Deploy an application to staging and production with ArgoCD, using different configurations per environment.

### Setup

```bash
# Create kind cluster
kind create cluster --name argocd-lab

# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods
kubectl -n argocd wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server --timeout=120s

# Get password
ARGO_PWD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD password: $ARGO_PWD"

# Port forward
kubectl -n argocd port-forward svc/argocd-server 8080:443 &
```

### Create Git Repository Structure

```bash
# Create local directory structure
mkdir -p argocd-lab/{base,overlays/{staging,production},apps}

# Base kustomization
cat > argocd-lab/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      containers:
        - name: app
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 10m
              memory: 32Mi
EOF

cat > argocd-lab/base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: demo-app
spec:
  selector:
    app: demo
  ports:
    - port: 80
EOF

cat > argocd-lab/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
EOF

# Staging overlay
cat > argocd-lab/overlays/staging/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: staging
namePrefix: staging-
resources:
  - ../../base
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 1
    target:
      kind: Deployment
      name: demo-app
EOF

# Production overlay
cat > argocd-lab/overlays/production/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: production
namePrefix: prod-
resources:
  - ../../base
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
    target:
      kind: Deployment
      name: demo-app
EOF
```

### Create ArgoCD Applications

Since we're using local files, we'll apply manifests directly:

```bash
# Create namespaces
kubectl create namespace staging
kubectl create namespace production

# Apply manifests
kubectl apply -k argocd-lab/overlays/staging/
kubectl apply -k argocd-lab/overlays/production/
```

For a real GitOps setup, create Application resources pointing to your Git repo:

```yaml
# apps/staging.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: demo-staging
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR_ORG/argocd-lab.git
    targetRevision: HEAD
    path: overlays/staging
  destination:
    server: https://kubernetes.default.svc
    namespace: staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### Verify Deployment

```bash
# Check staging (1 replica)
kubectl -n staging get pods

# Check production (3 replicas)
kubectl -n production get pods

# Access ArgoCD UI
open https://localhost:8080
# Login: admin / $ARGO_PWD
```

### Success Criteria

- [ ] ArgoCD is running and accessible
- [ ] Can view applications in the UI
- [ ] Staging has 1 replica
- [ ] Production has 3 replicas
- [ ] Understand Application and Kustomize structure

### Cleanup

```bash
kind delete cluster --name argocd-lab
rm -rf argocd-lab
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain ArgoCD's architecture: API Server, Repo Server, Application Controller
- [ ] Install ArgoCD and access the UI via port-forward or ingress
- [ ] Create Application CRs pointing to Git repos with Helm, Kustomize, or plain YAML
- [ ] Configure sync policies: `automated`, `prune`, and `selfHeal` with appropriate safeguards
- [ ] Use sync waves and hooks to control deployment order and run pre/post-sync jobs
- [ ] Implement App of Apps pattern for managing multiple applications
- [ ] Use ApplicationSets to generate applications from templates and generators
- [ ] Configure AppProjects and RBAC for multi-tenant isolation
- [ ] Troubleshoot sync failures: read diffs, check logs, use `ignoreDifferences`
- [ ] Roll back deployments using Git revert or ArgoCD CLI

## Next Module

Continue to [Module 2.2: Argo Rollouts](module-2.2-argo-rollouts.md) where we'll implement progressive delivery with canary and blue-green deployments.

---

*"The best deployment is the one you don't have to think about. GitOps with ArgoCD makes that possible."*

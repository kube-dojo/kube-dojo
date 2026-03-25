---
name: gitops-expert
description: GitOps discipline knowledge. Use for GitOps principles, ArgoCD, Flux, declarative infrastructure, reconciliation loops. Triggers on "GitOps", "ArgoCD", "Flux", "declarative", "reconciliation".
---

# GitOps Expert Skill

Authoritative knowledge source for GitOps principles, patterns, and tooling. Covers both theory and practical implementation with ArgoCD, Flux, and related ecosystem tools.

## When to Use
- Writing or reviewing GitOps curriculum content
- Designing GitOps workflows and repository structures
- Evaluating ArgoCD vs Flux
- Implementing progressive delivery
- Troubleshooting sync and drift issues

## Core GitOps Principles

### What is GitOps?

GitOps is an operational framework that takes DevOps best practices used for application development—version control, collaboration, compliance, CI/CD—and applies them to infrastructure automation.

**The GitOps Equation:**
```
IaC + MRs + CI/CD = GitOps
(Infrastructure as Code + Merge Requests + Continuous Deployment)
```

### The Four GitOps Principles (OpenGitOps)

| Principle | Description |
|-----------|-------------|
| **Declarative** | System state is described declaratively |
| **Versioned** | Desired state is versioned in Git |
| **Automated** | Approved changes are applied automatically |
| **Reconciled** | Software agents continuously ensure actual = desired |

### GitOps vs Traditional CI/CD

```
TRADITIONAL (Push-Based)
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│  Code  │───▶│   CI   │───▶│   CD   │───▶│ Cluster│
└────────┘    └────────┘    └────────┘    └────────┘
                                │
                        Pushes changes
                        (credentials needed)

GITOPS (Pull-Based)
┌────────┐    ┌────────┐    ┌────────┐
│  Code  │───▶│   CI   │───▶│  Git   │
└────────┘    └────────┘    └────────┘
                                │
                          Desired state
                                │
                                ▼
                        ┌──────────────┐
                        │ GitOps Agent │◀──┐
                        │  (in-cluster)│   │ Reconciles
                        └──────┬───────┘   │
                               │           │
                               ▼           │
                        ┌────────────┐     │
                        │  Cluster   │─────┘
                        │  (actual)  │
                        └────────────┘
```

## Key GitOps Concepts

### Reconciliation Loop

The GitOps agent continuously:
1. **Observes** - Reads desired state from Git
2. **Compares** - Diffs desired vs actual cluster state
3. **Acts** - Applies changes to match desired state
4. **Repeats** - Runs continuously (every 3-5 minutes typically)

### Drift Detection

**Drift** = actual state ≠ desired state

Causes:
- Manual kubectl changes
- Operators modifying resources
- External controllers
- Admission webhooks modifying resources

GitOps response to drift:
- **Alert** - Notify but don't fix (manual reconciliation)
- **Auto-heal** - Automatically revert to Git state (recommended)

### Application vs Infrastructure

| Layer | Examples | GitOps Approach |
|-------|----------|-----------------|
| Application | Deployments, Services | App-of-apps, Helm, Kustomize |
| Platform | Ingress controllers, cert-manager | Separate repo, bootstrap |
| Infrastructure | Clusters, networks, cloud resources | Crossplane, Terraform |

## Repository Strategies

### Monorepo

```
gitops-repo/
├── apps/
│   ├── app-a/
│   ├── app-b/
│   └── app-c/
├── infrastructure/
│   ├── ingress/
│   └── monitoring/
└── clusters/
    ├── dev/
    ├── staging/
    └── prod/
```

**Pros:** Simple, single source of truth, easy cross-cutting changes
**Cons:** Scale issues, broad permissions needed, blast radius

### Polyrepo

```
app-a-repo/           # App code + manifests
app-b-repo/
platform-repo/        # Shared infrastructure
cluster-config-repo/  # Cluster bootstrapping
```

**Pros:** Team autonomy, granular permissions, focused CI
**Cons:** Complexity, harder to see full picture, coordination overhead

### Hybrid (Recommended)

```
app-repos/            # Each app owns its manifests
├── app-a/
└── app-b/

platform-repo/        # Platform team owns infrastructure
├── base/
└── overlays/

environments-repo/    # Environment-specific config
├── dev/
├── staging/
└── prod/
```

## Environment Promotion

### Branch-per-Environment (Simple, Not Recommended)

```
main ────────────────────▶ dev cluster
     └── staging-branch ──▶ staging cluster
              └── prod-branch ──▶ prod cluster
```

**Problems:** Merge conflicts, divergent branches, hard to audit

### Directory-per-Environment (Recommended)

```
environments/
├── base/           # Common configuration
│   ├── deployment.yaml
│   └── service.yaml
├── dev/
│   └── kustomization.yaml  # patches for dev
├── staging/
│   └── kustomization.yaml  # patches for staging
└── prod/
    └── kustomization.yaml  # patches for prod
```

### Image Tag Promotion

```yaml
# environments/dev/kustomization.yaml
images:
  - name: myapp
    newTag: abc123  # Latest commit

# environments/prod/kustomization.yaml
images:
  - name: myapp
    newTag: v1.2.3  # Stable release
```

Promotion flow:
1. CI builds image with commit SHA
2. Update dev environment tag (auto or PR)
3. Test in dev/staging
4. Promote to prod via PR (changes only image tag)

## ArgoCD

### Core Concepts

| Concept | Description |
|---------|-------------|
| Application | A group of K8s resources from a Git source |
| AppProject | Logical grouping with access controls |
| ApplicationSet | Template for generating Applications |
| Sync | Process of applying Git state to cluster |

### ArgoCD Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      ARGOCD                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  API Server  │  │ Repo Server  │  │ Application  │  │
│  │    (UI)      │  │ (Git clone)  │  │  Controller  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                           │                  │          │
│                           ▼                  ▼          │
│                    ┌─────────────────────────────┐      │
│                    │         Redis Cache         │      │
│                    └─────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### ArgoCD Application Example

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/gitops-repo
    targetRevision: HEAD
    path: apps/my-app
  destination:
    server: https://kubernetes.default.svc
    namespace: my-app
  syncPolicy:
    automated:
      prune: true        # Delete resources removed from Git
      selfHeal: true     # Revert manual changes
    syncOptions:
      - CreateNamespace=true
```

### App of Apps Pattern

```yaml
# apps/root-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root
spec:
  source:
    path: apps/  # Directory containing other Application manifests
  destination:
    server: https://kubernetes.default.svc
```

### ApplicationSet

Generate Applications from templates:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: cluster-apps
spec:
  generators:
    - list:
        elements:
          - cluster: dev
            url: https://dev.example.com
          - cluster: prod
            url: https://prod.example.com
  template:
    metadata:
      name: '{{cluster}}-app'
    spec:
      destination:
        server: '{{url}}'
      source:
        path: 'environments/{{cluster}}'
```

## Flux

### Core Concepts

| Component | Purpose |
|-----------|---------|
| Source Controller | Fetches artifacts (Git, Helm, OCI) |
| Kustomize Controller | Reconciles Kustomizations |
| Helm Controller | Reconciles HelmReleases |
| Notification Controller | Handles alerts and events |
| Image Automation | Updates image tags automatically |

### Flux Architecture (GitOps Toolkit)

```
┌─────────────────────────────────────────────────────────┐
│                    FLUX CONTROLLERS                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Source    │  │  Kustomize   │  │     Helm     │  │
│  │  Controller  │  │  Controller  │  │  Controller  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ Notification │  │    Image     │                     │
│  │  Controller  │  │  Automation  │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### Flux GitRepository + Kustomization

```yaml
# Source: where to get manifests
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-repo
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/org/gitops-repo
  ref:
    branch: main
---
# Kustomization: what to apply
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./apps/my-app
  sourceRef:
    kind: GitRepository
    name: my-repo
  prune: true
  healthChecks:
    - kind: Deployment
      name: my-app
      namespace: my-app
```

## ArgoCD vs Flux

| Aspect | ArgoCD | Flux |
|--------|--------|------|
| UI | Built-in, polished | Third-party (Weave GitOps) |
| Architecture | Monolithic | Modular (GitOps Toolkit) |
| Multi-cluster | Application-centric | Cluster-centric |
| RBAC | Built-in AppProjects | Kubernetes native |
| Learning curve | Easier to start | More concepts |
| Extensibility | Plugin system | Compose controllers |
| CNCF Status | Graduated | Graduated |

**Choose ArgoCD if:** You want UI, simpler setup, application-focused
**Choose Flux if:** You want composability, GitOps Toolkit integration, image automation

## Progressive Delivery

### Deployment Strategies

| Strategy | Risk | Rollback Speed | Complexity |
|----------|------|----------------|------------|
| Recreate | High | Slow | Low |
| Rolling | Medium | Medium | Low |
| Blue/Green | Low | Fast | Medium |
| Canary | Very Low | Fast | High |

### Argo Rollouts

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: {duration: 5m}
        - setWeight: 30
        - pause: {duration: 5m}
        - setWeight: 50
        - pause: {duration: 5m}
  selector:
    matchLabels:
      app: my-app
  template:
    # Pod template...
```

### Flagger (Flux ecosystem)

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: my-app
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  service:
    port: 80
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        threshold: 99
```

## Secrets in GitOps

### The Problem
Git should store everything, but secrets can't be plaintext in Git.

### Solutions

| Solution | Approach | Complexity |
|----------|----------|------------|
| Sealed Secrets | Encrypt with cluster key | Low |
| SOPS | Encrypt with cloud KMS | Medium |
| External Secrets | Sync from Vault/AWS/etc | Medium |
| Vault Agent | Inject at runtime | High |

### External Secrets Example

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: my-secret
  data:
    - secretKey: password
      remoteRef:
        key: secret/data/myapp
        property: password
```

## Common GitOps Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Storing secrets in Git | Security breach | Sealed Secrets, ESO, SOPS |
| Manual kubectl | Drift, no audit trail | Everything through Git |
| Branch-per-env | Merge conflicts | Directory-per-env |
| No health checks | Silent failures | Sync hooks, health assessments |
| Giant monorepo | Scale, permissions | Hybrid approach |
| Ignoring drift | Actual ≠ desired | Enable auto-heal |

## Key Resources

- **OpenGitOps** - opengitops.dev (principles)
- **ArgoCD Docs** - argo-cd.readthedocs.io
- **Flux Docs** - fluxcd.io
- **GitOps Working Group** - github.com/gitops-working-group

*"Git is the source of truth. Everything else is a cache."*

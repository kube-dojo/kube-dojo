---
title: "Module 2.3: Flux"
slug: platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux
sidebar:
  order: 4
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 40-45 min

The platform engineer stared at the dashboard in disbelief. At 2:47 AM, their multi-cluster GitOps setup had saved them from what would have been a catastrophic misconfiguration. A developer had accidentally pushed a ConfigMap with `replicas: 0` for their payment service to the main branch. Within 90 seconds, Flux's image automation controller detected the change, and because they'd configured proper health checks, the Kustomization failed to reconcile—the cluster stayed healthy while the bad commit was automatically flagged. "Before Flux," she thought, "this would have taken down 12 clusters simultaneously." The company later estimated the prevented outage would have cost **$3.2 million** in lost transactions and SLA penalties.

## Prerequisites

Before starting this module:
- [Module 2.1: ArgoCD](../module-2.1-argocd/) — GitOps concepts (for comparison)
- [GitOps Discipline](../../../disciplines/delivery-automation/gitops/) — GitOps principles
- Kubernetes basics
- Git fundamentals

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Flux controllers and configure GitRepository, Kustomization, and HelmRelease resources**
- **Implement multi-cluster GitOps with Flux's toolkit approach and dependency ordering**
- **Configure image automation to detect new container images and update Git repositories automatically**
- **Compare Flux's controller-based architecture against ArgoCD for different organizational patterns**


## Why This Module Matters

Flux is the GitOps Toolkit—a set of specialized controllers that each do one thing well. While ArgoCD is an application, Flux is a framework. This gives you incredible flexibility but requires understanding how the pieces fit together.

Flux was created by Weaveworks, the company that coined "GitOps." It's now a CNCF graduated project, running in production at companies like Deutsche Telekom, Volvo, and SAP.

## Did You Know?

- **Weaveworks invented the term "GitOps" in 2017**—Flux was the first tool to implement the concept
- **Flux v2 was a complete rewrite**—the original Flux was a monolith; Flux v2 is a toolkit of specialized controllers
- **Flux can reconcile 1000+ resources per second**—its controller architecture makes it extremely efficient
- **Flux is the only CNCF graduated GitOps project**—ArgoCD is also CNCF but at incubating stage (as of 2024)

## Flux Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUX ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GIT REPOSITORY                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  clusters/                                                │   │
│  │  ├── production/                                          │   │
│  │  │   ├── flux-system/       (Flux components)            │   │
│  │  │   └── apps/              (Applications)               │   │
│  │  └── staging/                                             │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FLUX CONTROLLERS (GitOps Toolkit)            │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │   Source     │  │ Kustomize    │  │    Helm      │    │   │
│  │  │  Controller  │  │ Controller   │  │  Controller  │    │   │
│  │  │              │  │              │  │              │    │   │
│  │  │ Fetches Git, │  │ Applies      │  │ Manages Helm │    │   │
│  │  │ Helm repos,  │  │ Kustomize    │  │ releases     │    │   │
│  │  │ S3, OCI      │  │ overlays     │  │              │    │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │   │
│  │         │                 │                 │             │   │
│  │         └─────────────────┴─────────────────┘             │   │
│  │                           │                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │ Notification │  │    Image     │  │  Image       │    │   │
│  │  │ Controller   │  │  Reflector   │  │  Automation  │    │   │
│  │  │              │  │              │  │              │    │   │
│  │  │ Slack, Teams │  │ Scans        │  │ Updates Git  │    │   │
│  │  │ alerts       │  │ registries   │  │ with new     │    │   │
│  │  │              │  │ for tags     │  │ image tags   │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   KUBERNETES CLUSTER                      │   │
│  │                                                           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │   │
│  │  │ Deploy  │  │ Service │  │  Helm   │  │ Config  │     │   │
│  │  │         │  │         │  │ Release │  │  Map    │     │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Controllers

| Controller | CRD | Purpose |
|------------|-----|---------|
| **source-controller** | GitRepository, HelmRepository, OCIRepository, Bucket | Fetches artifacts from external sources |
| **kustomize-controller** | Kustomization | Applies Kustomize overlays |
| **helm-controller** | HelmRelease | Manages Helm chart installations |
| **notification-controller** | Alert, Provider | Sends notifications to Slack, Teams, etc. |
| **image-reflector-controller** | ImageRepository, ImagePolicy | Scans registries for new tags |
| **image-automation-controller** | ImageUpdateAutomation | Commits image tag updates to Git |

## Installing Flux

### Bootstrap with CLI

```bash
# Install Flux CLI
brew install fluxcd/tap/flux  # macOS
# or
curl -s https://fluxcd.io/install.sh | sudo bash

# Check prerequisites
flux check --pre

# Bootstrap with GitHub
flux bootstrap github \
  --owner=my-org \
  --repository=fleet-infra \
  --branch=main \
  --path=./clusters/my-cluster \
  --personal

# Bootstrap with GitLab
flux bootstrap gitlab \
  --owner=my-group \
  --repository=fleet-infra \
  --branch=main \
  --path=./clusters/my-cluster
```

### Bootstrap Result

```
# Creates this structure in your repo:
fleet-infra/
└── clusters/
    └── my-cluster/
        └── flux-system/
            ├── gotk-components.yaml    # Flux controllers
            ├── gotk-sync.yaml          # Self-management
            └── kustomization.yaml
```

### Manual Installation

```bash
# Install all components
kubectl apply -f https://github.com/fluxcd/flux2/releases/latest/download/install.yaml

# Or specific components
flux install \
  --components=source-controller,kustomize-controller,helm-controller \
  --export > flux-components.yaml
```

## Source Management

### GitRepository

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m                    # How often to check for updates
  url: https://github.com/org/my-app.git
  ref:
    branch: main                  # or tag: v1.0.0, semver: ">=1.0.0"

  # For private repos
  secretRef:
    name: git-credentials

  # Ignore certain paths
  ignore: |
    # Exclude all
    /*
    # Include only deploy folder
    !/deploy
---
# Secret for private repos
apiVersion: v1
kind: Secret
metadata:
  name: git-credentials
  namespace: flux-system
type: Opaque
data:
  username: <base64>
  password: <base64>  # Or use SSH key with 'identity' field
```

### HelmRepository

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 1h
  url: https://charts.bitnami.com/bitnami
---
# OCI Registry (Helm 3.8+)
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: podinfo
  namespace: flux-system
spec:
  interval: 1h
  url: oci://ghcr.io/stefanprodan/charts
  type: oci
```

### OCIRepository

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: manifests
  namespace: flux-system
spec:
  interval: 5m
  url: oci://ghcr.io/org/manifests
  ref:
    tag: latest

  # For private registries
  secretRef:
    name: oci-credentials
```

## Kustomization

### Basic Kustomization

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 10m
  retryInterval: 2m

  sourceRef:
    kind: GitRepository
    name: my-app

  path: ./deploy/overlays/production

  prune: true                     # Delete removed resources
  wait: true                      # Wait for resources to be ready

  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: my-app
      namespace: production

  # Substitute variables
  postBuild:
    substitute:
      ENVIRONMENT: production
      CLUSTER_NAME: prod-us-east
    substituteFrom:
      - kind: ConfigMap
        name: cluster-config
      - kind: Secret
        name: cluster-secrets
```

### Kustomization Dependencies

```yaml
# Install cert-manager first
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cert-manager
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: infrastructure
  path: ./cert-manager
---
# Then install ingress (depends on cert-manager)
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: ingress
  namespace: flux-system
spec:
  interval: 10m
  dependsOn:
    - name: cert-manager        # Wait for cert-manager
  sourceRef:
    kind: GitRepository
    name: infrastructure
  path: ./ingress
---
# Then install apps (depends on ingress)
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: apps
  namespace: flux-system
spec:
  interval: 10m
  dependsOn:
    - name: ingress             # Wait for ingress
  sourceRef:
    kind: GitRepository
    name: apps
  path: ./production
```

## HelmRelease

### Basic HelmRelease

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: nginx
  namespace: web
spec:
  interval: 10m
  chart:
    spec:
      chart: nginx
      version: "15.x"           # Semver range
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system
      interval: 1h

  values:
    replicaCount: 3
    service:
      type: ClusterIP

  # Or from ConfigMap/Secret
  valuesFrom:
    - kind: ConfigMap
      name: nginx-values
      valuesKey: values.yaml
```

### HelmRelease with Dependencies

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: wordpress
  namespace: blog
spec:
  interval: 10m
  dependsOn:
    - name: mysql               # Wait for MySQL to be ready
      namespace: database
  chart:
    spec:
      chart: wordpress
      version: "18.x"
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system

  values:
    externalDatabase:
      host: mysql.database.svc.cluster.local
      database: wordpress
    mariadb:
      enabled: false
```

### HelmRelease from Git

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: my-app
  namespace: production
spec:
  interval: 10m
  chart:
    spec:
      chart: ./charts/my-app    # Path to chart in repo
      sourceRef:
        kind: GitRepository
        name: my-app
        namespace: flux-system
```

## Image Automation

### Automated Image Updates

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGE AUTOMATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CI builds and pushes new image                              │
│     ┌─────────┐      ┌─────────────────┐                        │
│     │   CI    │─────▶│ Container       │                        │
│     │  Build  │      │ Registry        │                        │
│     └─────────┘      │ myapp:v1.2.3    │                        │
│                      └────────┬────────┘                        │
│                               │                                  │
│  2. Image Reflector scans     │                                  │
│     ┌─────────────────────────▼──────────────────────────┐      │
│     │              ImageRepository                        │      │
│     │  Scans registry every 1m                           │      │
│     │  Finds new tag: v1.2.3                             │      │
│     └─────────────────────────┬──────────────────────────┘      │
│                               │                                  │
│  3. Image Policy selects      │                                  │
│     ┌─────────────────────────▼──────────────────────────┐      │
│     │              ImagePolicy                            │      │
│     │  Policy: semver, filter: ^v1\.2\.x                 │      │
│     │  Selected: v1.2.3                                  │      │
│     └─────────────────────────┬──────────────────────────┘      │
│                               │                                  │
│  4. Image Automation updates  │                                  │
│     ┌─────────────────────────▼──────────────────────────┐      │
│     │          ImageUpdateAutomation                      │      │
│     │  Updates deployment.yaml in Git                    │      │
│     │  Commits: "Update myapp to v1.2.3"                 │      │
│     └─────────────────────────┬──────────────────────────┘      │
│                               │                                  │
│  5. Flux syncs change         │                                  │
│     ┌─────────────────────────▼──────────────────────────┐      │
│     │              Kustomization                          │      │
│     │  Detects Git change, applies new manifest          │      │
│     └──────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration

```yaml
# 1. ImageRepository - Scans container registry
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  image: ghcr.io/org/my-app
  interval: 1m
  secretRef:
    name: registry-credentials
---
# 2. ImagePolicy - Selects which tags to use
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: my-app
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: my-app
  policy:
    semver:
      range: ">=1.0.0"    # Use any 1.x.x or higher
---
# Or use alphabetical for date-based tags
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: my-app-dev
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: my-app
  policy:
    alphabetical:
      order: desc         # Latest date first
  filterTags:
    pattern: '^main-[a-f0-9]+-(?P<ts>.*)'
    extract: '$ts'
---
# 3. ImageUpdateAutomation - Commits updates
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 30m
  sourceRef:
    kind: GitRepository
    name: fleet-infra

  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        name: fluxcdbot
        email: flux@example.com
      messageTemplate: |
        Update image to {{range .Updated.Images}}{{println .}}{{end}}
    push:
      branch: main

  update:
    path: ./clusters/production
    strategy: Setters
```

### Marking Images for Update

```yaml
# In your deployment.yaml, add markers
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          image: ghcr.io/org/my-app:v1.0.0  # {"$imagepolicy": "flux-system:my-app"}
```

## Notifications

### Slack Notifications

```yaml
# Provider - Where to send
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: slack
  namespace: flux-system
spec:
  type: slack
  channel: gitops-alerts
  secretRef:
    name: slack-webhook
---
apiVersion: v1
kind: Secret
metadata:
  name: slack-webhook
  namespace: flux-system
data:
  address: <base64-encoded-webhook-url>
---
# Alert - What to send
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: all-alerts
  namespace: flux-system
spec:
  providerRef:
    name: slack
  eventSeverity: info
  eventSources:
    - kind: GitRepository
      name: "*"
    - kind: Kustomization
      name: "*"
    - kind: HelmRelease
      name: "*"
```

### GitHub Commit Status

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: github
  namespace: flux-system
spec:
  type: github
  address: https://github.com/org/repo
  secretRef:
    name: github-token
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: sync-status
  namespace: flux-system
spec:
  providerRef:
    name: github
  eventSources:
    - kind: Kustomization
      name: apps
```

## Multi-Cluster Management

### Repository Structure

```
fleet-infra/
├── clusters/
│   ├── production/
│   │   ├── flux-system/
│   │   │   └── gotk-sync.yaml
│   │   └── apps.yaml          # Points to apps/production
│   ├── staging/
│   │   ├── flux-system/
│   │   │   └── gotk-sync.yaml
│   │   └── apps.yaml          # Points to apps/staging
│   └── dev/
│       └── ...
├── infrastructure/
│   ├── base/                  # Shared infra (cert-manager, ingress)
│   ├── production/            # Prod-specific configs
│   └── staging/
└── apps/
    ├── base/                  # App definitions
    ├── production/            # Prod overlays
    └── staging/               # Staging overlays
```

### Cluster Kustomization

```yaml
# clusters/production/apps.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: apps
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: flux-system
  path: ./apps/production
  prune: true

  # Cluster-specific substitutions
  postBuild:
    substitute:
      CLUSTER_NAME: prod-us-east
      ENVIRONMENT: production
```

## Flux vs ArgoCD

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUX vs ARGOCD                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FLUX                              ARGOCD                        │
│  ────                              ──────                        │
│                                                                  │
│  Architecture:                     Architecture:                 │
│  • Toolkit of controllers          • Monolithic application     │
│  • CLI-driven                       • Web UI-driven              │
│  • GitOps-native only               • GitOps + traditional       │
│                                                                  │
│  Strengths:                        Strengths:                    │
│  • Simpler to extend               • Beautiful UI                │
│  • Image automation built-in       • Easier onboarding           │
│  • OCI artifacts native            • Rich RBAC/SSO               │
│  • Lower resource usage            • Diff visualization          │
│                                                                  │
│  Best for:                         Best for:                     │
│  • Platform teams                  • Application teams           │
│  • Automation-first                • UI-first                    │
│  • Multi-cluster at scale          • Developer self-service      │
│                                                                  │
│  Philosophy:                       Philosophy:                   │
│  "Everything is a CR"              "Applications are first-class"│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

RECOMMENDATION:
• Small team, wants UI → ArgoCD
• Platform team, automation-heavy → Flux
• Both work great, pick one and master it
```

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| No dependencies | Resources apply in random order | Use `dependsOn` for order |
| Missing healthChecks | Flux doesn't wait for readiness | Add deployment health checks |
| Hardcoded values | Can't reuse across environments | Use `postBuild.substitute` |
| No prune | Orphaned resources accumulate | Enable `prune: true` |
| Long intervals | Slow to detect changes | 1m for git, 10m for apps |
| No notifications | Silent failures | Set up Slack/Teams alerts |

## War Story: The $2.1 Million Substitution Surprise

A fintech company managing 8 clusters across 3 regions used Flux's `postBuild.substitute` to inject environment-specific values. Their setup worked flawlessly for 18 months—until it didn't.

They had a core deployment template with:

```yaml
replicas: ${REPLICAS}
resources:
  limits:
    memory: ${MEMORY_LIMIT}
    cpu: ${CPU_LIMIT}
```

In production, all variables were defined in a ConfigMap: `REPLICAS=5`, `MEMORY_LIMIT=2Gi`, `CPU_LIMIT=1000m`. But when they added a new cluster in Asia-Pacific, a junior engineer copied the cluster bootstrap but forgot to copy the ConfigMap.

The substitutions kept the literal strings. Kubernetes rejected `replicas: ${REPLICAS}` as an invalid integer—but **only for new deployments**. Existing deployments kept running, masking the problem. The Kustomization showed `Applied successfully` because the YAML was syntactically valid.

```
THE INCIDENT TIMELINE
─────────────────────────────────────────────────────────────────
Day 1, 09:00 AM   New APAC cluster bootstrapped with Flux
Day 1, 09:15 AM   Kustomization reports "Ready" (no health checks configured)
Day 1-14          Cluster appears healthy, no new deployments
Day 15, 03:00 AM  Scheduled maintenance deploys new version across all clusters
Day 15, 03:05 AM  APAC deployment fails: "replicas: ${REPLICAS} is not valid"
Day 15, 03:05 AM  APAC cluster has zero running pods (old pods terminated)
Day 15, 03:06 AM  PagerDuty alerts: APAC region completely down
Day 15, 03:45 AM  Root cause identified: missing ConfigMap
Day 15, 04:15 AM  ConfigMap applied, services restored
Day 15, 04:15 AM  70 minutes of complete APAC downtime
```

**Financial Impact:**

```
INCIDENT COST BREAKDOWN
─────────────────────────────────────────────────────────────────
APAC revenue during outage (70 min):     $1,450,000
  × 100% traffic loss                    = $1,450,000 lost revenue

SLA violation penalties:
  - Enterprise customers (12)            = $180,000
  - Contractual credits                  = $95,000

War room costs:
  - 8 engineers × 4 hours × $150/hr      = $4,800
  - Executive escalation                 = $25,000

Regulatory review (financial services):  = $150,000
Post-incident audit:                     = $75,000

Customer churn (attributed):             = $125,000

TOTAL COST: $2,104,800
─────────────────────────────────────────────────────────────────
```

**The Fix—Defense in Depth:**

```yaml
# 1. Make ConfigMap mandatory
postBuild:
  substituteFrom:
    - kind: ConfigMap
      name: cluster-config
      optional: false  # ← Fail if missing

# 2. Add health checks to catch silent failures
healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
    namespace: production
  - apiVersion: apps/v1
    kind: Deployment
    name: payment-service
    namespace: production

# 3. Add timeout to prevent indefinite waiting
timeout: 5m
```

**Additional Safeguards Added:**

```yaml
# Pre-bootstrap validation script
#!/bin/bash
REQUIRED_CMS="cluster-config cluster-secrets"
for cm in $REQUIRED_CMS; do
  if ! kubectl get configmap $cm -n flux-system &>/dev/null; then
    echo "ERROR: Missing required ConfigMap: $cm"
    exit 1
  fi
done

# Notification on Kustomization failure
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: reconciliation-failures
spec:
  providerRef:
    name: pagerduty
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      name: "*"
```

**Lessons Learned:**

1. **Never trust "Applied successfully"**—it only means YAML was valid, not that apps are healthy
2. **Always use `optional: false`** for required substitutions
3. **Always add healthChecks**—they're the only way to know if deployments actually work
4. **Validate new clusters** before production traffic with a checklist
5. **Alert on Kustomization failures**, not just successes

## Quiz

### Question 1
What's the main architectural difference between Flux and ArgoCD?

<details>
<summary>Show Answer</summary>

**Flux**: A toolkit of independent controllers (source-controller, kustomize-controller, helm-controller, etc.). Each controller manages specific CRDs and can be installed independently. Configuration is entirely through Kubernetes resources.

**ArgoCD**: A monolithic application with a web UI, API server, and backend. It's installed as a single unit and has its own Application CRD. Configuration can be through UI, CLI, or CRDs.

Flux is more composable and automation-friendly. ArgoCD is more user-friendly with better visualization. Both achieve the same GitOps outcomes.
</details>

### Question 2
How does Flux's image automation work?

<details>
<summary>Show Answer</summary>

Three components work together:

1. **ImageRepository**: Scans a container registry at intervals, finds all available tags

2. **ImagePolicy**: Selects which tag to use based on policy (semver, alphabetical, numerical)

3. **ImageUpdateAutomation**: Updates YAML files in Git with the selected tag and commits the change

The automation requires markers in your YAML:
```yaml
image: myapp:v1.0.0  # {"$imagepolicy": "flux-system:my-app"}
```

This closes the GitOps loop: CI pushes image → Flux updates Git → Flux applies from Git.
</details>

### Question 3
You have three Kustomizations: cert-manager, ingress, and apps. Apps depends on ingress, ingress depends on cert-manager. How would you configure this?

<details>
<summary>Show Answer</summary>

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cert-manager
spec:
  # No dependencies, runs first
  path: ./cert-manager
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: ingress
spec:
  dependsOn:
    - name: cert-manager
  path: ./ingress
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: apps
spec:
  dependsOn:
    - name: ingress
  path: ./apps
```

Flux will:
1. Apply cert-manager and wait for it to be healthy
2. Then apply ingress and wait for it to be healthy
3. Then apply apps
</details>

### Question 4
Your Flux reconciliation is failing. What commands would you use to debug?

<details>
<summary>Show Answer</summary>

```bash
# Check overall Flux health
flux check

# See all Flux resources and their status
flux get all

# Specific resource status
flux get sources git
flux get kustomizations
flux get helmreleases

# Detailed info on a failing resource
flux get kustomization my-app -o wide

# View events and conditions
kubectl describe kustomization my-app -n flux-system

# View controller logs
flux logs --kind=Kustomization --name=my-app

# Force immediate reconciliation
flux reconcile kustomization my-app --with-source

# Suspend to stop reconciliation during debugging
flux suspend kustomization my-app
flux resume kustomization my-app
```
</details>

### Question 5
Your organization needs to deploy the same application to 15 clusters with minor variations (different domains, replica counts). Compare how you'd approach this in Flux vs ArgoCD.

<details>
<summary>Show Answer</summary>

**Flux Approach:**

```yaml
# Base Kustomization with substitutions
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: apps
  path: ./my-app/base
  prune: true

  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-config  # Each cluster has its own
```

Each cluster's `cluster-config`:
```yaml
# clusters/prod-us-east-1/cluster-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-config
data:
  CLUSTER_NAME: prod-us-east-1
  DOMAIN: us-east.example.com
  REPLICAS: "5"
```

**ArgoCD Approach:**

```yaml
# ApplicationSet with cluster generator
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            env: production
  template:
    spec:
      source:
        helm:
          parameters:
            - name: domain
              value: "{{metadata.labels.domain}}"
            - name: replicas
              value: "{{metadata.labels.replicas}}"
```

**Comparison:**

| Aspect | Flux | ArgoCD |
|--------|------|--------|
| Config location | ConfigMaps per cluster | Cluster labels or Git files |
| Scaling | Add ConfigMap to new cluster | Register cluster with labels |
| Visibility | `flux get kustomizations` | UI shows all ApplicationSet instances |
| Flexibility | Full Kustomize power | Generator types (cluster, git, list) |

**Recommendation for 15 clusters:**
- Flux: Better if clusters have complex, unique configurations
- ArgoCD: Better if variations are simple and you want UI visibility
</details>

### Question 6
You're implementing image automation for a development environment. You want to auto-deploy any image tagged with the git commit SHA from the `develop` branch. Write the ImageRepository, ImagePolicy, and ImageUpdateAutomation configuration.

<details>
<summary>Show Answer</summary>

```yaml
# 1. ImageRepository - Scan the registry
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: my-app-dev
  namespace: flux-system
spec:
  image: ghcr.io/myorg/my-app
  interval: 1m
  secretRef:
    name: ghcr-credentials
---
# 2. ImagePolicy - Select develop branch builds
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: my-app-dev
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: my-app-dev

  # Match tags like: develop-abc123f-1702234567
  filterTags:
    pattern: '^develop-[a-f0-9]+-(?P<ts>[0-9]+)$'
    extract: '$ts'

  policy:
    numerical:
      order: asc  # Highest timestamp wins
---
# 3. ImageUpdateAutomation - Update Git
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: my-app-dev
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: fleet-infra

  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        name: flux-bot
        email: flux@example.com
      messageTemplate: |
        [dev] Auto-update {{ .AutomationObject }}

        Images:
        {{ range .Updated.Images }}
        - {{ . }}
        {{ end }}
    push:
      branch: main

  update:
    path: ./clusters/development
    strategy: Setters
```

**In your deployment YAML, add the marker:**

```yaml
spec:
  containers:
    - name: app
      image: ghcr.io/myorg/my-app:develop-abc123f-1702234567 # {"$imagepolicy": "flux-system:my-app-dev"}
```

**Tag pattern explained:**
- `develop` - branch name prefix
- `[a-f0-9]+` - git commit SHA
- `(?P<ts>[0-9]+)` - named capture group for timestamp
- Numerical policy sorts by extracted timestamp, picking latest
</details>

### Question 7
Calculate the resource requirements for Flux controllers managing 50 GitRepositories (checked every 1m), 100 Kustomizations, and 75 HelmReleases. What's the expected API server load?

<details>
<summary>Show Answer</summary>

**Controller Resource Estimation:**

```
FLUX CONTROLLER RESOURCE REQUIREMENTS
─────────────────────────────────────────────────────────────────
BASE REQUIREMENTS (minimal installation):
source-controller:     128Mi memory, 100m CPU
kustomize-controller:  256Mi memory, 100m CPU
helm-controller:       256Mi memory, 100m CPU
notification-controller: 64Mi memory, 50m CPU
                       ─────────────────────────
Base total:            704Mi memory, 350m CPU

SCALING FACTORS:
─────────────────────────────────────────────────────────────────
GitRepositories (50 × 1m interval):
  - Each git fetch: ~5MB memory spike during clone
  - Concurrent fetches: 2 (default)
  - Memory buffer: 50 × 2MB = 100Mi
  - Add: +128Mi to source-controller

Kustomizations (100):
  - Each reconcile: ~10MB for manifest processing
  - Concurrent reconciles: 4 (default)
  - Memory buffer: 4 × 10MB = 40Mi
  - Add: +256Mi to kustomize-controller

HelmReleases (75):
  - Each release: ~20MB for chart rendering
  - Concurrent releases: 2 (default)
  - Memory buffer: 2 × 20MB = 40Mi
  - Add: +256Mi to helm-controller

RECOMMENDED PRODUCTION LIMITS:
─────────────────────────────────────────────────────────────────
source-controller:     512Mi memory, 500m CPU
kustomize-controller:  768Mi memory, 500m CPU
helm-controller:       768Mi memory, 500m CPU
notification-controller: 128Mi memory, 100m CPU
                       ─────────────────────────
Total:                 2176Mi memory, 1600m CPU
```

**API Server Load Calculation:**

```
API SERVER CALLS PER MINUTE
─────────────────────────────────────────────────────────────────
Source reconciliation:
  50 GitRepositories × 1/min × 3 API calls = 150 calls/min
  (status update, event, artifact update)

Kustomization reconciliation:
  100 Kustomizations × 1/10min × 15 API calls = 150 calls/min
  (get manifests, apply each resource, status)

HelmRelease reconciliation:
  75 HelmReleases × 1/10min × 10 API calls = 75 calls/min
  (get chart, render, apply, status)

Informer watches (constant):
  ~20 watches × heartbeat = minimal

TOTAL: ~375 API calls/minute (~6 calls/second)
─────────────────────────────────────────────────────────────────

This is VERY LOW for a Kubernetes API server.
Typical API servers handle 1000+ calls/second easily.
```

**Optimization Tips:**

```yaml
# If API server load becomes concern:
spec:
  interval: 5m      # Increase from 1m (reduces load 5x)
  retryInterval: 1m # Keep retry fast for failures

# Reduce concurrent operations:
# In controller deployment args:
--concurrent=2  # Default is 4 for kustomize-controller
```
</details>

### Question 8
Your Kustomization is stuck in "Not Ready" with the message "dependency 'flux-system/cert-manager' is not ready". The cert-manager Kustomization shows "Applied successfully". What's wrong and how do you fix it?

<details>
<summary>Show Answer</summary>

**The Problem:**

"Applied successfully" means manifests were sent to the API server, but it does NOT mean resources are healthy. The dependent Kustomization waits for the dependency to be **Ready**, not just **Applied**.

**Root Cause Investigation:**

```bash
# Check cert-manager Kustomization status
flux get kustomization cert-manager -o wide

# Look for the actual status
kubectl get kustomization cert-manager -n flux-system -o yaml

# Common findings:
# - Status shows "Applied" but conditions show issues
# - Health checks are failing
# - Resources created but pods not running
```

**Common Causes:**

1. **No health checks defined** (most common):
```yaml
# BAD: No health checks, "Ready" based only on apply success
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cert-manager
spec:
  # ... no healthChecks
```

2. **Pods failing to start**:
```bash
# cert-manager pods might be CrashLooping
kubectl get pods -n cert-manager
kubectl logs -n cert-manager -l app=cert-manager
```

3. **CRDs not yet available**:
```bash
# cert-manager CRDs might not be registered yet
kubectl get crds | grep cert-manager
```

**The Fix:**

```yaml
# Add health checks to cert-manager Kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cert-manager
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: infrastructure
  path: ./cert-manager
  prune: true
  wait: true  # ← Wait for resources to be ready

  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: cert-manager
      namespace: cert-manager
    - apiVersion: apps/v1
      kind: Deployment
      name: cert-manager-cainjector
      namespace: cert-manager
    - apiVersion: apps/v1
      kind: Deployment
      name: cert-manager-webhook
      namespace: cert-manager

  timeout: 5m  # Fail if not healthy within 5 minutes
```

**Debugging Commands:**

```bash
# Force reconciliation with source refresh
flux reconcile kustomization cert-manager --with-source

# Watch the reconciliation progress
flux get kustomization cert-manager --watch

# Check what's blocking
kubectl describe kustomization cert-manager -n flux-system | grep -A 20 "Conditions"

# If cert-manager pods are the issue
kubectl get events -n cert-manager --sort-by='.lastTimestamp'
```

**Key Insight:** Always add `healthChecks` for any Kustomization that other resources depend on. Without them, Flux considers a Kustomization "Ready" as soon as `kubectl apply` succeeds, even if the actual pods never start.
</details>

## Hands-On Exercise

### Scenario: GitOps with Flux

Bootstrap Flux and deploy an application with image automation.

### Setup

```bash
# Create kind cluster
kind create cluster --name flux-lab

# Check Flux prerequisites
flux check --pre

# Since we don't have a real Git repo, we'll use local manifests
# Install Flux controllers only
flux install
```

### Deploy Application Manually (Simulated GitOps)

```bash
# Create a GitRepository pointing to a public repo
flux create source git podinfo \
  --url=https://github.com/stefanprodan/podinfo \
  --branch=master \
  --interval=1m \
  --export > podinfo-source.yaml

kubectl apply -f podinfo-source.yaml

# Create Kustomization to deploy podinfo
flux create kustomization podinfo \
  --source=GitRepository/podinfo \
  --path="./kustomize" \
  --prune=true \
  --interval=10m \
  --export > podinfo-kustomization.yaml

kubectl apply -f podinfo-kustomization.yaml
```

### Verify Deployment

```bash
# Check Flux resources
flux get sources git
flux get kustomizations

# Check deployed pods
kubectl get pods -A | grep podinfo

# Watch reconciliation
flux get kustomizations --watch
```

### Deploy a HelmRelease

```bash
# Add Bitnami repository
flux create source helm bitnami \
  --url=https://charts.bitnami.com/bitnami \
  --interval=1h \
  --export > bitnami-source.yaml

kubectl apply -f bitnami-source.yaml

# Deploy NGINX via Helm
cat <<EOF | kubectl apply -f -
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: nginx
  namespace: default
spec:
  interval: 10m
  chart:
    spec:
      chart: nginx
      version: "15.x"
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system
  values:
    replicaCount: 2
    service:
      type: ClusterIP
EOF

# Check HelmRelease status
flux get helmreleases
```

### Suspend and Resume

```bash
# Suspend reconciliation
flux suspend kustomization podinfo

# Make a change (it won't be reverted)
kubectl scale deployment podinfo --replicas=5

# Resume reconciliation (change will be reverted)
flux resume kustomization podinfo

# Verify pods went back to original count
kubectl get pods | grep podinfo
```

### Success Criteria

- [ ] Flux controllers are running
- [ ] GitRepository source is synced
- [ ] Kustomization applies manifests
- [ ] HelmRelease deploys chart
- [ ] Understand suspend/resume behavior

### Cleanup

```bash
kind delete cluster --name flux-lab
rm -f podinfo-*.yaml bitnami-source.yaml
```

## Key Takeaways

Before moving on, ensure you can:

- [ ] Explain Flux's toolkit architecture (source, kustomize, helm, notification controllers)
- [ ] Bootstrap Flux to a cluster with `flux bootstrap github/gitlab`
- [ ] Create GitRepository, HelmRepository, and OCIRepository sources
- [ ] Write Kustomizations with dependencies, health checks, and substitutions
- [ ] Configure HelmReleases with values from ConfigMaps and Secrets
- [ ] Set up image automation (ImageRepository, ImagePolicy, ImageUpdateAutomation)
- [ ] Configure Slack/Teams notifications for reconciliation events
- [ ] Debug failed reconciliations with `flux get`, `flux logs`, and `kubectl describe`
- [ ] Compare Flux vs ArgoCD trade-offs for different use cases
- [ ] Design multi-cluster GitOps with cluster-specific substitutions

## Next Module

Continue to [Module 2.4: Helm & Kustomize](../module-2.4-helm-kustomize/) where we'll dive deep into the package management tools that power GitOps.

---

*"GitOps is not a tool, it's a practice. Flux gives you the toolkit to practice it well."*

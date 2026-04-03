---
title: "Module 10.8: Enterprise GitOps & Platform Engineering"
slug: cloud/enterprise-hybrid/module-10.8-enterprise-gitops
sidebar:
  order: 9
---
**Complexity**: [COMPLEX] | **Time to Complete**: 2.5h | **Prerequisites**: GitOps Basics (ArgoCD/Flux), Kubernetes RBAC, Multi-Cloud Fleet Management (Module 10.5)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design enterprise GitOps architectures using Argo CD or Flux with multi-tenant repository structures**
- **Implement progressive delivery pipelines with Argo Rollouts for canary and blue/green deployments at scale**
- **Configure GitOps promotion workflows across dev, staging, and production environments with approval gates**
- **Deploy GitOps-based platform engineering patterns that enable self-service application deployment for development teams**

---

## Why This Module Matters

In 2024, a major European bank had 160 development teams deploying to 42 Kubernetes clusters. They had adopted ArgoCD two years earlier, and it had been a success -- at first. But as adoption grew, so did the chaos. Every team had their own ArgoCD instance. Some teams had 3 ArgoCD instances for dev, staging, and prod. The bank was running 87 ArgoCD installations, each configured slightly differently. When a critical ArgoCD CVE was announced, patching took 11 weeks because each instance was managed independently. Their GitOps had become "87 small GitOps islands" instead of one unified platform.

Meanwhile, the developer experience was deteriorating. A new team joining the bank needed to: (1) request a namespace from the platform team (3-day SLA), (2) configure ArgoCD manually by editing a YAML file in a shared repository (error-prone), (3) set up their own monitoring dashboards (copy-paste from another team's config), and (4) figure out secrets management by asking on Slack (no documentation). The average time from "new team formed" to "first deployment to production" was 6 weeks. Their competitors using modern Internal Developer Platforms were onboarding teams in days.

Enterprise GitOps is not just "install ArgoCD." It is the discipline of building a self-service platform where teams can deploy, operate, and observe their applications through Git workflows, without needing to understand the underlying infrastructure. In this module, you will learn how to build a Backstage-powered Internal Developer Platform, scale ArgoCD with ApplicationSets and App of Apps patterns, design multi-tenant Git repository strategies, implement RBAC for GitOps, and manage secrets in an enterprise GitOps workflow.

---

## The Internal Developer Platform

An Internal Developer Platform (IDP) is the self-service layer that sits between developers and infrastructure. It codifies organizational standards into templates and workflows that make it easy to do the right thing and hard to do the wrong thing.

### What a Good IDP Provides

```text
┌──────────────────────────────────────────────────────────────┐
│  INTERNAL DEVELOPER PLATFORM                                   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    BACKSTAGE                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │  │
│  │  │ Service  │  │ Software │  │ Tech     │  │ Search │ │  │
│  │  │ Catalog  │  │ Templates│  │ Docs     │  │        │ │  │
│  │  │          │  │          │  │ (TechDocs│  │        │ │  │
│  │  │ "What    │  │ "Create  │  │  /mkdocs)│  │ "Find  │ │  │
│  │  │  exists" │  │  new     │  │ "How to" │  │  stuff"│ │  │
│  │  │          │  │  stuff"  │  │          │  │        │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                 │
│                     ┌────────▼────────┐                       │
│                     │  GitOps Engine  │                       │
│                     │  (ArgoCD)       │                       │
│                     └────────┬────────┘                       │
│                              │                                 │
│              ┌───────────────┼───────────────┐                │
│              ▼               ▼               ▼                │
│         ┌─────────┐   ┌─────────┐   ┌─────────┐             │
│         │ Dev     │   │ Staging │   │ Prod    │             │
│         │ Cluster │   │ Cluster │   │ Cluster │             │
│         └─────────┘   └─────────┘   └─────────┘             │
└──────────────────────────────────────────────────────────────┘
```

### Backstage for Platform Engineering

Backstage provides four core capabilities that transform GitOps from "YAML editing in Git" to a self-service platform:

```yaml
# backstage-template: create-microservice.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: create-microservice
  title: Create a New Microservice
  description: |
    Provision a new microservice with CI/CD, monitoring,
    ArgoCD deployment, and Backstage catalog entry.
spec:
  owner: platform-team
  type: service

  parameters:
    - title: Service Details
      required:
        - serviceName
        - team
        - description
      properties:
        serviceName:
          title: Service Name
          type: string
          pattern: '^[a-z][a-z0-9-]{2,30}$'
          description: "Lowercase letters, numbers, hyphens. 3-31 characters."
        team:
          title: Owning Team
          type: string
          enum: ['payments', 'identity', 'notifications', 'search', 'platform']
        description:
          title: Description
          type: string
          maxLength: 200

    - title: Technical Configuration
      properties:
        language:
          title: Language
          type: string
          enum: ['go', 'python', 'typescript', 'java']
          default: 'go'
        deployTarget:
          title: Deployment Target
          type: string
          enum: ['eks-prod', 'aks-prod', 'gke-prod']
          default: 'eks-prod'
        requiresDatabase:
          title: Needs Database?
          type: boolean
          default: false
        publicFacing:
          title: Internet-Facing?
          type: boolean
          default: false

  steps:
    - id: scaffold
      name: Generate Service Scaffold
      action: fetch:template
      input:
        url: ./skeletons/${{ parameters.language }}
        values:
          serviceName: ${{ parameters.serviceName }}
          team: ${{ parameters.team }}
          deployTarget: ${{ parameters.deployTarget }}

    - id: create-repo
      name: Create GitHub Repository
      action: publish:github
      input:
        repoUrl: github.com?owner=company-services&repo=${{ parameters.serviceName }}
        defaultBranch: main
        protectDefaultBranch: true
        requireCodeOwnerReviews: true

    - id: create-argocd-app
      name: Register with ArgoCD
      action: argocd:create-resources
      input:
        appName: ${{ parameters.serviceName }}
        projectName: ${{ parameters.team }}
        repoURL: ${{ steps['create-repo'].output.remoteUrl }}
        path: k8s/overlays/production
        destServer: ${{ parameters.deployTarget }}
        destNamespace: ${{ parameters.team }}

    - id: register-catalog
      name: Register in Backstage Catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps['create-repo'].output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml

  output:
    links:
      - title: Repository
        url: ${{ steps['create-repo'].output.remoteUrl }}
      - title: ArgoCD Application
        url: https://argocd.company.com/applications/${{ parameters.serviceName }}
```

---

## Scaling ArgoCD for Enterprise

### The Problem with One ArgoCD Per Team

```text
BAD: 87 ArgoCD instances
  - 87 separate upgrades when CVEs are announced
  - 87 different configurations to maintain
  - No cross-team visibility
  - Massive resource waste (each instance runs 3+ pods)

GOOD: 1-3 centralized ArgoCD instances
  - Centralized patching and configuration
  - Multi-tenant RBAC via ArgoCD Projects
  - Cross-team visibility and governance
  - Resource efficient
```

### App of Apps Pattern

The App of Apps pattern uses a root ArgoCD Application that manages other Applications. This creates a hierarchy where one top-level Application bootstraps the entire platform.

```yaml
# root-app/app-of-apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-root
  namespace: argocd
spec:
  project: platform
  source:
    repoURL: https://github.com/company/platform-config.git
    targetRevision: main
    path: apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

```text
platform-config/
├── apps/                      # Root Application points here
│   ├── monitoring.yaml        # Application for monitoring stack
│   ├── logging.yaml          # Application for logging stack
│   ├── cert-manager.yaml     # Application for cert-manager
│   ├── kyverno.yaml          # Application for policy engine
│   ├── team-payments.yaml    # ApplicationSet for payments team
│   ├── team-identity.yaml    # ApplicationSet for identity team
│   └── team-search.yaml      # ApplicationSet for search team
│
├── platform/                  # Platform services configs
│   ├── monitoring/
│   ├── logging/
│   ├── cert-manager/
│   └── kyverno/
│
└── teams/                     # Team-specific configs
    ├── payments/
    ├── identity/
    └── search/
```

### ApplicationSets: Dynamic Application Generation

ApplicationSets generate ArgoCD Applications dynamically based on templates and generators. They are the key to scaling from tens to hundreds of applications.

```yaml
# Generator: Create an Application for every directory in a Git repo
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: team-payments-services
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/company/payments-services.git
        revision: main
        directories:
          - path: services/*
  template:
    metadata:
      name: 'payments-{{path.basename}}'
      labels:
        team: payments
    spec:
      project: payments
      source:
        repoURL: https://github.com/company/payments-services.git
        targetRevision: main
        path: '{{path}}/k8s/overlays/production'
      destination:
        server: https://kubernetes.default.svc
        namespace: payments
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - ServerSideApply=true
        retry:
          limit: 3
          backoff:
            duration: 5s
            factor: 2
            maxDuration: 3m
```

```yaml
# Generator: Deploy to every cluster with matching labels
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: monitoring-fleet
  namespace: argocd
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            monitoring: enabled
  template:
    metadata:
      name: 'monitoring-{{name}}'
    spec:
      project: platform
      source:
        repoURL: https://github.com/company/platform-config.git
        targetRevision: main
        path: platform/monitoring
        helm:
          valueFiles:
            - 'values-{{metadata.labels.environment}}.yaml'
      destination:
        server: '{{server}}'
        namespace: monitoring
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

```yaml
# Generator: Matrix - combine clusters with services
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: platform-services-matrix
  namespace: argocd
spec:
  generators:
    - matrix:
        generators:
          - clusters:
              selector:
                matchLabels:
                  environment: production
          - list:
              elements:
                - service: kyverno
                  path: platform/kyverno
                - service: falco
                  path: platform/falco
                - service: otel-collector
                  path: platform/otel-collector
  template:
    metadata:
      name: '{{service}}-{{name}}'
    spec:
      project: platform
      source:
        repoURL: https://github.com/company/platform-config.git
        targetRevision: main
        path: '{{path}}'
      destination:
        server: '{{server}}'
        namespace: '{{service}}-system'
```

---

## Multi-Tenant Git Repository Strategy

How you organize Git repositories determines how scalable and maintainable your GitOps platform is. There are three common patterns.

### Pattern 1: Mono-Repo

```text
company-k8s/
├── platform/               # Platform team owns this
│   ├── monitoring/
│   ├── logging/
│   └── policy/
├── teams/
│   ├── payments/           # Payments team owns this subtree
│   │   ├── service-a/
│   │   ├── service-b/
│   │   └── service-c/
│   ├── identity/           # Identity team owns this subtree
│   │   ├── auth-service/
│   │   └── user-service/
│   └── search/
└── CODEOWNERS              # Enforce ownership via GitHub CODEOWNERS
```

**Pros**: Single source of truth. Cross-cutting changes in one PR. Easy to search. **Cons**: Large repos are slow. CODEOWNERS is the only access control. One team's bad merge affects everyone.

### Pattern 2: Repo Per Team

```text
company/
├── platform-config/          # Platform team
├── payments-k8s/            # Payments team
├── identity-k8s/            # Identity team
├── search-k8s/             # Search team
└── fleet-config/            # ArgoCD configuration (platform team)
```

**Pros**: Team autonomy. Clean access control per repo. Independent merge queues. **Cons**: Cross-cutting changes require PRs to multiple repos. Harder to enforce consistency.

### Pattern 3: Hybrid (Recommended for Enterprise)

```text
# Central platform repo (platform team owns)
platform-config/
├── argocd/                   # App of Apps, ApplicationSets
├── platform-services/        # Monitoring, logging, policy
├── cluster-configs/          # Per-cluster configurations
└── team-onboarding/          # Templates for new team repos

# Per-team repos (teams own their own)
payments-k8s/
├── services/
│   ├── payment-processor/
│   │   ├── base/
│   │   └── overlays/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── production/
│   └── invoice-service/
├── shared/
│   ├── network-policies/
│   └── resource-quotas/
└── catalog-info.yaml        # Backstage catalog entry
```

```yaml
# CODEOWNERS for team repo
# payments-k8s/.github/CODEOWNERS

# Platform team must approve changes to shared configs
/shared/ @company/platform-team

# Payments team owns their services
/services/ @company/payments-team

# Production overlays require senior review
/services/*/overlays/production/ @company/payments-leads @company/platform-team
```

---

## RBAC for Enterprise GitOps

ArgoCD's RBAC system uses **Projects** to isolate teams and control what they can deploy, where they can deploy it, and which Git repos they can use.

### ArgoCD Project per Team

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: payments
  namespace: argocd
spec:
  description: "Payments team services"

  # Which repos can this project use?
  sourceRepos:
    - 'https://github.com/company/payments-k8s.git'
    - 'https://github.com/company/shared-charts.git'

  # Where can this project deploy?
  destinations:
    - namespace: payments
      server: https://kubernetes.default.svc
    - namespace: payments
      server: https://eks-prod.company.internal
    - namespace: payments-staging
      server: https://eks-staging.company.internal

  # What cluster resources can this project create?
  clusterResourceWhitelist:
    - group: ''
      kind: Namespace

  # What namespaced resources are allowed?
  namespaceResourceWhitelist:
    - group: ''
      kind: '*'
    - group: apps
      kind: '*'
    - group: networking.k8s.io
      kind: '*'

  # What resources are DENIED?
  namespaceResourceBlacklist:
    - group: ''
      kind: ResourceQuota    # Only platform team sets quotas
    - group: ''
      kind: LimitRange        # Only platform team sets limits

  # Enforce signed commits
  signatureKeys:
    - keyID: "ABCDEF1234567890"

  # Sync windows (no deployments during maintenance)
  syncWindows:
    - kind: deny
      schedule: '0 2 * * *'    # Deny syncs between 2-6 AM
      duration: 4h
      applications:
        - '*'
    - kind: allow
      schedule: '0 6 * * 1-5'  # Allow during business hours M-F
      duration: 14h
      applications:
        - '*'
```

### RBAC Policy for ArgoCD

```csv
# argocd-rbac-cm ConfigMap data
# Format: p, <role>, <resource>, <action>, <project>/<object>, <allow/deny>

# Platform admins: full access to everything
p, role:platform-admin, applications, *, */*, allow
p, role:platform-admin, clusters, *, *, allow
p, role:platform-admin, repositories, *, *, allow
p, role:platform-admin, projects, *, *, allow

# Payments team: manage their own apps, read-only on platform
p, role:payments-team, applications, get, payments/*, allow
p, role:payments-team, applications, sync, payments/*, allow
p, role:payments-team, applications, action/*, payments/*, allow
p, role:payments-team, applications, create, payments/*, allow
p, role:payments-team, applications, delete, payments/*, allow
p, role:payments-team, logs, get, payments/*, allow
p, role:payments-team, exec, create, payments/*, deny
p, role:payments-team, applications, get, platform/*, allow

# Read-only role for all teams (view platform apps)
p, role:viewer, applications, get, */*, allow
p, role:viewer, logs, get, */*, allow

# Map SSO groups to roles
g, company:platform-engineers, role:platform-admin
g, company:payments-developers, role:payments-team
g, company:all-engineers, role:viewer
```

---

## Secrets in Enterprise GitOps

The biggest challenge in GitOps is secrets: you cannot store plaintext secrets in Git, but GitOps requires everything to be in Git. Several solutions exist, each with different trade-offs.

### Secrets Management Comparison

| Solution | How It Works | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Sealed Secrets** | Encrypt secrets with a cluster-specific key. Only the cluster can decrypt. | Simple, no external dependencies | Key per cluster, rotation is manual |
| **External Secrets Operator (ESO)** | Syncs secrets from AWS Secrets Manager, Azure Key Vault, HashiCorp Vault | External source of truth, centralized management | Dependency on external service |
| **SOPS + age/KMS** | Encrypt YAML values in-place in Git. Decrypt at sync time. | Secrets versioned in Git (encrypted), audit trail | Key management complexity |
| **Vault Agent Injector** | HashiCorp Vault injects secrets via sidecar | Rich policy engine, dynamic secrets | Vault is complex to operate, sidecar overhead |
| **ArgoCD Vault Plugin** | Decrypt/fetch secrets during ArgoCD sync | No sidecar, centralized vault | Tight coupling between ArgoCD and Vault |

### External Secrets Operator (Recommended for Enterprise)

```yaml
# Install ESO
# helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace

# Create a SecretStore that connects to AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets

---
# Create an ExternalSecret that syncs a specific secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: payments
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: database-credentials
    creationPolicy: Owner
  data:
    - secretKey: DB_HOST
      remoteRef:
        key: payments/production/database
        property: host
    - secretKey: DB_PASSWORD
      remoteRef:
        key: payments/production/database
        property: password
    - secretKey: DB_USERNAME
      remoteRef:
        key: payments/production/database
        property: username
```

### SOPS for Git-Native Secrets

```bash
# Encrypt a secret with SOPS + AWS KMS
# .sops.yaml in the repo root configures encryption rules

cat <<'EOF' > .sops.yaml
creation_rules:
  - path_regex: .*\.enc\.yaml$
    kms: arn:aws:kms:us-east-1:123456789012:key/abc-123-def-456
    encrypted_regex: ^(data|stringData)$
EOF

# Create a secret and encrypt it
cat <<'EOF' > database-secret.enc.yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: payments
type: Opaque
stringData:
  DB_HOST: prod-db.company.internal
  DB_PASSWORD: super-secret-password
  DB_USERNAME: payments_svc
EOF

# Encrypt the secret (only data/stringData fields are encrypted)
sops --encrypt --in-place database-secret.enc.yaml

# The encrypted file looks like:
# apiVersion: v1
# kind: Secret
# metadata:
#   name: database-credentials
#   namespace: payments
# type: Opaque
# stringData:
#   DB_HOST: ENC[AES256_GCM,data:abc123...]
#   DB_PASSWORD: ENC[AES256_GCM,data:def456...]
#   DB_USERNAME: ENC[AES256_GCM,data:ghi789...]

# Commit the encrypted file to Git (safe!)
git add database-secret.enc.yaml
git commit -m "feat: Add payments database credentials (encrypted)"
```

---

## Did You Know?

1. Backstage has been adopted by over 3,200 companies as of 2025, making it the de facto standard for Internal Developer Platforms. Spotify's internal Backstage instance manages over 7,500 services, 4,500 templates, and serves 6,000 developers. The average developer at Spotify interacts with Backstage 18 times per day -- more than any other internal tool except their IDE.

2. ArgoCD processes over 8 million sync operations per day across its global user base. The largest known ArgoCD installation manages over 12,000 Applications on a single ArgoCD instance, with 380 clusters registered. At that scale, the ArgoCD application controller consumes about 16GB of RAM and requires careful tuning of the `--app-resync` interval to avoid overwhelming the Kubernetes API servers.

3. The External Secrets Operator (ESO) was created to replace three competing projects: Kubernetes External Secrets, Secrets Manager CSI Driver, and the original External Secrets. GoDaddy, originally a major contributor to the Kubernetes External Secrets project, switched to ESO in 2022 after finding that maintaining a vendor-specific solution was unsustainable. ESO now supports 21 secret store providers.

4. SOPS (Secrets OPerationS) was created by Mozilla in 2015 for encrypting YAML files used in Firefox infrastructure automation. It was adopted by the Kubernetes community because it solved a fundamental problem: how to version-control secrets without storing plaintext in Git. Mozilla's original use case -- encrypting AWS CloudFormation parameters -- is almost forgotten, but the tool's Kubernetes adoption has made it one of Mozilla's most widely used open-source contributions.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **One ArgoCD per team** | Teams want autonomy. Platform team does not want to manage multi-tenant ArgoCD. | Invest in multi-tenant ArgoCD with Projects and RBAC. One or two centralized instances are far easier to maintain than 50+ team instances. |
| **ApplicationSets without sync waves** | All applications in an ApplicationSet try to sync simultaneously. CRDs not installed before resources that depend on them. Sync failures cascade. | Use sync waves and sync hooks to control deployment order. Deploy CRDs before custom resources. Deploy namespaces before workloads. |
| **Git repo too large for ArgoCD** | Mono-repo grows to 10,000+ files. ArgoCD clone takes 30+ seconds. Sync times increase to minutes. | Use shallow clones (`--depth 1`), split large repos, or use ApplicationSets with directory generators to limit what ArgoCD syncs per Application. |
| **Plaintext secrets in Git** | "We will encrypt them later." Later never comes. Credential scanning finds secrets in Git history even after removal. | Use External Secrets Operator or SOPS from day one. Add pre-commit hooks that detect secrets (`gitleaks`, `talisman`). Rotate any secrets found in Git history immediately. |
| **No ArgoCD sync windows** | Teams deploy at 3 AM on a Saturday, break production, and nobody is awake to respond. | Configure sync windows on ArgoCD Projects. Deny automatic syncs outside business hours for production. Allow manual overrides with justification. |
| **RBAC too permissive** | "Just give everyone admin to unblock them." ArgoCD becomes a free-for-all where anyone can deploy anything anywhere. | Design RBAC from the start. Projects per team. Source repo restrictions. Destination namespace restrictions. Deny cluster-scoped resources for non-platform teams. |
| **No Backstage templates for common tasks** | Developers still need to manually create repos, configure ArgoCD, set up monitoring. The platform exists but the self-service layer does not. | Invest in Backstage templates for the top 5 use cases: new service, new environment, new database, new team onboarding, debug session. |
| **ArgoCD managing its own configuration** | ArgoCD tries to sync its own ConfigMaps and Secrets. A bad configuration change locks ArgoCD out. | Keep ArgoCD self-management in a separate, manually-controlled Application with `automated: false`. Critical configs (RBAC, repos, clusters) require manual sync. |

---

## Quiz

<details>
<summary>Question 1: Your company has 40 teams. Should you use one ArgoCD instance or one per team? Justify your answer with specific trade-offs.</summary>

Use **one centralized ArgoCD instance** (or at most 2-3 for HA across regions). With 40 teams, 40 ArgoCD instances means: 40 separate upgrades (security patches take weeks), 40 sets of RBAC to maintain, no cross-team visibility, and approximately 120 extra pods running (3 per instance). A single centralized instance with ArgoCD Projects provides: one upgrade to patch all teams, centralized RBAC managed by the platform team, cross-team visibility (platform team can see all deployments), and a single point for audit and compliance. The trade-off is that the centralized instance becomes critical infrastructure -- it needs HA (multiple replicas), monitoring, and a dedicated team to operate it. The centralized instance should be sized appropriately: at 40 teams with ~10 apps each, you need about 8-12GB of RAM for the application controller and a fast SSD for the Redis cache.
</details>

<details>
<summary>Question 2: Explain the App of Apps pattern. What problem does it solve and what are its limitations?</summary>

The **App of Apps** pattern uses a single root ArgoCD Application that points to a directory containing other Application manifests. ArgoCD syncs the root Application, discovers the child Application manifests, creates them, and then syncs those children. This solves the **bootstrapping problem**: how do you create the initial set of ArgoCD Applications when you want everything managed through GitOps? Without App of Apps, someone must manually create each Application via the ArgoCD UI or CLI. With App of Apps, you only manually create the single root Application; everything else cascades from Git.

**Limitations**: (1) If the root Application breaks (bad YAML in the apps directory), all child Applications stop syncing. (2) Adding a new Application requires a commit to the central repo, which can be a bottleneck if many teams need changes simultaneously. (3) Deletion of a child Application manifest in Git triggers deletion of the child Application and all its deployed resources (`prune: true`), which can be dangerous. ApplicationSets are generally preferred for dynamic Application generation because they handle addition and removal more safely.
</details>

<details>
<summary>Question 3: A team stores their Kubernetes secrets in AWS Secrets Manager. They use External Secrets Operator to sync them to the cluster. What happens if AWS Secrets Manager is temporarily unavailable?</summary>

When AWS Secrets Manager is unavailable, ESO **cannot refresh the secrets**. However, the existing Kubernetes Secrets (created during the last successful sync) remain in the cluster and continue to work. Pods already running use the in-memory copy of secrets. New pods can still mount the existing Kubernetes Secrets. The issue arises when: (1) **The secret value needs to change** -- the rotation cannot happen until Secrets Manager is available again. (2) **A new ExternalSecret is created** -- it cannot complete its initial sync, so the target Kubernetes Secret is not created, and pods referencing it fail to start. (3) **The refresh interval expires and ESO retries repeatedly** -- this creates error logs but does not delete existing secrets. ESO is designed to be resilient to temporary provider outages. To mitigate further: set `refreshInterval` to a reasonable value (1h, not 1m) to reduce API calls, and ensure secrets are created during initial deployment (not lazily).
</details>

<details>
<summary>Question 4: Your ArgoCD installation manages 500 Applications across 20 clusters. Users report that sync times are increasing and the ArgoCD UI is slow. What tuning would you apply?</summary>

Several optimizations: (1) **Increase `--app-resync` interval** from the default 180 seconds to 300-600 seconds. This reduces how often ArgoCD re-evaluates every Application. (2) **Enable sharding**: configure multiple application controller replicas with `--shard` flag so each controller manages a subset of clusters. (3) **Use Server-Side Apply** (`ServerSideApply=true` in syncOptions) to reduce the amount of data ArgoCD needs to calculate diffs for. (4) **Reduce Git polling**: set `timeout.reconciliation` to 300s and use Git webhooks for push-based notifications instead of polling. (5) **Increase Redis memory**: ArgoCD caches manifests in Redis; 500 apps need 4-8GB of Redis memory. (6) **Use `--app-hard-resync`** with a longer interval (24h) to periodically force-refresh cached state. (7) **Split into multiple ArgoCD instances** if one instance cannot handle the load -- use one instance per region or per environment.
</details>

<details>
<summary>Question 5: What is the difference between the mono-repo and repo-per-team Git strategies? When would you choose each?</summary>

**Mono-repo**: All teams' Kubernetes manifests in one repository. Choose when: teams are small (under 10), changes frequently span multiple services, and you want a single audit trail. The main risk is scale: Git operations slow down, and a merge conflict in one team's directory can block another team's deployment.

**Repo-per-team**: Each team has their own Git repository for Kubernetes manifests. Choose when: teams are large (10+), need independent merge queues, and have different deployment cadences. Access control is cleaner (repo-level permissions vs. CODEOWNERS). The main risk is consistency: cross-cutting changes (like updating a shared label standard) require PRs to every repo.

**Hybrid** (recommended for 10+ teams): A central platform repo for shared configuration plus per-team repos for application manifests. The platform team controls the baseline, teams control their applications. ArgoCD ApplicationSets dynamically discover team repos and create Applications. This balances consistency with autonomy.
</details>

<details>
<summary>Question 6: How do you prevent a team from deploying to a namespace they do not own in a multi-tenant ArgoCD setup?</summary>

Use **ArgoCD Projects** with destination restrictions. Each team's Project specifies exactly which namespaces and which cluster servers they can deploy to:

```yaml
spec:
  destinations:
    - namespace: payments
      server: https://kubernetes.default.svc
    - namespace: payments-staging
      server: https://staging.company.internal
```

Any Application in the `payments` Project that targets a different namespace (e.g., `identity`) will be rejected by ArgoCD. This is enforced server-side by the ArgoCD API server -- it cannot be bypassed by editing the Application manifest. Additionally, combine this with Kubernetes RBAC: the ArgoCD service account for each Project should only have permissions in the allowed namespaces. This provides defense-in-depth: ArgoCD Project restrictions prevent the Application from being created, and Kubernetes RBAC prevents the sync from succeeding even if the Project restriction were somehow bypassed.
</details>

---

## Hands-On Exercise: Build an Enterprise GitOps Platform

In this exercise, you will set up a multi-tenant ArgoCD installation with Project-based RBAC, ApplicationSets, and External Secrets Operator.

### Task 1: Create the Lab Cluster and Install ArgoCD

<details>
<summary>Solution</summary>

```bash
kind create cluster --name enterprise-gitops

# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=120s

ARGOCD_PW=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d)
echo "ArgoCD admin password: $ARGOCD_PW"
```

</details>

### Task 2: Configure Multi-Tenant ArgoCD Projects

<details>
<summary>Solution</summary>

```bash
# Create team namespaces
for TEAM in payments identity search platform; do
  kubectl create namespace $TEAM
done

# Create ArgoCD Projects for each team
cat <<'EOF' | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: payments
  namespace: argocd
spec:
  description: "Payments team"
  sourceRepos:
    - '*'
  destinations:
    - namespace: payments
      server: https://kubernetes.default.svc
  clusterResourceWhitelist: []
  namespaceResourceWhitelist:
    - group: ''
      kind: '*'
    - group: apps
      kind: '*'
    - group: networking.k8s.io
      kind: '*'
---
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: identity
  namespace: argocd
spec:
  description: "Identity team"
  sourceRepos:
    - '*'
  destinations:
    - namespace: identity
      server: https://kubernetes.default.svc
  clusterResourceWhitelist: []
  namespaceResourceWhitelist:
    - group: ''
      kind: '*'
    - group: apps
      kind: '*'
---
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: platform
  namespace: argocd
spec:
  description: "Platform team - full access"
  sourceRepos:
    - '*'
  destinations:
    - namespace: '*'
      server: '*'
  clusterResourceWhitelist:
    - group: '*'
      kind: '*'
EOF

echo "ArgoCD Projects:"
kubectl get appprojects -n argocd
```

</details>

### Task 3: Deploy Applications with the App of Apps Pattern

<details>
<summary>Solution</summary>

```bash
# Create a simulated application for the payments team
cat <<'EOF' | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-processor
  namespace: argocd
  labels:
    team: payments
spec:
  project: payments
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: payments
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: identity-auth
  namespace: argocd
  labels:
    team: identity
spec:
  project: identity
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: identity
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF

# Wait for sync
sleep 15

echo "=== ArgoCD Applications ==="
kubectl get applications -n argocd -o custom-columns=\
NAME:.metadata.name,\
PROJECT:.spec.project,\
STATUS:.status.sync.status,\
HEALTH:.status.health.status,\
NAMESPACE:.spec.destination.namespace
```

</details>

### Task 4: Test RBAC Enforcement

<details>
<summary>Solution</summary>

```bash
# Test: Try to create an application in the payments project targeting the identity namespace
echo "=== Test: Cross-namespace deployment (should fail) ==="
cat <<'EOF' | kubectl apply -f - 2>&1 || true
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-in-wrong-namespace
  namespace: argocd
spec:
  project: payments
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: identity
  syncPolicy:
    automated:
      prune: true
EOF

# The application might be created but sync should fail
echo ""
echo "=== Check if the cross-namespace app synced ==="
sleep 5
kubectl get application payments-in-wrong-namespace -n argocd \
  -o jsonpath='{.status.conditions[*].message}' 2>/dev/null || echo "Application rejected or sync failed as expected"

# Clean up the test
kubectl delete application payments-in-wrong-namespace -n argocd 2>/dev/null || true

echo ""
echo "=== Legitimate applications ==="
kubectl get applications -n argocd -o custom-columns=\
NAME:.metadata.name,PROJECT:.spec.project,SYNC:.status.sync.status
```

</details>

### Task 5: Build a Platform Dashboard

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/platform-dashboard.sh
#!/bin/bash
echo "============================================="
echo "  ENTERPRISE GITOPS PLATFORM DASHBOARD"
echo "  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================="

echo ""
echo "--- ArgoCD Health ---"
ARGO_PODS=$(kubectl get pods -n argocd --no-headers | grep Running | wc -l | tr -d ' ')
echo "  ArgoCD Pods Running: $ARGO_PODS"

echo ""
echo "--- Projects ---"
kubectl get appprojects -n argocd --no-headers | while read LINE; do
  PROJECT=$(echo $LINE | awk '{print $1}')
  APP_COUNT=$(kubectl get applications -n argocd -o json | jq "[.items[] | select(.spec.project == \"$PROJECT\")] | length")
  echo "  $PROJECT: $APP_COUNT applications"
done

echo ""
echo "--- Applications by Sync Status ---"
SYNCED=$(kubectl get applications -n argocd -o json | jq '[.items[] | select(.status.sync.status == "Synced")] | length')
OUTOFSYNC=$(kubectl get applications -n argocd -o json | jq '[.items[] | select(.status.sync.status == "OutOfSync")] | length')
UNKNOWN=$(kubectl get applications -n argocd -o json | jq '[.items[] | select(.status.sync.status == "Unknown")] | length')
echo "  Synced: $SYNCED"
echo "  OutOfSync: $OUTOFSYNC"
echo "  Unknown: $UNKNOWN"

echo ""
echo "--- Applications by Health ---"
HEALTHY=$(kubectl get applications -n argocd -o json | jq '[.items[] | select(.status.health.status == "Healthy")] | length')
PROGRESSING=$(kubectl get applications -n argocd -o json | jq '[.items[] | select(.status.health.status == "Progressing")] | length')
DEGRADED=$(kubectl get applications -n argocd -o json | jq '[.items[] | select(.status.health.status == "Degraded")] | length')
echo "  Healthy: $HEALTHY"
echo "  Progressing: $PROGRESSING"
echo "  Degraded: $DEGRADED"

echo ""
echo "--- Team Namespace Resources ---"
for NS in payments identity search; do
  PODS=$(kubectl get pods -n $NS --no-headers 2>/dev/null | wc -l | tr -d ' ')
  SVCS=$(kubectl get services -n $NS --no-headers 2>/dev/null | wc -l | tr -d ' ')
  echo "  $NS: $PODS pods, $SVCS services"
done

echo ""
echo "============================================="
SCRIPT

chmod +x /tmp/platform-dashboard.sh
bash /tmp/platform-dashboard.sh
```

</details>

### Clean Up

```bash
kind delete cluster --name enterprise-gitops
rm /tmp/platform-dashboard.sh
```

### Success Criteria

- [ ] I installed ArgoCD with multi-tenant Projects for 3 teams
- [ ] I deployed applications scoped to team namespaces
- [ ] I verified that cross-namespace deployment is prevented by Project RBAC
- [ ] I built a platform dashboard showing application sync and health status
- [ ] I can explain the App of Apps pattern and when to use ApplicationSets
- [ ] I can describe at least 3 secrets management strategies for GitOps
- [ ] I can design a Git repository strategy for a 10+ team organization

---

## Next Module

With the GitOps platform in place, it is time to secure it with Zero Trust principles. Head to [Module 10.9: Zero Trust Architecture in Hybrid Cloud](../module-10.9-zero-trust/) to learn about BeyondCorp, Identity-Aware Proxies, micro-segmentation, and how to remove VPNs from your enterprise architecture.

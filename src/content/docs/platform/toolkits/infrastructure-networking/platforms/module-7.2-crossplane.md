---
title: "Module 7.2: Crossplane"
slug: platform/toolkits/infrastructure-networking/platforms/module-7.2-crossplane
sidebar:
  order: 3
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 50-60 minutes

## Overview

Terraform in CI pipelines. CloudFormation templates. Manual console clicks. Infrastructure provisioning is fragmented. Crossplane unifies it by extending Kubernetes with cloud provider APIs—provision AWS RDS, GCP Cloud SQL, or Azure CosmosDB using `kubectl apply`. Infrastructure as Kubernetes resources.

**What You'll Learn**:
- Crossplane architecture and providers
- Managed Resources and Compositions
- Building self-service infrastructure APIs
- GitOps for infrastructure

**Prerequisites**:
- [Platform Engineering Discipline](../../../disciplines/core-platform/platform-engineering/)
- Kubernetes Custom Resource Definitions (CRDs)
- Basic cloud provider knowledge (AWS/GCP/Azure)

---

## Why This Module Matters

Platform engineers shouldn't be bottlenecks. When every database request requires a Terraform PR reviewed by the platform team, you don't scale. Crossplane lets you define self-service infrastructure APIs—developers get what they need (databases, buckets, queues) without ticket queues or manual provisioning.

> 💡 **Did You Know?** Crossplane was created by Upbound, founded by former Google engineers who worked on Kubernetes. The project is now a CNCF incubating project. Its key insight: Kubernetes already solved the control loop problem—why reinvent it for infrastructure? Crossplane uses the same reconciliation pattern for cloud resources.

---

## The Infrastructure Problem

```
TRADITIONAL INFRASTRUCTURE PROVISIONING
════════════════════════════════════════════════════════════════════

Developer needs database:

1. Creates Jira ticket: "Need PostgreSQL database"
2. Waits for platform team to see ticket (hours/days)
3. Platform engineer writes Terraform
4. PR review, approval process
5. Terraform apply (maybe in separate pipeline)
6. Platform engineer shares credentials with developer
7. Developer can finally use database

Time: Days to weeks
Problems: Bottleneck, manual steps, drift between environments

═══════════════════════════════════════════════════════════════════

WITH CROSSPLANE
════════════════════════════════════════════════════════════════════

Developer needs database:

1. Applies YAML:
   kubectl apply -f database.yaml

2. Crossplane provisions in cloud
3. Secret with credentials auto-created
4. Developer uses database

Time: Minutes
Benefits: Self-service, GitOps, consistent, no bottleneck
```

---

## Architecture

```
CROSSPLANE ARCHITECTURE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    CROSSPLANE CORE                          │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │ Composition │  │  Package    │  │   RBAC      │        │ │
│  │  │  Controller │  │  Manager    │  │  Controller │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────▼───────────────────────────────┐ │
│  │                       PROVIDERS                             │ │
│  │                                                             │ │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐              │ │
│  │  │  AWS      │  │   GCP     │  │   Azure   │              │ │
│  │  │ Provider  │  │ Provider  │  │  Provider │              │ │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘              │ │
│  │        │              │              │                     │ │
│  └────────┼──────────────┼──────────────┼─────────────────────┘ │
│           │              │              │                       │
└───────────┼──────────────┼──────────────┼───────────────────────┘
            │              │              │
            ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CLOUD PROVIDERS                            │
│                                                                  │
│      AWS               GCP                Azure                 │
│  (RDS, S3, etc)   (Cloud SQL, GCS)    (CosmosDB, etc)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Provider** | Plugin that talks to cloud API (AWS, GCP, Azure) |
| **Managed Resource** | Direct mapping to cloud resource (RDS instance, S3 bucket) |
| **Composition** | Template that combines multiple resources |
| **Composite Resource (XR)** | Custom API that triggers a Composition |
| **Claim (XRC)** | Namespace-scoped request for a Composite Resource |

---

## Installation

```bash
# Install Crossplane via Helm
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update

helm install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system \
  --create-namespace

# Wait for Crossplane
kubectl wait --for=condition=ready pod -l app=crossplane -n crossplane-system --timeout=120s

# Verify
kubectl get pods -n crossplane-system
```

### Install Provider

```yaml
# Install AWS Provider
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
spec:
  package: xpkg.upbound.io/upbound/provider-family-aws:v1.1.0
---
# Configure credentials
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-creds
      key: credentials
```

```bash
# Create credentials secret
kubectl create secret generic aws-creds \
  -n crossplane-system \
  --from-file=credentials=./aws-credentials.txt

# aws-credentials.txt:
# [default]
# aws_access_key_id = YOUR_ACCESS_KEY
# aws_secret_access_key = YOUR_SECRET_KEY
```

---

## Managed Resources

### Direct Cloud Resource Creation

```yaml
# Create S3 bucket directly
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: my-crossplane-bucket
spec:
  forProvider:
    region: us-west-2
    tags:
      Environment: production
      ManagedBy: crossplane
  providerConfigRef:
    name: default
---
# Create RDS instance directly
apiVersion: rds.aws.upbound.io/v1beta1
kind: Instance
metadata:
  name: my-database
spec:
  forProvider:
    region: us-west-2
    instanceClass: db.t3.micro
    engine: postgres
    engineVersion: "15"
    allocatedStorage: 20
    username: admin
    passwordSecretRef:
      name: db-password
      namespace: default
      key: password
    skipFinalSnapshot: true
  providerConfigRef:
    name: default
  writeConnectionSecretToRef:
    name: db-connection
    namespace: default
```

```bash
# Check status
kubectl get bucket.s3.aws.upbound.io
kubectl get instance.rds.aws.upbound.io

# See events
kubectl describe bucket.s3.aws.upbound.io my-crossplane-bucket
```

> 💡 **Did You Know?** Crossplane providers are generated from cloud provider APIs. The AWS provider supports 1,000+ resource types—everything AWS offers, from EC2 to SageMaker to IoT. If AWS has an API for it, Crossplane can manage it.

---

## Compositions

### Building Custom APIs

Compositions let you create opinionated abstractions. Instead of exposing raw RDS to developers, create a "Database" API with your organization's defaults.

```yaml
# CompositeResourceDefinition (XRD) - Define the API
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: databases.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: Database
    plural: databases
  claimNames:
    kind: DatabaseClaim
    plural: databaseclaims
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              size:
                type: string
                enum: ["small", "medium", "large"]
                description: "Database size"
              engine:
                type: string
                enum: ["postgres", "mysql"]
                default: "postgres"
            required:
              - size
          status:
            type: object
            properties:
              endpoint:
                type: string
              port:
                type: integer
---
# Composition - Define what gets created
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: database-aws
  labels:
    provider: aws
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: Database

  patchSets:
  - name: common-tags
    patches:
    - type: FromCompositeFieldPath
      fromFieldPath: metadata.labels
      toFieldPath: spec.forProvider.tags

  resources:
  # Security Group
  - name: security-group
    base:
      apiVersion: ec2.aws.upbound.io/v1beta1
      kind: SecurityGroup
      spec:
        forProvider:
          region: us-west-2
          description: Database security group
          vpcId: vpc-12345678
    patches:
    - type: FromCompositeFieldPath
      fromFieldPath: metadata.name
      toFieldPath: metadata.name
      transforms:
      - type: string
        string:
          fmt: "%s-sg"

  # RDS Instance
  - name: rds-instance
    base:
      apiVersion: rds.aws.upbound.io/v1beta1
      kind: Instance
      spec:
        forProvider:
          region: us-west-2
          skipFinalSnapshot: true
          publiclyAccessible: false
          storageEncrypted: true
          autoMinorVersionUpgrade: true
        writeConnectionSecretToRef:
          namespace: crossplane-system
    patches:
    # Map size to instance class
    - type: FromCompositeFieldPath
      fromFieldPath: spec.size
      toFieldPath: spec.forProvider.instanceClass
      transforms:
      - type: map
        map:
          small: db.t3.micro
          medium: db.t3.small
          large: db.t3.medium

    # Map size to storage
    - type: FromCompositeFieldPath
      fromFieldPath: spec.size
      toFieldPath: spec.forProvider.allocatedStorage
      transforms:
      - type: map
        map:
          small: 20
          medium: 50
          large: 100

    # Engine selection
    - type: FromCompositeFieldPath
      fromFieldPath: spec.engine
      toFieldPath: spec.forProvider.engine

    # Connection secret name
    - type: FromCompositeFieldPath
      fromFieldPath: metadata.name
      toFieldPath: spec.writeConnectionSecretToRef.name
      transforms:
      - type: string
        string:
          fmt: "%s-connection"

    # Expose endpoint to status
    - type: ToCompositeFieldPath
      fromFieldPath: status.atProvider.endpoint
      toFieldPath: status.endpoint
    - type: ToCompositeFieldPath
      fromFieldPath: status.atProvider.port
      toFieldPath: status.port

    connectionDetails:
    - name: endpoint
      fromFieldPath: status.atProvider.endpoint
    - name: port
      fromFieldPath: status.atProvider.port
    - name: username
      fromFieldPath: spec.forProvider.username
    - name: password
      fromConnectionSecretKey: attribute.password
```

### Developer Experience (Using Claims)

```yaml
# Developer applies this simple claim
apiVersion: platform.example.com/v1alpha1
kind: DatabaseClaim
metadata:
  name: my-app-db
  namespace: my-team
spec:
  size: small
  engine: postgres
  compositionRef:
    name: database-aws
  writeConnectionSecretToRef:
    name: my-app-db-connection
```

```bash
# Check status
kubectl get databaseclaim -n my-team

# Connection secret created automatically
kubectl get secret my-app-db-connection -n my-team -o yaml
```

---

## GitOps with Crossplane

```
GITOPS + CROSSPLANE
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                        GIT REPOSITORY                            │
│                                                                  │
│  infrastructure/                                                 │
│  ├── staging/                                                   │
│  │   └── database.yaml    # DatabaseClaim (size: small)        │
│  └── production/                                                │
│      └── database.yaml    # DatabaseClaim (size: large)        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ ArgoCD syncs
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES + CROSSPLANE                       │
│                                                                  │
│  DatabaseClaim ──▶ Composition ──▶ RDS Instance                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Crossplane provisions
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          AWS                                     │
│                                                                  │
│  Staging: db.t3.micro, 20GB                                     │
│  Production: db.t3.medium, 100GB                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Benefits

1. **Same PR process** for infrastructure and application changes
2. **Drift detection** - Crossplane reconciles continuously
3. **Self-service** - Developers can request infrastructure via GitOps
4. **Audit trail** - Git history shows who changed what

---

## Common Patterns

### Multi-Environment Compositions

```yaml
# Different composition per environment
apiVersion: platform.example.com/v1alpha1
kind: DatabaseClaim
metadata:
  name: my-db
spec:
  size: small
  compositionSelector:
    matchLabels:
      environment: production  # Selects production composition
```

### Composition Functions

```yaml
# Use Composition Functions for complex logic
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: database-with-backup
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: Database
  mode: Pipeline
  pipeline:
  - step: create-resources
    functionRef:
      name: function-patch-and-transform
    input:
      apiVersion: pt.fn.crossplane.io/v1beta1
      kind: Resources
      resources:
      - name: database
        base:
          apiVersion: rds.aws.upbound.io/v1beta1
          kind: Instance
          # ...
```

> 💡 **Did You Know?** Crossplane Composition Functions allow you to write custom logic in any language. You can create functions in Go, Python, or even call external APIs during composition. This enables complex scenarios like "if production, add read replicas" that would be impossible with static templates.

> 💡 **Did You Know?** Crossplane's "provider families" dramatically simplified multi-cloud setups. Before, each AWS service had its own provider package. Now, `provider-family-aws` installs a lightweight base, and you add only the service providers you need (RDS, S3, etc.). This reduced memory usage from gigabytes to megabytes for large installations—making Crossplane practical for clusters with hundreds of CRDs.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Exposing raw Managed Resources | Developers overwhelmed by options | Create Compositions with sensible defaults |
| No deletion policy | Resources deleted when claim deleted | Set `deletionPolicy: Orphan` when needed |
| Missing status mapping | Developers can't see endpoint | Use ToCompositeFieldPath patches |
| No connection secrets | App can't connect to provisioned resource | Always configure writeConnectionSecretToRef |
| Single provider config | Can't do multi-account | Create multiple ProviderConfigs |
| Not testing compositions | Broken compositions in production | Use Crossplane's composition validation |

---

## War Story: The Database That Wouldn't Die

*A team deleted a DatabaseClaim. Crossplane deleted the production RDS instance. Panic ensued.*

**What went wrong**:
1. Default `deletionPolicy` is `Delete`
2. Deleting the claim deleted the underlying RDS
3. No backup (skipFinalSnapshot: true was set)
4. Data gone

**The fix**:
```yaml
# For production databases
spec:
  forProvider:
    skipFinalSnapshot: false
    deletionProtection: true
  deletionPolicy: Orphan  # Don't delete cloud resource when CR deleted
```

**Best practices**:
1. Always use `deletionPolicy: Orphan` for production data
2. Enable `deletionProtection` on cloud resources
3. Disable `skipFinalSnapshot` for databases
4. Test deletion behavior in staging first

---

## Quiz

### Question 1
What's the difference between a Managed Resource and a Composite Resource?

<details>
<summary>Show Answer</summary>

**Managed Resource**:
- Direct 1:1 mapping to cloud resource
- Low-level, exposes all provider options
- Example: `Instance.rds.aws.upbound.io`

**Composite Resource (XR)**:
- Custom API defined by platform team
- Abstracts complexity via Composition
- Creates multiple Managed Resources
- Example: `Database.platform.example.com`

Developers typically use Composite Resources (via Claims), while platform engineers define them using Compositions.

</details>

### Question 2
Why use Compositions instead of direct Managed Resources?

<details>
<summary>Show Answer</summary>

**Direct Managed Resources**:
- Developers must know cloud-specific details
- No guardrails or defaults
- Easy to misconfigure
- Hard to enforce standards

**Compositions**:
- Abstract cloud complexity
- Enforce organizational standards
- Provide sensible defaults
- Self-service with guardrails
- Single resource can create many underlying resources

Example: A "Database" Composition can create RDS + security group + subnet group + parameter group, all with compliant settings.

</details>

### Question 3
How does Crossplane integrate with GitOps?

<details>
<summary>Show Answer</summary>

Crossplane resources are Kubernetes CRDs, so GitOps tools (ArgoCD, Flux) can manage them:

1. **Store claims in Git** alongside application manifests
2. **ArgoCD syncs** claims to cluster
3. **Crossplane provisions** cloud resources
4. **Drift detection** - Crossplane continuously reconciles

Benefits:
- Same PR workflow for app + infra
- Audit trail in Git
- Environment promotion via Git branches
- Self-service for developers

</details>

---

## Hands-On Exercise

### Objective
Install Crossplane and create a custom Database API.

### Environment Setup

```bash
# Install Crossplane
helm install crossplane crossplane-stable/crossplane \
  -n crossplane-system --create-namespace

# Wait for ready
kubectl wait --for=condition=ready pod -l app=crossplane -n crossplane-system --timeout=120s
```

### Tasks

1. **Verify Crossplane is running**:
   ```bash
   kubectl get pods -n crossplane-system
   ```

2. **Install AWS Provider** (or use local provider for testing):
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: pkg.crossplane.io/v1
   kind: Provider
   metadata:
     name: provider-nop
   spec:
     package: xpkg.upbound.io/crossplane-contrib/provider-nop:v0.2.0
   EOF
   ```

3. **Create a simple XRD**:
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: apiextensions.crossplane.io/v1
   kind: CompositeResourceDefinition
   metadata:
     name: xdatabases.example.com
   spec:
     group: example.com
     names:
       kind: XDatabase
       plural: xdatabases
     claimNames:
       kind: Database
       plural: databases
     versions:
     - name: v1alpha1
       served: true
       referenceable: true
       schema:
         openAPIV3Schema:
           type: object
           properties:
             spec:
               type: object
               properties:
                 size:
                   type: string
                   enum: ["small", "medium", "large"]
               required:
                 - size
   EOF
   ```

4. **Verify XRD is established**:
   ```bash
   kubectl get xrd
   kubectl get crd | grep example.com
   ```

5. **Create a Composition** (simplified, using NOP provider):
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: apiextensions.crossplane.io/v1
   kind: Composition
   metadata:
     name: database-composition
   spec:
     compositeTypeRef:
       apiVersion: example.com/v1alpha1
       kind: XDatabase
     resources:
     - name: nop-resource
       base:
         apiVersion: nop.crossplane.io/v1alpha1
         kind: NopResource
         spec:
           forProvider:
             fields:
               size: ""
       patches:
       - fromFieldPath: spec.size
         toFieldPath: spec.forProvider.fields.size
   EOF
   ```

6. **Create a Claim**:
   ```yaml
   kubectl apply -f - <<EOF
   apiVersion: example.com/v1alpha1
   kind: Database
   metadata:
     name: my-database
     namespace: default
   spec:
     size: small
   EOF
   ```

7. **Check resources**:
   ```bash
   kubectl get database
   kubectl get xdatabase
   kubectl get nopresource
   ```

### Success Criteria
- [ ] Crossplane running
- [ ] Provider installed
- [ ] XRD established
- [ ] Composition created
- [ ] Claim creates composite resource

### Bonus Challenge
Modify the Composition to create different resources based on the `size` parameter (e.g., add a second NopResource for "large" size).

---

## Further Reading

- [Crossplane Documentation](https://docs.crossplane.io/)
- [Upbound Marketplace](https://marketplace.upbound.io/) - Providers and Functions
- [Crossplane Compositions Guide](https://docs.crossplane.io/latest/concepts/compositions/)

---

## Next Module

Continue to [Module 7.3: cert-manager](module-7.3-cert-manager/) to learn automated certificate management for Kubernetes.

---

*"Infrastructure should be as easy to request as a library import. Crossplane makes it so."*

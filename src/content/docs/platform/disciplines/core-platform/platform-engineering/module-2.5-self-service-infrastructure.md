---
title: "Module 2.5: Self-Service Infrastructure"
slug: platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure
sidebar:
  order: 6
---
> **Discipline Module** | Complexity: `[COMPLEX]` | Time: 50-60 min

## Prerequisites

Before starting this module, you should:

- Complete [Module 2.1: What is Platform Engineering?](../module-2.1-what-is-platform-engineering/) - Platform foundations
- Complete [Module 2.3: Internal Developer Platforms](../module-2.3-internal-developer-platforms/) - IDP architecture
- Complete [Module 2.4: Golden Paths](../module-2.4-golden-paths/) - Template design
- Understand infrastructure-as-code concepts (Terraform, Pulumi, or similar)
- Familiarity with Kubernetes Custom Resources

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design self-service infrastructure workflows with appropriate guardrails and approval gates**
- **Implement infrastructure request APIs that provision resources in minutes instead of days**
- **Build policy-as-code controls that enforce organizational standards without blocking developer autonomy**
- **Evaluate self-service adoption patterns to identify gaps in your platform's capabilities**

## Why This Module Matters

The promise of cloud computing was "infrastructure in minutes." The reality for most developers:
- File a ticket
- Wait for approval
- Wait for provisioning
- Get credentials (maybe)
- Repeat when requirements change

Self-service infrastructure makes that promise real. Developers get what they need, when they need it, while organizations maintain governance, cost control, and security.

This module teaches you to build self-service systems that actually work.

## Did You Know?

- **Netflix provisions databases in under 10 minutes** through self-service—the same provisioning used to take 3 weeks with manual processes
- **The term "ClickOps"** describes the anti-pattern of infrastructure managed through cloud console clicks—brittle, unauditable, and error-prone
- **Crossplane**, a CNCF project, enables Kubernetes-style management of any infrastructure through custom resources
- **80% of cloud waste** comes from over-provisioned or orphaned resources—self-service with guardrails can dramatically reduce this

---

## What is Self-Service Infrastructure?

### Definition

**Self-service infrastructure** enables developers to provision, modify, and decommission infrastructure resources through automated systems, without requiring tickets, approvals, or manual intervention from operations teams.

```
┌─────────────────────────────────────────────────────────────────┐
│                 SELF-SERVICE EVOLUTION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Traditional            Partial Self-Service    Full Self-Service│
│  (Ticket-based)         (Guardrailed)           (Golden Paths)   │
│                                                                  │
│  Developer              Developer               Developer        │
│      │                      │                       │            │
│      ▼                      ▼                       ▼            │
│  ┌──────┐              ┌──────────┐            ┌──────────┐     │
│  │Ticket│              │ Request  │            │ Request  │     │
│  │System│              │ + Auto-  │            │ Instant  │     │
│  └──┬───┘              │ approval │            │ Provision│     │
│     │                  └────┬─────┘            └────┬─────┘     │
│     ▼                       │                       │            │
│  ┌──────┐                   │                       │            │
│  │ Ops  │                   ▼                       ▼            │
│  │Queue │              Provisioned            Provisioned        │
│  └──┬───┘              in ~1 hour             in ~5 minutes      │
│     │                                                            │
│     ▼                                                            │
│  Manual                                                          │
│  Provisioning                                                    │
│  (~days/weeks)                                                   │
│                                                                  │
│  Days-Weeks            Hours                   Minutes           │
└─────────────────────────────────────────────────────────────────┘
```

### The Self-Service Triangle

```
                        ┌─────────────┐
                        │             │
                        │   SPEED     │
                        │             │
                        └──────┬──────┘
                               │
                    Faster provisioning
                    means faster delivery
                               │
              ┌────────────────┴────────────────┐
              │                                  │
              │        SELF-SERVICE              │
              │                                  │
              │     Balance all three            │
              │                                  │
              └────────────────┬────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                                         │
          ▼                                         ▼
    ┌───────────┐                           ┌───────────┐
    │           │                           │           │
    │ CONTROL   │                           │ AUTONOMY  │
    │           │                           │           │
    └───────────┘                           └───────────┘

    Governance,                              Developer
    compliance,                              freedom and
    cost management                          velocity
```

The art of self-service is balancing these three:
- **Too much control** → Slow, ticket-based systems return
- **Too much autonomy** → Cost explosion, security gaps, chaos
- **Speed without governance** → Fast path to technical debt

---

## Self-Service Architecture

### The Control Plane Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    SELF-SERVICE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                      Developer Interface                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ Portal   │    │  CLI     │    │   API    │    │   Git    │ │
│  │ (UI)     │    │          │    │          │    │  (GitOps)│ │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘ │
│       │               │               │               │        │
│       └───────────────┴───────┬───────┴───────────────┘        │
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    CONTROL PLANE                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         ││
│  │  │  Request    │  │   Policy    │  │   Cost      │         ││
│  │  │  Validation │  │   Engine    │  │   Controls  │         ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘         ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         ││
│  │  │  Quota      │  │  Approval   │  │   Audit     │         ││
│  │  │  Management │  │  Workflows  │  │   Logging   │         ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘         ││
│  └─────────────────────────────────────────────────────────────┘│
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  PROVISIONING ENGINE                         ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   ││
│  │  │ Terraform│  │ Crossplane│ │ Pulumi   │  │ CloudForm│   ││
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   ││
│  └─────────────────────────────────────────────────────────────┘│
│                               │                                  │
│                               ▼                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   AWS    │  │   GCP    │  │  Azure   │  │ Internal │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

**1. Developer Interface**

Multiple ways to request infrastructure:

```yaml
# Option 1: Portal UI
# Click-based, guided experience for discovery and occasional use

# Option 2: CLI
$ platform infra create database \
    --type postgresql \
    --size medium \
    --env staging

# Option 3: API
POST /api/v1/infrastructure
{
  "type": "database",
  "provider": "postgresql",
  "size": "medium",
  "environment": "staging"
}

# Option 4: GitOps (Declarative)
# infrastructure/staging/database.yaml
apiVersion: platform.example.com/v1alpha1
kind: PostgreSQLInstance
metadata:
  name: orders-db
  namespace: team-orders
spec:
  size: medium
  version: "15"
```

**2. Control Plane**

The brain that enforces guardrails:

```yaml
# Policy Example (OPA/Rego)
package platform.infrastructure

# Deny databases larger than allowed
deny[msg] {
  input.kind == "PostgreSQLInstance"
  input.spec.size == "xlarge"
  not has_exception(input.metadata.namespace)
  msg := "XLarge databases require architecture review"
}

# Enforce cost tags
deny[msg] {
  not input.metadata.labels["cost-center"]
  msg := "All resources must have cost-center label"
}

# Limit resources per team
deny[msg] {
  team := input.metadata.labels["team"]
  count(resources_by_team[team]) > quota[team]
  msg := sprintf("Team %v has exceeded resource quota", [team])
}
```

**3. Provisioning Engine**

Translates requests into actual infrastructure:

```yaml
# Crossplane Composition Example
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: postgresql-standard
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: PostgreSQLInstance

  resources:
    # RDS Instance
    - name: rds-instance
      base:
        apiVersion: rds.aws.crossplane.io/v1beta1
        kind: Instance
        spec:
          forProvider:
            engine: postgres
            engineVersion: "15"
            instanceClass: db.t3.medium  # Default
            allocatedStorage: 20
            publiclyAccessible: false
            vpcSecurityGroupIds: []  # Patched
            dbSubnetGroupName: ""    # Patched
          writeConnectionSecretToRef:
            namespace: crossplane-system
      patches:
        # Size to instance class mapping
        - type: FromCompositeFieldPath
          fromFieldPath: spec.size
          toFieldPath: spec.forProvider.instanceClass
          transforms:
            - type: map
              map:
                small: db.t3.micro
                medium: db.t3.medium
                large: db.t3.large

    # Secret for connection details
    - name: connection-secret
      base:
        apiVersion: kubernetes.crossplane.io/v1alpha1
        kind: Object
        spec:
          forProvider:
            manifest:
              apiVersion: v1
              kind: Secret
              metadata:
                namespace: ""  # Patched
```

---

## Infrastructure Abstractions

### The Abstraction Ladder

```
┌─────────────────────────────────────────────────────────────────┐
│                    ABSTRACTION LEVELS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 4: Intent                                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ "I need a database for my orders service"                  │ │
│  │  → Platform chooses type, size, config                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  Level 3: Simplified Resource                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ apiVersion: platform/v1                                    │ │
│  │ kind: Database                                             │ │
│  │ spec:                                                      │ │
│  │   type: postgresql                                         │ │
│  │   size: medium                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  Level 2: Provider Resource                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ apiVersion: rds.aws.crossplane.io/v1beta1                  │ │
│  │ kind: Instance                                             │ │
│  │ spec:                                                      │ │
│  │   forProvider:                                             │ │
│  │     engine: postgres                                       │ │
│  │     instanceClass: db.t3.medium                            │ │
│  │     allocatedStorage: 50                                   │ │
│  │     # ... 20+ more fields                                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  Level 1: Cloud API                                             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ aws rds create-db-instance \                               │ │
│  │   --db-instance-identifier orders-db \                     │ │
│  │   --engine postgres \                                      │ │
│  │   --db-instance-class db.t3.medium \                       │ │
│  │   # ... 50+ flags                                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Higher = Simpler for developers                                │
│  Lower = More control but more complexity                       │
└─────────────────────────────────────────────────────────────────┘
```

### Designing Good Abstractions

**Principle 1: Hide Complexity, Expose Intent**

```yaml
# Bad: Exposing too much detail
apiVersion: platform/v1
kind: Database
spec:
  provider: aws
  service: rds
  engine: postgres
  version: "15.2"
  instanceClass: db.t3.medium
  storage:
    type: gp3
    size: 50
    iops: 3000
    throughput: 125
  networking:
    subnetGroup: prod-private
    securityGroups:
      - sg-12345
    publicAccess: false
  backup:
    retentionDays: 7
    window: "03:00-04:00"
  # ... 30 more fields

# Good: Intent-focused
apiVersion: platform/v1
kind: Database
spec:
  type: postgresql       # What kind
  size: medium           # Relative sizing
  environment: staging   # Environment determines many defaults
```

**Principle 2: Sensible Defaults with Override**

```yaml
# Default behaviors (from platform config)
database:
  defaults:
    postgresql:
      version: "15"        # Latest stable
      backup:
        enabled: true
        retention: 7       # days
      encryption: true
      monitoring: enabled

# User only specifies what they need differently
apiVersion: platform/v1
kind: Database
spec:
  type: postgresql
  size: medium
  # Override specific default
  backup:
    retention: 30  # Need longer retention for this one
```

**Principle 3: T-Shirt Sizing**

```yaml
# Define sizes centrally
sizes:
  database:
    postgresql:
      small:
        instanceClass: db.t3.micro
        storage: 20
        connections: 50
        cost: ~$15/month
        useCase: "Development, small apps"

      medium:
        instanceClass: db.t3.medium
        storage: 50
        connections: 200
        cost: ~$60/month
        useCase: "Production, moderate traffic"

      large:
        instanceClass: db.t3.large
        storage: 200
        connections: 500
        cost: ~$150/month
        useCase: "High traffic, data-intensive"

      xlarge:
        instanceClass: db.r5.xlarge
        storage: 500
        connections: 1000
        cost: ~$400/month
        useCase: "Critical systems, requires approval"
```

---

## Guardrails and Governance

### Types of Guardrails

```
┌─────────────────────────────────────────────────────────────────┐
│                     GUARDRAIL TYPES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PREVENTIVE                    DETECTIVE                        │
│  (Stop before it happens)      (Find after the fact)            │
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐          │
│  │ • Admission control │      │ • Compliance scans  │          │
│  │ • Policy enforcement│      │ • Drift detection   │          │
│  │ • Quota limits      │      │ • Cost alerts       │          │
│  │ • Pre-deployment    │      │ • Security audits   │          │
│  │   validation        │      │                     │          │
│  └─────────────────────┘      └─────────────────────┘          │
│                                                                  │
│  CORRECTIVE                    ADVISORY                         │
│  (Fix automatically)           (Warn and suggest)               │
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐          │
│  │ • Auto-remediation  │      │ • Best practice     │          │
│  │ • Self-healing      │      │   warnings          │          │
│  │ • Orphan cleanup    │      │ • Cost optimization │          │
│  │ • Right-sizing      │      │   suggestions       │          │
│  └─────────────────────┘      └─────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementing Policy Guardrails

**Using OPA Gatekeeper (Kubernetes):**

```yaml
# Constraint Template: Define the policy type
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sresourcequota
spec:
  crd:
    spec:
      names:
        kind: K8sResourceQuota
      validation:
        openAPIV3Schema:
          properties:
            maxCpu:
              type: string
            maxMemory:
              type: string

  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sresourcequota

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          cpu_requested := container.resources.requests.cpu
          max_cpu := input.parameters.maxCpu
          to_number(cpu_requested) > to_number(max_cpu)
          msg := sprintf("Container %v requests %v CPU, max allowed is %v",
                        [container.name, cpu_requested, max_cpu])
        }

---
# Constraint: Apply the policy
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sResourceQuota
metadata:
  name: max-cpu-per-container
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["team-*"]
  parameters:
    maxCpu: "2"
    maxMemory: "4Gi"
```

**Using Crossplane Composition Validation:**

```yaml
# Composition with built-in guardrails
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: database-with-guardrails
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: Database

  # Pipeline mode with validation functions
  mode: Pipeline
  pipeline:
    # Step 1: Validate request
    - step: validate
      functionRef:
        name: function-validation
      input:
        apiVersion: validation.fn.crossplane.io/v1beta1
        kind: Validate
        rules:
          - name: size-limit
            condition: |
              spec.size in ["small", "medium", "large"]
            message: "Size must be small, medium, or large"

          - name: production-requires-backup
            condition: |
              spec.environment != "production" ||
              (spec.backup != null && spec.backup.enabled == true)
            message: "Production databases must have backups enabled"

    # Step 2: Provision if validation passes
    - step: provision
      functionRef:
        name: function-go-templating
```

### Cost Guardrails

```yaml
# Budget Policies
apiVersion: platform/v1
kind: BudgetPolicy
metadata:
  name: team-orders-budget
spec:
  target:
    team: team-orders

  limits:
    monthly:
      soft: 5000   # Warn at $5k
      hard: 7500   # Block at $7.5k

  actions:
    onSoftLimit:
      - notify:
          channels: [slack, email]
          message: "Team orders approaching budget limit"

    onHardLimit:
      - notify:
          channels: [slack, email, pagerduty]
      - policy: block-new-resources
        exceptions:
          - critical-incidents
          - approved-by: platform-team

  tracking:
    granularity: daily
    breakdown: [service, resource-type, environment]
```

### Quota Management

```yaml
# Team Quotas
apiVersion: platform/v1
kind: ResourceQuota
metadata:
  name: team-orders-quota
spec:
  team: team-orders

  environments:
    development:
      databases: 3
      caches: 2
      queues: 2
      storage: 100Gi

    staging:
      databases: 2
      caches: 1
      queues: 2
      storage: 50Gi

    production:
      databases: 5
      caches: 3
      queues: 5
      storage: 500Gi

  overrides:
    # Temporary increase for migration
    - until: "2024-06-01"
      environment: production
      databases: 8
      reason: "Database migration project"
      approvedBy: "platform-team"
```

---

## Self-Service Workflows

### The Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE REQUEST LIFECYCLE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   REQUEST      VALIDATE     APPROVE?      PROVISION    READY    │
│      │            │            │              │           │      │
│      ▼            ▼            ▼              ▼           ▼      │
│   ┌─────┐     ┌─────┐      ┌─────┐       ┌─────┐     ┌─────┐  │
│   │     │     │     │      │     │       │     │     │     │  │
│   │ Dev │────►│Check│─────►│Auto/│──────►│ IaC │────►│Done │  │
│   │     │     │     │      │Human│       │     │     │     │  │
│   └─────┘     └─────┘      └─────┘       └─────┘     └─────┘  │
│                  │            │              │                   │
│                  │            │              │                   │
│                  ▼            ▼              ▼                   │
│              ┌───────┐   ┌───────┐      ┌───────┐              │
│              │Policy │   │Approval│     │Terraform│             │
│              │Engine │   │ Rules  │     │Crossplane│            │
│              │       │   │        │     │Pulumi   │             │
│              └───────┘   └───────┘      └───────┘              │
│                                                                  │
│   Timing:                                                        │
│   ────────────────────────────────────────────────────────────  │
│   Auto-approved: REQUEST ──────────────────────────► READY      │
│                           ~5 minutes                             │
│                                                                  │
│   Requires approval: REQUEST ─────► WAIT ──────────► READY      │
│                               ~4 hours (SLA)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Approval Strategies

**Strategy 1: Risk-Based Approval**

```yaml
# approval-policy.yaml
apiVersion: platform/v1
kind: ApprovalPolicy
metadata:
  name: infrastructure-approvals
spec:
  rules:
    # Low risk: Auto-approve
    - name: dev-environment
      conditions:
        - field: spec.environment
          operator: equals
          value: development
        - field: spec.cost.monthly
          operator: lessThan
          value: 50
      approval: automatic

    # Medium risk: Single approver
    - name: staging-environment
      conditions:
        - field: spec.environment
          operator: equals
          value: staging
      approval:
        type: single
        from:
          - role: team-lead
          - role: platform-engineer

    # High risk: Multiple approvers
    - name: production-database
      conditions:
        - field: spec.environment
          operator: equals
          value: production
        - field: kind
          operator: equals
          value: Database
      approval:
        type: all
        required: 2
        from:
          - role: team-lead
          - role: dba
          - role: security

    # Very high risk: Review board
    - name: large-infrastructure
      conditions:
        - field: spec.cost.monthly
          operator: greaterThan
          value: 1000
      approval:
        type: quorum
        required: 3
        from:
          - group: architecture-board
```

**Strategy 2: Time-Based Auto-Approval**

```yaml
# If no response in X hours, auto-approve (for low-risk items)
approvalPolicy:
  lowRisk:
    autoApproveAfter: 4h
    notify:
      - slack: #platform-requests
      - email: approvers@company.com

  mediumRisk:
    autoApproveAfter: 24h
    escalateAfter: 8h

  highRisk:
    autoApproveAfter: never
    escalateAfter: 4h
```

### Self-Service Portal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPER PORTAL FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DISCOVER                    2. CONFIGURE                     │
│  ┌─────────────────────────┐   ┌─────────────────────────────┐ │
│  │                         │   │                              │ │
│  │  What do you need?      │   │  Database Details            │ │
│  │                         │   │                              │ │
│  │  [Database     ▼]       │   │  Name: [orders-db        ]  │ │
│  │                         │   │  Type: [PostgreSQL   ▼]     │ │
│  │  ○ PostgreSQL           │   │  Size: ○ Small ($15/mo)     │ │
│  │  ○ MongoDB              │   │        ● Medium ($60/mo)    │ │
│  │  ○ Redis                │   │        ○ Large ($150/mo)    │ │
│  │                         │   │  Environment: [Staging ▼]   │ │
│  │  Learn more about       │   │                              │ │
│  │  database options →     │   │  [Show Advanced Options]    │ │
│  │                         │   │                              │ │
│  └─────────────────────────┘   └─────────────────────────────┘ │
│                                                                  │
│  3. REVIEW                      4. PROVISION                     │
│  ┌─────────────────────────┐   ┌─────────────────────────────┐ │
│  │                         │   │                              │ │
│  │  Review Your Request    │   │  ✓ Request submitted         │ │
│  │                         │   │  ✓ Validation passed         │ │
│  │  Database: orders-db    │   │  ✓ Auto-approved            │ │
│  │  Type: PostgreSQL 15    │   │  ◐ Provisioning... (2 min)  │ │
│  │  Size: Medium           │   │  ○ Connection details        │ │
│  │  Cost: ~$60/month       │   │                              │ │
│  │                         │   │  Progress: ████████░░ 80%   │ │
│  │  Approval: Auto         │   │                              │ │
│  │  (dev environment)      │   │  [View Logs]                │ │
│  │                         │   │                              │ │
│  │  [Back] [Create →]      │   │                              │ │
│  └─────────────────────────┘   └─────────────────────────────┘ │
│                                                                  │
│  5. READY                                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │  ✅ Database Ready!                                          ││
│  │                                                              ││
│  │  Connection Details:                                         ││
│  │  Host: orders-db.staging.internal                            ││
│  │  Port: 5432                                                  ││
│  │  Secret: platform/orders-db-credentials (Kubernetes Secret)  ││
│  │                                                              ││
│  │  [Copy Connection String]  [View in Console]  [Documentation]││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Lifecycle Management

### Day 2 Operations

Self-service doesn't stop at provisioning:

```
┌─────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LIFECYCLE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Day 0: Provision    Day 1: Configure    Day 2+: Operate        │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐│
│  │              │   │              │   │                      ││
│  │ • Create     │   │ • First use  │   │ • Scale              ││
│  │ • Initial    │   │ • Connect    │   │ • Backup/Restore     ││
│  │   config     │   │   apps       │   │ • Version upgrade    ││
│  │              │   │ • Test       │   │ • Config changes     ││
│  │              │   │              │   │ • Troubleshoot       ││
│  │              │   │              │   │ • Decommission       ││
│  └──────────────┘   └──────────────┘   └──────────────────────┘│
│                                                                  │
│  All must be self-service!                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Self-Service Operations:**

```yaml
# Scaling
$ platform infra scale orders-db --size large
Scaling orders-db from medium to large...
✓ Approved (within quota)
✓ Scaling in progress (maintenance window: 2:00 AM)
✓ Estimated completion: ~15 minutes

# Backup/Restore
$ platform infra backup create orders-db --name pre-migration
Creating backup pre-migration...
✓ Backup created: s3://backups/orders-db/pre-migration

$ platform infra backup restore orders-db --from pre-migration --target orders-db-restore
Restoring to new instance orders-db-restore...
✓ Restore complete

# Version Upgrade
$ platform infra upgrade orders-db --version 16
Pre-upgrade checks:
✓ Compatible application versions
✓ Backup exists (less than 24h old)
⚠ Breaking changes in PG16: [link to docs]

Schedule upgrade for maintenance window? [Y/n]

# Decommission
$ platform infra delete orders-db
This will permanently delete orders-db and all data.
Type 'orders-db' to confirm: orders-db
✓ Final backup created
✓ Dependent services notified
✓ Resource deleted
✓ Cost allocation updated
```

### Orphan Detection and Cleanup

```yaml
# Orphan Detection Policy
apiVersion: platform/v1
kind: OrphanPolicy
metadata:
  name: detect-orphaned-resources
spec:
  detectionRules:
    # No traffic for 30 days
    - name: unused-databases
      type: Database
      condition:
        metric: connections_per_day
        threshold: 0
        duration: 30d
      action:
        - notify:
            owner: true
            message: "Database has had no connections for 30 days"
        - label:
            orphan-candidate: "true"

    # No owner team exists
    - name: ownerless-resources
      condition:
        label: team
        teamExists: false
      action:
        - notify:
            channel: "#platform-orphans"
        - assignTo: platform-team

  cleanupPolicy:
    # After 60 days of no activity and notification
    gracePeriod: 60d
    actions:
      - backup
      - delete
    requireApproval: true
```

---

## War Story: The $2M Wake-Up Call

> **"Self-Service Without Guardrails"**
>
> A fast-growing startup gave developers full AWS access to move quickly. Their platform team's motto: "Trust the developers."
>
> Six months later:
> - 847 EC2 instances running (they needed ~200)
> - 156 RDS databases (many duplicates, test instances never deleted)
> - $2.1M monthly cloud bill (budget was $400K)
> - No one knew what half the resources were for
>
> The forensics revealed:
> - Test environments never cleaned up: "I'll delete it later"
> - Over-provisioned "just in case": "Make it big, we might need it"
> - Duplicate resources: "Easier to create new than find existing"
> - Shadow resources: "I needed it for a demo"
>
> **The Fix (6 months to implement):**
>
> 1. **Resource tagging required**: No tag, no provision
>    ```yaml
>    required_tags:
>      - team
>      - project
>      - environment
>      - cost-center
>      - expiry-date  # For non-prod
>    ```
>
> 2. **Auto-expiry for non-production**: Default 30-day TTL
>    ```yaml
>    non_prod_defaults:
>      ttl: 30d
>      extendable: true
>      max_extensions: 3
>    ```
>
> 3. **Right-sizing recommendations**: Weekly reports
>    ```
>    Resource: web-server-prod
>    Current: m5.2xlarge ($280/mo)
>    Recommended: m5.large ($70/mo)
>    Utilization: CPU 12%, Memory 23%
>    Potential savings: $210/mo
>    ```
>
> 4. **Budget alerts with teeth**: Soft limits warn, hard limits block
>
> 5. **Orphan hunting**: Weekly sweep, 60-day grace period
>
> **Results after 1 year:**
> - Cloud bill: $580K/month (down from $2.1M)
> - Resource count: 312 (down from 847 EC2 alone)
> - Developer satisfaction: Actually higher (less confusion)
>
> **Lesson**: Self-service without guardrails isn't freedom—it's chaos that eventually requires painful cleanup.

---

## Implementation Approaches

### Approach 1: Crossplane (Kubernetes-Native)

```yaml
# Composite Resource Definition
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xdatabases.platform.example.com
spec:
  group: platform.example.com
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
              required:
                - type
                - size
              properties:
                type:
                  type: string
                  enum: [postgresql, mysql, mongodb]
                size:
                  type: string
                  enum: [small, medium, large]
                version:
                  type: string
                backup:
                  type: object
                  properties:
                    enabled:
                      type: boolean
                      default: true
                    retentionDays:
                      type: integer
                      default: 7
            status:
              type: object
              properties:
                host:
                  type: string
                port:
                  type: integer
                secretName:
                  type: string
                status:
                  type: string

---
# User just creates this
apiVersion: platform.example.com/v1alpha1
kind: Database
metadata:
  name: orders-db
  namespace: team-orders
spec:
  type: postgresql
  size: medium
```

### Approach 2: Terraform with Atlantis

```hcl
# modules/database/main.tf
variable "name" {
  type = string
}

variable "size" {
  type = string
  validation {
    condition     = contains(["small", "medium", "large"], var.size)
    error_message = "Size must be small, medium, or large."
  }
}

variable "environment" {
  type = string
}

locals {
  size_map = {
    small  = "db.t3.micro"
    medium = "db.t3.medium"
    large  = "db.t3.large"
  }
}

resource "aws_db_instance" "main" {
  identifier     = var.name
  instance_class = local.size_map[var.size]
  engine         = "postgres"
  engine_version = "15"

  # Security defaults
  storage_encrypted   = true
  deletion_protection = var.environment == "production"

  # Networking (from environment)
  db_subnet_group_name   = data.aws_db_subnet_group.main.name
  vpc_security_group_ids = [data.aws_security_group.database.id]

  tags = {
    Name        = var.name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

```yaml
# atlantis.yaml - GitOps workflow
version: 3
projects:
  - name: team-orders-database
    dir: infrastructure/team-orders
    workflow: database
    autoplan:
      when_modified: ["*.tf"]
      enabled: true

workflows:
  database:
    plan:
      steps:
        - run: terraform init
        - run: |
            # Policy check before plan
            conftest test . --policy ../policies/
        - plan

    apply:
      steps:
        - run: |
            # Final validation
            terraform validate
        - apply
```

### Approach 3: Internal Platform API

```python
# platform_api/resources/database.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal

router = APIRouter()

class DatabaseRequest(BaseModel):
    name: str
    type: Literal["postgresql", "mysql", "mongodb"]
    size: Literal["small", "medium", "large"]
    environment: Literal["development", "staging", "production"]
    team: str

class DatabaseResponse(BaseModel):
    id: str
    status: str
    host: str | None
    port: int | None
    secret_name: str | None

@router.post("/databases", response_model=DatabaseResponse)
async def create_database(
    request: DatabaseRequest,
    user = Depends(get_current_user),
    policy_engine = Depends(get_policy_engine),
    provisioner = Depends(get_provisioner)
):
    # 1. Validate against policies
    policy_result = await policy_engine.evaluate(
        action="create",
        resource_type="database",
        request=request,
        user=user
    )
    if not policy_result.allowed:
        raise HTTPException(403, policy_result.reason)

    # 2. Check quotas
    quota_result = await check_quota(user.team, "database")
    if quota_result.exceeded:
        raise HTTPException(429, f"Quota exceeded: {quota_result.message}")

    # 3. Determine if approval needed
    approval = await get_approval_requirement(request, user)
    if approval.required:
        return await create_pending_request(request, approval)

    # 4. Provision
    result = await provisioner.create_database(request)

    # 5. Audit log
    await audit_log.record(
        action="database.create",
        user=user.id,
        resource=result.id,
        request=request.dict()
    )

    return result
```

---

## Common Mistakes

| Mistake | Why It Happens | Better Approach |
|---------|---------------|-----------------|
| **No guardrails** | Fear of slowing down developers | Start with lightweight guardrails, add more based on incidents |
| **Too many guardrails** | Overcorrection from past incidents | Focus on high-impact policies, automate the rest |
| **Manual approvals for everything** | Risk aversion | Risk-based approval tiers |
| **No cost visibility** | "Cloud is infinite" mindset | Show costs at request time, enable team accountability |
| **Day 0 only** | Provisioning is the "fun" part | Day 2 operations are where value is realized |
| **One size fits all** | Simplicity over usability | Different abstractions for different needs |
| **No feedback loop** | Build it and move on | Track usage, gather feedback, iterate |
| **Ignoring existing IaC** | Greenfield thinking | Support existing Terraform/Pulumi alongside new abstractions |

---

## Quiz

Test your understanding of self-service infrastructure:

**Question 1**: What are the three competing concerns that self-service infrastructure must balance?

<details>
<summary>Show Answer</summary>

The **Self-Service Triangle**:
1. **Speed** - Fast provisioning for developer velocity
2. **Control** - Governance, compliance, and cost management
3. **Autonomy** - Developer freedom and independence

Too much of any one creates problems:
- Speed without control → cost explosion, security gaps
- Control without autonomy → ticket-based systems return
- Autonomy without governance → chaos and inconsistency
</details>

**Question 2**: Why is Day 2 operations critical for self-service systems?

<details>
<summary>Show Answer</summary>

Day 2 operations (scaling, upgrades, troubleshooting, decommissioning) represent where infrastructure spends most of its lifecycle. If only provisioning is self-service:
- Developers file tickets for routine operations
- Resources become orphaned (no self-service delete)
- Version upgrades are delayed or blocked
- The promised velocity gains disappear

Complete self-service means covering the full lifecycle: provision, configure, operate, and decommission.
</details>

**Question 3**: An organization has $2M monthly cloud spend with significant waste from orphaned and over-provisioned resources. What guardrails would help?

<details>
<summary>Show Answer</summary>

Recommended guardrails:
1. **Required tagging** - team, project, environment, cost-center, expiry-date
2. **Auto-expiry for non-production** - Default TTL with extension limits
3. **Right-sizing recommendations** - Weekly reports comparing provisioned vs. actual usage
4. **Budget alerts** - Soft limits warn, hard limits block
5. **Orphan detection** - Automated scanning for unused resources
6. **Cost visibility at request time** - Show estimated cost before provisioning

The key is making costs visible and creating accountability without blocking legitimate work.
</details>

**Question 4**: What's the difference between preventive and detective guardrails?

<details>
<summary>Show Answer</summary>

**Preventive guardrails** stop problems before they happen:
- Admission control (block non-compliant requests)
- Policy enforcement at request time
- Quota limits

**Detective guardrails** find problems after the fact:
- Compliance scans
- Drift detection
- Cost alerts
- Security audits

Both are needed: preventive for known risks, detective for emerging issues and policy violations that slip through.
</details>

**Question 5**: Why use infrastructure abstractions instead of exposing raw cloud APIs?

<details>
<summary>Show Answer</summary>

Infrastructure abstractions provide:
1. **Simplicity** - Hide 50+ cloud API parameters behind a few intent-based options
2. **Consistency** - Enforce standards (encryption, tagging, networking) automatically
3. **Safety** - Prevent misconfigurations through validated compositions
4. **Portability** - Same interface across cloud providers
5. **Governance** - Central point for policy enforcement

The trade-off is flexibility. Good abstractions provide escape hatches for legitimate edge cases while keeping the common path simple.
</details>

---

## Hands-On Exercise

### Scenario

Your organization currently has a ticket-based system for database provisioning:
- Average time to provision: 5 days
- 60% of requests are for PostgreSQL in development
- Common complaints: "too slow", "don't know the status", "can't resize easily"
- Security finding: 30% of databases missing encryption

### Part 1: Design the Abstraction (15 minutes)

Design a simplified database API:

```yaml
# What fields does the developer specify?
apiVersion: platform.example.com/v1alpha1
kind: Database
metadata:
  name: ???
spec:
  # Required fields:
  ???

  # Optional fields with defaults:
  ???
```

Document your decisions:
- What options do you expose?
- What do you hide/default?
- How do you handle the encryption requirement?

### Part 2: Define Guardrails (15 minutes)

Create policies for your self-service database:

```yaml
# Policy: What checks run before provisioning?
validation_policies:
  - name: ???
    rule: ???

# Policy: What requires approval?
approval_policies:
  - name: ???
    condition: ???
    approvers: ???

# Policy: What limits apply?
quota_policies:
  - name: ???
    limit: ???
```

### Part 3: Lifecycle Operations (10 minutes)

Design the Day 2 self-service operations:

```bash
# What commands should developers have?
$ platform database ???

# Example operations:
# - Scale to larger size
# - Create backup
# - Restore from backup
# - Check status
# - Delete (with safeguards)
```

### Success Criteria

Your design should:
- [ ] Reduce provisioning time from 5 days to <15 minutes for standard requests
- [ ] Enforce encryption on all databases (the 30% gap is closed)
- [ ] Allow developers to manage their databases independently
- [ ] Provide appropriate controls for production environments
- [ ] Enable cost visibility and accountability

---

## Summary

Self-service infrastructure transforms how organizations deliver:

```
KEY PRINCIPLES:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  1. BALANCE the triangle: Speed, Control, Autonomy              │
│     None can dominate without consequences                      │
│                                                                  │
│  2. ABSTRACT for intent, not implementation                     │
│     Developers say what they need, not how to build it          │
│                                                                  │
│  3. GUARDRAILS enable, not restrict                             │
│     Make the right thing easy, the wrong thing hard             │
│                                                                  │
│  4. FULL LIFECYCLE, not just Day 0                              │
│     Provisioning is just the beginning                          │
│                                                                  │
│  5. VISIBILITY creates accountability                           │
│     Show costs, usage, and ownership                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The goal isn't to give developers AWS root access—it's to give them what they need to be productive while keeping the organization safe, compliant, and cost-effective.

---

## Further Reading

### Tools
- [Crossplane](https://crossplane.io/) - Kubernetes-native infrastructure orchestration
- [Backstage](https://backstage.io/) - Developer portal with self-service templates
- [Atlantis](https://www.runatlantis.io/) - GitOps for Terraform
- [Open Policy Agent](https://www.openpolicyagent.org/) - Policy as code

### Articles
- [Infrastructure Self-Service at Scale](https://www.hashicorp.com/resources/self-service-infrastructure-terraform)
- [Crossplane: Infrastructure as Code the Kubernetes Way](https://crossplane.io/docs/)
- [Platform Engineering and Self-Service](https://platformengineering.org/)

### Books
- *Infrastructure as Code* - Kief Morris
- *Cloud Native Infrastructure* - Justin Garrison & Kris Nova

---

## Next Module

Continue to [Module 2.6: Platform Maturity](../module-2.6-platform-maturity/) to learn how to assess your platform's maturity level and plan a roadmap for improvement.

---

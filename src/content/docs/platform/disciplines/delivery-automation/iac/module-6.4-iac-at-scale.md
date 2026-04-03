---
title: "Module 6.4: Infrastructure as Code at Scale"
slug: platform/disciplines/delivery-automation/iac/module-6.4-iac-at-scale
sidebar:
  order: 5
---
## Complexity: [COMPLEX]
## Time to Complete: 55 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](../module-6.1-iac-fundamentals/) - Core concepts
- [Module 6.2: IaC Testing](../module-6.2-iac-testing/) - Testing strategies
- [Module 6.3: IaC Security](../module-6.3-iac-security/) - Security practices
- Basic understanding of organizational structures

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design IaC module registries and versioning strategies that support hundreds of consuming teams**
- **Implement state management patterns — workspaces, accounts, backends — for large multi-team environments**
- **Build dependency management workflows that prevent breaking changes across shared IaC modules**
- **Evaluate monorepo versus multi-repo strategies for IaC at organizational scale**

## Why This Module Matters

**The Great Terraform Migration Crisis**

The platform team at a rapidly growing fintech company had what seemed like a great problem: they'd grown from 3 to 47 engineering teams in two years. Each team had been given autonomy to manage their own infrastructure, and they'd all chosen Terraform. The company now had over 2,400 Terraform configurations spread across 180 repositories.

Then came the compliance audit.

The auditors needed to verify that all databases were encrypted, all S3 buckets had versioning enabled, and all security groups followed the corporate baseline. The platform team spent three weeks writing scripts to scan the configurations. They found that 23% of databases weren't encrypted, 41% of S3 buckets lacked versioning, and security group configurations ranged from locked-down to completely open.

Fixing these issues took 4 months. During that time, teams couldn't ship new features because every infrastructure change required security review. The total cost in delayed features, overtime, and audit fees: $8.7 million.

This module teaches you how to scale infrastructure as code without losing control—because managing IaC for 3 teams is fundamentally different from managing it for 300.

---

## The Scale Challenge

As organizations grow, IaC complexity increases exponentially.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IAC COMPLEXITY GROWTH                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Complexity                                                         │
│      ▲                                                              │
│      │                                                      ████    │
│      │                                                 ████████     │
│      │                                            ████████████      │
│      │                                       █████████████████      │
│      │                                  ██████████████████████      │
│      │                             ███████████████████████████      │
│      │                        ████████████████████████████████      │
│      │                   █████████████████████████████████████      │
│      │              ██████████████████████████████████████████      │
│      │         ███████████████████████████████████████████████      │
│      │    ████████████████████████████████████████████████████      │
│      └─────────────────────────────────────────────────────────►    │
│           3       10      25      50     100     200+   Teams       │
│                                                                     │
│  Scale Challenges:                                                  │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ • State file conflicts and corruption                       │    │
│  │ • Inconsistent module versions across teams                 │    │
│  │ • Divergent security and compliance standards               │    │
│  │ • Duplicate infrastructure definitions                      │    │
│  │ • Long plan/apply times (10+ minutes)                       │    │
│  │ • Difficulty tracking who owns what                         │    │
│  │ • Cascading breaking changes from module updates            │    │
│  │ • Knowledge silos and tribal knowledge                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Repository Strategies

### Monorepo: Single Repository for All Infrastructure

```
infrastructure/
├── modules/                    # Shared, versioned modules
│   ├── vpc/
│   │   ├── v1.0.0/
│   │   ├── v1.1.0/
│   │   └── v2.0.0/
│   ├── eks/
│   ├── rds/
│   └── s3/
├── environments/               # Environment-specific configs
│   ├── shared/                # Cross-environment resources
│   │   ├── networking/
│   │   └── security/
│   ├── dev/
│   │   ├── team-alpha/
│   │   ├── team-beta/
│   │   └── team-gamma/
│   ├── staging/
│   │   └── ...
│   └── production/
│       ├── us-east-1/
│       ├── us-west-2/
│       └── eu-west-1/
├── policies/                   # OPA/Sentinel policies
├── tests/                      # Integration tests
├── .github/
│   └── workflows/
│       ├── module-release.yml
│       ├── policy-check.yml
│       └── deploy.yml
└── CODEOWNERS                  # Per-directory ownership
```

**Advantages**:
- Single source of truth
- Easy cross-team collaboration
- Consistent tooling and CI/CD
- Atomic changes across environments

**Disadvantages**:
- Requires strong access controls (CODEOWNERS)
- Large repository size over time
- All teams affected by CI/CD issues
- Permission boundaries harder to enforce

### Polyrepo: Separate Repository per Team/Project

```
org-infrastructure/
├── terraform-modules/          # Central modules repo
├── platform-core/              # Platform team's infra
├── team-alpha-infra/           # Each team owns their repo
├── team-beta-infra/
├── team-gamma-infra/
└── compliance-policies/        # Central policy repo
```

**Advantages**:
- Clear ownership boundaries
- Independent release cycles
- Simpler permissions (repo-level)
- Smaller, focused repositories

**Disadvantages**:
- Module version fragmentation
- Inconsistent practices
- Harder to enforce standards
- Duplication of common patterns

### Hybrid: Best of Both Worlds

```
# Centralized
platform-infrastructure/
├── modules/                    # Blessed modules
├── global/                     # Org-wide resources
└── policies/                   # Mandatory policies

# Team-owned (using central modules)
team-alpha-infrastructure/
└── environments/
    ├── dev/
    │   └── main.tf            # Uses central modules
    └── production/
        └── main.tf

# Example team configuration
module "vpc" {
  source  = "git::https://github.com/org/platform-infrastructure//modules/vpc?ref=v2.1.0"
  # ...
}
```

---

## Module Registry and Versioning

### Private Module Registry

Terraform Cloud/Enterprise or self-hosted registry for internal modules:

```hcl
# terraform.tf - Using private registry
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Using module from private registry
module "vpc" {
  source  = "app.terraform.io/company/vpc/aws"
  version = "2.1.0"

  environment = var.environment
  cidr_block  = "10.0.0.0/16"
}

module "eks" {
  source  = "app.terraform.io/company/eks/aws"
  version = "~> 3.0"  # Allow minor/patch updates

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}
```

### Semantic Versioning for Modules

```
version = "MAJOR.MINOR.PATCH"

MAJOR: Breaking changes (interface changes, removed features)
MINOR: New features (backward compatible)
PATCH: Bug fixes (backward compatible)
```

```hcl
# modules/vpc/CHANGELOG.md
# Changelog

## [3.0.0] - 2024-01-15
### Breaking Changes
- Removed `enable_nat_gateway` variable, NAT is now always enabled
- Changed output `subnet_ids` to `private_subnet_ids` and `public_subnet_ids`
- Minimum Terraform version now 1.5.0

### Added
- Support for IPv6
- Transit gateway attachment option

## [2.3.0] - 2024-01-01
### Added
- VPC flow logs enabled by default
- New `log_retention_days` variable

## [2.2.1] - 2023-12-15
### Fixed
- Subnet CIDR calculation for large VPCs
```

### Version Constraints

```hcl
# Exact version - most predictable
version = "2.1.0"

# Pessimistic constraint - allow patches
version = "~> 2.1.0"  # Allows 2.1.x, not 2.2.0

# Allow minor updates
version = "~> 2.1"    # Allows 2.x.x, not 3.0.0

# Range constraint
version = ">= 2.0.0, < 3.0.0"

# Best practice: Use pessimistic for stability
module "vpc" {
  source  = "app.terraform.io/company/vpc/aws"
  version = "~> 2.1.0"  # Get patches, avoid breaking changes
}
```

---

## State Management at Scale

### State File Organization

```
┌─────────────────────────────────────────────────────────────────┐
│                   STATE FILE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Approach 1: Monolithic State (Bad for Scale)                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  terraform.tfstate                                       │   │
│  │  ├── All VPCs                                            │   │
│  │  ├── All EKS clusters                                    │   │
│  │  ├── All databases                                       │   │
│  │  └── 50,000+ resources                                   │   │
│  │                                                          │   │
│  │  Problems:                                               │   │
│  │  • Plan takes 10+ minutes                                │   │
│  │  • Single team blocks all changes                        │   │
│  │  • Corruption affects everything                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Approach 2: State per Environment (Better)                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  s3://state/                                            │    │
│  │  ├── dev/terraform.tfstate                              │    │
│  │  ├── staging/terraform.tfstate                          │    │
│  │  └── production/terraform.tfstate                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Approach 3: State per Component (Best for Scale)               │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  s3://state/production/                                 │    │
│  │  ├── networking/terraform.tfstate      (VPC, subnets)   │    │
│  │  ├── security/terraform.tfstate        (IAM, KMS)       │    │
│  │  ├── eks/terraform.tfstate             (EKS cluster)    │    │
│  │  ├── databases/terraform.tfstate       (RDS, DynamoDB)  │    │
│  │  ├── team-alpha/terraform.tfstate      (Team workloads) │    │
│  │  ├── team-beta/terraform.tfstate                        │    │
│  │  └── team-gamma/terraform.tfstate                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Workspaces vs. Directories

```hcl
# Approach A: Terraform Workspaces
# Same code, different state per workspace

# Select workspace
terraform workspace select production

# Backend uses workspace name
terraform {
  backend "s3" {
    bucket = "terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
    # State file: terraform-state/env:/production/infrastructure/terraform.tfstate
  }
}

# Reference workspace in code
locals {
  environment = terraform.workspace

  instance_type = {
    dev        = "t3.small"
    staging    = "t3.medium"
    production = "t3.large"
  }[terraform.workspace]
}
```

```bash
# Approach B: Directory Structure (Recommended for Scale)
environments/
├── dev/
│   ├── backend.tf          # Points to dev state
│   ├── main.tf
│   └── terraform.tfvars    # Dev-specific values
├── staging/
│   ├── backend.tf          # Points to staging state
│   ├── main.tf
│   └── terraform.tfvars
└── production/
    ├── backend.tf          # Points to production state
    ├── main.tf
    └── terraform.tfvars
```

Directory approach advantages:
- Clear separation of environments
- Different providers/versions per environment
- Easier to understand state location
- No workspace switching mistakes

### Cross-State References

```hcl
# networking/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

# eks/main.tf - Reference networking state
data "terraform_remote_state" "networking" {
  backend = "s3"
  config = {
    bucket = "terraform-state"
    key    = "production/networking/terraform.tfstate"
    region = "us-east-1"
  }
}

module "eks" {
  source = "../modules/eks"

  vpc_id     = data.terraform_remote_state.networking.outputs.vpc_id
  subnet_ids = data.terraform_remote_state.networking.outputs.private_subnet_ids
}
```

### Terragrunt for DRY Configuration

```hcl
# terragrunt.hcl (root)
remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = "company-terraform-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}
EOF
}
```

```hcl
# production/eks/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../modules/eks"
}

dependency "vpc" {
  config_path = "../networking"
}

inputs = {
  environment = "production"
  vpc_id      = dependency.vpc.outputs.vpc_id
  subnet_ids  = dependency.vpc.outputs.private_subnet_ids
}
```

---

## Policy as Code at Scale

### OPA/Gatekeeper for Kubernetes

```yaml
# Constraint Template
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels

        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }
```

```yaml
# Constraint
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-labels
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace", "Pod"]
  parameters:
    labels:
      - "team"
      - "environment"
      - "cost-center"
```

### Sentinel for Terraform Enterprise

```python
# policy/require-encryption.sentinel
import "tfplan/v2" as tfplan

# Get all S3 buckets
s3_buckets = filter tfplan.resource_changes as _, rc {
    rc.type is "aws_s3_bucket" and
    rc.mode is "managed" and
    (rc.change.actions contains "create" or
     rc.change.actions contains "update")
}

# Check encryption configuration exists
require_encryption = rule {
    all s3_buckets as _, bucket {
        bucket.change.after.server_side_encryption_configuration is not null
    }
}

# Main rule
main = rule {
    require_encryption
}
```

### Conftest for CI/CD

```rego
# policy/terraform/required_tags.rego
package terraform.required_tags

import future.keywords.in

required_tags := ["Environment", "Team", "CostCenter"]

deny[msg] {
    resource := input.resource_changes[_]
    resource.change.actions[_] in ["create", "update"]

    # Resources that should have tags
    taggable := ["aws_instance", "aws_s3_bucket", "aws_rds_cluster", "aws_vpc"]
    resource.type in taggable

    tags := object.get(resource.change.after, "tags", {})

    missing := [tag |
        tag := required_tags[_]
        not tags[tag]
    ]

    count(missing) > 0
    msg := sprintf("%s is missing required tags: %v", [resource.address, missing])
}
```

```yaml
# .github/workflows/policy-check.yml
name: Policy Check

on:
  pull_request:
    paths: ['terraform/**']

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Generate Plan
        run: |
          cd terraform/environments/production
          terraform init -backend=false
          terraform plan -out=tfplan
          terraform show -json tfplan > tfplan.json

      - name: Install Conftest
        run: |
          wget -q https://github.com/open-policy-agent/conftest/releases/download/v0.45.0/conftest_0.45.0_Linux_x86_64.tar.gz
          tar xzf conftest_0.45.0_Linux_x86_64.tar.gz
          sudo mv conftest /usr/local/bin/

      - name: Run Policy Tests
        run: |
          conftest test terraform/environments/production/tfplan.json \
            --policy policy/terraform/ \
            --output table
```

---

## Self-Service Infrastructure

### Platform Engineering Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                 SELF-SERVICE INFRASTRUCTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Traditional Model:                                             │
│  ┌─────────┐    Ticket    ┌──────────┐    Manual    ┌───────┐  │
│  │Developer│ ──────────► │  Ops/SRE  │ ──────────► │Infra   │  │
│  └─────────┘   (days)    └──────────┘   (days)    └───────┘  │
│                                                                 │
│  Self-Service Model:                                            │
│  ┌─────────┐    PR/Form   ┌──────────┐  Automated   ┌───────┐  │
│  │Developer│ ──────────► │ Platform  │ ──────────► │Infra   │  │
│  └─────────┘  (minutes)  │    API    │  (minutes)  └───────┘  │
│                          └──────────┘                          │
│                               │                                 │
│                    ┌──────────┴──────────┐                     │
│                    │                     │                     │
│               Policy Gates         Module Library              │
│               (guardrails)         (golden paths)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Service Catalog with Backstage

```yaml
# catalog-info.yaml - Backstage template
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: kubernetes-microservice
  title: Kubernetes Microservice
  description: Create a new microservice with EKS deployment
  tags:
    - kubernetes
    - microservice
    - recommended
spec:
  owner: platform-team
  type: service

  parameters:
    - title: Service Information
      required:
        - name
        - team
      properties:
        name:
          title: Service Name
          type: string
          pattern: '^[a-z][a-z0-9-]*$'
        team:
          title: Owning Team
          type: string
          ui:field: OwnerPicker
        description:
          title: Description
          type: string

    - title: Infrastructure Options
      properties:
        environment:
          title: Environment
          type: string
          enum: ['dev', 'staging', 'production']
          default: 'dev'
        instanceSize:
          title: Instance Size
          type: string
          enum: ['small', 'medium', 'large']
          default: 'small'
          description: |
            small: 0.5 CPU, 512MB RAM
            medium: 1 CPU, 1GB RAM
            large: 2 CPU, 2GB RAM
        needsDatabase:
          title: Needs Database?
          type: boolean
          default: false
        databaseType:
          title: Database Type
          type: string
          enum: ['postgresql', 'mysql']
          ui:disabled: '{{ not parameters.needsDatabase }}'

  steps:
    - id: fetch-template
      name: Fetch Template
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          team: ${{ parameters.team }}
          environment: ${{ parameters.environment }}

    - id: create-terraform
      name: Create Infrastructure
      action: terraform:apply
      input:
        workspace: ${{ parameters.environment }}
        variables:
          service_name: ${{ parameters.name }}
          instance_size: ${{ parameters.instanceSize }}
          enable_database: ${{ parameters.needsDatabase }}
          database_type: ${{ parameters.databaseType }}

    - id: create-repo
      name: Create Repository
      action: publish:github
      input:
        repoUrl: github.com?owner=company&repo=${{ parameters.name }}
        defaultBranch: main

  output:
    links:
      - title: Repository
        url: ${{ steps.create-repo.output.remoteUrl }}
      - title: Infrastructure
        url: https://terraform.company.com/workspaces/${{ parameters.name }}
```

### Terraform Module as Service

```hcl
# modules/microservice/main.tf
# Complete microservice infrastructure in one module

variable "service_name" {
  description = "Name of the microservice"
  type        = string
}

variable "team" {
  description = "Owning team"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "instance_size" {
  description = "Resource allocation tier"
  type        = string
  default     = "small"

  validation {
    condition     = contains(["small", "medium", "large"], var.instance_size)
    error_message = "Instance size must be small, medium, or large"
  }
}

variable "enable_database" {
  description = "Create associated database"
  type        = bool
  default     = false
}

locals {
  # Size mappings
  sizes = {
    small = {
      cpu    = "500m"
      memory = "512Mi"
      replicas = 2
    }
    medium = {
      cpu    = "1000m"
      memory = "1Gi"
      replicas = 3
    }
    large = {
      cpu    = "2000m"
      memory = "2Gi"
      replicas = 5
    }
  }

  common_tags = {
    Service     = var.service_name
    Team        = var.team
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ECR repository for container images
resource "aws_ecr_repository" "service" {
  name                 = var.service_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

# Kubernetes namespace
resource "kubernetes_namespace" "service" {
  metadata {
    name = var.service_name
    labels = {
      "team"        = var.team
      "environment" = var.environment
    }
  }
}

# Resource quota for namespace
resource "kubernetes_resource_quota" "service" {
  metadata {
    name      = "${var.service_name}-quota"
    namespace = kubernetes_namespace.service.metadata[0].name
  }

  spec {
    hard = {
      "requests.cpu"    = "${local.sizes[var.instance_size].cpu * local.sizes[var.instance_size].replicas * 2}"
      "requests.memory" = "${local.sizes[var.instance_size].memory * local.sizes[var.instance_size].replicas * 2}"
      "limits.cpu"      = "${local.sizes[var.instance_size].cpu * local.sizes[var.instance_size].replicas * 4}"
      "limits.memory"   = "${local.sizes[var.instance_size].memory * local.sizes[var.instance_size].replicas * 4}"
      "pods"            = "${local.sizes[var.instance_size].replicas * 4}"
    }
  }
}

# Network policy
resource "kubernetes_network_policy" "service" {
  metadata {
    name      = "${var.service_name}-policy"
    namespace = kubernetes_namespace.service.metadata[0].name
  }

  spec {
    pod_selector {}

    ingress {
      from {
        namespace_selector {
          match_labels = {
            "name" = "ingress-nginx"
          }
        }
      }
    }

    egress {
      to {
        namespace_selector {
          match_labels = {
            "environment" = var.environment
          }
        }
      }
    }

    policy_types = ["Ingress", "Egress"]
  }
}

# Optional database
resource "aws_db_instance" "service" {
  count = var.enable_database ? 1 : 0

  identifier     = "${var.service_name}-${var.environment}"
  engine         = "postgres"
  engine_version = "15"
  instance_class = var.environment == "production" ? "db.t3.medium" : "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = var.environment == "production" ? 100 : 50
  storage_encrypted     = true

  db_name  = replace(var.service_name, "-", "_")
  username = "app"
  password = random_password.db[0].result

  vpc_security_group_ids = [aws_security_group.db[0].id]
  db_subnet_group_name   = data.aws_db_subnet_group.main.name

  backup_retention_period = var.environment == "production" ? 30 : 7
  skip_final_snapshot     = var.environment != "production"

  tags = local.common_tags
}

# Outputs for team consumption
output "ecr_repository_url" {
  description = "ECR repository URL for pushing images"
  value       = aws_ecr_repository.service.repository_url
}

output "namespace" {
  description = "Kubernetes namespace"
  value       = kubernetes_namespace.service.metadata[0].name
}

output "database_endpoint" {
  description = "Database endpoint (if enabled)"
  value       = var.enable_database ? aws_db_instance.service[0].endpoint : null
}
```

---

## Organizational Patterns

### Team Topologies for IaC

```
┌─────────────────────────────────────────────────────────────────┐
│                    IaC TEAM TOPOLOGIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Platform Team (Enabling)                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Responsibilities:                                        │   │
│  │ • Build and maintain module library                      │   │
│  │ • Define and enforce policies                            │   │
│  │ • Manage shared infrastructure (networking, security)    │   │
│  │ • Provide self-service capabilities                      │   │
│  │ • Train and support stream-aligned teams                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                      │
│          ┌───────────────┼───────────────┐                     │
│          ▼               ▼               ▼                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │Stream-Aligned│ │Stream-Aligned│ │Stream-Aligned│              │
│  │  Team Alpha  │ │  Team Beta   │ │  Team Gamma  │              │
│  ├─────────────┤ ├─────────────┤ ├─────────────┤               │
│  │ Own service │ │ Own service │ │ Own service │               │
│  │ Use modules │ │ Use modules │ │ Use modules │               │
│  │ Self-service│ │ Self-service│ │ Self-service│               │
│  │ deployments │ │ deployments │ │ deployments │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
│  Interaction Modes:                                             │
│  • Collaboration: Platform helps team with complex needs        │
│  • X-as-a-Service: Teams consume modules independently          │
│  • Facilitation: Platform trains teams on IaC practices         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Ownership Model

```yaml
# CODEOWNERS - Define ownership at scale
# Platform team owns shared infrastructure
/modules/                     @platform-team
/environments/*/networking/   @platform-team
/environments/*/security/     @platform-team
/policies/                    @platform-team @security-team

# Teams own their own infrastructure
/environments/*/team-alpha/   @team-alpha
/environments/*/team-beta/    @team-beta
/environments/*/team-gamma/   @team-gamma

# Security review required for production
/environments/production/     @platform-team @security-team
```

```hcl
# Enforce ownership via tags
variable "team" {
  description = "Team that owns this infrastructure"
  type        = string

  validation {
    condition = contains([
      "platform",
      "team-alpha",
      "team-beta",
      "team-gamma"
    ], var.team)
    error_message = "Team must be a valid team identifier"
  }
}

resource "aws_instance" "app" {
  # ...

  tags = {
    Team        = var.team
    ManagedBy   = "terraform"
    Repository  = "github.com/company/infrastructure"
    CostCenter  = local.team_cost_centers[var.team]
  }
}
```

---

## War Story: The 47-Team Consolidation

**Company**: Fast-growing fintech
**Challenge**: 47 teams, 180 repositories, 2,400 Terraform configurations

**The Problem**:
```
Before Consolidation:
├── 180 repositories with Terraform
├── 47 different VPC designs
├── 23 different RDS configurations
├── 12 different EKS setups
├── 0 standardization
├── 41% of S3 buckets without versioning
├── 23% of databases unencrypted
└── 4-month compliance remediation
```

**The Solution**:

Phase 1: Assessment (2 weeks)
```bash
# Inventory script across all repos
for repo in $(gh repo list company --json name -q '.[].name'); do
  gh repo clone company/$repo temp-repo
  find temp-repo -name "*.tf" -exec cat {} \; | \
    grep -E "^resource|^module" >> inventory.txt
  rm -rf temp-repo
done

# Result: 2,400 configurations, 847 unique resource types
```

Phase 2: Module Library (6 weeks)
```
Consolidated to 15 blessed modules:
├── vpc (replaced 47 variants)
├── eks (replaced 12 variants)
├── rds-postgresql
├── rds-mysql
├── s3-bucket
├── lambda-function
├── api-gateway
├── cloudfront
├── elasticache
├── sns-sqs
├── ecr
├── iam-role
├── security-group
├── route53
└── acm-certificate
```

Phase 3: Migration (12 weeks)
```hcl
# Migration pattern: Import existing, switch to module
# Step 1: Document existing
terraform state list > existing-resources.txt

# Step 2: Create new config with module
module "vpc" {
  source  = "app.terraform.io/company/vpc/aws"
  version = "1.0.0"
  # Match existing settings
}

# Step 3: Import existing resources
terraform import module.vpc.aws_vpc.main vpc-12345

# Step 4: Plan and verify no changes
terraform plan  # Should show no changes

# Step 5: Remove old config, keep module
```

Phase 4: Policy Enforcement (4 weeks)
```python
# Sentinel policy requiring module usage
import "tfplan/v2" as tfplan

# Modules that must come from registry
required_modules = [
    "vpc",
    "eks",
    "rds-postgresql",
    "rds-mysql",
    "s3-bucket"
]

# Check module sources
module_sources = rule {
    all tfplan.module_calls as _, mc {
        mc.source_type is "registry" or
        mc.source_type is "remote"
    }
}

main = rule {
    module_sources
}
```

**Results After 6 Months**:
```
After Consolidation:
├── 15 blessed modules (from 847 variants)
├── 100% compliance with security baseline
├── 90% reduction in infrastructure tickets
├── Plan time: 45 seconds (from 8+ minutes)
├── Mean time to provision: 15 minutes (from 3 days)
├── $2.1M/year saved in duplicate infrastructure
└── 0 compliance findings in next audit
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Monolithic state files | Slow plans, broad blast radius | Split by component/team |
| No module versioning | Breaking changes affect everyone | Semantic versioning, registry |
| Copy-paste modules | Drift, inconsistency | Central module library |
| No policy enforcement | Security/compliance issues | OPA/Sentinel in CI/CD |
| Teams reinvent wheels | Wasted effort, inconsistency | Self-service with golden paths |
| No ownership model | Nobody responsible, nobody fixes | CODEOWNERS, team tags |
| All-or-nothing permissions | Too broad or too restrictive | Environment-scoped IAM |
| Manual state management | Corruption, lost state | Remote backend with locking |

---

## Quiz

<details>
<summary>1. What are the three main repository strategies for IaC at scale?</summary>

**Answer**:
1. **Monorepo**: All infrastructure in one repository
   - Pros: Single source of truth, atomic changes, consistent tooling
   - Cons: Large repo, requires strong access controls

2. **Polyrepo**: Separate repository per team/project
   - Pros: Clear ownership, independent releases, simpler permissions
   - Cons: Module fragmentation, inconsistent practices

3. **Hybrid**: Central modules + team-owned configurations
   - Pros: Shared standards with team autonomy
   - Cons: More complex to set up
</details>

<details>
<summary>2. Why should state files be split by component rather than having one large state file?</summary>

**Answer**: Splitting state files:
- **Faster operations**: Plan/apply only processes relevant resources
- **Reduced blast radius**: Errors affect only one component
- **Parallel changes**: Teams can work simultaneously
- **Clearer ownership**: Each state file has defined owners
- **Easier debugging**: Smaller state files are easier to inspect
- **Less lock contention**: Different teams don't block each other

A 50,000-resource state file might take 10+ minutes to plan; split into 50 files of 1,000 resources each, plans complete in seconds.
</details>

<details>
<summary>3. What is the purpose of semantic versioning for Terraform modules?</summary>

**Answer**: Semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes - consumers must update their code
- **MINOR**: New features - backward compatible additions
- **PATCH**: Bug fixes - backward compatible fixes

This allows consumers to:
- Pin exact versions for stability (`version = "2.1.0"`)
- Accept patches automatically (`version = "~> 2.1.0"`)
- Accept minor updates (`version = "~> 2.0"`)
- Make informed decisions about upgrades
- Avoid surprise breaking changes
</details>

<details>
<summary>4. Calculate the time savings if 47 teams each spend 2 hours/week on infrastructure requests, and self-service reduces this to 15 minutes/week.</summary>

**Answer**:
- Before: 47 teams × 2 hours/week = **94 hours/week**
- After: 47 teams × 0.25 hours/week = **11.75 hours/week**
- Weekly savings: 94 - 11.75 = **82.25 hours/week**
- Annual savings: 82.25 × 52 = **4,277 hours/year**
- At $100/hour engineering cost: **$427,700/year saved**

Plus qualitative benefits: faster time-to-market, reduced context switching, fewer errors.
</details>

<details>
<summary>5. What is the role of a Platform Team in IaC at scale?</summary>

**Answer**: Platform Team responsibilities:
- **Build module library**: Create and maintain blessed modules
- **Define policies**: Security, compliance, and architectural standards
- **Manage shared infrastructure**: Networking, security, identity
- **Enable self-service**: Build tooling for team autonomy
- **Provide guardrails**: Policy as code enforcement
- **Support teams**: Training, documentation, troubleshooting
- **Reduce cognitive load**: Abstract complexity behind simple interfaces

They operate as an "enabling team" that makes stream-aligned teams more effective.
</details>

<details>
<summary>6. What is Terragrunt and when should you use it?</summary>

**Answer**: Terragrunt is a thin wrapper for Terraform that helps with:
- **DRY configuration**: Generate backend, provider blocks automatically
- **Dependencies**: Manage cross-module dependencies explicitly
- **Multi-environment**: Apply same code across environments with different inputs
- **Remote state**: Consistent state configuration across all modules

Use it when:
- You have many environments with similar configurations
- You need to manage complex module dependencies
- You want to reduce boilerplate in terraform configurations
- You need run-all commands across multiple modules
</details>

<details>
<summary>7. How do CODEOWNERS files help with IaC governance at scale?</summary>

**Answer**: CODEOWNERS:
- **Automatic review assignment**: PRs automatically request review from owners
- **Enforce approval requirements**: Changes require owner approval
- **Clear responsibility**: Everyone knows who owns what
- **Security boundaries**: Security team reviews sensitive changes
- **Compliance**: Audit trail of who approved what

Example governance:
- Platform team must approve module changes
- Security team must approve production changes
- Teams can self-serve within their owned directories
</details>

<details>
<summary>8. A company has 180 Terraform repositories with 847 unique resource configurations. They want to consolidate to a module library. What would be a reasonable number of modules to target?</summary>

**Answer**: Target 15-25 modules covering:
- Core networking (VPC, subnets, security groups)
- Compute (EKS, ECS, Lambda, EC2)
- Databases (RDS variants, DynamoDB, ElastiCache)
- Storage (S3, EFS)
- Messaging (SQS, SNS, EventBridge)
- Security (IAM roles, KMS, ACM)
- CDN/API (CloudFront, API Gateway)

Reasoning:
- 847 variants → 15-25 modules = ~95% reduction
- Each module should be cohesive and reusable
- Too few = modules too complex, too many = no standardization benefit
- Pareto principle: 20% of resource types cover 80% of use cases
</details>

---

## Hands-On Exercise

**Objective**: Design and implement a scalable IaC structure for a multi-team organization.

### Part 1: Repository Structure

```bash
# Create scalable directory structure
mkdir -p iac-at-scale/{modules,environments,policies,tests}

# Create module structure
for module in vpc eks rds s3; do
  mkdir -p iac-at-scale/modules/$module/{v1.0.0,tests}
done

# Create environment structure
for env in dev staging production; do
  for team in platform alpha beta; do
    mkdir -p iac-at-scale/environments/$env/$team
  done
done

# Create CODEOWNERS
cat > iac-at-scale/CODEOWNERS << 'EOF'
# Platform team owns shared infrastructure
/modules/                           @platform-team
/environments/*/platform/           @platform-team
/policies/                          @platform-team @security-team

# Production requires security review
/environments/production/           @platform-team @security-team

# Teams own their directories
/environments/*/alpha/              @team-alpha
/environments/*/beta/               @team-beta
EOF

# View structure
find iac-at-scale -type d | head -30
```

### Part 2: Create Base Module

```bash
# Create VPC module
cat > iac-at-scale/modules/vpc/v1.0.0/main.tf << 'EOF'
variable "environment" {
  type = string
}

variable "team" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

locals {
  tags = {
    Environment = var.environment
    Team        = var.team
    ManagedBy   = "terraform"
    Module      = "vpc/v1.0.0"
  }
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = merge(local.tags, { Name = "${var.environment}-${var.team}-vpc" })
}

output "vpc_id" {
  value = aws_vpc.main.id
}
EOF
```

### Part 3: Create Team Configuration

```bash
# Create team configuration using module
cat > iac-at-scale/environments/dev/alpha/main.tf << 'EOF'
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "dev/alpha/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

module "vpc" {
  source = "../../../modules/vpc/v1.0.0"

  environment = "dev"
  team        = "alpha"
  vpc_cidr    = "10.1.0.0/16"
}
EOF
```

### Part 4: Create Policy

```bash
# Create OPA policy for required tags
cat > iac-at-scale/policies/required_tags.rego << 'EOF'
package terraform.tags

required_tags := ["Environment", "Team", "ManagedBy"]

deny[msg] {
  resource := input.resource_changes[_]
  resource.change.actions[_] == "create"

  tags := object.get(resource.change.after, "tags", {})

  missing := [tag |
    tag := required_tags[_]
    not tags[tag]
  ]

  count(missing) > 0
  msg := sprintf("%s missing tags: %v", [resource.address, missing])
}
EOF
```

### Success Criteria

- [ ] Directory structure supports multiple teams and environments
- [ ] CODEOWNERS defines clear ownership boundaries
- [ ] Modules are versioned and reusable
- [ ] Teams can independently manage their infrastructure
- [ ] Policies enforce organizational standards

---

## Key Takeaways

- [ ] **Choose repository strategy wisely** - Monorepo, polyrepo, or hybrid based on organization size
- [ ] **Split state files** - By component/team for speed and reduced blast radius
- [ ] **Version your modules** - Semantic versioning enables safe updates
- [ ] **Use a module registry** - Central source of truth for blessed modules
- [ ] **Policy as code** - Enforce standards automatically in CI/CD
- [ ] **Enable self-service** - Platform team builds, stream teams consume
- [ ] **Define ownership clearly** - CODEOWNERS and tags for accountability
- [ ] **Standardize gradually** - Consolidate over time, don't big-bang
- [ ] **Measure and iterate** - Track time-to-provision, compliance, satisfaction
- [ ] **Document everything** - Golden paths need clear documentation

---

## Did You Know?

> **Module Reuse Statistics**: Organizations with mature IaC practices reuse modules an average of 47 times each, compared to 3 times for organizations without a module strategy.

> **State File Growth**: A typical enterprise Terraform state file grows by approximately 1,000 resources per year. Without splitting, plan times can exceed 30 minutes after 5 years.

> **Team Topology Origins**: The Platform Team model comes from the book "Team Topologies" (2019), which identified four fundamental team types including the "Platform Team" that provides internal services to other teams.

> **Cost of Inconsistency**: A 2023 study found that organizations with standardized IaC modules spent 67% less time on infrastructure incidents compared to those with ad-hoc configurations.

---

## Next Module

Continue to [Module 6.5: Drift Detection and Remediation](../module-6.5-drift-remediation/) to learn how to detect, prevent, and automatically fix infrastructure drift from your desired state.

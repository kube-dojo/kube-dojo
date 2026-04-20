---
title: "Module 7.1: Terraform Deep Dive"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.1-terraform
sidebar:
  order: 2
---
## Complexity: [COMPLEX]
## Time to Complete: 60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](/platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) - Core IaC concepts
- [Module 6.2: IaC Testing](/platform/disciplines/delivery-automation/iac/module-6.2-iac-testing/) - Testing strategies
- Basic command-line experience

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Configure Terraform workspaces and state backends for multi-environment infrastructure management**
- **Implement reusable Terraform modules with input validation, outputs, and versioned releases**
- **Deploy Kubernetes clusters and cloud resources using Terraform providers with drift detection**
- **Evaluate Terraform state management strategies for team collaboration and disaster recovery**


## Why This Module Matters

**The Tool That Changed Infrastructure**

[In 2014, HashiCorp released Terraform](https://www.hashicorp.com/blog/terraform-announcement), and infrastructure management changed significantly. Before Terraform, provisioning infrastructure meant either clicking through cloud consoles (slow, error-prone, not repeatable) or writing custom scripts for each cloud provider (complex, different APIs, no state tracking).

Terraform introduced three revolutionary concepts: declarative configuration (describe what you want, not how to get it), a provider model (one tool for any cloud), and state management (tracking what exists). Over the following years, Terraform became a widely adopted infrastructure-as-code tool.

Today, understanding Terraform deeply—not just copying examples from Stack Overflow—is essential for any infrastructure engineer. This module takes you beyond the basics into patterns that separate production-ready Terraform from tutorial code.

---

## Terraform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TERRAFORM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                     ┌──────────────────┐                        │
│                     │   Terraform CLI   │                       │
│                     │  (Core Engine)    │                       │
│                     └────────┬─────────┘                        │
│                              │                                  │
│          ┌───────────────────┼───────────────────┐             │
│          │                   │                   │             │
│          ▼                   ▼                   ▼             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   Provider   │   │   Provider   │   │   Provider   │       │
│  │     AWS      │   │    Azure     │   │     GCP      │       │
│  │   (plugin)   │   │   (plugin)   │   │   (plugin)   │       │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘       │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │  AWS APIs    │   │  Azure APIs  │   │  GCP APIs    │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Configuration Flow:                                            │
│                                                                 │
│  *.tf files ──▶ Parse ──▶ Build Graph ──▶ Plan ──▶ Apply       │
│       │            │           │           │          │         │
│       │            │           │           │          ▼         │
│       │            │           │           │     terraform      │
│       │            │           │           │      .tfstate      │
│       │            │           │           │          │         │
│       │            │           │           ▼          │         │
│       │            │           │     Compare with ◄───┘         │
│       │            │           │     current state              │
│       │            │           │           │                    │
│       │            │           │           ▼                    │
│       │            │           │     Determine changes          │
│       │            │           │     (create/update/delete)     │
│       │            │           │                                │
│       └────────────┴───────────┴────────────────────────────   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Provider Configuration

### Multi-Provider Setup

```hcl
# versions.tf - Pin provider versions
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

# providers.tf - Configure providers
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Project     = var.project_name
    }
  }

  # Assume role for cross-account access
  assume_role {
    role_arn     = var.assume_role_arn
    session_name = "TerraformSession"
  }
}

# Multiple regions with aliases
provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
}

# Kubernetes provider configured from EKS
provider "kubernetes" {
  host                   = data.aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", data.aws_eks_cluster.main.name]
  }
}

# Helm provider
provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", data.aws_eks_cluster.main.name]
    }
  }
}
```

### Provider Patterns for Multi-Account

```hcl
# Multi-account hub-spoke pattern
locals {
  accounts = {
    development = "111111111111"
    staging     = "222222222222"
    production  = "333333333333"
  }
}

# Generate providers for each account
provider "aws" {
  alias  = "development"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${local.accounts.development}:role/TerraformRole"
  }
}

provider "aws" {
  alias  = "staging"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${local.accounts.staging}:role/TerraformRole"
  }
}

provider "aws" {
  alias  = "production"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${local.accounts.production}:role/TerraformRole"
  }
}

# Use specific provider
resource "aws_s3_bucket" "prod_bucket" {
  provider = aws.production
  bucket   = "production-data-bucket"
}
```

---

## Advanced State Management

### Remote State Configuration

```hcl
# backend.tf - S3 backend with encryption and locking
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "environments/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "terraform-state-lock"

    # Cross-account state access
    role_arn = "arn:aws:iam::123456789012:role/TerraformStateAccess"
  }
}
```

### State Commands Mastery

```bash
# List all resources in state
terraform state list

# Show specific resource details
terraform state show aws_instance.web

# Move resource to different address (refactoring)
terraform state mv aws_instance.web aws_instance.application

# Move resource to different state file
terraform state mv -state-out=../other/terraform.tfstate aws_instance.web aws_instance.web

# Remove resource from state (doesn't destroy)
terraform state rm aws_instance.web

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Pull remote state to local
terraform state pull > terraform.tfstate.backup

# Push local state to remote (dangerous!)
terraform state push terraform.tfstate

# Force unlock stuck state
terraform force-unlock LOCK_ID
```

### State File Structure

```json
{
  "version": 4,
  "terraform_version": "1.6.0",
  "serial": 42,
  "lineage": "unique-id-for-this-state",
  "outputs": {
    "instance_ip": {
      "value": "10.0.1.100",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "ami": "ami-12345678",
            "instance_type": "t3.medium",
            "tags": {
              "Name": "web-server"
            }
          },
          "sensitive_attributes": [],
          "private": "base64-encoded-internal-state"
        }
      ]
    }
  ]
}
```

### Cross-State References

```hcl
# Reference outputs from another state
data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket   = "company-terraform-state"
    key      = "environments/production/networking/terraform.tfstate"
    region   = "us-east-1"
    role_arn = "arn:aws:iam::123456789012:role/TerraformStateAccess"
  }
}

# Use outputs from remote state
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.medium"
  subnet_id     = data.terraform_remote_state.networking.outputs.private_subnet_ids[0]

  vpc_security_group_ids = [
    data.terraform_remote_state.networking.outputs.app_security_group_id
  ]
}
```

---

## Module Design Patterns

### Module Structure Best Practice

```
modules/
└── vpc/
    ├── main.tf          # Primary resources
    ├── variables.tf     # Input variables
    ├── outputs.tf       # Output values
    ├── versions.tf      # Provider requirements
    ├── locals.tf        # Local values
    ├── data.tf          # Data sources
    ├── README.md        # Documentation
    ├── examples/        # Usage examples
    │   └── complete/
    │       └── main.tf
    └── tests/           # Tests
        └── vpc_test.tftest.hcl
```

### Composable Module Pattern

```hcl
# modules/vpc/main.tf - Core VPC module
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "${var.name}-vpc"
  })
}

resource "aws_internet_gateway" "main" {
  count  = var.create_igw ? 1 : 0
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${var.name}-igw"
  })
}

# modules/vpc/subnets.tf - Subnet resources
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.name}-public-${count.index + 1}"
    Tier = "public"
  })
}

resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.tags, {
    Name = "${var.name}-private-${count.index + 1}"
    Tier = "private"
  })
}
```

```hcl
# modules/vpc/variables.tf
variable "name" {
  description = "Name prefix for all resources"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.name))
    error_message = "Name must start with letter, contain only lowercase alphanumeric and hyphens."
  }
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be valid CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones required for HA."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = []
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = []
}

variable "create_igw" {
  description = "Create Internet Gateway"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

```hcl
# modules/vpc/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "igw_id" {
  description = "ID of Internet Gateway"
  value       = var.create_igw ? aws_internet_gateway.main[0].id : null
}
```

### Module Composition

```hcl
# environments/production/main.tf
module "vpc" {
  source = "../../modules/vpc"

  name               = "production"
  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

  tags = local.common_tags
}

module "eks" {
  source = "../../modules/eks"

  cluster_name   = "production"
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnet_ids

  node_groups = {
    general = {
      instance_types = ["t3.large"]
      min_size       = 2
      max_size       = 10
      desired_size   = 3
    }
  }

  tags = local.common_tags
}

module "rds" {
  source = "../../modules/rds"

  identifier     = "production"
  engine         = "postgres"
  engine_version = "15"
  instance_class = "db.r5.large"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  tags = local.common_tags
}
```

---

## Advanced HCL Patterns

### Dynamic Blocks

```hcl
# Dynamic security group rules
variable "ingress_rules" {
  description = "List of ingress rules"
  type = list(object({
    port        = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))
  default = []
}

resource "aws_security_group" "main" {
  name        = var.name
  description = var.description
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# Usage
module "web_sg" {
  source = "./modules/security-group"

  name   = "web-sg"
  vpc_id = module.vpc.vpc_id

  ingress_rules = [
    {
      port        = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTPS"
    },
    {
      port        = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTP (redirect to HTTPS)"
    }
  ]
}
```

### For Expressions

```hcl
# Transform list to map
variable "users" {
  type = list(object({
    name  = string
    email = string
    role  = string
  }))
}

locals {
  # Create map keyed by username
  users_by_name = { for u in var.users : u.name => u }

  # Filter admins
  admin_emails = [for u in var.users : u.email if u.role == "admin"]

  # Transform to different structure
  user_roles = { for u in var.users : u.email => u.role }
}

# Create IAM users from map
resource "aws_iam_user" "users" {
  for_each = local.users_by_name
  name     = each.key
  tags = {
    Email = each.value.email
    Role  = each.value.role
  }
}
```

### Conditional Resources

```hcl
# Create resource only in certain conditions
variable "create_nat_gateway" {
  description = "Create NAT Gateway"
  type        = bool
  default     = true
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# Single NAT for dev, multiple for production
locals {
  nat_gateway_count = var.create_nat_gateway ? (
    var.environment == "production" ? length(var.availability_zones) : 1
  ) : 0
}

resource "aws_nat_gateway" "main" {
  count = local.nat_gateway_count

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.name}-nat-${count.index + 1}"
  }
}

resource "aws_eip" "nat" {
  count  = local.nat_gateway_count
  domain = "vpc"
}
```

### Complex Locals

```hcl
locals {
  # Environment-specific configurations
  env_config = {
    dev = {
      instance_type = "t3.small"
      min_nodes     = 1
      max_nodes     = 3
      multi_az      = false
    }
    staging = {
      instance_type = "t3.medium"
      min_nodes     = 2
      max_nodes     = 5
      multi_az      = false
    }
    production = {
      instance_type = "t3.large"
      min_nodes     = 3
      max_nodes     = 20
      multi_az      = true
    }
  }

  # Current environment config
  config = local.env_config[var.environment]

  # Subnet CIDR calculation
  subnet_cidrs = {
    public = [
      for i in range(length(var.availability_zones)) :
      cidrsubnet(var.vpc_cidr, 8, i)
    ]
    private = [
      for i in range(length(var.availability_zones)) :
      cidrsubnet(var.vpc_cidr, 8, i + 10)
    ]
    database = [
      for i in range(length(var.availability_zones)) :
      cidrsubnet(var.vpc_cidr, 8, i + 20)
    ]
  }

  # Flatten nested structures
  all_subnets = flatten([
    for tier, cidrs in local.subnet_cidrs : [
      for i, cidr in cidrs : {
        tier = tier
        az   = var.availability_zones[i]
        cidr = cidr
        name = "${var.name}-${tier}-${i + 1}"
      }
    ]
  ])
}
```

---

## Lifecycle Management

### Lifecycle Rules

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    # Create new resource before destroying old one
    create_before_destroy = true

    # Prevent accidental destruction
    prevent_destroy = true

    # Ignore changes to certain attributes
    ignore_changes = [
      ami,              # Allow AMI updates outside Terraform
      user_data,        # User data changes don't require replacement
      tags["LastModified"]
    ]

    # Replace when any of these change
    replace_triggered_by = [
      aws_security_group.web.id  # Recreate if SG changes
    ]
  }
}

# Database with protection
resource "aws_db_instance" "main" {
  identifier     = var.db_identifier
  engine         = "postgres"
  instance_class = var.instance_class

  deletion_protection = true

  lifecycle {
    prevent_destroy = true

    # Ignore password changes (managed externally)
    ignore_changes = [password]
  }
}
```

### Moved Blocks ([Terraform 1.1+](https://github.com/hashicorp/terraform/releases/tag/v1.1.0))

```hcl
# Refactoring without recreating resources
# Old: resource "aws_instance" "web"
# New: resource "aws_instance" "application"

moved {
  from = aws_instance.web
  to   = aws_instance.application
}

# Moving into a module
moved {
  from = aws_vpc.main
  to   = module.networking.aws_vpc.main
}

# Moving from count to for_each
moved {
  from = aws_subnet.private[0]
  to   = aws_subnet.private["us-east-1a"]
}
```

### Import Blocks ([Terraform 1.5+](https://github.com/hashicorp/terraform/releases/tag/v1.5.0))

```hcl
# Declarative import
import {
  to = aws_instance.web
  id = "i-1234567890abcdef0"
}

import {
  to = aws_s3_bucket.data
  id = "my-existing-bucket"
}

# Generate configuration for imported resources
terraform plan -generate-config-out=generated.tf
```

---

## Terraform Functions

### String Functions

```hcl
locals {
  # Join list with delimiter
  subnet_list = join(", ", var.subnet_ids)
  # "subnet-111, subnet-222, subnet-333"

  # Split string into list
  tags_list = split(",", var.tags_string)

  # Format string
  instance_name = format("%s-%s-%03d", var.environment, var.role, var.instance_number)
  # "production-web-001"

  # Replace in string
  sanitized_name = replace(var.name, " ", "-")

  # Regex replace
  safe_name = regex("[a-z0-9-]+", lower(var.name))

  # Trim whitespace
  clean_value = trimspace(var.input)
}
```

### Collection Functions

```hcl
locals {
  # Flatten nested lists
  all_subnet_ids = flatten([
    module.vpc.public_subnet_ids,
    module.vpc.private_subnet_ids
  ])

  # Merge maps (later values override)
  all_tags = merge(
    var.default_tags,
    var.environment_tags,
    var.resource_tags
  )

  # Lookup with default
  instance_type = lookup(var.instance_types, var.environment, "t3.small")

  # Filter list
  public_subnets = [for s in var.subnets : s if s.public == true]

  # Distinct values
  unique_azs = distinct([for s in var.subnets : s.availability_zone])

  # Sort
  sorted_names = sort(var.names)

  # Contains
  has_production = contains(var.environments, "production")

  # Length
  subnet_count = length(var.subnet_ids)

  # Element (with wrap-around)
  first_az = element(var.availability_zones, 0)

  # Coalesce (first non-null)
  instance_type = coalesce(var.override_instance_type, local.default_instance_type)

  # Coalescelist (first non-empty list)
  subnet_ids = coalescelist(var.custom_subnets, data.aws_subnets.default.ids)
}
```

### Encoding Functions

```hcl
locals {
  # JSON encode
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "${aws_s3_bucket.main.arn}/*"
    }]
  })

  # JSON decode
  config = jsondecode(file("${path.module}/config.json"))

  # Base64
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    hostname = var.hostname
  }))

  # YAML encode (Terraform 1.3+)
  k8s_config = yamlencode({
    apiVersion = "v1"
    kind       = "ConfigMap"
    metadata = {
      name = "app-config"
    }
  })
}
```

### IP Network Functions

```hcl
locals {
  # Calculate subnet CIDRs
  public_cidrs = [
    for i in range(3) : cidrsubnet(var.vpc_cidr, 8, i)
  ]
  # ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24"]

  # Get host address
  first_host = cidrhost("10.0.1.0/24", 1)
  # "10.0.1.1"

  # Get netmask
  netmask = cidrnetmask("10.0.0.0/16")
  # "255.255.0.0"
}
```

---

## Example Scenario: Migrating Terraform State Layouts

**Scenario**: A team migrating from workspace-based state to directory-based layouts
**Challenge**: Migrating from workspace-based state to directory-based

**The Situation**:
```
Before: Single directory with workspaces
infrastructure/
└── terraform/
    └── main.tf  # Using terraform workspace for dev/staging/prod

After: Directory per environment
infrastructure/
└── terraform/
    ├── modules/
    ├── dev/
    ├── staging/
    └── production/
```

**The Problem**:
- Multiple workspaces and a large resource inventory
- Different resources per environment
- Can't have downtime during migration
- Need to preserve all resources

**The Solution**:

```bash
# Step 1: Document current state
for ws in dev staging production; do
  terraform workspace select $ws
  terraform state list > resources_${ws}.txt
  terraform state pull > state_${ws}.json
done

# Step 2: Create new directory structure
mkdir -p {dev,staging,production}
for env in dev staging production; do
  cp main.tf variables.tf outputs.tf $env/
  cat > $env/backend.tf << EOF
terraform {
  backend "s3" {
    bucket = "company-terraform-state"
    key    = "environments/${env}/terraform.tfstate"
    region = "us-east-1"
  }
}
EOF
done

# Step 3: Migrate state (per environment)
cd production

# Initialize with new backend, migrate from workspace
terraform init -migrate-state \
  -backend-config="bucket=company-terraform-state" \
  -backend-config="key=environments/production/terraform.tfstate"

# Verify resources
terraform plan  # Should show no changes!
```

**Lessons Learned**:
1. Always backup state before migration
2. Verify with `terraform plan` after each step
3. Document the process for audit trail
4. Test migration in dev first
5. Have rollback plan ready

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Hardcoded values | No flexibility, duplication | Use variables with defaults |
| No state locking | Concurrent modifications corrupt state | DynamoDB for S3 backend |
| Giant modules | Hard to maintain, slow plans | Break into smaller, composable modules |
| No version pinning | Unexpected breaking changes | Pin providers and modules |
| Ignoring plan output | Unexpected destroys | Always review plan before apply |
| Manual state edits | Corruption, lost resources | Use `terraform state` commands |
| No `.terraform.lock.hcl` in git | Version inconsistencies | Commit lock file |
| Sensitive in outputs | Secrets in logs | Use `sensitive = true` |

---

## Quiz

<details>
<summary>1. What is the purpose of the terraform.tfstate file?</summary>

**Answer**: The state file:
- Maps Terraform configuration to real-world resources
- Stores resource IDs and attributes
- Enables Terraform to detect drift and plan changes
- Tracks dependencies between resources
- Stores sensitive values (which is why it needs protection)
- Provides metadata for faster refresh operations
</details>

<details>
<summary>2. What is the difference between `count` and `for_each`?</summary>

**Answer**:
- **count**: Uses integer index, creates `resource[0]`, `resource[1]`, etc.
  - Problem: Removing item 0 causes all subsequent items to shift
  - Use for: Simple cases with stable ordering

- **for_each**: Uses string keys, creates `resource["key1"]`, `resource["key2"]`
  - Advantage: Adding/removing items doesn't affect others
  - Use for: Most cases, especially when items might be added/removed
</details>

<details>
<summary>3. Explain the `lifecycle` block and its options.</summary>

**Answer**: The lifecycle block controls resource behavior:
- **create_before_destroy**: Create replacement before destroying original
- **prevent_destroy**: Terraform will error if resource would be destroyed
- **ignore_changes**: Don't detect changes to specified attributes
- **replace_triggered_by**: Force replacement when referenced resources change

These help manage complex resource dependencies and prevent accidental destruction.
</details>

<details>
<summary>4. What is a data source and when should you use it?</summary>

**Answer**: A data source reads information from infrastructure:
```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}
```

Use data sources when:
- Referencing resources not managed by this Terraform
- Looking up dynamic values (latest AMI, current account ID)
- Cross-referencing between state files
- Reading external configuration
</details>

<details>
<summary>5. How do you refactor resources without recreating them?</summary>

**Answer**: Use `moved` blocks (Terraform 1.1+):
```hcl
moved {
  from = aws_instance.old_name
  to   = aws_instance.new_name
}
```

Or manually with state commands:
```bash
terraform state mv aws_instance.old_name aws_instance.new_name
```

This updates the state without modifying infrastructure.
</details>

<details>
<summary>6. What is provider aliasing and when do you need it?</summary>

**Answer**: Provider aliasing allows multiple configurations of the same provider:
```hcl
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "eu"
  region = "eu-west-1"
}

resource "aws_s3_bucket" "eu_bucket" {
  provider = aws.eu
  bucket   = "my-eu-bucket"
}
```

Use when:
- Multi-region deployments
- Multi-account access
- Different credentials for different resources
</details>

<details>
<summary>7. How do you handle sensitive values in Terraform?</summary>

**Answer**:
1. Mark variables as sensitive: `sensitive = true`
2. Mark outputs as sensitive: `sensitive = true`
3. Use external secret management (Vault, Secrets Manager)
4. Never commit `.tfvars` with secrets
5. Use environment variables: `TF_VAR_db_password`
6. Encrypt state file at rest (S3 SSE-KMS)
7. Restrict state file access (IAM policies)
</details>

<details>
<summary>8. What is the dependency graph and why does it matter?</summary>

**Answer**: Terraform builds a directed acyclic graph (DAG) of all resources:
- Determines execution order automatically
- Enables parallel resource creation
- Ensures dependencies are created first

```bash
# Visualize the graph
terraform graph | dot -Tpng > graph.png
```

Implicit dependencies come from references. Explicit dependencies use:
```hcl
depends_on = [aws_iam_role_policy.example]
```
</details>

---

## Hands-On Exercise

**Objective**: Build a production-ready Terraform module for a web application infrastructure.

### Part 1: Create Module Structure

```bash
mkdir -p terraform-exercise/{modules/webapp,environments/{dev,production}}

# Create module files
cat > terraform-exercise/modules/webapp/variables.tf << 'EOF'
variable "name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "min_size" {
  description = "Minimum ASG size"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum ASG size"
  type        = number
  default     = 3
}

variable "tags" {
  description = "Tags for all resources"
  type        = map(string)
  default     = {}
}
EOF

cat > terraform-exercise/modules/webapp/locals.tf << 'EOF'
locals {
  common_tags = merge(var.tags, {
    Application = var.name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  env_config = {
    dev = {
      instance_type = "t3.micro"
      multi_az      = false
    }
    staging = {
      instance_type = "t3.small"
      multi_az      = false
    }
    production = {
      instance_type = "t3.medium"
      multi_az      = true
    }
  }

  config = local.env_config[var.environment]
}
EOF
```

### Part 2: Add Resources

```bash
cat > terraform-exercise/modules/webapp/main.tf << 'EOF'
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${var.name}-vpc"
  })
}

# Subnets
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public" {
  count = local.config.multi_az ? 3 : 1

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.name}-public-${count.index + 1}"
    Tier = "public"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${var.name}-igw"
  })
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.name}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group
resource "aws_security_group" "web" {
  name        = "${var.name}-web-sg"
  description = "Web server security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.name}-web-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}
EOF

cat > terraform-exercise/modules/webapp/outputs.tf << 'EOF'
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "security_group_id" {
  description = "Web security group ID"
  value       = aws_security_group.web.id
}
EOF
```

### Part 3: Use the Module

```bash
cat > terraform-exercise/environments/dev/main.tf << 'EOF'
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "webapp" {
  source = "../../modules/webapp"

  name        = "myapp"
  environment = "dev"
  vpc_cidr    = "10.0.0.0/16"

  tags = {
    Team      = "platform"
    CostCenter = "CC-1234"
  }
}

output "vpc_id" {
  value = module.webapp.vpc_id
}
EOF

# Initialize and plan
cd terraform-exercise/environments/dev
terraform init
terraform plan
```

### Success Criteria

- [ ] Module structure follows best practices
- [ ] Variables have descriptions and validation
- [ ] Environment-specific configuration via locals
- [ ] Resources properly tagged
- [ ] Security group uses lifecycle rules
- [ ] `terraform plan` shows expected resources

---

## Key Takeaways

- [ ] **Pin versions** - Providers and modules for reproducibility
- [ ] **Use for_each over count** - Better handling of changes
- [ ] **Compose small modules** - Not monolithic configurations
- [ ] **Protect state** - Encryption, locking, restricted access
- [ ] **Use moved blocks** - Refactor without recreation
- [ ] **Leverage locals** - DRY configuration with computed values
- [ ] **Dynamic blocks** - Reduce repetition in complex resources
- [ ] **Lifecycle rules** - Control resource behavior
- [ ] **Data sources** - Reference external resources
- [ ] **Test your modules** - Native tests or Terratest

---

## Did You Know?

> **Terraform Origin**: Terraform began as a HashiCorp project focused on cloud-agnostic infrastructure automation.

> **Provider Ecosystem**: The Terraform Registry hosts over 3,500 providers, including many community-contributed providers for niche and unconventional services.

> **State File Scale**: Very large Terraform estates often need state splitting and careful operational boundaries.

> **Graph Visualization**: Terraform builds a dependency graph to determine resource ordering and parallelism during operations.

---

## Next Module

Continue to [Module 7.2: OpenTofu](../module-7.2-opentofu/) to learn about the open-source fork of Terraform and its unique features.

## Sources

- [HashiCorp Terraform Announcement](https://www.hashicorp.com/blog/terraform-announcement) — Primary-source background on Terraform's original 2014 release and early goals.
- [Terraform v1.1.0 Release Notes](https://github.com/hashicorp/terraform/releases/tag/v1.1.0) — Documents moved blocks and other refactoring-related language features.
- [Terraform v1.5.0 Release Notes](https://github.com/hashicorp/terraform/releases/tag/v1.5.0) — Documents declarative import blocks and generated configuration support.
- [HashiCorp Terraform Product Overview](https://www.hashicorp.com/products/terraform) — Further reading on Terraform's ecosystem and common provider-driven use cases.

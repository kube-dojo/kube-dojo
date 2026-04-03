---
title: "Module 7.2: OpenTofu - The Open Source Fork"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.2-opentofu
sidebar:
  order: 3
---
## Complexity: [MEDIUM]
## Time to Complete: 40 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 7.1: Terraform Deep Dive](../module-7.1-terraform/) - Terraform fundamentals
- Basic understanding of open-source licensing

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy infrastructure using OpenTofu as a drop-in replacement for Terraform with license freedom**
- **Configure OpenTofu state encryption and client-side encryption for sensitive infrastructure state**
- **Migrate existing Terraform configurations and state files to OpenTofu without disruption**
- **Compare OpenTofu's feature roadmap and community governance against Terraform's BSL licensing model**


## Why This Module Matters

**The License Change That Shook Infrastructure**

On August 10, 2023, HashiCorp announced a change that sent shockwaves through the infrastructure community. After nine years as open-source software under the Mozilla Public License (MPL 2.0), Terraform would switch to the Business Source License (BSL 1.1). The new license prohibited competitors from offering commercial Terraform services.

Within days, a coalition of companies and individuals announced OpenTofu—a community-driven fork of Terraform that would remain truly open source under the Linux Foundation. By September 2023, OpenTofu had 100+ contributors and commitments from major cloud vendors.

This module introduces OpenTofu, explains when and why to choose it over Terraform, and covers its unique features that have already surpassed the original.

---

## OpenTofu vs Terraform

```
┌─────────────────────────────────────────────────────────────────┐
│                   OPENTOFU VS TERRAFORM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OpenTofu                          Terraform                    │
│  ────────                          ─────────                    │
│  License: MPL 2.0                  License: BSL 1.1             │
│  Governance: Linux Foundation      Governance: HashiCorp        │
│  Open development                  Closed development           │
│  Community-driven roadmap          Company-driven roadmap       │
│                                                                 │
│  Unique Features:                  Unique Features:             │
│  • State encryption (built-in)     • Terraform Cloud            │
│  • Provider-defined functions      • Sentinel policies          │
│  • Looped imports                  • First-party support        │
│  • for_each for providers          • Private registry           │
│  • -exclude flag for targeting                                  │
│                                                                 │
│  Compatible:                                                    │
│  • Same HCL syntax                                              │
│  • Same providers (mostly)                                      │
│  • Same state file format                                       │
│  • Same module structure                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Install OpenTofu

```bash
# macOS with Homebrew
brew install opentofu

# Linux (Debian/Ubuntu)
curl -fsSL https://get.opentofu.org/install-opentofu.sh | sudo bash

# Linux (via package manager)
# Add repository first
curl -fsSL https://packages.opentofu.org/opentofu/tofu/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/opentofu.gpg
echo "deb [signed-by=/usr/share/keyrings/opentofu.gpg] https://packages.opentofu.org/opentofu/tofu/any/ any main" | sudo tee /etc/apt/sources.list.d/opentofu.list
sudo apt-get update
sudo apt-get install tofu

# Verify installation
tofu version
# OpenTofu v1.6.0

# Docker
docker run -it --rm ghcr.io/opentofu/opentofu:latest version
```

### Migration from Terraform

```bash
# OpenTofu is a drop-in replacement
# Simply replace 'terraform' with 'tofu'

# Before (Terraform)
terraform init
terraform plan
terraform apply

# After (OpenTofu)
tofu init
tofu plan
tofu apply

# For scripts, you can create an alias
alias terraform=tofu

# State files are compatible
# No migration needed for state
```

---

## OpenTofu-Specific Features

### 1. State Encryption (Built-in)

OpenTofu can encrypt state files natively—a feature Terraform lacks without Enterprise.

```hcl
# backend.tf with state encryption
terraform {
  encryption {
    # AWS KMS encryption
    key_provider "aws_kms" "main" {
      kms_key_id = "alias/tofu-state-key"
      region     = "us-east-1"
      key_spec   = "AES_256"
    }

    method "aes_gcm" "state_encryption" {
      keys = key_provider.aws_kms.main
    }

    # Apply to both state and plan files
    state {
      method   = method.aes_gcm.state_encryption
      enforced = true  # Fail if encryption fails
    }

    plan {
      method   = method.aes_gcm.state_encryption
      enforced = true
    }
  }

  backend "s3" {
    bucket = "company-tofu-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}
```

```hcl
# Alternative: PBKDF2 passphrase-based encryption
terraform {
  encryption {
    key_provider "pbkdf2" "passphrase" {
      passphrase = var.state_encryption_passphrase
    }

    method "aes_gcm" "state_method" {
      keys = key_provider.pbkdf2.passphrase
    }

    state {
      method = method.aes_gcm.state_method
    }
  }
}

# Use environment variable
# export TF_VAR_state_encryption_passphrase="your-secure-passphrase"
```

### 2. Provider-Defined Functions

OpenTofu allows providers to define custom functions.

```hcl
# Using provider-defined functions (hypothetical example)
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }
}

# Provider functions (when available)
locals {
  # Example: Provider-specific function
  # parsed_arn = provider::aws::parse_arn(aws_instance.web.arn)
  # account_id = local.parsed_arn.account

  # Current workaround without provider functions
  arn_parts  = split(":", aws_instance.web.arn)
  account_id = local.arn_parts[4]
}
```

### 3. Looped Imports (for_each imports)

Import multiple resources with a single import block.

```hcl
# Import multiple S3 buckets
import {
  for_each = toset(["bucket-a", "bucket-b", "bucket-c"])
  to       = aws_s3_bucket.imported[each.key]
  id       = each.key
}

# The resources
resource "aws_s3_bucket" "imported" {
  for_each = toset(["bucket-a", "bucket-b", "bucket-c"])
  bucket   = each.key
}

# Import with complex mapping
locals {
  instances_to_import = {
    "web-1" = "i-0abc123456789def0"
    "web-2" = "i-0abc123456789def1"
    "web-3" = "i-0abc123456789def2"
  }
}

import {
  for_each = local.instances_to_import
  to       = aws_instance.web[each.key]
  id       = each.value
}

resource "aws_instance" "web" {
  for_each      = local.instances_to_import
  ami           = "ami-12345678"
  instance_type = "t3.medium"

  tags = {
    Name = each.key
  }
}
```

### 4. -exclude Flag

Target resources to exclude (opposite of -target).

```bash
# Apply everything EXCEPT the database
tofu apply -exclude=module.database

# Apply except multiple resources
tofu apply -exclude=aws_instance.expensive -exclude=aws_db_instance.large

# Useful for:
# - Testing changes without affecting critical resources
# - Phased deployments
# - Debugging resource dependencies
```

### 5. Early Variable/Local Evaluation

```hcl
# OpenTofu can evaluate certain expressions earlier in the process

# Backend configuration with variables (limited support)
terraform {
  backend "s3" {
    bucket = "company-state-${var.environment}"  # Works in OpenTofu 1.7+
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

# Note: Full variable support in backend blocks is still evolving
```

---

## OpenTofu Registry

OpenTofu has its own registry that mirrors the Terraform Registry.

```hcl
# Using OpenTofu registry
terraform {
  required_providers {
    # Providers can come from OpenTofu registry
    aws = {
      source  = "hashicorp/aws"  # Same source, resolved from registry.opentofu.org
      version = "~> 5.30"
    }

    # Community providers
    datadog = {
      source  = "DataDog/datadog"
      version = "~> 3.30"
    }
  }
}

# Module from OpenTofu registry
module "vpc" {
  source  = "registry.opentofu.org/terraform-aws-modules/vpc/aws"
  version = "5.4.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
}
```

---

## Configuration Differences

### Provider Configuration

```hcl
# OpenTofu supports for_each in providers (experimental)
# Terraform does not support this

provider "aws" {
  alias = "multi_region"
  for_each = toset(["us-east-1", "us-west-2", "eu-west-1"])

  region = each.value

  default_tags {
    tags = {
      Region = each.value
    }
  }
}

# Use with resources
resource "aws_s3_bucket" "regional" {
  for_each = toset(["us-east-1", "us-west-2", "eu-west-1"])
  provider = aws.multi_region[each.key]

  bucket = "my-bucket-${each.key}"
}
```

### Testing Framework Enhancements

```hcl
# tests/vpc_test.tftest.hcl
# OpenTofu enhanced testing features

run "setup" {
  variables {
    environment = "test"
  }

  module {
    source = "./fixtures/setup"
  }
}

run "create_vpc" {
  variables {
    environment = "test"
    vpc_cidr    = "10.0.0.0/16"
  }

  # Reference setup run
  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR mismatch"
  }

  # OpenTofu: Enhanced condition support
  assert {
    condition     = length(aws_subnet.private) >= 2
    error_message = "Need at least 2 private subnets"
  }
}

run "verify_outputs" {
  # Use outputs from previous runs
  assert {
    condition     = output.vpc_id != ""
    error_message = "VPC ID should not be empty"
  }
}
```

---

## Migration Guide

### Step 1: Assess Compatibility

```bash
# Check current Terraform version
terraform version

# OpenTofu 1.6.x is compatible with Terraform 1.6.x configurations
# State file format is identical

# Check for HashiCorp-specific features
grep -r "cloud {" *.tf         # Terraform Cloud config
grep -r "backend \"remote\"" *.tf  # Remote backend (TFC)
```

### Step 2: Install OpenTofu

```bash
# Install alongside Terraform (they can coexist)
brew install opentofu

# Verify
tofu version
```

### Step 3: Initialize with OpenTofu

```bash
# In your existing Terraform directory
# No changes to .tf files needed

# Initialize (downloads providers from OpenTofu registry)
tofu init

# State file is compatible - no migration needed
tofu plan

# If you see no changes, migration is successful!
```

### Step 4: Update CI/CD

```yaml
# .github/workflows/infrastructure.yml
name: Infrastructure

on:
  pull_request:
    paths: ['terraform/**']
  push:
    branches: [main]

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Use OpenTofu instead of Terraform
      - name: Setup OpenTofu
        uses: opentofu/setup-opentofu@v1
        with:
          tofu_version: "1.6.0"

      - name: OpenTofu Init
        run: tofu init
        working-directory: terraform/

      - name: OpenTofu Plan
        run: tofu plan -out=tfplan
        working-directory: terraform/

  apply:
    needs: plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup OpenTofu
        uses: opentofu/setup-opentofu@v1

      - name: OpenTofu Apply
        run: tofu apply -auto-approve
        working-directory: terraform/
```

### Handling Terraform Cloud Users

```hcl
# If using Terraform Cloud, you'll need alternatives

# Option 1: Use S3 backend with state locking
terraform {
  backend "s3" {
    bucket         = "company-tofu-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "tofu-state-lock"
  }
}

# Option 2: Use Spacelift, env0, or Scalr (OpenTofu-compatible)

# Option 3: Self-hosted remote state
# terraform {
#   backend "http" {
#     address        = "https://state.company.com/terraform.tfstate"
#     lock_address   = "https://state.company.com/terraform.tfstate/lock"
#     unlock_address = "https://state.company.com/terraform.tfstate/lock"
#   }
# }
```

---

## When to Choose OpenTofu

### Choose OpenTofu When:

1. **Open-source commitment**: Your organization values true open-source licensing
2. **Vendor independence**: You want to avoid single-vendor lock-in
3. **State encryption**: You need native state encryption without Enterprise
4. **Advanced features**: You want early access to features like provider functions
5. **Competitive services**: You're building or using commercial IaC platforms
6. **Community governance**: You prefer Linux Foundation governance over corporate control

### Choose Terraform When:

1. **Terraform Cloud/Enterprise**: You're heavily invested in HashiCorp's platform
2. **First-party support**: You need commercial support from HashiCorp
3. **Sentinel policies**: You require Sentinel policy-as-code
4. **Risk aversion**: Your organization prefers established vendors
5. **Existing contracts**: You have agreements with HashiCorp

### Decision Matrix

```
┌────────────────────────────────────────────────────────────────┐
│                    DECISION MATRIX                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Factor                  OpenTofu    Terraform   Weight       │
│  ──────────────────────────────────────────────────────────   │
│  Open-source license        ✓           ✗         High        │
│  State encryption           ✓           ~*        High        │
│  Community governance       ✓           ✗         Medium      │
│  Vendor support             ~**         ✓         Medium      │
│  Terraform Cloud            ✗           ✓         Low***      │
│  Provider compatibility     ✓           ✓         High        │
│  Module compatibility       ✓           ✓         High        │
│  Innovation speed           ✓           ~         Medium      │
│                                                                │
│  * Terraform Enterprise only                                   │
│  ** Community + third-party vendors                            │
│  *** Alternatives exist (Spacelift, env0, Scalr)              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### State Encryption with Key Rotation

```hcl
terraform {
  encryption {
    # Current key
    key_provider "aws_kms" "current" {
      kms_key_id = "alias/tofu-state-key-v2"
      region     = "us-east-1"
      key_spec   = "AES_256"
    }

    # Old key (for reading old state)
    key_provider "aws_kms" "old" {
      kms_key_id = "alias/tofu-state-key-v1"
      region     = "us-east-1"
      key_spec   = "AES_256"
    }

    method "aes_gcm" "new_key" {
      keys = key_provider.aws_kms.current
    }

    method "aes_gcm" "old_key" {
      keys = key_provider.aws_kms.old
    }

    state {
      method = method.aes_gcm.new_key
      fallback {
        method = method.aes_gcm.old_key  # Try old key if new fails
      }
    }
  }
}
```

### Multi-Region Deployment

```hcl
# variables.tf
variable "regions" {
  description = "Regions to deploy to"
  type        = set(string)
  default     = ["us-east-1", "us-west-2", "eu-west-1"]
}

# main.tf
module "regional_infrastructure" {
  source   = "./modules/regional"
  for_each = var.regions

  region      = each.key
  environment = var.environment

  providers = {
    aws = aws.by_region[each.key]
  }
}

# outputs.tf
output "regional_endpoints" {
  description = "Endpoints by region"
  value = {
    for region, infra in module.regional_infrastructure :
    region => infra.endpoint
  }
}
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Assuming full compatibility | Some edge cases differ | Test thoroughly before migration |
| Mixing Terraform and OpenTofu | State format same but behaviors may differ | Use one tool per state file |
| Ignoring registry differences | Some providers may lag | Check provider availability |
| Not encrypting state | Sensitive data exposed | Use state encryption feature |
| Expecting Terraform Cloud | BSL doesn't allow competitors | Use alternatives (S3, Spacelift) |
| Skipping CI/CD updates | Jobs fail with wrong binary | Update all pipelines |

---

## Quiz

<details>
<summary>1. Why was OpenTofu created?</summary>

**Answer**: OpenTofu was created in response to HashiCorp changing Terraform's license from MPL 2.0 (open source) to BSL 1.1 (source-available but not open source). BSL restricts competitive commercial use, which concerned many organizations and vendors. OpenTofu maintains the original open-source license under Linux Foundation governance.
</details>

<details>
<summary>2. What is the main command difference between Terraform and OpenTofu?</summary>

**Answer**: The only command difference is the binary name:
- Terraform: `terraform init`, `terraform plan`, `terraform apply`
- OpenTofu: `tofu init`, `tofu plan`, `tofu apply`

All subcommands, flags, and behaviors are identical. You can even alias `terraform=tofu` for compatibility.
</details>

<details>
<summary>3. What unique feature does OpenTofu provide for sensitive data protection?</summary>

**Answer**: OpenTofu provides **native state encryption**. You can encrypt state files at rest using:
- AWS KMS
- GCP KMS
- Azure Key Vault
- PBKDF2 passphrase
- Other key providers

This feature is built-in, whereas Terraform requires Enterprise for state encryption beyond S3 SSE.
</details>

<details>
<summary>4. Can you use existing Terraform state files with OpenTofu?</summary>

**Answer**: Yes, state files are fully compatible. OpenTofu uses the same state file format as Terraform. You can:
- Run `tofu init` in an existing Terraform directory
- Continue from existing state without migration
- Even switch back to Terraform if needed

The only consideration is that once you use OpenTofu-specific features (like state encryption), you should continue with OpenTofu.
</details>

<details>
<summary>5. What is the -exclude flag in OpenTofu?</summary>

**Answer**: The `-exclude` flag is the opposite of `-target`. It allows you to apply changes to everything EXCEPT specified resources:

```bash
tofu apply -exclude=module.database
```

This is useful for:
- Phased deployments
- Testing changes without affecting critical resources
- Debugging dependency issues
</details>

<details>
<summary>6. What alternatives exist for Terraform Cloud users switching to OpenTofu?</summary>

**Answer**: Alternatives include:
- **S3 backend**: With DynamoDB for state locking
- **Spacelift**: Full-featured IaC platform supporting OpenTofu
- **env0**: Environment-as-a-Service with OpenTofu support
- **Scalr**: Terraform/OpenTofu platform
- **Self-hosted**: HTTP backend with custom state server
- **GitLab**: Built-in Terraform state management

Each provides similar functionality to Terraform Cloud (remote state, runs, policies).
</details>

---

## Hands-On Exercise

**Objective**: Migrate a Terraform project to OpenTofu with state encryption.

### Part 1: Install and Verify

```bash
# Install OpenTofu
brew install opentofu

# Verify installation
tofu version
```

### Part 2: Create Test Project

```bash
mkdir -p opentofu-lab
cd opentofu-lab

# Create simple configuration
cat > main.tf << 'EOF'
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_pet" "name" {
  length = 2
}

resource "local_file" "config" {
  filename = "${path.module}/config.txt"
  content  = "Hello from ${random_pet.name.id}!"
}

output "pet_name" {
  value = random_pet.name.id
}
EOF

# Initialize with OpenTofu
tofu init

# Apply
tofu apply -auto-approve

# Verify
cat config.txt
```

### Part 3: Add State Encryption (Simulated)

```bash
# Add encryption configuration (passphrase-based for demo)
cat > backend.tf << 'EOF'
terraform {
  encryption {
    key_provider "pbkdf2" "main" {
      passphrase = "demo-passphrase-do-not-use-in-production"
    }

    method "aes_gcm" "state_method" {
      keys = key_provider.pbkdf2.main
    }

    state {
      method = method.aes_gcm.state_method
    }
  }
}
EOF

# Reinitialize to apply encryption
tofu init

# Apply to re-encrypt state
tofu apply -auto-approve

# State file is now encrypted
cat terraform.tfstate | head -20
# Should show encrypted content
```

### Part 4: Use OpenTofu-Specific Features

```bash
# Test -exclude flag
cat >> main.tf << 'EOF'

resource "local_file" "secondary" {
  filename = "${path.module}/secondary.txt"
  content  = "Secondary file"
}
EOF

# Apply excluding secondary file
tofu apply -exclude=local_file.secondary

# Secondary file should not be created yet
ls -la
# Only config.txt should exist

# Now apply everything
tofu apply -auto-approve
# secondary.txt now created
```

### Success Criteria

- [ ] OpenTofu installed and working
- [ ] Basic resources created successfully
- [ ] State encryption configured
- [ ] -exclude flag demonstrated
- [ ] State file shows encrypted content

---

## Key Takeaways

- [ ] **Drop-in replacement** - Same syntax, same state format, different binary
- [ ] **State encryption built-in** - Major advantage over Terraform OSS
- [ ] **Linux Foundation governance** - Community-driven, truly open source
- [ ] **Growing feature set** - Provider functions, looped imports, -exclude flag
- [ ] **Provider compatibility** - Works with existing providers
- [ ] **Migration is simple** - Just use `tofu` instead of `terraform`
- [ ] **Alternatives to TFC exist** - Spacelift, env0, Scalr, self-hosted
- [ ] **Choose based on needs** - License, features, support requirements
- [ ] **Test thoroughly** - Some edge cases may behave differently
- [ ] **Stay updated** - OpenTofu is rapidly evolving

---

## Did You Know?

> **Fork Speed**: OpenTofu went from announcement to first stable release in just 6 weeks, making it one of the fastest major open-source project forks in history.

> **Foundation Backing**: OpenTofu is hosted by the Linux Foundation, the same organization that hosts Kubernetes, Linux, and Node.js, ensuring long-term governance stability.

> **Contributor Growth**: Within 3 months of launch, OpenTofu had more unique contributors than Terraform had in the previous year, demonstrating strong community support.

> **Name Origin**: "Tofu" was chosen because it's a versatile, foundational food that can be adapted to many uses—much like infrastructure as code itself.

---

## Next Module

Continue to [Module 7.3: Pulumi](../module-7.3-pulumi/) to learn about infrastructure as code using general-purpose programming languages.

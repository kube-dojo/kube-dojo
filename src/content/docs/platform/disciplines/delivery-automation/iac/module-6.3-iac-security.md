---
title: "Module 6.3: Infrastructure as Code Security"
slug: platform/disciplines/delivery-automation/iac/module-6.3-iac-security
sidebar:
  order: 4
---
## Complexity: [COMPLEX]
## Time to Complete: 50 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](module-6.1-iac-fundamentals/) - Core IaC concepts
- [Module 6.2: IaC Testing](module-6.2-iac-testing/) - Testing strategies
- [Module 4.2: Defense in Depth](../../foundations/security-principles/module-4.2-defense-in-depth/) - Security principles

---

## Why This Module Matters

**The $18.7 Million Terraform Secret**

The security team at a major financial services company received an alert that made their blood run cold. Their Terraform state file—stored in an S3 bucket with "private" permissions—had been accessed from an IP address in Eastern Europe. The state file contained everything: database passwords, API keys, service account credentials, and the complete topology of their production infrastructure.

The investigation revealed a chilling chain of events. A developer had accidentally committed their AWS credentials to a public GitHub repository six months earlier. Those credentials had minimal permissions—read-only access to S3. The attacker had been patiently mapping the organization's infrastructure ever since, downloading state files from dozens of projects. Now they had everything needed to access production systems.

The breach affected 2.3 million customer records. The total cost: $18.7 million in fines, remediation, and lost business.

This module teaches you how to secure infrastructure as code—because your Terraform state file might be the most valuable asset in your entire organization.

---

## The IaC Security Attack Surface

Infrastructure as code introduces unique security challenges that don't exist in traditional infrastructure management.

```
┌─────────────────────────────────────────────────────────────────┐
│                    IaC SECURITY ATTACK SURFACE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   SOURCE    │    │   SECRETS   │    │   STATE     │         │
│  │    CODE     │    │ MANAGEMENT  │    │   FILES     │         │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤         │
│  │ • Hardcoded │    │ • Plaintext │    │ • Sensitive │         │
│  │   secrets   │    │   in vars   │    │   values    │         │
│  │ • Insecure  │    │ • Env vars  │    │ • Resource  │         │
│  │   defaults  │    │   exposed   │    │   metadata  │         │
│  │ • Misconfig │    │ • Weak      │    │ • Access    │         │
│  │   in code   │    │   rotation  │    │   control   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                 │                   │                 │
│         └────────────┬────┴───────────────────┘                 │
│                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    CI/CD PIPELINE                        │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Credential theft from logs                            │   │
│  │ • Supply chain attacks on providers/modules             │   │
│  │ • Malicious pull request modifications                  │   │
│  │ • Insufficient access controls                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                      │                                          │
│                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 DEPLOYED INFRASTRUCTURE                  │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Overly permissive IAM policies                        │   │
│  │ • Public S3 buckets, open security groups               │   │
│  │ • Unencrypted storage, missing logging                  │   │
│  │ • Drift from secure baseline                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Scanning Tools

### Checkov: Comprehensive Policy Scanning

Checkov is the most comprehensive IaC security scanner, supporting Terraform, CloudFormation, Kubernetes, and more.

```bash
# Install Checkov
pip install checkov

# Scan Terraform directory
checkov -d . --framework terraform

# Scan with specific checks
checkov -d . --check CKV_AWS_18,CKV_AWS_19,CKV_AWS_20

# Skip specific checks
checkov -d . --skip-check CKV_AWS_18

# Output to JUnit for CI/CD
checkov -d . -o junitxml > checkov-results.xml

# Scan plan file for accurate results
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
checkov -f tfplan.json

# Custom policy example
cat > custom_policy.py << 'EOF'
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck
from checkov.common.models.enums import CheckResult, CheckCategories

class RequireDescriptionTag(BaseResourceCheck):
    def __init__(self):
        name = "Ensure all resources have description tag"
        id = "CUSTOM_001"
        supported_resources = ['aws_*']
        categories = [CheckCategories.CONVENTION]
        super().__init__(name=name, id=id,
                        categories=categories,
                        supported_resources=supported_resources)

    def scan_resource_conf(self, conf):
        tags = conf.get('tags', [{}])
        if isinstance(tags, list):
            tags = tags[0] if tags else {}
        if 'Description' in tags or 'description' in tags:
            return CheckResult.PASSED
        return CheckResult.FAILED

check = RequireDescriptionTag()
EOF
```

### tfsec: Terraform-Specific Scanner

tfsec (now part of Trivy) focuses specifically on Terraform:

```bash
# Install tfsec
brew install tfsec

# Basic scan
tfsec .

# Scan with specific severity
tfsec . --minimum-severity HIGH

# Output as JSON for parsing
tfsec . --format json > tfsec-results.json

# Scan with custom rules
cat > .tfsec/custom_check.yaml << 'EOF'
checks:
  - code: CUSTOM001
    description: Ensure S3 bucket has specific naming convention
    impact: Non-standard naming makes inventory management difficult
    resolution: Use naming pattern: {env}-{service}-{purpose}
    requiredTypes:
      - resource
    requiredLabels:
      - aws_s3_bucket
    severity: MEDIUM
    matchSpec:
      name: bucket
      action: regexMatches
      value: ^(dev|staging|prod)-[a-z]+-[a-z]+$
    errorMessage: S3 bucket name must follow pattern {env}-{service}-{purpose}
EOF

# Run with custom checks
tfsec . --custom-check-dir .tfsec/
```

### Trivy: All-in-One Scanner

Trivy scans IaC, containers, and filesystems:

```bash
# Install Trivy
brew install trivy

# Scan Terraform configuration
trivy config .

# Scan with severity filter
trivy config . --severity HIGH,CRITICAL

# Scan specific file types
trivy config . --tf-exclude-downloaded-modules

# Output as table with details
trivy config . --format table --output trivy-report.txt

# CI/CD integration with exit code
trivy config . --exit-code 1 --severity CRITICAL
```

### Terrascan: Policy-as-Code Scanner

Terrascan uses Rego policies (same as OPA):

```bash
# Install Terrascan
brew install terrascan

# Scan Terraform
terrascan scan -t terraform

# Scan with specific policy types
terrascan scan -t aws -t k8s

# Use custom policy
cat > custom_policy.rego << 'EOF'
package accurics

rdsEncryptionNotEnabled[retVal] {
    rds := input.aws_db_instance[_]
    rds.config.storage_encrypted != true
    retVal := {
        "Id": rds.id,
        "ReplaceType": "edit",
        "CodeType": "resource",
        "Attribute": "storage_encrypted",
        "Expected": "true"
    }
}
EOF

terrascan scan -t terraform -p custom_policy.rego
```

---

## Secrets Management in IaC

### The Problem with Secrets

```hcl
# ❌ NEVER DO THIS - Secrets in code
resource "aws_db_instance" "main" {
  identifier     = "production-db"
  engine         = "postgres"
  instance_class = "db.r5.large"

  username = "admin"
  password = "SuperSecretPassword123!"  # Committed to git history FOREVER
}

# ❌ NEVER DO THIS - Secrets in variables
variable "db_password" {
  default = "SuperSecretPassword123!"  # Still in code
}

# ❌ RISKY - Environment variables visible in CI/CD logs
# TF_VAR_db_password=SuperSecretPassword123!
```

### Solution 1: HashiCorp Vault

```hcl
# Configure Vault provider
provider "vault" {
  address = "https://vault.company.com:8200"
  # Uses VAULT_TOKEN from environment
}

# Read secrets from Vault
data "vault_generic_secret" "db_creds" {
  path = "secret/data/production/database"
}

# Use secrets without exposing them
resource "aws_db_instance" "main" {
  identifier     = "production-db"
  engine         = "postgres"
  instance_class = "db.r5.large"

  username = data.vault_generic_secret.db_creds.data["username"]
  password = data.vault_generic_secret.db_creds.data["password"]

  lifecycle {
    ignore_changes = [password]  # Don't show in plan
  }
}

# Dynamic secrets - even better
data "vault_aws_access_credentials" "creds" {
  backend = "aws"
  role    = "terraform-role"
  type    = "sts"
}

provider "aws" {
  access_key = data.vault_aws_access_credentials.creds.access_key
  secret_key = data.vault_aws_access_credentials.creds.secret_key
  token      = data.vault_aws_access_credentials.creds.security_token
}
```

### Solution 2: AWS Secrets Manager

```hcl
# Read existing secret
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "production/database/password"
}

resource "aws_db_instance" "main" {
  identifier     = "production-db"
  engine         = "postgres"
  instance_class = "db.r5.large"

  username = "admin"
  password = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
}

# Create and manage secret (for initial setup)
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "production/database/password"
  recovery_window_in_days = 7

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# Generate random password
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store in Secrets Manager
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.db_password.result
  })

  lifecycle {
    ignore_changes = [secret_string]  # Don't rotate on every apply
  }
}
```

### Solution 3: External Secrets Operator (Kubernetes)

```yaml
# ExternalSecret syncs secrets from external providers to Kubernetes
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secrets-manager
  target:
    name: database-credentials
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: production/database
        property: username
    - secretKey: password
      remoteRef:
        key: production/database
        property: password
```

```hcl
# Terraform to deploy External Secrets Operator
resource "helm_release" "external_secrets" {
  name             = "external-secrets"
  repository       = "https://charts.external-secrets.io"
  chart            = "external-secrets"
  namespace        = "external-secrets"
  create_namespace = true

  values = [<<-EOF
    installCRDs: true
    serviceAccount:
      annotations:
        eks.amazonaws.com/role-arn: ${aws_iam_role.external_secrets.arn}
  EOF
  ]
}

# IAM role for External Secrets
resource "aws_iam_role" "external_secrets" {
  name = "external-secrets-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:external-secrets:external-secrets"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "external_secrets" {
  name = "external-secrets-policy"
  role = aws_iam_role.external_secrets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ]
      Resource = "arn:aws:secretsmanager:*:*:secret:production/*"
    }]
  })
}
```

### Solution 4: SOPS (Secrets OPerationS)

SOPS encrypts secrets files that can be safely committed to git:

```bash
# Install SOPS
brew install sops

# Create .sops.yaml for configuration
cat > .sops.yaml << 'EOF'
creation_rules:
  - path_regex: \.enc\.yaml$
    kms: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
  - path_regex: \.enc\.json$
    kms: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
EOF

# Encrypt a secrets file
cat > secrets.yaml << 'EOF'
database:
  username: admin
  password: SuperSecretPassword123!
api_keys:
  stripe: sk_live_xxxxx
  sendgrid: SG.xxxxx
EOF

sops -e secrets.yaml > secrets.enc.yaml
rm secrets.yaml  # Remove plaintext

# Decrypt for use
sops -d secrets.enc.yaml > secrets.yaml

# Use with Terraform via templatefile
data "sops_file" "secrets" {
  source_file = "secrets.enc.yaml"
}

resource "aws_db_instance" "main" {
  password = data.sops_file.secrets.data["database.password"]
}
```

---

## State File Security

### The Danger of State Files

Terraform state files contain:
- All resource attributes (including sensitive values)
- Resource IDs that enable targeting
- Provider credentials if improperly configured
- Complete infrastructure topology

```
┌─────────────────────────────────────────────────────────────────┐
│                 TERRAFORM STATE FILE CONTENTS                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  {                                                              │
│    "resources": [                                               │
│      {                                                          │
│        "type": "aws_db_instance",                               │
│        "instances": [{                                          │
│          "attributes": {                                        │
│            "username": "admin",                                 │
│            "password": "EXPOSED_IN_PLAINTEXT!", ◄── DANGER!    │
│            "endpoint": "prod-db.xxx.us-east-1.rds.amazonaws"   │
│          }                                                      │
│        }]                                                       │
│      },                                                         │
│      {                                                          │
│        "type": "aws_iam_access_key",                            │
│        "instances": [{                                          │
│          "attributes": {                                        │
│            "secret": "EXPOSED_SECRET_KEY!" ◄── DANGER!         │
│          }                                                      │
│        }]                                                       │
│      }                                                          │
│    ]                                                            │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Secure State Storage

```hcl
# backend.tf - Secure S3 backend configuration
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "production/infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    dynamodb_table = "terraform-state-lock"

    # Role assumption for least privilege
    role_arn = "arn:aws:iam::123456789012:role/TerraformStateAccess"
  }
}
```

```hcl
# Create secure state bucket
resource "aws_s3_bucket" "terraform_state" {
  bucket = "company-terraform-state"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Purpose   = "Terraform State Storage"
    Sensitive = "true"
  }
}

# Enable versioning for recovery
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption with KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled = true
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Require encryption in transit
resource "aws_s3_bucket_policy" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyUnencryptedConnections"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid       = "DenyIncorrectEncryption"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.terraform_state.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "aws:kms"
          }
        }
      }
    ]
  })
}

# State locking with DynamoDB
resource "aws_dynamodb_table" "terraform_state_lock" {
  name         = "terraform-state-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Purpose = "Terraform State Locking"
  }
}

# KMS key for state encryption
resource "aws_kms_key" "terraform_state" {
  description             = "KMS key for Terraform state encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RootAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::123456789012:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "TerraformAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::123456789012:role/TerraformStateAccess"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}
```

### Marking Sensitive Values

```hcl
# Prevent sensitive values from appearing in logs/output
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

output "db_connection_string" {
  description = "Database connection string"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/app"
  sensitive   = true
}

# Sensitive values in resources
resource "aws_ssm_parameter" "db_password" {
  name  = "/production/database/password"
  type  = "SecureString"
  value = var.db_password

  lifecycle {
    ignore_changes = [value]
  }
}
```

---

## IAM and Access Control

### Principle of Least Privilege for Terraform

```hcl
# Bad: Overly permissive Terraform role
resource "aws_iam_role_policy" "terraform_bad" {
  name = "terraform-full-access"
  role = aws_iam_role.terraform.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"           # ❌ TOO BROAD
      Resource = "*"           # ❌ TOO BROAD
    }]
  })
}

# Good: Scoped permissions per environment
resource "aws_iam_role_policy" "terraform_production" {
  name = "terraform-production"
  role = aws_iam_role.terraform.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EC2Management"
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "ec2:CreateTags",
          "ec2:DeleteTags",
          "ec2:RunInstances",
          "ec2:TerminateInstances",
          "ec2:StopInstances",
          "ec2:StartInstances"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "ec2:ResourceTag/Environment" = "production"
          }
        }
      },
      {
        Sid    = "VPCManagement"
        Effect = "Allow"
        Action = [
          "ec2:CreateVpc",
          "ec2:DeleteVpc",
          "ec2:CreateSubnet",
          "ec2:DeleteSubnet",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupEgress"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestTag/Environment" = "production"
          }
        }
      },
      {
        Sid    = "S3StateAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::company-terraform-state/production/*"
      },
      {
        Sid    = "DynamoDBLocking"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "arn:aws:dynamodb:*:*:table/terraform-state-lock"
      }
    ]
  })
}
```

### Permission Boundaries

```hcl
# Permission boundary prevents privilege escalation
resource "aws_iam_policy" "terraform_boundary" {
  name = "terraform-permission-boundary"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowedServices"
        Effect   = "Allow"
        Action   = [
          "ec2:*",
          "rds:*",
          "s3:*",
          "eks:*",
          "elasticloadbalancing:*",
          "autoscaling:*",
          "cloudwatch:*",
          "logs:*",
          "sns:*",
          "sqs:*",
          "kms:*",
          "secretsmanager:*"
        ]
        Resource = "*"
      },
      {
        Sid      = "DenyIAMEscalation"
        Effect   = "Deny"
        Action   = [
          "iam:CreateUser",
          "iam:DeleteUser",
          "iam:AttachUserPolicy",
          "iam:CreateLoginProfile",
          "iam:UpdateLoginProfile",
          "iam:CreateAccessKey",
          "iam:UpdateAccessKey",
          "iam:PutUserPolicy",
          "iam:DeleteUserPolicy"
        ]
        Resource = "*"
      },
      {
        Sid      = "DenyBillingAccess"
        Effect   = "Deny"
        Action   = [
          "aws-portal:*",
          "budgets:*",
          "ce:*"
        ]
        Resource = "*"
      },
      {
        Sid      = "DenyOrganizationsAccess"
        Effect   = "Deny"
        Action   = "organizations:*"
        Resource = "*"
      }
    ]
  })
}

# Apply boundary to Terraform role
resource "aws_iam_role" "terraform" {
  name                 = "TerraformRole"
  permissions_boundary = aws_iam_policy.terraform_boundary.arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "codebuild.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}
```

---

## CI/CD Pipeline Security

### Secure GitHub Actions Workflow

```yaml
# .github/workflows/terraform-secure.yml
name: Terraform Secure Pipeline

on:
  pull_request:
    paths: ['terraform/**']
  push:
    branches: [main]
    paths: ['terraform/**']

# Minimal permissions
permissions:
  contents: read
  pull-requests: write
  id-token: write  # For OIDC

env:
  TF_VERSION: "1.6.0"
  AWS_REGION: "us-east-1"

jobs:
  security-scan:
    name: Security Scanning
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Scan for secrets in code
      - name: Gitleaks Secret Scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Terraform security scan
      - name: Checkov Security Scan
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          framework: terraform
          soft_fail: false
          output_format: sarif
          output_file_path: checkov.sarif

      # Upload results to GitHub Security
      - name: Upload Checkov Results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: checkov.sarif

  plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    needs: security-scan
    environment: production-plan  # Requires approval
    outputs:
      plan_exit_code: ${{ steps.plan.outputs.exitcode }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      # OIDC authentication - no static credentials
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsTerraform
          aws-region: ${{ env.AWS_REGION }}
          role-session-name: GitHubActions-${{ github.run_id }}

      - name: Terraform Init
        run: |
          cd terraform/environments/production
          terraform init -backend-config="encrypt=true"

      - name: Terraform Plan
        id: plan
        run: |
          cd terraform/environments/production
          terraform plan -detailed-exitcode -out=tfplan 2>&1 | tee plan.txt
          echo "exitcode=$?" >> $GITHUB_OUTPUT
        continue-on-error: true

      # Store plan as artifact (encrypted)
      - name: Encrypt and Upload Plan
        run: |
          cd terraform/environments/production
          gpg --symmetric --cipher-algo AES256 --batch --passphrase "${{ secrets.PLAN_ENCRYPTION_KEY }}" tfplan
          gpg --symmetric --cipher-algo AES256 --batch --passphrase "${{ secrets.PLAN_ENCRYPTION_KEY }}" plan.txt

      - uses: actions/upload-artifact@v4
        with:
          name: terraform-plan
          path: |
            terraform/environments/production/tfplan.gpg
            terraform/environments/production/plan.txt.gpg

      # Comment plan on PR (sanitized)
      - name: Comment Plan on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('terraform/environments/production/plan.txt', 'utf8');

            // Sanitize sensitive info from plan output
            const sanitized = plan
              .replace(/password\s*=\s*"[^"]*"/gi, 'password = "***REDACTED***"')
              .replace(/secret\s*=\s*"[^"]*"/gi, 'secret = "***REDACTED***"')
              .replace(/token\s*=\s*"[^"]*"/gi, 'token = "***REDACTED***"');

            const output = `#### Terraform Plan 📖

            <details><summary>Show Plan</summary>

            \`\`\`
            ${sanitized.substring(0, 60000)}
            \`\`\`

            </details>`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

  apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    needs: plan
    if: github.ref == 'refs/heads/main' && needs.plan.outputs.plan_exit_code == '2'
    environment: production-apply  # Requires approval
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsTerraform
          aws-region: ${{ env.AWS_REGION }}

      - uses: actions/download-artifact@v4
        with:
          name: terraform-plan

      - name: Decrypt Plan
        run: |
          cd terraform/environments/production
          gpg --decrypt --batch --passphrase "${{ secrets.PLAN_ENCRYPTION_KEY }}" tfplan.gpg > tfplan

      - name: Terraform Init
        run: |
          cd terraform/environments/production
          terraform init

      - name: Terraform Apply
        run: |
          cd terraform/environments/production
          terraform apply -auto-approve tfplan
```

### OIDC Authentication (No Static Credentials)

```hcl
# Create GitHub OIDC provider in AWS
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]
}

# Create role that GitHub Actions can assume
resource "aws_iam_role" "github_actions_terraform" {
  name = "GitHubActionsTerraform"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          # Only allow from specific repo and branch
          "token.actions.githubusercontent.com:sub" = "repo:company/infrastructure:ref:refs/heads/main"
        }
      }
    }]
  })

  # Apply permission boundary
  permissions_boundary = aws_iam_policy.terraform_boundary.arn
}
```

---

## Compliance and Auditing

### Compliance Frameworks in Code

```hcl
# modules/compliant-s3/main.tf
# SOC2 and HIPAA compliant S3 bucket

resource "aws_s3_bucket" "compliant" {
  bucket = var.bucket_name

  tags = merge(var.tags, {
    Compliance      = var.compliance_framework
    DataClassification = var.data_classification
    Owner           = var.owner
  })
}

# Requirement: Encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "compliant" {
  bucket = aws_s3_bucket.compliant.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Requirement: Access logging
resource "aws_s3_bucket_logging" "compliant" {
  bucket = aws_s3_bucket.compliant.id

  target_bucket = var.logging_bucket
  target_prefix = "${var.bucket_name}/"
}

# Requirement: Versioning for data integrity
resource "aws_s3_bucket_versioning" "compliant" {
  bucket = aws_s3_bucket.compliant.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Requirement: Block public access
resource "aws_s3_bucket_public_access_block" "compliant" {
  bucket = aws_s3_bucket.compliant.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Requirement: Lifecycle for data retention
resource "aws_s3_bucket_lifecycle_configuration" "compliant" {
  bucket = aws_s3_bucket.compliant.id

  rule {
    id     = "retention"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    expiration {
      days = var.retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.retention_days
    }
  }
}

# Compliance validation
resource "null_resource" "compliance_check" {
  triggers = {
    bucket_id = aws_s3_bucket.compliant.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Verify encryption
      encryption=$(aws s3api get-bucket-encryption --bucket ${aws_s3_bucket.compliant.id} 2>/dev/null)
      if [ -z "$encryption" ]; then
        echo "COMPLIANCE FAILURE: Encryption not enabled"
        exit 1
      fi

      # Verify public access block
      public_access=$(aws s3api get-public-access-block --bucket ${aws_s3_bucket.compliant.id})
      if echo "$public_access" | grep -q '"BlockPublicAcls": false'; then
        echo "COMPLIANCE FAILURE: Public access not fully blocked"
        exit 1
      fi

      echo "COMPLIANCE CHECK PASSED"
    EOT
  }
}
```

### Audit Trail

```hcl
# Enable CloudTrail for all Terraform operations
resource "aws_cloudtrail" "terraform_audit" {
  name                          = "terraform-audit-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.terraform_state.arn}/"]
    }
  }

  tags = {
    Purpose = "Terraform Audit Trail"
  }
}

# Alert on state file access
resource "aws_cloudwatch_log_metric_filter" "state_access" {
  name           = "terraform-state-access"
  pattern        = "{ $.eventSource = s3.amazonaws.com && $.requestParameters.bucketName = terraform-state }"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name

  metric_transformation {
    name      = "StateFileAccess"
    namespace = "TerraformSecurity"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "state_access_alert" {
  alarm_name          = "terraform-state-unusual-access"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "StateFileAccess"
  namespace           = "TerraformSecurity"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Unusual number of Terraform state file accesses"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}
```

---

## War Story: The State File Breach

**Company**: Financial services provider
**Incident**: Complete infrastructure compromise via state file

**Timeline**:
- **Day 1**: Developer commits AWS credentials to public GitHub repo
- **Day 7**: Credentials discovered by automated scanner (attacker)
- **Day 8**: Attacker finds S3 bucket with Terraform state via naming convention
- **Day 14**: Attacker downloads state files from 47 projects
- **Day 21**: Attacker begins accessing production systems using credentials from state
- **Day 28**: Security team detects unusual database queries
- **Day 29**: Full incident response initiated

**What the attacker gained from state files**:
```
From terraform.tfstate:
├── RDS passwords (plaintext)
├── API keys for third-party services
├── SSH key passphrases
├── IAM user secret access keys
├── SSL certificate private keys
├── Application secrets
├── VPN pre-shared keys
└── Complete network topology
```

**Financial Impact**:
- Incident response: $890K
- Forensics and investigation: $340K
- Regulatory fines (PCI DSS): $2.1M
- Customer notification: $450K
- Credit monitoring: $1.2M
- Legal fees: $780K
- Lost business: $4.2M
- Insurance premium increase: $340K/year
- **Total first year**: $10.3M

**Security Measures That Would Have Prevented This**:

```hcl
# 1. State encryption with customer-managed keys
terraform {
  backend "s3" {
    encrypt    = true
    kms_key_id = "alias/terraform-state"  # CMK, not default
  }
}

# 2. Secret values from Vault, not in state
data "vault_generic_secret" "db" {
  path = "secret/database"
}

# 3. Restrict state bucket access
resource "aws_s3_bucket_policy" "state" {
  policy = jsonencode({
    Statement = [{
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = "${aws_s3_bucket.state.arn}/*"
      Condition = {
        StringNotEquals = {
          "aws:PrincipalArn" = [
            "arn:aws:iam::123456789012:role/TerraformRole"
          ]
        }
      }
    }]
  })
}

# 4. No IAM access keys - use OIDC
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  # ...
}

# 5. Audit all state access
resource "aws_cloudtrail" "state_audit" {
  # Log all S3 data events for state bucket
}
```

---

## Common Mistakes

| Mistake | Risk | Solution |
|---------|------|----------|
| Secrets in terraform.tfvars | Committed to git, exposed | Use Vault, Secrets Manager, or SOPS |
| State file in version control | Secrets exposed in plaintext | Use remote backend with encryption |
| Overly permissive IAM for Terraform | Blast radius too large | Least privilege per environment |
| No state file encryption | Data exposure if bucket accessed | Enable SSE-KMS with CMK |
| Static credentials in CI/CD | Credential theft risk | Use OIDC federation |
| Skipping security scans | Misconfigurations reach production | Mandatory Checkov/tfsec in pipeline |
| No audit trail | Can't detect or investigate breaches | Enable CloudTrail for state bucket |
| Sensitive outputs not marked | Appear in logs and console | Always use `sensitive = true` |

---

## Quiz

Test your understanding of IaC security:

<details>
<summary>1. Why is the Terraform state file considered highly sensitive?</summary>

**Answer**: The Terraform state file contains:
- All resource attribute values, including sensitive ones (passwords, API keys, etc.) in plaintext
- Complete infrastructure topology (resource IDs, endpoints, IP addresses)
- Provider credentials if improperly configured
- Enough information to reconstruct and access the entire infrastructure

An attacker with state file access can extract credentials, understand the network topology, and target specific resources.
</details>

<details>
<summary>2. What is the advantage of OIDC federation over static IAM credentials for CI/CD?</summary>

**Answer**: OIDC federation:
- **No stored secrets**: No static credentials to leak or rotate
- **Short-lived tokens**: Each run gets temporary credentials (15min-1hr)
- **Condition-based access**: Can restrict to specific repos, branches, or workflows
- **Audit trail**: Each assume role call is logged with session name
- **No credential rotation**: Credentials are generated per-session
- **Reduced blast radius**: If pipeline is compromised, only current session affected
</details>

<details>
<summary>3. What security controls should a compliant S3 bucket have according to SOC2/HIPAA?</summary>

**Answer**: A compliant S3 bucket requires:
- **Encryption at rest**: Server-side encryption with KMS (not just AES-256)
- **Encryption in transit**: HTTPS-only bucket policy
- **Access logging**: All access logged to separate bucket
- **Versioning**: For data integrity and recovery
- **Public access blocked**: All four public access block settings enabled
- **Lifecycle policies**: For data retention compliance
- **Access controls**: Least privilege IAM policies
- **Audit trail**: CloudTrail logging of all data events
</details>

<details>
<summary>4. Calculate the total cost of a state file breach affecting 2.3 million records with an average cost of $150 per record.</summary>

**Answer**:
- Direct breach cost: 2,300,000 × $150 = **$345,000,000**

However, actual costs typically include:
- Incident response: ~$500K-$1M
- Forensics: ~$300K-$500K
- Regulatory fines: Variable (GDPR up to 4% revenue)
- Legal fees: ~$500K-$2M
- Customer notification: ~$1-5 per record
- Credit monitoring: ~$50-100 per affected person
- Lost business: 20-40% customer churn

The $150/record IBM figure includes these factors as an average.
</details>

<details>
<summary>5. What is a permission boundary and why use one with Terraform roles?</summary>

**Answer**: A permission boundary is an IAM policy that sets the maximum permissions a role can have, regardless of other attached policies. For Terraform:
- **Prevents privilege escalation**: Terraform can't create more powerful roles than itself
- **Limits blast radius**: Even if Terraform is compromised, it can't access everything
- **Enforces guardrails**: Certain actions (billing, organizations) always denied
- **Enables delegation**: Teams can create roles without admin review, within bounds

Example: A permission boundary might deny `iam:CreateUser`, `organizations:*`, and `aws-portal:*` while allowing normal infrastructure operations.
</details>

<details>
<summary>6. What is the difference between Checkov, tfsec, and Terrascan?</summary>

**Answer**:
- **Checkov**: Most comprehensive, supports Terraform/CloudFormation/Kubernetes/Docker, 1000+ policies, Python-based, easy custom policies
- **tfsec**: Terraform-specific (now part of Trivy), faster for Terraform-only, YAML-based custom rules, good IDE integration
- **Terrascan**: Uses Rego policies (like OPA), good for orgs already using OPA, supports multiple IaC frameworks

In practice, many teams use multiple scanners as they catch different issues. Checkov is often the primary choice for comprehensive coverage.
</details>

<details>
<summary>7. Why should you encrypt Terraform plan files in CI/CD pipelines?</summary>

**Answer**: Terraform plan files contain:
- All values that will be written to state (including sensitive ones)
- Resource changes with before/after values
- Variable values (including sensitive variables)

If stored unencrypted as CI/CD artifacts:
- Other pipeline stages might access them
- Artifact retention might expose them long-term
- Log aggregation might capture them
- Failed pipelines leave them accessible

Encrypting with GPG/age before storing as artifacts ensures only authorized steps can read them.
</details>

<details>
<summary>8. A team discovered that their Terraform state file was accessed from an unknown IP address. What immediate actions should they take?</summary>

**Answer**: Immediate response:
1. **Rotate all secrets in state**: Every password, API key, and credential
2. **Invalidate sessions**: Revoke all active sessions for exposed service accounts
3. **Review CloudTrail**: What else was accessed? What actions were taken?
4. **Enable state locking**: Prevent further modifications
5. **Change backend credentials**: Rotate S3 access keys, KMS keys
6. **Audit recent changes**: Look for unauthorized infrastructure modifications
7. **Notify security team**: Begin formal incident response
8. **Preserve evidence**: Don't delete logs, make copies of artifacts
9. **Check for persistence**: Look for new IAM users, access keys, or roles
10. **Enable additional monitoring**: Alert on all state access temporarily
</details>

---

## Hands-On Exercise

**Objective**: Implement a secure Terraform configuration with secrets management and security scanning.

### Part 1: Set Up Security Scanning

```bash
# Create project structure
mkdir -p secure-iac-lab/{terraform,policy}
cd secure-iac-lab

# Create intentionally insecure Terraform
cat > terraform/main.tf << 'EOF'
# Intentionally insecure for demonstration

variable "db_password" {
  default = "Password123!"  # BAD: Hardcoded secret
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
  # Missing: encryption, versioning, public access block
}

resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # BAD: SSH open to world
  }
}

resource "aws_db_instance" "main" {
  identifier     = "production"
  engine         = "mysql"
  instance_class = "db.t3.micro"

  username = "admin"
  password = var.db_password

  publicly_accessible = true  # BAD: DB public
  storage_encrypted   = false # BAD: No encryption
}
EOF

# Run security scans
pip install checkov
checkov -d terraform/

# You should see multiple failures
```

### Part 2: Fix Security Issues

```bash
# Create secure version
cat > terraform/main_secure.tf << 'EOF'
# Secure configuration

variable "db_password" {
  description = "Database password - provide via TF_VAR_db_password"
  type        = string
  sensitive   = true
  # No default - must be provided
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket-${random_id.suffix.hex}"

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Web server security group"

  # SSH only from internal network
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "SSH from internal only"
  }

  # HTTPS from anywhere
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

  tags = {
    Name = "web-sg"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "production"
  engine         = "mysql"
  instance_class = "db.t3.micro"

  username = "admin"
  password = var.db_password

  publicly_accessible    = false
  storage_encrypted      = true
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "production-final-snapshot"

  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  tags = {
    Environment = "production"
  }

  lifecycle {
    ignore_changes = [password]
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}
EOF

# Verify fixes
checkov -d terraform/ -f terraform/main_secure.tf
```

### Part 3: Implement Secrets Management

```bash
# Create secrets management example
cat > terraform/secrets.tf << 'EOF'
# Using AWS Secrets Manager

# Create the secret
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "production/database/password"
  recovery_window_in_days = 7
}

# Generate random password
resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}:?"
}

# Store password
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.db.result
  })
}

# Reference secret in RDS
data "aws_secretsmanager_secret_version" "db" {
  secret_id  = aws_secretsmanager_secret.db_password.id
  depends_on = [aws_secretsmanager_secret_version.db_password]
}

locals {
  db_creds = jsondecode(data.aws_secretsmanager_secret_version.db.secret_string)
}

# Use in database (reference to above RDS)
# password = local.db_creds["password"]
EOF
```

### Success Criteria

- [ ] Initial Checkov scan shows 5+ security issues
- [ ] Fixed configuration passes all Checkov checks
- [ ] No hardcoded secrets in final configuration
- [ ] S3 bucket has encryption, versioning, and public access block
- [ ] Security group restricts SSH to internal network
- [ ] Database is not publicly accessible and has encryption

---

## Key Takeaways

- [ ] **State files are crown jewels** - Encrypt, restrict access, audit all access
- [ ] **Never hardcode secrets** - Use Vault, Secrets Manager, SOPS, or environment variables
- [ ] **Scan early and often** - Checkov, tfsec, Trivy in every PR
- [ ] **Use OIDC for CI/CD** - No static credentials to steal
- [ ] **Apply permission boundaries** - Limit what Terraform can do even when compromised
- [ ] **Mark sensitive values** - `sensitive = true` prevents logging
- [ ] **Audit everything** - CloudTrail for state bucket, alerts on unusual access
- [ ] **Least privilege always** - Terraform role only needs what it manages
- [ ] **Compliance in code** - Encode requirements in modules and policies
- [ ] **Assume breach mentality** - Design so state file theft isn't catastrophic

---

## Did You Know?

> **State File Statistics**: A 2023 survey found that 43% of organizations store Terraform state files without encryption, and 12% store them in version control systems accessible to all developers.

> **Checkov Adoption**: Bridgecrew's Checkov has over 1,000 built-in policies and scans over 5 million infrastructure configurations per month, catching an average of 47 misconfigurations per project.

> **OIDC Origin**: The OpenID Connect protocol used for GitHub Actions authentication was standardized in 2014, but adoption for CI/CD didn't become widespread until AWS added support in 2021.

> **Cost of Secrets**: According to GitGuardian's 2023 report, over 10 million secrets were detected in public GitHub commits, with the average time to remediation being 327 days.

---

## Next Module

Continue to [Module 6.4: IaC at Scale](module-6.4-iac-at-scale/) to learn about managing infrastructure as code across large organizations with multiple teams and environments.
